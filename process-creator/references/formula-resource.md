# Formula / Scripting (Công thức tính)

Formula là custom resource (`type: 3`) chứa mã Cogover Scripting (cú pháp dựa trên Apache JEXL): nhận biến/dữ liệu từ resource khác (userTask fields, system variables, action outputs...), tính toán, xử lý chuỗi/ngày tháng/JSON, trả về một giá trị có kiểu định sẵn (`TEXT`, `NUMBER`, `BOOLEAN`, `DATE`, `DATE_TIME`). Dùng khi Variable hoặc Assignment không đủ: tạo JSON body cho HTTP request, tính công thức nghiệp vụ, ghép chuỗi có điều kiện. Cú pháp và hàm đầy đủ: [Cogover Scripting API Reference](../../object-info/references/cogover-scripting-api-vi.md). Mẫu: `samples/sample_formula.json` (User Task → Send HTTP Request với body là Formula).

## Cú pháp tóm tắt

```javascript
// Biến từ resource
$userTask.Root.text_1                     // trường của User Task "Root"
$userTask.Root.submittedBy.account_email  // trường con của lookup
$flow.instance.name                       // system resource
$action.send_http.output.body             // output của action

// Khai báo biến và return
var data = {
    "name": $userTask.Root.text_1,
    "age": $userTask.Root.number_1,
    "submittedByEmail": $userTask.Root.submittedBy.account_email
};
return Json.stringify(data);

// Hàm hỗ trợ (ví dụ)
Text.concat("Hello", " ", "World"); Text.upper($userTask.Root.text_1)
Math.round(3.7); Math.max(10, 20)
Date.now(); Date.format($userTask.Root.ngay, "dd/MM/yyyy")
Json.stringify(data); Json.parse(jsonString)
if ($userTask.Root.number_1 > 10) { return "Lớn"; } else { return "Nhỏ"; }
for (var item : list) { ... }
```

## Cấu trúc trong `resources.custom`

```json
{
  "absoluteSlug": "$flow.{formula_slug}",
  "parentMetadata": "",
  "defaultValue": "var data = {\n    \"name\": $userTask.Root.text_1,\n    \"age\": $userTask.Root.number_1\n};\nreturn Json.stringify(data);",
  "editable": true,
  "dataType": "TEXT",
  "description": "",
  "type": 3,
  "isList": false,
  "parentId": "{PROCESS_ID}",
  "assignable": false,
  "availableForInput": false,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "{FORMULA_NAME}",
  "metaDataType": {
    "convertNullNumberToZero": true,
    "richText": 1,
    "convertNullStringToEmpty": true
  },
  "availableForOutput": false,
  "absolutePath": "workflow_resource:list.formula / {FORMULA_NAME}",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "resourcesUsedIn": [],
  "slug": "{formula_slug}"
}
```

| Trường | Giá trị | Mô tả |
|---|---|---|
| `type` | `3` | Formula/Scripting |
| `dataType` | `"TEXT"`, `"NUMBER"`, `"BOOLEAN"`, `"DATE"`, `"DATE_TIME"` | Kiểu trả về |
| `absoluteSlug` | `$flow.{slug}` | Đường dẫn tham chiếu |
| `absolutePath` | `workflow_resource:list.formula / {Name}` | Tên hiển thị |
| `defaultValue` | mã Cogover Scripting | Nội dung công thức |
| `metaDataType` | đúng với `dataType` | Không dùng metadata TEXT cho kiểu khác (mục dưới) |
| `assignable` | `false` | Chỉ đọc/tính toán; không ghi bằng Assignment |
| `availableForInput`, `availableForOutput` | `false` | Không nhận input/không trả output cho quy trình cha |
| `parentTable` | `"process"` | |
| `isStandard` | `false` | |
| `id` | prefix `RS` + suffix chữ-số duy nhất | ví dụ `RS00000000094` |

## `metaDataType` theo kiểu trả về

Chỉ `TEXT` dùng `richText`, `convertNullStringToEmpty`, `convertNullNumberToZero`. Kiểu khác dùng metadata canonical của đúng data type, giống một Variable cùng kiểu trên workspace ([variables.md](variables.md#metadatatype-theo-kiểu)):

- `NUMBER`: metadata số (`valueLimit`, `displayType: 2`, `multipleLimit`, `format {format 2, type 1}`, `integralLength: 14`, `roundRule: "1"`); không gửi `richText`.
- `BOOLEAN`: metadata boolean canonical; không gửi metadata text hoặc number.
- `DATE`/`DATE_TIME`: metadata ngày/giờ canonical gồm format/timezone; không gửi `richText`.

Trước POST, đối chiếu `dataType` và `metaDataType`. Lỗi `Config object field metadata for resource is invalid` là lỗi metadata type, không phải lỗi code Formula.

## Dùng Formula trong action

Tham chiếu bằng `$flow.{formula_slug}` với `type: 4` (giá trị lấy từ resource: biến/formula/text template, không phải giá trị cố định). Ví dụ request body của Send HTTP Request:

```json
{
  "requestBody": {
    "valuePathName": "workflow_resource:list.formula / Formula 1",
    "valueDataType": "TEXT",
    "type": 4,
    "value": "$flow.formula_1"
  }
}
```

## `resourcesUsedIn` và `externalResourcesUsedIn`

Formula được dùng trong action: thêm vào `resourcesUsedIn` của Formula:

```json
{
  "resourcesUsedIn": [
    { "actionType": "SEND_HTTP_REQUEST", "name": "Send http", "count": 1, "id": "{ACTION_ID}", "parentTable": "action", "slug": "{action_slug}" }
  ]
}
```

Trường của userTask được dùng trong nội dung Formula (ví dụ `$userTask.Root.text_1`): thêm vào `resourcesUsedIn` của resource trường đó:

```json
{
  "resourcesUsedIn": [
    { "dataType": "TEXT", "name": "Formula 1", "count": 1, "id": "{FORMULA_RESOURCE_ID}", "parentTable": "resource", "slug": "{formula_slug}" }
  ]
}
```

Trường con của lookup dùng trong Formula (ví dụ `$userTask.Root.submittedBy.account_email`): thêm vào mảng `externalResourcesUsedIn` ở root level. `parentId` = ID resource lookup cha (resource `submittedBy`); `parentTable: "resource"` (trường con của resource lookup, không phải screen component; Text Template dùng `"screen_component"`); `absolutePath` theo `workflow_resource:list.userTask / {TaskName} / {LookupFieldName} / {SubFieldName}`.

```json
{
  "externalResourcesUsedIn": [
    {
      "absoluteSlug": "$userTask.Root.submittedBy.account_email",
      "parentMetadata": "",
      "dataType": "TEXT",
      "type": 1,
      "isList": false,
      "parentId": "{LOOKUP_RESOURCE_ID}",
      "isSystem": false,
      "availableForInput": false,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "name": "Account email",
      "availableForOutput": false,
      "absolutePath": "workflow_resource:list.userTask / Root / Submitted By / Account email",
      "parentTable": "resource",
      "slug": "account_email"
    }
  ]
}
```
