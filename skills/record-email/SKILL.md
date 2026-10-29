---
name: record-email
description: "Gửi Mẫu email (Email Template) tới từng bản ghi Liên hệ/Lead (hoặc Object khác có trường email) giống thao tác Soạn Email trên bản ghi: email đi từ hộp thư dùng chung của Workspace, hiện ở tab Hoạt động của bản ghi, có theo dõi mở. Gồm nhập danh sách từ Excel, chọn mẫu và hộp thư, cá nhân hoá biến `{$record.*}`, bọc Bố cục email, chạy thử, gửi thử cho chính người dùng, chống gửi trùng mẫu, gửi theo đợt và báo cáo trạng thái gửi/mở. Dùng khi người dùng muốn gửi email hàng loạt theo mẫu, gửi lại mẫu cho danh sách khách, hoặc xem ai đã nhận/mở email của một mẫu."
metadata:
  author: cogover
  version: "1.0.0"
---

# Record Email

- **Phiên bản:** `1.0.0`
- **Ngày phát hành:** `2026-10-29`

Gửi một Mẫu email tới từng bản ghi bằng chính request của màn **Soạn Email** trên trang bản ghi. Mỗi người nhận là một email riêng, gắn vào bản ghi đó (tab Hoạt động), được đếm lượt mở như khi người dùng tự bấm Gửi. Email đã gửi không thu hồi được, nên mọi lần gửi thật phải qua chạy thử và xác nhận của người dùng.

Không dùng skill này khi cần gửi tự động theo sự kiện hoặc lịch (dùng node Send Email của [$process-creator](../process-creator/SKILL.md)), hoặc gửi email từ code của Custom Module (`email.send` trong [$cogover-custom-module](../cogover-custom-module/SKILL.md)).

## Chuẩn bị

- Credential và phiên Web App: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Script đọc `COGOVER_BASE_URL` + `COGOVER_API_KEY` (hoặc `WORKSPACE_DOMAIN` + `API_KEY`), nếu chưa có trong môi trường thì đọc đúng các khoá đó trong file `.env` ở thư mục đang làm việc. Script tự đổi API Key thành phiên Web App cho bước gửi.
- Đọc [references/api-contract.md](references/api-contract.md) trước khi gửi: payload, cách render nội dung, cách đọc trạng thái gửi và các giới hạn đã kiểm chứng.
- Helper: `python3 scripts/record_email.py <lệnh>` (đường dẫn tính từ thư mục skill). Mọi lệnh chỉ đọc, trừ `send --apply`.

| Lệnh | Việc |
|---|---|
| `mailboxes` | Hộp thư dùng chung đã từng gửi email: ID, địa chỉ, tên hiển thị, số email, lần gửi cuối |
| `templates [--search <tên>]` | Mẫu email: ID, tên, tiêu đề, Object liên quan, các biến `{$...}` trong mẫu |
| `layouts` | Bố cục email (bọc nội dung tại `{$currentContent}`) |
| `send ...` | Render và gửi; mặc định chạy thử, thêm `--apply` mới gửi |
| `status --template <ID> [--ids ...] [--since YYYY-MM-DD]` | Trạng thái gửi (`sent`/`error`/đang chờ) và số lần mở từng email |

## Quy trình

### 1. Lấy danh sách người nhận

- **Từ Excel:** đọc file, chuẩn hoá email (bỏ khoảng trắng, chữ thường), rồi báo người dùng **trước khi tạo bản ghi**: số dòng hợp lệ, dòng thiếu email, dòng email sai định dạng, dòng trùng email trong file, dòng trùng với bản ghi đã có (lọc `emails` `=` theo [$object-record](../object-record/SKILL.md)). Chỉ tạo bản ghi cho dòng hợp lệ và chưa có; dòng trùng dùng lại ID bản ghi sẵn có. Map cột theo field thật của Object ([$object-info](../object-info/SKILL.md)); giá trị không khớp option của field lựa chọn thì để trống và báo, không tự thêm option.
- **Từ dữ liệu có sẵn:** lấy ID bản ghi theo điều kiện người dùng nêu bằng [$object-record](../object-record/SKILL.md). Ghi danh sách ID ra file (mỗi dòng một ID) để dùng `--ids-file`.

### 2. Chọn mẫu, hộp thư, bố cục

1. `templates --search <từ khoá>`: chọn đúng một mẫu theo tên người dùng nêu; nhiều mẫu cùng khớp thì đưa danh sách để người dùng chọn. Đọc cột `vars` để biết mẫu cần biến nào.
2. `mailboxes`: chọn hộp thư theo địa chỉ người dùng nêu (`--from` nhận cả địa chỉ email lẫn ID). Danh sách chỉ gồm hộp thư **đã từng gửi** email trong Workspace; hộp thư chưa gửi lần nào không hiện. Khi đó nhờ người dùng gửi một email bất kỳ từ hộp thư đó qua Soạn Email trên một bản ghi, rồi chạy lại.
3. `layouts`: dùng `--layout` khi người dùng muốn email có khung giống khi chọn Bố cục trên giao diện. Không chỉ định thì gửi nguyên nội dung mẫu.
4. Chữ ký: script không tự lấy chữ ký của hộp thư. Người dùng cần chữ ký thì lưu HTML chữ ký ra file và truyền `--signature-file` (nối sau nội dung, giống thứ tự trên giao diện).

### 3. Cá nhân hoá

- `{$record.<field>}` được thay bằng giá trị của bản ghi người nhận; `{$record.<lookup>.<field>}` đi vào bản ghi được lookup. Field lựa chọn in **nhãn** option, không in slug. Field có trong Object nhưng trống trên bản ghi thì thay bằng chuỗi rỗng.
- Biến không thay được (field không tồn tại, hoặc biến khác `{$record.*}` như `{$currentUser.*}`) chặn gửi bản ghi đó. Hỏi người dùng muốn thay bằng gì rồi truyền `--var "{$currentUser.gender}=text:Anh"` (chữ cố định) hoặc `--var "[Tên Khách Hàng]=name"` (placeholder tự đặt → field). Chỉ dùng `--allow-unresolved` khi người dùng chấp nhận email còn nguyên biến.
- Mẫu viết lời chào kiểu "Anh/Chị" sẵn mà không có biến tên: email gửi đúng như mẫu, không tự chèn tên. Nêu cho người dùng biết trước khi gửi.

### 4. Chạy thử, gửi thử, gửi thật

1. **Chạy thử** (không `--apply`) với toàn bộ danh sách và `--preview <file.html>`: đọc kết quả từng dòng `READY` / `SKIP` / `ERROR`, mở file preview để kiểm tra tiêu đề, lời chào, link, bố cục.
2. **Gửi thử:** gửi thật (`--apply`) cho **một bản ghi có email của chính người dùng** (tạo bản ghi `[TEST] ...` nếu chưa có), nhờ người dùng mở hộp thư kiểm tra. Không gửi thử bằng bản ghi của khách thật.
3. **Xác nhận:** nêu tên mẫu, tiêu đề, hộp thư gửi, số người sẽ nhận, số bỏ qua (và lý do), rồi chờ người dùng đồng ý rõ ràng.
4. **Gửi thật:** `send --apply` với cùng tham số đã chạy thử. Mặc định nghỉ 2 giây giữa hai email (`--delay`) và từ chối danh sách quá 200 bản ghi (`--max`). Danh sách lớn: chia đợt theo giới hạn gửi của nhà cung cấp hộp thư (Google Workspace khoảng 2.000 email/ngày cho một hộp thư), không nâng `--max` khi người dùng chưa đồng ý.

```bash
python3 scripts/record_email.py send --template QRXXXXXXXXXXXX --from sales@example.com \
  --layout FXXXXXXXXXXXXX --object contact --ids-file recipients.txt --preview first.html
# kiểm tra xong, người dùng đồng ý:
python3 scripts/record_email.py send ... --apply
```

- **Chống gửi trùng:** trước khi gửi, script bỏ qua bản ghi đã nhận chính mẫu đó (email có trạng thái khác `error`). Chỉ dùng `--allow-resend` khi người dùng yêu cầu gửi lại. Cơ chế này chỉ nhận ra email gửi qua Soạn Email (có ghi mẫu); email gửi bằng Process không lưu mẫu nên không được tính.
- **Object khác Liên hệ:** `--object lead` dùng được ngay. Object tuỳ chỉnh ở App khác Sales: truyền `--app-slug <slug App>` và `--related-field <slug Object>`, gửi thử một bản ghi trước rồi kiểm tra email hiện ở tab Hoạt động của bản ghi đó.

### 5. Báo cáo

`status --template <ID> --since <ngày gửi>`: trạng thái `sent` thường có sau vài giây đến khoảng một phút; email chưa có trạng thái là đang chờ, kiểm tra lại sau. `error` là gửi lỗi (hộp thư mất kết nối, địa chỉ bị từ chối): liệt kê cho người dùng, không tự gửi lại. Cột `opened` là số lần mở đã ghi nhận.

## Trả kết quả

- Số đã gửi / bỏ qua / lỗi, kèm lý do bỏ qua hoặc lỗi theo từng bản ghi.
- Tên mẫu, tiêu đề, hộp thư gửi, bố cục đã dùng; các biến đã thay bằng gì.
- Bản ghi mới tạo từ Excel (ID) và các dòng Excel không nhập.
- Trạng thái thực tế theo `status`; nói rõ email nào còn đang chờ. Không khẳng định khách đã nhận khi mới có trạng thái `sent`.
