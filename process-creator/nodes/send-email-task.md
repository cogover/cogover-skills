## Send Email Task (Task Gửi Email)

### Mô tả
Send Email Task là một task hệ thống tự động gửi email khi luồng chạy đến. Không cần người dùng tương tác.

### Hệ thống Type cho giá trị

Các trường trong email (to, cc, bcc, replyTo, subject, content) sử dụng hệ thống type để xác định cách lấy giá trị:

| Type | Mô tả                                                        | Áp dụng cho                                     |
|------|--------------------------------------------------------------|--------------------------------------------------|
| `1`  | Nhập trực tiếp (raw) - text thuần, không chứa biến           | to, cc, bcc, replyTo, subject, content           |
| `2`  | Giá trị từ Text Template                                     | content                                          |
| `3`  | Giá trị từ Scripting                                         | content                                          |
| `4`  | Giá trị từ biến hoặc resource (variable, text template, ...) | to, cc, bcc, replyTo, content                    |
| `5`  | Nhập trực tiếp có chứa biến bên trong (Simple Renderer)      | subject, content, name trong to/cc/bcc/replyTo   |

**Lưu ý về type=5 (Simple Renderer):**
- Hệ thống sử dụng Simple Renderer để render text, chỉ hỗ trợ render các biến
- KHÔNG hỗ trợ render if/else, for,... như Text Template
- Cú pháp biến: `$userTask.Root.submittedBy.first_last_name` (KHÔNG bọc xung quanh `{{}}` hay `{}`)

### Cấu trúc trong BPMN XML
```xml
<bpmn2:sendTask id="{SEND_TASK_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="SEND_EMAIL_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</bpmn2:sendTask>
```

**Lưu ý quan trọng:**
- Sử dụng `bpmn2:sendTask` thay vì `bpmn2:userTask`
- `renderKey="SEND_EMAIL_TASK"`
- Trong create payload, `action.id` và `action.nodeId` cùng bằng chính ID của `bpmn2:sendTask`. Skill có thể sinh `NO...`; BPMN modeler có thể sinh `Activity_*`. Cả hai hợp lệ nếu mọi reference nhất quán; không tự sinh `AC...` riêng.

### Cấu trúc `actions` trong JSON
Thêm section `actions` vào JSON root level với cấu trúc sau:
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
        "subject": {
          "type": 1,
          "value": "Tiêu đề email"
        },
        "content": {
          "type": "text/html",
          "content": {
            "type": 1,
            "value": "<div>Nội dung email HTML</div>"
          }
        },
        "from": {
          "fromType": "WORKSPACE_EMAIL",
          "isRaw": true,
          "personnel": null,
          "emailId": "{EMAIL_ID}"
        },
        "to": [
          {
            "email": {
              "type": 1,
              "value": "nguoinhan@example.com"
            }
          }
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

### Chi tiết các trường cấu hình email

#### 1. Subject (Tiêu đề)

**Cách 1: Nhập trực tiếp, text thuần không chứa biến (type=1)**
```json
{
  "subject": {
    "type": 1,
    "value": "Tieu de email"
  }
}
```

**Cách 2: Nhập trực tiếp có chứa biến bên trong (type=5 - Simple Renderer)**
```json
{
  "subject": {
    "type": 5,
    "value": "Tieu de email: $userTask.Root.submittedBy.first_last_name"
  }
}
```
- Sử dụng Simple Renderer, chỉ hỗ trợ render biến (không hỗ trợ if/else, for,... như Text Template)
- Cú pháp biến: `$userTask.Root.submittedBy.first_last_name` (KHÔNG bọc `{{}}` hay `{}`)

#### 2. Content (Nội dung)

Trường content có wrapper bên ngoài với `"type"` là `"text/html"` hoặc `"text/plain"`. Bên trong là object `content` chứa giá trị thực tế.

**Cách 1: Nội dung nhập trực tiếp, text thuần không chứa biến (type=1)**
```json
{
  "content": {
    "type": "text/html",
    "content": {
      "type": 1,
      "value": "<div>Nội dung nhập thủ công</div>"
    }
  }
}
```

**Cách 2: Nội dung từ Text Template (type=2)**
```json
{
  "content": {
    "type": "text/html",
    "content": {
      "type": 2,
      "value": "$flow.text_template",
      "valueDataType": "TEXT",
      "valuePathName": "workflow_resource:list.textTemplate / Text template"
    }
  }
}
```
- `content.type: 2` = giá trị từ Text Template
- `content.value` = đường dẫn Text Template: `$flow.{text_template_slug}`
- `content.valuePathName` = tên hiển thị: `workflow_resource:list.textTemplate / {Name}`
- `content.valueDataType` = `"TEXT"`
- Khi dùng Text Template, nội dung email sẽ được render với các biến VTL trong template

**Cách 3: Nội dung lấy từ biến hoặc resource khác (type=4)**
```json
{
  "content": {
    "type": "text/html",
    "content": {
      "type": 4,
      "value": "$flow.bien_string",
      "valueDataType": "TEXT",
      "valuePathName": "workflow_resource:list.variable / Biến string"
    }
  }
}
```
- `content.type: 4` = giá trị lấy từ biến hoặc resource
- `content.value` = đường dẫn đến biến: `$flow.{variable_slug}`
- `content.valuePathName` = tên hiển thị đường dẫn
- `content.valueDataType` = `"TEXT"`

**Cách 4: Nội dung từ Scripting (type=3)**
```json
{
  "content": {
    "type": "text/html",
    "content": {
      "type": 3,
      "value": "$flow.bien_formula"
    }
  }
}
```
- `content.type: 3` = giá trị từ Scripting engine
- `content.value` = đường dẫn đến biến

**Cách 5: Nội dung nhập trực tiếp có chứa biến bên trong (type=5 - Simple Renderer)**
```json
{
  "content": {
    "type": "text/html",
    "content": {
      "type": 5,
      "value": "<div>Đây là nội dung chứa biến: $userTask.Root.submittedBy.first_last_name</div>",
      "valueDataType": "TEXT",
      "valuePathName": "workflow_resource:list.variable / Biến string"
    }
  }
}
```
- `content.type: 5` = nội dung nhập trực tiếp có chứa biến
- Sử dụng Simple Renderer, chỉ hỗ trợ render biến (KHÔNG hỗ trợ if/else, for,... như Text Template)
- Cú pháp biến: `$userTask.Root.submittedBy.first_last_name` (KHÔNG bọc `{{}}` hay `{}`)

#### 3. From (Người gửi)

**Cách 1: Sử dụng email workspace**
```json
{
  "from": {
    "isRaw": true,
    "fromType": "WORKSPACE_EMAIL",
    "personnel": null,
    "emailId": "{EMAIL_ID}"
  }
}
```
- `fromType: "WORKSPACE_EMAIL"` = sử dụng email của workspace
- `emailId` = ID của email đã cấu hình trong workspace
- Đây là sender cấu hình ở khu vực workspace email dùng chung. Không suy ra `emailId` từ tên hiển thị hoặc địa chỉ email và không tái sử dụng ID trong sample.

**Cách 2: Sử dụng email của personnel**
```json
{
  "from": {
    "isRaw": true,
    "fromType": "PERSONNEL_EMAIL",
    "personnel": "{PERSONNEL_ID}",
    "emailId": null
  }
}
```
- `fromType: "PERSONNEL_EMAIL"` = sử dụng email của một personnel cụ thể
- `personnel` = ID của personnel (ví dụ: `"PER_SAMPLE_USER"`)
- `emailId` = `null` (không dùng email workspace)

#### Phân biệt `/process/account` và Workspace Email

- Email được kết nối ở `/process/account` là account gửi mail gắn với personnel hiện tại. Khi chọn sender này trong Process editor, payload canonical có thể là `fromType: "PERSONNEL_EMAIL"`, `personnel: "PER..."`, `emailId: null` — dù UI hiển thị tên/email của account. Đây là đúng contract.
- `WORKSPACE_EMAIL` là loại sender workspace dùng chung riêng và bắt buộc `emailId` thật. Hai loại không thay thế cho nhau.
- Địa chỉ email có trong hồ sơ personnel chưa đủ để `PERSONNEL_EMAIL` chạy; personnel phải có email account/channel đã kết nối. Nếu thiếu, runtime có thể báo `USER_DONT_HAVE_EMAIL`.

Nếu skill/API phụ trợ không cung cấp endpoint list sender:

1. Tạo một process DRAFT probe, mở editor trên Chrome và chọn đúng sender bằng tên/email người dùng chỉ định.
2. Save nhưng chưa Kích hoạt/Tạo lượt chạy.
3. GET-back process và copy nguyên object `data.from` canonical sang process mới; không đoán `fromType`, personnel ID hoặc emailId.
4. Xóa probe chỉ khi người dùng xác nhận xóa; nếu không, để nguyên DRAFT và báo link.

Khi retest sender vừa được cấu hình, đặt `continueIfFromEmailNotExist: false` để lỗi channel không bị che khuất. Chỉ đánh PASS sau khi mailbox đích nhận đúng From/To/Subject/body.

#### 4. To, CC, BCC, ReplyTo (Người nhận)

Cấu trúc `to`, `cc`, `bcc`, `replyTo` hoàn toàn giống nhau. Mỗi phần tử trong mảng có các trường: `email` và tùy chọn `name`.

**Lưu ý:** Trường `index` là optional, backend không bắt buộc.

**Cách 1: Nhập email trực tiếp (type=1)**
```json
{
  "email": {
    "type": 1,
    "value": "recipient@example.com"
  }
}
```

**Cách 2: Lấy từ biến TEXT (type=4)**
```json
{
  "name": {
    "type": 4,
    "value": "$flow.bien_string"
  },
  "email": {
    "type": 4,
    "value": "$flow.bien_string",
    "dataType": "TEXT",
    "dataPathName": "workflow_resource:list.variable / Biến string"
  }
}
```
- `email.type: 4` = lấy email từ biến hoặc resource
- `email.value` = đường dẫn đến biến (ví dụ: `$flow.bien_string`)
- `email.dataPathName` = tên hiển thị đường dẫn (dùng `dataPathName` thay vì `pathName`)
- `email.dataType` = `"TEXT"`
- `name` = trường tên hiển thị, `type` có thể dùng `4` hoặc `5`

**Cách 3: Lấy từ Text Template (type=4)**
```json
{
  "name": {
    "type": 4,
    "value": "$flow.text_template"
  },
  "email": {
    "type": 4,
    "value": "$flow.text_template",
    "dataType": "TEXT",
    "dataPathName": "workflow_resource:list.textTemplate / Text template"
  }
}
```

**Cách 4: Lấy từ trường con của lookup (type=4)**
```json
{
  "name": {
    "type": 4,
    "value": "$userTask.Root.chon_lead.emails"
  },
  "email": {
    "type": 4,
    "value": "$userTask.Root.chon_lead.emails",
    "dataType": "TEXT",
    "dataPathName": "workflow_resource:list.userTask / Root / Chọn Lead / Emails"
  }
}
```

**Ví dụ mảng `to` kết hợp nhiều kiểu:**
```json
{
  "to": [
    {
      "email": {
        "type": 1,
        "value": "recipient@example.com"
      }
    },
    {
      "email": {
        "type": 1,
        "value": "recipient2@example.com"
      }
    },
    {
      "name": {
        "type": 4,
        "value": "$flow.bien_string"
      },
      "email": {
        "dataPathName": "workflow_resource:list.variable / Biến string",
        "dataType": "TEXT",
        "type": 4,
        "value": "$flow.bien_string"
      }
    },
    {
      "name": {
        "type": 4,
        "value": "$flow.text_template"
      },
      "email": {
        "dataPathName": "workflow_resource:list.textTemplate / Text template",
        "dataType": "TEXT",
        "type": 4,
        "value": "$flow.text_template"
      }
    }
  ]
}
```

#### 5. Attachments (Đính kèm)
```json
{
  "attachments": []
}
```
Hoặc với file đính kèm từ biến:
```json
{
  "attachments": [
    {
      "type": 2,
      "value": "$userTask.Root.file_field",
      "pathName": "workflow_resource:list.userTask / Root / File Field",
      "dataType": "FILE"
    }
  ]
}
```

#### 6. Các thuộc tính khác (đều optional)
```json
{
  "sequenceFlowType": "AUTOMATIC",
  "maximumWaitTimeUnit": null,
  "maximumWaitTimeValue": null,
  "emailAppendSignature": false,
  "emailLayout": "",
  "continueIfFromEmailNotExist": false
}
```
- Tất cả các trường trên đều **không bắt buộc** (optional), backend sẽ dùng giá trị mặc định nếu không truyền
- `sequenceFlowType`: `"AUTOMATIC"` (mặc định) = tự động chuyển sang bước tiếp theo sau khi gửi; `"MANUAL"` = gửi thủ công (tạo todo task)
- `emailAppendSignature` = có thêm chữ ký không (mặc định `false`)
- `emailLayout` = layout email (mặc định `""`)
- `continueIfFromEmailNotExist` = nếu `true`, khi personnel không có email thì action sẽ bỏ qua thay vì báo lỗi (mặc định `false`). Hữu ích khi dùng `fromType: "PERSONNEL_EMAIL"` và personnel có thể chưa cấu hình email

#### 7. Cấu hình đặc biệt cho quy trình Sequence (gửi email đến bản ghi)

Khi quy trình là loại **Sequence** (gắn với một đối tượng/bản ghi như Lead, Contact,...), action Gửi email cần cấu hình thêm các trường sau:

**a. Gửi email đến trường email của bản ghi:**

Thay vì chỉ định người nhận trong `to`, cần sử dụng `slugEmailFieldRecord` để gửi email đến trường email của bản ghi mà người dùng kết nối. Ví dụ bản ghi Lead có trường `emails` lưu các email của khách hàng tiềm năng.

```json
{
  "slugEmailFieldRecord": ["emails"],
  "addActivityToRecord": true,
  "sendToRecordEmailsField": true,
  "to": []
}
```

- `slugEmailFieldRecord`: mảng chứa slug của trường email trong bản ghi (ví dụ: `["emails"]` cho bản ghi Lead)
- `addActivityToRecord: true`: thêm email log vào activities của bản ghi đó trên CRM
- `sendToRecordEmailsField: true`: cho phép gửi đến trường email của bản ghi
- `to: []`: mảng rỗng vì đã gửi qua `slugEmailFieldRecord`

**b. Người gửi (from) lấy từ Owner của bản ghi:**

Trong quy trình Sequence, thường gửi email từ Owner của bản ghi (người sở hữu lead/contact):

```json
{
  "from": {
    "personnelDataType": "RECORD",
    "personnelPathName": "workflow_resource:list.resource / Input / Record / Owner",
    "isRaw": false,
    "fromType": "PERSONNEL_EMAIL",
    "personnel": "$flow.input.record.owner",
    "emailId": null
  }
}
```

- `fromType: "PERSONNEL_EMAIL"` + `personnelDataType: "RECORD"` = gửi từ email của personnel lấy từ bản ghi
- `personnel: "$flow.input.record.owner"` = lấy owner của bản ghi input
- `personnelPathName` = tên hiển thị đường dẫn
- `isRaw: false` vì giá trị lấy từ biến (không phải nhập trực tiếp)
- `emailId: null`

**c. Gửi email vào cùng luồng (email thread) với một Node gửi email khác:**

Trường `sendEmailToEmailThreadPrevious` và `nodeIdSendEmailToEmailThreadPrevious` cho phép gửi email vào cùng luồng mail (email thread) với một Node gửi email khác trong cùng process. Tính năng này khả dụng cho **mọi loại workflow**, không chỉ Sequence.

```json
{
  "sendEmailToEmailThreadPrevious": true,
  "nodeIdSendEmailToEmailThreadPrevious": "{NODE_ID_CUA_EMAIL_TRUOC_DO}"
}
```

- `sendEmailToEmailThreadPrevious: true`: bật chế độ gửi vào cùng email thread
- `nodeIdSendEmailToEmailThreadPrevious`: chỉ ra nodeId của Node gửi email khác trong process mà muốn gửi tiếp vào cùng luồng mail đó

**Lưu ý:** Email đầu tiên cũng có `sendEmailToEmailThreadPrevious: true` nhưng KHÔNG có `nodeIdSendEmailToEmailThreadPrevious` (vì chưa có email trước đó).

**d. Ví dụ đầy đủ - Email đầu tiên trong Sequence (gửi đến bản ghi Lead):**

```json
{
  "data": {
    "cc": [],
    "sendEmailToEmailThreadPrevious": true,
    "bcc": [],
    "attachments": [],
    "subject": {
      "type": 1,
      "value": "Trao đổi thêm về Cogover CRM cho đội sales của anh/chị"
    },
    "slugEmailFieldRecord": [
      "emails"
    ],
    "addActivityToRecord": true,
    "emailLayout": "",
    "maximumWaitTimeUnit": null,
    "content": {
      "type": "text/html",
      "content": {
        "type": 2,
        "value": "$flow.email_1_body",
        "valueDataType": "TEXT",
        "valuePathName": "workflow_resource:list.textTemplate / Email 1 body"
      }
    },
    "emailAppendSignature": true,
    "maximumWaitTimeValue": null,
    "sendToRecordEmailsField": true,
    "from": {
      "personnelDataType": "RECORD",
      "personnelPathName": "workflow_resource:list.resource / Input / Record / Owner",
      "isRaw": false,
      "fromType": "PERSONNEL_EMAIL",
      "personnel": "$flow.input.record.owner",
      "emailId": null
    },
    "sequenceFlowType": "AUTOMATIC",
    "to": []
  },
  "processId": "{PROCESS_ID}",
  "name": "Gửi email 1",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "SEND_EMAIL",
  "nodeId": "{NODE_ID_EMAIL_1}",
  "slug": "gui_email_1"
}
```

**e. Ví dụ đầy đủ - Email follow-up (email thứ 2 trở đi) trong Sequence:**

```json
{
  "data": {
    "cc": [],
    "sendEmailToEmailThreadPrevious": true,
    "bcc": [],
    "attachments": [],
    "subject": {
      "type": 1,
      "value": "subject"
    },
    "slugEmailFieldRecord": [
      "emails"
    ],
    "addActivityToRecord": true,
    "emailLayout": "",
    "maximumWaitTimeUnit": null,
    "content": {
      "type": "text/html",
      "content": {
        "type": 2,
        "value": "$flow.email_2_body",
        "valueDataType": "TEXT",
        "valuePathName": "workflow_resource:list.textTemplate / Email 2 body"
      }
    },
    "emailAppendSignature": true,
    "maximumWaitTimeValue": null,
    "sendToRecordEmailsField": true,
    "nodeIdSendEmailToEmailThreadPrevious": "{NODE_ID_EMAIL_1}",
    "from": {
      "personnelDataType": "RECORD",
      "personnelPathName": "workflow_resource:list.resource / Input / Record / Owner",
      "isRaw": false,
      "fromType": "PERSONNEL_EMAIL",
      "personnel": "$flow.input.record.owner",
      "emailId": null
    },
    "sequenceFlowType": "AUTOMATIC",
    "to": []
  },
  "processId": "{PROCESS_ID}",
  "name": "Gửi email 2",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "SEND_EMAIL",
  "nodeId": "{NODE_ID_EMAIL_2}",
  "slug": "gui_email_2"
}
```

**Lưu ý khác biệt so với email đầu tiên:**
- Có thêm `nodeIdSendEmailToEmailThreadPrevious: "{NODE_ID_EMAIL_1}"` trỏ đến nodeId của email trước đó

#### 8. Xử lý biến `{{}}` trong nội dung email - Sử dụng Text Template

Khi người dùng viết nội dung email có chứa biến dạng `{{Tên biến}}` (ví dụ: `Chào anh/chị {{Tên}}`), cần **tạo Text Template** cho body của email và thay thế các biến `{{}}` bằng trường tương ứng trong bản ghi.

**Quy tắc:**
1. Mỗi body email có chứa `{{}}` cần tạo một Text Template riêng
2. Tìm trường thích hợp trong bản ghi (của đối tượng liên kết) để thay thế vào chỗ biến `{{}}`
3. Sử dụng cú pháp VTL trong Text Template: `$flow.input.record.{field_slug}`

**Ví dụ chuyển đổi:**

| Người dùng viết | Thay thế trong Text Template         |
|-----------------|--------------------------------------|
| `{{Tên}}`       | `$flow.input.record.last_first_name` |
| `{{Email}}`     | `$flow.input.record.emails`          |
| `{{Công ty}}`   | `$flow.input.record.company`         |
| `{{SĐT}}`       | `$flow.input.record.phones`          |

**Ví dụ:** Người dùng muốn nội dung:
```
Chào anh/chị {{Tên}},
Mình là {{Tên bạn}} từ Cogover.
```

Trong Text Template, nội dung sẽ là:
```
Chào anh/chị $flow.input.record.last_first_name,
Mình là $flow.input.record.owner.first_last_name từ Cogover.
```

**Cấu hình content trong action email khi dùng Text Template:**
```json
{
  "content": {
    "type": "text/html",
    "content": {
      "type": 2,
      "value": "$flow.email_1_body",
      "valueDataType": "TEXT",
      "valuePathName": "workflow_resource:list.textTemplate / Email 1 body"
    }
  }
}
```

- `content.type: 2` = giá trị từ Text Template
- `content.value`: `$flow.{text_template_slug}` - đường dẫn đến Text Template đã tạo
- Cần tạo Text Template tương ứng trong `resources.custom` (xem section Text Template)

### Ví dụ đầy đủ

#### Ví dụ 1: Subject và content nhập trực tiếp (type=1), to kết hợp nhiều kiểu

- **to**: nhập trực tiếp `recipient@example.com`, `recipient2@example.com` (type=1) + lấy từ biến TEXT `$flow.bien_string` (type=4) + lấy từ Text Template `$flow.text_template` (type=4)
- **cc, bcc**: hoàn toàn tương tự to
- **subject**: text thuần, không chứa biến (type=1)
- **content**: text thuần, không chứa biến (type=1)

```json
{
  "data": {
    "subject": {
      "type": 1,
      "value": "Tieu de email"
    },
    "content": {
      "type": "text/html",
      "content": {
        "type": 1,
        "value": "<div>Nội dung nhập thủ công</div>"
      }
    },
    "from": {
      "isRaw": true,
      "fromType": "WORKSPACE_EMAIL",
      "personnel": null,
      "emailId": "KWVWQEKLSHD"
    },
    "to": [
      {
        "email": {
          "type": 1,
          "value": "recipient@example.com"
        }
      },
      {
        "email": {
          "type": 1,
          "value": "recipient2@example.com"
        }
      },
      {
        "name": {
          "type": 4,
          "value": "$flow.bien_string"
        },
        "email": {
          "dataPathName": "workflow_resource:list.variable / Biến string",
          "dataType": "TEXT",
          "type": 4,
          "value": "$flow.bien_string"
        }
      },
      {
        "name": {
          "type": 4,
          "value": "$flow.text_template"
        },
        "email": {
          "dataPathName": "workflow_resource:list.textTemplate / Text template",
          "dataType": "TEXT",
          "type": 4,
          "value": "$flow.text_template"
        }
      }
    ],
    "cc": [],
    "bcc": [],
    "replyTo": [],
    "attachments": [],
    "emailAppendSignature": false
  },
  "processId": "PE00000000002",
  "name": "Send email",
  "description": "",
  "id": "AC00000000026",
  "type": "SEND_EMAIL",
  "nodeId": "NO00000000077",
  "slug": "send_email"
}
```

#### Ví dụ 2: Content lấy từ Text Template (type=2)

- **content**: lấy nội dung từ Text Template `$flow.text_template` (type=2)

```json
{
  "id": "AC00000000015",
  "nodeId": "NO00000000015",
  "type": "SEND_EMAIL",
  "name": "Send email",
  "slug": "send_email",
  "description": "",
  "data": {
    "subject": {
      "type": 1,
      "value": "Tieu de email"
    },
    "content": {
      "type": "text/html",
      "content": {
        "type": 2,
        "value": "$flow.text_template",
        "valueDataType": "TEXT",
        "valuePathName": "workflow_resource:list.textTemplate / Text template"
      }
    },
    "from": {
      "isRaw": true,
      "fromType": "WORKSPACE_EMAIL",
      "personnel": null,
      "emailId": "KWVWQEKLSHD"
    },
    "to": [
      {
        "email": {
          "type": 1,
          "value": "recipient@example.com"
        }
      },
      {
        "email": {
          "type": 1,
          "value": "recipient2@example.com"
        }
      },
      {
        "email": {
          "type": 4,
          "value": "$flow.bien_string",
          "dataType": "TEXT",
          "dataPathName": "workflow_resource:list.variable / Biến string"
        },
        "name": {
          "type": 4,
          "value": "$flow.bien_string"
        }
      },
      {
        "email": {
          "type": 4,
          "value": "$flow.text_template",
          "dataType": "TEXT",
          "dataPathName": "workflow_resource:list.textTemplate / Text template"
        },
        "name": {
          "type": 4,
          "value": "$flow.text_template"
        }
      }
    ],
    "cc": [],
    "bcc": [],
    "replyTo": [],
    "attachments": [],
    "emailAppendSignature": false
  }
}
```

#### Ví dụ 3: Content lấy từ biến/resource (type=4)

- **content**: lấy nội dung từ biến `$flow.bien_string` (type=4)

```json
{
  "data": {
    "subject": {
      "type": 1,
      "value": "Tieu de email"
    },
    "content": {
      "type": "text/html",
      "content": {
        "valuePathName": "workflow_resource:list.variable / Biến string",
        "valueDataType": "TEXT",
        "type": 4,
        "value": "$flow.bien_string"
      }
    },
    "from": {
      "isRaw": true,
      "fromType": "WORKSPACE_EMAIL",
      "personnel": null,
      "emailId": "KWVWQEKLSHD"
    },
    "to": [
      {
        "email": {
          "type": 1,
          "value": "recipient@example.com"
        }
      },
      {
        "email": {
          "type": 1,
          "value": "recipient2@example.com"
        }
      },
      {
        "name": {
          "type": 4,
          "value": "$flow.bien_string"
        },
        "email": {
          "dataPathName": "workflow_resource:list.variable / Biến string",
          "dataType": "TEXT",
          "type": 4,
          "value": "$flow.bien_string"
        }
      },
      {
        "name": {
          "type": 4,
          "value": "$flow.text_template"
        },
        "email": {
          "dataPathName": "workflow_resource:list.textTemplate / Text template",
          "dataType": "TEXT",
          "type": 4,
          "value": "$flow.text_template"
        }
      }
    ],
    "cc": [],
    "bcc": [],
    "replyTo": [],
    "attachments": [],
    "emailAppendSignature": false
  },
  "processId": "PE00000000002",
  "name": "Send email",
  "description": "",
  "id": "ACDWWSQEYKULP",
  "type": "SEND_EMAIL",
  "nodeId": "NO00000000081",
  "slug": "send_email"
}
```

#### Ví dụ 4: Content nhập trực tiếp có chứa biến (type=5 - Simple Renderer)

- **content**: nhập trực tiếp có chứa biến bên trong (type=5). Hệ thống sử dụng Simple Renderer để render, chỉ hỗ trợ render biến (KHÔNG hỗ trợ if/else, for,... như Text Template). Cú pháp biến: `$userTask.Root.submittedBy.first_last_name` (KHÔNG bọc `{{}}` hay `{}`)

```json
{
  "data": {
    "subject": {
      "type": 1,
      "value": "Tieu de email"
    },
    "content": {
      "type": "text/html",
      "content": {
        "valuePathName": "workflow_resource:list.variable / Biến string",
        "valueDataType": "TEXT",
        "type": 5,
        "value": "<div>Đây là nội dung chứa biến: $userTask.Root.submittedBy.first_last_name</div>"
      }
    },
    "from": {
      "isRaw": true,
      "fromType": "WORKSPACE_EMAIL",
      "personnel": null,
      "emailId": "KWVWQEKLSHD"
    },
    "to": [
      {
        "email": {
          "type": 1,
          "value": "recipient@example.com"
        }
      },
      {
        "email": {
          "type": 1,
          "value": "recipient2@example.com"
        }
      },
      {
        "name": {
          "type": 4,
          "value": "$flow.bien_string"
        },
        "email": {
          "dataPathName": "workflow_resource:list.variable / Biến string",
          "dataType": "TEXT",
          "type": 4,
          "value": "$flow.bien_string"
        }
      },
      {
        "name": {
          "type": 4,
          "value": "$flow.text_template"
        },
        "email": {
          "dataPathName": "workflow_resource:list.textTemplate / Text template",
          "dataType": "TEXT",
          "type": 4,
          "value": "$flow.text_template"
        }
      }
    ],
    "cc": [],
    "bcc": [],
    "replyTo": [],
    "attachments": [],
    "emailAppendSignature": false
  },
  "processId": "PE00000000002",
  "name": "Send email",
  "description": "",
  "id": "AC00000000004",
  "type": "SEND_EMAIL",
  "nodeId": "NO00000000026",
  "slug": "send_email"
}
```

#### Ví dụ 5: Subject nhập trực tiếp có chứa biến (type=5 - Simple Renderer)

- **subject**: nhập trực tiếp có chứa biến bên trong (type=5). Cú pháp biến: `$userTask.Root.submittedBy.first_last_name` (KHÔNG bọc `{{}}` hay `{}`)
- **content**: nhập trực tiếp có chứa biến (type=5)

```json
{
  "id": "AC00000000013",
  "nodeId": "NO00000000006",
  "type": "SEND_EMAIL",
  "name": "Send email",
  "slug": "send_email",
  "description": "",
  "data": {
    "subject": {
      "type": 5,
      "value": "Tieu de email: $userTask.Root.submittedBy.first_last_name"
    },
    "content": {
      "type": "text/html",
      "content": {
        "valuePathName": "workflow_resource:list.variable / Biến string",
        "valueDataType": "TEXT",
        "type": 5,
        "value": "<div>Đây là nội dung chứa biến:&nbsp;$userTask.Root.submittedBy.first_last_name</div>"
      }
    },
    "from": {
      "isRaw": true,
      "fromType": "WORKSPACE_EMAIL",
      "personnel": null,
      "emailId": "KWVWQEKLSHD"
    },
    "to": [
      {
        "email": {
          "type": 1,
          "value": "recipient@example.com"
        }
      },
      {
        "email": {
          "type": 1,
          "value": "recipient2@example.com"
        }
      },
      {
        "email": {
          "type": 4,
          "value": "$flow.bien_string",
          "dataType": "TEXT",
          "dataPathName": "workflow_resource:list.variable / Biến string"
        },
        "name": {
          "type": 4,
          "value": "$flow.bien_string"
        }
      },
      {
        "email": {
          "type": 4,
          "value": "$flow.text_template",
          "dataType": "TEXT",
          "dataPathName": "workflow_resource:list.textTemplate / Text template"
        },
        "name": {
          "type": 4,
          "value": "$flow.text_template"
        }
      }
    ],
    "cc": [],
    "bcc": [],
    "replyTo": [],
    "attachments": [],
    "emailAppendSignature": false
  }
}
```

### Sử dụng Text Template trong email

Khi sử dụng Text Template cho content (type=2), cần:
1. Tạo Text Template trong `resources.custom` (xem section Text Template)
2. Thêm `resourcesUsedIn` vào Text Template trỏ đến action email
3. Thêm `resourcesUsedIn` vào các resource được sử dụng trong Text Template
4. Thêm `externalResourcesUsedIn` ở root level nếu dùng trường con của lookup

---
