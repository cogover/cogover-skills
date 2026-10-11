# Object Form API contract

## Mục lục

- [1. Xác thực và response envelope](#1-xác-thực-và-response-envelope)
- [2. Resolve Object và layout](#2-resolve-object-và-layout)
- [3. Endpoint quản lý form](#3-endpoint-quản-lý-form)
- [4. Schema cấu hình](#4-schema-cấu-hình)
- [5. Payload mẫu](#5-payload-mẫu)
- [6. Responses và chia sẻ](#6-responses-và-chia-sẻ)
- [7. Ràng buộc update và lỗi](#7-ràng-buộc-update-và-lỗi)

## 1. Xác thực và response envelope

Tất cả endpoint quản trị bên dưới là Web App API `/api/v1`. Bắt buộc dùng `$cogover-api-auth` để đổi API Key thành phiên qua `POST /bapi/v1/auth-token`; không dùng `Authorization: Bearer {API_KEY}` trực tiếp với `/api/v1`.

Mọi request quản trị gửi:

```http
Cookie: HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
Content-Type: application/json
```

Response cơ bản:

```json
{
  "r": 0,
  "msg": "OK",
  "requestId": "{optional-request-id}"
}
```

List trả thêm:

```json
{
  "r": 0,
  "msg": "OK",
  "meta": {
    "total": 1,
    "currentPage": 1,
    "lastPage": 1,
    "perPage": 20
  },
  "data": []
}
```

Create và duplicate trả `data` là mảng phần tử tối thiểu `{ "id", "slug", "options" }`. Detail trả object form trong `data`. Update/delete thành công có thể chỉ trả envelope.

## 2. Resolve Object và layout

### Resolve Object và fields

```http
POST /api/v1/objects/object/get-by-slug
```

```json
{
  "slug": "{objectSlug}",
  "withFields": 1,
  "withRelatedList": 0,
  "display": true,
  "translate": true,
  "withPersonnelInfo": false
}
```

Chỉ tiếp tục khi `data[0].slug` khớp exact. Dùng `data[0].fields` để resolve field ID/slug/type khi kiểm tra content layout; form không có mảng field riêng.

### List layout của Object

```http
GET /api/v1/layouts/object/{objectSlug}?objectTypeSlug={objectSlug}&limit=1000&page=1&platform=all
```

Các trường cần đọc trong `data[]`:

| Trường | Ý nghĩa |
|---|---|
| `id`, `name` | ID/name để chọn layout |
| `objectTypeSlug` | Phải khớp Object form |
| `isForm` | Boolean `true` hoặc numeric `1` mới là candidate cho `objectLayoutId` theo UI |
| `functionLayout` | `1` Add, `2` View/Edit, `3` Add + View/Edit |
| `status` | Trạng thái layout |
| `content`, `pageSettings` | Field structure và style |

Đọc detail khi cần xác minh một ID:

```http
GET /api/v1/layouts/{layoutId}
```

`objectLayoutId` phải là layout cùng Object và `isForm: true`/`1`. Layout nhập liệu do workflow này tự tạo phải có `functionLayout: 1`, quyền `ADD`, `status: 1` và content hợp lệ. Với `successAction: 1`, `successLayoutId` phải là layout cùng Object có `functionLayout` bằng `2` hoặc `3`.

Khi mọi layout đều có `isForm: false`/`0`, selector “Chọn giao diện cho trang điền thông tin biểu mẫu” của UI không có option. Không gửi create với layout Add thông thường. Gọi `$object-layout` để tạo một layout Web active mới trên đúng Object với `functionLayout: 1`, quyền `ADD` và `isForm: 1`; không chuyển một layout hiện có từ `isForm: 0` sang `1`. Nếu người dùng không đưa yêu cầu bố cục, `$object-layout` tự dựng layout mặc định từ các field có thể nhập của Object. Sau khi tạo, đọc lại layout qua API quản trị và chỉ tiếp tục khi ID, `objectTypeSlug`, `isForm`, `functionLayout` và `status` đều khớp. Contract Object Form không tự dựng payload layout; toàn bộ việc thiết kế/tạo layout thuộc `$object-layout`.

## 3. Endpoint quản lý form

Base URI: `/api/v1/objects/forms`.

| Capability | Method và URI | Input |
|---|---|---|
| List/search | `POST /search` | JSON search body; `objectSlug` bắt buộc |
| Create | `POST /create` | Full form body |
| Detail | `GET /{id}` | Path `id` |
| Update/status | `PATCH /{id}` | Partial form body |
| Delete one/many | `DELETE /` | JSON `{ "id": "id1,id2", "objectSlug": "..." }` |
| Duplicate | `POST /{id}/duplicate` | Body có tối thiểu `name`; nên gửi `name`, `slug` mới |
| Check name/slug | `POST /{objectSlug}/check-exists` | `{ "objectSlug": "...", "name"?: "...", "slug"?: "..." }` |
| List responses | `GET /{id}/responses` | Query params |
| Response detail | `GET /{id}/responses/{responseId}` | Path params |

### Search body

```json
{
  "objectSlug": "{objectSlug}",
  "limit": 20,
  "page": 1,
  "order": "created",
  "sort": "desc",
  "search": "{optional-name-substring}",
  "createdStart": 0,
  "createdEnd": 0,
  "updatedStart": 0,
  "updatedEnd": 0,
  "createdBy": { "op": "IN", "params": ["{personnelId}"] },
  "updatedBy": { "op": "NOT_IN", "params": ["{personnelId}"] }
}
```

Chỉ gửi các filter thời gian có giá trị thật; không gửi `0` như placeholder. `search` là substring của name. `createdBy`/`updatedBy.op` hỗ trợ `IN` và `NOT_IN`. Default backend: `page: 1`, `limit: 20` trong request form, `order: "created"`, `sort: "desc"`.

### Check-exists response

Frontend gửi lại `objectSlug` trong body dù backend lấy Object đích từ path. Giữ hai giá trị giống nhau để request có thể được audit rõ ràng:

```json
{
  "objectSlug": "{objectSlug}",
  "name": "{candidate-name}",
  "slug": "{candidate-slug}"
}
```

Response `data` chỉ chứa key đã hỏi:

```json
{
  "r": 0,
  "msg": "Success",
  "data": {
    "name": false,
    "slug": false
  }
}
```

Check này không loại trừ form hiện tại. Khi update mà giữ nguyên name/slug, so sánh với detail trước thay vì coi form tự thân là xung đột.

## 4. Schema cấu hình

| Trường | Kiểu/giá trị | Quy tắc |
|---|---|---|
| `objectSlug` | string | Bắt buộc khi create/search; phải resolve exact |
| `name` | string | Bắt buộc, trim, UI giới hạn 100; unique trong Object |
| `slug` | string | UI bắt buộc 2–100; unique trong Object; bất biến sau create |
| `description` | string | Tùy chọn, UI giới hạn 1000 |
| `status` | `0 \| 1` | `1` active/published, `0` inactive; create default backend `1` |
| `objectLayoutId` | string | Bắt buộc; layout `isForm: true`/`1` của cùng Object |
| `successAction` | `1 \| 2` | `1` show success layout; `2` redirect URL |
| `successLayoutId` | string | Bắt buộc theo UI khi action `1`; View-capable layout cùng Object |
| `successRedirectUrl` | string | Bắt buộc và là URL hợp lệ theo UI khi action `2` |
| `autoCreateRecord` | `0 \| 1` | UI create mặc định `1`; backend tạo record khi `1` |
| `defaultLanguage` | `"vi-VN" \| "en-US"` | Ngôn ngữ form/email template |
| `notifyRelatedUsers` | string[] | Personnel record IDs; gửi khi phát hiện duplicate record |
| `notifyOtherUsers` | string[] | Personnel record IDs; gửi sau mỗi submit |
| `blockedEmails` | string[] | Email đầy đủ hoặc domain có tiền tố `@` theo backend matcher |
| `blockFreeEmail` | `0 \| 1` | Chặn nhà cung cấp email miễn phí khi `1` |

### Lưu ý `blockedEmails`

Backend so khớp không phân biệt hoa thường:

- Phần tử bắt đầu bằng `@` được so bằng `email.endsWith(blocked)` và chặn cả domain.
- Phần tử không bắt đầu bằng `@` chỉ được so exact với toàn bộ email.

Với API trực tiếp, dùng `@example.com` để chặn domain; dùng `user@example.com` để chặn đúng một email. Bare domain như `example.com` không được coi là domain rule bởi API. Khả năng nhập tag trên giao diện có thể khác quy tắc của API; kiểm tra giá trị lưu lại và không suy luận bare domain hoạt động chỉ từ việc giao diện chấp nhận nó.

`notifyRelatedUsers` và `notifyOtherUsers` trong UI chỉ chọn Personnel active, không phải system user và có `account_email` khác null. Giữ cùng điều kiện khi resolve ID.

## 5. Payload mẫu

### Create

```json
{
  "objectSlug": "doi_tuong_a",
  "name": "External intake",
  "slug": "external_intake",
  "description": "Collect data from external users",
  "status": 1,
  "objectLayoutId": "{formLayoutId}",
  "successAction": 1,
  "successLayoutId": "{viewLayoutId}",
  "successRedirectUrl": "",
  "autoCreateRecord": 1,
  "defaultLanguage": "vi-VN",
  "notifyRelatedUsers": [],
  "notifyOtherUsers": [],
  "blockedEmails": [],
  "blockFreeEmail": 0
}
```

### Patch đổi sang redirect và tắt form

```json
{
  "status": 0,
  "successAction": 2,
  "successLayoutId": "",
  "successRedirectUrl": "https://example.com/thank-you"
}
```

PATCH là partial. Omitted field được giữ nguyên; `null` không xoá hầu hết field vì persistence chỉ cập nhật giá trị khác null. Dùng `""` hoặc `[]` để clear. Khi muốn mô phỏng UI full-state, pre-read rồi chỉ merge các key trong bảng schema; loại `id`, `workspaceId`, counters, audit fields, personnel info và `accessControls` khỏi body.

### Duplicate

```http
POST /api/v1/objects/forms/{sourceFormId}/duplicate
```

```json
{
  "name": "Copy of External intake",
  "slug": "copy_external_intake"
}
```

Backend sao chép Object, layout, success settings, auto-create, language, notify và blocked-email settings từ source. `name` bắt buộc; nếu có `slug` mới thì phải unique. Đọc detail source trước và check name/slug đích trước mutation.

### Delete

```http
DELETE /api/v1/objects/forms
```

```json
{
  "id": "{formId1},{formId2}",
  "objectSlug": "doi_tuong_a"
}
```

`id` là một string CSV, không phải array. Chỉ gom các form đã resolve thuộc cùng Object.

Trước delete, đọc response list để biết số submission bị ảnh hưởng về khả năng truy cập. Contract API công khai không cam kết cascade hay retention, vì vậy không đưa ra tuyên bố về số phận response sau delete nếu deployment chưa có tài liệu công khai xác nhận.

## 6. Responses và chia sẻ

Responses là dữ liệu đã submit, không phải phần cấu hình. Chỉ đọc khi cần chẩn đoán hoặc xác minh phạm vi trước thao tác khác.

```http
GET /api/v1/objects/forms/{formId}/responses?objectSlug={objectSlug}&limit=20&page=1&order=created&sort=desc&search={text}&createdStart={ms}&createdEnd={ms}&objectRecordId={recordId}
```

List trả `data[]` gồm `id`, `workspaceId`, `name`, `objectSlug`, `objectFormId`, `objectRecordId`, `recordExists`, `data`, `created`, `updated`; detail dùng:

```http
GET /api/v1/objects/forms/{formId}/responses/{responseId}
```

Sau khi đọc detail response, kiểm tra `objectFormId` trong response khớp `{formId}` trước khi dùng kết quả.

Không dùng endpoint submit công khai để test cấu hình nếu người dùng chưa yêu cầu tạo dữ liệu thật. Không dùng endpoint layout công khai làm health check mặc định vì mỗi call tăng `viewCount`.

### URL chia sẻ

Không có share endpoint. Từ detail lấy `workspaceId`, dùng Base64 chuẩn trên chuỗi UTF-8/ASCII:

```text
raw  = {workspaceId}&{formId}
code = Base64(raw)
url  = https://form.{SITE_DOMAIN}/{code}
```

Sau create/duplicate, URL public là đầu ra bắt buộc. Chuẩn hoá `WORKSPACE_DOMAIN` thành hostname, lấy domain đăng ký gốc (`registrable domain`/`eTLD+1`) làm `SITE_DOMAIN`, rồi dùng host `form.{SITE_DOMAIN}`. Ví dụ: `tenant.example.com` → `SITE_DOMAIN=example.com` → `form.example.com`; `tenant.example.co.uk` → `SITE_DOMAIN=example.co.uk` → `form.example.co.uk`. Không đơn giản lấy hai label cuối khi public suffix có nhiều label. Nếu hostname là IP, `localhost` hoặc không xác định chắc `eTLD+1`, yêu cầu người dùng cung cấp `SITE_DOMAIN`. Không đọc frontend bundle, source map, static JavaScript/CSS, HTML, repository hay filesystem máy chủ để tìm domain hoặc suy ra hành vi. Sau mutation, đọc detail qua API để lấy `workspaceId` + `formId`, rồi trả link trong kết quả cuối. Với form `status: 0`, vẫn có thể dựng URL nhưng phải ghi rõ URL chưa truy cập được cho đến khi publish.

### URL cấu hình nội bộ

Sau create/duplicate, URL cấu hình nội bộ cũng là đầu ra bắt buộc:

```text
url = https://{WORKSPACE_DOMAIN}/sales/object/{objectSlug}/form/{formId}
```

Chỉ dựng URL sau khi đã resolve exact `objectSlug`, đọc detail và post-check `formId`. Dùng hostname workspace đã chuẩn hoá, không dùng `SITE_DOMAIN` hay host `form.{SITE_DOMAIN}` cho URL này. URL nội bộ không phụ thuộc `status`, nhưng yêu cầu người truy cập đã đăng nhập đúng workspace và có quyền xem/cấu hình Object Form. Trả bằng link Markdown có nhãn `Link cấu hình biểu mẫu nội bộ`; không mô tả URL này là public hoặc có thể truy cập ẩn danh.

Mã nhúng do UI tạo:

```html
<script src="https://form.{SITE_DOMAIN}/js/cogover-loader.js" defer></script>
<div class="cogover-form-frame" data-workspace-id="{workspaceId}" data-form-id="{formId}"></div>
```

Loader hỗ trợ `data-domain`; chỉ truyền domain deployment đã được xác minh bằng nguồn public-safe nêu trên. Không đọc code loader hoặc suy đoán domain mặc định. Form public chỉ load khi backend thấy form tồn tại và `status: 1`.

## 7. Ràng buộc update và lỗi

- Slug update bị backend giữ về slug hiện tại; persistence không cập nhật slug. Không báo thành công khi request chứa slug khác.
- `accessControls` không thuộc ba bước cấu hình UI. Nếu gửi danh sách non-empty, backend xoá và tạo lại access control; nếu null/rỗng, handler bỏ qua. Luôn omit trong workflow form thông thường.
- Update không chạy validation create. Agent phải tự áp dụng dependency `successAction`, URL, layout và enum trước request.
- Name/slug unique theo workspace + Object. Mã lỗi đã quan sát: `527` name existed, `525` slug existed.
- Các mã liên quan khác: `405` invalid ID, `434` invalid layout ID khi create, `435` invalid Object slug, `440` invalid name, `501` Object/form not found tùy endpoint.
- Detail trả `viewCount` và `submitCount`; đây là counters server quản lý, không đưa vào payload.
- Sau PATCH, đọc detail và so sánh từng key. Sau status patch, xác minh numeric `0/1`. Sau create/duplicate, không suy luận full resource từ create response tối thiểu; luôn GET detail.
