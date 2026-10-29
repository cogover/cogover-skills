# Record Email — API contract

Contract đã kiểm chứng trên Workspace thật (gửi tới Liên hệ và Lead, App Sales). ID dưới đây là ví dụ.

## Đọc dữ liệu (`/bapi/v1/records/list`, API Key)

| Object slug | Dùng cho | Field chính |
|---|---|---|
| `email_template` | Mẫu email | `name`, `subject`, `content` (HTML, có thể chứa `{$record.<field>}`), `related_object` (mảng slug Object) |
| `email_layout` | Bố cục email | `name`, `content` (HTML, chèn nội dung mẫu tại `{$currentContent}`) |
| `email_message` | Email đã gửi/nhận | `name` (tiêu đề), `from` (chuỗi JSON `{"id","type","email","name"}`), `to_meta` (chuỗi JSON `[{"recordId","objectTypeSlug","value":[...]}]`), `template` (ID mẫu, rỗng nếu không gửi theo mẫu), `send_status` (`sent`, `error`, trống khi đang chờ), `number_opened`, `body` |

- Hộp thư dùng chung: phần tử `from` có `type: "workspace"`; `id` của nó là giá trị gửi vào `data.from.id`. Lọc `{"field":"from","op":"like","params":"\"type\":\"workspace\"","fieldType":"long_text"}`. Workspace không có endpoint liệt kê hộp thư cho API Key, nên danh sách chỉ gồm hộp thư đã gửi ít nhất một email.
- Email đã gửi theo một mẫu cho một bản ghi: lọc `template` `=` `<ID mẫu>` (`short_text`) **và** `to_meta` `like` `<ID bản ghi>` (`long_text`).

## Gửi (`POST /api/v1/dashboard-server`, phiên Web App)

Header: cookie phiên + `x-csrf-token`/`x-xsrf-token` theo [$cogover-api-auth](../../cogover-api-auth/SKILL.md), thêm `x-req-service: 7`, `x-req-type: 9`, `x-app-slug: <slug App của trang bản ghi>` (`sales` cho Liên hệ/Lead).

```json
{
  "recordId": "ATVEXAMPLE0001",
  "objectTypeSlug": "contact",
  "type": "email",
  "clientTimeZone": "Asia/Saigon",
  "data": {
    "subject": "Tiêu đề đã render",
    "from": { "id": "EWXXXXXXXXXXXX", "type": "workspace" },
    "contentType": "rich_text_editor",
    "content": "<HTML đã render đầy đủ>",
    "sendEmail": true,
    "to": [{ "recordId": "ATVEXAMPLE0001", "objectTypeSlug": "contact", "value": ["customer@example.com"] }],
    "cc": [],
    "bcc": [],
    "template": "QRXXXXXXXXXXXX",
    "emailLayout": "FXXXXXXXXXXXXX",
    "files": null,
    "relatedObjectRecords": [{ "fieldSlug": "contacts", "recordIds": ["ATVEXAMPLE0001"] }],
    "time": null,
    "sendReminder": null,
    "_attachments": null
  }
}
```

- `content` là HTML **cuối cùng**: server không tự ghép mẫu, bố cục hay chữ ký. Thứ tự giống giao diện: `layout.content` thay `{$currentContent}` bằng `template.content`, rồi nối HTML chữ ký phía sau. Biến `{$record.*}` phải được thay trước khi gửi.
- `template`, `emailLayout` chỉ để ghi nhận (lọc `email_message` theo mẫu); không có bố cục thì gửi `null`.
- `relatedObjectRecords[].fieldSlug`: `contacts` cho Liên hệ, `lead` cho Lead. Giao diện gửi thêm các phần tử `recordIds: []` cho những quan hệ khác của bản ghi; bỏ đi vẫn gửi đúng.
- `type: "workspace"` là hộp thư dùng chung. Hộp thư cá nhân của nhân sự chưa kiểm chứng qua contract này.
- Thành công: HTTP `200`, `r: 0`. Server tạo một `activity` (`activity_type: email`, `source_object`/`source_record` là bản ghi nhận) và một `email_message`; `send_status` chuyển `sent` sau vài giây đến khoảng một phút.
- `cc`/`bcc` cùng cấu trúc với `to`. File đính kèm (`files`, `_attachments`) chưa kiểm chứng: đặt link tải trong nội dung.
