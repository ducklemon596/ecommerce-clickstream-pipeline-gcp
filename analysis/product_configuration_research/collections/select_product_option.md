# select_product_option

Status: **research proposal — awaiting user approval**. [Overview](../EVENT_OVERVIEW.md) · [Methods](../README.md) · [Decisions](../OPEN_QUESTIONS.md)

## 1. Event Overview

A selection action whose option array may describe one changed dimension. This purpose is an interpretation of field/URL evidence, not a verified instrumentation contract.

Investigated **63,716 events** in this stratum (21.239% of the shared random pool). Counts below describe this sample only. Each record is one event, not necessarily one product; cart-item counts are separate.

## 2. Observed Patterns

| Field / observed type | Events |
| --- | --- |
| option:array | 63,716 (100.00%) |
| product_id:string | 63,716 (100.00%) |
| recommendation_product_id:missing | 63,716 (100.00%) |
| store_id:string | 63,716 (100.00%) |
| viewing_product_id:missing | 63,716 (100.00%) |

### URL context

| URL category | Current URL | Referrer URL |
| --- | --- | --- |
| cart_or_checkout | 670 (1.05%) | 649 (1.02%) |
| empty | 0 (0.00%) | 6,670 (10.47%) |
| external | 0 (0.00%) | 11,353 (17.82%) |
| invalid_or_nonweb | 1 (0.00%) | 104 (0.16%) |
| merchant_other_page | 0 (0.00%) | 36,078 (56.62%) |
| product_shaped | 63,045 (98.95%) | 8,644 (13.57%) |
| recommendation_route | 0 (0.00%) | 218 (0.34%) |

### Query-key observations

Counts below are parameter occurrences, not events. Candidate names are not an approved option allowlist.

| Current query key | Occurrences |
| --- | --- |
| alloy | 62211 |
| diamond | 53624 |
| itm_medium | 30972 |
| itm_source | 30972 |
| stone2 | 29150 |
| gclid | 11911 |
| stone | 3893 |
| stone3 | 3232 |
| keyword | 873 |
| matchtype | 873 |
| pearl | 804 |
| synthetic | 780 |
| utm_medium | 611 |
| utm_source | 610 |
| utm_campaign | 444 |

Unknown/nonclassified current keys: `discountid` (83), `___store` (47), `client` (7), `amp;alloy` (4), `;diamond` (3), `kkkk` (3), `menstone` (3), `ctype` (2), `edit_form` (2), `kk` (2), `/skin/frontend/glamira2014/default/favicon.ico` (1), `123sd` (1). Values for these keys were redacted before transfer.

### Option and identifier paths

| Relevant path / observed JSON type | Path occurrences |
| --- | --- |
| option[].option_id:string | 65267 |
| option[].option_label:string | 65267 |
| option[].value_label:string | 65267 |
| option[].value_id:string | 64750 |
| option:array | 63716 |
| product_id:string | 63716 |
| store_id:string | 63716 |

| Top-level option item field | Occurrences |
| --- | --- |
| option_id:string | 65267 |
| option_label:string | 65267 |
| value_label:string | 65267 |
| value_id:string | 64750 |

Observed option labels/keys: `alloy` (32,869), `diamond` (24,341), `stone2` (5,714), `stone3` (1,087), `pear` (739), `stonetow` (517).

### Store and domain evidence

| Observed store ID / current host | Events |
| --- | --- |
| 6 @ www.glamira.de | 9755 |
| 7 @ www.glamira.co.uk | 5209 |
| 12 @ www.glamira.fr | 4172 |
| 41 @ www.glamira.com | 3731 |
| 14 @ www.glamira.it | 3125 |
| 19 @ www.glamira.se | 2481 |
| 8 @ www.glamira.es | 2481 |
| 11 @ www.glamira.nl | 2291 |

Observed 76 store IDs and 74 current hosts. 5 store IDs had more than one current host; 8 current hosts appeared with more than one store ID. This does not establish a global one-to-one store/domain/country mapping. Referrer hosts do not define the event store.

## 3. Edge Cases

| Event-level check | Observed in this stratum |
| --- | --- |
| option_url_pair_match | 60,252 (94.56%) |
| option_url_pair_conflict | 2,982 (4.68%) |
| selected_key_missing_from_url | 260 (0.41%) |
| unmapped_option_label | 313 (0.49%) |
| conflicting_option_labels | 0 (0.00%) |
| single_option_item | 63,199 (99.19%) |
| empty_value_label | 516 (0.81%) |
| current_no_candidate_option_values | 142 (0.22%) |
| current_unknown_query_keys | 158 (0.25%) |
| current_nonproduction_host | 188 (0.30%) |
| current_bad_percent | 0 (0.00%) |
| current_control_or_space | 0 (0.00%) |
| current_repeated_equal_key | 0 (0.00%) |
| current_repeated_conflicting_key | 1 (0.00%) |
| current_malformed_parameter_key | 4 (0.01%) |
| product_route_id_match | 9 (0.01%) |
| current_html_escaped | 1 (0.00%) |
| current_not_product_shaped | 671 (1.05%) |
| viewed_recommended_differ | 0 (0.00%) |

Zero means not observed in this sample. It does not prove absence in the collection. Different flags can overlap. URL/option comparison requires the literal same option label and nonempty value_label; missing or translated labels are not automatically repaired. A conflict does not identify which source is newer.

Classification: a cart/configure page, queryless HTTP URL or multi-item cart is a valid structural variation, not automatically a data-quality error. Blank values and unmapped display labels make configuration state unspecified/partial. Invalid web URLs, malformed parameter keys and conflicting repeated values are problematic input cases. Selection timing, recommendation ownership and grade-to-URL representation remain semantic hypotheses until independently verified. A valid nonproduction host still requires a separate crawl-scope decision.

### Extended timing investigation requested by the user

| Conflict-cohort outcome | Anchors | Stratum-weighted share |
| --- | --- | --- |
| inconclusive_anchor_timestamp_tie | 4 | 3.78% |
| inconclusive_no_successor_url | 30 | 28.09% |
| confirmed_pre_to_selected | 30 | 25.97% |
| inconclusive_intervening_selection | 39 | 29.46% |
| persistent_old_url_counterevidence | 8 | 5.96% |
| inconclusive_one_old_successor | 6 | 3.94% |
| different_successor_counterevidence | 3 | 2.81% |

120 conflict anchors plus 40 controls were examined in bounded device/product/store contexts ordered by time_stamp. Support means a visible chosen-key transition, not proof of a complete post-selection configuration. Counterevidence to prompt URL catch-up does not prove the selected value invalid. Details, examples and conditions are in [SELECTION_TIMING.md](../SELECTION_TIMING.md). Preserving snapshot and delta is approved; any inference branch remains a proposal.

### Candidate label aliases — hypotheses only

| Original label | Items | Nonempty value labels | Unique same-value URL key overlap | No overlap |
| --- | --- | --- | --- | --- |
| pear | 739 | 234 | pearl=229 | 5 |
| stonetow | 517 | 80 | none | 80 |

Same-value overlap is not proof of an alias: several stone dimensions can share one value. Do not map a translated/misspelled label from spelling alone.

Proposed label handling: when a `pear` value is already corroborated by an explicit `pearl` URL pair, retain that observed URL pair independently; do not manufacture a universal alias. The observed nonempty `stonetow` values had no exact candidate-URL overlap in this pool, so keep that label unresolved rather than autocorrecting its spelling.

## 4. Evidence

Excerpts are actual MongoDB records with source `_id` retained. Personal fields were never returned; campaign values and unknown query values were redacted on the VM. Tracking pairs are omitted for display only. Any truncated array is explicitly marked. Root ID strings are traceability keys, not event timestamps.

### direct identity with url subset

```json
{
  "_id": "5e8617248772593712fe58d3",
  "collection": "select_product_option",
  "store_id": "10",
  "product_id": "90315",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "107444",
      "value_label": "white-750",
      "value_id": "781569"
    }
  ],
  "current_url": "https://www.glamira.ch/glamira-bridal-set-heavenly-vows.html?diamond=diamond-sapphire&alloy=white-750",
  "referrer_url": "https://www.glamira.ch/bridal-set/585-weiss-gold/",
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

### option url pair conflict

```json
{
  "_id": "5e9a9ca39fade236dccec573",
  "collection": "select_product_option",
  "store_id": "62",
  "product_id": "84874",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "322818",
      "value_label": "red-585",
      "value_id": "2737691"
    }
  ],
  "current_url": "https://www.glamira.com.mx/glamira-diamante-anillo-estelle-skug100125.html?alloy=white-585&diamond=diamond-Brillant&stone2=diamond-Swarovsky",
  "referrer_url": "https://www.glamira.com.mx/anillos-de-compromiso/",
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

### selected key missing from url

```json
{
  "_id": "5ec1e4161b679337360f7882",
  "collection": "select_product_option",
  "store_id": "62",
  "product_id": "102492",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "315651",
      "value_label": "white-750",
      "value_id": "2687432"
    }
  ],
  "current_url": "https://www.glamira.com.mx/glamira-ring-zophiel.html",
  "referrer_url": "",
  "research_url_observations": {
    "current_url": {
      "scheme": "https:"
    },
    "referrer_url": {}
  }
}
```

### unmapped option label

```json
{
  "_id": "5ed3fb1f98c9ed37845aea05",
  "collection": "select_product_option",
  "store_id": "51",
  "product_id": "102878",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "258484",
      "value_label": "white-375",
      "value_id": "2138740"
    },
    {
      "option_label": "diamond",
      "option_id": "258483",
      "value_label": "diamond-Brillant",
      "value_id": "2138732"
    },
    {
      "option_label": "pear",
      "option_id": "",
      "value_label": "white_pearl",
      "value_id": ""
    },
    {
      "option_label": "stonetow",
      "option_id": "",
      "value_label": ""
    }
  ],
  "current_url": "https://www.glamira.ro/glamira-ring-lorelye-6-mm.html?diamond=diamond-Brillant&pearl=white_pearl&alloy=white-375",
  "referrer_url": "",
  "current_url_omitted_tracking_keys": [
    "itm_medium",
    "itm_source"
  ],
  "research_url_observations": {
    "current_url": {
      "scheme": "https:"
    },
    "referrer_url": {}
  }
}
```

### current repeated conflicting key

```json
{
  "_id": "5ecedd2d7d602a3748eb6c4d",
  "collection": "select_product_option",
  "store_id": "29",
  "product_id": "109723",
  "option": [
    {
      "option_label": "diamond",
      "option_id": "326101",
      "value_label": "ruby-Swarovsky",
      "value_id": "3174463"
    }
  ],
  "current_url": "https://www.glamira.com.au/glamira-earring-maritza.html?stone2=diamond-sapphire&alloy=white-platin&diamond=diamond-Swarovsky&alloy=white_yellow-585&diamond=ruby-Swarovsky",
  "referrer_url": "",
  "research_url_observations": {
    "current_url": {
      "html_escaped": true,
      "scheme": "https:",
      "repeated_conflicting_key": true
    },
    "referrer_url": {}
  }
}
```

### current not product shaped

```json
{
  "_id": "5ebfee0133eacf36f4b018a9",
  "collection": "select_product_option",
  "store_id": "33",
  "product_id": "102062",
  "option": [
    {
      "option_label": "alloy",
      "option_id": "253501",
      "value_label": "white-585",
      "value_id": "2111665"
    }
  ],
  "current_url": "https://www.glamira.be/fr/checkout/cart/configure/id/2157795/?alloy=white-585",
  "referrer_url": "https://www.glamira.be/fr/checkout/cart/configure/id/2157788/",
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
  "_id": "5ebe4f74e0da54376c1516a1",
  "collection": "select_product_option",
  "store_id": "7",
  "product_id": "109682",
  "option": [
    {
      "option_label": "stone2",
      "option_id": "3170591",
      "value_label": "black-sapphire",
      "value_id": "3397260"
    }
  ],
  "current_url": "https://stage.glamira.de/glgb/glamira-pendant-quinn.html?alloy=white-585&diamond=black-sapphire&stone2=black-sapphire",
  "referrer_url": "https://stage.glamira.de/glgb/diamond-necklaces/ct_black_sapphire/?order=%5BREDACTED%5D&dir=%5BREDACTED%5D",
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

Indexed source point reads reverified: `5e9a9ca39fade236dccec573`, `5ebfc2d166936336eea1ac4b`, `5ec1e4161b679337360f7882`, `5ed3c87978aa7636ca4d7b0e`. These are separate from the random-pool denominators.

### Bounded device/product/store context

```json
{
  "_id": "5e9a9ca39fade236dccec573",
  "scanned": 2000,
  "matched_count": 15,
  "anchor_current_url": "https://www.glamira.com.mx/glamira-diamante-anillo-estelle-skug100125.html?alloy=white-585&diamond=diamond-Brillant&stone2=diamond-Swarovsky",
  "nearby_observations": [
    {
      "_id": "5e9a9caaa32efc3766759c58",
      "collection": "select_product_option",
      "seconds_from_anchor": 7,
      "current_url": "https://www.glamira.com.mx/glamira-diamante-anillo-estelle-skug100125.html?stone2=diamond-Swarovsky&alloy=red-585&diamond=blackdiamond",
      "option": [
        {
          "option_label": "diamond",
          "value_label": "blackdiamond"
        }
      ]
    },
    {
      "_id": "5e9a9c9698c9ed3784113646",
      "collection": "view_product_detail",
      "seconds_from_anchor": -13,
      "current_url": "https://www.glamira.com.mx/glamira-diamante-anillo-estelle-skug100125.html?alloy=white-585&diamond=diamond-Brillant&stone2=diamond-Swarovsky",
      "option": [
        {
          "option_label": "alloy",
          "value_label": ""
        },
        {
          "option_label": "diamond",
          "value_label": ""
        }
      ]
    },
    {
      "_id": "5e9a9cb4c671fc36b7f67d8b",
      "collection": "select_product_option",
      "seconds_from_anchor": 16,
      "current_url": "https://www.glamira.com.mx/glamira-diamante-anillo-estelle-skug100125.html?stone2=diamond-Swarovsky&alloy=red-585&diamond=yellowdiamond",
      "option": [
        {
          "option_label": "diamond",
          "value_label": "yellowdiamond"
        }
      ]
    }
  ]
}
```

Read at most 1,000 predecessors and 1,000 successors through `_id_`; compare device ID, product and store on the VM, without returning the device value. The source time_stamp gives the displayed relative seconds. This is not a verified or complete session, and second-level ties cannot establish order.

### Bounded device/product/store context

```json
{
  "_id": "5ec1e4161b679337360f7882",
  "scanned": 2000,
  "matched_count": 11,
  "anchor_current_url": "https://www.glamira.com.mx/glamira-ring-zophiel.html",
  "nearby_observations": [
    {
      "_id": "5ec1e41830c31e3730100cf7",
      "collection": "select_product_option",
      "seconds_from_anchor": 3,
      "current_url": "https://www.glamira.com.mx/glamira-ring-zophiel.html",
      "option": [
        {
          "option_label": "alloy",
          "value_label": "white-platin"
        }
      ]
    },
    {
      "_id": "5ec1e42a66936336eea53546",
      "collection": "select_product_option",
      "seconds_from_anchor": 20,
      "current_url": "https://www.glamira.com.mx/glamira-ring-zophiel.html",
      "option": [
        {
          "option_label": "alloy",
          "value_label": "white-750"
        }
      ]
    },
    {
      "_id": "5ec1e3fe1b679337360f786f",
      "collection": "select_product_option",
      "seconds_from_anchor": -24,
      "current_url": "https://www.glamira.com.mx/glamira-ring-zophiel.html",
      "option": [
        {
          "option_label": "alloy",
          "value_label": "white-585"
        }
      ]
    }
  ]
}
```

Read at most 1,000 predecessors and 1,000 successors through `_id_`; compare device ID, product and store on the VM, without returning the device value. The source time_stamp gives the displayed relative seconds. This is not a verified or complete session, and second-level ties cannot establish order.

## 5. Proposed Strategy — approval pending

Proposed result class: **URL snapshot plus separately observed selection**.

Source priority: Explicit product_id and store/current hostname; compare each selected option_label/value_label with the current URL. Keep the observed URL snapshot and selected delta distinguishable.

- When a selected key/value agrees with the URL, recommend accepting that pair as corroborated. Extra URL options are still an observed subset, not proof of completeness.
- When the selected value disagrees, do not choose URL priority or overlay silently. The URL may be the previous state, or the option event may be stale; emission order is not documented.
- A selected key absent from the URL is a delta candidate, not permission to manufacture a full resulting configuration. Resolve timing with instrumentation or a validated same-session sequence before any overlay policy.
- The user approved preserving both sources for now. A future inferred overlay may be proposed only for a corroborated, unambiguous changed-key transition; preserve the original snapshot/delta and mark the result inferred and partial. See SELECTION_TIMING.md for measured support and counterevidence; no universal overlay is approved.
- Preserve original label/value spelling. Localized or unknown labels need an explicit alias reference; multiple different values for one option label remain unresolved.

Alternative and trade-off: Overlaying the selected value onto the URL is plausible after a change event, but can attach a future or stale delta to the wrong snapshot. Recommend retaining disagreement as unresolved until approved.

**Sampled opportunity, not achieved recovery:** 63,574 (99.78%) events have a nonempty product_id/viewing_product_id, store, current host and at least one candidate URL value. This is only an evidence-shape count: it can include the wrong page/product association or an invalid host and is not a success count. Base identities with no such values: 141 (0.22%). No unique-configuration coverage or population recovery rate was measured.

If identity is missing, source ownership conflicts, values are malformed or no approved mapping represents the selected dimension, configuration recovery remains **unknown/partial**. Session history is not a universal fallback: any proposed sequence join must establish a real session key, event ordering and matching product/store. Shared IP or neighboring BSON IDs are insufficient.

## 6. Limitations & Confidence

STRONGER structural coverage: at least 500 randomly sampled events; this is not validation of instrumentation timing or website option semantics.

The source is a random MongoDB sample without a reproducible random seed. Source metadata and private evidence identity are recorded in the research README. HTTP pages and the user-verified product-ID endpoint were not requested in this research; product existence, accepted query keys and website defaults were not tested. A product-shaped path is a heuristic; external .html pages, account pages and local files must not become product evidence by suffix alone.

Display labels may differ from URL slug tokens. Numeric/string IDs and literal equality were observed without assuming a universal identity or alias mapping. Product/configuration temporal state is not proven by event names. No extraction strategy in this file has been applied to production data.

## 7. Open Questions

Preserving snapshot and delta is approved. After reviewing the quantified timing study, are its conditional inferred-overlay criteria sufficient, or is stronger session/instrumentation verification required before any implementation?

Please approve or revise this event-specific proposal. Shared unresolved choices are listed in [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md).
