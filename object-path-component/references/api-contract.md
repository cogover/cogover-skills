# Object Path Component API contract

## Mục lục

- [Xác thực](#xác-thực)
- [Response envelope](#response-envelope)
- [Resolve object, field và option](#resolve-object-field-và-option)
- [Endpoint path-component](#endpoint-path-component)
- [Schema path và stage](#schema-path-và-stage)
- [Quy tắc update và ordering](#quy-tắc-update-và-ordering)
- [Layout, action và delete safety](#layout-action-và-delete-safety)
- [Validation và mã lỗi](#validation-và-mã-lỗi)
- [Mẫu request](#mẫu-request)

Tài liệu này là contract tự đủ cho skill công khai. Chỉ xác minh hành vi bằng endpoint và response được mô tả tại đây; không mở source code, repository, file dự án, test, database, log nội bộ, browser bundle hoặc source map. Nếu contract không bao phủ một trường hợp, báo giới hạn thay vì truy tìm implementation.

## Xác thực

Tất cả endpoint nghiệp vụ trong tài liệu này là `/api/v1/...` và cần phiên Web App. Trước khi gọi, dùng `$cogover-api-auth`:

1. Gọi `POST https://{workspace-domain}/bapi/v1/auth-token` bằng API Key Bearer.
2. Lấy `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` từ response.
3. Gửi mọi `/api/v1` với:

```http
Cookie: HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
Content-Type: application/json
```

Không dùng API Key Bearer trực tiếp cho `/api/v1`.

## Response envelope

Read/list thường trả:

```json
{
  "r": 0,
  "msg": "Success",
  "meta": {
    "total": 1,
    "currentPage": 1,
    "lastPage": 1,
    "perPage": 20
  },
  "data": []
}
```

Create path-component trả ID, không nên giả định trả full resource:

```json
{ "r": 0, "msg": "Success", "data": [{ "id": "{pathComponentId}" }] }
```

Update/delete thành công trả tối thiểu `{ "r": 0, "msg": "Success" }`.

Riêng constraint có hai kết quả hợp lệ:

- `r: 0`, `data: null`: không có transition-rule active cho field.
- `r: 1`, `data: [...]`: có dữ liệu constraint. Không coi `r: 1` là lỗi ở endpoint này.

## Resolve object, field và option

### Object detail có fields

```http
POST /api/v1/objects/object/get-by-slug
```

```json
{
  "slug": "{objectSlug}",
  "withFields": 1,
  "withRelatedList": 1,
  "display": true,
  "translate": true
}
```

Chọn chính xác một object trong `data`. Ghi lại `id`, `slug`, `workspaceId`, `status` và `fields`. Với field path:

- Match ID/slug/tên chính xác; dừng nếu không duy nhất.
- Yêu cầu `status` active.
- Yêu cầu `fieldType` bằng `single_choice` hoặc `radio_button`, đúng như UI.
- Dùng `field.id` làm `objectFieldId`.

Nếu không có object slug, có thể phân trang `POST /api/v1/objects/object/get` rồi match tên/slug chính xác tại client; không chọn kết quả gần đúng.

### Option fallback

Object detail thường chứa `field.options`. Nếu không có, thử gọi:

```http
POST /api/v1/objects/multiple/get
```

```json
{
  "field_id": "{objectFieldId}",
  "workspace_id": "{workspaceId}",
  "limit": 200,
  "page": 1
}
```

Mỗi option quan trọng có:

```json
{
  "id": "{optionId}",
  "objectFieldId": "{objectFieldId}",
  "value": "Nhãn hiển thị",
  "slug": "option_slug",
  "sort": 1,
  "status": 1,
  "category": "TO DO"
}
```

`stage.value` phải là `option.slug`. Category hợp lệ theo UI là `TO DO`, `IN PROGRESS`, `DONE FAIL`, `DONE PASS`, hoặc `null`. Nếu key `category` không xuất hiện trong response, chuẩn hóa thành `null`; server/UI xử lý stage đó như `intermediate`.

`POST /api/v1/objects/multiple/get` là fallback tùy chọn và có thể trả `404`. Chỉ dùng khi `field.options` thiếu; nếu fallback không khả dụng, không dựng stages cho tới khi có nguồn option chính thức khác.

## Endpoint path-component

Base URI:

```text
/api/v1/object_security/path_component
```

| Mục đích | Method và URI | Input |
|---|---|---|
| List/filter | `POST .../get` | JSON filter |
| Detail theo ID | `GET ...?id={id}&translate=false` | Query |
| List của object ID | `GET ...?objectTypeId={id}&translate=false` | Query |
| List của object slug | `GET ...?objectSlug={slug}&translate=false` | Query |
| Detail theo object/path slug | `GET .../{objectSlug}/{pathSlug}?translate=1` | Path + query |
| Constraint transition-rule | `GET .../constraint?objectFieldId={fieldId}&objectTypeId={objectId}` | Query |
| Create | `POST .../create` | Full create JSON |
| Update/status | `POST .../update` | Patch JSON; full stages nếu thay stage |
| Delete | `POST .../delete` | `{ "id": "..." }` |

### List/filter body

```json
{
  "limit": 20,
  "page": 1,
  "order": "created",
  "sort": "desc",
  "objectSlug": "{objectSlug}",
  "objectTypeId": "{optionalObjectId}",
  "objectFieldId": "{optionalFieldId}",
  "id": "{optionalPathId}",
  "name": "{optionalContainsText}",
  "status": "0,1",
  "withDetails": false,
  "withPersonnelInfo": true,
  "translate": false
}
```

Có thể thêm `created`, `updated` theo dạng `startMillis,endMillis`, `createdBy`, `updatedBy`, và `filterFieldsNotIn`. `sort` chỉ là `asc` hoặc `desc`. Khi cần stages trong list, đặt `withDetails: true`; detail GET theo ID luôn trả stages.

### Constraint response

```json
{
  "r": 1,
  "msg": "Success",
  "data": [
    {
      "activeTransitionRuleId": "{ruleId}",
      "activeTransitionRuleName": "Quy tắc A",
      "constraintStages": [
        { "value": "new", "type": "start" },
        { "value": "working", "type": "intermediate" },
        { "value": "done", "type": "finish" }
      ]
    }
  ]
}
```

`value` cũng là option slug. Endpoint này cung cấp preflight context; vẫn validate category và ordering theo schema path.

## Schema path và stage

### Create body

```json
{
  "name": "Quy trình xử lý",
  "slug": "quy_trinh_xu_ly",
  "status": 0,
  "description": "Mô tả tùy chọn",
  "objectFieldId": "{resolvedFieldId}",
  "finishStagesGroup": 1,
  "finishStagesGroupName": "Kết quả",
  "stages": [
    {
      "index": 1,
      "value": "new",
      "metaData": "{\"index\":1,\"value\":\"new\",\"label\":\"Mới\",\"category\":\"TO DO\",\"metaData\":\"\",\"instruction\":\"\",\"active\":true,\"hidden\":false,\"displayFields\":[],\"displayType\":1,\"layoutId\":null,\"action\":null}",
      "instruction": "",
      "action": null
    }
  ]
}
```

`name`, `slug`, `objectFieldId` và `stages` không rỗng là bắt buộc khi create. `status` mặc định server là `0` nếu bỏ qua. `description` có thể là `null` khi create.

### Stage wire body

Chỉ các key sau cần nằm ở cấp stage request:

```json
{
  "index": 1,
  "value": "new",
  "metaData": "{\"index\":1,\"value\":\"new\",\"label\":\"Mới\",\"category\":\"TO DO\",\"metaData\":\"\",\"instruction\":\"<p>Bắt đầu xử lý</p>\",\"active\":true,\"hidden\":false,\"displayFields\":[],\"displayType\":1,\"layoutId\":null,\"action\":null}",
  "instruction": "<p>Bắt đầu xử lý</p>",
  "action": null
}
```

Server tự sinh stage ID và tự suy `type`; không gửi ID cũ hay tự chọn `type` khi replace stages.

### JSON bên trong `metaData`

`metaData` là **JSON object được stringify thành string**, không phải object trực tiếp. UI đọc/ghi các key:

| Key | Kiểu | Ý nghĩa |
|---|---|---|
| `index` | integer | Mirror stage index, bắt đầu 1 |
| `value` | string | Mirror option slug |
| `label` | string | Nhãn option hiển thị hiện tại |
| `category` | string/null | Category option hiện tại |
| `metaData` | string | Metadata bổ sung của form, thường là `""` |
| `instruction` | string | HTML hướng dẫn; mirror key top-level |
| `active` | boolean | Trạng thái chọn trong form |
| `hidden` | boolean | Ẩn stage và vô hiệu cấu hình stage trong UI |
| `displayFields` | array | Field hiển thị và thứ tự |
| `displayType` | `1` hoặc `2` | `1` = fields, `2` = object layout |
| `layoutId` | string/null | Bắt buộc khi `displayType: 2` |
| `action` | string/null | Button/action-chain ID; mirror key top-level |
| `color` | string | Màu chữ RGBA của DONE stage |
| `bgColor` | string | Màu nền RGBA của DONE stage |

`displayFields` có dạng:

```json
[
  { "index": 0, "fieldId": "{fieldId}", "name": "Tên field", "required": false }
]
```

Giữ các key khác nếu detail hiện tại có. Cập nhật `instruction` và `action` ở cả top-level lẫn metadata để không tạo hai nguồn dữ liệu lệch nhau.

### Detail response

Path detail có các key:

```json
{
  "id": "{pathId}",
  "name": "Quy trình xử lý",
  "slug": "quy_trinh_xu_ly",
  "workspaceId": "{workspaceId}",
  "objectTypeId": "{objectId}",
  "objectSlug": "{objectSlug}",
  "objectFieldId": "{fieldId}",
  "status": 1,
  "description": "...",
  "finishStagesGroup": 1,
  "finishStagesGroupName": "Kết quả",
  "stages": [],
  "created": 0,
  "updated": 0,
  "createdBy": "{personnelId}",
  "updatedBy": "{personnelId}",
  "objectTypeName": "Đối tượng A",
  "objectFieldName": "Trạng thái"
}
```

Mỗi response stage còn có `id`, `workspaceId`, `pathComponentId`, `type`, timestamps và personnel IDs. Không dùng thứ tự mảng response; sort theo `index`.

## Quy tắc update và ordering

### Patch path-level

`POST .../update` yêu cầu `id` và `objectFieldId` hợp lệ. Các field không gửi sẽ được giữ nguyên đối với `name`, `description`, `status`, `finishStagesGroup`, `finishStagesGroupName`.

```json
{ "id": "{pathId}", "objectFieldId": "{currentFieldId}", "status": 0 }
```

- Endpoint update hiện không thay đổi `slug`.
- `objectFieldId` có thể đổi sang field single-choice/radio-button khác trong cùng object. Khi đổi field, bắt buộc gửi full stages được dựng từ option của field mới; không giữ stages cũ. Không trỏ sang field của object khác.
- `description: null` có nghĩa là giữ giá trị cũ. Chuỗi rỗng bị validation từ chối, nên contract hiện hành không có cách an toàn để xóa description; báo giới hạn thay vì ghi đè.

### Replace stages

- Bỏ `stages` hoặc gửi mảng rỗng: giữ stages hiện có.
- Gửi `stages` không rỗng: server xóa toàn bộ stages cũ và tạo lại từ payload.

Do đó, khi thay một stage:

1. GET detail mới nhất.
2. Sort theo `index`, parse metadata và merge targeted key.
3. Resolve lại option/field/layout/action có liên quan.
4. Reindex `displayFields` từ 0.
5. Xếp stage theo nhóm rồi reindex toàn cục từ 1.
6. Gửi full stages; không gửi stage ID cũ.

Server suy stage `type` từ category option:

| Option category | Stage type |
|---|---|
| `TO DO` | `start` |
| `IN PROGRESS` hoặc blank/null | `intermediate` |
| `DONE FAIL` | `finish` |
| `DONE PASS` | `finish` |

Indexes phải liên tiếp từ 1. Không đặt start stage sau intermediate; không đặt finish stage trước intermediate. UI chỉ cho reorder trong cùng nhóm.

## Layout, action và delete safety

### Resolve layout cho stage

```http
GET /api/v1/layouts/object/{objectSlug}?limit=1000&page=1
```

Match duy nhất layout theo ID hoặc tên chính xác. Với `displayType: 2`, UI chỉ cho layout view-capable:

- `functionLayout: 2` (VIEW), hoặc
- `functionLayout: 3` (ADD + VIEW).

### Resolve action

UI liệt kê button active cho object bằng:

```http
GET /api/v1/buttons?limit=1000&actionType=4,5,9,14&actionTypeOperator=IN&status=1&objectTypeSlug={objectSlug}
```

Current action types tương ứng create record, update record, create-or-update record và action chain. Lưu `button.id` vào `stage.action`; không lưu tên hoặc slug.

### Kiểm tra layout dùng path trước delete

```http
GET /api/v1/layouts/object/{objectSlug}?componentPathSlug={pathSlug}&limit=1000&page=1
```

Phân trang đến `lastPage`. Nếu `data` không rỗng, không gọi delete; liệt kê `id` và `name` của layout. Thực hiện check này cho cả path active và inactive.

## Validation và mã lỗi

Validation tối thiểu:

- Tối đa 50 path-component cho một object.
- `name`: bắt buộc khi create, không blank, tối đa 255; unique trong object.
- `slug`: bắt buộc khi create; UI dùng 2–100 ký tự, normalize về dạng `^[a-z][a-z0-9_]*$`; unique không phân biệt hoa/thường trong object.
- `description`: `null` hoặc chuỗi không blank tối đa 1000.
- `status`, `finishStagesGroup`: chỉ `0` hoặc `1` theo UI.
- `stages`: không rỗng khi create; index/value duy nhất; index liên tiếp từ 1; value phải là option slug của field.
- `displayType: 2`: phải có `layoutId` view-capable.
- `finishStagesGroup: 1`: chỉ dùng khi có DONE stage và phải có tên nhóm; màu `color`/`bgColor` thuộc metadata của DONE stages.

Mã `r` nghiệp vụ thường gặp:

| `r` | Ý nghĩa |
|---|---|
| `0` | Success |
| `1` | Success with data tại constraint |
| `405` | ID invalid |
| `407` | Name invalid/duplicate |
| `420` | Sort invalid |
| `434` | Description invalid |
| `435` | Slug invalid/duplicate |
| `439` | Stages empty khi create |
| `441` | Stage index/value/category order invalid |
| `501` | Path component not found |
| `506` | Object/field lookup không tồn tại trong context |
| `524` | Vượt giới hạn path cho object |

Không chỉ dựa vào HTTP 200; kiểm tra `r`, `msg`, `data`, sau đó read-after-write.

## Mẫu request

Mẫu tập trung vào contract; thay placeholder bằng giá trị đã resolve và dùng cookie/header từ `$cogover-api-auth`.

### Detail

```bash
curl --get 'https://{workspace-domain}/api/v1/object_security/path_component' \
  --data-urlencode 'id={pathId}' \
  --cookie 'HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}' \
  --header 'x-csrf-token: {XSRF-TOKEN}' \
  --header 'x-xsrf-token: {XSRF-TOKEN}'
```

### Deactivate không chạm stages

```bash
curl --request POST 'https://{workspace-domain}/api/v1/object_security/path_component/update' \
  --cookie 'HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}' \
  --header 'x-csrf-token: {XSRF-TOKEN}' \
  --header 'x-xsrf-token: {XSRF-TOKEN}' \
  --header 'Content-Type: application/json' \
  --data '{"id":"{pathId}","objectFieldId":"{currentFieldId}","status":0}'
```

### Delete sau dependency check và confirmation

```bash
curl --request POST 'https://{workspace-domain}/api/v1/object_security/path_component/delete' \
  --cookie 'HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}' \
  --header 'x-csrf-token: {XSRF-TOKEN}' \
  --header 'x-xsrf-token: {XSRF-TOKEN}' \
  --header 'Content-Type: application/json' \
  --data '{"id":"{pathId}"}'
```
