# Mẫu: thu hồi nợ (collections) đa ngôn ngữ

Mẫu cho callbot gọi ra nhắc nợ khoản vay bán lẻ, nói tiếng Hindi và Bengali, ghi kết quả vào Lead, hẹn trả nợ (PTP) hoặc hẹn gọi lại. Spec đầy đủ, chạy được bằng `apply`: [assets/collections-spec.example.json](../assets/collections-spec.example.json). Thay tên ngân hàng, ID nhân sự và field cho đúng Workspace.

## Dữ liệu

Thêm vào Lead (hoặc Object chứa hồ sơ khách) bằng [$object-info](../../object-info/SKILL.md):

| Field | Kiểu | Dùng cho |
|---|---|---|
| `col_language` | `single_choice`: `hindi`, `bengali`, `english` | Ngôn ngữ ưu tiên; bot ghi lại ngôn ngữ đã dùng |
| `col_loan_ref` | `short_text` | Mã khoản vay đã che (`XXXX1234`), để xác minh 4 số cuối |
| `col_overdue_amount` | `decimal` | Số tiền quá hạn bot đọc cho khách |
| `col_due_date` / `col_due_date_text` | `date` / `short_text` | Ngày đến hạn: `date` để lọc, bản văn bản để bot đọc |
| `col_dpd_bucket` | `single_choice` | Nhóm ngày quá hạn, để phân luồng chiến dịch |
| `col_status` | `single_choice`: `ptp`, `callback`, `paid`, `dispute`, `refused`, `wrong_party`, `do_not_call`, `no_contact` | Kết quả gần nhất |
| `col_ptp_date`, `col_ptp_amount` | `date`, `decimal` | Hẹn trả nợ |
| `col_callback_date`, `col_callback_time` | `date`, `short_text` (`HH:mm`) | Hẹn gọi lại |
| `col_call_summary` | `long_text` | Tóm tắt một dòng |

Lịch hẹn được theo dõi bằng bộ lọc/báo cáo trên `col_ptp_date`, `col_callback_date` (ví dụ "PTP đến hạn hôm nay", "Gọi lại hôm nay") và chiến dịch gọi lại theo `col_status`. Nhắc việc tự động cho nhân viên dùng Process, ngoài phạm vi skill này.

Số điện thoại: lưu đúng định dạng nhà mạng gửi sang (ví dụ `91XXXXXXXXXX`); `+91...` không tự khớp với `91...`, xem [Hành vi lúc chạy](tools.md#cogover_object).

## Cấu hình giọng

`provider: sarvam`, `model: sarvam-105b`, `providerOptions: {"language": "auto", "ttsModel": "bulbul:v3"}`, giọng đa ngôn ngữ (ví dụ `priya`). Lời chào bằng tiếng Hindi, hỏi khách muốn nói Hindi hay Bengali; từ câu trả lời đầu tiên bot nói theo ngôn ngữ khách.

## Tool

| Tool | Loại | Ghi | Xác nhận |
|---|---|---|---|
| `lookup_borrower` | `search` Lead theo số khách; chỉ trả họ tên, mã khoản vay che, số tiền, ngày đến hạn dạng văn bản | — | — |
| `record_promise_to_pay` | `update` Lead của người gọi | `col_ptp_date`, `col_ptp_amount`, `col_status`, `col_call_summary` | Có |
| `schedule_callback` | `update` Lead của người gọi | `col_callback_date`, `col_callback_time`, `col_status`, `col_call_summary` | Có |
| `log_call_result` | `update` Lead của người gọi | `col_status`, `col_language`, `col_call_summary` | Không |
| `create_lead` | `create` Lead | `name`, `first_name`, `last_name`, `mobile_phones`, `col_language`, `lead_source`, `col_call_summary` | Không |
| `set_outcome` | hệ thống | `ptp`/`paid`/`new_lead` → `done`, `callback` → `callback`, `refused` → `retry`, `do_not_call` → `do_not_call`, `wrong_party` → `none` | — |
| `end_call` | hệ thống | — | — |

Một cuộc gọi điển hình ghi 2 lần (hẹn + kết quả), dưới giới hạn 3 lệnh ghi mỗi phiên. Tool ghi để `returnFields: []` và tool tra cứu không trả `col_status`/`col_language`, để nền tảng không chặn lệnh ghi lại các giá trị này ([Chặn theo nguồn dữ liệu](tools.md#chặn-theo-nguồn-dữ-liệu-cuộc-gọi-thật)). Khách tranh chấp/khó khăn: `col_status` là `callback`, chi tiết nằm trong tóm tắt.

## Kịch bản (rút gọn)

Viết kịch bản bằng tiếng Anh cho callbot nhiều ngôn ngữ (model hiểu tốt, bot vẫn trả lời bằng ngôn ngữ khách). Các khối nên có:

1. **Language:** nhận diện từ câu đầu, trả lời đúng chữ viết (Devanagari/Bengali), đổi ngay khi khách yêu cầu; mỗi lượt 1–2 câu; số tiền giữ chữ số Latin nguyên văn như trong hồ sơ (không đổi sang chữ số Bengali/Devanagari, không thêm dấu phân cách), đọc ngày theo field văn bản; khi khách nói thứ trong tuần, quy ra ngày cụ thể và đọc lại.
2. **Call flow:** tra hồ sơ trước, chưa nói gì về khoản vay → xác minh (họ tên + 4 số cuối mã khoản vay, không tự đọc ra, tối đa 2 lần) → nói số tiền và ngày đến hạn → xử lý từng kết quả (PTP trong 30 ngày, hẹn gọi lại trong khung giờ cho phép, đã trả, tranh chấp/khó khăn → hẹn cán bộ gọi lại, từ chối, không muốn bị gọi) → ghi kết quả, đặt outcome, chào và chờ khách đáp rồi mới kết thúc (`end_call` ngay sau lệnh ghi có thể bị chặn). Lỗi tra cứu: xin lỗi, hẹn cán bộ gọi lại, không ghi gì thêm. Không có hồ sơ: tạo lead, báo cán bộ sẽ liên hệ, outcome `new_lead`, không nói về nợ.
3. **Conduct rules:** không đe doạ, xúc phạm, nhắc công an/bắt giữ/kiện tụng/tịch thu/báo người thân hay nơi làm việc; không bàn khoản vay với người khác; không hỏi/nhận số thẻ, OTP, PIN, mật khẩu; không hứa miễn giảm/tái cơ cấu; không thu tiền hay gửi link thanh toán trên cuộc gọi; khung giờ gọi theo giờ địa phương; tự nhận là trợ lý tự động khi được hỏi.
4. **Context:** `{{system.current_datetime}}` kèm độ lệch múi giờ (giờ hệ thống UTC+7; giờ Ấn Độ chậm hơn 1 giờ 30 phút) và bảng quy đổi thứ tiếng Việt sang tiếng Anh, `{{system.customer_number}}`.

## Đối chiếu quy định

Các mục cần người dùng/khách hàng xác nhận trước khi cho thử trên dữ liệu thật (skill không tư vấn pháp lý): quy định đòi nợ và khung giờ gọi của cơ quan quản lý, bảo vệ dữ liệu cá nhân và đồng ý xử lý dữ liệu, thời hạn lưu ghi âm/transcript, nơi lưu trữ dữ liệu (data residency) của ghi âm, transcript và nhà cung cấp giọng nói/LLM, quy trình khiếu nại và chuyển người thật.
