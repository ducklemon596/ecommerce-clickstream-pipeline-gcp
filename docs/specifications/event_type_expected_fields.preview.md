# Possible fields by event type

**100,000 sampled records · 21 observed event types**

Source: `summary_sample.json`. Observed 2026-11-01 (UTC).

This sequential JSON sample is not random. The lists show fields observed in the sample; rare fields or event types may be missing.

The 15 fields present in every sampled record are listed once below. Each event table then lists its additional observed fields, including nested paths.

**Present** means the key exists, including when its value is null or empty. **NULL** is explicit BSON null; **Empty** is an empty string, array, or object. Percentages use the sampled rows for that event. For nested array fields, a row counts if any item has the field or value. `[]` means an array item.

Meanings are inferred unless stated otherwise. An observed field is not necessarily required; an unobserved field is not proven inapplicable.

## Shared fields — present in all 100,000 sampled records

| Field | Meaning | BSON types | NULL | Empty |
|---|---|---|---:|---:|
| `_id` | Database document identifier (technical field). | objectId | 0.00% | 0.00% |
| `api_version` | Tracking API version. | string | 0.00% | 0.00% |
| `collection` | Event type used to group these records (observed). | string | 0.00% | 0.00% |
| `current_url` | Page URL that emitted the event. | string | 0.00% | 0.00% |
| `device_id` | Tracked device/browser reference. | string | 0.00% | 0.00% |
| `email_address` | Email value; examples redacted. | string | 0.00% | 92.44% |
| `ip` | Recorded IP address; proxy/client attribution unconfirmed. | string | 0.00% | 0.00% |
| `local_time` | Local time string; timezone unconfirmed. | string | 0.00% | 0.00% |
| `referrer_url` | Referring or previous page URL. | string | 0.00% | 11.42% |
| `resolution` | Screen or viewport dimensions. | string | 0.00% | 0.00% |
| `show_recommendation` | Possible recommendation-display setting. | null, string | 20.07% | 0.00% |
| `store_id` | Storefront reference; market mapping unconfirmed. | string | 0.00% | 0.00% |
| `time_stamp` | Event timestamp; units and timezone need confirmation. | int32 | 0.00% | 0.00% |
| `user_agent` | Browser/device user-agent string. | string | 0.00% | 0.00% |
| `user_id_db` | User reference; not a verified person identity. | string | 0.00% | 92.44% |

## `add_to_cart_action` — 508 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `currency` | Currency code or symbol; symbols can be ambiguous. | null, string | 100.00% | 2.17% | 0.00% |
| `is_paypal` | Possible PayPal flag; semantics unconfirmed. | bool, null | 100.00% | 97.83% | 0.00% |
| `option` | Product-option payload; object/array shape varies by event. | array | 100.00% | 0.00% | 0.00% |
| `option[]` | One item in the parent array. | object | 100.00% | 0.00% | 0.00% |
| `option[].option_id` | Product-option reference. | string | 100.00% | 0.00% | 36.61% |
| `option[].option_label` | Product-option label. | string | 100.00% | 0.00% | 0.00% |
| `option[].value_id` | Selected option-value reference. | string | 100.00% | 0.00% | 36.61% |
| `option[].value_label` | Selected option-value label. | string | 100.00% | 0.00% | 100.00% |
| `price` | Monetary value; locale, tax, and item/order basis unconfirmed. | null, string | 100.00% | 2.17% | 0.00% |
| `product_id` | Product reference. | string | 100.00% | 0.00% | 0.00% |

## `checkout` — 292 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `cart_products` | Cart-item payload; purchased-item meaning depends on the event. | array | 100.00% | 0.00% | 0.00% |
| `cart_products[]` | One item in the parent array. | object | 100.00% | 0.00% | 0.00% |
| `cart_products[].amount` | Item quantity; units unconfirmed. | int32 | 100.00% | 0.00% | 0.00% |
| `cart_products[].option` | Product-option payload; object/array shape varies by event. | array, string | 100.00% | 0.00% | 4.79% |
| `cart_products[].option[]` | One item in the parent array. | object | 95.55% | 0.00% | 0.00% |
| `cart_products[].option[].option_id` | Product-option reference. | int32 | 95.55% | 0.00% | 0.00% |
| `cart_products[].option[].option_label` | Product-option label. | string | 95.55% | 0.00% | 0.00% |
| `cart_products[].option[].value_id` | Selected option-value reference. | int32 | 95.55% | 0.00% | 0.00% |
| `cart_products[].option[].value_label` | Selected option-value label. | string | 95.55% | 0.00% | 0.00% |
| `cart_products[].product_id` | Product reference. | int32 | 100.00% | 0.00% | 0.00% |
| `order_id` | Order reference; its encoding varies. | string | 100.00% | 0.00% | 100.00% |

## `checkout_success` — 101 records

Small sample: other fields may exist for this event.

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `cart_products` | Cart-item payload; purchased-item meaning depends on the event. | array | 100.00% | 0.00% | 0.00% |
| `cart_products[]` | One item in the parent array. | object | 100.00% | 0.00% | 0.00% |
| `cart_products[].amount` | Item quantity; units unconfirmed. | int32 | 100.00% | 0.00% | 0.00% |
| `cart_products[].currency` | Currency code or symbol; symbols can be ambiguous. | string | 100.00% | 0.00% | 1.98% |
| `cart_products[].option` | Product-option payload; object/array shape varies by event. | array, string | 100.00% | 0.00% | 8.91% |
| `cart_products[].option[]` | One item in the parent array. | object | 92.08% | 0.00% | 0.00% |
| `cart_products[].option[].option_id` | Product-option reference. | int32 | 92.08% | 0.00% | 0.00% |
| `cart_products[].option[].option_label` | Product-option label. | string | 92.08% | 0.00% | 0.00% |
| `cart_products[].option[].value_id` | Selected option-value reference. | int32 | 92.08% | 0.00% | 0.00% |
| `cart_products[].option[].value_label` | Selected option-value label. | string | 92.08% | 0.00% | 0.00% |
| `cart_products[].price` | Monetary value; locale, tax, and item/order basis unconfirmed. | string | 100.00% | 0.00% | 0.00% |
| `cart_products[].product_id` | Product reference. | int32 | 100.00% | 0.00% | 0.00% |
| `order_id` | Order reference; its encoding varies. | double, int32 | 100.00% | 0.00% | 0.00% |

## `landing_page_recommendation_visible` — 10 records

Small sample: other fields may exist for this event.

No additional fields observed in this sample.

## `listing_page_recommendation_clicked` — 1 record

Small sample: other fields may exist for this event.

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `cat_id` | Unknown; category-like field name needs confirmation. | null | 100.00% | 100.00% | 0.00% |
| `collect_id` | Unknown tracking/collection code. | string | 100.00% | 0.00% | 100.00% |
| `option` | Product-option payload; object/array shape varies by event. | object | 100.00% | 0.00% | 0.00% |
| `option.alloy` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 0.00% |
| `option.diamond` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 100.00% |
| `option.shapediamond` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 100.00% |
| `recommendation_clicked_position` | Clicked recommendation position; index base unconfirmed. | null | 100.00% | 100.00% | 0.00% |
| `recommendation_product_id` | Recommended product reference. | null | 100.00% | 100.00% | 0.00% |

## `listing_page_recommendation_noticed` — 2 records

Small sample: other fields may exist for this event.

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `cat_id` | Unknown; category-like field name needs confirmation. | null | 100.00% | 100.00% | 0.00% |
| `collect_id` | Unknown tracking/collection code. | string | 100.00% | 0.00% | 100.00% |
| `option` | Product-option payload; object/array shape varies by event. | object | 100.00% | 0.00% | 0.00% |
| `option.alloy` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 100.00% |
| `option.diamond` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 100.00% |
| `option.shapediamond` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 100.00% |

## `listing_page_recommendation_visible` — 17 records

Small sample: other fields may exist for this event.

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `cat_id` | Unknown; category-like field name needs confirmation. | null | 100.00% | 100.00% | 0.00% |
| `collect_id` | Unknown tracking/collection code. | string | 100.00% | 0.00% | 94.12% |
| `option` | Product-option payload; object/array shape varies by event. | object | 100.00% | 0.00% | 0.00% |
| `option.alloy` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 94.12% |
| `option.diamond` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 100.00% |
| `option.shapediamond` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 100.00% |

## `product_detail_recommendation_clicked` — 291 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `recommendation_clicked_position` | Clicked recommendation position; index base unconfirmed. | int32 | 100.00% | 0.00% | 0.00% |
| `recommendation_product_id` | Recommended product reference. | string | 100.00% | 0.00% | 0.00% |
| `viewing_product_id` | Reference to the product being viewed. | string | 100.00% | 0.00% | 0.00% |

## `product_detail_recommendation_noticed` — 1,438 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `viewing_product_id` | Reference to the product being viewed. | string | 100.00% | 0.00% | 0.00% |

## `product_detail_recommendation_visible` — 3,844 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `viewing_product_id` | Reference to the product being viewed. | string | 100.00% | 0.00% | 0.00% |

## `search_box_action` — 688 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `key_search` | Possible search input; examples redacted. | null, string | 100.00% | 51.60% | 3.34% |

## `select_product_option` — 19,731 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `option` | Product-option payload; object/array shape varies by event. | array | 100.00% | 0.00% | 0.00% |
| `option[]` | One item in the parent array. | object | 100.00% | 0.00% | 0.00% |
| `option[].option_id` | Product-option reference. | string | 100.00% | 0.00% | 0.87% |
| `option[].option_label` | Product-option label. | string | 100.00% | 0.00% | 0.00% |
| `option[].value_id` | Selected option-value reference. | string | 100.00% | 0.00% | 0.91% |
| `option[].value_label` | Selected option-value label. | string | 100.00% | 0.00% | 0.87% |
| `product_id` | Product reference. | string | 100.00% | 0.00% | 0.00% |

## `select_product_option_quality` — 6,160 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `option` | Product-option payload; object/array shape varies by event. | array | 100.00% | 0.00% | 0.00% |
| `option[]` | One item in the parent array. | object | 100.00% | 0.00% | 0.00% |
| `option[].option_id` | Product-option reference. | string | 89.04% | 0.00% | 0.00% |
| `option[].option_label` | Product-option label. | string | 96.92% | 0.00% | 0.00% |
| `option[].quality` | Quality selection code. | string | 100.00% | 0.00% | 0.00% |
| `option[].quality_label` | Quality selection label. | string | 87.19% | 0.00% | 0.00% |
| `option[].value_id` | Selected option-value reference. | string | 96.92% | 0.00% | 0.00% |
| `option[].value_label` | Selected option-value label. | string | 96.92% | 0.00% | 0.00% |
| `product_id` | Product reference. | string | 100.00% | 0.00% | 0.00% |

## `view_home_page` — 3,131 records

No additional fields observed in this sample.

## `view_landing_page` — 3,461 records

No additional fields observed in this sample.

## `view_listing_page` — 26,032 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `cat_id` | Unknown; category-like field name needs confirmation. | null, string | 100.00% | 99.9962% | 0.00% |
| `collect_id` | Unknown tracking/collection code. | string | 100.00% | 0.00% | 76.97% |
| `option` | Product-option payload; object/array shape varies by event. | object | 100.00% | 0.00% | 0.00% |
| `option.alloy` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 75.74% |
| `option.diamond` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 69.07% |
| `option.shapediamond` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 96.13% |

## `view_my_account` — 526 records

No additional fields observed in this sample.

## `view_product_detail` — 27,993 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `option` | Product-option payload; object/array shape varies by event. | array | 100.00% | 0.00% | 0.00% |
| `option[]` | One item in the parent array. | object | 100.00% | 0.00% | 0.00% |
| `option[].option_id` | Product-option reference. | string | 100.00% | 0.00% | 33.40% |
| `option[].option_label` | Product-option label. | string | 100.00% | 0.00% | 0.00% |
| `option[].value_id` | Selected option-value reference. | string | 100.00% | 0.00% | 33.42% |
| `option[].value_label` | Selected option-value label. | string | 100.00% | 0.00% | 100.00% |
| `product_id` | Product reference. | string | 100.00% | 0.00% | 0.00% |
| `recommendation` | Recommendation-tracking value; flag semantics unconfirmed. | bool | 100.00% | 0.00% | 0.00% |
| `utm_medium` | Campaign medium; false/string encoding varies. | bool, string | 100.00% | 0.00% | 0.00% |
| `utm_source` | Campaign source; false/string encoding varies. | bool, string | 100.00% | 0.00% | 0.00% |

## `view_shopping_cart` — 920 records

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `cart_products` | Cart-item payload; purchased-item meaning depends on the event. | array | 100.00% | 0.00% | 27.39% |
| `cart_products[]` | One item in the parent array. | object | 72.61% | 0.00% | 0.00% |
| `cart_products[].option` | Product-option payload; object/array shape varies by event. | array, string | 72.61% | 0.00% | 1.96% |
| `cart_products[].option[]` | One item in the parent array. | object | 71.41% | 0.00% | 0.00% |
| `cart_products[].option[].option_id` | Product-option reference. | int32 | 71.41% | 0.00% | 0.00% |
| `cart_products[].option[].option_label` | Product-option label. | string | 71.41% | 0.00% | 0.00% |
| `cart_products[].option[].value_id` | Selected option-value reference. | int32 | 71.41% | 0.00% | 0.00% |
| `cart_products[].option[].value_label` | Selected option-value label. | string | 71.41% | 0.00% | 0.00% |
| `cart_products[].product_id` | Product reference. | int32 | 72.61% | 0.00% | 0.00% |

## `view_sorting_relevance` — 14 records

Small sample: other fields may exist for this event.

| Field | Meaning | BSON types | Present | NULL | Empty |
|---|---|---|---:|---:|---:|
| `option` | Product-option payload; object/array shape varies by event. | object | 100.00% | 0.00% | 0.00% |
| `option.alloy` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 85.71% |
| `option.diamond` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 57.14% |
| `option.shapediamond` | Unknown; obtain a tracking-owner definition. | string | 100.00% | 0.00% | 100.00% |

## `view_static_page` — 4,840 records

No additional fields observed in this sample.

This is a historical snapshot of the local sample. The former profiling command and supporting metrics have been removed.
