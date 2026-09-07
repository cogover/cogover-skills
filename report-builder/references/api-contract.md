# Public Report API contract

## Mục lục

1. [Endpoint và xác thực](#endpoint-và-xác-thực)
2. [Request/response](#requestresponse)
3. [Service dùng trong report-builder](#service-dùng-trong-report-builder)
4. [Payload mẫu](#payload-mẫu)
5. [Validation và semantics đặc biệt](#validation-và-semantics-đặc-biệt)
6. [Retry và idempotency](#retry-và-idempotency)

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
| `202` | Khởi tạo Report Config | `report_id`, `relations`, `meta_data` | Luôn gọi sau `212`; report một object thêm `src_object_id` |
| `203` | Xóa saved report | `ids` | Destructive; chỉ gọi khi được yêu cầu rõ |
| `207` | Cập nhật saved report | `id` | `acl` và `folder_id` có semantics thay thế |
| `208` | Tạo section | `report_id`, `section_name`, `section_index` | `report_id` ở đây là Report Type ID |
| `209` | Cập nhật section | `id`, `report_id`, `section_name`, `section_index` | Có thể thêm `section_type` |
| `210` | Xóa section | `id` | Destructive |
| `211` | List section | Không bắt buộc theo public catalog | Truyền `report_id` để giới hạn đúng Report Type |
| `212` | Tạo Report Type | `report_type_name`, `report_type_slug`, `primary_object` | Không gửi `meta_data` |
| `213` | Cập nhật Report Type | `id`, `report_type_name`, `report_type_slug` | Gửi full desired state để tránh reset mặc định |
| `214` | Xóa Report Type | `ids` | Destructive |
| `215` | List/detail Report Type | Không có | Detail thường dùng `id` |
| `220` | List saved report | Không có | Hỗ trợ filter/sort/pagination |
| `221` | Xem relation của Report Type | `report_id` | `report_id` là Report Type ID |
| `222` | Xem report field | `report_id` | Wire key là `report_id` |
| `223` | List relation có thể dùng | Không có | Resolve `object_relation_id` thật |
| `225` | Sắp xếp section | `sections` | Mỗi item `{section,index}` |
| `226` | Cập nhật report field | `id` | Tên, status, section, index là optional |
| `227` | Thêm report field | `report_type_id`, `field` | Thêm một field |
| `228` | Xóa report field | `report_type_id`, `id` | Destructive |
| `229` | Detail saved report | `report_id` hoặc `slug` | Dùng đúng một định danh |
| `230` | Kiểm tra field đang được dùng | `object_type_id`, `field_id` | Gọi trước thao tác field phá hủy |
| `231` | Cập nhật relation Report Type | `report_id`, `relations` | Có thể gửi `relations: []` cùng `src_object_id` cho graph một object |
| `232` | Sắp xếp field | `section_id`, `fields` | Mỗi item có ID và index |
| `239` | Kiểm tra slug saved report | `slug` | Shape response chưa được đặc tả |
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

`field_name` lấy từ display `name` của object field mà object API trả về. Nếu `workspace_id` hoặc `object_type` xuất hiện sau `202`, coi đó là field hệ thống backend tạo và không gọi `227` để tái tạo.

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
- Service `231`: `relations` có thể rỗng khi có `src_object_id`.
- Service `200`: `filter_type` là `1` AND, `2` OR, `3` custom; `logic_sequence` dùng với `3`.
- Service `200`: `size` mặc định `9999`, tối đa `10000`.
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
