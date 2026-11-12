# Event comparison

All strategies are proposals. Counts are from the shared random pool, not full-population event totals. Product-shaped paths are heuristics restricted to sampled merchant hosts. Referrer percentages are previous-page references, not target-product confirmations. Explicit null IDs remain listed as fields but are unusable identities.

| Event | Sample n | Identifier fields | Current product-shaped | Referrer product-shaped | Proposed recovery class | Unresolved issue |
| --- | --- | --- | --- | --- | --- | --- |
| [add_to_cart_action](collections/add_to_cart_action.md) | 1,355 | product_id | 1,208 (89.15%) | 313 (23.10%) | Observed product URL subset | unspecified/default settings; blank internal labels |
| [back_to_product_action](collections/back_to_product_action.md) | 2 | product_id | 0 (0.00%) | 2 (100.00%) | Context/target identities require association review | route filters versus product state; referrer disagreement; LOW n |
| [checkout](collections/checkout.md) | 636 | cart_products[].product_id | 0 (0.00%) | 31 (4.87%) | Per-item product identities; options need a scoped reference | localized labels; ID-reference ambiguity |
| [checkout_success](collections/checkout_success.md) | 178 | cart_products[].product_id | 0 (0.00%) | 0 (0.00%) | Per-item product identities; options need a scoped reference | localized labels; ID-reference ambiguity |
| [landing_page_recommendation_clicked](collections/landing_page_recommendation_clicked.md) | 144 | recommendation_product_id | 0 (0.00%) | 28 (19.44%) | Recommended product identity only | target identity; no target options |
| [landing_page_recommendation_noticed](collections/landing_page_recommendation_noticed.md) | 393 | none observed | 0 (0.00%) | 58 (14.76%) | Browsing/filter context, no configuration tuple | filter/page context has no product owner |
| [landing_page_recommendation_visible](collections/landing_page_recommendation_visible.md) | 2,332 | none observed | 0 (0.00%) | 260 (11.15%) | Browsing/filter context, no configuration tuple | filter/page context has no product owner |
| [listing_page_recommendation_clicked](collections/listing_page_recommendation_clicked.md) | 184 | recommendation_product_id | 0 (0.00%) | 11 (5.98%) | Recommended product identity only | target identity; no target options |
| [listing_page_recommendation_noticed](collections/listing_page_recommendation_noticed.md) | 280 | none observed | 0 (0.00%) | 22 (7.86%) | Browsing/filter context, no configuration tuple | filter/page context has no product owner |
| [listing_page_recommendation_visible](collections/listing_page_recommendation_visible.md) | 5,127 | none observed | 0 (0.00%) | 297 (5.79%) | Browsing/filter context, no configuration tuple | filter/page context has no product owner |
| [product_detail_recommendation_clicked](collections/product_detail_recommendation_clicked.md) | 1,313 | viewing_product_id, recommendation_product_id | 1,300 (99.01%) | 426 (32.44%) | Viewed-page candidate, not recommended-target configuration | viewed versus recommendation owner |
| [product_detail_recommendation_noticed](collections/product_detail_recommendation_noticed.md) | 3,648 | viewing_product_id | 3,578 (98.08%) | 846 (23.19%) | Viewed-page candidate, not recommended-target configuration | viewed versus recommendation owner |
| [product_detail_recommendation_visible](collections/product_detail_recommendation_visible.md) | 9,302 | viewing_product_id | 9,159 (98.46%) | 1,778 (19.11%) | Viewed-page candidate, not recommended-target configuration | viewed versus recommendation owner |
| [product_view_all_recommend_clicked](collections/product_view_all_recommend_clicked.md) | 119 | viewing_product_id, recommendation_product_id | 0 (0.00%) | 114 (95.80%) | Context/target identities require association review | route filters versus product state; referrer disagreement |
| [search_box_action](collections/search_box_action.md) | 1,742 | none observed | 277 (15.90%) | 180 (10.33%) | URL lead without a verified product ID | missing product ID |
| [select_product_option](collections/select_product_option.md) | 63,716 | product_id | 63,045 (98.95%) | 8,644 (13.57%) | URL snapshot plus separately observed selection | snapshot/delta timing and conflicts |
| [select_product_option_quality](collections/select_product_option_quality.md) | 16,210 | product_id | 16,005 (98.74%) | 2,954 (18.22%) | Product URL subset; quality semantics unresolved | grade not established in URL |
| [sorting_relevance_click_action](collections/sorting_relevance_click_action.md) | 15 | recommendation_product_id | 0 (0.00%) | 0 (0.00%) | Recommended product identity only | target identity; no target options; LOW n |
| [view_all_recommend](collections/view_all_recommend.md) | 259 | product_id | 0 (0.00%) | 242 (93.44%) | Context/target identities require association review | route filters versus product state; referrer disagreement |
| [view_home_page](collections/view_home_page.md) | 7,573 | none observed | 0 (0.00%) | 266 (3.51%) | Browsing/filter context, no configuration tuple | filter/page context has no product owner |
| [view_landing_page](collections/view_landing_page.md) | 10,214 | none observed | 0 (0.00%) | 1,209 (11.84%) | Browsing/filter context, no configuration tuple | filter/page context has no product owner |
| [view_listing_page](collections/view_listing_page.md) | 81,642 | none observed | 0 (0.00%) | 2,871 (3.52%) | Browsing/filter context, no configuration tuple | filter/page context has no product owner |
| [view_my_account](collections/view_my_account.md) | 831 | none observed | 0 (0.00%) | 47 (5.66%) | Browsing/filter context, no configuration tuple | filter/page context has no product owner |
| [view_product_detail](collections/view_product_detail.md) | 79,822 | product_id | 79,259 (99.29%) | 8,029 (10.06%) | Observed product URL subset | unspecified/default settings; blank internal labels |
| [view_shopping_cart](collections/view_shopping_cart.md) | 2,425 | cart_products[].product_id | 0 (0.00%) | 569 (23.46%) | Per-item product identities; options need a scoped reference | localized labels; ID-reference ambiguity |
| [view_sorting_relevance](collections/view_sorting_relevance.md) | 105 | none observed | 0 (0.00%) | 0 (0.00%) | Browsing/filter context, no configuration tuple | filter/page context has no product owner |
| [view_static_page](collections/view_static_page.md) | 10,433 | none observed | 22 (0.21%) | 1,118 (10.72%) | URL lead without a verified product ID | missing product ID |

No class means fully resolved website options. See each event's schema, counterexamples, source priority, reference needs and user question before selecting a rule.
