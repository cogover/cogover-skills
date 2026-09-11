## Create Record Task (Task Tạo Bản Ghi)

Task hệ thống tạo bản ghi mới cho một Object khi luồng chạy đến; mỗi trường nhận giá trị cố định hoặc lấy từ biến. Mẫu: `samples/sample_process_user_task_create_record.json` (Start → Root → Create Lead → End Process).

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

`elEx:createRecordTask` (KHÔNG phải `bpmn2:userTask` hay `bpmn2:sendTask`), cần `xmlns:elEx="http://element-ex/schema"` trong `bpmn2:definitions`; `renderKey="CREATE_RECORD_TASK"`.

### Cấu trúc `actions` trong JSON

Thêm vào mảng `actions` ở root level:

```json
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
```

| Trường trong `data` | Giá trị |
|---|---|
| `objectTypeId` | ID Object cần tạo bản ghi. BẮT BUỘC lấy qua `$object-info` (xem [Chuẩn bị](../SKILL.md#chuẩn-bị)); KHÔNG dùng ID trong ví dụ của tài liệu này |
| `layoutId` | ID layout hiển thị của Object |
| `recordData` | Mảng chứa MỘT bản ghi; key là slug của trường, value là cấu hình giá trị (mục dưới). Field slug và `fieldType` BẮT BUỘC lấy qua `$object-info`; KHÔNG đoán slug từ tên trường hoặc sao chép từ ví dụ |
| `valueSettingType` | `"MANUAL"`: cấu hình thủ công |
| `createOne` | `true`: chỉ tạo một bản ghi |
| `isRawValue`, `isList` | `true`, `false` |
| `handleDuplicate` | Bật/tắt kiểm tra trùng lặp |
| `fieldsForCheckDuplicate` | Mảng các trường dùng để kiểm tra trùng |
| `duplicateMatchLogicType` | `"AND"` |
| `duplicateConditionForMultipleValue` | `"DUPLICATE_ALL"` |
| `duplicateOneRecordStrategy` | Chiến lược khi tìm thấy 1 bản ghi trùng: `UPDATE`, `SKIP`, ... |
| `duplicateManyRecordStrategyFe` | `"UPDATE"` |
| `duplicateManyRecordStrategy` | Chiến lược khi tìm thấy nhiều bản ghi trùng: `UPDATE_LATEST`, ... |
| `onErrorStrategy` | `"SKIP_ERROR"`: bỏ qua lỗi và tiếp tục |
| `actionType` | `"CREATE_RECORD"` |

### Giá trị từng trường trong `recordData`

Giá trị cố định (`type: 1`):

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

Giá trị từ biến (`type: 4`): `value` là đường dẫn biến, `valueDataType` là kiểu dữ liệu nguồn (`TEXT`, `NUMBER`, `DATE_TIME`, `RECORD`, ...), `valuePathName` là tên hiển thị đường dẫn:

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

Bốn key BẮT BUỘC với cả `type: 1` và `type: 4`; thiếu sẽ gây lỗi `Error parse CreateRecordData` khi validate quy trình:

- `fieldType`: loại trường của field đích (`short_text`, `numeric`, `currency`, `date_time`, `boolean`, `single_choice`, `lookup_normal`, ...), lấy từ kết quả `$object-info`.
- `fieldTypeDisplayAsInteger`: `true` nếu `fieldType` là `numeric`, `currency`, `percentage`; `null` cho các loại khác.
- `isList`: `true` nếu trường chứa nhiều giá trị (`phone`, `email`, `url`); `false` cho trường đơn giá trị.
- `cleanable`: luôn `false`.

Dạng `value` theo `fieldType`:

| `fieldType` | `value` | `fieldTypeDisplayAsInteger` | `isList` |
|---|---|---|---|
| `short_text`, `long_text` | `"Công ty A"` | `null` | `false` |
| `numeric`, `currency` | `20`, `500000000` | `true` | `false` |
| `boolean` | `false` | `null` | `false` |
| `single_choice` | `"nurturing"` (giá trị option) | `null` | `false` |
| `lookup_normal` | `"PER_SAMPLE_USER"` (ID bản ghi) | `null` | `false` |
| `phone` | `["+84986116116"]` | `null` | `true` |
| `url` | `[{"url": "https://cogover.com", "alias": ""}]` | `null` | `true` |
| `email` lấy từ biến | `type: 4`, `value: "$userTask.Root.emails"`, `valueDataType: "TEXT"` | `null` | `true` |
| Giá trị null (ví dụ `phone` đơn giá trị) | `null` | `null` | `false` |

### Resources của Create Record Action

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

- `output.record`: bản ghi đã tạo (RECORD), liên kết đến object type đã cấu hình.
- `output.result`: mã kết quả (NUMBER).

### Cập nhật `resourcesUsedIn`

Resource của userTask được dùng trong `recordData` (`type: 4`) phải có `resourcesUsedIn` trỏ đến action Create Record trong `resources.userTasks[].resources[]` (ví dụ `$userTask.Root.ten` map vào `first_name` → resource `ten`):

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
