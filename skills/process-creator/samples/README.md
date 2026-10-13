# Mẫu Process

Các JSON trong thư mục này là fixture minh họa đã ẩn danh. ID có hậu tố số chứa `0000`, UUID mẫu và domain `example.com` không thuộc Workspace sử dụng thực tế. Một ID mẫu được dùng nhất quán ở JSON, JSON string lồng nhau và BPMN XML. Các ID định danh node cục bộ như `Activity_...`, `Flow_...`, `Event_...` chỉ nối các thành phần trong diagram.

Một số mẫu là snapshot response với metadata bổ sung, không phải body có thể POST nguyên trạng. Khi tạo Process, dựng request theo `api-process-builder.md`, resolve Object/field/user và tài nguyên thật của Workspace, bỏ metadata do server quản lý. Không dùng placeholder webhook secret để gọi hoặc kích hoạt webhook.

Chạy kiểm tra hình học từ root repo:

```bash
python3 skills/process-creator/scripts/validate_bpmn_geometry.py skills/process-creator/samples/sample_process_usertask_send_email.json --mode response
```

Mẫu gửi email có tuyến Start → Root → Send Email → End Process. Kết quả kiểm tra server cũ đã được bỏ; file không tuyên bố đã được xác minh runtime cho Workspace đích. Kiểm tra cú pháp/hình học không thay thế validation và kiểm thử nghiệp vụ theo skill, đặc biệt trước khi gửi email, gọi HTTP, tạo record hoặc để AI Agent nhắn cho nhân sự.

Hai mẫu AI Agent dùng ID chứa `EXAMPLE` và placeholder `{AGENT_ID}` trong `actions[].data`:

- `sample_ai_agent.json`: Start → AI Agent → End Process, chỉ gọi agent và đọc output.
- `sample_ai_agent_proactive_chat.json`: Start → AI Agent có `delivery` (người nhận là "Current User", `conversationMode: LATEST`, `continueOnFailure: true`) → Exclusive Gateway → ba End Process. Gateway xét `output.status != COMPLETED` trước rồi mới `output.deliveryStatus == SENT`; nhánh mặc định là agent không gửi hoặc tin không gửi được. Lượt chạy thật của mẫu này gửi tin nhắn chat thật cho người chạy.
