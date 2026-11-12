# view_shopping_cart

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

A cart snapshot containing zero or more separately identified products. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **2,425 events** in this stratum (0.808% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:missing | 2,425 (100.00%) |
| product_id:missing | 2,425 (100.00%) |
| recommendation_product_id:missing | 2,425 (100.00%) |
| store_id:string | 2,425 (100.00%) |
| viewing_product_id:missing | 2,425 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 2,424 (99.96%) | 905 (37.32%) |
| empty | 0 (0.00%) | 131 (5.40%) |
| external | 0 (0.00%) | 292 (12.04%) |
| invalid_or_nonweb | 1 (0.04%) | 4 (0.16%) |
| merchant_other_page | 0 (0.00%) | 524 (21.61%) |
| product_shaped | 0 (0.00%) | 569 (23.46%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| fbclid | 1 |

Unknown/nonclassified current keys: none observed. Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| cart_products[].option[].option_id:number | 6531 |
| cart_products[].option[].option_label:string | 6531 |
| cart_products[].option[].value_id:number | 6531 |
| cart_products[].option[].value_label:string | 6531 |
| cart_products[].product_id:number | 4616 |
| cart_products[].option:array | 3860 |
| cart_products:array | 2425 |
| store_id:string | 2425 |
| cart_products[].option:string | 756 |

### Nested cart items

Item counts have a different denominator from event counts.

| Item measurement | Count |
| --- | --- |
| array_options | 3860 |
| items_with_label_value | 3860 |
| nonempty_label_value_pairs | 6531 |
| total | 4616 |

| Nested option representation | Items |
| --- | --- |
| array | 3860 |
| empty_string | 756 |

| Nested option field / JSON type | Occurrences |
| --- | --- |
| option_id:number | 6531 |
| option_label:string | 6531 |
| value_id:number | 6531 |
| value_label:string | 6531 |

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 367 |
| 7 @ www.glamira.co.uk | 208 |
| 41 @ www.glamira.com | 188 |
| 12 @ www.glamira.fr | 174 |
| 14 @ www.glamira.it | 124 |
| 19 @ www.glamira.se | 107 |
| 11 @ www.glamira.nl | 88 |
| 38 @ www.glamira.ca | 79 |

Observed 65 store IDs and 61 current hosts. 4 store IDs had more than one current host; 6 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 2,425 (100.00%) |
| current_unknown_query_keys | 0 (0.00%) |
| current_nonproduction_host | 4 (0.16%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 0 (0.00%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 2,425 (100.00%) |
| empty_cart | 694 (28.62%) |
| multiple_cart_items | 1,064 (43.88%) |
| empty_cart_option_string | 754 (31.09%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.

### ID-reference sensitivity check

| Item/choice measurement | Count |
| --- | --- |
| ambiguous_in_sample | 755 |
| id_choices | 6531 |
| items_all_usable_ids_matched | 201 |
| items_with_any_reference | 836 |
| no_reference | 4904 |
| products_or_items | 4616 |
| unambiguous_in_sample | 872 |
| without_option_array | 756 |

This compares internal IDs with corroborated selector URL pairs in the same sample. Witnesses and targets are not independent; no holdout or global reference was validated. `items_all_usable_ids_matched` does not mean all configuration dimensions are known. Ambiguous keys are rejected by this diagnostic, not resolved by majority voting. Numeric/string comparison is a research scenario pending approval.

## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### representative

```json
{
  "_id": "5ec7464c66a4b33724ff2538",
  "collection": "view_shopping_cart",
  "store_id": "38",
  "cart_products": [
    {
      "product_id": 98772,
      "option": [
        {
          "option_label": "alloy",
          "option_id": 181035,
          "value_label": "Weiß-Gelbgold 585",
          "value_id": 1429638
        }
      ]
    }
  ],
  "current_url": "https://www.glamira.ca/checkout/cart/",
  "referrer_url": "https://www.glamira.ca/checkout/cart/configure/id/2190728/?alloy=white-silber",
  "cart_products_count": 1,
  "cart_products_excerpt_truncated": false,
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
  "_id": "5ec532d133eacf36f4b80cea",
  "collection": "view_shopping_cart",
  "store_id": "46",
  "cart_products": [],
  "current_url": "https://dev3.glamira.de/glhu/checkout/cart/",
  "referrer_url": "https://dev3.glamira.de/glhu/glamira-ring-verde.html?alloy=white-375&diamond=diamond-Brillant&stone2=diamond-Brillant",
  "cart_products_count": 0,
  "cart_products_excerpt_truncated": false,
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

### empty cart option string

```json
{
  "_id": "5ecbbbab6b9438374e2e73f5",
  "collection": "view_shopping_cart",
  "store_id": "11",
  "cart_products": [
    {
      "product_id": 110048,
      "option": ""
    },
    {
      "product_id": 90311,
      "option": [
        {
          "option_label": "diamond",
          "option_id": 246213,
          "value_label": "White Sapphire",
          "value_id": 2043604
        },
        {
          "option_label": "alloy",
          "option_id": 246214,
          "value_label": "Weißgold 585",
          "value_id": 2043612
        }
      ]
    }
  ],
  "current_url": "https://www.glamira.nl/checkout/cart/",
  "referrer_url": "https://www.glamira.nl/catalogsearch/result/?q=%5BREDACTED%5D",
  "cart_products_count": 3,
  "cart_products_excerpt_truncated": true,
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

### empty cart

```json
{
  "_id": "5eb6802d4f117c373c57df10",
  "collection": "view_shopping_cart",
  "store_id": "7",
  "cart_products": [],
  "current_url": "https://www.glamira.co.uk/checkout/cart/",
  "referrer_url": "https://www.glamira.co.uk/glamira-diamonds-ring-hercules-skug100545.html?stone2=diamond-Brillant&alloy=white-585&diamond=sapphire",
  "referrer_url_omitted_tracking_keys": [
    "gclid"
  ],
  "cart_products_count": 0,
  "cart_products_excerpt_truncated": false,
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
  "_id": "5eb69768385d1f36b8707ff1",
  "collection": "view_shopping_cart",
  "store_id": "6",
  "cart_products": [
    {
      "product_id": 86908,
      "option": [
        {
          "option_label": "diamond",
          "option_id": 67386,
          "value_label": "White Sapphire",
          "value_id": 784101
        },
        {
          "option_label": "alloy",
          "option_id": 67383,
          "value_label": "Weißgold 585",
          "value_id": 420232
        }
      ]
    }
  ],
  "current_url": "[REDACTED-NON-WEB-URL]",
  "referrer_url": "",
  "cart_products_count": 1,
  "cart_products_excerpt_truncated": false,
  "research_url_observations": {
    "current_url": {
      "scheme": "file:"
    },
    "referrer_url": {}
  }
}
```



## 5. Proposed Strategy — approval pending

Proposed result class: **Per-item product identities; options need a scoped reference**.

Source priority: Each cart_products[].product_id separately → event store/current hostname → that item's nested option array and IDs. Event-level URL/referrer parameters are not per-item options.

- Recommend including per-item identity evidence. Numeric IDs may be compared with digit-string IDs only through a documented lossless canonicalization proposal; preserve original types in provenance.
- Nested value_label values are display labels, sometimes localized, while URL option values are slug tokens. Never translate or concatenate these display labels into crawl URLs.
- Array options with IDs can be resolved only by a verified product/store/option/value-ID reference. An empty string, empty array or absent value means unspecified, not a known website default.
- A multi-item cart has one current/referrer URL. Do not apply that URL's configuration to every item or infer that the referrer belongs to an arbitrary cart product.

Alternative and trade-off: Ignoring carts loses transaction-related product evidence; guessing slugs from labels creates false configurations. Recommend identity evidence now and option recovery only where a scoped reference is verified.

**Sampled opportunity, not achieved recovery:** 0 (0.00%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 0 (0.00%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Include per-item identities, and recover option slugs only through verified product/store/option/value-ID references?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
