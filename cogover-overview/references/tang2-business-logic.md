# Tầng 2: Business Logic

Tầng 2 kết hợp dữ liệu và giao diện của Tầng 1 thành logic vận hành: quy trình, quyền, menu, tài liệu, báo cáo và tích hợp. File này chỉ mô tả phạm vi và chọn skill; contract triển khai nằm ở skill chuyên trách theo [bản đồ điều phối skill](../SKILL.md#bản-đồ-điều-phối-skill). Project chưa có skill độc lập cho Notification configuration, Assignment Rules và Workspace/Personal Email configuration: các task gửi thông báo, gửi email hoặc gán giá trị bên trong Process thuộc `$process-creator`, gửi notification/email từ code của Custom Backend Module thuộc `$cogover-custom-module`; cả hai không thay thế ba module cấu hình này.

## Object Process

Năm loại quy trình, chọn theo cơ chế khởi chạy; sau đó dùng `$process-creator` đọc support matrix, dựng JSON BPMN, triển khai và kiểm thử.

| Loại | Cơ chế khởi chạy | Trường hợp phù hợp |
|---|---|---|
| **Manual Flow** (`manual_flow`) | Người dùng submit Root User Task (form) | Đề nghị mua sắm, xin nghỉ phép, yêu cầu thanh toán |
| **Normal Flow** (`normal_flow`) | Người có quyền chủ động chạy; không bắt buộc Root form | Chạy trực tiếp từ Start đến action, gateway hoặc End |
| **Scheduled Flow** (`scheduled_flow`) | Lịch hoặc cron | Nhắc hạn, kiểm tra SLA, tổng hợp định kỳ |
| **Triggered Flow** (`triggered_flow`) | Record create/update/delete hoặc webhook theo contract | Phản ứng khi dữ liệu thay đổi hoặc nhận yêu cầu tích hợp |
| **Sequence Flow** (`sequence_flow`) | Liên kết record với một chuỗi bước tuần tự | Nurture Lead, onboarding hoặc follow-up theo record |

Chỉ Manual Flow bắt buộc Root User Task làm form khởi tạo; không áp quy tắc này cho Normal, Scheduled, Triggered hoặc Sequence Flow.

Nhóm node (danh sách thực tế lấy từ `$process-creator`): điều khiển luồng (Start/End, Exclusive/Inclusive/Parallel Gateway, Loop, Wait, Sub Process); tương tác người dùng (User Task, To Do, Phone Call); dữ liệu và biến (Variable, Assignment, Get/Create/Update Record, Organization); giao tiếp và tích hợp (Send Email, Send Notification, Send HTTP Request, Omni Message); đầu ra (Export Record và các resource/template liên quan).

Trình tự thiết kế:

1. Chốt mục tiêu, sự kiện bắt đầu, tiêu chí kết thúc; chọn một trong năm loại Flow.
2. Xác định actor, quyền chạy/xem/hủy và các nhánh ngoại lệ.
3. Resolve Object, field, option, Personnel/Role và resource thật.
4. Thiết kế happy path, timeout, retry, lỗi và idempotency nếu có tích hợp.
5. Dựng Process bằng `$process-creator`, kiểm tra tính hợp lệ rồi kích hoạt; chạy thử một instance, xác minh task, record, thông báo và quyền truy cập.

Ví dụ: xin nghỉ phép thường là Manual Flow (Root form → xác định cấp duyệt → User Task phê duyệt → cập nhật record → gửi kết quả); phản ứng khi một Lead được tạo thường là Triggered Flow (trigger record → tìm/gán nguồn lực theo logic đã xác nhận → cập nhật record → gửi thông báo).

## Quản lý ứng dụng

App gom Object, saved filter, report, dashboard và trang liên quan thành cấu trúc menu cho một nhóm người dùng: Menu item → Object hoặc saved filter; Menu group → Submenu → Report hoặc Dashboard; Menu item → trang được hỗ trợ khác.

`$app-menu-manager` snapshot cấu trúc hiện có, tạo hoặc cập nhật App/menu và kiểm tra ACL; `$cogover-icon` chọn icon hợp lệ. Không hardcode menu target hoặc ID từ overview.

## Vai trò và phân quyền

Thiết kế quyền theo bốn lớp: (1) truy cập App/menu; (2) chức năng trên Object, ví dụ Create/Read/Update/Delete theo contract; (3) Data Security cấp record theo owner, cơ cấu tổ chức, Role hoặc điều kiện nghiệp vụ; (4) quyền Process: khởi chạy, xem tiến độ, xử lý task, hủy instance.

`$user-permission` cho User, Personnel, Department, Position, Role, Object permission và Data Security; App hoặc Process có ACL riêng thì phối hợp thêm skill tương ứng. Custom Backend Module có thể thêm quy tắc nghiệp vụ trong code theo cơ cấu tổ chức (ví dụ chỉ quản lý của người tạo được duyệt) hoặc theo Super Admin/role của người gọi; đây là lớp bổ sung, không thay Data Security. Nghiệm thu bằng ít nhất một tài khoản được phép và một tài khoản bị từ chối.

## Thông báo

Thông báo phát sinh từ sự kiện (record mới, đổi trạng thái, đến hạn, kết quả phê duyệt); thiết kế phải xác định rõ sự kiện, người nhận, nội dung, kênh và chống gửi lặp.

- Hai cách gửi, chọn một cho mỗi thông báo:
  - **Process**: node Send Notification/Send Email theo `$process-creator` khi thông báo là một bước của luồng BPMN hoặc người dùng muốn tự cấu hình trên giao diện.
  - **Custom Backend Module**: `notifications.send` (lưu vào danh sách thông báo của người nhận, gửi qua web, web push, mobile push và bản sao email theo notification channel) và `email.send` trong route, record trigger after-change, background job hoặc webhook, khi người nhận hay nội dung do logic backend quyết định, ví dụ quản lý trực tiếp tìm từ cơ cấu tổ chức; theo `$cogover-custom-module`. Push message của backend (toast, làm mới record) chỉ tới người đang mở web và không lưu vào danh sách thông báo.
  - Không gửi cùng một thông báo bằng cả Process và backend; thiết kế chống gửi lặp bằng điều kiện của Process hoặc idempotency key của backend.
- Node **Send Notification** gửi được đến ứng dụng Cogover trên Android/iOS khi chọn **Loại thông báo** là **All** hoặc **In app**. `All` và `In app` là hai bản ghi của Object `notification_channel`; kênh nhận do các trường tương ứng được tick trên bản ghi đó quyết định. Khi trường **mobile push** được tick, người nhận nhận thêm thông báo đẩy trên thiết bị mobile kể cả khi không mở ứng dụng; phân biệt thông báo trong ứng dụng với push notification khi thiết kế và kiểm thử.
- Custom Backend Module chọn kênh bằng record ID của cùng Object `notification_channel` (không truyền kênh thì mọi hình thức gửi đều bật).
- Trước khi cấu hình node hoặc code backend: `$object-info` đọc schema và `$object-record` đọc bản ghi `notification_channel` trên Workspace đích; resolve đúng bản ghi `All`/`In app` và kiểm tra các trường kênh được tick. Không hardcode ID hoặc đoán slug của các trường kênh từ tên hiển thị; payload node theo `$process-creator`, lời gọi backend theo `$cogover-custom-module`.
- Project chưa có skill cho module cấu hình Notification độc lập; không suy đoán contract của module này.
- Nội dung phức tạp hoặc tái sử dụng: cân nhắc `$document-template` theo đúng phạm vi skill hỗ trợ.

## Mẫu văn bản

Template chèn dữ liệu động để tạo tài liệu nghiệp vụ như đề nghị, biên bản, hợp đồng, báo cáo hoặc email. `$document-template` khảo sát nguồn dữ liệu, tạo template, render thử và xác minh đầu ra. Không mặc định coi template tài liệu, email body trong Process và cấu hình email toàn workspace là cùng một loại tài nguyên.

## Quy tắc phân bổ

Assignment Rules phân bổ record mới theo điều kiện, nhóm nhân sự, lịch làm việc, round-robin hoặc tải công việc. Project chưa có skill chuyên trách đọc hay triển khai module này. Assignment Task trong `$process-creator` chỉ gán giá trị cho biến/process state theo contract của Process; nếu dùng Process để xây logic phân bổ thay thế, phải nêu rõ đây là giải pháp BPMN tùy chỉnh, xác minh race condition và không gọi nó là Assignment Rules của nền tảng.

## Tích hợp email

Gồm Workspace Email và Personal Email (email cá nhân nhân sự) để gửi/nhận email trực tiếp trong hệ thống và liên kết lịch sử với record. Project chưa có skill cấu hình tài khoản email ở hai cấp này. Send Email Task trong `$process-creator` chỉ bao phủ bước gửi email trong quy trình. Custom Backend Module gửi bằng `email.send` từ hộp thư dùng chung của Workspace hoặc hộp thư cá nhân của người khởi đầu thao tác, chỉ những hộp thư quản trị viên đã cho phép trong identity policy của Project, và có thể ghi email lên timeline record kèm file của record (theo `$cogover-custom-module`). Không khẳng định hai cách này thiết lập được mailbox, đồng bộ thư đến hoặc quản trị credential của Workspace/Personal Email.

## Report và Dashboard

Report biến dữ liệu Object thành bảng, nhóm, số liệu hoặc biểu đồ được lưu; Dashboard bố trí các report đã kiểm thử thành màn hình theo dõi. Thứ tự: `$report-builder` resolve Object, field, filter và tạo report → kiểm tra dữ liệu, filter, quyền và kết quả report → `$dashboard-builder` bố trí lên dashboard → `$app-menu-manager` nếu report/dashboard cần xuất hiện trong App menu.

## Cogover API

Cho hệ thống bên ngoài làm việc với tài nguyên Cogover. Hai họ endpoint với cơ chế xác thực khác nhau; luôn theo `$cogover-api-auth`, không dùng một API Token trực tiếp cho mọi endpoint:

| Họ endpoint | Cơ chế xác thực |
|---|---|
| `/bapi/v{N}/...` | API Key trong Bearer Authorization theo contract của `$cogover-api-auth` |
| `/api/v{N}/...` | Phiên Web App bằng cookie và CSRF/XSRF; có thể tạo phiên qua `/bapi/v1/auth-token` khi phù hợp |

Skill theo loại tác vụ: schema Object, field, option, Formula, lookup → `$object-info`; CRUD và query record → `$object-record`; App/menu → `$app-menu-manager`; Role, Personnel, Data Security → `$user-permission`; Process, report, dashboard và cấu hình khác → đúng skill chuyên trách, không tự suy ra endpoint.

Mỗi tích hợp phải xác minh endpoint, quyền, pagination, error handling, retry/idempotency và tác động đến Process/validation/security; không để credential trong repository hoặc log.

## Custom Backend Module

Logic nghiệp vụ phía server viết bằng TypeScript khi Object, Process hoặc API có sẵn chưa đáp ứng đủ. Module dùng dữ liệu và cơ chế quyền của Workspace: mặc định chạy với quyền của người gọi, không mặc nhiên vượt quyền dữ liệu; quyền hệ thống, quyền ủy quyền và hộp thư gửi email cần identity policy do quản trị viên duyệt cho từng version. Chọn loại module theo [Custom Module](../SKILL.md#custom-module); [$cogover-custom-module](../../cogover-custom-module/SKILL.md) khảo sát phần thiếu, thiết kế, lập trình, kiểm thử và publish, kể cả khi cần màn hình riêng gọi logic này.

| Khả năng | Dùng khi |
|---|---|
| HTTP route | API riêng cho frontend hoặc người dùng có phiên Workspace: tính giá, tổng hợp, ghi nhiều Object |
| Record trigger before-change | Kiểm tra hoặc điều chỉnh record trước khi lưu, áp cho mọi nguồn ghi (giao diện, API, import, Process, module khác) |
| Record trigger after-change | Xử lý tiếp ngay sau khi lưu: ghi record liên quan, gọi hệ thống ngoài, gửi thông báo |
| Background job | Việc nền chia trang, retry lỗi tạm thời, chạy trễ hoặc theo lịch cron do code quản lý |
| Inbound webhook | Hệ thống ngoài gọi vào không có phiên người dùng, xác thực bằng key hoặc chữ ký HMAC |
| Secret/credential, crypto | Gọi API ngoài có token mà code không thấy giá trị; băm, ký, mã hoá, xác minh chữ ký |
| Notification, email, push message | Báo người dùng việc cần xử lý, gửi email từ hộp thư Workspace, làm mới record hoặc hiện toast cho người đang mở |
| Cơ cấu tổ chức, role của người gọi | Chọn người duyệt theo chuỗi quản lý, kiểm tra ai quản lý ai hoặc thuộc phòng ban nào, giới hạn thao tác cho Super Admin hoặc role nhất định |

Chọn giữa Custom Backend Module và Process:

- **Custom Backend Module**: quy tắc bắt buộc áp cho mọi nguồn ghi, logic tính toán hoặc tích hợp phức tạp, retry và idempotency do code kiểm soát, webhook có xác thực, thông báo/email mà người nhận hoặc nội dung tính từ dữ liệu module.
- **Process** (`$process-creator`): luồng nhiều bước có người tham gia (User Task, chờ phê duyệt), chờ/hẹn giờ giữa các bước, gọi AI Agent, hoặc automation, lịch và thông báo mà người dùng muốn tự cấu hình trên giao diện không cần code.
- Chỉ nối Process với backend khi `$cogover-custom-module` và `$process-creator` xác nhận contract hỗ trợ cách nối và danh tính cần thiết. Không dùng record trigger và Triggered Flow cho cùng một quy tắc trên cùng Object, không dùng job theo lịch và Scheduled Flow cho cùng một việc, không gửi cùng một thông báo bằng cả hai; ghi rõ nơi xử lý khi thiết kế.
