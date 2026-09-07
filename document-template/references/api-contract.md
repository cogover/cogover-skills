# API contract cho Document Template

## Mục lục

- [Xác thực chung](#xác-thực-chung)
- [Tóm tắt endpoint](#tóm-tắt-endpoint)
- [Upload file template](#upload-file-template)
- [CRUD qua import-export](#crud-qua-import-export)
- [Export tài liệu để kiểm thử](#export-tài-liệu-để-kiểm-thử)
- [Payload template](#payload-template)
- [Metadata object hỗ trợ](#metadata-object-hỗ-trợ)
- [Validation và lỗi](#validation-và-lỗi)
- [Nguồn bằng chứng và giới hạn](#nguồn-bằng-chứng-và-giới-hạn)

## Xác thực chung

Mọi endpoint trong tài liệu này bắt đầu bằng `/api/v1`, nên bắt buộc dùng phiên Web App từ `$cogover-api-auth`:

```http
Cookie: HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
```

Tạo bộ giá trị trên bằng API Key qua `POST /bapi/v1/auth-token`. Không dùng `Authorization: Bearer {api-key}` trực tiếp với các endpoint `/api/v1`.

Các ví dụ dưới đây giả định biến shell `BASE_URL` chỉ chứa origin của workspace, ví dụ `https://{workspace-domain}`, và cookie/token được truyền bằng placeholder. Không lưu secret vào source control.

## Tóm tắt endpoint

| Mục đích | Method và path | Content-Type | Header phân loại |
|---|---|---|---|
| Upload file | `POST /api/v1/file/upload/v2/client_upload` | `multipart/form-data` | Không có `x-req-service` |
| Tạo template | `POST /api/v1/import-export` | `application/json` | `x-req-service: 12` |
| List/search | `POST /api/v1/import-export` | `application/json` | `x-req-service: 13` |
| Update template | `POST /api/v1/import-export` | `application/json` | `x-req-service: 14` |
| Detail template | `POST /api/v1/import-export` | `application/json` | `x-req-service: 15` |
| Delete template | `POST /api/v1/import-export` | `application/json` | `x-req-service: 16` |
| Export tài liệu từ template | `POST /api/v1/import-export` | `application/json` | `x-req-service: 17`, `x-req-type: 1` |
| List object metadata | `POST /api/v1/objects/object/get` | `application/json` | Không có |
| Object detail by slug | `POST /api/v1/objects/object/get-by-slug` | `application/json` | Không có |

`/api/v1/import-export` là một endpoint multiplexed. Method/path giống nhau; thiếu hoặc dùng sai `x-req-service` sẽ chọn sai operation.

## Upload file template

### Request

Gửi đúng một part tên `file`. Để client HTTP tự tạo boundary; không tự đặt chuỗi boundary trong `Content-Type`.

```bash
curl --fail-with-body \
  --request POST "$BASE_URL/api/v1/file/upload/v2/client_upload" \
  --cookie 'HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}' \
  --header 'x-csrf-token: {XSRF-TOKEN}' \
  --header 'x-xsrf-token: {XSRF-TOKEN}' \
  --form 'file=@/absolute/path/template.docx'
```

### Response

Front-end đọc metadata file tại top-level `data`. Ví dụ dưới đây là minh họa, không phải danh sách key bắt buộc:

```json
{
  "data": {
    "url": "{download-url-containing-{file_id}}",
    "temp_url": "{temporary-url}",
    "file_id": "{file-id}",
    "fileExt": "docx",
    "fileName": "template.docx",
    "fileSize": 12345,
    "fileType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "resolutionSizes": []
  }
}
```

Dùng toàn bộ object bên trong `data` làm `content_upload` của create/update. `temp_url` có thể vắng mặt; `fileType` là giá trị opaque và có thể là `file_push` thay vì MIME; server cũng có thể thêm `acl` hoặc `fileServerUrlTemplate`. Giữ nguyên tất cả key được trả về, không dựng lại metadata bằng tay. Xác minh tối thiểu `fileName`/`fileExt` khớp file đã gửi và response có ít nhất một server reference như `file_id`, `url` hoặc `fileServerUrlTemplate`.

## CRUD qua import-export

### Response envelope

Front-end đọc response create/list/detail theo envelope object-server:

```json
{
  "serviceVersion": 1,
  "service": 13,
  "id": 1770584747,
  "body": {
    "r": 0,
    "msg": "Thành công",
    "data": {}
  }
}
```

Xem `body.r === 0` là điều kiện nghiệp vụ thành công khi trường này tồn tại. Dữ liệu operation nằm tại `body.data`. Update/delete được khai báo qua response wrapper khác trong TypeScript, vì vậy vẫn kiểm tra status/mã lỗi thực tế và không phụ thuộc riêng tên wrapper của type.

### Tạo — service 12

Body là JSON template không có `id`. Ví dụ mode Word:

```bash
curl --fail-with-body \
  --request POST "$BASE_URL/api/v1/import-export" \
  --cookie 'HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}' \
  --header 'x-csrf-token: {XSRF-TOKEN}' \
  --header 'x-xsrf-token: {XSRF-TOKEN}' \
  --header 'x-req-service: 12' \
  --header 'Content-Type: application/json' \
  --data '{
    "name": "Mẫu hợp đồng",
    "description": "Mẫu hợp đồng cho Đối tượng A",
    "category": "{category-option-slug}",
    "related_object": "doi_tuong_a",
    "file_format": "Tai_len_file_Word",
    "download_format": "DOCX",
    "content_upload": {
      "url": "{upload-response-url}",
      "temp_url": "{upload-response-temp-url}",
      "file_id": "{upload-response-file-id}",
      "fileExt": "docx",
      "fileName": "template.docx",
      "fileSize": 12345,
      "fileType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "resolutionSizes": []
    }
  }'
```

Kết quả tạo nằm tại `body.data`; front-end dùng `body.data.id` để điều hướng sang detail.

### List/search — service 13

Payload tối thiểu thực dụng:

```json
{
  "page": 1,
  "limit": 20,
  "sort": "updated",
  "order": "desc",
  "search_after": []
}
```

Các filter đã được front-end chứng minh:

| Trường | Dạng gửi |
|---|---|
| `name` | string |
| `category` | string[] |
| `related_object` | string[] object slug |
| `file_format` | string[] |
| `download_format` | string[] |
| `created` / `updated` | chuỗi `start-end`; một đầu có thể rỗng |
| `created_by` / `updated_by` | `{ "op": "IN" | "NOT_IN", "params": ["{personnel-id}"] }` |
| `limit`, `page`, `sort`, `order` | pagination/sort |
| `search_after` | mảng cursor opaque lấy nguyên từ `searchAfter` của response trang trước |
| `filterFieldsNotIn` | string[] theo type front-end |

Không thêm các key UI `created_start`, `created_end`, `updated_start`, `updated_end`, `created_by_operator`, `updated_by_operator`; front-end chuyển chúng sang dạng API ở bảng trên rồi xóa các key UI.

Response `body.data`:

```json
{
  "total": 15,
  "searchAfter": [1747214884000, "{id}"],
  "rows": [
    {
      "id": "{document-template-id}",
      "name": "Mẫu hợp đồng",
      "related_object": {
        "id": "{object-id}",
        "name": "Đối tượng A",
        "slug": "doi_tuong_a",
        "status": "1"
      },
      "file_format": "Tai_len_file_Word",
      "download_format": "DOCX"
    }
  ]
}
```

### Detail — service 15

```json
{ "id": "{document-template-id}" }
```

Detail nằm tại `body.data` và có thể gồm:

- `id`, `name`, `description`, `category`;
- `related_object` dưới dạng object `{id,name,slug,status}` hoặc slug theo type;
- `file_format`, `download_format`;
- `content_upload`, `content_html` nếu mode tương ứng;
- `created`, `updated`, `created_by`, `updated_by`.

Dữ liệu lịch sử/mocked cho thấy `content_upload` có thể là chuỗi JSON, dù flow upload hiện tại gửi object. Khi đọc, parse một bản sao để kiểm tra/hiển thị; nếu không thay file, giữ nguyên representation server đã trả trong payload read-merge-write. Nếu thay file, dùng object mới từ upload response và không double-stringify.

### Update — service 14

Gửi JSON giống create nhưng bổ sung `id`. Front-end tải detail rồi post toàn bộ form hiện tại, vì vậy thực hiện read-merge-write để không xóa trường không liên quan:

```json
{
  "id": "{document-template-id}",
  "name": "Mẫu hợp đồng cập nhật",
  "description": "Mô tả mới",
  "category": "{category-option-slug}",
  "related_object": "doi_tuong_a",
  "file_format": "Tai_len_file_Html",
  "download_format": "PDF",
  "content_html": "<p>Nội dung mẫu hợp đồng</p>"
}
```

Không đổi `related_object` trên item hiện có: UI vô hiệu hóa trường này khi URL có template ID.

### Delete — service 16

```json
{ "id": "{document-template-id}" }
```

Response thành công có data tương đương `{ "r": 0 }` trong wrapper. Nếu mẫu đang được dùng, front-end xử lý error response có cấu trúc:

```json
{
  "body": {
    "data": {
      "{document-template-id}": [
        { "name": "Nút tạo hợp đồng" }
      ]
    }
  }
}
```

Không tự xóa hoặc sửa button/interface được liệt kê; báo blocker để người dùng quyết định.

## Export tài liệu để kiểm thử

Service `17` tạo file export bất đồng bộ từ một document template và một object record. Trước khi gọi, mở đúng record trong Chrome tại `https://{WORKSPACE_DOMAIN}/settings/o/{OBJECT_SLUG}/{OBJECT_RECORD_ID}` và giữ Web App hoạt động. Hệ thống gửi kết quả qua websocket; Web App nhận sự kiện rồi tự tải file về.

```bash
curl --fail-with-body \
  --request POST "$BASE_URL/api/v1/import-export" \
  --header 'accept: application/json, text/plain, */*' \
  --header 'content-type: application/json' \
  --cookie 'HttpSessionId={HttpSessionId}; AuthToken={AuthToken}; XSRF-TOKEN={XSRF-TOKEN}' \
  --header 'x-csrf-token: {XSRF-TOKEN}' \
  --header 'x-xsrf-token: {XSRF-TOKEN}' \
  --header 'x-req-service: 17' \
  --header 'x-req-type: 1' \
  --data '{
    "document_template_id": "{DOCUMENT_TEMPLATE_ID}",
    "object_record_id": "{OBJECT_RECORD_ID}",
    "object_slug": "{OBJECT_SLUG}",
    "related_list_sorts": {
      "{RELATED_LIST_SLUG}": [
        {"{RELATED_LIST_FIELD_SLUG}": {"order": "asc"}}
      ]
    }
  }'
```

Payload:

| Trường | Contract |
|---|---|
| `document_template_id` | ID template vừa create và đã xác minh bằng service `15` |
| `object_record_id` | ID record fixture thuộc đúng `object_slug` |
| `object_slug` | Slug của `related_object` trên template |
| `related_list_sorts` | Object map từ related-list slug sang mảng sort; mỗi sort map field slug thật sang `{ "order": "asc" | "desc" }` |

Dùng `$object-info` lấy `relatedLists` và fields thật trước khi dựng `related_list_sorts`. Không sao chép slug từ ví dụ của object khác. Chỉ gửi field sort tồn tại; khi không có sort cần thiết, gửi `{}`. Ví dụ đã quan sát có thể chứa nhiều related list và nhiều chiều sort:

```json
{
  "related_list_sorts": {
    "opportunity_contracts": [{"updated": {"order": "desc"}}],
    "quote_contract": [{"updated": {"order": "asc"}}],
    "contract_product_line_contract": [{"created": {"order": "asc"}}]
  }
}
```

Response HTTP/mã nghiệp vụ thành công chỉ xác nhận hệ thống đã nhận job. File tải qua Web App mới là artifact cần kiểm tra. Không suy đoán tên file hoặc response websocket; nhận diện download mới theo thời điểm gọi, record fixture và `download_format` của template. Không retry request khi timeout hoặc trạng thái nhận job chưa rõ vì job đầu có thể vẫn sinh file.

## Payload template

### Trường chung

| Trường | Bắt buộc | Contract |
|---|---|---|
| `name` | Có | string sau trim, 2–100 ký tự |
| `description` | Không | string/null, tối đa 1000 ký tự |
| `category` | Không | option slug lấy từ field `category` của object `document_template` |
| `related_object` | Có | slug của object đích |
| `file_format` | Có | một trong ba hằng số bên dưới |
| `download_format` | Có | phải khớp ma trận bên dưới |

### Mode và ma trận format

| `file_format` | Nội dung bắt buộc | Source extension | `download_format` hợp lệ | Default UI |
|---|---|---|---|---|
| `Tai_len_file_Excel` | `content_upload` | `.xlsx` | `XLSX` | `XLSX` |
| `Tai_len_file_Word` | `content_upload` | `.docx` | `DOCX`, `PDF`, `IMAGE` | `DOCX` |
| `Tai_len_file_Html` | `content_html` không rỗng | Không upload | `PDF`, `IMAGE` | `PDF` |

HTML editor lưu chuỗi HTML. UI tạo placeholder field bằng cách lấy chuỗi các field `slug` theo path và nối bằng dấu `.`; preview sau đó render bằng Velocity với record, related-list và current-user data. Chỉ dùng slug/path đã lấy từ metadata, không suy ra từ label.

## Metadata object hỗ trợ

### Lấy options của `document_template`

```http
POST /api/v1/objects/object/get
Content-Type: application/json

{
  "translate": true,
  "page": 1,
  "limit": 1000,
  "display": true,
  "withFields": 1,
  "slug": {
    "value": ["document_template", "personnel"],
    "equal": true
  }
}
```

Tìm object có `slug: "document_template"`; đọc `fields[].options` của các field slug `category`, `file_format`, `download_format`. Dùng option `slug` làm giá trị API và option `value` chỉ để hiển thị.

### Xác minh object đích và lấy field path

```http
POST /api/v1/objects/object/get-by-slug
Content-Type: application/json

{
  "slug": "doi_tuong_a",
  "withFields": 1,
  "withRelatedList": 1,
  "display": true,
  "translate": true,
  "withPersonnelInfo": false
}
```

Yêu cầu response có ít nhất một object matching slug trước khi tạo template. Dùng `fields` và `relatedLists` của object này để chọn placeholder hợp lệ cho template, không dùng display name làm slug.

## Validation và lỗi

- `body.r: 436`: tên document template đã tồn tại. Dừng và báo trùng tên; không tự sinh suffix.
- Upload lỗi, response thiếu object `data`, tên/extension lệch hoặc không có server reference: không gọi create/update. Không yêu cầu riêng `temp_url`, MIME trong `fileType`, `acl` hay `fileServerUrlTemplate`.
- Extension không khớp mode: dừng trước upload. Front-end so sánh extension cuối tên file, không phân biệt hoa thường.
- Không có giới hạn size template được chứng minh trong flow DocumentSample. Front-end không kiểm tra size và chỉ cấu hình timeout upload 3 phút; không biến timeout client này thành giới hạn server.
- Delete có `body.data[id]`: template đang được dùng; nêu tên dependency và dừng.
- Thiếu quyền: UI yêu cầu quyền view object `document_template`, view record, và quyền create/edit/delete record tương ứng. API có thể trả lỗi quyền; không retry bằng credential khác.
- Session hết hạn: làm theo `$cogover-api-auth` để tạo lại session; không chuyển sang API Key Bearer cho `/api/v1`.

## Nguồn bằng chứng và giới hạn

Contract được rút ra từ snapshot front-end `report-builder-app`, chủ yếu:

- `src/apis/document-sample/document-sample.api.ts` và `.type.ts`;
- `src/apis/file-server/file-server.api.ts` và `.type.ts`;
- `src/pages/DocumentSample/components/Form/*`;
- `src/pages/DocumentSample/DocumentSampleListPage/*`;
- `src/apis/object/object.api.ts` và `.type.ts`;
- tests/mock của `src/__tests__/pages/DocumentSample` và `src/__mocks__/handlers/documentSample.ts`.

Không có OpenAPI/backend schema trong phạm vi nguồn này. Khi server thực tế trả thêm trường, giữ lại khi read-merge-write nhưng không dựa vào trường đó cho logic mới cho tới khi có contract bổ sung.
