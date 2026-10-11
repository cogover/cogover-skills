# Users API

Đọc tài liệu này trước khi xem, mời hoặc xoá user khỏi Workspace. Tất cả endpoint dùng Bearer token và JSON body.

## Endpoint

| Thao tác | Method | Endpoint | Thành công |
|---|---|---|---|
| Danh sách | `POST` | `/bapi/v1/users/list` | `200`, `r: 0` |
| Chi tiết | `POST` | `/bapi/v1/users/view` | `200`, `r: 0` |
| Mời user | `POST` | `/bapi/v1/users` | `201`, `r: 0` |
| Cập nhật hồ sơ | `PUT` | `/bapi/v1/users/{user_id}` | `200`, `r: 0` |
| Xoá khỏi Workspace | `POST` | `/bapi/v1/users/delete` | `200`, `r: 0` |

## Danh sách và resolve user

```json
{
  "page": 1,
  "limit": 20,
  "status": "ACTIVE,INVITED",
  "search": "an@example.com",
  "order": "last_join_time",
  "sort": "desc"
}
```

- `limit` tối đa `100`.
- `search` tìm gần đúng theo tên hoặc email; kiểm tra `account_email` khớp chính xác trước thao tác ghi.
- Trạng thái hợp lệ: `ACTIVE`, `SUSPENDED`, `INVITED`, `DEACTIVATED`. Dùng `INVITED`, không dùng `INVITE`.
- Hỗ trợ lọc `role`, `department`, `position`, `department_ids`, `position_ids`, `license`, `ids` và `ignore_ids` bằng chuỗi phân tách dấu phẩy.
- Dùng `meta.search_after` làm JSON string cho trang tiếp theo và giữ nguyên bộ lọc/sắp xếp.

Xem chi tiết:

```json
{
  "id": "USR000000001"
}
```

`data.id` là workspace user ID dùng cho API user và `roles/addAccount`/`roles/removeAccount`.

## Mời user

```json
{
  "account_email": "an@example.com",
  "first_name": "An",
  "last_name": "Nguyễn Văn",
  "license": "FULL",
  "role": ["RO0000000001"],
  "_jobs": [
    {
      "department_id": "DEP000000001",
      "position_id": "POS000000003",
      "is_primary": true
    }
  ],
  "_apps": []
}
```

Quy tắc:

- Bắt buộc `account_email`, `first_name`, `license` và `role` có ít nhất một Role ID có thể gán.
- Email tối đa 100 ký tự, hợp lệ và chưa có trong Workspace.
- `_jobs` là tuỳ chọn; mỗi phần tử cần department và position cùng Workspace.
- Lời mời có hiệu lực 24 giờ. Không gọi lại create để gửi lại lời mời còn hiệu lực.
- Response thành công trả user có `status: "INVITED"`.

## Cập nhật hồ sơ

```json
{
  "first_name": "An",
  "last_name": "Nguyễn",
  "phone_numbers": ["0901234567"]
}
```

- `first_name` phải có trong mọi request cập nhật.
- `account_email` không thể đổi qua endpoint này.
- Response update là object rút gọn và `status` có thể là `null`; luôn gọi `users/view` để xác minh.
- Gán/gỡ Role không dùng endpoint update user; dùng Roles API.

## Xoá khỏi Workspace

```json
{
  "workspace_account_ids": ["USR000000001"],
  "is_delete_personnel": false
}
```

- `false`: xoá quyền truy cập Workspace, giữ hồ sơ liên quan. Chọn giá trị này khi người dùng chỉ yêu cầu “xoá khỏi Workspace”.
- `true`: đánh dấu xoá cả hồ sơ; có thể vẫn xem được bằng ID cũ với `status: "DELETED"` và `deleted: 1`.
- Không thể xoá chính user đang gọi API hoặc quản trị viên cao nhất cuối cùng.

## Trường và lỗi quan trọng

- User resource dùng snake_case. `role` có thể là array, string hoặc `null`; chuẩn hoá trước khi đối chiếu.
- Timestamps dùng milliseconds.
- Lỗi mời thường nằm trong `meta.account_email`: `unique`, `suspended`, `inactive`, `deactivated`.
- HTTP `400`: validation/nghiệp vụ; `401`: token; `429`: rate limit; `500`: server.

