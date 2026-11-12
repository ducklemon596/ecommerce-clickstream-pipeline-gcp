# view_listing_page

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

Category/listing context with an option object of filters. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **81,642 events** in this stratum (27.214% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:object | 81,642 (100.00%) |
| product_id:missing | 81,642 (100.00%) |
| recommendation_product_id:missing | 81,642 (100.00%) |
| store_id:string | 81,642 (100.00%) |
| viewing_product_id:missing | 81,642 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 0 (0.00%) | 134 (0.16%) |
| empty | 0 (0.00%) | 2,603 (3.19%) |
| external | 2 (0.00%) | 18,372 (22.50%) |
| invalid_or_nonweb | 0 (0.00%) | 111 (0.14%) |
| merchant_other_page | 81,640 (100.00%) | 57,523 (70.46%) |
| product_shaped | 0 (0.00%) | 2,871 (3.52%) |
| recommendation_route | 0 (0.00%) | 28 (0.03%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| gclid | 15581 |
| p | 6694 |
| order | 4525 |
| dir | 4440 |
| keyword | 2242 |
| matchtype | 2239 |
| imgps | 2193 |
| utm_expid | 613 |
| utm_referrer | 613 |
| mode | 124 |
| synthetic | 119 |
| stone2 | 18 |
| utm_medium | 16 |
| utm_source | 16 |
| fbclid | 13 |

Unknown/nonclassified current keys: `p` (6,694), `order` (4,525), `dir` (4,440), `imgps` (2,193), `mode` (124), `wood` (4), `zarsrc` (4), `leathercolour` (3), `from` (2), `limit` (2), `` (1), `a` (1). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| option.alloy:string | 81642 |
| option.diamond:string | 81642 |
| option.shapediamond:string | 81642 |
| option:object | 81642 |
| store_id:string | 81642 |

| Top-level option item field | Occurrences |
| --- | --- |
| alloy:string | 81642 |
| diamond:string | 81642 |
| shapediamond:string | 81642 |

Observed option labels/keys: `alloy` (81,642), `diamond` (81,642), `shapediamond` (81,642).

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 8637 |
| 7 @ www.glamira.co.uk | 6901 |
| 12 @ www.glamira.fr | 4625 |
| 41 @ www.glamira.com | 4502 |
| 51 @ www.glamira.ro | 3589 |
| 8 @ www.glamira.es | 3232 |
| 14 @ www.glamira.it | 3023 |
| 29 @ www.glamira.com.au | 2596 |

Observed 84 store IDs and 79 current hosts. 24 store IDs had more than one current host; 13 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 81,504 (99.83%) |
| current_unknown_query_keys | 12,400 (15.19%) |
| current_nonproduction_host | 38 (0.05%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 0 (0.00%) |
| current_repeated_conflicting_key | 1 (0.00%) |
| current_malformed_parameter_key | 1 (0.00%) |
| current_html_escaped | 16 (0.02%) |
| current_not_product_shaped | 81,642 (100.00%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.



## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### representative

```json
{
  "_id": "5ed7ec22fe6972375afffe43",
  "collection": "view_listing_page",
  "store_id": "51",
  "option": {
    "alloy": "yellow-585",
    "diamond": "",
    "shapediamond": ""
  },
  "current_url": "https://www.glamira.ro/inele-diamant/585-aur-galben/?p=%5BREDACTED%5D",
  "referrer_url": "https://www.glamira.ro/inele-diamant/585-aur-galben/?p=%5BREDACTED%5D",
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

### current repeated conflicting key

```json
{
  "_id": "5e9fd8ce5c503836d6855347",
  "collection": "view_listing_page",
  "store_id": "10",
  "option": {
    "alloy": "white-585",
    "diamond": "",
    "shapediamond": ""
  },
  "current_url": "https://www.glamira.ch/trauringe/585-weiss-gold/",
  "referrer_url": "https://www.google.de/[REDACTED-EXTERNAL-PATH]",
  "current_url_omitted_tracking_keys": [
    "gclid"
  ],
  "research_url_observations": {
    "current_url": {
      "scheme": "https:",
      "repeated_conflicting_key": true
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
  "_id": "5ecb3c4d796d133700bda95c",
  "collection": "view_listing_page",
  "store_id": "6",
  "option": {
    "alloy": "",
    "diamond": "",
    "shapediamond": ""
  },
  "current_url": "https://stage.glamira.de/glde/initialen-namensschmuck/",
  "referrer_url": "https://stage.glamira.de/glde/",
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
  "_id": "5ed78877bb30d63718be5c5b",
  "collection": "view_listing_page",
  "store_id": "50",
  "option": {
    "alloy": "",
    "diamond": "",
    "shapediamond": ""
  },
  "current_url": "https://www.translatoruser-int.com/[REDACTED-EXTERNAL-PATH]?from=%5BREDACTED%5D&to=%5BREDACTED%5D&csId=%5BREDACTED%5D&usId=%5BREDACTED%5D&dl=%5BREDACTED%5D&ref=%5BREDACTED%5D&ac=%5BREDACTED%5D&dt=%5BREDACTED%5D&h=%5BREDACTED%5D&a=%5BREDACTED%5D",
  "referrer_url": "https://www.translatoruser-int.com/[REDACTED-EXTERNAL-PATH]?from=%5BREDACTED%5D&to=%5BREDACTED%5D&csId=%5BREDACTED%5D&usId=%5BREDACTED%5D&ref=%5BREDACTED%5D&refd=%5BREDACTED%5D&dl=%5BREDACTED%5D&ac=%5BREDACTED%5D&dt=%5BREDACTED%5D&h=%5BREDACTED%5D&a=%5BREDACTED%5D",
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

Approve treating listing option objects as filters only, with no product configuration tuple absent independent product evidence?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
