# Chọn Object Field trong Cogover

## Mục lục

1. [Nguyên tắc nguồn chuẩn](#nguyên-tắc-nguồn-chuẩn)
2. [Nhóm field được hỗ trợ](#nhóm-field-được-hỗ-trợ)
3. [Cách chọn field](#cách-chọn-field)
4. [Quan hệ giữa các Object](#quan-hệ-giữa-các-object)
5. [Field hệ thống và cơ cấu tổ chức](#field-hệ-thống-và-cơ-cấu-tổ-chức)
6. [Quy trình áp dụng](#quy-trình-áp-dụng)

## Nguyên tắc nguồn chuẩn

File này chỉ giúp chọn field ở mức thiết kế. Khi cần đọc schema thật, tạo, sửa, xoá field, cấu hình options, metadata, Formula hoặc quan hệ, bắt buộc dùng [$object-info](../../object-info/SKILL.md). Danh sách type và contract triển khai đầy đủ nằm trong [Object Fields API](../../object-info/references/api-object-fields.md); không sao chép payload từ overview.

Không đoán field type từ tên hiển thị. Với app hiện có, luôn đọc Object và field thật trên workspace trước khi đề xuất thay đổi.

## Nhóm field được hỗ trợ

| Nhóm | Field type | Dùng cho |
|---|---|---|
| Văn bản | `short_text`, `long_text`, `email`, `phone`, `url`, `regex`, `label` | Tên, mô tả, liên hệ, chuỗi có validation hoặc nhãn |
| Boolean | `boolean` | Cờ có/không, bật/tắt |
| Số | `numeric`, `decimal`, `currency`, `percent`, `rating`, `auto_number` | Số nguyên, số thập phân, tiền tệ, tỷ lệ, đánh giá và mã tự sinh |
| Lựa chọn | `single_choice`, `radio_button`, `multi_choices`, `checkbox`, `cascading` | Danh sách lựa chọn đơn, nhiều hoặc phân cấp |
| Ngày giờ | `date`, `date_range`, `time`, `time_range`, `date_time`, `date_time_range`, `time_duration` | Ngày, giờ, khoảng thời gian và thời lượng |
| Tệp | `file` | Tài liệu hoặc hình ảnh; hành vi ảnh/avatar được cấu hình bằng metadata của field `file` |
| Liên kết Object | `lookup_normal`, `reference` | Quan hệ tham chiếu hoặc quan hệ phụ thuộc giữa Object |
| Tính toán | `formula`, `rollup_summary` | Tính từ field cùng record hoặc tổng hợp từ records liên quan |

Tên type trong bảng phải được giữ nguyên khi làm việc với Public Object Fields API. Không dùng các tên cũ như `percentage`, `lookup_dependency` hoặc `avatar` làm API field type.

## Cách chọn field

### Văn bản

- Dùng `short_text` cho tên, mã nhập thủ công và nội dung ngắn.
- Dùng `long_text` cho mô tả, ghi chú hoặc nội dung rich text/Markdown.
- Dùng `email`, `phone`, `url` khi cần metadata và validation chuyên biệt.
- Dùng `regex` khi chuỗi phải theo một định dạng nghiệp vụ cụ thể.
- Dùng `label` cho nội dung nhãn theo contract của workspace; không xem đây là thay thế cho Display Text trong layout.

### Số

- Dùng `numeric` cho số nguyên.
- Dùng `decimal` cho số có phần thập phân.
- Dùng `currency` khi field cần metadata đơn vị tiền tệ riêng.
- Dùng `percent` cho tỷ lệ; xác minh cách lưu default theo contract của `$object-info`.
- Dùng `rating` khi UI cần thang đánh giá.
- Dùng `auto_number` cho mã hệ thống tự sinh; field này không cho sửa thủ công.

### Lựa chọn

- Dùng `single_choice` hoặc `radio_button` khi record chỉ chọn một option.
- Dùng `multi_choices` hoặc `checkbox` khi record chọn nhiều option.
- Dùng `cascading` khi options có quan hệ cha-con.
- Khi field biểu diễn trạng thái nghiệp vụ, thiết kế option trước rồi phối hợp `$object-transition-rule` và `$object-path-component` nếu cần kiểm soát hoặc trực quan hóa luồng trạng thái.

### Ngày giờ

- Chọn type đơn khi chỉ lưu một mốc; chọn type range khi phải lưu cả điểm bắt đầu và kết thúc.
- Dùng `time_duration` cho thời lượng thay vì tự ghép nhiều field số khi cần quy đổi đơn vị.
- Luôn xác minh timezone và format trên workspace đích trước khi ghi metadata.

### File, Formula và Rollup

- Dùng `file` cho tài liệu và hình ảnh; cấu hình loại file, số lượng, dung lượng, public/private và khả năng resize bằng metadata.
- Dùng `formula` cho logic tính trên record bằng **Cogover Scripting**, một ngôn ngữ kịch bản có cú pháp gần Java và hỗ trợ kiểu dữ liệu, biểu thức, điều kiện, vòng lặp cùng các hàm xử lý nghiệp vụ. Formula phù hợp cho trường tính toán phức tạp vượt quá phép tính số học đơn giản. Bắt buộc dùng `$object-info` đọc API scripting, kiểm tra cú pháp và chạy thử trên record thật trước khi lưu.
- Dùng `rollup_summary` để tổng hợp dữ liệu liên quan; resolve quan hệ và field nguồn thật trước khi thiết kế phép tổng hợp.

## Quan hệ giữa các Object

### `lookup_normal`

Dùng cho quan hệ tham chiếu thông thường. Bản ghi có thể liên kết một hoặc nhiều record của Object khác tùy cấu hình. Không suy diễn hành vi xóa cascade.

### `reference`

Dùng cho lookup phụ thuộc theo contract Public Object Fields API. Đây là type triển khai tương ứng khái niệm quan hệ cha-con/phụ thuộc trong overview; không gửi `lookup_dependency` vào API.

Trước khi tạo lookup:

1. Xác định Object cha và Object con.
2. Xác định lực lượng quan hệ: một-một, một-nhiều hoặc nhiều-nhiều.
3. Quyết định record con có tồn tại độc lập hay không.
4. Xác định related list cần hiển thị ở Object liên quan.
5. Dùng `$object-info` resolve ID, slug và contract metadata thật.

## Field hệ thống và cơ cấu tổ chức

Các Object/field hệ thống có thể hạn chế thay đổi schema, nhưng record cơ cấu tổ chức vẫn được quản lý qua API chuyên trách:

- Dùng `$user-permission` cho Personnel, Department, Position, quan hệ phòng ban-vị trí, user và Role.
- Không dùng `$object-info` hoặc `$object-record` thay cho API cơ cấu tổ chức khi `$user-permission` đã quy định endpoint riêng.
- Với Owner của Object nghiệp vụ, dùng lookup đến Personnel và xác minh metadata/default thật trên workspace; không hardcode chỉ từ overview.

## Quy trình áp dụng

1. Dùng `$object-info` đọc Object/field/option/related list hiện có.
2. Phân tích ý nghĩa nghiệp vụ, cardinality, validation, multiple và quyền sửa.
3. Chọn field type từ bảng hỗ trợ chính thức.
4. Đọc phần cấu hình type tương ứng trong `$object-info` trước khi dựng payload.
5. Đánh giá tác động tới record, layout, filter, process, Formula, security và report.
6. Tạo hoặc cập nhật field bằng skill chuyên trách.
7. Đọc lại schema và kiểm thử trên record/layout liên quan.
