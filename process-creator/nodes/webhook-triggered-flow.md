# Webhook Triggered Flow — Triggered Flow loại `"webhook"`

Quy trình khởi chạy khi hệ thống nhận HTTP POST tới URL webhook của quy trình; body request được parse thành các biến `$flow.input.*` theo `parseToDataType`. Mẫu: `samples/Webhook_triggered_flow.json`.

## Cấu trúc metadata

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

| Trường | Giá trị |
|---|---|
| `type` | BẮT BUỘC `"webhook"` |
| `sampleData` | Chuỗi JSON mẫu của body HTTP request (body mẫu được stringify), dùng để hệ thống hiển thị preview |
| `dataTypeSlug` | Slug duy nhất của data type, format `"TriggeredHookData_<ID>__input"` (ID tự sinh, ví dụ `"TriggeredHookData_THDOP2IR0O5__input"`) |
| `respondTiming` | Thời điểm phản hồi HTTP cho caller: `"IMMEDIATELY"` (mặc định, khuyến nghị); `"WHEN_EXECUTION_COMPLETED"` (sau khi quy trình chạy xong); `"USE_RESPOND_TO_WEBHOOK"` (khi gặp task Respond to Webhook, đọc [response-webhook-task.md](response-webhook-task.md)) |
| `respondBodyType` | Kiểu body trả về khi `respondTiming` khác `"USE_RESPOND_TO_WEBHOOK"`: `"DEFAULT_DATA"` (dữ liệu mặc định); `"TEXT_TEMPLATE"` (nội dung Text Template, cần `documentSampleSlug`); `"REDIRECT_URL"` (chuyển hướng, cần `redirectUrl`) |
| `httpRespondCode` | Resource value `{ "type": 1\|4, "value": ... }`; bắt buộc khi `respondTiming` khác `"USE_RESPOND_TO_WEBHOOK"` |
| `redirectUrl` | Resource value `{ "type": 1\|4, "value": ... }`, chỉ khi `respondBodyType: "REDIRECT_URL"` |
| `documentSampleSlug` | `{ "type": 2, "value": "$flow.<text_template_slug>" }`, chỉ khi `respondBodyType: "TEXT_TEMPLATE"`. KHÔNG dùng `documentSampleId` |
| `verifySignature` / `verifySignatureAllVersions` | `true`/`false`: bật/tắt xác thực chữ ký cho version hiện tại / cho tất cả version |
| `authType` / `authTypeAllVersions` | `"bearer"`, `"apiKey"` hoặc `"basic"` |
| `isAutoGenerate` / `isAutoGenerateAllVersions` | Chỉ áp dụng cho Bearer/API Key: `true` để server sinh secret; `false` thì phải truyền secret do người dùng cung cấp |
| `basicUsername`, `basicPassword` | Bắt buộc khi `verifySignature=true` và `authType="basic"`; `basicUsernameAllVersions`/`basicPasswordAllVersions` bắt buộc khi `verifySignatureAllVersions=true` và `authTypeAllVersions="basic"` |
| Trường server tự sinh | `webhookId`, `webhookIdAllVersions` (ID webhook); `url`, `urlAllVersions` (URL nhận HTTP POST); `secret`, `secretAllVersions` khi bộ tương ứng dùng auto-generate. Không sao chép từ response vào create payload |

## Ma trận xác thực webhook

Hai phạm vi (version hiện tại và tất cả version) dùng cùng quy tắc; thay tên field bằng hậu tố `AllVersions` cho phạm vi thứ hai.

| `verifySignature` | `authType` | Field phải gửi |
|---:|---|---|
| `false` | bỏ qua | Không cần auth credential |
| `true` | `bearer` hoặc `apiKey` | `isAutoGenerate`; nếu `false`, bắt buộc `secret` |
| `true` | `basic` | `basicUsername`, `basicPassword` |

Secret nhập tay: nhận từ kênh credential an toàn và chỉ đặt vào request runtime; không ghi secret thật vào file skill, sample, log hoặc nội dung trả lời.

Ví dụ Basic Authentication cho version hiện tại:

```json
{
  "verifySignature": true,
  "authType": "basic",
  "basicUsername": "<runtime credential>",
  "basicPassword": "<runtime credential>",
  "verifySignatureAllVersions": false
}
```

Ví dụ response bằng Text Template:

```json
{
  "respondTiming": "WHEN_EXECUTION_COMPLETED",
  "respondBodyType": "TEXT_TEMPLATE",
  "httpRespondCode": { "type": 1, "value": 200 },
  "documentSampleSlug": { "type": 2, "value": "$flow.webhook_response_body" }
}
```

## Cấu trúc `parseToDataType`

Schema của dữ liệu đầu vào từ webhook: `nameDataType` luôn là `"input"`; `children` là mảng các trường, mỗi trường mô tả kiểu dữ liệu được parse từ body request.

Trường chung của mỗi child:

- `absoluteSlug`: `$flow.input.<tên_trường>` (ví dụ `$flow.input.text_1`)
- `dataType`: `TEXT`, `NUMBER`, `DATE`, `DATE_TIME`, `FILE`, `URL`, `RECORD`
- `displayOrder`: thứ tự hiển thị, bắt đầu từ 1
- `type`: `1`; `isSystem`: `false`; `actionType`: `""`; `isStandard`: `true`; `parentTable`: `""`
- `isList`: `false` (trường đơn) hoặc `true` (mảng/danh sách, dùng cho `RECORD`)
- `name` và `slug`: trùng với key trong body request
- `absolutePath`: `"Flow / Input / <tên_trường>"`
- `metaDataType`: theo `dataType` (mục dưới)

Ví dụ trường `TEXT`:

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

### `metaDataType` theo `dataType`

Các trường còn lại như ví dụ `TEXT`; chỉ `metaDataType` và field chuyển đổi (`transformationType`, `dateFormat`, bảng dưới) khác nhau:

- `TEXT`: `{ "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" }, "richText": "false" }`
- `NUMBER`: `{ "valueLimit": { "min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note" }, "displayType": 2, "multipleLimit": { "min": 1, "max": 30, "warning": "warning limit note" }, "format": { "format": 2, "type": 1 }, "integralLength": 10, "roundRule": "1", "fractionalLength": 6 }`
- `DATE`: `{ "defaultValueCurrent": false, "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" }, "format": { "format": "dd/MM/yyyy" } }`
- `DATE_TIME`: `{ "defaultValueCurrent": false, "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" }, "timeZone": "Asia/Saigon" }`
- `FILE`: `{ "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" }, "fileGroupType": "file-media", "isPublic": false, "maxSize": 52428800, "isResizable": false, "fileType": ["doc","docx","xlsx","xls","csv","ppt","pptx","pdf","txt","rtf","html","htm","zip","jpg","jpeg","png","svg","gif","bmp","tiff","tif","mp4","avi","mov","wmv","mkv","mp3"] }`
- `URL`: `{ "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" }, "characterLimit": { "min": 0, "max": 2048, "warning": "warning limit note" }, "useDisplayText": false }`
- `RECORD` (mảng object): metadata `TEXT` như trên, kèm cấu trúc riêng ở mục dưới

### Chuyển đổi kiểu (`transformationType`, `dateFormat`)

| Kiểu dữ liệu body | `dataType` | `transformationType` | `dateFormat` |
|---|---|---|---|
| Chuỗi văn bản | `TEXT` | *(không có)* | *(không có)* |
| Số | `NUMBER` | *(không có)* | *(không có)* |
| Mảng object | `RECORD` (`isList: true`) | *(không có)* | *(không có)* |
| Chuỗi ngày (ví dụ `"2026-02-12"`) | `DATE` | `string_to_date` | Format chuỗi ngày trong body (ví dụ `"yyyy-MM-dd"`) |
| Timestamp (long, ví dụ `1772775413`) → Date | `DATE` | `string_to_date` | Giá trị mẫu timestamp dạng chuỗi (ví dụ `"1772775413"`) |
| Chuỗi ngày giờ (ví dụ `"2026-02-12 21:25:50"`) | `DATE_TIME` | `string_to_datetime` | Format chuỗi (ví dụ `"yyyy-MM-dd HH:mm:ss"`) |
| Timestamp milliseconds (ví dụ `1772775413000`) → DateTime | `DATE_TIME` | `long_ms_to_datetime` | `""` |
| Timestamp seconds (ví dụ `1772775413`) → DateTime | `DATE_TIME` | `long_s_to_datetime` | `""` |
| URL file | `FILE` | `url_to_file` (hệ thống tải file từ URL trong body và lưu trữ) | *(không có)* |
| URL | `URL` | *(không có)* | *(không có)* |

Ví dụ trường `DATE` từ chuỗi ngày (các trường khác như `TEXT`):

```json
{
  "absoluteSlug": "$flow.input.dateString",
  "dateFormat": "yyyy-MM-dd",
  "dataType": "DATE",
  "displayOrder": 4,
  "transformationType": "string_to_date",
  "metaDataType": {
    "defaultValueCurrent": false,
    "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" },
    "format": { "format": "dd/MM/yyyy" }
  }
}
```

### Trường `RECORD` (mảng/danh sách object)

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

- `isList`: BẮT BUỘC `true` cho trường mảng; `nameDataType`: tên data type, trùng với `name`.
- `children[].absoluteSlug`: `$flow.input.<tên_mảng>[0].<tên_trường_con>`; `children[].absolutePath`: `"Flow / Input / <tên_mảng>[0] / <tên_trường_con>"`; trường con có cấu trúc giống các trường thông thường (TEXT, NUMBER, v.v.).

## System resources đặc biệt (loại webhook)

Có thêm `$flow.input` với children là các trường trong `parseToDataType.children`; mỗi trường trở thành một resource con của `$flow.input`:

- `absoluteSlug` dùng prefix `$flow.input.` (ví dụ `$flow.input.text_1`).
- `absolutePath` dùng prefix `workflow_resource:list.resource / Input /` (ví dụ `workflow_resource:list.resource / Input / text_1`).
- Trường mảng (RECORD, `isList: true`): children dùng format `$flow.input.<tên_mảng>[0].<tên_trường_con>`.
- KHÁC với loại record: webhook flow KHÔNG có `$flow.input.oldRecord` và `$flow.input.newRecord`; `$flow.input` chứa trực tiếp các trường từ body request.
