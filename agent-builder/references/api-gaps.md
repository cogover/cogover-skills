# API cần bổ sung khi tác vụ phụ thuộc

Đây là các khoảng trống của **tài liệu skill hiện tại**, không phải kết luận nền tảng không có API. Đọc metadata và response API đã được tài liệu hỗ trợ trước; chỉ xin phần còn thiếu cho tác vụ thực tế. Không mở trình duyệt, dò endpoint hoặc đọc source riêng để lấp khoảng trống.

| Nhu cầu | Contract cần người dùng cung cấp | Phần vẫn có thể thực hiện |
|---|---|---|
| Tạo/sửa HTTP Tool có tham số động | Endpoint hoặc service khai báo/đọc parameter schema; vị trí field trong payload; kiểu, required, default và mapping tham số vào path/query/header/body; ví dụ request/response | List/read Tool, tái sử dụng Tool có schema đã được xác minh; cấu hình Agent/Skill độc lập |
| Rà soát nội dung Data sau chuyển đổi trước khi duyệt | Field/endpoint lấy đầy đủ bản chuyển đổi; định dạng, phân trang hoặc tải nội dung và quyền đọc | Upload, tạo file, chuyển đổi và theo dõi trạng thái; dừng bước duyệt phụ thuộc rà soát |
| Chẩn đoán conversion/index lỗi khi response hiện có không đủ | Field/endpoint chi tiết lỗi/trạng thái tác vụ, mã lỗi và cách liên kết với file ID | Theo dõi trạng thái qua service 73; báo chưa index thành công |
| Đọc lại kết quả sau mất WebSocket hoặc xem lịch sử test | API lịch sử tin nhắn/trạng thái lượt hoặc replay, tham số session/conversation/turn/cursor, phân trang và thứ tự sự kiện | Test qua socket đang kết nối; giữ ID đã có, không tự gửi lại tin để đoán kết quả |

Các thiếu hụt tùy Workspace khác cần báo theo dữ liệu thực tế: metadata model/reasoning không đủ ràng buộc; Tool category/type chưa có schema; sự kiện thiếu trường để xác định lượt hoặc xác minh tool/nguồn RAG. Chỉ nêu trường hoặc thao tác còn thiếu, không khẳng định toàn bộ API tương ứng chưa có.

## Cách báo thiếu API

Báo ngắn: “Đang cần **[thao tác]** để hoàn tất **[bước/kết quả]**. Tài liệu/API hiện có **[phần đã biết]**, còn thiếu **[endpoint hoặc schema cụ thể]**. Vui lòng cung cấp method/path hoặc mã service, request/response mẫu đã ẩn danh và quy định xác thực/quyền. Tôi đã hoàn tất **[phần độc lập]**; **[phần phụ thuộc]** chưa được thực hiện/xác minh.”

Không yêu cầu token/cookie, HAR thô, dữ liệu thật hoặc source riêng. Không xin lại API tạo/gửi chat (10/11), duyệt Tool (12), hủy lượt (13), index (20), hay các thao tác cấu hình đã có chỉ vì script probe chưa tự động hóa chúng. Thiếu thư viện client là vấn đề môi trường; lỗi xác thực/quyền xử lý theo skill xác thực và quyền, không gọi đó là thiếu API.
