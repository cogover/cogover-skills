---
name: object-record
description: Quản lý bản ghi Cogover Object qua API, gồm lấy danh sách, tạo, cập nhật, xoá, upload/gắn file và chèn ảnh local vào trường long-text WYSIWYG. Sử dụng khi cần thao tác dữ liệu record, tạo record mới kèm file hoặc ảnh rich-text trong cùng request, hoặc đính kèm file vào record hiện có.
metadata:
  author: cogover
  version: "1.0.2"
---

# Object Record

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-07`

## Kích hoạt
- Lệnh: `/object-record`
- Người dùng có thể gọi: có
- Được sử dụng như sub-agent bởi các skill khác khi cần thao tác với bản ghi (record) của Cogover Object

## Mô tả
Sub-agent chuyên thao tác với bản ghi (record) của một Object trong hệ thống Cogover. Hỗ trợ lấy danh sách, tạo, cập nhật, xoá bản ghi và upload file vào field của bản ghi. Agent cần biết thông tin đối tượng (Object ID/slug và fields) để thực hiện — gọi skill `$object-info` để lấy nếu cần.

## Yêu cầu
- **WORKSPACE_DOMAIN**: Bắt buộc. Domain của workspace (ví dụ: `mycompany.cogover.net`). Nếu chưa có, hỏi người dùng trước khi thực hiện.
- **API_KEY**: Bắt buộc. Người dùng cần cung cấp API key để xác thực. Nếu chưa có, hỏi người dùng trước khi thực hiện.
- **Upload file/ảnh WYSIWYG**: Cần đường dẫn tuyệt đối tới file, metadata field đích và phiên Web App hợp lệ; chỉ cần ID bản ghi khi gắn vào record đã tồn tại. Dùng `$cogover-api-auth` để đổi API key thành phiên khi cần.

## Hướng dẫn thực hiện

### Bước 1: Xác nhận WORKSPACE_DOMAIN và API_KEY
- Nếu người dùng chưa cung cấp WORKSPACE_DOMAIN hoặc API_KEY, hỏi người dùng.
- Nếu đã có từ ngữ cảnh trước đó, sử dụng luôn.

### Bước 2: Xác định đối tượng (Object)
- Người dùng cần chỉ định đối tượng muốn thao tác (ví dụ: Lead, Contact, Order,...).
- Nếu chưa biết Object ID, `object_slug` hoặc thông tin fields của đối tượng, gọi skill `$object-info` để lấy. Với field file, luôn lấy cả `slug`, `fieldType` và `multiple`; không suy đoán từ tên hiển thị.

### Bước 3: Thực hiện theo yêu cầu

Tuỳ theo ngữ cảnh, thực hiện một hoặc nhiều khả năng bên dưới. Các khả năng này **độc lập với nhau**, không cần gọi theo thứ tự.

---

## Các khả năng

### Khả năng A: Lấy danh sách bản ghi (List Records)

Sử dụng khi cần lấy, tìm kiếm, hoặc lọc danh sách bản ghi của một đối tượng.

#### Gọi API

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/records/list' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "order_direction": "next",
    "logic_sequence": "{LOGIC_SEQUENCE}",
    "search_after": [],
    "size": {SIZE},
    "object_slug": "{OBJECT_SLUG}",
    "sorts": [
        {
            "{SORT_FIELD}": {
                "order": "{SORT_ORDER}"
            }
        }
    ],
    "show_detail_on_record": false,
    "filters": [
        {FILTERS}
    ],
    "type": {TYPE}
}'
```

**Lưu ý:**
- Thay `{API_KEY}` bằng giá trị thực từ người dùng.
- Thay `{OBJECT_SLUG}` bằng slug của đối tượng (ví dụ: `lead`, `contact`, `order`).
- `{SIZE}`: Số lượng bản ghi trả về mỗi trang (mặc định `20`, tối đa `200`).
- `{SORT_FIELD}`: Trường sắp xếp (mặc định `updated`).
- `{SORT_ORDER}`: Hướng sắp xếp — `desc` (mới nhất trước) hoặc `asc` (cũ nhất trước).
- `{TYPE}`: Chế độ kết hợp điều kiện lọc — `1` = AND (tất cả điều kiện phải thoả), `2` = OR (chỉ cần một điều kiện thoả), `3` = CUSTOM (dùng biểu thức `logic_sequence` tuỳ chỉnh). Luôn truyền số `type` tường minh ở cấp cao nhất của request body; dùng `1` khi cần AND, không dựa vào giá trị mặc định khi bỏ key. Đã kiểm chứng request thiếu `type` trả HTTP 400, `r: 27`, `msg: Invalid filter type`; cùng request thêm `type: 1` thành công. `type` này khác `filters[].fieldType`.
- `{LOGIC_SEQUENCE}`: Biểu thức logic kết hợp các điều kiện lọc. Để trống `""` khi `type` là `1` hoặc `2`. Chỉ cần thiết lập khi `type` là `3`, ví dụ: `"1 AND (2 OR 3)"`. Xem thêm records_filter_conditions.md.
- `{FILTERS}`: Mảng các điều kiện lọc. Xem chi tiết tại **Phần bộ lọc** bên dưới.

#### Phần bộ lọc (Filters)

Mỗi điều kiện lọc có cấu trúc:
```json
{
    "field": "{FIELD_SLUG}",
    "op": "{OPERATOR}",
    "params": {VALUE},
    "fieldType": "{FIELD_TYPE}"
}
```

- `field`: Slug của trường dữ liệu.
- `op`: Toán tử so sánh.
- `params`: Giá trị lọc (có thể là `null`, string, number, array tuỳ toán tử).
- `fieldType`: Loại trường dữ liệu (ví dụ: `single_choice`, `multi_choices`, `short_text`,...). Giá trị này khớp với `fieldType` trả về từ API `/object-info`.

**Tham khảo chi tiết danh sách toán tử và kiểu dữ liệu tại:** file `records_filter_conditions.md` trong cùng thư mục skill này.

**Ví dụ bộ lọc — lấy tất cả bản ghi (không lọc gì):**
```json
"filters": [
    {
        "field": "id",
        "op": "not null",
        "params": null,
        "fieldType": "short_text"
    }
]
```

**Ví dụ bộ lọc — lọc theo trạng thái:**
```json
"filters": [
    {
        "field": "status",
        "op": "in",
        "params": ["new", "nurturing"],
        "fieldType": "single_choice"
    }
]
```

#### Phân trang (Pagination)

Sử dụng `search_after` để phân trang:
- Lần đầu: `"search_after": []`
- Các lần tiếp theo: lấy giá trị `search_after` từ response trước truyền vào.

#### Cấu trúc response

```json
{
    "msg": "OK",
    "r": 0,
    "data": {
        "search_after": [1770650967000, "notgf0rqnekmue"],
        "total": 2,
        "rows": [
            {
                "id": "NO000000000120",
                "name": "All",
                "created": 1770650967471,
                "updated": 1770650968000,
                "created_by": {
                    "name": "Automation Cogover",
                    "id": "AUTOMATION-CGV"
                },
                ...
            }
        ]
    }
}
```

#### Xử lý kết quả

- `r`: Mã kết quả — `0` là thành công, khác `0` là lỗi.
- `data.total`: Tổng số bản ghi phù hợp.
- `data.rows`: Mảng các bản ghi, mỗi bản ghi chứa các trường dữ liệu theo cấu trúc đối tượng.
- `data.search_after`: Giá trị dùng để phân trang tiếp.
- `personnelId`: ID người thực hiện request.
- `workspaceDomain`: Domain của workspace.
- `workspaceId`: ID của workspace.

**Lưu ý về giá trị trả về trong `data.rows`:**
- Trường `boolean`: trả về `0` (false) hoặc `1` (true), không phải `true`/`false`.
- Trường `url`: trả về mảng object `[{"alias": "", "url": "https://..."}]`, không phải mảng string.
- Trường `lookup_normal`/`reference`: trả về full object của bản ghi được lookup (bao gồm id, name, và các trường khác).

---

### Khả năng B: Tạo bản ghi (Create Record)

Sử dụng khi cần tạo mới một bản ghi cho một đối tượng.

#### Chuẩn bị dữ liệu

Trước khi tạo bản ghi, cần biết:
- `object_slug` của đối tượng.
- Danh sách các trường (fields) và kiểu dữ liệu của chúng — gọi skill `/object-info` nếu chưa có.
- Giá trị cho các trường bắt buộc (required fields).
- Với file: đường dẫn file, field slug và cờ `multiple` của từng field.

#### Gọi API

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/records' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "object_slug": "{OBJECT_SLUG}",
    "data": {
        "{FIELD_SLUG_1}": "{VALUE_1}",
        "{FIELD_SLUG_2}": "{VALUE_2}"
    },
    "client_time_zone": "Asia/Saigon"
}'
```

**Lưu ý:**
- Thay `{API_KEY}` bằng giá trị thực từ người dùng.
- Thay `{OBJECT_SLUG}` bằng slug của đối tượng (ví dụ: `lead`, `contact`).
- Trong `data`, truyền các cặp `field_slug: value` theo đúng kiểu dữ liệu của trường.

#### Tạo record mới kèm file

Đọc [references/upload-file.md](references/upload-file.md), rồi thực hiện nhánh **Tạo record mới kèm file**:

1. Tạo phiên Web App và upload file riêng cho từng field đích để lấy `FILE_METADATA`; không tái sử dụng metadata của field khác.
2. Đưa metadata trực tiếp vào `data` của một lần `POST /bapi/v1/records`: field đơn nhận object, field đa nhận mảng metadata.
3. Gửi cả field thường, field bắt buộc và mọi field file trong cùng request create. Khi create trả HTTP thành công và `r: 0`, không gọi thêm `POST /api/v1/records`.
4. Đọc lại record để xác minh. Nếu create thất bại sau khi upload, báo các file ID có thể bị mồ côi và không retry mù quáng.

#### Tạo record có ảnh local trong long-text WYSIWYG

Đọc đầy đủ [references/wysiwyg-long-text-images.md](references/wysiwyg-long-text-images.md). Dùng ID của field hệ thống `_attachments` và Object ID để upload ảnh bằng phiên Web App; nếu không tạo được phiên qua `$cogover-api-auth`, dừng và báo người dùng. Sau đó gửi metadata ảnh vào `data._attachments`, gửi field WYSIWYG dưới dạng `{"value":"<HTML>","text_type":2}` và tạo record bằng đúng một request `/bapi/v1/records` dùng API Key. Không dùng các cookie `deviceId`, `workspace_openning_ids` hoặc `app_ids_by_position`.

#### Quy tắc giá trị theo kiểu trường

| Kiểu trường     | Giá trị truyền vào    | Ví dụ                                        |
|-----------------|-----------------------|----------------------------------------------|
| `short_text`    | String                | `"Nguyễn Văn A"`                             |
| `long_text`     | String hoặc object WYSIWYG | Thường: `"Mô tả..."`; WYSIWYG: `{"value":"<div>...</div>","text_type":2}` |
| `phone`         | String                | `"0901234567"`                               |
| `email`         | String                | `"a@example.com"`                            |
| `boolean`       | Boolean               | `true`, `false` (response trả về `1`/`0`)    |
| `single_choice` | Slug của option       | `"new"`, `"qualified"`                       |
| `multi_choices` | Mảng slug của options | `["option1", "option2"]`                     |
| `numeric`       | Number                | `100`                                        |
| `date`          | String (YYYY-MM-DD)   | `"2026-02-12"`                               |
| `date_time`     | Timestamp (ms)        | `1770650967000`                              |
| `url`           | Object (đơn) hoặc Mảng object (nhiều) | Đơn: `{"alias":"","url":"https://example.com"}`, Nhiều: `[{"alias":"","url":"https://a.example.com"},{"alias":"","url":"https://b.example.com"}]` |
| `currency`      | Number                | `1500000`                                    |
| `percent`       | Number (0-1)          | `0.75`                                       |
| `rating`        | Number                | `1`, `3`, `5`                                |
| `regex`         | String (phải match regex pattern cấu hình trên field, lấy từ `metaData.regex` trong object info) | Field có regex `^\d{12}$` → `"123456789012"` |
| `time_duration` | Timestamp (ms)        | `3600000` (1 giờ)                            |
| `lookup_normal` | Record ID             | `"PER00000000003"`                           |
| `reference`     | Record ID             | `"PER00000000003"`                           |
| `file`          | Metadata upload; object nếu đơn, mảng nếu nhiều | Xem `references/upload-file.md`                |

#### Cấu trúc response

**Thành công:**
```json
{
    "msg": "OK",
    "r": 0,
    "data": {
        "id": "LE000000000003"
    }
}
```

**Lỗi:**
```json
{
    "msg": "Error message",
    "r": 1,
    "data": {}
}
```

#### Xử lý kết quả

- `r`: Mã kết quả — `0` là thành công, khác `0` là lỗi.
- `data.id`: ID của bản ghi vừa tạo (dùng cho các thao tác tiếp theo như cập nhật, xoá).

---

### Khả năng C: Cập nhật bản ghi (Update Record)

Sử dụng khi cần cập nhật thông tin một bản ghi đã tồn tại.

#### Chuẩn bị dữ liệu

Cần biết:
- `object_slug` của đối tượng.
- `RECORD_ID` của bản ghi cần cập nhật — có thể lấy từ kết quả **Khả năng A** (lấy danh sách bản ghi) hoặc từ ngữ cảnh người dùng cung cấp.
- Các trường cần cập nhật và giá trị mới.

#### Gọi API

```bash
curl --location --request PUT 'https://{WORKSPACE_DOMAIN}/bapi/v1/records/{RECORD_ID}' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "object_slug": "{OBJECT_SLUG}",
    "data": {
        "{FIELD_SLUG_1}": "{VALUE_1}",
        "{FIELD_SLUG_2}": "{VALUE_2}"
    }
}'
```

**Lưu ý:**
- Thay `{API_KEY}` bằng giá trị thực từ người dùng.
- Thay `{RECORD_ID}` bằng ID của bản ghi cần cập nhật (ví dụ: `LE000000000003`).
- Thay `{OBJECT_SLUG}` bằng slug của đối tượng.
- Trong `data`, chỉ truyền các trường cần cập nhật (không cần truyền tất cả các trường).
- Quy tắc giá trị theo kiểu trường: giống **Khả năng B**.

#### Cấu trúc response

**Thành công:**
```json
{
    "msg": "OK",
    "r": 0,
    "data": {}
}
```

**Lỗi — bản ghi không tồn tại:**
```json
{
    "msg": "Record not existed",
    "r": 1,
    "data": {}
}
```

#### Xử lý kết quả

- `r`: Mã kết quả — `0` là thành công, khác `0` là lỗi.
- Nếu `msg` là `"Record not existed"`: RECORD_ID không đúng hoặc bản ghi đã bị xoá. Thông báo người dùng kiểm tra lại.

---

### Khả năng D: Xoá bản ghi (Delete Records)

Sử dụng khi cần xoá một hoặc nhiều bản ghi của một đối tượng.

> **CẢNH BÁO: Đây là hành động nguy hiểm và không thể hoàn tác.**
> - **BẮT BUỘC** phải xác nhận với người dùng trước khi thực hiện xoá.
> - Liệt kê rõ ràng ID (và tên nếu có) của các bản ghi sẽ bị xoá để người dùng kiểm tra.
> - Chỉ thực hiện gọi API xoá khi người dùng đã xác nhận đồng ý.
> - Nếu người dùng từ chối, huỷ thao tác và thông báo.

#### Chuẩn bị dữ liệu

Cần biết:
- `object_type` của đối tượng (ID dạng slug của object, ví dụ: `OT00000000011`). Có thể lấy từ skill `/object-info`.
- Danh sách `ids` — mảng ID của các bản ghi cần xoá. Có thể lấy từ kết quả **Khả năng A** hoặc từ ngữ cảnh người dùng cung cấp.

#### Gọi API

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/records/delete' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "object_type": "{OBJECT_TYPE}",
    "ids": [
        "{RECORD_ID_1}",
        "{RECORD_ID_2}"
    ]
}'
```

**Lưu ý:**
- Thay `{API_KEY}` bằng giá trị thực từ người dùng.
- Thay `{OBJECT_TYPE}` bằng ID của đối tượng (ví dụ: `OT00000000011`).
- Thay `{RECORD_ID_1}`, `{RECORD_ID_2}`,... bằng ID của các bản ghi cần xoá.
- Có thể xoá nhiều bản ghi cùng lúc bằng cách truyền nhiều ID trong mảng `ids`.

#### Cấu trúc response

**Thành công:**
```json
{
    "msg": "Success",
    "r": 0,
    "data": {
        "deleted": ["RECORD_ID_1", "RECORD_ID_2"],
        "not_deleted": []
    }
}
```

**Lỗi — bản ghi không tồn tại:**
```json
{
    "msg": "Record not existed",
    "r": 1,
    "data": {}
}
```

#### Xử lý kết quả

- `r`: Mã kết quả — `0` là thành công, khác `0` là lỗi.
- `data.deleted`: Mảng ID các bản ghi đã xoá thành công.
- `data.not_deleted`: Mảng ID các bản ghi không xoá được.
- Nếu `msg` là `"Record not existed"`: một hoặc nhiều RECORD_ID không đúng hoặc bản ghi đã bị xoá trước đó. Thông báo người dùng kiểm tra lại.

---

### Khả năng E: Upload file vào bản ghi hiện có (Upload Existing Record File)

Sử dụng khi cần upload một file cục bộ và gắn file đó vào một hoặc nhiều field `file` của bản ghi hiện có. Thực hiện bằng API, không dùng trình duyệt.

1. Đọc đầy đủ [references/upload-file.md](references/upload-file.md) trước khi gọi API.
2. Xác định `WORKSPACE_DOMAIN`, `OBJECT_SLUG` và `RECORD_ID` từ URL bản ghi hoặc ngữ cảnh người dùng. Xác minh file cục bộ tồn tại và không rỗng.
3. Dùng `$object-info` để lấy `OBJECT_TYPE_ID` và xác minh từng field đích có `fieldType=file`; giữ nguyên `FILE_FIELD_SLUG` và cờ `multiple` từ metadata.
4. Dùng `$cogover-api-auth` để tạo phiên Web App cho các endpoint `/api/v1`; không dùng API key trực tiếp cho các endpoint này.
5. Upload file riêng cho từng field đích bằng `POST /api/v1/file/upload/v2/client_upload`. Nếu cùng một file được gắn vào nhiều field, mỗi field vẫn cần một request upload với `field_slug` tương ứng và một `FILE_METADATA` riêng.
6. Chỉ tiếp tục khi upload trả HTTP `2xx`, `r: 0` và có object `data`. Gắn metadata vào record bằng `POST /api/v1/records`:
   - Field đơn (`multiple=false`): gửi trực tiếp object `FILE_METADATA`.
   - Field đa (`multiple=true`): gửi mảng metadata. Nếu người dùng yêu cầu thêm file mà không thay file cũ, đọc giá trị hiện tại và nối metadata mới trước khi cập nhật.
7. Có thể gắn nhiều field trong cùng request record sau khi mọi upload đều thành công. Không tái sử dụng metadata đã upload cho field khác.
8. Coi thao tác hoàn tất chỉ khi request gắn file trả HTTP `2xx` và `r: 0` (kiểm tra cả `body.r`). Báo tên file, Object/field slug, ID bản ghi và kết quả của từng bước.

Không retry mù quáng request upload hoặc gắn file khi timeout hay mất kết nối vì kết quả ghi có thể đã xảy ra. Báo trạng thái chưa xác định và chỉ thử lại khi người dùng yêu cầu rõ.

---

## Trả kết quả

Tuỳ theo ngữ cảnh sử dụng:

### Khi người dùng gọi trực tiếp (`/object-record`)
Hiển thị kết quả dạng bảng hoặc danh sách dễ đọc:
- **Lấy danh sách**: Hiển thị bảng bản ghi với các trường quan trọng (id, name, status, created,...). Nếu có nhiều bản ghi, hiển thị tóm tắt và hỏi người dùng muốn xem thêm không.
- **Tạo bản ghi**: Thông báo thành công kèm ID bản ghi vừa tạo.
- **Cập nhật bản ghi**: Thông báo thành công hoặc lỗi.
- **Xoá bản ghi**: Thông báo thành công hoặc lỗi. Nhấn mạnh bản ghi đã bị xoá vĩnh viễn.
- **Upload file**: Báo tên file, Object/field slug, cờ đơn/đa giá trị, ID bản ghi và kết quả upload/gắn file.

### Khi được gọi bởi sub-agent khác
Trả về dữ liệu đã trích xuất ở dạng có cấu trúc để skill gọi có thể sử dụng trực tiếp.

## Xử lý lỗi

| Lỗi                         | Cách xử lý                                                                                 |
|-----------------------------|--------------------------------------------------------------------------------------------|
| HTTP 401 / 403              | API_KEY không hợp lệ hoặc hết hạn. Yêu cầu người dùng cung cấp lại.                        |
| HTTP 500                    | Lỗi server. Thông báo người dùng thử lại sau.                                              |
| Timeout khi đọc             | Thông báo và chỉ thử lại khi phù hợp với yêu cầu của người dùng.                           |
| Timeout khi ghi/upload      | Không tự retry; báo kết quả chưa xác định để tránh tạo file hoặc cập nhật trùng.            |
| `r: 27` — Invalid filter type | Kiểm tra request `/records/list` có `type` dạng số `1`, `2` hoặc `3` ở cấp cao nhất; đối chiếu `logic_sequence`. Không thay `filters[].fieldType` để chữa lỗi thiếu `type`. |
| `r: 1` — Record not existed | RECORD_ID không đúng. Yêu cầu người dùng kiểm tra lại hoặc dùng Khả năng A để tìm bản ghi. |
| `r: 1` — Lỗi khác           | Hiển thị `msg` từ response cho người dùng biết.                                            |
| Không biết object_slug      | Gọi skill `/object-info` để lấy danh sách đối tượng, hoặc hỏi người dùng.                  |
| Không biết field slugs      | Gọi skill `/object-info` để lấy danh sách trường của đối tượng.                            |
| Thiếu phiên Web App         | Dùng `$cogover-api-auth`; dừng và báo người dùng nếu không tạo được phiên hợp lệ.           |
| `r: 626` khi gắn file       | Kiểm tra kiểu đơn/đa của field; không bọc object metadata trong mảng với field đơn.         |
| Create lỗi sau upload       | Báo các file ID đã upload có thể bị mồ côi; không tự retry create.                          |
| Thiếu field `_attachments`  | Đọc lại Object fields; không upload ảnh WYSIWYG nếu không xác định được field ID này.       |

## Ví dụ sử dụng

### Ví dụ 1: Lấy danh sách bản ghi
```
Người dùng: /object-record
Agent: Bạn muốn thao tác gì? (Lấy danh sách / Tạo / Cập nhật / Xoá)
Người dùng: Lấy danh sách Lead có trạng thái "Mới"
Agent: Bạn vui lòng cung cấp WORKSPACE_DOMAIN và API_KEY.
Người dùng: abc123xyz
Agent: [Gọi API lấy danh sách Lead với filter status = "new", hiển thị kết quả dạng bảng]
```

### Ví dụ 2: Tạo bản ghi mới
```
Người dùng: Tạo 1 Lead mới với Họ: Nguyễn, Tên: Văn A và đính kèm báo giá.xlsx
Agent: [Lấy field metadata → upload file → gọi một lần POST /bapi/v1/records với dữ liệu Lead và FILE_METADATA → đọc lại để xác minh]
```

### Ví dụ 3: Cập nhật bản ghi
```
Người dùng: Cập nhật Lead LE000000000003, đổi Họ thành "Trần"
Agent: [Gọi API cập nhật bản ghi → Thông báo thành công]
```

### Ví dụ 4: Xoá bản ghi
```
Người dùng: Xoá Lead LE000000000003
Agent: ⚠️ Bạn có chắc chắn muốn xoá bản ghi Lead sau đây không? Hành động này KHÔNG THỂ hoàn tác.
  - ID: LE000000000003
  Xác nhận xoá? (Có / Không)
Người dùng: Có
Agent: [Gọi API xoá bản ghi → Thông báo đã xoá thành công]
```

### Ví dụ 5: Được gọi bởi skill khác
```
Skill BPMN cần tạo bản ghi Contact sau khi user điền form.
→ Gọi Records Agent với API_KEY đã có, thao tác = tạo bản ghi
→ Nhận về ID bản ghi vừa tạo
→ Sử dụng trong flow tiếp theo
```

### Ví dụ 6: Upload file vào hai field
```
Người dùng: Upload báo giá.xlsx vào field “Hợp đồng” và “Tài liệu” của bản ghi theo URL này.
Agent: [Tách URL → lấy Object/field metadata → tạo phiên Web App → upload riêng cho từng field → gắn hai metadata vào bản ghi → báo kết quả]
```
