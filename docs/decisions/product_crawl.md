# Product enrichment by crawling `react_data`

**Status:** accepted and executed, 2026-11-13.
**Scope:** how product attributes (name, type, collection, gender, prices, options) are obtained for the 19,557 product IDs referenced in `countly.summary`.

The events carry `product_id` but no product name or category (see the [scope confirmation](../reports/scope_confirmation.md)). Those attributes have to come from the live Glamira website. The site sits behind Akamai Bot Manager, so every decision below balances completeness against crawling politely and honestly.

## 1. Data source: the `react_data` JSON endpoint

**Options considered**

| Option | Finding |
| --- | --- |
| Product HTML pages (JSON-LD, GTM `dataLayer`, Open Graph) | Rich, server-rendered data. A plain HTTP client received `403 Access Denied` from Akamai on the first attempts. Names and categories are localized per domain |
| Selenium (unmodified Chrome, honest `navigator.webdriver = true`) | Headless was denied immediately. Headed sessions were disconnected (`ERR_HTTP2_PROTOCOL_ERROR`) after 2–4 pages, whether the pause was 10 s, 45 s or a random 6–20 s. Slowing down did not help, which points to session classification rather than rate limiting |
| Public archives (Common Crawl) | Coverage of a specific 2019 catalog is not guaranteed, and the pages would still need HTML parsing |
| `/productcustomizer/reactdata/index/id/{id}/` | Explicitly allowed by robots.txt (`Allow: /productcustomizer/reactdata/`). Returned JSON to plain `curl` for 9/9 sampled IDs, including one that Selenium had just been disconnected on. A missing product is a distinct `404 {"error":"Product not found"}` |

**Decision.** Use `react_data` with Python's standard-library HTTP client and an honest User-Agent (`glamira-pipeline/0.1`). Do not use a browser.

**Consequences**
- No browser is involved, so there is nothing to disguise.
- Responses are about 834 KB uncompressed (mostly the option matrix). With `Accept-Encoding: gzip` they shrink to roughly 10–25 KB per request; the full crawl transferred 188 MB.
- The endpoint takes no option parameters, so every field is invariant to the product configuration by construction.
- `category` and `category_name` are almost always empty (`0`/`""`; 2 of 198 sampled products had a value). The language-neutral `product_type` (`ring`, `wedding_ring`, `earring`, …) is the practical category for analysis. On the HTML side, the GTM category was also null for 2 of 10 products.

## 2. Stores: one English storefront per product, with fallback

**Evidence.**
- All 11 English-language storefronts served `react_data` with English names.
- The `?currency=` parameter does not change a host's currency, and prices differ per store beyond currency conversion. For example, product 100002 is 901 USD on `.com` and 968 USD on `.africa`.

**Decision**
- Request each product from the first store in a fixed priority list, ordered by currency popularity: USD (`.com`, `.africa`) → EUR (`.ie`, `.com.mt`) → GBP (`.co.uk`) → AUD, CAD, SGD, NZD, ZAR, AED.
- Fall back to the next store only on `404 Product not found`.
- Store the host, store code and requested currency with every record, because a price is only meaningful together with its store.
- By default, try 3 stores.

**Validation of the default.**
- In the full crawl, every product that was found was found on `www.glamira.com`.
- The 436 IDs that were `not_found` on all 3 default stores were rechecked on all 11 stores: 4,796 requests, every one a 404.
- So a deeper fallback would not have added a single product. `--max-stores 11` together with `--recheck-not-found` remains available.

## 3. What is stored

| Decision | Reason |
| --- | --- |
| Do not store raw JSON by default; `--raw-dir` saves gzip files when needed | The raw payload is about 834 KB per product, mostly option combinations that are not needed for analysis |
| Store every price field: `price`, `min_price`, `max_price`, `full_price`, `sale_price` as `Decimal128`, plus formatted strings, tax flags and currency | The meaning of each price is not documented, so keep all of them. Exact decimals load into BigQuery `NUMERIC` without float error |
| Store the option table as reference rows only (`product_id`, `option_id`, `value_id` → titles, SKU, price) | Lets the `option` IDs seen in events be decoded later. Combinations are not crawled |
| Keep values as served: `gender: false` stays `false`; `null` only when the site sends null or the key is missing | `false` is mostly wedding rings, not "unknown". Conflating it with null would lose information |
| Every outcome (`success`, `not_found`, `error`, `blocked`) writes a document with the same key set | One document per input ID, so completeness is a simple count |

Crawled prices are the 2026 catalog, not 2019 transaction prices. Revenue must come from `checkout_success.cart_products`; crawled prices are only descriptive attributes of a product.

## 4. Request rate

Throughput is `min(1 / delay, concurrency / latency)`, with a median latency of about 0.53 s. The rate was raised in steps, stopping immediately on any block:

| Setting | Measured | Requests | Outcome |
| --- | ---: | ---: | --- |
| 1 worker, 0.5 s between starts | 0.74 req/s | 80 | No block; bound by latency |
| 4 workers, 0.5 s | 1.99 req/s | 1,048 | No block; stable minute by minute |
| 4 workers, 0.25 s | 3.95 req/s | 1,054 | No block |
| 8 workers, 0.125 s | 7.88 req/s | 1,034 | No block in a 2-minute batch |
| Full crawl, 8 workers, 0.125 s | 7.37 req/s | 1,562 | **Akamai challenge** after 3.5 min; about 5,600 requests from this IP in the preceding 1.5 h |
| Full crawl, 6 workers, 0.2 s + up to 0.1 s jitter | 3.80 req/s | 18,329 | **Completed in 80 min, no block** |

**Decision.** Run full crawls at about 4 req/s with small jitter. The CLI hard-caps the rate at 8 req/s (`--delay ≥ 0.125 s`, `--concurrency ≤ 8`).

**Caveat.** The second run also started after a 10-minute pause, so the effect of rate and the effect of rest are not separated. About 4 req/s is a rate observed to work, not a measured limit.

## 5. Checkpointing: the data is the checkpoint

**Options considered**
- Sort the IDs and resume from the last written ID (a cursor).
- A separate SQLite checkpoint file.
- Use the written MongoDB documents themselves as the checkpoint.

**Decision.**
- Use the written MongoDB documents themselves as the checkpoint.
- An ID is finished when its `products` document has status `success` or `not_found`, or `error` after `--max-attempts`.
- Each run crawls `input IDs − finished IDs`.

**Why**
- **Nothing extra to keep consistent.** The checkpoint cannot disagree with the data, because it *is* the data.
- **Order is irrelevant.** Concurrent workers finish out of order, so a "last ID" cursor would be wrong or would force serialization. A set difference needs no sorting.
- **Safe when inputs change.** Changing or reordering the input file stays safe: finished IDs are skipped by `_id`.
- **Small enough to load.** Loading `_id`, `status` and `attempts` for about 20K documents takes milliseconds.

**Why MongoDB first, files later.** MongoDB already hosts the source events and provides upserts, schema validation and a single place to query results. Exporting to GCS/BigQuery is a separate, later step: a snapshot per run (for example `products/run_id=…/part-*.jsonl.gz`) loaded with `WRITE_TRUNCATE`. Writing files during the crawl would duplicate checkpoint logic.

## 6. Blocks: stop, wait, never bypass

**Decision**
- **Detection:** any `401`/`403`/`429`, or any non-JSON `200`, counts as `blocked`. The Akamai challenge is an HTML page with a `bm-verify` meta refresh.
- **On a block:**
  - Stop issuing requests immediately.
  - Flush what was already fetched.
  - End the run as `stopped`.
- **Optional resume:** `--block-retries N` (at most 3) resumes after waits of 5, 10 and 20 minutes. Each resume is a new run document.
- **What the crawler never does:** follow the challenge, execute JavaScript, change its User-Agent, rotate IPs or solve CAPTCHAs.

**Consequence.** If a block persists after the last retry, the remaining IDs simply stay unfinished. A later run, or a permitted data source, picks them up.

## Outcome

| Metric | Value |
| --- | ---: |
| Input IDs (distinct across `product_id`, `viewing_product_id`, `cart_products[].product_id`) | 19,557 |
| `success` / `not_found` | 19,121 / 436 |
| Event product references without crawled attributes | 385,273 of 25,054,210 (1.54%) |
| Option reference rows | 923,294 (170,256 product–option pairs) |
| Storage | `products` 3.9 MB, `product_option_values` 73.0 MB |

The [product crawl README](../../src/glamira_pipeline/products/README.md) documents the commands, schema and verification queries.
