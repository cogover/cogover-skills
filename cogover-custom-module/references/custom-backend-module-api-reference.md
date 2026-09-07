# Custom Backend Module API Reference

Tài liệu này mô tả API HTTP public cho Custom Backend Module của Cogover, bao gồm quản lý Project (module) và version, identity policy, Project key, gọi module production và preview một version cụ thể.

Dùng HTTPS origin của Cogover Workspace đích làm base URL:

```text
https://{WORKSPACE_DOMAIN}
```

`WORKSPACE_DOMAIN` là hostname đầy đủ của Workspace, bao gồm cả domain suffix. Không nối thêm suffix khác.

Chỉ các path, header, request field và response field public được mô tả tại đây thuộc contract tích hợp.

## Xác thực và định tuyến

### Xác thực bằng Workspace session

API quản lý module, quản lý Project key, gọi production và preview version dùng Cogover Workspace session đã xác thực:

```http
Cookie: HttpSessionId=<session-id>; AuthToken=<workspace-auth-token>
X-Csrf-Token: <csrf-token>
```

Gửi thêm routing header theo nhóm API:

| Nhóm API | Header | Quyền bắt buộc |
|---|---|---|
| Gọi production | `x-req-service: 3` | Người dùng Workspace đã xác thực; module phải có active version |
| Quản lý module, version, policy và key | `x-req-service: 4` | TypeScript Project SuperAdmin |
| Preview chính xác một version | `x-req-service: 6` | TypeScript Project SuperAdmin |

Giá trị CSRF thường được cấp cùng phiên đăng nhập Cogover. Không đặt `HttpSessionId`, `AuthToken` hoặc CSRF token trong URL hay JSON body.

## Quy ước chung

- Request và response body dùng JSON, trừ khi module được gọi trả về content type khác được hỗ trợ.
- Tất cả route quản lý đều dùng `POST`, kể cả thao tác đọc hoặc xóa.
- Path resource ID như `projectId`, `versionId` và `keyId` gồm 15 chữ cái in hoa hoặc chữ số.
- Timestamp là Unix epoch millisecond.
- API dùng tên field `projectId` cho module trong route quản lý và `projectSlug` cho module đã deploy trong route invocation.
- Slug phải khớp `[A-Za-z_][A-Za-z0-9_]{0,99}` và không thể đổi sau khi tạo.
- `Idempotency-Key` phải khớp `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`.
- Nội dung thông báo do Cogover trả về luôn bằng tiếng Anh.

Lỗi có JSON shape sau. Một số lỗi có thêm field chẩn đoán an toàn như `code`, `reason`, `operation`, `objectSlug`, `objectServerR` hoặc `writesMayHaveCompleted`.

```json
{
  "r": 400,
  "msg": "Invalid resource ID"
}
```

Các HTTP status thường gặp: `400` request không hợp lệ, `401` cần xác thực hoặc phiên hết hạn, `403` thiếu quyền, `404` không tìm thấy resource, `409` xung đột lifecycle hoặc idempotency, `413` request quá lớn, `422` script chạy thất bại, `429` vượt quota và `502`/`503`/`504` lỗi dịch vụ tạm thời.

## Tổng hợp endpoint

### Module và version

Tất cả endpoint trong bảng này yêu cầu `x-req-service: 4` và quyền SuperAdmin.

| Method | Path | Thành công |
|---|---|---:|
| `POST` | `/api/v1/ts-projects` | `201` |
| `POST` | `/api/v1/ts-projects/list` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/update` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/delete` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/versions` | `202` |
| `POST` | `/api/v1/ts-projects/{projectId}/versions/list` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/versions/{versionId}` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/versions/{versionId}/delete` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/versions/{versionId}/activate` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/deactivate` | `200` |

### Identity policy

Tất cả endpoint trong bảng này yêu cầu `x-req-service: 4` và quyền SuperAdmin.

| Method | Path | Mục đích |
|---|---|---|
| `POST` | `/api/v1/ts-projects/{projectId}/identity-policy` | Lưu policy đang chỉnh sửa của module |
| `POST` | `/api/v1/ts-projects/{projectId}/identity-policy/get` | Đọc policy đang chỉnh sửa |
| `POST` | `/api/v1/ts-projects/{projectId}/identity-policy/activate` | Kích hoạt policy đang chỉnh sửa |
| `POST` | `/api/v1/ts-projects/{projectId}/identity-policy/disable` | Vô hiệu hóa policy và active snapshot |
| `POST` | `/api/v1/ts-projects/{projectId}/versions/{versionId}/identity-policy/approve` | Duyệt policy hiện tại cho một version |
| `POST` | `/api/v1/ts-projects/{projectId}/versions/{versionId}/identity-policy/get` | Đọc snapshot đã duyệt của version |
| `POST` | `/api/v1/ts-projects/{projectId}/versions/{versionId}/identity-policy` | Lưu và duyệt trong một thao tác tương thích |

### Project key

Tất cả endpoint trong bảng này yêu cầu `x-req-service: 4` và quyền SuperAdmin.

| Method | Path | Thành công |
|---|---|---:|
| `POST` | `/api/v1/ts-projects/{projectId}/keys` | `201` |
| `POST` | `/api/v1/ts-projects/{projectId}/keys/list` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/keys/{keyId}` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/keys/{keyId}/update` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/keys/{keyId}/rotate` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/keys/{keyId}/revoke` | `200` |

### Invocation

| Method | Path | Routing/xác thực |
|---|---|---|
| `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | `/api/v1/ts-projects/{projectSlug}[/{route}]` | Service `3`, Workspace session |
| `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | `/api/v1/ts-projects/{projectSlug}[/{route}]` | Service `6`, SuperAdmin Workspace session; body chọn version |

## Quản lý module

### Tạo module

```http
POST /api/v1/ts-projects
x-req-service: 4
Content-Type: application/json
```

```json
{
  "name": "Order automation",
  "description": "Synchronize order data",
  "slug": "order_automation"
}
```

`name` bắt buộc và dài tối đa 250 ký tự. `description` không bắt buộc và dài tối đa 2.000 ký tự. Slug phải duy nhất trong Workspace.

HTTP `201` trả về module object:

```json
{
  "id": "TSPXXXXXXXXXXXX",
  "workspaceId": "WSXXXXXXXXXXXXX",
  "name": "Order automation",
  "description": "Synchronize order data",
  "slug": "order_automation",
  "status": "DRAFT",
  "activeVersionId": null,
  "lockVersion": 0,
  "created": 1788023000000,
  "updated": 1788023000000
}
```

`lockVersion` là dấu phiên bản đồng thời dạng opaque; client không được tự thay đổi.

### Liệt kê module

```http
POST /api/v1/ts-projects/list
x-req-service: 4
Content-Type: application/json
```

```json
{
  "page": 1,
  "pageSize": 20,
  "keyword": "order"
}
```

`page` mặc định là `1`; `pageSize` mặc định là `20` và phải từ `1` đến `100`; `keyword` không bắt buộc và dài tối đa 100 ký tự.

```json
{
  "items": [],
  "page": 1,
  "pageSize": 20,
  "totalItems": 0,
  "totalPages": 0
}
```

### Đọc một module

```http
POST /api/v1/ts-projects/{projectId}
x-req-service: 4
Content-Type: application/json

{}
```

Response là module object ở trên.

### Cập nhật module

```http
POST /api/v1/ts-projects/{projectId}/update
x-req-service: 4
Content-Type: application/json
```

```json
{
  "name": "Order automation v2",
  "description": null
}
```

Gửi ít nhất một trong hai field `name` hoặc `description`. `description: null` xóa mô tả. Request có field `slug`, kể cả giữ nguyên giá trị cũ, sẽ bị từ chối.

### Xóa module

```http
POST /api/v1/ts-projects/{projectId}/delete
x-req-service: 4
Content-Type: application/json

{}
```

Thao tác xóa có tính idempotent. Module trả về có `status: "DISABLED"` và không thể được gọi, cập nhật, publish hoặc activate.

## Quản lý version

### Publish version

Trước tiên upload ZIP private qua API upload file của Cogover. Archive phải có `src/main.ts` tại root.

```http
POST /api/v1/ts-projects/{projectId}/versions
x-req-service: 4
Content-Type: application/json
```

```json
{
  "idempotencyKey": "publish-20260905-001",
  "file": {
    "file_id": "<PRIVATE_ZIP_FILE_ID>",
    "fileName": "project.zip",
    "fileSize": 6696,
    "fileExt": "zip",
    "fileType": "application/zip",
    "acl": "private"
  }
}
```

Tên ZIP dài tối đa 255 ký tự. `fileSize` phải dương, `fileExt` phải là `zip`, `acl` phải là `private` và `idempotencyKey` là bắt buộc. Dùng lại key với publish input khác trả về `409`.

HTTP `202` trả về version object và quá trình publish tiếp tục bất đồng bộ:

```json
{
  "id": "TSVXXXXXXXXXXXX",
  "projectId": "TSPXXXXXXXXXXXX",
  "versionNumber": 1,
  "status": "PENDING",
  "sourceFileId": "<PRIVATE_ZIP_FILE_ID>",
  "sourceFileName": "project.zip",
  "sourceFileSize": 6696,
  "sourceSha256": null,
  "sourcePermanent": false,
  "bundleSize": null,
  "bundleSha256": null,
  "buildErrorCode": null,
  "buildErrorMessage": null,
  "deleted": false,
  "deletedAt": null,
  "identityPolicyApproved": false,
  "identityPolicyRevision": null,
  "identityPolicyApprovedAt": null,
  "created": 1788023000000,
  "updated": 1788023000000
}
```

Các build state có thể có: `PENDING`, `DOWNLOADING`, `VALIDATING`, `COMPILING`, `FILE_COMMIT_PENDING`, `READY` và `FAILED`. Poll endpoint chi tiết version cho tới khi nhận `READY` hoặc `FAILED`. Khi thất bại, `buildErrorCode` và `buildErrorMessage` chứa thông tin chẩn đoán public.

### Liệt kê version

```http
POST /api/v1/ts-projects/{projectId}/versions/list
x-req-service: 4
Content-Type: application/json

{}
```

Response là JSON array các version object.

### Đọc một version

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}
x-req-service: 4
Content-Type: application/json

{}
```

Response là một version object.

### Activate version

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/activate
x-req-service: 4
Content-Type: application/json

{}
```

Version phải ở trạng thái `READY` và đã được giữ lại. Activate version độc lập với việc cấp quyền `data.asSystem()` hoặc `data.asUser()`. Module trả về có `status: "ACTIVE"` và `activeVersionId` trỏ tới version đã chọn.

### Deactivate module

```http
POST /api/v1/ts-projects/{projectId}/deactivate
x-req-service: 4
Content-Type: application/json

{}
```

Module trả về có `status: "DRAFT"` và `activeVersionId: null`. Các version hiện có vẫn được giữ lại.

### Xóa version

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/delete
x-req-service: 4
Content-Type: application/json

{}
```

Không thể xóa active version. Hãy activate version khác hoặc deactivate module trước. Version trả về có `deleted: true`.

## Identity policy

Identity policy kiểm soát caller nào được dùng quyền ủy quyền `data.asSystem()` hoặc `data.asUser()` từ Custom Backend Module. Policy không chặn việc chạy module thông thường hoặc truy cập dữ liệu theo quyền mặc định của caller. Policy đang chỉnh sửa của module và snapshot bất biến đã duyệt cho version là hai resource riêng. Cập nhật policy đang chỉnh sửa không làm thay đổi snapshot đã duyệt trước đó.

Hỗ trợ policy schema version `2`:

```json
{
  "schemaVersion": 2,
  "callerPersonnelIds": {
    "mode": "ONLY",
    "personnelIds": ["PERXXXXXXXXXXXX"]
  },
  "allowInternalSystem": false,
  "data.asSystem": {
    "objects": {
      "mode": "ONLY",
      "objectSlugs": ["order"]
    },
    "operations": ["RECORD_READ", "RECORD_UPDATE"]
  },
  "data.asUser": {
    "users": {
      "mode": "ONLY",
      "personnelIds": ["PERYXXXXXXXXXX"]
    },
    "operations": ["RECORD_READ"]
  }
}
```

Selector mode gồm `ALL`, `ALL_EXCEPT` và `ONLY`. Operation được hỗ trợ gồm `RECORD_READ`, `RECORD_CREATE`, `RECORD_UPDATE` và `RECORD_DELETE`. Tên JSON key chính xác là `data.asSystem` và `data.asUser`; không chuyển thành object `data` lồng nhau. Field lạ sẽ bị từ chối.

`callerPersonnelIds` chọn public caller đủ điều kiện dùng delegated grant. `data.asSystem` chọn object và operation được phép. `data.asUser` chọn personnel đích và operation được phép; user đích vẫn phải có quyền thực tế trên dữ liệu được yêu cầu. Bỏ grant nào thì identity mode đó bị cấm.

### Lưu hoặc đọc policy đang chỉnh sửa

```http
POST /api/v1/ts-projects/{projectId}/identity-policy
x-req-service: 4
Content-Type: application/json

<policy-object>
```

Mọi lần lưu đều đưa editable policy về `DRAFT`. Revision chỉ tăng khi nội dung policy thay đổi; lưu nội dung giống hệt khi policy đã ở `DRAFT` có tính idempotent.

```http
POST /api/v1/ts-projects/{projectId}/identity-policy/get
x-req-service: 4
Content-Type: application/json

{}
```

Response có shape:

```json
{
  "id": "TPCXXXXXXXXXXXX",
  "projectId": "TSPXXXXXXXXXXXX",
  "revision": 2,
  "status": "DRAFT",
  "policySha256": "<sha256>",
  "policy": {},
  "created": 1788023000000,
  "updated": 1788024000000
}
```

### Activate hoặc disable policy đang chỉnh sửa

Gửi `{}` tới một trong hai endpoint:

```http
POST /api/v1/ts-projects/{projectId}/identity-policy/activate
POST /api/v1/ts-projects/{projectId}/identity-policy/disable
x-req-service: 4
Content-Type: application/json
```

Response là editable policy object có `status` bằng `ACTIVE` hoặc `DISABLED`. Disable policy cũng khiến các active version snapshot từ chối privileged identity operation.

### Duyệt và đọc version snapshot

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/identity-policy/approve
x-req-service: 4
Content-Type: application/json

{}
```

Version phải `READY` và editable policy phải tồn tại. Response:

```json
{
  "id": "TIPXXXXXXXXXXXX",
  "versionId": "TSVXXXXXXXXXXXX",
  "revision": 1,
  "status": "ACTIVE",
  "bundleSha256": "<sha256>",
  "policySha256": "<sha256>",
  "projectPolicyId": "TPCXXXXXXXXXXXX",
  "projectPolicyRevision": 2,
  "policy": {},
  "approved": 1788025000000,
  "approvedByAccountId": "ACXXXXXXXXXXXXX"
}
```

Đọc snapshot bằng:

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/identity-policy/get
x-req-service: 4
Content-Type: application/json

{}
```

Endpoint tương thích dưới đây trước tiên lưu policy được gửi lên, sau đó duyệt policy cho version:

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/identity-policy
x-req-service: 4
Content-Type: application/json

<policy-object>
```

## Project key

Project key cấp quyền phát triển local cho một module và một caller personnel identity. `permissionCeiling` chỉ có thể thu hẹp quyền hiệu lực.

### Tạo Project key

```http
POST /api/v1/ts-projects/{projectId}/keys
x-req-service: 4
Content-Type: application/json
```

```json
{
  "name": "developer-an",
  "callerPersonnelId": "PERXXXXXXXXXXXX",
  "expiresAt": 1798761600000,
  "permissionCeiling": {
    "schemaVersion": 1,
    "allowWrites": false,
    "allowAsSystem": false,
    "allowAsUser": true
  }
}
```

`name` dài từ 1–100 ký tự, `expiresAt` phải nằm trong tương lai và `permissionCeiling` là bắt buộc.

HTTP `201` trả Project-key object có thêm `projectKey`:

```json
{
  "keyId": "TSKXXXXXXXXXXXX",
  "keyName": "developer-an",
  "workspaceId": "WSXXXXXXXXXXXXX",
  "projectId": "TSPXXXXXXXXXXXX",
  "callerPersonnelId": "PERXXXXXXXXXXXX",
  "secretHint": "Ab_9",
  "permissionCeiling": {
    "schemaVersion": 1,
    "allowWrites": false,
    "allowAsSystem": false,
    "allowAsUser": true
  },
  "status": "ACTIVE",
  "expiresAt": 1798761600000,
  "lastUsedAt": null,
  "revokedAt": null,
  "created": 1788023000000,
  "updated": 1788023000000,
  "projectKey": "cog_pk_TSKXXXXXXXXXXXX_<secret>"
}
```

`projectKey` chỉ được trả về khi create và rotate. Hãy lưu ngay vào nơi lưu credential an toàn.

### Liệt kê hoặc đọc Project key

```http
POST /api/v1/ts-projects/{projectId}/keys/list
POST /api/v1/ts-projects/{projectId}/keys/{keyId}
x-req-service: 4
Content-Type: application/json

{}
```

List trả `{ "items": [...], "total": 1 }`. Hai endpoint này không trả `projectKey`. Active key đã hết hạn được hiển thị với `status: "EXPIRED"`.

### Cập nhật Project key

```http
POST /api/v1/ts-projects/{projectId}/keys/{keyId}/update
x-req-service: 4
Content-Type: application/json
```

```json
{
  "name": "developer-an-read-only",
  "expiresAt": 1800000000000,
  "permissionCeiling": {
    "schemaVersion": 1,
    "allowWrites": false,
    "allowAsSystem": false,
    "allowAsUser": false
  }
}
```

Gửi ít nhất một field. Không thể thay đổi `callerPersonnelId`. Thay đổi key hoặc policy có thể làm mất hiệu lực Development session hiện có.

### Rotate hoặc revoke Project key

```http
POST /api/v1/ts-projects/{projectId}/keys/{keyId}/rotate
POST /api/v1/ts-projects/{projectId}/keys/{keyId}/revoke
x-req-service: 4
Content-Type: application/json

{}
```

Rotate trả về `projectKey` mới đúng một lần và vô hiệu hóa giá trị cũ. Revoke có tính idempotent, đổi status thành `REVOKED` và vô hiệu hóa các Development session của key.

## Phát triển local

Dùng Cogover Dev CLI để phát triển local. Sau khi nhận Project key từ quản trị viên Workspace, chạy các lệnh đăng nhập và chạy ứng dụng local được hướng dẫn trong tài liệu CLI. CLI tự động quản lý an toàn việc xác thực, phiên ngắn hạn, thứ tự request và các SDK capability call.

Không gọi trực tiếp các transport endpoint của Development session. Đây là protocol có version giữa Cogover Dev CLI và Runtime, không phải public integration API dành cho code của Custom Backend Module.

## Gọi module production

Gọi active version bằng module slug và route tùy chọn:

```http
POST /api/v1/ts-projects/order_automation/orders/create?notify=true
x-req-service: 3
Cookie: HttpSessionId=<session-id>; AuthToken=<workspace-auth-token>
X-Csrf-Token: <csrf-token>
Idempotency-Key: order-create-001
Content-Type: application/json

{
  "orderId": "ORD-001"
}
```

Hỗ trợ `GET`, `POST`, `PUT`, `PATCH` và `DELETE`. Request body phải là một JSON object; script input hiệu lực giới hạn 256 KiB. Route phân biệt chữ hoa/thường, không được có dấu `/` cuối và không được chứa segment rỗng, `.` hoặc `..`. Root của module là `/api/v1/ts-projects/{projectSlug}` và không có dấu `/` cuối.

Script nhận JSON body cùng request context chỉ đọc, gồm method, route path, query parameter, request header an toàn, Workspace và user đã xác thực. Credential và transport header không bao giờ được truyền cho code của module.

Module chọn HTTP status, content type, header và body qua public SDK response API. Nếu không dùng custom response, JSON result hợp lệ được trả với HTTP `200` và `application/json; charset=utf-8`. Code trong module không thể đặt hop-by-hop header, cookie, server-identifying header hoặc Cogover routing header.

`Idempotency-Key` không bắt buộc nhưng nên dùng cho request có thể ghi dữ liệu. Retry đã hoàn tất với cùng caller, version deploy, method, route và key sẽ phát lại kết quả đầu tiên. Request trùng đang chạy trả `409`. Idempotency không biến nhiều thao tác dữ liệu thành một transaction.

## Preview chính xác một version

SuperAdmin có thể chạy một version bất biến cụ thể mà không thay đổi active version:

```http
POST /api/v1/ts-projects/order_automation/orders/test
x-req-service: 6
Cookie: HttpSessionId=<session-id>; AuthToken=<workspace-auth-token>
X-Csrf-Token: <csrf-token>
Idempotency-Key: preview-001
Content-Type: application/json
```

```json
{
  "input": {"orderId": "ORD-001"},
  "versionId": "TSVXXXXXXXXXXXX",
  "mode": "READ_ONLY",
  "showDebugData": true
}
```

`input` mặc định `{}`; `mode` mặc định `READ_WRITE` và nhận `READ_ONLY` hoặc `READ_WRITE`; `showDebugData` mặc định `false`. Hỗ trợ cả năm HTTP method invocation; envelope trên vẫn là request body, kể cả với `GET`.

Khi `showDebugData` là `false`, response giống contract HTTP trực tiếp của production invocation. Khi là `true`, response thành công có dạng:

```json
{
  "projectId": "TSPXXXXXXXXXXXX",
  "projectSlug": "order_automation",
  "versionId": "TSVXXXXXXXXXXXX",
  "mode": "READ_ONLY",
  "route": "/orders/test",
  "executionId": "<uuid>",
  "bundleSha256": "<sha256>",
  "success": true,
  "result": {"ok": true},
  "httpResponse": {
    "status": 200,
    "headers": {"content-type": ["application/json; charset=utf-8"]},
    "bodyType": "json"
  },
  "durationMs": 24,
  "replayed": false,
  "stdout": "",
  "stderr": "",
  "logsTruncated": false
}
```

Debug output bị giới hạn kích thước. Script lỗi trả `success: false` cùng object `error`. Stack trace và thông tin hệ thống nội bộ không được trả về.

`READ_ONLY` chỉ cho phép thao tác đọc. `READ_WRITE` không tự cấp thêm quyền; mọi lời gọi vẫn bị giới hạn bởi caller, policy và capability hiện có. Các thao tác ghi là thật và không được rollback theo nhóm.
