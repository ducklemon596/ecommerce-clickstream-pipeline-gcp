# Selection timing: observed URL snapshot versus selected delta

Research follow-up requested and observed 6 November 2026. **Approved for now:** preserve both sources separately. An overlay remains a proposal; none was applied or emitted by these tools.

## Method and evidence limits

The 300,000-event random pool contained 2,982 conflicting select_product_option events. Seed `20261106` selected 120 conflict anchors stratified by selected key, plus 20 missing-key and 20 already-matching controls. The conflict cohort covers 105 products and 34 stores. Sampling is without replacement; rare keys are deliberately oversampled.

Each exact anchor was read through `_id_`, followed by at most 1,000 indexed predecessors and 1,000 successors. Exactly **320,000 neighboring records** were examined, with device_id/product_id/store_id equality applied on the VM. Matching context is ordered by actual `time_stamp`, restricted to ±1,800 seconds. The device value is never exported. Device history is not automatically a session, and anchors can be correlated.

The collection has no device/product/time index. These are bounded storage neighborhoods, not guaranteed globally nearest events in time. Missing context is censoring, not evidence that a transition did not happen. A global device/session reconstruction would need a separately justified access strategy; no index or source write was performed.

## Quantified outcomes

**30/120 (25.00%)** showed the strict visible pre-value → selected-value sequence. **11/120 (9.17%)** showed counterevidence to a simple prompt URL-catch-up interpretation. **79/120 (65.83%)** were inconclusive.

Stratum-weighted fractions are **25.97% supportive / 8.76% counterevidence / 65.27% inconclusive**. They refer to the 2,982 conflicts in the source random pool under this bounded-window procedure, not all 41.4M events or complete sessions. No confidence interval or population-wide causal claim is established.

| Classification | Anchors | Unweighted cohort share | Stratum-weighted share |
| --- | --- | --- | --- |
| inconclusive_anchor_timestamp_tie | 4 | 3.33% | 3.78% |
| inconclusive_no_successor_url | 30 | 25.00% | 28.09% |
| confirmed_pre_to_selected | 30 | 25.00% | 25.97% |
| inconclusive_intervening_selection | 39 | 32.50% | 29.46% |
| persistent_old_url_counterevidence | 8 | 6.67% | 5.96% |
| inconclusive_one_old_successor | 6 | 5.00% | 3.94% |
| different_successor_counterevidence | 3 | 2.50% | 2.81% |

| Selected key | Conflicts in source pool | Inspected | Strict supportive sequence | Counterevidence |
| --- | --- | --- | --- | --- |
| alloy | 2370 | 85 | 25 | 4 |
| diamond | 435 | 15 | 2 | 4 |
| stone2 | 161 | 10 | 1 | 2 |
| stone3 | 16 | 10 | 2 | 1 |

Strict support requires the nearest available earlier URL to contain the old value and the earliest available later URL to contain the selected value, with no intervening different selection on that key and no ambiguous timestamp tie. Counterevidence includes at least two later old-value URL observations without an observed competing selection, or a different successor value. Persistent old URLs do not prove that the selection failed: the URL can remain stale, and unobserved events can still matter. These classifications test the chosen key, not every dimension of a full configuration.

Seconds until the next corroborating URL among strict supportive cases: `{"minimum": 1, "median": 6.5, "maximum": 62}`. These observed intervals are not a universal session timeout or overlay threshold.

## Comparison cohorts

| missing_key control outcome | Anchors |
| --- | --- |
| inconclusive_intervening_selection | 7 |
| inconclusive_no_successor_url | 5 |
| missing_key_different_successor | 1 |
| missing_key_forward_support | 5 |
| missing_key_stays_absent | 2 |

| match control outcome | Anchors |
| --- | --- |
| control_url_remains_selected | 5 |
| inconclusive_anchor_timestamp_tie | 2 |
| inconclusive_intervening_selection | 13 |

Already-matching anchors demonstrate that the URL is not universally a visibly different pre-selection state. Missing-key anchors can add only partial evidence; the absent dimensions and website defaults remain unknown. Intervening choices and timestamp ties remain inconclusive.

## Traceable examples

### confirmed pre to selected

```json
{
  "_id": "5e9b536973c8be36d01b0b2c",
  "kind": "conflict",
  "key": "alloy",
  "product_id": "95215",
  "store_id": "19",
  "selected_value": "white-750",
  "anchor_url_values": [
    "red-750"
  ],
  "matched_context": 2,
  "status": "confirmed_pre_to_selected",
  "next_url_value": "white-750",
  "next_source_id": "5e9b539593ed00371e88f204",
  "seconds_to_next_url": 44,
  "previous_url_value": "red-750",
  "previous_source_id": "5e9b535984f6c5377e473d74"
}
```

### persistent old url counterevidence

```json
{
  "_id": "5e8b623cb9a5fa3754026c07",
  "kind": "conflict",
  "key": "alloy",
  "product_id": "94964",
  "store_id": "10",
  "selected_value": "white-silber",
  "anchor_url_values": [
    "white_red-375"
  ],
  "matched_context": 5,
  "status": "persistent_old_url_counterevidence",
  "next_url_value": "white_red-375",
  "next_source_id": "5e8b623e5c503836d6723747",
  "seconds_to_next_url": 2,
  "previous_url_value": "white_red-375",
  "previous_source_id": "5e8b61e771a3b936be3634e6"
}
```

### different successor counterevidence

```json
{
  "_id": "5ed38bf466a4b337240f274a",
  "kind": "conflict",
  "key": "alloy",
  "product_id": "109665",
  "store_id": "29",
  "selected_value": "red_white-375",
  "anchor_url_values": [
    "yellow-375"
  ],
  "matched_context": 3,
  "status": "different_successor_counterevidence",
  "next_url_value": "white-375",
  "next_source_id": "5ed38c0684f6c5377e8f73c6",
  "seconds_to_next_url": 18,
  "previous_url_value": "yellow-375",
  "previous_source_id": "5ed38bdc71a3b936be8cd2cc"
}
```

### inconclusive intervening selection

```json
{
  "_id": "5eb07fcb71a3b936be5c8f7c",
  "kind": "conflict",
  "key": "alloy",
  "product_id": "103324",
  "store_id": "7",
  "selected_value": "yellow-585",
  "anchor_url_values": [
    "red-585"
  ],
  "matched_context": 4,
  "status": "inconclusive_intervening_selection",
  "next_url_value": "white_red-585",
  "next_source_id": "5eb07fd7e73652372adbf392",
  "seconds_to_next_url": 12
}
```

## Conditional inference proposal — approval required

Recommend retaining the raw observed URL subset and selected delta for every anchor. For a later approved inference branch, require an explicit product/store/current-host association, one recognized selected key with an approved slug value, one unambiguous prior URL value and a later same-device/product/store URL corroborating the selected value before a competing same-key selection. Do not resolve second-level ties using `_id` order.

Only then propose a separate **inferred, partial post-selection observation** that replaces the changed key in the observed URL subset. Preserve the source snapshot and delta alongside it, with anchor/prior/successor IDs and timing evidence. Do not claim website defaults, unrepresented quality dimensions or untouched missing options are resolved. Malformed URL pairs, unknown key mappings, conflicts and incomplete context remain unresolved.

This study checks the selected key, not the stability of every untouched option. Generating an entire overlaid option set would additionally require checking those other dimensions; otherwise the result could be a hybrid state never observed. Where a later URL already directly records the desired state, prefer that observed evidence for crawl input and retain the inferred transition separately. Overlaying is useful only as an explicitly qualified state hypothesis, not a way to increase resolved-configuration counts automatically.

Alternatives: URL-only handling is simple but loses selected deltas; universal selected-value overlay assumes ordering that the counterexamples do not establish. The recommended research proposal keeps both sources, uses directly observed later state where available, and considers a separately marked inference branch only after all stated conditions are reviewed.

The 30 supportive anchors justify investigating this conditional branch; they do not authorize a universal overlay. The 11 counterevidence anchors and 79 inconclusive anchors must not be silently dropped or forced into it. Review and approval are still required before implementation.

## Reproduce and next decision

Private inputs: `timing_cohort.json` and `timing_probes.jsonl`; output metrics: `timing_results.json` beside the source pool. `tools/timing.py cohort` selects anchors; `tools/capture.py --script analysis/product_configuration_research/tools/timing.mjs --ids-file <cohort>` performs indexed read-only probes; `tools/timing.py summarize --cohort <cohort> --probes <probes> --output <metrics> --report analysis/product_configuration_research/SELECTION_TIMING.md` renders this note. Supply the same authorized SSH/config flags documented in the research README. No overlay, configuration export or crawler runs.

Please review the conditional inference proposal, especially whether bounded same-device context is sufficient or a verified session/instrumentation contract is required. See [the event note](collections/select_product_option.md) and [open decisions](OPEN_QUESTIONS.md).
