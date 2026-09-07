# Đặc tả Cogover Object

## Tổng quan

Cogover Object là cấu trúc dữ liệu chứa các trường mô tả thực thể kinh doanh. Tương tự như:
- Bảng trong cơ sở dữ liệu MySQL
- Sheet trong Excel/Google Spreadsheet

Mỗi Object = một Sheet trong file Excel. Các trường = các cột.

## Chi tiết loại trường

### Loại văn bản

**Short text**
- Tối đa 255 ký tự
- Dùng cho: tên, tiêu đề, mã, chức danh
- Ví dụ: Họ, Tên, Chức danh

**Long text (min, max)**
- Văn bản dài với giới hạn độ dài
- Định dạng: `Long text (0, 32000)` hoặc `Long text (0, 65000)`
- Có thể bật rich text với `Enable rich text: Yes`
- Dùng cho: mô tả, ghi chú, nội dung

### Loại số

**Number (min, max)**
- Số nguyên hoặc số thập phân
- Định dạng: `Number (0, 1000000)`
- Dùng cho: số lượng, đếm, kích thước

**Decimal**
- Số thập phân
- BẮT BUỘC dùng cho trường số dạng tiền như giá, thành tiền, tổng tiền, số dư, đã thanh toán, còn phải thu/phải trả và số tiền cấn trừ
- Không thay bằng `Number (min, max)` hoặc `Currency` chỉ vì field được định dạng/hiển thị như tiền tệ
- Dòng `Currency` trong Excel để trống; cấu hình hiển thị tiền tệ được thiết lập riêng khi import hoặc trên Workspace

**% (min, max)**
- Giá trị phần trăm
- Định dạng: `% (0, 100)`
- Dùng cho: xác suất, tỷ lệ chiết khấu, tiến độ

**Currency**
- Kiểu tiền tệ chuyên biệt
- Chỉ dùng khi người dùng yêu cầu rõ field có type `Currency`; không dùng mặc định cho trường số dạng tiền
- Khi dùng type này, BẮT BUỘC chỉ định loại tiền ở dòng 13: VND hoặc USD

**Duration**
- Khoảng thời gian tính bằng giây
- Dùng cho: thời lượng cuộc gọi, độ dài cuộc họp

### Loại ngày giờ

**Date**
- Chỉ ngày (không có giờ)
- Dùng cho: ngày sinh, ngày bắt đầu, ngày hết hạn

**Datetime**
- Ngày kèm giờ
- Dùng cho: thời gian tạo, lịch hẹn

### Boolean

**Boolean**
- TRUE hoặc FALSE
- Mặc định có thể là: True, False
- Dùng cho: trạng thái hoạt động, cờ, bật/tắt

### Loại liên hệ

**Email**
- Định dạng địa chỉ email
- Có thể cho phép nhiều giá trị
- Khi `Multiple values?: Yes`, đặt Min/Max elements

**Phone**
- Định dạng số điện thoại
- Có thể cho phép nhiều giá trị
- Dùng cho: di động, điện thoại công ty

**URL**
- Định dạng địa chỉ web
- Có thể cho phép nhiều giá trị
- Dùng cho: website, liên kết mạng xã hội

### Loại lựa chọn

**Single choice**
- Chọn đúng một tùy chọn
- YÊU CẦU bảng Selective field options bên dưới
- Dùng cho: trạng thái, loại, danh mục

**Multi choices**
- Chọn một hoặc nhiều tùy chọn
- YÊU CẦU bảng Selective field options bên dưới
- Dùng cho: thẻ, sở thích, vai trò

### Loại Lookup

**Normal lookup**
- Tham chiếu đến Object khác
- Không xóa cascade
- BẮT BUỘC chỉ định `Lookup to object`
- Dùng cho: quan hệ tùy chọn

**Dependency lookup**
- Quan hệ cha-con
- Xóa cascade: con bị xóa khi cha bị xóa
- BẮT BUỘC chỉ định `Lookup to object`
- Dùng cho: dòng chi tiết, bản ghi con

### Loại đặc biệt

**Auto number**
- ID tự động tăng
- Hệ thống tạo, không cần nhập
- Dùng cho: số thứ tự, mã bản ghi

**File**
- Tệp đính kèm
- Có thể cho phép nhiều giá trị
- Không đặt tên trường "Attachments" → dùng "Files"

**Avatar**
- Ảnh đại diện
- Tải lên một ảnh
- Dùng cho: ảnh hồ sơ

**Rating**
- Đánh giá sao (thường 1-5)
- Dùng cho: mức hài lòng, đánh giá

**Formula**
- Trường tính toán dựa trên trường khác
- Dùng cho: tổng, giá trị tính toán

**Regex**
- Kiểm tra theo mẫu
- Ràng buộc định dạng tùy chỉnh

**Label**
- Nhãn chỉ hiển thị
- Phân loại không chỉnh sửa được

## Chi tiết cấu trúc Excel

### Bố cục cột

- Cột A: Nhãn dòng (Field name, Translation, Data type, v.v.)
- Cột B trở đi: Mỗi cột = một trường

### Bố cục dòng (Bảng 1: Trường)

| Dòng | Nhãn | Nội dung |
|------|------|----------|
| 1 | Field name | Tên trường tiếng Anh |
| 2 | Translation: vi-VN | Bản dịch tiếng Việt |
| 3 | Data type | Loại trường từ danh sách trên |
| 4 | Multiple values? | Yes hoặc để trống |
| 5 | Lookup to object | Tên Object đích |
| 6 | Default | Giá trị mặc định |
| 7 | Slug | Định danh URL-safe; field record-name bắt buộc là `name` |
| 8 | Tooltip | Văn bản trợ giúp |
| 9 | Placeholder | Gợi ý nhập liệu |
| 10 | Description | Mô tả trường |
| 11 | Multiple values: Min elements | Số lượng tối thiểu |
| 12 | Multiple values: Max elements | Số lượng tối đa |
| 13 | Currency | VND hoặc USD |
| 14 | Enable rich text | Yes hoặc để trống |
| 15 | Notes | Ghi chú nội bộ |

### Bố cục dòng (Bảng 2: Thông tin Object)

Bắt đầu từ dòng 18:

| Dòng | Cột A | Cột B | Cột C |
|------|-------|-------|-------|
| 18 | Object info | | Translation: vi-VN |
| 19 | Object name | TênTiếngAnh | TênTiếngViệt |
| 20 | Plural name | TênSốNhiềuAnh | TênSốNhiềuViệt |
| 21 | "Record name" field | TênTrường | (ghi chú tùy chọn) |

### Bất biến field record-name

Mỗi Object Cogover luôn có một field tên chính (record-name). Định nghĩa Excel phải tuân thủ đồng thời các điều kiện sau:

1. Mỗi sheet có **đúng một** field record-name và field đó có `Slug` chính xác là **`name`**.
2. Dòng `"Record name" field` ở Bảng 2 ghi tên hiển thị của chính field `name` trong Bảng 1. Khi đối chiếu, bỏ dấu `*` đánh dấu bắt buộc.
3. Tên hiển thị không bắt buộc là `Name`: có thể là `Title`, `Subject`, `Membership code`, `Order number` hoặc nhãn nghiệp vụ khác. Slug kỹ thuật vẫn phải là `name`.
4. Field `name` BẮT BUỘC có type **Short text** hoặc **Auto number**; không chấp nhận Number, Long text hay type khác.
5. Chọn type theo nghiệp vụ:
   - Object con/phụ thuộc, Object trung gian (junction), dòng chi tiết hoặc bản ghi kỹ thuật: mặc định **Auto number**.
   - Object thông thường được nhận diện bằng tên/tiêu đề người dùng nhập: **Short text**.
   - Chứng từ, giao dịch hoặc bản ghi được nhận diện bằng số/mã hệ thống cấp: **Auto number**.
6. Không gán field record-name một slug riêng như `membership_code`, `title`, `subject` hoặc `order_number`. Các slug đó chỉ dùng cho field nghiệp vụ bổ sung không phải record-name.
7. Nếu chưa có field phù hợp, thêm field hiển thị phù hợp (mặc định `Name`) với `Slug: name` và type được chọn theo các quy tắc trên.

Ví dụ hợp lệ:

| Field name | Data type | Slug | `"Record name" field` |
|---|---|---|---|
| Project name* | Short text | `name` | Project name |
| Membership code* | Auto number | `name` | Membership code |
| Order number* | Auto number | `name` | Order number |

### Bố cục dòng (Bảng 3: Tùy chọn Selective)

Bắt đầu từ dòng 24 (sau 2 dòng trống):

```
Dòng 24: Selective field | TênTrường | TênTrường: vi-VN
Dòng 25: Selective field option | OptionEN | OptionVI | (state)
Dòng 26: Selective field option | OptionEN | OptionVI | (state)
...
(2 dòng trống)
Dòng N: Selective field | TrườngTiếpTheo | TrườngTiếpTheo: vi-VN
...
```

Loại trạng thái (cột 4, tùy chọn):
- `start_state` - Trạng thái khởi đầu/mặc định
- `intermediate_state` - Trạng thái đang xử lý
- `end_state` - Trạng thái kết thúc/đóng

## Mẫu Object thường gặp

### Các Object CRM tiêu chuẩn

**Lead** - Khách hàng tiềm năng
- Trường chính: Tiêu đề, Họ, Tên, Công ty, Email, Điện thoại, Trạng thái, Đánh giá, Nguồn

**Contact** - Liên hệ thuộc Tài khoản
- Trường chính: Tên, Email, Điện thoại, Tài khoản (lookup), Chức danh

**Account** - Công ty/Tổ chức
- Trường chính: Tên, Mã, Ngành, Website, Người sở hữu

**Opportunity** - Cơ hội bán hàng
- Trường chính: Tên, Tài khoản (lookup), Giai đoạn, Doanh thu dự kiến, Ngày chốt, Xác suất

**Quote** - Báo giá
- Trường chính: Tên, Tài khoản, Cơ hội, Trạng thái, Ngày hết hạn, Tổng cộng

**Contract** - Hợp đồng đã ký
- Trường chính: Tên, Tài khoản, Trạng thái, Ngày bắt đầu, Ngày kết thúc, Giá trị

**Activity** - Công việc, cuộc gọi, cuộc họp
- Trường chính: Loại, Tiêu đề, Nội dung, Bản ghi liên quan (lookups)

**Ticket** - Phiếu hỗ trợ
- Trường chính: Tiêu đề, Trạng thái, Độ ưu tiên, Liên hệ, Người xử lý

### Mẫu dòng chi tiết

Cho bản ghi con (Dòng báo giá, Dòng sản phẩm hợp đồng):

```
Object: Quote line item
Các trường:
- Quote* (Dependency lookup tới Quote)
- Product* (Dependency lookup tới Product)
- Unit (Dependency lookup tới Unit)
- Quantity (Number)
- Price per unit (Decimal)
- Discount (%)
- Subtotal (Formula, kết quả số dạng tiền)
- Total (Formula, kết quả số dạng tiền)
```

## Trường hệ thống mặc định (KHÔNG tạo)

Các trường sau do hệ thống tự quản lý, **KHÔNG** định nghĩa trong Excel:

- `created` / `created_date` - Ngày tạo bản ghi
- `updated` / `updated_date` - Ngày cập nhật bản ghi
- `created_by` - Người tạo bản ghi
- `updated_by` - Người cập nhật bản ghi

## Object hệ thống (Có sẵn)

Các Object này có sẵn - có thể tham chiếu nhưng không tạo mới:

- **Personnel** - Người dùng/nhân viên hệ thống
- **Department** - Đơn vị tổ chức
- **Queue** - Hàng đợi công việc

## Danh sách kiểm tra

Trước khi hoàn thành:

1. ☐ Tất cả lookup target tồn tại (tạo sheet cho Object mới)
2. ☐ Trường bắt buộc đánh dấu *
3. ☐ Mọi trường số dạng tiền dùng `Data type: Decimal`; dòng Currency để trống
4. ☐ Currency được chỉ định nếu người dùng yêu cầu rõ trường type Currency
5. ☐ Selective options được định nghĩa cho trường lựa chọn
6. ☐ Bản dịch đầy đủ cho tất cả trường
7. ☐ Bảng thông tin Object hoàn chỉnh (tên, số nhiều, record name)
8. ☐ Không có trường tên "Attachments" (dùng "Files")
9. ☐ Giá trị mặc định phù hợp
10. ☐ Cấu hình nhiều giá trị đúng
11. ☐ Không tạo trường hệ thống (created, updated, created_by, updated_by)
12. ☐ Mỗi sheet có đúng một field slug `name`; không có record-name slug riêng như `membership_code`, `title` hoặc `order_number`
13. ☐ Dòng `"Record name" field` trỏ đúng field slug `name` (bỏ dấu `*` khi đối chiếu tên)
14. ☐ Field `name` là Short text hoặc Auto number; Object con/phụ thuộc/junction mặc định dùng Auto number
15. ☐ Chạy `python3 scripts/validate_record_name.py <đường-dẫn-xlsx>` và không còn lỗi
