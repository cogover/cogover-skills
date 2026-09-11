## Update Record Task (Task Cập Nhật Bản Ghi)

Task hệ thống cập nhật bản ghi đã tồn tại của một Object, chỉ định qua `outputVariable`. Khác Create Record ở cấu hình `actions`, không ở XML. Mẫu: `samples/sample_process_user_task_update_record.json` (Start → Root → Update Lead → End Process).

### Cấu trúc trong BPMN XML

Dùng cùng element và renderKey với Create Record: `elEx:createRecordTask` (cần `xmlns:elEx="http://element-ex/schema"` trong `bpmn2:definitions`), `renderKey="CREATE_RECORD_TASK"`.

```xml
<elEx:createRecordTask id="{UPDATE_RECORD_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="CREATE_RECORD_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:createRecordTask>
```

### Cấu trúc `actions` trong JSON

Giống [Create Record](create-record-task.md#cấu-trúc-actions-trong-json) (action `type: "CREATE_RECORD"`; các key `valueSettingType`, `createOne`, `handleDuplicate`, `isRawValue`, `isList`, `fieldsForCheckDuplicate`, `duplicate*`, `onErrorStrategy` cùng giá trị), khác ở:

| Thuộc tính | Create Record | Update Record |
|---|---|---|
| `data.actionType` | `"CREATE_RECORD"` | `"UPDATE_RECORD"` |
| `data.outputVariable` | Không có hoặc rỗng | Đường dẫn đến bản ghi cần cập nhật, ví dụ `"$userTask.Root.lead"` |
| `data.outputVariableDataType` | Không có | `"RECORD"` |
| `data.outputVariablePathName` | Không có | Tên hiển thị đường dẫn, ví dụ `"workflow_resource:list.userTask / Root / Lead"` |
| Action `type` (root level) | `"CREATE_RECORD"` | `"CREATE_RECORD"` (giống nhau) |
| XML element | `elEx:createRecordTask` | `elEx:createRecordTask` (giống nhau) |

```json
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
```

- `outputVariable`: bản ghi cần cập nhật, thường là trường lookup của userTask trước (`$userTask.Root.lead`), output của Get Record (`$action.get_leads.output.record`) hoặc của Create Record trước đó (`$action.create_lead.output.record`); `outputVariableDataType` luôn `"RECORD"`; `outputVariablePathName` theo format `workflow_resource:list.userTask / {TaskName} / {FieldName}`.
- `objectTypeId`: phải khớp object type của bản ghi tham chiếu trong `outputVariable`; BẮT BUỘC lấy qua `$object-info` (xem [Chuẩn bị](../SKILL.md#chuẩn-bị)). `layoutId`: ID layout hiển thị của Object.

### `recordData`

Cấu trúc giống Create Record, chỉ liệt kê các trường cần cập nhật. Mỗi trường có thêm `isRaw` (`false` khi lấy từ biến, `type: 4`), `dataType` (kiểu dữ liệu của trường đích: `TEXT`, `NUMBER`, ...) và `slug` (slug trường đích trong object type).

Giá trị từ biến (`type: 4`):

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

Giá trị cố định (`type: 1`):

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

### Resources của Update Record Action

Giống Create Record: nhóm `type: "CREATE_RECORD"` trong `resources.actions[]` với `startAt`, `endAt` (DATE_TIME), `output` (RECORD, `actionType: "CREATE_RECORD"`) gồm `output.record` (RECORD, `metaDataType.object` là object type đã cấu hình) và `output.result` (NUMBER).

### Cập nhật `resourcesUsedIn`

Giống Create Record: resource của userTask dùng trong `recordData` (`type: 4`) có `resourcesUsedIn` trỏ đến action; `actionType` vẫn là `"CREATE_RECORD"` (không phải `"UPDATE_RECORD"`):

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
