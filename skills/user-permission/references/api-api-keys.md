# API Keys API

Đọc tài liệu này trước khi tạo API key tạm để kiểm thử quyền dưới danh tính một user. API key hoạt động bằng quyền hiện tại của tài khoản được chọn tại `accountId`; key không sao chép hay đóng băng quyền tại thời điểm tạo.

## Endpoint

| Thao tác | Method | Endpoint | Thành công |
|---|---|---|---|
| Danh sách | `POST` | `/bapi/v1/api-keys/list` | `200`, `r: 0` |
| Tạo | `POST` | `/bapi/v1/api-keys` | `201`, `r: 0` |
| Tạo alias | `POST` | `/bapi/v1/api-keys/create` | `201`, `r: 0` |
| Cập nhật | `PUT` | `/bapi/v1/api-keys/{apiKeyId}` | `200`, `r: 0` |
| Xoá | `POST` | `/bapi/v1/api-keys/delete` | `200`, `r: 0` |

Credential gọi API phải có quyền xem, tạo/sửa hoặc xoá API Key tương ứng. Workspace được xác định từ credential; không gửi Workspace ID trong body.

## Phân biệt ID

- `accountId` của API key là account ID của active user. Resolve từ `account_id` trong Users API.
- Không dùng workspace user `id`, Personnel record ID, department ID hoặc position ID làm `accountId`.
- Invited user có thể chưa có `account_id`; không tạo key cho user đó cho đến khi tài khoản active.

## Danh sách và xác minh key

```json
{
  "page": 1,
  "limit": 50,
  "id": "AT0000000001",
  "accountId": "AC0000000018",
  "order": "created",
  "sort": "desc"
}
```

Các filter đều không bắt buộc. API danh sách không bao giờ trả lại secret có thể sử dụng.

## Tạo key tạm cho kiểm thử

```json
{
  "name": "codex-permission-test-user-object-unique",
  "description": "Temporary permission verification key; delete after test",
  "isActive": true,
  "expiresOn": 1786185511152,
  "accountId": "AC0000000018"
}
```

Quy tắc dành cho key test:

1. Chỉ tạo sau khi người dùng cho phép rõ và xác nhận user mục tiêu.
2. Đặt tên duy nhất trong Workspace; tên trùng trả `r: 407`.
3. Tính `expiresOn` bằng Unix milliseconds và giới hạn tối đa `now + 172800000` (48 giờ). Không dùng `0` hoặc bỏ thời hạn cho key test.
4. Chọn tài khoản có đúng persona cần kiểm thử; không dùng Super Admin thay thế.
5. Response tạo trả credential đầy đủ đúng một lần:

   ```json
   {
     "r": 0,
     "msg": "Success",
     "data": {
       "id": "AT0000000001",
       "secretToken": "AT0000000001-<one-time-secret>"
     }
   }
   ```

6. Giữ `data.secretToken` trong bộ nhớ ngắn hạn để gọi Records API. Không ghi secret vào file, source, log, URL, báo cáo hoặc câu trả lời. Chỉ lưu metadata không nhạy cảm phục vụ cleanup: key ID, account ID, user, expiry.

## Vô hiệu hoá

```json
{
  "isActive": false,
  "expiresOn": 1786185511152
}
```

Luôn gửi `expiresOn` khi update; nếu bỏ, server hiện tại có thể đặt thành `0` và vô tình biến key thành không hết hạn. Vô hiệu hoá chỉ là fallback khi chưa xoá được key tạm.

## Xoá và cleanup

```json
{
  "id": "AT0000000001"
}
```

- Xoá key là vĩnh viễn. Dùng credential quản trị ban đầu để xoá key test sau khi hoàn tất cleanup records.
- Không để key tự xoá chính nó vì credential sẽ không dùng được cho bước xác minh sau đó.
- Sau delete, gọi list theo ID để xác minh key không còn.
- Không update, disable hoặc delete key do người dùng cung cấp cho phiên test.
- Nếu delete thất bại, update `isActive: false` đồng thời giữ nguyên `expiresOn`, rồi báo key ID và expiry; không báo secret.

## Lỗi thường gặp

| HTTP | `r` | Ý nghĩa |
|---:|---:|---|
| `400` | `10` | Caller thiếu quyền quản lý API Key |
| `400` | `405` | Thiếu hoặc không tìm thấy key ID |
| `400` | `407` | Thiếu tên hoặc tên trùng |
| `400` | `420` | `sort` không hợp lệ |
| `401` | `100001` | Credential sai, inactive hoặc hết hạn |
| `429` | `42900` | Rate limit |

Chỉ coi thao tác thành công khi HTTP status phù hợp và `r: 0`.
