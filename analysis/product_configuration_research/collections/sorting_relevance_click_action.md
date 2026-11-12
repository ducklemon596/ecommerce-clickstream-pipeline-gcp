# sorting_relevance_click_action

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

A recommendation target ID/position attached to sorting/listing context. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **15 events** in this stratum (0.005% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:missing | 15 (100.00%) |
| product_id:missing | 15 (100.00%) |
| recommendation_product_id:null | 2 (13.33%) |
| recommendation_product_id:string | 13 (86.67%) |
| store_id:string | 15 (100.00%) |
| viewing_product_id:missing | 15 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| merchant_other_page | 15 (100.00%) | 15 (100.00%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| order | 13 |
| mode | 12 |
| p | 2 |

Unknown/nonclassified current keys: `order` (13), `mode` (12), `p` (2). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| store_id:string | 15 |
| recommendation_product_id:string | 13 |
| recommendation_product_position:string | 13 |
| recommendation_product_id:null | 2 |
| recommendation_product_position:null | 2 |

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 10 @ www.glamira.ch | 1 |
| 11 @ www.glamira.nl | 1 |
| 16 @ www.glamira.fi | 1 |
| 38 @ www.glamira.ca | 1 |
| 41 @ www.glamira.com | 1 |
| 45 @ www.glamira.cz | 1 |
| 46 @ www.glamira.hu | 1 |
| 50 @ www.glamira.pl | 1 |

Observed 15 store IDs and 15 current hosts. 0 store IDs had more than one current host; 0 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 15 (100.00%) |
| current_unknown_query_keys | 13 (86.67%) |
| current_nonproduction_host | 0 (0.00%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 0 (0.00%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 15 (100.00%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.



## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### representative

```json
{
  "_id": "5eb83d4c30c31e3730022cf4",
  "collection": "sorting_relevance_click_action",
  "store_id": "62",
  "recommendation_product_id": "102009",
  "recommendation_product_position": "22",
  "current_url": "https://www.glamira.com.mx/anillos-de-compromiso/carat-4.01,20.0/oro-blanco-585/esmeralda/?order=%5BREDACTED%5D&mode=%5BREDACTED%5D",
  "referrer_url": "https://www.glamira.com.mx/anillos-de-compromiso/carat-4.01,20.0/esmeralda/?order=%5BREDACTED%5D&mode=%5BREDACTED%5D",
  "research_url_observations": {
    "current_url": {
      "scheme": "https:"
    },
    "referrer_url": {
      "scheme": "https:"
    }
  }
}
```



## 5. Proposed Strategy — approval pending

Proposed result class: **Recommended product identity only**.

Source priority: Nonempty recommendation_product_id → event store/current storefront → a separate product lookup using the user-verified ID route. No current-page configuration is transferred.

- Recommend keeping a valid recommended target ID as an identity-only lead, pending approval that the field denotes the clicked target.
- Landing/listing options describe the page context. They do not identify the target product's selected settings; mark target options unknown.
- Null or blank recommended IDs are not recoverable through this rule. A referrer can describe another product and must not fill the target identity by assumption.

Alternative and trade-off: Discarding all such events reduces product-identity coverage; assigning page filters as target options corrupts configuration coverage. Recommend identity-only leads, not resolved configurations.

**Sampled opportunity, not achieved recovery:** 0 (0.00%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 0 (0.00%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

LOW: fewer than 30 sampled events; rare-event semantics and exceptions need further evidence.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Approve target IDs only after validating their meaning, without inheriting category filters as target options?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
