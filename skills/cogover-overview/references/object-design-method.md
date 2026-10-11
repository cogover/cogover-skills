# Phương pháp thiết kế Object (Database-First)

Bắt buộc khi người dùng mô tả nghiệp vụ ứng dụng và yêu cầu thiết kế Object: đóng vai chuyên gia thiết kế database, phân tích xong mới mapping sang Cogover. Khái niệm Object, quy tắc đặt tên và các module của Tầng 1: [tang1-object-manager.md](tang1-object-manager.md).

## Bước 1: Xác định entity

Từ mô tả nghiệp vụ, trích các entity chính: mỗi đối tượng cần quản lý = 1 entity; mỗi thuộc tính = 1 field; hành vi/trạng thái = workflow, lifecycle.

## Bước 2: Xác định quan hệ

| Quan hệ DB | Mapping sang Cogover |
|---|---|
| 1-N (One-to-Many) | Object con dùng `lookup_normal` hoặc `reference` đến Object cha |
| 1-N phụ thuộc: con không tồn tại nếu thiếu cha (Order line với Order) | `reference`; xác minh hành vi xoá thật trước khi triển khai |
| 1-N tham chiếu: con vẫn có ý nghĩa khi thiếu cha (Contact với Account) | `lookup_normal` |
| N-N (Many-to-Many) | `lookup_normal` có nhiều giá trị; hoặc Object trung gian nếu quan hệ có thuộc tính riêng |
| 1-1 (One-to-One) | `lookup_normal` và ràng buộc nghiệp vụ phù hợp; thường cân nhắc gộp cùng Object |

Chọn `reference` hay `lookup_normal` bằng câu hỏi: xoá bản ghi cha thì bản ghi con còn ý nghĩa không? Không → cân nhắc `reference`; Có → `lookup_normal`. Không mặc định suy ra cascade delete; đọc schema và contract thật bằng `$object-info`.

## Bước 3: Chọn kiểu dữ liệu từng cột

Chọn field type theo [Các loại Object Field](object-fields.md). Khi mapping từ schema DB:

- PK surrogate hoặc mã do hệ thống tự sinh → `auto_number`, không dùng `short_text`.
- Trạng thái, phân loại chọn 1 → `single_choice` (định nghĩa options và state types); tags, kỹ năng chọn nhiều → `multi_choices`.
- FK đến entity khác → `lookup_normal` hoặc `reference` theo Bước 2; FK đến user/nhân sự → `lookup_normal` → Personnel, xác minh metadata/default bằng `$object-info`.

## Bước 4: Thứ tự tạo Object

Object được lookup đến phải tạo trước: Object không phụ thuộc ai tạo đầu tiên; Object có lookup tạo sau Object đích; Object dùng `reference` tạo sau Object cha.

## Bước 5: Bổ sung tính năng Cogover

| Tính năng | Khi nào bổ sung |
|---|---|
| **Owner** (`lookup_normal` → Personnel) | Nghiệp vụ cần người sở hữu; xác minh default thực tế |
| **Transition Rules** | Object có trường trạng thái (Single choice với state types) |
| **UI Rules** | Cần ẩn/hiện/bắt buộc trường theo điều kiện |
| **Data Security Rules** | Cần phân quyền xem bản ghi theo owner/phòng ban/vai trò |
| **Duplicate Rules** | Cần kiểm tra trùng lặp (Email, SĐT, Mã...) |
| **Field Change History** | Cần audit trail cho trường trạng thái, giá trị, owner |
| **Layout Builder** | Luôn luôn: form tạo/xem/sửa bản ghi |
| **Actions & Sequences** | Có hành động tuỳ chỉnh trên bản ghi |

## Bước 6: Trình bày kết quả

1. Phân tích nghiệp vụ: các entity đã xác định và lý do.
2. Sơ đồ quan hệ giữa các entity (text hoặc diagram).
3. Chi tiết từng Object: trường, kiểu dữ liệu, lookup, options.
4. Thứ tự tạo Object: từ Object độc lập đến Object phụ thuộc.
5. Module bổ trợ: Transition Rules, UI Rules, Data Security, Flow...

## Ví dụ: Quản lý bảo trì thiết bị

Nghiệp vụ: công ty sản xuất cần quản lý thiết bị, lịch bảo trì định kỳ và yêu cầu sửa chữa.

- **Entity**: Equipment, Equipment category, Maintenance request, Maintenance schedule, Spare part, Part usage.
- **Quan hệ**: Equipment category → Equipment (1-N, `lookup_normal`); Equipment → Maintenance request (1-N, `lookup_normal`); Equipment → Maintenance schedule (1-N, `reference`, lịch bảo trì gắn chặt với thiết bị); Maintenance request → Part usage (1-N, `reference`); Part usage → Spare part (N-1, `lookup_normal`).
- **Kiểu dữ liệu**: Equipment: Mã thiết bị (`auto_number`), Tên (`short_text`), Loại (`lookup_normal` → Equipment category), Vị trí (`short_text`), Ngày mua (`date`), Trạng thái (`single_choice`), Owner (`lookup_normal` → Personnel). Maintenance request: Mã yêu cầu (`auto_number`), Thiết bị (`lookup_normal` → Equipment), Mô tả (`long_text`), Mức ưu tiên (`single_choice`), Trạng thái (`single_choice`), Người yêu cầu (`lookup_normal` → Personnel), Files (`file`, multiple).
- **Thứ tự tạo**: Equipment category → Spare part → Equipment → Maintenance schedule → Maintenance request → Part usage.
- **Tính năng Cogover**: Transition Rules cho Equipment.Trạng thái (chỉ cho Hoạt động ↔ Bảo trì, Bảo trì → Hỏng); Data Security (kỹ thuật viên thấy yêu cầu được gán, manager thấy tất cả); Field Change History cho Trạng thái của Equipment và Maintenance request; Triggered Flow khi có yêu cầu mới → thông báo kỹ thuật viên; Scheduled Flow nhắc bảo trì định kỳ.
