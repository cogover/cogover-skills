# Webhook Triggered Flow — Triggered Flow loại `"webhook"`

Khi `type` = `"webhook"`, quy trình sẽ khởi chạy khi hệ thống nhận được HTTP POST request đến URL webhook của quy trình. Dữ liệu trong body request sẽ được parse thành các biến `$flow.input.*` theo cấu hình `parseToDataType`.

## Cấu trúc metadata cho webhook

```json
{
  "metadata": {
    "type": "webhook",
    "sampleData": "<chuỗi JSON mẫu của body request>",
    "dataTypeSlug": "TriggeredHookData_<ID tự sinh>__input",
    "respondTiming": "IMMEDIATELY",
    "respondBodyType": "DEFAULT_DATA",
    "httpRespondCode": { "type": 1, "value": 200 },
    "verifySignature": true,
    "authType": "bearer",
    "isAutoGenerate": true,
    "verifySignatureAllVersions": true,
    "authTypeAllVersions": "bearer",
    "isAutoGenerateAllVersions": true,
    "parseToDataType": {
      "nameDataType": "input",
      "children": [...]
    }
  }
}
```

## Giải thích các trường metadata webhook

- `type`: **BẮT BUỘC** `"webhook"`
- `sampleData`: chuỗi JSON mẫu của body HTTP request — dùng để hệ thống hiển thị preview cho người dùng. Chính là nội dung body request mẫu được stringify
- `dataTypeSlug`: slug duy nhất cho data type, format: `"TriggeredHookData_<ID>__input"` (ID tự sinh, ví dụ: `"TriggeredHookData_THDOP2IR0O5__input"`)
- `respondTiming`: thời điểm hệ thống phản hồi HTTP response cho webhook caller:
  - `"IMMEDIATELY"`: phản hồi ngay lập tức (mặc định, khuyến nghị)
  - `"WHEN_EXECUTION_COMPLETED"`: phản hồi sau khi quy trình chạy xong
  - `"USE_RESPOND_TO_WEBHOOK"`: phản hồi khi gặp task "Respond to Webhook" trong quy trình; đọc `response-webhook-task.md`
- `respondBodyType`: kiểu body trả về khi `respondTiming` khác `"USE_RESPOND_TO_WEBHOOK"`:
  - `"DEFAULT_DATA"`: trả dữ liệu mặc định
  - `"TEXT_TEMPLATE"`: trả nội dung từ Text Template (cần `documentSampleSlug`)
  - `"REDIRECT_URL"`: chuyển hướng (cần `redirectUrl`)
- `httpRespondCode`: resource value dạng `{ "type": 1|4, "value": ... }`; bắt buộc khi `respondTiming` khác `"USE_RESPOND_TO_WEBHOOK"`
- `redirectUrl`: resource value dạng `{ "type": 1|4, "value": ... }`, chỉ dùng khi `respondBodyType` = `"REDIRECT_URL"`
- `documentSampleSlug`: resource value dạng `{ "type": 2, "value": "$flow.<text_template_slug>" }`, chỉ dùng khi `respondBodyType` = `"TEXT_TEMPLATE"`. **Không dùng `documentSampleId`.**
- `verifySignature`: `true`/`false` — bật/tắt xác thực chữ ký cho webhook request hiện tại version
- `verifySignatureAllVersions`: `true`/`false` — bật/tắt xác thực chữ ký cho webhook request tất cả version
- `authType`/`authTypeAllVersions`: `"bearer"`, `"apiKey"` hoặc `"basic"`
- `isAutoGenerate`/`isAutoGenerateAllVersions`: chỉ áp dụng cho Bearer/API Key. `true` để server sinh secret; `false` thì phải truyền secret do người dùng cung cấp
- `basicUsername`/`basicPassword`: bắt buộc khi `verifySignature=true` và `authType="basic"`
- `basicUsernameAllVersions`/`basicPasswordAllVersions`: bắt buộc khi `verifySignatureAllVersions=true` và `authTypeAllVersions="basic"`
- **Các trường tự sinh bởi server** (không sao chép từ response vào create payload):
  - `webhookId`, `webhookIdAllVersions`: ID webhook
  - `url`, `urlAllVersions`: URL webhook để gọi HTTP POST đến
  - `secret`, `secretAllVersions` khi bộ tương ứng dùng auto-generate

## Ma trận xác thực webhook

Hai phạm vi — version hiện tại và tất cả version — dùng cùng quy tắc. Thay tên field bằng hậu tố `AllVersions` cho phạm vi thứ hai.

| `verifySignature` | `authType` | Field phải gửi |
|---:|---|---|
| `false` | bỏ qua | Không cần auth credential |
| `true` | `bearer` hoặc `apiKey` | `isAutoGenerate`; nếu `false`, bắt buộc `secret` |
| `true` | `basic` | `basicUsername`, `basicPassword` |

Không ghi secret thật vào file skill, sample, log hoặc nội dung trả lời. Khi cần secret nhập tay, nhận từ kênh credential an toàn và chỉ đặt vào request runtime.

### Ví dụ Bearer/API Key tự sinh

```json
{
  "verifySignature": true,
  "authType": "bearer",
  "isAutoGenerate": true,
  "verifySignatureAllVersions": true,
  "authTypeAllVersions": "apiKey",
  "isAutoGenerateAllVersions": true
}
```

### Ví dụ Basic Authentication

```json
{
  "verifySignature": true,
  "authType": "basic",
  "basicUsername": "<runtime credential>",
  "basicPassword": "<runtime credential>",
  "verifySignatureAllVersions": false
}
```

### Ví dụ response bằng Text Template

```json
{
  "respondTiming": "WHEN_EXECUTION_COMPLETED",
  "respondBodyType": "TEXT_TEMPLATE",
  "httpRespondCode": { "type": 1, "value": 200 },
  "documentSampleSlug": {
    "type": 2,
    "value": "$flow.webhook_response_body"
  }
}
```

## Cấu trúc `parseToDataType`

Định nghĩa schema cho dữ liệu đầu vào từ webhook:
- `nameDataType`: luôn là `"input"`
- `children`: mảng các trường dữ liệu, mỗi trường là một object mô tả kiểu dữ liệu được parse từ body request

### Các trường chung của mỗi child

- `absoluteSlug`: đường dẫn tuyệt đối, format `$flow.input.<tên_trường>` (ví dụ: `$flow.input.text_1`)
- `dataType`: kiểu dữ liệu (`TEXT`, `NUMBER`, `DATE`, `DATE_TIME`, `FILE`, `URL`, `RECORD`)
- `displayOrder`: thứ tự hiển thị (bắt đầu từ 1)
- `type`: `1`
- `isList`: `false` (trường đơn) hoặc `true` (mảng/danh sách — dùng cho `RECORD`)
- `isSystem`: `false`
- `actionType`: `""`
- `isStandard`: `true`
- `name`: tên trường (trùng với key trong body request)
- `absolutePath`: đường dẫn hiển thị, format `"Flow / Input / <tên_trường>"`
- `parentTable`: `""`
- `slug`: slug của trường (trùng với key trong body request)

### a) Trường TEXT — Cho giá trị chuỗi

```json
{
  "absoluteSlug": "$flow.input.text_1",
  "dataType": "TEXT",
  "displayOrder": 1,
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "",
  "isStandard": true,
  "name": "text_1",
  "absolutePath": "Flow / Input / text_1",
  "metaDataType": {
    "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
    "richText": "false"
  },
  "parentTable": "",
  "slug": "text_1"
}
```

### b) Trường NUMBER — Cho giá trị số

```json
{
  "absoluteSlug": "$flow.input.int_1",
  "dataType": "NUMBER",
  "displayOrder": 2,
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "",
  "isStandard": true,
  "name": "int_1",
  "absolutePath": "Flow / Input / int_1",
  "metaDataType": {
    "valueLimit": { "min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note" },
    "displayType": 2,
    "multipleLimit": { "min": 1, "max": 30, "warning": "warning limit note" },
    "format": { "format": 2, "type": 1 },
    "integralLength": 10,
    "roundRule": "1",
    "fractionalLength": 6
  },
  "parentTable": "",
  "slug": "int_1"
}
```

### c) Trường RECORD (mảng/danh sách) — Cho giá trị mảng object

Dùng `isList: true` và có `children` bên trong:

```json
{
  "absoluteSlug": "$flow.input.array_1",
  "dataType": "RECORD",
  "displayOrder": 3,
  "type": 1,
  "isList": true,
  "isSystem": false,
  "nameDataType": "array_1",
  "actionType": "",
  "isStandard": true,
  "children": [
    {
      "absoluteSlug": "$flow.input.array_1[0].text_2",
      "dataType": "TEXT",
      "displayOrder": 1,
      "type": 1,
      "isList": false,
      "isSystem": false,
      "actionType": "",
      "isStandard": true,
      "name": "text_2",
      "absolutePath": "Flow / Input / array_1[0] / text_2",
      "metaDataType": {
        "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
        "richText": "false"
      },
      "parentTable": "",
      "slug": "text_2"
    }
  ],
  "name": "array_1",
  "absolutePath": "Flow / Input / array_1",
  "metaDataType": {
    "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
    "richText": "false"
  },
  "parentTable": "",
  "slug": "array_1"
}
```

Lưu ý:
- `isList`: **BẮT BUỘC** `true` cho trường mảng
- `nameDataType`: tên data type, trùng với `name`
- `children[].absoluteSlug` dùng format `$flow.input.<tên_mảng>[0].<tên_trường_con>`
- `children[].absolutePath` dùng format `"Flow / Input / <tên_mảng>[0] / <tên_trường_con>"`
- Trường con (`children`) có cấu trúc giống các trường thông thường (TEXT, NUMBER, v.v.)

### d) Trường DATE — Cho giá trị ngày

Có 2 cách chuyển đổi:

**Cách 1: Từ chuỗi ngày (`transformationType: "string_to_date"`)** — Khi giá trị trong body là chuỗi date string (ví dụ: `"2026-02-12"`):

```json
{
  "absoluteSlug": "$flow.input.dateString",
  "dateFormat": "yyyy-MM-dd",
  "dataType": "DATE",
  "displayOrder": 4,
  "transformationType": "string_to_date",
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "",
  "isStandard": true,
  "name": "dateString",
  "absolutePath": "Flow / Input / dateString",
  "metaDataType": {
    "defaultValueCurrent": false,
    "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
    "format": { "format": "dd/MM/yyyy" }
  },
  "parentTable": "",
  "slug": "dateString"
}
```
- `dateFormat`: format của chuỗi ngày trong body request (ví dụ: `"yyyy-MM-dd"`)
- `transformationType`: `"string_to_date"`

**Cách 2: Từ timestamp long (`transformationType: "string_to_date"`)** — Khi giá trị trong body là số timestamp (ví dụ: `1772775413`):

```json
{
  "absoluteSlug": "$flow.input.dateLong",
  "dateFormat": "1772775413",
  "dataType": "DATE",
  "displayOrder": 5,
  "transformationType": "string_to_date",
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "",
  "isStandard": true,
  "name": "dateLong",
  "absolutePath": "Flow / Input / dateLong",
  "metaDataType": {
    "defaultValueCurrent": false,
    "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
    "format": { "format": "dd/MM/yyyy" }
  },
  "parentTable": "",
  "slug": "dateLong"
}
```
- `dateFormat`: giá trị mẫu timestamp (dạng chuỗi)

### e) Trường DATE_TIME — Cho giá trị ngày giờ

Có 3 cách chuyển đổi:

**Cách 1: Từ chuỗi datetime (`transformationType: "string_to_datetime"`)** — Ví dụ: `"2026-02-12 21:25:50"`:

```json
{
  "absoluteSlug": "$flow.input.dateTimeString",
  "dateFormat": "yyyy-MM-dd HH:mm:ss",
  "dataType": "DATE_TIME",
  "displayOrder": 6,
  "transformationType": "string_to_datetime",
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "",
  "isStandard": true,
  "name": "dateTimeString",
  "absolutePath": "Flow / Input / dateTimeString",
  "metaDataType": {
    "defaultValueCurrent": false,
    "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
    "timeZone": "Asia/Saigon"
  },
  "parentTable": "",
  "slug": "dateTimeString"
}
```
- `dateFormat`: format chuỗi datetime (ví dụ: `"yyyy-MM-dd HH:mm:ss"`)
- `transformationType`: `"string_to_datetime"`

**Cách 2: Từ timestamp milliseconds (`transformationType: "long_ms_to_datetime"`)** — Ví dụ: `1772775413000`:

```json
{
  "absoluteSlug": "$flow.input.dateTimeLongMs",
  "dateFormat": "",
  "dataType": "DATE_TIME",
  "displayOrder": 7,
  "transformationType": "long_ms_to_datetime",
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "",
  "isStandard": true,
  "name": "dateTimeLongMs",
  "absolutePath": "Flow / Input / dateTimeLongMs",
  "metaDataType": {
    "defaultValueCurrent": false,
    "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
    "timeZone": "Asia/Saigon"
  },
  "parentTable": "",
  "slug": "dateTimeLongMs"
}
```
- `dateFormat`: `""` (để trống)
- `transformationType`: `"long_ms_to_datetime"`

**Cách 3: Từ timestamp seconds (`transformationType: "long_s_to_datetime"`)** — Ví dụ: `1772775413`:

```json
{
  "absoluteSlug": "$flow.input.dateTimeLongSecond",
  "dateFormat": "",
  "dataType": "DATE_TIME",
  "displayOrder": 8,
  "transformationType": "long_s_to_datetime",
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "",
  "isStandard": true,
  "name": "dateTimeLongSecond",
  "absolutePath": "Flow / Input / dateTimeLongSecond",
  "metaDataType": {
    "defaultValueCurrent": false,
    "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
    "timeZone": "Asia/Saigon"
  },
  "parentTable": "",
  "slug": "dateTimeLongSecond"
}
```
- `dateFormat`: `""` (để trống)
- `transformationType`: `"long_s_to_datetime"`

### f) Trường FILE — Cho giá trị URL file

Hệ thống sẽ tải file từ URL và lưu trữ:

```json
{
  "absoluteSlug": "$flow.input.fileUrl",
  "dataType": "FILE",
  "displayOrder": 9,
  "transformationType": "url_to_file",
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "",
  "isStandard": true,
  "name": "fileUrl",
  "absolutePath": "Flow / Input / fileUrl",
  "metaDataType": {
    "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
    "fileGroupType": "file-media",
    "isPublic": false,
    "maxSize": 52428800,
    "isResizable": false,
    "fileType": ["doc","docx","xlsx","xls","csv","ppt","pptx","pdf","txt","rtf","html","htm","zip","jpg","jpeg","png","svg","gif","bmp","tiff","tif","mp4","avi","mov","wmv","mkv","mp3"]
  },
  "parentTable": "",
  "slug": "fileUrl"
}
```
- `transformationType`: `"url_to_file"` — hệ thống download file từ URL trong body request

### g) Trường URL — Cho giá trị đường dẫn URL

```json
{
  "absoluteSlug": "$flow.input.url",
  "dataType": "URL",
  "displayOrder": 10,
  "type": 1,
  "isList": false,
  "isSystem": false,
  "actionType": "",
  "isStandard": true,
  "name": "url",
  "absolutePath": "Flow / Input / url",
  "metaDataType": {
    "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
    "characterLimit": { "min": 0, "max": 2048, "warning": "warning limit note" },
    "useDisplayText": false
  },
  "parentTable": "",
  "slug": "url"
}
```

## Bảng tổng hợp transformationType

| Kiểu dữ liệu body | `dataType` | `transformationType` | `dateFormat` |
|---|---|---|---|
| Chuỗi văn bản | `TEXT` | *(không có)* | *(không có)* |
| Số | `NUMBER` | *(không có)* | *(không có)* |
| Mảng object | `RECORD` (`isList: true`) | *(không có)* | *(không có)* |
| Chuỗi ngày | `DATE` | `string_to_date` | Format chuỗi (ví dụ: `"yyyy-MM-dd"`) |
| Timestamp (long) → Date | `DATE` | `string_to_date` | Giá trị mẫu timestamp |
| Chuỗi ngày giờ | `DATE_TIME` | `string_to_datetime` | Format chuỗi (ví dụ: `"yyyy-MM-dd HH:mm:ss"`) |
| Timestamp milliseconds → DateTime | `DATE_TIME` | `long_ms_to_datetime` | `""` |
| Timestamp seconds → DateTime | `DATE_TIME` | `long_s_to_datetime` | `""` |
| URL file | `FILE` | `url_to_file` | *(không có)* |
| URL | `URL` | *(không có)* | *(không có)* |

## System resources đặc biệt (loại webhook)

Có thêm `$flow.input` với children là các trường được định nghĩa trong `parseToDataType.children`. Mỗi trường trong `parseToDataType.children` sẽ trở thành một resource con của `$flow.input`:
- `absoluteSlug` trong resources dùng prefix `$flow.input.` (ví dụ: `$flow.input.text_1`)
- `absolutePath` trong resources dùng prefix `workflow_resource:list.resource / Input /` (ví dụ: `workflow_resource:list.resource / Input / text_1`)
- Với trường mảng (RECORD, `isList: true`): children dùng format `$flow.input.<tên_mảng>[0].<tên_trường_con>`
- **KHÁC với loại record:** Webhook flow **KHÔNG** có `$flow.input.oldRecord` và `$flow.input.newRecord`. Thay vào đó, `$flow.input` chứa trực tiếp các trường từ body request

## File mẫu

`samples/Webhook_triggered_flow.json`
