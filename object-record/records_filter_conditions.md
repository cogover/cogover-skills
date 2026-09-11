# Lọc danh sách bản ghi

Danh mục dùng chung cho cả bộ skill. Mỗi điều kiện lọc là một object `{"field", "op", "params", "fieldType"}`; bảng ở mục [Các điều kiện](#các-điều-kiện) là nguồn duy nhất về toán tử `op` và kiểu `params` theo `fieldType`. Cách bọc các điều kiện khác nhau theo API, xem mục [Cấu trúc bộ lọc](#cấu-trúc-bộ-lọc).

## Cấu trúc bộ lọc

### Records API (`POST /bapi/v1/records/list`)

Request body dùng `filters` (mảng điều kiện), `type` (số) và `logic_sequence` (xem [SKILL.md](SKILL.md)). Luôn truyền `type` tường minh ở cấp cao nhất; thiếu `type` đã kiểm chứng trả `r: 27`, `Invalid filter type`, kể cả khi `filters[].fieldType` hợp lệ.

| `type` | Chế độ | `logic_sequence` |
|--------|--------|-------------------|
| `1` | **AND** — tất cả điều kiện phải thoả mãn | `""` |
| `2` | **OR** — chỉ cần một điều kiện thoả mãn | `""` |
| `3` | **CUSTOM** — kết hợp AND/OR theo biểu thức tự định nghĩa | Biểu thức, ví dụ `"1 AND (2 OR 3)"` |

Trong biểu thức, các số `1`, `2`, `3`,... là thứ tự phần tử trong mảng điều kiện (bắt đầu từ 1); dùng `AND`, `OR` và dấu ngoặc `()`. Ví dụ CUSTOM — điều kiện 1 AND (điều kiện 2 OR điều kiện 3):

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

### Dùng trong Process (`$process-creator`)

Node và trigger của Process dùng cùng phần tử điều kiện nhưng bọc bằng `conditions` + `logicType` + `logic` thay cho `filters` + `type` + `logic_sequence`:

| | Records API | Process |
|---|---|---|
| Mảng điều kiện | `filters` | `conditions` |
| Chế độ kết hợp | `type`: `1` / `2` / `3` | `logicType`: `"AND"` / `"OR"` / `"CUSTOM"` |
| Biểu thức | `logic_sequence`, chỉ khi `type: 3` | `logic`, chỉ khi `logicType` là `"CUSTOM"`; các chế độ khác để `""` |

```json
{
    "conditions": [
        {"field": "is_active", "op": "=", "params": 1, "fieldType": "boolean"},
        {"field": "status", "op": "in", "params": ["nurturing", "qualified"], "fieldType": "single_choice"}
    ],
    "logicType": "AND",
    "logic": ""
}
```

Cách đánh số trong `logic` giống `logic_sequence`. Quy tắc riêng của từng node (giá trị `logicType` khi không có điều kiện, điều kiện tham chiếu biến workflow) theo tài liệu node trong `$process-creator`.

## Các điều kiện

Ví dụ ba điều kiện: boolean bằng `0`, số điện thoại không trống, email không trống:

```json
[
    {"field": "do_not_call", "op": "=", "params": 0, "fieldType": "boolean"},
    {"field": "mobile_phones", "op": "not null", "params": null, "fieldType": "phone"},
    {"field": "emails", "op": "not null", "params": null, "fieldType": "email"}
]
```

- `field`: Slug của trường dữ liệu.
- `op`, `params`, `fieldType`: Điều kiện, giá trị và loại trường của trường dữ liệu; `fieldType` khớp giá trị `fieldType` của field trong Object.

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
