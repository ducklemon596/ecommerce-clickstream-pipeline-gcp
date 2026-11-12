# search_box_action

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

Search interaction on varying page contexts, sometimes a product-shaped URL. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **1,742 events** in this stratum (0.581% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:missing | 1,742 (100.00%) |
| product_id:missing | 1,742 (100.00%) |
| recommendation_product_id:missing | 1,742 (100.00%) |
| store_id:string | 1,742 (100.00%) |
| viewing_product_id:missing | 1,742 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 47 (2.70%) | 36 (2.07%) |
| empty | 0 (0.00%) | 159 (9.13%) |
| external | 0 (0.00%) | 423 (24.28%) |
| invalid_or_nonweb | 0 (0.00%) | 7 (0.40%) |
| merchant_other_page | 1,415 (81.23%) | 935 (53.67%) |
| product_shaped | 277 (15.90%) | 180 (10.33%) |
| recommendation_route | 3 (0.17%) | 2 (0.11%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| gclid | 379 |
| q | 304 |
| alloy | 238 |
| diamond | 169 |
| itm_medium | 95 |
| itm_source | 95 |
| stone2 | 86 |
| p | 85 |
| keyword | 29 |
| matchtype | 28 |
| filter-diamond | 27 |
| stone | 21 |
| order | 20 |
| dir | 19 |
| imgps | 6 |

Unknown/nonclassified current keys: `q` (304), `p` (85), `filter-diamond` (27), `order` (20), `dir` (19), `imgps` (6), `filter-alloycolour` (4), `mode` (3), `kkkalloy` (1), `limit` (1). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| store_id:string | 1742 |

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 7 @ www.glamira.co.uk | 223 |
| 6 @ www.glamira.de | 190 |
| 41 @ www.glamira.com | 168 |
| 12 @ www.glamira.fr | 115 |
| 29 @ www.glamira.com.au | 84 |
| 19 @ www.glamira.se | 67 |
| 14 @ www.glamira.it | 65 |
| 8 @ www.glamira.es | 63 |

Observed 62 store IDs and 58 current hosts. 1 store IDs had more than one current host; 4 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 1,493 (85.71%) |
| current_unknown_query_keys | 384 (22.04%) |
| current_nonproduction_host | 1 (0.06%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 1 (0.06%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 1,465 (84.10%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.

### Targeted route-association comparisons within the pool

| Route check (event count) | Observed |
| --- | --- |
| path_referrer_pair_conflict | 3 |
| some_path_referrer_pairs_match | 3 |
| total | 3 |

| Path-segment key | Occurrences |
| --- | --- |
| alloy | 3 |
| diamond | 2 |
| finish | 1 |
| id | 3 |
| price | 3 |
| profile | 1 |
| stone | 1 |
| stone2 | 2 |

A matching `/id/` segment strengthens source-product association, not the claim that route filters are the product's complete settings. A referrer pair can agree on one dimension and disagree on another; those event counters overlap. Price/category/list facets are not automatically crawl options. No precedence or path-to-query rule is approved.

## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### representative

```json
{
  "_id": "5ec6f9bb9d843b37065fe449",
  "collection": "search_box_action",
  "store_id": "38",
  "current_url": "https://www.glamira.ca/necklaces/375-white-gold/",
  "referrer_url": "https://www.google.com/[REDACTED-EXTERNAL-PATH]",
  "current_url_omitted_tracking_keys": [
    "gclid"
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

### current nonproduction host

```json
{
  "_id": "5e9fe2f66b9438374ef4c978",
  "collection": "search_box_action",
  "store_id": "6",
  "current_url": "https://test.glamira.de/glde/glamira-pendant-illa.html?alloy=white-silber",
  "referrer_url": "",
  "research_url_observations": {
    "current_url": {
      "scheme": "https:"
    },
    "referrer_url": {}
  }
}
```

### current unknown query keys

```json
{
  "_id": "5ea9627ebb30d637187f8f4c",
  "collection": "search_box_action",
  "store_id": "29",
  "current_url": "https://www.glamira.com.au/catalogsearch/result/?q=%5BREDACTED%5D",
  "referrer_url": "https://www.glamira.com.au/",
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

Proposed result class: **URL lead without a verified product ID**.

Source priority: Valid current HTTP(S) storefront URL → independently verified product/page mapping. Store is explicit store_id plus observed current hostname.

- Recommend retaining a product-shaped current URL only as an unresolved lead. A slug and query can identify a page candidate but do not supply the required product_id.
- A future approved cross-event join may associate an exact storefront/path with a product ID if mappings are consistent. Do not infer IDs from arbitrary slug digits.
- Do not use a previous referrer product as the identity of the current page. Invalid, file, external and development URLs need their own review state.

Alternative and trade-off: URL-only crawling could discover an ID later, but that would be a separately approved crawler task. Recommend review leads and no product/configuration tuple yet.

**Sampled opportunity, not achieved recovery:** 0 (0.00%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 0 (0.00%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Keep product-shaped current URLs as review leads needing a verified product ID, rather than inventing IDs from slugs?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
