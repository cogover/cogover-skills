# Push Message Task

Đọc file này khi cần gửi lệnh hoặc thông báo real-time tới client đang mở Cogover.

## Nhận diện

| Thuộc tính | Giá trị |
|---|---|
| renderKey | `PUSH_MESSAGE_TASK` |
| XML element | `elEx:pushMessageTask` |
| Action type | `PUSH_MESSAGE` |

## Các mode

| `pushType` | Field chính |
|---|---|
| `REFRESH_DATA` | `objectSlug`, `records`; yêu cầu client refresh record |
| `TOAST` | `position`, `size`, `duration`, `title`, `content`, `links` |
| `BACKGROUND` | `contentType`, `content`; xử lý notification nền |

`recipientType` nhận `PERSONNEL` hoặc `VIEWING_RECORD`:

- `PERSONNEL`: bắt buộc `recipients`; có thể dùng `excludes`.
- `VIEWING_RECORD`: bắt buộc `objectSlug` và `records` để xác định client đang xem record.

Mọi giá trị động dùng `{ "type": 4, "value": "$...", "valueDataType": "...", "valuePathName": "..." }`. Giá trị raw dùng `type: 1`.

## Ví dụ TOAST data

```json
{
  "pushType": "TOAST",
  "recipientType": "PERSONNEL",
  "recipients": [{ "type": 1, "value": "PERSONNEL_ID" }],
  "excludes": [],
  "position": "TOP_RIGHT",
  "size": "MEDIUM",
  "duration": 5,
  "title": { "type": 1, "value": "Process completed" },
  "content": { "type": 1, "value": "The record is ready." },
  "links": [{
    "label": { "type": 1, "value": "Open" },
    "url": { "type": 1, "value": "https://example.com" }
  }]
}
```

`position`: `TOP_LEFT`, `TOP_CENTER`, `TOP_RIGHT`, `BOTTOM_LEFT`, `BOTTOM_CENTER`, `BOTTOM_RIGHT`. `size`: `SMALL`, `MEDIUM`, `LARGE`. `duration` phải từ 1 trở lên.

## Output resources

Tạo `startAt` và `endAt` kiểu `DATE_TIME`, `availableForInput: false`, `availableForOutput: true`.

## XML

```xml
<elEx:pushMessageTask id="NOPUSH00000001" name="Notify user">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="PUSH_MESSAGE_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>FLFLOW00000001</bpmn2:incoming>
  <bpmn2:outgoing>FLFLOW00000002</bpmn2:outgoing>
</elEx:pushMessageTask>
```

Xem `samples/sample_push_message.json`.
