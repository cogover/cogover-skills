# To Do Task

Đọc file này khi tạo To Do trong **Sequence Flow**. Không dùng node này cho các workflow type khác vì palette chỉ bật To Do với `sequence_flow`.

## Nhận diện

| Thuộc tính | Giá trị |
|---|---|
| renderKey | `TODO_TASK` |
| XML element | `elEx:todoTask` |
| Action type | `TO_DO` |
| Nơi lưu | `actions[]` và `resources.actions[]` |

## Action payload

```json
{
  "nodeId": "NOTODO00000001",
  "type": "TO_DO",
  "name": "Follow up customer",
  "slug": "follow_up_customer",
  "description": "",
  "data": {
    "maximumWaitTimeUnit": "days",
    "maximumWaitTimeValue": 3,
    "activity": {
      "title": { "type": 1, "value": "Call customer" },
      "content": { "type": 1, "value": "Confirm the requested information" },
      "contentType": "text/html",
      "taskPriority": "medium",
      "assigned": { "type": 1, "value": "PERSONNEL_ID" },
      "timeUnit": "hours",
      "dueDate": 24,
      "reminderBeforeDue": 2,
      "type": "todo",
      "status": "todo"
    }
  }
}
```

Quy tắc:

- Dùng `type` của content resource: `1` raw, `2` text template, `3` scripting, `4` other resource, `5` simple text template.
- Dùng `maximumWaitTimeUnit`: `minutes`, `hours`, `days`, `weeks`; khi có unit phải có value và ngược lại.
- Bắt buộc `activity.title.value` và `activity.assigned.value`.
- Khi có `reminderBeforeDue`, phải có `dueDate` và `timeUnit`.
- Giữ `activity.type: "todo"` và `activity.status: "todo"`.

## Output resources

Tạo ba resource, đều `availableForInput: false`, `availableForOutput: true`:

| Slug | Data type | Ý nghĩa |
|---|---|---|
| `submittedBy` | `RECORD` | Người hoàn thành task |
| `skipped` | `BOOLEAN` | Task bị bỏ qua hay không |
| `status` | `TEXT` | Trạng thái task |

## XML

```xml
<elEx:todoTask id="NOTODO00000001" name="Follow up customer">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="TODO_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>FLFLOW00000001</bpmn2:incoming>
  <bpmn2:outgoing>FLFLOW00000002</bpmn2:outgoing>
</elEx:todoTask>
```

Xem `samples/sample_sequence_flow_todo.json`.
