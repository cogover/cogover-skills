# Object Fields API

API dùng để tạo, cập nhật và xoá field (trường dữ liệu) của một Object.

## Xác thực

Tất cả request yêu cầu header:

```http
Authorization: Bearer {tokenId}-{secretToken}
Content-Type: application/json
```

Workspace được xác định từ access token; request không cần thêm thông tin nhận diện workspace trong header hoặc body.

---

## Tổng quan endpoint

| Chức năng | Method | Endpoint |
|---|---|---|
| Tạo field | `POST` | `/bapi/v1/object-fields` |
| Tạo field (alias) | `POST` | `/bapi/v1/object-fields/create` |
| Cập nhật field | `PUT` | `/bapi/v1/object-fields/{fieldId}` |
| Xoá/khôi phục field | `POST` | `/bapi/v1/object-fields/delete` |

Quy ước HTTP status:

| Trường hợp | HTTP status |
|---|---|
| Tạo thành công (`r = 0`) | `201` |
| Cập nhật hoặc xoá thành công (`r = 0`) | `200` |
| API trả lỗi nghiệp vụ (`r != 0`) | `400` |
| Token không hợp lệ/hết hạn | `401` |
| Vượt rate limit | `429` |
| Lỗi máy chủ | `500` |

> `r = 0` mới là điều kiện thành công ở cấp nghiệp vụ. Khi xử lý lỗi, nên ghi log cả HTTP status, `r`, `msg` và `requestId`.

---

## Quy ước dữ liệu

### Cờ số và Boolean

- Các trường `required`, `multiple`, `unique`, `status`, `creatable`, `editable`, `viewable`, `read_only`, `is_standard`, `is_display` và `quickSearch` dùng số, không dùng Boolean.
- Cờ bật/tắt thường nhận `1` hoặc `0`.
- `manual_modify_allow` là Boolean nghiêm ngặt, phải gửi `true` hoặc `false`.
- `status`: `0` = inactive, `1` = active, `2` = pending delete. Khi tạo, mặc định là `1`.

### `meta_data` là JSON string

`meta_data` không phải JSON object trực tiếp mà là một chuỗi chứa JSON hợp lệ:

```json
{
  "meta_data": "{\"character_limit\":{\"min\":0,\"max\":255}}"
}
```

Không gửi như sau:

```json
{
  "meta_data": {
    "character_limit": {
      "min": 0,
      "max": 255
    }
  }
}
```

Khi cập nhật, nếu gửi `meta_data`, API thay toàn bộ chuỗi metadata đã lưu. Client phải merge metadata cũ với phần thay đổi trước khi gọi API nếu muốn giữ các key cũ.

### `default_value`

Kiểu biểu diễn phụ thuộc loại field:

- Text/lookup đơn: chuỗi.
- Boolean: chuỗi `"true"` hoặc `"false"`.
- Number/currency/percent/rating: số hoặc chuỗi số hợp lệ.
- Nhiều giá trị/range/file: chuỗi JSON, ví dụ `"[\"A\",\"B\"]"` hoặc `"{\"gte\":1711929600000,\"lte\":1714521600000}"`.
- Không có giá trị mặc định: `null` hoặc chuỗi rỗng tuỳ loại field.

---

## 1. Tạo field

**Endpoint:** `POST /bapi/v1/object-fields`

Alias tương đương: `POST /bapi/v1/object-fields/create`.

### Tham số chung

| Trường | Kiểu | Bắt buộc | Mặc định | Mô tả |
|---|---|---|---|---|
| `type` | String | Có | — | Loại field. Xem danh sách type bên dưới |
| `object_type_id` | String | Có | — | ID Object chứa field |
| `name` | String | Có | — | Tên hiển thị. Phải hợp lệ và không trùng tên field khác trong Object |
| `slug` | String | Không | Sinh từ `name` | Khoá kỹ thuật. Phải hợp lệ và duy nhất trong Object |
| `description` | String | Không | — | Mô tả, tối đa 1.000 ký tự |
| `tool_tip` | String | Không | — | Tooltip, tối đa 255 ký tự |
| `hint_text` | String | Không | — | Placeholder/hint, tối đa 255 ký tự |
| `status` | Integer | Không | `1` | `0` inactive, `1` active, `2` pending delete |
| `required` | Integer | Không | `0` | `1` bắt buộc, `0` không bắt buộc |
| `multiple` | Integer | Không | `0` | `1` cho phép nhiều giá trị, `0` một giá trị |
| `unique` | Integer | Không | `0` | Bật ràng buộc unique |
| `default_value` | String/Number/null | Không | `""` | Giá trị mặc định; định dạng phụ thuộc `type` |
| `manual_modify_allow` | Boolean | Không | `false` | Cho phép người dùng sửa giá trị thủ công |
| `creatable` | Integer | Không | `1` | Có cho phép nhập field khi tạo record hay không |
| `editable` | Integer | Không | `1` khi lưu | Có cho phép sửa field hay không |
| `viewable` | Integer | Không | `1` khi lưu | Có cho phép xem field hay không |
| `read_only` | Integer | Không | `0` | Cờ chỉ đọc |
| `is_standard` | Integer | Không | `0` | Field chuẩn (`1`) hay custom (`0`) |
| `is_display` | Integer | Không | `1` | Field có hiển thị hay không |
| `quickSearch` | Integer | Không | `0` khi lưu | Tham gia quick search. Tên key phân biệt hoa/thường |
| `sort` | Integer | Không | Tự tính | Thứ tự field; nếu gửi phải lớn hơn `0` |
| `option_sorting_policy` | Integer | Không | `0` | Chính sách sắp xếp option; nhận `0`, `1` hoặc `2` |
| `options` | Array | Khi cần lưu options | — | Danh sách option đầy đủ cho `single_choice`, `radio_button`, `multi_choices`, `checkbox` hoặc `cascading` |
| `meta_data` | String (JSON) | Tuỳ type | — | Cấu hình riêng của field, encode thành JSON string |
| `translations` | Array | Không | `[]` | Bản dịch tên, mô tả, tooltip và placeholder |
| `rating_icons` | Array | Chỉ rating custom | — | Danh sách icon của field `rating` |
| `related_list_name` | String | Với lookup | — | Tên related list; bắt buộc với `lookup_normal`, `reference` |
| `related_list_slug` | String | Không | — | Slug related list |
| `lookup_filter` | Object | Không | — | Bộ lọc lookup cần tạo/cập nhật cùng field |
| `rollup_summary_filter` | Object | Không | — | Bộ lọc áp dụng cho rollup summary |

### Field record-name chuẩn `name`

- Mỗi Object đã có đúng một field record-name chuẩn với slug `name`, được tạo qua `name_field` của Objects API. Không dùng `POST /bapi/v1/object-fields` để tạo field record-name thay thế hoặc field `name` thứ hai.
- Nhãn hiển thị có thể là `Name`, `Title`, `Subject`, `Membership code`, `Order number`... nhưng slug của record-name vẫn luôn là `name`.
- Field `name` chỉ có type `short_text` hoặc `auto_number`. Object con/phụ thuộc, junction, dòng chi tiết hoặc bản ghi kỹ thuật mặc định dùng `auto_number`; Object nhận diện bằng tên/tiêu đề người dùng nhập dùng `short_text`; chứng từ/giao dịch nhận diện bằng mã hệ thống cấp dùng `auto_number`.
- Không đổi slug của field record-name. Nếu cần cập nhật nhãn, type hoặc metadata của record-name, dùng `name_field` trong Objects API theo contract được hỗ trợ, rồi đọc lại Object để xác minh vẫn có đúng một field active slug `name`.
- Trước khi tạo custom field, nếu slug dự kiến là `name`, dừng và đọc lại schema: đây là slug dành riêng cho record-name chuẩn.

### Các loại field được hỗ trợ

| Nhóm | Giá trị `type` |
|---|---|
| Text | `short_text`, `long_text`, `email`, `phone`, `url`, `regex`, `label` |
| Boolean | `boolean` |
| Số | `numeric`, `decimal`, `currency`, `percent`, `rating`, `auto_number` |
| Lựa chọn | `single_choice`, `radio_button`, `multi_choices`, `checkbox`, `cascading` |
| Ngày giờ | `date`, `date_range`, `time`, `time_range`, `date_time`, `date_time_range`, `time_duration` |
| File | `file` |
| Liên kết Object | `lookup_normal`, `reference` |
| Tính toán | `formula`, `rollup_summary` |

Nếu `type` không được hỗ trợ, response có `r = 504`.

### Cấu hình theo từng loại field

#### `short_text`

```json
{
  "character_limit": { "min": 0, "max": 255 },
  "multiple_limit": { "min": 1, "max": 30 },
  "display_type": 1,
  "unique_rule": 1
}
```

| Key metadata | Kiểu | Mô tả |
|---|---|---|
| `character_limit.min/max` | Integer | Số ký tự tối thiểu/tối đa; giá trị thông dụng là `0/255` |
| `multiple_limit.min/max` | Integer | Số phần tử tối thiểu/tối đa khi `multiple = 1`; mặc định `1/30` |
| `display_type` | Integer | Kiểu hiển thị short text |
| `unique_rule` | Integer | Chỉ gửi khi `unique = 1`: `1` kiểm tra từng giá trị, `2` kiểm tra tổ hợp |

#### `long_text`

```json
{
  "character_limit": { "min": 0, "max": 131072 },
  "text_type": 1,
  "text_types": [1],
  "default_values": { "1": "Nội dung mặc định" }
}
```

| Key metadata | Kiểu | Mô tả |
|---|---|---|
| `character_limit.min/max` | Integer/null | Giới hạn ký tự; giá trị max thông dụng là `131072` |
| `text_type` | Integer | Kiểu chính; rich text là `2`, Markdown là `3` |
| `text_types` | Array[Integer] | Các kiểu nội dung được cho phép |
| `default_values` | Object | Giá trị mặc định theo từng `text_type` |

Nếu `text_type = 2`, API loại bỏ HTML tag khỏi `default_value` trước khi lưu.

#### `email`, `label`

```json
{
  "character_limit": { "min": 0, "max": 255 },
  "multiple_limit": { "min": 1, "max": 30 },
  "unique_rule": 1
}
```

`unique_rule` chỉ cần khi `unique = 1`. Với field unique thuộc nhóm `short_text`, `email`, `single_choice`, `multi_choices`, API không cho phép đồng thời có `default_value`.

#### `phone`

```json
{
  "country_code": ["VN", "US"],
  "multiple_limit": { "min": 1, "max": 30 },
  "regex": "",
  "is_show_button_call": 0,
  "is_validate_format": true,
  "duplicate_check_type": 1,
  "unique_rule": 1
}
```

| Key metadata | Kiểu | Mô tả |
|---|---|---|
| `country_code` | Array[String] | Mã quốc gia được chấp nhận; `"*"` có thể dùng cho tất cả |
| `is_show_button_call` | Integer | Chế độ hiển thị nút gọi |
| `is_validate_format` | Boolean | Có kiểm tra định dạng số điện thoại hay không |
| `duplicate_check_type` | Integer | Cách chuẩn hoá/kiểm tra trùng số điện thoại |
| `regex` | String | Regex bổ sung nếu có |

#### `url`

```json
{
  "character_limit": { "min": 0, "max": 2048 },
  "multiple_limit": { "min": 1, "max": 30 },
  "use_display_text": false,
  "unique_rule": 1
}
```

`use_display_text = true` cho phép lưu nhãn hiển thị riêng với URL.

#### `regex`

```json
{
  "character_limit": { "min": 0, "max": 255 },
  "multiple_limit": { "min": 1, "max": 30 },
  "regex": "^[A-Z0-9]+$",
  "remove_special_characters": false,
  "unique_rule": 1
}
```

Nếu `remove_special_characters = true`, `default_value` phải được loại bỏ các ký tự không phải chữ/số trước khi gửi.

#### `boolean`

```json
{
  "true_value": "Có",
  "false_value": "Không"
}
```

`default_value` gửi dưới dạng chuỗi `"true"` hoặc `"false"`.

#### `numeric` và `decimal`

```json
{
  "value_limit": { "min": -9999999999, "max": 9999999999 },
  "multiple_limit": { "min": 1, "max": 30 },
  "format": { "type": 1, "format": 6 },
  "precision": 2,
  "integral_length": 10,
  "fractional_length": 2,
  "display_type": 2,
  "round_rule": 1,
  "display_as_currency": false,
  "unique_rule": 1
}
```

| Key metadata | Kiểu | Mô tả |
|---|---|---|
| `value_limit.min/max` | Number/null | Giá trị nhỏ nhất/lớn nhất |
| `format.type` | Integer | Kiểu format; giá trị hiện được hỗ trợ là `1` |
| `format.format` | Integer | Mã định dạng số do UI/workspace quy định; không suy ra ý nghĩa chỉ từ mã |
| `precision` | Integer | Độ chính xác |
| `integral_length` | Integer | Số chữ số phần nguyên, tối đa `16` |
| `fractional_length` | Integer | Số chữ số thập phân, tối đa `16` |
| `display_type` | Integer | `1` integer, `2` decimal |
| `round_rule` | Integer | Quy tắc làm tròn; chỉ dùng cho decimal |
| `display_as_currency` | Boolean | Hiển thị numeric như tiền tệ |

Chọn `type = "numeric"` cho integer và `type = "decimal"` cho số thập phân. API chỉ cho đổi type trong cặp `numeric`/`decimal` theo quy tắc chuyển đổi field.

> **Không hardcode format mặc định Workspace:** object `format` trong ví dụ chỉ minh hoạ schema, không khẳng định `format: 6` là “Theo cấu hình chung của Workspace”. Khi cần cấu hình này, đọc một field `numeric`/`decimal` đã được xác nhận đúng trong cùng Workspace và sao chép nguyên `metaData.format`, sau đó đọc lại field để xác minh. Trong một mẫu đã ẩn danh, `{"format":7,"type":1}` là cấu hình chung Workspace, còn `format: 6` hiển thị `#,##,##0.00` theo kiểu Ấn Độ; không áp dụng kết luận này cho Workspace khác nếu chưa kiểm tra.

#### `currency`

Dùng các key số giống `numeric`/`decimal`, thêm:

```json
{
  "country_code": "VND",
  "unit_position": "after"
}
```

`unit_position` nhận `before` hoặc `after`. Khoảng giá trị thông dụng là từ `0` đến `999999999999999`.

#### `percent`

Metadata giống numeric. Giá trị phần trăm mặc định được lưu theo tỷ lệ: `25%` gửi `default_value = 0.25`.

#### `auto_number`

```json
{
  "prefix": "CUS-",
  "suffix": "",
  "format": "0000",
  "start": 1,
  "step": 1,
  "is_identifier": false,
  "is_auto_fill_missed_data": false
}
```

| Key metadata | Kiểu | Mô tả |
|---|---|---|
| `prefix`/`suffix` | String | Tiền tố/hậu tố |
| `format` | String | Mẫu phần số, ví dụ `0000` |
| `start` | Integer | Giá trị bắt đầu |
| `step` | Integer | Bước tăng |
| `is_identifier` | Boolean | Dùng field làm identifier; mỗi Object chỉ có một auto-number identifier |
| `is_auto_fill_missed_data` | Boolean | Tự điền dữ liệu cho record đã tồn tại |

API luôn đặt `manual_modify_allow = false` cho `auto_number`.

#### `rating`

```json
{
  "display_type": 1,
  "rating_type": 1,
  "display_number": 5
}
```

Ngoài `meta_data`, gửi `rating_icons`:

```json
{
  "rating_icons": [
    {
      "value": "star",
      "icon": "star"
    }
  ]
}
```

- `rating_type = 1`: yêu cầu đúng một phần tử cấu hình icon.
- `rating_type = 2`: số phần tử `rating_icons` phải bằng `display_number`.
- `default_value`, nếu có, là một số nằm trong thang rating.

#### `single_choice`, `radio_button`

```json
{
  "sort_rule": 0,
  "prioritized_sort_rule": 0,
  "option_display_type": 2
}
```

`single_choice` hiển thị dạng select; `radio_button` hiển thị dạng radio. Danh sách lựa chọn được gửi ở top-level `options`.

#### `multi_choices`, `checkbox`

```json
{
  "sort_rule": 0,
  "prioritized_sort_rule": 0,
  "object_picker": false,
  "multiple_limit": { "min": 1, "max": 30 },
  "unique_rule": 1
}
```

Hai type này luôn gửi `multiple = 1`. `multi_choices` hiển thị dạng multiple select; `checkbox` hiển thị dạng danh sách checkbox.

#### Cấu trúc `options`

```json
{
  "options": [
    {
      "id": "00000000-0000-4000-8000-000000000130",
      "value": "Đang xử lý",
      "slug": "working",
      "sort": 1,
      "status": 1,
      "is_default": 0,
      "icon": null,
      "background_color": "#E8F1FF",
      "text_color": "#1F5EFF",
      "translations": [
        { "language": "en-US", "value": "Working" }
      ]
    }
  ]
}
```

| Trường option | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `id` | String | Có | ID option; khi tạo nên dùng UUID |
| `value` | String | Có | Giá trị hiển thị, không rỗng, tối đa 255 ký tự |
| `slug` | String | Không | Slug option, phải đúng định dạng và duy nhất |
| `sort` | Integer | Không | Thứ tự; nếu gửi phải lớn hơn `0` |
| `status` | Integer | Không | `0`, `1` hoặc `2`; mặc định `1` |
| `is_default` | Integer | Không | `0` hoặc `1`; mặc định `0` |
| `icon` | String/null | Không | Icon option |
| `type` | String | Không | Loại option bổ sung |
| `category` | String/null | Không | Category của option |
| `category_level` | Integer/null | Không | Cấp category |
| `parent_id` | String/null | Với cascading con | ID option cha |
| `background_color` | String | Không | Màu nền |
| `text_color` | String | Không | Màu chữ |
| `translations` | Array | Không | Bản dịch `value` |

Tối đa `200` options. API kiểm tra trùng ID và trùng value theo từng loại field.

#### `cascading`

```json
{
  "multiple_limit": { "min": 1, "max": 20 },
  "format": 1,
  "display_value_format": 1,
  "unique_rule": 1
}
```

`options` là danh sách cây đã flatten; option con tham chiếu option cha qua `parent_id`. `multiple` được xác định từ mode `format`. `display_value_format` điều khiển cách ghép giá trị cha/con khi hiển thị.

Các endpoint field thông thường hỗ trợ lưu options mà không cần URI riêng:

- `POST /bapi/v1/object-fields` tạo đồng thời field và options khi request có key `options` ở top-level.
- `PUT /bapi/v1/object-fields/{fieldId}` cập nhật đồng thời field và options khi request có key `options` ở top-level.
- Không gửi `options` thì mutation không xử lý danh sách option. Khi cập nhật, gửi `"options": []` sẽ xoá toàn bộ options hiện có.
- Khi cập nhật, `options` là trạng thái đầy đủ mong muốn. Option hiện có nhưng không xuất hiện trong mảng sẽ bị xoá; ID hiện có được cập nhật; ID chưa tồn tại được tạo thành option mới.
- Request có `options` bắt buộc phải có `type`, và type phải là một trong các giá trị `single_choice`, `radio_button`, `multi_choices`, `checkbox` hoặc `cascading`.

#### Ngày, giờ và duration

| `type` | Giá trị |
|---|---|
| `date` | Một ngày |
| `date_range` | Khoảng ngày |
| `time` | Một thời điểm trong ngày |
| `time_range` | Khoảng thời gian trong ngày |
| `date_time` | Ngày giờ |
| `date_time_range` | Khoảng ngày giờ |
| `time_duration` | Khoảng thời lượng |

Các key metadata chính:

| Key | Kiểu | Mô tả |
|---|---|---|
| `default_value_current` | Boolean/null | Dùng thời điểm hiện tại làm mặc định |
| `format.format` | String | Format cho `date`/`time`, ví dụ `dd/MM/yyyy`, `HH:mm` hoặc `workspace` |
| `format.date`/`format.time` | String | Format riêng ngày và giờ của `date_time` |
| `time_zone` | String | IANA timezone, ví dụ `Asia/Ho_Chi_Minh` |
| `value_limit.from/to` | Object/null | Giới hạn cho field đơn |
| `start`/`end` | Object | Giới hạn đầu/cuối cho field range |
| `multiple_limit.min/max` | Integer | Số phần tử nếu field đơn bật `multiple` |
| `rules` | Object | Quy tắc quy đổi unit cho `time_duration` |

Cấu trúc một giới hạn:

```json
{
  "type": "relative-current",
  "unit": "day",
  "value": -30
}
```

- `type`: `absolute`, `relative-current`, `relative-from` hoặc `relative-to`.
- `unit`: `year`, `month`, `week`, `day`, `hour`, `minute`, `second`.
- `value`: giá trị tuyệt đối hoặc độ lệch; số âm là trước, số dương là sau.
- Timestamp dùng mili giây.
- Giá trị range trong `default_value` là chuỗi JSON có `gte` và `lte`.

#### `file`

```json
{
  "multiple_limit": { "min": 1, "max": 30 },
  "max_size": 52428800,
  "file_type": ["image/png", "image/jpeg"],
  "file_group_type": "image",
  "is_public": false,
  "is_resizable": true
}
```

`max_size` tính bằng byte. `default_value`, nếu có, phải là chuỗi JSON array không rỗng; mỗi phần tử phải là object có `file_id`.

#### Lookup: `lookup_normal`, `reference`

```json
{
  "object": "OT_TARGET_ID",
  "object_slug": "customer",
  "link_field": "id",
  "multiple_limit": { "min": 1, "max": 30 },
  "unique_rule": 1,
  "lookup_filter": "FILTER_ID",
  "lookup_filter_type": 1,
  "lookup_filter_error_msg": "Record không hợp lệ",
  "lookup_filter_status": true,
  "related_list_filter": "FILTER_ID",
  "related_list_filter_related_list_id": "RL_ID",
  "related_list_filter_status": true
}
```

| Type | Mô tả chính |
|---|---|
| `lookup_normal` | Lookup thường, không tìm kiếm kết hợp |
| `reference` | Lookup phụ thuộc; metadata có thêm `allow_searching` |

Với `lookup_normal` và `reference`, `related_list_name` là bắt buộc. Có thể gửi `lookup_filter` top-level để API tạo/cập nhật filter và ghi ID vào metadata.

`lookup_filter` và `rollup_summary_filter` dùng cấu trúc filter rút gọn:

```json
{
  "logicType": "AND",
  "logic": "",
  "conditions": [
    {
      "field": "status",
      "op": "in",
      "params": ["active"],
      "fieldType": "single_choice"
    }
  ],
  "sortFields": [
    {
      "field": "created",
      "order": "desc"
    }
  ]
}
```

API cũng nhận alias snake_case `logic_type` và `sort_fields`. Ý nghĩa condition/operator được mô tả chi tiết trong [Filters API](../../object-filter/references/api-filters.md).

Giá trị mặc định lookup đơn là record ID. Lookup multiple dùng chuỗi JSON array các record ID. Có thể dùng placeholder `$currentUser` và `$currentUser.primaryDepartment` cho lookup phù hợp.

#### `formula`

Nội dung `script` sử dụng ngôn ngữ Cogover Scripting. Trước khi viết hoặc sửa công thức, dùng [Cogover Scripting API Reference](cogover-scripting-api-vi.md) để tra đúng kiểu dữ liệu, toán tử, cú pháp, hàm, giới hạn sandbox và các công thức mẫu theo chỉ dẫn trong `SKILL.md`. Trước khi gọi API tạo/cập nhật field, bắt buộc thực hiện [kiểm tra cú pháp và chạy thử Formula](formula-validation.md).

```json
{
  "return_type": 2,
  "script": "price * quantity",
  "display_html": false,
  "zero_default_value": true,
  "range_date": false,
  "time_zone": "Asia/Ho_Chi_Minh",
  "calculation_mode": 0,
  "format": "# ##0.0",
  "fractional_length": 2,
  "number_type": 1,
  "currency_code": "VND",
  "unit_position": "after",
  "meta": {}
}
```

| Key | Kiểu | Mô tả |
|---|---|---|
| `return_type` | Integer | `1` text, `2` number, `4` date-time, `5` date, `6` date-time range, `7` date range, `8` boolean |
| `script` | String | Biểu thức formula |
| `calculation_mode` | Integer | Chế độ tính toán: `0` hoặc `1` |
| `display_html` | Boolean | Cho phép hiển thị kết quả text như HTML |
| `zero_default_value` | Boolean | Dùng 0 cho giá trị rỗng trong phép tính |
| `range_date` | Boolean | Kết quả date/date-time là range |
| `format`, `fractional_length`, `number_type`, `currency_code`, `unit_position` | Tuỳ chọn | Chỉ áp dụng cho kết quả number |
| `display_type` | Integer | Kiểu hiển thị kết quả Boolean |
| `alternative_text_true/false` | String | Nhãn thay thế nếu Boolean dùng display type text |

Khi dựng `script`:

- Resolve field của Object trước và dùng đúng slug kỹ thuật trong công thức; không suy đoán slug từ tên hiển thị.
- Mọi nhánh `return` phải tương thích với `return_type`.
- Chỉ dùng API được liệt kê trong Cogover Scripting reference và chú ý null, phép chia số nguyên, timezone, giới hạn 10 giây cùng tối đa 10.000 lượt lặp.
- Khi đưa cấu hình vào request Object Fields API, serialize toàn bộ object Formula thành JSON string ở `meta_data`; escape đúng dấu nháy, dấu gạch chéo ngược và ký tự xuống dòng trong `script`.
- Sau create/update, đọc lại field, parse `metaData` và đối chiếu nguyên văn `script`, `return_type` cùng các tuỳ chọn hiển thị.

Public Object Fields API `/bapi/v1/object-fields` không cung cấp endpoint validate/suggest Formula. Dùng hai endpoint Web App `/api/v1` trong [quy trình kiểm tra Formula](formula-validation.md) bằng phiên do `$cogover-api-auth` tạo. Nếu không thể tạo phiên hoặc kiểm tra không thành công, dừng trước thao tác lưu và báo người dùng.

#### `rollup_summary`

```json
{
  "object": "OT_CHILD_ID",
  "field": "OF_AMOUNT_ID",
  "field_slug": "amount",
  "summary_type": "SUM",
  "filter_criteria": 1
}
```

| Key | Kiểu | Mô tả |
|---|---|---|
| `object` | String | Object nguồn để tổng hợp |
| `field` | String | ID field nguồn |
| `field_slug` | String | Slug field nguồn |
| `summary_type` | String | `SUM`, `COUNT`, `MIN`, `MAX`, `AVERAGE` |
| `filter_criteria` | Integer | Có/loại áp dụng điều kiện filter |

Nếu có điều kiện, gửi thêm top-level `rollup_summary_filter` với `logicType`, `logic`, `conditions`, `sortFields`. `SUM` chỉ phù hợp field số; `MIN`, `MAX`, `AVERAGE` hỗ trợ nhóm số và ngày/giờ phù hợp.

### Bản dịch

```json
{
  "translations": [
    {
      "language": "en-US",
      "name": "Customer code",
      "description": "Unique customer code",
      "tooltip": "Enter the customer code",
      "placeholder": "CUS-0001"
    },
    {
      "language": "vi-VN",
      "name": "Mã khách hàng",
      "description": "Mã khách hàng duy nhất",
      "tooltip": "Nhập mã khách hàng",
      "placeholder": "CUS-0001"
    }
  ]
}
```

Các thuộc tính dịch được của field: `name`, `description`, `tooltip`, `placeholder`. Với option, chỉ `value` được dịch.

Khi cập nhật, mỗi phần tử `translations[]` là trạng thái đầy đủ của riêng ngôn ngữ đó:

- Có ngôn ngữ trong payload: API cập nhật các thuộc tính được gửi; thuộc tính dịch được nhưng bị thiếu sẽ bị xoá bản dịch và fallback về giá trị gốc của field.
- Không có ngôn ngữ trong payload: các bản dịch hiện có của ngôn ngữ đó được giữ nguyên.
- `language` rỗng hoặc thiếu sẽ bị bỏ qua.
- Option áp dụng cùng nguyên tắc cho thuộc tính `value`; xoá hẳn option cũng xoá bản dịch của option trên mọi ngôn ngữ.

### Ví dụ cURL tạo `short_text`

```bash
curl --location 'https://{workspace-domain}/bapi/v1/object-fields' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "type": "short_text",
    "object_type_id": "OT00000000020",
    "name": "Mã khách hàng",
    "slug": "customer_code",
    "tool_tip": "Nhập mã khách hàng",
    "default_value": "",
    "required": 1,
    "description": "Mã dùng để nhận diện khách hàng",
    "hint_text": "CUS-0001",
    "status": 1,
    "manual_modify_allow": true,
    "creatable": 1,
    "multiple": 0,
    "unique": 1,
    "quickSearch": 1,
    "meta_data": "{\"character_limit\":{\"min\":1,\"max\":255},\"multiple_limit\":{\"min\":1,\"max\":30},\"display_type\":1,\"unique_rule\":1}",
    "translations": [
      {
        "language": "en-US",
        "name": "Customer code",
        "description": "Unique customer identifier",
        "tooltip": "Enter the customer code",
        "placeholder": "CUS-0001"
      }
    ]
  }'
```

### Response thành công (201)

```json
{
  "tags": [],
  "r": 0,
  "msg": "OK",
  "requestId": "RQ00000001-ef58-4ec1-9bb5-e279afedb1ce",
  "data": [
    {
      "id": "OF00000000027",
      "slug": "customer_code",
      "options": []
    }
  ],
  "meta": null
}
```

`data` có thể chứa thêm field liên kết được tạo tự động đối với một số type quan hệ.

### Ví dụ cURL tạo `single_choice` với options

Khi có key `options` ở top-level, API tạo field và danh sách option trong cùng một thao tác.

```bash
curl --location 'https://{workspace-domain}/bapi/v1/object-fields' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "type": "single_choice",
    "object_type_id": "OT00000000020",
    "name": "Status",
    "slug": "status",
    "required": 0,
    "status": 1,
    "manual_modify_allow": true,
    "creatable": 1,
    "unique": 0,
    "meta_data": "{\"sort_rule\":0,\"prioritized_sort_rule\":0,\"option_display_type\":2}",
    "options": [
      {
        "id": "00000000-0000-4000-8000-000000000336",
        "sort": 1,
        "value": "Draft",
        "is_default": 1,
        "slug": "draft",
        "status": 1,
        "background_color": "rgba(0, 0, 0, 0)",
        "text_color": "#484848",
        "translations": [
          { "language": "vi-VN", "value": "Nháp" }
        ]
      },
      {
        "id": "00000000-0000-4000-8000-000000000434",
        "sort": 2,
        "value": "Completed",
        "is_default": 0,
        "slug": "completed",
        "status": 1,
        "background_color": "rgba(0, 0, 0, 0)",
        "text_color": "#484848",
        "translations": [
          { "language": "vi-VN", "value": "Hoàn thành" }
        ]
      }
    ],
    "translations": [
      { "language": "vi-VN", "name": "Trạng thái" }
    ]
  }'
```

Khi thành công, `data[0].options` chứa các ID option đã được lưu.

---

## 2. Cập nhật field

**Endpoint:** `PUT /bapi/v1/object-fields/{fieldId}`

`fieldId` trên URL là nguồn tin cậy. Nếu body có `id` khác, ID trên URL được ưu tiên.

API hỗ trợ cập nhật từng phần: field không có trong body thường được giữ nguyên. Riêng `meta_data` là một JSON string hoàn chỉnh; nếu gửi thì cần chứa toàn bộ metadata muốn giữ lại.

### Quy tắc quan trọng

- Nên gửi `type` hiện tại khi cập nhật cấu hình type-specific. Nếu không gửi, API lấy type hiện tại.
- Chỉ một số nhóm được đổi type trực tiếp: `numeric` ↔ `decimal`, `single_choice` ↔ `radio_button`, `multi_choices` ↔ `checkbox`; name field có thể đổi giữa `short_text` và `auto_number` theo các điều kiện áp dụng.
- Với name field, type có thể đổi giữa `short_text` và `auto_number` theo điều kiện áp dụng nhưng slug vẫn bất biến là `name`; ưu tiên cập nhật qua `name_field` của Objects API và bắt buộc GET-back.
- Không thể đổi `slug` nếu Object đã có record; field đang được filter/workflow/layout sử dụng cũng có thể bị chặn với cảnh báo.
- Khi đổi `multiple`, API có thể từ chối nếu dữ liệu hiện tại không tương thích (`r = 543`).
- Khi gửi `options`, bắt buộc có `type` và mảng options là trạng thái thay thế toàn bộ; xem phần `options`.

### Ví dụ cURL

```bash
curl --location --request PUT 'https://{workspace-domain}/bapi/v1/object-fields/OF00000000027' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "type": "short_text",
    "object_type_id": "OT00000000020",
    "name": "Mã khách hàng (đã cập nhật)",
    "slug": "customer_code",
    "tool_tip": "Tooltip mới",
    "default_value": "",
    "required": 0,
    "description": "Mô tả mới",
    "hint_text": "CUS-0001",
    "status": 1,
    "manual_modify_allow": false,
    "creatable": 0,
    "multiple": 0,
    "unique": 1,
    "quickSearch": 1,
    "meta_data": "{\"character_limit\":{\"min\":0,\"max\":255},\"multiple_limit\":{\"min\":1,\"max\":30},\"display_type\":1,\"unique_rule\":1}",
    "translations": [
      {
        "language": "en-US",
        "name": "Customer code",
        "description": "Updated description",
        "tooltip": "Updated tooltip",
        "placeholder": "CUS-0001"
      }
    ]
  }'
```

### Ví dụ cURL cập nhật options của `single_choice`

Request phải có `type` và toàn bộ mảng `options` mong muốn. Không cần gửi `id` trong body vì ID trên URL là nguồn tin cậy.

```bash
curl --location --request PUT 'https://{workspace-domain}/bapi/v1/object-fields/OF00000000036' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "type": "single_choice",
    "name": "Status",
    "slug": "status",
    "meta_data": "{\"sort_rule\":0,\"isActiveTransitionRule\":false,\"prioritized_sort_rule\":0,\"option_display_type\":2}",
    "options": [
      {
        "id": "OP00000000001",
        "sort": 1,
        "value": "Draft",
        "is_default": 1,
        "slug": "draft",
        "status": 1,
        "translations": [
          { "language": "vi-VN", "value": "Nháp" }
        ]
      },
      {
        "id": "OP00000000002",
        "sort": 2,
        "value": "Completed",
        "is_default": 0,
        "slug": "completed",
        "status": 1,
        "translations": [
          { "language": "vi-VN", "value": "Hoàn thành" }
        ]
      },
      {
        "id": "00000000-0000-4000-8000-000000000200",
        "sort": 3,
        "value": "Creating",
        "is_default": 0,
        "slug": "creating",
        "status": 1,
        "translations": [
          { "language": "vi-VN", "value": "Đang tạo" }
        ]
      }
    ],
    "translations": [
      { "language": "vi-VN", "name": "Trạng thái" }
    ]
  }'
```

### Response thành công (200)

```json
{
  "tags": [],
  "r": 0,
  "msg": "OK",
  "requestId": "RQ00000001-ef58-4ec1-9bb5-e279afedb1ce"
}
```

---

## 3. Xoá hoặc khôi phục field

**Endpoint:** `POST /bapi/v1/object-fields/delete`

Endpoint dùng request dạng danh sách. Để thao tác một field, gửi đúng một phần tử trong `data`.

### Request Body

```json
{
  "data": [
    {
      "id": "OF00000000027",
      "delete_type": 1
    }
  ]
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `data` | Array | Có | Danh sách field cần thao tác |
| `data[].id` | String | Có | ID field |
| `data[].delete_type` | Integer | Có | Loại thao tác xoá/khôi phục |

### Giá trị `delete_type`

| Giá trị | Ý nghĩa | Khuyến nghị public client |
|---|---|---|
| `1` | Soft delete: chuyển status sang pending delete, lưu trạng thái cũ và đặt lịch xoá sau 14 ngày | Nên dùng cho thao tác xoá thông thường |
| `2` | Undo soft delete: khôi phục status cũ và huỷ lịch xoá | Dùng để khôi phục |
| `3` | Actual delete: dọn option/relation/filter, chuyển field sang deleting và xoá dữ liệu field khỏi record | Chỉ dùng sau khi người dùng xác nhận xoá thực tế |

API có thể trả cảnh báo `r = 524` nếu field đang được dùng trong filter, object security, formula hoặc workflow. Field của workflow Object có thể không được phép xoá.

### Ví dụ cURL soft delete

```bash
curl --location 'https://{workspace-domain}/bapi/v1/object-fields/delete' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "data": [
      {
        "id": "OF00000000027",
        "delete_type": 1
      }
    ]
  }'
```

### Ví dụ cURL khôi phục

```bash
curl --location 'https://{workspace-domain}/bapi/v1/object-fields/delete' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "data": [
      {
        "id": "OF00000000027",
        "delete_type": 2
      }
    ]
  }'
```

### Response thành công (200)

```json
{
  "tags": [],
  "r": 0,
  "msg": "OK",
  "requestId": "RQ00000001-ef58-4ec1-9bb5-e279afedb1ce"
}
```

---

## Response lỗi thường gặp

| `r` | Mô tả |
|---|---|
| `400` | `object_type_id` không hợp lệ |
| `401` | Không xác định được workspace từ access token |
| `405` | Thiếu/không hợp lệ field ID |
| `408` | Thiếu hoặc sai field type |
| `409` | Giá trị hoặc option value không hợp lệ |
| `411` | `required` không phải `0/1` |
| `412` | `multiple` không phải `0/1` |
| `413` | `status` hoặc cờ standard không hợp lệ |
| `418` | `unique` hoặc `delete_type` không hợp lệ |
| `419` | `option_sorting_policy` không thuộc `0/1/2` |
| `424` | Trùng option value |
| `425` | Trùng option ID |
| `429` | `meta_data` không hợp lệ |
| `432` | Tooltip dài hơn 255 ký tự |
| `433` | Hint dài hơn 255 ký tự hoặc unique rule không hợp lệ |
| `434` | Description dài hơn 1.000 ký tự |
| `439` | Slug sai định dạng |
| `440` | Tên field không hợp lệ |
| `446` | Thiếu/sai `related_list_name` |
| `502` | Không tìm thấy field |
| `504` | Type không được định nghĩa |
| `505` | `default_value` không hợp lệ với type/metadata |
| `516` | Vượt quá 200 options |
| `524` | Cảnh báo field đang được sử dụng hoặc không thể xoá |
| `525` | Slug đã tồn tại |
| `527` | Tên field đã tồn tại |
| `535` | Vượt giới hạn custom field của gói subscription |
| `542` | Type không hỗ trợ multiple value |
| `543` | Record hiện tại không tương thích khi đổi multiple |
| `700` | Lỗi máy chủ |

Ví dụ:

```json
{
  "r": 429,
  "msg": "Meta data is invalid",
  "requestId": "RQ...",
  "tags": []
}
```

## Lưu ý sử dụng

- Nếu chỉ muốn thay đổi một số option, client cần merge thay đổi vào danh sách option hiện tại rồi gửi lại toàn bộ mảng. Option hiện có bị thiếu trong mảng `options` đã gửi sẽ bị xoá.
- Việc đổi slug, type, unique, multiple hoặc xoá field có thể ảnh hưởng dữ liệu record, filter, workflow, formula, related list và object relation. Client nên hiển thị `msg`/metadata cảnh báo thay vì chỉ dựa vào HTTP status.
