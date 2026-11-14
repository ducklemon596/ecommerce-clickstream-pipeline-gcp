"""Serialize a schema profile to JSON and render it as a Markdown report.

The report contains field names, counts and type names only; no field values
are written, so it carries no IP addresses, emails or other event content.
"""
from __future__ import annotations

from html import escape
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from glamira_pipeline.profiling.schema import SchemaProfile, TypeProfile, container_count, missing_count


def _rate(count: int, total: int) -> str:
    if not total:
        return "n/a"
    value = 100 * count / total
    return f"{value:.2f}%" if value in (0, 100) or round(value, 2) not in (0, 100) else f"{value:.4f}%"


def _cell(text: str) -> str:
    return escape(text, quote=False).replace("|", "\\|").replace("\n", " ")


def _types(stats_types: dict[str, int]) -> str:
    return ", ".join(f"{name} {count:,}" for name, count in sorted(stats_types.items(), key=lambda kv: (-kv[1], kv[0])))


def profile_to_dict(profile: SchemaProfile, metadata: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-serializable view: metadata plus per-type, per-path counts."""
    types = {}
    for name, tp in sorted(profile.types.items()):
        types[name] = {
            "events": tp.events,
            "dropped_paths": tp.dropped_paths,
            "truncated_arrays": tp.truncated_arrays,
            "depth_limited": tp.depth_limited,
            "paths": {path: {"containers": container_count(tp, path), "present": s.present,
                             "missing": missing_count(tp, path), "null": s.null, "empty": s.empty,
                             "types": dict(s.types)}
                      for path, s in sorted(tp.paths.items())},
        }
    return {"metadata": metadata, "documents": profile.documents, "event_types": types}


def _type_section(name: str, tp: TypeProfile, total: int) -> list[str]:
    lines = [f"## `{_cell(name)}`", "",
             f"{tp.events:,} sampled events ({_rate(tp.events, total)} of the sample).", ""]
    bounds = [f"{label} {count:,}" for label, count in (("paths dropped", tp.dropped_paths),
                                                        ("arrays truncated", tp.truncated_arrays),
                                                        ("values beyond depth limit", tp.depth_limited)) if count]
    if bounds:
        lines += ["Profiling bounds reached: " + ", ".join(bounds) + ".", ""]
    lines += ["| Path | Containers | Present | Missing | Null | Empty | BSON types |",
              "|---|---:|---:|---:|---:|---:|---|"]
    for path, s in sorted(tp.paths.items()):
        containers = container_count(tp, path)
        lines.append(f"| `{_cell(path)}` | {containers:,} | {_rate(s.present, containers)} | "
                     f"{_rate(missing_count(tp, path), containers)} | {_rate(s.null, containers)} | "
                     f"{_rate(s.empty, containers)} | {_cell(_types(s.types))} |")
    return lines + [""]


def render_markdown(profile: SchemaProfile, metadata: dict[str, Any]) -> str:
    """Render the profile as Markdown: method, event-type overview, then one table per type."""
    total = profile.documents
    lines = [
        "# Schema profile — `{}`".format(_cell(metadata["namespace"])), "",
        f"- Observed (UTC): {metadata['observed_at']}.",
        f"- Method: {_cell(metadata['method'])}",
        f"- Documents profiled: **{total:,}** of {metadata['requested']:,} requested; "
        f"collection estimate {metadata['collection_estimate']:,}.",
        f"- Git commit: `{metadata.get('git_sha') or 'unknown'}`.", "",
        "Rates are relative to **containers**: events of the type for a top-level field, array elements "
        "for `a[]`, object elements of `a[]` for `a[].b`. *Missing* = key absent; *Null* = explicit BSON "
        "null; *Empty* = empty/whitespace string, empty array or empty object. Present includes null and "
        "empty values. Event types are labelled by `collection`; missing or non-string values are "
        "`<missing>`.", "",
        "| Event type | Sampled events | Share | Paths |", "|---|---:|---:|---:|",
    ]
    ordered = sorted(profile.types.items(), key=lambda kv: (-kv[1].events, kv[0]))
    lines += [f"| `{_cell(name)}` | {tp.events:,} | {_rate(tp.events, total)} | {len(tp.paths):,} |"
              for name, tp in ordered]
    lines.append("")
    for name, tp in ordered:
        lines += _type_section(name, tp, total)
    return "\n".join(lines)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp") as tmp:
        tmp.write(text)
        temp_path = Path(tmp.name)
    os.replace(temp_path, path)


def write_outputs(profile: SchemaProfile, metadata: dict[str, Any], markdown_path: Path,
                  json_path: Path) -> None:
    """Write the Markdown report and the JSON counts, each replaced atomically."""
    _atomic_write(json_path, json.dumps(profile_to_dict(profile, metadata), indent=2) + "\n")
    _atomic_write(markdown_path, render_markdown(profile, metadata))
