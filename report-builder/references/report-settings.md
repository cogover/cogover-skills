# Saved report settings và preview

## Mục lục

1. [Base setting](#base-setting)
2. [Field và group](#field-và-group)
3. [Aggregate](#aggregate)
4. [Group theo thời gian](#group-theo-thời-gian)
5. [Filter và relation filter](#filter-và-relation-filter)
6. [Sort, cutoff và view](#sort-cutoff-và-view)
7. [Formula](#formula)
8. [Chuyển setting thành service 200](#chuyển-setting-thành-service-200)
9. [Các mẫu cấu hình](#các-mẫu-cấu-hình)
10. [Checklist](#checklist)

## Base setting

Dùng một object đầy đủ để saved report có thể được đọc và cập nhật ổn định:

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

Không copy `filterId`, report field ID, workspace ID, timestamps hoặc ACL IDs từ payload mẫu.

Base setting chỉ dùng cho create. Khi update report hiện có, merge vào toàn bộ setting vừa đọc từ service `229` và bảo toàn các key mà template này chưa liệt kê.

## Field và group

- `displayFieldIds`: mảng `{ "data": "<REPORT_FIELD_ID>" }`.
- `groupByRows`: tối đa 2 report field IDs.
- `groupByColumns`: tối đa 2 field IDs và chỉ dùng khi có ít nhất một group row.
- Không dùng cùng field ở cả row và column group.
- Giữ `displayFieldIds`, `groupByRows` và `groupByColumns` không trùng nhau.
- Khi bỏ toàn bộ group row, xóa group column, `sortsColumn` và `summaryFormulas`.
- Khi thêm group column, xóa `rowFormulas` và `summaryFormulas`.

Field group hợp lệ phải ở section hiển thị, không multiple, và không có data type `cascading`, `file` hoặc `formula`.

## Aggregate

Operation hợp lệ:

```text
sum, avg, count, max, min, median
```

`aggregates` trong saved setting là map:

```json
{
  "<REPORT_FIELD_ID>": ["sum", "count"]
}
```

Public Report API cho phép summarize field không multiple, không đang group, và có data type:

- `numeric`, `decimal`, `percent`, `currency`, `rating`, `formula`, `time_duration`.
- Formula chỉ aggregate khi metadata trả về number.
- `count` có thể dùng cho display field khác, nhưng phải chọn field không null phù hợp với grain. Không thêm count cho mọi field nếu không có yêu cầu nghiệp vụ.

Trong request service `200`, chuyển map thành mảng:

```json
[
  { "id": "<REPORT_FIELD_ID>", "operations": ["sum", "count"] }
]
```

## Group theo thời gian

`groupTypeMap` chỉ áp dụng cho field `date`/`date_time` đang nằm trong row/column group:

```json
{ "<DATE_REPORT_FIELD_ID>": "month" }
```

Giá trị hợp lệ:

```text
date, week, month, quarter, year, miy, dim
```

Khi gọi service `200`, đổi group field thành `<FIELD_ID>_<groupType>`, ví dụ `FRP123_month`. Không đổi ID trong saved `setting`; chỉ transform request chạy.

## Filter và relation filter

Filter item dùng shape Public API đã xác minh, ví dụ:

```json
{
  "op": "This quarter",
  "field": "<REPORT_FIELD_ID>",
  "isPinned": false,
  "params": null,
  "fieldType": "date_time"
}
```

Đây không phải catalog đầy đủ. Operator và `params` phụ thuộc data type. Không tự sáng tác operator; chỉ dùng operator và shape đã được Public API contract hoặc response thực tế của workspace xác nhận. Nếu chưa xác nhận được, dừng trước mutation và báo phần contract còn thiếu.

Quy tắc logic:

- Không có filter: `filterItems: []`, `logicSequence: ""`.
- Có filter nhưng không có logic tùy chỉnh: dùng `1 AND 2 AND ...`.
- Logic tùy chỉnh: service `200` dùng `filter_type: 3` và `logic_sequence` khớp đúng chỉ số item.

Saved relation filter:

```json
{
  "objectId": "<MAIN_OBJECT_ID>",
  "filterItems": [],
  "op": "with",
  "param": "<MAIN_FIELD_ID>-<REF_OBJECT_ID>"
}
```

Chuyển thành `service 200.cross_filters`:

```json
{
  "main_object": "<MAIN_OBJECT_ID>",
  "main_field_id": "<MAIN_FIELD_ID>",
  "ref_object": "<REF_OBJECT_ID>",
  "type": "with",
  "filters": []
}
```

`type` chỉ là `with` hoặc `without`. Không thêm relation filter nếu Report Type chưa có relation tương ứng hoặc `param` chưa được Public API xác nhận.

## Sort, cutoff và view

Saved sort là mảng map:

```json
[
  {
    "<REPORT_FIELD_ID>": {
      "key": "<REPORT_FIELD_ID>",
      "order": "desc",
      "operation": "sum"
    }
  }
]
```

Service `200` nhận mảng phẳng `{key, order, operation?}`. Khi key saved setting có suffix aggregate như `__sum`, loại suffix trước request.

Không đoán key sort của summary/row formula từ slug. Chỉ sort formula khi key và wire shape đã được Public API contract hoặc response hiện tại xác nhận.

Cutoff/top-N:

```json
{
  "isCutoffRecord": true,
  "cutoffRecordConfig": { "key": "<GROUP_OR_METRIC_FIELD_ID>", "limit": 10 }
}
```

Chỉ dùng cutoff khi có group row và key hợp lệ. `viewConfig.showDetailRow: false` ẩn detail row cho báo cáo tổng hợp; giữ `{}` nếu không có yêu cầu.

## Formula

Row formula:

- Cần ít nhất một display field.
- Không dùng cùng group column.
- Tối đa 1.

Summary formula:

- Cần group row và display field.
- Không dùng cùng group column.
- Tối đa 5.

Shape điển hình:

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

`return_type`: `0` number, `1` currency, `2` percent. `formula_return_type`: `0` number, `1` text. Không giả định variable name hoặc formula context từ ví dụ; gọi service `246` và validate schema trước khi lưu.

## Chuyển setting thành service 200

Dùng Report Type ID trong `service 200.report_id` cho preview/final run; saved report ID chỉ dùng cho detail/update saved report.

Payload preview/final run:

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

Transform bắt buộc:

1. `fields` = union có thứ tự của display, group column và group row; loại rỗng/trùng.
2. `group_type_map` chỉ dùng để đổi ID trong `group_rows/group_columns` trước request.
3. `aggregates` map → mảng `{id,operations}` và chỉ giữ field hợp lệ.
4. `relationFilterItems` → `cross_filters` như trên.
5. `isCutoffRecord` → `rows_limit`; bỏ khi false.
6. Saved `sorts` map → list phẳng.
7. Dùng `filter_type: 3` khi có custom `logic_sequence`; nếu không dùng 1/2 đúng semantics.

Trong service `200`, `setting: true` là cờ chạy đồng bộ, không phải saved setting object. Kết quả chờ có thể dùng `r != 0`/HTTP `400`; chỉ theo cơ chế async mà response hiện tại chứng minh.

## Các mẫu cấu hình

### Danh sách chi tiết

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

### Count theo dimension

```json
{
  "displayFieldIds": [{ "data": "<RECORD_KEY_FIELD>" }],
  "groupByRows": ["<DIMENSION_FIELD>"],
  "groupByColumns": [],
  "aggregates": { "<RECORD_KEY_FIELD>": ["count"] },
  "viewConfig": { "showDetailRow": false }
}
```

### Tổng theo tháng

```json
{
  "displayFieldIds": [{ "data": "<AMOUNT_FIELD>" }],
  "groupByRows": ["<DATE_FIELD>"],
  "groupByColumns": [],
  "groupTypeMap": { "<DATE_FIELD>": "month" },
  "aggregates": { "<AMOUNT_FIELD>": ["sum"] },
  "viewConfig": { "showDetailRow": false }
}
```

### Pivot theo dimension và tháng

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

- Mọi ID là report field thuộc Report Type hiện tại.
- Display/group không trùng nhau.
- Mỗi group array không quá 2; group column có group row.
- Aggregate đúng data type và không làm sai grain/cardinality.
- Date grouping chỉ dùng date/date_time field đang group.
- Filter operator/params đến từ Public API contract hoặc response đã xác minh.
- Formula đã evaluate và slug không trùng.
- `folder_id`/`acl` được giữ khi update.
- Service `229` hydrate lại đúng setting.
- Service `200` dùng Report Type ID.
- Service `200` trả rows/summary đúng tiêu chí nghiệm thu.
