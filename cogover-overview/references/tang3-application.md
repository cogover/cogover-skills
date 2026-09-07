# Tầng 3: Application — Tổng quan các miền ứng dụng

## Mục lục

1. [Cách sử dụng tài liệu](#cách-sử-dụng-tài-liệu)
2. [Sales](#sales--quản-lý-quan-hệ-khách-hàng)
3. [Inventory](#inventory--quản-lý-kho)
4. [People](#people--quản-lý-nhân-sự)
5. [Process](#process--quản-lý-quy-trình)
6. [Omni Channel](#omni-channel--quản-lý-tin-nhắn-đa-kênh)
7. [Finance](#finance--quản-lý-tài-chính)
8. [Service](#service--contact-center-và-call-center)
9. [Manufacture](#manufacture--quản-lý-sản-xuất)
10. [Goal](#goal--quản-lý-mục-tiêu)
11. [Các miền mở rộng](#các-miền-mở-rộng)
12. [Custom Frontend Module](#custom-frontend-module)

## Cách sử dụng tài liệu

Tầng 3 là lớp ứng dụng nghiệp vụ được lắp ghép từ Object, Layout, rule, Process, permission, report, dashboard và App menu của hai tầng dưới.

Các Object và quy trình trong file này là **mô hình tham khảo**, không phải cam kết rằng mọi workspace đã có sẵn cùng tên hoặc cùng schema. Trước khi hướng dẫn hoặc triển khai:

1. Dùng [$app-menu-manager](../../app-menu-manager/SKILL.md) đọc App/menu hiện có.
2. Dùng [$object-info](../../object-info/SKILL.md) đọc Object/field thật.
3. Chỉ gọi các skill chuyên trách cần cho change set đã xác định.

Project chưa có skill chuyên biệt để triển khai nghiệp vụ đóng gói riêng của Omni Channel, Sales, Finance, Inventory, Service, Manufacture hoặc Goal. Với Sales, Finance, Inventory, Manufacture và Omni Channel, dùng danh mục tính năng chuẩn được liên kết bên dưới để hiểu phạm vi nghiệp vụ và tên Object; vẫn phải đọc state và contract thật của workspace trước khi thay đổi. Có thể thiết kế nền tảng chung bằng các skill Object/Layout/Process/Permission/Report/Dashboard/App Menu, nhưng không suy đoán contract triển khai.

## Sales — Quản lý quan hệ khách hàng

### Mục tiêu

Quản lý vòng đời từ khách hàng tiềm năng đến khách hàng, cơ hội, hợp đồng và chăm sóc sau bán.

### Phạm vi chuẩn

App chuẩn bao phủ hồ sơ khách hàng và người liên hệ; lead, cơ hội, đối thủ và đối tác; báo giá, hợp đồng, sản phẩm, bảng giá và đơn bán hàng; yêu cầu hỗ trợ; chiến dịch tiếp thị; nhóm đơn vị tính và đơn vị tính.

Đọc đầy đủ [Danh sách tính năng chuẩn của Sales](sales-app-features.md) khi cần trả lời app có tính năng gì, xác định vị trí trong menu hoặc tra cứu các Object liên quan. Dùng `$object-info` để xác minh Object, field và option trạng thái thật; dùng `$object-transition-rule`, `$process-creator`, `$report-builder` và `$dashboard-builder` khi cần kiểm soát lifecycle, tự động hóa hoặc phân tích pipeline.

## Inventory — Quản lý kho

### Mục tiêu

Quản lý danh mục hàng hóa, đơn vị tính, kho, giao dịch nhập/xuất và số liệu tồn.

### Phạm vi chuẩn

App chuẩn bao phủ cấu hình kho, vị trí và tuyến cung ứng; theo dõi tồn theo số lượng/lô/serial; đơn vị tính và combo; vòng đời phiếu nhập/xuất/điều chuyển; phân bổ FIFO/LIFO/FEFO; nhập Excel; đồng bộ đơn hàng; kiểm kê; tổng hợp tồn; sổ kho; định giá và báo cáo.

Đọc đầy đủ [Danh sách tính năng chuẩn của Inventory](inventory-app-features.md) khi cần trả lời app có tính năng gì, phân tích một luồng Inventory hoặc xác định các Object liên quan. Thiết kế vẫn phải xác định rõ cách tính tồn, thời điểm ghi nhận, đơn vị quy đổi, âm kho, điều chỉnh và tính nhất quán khi nhiều giao dịch chạy đồng thời. Không mặc định “tồn kho thời gian thực” chỉ bằng một Formula; chọn Process và report sau khi chốt nguồn sự thật.

## People — Quản lý nhân sự

### Mục tiêu

Khai thác cơ cấu Personnel, Department và Position để vận hành hồ sơ nhân sự và các quy trình nội bộ.

### Mô hình tham khảo

- Dùng `$user-permission` cho cơ cấu tổ chức, User, Personnel, Department, Position và Role.
- Có thể tạo Object nghiệp vụ như Employee profile, Leave request, Expense claim hoặc Onboarding task bằng `$object-info`.
- Dùng `$process-creator` cho xin nghỉ, onboarding, offboarding hoặc phê duyệt.
- Không giả định Object hệ thống có thể sửa schema giống Object nghiệp vụ; đọc contract của skill tương ứng.

## Process — Quản lý quy trình

### Mục tiêu

Thiết kế, kích hoạt, theo dõi và kiểm thử quy trình nghiệp vụ bằng BPMN.

Cogover hỗ trợ Manual, Normal, Scheduled, Triggered và Sequence Flow. Dùng `$process-creator` làm nguồn chuẩn cho node, resource, permission và payload. Nếu Process được đưa vào một App nghiệp vụ, phối hợp `$app-menu-manager` và `$user-permission` để kiểm tra khả năng truy cập.

## Omni Channel — Quản lý tin nhắn đa kênh

### Mục tiêu

Giải pháp quản lý tin nhắn đa kênh tập trung từ WhatsApp, Zalo OA và Facebook.

### Phạm vi chuẩn

App chuẩn bao phủ hợp nhất nhiều kênh chat; vòng đời, thành viên và hồ sơ khách hàng của hội thoại; chuyển người phụ trách và hàng đợi; AI Agent; danh sách và phân quyền; nhãn, chưa đọc và lịch sử; nhắn tin đa định dạng, tương tác và tìm kiếm; nghiệp vụ Facebook; xem tệp an toàn; cập nhật thời gian thực và thông báo đa thiết bị.

Đọc đầy đủ [Danh sách tính năng chuẩn của Omni Channel](omni-channel-app-features.md) khi cần trả lời app hỗ trợ kênh hoặc thao tác nào, phân tích một luồng hội thoại hoặc xác định các Object liên quan. Omni Message trong `$process-creator` là một node Process được hỗ trợ; không đồng nhất node này với toàn bộ hộp thư Omni Channel. Đọc state và contract thật trước khi cấu hình kết nối kênh hoặc nghiệp vụ inbox.

## Finance — Quản lý tài chính

### Mục tiêu

Kiểm soát tài chính minh bạch, lập ngân sách và báo cáo chính xác để ra quyết định chiến lược.

### Phạm vi chuẩn

App chuẩn bao phủ hóa đơn khách hàng và nhà cung cấp, mua hàng và đề nghị thanh toán, phiếu thu/chi, lịch thanh toán, đặt cọc, công nợ, tạm ứng/quyết toán, kiểm soát ngân sách, dự báo dòng tiền, sao kê và một số tiện ích tích hợp.

Đọc đầy đủ [Danh sách tính năng chuẩn của Finance](finance-app-features.md) khi cần trả lời app có tính năng gì, phân tích một luồng Finance hoặc xác định các Object liên quan. Danh mục này không thay thế contract API, state workspace, hệ thống kế toán hoặc yêu cầu tuân thủ chuyên ngành; xác minh scope, chuẩn dữ liệu và tích hợp trước khi triển khai.

## Service — Contact Center và Call Center

### Mục tiêu

Phần mềm Contact Center, Call Center phục vụ tiếp nhận, định tuyến và theo dõi tương tác khách hàng.

### Khung thiết kế tham khảo

- Object: Queue, Interaction/Call, Customer, Agent assignment, Ticket, SLA và Disposition.
- Logic: phân loại nhu cầu, gán agent, chuyển tuyến, follow-up, escalation và đóng yêu cầu.
- Giao diện: hàng đợi, màn hình tương tác, lịch sử khách hàng và danh sách việc cần làm.
- Phân tích: thời gian chờ, thời gian xử lý, tỷ lệ bỏ cuộc, SLA và kết quả xử lý.

Tích hợp tổng đài, routing thời gian thực và media cần contract chuyên biệt; các skill chung chỉ bao phủ phần Object/Layout/Process/Permission/Report/App.

## Manufacture — Quản lý sản xuất

### Mục tiêu

Lập kế hoạch sản xuất, quản lý nguyên vật liệu và định mức sản xuất.

### Phạm vi chuẩn

App chuẩn bao phủ BOM nhiều cấp; tạo và điều phối lệnh sản xuất; quản lý nguyên vật liệu theo lô/serial; cấp phát, tiêu thụ, công đoạn, sản lượng và nhập thành phẩm; lệnh sửa chữa và luồng linh kiện. Bản chuẩn còn bao gồm tiện ích nhập đơn Shopee, tự động xử lý đóng gói/hóa đơn, đối soát thu hộ, tạo phiếu thu, nhập bảng giá và xuất mẫu serial nhập kho.

Đọc đầy đủ [Danh sách tính năng chuẩn của Manufacture](manufacture-app-features.md) khi cần trả lời app có tính năng gì, phân tích một luồng sản xuất/sửa chữa hoặc xác định các Object liên quan. Phải chốt đơn vị tính, phiên bản BOM, truy xuất lô/serial, cách ghi nhận dở dang và tích hợp kho trước khi thay đổi cấu hình.

## Goal — Quản lý mục tiêu

### Mục tiêu

Thiết lập, theo dõi và đo lường mục tiêu theo thời gian thực với chỉ số minh bạch.

### Khung thiết kế tham khảo

- Object: Goal, Key result, Measurement, Check-in, Period, Owner và Alignment relation.
- Logic: thiết lập mục tiêu, phê duyệt, check-in định kỳ, cập nhật tiến độ, cảnh báo trễ và đóng kỳ.
- Quyền: phân biệt mục tiêu cá nhân, nhóm, đơn vị và phạm vi công khai/hạn chế.
- Phân tích: tiến độ theo kỳ, mục tiêu có rủi ro, mức độ liên kết và lịch sử check-in.

Phải chốt công thức tiến độ, đơn vị đo, nguồn cập nhật và quy tắc roll-up trước khi thiết kế Formula/report.

## Các miền mở rộng

Cogover có thể được mô hình hóa cho các miền như Order Management, Warranty, Reseller, E-Commerce, Purchasing, Ticket và Task Management. Đây là các hướng giải pháp, không phải bằng chứng rằng workspace đích đã có đủ module hoặc kết nối chuyên biệt.

| Miền | Phạm vi mô hình tham khảo |
|---|---|
| Order Management | Đơn hàng, dòng hàng, trạng thái xử lý, giao nhận và hoàn tất |
| Warranty | Gói bảo hành, tài sản/sản phẩm, yêu cầu và lịch sử xử lý |
| Reseller | Đại lý, nhóm/chính sách, đơn hàng và công nợ nghiệp vụ |
| E-Commerce | Đơn sàn, dòng hàng, tồn, giao dịch và đối soát |
| Purchasing | Yêu cầu mua, nhà cung cấp, PO, nhận hàng và đối chiếu |
| Ticket | Tiếp nhận, phân loại, phân bổ, SLA, escalation và đóng phiếu |
| Task | Công việc, người thực hiện, deadline, trạng thái và tiến độ |

Các kết nối vận chuyển, mạng xã hội, email/SMS, portal hoặc mobile app cần được xác minh riêng. Không khẳng định connector có sẵn nếu project chưa có skill hoặc contract tương ứng.

## Custom Frontend Module

Custom Frontend Module bổ sung màn hình hoặc trải nghiệm riêng cho ứng dụng, ví dụ màn hình tra cứu, biểu mẫu nghiệp vụ hoặc báo cáo tùy chỉnh. Chọn frontend thuần khi API hiện có đáp ứng dữ liệu và logic với quyền người dùng; kết hợp Custom Backend Module khi màn hình cần logic phía server hoặc API riêng.

Dùng [$cogover-custom-module](../../cogover-custom-module/SKILL.md) để khảo sát, thiết kế, lập trình, kiểm thử và publish cả hai lựa chọn. Link frontend yêu cầu phiên đăng nhập Workspace; không đặt secret trong mã frontend. Nếu yêu cầu chỉ là thay đổi layout của Object, dùng `$object-layout` và `$layout-scripting` theo phạm vi tương ứng.
