# product_detail_recommendation_visible

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

Recommendation visibility alongside a viewing_product_id. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **9,302 events** in this stratum (3.101% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:missing | 9,302 (100.00%) |
| product_id:missing | 9,302 (100.00%) |
| recommendation_product_id:missing | 9,302 (100.00%) |
| store_id:string | 9,302 (100.00%) |
| viewing_product_id:string | 9,302 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 142 (1.53%) | 133 (1.43%) |
| empty | 0 (0.00%) | 1,303 (14.01%) |
| external | 0 (0.00%) | 1,585 (17.04%) |
| invalid_or_nonweb | 1 (0.01%) | 12 (0.13%) |
| merchant_other_page | 0 (0.00%) | 4,418 (47.50%) |
| product_shaped | 9,159 (98.46%) | 1,778 (19.11%) |
| recommendation_route | 0 (0.00%) | 73 (0.78%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| alloy | 8877 |
| diamond | 6807 |
| itm_medium | 4233 |
| itm_source | 4233 |
| stone2 | 3353 |
| gclid | 1988 |
| stone | 866 |
| keyword | 165 |
| matchtype | 165 |
| pearl | 152 |
| stone3 | 143 |
| utm_medium | 113 |
| utm_source | 111 |
| utm_campaign | 84 |
| fbclid | 74 |

Unknown/nonclassified current keys: `discountid` (8), `___store` (7), `client` (5), `ctype` (3), `zarsrc` (1). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| store_id:string | 9302 |
| viewing_product_id:string | 9302 |

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 1178 |
| 7 @ www.glamira.co.uk | 674 |
| 12 @ www.glamira.fr | 518 |
| 14 @ www.glamira.it | 514 |
| 41 @ www.glamira.com | 429 |
| 8 @ www.glamira.es | 406 |
| 19 @ www.glamira.se | 380 |
| 51 @ www.glamira.ro | 318 |

Observed 68 store IDs and 65 current hosts. 5 store IDs had more than one current host; 7 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 293 (3.15%) |
| current_unknown_query_keys | 21 (0.23%) |
| current_nonproduction_host | 18 (0.19%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 8 (0.09%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 143 (1.54%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.



## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### direct identity with url subset

```json
{
  "_id": "5ebedf6678aa7636ca30ddae",
  "collection": "product_detail_recommendation_visible",
  "store_id": "19",
  "viewing_product_id": "98401",
  "current_url": "https://www.glamira.se/glamira-bracelet-peratra.html?alloy=yellow-585&diamond=ruby",
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

### current not product shaped

```json
{
  "_id": "5ebce444fe6972375adaefe8",
  "collection": "product_detail_recommendation_visible",
  "store_id": "6",
  "viewing_product_id": "96598",
  "current_url": "https://www.glamira.de/checkout/cart/configure/id/2137610/",
  "referrer_url": "https://www.glamira.de/diamant-ohrringe/smaragd/",
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
  "_id": "5e9e9c3460f01837771e4a2a",
  "collection": "product_detail_recommendation_visible",
  "store_id": "7",
  "viewing_product_id": "89490",
  "current_url": "https://test.glamira.de/glgb/glamira-ring-jena.html",
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
  "_id": "5ea67a264f117c373c4329b4",
  "collection": "product_detail_recommendation_visible",
  "store_id": "7",
  "viewing_product_id": "103846",
  "current_url": "https://dev3.glamira.de/glgb/glamira-ring-darnetta.html?discountid=%5BREDACTED%5D&stone2=diamond-Brillant&alloy=yellow-750&diamond=rhodolite-cabochon",
  "referrer_url": "https://dev3.glamira.de/glgb/surprise-deals/",
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

### current unusable or external

```json
{
  "_id": "5ed4e31f800034376000025a",
  "collection": "product_detail_recommendation_visible",
  "store_id": "33",
  "viewing_product_id": "91022",
  "current_url": "[REDACTED-NON-WEB-URL]",
  "referrer_url": "",
  "research_url_observations": {
    "current_url": {
      "scheme": "file:"
    },
    "referrer_url": {}
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

**Sampled opportunity, not achieved recovery:** 9,009 (96.85%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 292 (3.14%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Approve the viewed page as a product/configuration candidate without treating visible recommendations as the same product?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
