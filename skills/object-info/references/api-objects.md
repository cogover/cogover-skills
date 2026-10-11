# Objects API — thao tác thay đổi Object

API dùng để tạo, cập nhật, xoá hoặc khôi phục Object Type trong Cogover.

## Mục lục

- [Xác thực và endpoint](#xác-thực-và-endpoint)
- [1. Tạo Object](#1-tạo-object)
- [2. Cập nhật Object](#2-cập-nhật-object)
- [3. Xoá hoặc khôi phục Object](#3-xoá-hoặc-khôi-phục-object)
- [Response lỗi thường gặp](#response-lỗi-thường-gặp)
- [Lưu ý sử dụng](#lưu-ý-sử-dụng)

## Xác thực và endpoint

Tất cả request yêu cầu:

```http
Authorization: Bearer {tokenId}-{secretToken}
Content-Type: application/json
```

Workspace được xác định từ access token. Nếu client gửi `workspace_id`, API thay bằng workspace ID đã xác thực.

| Chức năng | Method | Endpoint |
|---|---|---|
| Tạo Object | `POST` | `/bapi/v1/objects` |
| Tạo Object (alias) | `POST` | `/bapi/v1/objects/create` |
| Cập nhật Object | `PUT` | `/bapi/v1/objects/{objectId}` |
| Xoá hoặc khôi phục Object | `POST` | `/bapi/v1/objects/delete` |

| Trường hợp | HTTP status |
|---|---|
| Tạo thành công (`r = 0`) | `201` |
| Cập nhật, xoá hoặc khôi phục thành công | `200` |
| API trả lỗi nghiệp vụ (`r != 0`) | `400` |
| Token không hợp lệ hoặc hết hạn | `401` |
| Vượt rate limit | `429` |
| Lỗi máy chủ | `500` |

Chỉ coi thao tác thành công ở cấp nghiệp vụ khi `r = 0`.

## 1. Tạo Object

**Endpoint:** `POST /bapi/v1/objects`

Alias tương đương: `POST /bapi/v1/objects/create`.

### Request Body

| Trường | Kiểu | Bắt buộc | Mặc định | Mô tả |
|---|---|---|---|---|
| `name` | String | Có | — | Tên hiển thị gốc. Phải hợp lệ và không trùng trong workspace |
| `plural_name` | String | Không | `name` | Tên số nhiều gốc. Phải không trùng trong workspace |
| `slug` | String | Không | Sinh từ `name` | Định danh ổn định. Nếu truyền vào thì phải hợp lệ và không trùng |
| `description` | String | Không | `null` | Mô tả Object |
| `status` | Integer | Không | `1` | `0` = inactive, `1` = active |
| `type` | Integer | Không | `0` | `0` = normal, `1` = child, `2` = junction |
| `name_field` | Object | Có khi tạo qua public API | — | Định nghĩa trường tên chính của Object |
| `translations` | Array | Không | `[]` | Bản dịch Object; hỗ trợ `name` và `plural_name` |
| `meta_data` | String | Không | `null` | Chuỗi chứa JSON metadata hợp lệ |
| `standard_fields` | Boolean | Không | `true` | Cờ tương thích khi validate; public API vẫn khởi tạo các field chuẩn |
| `standard_layout` | Boolean | Không | `true` | Tạo layout chuẩn |
| `standard_buttons` | Boolean | Không | `true` | Tạo các button chuẩn |
| `standard_filter` | Boolean | Không | `true` | Tạo filter chuẩn |
| `creatable` | Integer | Không | `1` | Cho phép tạo record (`0` hoặc `1`) |
| `editable` | Integer | Không | `1` | Cho phép sửa record (`0` hoặc `1`) |
| `viewable` | Integer | Không | `1` | Cho phép xem record (`0` hoặc `1`) |
| `quick_search` | Integer | Không | `1` | Cho phép tham gia quick search (`0` hoặc `1`) |
| `parent_field` | Object | Không | `null` | Định nghĩa field cha cho child Object; khi truyền sẽ chuyển `type` thành `1` |
| `composite_keys` | Array | Không | `null` | Các định nghĩa composite unique key |

Public client chỉ tạo custom Object; `is_standard=1` sẽ bị từ chối. Public API luôn khởi tạo các field chuẩn, vì vậy client nên truyền `name_field` và giữ `standard_fields` ở giá trị mặc định.

### Bất biến record-name

- Mỗi Object có đúng một field record-name chuẩn với slug kỹ thuật **`name`**.
- `name_field.name` là nhãn hiển thị của field (ví dụ `Project name`, `Membership code`, `Order number`), không phải slug. Không gửi `name_field.slug`; nếu một client/compiler có thuộc tính này thì giá trị duy nhất hợp lệ là `name`.
- `name_field.type` chỉ hỗ trợ `short_text` hoặc `auto_number`. Giá trị `meta_data` của field này là JSON string và tuân theo [Object Fields API](api-object-fields.md).
- Object con/phụ thuộc, junction, dòng chi tiết hoặc bản ghi kỹ thuật mặc định dùng `auto_number`. Object nhận diện bằng tên/tiêu đề người dùng nhập dùng `short_text`; chứng từ/giao dịch nhận diện bằng mã hệ thống cấp dùng `auto_number`.
- Không tạo custom field record-name có slug như `membership_code`, `title`, `subject` hoặc `order_number`. Các giá trị đó chỉ có thể là nhãn hiển thị hoặc slug của một field nghiệp vụ khác.
- Sau create/update, đọc lại Object và xác minh có đúng một field active slug `name`, đúng nhãn/bản dịch/type/metadata và type thuộc `short_text`/`auto_number`. `data.standard_fields[].slug = "name"` trong response create là bằng chứng sơ bộ, không thay thế read-back đầy đủ.

### Bản dịch

Mỗi phần tử `translations` chứa mã `language` và một hoặc cả hai thuộc tính có thể dịch:

```json
{
  "translations": [
    {
      "language": "en-US",
      "name": "Customer",
      "plural_name": "Customers"
    }
  ]
}
```

### Ví dụ cURL

```bash
curl --location 'https://{workspace-domain}/bapi/v1/objects' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "name": "Customer",
    "plural_name": "Customers",
    "slug": "customer",
    "description": "Manage customer information",
    "translations": [
      {
        "language": "en-US",
        "name": "Customer",
        "plural_name": "Customers"
      },
      {
        "language": "vi-VN",
        "name": "Khách hàng",
        "plural_name": "Danh sách khách hàng"
      }
    ],
    "name_field": {
      "name": "Customer ID",
      "type": "auto_number",
      "required": 1,
      "meta_data": "{\"prefix\":\"CUS-\",\"format\":\"00000\",\"start\":\"1\",\"step\":\"1\",\"is_identifier\":true}"
    }
  }'
```

### Response thành công (201)

```json
{
  "r": 0,
  "msg": "OK",
  "requestId": "RQ00000001-ef58-4ec1-9bb5-e279afedb1ce",
  "data": {
    "id": "OT00000000020",
    "slug": "customer",
    "options": [],
    "standard_fields": [
      {
        "id": "OF00000000027",
        "slug": "name",
        "options": []
      }
    ]
  }
}
```

Ví dụ cố ý không gửi `name_field.slug`: `Customer ID` là nhãn hiển thị, còn field chuẩn được tạo có slug `name` như response bên dưới.

`data.standard_fields` chứa toàn bộ các field chuẩn được tạo cùng Object.

## 2. Cập nhật Object

**Endpoint:** `PUT /bapi/v1/objects/{objectId}`

Đây là API partial update. Các thuộc tính không xuất hiện trong payload được giữ nguyên.

### Quy tắc quan trọng

- `objectId` trên URL là nguồn tin cậy. Nếu body chứa `id` khác, API thay bằng giá trị trên URL.
- `workspace_id` luôn được thay bằng workspace ID đã xác thực.
- Không thể cập nhật Object đang ở trạng thái chờ xoá (`status=2`).
- `name` và `plural_name` gốc phải tiếp tục không trùng trong workspace.
- Với standard Object, chỉ cho phép sửa `name`, `plural_name`, `description`, `translations` và các metadata key được hỗ trợ.
- API không hỗ trợ đổi `slug` sau khi tạo.
- Khi cập nhật `name_field`, slug chuẩn vẫn là `name`; chỉ cập nhật các thuộc tính được hỗ trợ và không tạo field `name` thứ hai.

### Các thuộc tính có thể cập nhật

| Trường | Kiểu | Mô tả |
|---|---|---|
| `name` | String | Tên hiển thị gốc mới |
| `plural_name` | String | Tên số nhiều gốc mới |
| `description` | String | Mô tả mới; gửi chuỗi rỗng để xoá mô tả |
| `status` | Integer | `0` = inactive, `1` = active |
| `meta_data` | String | Chuỗi chứa JSON metadata hợp lệ |
| `quick_search` | Integer | Bật hoặc tắt quick search (`0` hoặc `1`) |
| `translations` | Array | Upsert `name` và/hoặc `plural_name` theo ngôn ngữ |
| `name_field` | Object | Partial update trường tên chính |
| `parent_field` | Object | Cập nhật field cha của child Object, tuỳ ràng buộc quan hệ/dữ liệu |
| `composite_keys` | Array | Toàn bộ tập composite key mong muốn |

Với mỗi ngôn ngữ có trong `translations`, API chỉ cập nhật các thuộc tính xuất hiện trong phần tử đó. Thuộc tính và ngôn ngữ không gửi được giữ nguyên. Giá trị bản dịch rỗng fallback về giá trị gốc tương ứng.

Với custom Object, nếu gửi `meta_data`, API thay toàn bộ chuỗi đã lưu; client cần merge các key hiện có trước khi cập nhật. Với standard Object, API chỉ chấp nhận và merge các key: `enable_auto_fill`, `enable_smart_paste`, `hide_create_button`, `allow_report`, `is_config_field_name_with_view`, `config_field_name_with_view`, `config_text`, `config_text_formula` và `is_show_avatar_before`.

### Ví dụ cURL

```bash
curl --location --request PUT \
  'https://{workspace-domain}/bapi/v1/objects/OT00000000020' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "description": "Updated description",
    "translations": [
      {
        "language": "vi-VN",
        "name": "Khách hàng"
      }
    ]
  }'
```

Ví dụ chỉ cập nhật mô tả gốc và tên tiếng Việt. `plural_name` tiếng Việt đã có được giữ nguyên.

### Response thành công (200)

```json
{
  "r": 0,
  "msg": "OK",
  "requestId": "RQ00000001-ef58-4ec1-9bb5-e279afedb1ce"
}
```

## 3. Xoá hoặc khôi phục Object

**Endpoint:** `POST /bapi/v1/objects/delete`

Endpoint nhận request dạng danh sách. Để thao tác một Object, gửi đúng một phần tử trong `data`.

### Request Body

```json
{
  "data": [
    {
      "id": "OT00000000020",
      "delete_type": 1
    }
  ]
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `data` | Array | Có | Danh sách Object cần thao tác |
| `data[].id` | String | Có | Object ID |
| `data[].delete_type` | Integer | Có | Loại thao tác xoá hoặc khôi phục |

### Giá trị `delete_type`

| Giá trị | Ý nghĩa | Khuyến nghị cho public client |
|---|---|---|
| `1` | Soft delete: chuyển Object sang pending delete và đặt lịch xoá thực tế sau 14 ngày | Nên dùng cho thao tác xoá thông thường |
| `2` | Undo soft delete: khôi phục trạng thái trước đó và huỷ lịch xoá | Dùng để khôi phục Object |
| `3` | Actual delete: xoá cấu hình liên quan và dữ liệu Object | Có tính phá huỷ; chỉ dùng sau khi xác nhận rõ ràng |

Không thể xoá standard Object. Yêu cầu xoá có thể bị từ chối nếu Object đang được Object Picker tham chiếu hoặc các field, relationship, filter, workflow hay thực thể liên kết khác đang ngăn cản thao tác.

### Ví dụ cURL soft delete

```bash
curl --location 'https://{workspace-domain}/bapi/v1/objects/delete' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "data": [
      {
        "id": "OT00000000020",
        "delete_type": 1
      }
    ]
  }'
```

### Ví dụ cURL khôi phục

```bash
curl --location 'https://{workspace-domain}/bapi/v1/objects/delete' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "data": [
      {
        "id": "OT00000000020",
        "delete_type": 2
      }
    ]
  }'
```

### Response thành công (200)

```json
{
  "r": 0,
  "msg": "Success",
  "requestId": "RQ00000001-ef58-4ec1-9bb5-e279afedb1ce"
}
```

## Response lỗi thường gặp

| `r` | Mô tả |
|---|---|
| `405` | Thiếu hoặc sai Object ID |
| `407` | Thiếu hoặc sai tên Object |
| `413` | `status` hoặc cờ standard không hợp lệ |
| `418` | `delete_type` không hợp lệ |
| `430` | Tên số nhiều không hợp lệ |
| `435` | Slug không hợp lệ |
| `436` | Thiếu hoặc sai trường tên chính |
| `438` | Thao tác không được phép với standard Object |
| `445` | Object type không hợp lệ |
| `501` | Không tìm thấy Object |
| `503` | Slug Object đã tồn tại |
| `506` | Tên Object đã tồn tại |
| `512` | Object đang chờ xoá nên không thể cập nhật |
| `517` | Object đang được Object Picker chọn nên không thể xoá |
| `518` | Tên số nhiều của Object đã tồn tại |
| `534` | Workspace đã đạt giới hạn Object của gói thuê bao |

Ví dụ response lỗi:

```json
{
  "r": 503,
  "msg": "Object slug customer already existed",
  "requestId": "RQ00000001-ef58-4ec1-9bb5-e279afedb1ce"
}
```

## Lưu ý sử dụng

- Coi Object ID và field ID là chuỗi opaque, không phân tích cấu trúc ID.
- Dùng `slug` ổn định, chữ thường; API không hỗ trợ đổi slug sau khi tạo.
- Ưu tiên soft delete (`delete_type=1`) để có thể khôi phục trong thời gian lưu giữ.
- Actual delete (`delete_type=3`) có tính phá huỷ và có thể xoá record cùng cấu hình liên quan.
- Không chỉ dựa vào HTTP status; kiểm tra thêm `r = 0`.
