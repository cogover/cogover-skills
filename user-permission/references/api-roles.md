# Roles API

Đọc tài liệu này trước khi xem, tạo, cập nhật, xoá, gán hoặc gỡ Role, và trước mọi yêu cầu cấp quyền qua Role.

## Endpoint

| Thao tác | Method | Endpoint | Thành công |
|---|---|---|---|
| Danh sách | `POST` | `/bapi/v1/roles/list` | `200`, `r: 0` |
| Chi tiết | `POST` | `/bapi/v1/roles/view` | `200`, `r: 0` |
| Tạo | `POST` | `/bapi/v1/roles` | `201`, `r: 0` |
| Cập nhật | `PUT` | `/bapi/v1/roles/{role_id}` | `200`, `r: 0` |
| Xoá | `POST` | `/bapi/v1/roles/delete` | `200`, `r: 0` |
| Gán cho user | `POST` | `/bapi/v1/roles/addAccount` | `200`, `r: 0` |
| Gỡ khỏi user | `POST` | `/bapi/v1/roles/removeAccount` | `200`, `r: 0` |

## Danh sách và chi tiết

Tìm Role theo tên:

```json
{
  "page": 1,
  "limit": 20,
  "name": "Quản lý",
  "nameOperator": "LIKE",
  "roleType": 2,
  "order": "updated",
  "sort": "desc"
}
```

- `roleType: 1` là Role có sẵn; `2` là Role tuỳ chỉnh.
- API danh sách không trả `permissions`, nhưng trả `canAssign`. Chỉ gán/gỡ Role khi danh sách cho biết token được phép quản lý Role đó.
- Dùng `roles/view` để lấy permission đầy đủ:

  ```json
  {
    "id": "RO0000000001"
  }
  ```

- `canAssign` trong response chi tiết có thể là `null`; không dùng giá trị này thay cho danh sách.

## Permission schema

```json
{
  "functionCode": "record",
  "actions": ["view", "edit", "delete"],
  "groupSlug": "object",
  "parent": "",
  "values": [
    {
      "id": "OT00000000008",
      "slug": "ticket"
    }
  ],
  "valueOption": 1
}
```

| Trường | Ý nghĩa |
|---|---|
| `functionCode` | Mã tính năng, ví dụ `record` cho records của Object |
| `actions` | Các action thực sự được cấp, ví dụ `create`, `view`, `edit`, `delete` |
| `groupSlug` | Nhóm quyền; quyền Object thường dùng `object` |
| `parent` | Mã quyền cha nếu có |
| `values` | Phạm vi dữ liệu, thường gồm Object `id` và `slug` |
| `valueOption` | `1`: chỉ values đã chọn; `2`: tất cả trừ values; `3`: tất cả |

Khi `valueOption: 3`, gửi `values: []`. Không suy ra action từ tên hoặc mô tả Role. Không đoán feature `functionCode`; lấy từ Role đã xác nhận trên cùng Workspace.

## Tạo Role

```json
{
  "name": "Vai trò nhân viên chăm sóc khách hàng",
  "description": "Xem/sửa/xoá được bản ghi đối tượng Ticket",
  "permissions": [
    {
      "functionCode": "record",
      "actions": ["view", "edit", "delete"],
      "groupSlug": "object",
      "values": [
        {
          "id": "OT00000000008",
          "slug": "ticket"
        }
      ],
      "valueOption": 1
    }
  ]
}
```

- `name` dài 1–100 ký tự và duy nhất trong Workspace.
- `description` tối đa 500 ký tự.
- `permissions` bắt buộc có ít nhất một phần tử; mảng rỗng bị validation.
- Sau create, lấy Role ID rồi gọi `roles/view` để xác minh.

Snapshot thật của Role Ticket nằm tại [sample-customer-service-role.json](sample-customer-service-role.json). Snapshot có `actions: ["view"]`; payload phía trên minh hoạ trạng thái mong muốn khi yêu cầu thực sự là xem/sửa/xoá.

## Cập nhật Role

```json
{
  "name": "Quản lý bán hàng cấp cao",
  "description": "Mô tả đã cập nhật",
  "permissions": [
    {
      "id": "PER000000005",
      "functionCode": "workspace_account",
      "actions": ["view", "create", "edit", "delete"],
      "groupSlug": "object",
      "values": [],
      "valueOption": 3
    }
  ]
}
```

Quy tắc merge:

- Luôn đọc chi tiết mới nhất trước khi update.
- Luôn gửi `description` để giữ hoặc xoá đúng giá trị (`null` để xoá mô tả).
- Có permission `id`: cập nhật phần tử hiện có và thay thế toàn bộ `values` của phần tử đó.
- Không có `id`: thêm permission mới.
- Có `id` và `status: 0`: xoá permission.
- Không gửi permission hiện có không đồng nghĩa với xoá. Khi không đổi quyền, dùng `permissions: []` theo API.
- Response update có thể chứa tên/mô tả cũ và thiếu permissions; luôn gọi `roles/view` sau update.

## Xoá Role

```json
{
  "ids": ["RO0000000001"]
}
```

Chỉ xoá Role mà token được phép quản lý. Kiểm tra user đang gán Role và ảnh hưởng mất quyền trước khi xoá. Không làm Workspace mất quản trị viên cao nhất cuối cùng.

## Gán và gỡ Role

```json
{
  "roleId": "RO0000000001",
  "userId": "USR000000001"
}
```

- `addAccount` chỉ thêm Role được chỉ định, không thay thế các Role khác; thao tác idempotent nếu Role đã được gán.
- User phải có trạng thái `ACTIVE` hoặc `INVITED`.
- `removeAccount` chỉ gỡ Role được chỉ định và không idempotent. Nếu user không có Role, API trả `meta.accounts: "accounts_not_in_current_role"`.
- Sau add/remove, gọi `users/view` và đối chiếu `role`.

## Lỗi quan trọng

- Tên trùng: `meta.name: "name_exist"`.
- Mã quyền/action không hợp lệ hoặc ID không cùng Workspace: HTTP `400`, `r != 0`.
- HTTP `401`: token; `429`: rate limit; `500`: server.
- Roles API dùng camelCase; Users API dùng snake_case.
