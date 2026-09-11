## Send HTTP Request Task (Task Gửi HTTP Request)

Task hệ thống gửi HTTP request tới một URL khi luồng chạy đến; method `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD` với headers và body tuỳ chỉnh. Formula làm body: [references/formula-resource.md](../references/formula-resource.md); Text Template: [references/text-template-resource.md](../references/text-template-resource.md). Mẫu: `samples/sample_send_http_request.json`, `samples/sample_formula.json`.

### BPMN XML

```xml
<elEx:httpTask id="{HTTP_TASK_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="SEND_HTTP_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:httpTask>
```

Element `elEx:httpTask` (không phải `bpmn2:userTask`/`bpmn2:sendTask`); khai báo `xmlns:elEx="http://element-ex/schema"` trong `bpmn2:definitions` ([namespace](../references/bpmn-xml-and-diagram.md#namespace-và-kết-nối-logic)).

### `actions` trong JSON

```json
{
  "actions": [
    {
      "id": "{ACTION_ID}",
      "nodeId": "{HTTP_TASK_NODE_ID}",
      "type": "SEND_HTTP_REQUEST",
      "name": "{TASK_NAME}",
      "slug": "{task_slug}",
      "description": "",
      "processId": "{PROCESS_ID}",
      "data": {
        "url": { "type": 1, "value": "https://example.com/api" },
        "method": "POST",
        "headers": {
          "header-1": { "type": 1, "value": "value-1", "isHidden": false, "order": 0 }
        },
        "contentType": "application/json",
        "requestBodyType": 1,
        "requestBody": { "type": 1, "value": "{\n    \"key\": \"value\"\n}" },
        "timeout": 10,
        "retry": 1,
        "waitUntilReceivedResponse": true,
        "parseResponseToJson": true,
        "continueRunningEventRequestNotSuccessful": true,
        "sampleResponse": "",
        "parseToDataType": { "nameDataType": "output", "children": [] }
      }
    }
  ]
}
```

### Hệ thống type cho giá trị

| Type | Mô tả | Áp dụng cho |
|------|-------|-------------|
| `1` | Nhập trực tiếp (raw), text thuần không chứa biến | url, headers value, requestBody |
| `2` | Giá trị từ Text Template | requestBody |
| `4` | Giá trị từ biến hoặc resource | url, headers value, requestBody |
| `5` | Nhập trực tiếp có chứa biến bên trong (Simple Renderer) | url, requestBody |

Type `5` (Simple Renderer) chỉ render biến, KHÔNG hỗ trợ if/else, for như Text Template; cú pháp `$userTask.Root.submittedBy.first_last_name`, KHÔNG bọc `{{}}` hay `{}`.

**Ràng buộc kiểu dữ liệu:** `requestBody` type 3/4/5 chỉ chấp nhận biến/resource có `dataType` **`TEXT`**; KHÔNG hỗ trợ trực tiếp biến `RECORD` (ví dụ `$flow.input.newRecord`, `$action.get_record.output.record`). Cần gửi RECORD làm body thì BẮT BUỘC tạo Formula (`type: 3`) chuyển sang TEXT rồi tham chiếu Formula trong `requestBody`; `url` và headers value type 4 cũng chỉ nhận `TEXT`:

```javascript
return Json.stringify($flow.input.newRecord);
```

```json
{
  "requestBody": {
    "type": 4,
    "value": "$flow.formula_body",
    "valueDataType": "TEXT",
    "valuePathName": "workflow_resource:list.formula / Body request"
  }
}
```

### Chi tiết các trường trong `data`

#### 1. `url`

- Type 1: `{"type": 1, "value": "https://example.com/api/endpoint"}`.
- Type 5: `{"type": 5, "value": "https://example.com/api/$userTask.Root.submittedBy.id"}`.
- Type 4: `{"type": 4, "value": "$flow.url_variable", "valueDataType": "TEXT", "valuePathName": "workflow_resource:list.variable / URL variable"}`.

#### 2. `method`

`"GET"`, `"POST"`, `"PUT"`, `"PATCH"`, `"DELETE"`, `"HEAD"`. `GET`/`HEAD` thường không gửi body: chỉ thêm `requestBodyType`/`requestBody` khi endpoint thực sự yêu cầu và backend đích hỗ trợ.

#### 3. `headers`

Object, mỗi key là tên header, value mô tả giá trị với `isHidden` (ẩn giá trị nhạy cảm) và `order` (thứ tự hiển thị, từ 0). Header rỗng mặc định: `"headers": {"": {"type": 1, "value": "", "isHidden": false, "order": 0}}`.

```json
{
  "headers": {
    "Authorization": { "type": 1, "value": "Bearer token123", "isHidden": false, "order": 0 },
    "key_1": {
      "type": 4,
      "value": "$flow.bien_string",
      "valueDataType": "TEXT",
      "valuePathName": "workflow_resource:list.variable / Biến string",
      "order": 1,
      "isHidden": false
    }
  }
}
```

#### 4. `contentType`

Giá trị phổ biến: `"application/json"`, `"text/plain"`, `"html"`, `"xml-application"`, `"xml-text"`.

#### 5. `requestBodyType` và `requestBody`

| `requestBodyType` | Body | Dạng `requestBody` |
|---|---|---|
| `1` | Raw (JSON, text, XML...) | object TypeValuePair |
| `2` | `application/x-www-form-urlencoded` | mảng key-value |
| `3` | `multipart/form-data` | mảng key-value, thêm kiểu `FILE` |

Không cần body (ví dụ GET): có thể không truyền cả `requestBodyType` lẫn `requestBody`.

`requestBodyType: 1`, `requestBody` là object:

- Type 1: `{"type": 1, "value": "{\n    \"name\": \"John\",\n    \"email\": \"john@example.com\"\n}"}`.
- Type 2: `{"type": 2, "value": "$flow.text_template", "valueDataType": "TEXT", "valuePathName": "workflow_resource:list.textTemplate / Text template"}`.
- Type 5: `{"type": 5, "value": "{\n    \"a\": \"$userTask.Root.submittedBy.first_last_name\"\n}", "valuePathName": "", "valueDataType": ""}` (`valuePathName`/`valueDataType` có thể để rỗng).
- Type 4: `{"type": 4, "value": "$flow.body_variable", "valueDataType": "TEXT", "valuePathName": "workflow_resource:list.variable / Body variable"}`.

`requestBodyType: 2` hoặc `3`, `requestBody` là mảng (JSONArray); mỗi phần tử nhận giá trị trực tiếp hoặc từ biến. Data type cho phép: `NUMBER`, `TEXT`, `DATE`, `DATE_TIME`, `BOOLEAN`, `URL`; type 3 thêm `FILE` (`"valueDataType": "FILE"`, ví dụ `"value": "$flow.file_variable"`):

```json
{
  "requestBodyType": 2,
  "requestBody": [
    { "key": "field_name", "type": 1, "value": "field_value", "order": 0 },
    {
      "key": "field_from_var",
      "type": 4,
      "value": "$flow.some_variable",
      "valueDataType": "TEXT",
      "valuePathName": "workflow_resource:list.variable / Some variable",
      "order": 1
    }
  ]
}
```

#### 6. Thuộc tính khác

- `timeout`: thời gian chờ (giây), 10–120, mặc định 10.
- `retry`: số lần thử lại khi thất bại, 0–5, mặc định 1.
- `waitUntilReceivedResponse`: chờ nhận response trước khi tiếp tục.
- `parseResponseToJson`: parse response thành JSON, kiểu string `"true"`/`"false"` (template FE cũng gặp boolean `true`).
- `continueRunningEventRequestNotSuccessful`: tiếp tục chạy khi request thất bại.
- `sampleResponse`: JSON response mẫu (string) để parse schema cho `parseToDataType.children`.
- `parseToDataType`: cấu trúc dữ liệu parse từ response mẫu, tạo resource tham chiếu được ở node khác.

#### 7. Parse response thành dữ liệu có cấu trúc

Để dùng dữ liệu response ở node khác (hiển thị trên User Task, input cho node sau): đặt `parseResponseToJson: "true"`, cung cấp `sampleResponse`, định nghĩa `parseToDataType.children` mô tả từng trường. Ví dụ `sampleResponse` cho đủ các kiểu:

```json
{
  "sampleResponse": "{\n\t\"text_1\": \"text 1\",\n\t\"number_1\": 1,\n\t\"array_1\": [\n\t\t{\n\t\t\t\"key_1\": 1\n\t\t}\n\t],\n\t\"dateString\": \"2026-02-03\",\n\t\"dateTimeString\": \"2026-02-03 21:02:01\",\n\t\"dateTimeLongMs\": 1773122429000,\n\t\"dateTimeLongSecond\": 1773122429,\n\t\"url\": \"https://www.epochconverter.com/\",\n\t\"urlAsFile\": \"https://www.epochconverter.com/file.png\"\n}"
}
```

Mỗi trường trong response mẫu là một phần tử `children` (ví dụ TEXT; kiểu khác chỉ đổi các key trong bảng dưới):

```json
{
  "parseToDataType": {
    "nameDataType": "output",
    "children": [
      {
        "absoluteSlug": "$action.{ACTION_SLUG}.output.body.text_1",
        "dataType": "TEXT",
        "displayOrder": 1,
        "type": 1,
        "isList": false,
        "isSystem": false,
        "actionType": "SEND_HTTP_REQUEST",
        "isStandard": true,
        "name": "text_1",
        "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / Body / text_1",
        "metaDataType": {
          "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
          "richText": "false"
        },
        "parentTable": "action",
        "slug": "text_1"
      }
    ]
  }
}
```

| `dataType` | Key riêng | `metaDataType` |
|---|---|---|
| `TEXT` | — | `{"characterLimit": {"min": 0, "max": 131072, "warning": "warning limit note"}, "richText": "false"}` |
| `NUMBER` | — | `{"valueLimit": {"min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note"}, "displayType": 2, "multipleLimit": {"min": 1, "max": 30, "warning": "warning limit note"}, "format": {"format": 2, "type": 1}, "integralLength": 10, "roundRule": "1", "fractionalLength": 6}` |
| `RECORD` (mảng/object lồng nhau) | `"isList": true` khi là mảng; `"nameDataType"` = tên trường gốc (`"array_1"`); `"children": [...]` mô tả phần tử con, absoluteSlug dùng `[0]`: `$action.{ACTION_SLUG}.output.body.array_1[0].key_1`, absolutePath `... / Output / Body / array_1[0] / key_1` | như `TEXT` |
| `DATE` | `"transformationType": "string_to_date"`, `"dateFormat": "yyyy-MM-dd"` (format của chuỗi nguồn) | `{"defaultValueCurrent": false, "multipleLimit": {"min": 0, "max": 30, "warning": "warning limit note"}, "format": {"format": "dd/MM/yyyy"}}` |
| `DATE_TIME` | `"transformationType"`: `"string_to_datetime"` với `"dateFormat": "yyyy-MM-dd HH:mm:ss"`; `"long_ms_to_datetime"` (epoch milliseconds) hoặc `"long_s_to_datetime"` (epoch seconds) với `"dateFormat": ""` | `{"defaultValueCurrent": false, "format": {"date": "dd/MM/yyyy", "time": "hh:mm:ss"}, "timeZone": "Asia/Saigon"}` |
| `URL` | — | `{"multipleLimit": {"min": 0, "max": 30, "warning": "warning limit note"}, "characterLimit": {"min": 0, "max": 2048, "warning": "warning limit note"}, "useDisplayText": false}` |
| `FILE` (URL chuyển thành file) | `"transformationType": "url_to_file"` | `{"multipleLimit": {"min": 0, "max": 30, "warning": "warning limit note"}, "fileGroupType": "file-media", "isPublic": false, "maxSize": 52428800, "isResizable": false, "fileType": ["doc","docx","xlsx","xls","csv","ppt","pptx","pdf","txt","rtf","html","htm","zip","jpg","jpeg","png","svg","gif","bmp","tiff","tif","mp4","avi","mov","wmv","mkv","mp3"]}` |

Tham chiếu ở node khác bằng `$action.{ACTION_SLUG}.output.body.{FIELD_SLUG}` (kiểu theo `dataType` đã khai báo; phần tử mảng `$action.send_http.output.body.array_1[0].key_1`). Làm `defaultValue` trong component User Task:

```json
{
  "defaultValue": "$action.send_http.output.body.text_1",
  "defaultValueDataType": "TEXT",
  "defaultValuePathName": "workflow_resource:list.sendHttp: / send http / Output / Body  / text_1"
}
```

### Resources của action (`resources.actions[]`)

Luôn có `startAt`, `endAt` (DATE_TIME) và `output` (RECORD); `output.body.children` chứa nội dung **giống hệt** `parseToDataType.children` trong `data` của action; `output.body.absolutePath` theo format `workflow_resource:list.sendHttp / {ACTION_NAME} / Output / {ACTION_SLUG}__output`.

```json
{
  "id": "{ACTION_ID}",
  "type": "SEND_HTTP_REQUEST",
  "name": "{ACTION_NAME}",
  "slug": "{ACTION_SLUG}",
  "processId": "{PROCESS_ID}",
  "resources": [
    {
      "absoluteSlug": "$action.{ACTION_SLUG}.startAt",
      "parentMetadata": "",
      "editable": false,
      "dataType": "DATE_TIME",
      "type": 1,
      "isList": false,
      "parentId": "{ACTION_ID}",
      "assignable": false,
      "availableForInput": true,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "name": "Start At",
      "metaDataType": { "defaultValueCurrent": false, "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" }, "timeZone": "Asia/Saigon" },
      "availableForOutput": true,
      "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / StartAt",
      "id": "{RESOURCE_ID_1}",
      "parentTable": "action",
      "slug": "startAt"
    },
    {
      "absoluteSlug": "$action.{ACTION_SLUG}.endAt",
      "name": "End At",
      "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / End At",
      "id": "{RESOURCE_ID_2}",
      "slug": "endAt",
      "...": "các key còn lại giống startAt"
    },
    {
      "absoluteSlug": "$action.{ACTION_SLUG}.output",
      "parentMetadata": "",
      "editable": false,
      "dataType": "RECORD",
      "type": 1,
      "isList": false,
      "parentId": "{ACTION_ID}",
      "assignable": false,
      "actionType": "SEND_HTTP_REQUEST",
      "availableForInput": true,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "children": [
        {
          "absoluteSlug": "$action.{ACTION_SLUG}.output.statusCode",
          "dataType": "TEXT",
          "displayOrder": 1,
          "type": 1,
          "isList": false,
          "isSystem": false,
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "name": "statusCode",
          "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / statusCode",
          "metaDataType": { "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" }, "richText": "false" },
          "parentTable": "action",
          "slug": "statusCode"
        },
        {
          "absoluteSlug": "$action.{ACTION_SLUG}.output.headers",
          "dataType": "TEXT",
          "displayOrder": 2,
          "name": "headers",
          "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / headers",
          "slug": "headers",
          "...": "các key còn lại giống statusCode"
        },
        {
          "absoluteSlug": "$action.{ACTION_SLUG}.output.body",
          "dataType": "RECORD",
          "displayOrder": 3,
          "type": 1,
          "isList": false,
          "isSystem": false,
          "nameDataType": "output",
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "children": "<<< giống parseToDataType.children >>>",
          "name": "Body",
          "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / {ACTION_SLUG}__output",
          "parentTable": "action",
          "slug": "body"
        }
      ],
      "name": "Output",
      "metaDataType": { "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" }, "richText": "false" },
      "availableForOutput": true,
      "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output",
      "id": "{RESOURCE_ID_3}",
      "parentTable": "action",
      "slug": "output"
    }
  ]
}
```

Resource `output` được dùng ở node khác thì có `resourcesUsedIn`, ví dụ User Task hiển thị dữ liệu: `[{"name": "Show data", "count": 3, "id": "NC00000000014", "parentTable": "node_screen", "slug": "show_data"}]`.
