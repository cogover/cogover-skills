# Tầng 2: Business Logic — Tổng quan và định tuyến

## Mục lục

1. [Nguyên tắc sử dụng](#nguyên-tắc-sử-dụng)
2. [Skill chuyên trách](#skill-chuyên-trách)
3. [Object Process](#object-process)
4. [Quản lý ứng dụng](#quản-lý-ứng-dụng)
5. [Vai trò và phân quyền](#vai-trò-và-phân-quyền)
6. [Thông báo](#thông-báo)
7. [Mẫu văn bản](#mẫu-văn-bản)
8. [Quy tắc phân bổ](#quy-tắc-phân-bổ)
9. [Tích hợp email](#tích-hợp-email)
10. [Report và Dashboard](#report-và-dashboard)
11. [Cogover API](#cogover-api)
12. [Custom Backend Module](#custom-backend-module)

## Nguyên tắc sử dụng

Tầng 2 kết hợp dữ liệu và giao diện của Tầng 1 thành logic vận hành: quy trình, quyền, menu, tài liệu, báo cáo và tích hợp. File này chỉ mô tả phạm vi và chọn đúng skill; contract triển khai trong skill chuyên trách mới là nguồn chuẩn.

- Với workspace hiện có, đọc state thật trước khi thiết kế hoặc thay đổi.
- Giữ nguyên cấu hình ngoài phạm vi; ưu tiên merge có chủ đích thay vì thay toàn bộ.
- Không sao chép endpoint hoặc payload từ overview.
- Sau thay đổi, đọc lại state và chạy một kịch bản nghiệp vụ tiêu biểu.

## Skill chuyên trách

| Nhu cầu | Skill nguồn chuẩn |
|---|---|
| Thiết kế, tạo, kích hoạt và kiểm thử BPMN | [$process-creator](../../process-creator/SKILL.md) |
| Tạo App, menu, menu group, ACL và cấu hình hiển thị | [$app-menu-manager](../../app-menu-manager/SKILL.md) |
| Chọn icon cho App hoặc menu | [$cogover-icon](../../cogover-icon/SKILL.md) |
| User, Personnel, Department, Position, Role, permission và Data Security | [$user-permission](../../user-permission/SKILL.md) |
| Tạo và kiểm thử mẫu văn bản | [$document-template](../../document-template/SKILL.md) |
| Tạo saved report | [$report-builder](../../report-builder/SKILL.md) |
| Tạo dashboard từ report | [$dashboard-builder](../../dashboard-builder/SKILL.md) |
| Xác thực đúng theo họ endpoint | [$cogover-api-auth](../../cogover-api-auth/SKILL.md) |
| Object schema và Object records qua API | [$object-info](../../object-info/SKILL.md), [$object-record](../../object-record/SKILL.md) |
| Logic phía server, API riêng hoặc kết hợp backend với giao diện riêng | [$cogover-custom-module](../../cogover-custom-module/SKILL.md) |

Project chưa có skill độc lập cho Notification configuration, Assignment Rules và Workspace/Personal Email configuration. Các task gửi thông báo, gửi email hoặc gán giá trị bên trong Process vẫn thuộc `$process-creator`, nhưng không được xem là thay thế cho ba module cấu hình độc lập này.

## Object Process

Cogover hỗ trợ năm loại quy trình. Chọn loại theo cơ chế khởi chạy, sau đó dùng `$process-creator` để đọc support matrix, dựng JSON BPMN, triển khai và kiểm thử.

### Năm loại quy trình

| Loại | Cơ chế khởi chạy | Trường hợp phù hợp |
|---|---|---|
| **Manual Flow** (`manual_flow`) | Người dùng submit Root User Task | Đề nghị mua sắm, xin nghỉ phép, yêu cầu thanh toán |
| **Normal Flow** (`normal_flow`) | Người có quyền chủ động chạy; không bắt buộc Root form | Quy trình chạy trực tiếp từ Start đến action, gateway hoặc End |
| **Scheduled Flow** (`scheduled_flow`) | Lịch hoặc cron | Nhắc hạn, kiểm tra SLA, tổng hợp định kỳ |
| **Triggered Flow** (`triggered_flow`) | Record create/update/delete hoặc webhook theo contract | Phản ứng khi dữ liệu thay đổi hoặc nhận yêu cầu tích hợp |
| **Sequence Flow** (`sequence_flow`) | Liên kết record với một chuỗi bước tuần tự | Nurture Lead, onboarding hoặc follow-up theo record |

Chỉ Manual Flow bắt buộc Root User Task làm form khởi tạo. Không áp quy tắc này cho Normal, Scheduled, Triggered hoặc Sequence Flow.

### Thành phần tiêu biểu

Một Process có thể dùng các nhóm node sau; danh sách thực tế phải lấy từ `$process-creator`:

- Điều khiển luồng: Start/End, Exclusive/Inclusive/Parallel Gateway, Loop, Wait, Sub Process.
- Tương tác người dùng: User Task, To Do, Phone Call.
- Dữ liệu và biến: Variable, Assignment, Get/Create/Update Record, Organization.
- Giao tiếp và tích hợp: Send Email, Send Notification, Send HTTP Request, Omni Message.
- Đầu ra: Export Record và các resource/template liên quan.

### Trình tự thiết kế

1. Chốt mục tiêu, sự kiện bắt đầu và tiêu chí kết thúc.
2. Chọn một trong năm loại Flow.
3. Xác định actor, quyền chạy/xem/hủy và các nhánh ngoại lệ.
4. Resolve Object, field, option, Personnel/Role và resource thật.
5. Thiết kế happy path, timeout, retry, lỗi và idempotency nếu có tích hợp.
6. Dựng Process bằng `$process-creator`, kiểm tra tính hợp lệ rồi kích hoạt.
7. Chạy thử một instance, xác minh task, record, thông báo và quyền truy cập.

### Ví dụ định hướng

Quy trình xin nghỉ phép thường là Manual Flow: Root form → xác định cấp duyệt → User Task phê duyệt → cập nhật record → gửi kết quả. Tự động phản ứng khi một Lead được tạo thường là Triggered Flow: trigger record → tìm/gán nguồn lực theo logic đã xác nhận → cập nhật record → gửi thông báo.

## Quản lý ứng dụng

App gom các Object, saved filter, report, dashboard và trang liên quan thành cấu trúc menu dành cho một nhóm người dùng.

```
App
├── Menu item → Object hoặc saved filter
├── Menu group
│   ├── Submenu → Report
│   └── Submenu → Dashboard
└── Menu item → Trang được hỗ trợ khác
```

Dùng `$app-menu-manager` để snapshot cấu trúc hiện có, tạo hoặc cập nhật App/menu và kiểm tra ACL. Dùng `$cogover-icon` khi cần chọn icon hợp lệ. Không hardcode menu target hoặc ID từ overview.

## Vai trò và phân quyền

Quyền cần được thiết kế theo nhiều lớp:

1. Quyền truy cập App/menu.
2. Quyền chức năng trên Object, ví dụ Create/Read/Update/Delete theo contract.
3. Data Security ở cấp record theo owner, cơ cấu tổ chức, Role hoặc điều kiện nghiệp vụ.
4. Quyền Process như khởi chạy, xem tiến độ, xử lý task hoặc hủy instance.

Dùng `$user-permission` cho User, Personnel, Department, Position, Role, Object permission và Data Security. Khi App hoặc Process có ACL riêng, phối hợp thêm skill tương ứng. Nghiệm thu bằng ít nhất một tài khoản được phép và một tài khoản bị từ chối.

## Thông báo

Thông báo thường phát sinh từ một sự kiện như record mới, đổi trạng thái, đến hạn hoặc kết quả phê duyệt. Thiết kế cần xác định rõ sự kiện, người nhận, nội dung, kênh và chống gửi lặp.

- Nếu thông báo là một bước trong BPMN, dùng Send Notification/Send Email theo `$process-creator`.
- Node **Send Notification** có thể gửi thông báo đến ứng dụng Cogover trên Android/iOS khi chọn **Loại thông báo** là **All** hoặc **In app**. `All` và `In app` là hai bản ghi của Object `notification_channel`; kênh nhận được quyết định bởi các trường tương ứng được tick trên bản ghi đó.
- Khi trường **mobile push** được tick, người nhận nhận thêm thông báo đẩy trên thiết bị mobile, kể cả khi không mở ứng dụng. Phân biệt thông báo trong ứng dụng với push notification khi thiết kế và kiểm thử.
- Trước khi cấu hình node, dùng `$object-info` đọc schema và `$object-record` đọc bản ghi `notification_channel` trên Workspace đích; resolve đúng bản ghi `All`/`In app` và kiểm tra các trường kênh được tick. Không hardcode ID hoặc đoán slug của các trường kênh từ tên hiển thị; dùng `$process-creator` cho payload node.
- Project chưa có skill cho module cấu hình Notification độc lập; không suy đoán contract của module này.
- Nếu nội dung phức tạp hoặc tái sử dụng, cân nhắc `$document-template` theo đúng phạm vi được skill hỗ trợ.

## Mẫu văn bản

Mẫu văn bản dùng dữ liệu động để tạo tài liệu nghiệp vụ như đề nghị, biên bản hoặc hợp đồng. Dùng `$document-template` để khảo sát nguồn dữ liệu, tạo template, render thử và xác minh đầu ra. Không mặc định coi template tài liệu, email body trong Process và cấu hình email toàn workspace là cùng một loại tài nguyên.

## Quy tắc phân bổ

Assignment Rules là module phân bổ record theo điều kiện, nhóm nhân sự, lịch hoặc tải công việc. Project chưa có skill chuyên trách để đọc hay triển khai module này.

Assignment Task trong `$process-creator` chỉ gán giá trị cho biến/process state theo contract của Process. Nếu dùng Process để xây logic phân bổ thay thế, phải mô tả rõ đây là giải pháp BPMN tùy chỉnh, xác minh race condition và không gọi nó là Assignment Rules của nền tảng.

## Tích hợp email

Tích hợp email có thể gồm Workspace Email và Personal Email, phục vụ gửi/nhận và liên kết lịch sử với record. Project chưa có skill chuyên trách cho cấu hình tài khoản email ở hai cấp này.

Send Email Task trong `$process-creator` chỉ bao phủ bước gửi email trong quy trình. Không khẳng định task này có thể thiết lập mailbox, đồng bộ thư đến hoặc quản trị credential của Workspace/Personal Email.

## Report và Dashboard

Report biến dữ liệu Object thành bảng, nhóm, số liệu hoặc biểu đồ được lưu; Dashboard bố trí các report đã kiểm thử thành màn hình theo dõi.

1. Dùng `$report-builder` resolve Object, field, filter và tạo report.
2. Kiểm tra dữ liệu, filter, quyền và kết quả report trước.
3. Chỉ sau đó dùng `$dashboard-builder` để bố trí các report lên dashboard.
4. Dùng `$app-menu-manager` nếu report/dashboard cần xuất hiện trong App menu.

## Cogover API

Cogover có hai họ endpoint với cơ chế xác thực khác nhau. Luôn dùng `$cogover-api-auth`; không dùng một API Token trực tiếp cho mọi endpoint.

| Họ endpoint | Cơ chế xác thực |
|---|---|
| `/bapi/v{N}/...` | API Key trong Bearer Authorization theo contract của `$cogover-api-auth` |
| `/api/v{N}/...` | Phiên Web App bằng cookie và CSRF/XSRF; có thể tạo phiên qua `/bapi/v1/auth-token` khi phù hợp |

Phân công skill theo loại tác vụ:

- Schema Object, field, option, Formula và lookup: `$object-info`.
- CRUD và query record: `$object-record`.
- App/menu: `$app-menu-manager`.
- Role, Personnel và Data Security: `$user-permission`.
- Process, report, dashboard và các cấu hình khác: dùng đúng skill chuyên trách; không tự suy ra endpoint.

Mỗi tích hợp cần xác minh endpoint, quyền, pagination, error handling, retry/idempotency, tác động đến Process/validation/security và không để credential trong repository hoặc log.

## Custom Backend Module

Custom Backend Module bổ sung logic phía server khi Object, Process hoặc API có sẵn chưa đáp ứng đủ: tính giá, tổng hợp/ghi dữ liệu Object, cung cấp API riêng hoặc xử lý tích hợp có thông tin bí mật. Module tiếp tục sử dụng dữ liệu và cơ chế quyền của Workspace; chạy ở backend không mặc nhiên vượt quyền dữ liệu.

Dùng [$cogover-custom-module](../../cogover-custom-module/SKILL.md) để khảo sát phần thiếu, thiết kế, lập trình, kiểm thử và publish. Khi cần màn hình riêng gọi logic này, dùng cùng skill để triển khai cả frontend và backend. Với sự kiện record hoặc lịch chạy, phối hợp Process theo contract được hỗ trợ; không mặc định backend tự đăng ký trigger hoặc lịch.
