# Phone Call Task

Đọc file này khi tạo cuộc gọi từ hotline Cogover.

## Nhận diện

| Thuộc tính | Giá trị |
|---|---|
| renderKey | `PHONE_CALL_TASK` |
| XML element | `elEx:phoneCallTask` |
| Action type | `PHONE_CALL` |

## Action data

```json
{
  "from": "HOTLINE_ID",
  "to": { "type": 1, "value": "+84901234567" },
  "contentFormat": "TEXT_TO_SPEECH",
  "content": { "type": 1, "value": "Xin chào, đây là cuộc gọi từ Cogover." },
  "sequenceFlowType": "AUTOMATIC"
}
```

`contentFormat` nhận:

- `RECORDING_FILE`: dùng cấu trúc file upload đã mã hóa theo contract làm `content.value`; đặt content type của giá trị này thành raw.
- `TEXT_TO_SPEECH`: dùng text hoặc resource trong `content`.

Trong Sequence Flow:

- `AUTOMATIC`: bắt buộc hotline, người nhận và nội dung/file tương ứng.
- `MANUAL`: thêm `activity`, `maximumWaitTimeUnit`, `maximumWaitTimeValue`; bắt buộc assignee. Dù UI không dùng hotline/TTS để tự gọi ở nhánh này, API hiện lỗi NPE nếu bỏ hẳn `from`, `to` hoặc `content`. Luôn gửi ba field với giá trị rỗng theo mẫu dưới đây.

Payload tối thiểu cho Sequence `MANUAL`:

```json
{
  "sequenceFlowType": "MANUAL",
  "contentFormat": "TEXT_TO_SPEECH",
  "from": "",
  "to": { "type": 1, "value": "" },
  "content": { "type": 1, "value": "" },
  "maximumWaitTimeUnit": "days",
  "maximumWaitTimeValue": 3,
  "activity": {
    "title": { "type": 1, "value": "Call customer" },
    "content": { "type": 1, "value": "Follow up manually" },
    "contentType": "text/html",
    "taskPriority": "medium",
    "assigned": { "type": 1, "value": "PERSONNEL_ID" },
    "timeUnit": "hours",
    "dueDate": 24,
    "reminderBeforeDue": 2,
    "type": "phone_call",
    "status": "todo"
  }
}
```

`from`, `to.value` và `content.value` rỗng ở mode `MANUAL` là field giữ contract, không phải cấu hình gọi tự động. Không dùng ID personnel minh họa; lấy assignee thật từ workspace.

Ngoài Sequence Flow có thể bỏ `sequenceFlowType`; hành vi tương đương automatic.

## Output resources

Luôn tạo `$action.{slug}.output` kiểu `RECORD`. Schema runtime dự kiến gồm `from`, `to`, `recorded`, `answer_duration`, `answer_time`, `start_time`, `end_time`, `end_call_by`, `duration`.

Với Sequence manual, tạo thêm `submittedBy` (`RECORD`) và `skipped` (`BOOLEAN`). Đặt mọi output resource `availableForInput: false`, `availableForOutput: true`.

> Front-end hiện có sai khác trong handler khiến datatype của một số output child có thể bị tạo thành `RECORD`. Giữ schema semantic ở trên và xác minh payload server nếu phụ thuộc vào datatype của child.

## XML

```xml
<elEx:phoneCallTask id="NOPHONE0000001" name="Call customer">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="PHONE_CALL_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>FLFLOW00000001</bpmn2:incoming>
  <bpmn2:outgoing>FLFLOW00000002</bpmn2:outgoing>
</elEx:phoneCallTask>
```

Xem `samples/sample_phone_call.json`.
