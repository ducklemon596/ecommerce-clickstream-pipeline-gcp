# view_static_page

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

Broad static/search context with occasional product-shaped paths. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **10,433 events** in this stratum (3.478% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:missing | 10,433 (100.00%) |
| product_id:missing | 10,433 (100.00%) |
| recommendation_product_id:missing | 10,433 (100.00%) |
| store_id:string | 10,433 (100.00%) |
| viewing_product_id:missing | 10,433 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 114 (1.09%) | 336 (3.22%) |
| empty | 0 (0.00%) | 1,181 (11.32%) |
| external | 1 (0.01%) | 1,723 (16.51%) |
| invalid_or_nonweb | 0 (0.00%) | 114 (1.09%) |
| merchant_other_page | 10,296 (98.69%) | 5,956 (57.09%) |
| product_shaped | 22 (0.21%) | 1,118 (10.72%) |
| recommendation_route | 0 (0.00%) | 5 (0.05%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| q | 1970 |
| gclid | 1564 |
| p | 535 |
| code | 410 |
| keyword | 283 |
| matchtype | 283 |
| filter-diamond | 231 |
| filter-alloycolour | 92 |
| itemid | 66 |
| ___store | 27 |
| diamond | 19 |
| alloy | 17 |
| utm_medium | 8 |
| utm_source | 8 |
| utm_campaign | 7 |

Unknown/nonclassified current keys: `q` (1,970), `p` (535), `code` (410), `filter-diamond` (231), `filter-alloycolour` (92), `itemid` (66), `___store` (27), `dir` (3), `order` (3), `alloycolour` (2). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| store_id:string | 10433 |

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 1064 |
| 7 @ www.glamira.co.uk | 838 |
| 41 @ www.glamira.com | 626 |
| 12 @ www.glamira.fr | 620 |
| 29 @ www.glamira.com.au | 435 |
| 8 @ www.glamira.es | 435 |
| 51 @ www.glamira.ro | 407 |
| 14 @ www.glamira.it | 364 |

Observed 81 store IDs and 80 current hosts. 20 store IDs had more than one current host; 12 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 10,413 (99.81%) |
| current_unknown_query_keys | 2,699 (25.87%) |
| current_nonproduction_host | 31 (0.30%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 0 (0.00%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 10,411 (99.79%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.



## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### representative

```json
{
  "_id": "5ea9db17c671fc36b7069fb1",
  "collection": "view_static_page",
  "store_id": "10",
  "current_url": "https://www.glamira.ch/customer/account/logoutSuccess/",
  "referrer_url": "https://www.glamira.ch/customer/account/",
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
  "_id": "5e9e7ccb93ed00371e8c473a",
  "collection": "view_static_page",
  "store_id": "6",
  "current_url": "https://dev.glamira.de/glde/catalogsearch/result/?filter-diamond=%5BREDACTED%5D&q=%5BREDACTED%5D",
  "referrer_url": "https://dev.glamira.de/glde/diamantringe/diamant/",
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
  "_id": "5e8b44381b67933736d04c79",
  "collection": "view_static_page",
  "store_id": "19",
  "current_url": "https://www.glamira.se/catalogsearch/result/index/?filter-diamond=%5BREDACTED%5D&q=%5BREDACTED%5D",
  "referrer_url": "https://www.glamira.se/catalogsearch/result/?q=%5BREDACTED%5D",
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
  "_id": "5ed0079c4f117c373c7be695",
  "collection": "view_static_page",
  "store_id": "17",
  "current_url": "https://a11391265293.cdn.optimizely.com/[REDACTED-EXTERNAL-PATH]",
  "referrer_url": "",
  "research_url_observations": {
    "current_url": {
      "scheme": "https:"
    },
    "referrer_url": {}
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

Allow independently confirmed product-path leads for review, or exclude this event entirely from future recovery?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
