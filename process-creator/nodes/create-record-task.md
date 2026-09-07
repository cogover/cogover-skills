## Create Record Task (Task Tạo Bản Ghi)

### Mô tả
Create Record Task là một task hệ thống tự động tạo bản ghi mới cho một đối tượng (object type) trong hệ thống khi luồng chạy đến. Có thể cấu hình đối tượng cần tạo, các trường dữ liệu và giá trị cho mỗi trường (giá trị cố định hoặc lấy từ biến).

### Cấu trúc trong BPMN XML
```xml
<elEx:createRecordTask id="{CREATE_RECORD_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="CREATE_RECORD_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:createRecordTask>
```

**Lưu ý quan trọng:**
- Sử dụng `elEx:createRecordTask` (KHÔNG phải `bpmn2:userTask` hay `bpmn2:sendTask`)
- Cần thêm namespace: `xmlns:elEx="http://element-ex/schema"` vào `bpmn2:definitions`
- `renderKey="CREATE_RECORD_TASK"`

### Cấu trúc `actions` trong JSON
Thêm vào mảng `actions` ở root level:
```json
{
  "actions": [
    {
      "id": "{ACTION_ID}",
      "nodeId": "{CREATE_RECORD_NODE_ID}",
      "type": "CREATE_RECORD",
      "name": "{TASK_NAME}",
      "slug": "{task_slug}",
      "description": "",
      "processId": "{PROCESS_ID}",
      "data": {
        "valueSettingType": "MANUAL",
        "objectTypeId": "{OBJECT_TYPE_ID}",
        "layoutId": "{LAYOUT_ID}",
        "recordData": [
          {
            "field_slug_1": { ... },
            "field_slug_2": { ... }
          }
        ],
        "createOne": true,
        "handleDuplicate": false,
        "isRawValue": true,
        "isList": false,
        "fieldsForCheckDuplicate": [],
        "duplicateMatchLogicType": "AND",
        "duplicateConditionForMultipleValue": "DUPLICATE_ALL",
        "duplicateOneRecordStrategy": "UPDATE",
        "duplicateManyRecordStrategyFe": "UPDATE",
        "duplicateManyRecordStrategy": "UPDATE_LATEST",
        "onErrorStrategy": "SKIP_ERROR",
        "actionType": "CREATE_RECORD"
      }
    }
  ]
}
```

### Chi tiết các trường cấu hình Create Record

#### 1. Object Type (Đối tượng)
```json
{
  "objectTypeId": "OT00000000011",
  "layoutId": "LO00000000002"
}
```
- `objectTypeId` = ID của loại đối tượng cần tạo bản ghi. **BẮT BUỘC** sử dụng skill `/object-info` để lấy objectTypeId chính xác từ API (xem mục 25 trong Lưu ý quan trọng). **KHÔNG** sử dụng ID từ ví dụ trong tài liệu này.
- `layoutId` = ID của layout hiển thị của đối tượng

#### 2. Record Data (Dữ liệu bản ghi)
`recordData` là mảng chứa **một bản ghi** với các trường dữ liệu cần tạo. Key là slug của trường, value là cấu hình giá trị. **BẮT BUỘC** sử dụng skill `/object-info` để lấy đúng field slug và fieldType của đối tượng — **KHÔNG** đoán slug dựa trên tên trường hoặc sao chép từ ví dụ (xem mục 25 trong Lưu ý quan trọng).

##### Giá trị cố định (type: 1)
Nhập giá trị trực tiếp:
```json
{
  "field_slug": {
    "type": 1,
    "value": "Giá trị cố định",
    "isList": false,
    "fieldType": "short_text",
    "fieldTypeDisplayAsInteger": null,
    "cleanable": false
  }
}
```

**Các trường BẮT BUỘC cho mọi type (1 và 4):**
- `fieldType` — Loại trường của field đích (ví dụ: `"short_text"`, `"numeric"`, `"currency"`, `"date_time"`, `"boolean"`, `"single_choice"`, `"lookup_normal"`, ...). Lấy từ kết quả skill `/object-info`.
- `fieldTypeDisplayAsInteger` — `true` nếu fieldType là `numeric`, `currency`, `percentage`; `null` cho các loại khác.
- `isList` — `true` nếu trường chứa nhiều giá trị (ví dụ: `phone`, `email`, `url`); `false` cho các trường đơn giá trị.
- `cleanable` — Luôn đặt `false`.

> **⚠️ Thiếu các trường này sẽ gây lỗi `Error parse CreateRecordData` khi validate quy trình.**

##### Giá trị từ biến (type: 4)
Lấy giá trị từ trường trong user task:
```json
{
  "field_slug": {
    "type": 4,
    "isList": false,
    "value": "$userTask.Root.ten",
    "valueDataType": "TEXT",
    "valuePathName": "workflow_resource:list.userTask / Root / Tên",
    "fieldType": "short_text",
    "fieldTypeDisplayAsInteger": null,
    "cleanable": false
  }
}
```
- `value` = đường dẫn biến (ví dụ: `$userTask.Root.ten`)
- `valueDataType` = kiểu dữ liệu nguồn (TEXT, NUMBER, DATE_TIME, RECORD, ...)
- `valuePathName` = tên hiển thị đường dẫn
- `fieldType`, `fieldTypeDisplayAsInteger`, `isList`, `cleanable` = **BẮT BUỘC** (xem bảng mô tả ở trên)

##### Ví dụ các loại giá trị

**Chuỗi (short_text, long_text):**
```json
{
  "company": {
    "type": 1,
    "value": "Công ty A",
    "isList": false,
    "fieldType": "short_text",
    "fieldTypeDisplayAsInteger": null,
    "cleanable": false
  }
}
```

**Số (numeric, currency):**
```json
{
  "annual_revenue": {
    "type": 1,
    "value": 500000000,
    "isList": false,
    "fieldType": "currency",
    "fieldTypeDisplayAsInteger": true,
    "cleanable": false
  },
  "no_of_employees": {
    "type": 1,
    "value": 20,
    "isList": false,
    "fieldType": "numeric",
    "fieldTypeDisplayAsInteger": true,
    "cleanable": false
  }
}
```

**Boolean:**
```json
{
  "do_not_call": {
    "type": 1,
    "value": false,
    "isList": false,
    "fieldType": "boolean",
    "fieldTypeDisplayAsInteger": null,
    "cleanable": false
  }
}
```

**Danh sách lựa chọn (single_choice):**
```json
{
  "status": {
    "type": 1,
    "value": "nurturing",
    "isList": false,
    "fieldType": "single_choice",
    "fieldTypeDisplayAsInteger": null,
    "cleanable": false
  }
}
```

**Lookup (tra cứu):**
```json
{
  "owner": {
    "type": 1,
    "value": "PER_SAMPLE_USER",
    "isList": false,
    "fieldType": "lookup_normal",
    "fieldTypeDisplayAsInteger": null,
    "cleanable": false
  }
}
```

**Số điện thoại (nhiều giá trị):**
```json
{
  "business_phones": {
    "type": 1,
    "value": ["+84986116116"],
    "isList": true,
    "fieldType": "phone",
    "fieldTypeDisplayAsInteger": null,
    "cleanable": false
  }
}
```

**URL (nhiều giá trị):**
```json
{
  "websites": {
    "type": 1,
    "value": [{"url": "https://cogover.com", "alias": ""}],
    "isList": true,
    "fieldType": "url",
    "fieldTypeDisplayAsInteger": null,
    "cleanable": false
  }
}
```

**Email từ biến (nhiều giá trị):**
```json
{
  "emails": {
    "type": 4,
    "isList": true,
    "value": "$userTask.Root.emails",
    "valueDataType": "TEXT",
    "valuePathName": "workflow_resource:list.userTask / Root / Emails",
    "fieldType": "email",
    "fieldTypeDisplayAsInteger": null,
    "cleanable": false
  }
}
```

**Giá trị null:**
```json
{
  "mobile_phones": {
    "type": 1,
    "value": null,
    "isList": false,
    "fieldType": "phone",
    "fieldTypeDisplayAsInteger": null,
    "cleanable": false
  }
}
```

#### 3. Duplicate Handling (Xử lý trùng lặp)
```json
{
  "handleDuplicate": false,
  "fieldsForCheckDuplicate": [],
  "duplicateMatchLogicType": "AND",
  "duplicateConditionForMultipleValue": "DUPLICATE_ALL",
  "duplicateOneRecordStrategy": "UPDATE",
  "duplicateManyRecordStrategyFe": "UPDATE",
  "duplicateManyRecordStrategy": "UPDATE_LATEST"
}
```
- `handleDuplicate` = bật/tắt kiểm tra trùng lặp
- `fieldsForCheckDuplicate` = mảng các trường dùng để kiểm tra trùng
- `duplicateOneRecordStrategy` = chiến lược khi tìm thấy 1 bản ghi trùng (UPDATE, SKIP, ...)
- `duplicateManyRecordStrategy` = chiến lược khi tìm thấy nhiều bản ghi trùng (UPDATE_LATEST, ...)

#### 4. Error Strategy (Chiến lược xử lý lỗi)
```json
{
  "onErrorStrategy": "SKIP_ERROR"
}
```
- `"SKIP_ERROR"` = bỏ qua lỗi và tiếp tục

#### 5. Các thuộc tính khác
```json
{
  "valueSettingType": "MANUAL",
  "createOne": true,
  "isRawValue": true,
  "isList": false,
  "actionType": "CREATE_RECORD"
}
```
- `valueSettingType: "MANUAL"` = cấu hình thủ công
- `createOne: true` = chỉ tạo một bản ghi
- `actionType: "CREATE_RECORD"` = loại action

### Resources của Create Record Action

Create Record action tạo ra các resources có thể sử dụng trong các bước khác:

```json
{
  "resources": {
    "actions": [
      {
        "id": "{ACTION_ID}",
        "type": "CREATE_RECORD",
        "name": "{TASK_NAME}",
        "slug": "{task_slug}",
        "nodeId": "{CREATE_RECORD_NODE_ID}",
        "processId": "{PROCESS_ID}",
        "resources": [
          {
            "absoluteSlug": "$action.{task_slug}.startAt",
            "dataType": "DATE_TIME",
            "name": "Start At",
            "slug": "startAt"
          },
          {
            "absoluteSlug": "$action.{task_slug}.endAt",
            "dataType": "DATE_TIME",
            "name": "End At",
            "slug": "endAt"
          },
          {
            "absoluteSlug": "$action.{task_slug}.output",
            "dataType": "RECORD",
            "name": "Output",
            "slug": "output",
            "actionType": "CREATE_RECORD",
            "children": [
              {
                "absoluteSlug": "$action.{task_slug}.output.record",
                "dataType": "RECORD",
                "name": "Record",
                "slug": "record",
                "metaDataType": {
                  "linkField": "id",
                  "objectSlug": "",
                  "object": "{OBJECT_TYPE_ID}"
                }
              },
              {
                "absoluteSlug": "$action.{task_slug}.output.result",
                "dataType": "NUMBER",
                "name": "Result",
                "slug": "result"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**Chi tiết Output:**
- `output.record` = bản ghi đã tạo (RECORD), liên kết đến object type đã cấu hình
- `output.result` = mã kết quả (NUMBER)

### Cập nhật resourcesUsedIn

Khi một resource của userTask được sử dụng trong recordData của Create Record (type: 4), cần thêm `resourcesUsedIn` vào resource đó trong `resources.userTasks`:

```json
{
  "resourcesUsedIn": [
    {
      "actionType": "CREATE_RECORD",
      "name": "Create Lead",
      "count": 1,
      "id": "{ACTION_ID}",
      "parentTable": "action",
      "slug": "create_lead"
    }
  ]
}
```

Ví dụ: Khi trường `$userTask.Root.ten` được dùng để map vào `first_name` trong recordData, resource `ten` trong `resources.userTasks[].resources[]` cần có `resourcesUsedIn` trỏ đến action Create Record.

### Ví dụ quy trình với Create Record Task

**Mô tả:** Start -> Root -> Create Lead -> End Process

```
Bắt đầu -> Root (User Task) -> Create Lead (Create Record Task) -> Kết thúc
```

**Cấu hình:**
- Object Type: Lead (`objectTypeId: "OT00000000011"`) — *ID chỉ là ví dụ, thực tế lấy từ skill `/object-info` (xem mục 25 trong Lưu ý quan trọng)*
- Các trường (*field slug lấy từ skill `/object-info`*):
  - `first_name` = lấy từ biến `$userTask.Root.ten` (type: 4)
  - `emails` = lấy từ biến `$userTask.Root.emails` (type: 4, isList: true)
  - `company` = giá trị cố định "Công ty A" (type: 1)
  - `annual_revenue` = giá trị cố định 500000000 (type: 1, fieldTypeDisplayAsInteger: true)
  - `status` = giá trị cố định "nurturing" (type: 1, fieldType: single_choice)

---

