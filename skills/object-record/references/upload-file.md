# Upload và gắn file vào bản ghi Cogover bằng API

Áp dụng cho field `file` thông thường; ảnh local trong field `long_text` bật WYSIWYG dùng quy trình `_attachments` tại [wysiwyg-long-text-images.md](wysiwyg-long-text-images.md).

Upload (mục 1) và gắn vào record đã tồn tại (mục 3) là endpoint `/api/v1`: dùng phiên Web App tạo qua `$cogover-api-auth`, không dùng API Key trực tiếp; không tạo được phiên thì dừng và báo người dùng. Tạo record `/bapi/v1/records` (mục 2) dùng API Key Bearer.

## 1. Upload file lên file-server

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

Chỉ tiếp tục khi HTTP `2xx`, `r: 0` và có object `data`; lưu nguyên `data` làm `FILE_METADATA`. Upload riêng cho từng field đích — mỗi field một request với `field_slug` của nó và một `FILE_METADATA` riêng — kể cả khi các field dùng cùng một file; không tái sử dụng metadata cho field khác.

## 2. Tạo record mới kèm file trong cùng request

Sau khi mọi upload thành công, gọi đúng một lần `POST /bapi/v1/records` (API Key Bearer), gửi field thường, field bắt buộc và mọi field file trong cùng body:

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

- Field đơn nhận object metadata, field đa nhận mảng metadata.
- Thành công khi HTTP `2xx`, `r: 0` và `data.id` chứa ID record mới. Sau đó không gọi thêm `POST /api/v1/records`; đọc lại record để xác minh file đã lưu.
- Create thất bại sau upload: file đã upload có thể bị mồ côi; báo file ID và không retry create mù quáng.

## 3. Gắn file vào bản ghi đã tồn tại

`POST https://{{WORKSPACE_DOMAIN}}/api/v1/records` với header/cookie:

```text
content-type: application/json
x-csrf-token: {{XSRF_TOKEN}}
x-xsrf-token: {{XSRF_TOKEN}}
x-req-service: 10201
x-req-type: 1
Cookie: AuthToken={{AUTH_TOKEN}}; HttpSessionId={{HTTP_SESSION_ID}}; XSRF-TOKEN={{XSRF_TOKEN}}
```

Body cho field đơn giá trị (`multiple=false`):

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

- Field đa giá trị (`multiple=true`): giá trị field là mảng `[{{FILE_METADATA}}]`; khi thêm file mà không thay file cũ, đọc giá trị hiện tại và nối metadata mới vào mảng trước khi gửi. Không dùng mảng cho field đơn giá trị: backend có thể trả `r: 626` (`not found file id`).
- Có thể gắn nhiều field trong cùng body sau khi mọi upload đều thành công.
- Thành công khi HTTP `2xx` và `r: 0` (có thể nằm trong `body.r`). Báo tên file, Object/field slug đã dùng, ID bản ghi và kết quả của hai bước.
- Không retry mù quáng upload hoặc gắn file khi timeout/mất kết nối vì thao tác ghi có thể đã xảy ra; báo trạng thái chưa xác định.
