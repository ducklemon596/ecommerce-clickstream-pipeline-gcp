"""Present additional measured research checks without finalizing policy choices."""
from __future__ import annotations

import json
from pathlib import Path

from profile import records


def load_checks(directory: Path | None) -> dict:
    """Load optional private follow-up metrics and point/window probes."""
    if directory is None:
        return {}
    result = {}
    for key, filename in (("reference", "reference_comparison.json"), ("cross", "cross_checks.json"), ("timing", "timing_results.json")):
        path = directory / filename
        if path.exists():
            result[key] = json.loads(path.read_text())
    for key, filename in (("points", "targeted_points.jsonl"), ("sequences", "bounded_sequence_probes.jsonl")):
        path = directory / filename
        if path.exists():
            result[key] = list(records(path))
    return result


def event_checks(event: str, checks: dict, table) -> str:
    """Render follow-up metrics with their own item/event denominators."""
    parts = []
    cross = checks.get("cross", {})
    timing = checks.get("timing")
    if event == "select_product_option" and timing:
        rows = [[key, value, f"{timing['weighted_conflict_fractions'][key]:.2%}"] for key, value in timing["conflict_outcomes"].items()]
        parts.append("### Extended timing investigation requested by the user\n\n" + table(
            ["Conflict-cohort outcome", "Anchors", "Stratum-weighted share"], rows) +
            "\n\n120 conflict anchors plus 40 controls were examined in bounded device/product/store contexts ordered by time_stamp. "
            "Support means a visible chosen-key transition, not proof of a complete post-selection configuration. "
            "Counterevidence to prompt URL catch-up does not prove the selected value invalid. Details, examples and conditions are in [SELECTION_TIMING.md](../SELECTION_TIMING.md). "
            "Preserving snapshot and delta is approved; any inference branch remains a proposal.")
    routes = cross.get("routes", {}).get(event)
    if routes:
        parts += ["### Targeted route-association comparisons within the pool\n\n" + table(
            ["Route check (event count)", "Observed"], sorted(routes["events"].items())),
            table(["Path-segment key", "Occurrences"], sorted(routes["path_keys"].items())),
            "A matching `/id/` segment strengthens source-product association, not the claim that route filters are the product's complete settings. "
            "A referrer pair can agree on one dimension and disagree on another; those event counters overlap. "
            "Price/category/list facets are not automatically crawl options. No precedence or path-to-query rule is approved."]
    if event in {"select_product_option", "select_product_option_quality"}:
        labels = {key.split(":", 1)[1]: value for key, value in cross.get("labels", {}).items()
                  if key.startswith(event + ":")}
        rows = []
        for label, values in labels.items():
            overlap = "; ".join(f"{key.split(':', 1)[1]}={count}" for key, count in values.items() if key.startswith("unique_value_overlap:"))
            if label not in {"alloy", "diamond", "stone", "stone2", "stone3", "stone4"}:
                rows.append([label, values.get("items", 0), values.get("nonempty_value_label", 0), overlap or "none", values.get("no_value_overlap", 0)])
        if rows:
            parts += ["### Candidate label aliases — hypotheses only\n\n" + table(
                ["Original label", "Items", "Nonempty value labels", "Unique same-value URL key overlap", "No overlap"], rows),
                "Same-value overlap is not proof of an alias: several stone dimensions can share one value. "
                "Do not map a translated/misspelled label from spelling alone."]
        if event == "select_product_option":
            parts.append("Proposed label handling: when a `pear` value is already corroborated by an explicit `pearl` URL pair, retain that observed URL pair independently; do not manufacture a universal alias. "
                         "The observed nonempty `stonetow` values had no exact candidate-URL overlap in this pool, so keep that label unresolved rather than autocorrecting its spelling.")
    if event == "select_product_option_quality" and cross.get("quality"):
        values = {**cross["quality"]}
        for key in ("quality_named_query_key", "grade_literal_in_candidate_url_value"):
            values.setdefault(key, 0)
        parts += ["### URL representation of quality\n\n" + table(["Measured quality check", "Count"], sorted(values.items())),
                  "Repeated-URL groups compare the redacted URL, product/store and option/value label; campaign values were removed before transfer. "
                  "Different grade observations for the same group are a counterexample to URL-only completeness. No inference about website defaults or accepted grade parameters follows."]
    reference = checks.get("reference", {}).get("by_event", {}).get(event)
    if reference:
        parts += ["### ID-reference sensitivity check\n\n" + table(["Item/choice measurement", "Count"], sorted(reference.items())),
                  "This compares internal IDs with corroborated selector URL pairs in the same sample. "
                  "Witnesses and targets are not independent; no holdout or global reference was validated. "
                  "`items_all_usable_ids_matched` does not mean all configuration dimensions are known. "
                  "Ambiguous keys are rejected by this diagnostic, not resolved by majority voting. Numeric/string comparison is a research scenario pending approval."]
    return "\n\n".join(parts)


def event_probes(event: str, checks: dict) -> str:
    """Summarize indexed follow-ups with source IDs, never identity-field values."""
    parts = []
    point_ids = [document["_id"] for document in checks.get("points", []) if document.get("collection") == event]
    if point_ids:
        parts.append("Indexed source point reads reverified: " + ", ".join(f"`{value}`" for value in point_ids) + ". These are separate from the random-pool denominators.")
    for probe in checks.get("sequences", []):
        if probe.get("collection") != event:
            continue
        summary = {key: probe[key] for key in ("_id", "scanned", "matched_count", "anchor_current_url")}
        # Show nearest observations by the measured timestamp difference. The
        # source lookup order itself is not claimed as event-time ordering.
        summary["nearby_observations"] = probe.get("matches", [])[:3]
        parts.append("### Bounded device/product/store context\n\n```json\n" + json.dumps(summary, ensure_ascii=False, indent=2) + "\n```\n\n"
                     "Read at most 1,000 predecessors and 1,000 successors through `_id_`; compare device ID, product and store on the VM, without returning the device value. "
                     "The source time_stamp gives the displayed relative seconds. This is not a verified or complete session, and second-level ties cannot establish order.")
    if event == "select_product_option_quality":
        for probe in checks.get("sequences", []):
            grades = [entry for entry in probe.get("matches", []) if entry.get("collection") == event]
            if len(grades) > 1:
                parts.append("### Different quality observations with an unchanged configuration URL\n\n```json\n" +
                    json.dumps(grades[:2], ensure_ascii=False, indent=2) + "\n```\n\n"
                    "These nearby records match device/product/store inside the bounded probe. Grade changes are observable even when the URL option subset is unchanged. "
                    "No user/device identifier is published, and this does not establish a complete session contract.")
                break
    return "\n\n".join(parts)


def shared_findings(checks: dict) -> str:
    """Write the strongest measured cross-event limitations and traceability."""
    reference = checks.get("reference", {})
    if not reference:
        return ""
    ambiguous, total = reference["ambiguous_reference_keys"], reference["reference_keys"]
    text = f"""
## Additional measured findings

A strict reference sensitivity check found **{ambiguous:,}/{total:,} ({ambiguous / total:.2%})** product/store/option/value-ID keys associated with more than one URL key/token, even though each witness's selected value agreed with its own URL. Therefore ID equality alone cannot supply a trusted slug mapping. This may reflect stale identifiers, catalog/instrumentation changes or another unverified behavior; the cause was not established.

One point-verified counterexample: product `85792`, store `6`, option ID `57620`, value ID `307365` appeared with `red-375` at `_id=5ebfc2d166936336eea1ac4b` and `white-platin` at `_id=5ed3c87978aa7636ca4d7b0e`. These are substantive different tokens, not a capitalization-only alias. A unique mapping inside this sample also does not prove a universal mapping.

Nine exact `_id` point reads verified the user-supplied add-to-cart record and important counterexamples. Three additional indexed context probes examined at most **6,000 neighboring records** combined. Raw device values stayed on the VM; nine point-read records had a nonempty device_id, one had a nonempty user_id_db, and none had a nonempty session_id. These targeted counts cannot be extrapolated.

For selector anchor `5e9a9ca39fade236dccec573`, the URL said `alloy=white-585` while the selected field said `red-585`; a same-device/product/store observation 7 seconds later carried `alloy=red-585`. This supports a stale-URL hypothesis for that example, not a universal overlay rule. Another probe found multiple different selected alloys while the URL remained queryless. Grade selections also changed with the same URL subset. See the selector and quality event files for traceable excerpts.

The reference check emits aggregate measurements and a few witness IDs, not a lookup table or reconstructed configuration dataset. Its sample/reference overlap makes potential mapping coverage optimistic. Private follow-up artifacts are `reference_comparison.json`, `cross_checks.json`, `targeted_points.jsonl`, and `bounded_sequence_probes.jsonl` beside the captured pool. Their records are not added to random-sample denominators.
"""
    if checks.get("timing"):
        text += "\nThe subsequent user-requested [stratified timing study](SELECTION_TIMING.md) adds 160 exact anchors and 320,000 bounded neighboring-record reads. These are separate research cohorts and are not included in the 300,000-event random-pool denominators.\n"
    return text
