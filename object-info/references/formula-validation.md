# Kiểm tra Formula trước khi lưu

Sau khi viết hoặc sửa `script` của field `formula`, thực hiện đúng thứ tự sau trước khi gọi `POST /bapi/v1/object-fields` hoặc `PUT /bapi/v1/object-fields/{fieldId}`:

1. Dùng `$cogover-api-auth` đổi API Key thành phiên Web App hợp lệ.
2. Gọi API kiểm tra cú pháp và metadata Formula.
3. Chọn một record có thật thuộc đúng Object rồi gọi API chạy thử Formula trên record đó.
4. Chỉ lưu field khi đủ [điều kiện được phép lưu](#điều-kiện-được-phép-lưu).

Viết công thức tránh các [bẫy thường gặp](#bẫy-thường-gặp-khi-viết-formula): qua kiểm tra cú pháp chưa đủ, vẫn phải chạy thử trên record thật.

Không tạo được phiên Web App, không có record thử phù hợp, kiểm tra cú pháp thất bại hoặc chạy thử thất bại: dừng trước thao tác lưu và báo rõ cho người dùng; không bỏ qua bước kiểm tra. Hai API dưới đây chỉ kiểm tra/chạy thử, không thay thế API tạo hoặc cập nhật field.

## Phiên Web App

Hai endpoint dùng tiền tố `/api/v1`, không gửi API Key trực tiếp: theo [$cogover-api-auth](../../cogover-api-auth/SKILL.md), gọi `POST /bapi/v1/auth-token` bằng API Key để nhận phiên rồi gửi ba cookie `AuthToken`, `HttpSessionId`, `XSRF-TOKEN` cùng hai header `x-csrf-token` và `x-xsrf-token` bằng đúng cookie `XSRF-TOKEN`, kèm `Content-Type: application/json`. Chỉ gửi ba cookie trên, không thêm cookie Web App khác. Phiên hết hạn hoặc endpoint trả `401`/`403`: chỉ tạo lại phiên, không chuyển sang dùng API Key cho `/api/v1`.

## Kiểm tra cú pháp và metadata

`POST /api/v1/objects/field/validate-formula`. Body dùng schema của request field: `meta_data` là JSON string và `script` nằm bên trong chuỗi đó.

```json
{
  "meta_data": "{\"return_type\":1,\"script\":\"return \\\"OK\\\";\",\"display_html\":false,\"zero_default_value\":true,\"range_date\":false,\"time_zone\":\"{TIME_ZONE}\",\"calculation_mode\":0,\"meta\":{}}",
  "object_type_id": "{OBJECT_TYPE_ID}",
  "type": "formula"
}
```

Thành công khi HTTP `200` và `r: 0`. Khi lỗi, dùng `r`, `msg` và metadata lỗi để sửa công thức.

## Chạy thử trên một record

API chạy thử không phải `validate-formula`. Gọi Record API với service `229`:

```http
POST /api/v1/records
x-req-service: 229
x-req-type: 1
```

`{RECORD_ID}` phải thuộc chính `{OBJECT_TYPE_ID}`. Khác bước kiểm tra cú pháp, `meta_data` ở đây là JSON object:

```json
{
  "id": "{RECORD_ID}",
  "workspace_id": "{WORKSPACE_ID}",
  "object_type": "{OBJECT_TYPE_ID}",
  "time_zone": "{TIME_ZONE}",
  "meta_data": {"return_type": 1, "script": "return \"OK\";", "display_html": false, "zero_default_value": true, "range_date": false, "calculation_mode": 0, "meta": {}}
}
```

Response được bọc theo service envelope: thành công khi HTTP `200` và `body.r` bằng `0`; kết quả tại `body.data.result`, `body.data.params` có thể chứa các field/giá trị record mà Formula đã dùng.

```json
{"body": {"r": 0, "msg": "OK", "data": {"result": "OK", "params": {}}}}
```

Đối chiếu kiểu và ý nghĩa của `result` với `return_type`; API thành công nhưng kết quả sai nghiệp vụ vẫn là kiểm tra thất bại.

## Điều kiện được phép lưu

Chỉ gọi API tạo/cập nhật field khi ghi nhận đủ:

- Kiểm tra cú pháp: HTTP `200`, `r: 0`.
- Chạy thử: HTTP `200`, `body.r: 0`; record thử thuộc đúng Object; `body.data.result` đúng kiểu trả về và phù hợp kỳ vọng nghiệp vụ.
- `meta_data` dùng khi lưu giống nội dung đã kiểm tra; sửa `script`, `return_type` hoặc metadata sau kiểm tra thì chạy lại cả hai bước.

Sau khi lưu vẫn đọc lại field qua Object list API và đối chiếu metadata đã lưu; kiểm tra trước khi lưu không thay thế xác minh sau khi lưu.

## Bẫy thường gặp khi viết Formula

Các dòng dưới *đã sửa và chạy đúng* qua API kiểm tra cú pháp và chạy thử, trừ dòng ghi khác.

| Bẫy | Triệu chứng | Cách viết đúng |
|---|---|---|
| Thiếu khoảng trắng trước `$` sau toán tử | `error_type 20010`, `detail "=$"` | `var amount = $record.amount;`, không viết `var amount=$record.amount;` |
| `!` đặt ngay trước `$record` | `error_type 20010`, `detail "!$"` | `$record.is_paid == false` hoặc gán biến rồi phủ định |
| Tham chiếu field thiếu tiền tố | `error_type 20012`, `is_undefined` | Luôn viết `$record.<slug>` |
| Đi qua lookup trống | Chạy thử trả `r: 20001`, `Result is null` | Kiểm tra null từng cấp: `var contact = $record.contact; if (contact == null) { return ""; }` |
| Nhánh trả `null` | Nơi dùng nhận "null" hoặc lỗi | Mọi nhánh trả giá trị khớp `return_type`: `""` cho text, `0` cho số |
| Field ngày trống khi `zero_default_value: true` | Đọc thành 01/01/1970 | Coi là trống khi `getYear() <= 1970` trước khi định dạng hoặc so sánh |
| Kết quả Boolean dùng ở nơi cần số (gateway Process, rollup) | Lỗi ép kiểu khi chạy | Trả `1`/`0` với `return_type: 2` |
| Formula text trả chuỗi chỉ gồm chữ số và dấu chấm | Bị đọc thành số: `"600.000"` thành `600`, mã mất số 0 đầu | Kèm chữ hoặc đơn vị (`Number.format(v, ".", ",", 0) + " VND"`); mã có số 0 đầu lưu ở field `short_text`, không tạo bằng formula, xem [$create-cogover-objects](../../create-cogover-objects/SKILL.md#quy-tắc) |
| Formula đã kèm đơn vị, nội dung hiển thị lại in thêm đơn vị | "VND VND" | Chỉ một nơi thêm đơn vị; field formula hiển thị nên trả sẵn chuỗi hoàn chỉnh |
| Method không có trong tài liệu (`getSelectedSlugs()`, `.length()`…) | Không chạy được | Dùng `size()`, `isEmpty()` và API trong [Cogover Scripting API Reference](cogover-scripting-api-vi.md) |
| `Math.round(x)` một tham số | Không chạy được | `Math.round(x, 0)`; tài liệu chỉ mô tả `Math.round(n, places)` |

Field lựa chọn của record (*quan sát, cần kiểm chứng*): `containsOptionValue(...)` trên `$record.<field_lựa_chọn>` đã trả `true` cả khi option không được chọn. Kiểm tra lựa chọn bằng `getSelectedOptions()` và so sánh `slug`; mẫu sau *đã sửa và chạy đúng* qua kiểm tra cú pháp và chạy thử:

```javascript
var selected = $record.status.getSelectedOptions();
var isSubmitted = false;
for (var i = 0; i < selected.size(); i++) {
    if (selected.get(i).slug == "submitted") { isSubmitted = true; }
}
return isSubmitted ? 1 : 0;
```

Chưa kiểm chứng, tránh dùng cho tới khi chạy thử được: `Workspace.getInstance()` trong field formula của Object (đã gặp `r: 20000`); đọc field lựa chọn qua lookup (`$record.<lookup>.<field_lựa_chọn>`) bằng so sánh chuỗi.
