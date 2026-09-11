# Thuộc tính component theo fieldType

Bổ sung cho các trường chung ở [layout-json-structure.md#component](layout-json-structure.md#component). Object Field giữ `id` thật và `fieldMetaData`; component đặc biệt (`report`, `dashboard`, `tracking_history`, `path_component`, `display_box`, `related_list`, `button_group`, `workflow_button`, `up_next_task`) dùng `id` UUID v4, `slug` theo prefix của loại (quy tắc trong [SKILL.md](../SKILL.md)) và không cần `fieldMetaData`.

## lookup_normal và lookup_dependency

`showFieldName` mặc định `"$record.name"`. Lookup trỏ tới Object Personnel (slug `personnel`) dùng `"{$record.first_name} {$record.last_name}"`; Object khác có cách hiển thị tên riêng thì chỉnh tương ứng.

```json
{
  "isAddRecord": true,
  "typeView": "field",
  "layoutViewId": "",
  "showFieldName": "$record.name",
  "showFieldAvatar": "",
  "listAction": [{"value": "Value 1"}],
  "fieldMetaData": "{\"object\":\"OT...\",\"object_slug\":\"...\"}",
  "combineAction": false,
  "menuAction": [],
  "numberRecord": 1,
  "numberColumn": 1,
  "showBorder": true,
  "showLine": true,
  "gap": 20,
  "useHeight": false,
  "heightList": 100,
  "orderBy": "updated",
  "orderType": "asc",
  "allowSort": true,
  "isHoverShowRecord": true,
  "isWrapText": true,
  "layoutHover": "",
  "popupWidth": 350,
  "popupHeight": 450,
  "multiple": 0
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `showFieldAvatar` | String | ID field avatar hiển thị cạnh tên bản ghi lookup; trống nếu không dùng |
| `layoutHover` | String | ID layout cho popup preview khi hover; trống nếu không dùng |
| `popupWidth` / `popupHeight` | Number | Kích thước popup preview (px). Mặc định `350` / `450` |

## file

```json
{
  "fieldMetaData": "{\"file_type\":[\"jpg\",\"jpeg\",\"png\"],\"is_public\":false,\"multiple_limit\":{\"min\":1,\"max\":10},\"file_group_type\":\"avatar\",\"max_size\":5242880,\"is_resizable\":false}",
  "radius": "50%",
  "size": 75,
  "objectFit": "cover",
  "altField": [{"value": "OF..."}]
}
```

## long_text

```json
{ "maxHeight": 400 }
```

## select

```json
{
  "displayTypeOptions": 2,
  "fieldMetaData": "{\"option_display_type\":2}"
}
```

## boolean

```json
{ "labelPlacement": "right" }
```

## phone

```json
{ "showButtonCall": true, "showWhenHover": true }
```

`showButtonCall`: nút gọi điện cạnh trường (mặc định `true`); `showWhenHover`: chỉ hiện nút gọi khi hover (mặc định `true`).

## rating

```json
{ "type": "horizontal", "sizeIcon": 24 }
```

`type`: `"horizontal"` (mặc định) hoặc `"vertical"`; `sizeIcon`: kích thước icon px (mặc định `24`).

## report

```json
{
  "id": "<uuid>",
  "fieldType": "report",
  "status": 1,
  "slug": "report_sales_performance",
  "name": "report",
  "label": "report",
  "uiSlug": "report_sales_performance_1",
  "useLayouts": [2],
  "reportId": "RV...",
  "reportTypeId": "RTV...",
  "logicSequence": null,
  "filterItems": [],
  "reportHeight": 300,
  "isShowName": true,
  "customName": null
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `useLayouts` | Array | `[2]` chỉ view/edit; `[3, 2]` cả tạo và view/edit |
| `reportId` | String | **Bắt buộc.** ID báo cáo (`RV...`) từ danh sách báo cáo trên hệ thống |
| `reportTypeId` | String/null | ID loại báo cáo (`RTV...`); `null` = mặc định |
| `logicSequence` | String/null | Biểu thức logic lọc, ví dụ `"1 AND 2 OR 3"`; `null` = không lọc |
| `filterItems` | Array | Bộ lọc, dùng operator bên dưới |
| `reportHeight` | Number | px. Mặc định `300` |
| `isShowName` | Boolean | Mặc định `true` |
| `customName` | String/null | `null` = dùng tên gốc |

Filter operators: `=`, `!=`, `<`, `>`, `<=`, `>=`, `like`, `not like`, `contains any`, `not contains any`, `is null`, `not null`, `startsWith`, `endsWith`, `in`, `not in`, `between`, `rangeWithin`, `rangeContains`.

Filter ngày: `Yesterday`, `Today`, `Tomorrow`, `Last n days`, `Next n days`, `n Days ago`, `n Days from now`, `Last week`, `This week`, `Next week`, `Last n weeks`, `Next n weeks`, `Last month`, `This month`, `Next month`, `Last n months`, `Next n months`, `Last quarter`, `This quarter`, `Next quarter`, `Last year`, `This year`, `Next year`, `Last n years`, `Next n years`.

## dashboard

```json
{
  "id": "<uuid>",
  "fieldType": "dashboard",
  "status": 1,
  "slug": "dashboard_sales_overview",
  "name": "dashboard",
  "label": "dashboard",
  "uiSlug": "dashboard_sales_overview_1",
  "useLayouts": [2],
  "dashboardSlug": "inbound_calls",
  "dashboardHeight": 300,
  "reportFilters": [],
  "isShowName": true,
  "customName": null
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `useLayouts` | Array | `[2]` = chỉ view/edit |
| `dashboardSlug` | String | **Bắt buộc.** Slug dashboard từ danh sách dashboard trên hệ thống |
| `dashboardHeight` | Number | px. Mặc định `300` |
| `reportFilters` | Array | Bộ lọc cho các report trong dashboard. Mặc định `[]` |
| `isShowName` | Boolean | Mặc định `true` |
| `customName` | String/null | `null` = dùng tên gốc |

## button_group

Component `button_group` nằm trong `content`, nhúng nhóm nút tại một vị trí của bố cục; các nút lấy từ Object Button của Object. Cụm action mặc định trên header màn xem/sửa nằm ở `pageSettings.buttons` (xem [record-button-placement.md](record-button-placement.md)). Khi chỉ cần record-level button xuất hiện trên màn xem bản ghi, cập nhật `pageSettings.buttons.listButton`; không tự tạo `button_group` trong `content`.

```json
{
  "id": "<uuid>",
  "fieldType": "button_group",
  "status": 1,
  "slug": "button_group_primary_actions",
  "name": "button_group",
  "label": "button_group",
  "uiSlug": "button_group_primary_actions_1",
  "buttonPosition": "right",
  "combineAction": false,
  "menuIcon": "ellipsis-vertical",
  "gap": 8,
  "listButton": [
    {
      "buttonId": "BU...",
      "type": "contained",
      "size": "medium",
      "useIcon": false,
      "onlyShowIcon": false,
      "icon": null,
      "slug": "convert",
      "iconDarkMode": null
    }
  ]
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `buttonPosition` | String | `"left"`, `"right"` (mặc định), `"center"` |
| `combineAction` | Boolean | Gom các nút thành menu dropdown. Mặc định `false` |
| `menuIcon` | String | Icon menu khi `combineAction: true`. Mặc định `"ellipsis-vertical"` |
| `gap` | Number | px. Mặc định `8` |
| `listButton[].buttonId` | String | **Bắt buộc.** ID button (`BU...`) từ danh sách button của Object |
| `listButton[].type` | String | `"contained"` (nền đặc), `"outlined"` (viền), `"text"` |
| `listButton[].size` | String | `"small"`, `"medium"` (mặc định), `"large"` |
| `listButton[].useIcon` | Boolean | Mặc định `false` |
| `listButton[].onlyShowIcon` | Boolean | Chỉ hiển thị icon, ẩn text. Mặc định `false` |
| `listButton[].icon` / `iconDarkMode` | String/null | Đường dẫn hoặc tên icon; `null` = mặc định / dùng chung icon |
| `listButton[].slug` | String | Slug button (`"convert"`, `"cancel"`) |

## tracking_history

```json
{
  "id": "<uuid>",
  "fieldType": "tracking_history",
  "status": 1,
  "slug": "tracking_history_<timestamp>",
  "name": "tracking_history",
  "label": "tracking_history",
  "uiSlug": "tracking_history_<timestamp>_1",
  "useLayouts": [3, 2],
  "recordCount": 10
}
```

`useLayouts: [3, 2]` = dùng cho cả tạo+xem và xem/sửa; `recordCount`: số bản ghi lịch sử hiển thị (mặc định `10`).

## up_next_task

```json
{
  "id": "<uuid>",
  "fieldType": "up_next_task",
  "status": 1,
  "slug": "up_next_task_<timestamp>",
  "name": "up_next_task",
  "label": "Up Next Task",
  "uiSlug": "up_next_task_<timestamp>_1"
}
```

## workflow_button

```json
{
  "id": "<uuid>",
  "fieldType": "workflow_button",
  "status": 1,
  "slug": "workflow_button_approval_actions",
  "name": "workflow_button",
  "label": "Workflow Button",
  "uiSlug": "workflow_button_approval_actions_1"
}
```

## path_component

Chỉ dùng trên layout Xem/sửa (`functionLayout: 2`). Quy trình resolve, merge và verify: mục "Đưa Path Component vào layout Xem/sửa" trong [SKILL.md](../SKILL.md).

Schema đã quan sát từ Layouts V2:

```json
{
  "id": "<uuid-v4>",
  "fieldType": "path_component",
  "status": 1,
  "slug": "path_component_contract_status",
  "name": "path_component",
  "label": "path_component",
  "uiSlug": "path_component_contract_status_1",
  "useLayouts": [2],
  "pathComponentSlug": "contract_status_path",
  "isPinned": false
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | String | UUID v4 riêng của layout component; không dùng Path ID `PC...` hay Object Field ID `OF...` |
| `useLayouts` | Array | Bắt buộc `[2]` |
| `pathComponentSlug` | String | **Bắt buộc.** Slug thật của Path đã resolve trên cùng Object (`path.slug`); không điền Path ID `PC...` |
| `slug` | String | Identity của layout component, prefix `path_component_`, unique toàn hệ thống; không phải `pathComponentSlug` |
| `uiSlug` | String | Sinh từ `slug` của component, unique trong layout |
| `status` | Number | `1` (đã xác minh) |
| `isPinned` | Boolean | Mặc định `false` nếu người dùng không yêu cầu khác |

Không cần `fieldMetaData`. Khi di chuyển component có sẵn, giữ nguyên `id`, `slug`, `uiSlug`.

### Row mặc định tối giản cho Path Component

Dùng khi người dùng không chỉ định vị trí: prepend Row này vào đầu `content`. Row/Column/Section/Group không border, không hiện tên, không padding để Path đủ chiều ngang.

```json
{
  "id": "<row-uuid>",
  "type": "layoutRow",
  "numberOfColumns": 1,
  "gap": 20,
  "slug": "layout_row_contract_status_path",
  "isShowChildren": true,
  "isBorder": false,
  "paddingLeft": 0,
  "paddingRight": 0,
  "paddingTop": 0,
  "paddingBottom": 0,
  "children": [
    {
      "id": "<column-uuid>",
      "type": "layoutColumn",
      "colSpan": 1,
      "name": null,
      "slug": "layout_column_contract_status_path",
      "isShowName": false,
      "isShowChildren": true,
      "isBorder": false,
      "paddingLeft": 0,
      "paddingRight": 0,
      "paddingTop": 0,
      "paddingBottom": 0,
      "gap": 20,
      "children": [
        {
          "id": "<section-uuid>",
          "type": "section",
          "typeSection": "normal",
          "numberOfTabs": 1,
          "name": null,
          "slug": "section_contract_status_path",
          "isShowName": false,
          "isShowChildren": true,
          "isBorder": false,
          "paddingLeft": 0,
          "paddingRight": 0,
          "paddingTop": 0,
          "paddingBottom": 0,
          "gap": 20,
          "displayUnderline": false,
          "children": [
            {
              "id": "<tab-uuid>",
              "name": null,
              "slug": "tab_contract_status_path",
              "isShowChildren": true,
              "children": [
                {
                  "id": "<group-uuid>",
                  "type": "group",
                  "name": null,
                  "slug": "group_contract_status_path",
                  "numberOfColumns": 1,
                  "canCollapse": false,
                  "isShowName": false,
                  "isShowChildren": true,
                  "isBorder": false,
                  "paddingLeft": 0,
                  "paddingRight": 0,
                  "paddingTop": 0,
                  "paddingBottom": 0,
                  "gap": 12,
                  "tabKey": 1,
                  "components": [
                    {
                      "id": "<component-uuid>",
                      "fieldType": "path_component",
                      "status": 1,
                      "slug": "path_component_contract_status",
                      "name": "path_component",
                      "label": "path_component",
                      "uiSlug": "path_component_contract_status_1",
                      "useLayouts": [2],
                      "pathComponentSlug": "contract_status_path",
                      "isPinned": false
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## display_box

Nội dung tùy chỉnh dạng HTML, ReactJS, Text hoặc Markdown; bắt buộc nằm trong Group.

```json
{
  "id": "<uuid>",
  "fieldType": "display_box",
  "status": 1,
  "slug": "display_box_contact_summary",
  "displayBoxType": "react",
  "content": "<code ReactJS hoặc HTML>",
  "name": "display_box",
  "label": "display_box",
  "uiSlug": "display_box_contact_summary_1",
  "displayBoxFields": [{"slug": "avatar", "size": 98}]
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | String | UUID v4 |
| `slug` | String | `display_box_<meaningful_name>` |
| `displayBoxType` | String | `"react"`, `"html"`, `"text"`, `"markdown"` |
| `content` | String | Code hoặc nội dung; escape `"` thành `\"`, xuống dòng thành `\n` |
| `name` / `label` | String | Thường là `"display_box"` |
| `uiSlug` | String | `{component_slug}_{số thứ tự}` |
| `displayBoxFields` | Array | Các field dùng qua `<Field />`, mỗi phần tử gồm `slug` và props; `[]` nếu không dùng `<Field />` |

Viết nội dung:

- `$record` là bản ghi hiện tại; truy cập `$record.field_slug` hoặc `$record?.field_slug` để tránh lỗi null.
- `displayBoxType: "react"`: code phải kết thúc bằng `render(<App />);`.
- `<Field slug="field_slug" />` render field đặc biệt (ví dụ avatar); props `slug` (bắt buộc), `size` (px), `alt`. Field dùng trong `<Field />` phải khai báo trong `displayBoxFields`.
- CSS variables hệ thống: `var(--primary-main)`, `var(--typography-primary)`, `var(--typography-secondary)`.
- `"text"` và `"markdown"`: nội dung thuần/Markdown, có thể dùng `$record.field_slug`.

Ví dụ ReactJS: avatar và thông tin nhân sự.

```json
{
  "id": "00000000-0000-4000-8000-000000000402",
  "fieldType": "display_box",
  "status": 1,
  "slug": "display_box_person_profile",
  "displayBoxType": "react",
  "content": "const App = () => {\n    return (\n        <div style={{ borderRadius: \"4px\", overflow: \"hidden\", paddingBottom: \"73px\", position: \"relative\" }}>\n            <div style={{ backgroundColor: \"var(--primary-main)\", height: \"90px\", position: \"relative\" }}>\n                <img\n                    src=\"/images/personal-cover-bg.png\"\n                    style={{ position: \"absolute\", top: 0, left: 0, width: \"100%\", height: \"100%\", objectFit: \"cover\" }}\n                />\n                <div style={{ position: \"absolute\", top: \"100%\", left: \"24px\", transform: \"translateY(-50%)\" }}>\n                    <Field slug=\"avatar\" size={98} alt={$record?.first_name} />\n                </div>\n            </div>\n            <div style={{ position: \"absolute\", left: \"137px\", top: \"100px\", maxWidth: \"calc(100% - 156px)\" }}>\n                <p style={{ fontSize: \"14px\", fontWeight: 700, lineHeight: \"142.857%\", color: \"var(--typography-primary)\", maxWidth: \"100%\", overflowWrap: \"break-word\" }}>\n                    {$record?.name || \"\"} {$record?.first_name || \"\"}\n                </p>\n                <p style={{ color: \"var(--typography-secondary)\", fontSize: \"14px\", fontWeight: 400, lineHeight: \"142.857%\", maxWidth: \"100%\", overflowWrap: \"break-word\" }}>\n                    {$record?.account_email || $record?.work_email || $record?.emails?.[0] || \"\"}\n                </p>\n            </div>\n        </div>\n    );\n};\nrender(<App />);",
  "name": "display_box",
  "label": "display_box",
  "uiSlug": "display_box_person_profile_1",
  "displayBoxFields": [{"slug": "avatar", "size": 98}]
}
```

## related_list

Khi Object B có lookup trỏ tới Object A, hệ thống tự tạo Related List trên A. Đặt `related_list` vào layout của A để hiển thị các bản ghi B trỏ về bản ghi A đang xem. Ví dụ: "Order Product Line" có lookup `order` tới "Order" → Related List `Order_Product_lines` trên Order.

```json
{
  "id": "<uuid>",
  "fieldType": "related_list",
  "slug": "related_list_order_items",
  "relatedListId": "RL...",
  "fePlaceholder": false,
  "originSlug": "slug_object_con",
  "status": 1,
  "showFieldName": "{$record.name}",
  "typeView": "field",
  "label": "Tên hiển thị"
}
```

| Trường | Mô tả |
|---|---|
| `relatedListId` | ID danh sách liên quan (`RL...`), lấy từ `POST /bapi/v1/objects/list` |
| `originSlug` | Slug Object con (Object chứa lookup), ví dụ `order_product_line` |
| `slug` | `related_list_<meaningful_name>` |
| `showFieldName` | Trường hiển thị của bản ghi, ví dụ `{$record.name}` |

### typeView

| Giá trị | Mô tả | Yêu cầu thêm |
|---|---|---|
| `"field"` | Dạng field đơn giản | Không |
| `"list"` | Dạng bảng | `tableSettings` |
| `"card"` | Dạng thẻ | `layoutViewId` (layout render thẻ) |
| `"layout_create"` | Form tạo bản ghi nhúng | `layoutViewId` (layout tạo bản ghi) |
| `"timeline"` | Dòng thời gian | `activityTypeAllow` nếu `isAllTabActivity: false` |

### Thuộc tính khi typeView là list

```json
{
  "typeView": "list",
  "listAction": [{"value": "CREATE"}],
  "combineAction": false,
  "menuAction": [],
  "hideWhenNoData": false,
  "numberRecord": 1,
  "numberColumn": 1,
  "showBorder": true,
  "showLine": true,
  "gap": 20,
  "useHeight": false,
  "heightList": 100,
  "orderBy": "updated",
  "orderType": "asc",
  "allowSort": true,
  "isAddRecord": true,
  "tableSettings": "<chuỗi JSON, xem bên dưới>"
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `listAction` | Array | Hành động trên danh sách; `[{"value": "CREATE"}]` cho phép tạo bản ghi mới |
| `combineAction` | Boolean | Gom hành động. Mặc định `false` |
| `menuAction` | Array | Hành động trong menu. Mặc định `[]` |
| `hideWhenNoData` | Boolean | Mặc định `false` |
| `numberRecord` | Number | Bản ghi mỗi trang. Mặc định `1` |
| `numberColumn` | Number | Mặc định `1` |
| `showBorder` / `showLine` | Boolean | Mặc định `true` |
| `gap` | Number | Mặc định `20` |
| `useHeight` / `heightList` | Boolean / Number | Chiều cao cố định; `heightList` (px) khi `useHeight: true`. Mặc định `false` / `100` |
| `orderBy` / `orderType` | String | Mặc định `"updated"` / `"asc"` (`"desc"`) |
| `allowSort` | Boolean | Mặc định `true` |
| `isAddRecord` | Boolean | Mặc định `true` |
| `isAllTabActivity` | Boolean | Hiển thị tất cả tab hoạt động (timeline/activity). Mặc định `true` |
| `activityTypeAllow` | Array | Loại hoạt động cho phép; rỗng = tất cả; ít nhất 1 phần tử nếu `isAllTabActivity: false` |
| `tableSettings` | String | Cấu hình bảng dạng **chuỗi JSON**, chỉ dùng khi `typeView: "list"` |

### tableSettings

`tableSettings` là chuỗi JSON (string, không phải object), escape quotes. Cấu trúc bên trong:

```json
{
  "columns": [
    {"key": "field_slug", "width": 150},
    {"key": "_action_column", "width": 40}
  ],
  "pinnedColumns": { "left": [], "right": ["_action_column"] },
  "showingColumns": ["field_slug_1", "field_slug_2", "_action_column"],
  "editableColumns": []
}
```

Dạng gửi lên API:

```json
"tableSettings": "{\"columns\":[{\"key\":\"serial\",\"width\":90},{\"key\":\"name\",\"width\":300}],\"pinnedColumns\":{\"left\":[],\"right\":[\"_action_column\"]},\"showingColumns\":[\"serial\",\"name\",\"_action_column\"],\"editableColumns\":[]}"
```

| Trường | Mô tả |
|---|---|
| `columns` | Tất cả cột có thể hiển thị: `key` (slug trường), `width` (px) |
| `pinnedColumns` | `left` / `right`; thường ghim `_action_column` bên phải |
| `showingColumns` | Cột thực sự hiển thị; thứ tự trong mảng là thứ tự cột |
| `editableColumns` | Cột cho sửa trực tiếp trên bảng. Mặc định `[]` |

`_action_column` (xem/sửa/xoá) luôn `width: 40`; đặt cuối `columns`, cuối `showingColumns` và trong `pinnedColumns.right`. Trên layout xem/sửa, cột đã pinned tự hiển thị nên không cần đưa vào `showingColumns`.

### Quy tắc thiết kế tableSettings

1. `showingColumns`: chỉ cột cần cho nghiệp vụ, 5-10 cột. Bỏ cột lookup trỏ về Object đang xem (related_list Ticket trên layout Contact → bỏ cột `contact`). Ưu tiên mã/serial, tên/tiêu đề, trạng thái, người phụ trách, loại, mức ưu tiên. Bỏ cột hệ thống ít dùng: `id`, `created_by`, `updated_by`, `last_activity_time`, `call_id`.
2. `width` (px) theo loại cột: mã/serial (auto_number) `80-100`; tên/tiêu đề `250-400`; select/status `100-140`; lookup `150-200`; lookup personnel `130-160`; datetime/date `160-200`; boolean `80-100`; long_text `200-300`; file `150-200`; `_action_column` `40`.
3. Thứ tự: mã → tên → trạng thái → người phụ trách → cột nghiệp vụ → ngày tháng → `_action_column`.

### editableColumns

Dùng khi người dùng nhập/sửa trực tiếp trên bảng, đặc biệt trên layout tạo bản ghi có danh sách con.

- Đưa vào: cột người dùng cần nhập (sản phẩm lookup, số lượng, đơn giá, đơn vị, chiết khấu, thuế, phí...).
- Không đưa vào: cột tính toán (`formula`, `rollup_summary`: thành tiền, tổng); cột hệ thống (`id`, `name` nếu là `auto_number`, `created`, `updated`, `created_by`, `updated_by`); cột chỉ đọc (`manualModifyAllow: false`, `readOnly: true`); cột lookup trỏ về Object cha (tự gán khi tạo con từ cha).
- Ví dụ layout tạo Đơn hàng, bảng "Sản phẩm trong đơn hàng": `editableColumns: ["product", "quantity", "price_per_unit", "unit", "discount_by_unit", "tax_by_unit", "fee_by_unit"]`; `showingColumns` = các cột editable + cột tính toán chỉ xem `total_price` + `_action_column`; cột `order` (lookup về Order) bị loại vì thừa. Trên layout xem/sửa thêm `subtotal` vào `showingColumns`, `listAction` `CREATE_PRODUCT_LINE`/`DELETE`, `orderBy: "created"`.
- Mẫu: `assets/sample_layout_create_order.json`.
