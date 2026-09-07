# Dashboard model

## Mục lục

- [Dashboard component](#dashboard-component)
- [Chart types](#chart-types)
- [Layout](#layout)
- [Report-backed charts](#report-backed-charts)
- [Text và image](#text-và-image)
- [Dashboard filter](#dashboard-filter)
- [Update an toàn](#update-an-toàn)

## Dashboard component

Mỗi phần tử `components` có envelope:

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

Component đã lưu có thể có `id` và `slug`; giữ nguyên khi update. `chartId`, `location.i` và `config.chartId` phải cùng định danh. Dùng UUID mới cho component mới.

## Chart types

| Value | Loại |
|---:|---|
| `1` | Text |
| `2` | Image |
| `3` | Table |
| `4` | Vertical bar |
| `5` | Horizontal bar |
| `6` | Stacked vertical bar |
| `7` | Stacked horizontal bar |
| `8` | Pie |
| `9` | Line |
| `10` | Scattered; chưa có create contract trong tài liệu skill |
| `11` | Metric |
| `12` | Gauge |
| `13` | Funnel |
| `14` | Formula metric |

Không tạo type `10` nếu chưa có contract thực tế từ một component đang chạy.

## Layout

- `i`: bằng `chartId`.
- `x`, `y`: vị trí nguyên không âm.
- `w`, `h`: kích thước nguyên dương.
- Tổng `x + w` không vượt `layoutSize`.
- Text/image: minimum khoảng `2x2`.
- Metric: minimum width `2`, height phụ thuộc title/footer/comparison.
- Gauge: minimum width `3`, height phụ thuộc title/footer.
- Các chart report-backed khác: minimum `4x8`.

Khi update, giữ các layout key chưa biết như `static`, `moved`, `minW`, `minH`.

## Report-backed charts

Các type `3`–`13` thường tham chiếu saved report bằng `reportId`. Field trong axis/measure/group phải là report field/aggregate key mà saved report thực tế trả về.

Common config keys:

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

Các key đặc thù quan trọng:

- Vertical bar/line: `xAxis[]`, `yAxis[]`.
- Horizontal bar: `yAxis[]`, `xAxis[]`.
- Stacked bar: thêm `xAxisStackedBarGroupField` hoặc `yAxisStackedBarGroupField`.
- Pie/funnel: `measurementIndex`, `group`, `maxGroupShow`.
- Metric: `metricIndicator`, `maxValueRange`, `defineColorValueRanges`.
- Gauge: `metricIndicator`, `typeScale`, target config.
- Table: `groupByRows`, `groupByColumns`, `groupTypeMap`, `displayFieldIds`, `aggregates`, `viewConfig`, formulas và sorts.
- Formula metric: `sources`, `metaData`, `script`, `return_type`, `allow_zero_if_null`.

Các config này có nhiều key hiển thị bắt buộc phụ thuộc phiên bản. Quy trình an toàn:

1. Dùng `$report-builder` để preview saved report.
2. Đọc một component cùng type đang chạy đúng từ API response hoặc dùng contract đóng gói trong skill.
3. Deep-copy config.
4. Chỉ thay report/field/filter/title/palette cần thiết.
5. Giữ key chưa biết.
6. Update dashboard và đọc lại; sau đó mở deep-link chỉ khi người dùng yêu cầu kiểm chứng UI.

## Text và image

Text config tối thiểu:

```json
{
  "chartId": "UUID",
  "type": 1,
  "location": { "i": "UUID", "x": 0, "y": 0, "w": 2, "h": 2 },
  "reportId": "",
  "content": "<p>Inventory overview</p>"
}
```

Image config:

```json
{
  "chartId": "UUID",
  "type": 2,
  "location": { "i": "UUID", "x": 0, "y": 0, "w": 2, "h": 2 },
  "reportId": "",
  "file": null,
  "displayRatio": "original",
  "tooltip": "",
  "horizontalAlign": "left",
  "verticalAlign": "top"
}
```

`displayRatio`: `original`, `stretch`, `tile`, `fitWidth`, `fitHeight`. Không tự dựng `file`; dùng response file upload/Cogover file object thực tế.

## Dashboard filter

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
- Nếu `params` là object/array, JSON-stringify trước khi lưu.
- Giữ `id` và `dashboard_filter_id` trên filter/options đã tồn tại.
- `fieldId` phải ánh xạ hợp lệ cho các report được áp dụng; dùng `filtersReplace` khi các report dùng report field ID khác nhau.

## Update an toàn

1. Đọc detail với `getDetail: true`.
2. Deep-parse JSON string trong response nếu gateway trả serialized JSON.
3. Loại field server-managed ở root.
4. Giữ nguyên `components[].id`, `slug`, config và layout key chưa sửa.
5. Áp patch lên đúng component bằng `chartId`, không theo array index.
6. Validate không trùng `chartId`, layout không vượt grid và report reference tồn tại.
7. Gửi full update payload.
