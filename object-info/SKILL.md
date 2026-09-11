---
name: object-info
description: "Xem Object Cogover cùng fields, options, metadata, related lists và nhận diện Object đặc biệt của Workspace; tạo, cập nhật, xoá mềm/khôi phục/xoá thực tế Object và field qua `/bapi/v1`, gồm options và Formula (kiểm tra cú pháp, chạy thử trên record trước khi lưu). Dùng khi cần Object/field ID, slug, schema hoặc metadata cho skill khác."
metadata:
  author: cogover
  version: "1.0.2"
---

# Object Info

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Xem và quản lý cấu trúc Object Cogover qua `/bapi/v1` (API Key Bearer): xem Object cùng fields, options, metadata, related lists; tạo, sửa, xoá mềm, khôi phục, xoá thực tế Object hoặc field; tạo/cập nhật options của field lựa chọn; viết và kiểm tra Formula. Skill khác gọi `$object-info` để lấy Object ID, field slug, `fieldType`, options, metadata hoặc quan hệ trước khi dựng payload nghiệp vụ. Object phổ biến: Lead, Quote, Order, Product, Personnel, Contact, Account, Opportunity, Task.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Riêng kiểm tra cú pháp và chạy thử Formula dùng `/api/v1` bằng phiên Web App đổi từ API Key, xem [references/formula-validation.md](references/formula-validation.md).
- Ngoại lệ riêng: `429` tôn trọng rate limit; `500`, timeout hoặc lỗi mạng sau request ghi thì không lặp mù, chỉ thử lại có kiểm soát khi thao tác an toàn; create có kết quả không rõ phải tra lại Object và slug trước khi thử lại để tránh tạo trùng.
- Tra Object và field thật (Phần 1) trước khi dùng ID hoặc slug; nhiều kết quả gần giống thì đưa danh sách ứng viên để làm rõ, không tự chọn.

## Phần 1 — Xem Object và fields

`POST /bapi/v1/objects/list`; body lấy đủ cấu trúc:

```json
{"pageSize": 2000, "includeFields": true, "includeRelatedLists": true, "includeOptions": true, "includeMetaData": true}
```

Chỉ yêu cầu phần cần dùng để giảm response:

| Tham số | Mặc định | Cách dùng |
|---|---:|---|
| `pageSize` | `2000` | Giới hạn số Object trả về |
| `keywords` | `[]` | Tìm mờ, không phân biệt hoa thường theo `name`, `slug`, `nameTranslations`; dùng để khám phá |
| `slugs` / `ids` | `[]` | Lọc chính xác theo Object slug / Object ID; ưu tiên khi đã xác định Object |
| `includeFields` | `false` | Trả `fields` của mỗi Object |
| `includeRelatedLists` | `false` | Trả `relatedLists` của mỗi Object |
| `includeOptions` | `true` | Trả options khi `includeFields=true` |
| `includeMetaData` | `true` | Trả metadata khi `includeFields=true` |
| `includeNonStandard` | `true` | `false` để chỉ lấy Object tiêu chuẩn |
| `includeWorkflowObjects` | `false` | `true` để gồm Workflow Object |

Từ `items[]` trích tối thiểu:

- Object: `id`, `name`, `slug`, `nameTranslations`, mô tả nếu có.
- Field: `id`, `name`, `slug`, `fieldType`, `nameTranslations`, `required`, `status`, `description`, `multiple`, `readOnly`, `manualModifyAllow`, `defaultValue`, options, metadata.
- Option của field lựa chọn: `id`, `value`, `slug`, `isDefault`, trạng thái, màu/icon, bản dịch.
- Related list: `id`, `name`, `slug`, `status`, `sort`, `displayColumn`, `minRecord`, `maxRecord`, Object/field nguồn, Object lookup, `lookupType`.

Field có trong response đọc chưa chắc ghi được: Object có thể chứa field hệ thống, field chuẩn, field read-only hoặc `fieldType` mà Object Fields API không hỗ trợ tạo mới.

Trả kết quả:

- Hỏi một Object: chỉ Object đó và field liên quan, bảng gọn nếu nhiều field. Hỏi nhiều Object: tóm tắt Object trước, mở rộng fields theo phạm vi yêu cầu.
- Skill khác gọi: trả dữ liệu có cấu trúc, giữ nguyên ID, slug, `fieldType`, option slug/value và metadata cần thiết; không dịch hoặc tự sinh giá trị kỹ thuật.
- Không tìm thấy: nêu bộ lọc đã dùng thay vì kết luận Object không tồn tại trong toàn workspace.

## Object đặc biệt của Workspace cần nắm

Các Object nền tảng hoặc dùng chung sau không phải Object nghiệp vụ thông thường; không tạo bản sao khi Object tương ứng đã tồn tại.

| Object slug | Ý nghĩa | Lưu ý sử dụng |
|---|---|---|
| `Process_Debug_data` | Dữ liệu debug khi chạy Process | Dữ liệu kỹ thuật, không dùng làm master data; giữ nguyên slug và cách viết hoa/thường đọc từ Workspace |
| `global_settings` | Cấu hình dùng chung mức Workspace hoặc ứng dụng | Đọc schema và records thật trước khi dùng; không suy đoán cấu trúc cấu hình giữa các Workspace |
| `app_user` | Danh tính người dùng ứng dụng | Khác `account` (doanh nghiệp, tổ chức hoặc khách hàng trong CRM) |
| `notification_channel` | Kênh gửi thông báo | Kiểm tra Object/quan hệ thành viên kênh đang có trước khi tích hợp hoặc tạo dữ liệu |
| `activity` | Hoạt động trên một bản ghi nghiệp vụ (hợp đồng, lead, cơ hội, công việc): ghi chú, email, cuộc gọi, task, cuộc họp, SMS hoặc chat | Muốn Object có khu vực thảo luận/ghi chú/hoạt động: tạo lookup từ `activity` tới Object đó rồi đưa Related List được sinh ra vào layout Xem/Sửa, theo mục dưới |
| `activity_comment` | Bình luận gắn với một bản ghi `activity` | Dữ liệu con của Activity; không dùng thay quan hệ trực tiếp giữa `activity` và Object nghiệp vụ |

### Bổ sung Activity cho một Object nghiệp vụ

Quy trình 5 bước (đọc hai Object thật, tạo `lookup_normal` trên `activity`, xác minh Related List sinh ra, đưa component `related_list` vào layout Xem/Sửa qua `$object-layout`, cấu hình timeline/loại hoạt động): [references/activity-related-list.md](references/activity-related-list.md).

## Quy tắc chung cho thao tác ghi (Phần 2 và 3)

- Đọc contract trước khi dựng payload hoặc gọi endpoint: field theo [references/api-object-fields.md](references/api-object-fields.md) (field types, schema, metadata, translations, giới hạn, mã lỗi, ví dụ cURL); Object theo [references/api-objects.md](references/api-objects.md) (schema create/update, `delete_type`, giới hạn standard Object, mã lỗi).
- Dùng Phần 1 ngay trước thao tác: create kiểm tra trùng (field: tên tiếng Anh, tên được dịch, `slug` dự kiến; Object: `name`, `plural_name`, `slug`); update/delete/restore lấy ID thật cùng type, slug, trạng thái, metadata, standard/custom và quan hệ hiện tại. `object_type_id` là Object ID thật, không dùng tên hoặc slug thay ID.
- Đánh giá tác động trước khi đổi `slug`, `type`, `unique`, `multiple`, trạng thái, quan hệ cha, composite key, xoá field/Object hoặc xoá options đã có dữ liệu/tham chiếu: records, fields, relationships, filters, workflows, formulas, layouts, related lists, Object relations, buttons, Object Picker và skill/cấu hình đang tham chiếu.
- Kiểu dữ liệu: cờ số `0`/`1` cho `required`, `multiple`, `unique`, `status`, `creatable`, `editable`, `viewable`, `read_only`, `is_standard`, `is_display`, `quickSearch` (field) và `status`, `creatable`, `editable`, `viewable`, `quick_search` (Object); Object `type` nhận `0`, `1` hoặc `2`. Boolean nghiêm ngặt `true`/`false` chỉ với `manual_modify_allow` (field) và `standard_fields`, `standard_layout`, `standard_buttons`, `standard_filter` (Object). Giữ nguyên cách viết `quickSearch`; các key còn lại chủ yếu `snake_case`.
- `meta_data` (kể cả `name_field.meta_data`) là JSON string, không gửi JSON object. Khi sửa: parse metadata hiện tại, merge đúng key cần đổi, kiểm tra lại theo type rồi serialize toàn bộ; không gửi một phần vì server thay toàn bộ chuỗi đã lưu. Ngoại lệ: standard Object chỉ nhận các metadata key được reference cho phép và API tự merge.
- Sau request ghi: mong đợi HTTP `201` (create) hoặc `200` (update, delete, restore) cùng `r: 0`, rồi dùng Phần 1 đọc lại và so sánh trước/sau; không dựa riêng vào response rút gọn.

### Ngôn ngữ gốc và bản dịch khi tạo

Áp dụng khi tạo field, tạo Object hoặc chuẩn bị tên/metadata cho luồng tạo khác:

- Dữ liệu gốc có thể dịch (`name`, plural name, `description`, `tool_tip`, `hint_text`, option `value` và nhãn tương tự) dùng tiếng Anh; nội dung người dùng đưa bằng ngôn ngữ khác thì dịch sang tiếng Anh làm giá trị gốc. `slug` kỹ thuật tạo từ tên hoặc value tiếng Anh, ưu tiên ASCII `lower_snake_case`; `slug` không có bản dịch.
- `translations[]` luôn có `en-US` với giá trị tiếng Anh tương ứng dữ liệu gốc; nội dung nguồn không phải tiếng Anh thì gửi thêm nguyên nội dung người dùng ở đúng locale nguồn (tiếng Việt: `vi-VN`). Field tối thiểu dịch `name` và giữ đủ mọi thuộc tính người dùng đã cung cấp (`name`, `description`, `tooltip`, `placeholder`); option chỉ dịch `value`. Không bịa nội dung còn thiếu chỉ để làm đầy bản dịch.
- API không tự dịch: tự dựng giá trị gốc và `translations[]`, rồi xác minh field cùng từng option sau khi tạo. Không xác định chắc ngôn ngữ/locale thì hỏi trước khi ghi.
- Người dùng chỉ định rõ tên hoặc slug kỹ thuật phải là giá trị gốc: tôn trọng, vẫn thêm bản dịch cho nội dung hiển thị không phải tiếng Anh nếu API hỗ trợ.

Ví dụ người dùng yêu cầu field `Số tiền`:

```json
{"name": "Amount", "slug": "amount", "description": "", "manual_modify_allow": true,
 "translations": [{"language": "en-US", "name": "Amount"}, {"language": "vi-VN", "name": "Số tiền"}]}
```

### Mặc định khi tạo field

Khi người dùng không chỉ định khác và type không có ràng buộc đặc thù, gửi tường minh thay vì để server tự áp dụng: `manual_modify_allow: true` (tôn trọng ngoại lệ của API, ví dụ `auto_number` luôn bị đặt `false`), `description: ""` khi không có mô tả, `translations[]` có ít nhất `en-US` và locale nguồn nếu khác tiếng Anh.

#### Định dạng hiển thị số theo Workspace

- Yêu cầu “Theo cấu hình chung của Workspace”: không tự suy ra hoặc hardcode `meta_data.format.format` từ ví dụ API, field cũ khác type hay workspace khác; mã format là giá trị UI phụ thuộc cấu hình/phiên bản và có thể biểu diễn một kiểu phân nhóm số cụ thể. Đọc một field `numeric`/`decimal` đã được người dùng xác nhận đúng trong chính workspace rồi sao chép nguyên object `metaData.format`; chưa có field mẫu đáng tin cậy thì yêu cầu người dùng xác nhận, không đoán mã (mẫu ẩn danh chỉ để tham khảo, xem ghi chú tại [api-object-fields.md](references/api-object-fields.md#numeric-và-decimal)).
- Xoá field `currency` để tạo lại thành `decimal`: lấy lại field nguồn ngay trước khi xoá để giữ tên, slug, mô tả, bản dịch, cờ, default và giới hạn âm/dương; `format` chỉ lấy từ field mẫu `decimal` đã xác nhận, không kế thừa mã format của `currency`.
- Sau khi tạo, đọc lại field và đối chiếu cả `metaData.format`, `integral_length`, `fractional_length`, `display_type`, `display_as_currency`; `r: 0` của create chưa đủ để coi hoàn tất.

### Xoá hoặc khôi phục field và Object

1. Resolve và hiển thị định danh trước thao tác: field gồm Object, tên, ID, slug, type, trạng thái; Object gồm tên, ID, slug, trạng thái, standard/custom và các dependency đã phát hiện.
2. Yêu cầu người dùng xác nhận rõ mục tiêu và `delete_type` trước khi gọi endpoint; người dùng chỉ nói “xoá” thì khuyến nghị `delete_type: 1`.
3. Gọi `POST /bapi/v1/object-fields/delete` (field) hoặc `POST /bapi/v1/objects/delete` (Object) với `{"data": [{"id": "{FIELD_ID hoặc OBJECT_ID}", "delete_type": 1}]}`.

   | `delete_type` | Ý nghĩa |
   |---|---|
   | `1` | Soft delete: chuyển sang pending delete và đặt lịch xoá thực tế sau 14 ngày |
   | `2` | Khôi phục bản đã soft delete về trạng thái trước đó và huỷ lịch xoá |
   | `3` | Actual delete: field bị dọn quan hệ/cấu hình liên quan và xoá dữ liệu khỏi records; Object bị xoá cấu hình liên quan và dữ liệu records. Chỉ dùng sau khi người dùng xác nhận rõ xoá thực tế và đã được cảnh báo không thể khôi phục |

4. Mong đợi HTTP `200`, `r: 0`, rồi tra lại bằng ID/slug (Phần 1) để xác minh trạng thái sau soft delete/restore hoặc không còn tồn tại sau actual delete. Object vắng mặt trong một list mặc định chưa đủ làm bằng chứng nếu bộ lọc có thể loại pending-delete Object.
5. Riêng field: API trả `r: 524` thì trình bày đầy đủ cảnh báo về nơi field đang được sử dụng và không coi thao tác thành công. Riêng Object: không xoá standard Object; Object đang được Object Picker, field, relationship, filter, workflow hoặc thực thể khác tham chiếu thì báo dependency và không tuyên bố thao tác thành công.

### Xử lý lỗi và báo cáo

- `r != 0`: dùng bảng mã lỗi trong reference tương ứng để chỉ rõ field hoặc ràng buộc gây lỗi (với Object đặc biệt là trùng tên/slug, Object pending delete, standard Object, Object Picker dependency, giới hạn gói thuê bao); không chỉ báo “HTTP 400”.
- Backend chặn do dependency hoặc validation của options: nói rõ phần đã làm, phần chưa làm và mã lỗi; không tuyên bố hoàn tất khi danh sách options sau ghi không khớp trạng thái đích.
- Create/update: báo ID, name (Object thêm plural name), slug, type và Object chứa field (với field), trạng thái đã được API đọc xác minh; có options thì báo số lượng tạo/cập nhật/xoá và kết quả đối chiếu danh sách cuối.
- Delete/restore: báo `delete_type`, ID đã gửi, kết quả xác minh, thời hạn 14 ngày nếu soft delete và mọi dependency/cảnh báo còn lại.

## Phần 2 — Tạo, sửa, xoá fields của Object

Options (create và update): chỉ gửi `options` ở top-level cho `single_choice`, `radio_button`, `multi_choices`, `checkbox` hoặc `cascading`; request có `options` bắt buộc kèm `type` hiện tại hoặc type đích hợp lệ; không đặt options trong `meta_data`, không gọi URI riêng cho options. Không có key `options` thì giữ nguyên danh sách; có key thì mảng thay thế toàn bộ (option vắng mặt bị xoá); `options: []` xoá toàn bộ, chỉ gửi khi người dùng yêu cầu rõ và đã xác nhận tác động dữ liệu. Sửa một phần: đọc danh sách hiện tại ngay trước thao tác, giữ nguyên ID option cần bảo toàn, tạo UUID cho option mới, merge rồi gửi lại toàn bộ mảng; không dùng ID mới để biểu diễn việc sửa một option hiện có.

### Tạo field

1. Chuẩn hoá tên gốc, slug và bản dịch theo mục Ngôn ngữ; chọn `type` được API hỗ trợ và đọc cấu hình riêng của type đó trong reference, không suy metadata của type này từ type khác.
2. Gửi `type`, `object_type_id`, `name` tiếng Anh và các giá trị ở mục Mặc định. Có thể để server sinh `slug` từ tên tiếng Anh và tự tính `sort`; chỉ gửi slug kỹ thuật hoặc cấu hình tuỳ chọn khi cần, nhưng không dựa vào server cho các mặc định đã quy định.
3. Field lựa chọn: gửi đủ options ở top-level; mỗi option mới có UUID riêng và `value`; tối đa 200 options, không trùng ID/value, `sort > 0` nếu gửi, cờ số hợp lệ, slug duy nhất; `cascading` flatten cây và `parent_id` trỏ đúng option cha. Không tự bịa options khi người dùng chưa cung cấp.
4. `lookup_normal`/`reference`: resolve Object đích, gửi `related_list_name`, xác minh metadata quan hệ trước khi tạo.
5. `formula`: viết `meta_data.script` theo [Cogover Scripting API Reference](references/cogover-scripting-api-vi.md), đọc mục 1–4 (nền tảng cú pháp) và mục 14 (giới hạn, an toàn) rồi đọc đầy đủ các mục hàm/kiểu dữ liệu cùng recipe liên quan tới công thức (định vị qua Mục lục đầu file); tuân thủ các quy tắc dựng `script` ở [api-object-fields.md](references/api-object-fields.md#formula) (slug thật của field tham chiếu, mọi nhánh `return` khớp `return_type`, chỉ dùng API trong reference, kiểm tra tĩnh null, phép chia số nguyên, timezone, giới hạn sandbox, escaping khi serialize `meta_data`). Trước khi lưu, thực hiện đủ [Kiểm tra Formula trước khi lưu](references/formula-validation.md): phiên Web App qua `$cogover-api-auth`, kiểm tra cú pháp rồi chạy thử trên một record thật của Object; chỉ tiếp tục khi cả hai bước thành công và kết quả đúng kỳ vọng, nếu không (kể cả không tạo được phiên hoặc không có record thử) thì dừng, báo người dùng và không gọi API tạo field.
6. Gọi `POST /bapi/v1/object-fields` (alias `/bapi/v1/object-fields/create` chỉ khi có lý do tương thích cụ thể). Mong đợi `201`, `r: 0`; lấy field ID/slug và option IDs từ `data`, rồi đọc lại đối chiếu tên tiếng Anh, slug, bản dịch có `en-US`, `description`, `manualModifyAllow`, type, cờ và metadata. `formula`: parse metadata đọc lại, đối chiếu nguyên văn `script`, `return_type` và tuỳ chọn liên quan. Options: đối chiếu ID, value, slug, sort, trạng thái, mặc định, màu/icon, quan hệ cha và bản dịch.

### Cập nhật field

1. Lấy trạng thái mới nhất (Phần 1) và chỉ thay đổi phần người dùng yêu cầu. Gọi `PUT /bapi/v1/object-fields/{fieldId}`; `fieldId` trên URL là nguồn tin cậy, không gửi body có ID khác.
2. Gửi `type` hiện tại khi thay đổi cấu hình riêng theo type; chỉ đổi type trong các cặp API hỗ trợ và sau khi kiểm tra dữ liệu hiện có. Không đổi `slug` khi Object đã có records hoặc chưa đánh giá tham chiếu từ filter/workflow/layout; không đổi `multiple` nếu dữ liệu hiện tại không tương thích.
3. `translations[]`: mỗi phần tử gửi lên là trạng thái đầy đủ của ngôn ngữ đó, thuộc tính bị thiếu có thể bị xoá bản dịch và fallback về giá trị gốc (khác Object, xem Phần 3); áp dụng tương tự cho `translations[]` của từng option với thuộc tính `value`.
4. `formula`: áp dụng bước 5 của Tạo field (đọc reference, resolve lại slug đang được script tham chiếu, kiểm tra tĩnh). Chỉ sửa `script` vẫn giữ toàn bộ metadata Formula hiện có sau khi merge; đổi `return_type` phải đánh giá lại mọi nhánh `return` và tuỳ chọn hiển thị phụ thuộc kiểu kết quả. Mọi thay đổi `script`, `return_type` hoặc metadata Formula phải qua [quy trình kiểm tra Formula](references/formula-validation.md) trước `PUT`; không kiểm tra cú pháp và chạy thử thành công trên record thật thì dừng và báo.
5. Mong đợi `200`, `r: 0`; đọc lại so sánh field và toàn bộ options trước/sau; `formula` đối chiếu nguyên văn metadata.

## Phần 3 — Tạo, cập nhật, xoá hoặc khôi phục Object

### Tạo Object

1. Chỉ tạo custom Object qua public API; không gửi `is_standard: 1`. Tên gốc `name`, `plural_name`, `description`, slug kỹ thuật và `translations[]` theo mục Ngôn ngữ.
2. Gửi `name_field` vì public API yêu cầu trường tên chính. Cogover luôn tạo field record-name chuẩn với slug **`name`**: `name_field.name` là nhãn hiển thị, không phải slug kỹ thuật. Không gửi `name_field.slug`; nếu compiler/client bắt buộc biểu diễn slug thì chỉ chấp nhận giá trị `name` và dừng nếu nhận giá trị khác. Không tạo record-name bằng custom field slug như `membership_code`, `title`, `subject`, `order_number`; các nhãn này chỉ dùng làm `name_field.name`.
3. `name_field.type` chỉ `short_text` hoặc `auto_number`, schema và metadata theo [api-object-fields.md](references/api-object-fields.md). Object con/phụ thuộc, junction, dòng chi tiết, bản ghi kỹ thuật, chứng từ/giao dịch hoặc mã do hệ thống cấp: `auto_number`; Object nhận diện bằng tên/tiêu đề người dùng nhập: `short_text`.
4. Public API luôn tạo các field chuẩn: giữ `standard_fields` ở mặc định; chỉ đổi `standard_layout`, `standard_buttons`, `standard_filter` khi người dùng yêu cầu rõ. Gửi `parent_field` thì Object thành child Object (`type: 1`); chỉ gửi `composite_keys` sau khi resolve chính xác các field tham gia và kiểm tra ràng buộc unique mong muốn.
5. Gọi `POST /bapi/v1/objects` (alias `/bapi/v1/objects/create` chỉ khi có lý do tương thích cụ thể). Mong đợi `201`, `r: 0`; lấy Object ID, slug và `standard_fields` từ `data`, rồi đọc lại đúng ID/slug (Phần 1) xác minh tên gốc, bản dịch, trạng thái, fields và thành phần chuẩn. Read-back phải chứng minh có đúng một field active slug `name`, là record-name, đúng nhãn/bản dịch/type/metadata và type thuộc `short_text`/`auto_number`; không khớp thì không tạo custom field thay thế và không tuyên bố hoàn tất.

### Cập nhật Object

1. Lấy trạng thái mới nhất (Phần 1). API là partial update: chỉ gửi thuộc tính, nội dung gốc hoặc locale cần thay đổi; key vắng mặt được giữ nguyên. Gọi `PUT /bapi/v1/objects/{objectId}`; `objectId` trên URL là nguồn tin cậy, không gửi body có ID khác.
2. Không cập nhật `slug` (public API không hỗ trợ đổi slug sau khi tạo); không cập nhật Object đang pending delete (`status: 2`).
3. `name_field`: giữ slug chuẩn `name`, chỉ đổi nhãn, bản dịch, type hoặc metadata được API hỗ trợ; không đổi record-name sang custom slug, không tạo field `name` thứ hai; đọc lại xác minh vẫn có đúng một field active slug `name` với type `short_text` hoặc `auto_number`.
4. `translations[]`: mỗi phần tử chỉ upsert thuộc tính `name` hoặc `plural_name` được gửi; ngôn ngữ và thuộc tính không xuất hiện giữ nguyên; giá trị bản dịch rỗng fallback về giá trị gốc (khác field, xem Phần 2).
5. Standard Object: chỉ sửa `name`, `plural_name`, `description`, `translations` và các metadata key được hỗ trợ; không gửi thuộc tính khác.
6. Mong đợi `200`, `r: 0`; đọc lại so sánh trạng thái trước/sau.
