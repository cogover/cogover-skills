## Update Record Task (Task Cập Nhật Bản Ghi)

### Mô tả
Update Record Task là một task hệ thống tự động cập nhật bản ghi đã tồn tại của một đối tượng (object type) trong hệ thống khi luồng chạy đến. Khác với Create Record (tạo mới), Update Record cập nhật bản ghi hiện có được chỉ định qua `outputVariable`.

### Cấu trúc trong BPMN XML
```xml
<elEx:createRecordTask id="{UPDATE_RECORD_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="CREATE_RECORD_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:createRecordTask>
```

**Lưu ý quan trọng:**
- Sử dụng cùng element `elEx:createRecordTask` giống Create Record
- `renderKey="CREATE_RECORD_TASK"` (giống Create Record)
- Cần thêm namespace: `xmlns:elEx="http://element-ex/schema"` vào `bpmn2:definitions`
- Sự khác biệt với Create Record nằm trong cấu hình `actions`, không phải trong XML

### Cấu trúc `actions` trong JSON
Thêm vào mảng `actions` ở root level:
```json
{
  "actions": [
    {
      "id": "{ACTION_ID}",
      "nodeId": "{UPDATE_RECORD_NODE_ID}",
      "type": "CREATE_RECORD",
      "name": "{TASK_NAME}",
      "slug": "{task_slug}",
      "description": "",
      "processId": "{PROCESS_ID}",
      "data": {
        "valueSettingType": "MANUAL",
        "actionType": "UPDATE_RECORD",
        "objectTypeId": "{OBJECT_TYPE_ID}",
        "layoutId": "{LAYOUT_ID}",
        "outputVariable": "{RECORD_VARIABLE_PATH}",
        "outputVariableDataType": "RECORD",
        "outputVariablePathName": "{RECORD_VARIABLE_DISPLAY_PATH}",
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
        "onErrorStrategy": "SKIP_ERROR"
      }
    }
  ]
}
```

### Điểm khác biệt so với Create Record

| Thuộc tính                    | Create Record           | Update Record                                                                     |
|-------------------------------|-------------------------|-----------------------------------------------------------------------------------|
| `data.actionType`             | `"CREATE_RECORD"`       | `"UPDATE_RECORD"`                                                                 |
| `data.outputVariable`         | Không có hoặc rỗng      | Đường dẫn đến bản ghi cần cập nhật (ví dụ: `"$userTask.Root.lead"`)               |
| `data.outputVariableDataType` | Không có                | `"RECORD"`                                                                        |
| `data.outputVariablePathName` | Không có                | Tên hiển thị đường dẫn (ví dụ: `"workflow_resource:list.userTask / Root / Lead"`) |
| Action `type` (root level)    | `"CREATE_RECORD"`       | `"CREATE_RECORD"` (giống nhau!)                                                   |
| XML element                   | `elEx:createRecordTask` | `elEx:createRecordTask` (giống nhau!)                                             |

### Chi tiết các trường cấu hình Update Record

#### 1. Output Variable (Bản ghi cần cập nhật)
```json
{
  "outputVariable": "$userTask.Root.lead",
  "outputVariableDataType": "RECORD",
  "outputVariablePathName": "workflow_resource:list.userTask / Root / Lead"
}
```
- `outputVariable` = đường dẫn đến bản ghi cần cập nhật, thường là một trường lookup trong userTask trước đó
- `outputVariableDataType` = luôn là `"RECORD"`
- `outputVariablePathName` = tên hiển thị đường dẫn theo format `workflow_resource:list.userTask / {TaskName} / {FieldName}`

**Ví dụ các nguồn bản ghi:**
- Từ trường lookup trong userTask: `$userTask.Root.lead` (trường lead ở task Root)
- Từ output của Get Record: `$action.get_leads.output.record`
- Từ output của Create Record trước đó: `$action.create_lead.output.record`

#### 2. Object Type (Đối tượng)
```json
{
  "objectTypeId": "OT00000000011",
  "layoutId": "LO00000000001"
}
```
- `objectTypeId` = ID của loại đối tượng cần cập nhật (phải khớp với object type của bản ghi được tham chiếu trong `outputVariable`). **BẮT BUỘC** sử dụng skill `/object-info` để lấy chính xác (xem mục 25 trong Lưu ý quan trọng).
- `layoutId` = ID của layout hiển thị của đối tượng

#### 3. Record Data (Dữ liệu cập nhật)
Cấu trúc `recordData` giống hoàn toàn với Create Record. Chỉ cần liệt kê các trường cần cập nhật.

**Giá trị từ biến (type: 4):**
```json
{
  "first_name": {
    "fieldTypeDisplayAsInteger": false,
    "isRaw": false,
    "dataType": "TEXT",
    "valuePathName": "workflow_resource:list.userTask / Root / Tên",
    "valueDataType": "TEXT",
    "type": 4,
    "value": "$userTask.Root.ten",
    "fieldType": "short_text",
    "isList": false,
    "slug": "first_name",
    "cleanable": false
  }
}
```

**Giá trị cố định (type: 1):**
```json
{
  "do_not_call": {
    "fieldTypeDisplayAsInteger": false,
    "isRaw": false,
    "dataType": "",
    "type": 1,
    "value": false,
    "fieldType": "boolean",
    "isList": false,
    "slug": "do_not_call",
    "cleanable": false
  }
}
```

**Lưu ý thêm cho Update Record recordData:**
- Các trường trong recordData có thêm `isRaw`, `dataType`, `slug` so với Create Record
- `isRaw: false` khi lấy từ biến (type: 4)
- `dataType` = kiểu dữ liệu của trường đích (TEXT, NUMBER, etc.)
- `slug` = slug của trường đích trong object type

#### 4. Các thuộc tính khác
Giống với Create Record:
```json
{
  "valueSettingType": "MANUAL",
  "createOne": true,
  "isRawValue": true,
  "isList": false,
  "handleDuplicate": false,
  "onErrorStrategy": "SKIP_ERROR"
}
```

### Resources của Update Record Action

Resources giống cấu trúc Create Record:

```json
{
  "resources": {
    "actions": [
      {
        "id": "{ACTION_ID}",
        "type": "CREATE_RECORD",
        "name": "{TASK_NAME}",
        "slug": "{task_slug}",
        "nodeId": "{UPDATE_RECORD_NODE_ID}",
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

### Cập nhật resourcesUsedIn

Giống Create Record, khi một resource của userTask được sử dụng trong recordData của Update Record (type: 4), cần thêm `resourcesUsedIn` vào resource đó trong `resources.userTasks`:

```json
{
  "resourcesUsedIn": [
    {
      "actionType": "CREATE_RECORD",
      "name": "Update Lead",
      "count": 1,
      "id": "{ACTION_ID}",
      "parentTable": "action",
      "slug": "update_lead"
    }
  ]
}
```

**Lưu ý:** `actionType` trong `resourcesUsedIn` vẫn là `"CREATE_RECORD"` (không phải `"UPDATE_RECORD"`).

### Ví dụ quy trình với Update Record Task

**Mô tả:** Start -> Root -> Update Lead -> End Process

```
Bắt đầu -> Root (User Task) -> Update Lead (Update Record Task) -> Kết thúc
```

**Cấu hình:**
- Object Type: Lead (`objectTypeId: "OT00000000011"`) — *ID chỉ là ví dụ, thực tế lấy từ skill `/object-info` (xem mục 25 trong Lưu ý quan trọng)*
- Bản ghi cần cập nhật: `$userTask.Root.lead` (trường lookup Lead ở task Root)
- Các trường cập nhật (*field slug lấy từ skill `/object-info`*):
  - `first_name` = lấy từ biến `$userTask.Root.ten` (type: 4)
  - `last_name` = lấy từ biến `$userTask.Root.ho` (type: 4)
  - `emails` = lấy từ biến `$userTask.Root.emails` (type: 4, isList: true)
  - `do_not_call` = giá trị cố định `false` (type: 1, fieldType: boolean)

---

