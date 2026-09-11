# Cấu trúc JSON Layout

Schema từng cấp của payload Layouts V2. Quy tắc bắt buộc về `type`/`children`/`components`/ID, quy tắc UUID/slug và quy tắc tạo layout nằm trong [SKILL.md](../SKILL.md); thuộc tính riêng theo `fieldType` ở [component-field-types.md](component-field-types.md); `pageSettings` ở [page-settings.md](page-settings.md). Mẫu thật: `assets/sample_layout_1.json`.

## Cấu trúc top-level

```json
{
  "name": "Create",
  "objectTypeSlug": "slug_doi_tuong",
  "status": 1,
  "type": 2,
  "updateRecordMode": 4,
  "accessControls": [
    { "functions": ["ADD", "VIEW_EDIT"], "option": 1, "items": [], "type": "personnel" }
  ],
  "hasComponentPath": 0,
  "content": [ /* mảng layoutRow */ ],
  "title": {
    "id": "<uuid>",
    "slug": "title_<timestamp>",
    "value": "",
    "valueType": "html",
    "valueIsRaw": false,
    "valuePathName": "",
    "valueDataType": "",
    "isShowTitle": true,
    "isShowHelpText": false,
    "helpText": ""
  },
  "pageSettings": { /* xem page-settings.md */ },
  "functionLayout": 3,
  "isWeb": true,
  "isMobile": false,
  "isForm": 0
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `name` | String | Tên layout, bắt buộc tiếng Anh |
| `objectTypeSlug` | String | Slug của Object (`product`, `lead`) |
| `status` | Number | `1` = active |
| `type` | Number | `0` Custom layout, `1` Standard layout, `2` record detail (mặc định) |
| `updateRecordMode` | Number | `4` = mặc định |
| `accessControls` | Array | `type`: `"personnel"` (nhân sự), `"position"` (chức vụ), `"department"` (phòng ban), `"role"` (vai trò); `option: 1` tất cả, `option: 2` chỉ định cụ thể kèm `items`; `functions` theo loại layout |
| `hasComponentPath` | Number/null | `0`, `1` hoặc `null`. Không suy ra sự hiện diện của Path Component từ trường này: layout thật có `path_component` trong `content` vẫn có thể trả `null`. Khi update giữ nguyên giá trị response; không đổi thành `1`, không chuẩn hoá `null` thành `0`. Xác định Path bằng cách duyệt `content` tìm `fieldType: "path_component"` |
| `content` | Array | Mảng `layoutRow` |
| `title` | Object | `value`; `valueType` `"text"`/`"html"`/`"react"`/`"markdown"`; `valueIsRaw` (nội dung raw); `valuePathName` (tham chiếu data path); `valueDataType`; `isShowTitle`; `isShowHelpText`; `helpText` |
| `pageSettings` | Object | Cấu hình trang (padding, màu, breadcrumb, script, buttons) |
| `functionLayout` | Number | `1` Tạo, `2` Xem/Sửa, `3` Tạo/Xem/Sửa |
| `isWeb`, `isMobile` | Boolean | Layout dùng cho Web / Mobile |
| `isForm` | Number/Boolean | `1`/`true` = layout nhập liệu Object Form có thể chọn; `0`/`false` = layout thường |

## Phân cấp

```text
content[]
└── layoutRow
    └── layoutColumn
        └── section (typeSection "normal" | "menu")
            └── tab
                └── group
                    └── components[]  (field / component)
```

## Ví dụ cấu trúc đúng tối giản

```json
{
  "content": [
    {
      "id": "<uuid>",
      "type": "layoutRow",
      "numberOfColumns": 2,
      "gap": 20,
      "slug": "layout_row_main_content",
      "isShowChildren": true,
      "isBorder": false,
      "paddingLeft": 0, "paddingRight": 0, "paddingTop": 0, "paddingBottom": 0,
      "children": [
        {
          "id": "<uuid>",
          "type": "layoutColumn",
          "colSpan": 1,
          "name": "",
          "slug": "layout_column_main_information",
          "isShowName": false,
          "isShowChildren": true,
          "isBorder": false,
          "paddingLeft": 0, "paddingRight": 0, "paddingTop": 0, "paddingBottom": 0,
          "gap": 20,
          "children": [
            {
              "id": "<uuid>",
              "type": "section",
              "typeSection": "normal",
              "numberOfTabs": 1,
              "name": "Section Name",
              "slug": "section_system_information",
              "isShowName": true,
              "isShowChildren": true,
              "isBorder": true,
              "paddingLeft": 20, "paddingRight": 20, "paddingTop": 24, "paddingBottom": 24,
              "gap": 20,
              "displayUnderline": false,
              "children": [
                {
                  "id": "<uuid>",
                  "name": "",
                  "slug": "tab_basic_information",
                  "isShowChildren": true,
                  "children": [
                    {
                      "id": "<uuid>",
                      "type": "group",
                      "name": "",
                      "numberOfColumns": 2,
                      "canCollapse": false,
                      "slug": "group_system_fields",
                      "isShowName": false,
                      "isShowChildren": true,
                      "isBorder": false,
                      "paddingLeft": 0, "paddingRight": 0, "paddingTop": 0, "paddingBottom": 0,
                      "gap": 12,
                      "tabKey": 1,
                      "components": [
                        {
                          "id": "OF...",
                          "name": "Field Name",
                          "status": 1,
                          "slug": "field_slug",
                          "fieldType": "short_text",
                          "required": 0,
                          "manualModifyAllow": true,
                          "showLabel": true,
                          "showIcon": true,
                          "isLinkRedirect": true,
                          "labelPlacement": "top",
                          "labelAlign": "left",
                          "enabledAISearch": false,
                          "label": "Field Label",
                          "uiSlug": "field_slug_1",
                          "fieldMetaData": "{...}"
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
  ]
}
```

## Phân loại thành phần

### Container

| Thành phần | Mô tả |
|---|---|
| Section | `type: "section"`, `typeSection: "normal"`, `numberOfTabs: 1` |
| Tab-section | `type: "section"`, `typeSection: "menu"`, `numberOfTabs ≥ 2`; mỗi tab là một trang riêng |
| Group | Chứa field, bố trí theo `numberOfColumns`. `type`: `"group"` (mặc định), `"accountGroup"` (group cho account), `"departmentPositionGroup"` (group cho phòng ban/chức vụ) |
| Display Box | `fieldType: "display_box"`, nội dung HTML/ReactJS/Text/Markdown; phải nằm trong Group; dùng cho avatar card, banner, UI phức tạp |
| Button Group | `fieldType: "button_group"`, nhóm nút hành động nhúng tại một vị trí trong `content` |

### Field và component đặc biệt

| `fieldType` | Mô tả |
|---|---|
| Field của Object | `short_text`, `boolean`, `lookup_normal`, `file`, ... theo `$object-info` |
| `related_list` | Danh sách bản ghi từ Object khác có lookup trỏ về Object hiện tại |
| `report` | Nhúng báo cáo với bộ lọc tùy chỉnh |
| `dashboard` | Nhúng dashboard |
| `tracking_history` | Lịch sử thay đổi/hoạt động của bản ghi |
| `up_next_task` | Task tiếp theo cần thực hiện |
| `path_component` | Lộ trình trạng thái (pipeline stages) của bản ghi |
| `smart_paste` | Dán thông minh từ clipboard vào các trường |
| `workflow_button` | Nút kích hoạt workflow |
| `display_text` | Nội dung text tĩnh |

### Lookup và quan hệ

| `fieldType` | Mô tả |
|---|---|
| `lookup_normal` | Lookup tiêu chuẩn |
| `lookup_parent` | Lookup cha (quan hệ cha-con) |
| `lookup_peer2peer` | Lookup ngang hàng |
| `embedded` | Bản ghi nhúng: hiển thị bản ghi con trực tiếp trong layout cha |
| `reference` | Tham chiếu tới bản ghi khác |
| `children` | Danh sách bản ghi con |
| `department_personnel_select` | Chọn nhân sự/phòng ban |

Mọi field và component đều phải nằm trong một Group.

## layoutRow

```json
{
  "id": "<uuid>",
  "type": "layoutRow",
  "numberOfColumns": 2,
  "gap": 20,
  "maxWidth": 1000,
  "unitMaxWidth": "px",
  "horizontalAlignment": "center",
  "slug": "layout_row_main_content",
  "name": "",
  "isShowChildren": true,
  "isBorder": false,
  "paddingLeft": 0,
  "paddingRight": 0,
  "paddingTop": 0,
  "paddingBottom": 0,
  "children": [ /* mảng layoutColumn */ ]
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | String | UUID v4 |
| `type` | String | Luôn `"layoutRow"` |
| `numberOfColumns` | Number | Số cột trong hàng; tổng `colSpan` của các cột phải bằng giá trị này |
| `gap` | Number | Khoảng cách giữa các cột (px). Mặc định `20` |
| `maxWidth` | Number | Chiều rộng tối đa của Row, đơn vị theo `unitMaxWidth`. Layout Tạo dạng form thường: `1000`; Row chứa bảng rộng: `100` |
| `unitMaxWidth` | String | `"px"` cho form giới hạn chiều rộng, `"%"` cho Row chiếm toàn bộ chiều ngang |
| `horizontalAlignment` | String | Căn Row trong vùng nội dung; `"center"` cho Row ngoài cùng của layout Tạo |
| `slug` | String | `layout_row_<meaningful_name>`; chỉ thêm `_<index>` khi trùng |
| `name` | String | Thường để trống |
| `isShowChildren` | Boolean | Mặc định `true` |
| `isBorder` | Boolean | Mặc định `false` |
| `paddingLeft/Right/Top/Bottom` | Number | px. Mặc định `0` |
| `children` | Array | Mảng `layoutColumn` |

## layoutColumn

```json
{
  "id": "<uuid>",
  "type": "layoutColumn",
  "colSpan": 1,
  "name": "",
  "slug": "layout_column_main_information",
  "isShowName": false,
  "isShowChildren": true,
  "isBorder": false,
  "paddingLeft": 0,
  "paddingRight": 0,
  "paddingTop": 0,
  "paddingBottom": 0,
  "gap": 20,
  "children": [ /* mảng section */ ]
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | String | UUID v4 |
| `type` | String | Luôn `"layoutColumn"` |
| `colSpan` | Number | Tỷ lệ chiều rộng = `colSpan` / tổng `colSpan` trong Row: `1` và `3` → 25%/75%; `1` và `1` → 50%/50%; `1`,`1`,`1` → 33,3% mỗi cột |
| `name` | String | Thường để trống |
| `slug` | String | `layout_column_<meaningful_name>`; chỉ thêm `_<index>` khi trùng |
| `isShowName` | Boolean | Mặc định `false` |
| `isShowChildren` | Boolean | Mặc định `true` |
| `isBorder` | Boolean | Mặc định `false` |
| `paddingLeft/Right/Top/Bottom` | Number | px. Mặc định `0` |
| `gap` | Number | Khoảng cách giữa các section (px). Mặc định `20` |
| `children` | Array | Mảng `section` |

## section

```json
{
  "id": "<uuid>",
  "type": "section",
  "typeSection": "normal",
  "numberOfTabs": 1,
  "name": "Section 1",
  "slug": "section_system_information",
  "isShowName": false,
  "isShowChildren": true,
  "isBorder": true,
  "paddingLeft": 20,
  "paddingRight": 20,
  "paddingTop": 24,
  "paddingBottom": 24,
  "gap": 20,
  "displayUnderline": false,
  "children": [ /* mảng tab */ ]
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | String | UUID v4 |
| `type` | String | Luôn `"section"` |
| `typeSection` | String | `"normal"` + `numberOfTabs: 1`: section thường, chứa 1 tab ẩn; `"menu"` + `numberOfTabs ≥ 2`: section có hệ thống tab, mỗi tab là một trang riêng |
| `numberOfTabs` | Number | `1` không có tab; `≥2` có tab |
| `name` | String | Tên section |
| `slug` | String | `section_<meaningful_name>`; chỉ thêm `_<index>` khi trùng |
| `isShowName` | Boolean | Mặc định `false` |
| `isShowChildren` | Boolean | Mặc định `true` |
| `isBorder` | Boolean | Mặc định `true` |
| `paddingLeft/Right` | Number | Mặc định `20` |
| `paddingTop/Bottom` | Number | Mặc định `24` |
| `gap` | Number | Khoảng cách giữa các group (px). Mặc định `20` |
| `displayUnderline` | Boolean | Gạch dưới tab. Mặc định `false` |
| `children` | Array | Mảng `tab` |

## tab

Tab không có `type`.

```json
{
  "id": "<uuid>",
  "name": "Tab 1",
  "slug": "tab_activities",
  "isShowChildren": true,
  "children": [ /* mảng group */ ]
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | String | UUID v4 |
| `name` | String | Tên tab; section `numberOfTabs: 1` thường để trống hoặc `"Tab 1"` |
| `slug` | String | `tab_<meaningful_name>`; chỉ thêm `_<index>` khi trùng |
| `isShowChildren` | Boolean | Mặc định `true` |
| `children` | Array | Mảng `group` |

## group

```json
{
  "id": "<uuid>",
  "type": "group",
  "name": "Group 1",
  "numberOfColumns": 2,
  "canCollapse": false,
  "slug": "group_system_fields",
  "isShowName": false,
  "isShowChildren": true,
  "isBorder": false,
  "paddingLeft": 0,
  "paddingRight": 0,
  "paddingTop": 0,
  "paddingBottom": 0,
  "gap": 12,
  "tabKey": 1,
  "components": [ /* mảng field/component */ ]
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | String | UUID v4 |
| `type` | String | `"group"` (mặc định), `"accountGroup"`, `"departmentPositionGroup"` |
| `name` | String | Tên nhóm |
| `numberOfColumns` | Number | `1`, `2` hoặc `3` cột; field xếp trái sang phải rồi xuống dòng |
| `canCollapse` | Boolean | Cho phép thu gọn. Mặc định `false` |
| `slug` | String | `group_<meaningful_name>`; chỉ thêm `_<index>` khi trùng |
| `isShowName` | Boolean | Mặc định `false` |
| `isShowChildren` | Boolean | Mặc định `true` |
| `isBorder` | Boolean | Mặc định `false` |
| `paddingLeft/Right/Top/Bottom` | Number | Mặc định `0` |
| `gap` | Number | Khoảng cách giữa các field (px). Mặc định `12` |
| `tabKey` | Number | Index tab chứa group (bắt đầu từ `0` hoặc `1` tùy context) |
| `components` | Array | Mảng field/component; dùng `components`, không dùng `children` |

## component

### Trường chung

```json
{
  "id": "OF...",
  "name": "Tên field",
  "status": 1,
  "slug": "field_slug",
  "fieldType": "short_text",
  "required": 0,
  "disabled": 0,
  "readOnly": 0,
  "manualModifyAllow": true,
  "showLabel": true,
  "showIcon": true,
  "isLinkRedirect": true,
  "labelPlacement": "top",
  "labelAlign": "left",
  "customName": "",
  "enabledAISearch": false,
  "fieldVariableSlug": "",
  "isAllowVariable": false,
  "label": "Nhãn hiển thị",
  "uiSlug": "field_slug_1",
  "fieldMetaData": "{...}"
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | String | Object Field ID (`OF...`) lấy từ Object definition; component đặc biệt dùng UUID v4 |
| `name` | String | Tên field gốc |
| `status` | Number | `1` = active |
| `slug` | String | Slug field gốc |
| `fieldType` | String | Loại field theo `$object-info` |
| `required` | Number | `0`/`1`. Không khả dụng cho `formula`, `auto_number` |
| `disabled` | Number | `1` = hiển thị nhưng không tương tác được |
| `readOnly` | Number | `1` = chỉ đọc |
| `manualModifyAllow` | Boolean | Cho phép sửa thủ công |
| `showLabel` | Boolean | Mặc định `true` |
| `showIcon` | Boolean | Mặc định `true` |
| `isLinkRedirect` | Boolean | Nhấn để chuyển trang. Mặc định `true` |
| `labelPlacement` | String | `"top"`, `"left"`, `"right"`, `"bottom"` |
| `labelAlign` | String | `"left"`, `"right"`, `"center"` |
| `customName` | String | Tên hiển thị ghi đè tên gốc |
| `enabledAISearch` | Boolean | Chỉ cho `short_text`, `phone`, `email`, `url`. Mặc định `false` |
| `fieldVariableSlug` | String | Slug biến khi field lấy giá trị từ biến |
| `isAllowVariable` | Boolean | Cho phép thay thế biến trong giá trị. Mặc định `false` |
| `label` | String | Nhãn hiển thị, có thể khác `name` |
| `uiSlug` | String | `{slug}_{số thứ tự}`, ví dụ `name_1` |
| `fieldMetaData` | String | Chuỗi JSON stringify từ `metaData` của field; bắt buộc với Object Field |
| `useLayouts` | Array | Chỉ cho component đặc biệt (report, dashboard, tracking_history, path_component): `[2]` = chỉ view/edit, `[3, 2]` = tạo + view/edit. Field thường không cần |

### Object Field: id và fieldMetaData

Object Field đặt lên layout bắt buộc có `id` thật (`OF...`, từ `POST /bapi/v1/objects/list` với `includeFields: true`) và `fieldMetaData` (stringify `metaData` của field). Thiếu một trong hai, layout vẫn tạo được nhưng trong layout editor không thể sửa, di chuyển hoặc xoá field đã có; chỉ thêm mới được từ palette. Quy tắc này không áp dụng cho component đặc biệt như `path_component`.

Ví dụ đúng (lookup tới Personnel):

```json
{
  "id": "OF00000000024",
  "slug": "owner",
  "fieldType": "lookup_normal",
  "name": "Owner",
  "label": "Người sở hữu",
  "uiSlug": "owner_1",
  "status": 1,
  "required": 0,
  "manualModifyAllow": true,
  "readOnly": 0,
  "showLabel": true,
  "labelPlacement": "top",
  "labelAlign": "left",
  "showIcon": true,
  "isLinkRedirect": true,
  "fieldMetaData": "{\"link_field\":\"id\",\"object_slug\":\"personnel\",\"object\":\"OT00000000021\"}",
  "typeView": "field",
  "showFieldName": "{$record.first_name} {$record.last_name}",
  "isAddRecord": true,
  "isHoverShowRecord": true,
  "multiple": 0
}
```
