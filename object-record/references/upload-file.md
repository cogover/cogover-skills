# Upload và gắn file vào bản ghi Cogover bằng API

Tài liệu này áp dụng cho field `file` thông thường. Khi cần chèn ảnh local vào nội dung của field `long_text` bật WYSIWYG, dùng quy trình `_attachments` tại [wysiwyg-long-text-images.md](wysiwyg-long-text-images.md).

## 1. Upload file lên file-server

Gọi `POST`:

```bash
curl --silent --show-error \
  --url 'https://{{WORKSPACE_DOMAIN}}/api/v1/file/upload/v2/client_upload' \
  -H 'x-csrf-token: {{XSRF_TOKEN}}' \
  -H 'x-xsrf-token: {{XSRF_TOKEN}}' \
  -b 'AuthToken={{AUTH_TOKEN}}; HttpSessionId={{HTTP_SESSION_ID}}; XSRF-TOKEN={{XSRF_TOKEN}}' \
  -F 'field_slug={{FILE_FIELD_SLUG}}' \
  -F 'object_slug={{OBJECT_SLUG}}' \
  -F 'file=@{{ABSOLUTE_FILE_PATH}}' \
  --write-out '\nHTTP_STATUS:%{http_code}\n'
```

Chỉ tiếp tục khi HTTP thuộc `2xx` và response có `r: 0`. Lưu nguyên object `data` trả về; đây là `FILE_METADATA`. Upload riêng cho từng field đích, kể cả khi các field dùng cùng một file.

## 2. Tạo record mới kèm file trong cùng request

Sau khi mọi upload thành công, gọi đúng một lần `POST /bapi/v1/records` bằng `Authorization: Bearer {{API_KEY}}`:

```json
{
  "object_slug": "{{OBJECT_SLUG}}",
  "data": {
    "{{REQUIRED_FIELD_SLUG}}": "{{VALUE}}",
    "{{SINGLE_FILE_FIELD_SLUG}}": {{SINGLE_FILE_METADATA}},
    "{{MULTIPLE_FILE_FIELD_SLUG}}": [{{MULTIPLE_FILE_METADATA}}]
  },
  "client_time_zone": "Asia/Saigon"
}
```

- Gửi object metadata trực tiếp cho field đơn và mảng metadata cho field đa.
- Gửi các field thường, field bắt buộc và mọi field file trong cùng request create.
- Chỉ thành công khi HTTP thuộc `2xx`, response có `r: 0` và `data.id` chứa ID record mới.
- Khi thành công, không gọi thêm `POST /api/v1/records`; đọc lại record để xác minh file đã lưu.
- Nếu create thất bại sau upload, file có thể bị mồ côi. Báo file ID và không retry create mù quáng.

## 3. Gắn file vào bản ghi đã tồn tại

Gọi `POST` đến:

```text
https://{{WORKSPACE_DOMAIN}}/api/v1/records
```

Headers/cookie:

```text
content-type: application/json
x-csrf-token: {{XSRF_TOKEN}}
x-xsrf-token: {{XSRF_TOKEN}}
x-req-service: 10201
x-req-type: 1
Cookie: AuthToken={{AUTH_TOKEN}}; HttpSessionId={{HTTP_SESSION_ID}}; XSRF-TOKEN={{XSRF_TOKEN}}
```

JSON body cho field đơn giá trị (`FILE_FIELD_MULTIPLE=false`):

```json
{
  "workspace_id": "{{WORKSPACE_ID}}",
  "object_type": "{{OBJECT_TYPE_ID}}",
  "data": {
    "{{FILE_FIELD_SLUG}}": {{FILE_METADATA}},
    "object_type": "{{OBJECT_TYPE_ID}}",
    "workspace_id": "{{WORKSPACE_ID}}",
    "id": "{{RECORD_ID}}"
  },
  "client_time_zone": "Asia/Saigon"
}
```

Với field đa giá trị (`FILE_FIELD_MULTIPLE=true`), chỉ đổi giá trị field thành mảng:

```json
"{{FILE_FIELD_SLUG}}": [{{FILE_METADATA}}]
```

Không dùng mảng cho field đơn giá trị; backend có thể trả `r: 626` (`not found file id`).

Thành công khi HTTP thuộc `2xx` và response có `r: 0` (có thể nằm trong `body.r`). Báo lại tên file, Object/field slug đã dùng, ID bản ghi và kết quả của hai bước.

## Xác thực

Endpoint upload và endpoint gắn vào record đã tồn tại dùng phiên Web App, không dùng API key trực tiếp. Endpoint tạo record `/bapi/v1/records` dùng API Key Bearer. Dùng `$cogover-api-auth` để tạo phiên hợp lệ trước khi upload; nếu không thể tạo phiên, dừng và báo người dùng.
