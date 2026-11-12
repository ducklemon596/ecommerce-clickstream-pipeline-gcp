"""Research sensitivity check for scoped internal-ID/URL-token associations."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from profile import records, url_facts


def identity_key(product, store, choice: dict) -> tuple[str, ...] | None:
    """Return a research comparison key with lossless digit-ID string coercion.

    This canonicalization is a proposed comparison scenario, not production
    identity policy. Blank, nonnumeric and noninteger identifiers are excluded.
    """
    values = [product, store, choice.get("option_id"), choice.get("value_id")]
    text = tuple(str(value) for value in values)
    return text if all(value.isdigit() for value in text) else None


def compare(sample: Path) -> dict:
    """Measure in-sample association coverage; emit no mapping/configuration set.

    A witness must be a selector whose literal option label/value agrees with
    the current URL. Returns aggregate coverage and a few traceable match or
    ambiguity examples. The same sample supplies witnesses and targets, so this
    is an optimistic sensitivity check without a holdout or global guarantee.
    """
    references, witnesses = defaultdict(set), {}
    witness_count = 0
    for document in records(sample):
        if document.get("collection") != "select_product_option":
            continue
        url = url_facts(document, "current_url")
        option = document.get("option")
        if not isinstance(option, list):
            continue
        for choice in option:
            if not isinstance(choice, dict):
                continue
            label, value = choice.get("option_label"), choice.get("value_label")
            key = identity_key(document.get("product_id"), document.get("store_id"), choice)
            if key and label in url["values"] and value in url["values"][label]:
                references[key].add((label, value))
                witnesses.setdefault((key, label, value), document["_id"])
                witness_count += 1
    by_event, examples = defaultdict(Counter), {}
    for document in records(sample):
        event = document.get("collection")
        if event not in {"view_product_detail", "add_to_cart_action", "view_shopping_cart", "checkout", "checkout_success"}:
            continue
        entries = (document.get("cart_products", []) if isinstance(document.get("cart_products"), list)
                   else [{"product_id": document.get("product_id"), "option": document.get("option")}])
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            counts = by_event[event]
            counts["products_or_items"] += 1
            options = entry.get("option")
            if not isinstance(options, list) or not options:
                counts["without_option_array"] += 1
                continue
            usable = matched = 0
            for choice in options:
                if not isinstance(choice, dict):
                    continue
                key = identity_key(entry.get("product_id"), document.get("store_id"), choice)
                if not key:
                    continue
                usable += 1
                counts["id_choices"] += 1
                matches = references.get(key, set())
                status = "unambiguous_in_sample" if len(matches) == 1 else "ambiguous_in_sample" if matches else "no_reference"
                counts[status] += 1
                if len(matches) == 1:
                    matched += 1
                    label, value = next(iter(matches))
                    examples.setdefault(event, {"target_source_id": document["_id"],
                        "selector_witness_id": witnesses[key, label, value],
                        "target_option_label": choice.get("option_label"),
                        "target_display_value": choice.get("value_label"),
                        "witness_url_key": label, "witness_url_token": value,
                        "note": "candidate association only; not a reconstructed configuration"})
            counts["items_with_any_reference"] += bool(matched)
            counts["items_all_usable_ids_matched"] += bool(usable and matched == usable)
    conflicts = []
    for key, values in references.items():
        if len(values) > 1:
            conflicts.append({"product_id": key[0], "store_id": key[1], "option_id": key[2], "value_id": key[3],
                "alternatives": [{"url_key": label, "url_token": value, "source_id": witnesses[key, label, value]}
                                 for label, value in sorted(values)[:4]]})
        if len(conflicts) == 6:
            break
    return {"selector_witnesses": witness_count, "reference_keys": len(references),
            "ambiguous_reference_keys": sum(len(values) > 1 for values in references.values()),
            "by_event": {key: dict(value) for key, value in by_event.items()}, "examples": examples,
            "conflict_examples": conflicts,
            "limitations": "Same-sample comparison; no holdout, global completeness or target-configuration completeness. Numeric-string comparison and reference use remain unapproved."}


def main() -> None:
    """Write private aggregate sensitivity metrics for a complete captured pool."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.sample)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    args.output.chmod(0o600)
    print(json.dumps({key: value for key, value in result.items() if key not in {"examples", "conflict_examples"}}, indent=2))


if __name__ == "__main__":
    main()
