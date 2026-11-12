# Nghiên cứu crawl thông tin sản phẩm Glamira

**Chỉ là nghiên cứu, chưa có code crawler.** Quan sát ngày 12/11/2026 trên **một sản phẩm** (`product_id = 100002`) ở hai storefront (`www.glamira.co.uk`, `www.glamira.de`), cộng một ID không tồn tại. Kết luận về cấu trúc trang dựa trên mẫu nhỏ này và phải được xác nhận lại ở checkpoint crawl 100 sản phẩm.

## 1. URL mục tiêu

```text
https://www.glamira.{domain}/catalog/product/view/id/{product_id}
```

- Route Magento này trả **HTTP 200 ngay tại URL đó** (không redirect). `<link rel="canonical">` trỏ tới slug SEO, ví dụ `https://www.glamira.de/glamira-ring-palmier.html`.
- ID không tồn tại → **HTTP 404**.
- Nội dung khớp dữ liệu sự kiện: trong sample, ID 100002 có URL `glamira-ring-palmier.html` và trang crawl đúng là “Ring Palmier”.

### Chọn domain

Sample 100K có **5,142 `product_id`** trên **62 hostname**; **2,112 ID** xuất hiện ở nhiều hơn một hostname. Tên và category được **bản địa hoá theo domain**:

| Field | `glamira.co.uk` | `glamira.de` |
| --- | --- | --- |
| Tên | Engagement Ring Palmier | Verlobungsring Palmier |
| Category | Engagement Rings | Verlobungsringe |
| Currency | GBP | EUR |
| `store_code` | `glgb` | `glde` |
| `product_type` / `attribute_set` / `collection` / `gender` | `ring` / `diamonds` / `halo` / `women` | giống hệt |

Danh sách storefront tiếng Anh đã xác minh và danh sách field bất biến theo option nằm ở [product_crawl_fields_and_domains.md](product_crawl_fields_and_domains.md).

Đề xuất: crawl **một lần mỗi `product_id`** trên một domain chuẩn tiếng Anh (`www.glamira.co.uk` hoặc `www.glamira.com`), fallback sang hostname đã quan sát trong dữ liệu nếu domain chuẩn trả 404 (sản phẩm có thể không bán ở mọi thị trường). Bỏ các host dev/stage (`glamira.local`, `dev5.glamira.de`, `stage.glamira.de`). Như vậy `dim_product` có một tên/category tiếng Anh nhất quán, và dùng thêm mã trung lập `product_type`/`attribute_set` để nhóm.

## 2. Các nguồn dữ liệu trong trang

Trang sản phẩm (HTML ~500 KB) có ba khối dữ liệu có cấu trúc **được render sẵn trên server**, parse được mà không cần chạy JavaScript:

### 2.1 JSON-LD `schema.org/Product` (`<script type="application/ld+json">`)

Là chuẩn công khai, ổn định nhất. Nằm trong `ItemPage.mainEntity`.

| Key | Ví dụ (UK) |
| --- | --- |
| `name` | 9ct Yellow & White Gold Heart Lab Grown Diamond Engagement Ring Palmier |
| `sku` | `100002_7` |
| `mpn` | `PALMIER` |
| `gtin` | `0010000287059` |
| `brand.name` | Glamira Diamonds |
| `material` | 9ct Yellow & White Gold |
| `image[]` | URL ảnh CDN |
| `offers.price` / `offers.priceCurrency` | `1046.32` / `GBP` |
| `offers.availability` | `https://schema.org/InStock` |
| `offers.url` | URL có tham số cấu hình mặc định (`alloy`, `stone1`...) |

Một khối JSON-LD khác là `BreadcrumbList`: Home → **Engagement Rings** → Engagement Ring Palmier.

### 2.2 `dataLayer.push({"event":"productPage", "product": {...}})` (Google Tag Manager)

Nằm trong một `<script>` inline. Gọn và có category trực tiếp:

```json
{"id":"100002_7","sku":"PALMIER","parent_sku":"PALMIER","product_type":"simple",
 "name":"Engagement Ring Palmier","price":"1276.00","attribute_set_id":"55",
 "path":"Engagement Rings > Engagement Ring Palmier","category":"Engagement Rings",
 "stone":"lab-grown-diamond","alloy":"yellow_white-375","gender":"Female","style_id":"538"}
```

Một `dataLayer.push` trước đó có `ecomm_category`, `item_group_id` (= `product_id`), `currencyCode`.

### 2.3 Meta tag Open Graph

`og:title`, `og:url` (slug), `og:image`, `product:price:amount` (`720`), `product:price:currency` (`GBP`).

### 2.4 Endpoint JSON `react_data` (không có trong HTML)

Trang tải thêm bằng JS: `/productcustomizer/reactdata/index/id/{product_id}/?currency={CUR}`. robots.txt **cho phép rõ ràng** đường dẫn này (`Allow: /productcustomizer/reactdata/`). Trả JSON 200, hoặc 404 `{"error":"Product not found"}`. Có các field giàu nhất: `product_id`, `name`, `sku`, `attribute_set` (`diamonds`), `product_type` (`ring`), `collection` (`halo`), `collection_id`, `gender`, `price`, `min_price`, `max_price`, `gold_weight`, `store_code`, `attributes` (bảng thông số kèm label).

Nhược điểm: response **~836 KB**, lớn hơn trang HTML, vì chứa toàn bộ ma trận tuỳ chọn. Lưu ý `category`/`category_name` trong endpoint này rỗng (`0`/`""`) cho sản phẩm thử; category phải lấy từ GTM hoặc breadcrumb.

## 3. Mapping field đề xuất cho collection `products`

| Field đích | Nguồn chính | Fallback | Ghi chú |
| --- | --- | --- | --- |
| `product_id` | ID đầu vào | `item_group_id` (GTM) | Khoá upsert; kiểm tra trùng với ID trên trang |
| `product_name` | GTM `product.name` | breadcrumb cuối, `og:title` | Tên ngắn; JSON-LD `name` là tên dài theo cấu hình mặc định |
| `category_name` | GTM `product.category` | breadcrumb vị trí 2, `ecomm_category` | Bản địa hoá theo domain |
| `category_path` | GTM `product.path` | breadcrumb | |
| `product_type_code` | `react_data.product_type` | — | Mã trung lập (`ring`); chỉ có trong endpoint JSON |
| `attribute_set_id` | GTM / `window.product.attribute_set_id` | — | `55` |
| `sku` | GTM `product.sku` | JSON-LD `mpn` | `PALMIER` |
| `gender` | GTM `product.gender` | — | |
| `price_amount` | JSON-LD `offers.price` | — | Xem định nghĩa giá bên dưới |
| `currency_code` | JSON-LD `offers.priceCurrency` | `product:price:currency` | **Đây là “đơn vị” giá** |
| `availability` | JSON-LD `offers.availability` | — | |
| `image_url` | JSON-LD `image[0]` | `og:image` | |
| `canonical_url` | `<link rel=canonical>` | `og:url` | |
| `store_code`, `source_url`, `crawled_at`, `http_status`, `crawl_status`, `parser_version` | metadata crawler | — | Provenance |

### Định nghĩa giá — cần chốt

Cùng một sản phẩm, trang có **ít nhất bốn con số giá** (UK, 100002):

| Nguồn | Giá trị | Ý nghĩa (suy luận, chưa xác nhận) |
| --- | --- | --- |
| `product:price:amount`, `react_data.price` | 720 | Giá gốc cơ bản |
| `window.product.price_init.full_price`, GTM `price` | 1276.00 | Giá cấu hình mặc định trước khuyến mãi |
| JSON-LD `offers.price` | 1046.32 | Giá cấu hình mặc định sau giảm 18% |
| `react_data.min_price` / `max_price` | 245 / 38075 | Khoảng giá theo mọi cấu hình |

Giá crawl là giá **năm 2026**, không phải giá giao dịch 10–11/2019. Doanh thu trong fact table phải lấy từ `checkout_success.cart_products`; giá crawl chỉ là thuộc tính mô tả của `dim_product`. Đề xuất lưu `price_amount` = JSON-LD `offers.price` kèm `currency_code` và ghi rõ ý nghĩa.

## 4. Robots.txt và rào cản truy cập

- `robots.txt` (`glamira.co.uk`) **không chặn** `/catalog/product/view/` và không có `Crawl-delay`. Nó chặn `/rest/`, `/checkout/`, `/customer/`, các tham số `SID`/`___store`... Vậy không dùng REST API (`/rest/...`).
- **Rào cản chính:** request HTTP thông thường (curl với User-Agent trình duyệt) tới cả `robots.txt` lẫn trang sản phẩm đều nhận **`403 Access Denied`** từ CDN **Akamai** (`errors.edgesuite.net`). Trình duyệt thật thì truy cập bình thường. Vậy site có cơ chế quản lý bot chủ động.
- Theo `AGENTS.md` (“Do not implement block circumvention”), crawler **không được** né cơ chế này bằng xoay User-Agent, giả lập fingerprint TLS/trình duyệt, proxy xoay vòng... Gợi ý trong brief (`fake_useragent` để “tránh bị detect”) mâu thuẫn với quy tắc đó.

### Các phương án hợp lệ (cần người dùng chọn)

1. **Con đường “Rank B” trong brief:** viết `crawl_products.py` đúng chuẩn (rate limit, retry có giới hạn, log 403/timeout, resume), chạy crawl thử, nộp log lỗi cho coach để nhận `products_backup.csv`. Phần parser vẫn được kiểm chứng bằng các trang HTML lưu lại.
2. **Xin phép/whitelist** từ Glamira hoặc từ coach (ví dụ một IP/User-Agent được cho phép, có liên hệ), rồi crawl với User-Agent định danh trung thực.
3. Xác nhận với coach xem việc tự động hoá trình duyệt có được Glamira cho phép trong khuôn khổ khoá học không. Không triển khai khi chưa có sự cho phép.

### Thử nghiệm Selenium (12/11/2026)

Probe: [`analysis/crawl_research/selenium_probe.py`](../../analysis/crawl_research/selenium_probe.py). Cấu hình Chrome 157 **không chỉnh sửa**: không giả User-Agent, không dùng plugin stealth, `navigator.webdriver = true`. Driver được Selenium Manager tự tải. Selenium nằm trong dependency group `research`. Mỗi lần chạy tối đa 20 ID, nghỉ 4 giây giữa các trang, và tự dừng khi gặp dấu hiệu chặn. Output ở `data/crawl_research/` (bị gitignore).

| Lần chạy | Kết quả |
| --- | --- |
| Headless (`--headless=new`), ID 100002 | **`Access Denied`** (Akamai), dừng ngay |
| Có cửa sổ (headed), ID 100002 và 104054 | **OK**, khoảng 2.5 s/trang; có đủ JSON-LD, GTM `productPage`, `react_data`, `store = 7`, `lang = en-GB` |
| Headed, ID 999999999 | Trang `404 Not Found`, phát hiện được qua title |
| Headed, ID 101800 và 90784 (chạy ngay sau 404, cùng phiên) | **`ERR_HTTP2_PROTOCOL_ERROR`**: server ngắt kết nối. Hai ID này tải bình thường từ trình duyệt nhúng trước đó |
| Headed, phiên mới, `100002?alloy=white-585&stone1=ruby` | OK; cấu hình được áp dụng (JSON-LD 1229.18 GBP, `offers.url` chứa `stone1=ruby`) |

**Lần chạy 20 ID chậm** (headed, nghỉ 10 s giữa các trang; 20 ID chọn theo hash từ pool 300K, gồm 14 ID từ event xem sản phẩm và 6 ID từ giỏ hàng; output `data/crawl_research/selenium_probe_20.jsonl`):

| # | ID | Kết quả | `product_type` | GTM `category` |
| ---: | --- | --- | --- | --- |
| 1 | 107528 | OK, 2.5 s | `wedding_ring` | Men’s Wedding Rings |
| 2 | 103590 | OK, 2.8 s | `ring` | Rings |
| 3 | 109887 | OK, 2.4 s | `pendant` | Necklaces |
| 4 | 107335 | OK, 2.5 s | `wedding_ring` | **null** (breadcrumb chỉ có `Home > tên`) |
| 5 | 90563 | **`connection_error`** (`ERR_HTTP2_PROTOCOL_ERROR`) sau khoảng 1 phút, probe tự dừng | — | — |

15 ID còn lại không được thử trong lần này.

**Lần chạy nghỉ 45 s** (phiên headed mới, bắt đầu khoảng 8 phút sau lần trước, 15 ID còn lại; output `data/crawl_research/selenium_probe_slow45.jsonl`): 90563 OK (Men's Wedding Ring Immortal Wish, `wedding_ring`), 101597 OK (Kid's Earring Chibuzo, `earring`). Trang thứ 3 (105499) bị **`connection_error`** sau khoảng 2 phút và probe tự dừng. Chạy chậm hơn **không** giúp lấy thêm trang: lần nghỉ 10 s được 4 trang, lần nghỉ 45 s chỉ được 2. Như vậy việc chặn dựa trên nhận diện phiên tự động, không phải giới hạn tốc độ. Ở cả hai phiên headed, server đều ngắt kết nối **sau 2–4 trang**, nên tốc độ chậm không ngăn được việc bị đánh dấu. Trong 4 trang OK: `name`, `product_type`, `attribute_set`, `currency` có đủ 4/4; GTM `category` null 1/4. `gender` có giá trị `false` ở 107335. Meta `product:price:amount` (664) **lớn hơn** giá cấu hình mặc định ở JSON-LD (88.56 GBP) với ID 107528, nên ý nghĩa "giá gốc" của meta chưa đáng tin.

**Lần chạy có jitter** (`--delay 6 --jitter 14`, tức nghỉ ngẫu nhiên 6–20 s; headed, phiên mới; khoảng 35 phút sau lần chạy 45 s):

| Lô | ID | Kết quả | Output |
| --- | --- | --- | --- |
| 1 | 10 ID đã thử trước đó | **10/10 OK** | `data/crawl_research/selenium_probe_jitter.jsonl` |
| 2 (phiên mới, ngay sau lô 1) | 10 ID ngẫu nhiên từ pool (seed 7) | 2 OK, trang thứ 3 (89495) bị **`connection_error`**, dừng | `data/crawl_research/selenium_probe_jitter2.jsonl` |

Ở lô 1, 2/10 trang (104054, 107528) chưa có `react_data` lúc trích xuất, vì probe chỉ chờ một trong hai nguồn (GTM hoặc `react_data`); GTM `category` null ở 2/10. Lô 1 thành công nhiều khả năng là do IP đã "nghỉ" khoảng 35 phút chứ không phải nhờ jitter: lô 2 dùng đúng cấu hình đó nhưng lại bị ngắt sau 2 trang. **Jitter không giúp ổn định**; 12/13 trang OK trong khoảng 4 phút, sau đó bị chặn.

### Thử endpoint `react_data` bằng curl thường (12/11/2026, sau lần Selenium ở trên)

`curl -s "https://www.glamira.co.uk/productcustomizer/reactdata/index/id/{id}/?currency=GBP"`: UA mặc định của curl, không thêm header nào, tuần tự, nghỉ 3 s.

| Kết quả | Số lượng |
| --- | --- |
| 200 `application/json` | **9/9 ID** (gồm 89495, ID mà Selenium vừa bị ngắt) |
| ID không tồn tại (999999999) | 404, `{"error":"Product not found"}`; phân biệt rõ với lỗi mạng hoặc bị chặn |

Field có đủ ở 9/9 ID: `name`, `sku`, `product_type` (ring, earring, wedding_ring, pendant, cufflink), `attribute_set`, `collection`, `gender`, `price`/`min_price`/`max_price`, `product_price.currencyCode` (GBP), `options[]`, `store_code` (`glgb`). `category` = 0 và `category_name` = "" ở 9/9 ID, nên dùng `product_type` làm category. Kích thước 59–834 KB mỗi sản phẩm (phần lớn là `options`).

Ý nghĩa: endpoint này được robots.txt cho phép và trả JSON cho client thường mà không cần trình duyệt. Trước đây request kiểu này bị 403, nên hành vi của Akamai thay đổi theo thời gian hoặc theo IP. Nếu crawl thì phải dừng ngay khi gặp 403/429, không retry dồn dập. Mẫu mới chỉ có 9 ID, chưa đủ để khẳng định chạy được ổn định cho khoảng 12K ID.

Diễn giải:

- Akamai phân biệt được headless. Chế độ headed được phục vụ dù tự khai báo `webdriver`.
- Việc bị ngắt kết nối giữa phiên là dấu hiệu bị đánh dấu nghi ngờ (soft-block). Probe giờ ghi trạng thái `connection_error` và dừng, không retry.
- Muốn chạy headed trên VM không có màn hình thì cần một display ảo (Xvfb). Cách đó giả trạng thái có màn hình chỉ để đi qua bộ lọc headless, nên cần được cho phép trước khi dùng.
- Kết luận: Selenium headed **về kỹ thuật** lấy được dữ liệu ở tốc độ thấp, nhưng site có cơ chế chống bot đang hoạt động. Việc mở rộng quy mô vẫn là quyết định chính sách (xem các phương án ở trên), không chỉ là vấn đề kỹ thuật.

## 5. Thiết kế crawler đề xuất (sau khi chốt phương án truy cập)

- **Input:** danh sách unique `product_id` (+ hostname đã quan sát) từ Stage 3 (xem `docs/specifications/e2e_pipeline_requirements.md`).
- **Tách module:** `fetch` (HTTP, rate limit, retry) / `parse` (hàm thuần: HTML → dict, test bằng fixture HTML đã lưu) / `store` (upsert MongoDB theo `product_id`, staging → publish) / `cli`.
- **Parse:** ưu tiên JSON-LD và GTM `dataLayer` (parse JSON trong `<script>`, không dựa vào class CSS); BeautifulSoup + `json`. Ghi `parse_warnings` khi thiếu field.
- **Lịch:** 1 request đồng thời, delay ≥ 1.5–4 s, nghỉ dài hơn sau mỗi batch; dừng hẳn (circuit breaker) khi gặp liên tiếp 403/429 thay vì thử né.
- **Trạng thái:** `ok`, `not_found` (404), `blocked` (403), `failed` (timeout/5xx sau N lần retry), `parse_error`. Lưu cả ID lỗi để count `products` = số ID đầu vào.
- **Resume:** bỏ qua ID đã có trạng thái cuối `ok`/`not_found`; retry các ID `failed`.
- **Khối lượng:** thời gian ≈ số ID × (delay trung bình + thời gian tải). Sample có 5,142 ID (≈ 4.3 giờ ở 3 s/ID); số ID trên full data chưa đo, cần chạy Stage 3 full trước khi ước tính.
- **Checkpoint 2.2b:** 100 ID, AC = `product_name` và category có dữ liệu, không exception không xử lý.

## 6. Giới hạn

- Cấu trúc chỉ quan sát trên **một sản phẩm**, loại `simple`, attribute set `diamonds`. Sản phẩm `configurable`, đã ngừng bán, hoặc thuộc loại khác (vòng tay, dây chuyền...) có thể có cấu trúc khác.
- Quan sát qua trình duyệt nhúng; không kiểm tra Terms of Service của Glamira.
- Website hiện tại có thể đã đổi tên/category so với 2019; sản phẩm 2019 có thể đã bị xoá (404).

## 7. Crawler `react_data`: kiểm chứng store và test tốc độ (12/11/2026)

Code: `uv run crawl-products` (`src/glamira_pipeline/products/crawl.py`). Client là `urllib` với User-Agent trung thực `glamira-pipeline-research/0.1`, gzip, 1 luồng. Crawler dừng ngay khi gặp 401/403/429 hoặc trang không phải JSON.

### Store tiếng Anh (1 request mỗi host, ID 100002, nghỉ 3 s)

Cả 11 host đều trả 200 JSON với tên tiếng Anh. `?currency=` **không** đổi được currency trong cùng host (`.co.uk` với `USD` vẫn trả GBP). Giá khác nhau theo store, không chỉ là quy đổi tỷ giá: `.com` có `price` 901 USD còn `.africa` có 968 USD.

| Ưu tiên | Host | Currency | `store_code` | `price` | `sale_price` |
| ---: | --- | --- | --- | ---: | ---: |
| 1 | www.glamira.com | USD | glus | 901 | 1357.45 |
| 2 | www.glamira.africa | USD | glaf | 968 | 1407.94 |
| 3 | www.glamira.ie | EUR | glie | 832 | 1254.60 |
| 4 | www.glamira.com.mt | EUR | glmt | 832 | 1254.60 |
| 5 | www.glamira.co.uk | GBP | glgb | 720 | 1084.60 |
| 6–11 | .com.au, .ca, .sg, .co.nz, .co.za, .ae | AUD, CAD, SGD, NZD, ZAR, AED | glau … glae | — | — |

Gzip giảm response từ khoảng 834 KB xuống khoảng 25 KB với 100002 (trung bình khoảng 11 KB mỗi request trong lần test bên dưới).

### Tăng tốc theo nấc

Sample là 200 ID ngẫu nhiên (`--sample 200 --seed 7`) từ 12,734 ID có trong pool `$sample` 300K ở local. **Đây chưa phải danh sách distinct từ MongoDB**: lần truy vấn MongoDB còn chờ credential read-only.

| Nấc | `--delay` | Request | Thời gian | req/s thực tế | p50 / p95 latency | Kết quả |
| ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 3 s | 40 | 166 s | 0.24 | 1.02 / 3.28 s | 40 ok |
| 2 | 2 s | 40 | 117 s | 0.34 | 0.87 / 1.76 s | 40 ok; bỏ qua 40 ID đã xong |
| 3 | 1 s | 44 | 81 s | 0.55 | 0.89 / 1.20 s | 38 ok, 6 not_found (2 ID × 3 store) |
| 4 | 0.5 s (giới hạn) | 80 | 108 s | 0.74 | 0.87 / 1.32 s | 80 ok |

- **Không bị chặn ở nấc nào**, nên không cần jitter. Mình không tăng quá 0.5 s/1 luồng (≤ 2 req/s) để tôn trọng site.
- Ở 1 luồng, tốc độ bị giới hạn bởi latency (khoảng 0.9 s), nên thực tế chỉ đạt khoảng 0.74 req/s.
- Mọi ID tìm thấy đều có ở store ưu tiên số 1 (`.com`). 2 ID (110296, 110328) trả 404 ở cả `.com`, `.africa` và `.ie`.
- **Ước tính:** với 19,557 distinct ID từ MongoDB (xem [product_ids_distinct](product_ids_distinct.md)), crawl mất khoảng 7.3 giờ ở nấc 4 và khoảng 9.9 giờ ở nấc 3; tổng dung lượng truyền khoảng 215 MB.

### Chất lượng 198 sản phẩm crawl được

| Field | Quan sát |
| --- | --- |
| `name`, `sku`, `product_type`, `attribute_set`, `price`, `currency`, `gender` | Có ở 198/198 |
| `gender` | women 109, `false` 55, men 34. `false` chủ yếu là `wedding_ring` (41/55), nên **không** có nghĩa là "kids" |
| `product_type` | 12 giá trị (wedding_ring 87, ring 53, earring 22, …). Có 1 giá trị placeholder `--_select_--` (92542 "Sonate") |
| `min_price`/`max_price` | null ở 5/198 (sản phẩm vẫn có `price`) |
| `collection` | rỗng ở 10/198 (`collection_id` null) |
| `category_name` | rỗng ở 196/198; có giá trị ở 2 sản phẩm ("Women’s Wedding Rings", "Diamond Earrings") |
| Bảng option | 9,673 dòng. 350 dòng không có `value_id` (option nhập tự do: engraving). 1,146 dòng không có `part_type` (`radio`, `engraving_*`), khi đó nhận diện bằng `option_type` |

Giới hạn: đây là catalog năm 2026, giá là USD của store `.com` hiện tại. Sample lấy từ pool local, chưa phải danh sách distinct ID từ MongoDB.

### Async: nghỉ 0.5 s giữa các lần bắt đầu request, tối đa 4 request đồng thời

`--delay` giờ là khoảng cách tối thiểu giữa **các lần bắt đầu request**, nên `--delay 0.5` giới hạn ở tối đa 2 req/s, dù có bao nhiêu request đang chạy. Lệnh:

```bash
uv run crawl-products --ids-file data/product_ids/full/product_ids.jsonl --output-dir data/product_crawl/async_test --sample 200 --seed 11 --delay 0.5 --concurrency 4
```

Sample là 200 ID ngẫu nhiên từ 19,557 distinct ID trong MongoDB.

| Request | Thời gian | req/s | p50 / p95 latency | Kết quả |
| ---: | ---: | ---: | --- | --- |
| 206 | 103.5 s | **1.99** | 0.66 / 1.10 s | 197 ok; 3 ID not_found (9 request); không bị chặn |

- Bảng option có 9,482 dòng; tổng dung lượng truyền 2.06 MB (khoảng 10 KB mỗi request).
- **Ước tính crawl toàn bộ 19,557 ID: khoảng 2.7 giờ** ở 2 req/s, thêm khoảng 1.5% request fallback cho các ID 404.
- Lần chạy chỉ kéo dài khoảng 2 phút; chưa kiểm chứng việc duy trì 2 req/s trong nhiều giờ.

### Độ ổn định: 1,000 ID mỗi lô, 4 request đồng thời

| Lô | `--delay` | Seed | Request | Thời gian | req/s | p50 / p95 latency | Kết quả |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `stability_1000` | 0.5 s | 21 | 1,048 | 527.8 s | 1.99 | 0.55 / 1.11 s | 976 ok, 24 ID not_found, **0 bị chặn hoặc lỗi** |
| `rate_025` | 0.25 s | 31 | 1,054 | 266.7 s | 3.95 | 0.54 / 0.88 s | 973 ok, 27 ID not_found, **0 bị chặn hoặc lỗi** |

- **Theo từng phút:** ở 0.5 s, mỗi phút đều đạt 1.93–2.02 req/s; ở 0.25 s, mỗi phút đạt 3.87–4.00 req/s. p50 giữ ổn định ở 0.53–0.62 s, không có xu hướng tăng dần.
- **Không tìm thấy:** 2.4–2.7% ID trả 404 trên cả 3 store đầu.
- **Ước tính crawl toàn bộ 19,557 ID ở 4 req/s:** khoảng 1.4 giờ, khoảng 20,000 request, khoảng 200 MB truyền.
- **Giới hạn trên của CLI:** `--delay ≥ 0.25 s` (≤ 4 req/s), tối đa 4 request đồng thời.
- **Chưa kiểm chứng:** mỗi lô chỉ chạy dưới 9 phút; một lần crawl kéo dài hơn 1 giờ vẫn có thể bị Akamai đánh giá khác.
