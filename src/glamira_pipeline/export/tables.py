"""The raw-layer data contract: one declaration per exported table.

Types and modes follow the full-data profiles (41,432,473 events on
2026-11-14; enrichment collections on 2026-11-17). Rules are explained in
``docs/raw_layer_contract.md``; the reasoning is in
``docs/decisions/raw_events_schema.md``.
"""
from __future__ import annotations

from glamira_pipeline.export.schema import (BOOL, INT64, NUMERIC, REPEATED, REQUIRED, STRING,
                                            TIMESTAMP, Field, Record, Table)

# --- events (countly.summary) ---------------------------------------------------------------

OPTION_ITEM = Record("OptionItem", (
    Field("option_label", STRING, description="Option name, e.g. alloy, diamond, stone/diamonds"),
    Field("option_id", STRING, description="Product option ID; joins product_option_values.option_id"),
    Field("value_label", STRING, description="Selected value label"),
    Field("value_id", STRING, description="Selected value ID; joins product_option_values.value_id"),
    Field("quality", STRING, description="Stone quality code (select_product_option_quality only)"),
    Field("quality_label", STRING, description="Stone quality label (select_product_option_quality only)"),
))

OPTION_FILTER = Record("OptionFilter", (
    Field("alloy", STRING, description="Metal filter"),
    Field("diamond", STRING, description="Stone filter"),
    Field("shapediamond", STRING, description="Stone shape filter"),
    Field("stone", STRING, description="Stone filter (view_all_recommend)"),
    Field("price", STRING, description="Price filter (view_all_recommend)"),
    Field("finish", STRING, description="Finish filter (view_all_recommend)"),
    Field("pearlcolor", STRING, description="Pearl colour filter (view_all_recommend)"),
    Field("kollektion", STRING, source="Kollektion", description="Collection filter; source key 'Kollektion'"),
    Field("kollektion_id", STRING, description="Collection ID filter (view_all_recommend)"),
    Field("category_id", STRING, source="category id", description="Category filter; source key 'category id'"),
))

CART_OPTION = Record("CartOption", (
    Field("option_id", STRING, rule="integer_as_string", description="Option ID; int in the source"),
    Field("option_label", STRING, description="Option name"),
    Field("value_id", STRING, rule="integer_as_string", description="Value ID; int in the source"),
    Field("value_label", STRING, description="Selected value label"),
))

CART_PRODUCT = Record("CartProduct", (
    Field("product_id", STRING, rule="integer_as_string", description="Product ID; int in the source"),
    Field("amount", INT64, description="Quantity (checkout, checkout_success); -1 to 9,999 observed"),
    Field("price", STRING, description="Locale-formatted unit price (checkout_success), e.g. '55,00'"),
    Field("currency", STRING, description="Currency symbol (checkout_success), e.g. '€'"),
    Field("option", CART_OPTION, REPEATED, rule="empty_string_as_empty_array",
          description="Chosen options; the source string '' becomes an empty array"),
))

EVENTS = Table(
    name="events",
    record_name="Event",
    source_collection="summary",
    description="One row per tracking event (27 event types) from countly.summary.",
    fields=(
        Field("_id", STRING, REQUIRED, rule="objectid_hex", description="Event ID: source ObjectId as 24 hex chars"),
        Field("collection", STRING, REQUIRED, description="Event type, e.g. view_product_detail"),
        Field("time_stamp", TIMESTAMP, REQUIRED, rule="unix_seconds",
              description="Event time (UTC) from Unix seconds"),
        Field("api_version", STRING, REQUIRED, description="Tracker API version"),
        Field("store_id", STRING, REQUIRED, description="Glamira store ID (digits)"),
        Field("current_url", STRING, REQUIRED, description="Page URL"),
        Field("referrer_url", STRING, REQUIRED, description="Referrer URL; '' for direct entries"),
        Field("ip_hash", STRING, REQUIRED, source="ip", rule="hmac_ip",
              description="HMAC-SHA256 of the normalized client IP; joins ip_locations.ip_hash"),
        Field("device_id_hash", STRING, REQUIRED, source="device_id", rule="hmac",
              description="HMAC-SHA256 of the device ID"),
        Field("user_id_hash", STRING, REQUIRED, source="user_id_db", rule="hmac",
              description="HMAC-SHA256 of the customer ID; '' for anonymous visits (95.19%)"),
        Field("user_agent", STRING, REQUIRED, description="Browser user agent"),
        Field("local_time", STRING, description="Client local time as sent, e.g. '2020-05-20 3:6:40'"),
        Field("resolution", STRING, description="Screen resolution as sent"),
        Field("email_hash", STRING, source="email_address", rule="hmac_email",
              description="HMAC-SHA256 of the trimmed, lower-cased email; '' when not given"),
        Field("show_recommendation", STRING, description="'true'/'false' as sent; a few malformed values"),
        Field("product_id", STRING, description="Product of a product event"),
        Field("viewing_product_id", STRING, description="Product page on which a recommendation was shown"),
        Field("recommendation_product_id", STRING, description="Recommended product"),
        Field("recommendation_clicked_position", INT64, description="Clicked slot (always 0 observed)"),
        Field("recommendation_product_position", STRING, rule="integer_as_string",
              description="Slot of the recommended product; int or string in the source"),
        Field("recommendation", BOOL, description="Recommendation flag (only false observed)"),
        Field("utm_source", STRING, rule="bool_as_string", description="Campaign source; source false becomes 'false'"),
        Field("utm_medium", STRING, rule="bool_as_string", description="Campaign medium; source false becomes 'false'"),
        Field("cat_id", STRING, description="Category ID of a listing page"),
        Field("collect_id", STRING, description="Collection ID of a listing page"),
        Field("key_search", STRING, description="Search text (search_box_action)"),
        Field("price", STRING, description="Locale-formatted price (add_to_cart_action)"),
        Field("currency", STRING, description="Currency symbol (add_to_cart_action)"),
        Field("is_paypal", BOOL, description="PayPal express checkout (only true observed)"),
        Field("order_id", STRING, rule="integer_as_string",
              description="Order number (checkout_success); '' in checkout"),
        Field("option", OPTION_ITEM, REPEATED, rule="array_form",
              description="Chosen product options: the array form of the source 'option'"),
        Field("option_filter", OPTION_FILTER, source="option", rule="object_form",
              description="Listing filter state: the object form of the source 'option'"),
        Field("cart_products", CART_PRODUCT, REPEATED, description="Cart lines (cart and checkout events)"),
    ),
)

# --- ip_locations ---------------------------------------------------------------------------

IP_LOCATIONS = Table(
    name="ip_locations",
    record_name="IpLocation",
    source_collection="ip_locations",
    description="Offline IP2Location lookup of every distinct valid event IP.",
    sensitive_key=True,
    fields=(
        Field("ip_hash", STRING, REQUIRED, source="_id", rule="hmac_ip",
              description="HMAC-SHA256 of the normalized IP; joins events.ip_hash"),
        Field("ip_version", INT64, REQUIRED, description="4 or 6"),
        Field("status", STRING, REQUIRED,
              description="resolved, no_match, not_public, unsupported_ipv6 or lookup_failed"),
        Field("country_code", STRING, description="ISO 3166-1 alpha-2; null unless resolved"),
        Field("country_name", STRING, description="Country name; null unless resolved"),
        Field("region", STRING, description="Region; null when unknown"),
        Field("city", STRING, description="City; null when unknown"),
        Field("database_id", STRING, REQUIRED, description="SHA-256 of the IP2Location BIN used"),
    ),
)

# --- products and product_option_values -----------------------------------------------------

PRODUCT_SOURCE = Record("ProductSource", (
    Field("host", STRING, REQUIRED, description="Storefront host that answered"),
    Field("store_code", STRING, REQUIRED, description="Storefront code"),
    Field("url", STRING, REQUIRED, description="Requested react_data URL"),
    Field("requested_currency", STRING, REQUIRED, description="Currency requested"),
))

PRODUCTS = Table(
    name="products",
    record_name="Product",
    source_collection="products",
    description="Product attributes crawled from Glamira react_data (2026 catalog), one row per event product ID.",
    redundant_id=("product_id",),
    fields=(
        Field("product_id", STRING, REQUIRED, description="Product ID, same form as events.product_id"),
        Field("status", STRING, REQUIRED, description="success, not_found, error or blocked"),
        Field("status_code", INT64, description="HTTP status; null on a network error"),
        Field("attempts", INT64, REQUIRED, description="Crawl attempts"),
        Field("error", STRING, description="Error message of a failed attempt"),
        Field("name", STRING, description="Product name"),
        Field("sku", STRING, description="SKU"),
        Field("attribute_set_id", STRING, rule="integer_as_string", description="Attribute set ID"),
        Field("attribute_set", STRING, description="Attribute set name"),
        Field("type_id", STRING, description="simple, product_set, virtual or deposit"),
        Field("product_type", STRING, description="ring, wedding_ring, pendant, ..."),
        Field("product_type_value", STRING, description="Product type code"),
        Field("collection", STRING, description="Collection name"),
        Field("collection_id", STRING, description="Collection ID"),
        Field("category", STRING, rule="integer_as_string", description="Category ID; usually '0'"),
        Field("category_name", STRING, description="Category name"),
        Field("gender", STRING, rule="bool_as_string",
              description="women, men, or 'false' when the site sends false"),
        Field("price", NUMERIC, description="Price in currency, tax included"),
        Field("min_price", NUMERIC, description="Lowest configurable price"),
        Field("max_price", NUMERIC, description="Highest configurable price"),
        Field("min_price_format", STRING, description="Formatted lowest price"),
        Field("max_price_format", STRING, description="Formatted highest price"),
        Field("full_price", NUMERIC, description="List price"),
        Field("sale_price", NUMERIC, description="Sale price"),
        Field("full_price_format", STRING, description="Formatted list price"),
        Field("sale_price_format", STRING, description="Formatted sale price"),
        Field("currency", STRING, description="ISO currency code, e.g. USD"),
        Field("include_tax", BOOL, description="Whether prices include tax"),
        Field("default_tax", NUMERIC, rule="number_as_decimal", description="Default tax rate"),
        Field("current_tax", NUMERIC, rule="number_as_decimal", description="Current tax rate"),
        Field("use_gold_price", BOOL, description="Price follows the gold price"),
        Field("option_count", INT64, description="Number of configurable options"),
        Field("source", PRODUCT_SOURCE, REQUIRED, description="Storefront request that produced the row"),
        Field("run_id", STRING, REQUIRED, description="Crawl run ID (enrichment_runs)"),
        Field("crawled_at", TIMESTAMP, REQUIRED, description="Crawl time (UTC)"),
    ),
)

PRODUCT_OPTION_VALUES = Table(
    name="product_option_values",
    record_name="ProductOptionValue",
    source_collection="product_option_values",
    description="One row per (product, option, value) served by react_data: resolves event option/value IDs.",
    redundant_id=("product_id", "option_id", "value_id"),
    fields=(
        Field("product_id", STRING, REQUIRED, description="Product ID"),
        Field("option_id", STRING, REQUIRED, description="Option ID; joins events option[].option_id"),
        Field("value_id", STRING, description="Value ID; null for free-text options such as engraving"),
        Field("part_type", STRING, description="Part, e.g. stone1, alloy"),
        Field("option_type", STRING, description="alloy, stone, engraving_font, ..."),
        Field("option_title", STRING, description="Option title in the store language"),
        Field("option_default_title", STRING, description="Option default title"),
        Field("is_require", BOOL, rule="int_as_bool", description="Option is mandatory; source 0/1"),
        Field("sort_order", STRING, rule="integer_as_string", description="Display order as served"),
        Field("value_sku", STRING, description="Value token used in product URLs"),
        Field("value_title", STRING, description="Value title"),
        Field("value_default_title", STRING, description="Value default title"),
        Field("value_store_title", STRING, description="Value title in the store"),
        Field("is_default", BOOL, rule="int_as_bool", description="Default value; source bool or 0"),
        Field("value_price", NUMERIC, description="Price surcharge of the value"),
        Field("price_type", STRING, description="fixed, percent or abs"),
        Field("run_id", STRING, REQUIRED, description="Crawl run ID"),
        Field("crawled_at", TIMESTAMP, REQUIRED, description="Crawl time (UTC)"),
    ),
)

TABLES: dict[str, Table] = {t.name: t for t in (EVENTS, IP_LOCATIONS, PRODUCTS, PRODUCT_OPTION_VALUES)}
