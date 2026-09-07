# Custom Frontend Module API Reference

Tài liệu này mô tả API HTTP public cho Custom Frontend Module của Cogover và contract URL public của static asset đã deploy.

Dùng HTTPS origin của Cogover Workspace đích làm base URL:

```text
https://{WORKSPACE_DOMAIN}
```

`WORKSPACE_DOMAIN` là hostname đầy đủ của Workspace, bao gồm cả domain suffix. Không nối thêm suffix khác.

Chỉ các path, header, request field và response field public được mô tả tại đây thuộc contract tích hợp.

## Xác thực và định tuyến

Mọi request quản lý đều yêu cầu Cogover Workspace session đã xác thực và quyền TypeScript Project SuperAdmin:

```http
x-req-service: 4
Cookie: HttpSessionId=<session-id>; AuthToken=<workspace-auth-token>
X-Csrf-Token: <csrf-token>
Content-Type: application/json
```

Giá trị CSRF thường được cấp cùng phiên đăng nhập Cogover. Không đặt `HttpSessionId`, `AuthToken` hoặc CSRF token trong URL hay JSON body.

Request static asset dùng hai cookie `HttpSessionId` và `AuthToken`. Đây là thao tác chỉ đọc nên không cần CSRF header.

## Quy ước chung

- Tất cả route quản lý dùng `POST`, kể cả thao tác đọc hoặc xóa.
- Request và response body quản lý dùng JSON.
- Path resource ID như `projectId` và `versionId` gồm 15 chữ cái in hoa hoặc chữ số.
- Timestamp là Unix epoch millisecond.
- Slug phải khớp `[A-Za-z_][A-Za-z0-9_]{0,99}`, duy nhất trong Workspace và không thể thay đổi.
- `idempotencyKey` khi publish phải khớp `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`.
- Nội dung thông báo do Cogover trả về luôn bằng tiếng Anh.

Lỗi có JSON shape:

```json
{
  "r": 400,
  "msg": "Invalid resource ID"
}
```

Các HTTP status thường gặp: `400` request không hợp lệ, `401` cần xác thực, `403` thiếu quyền, `404` không tìm thấy resource, `409` xung đột lifecycle, uniqueness, quota hoặc idempotency và `503` lỗi dịch vụ tạm thời.

## Tổng hợp endpoint

| Method | Path | Thành công |
|---|---|---:|
| `POST` | `/api/v1/ts-projects/frontend` | `201` |
| `POST` | `/api/v1/ts-projects/frontend/list` | `200` |
| `POST` | `/api/v1/ts-projects/frontend/{projectId}` | `200` |
| `POST` | `/api/v1/ts-projects/frontend/{projectId}/update` | `200` |
| `POST` | `/api/v1/ts-projects/frontend/{projectId}/delete` | `200` |
| `POST` | `/api/v1/ts-projects/frontend/{projectId}/versions` | `202` |
| `POST` | `/api/v1/ts-projects/frontend/{projectId}/versions/list` | `200` |
| `POST` | `/api/v1/ts-projects/frontend/{projectId}/versions/{versionId}` | `200` |
| `POST` | `/api/v1/ts-projects/frontend/{projectId}/versions/{versionId}/delete` | `200` |
| `POST` | `/api/v1/ts-projects/frontend/{projectId}/versions/{versionId}/activate` | `200` |
| `POST` | `/api/v1/ts-projects/frontend/{projectId}/deactivate` | `200` |
| `GET`, `HEAD` | `/{slugSlot}/{relativePath}` | Static asset đã deploy |

## Project object

Các project endpoint trả shape sau:

```json
{
  "id": "FEPXXXXXXXXXXXX",
  "workspaceId": "WSXXXXXXXXXXXXX",
  "name": "Sales dashboard",
  "description": "Workspace sales UI",
  "slug": "sales_dashboard",
  "slugSlot": "_cm_1",
  "status": "DRAFT",
  "activeVersionId": null,
  "lockVersion": 0,
  "created": 1788023000000,
  "updated": 1788023000000
}
```

`slug` là định danh module do client chọn. `slugSlot` là public path segment do Cogover cấp, từ `_cm_1` đến `_cm_100`. Khi tạo link tới asset đã deploy, dùng `slugSlot` thay vì `slug`. `lockVersion` là dấu phiên bản đồng thời dạng opaque.

Project status:

| Status | Ý nghĩa |
|---|---|
| `DRAFT` | Hiện không có version nào được phục vụ |
| `ACTIVE` | `activeVersionId` đang được phục vụ tại `slugSlot` |
| `DISABLED` | Module đã bị xóa và không thể sử dụng |

## Tạo module

```http
POST /api/v1/ts-projects/frontend
x-req-service: 4
Content-Type: application/json
```

```json
{
  "name": "Sales dashboard",
  "description": "Workspace sales UI",
  "slug": "sales_dashboard"
}
```

`name` bắt buộc và dài tối đa 250 ký tự. `description` không bắt buộc và dài tối đa 2.000 ký tự. Mỗi Workspace có thể có tối đa 100 Custom Frontend Module đang tồn tại.

HTTP `201` trả project object.

## Liệt kê module

```http
POST /api/v1/ts-projects/frontend/list
x-req-service: 4
Content-Type: application/json
```

```json
{
  "page": 1,
  "pageSize": 20,
  "keyword": "sales"
}
```

`page` mặc định `1`; `pageSize` mặc định `20` và phải từ `1` đến `100`; `keyword` không bắt buộc và dài tối đa 100 ký tự.

```json
{
  "items": [],
  "page": 1,
  "pageSize": 20,
  "totalItems": 0,
  "totalPages": 0
}
```

## Đọc một module

```http
POST /api/v1/ts-projects/frontend/{projectId}
x-req-service: 4
Content-Type: application/json

{}
```

Response là project object.

## Cập nhật module

```http
POST /api/v1/ts-projects/frontend/{projectId}/update
x-req-service: 4
Content-Type: application/json
```

```json
{
  "name": "Sales dashboard v2",
  "description": null
}
```

Gửi ít nhất một trong hai field `name` hoặc `description`. `description: null` xóa mô tả. `slug` và `slugSlot` đều bất biến; request chứa một trong hai field này sẽ bị từ chối.

## Xóa module

```http
POST /api/v1/ts-projects/frontend/{projectId}/delete
x-req-service: 4
Content-Type: application/json

{}
```

Thao tác xóa có tính idempotent. Project trả về có `status: "DISABLED"` và asset path không còn phục vụ nội dung.

## Version object

Các version endpoint trả shape sau:

```json
{
  "id": "FEVXXXXXXXXXXXX",
  "projectId": "FEPXXXXXXXXXXXX",
  "versionNumber": 1,
  "status": "PENDING",
  "sourceFileId": "<PRIVATE_ZIP_FILE_ID>",
  "sourceFileName": "dist.zip",
  "sourceFileSize": 123456,
  "sourceSha256": null,
  "artifactSha256": null,
  "sourcePermanent": false,
  "buildErrorCode": null,
  "buildErrorMessage": null,
  "deleted": false,
  "created": 1788023000000,
  "updated": 1788023000000
}
```

Các build state có thể có: `PENDING`, `DOWNLOADING`, `VALIDATING`, `FILE_COMMIT_PENDING`, `READY` và `FAILED`. Khi thất bại, `buildErrorCode` và `buildErrorMessage` chứa thông tin chẩn đoán public.

## Publish version

Build ứng dụng trước khi upload. Upload ZIP private qua API upload file của Cogover với layout:

```text
dist/
  index.html
  assets/
  images/
```

Chỉ file bên trong `dist/` được publish. Archive không được chứa symbolic link, special file, path không an toàn hoặc các path chỉ khác nhau về chữ hoa/thường.

```http
POST /api/v1/ts-projects/frontend/{projectId}/versions
x-req-service: 4
Content-Type: application/json
```

```json
{
  "idempotencyKey": "sales-dashboard-20260905-001",
  "file": {
    "file_id": "<PRIVATE_ZIP_FILE_ID>",
    "fileName": "dist.zip",
    "fileSize": 123456,
    "fileExt": "zip",
    "fileType": "application/zip",
    "acl": "private"
  }
}
```

Tên ZIP dài tối đa 255 ký tự. `fileSize` phải dương, `fileExt` phải là `zip`, `acl` phải là `private` và `idempotencyKey` là bắt buộc.

HTTP `202` trả version object; quá trình publish tiếp tục bất đồng bộ. Poll endpoint chi tiết version cho tới khi version là `READY` hoặc `FAILED`.

## Liệt kê hoặc đọc version

```http
POST /api/v1/ts-projects/frontend/{projectId}/versions/list
POST /api/v1/ts-projects/frontend/{projectId}/versions/{versionId}
x-req-service: 4
Content-Type: application/json

{}
```

List trả JSON array các version object. Detail trả một version object.

## Activate version

```http
POST /api/v1/ts-projects/frontend/{projectId}/versions/{versionId}/activate
x-req-service: 4
Content-Type: application/json

{}
```

Version phải đã được giữ lại và ở trạng thái `READY`. Project trả về có `status: "ACTIVE"` và `activeVersionId` là version đã chọn. Asset request mới sẽ resolve tới version này.

## Deactivate module

```http
POST /api/v1/ts-projects/frontend/{projectId}/deactivate
x-req-service: 4
Content-Type: application/json

{}
```

Project trả về có `status: "DRAFT"` và `activeVersionId: null`. Asset path dừng phục vụ nội dung; các version vẫn tồn tại để có thể activate sau.

## Xóa version

```http
POST /api/v1/ts-projects/frontend/{projectId}/versions/{versionId}/delete
x-req-service: 4
Content-Type: application/json

{}
```

Không thể xóa active version. Hãy activate version khác hoặc deactivate module trước. Version trả về có `deleted: true`.

## Truy cập asset đã deploy

Với module đang active, tạo public URL từ Workspace origin, `slugSlot` được trả về và path file bên trong `dist/`:

```text
https://{WORKSPACE_DOMAIN}/{slugSlot}/{relativePath}
```

Ví dụ:

```text
https://{WORKSPACE_DOMAIN}/_cm_1/index.html
https://{WORKSPACE_DOMAIN}/_cm_1/assets/app.a1b2c3.js
https://{WORKSPACE_DOMAIN}/_cm_1/images/logo.png
```

Request hỗ trợ `GET` và `HEAD`, đồng thời yêu cầu:

```http
Cookie: HttpSessionId=<session-id>; AuthToken=<workspace-auth-token>
```

Không có cơ chế tự động fallback cho single-page application. Hãy request rõ `index.html` làm entry point và cấu hình client-side routing để thao tác refresh trình duyệt không phụ thuộc vào server fallback.

Asset path phải trỏ tới một file, không được có dấu `/` cuối và không được chứa path component đã encode, segment rỗng hoặc segment bắt đầu bằng `.`. Asset không tồn tại trả `404`; request chưa xác thực trả `401`; module inactive, không tồn tại hoặc không thể truy cập trả `403`.

HTML và static asset có thể được browser cache. Hãy dùng filename có content hash cho JavaScript, CSS, image và asset được version hóa để release mới sau khi activate được nhận biết nhanh.
