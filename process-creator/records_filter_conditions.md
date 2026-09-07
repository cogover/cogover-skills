# Lọc danh sách bản ghi

## Cấu trúc bộ lọc:
```
{
    ...
    "conditions": [
        {
            "field": "last_first_name",
            "op": "is null",
            "params": null,
            "fieldType": "formula"
        },
        {
            "field": "first_last_name",
            "op": "not like",
            "params": "x",
            "fieldType": "formula"
        },
        {
            "field": "status",
            "op": "in",
            "params": [
                "nurturing",
                "unqualified",
                "qualified"
            ],
            "fieldType": "single_choice"
        }
    ],
    "logic": "1 AND (2 OR 3)",
    "logicType": "AND",
    ...
}
```

Trong đó: logicType = 'CUSTOM' hoặc 'AND' hoặc 'OR'. Nếu logicType=CUSTOM thì logic sẽ chỉ ra biểu thức, VD: 1 AND (2 OR 3)


## Các điều kiện

Có thể lọc danh sách bản ghi trả về bằng cách truyền các điều kiện lọc vào mảng `conditions`.

```json
"conditions": [
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
],
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
    | Boolean (`boolean`) | Bằng | = | `1`: true<br>`2`: false |
    |  | Không bằng | != | `1`: true<br>`2`: false |
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
