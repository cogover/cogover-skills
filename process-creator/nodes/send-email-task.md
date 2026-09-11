## Send Email Task (Task Gửi Email)

Task hệ thống tự động gửi email khi luồng chạy đến, không cần người dùng tương tác. Text Template làm body: [references/text-template-resource.md](../references/text-template-resource.md). Tiêu chí PASS runtime và email workspace: [runtime-validation.md](runtime-validation.md#email-workspace). Mẫu: `samples/sample_process_usertask_send_email.json`.

### Hệ thống type cho giá trị

| Type | Mô tả | Áp dụng cho |
|------|-------|-------------|
| `1` | Nhập trực tiếp (raw), text thuần không chứa biến | to, cc, bcc, replyTo, subject, content |
| `2` | Giá trị từ Text Template | content |
| `3` | Giá trị từ Scripting (Formula) | content |
| `4` | Giá trị từ biến hoặc resource (variable, text template, trường con lookup...) | to, cc, bcc, replyTo, content |
| `5` | Nhập trực tiếp có chứa biến bên trong (Simple Renderer) | subject, content, `name` trong to/cc/bcc/replyTo |

Type `5` (Simple Renderer) chỉ render biến, KHÔNG hỗ trợ if/else, for như Text Template; cú pháp biến `$userTask.Root.submittedBy.first_last_name`, KHÔNG bọc `{{}}` hay `{}`.

### BPMN XML

```xml
<bpmn2:sendTask id="{SEND_TASK_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="SEND_EMAIL_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</bpmn2:sendTask>
```

Element là `bpmn2:sendTask` (không phải `bpmn2:userTask`). `action.id` và `action.nodeId` cùng bằng ID của `bpmn2:sendTask` theo [quy tắc ID](../SKILL.md#quy-tắc-id).

### `actions` trong JSON

```json
{
  "actions": [
    {
      "id": "{SEND_TASK_NODE_ID}",
      "nodeId": "{SEND_TASK_NODE_ID}",
      "type": "SEND_EMAIL",
      "name": "{TASK_NAME}",
      "slug": "{task_slug}",
      "description": "",
      "data": {
        "subject": { "type": 1, "value": "Tiêu đề email" },
        "content": {
          "type": "text/html",
          "content": { "type": 1, "value": "<div>Nội dung email HTML</div>" }
        },
        "from": {
          "fromType": "WORKSPACE_EMAIL",
          "isRaw": true,
          "personnel": null,
          "emailId": "{EMAIL_ID}"
        },
        "to": [
          { "email": { "type": 1, "value": "nguoinhan@example.com" } }
        ],
        "cc": [],
        "bcc": [],
        "replyTo": [],
        "attachments": [],
        "emailAppendSignature": false
      }
    }
  ]
}
```

### Chi tiết các trường trong `data`

#### 1. `subject`

- Type 1: `{"type": 1, "value": "Tieu de email"}`.
- Type 5: `{"type": 5, "value": "Tieu de email: $userTask.Root.submittedBy.first_last_name"}`.

#### 2. `content`

Wrapper ngoài có `"type"` là `"text/html"` hoặc `"text/plain"`; object `content` bên trong chứa giá trị thực tế theo type:

| Type | Object `content` bên trong |
|---|---|
| `1` | `{"type": 1, "value": "<div>Nội dung nhập thủ công</div>"}` |
| `2` | `{"type": 2, "value": "$flow.{text_template_slug}", "valueDataType": "TEXT", "valuePathName": "workflow_resource:list.textTemplate / {Name}"}`; nội dung render với biến VTL trong template |
| `3` | `{"type": 3, "value": "$flow.{formula_slug}"}` |
| `4` | `{"type": 4, "value": "$flow.{variable_slug}", "valueDataType": "TEXT", "valuePathName": "workflow_resource:list.variable / {Name}"}` |
| `5` | `{"type": 5, "value": "<div>Đây là nội dung chứa biến: $userTask.Root.submittedBy.first_last_name</div>"}`; payload front-end có thể kèm `valueDataType: "TEXT"` và `valuePathName` như type 4 |

Nội dung người dùng viết có biến dạng `{{Tên biến}}` (ví dụ `Chào anh/chị {{Tên}}`): tạo một Text Template riêng cho mỗi body, thay `{{}}` bằng trường tương ứng của bản ghi liên kết theo cú pháp VTL `$flow.input.record.{field_slug}`, rồi trỏ `content` type 2 tới template đó. Ví dụ: `{{Tên}}` → `$flow.input.record.last_first_name`, `{{Email}}` → `$flow.input.record.emails`, `{{Công ty}}` → `$flow.input.record.company`, `{{SĐT}}` → `$flow.input.record.phones`, `{{Tên bạn}}` (người gửi) → `$flow.input.record.owner.first_last_name`.

#### 3. `from`

- Email workspace: `{"isRaw": true, "fromType": "WORKSPACE_EMAIL", "personnel": null, "emailId": "{EMAIL_ID}"}`. `emailId` là ID sender cấu hình ở khu vực workspace email dùng chung; không suy ra `emailId` từ tên hiển thị hoặc địa chỉ email và không tái sử dụng ID trong sample.
- Email của personnel: `{"isRaw": true, "fromType": "PERSONNEL_EMAIL", "personnel": "{PERSONNEL_ID}", "emailId": null}`.

Phân biệt `/process/account` và Workspace Email:

- Email kết nối ở `/process/account` là account gửi mail gắn với personnel hiện tại. Chọn sender này trong Process editor thì payload canonical là `fromType: "PERSONNEL_EMAIL"`, `personnel: "PER..."`, `emailId: null`, dù UI hiển thị tên/email của account. `WORKSPACE_EMAIL` là loại sender workspace dùng chung và bắt buộc `emailId` thật; hai loại không thay thế cho nhau.
- Địa chỉ email trong hồ sơ personnel chưa đủ để `PERSONNEL_EMAIL` chạy; personnel phải có email account/channel đã kết nối, nếu thiếu runtime báo `USER_DONT_HAVE_EMAIL`.
- Không có endpoint list sender: (1) tạo một process DRAFT probe, mở editor trên Chrome và chọn đúng sender theo tên/email người dùng chỉ định; (2) Save nhưng chưa Kích hoạt/Tạo lượt chạy; (3) GET-back và copy nguyên object `data.from` sang process mới, không đoán `fromType`, personnel ID hay `emailId`; (4) xoá probe chỉ khi người dùng xác nhận, nếu không để nguyên DRAFT và báo link.
- Retest sender vừa cấu hình: đặt `continueIfFromEmailNotExist: false` để lỗi channel không bị che. Chỉ đánh PASS sau khi mailbox đích nhận đúng From/To/Subject/body.

#### 4. `to`, `cc`, `bcc`, `replyTo`

Bốn mảng cùng cấu trúc; mỗi phần tử có `email` và tuỳ chọn `name` (`type` `4` hoặc `5`); `index` optional.

- Nhập trực tiếp: `{"email": {"type": 1, "value": "recipient@example.com"}}`.
- Từ biến/resource (type 4): `email` dùng `dataType` và `dataPathName` (không phải `pathName`):

```json
{
  "name": { "type": 4, "value": "$flow.bien_string" },
  "email": {
    "type": 4,
    "value": "$flow.bien_string",
    "dataType": "TEXT",
    "dataPathName": "workflow_resource:list.variable / Biến string"
  }
}
```

Nguồn type 4 khác chỉ đổi `value`/`dataPathName`: Text Template `$flow.text_template` với `workflow_resource:list.textTemplate / Text template`; trường con của lookup `$userTask.Root.chon_lead.emails` với `workflow_resource:list.userTask / Root / Chọn Lead / Emails`. Một mảng có thể trộn nhiều kiểu phần tử.

#### 5. `attachments`

`[]` hoặc file từ biến/trường: `[{"type": 2, "value": "$userTask.Root.file_field", "pathName": "workflow_resource:list.userTask / Root / File Field", "dataType": "FILE"}]`.

#### 6. Thuộc tính khác (đều optional, backend dùng mặc định nếu không truyền)

- `sequenceFlowType`: `"AUTOMATIC"` (mặc định) tự chuyển bước sau khi gửi; `"MANUAL"` gửi thủ công (tạo todo task).
- `maximumWaitTimeUnit`, `maximumWaitTimeValue`: `null`.
- `emailAppendSignature`: thêm chữ ký, mặc định `false`. `emailLayout`: mặc định `""`.
- `continueIfFromEmailNotExist`: mặc định `false`; `true` thì personnel không có email → action bỏ qua thay vì báo lỗi (dùng với `PERSONNEL_EMAIL` khi personnel có thể chưa cấu hình email).

#### 7. Quy trình Sequence (gửi email đến bản ghi)

- Gửi đến trường email của bản ghi được kết nối thay vì `to`: `"slugEmailFieldRecord": ["emails"]` (slug trường email của bản ghi, ví dụ Lead có trường `emails`), `"addActivityToRecord": true` (ghi email log vào activities của bản ghi trên CRM), `"sendToRecordEmailsField": true`, `"to": []`.
- Người gửi là Owner của bản ghi: `{"personnelDataType": "RECORD", "personnelPathName": "workflow_resource:list.resource / Input / Record / Owner", "isRaw": false, "fromType": "PERSONNEL_EMAIL", "personnel": "$flow.input.record.owner", "emailId": null}`.
- Gửi vào cùng email thread với một node email khác (khả dụng cho mọi loại workflow): `"sendEmailToEmailThreadPrevious": true` và `"nodeIdSendEmailToEmailThreadPrevious": "{NODE_ID_CUA_EMAIL_TRUOC_DO}"` (nodeId của node email muốn nối tiếp). Email đầu tiên cũng đặt `sendEmailToEmailThreadPrevious: true` nhưng KHÔNG có `nodeIdSendEmailToEmailThreadPrevious`; email thứ 2 trở đi thêm key này trỏ tới email trước.

### Dùng Text Template cho content

Tạo Text Template trong `resources.custom`; thêm `resourcesUsedIn` của Text Template trỏ tới action email, `resourcesUsedIn` của các resource được dùng trong template và `externalResourcesUsedIn` ở root level khi dùng trường con của lookup: [references/text-template-resource.md](../references/text-template-resource.md#resourcesusedin-và-externalresourcesusedin).
