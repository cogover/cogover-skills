# Upload icon/ảnh vào thư viện của Workspace

Tài liệu bao gồm API đọc danh sách icon hiện có và quy trình hai bước để upload file lên file-server rồi thêm metadata vào thư viện icon/ảnh của Workspace.

## Mục lục

- [Đọc danh sách icon trong thư viện](#đọc-danh-sách-icon-trong-thư-viện)
- [Chuẩn bị upload](#chuẩn-bị-upload)
- [Bước 1: Upload file lên file-server](#bước-1-upload-file-lên-file-server)
- [Bước 2: Thêm icon hoặc ảnh vào thư viện](#bước-2-thêm-icon-hoặc-ảnh-vào-thư-viện)
- [Lưu ý](#lưu-ý)

> Các endpoint dưới đây dùng phiên Web App, không dùng API Key trực tiếp. Dùng `$cogover-api-auth` để lấy `AUTH_TOKEN`, `HTTP_SESSION_ID` và `XSRF_TOKEN`. Nếu không tạo được phiên hợp lệ, dừng và báo người dùng.

## Đọc danh sách icon trong thư viện

Gọi `GET /api/v1/objects/icon` bằng đủ ba cookie phiên và hai header CSRF/XSRF:

```bash
ICON_LIBRARY_RESPONSE=$(curl --silent --show-error --fail-with-body \
  --url "https://${WORKSPACE_DOMAIN}/api/v1/objects/icon" \
  -H 'accept: application/json, text/plain, */*' \
  -H "x-csrf-token: ${XSRF_TOKEN}" \
  -H "x-xsrf-token: ${XSRF_TOKEN}" \
  -b "AuthToken=${AUTH_TOKEN}; HttpSessionId=${HTTP_SESSION_ID}; XSRF-TOKEN=${XSRF_TOKEN}")
```

Response đã xác minh có dạng:

```json
{
  "r": 0,
  "msg": "OK",
  "data": [
    {
      "id": "{library-item-id}",
      "workspaceId": "{workspace-id}",
      "name": "finance_menu_income_receivables",
      "data": "https://{workspace-domain}/files/{file-id}/original/finance_income_receivables.svg?redirect=true",
      "created": 1780000000000,
      "updated": 1780000001000,
      "createdBy": "{personnel-id}",
      "updatedBy": "{personnel-id}"
    }
  ],
  "meta": null,
  "tags": []
}
```

Chỉ tiếp tục khi HTTP thành công, `r: 0` và `data` là mảng. Với từng phần tử list:

- `id`: ID bản ghi thư viện, thường có dạng `CON...`; dùng để nhận diện/resolve item.
- `name`: tên library item.
- `data`: URL file icon; dùng giá trị này khi cài icon vào Button hoặc App Menu.
- `workspaceId`, timestamps và creator/updater: metadata server-managed, không gửi lại khi cài icon.

Không nhầm hai response shape:

- `GET /api/v1/objects/icon`: URL icon nằm ở `data[].data`.
- `POST /api/v1/objects/icon/add-multiple`: URL icon nằm ở `data[].id`.

Khi tìm icon, ưu tiên exact match theo `id` hoặc `name`. Nếu nhiều item cùng name hoặc kết quả mơ hồ, dừng và làm rõ. `meta` đã được quan sát có thể là `null`; không suy ra hỗ trợ hoặc semantics phân trang nếu response hiện hành không cung cấp.

Trước khi upload một library item name mới, đọc danh sách và kiểm tra trùng name. Nếu item hiện có đúng asset mong muốn, tái sử dụng URL trong `data`; nếu cùng name nhưng asset khác hoặc không thể xác minh nội dung, không tự ghi đè hay tạo bản sao.

## Chuẩn bị upload

Các biến cần chuẩn bị:

```bash
WORKSPACE_DOMAIN='tenant.example.com'
FILE_PATH='/absolute/path/to/instagram_6422200.svg'
LIBRARY_ITEM_NAME='instagram_6422200'
```

Không ghi token hoặc cookie thật vào source code, log hay Git.

## Bước 1: Upload file lên file-server

```bash
UPLOAD_RESPONSE=$(curl --silent --show-error --fail-with-body \
  --url "https://${WORKSPACE_DOMAIN}/api/v1/file/upload/v2/client_upload" \
  -H 'accept: application/json, text/plain, */*' \
  -H "x-csrf-token: ${XSRF_TOKEN}" \
  -H "x-xsrf-token: ${XSRF_TOKEN}" \
  -b "AuthToken=${AUTH_TOKEN}; HttpSessionId=${HTTP_SESSION_ID}; XSRF-TOKEN=${XSRF_TOKEN}" \
  -F "file=@${FILE_PATH}")
```

Dùng `-F` để `curl` tự tạo multipart boundary và gửi nội dung file thật. Không tự khai báo header `content-type: multipart/form-data`.

Response thành công:

```json
{
  "msg": "OK",
  "r": 0,
  "data": {
    "fileName": "instagram_6422200.svg",
    "fileSize": 1789,
    "file_id": "asia-1_3W_5P1ZQEKMOG",
    "resolutionSizes": [],
    "acl": "private",
    "fileExt": "svg",
    "fileServerUrlTemplate": "//asia-1{FILE_SERVER_SUFFIX_PUBLIC_URL}/{SHORT_LIVED_TOKEN}/asia-1_3W_5P1ZQEKMOG/instagram_6422200.svg",
    "fileType": "file_push",
    "url": "https://tenant.example.com/files/{file_id}/original/example-icon.svg?redirect=true"
  }
}
```

Object `data` là metadata của file. Lấy nguyên object này từ response, không tự dựng lại hoặc thay `file_id`:

```bash
FILE_METADATA=$(jq -c '.data' <<<"${UPLOAD_RESPONSE}")
```

Chỉ tiếp tục khi HTTP thành công, `r: 0` và response có `data.file_id`.

## Bước 2: Thêm icon hoặc ảnh vào thư viện

Trường `data` trong mỗi phần tử phải là **chuỗi JSON** chứa metadata. Dùng `jq` để serialize đúng:

```bash
ADD_LIBRARY_PAYLOAD=$(jq -n \
  --arg name "${LIBRARY_ITEM_NAME}" \
  --argjson metadata "${FILE_METADATA}" \
  '{data: [{name: $name, data: ($metadata | tojson)}]}')
```

Gửi request:

```bash
ADD_LIBRARY_RESPONSE=$(curl --silent --show-error --fail-with-body \
  --url "https://${WORKSPACE_DOMAIN}/api/v1/objects/icon/add-multiple" \
  -H 'accept: application/json, text/plain, */*' \
  -H 'content-type: application/json' \
  -H "x-csrf-token: ${XSRF_TOKEN}" \
  -H "x-xsrf-token: ${XSRF_TOKEN}" \
  -b "AuthToken=${AUTH_TOKEN}; HttpSessionId=${HTTP_SESSION_ID}; XSRF-TOKEN=${XSRF_TOKEN}" \
  --data-raw "${ADD_LIBRARY_PAYLOAD}")
```

Response thành công:

```json
{
  "r": 0,
  "msg": "OK",
  "data": [
    {
      "id": "https://tenant.example.com/files/{file_id}/original/example-icon.svg?redirect=true",
      "slug": null,
      "options": []
    }
  ]
}
```

Chỉ báo hoàn tất khi HTTP thành công, `r: 0` và mảng `data` không rỗng.

## Lưu ý

- Upload riêng từng file để nhận metadata tương ứng; `add-multiple` có thể nhận nhiều phần tử trong mảng `data`.
- URL file thư viện có thể là asset private. Khi kiểm tra khả năng đọc file, dùng cùng phiên Web App; request không có cookie có thể trả `401` dù icon đã được upload và cài đúng.
- Luôn gửi đủ ba cookie và hai header CSRF/XSRF theo `$cogover-api-auth`.
- Nếu bước 1 thành công nhưng bước 2 thất bại, báo `file_id`; không upload lại một cách mù quáng.
- Nếu phiên hết hạn hoặc API trả `401`/`403`, tạo lại phiên bằng `$cogover-api-auth` rồi mới thử lại.
