"""Provisional event interpretations for the research documents, not policies."""

FAMILIES = {
    "snapshot": {
        "name": "Observed product URL subset",
        "priority": "Explicit product_id → explicit store_id plus current hostname → nonempty, approved current-URL option pairs. The option array validates labels/IDs where possible; it does not fill blanks.",
        "rules": [
            "Recommend retaining only the configuration subset explicitly present in a valid current URL. A missing parameter remains unspecified; an empty query is base-product evidence, not a verified website default.",
            "Require a trusted storefront host and an unambiguous product association. A product-shaped slug is supporting evidence, not existence validation; the user-verified numeric product route avoids inventing SEO slugs.",
            "Keep unknown keys and disagreements for review. Conflicting repeated URL values, malformed encoding/keys, or incompatible identity evidence must not produce a resolved configuration.",
            "Option/value IDs alone cannot supply URL slug values without a product/store-scoped, verified reference. Do not translate labels or use a global ID-to-token dictionary.",
        ],
        "alternative": "Using option/value IDs to fill every missing URL field could increase apparent coverage, but needs a verified reference and may invent implicit defaults. Recommend the explicit URL subset for this phase.",
    },
    "selection": {
        "name": "URL snapshot plus separately observed selection",
        "priority": "Explicit product_id and store/current hostname; compare each selected option_label/value_label with the current URL. Keep the observed URL snapshot and selected delta distinguishable.",
        "rules": [
            "When a selected key/value agrees with the URL, recommend accepting that pair as corroborated. Extra URL options are still an observed subset, not proof of completeness.",
            "When the selected value disagrees, do not choose URL priority or overlay silently. The URL may be the previous state, or the option event may be stale; emission order is not documented.",
            "A selected key absent from the URL is a delta candidate, not permission to manufacture a full resulting configuration. Resolve timing with instrumentation or a validated same-session sequence before any overlay policy.",
            "The user approved preserving both sources for now. A future inferred overlay may be proposed only for a corroborated, unambiguous changed-key transition; preserve the original snapshot/delta and mark the result inferred and partial. See SELECTION_TIMING.md for measured support and counterevidence; no universal overlay is approved.",
            "Preserve original label/value spelling. Localized or unknown labels need an explicit alias reference; multiple different values for one option label remain unresolved.",
        ],
        "alternative": "Overlaying the selected value onto the URL is plausible after a change event, but can attach a future or stale delta to the wrong snapshot. Recommend retaining disagreement as unresolved until approved.",
    },
    "quality": {
        "name": "Product URL subset; quality semantics unresolved",
        "priority": "Explicit product_id and store/current hostname → observed URL option pairs; preserve quality, quality_label, option_label and value IDs as separate evidence.",
        "rules": [
            "Recommend retaining the explicit URL subset while marking the selected quality dimension unresolved. A URL value may describe a stone, while quality/quality_label describe a separate grade.",
            "Do not turn translated labels such as stone/diamonds or stone 2 into diamond/stone2 keys by spelling similarity. Do not append quality as a URL parameter merely because the field exists.",
            "Require product/store/option identity and a verified grade-to-URL representation before encoding quality. If the URL does not represent that dimension, configuration-level crawling may be impossible through URL parameters alone.",
        ],
        "alternative": "A universal quality parameter would be simple, but the sample cannot establish that the website accepts it or that it identifies the selected grade. Recommend holding this dimension for review.",
    },
    "viewed": {
        "name": "Viewed-page candidate, not recommended-target configuration",
        "priority": "viewing_product_id → store_id/current hostname → current URL subset, only after approving that the ID describes that page.",
        "rules": [
            "Recommend considering the viewed page as one product candidate. These events do not establish that a recommended product inherits the viewed product's alloy/stone parameters.",
            "Do not attach current URL options to recommendation_product_id. Treat recommended IDs as separate identity-only leads unless their own page/configuration evidence exists.",
            "A referrer is a previous-page reference, not the target of the recommendation. Product/page association requires corroboration rather than an automatic fallback.",
        ],
        "alternative": "Crawling every recommendation ID with the current page's options could recover more records but mixes different products. Recommend viewed-page evidence and separate unresolved target IDs.",
    },
    "recommendation_route": {
        "name": "Context/target identities require association review",
        "priority": "Explicit IDs with their original field names → store/current hostname → recommendation-route segments as context → any independently corroborated product-page reference.",
        "rules": [
            "The current recommendation-list route can encode /id/, alloy, stone and price in its path. Do not treat the route as a product page or assume every segment is a crawl option.",
            "Recommend preserving identities as unresolved context/target leads. The source product, recommended target and list filters can be different objects.",
            "Referrer URLs may retain a product-page configuration. Permit recovery only if an independent product/store/page association is established and use of referrers is explicitly approved.",
            "Do not merge the option object with path segments: category, collection and price filters are not established product options. A product URL may be recoverable while its configuration remains unknown.",
        ],
        "alternative": "Parsing all route pairs into options is easy but confuses page filters with product settings. Recommend withholding configuration recovery from this route until its semantics are approved.",
    },
    "cart": {
        "name": "Per-item product identities; options need a scoped reference",
        "priority": "Each cart_products[].product_id separately → event store/current hostname → that item's nested option array and IDs. Event-level URL/referrer parameters are not per-item options.",
        "rules": [
            "Recommend including per-item identity evidence. Numeric IDs may be compared with digit-string IDs only through a documented lossless canonicalization proposal; preserve original types in provenance.",
            "Nested value_label values are display labels, sometimes localized, while URL option values are slug tokens. Never translate or concatenate these display labels into crawl URLs.",
            "Array options with IDs can be resolved only by a verified product/store/option/value-ID reference. An empty string, empty array or absent value means unspecified, not a known website default.",
            "A multi-item cart has one current/referrer URL. Do not apply that URL's configuration to every item or infer that the referrer belongs to an arbitrary cart product.",
        ],
        "alternative": "Ignoring carts loses transaction-related product evidence; guessing slugs from labels creates false configurations. Recommend identity evidence now and option recovery only where a scoped reference is verified.",
    },
    "target_identity": {
        "name": "Recommended product identity only",
        "priority": "Nonempty recommendation_product_id → event store/current storefront → a separate product lookup using the user-verified ID route. No current-page configuration is transferred.",
        "rules": [
            "Recommend keeping a valid recommended target ID as an identity-only lead, pending approval that the field denotes the clicked target.",
            "Landing/listing options describe the page context. They do not identify the target product's selected settings; mark target options unknown.",
            "Null or blank recommended IDs are not recoverable through this rule. A referrer can describe another product and must not fill the target identity by assumption.",
        ],
        "alternative": "Discarding all such events reduces product-identity coverage; assigning page filters as target options corrupts configuration coverage. Recommend identity-only leads, not resolved configurations.",
    },
    "url_only": {
        "name": "URL lead without a verified product ID",
        "priority": "Valid current HTTP(S) storefront URL → independently verified product/page mapping. Store is explicit store_id plus observed current hostname.",
        "rules": [
            "Recommend retaining a product-shaped current URL only as an unresolved lead. A slug and query can identify a page candidate but do not supply the required product_id.",
            "A future approved cross-event join may associate an exact storefront/path with a product ID if mappings are consistent. Do not infer IDs from arbitrary slug digits.",
            "Do not use a previous referrer product as the identity of the current page. Invalid, file, external and development URLs need their own review state.",
        ],
        "alternative": "URL-only crawling could discover an ID later, but that would be a separately approved crawler task. Recommend review leads and no product/configuration tuple yet.",
    },
    "context": {
        "name": "Browsing/filter context, no configuration tuple",
        "priority": "Inspect current URL and explicit fields; absent product identity cannot be replaced by a page filter or previous referrer.",
        "rules": [
            "Recommend excluding the observed page/filter state from configuration tuples while retaining aggregate evidence. There is no established product owner for the filter values.",
            "An option object containing alloy/diamond/shape on a category page is filter context, not proof of one product configuration. A queryless URL does not establish a default product configuration.",
            "If an exceptional current URL has independently verified product-page evidence, it can be reconsidered as an unresolved URL lead; event names alone should not override the record.",
            "Referrer product references remain previous-page evidence. Their use would require reopening the earlier current_url-only scope and verifying association.",
        ],
        "alternative": "Recovering product URLs from navigation referrers may add leads, but can attach a previous product to unrelated page state. Recommend no configuration tuple from the page context itself.",
    },
}

# Purpose wording is intentionally an interpretation unless structural evidence
# can prove it. Every file also contains the measured schema and counterexamples.
EVENTS = {
    "view_product_detail": ("snapshot", "Product-page observation with product_id and option metadata.", "Should this be the primary URL-subset source, leaving empty value labels/IDs as validation evidence rather than filling defaults?"),
    "add_to_cart_action": ("snapshot", "An add-to-cart action carrying a product identity and page URL.", "Approve URL-subset evidence when option value labels are blank, and retain non-product current URLs or contradictions for review?"),
    "select_product_option": ("selection", "A selection action whose option array may describe one changed dimension.", "Preserving snapshot and delta is approved. After reviewing the quantified timing study, are its conditional inferred-overlay criteria sufficient, or is stronger session/instrumentation verification required before any implementation?"),
    "select_product_option_quality": ("quality", "A selection action with additional quality/quality_label fields.", "Keep quality unresolved until its option/URL representation is verified (recommended), or approve a specific product-scoped mapping to investigate?"),
    "product_detail_recommendation_visible": ("viewed", "Recommendation visibility alongside a viewing_product_id.", "Approve the viewed page as a product/configuration candidate without treating visible recommendations as the same product?"),
    "product_detail_recommendation_noticed": ("viewed", "Recommendation attention alongside a viewing_product_id.", "Approve the viewed-page URL subset only, keeping recommendation attention as context?"),
    "product_detail_recommendation_clicked": ("viewed", "A click with both viewing_product_id and recommendation_product_id.", "Approve separate viewed-page candidates and identity-only recommended targets, with no configuration transfer between them?"),
    "product_view_all_recommend_clicked": ("recommendation_route", "A recommendation-list interaction with viewed and recommended identities.", "Which ID denotes the crawl target, and what independent product/store evidence is sufficient before considering a previous product URL? Conditional corroboration is already required."),
    "view_all_recommend": ("recommendation_route", "Recommendation-list context with product_id and a broad option/filter object.", "Should product_id be retained as context-only until /id/ and filter semantics are verified, rather than interpreting the entire option object as product settings?"),
    "back_to_product_action": ("recommendation_route", "A rare action with product_id, a recommendation-list URL and a previous page reference.", "Keep this low-sample event unresolved (recommended), or approve an expanded targeted investigation before deciding its ID/referrer association?"),
    "view_shopping_cart": ("cart", "A cart snapshot containing zero or more separately identified products.", "Include per-item identities, and recover option slugs only through verified product/store/option/value-ID references?"),
    "checkout": ("cart", "A checkout snapshot containing per-item product identities and options.", "Approve per-item evidence while forbidding the event-level URL/referrer from supplying every item's options?"),
    "checkout_success": ("cart", "A success-page event with nested purchased-item identities and options.", "Include purchased-item identity evidence, retaining localized labels and unresolved ID-to-slug mappings rather than translating them?"),
    "landing_page_recommendation_clicked": ("target_identity", "A recommended target ID attached to a landing-page click context.", "Approve nonempty recommendation IDs as identity-only leads, with target configuration unknown?"),
    "sorting_relevance_click_action": ("target_identity", "A recommendation target ID/position attached to sorting/listing context.", "Approve target IDs only after validating their meaning, without inheriting category filters as target options?"),
    "listing_page_recommendation_clicked": ("target_identity", "A listing recommendation click; the target ID can be explicitly null.", "Hold null-target events unresolved; if a nonempty target ID is observed, consider it identity-only rather than using listing filters?"),
    "search_box_action": ("url_only", "Search interaction on varying page contexts, sometimes a product-shaped URL.", "Keep product-shaped current URLs as review leads needing a verified product ID, rather than inventing IDs from slugs?"),
    "view_static_page": ("url_only", "Broad static/search context with occasional product-shaped paths.", "Allow independently confirmed product-path leads for review, or exclude this event entirely from future recovery?"),
    "view_listing_page": ("context", "Category/listing context with an option object of filters.", "Approve treating listing option objects as filters only, with no product configuration tuple absent independent product evidence?"),
    "listing_page_recommendation_visible": ("context", "Recommendation visibility on a listing page with filter context.", "Approve excluding the listing filter state from product configurations unless an exceptional record has independent product evidence?"),
    "listing_page_recommendation_noticed": ("context", "Recommendation attention on a listing page with filter context.", "Approve keeping page filters separate from product configurations?"),
    "landing_page_recommendation_visible": ("context", "Recommendation visibility on a landing page without a direct product owner.", "Approve no configuration tuple from this page context; reconsider only independently verified exceptional product records?"),
    "landing_page_recommendation_noticed": ("context", "Recommendation attention on a landing page without a direct product owner.", "Approve no configuration tuple from this context rather than assigning a previous referrer product?"),
    "view_home_page": ("context", "Homepage context; previous-page references can mention products.", "Approve excluding homepage state from product configurations under the current_url-only scope?"),
    "view_landing_page": ("context", "Landing-page context with no established product identity.", "Approve excluding landing-page state while allowing only independently proven exceptional product records to be reviewed?"),
    "view_my_account": ("context", "Account-page context; product-shaped suffixes can be false positives.", "Approve excluding account state and rejecting file/external URLs even when their paths end in .html?"),
    "view_sorting_relevance": ("context", "Sorting/listing context with an option object of filters.", "Approve treating option fields as listing filters and leaving any recommended product configuration unknown?"),
}
