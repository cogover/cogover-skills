## Send Notification Task (Task Gửi Thông báo)

### Mô tả
Send Notification Task là một task hệ thống tự động gửi thông báo (notification) đến người dùng trong workspace khi luồng chạy đến. Thông báo sẽ hiển thị trong hệ thống notification của ứng dụng.

### Cấu trúc trong BPMN XML
```xml
<elEx:sendNotificationTask id="{NOTIFICATION_TASK_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="SEND_NOTIFICATION_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:sendNotificationTask>
```

**Lưu ý quan trọng:**
- Sử dụng `elEx:sendNotificationTask` (KHÔNG phải `bpmn2:userTask` hay `bpmn2:sendTask`)
- Cần thêm namespace: `xmlns:elEx="http://element-ex/schema"` vào `bpmn2:definitions`
- `renderKey="SEND_NOTIFICATION_TASK"`

### Cấu trúc `actions` trong JSON
Thêm vào mảng `actions` ở root level:
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
        "title": {
          "type": 1,
          "value": "Tiêu đề thông báo"
        },
        "subTitle": {
          "type": 1,
          "value": ""
        },
        "content": {
          "type": "text/html",
          "content": {
            "type": 1,
            "value": "<div>Nội dung thông báo</div>"
          }
        },
        "from": {
          "fromType": "WORKSPACE_NOTIFICATION",
          "isRaw": true,
          "personnel": null
        },
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
        "redirectToPage": {
          "type": 1,
          "value": ""
        },
        "notificationChannel": "{NOTIFICATION_CHANNEL_ID}"
      }
    }
  ]
}
```

### Hệ thống Type cho giá trị

Tương tự như Send Email Task, các trường trong notification sử dụng hệ thống type:

| Type | Mô tả                                                   | Áp dụng cho                                |
|------|---------------------------------------------------------|--------------------------------------------|
| `1`  | Nhập trực tiếp (raw) - text thuần, không chứa biến      | title, subTitle, content, to (Personnel ID) |
| `2`  | Giá trị từ Text Template                                | content                                    |
| `3`  | Giá trị từ Scripting (Formula)                          | content                                    |
| `4`  | Giá trị từ biến hoặc resource                           | title, subTitle, content, to               |
| `5`  | Nhập trực tiếp có chứa biến bên trong (Simple Renderer) | title, subTitle, content                   |

**Lưu ý về type=5 (Simple Renderer):**
- Hệ thống sử dụng Simple Renderer để render text, chỉ hỗ trợ render các biến
- KHÔNG hỗ trợ render if/else, for,... như Text Template
- Cú pháp biến: `$userTask.Root.submittedBy.id` (KHÔNG bọc xung quanh `{{}}` hay `{}`)

### Chi tiết các trường cấu hình thông báo

#### 1. Title (Tiêu đề)

**Cách 1: Nhập trực tiếp, text thuần không chứa biến (type=1)**
```json
{
  "title": {
    "type": 1,
    "value": "Tieu de thong bao"
  }
}
```

**Cách 2: Lấy giá trị từ biến/resource khác (type=4)**
```json
{
  "title": {
    "type": 4,
    "value": "$flow.bien_string",
    "valueDataType": "TEXT",
    "valuePathName": "workflow_resource:list.variable / Biến string"
  }
}
```
- `valuePathName` = tên hiển thị đường dẫn
- `valueDataType` = `"TEXT"`

**Cách 3: Nhập trực tiếp có chứa biến bên trong (type=5 - Simple Renderer)**
```json
{
  "title": {
    "type": 5,
    "value": "Tieu de thong bao: $userTask.Root.submittedBy.id"
  }
}
```
- Sử dụng Simple Renderer, chỉ hỗ trợ render biến (không hỗ trợ if/else, for,... như Text Template)
- Cú pháp biến: `$userTask.Root.submittedBy.id` (KHÔNG bọc `{{}}` hay `{}`)

#### 2. Sub Title (Tiêu đề phụ)

Trường `subTitle` chỉ hiển thị khi `displayType = "FULL"`. Cấu trúc giống hệt trường `title`.

**Cách 1: Nhập trực tiếp, text thuần không chứa biến (type=1)**
```json
{
  "subTitle": {
    "type": 1,
    "value": "Tieu de phu"
  }
}
```

**Cách 2: Lấy giá trị từ biến/resource khác (type=4)**
```json
{
  "subTitle": {
    "type": 4,
    "value": "$flow.bien_string",
    "valueDataType": "TEXT",
    "valuePathName": "workflow_resource:list.variable / Biến string"
  }
}
```

**Cách 3: Nhập trực tiếp có chứa biến bên trong (type=5 - Simple Renderer)**
```json
{
  "subTitle": {
    "type": 5,
    "value": "Tieu de phu: $userTask.Root.submittedBy.id"
  }
}
```

#### 3. Content (Nội dung)

Trường content có wrapper bên ngoài với `"type"` là `"text/html"` hoặc `"text/plain"`. Bên trong là object `content` chứa giá trị thực tế.

**Cách 1: Nội dung nhập trực tiếp, text thuần không chứa biến (type=1)**
```json
{
  "content": {
    "type": "text/html",
    "content": {
      "type": 1,
      "value": "<div>Nội dung thông báo dạng HTML</div>"
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
- `content.valuePathName` = tên hiển thị
- `content.valueDataType` = `"TEXT"`

**Cách 3: Nội dung từ Scripting/Formula (type=3)**
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
- `content.value` = đường dẫn đến biến Formula

**Cách 4: Nội dung nhập trực tiếp có chứa biến bên trong (type=5 - Simple Renderer)**
```json
{
  "content": {
    "type": "text/html",
    "content": {
      "type": 5,
      "value": "<div>Noi dung:&nbsp;$userTask.Root.submittedBy.id</div>"
    }
  }
}
```
- Sử dụng Simple Renderer, chỉ hỗ trợ render biến (KHÔNG hỗ trợ if/else, for,... như Text Template)
- Cú pháp biến: `$userTask.Root.submittedBy.id` (KHÔNG bọc `{{}}` hay `{}`)

**Cách 5: Nội dung dạng plain text (type=1, format text/plain)**
```json
{
  "content": {
    "type": "text/plain",
    "content": {
      "type": 1,
      "value": "Nội dung thông báo dạng text thuần"
    }
  }
}
```
- `content.type` bên ngoài = `"text/plain"` thay vì `"text/html"`

#### 4. From (Nguồn gửi)

**Cách 1: Gửi từ hệ thống Workspace (Cogover)**
```json
{
  "from": {
    "isRaw": true,
    "fromType": "WORKSPACE_NOTIFICATION",
    "personnel": null
  }
}
```
- `fromType: "WORKSPACE_NOTIFICATION"` = sử dụng notification của workspace (Cogover system)

**Cách 2: Gửi từ một Personnel cụ thể (nhập trực tiếp Personnel ID)**
```json
{
  "from": {
    "isRaw": true,
    "fromType": "PERSONNEL_NOTIFICATION",
    "personnel": "PER_SAMPLE_USER"
  }
}
```
- `fromType: "PERSONNEL_NOTIFICATION"` = gửi từ một personnel cụ thể
- `personnel` = Personnel ID của người gửi
- `isRaw: true` vì nhập trực tiếp Personnel ID

**Cách 3: Gửi từ Personnel lấy từ biến/resource**
```json
{
  "from": {
    "isRaw": false,
    "fromType": "PERSONNEL_NOTIFICATION",
    "personnel": "$userTask.Root.submittedBy"
  }
}
```
- `fromType: "PERSONNEL_NOTIFICATION"` = gửi từ một personnel
- `personnel` = đường dẫn biến trỏ đến personnel
- `isRaw: false` vì giá trị lấy từ biến (không phải nhập trực tiếp)

#### 5. To (Người nhận)

Mảng các người nhận. Khác với Send Email, trường `to` của notification sử dụng Personnel ID trực tiếp.

**Cách 1: Nhập trực tiếp Personnel ID (type=1)**
```json
{
  "to": [
    {
      "type": 1,
      "value": "PER_SAMPLE_USER"
    }
  ]
}
```
- `value` = Personnel ID của người nhận

**Nhiều người nhận nhập trực tiếp:**
```json
{
  "to": [
    {
      "type": 1,
      "value": "PER_SAMPLE_USER"
    },
    {
      "type": 1,
      "value": "PER00000000001"
    }
  ]
}
```

**Cách 2: Lấy từ biến personnel/user (type=4)**
```json
{
  "to": [
    {
      "type": 4,
      "value": "$userTask.Root.submittedBy",
      "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
      "valueDataType": "RECORD"
    }
  ]
}
```
- `value` = đường dẫn biến (ví dụ: `$userTask.Root.submittedBy`)
- `valuePathName` = tên hiển thị của đường dẫn
- `valueDataType: "RECORD"` = kiểu dữ liệu record (personnel)

#### 6. Exclude (Loại trừ)
```json
{
  "exclude": []
}
```
Danh sách người bị loại trừ không nhận thông báo. Cấu trúc mỗi phần tử giống hệt `to`.

#### 7. Display Type
```json
{
  "displayType": "SIMPLE"
}
```
- `"SIMPLE"` = hiển thị thông báo đơn giản (không có subTitle)
- `"FULL"` = hiển thị thông báo đầy đủ (có thêm trường `subTitle`)

#### 8. Redirect (Chuyển hướng)
```json
{
  "redirectType": "ROUTING",
  "redirectToPage": {
    "type": 1,
    "value": ""
  }
}
```
- `redirectType`: có 2 giá trị:
  - `"ROUTING"` = chuyển hướng theo routing mặc định (điều hướng trong app)
  - `"NEW_TAB"` = mở trang mới trong tab mới của trình duyệt
- `redirectToPage` = URL trang chuyển hướng khi click thông báo

#### 9. Notification Channel
```json
{
  "notificationChannel": "{NOTIFICATION_CHANNEL_ID}"
}
```
- ID của kênh thông báo đã cấu hình trong workspace.
- **Cách lấy `{NOTIFICATION_CHANNEL_ID}`:** Gọi skill `/object-record`, yêu cầu lấy danh sách bản ghi của đối tượng có `object_slug=notification_channel`. API thường trả về 2 bản ghi:
  - `name="All"`: Kênh thông báo qua **email, web push, in-app**
  - `name="In App"`: Kênh thông báo chỉ qua **in-app**
- Lấy `id` của bản ghi phù hợp với lựa chọn của người dùng làm giá trị cho `notificationChannel`.
- **Nếu người dùng không chỉ định kênh thông báo**, mặc định chọn bản ghi có `name="All"`.

### Resources của Send Notification Action

Send Notification action tạo ra các resources có thể sử dụng trong các bước sau:

```json
{
  "resources": {
    "actions": [
      {
        "id": "{ACTION_ID}",
        "type": "SEND_NOTIFICATION",
        "name": "Send notification",
        "slug": "send_notification",
        "nodeId": "{NOTIFICATION_TASK_NODE_ID}",
        "resources": [
          {
            "absoluteSlug": "$action.send_notification.startAt",
            "dataType": "DATE_TIME",
            "name": "Start At",
            "slug": "startAt"
          },
          {
            "absoluteSlug": "$action.send_notification.endAt",
            "dataType": "DATE_TIME",
            "name": "End At",
            "slug": "endAt"
          },
          {
            "absoluteSlug": "$action.send_notification.output",
            "dataType": "NUMBER",
            "name": "Output",
            "slug": "output"
          }
        ]
      }
    ]
  }
}
```

### Ví dụ đầy đủ

#### Ví dụ 1: Title và content nhập trực tiếp có chứa biến (type=5 - Simple Renderer)

- **displayType**: `"SIMPLE"` (không có subTitle)
- **title**: nhập trực tiếp có chứa biến (type=5)
- **content**: nhập trực tiếp có chứa biến (type=5), format `text/html`
- **from**: gửi từ Workspace (Cogover system)
- **to**: nhiều personnel nhập trực tiếp (type=1)

```json
{
  "data": {
    "displayType": "SIMPLE",
    "from": {
      "isRaw": true,
      "fromType": "WORKSPACE_NOTIFICATION",
      "personnel": null
    },
    "exclude": [],
    "to": [
      {
        "type": 1,
        "value": "PER_SAMPLE_USER"
      },
      {
        "type": 1,
        "value": "PER00000000001"
      }
    ],
    "redirectType": "ROUTING",
    "title": {
      "type": 5,
      "value": "Tieu de thong bao: $userTask.Root.submittedBy.id"
    },
    "subTitle": {
      "type": 1,
      "value": ""
    },
    "notificationChannel": "NO000000000122",
    "redirectToPage": {
      "type": 1,
      "value": ""
    },
    "content": {
      "type": "text/html",
      "content": {
        "type": 5,
        "value": "<div>Noi dung:&nbsp;$userTask.Root.submittedBy.id</div>"
      }
    }
  },
  "processId": "PE00000000002",
  "name": "thong bao",
  "description": "",
  "id": "ACDWWSQEFKWQK",
  "type": "SEND_NOTIFICATION",
  "nodeId": "NO00000000075",
  "slug": "thong_bao"
}
```

#### Ví dụ 2: Title từ biến (type=4), content từ Text Template (type=2)

- **title**: lấy giá trị từ biến/resource (type=4)
- **content**: lấy giá trị từ Text Template (type=2)

```json
{
  "data": {
    "displayType": "SIMPLE",
    "from": {
      "isRaw": true,
      "fromType": "WORKSPACE_NOTIFICATION",
      "personnel": null
    },
    "exclude": [],
    "to": [
      {
        "type": 1,
        "value": "PER_SAMPLE_USER"
      },
      {
        "type": 1,
        "value": "PER00000000001"
      }
    ],
    "redirectType": "ROUTING",
    "title": {
      "valuePathName": "workflow_resource:list.variable / Biến string",
      "valueDataType": "TEXT",
      "type": 4,
      "value": "$flow.bien_string"
    },
    "subTitle": {
      "type": 1,
      "value": ""
    },
    "notificationChannel": "NO000000000122",
    "redirectToPage": {
      "type": 1,
      "value": ""
    },
    "content": {
      "type": "text/html",
      "content": {
        "valuePathName": "workflow_resource:list.textTemplate / Text template",
        "valueDataType": "TEXT",
        "type": 2,
        "value": "$flow.text_template"
      }
    }
  },
  "processId": "PE00000000002",
  "name": "thong bao",
  "description": "",
  "id": "AC00000000005",
  "type": "SEND_NOTIFICATION",
  "nodeId": "NO00000000009",
  "slug": "thong_bao"
}
```

#### Ví dụ 3: DisplayType FULL với subTitle, from Personnel, content Scripting (type=3), redirect NEW_TAB

- **displayType**: `"FULL"` (có subTitle)
- **subTitle**: nhập trực tiếp (type=1)
- **from**: gửi từ Personnel cụ thể
- **content**: lấy từ Scripting/Formula (type=3)
- **redirectType**: `"NEW_TAB"`
- **to**: lấy từ biến (type=4)

```json
{
  "data": {
    "displayType": "FULL",
    "from": {
      "isRaw": true,
      "fromType": "PERSONNEL_NOTIFICATION",
      "personnel": "PER_SAMPLE_USER"
    },
    "exclude": [],
    "to": [
      {
        "type": 4,
        "value": "$userTask.Root.submittedBy",
        "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
        "valueDataType": "RECORD"
      }
    ],
    "redirectType": "NEW_TAB",
    "title": {
      "type": 1,
      "value": "Thong bao moi"
    },
    "subTitle": {
      "type": 1,
      "value": "Chi tiet thong bao"
    },
    "notificationChannel": "NO000000000122",
    "redirectToPage": {
      "type": 1,
      "value": "https://example.com/detail"
    },
    "content": {
      "type": "text/html",
      "content": {
        "type": 3,
        "value": "$flow.bien_formula"
      }
    }
  },
  "processId": "PE00000000002",
  "name": "thong bao day du",
  "description": "",
  "id": "AC00000000009",
  "type": "SEND_NOTIFICATION",
  "nodeId": "NO00000000010",
  "slug": "thong_bao_day_du"
}
```

### Cập nhật resourcesUsedIn

Khi một resource được sử dụng trong Send Notification (ví dụ: `$userTask.Root.submittedBy`), cần thêm `resourcesUsedIn` vào resource đó:

```json
{
  "resourcesUsedIn": [
    {
      "actionType": "SEND_NOTIFICATION",
      "name": "Send notification",
      "count": 1,
      "id": "{ACTION_ID}",
      "parentTable": "action",
      "slug": "send_notification"
    }
  ]
}
```

---

