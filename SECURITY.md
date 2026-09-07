# Báo cáo vấn đề bảo mật

Không đăng credential, cookie, token, URL webhook có secret hoặc dữ liệu khách hàng trong GitHub issue/PR công khai.

Nếu repository đã bật **Security → Report a vulnerability**, dùng kênh báo cáo riêng tư đó. Nếu chưa có, liên hệ Cogover qua kênh hỗ trợ riêng đang dùng cho Workspace của bạn và yêu cầu chuyển báo cáo cho người bảo trì bộ skill. Không gửi secret để chứng minh lỗi; chỉ nêu loại thông tin, vị trí file/commit và ví dụ đã che giá trị.

## Khi phát hiện secret

1. Chủ sở hữu xác định và thu hồi/rotate đúng credential hoặc webhook secret bị ảnh hưởng theo cơ chế sản phẩm; xóa khỏi file không vô hiệu hóa secret.
2. Làm sạch working tree, bản cài, artifact, log và lịch sử Git nếu giá trị đã được commit. Phối hợp trước thao tác viết lại lịch sử của repo dùng chung.
3. Kiểm tra lại các blob trong lịch sử, file nhị phân/Office và nội dung mã hóa. Không xác minh token bằng cách gọi một Workspace khi chưa được phép.
4. Công bố bản sửa với mô tả tác động đã ẩn danh và hướng cập nhật; không đưa giá trị bị lộ vào changelog.

Người bảo trì xử lý báo cáo theo khả năng hiện có; tài liệu này không cam kết SLA hoặc chương trình thưởng lỗi. Khi tạo GitHub repository public, bật private vulnerability reporting để cung cấp kênh trực tiếp tại repository.
