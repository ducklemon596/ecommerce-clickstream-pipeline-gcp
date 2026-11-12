# Crawl mỗi product một lần: field chung và domain tiếng Anh

**Chỉ là nghiên cứu, chưa có code crawler.** Quan sát ngày 12/11/2026 bằng trình duyệt nhúng; các request gửi tuần tự, cách nhau 2 giây. Báo cáo này bổ sung cho [product_crawl_research.md](product_crawl_research.md).

## 1. Phương pháp

- **Bất biến theo option:** tải trang `/catalog/product/view/id/{id}` của `www.glamira.co.uk` với **3 cấu hình khác nhau** (mặc định, đổi kim loại + đá, đổi cả đá phụ), áp dụng cho 2 sản phẩm thuộc 2 loại khác nhau (nhẫn 100002, khuyên tai 104054). Sau đó so sánh từng field.
- **Bất biến theo store:** so sánh product 100002 giữa `.co.uk` và `.de` (tiếng Đức), và giữa 10 storefront tiếng Anh.
- **Độ phủ:** lấy 10 `product_id` **chưa từng xuất hiện trên store tiếng Anh** trong pool 300K, rồi kiểm tra chúng trên `.co.uk`. Thêm 4 ID để kiểm tra fallback category.
- Endpoint `react_data` (`/productcustomizer/reactdata/index/id/{id}/?currency=…`) không nhận tham số option, nên mọi field của nó **bất biến theo option ngay từ cách thiết kế**.

## 2. Field nên lấy (chung cho mọi tổ hợp option)

### 2.1 Field chung, nên lưu vào `products` / `dim_product`

| Field đích | Nguồn | Ví dụ | Bất biến theo option | Bất biến theo store | Ghi chú |
| --- | --- | --- | :---: | :---: | --- |
| `product_id` | ID đầu vào; kiểm tra với GTM `item_group_id` | `100002` | ✓ | ✓ | Khoá |
| `product_name` | GTM `product.name` (fallback `<h1>`, `og:title`) | Engagement Ring Palmier | ✓ | ✗ (bản địa hoá) | **Không** dùng JSON-LD `name` (thay đổi theo cấu hình) |
| `product_type_code` | `react_data.product_type` | `ring`, `wedding_ring`, `pendant`, `earring` | ✓ | ✓ | **Nên làm category chính**: mã trung lập, có giá trị ở 18/18 sản phẩm đã thử (1 giá trị bẩn, xem §2.3) |
| `attribute_set_code` | `react_data.attribute_set` | `diamonds`, `trauring` | ✓ | ✓ | Nhóm kỹ thuật (trauring = nhẫn cưới) |
| `attribute_set_id` | GTM / `window.product.attribute_set_id` | `55` | ✓ | ✓ | |
| `collection_code` | `react_data.collection` | `halo`, `pearl`, `memoire` | ✓ | ✓ | |
| `gender` | `react_data.gender` (fallback GTM `gender`) | `women` | ✓ | ✓ | Có thể là `false` (99003) |
| `category_name` | GTM `product.category` (fallback breadcrumb) | Engagement Rings | ✓ | ✗ | Category merchandising, **null ở 2/10** sản phẩm thử; mặt dây chuyền lại nằm trong "Necklaces". Chỉ nên dùng làm sub-category |
| `category_path` | GTM `product.path` / BreadcrumbList | Jewellery > Women's Jewellery > … | ✓ | ✗ | Có khi chỉ là `Home > tên` |
| `sku` (mã mẫu) | GTM `product.sku` = JSON-LD `mpn` | `PALMIER` | ✓ | ✓ | |
| `brand_name` | JSON-LD `brand.name` | Glamira Diamonds | ✓ | ✓ | |
| `product_url` | `<link rel=canonical>` **của trang không có tham số** | `…/glamira-ring-palmier.html` | ✗ (thêm query) | ✗ (domain) | Bỏ query string |
| `base_price_amount` | `product:price:amount` = `react_data.price` | `720` | ✓ | ✗ (theo currency) | Giá gốc trước cấu hình. Ý nghĩa cần xác nhận |
| `min_price_amount`, `max_price_amount` | `react_data.min_price` / `max_price` | `245` / `38075` | ✓ | ✗ | Khoảng giá trên mọi cấu hình |
| `currency_code` | `product:price:currency` / JSON-LD `priceCurrency` | `GBP` | ✓ | ✗ | **Đơn vị** của mọi field giá |
| `availability` | JSON-LD `offers.availability` | InStock | ✓ (2 sản phẩm thử) | ? | |
| `default_config` | JSON-LD `offers.url` của trang không có tham số | `alloy=yellow_white-375&stone1=…` | — | ✗ (mặc định khác theo store) | Ghi lại để biết giá mặc định ứng với cấu hình nào |
| `store_code`, `store_id`, `source_url`, `crawled_at`, `http_status`, `crawl_status`, `parser_version` | metadata crawler | `glgb`, `7` | | | Provenance |

### 2.2 Field thay đổi theo cấu hình: **không** dùng làm thuộc tính sản phẩm

Field trong cột thứ hai là field đã quan sát thấy thay đổi khi đổi option.

| Field | Thay đổi khi đổi option | Ví dụ (100002) |
| --- | --- | --- |
| JSON-LD `name` | ✓ | "9ct Yellow & White Gold … Lab Grown Diamond …" → "14ct White Gold … Diamond …" |
| JSON-LD `sku`, GTM `id`, `ecomm_prodid` | ✓ | `100002_7` → `100002_7_diamond-Brillant_white-585` |
| JSON-LD `gtin` | ✓ | Mỗi cấu hình một GTIN |
| JSON-LD `offers.price`, GTM `price`, `price_init.full_price` | ✓ | 1046.32 → 3332.48 → 1443.20 GBP |
| JSON-LD `material`, `color`, `image[]`, `og:image`, `description` | ✓ | "9ct Yellow & White Gold" → "18ct Rose Gold" |
| GTM `alloy`, `stone`, `stone2`, `stone3` | ✓ | Chính là cấu hình |
| `<title>`, `og:url`, canonical (khi có query) | ✓ | |

Một số field không mang thông tin: GTM `image_url` (`…productno_selection`) và GTM `style_id` (cùng giá trị `538` cho cả hai sản phẩm khác loại, có vẻ không phải thuộc tính sản phẩm).

### 2.3 Đề xuất nguồn cho từng câu hỏi dashboard

- **"Nhẫn bán chạy hơn vòng tay?"** Dùng `product_type_code` (`ring`, `wedding_ring`, `bracelet`, …), vì nó trung lập ngôn ngữ và luôn có giá trị. `category_name` chỉ dùng làm cấp con.
- **Doanh thu** vẫn lấy từ `checkout_success.cart_products` của năm 2019. Giá crawl (2026) chỉ là thuộc tính mô tả.
- **Dữ liệu bẩn cần xử lý:** sản phẩm 90784 (Braut-Set) có `product_type = "--_select_--"`, nên map thành `unknown` và giữ nguyên giá trị gốc.

### 2.4 Hai request cho mỗi product

Để có đủ field chung cần: (1) **trang HTML không có tham số** (~500 KB) cho tên, category, breadcrumb, canonical, giá mặc định, currency; (2) **`react_data`** (~800 KB) cho `product_type`, `attribute_set`, `collection`, `gender`, khoảng giá, và bảng mapping option ID → token ([OPTION_ID_SEMANTICS](../../analysis/product_configuration_research/OPTION_ID_SEMANTICS.md)). Nếu cần giảm tải, `react_data` một mình đã có `name`, `sku`, `price`, `product_type`, `attribute_set`, `collection`, `gender`, `currencyCode`; chỉ thiếu category merchandising và canonical.

## 3. Domain tiếng Anh

### 3.1 Storefront đã xác minh trên website (`<html lang>`, store ID, currency)

| Hostname | `lang` | Store ID hiện tại | `store_id` trong event 2019 | Currency | Tên / category của 100002 |
| --- | --- | ---: | ---: | --- | --- |
| `www.glamira.co.uk` | en-GB | 7 | 7 | GBP | Engagement Ring Palmier / Engagement Rings |
| `www.glamira.com.au` | en-AU | 29 | 29 | AUD | giống UK |
| `www.glamira.ca` (gốc, không có `/fr/`) | en-CA | 38 | 38 (`/fr/` = 39) | CAD | giống UK |
| `www.glamira.ie` | en-IE | 40 | 40 | EUR | giống UK |
| `www.glamira.co.za` | en-ZA | 79 | 79 | ZAR | giống UK |
| `www.glamira.sg` (gốc, không có `/cn/`) | en-SG | 37 | 37 (`/cn/` = 77) | SGD | giống UK |
| `www.glamira.co.nz` | en-NZ | 60 | 60 | NZD | giống UK |
| `www.glamira.ae` | en-AE | 63 | 63 | AED | giống UK |
| `www.glamira.com.mt` | en-MT | 36 | 36 | EUR | giống UK |
| `www.glamira.africa` (gốc; `/fr/`, `/pt/` là ngôn ngữ khác) | en-NG | 80 | 80 | USD | giống UK |

GTM `name`/`category` giống hệt nhau trên cả 10 storefront. Chỉ `<title>` SEO khác chút ít, ví dụ Canada ghi `9k` thay cho `9ct`.

### 3.2 Có khả năng là tiếng Anh nhưng **chưa xác minh**

| Hostname | `store_id` trong event | Lý do chưa xác minh |
| --- | ---: | --- |
| `www.glamira.com` (gốc; `/es/` = 68) | 41 | Trả trang chặn bot ("Powered and protected by…"); không thử vượt |
| `www.glamira.com.ph` | 86 | Như trên |
| `www.glamira.in` | 64 | Như trên |
| `www.glamira.com.my` | 99 | Như trên |
| `www.glamira.com.kw` | 100 | Như trên |
| `www.glamira.az/en/` | 98 | Như trên |
| `www.glamira.store` | 87 | Chứng chỉ TLS không khớp tên miền |

### 3.3 Đã kiểm tra, **không** phải tiếng Anh

- `www.glamira.hk` hiện có `lang = zh-HK`, store ID **110**. Trong dữ liệu 2019, store `47` (gốc) và `48` (`/cn/`) thuộc domain này. Như vậy **store ID có thể thay đổi theo thời gian**; không nên mặc định là `store_id` 2019 bằng store ID hiện tại.

### 3.4 Độ phủ và đề xuất domain

Trên pool 300K, có 12,734 ID sản phẩm (gồm `product_id`, `viewing_product_id` và ID trong giỏ hàng):

| Domain (cộng dồn theo thứ tự) | ID quan sát | Tỷ lệ cộng dồn |
| --- | ---: | ---: |
| `.co.uk` | 4,233 | 33.2% |
| + `.com` | +1,297 | 43.4% |
| + `.com.au`, `.ca`, `.ie`, `.co.za`, `.sg`, … | | 60.2% |

Tuy nhiên, "quan sát" không đồng nghĩa với "tồn tại". **10/10 ID chưa từng xuất hiện trên store tiếng Anh nào vẫn trả HTTP 200 trên `.co.uk`**, với tên tiếng Anh. Catalog có vẻ dùng chung giữa các store.

Đề xuất:

1. **Domain chính: `www.glamira.co.uk`.** Nó có traffic tiếng Anh lớn nhất, đã xác minh, và currency GBP cố định.
2. **Fallback** khi `.co.uk` trả 404: thử lần lượt `.com.au` → `.ca` → `.ie` (các store đã xác minh). Lưu `store_code` và `currency_code` của nơi crawl được. Giá từ fallback có currency khác, nên **không trộn giá giữa các currency** mà không quy đổi.
3. **Chỉ một bộ field tiếng Anh cho mỗi `product_id`**: đáp ứng yêu cầu "một `product_information` active cho mỗi `product_id`" của brief.
4. Loại khỏi danh sách crawl các host dev/test (`glamira.local`, `dev*.glamira.de`, `stage.glamira.de`, `test.glamira.de`) và `www.ring-paare.de` (thương hiệu khác).

## 4. Giới hạn

- So sánh option mới thực hiện trên 2 sản phẩm × 3 cấu hình; so sánh store thực hiện trên 1 sản phẩm. Loại `configurable`, bundle (bộ Braut-Set) hoặc sản phẩm không có option có thể khác.
- 10 ID thử độ phủ được chọn theo hash, chưa đủ để khẳng định mọi ID đều có trên `.co.uk`; ID đã bị xoá sẽ trả 404.
- Việc truy cập tự động vẫn bị Akamai chặn với HTTP client thường (xem [product_crawl_research.md](product_crawl_research.md) §4). Phương án truy cập chưa được chốt.
