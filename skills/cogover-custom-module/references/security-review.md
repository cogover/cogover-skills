# Review bảo mật bằng sub-agent độc lập

Đọc khi Custom Module có code backend hoặc frontend: mọi project có code đều qua review này trước khi publish, phạm vi soát theo capability thực sự dùng. Contract nền tảng: [SDK API reference](cogover-sdk-api-reference.md), [Backend API Reference](custom-backend-module-api-reference.md), [Frontend API Reference](custom-frontend-module-api-reference.md). Quyền dữ liệu của Object do sub-agent Security cấu hình ở bước 2A theo `$user-permission`, không thuộc review này. Công cụ, lệnh và tên file bên dưới chỉ minh họa.

Unit test, E2E và review backend kiểm chứng hành vi đúng theo contract; chúng hiếm khi thử input do người tấn công kiểm soát, quyền bị nâng qua dữ liệu client gửi, hay secret lọt vào log, bundle và repository. Review bảo mật soát riêng các đường đó trên code sẽ publish.

## 1. Tính độc lập

- Agent chính giao một **sub-agent Review bảo mật**, khác sub-agent Backend và Frontend; agent chính không tự nhận vai này. Nên tách khỏi sub-agent Review backend để tập trung; gộp thì báo cáo bảo mật riêng và soát đủ mục 3–5. Không có công cụ sub-agent thì báo rõ yêu cầu review bảo mật độc lập chưa đáp ứng.
- Gói giao việc: contract và tiêu chí nghiệm thu; ma trận quyền, quy tắc theo Super Admin/role và theo cơ cấu tổ chức; danh sách capability đang dùng; identity policy ở mức metadata; tên secret/credential, inbound access và hộp thư được grant (không kèm giá trị); đường dẫn repository và commit sẽ publish của từng project. Chỉ truyền cách truy cập credential an toàn.
- Sub-agent không sửa source, không commit, không publish/activate, không sửa policy, secret hay quyền. Không thử khai thác trên Workspace: phát hiện cần chứng minh lúc chạy được chuyển thành ca kiểm thử ở bước 9 cho sub-agent Review backend hoặc E2E, chạy trên dữ liệu test. Lỗi báo agent chính kèm bằng chứng; agent chính giao sub-agent phụ trách sửa rồi giao review lại phần sửa.

## 2. Thời điểm và cách review

- Bước 8, sau khi unit test và coverage của project đạt, trên đúng commit sẽ publish (working tree sạch, ngoài `e2e/`). Sau mỗi vòng sửa, review lại phần sửa cùng phần liên quan. Commit publish ở các vòng sau (sửa chức năng, sửa hiệu năng) khác commit đã review thì review phần chênh lệch trước khi publish.
- Đọc code theo luồng dữ liệu: điểm vào (route, `/hooks/`, record trigger, payload job, input action, response API ngoài, input người dùng trên frontend) → kiểm tra → quyết định quyền → thao tác ghi, gửi, trả về.
- Kèm kiểm tra bằng lệnh: lỗ hổng đã biết của dependency từ lockfile (ví dụ `npm audit --omit=dev`); chuỗi giống key, token, private key, cookie trong source, `dist/`, `docs/`, `e2e/` và lịch sử Git của repository; danh sách file trong ZIP sẽ publish.

## 3. Danh mục backend

- **Danh tính và quyền:** mặc định chạy dưới danh tính người gọi; `data.asSystem()` chỉ sau khi đã kiểm quyền nghiệp vụ, trước lệnh ghi đầu tiên. Grant của identity policy (Object, field, thao tác, `allowInternalSystem`, `allowSystem`, `allowAutoApprove`, mục `email`, `processes`, `agents`) không rộng hơn thao tác code thực sự làm. Không lấy `personnelId`, role, cờ quản trị, mailbox ID, người duyệt, giá tiền hay số liệu báo cáo do client, LLM hoặc dữ liệu Process gửi làm căn cứ quyết định; quyền theo role so bằng role ID; nhánh `invocation.user` là `null` (`system`, `inbound`) được xử lý rõ. Action mở cho AI Agent áp quy tắc theo người dùng thật bằng `initiatorPersonnelId`; action `"write"` mở cho agent và `approvalPolicy: "autoApprove"` có lý do trong contract. Route chỉ dành cho Super Admin/role trả `403` ở mọi nhánh, không chỉ nhánh chính.
- **Input:** mọi điểm vào được kiểm tra kiểu, độ dài và định dạng ID trước khi dùng. `where`, `fields` hay trường sắp xếp dựng từ input chỉ nhận field và toán tử trong danh sách cho phép. URL và host của `fetch` không ghép từ input (chỉ host cố định hoặc danh sách cho phép). `limit`, kích thước mảng và số vòng lặp phụ thuộc input có trần.
- **Secret và crypto:** không hardcode key, token, private key, AES key, kể cả trong test và fixture. Giá trị secret không vào log, record, state, response, thông báo lỗi hay nội dung notification/email; response của dịch vụ ngoài chỉ trả field cần. Credential chỉ cho host cần thiết. So sánh chữ ký/token bằng `timingSafeEqual`, kiểm giá trị trả về của `verify`, JWT kiểm `exp`, `iss`, `aud`; không dùng lại IV với cùng key GCM, CBC có HMAC kèm, không dùng `RSA-SHA1` cho chữ ký mới, không băm mật khẩu bằng SHA-256.
- **Inbound webhook:** handler kiểm `invocation.identity === "inbound"` và `invocation.inbound.mode` khi bắt buộc HMAC; chữ ký riêng của nhà cung cấp kiểm trên `request.rawBody`; chống gửi lại theo event ID (và timestamp khi có); không thực hiện thao tác đặc quyền chỉ dựa vào nội dung body chưa kiểm.
- **Gửi ra ngoài:** dữ liệu người dùng ghép vào HTML của notification/email được escape. Người nhận lấy từ nguồn tin cậy (`org`, record đã kiểm quyền), không từ input tuỳ ý. Toast, notification, email và tin nhắn `deliverTo` không chứa dữ liệu người nhận không được xem; link là path web app hoặc URL `http(s)` tuyệt đối; `idempotencyKey` chặn gửi lặp. `instruction` của `agents.start` không chứa secret và không đưa input người dùng chưa kiểm vào như chỉ dẫn cho agent.
- **Lạm dụng tài nguyên:** một lời gọi route hoặc webhook không tạo được khối lượng tuỳ ý (record, job, email, notification, lượt chạy Process/AI Agent); job tự enqueue có điều kiện dừng; chuỗi Process/AI Agent → action/job → start không tự gọi lại chính nó.
- **Lỗi và log:** response lỗi không chứa stack, chi tiết nội bộ, secret hay dữ liệu ngoài quyền người gọi; log không chứa secret, cookie, input/output nhạy cảm của action hay dữ liệu cá nhân không cần thiết.

## 4. Danh mục frontend

- Mọi mã frontend được coi là công khai: không có key, token, secret trong source, biến `VITE_*`, `dist/` hay source map.
- Không phân quyền bằng cách ẩn nút hoặc route: thao tác cần quyền phải bị backend hoặc Object Security Rules chặn, frontend chỉ phản ánh.
- XSS: không dùng `dangerouslySetInnerHTML`/`innerHTML` với dữ liệu record, input hay response chưa làm sạch; URL lấy từ dữ liệu chỉ nhận `http(s)` hoặc path nội bộ (chặn `javascript:`); link ra ngoài mở tab mới có `rel="noopener noreferrer"`.
- Gọi API qua HTTP client của template hoặc cùng cơ chế phiên Workspace (cookie, CSRF theo `XSRF-TOKEN`); không lưu token hay dữ liệu nhạy cảm vào `localStorage`/`sessionStorage`; không in dữ liệu nhạy cảm ra console. Dữ liệu nhận qua message từ trang chứa hoặc `push.message` được kiểm như input không tin cậy.

## 5. Dependency, repository và gói publish

- Dependency chạy trong bundle frontend hoặc code backend không có lỗ hổng Cao/Nghiêm trọng đã biết mà cách module dùng có thể bị khai thác; lockfile được commit; package mới thêm có lý do.
- Repository: `.gitignore` theo [Bố cục repository](cli-session-and-delivery.md#bố-cục-repository); không có `.env`, file phiên, `cogover.json`, artifact E2E hay secret trong file đã commit và trong lịch sử Git. Secret đã vào lịch sử là phát hiện Nghiêm trọng: báo người dùng xoay secret đó, không tự viết lại lịch sử Git.
- ZIP publish: backend chỉ chứa `src/`, frontend chỉ chứa `dist/` không có source map; không có `.env`, file phiên, `local/`, `docs/`, `e2e/`.

## 6. Mức độ, cổng publish và vòng sửa

| Mức | Ví dụ | Xử lý |
|---|---|---|
| Nghiêm trọng | Lộ secret/credential; đọc hoặc ghi dữ liệu ngoài quyền trên diện rộng; inbound webhook không xác thực; thực thi tuỳ ý | Phải sửa và review lại trước khi publish. Không giới hạn số vòng sửa và agent chính không tự chấp nhận rủi ro thay người dùng; sau 2 vòng vẫn còn thì dừng vòng sửa, báo người dùng phát hiện, bằng chứng và phương án (đổi thiết kế, bỏ hoặc thu hẹp tính năng); không publish cho tới khi phát hiện được đóng |
| Cao | Vượt quyền trong phạm vi hẹp; XSS lưu trữ; bỏ qua kiểm tra chữ ký hoặc chống gửi lại; grant ghi rộng không cần; dependency có lỗ hổng Cao khai thác được | Như mức Nghiêm trọng |
| Trung bình | Thiếu kiểm tra input gây lạm dụng có giới hạn; log dữ liệu cá nhân; lỗi trả chi tiết nội bộ; grant đọc rộng hơn cần | Sửa tối đa 2 vòng; phần còn lại agent chính ghi rủi ro chấp nhận kèm lý do, báo người dùng trước khi publish và ghi vào bàn giao |
| Thấp | Thiếu biện pháp phòng thủ bổ sung khi rủi ro đã được chặn ở lớp khác | Như mức Trung bình |
| Thông tin | Gợi ý cải thiện | Ghi nhận, không bắt buộc sửa |

- Một vòng sửa: sub-agent phụ trách sửa → sub-agent Review bảo mật review lại phần sửa cùng phần liên quan. Phát hiện mới phát sinh trong vòng sửa được xử lý theo mức của nó.
- Phát hiện đọc được trực tiếp trong code ghi `CONFIRMED`; phụ thuộc hành vi nền tảng chưa đo được ghi `PLAUSIBLE` kèm cách kiểm chứng. Phát hiện Nghiêm trọng/Cao `PLAUSIBLE` cần chạy thử mới kiểm chứng được thì được publish để preview (service `6`, `READ_ONLY` khi có thể) nhưng chưa activate cho tới khi đã kiểm chứng hoặc đã sửa.

## 7. Báo cáo

Gồm: project và commit đã review; capability trong phạm vi; lệnh đã chạy và kết quả (audit dependency, tìm secret, danh sách file trong ZIP); bảng phát hiện (mức, `CONFIRMED`/`PLAUSIBLE`, file:dòng, mô tả, kịch bản khai thác cụ thể, đề xuất sửa); ca kiểm thử chuyển sang bước 9; mục review lại sau mỗi vòng sửa; rủi ro được chấp nhận, lý do và người quyết định; giới hạn (phần chưa đọc, dependency không quét được). Không đưa giá trị secret hay dữ liệu thật vào báo cáo, kể cả khi đó chính là phát hiện: chỉ nêu vị trí và loại.
