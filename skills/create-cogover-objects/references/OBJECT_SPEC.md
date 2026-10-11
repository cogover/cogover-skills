# Đặc tả Cogover Object

Cogover Object là cấu trúc dữ liệu mô tả một thực thể nghiệp vụ (tương tự bảng trong cơ sở dữ liệu hoặc sheet trong spreadsheet). Trong workbook: mỗi Object = một sheet; cột A = nhãn dòng; cột B trở đi = mỗi cột một trường.

## Cấu trúc sheet

Mỗi sheet gồm ba bảng theo thứ tự: Bảng 1 định nghĩa trường → Bảng 2 thông tin Object → Bảng 3 tùy chọn Selective field.

### Bảng 1: Định nghĩa trường (dòng 1-15)

| Dòng | Nhãn (cột A) | Nội dung |
|---|---|---|
| 1 | Field name | Tên trường tiếng Anh; trường bắt buộc thêm `*` sau tên (`Name*`) |
| 2 | Translation: vi-VN | Bản dịch tiếng Việt |
| 3 | Data type | Giá trị theo [Loại trường](#loại-trường) |
| 4 | Multiple values? | `Yes` hoặc để trống; `Yes` thì khai báo dòng 11-12 (VD Emails: 0-10) |
| 5 | Lookup to object | Tên Object đích (trường lookup) |
| 6 | Default | Giá trị mặc định |
| 7 | Slug | Định danh URL-safe; field record-name bắt buộc là `name` |
| 8 | Tooltip | Văn bản trợ giúp |
| 9 | Placeholder | Gợi ý nhập liệu |
| 10 | Description | Mô tả trường |
| 11 | Multiple values: Min elements | Số phần tử tối thiểu |
| 12 | Multiple values: Max elements | Số phần tử tối đa |
| 13 | Currency | `VND` hoặc `USD`, chỉ cho trường type Currency |
| 14 | Enable rich text | `Yes` (Long text) hoặc để trống |
| 15 | Notes | Ghi chú nội bộ |

### Bảng 2: Thông tin Object (dòng 18-21)

| Dòng | Cột A | Cột B | Cột C |
|---|---|---|---|
| 18 | Object info | (trống) | Translation: vi-VN |
| 19 | Object name | TênTiếngAnh | TênTiếngViệt |
| 20 | Plural name | TênSốNhiềuAnh | TênSốNhiềuViệt |
| 21 | "Record name" field | Tên hiển thị của field slug `name` | (ghi chú nếu cần) |

### Bảng 3: Tùy chọn Selective field (dòng 24+)

Một bảng cho mỗi trường Single choice / Multi choices, bắt đầu từ dòng 24 (sau 2 dòng trống), các bảng cách nhau 2 dòng trống:

```
Dòng 24: Selective field | TênTrường | TênTrường: vi-VN
Dòng 25: Selective field option | OptionEN | OptionVI | (state)
Dòng 26: Selective field option | OptionEN | OptionVI | (state)
...
(2 dòng trống)
Dòng N:  Selective field | TrườngTiếpTheo | TrườngTiếpTheo: vi-VN
```

- Dòng `Selective field`: cột B giữ nguyên tên trường tiếng Anh, cột C là tên tiếng Anh + `: vi-VN`; KHÔNG dịch. Đúng: `Selective field | Category | Category: vi-VN`. Sai: `Selective field | Category | Phân loại`.
- Chỉ dòng `Selective field option` mới có bản dịch tiếng Việt ở cột C.
- Cột 4 (tùy chọn) là trạng thái của option: `start_state` (khởi đầu/mặc định), `intermediate_state` (đang xử lý), `end_state` (kết thúc/đóng).

### Bất biến field record-name

Mỗi Object Cogover luôn có một field tên chính (record-name). Định nghĩa Excel phải thỏa đồng thời:

1. Mỗi sheet có **đúng một** field record-name và field đó có `Slug` chính xác là **`name`**.
2. Dòng `"Record name" field` ở Bảng 2 ghi tên hiển thị của chính field `name` trong Bảng 1; khi đối chiếu, bỏ dấu `*` đánh dấu bắt buộc.
3. Tên hiển thị không bắt buộc là `Name`: có thể là `Title`, `Subject`, `Membership code`, `Order number` hoặc nhãn nghiệp vụ khác; slug kỹ thuật vẫn phải là `name`.
4. Field `name` BẮT BUỘC có type **Short text** hoặc **Auto number**; không chấp nhận Number, Long text hay type khác.
5. Chọn type theo nghiệp vụ: Object con/phụ thuộc, Object trung gian (junction), dòng chi tiết hoặc bản ghi kỹ thuật → mặc định **Auto number**; Object thông thường nhận diện bằng tên/tiêu đề người dùng nhập → **Short text**; chứng từ, giao dịch hoặc bản ghi nhận diện bằng số/mã hệ thống cấp → **Auto number**.
6. Không gán field record-name một slug riêng như `membership_code`, `title`, `subject` hoặc `order_number`; các slug đó chỉ dùng cho field nghiệp vụ bổ sung không phải record-name.
7. Nếu chưa có field phù hợp, thêm field hiển thị phù hợp (mặc định `Name`) với `Slug: name` và type chọn theo các quy tắc trên.

Ví dụ hợp lệ:

| Field name | Data type | Slug | `"Record name" field` |
|---|---|---|---|
| Project name* | Short text | `name` | Project name |
| Membership code* | Auto number | `name` | Membership code |
| Order number* | Auto number | `name` | Order number |

## Loại trường

Giá trị hợp lệ của dòng `Data type`:

| Data type | Ghi chú | Dùng cho |
|---|---|---|
| Short text | Tối đa 255 ký tự | Tên, tiêu đề, mã, chức danh |
| Long text (min, max) | `Long text (0, 32000)` hoặc `Long text (0, 65000)`; bật rich text bằng `Enable rich text: Yes` | Mô tả, ghi chú, nội dung |
| Number (min, max) | Số nguyên hoặc thập phân, VD `Number (0, 1000000)` | Số lượng, đếm, kích thước |
| Decimal | Số thập phân; bắt buộc cho mọi trường số dạng tiền (quy tắc trong SKILL.md); dòng Currency để trống | Giá, thành tiền, số dư |
| % (min, max) | VD `% (0, 100)` | Xác suất, tỷ lệ chiết khấu, tiến độ |
| Currency | Kiểu tiền tệ chuyên biệt; chỉ khi người dùng yêu cầu rõ type Currency, không mặc định cho trường tiền; bắt buộc ghi VND hoặc USD ở dòng 13 | Trường có semantics Currency riêng |
| Duration | Khoảng thời gian tính bằng giây | Thời lượng cuộc gọi, độ dài cuộc họp |
| Date | Chỉ ngày | Ngày sinh, ngày bắt đầu, ngày hết hạn |
| Datetime | Ngày kèm giờ | Thời gian tạo, lịch hẹn |
| Boolean | TRUE/FALSE; Default có thể là True hoặc False | Cờ, bật/tắt, còn hoạt động |
| Email | Có thể nhiều giá trị (`Multiple values?: Yes` kèm Min/Max elements) | Email liên hệ |
| Phone | Có thể nhiều giá trị | Di động, điện thoại công ty |
| URL | Có thể nhiều giá trị | Website, liên kết mạng xã hội |
| Single choice | Chọn đúng một; bắt buộc có bảng Selective field options | Trạng thái, loại, danh mục |
| Multi choices | Chọn một hoặc nhiều; bắt buộc có bảng Selective field options | Thẻ, sở thích, vai trò |
| Normal lookup | Tham chiếu Object khác, không xóa cascade; bắt buộc ghi `Lookup to object` | Quan hệ tùy chọn (Tài khoản, Người sở hữu) |
| Dependency lookup | Quan hệ cha-con, xóa cascade (con bị xóa khi cha bị xóa); bắt buộc ghi `Lookup to object` | Dòng chi tiết, bản ghi con (Báo giá → Dòng báo giá) |
| Auto number | ID tự tăng do hệ thống tạo, không cần nhập | Số thứ tự, mã bản ghi |
| File | Tệp đính kèm; có thể nhiều giá trị | Tài liệu (tên trường `Files`) |
| Avatar | Tải lên một ảnh | Ảnh đại diện, ảnh hồ sơ |
| Rating | Đánh giá sao (thường 1-5) | Mức hài lòng, đánh giá |
| Formula | Trường tính toán dựa trên trường khác | Tổng, giá trị tính toán |
| Regex | Kiểm tra theo mẫu, ràng buộc định dạng tùy chỉnh | Định dạng tùy chỉnh |
| Label | Nhãn chỉ hiển thị, phân loại không chỉnh sửa được | Nhãn danh mục |

## Mẫu Object thường gặp

| Object | Trường chính |
|---|---|
| Lead (khách hàng tiềm năng) | Tiêu đề, Họ, Tên, Công ty, Email, Điện thoại, Trạng thái, Đánh giá, Nguồn |
| Contact (liên hệ thuộc Tài khoản) | Tên, Email, Điện thoại, Tài khoản (lookup), Chức danh |
| Account (công ty/tổ chức) | Tên, Mã, Ngành, Website, Người sở hữu |
| Opportunity (cơ hội bán hàng) | Tên, Tài khoản (lookup), Giai đoạn, Doanh thu dự kiến, Ngày chốt, Xác suất |
| Quote (báo giá) | Tên, Tài khoản, Cơ hội, Trạng thái, Ngày hết hạn, Tổng cộng |
| Contract (hợp đồng đã ký) | Tên, Tài khoản, Trạng thái, Ngày bắt đầu, Ngày kết thúc, Giá trị |
| Activity (công việc, cuộc gọi, cuộc họp) | Loại, Tiêu đề, Nội dung, Bản ghi liên quan (lookups) |
| Ticket (phiếu hỗ trợ) | Tiêu đề, Trạng thái, Độ ưu tiên, Liên hệ, Người xử lý |

Mẫu dòng chi tiết cho bản ghi con (Dòng báo giá, Dòng sản phẩm hợp đồng), Object `Quote line item`: Quote* (Dependency lookup tới Quote), Product* (Dependency lookup tới Product), Unit (Dependency lookup tới Unit), Quantity (Number), Price per unit (Decimal), Discount (%), Subtotal và Total (Formula, kết quả số dạng tiền).
