# Kiểm tra Formula trước khi lưu

Sau khi viết hoặc sửa `script` của field `formula`, thực hiện đúng thứ tự sau trước khi gọi `POST /bapi/v1/object-fields` hoặc `PUT /bapi/v1/object-fields/{fieldId}`:

1. Dùng `$cogover-api-auth` đổi API Key thành phiên Web App hợp lệ.
2. Gọi API kiểm tra cú pháp và metadata Formula.
3. Chọn một record có thật thuộc đúng Object rồi gọi API chạy thử Formula trên record đó.
4. Chỉ lưu field khi đủ [điều kiện được phép lưu](#điều-kiện-được-phép-lưu).

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
