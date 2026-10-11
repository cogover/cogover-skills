# Dashboard model

Cấu trúc `components[]` và `filterData[]` trong payload create/update ([Create và update](api-contract.md#create-và-update)).

## Dashboard component

Envelope của mỗi phần tử `components`:

```json
{
  "chartId": "UUID",
  "type": 1,
  "location": { "i": "UUID", "x": 0, "y": 0, "w": 2, "h": 2, "minW": 2, "minH": 2 },
  "config": {
    "chartId": "UUID",
    "type": 1,
    "location": { "i": "UUID", "x": 0, "y": 0, "w": 2, "h": 2, "minW": 2, "minH": 2 }
  }
}
```

- `chartId`, `location.i` và `config.chartId` phải cùng một định danh; component mới dùng UUID mới.
- Component đã lưu có thể có `id` và `slug`: giữ nguyên khi update.
- `type`: `1` Text, `2` Image, `3` Table, `4` Vertical bar, `5` Horizontal bar, `6` Stacked vertical bar, `7` Stacked horizontal bar, `8` Pie, `9` Line, `10` Scattered, `11` Metric, `12` Gauge, `13` Funnel, `14` Formula metric. Type `10` chưa có create contract trong skill: không tạo khi chưa có config thực tế từ một component đang chạy.

## Layout

- `i` bằng `chartId`; `x`, `y` nguyên không âm; `w`, `h` nguyên dương; `x + w` không vượt `layoutSize`.
- Kích thước tối thiểu: text/image khoảng `2x2`; metric width `2`, height phụ thuộc title/footer/comparison (xem [Lỗi hiển thị đã gặp](#lỗi-hiển-thị-đã-gặp)); gauge width `3`, height phụ thuộc title/footer; chart report-backed khác `4x8`.
- Khi update, giữ layout key chưa biết như `static`, `moved`, `minW`, `minH`.

## Report-backed charts

Type `3`–`13` thường tham chiếu saved report bằng `reportId`; field trong axis/measure/group phải là report field/aggregate key mà saved report thực tế trả về. Config có nhiều key hiển thị bắt buộc phụ thuộc phiên bản: clone component cùng type đang chạy đúng theo bước 3 của `SKILL.md` thay vì tự dựng.

Key chung:

```json
{
  "reportId": "SAVED_REPORT_ID_OR_SUPPORTED_IDENTIFIER",
  "useChartOfReport": false,
  "applyDashboardFilter": true,
  "filtersReplace": {},
  "filterId": null,
  "logicSequence": "",
  "filterItems": [],
  "relationFilterItems": [],
  "isCutoffRecord": false,
  "sortFields": [],
  "title": "",
  "footer": ""
}
```

Key đặc thù theo type:

- Vertical bar, line: `xAxis[]`, `yAxis[]`; horizontal bar: `yAxis[]`, `xAxis[]`; stacked bar thêm `xAxisStackedBarGroupField` hoặc `yAxisStackedBarGroupField`.
- Pie, funnel: `measurementIndex`, `group`, `maxGroupShow`.
- Metric: `metricIndicator`, `maxValueRange`, `defineColorValueRanges`; gauge: `metricIndicator`, `typeScale`, target config.
- Table: `groupByRows`, `groupByColumns`, `groupTypeMap`, `displayFieldIds`, `aggregates`, `viewConfig`, formulas và sorts.
- Formula metric: `sources`, `metaData`, `script`, `return_type`, `allow_zero_if_null`.

## Lỗi hiển thị đã gặp

API không báo lỗi với các trường hợp sau: service đọc lại khớp payload, saved report vẫn chạy đúng. Rà trước khi tạo hoặc sửa component.

| Triệu chứng trên giao diện | Nguyên nhân | Cách làm | Mức chắc chắn |
|---|---|---|---|
| Chart cột hoặc đường có trục 0–1, không có cột | Saved report nguồn có 2 cấp group theo hàng, dữ liệu trả dạng cây | Chart dùng saved report có tối đa 1 group hàng. Cần giữ bản 2 cấp để xem dạng bảng thì tạo thêm saved report tóm tắt 1 cấp trên cùng Report Type cho chart | *đã sửa và chạy đúng* |
| Metric hiện `- - -` dù report có số | Ô quá thấp, chữ số bị cắt | Metric có tiêu đề và footer: `h` từ `5`, `minH` từ `4` (`h: 3` đã bị cắt) | *đã sửa và chạy đúng* |
| Một series luôn bằng 0 hoặc hiện số của series khác | Nhiều aggregate trong cùng chart có field slug là hậu tố của nhau, ví dụ `amount` và `committed_amount` | Tách chart hoặc chọn field có slug không là hậu tố của nhau | *quan sát, cần kiểm chứng* |

## Text và image

Text (`type` `1`) config tối thiểu:

```json
{ "chartId": "UUID", "type": 1, "location": { "i": "UUID", "x": 0, "y": 0, "w": 2, "h": 2 }, "reportId": "", "content": "<p>Inventory overview</p>" }
```

Image (`type` `2`) config:

```json
{ "chartId": "UUID", "type": 2, "location": { "i": "UUID", "x": 0, "y": 0, "w": 2, "h": 2 }, "reportId": "", "file": null, "displayRatio": "original", "tooltip": "", "horizontalAlign": "left", "verticalAlign": "top" }
```

`displayRatio`: `original`, `stretch`, `tile`, `fitWidth`, `fitHeight`. Không tự dựng `file`; dùng file object thực tế từ response file upload của Cogover.

## Dashboard filter

Phần tử `filterData[]`:

```json
{
  "name": "Created date",
  "fieldId": "REPORT_FIELD_ID",
  "fieldType": "DATE_TIME",
  "reportTypeId": "REPORT_TYPE_ID",
  "isDynamic": 0,
  "options": [
    { "name": "This month", "op": "BETWEEN", "params": "[\"...\",\"...\"]" }
  ]
}
```

- `isDynamic` là `0` hoặc `1`, không phải boolean.
- `params` là object/array thì JSON-stringify trước khi lưu.
- Giữ `id` và `dashboard_filter_id` trên filter/options đã tồn tại.
- `fieldId` phải ánh xạ hợp lệ cho các report được áp dụng; dùng `filtersReplace` khi các report dùng report field ID khác nhau.
