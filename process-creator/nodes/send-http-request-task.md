## Send HTTP Request Task (Task Gửi HTTP Request)

### Mô tả
Send HTTP Request Task là một task hệ thống tự động gửi HTTP request đến một URL khi luồng chạy đến. Hỗ trợ các method GET, POST, PUT, PATCH, DELETE, HEAD với headers và body tùy chỉnh.

### Cấu trúc trong BPMN XML
```xml
<elEx:httpTask id="{HTTP_TASK_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="SEND_HTTP_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:httpTask>
```

**Lưu ý quan trọng:**
- Sử dụng `elEx:httpTask` (KHÔNG phải `bpmn2:userTask` hay `bpmn2:sendTask`)
- Cần thêm namespace: `xmlns:elEx="http://element-ex/schema"` vào `bpmn2:definitions`
- `renderKey="SEND_HTTP_TASK"`

### Cấu trúc `actions` trong JSON
Thêm vào mảng `actions` ở root level:
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
        "url": {
          "type": 1,
          "value": "https://example.com/api"
        },
        "method": "POST",
        "headers": {
          "header-1": {
            "type": 1,
            "value": "value-1",
            "isHidden": false,
            "order": 0
          }
        },
        "contentType": "application/json",
        "requestBodyType": 1,
        "requestBody": {
          "type": 1,
          "value": "{\n    \"key\": \"value\"\n}"
        },
        "timeout": 10,
        "retry": 1,
        "waitUntilReceivedResponse": true,
        "parseResponseToJson": true,
        "continueRunningEventRequestNotSuccessful": true,
        "sampleResponse": "",
        "parseToDataType": {
          "nameDataType": "output",
          "children": []
        }
      }
    }
  ]
}
```

### Hệ thống Type cho giá trị

Tương tự như Send Email Task, các trường trong HTTP Request sử dụng hệ thống type:

| Type | Mô tả                                                   | Áp dụng cho                          |
|------|---------------------------------------------------------|--------------------------------------|
| `1`  | Nhập trực tiếp (raw) - text thuần, không chứa biến      | url, headers value, requestBody      |
| `2`  | Giá trị từ Text Template                                | requestBody                          |
| `4`  | Giá trị từ biến hoặc resource                           | url, headers value, requestBody      |
| `5`  | Nhập trực tiếp có chứa biến bên trong (Simple Renderer) | url, requestBody                     |

**Lưu ý về type=5 (Simple Renderer):**
- Hệ thống sử dụng Simple Renderer để render text, chỉ hỗ trợ render các biến
- KHÔNG hỗ trợ render if/else, for,... như Text Template
- Cú pháp biến: `$userTask.Root.submittedBy.first_last_name` (KHÔNG bọc xung quanh `{{}}` hay `{}`)

**QUAN TRỌNG — Ràng buộc kiểu dữ liệu cho `requestBody` khi dùng type=3,4,5 (biến/resource):**
- `requestBody` chỉ chấp nhận biến/resource có `dataType` là **`TEXT`**. **KHÔNG** hỗ trợ trực tiếp biến có `dataType` là `RECORD` (ví dụ: `$flow.input.newRecord`, `$action.get_record.output.record`).
- Nếu cần gửi dữ liệu từ biến dạng RECORD làm body, **BẮT BUỘC** phải tạo một **Formula** (type: 3) dùng `Json.stringify()` để chuyển RECORD thành TEXT, rồi tham chiếu Formula đó trong `requestBody`:
  ```javascript
  // Ví dụ Formula chuyển RECORD → TEXT
  return Json.stringify($flow.input.newRecord);
  ```
  ```json
  "requestBody": {
    "type": 4,
    "value": "$flow.formula_body",
    "valueDataType": "TEXT",
    "valuePathName": "workflow_resource:list.formula / Body request"
  }
  ```
- Quy tắc tương tự áp dụng cho `url` và `headers value` khi dùng type=4: chỉ chấp nhận `TEXT`.

### Chi tiết các trường cấu hình HTTP Request

#### 1. URL

**Cách 1: Nhập trực tiếp, không chứa biến (type=1)**
```json
{
  "url": {
    "type": 1,
    "value": "https://example.com/api/endpoint"
  }
}
```

**Cách 2: Nhập trực tiếp có chứa biến bên trong (type=5 - Simple Renderer)**
```json
{
  "url": {
    "type": 5,
    "value": "https://example.com/api/$userTask.Root.submittedBy.id"
  }
}
```
- Sử dụng Simple Renderer, chỉ hỗ trợ render biến (không hỗ trợ if/else, for,... như Text Template)
- Cú pháp biến: `$userTask.Root.submittedBy.id` (KHÔNG bọc `{{}}` hay `{}`)

**Cách 3: Lấy giá trị từ biến hoặc resource (type=4)**
```json
{
  "url": {
    "type": 4,
    "value": "$flow.url_variable",
    "valueDataType": "TEXT",
    "valuePathName": "workflow_resource:list.variable / URL variable"
  }
}
```
- `value` = đường dẫn đến biến/resource: `$flow.{variable_slug}`
- `valueDataType` = `"TEXT"`
- `valuePathName` = tên hiển thị đường dẫn

#### 2. Method
```json
{
  "method": "POST"
}
```
Các giá trị hỗ trợ: `"GET"`, `"POST"`, `"PUT"`, `"PATCH"`, `"DELETE"`, `"HEAD"`.

`GET` và `HEAD` thường không gửi request body. Chỉ thêm `requestBodyType`/`requestBody` khi endpoint thực sự yêu cầu và backend đích hỗ trợ.

#### 3. Headers

Object chứa các header, mỗi key là tên header, value là object mô tả giá trị.

**Cách 1: Header rỗng (mặc định)**
```json
{
  "headers": {
    "": {
      "type": 1,
      "value": "",
      "isHidden": false,
      "order": 0
    }
  }
}
```

**Cách 2: Nhập giá trị trực tiếp (type=1)**
```json
{
  "headers": {
    "Authorization": {
      "type": 1,
      "value": "Bearer token123",
      "isHidden": false,
      "order": 0
    }
  }
}
```

**Cách 3: Lấy giá trị từ biến hoặc resource (type=4)**
```json
{
  "headers": {
    "key_1": {
      "type": 4,
      "value": "$flow.bien_string",
      "valueDataType": "TEXT",
      "valuePathName": "workflow_resource:list.variable / Biến string",
      "order": 0,
      "isHidden": false
    }
  }
}
```
- `valuePathName` = tên hiển thị đường dẫn
- `valueDataType` = `"TEXT"`

**Các thuộc tính chung của header:**
- `isHidden` = ẩn giá trị (cho sensitive data)
- `order` = thứ tự hiển thị (bắt đầu từ 0)

#### 4. Content Type
```json
{
  "contentType": "application/json"
}
```
Các giá trị phổ biến:
- `"application/json"`
- `"text/plain"`
- `"html"`
- `"xml-application"`
- `"xml-text"`

#### 5. Request Body Type

```json
{
  "requestBodyType": 1
}
```

| Giá trị | Mô tả                              |
|---------|-------------------------------------|
| `1`     | Raw body (JSON, text, XML,...)      |
| `2`     | `application/x-www-form-urlencoded` |
| `3`     | `multipart/form-data`               |

**Lưu ý:** Khi không cần gửi body (ví dụ method GET), có thể không truyền `requestBodyType` và `requestBody`.

#### 6. Request Body

Cấu trúc `requestBody` phụ thuộc vào `requestBodyType`:

##### 6.1. Khi `requestBodyType = 1` (Raw body)

`requestBody` là **object** với cấu trúc `TypeValuePair`:

**Cách 1: Nhập trực tiếp, text thuần không chứa biến (type=1)**
```json
{
  "requestBodyType": 1,
  "requestBody": {
    "type": 1,
    "value": "{\n    \"name\": \"John\",\n    \"email\": \"john@example.com\"\n}"
  }
}
```

**Cách 2: Lấy giá trị từ Text Template (type=2)**
```json
{
  "requestBodyType": 1,
  "requestBody": {
    "type": 2,
    "value": "$flow.text_template",
    "valueDataType": "TEXT",
    "valuePathName": "workflow_resource:list.textTemplate / Text template"
  }
}
```
- `requestBody.type: 2` = giá trị từ Text Template
- `requestBody.value` = đường dẫn Text Template: `$flow.{text_template_slug}`
- `requestBody.valuePathName` = tên hiển thị
- `requestBody.valueDataType` = `"TEXT"`

**Cách 3: Nhập trực tiếp có chứa biến bên trong (type=5 - Simple Renderer)**
```json
{
  "requestBodyType": 1,
  "requestBody": {
    "type": 5,
    "value": "{\n    \"a\": \"$userTask.Root.submittedBy.first_last_name\"\n}",
    "valuePathName": "",
    "valueDataType": ""
  }
}
```
- Sử dụng Simple Renderer, chỉ hỗ trợ render biến (KHÔNG hỗ trợ if/else, for,... như Text Template)
- Cú pháp biến: `$userTask.Root.submittedBy.first_last_name` (KHÔNG bọc `{{}}` hay `{}`)
- Khi type=5, `valuePathName` và `valueDataType` có thể để rỗng `""`

**Cách 4: Lấy giá trị từ biến hoặc resource (type=4)**
```json
{
  "requestBodyType": 1,
  "requestBody": {
    "type": 4,
    "value": "$flow.body_variable",
    "valueDataType": "TEXT",
    "valuePathName": "workflow_resource:list.variable / Body variable"
  }
}
```

##### 6.2. Khi `requestBodyType = 2` (application/x-www-form-urlencoded)

`requestBody` là **mảng (JSONArray)** các key-value pair. Mỗi phần tử hỗ trợ giá trị trực tiếp hoặc từ biến:

```json
{
  "requestBodyType": 2,
  "requestBody": [
    {
      "key": "field_name",
      "type": 1,
      "value": "field_value",
      "order": 0
    },
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
- Các data type cho phép: `NUMBER`, `TEXT`, `DATE`, `DATE_TIME`, `BOOLEAN`, `URL`

##### 6.3. Khi `requestBodyType = 3` (multipart/form-data)

`requestBody` là **mảng (JSONArray)**, tương tự type=2 nhưng hỗ trợ thêm kiểu `FILE`:

```json
{
  "requestBodyType": 3,
  "requestBody": [
    {
      "key": "file_field",
      "type": 4,
      "value": "$flow.file_variable",
      "valueDataType": "FILE",
      "valuePathName": "workflow_resource:list.variable / File variable",
      "order": 0
    },
    {
      "key": "text_field",
      "type": 1,
      "value": "some text",
      "order": 1
    }
  ]
}
```
- Các data type cho phép: `NUMBER`, `TEXT`, `DATE`, `DATE_TIME`, `BOOLEAN`, `URL`, `FILE`

#### 7. Các thuộc tính khác
```json
{
  "timeout": 10,
  "retry": 1,
  "waitUntilReceivedResponse": true,
  "parseResponseToJson": "true",
  "continueRunningEventRequestNotSuccessful": true,
  "sampleResponse": "",
  "parseToDataType": {
    "nameDataType": "output",
    "children": []
  }
}
```
- `timeout` = thời gian chờ (giây), giá trị từ 10 đến 120, mặc định 10
- `retry` = số lần thử lại nếu thất bại, giá trị từ 0 đến 5, mặc định 1
- `waitUntilReceivedResponse` = chờ nhận response trước khi tiếp tục
- `parseResponseToJson` = parse response thành JSON (kiểu string: `"true"` hoặc `"false"`)
- `continueRunningEventRequestNotSuccessful` = tiếp tục chạy ngay cả khi request thất bại
- `sampleResponse` = JSON response mẫu (string), dùng để parse schema cho `parseToDataType.children`
- `parseToDataType` = cấu trúc dữ liệu được parse từ response mẫu, tạo thành các resource có thể tham chiếu trong các node khác

#### 8. Parse Response thành dữ liệu có cấu trúc (sampleResponse & parseToDataType)

Khi cần sử dụng dữ liệu từ HTTP response trong các node khác (ví dụ hiển thị trên User Task, dùng làm input cho node tiếp theo), cần:
1. Đặt `parseResponseToJson` = `"true"`
2. Cung cấp `sampleResponse` chứa JSON response mẫu
3. Định nghĩa `parseToDataType.children` mô tả cấu trúc dữ liệu từ response

**Ví dụ response mẫu:**
```json
{
  "sampleResponse": "{\n\t\"text_1\": \"text 1\",\n\t\"number_1\": 1,\n\t\"array_1\": [\n\t\t{\n\t\t\t\"key_1\": 1\n\t\t}\n\t],\n\t\"dateString\": \"2026-02-03\",\n\t\"dateTimeString\": \"2026-02-03 21:02:01\",\n\t\"dateTimeLongMs\": 1773122429000,\n\t\"dateTimeLongSecond\": 1773122429,\n\t\"url\": \"https://www.epochconverter.com/\",\n\t\"urlAsFile\": \"https://www.epochconverter.com/file.png\"\n}"
}
```

**Cấu trúc `parseToDataType.children`** - Mỗi trường trong response mẫu được map thành 1 phần tử:

```json
{
  "parseToDataType": {
    "nameDataType": "output",
    "children": [
      {
        "absoluteSlug": "$action.{ACTION_SLUG}.output.body.{FIELD_SLUG}",
        "dataType": "{DATA_TYPE}",
        "displayOrder": 1,
        "type": 1,
        "isList": false,
        "isSystem": false,
        "actionType": "SEND_HTTP_REQUEST",
        "isStandard": true,
        "name": "{FIELD_NAME}",
        "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / Body / {FIELD_NAME}",
        "metaDataType": { ... },
        "parentTable": "action",
        "slug": "{FIELD_SLUG}"
      }
    ]
  }
}
```

##### Các dataType được hỗ trợ và metaDataType tương ứng

**TEXT** - Cho trường text/string:
```json
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
```

**NUMBER** - Cho trường số:
```json
{
  "absoluteSlug": "$action.{ACTION_SLUG}.output.body.number_1",
  "dataType": "NUMBER",
  "displayOrder": 2,
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "SEND_HTTP_REQUEST",
  "isStandard": true,
  "name": "number_1",
  "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / Body / number_1",
  "metaDataType": {
    "valueLimit": { "min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note" },
    "displayType": 2,
    "multipleLimit": { "min": 1, "max": 30, "warning": "warning limit note" },
    "format": { "format": 2, "type": 1 },
    "integralLength": 10,
    "roundRule": "1",
    "fractionalLength": 6
  },
  "parentTable": "action",
  "slug": "number_1"
}
```

**RECORD (Array/Object)** - Cho trường mảng hoặc object lồng nhau:
```json
{
  "absoluteSlug": "$action.{ACTION_SLUG}.output.body.array_1",
  "dataType": "RECORD",
  "displayOrder": 3,
  "type": 1,
  "isList": true,
  "isSystem": false,
  "nameDataType": "array_1",
  "actionType": "SEND_HTTP_REQUEST",
  "isStandard": true,
  "children": [
    {
      "absoluteSlug": "$action.{ACTION_SLUG}.output.body.array_1[0].key_1",
      "dataType": "NUMBER",
      "displayOrder": 1,
      "type": 1,
      "isList": false,
      "isSystem": false,
      "actionType": "SEND_HTTP_REQUEST",
      "isStandard": true,
      "name": "key_1",
      "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / Body / array_1[0] / key_1",
      "metaDataType": {
        "valueLimit": { "min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note" },
        "displayType": 2,
        "multipleLimit": { "min": 1, "max": 30, "warning": "warning limit note" },
        "format": { "format": 2, "type": 1 },
        "integralLength": 10,
        "roundRule": "1",
        "fractionalLength": 6
      },
      "parentTable": "action",
      "slug": "key_1"
    }
  ],
  "name": "array_1",
  "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / Body / array_1",
  "metaDataType": {
    "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
    "richText": "false"
  },
  "parentTable": "action",
  "slug": "array_1"
}
```
- `isList: true` khi trường là mảng
- `nameDataType` = tên trường gốc trong response
- Phần tử con trong mảng dùng cú pháp `[0]` trong absoluteSlug: `$action.{SLUG}.output.body.array_1[0].key_1`

**DATE** - Cho trường ngày (chuyển đổi từ string):
```json
{
  "absoluteSlug": "$action.{ACTION_SLUG}.output.body.dateString",
  "dateFormat": "yyyy-MM-dd",
  "dataType": "DATE",
  "displayOrder": 4,
  "transformationType": "string_to_date",
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "SEND_HTTP_REQUEST",
  "isStandard": true,
  "name": "dateString",
  "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / Body / dateString",
  "metaDataType": {
    "defaultValueCurrent": false,
    "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
    "format": { "format": "dd/MM/yyyy" }
  },
  "parentTable": "action",
  "slug": "dateString"
}
```
- `transformationType`: `"string_to_date"` - chuyển string thành DATE
- `dateFormat`: format của string nguồn, ví dụ `"yyyy-MM-dd"`

**DATE_TIME** - Cho trường ngày giờ (nhiều kiểu chuyển đổi):

Từ string:
```json
{
  "absoluteSlug": "$action.{ACTION_SLUG}.output.body.dateTimeString",
  "dateFormat": "yyyy-MM-dd HH:mm:ss",
  "dataType": "DATE_TIME",
  "displayOrder": 5,
  "transformationType": "string_to_datetime",
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "SEND_HTTP_REQUEST",
  "isStandard": true,
  "name": "dateTimeString",
  "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / Body / dateTimeString",
  "metaDataType": {
    "defaultValueCurrent": false,
    "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
    "timeZone": "Asia/Saigon"
  },
  "parentTable": "action",
  "slug": "dateTimeString"
}
```

Từ epoch milliseconds:
```json
{
  "absoluteSlug": "$action.{ACTION_SLUG}.output.body.dateTimeLongMs",
  "dateFormat": "",
  "dataType": "DATE_TIME",
  "displayOrder": 6,
  "transformationType": "long_ms_to_datetime",
  "...": "..."
}
```

Từ epoch seconds:
```json
{
  "absoluteSlug": "$action.{ACTION_SLUG}.output.body.dateTimeLongSecond",
  "dateFormat": "",
  "dataType": "DATE_TIME",
  "displayOrder": 7,
  "transformationType": "long_s_to_datetime",
  "...": "..."
}
```

| transformationType | Mô tả | dateFormat |
|---|---|---|
| `string_to_date` | Chuyển string thành DATE | Format của string nguồn, vd: `"yyyy-MM-dd"` |
| `string_to_datetime` | Chuyển string thành DATE_TIME | Format của string nguồn, vd: `"yyyy-MM-dd HH:mm:ss"` |
| `long_ms_to_datetime` | Chuyển epoch milliseconds thành DATE_TIME | `""` (rỗng) |
| `long_s_to_datetime` | Chuyển epoch seconds thành DATE_TIME | `""` (rỗng) |

**URL** - Cho trường URL:
```json
{
  "absoluteSlug": "$action.{ACTION_SLUG}.output.body.url",
  "dataType": "URL",
  "displayOrder": 8,
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "SEND_HTTP_REQUEST",
  "isStandard": true,
  "name": "url",
  "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / Body / url",
  "metaDataType": {
    "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
    "characterLimit": { "min": 0, "max": 2048, "warning": "warning limit note" },
    "useDisplayText": false
  },
  "parentTable": "action",
  "slug": "url"
}
```

**FILE** - Cho trường URL chuyển thành file:
```json
{
  "absoluteSlug": "$action.{ACTION_SLUG}.output.body.urlAsFile",
  "dataType": "FILE",
  "displayOrder": 9,
  "transformationType": "url_to_file",
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "SEND_HTTP_REQUEST",
  "isStandard": true,
  "name": "urlAsFile",
  "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / Body / urlAsFile",
  "metaDataType": {
    "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
    "fileGroupType": "file-media",
    "isPublic": false,
    "maxSize": 52428800,
    "isResizable": false,
    "fileType": ["doc","docx","xlsx","xls","csv","ppt","pptx","pdf","txt","rtf","html","htm","zip","jpg","jpeg","png","svg","gif","bmp","tiff","tif","mp4","avi","mov","wmv","mkv","mp3"]
  },
  "parentTable": "action",
  "slug": "urlAsFile"
}
```
- `transformationType`: `"url_to_file"` - chuyển URL thành FILE

##### Cách tham chiếu resource từ HTTP Response trong các node khác

Sau khi parse, các trường trong response body trở thành resource có thể tham chiếu bằng cú pháp:
```
$action.{ACTION_SLUG}.output.body.{FIELD_SLUG}
```

Ví dụ với action slug là `send_http`:
- `$action.send_http.output.body.text_1` → TEXT
- `$action.send_http.output.body.number_1` → NUMBER
- `$action.send_http.output.body.array_1[0].key_1` → NUMBER (phần tử trong mảng)
- `$action.send_http.output.body.dateString` → DATE
- `$action.send_http.output.body.dateTimeString` → DATE_TIME
- `$action.send_http.output.body.url` → URL

Khi dùng làm defaultValue trong User Task component:
```json
{
  "defaultValue": "$action.send_http.output.body.text_1",
  "defaultValueDataType": "TEXT",
  "defaultValuePathName": "workflow_resource:list.sendHttp: / send http / Output / Body  / text_1"
}
```

### Resources của HTTP Request Action

HTTP Request action tạo ra các resources có thể sử dụng trong các bước khác.

#### Resources mặc định (luôn có):
```json
{
  "resources": {
    "actions": [
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
            "metaDataType": {
              "defaultValueCurrent": false,
              "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
              "timeZone": "Asia/Saigon"
            },
            "availableForOutput": true,
            "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / StartAt",
            "id": "{RESOURCE_ID_1}",
            "parentTable": "action",
            "slug": "startAt"
          },
          {
            "absoluteSlug": "$action.{ACTION_SLUG}.endAt",
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
            "name": "End At",
            "metaDataType": {
              "defaultValueCurrent": false,
              "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
              "timeZone": "Asia/Saigon"
            },
            "availableForOutput": true,
            "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / End At",
            "id": "{RESOURCE_ID_2}",
            "parentTable": "action",
            "slug": "endAt"
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
                "metaDataType": {
                  "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
                  "richText": "false"
                },
                "parentTable": "action",
                "slug": "statusCode"
              },
              {
                "absoluteSlug": "$action.{ACTION_SLUG}.output.headers",
                "dataType": "TEXT",
                "displayOrder": 2,
                "type": 1,
                "isList": false,
                "isSystem": false,
                "actionType": "SEND_HTTP_REQUEST",
                "isStandard": true,
                "name": "headers",
                "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / headers",
                "metaDataType": {
                  "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
                  "richText": "false"
                },
                "parentTable": "action",
                "slug": "headers"
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
                "children": "<<< NỘI DUNG GIỐNG parseToDataType.children >>>",
                "name": "Body",
                "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output / {ACTION_SLUG}__output",
                "parentTable": "action",
                "slug": "body"
              }
            ],
            "name": "Output",
            "metaDataType": {
              "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
              "richText": "false"
            },
            "availableForOutput": true,
            "absolutePath": "workflow_resource:list.sendHttp / {ACTION_NAME} / Output",
            "id": "{RESOURCE_ID_3}",
            "parentTable": "action",
            "slug": "output"
          }
        ]
      }
    ]
  }
}
```

**Lưu ý quan trọng:**
- `output.body.children` chứa nội dung giống hệt `parseToDataType.children` trong `data` của action
- `output.body.absolutePath` dùng format: `workflow_resource:list.sendHttp / {ACTION_NAME} / Output / {ACTION_SLUG}__output`
- `resourcesUsedIn` trên resource `output` cho biết resource này đang được dùng ở node nào:
```json
{
  "resourcesUsedIn": [
    { "name": "Show data", "count": 3, "id": "NC00000000014", "parentTable": "node_screen", "slug": "show_data" }
  ]
}
```

### Ví dụ đầy đủ

#### Ví dụ 1: URL nhập trực tiếp (type=1), requestBody nhập trực tiếp có chứa biến (type=5)

- **url**: nhập trực tiếp không chứa biến (type=1)
- **requestBody**: nhập trực tiếp có chứa biến (type=5 - Simple Renderer)
- **headers**: rỗng

```json
{
  "data": {
    "headers": {
      "": {
        "type": 1,
        "value": "",
        "isHidden": false,
        "order": 0
      }
    },
    "method": "POST",
    "requestBody": {
      "valuePathName": "",
      "valueDataType": "",
      "type": 5,
      "value": "{\n    \"a\": \"$userTask.Root.submittedBy.first_last_name\"\n}"
    },
    "requestBodyType": 1,
    "parseToDataType": {
      "nameDataType": "output",
      "children": []
    },
    "waitUntilReceivedResponse": true,
    "contentType": "application/json",
    "retry": 1,
    "timeout": 10,
    "continueRunningEventRequestNotSuccessful": true,
    "url": {
      "type": 1,
      "value": "https://example.com/api/endpoint"
    },
    "parseResponseToJson": true,
    "sampleResponse": ""
  },
  "processId": "PE00000000002",
  "name": "Send http",
  "description": "",
  "id": "AC00000000023",
  "type": "SEND_HTTP_REQUEST",
  "nodeId": "NO00000000092",
  "slug": "send_http"
}
```

#### Ví dụ 2: URL có chứa biến (type=5), requestBody từ Text Template (type=2), header từ biến (type=4)

- **url**: nhập trực tiếp có chứa biến (type=5 - Simple Renderer)
- **requestBody**: lấy giá trị từ Text Template (type=2)
- **headers**: lấy giá trị từ biến (type=4)

```json
{
  "data": {
    "headers": {
      "key_1": {
        "valuePathName": "workflow_resource:list.variable / Biến string",
        "valueDataType": "TEXT",
        "type": 4,
        "value": "$flow.bien_string",
        "order": 0,
        "isHidden": false
      }
    },
    "method": "POST",
    "requestBodyType": 1,
    "timeout": 10,
    "continueRunningEventRequestNotSuccessful": true,
    "sampleResponse": "",
    "url": {
      "type": 5,
      "value": "https://example.com/api/$userTask.Root.submittedBy.id"
    },
    "parseResponseToJson": true,
    "requestBody": {
      "valuePathName": "workflow_resource:list.textTemplate / Text template",
      "valueDataType": "TEXT",
      "type": 2,
      "value": "$flow.text_template"
    },
    "parseToDataType": {
      "nameDataType": "output",
      "children": []
    },
    "waitUntilReceivedResponse": true,
    "contentType": "application/json",
    "retry": 1
  },
  "processId": "PE00000000002",
  "name": "Send http",
  "description": "",
  "id": "AC00000000008",
  "type": "SEND_HTTP_REQUEST",
  "nodeId": "NO00000000007",
  "slug": "send_http"
}
```

#### Ví dụ 3: Có sampleResponse và parseToDataType (parse response thành dữ liệu có cấu trúc)

- **sampleResponse**: JSON response mẫu
- **parseToDataType**: cấu trúc dữ liệu được parse từ response mẫu
- Các resource được tạo ra có thể tham chiếu trong node khác qua cú pháp `$action.send_http.output.body.{field}`

```json
{
  "data": {
    "headers": {
      "": { "type": 1, "value": "", "isHidden": false, "order": 0 }
    },
    "method": "POST",
    "requestBodyType": 1,
    "timeout": 10,
    "continueRunningEventRequestNotSuccessful": true,
    "sampleResponse": "{\n\t\"text_1\": \"text 1\",\n\t\"number_1\": 1,\n\t\"array_1\": [\n\t\t{\n\t\t\t\"key_1\": 1\n\t\t}\n\t],\n\t\"dateString\": \"2026-02-03\",\n\t\"dateTimeString\": \"2026-02-03 21:02:01\",\n\t\"dateTimeLongMs\": 1773122429000,\n\t\"dateTimeLongSecond\": 1773122429,\n\t\"url\": \"https://www.epochconverter.com/\",\n\t\"urlAsFile\": \"https://www.epochconverter.com/file.png\"\n}",
    "url": { "type": 1, "value": "https://reqbin.com/post-online" },
    "parseResponseToJson": "true",
    "requestBody": { "type": 1, "value": "{\n    \n}" },
    "parseToDataType": {
      "nameDataType": "output",
      "children": [
        {
          "absoluteSlug": "$action.send_http.output.body.text_1",
          "dataType": "TEXT",
          "displayOrder": 1,
          "type": 1,
          "isList": false,
          "isSystem": false,
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "name": "text_1",
          "absolutePath": "workflow_resource:list.sendHttp / send http / Output / Body / text_1",
          "metaDataType": {
            "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
            "richText": "false"
          },
          "parentTable": "action",
          "slug": "text_1"
        },
        {
          "absoluteSlug": "$action.send_http.output.body.number_1",
          "dataType": "NUMBER",
          "displayOrder": 2,
          "type": 1,
          "isList": false,
          "isSystem": false,
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "name": "number_1",
          "absolutePath": "workflow_resource:list.sendHttp / send http / Output / Body / number_1",
          "metaDataType": {
            "valueLimit": { "min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note" },
            "displayType": 2,
            "multipleLimit": { "min": 1, "max": 30, "warning": "warning limit note" },
            "format": { "format": 2, "type": 1 },
            "integralLength": 10,
            "roundRule": "1",
            "fractionalLength": 6
          },
          "parentTable": "action",
          "slug": "number_1"
        },
        {
          "absoluteSlug": "$action.send_http.output.body.array_1",
          "dataType": "RECORD",
          "displayOrder": 3,
          "type": 1,
          "isList": true,
          "isSystem": false,
          "nameDataType": "array_1",
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "children": [
            {
              "absoluteSlug": "$action.send_http.output.body.array_1[0].key_1",
              "dataType": "NUMBER",
              "displayOrder": 1,
              "type": 1,
              "isList": false,
              "isSystem": false,
              "actionType": "SEND_HTTP_REQUEST",
              "isStandard": true,
              "name": "key_1",
              "absolutePath": "workflow_resource:list.sendHttp / send http / Output / Body / array_1[0] / key_1",
              "metaDataType": {
                "valueLimit": { "min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note" },
                "displayType": 2,
                "multipleLimit": { "min": 1, "max": 30, "warning": "warning limit note" },
                "format": { "format": 2, "type": 1 },
                "integralLength": 10,
                "roundRule": "1",
                "fractionalLength": 6
              },
              "parentTable": "action",
              "slug": "key_1"
            }
          ],
          "name": "array_1",
          "absolutePath": "workflow_resource:list.sendHttp / send http / Output / Body / array_1",
          "metaDataType": {
            "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
            "richText": "false"
          },
          "parentTable": "action",
          "slug": "array_1"
        },
        {
          "absoluteSlug": "$action.send_http.output.body.dateString",
          "dateFormat": "yyyy-MM-dd",
          "dataType": "DATE",
          "displayOrder": 4,
          "transformationType": "string_to_date",
          "type": 1,
          "isList": false,
          "isSystem": false,
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "name": "dateString",
          "absolutePath": "workflow_resource:list.sendHttp / send http / Output / Body / dateString",
          "metaDataType": {
            "defaultValueCurrent": false,
            "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
            "format": { "format": "dd/MM/yyyy" }
          },
          "parentTable": "action",
          "slug": "dateString"
        },
        {
          "absoluteSlug": "$action.send_http.output.body.dateTimeString",
          "dateFormat": "yyyy-MM-dd HH:mm:ss",
          "dataType": "DATE_TIME",
          "displayOrder": 5,
          "transformationType": "string_to_datetime",
          "type": 1,
          "isList": false,
          "isSystem": false,
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "name": "dateTimeString",
          "absolutePath": "workflow_resource:list.sendHttp / send http / Output / Body / dateTimeString",
          "metaDataType": {
            "defaultValueCurrent": false,
            "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
            "timeZone": "Asia/Saigon"
          },
          "parentTable": "action",
          "slug": "dateTimeString"
        },
        {
          "absoluteSlug": "$action.send_http.output.body.dateTimeLongMs",
          "dateFormat": "",
          "dataType": "DATE_TIME",
          "displayOrder": 6,
          "transformationType": "long_ms_to_datetime",
          "type": 1,
          "isList": false,
          "isSystem": false,
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "name": "dateTimeLongMs",
          "absolutePath": "workflow_resource:list.sendHttp / send http / Output / Body / dateTimeLongMs",
          "metaDataType": {
            "defaultValueCurrent": false,
            "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
            "timeZone": "Asia/Saigon"
          },
          "parentTable": "action",
          "slug": "dateTimeLongMs"
        },
        {
          "absoluteSlug": "$action.send_http.output.body.dateTimeLongSecond",
          "dateFormat": "",
          "dataType": "DATE_TIME",
          "displayOrder": 7,
          "transformationType": "long_s_to_datetime",
          "type": 1,
          "isList": false,
          "isSystem": false,
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "name": "dateTimeLongSecond",
          "absolutePath": "workflow_resource:list.sendHttp / send http / Output / Body / dateTimeLongSecond",
          "metaDataType": {
            "defaultValueCurrent": false,
            "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
            "timeZone": "Asia/Saigon"
          },
          "parentTable": "action",
          "slug": "dateTimeLongSecond"
        },
        {
          "absoluteSlug": "$action.send_http.output.body.url",
          "dataType": "URL",
          "displayOrder": 8,
          "type": 1,
          "isList": false,
          "isSystem": false,
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "name": "url",
          "absolutePath": "workflow_resource:list.sendHttp / send http / Output / Body / url",
          "metaDataType": {
            "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
            "characterLimit": { "min": 0, "max": 2048, "warning": "warning limit note" },
            "useDisplayText": false
          },
          "parentTable": "action",
          "slug": "url"
        },
        {
          "absoluteSlug": "$action.send_http.output.body.urlAsFile",
          "dataType": "FILE",
          "displayOrder": 9,
          "transformationType": "url_to_file",
          "type": 1,
          "isList": false,
          "isSystem": false,
          "actionType": "SEND_HTTP_REQUEST",
          "isStandard": true,
          "name": "urlAsFile",
          "absolutePath": "workflow_resource:list.sendHttp / send http / Output / Body / urlAsFile",
          "metaDataType": {
            "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
            "fileGroupType": "file-media",
            "isPublic": false,
            "maxSize": 52428800,
            "isResizable": false,
            "fileType": ["doc","docx","xlsx","xls","csv","ppt","pptx","pdf","txt","rtf","html","htm","zip","jpg","jpeg","png","svg","gif","bmp","tiff","tif","mp4","avi","mov","wmv","mkv","mp3"]
          },
          "parentTable": "action",
          "slug": "urlAsFile"
        }
      ]
    },
    "waitUntilReceivedResponse": true,
    "contentType": "application/json",
    "retry": 1
  },
  "processId": "PE00000000016",
  "name": "send http",
  "description": "",
  "id": "AC00000000019",
  "type": "SEND_HTTP_REQUEST",
  "nodeId": "NO00000000055",
  "slug": "send_http"
}
```

---
