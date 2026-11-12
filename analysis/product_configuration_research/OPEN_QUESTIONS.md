# Decisions requiring review

The user confirmed three research constraints on 6 November 2026: preserve URL snapshot and selected delta separately; keep unmapped options partial; consider referrers only with independent product/store corroboration. Event-specific recovery handlers and any inferred overlay still require review. No extraction rule has been implemented.

1. **Selection timing — preservation approved:** keep URL snapshots and selected deltas distinct. The requested [timing investigation](SELECTION_TIMING.md) quantifies supportive, counterevidence and inconclusive sequences. Review the conditional inferred-overlay proposal; no universal overlay is approved.
2. **Quality representation:** keep quality unresolved until a product-scoped mapping proves how quality/quality_label relate to URL options (recommended). Matching stone text alone does not identify a grade.
3. **Viewed versus recommended products:** use current-page options only for a corroborated viewed product; recommended IDs remain separate identity-only leads (recommended). Never copy the viewed product's options to a recommendation target.
4. **Cart labels and IDs — partial state approved:** keep unmapped options partial. Per-item source inclusion, a trusted catalog reference, and numeric/string canonicalization need separate review. Do not translate localized labels into URL tokens or treat the ambiguous sample reference as authoritative.
5. **Referrers — corroboration constraint approved:** future recovery may be considered only with independent product/store corroboration; never an unconditional fallback. Matching context alone does not resolve conflicting option state.
6. **Unknown query keys, route segments and storefronts:** known campaign keys have no configuration role; unknown keys, category/price filters and nonproduction hosts stay unresolved until classified. Candidate option names in these measurements are not an approved allowlist.
7. **Unspecified options:** preserve an observed subset and absence of values; do not infer website defaults or label a partial subset complete. Missing product identity or an unrepresentable quality dimension can make configuration recovery impossible.

## Event-specific review

- **[add_to_cart_action](collections/add_to_cart_action.md):** Approve URL-subset evidence when option value labels are blank, and retain non-product current URLs or contradictions for review?

- **[back_to_product_action](collections/back_to_product_action.md):** Keep this low-sample event unresolved (recommended), or approve an expanded targeted investigation before deciding its ID/referrer association?

- **[checkout](collections/checkout.md):** Approve per-item evidence while forbidding the event-level URL/referrer from supplying every item's options?

- **[checkout_success](collections/checkout_success.md):** Include purchased-item identity evidence, retaining localized labels and unresolved ID-to-slug mappings rather than translating them?

- **[landing_page_recommendation_clicked](collections/landing_page_recommendation_clicked.md):** Approve nonempty recommendation IDs as identity-only leads, with target configuration unknown?

- **[landing_page_recommendation_noticed](collections/landing_page_recommendation_noticed.md):** Approve no configuration tuple from this context rather than assigning a previous referrer product?

- **[landing_page_recommendation_visible](collections/landing_page_recommendation_visible.md):** Approve no configuration tuple from this page context; reconsider only independently verified exceptional product records?

- **[listing_page_recommendation_clicked](collections/listing_page_recommendation_clicked.md):** Hold null-target events unresolved; if a nonempty target ID is observed, consider it identity-only rather than using listing filters?

- **[listing_page_recommendation_noticed](collections/listing_page_recommendation_noticed.md):** Approve keeping page filters separate from product configurations?

- **[listing_page_recommendation_visible](collections/listing_page_recommendation_visible.md):** Approve excluding the listing filter state from product configurations unless an exceptional record has independent product evidence?

- **[product_detail_recommendation_clicked](collections/product_detail_recommendation_clicked.md):** Approve separate viewed-page candidates and identity-only recommended targets, with no configuration transfer between them?

- **[product_detail_recommendation_noticed](collections/product_detail_recommendation_noticed.md):** Approve the viewed-page URL subset only, keeping recommendation attention as context?

- **[product_detail_recommendation_visible](collections/product_detail_recommendation_visible.md):** Approve the viewed page as a product/configuration candidate without treating visible recommendations as the same product?

- **[product_view_all_recommend_clicked](collections/product_view_all_recommend_clicked.md):** Which ID denotes the crawl target, and what independent product/store evidence is sufficient before considering a previous product URL? Conditional corroboration is already required.

- **[search_box_action](collections/search_box_action.md):** Keep product-shaped current URLs as review leads needing a verified product ID, rather than inventing IDs from slugs?

- **[select_product_option](collections/select_product_option.md):** Preserving snapshot and delta is approved. After reviewing the quantified timing study, are its conditional inferred-overlay criteria sufficient, or is stronger session/instrumentation verification required before any implementation?

- **[select_product_option_quality](collections/select_product_option_quality.md):** Keep quality unresolved until its option/URL representation is verified (recommended), or approve a specific product-scoped mapping to investigate?

- **[sorting_relevance_click_action](collections/sorting_relevance_click_action.md):** Approve target IDs only after validating their meaning, without inheriting category filters as target options?

- **[view_all_recommend](collections/view_all_recommend.md):** Should product_id be retained as context-only until /id/ and filter semantics are verified, rather than interpreting the entire option object as product settings?

- **[view_home_page](collections/view_home_page.md):** Approve excluding homepage state from product configurations under the current_url-only scope?

- **[view_landing_page](collections/view_landing_page.md):** Approve excluding landing-page state while allowing only independently proven exceptional product records to be reviewed?

- **[view_listing_page](collections/view_listing_page.md):** Approve treating listing option objects as filters only, with no product configuration tuple absent independent product evidence?

- **[view_my_account](collections/view_my_account.md):** Approve excluding account state and rejecting file/external URLs even when their paths end in .html?

- **[view_product_detail](collections/view_product_detail.md):** Should this be the primary URL-subset source, leaving empty value labels/IDs as validation evidence rather than filling defaults?

- **[view_shopping_cart](collections/view_shopping_cart.md):** Include per-item identities, and recover option slugs only through verified product/store/option/value-ID references?

- **[view_sorting_relevance](collections/view_sorting_relevance.md):** Approve treating option fields as listing filters and leaving any recommended product configuration unknown?

- **[view_static_page](collections/view_static_page.md):** Allow independently confirmed product-path leads for review, or exclude this event entirely from future recovery?
