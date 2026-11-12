# view_product_detail

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

Product-page observation with product_id and option metadata. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **79,822 events** in this stratum (26.607% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:array | 79,822 (100.00%) |
| product_id:string | 79,822 (100.00%) |
| recommendation_product_id:missing | 79,822 (100.00%) |
| store_id:string | 79,822 (100.00%) |
| viewing_product_id:missing | 79,822 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 561 (0.70%) | 524 (0.66%) |
| empty | 0 (0.00%) | 9,136 (11.45%) |
| external | 0 (0.00%) | 37,796 (47.35%) |
| invalid_or_nonweb | 2 (0.00%) | 87 (0.11%) |
| merchant_other_page | 0 (0.00%) | 24,075 (30.16%) |
| product_shaped | 79,259 (99.29%) | 8,029 (10.06%) |
| recommendation_route | 0 (0.00%) | 175 (0.22%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| alloy | 58855 |
| diamond | 34451 |
| itm_source | 32311 |
| itm_medium | 32310 |
| fbclid | 28509 |
| stone2 | 17213 |
| gclid | 12982 |
| stone | 10672 |
| keyword | 1891 |
| matchtype | 1891 |
| utm_medium | 714 |
| pearl | 710 |
| stone3 | 696 |
| utm_source | 692 |
| utm_campaign | 660 |

Unknown/nonclassified current keys: `___store` (61), `client` (49), `discountid` (32), `ctype` (28), `smartid` (16), `edit_form` (12), `` (5), `from` (3), `instock` (3), `?no_cache` (2), `?stone` (1), `amp;alloy` (1). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| option[].option_id:string | 159644 |
| option[].option_label:string | 159644 |
| option[].value_id:string | 159644 |
| option[].value_label:string | 159644 |
| option:array | 79822 |
| product_id:string | 79822 |
| store_id:string | 79822 |

| Top-level option item field | Occurrences |
| --- | --- |
| option_id:string | 159644 |
| option_label:string | 159644 |
| value_id:string | 159644 |
| value_label:string | 159644 |

Observed option labels/keys: `alloy` (79,822), `diamond` (79,822).

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 10053 |
| 7 @ www.glamira.co.uk | 6381 |
| 12 @ www.glamira.fr | 5152 |
| 14 @ www.glamira.it | 4213 |
| 41 @ www.glamira.com | 4021 |
| 8 @ www.glamira.es | 3821 |
| 19 @ www.glamira.se | 3571 |
| 29 @ www.glamira.com.au | 2766 |

Observed 80 store IDs and 77 current hosts. 14 store IDs had more than one current host; 12 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| conflicting_option_labels | 0 (0.00%) |
| empty_value_label | 79,822 (100.00%) |
| id_only_option | 79,153 (99.16%) |
| current_no_candidate_option_values | 19,759 (24.75%) |
| current_unknown_query_keys | 188 (0.24%) |
| current_nonproduction_host | 94 (0.12%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 107 (0.13%) |
| current_repeated_conflicting_key | 1 (0.00%) |
| current_malformed_parameter_key | 8 (0.01%) |
| product_route_id_match | 12 (0.02%) |
| current_html_escaped | 3 (0.00%) |
| current_not_product_shaped | 563 (0.71%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.

### ID-reference sensitivity check

| Item/choice measurement | Count |
| --- | --- |
| ambiguous_in_sample | 22987 |
| id_choices | 132674 |
| items_all_usable_ids_matched | 3469 |
| items_with_any_reference | 17515 |
| no_reference | 91349 |
| products_or_items | 79822 |
| unambiguous_in_sample | 18338 |

This compares internal IDs with corroborated selector URL pairs in the same sample. Witnesses and targets are not independent; no holdout or global reference was validated. `items_all_usable_ids_matched` does not mean all configuration dimensions are known. Ambiguous keys are rejected by this diagnostic, not resolved by majority voting. Numeric/string comparison is a research scenario pending approval.

## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### direct identity with url subset

```json
{
  "_id": "5eb24b0534103036e2593bb6",
  "collection": "view_product_detail",
  "store_id": "19",
  "product_id": "96542",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "159483",
      "value_label": "",
      "value_id": "1219015"
    },
    {
      "option_label": "diamond",
      "option_id": "",
      "value_label": "",
      "value_id": ""
    }
  ],
  "current_url": "https://www.glamira.se/damring-bright-love-3-mm.html?alloy=white-silber",
  "referrer_url": "https://www.glamira.se/damring-bright-love-2-mm.html?alloy=white-silber",
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

### representative

```json
{
  "_id": "5e8a2d3f5d4dd036fab90cd6",
  "collection": "view_product_detail",
  "store_id": "14",
  "product_id": "110549",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "332509",
      "value_label": "",
      "value_id": "3284689"
    },
    {
      "option_label": "diamond",
      "option_id": "332508",
      "value_label": "",
      "value_id": "3284664"
    }
  ],
  "current_url": "https://www.glamira.it/glamira-pendant-melpomene.html",
  "referrer_url": "https://www.facebook.com/[REDACTED-EXTERNAL-PATH]",
  "current_url_omitted_tracking_keys": [
    "fbclid"
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

### current repeated conflicting key

```json
{
  "_id": "5e84447a78aa7636caf0f64d",
  "collection": "view_product_detail",
  "store_id": "55",
  "product_id": "105898",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "285419",
      "value_label": "",
      "value_id": "2366389"
    },
    {
      "option_label": "diamond",
      "option_id": "",
      "value_label": "",
      "value_id": ""
    }
  ],
  "current_url": "https://www.glamira.si/universe-adore-5-mm.html?alloy=red_white-375%3Fstone&alloy=red_white-375",
  "referrer_url": "https://www.glamira.si/universe-adore-6-mm.html?alloy=red_white-375%3Fstone%3Ddiamond-zirconia",
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

### current not product shaped

```json
{
  "_id": "5e8dbc2766a4b33724ba5f4f",
  "collection": "view_product_detail",
  "store_id": "14",
  "product_id": "104233",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "267902",
      "value_label": "",
      "value_id": "2261517"
    },
    {
      "option_label": "diamond",
      "option_id": "267901",
      "value_label": "",
      "value_id": "2261488"
    }
  ],
  "current_url": "https://www.glamira.it/checkout/cart/configure/id/2017432/",
  "referrer_url": "https://www.glamira.it/",
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
  "_id": "5ebe526d98c9ed37843cf6ce",
  "collection": "view_product_detail",
  "store_id": "7",
  "product_id": "91883",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "248287",
      "value_label": "",
      "value_id": "2062009"
    },
    {
      "option_label": "diamond",
      "option_id": "248286",
      "value_label": "",
      "value_id": "2061985"
    }
  ],
  "current_url": "https://stage.glamira.de/glgb/glamira-pendant-delmare-4-mm.html?alloy=white-silber&diamond=black-sapphire&pearl=red_pearl",
  "referrer_url": "https://stage.glamira.de/glgb/diamond-necklaces/ct_black_sapphire/?order=%5BREDACTED%5D&dir=%5BREDACTED%5D&p=%5BREDACTED%5D",
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
  "_id": "5ed64a3e87725937125cdf53",
  "collection": "view_product_detail",
  "store_id": "12",
  "product_id": "110648",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "336189",
      "value_label": "",
      "value_id": "3346643"
    },
    {
      "option_label": "diamond",
      "option_id": "336188",
      "value_label": "",
      "value_id": "3346621"
    }
  ],
  "current_url": "https://www.glamira.fr/glamira-ring-misha.html?client=%5BREDACTED%5D",
  "referrer_url": "https://www.facebook.com/[REDACTED-EXTERNAL-PATH]",
  "current_url_omitted_tracking_keys": [
    "fbclid"
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

### current unusable or external

```json
{
  "_id": "5eb06fbdb9a5fa3754289c8c",
  "collection": "view_product_detail",
  "store_id": "6",
  "product_id": "108912",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "317678",
      "value_label": "",
      "value_id": "2703948"
    },
    {
      "option_label": "diamond",
      "option_id": "",
      "value_label": "",
      "value_id": ""
    }
  ],
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

Indexed source point reads reverified: `5e84447a78aa7636caf0f64d`, `5e8dbc2766a4b33724ba5f4f`. These are separate from the random-pool denominators.

## 5. Proposed Strategy — approval pending

Proposed result class: **Observed product URL subset**.

Source priority: Explicit product_id → explicit store_id plus current hostname → nonempty, approved current-URL option pairs. The option array validates labels/IDs where possible; it does not fill blanks.

- Recommend retaining only the configuration subset explicitly present in a valid current URL. A missing parameter remains unspecified; an empty query is base-product evidence, not a verified website default.
- Require a trusted storefront host and an unambiguous product association. A product-shaped slug is supporting evidence, not existence validation; the user-verified numeric product route avoids inventing SEO slugs.
- Keep unknown keys and disagreements for review. Conflicting repeated URL values, malformed encoding/keys, or incompatible identity evidence must not produce a resolved configuration.
- Option/value IDs alone cannot supply URL slug values without a product/store-scoped, verified reference. Do not translate labels or use a global ID-to-token dictionary.

Alternative and trade-off: Using option/value IDs to fill every missing URL field could increase apparent coverage, but needs a verified reference and may invent implicit defaults. Recommend the explicit URL subset for this phase.

**Sampled opportunity, not achieved recovery:** 60,063 (75.25%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 19,757 (24.75%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Should this be the primary URL-subset source, leaving empty value labels/IDs as validation evidence rather than filling defaults?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
