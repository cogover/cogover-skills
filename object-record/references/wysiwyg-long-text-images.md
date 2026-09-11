# Tạo record có ảnh local trong long-text WYSIWYG

## 1. Điều kiện và metadata cần lấy

Dùng `$object-info` để lấy và xác minh:

- `WORKSPACE_ID` và `OBJECT_TYPE_ID` của Object.
- `LONG_TEXT_FIELD_ID` và `LONG_TEXT_FIELD_SLUG` của field `long_text` bật rich text/WYSIWYG (`text_type = 2`).
- `ATTACHMENTS_FIELD_ID` của field `file` hệ thống có slug `_attachments`. Object có ít nhất một field `long_text` bật WYSIWYG sẽ có field này; không suy đoán ID từ ví dụ hoặc tên hiển thị. Không tìm thấy `_attachments` thì dừng trước khi upload và báo người dùng.

Ảnh local phải tồn tại, không rỗng và dùng đường dẫn tuyệt đối. Nhiều ảnh: lặp bước upload cho từng ảnh và giữ từng object metadata riêng.

## 2. Tạo phiên Web App

Endpoint upload thuộc `/api/v1`: đổi API Key thành phiên qua `$cogover-api-auth` (`POST /bapi/v1/auth-token`) và chỉ tiếp tục khi có đủ `AuthToken`, `HttpSessionId`, `XSRF-TOKEN`. Không tạo được phiên hợp lệ thì dừng và báo người dùng; không gọi upload chỉ với API Key. Không gửi các cookie `deviceId`, `workspace_openning_ids` hoặc `app_ids_by_position`.

## 3. Upload ảnh tạm

Upload vào field `_attachments` theo **field ID** và **Object ID** (khác upload file thường dùng `field_slug`/`object_slug`):

```bash
curl --silent --show-error \
  --url 'https://{WORKSPACE_DOMAIN}/api/v1/file/upload/v2/client_upload' \
  --header 'x-csrf-token: {XSRF_TOKEN}' \
  --header 'x-xsrf-token: {XSRF_TOKEN}' \
  --cookie 'AuthToken={AUTH_TOKEN}; HttpSessionId={HTTP_SESSION_ID}; XSRF-TOKEN={XSRF_TOKEN}' \
  --form 'file=@{ABSOLUTE_FILE_PATH}' \
  --form 'field_id={ATTACHMENTS_FIELD_ID}' \
  --form 'object_id={OBJECT_TYPE_ID}' \
  --write-out '\nHTTP_STATUS:%{http_code}\n'
```

Để `curl --form` tự tạo `Content-Type: multipart/form-data` và boundary; không chép raw binary vào `--data-raw` và không tự đặt boundary.

Chỉ tiếp tục khi HTTP `2xx`, `r: 0` và `data` là object. Lưu nguyên `data` làm `IMAGE_METADATA`, ví dụ:

```json
{
  "fileName": "image.png",
  "fileSize": 2520608,
  "resizable": true,
  "file_id": "asia-1_1Y_LM2AQEKMXP",
  "resolutionSizes": ["original", "tiny", "small", "medium", "large"],
  "acl": "private",
  "fileExt": "png",
  "fileServerUrlTemplate": "//asia-1{FILE_SERVER_SUFFIX_PUBLIC_URL}/{SHORT_LIVED_TOKEN}/asia-1_1Y_LM2AQEKMXP/image.png",
  "fileType": "object_field",
  "url": "https://{WORKSPACE_DOMAIN}/files/{file_id}/{resolution_size}/image.png?redirect=true"
}
```

## 4. Dựng metadata và HTML

Thêm query parameter `long_text_field_id={LONG_TEXT_FIELD_ID}` vào `IMAGE_METADATA.url` dùng trong `_attachments`; URL đã có `?redirect=true` thì nối bằng `&`:

```text
https://{WORKSPACE_DOMAIN}/files/%7Bfile_id%7D/%7Bresolution_size%7D/image.png?redirect=true&long_text_field_id={LONG_TEXT_FIELD_ID}
```

Giữ nguyên mọi key metadata khác từ response. Không thay placeholder trong metadata bằng file ID cụ thể nếu response trả URL dạng template.

Trong HTML của field WYSIWYG, dùng URL ảnh cụ thể với `file_id`, resolution và cùng `long_text_field_id`; kích thước theo yêu cầu thực tế:

```html
<div>
  Nội dung trước ảnh:<br />
  <br />
  <img src="https://{WORKSPACE_DOMAIN}/files/{FILE_ID}/original/image.png?redirect=true&amp;long_text_field_id={LONG_TEXT_FIELD_ID}" style="width: 600px; height: 307px;" />
</div>
```

Nhiều ảnh: đưa toàn bộ metadata vào `_attachments` và tạo một thẻ `<img>` tương ứng cho từng ảnh.

## 5. Tạo record qua BAPI

Gọi đúng một lần `POST /bapi/v1/records` bằng API Key Bearer: metadata ảnh vào `_attachments`, field long-text là object có `text_type: 2`, kèm mọi field bắt buộc của Object trong cùng request:

```json
{
  "workspace_id": "{WORKSPACE_ID}",
  "object_type": "{OBJECT_TYPE_ID}",
  "data": {
    "{REQUIRED_FIELD_SLUG}": "{REQUIRED_VALUE}",
    "_attachments": [
      {IMAGE_METADATA_WITH_LONG_TEXT_FIELD_ID_IN_URL}
    ],
    "{LONG_TEXT_FIELD_SLUG}": {
      "value": "<div>Nội dung trước ảnh:<br /><br /><img src=\"https://{WORKSPACE_DOMAIN}/files/{FILE_ID}/original/image.png?redirect=true&amp;long_text_field_id={LONG_TEXT_FIELD_ID}\" style=\"width: 600px; height: 307px;\" /></div>",
      "text_type": 2
    },
    "object_type": "{OBJECT_TYPE_ID}",
    "workspace_id": "{WORKSPACE_ID}"
  },
  "client_time_zone": "Asia/Saigon"
}
```

`{IMAGE_METADATA_WITH_LONG_TEXT_FIELD_ID_IN_URL}` là JSON object thật từ bước upload (đã thêm `long_text_field_id` vào `url`), không phải chuỗi có dấu ngoặc kép bao quanh.

## 6. Kiểm tra kết quả và xử lý lỗi

Coi create thành công khi HTTP `2xx`, `r: 0` và `data.id` chứa record ID. Đọc lại record để xác minh:

- Field WYSIWYG có `text_type = 2` và HTML mong muốn.
- `_attachments` chứa đúng `file_id` vừa upload.
- URL ảnh có `long_text_field_id` bằng ID của chính field WYSIWYG.

Không retry mù quáng request upload hoặc create khi timeout/mất kết nối vì thao tác ghi có thể đã xảy ra. Create thất bại sau upload: báo `file_id` có thể bị mồ côi. Không gọi thêm `/api/v1/records` sau khi `/bapi/v1/records` đã tạo record thành công.
