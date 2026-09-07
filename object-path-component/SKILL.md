---
name: object-path-component
description: "Đọc, tạo, sửa, kích hoạt, vô hiệu hóa và xóa Cogover object path-component qua API `/api/v{N}`; cấu hình thứ tự stage từ option của field single-choice/radio-button, hướng dẫn, key fields, layout hiển thị, action chain và nhóm trạng thái kết thúc. Dùng khi Codex cần thao tác Path Component trong Object Settings bằng API thay vì trình duyệt, bao gồm resolve object/field/option, kiểm tra transition-rule constraint, merge cấu hình an toàn và xác minh sau khi ghi."
metadata:
  author: cogover
  version: "1.0.0"
---

# Object Path Component

- **Phiên bản:** `1.0.0`
- **Ngày phát hành:** `2026-08-23`

Skill này dành cho người dùng bên ngoài. Chỉ dùng tài liệu đi kèm skill, thông tin người dùng cung cấp, cơ chế credential an toàn có sẵn và response API của workspace. Không tìm hoặc đọc source code, repository, file dự án, test, migration, database, log nội bộ, browser bundle hay source map để suy ra contract. Nếu tài liệu và API không đủ thông tin, dừng và báo rõ phần còn thiếu.

## Nguyên tắc bắt buộc

- Chỉ thao tác bằng API. Không dùng trang Settings hay tự động hóa trình duyệt.
- Đọc [references/api-contract.md](references/api-contract.md) trước khi lập payload hoặc gửi request.
- Gọi `$cogover-api-auth` trước mọi request và tuân theo interface công khai của skill đó. Vì các endpoint cấu hình dùng `/api/v1`, hãy dùng API Key duy nhất cho `POST /bapi/v1/auth-token`, sau đó gửi phiên Web App gồm ba cookie và hai header CSRF/XSRF. Không mở file triển khai của skill khác và không gửi `Authorization: Bearer {API-Key}` trực tiếp tới `/api/v1`.
- Không ghi API Key, cookie hay token thật vào file, log hoặc câu trả lời.
- Không đoán object slug, path ID, field ID, option slug, layout ID hay action ID. Resolve bằng response thật và dừng khi tên bị trùng hoặc không tìm thấy.
- Chỉ ghi khi người dùng yêu cầu thay đổi. Với yêu cầu đọc/kiểm tra, không gửi create, update hay delete.

## Quy trình

### 1. Chốt workspace và ý định

Xác định workspace domain, thao tác `read | create | update | activate | deactivate | delete`, object và path mục tiêu. Yêu cầu người dùng chọn nếu có nhiều kết quả cùng tên. Khi create mà người dùng chưa cung cấp `name` hoặc `slug`, tự suy luận và chọn cả path name lẫn slug từ mục đích, object và field. Luôn dùng tiếng Anh cho name và slug, trừ khi người dùng chỉ định rõ một ngôn ngữ khác. Chuẩn hóa slug theo quy tắc validation, kiểm tra trùng trong object và tự chọn một name/slug duy nhất; không dừng để xin phê duyệt chỉ vì thiếu name hoặc slug. Mặc định tạo path ở trạng thái active và luôn gửi rõ `status: 1` trong create payload; chỉ gửi `status: 0` khi người dùng yêu cầu path inactive.

### 2. Tạo phiên Web App

Dùng `$cogover-api-auth` để đổi API Key thành `HttpSessionId`, `XSRF-TOKEN` và `AuthToken`. Xác nhận `workspaceDomain` theo quy tắc chuẩn hóa của auth skill: response có thể là FQDN hoặc tenant label đầu của hostname. Dùng cùng giá trị `XSRF-TOKEN` cho `x-csrf-token` và `x-xsrf-token`.

### 3. Resolve object, field và option

1. Đọc object bằng `POST /api/v1/objects/object/get-by-slug` với `withFields: 1`; nếu chỉ có tên, liệt kê object rồi match chính xác tại client.
2. Chọn duy nhất field thuộc object, đang active và có `fieldType` là `single_choice` hoặc `radio_button`.
3. Lấy option từ `field.options`; nếu response không kèm option, thử `POST /api/v1/objects/multiple/get` bằng `field_id` và `workspace_id` đã resolve. Endpoint fallback không có trên mọi deployment; nếu trả `404`, dừng và báo thiếu nguồn option thay vì suy đoán.
4. Dùng `option.slug` làm `stage.value`; không dùng nhãn hiển thị. Ghi lại `category`, `sort`, `status` và nhãn hiển thị để validate/diễn giải. Khi response thiếu hẳn `category`, chuẩn hóa thành `null` và xử lý stage là `intermediate`, trừ ngoại lệ all-null ở bước tiếp theo.
5. Khi `category` của tất cả option đều là `null` và chưa biết option nào là start/finish, tự phán đoán category từ `option.slug` và nhãn/bản dịch của option; không dừng để hỏi người dùng. Ưu tiên ngữ nghĩa vòng đời: trạng thái khởi tạo như `new`, `draft`, `open`, `pending` là `TO DO`; trạng thái đang xử lý như `in_progress`, `processing`, `review`, `approval`, `active` là `IN PROGRESS`; kết quả thành công như `approved`, `completed`, `activated`, `renewed`, `won` là `DONE PASS`; kết quả không thành công hoặc chấm dứt như `rejected`, `failed`, `cancelled`, `expired`, `terminated`, `lost` là `DONE FAIL`. Dùng cả slug và bản dịch theo ngữ cảnh nghiệp vụ thay vì chỉ khớp từ khóa máy móc. Nếu có `constraintStages`, coi type `start | intermediate | finish` trong constraint là nguồn ưu tiên; chỉ dùng suy luận ngữ nghĩa để phân biệt `DONE PASS` với `DONE FAIL` và sắp thứ tự trong cùng nhóm. Ghi rõ mapping đã suy luận trong diff/kết quả.

Khi tạo mới theo hành vi UI, đưa mỗi option do field trả về vào stage đúng một lần. Khi sửa, giữ nguyên tập stage hiện có trừ khi người dùng yêu cầu thay đổi; không tự ý thêm/xóa option mới/cũ. Nếu stage trỏ tới option không còn tồn tại, dừng stage update và yêu cầu người dùng chọn xóa hay map sang option nào.

### 4. Đọc trạng thái hiện tại

- Tìm path bằng object slug/path slug, ID, hoặc `POST .../get` có filter object. Match chính xác và phân trang đến hết khi cần.
- Luôn đọc detail bằng `GET .../path_component?id={id}` trước update/delete. Không dùng row từ list làm payload vì list thường không có `stages`.
- Sắp xếp `stages` theo `index` trước khi so sánh. Parse từng `stage.metaData` như JSON string; nếu parse thất bại, báo rõ và không ghi đè stage đó.
- Gọi `GET .../constraint?objectFieldId=...&objectTypeId=...`. Nếu có transition-rule active, so sánh tập/thứ tự/loại stage với `constraintStages`. Khi tất cả option category đều `null`, áp dụng quy tắc suy luận ở bước 3 và dùng constraint để chốt type thay vì coi all-null là blocker. Với các bất đồng khác, không tự ý khắc phục bằng cách đoán luồng.

### 5. Lập diff an toàn

Giữ nguyên mọi thuộc tính không được yêu cầu thay đổi. Nêu diff theo tên dễ đọc và ID/slug đã resolve.

- Với update chỉ đổi `name`, `status`, `description` hoặc finish-group, gửi patch tối thiểu với `id` **và `objectFieldId` hiện tại**; bỏ `stages` khỏi body.
- Với bất kỳ thay đổi stage nào, merge trên detail mới đọc và gửi lại **toàn bộ** stage. Server xóa và tạo lại stages khi `stages` không rỗng.
- Giữ các key không nhận biết trong JSON `metaData`; chỉ merge key mục tiêu. Reindex stage từ `1` liên tiếp và reindex `displayFields` từ `0`.
- Không cố đổi `slug` bằng update; endpoint update hiện không thay đổi slug. Có thể đổi `objectFieldId` sang field single-choice/radio-button khác **trong cùng object**, nhưng phải resolve field/options mới và gửi full stages hợp lệ cho field mới; không đổi field mà giữ stages cũ.

### 6. Validate trước khi ghi

- Dùng `status` và `finishStagesGroup` thuộc `{0,1}`.
- Dùng tên không rỗng, tối đa 255 ký tự; description tối đa 1000 ký tự.
- Dùng path slug dài 2–100 ký tự theo dạng UI sinh ra: chữ thường Latin, chữ số và `_`, bắt đầu bằng chữ cái; kiểm tra trùng trong cùng object.
- Dùng `index` duy nhất, liên tiếp từ 1; dùng `value` duy nhất và phải khớp option slug hiện có.
- Xếp các nhóm theo `TO DO` → `IN PROGRESS`/không category → `DONE FAIL`/`DONE PASS`; chỉ thay thứ tự bên trong từng nhóm.
- Nếu `displayType: 1`, validate từng `displayFields[].fieldId` thuộc object và không phải field điều khiển path. Khi tạo mới, dùng `required: false` trừ khi người dùng yêu cầu field đó bắt buộc trong path; khi update, giữ giá trị hiện tại. Nếu `displayType: 2`, resolve `layoutId` từ layout của object có `functionLayout` là `2` hoặc `3`.
- Nếu gán `action`, resolve ID qua danh sách button active mà UI cho phép. Không dùng tên/slug button làm ID.
- Chỉ bật `finishStagesGroup` khi có ít nhất một DONE stage; nếu bật, yêu cầu `finishStagesGroupName` không rỗng. Chỉ cấu hình màu cho DONE stages.

### 7. Ghi và xác minh

- Gửi endpoint create/update/deactivate sau khi payload vượt validation.
- Trước delete, truy vấn **tất cả trang** layout dùng `componentPathSlug`. Không delete nếu còn layout tham chiếu; liệt kê layout cần gỡ. Nếu không có dependency, yêu cầu xác nhận xóa rõ ràng rồi mới gửi `{ "id": "..." }`.
- Sau create/update/activate/deactivate, `GET` lại bằng ID, sort stage theo index, parse metadata và so sánh với intended state. Sau delete, xác minh ID không còn trả về.
- Chỉ báo thành công khi HTTP thành công, response code hợp lệ và read-after-write khớp. Nếu verification lệch, báo observed state và không tự động ghi lần hai.

## Kết quả cần báo

Nêu workspace/object/field/path đã resolve, thao tác đã gửi, diff quan trọng, ID do server trả về, kết quả verification và side effect/dependency nếu có. Không hiển thị credential.
