# view_landing_page

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

Landing-page context with no established product identity. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **10,214 events** in this stratum (3.405% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:missing | 10,214 (100.00%) |
| product_id:missing | 10,214 (100.00%) |
| recommendation_product_id:missing | 10,214 (100.00%) |
| store_id:string | 10,214 (100.00%) |
| viewing_product_id:missing | 10,214 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 0 (0.00%) | 64 (0.63%) |
| empty | 0 (0.00%) | 836 (8.18%) |
| external | 0 (0.00%) | 4,210 (41.22%) |
| invalid_or_nonweb | 0 (0.00%) | 29 (0.28%) |
| merchant_other_page | 10,214 (100.00%) | 3,859 (37.78%) |
| product_shaped | 0 (0.00%) | 1,209 (11.84%) |
| recommendation_route | 0 (0.00%) | 7 (0.07%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| gclid | 4564 |
| keyword | 629 |
| matchtype | 629 |
| ___store | 8 |
| no_cache | 5 |
| synthetic | 4 |
| fbclid | 3 |
| utm_campaign | 3 |
| utm_medium | 3 |
| utm_source | 3 |
| zarsrc | 1 |

Unknown/nonclassified current keys: `___store` (8), `zarsrc` (1). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| store_id:string | 10214 |

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 1319 |
| 7 @ www.glamira.co.uk | 747 |
| 41 @ www.glamira.com | 655 |
| 12 @ www.glamira.fr | 481 |
| 51 @ www.glamira.ro | 427 |
| 62 @ www.glamira.com.mx | 383 |
| 8 @ www.glamira.es | 382 |
| 19 @ www.glamira.se | 323 |

Observed 75 store IDs and 67 current hosts. 14 store IDs had more than one current host; 7 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 10,210 (99.96%) |
| current_unknown_query_keys | 9 (0.09%) |
| current_nonproduction_host | 25 (0.24%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 0 (0.00%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 10,214 (100.00%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.



## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### representative

```json
{
  "_id": "5ec4d16c98c9ed378446c9cf",
  "collection": "view_landing_page",
  "store_id": "38",
  "current_url": "https://www.glamira.ca/engagement/",
  "referrer_url": "https://www.glamira.ca/glamira-ring-calybe.html?alloy=red-375&diamond=diamond-Brillant",
  "referrer_url_omitted_tracking_keys": [
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
  "_id": "5e982ae14f117c373c34ae11",
  "collection": "view_landing_page",
  "store_id": "7",
  "current_url": "https://dev5.glamira.de/glgb/engagement/",
  "referrer_url": "https://dev5.glamira.de/glgb/jewelry/",
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
  "_id": "5e8e8c1d4c9ffc36e8ce048d",
  "collection": "view_landing_page",
  "store_id": "93",
  "current_url": "https://dev5.glamira.de/glpr/easter-gifts/?___store=%5BREDACTED%5D",
  "referrer_url": "https://dev5.glamira.de/index.php/admin/admin/cms_page/",
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

STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Approve excluding landing-page state while allowing only independently proven exceptional product records to be reviewed?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
