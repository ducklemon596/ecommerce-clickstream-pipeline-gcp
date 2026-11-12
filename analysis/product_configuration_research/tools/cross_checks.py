"""Additional bounded-pool checks for aliases, quality and recommendation routes."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from urllib.parse import urlsplit

from profile import CANDIDATE_KEYS, records, url_facts


def investigate(sample: Path) -> dict:
    """Measure possible associations without resolving or emitting configurations.

    Literal value overlap suggests a hypothesis, not an approved alias map.
    Path-ID equality describes association evidence, not product existence.
    """
    labels, quality = defaultdict(Counter), Counter()
    routes = defaultdict(lambda: defaultdict(Counter))
    examples = {}
    quality_states = defaultdict(dict)
    for document in records(sample):
        event = document["collection"]
        current = url_facts(document, "current_url")
        choices = document.get("option")
        if event in {"select_product_option", "select_product_option_quality"} and isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                label, value = choice.get("option_label"), choice.get("value_label")
                if isinstance(label, str):
                    counts = labels[event + ":" + label]
                    counts["items"] += 1
                    if isinstance(value, str) and value:
                        counts["nonempty_value_label"] += 1
                        matched = [key for key, values in current["values"].items() if value in values]
                        if len(matched) == 1:
                            counts["unique_value_overlap:" + matched[0]] += 1
                            if matched[0] != label:
                                examples.setdefault(event + ":" + label, {"_id": document["_id"],
                                    "option_label": label, "value_label": value,
                                    "matching_url_key": matched[0], "quality": choice.get("quality")})
                        elif len(matched) > 1:
                            counts["ambiguous_value_overlap"] += 1
                        else:
                            counts["no_value_overlap"] += 1
                if event == "select_product_option_quality":
                    quality["items"] += 1
                    grades = [choice.get("quality"), choice.get("quality_label")]
                    if any(grade and grade in values for grade in grades for values in current["values"].values()):
                        quality["grade_literal_in_candidate_url_value"] += 1
                    if any(key.lower().startswith("quality") for key, _ in current["pairs"]):
                        quality["quality_named_query_key"] += 1
                    if grades[0] and grades[1]:
                        quality["quality_and_label_equal" if grades[0] == grades[1] else "quality_and_label_differ"] += 1
                    state_key = (str(document.get("product_id")), str(document.get("store_id")),
                                 document.get("current_url"), str(label), str(value))
                    quality_states[state_key].setdefault(tuple(str(grade or "") for grade in grades), document["_id"])
        if current["category"] != "recommendation_route":
            continue
        result = routes[event]
        result["events"]["total"] += 1
        parts = urlsplit(document["current_url"]).path.split("/county/recommendation/list/", 1)[1].strip("/").split("/")
        pairs = list(zip(parts[::2], parts[1::2]))
        path_values = dict(pairs)
        result["path_keys"].update(key for key, _ in pairs)
        route_id = path_values.get("id")
        for field in ("product_id", "viewing_product_id", "recommendation_product_id"):
            if document.get(field) not in (None, ""):
                result["events"][field + ("_matches_route_id" if str(document[field]) == route_id else "_differs_from_route_id")] += 1
        referrer = url_facts(document, "referrer_url")
        matching, conflicting = [], []
        for key, value in pairs:
            if key in CANDIDATE_KEYS and key in referrer["values"]:
                (matching if value in referrer["values"][key] else conflicting).append(key)
        if matching:
            result["events"]["some_path_referrer_pairs_match"] += 1
        if conflicting:
            result["events"]["path_referrer_pair_conflict"] += 1
        if isinstance(choices, dict):
            for key, value in pairs:
                if key in CANDIDATE_KEYS and choices.get(key) not in (None, ""):
                    result["object_comparisons"]["pair_match" if str(choices[key]) == value else "pair_conflict"] += 1
        examples.setdefault(event + ":route", {"_id": document["_id"], "route_id": route_id,
            "product_id": document.get("product_id"), "viewing_product_id": document.get("viewing_product_id"),
            "recommendation_product_id": document.get("recommendation_product_id"),
            "path_keys": [key for key, _ in pairs], "matching_referrer_keys": matching,
            "conflicting_referrer_keys": conflicting})
    collisions = []
    for state, grades in quality_states.items():
        if len(grades) > 1:
            collisions.append({"product_id": state[0], "store_id": state[1], "current_url": state[2],
                "option_label": state[3], "value_label": state[4],
                "grade_observations": [{"quality": grade[0], "quality_label": grade[1], "_id": source}
                                       for grade, source in list(grades.items())[:4]]})
    quality["distinct_redacted_url_product_option_groups"] = len(quality_states)
    quality["groups_with_multiple_quality_observations"] = len(collisions)
    quality["groups_with_multiple_nonempty_quality_codes"] = sum(
        len({grade[0] for grade in grades if grade[0]}) > 1 for grades in quality_states.values())
    return {"labels": {key: dict(value) for key, value in labels.items()}, "quality": dict(quality),
            "routes": {event: {key: dict(value) for key, value in result.items()} for event, result in routes.items()},
            "examples": examples, "quality_collision_examples": collisions[:3]}


def main() -> None:
    """Write private association-check metrics from the captured sample."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = investigate(args.sample)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    args.output.chmod(0o600)
    print(json.dumps({"quality": result["quality"], "routes": result["routes"],
        "alias_hypotheses": {key: value for key, value in result["labels"].items()
                             if key.startswith("select_product_option:") and key.split(":")[1] not in CANDIDATE_KEYS}}, indent=2))


if __name__ == "__main__":
    main()
