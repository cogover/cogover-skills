# Public Report API contract

## Mục lục

1. [Endpoint và xác thực](#endpoint-và-xác-thực)
2. [Gọi bằng phiên Web App](#gọi-bằng-phiên-web-app)
3. [Request/response](#requestresponse)
4. [Service dùng trong report-builder](#service-dùng-trong-report-builder)
5. [Payload mẫu](#payload-mẫu)
6. [Validation và semantics đặc biệt](#validation-và-semantics-đặc-biệt)
7. [Retry và idempotency](#retry-và-idempotency)

## Endpoint và xác thực

Gọi tất cả Report service qua:

```text
POST https://{workspace-domain}/bapi/v1/report
Authorization: Bearer {tokenId}-{secretToken}
Content-Type: application/json
```

Public API đặt service trong JSON body:

```json
{
  "service": 215,
  "payload": { "page": 0, "size": 20 }
}
```

Token xác định workspace và user; không gửi `workspace_id` hoặc dữ liệu xác thực trong `payload`. Luôn lấy workspace domain từ người dùng hoặc biến môi trường `COGOVER_WORKSPACE_DOMAIN`; không hard-code hostname của một workspace cụ thể.

## Gọi bằng phiên Web App

Trang hoặc Custom Frontend Module chạy trong Workspace gọi cùng các service bằng phiên của người dùng đang đăng nhập, không dùng API Key:

```text
POST https://{workspace-domain}/api/v1/report
Content-Type: application/json
x-req-type: 9
x-req-service: {service}
Cookie: HttpSessionId=...; XSRF-TOKEN=...; AuthToken=...
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
```

- Body là chính `payload` của service, không bọc `{ "service", "payload" }`. Trình duyệt tự gửi cookie; từ công cụ ngoài trình duyệt, tạo phiên theo `$cogover-api-auth`.
- Response là `{ r, msg, data }` ở root như Public API, không bọc envelope. Khác Public API, lỗi nghiệp vụ vẫn trả HTTP `200`: luôn kiểm tra `r` (ví dụ `r: 404` Report Type không tồn tại, `r: 5000` saved report không tồn tại, `r: 5001` sai `x-req-service`). Lỗi phiên do Authorization Server trả có HTTP `401` và header `x-proxy-error: 1` (ví dụ `r: 2` `TOKEN_NOT_VALID`); body không phải một JSON object trả HTTP `400`, `r: 400`.
- Không dùng `/api/v1/report-server` hoặc `x-req-type: 6`: cùng service và dữ liệu nhưng kết quả bị bọc trong `{ serviceVersion, service, id, type, body }`, lỗi phiên trả HTTP `403` không có `x-proxy-error`.
- Request chạy dưới danh tính và quyền của người sở hữu phiên. Kiểm chứng quyền của một persona bằng phiên của chính persona đó, không bằng phiên Super Admin.

## Request/response

`service` là integer và `payload` là object. Quy ước response hiện có:

- HTTP `201` cùng `r = 0`: thao tác thành công, kể cả list/view/update/delete.
- HTTP `400` cùng `r != 0`: lỗi nghiệp vụ hoặc payload; đọc `msg`.
- HTTP `200`: response không có `r`.
- HTTP `429`: rate limit; đọc `Retry-After`, `X-RateLimit-*`, `RateLimit-Reason`.
- HTTP `500`: lỗi server không mong muốn.

Contract không định nghĩa một response schema cố định cho từng service. Không hard-code rằng ID luôn nằm ở `data.id`, `result.id` hoặc một path khác. In/đọc response đã redacted, rồi xác minh resource bằng API list/detail.

## Service dùng trong report-builder

| Service | Thao tác | Payload bắt buộc | Ghi chú |
|---:|---|---|---|
| `200` | Chạy report | `report_id`, `filter_type` | `report_id` là Report Type ID |
| `201` | Tạo saved report | `report_type`, `name` | Có thể thêm slug, setting, folder, ACL |
| `202` | Khởi tạo Report Config | `report_id`, `relations`, `meta_data` | Luôn gọi sau `212`; report một object thêm `src_object_id`. Backend tự tạo section và report field cho mọi object trong graph |
| `203` | Xóa saved report | `ids` | Destructive; chỉ gọi khi được yêu cầu rõ |
| `207` | Cập nhật saved report | `id` | `acl` và `folder_id` có semantics thay thế |
| `208` | Tạo section | `report_id`, `section_name`, `section_index` | `report_id` ở đây là Report Type ID |
| `209` | Cập nhật section | `id`, `report_id`, `section_name`, `section_index` | Có thể thêm `section_type` |
| `210` | Xóa section | `id` | Destructive |
| `211` | List section | Không bắt buộc theo public catalog | Truyền `report_id` để giới hạn đúng Report Type; phân trang như `222` |
| `212` | Tạo Report Type | `report_type_name`, `report_type_slug`, `primary_object` | Không gửi `meta_data` |
| `213` | Cập nhật Report Type | `id`, `report_type_name`, `report_type_slug` | Gửi full desired state để tránh reset mặc định |
| `214` | Xóa Report Type | `ids` | Destructive |
| `215` | List/detail Report Type | Không có | Detail thường dùng `id` |
| `220` | List saved report | Không có | Hỗ trợ filter/sort/pagination |
| `221` | Xem relation của Report Type | `report_id` | `report_id` là Report Type ID |
| `222` | Xem report field | `report_id` | Wire key là `report_id`. Mặc định trả 50 dòng: gửi `size` (ví dụ `1000`) hoặc lặp `page` từ `1` tới đủ `data.total` |
| `223` | List relation có thể dùng | Không có | Resolve `object_relation_id` thật |
| `225` | Sắp xếp section | `sections` | Mỗi item `{section,index}` |
| `226` | Cập nhật report field | `id` | Tên, status, section, index là optional |
| `227` | Thêm report field | `report_type_id`, `field` | Thêm một field |
| `228` | Xóa report field | `report_type_id`, `id` | Destructive |
| `229` | Detail saved report | `report_id` hoặc `slug` | Dùng đúng một định danh |
| `230` | Kiểm tra field đang được dùng | `object_type_id`, `field_id` | Gọi trước thao tác field phá hủy |
| `231` | Cập nhật relation Report Type | `report_id`, `relations` | `relations` cần ít nhất một phần tử; `relations: []` trả `r: 4` |
| `232` | Sắp xếp field | `section_id`, `fields` | Mỗi item có ID và index |
| `239` | Kiểm tra slug saved report | `slug` | Đọc `data.exists`: `false` là slug còn trống; `msg` là `Failed` kể cả khi `r: 0` |
| `246` | Evaluate formula | `script`, `return_type` | Chỉ dùng khi có formula |

## Payload mẫu

### Tạo Report Type (`212`)

```json
{
  "report_type_name": "Báo cáo doanh thu",
  "report_type_slug": "bao_cao_doanh_thu",
  "report_type_description": "Doanh thu theo thời gian",
  "primary_object": "<OBJECT_ID>",
  "category": "OTHER",
  "status": 1
}
```

Trạng thái: `0` draft, `1` development, `2` deployed. Không đưa `meta_data` vào `212`; tạo Report Config và relation metadata bằng service `202`.

### Khởi tạo Report Config một object (`202`)

```json
{
  "report_id": "<REPORT_TYPE_ID>",
  "relations": [],
  "src_object_id": "<PRIMARY_OBJECT_ID>",
  "meta_data": "{\"nodes\":[{\"id\":\"<PRIMARY_OBJECT_ID>\",\"type\":\"nodeRoot\",\"position\":{\"x\":0,\"y\":0},\"data\":{\"title\":\"Đối tượng chính\",\"content\":\"<OBJECT_DISPLAY_NAME>\"},\"selected\":false}],\"edges\":[],\"viewport\":{\"x\":0,\"y\":0,\"zoom\":1}}"
}
```

Với nhiều object, thay `relations: []` bằng toàn bộ relation đã xác minh và đưa child node/edge tương ứng vào cùng graph. Mỗi edge bắt buộc có `data.lookup_type` và `data.source_name` ngoài `src_object_id`, `dst_object_id`, `relation_type`, `object_relation_id`, `field_slug`. Không dùng `meta_data: "{}"`; service `202` yêu cầu graph đầy đủ. Xem shape và semantics hướng lookup trong [report-modeling.md](report-modeling.md).

### Tạo section (`208`)

```json
{
  "report_id": "<REPORT_TYPE_ID>",
  "section_name": "Phần mới",
  "section_index": 1000,
  "section_type": 1
}
```

`section_type: 1` là section hiển thị; `0` là ẩn. Chỉ dùng `208` để thêm section sau khi đã đọc `211`; gửi `section_index: 1000` cho section mới. Default section persisted với index `0` là state backend tạo hoặc chuẩn hóa sau `202`, không phải payload của service `208`.

### Thêm field (`227`)

```json
{
  "report_type_id": "<REPORT_TYPE_ID>",
  "field": {
    "object_type_id": "<OBJECT_ID>",
    "field_name": "Tổng tiền",
    "section_id": "<SECTION_ID>",
    "field_slug": "total_amount",
    "field_type": 0,
    "status": 0,
    "index_in_section": 0
  }
}
```

`field_type`: `0` normal/direct, `1` lookup path. Dùng `status: 0` khi thêm field; không nhầm với status của object field hoặc Report Type.

`field_name` lấy từ display `name` của object field mà object API trả về.

Sau `202`, backend tự tạo một section cho mỗi object trong graph (primary object ở `section_index: 0`) và thêm vào đó report field (`field_type: 0`) cho mọi field của object, gồm field hệ thống `workspace_id`, `object_type`. Đọc đủ các trang của `222` rồi dùng report field ID sẵn có; chỉ gọi `227` cho field chưa có trong `222`, ví dụ field đã xoá bằng `228`. Gọi `227` cho field đã có trả `r: -1` `Field [<field_slug>] already exists`.

### Tạo saved report (`201`)

```json
{
  "report_type": "<REPORT_TYPE_ID>",
  "name": "Doanh thu theo tháng",
  "slug": "doanh_thu_theo_thang",
  "description": "",
  "folder_id": null,
  "setting": {},
  "acl": []
}
```

Không truyền ACL rộng mặc định chỉ để payload giống ví dụ. Hỏi người dùng hoặc dùng default backend đã được workspace xác nhận.

### List/detail

```json
{ "service": 215, "payload": { "id": "<REPORT_TYPE_ID>" } }
```

```json
{ "service": 229, "payload": { "slug": "doanh_thu_theo_thang" } }
```

```json
{
  "service": 220,
  "payload": {
    "page": 0,
    "size": 50,
    "filter": { "op": "and", "conditions": [] },
    "sorts": [{ "field": "updated", "order": "desc" }]
  }
}
```

## Validation và semantics đặc biệt

- Service `215`: `status` phải là mảng integer khi truyền vào filter.
- Service `202`: luôn gửi `report_id`, `relations`, `meta_data`; khi `relations` rỗng phải có `src_object_id`.
- Mỗi request relation có tối đa 4 relation; `relation_type` chỉ nhận `1` inner hoặc `2` left.
- Mỗi relation trong `202/231.meta_data` phải có đúng một edge khớp cùng `src_object_id`, `dst_object_id`, `relation_type` và `object_relation_id`.
- `edge.data.lookup_type`: `2` khi parent graph là relation source (“Tra cứu từ alias parent”); `1` khi parent graph là relation destination (“Tra cứu tới alias parent”).
- `edge.data.source_name` là alias của parent node theo thứ tự graph (`A` cho root, tiếp theo `B`, `C`, `D`, `E`). Không bỏ hai key này: UI dùng chúng để dựng chiều lookup và biểu thức JOIN.
- Service `231`: `relations` phải có ít nhất một phần tử. `relations: []`, kể cả khi có `src_object_id`, trả `r: 4` `Relations are required`; không dùng `231` để đưa Report Type về một object.
- Service `239`: response `{ "r": 0, "msg": "Failed", "data": { "exists": <boolean> } }`; `msg` không báo lỗi, chỉ dùng `data.exists`.
- Service `200`: `filter_type` là `1` AND, `2` OR, `3` custom; `logic_sequence` dùng với `3`.
- Service `200`: `size` mặc định `9999`, tối đa `10000`.
- Service `200` không có `setting: true` trả `r: 32` (`Wait for response`) kèm `data.id`, kết quả không nằm trong response (HTTP `400` với Public API, HTTP `200` với phiên Web App). Gửi `setting: true` để chạy đồng bộ và nhận `data` gồm `rows`, `summary`, `total` trong cùng response; đây là cách dùng khi code cần đọc kết quả.
- `group_rows` và `group_columns` nhận tối đa 2 field ID mỗi mảng.
- Aggregate hợp lệ: `sum`, `avg`, `count`, `max`, `min`, `median`.
- `setting` bị overload: service `201/207` dùng object cấu hình saved report; service `200` dùng boolean để yêu cầu tính đồng bộ.
- `report_id` bị overload: `200/202/208/211/221/222/231` dùng Report Type ID; `229` dùng saved report ID hoặc slug.
- `meta_data` của Report Config/relation là JSON string; `setting` của saved report là JSON object. Service `212` không nhận `meta_data`.
- Service `207`: bỏ `folder_id` có thể đưa report ra khỏi folder; bỏ `acl` có thể xóa ACL hiện tại. Fetch → merge → update.
- Service `213`: gửi full desired state; bỏ description/category/status/metadata có thể reset về mặc định.
- ACL report/Report Type dùng `acl`; folder dùng `accessControls`.
- ACL `option`: `1` all, `2` include, `3` exclude. `type`: `personnel`, `owner`, `position`, `department`, `role`. Public API nhận các function `VIEW`, `EDIT`, `ADD`, `DELETE`, `EXECUTE`.

## Retry và idempotency

- Retry một read request tối đa một lần khi timeout.
- Không blind-retry `201`, `202`, `207`, `208`, `212`, `227` hoặc mutation khác.
- Sau timeout create, tìm resource bằng slug/name và kiểm tra relation/field trước khi gọi lại.
- Sau HTTP `429`, chờ theo `Retry-After`; không đổi payload hoặc tạo request song song.
- Khi một bước thất bại, ghi lại resource ID đã tạo. Không tự gọi delete vì contract không mô tả soft-delete, cascade hoặc undo.
