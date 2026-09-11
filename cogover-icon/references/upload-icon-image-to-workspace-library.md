# Upload icon/ảnh vào thư viện của Workspace

API đọc danh sách icon hiện có và quy trình hai bước: upload file lên file-server, rồi thêm metadata vào thư viện icon/ảnh của Workspace. Các endpoint là `/api/v1`, dùng phiên Web App (`AUTH_TOKEN`, `HTTP_SESSION_ID`, `XSRF_TOKEN` lấy qua `$cogover-api-auth`); không tạo được phiên hợp lệ thì dừng và báo người dùng. Mọi request dưới đây dùng chung hàm:

```bash
cogover_session_curl() {
  curl --silent --show-error --fail-with-body \
    -H 'accept: application/json, text/plain, */*' \
    -H "x-csrf-token: ${XSRF_TOKEN}" \
    -H "x-xsrf-token: ${XSRF_TOKEN}" \
    -b "AuthToken=${AUTH_TOKEN}; HttpSessionId=${HTTP_SESSION_ID}; XSRF-TOKEN=${XSRF_TOKEN}" \
    "$@"
}
```

## Đọc danh sách icon trong thư viện

```bash
ICON_LIBRARY_RESPONSE=$(cogover_session_curl --url "https://${WORKSPACE_DOMAIN}/api/v1/objects/icon")
```

Response `GET /api/v1/objects/icon` đã xác minh:

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

Chỉ tiếp tục khi HTTP thành công, `r: 0` và `data` là mảng. Với từng phần tử:

- `id`: ID bản ghi thư viện, thường có dạng `CON...`; dùng để nhận diện/resolve item.
- `name`: tên library item.
- `data`: URL file icon; dùng giá trị này khi cài icon vào Button hoặc App Menu.
- `workspaceId`, timestamps và creator/updater: metadata server-managed, không gửi lại khi cài icon.
- `meta` đã được quan sát có thể là `null`; không suy ra hỗ trợ hoặc semantics phân trang nếu response hiện hành không cung cấp.

Không nhầm hai response shape: `GET /api/v1/objects/icon` có URL icon ở `data[].data`; `POST /api/v1/objects/icon/add-multiple` có URL icon ở `data[].id`.

Khi tìm icon, ưu tiên exact match theo `id` hoặc `name`; nhiều item cùng name hoặc kết quả mơ hồ thì dừng và làm rõ. Trước khi upload một library item name mới, đọc danh sách và kiểm tra trùng name: item hiện có đúng asset mong muốn thì tái sử dụng URL trong `data`; cùng name nhưng asset khác hoặc không thể xác minh nội dung thì không tự ghi đè hay tạo bản sao.

## Chuẩn bị upload

```bash
WORKSPACE_DOMAIN='tenant.example.com'
FILE_PATH='/absolute/path/to/menu_budget.svg'
LIBRARY_ITEM_NAME='menu_budget'
```

## Bước 1: Upload file lên file-server

```bash
UPLOAD_RESPONSE=$(cogover_session_curl \
  --url "https://${WORKSPACE_DOMAIN}/api/v1/file/upload/v2/client_upload" \
  -F "file=@${FILE_PATH}")
```

Dùng `-F` để `curl` tự tạo multipart boundary và gửi nội dung file thật; không tự khai báo header `content-type: multipart/form-data`.

Response thành công:

```json
{
  "msg": "OK",
  "r": 0,
  "data": {
    "fileName": "menu_budget.svg",
    "fileSize": 1789,
    "file_id": "{FILE_ID}",
    "resolutionSizes": [],
    "acl": "private",
    "fileExt": "svg",
    "fileServerUrlTemplate": "//{FILE_SERVER_HOST}{FILE_SERVER_SUFFIX_PUBLIC_URL}/{SHORT_LIVED_TOKEN}/{FILE_ID}/menu_budget.svg",
    "fileType": "file_push",
    "url": "https://tenant.example.com/files/{file_id}/original/example-icon.svg?redirect=true"
  }
}
```

Object `data` là metadata của file: lấy nguyên object này từ response, không tự dựng lại hoặc thay `file_id`. Chỉ tiếp tục khi HTTP thành công, `r: 0` và response có `data.file_id`.

```bash
FILE_METADATA=$(jq -c '.data' <<<"${UPLOAD_RESPONSE}")
```

## Bước 2: Thêm icon hoặc ảnh vào thư viện

Trường `data` trong mỗi phần tử phải là **chuỗi JSON** chứa metadata; serialize bằng `jq`:

```bash
ADD_LIBRARY_PAYLOAD=$(jq -n \
  --arg name "${LIBRARY_ITEM_NAME}" \
  --argjson metadata "${FILE_METADATA}" \
  '{data: [{name: $name, data: ($metadata | tojson)}]}')
ADD_LIBRARY_RESPONSE=$(cogover_session_curl \
  --url "https://${WORKSPACE_DOMAIN}/api/v1/objects/icon/add-multiple" \
  -H 'content-type: application/json' \
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
- URL file thư viện có thể là asset private: kiểm tra khả năng đọc file bằng cùng phiên Web App; request không có cookie có thể trả `401` dù icon đã được upload và cài đúng.
- Bước 1 thành công nhưng bước 2 thất bại: báo `file_id`, không upload lại một cách mù quáng.
