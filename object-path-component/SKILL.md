---
name: object-path-component
description: "Đọc, tạo, sửa, bật/tắt, xóa Path Component của Cogover Object qua API `/api/v1` (phiên Web App): thứ tự stage từ option field single-choice/radio-button, hướng dẫn, key fields, layout, action chain, nhóm trạng thái kết thúc. Dùng khi cần cấu hình Path Component bằng API thay vì trình duyệt; kiểm tra transition-rule constraint, xác minh sau khi ghi."
metadata:
  author: cogover
  version: "1.0.1"
---

# Object Path Component

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-11`

Quản lý Path Component của Cogover Object chỉ bằng API, không dùng trang Settings hay tự động hóa trình duyệt. Chỉ dùng tài liệu đi kèm skill, thông tin người dùng cung cấp và response API của workspace; không đọc source code, bundle hay log nội bộ để suy contract. Tài liệu và API không đủ thông tin thì dừng và báo rõ phần còn thiếu.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Mọi endpoint của skill dùng `/api/v1` bằng phiên Web App. Ngoại lệ riêng: `GET .../constraint` trả `r: 1` kèm `data` khi có transition-rule active và `r: 0` với `data: null` khi không có; không coi `r: 1` là lỗi ở endpoint này.
- Đọc [references/api-contract.md](references/api-contract.md) (endpoint, schema path/stage và `metaData`, quy tắc update, validation, mã lỗi, mẫu request) trước khi lập payload hoặc gửi request.
- Không đoán object slug, path ID, field ID, option slug, layout ID hay action ID: resolve từ response thật; nhiều kết quả cùng tên thì yêu cầu người dùng chọn, không tìm thấy thì dừng.

## Quy trình

### 1. Chốt workspace và ý định

Xác định workspace domain, thao tác `read | create | update | activate | deactivate | delete`, object và path mục tiêu. Create mà thiếu `name` hoặc `slug`: tự suy luận cả hai từ mục đích, object và field; luôn dùng tiếng Anh trừ khi người dùng chỉ định rõ ngôn ngữ khác; chuẩn hóa slug theo quy tắc ở bước 5, kiểm tra trùng trong object và tự chọn giá trị duy nhất, không dừng để xin phê duyệt. Mặc định path active: luôn gửi rõ `status: 1` trong create payload; chỉ gửi `status: 0` khi người dùng yêu cầu inactive.

### 2. Resolve object, field và option

1. `POST /api/v1/objects/object/get-by-slug` với `withFields: 1`; chỉ có tên thì phân trang `POST /api/v1/objects/object/get` rồi match chính xác tại client.
2. Chọn duy nhất field thuộc object, đang active, `fieldType` là `single_choice` hoặc `radio_button`.
3. Option lấy từ `field.options`; nếu response không kèm option, thử `POST /api/v1/objects/multiple/get` với `field_id` và `workspace_id` đã resolve. Fallback này không có trên mọi deployment: trả `404` thì dừng và báo thiếu nguồn option, không suy đoán.
4. `stage.value` là `option.slug`, không dùng nhãn hiển thị. Ghi lại `category`, `sort`, `status` và nhãn để validate/diễn giải. Response thiếu hẳn key `category`: chuẩn hóa thành `null` và xử lý stage là `intermediate`, trừ trường hợp all-null dưới đây.
5. Khi `category` của mọi option đều `null` và chưa biết option nào là start/finish: tự phán đoán từ `option.slug` và nhãn/bản dịch theo ngữ cảnh nghiệp vụ (không khớp từ khóa máy móc), không dừng để hỏi. Ngữ nghĩa vòng đời: khởi tạo (`new`, `draft`, `open`, `pending`) → `TO DO`; đang xử lý (`in_progress`, `processing`, `review`, `approval`, `active`) → `IN PROGRESS`; thành công (`approved`, `completed`, `activated`, `renewed`, `won`) → `DONE PASS`; không thành công hoặc chấm dứt (`rejected`, `failed`, `cancelled`, `expired`, `terminated`, `lost`) → `DONE FAIL`. Nếu có `constraintStages`, type `start | intermediate | finish` trong constraint là nguồn ưu tiên; suy luận ngữ nghĩa chỉ để phân biệt `DONE PASS` với `DONE FAIL` và sắp thứ tự trong cùng nhóm. Ghi rõ mapping đã suy luận trong diff/kết quả.

Tập stage: tạo mới theo hành vi UI đưa mỗi option do field trả về vào stage đúng một lần; khi sửa, giữ nguyên tập stage hiện có trừ khi người dùng yêu cầu, không tự thêm/xóa theo option mới/cũ. Stage trỏ tới option không còn tồn tại: dừng stage update và yêu cầu người dùng chọn xóa hay map sang option nào.

### 3. Đọc trạng thái hiện tại

- Tìm path bằng object slug/path slug, ID, hoặc `POST .../get` có filter object; match chính xác và phân trang đến hết.
- Luôn đọc detail `GET .../path_component?id={id}` trước update/delete; không dùng row từ list làm payload vì list thường không có `stages`.
- Sắp xếp `stages` theo `index` trước khi so sánh. Parse từng `stage.metaData` (JSON string); parse thất bại thì báo rõ và không ghi đè stage đó.
- Gọi `GET .../constraint?objectFieldId=...&objectTypeId=...`. Có transition-rule active thì so sánh tập/thứ tự/loại stage với `constraintStages`. Option all-null category: áp dụng suy luận ở bước 2 và dùng constraint để chốt type, không coi là blocker. Bất đồng khác: không tự khắc phục bằng cách đoán luồng.

### 4. Lập diff an toàn

Giữ nguyên mọi thuộc tính không được yêu cầu thay đổi. Nêu diff theo tên dễ đọc và ID/slug đã resolve.

- Chỉ đổi `name`, `status`, `description` hoặc finish-group: gửi patch tối thiểu với `id` **và `objectFieldId` hiện tại**; bỏ `stages` khỏi body.
- Có thay đổi stage: merge trên detail vừa đọc và gửi lại **toàn bộ** stage (server xóa và tạo lại stages khi `stages` không rỗng). Giữ các key không nhận biết trong JSON `metaData`, chỉ merge key mục tiêu; reindex stage từ `1` liên tiếp và `displayFields` từ `0`.
- Không đổi `slug` bằng update (endpoint update không thay đổi slug). Đổi `objectFieldId` chỉ sang field single-choice/radio-button khác **trong cùng object**, phải resolve field/option mới và gửi full stages hợp lệ cho field mới; không đổi field mà giữ stages cũ.

### 5. Validate trước khi ghi

- `status` và `finishStagesGroup` thuộc `{0,1}`; tên không rỗng, tối đa 255 ký tự; description tối đa 1000; path slug 2–100 ký tự gồm chữ thường Latin, chữ số và `_`, bắt đầu bằng chữ cái, không trùng trong cùng object.
- `index` duy nhất, liên tiếp từ 1; `value` duy nhất và khớp option slug hiện có.
- Thứ tự nhóm `TO DO` → `IN PROGRESS`/không category → `DONE FAIL`/`DONE PASS`; chỉ thay thứ tự bên trong từng nhóm.
- `displayType: 1`: từng `displayFields[].fieldId` thuộc object và không phải field điều khiển path; tạo mới dùng `required: false` trừ khi người dùng yêu cầu field bắt buộc trong path, update giữ giá trị hiện tại. `displayType: 2`: resolve `layoutId` từ layout của object có `functionLayout` là `2` hoặc `3`.
- Gán `action`: resolve ID qua danh sách button active mà UI cho phép; không dùng tên/slug button làm ID.
- Chỉ bật `finishStagesGroup` khi có ít nhất một DONE stage và `finishStagesGroupName` không rỗng; chỉ cấu hình màu cho DONE stages.
- Mã lỗi `r` nghiệp vụ: [Validation và mã lỗi](references/api-contract.md#validation-và-mã-lỗi).

### 6. Ghi và xác minh

- Gửi create/update/deactivate sau khi payload vượt validation.
- Delete: truy vấn **tất cả trang** layout dùng `componentPathSlug`; còn layout tham chiếu thì không delete và liệt kê layout cần gỡ. Không có dependency: yêu cầu xác nhận xóa rõ ràng rồi mới gửi `{ "id": "..." }`.
- Sau create/update/activate/deactivate: `GET` lại bằng ID, sort stage theo index, parse metadata và so sánh với intended state. Sau delete: xác minh ID không còn trả về.
- Chỉ báo thành công khi HTTP thành công, response code hợp lệ và read-after-write khớp. Verification lệch: báo observed state, không tự động ghi lần hai.

## Kết quả cần báo

Workspace/object/field/path đã resolve, thao tác đã gửi, diff quan trọng, ID do server trả về, kết quả verification và side effect/dependency nếu có.
