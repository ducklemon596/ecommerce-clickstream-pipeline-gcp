# Scope Confirmation - Glamira Pipeline

The project will enrich location and product information and target the full dataset to support geographic performance, product and category performance, and time-trend analysis.

## Location enrichment

Derive country and region from event IP addresses to support geographic analysis. All 100,000 sampled records contain a syntactically valid IPv4 address, providing a practical starting point for IP geolocation. Use a licensed or otherwise permitted lookup source, measure coverage, and retain unknown locations when a lookup fails. IP syntax alone does not guarantee accurate location. See the [IP assessment](data_quality/ip_addresses.md).

## Product enrichment

Build product details from product identifiers and relevant web URLs to support analysis by product name and category. The 27,993 sampled `view_product_detail` events contain `product_id`, but no `product_name` was observed in those events. Validate a small crawl before scaling, respect website access rules, and record missing or failed matches. Product attributes therefore have to come from an external source.

## Data volume

Target the full restored MongoDB collection, previously reported at **41,432,473 documents**, for complete analysis. Use the 100,000-event sequential sample to develop and test the enrichment workflows; it is not representative of the full dataset. Verify source parity and event coverage before treating full-load results as complete.

## Conclusion

IP geolocation and product-detail enrichment can provide the missing dimensions needed for the requested insights. Confirm revenue and currency definitions before calculating geographic or product revenue, and measure enrichment coverage to make the limits of the results clear.
