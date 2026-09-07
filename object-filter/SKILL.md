---
name: object-filter
description: Quản lý các bộ lọc đã lưu (saved filters) của Cogover Object qua Filters API. Sử dụng khi cần xem danh sách hoặc chi tiết, tạo, cập nhật, xóa bộ lọc; thiết kế conditions, logic, sortFields, tableSettings, thứ tự và độ rộng cột theo nghiệp vụ Object; cấu hình layoutConfig/accessControls; hay kiểm tra bộ lọc sau khi ghi.
metadata:
  author: cogover
  version: "1.0.1"
---

# Object Filter

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

Quản lý bộ lọc đã lưu của Cogover Object qua `/bapi/v1/filters`. Hỗ trợ list, view, create, update và delete; không dùng skill này chỉ để lọc tạm thời một request lấy records.

## Chuẩn bị

1. Resolve `WORKSPACE_DOMAIN` và API Key theo mục quản lý credential của `$cogover-api-auth`: ưu tiên credential đã được cấp cho đúng Workspace, scoped environment hoặc secret store; không dò file dự án để tìm secret. Chỉ hỏi qua kênh an toàn khi chưa có hoặc không truy cập được.
2. Không in, ghi log hoặc đưa `API_KEY` vào câu trả lời.
3. Chuẩn hóa `WORKSPACE_DOMAIN`: bỏ protocol và dấu `/` cuối nếu có, rồi gọi API qua `https://{WORKSPACE_DOMAIN}`.
4. Xác định thao tác, object và filter đích. Nếu người dùng chỉ đưa tên, tra danh sách để lấy đúng ID; không đoán ID.
5. Dùng `$object-info` khi cần lấy `objectTypeId`, `objectTypeSlug`, field slug, `fieldType`, options hoặc metadata của field.
6. Đọc [references/api-filters.md](references/api-filters.md) trước khi tạo payload hoặc gọi endpoint. Đây là nguồn chuẩn cho schema, ràng buộc và ví dụ cURL.
7. Nếu phần mô tả condition trong API reference chưa đủ cho `fieldType` hoặc operator đang dùng, đọc [danh mục điều kiện của object-record](../object-record/records_filter_conditions.md). Áp dụng schema saved filter (`conditions`, `logicType`, `logic`) của Filters API; chỉ tái sử dụng quy tắc tương thích giữa `fieldType`, `op` và `params`, không sao chép nguyên schema request của Records API.

## Quy trình chung

1. Thu thập tối thiểu thông tin còn thiếu cho đúng thao tác. Tận dụng ngữ cảnh và API read-only trước khi hỏi người dùng.
2. Lấy metadata Object khi payload có `objectTypeId` hoặc `conditions`.
3. Kiểm tra từng condition với field thật:
   - Dùng đúng field slug và `fieldType` từ Object.
   - Dùng option slug/value mà API Object trả về cho field lựa chọn; không tự dịch hoặc tự sinh.
   - Với lookup tới người dùng hiện tại, dùng `op: "="`, `params: "$currentUser"` và đúng `fieldType`; không thêm key ngoài schema như `iu` vì UI có thể diễn giải sai condition.
   - Dùng `params: null` cho `is null` và `not null`.
   - Dùng mảng cho `in`, `not in` và `between`; kiểm tra thứ tự hai đầu của khoảng.
4. Kiểm tra `logicType`, `logic`, tối đa ba `sortFields`, `limitRecord >= 1`, độ dài tên/mô tả và kiểu dữ liệu của các cấu hình.
5. Gọi API với `Authorization: Bearer {API_KEY}` và `Content-Type: application/json`.
6. Chỉ coi thao tác thành công khi HTTP status phù hợp và response có `r: 0`. Nếu response tạo/cập nhật là resource rút gọn, không suy luận rằng trường `null` đã bị mất.
7. Trình bày kết quả ngắn gọn bằng tên, ID, object, logic, số conditions và cấu hình sắp xếp liên quan.

## Xem danh sách

Gọi `POST /bapi/v1/filters/list`.

- Nếu biết Object, ưu tiên lọc bằng `objectTypeId` và `objectTypeIdOperator: "IN"`.
- Phân trang cho đến khi đủ phạm vi người dùng yêu cầu; mặc định bắt đầu từ `page: 1`, `limit: 20`.
- Hiển thị tối thiểu: ID, name, slug, objectTypeSlug, logicType, số conditions, type, starred, status và quyền hiện tại.
- Nếu tìm theo tên mà có nhiều kết quả trùng/gần giống, đưa danh sách ứng viên thay vì tự chọn.

## Xem chi tiết

Gọi `POST /bapi/v1/filters/view` với `id`.

- Phân tích `tableSettings` từ JSON string khi cần mô tả cột hoặc sửa cấu hình bảng.
- Giữ rõ sự khác biệt giữa filter standard (`type: 1`) và filter do người dùng tạo (thường `type: 2`).
- Không tự sửa dữ liệu trong thao tác chỉ yêu cầu xem.

## Tạo bộ lọc

1. Đặt tên bộ lọc (`name`) bằng tiếng Anh theo mặc định. Chỉ dùng ngôn ngữ khác khi người dùng chủ động yêu cầu hoặc cung cấp rõ tên bộ lọc bằng ngôn ngữ đó.
2. Dùng `$object-info` để lấy và đọc đầy đủ `id`, `name`, `slug`, `description`, `nameTranslations` của Object cùng danh sách fields. Với mỗi field có thể tham gia bộ lọc hoặc bảng, đọc ít nhất `name`, `slug`, `description`, `fieldType`, `required`, `manualModifyAllow`, `readOnly`, options và metadata liên kết.
3. Xác định rõ nghiệp vụ của Object trước khi dựng payload:
   - Suy ra Object đại diện cho thực thể/giao dịch/hoạt động nào từ tên, slug, mô tả và tập fields.
   - Xác định người dùng cần nhận biết, so sánh và hành động trên thông tin nào trong màn hình danh sách.
   - Nếu tên/slug/mô tả và fields vẫn không đủ để xác định nghiệp vụ, hỏi một câu ngắn để làm rõ; không thiết kế bảng bằng cách chọn field ngẫu nhiên.
4. Thiết kế `conditions` từ metadata thật của Object. Nếu yêu cầu chưa nói rõ logic, dùng `logicType: "AND"`; chỉ dùng `OR` hoặc biểu thức `logic` khi yêu cầu nghiệp vụ cần.
5. Thiết kế thứ tự và độ rộng cột theo [references/filter-table-design.md](references/filter-table-design.md). Đây là bước bắt buộc, quan trọng ngang với conditions:
   - Chọn các cột phục vụ trực tiếp nghiệp vụ; không mặc định hiển thị tất cả fields.
   - Sắp `showingColumns` theo trình tự người dùng đọc và ra quyết định.
   - Nếu Object có field `created` đang active và người dùng không yêu cầu bỏ, thêm `created` làm cột hiển thị cuối cùng với width phù hợp cho ngày giờ; đặt trước cột hành động nếu cột hành động cũng nằm trong `showingColumns`.
   - Tạo `columns` với width riêng cho từng field dựa trên ý nghĩa và nội dung dự kiến, không dùng một width đồng loạt.
   - Bảo đảm thứ tự key trong `columns` nhất quán với `showingColumns` cho các cột hiển thị.
   - Chọn `sortFields` từ metadata và ý nghĩa nghiệp vụ, không suy ra từ field nhận diện hoặc thứ tự cột. Không mặc định sắp xếp theo `name` khi `name.fieldType` là `short-text`. Chỉ dùng `name` khi người dùng yêu cầu, nghiệp vụ xác nhận cần thứ tự chữ cái, hoặc metadata cho thấy đây là mã tuần tự như `auto_number`.
6. Mặc định hợp lý nếu người dùng không chỉ định:
   - `conditions: []`
   - `sortFields: [{"field":"created","order":"desc"}]` nếu `created` tồn tại và active; nếu không, chọn field ngày/mã tuần tự phù hợp từ metadata. Không thay bằng `name asc` chỉ vì Object là master data hoặc có field `name`.
   - `limitRecord: 20`
   - Chia sẻ quyền xem cho tất cả bằng `accessControls: [{"functions":["VIEW"],"option":1,"items":[],"type":"personnel"}]`.
   - Đặt `layoutConfig.assignment` giống hệt `accessControls`; đồng bộ thêm `objectId`, `name`, `description`, `limitRecord`, `sortFieldItems`, `layoutFilterType` và `displayTaskMode` với payload cấp cao để UI hiển thị đúng cấu hình.
   - Dùng `layoutFilterType: 1` và `displayTaskMode: 0` khi người dùng không yêu cầu chế độ khác; bỏ qua các cấu hình layout tùy chọn còn lại thay vì tự đoán.
7. Serialize `tableSettings` thành JSON string. Giữ `layoutConfig` là JSON object. Parse lại chuỗi vừa tạo để chắc chắn JSON hợp lệ trước khi gọi API.
8. Gọi `POST /bapi/v1/filters`.
9. Lấy ID từ response rồi luôn gọi endpoint view để kiểm tra trạng thái đầy đủ đã lưu, bao gồm conditions, `accessControls`, `layoutConfig.assignment`, thứ tự `showingColumns` và width trong `columns`.
10. Trả về ID, name, slug, object và tóm tắt điều kiện, sắp xếp, thứ tự cột cùng các width chính.

## Cập nhật bộ lọc

1. Gọi view ngay trước khi sửa để lấy trạng thái mới nhất và kiểm tra quyền `EDIT`.
2. Chỉ thay đổi các trường người dùng yêu cầu. Giữ nguyên các trường cấu hình còn lại khi gửi payload.
3. Không gửi `conditions: []` trừ khi người dùng muốn xóa toàn bộ điều kiện.
4. Nếu sửa `tableSettings`, parse JSON string hiện tại, cập nhật đúng key, rồi serialize lại; không ghi đè các key không liên quan.
5. Nếu tối ưu `sortFields`, kiểm tra `fieldType` và ý nghĩa nghiệp vụ trước khi đổi. Giữ nguyên sort hiện có khi chưa có căn cứ tốt hơn; không đổi sang `name asc` nếu `name` chỉ là `short-text`.
6. Gọi `PUT /bapi/v1/filters/{filter_id}`.
7. Luôn gọi view lại và so sánh các trường mục tiêu vì response update có thể rút gọn hoặc trả `conditions: null`.
8. Báo chính xác phần đã đổi và phần giữ nguyên.

## Xóa bộ lọc

1. Resolve mọi ID, gọi view từng filter và hiển thị tên, ID, Object trước khi xóa.
2. Từ chối xóa filter standard. Kiểm tra người dùng hiện tại có quyền `DELETE` cho mọi filter.
3. Yêu cầu xác nhận rõ ràng danh sách filter sẽ bị xóa vì thao tác không thể hoàn tác. Chỉ tiếp tục sau khi người dùng xác nhận.
4. Gọi `POST /bapi/v1/filters/delete` với `ids`.
5. Không diễn giải `data` trong response là số filter đã xóa; giá trị này không nhất thiết bằng số ID gửi lên.
6. Gọi list hoặc view để xác minh các filter mục tiêu không còn truy cập được.

## An toàn khi dựng payload

- Dùng công cụ tạo JSON như `jq` khi payload có JSON lồng nhau hoặc chuỗi `tableSettings`; không escape thủ công chuỗi phức tạp.
- Dùng tên trường camelCase cho create/update.
- Không đổi `objectTypeId` của filter hiện có nếu người dùng chỉ yêu cầu sửa điều kiện hay hiển thị.
- Khi tạo mới mà người dùng không chỉ định đối tượng chia sẻ, dùng mặc định chia sẻ `VIEW` cho tất cả như quy tắc ở trên. Khi cập nhật, giữ nguyên quyền hiện có trừ khi người dùng yêu cầu thay đổi.
- Không đưa field không tồn tại, field inactive hoặc option tự suy đoán vào conditions/sort/table settings.
- Với lỗi 401, 429 hoặc 500, làm theo hướng dẫn xử lý lỗi trong tài liệu tham chiếu; không lặp request ghi một cách mù quáng.

## Trả kết quả

- Với read: trả bảng hoặc danh sách gọn, kèm tổng số và thông tin phân trang nếu có.
- Với create/update: trả trạng thái đã được endpoint view xác minh, không chỉ response rút gọn của thao tác ghi.
- Với delete: nêu các ID đã gửi, kết quả xác minh và cảnh báo rõ nếu có filter không xóa được.
- Khi lỗi validation, chỉ rõ field payload gây lỗi và đề xuất giá trị hợp lệ dựa trên metadata Object hoặc response server.
