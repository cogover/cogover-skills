# Mẫu: thu hồi nợ (collections) đa ngôn ngữ

Mẫu cho callbot gọi ra nhắc nợ khoản vay bán lẻ, nói tiếng Hindi và Bengali: đọc hồ sơ khoản vay trên Lead, tạo task hẹn trả nợ (PTP) hoặc hẹn gọi lại cho cán bộ thu hồi nợ, ghi kết quả vào outcome của chiến dịch. Bot không sửa Lead (nền tảng chặn sửa lead/contact/account). Spec đầy đủ, chạy được bằng `apply`: [assets/collections-spec.example.json](../assets/collections-spec.example.json). Thay tên ngân hàng, ID nhân sự và field cho đúng Workspace.

## Dữ liệu

Thêm vào Lead (hoặc Object chứa hồ sơ khách) bằng [$object-info](../../object-info/SKILL.md) các field bot **đọc**:

| Field | Kiểu | Dùng cho |
|---|---|---|
| `col_language` | `single_choice`: `hindi`, `bengali`, `english` | Ngôn ngữ ưu tiên; bot ghi lại ngôn ngữ đã dùng |
| `col_loan_ref` | `short_text` | Mã khoản vay đã che (`XXXX1234`), để xác minh 4 số cuối |
| `col_overdue_amount` | `decimal` | Số tiền quá hạn bot đọc cho khách |
| `col_due_date` / `col_due_date_text` | `date` / `short_text` | Ngày đến hạn: `date` để lọc, bản văn bản để bot đọc |
| `col_dpd_bucket` | `single_choice` | Nhóm ngày quá hạn, để phân luồng chiến dịch |

Bot **ghi** bằng hồ sơ ghi v2 vào `activity` (task) có sẵn, gắn Lead bằng `caller.lead`: hẹn trả nợ là task "PTP <số tiền>" hạn đúng giờ khách hẹn, hẹn gọi lại là task gọi lại; cả hai giao cho cán bộ thu hồi nợ (đặt email nhân sự thật trong `choices`), nhắc trước theo `reminder_before_due`. Kết quả cuộc gọi (`ptp`, `callback`, `paid`, `refused`...) cùng ngôn ngữ và tóm tắt nằm ở `set_outcome`, xem trong lịch sử phiên và chiến dịch. Cần trạng thái thu hồi nợ trên Lead (`col_status`...) để lọc/báo cáo thì dựng Process cập nhật Lead từ task hoặc outcome, ngoài phạm vi skill này.

Số điện thoại: lưu đúng định dạng nhà mạng gửi sang (ví dụ `91XXXXXXXXXX`); `+91...` không tự khớp với `91...`, xem [Hành vi lúc chạy](tools.md#cogover_object).

## Cấu hình giọng

`provider: sarvam`, `model: sarvam-105b`, `providerOptions: {"language": "auto", "ttsModel": "bulbul:v3", "timezone": "Asia/Kolkata"}`, giọng đa ngôn ngữ (ví dụ `priya`). `timezone` cho bot giờ Ấn Độ và thứ bằng tiếng Anh, không cần tự quy đổi từ UTC+7. Lời chào bằng tiếng Hindi, hỏi khách muốn nói Hindi hay Bengali; từ câu trả lời đầu tiên bot nói theo ngôn ngữ khách.

## Tool

| Tool | Loại | Ghi | Xác nhận |
|---|---|---|---|
| `lookup_borrower` | `search` Lead theo số khách; chỉ trả họ tên, mã khoản vay che, số tiền, ngày đến hạn dạng văn bản | — | — |
| `record_promise_to_pay` | Hồ sơ ghi v2, tạo `activity` | `name` ← `title` ("PTP 12450 rupees", kèm số gọi), `time`/`activity_time` ← `promise_at`, `content` ← `note` (tóm tắt cuộc gọi), task `call` ưu tiên `high`, `lead` ← `caller.lead`, người phụ trách | Luôn |
| `schedule_callback` | Hồ sơ ghi v2, tạo `activity` (mẫu Task gọi lại) | `name` ← `title`, `time`/`activity_time` ← `due_at`, `content` ← `description`, nhắc trước 15 phút, `lead` ← `caller.lead`, người phụ trách | Luôn |
| `create_lead` | Hồ sơ ghi v2, tạo `lead` | `name` và `last_name` ← `full_name`, `mobile_phones` ← `call.number`, `lead_source` = `call`, `description` ← `summary` | Luôn |
| `set_outcome` | hệ thống | `ptp`/`paid`/`new_lead` → `done`, `callback` → `callback`, `refused` → `retry`, `do_not_call` → `do_not_call`, `wrong_party` → `none`; field `language` (`hindi`/`bengali`/`english`, bắt buộc), `summary` | — |
| `end_call` | hệ thống | — | — |

Một cuộc gọi điển hình ghi 1 lần (PTP hoặc gọi lại), dưới giới hạn 3 lệnh ghi mỗi phiên; `maxPerSession: 1` chặn bot tạo hai task cho cùng một cuộc gọi. Số điện thoại lead mới lấy từ cuộc gọi (`call.number`), không để bot đọc hay chép số. Kịch bản cấm đưa tên khách, mã khoản vay hay văn bản hồ sơ vào tiêu đề/ghi chú ([Chặn theo nguồn dữ liệu](tools.md#chặn-theo-nguồn-dữ-liệu-cuộc-gọi-thật)). Khách tranh chấp/khó khăn: hẹn gọi lại, ghi lý do trong ghi chú. Giờ hẹn gọi lại nằm trong task cho cán bộ; outcome `callback` không có field `callback_at` nên chiến dịch gọi lại theo lịch mặc định (thêm field `callback_at` kiểu `datetime` nếu muốn chiến dịch tự gọi lại đúng giờ khách hẹn). Workspace có field bắt buộc riêng trên Lead (ví dụ `currency`) thì thêm vào `fields` của `create_lead` với `source: fixed`.

Đã kiểm chứng bằng mô phỏng trên Workspace thật (2026-11-16): xác minh tên + 4 số cuối → PTP "PTP 12450 rupees" lúc `2026-11-20T18:00` giờ Ấn Độ → đọc lại → `confirm_pending` → `set_outcome ptp` → `end_call` khi khách chào; nhánh gọi lại `2026-11-17T11:00`.

## Kịch bản (rút gọn)

Viết kịch bản bằng tiếng Anh cho callbot nhiều ngôn ngữ (model hiểu tốt, bot vẫn trả lời bằng ngôn ngữ khách). Các khối nên có:

1. **Language:** nhận diện từ câu đầu, trả lời đúng chữ viết (Devanagari/Bengali), đổi ngay khi khách yêu cầu; mỗi lượt 1–2 câu; số tiền giữ chữ số Latin nguyên văn như trong hồ sơ (không đổi sang chữ số Bengali/Devanagari, không thêm dấu phân cách), đọc ngày theo field văn bản; khi khách nói thứ trong tuần, quy ra ngày cụ thể và đọc lại.
2. **Call flow:** tra hồ sơ trước, chưa nói gì về khoản vay → xác minh (họ tên + 4 số cuối mã khoản vay, không tự đọc ra, tối đa 2 lần) → nói số tiền và ngày đến hạn → xử lý từng kết quả (PTP trong 30 ngày, hẹn gọi lại trong khung giờ cho phép, đã trả, tranh chấp/khó khăn → hẹn cán bộ gọi lại, từ chối, không muốn bị gọi) → đặt outcome một lần, hỏi khách còn cần gì; khách chào thì chào ngắn và `end_call` ngay lượt đó (không `end_call` cùng lượt với kết quả tra cứu). Lỗi tra cứu: xin lỗi, hẹn cán bộ gọi lại, không ghi gì thêm. Không có hồ sơ: tạo lead, báo cán bộ sẽ liên hệ, outcome `new_lead`, không nói về nợ.
3. **Conduct rules:** không đe doạ, xúc phạm, nhắc công an/bắt giữ/kiện tụng/tịch thu/báo người thân hay nơi làm việc; không bàn khoản vay với người khác; không hỏi/nhận số thẻ, OTP, PIN, mật khẩu; không hứa miễn giảm/tái cơ cấu; không thu tiền hay gửi link thanh toán trên cuộc gọi; khung giờ gọi theo giờ địa phương; tự nhận là trợ lý tự động khi được hỏi.
4. **Context:** `{{system.current_datetime}}` (đã theo `timezone` của callbot, thứ bằng tiếng Anh), `{{system.customer_number}}`; dặn bot quy thứ trong tuần ra ngày cụ thể và đọc lại.

## Đối chiếu quy định

Các mục cần người dùng/khách hàng xác nhận trước khi cho thử trên dữ liệu thật (skill không tư vấn pháp lý): quy định đòi nợ và khung giờ gọi của cơ quan quản lý, bảo vệ dữ liệu cá nhân và đồng ý xử lý dữ liệu, thời hạn lưu ghi âm/transcript, nơi lưu trữ dữ liệu (data residency) của ghi âm, transcript và nhà cung cấp giọng nói/LLM, quy trình khiếu nại và chuyển người thật.
