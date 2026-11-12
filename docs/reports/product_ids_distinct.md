# Distinct product IDs in `countly.summary`

Observed 2026-11-12. Command:

```bash
uv run list-product-ids --output-dir data/product_ids/full
```

The command ran from the local workstation through an SSH tunnel to the VM (MongoDB 8.0.34). Outputs are in ignored `data/product_ids/full/`.

## Method

- **One read-only aggregation**, no indexes created. `explain` showed a single `COLLSCAN` with the projection pushed into the scan.
- **Fields read:** `product_id`, `viewing_product_id` and every `cart_products[].product_id`.
- **Excluded:** missing, null and empty values.
- **Grouping:** by the value converted to a string, so int32 cart IDs and string event IDs merge.
- **Client side:** only grouped rows were transferred.

## Result

| Metric | Value |
| --- | ---: |
| Source documents (`estimatedDocumentCount`) | 41,432,473 |
| **Distinct product IDs** | **19,557** |
| Non-numeric IDs / unconvertible values | 0 / 0 |
| Product references counted | 25,054,210 |
| Query wall time (server scan + streaming) | **375.1 s** (6 min 15 s) |
| Client peak RSS | 49 MB |

| Field | Distinct IDs | References | BSON type |
| --- | ---: | ---: | --- |
| `product_id` | 19,417 | 22,242,720 | string |
| `viewing_product_id` | 16,981 | 1,989,052 | string |
| `cart_products[].product_id` | 10,922 | 822,438 | int32 |

The collection is 33.5 GB uncompressed (11.3 GB on disk) and has only the `_id_` index.

## Notes

- All 12,734 IDs from the local 300K `$sample` pool used in the crawl rate test appear in this list.
- At the measured single-thread crawl rate (about 0.74 req/s at a 0.5 s delay; see [crawl research](product_crawl_research.md)), crawling 19,557 IDs would take about 7.3 hours, plus extra requests for IDs that fall back to other stores on 404.
- References count occurrences, not events: a cart with two items of one product counts twice.
