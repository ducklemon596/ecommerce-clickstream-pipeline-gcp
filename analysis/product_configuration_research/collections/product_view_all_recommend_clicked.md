# product_view_all_recommend_clicked

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

A recommendation-list interaction with viewed and recommended identities. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **119 events** in this stratum (0.040% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:missing | 119 (100.00%) |
| product_id:missing | 119 (100.00%) |
| recommendation_product_id:string | 119 (100.00%) |
| store_id:string | 119 (100.00%) |
| viewing_product_id:string | 119 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 0 (0.00%) | 2 (1.68%) |
| external | 0 (0.00%) | 1 (0.84%) |
| merchant_other_page | 0 (0.00%) | 2 (1.68%) |
| product_shaped | 0 (0.00%) | 114 (95.80%) |
| recommendation_route | 119 (100.00%) | 0 (0.00%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |

Unknown/nonclassified current keys: none observed. Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| recommendation_product_id:string | 119 |
| recommendation_product_position:string | 119 |
| store_id:string | 119 |
| viewing_product_id:string | 119 |

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 41 @ www.glamira.com | 17 |
| 6 @ www.glamira.de | 16 |
| 7 @ www.glamira.co.uk | 9 |
| 10 @ www.glamira.ch | 6 |
| 12 @ www.glamira.fr | 6 |
| 19 @ www.glamira.se | 6 |
| 17 @ www.glamira.com.tr | 5 |
| 38 @ www.glamira.ca | 5 |

Observed 31 store IDs and 28 current hosts. 0 store IDs had more than one current host; 3 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 119 (100.00%) |
| current_unknown_query_keys | 0 (0.00%) |
| current_nonproduction_host | 0 (0.00%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 0 (0.00%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 119 (100.00%) |
| viewed_recommended_equal | 1 (0.84%) |
| viewed_recommended_differ | 118 (99.16%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.

### Targeted route-association comparisons within the pool

| Route check (event count) | Observed |
| --- | --- |
| path_referrer_pair_conflict | 64 |
| recommendation_product_id_differs_from_route_id | 118 |
| recommendation_product_id_matches_route_id | 1 |
| some_path_referrer_pairs_match | 110 |
| total | 119 |
| viewing_product_id_matches_route_id | 119 |

| Path-segment key | Occurrences |
| --- | --- |
| alloy | 117 |
| diamond | 95 |
| finish | 12 |
| id | 119 |
| pearlcolor | 2 |
| price | 119 |
| profile | 13 |
| stone | 14 |
| stone2 | 55 |

A matching `/id/` segment strengthens source-product association, not the claim that route filters are the product's complete settings. A referrer pair can agree on one dimension and disagree on another; those event counters overlap. Price/category/list facets are not automatically crawl options. No precedence or path-to-query rule is approved.

## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### representative

```json
{
  "_id": "5ed6e649385d1f36b89d1cae",
  "collection": "product_view_all_recommend_clicked",
  "store_id": "39",
  "viewing_product_id": "92340",
  "recommendation_product_id": "89485",
  "recommendation_product_position": "",
  "current_url": "https://www.glamira.ca/fr/county/recommendation/list/id/92340/alloy/white-585/diamond/diamond-brillant/stone2/diamond-brillant/price/1,999.00",
  "referrer_url": "https://www.glamira.ca/fr/glamira-ring-kailey.html?alloy=white-585&diamond=diamond-Brillant&stone2=diamond-Brillant",
  "referrer_url_omitted_tracking_keys": [
    "itm_medium",
    "itm_source"
  ],
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

Proposed result class: **Context/target identities require association review**.

Source priority: Explicit IDs with their original field names → store/current hostname → recommendation-route segments as context → any independently corroborated product-page reference.

- The current recommendation-list route can encode /id/, alloy, stone and price in its path. Do not treat the route as a product page or assume every segment is a crawl option.
- Recommend preserving identities as unresolved context/target leads. The source product, recommended target and list filters can be different objects.
- Referrer URLs may retain a product-page configuration. Permit recovery only if an independent product/store/page association is established and use of referrers is explicitly approved.
- Do not merge the option object with path segments: category, collection and price filters are not established product options. A product URL may be recoverable while its configuration remains unknown.

Alternative and trade-off: Parsing all route pairs into options is easy but confuses page filters with product settings. Recommend withholding configuration recovery from this route until its semantics are approved.

**Sampled opportunity, not achieved recovery:** 0 (0.00%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 119 (100.00%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

MODERATE structural coverage: 30–499 sampled events; semantic conclusions remain provisional.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Which ID denotes the crawl target, and what independent product/store evidence is sufficient before considering a previous product URL? Conditional corroboration is already required.

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
