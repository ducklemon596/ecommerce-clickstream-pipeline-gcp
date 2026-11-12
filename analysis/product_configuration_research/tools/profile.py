"""Measure event evidence; this module does not emit reconstructed configurations."""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterator
import hashlib
from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from glamira_pipeline.products.normalize import CONTROLS, KNOWN_OPTIONS, is_tracking

# Candidate names are research classifications, not approved extraction rules.
CANDIDATE_KEYS = KNOWN_OPTIONS | {
    "pearlcolor", "quality", "quality2", "quality3", "finish", "profile",
    "shape", "shapediamond", "width", "bandwidth", "size", "ring_size", "ringsize",
}
EVENTS = sorted("""add_to_cart_action back_to_product_action checkout checkout_success
landing_page_recommendation_clicked landing_page_recommendation_noticed
landing_page_recommendation_visible listing_page_recommendation_clicked
listing_page_recommendation_noticed listing_page_recommendation_visible
product_detail_recommendation_clicked product_detail_recommendation_noticed
product_detail_recommendation_visible product_view_all_recommend_clicked
search_box_action select_product_option select_product_option_quality
sorting_relevance_click_action view_all_recommend view_home_page view_landing_page
view_listing_page view_my_account view_product_detail view_shopping_cart
view_sorting_relevance view_static_page""".split())


def value_type(value: object) -> str:
    """Describe JSON-level types; source BSON root types are measured separately."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, str):
        return "string"
    return "number"


def records(path: Path) -> Iterator[dict]:
    """Yield captured JSONL events, excluding the metadata/completion markers."""
    with path.open() as stream:
        for line in stream:
            item = json.loads(line)
            if "_metadata" not in item and "_completed" not in item:
                yield item


def partition(sample: Path, directory: Path) -> tuple[dict, Counter]:
    """Stratify the shared random pool by event without another MongoDB scan.

    Returns source metadata and event counts. Files remain private under data/.
    Refuses to overwrite a prior stratification and closes files on failures.
    """
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    handles, counts, metadata = {}, Counter(), {}
    try:
        with sample.open() as stream:
            for line in stream:
                document = json.loads(line)
                if "_metadata" in document:
                    metadata = document["_metadata"]
                    continue
                if "_completed" in document:
                    if document["_completed"]["emitted"] != sum(counts.values()):
                        raise ValueError("capture completion count does not reconcile")
                    continue
                event = document.get("collection")
                if not isinstance(event, str) or not re.fullmatch(r"[a-z_]+", event):
                    raise ValueError("unexpected event name; inspect privately")
                if event not in handles:
                    path = directory / (event + ".jsonl")
                    handles[event] = path.open("x")
                    path.chmod(0o600)
                handles[event].write(line)
                counts[event] += 1
    finally:
        for stream in handles.values():
            stream.close()
    return metadata, counts


def url_facts(document: dict, field: str) -> dict:
    """Classify a redacted URL and retain candidate query pairs for comparison.

    No query value is recovered from redaction. A product-shaped path is only a
    shape observation, not proof that a website page or product exists.
    """
    if field not in document:
        return {"category": "missing", "pairs": [], "values": {}, "unknown": []}
    raw = document[field]
    if not isinstance(raw, str) or not raw:
        return {"category": "empty" if raw == "" else value_type(raw), "pairs": [], "values": {}, "unknown": []}
    try:
        parsed = urlsplit(unescape(raw))
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError()
        host, path = parsed.hostname.lower(), parsed.path.lower().rstrip("/")
        merchant = bool(re.search(r"(^|\.)(glamira\.[a-z.]+|ring-paare\.de)$", host))
        category = "external"
        if merchant:
            if "/county/recommendation/list/" in path:
                category = "recommendation_route"
            elif path.endswith(".html") or "/catalog/product/view/id/" in path:
                category = "product_shaped"
            elif "checkout" in path or "/cart" in path:
                category = "cart_or_checkout"
            else:
                category = "merchant_other_page"
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        values = defaultdict(set)
        for key, value in pairs:
            if key.lower() in CANDIDATE_KEYS and value and value != "[REDACTED]":
                values[key].add(value)
        return {"category": category, "host": host, "path": path, "pairs": pairs,
                "values": dict(values), "nonproduction": bool(re.search(r"(^|\.)(test|stage|dev\d*|local)[.-]", host)),
                "unknown": [key for key, _ in pairs if key.lower() not in CANDIDATE_KEYS
                            and not is_tracking(key) and key.lower() not in CONTROLS]}
    except ValueError:
        return {"category": "invalid_or_nonweb", "pairs": [], "values": {}, "unknown": []}


def nested_types(value: object, prefix: str = "") -> Iterator[str]:
    """Yield relevant paths and types, counting array members as observations."""
    if isinstance(value, list):
        for item in value:
            yield from nested_types(item, prefix + "[]")
    elif isinstance(value, dict):
        for key, item in value.items():
            if key == "_research":
                continue
            path = prefix + "." + key if prefix else key
            if re.search("product|sku|option|store", path, re.I):
                yield path + ":" + value_type(item)
            yield from nested_types(item, path)


def excerpt(document: dict) -> dict:
    """Produce a short traceable excerpt; omitted keys remain documented.

    Marketing query values were already redacted on the VM. Omit those query
    pairs entirely here so committed examples focus on product evidence.
    """
    result = {key: value for key, value in document.items() if key != "_research"}
    for field in ("current_url", "referrer_url"):
        if not isinstance(result.get(field), str):
            continue
        parsed = urlsplit(result[field])
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        omitted = sorted({key for key, _ in pairs if is_tracking(key)})
        retained = [(key, value) for key, value in pairs if not is_tracking(key)]
        result[field] = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(retained), ""))
        if omitted:
            result[field + "_omitted_tracking_keys"] = omitted
    if isinstance(result.get("cart_products"), list):
        products = result["cart_products"]
        result["cart_products_count"] = len(products)
        result["cart_products"] = products[:2]
        result["cart_products_excerpt_truncated"] = len(products) > 2
    if isinstance(result.get("option"), list) and len(result["option"]) > 6:
        result["option_count"] = len(result["option"])
        result["option"] = result["option"][:6]
    flags = {field: {key: value for key, value in info.items() if value and key != "redacted_query_keys"}
             for field, info in document.get("_research", {}).items()
             if field != "root_types" and isinstance(info, dict)}
    result["research_url_observations"] = flags
    return result


def option_metrics(option: object, url: dict, counters: dict) -> set[str]:
    """Measure option shape and literal comparisons; return event-level flags.

    Different option-label spelling is retained. No alias mapping, quality
    overlay, website default, or temporal inference is applied.
    """
    counters["option_types"][value_type(option)] += 1
    flags, named_values = set(), defaultdict(set)
    if isinstance(option, list):
        counters["option_lengths"][str(len(option))] += 1
        if len(option) == 1:
            flags.add("single_option_item")
        for item in option:
            if not isinstance(item, dict):
                flags.add("invalid_option_item")
                continue
            counters["option_fields"].update(key + ":" + value_type(value) for key, value in item.items())
            label, value = item.get("option_label"), item.get("value_label")
            if isinstance(label, str):
                counters["option_labels"][label] += 1
            if value in (None, ""):
                flags.add("empty_value_label")
                if item.get("value_id") not in (None, ""):
                    flags.add("id_only_option")
            elif isinstance(label, str) and isinstance(value, str):
                named_values[label].add(value)
                if label in url["values"]:
                    flags.add("option_url_pair_match" if value in url["values"][label] else "option_url_pair_conflict")
                elif label.lower() in CANDIDATE_KEYS:
                    flags.add("selected_key_missing_from_url")
                else:
                    flags.add("unmapped_option_label")
            if item.get("quality") not in (None, ""):
                flags.add("quality_present")
            if item.get("quality_label") not in (None, ""):
                flags.add("quality_label_present")
    elif isinstance(option, dict):
        counters["option_fields"].update(key + ":" + value_type(value) for key, value in option.items())
        for key, value in option.items():
            counters["option_labels"][key] += 1
            if value in (None, ""):
                flags.add("empty_option_object_value")
            if isinstance(value, str) and value and key in url["values"]:
                flags.add("object_url_pair_match" if value in url["values"][key] else "object_url_pair_conflict")
    if any(len(values) > 1 for values in named_values.values()):
        flags.add("conflicting_option_labels")
    return flags


def cart_metrics(document: dict, counters: dict) -> set[str]:
    """Count nested item identities and options; empty strings stay distinct."""
    products = document.get("cart_products")
    if not isinstance(products, list):
        return set()
    flags = {"cart_present"}
    counters["cart_lengths"][str(len(products))] += 1
    if not products:
        flags.add("empty_cart")
    if len(products) > 1:
        flags.add("multiple_cart_items")
    for item in products:
        counters["cart_items"]["total"] += 1
        if not isinstance(item, dict):
            counters["cart_items"]["invalid_item"] += 1
            continue
        counters["cart_id_types"][value_type(item.get("product_id"))] += 1
        option = item.get("option")
        counters["cart_option_types"]["empty_string" if option == "" else value_type(option)] += 1
        if option == "":
            flags.add("empty_cart_option_string")
        if isinstance(option, list):
            counters["cart_items"]["array_options"] += 1
            usable = 0
            for choice in option:
                if not isinstance(choice, dict):
                    continue
                counters["cart_option_fields"].update(key + ":" + value_type(value) for key, value in choice.items())
                if choice.get("option_label") and choice.get("value_label"):
                    usable += 1
            counters["cart_items"]["nonempty_label_value_pairs"] += usable
            counters["cart_items"]["items_with_label_value"] += bool(usable)
    return flags


def profile_event(path: Path) -> dict:
    """Profile one event stratum and choose reproducible normal/edge examples.

    Returns counters and redacted examples only; no configurations or reference
    mapping outputs. Memory is bounded by counter cardinality and evidence bins.
    """
    counters = defaultdict(Counter)
    evidence = {}
    for document in records(path):
        counters["totals"]["events"] += 1
        counters["paths"].update(nested_types(document))
        for field in document.get("_research", {}).get("root_types", []):
            counters["root_types"][field["key"] + ":" + field["bson_type"]] += 1
        for key in ("product_id", "viewing_product_id", "recommendation_product_id", "store_id", "option"):
            counters["fields"][key + ":" + (value_type(document[key]) if key in document else "missing")] += 1
            if document.get(key) == "":
                counters["empty_fields"][key] += 1
            if key.endswith("product_id") and document.get(key) not in (None, ""):
                if not re.fullmatch(r"[0-9]+", str(document[key])):
                    counters["invalid_ids"][key] += 1
        current, referrer = url_facts(document, "current_url"), url_facts(document, "referrer_url")
        flags = set()
        for field, facts in (("current", current), ("referrer", referrer)):
            counters[field + "_categories"][facts["category"]] += 1
            counters[field + "_keys"].update(key for key, _ in facts["pairs"])
            counters[field + "_unknown_keys"].update(facts["unknown"])
            if facts.get("host"):
                counters[field + "_hosts"][facts["host"]] += 1
            if facts.get("values"):
                flags.add(field + "_candidate_option_values")
            else:
                flags.add(field + "_no_candidate_option_values")
            if facts.get("nonproduction"):
                flags.add(field + "_nonproduction_host")
            if facts["unknown"]:
                flags.add(field + "_unknown_query_keys")
            if any(not key or key[0] in ";?" or "/" in key for key, _ in facts["pairs"]):
                flags.add(field + "_malformed_parameter_key")
            if facts["category"] in {"invalid_or_nonweb", "external"}:
                flags.add(field + "_unusable_or_external")
            observations = document.get("_research", {}).get(field + "_url", {})
            flags.update(field + "_" + key for key in ("html_escaped", "bad_percent", "control_or_space", "repeated_equal_key", "repeated_conflicting_key") if observations.get(key))
        if current["category"] != "product_shaped":
            flags.add("current_not_product_shaped")
        if referrer["category"] == "product_shaped":
            flags.add("referrer_product_shaped")
        direct = document.get("product_id") or document.get("viewing_product_id")
        store = document.get("store_id")
        if direct and store and current.get("host"):
            flags.add("direct_identity_and_current_host")
            flags.add("direct_identity_with_url_subset" if current["values"] else "direct_identity_options_unspecified")
            if current["category"] == "product_shaped" and current["values"]:
                flags.add("direct_identity_product_page_subset")
        else:
            flags.add("no_direct_identity_store_host")
        if store and current.get("host"):
            counters["store_host_pairs"][str(store) + " @ " + current["host"]] += 1
        viewed, recommended = document.get("viewing_product_id"), document.get("recommendation_product_id")
        if viewed and recommended:
            flags.add("viewed_recommended_equal" if viewed == recommended else "viewed_recommended_differ")
        route_id = re.search(r"/catalog/product/view/id/([^/]+)", current.get("path", ""))
        if direct and route_id:
            flags.add("product_route_id_match" if str(direct) == route_id[1] else "product_route_id_conflict")
        flags.update(option_metrics(document.get("option"), current, counters))
        flags.update(cart_metrics(document, counters))
        counters["events"].update(flags)
        # Stable hash picks examples across the pool, rather than its first rows.
        rank = hashlib.sha256(document["_id"].encode()).hexdigest()
        for reason in flags | {"representative"}:
            if reason not in evidence or rank < evidence[reason][0]:
                evidence[reason] = (rank, document)
    return {"counts": {key: dict(value) for key, value in counters.items()},
            "evidence": {reason: excerpt(value[1]) for reason, value in evidence.items()}}
