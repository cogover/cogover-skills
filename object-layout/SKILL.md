---
name: object-layout
description: "Quản lý layout Cogover Object qua Layouts V2 API `/bapi/v1/layouts_v2`: tạo, xem, cập nhật, xoá layout; tạo layout `isForm: 1` khi $object-form gọi; thiết kế row/column/section/tab/group/component; lấy/cập nhật `pageSettings.script`; đặt Object Button vào `pageSettings.buttons.listButton` và Path Component vào layout xem/sửa."
metadata:
  author: cogover
  version: "1.0.2"
---

# Object Layout

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Skill này được `$object-form` gọi như sub-skill khi Object chưa có layout `isForm` hợp lệ, được `$layout-scripting` dùng để lấy/ghi `pageSettings.script`, và phối hợp với `$object-button`, `$document-template`, `$object-path-component` khi cần đặt Object Button hoặc Path Component lên layout xem/sửa.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Skill này chỉ dùng nhóm `/bapi/v1` (API Key Bearer), cụ thể `/bapi/v1/layouts_v2`. Khi API v2 lỗi xác thực, không nhận payload hoặc xác minh sai: báo nguyên nhân cùng thông báo lỗi từ response rồi dừng; không đổi endpoint, phiên bản API hay cơ chế xác thực.
- `objectTypeSlug` và danh sách field của Object (`id`, `name`, `slug`, `fieldType`, `description`, `metaData`, `manualModifyAllow`, related lists): lấy qua [$object-info](../object-info/SKILL.md) (`POST /bapi/v1/objects/list`, `includeFields: true`). Không đoán field ID hoặc slug từ tên.
- Tài liệu trong skill, đọc đúng bước cần dùng:

| Khi làm gì | Đọc |
|---|---|
| Dựng hoặc sửa `content` (schema row/column/section/tab/group/component) | [references/layout-json-structure.md](references/layout-json-structure.md) và mẫu thật `assets/sample_layout_1.json` |
| Cấu hình component theo `fieldType` (lookup, file, related_list, display_box, report, dashboard, button_group, path_component...) | [references/component-field-types.md](references/component-field-types.md) |
| Dựng `pageSettings` | [references/page-settings.md](references/page-settings.md) |
| Cần ví dụ cây bố cục Lead/Đơn hàng khi thiết kế | [references/layout-design-examples.md](references/layout-design-examples.md), `assets/sample_layout_create_order.json` |
| Dựng payload `PUT` (mẫu curl, jq cho script) | [references/layout-update-payload.md](references/layout-update-payload.md) |
| Thêm, sắp xếp hoặc gỡ Object Button trên layout xem/sửa | [references/record-button-placement.md](references/record-button-placement.md) |

## Nguyên tắc xác nhận

- Mặc định **không hỏi xác nhận bổ sung** cho tạo, cập nhật, đặt/gỡ Object Button hoặc xoá layout khi người dùng đã nêu rõ thao tác và đích. Sau khi resolve đúng tài nguyên, payload hợp lệ và đủ quyền: thực hiện ngay rồi xác minh kết quả.
- Chỉ hiển thị bản xem trước/tóm tắt và chờ xác nhận khi người dùng **chủ động yêu cầu** xem trước, phê duyệt hoặc xác nhận trước khi ghi.
- Đích hoặc phạm vi mơ hồ và các lựa chọn dẫn đến kết quả khác nhau đáng kể: hỏi làm rõ phạm vi; đây không phải bước xác nhận mặc định.
- Xoá: vẫn resolve chính xác ID, hiển thị ID/tên/slug/đối tượng, nêu rõ không thể hoàn tác và kiểm tra tác động trước khi gọi API; không thêm lượt xác nhận nếu yêu cầu xoá đã rõ và người dùng không yêu cầu quy trình phê duyệt.
- Khi `$object-form` gọi vì thiếu layout `isForm`: không hỏi lại thông tin đã có, không yêu cầu xác nhận; dùng đúng Object đã resolve, đặt tên tiếng Anh theo form/Object, tự thiết kế bố cục mặc định hợp lý từ các field có thể nhập nếu người dùng chưa mô tả chi tiết.

## Layouts V2 API

| Thao tác | Request |
|---|---|
| Tạo | `POST /bapi/v1/layouts_v2` |
| Danh sách layout của Object | `POST /bapi/v1/layouts_v2/list` body `{"objectTypeSlug": "{OBJECT_SLUG}", "limit": 2000, "page": 1}` |
| Chi tiết | `POST /bapi/v1/layouts_v2/view` body `{"id": "{LAYOUT_ID}"}` |
| Cập nhật | `PUT /bapi/v1/layouts_v2/{LAYOUT_ID}` |
| Xoá | `POST /bapi/v1/layouts_v2/delete` body `{"data": ["{LAYOUT_ID}"]}` |

Link layout: `https://{WORKSPACE_DOMAIN}/settings/object/{OBJECT_SLUG}/layout/{LAYOUT_ID}`.

Quy tắc cho mọi `PUT`:

- View lại layout ngay trước khi sửa và dựng payload từ `data` mới nhất để không ghi đè thay đổi của người khác.
- Payload chỉ gồm allowlist: `name`, `objectTypeSlug`, `status`, `type`, `updateRecordMode`, `accessControls`, `hasComponentPath`, `content`, `title`, `pageSettings`, `functionLayout`, `isWeb`, `isMobile`. Không gửi raw `data` của response view (chứa trường server-managed `id`, `slug`, `created`, `updated`, `createdBy`, `updatedBy`, `workspaceId`, `objectTypeId`, `contentCompiled` mà API update không nhận). Không gửi payload rút gọn chỉ có `pageSettings.script` hoặc chỉ `name`, `content`, `pageSettings`.
- Giữ nguyên mọi giá trị không được yêu cầu thay đổi, kể cả `hasComponentPath` (có thể là `null`); không tự dựng lại `content` khi chỉ sửa script, button hoặc thêm một component.
- Sau `PUT`, view lại và so với payload. Không khớp: báo dữ liệu chưa được lưu đúng và dừng.

## Phân loại layout

| Loại | `functionLayout` | `accessControls[].functions` | Ghi chú |
|---|---|---|---|
| Tạo | `1` | `["ADD"]` | |
| Xem/Sửa | `2` | `["VIEW_EDIT"]` | Loại duy nhất nhận Path Component |
| Tạo/Xem/Sửa | `3` | `["ADD", "VIEW_EDIT"]` | Field `manualModifyAllow: false` và `auto_number` tự ẩn khi tạo |

- `isWeb`/`isMobile` chọn layout dùng cho Web, Mobile hoặc cả hai.
- `isForm: 1` chỉ khi người dùng yêu cầu layout cho Object Form hoặc `$object-form` gọi fallback; layout khác dùng `isForm: 0` hoặc giữ mặc định backend. Không suy diễn layout Add thông thường là form-compatible; không chuyển layout hiện có từ `isForm: 0` sang `1`.
- Layout cho Object Form: Web active với `functionLayout: 1`, quyền `ADD`, `isForm: 1`, `status: 1`, `isWeb: true` và `content` hợp lệ; không dùng `functionLayout: 3` cho fallback này. Sau create, view/list lại và chỉ trả ID cho `$object-form` khi `objectTypeSlug` cùng các giá trị trên khớp chính xác.

## Tạo layout

### Bước 1: Thu thập yêu cầu

1. Đối tượng (`objectTypeSlug`).
2. Mô tả bố cục: bao nhiêu row, column, section, tab, group và field nào ở đâu.
3. Tên layout: chuẩn hoá hoặc dịch sang tiếng Anh; nếu không chỉ định, đặt theo chức năng (`Create`, `View/Edit`, `Create Order`).

Lấy fields của Object qua `$object-info`; xác định `id`, `name`, `slug`, `fieldType`, `description`, `metaData` của từng field sẽ đặt lên layout.

### Bước 2: Thiết kế bố cục

Đóng vai chuyên gia UI/UX cho nhân viên doanh nghiệp dùng CRM/HRM/ERP: đọc `name`/`slug`/`description` của field và Object, sắp xếp field theo thứ tự nhập/đọc trong nghiệp vụ; ưu tiên thuận tiện, logic, không hoa mỹ. Có thể list/view layout của Object tương tự để tham khảo cách bố trí (Lead: `functionLayout: 1` cho tạo, `2` cho xem/sửa; ID lấy từ API list). Ví dụ cây bố cục: [references/layout-design-examples.md](references/layout-design-examples.md).

Layout tham khảo chỉ dùng để học cấu trúc. Trước khi tái sử dụng `content`, xác minh nó là array không rỗng và đủ chuỗi `layoutRow → layoutColumn → section → tab → group → component`; nếu `content` là `null`, không phải array, `[]` hoặc có cấp con rỗng, không dùng làm payload mà dựng mới từ fields của Object và asset mẫu.

**Layout Tạo (`functionLayout: 1` hoặc `3`)**

- Khung trang: giữ `settingPage.paddingTop/Bottom/Left/Right: 0`, `settingPage.typeColor: "primary"`, `settingPage.combinationRatio: 100`; `settingContentPage.maxWidth: 100`, `unitMaxWidth: "%"`, `isShowBorder: false`. Giới hạn độ rộng form bằng **Layout Row ngoài cùng**, không đổi `settingContentPage` sang `1000px`.
- Row ngoài cùng, tính trước khi dựng JSON: form thường (không có bảng/component rộng) → `maxWidth: 1000`, `unitMaxWidth: "px"`, `horizontalAlignment: "center"` (đủ cho group 2-3 cột; chọn độ rộng khác chỉ khi số cột, loại field hoặc UI thực tế chứng minh cần). Có `related_list` `typeView: "list"` hoặc bảng/component rộng tương tự → `maxWidth: 100`, `unitMaxWidth: "%"`, `horizontalAlignment: "center"`. Không dùng `100%` cho form thường chỉ vì nhiều field.
- Cấu trúc: 1 Layout Row, 1 Layout Column trừ khi có lý do rõ hoặc người dùng yêu cầu. Trong Column chia 1 hoặc nhiều Section có border (`isBorder: true`) và tiêu đề (`isShowName: true`); ví dụ Lead: "Lead Information", "Additional Information".
- Field quan trọng (tên, tiêu đề, trạng thái) và field `required` lên đầu section đầu tiên.
- Group: field nội dung dài (tiêu đề, mô tả) → `numberOfColumns: 1`; field ngắn (SĐT, email, trạng thái, select) → `2` hoặc `3`; cặp liên quan ngắn đặt cùng hàng trong group nhiều cột (Họ + Tên, Quốc gia + Thành phố, Ngày bắt đầu + Ngày kết thúc). Field xếp từ trái qua phải, hết hàng thì xuống dòng.
- `long_text` đặt cuối section/group. Boolean gom vào group nhiều cột với `labelPlacement: "right"`.
- Không đưa vào layout tạo: field `manualModifyAllow: false`, `auto_number`, `created`, `updated`, `created_by`, `updated_by` (tự ẩn nếu `functionLayout: 3`, nhưng vẫn tránh).
- Object cha cần nhập danh sách con ngay khi tạo (Đơn hàng → Sản phẩm trong đơn hàng, Báo giá → Sản phẩm báo giá): đặt `related_list` `typeView: "list"` có `tableSettings.editableColumns` trong Group `numberOfColumns: 1` ở cuối section, sau các field cơ bản của cha; Row ngoài cùng dùng `100%`. Quy tắc chọn `editableColumns`/`showingColumns`: [references/component-field-types.md#related_list](references/component-field-types.md#related_list); mẫu `assets/sample_layout_create_order.json`.

**Layout Xem/Sửa (`functionLayout: 2` hoặc `3`)**

- 1-2 Layout Row. Row chính nhiều cột: 2 cột sidebar + main `colSpan` `1:2` hoặc `1:3`; 3 cột `1:2:1` (trái: liên hệ/tóm tắt; giữa: nội dung chính + tab; phải: bổ sung/metadata).
- Sidebar: avatar (`display_box`), liên hệ cơ bản, tóm tắt; hoặc owner và metadata. Group trong sidebar dùng `numberOfColumns: 1`.
- Cột chính: tiêu đề/tên (Group 1 cột) → field chính (Group 2 cột) → Tab-section (`typeSection: "menu"`) gom related list, activities, lịch sử; mỗi tab một nhóm related list liên quan (ví dụ "Activities", "Converted to", "Marketing Campaign").
- Field hệ thống (`created`, `updated`, `created_by`, `updated_by`, `last_activity_time`): section riêng hoặc sidebar/cột phụ, dưới cùng.
- Path Component: chỉ layout `functionLayout: 2` quyền `VIEW_EDIT`. Không chỉ định vị trí → Row đầu tiên, Row 1 Column (`numberOfColumns: 1`, `colSpan: 1`), Group `numberOfColumns: 1`, Section không border và không hiện tên. Đây là gợi ý UI, không phải ràng buộc schema; có thể đặt Row/Column khác nếu người dùng yêu cầu hoặc bố cục đủ rộng. Quy trình: mục "Đưa Path Component vào layout Xem/sửa".
- Related list editable trên xem/sửa: như layout tạo, nhưng `showingColumns` có thể thêm cột tính toán (`subtotal`); `_action_column` không cần trong `showingColumns` khi đã ở `pinnedColumns.right`; `orderBy: "created"` thay vì `"updated"` để giữ thứ tự dòng; đặt trong section riêng trên cột chính, lookup liên quan phía trên (Bảng giá trên bảng Sản phẩm).
- Record-level Object Button nằm ở `pageSettings.buttons.listButton`, không phải trong `content`. Quy trình: mục "Đặt Object Button lên layout xem/sửa".

**Mọi loại layout**

- Nhóm field theo ngữ nghĩa vào cùng section/group: cá nhân (họ, tên, danh xưng, chức danh); liên lạc (email, điện thoại, địa chỉ); công ty (tên, ngành, doanh thu, số nhân viên, website).
- Thứ tự: định danh (tên, tiêu đề, mã) → trạng thái/phân loại → nghiệp vụ chính (owner, giá trị, số lượng) → liên hệ → mô tả/ghi chú → hệ thống.
- Không group/section trống. Section hiện tiêu đề khi có từ 2 section; 1 section duy nhất có thể ẩn tiêu đề.
- Lookup quan trọng (owner, assigned_to): layout tạo ở section chính, layout xem ở sidebar. Ảnh đại diện ở đầu sidebar; file đính kèm cuối section hoặc section riêng.

### Bước 3: Dựng JSON

Dựng payload trong bộ nhớ để gửi API; **không tạo file JSON**. Schema từng cấp: [references/layout-json-structure.md](references/layout-json-structure.md) và `assets/sample_layout_1.json`; thuộc tính theo `fieldType`: [references/component-field-types.md](references/component-field-types.md); `pageSettings`: [references/page-settings.md](references/page-settings.md).

```text
content[] → layoutRow → layoutColumn → section (normal | menu) → tab → group → components[]
```

Quy tắc bắt buộc; sai sẽ gây lỗi UI "Cannot read properties of undefined (reading 'map')":

1. Container dùng `type` (`"layoutRow"`, `"layoutColumn"`, `"section"`, `"group"`), không dùng `fieldType`.
2. Phần tử con nằm trong `children` (row → column → section → tab → group); không dùng `layoutColumns`, `sections`, `tabs`, `groups`.
3. Group chứa field trong `components`, không phải `children`.
4. Field nằm trực tiếp trong `components`; không bọc dạng `{"component": {...}, "fieldType": "component"}`.
5. `id` của Object Field là Object Field ID (`OF...`), không phải UUID. Component đặc biệt không phải Object Field (`path_component`, `display_box`, `related_list`, `report`...) dùng UUID v4 riêng và không cần `fieldMetaData`.
6. `id` của layoutRow, layoutColumn, section, tab, group là UUID v4.
7. Field và component bắt buộc nằm trong Group; không đặt trực tiếp vào section hoặc tab.

Object Field component bắt buộc có `id` thật và `fieldMetaData` (chuỗi JSON stringify từ `metaData` của field). Thiếu thì layout vẫn tạo được nhưng không sửa/di chuyển/xoá được field trong layout editor, chỉ thêm mới từ palette.

`showFieldName` của lookup mặc định `"$record.name"`; lookup tới Personnel (`personnel`) dùng `"{$record.first_name} {$record.last_name}"`; Object có cách hiển thị tên riêng thì chỉnh tương ứng.

Tên và slug:

- `name` layout bắt buộc tiếng Anh, ngắn, theo chức năng (`Create`, `View/Edit`, `Create Order`); đầu vào ngôn ngữ khác thì dịch trước khi gọi API, không có ngoại lệ. Không gửi `Tạo`, `Xem`, `Chỉnh sửa`.
- UUID v4 cho `id` của mọi container và component đặc biệt không phải Object Field.
- Slug sinh mới: `{type_prefix}_{meaningful_name}`, tiếng Anh, chữ thường, `snake_case`, bất kể ngôn ngữ của tên layout/tên hiển thị. Prefix đúng loại: `layout_row_`, `layout_column_`, `section_`, `tab_`, `group_`, `related_list_`, `display_box_`, `report_`, `dashboard_`, `button_group_`, `path_component_`, `workflow_button_`. Đặt theo chức năng/nội dung hoặc suy từ vai trò, vị trí, field bên trong (`layout_column_contact_sidebar`, `section_system_information`, `group_address_fields`); tránh `section_1`, `group_new`; không thêm timestamp.
- Slug phải unique trên **toàn hệ thống**, không chỉ trong một layout: kiểm tra với slug đã có và mọi slug trong payload đang dựng. Chỉ thêm hậu tố khi trùng thật, dùng số nhỏ nhất chưa dùng (`group_address_fields`, `group_address_fields_2`, `_3`...). API báo slug đã tồn tại → tăng hậu tố và gọi lại.
- `uiSlug`: Object Field `{field_slug}_{số thứ tự}` (`name_1`, `status_1`); component sinh mới `{component_slug}_{số thứ tự}` (`display_box_contact_summary_1`).
- Không dịch hoặc đổi slug tham chiếu có sẵn: Object Field slug, `originSlug`, `dashboardSlug`, `pathComponentSlug`.

Quy tắc tạo layout:

1. `content` là array không rỗng; `null`, kiểu khác array hoặc `[]` là payload không hợp lệ.
2. Mỗi layoutRow ≥ 1 layoutColumn; layoutColumn ≥ 1 section; section ≥ 1 tab (section `normal` vẫn có 1 tab ẩn); tab ≥ 1 group; group ≥ 1 component.
3. `id` Object Field khớp `id` field trong Object definition.
4. Mỗi field chỉ xuất hiện một lần trong toàn layout, trừ khi ở tab khác nhau của section `menu`.
5. Tổng `colSpan` các cột = `numberOfColumns` của layoutRow.
6. Layout cho Object Form: theo mục "Phân loại layout".

### Bước 4: Kiểm tra trước khi gọi API

- Chặn payload rỗng: chỉ gọi `POST` khi `content` là array có phần tử; kiểm tra đệ quy từng cấp theo Quy tắc tạo layout.
- Layout Tạo: Row ngoài cùng có đúng bộ `maxWidth`/`unitMaxWidth`/`horizontalAlignment: "center"` (1000px hoặc 100% theo Bước 2); không nhầm với `pageSettings.settingContentPage`.
- `name` là tiếng Anh với mọi request tạo hoặc đổi `name`.
- Khi `$object-form` gọi: payload có `functionLayout: 1`, `ADD`, `isForm: 1`, `status: 1`, `isWeb: true`.
- Layout tham khảo có `content: null`, `[]` hoặc cấp con rỗng: không gửi và không thử lại cùng payload; dựng `content` mới rồi chạy lại toàn bộ kiểm tra.
- Đủ điều kiện thì gọi API ngay; chỉ chờ khi người dùng chủ động yêu cầu xem trước.

### Bước 5: Gọi API tạo và xác minh

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "objectTypeSlug": "{OBJECT_SLUG}",
    "name": "Create",
    "functionLayout": 3,
    "isForm": 0,
    "status": 1,
    "isWeb": true,
    "accessControls": [ ... ],
    "content": [ ... ],
    "pageSettings": { ... }
  }'
```

Hiển thị ID, tên, slug và link layout. Khi tạo cho `$object-form`: `functionLayout: 1`, `isForm: 1`, quyền `ADD`, `status: 1`, `isWeb: true`; view/list lại và chỉ trả ID khi khớp.

## Xem danh sách và chi tiết layout

- Danh sách: gọi `list` theo `objectTypeSlug`, hiển thị bảng ID, tên, slug, `functionLayout`, `isWeb`, `isMobile`, `status`.
- Chi tiết: gọi `view` theo ID.

## Lấy script đang có sẵn trên layout

1. View layout, đọc `data.pageSettings.script` (`jq -r '.data.pageSettings.script // ""'`).
2. Giá trị `null`, rỗng hoặc không tồn tại → trả lời rõ layout chưa có script.
3. Chỉ hiển thị script; không tự chỉnh sửa layout.

## Cập nhật script cho một layout

Chỉ thay đổi `pageSettings.script`; giữ `content`, `title`, quyền truy cập và cấu hình khác nếu không được yêu cầu.

1. View layout, dựng payload theo allowlist (mục "Layouts V2 API"), chỉ thay `pageSettings.script` bằng script mới; xoá script → `""` hoặc `null` theo payload hiện tại của hệ thống.
2. Ưu tiên dựng bằng `jq --rawfile` để giữ nguyên xuống dòng và dấu nháy; mẫu ở [references/layout-update-payload.md](references/layout-update-payload.md).
3. `PUT`, rồi view lại và so sánh `data.pageSettings.script`. Lỗi hoặc không khớp → báo và dừng.

## Cập nhật layout

1. View layout, hiển thị cấu trúc hiện tại, thu thập thay đổi, dựng `content`/`pageSettings` mới theo quy tắc ở "Tạo layout".
2. Payload theo allowlist; giữ nguyên phần không được yêu cầu thay đổi.
3. Mặc định cập nhật ngay; `PUT` rồi view lại để xác minh.

## Xoá layout

1. Resolve chính xác layout; hiển thị ID, tên, slug, đối tượng; nêu rõ hành động không thể hoàn tác.
2. Gọi `delete` ngay sau các kiểm tra bắt buộc; chỉ chờ xác nhận khi người dùng chủ động yêu cầu, hoặc hỏi làm rõ khi nhiều layout có thể khớp.
3. List/view lại để xác minh layout không còn tồn tại.

## Đặt Object Button lên layout xem/sửa

Đọc [references/record-button-placement.md](references/record-button-placement.md) trước. Dùng khi record-level Object Button đã tồn tại nhưng chưa xuất hiện trên màn hình bản ghi.

1. Xác minh button qua Object Buttons API `view`: `id`, `slug`, `objectTypeSlug`, trạng thái, icon. Không đoán ID/slug từ tên.
2. Button chỉ hiển thị trên màn danh sách (list action `16`/`19` hoặc luồng list/bulk tương ứng) → cấu hình ở màn danh sách/filter, không đặt vào record layout.
3. Resolve layout đích bằng ID hoặc list layout của Object: cùng `objectTypeSlug`, `functionLayout: 2` hoặc `3` có `VIEW_EDIT`. Nhiều layout theo quyền hoặc web/mobile → không tự cập nhật tất cả; yêu cầu người dùng chọn khi chưa đủ ngữ cảnh.
4. View layout ngay trước khi sửa; đọc `pageSettings.buttons`, chưa có thì khởi tạo theo schema trong reference.
5. Chống trùng theo `buttonId`: đã có thì không thêm bản sao, chỉ đổi cấu hình hiển thị khi được yêu cầu. Giữ nguyên thứ tự và toàn bộ entry hiện có; chèn vào vị trí người dùng yêu cầu, không chỉ định thì append cuối. Dùng ID, slug, icon thật của button; mặc định quan sát được `type: "gray"`, `size: "medium"`, `customName: null`.
6. Payload theo allowlist, chỉ thay `pageSettings.buttons`; `PUT` rồi view lại. Thành công khi `pageSettings.buttons.listButton` có đúng một entry với `buttonId` mục tiêu và các button cũ vẫn nguyên.

Gỡ button khỏi layout chỉ làm button không hiển thị trên layout đó, không xoá Object Button. Xoá Object Button không tự gỡ tham chiếu trên layout → kiểm tra các layout liên quan trước khi xoá.

## Đưa Path Component vào layout Xem/sửa

Dùng khi Path Component đã tồn tại trên Object và cần hiển thị trên màn hình bản ghi. Schema component và Row mặc định: [references/component-field-types.md#path_component](references/component-field-types.md#path_component).

Ràng buộc:

- Layout đích phải `functionLayout: 2` và có `VIEW_EDIT`; không đưa vào layout `1` hoặc `3`.
- Path phải active và cùng `objectTypeSlug`; resolve bằng `$object-path-component` (thao tác read) theo ID/URL/slug, không đoán slug.
- Layout lưu slug thật của Path trong `pathComponentSlug`, không lưu Path ID `PC...`; từ URL/ID phải resolve detail rồi lấy `path.slug`.
- `id` component là UUID v4 mới, không phải Path ID hay Object Field ID; không cần `fieldMetaData`.
- Duyệt đệ quy toàn bộ `content`: đã có đúng một component cùng `pathComponentSlug` → idempotent, không thêm bản sao; nhiều bản sao hoặc có Path khác tại vị trí đích → báo rõ, không tự xoá hay thay thế.
- Giữ `hasComponentPath` đúng như response, kể cả `null`; không tự set `1`.
- Tạo mới: slug `path_component_<name>` tiếng Anh `snake_case`, unique toàn hệ thống, sinh `uiSlug` tương ứng; `useLayouts: [2]`, `status: 1`, `isPinned: false` trừ khi người dùng yêu cầu khác. Di chuyển component có sẵn: giữ nguyên `id`, `slug`, `uiSlug`.

Quy trình:

1. Resolve Path detail và layout detail mới nhất; xác minh Path active, cùng Object; layout `functionLayout: 2`, có `VIEW_EDIT`, `content` hợp lệ.
2. Duyệt mọi `group.components` để kiểm tra trùng `pathComponentSlug` và thu thập mọi `id`, `slug`, `uiSlug` đang tồn tại.
3. Dựng component. Không chỉ định vị trí → dựng Row mặc định và prepend vào `content`; có vị trí → merge component vào Group đích, không dựng lại phần còn lại.
4. Kiểm tra hierarchy không rỗng, UUID và slug unique, mỗi `pathComponentSlug` mục tiêu chỉ xuất hiện một lần.
5. Payload theo allowlist, `PUT`, view lại. Thành công khi: layout vẫn `functionLayout: 2`; có đúng một component active `fieldType: "path_component"` với `pathComponentSlug` mục tiêu, nằm đúng vị trí; Row/component cũ và top-level setting không đổi ngoài diff dự kiến.

## Xử lý lỗi đặc thù

| Tình huống | Xử lý |
|---|---|
| Layout tham khảo có `content: null`, `[]` hoặc cấp con rỗng | Không dùng làm payload, không gọi API với nó; dựng `content` mới từ fields và asset mẫu rồi kiểm tra lại hierarchy |
| API trả slug đã tồn tại | Tăng hậu tố số của slug và gọi lại |
| Field người dùng nêu không có trong Object | Báo field không tồn tại trong Object và hỏi lại |
| Update trả thành công nhưng view không khớp | Báo dữ liệu chưa được lưu đúng và dừng; không fallback endpoint khác |
| 401/403, 422 hoặc `r` khác `0`, 5xx | Theo `$cogover-api-auth`; hiển thị `r`, `msg`; không đổi endpoint hay cơ chế xác thực |
