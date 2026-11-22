"""Compare file formats for the raw-layer hop GCS → BigQuery: storage, write time, load time, schema behaviour.

The same rows are written in every format, decoded once from a verified export (Parquet, or Avro for
exports made before 2026-11-22):

    avro_deflate   Avro with deflate (the format before 2026-11-22)
    avro_null      Avro without compression, to separate format from compression
    jsonl          newline-delimited JSON, uncompressed
    jsonl_gzip     the same, gzip level 6
    parquet        Parquet with Snappy (pyarrow), the production format

Subcommands (see benchmarks/README.md for the full procedure):

    convert   on the VM: decode chunks of an export once, write every format, time each writer
    upload    on the VM: upload every format to gs://<bucket>/<prefix>/<format>/, time it
    load      on a workstation: load each format into <dataset>.events_<format>, read job statistics
    contract  local checks, plus (with --bucket) small BigQuery loads: autodetect, coercion, late failure

Run with: uv run --group bench python benchmarks/file_formats.py <subcommand> --help
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
from datetime import datetime, timezone
from decimal import Decimal
import gzip
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time

from fastavro import reader as avro_reader
from fastavro import writer as avro_write_block
from fastavro.write import Writer as AvroWriter

from glamira_pipeline.export.schema import parquet_schema

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "raw"
FORMATS = ("avro_deflate", "avro_null", "jsonl", "jsonl_gzip", "parquet")
EXTENSIONS = {"avro_deflate": "avro", "avro_null": "avro", "jsonl": "jsonl", "jsonl_gzip": "jsonl.gz",
              "parquet": "parquet"}
PARQUET_BATCH = 50_000
clock = time.perf_counter


# --- row serialization ----------------------------------------------------------------------

def _json_default(value):
    if isinstance(value, datetime):  # BigQuery's canonical TIMESTAMP text form
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f UTC")
    if isinstance(value, Decimal):  # NUMERIC as a string keeps every digit
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def json_line(row: dict) -> bytes:
    return (json.dumps(row, ensure_ascii=False, separators=(",", ":"), default=_json_default) + "\n").encode()


def avro_schema(bq_fields: list[dict]) -> dict:
    """An Avro schema equivalent to a BigQuery JSON schema (Avro is only a benchmark format now)."""
    scalar = {"STRING": "string", "INTEGER": "long", "BOOLEAN": "boolean",
              "NUMERIC": {"type": "bytes", "logicalType": "decimal", "precision": 38, "scale": 9},
              "TIMESTAMP": {"type": "long", "logicalType": "timestamp-micros"}}

    def fields(specs: list[dict], path: str) -> list[dict]:
        out = []
        for spec in specs:
            if spec["type"] == "RECORD":
                name = "".join(part.capitalize() for part in f"{path}_{spec['name']}".split("_") if part)
                kind = {"type": "record", "name": name, "fields": fields(spec["fields"], f"{path}_{spec['name']}")}
            else:
                kind = scalar[spec["type"]]
            mode = spec.get("mode", "NULLABLE")
            if mode == "REPEATED":
                out.append({"name": spec["name"], "type": {"type": "array", "items": kind}, "default": []})
            elif mode == "NULLABLE":
                out.append({"name": spec["name"], "type": ["null", kind], "default": None})
            else:
                out.append({"name": spec["name"], "type": kind})
        return out

    return {"type": "record", "name": "Event", "namespace": "glamira.raw", "fields": fields(bq_fields, "")}


def read_rows(path: Path):
    """Decoded rows of one exported part, Parquet (current exports) or Avro (exports before 2026-11-22)."""
    if path.suffix == ".parquet":
        import pyarrow.parquet as pq

        for batch in pq.ParquetFile(path).iter_batches(batch_size=10_000):
            yield from batch.to_pylist()
    else:
        with path.open("rb") as stream:
            yield from avro_reader(stream)


class FormatWriters:
    """One open file per format for the current chunk; ``seconds`` accumulates time spent in each format."""

    def __init__(self, out: Path, chunk: str, avro_schema: dict, parquet_schema, formats: tuple[str, ...]):
        import pyarrow.parquet as pq

        self.formats = formats
        self.seconds = dict.fromkeys(formats, 0.0)
        self.paths = {f: out / f / f"chunk={chunk}" / f"part-00000.{EXTENSIONS[f]}" for f in formats}
        for path in self.paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)
        self.streams, self.avro = {}, {}
        for fmt in formats:
            started = clock()
            if fmt.startswith("avro"):
                self.streams[fmt] = self.paths[fmt].open("wb")
                codec = "deflate" if fmt == "avro_deflate" else "null"
                self.avro[fmt] = AvroWriter(self.streams[fmt], avro_schema, codec=codec)
            elif fmt == "jsonl":
                self.streams[fmt] = self.paths[fmt].open("wb", buffering=1 << 20)
            elif fmt == "jsonl_gzip":
                self.streams[fmt] = gzip.open(self.paths[fmt], "wb", compresslevel=6)
            self.seconds[fmt] += clock() - started
        self.parquet_schema = parquet_schema
        self.parquet = (pq.ParquetWriter(self.paths["parquet"], parquet_schema, compression="snappy")
                        if "parquet" in formats else None)
        self.batch: list[dict] = []

    def write(self, row: dict) -> None:
        line = None
        for fmt in self.formats:
            started = clock()
            if fmt.startswith("avro"):
                self.avro[fmt].write(row)
            elif fmt == "jsonl":
                line = json_line(row)
                self.streams[fmt].write(line)
            elif fmt == "jsonl_gzip":
                self.streams[fmt].write(json_line(row))  # serialized again: each format pays its own cost
            elif fmt == "parquet":
                self.batch.append(row)
                if len(self.batch) >= PARQUET_BATCH:
                    self._flush_parquet()
            self.seconds[fmt] += clock() - started

    def _flush_parquet(self) -> None:
        import pyarrow as pa

        if self.batch:
            self.parquet.write_table(pa.Table.from_pylist(self.batch, schema=self.parquet_schema))
            self.batch = []

    def close(self) -> None:
        for fmt in self.formats:
            started = clock()
            if fmt.startswith("avro"):
                self.avro[fmt].flush()
                self.streams[fmt].close()
            elif fmt in ("jsonl", "jsonl_gzip"):
                self.streams[fmt].close()
            elif fmt == "parquet":
                self._flush_parquet()
                self.parquet.close()
            self.seconds[fmt] += clock() - started


# --- convert ----------------------------------------------------------------------------------

def chunk_parts(table_dir: Path, chunks: list[str] | None) -> dict[str, list[Path]]:
    manifest = json.loads((table_dir / "_manifest.json").read_text())
    parts: dict[str, list[Path]] = {}
    for part in manifest["files"]:
        chunk = part["name"].split("/", 1)[0].removeprefix("chunk=")
        if chunks is None or chunk in chunks:
            parts.setdefault(chunk, []).append(table_dir / part["name"])
    missing = set(chunks or ()) - parts.keys()
    if missing:
        raise SystemExit(f"chunks not in the export: {sorted(missing)}")
    return parts


def convert(args) -> None:
    bq_fields = json.loads((SCHEMAS / "events.bq.json").read_text())
    avro, parquet = avro_schema(bq_fields), parquet_schema(bq_fields)
    formats = tuple(args.formats)
    parts = chunk_parts(args.export_table, args.chunks)
    totals = dict.fromkeys(formats, 0.0)
    rows, decode_seconds, started = 0, 0.0, clock()
    for chunk, paths in sorted(parts.items()):
        writers = FormatWriters(args.out, chunk, avro, parquet, formats)
        chunk_rows, t0 = 0, clock()
        for path in paths:
            records = read_rows(path)
            while True:
                d0 = clock()
                row = next(records, None)
                decode_seconds += clock() - d0
                if row is None:
                    break
                writers.write(row)
                chunk_rows += 1
        writers.close()
        rows += chunk_rows
        for fmt in formats:
            totals[fmt] += writers.seconds[fmt]
        print(f"{chunk}: {chunk_rows:,} rows in {clock() - t0:.1f} s", file=sys.stderr, flush=True)
    result = {
        "rows": rows,
        "chunks": sorted(parts),
        "decode_seconds": round(decode_seconds, 1),
        "wall_seconds": round(clock() - started, 1),
        "formats": {fmt: {"files": len(parts),
                          "bytes": sum(p.stat().st_size for p in (args.out / fmt).rglob("part-*")),
                          "write_seconds": round(totals[fmt], 1),
                          "rows_per_second": round(rows / totals[fmt]) if totals[fmt] else None}
                    for fmt in formats},
        "environment": environment(),
    }
    source_bytes = sum(p.stat().st_size for paths in parts.values() for p in paths)
    result["source_avro_bytes"] = source_bytes
    write_result(args.out / "convert_results.json", result)


# --- upload -----------------------------------------------------------------------------------

def upload(args) -> None:
    from google.cloud import storage

    bucket = storage.Client().bucket(args.bucket)
    result = {"bucket": args.bucket, "prefix": args.prefix, "formats": {}}
    for fmt in args.formats:
        files = sorted((args.out / fmt).rglob("part-*"))
        started = clock()

        def send(path: Path, fmt=fmt) -> int:
            name = f"{args.prefix.strip('/')}/{fmt}/{path.relative_to(args.out / fmt).as_posix()}"
            bucket.blob(name).upload_from_filename(str(path), checksum="crc32c")
            return path.stat().st_size

        with ThreadPoolExecutor(args.workers) as pool:
            sent = sum(pool.map(send, files))
        seconds = clock() - started
        result["formats"][fmt] = {"files": len(files), "bytes": sent, "seconds": round(seconds, 1),
                                  "mb_per_second": round(sent / seconds / 1e6, 1)}
        print(f"{fmt}: {sent / 1e9:.2f} GB in {seconds:.1f} s", file=sys.stderr, flush=True)
    result["environment"] = environment()
    write_result(args.out / "upload_results.json", result)


# --- load -------------------------------------------------------------------------------------

def job_config(fmt: str, **extra):
    from google.cloud import bigquery

    if fmt.startswith("avro"):
        return bigquery.LoadJobConfig(source_format="AVRO", use_avro_logical_types=True,
                                      decimal_target_types=["NUMERIC"], **extra)
    if fmt.startswith("jsonl"):
        return bigquery.LoadJobConfig(source_format="NEWLINE_DELIMITED_JSON", **extra)
    options = bigquery.ParquetOptions()
    options.enable_list_inference = True  # LIST<struct> → REPEATED RECORD, not list.element
    return bigquery.LoadJobConfig(source_format="PARQUET", parquet_options=options,
                                  decimal_target_types=["NUMERIC"], **extra)


def create_contract_table(bq, table_id: str) -> None:
    """(Re)create ``table_id`` exactly as production creates raw tables: contract schema, partitions, clustering."""
    from google.cloud import bigquery

    bq.delete_table(table_id, not_found_ok=True)
    schema = [bigquery.SchemaField.from_api_repr(f) for f in json.loads((SCHEMAS / "events.bq.json").read_text())]
    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(type_=bigquery.TimePartitioningType.DAY, field="time_stamp")
    table.clustering_fields = ["collection"]
    bq.create_table(table)


def load(args) -> None:
    from google.cloud import bigquery, storage

    bq, gcs = bigquery.Client(project=args.project), storage.Client(project=args.project)
    location = bq.get_dataset(args.dataset).location
    result = {"dataset": args.dataset, "location": location, "repeats": args.repeats, "formats": {}}
    for fmt in args.formats:
        prefix = f"{args.prefix.strip('/')}/{fmt}/"
        uris = sorted(f"gs://{args.bucket}/{b.name}" for b in gcs.list_blobs(args.bucket, prefix=prefix)
                      if "/part-" in b.name)
        if not uris:
            raise SystemExit(f"no files under gs://{args.bucket}/{prefix}")
        table_id = f"{bq.project}.{args.dataset}.events_{fmt}"
        create_contract_table(bq, table_id)
        runs = []
        for repeat in range(1, args.repeats + 1):
            submitted = clock()
            job = bq.load_table_from_uri(uris, table_id, location=location,
                                         job_config=job_config(fmt, write_disposition="WRITE_TRUNCATE_DATA"))
            job.result()
            stats = job._properties["statistics"]
            runs.append({
                "job_id": job.job_id,
                "server_seconds": round((job.ended - job.started).total_seconds(), 1),
                "queue_seconds": round((job.started - job.created).total_seconds(), 1),
                "client_seconds": round(clock() - submitted, 1),
                "slot_seconds": round(int(stats.get("totalSlotMs", 0)) / 1000, 1),
                "input_bytes": int(stats["load"]["inputFileBytes"]),
                "output_rows": int(stats["load"]["outputRows"]),
                "output_bytes": int(stats["load"]["outputBytes"]),
            })
            print(f"{fmt} #{repeat}: {runs[-1]['server_seconds']} s, {runs[-1]['slot_seconds']} slot-s, "
                  f"{runs[-1]['output_rows']:,} rows", file=sys.stderr, flush=True)
        result["formats"][fmt] = {
            "files": len(uris),
            "runs": runs,
            "median_server_seconds": statistics.median(r["server_seconds"] for r in runs),
            "median_slot_seconds": statistics.median(r["slot_seconds"] for r in runs),
            "rows": runs[-1]["output_rows"],
            "table_bytes": runs[-1]["output_bytes"],
        }
    write_result(args.results, result)


# --- contract ---------------------------------------------------------------------------------

def bad_rows(row: dict) -> dict[str, dict]:
    """Two realistic contract breaks on a real row: a quoted number, and text in a TIMESTAMP."""
    quoted = copy.deepcopy(row)
    quoted["recommendation_clicked_position"] = "7"
    broken = copy.deepcopy(row)
    broken["time_stamp"] = "not-a-time"
    return {"quoted_number": quoted, "text_in_timestamp": broken}


def contract(args) -> None:
    bq_fields = json.loads((SCHEMAS / "events.bq.json").read_text())
    avro, parquet = avro_schema(bq_fields), parquet_schema(bq_fields)
    row = next(read_rows(args.sample))
    result: dict = {"local_write": {}}
    for case, bad in bad_rows(row).items():  # where does each format notice the break?
        try:
            with open(os.devnull, "wb") as sink:
                avro_write_block(sink, avro, [bad], validator=True)
            avro = "accepted"
        except Exception as exc:  # noqa: BLE001 - the error type is what is being reported
            avro = f"rejected at write: {type(exc).__name__}"
        try:
            json_line(bad)
            jsonl = "accepted"
        except Exception as exc:  # noqa: BLE001
            jsonl = f"rejected at write: {type(exc).__name__}"
        try:
            import pyarrow as pa

            pa.Table.from_pylist([bad], schema=parquet)
            parquet = "accepted"
        except Exception as exc:  # noqa: BLE001
            parquet = f"rejected at write: {type(exc).__name__}"
        result["local_write"][case] = {"avro": avro, "parquet": parquet, "jsonl": jsonl}
    if args.bucket:
        result["bigquery"] = contract_bigquery(args, row)
    write_result(args.results, result)


def contract_bigquery(args, row: dict) -> dict:
    from google.api_core.exceptions import GoogleAPICallError
    from google.cloud import bigquery, storage

    bq, gcs = bigquery.Client(project=args.project), storage.Client(project=args.project)
    location = bq.get_dataset(args.dataset).location
    bucket = gcs.bucket(args.bucket)
    base = f"{args.prefix.strip('/')}/contract"
    out: dict = {}

    def put(name: str, data: bytes) -> str:
        bucket.blob(f"{base}/{name}").upload_from_string(data)
        return f"gs://{args.bucket}/{base}/{name}"

    def run(uris, table_id, config) -> dict:
        try:
            job = bq.load_table_from_uri(uris, table_id, location=location, job_config=config)
            job.result()
            return {"status": "loaded", "rows": job.output_rows}
        except GoogleAPICallError as exc:
            return {"status": "failed at load", "error": str(exc)[:300]}

    # 1. Schema from the files alone: Avro carries it, JSONL must be guessed by autodetect.
    for fmt in ("avro_deflate", "jsonl"):
        uris = [u for u in (f"gs://{args.bucket}/{b.name}" for b in
                            gcs.list_blobs(args.bucket, prefix=f"{args.prefix.strip('/')}/{fmt}/")) if "/part-" in u]
        table_id = f"{bq.project}.{args.dataset}.schema_from_{fmt}"
        bq.delete_table(table_id, not_found_ok=True)
        config = job_config(fmt, write_disposition="WRITE_TRUNCATE")
        if fmt == "jsonl":
            config.autodetect = True
        outcome = run(uris[:1], table_id, config)
        if outcome["status"] == "loaded":
            outcome["differences_from_contract"] = schema_differences(
                [f.to_api_repr() for f in bq.get_table(table_id).schema],
                json.loads((SCHEMAS / "events.bq.json").read_text()))
        out[f"schema_from_{fmt}"] = outcome

    # 2. A contract break that reaches BigQuery as JSONL (Avro refuses to write it).
    for case, bad in bad_rows(row).items():
        table_id = f"{bq.project}.{args.dataset}.contract_{case}"
        create_contract_table(bq, table_id)
        uri = put(f"{case}.jsonl", json_line(row) + json_line(bad))
        outcome = run([uri], table_id, job_config("jsonl", write_disposition="WRITE_TRUNCATE_DATA"))
        if outcome["status"] == "loaded" and case == "quoted_number":
            query = (f"SELECT recommendation_clicked_position AS value, COUNT(*) AS n FROM `{table_id}` "
                     "GROUP BY 1 ORDER BY 1")
            outcome["stored_values"] = [dict(r) for r in bq.query(query, location=location).result()]
        out[case] = outcome
    return out


def schema_differences(actual: list[dict], expected: list[dict], path: str = "") -> list[str]:
    """Columns whose type or mode differs, or that are missing or extra, compared with the contract."""
    aliases = {"INT64": "INTEGER", "BOOL": "BOOLEAN", "FLOAT64": "FLOAT", "STRUCT": "RECORD"}

    def norm(f):
        return aliases.get(f["type"], f["type"]), f.get("mode") or "NULLABLE"

    found, wanted = {f["name"]: f for f in actual}, {f["name"]: f for f in expected}
    diffs = [f"{path}{n}: missing" for n in wanted.keys() - found.keys()]
    diffs += [f"{path}{n}: extra ({found[n]['type']})" for n in found.keys() - wanted.keys()]
    for name in sorted(found.keys() & wanted.keys()):
        a, e = found[name], wanted[name]
        if norm(a) != norm(e):
            diffs.append(f"{path}{name}: {'/'.join(norm(a))}, contract {'/'.join(norm(e))}")
        if a.get("fields") and e.get("fields"):
            diffs += schema_differences(a["fields"], e["fields"], f"{path}{name}.")
    return sorted(diffs)


# --- helpers ----------------------------------------------------------------------------------

def environment() -> dict:
    import fastavro
    import pyarrow

    return {"host": platform.node(), "cpus": os.cpu_count(), "python": platform.python_version(),
            "fastavro": fastavro.__version__, "pyarrow": pyarrow.__version__,
            "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def write_result(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps(result, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("convert", help="write the same rows in every format and time each writer")
    p.add_argument("export_table", type=Path, help="an events export directory (holds _manifest.json)")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--chunks", nargs="+", help="chunk IDs (default: all)")
    p.add_argument("--formats", nargs="+", choices=FORMATS, default=list(FORMATS))
    p.set_defaults(func=convert)

    p = sub.add_parser("upload", help="upload every format to GCS and time it")
    p.add_argument("out", type=Path, help="the convert output directory")
    p.add_argument("--bucket", required=True)
    p.add_argument("--prefix", default="bench/formats")
    p.add_argument("--formats", nargs="+", choices=FORMATS, default=list(FORMATS))
    p.add_argument("--workers", type=int, default=8)
    p.set_defaults(func=upload)

    p = sub.add_parser("load", help="load each format into BigQuery and read job statistics")
    p.add_argument("--bucket", required=True)
    p.add_argument("--prefix", default="bench/formats")
    p.add_argument("--dataset", default="glamira_bench")
    p.add_argument("--project")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--formats", nargs="+", choices=FORMATS, default=list(FORMATS))
    p.add_argument("--results", type=Path, default=Path("load_results.json"))
    p.set_defaults(func=load)

    p = sub.add_parser("contract", help="where each format notices a contract break; schema without a contract")
    p.add_argument("sample", type=Path, help="one part of an export, Parquet or Avro (a real row is taken from it)")
    p.add_argument("--bucket", help="also run the BigQuery checks (needs the uploaded formats)")
    p.add_argument("--prefix", default="bench/formats")
    p.add_argument("--dataset", default="glamira_bench")
    p.add_argument("--project")
    p.add_argument("--results", type=Path, default=Path("contract_results.json"))
    p.set_defaults(func=contract)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
