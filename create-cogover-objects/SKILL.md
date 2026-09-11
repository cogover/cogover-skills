---
name: create-cogover-objects
description: "Tạo workbook Excel (.xlsx) định nghĩa Cogover Object: mỗi sheet một Object với trường, bản dịch Anh/Việt, selective option, quan hệ lookup và record-name slug `name`; có Log mode cho bảng log phẳng. Dùng khi cần thiết kế schema Object cho CRM/ứng dụng doanh nghiệp hoặc tạo file import Object; chạy validator kèm theo trước khi bàn giao."
metadata:
  author: cogover
  version: "1.0.2"
---

# Tạo Cogover Object

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Tạo workbook Excel định nghĩa Cogover Object: mỗi sheet một Object, mỗi cột một trường. Đặc tả cấu trúc sheet và loại trường: [references/OBJECT_SPEC.md](references/OBJECT_SPEC.md); mẫu đầy đủ 29 Object: `assets/Objects_for_CRM.xlsx` (chỉ là schema minh họa, không dùng ID hoặc credential từ mẫu để ghi vào Workspace). Đường dẫn tài nguyên resolve từ thư mục chứa `SKILL.md`.

Công cụ: dùng skill spreadsheet của môi trường nếu có; nếu không, dùng công cụ XLSX giữ được cấu trúc, kiểu dữ liệu và định dạng workbook. Không yêu cầu plugin spreadsheet theo tên cố định.

## Quy trình

1. Xác định Object và trường cần tạo; chọn chế độ: [Log mode](#chế-độ-log) khi người dùng nói "tạo bảng log", "ghi log", "log mode" hoặc tên object chứa `log`/`_log` (`product_log`, `call_log`); còn lại là Normal mode.
2. Normal mode: với mỗi `Normal lookup`/`Dependency lookup`, kiểm tra Object đích tồn tại; Object thiếu thì tạo trong sheet riêng và tạo Object phụ thuộc trước. `Personnel` (người dùng/nhân viên), `Department` (đơn vị tổ chức), `Queue` (hàng đợi công việc) là Object hệ thống có sẵn: tham chiếu được, không tạo mới. Log mode: bỏ lookup, áp bảng chuyển đổi.
3. Chọn `Data type` theo [bảng loại trường](references/OBJECT_SPEC.md#loại-trường) và [Quy tắc](#quy-tắc) bên dưới.
4. Dựng mỗi sheet theo [Cấu trúc sheet](references/OBJECT_SPEC.md#cấu-trúc-sheet): Bảng 1 định nghĩa trường (dòng 1-15) → Bảng 2 thông tin Object (dòng 18-21) → Bảng 3 tùy chọn Selective field (dòng 24+). Bẫy ở Bảng 3: dòng `Selective field` giữ tên trường tiếng Anh ở cả cột B và C (`Selective field | Category | Category: vi-VN`), chỉ dòng `Selective field option` mới dịch.
5. Xuất workbook, rồi [kiểm tra trước khi bàn giao](#kiểm-tra-trước-khi-bàn-giao).

## Quy tắc

- **Record-name**: mỗi sheet đúng một field có `Slug` là `name`, type `Short text` hoặc `Auto number`; dòng `"Record name" field` ghi tên hiển thị của chính field này (bỏ `*` khi đối chiếu). Tên hiển thị theo nghiệp vụ (`Name`, `Title`, `Subject`, `Membership code`, `Order number`...) nhưng slug luôn là `name`; không dùng slug riêng như `membership_code`, `title`, `order_number` cho record-name. Chọn type: Object con/phụ thuộc, junction, dòng chi tiết, bản ghi kỹ thuật → `Auto number`; tên/tiêu đề do người dùng nhập → `Short text`; số chứng từ/mã giao dịch do hệ thống cấp → `Auto number`. Chưa có field phù hợp thì thêm field hiển thị (mặc định `Name`) với `Slug: name`; không tạo thêm field record-name có slug khác. Chi tiết và ví dụ: [Bất biến field record-name](references/OBJECT_SPEC.md#bất-biến-field-record-name).
- **Trường số dạng tiền** (giá, thành tiền, tổng tiền, số dư, đã thanh toán, còn phải thu/phải trả, số tiền cấn trừ): `Data type` là `Decimal`, dòng `Currency` để trống (định dạng tiền tệ cấu hình riêng khi import hoặc trên Workspace). Không dùng `Number (min, max)` hay `Currency` chỉ vì field hiển thị như tiền tệ. `Currency` chỉ khi người dùng yêu cầu rõ type này, và khi đó bắt buộc ghi `VND` hoặc `USD` ở dòng 13.
- **Trường hệ thống**, KHÔNG tạo: `created`/`created_date`, `updated`/`updated_date`, `created_by`, `updated_by`.
- Không đặt tên trường `Attachments`; dùng `Files`.
- `Default`: `$currentUser` = người dùng hiện tại (trường Owner); các mặc định khác dùng giá trị thực.

## Chế độ Log

Bảng log lưu dữ liệu phẳng (denormalized), không quan hệ lookup: loại trường phức tạp đơn giản hóa thành `Short text` hoặc `Number`.

| Loại gốc | Chuyển thành |
|---|---|
| Normal lookup, Dependency lookup | Theo sample data: giá trị số → `Number`, text → `Short text` |
| Single choice | `Short text` (lưu giá trị text thay vì option) |
| Multi choices | `Short text` (các giá trị phân cách bằng dấu phẩy) |
| Currency | `Short text` (giá trị kèm đơn vị) |
| Email, Phone, URL, Formula | `Short text` |
| File, Avatar | `Short text` (URL hoặc tên file) |
| Rating | `Number (0, 5)` |
| Boolean | `Boolean` |

Giữ nguyên: Short text, Long text, Number, Decimal, %, Date, Datetime, Duration, Auto number, Boolean.

Quy tắc: KHÔNG tạo sheet phụ thuộc (lookup target); KHÔNG tạo Bảng 3 Selective field options; giữ nguyên cấu trúc Bảng 1 và Bảng 2; dòng 5 (`Lookup to object`) luôn để trống.

Ví dụ: `product_log` với cột `source=6546, default_code=VTP.KLX, name=Khăn lau xe, categ_id=60`:

```
Field name:         | Source     | Default Code* | Name*      | Category
Translation: vi-VN: | Nguồn      | Mã mặc định   | Tên        | Danh mục sản phẩm
Data type:          | Short text | Short text    | Short text | Number
```

`categ_id=60` là số → `Number`, không phải lookup.

## Mẫu thường dùng

Trường Owner và CCs (người theo dõi):

```
Field name          | Owner         | CCs
Translation: vi-VN  | Người sở hữu  | Người theo dõi
Data type           | Normal lookup | Normal lookup
Multiple values?    |               | Yes
Lookup to object    | Personnel     | Personnel
Default             | $currentUser  |
```

Trường Status với trạng thái:

```
Selective field        | Status      | Status: vi-VN
Selective field option | New         | Mới        | start_state
Selective field option | In Progress | Đang xử lý | intermediate_state
Selective field option | Closed      | Đã đóng    | end_state
```

## Kiểm tra trước khi bàn giao

- Mọi lookup target tồn tại (Normal mode); mọi trường Single choice/Multi choices có bảng option; bản dịch đầy đủ cho mọi trường; trường bắt buộc có `*`; Bảng 2 đủ tên, số nhiều, record name; giá trị mặc định và cấu hình nhiều giá trị đúng; trường tiền dùng `Decimal` với dòng Currency trống (`Currency` chỉ khi được yêu cầu rõ, kèm VND/USD); không có trường hệ thống, không có `Attachments`.
- Record-name: mỗi sheet đúng một dòng `"Record name" field`, cột B khớp đúng một field ở dòng `Field name` (bỏ `*`); field đó có đúng một `Slug: name` trong sheet và type Short text/Auto number.
- Chạy `python3 scripts/validate_record_name.py <đường-dẫn-xlsx>`; sửa mọi lỗi trước khi bàn giao.
