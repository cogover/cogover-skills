# Dashboard API contract

## Mục lục

- [Endpoint và auth](#endpoint-và-auth)
- [Service dispatch](#service-dispatch)
- [List và detail](#list-và-detail)
- [Create và update](#create-và-update)
- [Delete và duplicate](#delete-và-duplicate)
- [Response và kiểm chứng](#response-và-kiểm-chứng)

## Endpoint và auth

Tất cả operation dùng:

```http
POST /api/v1/dashboard-server
Content-Type: application/json
x-req-type: 9
x-req-service: {service}
Cookie: HttpSessionId=...; XSRF-TOKEN=...; AuthToken=...
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
```

Đây là `/api/v1`, vì vậy phải dùng `$cogover-api-auth` để tạo phiên từ API Key. Không đặt API Key vào `Authorization` của request này.

## Service dispatch

| Service | Operation | Mutation |
|---:|---|---|
| `3` | Create dashboard | Có |
| `4` | Update dashboard | Có |
| `5` | Delete dashboards | Có |
| `6` | List/detail dashboards | Không |
| `20` | Duplicate dashboard | Có |

Không thử service number khác khi server báo lỗi processor.

## List và detail

List chuẩn:

```json
{
  "size": 20,
  "page": 1,
  "filters": [],
  "sorts": [{ "field": "updated", "order": "desc" }]
}
```

Filter shape:

```json
{ "field": "slug", "op": "=", "params": "activity_overview" }
```

Các operator được hỗ trợ gồm `=`, `!=`, `IN`, `NOT IN`, `LIKE`, `BETWEEN`, `>=`, `<=`.

Detail theo slug:

```json
{
  "size": 1,
  "page": 1,
  "getDetail": true,
  "filters": [{ "field": "slug", "op": "=", "params": "activity_overview" }]
}
```

Detail theo ID thay field `slug` bằng `id`. Chỉ chấp nhận đúng một kết quả.

## Create và update

Create tối thiểu cho dashboard trống, service `3`:

```json
{
  "name": "Inventory overview",
  "slug": "inventory_overview",
  "description": "",
  "layoutSize": 12,
  "colorPalette": 1,
  "components": [],
  "filterData": null
}
```

Ràng buộc contract:

- `name`: trim, bắt buộc.
- `slug`: bắt buộc, ít nhất 2 ký tự, tối đa 100; bắt đầu bằng chữ; không có `__`; không kết thúc bằng `_`; chuẩn hoá lowercase trước khi gửi.
- `description`: string, mặc định rỗng.
- `layoutSize`: integer `9` hoặc `12`.
- `colorPalette`: built-in palette number hoặc custom palette ID string tồn tại.
- `components`: array, xem `dashboard-model.md`.
- `filterData`: `null` hoặc array, xem `dashboard-model.md`.

Update dùng service `4` và cùng payload create cộng thêm `id`. Không gửi `created`, `updated`, `createdBy`, `updatedBy`, `workspaceId`.

## Delete và duplicate

Delete bằng service `5`:

```json
{ "ids": ["DA..."] }
```

Duplicate bằng service `20`:

```json
{
  "id": "SOURCE_DASHBOARD_ID",
  "name": "Inventory overview copy",
  "slug": "inventory_overview_copy"
}
```

Duplicate không phải update; backend sao chép component/filter từ source.

## Response và kiểm chứng

Với `x-req-type: 9`, response là nguyên kết quả của service ở root, không bọc `{serviceVersion, service, id, type, body}` như `x-req-type: 6` cũ:

```json
{ "r": 0, "msg": "OK", "data": [], "meta": { "total": 0, "perPage": 20, "currentPage": 1 } }
```

Lỗi cũng trả `r`, `msg` ở root kèm HTTP status khác `200`; số sau `service=` thay đổi theo request:

```json
{ "r": 5001, "msg": "Can not found processor for request: service=<SERVICE_NUMBER>" }
```

| Trường hợp | HTTP | Response |
|---|---:|---|
| Thành công, kể cả list/detail không có kết quả (`data: []`) | `200` | `r: 0` |
| Service không tồn tại | `500` | `r: 5001` |
| Filter theo field không tồn tại | `500` | `r: 5000`, `msg: "Error"` |
| `AuthToken` không hợp lệ | `401` | Header `x-proxy-error: 1`, `r: 2`, `msg: "TOKEN_NOT_VALID"` |
| Cookie phiên hoặc CSRF token không hợp lệ | `400` | `r: 19000`, `msg: "CSRF_TOKEN_NOT_VALID"` |

Kiểm tra HTTP status và `r` ở root; không đọc `response.body`. Thành công chỉ khi HTTP `2xx` và `r` là `0`, sau đó phải đọc lại resource để xác minh; đối chiếu component theo `chartId` vì thứ tự `components` có thể khác giữa các lần đọc. Lỗi phiên xử lý theo `$cogover-api-auth`.
