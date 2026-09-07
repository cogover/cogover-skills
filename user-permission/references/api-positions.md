# Positions API — ghi chú cho `user-permission`

Nguồn rút gọn từ tài liệu Authorization Server. Dùng API này để resolve hoặc quản lý vị trí công việc; không đọc Object schema/record để suy đoán Position.

## Endpoints cần dùng

| Mục đích | Method và path |
|---|---|
| Liệt kê/tìm kiếm | `POST /bapi/v1/positions/list` |
| Xem chi tiết | `POST /bapi/v1/positions/view` |
| Tạo | `POST /bapi/v1/positions` |
| Cập nhật | `PUT /bapi/v1/positions/{id}` |
| Xoá | `POST /bapi/v1/positions/delete` |

## Resolve vị trí

Dùng list để tìm theo ID/tên/trạng thái hoặc giới hạn theo phòng ban, rồi gọi view với đúng ID đã chọn.

```json
{
  "name": "Support Agent",
  "is_active": 1,
  "department_ids": ["{DEPARTMENT_ID}"],
  "page": 1,
  "limit": 50
}
```

Các filter hữu ích gồm `id`, `ids`, tên, trạng thái, `department_ids` và `is_department_only`.

```json
{
  "id": "{POSITION_ID}"
}
```

Trước khi gán cho Personnel, xác minh Position active. Nếu `is_department_only` bật, Department đích phải nằm trong `department_ids`; không coi Position cùng tên ở phòng ban khác là tương đương.

## Ghi dữ liệu

Payload tạo Position có tên đa ngôn ngữ, các cờ trạng thái/phạm vi và `department_ids` khi Position chỉ dùng cho một số phòng ban. Update là partial update theo ID trên URL.

Không tạo Position mới chỉ để dựng persona test khi có thể dùng Position hiện hữu. Xoá Position đang được sử dụng có thể cần mapping thay thế và ảnh hưởng nhiều Personnel; không dùng endpoint delete để cleanup quan hệ test. Dùng Personnels API `departmentPosition` để gỡ hoặc phục hồi quan hệ.

Sau create/update, gọi `positions/view` để xác minh cấu hình đã lưu.
