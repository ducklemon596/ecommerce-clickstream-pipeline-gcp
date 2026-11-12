# product_detail_recommendation_clicked

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

A click with both viewing_product_id and recommendation_product_id. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **1,313 events** in this stratum (0.438% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:missing | 1,313 (100.00%) |
| product_id:missing | 1,313 (100.00%) |
| recommendation_product_id:string | 1,313 (100.00%) |
| store_id:string | 1,313 (100.00%) |
| viewing_product_id:string | 1,313 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 13 (0.99%) | 15 (1.14%) |
| empty | 0 (0.00%) | 152 (11.58%) |
| external | 0 (0.00%) | 202 (15.38%) |
| merchant_other_page | 0 (0.00%) | 502 (38.23%) |
| product_shaped | 1,300 (99.01%) | 426 (32.44%) |
| recommendation_route | 0 (0.00%) | 16 (1.22%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| alloy | 1283 |
| diamond | 989 |
| itm_medium | 733 |
| itm_source | 733 |
| stone2 | 505 |
| gclid | 251 |
| stone | 124 |
| pearl | 21 |
| keyword | 20 |
| matchtype | 20 |
| stone3 | 20 |
| utm_medium | 13 |
| utm_source | 13 |
| utm_campaign | 8 |
| fbclid | 6 |

Unknown/nonclassified current keys: `___store` (1). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| recommendation_product_id:string | 1313 |
| store_id:string | 1313 |
| viewing_product_id:string | 1313 |

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 186 |
| 12 @ www.glamira.fr | 87 |
| 7 @ www.glamira.co.uk | 79 |
| 19 @ www.glamira.se | 71 |
| 14 @ www.glamira.it | 59 |
| 41 @ www.glamira.com | 58 |
| 8 @ www.glamira.es | 54 |
| 51 @ www.glamira.ro | 48 |

Observed 57 store IDs and 52 current hosts. 0 store IDs had more than one current host; 4 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 15 (1.14%) |
| current_unknown_query_keys | 1 (0.08%) |
| current_nonproduction_host | 0 (0.00%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 1 (0.08%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 13 (0.99%) |
| viewed_recommended_differ | 1,313 (100.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.



## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### direct identity with url subset

```json
{
  "_id": "5ecc4df771a3b936be8419c9",
  "collection": "product_detail_recommendation_clicked",
  "store_id": "32",
  "viewing_product_id": "102714",
  "recommendation_product_id": "92033",
  "current_url": "https://www.glamira.be/glamira-earring-lamarria.html?alloy=yellow-375&diamond=diamond-Brillant&pearl=white_pearl",
  "referrer_url": "https://www.glamira.be/glamira-earring-kiamara-6-8-mm.html?pearl=white_pearl&alloy=yellow-375",
  "current_url_omitted_tracking_keys": [
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

### current not product shaped

```json
{
  "_id": "5ec44c191b67933736132b5d",
  "collection": "product_detail_recommendation_clicked",
  "store_id": "17",
  "viewing_product_id": "103326",
  "recommendation_product_id": "103307",
  "current_url": "https://www.glamira.com.tr/checkout/cart/configure/id/2159519/",
  "referrer_url": "https://www.glamira.com.tr/glamira-yuzuk-giselle-skug100375.html?stone2=diamond-Brillant&diamond=diamond-Brillant&alloy=red-585",
  "referrer_url_omitted_tracking_keys": [
    "utm_campaign",
    "utm_medium",
    "utm_source"
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

### current unknown query keys

```json
{
  "_id": "5ecb4e24b9a5fa37544ea02b",
  "collection": "product_detail_recommendation_clicked",
  "store_id": "79",
  "viewing_product_id": "90470",
  "recommendation_product_id": "90473",
  "current_url": "https://www.glamira.co.za/womens-ring-celtic-solstice.html?___store=%5BREDACTED%5D&alloy=white-silber",
  "referrer_url": "",
  "research_url_observations": {
    "current_url": {
      "scheme": "https:"
    },
    "referrer_url": {}
  }
}
```

### current no candidate option values

```json
{
  "_id": "5ed509229d843b3706723726",
  "collection": "product_detail_recommendation_clicked",
  "store_id": "34",
  "viewing_product_id": "101815",
  "recommendation_product_id": "101827",
  "current_url": "https://www.glamira.pt/anel-femininos-silver-&-diamonds-twice.html",
  "referrer_url": "https://www.glamira.pt/silver-&-diamonds-twice.html",
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

**Sampled opportunity, not achieved recovery:** 1,298 (98.86%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 15 (1.14%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Approve separate viewed-page candidates and identity-only recommended targets, with no configuration transfer between them?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
