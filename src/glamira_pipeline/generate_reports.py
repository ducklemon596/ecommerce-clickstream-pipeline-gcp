"""Generate separate Phase 0 exploration, schema, and quality reports."""
from __future__ import annotations

import argparse
import ipaddress
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from glamira_pipeline.sample_data import DEFAULT_REPORT_DIR, DEFAULT_SAMPLE, read_sample

# These types are stable enough to check from the observed BSON structure. For
# fields without an agreed contract, the report shows type distributions instead
# of labeling a type as invalid.
EXPECTED_TYPES: dict[str, tuple[type, ...]] = {
    "collection": (str,),
    "time_stamp": (int,),
    "ip": (str,),
    "current_url": (str,),
    "referrer_url": (str,),
    "product_id": (str,),
    "cart_products": (list,),
}
MAX_DOCUMENTS = 100_000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE, help="Extracted BSON sample")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--max-documents", type=int, default=MAX_DOCUMENTS, help=f"Maximum rows to read (max {MAX_DOCUMENTS:,})")
    args = parser.parse_args()

    if args.max_documents > MAX_DOCUMENTS:
        parser.error(f"--max-documents cannot exceed {MAX_DOCUMENTS:,}")

    try:
        documents = read_sample(args.sample, args.max_documents)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
    if not documents:
        parser.error(f"No BSON documents found in {args.sample}")

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    reports = {
        "data_exploration_report.md": build_overview(documents, args.sample, generated_at),
        "schema_null_report.md": build_schema_report(documents, args.sample, generated_at),
        "data_quality_report.md": build_quality_report(documents, args.sample, generated_at),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in reports.items():
        (args.output_dir / filename).write_text(content, encoding="utf-8")
        print(f"Wrote {args.output_dir / filename}")


def build_overview(documents: list[dict[str, Any]], sample: Path, generated_at: str) -> str:
    event_counts = Counter(_event_name(doc) for doc in documents)
    fields = sorted({field for doc in documents for field in doc})
    type_counts: dict[str, Counter[str]] = {
        field: Counter(_type_name(doc[field]) for doc in documents if field in doc)
        for field in fields
    }
    timestamps = [doc.get("time_stamp") for doc in documents]
    timestamps = [value for value in timestamps if isinstance(value, (int, float)) and not isinstance(value, bool)]
    date_values = [datetime.fromtimestamp(value, tz=timezone.utc) for value in timestamps]
    ips = {doc["ip"] for doc in documents if isinstance(doc.get("ip"), str) and doc["ip"]}

    lines = _report_header("Data Exploration Report", sample, len(documents), generated_at)
    lines += [
        "## Overview",
        "",
        f"- Records profiled: {len(documents):,}",
        f"- Top-level fields: {len(fields)}",
        f"- Event types: {len(event_counts)}",
        f"- Unique non-empty IPs: {len(ips):,} (count only; values omitted)",
        f"- Timestamp range (interpreted as Unix seconds, UTC): {_format_date(min(date_values) if date_values else None)} to {_format_date(max(date_values) if date_values else None)}",
        "",
        "## Rows by event type",
        "",
        "| Event type | Rows | Share |",
        "|---|---:|---:|",
    ]
    for event, count in event_counts.most_common():
        lines.append(f"| {_escape(event)} | {count:,} | {count / len(documents) * 100:.2f}% |")
    lines += ["", "## Top-level fields and observed BSON types", "", "| Field | Present rows | Types among present values |", "|---|---:|---|"]
    for field in fields:
        present = sum(field in doc for doc in documents)
        observed_types = ", ".join(f"{name}: {count:,}" for name, count in type_counts[field].most_common())
        lines.append(f"| `{field}` | {present:,}/{len(documents):,} | {_escape(observed_types)} |")
    lines += ["", "No document values are included in this report.", ""]
    return "\n".join(lines)


def build_schema_report(documents: list[dict[str, Any]], sample: Path, generated_at: str) -> str:
    all_fields = sorted({field for doc in documents for field in doc})
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for doc in documents:
        groups[_event_name(doc)].append(doc)

    lines = _report_header("Schema and NULL Report", sample, len(documents), generated_at)
    lines += [
        "## How values are classified",
        "",
        "- **Missing**: the key is absent from a BSON document.",
        "- **Explicit null**: the key exists and its BSON value is null (`None`).",
        "- **Empty**: an empty string, list, or object.",
        "- **Populated**: present, non-null, and non-empty.",
        "- **Invalid type**: checked only for fields with a provisional expected type listed below. Other fields show their observed types without guessing a contract.",
        "",
        "Provisional type checks: " + ", ".join(
            "`" + field + "` → " + "/".join(t.__name__ for t in expected)
            for field, expected in EXPECTED_TYPES.items()
        ) + ".",
        "",
        "## Field states across the full sample",
        "",
        "| Field | Missing | Explicit null | Empty | Populated | Invalid type |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    always_populated: list[str] = []
    for field in all_fields:
        states = Counter()
        expected = EXPECTED_TYPES.get(field)
        for doc in documents:
            if field not in doc:
                states["missing"] += 1
                continue
            value = doc[field]
            if value is None:
                states["explicit null"] += 1
            elif _is_empty(value):
                states["empty"] += 1
            elif expected and not _matches_expected_type(value, expected):
                states["invalid type"] += 1
            else:
                states["populated"] += 1
        if states["populated"] == len(documents):
            always_populated.append(field)
        lines.append(
            f"| `{field}` | {states['missing']} | {states['explicit null']} | {states['empty']} | "
            f"{states['populated']} | {states['invalid type']} |"
        )
    lines += [
        "",
        "Always populated in this sample: " + (", ".join(f"`{field}`" for field in always_populated) or "none") + ".",
        "",
        "## Per-event field presence and NULL patterns",
        "",
    ]
    for event, event_docs in sorted(groups.items()):
        lines += [f"### `{event}` ({len(event_docs):,} rows)", "", "| Field | Missing | Explicit null | Empty | Populated | Invalid type | Observed types |", "|---|---:|---:|---:|---:|---:|---|"]
        for field in all_fields:
            state_counts: Counter[str] = Counter()
            types: Counter[str] = Counter()
            expected = EXPECTED_TYPES.get(field)
            for doc in event_docs:
                if field not in doc:
                    state_counts["missing"] += 1
                    continue
                value = doc[field]
                if value is None:
                    state_counts["explicit null"] += 1
                elif _is_empty(value):
                    state_counts["empty"] += 1
                elif expected and not _matches_expected_type(value, expected):
                    state_counts["invalid type"] += 1
                else:
                    state_counts["populated"] += 1
                types[_type_name(value)] += 1
            type_text = ", ".join(f"{name}: {count}" for name, count in types.most_common()) or "—"
            lines.append(
                f"| `{field}` | {state_counts['missing']} | {state_counts['explicit null']} | "
                f"{state_counts['empty']} | {state_counts['populated']} | {state_counts['invalid type']} | {type_text} |"
            )
        lines.append("")
    lines += [
        "## Interpretation",
        "",
        "Field sparsity differs by event type in this sample, which is consistent with a schema-on-read event model. Treat missing fields on event types that do not use them as potentially expected; confirm semantics with the event producer before calling them defects.",
        "",
        "Some fields can contain both missing values and explicit BSON nulls. The two states are reported separately. Type checks are provisional and should be replaced with a documented source contract when available.",
        "",
    ]
    return "\n".join(lines)


def build_quality_report(documents: list[dict[str, Any]], sample: Path, generated_at: str) -> str:
    total = len(documents)
    id_counts = Counter(_type_aware_key(doc.get("_id")) for doc in documents if "_id" in doc)
    duplicate_id_groups = sum(count > 1 for count in id_counts.values())
    duplicate_id_excess = sum(count - 1 for count in id_counts.values() if count > 1)

    ip_values = [doc.get("ip") for doc in documents]
    nonempty_ips = [value for value in ip_values if isinstance(value, str) and value.strip()]
    valid_ip_count = sum(_valid_ip(value) for value in nonempty_ips)
    ip_missing = sum("ip" not in doc for doc in documents)
    ip_null = sum("ip" in doc and doc["ip"] is None for doc in documents)
    ip_empty = sum("ip" in doc and _is_empty(doc["ip"]) for doc in documents)

    pairs = Counter(
        (_type_aware_key(doc["ip"]), _type_aware_key(doc["time_stamp"]))
        for doc in documents
        if doc.get("ip") is not None and doc.get("time_stamp") is not None
    )
    duplicate_pair_groups = sum(count > 1 for count in pairs.values())
    duplicate_pair_excess = sum(count - 1 for count in pairs.values() if count > 1)

    timestamp_values = [doc.get("time_stamp") for doc in documents]
    valid_timestamps = [value for value in timestamp_values if isinstance(value, (int, float)) and not isinstance(value, bool)]
    now_epoch = datetime.now(timezone.utc).timestamp()
    future_count = sum(value > now_epoch for value in valid_timestamps)
    invalid_timestamp_count = sum(
        "time_stamp" not in doc or doc["time_stamp"] is None or not isinstance(doc["time_stamp"], (int, float)) or isinstance(doc["time_stamp"], bool)
        for doc in documents
    )

    currencies: Counter[str] = Counter()
    checkout_items = 0
    for doc in documents:
        if doc.get("collection") != "checkout_success":
            continue
        cart = doc.get("cart_products")
        if isinstance(cart, list):
            for item in cart:
                if isinstance(item, dict):
                    checkout_items += 1
                    currency = item.get("currency")
                    if currency is not None and str(currency).strip():
                        currencies[str(currency)] += 1

    high_null_fields = []
    for field in sorted({key for doc in documents for key in doc}):
        absent_or_null = sum(field not in doc or doc[field] is None for doc in documents)
        if absent_or_null / total > 0.5:
            high_null_fields.append((field, absent_or_null, absent_or_null / total * 100))

    lines = _report_header("Data Quality Report", sample, total, generated_at)
    lines += [
        "## Summary of checks",
        "",
        "| Check | Result | Interpretation / action |",
        "|---|---|---|",
        f"| Duplicate `_id` values | {duplicate_id_groups:,} duplicate groups; {duplicate_id_excess:,} excess rows | Review if nonzero; `_id` is expected to identify a document. |",
        f"| Duplicate `(ip, time_stamp)` pairs | {duplicate_pair_groups:,} groups; {duplicate_pair_excess:,} excess rows | Not a unique event key: timestamps have second-level granularity and many events can share a second. |",
        f"| Future timestamps | {future_count:,}/{len(valid_timestamps):,} valid numeric timestamps | Review any future-dated rows. |",
        f"| Missing/null/empty `ip` | {ip_missing:,} missing; {ip_null:,} null; {ip_empty:,} empty | IP coverage denominator is all sampled events. |",
        f"| Valid IP format | {valid_ip_count:,}/{len(nonempty_ips):,} non-empty string IP values | Syntax check only; no geolocation or routability claim. |",
        f"| Currency coverage in checkout cart items | {sum(currencies.values()):,}/{checkout_items:,} items with currency | Multiple currency codes/symbols require normalization before cross-market revenue comparison. |",
        "| Negative or unusually large revenue | Not reliably assessed | Top-level checkout `price`/`currency` are absent in this sample; nested prices are locale-formatted strings. Parse with locale and currency rules before numeric checks. |",
        "",
        "## Fields missing or null in over 50% of sample rows",
        "",
    ]
    if high_null_fields:
        lines += ["| Field | Missing or explicit null | Rate |", "|---|---:|---:|"]
        lines += [f"| `{field}` | {count:,}/{total:,} | {rate:.1f}% |" for field, count, rate in high_null_fields]
    else:
        lines.append("None.")
    currency_text = ", ".join(f"`{name}` ({count})" for name, count in currencies.most_common()) or "No nested checkout currencies found."
    lines += [
        "",
        "## Currency values observed in checkout items",
        "",
        currency_text,
        "",
        "## Limitations and full-data risks",
        "",
        f"- This is a sequential prefix sample of {total:,} documents from a BSON dump, not a random or population-representative sample.",
        "- Duplicate-pair results can be inflated by timestamp precision and event volume; do not deduplicate on `(ip, time_stamp)`.",
        "- Revenue sanity checks need a confirmed nested cart schema, decimal parsing rules, and currency-specific thresholds.",
        "- Counts and quality rates must be recomputed on the full collection before making population-wide claims.",
        "",
    ]
    return "\n".join(lines)


def _report_header(title: str, sample: Path, count: int, generated_at: str) -> list[str]:
    source_line = (
        "- Source: `glamira_ubl_oct2019_nov2019.tar.gz` → `dump/countly/summary.bson`."
        if sample.resolve() == DEFAULT_SAMPLE.resolve()
        else "- Source archive: not recorded for this custom sample path."
    )
    return [
        f"# {title}",
        "",
        f"- Generated at (UTC): {generated_at}",
        f"- Input sample: `{sample.name}`",
        source_line,
        f"- Rows analyzed: {count:,}",
        "- Extraction and sampling: first documents from the BSON member (sequential, non-random); no full archive extraction.",
        "- Scope: local sample only; do not interpret as full-dataset statistics.",
        "",
    ]


def _event_name(document: dict[str, Any]) -> str:
    value = document.get("collection")
    return str(value) if value is not None else "<missing/null collection>"


def _is_empty(value: Any) -> bool:
    return isinstance(value, (str, list, dict)) and len(value) == 0


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return type(value).__name__


def _matches_expected_type(value: Any, expected: tuple[type, ...]) -> bool:
    if isinstance(value, bool) and int in expected and bool not in expected:
        return False
    return isinstance(value, expected)


def _type_aware_key(value: Any) -> tuple[str, str]:
    return (_type_name(value), repr(value))


def _valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def _format_date(value: datetime | None) -> str:
    return value.isoformat() if value else "not available"


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
