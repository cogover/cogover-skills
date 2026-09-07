# Personnels API — ghi chú cho `user-permission`

Nguồn rút gọn từ tài liệu Authorization Server. Dùng API này để resolve Personnel và đọc/thiết lập quan hệ Department–Position; không dùng Object `personnel` hoặc `department_personnel` qua `object-record` cho các tác vụ này.

## Endpoints cần dùng

| Mục đích | Method và path |
|---|---|
| Liệt kê/tìm kiếm | `POST /bapi/v1/personnels/list` |
| Xem chi tiết và quan hệ tổ chức | `POST /bapi/v1/personnels/view` |
| Tạo | `POST /bapi/v1/personnels` |
| Cập nhật | `PUT /bapi/v1/personnels/{id}` |
| Xoá | `POST /bapi/v1/personnels/delete` |
| Thêm/sửa/gỡ quan hệ Department–Position | `POST /bapi/v1/personnels/departmentPosition` |

## Resolve Personnel

Dùng list để tìm ứng viên theo ID, tên/full name, trạng thái, Role, Department hoặc Position. Endpoint không có filter email riêng; nếu đầu vào là email, dùng các filter được hỗ trợ để thu hẹp rồi đối chiếu chính xác với `emails` trong từng kết quả và phân trang tiếp nếu cần. Khớp chính xác với workspace user/account đích, sau đó gọi view để lấy dữ liệu mới nhất.

```json
{
  "full_name": "Nguyen An",
  "status": "ACTIVE",
  "page": 1,
  "limit": 50
}
```

```json
{
  "id": "{PERSONNEL_ID}"
}
```

Từ response view, lưu các quan hệ hiện tại và ID của từng quan hệ trước khi cập nhật. Đối chiếu ít nhất Personnel ID, Department ID, Position ID, `is_primary`, `level` và relation ID. Đồng thời đối chiếu email/account với Users API; workspace user ID, `account_id` và Personnel ID là các định danh khác nhau.

## Thiết lập Department–Position

Endpoint nhận mảng `data`. Ví dụ thêm một quan hệ:

```json
{
  "data": [
    {
      "personnel_id": "{PERSONNEL_ID}",
      "department_id": "{DEPARTMENT_ID}",
      "position_id": "{POSITION_ID}",
      "level": 1,
      "is_primary": true,
      "deleted": false
    }
  ]
}
```

Khi sửa hoặc xoá một quan hệ đã có, gửi đúng `id` của quan hệ. Gỡ quan hệ bằng `deleted: true`; không xoá Personnel, Department hoặc Position.

```json
{
  "data": [
    {
      "id": "{RELATION_ID}",
      "personnel_id": "{PERSONNEL_ID}",
      "department_id": "{DEPARTMENT_ID}",
      "position_id": "{POSITION_ID}",
      "level": 1,
      "is_primary": false,
      "deleted": true
    }
  ]
}
```

Không gửi cùng một Personnel nhiều lần cho cùng một Department trong một request. Resolve Department/Position bằng API riêng và kiểm tra Position hợp lệ cho Department trước khi ghi.

## Quy trình an toàn khi dựng persona test

1. Gọi `personnels/view` và lưu snapshot quan hệ ban đầu.
2. Xác nhận thay đổi với người dùng nếu cần sửa dữ liệu nhân sự.
3. Gọi `departmentPosition` bằng credential quản trị/kiểm soát.
4. Gọi lại `personnels/view`; chỉ dùng API key của Personnel để test records sau khi quan hệ đã khớp.
5. Sau khi cleanup records, gỡ relation mới bằng `deleted: true` hoặc khôi phục relation đã sửa theo snapshot.
6. Gọi lại `personnels/view` và so sánh với snapshot. Báo rõ mọi sai khác không phục hồi được.

Không tạo/xoá Personnel chỉ để kiểm thử quyền nếu người dùng không yêu cầu rõ.
