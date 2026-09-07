---
name: object-info
description: Xem thông tin Cogover Object cùng fields, options, metadata và related lists; nhận diện các Object nền tảng đặc biệt của Workspace; đồng thời tạo, cập nhật, xoá hoặc khôi phục Object và fields, bao gồm options của field lựa chọn và nội dung field Formula viết bằng Cogover Scripting, qua public API. Sử dụng khi cần tra Object/field ID hoặc slug, hiểu schema hay các Object đặc biệt của Workspace, viết hoặc sửa công thức Formula, kiểm tra cú pháp và chạy thử Formula trên record trước khi lưu, chuẩn bị metadata cho skill khác, quản lý vòng đời Object/field/option, hay kiểm tra lại kết quả sau thao tác ghi.
metadata:
  author: cogover
  version: "1.0.1"
---

# Object Info

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

## Mô tả chung

Chuyên xem và quản lý cấu trúc các Object trong hệ thống Cogover. Trả về thông tin Object gồm tên, slug, fields, options và related lists; đồng thời hỗ trợ tạo, sửa, xoá mềm, khôi phục và xoá thực tế Object hoặc field, cũng như tạo và cập nhật options của field lựa chọn.

Các Object phổ biến gồm Lead, Quote, Order, Product, Personnel, Contact, Account, Opportunity và Task. Skill khác có thể dùng `$object-info` để lấy Object ID, field slug, `fieldType`, options, metadata hoặc quan hệ trước khi dựng payload nghiệp vụ.

Thực hiện theo một trong ba phần:

1. Xem thông tin Object và fields.
2. Tạo, sửa hoặc xoá fields của Object.
3. Tạo, sửa, xoá hoặc khôi phục Object.

## Chuẩn bị và nguyên tắc chung

1. Resolve `WORKSPACE_DOMAIN` và API Key theo mục quản lý credential của `$cogover-api-auth`: ưu tiên credential đã được cấp cho đúng Workspace, scoped environment hoặc secret store; không dò file dự án để tìm secret. Chỉ hỏi qua kênh an toàn khi chưa có hoặc không truy cập được.
2. Không in, ghi log hoặc đưa `API_KEY` vào câu trả lời. Token có dạng `{tokenId}-{secretToken}`.
3. Chuẩn hoá `WORKSPACE_DOMAIN`: bỏ protocol và dấu `/` cuối nếu có, rồi gọi API qua `https://{WORKSPACE_DOMAIN}`.
4. Phân biệt yêu cầu đọc với yêu cầu ghi. Nếu người dùng chỉ yêu cầu xem, phân tích hoặc lấy mẫu payload, không tạo, cập nhật hay xoá Object hoặc field.
5. Tra Object và field thật trước khi dùng ID hoặc slug. Không suy đoán ID từ tên hiển thị; nếu có nhiều kết quả gần giống, đưa danh sách ứng viên để làm rõ.
6. Gọi API với hai header:

   ```http
   Authorization: Bearer {API_KEY}
   Content-Type: application/json
   ```

7. Chỉ coi thao tác thành công khi HTTP status phù hợp và response có `r: 0` nếu endpoint trả envelope nghiệp vụ. Khi lỗi, giữ lại HTTP status, `r`, `msg` và `requestId` để chẩn đoán, nhưng không để lộ token.
8. Không lặp mù quáng request ghi khi timeout hoặc lỗi mạng. Với create có kết quả không rõ, tra lại Object và slug trước khi thử lại để tránh tạo trùng.

## Ngôn ngữ gốc và bản dịch khi tạo

Áp dụng quy tắc này khi skill tạo field hoặc chuẩn bị tên/metadata cho luồng tạo Object hay field khác:

1. Cố gắng dùng tiếng Anh cho dữ liệu gốc có thể dịch như `name`, plural name, `description`, `tool_tip`, `hint_text`, option `value` và các nhãn tương tự. Tạo `slug` kỹ thuật từ tên hoặc value tiếng Anh, ưu tiên ASCII `lower_snake_case`; `slug` không phải thuộc tính có bản dịch.
2. Luôn thêm bản dịch `en-US` cho field và option được tạo, dùng các giá trị tiếng Anh tương ứng với dữ liệu gốc; field tối thiểu phải có `name`, option chỉ dịch `value`. Nếu nội dung người dùng yêu cầu không phải tiếng Anh, dịch nội dung đó sang tiếng Anh để làm giá trị gốc, đồng thời gửi cả `en-US` và nguyên nội dung người dùng trong bản dịch đúng locale. Với tiếng Việt, dùng `vi-VN`.
3. Trong `translations[]` của field, giữ đủ mọi thuộc tính người dùng đã cung cấp ở ngôn ngữ nguồn: `name`, `description`, `tooltip`, `placeholder`. Với option, chỉ gửi `value`. Không tự bịa nội dung còn thiếu chỉ để làm đầy bản dịch, ngoại trừ bản dịch `en-US` bắt buộc theo quy tắc trên.
4. API không tự dịch. Skill phải tự dựng giá trị gốc và `translations[]`, rồi xác minh field cùng từng option sau thao tác tạo. Nếu không xác định chắc ngôn ngữ/locale, yêu cầu làm rõ trước khi ghi.
5. Tôn trọng tên hoặc slug kỹ thuật chính xác nếu người dùng chỉ định rõ chúng phải là giá trị gốc; khi đó vẫn thêm bản dịch cho các nội dung hiển thị không phải tiếng Anh nếu API hỗ trợ.

Ví dụ khi người dùng yêu cầu field `Số tiền`:

```json
{
  "name": "Amount",
  "slug": "amount",
  "description": "",
  "manual_modify_allow": true,
  "translations": [
    {
      "language": "en-US",
      "name": "Amount"
    },
    {
      "language": "vi-VN",
      "name": "Số tiền"
    }
  ]
}
```

## Mặc định khi tạo field

Nếu người dùng không chỉ định khác và type không có ràng buộc đặc thù, luôn gửi các giá trị mặc định sau thay vì để server tự áp dụng:

1. Gửi `manual_modify_allow: true` để field cho phép người dùng sửa thủ công. Tôn trọng ngoại lệ của API, ví dụ `auto_number` luôn bị đặt thành `false`.
2. Gửi `description: ""` khi người dùng không cung cấp mô tả.
3. Gửi `translations[]` có ít nhất bản dịch `en-US`; nếu ngôn ngữ nguồn không phải tiếng Anh, gửi thêm đúng locale nguồn như `vi-VN`.

### Định dạng hiển thị số theo Workspace

1. Khi người dùng yêu cầu “Theo cấu hình chung của Workspace”, không tự suy ra hoặc hardcode `meta_data.format.format` từ ví dụ API, field cũ khác type hay workspace khác. Mã format là giá trị UI phụ thuộc cấu hình/phiên bản và có thể biểu diễn một kiểu phân nhóm số cụ thể thay vì mặc định Workspace.
2. Đọc một field `numeric`/`decimal` đã được người dùng xác nhận đúng trong chính workspace, rồi sao chép nguyên object `metaData.format` của field mẫu. Nếu chưa có field mẫu đáng tin cậy, yêu cầu người dùng xác nhận thay vì đoán mã.
3. Khi xoá field `currency` để tạo lại thành `decimal`, lấy lại field nguồn ngay trước khi xoá để giữ tên, slug, mô tả, bản dịch, cờ, default và giới hạn âm/dương; chỉ lấy `format` từ field mẫu `decimal` đã xác nhận, không kế thừa mã format của field `currency`.
4. Sau khi tạo, đọc lại field và đối chiếu cả `metaData.format`, `integral_length`, `fractional_length`, `display_type` và `display_as_currency`. Không coi thao tác hoàn tất chỉ vì API create trả `r: 0`.

Trong một mẫu đã ẩn danh, `{"format":7,"type":1}` là “Theo cấu hình chung của Workspace”, còn `format: 6` hiển thị `#,##,##0.00` theo kiểu Ấn Độ. Đây chỉ là dữ kiện tham khảo; vẫn phải đọc field mẫu khi làm việc ở Workspace đích.

## Object đặc biệt của Workspace cần nắm

Các Object dưới đây có vai trò nền tảng hoặc dùng chung trong một Workspace. Khi đọc danh sách Object, không diễn giải chúng như Object nghiệp vụ thông thường và không tạo bản sao nếu Object tương ứng đã tồn tại.

| Object slug | Ý nghĩa | Lưu ý sử dụng |
|---|---|---|
| `Process_Debug_data` | Lưu dữ liệu debug phục vụ chẩn đoán quá trình chạy Process. | Đây là dữ liệu kỹ thuật của Process; không dùng làm master data nghiệp vụ. Giữ nguyên đúng slug và cách viết hoa/thường đọc từ Workspace. |
| `global_settings` | Lưu cấu hình dùng chung ở mức Workspace hoặc ứng dụng. | Đọc schema và records thật trước khi dùng; không tự suy đoán cấu trúc cấu hình giữa các Workspace. |
| `app_user` | Lưu danh tính người dùng ứng dụng. | Phân biệt với `account`: `app_user` là người dùng ứng dụng, còn `account` thường là doanh nghiệp, tổ chức hoặc khách hàng trong CRM. |
| `notification_channel` | Định nghĩa các kênh gửi thông báo. | Kiểm tra thêm Object/quan hệ thành viên kênh đang có trong Workspace trước khi tích hợp hoặc tạo dữ liệu. |
| `activity` | Lưu hoạt động tương tác trên một bản ghi nghiệp vụ như hợp đồng, lead, cơ hội hoặc công việc; hoạt động có thể là ghi chú, email, cuộc gọi, task, cuộc họp, SMS hoặc chat. | Để một Object nghiệp vụ có khu vực thảo luận/ghi chú/hoạt động, tạo lookup từ `activity` tới Object đó rồi đưa Related List được sinh ra vào layout Xem/Sửa của Object đích. |
| `activity_comment` | Lưu bình luận gắn với một bản ghi `activity`. | Đây thường là dữ liệu con của Activity; không dùng thay cho quan hệ trực tiếp giữa `activity` và Object nghiệp vụ. |

### Bổ sung Activity cho một Object nghiệp vụ

Ví dụ cần cho phép người dùng cùng thảo luận, ghi chú và theo dõi hoạt động trên Object `contract`:

1. Dùng Phần 1 đọc Object `activity` và `contract` thật, kiểm tra `activity` chưa có field lookup phù hợp và `contract` chưa có Related List tương ứng. Không tạo trùng quan hệ đã tồn tại.
2. Trên Object `activity`, tạo field `lookup_normal` trỏ tới Object `contract`; dùng slug kỹ thuật `contract` và gửi `related_list_name` có ý nghĩa theo contract của Object Fields API. Resolve Object ID thật, translations và metadata theo quy trình tạo field của skill này; không suy đoán ID.
3. Đọc lại cả hai Object. Chỉ tiếp tục khi field `activity.contract` tồn tại đúng type/metadata và `contract.relatedLists` đã có Related List nguồn `activity`. Lấy `relatedListId`, `originSlug`, tên, slug và lookup field thật từ response; không tự tạo hoặc đoán Related List ID.
4. Dùng `$object-layout` đọc layout Xem/Sửa hiện tại của `contract` (`functionLayout: 2`, quyền `VIEW_EDIT`). Đặt component `fieldType: "related_list"` vào đúng hierarchy `layoutRow → layoutColumn → section → tab → group → components`; ưu tiên một tab/section “Activities” trên cột nội dung chính. Giữ nguyên toàn bộ cấu hình ngoài phạm vi và view lại layout sau update.
5. Với Activity, ưu tiên `typeView: "timeline"`, `listAction: [{"value":"CREATE"}]` và `isAllTabActivity: true` để người dùng xem và tạo hoạt động ngay trên bản ghi. Nếu giới hạn loại hoạt động, chỉ dùng các giá trị đã xác minh trên Workspace; layout Lead mẫu hỗ trợ `note`, `email`, `call`, `task`, `meeting`, `sms`, `chat_zalo_fb` và `chat`.

## Phần 1 — Xem thông tin Object + fields

### Gọi API

Gọi `POST /bapi/v1/objects/list`:

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/objects/list' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "pageSize": 2000,
    "includeFields": true,
    "includeRelatedLists": true,
    "includeOptions": true,
    "includeMetaData": true
  }'
```

Chỉ yêu cầu phần dữ liệu cần dùng để giảm response:

| Tham số | Mặc định | Cách dùng |
|---|---:|---|
| `pageSize` | `2000` | Giới hạn số Object trả về |
| `keywords` | `[]` | Tìm mờ không phân biệt hoa thường theo `name`, `slug`, `nameTranslations` |
| `slugs` | `[]` | Lọc chính xác theo Object slug |
| `ids` | `[]` | Lọc chính xác theo Object ID |
| `includeFields` | `false` | Trả `fields` của mỗi Object |
| `includeRelatedLists` | `false` | Trả `relatedLists` của mỗi Object |
| `includeOptions` | `true` | Trả options khi `includeFields=true` |
| `includeMetaData` | `true` | Trả metadata khi `includeFields=true` |
| `includeNonStandard` | `true` | Đặt `false` để chỉ lấy Object tiêu chuẩn |
| `includeWorkflowObjects` | `false` | Đặt `true` để gồm Workflow Object |

Ưu tiên `slugs` hoặc `ids` khi người dùng đã xác định chính xác Object. Dùng `keywords` để khám phá; không tự chọn một kết quả mờ khi có nhiều ứng viên.

### Đọc kết quả

Từ `items[]`, trích xuất tối thiểu:

- Object: `id`, `name`, `slug`, `nameTranslations` và mô tả nếu response có.
- Field: `id`, `name`, `slug`, `fieldType`, `nameTranslations`, `required`, `status`, `description`, `multiple`, `readOnly`, `manualModifyAllow`, `defaultValue`, options và metadata.
- Option của field lựa chọn: `id`, `value`, `slug`, `isDefault`, trạng thái, màu/icon và bản dịch nếu có.
- Related list: `id`, `name`, `slug`, `status`, `sort`, `displayColumn`, `minRecord`, `maxRecord`, Object/field nguồn, Object lookup và `lookupType`.

Không giả định field có thể ghi chỉ vì nó xuất hiện trong response đọc. Object có thể chứa field hệ thống, field chuẩn, field read-only hoặc `fieldType` mà Object Fields API không hỗ trợ tạo mới.

### Trả kết quả

- Khi người dùng hỏi một Object, chỉ hiển thị Object đó và các field liên quan; dùng bảng gọn nếu có nhiều field.
- Khi người dùng hỏi nhiều Object, tóm tắt Object trước rồi chỉ mở rộng fields theo phạm vi yêu cầu.
- Khi skill khác gọi, trả dữ liệu có cấu trúc và giữ nguyên ID, slug, `fieldType`, option slug/value cùng metadata cần thiết; không dịch hoặc tự sinh giá trị kỹ thuật.
- Khi không tìm thấy kết quả, nêu rõ bộ lọc đã dùng thay vì kết luận Object không tồn tại trong toàn workspace.

## Phần 2 — Tạo, sửa, xoá fields của Object

### Chuẩn bị thao tác ghi

1. Đọc đầy đủ [references/api-object-fields.md](references/api-object-fields.md) trước khi dựng payload hoặc gọi endpoint. Đây là nguồn chuẩn cho field types, schema, metadata, translations, giới hạn, mã lỗi và ví dụ cURL.
2. Dùng Phần 1 để resolve đúng Object. Lấy `object_type_id` từ Object ID thật; không dùng tên hoặc slug thay cho ID.
3. Với update/delete, lấy lại Object cùng fields ngay trước thao tác để xác nhận field ID, type, slug, trạng thái và metadata hiện tại.
4. Kiểm tra tác động tới records, filters, workflows, formulas, layouts, related lists và Object relations khi đổi `slug`, `type`, `unique`, `multiple`, xoá field hoặc xoá options đã có dữ liệu record/tham chiếu.
5. Chỉ gửi `options` ở top-level cho `single_choice`, `radio_button`, `multi_choices`, `checkbox` hoặc `cascading`; request có `options` bắt buộc gửi `type` hiện tại hoặc type đích hợp lệ. Không đặt options trong `meta_data` và không gọi URI riêng cho options.
6. Phân biệt rõ semantics của `options` khi update:
   - Không có key `options`: giữ nguyên toàn bộ options hiện tại.
   - Có key `options`: thay thế toàn bộ danh sách bằng trạng thái trong mảng.
   - `options: []`: xoá toàn bộ options. Chỉ gửi khi người dùng yêu cầu rõ và đã xác nhận tác động dữ liệu.
   - Khi chỉ sửa một phần, đọc danh sách hiện tại, merge thay đổi rồi gửi lại toàn bộ mảng; không để mất option ngoài phạm vi yêu cầu.
7. Giữ đúng kiểu dữ liệu của request:
   - Dùng số `0`/`1` cho `required`, `multiple`, `unique`, `status`, `creatable`, `editable`, `viewable`, `read_only`, `is_standard`, `is_display` và `quickSearch`.
   - Chỉ `manual_modify_allow` dùng Boolean nghiêm ngặt `true`/`false`.
   - Giữ nguyên cách viết `quickSearch`; các key còn lại của Object Fields API chủ yếu dùng `snake_case`.
   - Encode `meta_data` thành JSON string hợp lệ, không gửi JSON object trực tiếp.

### Tạo field

1. Chuẩn hoá tên gốc, slug và bản dịch theo phần **Ngôn ngữ gốc và bản dịch khi tạo**. Kiểm tra trong Object chưa có field trùng tên tiếng Anh, tên được dịch hoặc `slug` dự kiến.
2. Chọn `type` được API hỗ trợ và đọc cấu hình riêng của type đó trong API reference. Không suy ra metadata của type này từ type khác.
3. Gửi `type`, `object_type_id`, `name` tiếng Anh và các giá trị trong phần **Mặc định khi tạo field**. `translations[]` luôn phải có `en-US`; khi đầu vào không phải tiếng Anh, gửi thêm đúng locale nguồn và chỉ giữ các thuộc tính dịch người dùng thực sự cung cấp.
4. Với field lựa chọn cần options, gửi danh sách đầy đủ ở top-level. Mỗi option mới phải có UUID riêng và `value`; kiểm tra tối đa 200 options, không trùng ID/value, `sort > 0` nếu gửi, flags số hợp lệ và slug duy nhất. Với `cascading`, flatten cây và dùng `parent_id` trỏ đúng ID option cha. Không tự bịa options nếu người dùng chưa cung cấp.
5. Nếu không được chỉ định, có thể để server sinh field `slug` từ tên tiếng Anh và tự tính `sort`. Không dựa vào server cho các mặc định đã quy định trong skill. Chỉ gửi slug kỹ thuật hoặc cấu hình tuỳ chọn khi cần.
6. Với lookup `lookup_normal` hoặc `reference`, bắt buộc resolve Object đích và gửi `related_list_name`; xác minh metadata quan hệ trước khi tạo.
7. Với field `formula`, dùng [Cogover Scripting API Reference](references/cogover-scripting-api-vi.md) để viết hoặc sửa `meta_data.script`. Đọc mục 1–4 về nền tảng cú pháp, mục 14 về giới hạn và an toàn, sau đó đọc đầy đủ các mục hàm/kiểu dữ liệu cùng recipe liên quan tới công thức cần viết. Có thể dùng `rg -n '^## |^### |^#### ' references/cogover-scripting-api-vi.md` để định vị phần cần đọc. Resolve các field được tham chiếu từ Object thật và dùng đúng slug kỹ thuật; không suy đoán slug từ tên hiển thị. Chỉ dùng API có trong reference; bảo đảm mọi nhánh trả về giá trị tương thích với `return_type`. Kiểm tra tĩnh giới hạn vòng lặp, thời gian thực thi, null, phép chia số nguyên, timezone và escaping khi serialize `meta_data` thành JSON string.
8. Trước khi lưu field `formula`, đọc đầy đủ [Kiểm tra Formula trước khi lưu](references/formula-validation.md). Dùng `$cogover-api-auth` tạo phiên Web App, gọi API kiểm tra cú pháp rồi chạy thử trên một record thật thuộc Object. Chỉ tiếp tục khi cả hai bước thành công và kết quả đúng kỳ vọng. Nếu không tạo được phiên, không có record thử hoặc một bước kiểm tra thất bại, dừng và báo người dùng; không gọi API tạo field.
9. Gọi `POST /bapi/v1/object-fields`. Chỉ dùng alias `/bapi/v1/object-fields/create` khi có lý do tương thích cụ thể.
10. Mong đợi HTTP `201` và `r: 0`. Lấy field ID/slug cùng option IDs từ `data`, rồi dùng Phần 1 để kiểm tra field đã xuất hiện với đúng tên tiếng Anh, slug, bản dịch gồm `en-US`, `description`, `manualModifyAllow`, type, flags và metadata. Với `formula`, parse metadata đọc lại và đối chiếu nguyên văn `script`, `return_type` cùng các tuỳ chọn liên quan. Nếu có options, đối chiếu đầy đủ ID, value, slug, sort, trạng thái, mặc định, màu/icon, quan hệ cha và bản dịch.

### Cập nhật field

1. Lấy trạng thái mới nhất của field bằng Phần 1 và chỉ thay đổi phần người dùng yêu cầu.
2. Gọi `PUT /bapi/v1/object-fields/{fieldId}`. Xem `fieldId` trên URL là nguồn tin cậy; không gửi body có ID khác.
3. Gửi `type` hiện tại khi thay đổi cấu hình riêng theo type. Chỉ đổi type trong các cặp được API hỗ trợ và sau khi kiểm tra dữ liệu hiện có.
4. Khi sửa `meta_data`, parse metadata hiện tại, merge đúng key cần đổi, kiểm tra lại theo type, rồi serialize toàn bộ kết quả thành JSON string. Không gửi metadata một phần vì server sẽ thay toàn bộ chuỗi đã lưu.
5. Khi sửa `formula`, đọc các phần bắt buộc và liên quan trong [Cogover Scripting API Reference](references/cogover-scripting-api-vi.md) theo chỉ dẫn ở bước tạo, resolve lại field slug đang được script tham chiếu và áp dụng các kiểm tra tĩnh như khi tạo. Nếu chỉ sửa `script`, vẫn giữ toàn bộ metadata Formula hiện có sau khi merge; nếu đổi `return_type`, đánh giá lại mọi nhánh `return` và các tuỳ chọn hiển thị phụ thuộc kiểu kết quả.
6. Trước khi gửi update có thay đổi `script`, `return_type` hoặc metadata Formula, thực hiện đầy đủ [quy trình kiểm tra Formula](references/formula-validation.md) bằng phiên Web App do `$cogover-api-auth` tạo. Nếu không thể kiểm tra cú pháp và chạy thử thành công trên record thật, dừng trước `PUT` và báo người dùng.
7. Khi cập nhật options, luôn đọc options hiện tại ngay trước thao tác, giữ nguyên ID của option cần bảo toàn, tạo UUID cho option mới, merge đúng thay đổi và gửi toàn bộ trạng thái đích cùng `type`. Option bị loại khỏi mảng sẽ bị xoá; không dùng ID mới để biểu diễn việc sửa một option hiện có.
8. Khi gửi một phần tử `translations[]`, xem nó là trạng thái đầy đủ của ngôn ngữ đó. Giữ lại mọi thuộc tính dịch cần bảo toàn; thuộc tính bị thiếu có thể bị xoá bản dịch và fallback về giá trị gốc. Quy tắc này áp dụng riêng cho `translations[]` của từng option với thuộc tính `value`.
9. Không đổi `slug` khi Object đã có records hoặc khi chưa đánh giá tham chiếu từ filter/workflow/layout. Không đổi `multiple` nếu dữ liệu hiện tại không tương thích.
10. Mong đợi HTTP `200` và `r: 0`, rồi dùng Phần 1 để so sánh field và toàn bộ options trước/sau. Với `formula`, đối chiếu nguyên văn metadata sau khi đọc lại. Không dựa riêng vào response update rút gọn.

### Xoá hoặc khôi phục field

1. Resolve và hiển thị chính xác Object, field name, field ID, slug, type và trạng thái trước thao tác.
2. Yêu cầu người dùng xác nhận rõ field mục tiêu và `delete_type` trước khi gọi endpoint xoá. Nếu người dùng chỉ nói “xoá”, khuyến nghị `delete_type: 1` để soft delete.
3. Gọi `POST /bapi/v1/object-fields/delete` với danh sách:

   ```json
   {
     "data": [
       {
         "id": "OF00000000027",
         "delete_type": 1
       }
     ]
   }
   ```

4. Chọn đúng thao tác:
   - `1`: soft delete, chuyển field sang pending delete và đặt lịch xoá sau 14 ngày.
   - `2`: khôi phục field đã soft delete và huỷ lịch xoá.
   - `3`: actual delete, dọn quan hệ/cấu hình liên quan và xoá dữ liệu field khỏi records. Chỉ dùng sau khi người dùng xác nhận rõ xoá thực tế và đã được cảnh báo không thể khôi phục.
5. Mong đợi HTTP `200` và `r: 0`. Dùng Phần 1 để xác minh trạng thái sau soft delete/restore hoặc field không còn tồn tại sau actual delete. Nếu API trả `r: 524`, trình bày đầy đủ cảnh báo về nơi field đang được sử dụng và không coi thao tác là thành công.

### Xử lý lỗi và báo cáo

- Với HTTP `401`, yêu cầu API key hợp lệ; với `429`, tôn trọng rate limit; với `500`, báo lỗi và chỉ thử lại có kiểm soát khi thao tác an toàn.
- Với `r != 0`, dùng bảng mã lỗi trong API reference để chỉ rõ field hoặc ràng buộc gây lỗi. Không chỉ báo “HTTP 400”.
- Với create/update, báo field ID, name, slug, type, Object và trạng thái đã được API đọc xác minh; nếu có options, báo số lượng tạo/cập nhật/xoá và kết quả đối chiếu danh sách cuối.
- Với delete/restore, báo `delete_type`, ID đã gửi, kết quả xác minh và tác động/cảnh báo còn lại.
- Nếu backend chặn do dependency hoặc validation của options, nói rõ phần đã làm, phần chưa làm và mã lỗi liên quan; không tuyên bố hoàn tất khi danh sách options sau ghi không khớp trạng thái đích.

## Phần 3 — Tạo, cập nhật, xoá hoặc khôi phục Object

### Chuẩn bị thao tác ghi

1. Đọc đầy đủ [references/api-objects.md](references/api-objects.md) trước khi dựng payload hoặc gọi endpoint. Đây là nguồn chuẩn cho schema create/update, `delete_type`, giới hạn của standard Object, mã lỗi và ví dụ cURL.
2. Dùng Phần 1 để kiểm tra Object hiện có ngay trước thao tác. Với create, kiểm tra trùng `name`, `plural_name` và `slug`; với update/delete/restore, resolve Object ID thật cùng trạng thái, loại standard/custom và các quan hệ liên quan.
3. Khi tạo Object, dùng tiếng Anh cho `name`, `plural_name`, `description` gốc và slug kỹ thuật nếu người dùng không yêu cầu khác. Luôn thêm bản dịch `en-US`; nếu đầu vào không phải tiếng Anh, thêm cả locale nguồn như `vi-VN`. Khi cập nhật, chỉ gửi nội dung gốc hoặc locale thực sự cần thay đổi để giữ đúng semantics partial update.
4. Giữ đúng kiểu dữ liệu:
   - Dùng số `0`/`1` cho `status`, `creatable`, `editable`, `viewable`, `quick_search`; `type` nhận `0`, `1` hoặc `2`.
   - Dùng Boolean cho `standard_fields`, `standard_layout`, `standard_buttons`, `standard_filter`.
   - Encode `meta_data` và `name_field.meta_data` thành JSON string hợp lệ, không gửi JSON object trực tiếp.
5. Đánh giá tác động tới records, fields, relationships, filters, workflows, formulas, layouts, buttons, Object Picker và skill/cấu hình đang tham chiếu Object trước khi đổi trạng thái, quan hệ cha, composite key hoặc xoá Object.

### Tạo Object

1. Chỉ tạo custom Object qua public API; không gửi `is_standard: 1`.
2. Gửi `name_field` vì public API yêu cầu trường tên chính. Cogover luôn tạo field record-name chuẩn với slug **`name`**: `name_field.name` là nhãn hiển thị, không phải slug kỹ thuật. Không gửi `name_field.slug`; nếu compiler/client bắt buộc biểu diễn slug thì chỉ chấp nhận giá trị `name` và dừng nếu nhận giá trị khác.
3. `name_field.type` chỉ dùng `short_text` hoặc `auto_number`, áp dụng schema và metadata tương ứng trong [references/api-object-fields.md](references/api-object-fields.md). Chọn type theo nghiệp vụ:
   - Object con/phụ thuộc, junction, dòng chi tiết hoặc bản ghi kỹ thuật: mặc định `auto_number`.
   - Object thông thường được nhận diện bằng tên/tiêu đề người dùng nhập: `short_text`.
   - Chứng từ, giao dịch hoặc mã bản ghi do hệ thống cấp: `auto_number`.
4. Không tạo record-name bằng một custom field slug như `membership_code`, `title`, `subject` hoặc `order_number`. Các nhãn này có thể dùng làm `name_field.name`, nhưng slug sau create vẫn phải là `name`.
5. Public API luôn tạo các field chuẩn. Giữ `standard_fields` ở mặc định; chỉ thay đổi các cờ `standard_layout`, `standard_buttons` hoặc `standard_filter` khi người dùng yêu cầu rõ.
6. Nếu gửi `parent_field`, hiểu rằng Object sẽ thành child Object (`type: 1`). Chỉ gửi `composite_keys` sau khi resolve chính xác các field tham gia và kiểm tra ràng buộc unique mong muốn.
7. Gọi `POST /bapi/v1/objects`; chỉ dùng alias `/bapi/v1/objects/create` khi có lý do tương thích cụ thể.
8. Mong đợi HTTP `201` và `r: 0`. Lấy Object ID, slug và `standard_fields` từ `data`, rồi dùng Phần 1 với chính xác ID/slug để xác minh tên gốc, bản dịch, trạng thái, fields và các thành phần chuẩn đã được tạo. Read-back bắt buộc chứng minh có đúng một field active slug `name`, field đó là record-name, có đúng nhãn/bản dịch/type/metadata mong muốn và type thuộc `short_text`/`auto_number`. Nếu không khớp, không tạo custom field thay thế và không tuyên bố hoàn tất.

### Cập nhật Object

1. Lấy trạng thái mới nhất bằng Phần 1 và chỉ gửi các thuộc tính người dùng yêu cầu thay đổi. API là partial update; key không có trong payload được giữ nguyên.
2. Gọi `PUT /bapi/v1/objects/{objectId}`. Xem `objectId` trên URL là nguồn tin cậy; không gửi body có ID khác.
3. Không cố cập nhật `slug`; public API không hỗ trợ đổi slug sau khi tạo. Không cập nhật Object đang pending delete (`status: 2`).
4. Khi cập nhật `name_field`, giữ slug chuẩn `name`; chỉ thay đổi nhãn, bản dịch, type hoặc metadata được API hỗ trợ. Không đổi record-name sang custom slug và không tạo field `name` thứ hai. Đọc lại để xác minh vẫn có đúng một field active slug `name` với type `short_text` hoặc `auto_number`.
5. Với `translations[]`, mỗi phần tử chỉ upsert các thuộc tính `name` hoặc `plural_name` được gửi; ngôn ngữ và thuộc tính không xuất hiện được giữ nguyên. Giá trị bản dịch rỗng sẽ fallback về giá trị gốc.
6. Với custom Object, khi sửa `meta_data`, parse metadata hiện tại, merge phần thay đổi rồi serialize toàn bộ kết quả vì API thay toàn bộ chuỗi đã lưu. Với standard Object, chỉ gửi các metadata key được reference cho phép; API sẽ merge các key hợp lệ.
7. Với standard Object, chỉ sửa `name`, `plural_name`, `description`, `translations` và các metadata key được hỗ trợ. Không gửi các thuộc tính khác.
8. Mong đợi HTTP `200` và `r: 0`, rồi dùng Phần 1 để so sánh trạng thái trước/sau. Không dựa riêng vào response update rút gọn.

### Xoá hoặc khôi phục Object

1. Resolve và hiển thị chính xác Object name, ID, slug, trạng thái, standard/custom cùng các dependency đã phát hiện trước thao tác.
2. Không xoá standard Object. Nếu Object đang được Object Picker, field, relationship, filter, workflow hoặc thực thể khác tham chiếu, báo dependency và không tuyên bố thao tác thành công.
3. Yêu cầu người dùng xác nhận rõ Object mục tiêu và `delete_type` trước khi gọi endpoint. Nếu người dùng chỉ nói “xoá”, khuyến nghị `delete_type: 1`.
4. Gọi `POST /bapi/v1/objects/delete` với danh sách:

   ```json
   {
     "data": [
       {
         "id": "OT00000000020",
         "delete_type": 1
       }
     ]
   }
   ```

5. Chọn đúng thao tác:
   - `1`: soft delete, chuyển Object sang pending delete và đặt lịch xoá thực tế sau 14 ngày.
   - `2`: khôi phục Object đã soft delete, phục hồi trạng thái trước đó và huỷ lịch xoá.
   - `3`: actual delete, xoá cấu hình liên quan và dữ liệu records của Object. Chỉ dùng sau khi người dùng xác nhận rõ xoá thực tế và đã được cảnh báo không thể khôi phục.
6. Mong đợi HTTP `200` và `r: 0`. Tra lại bằng ID/slug để xác minh trạng thái sau soft delete/restore hoặc việc Object không còn tồn tại sau actual delete; không coi riêng việc Object vắng mặt trong một list mặc định là bằng chứng đủ nếu bộ lọc có thể loại pending-delete Object.

### Xử lý lỗi và báo cáo

- Với HTTP `401`, yêu cầu API key hợp lệ; với `429`, tôn trọng rate limit; với `500`, báo lỗi và chỉ thử lại có kiểm soát khi thao tác an toàn.
- Với `r != 0`, dùng bảng mã lỗi trong API reference để nêu đúng ràng buộc, đặc biệt lỗi trùng tên/slug, Object pending delete, standard Object, Object Picker dependency hoặc giới hạn gói thuê bao.
- Với create/update, báo Object ID, name, plural name, slug, trạng thái và kết quả đọc xác minh.
- Với delete/restore, báo `delete_type`, Object ID, kết quả xác minh, thời hạn 14 ngày nếu soft delete và mọi dependency/cảnh báo còn lại.
