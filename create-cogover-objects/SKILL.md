---
name: create-cogover-objects
description: "Tạo định nghĩa Cogover Object trong file Excel (.xlsx). Sử dụng khi cần: (1) định nghĩa cấu trúc dữ liệu cho CRM hoặc ứng dụng doanh nghiệp, (2) tạo schema Object với các trường, bản dịch và tùy chọn, (3) tạo định nghĩa trường đa ngôn ngữ Anh/Việt, hoặc (4) thiết kế quan hệ lookup giữa các Object."
metadata:
  author: cogover
  version: "1.0.1"
---

# Tạo Cogover Object

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

Tạo file Excel định nghĩa Cogover Object - cấu trúc dữ liệu cho ứng dụng CRM/doanh nghiệp.

## Bắt đầu nhanh

Đường dẫn tài nguyên được resolve từ thư mục chứa `SKILL.md`. Dùng skill spreadsheet của môi trường khi có; nếu không, dùng công cụ XLSX có thể giữ cấu trúc, kiểu dữ liệu và định dạng workbook, rồi chạy validator đi kèm. Không yêu cầu một plugin spreadsheet theo tên cố định. Workbook mẫu chỉ chứa schema minh họa, không dùng ID hoặc credential từ mẫu để ghi vào Workspace.

1. Đọc `references/OBJECT_SPEC.md` để hiểu các loại trường và cấu trúc
2. Tham khảo `assets/Objects_for_CRM.xlsx` làm mẫu
3. Tuân theo cấu trúc sheet: bảng trường → thông tin object → tùy chọn selective field

## Quy trình

```
1. Hiểu yêu cầu → cần Object nào? trường nào?
2. Xác định chế độ: Log mode hay Normal mode?
   - Log mode: nếu người dùng nói "tạo bảng log", "ghi log" hoặc tên object chứa "log"
3. Nếu Normal mode → kiểm tra lookup target, tạo Object phụ thuộc trước
   Nếu Log mode → bỏ qua lookup, áp dụng bảng chuyển đổi bên dưới
4. Tạo Excel với cấu trúc đúng cho mỗi Object
5. Kiểm tra: loại trường, bản dịch, record-name/slug `name`, tham chiếu lookup (chỉ Normal mode)
```

## Chế độ Log (Bảng ghi log)

Khi tạo bảng log, tất cả loại trường phức tạp được **đơn giản hóa** thành Short text hoặc Number. Mục đích: lưu dữ liệu phẳng (denormalized), không cần quan hệ lookup.

### Khi nào kích hoạt Log mode?
- Người dùng nói rõ: "tạo bảng log", "ghi log", "log mode"
- Tên object chứa từ `_log` hoặc `log` (VD: `product_log`, `call_log`)

### Bảng chuyển đổi loại trường

| Loại trường gốc | → Chuyển thành | Ghi chú |
|---|---|---|
| Normal lookup | **Tùy sample data**: số → `Number`, text → `Short text` | Phân tích giá trị mẫu để quyết định |
| Dependency lookup | **Tùy sample data**: số → `Number`, text → `Short text` | Tương tự |
| Single choice | `Short text` | Lưu giá trị text thay vì option |
| Multi choices | `Short text` | Lưu giá trị text, phân cách bằng dấu phẩy |
| Boolean | `Boolean` | Giữ nguyên TRUE/FALSE |
| Currency | `Short text` | Lưu giá trị kèm đơn vị dạng text |
| Email | `Short text` | |
| Phone | `Short text` | |
| URL | `Short text` | |
| Rating | `Number (0, 5)` | |
| Formula | `Short text` | |
| File / Avatar | `Short text` | Lưu URL hoặc tên file |

**Giữ nguyên**: Short text, Long text, Number, Decimal, %, Date, Datetime, Duration, Auto number, Boolean

### Quy tắc Log mode
1. **KHÔNG** tạo sheet phụ thuộc (lookup target)
2. **KHÔNG** tạo bảng Selective field options (Bảng 3)
3. Giữ nguyên cấu trúc Bảng 1 (trường) và Bảng 2 (thông tin object)
4. Dòng 5 (Lookup to object) luôn để trống

### Ví dụ Log mode

Yêu cầu: `product_log` với cột `source=6546, default_code=VTP.KLX, name=Khăn lau xe, categ_id=60`

Kết quả:
```
Field name:         | Source       | Default Code* | Name*      | Category
Translation: vi-VN: | Nguồn        | Mã mặc định   | Tên        | Danh mục sản phẩm
Data type:          | Short text   | Short text     | Short text | Number
```
→ `categ_id=60` là số → dùng `Number` (không phải lookup)

## Cấu trúc Sheet (Mỗi Object)

Mỗi sheet = một Object. Các thành phần bắt buộc:

### Bảng 1: Định nghĩa trường (Dòng 1-15)
- Dòng 1: `Field name` + tên trường (tiếng Anh)
- Dòng 2: `Translation: vi-VN` + bản dịch tiếng Việt
- Dòng 3: `Data type` + loại trường
- Dòng 4: `Multiple values?` (Yes/để trống)
- Dòng 5: `Lookup to object` (cho trường lookup)
- Dòng 6: `Default` giá trị mặc định
- Dòng 7: `Slug`
- Dòng 8: `Tooltip`
- Dòng 9: `Placeholder`
- Dòng 10: `Description`
- Dòng 11: `Multiple values: Min elements`
- Dòng 12: `Multiple values: Max elements`
- Dòng 13: `Currency` (VND/USD cho trường Currency)
- Dòng 14: `Enable rich text` (Yes cho Long text)
- Dòng 15: `Notes`

### Bảng 2: Thông tin Object (Dòng 18-21)
```
Dòng 18: Object info | (trống) | Translation: vi-VN
Dòng 19: Object name | TênTiếngAnh | TênTiếngViệt
Dòng 20: Plural name | TênSốNhiềuAnh | TênSốNhiềuViệt
Dòng 21: "Record name" field | TênTrường | (ghi chú nếu cần)
```

> **Bất biến record-name của Cogover**:
> - Mỗi Object phải có **đúng một** field record-name với `Slug` chính xác là **`name`**. Dòng `"Record name" field` phải trỏ tới chính field này.
> - Tên hiển thị của field có thể theo nghiệp vụ như `Name`, `Title`, `Subject`, `Membership code`, `Order number`... nhưng slug kỹ thuật vẫn luôn là `name`. Không dùng slug riêng như `membership_code`, `title` hay `order_number` cho field record-name.
> - Field `name` chỉ được có type **Short text** hoặc **Auto number**.
> - Với Object con/phụ thuộc, Object trung gian (junction), dòng chi tiết hoặc Object chỉ dùng làm bản ghi kỹ thuật, mặc định chọn **Auto number**.
> - Với Object thông thường, chọn theo ngữ nghĩa: tên/tiêu đề do người dùng nhập → **Short text**; số chứng từ/mã giao dịch/mã bản ghi do hệ thống cấp → **Auto number**.
> - Nếu chưa có field phù hợp, tự thêm một field hiển thị phù hợp (mặc định `Name`) với `Slug: name`; không tạo thêm field record-name có slug khác.

### Bảng 3: Tùy chọn Selective Field (Dòng 24+)
Cho mỗi trường Single choice / Multi choices:
```
Dòng N:   Selective field | TênTrường | TênTrường: vi-VN
Dòng N+1: Selective field option | Option1 | Option1_VN
Dòng N+2: Selective field option | Option2 | Option2_VN
...
(2 dòng trống giữa các bảng option)
```

> **QUAN TRỌNG về format dòng Selective field (dòng N):**
> - Cột B: giữ nguyên tên trường tiếng Anh (KHÔNG dịch)
> - Cột C: tên trường tiếng Anh + `: vi-VN` (KHÔNG dịch sang tiếng Việt)
> - Ví dụ đúng: `Selective field | Category | Category: vi-VN`
> - Ví dụ SAI: `Selective field | Category | Phân loại` ← KHÔNG dịch tên trường ở header
>
> Chỉ các dòng **Selective field option** mới có bản dịch tiếng Việt ở cột C.

## Tham khảo loại trường

| Loại | Mô tả | Ví dụ |
|------|-------|-------|
| Short text | Văn bản ngắn ≤255 ký tự | Tên, Tiêu đề |
| Long text (min, max) | Văn bản dài với giới hạn | Long text (0, 32000) |
| Number (min, max) | Số với khoảng giá trị | Number (0, 1000000) |
| % (min, max) | Phần trăm | % (0, 100) |
| Decimal | Số thập phân; bắt buộc dùng cho trường số dạng tiền | Giá, thành tiền, số dư |
| Currency | Kiểu tiền tệ chuyên biệt; chỉ dùng khi người dùng yêu cầu rõ type Currency | Trường có semantics Currency riêng |
| Date | Chỉ ngày | Ngày sinh |
| Datetime | Ngày + giờ | Thời gian tạo |
| Duration | Khoảng thời gian | Thời lượng cuộc gọi |
| Boolean | TRUE/FALSE | Còn hoạt động |
| Email | Địa chỉ email | Email liên hệ |
| Phone | Số điện thoại | Di động |
| URL | Địa chỉ web | Website |
| Single choice | Chọn một | Trạng thái |
| Multi choices | Chọn nhiều | Thẻ |
| Normal lookup | Liên kết tới Object | Tài khoản |
| Dependency lookup | Liên kết cha (xóa cascade) | Báo giá → Dòng báo giá |
| Auto number | ID tự tăng | Số thứ tự |
| File | Tải lên tệp | Tài liệu |
| Avatar | Ảnh đại diện | Ảnh |
| Rating | Đánh giá sao | Mức hài lòng |
| Formula | Trường tính toán | Tổng cộng |
| Regex | Kiểm tra theo mẫu | Định dạng tùy chỉnh |
| Label | Nhãn hiển thị | Nhãn danh mục |

## Quy tắc quan trọng

1. **Trường số dạng tiền**: Luôn khai báo `Data type` là **`Decimal`** cho các field lưu số tiền như giá, thành tiền, tổng tiền, số dư, đã thanh toán, còn phải thu/phải trả hoặc số tiền cấn trừ. Không dùng `Number (min, max)` và không dùng `Currency` chỉ vì field được định dạng/hiển thị như tiền tệ. Dòng `Currency` để trống đối với field `Decimal`; định dạng tiền tệ được cấu hình riêng khi import hoặc trên Workspace.

2. **Trường hệ thống mặc định**: KHÔNG tạo các trường sau vì hệ thống tự quản lý:
   - `created` / `created_date` (ngày tạo)
   - `updated` / `updated_date` (ngày cập nhật)
   - `created_by` (người tạo)
   - `updated_by` (người cập nhật)

3. **Kiểm tra lookup**: Nếu tạo `Normal lookup` hoặc `Dependency lookup`, kiểm tra Object đích có tồn tại. Tạo Object thiếu trong sheet riêng.

4. **Đặt tên trường**: Không dùng "Attachments" → dùng "Files" thay thế

5. **Trường bắt buộc**: Đánh dấu `*` sau tên trường (VD: `Name*`)

6. **Giá trị mặc định**:
   - `$currentUser` = người dùng hiện tại (cho trường Owner)
   - Dùng giá trị thực cho các mặc định khác

7. **Loại trạng thái selective field** (cột 4 tùy chọn):
   - `start_state` = trạng thái khởi đầu
   - `intermediate_state` = đang xử lý
   - `end_state` = trạng thái kết thúc

8. **Cấu hình nhiều giá trị**:
   - Đặt `Multiple values?` = Yes
   - Định nghĩa Min/Max elements (VD: 0-10 cho Emails)

9. **Xác minh record-name trước khi bàn giao**:
   - Mỗi sheet có đúng một dòng `"Record name" field` và giá trị ở cột B khớp một field trong dòng `Field name` (bỏ dấu `*` khi so sánh).
   - Field được chọn có đúng một `Slug: name` trong sheet và type là `Short text` hoặc `Auto number`.
   - Sau khi xuất workbook bằng skill spreadsheet sẵn có hoặc thư viện XLSX tương đương, chạy `python3 scripts/validate_record_name.py <đường-dẫn-xlsx>`; mọi lỗi phải được sửa trước khi bàn giao.

## Mẫu thường dùng

**Trường Owner:**
```
Field name: Owner
Translation: vi-VN: Người sở hữu  
Data type: Normal lookup
Lookup to object: Personnel
Default: $currentUser
```

**Trường Status với trạng thái:**
```
Selective field | Status | Status: vi-VN
Selective field option | New | Mới | start_state
Selective field option | In Progress | Đang xử lý | intermediate_state
Selective field option | Closed | Đã đóng | end_state
```

**Trường CCs (người theo dõi):**
```
Field name: CCs
Translation: vi-VN: Người theo dõi
Data type: Normal lookup
Multiple values?: Yes
Lookup to object: Personnel
```

## Xem thêm

- `references/OBJECT_SPEC.md` - Đặc tả đầy đủ các loại trường
- `assets/Objects_for_CRM.xlsx` - Ví dụ đầy đủ với 29 Object
