# Lọc danh sách bản ghi

## Cấu trúc bộ lọc:

Khi gọi API `/bapi/v1/records/list`, sử dụng key `filters` trong request body (xem SKILL.md). Bên dưới mô tả cấu trúc chi tiết của mỗi phần tử trong mảng `filters`, cùng với `logic_sequence` và `type` để kết hợp các điều kiện.

### Chế độ kết hợp điều kiện (`type` và `logic_sequence`)

Có 3 chế độ kết hợp các điều kiện lọc, được điều khiển bởi tham số số `type` ở cấp cao nhất của request body. Luôn truyền tường minh; không bỏ key để trông chờ mặc định AND. Request thiếu `type` đã được kiểm chứng trả `r: 27`, `Invalid filter type`, kể cả khi `filters[].fieldType` hợp lệ.

| `type` | Chế độ | `logic_sequence` | Mô tả |
|--------|--------|-------------------|--------|
| `1` | **AND** | `""` (để trống) | Tất cả điều kiện phải thoả mãn |
| `2` | **OR** | `""` (để trống) | Chỉ cần một trong các điều kiện thoả mãn |
| `3` | **CUSTOM** | Biểu thức tuỳ chỉnh | Kết hợp AND/OR theo biểu thức tự định nghĩa |

**Ví dụ AND (`type: 1`)** — lọc bản ghi có `status` là "new" VÀ `is_active` là true:
```json
{
    "type": 1,
    "logic_sequence": "",
    "filters": [
        {"field": "status", "op": "=", "params": "new", "fieldType": "single_choice"},
        {"field": "is_active", "op": "=", "params": 1, "fieldType": "boolean"}
    ]
}
```

**Ví dụ OR (`type: 2`)** — lọc bản ghi có `status` là "new" HOẶC `status` là "completed":
```json
{
    "type": 2,
    "logic_sequence": "",
    "filters": [
        {"field": "status", "op": "=", "params": "new", "fieldType": "single_choice"},
        {"field": "status", "op": "=", "params": "completed", "fieldType": "single_choice"}
    ]
}
```

**Ví dụ CUSTOM (`type: 3`)** — kết hợp tuỳ chỉnh: điều kiện 1 AND (điều kiện 2 OR điều kiện 3):
```json
{
    "type": 3,
    "logic_sequence": "1 AND (2 OR 3)",
    "filters": [
        {"field": "is_active", "op": "=", "params": 1, "fieldType": "boolean"},
        {"field": "status", "op": "=", "params": "new", "fieldType": "single_choice"},
        {"field": "status", "op": "=", "params": "completed", "fieldType": "single_choice"}
    ]
}
```

Trong `logic_sequence`, các số `1`, `2`, `3`,... tương ứng với thứ tự các phần tử trong mảng `filters` (bắt đầu từ 1). Sử dụng `AND`, `OR` và dấu ngoặc `()` để tạo biểu thức logic.


## Các điều kiện

Có thể lọc danh sách bản ghi trả về bằng cách truyền các điều kiện lọc vào mảng `filters`.

```json
"filters": [
    {
        "field": "do_not_call",
        "op": "=",
        "params": 0,
        "fieldType": "boolean"
    },
    {
        "field": "mobile_phones",
        "op": "not null",
        "params": null,
        "fieldType": "phone"
    },
    {
        "field": "emails",
        "op": "not null",
        "params": null,
        "fieldType": "email"
    }
]
```

- `field`: Slug của trường dữ liệu.
- `op`, `params`, `fieldType`: Điều kiện, giá trị và loại trường của trường dữ liệu.

    | Trường dữ liệu `fieldType` | Điều kiện | Giá trị `op` | Kiểu dữ liệu truyền vào `params`
    | ----------- | ----------- | ----------- | ----------- |
    | Văn bản ngắn (`short_text`) | Bằng | = | String |
    |  | Không bằng | != | String |
    |  | Chứa | like | String |
    |  | Không chứa | not like | String |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Bắt đầu với | startsWith | String |
    |  | Kết thúc với | endsWith | String |
    |  | Bằng một trong | in | Array (String) |
    |  | Không bằng bất kỳ | not in | Array (String) |
    | Văn bản dài (`long_text`) | Chứa (gần đúng) | contains any | String |
    |  | Không chứa (gần đúng) | not contains any | String |
    |  | Chứa chính xác | like | String |
    |  | Không chứa chính xác | not like | String |
    |  | Chứa | like | String |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Số điện thoại (`phone`) | Bằng | = | String |
    |  | Không bằng | != | String |
    |  | Chứa | like | String |
    |  | Không chứa | not like | String |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Bắt đầu với | startsWith | String |
    |  | Kết thúc với | endsWith | String |
    |  | Bằng một trong | in | Array (String) |
    |  | Không bằng bất kỳ | not in | Array (String) |
    | Boolean (`boolean`) | Bằng | = | `1`: true<br>`0`: false |
    |  | Không bằng | != | `1`: true<br>`0`: false |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Email (`email`) | Bằng | = | String |
    |  | Không bằng | != | String |
    |  | Chứa | like | String |
    |  | Không chứa | not like | String |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Bắt đầu với | startsWith | String |
    |  | Kết thúc với | endsWith | String |
    |  | Bằng một trong | in | Array (String) |
    |  | Không bằng bất kỳ | not in | Array (String) |
    | Lựa chọn đơn (`single_choice`) | Bằng | = | String |
    |  | Không bằng | != | String |
    |  | Là một trong | in | Array (String) |
    |  | Không thuộc | not in | Array (String) |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Lựa chọn nhiều (`multi_choices`) | Chứa một trong | in | Array (String) |
    |  | Không chứa bất kỳ | not in | Array (String) |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Cây thư mục (`cascading`) | Bằng | = | Array (String) |
    |  | Không bằng | != | Array (String) |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Ngày (`date`) | Bằng | = | String<br>Định dạng `"YYYY-MM-DD"`<br>Ví dụ: `"2025-10-02"` |
    |  | Không bằng | != | String<br>Định dạng `"YYYY-MM-DD"`<br>Ví dụ: `"2025-10-02"` |
    |  | Nhỏ hơn | < | String<br>Định dạng `"YYYY-MM-DD"`<br>Ví dụ: `"2025-10-02"` |
    |  | Nhỏ hơn hoặc bằng | <= | String<br>Định dạng `"YYYY-MM-DD"`<br>Ví dụ: `"2025-10-02"` |
    |  | Lớn hơn | > | String<br>Định dạng `"YYYY-MM-DD"`<br>Ví dụ: `"2025-10-02"` |
    |  | Lớn hơn hoặc bằng | >= | String<br>Định dạng `"YYYY-MM-DD"`<br>Ví dụ: `"2025-10-02"` |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Thuộc khoảng | between | Array (String)<br>Định dạng `["YYYY-MM-DD", "YYYY-MM-DD"]`<br>Ví dụ: `["2025-10-14", "2025-10-17"]` |
    |  | Hôm qua | Yesterday |  |
    |  | Hôm nay | Today |  |
    |  | Ngày mai | Tomorrow |  |
    |  | Trong n ngày vừa qua | Last n days | Int |
    |  | Trong n ngày tới | Next n days | Int |
    |  | n Ngày trước | n Days ago | Int |
    |  | n Ngày nữa | n Days from now | Int |
    |  | Tuần trước | Last week |  |
    |  | Tuần này | This week |  |
    |  | Tuần sau | Next week |  |
    |  | Trong n tuần vừa qua | Last n weeks | Int |
    |  | Trong n tuần tới | Next n weeks | Int |
    |  | Tháng trước | Last month |  |
    |  | Tháng này | This month |  |
    |  | Tháng sau | Next month |  |
    |  | Trong n tháng vừa qua | Last n months | Int |
    |  | Trong n tháng tới | Next n months | Int |
    |  | Quý trước | Last quarter |  |
    |  | Quý này | This quarter |  |
    |  | Quý sau | Next quarter |  |
    |  | Năm ngoái | Last year |  |
    |  | Năm nay | This year |  |
    |  | Năm sau | Next year |  |
    |  | Trong n năm vừa qua | Last n years | Int |
    |  | Trong n năm tới | Next n years | Int |
    | Ngày giờ (`date_time`) | Bằng | = | Timestamp (milisecond) |
    |  | Không bằng | != | Timestamp (milisecond) |
    |  | Nhỏ hơn | < | Timestamp (milisecond) |
    |  | Nhỏ hơn hoặc bằng | <= | Timestamp (milisecond) |
    |  | Lớn hơn | > | Timestamp (milisecond) |
    |  | Lớn hơn hoặc bằng | >= | Timestamp (milisecond) |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Thuộc khoảng | between | Array Timestamp (milisecond)<br>Ví dụ: `[1760382900000, 1760725800000]` |
    |  | Hôm qua | Yesterday |  |
    |  | Hôm nay | Today |  |
    |  | Ngày mai | Tomorrow |  |
    |  | Trong n ngày vừa qua | Last n days | Int |
    |  | Trong n ngày tới | Next n days | Int |
    |  | n Ngày trước | n Days ago | Int |
    |  | n Ngày nữa | n Days from now | Int |
    |  | Tuần trước | Last week |  |
    |  | Tuần này | This week |  |
    |  | Tuần sau | Next week |  |
    |  | Trong n tuần vừa qua | Last n weeks | Int |
    |  | Trong n tuần tới | Next n weeks | Int |
    |  | Tháng trước | Last month |  |
    |  | Tháng này | This month |  |
    |  | Tháng sau | Next month |  |
    |  | Trong n tháng vừa qua | Last n months | Int |
    |  | Trong n tháng tới | Next n months | Int |
    |  | Quý trước | Last quarter |  |
    |  | Quý này | This quarter |  |
    |  | Quý sau | Next quarter |  |
    |  | Năm ngoái | Last year |  |
    |  | Năm nay | This year |  |
    |  | Năm sau | Next year |  |
    |  | Trong n năm vừa qua | Last n years | Int |
    |  | Trong n năm tới | Next n years | Int |
    | Thời giờ (`time`) | Bằng | = | Timestamp (milisecond, trong khoản từ `0` tới `86340000`) |
    |  | Không bằng | != | Timestamp (milisecond, trong khoản từ `0` tới `86340000`) |
    |  | Nhỏ hơn | < | Timestamp (milisecond, trong khoản từ `0` tới `86340000`) |
    |  | Nhỏ hơn hoặc bằng | <= | Timestamp (milisecond, trong khoản từ `0` tới `86340000`) |
    |  | Lớn hơn | > | Timestamp (milisecond, trong khoản từ `0` tới `86340000`) |
    |  | Lớn hơn hoặc bằng | >= | Timestamp (milisecond, trong khoản từ `0` tới `86340000`) |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Thuộc khoảng | between | Array Timestamp (milisecond, trong khoản từ `0` tới `86340000`)<br>Ví dụ: `[0, 1800000]` |
    | Thời lượng (`time_duration`)  | Bằng | = | Timestamp (milisecond) |
    |  | Không bằng | != | Timestamp (milisecond) |
    |  | Nhỏ hơn | < | Timestamp (milisecond) |
    |  | Nhỏ hơn hoặc bằng | <= | Timestamp (milisecond) |
    |  | Lớn hơn | > | Timestamp (milisecond) |
    |  | Lớn hơn hoặc bằng | >= | Timestamp (milisecond) |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Thuộc khoảng | between | Array Timestamp (milisecond)<br>Ví dụ: `[28800000, 19353600000]` |
    | Khoảng ngày (`date_range`) | Chứa | = | String<br>Định dạng `"YYYY-MM-DD"`<br>Ví dụ: `"2025-10-02"` |
    |  | Nằm hoàn toàn trong | rangeWithin | Array (String)<br>Định dạng `["YYYY-MM-DD", "YYYY-MM-DD"]`<br>Ví dụ: `["2025-10-14", "2025-10-17"]` |
    |  | Chứa hoàn toàn | rangeContains | Array (String)<br>Định dạng `["YYYY-MM-DD", "YYYY-MM-DD"]`<br>Ví dụ: `["2025-10-14", "2025-10-17"]` |
    |  | Có phần giao nhau | between | Array (String)<br>Định dạng `["YYYY-MM-DD", "YYYY-MM-DD"]`<br>Ví dụ: `["2025-10-14", "2025-10-17"]` |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Khoảng ngày giờ (`date_time_range`) | Chứa | = | Timestamp (milisecond) |
    |  | Nằm hoàn toàn trong | rangeWithin | Array Timestamp (milisecond)<br>Ví dụ: `[1760382900000, 1760725800000]` |
    |  | Chứa hoàn toàn | rangeContains | Array Timestamp (milisecond)<br>Ví dụ: `[1760382900000, 1760725800000]` |
    |  | Có phần giao nhau | between | Array Timestamp (milisecond)<br>Ví dụ: `[1760382900000, 1760725800000]` |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Khoảng giờ (`time_range`) | Chứa | = | Timestamp (milisecond, trong khoản từ `0` tới `86340000`) |
    |  | Nằm hoàn toàn trong | rangeWithin | Array Timestamp (milisecond, trong khoản từ `0` tới `86340000`)<br>Ví dụ: `[0, 1800000]` |
    |  | Chứa hoàn toàn | rangeContains | Array Timestamp (milisecond, trong khoản từ `0` tới `86340000`)<br>Ví dụ: `[0, 1800000]` |
    |  | Có phần giao nhau | between | Array Timestamp (milisecond, trong khoản từ `0` tới `86340000`)<br>Ví dụ: `[0, 1800000]` |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Đường dẫn liên kết URL (`url`) | Bằng | = | String |
    |  | Không bằng | != | String |
    |  | Chứa | like | String |
    |  | Không chứa | not like | String |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Bắt đầu với | startsWith | String |
    |  | Kết thúc với | endsWith | String |
    |  | Bằng một trong | in | Array (String) |
    |  | Không bằng bất kỳ | not in | Array (String) |
    | Tiền tệ (`currency`) | Bằng | = | Dec |
    |  | Không bằng | != | Dec |
    |  | Nhỏ hơn | < | Dec |
    |  | Nhỏ hơn hoặc bằng | <= | Dec |
    |  | Lớn hơn | > | Dec |
    |  | Lớn hơn hoặc bằng | >= | Dec |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Thuộc khoảng | between | Array (Dec) |
    | Số nguyên (`numeric`) | Bằng | = | Int |
    |  | Không bằng | != | Int |
    |  | Nhỏ hơn | < | Int |
    |  | Nhỏ hơn hoặc bằng | <= | Int |
    |  | Lớn hơn | > | Int |
    |  | Lớn hơn hoặc bằng | >= | Int |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Thuộc khoảng | between | Array (Int) |
    | Số thập phân (`decimal`) | Bằng | = | Dec |
    |  | Không bằng | != | Dec |
    |  | Nhỏ hơn | < | Dec |
    |  | Nhỏ hơn hoặc bằng | <= | Dec |
    |  | Lớn hơn | > | Dec |
    |  | Lớn hơn hoặc bằng | >= | Dec |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Thuộc khoảng | between | Array (Dec) |
    | Nhãn (`label`) | Bằng một trong | in | Array (String) |
    |  | Không bằng bất kỳ | not in | Array (String) |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Phần trăm (`percent`) | Bằng | = | Dec<br>`0` tương ứng `0%`<br>`1` tương ứng `100%` |
    |  | Không bằng | != | Dec<br>`0` tương ứng `0%`<br>`1` tương ứng `100%` |
    |  | Nhỏ hơn | < | Dec<br>`0` tương ứng `0%`<br>`1` tương ứng `100%` |
    |  | Nhỏ hơn hoặc bằng | <= | Dec<br>`0` tương ứng `0%`<br>`1` tương ứng `100%` |
    |  | Lớn hơn | > | Dec<br>`0` tương ứng `0%`<br>`1` tương ứng `100%` |
    |  | Lớn hơn hoặc bằng | >= | Dec<br>`0` tương ứng `0%`<br>`1` tương ứng `100%` |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Thuộc khoảng | between | Array (Dec)<br>`0` tương ứng `0%`<br>`1` tương ứng `100%` |
    | Tệp tin (`file`)  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Xếp hạng (`rating`) | Bằng | = | Int |
    |  | Không bằng | != | Int |
    |  | Nhỏ hơn | < | Int |
    |  | Nhỏ hơn hoặc bằng | <= | Int |
    |  | Lớn hơn | > | Int |
    |  | Lớn hơn hoặc bằng | >= | Int |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Thuộc khoảng | between | Array (Int) |
    | Tra cứu (`reference`) | Bằng | = | Record ID hoặc `"$currentUser"` |
    |  | Không bằng | != | Record ID hoặc `"$currentUser"` |
    |  | Bằng một trong | in | Array (Record ID) |
    |  | Không bằng bất kỳ | not in | Array (Record ID) |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    | Đánh số tự động (`auto_number`) | Bằng | = | String |
    |  | Không bằng | != | String |
    |  | Chứa | like | String |
    |  | Không chứa | not like | String |
    |  | Trống | is null |  |
    |  | Không trống | not null |  |
    |  | Bắt đầu với | startsWith | String |
    |  | Kết thúc với | endsWith | String |
    |  | Bằng một trong | in | Array (String) |
    |  | Không bằng bất kỳ | not in | Array (String) |
