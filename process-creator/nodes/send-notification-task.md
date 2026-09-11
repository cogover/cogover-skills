## Send Notification Task (Task Gửi Thông báo)

Task hệ thống gửi thông báo tới personnel trong workspace khi luồng chạy đến; thông báo hiển thị trong hệ thống notification của ứng dụng. Mẫu: `samples/sample_process_send_notification.json`.

### BPMN XML

```xml
<elEx:sendNotificationTask id="{NOTIFICATION_TASK_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="SEND_NOTIFICATION_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:sendNotificationTask>
```

Element `elEx:sendNotificationTask` (không phải `bpmn2:userTask`/`bpmn2:sendTask`); khai báo `xmlns:elEx="http://element-ex/schema"` trong `bpmn2:definitions` ([namespace](../references/bpmn-xml-and-diagram.md#namespace-và-kết-nối-logic)).

### `actions` trong JSON

```json
{
  "actions": [
    {
      "id": "{ACTION_ID}",
      "nodeId": "{NOTIFICATION_TASK_NODE_ID}",
      "type": "SEND_NOTIFICATION",
      "name": "{TASK_NAME}",
      "slug": "{task_slug}",
      "description": "",
      "processId": "{PROCESS_ID}",
      "data": {
        "displayType": "SIMPLE",
        "title": { "type": 1, "value": "Tiêu đề thông báo" },
        "subTitle": { "type": 1, "value": "" },
        "content": {
          "type": "text/html",
          "content": { "type": 1, "value": "<div>Nội dung thông báo</div>" }
        },
        "from": { "fromType": "WORKSPACE_NOTIFICATION", "isRaw": true, "personnel": null },
        "to": [
          {
            "type": 4,
            "value": "$userTask.Root.submittedBy",
            "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
            "valueDataType": "RECORD"
          }
        ],
        "exclude": [],
        "redirectType": "ROUTING",
        "redirectToPage": { "type": 1, "value": "" },
        "notificationChannel": "{NOTIFICATION_CHANNEL_ID}"
      }
    }
  ]
}
```

### Hệ thống type cho giá trị

| Type | Mô tả | Áp dụng cho |
|------|-------|-------------|
| `1` | Nhập trực tiếp (raw), text thuần không chứa biến | title, subTitle, content, to (Personnel ID) |
| `2` | Giá trị từ Text Template | content |
| `3` | Giá trị từ Scripting (Formula) | content |
| `4` | Giá trị từ biến hoặc resource | title, subTitle, content, to |
| `5` | Nhập trực tiếp có chứa biến bên trong (Simple Renderer) | title, subTitle, content |

Type `5` (Simple Renderer) chỉ render biến, KHÔNG hỗ trợ if/else, for như Text Template; cú pháp `$userTask.Root.submittedBy.id`, KHÔNG bọc `{{}}` hay `{}`.

### Chi tiết các trường trong `data`

- `displayType`: `"SIMPLE"` (không có subTitle) hoặc `"FULL"` (có thêm `subTitle`).
- `title`: type 1 `{"type": 1, "value": "Tieu de thong bao"}`; type 4 `{"type": 4, "value": "$flow.bien_string", "valueDataType": "TEXT", "valuePathName": "workflow_resource:list.variable / Biến string"}`; type 5 `{"type": 5, "value": "Tieu de thong bao: $userTask.Root.submittedBy.id"}`.
- `subTitle`: cấu trúc giống `title`; chỉ hiển thị khi `displayType: "FULL"`.
- `content`: wrapper ngoài `"type"` là `"text/html"` hoặc `"text/plain"`; object `content` bên trong theo type: `1` `{"type": 1, "value": "<div>Nội dung thông báo dạng HTML</div>"}` (với `text/plain` là text thuần); `2` `{"type": 2, "value": "$flow.{text_template_slug}", "valueDataType": "TEXT", "valuePathName": "workflow_resource:list.textTemplate / {Name}"}`; `3` `{"type": 3, "value": "$flow.{formula_slug}"}`; `5` `{"type": 5, "value": "<div>Noi dung:&nbsp;$userTask.Root.submittedBy.id</div>"}`.
- `from`: từ hệ thống workspace `{"isRaw": true, "fromType": "WORKSPACE_NOTIFICATION", "personnel": null}`; từ personnel nhập ID `{"isRaw": true, "fromType": "PERSONNEL_NOTIFICATION", "personnel": "PER_SAMPLE_USER"}`; từ personnel lấy từ biến/resource `{"isRaw": false, "fromType": "PERSONNEL_NOTIFICATION", "personnel": "$userTask.Root.submittedBy"}`.
- `to`: mảng người nhận; khác Send Email, dùng Personnel ID trực tiếp. Type 1 `{"type": 1, "value": "PER_SAMPLE_USER"}` (nhiều người: nhiều phần tử); type 4 `{"type": 4, "value": "$userTask.Root.submittedBy", "valuePathName": "workflow_resource:list.userTask / Root / Submitted By", "valueDataType": "RECORD"}`.
- `exclude`: danh sách người bị loại trừ; phần tử cấu trúc giống `to`.
- `redirectType`: `"ROUTING"` (điều hướng trong app theo routing mặc định) hoặc `"NEW_TAB"` (mở tab mới); `redirectToPage`: `{"type": 1, "value": "https://example.com/detail"}` là URL mở khi click thông báo (`""` nếu không có).
- `notificationChannel`: ID kênh thông báo đã cấu hình trong workspace. Cách lấy: dùng `$object-record` lấy danh sách bản ghi của đối tượng `object_slug=notification_channel`; thường có 2 bản ghi: `name="All"` (email, web push, in-app) và `name="In App"` (chỉ in-app). Dùng `id` của bản ghi phù hợp lựa chọn người dùng; không chỉ định thì mặc định chọn `name="All"`.

### Resources của action (`resources.actions[]`)

```json
{
  "id": "{ACTION_ID}",
  "type": "SEND_NOTIFICATION",
  "name": "Send notification",
  "slug": "send_notification",
  "nodeId": "{NOTIFICATION_TASK_NODE_ID}",
  "resources": [
    { "absoluteSlug": "$action.send_notification.startAt", "dataType": "DATE_TIME", "name": "Start At", "slug": "startAt" },
    { "absoluteSlug": "$action.send_notification.endAt", "dataType": "DATE_TIME", "name": "End At", "slug": "endAt" },
    { "absoluteSlug": "$action.send_notification.output", "dataType": "NUMBER", "name": "Output", "slug": "output" }
  ]
}
```

### `resourcesUsedIn`

Resource được dùng trong Send Notification (ví dụ `$userTask.Root.submittedBy`) thêm entry:

```json
{
  "resourcesUsedIn": [
    { "actionType": "SEND_NOTIFICATION", "name": "Send notification", "count": 1, "id": "{ACTION_ID}", "parentTable": "action", "slug": "send_notification" }
  ]
}
```
