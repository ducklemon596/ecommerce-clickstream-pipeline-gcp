# product_detail_recommendation_noticed

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

Recommendation attention alongside a viewing_product_id. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **3,648 events** in this stratum (1.216% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:missing | 3,648 (100.00%) |
| product_id:missing | 3,648 (100.00%) |
| recommendation_product_id:missing | 3,648 (100.00%) |
| store_id:string | 3,648 (100.00%) |
| viewing_product_id:string | 3,648 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 70 (1.92%) | 71 (1.95%) |
| empty | 0 (0.00%) | 481 (13.19%) |
| external | 0 (0.00%) | 457 (12.53%) |
| invalid_or_nonweb | 0 (0.00%) | 4 (0.11%) |
| merchant_other_page | 0 (0.00%) | 1,749 (47.94%) |
| product_shaped | 3,578 (98.08%) | 846 (23.19%) |
| recommendation_route | 0 (0.00%) | 40 (1.10%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| alloy | 3499 |
| diamond | 2798 |
| itm_medium | 1745 |
| itm_source | 1745 |
| stone2 | 1374 |
| gclid | 633 |
| stone | 316 |
| pearl | 75 |
| stone3 | 72 |
| fbclid | 47 |
| keyword | 43 |
| matchtype | 43 |
| utm_medium | 41 |
| utm_source | 41 |
| synthetic | 40 |

Unknown/nonclassified current keys: `discountid` (5), `___store` (1). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| store_id:string | 3648 |
| viewing_product_id:string | 3648 |

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 442 |
| 7 @ www.glamira.co.uk | 252 |
| 12 @ www.glamira.fr | 218 |
| 14 @ www.glamira.it | 185 |
| 19 @ www.glamira.se | 161 |
| 41 @ www.glamira.com | 141 |
| 51 @ www.glamira.ro | 139 |
| 29 @ www.glamira.com.au | 134 |

Observed 63 store IDs and 61 current hosts. 5 store IDs had more than one current host; 6 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 82 (2.25%) |
| current_unknown_query_keys | 6 (0.16%) |
| current_nonproduction_host | 11 (0.30%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 2 (0.05%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| product_route_id_match | 1 (0.03%) |
| current_html_escaped | 1 (0.03%) |
| current_not_product_shaped | 70 (1.92%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.



## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### direct identity with url subset

```json
{
  "_id": "5e988e2998c9ed37840f61b5",
  "collection": "product_detail_recommendation_noticed",
  "store_id": "85",
  "viewing_product_id": "104631",
  "current_url": "https://www.glamira.cl/anillo-de-mujer-romantic-shape-4-mm.html?alloy=yellow-750",
  "referrer_url": "",
  "current_url_omitted_tracking_keys": [
    "gclid"
  ],
  "research_url_observations": {
    "current_url": {
      "scheme": "https:"
    },
    "referrer_url": {}
  }
}
```

### current not product shaped

```json
{
  "_id": "5ec2fd5b87725937124367ec",
  "collection": "product_detail_recommendation_noticed",
  "store_id": "71",
  "viewing_product_id": "101846",
  "current_url": "https://www.glamira.co.cr/checkout/cart/configure/id/2155466/",
  "referrer_url": "https://www.glamira.co.cr/checkout/cart/",
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
  "_id": "5ea28d2933eacf36f48a163c",
  "collection": "product_detail_recommendation_noticed",
  "store_id": "76",
  "viewing_product_id": "108772",
  "current_url": "https://dev3.glamira.de/glpe/glamira-ring-katherina-1.0-crt.html?diamond=blackdiamond&alloy=yellow-585",
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
  "_id": "5ea9f46773c8be36d02a9769",
  "collection": "product_detail_recommendation_noticed",
  "store_id": "12",
  "viewing_product_id": "103485",
  "current_url": "https://www.glamira.fr/glamira-ring-manilla.html?discountid=%5BREDACTED%5D&stone2=diamond-Swarovsky&diamond=diamond-Swarovsky&alloy=yellow-750",
  "referrer_url": "https://www.glamira.fr/offres-speciales/",
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

Proposed result class: **Viewed-page candidate, not recommended-target configuration**.

Source priority: viewing_product_id → store_id/current hostname → current URL subset, only after approving that the ID describes that page.

- Recommend considering the viewed page as one product candidate. These events do not establish that a recommended product inherits the viewed product's alloy/stone parameters.
- Do not attach current URL options to recommendation_product_id. Treat recommended IDs as separate identity-only leads unless their own page/configuration evidence exists.
- A referrer is a previous-page reference, not the target of the recommendation. Product/page association requires corroboration rather than an automatic fallback.

Alternative and trade-off: Crawling every recommendation ID with the current page's options could recover more records but mixes different products. Recommend viewed-page evidence and separate unresolved target IDs.

**Sampled opportunity, not achieved recovery:** 3,566 (97.75%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 82 (2.25%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Approve the viewed-page URL subset only, keeping recommendation attention as context?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
