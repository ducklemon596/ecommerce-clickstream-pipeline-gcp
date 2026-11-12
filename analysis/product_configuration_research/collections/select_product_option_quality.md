# select_product_option_quality

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

A selection action with additional quality/quality_label fields. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **16,210 events** in this stratum (5.403% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:array | 16,210 (100.00%) |
| product_id:string | 16,210 (100.00%) |
| recommendation_product_id:missing | 16,210 (100.00%) |
| store_id:string | 16,210 (100.00%) |
| viewing_product_id:missing | 16,210 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 205 (1.26%) | 193 (1.19%) |
| empty | 0 (0.00%) | 2,039 (12.58%) |
| external | 0 (0.00%) | 2,011 (12.41%) |
| invalid_or_nonweb | 0 (0.00%) | 20 (0.12%) |
| merchant_other_page | 0 (0.00%) | 8,916 (55.00%) |
| product_shaped | 16,005 (98.74%) | 2,954 (18.22%) |
| recommendation_route | 0 (0.00%) | 77 (0.48%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| alloy | 15630 |
| diamond | 14980 |
| stone2 | 8801 |
| itm_medium | 8049 |
| itm_source | 8049 |
| gclid | 2486 |
| stone3 | 790 |
| stone | 750 |
| keyword | 176 |
| matchtype | 176 |
| utm_medium | 128 |
| utm_source | 126 |
| fbclid | 95 |
| utm_campaign | 83 |
| pearl | 59 |

Unknown/nonclassified current keys: `___store` (15), `discountid` (9), `client` (1), `ctype` (1), `edit_form` (1), `kkalloy` (1), `kkkkkalloy` (1). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| option:array | 16210 |
| option[].quality:string | 16210 |
| product_id:string | 16210 |
| store_id:string | 16210 |
| option[].option_label:string | 15388 |
| option[].value_id:string | 15388 |
| option[].value_label:string | 15388 |
| option[].option_id:string | 14080 |
| option[].quality_label:string | 14008 |

| Top-level option item field | Occurrences |
| --- | --- |
| quality:string | 16210 |
| option_label:string | 15388 |
| value_id:string | 15388 |
| value_label:string | 15388 |
| option_id:string | 14080 |
| quality_label:string | 14008 |

Observed option labels/keys: `stone/diamonds` (13,186), `stone 2` (1,110), `damenring steinbesatz` (894), `stone 3` (198).

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 2486 |
| 7 @ www.glamira.co.uk | 1271 |
| 12 @ www.glamira.fr | 927 |
| 14 @ www.glamira.it | 800 |
| 41 @ www.glamira.com | 794 |
| 19 @ www.glamira.se | 684 |
| 11 @ www.glamira.nl | 638 |
| 8 @ www.glamira.es | 566 |

Observed 68 store IDs and 65 current hosts. 3 store IDs had more than one current host; 5 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_conflict | 0 (0.00%) |
| unmapped_option_label | 15,388 (94.93%) |
| conflicting_option_labels | 0 (0.00%) |
| single_option_item | 16,210 (100.00%) |
| empty_value_label | 822 (5.07%) |
| quality_present | 16,210 (100.00%) |
| quality_label_present | 14,008 (86.42%) |
| current_no_candidate_option_values | 198 (1.22%) |
| current_unknown_query_keys | 28 (0.17%) |
| current_nonproduction_host | 55 (0.34%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 8 (0.05%) |
| current_repeated_conflicting_key | 0 (0.00%) |
| current_malformed_parameter_key | 0 (0.00%) |
| product_route_id_match | 1 (0.01%) |
| current_html_escaped | 0 (0.00%) |
| current_not_product_shaped | 205 (1.26%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.

### Candidate label aliases — hypotheses only

| Original label | Items | Nonempty value labels | Unique same-value URL key overlap | No overlap |
| --- | --- | --- | --- | --- |
| stone/diamonds | 13186 | 13186 | diamond=9567; stone2=170; stone3=5 | 2145 |
| stone 3 | 198 | 198 | stone2=23; diamond=25; stone3=29 | 52 |
| damenring steinbesatz | 894 | 894 | stone=611 | 280 |
| stone 2 | 1110 | 1110 | stone2=542; diamond=67; stone3=4 | 189 |

Same-value overlap is not proof of an alias: several stone dimensions can share one value. Do not map a translated/misspelled label from spelling alone.

### URL representation of quality

| Measured quality check | Count |
| --- | --- |
| distinct_redacted_url_product_option_groups | 15255 |
| grade_literal_in_candidate_url_value | 0 |
| groups_with_multiple_nonempty_quality_codes | 489 |
| groups_with_multiple_quality_observations | 489 |
| items | 16210 |
| quality_and_label_differ | 6367 |
| quality_and_label_equal | 7641 |
| quality_named_query_key | 0 |

Repeated-URL groups compare the redacted URL, product/store and option/value label; campaign values were removed before transfer. Different grade observations for the same group are a counterexample to URL-only completeness. No inference about website defaults or accepted grade parameters follows.

## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### direct identity with url subset

```json
{
  "_id": "5ea60a28fe6972375abd0d61",
  "collection": "select_product_option_quality",
  "store_id": "6",
  "product_id": "99417",
  "option": [
    {
      "option_label": "damenring steinbesatz",
      "option_id": "188684",
      "value_label": "diamond-Brillant",
      "value_id": "1498598",
      "quality": "AAAA"
    }
  ],
  "current_url": "https://www.glamira.de/checkout/cart/configure/id/2067273/?alloy=white-platin",
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
  "_id": "5ece86fc78aa7636ca471c7d",
  "collection": "select_product_option_quality",
  "store_id": "6",
  "product_id": "103307",
  "option": [
    {
      "option_label": "stone/diamonds",
      "option_id": "261013",
      "value_label": "greentourmaline",
      "value_id": "2164504",
      "quality": "A",
      "quality_label": "A"
    }
  ],
  "current_url": "https://test.glamira.de/glde/glamira-ring-jimalee.html?alloy=yellow-585&stone2=ruby&stone3=sapphire&diamond=greentourmaline",
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
  "_id": "5eb941221b6793373602f914",
  "collection": "select_product_option_quality",
  "store_id": "32",
  "product_id": "104413",
  "option": [
    {
      "option_label": "stone/diamonds",
      "option_id": "268617",
      "value_label": "tanzanite",
      "value_id": "2270284",
      "quality": "AAAA",
      "quality_label": "AAAA"
    }
  ],
  "current_url": "https://www.glamira.be/glamira-ring-denis.html?stone2=diamond-Swarovsky&alloy=white-silber&diamond=tanzanite&ctype=%5BREDACTED%5D&client=%5BREDACTED%5D",
  "referrer_url": "https://html5.gamedistribution.com/[REDACTED-EXTERNAL-PATH]",
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

### current no candidate option values

```json
{
  "_id": "5eb136cd60f0183777339ba1",
  "collection": "select_product_option_quality",
  "store_id": "50",
  "product_id": "95210",
  "option": [
    {
      "option_label": "stone/diamonds",
      "option_id": "334984",
      "value_label": "green-sapphire",
      "value_id": "3314295",
      "quality": "A",
      "quality_label": "A"
    }
  ],
  "current_url": "https://www.glamira.pl/glamira-ring-berdina-3.0-crt.html",
  "referrer_url": "",
  "research_url_observations": {
    "current_url": {
      "scheme": "https:"
    },
    "referrer_url": {}
  }
}
```

Indexed source point reads reverified: `5ea60a28fe6972375abd0d61`. These are separate from the random-pool denominators.

### Bounded device/product/store context

```json
{
  "_id": "5ea60a28fe6972375abd0d61",
  "scanned": 2000,
  "matched_count": 5,
  "anchor_current_url": "https://www.glamira.de/checkout/cart/configure/id/2067273/?alloy=white-platin",
  "nearby_observations": [
    {
      "_id": "5ea60a29bb30d637187c09af",
      "collection": "select_product_option_quality",
      "seconds_from_anchor": 0,
      "current_url": "https://www.glamira.de/checkout/cart/configure/id/2067273/?alloy=white-platin",
      "option": [
        {
          "option_label": "damenring steinbesatz",
          "value_label": "diamond-Brillant",
          "quality": "AAA"
        }
      ]
    },
    {
      "_id": "5ea60a281b67933736e9f14b",
      "collection": "select_product_option_quality",
      "seconds_from_anchor": -1,
      "current_url": "https://www.glamira.de/checkout/cart/configure/id/2067273/?alloy=white-platin",
      "option": [
        {
          "option_label": "damenring steinbesatz",
          "value_label": "diamond-Brillant",
          "quality": "AAA"
        }
      ]
    },
    {
      "_id": "5ea60a2656b3dd3742e22628",
      "collection": "select_product_option_quality",
      "seconds_from_anchor": -2,
      "current_url": "https://www.glamira.de/checkout/cart/configure/id/2067273/?alloy=white-platin",
      "option": [
        {
          "option_label": "damenring steinbesatz",
          "value_label": "diamond-Brillant",
          "quality": "AAAA"
        }
      ]
    }
  ]
}
```

Read at most 1,000 predecessors and 1,000 successors through `_id_`; compare device ID, product and store on the VM, without returning the device value. The source time_stamp gives the displayed relative seconds. This is not a verified or complete session, and second-level ties cannot establish order.

### Different quality observations with an unchanged configuration URL

```json
[
  {
    "_id": "5e9a9cfaa32efc3766759c86",
    "collection": "select_product_option_quality",
    "seconds_from_anchor": 86,
    "current_url": "https://www.glamira.com.mx/glamira-diamante-anillo-estelle-skug100125.html?stone2=diamond-Swarovsky&diamond=diamond-Brillant&alloy=yellow-585",
    "option": [
      {
        "option_label": "stone/diamonds",
        "value_label": "diamond-Brillant",
        "quality": "AAAA",
        "quality_label": "VVS"
      }
    ]
  },
  {
    "_id": "5e9a9cfca32efc3766759c88",
    "collection": "select_product_option_quality",
    "seconds_from_anchor": 88,
    "current_url": "https://www.glamira.com.mx/glamira-diamante-anillo-estelle-skug100125.html?stone2=diamond-Swarovsky&diamond=diamond-Brillant&alloy=yellow-585",
    "option": [
      {
        "option_label": "stone/diamonds",
        "value_label": "diamond-Brillant",
        "quality": "AA",
        "quality_label": "SI"
      }
    ]
  }
]
```

These nearby records match device/product/store inside the bounded probe. Grade changes are observable even when the URL option subset is unchanged. No user/device identifier is published, and this does not establish a complete session contract.

## 5. Proposed Strategy — approval pending

Proposed result class: **Product URL subset; quality semantics unresolved**.

Source priority: Explicit product_id and store/current hostname → observed URL option pairs; preserve quality, quality_label, option_label and value IDs as separate evidence.

- Recommend retaining the explicit URL subset while marking the selected quality dimension unresolved. A URL value may describe a stone, while quality/quality_label describe a separate grade.
- Do not turn translated labels such as stone/diamonds or stone 2 into diamond/stone2 keys by spelling similarity. Do not append quality as a URL parameter merely because the field exists.
- Require product/store/option identity and a verified grade-to-URL representation before encoding quality. If the URL does not represent that dimension, configuration-level crawling may be impossible through URL parameters alone.

Alternative and trade-off: A universal quality parameter would be simple, but the sample cannot establish that the website accepts it or that it identifies the selected grade. Recommend holding this dimension for review.

**Sampled opportunity, not achieved recovery:** 16,012 (98.78%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 198 (1.22%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Keep quality unresolved until its option/URL representation is verified (recommended), or approve a specific product-scoped mapping to investigate?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
