# Ví dụ Velocity an toàn cho DOCX/XLSX

Minh họa cấu trúc hoàn chỉnh theo [template-syntax.md](template-syntax.md), không mở rộng contract cú pháp. Các slug như `order`, `account`, `order_product_lines`, `product` và `price_per_unit` chỉ là ví dụ: dùng `$object-info` resolve lại Object, field, lookup path và related-list slug thật trước khi dùng. Giữ nguyên cấu trúc row/paragraph của directive; ví dụ đúng về cú pháp không thay thế bước [Kiểm tra trước upload](template-syntax.md#kiểm-tra-trước-upload) (OOXML và render/preview).

## Field, lookup và format

Khối thông tin đơn hàng sau khi mọi path đã được resolve:

```velocity
Mã đơn hàng: $record.name
Khách hàng: $record.account.name
Địa chỉ giao hàng: $record.shipping_address
Ngày tạo: $record.created.format("dd/MM/yyyy")
Người sở hữu: $record.owner.last_first_name
Tổng cộng: $record.grand_total.format("#,##0")
Người xuất: $currentUser.last_first_name
```

- `$record.account.name` và `$record.owner.last_first_name` chỉ hợp lệ khi từng đoạn trung gian là lookup/field thật; chỉ gọi `.format(...)` sau khi metadata xác nhận field có kiểu tương ứng.
- `$currentUser.last_first_name` vẫn phải được resolve trên Object personnel; không giả định mọi workspace có field này.

## Khối điều kiện

Mỗi directive ở paragraph riêng trong DOCX hoặc cell/row riêng trong XLSX. Nhiều nhánh:

```velocity
#if($record.status)
Trạng thái: $record.status
#elseif($record._previous_status)
Trạng thái trước: $record._previous_status
#else
Chưa xác định trạng thái
#end
```

Không tự thêm phép so sánh, method hoặc toán tử chưa có trong contract hay một template server đã xác minh.

## Loop bảng DOCX

Giả sử `$object-info` đã xác nhận related list `order_product_lines` và các path của item. Đúng ba hàng: hàng 1 chỉ chứa `#foreach(...)`, hàng 3 chỉ chứa `#end`, hàng 2 là hàng mẫu duy nhất được nhân bản; mỗi token liền mạch trong một run hoặc các run cùng style.

| Hàng | Cột 1 | Cột 2 | Cột 3 | Cột 4 | Cột 5 |
|---:|---|---|---|---|---|
| 1 | `#foreach($item in $relatedList.order_product_lines.sort("created", "asc"))` | *(trống)* | *(trống)* | *(trống)* | *(trống)* |
| 2 | `$item.name` | `$item.product.code` | `$item.product.name` | `$item.quantity.format("#,##0.##")` | `$item.total_price.format("#,##0")` |
| 3 | `#end` | *(trống)* | *(trống)* | *(trống)* | *(trống)* |

Đặt tổng tạm tính, thuế và tổng cộng ngoài block loop; ưu tiên field tổng đã resolve từ record chính.

## Loop dòng XLSX

Vùng sản phẩm bắt đầu tại row 8; các dòng tổng nằm ngoài loop:

| Row | A | B | C | D | E | F |
|---:|---|---|---|---|---|---|
| 8 | `#foreach($item in $relatedList.order_product_lines.sort("created", "asc"))` | *(trống)* | *(trống)* | *(trống)* | *(trống)* | *(trống)* |
| 9 | `$item.name` | `$item.product.code` | `$item.product.name` | `$item.quantity.format("#,##0.##")` | `$item.price_per_unit.format("#,##0")` | `$item.total_price.format("#,##0")` |
| 10 | `#end` | *(trống)* | *(trống)* | *(trống)* | *(trống)* | *(trống)* |
| … | | | | | | |
| 19 | | | | | | `$record.subtotal.format("#,##0")` |
| 21 | | | | | | `$record.tax_amount.format("#,##0")` |
| 22 | | | | | | `$record.grand_total.format("#,##0")` |

Không để các dòng dữ liệu mẫu khác trong vùng lặp. Khi file có formula, merged cell hoặc named range gần vùng loop, mở lại và kiểm tra tham chiếu sau chuyển đổi; không kết luận an toàn chỉ từ việc workbook còn mở được.

## Chuyển file dữ liệu mẫu

Ví dụ mapping một file đơn hàng:

| Nội dung mẫu | Ý nghĩa đã xác nhận | Thay bằng |
|---|---|---|
| `SO-2026-0087` | Mã đơn hàng | `$record.name` |
| `CÔNG TY CỔ PHẦN ÁNH DƯƠNG` | Tên account lookup | `$record.account.name` |
| `15/08/2026` | Ngày tạo đơn | `$record.created.format("dd/MM/yyyy")` |
| `Laptop Lenovo ThinkBook 14 G7` | Tên product trong related item | `$item.product.name` |
| `18.500.000` | Đơn giá related item | `$item.price_per_unit.format("#,##0")` |
| `138.050.000` | Tổng cộng record | `$record.grand_total.format("#,##0")` |

Chỉ thực hiện các thay thế sau khi bảng mapping hiện hành đã được người dùng duyệt. Không suy ra field từ giá trị mẫu nếu có nhiều field hợp lý.

## Tình huống không được suy đoán

- **Số thứ tự dòng:** không dùng `$foreach.count`, `$velocityCount` hoặc biến counter khác khi contract/server reference chưa chứng minh. Resolve một field thứ tự thật; nếu không có, trình bày ứng viên như `$item.name`, để trống hoặc hỏi người dùng.
- **Thuế suất chung:** nếu record chỉ có `tax_amount` còn từng item có `tax_percent`, không tự lấy thuế suất của item đầu tiên làm thuế suất toàn đơn; chỉ giữ một tỷ lệ tĩnh sau khi người dùng xác nhận hoặc yêu cầu mapping khác.
- **Tổng tiền:** ưu tiên field tổng/rollup/formula của record như `subtotal`, `tax_amount`, `grand_total`. Không tự viết phép tính Velocity hoặc dựa vào công thức Excel đi qua vùng loop nếu chưa render thử và xác minh kết quả.
- **Lookup mơ hồ:** khi Object có cả `product.code` và `product.sku`, trình bày cả hai ứng viên; không chọn chỉ vì nhãn trong file gần giống một field.
- **Giá trị lựa chọn:** không hard-code option label từ file dữ liệu mẫu. Dùng field/option path đã resolve và để renderer lấy giá trị thật của record.
