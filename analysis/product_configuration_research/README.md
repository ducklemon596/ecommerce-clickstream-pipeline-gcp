# Product configuration reconstruction research

**Research only; proposals await user approval.** Observed 6 November 2026 (Asia/Ho_Chi_Minh); source metadata below uses UTC. Start with [the event matrix](EVENT_OVERVIEW.md) and [open decisions](OPEN_QUESTIONS.md). Each of the 27 [event files](collections/) contains measured patterns, counterexample searches, traceable excerpts and an event-specific proposed source priority.

## Findings requiring decisions

- Selector URL/option disagreements: **2,982/63,716 (4.68%)**. The sample alone does not establish universal source precedence.
- Quality changes: **489** sampled product/store/option groups have different nonempty quality codes with the same redacted URL. The selected grade is not established by URL tokens alone.
- The [requested timing study](SELECTION_TIMING.md) found **30/120** strictly supportive sequences, **11/120** counterevidence sequences and **79/120** inconclusive cases; weighted shares differ because rare keys were oversampled. Snapshot/delta preservation is approved; overlay implementation is not.
- ID-to-token references: **3,951/45,491** sampled scoped keys are ambiguous. Treat internal IDs and localized cart labels as unresolved until a trusted reference exists.
- Recommendation routes identify context products, while recommended targets can differ. Overlapping route/referrer values disagree in 118/259 view_all_recommend and 64/119 product_view_all_recommend_clicked events. Do not assume they are one state.
- Rare strata: back_to_product_action: **2** random records; sorting_relevance_click_action: **15** random records. Small strata remain low confidence.

- **Option ID semantics (12/11/2026):** ID-only `option` arrays on product pages appear to record the product default, not the selection. See [OPTION_ID_SEMANTICS.md](OPTION_ID_SEMANTICS.md).

## Evidence and method

The prior exact MongoDB `distinct(collection)` investigation on 5 November 2026 confirmed 27 event names. This run rechecks the names observed in a new bounded random pool against that list, rather than repeating an unindexed full scan. Current collection metadata is below. Metadata document count is an estimate, not a new source-parity validation.

```json
{
  "captured_at": "2026-11-05T18:57:19.400Z",
  "namespace": "countly.summary",
  "collection_uuid": "f2b938ba-4f48-46e3-9a76-45b3ab3af985",
  "server_version": "8.0.34",
  "estimated_documents": 41432473,
  "indexes": [
    {
      "name": "_id_",
      "key": {
        "_id": 1
      }
    }
  ],
  "method": "$sample first, no seed; redact before SSH output",
  "requested_sample_size": 300000
}
```

Private evidence: `data/product_configuration_research/random_300k_v2.jsonl`; SHA-256 `3363db8fb705edd9cda6182bdf6c169ea6f6366e7240eadf7056b9370c218a3d`. The pool contains **300,000 events**. `$sample` is the first aggregation stage; its randomness is not seeded. Root product/option/store fields and URLs are projected; other root field **names/types only** support schema and session-key investigation. MongoDB output is redacted on the VM before SSH transfer. No IP, email, device-ID values or credentials remain in the final evidence. `_id` is retained for direct read-only point verification.

Privacy audit additionally removed three literal IP URL hosts from the local private evidence and corresponding counters. The hash above identifies the final redacted pool. The sampler now redacts such hosts on the VM too; `tools/privacy.py` records the reproducible local address-host cleanup. No raw address appeared in published examples. The first large capture returned no usable output and was rejected; transport probes were excluded from all measurement denominators. Only the completed pool contributes to reported sample metrics.

The pool is partitioned by actual event type locally, then each stratum is investigated sequentially. All sampled records in each stratum contribute metrics, not only a first-N prefix. Deterministic hashes select normal and edge-case examples from the entire stratum. URL/option disagreement, missing values, translated labels, repeated keys, malformed encoding, unknown keys, development hosts, multi-item carts, null IDs and recommendation-owner differences are deliberately searched. Zero observations do not establish impossibility. Very rare strata remain low confidence.

The complete root schema-name/type check found only `option` and `cart_products` as object/array roots in this pool; both were inspected recursively for relevant identifiers and choices. No additional opaque object/array root was observed.

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
uv run python analysis/product_configuration_research/tools/capture.py \
  --project "$GCP_PROJECT" --zone "$GCP_ZONE" --vm "$GCP_VM" \
  --ssh-user "$VM_USER" --mongo-user "$MONGO_USER" \
  --config '~/.config/glamira/restore.yml' --size 300000 \
  --output data/product_configuration_research/new_pool.jsonl
uv run python analysis/product_configuration_research/tools/report.py \
  --sample data/product_configuration_research/new_pool.jsonl \
  --private-dir data/product_configuration_research/new_profiles
```

Optional pool-only follow-ups use `tools/reference.py` and `tools/cross_checks.py`, each with `--sample` and `--output`; they do not query MongoDB. For this recorded run, regenerate the notes with the original pool and `--private-dir data/product_configuration_research/profiles_v1 --reuse-profiles --supplements data/product_configuration_research`. Reuse checks the sample SHA-256 already recorded here. Capture also supports repeated `--id <ObjectId>` for indexed point verification, and `--script tools/sequence.mjs` for the documented bounded context probes.

Capture requires authorized SSH access, VM Python/PyYAML and mongosh. The protected VM YAML supplies only the password to a child-process environment; credentials are never arguments or report content. Sampling uses read-only commands; existing source indexes are listed but not altered. The VM client talks to MongoDB loopback. Generated evidence and profiles remain ignored under `data/` with private file permissions.

`report.py` writes these research Markdown files and private per-event aggregate/evidence JSON. Use a new private directory for a new pool; it rejects implicit checkpoint reuse. These tools are research sampling/profiling only, not an extraction/deduplication pipeline. They do not test the website. The user-verified `/catalog/product/view/id/{product_id}` endpoint is contextual input, not a new HTTP verification.

Local verification: `uv run python -m unittest discover -s analysis/product_configuration_research/tools -p 'test_*.py' -v` covers missing context, timestamp ties, competing selections, persistence and partial evidence in the timing classifier. All eight tests passed. Python syntax and command help were checked; document audits reconcile the 27 strata to 300,000 unique source IDs and validate links, source-ID traceability and redaction. `git diff --check` passed. Production-pipeline tests and web requests are outside this research validation.

## Limits and next allowed step

No instrumentation contract proves whether a URL precedes or follows a selection. A shared IP is not a session key; BSON `_id` order is not guaranteed event-time order. A display label is not necessarily a URL slug. The same field name can denote filters, selected deltas, internal IDs or per-item settings depending on the event.

Review [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) before any implementation. The next checkpoint is approval of event-specific rules and, where needed, bounded instrumentation/session/reference validation. Existing extraction code was inspected for reusable helpers but was not changed or run by this research.

## Additional measured findings

A strict reference sensitivity check found **3,951/45,491 (8.69%)** product/store/option/value-ID keys associated with more than one URL key/token, even though each witness's selected value agreed with its own URL. Therefore ID equality alone cannot supply a trusted slug mapping. This may reflect stale identifiers, catalog/instrumentation changes or another unverified behavior; the cause was not established.

One point-verified counterexample: product `85792`, store `6`, option ID `57620`, value ID `307365` appeared with `red-375` at `_id=5ebfc2d166936336eea1ac4b` and `white-platin` at `_id=5ed3c87978aa7636ca4d7b0e`. These are substantive different tokens, not a capitalization-only alias. A unique mapping inside this sample also does not prove a universal mapping.

Nine exact `_id` point reads verified the user-supplied add-to-cart record and important counterexamples. Three additional indexed context probes examined at most **6,000 neighboring records** combined. Raw device values stayed on the VM; nine point-read records had a nonempty device_id, one had a nonempty user_id_db, and none had a nonempty session_id. These targeted counts cannot be extrapolated.

For selector anchor `5e9a9ca39fade236dccec573`, the URL said `alloy=white-585` while the selected field said `red-585`; a same-device/product/store observation 7 seconds later carried `alloy=red-585`. This supports a stale-URL hypothesis for that example, not a universal overlay rule. Another probe found multiple different selected alloys while the URL remained queryless. Grade selections also changed with the same URL subset. See the selector and quality event files for traceable excerpts.

The reference check emits aggregate measurements and a few witness IDs, not a lookup table or reconstructed configuration dataset. Its sample/reference overlap makes potential mapping coverage optimistic. Private follow-up artifacts are `reference_comparison.json`, `cross_checks.json`, `targeted_points.jsonl`, and `bounded_sequence_probes.jsonl` beside the captured pool. Their records are not added to random-sample denominators.

The subsequent user-requested [stratified timing study](SELECTION_TIMING.md) adds 160 exact anchors and 320,000 bounded neighboring-record reads. These are separate research cohorts and are not included in the 300,000-event random-pool denominators.
