# Kiểm tra Formula trước khi lưu

## Mục lục

- [1. Quy trình bắt buộc](#1-quy-trình-bắt-buộc)
- [2. Xác thực bằng phiên Web App](#2-xác-thực-bằng-phiên-web-app)
- [3. Kiểm tra cú pháp và metadata](#3-kiểm-tra-cú-pháp-và-metadata)
- [4. Chạy thử trên một record](#4-chạy-thử-trên-một-record)
- [5. Điều kiện được phép lưu](#5-điều-kiện-được-phép-lưu)

## 1. Quy trình bắt buộc

Sau khi viết hoặc sửa nội dung `script` của field `formula`, thực hiện đúng thứ tự sau trước khi gọi API tạo/cập nhật field:

1. Dùng `$cogover-api-auth` để đổi API Key thành phiên Web App hợp lệ.
2. Gọi API kiểm tra cú pháp và metadata Formula.
3. Chọn một record có thật thuộc đúng Object rồi gọi API chạy thử Formula trên record đó.
4. Chỉ lưu field khi cả hai request đều thành công và kết quả chạy thử phù hợp với `return_type` cùng yêu cầu nghiệp vụ.

Nếu không tạo được phiên Web App, không có record thử phù hợp, kiểm tra cú pháp thất bại hoặc chạy thử thất bại, dừng trước thao tác lưu và báo rõ cho người dùng. Không bỏ qua bước kiểm tra rồi gọi `POST /bapi/v1/object-fields` hoặc `PUT /bapi/v1/object-fields/{fieldId}`.

Hai API dưới đây chỉ kiểm tra/chạy thử và không thay thế API tạo hoặc cập nhật field.

## 2. Xác thực bằng phiên Web App

Hai endpoint kiểm tra dùng tiền tố `/api/v1`, vì vậy không gửi API Key trực tiếp. Đọc và làm theo `$cogover-api-auth`: gọi `POST /bapi/v1/auth-token` bằng API Key để nhận phiên, sau đó gửi đúng ba cookie:

```http
Cookie: AuthToken={AuthToken}; HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
```

Chỉ gửi ba cookie trên; không thêm cookie Web App khác. Hai header CSRF/XSRF phải cùng bằng cookie `XSRF-TOKEN`.

Không ghi token/cookie thật vào skill, source code, log hay câu trả lời. Mọi ví dụ phải dùng placeholder. Nếu phiên hết hạn hoặc endpoint trả `401`/`403`, chỉ tạo lại phiên theo `$cogover-api-auth`; không thử chuyển sang dùng API Key trực tiếp cho `/api/v1`.

## 3. Kiểm tra cú pháp và metadata

Gọi:

```http
POST /api/v1/objects/field/validate-formula
```

Body dùng schema của request field, trong đó `meta_data` là JSON string và `script` nằm bên trong chuỗi đó:

```json
{
  "meta_data": "{\"return_type\":1,\"script\":\"return \\\"OK\\\";\",\"display_html\":false,\"zero_default_value\":true,\"range_date\":false,\"time_zone\":\"{TIME_ZONE}\",\"calculation_mode\":0,\"meta\":{}}",
  "object_type_id": "{OBJECT_TYPE_ID}",
  "type": "formula"
}
```

Ví dụ cURL an toàn:

```bash
curl --silent --show-error \
  --url 'https://{WORKSPACE_DOMAIN}/api/v1/objects/field/validate-formula' \
  --header 'accept: application/json, text/plain, */*' \
  --header 'content-type: application/json' \
  --cookie 'AuthToken={AuthToken}; HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}' \
  --header 'x-csrf-token: {XSRF-TOKEN}' \
  --header 'x-xsrf-token: {XSRF-TOKEN}' \
  --data-raw '{"meta_data":"{\"return_type\":1,\"script\":\"return \\\"OK\\\";\",\"display_html\":false,\"zero_default_value\":true,\"range_date\":false,\"time_zone\":\"{TIME_ZONE}\",\"calculation_mode\":0,\"meta\":{}}","object_type_id":"{OBJECT_TYPE_ID}","type":"formula"}'
```

Chỉ coi bước này thành công khi HTTP status là `200` và response có `r: 0`. Khi lỗi, giữ lại `r`, `msg` và metadata lỗi để sửa công thức, nhưng không để lộ thông tin phiên.

## 4. Chạy thử trên một record

API chạy thử không phải `/api/v1/objects/field/validate-formula`. Gọi Record API với service `229`:

```http
POST /api/v1/records
x-req-service: 229
x-req-type: 1
```

Chọn `{RECORD_ID}` thuộc chính `{OBJECT_TYPE_ID}`. Body của bước này khác bước kiểm tra cú pháp: `meta_data` là JSON object, không phải JSON string.

```json
{
  "id": "{RECORD_ID}",
  "workspace_id": "{WORKSPACE_ID}",
  "object_type": "{OBJECT_TYPE_ID}",
  "time_zone": "{TIME_ZONE}",
  "meta_data": {
    "return_type": 1,
    "script": "return \"OK\";",
    "display_html": false,
    "zero_default_value": true,
    "range_date": false,
    "calculation_mode": 0,
    "meta": {}
  }
}
```

Ví dụ cURL an toàn:

```bash
curl --silent --show-error \
  --url 'https://{WORKSPACE_DOMAIN}/api/v1/records' \
  --header 'accept: application/json, text/plain, */*' \
  --header 'content-type: application/json' \
  --header 'x-req-service: 229' \
  --header 'x-req-type: 1' \
  --cookie 'AuthToken={AuthToken}; HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}' \
  --header 'x-csrf-token: {XSRF-TOKEN}' \
  --header 'x-xsrf-token: {XSRF-TOKEN}' \
  --data-raw '{"id":"{RECORD_ID}","workspace_id":"{WORKSPACE_ID}","object_type":"{OBJECT_TYPE_ID}","time_zone":"{TIME_ZONE}","meta_data":{"return_type":1,"script":"return \"OK\";","display_html":false,"zero_default_value":true,"range_date":false,"calculation_mode":0,"meta":{}}}'
```

Response được bọc theo service envelope. Chỉ coi bước chạy thử thành công khi HTTP status là `200` và `body.r` bằng `0`. Đọc kết quả tại `body.data.result`; `body.data.params` có thể chứa các field/giá trị record đã được Formula dùng.

```json
{
  "body": {
    "r": 0,
    "msg": "OK",
    "data": {
      "result": "OK",
      "params": {}
    }
  }
}
```

Đối chiếu kiểu và ý nghĩa của `result` với `return_type`. Thành công ở cấp API nhưng kết quả sai nghiệp vụ vẫn phải được xem là kiểm tra thất bại.

## 5. Điều kiện được phép lưu

Chỉ gọi API tạo/cập nhật field sau khi ghi nhận đủ:

- API cú pháp: HTTP `200`, `r: 0`.
- API chạy thử: HTTP `200`, `body.r: 0`.
- Record thử thuộc đúng Object.
- `body.data.result` đúng kiểu trả về và phù hợp kỳ vọng nghiệp vụ.
- `meta_data` dùng khi lưu giống nội dung đã kiểm tra; nếu sửa `script`, `return_type` hoặc metadata sau kiểm tra, chạy lại cả hai bước.

Sau khi lưu, vẫn đọc lại field qua Object list API và đối chiếu metadata đã lưu. Việc kiểm tra trước khi lưu không thay thế bước xác minh sau khi lưu.
