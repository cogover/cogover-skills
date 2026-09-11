# Departments API — ghi chú cho `user-permission`

Dùng API này để resolve hoặc quản lý phòng ban; không đọc Object `department` qua `object-record` cho mục đích này.

## Endpoints cần dùng

| Mục đích | Method và path |
|---|---|
| Liệt kê/tìm kiếm | `POST /bapi/v1/departments/list` |
| Xem chi tiết | `POST /bapi/v1/departments/view` |
| Tạo | `POST /bapi/v1/departments` |
| Cập nhật | `PUT /bapi/v1/departments/{id}` |
| Xoá/di chuyển dữ liệu | `POST /bapi/v1/departments/delete` |

## Resolve phòng ban

Tìm ứng viên bằng endpoint list, sau đó luôn đọc lại ứng viên đã chọn bằng endpoint view.

```json
{
  "name": "Customer Service",
  "is_active": 1,
  "type": "list",
  "page": 1,
  "limit": 50
}
```

Các filter hữu ích gồm `ids`, `name`, `is_active`, `hierarchy_id` và `sub_level`. `type` có thể là `list`, `tree` hoặc `group`; dùng `tree` khi phải xác minh quan hệ cha/con hoặc phạm vi phòng ban con.

```json
{
  "id": "{DEPARTMENT_ID}"
}
```

Không chọn theo tên gần đúng nếu có nhiều kết quả. Đối chiếu trạng thái active, parent/hierarchy và ID trước khi dùng Department trong `personnelFilters` hoặc gán cho Personnel.

## Ghi dữ liệu

Payload tạo phòng ban có tên đa ngôn ngữ, `parent_id`, `is_active` và có thể có managers. Update là partial update theo ID trên URL. Không tạo hoặc sửa phòng ban chỉ để kiểm thử quyền nếu người dùng chưa yêu cầu rõ.

Endpoint delete có các chế độ xử lý dữ liệu/phòng ban đích. Đây là thao tác có ảnh hưởng rộng; không dùng để dọn quan hệ Personnel tạm. Muốn gỡ Personnel khỏi phòng ban, dùng Personnels API `departmentPosition`.

Sau mọi thay đổi, gọi `departments/view` để xác minh trạng thái thực tế.
