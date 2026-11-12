# checkout_success

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

A success-page event with nested purchased-item identities and options. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **178 events** in this stratum (0.059% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:missing | 178 (100.00%) |
| product_id:missing | 178 (100.00%) |
| recommendation_product_id:missing | 178 (100.00%) |
| store_id:string | 178 (100.00%) |
| viewing_product_id:missing | 178 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 178 (100.00%) | 85 (47.75%) |
| empty | 0 (0.00%) | 2 (1.12%) |
| external | 0 (0.00%) | 89 (50.00%) |
| merchant_other_page | 0 (0.00%) | 2 (1.12%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |

Unknown/nonclassified current keys: none observed. Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| cart_products[].option[].option_id:number | 292 |
| cart_products[].option[].option_label:string | 292 |
| cart_products[].option[].value_id:number | 292 |
| cart_products[].option[].value_label:string | 292 |
| cart_products[].product_id:number | 230 |
| cart_products[].option:array | 186 |
| cart_products:array | 178 |
| store_id:string | 178 |
| cart_products[].option:string | 44 |

### Nested cart items

Item counts have a different denominator from event counts.

| Item measurement | Count |
| --- | --- |
| array_options | 186 |
| items_with_label_value | 186 |
| nonempty_label_value_pairs | 292 |
| total | 230 |

| Nested option representation | Items |
| --- | --- |
| array | 186 |
| empty_string | 44 |

| Nested option field / JSON type | Occurrences |
| --- | --- |
| option_id:number | 292 |
| option_label:string | 292 |
| value_id:number | 292 |
| value_label:string | 292 |

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 33 |
| 12 @ www.glamira.fr | 14 |
| 7 @ www.glamira.co.uk | 14 |
| 10 @ www.glamira.ch | 12 |
| 14 @ www.glamira.it | 9 |
| 11 @ www.glamira.nl | 8 |
| 13 @ www.glamira.dk | 7 |
| 41 @ www.glamira.com | 7 |

Observed 36 store IDs and 35 current hosts. 1 store IDs had more than one current host; 2 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| current_no_candidate_option_values | 178 (100.00%) |
| current_unknown_query_keys | 0 (0.00%) |
| current_nonproduction_host | 1 (0.56%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 0 (0.00%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 178 (100.00%) |
| multiple_cart_items | 42 (23.60%) |
| empty_cart_option_string | 44 (24.72%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.

### ID-reference sensitivity check

| Item/choice measurement | Count |
| --- | --- |
| ambiguous_in_sample | 50 |
| id_choices | 292 |
| items_all_usable_ids_matched | 14 |
| items_with_any_reference | 47 |
| no_reference | 194 |
| products_or_items | 230 |
| unambiguous_in_sample | 48 |
| without_option_array | 44 |

This compares internal IDs with corroborated selector URL pairs in the same sample. Witnesses and targets are not independent; no holdout or global reference was validated. `items_all_usable_ids_matched` does not mean all configuration dimensions are known. Ambiguous keys are rejected by this diagnostic, not resolved by majority voting. Numeric/string comparison is a research scenario pending approval.

## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### representative

```json
{
  "_id": "5ed63c9b4c9ffc36e825b374",
  "collection": "checkout_success",
  "store_id": "8",
  "cart_products": [
    {
      "product_id": 99576,
      "option": [
        {
          "option_label": "alloy",
          "option_id": 196812,
          "value_label": "Weißgold 585",
          "value_id": 1575355
        }
      ]
    }
  ],
  "current_url": "https://www.glamira.es/checkout/onepage/success/",
  "referrer_url": "https://www.glamira.es/customcheckout/onepage/review/",
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
  "_id": "5ea001764c9ffc36e8deb695",
  "collection": "checkout_success",
  "store_id": "6",
  "cart_products": [
    {
      "product_id": 109802,
      "option": ""
    },
    {
      "product_id": 102879,
      "option": [
        {
          "option_label": "diamond",
          "option_id": 258491,
          "value_label": "White Sapphire",
          "value_id": 2138775
        },
        {
          "option_label": "alloy",
          "option_id": 258492,
          "value_label": "Weißgold 585",
          "value_id": 2138783
        }
      ]
    }
  ],
  "current_url": "https://stage.glamira.de/glde/checkout/onepage/success/",
  "referrer_url": "https://stage.glamira.de/glde/customcheckout/onepage/review/",
  "cart_products_count": 2,
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
  "_id": "5e8f51da60f01837770f9eaf",
  "collection": "checkout_success",
  "store_id": "19",
  "cart_products": [
    {
      "product_id": 97980,
      "option": [
        {
          "option_label": "alloy",
          "option_id": 173714,
          "value_label": "Weiß-Rotgold 585",
          "value_id": 1339549
        }
      ]
    },
    {
      "product_id": 109972,
      "option": ""
    }
  ],
  "current_url": "https://www.glamira.se/checkout/onepage/success/",
  "referrer_url": "https://www.glamira.se/customcheckout/onepage/review/",
  "cart_products_count": 2,
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

MODERATE structural coverage: 30–499 sampled events; semantic conclusions remain provisional.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Include purchased-item identity evidence, retaining localized labels and unresolved ID-to-slug mappings rather than translating them?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
