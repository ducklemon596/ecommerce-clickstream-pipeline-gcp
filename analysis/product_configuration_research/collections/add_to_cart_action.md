# add_to_cart_action

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

An add-to-cart action carrying a product identity and page URL. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **1,355 events** in this stratum (0.452% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:array | 1,355 (100.00%) |
| product_id:string | 1,355 (100.00%) |
| recommendation_product_id:missing | 1,355 (100.00%) |
| store_id:string | 1,355 (100.00%) |
| viewing_product_id:missing | 1,355 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 147 (10.85%) | 149 (11.00%) |
| empty | 0 (0.00%) | 112 (8.27%) |
| external | 0 (0.00%) | 67 (4.94%) |
| invalid_or_nonweb | 0 (0.00%) | 1 (0.07%) |
| merchant_other_page | 0 (0.00%) | 706 (52.10%) |
| product_shaped | 1,208 (89.15%) | 313 (23.10%) |
| recommendation_route | 0 (0.00%) | 7 (0.52%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| alloy | 1268 |
| diamond | 813 |
| itm_medium | 602 |
| itm_source | 602 |
| stone2 | 371 |
| stone | 198 |
| gclid | 77 |
| stone3 | 34 |
| pearl | 31 |
| synthetic | 7 |
| utm_medium | 6 |
| utm_source | 6 |
| accent | 5 |
| leather | 5 |
| smartid | 5 |

Unknown/nonclassified current keys: `smartid` (5), `___store` (3). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| option[].option_id:string | 2710 |
| option[].option_label:string | 2710 |
| option[].value_id:string | 2710 |
| option[].value_label:string | 2710 |
| option:array | 1355 |
| product_id:string | 1355 |
| store_id:string | 1355 |

| Top-level option item field | Occurrences |
| --- | --- |
| option_id:string | 2710 |
| option_label:string | 2710 |
| value_id:string | 2710 |
| value_label:string | 2710 |

Observed option labels/keys: `alloy` (1,355), `diamond` (1,355).

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 262 |
| 7 @ www.glamira.co.uk | 119 |
| 41 @ www.glamira.com | 117 |
| 12 @ www.glamira.fr | 94 |
| 14 @ www.glamira.it | 50 |
| 11 @ www.glamira.nl | 47 |
| 19 @ www.glamira.se | 47 |
| 10 @ www.glamira.ch | 42 |

Observed 60 store IDs and 61 current hosts. 8 store IDs had more than one current host; 6 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| empty_value_label | 1,355 (100.00%) |
| id_only_option | 1,331 (98.23%) |
| current_no_candidate_option_values | 65 (4.80%) |
| current_unknown_query_keys | 8 (0.59%) |
| current_nonproduction_host | 8 (0.59%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 4 (0.30%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| product_route_id_match | 2 (0.15%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 147 (10.85%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.

### ID-reference sensitivity check

| Item/choice measurement | Count |
| --- | --- |
| ambiguous_in_sample | 369 |
| id_choices | 2235 |
| items_all_usable_ids_matched | 74 |
| items_with_any_reference | 358 |
| no_reference | 1498 |
| products_or_items | 1355 |
| unambiguous_in_sample | 368 |

This compares internal IDs with corroborated selector URL pairs in the same sample. Witnesses and targets are not independent; no holdout or global reference was validated. `items_all_usable_ids_matched` does not mean all configuration dimensions are known. Ambiguous keys are rejected by this diagnostic, not resolved by majority voting. Numeric/string comparison is a research scenario pending approval.

## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### direct identity with url subset

```json
{
  "_id": "5e8b866cfe6972375aa3b330",
  "collection": "add_to_cart_action",
  "store_id": "8",
  "product_id": "89584",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "105635",
      "value_label": "",
      "value_id": "764845"
    },
    {
      "option_label": "diamond",
      "option_id": "105637",
      "value_label": "",
      "value_id": "764885"
    }
  ],
  "current_url": "https://www.glamira.es/glamira-anillo-absolute-strength.html?stone2=diamond-Brillant&diamond=topaz-Blue&alloy=yellow-375",
  "referrer_url": "https://www.glamira.es/hombre-anillos-de-diamantes/",
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
  "_id": "5ebf245e5d4dd036faf4ddc4",
  "collection": "add_to_cart_action",
  "store_id": "6",
  "product_id": "109341",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "321608",
      "value_label": "",
      "value_id": "2726146"
    },
    {
      "option_label": "diamond",
      "option_id": "",
      "value_label": "",
      "value_id": ""
    }
  ],
  "current_url": "https://www.glamira.de/checkout/cart/configure/id/2155557/?alloy=red-585",
  "referrer_url": "https://www.glamira.de/checkout/cart/",
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
  "_id": "5ec53d584c9ffc36e80f4ef4",
  "collection": "add_to_cart_action",
  "store_id": "47",
  "product_id": "95560",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "250141",
      "value_label": "",
      "value_id": "2078287"
    },
    {
      "option_label": "diamond",
      "option_id": "250140",
      "value_label": "",
      "value_id": "2078266"
    }
  ],
  "current_url": "https://dev3.glamira.de/glhk/checkout/cart/configure/id/1776183/",
  "referrer_url": "https://dev3.glamira.de/glhk/checkout/cart/",
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
  "_id": "5eb86a6a8772593712342d61",
  "collection": "add_to_cart_action",
  "store_id": "7",
  "product_id": "102023",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "330018",
      "value_label": "",
      "value_id": "3261752"
    },
    {
      "option_label": "diamond",
      "option_id": "330017",
      "value_label": "",
      "value_id": "3261706"
    }
  ],
  "current_url": "https://www.glamira.co.uk/glamira-ring-jeslanie.html?___store=%5BREDACTED%5D&alloy=yellow-375",
  "referrer_url": "https://www.glamira.pt/glamira-ring-jeslanie.html?stone2=diamond-Swarovsky&diamond=opal&alloy=yellow-375",
  "referrer_url_omitted_tracking_keys": [
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

### current no candidate option values

```json
{
  "_id": "5eacb0db9fade236dce2605e",
  "collection": "add_to_cart_action",
  "store_id": "7",
  "product_id": "108734",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "316029",
      "value_label": "",
      "value_id": "2691941"
    },
    {
      "option_label": "diamond",
      "option_id": "316027",
      "value_label": "",
      "value_id": "2691878"
    }
  ],
  "current_url": "https://www.glamira.co.uk/checkout/cart/configure/id/2087323/",
  "referrer_url": "https://www.glamira.co.uk/checkout/cart/",
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

Indexed source point reads reverified: `5ed8caa45c503836d6cfb157`. These are separate from the random-pool denominators.

## 5. Proposed Strategy — approval pending

Proposed result class: **Observed product URL subset**.

Source priority: Explicit product_id → explicit store_id plus current hostname → nonempty, approved current-URL option pairs. The option array validates labels/IDs where possible; it does not fill blanks.

- Recommend retaining only the configuration subset explicitly present in a valid current URL. A missing parameter remains unspecified; an empty query is base-product evidence, not a verified website default.
- Require a trusted storefront host and an unambiguous product association. A product-shaped slug is supporting evidence, not existence validation; the user-verified numeric product route avoids inventing SEO slugs.
- Keep unknown keys and disagreements for review. Conflicting repeated URL values, malformed encoding/keys, or incompatible identity evidence must not produce a resolved configuration.
- Option/value IDs alone cannot supply URL slug values without a product/store-scoped, verified reference. Do not translate labels or use a global ID-to-token dictionary.

Alternative and trade-off: Using option/value IDs to fill every missing URL field could increase apparent coverage, but needs a verified reference and may invent implicit defaults. Recommend the explicit URL subset for this phase.

**Sampled opportunity, not achieved recovery:** 1,290 (95.20%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 65 (4.80%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Approve URL-subset evidence when option value labels are blank, and retain non-product current URLs or contradictions for review?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
