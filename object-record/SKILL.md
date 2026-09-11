---
name: object-record
description: "Quản lý bản ghi Cogover Object qua Records API `/bapi/v1/records` (lấy danh sách có lọc/phân trang, tạo, cập nhật, xoá) và upload/gắn file, chèn ảnh local vào long-text WYSIWYG bằng phiên Web App. Dùng khi cần thao tác record, tạo record kèm file hoặc ảnh trong cùng request, hoặc đính kèm file vào record hiện có; xoá phải xác nhận trước."
metadata:
  author: cogover
  version: "1.0.3"
---

# Object Record

- **Phiên bản:** `1.0.3`
- **Ngày phát hành:** `2026-09-11`

Sub-agent thao tác bản ghi (record) của một Cogover Object; skill khác gọi skill này khi cần đọc/ghi record. Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Các API record dùng `/bapi/v1` với API Key Bearer; riêng upload file và gắn file vào record đã tồn tại dùng `/api/v1` bằng phiên Web App (đổi từ API Key qua `$cogover-api-auth`; không tạo được phiên thì dừng và báo người dùng, không gọi `/api/v1` bằng API Key).

## Chuẩn bị

- Object ID, `object_slug` và fields của Object: lấy qua `$object-info` nếu chưa có. Với field file luôn lấy `slug`, `fieldType` và `multiple` từ metadata; không suy đoán từ tên hiển thị.
- Upload file/ảnh WYSIWYG: cần đường dẫn tuyệt đối tới file (tồn tại, không rỗng), metadata field đích và phiên Web App; chỉ cần ID bản ghi khi gắn vào record đã tồn tại.
- Các khả năng A–E độc lập, không cần gọi theo thứ tự.

## A. Lấy danh sách — `POST /bapi/v1/records/list`

```json
{
  "object_slug": "{OBJECT_SLUG}",
  "type": {TYPE},
  "logic_sequence": "{LOGIC_SEQUENCE}",
  "filters": [{FILTERS}],
  "sorts": [{"{SORT_FIELD}": {"order": "{SORT_ORDER}"}}],
  "order_direction": "next",
  "search_after": [],
  "size": {SIZE},
  "show_detail_on_record": false
}
```

- `type` (số, ở cấp cao nhất, luôn truyền tường minh, không dựa vào mặc định): `1` AND, `2` OR, `3` CUSTOM. Đã kiểm chứng: thiếu `type` trả HTTP 400, `r: 27`, `msg: Invalid filter type`; cùng request thêm `type: 1` thành công. `type` khác `filters[].fieldType`; không sửa `fieldType` để chữa lỗi này.
- `logic_sequence`: `""` khi `type` là `1`/`2`; khi `3` là biểu thức như `"1 AND (2 OR 3)"` (số là thứ tự phần tử trong `filters`, bắt đầu từ 1).
- `filters[]`: `{"field": "<slug>", "op": "<toán tử>", "params": <null | string | number | array>, "fieldType": "<fieldType từ $object-info>"}`. Toán tử và kiểu `params` theo từng `fieldType`: [records_filter_conditions.md](records_filter_conditions.md). Lấy tất cả bản ghi: `{"field": "id", "op": "not null", "params": null, "fieldType": "short_text"}`; lọc trạng thái: `{"field": "status", "op": "in", "params": ["new", "nurturing"], "fieldType": "single_choice"}`.
- `sorts`: field mặc định `updated`; `order` là `desc` (mới nhất trước) hoặc `asc`.
- `size`: mặc định `20`, tối đa `200`. Phân trang: lần đầu `"search_after": []`, các lần sau truyền `data.search_after` của response trước.

Response: `data.total` (tổng bản ghi phù hợp), `data.rows[]` (mỗi bản ghi gồm `id`, `name`, `created`, `updated`, `created_by{id,name}` và các field theo Object), `data.search_after` (mảng, dùng cho trang tiếp); ngoài `data` còn `personnelId`, `workspaceDomain`, `workspaceId`. Giá trị trong `rows`:

- `boolean`: `0`/`1`, không phải `true`/`false`.
- `url`: mảng object `[{"alias": "", "url": "https://..."}]`, không phải mảng string.
- `lookup_normal`/`reference`: full object của bản ghi được lookup (`id`, `name` và các field khác).

## B. Tạo — `POST /bapi/v1/records`

```json
{"object_slug": "{OBJECT_SLUG}", "data": {"{FIELD_SLUG}": {VALUE}}, "client_time_zone": "Asia/Saigon"}
```

`data` chứa các cặp `field_slug: value` đúng kiểu theo bảng dưới, gồm mọi field bắt buộc. Thành công: `r: 0`, `data.id` là ID bản ghi mới (dùng cho cập nhật/xoá); lỗi: `r: 1` kèm `msg`.

### Giá trị theo kiểu trường (dùng cho B và C)

| Kiểu trường | Giá trị | Ví dụ |
|---|---|---|
| `short_text`, `phone`, `email` | String | `"Nguyễn Văn A"`, `"0901234567"`, `"a@example.com"` |
| `long_text` | String; bật WYSIWYG: object | `"Mô tả..."`; `{"value":"<div>...</div>","text_type":2}` |
| `boolean` | `true`/`false` (response trả `1`/`0`) | `true` |
| `single_choice` | Slug của option | `"new"`, `"qualified"` |
| `multi_choices` | Mảng slug option | `["option1", "option2"]` |
| `numeric`, `currency`, `rating` | Number | `100`, `1500000`, `3` |
| `percent` | Number 0–1 | `0.75` |
| `date` | String `YYYY-MM-DD` | `"2026-02-12"` |
| `date_time`, `time_duration` | Timestamp (ms) | `1770650967000`; `3600000` (1 giờ) |
| `url` | Object (đơn) hoặc mảng object (nhiều) | `{"alias":"","url":"https://example.com"}`; `[{"alias":"","url":"https://a.example.com"},{"alias":"","url":"https://b.example.com"}]` |
| `regex` | String khớp pattern `metaData.regex` của field trong object info | Pattern `^\d{12}$` → `"123456789012"` |
| `lookup_normal`, `reference` | Record ID | `"PER00000000003"` |
| `file` | Metadata upload: object nếu đơn, mảng nếu `multiple` | [references/upload-file.md](references/upload-file.md) |

### Tạo kèm file

Theo [references/upload-file.md](references/upload-file.md): upload riêng cho từng field đích bằng phiên Web App để lấy `FILE_METADATA`, rồi đưa metadata vào `data` của đúng một request create cùng các field thường và bắt buộc (field đơn: object, field đa: mảng). Không gọi thêm `POST /api/v1/records` sau khi create trả `r: 0`. Đọc lại record để xác minh.

### Tạo kèm ảnh local trong long-text WYSIWYG

Theo [references/wysiwyg-long-text-images.md](references/wysiwyg-long-text-images.md): lấy ID field hệ thống `_attachments` và ID field WYSIWYG qua `$object-info` (không có `_attachments` thì dừng), upload ảnh bằng phiên Web App theo field ID và Object ID, rồi tạo record bằng đúng một request `/bapi/v1/records` với metadata ảnh trong `data._attachments` và field WYSIWYG dạng `{"value":"<HTML>","text_type":2}`.

## C. Cập nhật — `PUT /bapi/v1/records/{RECORD_ID}`

```json
{"object_slug": "{OBJECT_SLUG}", "data": {"{FIELD_SLUG}": {VALUE}}}
```

`data` chỉ chứa các field cần cập nhật, giá trị theo bảng ở B. `RECORD_ID` lấy từ kết quả A hoặc từ người dùng. Thành công: `r: 0`, `data: {}`. `r: 1` với `msg: "Record not existed"`: RECORD_ID sai hoặc bản ghi đã bị xoá; báo người dùng kiểm tra lại hoặc dùng A để tìm.

## D. Xoá — `POST /bapi/v1/records/delete`

Hành động không thể hoàn tác. BẮT BUỘC liệt kê ID (và tên nếu có) các bản ghi sẽ xoá, hỏi và chỉ gọi API khi người dùng xác nhận đồng ý; người dùng từ chối thì huỷ và thông báo.

```json
{"object_type": "{OBJECT_TYPE_ID}", "ids": ["{RECORD_ID_1}", "{RECORD_ID_2}"]}
```

`object_type` là ID của Object (ví dụ `OT00000000011`, lấy qua `$object-info`); `ids` nhận nhiều bản ghi cùng lúc. Thành công: `r: 0`, `data.deleted[]` (đã xoá) và `data.not_deleted[]` (không xoá được). `r: 1` với `msg: "Record not existed"`: có ID sai hoặc đã bị xoá trước đó.

## E. Gắn file vào bản ghi hiện có

Thực hiện bằng API, không dùng trình duyệt. Đọc [references/upload-file.md](references/upload-file.md) trước khi gọi.

1. Xác định `WORKSPACE_DOMAIN`, `OBJECT_SLUG` và `RECORD_ID` từ URL bản ghi hoặc ngữ cảnh; xác minh file cục bộ tồn tại và không rỗng.
2. Dùng `$object-info` lấy `OBJECT_TYPE_ID` và xác minh từng field đích có `fieldType=file`; giữ nguyên `FILE_FIELD_SLUG` và cờ `multiple` từ metadata.
3. Tạo phiên Web App qua `$cogover-api-auth` cho các endpoint `/api/v1`.
4. Upload riêng cho từng field đích bằng `POST /api/v1/file/upload/v2/client_upload`; cùng một file gắn vào nhiều field vẫn cần mỗi field một request với `field_slug` tương ứng và một `FILE_METADATA` riêng. Chỉ tiếp tục khi upload trả HTTP `2xx`, `r: 0` và có object `data`.
5. Sau khi mọi upload thành công, gắn metadata bằng `POST /api/v1/records`; có thể gắn nhiều field trong cùng request, không tái sử dụng metadata cho field khác. Field đơn (`multiple=false`) gửi object, field đa (`multiple=true`) gửi mảng; nếu người dùng muốn thêm file mà không thay file cũ, đọc giá trị hiện tại và nối metadata mới trước khi gửi.
6. Hoàn tất chỉ khi request gắn file trả HTTP `2xx` và `r: 0` (kiểm tra cả `body.r`). Báo tên file, Object/field slug, cờ đơn/đa, ID bản ghi và kết quả từng bước.

## Trả kết quả

- Người dùng gọi trực tiếp: bảng hoặc danh sách dễ đọc. Danh sách: các trường quan trọng (`id`, `name`, `status`, `created`...); nhiều bản ghi thì tóm tắt và hỏi có xem thêm không. Tạo: kèm ID bản ghi mới. Xoá: nhấn mạnh bản ghi đã bị xoá vĩnh viễn. Upload: như bước 6 của E.
- Skill khác gọi: trả dữ liệu có cấu trúc để skill gọi dùng trực tiếp.

## Xử lý lỗi

| Lỗi | Cách xử lý |
|---|---|
| `r: 27` — Invalid filter type | Request `/records/list` thiếu hoặc sai `type`: thêm `type` số `1`/`2`/`3` ở cấp cao nhất và đối chiếu `logic_sequence`. Không thay `filters[].fieldType` để chữa. |
| `r: 1` — Record not existed | RECORD_ID sai hoặc bản ghi đã bị xoá; kiểm tra lại hoặc dùng A để tìm. |
| `r: 626` khi gắn file (`not found file id`) | Sai kiểu đơn/đa: không bọc object metadata trong mảng với field đơn. |
| Timeout hoặc mất kết nối khi upload, gắn file, create | Không tự retry vì thao tác ghi có thể đã xảy ra; báo kết quả chưa xác định, chỉ thử lại khi người dùng yêu cầu rõ. Timeout khi đọc: thử lại khi phù hợp yêu cầu. |
| Create lỗi sau khi upload | Báo các file ID đã upload có thể bị mồ côi; không tự retry create. |
| Không tạo được phiên Web App | Dừng và báo người dùng; không gọi `/api/v1` bằng API Key. |
| Không tìm thấy field `_attachments` | Đọc lại Object fields; không upload ảnh WYSIWYG khi chưa xác định được field ID này. |
