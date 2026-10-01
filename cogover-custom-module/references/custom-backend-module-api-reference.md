# Custom Backend Module API Reference

Tài liệu này mô tả API HTTP public cho Custom Backend Module của Cogover, bao gồm quản lý Project (module) và version, identity policy, Project key, secret, inbound access, background job, Git repository, danh mục Custom Module Action, gọi module production, gọi inbound webhook và preview một version cụ thể.

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

Gửi thêm hai routing header: `x-req-type: 9` cho mọi nhóm, và `x-req-service` theo nhóm API:

| Nhóm API | Header | Quyền bắt buộc |
|---|---|---|
| Gọi production | `x-req-service: 3` | Người dùng Workspace đã xác thực; module phải có active version |
| Quản lý module, version, policy và key | `x-req-service: 4` | TypeScript Project SuperAdmin |
| Preview chính xác một version | `x-req-service: 6` | TypeScript Project SuperAdmin |
| Danh mục Custom Module Action | `x-req-service: 4` | Mọi thành viên đang hoạt động của Workspace |

Thiếu `x-req-type: 9` thì request service `4` bị Authorization Server xử lý như lệnh logout, trả `{"data":{"deletedTokens":N}}` và thu hồi phiên; service `3` trả `{"msg":"Error","r":5000}`; service `6` trả `r: 5001` (`Can not found processor for request: service=6`).

Với `x-req-type: 9`, gateway của Workspace trả nguyên HTTP status, header và body của Runtime, không bọc envelope. Body request có thể gửi kèm `Content-Encoding: gzip`; khi gửi `Accept-Encoding: gzip`, response lớn có thể được nén gzip. Lỗi do chính gateway sinh ra, không phải của Runtime, ví dụ phiên hết hạn, Runtime không khả dụng hoặc hết thời gian chờ, có header response `x-proxy-error: 1` và body `{"r": <mã>, "msg": "<thông báo>"}`.

Giá trị CSRF thường được cấp cùng phiên đăng nhập Cogover. Không đặt `HttpSessionId`, `AuthToken` hoặc CSRF token trong URL hay JSON body.

Quản lý secret, inbound access và job dùng cùng Workspace session và `x-req-service: 4`. Gọi inbound webhook thì khác: không dùng Workspace session lẫn routing header, chỉ dùng inbound credential mô tả ở [Gọi inbound webhook](#gọi-inbound-webhook).

## Quy ước chung

- Request và response body dùng JSON, trừ khi module được gọi trả về content type khác được hỗ trợ.
- Tất cả route quản lý đều dùng `POST`, kể cả thao tác đọc hoặc xóa. Hai route danh mục [Custom Module Action](#custom-module-action-1) dùng `GET` và cũng nhận `POST`.
- Path resource ID như `projectId`, `versionId` và `keyId` gồm 15 chữ cái in hoa hoặc chữ số.
- Timestamp là Unix epoch millisecond.
- API dùng tên field `projectId` cho module trong route quản lý và `projectSlug` cho module đã deploy trong route invocation.
- Slug phải khớp `[A-Za-z_][A-Za-z0-9_]{0,99}` và không thể đổi sau khi tạo.
- `Idempotency-Key` phải khớp `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`.
- Nội dung thông báo do Cogover trả về luôn bằng tiếng Anh.

Lỗi có JSON shape sau, với `Content-Type: application/json; charset=utf-8`. Một số lỗi có thêm field chẩn đoán an toàn như `code`, `reason`, `operation`, `objectSlug`, `fieldSlug`, `objectServerR` hoặc `writesMayHaveCompleted`.

```json
{
  "r": 400,
  "msg": "Invalid resource ID"
}
```

Các HTTP status thường gặp: `400` request không hợp lệ, `401` cần xác thực hoặc phiên hết hạn, `403` thiếu quyền, `404` không tìm thấy resource, `405` HTTP method không được hỗ trợ, `409` xung đột lifecycle hoặc idempotency, `413` request quá lớn, `422` script chạy thất bại, `429` vượt quota, `500` lỗi server không dự kiến và `502`/`503`/`504` lỗi dịch vụ tạm thời. Lỗi server không dự kiến trả `{ "r": 500, "msg": "Internal server error" }`, không kèm chi tiết. Path quản lý không khớp route nào, ví dụ `/api/v1/ts-projects/{projectId}/secrets/unknown/update`, trả `404` với `msg: "TypeScript project management route not found"`.

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
| `POST` | `/api/v1/ts-projects/{projectId}/git/repository` | `201` / `200` |
| `POST` | `/api/v1/ts-projects/{projectId}/git/repository/unlink` | `200` |
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

### Git repository

`x-req-service: 4`. Mọi user đã đăng nhập đều xem được tài khoản Git của chính mình; các endpoint còn lại yêu cầu
SuperAdmin. Xem [Git repository](#git-repository-1).

| Method | Path | Thành công |
|---|---|---:|
| `POST` | `/api/v1/ts-projects/git/overview` | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/get` | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/list` | `200` |
| `POST` | `/api/v1/ts-projects/git/members/list` | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts` | `201` / `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/lock` | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/unlock` | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/delete` | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/repos/list` | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/list` | `200` |
| `POST` | `/api/v1/ts-projects/git/repos` | `201` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}` | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/archive` | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/unarchive` | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/delete` | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/collaborators/list` | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/collaborators` | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/collaborators/remove` | `200` |
| `POST` | `/api/v1/ts-projects/git/tokens/list` | `200` |
| `POST` | `/api/v1/ts-projects/git/tokens` | `201` |
| `POST` | `/api/v1/ts-projects/git/tokens/{tokenId}/delete` | `200` |

### Custom Module Action

`x-req-service: 4`. Mở cho mọi thành viên đang hoạt động của Workspace. Xem [Custom Module Action](#custom-module-action-1).

| Method | Path | Thành công |
|---|---|---:|
| `GET` | `/api/v1/ts-projects/actions?consumer=process\|agent` | `200` |
| `GET` | `/api/v1/ts-projects/actions/{projectSlug}/{actionKey}?consumer=process\|agent` | `200` |

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
x-req-type: 9
x-req-service: 4
Content-Type: application/json
```

```json
{
  "name": "Order automation",
  "description": "Synchronize order data",
  "slug": "order_automation",
  "createGitRepository": true
}
```

`name` bắt buộc và dài tối đa 250 ký tự. `description` không bắt buộc và dài tối đa 2.000 ký tự. Slug phải duy nhất trong Workspace. `createGitRepository` (mặc định `true`) tạo [repository của module](#repository-của-module) cùng lúc với module.

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
  "updated": 1788023000000,
  "git": {
    "status": "LINKED",
    "repository": {
      "id": 42,
      "name": "order_automation",
      "cloneUrl": "https://{WORKSPACE_DOMAIN}/git/example/order_automation.git",
      "webUrl": "https://{WORKSPACE_DOMAIN}/git/example/order_automation"
    }
  }
}
```

`lockVersion` là dấu phiên bản đồng thời dạng opaque; client không được tự thay đổi. Mọi module object (tạo, liệt kê,
đọc, cập nhật và xóa) có `git`, mô tả ở [Repository của module](#repository-của-module).

### Liệt kê module

```http
POST /api/v1/ts-projects/list
x-req-type: 9
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
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

Response là module object ở trên.

### Cập nhật module

```http
POST /api/v1/ts-projects/{projectId}/update
x-req-type: 9
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
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

Thao tác xóa có tính idempotent. Module trả về có `status: "DISABLED"` và không thể được gọi, cập nhật, publish hoặc activate.

### Repository của module

Một module có tối đa một repository trong [organization Git](#git-repository-1) của Workspace, và một repository thuộc
tối đa một module. Field `git` của module object:

| `status` | Ý nghĩa |
|---|---|
| `LINKED` | `repository` có `id`, `name`, `cloneUrl` và `webUrl` của repository |
| `NONE` | Module chưa có repository; `repository` là `null` |
| `DISABLED` | Git chưa được bật ở môi trường của Workspace; `repository` là `null` |

Module mới được tạo repository, trừ khi `createGitRepository` là `false`. Repository đặt tên theo slug; nếu tên đã được
dùng thì thêm `-backend` (`-frontend` với module frontend), rồi hậu tố ngẫu nhiên. Nếu không tạo được repository, ví dụ
khi đã đủ giới hạn repository, module vẫn được tạo (`201`): khi đó riêng response tạo module có `git.error` gồm `code`
và `msg` của [lỗi Git](#mã-lỗi-git), `git.status` là `NONE`, và có thể tạo repository sau. SuperAdmin tạo module cũng
được tạo tài khoản Git nếu chưa có, trừ khi tạo từ phiên SuperAdmin đang thao tác dưới danh nghĩa user khác: khi đó
repository vẫn được tạo nhưng không tạo tài khoản Git.

`POST /api/v1/ts-projects/{projectId}/git/repository` tạo repository cho module chưa có (`201`), hoặc với
`{"repository": "<tên>"}` liên kết một repository có sẵn của organization chưa thuộc module nào (`200`). Response là
object `git`. Lỗi: `409` với `PROJECT_ALREADY_LINKED`, `GIT_REPOSITORY_LINKED`, `GIT_REPOSITORY_LIMIT_REACHED` hoặc
`PROJECT_DISABLED`; `404` với `GIT_REPOSITORY_NOT_FOUND`.

`POST /api/v1/ts-projects/{projectId}/git/repository/unlink` với `{}` bỏ liên kết repository (repository vẫn được giữ)
và trả `git` với `status: "NONE"`; module chưa có repository cũng thành công.

Xóa module thì repository được archive: code được giữ ở chế độ chỉ đọc, và sau đó có thể xoá repository.

## Quản lý version

### Publish version

Trước tiên upload ZIP private qua API upload file của Cogover. Archive phải có `src/main.ts` tại root.

```http
POST /api/v1/ts-projects/{projectId}/versions
x-req-type: 9
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

Tên ZIP dài tối đa 255 ký tự. `fileSize` phải dương, `fileExt` phải là `zip`, `acl` phải là `private` và `idempotencyKey` là bắt buộc. Dùng lại key với publish input khác trả về `409`. File phải là ZIP private đã upload vào chính Workspace đó; `file_id` khác trả về `400` và không tạo version.

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

| `buildErrorCode` | Ý nghĩa |
|---|---|
| `SOURCE_DOWNLOAD_FAILED` | Không tải hoặc xác minh được file ZIP đã upload. |
| `INVALID_PROJECT_ARCHIVE` | ZIP sai cấu trúc hoặc vượt giới hạn. |
| `TYPESCRIPT_COMPILE_FAILED` | Source TypeScript compile không thành công. |
| `INVALID_COMPILED_BUNDLE` | Không nạp được module đã compile, ví dụ vì khai báo `defineTrigger` hoặc `defineJob` ném lỗi khi module được import. |
| `TRIGGER_MANIFEST_INVALID` | Khai báo record trigger không hợp lệ (xem [Đọc một version](#đọc-một-version)). |
| `JOB_MANIFEST_INVALID` | Khai báo background job không hợp lệ, ví dụ job key trùng, biểu thức cron không bao giờ chạy hoặc múi giờ không tồn tại. |
| `ACTION_MANIFEST_INVALID` | Khai báo Custom Module Action không hợp lệ (xem [Custom Module Action](#custom-module-action-1)). |
| `BUILD_FAILED` | Lỗi build khác. |

#### Giới hạn kích thước

| Giới hạn | Giá trị | Kiểm tra |
|---|---|---|
| File ZIP | 20 MiB | khi publish, rồi kiểm tra lại khi build |
| Số entry trong ZIP (file và thư mục) | 512 | `INVALID_PROJECT_ARCHIVE` |
| Tổng dung lượng sau khi giải nén | 20 MiB | `INVALID_PROJECT_ARCHIVE` |
| Dung lượng một file | 5 MiB | `INVALID_PROJECT_ARCHIVE` |
| Số source file được `src/main.ts` import tới | 512 | `TYPESCRIPT_COMPILE_FAILED` |
| Tổng dung lượng các source file đó | 4 MiB | `TYPESCRIPT_COMPILE_FAILED` |
| Bundle JavaScript sau khi compile | 4 MiB | `TYPESCRIPT_COMPILE_FAILED` |

Request có `fileSize` lớn hơn 20 MiB bị từ chối với `400` trước khi tạo version, ví dụ `ZIP file is 25 MiB, which exceeds the 20 MiB limit`. Các giới hạn còn lại làm version chuyển sang `FAILED`, và `buildErrorMessage` nêu giới hạn bị vượt cùng đường dẫn file liên quan (nếu có):

| Trường hợp | `buildErrorMessage` |
|---|---|
| Một file quá lớn | `File "src/data/rates.json" exceeds the 5 MiB per-file limit` |
| Tổng các file quá lớn | `ZIP content exceeds the 20 MiB total size limit after extraction; the limit was reached at "src/vendor/sdk.ts"` |
| Quá nhiều entry | `ZIP contains more than 512 entries; files and directories both count` |
| Một file nén hơn 100:1 | `File "src/data/rates.json" exceeds the 100:1 compression-ratio limit` |
| Quá nhiều source file | `Project exceeds the limit of 512 source files; the limit was reached at src/lib/helpers.ts` |
| Source code quá lớn | `Project source exceeds the 4 MiB total size limit; the limit was reached at src/lib/tables.ts` |
| Bundle quá lớn | `Compiled JavaScript exceeds the 4 MiB limit` |

Chỉ các file được `src/main.ts` import trực tiếp hoặc gián tiếp mới tính vào giới hạn source; `@cogover/sdk` được bundle kèm không tính. Mỗi invocation đều nạp toàn bộ bundle, nên bundle nhỏ hơn cũng khởi động nhanh hơn. 1 MiB bằng 1.048.576 byte. Cogover Dev CLI kiểm tra các giới hạn ZIP trước khi upload ZIP do CLI tạo. Bước upload file của Workspace áp dụng dung lượng tối đa riêng cho file ZIP (field Files của object Contract), có thể thấp hơn giới hạn ZIP ở trên; khi đó upload bị từ chối trước khi tạo version.

### Liệt kê version

```http
POST /api/v1/ts-projects/{projectId}/versions/list
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

Response là JSON array các version object.

### Đọc một version

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}
x-req-type: 9
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

Hãy xem lại `triggerManifest` trước khi activate version: khi version đã active, các trigger của nó chạy cho mọi thao tác tạo, sửa hoặc xoá bản ghi của các object được liệt kê và thoả điều kiện, từ bất kỳ nguồn nào. Trigger có `"timing": "beforeChange"` chạy trước khi thay đổi được lưu và có thể từ chối hoặc điều chỉnh thay đổi. Trigger có `"timing": "afterChange"` chạy bất đồng bộ sau khi thay đổi đã được lưu, theo cơ chế best-effort, và không thể từ chối hay sửa thay đổi đó. Version có khai báo trigger không hợp lệ kết thúc ở `FAILED` với `buildErrorCode: "TRIGGER_MANIFEST_INVALID"`: ví dụ object hoặc field không tồn tại, key trùng nhau, `writableFields` có field không ghi được (Formula, đánh số tự động, Rollup Summary, field read-only khác hoặc field hệ thống), hoặc hơn 20 trigger `beforeChange` trên cùng một object.

### Activate version

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/activate
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

Version phải ở trạng thái `READY` và đã được giữ lại. Activate version cũng kích hoạt các record trigger trong `triggerManifest` của nó và gỡ trigger của version active trước đó; deactivate module sẽ gỡ các trigger này. Activate version độc lập với việc cấp quyền `data.asSystem()` hoặc `data.asUser()`. Module trả về có `status: "ACTIVE"` và `activeVersionId` trỏ tới version đã chọn.

### Deactivate module

```http
POST /api/v1/ts-projects/{projectId}/deactivate
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

Module trả về có `status: "DRAFT"` và `activeVersionId: null`. Các version hiện có vẫn được giữ lại. Deactivate gỡ các record trigger và lịch job của module; lần chạy job còn đang chờ sẽ thất bại với `lastErrorCode: "JOB_PROJECT_UNAVAILABLE"` khi tới hạn.

### Xóa version

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/delete
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

Không thể xóa active version. Hãy activate version khác hoặc deactivate module trước. Version trả về có `deleted: true`.

## Identity policy

Identity policy kiểm soát caller nào được dùng quyền ủy quyền `data.asSystem()` hoặc `data.asUser()` từ Custom Backend Module, module được gửi email bằng `email.send()` từ những hộp thư nào, `fetch()` được gọi những origin HTTPS nào trên port khác 443, và module được khởi chạy những Process, AI Agent nào bằng `processes.start()`, `agents.start()`. Policy không chặn việc chạy module thông thường hoặc truy cập dữ liệu theo quyền mặc định của caller. Policy đang chỉnh sửa của module và snapshot bất biến đã duyệt cho version là hai resource riêng. Cập nhật policy đang chỉnh sửa không làm thay đổi snapshot đã duyệt trước đó.

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

Policy phải có ít nhất một trong `data.asSystem`, `data.asUser`, `email`, `fetch`, `processes` và `agents`.

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

### Origin fetch trên port khác

Mặc định `fetch()` chỉ gọi được URL HTTPS công khai trên port 443. Mục `fetch` (không bắt buộc) duyệt các origin HTTPS chính xác trên port khác, ví dụ hệ thống on-premise công bố tại `https://erp.example.com:9899`:

```json
{
  "schemaVersion": 2,
  "callerPersonnelIds": {
    "mode": "ALL",
    "personnelIds": []
  },
  "allowInternalSystem": false,
  "fetch": {
    "allowedOrigins": ["https://erp.example.com:9899"]
  }
}
```

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `allowedOrigins` | mảng string | 1 đến 20 origin dạng `https://host:port`. Origin trùng được bỏ qua. `null` và mảng rỗng bị từ chối. |

- Mỗi origin phải dùng `https`, host là tên DNS có ít nhất hai nhãn (tên miền quốc tế ghi ở dạng `xn--`) và port ghi rõ từ 1024 đến 65535. Path khác `/`, query, fragment, thông tin người dùng, wildcard, địa chỉ IP và port 443 (không cần duyệt) bị từ chối với HTTP `400`. Host được lưu ở dạng chữ thường, không kèm `/` ở cuối.
- Không duyệt được các port: 2375, 2376, 2379, 2380, 2381, 4001, 6443, 6444, 8200, 8201, 8500, 8501, 9345, 10249, 10250, 10255 đến 10260, 16443 và 30000 đến 32767.
- Việc duyệt chỉ bỏ giới hạn port 443 cho đúng các origin được liệt kê. Mọi quy tắc khác của `fetch()` vẫn áp dụng: HTTPS với chứng chỉ hợp lệ cho host, đích chỉ được phân giải tới địa chỉ công khai không bị nền tảng giữ lại, không theo redirect và các giới hạn request. Đích phân giải tới địa chỉ bị từ chối lỗi `FETCH_FAILED`; URL trên port chưa được duyệt lỗi `FETCH_BLOCKED`.
- Khác các mục còn lại, `fetch` không phụ thuộc `callerPersonnelIds` hay `allowInternalSystem`: mọi execution của version đã duyệt đều gọi được các origin trong danh sách, kể cả record trigger, job và inbound webhook. Development session dùng policy đang chỉnh sửa của module khi policy ở trạng thái `ACTIVE`.
- Mục này chỉ có hiệu lực qua version snapshot đã duyệt. Đổi `allowedOrigins` tạo revision policy mới và phải duyệt lại; vô hiệu hoá policy sẽ gỡ việc duyệt.
- Khi lưu policy, backend không kiểm tra DNS hay khả năng kết nối; mỗi request được kiểm tra lúc gửi.
- Credential secret chỉ được gửi tới port khác khi `allowedHosts` của nó ghi port đó (xem [Secret](#secret-1)).
- Request rời Cogover từ các địa chỉ outbound dùng chung với Workspace khác. Cho phép các địa chỉ đó trên firewall của hệ thống đích không xác định được Workspace của bạn: hãy bảo vệ endpoint bằng cơ chế xác thực riêng và gửi kèm bằng credential secret.

### Process và AI Agent

Mục `processes` (không bắt buộc) cho phép module khởi chạy Process bằng `processes.start()` và đọc các lượt chạy do chính module khởi tạo bằng `processes.get()`. Mục `agents` (không bắt buộc) cho phép module chạy AI Agent bằng `agents.start()` và đọc các lượt chạy do chính module khởi tạo bằng `agents.get()`. Thiếu mục nào thì lời gọi tương ứng lỗi `PermissionDeniedError` với `details.reason` là `"PROCESSES_NOT_ALLOWED"` hoặc `"AGENTS_NOT_ALLOWED"`.

```json
{
  "schemaVersion": 2,
  "callerPersonnelIds": {
    "mode": "ALL",
    "personnelIds": []
  },
  "allowInternalSystem": false,
  "processes": {
    "processes": {
      "mode": "ONLY",
      "processInfoIds": ["PIXXXXXXXXXXXX"]
    },
    "allowSystem": false
  },
  "agents": {
    "agents": {
      "mode": "ALL",
      "agentIds": []
    },
    "allowSystem": false,
    "maxRunsPerDay": 200,
    "allowAutoApprove": false
  }
}
```

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `processes.processes` | selector | `mode` (`ALL`, `ALL_EXCEPT`, `ONLY`) và `processInfoIds`: ID của Process, không phải ID version hay ID lượt chạy của Process. |
| `processes.allowSystem` | boolean | Cho phép execution không có người dùng (danh tính system) khởi chạy các Process đã chọn. Mặc định `false`. |
| `agents.agents` | selector | `mode` và `agentIds`: ID của AI Agent. |
| `agents.allowSystem` | boolean | Cho phép execution không có người dùng chạy các agent đã chọn; khi đó agent chạy bằng danh tính mặc định của chính agent. Mặc định `false`. |
| `agents.maxRunsPerDay` | số nguyên | Số lần gọi `agents.start()` tối đa của module trong một ngày UTC, từ 1 đến 10000. Mặc định `200`. |
| `agents.allowAutoApprove` | boolean | Cho phép `agents.start()` với `approvalPolicy: "autoApprove"`, tức là chạy các tool cần người phê duyệt của agent mà không cần phê duyệt. Mặc định `false`; execution không có người dùng không bao giờ dùng được. Không bật thì lời gọi đó lỗi `PermissionDeniedError` với `details.reason` là `"AGENT_AUTO_APPROVE_NOT_ALLOWED"`. |

- Mỗi selector liệt kê tối đa 200 ID, mỗi ID khớp `[A-Za-z0-9_-]{1,64}`. `ONLY` cần ít nhất một ID, `ALL` không được liệt kê ID nào, ID trùng được bỏ qua. `allowSystem` và `allowAutoApprove` phải là boolean JSON. Giá trị sai bị từ chối với HTTP `400`.
- Giống `fetch`, hai mục này không phụ thuộc `callerPersonnelIds`: mọi execution của version đã duyệt đều dùng được. Khi execution có người dùng, Process hoặc agent chạy với danh tính người đó và Cogover vẫn kiểm tra người đó có quyền khởi chạy Process hoặc chạy agent đó.
- Đổi một trong hai mục tạo revision policy mới và phải duyệt lại.
- Module vượt `maxRunsPerDay` nhận `RateLimitError`.

### Lưu hoặc đọc policy đang chỉnh sửa

```http
POST /api/v1/ts-projects/{projectId}/identity-policy
x-req-type: 9
x-req-service: 4
Content-Type: application/json

<policy-object>
```

Lưu nội dung thay đổi làm tăng revision và đưa editable policy về `DRAFT`. Lưu nội dung giống hệt policy đã lưu không thay đổi gì khi policy ở `DRAFT` hoặc `ACTIVE`: revision và status giữ nguyên. Lưu nội dung giống hệt vào policy `DISABLED` đưa policy về `DRAFT` với cùng revision.

```http
POST /api/v1/ts-projects/{projectId}/identity-policy/get
x-req-type: 9
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
x-req-type: 9
x-req-service: 4
Content-Type: application/json
```

Response là editable policy object có `status` bằng `ACTIVE` hoặc `DISABLED`. Cả hai thao tác có tính idempotent: gọi cho policy đã ở đúng status đó trả policy không đổi, và policy đã disable có thể được activate lại với cùng revision. Disable policy cũng disable các version snapshot đã duyệt, khiến chúng từ chối privileged identity operation. Activate lại editable policy không bật lại các snapshot đó; hãy duyệt lại version. Duyệt một version cũng đặt editable policy thành `ACTIVE`.

### Duyệt và đọc version snapshot

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/identity-policy/approve
x-req-type: 9
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
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

Endpoint tương thích dưới đây trước tiên lưu policy được gửi lên, sau đó duyệt policy cho version:

```http
POST /api/v1/ts-projects/{projectId}/versions/{versionId}/identity-policy
x-req-type: 9
x-req-service: 4
Content-Type: application/json

<policy-object>
```

## Project key

Project key cấp quyền phát triển local cho một module và một caller personnel identity. `permissionCeiling` chỉ có thể thu hẹp quyền hiệu lực.

### Tạo Project key

```http
POST /api/v1/ts-projects/{projectId}/keys
x-req-type: 9
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
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

List trả `{ "items": [...], "total": 1 }`. Hai endpoint này không trả `projectKey`. Active key đã hết hạn được hiển thị với `status: "EXPIRED"`.

### Cập nhật Project key

```http
POST /api/v1/ts-projects/{projectId}/keys/{keyId}/update
x-req-type: 9
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
x-req-type: 9
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
x-req-type: 9
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
| `kind` | Không bắt buộc, mặc định `OPAQUE`. `OPAQUE` (code của module đọc được), `BEARER` (`Authorization: Bearer <value>`), `BASIC` (`Authorization: Basic base64(<value>)`, với `value` dạng `user:password`) hoặc `HEADER` (`<headerName>: <value>`). |
| `value` | Bắt buộc. Chuỗi không rỗng, tối đa 8.192 ký tự. Giá trị credential không được chứa ký tự điều khiển, và header do nó tạo ra không được vượt 8.192 ký tự: giá trị `BEARER` tối đa 8.185 ký tự, giá trị `BASIC` tối đa 6.138 byte UTF-8, giá trị `HEADER` tối đa 8.192 ký tự. Giá trị dài hơn bị từ chối với `400` khi lưu. |
| `headerName` | Bắt buộc với `HEADER`, không được gửi với loại khác. Tên header mang giá trị. |
| `allowedHosts` | Bắt buộc và không rỗng với `BEARER`, `BASIC`, `HEADER`; không được gửi với `OPAQUE`. Tối đa 20 phần tử. Mỗi phần tử là một host chính xác hoặc `*.suffix`, khớp mọi host kết thúc bằng `.suffix`, có thể kèm `:port`. Phần tử không có port chỉ khớp port 443; `host:443` được lưu thành `host`. Port khác phải là port mà identity policy duyệt được (xem [Origin fetch trên port khác](#origin-fetch-trên-port-khác)); ghi port ở đây không có nghĩa là origin đã được duyệt. Credential chỉ được gửi tới host và port khớp. |
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
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

List trả `{ "items": [...], "total": 1 }` gồm metadata của secret. Hai endpoint này không trả giá trị.

### Cập nhật secret

```http
POST /api/v1/ts-projects/{projectId}/secrets/{secretId}/update
x-req-type: 9
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
x-req-type: 9
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
x-req-type: 9
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
| `hmac` | Bắt buộc với `HMAC`, không được gửi với `KEY`. `secret` (bắt buộc, 8 đến 1.024 ký tự in được) là signing secret mà hệ thống ngoài dùng; `header` (bắt buộc) là request header mang chữ ký; `encoding` là `HEX` (mặc định) hoặc `BASE64`; `prefix` (không bắt buộc, tối đa 32 ký tự) là đoạn text hệ thống ngoài đặt trước chữ ký đã mã hóa, ví dụ `sha256=`; `timestampHeader` (không bắt buộc, khác `header`) bật chống replay như mô tả bên dưới, và `toleranceSeconds` (1 đến 86.400, mặc định 300) cần có `timestampHeader`. |

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
  "url": "/api/v1/ts-projects/order_automation/hooks/TSIXXXXXXXXXXXX",
  "inboundKey": "cog_ik_TSIXXXXXXXXXXXX_<secret>"
}
```

Với `authMode: "HMAC"`, `secretHint` là `null` và `hmac` trả lại `header`, `encoding`, `prefix`, `timestampHeader`, `toleranceSeconds`; signing secret không bao giờ được trả về. `url` là path gốc của inbound access, `/api/v1/ts-projects/{projectSlug}/hooks/{inboundId}`, tương đối với origin của Workspace; không chứa origin lẫn `routePrefix`. Hệ thống ngoài gọi `https://{WORKSPACE_DOMAIN}` nối với `url` và phần route sau `/hooks`, ví dụ `.../hooks/TSIXXXXXXXXXXXX/payments` cho route `/hooks/payments`.

### Liệt kê hoặc đọc inbound access

```http
POST /api/v1/ts-projects/{projectId}/inbound/list
POST /api/v1/ts-projects/{projectId}/inbound/{inboundId}
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

List trả `{ "items": [...], "total": 1 }`. Hai endpoint này không trả `inboundKey` hay HMAC secret. Inbound access đã hết hạn được hiển thị với `status: "EXPIRED"`.

### Cập nhật inbound access

```http
POST /api/v1/ts-projects/{projectId}/inbound/{inboundId}/update
x-req-type: 9
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

Gửi ít nhất một field. Không thể đổi `authMode`. `hmac` chỉ được chấp nhận với inbound access loại `HMAC` và được gộp vào cấu hình HMAC hiện có: member không gửi giữ giá trị hiện tại, nên ví dụ trên thay secret và header, giữ nguyên encoding, prefix và cấu hình timestamp. Gửi `prefix: null` để bỏ prefix. Để tắt chống replay, gửi cả `timestampHeader: null` và `toleranceSeconds: null`; chỉ gửi `timestampHeader: null` bị từ chối với `400` khi tolerance đang được cấu hình. Trả về metadata đã cập nhật.

### Rotate hoặc revoke inbound access

```http
POST /api/v1/ts-projects/{projectId}/inbound/{inboundId}/rotate
POST /api/v1/ts-projects/{projectId}/inbound/{inboundId}/revoke
x-req-type: 9
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
x-req-type: 9
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

Mọi field đều không bắt buộc. `status` là `PENDING`, `RUNNING`, `SUCCEEDED` hoặc `FAILED`; `page` bắt đầu từ 1 và `pageSize` (mặc định 20) tối đa 200. Trang có offset lớn hơn 2.147.483.647 bị từ chối với `400`. Trả `{ "items": [...], "page": 1, "pageSize": 50, "totalItems": 3 }`, mới nhất trước.

```http
POST /api/v1/ts-projects/{projectId}/jobs/runs/{runId}
x-req-type: 9
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
  "enqueuedBy": "rpc",
  "actorPersonnelId": "PERXXXXXXXXXXXX",
  "idempotencyKey": "recalc:daily",
  "payloadBytes": 42,
  "lastErrorCode": "RETRYABLE",
  "lastErrorMessage": "The job reported a temporary failure",
  "created": 1788022000000,
  "updated": 1788024000000,
  "startedAt": 1788023900000,
  "finishedAt": 1788024000000,
  "durationMs": 1830,
  "usage": {
    "capabilityCalls": 212,
    "localCalls": 0,
    "recordsRead": 4200,
    "recordsWritten": 0
  }
}
```

`source` là `ENQUEUE` hoặc `SCHEDULE`. `enqueuedBy` cho biết nguồn tạo lần chạy: `rpc` hoặc `http` với lời gọi module (lời gọi qua domain Workspace được ghi là `rpc`), `trigger:<key>`, `job:<key>`, `inbound:<inboundId>`, `action:<key>` với job do một action mà Process hoặc AI Agent gọi enqueue, `process:<instanceId>` với job `onComplete` của `processes.start`, `agent:<runId>` với job `onResult` của `agents.start`, `schedule`, `development`, hoặc `management` với endpoint enqueue bên dưới. `actorPersonnelId` là nhân sự mà lần chạy thực thi dưới danh nghĩa, hoặc `null` với lần chạy không có user. Payload của lần chạy không bao giờ được trả về; chỉ có `payloadBytes`. Lần chạy đã kết thúc được giữ 7 ngày.

`lastErrorCode` và `lastErrorMessage` mô tả lần thử thất bại gần nhất. Message là đoạn text tiếng Anh cố định do Cogover chọn; không bao giờ chứa message lỗi do module ném ra hay dữ liệu payload.

`durationMs` và `usage` mô tả lần thử gần nhất: thời gian chạy và phần đã dùng của các ngân sách mỗi lần thực thi của job (capability call, lời gọi cục bộ như `crypto`, record đọc và record ghi; xem "Giới hạn của một lần thực thi" trong SDK API reference). `usage` là `null` với lần thử không chạy tới handler, và cả hai là `null` với lần thử kết thúc trước khi Cogover ghi nhận các giá trị này.

| `lastErrorCode` | Ý nghĩa |
|---|---|
| `RETRYABLE` | Handler ném `RetryableError`; lần chạy được thử lại khi còn lượt. |
| `JOB_TIMEOUT` | Lần thử vượt `timeoutMs` của job; được thử lại khi còn lượt. |
| `JOB_CAPACITY_EXHAUSTED` | Không còn năng lực runtime; được thử lại khi còn lượt. |
| `JOB_EXECUTION_FAILED` | Handler ném lỗi khác hoặc vượt giới hạn (không thử lại), hoặc gặp lỗi nền tảng (được thử lại). |
| `JOB_NOT_DEFINED` | Active version không còn khai báo job này. |
| `JOB_PROJECT_UNAVAILABLE` | Module hoặc active version của nó không còn khả dụng, ví dụ sau khi deactivate. |
| `JOB_ACTOR_UNAVAILABLE` | User mà lần chạy thực thi dưới danh nghĩa không còn là thành viên Workspace. |
| `JOB_ABANDONED` | Lần thử bị gián đoạn và không còn lượt thử. |

### Enqueue một lần chạy job

```http
POST /api/v1/ts-projects/{projectId}/jobs/enqueue
x-req-type: 9
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

`jobKey` phải được active version khai báo. `payload` là JSON không bắt buộc, tối đa 65.536 byte; `delayMs` không bắt buộc, từ 0 đến 2.592.000.000 (30 ngày); `idempotencyKey` không bắt buộc và khớp `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`. HTTP `201` trả `{ "runId": "TSJXXXXXXXXXXXX", "duplicate": false }`; `duplicate: true` nghĩa là đã tồn tại lần chạy cùng job và cùng idempotency key, và `runId` là lần chạy đó. Lần chạy thực thi dưới danh nghĩa Super Admin đã gọi endpoint này, như một lời gọi module do chính user đó thực hiện: `data.object()` dùng quyền của họ, và lần chạy được liệt kê với `enqueuedBy: "management"` cùng `actorPersonnelId` của họ. Module phải có active version khai báo `jobKey` và tối đa 10.000 lần chạy đang chờ hoặc đang chạy; nếu không trả `409` (kèm `code: "JOB_NOT_DEFINED"` khi job không được khai báo) hoặc `429`.

### Liệt kê lịch job

```http
POST /api/v1/ts-projects/{projectId}/jobs/schedules/list
x-req-type: 9
x-req-service: 4
Content-Type: application/json

{}
```

Trả `{ "items": [...], "total": 1 }` với một phần tử cho mỗi job có lịch của active version, sắp theo `jobKey`:

```json
{
  "jobKey": "cancel_stale_orders",
  "cron": "0 2 * * *",
  "timezone": "Asia/Ho_Chi_Minh",
  "status": "ACTIVE",
  "nextRunAt": 1788037200000,
  "lastRunAt": 1787950800000,
  "timeoutMs": 30000,
  "maxAttempts": 5,
  "created": 1788023000000,
  "updated": 1788023000000
}
```

`timezone` là ID múi giờ đã chuẩn hoá, nên offset khai báo là `UTC+7` được liệt kê là `UTC+07:00`; giá trị là `UTC` khi job không khai báo múi giờ. `lastRunAt` là thời điểm theo lịch gần nhất đã tạo lần chạy, hoặc `null`. `timeoutMs` và `maxAttempts` là giá trị mỗi lần chạy theo lịch nhận được. Lịch được tạo, cập nhật và gỡ khi activate version và khi deactivate module; không chỉnh sửa được tại đây. Deactivate module sẽ gỡ các lịch của module. Lịch không còn tính được thời điểm chạy kế tiếp bị chuyển sang `DISABLED` cho tới khi activate version khác.

## Theo dõi toàn workspace

Các endpoint chỉ đọc bổ sung này dùng phiên Workspace, `x-req-type: 9`,
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

## Git repository

Mỗi Workspace có một Git server tại `https://{WORKSPACE_DOMAIN}/git/`: giao diện web gồm repository, pull request và
code review, cùng Git over HTTPS. User đã đăng nhập Workspace mở giao diện web bằng chính session Cogover, không có
bước đăng nhập Git riêng. Chỉ user đã có tài khoản Git mới dùng được, và chỉ SuperAdmin tạo, khoá và xoá tài khoản Git.
Session mà SuperAdmin đang thao tác dưới danh nghĩa user khác không mở được giao diện web Git (`403`). Đăng nhập, mật
khẩu, xác thực hai lớp, địa chỉ email và việc là thành viên organization của Workspace đều theo tài khoản Cogover: các
trang thiết lập Git tương ứng hiện "Managed by Cogover" (`403`). Profile Git chỉ đọc: tên theo tài khoản Cogover sau
vài phút, và mục **Settings** mở trang access token. Không dùng được SSH key, GPG key, chặn user hay organization khác;
mỗi Workspace có đúng một organization Git.

Mọi endpoint dưới đây dùng Workspace session, `x-req-type: 9` và `x-req-service: 4`. Mọi user đã đăng nhập đều xem
được tài khoản Git của chính mình; các endpoint còn lại yêu cầu SuperAdmin.

| Method | Path | Quyền | Thành công |
|---|---|---|---:|
| `POST` | `/api/v1/ts-projects/git/overview` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/get` | Tài khoản của mình: mọi user. Của người khác: SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/list` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/members/list` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts` | SuperAdmin | `201` vừa tạo, `200` đã có |
| `POST` | `/api/v1/ts-projects/git/accounts/lock` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/unlock` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/delete` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/accounts/repos/list` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/list` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/repos` | SuperAdmin | `201` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/archive` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/unarchive` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/delete` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/collaborators/list` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/collaborators` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/repos/{repository}/collaborators/remove` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/tokens/list` | SuperAdmin | `200` |
| `POST` | `/api/v1/ts-projects/git/tokens` | SuperAdmin | `201` |
| `POST` | `/api/v1/ts-projects/git/tokens/{tokenId}/delete` | SuperAdmin | `200` |

Field lạ trong body trả `400`. Lỗi bị từ chối có thêm `code` (bảng ở [Mã lỗi Git](#mã-lỗi-git)) bên cạnh `r` và
`msg`. Khi Git chưa được bật ở môi trường của Workspace, mọi endpoint trả `404` với `code: "GIT_DISABLED"`, riêng
endpoint tổng quan trả `{"enabled": false}`.

Phiên SuperAdmin đang thao tác dưới danh nghĩa user khác chỉ đọc được; mọi endpoint ở bảng trên tạo, sửa hoặc xoá tài
khoản, repository, quyền hay token đều trả `403` với `code: "IMPERSONATION_NOT_ALLOWED"`. Repository của module vẫn
quản lý được từ phiên này; xem [Repository của module](#repository-của-module).

### Tổng quan Git

`POST /api/v1/ts-projects/git/overview` với `{}`:

```json
{
  "enabled": true,
  "organization": "example",
  "webUrl": "https://{WORKSPACE_DOMAIN}/git/example",
  "repositoryCount": 3,
  "repositoryLimit": 100,
  "myAccount": {"accountId": "AC00000000101", "exists": false, "organization": "example"}
}
```

`organization` và `webUrl` là `null` cho tới khi Workspace có tài khoản Git đầu tiên. `myAccount` là
[tài khoản Git](#object-tài-khoản-git) của user đang đăng nhập. `repositoryCount` đếm mọi repository của organization,
kể cả repository đã archive và repository của project.

### Object tài khoản Git

```json
{
  "accountId": "AC00000000101",
  "exists": true,
  "username": "jane.doe-example",
  "status": "ACTIVE",
  "memberActive": true,
  "superAdmin": false,
  "organizationOwner": false,
  "organization": "example",
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "personnel": {"id": "PE000000000101", "code": "NV0001", "name": "Jane Doe"},
  "created": 1790640000000,
  "createdByAccountId": "AC00000000100"
}
```

| Field | Ý nghĩa |
|---|---|
| `exists` | `true` với tài khoản đang dùng: `ACTIVE` hoặc `LOCKED` |
| `status` | `ACTIVE`, `LOCKED` (chặn đăng nhập, giữ quyền và token) hoặc `DELETED`. Không có khi user chưa từng có tài khoản |
| `memberActive` | `false` khi user đã rời Workspace hoặc không còn hoạt động ở đó; Git khi đó tự chặn đăng nhập |
| `superAdmin` | User là SuperAdmin của Workspace |
| `organizationOwner` | Tài khoản đang hoạt động và sở hữu mọi repository của organization (SuperAdmin) |
| `personnel` | Nhân sự gắn với user, hoặc `null` |

`name`, `email`, `personnel`, `memberActive` và `superAdmin` luôn có. `username`, `status` và `organization` có khi
user đã có tài khoản; `organizationOwner`, `created` và `createdByAccountId` chỉ có khi tài khoản chưa bị xoá.

### Xem tài khoản Git

`POST /api/v1/ts-projects/git/accounts/get`, `accountId` không bắt buộc. Không truyền thì endpoint trả lời cho user
đang đăng nhập. User không phải SuperAdmin xem tài khoản của người khác nhận `403`.

```json
{"accountId": "AC00000000101"}
```

Response là một [object tài khoản Git](#object-tài-khoản-git).

### Liệt kê tài khoản Git

`POST /api/v1/ts-projects/git/accounts/list`:

```json
{"page": 1, "pageSize": 20, "keyword": "jane", "status": "LOCKED"}
```

`page` mặc định 1, `pageSize` mặc định 20 (tối đa 100). `keyword` (không bắt buộc, tối đa 100 ký tự) tìm theo
username, họ tên hoặc email. `status` lọc một trạng thái (`ACTIVE`, `LOCKED` hoặc `DELETED`); không truyền thì trả tài
khoản đang hoạt động và đang khoá, mới nhất trước. Response gồm `items` ([object tài khoản Git](#object-tài-khoản-git)),
`page`, `pageSize`, `totalItems`, `totalPages` và `organization`.

### Liệt kê thành viên Workspace

`POST /api/v1/ts-projects/git/members/list` liệt kê thành viên đang hoạt động của Workspace, để chọn người được cấp tài
khoản Git:

```json
{"page": 1, "pageSize": 20, "keyword": "jane", "hasGitAccount": false}
```

`keyword` tìm theo họ tên hoặc email. `hasGitAccount` lọc thành viên đã có (`true`) hoặc chưa có (`false`) tài khoản
đang hoạt động hoặc đang khoá; thành viên có tài khoản đã bị xoá được tính là chưa có.

```json
{
  "items": [
    {
      "accountId": "AC00000000101",
      "name": "Jane Doe",
      "email": "jane.doe@example.com",
      "personnel": {"id": "PE000000000101", "code": "NV0001", "name": "Jane Doe"},
      "superAdmin": false,
      "gitAccount": null
    }
  ],
  "page": 1,
  "pageSize": 20,
  "totalItems": 1,
  "totalPages": 1
}
```

`gitAccount` là `null` hoặc `{"username": "...", "status": "ACTIVE|LOCKED|DELETED"}`.

### Tạo tài khoản Git

`POST /api/v1/ts-projects/git/accounts` tạo tài khoản Git cho một member đang hoạt động của Workspace, nếu chưa có.
Mỗi user có tối đa một tài khoản Git trong một Workspace.

```json
{"accountId": "AC00000000101"}
```

| Kết quả | Status | Response |
|---|---:|---|
| Tạo mới | `201` | [Object tài khoản](#object-tài-khoản-git) và `"created": true` |
| Đã có, đang hoạt động hoặc đang khoá | `200` | Object tài khoản và `"created": false`; tài khoản đang khoá vẫn khoá |
| Đã bị xoá trước đó | `200` | Khôi phục với username cũ, không có quyền và token: `"created": false`, `"restored": true` |

Tài khoản đầu tiên của Workspace tạo luôn organization của Workspace. Tài khoản của SuperAdmin được thêm vào nhóm owner
của organization, và nhóm này tự cập nhật khi quyền SuperAdmin thay đổi. `404` với `MEMBER_NOT_ACTIVE` nghĩa là
`accountId` không phải member đang hoạt động của Workspace.

### Khoá, mở khoá hoặc xoá tài khoản Git

Mỗi endpoint nhận `{"accountId": "..."}`, trả [object tài khoản](#object-tài-khoản-git), và vẫn thành công khi tài
khoản đã ở trạng thái được yêu cầu.

- `POST /api/v1/ts-projects/git/accounts/lock` chặn ngay mọi lần đăng nhập của tài khoản, cả web lẫn Git over HTTPS.
  Quyền trên repository và access token được giữ; SuperAdmin bị khoá mất quyền owner cho tới khi được mở khoá.
- `POST /api/v1/ts-projects/git/accounts/unlock` cho đăng nhập lại. User không còn là member đang hoạt động của
  Workspace thì không mở khoá được: `409` với `MEMBER_NOT_ACTIVE`.
- `POST /api/v1/ts-projects/git/accounts/delete` chặn đăng nhập, gỡ mọi quyền trên repository và mọi team, thu hồi mọi
  access token. Response có thêm `removedPermissions` và `revokedTokens`. Username vẫn được giữ cho chính user đó:
  commit giữ tác giả, và tạo lại tài khoản sẽ khôi phục nó.

User chưa có tài khoản (hoặc, với khoá và mở khoá, có tài khoản đã bị xoá) nhận `404` với `GIT_ACCOUNT_NOT_FOUND`.

### Repository của một thành viên

`POST /api/v1/ts-projects/git/accounts/repos/list` với `{"accountId": "..."}`:

```json
{
  "accountId": "AC00000000101",
  "username": "jane.doe-example",
  "organizationOwner": false,
  "items": [{"repository": "order_automation", "permission": "write"}]
}
```

`items` liệt kê repository được cấp cho user và [mức quyền](#quyền-trên-repository) trên từng repository. Owner của
organization có mọi repository: khi đó `organizationOwner` là `true` và `items` rỗng.

### Object repository

```json
{
  "id": 42,
  "name": "order_automation",
  "description": "",
  "empty": false,
  "archived": false,
  "defaultBranch": "main",
  "updated": 1790640000000,
  "cloneUrl": "https://{WORKSPACE_DOMAIN}/git/example/order_automation.git",
  "webUrl": "https://{WORKSPACE_DOMAIN}/git/example/order_automation",
  "project": {"type": "BACKEND", "id": "TSPXXXXXXXXXXXX", "name": "Order automation", "slug": "order_automation",
    "status": "ACTIVE"}
}
```

`project` là `null` với repository không thuộc project nào; nếu có thì `type` là `BACKEND` hoặc `FRONTEND`, `status` là
trạng thái của project (`DRAFT`, `ACTIVE` hoặc `DISABLED`). Repository có thể được đổi tên trên giao diện web; nó vẫn là
repository của project đó.

### Liệt kê repository

`POST /api/v1/ts-projects/git/repos/list`:

```json
{"page": 1, "pageSize": 20, "keyword": "order", "archived": false}
```

`page` mặc định 1, `pageSize` mặc định 20 (tối đa 50). `keyword` tìm theo tên; `archived` lọc repository đã archive
(`true`) hoặc đang hoạt động (`false`). Response gồm `organization`, `items` ([object repository](#object-repository)),
`page`, `pageSize`, `totalItems`, `repositoryCount` và `repositoryLimit`.

### Tạo, xem, archive hoặc xoá repository

| Endpoint | Body | Thành công | Lỗi riêng |
|---|---|---|---|
| `POST /api/v1/ts-projects/git/repos` | `{"name", "description"}` | `201` object repository | `400` tên sai; `409` `GIT_REPOSITORY_EXISTS`, `GIT_REPOSITORY_LIMIT_REACHED` |
| `POST /api/v1/ts-projects/git/repos/{repository}` | `{}` | `200` object repository | `404` `GIT_REPOSITORY_NOT_FOUND` |
| `POST /api/v1/ts-projects/git/repos/{repository}/archive` | `{}` | `200` object repository | `404` |
| `POST /api/v1/ts-projects/git/repos/{repository}/unarchive` | `{}` | `200` object repository | `404` |
| `POST /api/v1/ts-projects/git/repos/{repository}/delete` | `{"confirm": "<repository>"}` | `200` `{"name", "deleted": true}` | `400` `CONFIRM_MISMATCH`; `409` `GIT_REPOSITORY_LINKED` |

- Tên repository gồm 1 đến 100 chữ cái, chữ số, `.`, `_` hoặc `-`, không bắt đầu bằng `.`, không kết thúc bằng `.git`
  và không phải `list`. Tên là duy nhất, không phân biệt hoa thường.
- Repository mới là private và rỗng (không có README, nên lần push đầu từ repository local không bao giờ xung đột);
  nhánh mặc định là `main`.
- Repository đã archive chỉ đọc. Xoá repository xoá cả lịch sử và không khôi phục được; repository thuộc project chưa bị
  xoá thì không xoá được.
- Một Workspace có tối đa `repositoryLimit` repository (mặc định 100), kể cả repository đã archive. Repository tạo trên
  giao diện web cũng được tính và bị từ chối khi đã đủ giới hạn.

### Quyền trên repository

SuperAdmin sở hữu mọi repository. Các endpoint dưới đây cấp cho user khác quyền trên một repository của organization
Workspace, với một trong ba mức:

| `permission` | Được làm |
|---|---|
| `read` | Clone, xem code, tạo issue và comment pull request |
| `write` | Mọi quyền của `read`, thêm push và merge pull request theo branch protection |
| `admin` | Mọi quyền của `write`, thêm cài đặt repository, collaborator và branch protection |

`POST /api/v1/ts-projects/git/repos/{repository}/collaborators` thêm user hoặc đổi mức quyền của họ:

```json
{"accountId": "AC00000000101", "permission": "write"}
```

```json
{
  "organization": "example",
  "repository": "order_automation",
  "accountId": "AC00000000101",
  "username": "jane.doe-example",
  "permission": "write"
}
```

`POST /api/v1/ts-projects/git/repos/{repository}/collaborators/remove` với `{"accountId": "..."}` thu hồi quyền và trả
`"removed": true`. Thu hồi quyền của user vốn không có quyền cũng thành công.
`POST /api/v1/ts-projects/git/repos/{repository}/collaborators/list` trả:

```json
{
  "organization": "example",
  "repository": "order_automation",
  "owners": [{"accountId": "AC00000000100", "username": "admin-example", "name": "Admin"}],
  "items": [{"username": "jane.doe-example", "accountId": "AC00000000101", "name": "Jane Doe",
    "status": "ACTIVE", "permission": "write"}],
  "total": 1
}
```

`owners` là các SuperAdmin sở hữu repository. Trong `items`, `accountId`, `name` và `status` là `null` với collaborator
không phải tài khoản Git của Workspace này.

User phải có tài khoản Git đang hoạt động hoặc đang khoá trong cùng Workspace, nếu không trả `404` với
`GIT_ACCOUNT_NOT_FOUND`. Repository không tồn tại trả `404`; tên repository hoặc `permission` không hợp lệ trả `400`.
Thay đổi có hiệu lực từ request kế tiếp của user đó.

### Access token

Access token là mật khẩu của Git over HTTPS. Mọi token có đúng hai quyền, đọc và ghi `repository` và đọc `user`;
client không chọn quyền.

| Endpoint | Body | Thành công |
|---|---|---|
| `POST /api/v1/ts-projects/git/tokens/list` | `{"accountId"}`, không bắt buộc | `200` |
| `POST /api/v1/ts-projects/git/tokens` | `{"name"}` | `201` |
| `POST /api/v1/ts-projects/git/tokens/{tokenId}/delete` | `{"accountId"}`, không bắt buộc | `200` `{"id", "deleted": true}` |

- Không truyền `accountId` thì việc liệt kê và thu hồi áp dụng cho token của chính user đang đăng nhập; có truyền thì
  áp dụng cho token của user đó. Token chỉ được tạo cho user đang đăng nhập: không ai tạo token dưới tên người khác.
- `name` gồm 1 đến 64 chữ cái, chữ số, khoảng trắng hoặc các ký tự `.` `_` `@` `:` `-`, duy nhất trong một tài khoản
  (`409` với `GIT_TOKEN_NAME_EXISTS`). Một tài khoản có tối đa 20 token (`409` với `GIT_TOKEN_LIMIT_REACHED`). User đang
  đăng nhập cần có tài khoản Git đang hoạt động (`409` với `GIT_ACCOUNT_NOT_ACTIVE`).
- Thu hồi token đã không còn cũng thành công. Token tạo trên giao diện web cũng có trong danh sách.

Response tạo token là lần duy nhất có giá trị token:

```json
{
  "id": 18,
  "name": "laptop",
  "scopes": ["write:repository", "read:user"],
  "lastEight": "9f8e7d6c",
  "token": "<giá trị token>",
  "username": "jane.doe-example"
}
```

Danh sách gồm `accountId`, `username`, `total` và `items` có `id`, `name`, `scopes` và `lastEight` (8 ký tự cuối của
giá trị).

### Repository của các module

Mỗi module backend hoặc frontend có thể có một repository của organization Workspace, và một repository thuộc tối đa
một module. Module mới được tạo repository, trừ khi tạo với `"createGitRepository": false`; xem
[Repository của module](#repository-của-module). Xoá module thì repository được archive; code vẫn được giữ.

### Dùng Git over HTTPS

1. Lấy access token: bằng endpoint ở trên, hoặc trên giao diện web `https://{WORKSPACE_DOMAIN}/git/`, mục
   **Settings → Applications**, với hai quyền: `repository` **Read and write** và `user` **Read**. Quyền `user` cho Git
   server kiểm tra token đúng là của username bạn gửi; token thiếu quyền này bị từ chối.
2. Clone bằng `username` Git của bạn, dùng token làm mật khẩu:

   ```bash
   git clone https://{WORKSPACE_DOMAIN}/git/{organization}/{repository}.git
   ```

Username phải là chủ của token. Username Git chỉ dùng được trên domain của chính Workspace đó. Username của người
khác, username không phải tài khoản Git đang hoạt động của Workspace đó, token thiếu quyền đọc `user` và token sai đều
nhận cùng một `401`, kể cả khi dùng scheme xác thực khác Basic. Quá nhiều request kèm credential từ một địa chỉ nhận
`429`; thử lại sau vài giây. Chỉ gửi token ở
vị trí mật khẩu; token đặt trong query string của URL bị từ chối. Vài phút sau khi user rời Workspace, việc đăng nhập
Git và token của user đó sẽ ngừng hoạt động; tài khoản bị khoá hoặc bị xoá thì ngừng ngay, và token của tài khoản
vừa mở khoá dùng lại được ngay. Chưa hỗ trợ SSH.

Repository chỉ chia sẻ được cho tài khoản Git trong cùng Workspace: thành viên team và collaborator thuộc Workspace
khác sẽ tự động bị gỡ, trong vài giây nếu được thêm qua giao diện web.

### Mã lỗi Git

| `code` | Status | Khi nào |
|---|---:|---|
| `GIT_DISABLED` | `404` | Git chưa được bật ở môi trường của Workspace |
| `MEMBER_NOT_ACTIVE` | `404` / `409` | User không phải member đang hoạt động của Workspace |
| `GIT_ACCOUNT_NOT_FOUND` | `404` | User chưa có tài khoản Git, hoặc tài khoản không ở trạng thái cần thiết |
| `GIT_ACCOUNT_NOT_ACTIVE` | `409` | Tạo token khi chưa có tài khoản Git đang hoạt động |
| `GIT_REPOSITORY_NOT_FOUND` | `404` | Không có repository này trong organization |
| `GIT_REPOSITORY_EXISTS` | `409` | Tên repository đã được dùng |
| `GIT_REPOSITORY_LIMIT_REACHED` | `409` | Workspace đã đủ giới hạn repository |
| `GIT_REPOSITORY_LINKED` | `409` | Repository thuộc một project (khi xoá, hoặc khi liên kết vào project khác) |
| `PROJECT_ALREADY_LINKED` | `409` | Project đã có repository |
| `PROJECT_DISABLED` | `409` | Project đã bị xoá |
| `CONFIRM_MISMATCH` | `400` | `confirm` khác tên repository |
| `GIT_TOKEN_NAME_EXISTS` | `409` | Tên token đã được dùng |
| `GIT_TOKEN_LIMIT_REACHED` | `409` | Tài khoản đã có 20 token |
| `IMPERSONATION_NOT_ALLOWED` | `403` | Thao tác thay đổi gửi từ phiên đang thao tác dưới danh nghĩa user khác |
| `GIT_UNAVAILABLE` | `503` | Git server tạm thời không phản hồi; thử lại sau |

## Custom Module Action

Một version của module khai báo Custom Module Action bằng `defineAction` trong package `@cogover/sdk`. Khi version được activate, Process Builder hiển thị mỗi action mở cho `process` thành node **Custom Module Action**, và AI Agent Builder hiển thị mỗi action mở cho `agent` thành một tool. Hai route dưới đây trả về action của các version đang active của mọi module trong Workspace. Route chỉ đọc và mở cho mọi thành viên đang hoạt động của Workspace, vì vậy không đặt thông tin bí mật trong nhãn, mô tả hay schema của action.

```http
GET /api/v1/ts-projects/actions?consumer=process
x-req-type: 9
x-req-service: 4
```

```http
GET /api/v1/ts-projects/actions/{projectSlug}/{actionKey}?consumer=agent
x-req-type: 9
x-req-service: 4
```

`consumer` là bắt buộc, giá trị `process` hoặc `agent`. Chỉ action có `exposeTo` chứa giá trị đó được trả về. Hai route cũng nhận `POST` với cùng query string.

```json
{
  "r": 0,
  "msg": "OK",
  "data": {
    "actions": [
      {
        "projectId": "TSPXXXXXXXXXXXX",
        "projectSlug": "crm_tools",
        "projectName": "CRM tools",
        "versionId": "TSVXXXXXXXXXXXX",
        "key": "score_lead",
        "label": "Score lead",
        "description": "Scores a lead from its recent activities and returns a tier.",
        "effect": "read",
        "exposeTo": ["process", "agent"],
        "timeoutMs": 5000,
        "inputSchema": {
          "type": "object",
          "properties": {
            "leadId": {"type": "string", "x-cogover-object": "lead", "description": "ID of the lead to score"}
          },
          "required": ["leadId"],
          "additionalProperties": false
        },
        "outputSchema": {
          "type": "object",
          "properties": {
            "score": {"type": "number"},
            "tier": {"type": "string", "enum": ["A", "B", "C"]}
          },
          "required": ["score", "tier"],
          "additionalProperties": false
        }
      }
    ]
  }
}
```

Route chi tiết trả một phần tử trong `data.action`. Action được sắp theo `projectSlug`, rồi theo thứ tự khai báo; property của schema giữ thứ tự khai báo.

| Field | Ý nghĩa |
|---|---|
| `key`, `label`, `description` | Key của action (`[a-z][a-z0-9_]{0,63}`, duy nhất trong module), tên hiển thị và mô tả. Action mở cho `agent` luôn có mô tả, AI Agent đọc mô tả này. |
| `effect` | `read`: action chạy ở chế độ chỉ đọc, thao tác ghi bị từ chối. `write`: action được ghi; tool AI Agent của action này mặc định cần phê duyệt. |
| `exposeTo` | `process`, `agent` hoặc cả hai. |
| `timeoutMs` | Giới hạn thời gian của action, từ 1000 đến 8000 ms. |
| `inputSchema`, `outputSchema` | JSON Schema của input và output. Các keyword được dùng: `type`, `properties`, `required`, `additionalProperties: false`, `items`, `enum`, `minLength`, `maxLength`, `minimum`, `maximum`, `maxItems`, `description`, `format` (`date`, `x-epoch-ms`) và `x-cogover-object` (object slug của một record ID). |

| HTTP | `data.errorCode` | Nguyên nhân |
|---:|---|---|
| `400` | `INVALID_REQUEST` | Thiếu `consumer` hoặc giá trị khác `process`, `agent`. |
| `401` | | Chưa xác thực. |
| `403` | | Người gọi không phải thành viên đang hoạt động của Workspace. |
| `404` | `ACTION_NOT_FOUND` | Không có version active nào của module đó khai báo action đó cho consumer đó. |

Version có khai báo action không hợp lệ kết thúc ở `FAILED` với `buildErrorCode: "ACTION_MANIFEST_INVALID"`, ví dụ action key trùng, schema dùng keyword không được hỗ trợ hoặc schema lớn hơn 16 KiB.

Khi Process hoặc AI Agent chạy một action, input được kiểm tra theo `inputSchema` trước khi chạy và output theo `outputSchema` sau khi action trả về. Lượt chạy thất bại báo cho node Process hoặc AI Agent một trong các mã lỗi sau:

| Mã | Ý nghĩa |
|---|---|
| `INPUT_INVALID` | Input không khớp `inputSchema`. |
| `OUTPUT_INVALID` | Action trả về giá trị không phải dữ liệu JSON hoặc không khớp `outputSchema`. |
| `SCRIPT_ERROR` | Action ném lỗi của SDK; mã lỗi được giữ trong `details.scriptErrorCode` và message là thông báo public cố định của mã đó, giống cách route HTTP trả về (message riêng của handler không được trả về). Lỗi không có mã public được báo bằng một thông báo cố định khác. Handler dùng hết một giới hạn tài nguyên của sandbox (số câu lệnh, bộ nhớ hoặc stack) báo `SCRIPT_ERROR` với `details.reason` là `"RESOURCE_LIMIT_EXCEEDED"`. |
| `TIMEOUT` | Action chạy quá `timeoutMs`. |
| `RATE_LIMITED` | Action vượt một giới hạn của lần chạy (`details.budget`). |
| `PERMISSION_DENIED` | Action bị từ chối một thao tác. Trong lúc activate version mới, lời gọi có thể thất bại trong chốc lát với `details.reason` là `"PROJECT_POLICY_NOT_APPROVED"` trước khi chạy; lần gửi lại của bên gọi sẽ chạy. |
| `INTERNAL_ERROR` | Lỗi khác. |

Lời gọi cũng có thể bị từ chối trước khi action chạy: `ACTION_NOT_FOUND`, `ACTION_NOT_EXPOSED` (action không mở cho bên gọi đó), `ACTOR_NOT_ALLOWED` (người dùng mà Process hoặc agent chạy thay không còn là thành viên đang hoạt động), `SYSTEM_IDENTITY_NOT_ALLOWED` (lời gọi không có người dùng cần `allowInternalSystem: true` trong identity policy đã duyệt của version active), `MAX_HOP_EXCEEDED` (chuỗi tự động hoá gọi lẫn nhau bị dừng), `IDEMPOTENCY_CONFLICT` (mã lượt chạy của bên gọi đã được dùng với input khác, từ node Process hay phiên agent khác, hoặc cho danh tính khác) và `RUNTIME_UNAVAILABLE` (tạm thời; bên gọi tự gửi lại). Khi action chạy với danh tính người dùng, quyền truy cập record mặc định theo quyền của người đó như khi gọi module production; khi không có người dùng, action chỉ có các quyền mà identity policy đã duyệt cấp. Version active chưa có identity policy được duyệt thì hoạt động như route: lời gọi có người dùng chạy với quyền riêng của người đó và không có quyền nào của policy, lời gọi không có người dùng bị từ chối với `SYSTEM_IDENTITY_NOT_ALLOWED`.

## Phát triển local

Dùng Cogover Dev CLI để phát triển local. Sau khi nhận Project key từ quản trị viên Workspace, chạy các lệnh đăng nhập và chạy ứng dụng local được hướng dẫn trong tài liệu CLI. CLI tự động quản lý an toàn việc xác thực, phiên ngắn hạn, thứ tự request và các SDK capability call.

Không gọi trực tiếp các transport endpoint của Development session. Đây là protocol có version giữa Cogover Dev CLI và Runtime, không phải public integration API dành cho code của Custom Backend Module.

## Gọi module production

Gọi active version bằng module slug và route tùy chọn:

```http
POST /api/v1/ts-projects/order_automation/orders/create?notify=true
x-req-type: 9
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

Script nhận JSON body cùng request context chỉ đọc, gồm method, route path, query parameter, request header an toàn, Workspace và user đã xác thực. Query parameter luôn lấy từ URL của request, không bao giờ lấy từ body. Credential và transport header không bao giờ được truyền cho code của module.

Project slug không tồn tại trả `404`, module không có active version trả `409`. Method khác năm method trên trả `405`.

Module chọn HTTP status, content type, header và body qua public SDK response API. Nếu không dùng custom response, JSON result hợp lệ được trả với HTTP `200` và `application/json; charset=utf-8`; kể cả object trả về chỉ trông giống SDK response cũng được gửi như dữ liệu JSON. Code trong module không thể đặt hop-by-hop header, cookie, server-identifying header hoặc Cogover routing header. `response.redirect` chỉ nhận status `301`, `302`, `303`, `307` và `308`.

Khi lỗi SDK thoát khỏi handler, response dùng HTTP status theo nhóm lỗi (ví dụ `400` với `VALIDATION_ERROR`, `403` với `PERMISSION_DENIED`, `404` với `NOT_FOUND`, `429` với `RATE_LIMITED`) và có `r`, `code`, `msg` tiếng Anh, `writesMayHaveCompleted`, cùng các chi tiết an toàn khi liên quan như `reason`, `operation`, `objectSlug`, `fieldSlug` và `objectServerR`. Ví dụ, thao tác ghi record bị record trigger before-change từ chối mà handler không bắt lỗi sẽ trả `400` với `code: "VALIDATION_ERROR"` và `reason: "TRIGGER_REJECTED"`.

Mọi lỗi khác, như exception JavaScript không được bắt hoặc vượt giới hạn thực thi, trả `422` không có `code`:

```json
{
  "r": 422,
  "msg": "Script execution failed or exceeded its limits; writes may already have completed"
}
```

Cả `writesMayHaveCompleted: true` lẫn message này đều không có nghĩa là thao tác ghi đã thành công; hãy kiểm tra dữ liệu trước khi retry lời gọi có ghi.

Mỗi lời gọi chạy trong giới hạn của nền tảng về thời gian thực thi và về số lượng, kích thước các SDK call; giá trị do nền tảng đặt và có thể khác nhau giữa các môi trường. Giới hạn thời gian tính từ lúc handler bắt đầu chạy; vượt quá thì lời gọi kết thúc với response `422` ở trên. SDK call vượt ngân sách call, hoặc một call quá lớn, bị từ chối trước khi gửi bằng lỗi mà handler bắt được. Khi Workspace đã có quá nhiều lời gọi đang chờ, lời gọi mới bị từ chối trước khi chạy với `429` và `code: "RATE_LIMITED"`; hãy thử lại sau.

`Idempotency-Key` không bắt buộc nhưng nên dùng cho request có thể ghi dữ liệu. Retry đã hoàn tất với cùng caller, version deploy, method, route và key sẽ phát lại kết quả đầu tiên trong tối đa 6 giờ. Request trùng đang chạy trả `409`. Kết quả đầu tiên lớn hơn 32 KiB, hoặc vượt hạn mức phát lại theo giờ của Workspace, không được lưu: retry cùng key khi đó trả `409` mà không chạy lại handler. Idempotency không biến nhiều thao tác dữ liệu thành một transaction.

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
- `HMAC`: gửi chữ ký trong `header` đã cấu hình. Chữ ký là `<prefix>` nối với HMAC-SHA256 của signed payload, mã hóa theo `encoding`, tính bằng secret dùng chung. Signed payload là raw body của request theo byte; khi có cấu hình `timestampHeader`, signed payload là `<timestamp>.<raw body>`, với `<timestamp>` là giá trị header đó tính bằng giây Unix (cũng chấp nhận millisecond Unix), và lời gọi bị từ chối khi timestamp lệch quá `toleranceSeconds` so với giờ server.

```http
POST /api/v1/ts-projects/order_automation/hooks/TSIXXXXXXXXXXXX/payments
X-Payment-Timestamp: 1788023000
X-Payment-Signature: sha256=<HMAC-SHA256 dạng hex của "1788023000.<body>">
Content-Type: application/json

{"id": "evt_123", "orderId": "ORD-001", "status": "succeeded"}
```

Mọi lỗi xác thực — inbound access không tồn tại, đã revoke hoặc hết hạn, inbound access của module khác, route ngoài `routePrefix`, key hoặc chữ ký sai, timestamp ngoài tolerance — trả HTTP `401` với `{ "r": 401, "msg": "Inbound authentication failed" }`, không kèm chi tiết. Mỗi inbound access, và mỗi địa chỉ gọi, nhận tối đa 600 request mỗi phút; vượt quá trả `429`. Khi có `timestampHeader`, mỗi chữ ký chỉ được chấp nhận một lần: request thứ hai cùng chữ ký trong cửa sổ tolerance bị từ chối với `401`, nên request bị chặn bắt không thể phát lại.

Request body giới hạn 256 KiB (`413` nếu lớn hơn). Khi body là JSON object, nó trở thành `request.body` của module; body dạng form, text hoặc dạng khác vẫn được chấp nhận và cho module `request.body` rỗng. Trong mọi trường hợp module nhận raw body qua `request.rawBody` và content type của request qua `request.contentType`, nên có thể tự kiểm tra cơ chế chữ ký riêng của hệ thống ngoài. Raw body chỉ tính vào giới hạn body 256 KiB, nhưng JSON body đã parse, request header và context của lời gọi cộng lại cũng bị giới hạn 256 KiB như mọi lời gọi khác, nên JSON body sát 256 KiB vẫn có thể bị từ chối với `413`. Query parameter và request header an toàn được truyền như mọi lời gọi khác. Header chứa inbound key và `header` chữ ký HMAC đã cấu hình không bao giờ lộ vào code của module; `timestampHeader`, nếu có, vẫn hiện trong `request.headers`.

Module chạy với danh tính `inbound`: `invocation.identity` là `"inbound"`, không có user, và thao tác record dùng danh tính system theo identity policy đã duyệt của module. HTTP status, header và body do module chọn như mọi lời gọi khác. `Idempotency-Key` hoạt động như bình thường nhưng chỉ dưới dạng request header: request body là dữ liệu của hệ thống ngoài và không bao giờ được dùng làm idempotency key. Module không có active version trả `404` với `msg: "TypeScript project not found"`, và route mà module không định nghĩa trả `404`.

## Preview chính xác một version

SuperAdmin có thể chạy một version bất biến cụ thể mà không thay đổi active version:

```http
POST /api/v1/ts-projects/order_automation/orders/test
x-req-type: 9
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
  "usage": {
    "capabilityCalls": {"used": 3, "limit": 100},
    "localCalls": {"used": 0, "limit": 200},
    "recordsRead": {"used": 120, "limit": 10000},
    "recordsWritten": {"used": 0, "limit": 10000},
    "elapsedMs": 21,
    "timeLimitMs": 8000
  },
  "operations": {"records.list": 2, "state.get": 1},
  "stdout": "",
  "stderr": "",
  "logsTruncated": false
}
```

`usage` cho biết preview đã dùng bao nhiêu mỗi ngân sách của lần thực thi, giống `limits.usage()` của SDK, còn `operations` đếm số lời gọi SDK theo operation, kể cả lời gọi bị từ chối vì đã hết ngân sách. Dùng chúng để tìm lời gọi chạm giới hạn.

Debug output bị giới hạn kích thước. Script lỗi trả `success: false` cùng object `error`; response lỗi cũng có `durationMs`, và có `usage`, `operations` khi handler đã bắt đầu chạy. Stack trace và thông tin hệ thống nội bộ không được trả về. Lỗi không thuộc nhóm lỗi SDK nào trả `422`: ở mode `READ_WRITE`, `error` có message giống production `"Script execution failed or exceeded its limits; writes may already have completed"` và `writesMayHaveCompleted: true`; ở mode `READ_ONLY`, message là `"Script execution failed or exceeded its limits"` và `writesMayHaveCompleted: false`.

`READ_ONLY` chỉ cho phép thao tác đọc. `READ_WRITE` không tự cấp thêm quyền; mọi lời gọi vẫn bị giới hạn bởi caller, policy và capability hiện có. Các thao tác ghi là thật và không được rollback theo nhóm.
