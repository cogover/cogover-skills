# Scheduled Start Event

Scheduled Flow dùng `bpmn2:startEvent` với `renderKey="START_SCHEDULED_EVENT"`. Cấu hình lịch nằm trong `metadata.scheduleRules`.

## Cấu trúc canonical từ front-end

```json
{
  "metadata": {
    "scheduleRules": [
      {
        "triggerInterval": {
          "type": "DAYS",
          "between": 1,
          "atHour": 9,
          "atMinute": 0,
          "atSecond": 0
        },
        "start": null,
        "end": null,
        "maxRun": 0,
        "maxRunTypeFE": "UNLIMITED",
        "id": "SR..."
      }
    ]
  }
}
```

`start` và `end` là timestamp milliseconds hoặc `null`. Front-end chuyển giá trị ngày giờ của form thành timestamp trước khi gửi. Không đưa các field chỉ dùng trên form như `temporaryExecutionHours` hoặc `temporaryExecutionMinutes` vào payload.

## Các chu kỳ được hỗ trợ

| `triggerInterval.type` | Field bổ sung |
|---|---|
| `SECONDS` | `between` |
| `MINUTES` | `between` |
| `HOURS` | `between`, `atMinute`, `atSecond` |
| `DAYS` | `between`, `atHour`, `atMinute`, `atSecond` |
| `WEEKS` | `between`, `daysOfWeek`, `atHour`, `atMinute`, `atSecond` |
| `MONTHS` | `between`, một trong `daysOfMonth` hoặc `daysOfWeek`, cùng `atHour`, `atMinute`, `atSecond` |
| `YEARS` | `between`, `atDays`, `atHour`, `atMinute`, `atSecond` |
| `CRON` | `cronExpression`; không dùng `between` |

### Theo tuần

`daysOfWeek` là mảng số và phải có ít nhất một phần tử:

- `1`: Chủ nhật
- `2`: Thứ hai
- `3`: Thứ ba
- `4`: Thứ tư
- `5`: Thứ năm
- `6`: Thứ sáu
- `7`: Thứ bảy

```json
{
  "type": "WEEKS",
  "between": 2,
  "daysOfWeek": [2, 4, 6],
  "atHour": 10,
  "atMinute": 0,
  "atSecond": 0
}
```

### Theo tháng

Chọn một trong hai cách:

- Ngày tuyệt đối: `daysOfMonth`, ví dụ `["1", "15", "L"]`; `L` là ngày cuối tháng.
- Thứ tương đối trong tháng: `daysOfWeek`, mỗi phần tử có `dayOfWeek` và `nth`; `nth` nhận `"1"`, `"2"`, `"3"`, `"4"` hoặc `"L"`.

```json
{
  "type": "MONTHS",
  "between": 1,
  "daysOfWeek": [
    { "dayOfWeek": 2, "nth": "1" }
  ],
  "atHour": 8,
  "atMinute": 30,
  "atSecond": 0
}
```

### Theo năm

`atDays` phải có ít nhất một phần tử. `month` nằm trong `1..12`; `dayOfMonth` là ngày hợp lệ của tháng đó.

```json
{
  "type": "YEARS",
  "between": 1,
  "atDays": [
    { "month": 1, "dayOfMonth": "15" },
    { "month": 12, "dayOfMonth": "31" }
  ],
  "atHour": 9,
  "atMinute": 0,
  "atSecond": 0
}
```

### Cron tùy chỉnh

```json
{
  "type": "CRON",
  "cronExpression": "0 0 9 ? * MON-FRI"
}
```

Biểu thức dùng Quartz cron có trường giây và có thể có trường năm. Bắt buộc validate cron trước khi POST.

## Số lần chạy

- `maxRunTypeFE: "UNLIMITED"`: đặt `maxRun: 0`.
- `maxRunTypeFE: "CUSTOM"`: `maxRun` là số lần chạy tối đa và bắt buộc có giá trị.
- Không dùng `LIMITED`; đây không phải giá trị front-end hiện hành.

## Tương thích payload cũ

Response hoặc sample cũ có thể chứa các field dẫn xuất như `cron` và `at`. Khi tạo payload mới, ưu tiên các field canonical ở trên. Không sao chép field form-only hoặc field response-only nếu backend không yêu cầu.
