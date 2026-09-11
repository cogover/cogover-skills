# Variable (Biến)

Biến cấp process, lưu và truyền dữ liệu giữa các bước: làm giá trị mặc định cho field trong userTask, tham số cho action, điều kiện gateway; đọc/ghi được (ghi bằng Assignment, [nodes/assignment-task.md](../nodes/assignment-task.md)). So sánh với Formula/Text Template: bảng trong `SKILL.md`. Mẫu: `samples/sample_process_variable.json`.

## Kiểu dữ liệu

| Kiểu | `dataType` | Ví dụ `defaultValue` |
|---|---|---|
| Chữ | `TEXT` | `"Giá trị chữ mặc định"` |
| Số | `NUMBER` | `"9"` |
| Boolean | `BOOLEAN` | `"true"` hoặc `"false"` |
| Ngày | `DATE` | `"2026-02-11"` |
| Ngày giờ | `DATE_TIME` | `"1770573600000"` (timestamp milliseconds) |
| Bản ghi | `RECORD` | không có `defaultValue` (giá trị là tham chiếu bản ghi) |

`isList: false` đơn giá trị; `isList: true` nhiều giá trị (mảng). Biến nhiều giá trị giống biến đơn giá trị cùng kiểu, chỉ khác `isList` (TEXT list có `defaultValue: ""`).

## Cấu trúc trong `resources.custom`

```json
{
  "absoluteSlug": "$flow.{variable_slug}",
  "parentMetadata": "",
  "defaultValue": "{GIA_TRI_MAC_DINH hoặc DUONG_DAN_THAM_CHIEU}",
  "editable": true,
  "dataType": "{DATA_TYPE}",
  "description": "",
  "refAbsoluteSlug": "{DUONG_DAN_THAM_CHIEU nếu defaultValue là biến/resource}",
  "refAbsolutePath": "{TEN_HIEN_THI_DUONG_DAN nếu defaultValue là biến/resource}",
  "type": 1,
  "isList": false,
  "parentId": "{PROCESS_ID}",
  "assignable": true,
  "availableForInput": true,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "{TEN_BIEN}",
  "metaDataType": { ... },
  "availableForOutput": true,
  "absolutePath": "workflow_resource:list.variable / {TEN_BIEN}",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "slug": "{variable_slug}"
}
```

| Trường | Giá trị | Mô tả |
|---|---|---|
| `type` | `1` | Variable (Text Template là `4`, Formula là `3`) |
| `absoluteSlug` | `$flow.{slug}` | Đường dẫn tham chiếu |
| `absolutePath` | `workflow_resource:list.variable / {Name}` | Tên hiển thị đường dẫn |
| `defaultValue` | tuỳ kiểu | Giá trị tĩnh (`"9"`) hoặc tham chiếu biến/resource (`"$userTask.Root.so_a"`) |
| `refAbsoluteSlug`, `refAbsolutePath` | chỉ khi tham chiếu | Nguồn của `defaultValue`, xem mục dưới |
| `editable`, `assignable` | `true` | Luôn `true` với Variable |
| `availableForInput` | `true`/`false` | Cho phép nhận giá trị từ quy trình cha (khi bắt đầu quy trình) |
| `availableForOutput` | `true`/`false` | Cho phép quy trình cha truy xuất giá trị |
| `isList` | `true`/`false` | Nhiều/đơn giá trị |
| `parentTable` | `"process"` | |
| `isStandard` | `false` | |
| `id` | prefix `RS` + suffix chữ-số duy nhất | ví dụ `RS00000000069` |

## `metaDataType` theo kiểu

Các trường còn lại giống template trên; chỉ `metaDataType` (và `defaultValue`) khác theo `dataType`.

`TEXT` (đơn hoặc nhiều giá trị):

```json
{
  "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
  "richText": "false"
}
```

`NUMBER`:

```json
{
  "valueLimit": { "min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note" },
  "displayType": 2,
  "multipleLimit": { "min": 1, "max": 30, "warning": "warning limit note" },
  "format": { "format": 2, "type": 1 },
  "integralLength": 14,
  "roundRule": "1"
}
```

`BOOLEAN`:

```json
{ "falseValue": "Không", "trueValue": "Có", "language": "vi-VN" }
```

`DATE`:

```json
{
  "defaultValueCurrent": false,
  "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
  "format": { "format": "dd/MM/yyyy" }
}
```

`DATE_TIME`:

```json
{
  "defaultValueCurrent": false,
  "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
  "timeZone": "Asia/Saigon"
}
```

`RECORD` (không có `defaultValue`):

```json
{ "linkField": "id", "objectSlug": "lead", "object": "OT00000000011" }
```

`metaDataType.object` (objectTypeId) và `metaDataType.objectSlug` của biến RECORD BẮT BUỘC lấy từ `$object-info`; `OT00000000011`/`lead` chỉ minh hoạ.

## Giá trị mặc định từ biến/resource khác

Variable nhận giá trị mặc định từ biến hoặc resource khác (ví dụ trường trong userTask) thì thêm hai trường:

- `refAbsoluteSlug`: đường dẫn nguồn, bằng `defaultValue` (ví dụ `$userTask.Root.so_a`, `$flow.bien_khac`).
- `refAbsolutePath`: tên hiển thị theo format `workflow_resource:list.{loại} / {Tên nguồn} / {Tên trường}`; trường userTask: `workflow_resource:list.userTask / {TaskName} / {FieldName}`; biến khác: `workflow_resource:list.variable / {TênBiến}`.

Ví dụ biến số nhận mặc định từ trường "Số A" của userTask Root (các trường còn lại như template NUMBER):

```json
{
  "absoluteSlug": "$flow.bien_so",
  "defaultValue": "$userTask.Root.so_a",
  "dataType": "NUMBER",
  "refAbsoluteSlug": "$userTask.Root.so_a",
  "refAbsolutePath": "workflow_resource:list.userTask / Root / Số A",
  "availableForInput": false,
  "availableForOutput": false,
  "name": "Biến số",
  "slug": "bien_so"
}
```

Resource của trường nguồn (trong `resources.userTasks[].resources[]`) phải có `resourcesUsedIn` trỏ đến biến:

```json
{
  "resourcesUsedIn": [
    { "dataType": "NUMBER", "name": "Biến số", "count": 1, "id": "{VARIABLE_RESOURCE_ID}", "parentTable": "resource", "slug": "bien_so" }
  ]
}
```

## Variable làm giá trị mặc định cho component trong userTask

Trong component (mảng `content`) thêm:

```json
{
  "defaultValue": "$flow.{variable_slug}",
  "defaultValueDataType": "{DATA_TYPE}",
  "defaultValuePathName": "workflow_resource:list.variable / {TEN_BIEN}"
}
```

- `defaultValueDataType`: kiểu của biến (`TEXT`, `NUMBER`, `BOOLEAN`, `DATE`, `DATE_TIME`, `RECORD`).
- `defaultTextValueType` trong component và trong resource của component: `4` cho trường text (`short_text`, `long_text`) khi giá trị đến từ biến; `0` cho trường không phải text (`numeric`, `boolean`, `date`, `date_time`, `lookup_normal`).
- Trường `lookup_normal`: `defaultValueRecord: 0` khi giá trị mặc định đến từ biến/resource (`$flow.xxx`, `$action.xxx.output.record`); `1` khi không có giá trị mặc định từ biến (người dùng tự chọn). Đặt sai `1` cho lookup có default từ biến → layout lỗi hiển thị.

Ví dụ component `short_text` dùng biến TEXT (component kiểu khác chỉ khác `fieldType`, `defaultValueDataType`, `fieldMetaData` theo [nodes/user-task-form-fields.md](../nodes/user-task-form-fields.md), và thêm `defaultValueRecord: 0` với `lookup_normal`):

```json
{
  "manualModifyAllow": true,
  "defaultValue": "$flow.bien_chu_text_mot_gia_tri",
  "description": "",
  "uiSlug": "_1",
  "required": 0,
  "defaultValueDataType": "TEXT",
  "defaultValuePathName": "workflow_resource:list.variable / Biến chữ (text): một gía trị",
  "availableForInput": false,
  "fieldMetaData": {
    "character_limit": { "min": 0, "max": 255 },
    "multiple_limit": { "min": 0, "max": 30 }
  },
  "options": [],
  "id": "uuid",
  "defaultTextValueType": 4,
  "slug": "van_ban_ngan",
  "multiple": 0,
  "toolTip": "",
  "readOnly": null,
  "label": "",
  "isStandard": 0,
  "hintText": "",
  "disable": null,
  "unique": false,
  "name": "Van ban ngan",
  "availableForOutput": false,
  "fieldType": "short_text",
  "status": 1
}
```

Resource của component đó trong `resources.userTasks[].resources[]` cũng lưu `defaultValue`:

```json
{
  "absoluteSlug": "$userTask.Root.van_ban_ngan",
  "parentMetadata": "",
  "defaultValue": "$flow.bien_chu_text_mot_gia_tri",
  "dataType": "TEXT",
  "description": "",
  "type": 1,
  "isList": false,
  "parentId": "{NODE_CONFIG_ID}",
  "availableForInput": false,
  "isStandard": true,
  "processId": "{PROCESS_ID}",
  "name": "Van ban ngan",
  "metaDataType": { ... },
  "availableForOutput": false,
  "absolutePath": "workflow_resource:list.userTask / Root / Van ban ngan",
  "id": "{SCREEN_ID}",
  "parentTable": "node_screen",
  "defaultTextValueType": 4,
  "slug": "van_ban_ngan",
  "fieldId": "{COMPONENT_UUID}",
  "isComponent": true
}
```

Variable được dùng trong userTask phải có `resourcesUsedIn` với `parentTable: "node_screen"` và `id` = ID cấu hình node (`NC...`) của userTask; dùng trong nhiều userTask thì nhiều entry:

```json
{
  "resourcesUsedIn": [
    { "name": "Root", "count": 1, "id": "NC00000000004", "parentTable": "node_screen", "slug": "Root" }
  ]
}
```
