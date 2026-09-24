# Custom Backend Module API Reference

Tài liệu này mô tả API HTTP public cho Custom Backend Module của Cogover, bao gồm quản lý Project (module) và version, identity policy, Project key, secret, inbound access, background job, gọi module production, gọi inbound webhook và preview một version cụ thể.

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

Gửi thêm hai routing header: `x-req-type: 6` cho mọi nhóm, và `x-req-service` theo nhóm API:

| Nhóm API | Header | Quyền bắt buộc |
|---|---|---|
| Gọi production | `x-req-service: 3` | Người dùng Workspace đã xác thực; module phải có active version |
| Quản lý module, version, policy và key | `x-req-service: 4` | TypeScript Project SuperAdmin |
| Preview chính xác một version | `x-req-service: 6` | TypeScript Project SuperAdmin |

Thiếu `x-req-type: 6` thì request service `4` bị Authorization Server xử lý như lệnh logout, trả `{"data":{"deletedTokens":N}}` và thu hồi phiên; service `3` trả `{"msg":"Error","r":5000}`; service `6` trả `r: 5001` (`Can not found processor for request: service=6`).

Giá trị CSRF thường được cấp cùng phiên đăng nhập Cogover. Không đặt `HttpSessionId`, `AuthToken` hoặc CSRF token trong URL hay JSON body.

Quản lý secret, inbound access và job dùng cùng Workspace session và `x-req-service: 4`. Gọi inbound webhook thì khác: không dùng Workspace session lẫn routing header, chỉ dùng inbound credential mô tả ở [Gọi inbound webhook](#gọi-inbound-webhook).

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

### Secret

Tất cả endpoint trong bảng này yêu cầu `x-req-service: 4` và quyền SuperAdmin.

| Method | Path | Thành công |
|---|---|---:|
| `POST` | `/api/v1/ts-projects/{projectId}/secrets` | `201` |
| `POST` | `/api/v1/ts-projects/{projectId}/secrets/list` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/secrets/{secretId}` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/secrets/{secretId}/update` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/secrets/{secretId}/delete` | `200` |

### Inbound access

Tạo, cập nhật, rotate và revoke inbound access có thể trả `503` khi chưa thể áp dụng thay đổi cấu hình an toàn. Sau response thành công, các request tiếp theo dùng cấu hình mới; request đã bắt đầu xác thực có thể hoàn tất với cấu hình trước đó.

Tất cả endpoint trong bảng này yêu cầu `x-req-service: 4` và quyền SuperAdmin.

| Method | Path | Thành công |
|---|---|---:|
| `POST` | `/api/v1/ts-projects/{projectId}/inbound` | `201` |
| `POST` | `/api/v1/ts-projects/{projectId}/inbound/list` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/inbound/{inboundId}` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/inbound/{inboundId}/update` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/inbound/{inboundId}/rotate` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/inbound/{inboundId}/revoke` | `200` |

### Background job

Tất cả endpoint trong bảng này yêu cầu `x-req-service: 4` và quyền SuperAdmin.

| Method | Path | Thành công |
|---|---|---:|
| `POST` | `/api/v1/ts-projects/{projectId}/jobs/runs/list` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/jobs/runs/{runId}` | `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/jobs/enqueue` | `201` |
| `POST` | `/api/v1/ts-projects/{projectId}/jobs/schedules/list` | `200` |

### Invocation

| Method | Path | Routing/xác thực |
|---|---|---|
| `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | `/api/v1/ts-projects/{projectSlug}[/{route}]` | Service `3`, Workspace session |
| `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | `/api/v1/ts-projects/{projectSlug}[/{route}]` | Service `6`, SuperAdmin Workspace session; body chọn version |
| `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | `/api/v1/ts-projects/{projectSlug}/hooks/{inboundId}[/{route}]` | Inbound key hoặc chữ ký HMAC; không session, không routing header |

## Quản lý module

### Tạo module

```http
POST /api/v1/ts-projects
x-req-type: 6
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
x-req-type: 6
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
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Response là module object ở trên.

### Cập nhật module

```http
POST /api/v1/ts-projects/{projectId}/update
x-req-type: 6
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
x-req-type: 6
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
x-req-type: 6
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
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Response là JSON array các version object.

### Đọc một version

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Response là một version object. Response chi tiết có thêm `triggerManifest`: danh sách record trigger mà version khai báo bằng `defineTrigger`, dạng JSON array chỉ đọc. Giá trị là `[]` khi version không khai trigger nào và `null` khi chưa có build tạo ra nó (gồm cả các version được publish trước khi có record trigger). Response liệt kê không có field này.

```json
{
  "id": "TSVXXXXXXXXXXXX",
  "status": "READY",
  "triggerManifest": [
    {
      "key": "order_credit_check",
      "object": "order",
      "timing": "beforeChange",
      "operations": ["create", "update"],
      "fields": ["status", "amount", "customer"],
      "changedFields": ["status", "amount"],
      "when": {"op": "=", "field": "status", "params": "confirmed"},
      "runWhen": "always",
      "writableFields": ["approval_level"],
      "order": 5000,
      "timeoutMs": 2000
    }
  ]
}
```

Hãy xem lại `triggerManifest` trước khi activate version: khi version đã active, các trigger của nó chạy cho mọi thao tác tạo, sửa hoặc xoá bản ghi của các object được liệt kê và thoả điều kiện, từ bất kỳ nguồn nào. Trigger có `"timing": "beforeChange"` chạy trước khi thay đổi được lưu và có thể từ chối hoặc điều chỉnh thay đổi. Trigger có `"timing": "afterChange"` chạy bất đồng bộ sau khi thay đổi đã được lưu, theo cơ chế best-effort, và không thể từ chối hay sửa thay đổi đó. Version có khai báo trigger không hợp lệ (ví dụ object hoặc field không tồn tại, field không ghi được, hoặc key trùng nhau) kết thúc ở `FAILED` với `buildErrorCode: "TRIGGER_MANIFEST_INVALID"`.

### Activate version

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/activate
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Version phải ở trạng thái `READY` và đã được giữ lại. Activate version cũng kích hoạt các record trigger trong `triggerManifest` của nó và gỡ trigger của version active trước đó; deactivate module sẽ gỡ các trigger này. Activate version độc lập với việc cấp quyền `data.asSystem()` hoặc `data.asUser()`. Module trả về có `status: "ACTIVE"` và `activeVersionId` trỏ tới version đã chọn.

### Deactivate module

```http
POST /api/v1/ts-projects/{projectId}/deactivate
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Module trả về có `status: "DRAFT"` và `activeVersionId: null`. Các version hiện có vẫn được giữ lại.

### Xóa version

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/delete
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Không thể xóa active version. Hãy activate version khác hoặc deactivate module trước. Version trả về có `deleted: true`.

## Identity policy

Identity policy kiểm soát caller nào được dùng quyền ủy quyền `data.asSystem()` hoặc `data.asUser()` từ Custom Backend Module, và module được gửi email bằng `email.send()` từ những hộp thư nào. Policy không chặn việc chạy module thông thường hoặc truy cập dữ liệu theo quyền mặc định của caller. Policy đang chỉnh sửa của module và snapshot bất biến đã duyệt cho version là hai resource riêng. Cập nhật policy đang chỉnh sửa không làm thay đổi snapshot đã duyệt trước đó.

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
  },
  "email": {
    "workspaceMailboxIds": ["EMWXXXXXXXXXXXX"],
    "allowActorMailbox": true
  }
}
```

Selector mode gồm `ALL`, `ALL_EXCEPT` và `ONLY`. Operation được hỗ trợ gồm `RECORD_READ`, `RECORD_CREATE`, `RECORD_UPDATE` và `RECORD_DELETE`. Tên JSON key chính xác là `data.asSystem` và `data.asUser`; không chuyển thành object `data` lồng nhau. Field lạ sẽ bị từ chối.

`callerPersonnelIds` chọn public caller đủ điều kiện dùng delegated grant. `data.asSystem` chọn object và operation được phép. `data.asUser` chọn personnel đích và operation được phép; user đích vẫn phải có quyền thực tế trên dữ liệu được yêu cầu. Bỏ grant nào thì identity mode đó bị cấm.

Policy phải có ít nhất một trong `data.asSystem`, `data.asUser` và `email`.

### Người gửi email

Mục `email` (không bắt buộc) chọn các hộp thư mà module được gửi email từ đó bằng `email.send()`:

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `workspaceMailboxIds` | mảng string | ID của các hộp thư dùng chung của workspace mà module được gửi từ đó, tối đa 50. Mỗi ID khớp `[A-Za-z0-9_-]{1,64}`; ID trùng được bỏ qua. Mặc định `[]`; giá trị `null` bị từ chối. |
| `allowActorMailbox` | boolean | Cho phép gửi từ hộp thư cá nhân mặc định của người dùng có hành động khởi đầu execution (`from: "actor"`). Mặc định `false`. |

- Mục này phải cấp ít nhất một quyền: `workspaceMailboxIds` không rỗng, `allowActorMailbox: true`, hoặc cả hai. Object `email` không cấp quyền nào bị từ chối với HTTP `400`.
- Bỏ `email` nghĩa là module không gửi được email. Gửi notification không cần grant.
- Mục này tuân theo cùng quy tắc với phần còn lại của policy: chỉ có hiệu lực qua version snapshot đã duyệt, chỉ áp dụng cho caller được chọn trong `callerPersonnelIds`, và chỉ áp dụng cho execution không có người dùng khi `allowInternalSystem` là `true`.
- Khi lưu policy, backend không kiểm tra các hộp thư được liệt kê có tồn tại hay không. Việc hộp thư có tồn tại và đang hoạt động hay không được kiểm tra mỗi lần module gửi; hộp thư có trong danh sách nhưng đã bị vô hiệu hoá sẽ bị từ chối tại thời điểm đó.
- Module gửi từ hộp thư mà policy đã duyệt không cho phép nhận `PermissionDeniedError` có `details.reason` là `"EMAIL_SENDER_NOT_GRANTED"`.

Policy có thể chỉ gồm mục `email`:

```json
{
  "schemaVersion": 2,
  "callerPersonnelIds": {
    "mode": "ALL",
    "personnelIds": []
  },
  "allowInternalSystem": true,
  "email": {
    "workspaceMailboxIds": ["EMWXXXXXXXXXXXX"],
    "allowActorMailbox": false
  }
}
```

### Lưu hoặc đọc policy đang chỉnh sửa

```http
POST /api/v1/ts-projects/{projectId}/identity-policy
x-req-type: 6
x-req-service: 4
Content-Type: application/json

<policy-object>
```

Mọi lần lưu đều đưa editable policy về `DRAFT`. Revision chỉ tăng khi nội dung policy thay đổi; lưu nội dung giống hệt khi policy đã ở `DRAFT` có tính idempotent.

```http
POST /api/v1/ts-projects/{projectId}/identity-policy/get
x-req-type: 6
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
x-req-type: 6
x-req-service: 4
Content-Type: application/json
```

Response là editable policy object có `status` bằng `ACTIVE` hoặc `DISABLED`. Disable policy cũng khiến các active version snapshot từ chối privileged identity operation.

### Duyệt và đọc version snapshot

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/identity-policy/approve
x-req-type: 6
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
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Endpoint tương thích dưới đây trước tiên lưu policy được gửi lên, sau đó duyệt policy cho version:

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/identity-policy
x-req-type: 6
x-req-service: 4
Content-Type: application/json

<policy-object>
```

## Project key

Project key cấp quyền phát triển local cho một module và một caller personnel identity. `permissionCeiling` chỉ có thể thu hẹp quyền hiệu lực.

### Tạo Project key

```http
POST /api/v1/ts-projects/{projectId}/keys
x-req-type: 6
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
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

List trả `{ "items": [...], "total": 1 }`. Hai endpoint này không trả `projectKey`. Active key đã hết hạn được hiển thị với `status: "EXPIRED"`.

### Cập nhật Project key

```http
POST /api/v1/ts-projects/{projectId}/keys/{keyId}/update
x-req-type: 6
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
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Rotate trả về `projectKey` mới đúng một lần và vô hiệu hóa giá trị cũ. Revoke có tính idempotent, đổi status thành `REVOKED` và vô hiệu hóa các Development session của key.

## Secret

Secret lưu một giá trị cho một module. Code của module đọc secret loại `OPAQUE` bằng `secrets.get`; các loại còn lại là **credential** chỉ dùng cho `fetch(url, { credential })`: Cogover thêm header xác thực vào request đi ra, và code của module không bao giờ đọc được giá trị. Giá trị được lưu mã hóa. Không endpoint, log hay thông báo lỗi nào trả về giá trị, và Cogover không ghi log request/response body của các route này.

### Tạo secret

```http
POST /api/v1/ts-projects/{projectId}/secrets
x-req-type: 6
x-req-service: 4
Content-Type: application/json
```

```json
{
  "name": "erp_api",
  "kind": "BEARER",
  "value": "<token do hệ thống ngoài cấp>",
  "allowedHosts": ["erp.example.com", "*.erp-cloud.example"],
  "description": "ERP API token used by fetch"
}
```

| Field | Quy tắc |
|---|---|
| `name` | Bắt buộc. Khớp `[A-Za-z][A-Za-z0-9_]{0,63}` và duy nhất trong module. Đây là tên dùng trong `secrets.get`, `fetch({ credential })` và `crypto.hmacSha256({ secret })`. |
| `kind` | Bắt buộc. `OPAQUE` (code của module đọc được), `BEARER` (`Authorization: Bearer <value>`), `BASIC` (`Authorization: Basic base64(<value>)`, với `value` dạng `user:password`) hoặc `HEADER` (`<headerName>: <value>`). |
| `value` | Bắt buộc. Giá trị secret; tối đa 8 KiB. |
| `headerName` | Bắt buộc với `HEADER`, không được gửi với loại khác. Tên header mang giá trị. |
| `allowedHosts` | Bắt buộc và không rỗng với `BEARER`, `BASIC`, `HEADER`; không được gửi với `OPAQUE`. Mỗi phần tử là một host chính xác hoặc `*.suffix`, khớp mọi host kết thúc bằng `.suffix`. Credential chỉ được gửi tới host khớp. |
| `description` | Không bắt buộc, tối đa 255 ký tự. |

HTTP `201` trả về metadata của secret:

```json
{
  "secretId": "TSSXXXXXXXXXXXX",
  "name": "erp_api",
  "kind": "BEARER",
  "headerName": null,
  "allowedHosts": ["erp.example.com", "*.erp-cloud.example"],
  "description": "ERP API token used by fetch",
  "status": "ACTIVE",
  "valueVersion": 1,
  "created": 1788023000000,
  "updated": 1788023000000
}
```

`valueVersion` tăng mỗi lần giá trị được thay. Secret dùng được ngay từ code của module sau khi tạo; không cần publish version mới.

### Liệt kê hoặc đọc secret

```http
POST /api/v1/ts-projects/{projectId}/secrets/list
POST /api/v1/ts-projects/{projectId}/secrets/{secretId}
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

List trả `{ "items": [...], "total": 1 }` gồm metadata của secret. Hai endpoint này không trả giá trị.

### Cập nhật secret

```http
POST /api/v1/ts-projects/{projectId}/secrets/{secretId}/update
x-req-type: 6
x-req-service: 4
Content-Type: application/json
```

```json
{
  "value": "<token mới>",
  "allowedHosts": ["erp.example.com"],
  "description": "Rotated on 2026-09-21",
  "status": "ACTIVE"
}
```

Gửi ít nhất một trong `value`, `kind`, `headerName`, `allowedHosts`, `description` hoặc `status`; không thể đổi `name`. Tổ hợp `kind`, `headerName`, `allowedHosts` sau cập nhật phải thỏa cùng quy tắc như khi tạo. Đổi `kind` bắt buộc gửi kèm `value` mới trong cùng request (nếu không trả `400`): credential đã lưu không bao giờ trở thành secret `OPAQUE` đọc được, và ngược lại, với giá trị cũ. `status` là `ACTIVE` hoặc `DISABLED`; secret bị disable bị từ chối với code của module như thể không tồn tại. Trả về metadata đã cập nhật; `value` mới làm `valueVersion` tăng và có hiệu lực từ invocation kế tiếp.

### Xóa secret

```http
POST /api/v1/ts-projects/{projectId}/secrets/{secretId}/delete
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Trả `{ "secretId": "TSSXXXXXXXXXXXX", "deleted": true }`. Code của module còn tham chiếu tên này sẽ gặp lỗi validation.

## Inbound access

Inbound access cho phép hệ thống ngoài gọi các route `/hooks/...` của module mà không cần phiên người dùng Cogover (xem [Gọi inbound webhook](#gọi-inbound-webhook)). Cogover xác thực mỗi lời gọi bằng **inbound key** do Cogover cấp (`authMode: "KEY"`) hoặc **chữ ký HMAC-SHA256** do hệ thống ngoài tính bằng secret dùng chung (`authMode: "HMAC"`). Cogover không ghi log request/response body của các route này.

### Tạo inbound access

```http
POST /api/v1/ts-projects/{projectId}/inbound
x-req-type: 6
x-req-service: 4
Content-Type: application/json
```

```json
{
  "name": "Payment provider",
  "authMode": "HMAC",
  "routePrefix": "/hooks/payments",
  "expiresAt": 1798761600000,
  "hmac": {
    "secret": "<signing secret dùng chung với hệ thống ngoài>",
    "header": "X-Payment-Signature",
    "encoding": "HEX",
    "prefix": "sha256=",
    "timestampHeader": "X-Payment-Timestamp",
    "toleranceSeconds": 300
  }
}
```

| Field | Quy tắc |
|---|---|
| `name` | Bắt buộc, 1–100 ký tự, duy nhất trong module. |
| `authMode` | Bắt buộc. `KEY` hoặc `HMAC`. |
| `routePrefix` | Không bắt buộc. Route, hoặc tiền tố route, dưới `/hooks` mà inbound access này được gọi, ví dụ `/hooks/payments`. Mặc định `/hooks`, cho phép mọi route hook của module. |
| `expiresAt` | Không bắt buộc; thời điểm Unix millisecond trong tương lai, sau đó inbound access ngừng hoạt động. |
| `hmac` | Bắt buộc với `HMAC`, không được gửi với `KEY`. `secret` (bắt buộc, tối đa 8 KiB) là signing secret mà hệ thống ngoài dùng; `header` (bắt buộc) là request header mang chữ ký; `encoding` là `HEX` (mặc định) hoặc `BASE64`; `prefix` (không bắt buộc, tối đa 32 ký tự) là đoạn text hệ thống ngoài đặt trước chữ ký đã mã hóa, ví dụ `sha256=`; `timestampHeader` và `toleranceSeconds` (không bắt buộc, đi cùng nhau) bật chống replay như mô tả bên dưới. |

HTTP `201` trả về metadata của inbound access. Với `authMode: "KEY"`, response có thêm `inboundKey`, chỉ được trả về khi create và rotate; hãy đưa cho hệ thống ngoài và lưu vào nơi lưu credential an toàn.

```json
{
  "inboundId": "TSIXXXXXXXXXXXX",
  "name": "Payment provider",
  "authMode": "KEY",
  "routePrefix": "/hooks/payments",
  "status": "ACTIVE",
  "expiresAt": 1798761600000,
  "secretHint": "Ab_9",
  "hmac": null,
  "lastUsedAt": null,
  "created": 1788023000000,
  "updated": 1788023000000,
  "url": "https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/order_automation/hooks/TSIXXXXXXXXXXXX/payments",
  "inboundKey": "cog_ik_TSIXXXXXXXXXXXX_<secret>"
}
```

Với `authMode: "HMAC"`, `secretHint` là `null` và `hmac` trả lại `header`, `encoding`, `prefix`, `timestampHeader`, `toleranceSeconds`; signing secret không bao giờ được trả về. `url` là URL gốc mà hệ thống ngoài gọi, ghép từ slug của module, inbound ID và `routePrefix`.

### Liệt kê hoặc đọc inbound access

```http
POST /api/v1/ts-projects/{projectId}/inbound/list
POST /api/v1/ts-projects/{projectId}/inbound/{inboundId}
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

List trả `{ "items": [...], "total": 1 }`. Hai endpoint này không trả `inboundKey` hay HMAC secret. Inbound access đã hết hạn được hiển thị với `status: "EXPIRED"`.

### Cập nhật inbound access

```http
POST /api/v1/ts-projects/{projectId}/inbound/{inboundId}/update
x-req-type: 6
x-req-service: 4
Content-Type: application/json
```

```json
{
  "name": "Payment provider (production)",
  "routePrefix": "/hooks/payments",
  "expiresAt": 1800000000000,
  "hmac": { "secret": "<signing secret mới>", "header": "X-Payment-Signature" }
}
```

Gửi ít nhất một field. Không thể đổi `authMode`. `hmac` chỉ được chấp nhận với inbound access loại `HMAC` và thay thế toàn bộ cấu hình HMAC, kể cả secret. Trả về metadata đã cập nhật.

### Rotate hoặc revoke inbound access

```http
POST /api/v1/ts-projects/{projectId}/inbound/{inboundId}/rotate
POST /api/v1/ts-projects/{projectId}/inbound/{inboundId}/revoke
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Rotate dùng cho `authMode: "KEY"`: trả về metadata kèm `inboundKey` mới đúng một lần và vô hiệu hóa key cũ ngay lập tức. Để đổi HMAC secret, dùng update. Revoke có tính idempotent và đổi status thành `REVOKED`; inbound access đã revoke từ chối mọi lời gọi và không thể kích hoạt lại.

## Background job

Job được khai báo trong code của module bằng `defineJob` và là một phần của version đã publish. Các endpoint này cho quản trị viên xem lần chạy và lịch của job, đồng thời khởi chạy một lần chạy thủ công.

### Liệt kê hoặc đọc lần chạy job

```http
POST /api/v1/ts-projects/{projectId}/jobs/runs/list
x-req-type: 6
x-req-service: 4
Content-Type: application/json
```

```json
{
  "jobKey": "recalc_totals",
  "status": "FAILED",
  "page": 1,
  "pageSize": 50
}
```

Mọi field đều không bắt buộc. `status` là `PENDING`, `RUNNING`, `SUCCEEDED` hoặc `FAILED`; `page` bắt đầu từ 1 và `pageSize` tối đa 200. Trả `{ "items": [...], "page": 1, "pageSize": 50, "totalItems": 3 }`, mới nhất trước.

```http
POST /api/v1/ts-projects/{projectId}/jobs/runs/{runId}
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Trả về một lần chạy:

```json
{
  "runId": "TSJXXXXXXXXXXXX",
  "jobKey": "recalc_totals",
  "source": "ENQUEUE",
  "status": "FAILED",
  "attempt": 3,
  "maxAttempts": 3,
  "timeoutMs": 60000,
  "runAt": 1788023000000,
  "enqueuedBy": "http",
  "idempotencyKey": "recalc:daily",
  "payloadBytes": 42,
  "lastErrorCode": "RETRYABLE",
  "lastErrorMessage": "The ERP is temporarily unavailable",
  "created": 1788022000000,
  "updated": 1788024000000,
  "startedAt": 1788023900000,
  "finishedAt": 1788024000000
}
```

`source` là `ENQUEUE` hoặc `SCHEDULE`. `enqueuedBy` cho biết nguồn tạo lần chạy: `http` hoặc `rpc` với lời gọi module, `trigger:<key>`, `job:<key>`, `inbound:<inboundId>`, `schedule` hoặc `development`. Payload của lần chạy không bao giờ được trả về; chỉ có `payloadBytes`. `lastErrorMessage` là thông báo tiếng Anh từ module hoặc Cogover, không chứa dữ liệu payload. Lần chạy đã kết thúc được giữ 7 ngày.

### Enqueue một lần chạy job

```http
POST /api/v1/ts-projects/{projectId}/jobs/enqueue
x-req-type: 6
x-req-service: 4
Content-Type: application/json
```

```json
{
  "jobKey": "recalc_totals",
  "payload": { "cursor": null },
  "delayMs": 0,
  "idempotencyKey": "recalc:2026-09-21"
}
```

`jobKey` phải được active version khai báo. `payload` là JSON không bắt buộc, tối đa 65.536 byte; `delayMs` không bắt buộc, từ 0 đến 2.592.000.000 (30 ngày); `idempotencyKey` không bắt buộc và khớp `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`. HTTP `201` trả `{ "runId": "TSJXXXXXXXXXXXX", "duplicate": false }`; `duplicate: true` nghĩa là đã tồn tại lần chạy cùng job và cùng idempotency key, và `runId` là lần chạy đó. Lần chạy thực thi với danh tính system, theo identity policy đã duyệt của module. Module phải có active version và tối đa 10.000 lần chạy đang chờ hoặc đang chạy, nếu không trả `409` hoặc `429`.

### Liệt kê lịch job

```http
POST /api/v1/ts-projects/{projectId}/jobs/schedules/list
x-req-type: 6
x-req-service: 4
Content-Type: application/json

{}
```

Trả `{ "items": [...] }` với một phần tử cho mỗi job có lịch của active version:

```json
{
  "jobKey": "cancel_stale_orders",
  "cron": "0 2 * * *",
  "timezone": "Asia/Ho_Chi_Minh",
  "status": "ACTIVE",
  "nextRunAt": 1788037200000,
  "lastRunAt": 1787950800000,
  "created": 1788023000000,
  "updated": 1788023000000
}
```

Lịch được tạo và gỡ khi activate/deactivate version; không chỉnh sửa được tại đây. Deactivate module sẽ vô hiệu hóa các lịch của module.

## Theo dõi toàn workspace

Các endpoint chỉ đọc bổ sung này dùng phiên Workspace, `x-req-type: 6`,
`x-req-service: 4` và quyền SuperAdmin. Endpoint theo project mà CLI đang dùng
và cấu trúc response cũ không thay đổi.

| Method | Path | Thành công |
|---|---|---|
| `POST` | `/api/v1/ts-projects/jobs/runs/list` | `200` |
| `POST` | `/api/v1/ts-projects/jobs/schedules/list` | `200` |
| `POST` | `/api/v1/ts-projects/triggers/list` | `200` |
| `POST` | `/api/v1/ts-projects/inbound/list` | `200` |

Mọi bộ lọc đều tùy chọn và kết hợp bằng AND. Bỏ field hoặc gửi `null` có cùng ý nghĩa;
chuỗi rỗng không hợp lệ. `projectId` là ID 15 ký tự chữ hoa hoặc chữ số; bỏ qua để liệt kê
mọi project trong Workspace đã xác thực. Không chọn Workspace qua body. Project ID hợp lệ
nhưng không tồn tại hoặc ngoài phạm vi truy cập trả danh sách rỗng.
Field lạ và bộ lọc không hợp lệ trả `400`.

Cả bốn endpoint nhận số nguyên dương `page` (mặc định 1), `pageSize` (mặc định 20,
tối đa 200). Offset lớn hơn 2.147.483.647 bị từ chối bằng `400`. Response có cấu trúc:

```json
{"items": [], "page": 1, "pageSize": 20, "totalItems": 0, "totalPages": 0}
```

Mỗi item có `projectId`, `projectSlug`, `projectName`. Hai field sau có thể `null` nếu
metadata project không khả dụng; lịch sử run còn được giữ có thể chứa project đã xóa mềm.
Trang vượt dữ liệu trả `items` rỗng nhưng giữ tổng số. Danh sách thay đổi theo thời gian,
không phải snapshot cố định giữa các request. Enum bộ lọc không phân biệt hoa/thường;
response dùng chữ hoa.

### Lượt chạy job toàn workspace

`POST /api/v1/ts-projects/jobs/runs/list` nhận `projectId?`, `jobKey?`, `status?`,
`source?`, `createdFrom?`, `createdTo?`, `page?`, `pageSize?`.

```json
{"projectId":"TSP000000000001","status":"FAILED","source":"SCHEDULE","createdFrom":1789948800000,"createdTo":1790035200000,"page":1,"pageSize":20}
```

`jobKey` lọc chính xác, khớp `[A-Za-z][A-Za-z0-9_]{0,99}`. `status` là `PENDING`,
`RUNNING`, `SUCCEEDED` hoặc `FAILED`; `source` là `ENQUEUE` hoặc `SCHEDULE`.
Khoảng thời gian áp dụng cho lúc tạo: `created >= createdFrom` và `created < createdTo`.
Cả hai là số nguyên epoch milliseconds không âm; khi có đủ hai cận, `createdFrom < createdTo`.
Item có cùng field với response chi tiết run hiện có, gồm `actorPersonnelId` nullable,
cộng ba field project ở trên. Sắp xếp `created DESC, runId DESC`.
Không trả payload, output nghiệp vụ, log hoặc lịch sử từng lần thử. Đọc chi tiết bằng
`POST /api/v1/ts-projects/{projectId}/jobs/runs/{runId}`.

### Lịch job toàn workspace

`POST /api/v1/ts-projects/jobs/schedules/list` nhận `projectId?`, `jobKey?`, `status?`,
`page?`, `pageSize?`. `jobKey` có cùng quy tắc với bộ lọc run; `status` là `ACTIVE`
hoặc `DISABLED`. Mỗi item có `projectId`, `projectSlug`, `projectName`, `jobKey`, `cron`,
`timezone`, `nextRunAt`, `lastRunAt` (nullable), `status`, `timeoutMs`, `maxAttempts`,
`created`, `updated`. Timestamp là epoch milliseconds. Sắp xếp
`nextRunAt ASC, projectId ASC, jobKey ASC`.

Đây là lịch cron, không phải các run enqueue có delay. `lastRunAt` chỉ lần lịch gần nhất
đã tạo run, không phải lần hoàn thành thành công. Lịch vẫn được quản lý qua code/version;
endpoint này không sửa hoặc bật/tắt lịch.

### Record trigger đã đăng ký

`POST /api/v1/ts-projects/triggers/list` nhận `projectId?`, `objectSlug?`, `timing?`,
`status?`, `page?`, `pageSize?`. `objectSlug` lọc chính xác, phải khớp
`[A-Za-z_][A-Za-z0-9_]{0,354}`. `timing` là `BEFORE_CHANGE` hoặc `AFTER_CHANGE`;
`status` là `ACTIVE` hoặc `DISABLED`.

```json
{
  "items": [{
    "triggerId": "RT0000000000001", "projectId": "TSP000000000001",
    "projectSlug": "orders", "projectName": "Orders", "objectTypeId": "OT0000000000001",
    "objectSlug": "order", "triggerKey": "check_credit", "name": "Credit check",
    "timing": "BEFORE_CHANGE", "operations": ["create", "update"], "order": 5000,
    "when": null, "changedFields": ["status"], "runWhen": "ALWAYS",
    "fields": ["status", "amount"], "writableFields": ["amount"], "timeoutMs": 2000,
    "status": "ACTIVE", "created": 1789948800000, "updated": 1789948800000
  }],
  "page": 1, "pageSize": 20, "totalItems": 1, "totalPages": 1
}
```

`operations` chứa `create`, `update` và/hoặc `delete`; `when` là object điều kiện hoặc
`null`; `changedFields`, `writableFields` là mảng string hoặc `null`; `fields` là mảng
string; `runWhen` là `ALWAYS` hoặc `ON_ENTER`. Sắp xếp `projectId`, `objectSlug`, `timing`,
`order`, `triggerId`, tất cả tăng dần.

Chỉ trả trigger Custom Backend Module đã đăng ký, gồm cả trigger bị disable;
không gồm trigger hệ thống hoặc thuộc module khác. Trạng thái đăng ký riêng lẻ không bảo đảm
việc thực thi: còn phụ thuộc trạng thái project và điều kiện trigger.
Activate/deactivate có thể chưa phản ánh ngay vì đăng ký cần đồng bộ.
Đây không phải lịch sử thực thi và không có thao tác sửa/bật tắt/xóa. `triggerManifest`
của version vẫn là nguồn khai báo chỉ đọc riêng; enum `beforeChange`/`afterChange` của
manifest khác enum đăng ký chữ hoa phía trên.

### Inbound access toàn workspace

`POST /api/v1/ts-projects/inbound/list` nhận `projectId?`, `authMode?`, `status?`,
`page?`, `pageSize?`. `authMode` là `KEY` hoặc `HMAC`. `status` là trạng thái hiệu lực
`ACTIVE`, `EXPIRED` hoặc `REVOKED`: dòng `ACTIVE` đã qua `expiresAt` được liệt kê và lọc
như `EXPIRED`.

```json
{"projectId":"TSP000000000001","authMode":"KEY","status":"ACTIVE","page":1,"pageSize":20}
```

Item có cùng field với danh sách inbound access theo project, gồm `url`, `secretHint`,
`hmac`, `lastUsedAt`, `revokedAt`, cộng ba field project ở trên. `url` là `null` khi
metadata project không khả dụng. Sắp xếp `created DESC, inboundId DESC`. Không bao giờ trả
`inboundKey`, hash của key hay HMAC secret. Tạo, cập nhật, rotate và revoke vẫn là thao tác
theo project.

Cả bốn API đọc trả `401`/`403` khi thiếu/bị từ chối xác thực hoặc không đủ quyền, `503`
khi kho dữ liệu theo dõi không khả dụng. Cấu hình trigger đã lưu không hợp lệ trả `500`
với `msg: "Stored trigger configuration is invalid"`.

## Phát triển local

Dùng Cogover Dev CLI để phát triển local. Sau khi nhận Project key từ quản trị viên Workspace, chạy các lệnh đăng nhập và chạy ứng dụng local được hướng dẫn trong tài liệu CLI. CLI tự động quản lý an toàn việc xác thực, phiên ngắn hạn, thứ tự request và các SDK capability call.

Không gọi trực tiếp các transport endpoint của Development session. Đây là protocol có version giữa Cogover Dev CLI và Runtime, không phải public integration API dành cho code của Custom Backend Module.

## Gọi module production

Gọi active version bằng module slug và route tùy chọn:

```http
POST /api/v1/ts-projects/order_automation/orders/create?notify=true
x-req-type: 6
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

Module mà code chỉ khai báo record trigger hoặc background job và không có HTTP handler mặc định thì không có endpoint để gọi: mọi URI gọi module đó trả `404`. Record trigger và job không bao giờ truy cập được qua URI gọi module; trigger chỉ chạy khi bản ghi thay đổi và job chỉ chạy khi được enqueue hoặc theo lịch.

## Gọi inbound webhook

Hệ thống ngoài gọi module qua một [inbound access](#inbound-access) tại URI riêng. Lời gọi không cần Workspace session của Cogover lẫn hai header `x-req-type`, `x-req-service`; Workspace session không thay thế được inbound credential trên các URI này, và các URI gọi module thông thường không chấp nhận inbound credential.

```http
POST /api/v1/ts-projects/{projectSlug}/hooks/{inboundId}/{route}
POST /api/v1/ts-projects/{projectSlug}/hooks/{inboundId}
```

Hỗ trợ `GET`, `POST`, `PUT`, `PATCH` và `DELETE`. `inboundId` là ID của inbound access, và `route` phải bắt đầu bằng `routePrefix` của inbound access sau segment `/hooks`. Route handler của module nhận `request.path` là `/hooks/{route}` (hoặc `/hooks` khi không có route); inbound ID không nằm trong path mà module thấy.

Xác thực phụ thuộc vào `authMode` của inbound access:

- `KEY`: gửi inbound key trong `Authorization: Bearer cog_ik_<inboundId>_<secret>` hoặc trong `X-Cogover-Inbound-Key: cog_ik_<inboundId>_<secret>`.
- `HMAC`: gửi chữ ký trong `header` đã cấu hình. Chữ ký là `<prefix>` nối với HMAC-SHA256 của signed payload, mã hóa theo `encoding`, tính bằng secret dùng chung. Signed payload là raw body của request theo byte; khi có cấu hình `timestampHeader`, signed payload là `<timestamp>.<raw body>`, với `<timestamp>` là giá trị header đó tính bằng giây Unix, và lời gọi bị từ chối khi timestamp lệch quá `toleranceSeconds` so với giờ server.

```http
POST /api/v1/ts-projects/order_automation/hooks/TSIXXXXXXXXXXXX/payments
X-Payment-Timestamp: 1788023000
X-Payment-Signature: sha256=<HMAC-SHA256 dạng hex của "1788023000.<body>">
Content-Type: application/json

{"id": "evt_123", "orderId": "ORD-001", "status": "succeeded"}
```

Mọi lỗi xác thực — inbound access không tồn tại, đã revoke hoặc hết hạn, inbound access của module khác, route ngoài `routePrefix`, key hoặc chữ ký sai, timestamp ngoài tolerance — trả HTTP `401` với `{ "r": 401, "msg": "Inbound authentication failed" }`, không kèm chi tiết. Mỗi inbound access, và mỗi địa chỉ gọi, nhận tối đa 600 request mỗi phút; vượt quá trả `429`. Khi có `timestampHeader`, mỗi chữ ký chỉ được chấp nhận một lần: request thứ hai cùng chữ ký trong cửa sổ tolerance bị từ chối với `401`, nên request bị chặn bắt không thể phát lại.

Request body giới hạn 256 KiB (`413` nếu lớn hơn). Khi body là JSON object, nó trở thành `request.body` của module; body dạng form, text hoặc dạng khác vẫn được chấp nhận và cho module `request.body` rỗng. Trong mọi trường hợp module nhận raw body qua `request.rawBody` và content type của request qua `request.contentType`, nên có thể tự kiểm tra cơ chế chữ ký riêng của hệ thống ngoài. Query parameter và request header an toàn được truyền như mọi lời gọi khác; inbound key và header chữ ký không bao giờ lộ vào code của module.

Module chạy với danh tính `inbound`: `invocation.identity` là `"inbound"`, không có user, và thao tác record dùng danh tính system theo identity policy đã duyệt của module. HTTP status, header và body do module chọn như mọi lời gọi khác, và `Idempotency-Key` hoạt động như bình thường. Module không có active version, hoặc route mà module không định nghĩa, trả `404`.

## Preview chính xác một version

SuperAdmin có thể chạy một version bất biến cụ thể mà không thay đổi active version:

```http
POST /api/v1/ts-projects/order_automation/orders/test
x-req-type: 6
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
