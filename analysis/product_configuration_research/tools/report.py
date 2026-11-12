"""Write measured research notes sequentially; no extraction policy is executed."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from decisions import EVENTS as DECISIONS, FAMILIES
from interpret import event_checks, event_probes, load_checks, shared_findings
from profile import EVENTS, partition, profile_event


def table(headers: list[str], rows) -> str:
    """Render a compact Markdown table, escaping data cells for readability."""
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def rate(number: int, denominator: int) -> str:
    """Return a sampled count and percentage; report zero denominators as N/A."""
    return f"{number:,} ({number / denominator:.2%})" if denominator else "N/A"


def count_rows(counts: dict, limit: int = 15):
    """Return the largest measured categories without implying absent tails."""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]


def measured_sections(profile: dict) -> str:
    """Render source types, URL categories, options and sampled event flags."""
    counts = profile["counts"]
    n = counts["totals"]["events"]
    fields = counts.get("fields", {})
    categories = sorted(set(counts.get("current_categories", {})) | set(counts.get("referrer_categories", {})))
    parts = [table(["Field / observed type", "Events"], [(key, rate(value, n)) for key, value in sorted(fields.items())]),
             "### URL context\n\n" + table(["URL category", "Current URL", "Referrer URL"],
                [(key, rate(counts.get("current_categories", {}).get(key, 0), n), rate(counts.get("referrer_categories", {}).get(key, 0), n)) for key in categories]),
             "### Query-key observations\n\nCounts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.\n\n" + table(
                 ["Current query key", "Occurrences"], count_rows(counts.get("current_keys", {}), 15)),
             "Unknown/nonclassified current keys: " + (", ".join(f"`{key}` ({value:,})" for key, value in count_rows(counts.get("current_unknown_keys", {}), 12)) or "none observed") + ". Values for these keys were redacted before transfer.",
             "### Option and identifier paths\n\n" + table(["Relevant path / observed JSON type", "Path occurrences"], count_rows(counts.get("paths", {}), 24))]
    if counts.get("option_fields"):
        parts += [table(["Top-level option item field", "Occurrences"], count_rows(counts["option_fields"], 15)),
                  "Observed option labels/keys: " + ", ".join(f"`{key}` ({value:,})" for key, value in count_rows(counts.get("option_labels", {}), 12)) + "."]
    if counts.get("cart_items"):
        parts += ["### Nested cart items\n\nItem counts have a different denominator from event counts.\n\n" + table(["Item measurement", "Count"], sorted(counts["cart_items"].items())),
                  table(["Nested option representation", "Items"], sorted(counts.get("cart_option_types", {}).items())),
                  table(["Nested option field / JSON type", "Occurrences"], count_rows(counts.get("cart_option_fields", {}), 16))]
    pairs = counts.get("store_host_pairs", {})
    stores, hosts = {}, {}
    for pair in pairs:
        store, host = pair.split(" @ ", 1)
        stores.setdefault(store, set()).add(host)
        hosts.setdefault(host, set()).add(store)
    parts += ["### Store and domain evidence\n\n" + table(["Observed store ID / current host", "Events"], count_rows(pairs, 8)),
              f"Observed {len(stores)} store IDs and {len(hosts)} current hosts. "
              f"{sum(len(values) > 1 for values in stores.values())} store IDs had more than one current host; "
              f"{sum(len(values) > 1 for values in hosts.values())} current hosts appeared with more than one store ID. "
              "This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store."]
    return "\n\n".join(parts)


def edge_sections(profile: dict) -> str:
    """Report counterexample searches, including zero observed occurrences."""
    counts = profile["counts"]
    events, n = counts.get("events", {}), counts["totals"]["events"]
    checks = ["option_url_pair_match", "option_url_pair_conflict", "selected_key_missing_from_url",
              "unmapped_option_label", "conflicting_option_labels", "single_option_item", "empty_value_label",
              "id_only_option", "quality_present", "quality_label_present", "current_no_candidate_option_values",
              "current_unknown_query_keys", "current_nonproduction_host", "current_bad_percent",
              "current_control_or_space", "current_repeated_equal_key", "current_repeated_conflicting_key",
              "current_malformed_parameter_key", "product_route_id_match", "product_route_id_conflict",
              "current_html_escaped", "current_not_product_shaped", "empty_cart", "multiple_cart_items",
              "empty_cart_option_string", "viewed_recommended_equal", "viewed_recommended_differ"]
    applicable = [key for key in checks if events.get(key) or key.startswith("current_") or key in {
        "option_url_pair_conflict", "conflicting_option_labels", "viewed_recommended_differ"}]
    return table(["Event-level check", "Observed in this stratum"], [(key, rate(events.get(key, 0), n)) for key in applicable]) + (
        "\n\nZero means not observed in this sample. It does not prove absence in the collection. "
        "Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; "
        "missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.\n\n"
        "Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. "
        "Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. "
        "Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. "
        "A valid nonproduction host still requires a separate crawl-scope decision.")


def evidence_sections(profile: dict) -> str:
    """Select normal and problematic traceable excerpts with bounded length."""
    priorities = ["direct_identity_with_url_subset", "representative", "option_url_pair_conflict",
                  "selected_key_missing_from_url", "unmapped_option_label", "current_repeated_conflicting_key",
                  "current_not_product_shaped",
                  "current_bad_percent", "current_nonproduction_host", "current_unknown_query_keys",
                  "empty_cart_option_string", "multiple_cart_items", "empty_cart", "viewed_recommended_differ",
                  "current_no_candidate_option_values", "current_unusable_or_external"]
    selected, ids = [], set()
    evidence = profile["evidence"]
    for reason in priorities:
        document = evidence.get(reason)
        if document and document["_id"] not in ids:
            ids.add(document["_id"])
            selected.append("### " + reason.replace("_", " ") + "\n\n```json\n" + json.dumps(document, ensure_ascii=False, indent=2) + "\n```")
        if len(selected) == 7:
            break
    return ("Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; "
            "campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. "
            "Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.\n\n" + "\n\n".join(selected))


def write_event(event: str, profile: dict, total: int, root: Path, checks: dict) -> None:
    """Write the seven requested research sections for one investigated event."""
    family_name, description, question = DECISIONS[event]
    family = FAMILIES[family_name]
    n = profile["counts"]["totals"]["events"]
    sparse = "LOW: fewer than 30 sampled events; rare-event semantics and exceptions need further evidence." if n < 30 else (
        "MODERATE structural coverage: 30–499 sampled events; semantic conclusions remain provisional." if n < 500 else
        "STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.")
    text = f"""# {event}

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

{description} This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **{n:,} events** in this stratum ({n / total:.3%} of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

{measured_sections(profile)}

## 3. Edge Cases

{edge_sections(profile)}

{event_checks(event, checks, table)}

## 4. Evidence

{evidence_sections(profile)}

{event_probes(event, checks)}

## 5. Proposed Strategy — approval pending

Proposed result class: **{family['name']}**.

Source priority: {family['priority']}

"""
    text += "\n".join("- " + rule for rule in family["rules"])
    text += f"""

Alternative and trade-off: {family['alternative']}

**Sampled opportunity, not achieved recovery:** {rate(profile['counts'].get('events', {}).get('direct_identity_with_url_subset', 0), n)} events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: {rate(profile['counts'].get('events', {}).get('direct_identity_options_unspecified', 0), n)}. No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

{sparse}

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

{question}

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
"""
    (root / "collections" / (event + ".md")).write_text(text)


def write_indexes(root: Path, profiles: dict, metadata: dict, sample: Path, digest: str, checks: dict) -> None:
    """Create the methods, comparison and user-decision documents from metrics."""
    total = sum(profile["counts"]["totals"]["events"] for profile in profiles.values())
    rows = []
    for event, profile in profiles.items():
        counts = profile["counts"]
        n = counts["totals"]["events"]
        fields = ", ".join(key for key in ("product_id", "viewing_product_id", "recommendation_product_id")
                           if any(name.startswith(key + ":") and not name.endswith(":missing") for name in counts["fields"])) or "none observed"
        if counts.get("cart_items"):
            fields = "cart_products[].product_id"
        family = DECISIONS[event][0]
        blockers = {"snapshot": "unspecified/default settings; blank internal labels", "selection": "snapshot/delta timing and conflicts",
                    "quality": "grade not established in URL", "viewed": "viewed versus recommendation owner",
                    "recommendation_route": "route filters versus product state; referrer disagreement", "cart": "localized labels; ID-reference ambiguity",
                    "target_identity": "target identity; no target options", "url_only": "missing product ID", "context": "filter/page context has no product owner"}
        rows.append([f"[{event}](collections/{event}.md)", f"{n:,}", fields,
                     rate(counts.get("current_categories", {}).get("product_shaped", 0), n),
                     rate(counts.get("referrer_categories", {}).get("product_shaped", 0), n),
                     FAMILIES[family]["name"], blockers[family] + ("; LOW n" if n < 30 else "")])
    (root / "EVENT_OVERVIEW.md").write_text("# Event comparison\n\nAll strategies are proposals. Counts are from the shared random pool, not full-population event totals. Product-shaped paths are heuristics restricted to sampled merchant hosts. Referrer percentages are previous-page references, not target-product confirmations. Explicit null IDs remain listed as fields but are unusable identities.\n\n" + table(
        ["Event", "Sample n", "Identifier fields", "Current product-shaped", "Referrer product-shaped", "Proposed recovery class", "Unresolved issue"], rows) +
        "\n\nNo class means fully resolved website options. See each event's schema, counterexamples, source priority, reference needs and user question before selecting a rule.\n")
    questions = """# Decisions requiring review

The user confirmed three research constraints on 6 November 2026: preserve URL snapshot and selected delta separately; keep unmapped options partial; consider referrers only with independent product/store corroboration. Event-specific recovery handlers and any inferred overlay still require review. No extraction rule has been implemented.

1. **Selection timing — preservation approved:** keep URL snapshots and selected deltas distinct. The requested [timing investigation](SELECTION_TIMING.md) quantifies supportive, counterevidence and inconclusive sequences. Review the conditional inferred-overlay proposal; no universal overlay is approved.
2. **Quality representation:** keep quality unresolved until a product-scoped mapping proves how quality/quality_label relate to URL options (recommended). Matching stone text alone does not identify a grade.
3. **Viewed versus recommended products:** use current-page options only for a corroborated viewed product; recommended IDs remain separate identity-only leads (recommended). Never copy the viewed product's options to a recommendation target.
4. **Cart labels and IDs — partial state approved:** keep unmapped options partial. Per-item source inclusion, a trusted catalog reference, and numeric/string canonicalization need separate review. Do not translate localized labels into URL tokens or treat the ambiguous sample reference as authoritative.
5. **Referrers — corroboration constraint approved:** future recovery may be considered only with independent product/store corroboration; never an unconditional fallback. Matching context alone does not resolve conflicting option state.
6. **Unknown query keys, route segments and storefronts:** known campaign keys have no configuration role; unknown keys, category/price filters and nonproduction hosts stay unresolved until classified. Candidate option names in these measurements are not an approved allowlist.
7. **Unspecified options:** preserve an observed subset and absence of values; do not infer website defaults or label a partial subset complete. Missing product identity or an unrepresentable quality dimension can make configuration recovery impossible.

## Event-specific review

"""
    questions += "\n\n".join(f"- **[{event}](collections/{event}.md):** {DECISIONS[event][2]}" for event in profiles)
    (root / "OPEN_QUESTIONS.md").write_text(questions + "\n")
    source = json.dumps(metadata, ensure_ascii=False, indent=2)
    readme = f"""# Product configuration reconstruction research

**Research only; proposals await user approval.** Observed 6 November 2026 (Asia/Ho_Chi_Minh); source metadata below uses UTC. Start with [the event matrix](EVENT_OVERVIEW.md) and [open decisions](OPEN_QUESTIONS.md). Each of the 27 [event files](collections/) contains measured patterns, counterexample searches, traceable excerpts and an event-specific proposed source priority.

## Evidence and method

The prior exact MongoDB `distinct(collection)` investigation on 5 November 2026 confirmed 27 event names. This run rechecks the names observed in a new bounded random pool against that list, rather than repeating an unindexed full scan. Current collection metadata is below. Metadata document count is an estimate, not a new source-parity validation.

```json
{source}
```

Private evidence: `{sample}`; SHA-256 `{digest}`. The pool contains **{total:,} events**. `$sample` is the first aggregation stage; its randomness is not seeded. Root product/option/store fields and URLs are projected; other root field **names/types only** support schema and session-key investigation. MongoDB output is redacted on the VM before SSH transfer. No IP, email, device-ID values or credentials remain in the final evidence. `_id` is retained for direct read-only point verification.

Privacy audit additionally removed three literal IP URL hosts from the local private evidence and corresponding counters. The hash above identifies the final redacted pool. The sampler now redacts such hosts on the VM too; `tools/privacy.py` records the reproducible local address-host cleanup. No raw address appeared in published examples. The first large capture returned no usable output and was rejected; transport probes were excluded from all measurement denominators. Only the completed pool contributes to reported sample metrics.

The pool is partitioned by actual event type locally, then each stratum is investigated sequentially. All sampled records in each stratum contribute metrics, not only a first-N prefix. Deterministic hashes select normal and edge-case examples from the entire stratum. URL/option disagreement, missing values, translated labels, repeated keys, malformed encoding, unknown keys, development hosts, multi-item carts, null IDs and recommendation-owner differences are deliberately searched. Zero observations do not establish impossibility. Very rare strata remain low confidence.

This conditional stratification gives many more observations for common events than rare ones. It is not a balanced experiment or a full-population frequency estimate for rare events. Targeted point verification and any additional bounded probes are recorded separately; their rows must not be mixed into the random-sample denominator.

## Interpretation and provenance

- **Explicit:** a value was directly observed in a named URL parameter, option field or ID field. Preserve its original text/type and source `_id`.
- **Inferred:** association through another event, a reference mapping or timing hypothesis. It is not a raw fact and needs verification/approval.
- **Default:** a website-supplied setting. Not measured by this research; an empty URL does not establish it.
- **Partial:** a known product/store with only an explicit subset of configuration dimensions, or unresolved selected quality/label mapping.
- **Unknown:** no reliable product owner, option values, ordering or representation. Keep unknown distinct from an explicitly empty value and from a default.

Proposed future provenance should retain source event/field, product-ID field and original type, store ID/current host, URL subset versus selected delta, source and mapping confidence, and unresolved reasons. This research emits no reconstructed configurations, production mapping, generated product URLs or crawler output.

## Shared proposals versus event-specific proposals

Shared proposals: keep explicit product ownership, store ID and observed storefront hostname separately; preserve nonempty option token text; leave absent/empty options unspecified; never invent defaults. Known campaign keys such as gclid/fbclid/itm_source/itm_medium do not identify product configuration. Unknown keys, ambiguous repeated values and malformed separators remain review cases. HTML entity and percent decoding used in this research is for observed-value comparison, not permission to repair malformed records.

Event-specific proposals: product snapshots can supply explicit URL subsets; selection events expose a delta that may precede URL updates; quality can change without a URL change; recommendation IDs identify different owners; cart items carry localized labels/internal IDs; listing objects describe filters. Each event file states source priority and what cannot be recovered. No dimension is called fully resolved merely because some values are present.

Only the user-verified `/catalog/product/view/id/` route explicitly denotes a product in the endpoint contract supplied for this task. Other `/id/` segments need context: sampled `/checkout/cart/configure/id/2017432/` had product_id `104233`, so that route number must not replace the explicit product ID. Recommendation-route /id/ values are measured separately in the event files.

## Reproduce the research

```bash
uv sync --frozen
uv run python analysis/product_configuration_research/tools/capture.py \\
  --project "$GCP_PROJECT" --zone "$GCP_ZONE" --vm "$GCP_VM" \\
  --ssh-user "$VM_USER" --mongo-user "$MONGO_USER" \\
  --config '~/.config/glamira/restore.yml' --size 300000 \\
  --output data/product_configuration_research/new_pool.jsonl
uv run python analysis/product_configuration_research/tools/report.py \\
  --sample data/product_configuration_research/new_pool.jsonl \\
  --private-dir data/product_configuration_research/new_profiles
```

Optional pool-only follow-ups use `tools/reference.py` and `tools/cross_checks.py`, each with `--sample` and `--output`; they do not query MongoDB. For this recorded run, regenerate the notes with the original pool and `--private-dir data/product_configuration_research/profiles_v1 --reuse-profiles --supplements data/product_configuration_research`. Reuse checks the sample SHA-256 already recorded here. Capture also supports repeated `--id <ObjectId>` for indexed point verification, and `--script tools/sequence.mjs` for the documented bounded context probes.

Capture requires authorized SSH access, VM Python/PyYAML and mongosh. The protected VM YAML supplies only the password to a child-process environment; credentials are never arguments or report content. Sampling uses read-only commands; existing source indexes are listed but not altered. The VM client talks to MongoDB loopback. Generated evidence and profiles remain ignored under `data/` with private file permissions.

`report.py` writes these research Markdown files and private per-event aggregate/evidence JSON. Use a new private directory for a new pool; it rejects implicit checkpoint reuse. These tools are research sampling/profiling only, not an extraction/deduplication pipeline. They do not test the website. The user-verified `/catalog/product/view/id/{{product_id}}` endpoint is contextual input, not a new HTTP verification.

Local verification: `uv run python -m unittest discover -s analysis/product_configuration_research/tools -p 'test_*.py' -v` covers missing context, timestamp ties, competing selections, persistence and partial evidence in the timing classifier. All eight tests passed. Python syntax and command help were checked; document audits reconcile the 27 strata to 300,000 unique source IDs and validate links, source-ID traceability and redaction. `git diff --check` passed. Production-pipeline tests and web requests are outside this research validation.

## Limits and next allowed step

No instrumentation contract proves whether a URL precedes or follows a selection. A shared IP is not a session key; BSON `_id` order is not guaranteed event-time order. A display label is not necessarily a URL slug. The same field name can denote filters, selected deltas, internal IDs or per-item settings depending on the event.

Review [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) before any implementation. The next checkpoint is approval of event-specific rules and, where needed, bounded instrumentation/session/reference validation. Existing extraction code was inspected for reusable helpers but was not changed or run by this research.
"""
    readme += shared_findings(checks)
    selector = profiles["select_product_option"]["counts"]
    selector_n = selector["totals"]["events"]
    conflicts = selector["events"].get("option_url_pair_conflict", 0)
    quality = checks.get("cross", {}).get("quality", {})
    reference = checks.get("reference", {})
    headline = ("## Findings requiring decisions\n\n"
        f"- Selector URL/option disagreements: **{conflicts:,}/{selector_n:,} ({conflicts / selector_n:.2%})**. The sample alone does not establish universal source precedence.\n")
    if quality:
        headline += f"- Quality changes: **{quality['groups_with_multiple_nonempty_quality_codes']:,}** sampled product/store/option groups have different nonempty quality codes with the same redacted URL. The selected grade is not established by URL tokens alone.\n"
    if checks.get("timing"):
        timing = checks["timing"]["conflict_outcomes"]
        total_timing = sum(timing.values())
        supportive = timing.get("confirmed_pre_to_selected", 0)
        contrary = sum(value for key, value in timing.items() if key.endswith("counterevidence"))
        headline += f"- The [requested timing study](SELECTION_TIMING.md) found **{supportive}/{total_timing}** strictly supportive sequences, **{contrary}/{total_timing}** counterevidence sequences and **{total_timing - supportive - contrary}/{total_timing}** inconclusive cases; weighted shares differ because rare keys were oversampled. Snapshot/delta preservation is approved; overlay implementation is not.\n"
    if reference:
        headline += f"- ID-to-token references: **{reference['ambiguous_reference_keys']:,}/{reference['reference_keys']:,}** sampled scoped keys are ambiguous. Treat internal IDs and localized cart labels as unresolved until a trusted reference exists.\n"
    routes = checks.get("cross", {}).get("routes", {})
    route_rates = []
    for name in ("view_all_recommend", "product_view_all_recommend_clicked"):
        if name in routes:
            values = routes[name]["events"]
            route_rates.append(f"{values.get('path_referrer_pair_conflict', 0)}/{values['total']} {name}")
    if route_rates:
        headline += "- Recommendation routes identify context products, while recommended targets can differ. Overlapping route/referrer values disagree in " + " and ".join(route_rates) + " events. Do not assume they are one state.\n"
    rare = {name: profiles[name]["counts"]["totals"]["events"] for name in ("back_to_product_action", "sorting_relevance_click_action")}
    headline += "- Rare strata: " + "; ".join(f"{name}: **{number}** random records" for name, number in rare.items()) + ". Small strata remain low confidence.\n\n"
    readme = readme.replace("## Evidence and method\n", headline + "## Evidence and method\n", 1)
    readme = readme.replace("This conditional stratification gives", "The complete root schema-name/type check found only `option` and `cart_products` as object/array roots in this pool; both were inspected recursively for relevant identifiers and choices. No additional opaque object/array root was observed.\n\nThis conditional stratification gives", 1)
    (root / "README.md").write_text(readme)


def main() -> None:
    """Validate a sample, investigate event strata in sequence, and write notes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--supplements", type=Path, help="Private follow-up metrics directory")
    parser.add_argument("--reuse-profiles", action="store_true", help="Render the same measured strata without profiling again")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.reuse_profiles:
        with args.sample.open() as stream:
            metadata = json.loads(next(stream))["_metadata"]
        counts = Counter({event: json.loads((args.private_dir / (event + ".json")).read_text())["counts"]["totals"]["events"] for event in EVENTS})
    else:
        metadata, counts = partition(args.sample, args.private_dir / "by_event")
    if set(counts) - set(EVENTS):
        raise ValueError("new event type observed; inspect and add an explicit research interpretation")
    missing = set(EVENTS) - set(counts)
    if missing:
        raise ValueError(f"random sample lacks event types: {sorted(missing)}; add a separate targeted stratum")
    hasher = hashlib.sha256()
    with args.sample.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            hasher.update(block)
    digest = hasher.hexdigest()
    if args.reuse_profiles and digest not in (root / "README.md").read_text():
        raise ValueError("profile reuse rejected: source SHA-256 differs from the recorded research pool")
    if sum(counts.values()) != metadata["requested_sample_size"]:
        raise ValueError("stratum totals differ from the captured source size")
    (root / "collections").mkdir(exist_ok=True)
    profiles = {}
    checks = load_checks(args.supplements)
    for event in EVENTS:
        profile = (json.loads((args.private_dir / (event + ".json")).read_text()) if args.reuse_profiles
                   else profile_event(args.private_dir / "by_event" / (event + ".jsonl")))
        profiles[event] = profile
        output = args.private_dir / (event + ".json")
        output.write_text(json.dumps(profile, ensure_ascii=False, indent=2))
        output.chmod(0o600)
        write_event(event, profile, sum(counts.values()), root, checks)
        print(f"Investigated {event}: {counts[event]:,} sampled events", flush=True)
    write_indexes(root, profiles, metadata, args.sample, digest, checks)
    print(f"Written {len(profiles)} event files, overview, methods and open questions")


if __name__ == "__main__":
    main()
