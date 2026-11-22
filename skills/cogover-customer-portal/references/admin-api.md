# API quản trị Customer Portal

Mọi endpoint dưới đây là Web App API, gọi bằng phiên đổi từ API Key theo [$cogover-api-auth](../../cogover-api-auth/SKILL.md) (cookie phiên + hai header CSRF/XSRF). Không gửi API Key trực tiếp. Tiền tố chung:

```text
{WORKSPACE_URL}/api/v1/workspace/customer-portal/
```

Script [`scripts/customer_portal_api.py`](../scripts/customer_portal_api.py) đã làm sẵn bước đổi phiên, kiểm Workspace, che bí mật và chặn ghi khi thiếu `--apply`.

## Mục lục

- [Quy ước response và lỗi](#quy-ước-response-và-lỗi)
- [Bảng endpoint](#bảng-endpoint)
- [Cấu hình chung](#cấu-hình-chung)
- [Object trên cổng](#object-trên-cổng)
- [Người dùng cổng](#người-dùng-cổng)
- [Vận hành của nhân viên](#vận-hành-của-nhân-viên)
- [Tên miền riêng](#tên-miền-riêng)
- [API ngoài tiền tố dùng kèm](#api-ngoài-tiền-tố-dùng-kèm)

## Quy ước response và lỗi

- Thành công: HTTP 200 (tạo tin trao đổi: 201), `{"r": 0, "msg": "Successful", "data": ...}`.
- Lỗi: `{"r": <mã>, "msg": "...", "meta": {"code": "CP_...", ...}}`. `meta.errors` là object theo field (`{"<field>": "<mã>"}`), `meta.issues` là mảng `{objectKey, field, issue, label}`.

| HTTP / `r` | `meta.code` | Ý nghĩa | Xử lý |
|---|---|---|---|
| 422 / 42201 | `CP_VALIDATION_FAILED` | Dữ liệu sai; không có gì được ghi | Sửa đúng field trong `meta.errors` |
| 422 / 42201 | `CP_CONFLICT` | `lockVersion` cũ (người khác vừa lưu) | Đọc lại `config`, áp lại thay đổi trên bản mới |
| 422 / 42201 | `CP_PUBLISH_INVALID` | Xuất bản không qua kiểm tra; bản đang chạy giữ nguyên | Sửa từng mục trong `meta.issues` rồi xuất bản lại |
| 422 / 42201 | `CP_TRANSITION_NOT_ALLOWED` | Đơn/yêu cầu không còn ở trạng thái chờ, hoặc không phải đơn từ cổng | Đọc lại bản ghi |
| 422 / 42201 | `CP_PORTAL_NOT_PUBLISHED` | Cấp quyền khi cổng chưa xuất bản | Xuất bản trước |
| 422 / 42201 | `CP_DOMAIN_LIMIT` (`meta.max`) | Đã đủ số tên miền của gói | Gỡ tên miền cũ hoặc liên hệ Cogover |
| 403 | `CP_FORBIDDEN` hoặc thông báo từ chối quyền | Thiếu quyền, hoặc thao tác chỉ dành cho Super Admin | Xem [quyền](customer-access-and-operations.md#phân-quyền-nhân-viên) |
| 404 / 40401 | `CP_NOT_FOUND` | Không có, hoặc người gọi không xem được bản ghi liên quan | Kiểm ID và quyền xem record |
| 429 / 42901 | `CP_RATE_LIMITED` (`meta.retryAfter`, `meta.reason`) | Gửi lại thư mời quá nhanh (`resend_cooldown`) hoặc quá số lần/ngày | Chờ `retryAfter` giây |
| 503 / 50301 | `CP_DEPENDENCY_UNAVAILABLE` | Thành phần phụ thuộc chưa có (vd duyệt đăng ký khi tự đăng ký chưa từng được xuất bản) | Không thử lại dồn dập; kiểm điều kiện tiên quyết |

`POST /bapi/v1/auth-token` giới hạn **120 phiên/giờ cho tài khoản sở hữu API Key** (HTTP 429, `r: 42900`, header `Retry-After` tính bằng giây; mọi skill và tiến trình dùng chung key chia chung hạn mức). Mỗi lần chạy script tạo một phiên: gom thao tác, không chạy vòng lặp dày. Script chờ và thử lại khi phải chờ ≤ 60 giây; lâu hơn thì dừng và in số giây cần chờ. Chuỗi thao tác dài dùng lệnh `batch` (một phiên cho cả chuỗi, dừng ở bước lỗi đầu tiên; `"lockVersion": "current"` được điền từ `GET config` ngay trước bước đó):

```json
[
  {"method": "PUT", "path": "config", "body": {"lockVersion": "current", "settings": {"supportPhone": "1900 0000"}}},
  {"method": "POST", "path": "publish", "body": {}},
  {"method": "GET", "path": "config"}
]
```

Tham chiếu kết quả bước trước: chuỗi `{{steps.N.<đường dẫn>}}` trong `path` hoặc `body` được thay bằng giá trị trong response của bước `N` (đếm từ 1, đường dẫn tính từ gốc response: `data.id`, `data.items.0.id`). Chuỗi chỉ gồm một tham chiếu thì nhận nguyên giá trị (số, object); tham chiếu không tồn tại thì dừng trước khi gửi bước đó. Ví dụ đã chạy thật (thêm Object, sửa, xoá trong một phiên):

```json
[
  {"method": "POST", "path": "objects", "body": {"objectSlug": "contract", "preset": "contract", "objectKey": "contract"}},
  {"method": "PUT", "path": "objects/{{steps.1.data.id}}", "body": {"config": {"label": {"vi-VN": "Hợp đồng", "en-US": "Contracts"}, "accountField": "account", "permissions": {"view": true, "create": false}, "listColumns": ["code", "name"]}}},
  {"method": "GET", "path": "objects/{{steps.1.data.id}}"}
]
```

Đầu ra: các lệnh `get`, `call` in một khối JSON `{"httpStatus", "response"}` (dữ liệu nằm ở `response.data`); `batch` in cho mỗi bước một dòng `# step N: METHOD path` rồi một khối JSON cùng dạng (bí mật đã che); bước lỗi in thêm `Request failed...` vào stderr và dừng (exit 1). Thêm `--out <file>` để ghi kết quả mọi bước đã chạy thành **một mảng JSON hợp lệ** `[{step, method, path, httpStatus, response}]`: đọc file này thay vì tách stdout. Bước `POST publish` trong `batch` chỉ trả `{configVersion, publishedAt, warnings}`; thêm bước `GET config` sau nó để đọc `dirty` (lệnh `publish` riêng của script tự in khối `after`).

## Bảng endpoint

Cột "SA" = chỉ Super Admin (người có quyền cổng nhưng không phải Super Admin nhận 403).

| Method + path (sau tiền tố) | Quyền | SA | Dùng để |
|---|---|---|---|
| `GET config` | Thiết lập: xem | | Đọc nháp, bản đã xuất bản, trạng thái |
| `PUT config` | Thiết lập: sửa | khối `lookups`, `chat`, `help` | Lưu nháp cấu hình chung |
| `POST config/logo` | Thiết lập: sửa | | Tải logo vào nháp |
| `POST publish` | Thiết lập: sửa | | Xuất bản |
| `POST unpublish` | Thiết lập: sửa | | Tắt cổng |
| `GET objects` | Thiết lập: xem | | Danh sách Object trên cổng |
| `GET objects/presets` | Thiết lập: xem | có | Mẫu có sẵn |
| `GET objects/candidates/{objectSlug}[?layoutId=]` | Thiết lập: xem | có | Field, layout, related list chọn được |
| `POST objects` | Thiết lập: sửa | có | Thêm Object |
| `GET objects/{configId}` | Thiết lập: xem | | Chi tiết cấu hình Object |
| `PUT objects/{configId}` | Thiết lập: sửa | có | Sửa nháp Object |
| `DELETE objects/{configId}` | Thiết lập: sửa | có | Bỏ Object |
| `GET users` | Tài khoản: xem | | Người dùng cổng |
| `GET contacts/status?contactIds=` | Tài khoản: xem | | Trạng thái và điều kiện của Liên hệ |
| `POST grants` | Tài khoản: cấp | | Cấp quyền 1–100 Liên hệ |
| `POST links/{linkId}/resend-invite` | Tài khoản: sửa | | Gửi lại thư mời |
| `POST links/{linkId}/lock`, `/unlock` | Tài khoản: sửa | | Khoá, mở khoá |
| `PUT links/{linkId}/role` | Tài khoản: sửa | | Quản trị viên phía khách / thành viên |
| `DELETE links/{linkId}` | Tài khoản: thu hồi | | Thu hồi quyền |
| `POST users/{userId}/revoke-sessions` | Tài khoản: sửa | | Đăng xuất mọi phiên |
| `GET usage` | Tài khoản: xem | | Đã dùng / trần người dùng |
| `GET audit-logs` | Tài khoản: xem | | Nhật ký |
| `POST registrations/{recordId}/approve`, `/reject` | Tài khoản: duyệt | | Duyệt yêu cầu tự đăng ký |
| `POST orders/{orderId}/confirm`, `/reject` | Quyền sửa đơn hàng | | Xác nhận/từ chối đơn từ cổng |
| `GET`, `POST records/{objectSlug}/{recordId}/conversation` | Quyền record của nhân viên | | Đọc/gửi trao đổi với khách |
| `GET domains` | Thiết lập: xem | | Tên miền riêng |
| `POST domains`, `POST domains/{id}/check`, `DELETE domains/{id}` | Thiết lập: sửa | có | Thêm, kiểm, gỡ tên miền |

## Cấu hình chung

### `GET config`

```json
{"status": "PUBLISHED", "portalUrl": "{WORKSPACE_URL}/portal", "configVersion": 12, "lockVersion": 40,
 "publishedAt": 1767225600000, "draft": {"displayName": "Công ty Ví Dụ", "...": "..."},
 "published": {"...": "..."}, "objects": [{"id": "<CONFIG_ID>", "objectKey": "invoice", "objectSlug": "customer_invoice",
 "enabled": true, "published": true, "sortOrder": 1}], "dirty": false, "helpStatus": null}
```

- `status`: `DISABLED` (chưa bật hoặc đã tắt) / `PUBLISHED`. Workspace chưa từng cấu hình vẫn trả mặc định.
- `dirty: true`: nháp khác bản đang chạy (cần xuất bản). `lockVersion` tăng mỗi lần lưu; `configVersion` tăng mỗi lần xuất bản.
- Khối chưa từng cấu hình không có trong `draft` (vd không có `help`); chịu được khối vắng.

### `PUT config`

```json
{"lockVersion": 40, "settings": {"supportPhone": "1900 0000"}}
```

- **Chỉ khoá có mặt bị thay**: khoá cấp một không gửi giữ nguyên. Khoá đơn (`supportPhone`, `displayName`, `primaryColor`...) gửi riêng là đủ, các khoá/khối khác không đổi (đã kiểm bằng so sánh toàn bộ cấu hình trước/sau).
- **Khối object cấp một bị thay cả khối**: `statement`, `notifications`, `ordering`, `tasks`, `team`, `selfRegistration`, `chat`, `help`, `profile`, `session`, `invite`, và mảng `lookups`. Gửi `{"statement": {"enabled": true}}` làm mất `label`, `menuOrder` đã có (đã kiểm). Với các khối này luôn đọc `draft.<khối>`, sửa trên bản đó rồi gửi lại cả khối. `null` xoá khối.
- Khoá cấp một lạ → 422 `settings.<khoá>: not_allowed`. Cờ bật/tắt phải là boolean JSON (`"true"` → `invalid_format`).
- Response giống `GET config` (đọc `dirty`, `lockVersion` mới).
- Chi tiết từng khối: [settings-and-features.md](settings-and-features.md).

### `POST config/logo`

Multipart, field `logo`, PNG/JPEG/WEBP thật (kiểm nội dung) ≤ 1 MB. Sai loại → 422 `logo: type_not_allowed`. Thành công trả cấu hình như `GET config`, logo nằm ở `draft.logo` và cổng chỉ đổi sau khi xuất bản.

### `POST publish`

Body `{}`. Thành công:

```json
{"configVersion": 13, "publishedAt": 1767225600000,
 "warnings": [{"objectKey": "quote", "field": "actions.accept.statusField", "issue": "action_no_transition_rule", "label": null}]}
```

Thất bại: 422 `CP_PUBLISH_INVALID` + `meta.issues`, bản đang chạy không đổi. Xuất bản có thể mất vài giây (lần đầu bật một tính năng, cổng tự tạo Object/field cần thiết), đặt timeout HTTP ≥ 60 giây; mất phản hồi thì đọc lại `config` (`configVersion`, `dirty`) trước khi gọi lại. Gọi lại an toàn. Mã issue/cảnh báo: [troubleshooting.md](troubleshooting.md#mã-issue-và-cảnh-báo-khi-xuất-bản).

### `POST unpublish`

Body `{}`. `status` thành `DISABLED`, mọi trang `/portal` trả "không tìm thấy" ngay; cấu hình và người dùng giữ nguyên, xuất bản lại là bật lại. Sau khi tắt, `dirty` có thể là `true` cho tới lần xuất bản sau.

## Object trên cổng

- `GET objects` → `{"items": [{id, objectKey, objectSlug, label, preset, enabled, sortOrder, published, publishedVersion}]}`.
- `GET objects/presets` → `{"items": [{preset, objectSlug, available, defaults}]}`; `defaults` là cấu hình khởi tạo.
- `GET objects/candidates/{objectSlug}` → `{object, accountFields, contactFields, fields[{slug,label,type,supported,readable,writable}], layouts[{id,title,functionLayout}], relatedLists[{id,label,childObjectSlug,selectable,reason,onLayout,columns,columnLabels}], notices}`. Thêm `?layoutId=<LAYOUT_ID>` để biết related list nào có trên layout (`onLayout`) và cột của nó.
- `POST objects` → `{"objectSlug": "contract", "preset": "contract", "objectKey": "contract"}` (preset, server điền `defaults`) hoặc `{"objectSlug": "<slug>", "objectKey": "<key>", "config": {...}}` (tuỳ biến). Response như `GET objects/{configId}`.
- `GET objects/{configId}` → `{id, objectKey, objectSlug, preset, enabled, sortOrder, draft, published}`.
- `PUT objects/{configId}` → `{"config": {...đủ cấu hình...}, "enabled"?: true, "sortOrder"?: 2}`. Gửi cấu hình đầy đủ (lấy `draft` rồi sửa); kiểm dạng khi lưu, kiểm đủ khi xuất bản.
- `DELETE objects/{configId}` → chưa từng xuất bản: `{"deleted": true, "disabled": false}`; đã xuất bản: `{"deleted": false, "disabled": true}` (gỡ khỏi cổng sau lần xuất bản kế tiếp; gọi DELETE lần nữa sau xuất bản để xoá hẳn dòng cấu hình).

Schema `config`: [portal-objects.md](portal-objects.md).

## Người dùng cổng

| Endpoint | Request | Response chính |
|---|---|---|
| `GET users` | query `q` (một phần tên Liên hệ hoặc email; dùng để tìm `linkId`/`userId`), `status` (`INVITED`/`ACTIVE`/`LOCKED`), `accountId`, `cursor`, `limit` ≤ 100 | `{"rows": [{linkId, userId, email, contactId, contactName, accountId, accountName, status, customerRole, storedCustomerRole, source, invitedAt, activatedAt, lastLoginAt}], "nextCursor"}`. `customerRole` = vai trò hiệu lực; `storedCustomerRole` khác `null` khi vai trò đã lưu không còn hiệu lực; `source` = nguồn cấp (`STAFF` nhân viên cấp, các giá trị khác cho tự đăng ký/quản trị viên phía khách mời) |
| `GET contacts/status` | `contactIds` ≤ 100, phân cách dấu phẩy | `{"portalStatus", "items": [{contactId, contactName, linkId, status: NOT_GRANTED/INVITED/ACTIVE/LOCKED, email, eligible, reason: null/NO_EMAIL/NO_ACCOUNT/CONTACT_NOT_FOUND}]}` |
| `POST grants` | `{"contactIds": ["<CONTACT_ID>"], "language": "vi-VN"}` (`language` tuỳ chọn) | `{"results": [{contactId, outcome: INVITED/ALREADY_INVITED/ALREADY_ACTIVE/SKIPPED, reason, linkId}], "usage": {used, max}}` |
| `POST links/{linkId}/resend-invite` | không body | `{linkId, userId, contactId, status, expiresAt}`; quá nhanh → 429 `resend_cooldown` (khoảng 60 giây), tối đa 5 lần/ngày/liên kết |
| `POST links/{linkId}/lock` | `{"reason": "..."}` (tuỳ chọn) | `{linkId, userId, contactId, status: "LOCKED"}` |
| `POST links/{linkId}/unlock` | không body | `status` về `ACTIVE` nếu từng đăng nhập, ngược lại `INVITED` |
| `PUT links/{linkId}/role` | `{"customerRole": "ADMIN"}` hoặc `"MEMBER"` (đúng chữ hoa) | `{linkId, userId, contactId, status, customerRole}`; chữ thường → 422 `customerRole: invalid` |
| `DELETE links/{linkId}` | không body | `{linkId, userId, contactId, status: "NOT_GRANTED", sessionsRevoked}` |
| `POST users/{userId}/revoke-sessions` | không body | `{userId, revokedSessions}` |
| `GET usage` | | `{"used": 8, "max": 1000}` (`used` = người dùng có ít nhất một liên kết) |
| `GET audit-logs` | `from`, `to` (ms, cách nhau ≤ 93 ngày, quá → 422 `to: invalid`; vắng = không giới hạn), `action`, `portalUserId`, `accountId`, `objectSlug`, `recordId`, `cursor` (= `nextCursor`, là `id` dòng cuối), `limit` ≤ 200 | `{"rows": [{id, createdAt, actorType (STAFF/CUSTOMER/ANONYMOUS/SYSTEM), actorName, action, accountId, accountName, objectSlug, recordId, recordName, outcome, ip, detail}], "nextCursor"}`, mới nhất trước. Giới hạn: [nhật ký](customer-access-and-operations.md#nhật-ký-và-hạn-mức) |

Cổng ghi trạng thái vào field `contact.portal_status` (`not_granted`, `invited`, `active`, `locked`); field này chỉ để xem/lọc, không sửa tay được (`/bapi` trả `r: 47`).

## Vận hành của nhân viên

- `GET records/{objectSlug}/{recordId}/conversation?limit=&cursor=` → `{enabled, canRead, canReply, rows[{id, author{type: customer/staff, name}, isPublic, content, files[{id,name,size}], createdAt}], nextCursor}`. Object chưa bật trao đổi: `enabled: false`.
- `POST records/{objectSlug}/{recordId}/conversation` → `{"content": "Văn bản thuần", "isPublic": true}` → 201, trả tin vừa tạo. `isPublic: false` là ghi chú nội bộ (khách không thấy). Nội dung chứa đường dẫn tệp nội bộ → 422 `content: file_link_not_allowed`; không đính tệp được. Object không bật trao đổi → 404.
- `POST orders/{orderId}/confirm` (body `{}`) và `POST orders/{orderId}/reject` (`{"reason": "1–2.000 ký tự"}`): chỉ với đơn khách đặt từ cổng còn chờ xác nhận. Response `{orderId, status, portalReviewStatus, notification}` (`notification`: `QUEUED`/`FAILED`/`SKIPPED`/`DUPLICATE`/`NOT_ELIGIBLE`/`DISABLED`). Thiếu lý do → 422 `reason: required`; đơn thường hoặc đã xử lý → 422 `CP_TRANSITION_NOT_ALLOWED`; không thấy đơn → 404.
- `POST registrations/{recordId}/approve` → `{"accountId": "<ACCOUNT_ID>", "contactId": "<CONTACT_ID>"}` hoặc `{"accountId": "...", "createContact": {"name": "..."}}` (đúng một trong hai). `POST registrations/{recordId}/reject` → `{"reason": "..."}`. Chỉ áp cho yêu cầu do cổng tạo, còn `pending`.

## Tên miền riêng

- `GET domains` → `{"rows": [DomainView], "max": 1, "configured": true, "cnameTarget": "<CNAME_TARGET>", "txtLabel": "_cogover-portal"}`. `configured: false` → Workspace chưa được Cogover bật hạ tầng tên miền riêng, `POST` sẽ bị từ chối.
- `POST domains` → `{"domain": "portal.example.com"}` → `{id, domain, displayDomain, status: "PENDING", cname, txtValidation{name, value}, records[{type, name, value}], lastError, portalUrl, expiresAt, ...}`.
- `POST domains/{id}/check` → DomainView kèm `check{verdict, txt, cname}`; `lastError` như `TXT_MISSING`, `CNAME_MISSING`, `CNAME_MISMATCH`, `DNS_ERROR`, `PROVIDER_NOT_CONFIGURED`.
- `DELETE domains/{id}` → `{id, domain, removed: true}`.
- Lỗi `domain`: `invalid_format`, `wildcard_not_allowed`, `ip_not_allowed`, `cogover_domain` (tên chứa "cogover"), `reserved`, `mixed_script`, `unsupported_script`...; mã `CP_DOMAIN_LIMIT`, `CP_DOMAIN_DUPLICATE`, `CP_DOMAIN_TAKEN`, `CP_DOMAIN_NOT_CONFIGURED`. Kiểm quá dày → 429 (`meta.retryAfter`).

## API ngoài tiền tố dùng kèm

- `GET {WORKSPACE_URL}/api/v1/workspaceEmail` (phiên Web App): danh sách hộp thư của Workspace `[{id, type, email, status}]`. Chỉ hộp thư `type` 1–4 (SMTP, Gmail, Outlook, SendGrid) và `status: 1` gửi được thư của cổng; `type` 5 (địa chỉ chuyển tiếp mặc định) bị từ chối khi lưu (`not_found`). Lệnh `mailboxes` của script đọc và đánh dấu `sendable`.
- Đọc/ghi bản ghi nghiệp vụ (Liên hệ, bảng giá, việc cần làm...): [$object-record](../../object-record/SKILL.md). Metadata Object/field: [$object-info](../../object-info/SKILL.md).
