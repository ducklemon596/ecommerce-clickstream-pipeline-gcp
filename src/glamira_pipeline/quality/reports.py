"""Render and publish the sample data-quality summary and focused reports."""
from __future__ import annotations

from collections import Counter
from html import escape
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from glamira_pipeline.quality.assessment import Assessment
from glamira_pipeline.quality.duplicates import duplicate_summary
from glamira_pipeline.quality.transactions import CurrencyCounts

DETAIL_FILES = ("nulls.md", "duplicates.md", "timestamps.md", "revenue.md", "currencies.md", "ip_addresses.md")


def percentage(count: int, total: int) -> str:
    """Format a count as a percentage string; return “n/a” when total is zero.

    Args:
        count: Number of matching records.
        total: Number of records in the denominator.
    """
    if not total:
        return "n/a"
    value = 100 * count / total
    precision = 4 if value not in (0, 100) and round(value, 2) in (0, 100) else 2
    return f"{value:.{precision}f}%"


def _safe(value: str) -> str:
    """Return a string escaped for use in a Markdown table.

    Args:
        value: Untrusted display text; newlines and table separators are escaped.
    """
    return escape(value, quote=False).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def sample_provenance(sample: Path) -> str:
    """Return a safe sampling-method description for a JSON sample path.

    Use its adjacent extraction metadata only when the recorded size matches;
    missing, invalid, or unrecognized metadata yields an unverified description.
    """
    metadata_path = sample.with_suffix(".metadata.json")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("outputs", {}).get(sample.name) != sample.stat().st_size:
            return "Selection method unverified: metadata does not match sample size."
        method = metadata.get("sampling_method", "Unknown")
        # The extractor emits this fixed label; avoid publishing arbitrary sidecar text.
        if method != "sequential prefix (non-random)":
            return "Selection method unverified in extraction metadata."
        return "Sequential archive prefix (non-random); not representative of the full dataset."
    except (OSError, ValueError, TypeError, AttributeError):
        return "Selection method unverified: extraction metadata unavailable or invalid."


def _header(title: str, assessment: Assessment, sample: Path, provenance: str) -> list[str]:
    """Build the common report header as a list of Markdown lines.

    Args:
        title: Report title.
        assessment: Completed counters and generation time.
        sample: Input path; only its filename is displayed.
        provenance: Verified or unknown sampling-method description.
    """
    scope = "Input continues beyond the configured cap; only the prefix was assessed." if assessment.truncated else "Input ended within the configured cap."
    return [
        f"# {title}", "",
        f"- Sample: `{_safe(sample.name)}`; rows assessed: **{assessment.rows:,}**.",
        f"- Generated / future-time reference (UTC): {assessment.now.isoformat(timespec='seconds')}.",
        f"- Sampling: {provenance}",
        f"- Coverage: {scope}", "",
    ]


def _id_result(assessment: Assessment) -> tuple[str, int, int, int]:
    """Return the identifier label, usable count, duplicate groups, and excess rows.

    Args:
        assessment: Completed sample assessment; use for summary reporting.
    """
    data = assessment.duplicates
    if data.mongo_id_usable:
        groups, excess = duplicate_summary(data.mongo_ids)
        return "_id", data.mongo_id_usable, groups, excess
    return "_id (unavailable)", 0, 0, 0


def render_summary(assessment: Assessment, sample: Path, provenance: str) -> str:
    """Return the Markdown summary linking to all six detail reports.

    Args:
        assessment: Completed sample assessment.
        sample: Input JSON path, used for its filename.
        provenance: Description of the sampling method.
    """
    identifier, usable, groups, excess = _id_result(assessment)
    pairs, pair_excess = duplicate_summary(assessment.duplicates.pairs)
    t, tx, ip = assessment.timestamps, assessment.transactions, assessment.ips
    valid_ips = ip.ipv4 + ip.ipv6
    negative_signs = tx.price_string_negative_sign + tx.price_numeric_negative
    currencies = len(set(tx.top_level_currencies.values) | set(tx.cart_item_currencies.values))
    lines = _header("Data Quality Report — Summary", assessment, sample, provenance)
    lines += [
        "| Check | Sample result | Details |", "|---|---|---|",
        f"| NULL analysis | {len(assessment.nulls.present):,} top-level fields measured; high rates require event context | [NULL report](data_quality/nulls.md) |",
        f"| Duplicate identifiers | {identifier}: {groups:,} groups, {excess:,} excess rows ({usable:,} usable IDs) | [Duplicates](data_quality/duplicates.md) |",
        f"| Duplicate IP/timestamp pairs | {pairs:,} groups, {pair_excess:,} excess rows; not necessarily duplicate events | [Duplicates](data_quality/duplicates.md) |",
        f"| Timestamps | {t.future:,} future, {t.invalid:,} invalid, {t.missing:,} missing/null | [Timestamps](data_quality/timestamps.md) |",
        f"| Checkout price signs | {negative_signs:,} leading-negative strings or negative numeric prices in {tx.checkout_items:,} cart items from {tx.checkout_events:,} checkout-success events | [Revenue](data_quality/revenue.md) |",
        f"| Currency values | {currencies:,} distinct currency-like values across top-level and cart items | [Currencies](data_quality/currencies.md) |",
        f"| IP syntax | {valid_ips:,} valid, {ip.invalid_format:,} invalid format, {ip.invalid_type:,} invalid type | [IP addresses](data_quality/ip_addresses.md) |",
        "", "Order-level revenue and unusually large amounts are **not assessed**: confirmed amount semantics, locale parsing, and thresholds are unavailable.",
        "", "These observations describe this sample only. Empty values, explicit BSON nulls, and missing keys are separate categories.", "",
    ]
    return "\n".join(lines)


def render_nulls(a: Assessment, sample: Path, provenance: str) -> str:
    """Return the Markdown report for top-level missing and BSON-null counts.

    Args:
        a: Completed assessment.
        sample: Input JSON path, used for its filename.
        provenance: Description of the sampling method.
    """
    lines = _header("NULL Analysis", a, sample, provenance)
    lines += [
        "Missing keys and explicit BSON nulls count as NULL; empty strings/arrays/objects do not. This is the existing top-level calculation, with no nested-field expansion. A rate above 50% is flagged for review, not automatically treated as a defect: event types have different payloads.", "",
        "| Field | Missing | BSON null | Missing + null | Rate | Review |", "|---|---:|---:|---:|---:|---|",
    ]
    ordered = sorted(a.nulls.present, key=lambda key: (-(a.rows - a.nulls.present[key] + a.nulls.explicit_null[key]), key))
    for key in ordered:
        missing = a.rows - a.nulls.present[key]
        explicit = a.nulls.explicit_null[key]
        null_count = missing + explicit
        lines.append(f"| `{_safe(key)}` | {missing:,} | {explicit:,} | {null_count:,} | {percentage(null_count, a.rows)} | {'>50%' if null_count * 2 > a.rows else '—'} |")
    lines += ["", "Percentages use all sampled events, so a field relevant to only one event may be mostly absent by design.", ""]
    return "\n".join(lines)


def render_duplicates(a: Assessment, sample: Path, provenance: str) -> str:
    """Return a Markdown duplicate report from aggregate sample counters.

    Args:
        a: Completed assessment containing type-aware duplicate counters.
        sample: Input sample path, used only for its filename.
        provenance: Description of the sample selection method.

    Returns:
        A Markdown report containing aggregate counts only.
    """
    d = a.duplicates
    groups, excess = duplicate_summary(d.pairs)
    repeated_rows = sum(count for count in d.pairs.values() if count > 1)
    lines = _header("Duplicate Detection", a, sample, provenance)
    lines += ["Identifier check uses `_id`. Missing, null, and blank IDs are excluded; counts are type-aware.", "",
              "| Key | Usable rows | Skipped rows | Duplicate groups | Excess rows |", "|---|---:|---:|---:|---:|"]
    for label, count, counter in (("_id", d.mongo_id_usable, d.mongo_ids), ("(ip, time_stamp)", d.pair_usable, d.pairs)):
        key_groups, key_excess = duplicate_summary(counter)
        lines.append(f"| `{label}` | {count:,} | {a.rows - count:,} | {key_groups:,} | {key_excess:,} |")
    lines += [
        "", f"The {groups:,} repeated IP/timestamp groups contain **{repeated_rows:,} rows** in total: {groups:,} first occurrences plus {excess:,} excess rows.",
        f"Of those groups, {len(d.mixed_event_groups):,} include multiple event-type labels and {groups - len(d.mixed_event_groups):,} have one observed label. Missing or invalid labels share one placeholder.",
        "", "## Repeated pairs by IP version", "",
        "Addresses are parsed only for classification. Pair grouping preserves the original exact IP string and BSON timestamp; equivalent spellings are not merged. IPv4-mapped IPv6 addresses are classified as IPv6.", "",
        "| IP version | Duplicate groups | Rows in groups | Excess rows |", "|---|---:|---:|---:|",
    ]
    for version, label in (("ipv4", "IPv4"), ("ipv6", "IPv6"), ("invalid", "Invalid address")):
        keys = [key for key, observed in d.pair_versions.items() if observed == version]
        rows = sum(d.pairs[key] for key in keys)
        lines.append(f"| {label} | {len(keys):,} | {rows:,} | {rows - len(keys):,} |")
    lines += ["", "## Group sizes", "", "| Rows per group | Groups | Rows in those groups |", "|---:|---:|---:|"]
    sizes = Counter(count for count in d.pairs.values() if count > 1)
    for size, frequency in sorted(sizes.items()):
        lines.append(f"| {size:,} | {frequency:,} | {size * frequency:,} |")
    if not sizes:
        lines.append("| — | 0 | 0 |")
    lines += ["", "Excess rows count repetitions after the first in each group. IP/timestamp pairs exclude missing, null, or blank IPs and missing/null timestamps. A shared IP and second can represent legitimate distinct actions; never deduplicate events solely on this pair. Raw IP examples are not retained.", ""]
    return "\n".join(lines)


def render_timestamps(a: Assessment, sample: Path, provenance: str) -> str:
    """Return the Markdown report for timestamp validity, range, and future values.

    Args:
        a: Completed assessment.
        sample: Input JSON path, used for its filename.
        provenance: Description of the sampling method.
    """
    t = a.timestamps
    lines = _header("Timestamp Validation", a, sample, provenance)
    lines += ["Numeric `time_stamp` values are interpreted as Unix seconds in UTC based on observed values; confirm units and meaning with the event producer. BSON dates are interpreted as UTC. A timestamp is future-dated if it is later than the report generation time.", "",
              "| Check | Result |", "|---|---:|",
              f"| Valid timestamps | {t.valid:,} |", f"| Missing or null timestamps | {t.missing:,} |",
              f"| Invalid or out-of-range timestamps | {t.invalid:,} |", f"| Future timestamps | {t.future:,} |",
              f"| Earliest valid (UTC) | {t.minimum.isoformat() if t.minimum else 'Not available'} |",
              f"| Latest valid (UTC) | {t.maximum.isoformat() if t.maximum else 'Not available'} |", "",
              "## Local time field", "",
              "`local_time` is parsed as a wall-clock string (`YYYY-MM-DD H:MM:SS`). Its timezone is unknown and may vary between records, so its range is not converted to UTC and future dates are not assessed.", "",
              "| Check | Result |", "|---|---:|",
              f"| Valid local times | {t.local_valid:,} |", f"| Missing or null local times | {t.local_missing:,} |",
              f"| Invalid local times | {t.local_invalid:,} |",
              f"| Earliest local time (timezone unknown) | {t.local_minimum.isoformat(sep=' ') if t.local_minimum else 'Not available'} |",
              f"| Latest local time (timezone unknown) | {t.local_maximum.isoformat(sep=' ') if t.local_maximum else 'Not available'} |", ""]
    return "\n".join(lines)


def render_revenue(a: Assessment, sample: Path, provenance: str) -> str:
    """Return the Markdown report for checkout item price-sign checks.

    Args:
        a: Completed assessment.
        sample: Input JSON path, used for its filename.
        provenance: Description of the sampling method.
    """
    t = a.transactions
    lines = _header("Checkout Price Sign Check", a, sample, provenance)
    lines += [
        "Only `checkout_success` events are considered. The check looks at `cart_products[].price`, which is an item price, not a verified order amount. For strings it detects a leading minus sign followed by a digit; it does not parse locale-dependent amounts or claim that every other string is nonnegative. Numeric values are checked directly.", "",
        "| Check | Result |", "|---|---:|",
        f"| Checkout-success events | {t.checkout_events:,} |",
        f"| Checkout events with missing/invalid cart | {t.checkout_missing_or_invalid_cart:,} |",
        f"| Object cart items | {t.checkout_items:,} |",
        f"| Non-object checkout cart items | {t.checkout_malformed_items:,} |",
        f"| Nonempty price strings | {t.price_string:,} |",
        f"| Strings with leading negative sign | {t.price_string_negative_sign:,} |",
        f"| Strings without a recognizable leading number | {t.price_string_no_leading_number:,} |",
        f"| Numeric prices / negative numeric prices | {t.price_numeric:,} / {t.price_numeric_negative:,} |",
        f"| Missing / null / empty / invalid prices | {t.price_missing:,} / {t.price_null:,} / {t.price_empty:,} / {t.price_invalid:,} |",
        f"| Checkout events with top-level `order_amount` present / non-null | {t.root_order_amount_present:,} / {t.root_order_amount_nonnull:,} |",
        "", "**Not assessed:** order-level revenue and unusually large amounts. The sample uses locale-formatted item-price strings; currency-specific parsing, price semantics, and business thresholds are not confirmed.", "",
    ]
    return "\n".join(lines)


def _currency_context(label: str, counts: CurrencyCounts, total: int) -> list[str]:
    """Return one Markdown table row summarizing a currency-count context.

    Args:
        label: Display name for the context.
        counts: Currency values and invalid/missing counters.
        total: Number of events or cart items in the context.
    """
    return [f"| {label} | {total:,} | {sum(counts.values.values()):,} | {counts.missing:,} | {counts.null:,} | {counts.empty:,} | {counts.invalid:,} |"]


def render_currencies(a: Assessment, sample: Path, provenance: str) -> str:
    """Return the Markdown report for observed top-level and cart-item currencies.

    Args:
        a: Completed assessment.
        sample: Input JSON path, used for its filename.
        provenance: Description of the sampling method.
    """
    t = a.transactions
    top, cart = t.top_level_currencies, t.cart_item_currencies
    values = sorted(set(top.values) | set(cart.values))
    lines = _header("Currency Values", a, sample, provenance)
    lines += ["Top-level currency values are counted across all sampled events; nested currency values are counted across object items in every `cart_products` array. These are distinct contexts, so counts should not be added as event counts.", "",
              "| Value | Top-level events | Cart items |", "|---|---:|---:|"]
    lines += [f"| `{_safe(value).replace('`', 'ˋ')}` | {top.values[value]:,} | {cart.values[value]:,} |" for value in values]
    if not values:
        lines.append("| — | 0 | 0 |")
    lines += ["", "| Context | Rows/items | Nonempty values | Missing | Null | Empty | Invalid/redacted |", "|---|---:|---:|---:|---:|---:|---:|"]
    lines += _currency_context("Top level", top, a.rows)
    lines += _currency_context("Cart items", cart, t.cart_item_count)
    lines += ["", f"Non-object cart items excluded from currency checks: {t.malformed_cart_items:,}.", "", "Currency symbols can be ambiguous. Normalize currencies and confirm exchange-rate rules before comparing monetary values. Invalid or suspicious currency values are counted without exposing their contents.", ""]
    return "\n".join(lines)


def render_ips(a: Assessment, sample: Path, provenance: str) -> str:
    """Return the Markdown report for IP completeness and IPv4/IPv6 syntax.

    Args:
        a: Completed assessment.
        sample: Input JSON path, used for its filename.
        provenance: Description of the sampling method.
    """
    ip = a.ips
    valid = ip.ipv4 + ip.ipv6
    nonnull = a.rows - ip.missing - ip.null
    usable = ip.ipv4 + ip.ipv6 + ip.invalid_format
    field_names = ", ".join(f"`{_safe(name)}`: {count:,}" for name, count in sorted(ip.field_names.items()))
    lines = _header("IP Address Completeness and Format", a, sample, provenance)
    lines += [f"Field selected per event: {field_names}. If both fields exist, `ip` takes precedence. Raw addresses are not written to this report.", "",
              "| Check | Result |", "|---|---:|",
              f"| Non-null IP field (includes empty/invalid values) | {nonnull:,}/{a.rows:,} ({percentage(nonnull, a.rows)}) |",
              f"| Missing / BSON null / empty | {ip.missing:,} / {ip.null:,} / {ip.empty:,} |",
              f"| Invalid type | {ip.invalid_type:,} |", f"| Nonempty strings checked | {usable:,} |",
              f"| Valid IPv4 | {ip.ipv4:,} |", f"| Valid IPv6 | {ip.ipv6:,} |", f"| Invalid IP syntax | {ip.invalid_format:,} |",
              f"| Valid syntax among nonempty strings | {valid:,}/{usable:,} ({percentage(valid, usable)}) |", "",
              "This is a syntax check only; it does not verify routability, identity, or geolocation.", ""]
    return "\n".join(lines)


def write_reports(a: Assessment, sample: Path, output_dir: Path) -> list[Path]:
    """Write the summary and six reports, returning their output paths.

    Args:
        a: Completed assessment containing aggregate check results.
        sample: JSON sample path for provenance; no records are reread.
        output_dir: Directory receiving the summary and `data_quality/` folder.

    Raises:
        OSError: If a destination cannot be created or a report cannot be written.
    """
    provenance = sample_provenance(sample)
    detail_renderers = (render_nulls, render_duplicates, render_timestamps, render_revenue, render_currencies, render_ips)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Render everything before replacing any prior report; publish the summary last.
    with TemporaryDirectory(prefix=".quality-", dir=output_dir) as temporary:
        staging = Path(temporary)
        staged_details = staging / "data_quality"
        staged_details.mkdir()
        for filename, renderer in zip(DETAIL_FILES, detail_renderers):
            (staged_details / filename).write_text(renderer(a, sample, provenance), encoding="utf-8")
        summary = staging / "data_quality_report.md"
        summary.write_text(render_summary(a, sample, provenance), encoding="utf-8")
        detail_dir = output_dir / "data_quality"
        detail_dir.mkdir(exist_ok=True)
        targets = []
        for filename in DETAIL_FILES:
            target = detail_dir / filename
            (staged_details / filename).replace(target)
            targets.append(target)
        target_summary = output_dir / "data_quality_report.md"
        summary.replace(target_summary)
        return [target_summary, *targets]
