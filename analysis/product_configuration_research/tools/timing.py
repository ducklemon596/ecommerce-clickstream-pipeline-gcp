"""Research selector timing with stratified anchors and bounded device contexts."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
from statistics import median

from profile import records, url_facts


def draw_cohort(sample: Path, seed: int = 20261106) -> dict:
    """Select 120 conflicts by option stratum plus 20 missing-key/20 match controls.

    All conflicts must have one clear URL value and a nonempty selected value.
    Sampling oversamples rare keys, so overall conflict rates need stratum
    weighting. Returns source IDs and evidence labels only, not configurations.
    """
    conflicts, missing, controls = defaultdict(list), [], []
    for document in records(sample):
        if document.get("collection") != "select_product_option":
            continue
        url = url_facts(document, "current_url")
        choices = [choice for choice in document.get("option", []) if isinstance(choice, dict)
                   and isinstance(choice.get("option_label"), str) and choice.get("value_label")]
        different = [choice for choice in choices if choice["option_label"] in url["values"]
                     and choice["value_label"] not in url["values"][choice["option_label"]]]
        absent = [choice for choice in choices if choice["option_label"].lower() in {"alloy", "diamond", "stone2", "stone3"}
                  and choice["option_label"] not in url["values"]]
        if different:
            choice = different[0]
            if len(url["values"][choice["option_label"]]) == 1:
                conflicts[choice["option_label"]].append({"_id": document["_id"], "group": "conflict", "key": choice["option_label"]})
        elif absent:
            missing.append({"_id": document["_id"], "group": "missing_key", "key": absent[0]["option_label"]})
        elif len(choices) == 1:
            choice = choices[0]
            if choice["value_label"] in url["values"].get(choice["option_label"], set()):
                controls.append({"_id": document["_id"], "group": "match", "key": choice["option_label"]})
    populations = {key: len(values) for key, values in conflicts.items()}
    quotas = {key: min(10, count) for key, count in populations.items()}
    while sum(quotas.values()) < 120:
        candidates = [key for key in quotas if quotas[key] < populations[key]]
        if not candidates:
            raise ValueError("insufficient source conflicts for planned cohort")
        key = max(candidates, key=lambda name: populations[name] / (quotas[name] + 1))
        quotas[key] += 1
    rng = random.Random(seed)
    anchors = []
    for key in sorted(conflicts):
        anchors.extend(rng.sample(conflicts[key], quotas[key]))
    anchors.extend(rng.sample(missing, 20))
    anchors.extend(rng.sample(controls, 20))
    return {"seed": seed, "conflict_population": populations, "conflict_quotas": quotas,
            "control_populations": {"missing_key": len(missing), "match": len(controls)}, "anchors": anchors}


def classify(document: dict) -> dict:
    """Classify chosen-key temporal evidence without asserting a full session.

    Requires strict timestamp ordering; ties/competing selections are not
    silently ordered by _id. Persistence is counterevidence to prompt URL
    catch-up, not proof that the user selection failed or was invalid.
    """
    selected = document["selected_value"]
    old = document["anchor_url_values"]
    matches = document["matches"]
    before = [item for item in matches if item["seconds_from_anchor"] < 0 and len(item["url_values_for_key"]) == 1]
    after = [item for item in matches if item["seconds_from_anchor"] > 0 and len(item["url_values_for_key"]) == 1]
    result = {"_id": document["_id"], "kind": document["kind"], "key": document["key"],
              "product_id": document["product_id"], "store_id": document["store_id"],
              "selected_value": selected, "anchor_url_values": old,
              "matched_context": len(matches), "status": "inconclusive_no_successor_url"}
    if not document["device_id_available"]:
        result["status"] = "inconclusive_no_device"
        return result
    if any(item["seconds_from_anchor"] == 0 and (item["selected_values_for_key"] or item["url_values_for_key"]) for item in matches):
        result["status"] = "inconclusive_anchor_timestamp_tie"
        return result
    if not after:
        if document["kind"] == "missing_key" and any(item["seconds_from_anchor"] > 0 for item in matches):
            result["status"] = "missing_key_stays_absent"
        return result
    first_time = min(item["seconds_from_anchor"] for item in after)
    first_group = [item for item in after if item["seconds_from_anchor"] == first_time]
    values = {item["url_values_for_key"][0] for item in first_group}
    if len(values) != 1:
        result["status"] = "inconclusive_successor_timestamp_tie"
        return result
    next_value = next(iter(values))
    result.update({"next_url_value": next_value, "next_source_id": first_group[0]["_id"], "seconds_to_next_url": first_time})
    competing = [item for item in matches if 0 < item["seconds_from_anchor"] <= first_time
                 and any(value != selected for value in item["selected_values_for_key"])]
    if competing:
        result["status"] = "inconclusive_intervening_selection"
        return result
    previous_value = None
    if before:
        last_time = max(item["seconds_from_anchor"] for item in before)
        last_group = [item for item in before if item["seconds_from_anchor"] == last_time]
        previous_values = {item["url_values_for_key"][0] for item in last_group}
        if len(previous_values) != 1:
            result["status"] = "inconclusive_predecessor_timestamp_tie"
            return result
        previous_value = next(iter(previous_values))
        result.update({"previous_url_value": previous_value, "previous_source_id": last_group[0]["_id"]})
    if document["kind"] == "match":
        result["status"] = "control_url_remains_selected" if next_value == selected else "control_url_changes_without_observed_delta"
    elif document["kind"] == "missing_key":
        result["status"] = "missing_key_forward_support" if next_value == selected else "missing_key_different_successor"
    elif previous_value == selected:
        result["status"] = "prior_already_selected_counterevidence"
    elif next_value == selected:
        result["status"] = "confirmed_pre_to_selected" if previous_value in old else "forward_only_support"
    elif next_value not in old:
        result["status"] = "different_successor_counterevidence"
    else:
        persistent = [item for item in after if item["url_values_for_key"][0] in old
                      and not any(0 < other["seconds_from_anchor"] <= item["seconds_from_anchor"]
                                  and any(value != selected for value in other["selected_values_for_key"]) for other in matches)]
        result["status"] = "persistent_old_url_counterevidence" if len({item['seconds_from_anchor'] for item in persistent}) >= 2 else "inconclusive_one_old_successor"
    return result


def summarize(cohort: dict, probes: Path) -> dict:
    """Return raw and stratum-weighted timing outcomes with traceable examples."""
    expected = {item["_id"]: item for item in cohort["anchors"]}
    raw, by_key, controls, outcomes = Counter(), defaultdict(Counter), defaultdict(Counter), []
    scanned = 0
    for document in records(probes):
        anchor = expected.pop(document["_id"])
        if document["kind"] != anchor["group"] or document["key"] != anchor["key"]:
            raise ValueError("source cohort classification changed")
        scanned += document["scanned"]
        result = classify(document)
        outcomes.append(result)
        if result["kind"] == "conflict":
            raw[result["status"]] += 1
            by_key[result["key"]][result["status"]] += 1
        else:
            controls[result["kind"]][result["status"]] += 1
    if expected:
        raise ValueError("incomplete timing probe cohort")
    total = sum(cohort["conflict_population"].values())
    weighted = {status: sum(cohort["conflict_population"][key] / total * counts.get(status, 0) / sum(counts.values())
                            for key, counts in by_key.items()) for status in raw}
    confirmations = [result for result in outcomes if result["status"] == "confirmed_pre_to_selected"]
    delays = [result["seconds_to_next_url"] for result in confirmations]
    return {"cohort": {key: value for key, value in cohort.items() if key != "anchors"}, "scanned_neighbors": scanned,
            "conflict_outcomes": dict(raw), "by_key": {key: dict(value) for key, value in by_key.items()},
            "weighted_conflict_fractions": weighted, "controls": {key: dict(value) for key, value in controls.items()},
            "diversity": {"conflict_stores": len({result["store_id"] for result in outcomes if result["kind"] == "conflict"}),
                          "conflict_products": len({result["product_id"] for result in outcomes if result["kind"] == "conflict"})},
            "confirmed_delay_seconds": {"minimum": min(delays), "median": median(delays), "maximum": max(delays)} if delays else {},
            "outcomes": outcomes,
            "scope": "Selected-key transitions in bounded device/product/store windows; no full-session or full-overlay validation. Weighted fractions refer only to the source random-pool conflict population."}


def write_note(result: dict, destination: Path) -> None:
    """Write the timing-study evidence, counterevidence and conditional proposal."""
    from report import table
    outcomes = result["conflict_outcomes"]
    weighted = result["weighted_conflict_fractions"]
    total = sum(outcomes.values())
    confirmed = outcomes.get("confirmed_pre_to_selected", 0)
    counter = sum(count for status, count in outcomes.items() if status.endswith("counterevidence"))
    weighted_counter = sum(value for status, value in weighted.items() if status.endswith("counterevidence"))
    rows = [[status, count, f"{count / total:.2%}", f"{weighted[status]:.2%}"] for status, count in outcomes.items()]
    strata = [[key, result["cohort"]["conflict_population"][key], sum(counts.values()),
               counts.get("confirmed_pre_to_selected", 0), sum(value for status, value in counts.items() if status.endswith("counterevidence"))]
              for key, counts in result["by_key"].items()]
    text = f"""# Selection timing: observed URL snapshot versus selected delta

Research follow-up requested and observed 6 November 2026. **Approved for now:** preserve both sources separately. An overlay remains a proposal; none was applied or emitted by these tools.

## Method and evidence limits

The 300,000-event random pool contained 2,982 conflicting select_product_option events. Seed `{result['cohort']['seed']}` selected 120 conflict anchors stratified by selected key, plus 20 missing-key and 20 already-matching controls. The conflict cohort covers {result['diversity']['conflict_products']} products and {result['diversity']['conflict_stores']} stores. Sampling is without replacement; rare keys are deliberately oversampled.

Each exact anchor was read through `_id_`, followed by at most 1,000 indexed predecessors and 1,000 successors. Exactly **{result['scanned_neighbors']:,} neighboring records** were examined, with device_id/product_id/store_id equality applied on the VM. Matching context is ordered by actual `time_stamp`, restricted to ±1,800 seconds. The device value is never exported. Device history is not automatically a session, and anchors can be correlated.

The collection has no device/product/time index. These are bounded storage neighborhoods, not guaranteed globally nearest events in time. Missing context is censoring, not evidence that a transition did not happen. A global device/session reconstruction would need a separately justified access strategy; no index or source write was performed.

## Quantified outcomes

**{confirmed}/{total} ({confirmed / total:.2%})** showed the strict visible pre-value → selected-value sequence. **{counter}/{total} ({counter / total:.2%})** showed counterevidence to a simple prompt URL-catch-up interpretation. **{total - confirmed - counter}/{total} ({(total - confirmed - counter) / total:.2%})** were inconclusive.

Stratum-weighted fractions are **{weighted.get('confirmed_pre_to_selected', 0):.2%} supportive / {weighted_counter:.2%} counterevidence / {1 - weighted.get('confirmed_pre_to_selected', 0) - weighted_counter:.2%} inconclusive**. They refer to the 2,982 conflicts in the source random pool under this bounded-window procedure, not all 41.4M events or complete sessions. No confidence interval or population-wide causal claim is established.

{table(['Classification', 'Anchors', 'Unweighted cohort share', 'Stratum-weighted share'], rows)}

{table(['Selected key', 'Conflicts in source pool', 'Inspected', 'Strict supportive sequence', 'Counterevidence'], strata)}

Strict support requires the nearest available earlier URL to contain the old value and the earliest available later URL to contain the selected value, with no intervening different selection on that key and no ambiguous timestamp tie. Counterevidence includes at least two later old-value URL observations without an observed competing selection, or a different successor value. Persistent old URLs do not prove that the selection failed: the URL can remain stale, and unobserved events can still matter. These classifications test the chosen key, not every dimension of a full configuration.

Seconds until the next corroborating URL among strict supportive cases: `{json.dumps(result['confirmed_delay_seconds'])}`. These observed intervals are not a universal session timeout or overlay threshold.

## Comparison cohorts

"""
    for kind, counts in result["controls"].items():
        text += table([f"{kind} control outcome", "Anchors"], sorted(counts.items())) + "\n\n"
    text += "Already-matching anchors demonstrate that the URL is not universally a visibly different pre-selection state. Missing-key anchors can add only partial evidence; the absent dimensions and website defaults remain unknown. Intervening choices and timestamp ties remain inconclusive.\n\n## Traceable examples\n\n"
    for status in ("confirmed_pre_to_selected", "persistent_old_url_counterevidence", "different_successor_counterevidence", "inconclusive_intervening_selection"):
        example = next((item for item in result["outcomes"] if item["status"] == status), None)
        if example:
            text += "### " + status.replace("_", " ") + "\n\n```json\n" + json.dumps(example, ensure_ascii=False, indent=2) + "\n```\n\n"
    text += f"""## Conditional inference proposal — approval required

Recommend retaining the raw observed URL subset and selected delta for every anchor. For a later approved inference branch, require an explicit product/store/current-host association, one recognized selected key with an approved slug value, one unambiguous prior URL value and a later same-device/product/store URL corroborating the selected value before a competing same-key selection. Do not resolve second-level ties using `_id` order.

Only then propose a separate **inferred, partial post-selection observation** that replaces the changed key in the observed URL subset. Preserve the source snapshot and delta alongside it, with anchor/prior/successor IDs and timing evidence. Do not claim website defaults, unrepresented quality dimensions or untouched missing options are resolved. Malformed URL pairs, unknown key mappings, conflicts and incomplete context remain unresolved.

This study checks the selected key, not the stability of every untouched option. Generating an entire overlaid option set would additionally require checking those other dimensions; otherwise the result could be a hybrid state never observed. Where a later URL already directly records the desired state, prefer that observed evidence for crawl input and retain the inferred transition separately. Overlaying is useful only as an explicitly qualified state hypothesis, not a way to increase resolved-configuration counts automatically.

Alternatives: URL-only handling is simple but loses selected deltas; universal selected-value overlay assumes ordering that the counterexamples do not establish. The recommended research proposal keeps both sources, uses directly observed later state where available, and considers a separately marked inference branch only after all stated conditions are reviewed.

The {confirmed} supportive anchors justify investigating this conditional branch; they do not authorize a universal overlay. The {counter} counterevidence anchors and {total - confirmed - counter} inconclusive anchors must not be silently dropped or forced into it. Review and approval are still required before implementation.

## Reproduce and next decision

Private inputs: `timing_cohort.json` and `timing_probes.jsonl`; output metrics: `timing_results.json` beside the source pool. `tools/timing.py cohort` selects anchors; `tools/capture.py --script analysis/product_configuration_research/tools/timing.mjs --ids-file <cohort>` performs indexed read-only probes; `tools/timing.py summarize --cohort <cohort> --probes <probes> --output <metrics> --report analysis/product_configuration_research/SELECTION_TIMING.md` renders this note. Supply the same authorized SSH/config flags documented in the research README. No overlay, configuration export or crawler runs.

Please review the conditional inference proposal, especially whether bounded same-device context is sufficient or a verified session/instrumentation contract is required. See [the event note](collections/select_product_option.md) and [open decisions](OPEN_QUESTIONS.md).
"""
    destination.write_text(text)


def main() -> None:
    """Create a reproducible cohort or summarize its private timing probes."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    draw = commands.add_parser("cohort")
    draw.add_argument("--sample", type=Path, required=True)
    draw.add_argument("--output", type=Path, required=True)
    summary = commands.add_parser("summarize")
    summary.add_argument("--cohort", type=Path, required=True)
    summary.add_argument("--probes", type=Path, required=True)
    summary.add_argument("--output", type=Path, required=True)
    summary.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = draw_cohort(args.sample) if args.command == "cohort" else summarize(json.loads(args.cohort.read_text()), args.probes)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    args.output.chmod(0o600)
    if args.command == "summarize" and args.report:
        write_note(result, args.report)
    print(json.dumps({key: value for key, value in result.items() if key not in {"anchors", "outcomes"}}, indent=2))


if __name__ == "__main__":
    main()
