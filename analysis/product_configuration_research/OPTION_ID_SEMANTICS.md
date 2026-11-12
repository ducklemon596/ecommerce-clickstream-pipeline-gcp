# Ý nghĩa của `option` chỉ có ID (value_label rỗng)

**Chỉ là nghiên cứu; chưa có rule nào được implement.** Quan sát ngày 12/11/2026 trên pool `$sample` 300K đã redact (`data/product_configuration_research/random_300k_v2.jsonl`, xem [README](README.md)). Có đối chiếu với website hiện tại qua endpoint `react_data` (robots.txt cho phép) cho **13 sản phẩm**, request tuần tự, nghỉ 2 giây giữa các request.

## 1. Các dạng `option` theo event

Chạy lệnh: `python3 -I tools/option_shapes.py <pool.jsonl>`.

| Dạng | Event | Tỷ lệ trong pool | Ví dụ |
| --- | --- | --- | --- |
| **List, chỉ có ID** (`value_label` = `""`, có `value_id`) | `view_product_detail` | 79,153 / 79,822 (99.2%) | `{"option_label":"alloy","option_id":"322807","value_label":"","value_id":"2737438"}` |
| | `add_to_cart_action` | 1,331 / 1,355 (98.2%) | luôn là đúng 2 mục `alloy`, `diamond` |
| List có label + ID (label là token URL) | `select_product_option` | 63,716 (100%) | `value_label:"white_yellow-585"` |
| List có label + ID + quality | `select_product_option_quality` | 15,388; **822 mục rỗng hoàn toàn** | `option_label` không chuẩn: `stone/diamonds`, `stone 2`, `damenring steinbesatz` (tiếng Đức) |
| List trong `cart_products[]`, label kiểu admin bản địa hoá, ID dạng **int** | `view_shopping_cart`, `checkout`, `checkout_success` | 3,860 / 694 / 186 item | `"Weißgold 585"`, `"Swarovsky Cristall"` |
| `option = ""` (chuỗi rỗng) trong item giỏ hàng | 3 event giỏ hàng ở trên | 756 / 220 / 44 item | — |
| Dict filter (`alloy`, `diamond`, `shapediamond`) | `view_listing_page`, `listing_page_recommendation_*`, `view_sorting_relevance` | 100% event của các loại này | Bộ lọc trang danh mục, **không phải cấu hình sản phẩm** |
| Dict filter collection | `view_all_recommend` | 259 | key `Kollektion`, `category id`, `finish`, `kollektion_id`, `pearlcolor` |

Một số điểm bất thường khác: `select_product_option` có `option_label` viết sai là `pear` (505 mục có `value_id = ""`) và `stonetow` (437 mục có `value_id = null`). Kiểu của `value_id` không thống nhất: event trang sản phẩm dùng string, item giỏ hàng dùng int.

## 2. Phát hiện chính: ID ở trang sản phẩm là **cấu hình mặc định**, không phải lựa chọn

Giả thuyết: với `view_product_detail` và `add_to_cart_action`, `value_id` ghi lại **giá trị mặc định của sản phẩm** lúc trang được render, chứ không phải lựa chọn của người dùng (lựa chọn nằm ở token trên URL).

### Bằng chứng A — đối chiếu với website (12 sản phẩm có ID-only)

| Kết quả | Số lượng |
| --- | --- |
| `option_id` vẫn tồn tại trên website | 9/12 sản phẩm (ba sản phẩm 90784, 92381, 92185 đã đổi toàn bộ bộ option) |
| `value_id` tra được | 15 giá trị |
| …trong đó trỏ vào giá trị `is_default: true` hiện tại | **13/15** |
| Trường hợp phân định được | **90941**: URL `diamond=diamond-sapphire`, nhưng ID trỏ tới `diamond-Brillant` (mặc định) |
| | **90736**: hai event có **cùng `value_id`**, một event có URL `alloy=red_white-585&diamond=diamond-Brillant`, event kia không có option trên URL |

Hai mục còn lại (90736 `diamond` → `diamond-sapphire`, `is_default: false`) phù hợp với khả năng giá trị mặc định đã thay đổi từ 2019 đến nay.

### Bằng chứng B — tính bất biến ngay trong dữ liệu (không cần website)

Chạy lệnh: `python3 -I tools/option_value_id_invariance.py <pool.jsonl>`. Chỉ xét các cặp (`product_id`, `option_id`) có ít nhất 5 event ID-only.

| Chỉ số | Kết quả |
| --- | ---: |
| Cặp được xét | 5,659 |
| Chỉ có đúng 1 `value_id` | 2,809 (49.6%) |
| Cặp mà URL cho thấy ≥ 2 token khác nhau | 4,838 |
| …nhưng vẫn chỉ có 1 `value_id` | **2,154 (44.5%)** |

Nếu `value_id` là lựa chọn thì nó phải thay đổi theo URL. Trong gần một nửa số trường hợp nó không thay đổi. Các cặp có nhiều ID thường chỉ có 2–3 ID (1,883 cặp có 2 ID, 655 cặp có 3 ID), trong khi URL có 5–6 token.

Chạy lệnh: `python3 -I tools/option_value_id_by_store.py <pool.jsonl>`. Kết quả: trong 2,850 cặp có nhiều ID, **1,379 cặp được giải thích hoàn toàn bằng việc khác store** (giá trị mặc định theo thị trường). 1,471 cặp còn lại thay đổi ngay trong cùng một store. Nguyên nhân có thể là mặc định đổi theo thời gian, nhưng pool không có `time_stamp` nên chưa kiểm chứng được.

### Bằng chứng C — `select_product_option` cũng không ổn định theo ID

Trong 25,757 bộ ba (`product`, `option`, `value_id`), **3,581 bộ (13.9%) có hơn một `value_label`**. Ví dụ `value_id` 2752262 của product 100002 đi kèm cả `yellow-585` lẫn `white_yellow-585`. Ngược lại, chiều label → ID chỉ mơ hồ ở 2.6% trường hợp. Như vậy label/token mới là lựa chọn thực; ID chỉ là thông tin phụ.

## 3. Dùng ID để tra token hiện tại (khi cần)

`react_data.options[]` chứa đầy đủ bảng ánh xạ theo sản phẩm: `option_id` → `part_type` (`alloy`, `stone1`, `stone2`, ...) và `option_type_id` (chính là `value_id` của event) → `sku` (token URL hiện tại), `default_title` (nhãn admin tiếng Đức), `is_default`.

| Event 2019 | Website hiện tại |
| --- | --- |
| `option_label: "diamond"` | `part_type: "stone1"`. URL hiện tại phải dùng `stone1=`; key `diamond=` bị bỏ qua |
| Item giỏ hàng `"Swarovsky Cristall"`, `value_id` 2746464 (product 109494) | `sku: "diamond-zirconia"`, `default_title: "Zirkonia"`, nghĩa là token đã đổi tên |
| Item giỏ hàng `"Weißgold 585"`, `value_id` 2746520 | `sku: "white-585"`, `default_title: "Weißgold 585"` (trùng khớp) |

Nhãn trong giỏ hàng là `default_title` (nhãn admin), không phải bản dịch theo storefront. Vì vậy có thể tra **ID → sku** một cách xác định nếu option đó còn tồn tại.

## 4. Hệ quả và đề xuất (chờ duyệt)

1. **Không dùng `value_id` của `view_product_detail`/`add_to_cart_action` làm cấu hình người dùng chọn.** Chỉ lưu nó như `default_value_id_at_event` để làm provenance.
2. **Lựa chọn của người dùng** = token trên URL (snapshot). Đổi key `diamond` → `stone1` và dùng ID để dịch token khi token cũ đã bị đổi tên.
3. **Event có URL không chứa option** (19,624 + 360 cart-configure trong `view_product_detail`): người dùng đang xem cấu hình mặc định. Khi crawl thì dùng URL không có tham số `/catalog/product/view/id/{id}`, không cần dựng option. Lưu ý mặc định của năm 2019 có thể khác hiện tại.
4. **Item giỏ hàng / `checkout_success`:** `value_id` + `default_title` là nguồn tốt nhất cho cấu hình đã mua. Tra ID → sku qua `react_data`; option không còn tồn tại thì đánh dấu `unmappable`. Riêng 44 item `checkout_success` có `option = ""` thì không có cấu hình.
5. **Dict filter** (listing/`view_all_recommend`): loại khỏi cấu hình sản phẩm, đúng như đề xuất trước đây trong [OPEN_QUESTIONS](OPEN_QUESTIONS.md).

## 5. Giới hạn

- Đối chiếu website chỉ trên 13 sản phẩm, chọn theo hash `_id` từ 5 storefront lớn. Catalog hiện tại đã thay đổi so với 2019 (3/12 sản phẩm mất toàn bộ `option_id`), nên `is_default` hiện tại không chắc là mặc định của năm 2019.
- Pool không chứa `time_stamp`, nên chưa phân biệt được "mặc định đổi theo thời gian" với các nguyên nhân khác.
- Pool `$sample` không có seed; tỷ lệ phản ánh pool này, không phải toàn bộ 41M document.
