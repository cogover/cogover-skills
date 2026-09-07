# Bắt đầu với Custom Module

Custom Module dành cho các nghiệp vụ mà những module có sẵn của Cogover như Cogover Object hoặc Cogover Process chưa đáp ứng đủ. Chúng ta có thể tự viết logic phía server, giao diện riêng, hoặc cả hai mà vẫn sử dụng dữ liệu và quyền của Workspace.

## Chọn loại module

| Loại | Dùng khi | Ví dụ |
|---|---|---|
| **Custom Backend Module** | Cần xử lý nghiệp vụ phía server, đọc/ghi Object, kiểm tra quyền, giữ bí mật tích hợp hoặc cung cấp API riêng. | Tính giá đơn hàng, đồng bộ dữ liệu với hệ thống kế toán, tạo API tổng hợp tồn kho. |
| **Custom Frontend Module** | Cần một màn hình hoặc trải nghiệm riêng nhưng không cần thêm logic server. | Dashboard chỉ đọc từ API có sẵn, biểu mẫu nội bộ, trang báo cáo tùy chỉnh. |
| **Kết hợp Backend + Frontend** | Giao diện cần gọi logic hoặc dữ liệu đã được xử lý riêng ở backend. | Trang CRM tìm 5 Account lâu năm nhất và đánh dấu chúng là `Heritage Account`. |

Không đặt secret trong Custom Frontend Module vì mã frontend được tải xuống trình duyệt. Logic nhạy cảm, quyền nâng cao và credential tích hợp phải nằm ở backend.

## Bắt đầu

1. [Viết Custom Backend Module đầu tiên](./get-started-custom-backend-module.md)
2. [Viết Custom Frontend Module đầu tiên](./get-started-custom-frontend-module.md)
3. [Kết nối frontend và backend](./full-stack-integration.md)
