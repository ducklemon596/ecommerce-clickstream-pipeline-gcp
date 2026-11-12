# view_all_recommend

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

Recommendation-list context with product_id and a broad option/filter object. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **259 events** in this stratum (0.086% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:object | 259 (100.00%) |
| product_id:string | 259 (100.00%) |
| recommendation_product_id:missing | 259 (100.00%) |
| store_id:string | 259 (100.00%) |
| viewing_product_id:missing | 259 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 0 (0.00%) | 5 (1.93%) |
| empty | 0 (0.00%) | 10 (3.86%) |
| external | 0 (0.00%) | 1 (0.39%) |
| merchant_other_page | 0 (0.00%) | 1 (0.39%) |
| product_shaped | 0 (0.00%) | 242 (93.44%) |
| recommendation_route | 259 (100.00%) | 0 (0.00%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |

Unknown/nonclassified current keys: none observed. Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| option.Kollektion:string | 259 |
| option.alloy:string | 259 |
| option.category id:string | 259 |
| option.finish:string | 259 |
| option.kollektion_id:string | 259 |
| option.pearlcolor:string | 259 |
| option.price:string | 259 |
| option.stone:string | 259 |
| option:object | 259 |
| product_id:string | 259 |
| store_id:string | 259 |

| Top-level option item field | Occurrences |
| --- | --- |
| Kollektion:string | 259 |
| alloy:string | 259 |
| category id:string | 259 |
| finish:string | 259 |
| kollektion_id:string | 259 |
| pearlcolor:string | 259 |
| price:string | 259 |
| stone:string | 259 |

Observed option labels/keys: `Kollektion` (259), `alloy` (259), `category id` (259), `finish` (259), `kollektion_id` (259), `pearlcolor` (259), `price` (259), `stone` (259).

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 32 |
| 7 @ www.glamira.co.uk | 29 |
| 19 @ www.glamira.se | 21 |
| 41 @ www.glamira.com | 20 |
| 8 @ www.glamira.es | 15 |
| 12 @ www.glamira.fr | 12 |
| 30 @ www.glamira.no | 12 |
| 11 @ www.glamira.nl | 11 |

Observed 42 store IDs and 40 current hosts. 0 store IDs had more than one current host; 2 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 259 (100.00%) |
| current_unknown_query_keys | 0 (0.00%) |
| current_nonproduction_host | 0 (0.00%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 0 (0.00%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 259 (100.00%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.

### Targeted route-association comparisons within the pool

| Route check (event count) | Observed |
| --- | --- |
| path_referrer_pair_conflict | 118 |
| product_id_matches_route_id | 259 |
| some_path_referrer_pairs_match | 230 |
| total | 259 |

| Path-segment key | Occurrences |
| --- | --- |
| accent_color | 1 |
| alloy | 254 |
| diamond | 201 |
| finish | 25 |
| id | 259 |
| pearlcolor | 6 |
| price | 259 |
| profile | 26 |
| stone | 34 |
| stone2 | 107 |

A matching `/id/` segment strengthens source-product association, not the claim that route filters are the product's complete settings. A referrer pair can agree on one dimension and disagree on another; those event counters overlap. Price/category/list facets are not automatically crawl options. No precedence or path-to-query rule is approved.

## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### representative

```json
{
  "_id": "5ed181c8c671fc36b73d41c4",
  "collection": "view_all_recommend",
  "store_id": "6",
  "product_id": "103101",
  "option": {
    "alloy": "white-375",
    "stone": "6",
    "pearlcolor": "",
    "finish": "",
    "price": "394.00",
    "category id": "27",
    "Kollektion": "Lovely",
    "kollektion_id": "1289"
  },
  "current_url": "https://www.glamira.de/county/recommendation/list/id/103101/alloy/white-375/diamond/pink-tourmaline/stone2/diamond-swarovsky/price/394.00",
  "referrer_url": "https://www.glamira.de/glamira-ring-aizaya.html?alloy=white-375&diamond=pink-tourmaline&stone2=diamond-Swarovsky",
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

**Sampled opportunity, not achieved recovery:** 0 (0.00%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 259 (100.00%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

MODERATE structural coverage: 30–499 sampled events; semantic conclusions remain provisional.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Should product_id be retained as context-only until /id/ and filter semantics are verified, rather than interpreting the entire option object as product settings?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
