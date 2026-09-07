# Object History Tracking API Contract

## Mục lục

- [Xác thực](#xác-thực)
- [Resolve Object và fields](#resolve-object-và-fields)
- [Đọc cấu hình](#đọc-cấu-hình)
- [Đọc giới hạn subscription](#đọc-giới-hạn-subscription)
- [Ghi cấu hình](#ghi-cấu-hình)
- [Semantics và lỗi](#semantics-và-lỗi)

Tài liệu này là contract tự đủ cho skill công khai. Chỉ xác minh hành vi bằng endpoint và response được mô tả tại đây; không mở source code, repository, file dự án, test, database, log nội bộ, browser bundle hoặc source map. Nếu contract không bao phủ một trường hợp, báo giới hạn thay vì truy tìm implementation.

## Xác thực

Mọi endpoint cấu hình bên dưới có tiền tố `/api/v1` và bắt buộc dùng phiên Web App. Dùng `$cogover-api-auth`:

1. Gửi API Key Bearer tới `POST /bapi/v1/auth-token` với JSON `{}`.
2. Lấy `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` từ response/cookie.
3. Gửi ba cookie đó tới `/api/v1/...` và đặt cả `x-csrf-token` lẫn `x-xsrf-token` bằng `XSRF-TOKEN`.

Không gửi `Authorization: Bearer {API_KEY}` trực tiếp tới endpoint `/api/v1`.

Các ví dụ dưới đây giả định client đã có cookie jar và biến XSRF trong bộ nhớ. Không ghi token vào file hoặc output.

## Resolve Object và fields

### Request

```http
POST /api/v1/objects/object/get-by-slug
Content-Type: application/json
Cookie: HttpSessionId=...; XSRF-TOKEN=...; AuthToken=...
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
```

Payload đúng luồng History Tracking UI:

```json
{
  "slug": "doi_tuong_a",
  "withFields": 1,
  "withRelatedList": 1,
  "display": true,
  "translate": true,
  "withPersonnelInfo": false,
  "withAllTranslations": false
}
```

Không phụ thuộc `withAllTranslations` để resolve field; dùng `name`, `originalName` và `slug` có trong response.

### Response liên quan

```json
{
  "r": 0,
  "msg": "Success",
  "requestId": "{requestId}",
  "meta": {
    "total": 1,
    "currentPage": 1,
    "lastPage": 1,
    "perPage": 1
  },
  "data": [
    {
      "id": "{objectTypeId}",
      "workspaceId": "{workspaceId}",
      "name": "Đối tượng A",
      "originalName": "Object A",
      "slug": "doi_tuong_a",
      "category": "normal",
      "fields": [
        {
          "id": "{fieldId}",
          "name": "Trạng thái",
          "originalName": "Status",
          "slug": "status",
          "fieldType": "single_choice",
          "status": 1,
          "manualModifyAllow": false,
          "sort": 10
        }
      ]
    }
  ]
}
```

Response thực tế có thêm thuộc tính Object/field. Chỉ phụ thuộc các key trên cho workflow này.

### Quy tắc field hợp lệ

1. Gửi `display: true` và chỉ dùng các field có trong response.
2. Chỉ dùng field có `status: 1` (`Active`).
3. Loại field có `fieldType` là `formula`, `auto_number` hoặc `rollup_summary`.
4. Không loại field chỉ vì `manualModifyAllow: false`.
5. Chỉ thao tác với Object có `category: "normal"`.

Gửi field **slug** vào setting, không gửi field ID hoặc name.

## Đọc cấu hình

### Request

```http
GET /api/v1/objects/history_tracking/setting/{objectSlug}
```

Path hiện hành:

```text
/api/v1/objects/history_tracking/setting/doi_tuong_a
```

URL-encode path segment khi slug đến từ input. Không thêm query/body.

### Có cấu hình

```json
{
  "r": 0,
  "msg": "Success",
  "requestId": "{requestId}",
  "data": {
    "id": "{settingId}",
    "workspaceId": "{workspaceId}",
    "objectTypeId": "{objectTypeId}",
    "objectSlug": "doi_tuong_a",
    "enabled": true,
    "objectHistorySlug": "_history_object_a",
    "fields": ["status", "owner"],
    "createdBy": {
      "id": "{id}",
      "personnelId": "{personnelId}",
      "firstName": "...",
      "lastName": "...",
      "fullName": "...",
      "email": "..."
    },
    "updatedBy": {
      "id": "{id}",
      "personnelId": "{personnelId}",
      "firstName": "...",
      "lastName": "...",
      "fullName": "...",
      "email": "..."
    },
    "created": 1720000000000,
    "updated": 1720000000000
  }
}
```

`createdBy`/`updatedBy` phụ thuộc personnel còn resolve được; không dùng chúng để xác định cấu hình đích.

### Chưa có cấu hình

```json
{
  "r": 0,
  "msg": "Success",
  "requestId": "{requestId}",
  "data": null
}
```

Đây là “chưa tạo setting”, khác với setting đã tồn tại có `enabled: false`.

## Đọc giới hạn subscription

Đọc giới hạn động từ `limits.historyTrackingFieldsPerObject`; giá trị có thể khác nhau theo gói. Không hardcode.

### Request

```http
POST /api/v1/subscription
Content-Type: application/json
```

```json
{
  "service": 217,
  "type": 1,
  "body": {
    "workspace_id": "{workspaceId}",
    "id": "",
    "page": 0,
    "size": 100,
    "active": 1
  }
}
```

Lấy `workspaceId` từ Object response. Response dùng service envelope; giới hạn ở:

```text
body.data.data[0].limits.historyTrackingFieldsPerObject
```

Kiểm tra `body.r == 0`, `body.data.data` có đúng một subscription active phù hợp workspace, và limit là số nguyên không âm. Nếu không đọc được limit, không suy đoán; có thể để server xác thực nhưng phải xử lý `r: 535` mà không làm mất trạng thái.

Envelope thực tế không nhất thiết có `r` ở top-level:

```json
{
  "serviceVersion": 1,
  "service": 217,
  "body": {
    "r": 0,
    "msg": "Success",
    "data": {
      "data": [
        {
          "limits": {
            "historyTrackingFieldsPerObject": 5
          }
        }
      ]
    }
  }
}
```

Đọc mã nghiệp vụ tại `body.r`; không yêu cầu top-level `r` tồn tại.

## Ghi cấu hình

### Request

```http
POST /api/v1/objects/history_tracking/setting/{objectSlug}
Content-Type: application/json
```

```json
{
  "enabled": 1,
  "fields": ["status", "owner"]
}
```

Contract request:

| Key | Kiểu gửi | Bắt buộc | Semantics |
|---|---|---:|---|
| `enabled` | number `0` hoặc `1` | Có | Trạng thái cấp Object; GET trả Boolean |
| `fields` | `string[]` | Có | Toàn bộ field slug được lưu, không phải delta |

Luôn gửi cả hai key và dùng số `0`/`1` cho `enabled`. Key thiếu hoặc `null` có thể bị từ chối thay vì được giữ nguyên.

### Response thành công

```json
{
  "r": 0,
  "msg": "Success",
  "requestId": "{requestId}",
  "data": "{settingId}"
}
```

`data` chỉ là setting ID, không phải full resource. Luôn gọi GET setting để xác minh.

## Semantics và lỗi

- POST là create-or-update theo `(workspace, objectSlug)` và thay cả `enabled` lẫn serialized `fields`.
- Tắt (`enabled: 0`) không tự xoá `fields`, setting, Object history nội bộ hoặc log đã có. Web App tắt bằng cách gửi lại nguyên `fields` hiện tại.
- Bật lần đầu có thể tạo Object history nội bộ; GET sau đó có thể trả `objectHistorySlug`.
- API áp dụng giới hạn cho toàn bộ mảng `fields`, kể cả khi `enabled: 0`. Mọi phần tử, bao gồm duplicate hoặc slug cũ, đều góp vào giới hạn.
- `r: 0` một mình không chứng minh field slug hợp lệ. Luôn resolve và lọc field theo Object schema trước khi ghi.
- API không có partial add/remove. Client phải read-modify-write và chống lost update bằng GET lại ngay trước POST.

Các lỗi nghiệp vụ đã xác nhận:

| HTTP thường gặp | `r` | `msg`/ý nghĩa |
|---:|---:|---|
| 422 | `501` | `Object not found` |
| 422 | `535` | `Exceed history tracking fields per object max limit: {N}` |
| 422 hoặc 500 tùy nhánh lỗi | `700` | `Internal server error` hoặc lỗi nội bộ |

Giữ `requestId` khi báo lỗi. Lỗi auth/CSRF có thể không theo đúng bảng này.
