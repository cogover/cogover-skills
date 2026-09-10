# Product batch — Schema tối thiểu cho quản lý serial và lô

## Điều kiện áp dụng

Dùng khi yêu cầu có quản lý sản phẩm theo số serial, số lô hoặc cả hai và đã xác minh Workspace đích chưa cài App Inventory. Object lưu thông tin serial/lô phải có slug **`product_batch`**; tên gốc **Product batch**, bản dịch tiếng Việt **Lô sản phẩm**. Khảo sát Object hiện có trước khi thiết kế mới để tránh trùng dữ liệu và quan hệ.

Danh sách dưới đây được đối chiếu bằng `$object-info`, qua API đọc Object/fields/options/metadata, ngày **2026-09-11**. Chỉ lưu cấu trúc đã khái quát hóa; mọi Object ID, Field ID, option ID và filter ID phải resolve lại trên Workspace đích. Đây là bằng chứng đọc schema, không phải bằng chứng đã tạo hoặc kiểm thử nghiệp vụ serial/lô.

## 10 trường nghiệp vụ tối thiểu

“Bắt buộc trong mẫu” là giá trị `required` quan sát được, không có nghĩa các trường còn lại được bỏ khỏi schema tối thiểu. Các trường trong bảng đều active, đơn giá trị, cho phép sửa thủ công và không chỉ đọc trong mẫu.

| Slug | Tên gốc / nhãn tiếng Việt | `fieldType` | Bắt buộc trong mẫu | Cấu hình và ý nghĩa |
|---|---|---|---|---|
| `name` | Name / Tên | `short_text` | Có | Record-name chuẩn; độ dài 1–255 ký tự. Giữ slug `name`, không thay bằng `serial_number` và không chuyển thành `auto_number` chỉ vì đây là Object phụ thuộc. |
| `product` | Product / Sản phẩm | `reference` | Có | Tham chiếu đơn tới Object `product`, liên kết qua `id`. Resolve Object đích và metadata quan hệ trước khi tạo. |
| `serial_number` | Serial number / Số seri | `short_text` | Không | Lưu số serial; độ dài tối đa 255 ký tự. Chốt quy tắc bắt buộc và phạm vi duy nhất theo phần bên dưới. |
| `batch_number` | Batch number / Số lô | `short_text` | Không | Lưu số lô; độ dài tối đa 255 ký tự. Chốt quy tắc bắt buộc theo chế độ quản lý lô; nhiều serial có thể cùng số lô. |
| `active` | Active / Hoạt động | `boolean` | Không | Mặc định `true`; nhãn giá trị trong mẫu là `Yes`/`No`. |
| `manufacturing_date` | Manufacturing date / Ngày sản xuất | `date` | Không | Định dạng ngày trong mẫu `dd/MM/yyyy`; không tự mặc định ngày hiện tại. |
| `expiration_date` | Expiration date / Ngày hết hạn | `date` | Không | Định dạng ngày trong mẫu `dd/MM/yyyy`; không tự mặc định ngày hiện tại. |
| `warranty_duration` | Warranty duration / Thời hạn bảo hành | `numeric` | Không | Số nguyên: `integral_length: 10`, `fractional_length: 0`. Dùng cùng `warranty_unit`. |
| `warranty_unit` | Warranty unit / Đơn vị Thời hạn bảo hành | `single_choice` | Không | Ba option `day`, `month`, `year`; mẫu không đặt option mặc định. |
| `description` | Description / Mô tả | `long_text` | Không | Văn bản thuần (`rich_text: false`), tối đa 32.000 ký tự. |

### Options của `warranty_unit`

| Slug | Giá trị gốc / `en-US` | `vi-VN` | Mặc định trong mẫu |
|---|---|---|---|
| `day` | Day | Ngày | Không |
| `month` | Month | Tháng | Không |
| `year` | Year | Năm | Không |

Sinh ID mới cho option được tạo và giữ ID của option được tái sử dụng theo `$object-info`; không mang ID của Workspace mẫu sang Workspace đích.

## Trường hệ thống

Mẫu còn có các trường dưới đây. Khi tạo Object, dùng các trường hệ thống nền tảng cung cấp; không tạo custom field trùng slug và không đưa chúng vào nhóm trường nhập liệu.

| Slug | Tên gốc / `vi-VN` | `fieldType` | Bắt buộc trong mẫu | Quan hệ / hành vi |
|---|---|---|---|---|
| `id` | ID / ID | `short_text` | Có | Định danh bản ghi; chỉ đọc, không cho sửa thủ công. |
| `created` | Created / Tạo lúc | `date_time` | Có | Thời điểm tạo; chỉ đọc, không cho sửa thủ công. |
| `updated` | Updated / Cập nhật lúc | `date_time` | Có | Thời điểm cập nhật; chỉ đọc, không cho sửa thủ công. |
| `created_by` | Created By / Tạo bởi | `lookup_normal` | Không | Liên kết tới `personnel.id`; chỉ đọc, không cho sửa thủ công. |
| `updated_by` | Updated By / Cập nhật bởi | `lookup_normal` | Không | Liên kết tới `personnel.id`; chỉ đọc, không cho sửa thủ công. |

## Chuyển schema mẫu thành thiết kế dự án

1. **Tái sử dụng và dependency:** Đọc `product_batch` và `product` trên Workspace đích. Khi cần tạo mới, thiết kế/resolve `product` trước, rồi `product_batch.product`. Không sao chép filter lookup từ mẫu; chỉ cấu hình filter đã tồn tại hoặc đã được thiết kế cho Workspace đích. Không sao chép toàn bộ metadata giữa các type; với `name`, chỉ dùng metadata hợp lệ của `short_text`.
2. **Record-name:** Khi tạo Object, dùng `name_field` với nhãn Name/Tên, type `short_text`; slug record-name do nền tảng tạo là `name`. `serial_number` và `batch_number` vẫn là hai field nghiệp vụ riêng. Chốt cách điền `name` để bản ghi có tên dễ nhận biết.
3. **Bắt buộc và chống trùng serial/lô:** Mẫu trả cả `serial_number.required: false` và `batch_number.required: false`; chốt lại theo chế độ quản lý của dự án. Chỉ quản lý lô thì không bắt buộc serial; chỉ quản lý serial thì không tự bắt buộc số lô. Chốt phạm vi duy nhất toàn Workspace hay theo `product`, quy tắc khoảng trắng/chữ hoa thường và xử lý trùng khi import/tạo đồng thời. Nếu mỗi bản ghi là một serial có gắn số lô, cho phép nhiều serial cùng lô; không áp unique đơn lên `batch_number`. Nếu mỗi bản ghi là một lô, chốt khóa nhận diện lô phù hợp. Hai trường trong mẫu có metadata `unique_rule: 1` nhưng không đủ để khẳng định đã có ràng buộc duy nhất phù hợp; xác minh cơ chế được hỗ trợ trước khi cấu hình và kiểm thử trường hợp trùng.
4. **Ngày và bảo hành:** Chốt quan hệ ngày sản xuất/hết hạn, quy tắc thời hạn bảo hành không âm và thời điểm bắt đầu tính bảo hành khi nghiệp vụ cần. Mẫu không có trường ngày bắt đầu/kết thúc bảo hành; không diễn giải `expiration_date` thành ngày hết bảo hành. Mẫu cho phép miền số âm ở `warranty_duration`; nếu yêu cầu giá trị không âm, ghi đây là thay đổi thiết kế so với mẫu. Resolve định dạng số theo Workspace đích, không hardcode mã format của Workspace mẫu.
5. **Dữ liệu và quyền:** Ghi rõ mỗi bản ghi đại diện cho một đơn vị sản phẩm có serial hay một lô gồm nhiều đơn vị sản phẩm. Nếu quản lý cả hai, chốt cách gắn serial với lô và tránh trộn hai cách biểu diễn mà không có quy tắc phân biệt. Các quan hệ với bán hàng, khách hàng, bảo hành hoặc nghiệp vụ khác chỉ bổ sung khi có yêu cầu. Thiết kế quyền và lịch sử thay đổi phù hợp; không suy ra quản lý tồn kho, dịch chuyển kho hoặc giá vốn chỉ từ sự tồn tại của `product_batch`.
6. **Bàn giao và kiểm thử:** Đưa đủ 10 trường, options, quan hệ và các quyết định khác mẫu vào data design/workbook. Khi tạo schema, dùng `$object-info` và bản dịch `en-US`/`vi-VN`; chỉ triển khai sau các gate của `$build-cogover-app`. Read-back kiểm tra slug/type/flags/metadata/options/lookup, rồi kiểm thử nhập serial/lô, chống trùng theo khóa đã chốt và các validation đã duyệt. Khi chỉ quản lý lô, kiểm tra tạo lô không cần serial; khi kết hợp, kiểm tra nhiều serial cùng lô hợp lệ. Nếu chưa chạy, ghi rõ chưa kiểm thử.
