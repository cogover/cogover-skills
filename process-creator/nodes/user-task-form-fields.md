## Các loại trường Form trong User Task

Field đặt trong mảng `components` của group (`layoutRow → layoutColumn → section → tab → group → components`). Template `content`/`pageSettings`, nhóm nút và bảng thuộc tính chung (`required`, `multiple`, `unique`, `readOnly`, `disable`, `canSendData`, `uiSlug`): [references/user-task-templates.md](../references/user-task-templates.md). Giá trị mặc định từ Variable/output action (`defaultValue`, `defaultValueDataType`, `defaultValuePathName`, `defaultTextValueType`) và resource của component trong `resources.userTasks[].resources[]`: [references/variables.md](../references/variables.md#variable-làm-giá-trị-mặc-định-cho-component-trong-usertask). `object`/`object_slug`/`objectId` của lookup và bảng chọn bản ghi: bullet "Thông tin Object thật" ở [mục Chuẩn bị của SKILL.md](../SKILL.md#chuẩn-bị). Mẫu: `samples/sample_process_user_task_full.json`.

### Cấu trúc chung của một trường

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "ten_truong",
  "name": "Tên trường",
  "description": "",
  "fieldType": "loai_truong",
  "fieldMetaData": { ... },
  "required": 0,
  "multiple": 0,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_1",
  "disable": null,
  "readOnly": null
}
```

Các mục dưới chỉ nêu `fieldType`, `fieldMetaData` và key riêng của từng loại; key còn lại theo cấu trúc chung (`uiSlug` tăng dần `"_1"`, `"_2"`, ...).

### Ràng buộc Trường bắt buộc, Trường chỉ đọc và Gửi dữ liệu

| Checkbox trên UI | Key trong payload |
|---|---|
| Trường bắt buộc | `required` |
| Trường chỉ đọc | `readOnly` |
| Gửi dữ liệu | `canSendData` |

Field vừa `required: 1` (hoặc `true`) vừa `readOnly: true` (hoặc `1`) **bắt buộc** có `canSendData: true` ngay trên component trong `userTasks[].content` (ví dụ `{"id": "{COMPONENT_UUID}", "slug": "ma_yeu_cau", "required": 1, "readOnly": true, "canSendData": true}`). Trước khi create, update hoặc lưu version mới, duyệt toàn bộ field của mọi User Task và reject payload nếu còn `required && readOnly && canSendData !== true`. `canSendData` quyết định field có được đưa vào payload submit form gửi tới runtime Process hay không; độc lập với `availableForOutput` của component/resource và không cần đồng bộ sang `resources.userTasks[].resources[]`. Không bật **Gửi dữ liệu** thì server có thể không nhận field chỉ đọc trong dữ liệu submit và trả lỗi thiếu dữ liệu bắt buộc.

### Các loại trường

| # | `fieldType` | `fieldMetaData` | Key riêng / ghi chú |
|---|---|---|---|
| 1 | `short_text` | `{"character_limit": {"min": 0, "max": 255}, "multiple_limit": {"min": 0, "max": 30}}` | `"defaultTextValueType": 1` |
| 2 | `long_text` | `{"character_limit": {"min": 0, "max": 131072}, "rich_text": false}` | `"defaultTextValueType": 1` |
| 3 | `url` | `{"character_limit": {"min": 0, "max": 2048}, "multiple_limit": {"min": 0, "max": 30}, "use_display_text": false}` | |
| 4 | `numeric` (số nguyên) | `{"value_limit": {"min": -9999999999, "max": 9999999999}, "multiple_limit": {"min": 0, "max": 30}, "format": {"type": 1, "format": 3}, "precision": -1, "integral_length": 10, "fractional_length": 0, "display_type": 1, "round_rule": 0}` | `"defaultValue": null`; top-level thêm `"min": -9999999999`, `"max": 9999999999`, `"displayType": "integer"`, `"format": "# ##0"`, `"roundRule": null`, `"precision": -1`, `"numberOfIntegerDigits": 10`, `"numberOfDecimalDigits": 0` |
| 5 | `decimal` (số thập phân) | `{"value_limit": {"min": -9999999999.999998, "max": 9999999999.999998}, "multiple_limit": {"min": 0, "max": 30}, "format": {"type": 1, "format": 5}, "precision": 5, "integral_length": 10, "fractional_length": 6, "display_type": 2, "round_rule": 0}` | `"defaultValue": null`; top-level thêm `"min": -9999999999.999998`, `"max": 9999999999.999998`, `"displayType": "decimal"`, `"format": "# ##0.0"`, `"roundRule": null`, `"precision": 5`, `"numberOfIntegerDigits": 10`, `"numberOfDecimalDigits": 6` |
| 6 | `percent` | giống `numeric` | giống `numeric` |
| 7 | `currency` | giống `numeric` nhưng `"integral_length": 14`, thêm `"country_code": "vn"`, `"unit_position": "after"` | giống `numeric` nhưng `"numberOfIntegerDigits": 14`, thêm `"countryCode": ["vn"]`, `"unitPosition": "after"` |
| 8 | `file` | `{"multiple_limit": {"min": 0, "max": 30}, "max_size": 52428800, "file_type": ["doc", "docx", "xlsx", "xls", "csv", "ppt", "pptx", "pdf", "txt", "rtf", "html", "htm", "zip", "jpg", "jpeg", "png", "svg", "gif", "bmp", "tiff", "tif", "webp", "mp4", "avi", "mov", "wmv", "mkv", "qt", "webm", "mp3", "aac", "m4a"], "file_group_type": "file-media", "is_public": false, "is_resizable": true, "signing_position": [], "is_signing_file": false}` | nhiều file: `"multiple": 1` |
| 9 | `date` | `{"value_limit": {"from": null, "to": null}, "default_value_current": false, "format": {"format": "workspace"}, "multiple_limit": {"min": 0, "max": 30}}` | `"defaultValue": null` |
| 10 | `date_time` | `{"value_limit": {"from": null, "to": null}, "default_value_current": false, "format": {"date": "workspace", "time": "workspace"}, "multiple_limit": {"min": 0, "max": 30}}` | `"defaultValue": null` |
| 11 | `email` | `{"character_limit": {"min": 0, "max": 255}, "multiple_limit": {"min": 0, "max": 30}}` | nhiều email: `"multiple": 1` |
| 12 | `label` (nhãn) | `{"character_limit": {"min": 0, "max": 255}, "multiple_limit": {"min": 0, "max": 30}}` | `"multiple": 1` |
| 13 | `phone` | `{"country_code": ["*"], "multiple_limit": {"min": 0, "max": 30}}` | `["*"]` cho phép mọi mã quốc gia; nhiều số: `"multiple": 1` |
| 14 | `boolean` | `{"true_value": "Yes", "false_value": "No"}` | `"defaultValue": "false"` |
| 15 | `lookup_normal` (tra cứu) | `{"multiple_limit": {"min": 0, "max": 30}, "link_field": "id", "object": "{OBJECT_TYPE_ID}", "object_slug": "{object_slug}"}` | `"defaultValue": null`, `"defaultValueRecord"`, `"minLength": 0`, `"maxLength": 30`; xem ghi chú dưới |
| 16 | `select_list` | xem mục riêng | |
| 17 | `regex` (văn bản theo biểu thức) | `{"character_limit": {"min": 0, "max": 255}, "multiple_limit": {"min": 0, "max": 30}, "regex": "^[A-Z]{3}-[0-9]{4}$"}` | field nhập TEXT có validation regex; resource tương ứng `dataType: "TEXT"`. `multiple: 1`: giữ `multiple_limit` hợp lệ và serialize `defaultValue` dạng danh sách như field text nhiều giá trị |
| 18 | `display_text` (văn bản hiển thị) | `{"rich_text": true}` | chỉ hiển thị nội dung, không phải field nhập, không tạo variable/resource User Task; `"displayTextType"`: `"text"`, `"html"` hoặc `"markdown"`; `"defaultValue"` là nội dung (ví dụ `"<p>Vui lòng kiểm tra thông tin trước khi gửi.</p>"`), `"defaultTextValueType": 1`; nội dung tham chiếu resource thì thêm `defaultValueDataType`/`defaultValuePathName` và `defaultTextValueType` phù hợp resource |
| 19 | `select_record_table` (bảng chọn bản ghi) | không dùng | xem mục riêng |

Ghi chú `lookup_normal`:

- `object` (objectTypeId) và `object_slug` (ví dụ `"contact"`, `"personnel"`) của đối tượng đích BẮT BUỘC lấy qua `$object-info` trước khi tạo JSON; `OT00000000007`/`contact` trong mẫu chỉ minh hoạ, giá trị thay đổi theo workspace.
- `defaultValueRecord`: `1` khi field **không có** giá trị mặc định từ biến/resource (người dùng tự chọn); `0` khi `defaultValue` là tham chiếu biến/resource (`$flow.xxx`, `$action.xxx.output.record`, `$userTask.xxx`) — bắt buộc `0` trong trường hợp này.

### `select_list` (danh sách lựa chọn)

Chọn một hoặc nhiều giá trị từ danh sách tuỳ chọn; kiểu dữ liệu `TEXT`, `NUMBER`, `DATE`, `DATE_TIME`.

| `multiple` | `displayType` |
|---|---|
| `0` (chọn một) | `"single_choice"` |
| `1` (chọn nhiều) | `"multi_choices"` (KHÔNG phải `multiple_choice`) |

| `dataType` = `optionConfig.valueDataType` | Kiểu `value` trong option |
|---|---|
| `"TEXT"` | chuỗi `"Lua chon 1"` |
| `"NUMBER"` | số `1`, `2`, `3` |
| `"DATE"` | chuỗi ngày `"2026-02-01"` |
| `"DATE_TIME"` | timestamp hoặc tham chiếu biến |

Component (ngoài key chung):

```json
{
  "slug": "lua_chon_nhieu_chu",
  "name": "Lựa chọn nhiều: chữ",
  "displayType": "multi_choices",
  "fieldType": "select_list",
  "fieldMetaData": { "object": "", "link_field": "id", "object_slug": "", "fractional_length": 0 },
  "multiple": 1,
  "dataType": "TEXT",
  "useVariableOrResource": 0,
  "optionConfig": {
    "options": [
      {
        "sourceType": "RAW",
        "label": "Lua chon 1",
        "labelPathName": "",
        "labelDataType": "",
        "labelIsRaw": true,
        "slug": "lua_chon_1",
        "isDefault": false,
        "value": "Lua chon 1",
        "valuePathName": "",
        "valueIsRaw": true,
        "objectTypeId": "",
        "logic": "",
        "logicType": "AND",
        "conditions": [],
        "sortFields": []
      },
      {
        "sourceType": "RAW",
        "label": "Lua chon 2",
        "labelPathName": "",
        "labelDataType": "",
        "labelIsRaw": true,
        "slug": "lua_chon_2",
        "isDefault": true,
        "value": "Lua chon 2",
        "valuePathName": "",
        "valueIsRaw": true,
        "objectTypeId": "",
        "logic": "",
        "logicType": "AND",
        "conditions": [],
        "sortFields": []
      }
    ],
    "valueDataType": "TEXT"
  }
}
```

- Option giá trị raw: `valueIsRaw: true`, `valuePathName: ""`. `isDefault: true` là lựa chọn chọn sẵn; `multi_choices` có thể có nhiều `isDefault: true`.
- Option tham chiếu biến/resource (`dataType`/`valueDataType` `"DATE_TIME"`, ví dụ `$userTask.{task_slug}.submittedBy.created` hoặc `$userTask.{task_slug}.startAt`): `valueIsRaw: false`, `value` là đường dẫn, thêm `valuePathName` và `valueDataType` trong option; tham chiếu trường con của resource thì thêm `externalResourcesUsedIn` (dưới). Các key khác như option raw:

```json
{
  "sourceType": "RAW",
  "label": "Ngày giờ 1",
  "slug": "ngay_gio_1",
  "isDefault": true,
  "value": "$userTask.{task_slug}.submittedBy.created",
  "valuePathName": "workflow_resource:list.userTask / {Task Name} / Submitted By / Created",
  "valueDataType": "DATE_TIME",
  "valueIsRaw": false
}
```

Resource tương ứng trong `resources.userTasks[].resources[]` khác field thường: `dataType` luôn `"SELECT_LIST"`, kiểu thực tế ở `selectListDataType`, chế độ ở `selectListDisplayType`, `isList: true` nếu `multi_choices` / `false` nếu `single_choice`:

```json
{
  "absoluteSlug": "$userTask.{task_slug}.{field_slug}",
  "parentMetadata": "",
  "defaultValue": "",
  "dataType": "SELECT_LIST",
  "description": "",
  "type": 1,
  "isList": true,
  "selectListDataType": "TEXT",
  "parentId": "{NODE_CONFIG_ID}",
  "availableForInput": false,
  "isStandard": true,
  "processId": "{PROCESS_ID}",
  "optionConfig": {
    "valueObjectTypeId": "",
    "valueDataTypeId": "",
    "name": "",
    "options": [
      { "isDefault": false, "sourceType": "RAW", "displayOrder": 1, "id": "{OPTION_ID_PREFIX_SLO}", "label": "Lua chon 1", "value": "Lua chon 1", "slug": "lua_chon_1", "valueIsRaw": true },
      { "isDefault": true, "sourceType": "RAW", "displayOrder": 2, "id": "{OPTION_ID_PREFIX_SLO}", "label": "Lua chon 2", "value": "Lua chon 2", "slug": "lua_chon_2", "valueIsRaw": true }
    ],
    "valueDataType": "TEXT",
    "slug": ""
  },
  "selectListDisplayType": "multi_choices",
  "name": "Lựa chọn nhiều: chữ",
  "metaDataType": { "link_field": "id", "fractional_length": 0, "object_slug": "", "object": "" },
  "availableForOutput": false,
  "absolutePath": "workflow_resource:list.userTask / {Task Name} / {Field Name}",
  "id": "{SCREEN_ID}",
  "parentTable": "node_screen",
  "defaultTextValueType": 0,
  "slug": "{field_slug}",
  "fieldId": "{COMPONENT_UUID}",
  "isComponent": true
}
```

Option trong component và trong resource: chung `sourceType: "RAW"`, `label`, `value`, `slug`, `isDefault`, `valueIsRaw`; chỉ resource có `displayOrder` (1, 2, 3, ...) và `id` (prefix `SLO`); chỉ component có `labelPathName`/`labelDataType`/`labelIsRaw`, `objectTypeId`/`logic`/`logicType`/`conditions`/`sortFields` và `valuePathName`/`valueDataType` khi tham chiếu.

`externalResourcesUsedIn` ở root level cho option tham chiếu trường con của resource:

```json
{
  "externalResourcesUsedIn": [
    {
      "absoluteSlug": "$userTask.{task_slug}.submittedBy.created",
      "parentMetadata": "",
      "dataType": "DATE_TIME",
      "type": 1,
      "isList": false,
      "parentId": "{SUBMITTED_BY_RESOURCE_ID}",
      "isSystem": false,
      "availableForInput": false,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "name": "Created",
      "availableForOutput": false,
      "absolutePath": "workflow_resource:list.userTask / {Task Name} / Submitted By / Created",
      "parentTable": "resource",
      "slug": "created"
    }
  ]
}
```

### `select_record_table` (bảng chọn bản ghi)

Hiển thị bảng record của một Object Type; `selectionMode`: `"multiple"`, `"single"`, `"display_only"`.

```json
{
  "id": "{COMPONENT_UUID}",
  "status": 1,
  "slug": "chon_khach_hang",
  "name": "Chọn khách hàng",
  "fieldType": "select_record_table",
  "description": "",
  "required": 1,
  "readOnly": 0,
  "disable": 0,
  "isShowName": true,
  "objectId": "{OBJECT_TYPE_ID}",
  "objectSlug": "{OBJECT_TYPE_SLUG}",
  "sourceData": "",
  "searchFields": ["name"],
  "selectionMode": "multiple",
  "minCount": 1,
  "maxCount": 10,
  "defaultValue": "",
  "availableForInput": false,
  "availableForOutput": false,
  "tableSettings": ""
}
```

- Luôn lấy `objectId`, `objectSlug`, search field và table settings từ API/object metadata thật.
- `display_only` không tạo resource (người dùng không chọn record). `single` tạo child resource `selected_row`. `multiple` tạo child resources `selected_rows` (`isList: true`) và `first_selected_row` (`isList: false`). Resource cha `dataType: "RECORD"`, `isList: false`, chứa các child trên.
