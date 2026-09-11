# Saved report settings và preview

## Base setting

Base setting chỉ dùng cho create; khi update, merge vào toàn bộ setting vừa đọc từ service `229` và bảo toàn các key mà template chưa liệt kê. Không copy `filterId`, report field ID, workspace ID, timestamps hoặc ACL IDs từ payload mẫu.

```json
{
  "displayFieldIds": [],
  "groupByRows": [],
  "groupByColumns": [],
  "groupTypeMap": {},
  "filterId": null,
  "logicSequence": "",
  "filterItems": [],
  "relationFilterItems": [],
  "aggregates": {},
  "columnSettings": [],
  "viewConfig": {},
  "summaryFormulas": [],
  "rowFormulas": [],
  "sorts": [],
  "sortsColumn": [],
  "isCutoffRecord": false
}
```

## Field và group

- `displayFieldIds`: mảng `{ "data": "<REPORT_FIELD_ID>" }`.
- `groupByRows` và `groupByColumns`: tối đa 2 report field ID mỗi mảng; chỉ group cột khi có ít nhất một group hàng. `displayFieldIds`, `groupByRows`, `groupByColumns` không trùng nhau (không dùng cùng field ở cả row và column group).
- Field group phải ở section hiển thị, không multiple, không có data type `cascading`, `file` hoặc `formula`.
- Bỏ toàn bộ group hàng: xóa group cột, `sortsColumn` và `summaryFormulas`. Thêm group cột: xóa `rowFormulas` và `summaryFormulas`.

## Aggregate

`aggregates` trong saved setting là map `{ "<REPORT_FIELD_ID>": ["sum", "count"] }` với operation `sum`, `avg`, `count`, `max`, `min`, `median`. Chỉ summarize field không multiple, không đang group và có data type `numeric`, `decimal`, `percent`, `currency`, `rating`, `formula` (chỉ khi metadata trả về number) hoặc `time_duration`. `count` dùng được cho display field khác nhưng phải chọn field không null phù hợp với grain; không thêm count cho mọi field khi không có yêu cầu nghiệp vụ.

## Group theo thời gian

`groupTypeMap` chỉ áp dụng cho field `date`/`date_time` đang nằm trong group hàng/cột: `{ "<DATE_REPORT_FIELD_ID>": "month" }` với giá trị `date`, `week`, `month`, `quarter`, `year`, `miy`, `dim`. Khi gọi service `200`, đổi ID group field thành `<FIELD_ID>_<groupType>` (ví dụ `FRP123_month`) trong request; không đổi ID trong saved `setting`.

## Filter và relation filter

Filter item theo shape Public API đã xác minh, ví dụ:

```json
{ "op": "This quarter", "field": "<REPORT_FIELD_ID>", "isPinned": false, "params": null, "fieldType": "date_time" }
```

Đây không phải catalog đầy đủ: operator và `params` phụ thuộc data type. Không tự sáng tác operator; chỉ dùng operator và shape đã được Public API contract hoặc response thực tế của workspace xác nhận. Chưa xác nhận được thì dừng trước mutation và báo phần contract còn thiếu.

Logic: không có filter → `filterItems: []`, `logicSequence: ""`; có filter không có logic tùy chỉnh → `1 AND 2 AND ...`; logic tùy chỉnh → `logicSequence` khớp đúng chỉ số item và service `200` dùng `filter_type: 3` với `logic_sequence` tương ứng.

Saved relation filter và dạng `cross_filters` tương ứng trong service `200`:

```json
{ "objectId": "<MAIN_OBJECT_ID>", "filterItems": [], "op": "with", "param": "<MAIN_FIELD_ID>-<REF_OBJECT_ID>" }
```

```json
{ "main_object": "<MAIN_OBJECT_ID>", "main_field_id": "<MAIN_FIELD_ID>", "ref_object": "<REF_OBJECT_ID>", "type": "with", "filters": [] }
```

`type` chỉ là `with` hoặc `without`. Không thêm relation filter khi Report Type chưa có relation tương ứng hoặc `param` chưa được Public API xác nhận.

## Sort, cutoff và view

Saved `sorts` là mảng map; service `200` nhận mảng phẳng `{key, order, operation?}`; key trong saved setting có suffix aggregate như `__sum` thì loại suffix trước request:

```json
[{ "<REPORT_FIELD_ID>": { "key": "<REPORT_FIELD_ID>", "order": "desc", "operation": "sum" } }]
```

Không đoán key sort của summary/row formula từ slug; chỉ sort formula khi key và wire shape đã được Public API contract hoặc response hiện tại xác nhận.

Cutoff/top-N chỉ dùng khi có group hàng và key hợp lệ: `"isCutoffRecord": true, "cutoffRecordConfig": { "key": "<GROUP_OR_METRIC_FIELD_ID>", "limit": 10 }`. `viewConfig.showDetailRow: false` ẩn detail row cho báo cáo tổng hợp; giữ `viewConfig: {}` nếu không có yêu cầu.

## Formula

Row formula cần ít nhất một display field, tối đa 1. Summary formula cần group hàng và display field, tối đa 5. Cả hai không dùng cùng group cột. Shape điển hình:

```json
{
  "name": "Tỷ trọng",
  "slug": "share",
  "return_type": 2,
  "formula_return_type": 0,
  "decimal_point": 2,
  "script": "current / total * 100",
  "allow_zero_if_null": true,
  "apply_type": 0
}
```

`return_type`: `0` number, `1` currency, `2` percent. `formula_return_type`: `0` number, `1` text. Không giả định variable name hoặc formula context từ ví dụ; gọi service `246` evaluate và validate schema trước khi lưu.

## Chuyển setting thành service 200

`report_id` là Report Type ID; saved report ID chỉ dùng cho detail/update saved report. `setting: true` trong service `200` là cờ chạy đồng bộ, không phải saved setting object; kết quả chờ có thể trả `r != 0`/HTTP `400`, chỉ theo cơ chế async mà response hiện tại chứng minh.

```json
{
  "report_id": "<REPORT_TYPE_ID>",
  "filter_id": null,
  "fields": ["<DISPLAY_ID>", "<GROUP_ID>"],
  "preview": false,
  "size": 100,
  "filters": [],
  "filter_type": 1,
  "logic_sequence": "",
  "group_rows": ["<GROUP_ID>"],
  "group_columns": [],
  "calc_sub_total": true,
  "calc_total": true,
  "aggregates": [
    { "id": "<DISPLAY_ID>", "operations": ["count"] }
  ],
  "summary_formulas": [],
  "row_formulas": [],
  "sorts": [],
  "with_lookup": true,
  "force": false
}
```

Transform bắt buộc từ saved `setting`:

1. `fields` = union có thứ tự của display, group cột và group hàng; loại rỗng/trùng.
2. `group_type_map` chỉ dùng để đổi ID trong `group_rows`/`group_columns` trước request (xem [Group theo thời gian](#group-theo-thời-gian)).
3. `aggregates` map → mảng `[{ "id": "<REPORT_FIELD_ID>", "operations": ["sum", "count"] }]`, chỉ giữ field hợp lệ.
4. `relationFilterItems` → `cross_filters`.
5. `isCutoffRecord` → `rows_limit`; bỏ khi false.
6. Saved `sorts` map → mảng phẳng.
7. `filter_type`: `3` khi có custom `logic_sequence`; nếu không, `1` AND hoặc `2` OR đúng semantics.

## Các mẫu cấu hình

Danh sách chi tiết:

```json
{
  "displayFieldIds": [
    { "data": "<CODE_FIELD>" },
    { "data": "<NAME_FIELD>" },
    { "data": "<AMOUNT_FIELD>" }
  ],
  "groupByRows": [],
  "groupByColumns": [],
  "aggregates": {},
  "viewConfig": { "showDetailRow": true }
}
```

Count theo dimension:

```json
{
  "displayFieldIds": [{ "data": "<RECORD_KEY_FIELD>" }],
  "groupByRows": ["<DIMENSION_FIELD>"],
  "groupByColumns": [],
  "aggregates": { "<RECORD_KEY_FIELD>": ["count"] },
  "viewConfig": { "showDetailRow": false }
}
```

Pivot theo dimension và tháng (tổng theo tháng không pivot: bỏ `groupByColumns`, đưa `<DATE_FIELD>` vào `groupByRows`):

```json
{
  "displayFieldIds": [{ "data": "<AMOUNT_FIELD>" }],
  "groupByRows": ["<DIMENSION_FIELD>"],
  "groupByColumns": ["<DATE_FIELD>"],
  "groupTypeMap": { "<DATE_FIELD>": "month" },
  "aggregates": { "<AMOUNT_FIELD>": ["sum"] },
  "summaryFormulas": [],
  "rowFormulas": []
}
```

## Checklist

- Mọi ID là report field thuộc Report Type hiện tại; display/group không trùng nhau.
- Mỗi mảng group không quá 2; group cột có group hàng; `groupTypeMap` chỉ dùng field date/date_time đang group.
- Aggregate đúng data type và không làm sai grain/cardinality.
- Filter operator/params đến từ Public API contract hoặc response đã xác minh; `logicSequence` khớp chỉ số `filterItems`.
- Sort, cutoff và relation filter đúng shape ở các mục trên.
- Formula đã evaluate bằng `246` và slug không trùng.
