# view_sorting_relevance

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

Sorting/listing context with an option object of filters. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **105 events** in this stratum (0.035% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:object | 105 (100.00%) |
| product_id:missing | 105 (100.00%) |
| recommendation_product_id:missing | 105 (100.00%) |
| store_id:string | 105 (100.00%) |
| viewing_product_id:missing | 105 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| empty | 0 (0.00%) | 7 (6.67%) |
| external | 0 (0.00%) | 29 (27.62%) |
| merchant_other_page | 105 (100.00%) | 69 (65.71%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| order | 29 |
| gclid | 25 |
| mode | 25 |
| keyword | 23 |
| matchtype | 23 |
| imgps | 2 |
| p | 2 |
| utm_medium | 1 |
| utm_source | 1 |

Unknown/nonclassified current keys: `order` (29), `mode` (25), `imgps` (2), `p` (2). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| option.alloy:string | 105 |
| option.diamond:string | 105 |
| option.shapediamond:string | 105 |
| option:object | 105 |
| store_id:string | 105 |

| Top-level option item field | Occurrences |
| --- | --- |
| alloy:string | 105 |
| diamond:string | 105 |
| shapediamond:string | 105 |

Observed option labels/keys: `alloy` (105), `diamond` (105), `shapediamond` (105).

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 8 |
| 99 @ www.glamira.com.my | 8 |
| 7 @ www.glamira.co.uk | 7 |
| 87 @ www.glamira.store | 7 |
| 14 @ www.glamira.it | 5 |
| 65 @ www.glamira.com.ar | 4 |
| 96 @ www.glamira.com.tw | 4 |
| 46 @ www.glamira.hu | 3 |

Observed 38 store IDs and 38 current hosts. 7 store IDs had more than one current host; 1 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 105 (100.00%) |
| current_unknown_query_keys | 30 (28.57%) |
| current_nonproduction_host | 11 (10.48%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 0 (0.00%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 105 (100.00%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.



## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### representative

```json
{
  "_id": "5e959d5333eacf36f47d3ca8",
  "collection": "view_sorting_relevance",
  "store_id": "96",
  "option": {
    "alloy": "",
    "diamond": "diamond-Swarovsky",
    "shapediamond": ""
  },
  "current_url": "https://www.glamira.com.tw/diamond-necklaces/swarovski-crystal/",
  "referrer_url": "https://www.glamira.com.tw/swarovski-crystal/",
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
  "_id": "5ea642c834103036e24a29ef",
  "collection": "view_sorting_relevance",
  "store_id": "6",
  "option": {
    "alloy": "",
    "diamond": "diamond-Brillant",
    "shapediamond": ""
  },
  "current_url": "https://dev5.glamira.de/glde/diamantringe/diamant/big_stone/",
  "referrer_url": "https://dev5.glamira.de/glde/diamantringe/diamant/",
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
  "_id": "5ea7316a4c9ffc36e8e63beb",
  "collection": "view_sorting_relevance",
  "store_id": "7",
  "option": {
    "alloy": "",
    "diamond": "",
    "shapediamond": ""
  },
  "current_url": "https://www.glamira.co.uk/engagement-rings/eternity/?imgps=%5BREDACTED%5D&order=%5BREDACTED%5D&mode=%5BREDACTED%5D",
  "referrer_url": "https://www.glamira.co.uk/engagement-rings/side_stone/?imgps=%5BREDACTED%5D&order=%5BREDACTED%5D&mode=%5BREDACTED%5D",
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

Proposed result class: **Browsing/filter context, no configuration tuple**.

Source priority: Inspect current URL and explicit fields; absent product identity cannot be replaced by a page filter or previous referrer.

- Recommend excluding the observed page/filter state from configuration tuples while retaining aggregate evidence. There is no established product owner for the filter values.
- An option object containing alloy/diamond/shape on a category page is filter context, not proof of one product configuration. A queryless URL does not establish a default product configuration.
- If an exceptional current URL has independently verified product-page evidence, it can be reconsidered as an unresolved URL lead; event names alone should not override the record.
- Referrer product references remain previous-page evidence. Their use would require reopening the earlier current_url-only scope and verifying association.

Alternative and trade-off: Recovering product URLs from navigation referrers may add leads, but can attach a previous product to unrelated page state. Recommend no configuration tuple from the page context itself.

**Sampled opportunity, not achieved recovery:** 0 (0.00%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 0 (0.00%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

MODERATE structural coverage: 30–499 sampled events; semantic conclusions remain provisional.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Approve treating option fields as listing filters and leaving any recommended product configuration unknown?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
