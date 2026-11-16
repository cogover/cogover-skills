# Mẫu tiếng Việt: CSKH, telesale, nhắc lịch

Bốn callbot mẫu cho một chuỗi điện máy giả định (**An Phát Home**: điều hoà, máy lọc nước, máy lọc không khí). Chúng phủ các nhóm callbot phổ biến: tổng đài CSKH gọi vào, telesale chăm sóc lead gọi ra, nhắc và xác nhận lịch hẹn gọi ra, khảo sát hài lòng sau dịch vụ gọi ra. Cả 3 dùng `openai_realtime` (`gpt-realtime`, giọng `marin`, `gpt-4o-mini-transcribe`), ghi âm bật, ghi dữ liệu bằng hồ sơ ghi v2.

Spec chạy được bằng `apply` (dựng và mô phỏng trên Workspace thật ngày 2026-11-16; bản khảo sát được dựng bằng chính skill này qua `apply`; đã thay `runAsPersonnelId` và email nhân sự bằng giá trị mẫu):

| Spec | Hướng | Tool |
|---|---|---|
| [an-phat-cskh.spec.json](../assets/vi-an-phat/an-phat-cskh.spec.json) | Gọi vào (IVR "Kết nối callbot") | `tra_cuu_khach_hang` (search contact), `tra_cuu_yeu_cau` (search ticket theo `phone_number`), `tao_yeu_cau_ho_tro` (hồ sơ ghi: ticket), `switch_to_consultant`, `set_outcome`, `end_call` |
| [an-phat-telesale.spec.json](../assets/vi-an-phat/an-phat-telesale.spec.json) | Gọi ra (chiến dịch, biến `ten_khach`, `san_pham`) | `tra_cuu_lead` (search lead), `dat_lich_tu_van` (hồ sơ ghi: task gọi lại gắn lead/contact, giao chuyên viên), `set_outcome` (chấm điểm + `callback_at`), `switch_to_consultant`, `end_call` |
| [an-phat-khao-sat.spec.json](../assets/vi-an-phat/an-phat-khao-sat.spec.json) | Gọi ra (chiến dịch, biến `ten_khach`, `dich_vu`, `ngay_hoan_thanh`) | `tra_cuu_khach_hang`, `tao_phan_anh` (hồ sơ ghi: ticket `problem` khi điểm 1–3 hoặc thiết bị chưa ổn), `set_outcome` (`diem_hai_long`, `thiet_bi_on_dinh`, `gop_y`, `callback_at`), `switch_to_consultant`, `end_call` |
| [an-phat-nhac-lich.spec.json](../assets/vi-an-phat/an-phat-nhac-lich.spec.json) | Gọi ra (chiến dịch, biến `ten_khach`, `dich_vu`, `thoi_gian_hen`, `dia_chi_rut_gon`) | `tao_yeu_cau_doi_lich` (hồ sơ ghi: ticket đổi/huỷ lịch), `set_outcome`, `switch_to_consultant`, `end_call` |

Trước khi `apply` lên Workspace khác:

1. Đổi `runAsPersonnelId` và `personnelEmail` (`tu-van@example.com`) thành nhân sự thật; nhân sự run-as cần quyền đọc contact/lead/ticket và tạo ticket/activity.
2. Đọc field bằng `rpc get_object_fields --callbot ID --object ticket` (và `activity`, `lead`): slug option (`status`, `type`, `priority`, `origin`, `task_type`...) phải khớp Workspace; Object có field bắt buộc riêng thì thêm vào `fields`.
3. Đổi tên hàng đợi `Support` trong `switch_to_consultant` thành hàng đợi có thật.
4. Sửa phần "Thông tin được phép trả lời" (bảo hành, giá, ưu đãi) theo dữ liệu thật của khách hàng; bot chỉ được nói những gì có trong kịch bản.

## Thiết kế dùng lại được

- **Tra cứu chỉ để xưng hô:** tool đọc trả `salutation`, `first_name` (contact/lead) và yêu cầu cũ (`serial`, `name`, `status`, `created`). Kịch bản cấm đọc số điện thoại/hồ sơ, và có bảng đọc trạng thái bằng tiếng Việt (`in_progress` = đang xử lý...).
- **Ticket bằng hồ sơ ghi:** bot chỉ hỏi `tieu_de`, `mo_ta`, `loai`, `muc_do`; `status` = `new`, `origin` = `phone` cố định, `phone_number` ← `call.number`, `contact` ← `caller.contact`. Với bot nhắc lịch, `type` và `priority` cũng cố định nên bot chỉ hỏi nội dung.
- **Task gọi lại bằng hồ sơ ghi:** `time` và `activity_time` dùng chung tham số `due_at` (`range: future`), `name` có `appendCallNumber`, `content` có `callSummary`, nhắc trước `900000` ms, người phụ trách là `choice` một lựa chọn mặc định, gắn `lead` và `contacts` bằng `caller.*`.
- **Outcome có cấu trúc:** mỗi bot có bộ outcome riêng với `campaignAction` (`done`, `callback`, `do_not_call`), field chấm điểm (`muc_do_quan_tam` enum `hot`/`warm`/`cold`, `ngan_sach`, `thoi_diem_mua`...) và `callback_at` kiểu `datetime` theo giờ địa phương. Kịch bản dặn chỉ gửi field khách đã trả lời.
- **Xác minh trước khi nói chi tiết (gọi ra):** bot nhắc lịch hỏi đúng người trước khi đọc dịch vụ, giờ, địa chỉ; sai người thì `set_outcome sai_nguoi` và không lộ gì.
- **An toàn và chuyển người thật:** thiết bị có mùi khét/chập điện thì hướng dẫn ngắt nguồn, tạo ticket mức `urgent`, đề nghị chuyển hàng đợi; khách đòi gặp người thật thì `set_outcome` rồi `switch_to_consultant`.

## Lỗi kịch bản đã gặp khi mô phỏng và câu đã thêm

| Hiện tượng | Câu trong kịch bản |
|---|---|
| Hỏi lại thông tin khách đã nói (model, ngày mua, địa chỉ) | Liệt kê thông tin bắt buộc; thông tin thêm khách đã nói hoặc nói không nhớ thì coi như đã có, "TUYỆT ĐỐI không hỏi lại" |
| Hỏi "anh có muốn tạo yêu cầu không" / tự đọc lại trước khi gọi tool | "Ngay khi có ... gọi tool trong lượt đó; hệ thống sẽ tự đọc lại để khách xác nhận" |
| Nói "em sẽ ghi nhận" mà không tạo gì | "Không bao giờ nói 'đã ghi nhận'... khi chưa tạo thành công; khách muốn kết thúc khi chưa tạo thì hỏi nhanh có muốn tạo ngay không" |
| Tự chọn giờ hẹn | "TUYỆT ĐỐI không tự chọn hay gợi ý sẵn một giờ; chỉ gọi tool SAU KHI khách đã tự nói ngày giờ" |
| Chèn tên khách vào mô tả ticket (nguy cơ bị chặn khi gọi thật) | "Không ghi tên, danh xưng hay dữ liệu tra cứu vào tieu_de và mo_ta; viết dạng 'Khách báo ...'" |
| Gọi `set_outcome` hai lần; chào mà không `end_call` | Khối "Quy tắc công cụ kết thúc (bắt buộc)": `set_outcome` chỉ một lần; khách chào thì chào ngắn **và** gọi `end_call` trong lượt đó |
| Đọc hiểu quá đà câu "không hứa chắc giờ" thành lời từ chối | Viết sẵn nguyên câu bot nói sau khi tạo yêu cầu đổi lịch |
| Khách bận: tự chọn giờ gọi lại hoặc `end_call` trước khi khách chào | Tách nhánh: "khách CHƯA nói giờ thì chỉ hỏi giờ, KHÔNG gọi công cụ nào"; "khi khách đã nói giờ: `set_outcome` với ĐÚNG HAI trường outcome và `callback_at`... chưa `end_call`, gọi ở lượt sau khi khách chào lại" |
| Bot nói ra ghi chú hành động ("(kết thúc cuộc gọi)") | "Không bao giờ nói ra tên công cụ hay ghi chú hành động" |
| Tự điền field chấm điểm khi khách chỉ hẹn gọi lại | "KHÔNG kèm các trường chấm điểm" ở nhánh gọi lại (model đôi khi vẫn điền; không ảnh hưởng luồng) |

## Dữ liệu demo

Mô phỏng dùng số trong hồ sơ nhân sự của người thao tác, nên contact, lead và ticket demo phải có số đó. Lead có duplicate rule theo số điện thoại thì đừng tạo hai lead cùng số: trùng số làm thao tác trên lead bị chặn và bot xưng hô theo lead khác. Đặt tiền tố nhận biết (ví dụ `[An Phát]`) cho mọi bản ghi demo.
