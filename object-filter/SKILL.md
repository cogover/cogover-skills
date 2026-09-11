---
name: object-filter
description: "Quản lý saved filter của Cogover Object qua Filters API `/bapi/v1/filters`: list, view, tạo, cập nhật, xóa; thiết kế conditions, logic, sortFields, tableSettings (thứ tự, độ rộng cột) theo nghiệp vụ Object; cấu hình layoutConfig/accessControls; verify bằng view sau khi ghi. Phối hợp $object-info lấy metadata; không dùng chỉ để lọc tạm thời records."
metadata:
  author: cogover
  version: "1.0.2"
---

# Object Filter

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Quản lý bộ lọc đã lưu của Cogover Object qua `/bapi/v1/filters` (API Key Bearer): list, view, create, update, delete. Không dùng skill này chỉ để lọc tạm thời một request lấy records.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Ngoại lệ riêng: `429` và timeout sau request ghi xử lý theo [Validation và lỗi](references/api-filters.md#validation-và-lỗi); `500` sau request ghi thì không tự lặp request khi chưa xác định trạng thái.
- Người dùng chỉ đưa tên filter: tra `POST /bapi/v1/filters/list` để lấy ID; nhiều kết quả trùng hoặc gần giống thì đưa danh sách ứng viên thay vì tự chọn.
- Dùng `$object-info` lấy `objectTypeId`, `objectTypeSlug`, field slug, `fieldType`, options và metadata field; bắt buộc khi payload có `objectTypeId` hoặc `conditions`.
- Đọc [references/api-filters.md](references/api-filters.md) (schema, ràng buộc, ví dụ cURL) trước khi dựng payload hoặc gọi endpoint. Nếu mô tả condition ở đó chưa đủ cho `fieldType`/operator đang dùng, đọc [danh mục điều kiện của object-record](../object-record/records_filter_conditions.md): chỉ tái sử dụng quy tắc tương thích `fieldType` + `op` + `params`; vẫn dùng schema saved filter (`conditions`, `logicType`, `logic`) của Filters API, không sao chép schema request của Records API.

## Quy tắc payload

Áp dụng cho create và update:

- Tên trường camelCase. `tableSettings` là JSON string (dựng bằng `jq` hoặc tương đương, không escape thủ công); `layoutConfig` là JSON object.
- Mỗi condition dùng field slug, `fieldType` và option slug/value thật mà API Object trả về; không tự dịch hoặc tự sinh option; không đưa field không tồn tại hoặc inactive vào conditions, sort, `tableSettings`.
- Lookup tới người dùng hiện tại: `op: "="`, `params: "$currentUser"`, đúng `fieldType`; không thêm key ngoài schema như `iu` vì UI có thể diễn giải sai condition.
- `params: null` cho `is null` và `not null`; mảng cho `in`, `not in`, `between` (kiểm tra thứ tự hai đầu khoảng).
- Kiểm tra `logicType`, `logic`, tối đa ba `sortFields`, `limitRecord >= 1`, độ dài `name`/`description` và kiểu dữ liệu của các cấu hình.
- Response create/update có thể là resource rút gọn (`conditions`, `accessControls` có thể `null`): không suy luận trường `null` đã bị mất; luôn gọi view để xác minh.

## Xem danh sách

`POST /bapi/v1/filters/list`. Biết Object thì lọc bằng `objectTypeId` và `objectTypeIdOperator: "IN"`; phân trang cho đến khi đủ phạm vi người dùng yêu cầu.

## Xem chi tiết

`POST /bapi/v1/filters/view` với `id`. Parse `tableSettings` khi cần mô tả cột hoặc sửa bảng. Phân biệt filter standard (`type: 1`) với filter người dùng tạo (thường `type: 2`).

## Tạo bộ lọc

1. Đặt `name` bằng tiếng Anh theo mặc định; chỉ dùng ngôn ngữ khác khi người dùng chủ động yêu cầu hoặc cung cấp rõ tên bằng ngôn ngữ đó.
2. Dùng `$object-info` đọc `id`, `name`, `slug`, `description`, `nameTranslations` của Object và, với mỗi field có thể vào bộ lọc hoặc bảng: `name`, `slug`, `description`, `fieldType`, `required`, `manualModifyAllow`, `readOnly`, options, metadata liên kết.
3. Xác định nghiệp vụ của Object và điều người dùng cần nhận biết, so sánh, hành động trên danh sách theo [Phân tích Object](references/filter-table-design.md#phân-tích-object). Metadata không đủ thì hỏi một câu ngắn; không thiết kế bảng bằng field chọn ngẫu nhiên.
4. Dựng `conditions` từ metadata thật. Chưa rõ logic thì `logicType: "AND"`; chỉ dùng `OR` hoặc biểu thức `logic` khi nghiệp vụ cần.
5. Thiết kế cột, thứ tự, width, pinned và `sortFields` theo [references/filter-table-design.md](references/filter-table-design.md). Bước bắt buộc, quan trọng ngang conditions.
6. Mặc định khi người dùng không chỉ định:
   - `conditions: []`, `limitRecord: 20`.
   - `sortFields: [{"field":"created","order":"desc"}]` nếu `created` tồn tại và active; nếu không, chọn field ngày hoặc mã tuần tự phù hợp từ metadata. Không thay bằng `name asc` chỉ vì Object là master data hoặc có field `name`.
   - `accessControls: [{"functions":["VIEW"],"option":1,"items":[],"type":"personnel"}]` (quyền xem cho tất cả).
   - `layoutConfig.assignment` giống hệt `accessControls`; `layoutConfig` đồng bộ `objectId`, `name`, `description`, `limitRecord`, `sortFieldItems`, `layoutFilterType`, `displayTaskMode` với payload cấp cao.
   - `layoutFilterType: 1`, `displayTaskMode: 0`; bỏ qua các cấu hình layout tùy chọn còn lại thay vì tự đoán.
7. Gọi `POST /bapi/v1/filters`, lấy ID rồi gọi view: kiểm tra conditions, `accessControls`, `layoutConfig.assignment`, thứ tự `showingColumns`, width trong `columns` và `sortFields` theo [Kiểm tra sau khi tạo](references/filter-table-design.md#kiểm-tra-sau-khi-tạo).

## Cập nhật bộ lọc

1. Gọi view ngay trước khi sửa để lấy trạng thái mới nhất và kiểm tra quyền `EDIT`.
2. Chỉ đổi trường người dùng yêu cầu; gửi kèm nguyên vẹn các trường còn lại. Không đổi `objectTypeId` khi chỉ sửa điều kiện hoặc hiển thị; giữ nguyên quyền chia sẻ trừ khi được yêu cầu.
3. Không gửi `conditions: []` trừ khi người dùng muốn xóa toàn bộ điều kiện.
4. Sửa `tableSettings`: parse JSON string hiện tại, cập nhật đúng key, serialize lại; không ghi đè key không liên quan.
5. Đổi `sortFields` chỉ khi có căn cứ `fieldType` và nghiệp vụ; không đổi sang `name asc` khi `name` chỉ là `short_text` (xem [Chọn trường sắp xếp](references/filter-table-design.md#chọn-trường-sắp-xếp)).
6. Gọi `PUT /bapi/v1/filters/{filter_id}`, rồi view lại và so sánh các trường mục tiêu; response update có thể rút gọn hoặc trả `conditions: null`.

## Xóa bộ lọc

1. Resolve mọi ID, gọi view từng filter và hiển thị tên, ID, Object.
2. Từ chối xóa filter standard; kiểm tra người dùng hiện tại có quyền `DELETE` với mọi filter.
3. Chỉ tiếp tục sau khi người dùng xác nhận rõ danh sách sẽ xóa (thao tác không hoàn tác).
4. Gọi `POST /bapi/v1/filters/delete` với `ids`. Không diễn giải `data` là số filter đã xóa; giá trị này không nhất thiết bằng số ID gửi lên.
5. Gọi list hoặc view để xác minh các filter mục tiêu không còn truy cập được.

## Trả kết quả

- List: tối thiểu ID, name, slug, objectTypeSlug, logicType, số conditions, type, starred, status và quyền hiện tại; kèm tổng số và phân trang.
- Create/update: trạng thái đã được view xác minh, không chỉ response rút gọn: ID, name, slug, object, tóm tắt điều kiện, sắp xếp, thứ tự cột và width chính. Với update, nêu rõ phần đã đổi và phần giữ nguyên.
- Delete: các ID đã gửi, kết quả xác minh và cảnh báo rõ filter không xóa được.
