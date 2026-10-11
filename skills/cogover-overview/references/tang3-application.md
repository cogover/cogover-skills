# Tầng 3: Application

Tầng 3 là lớp ứng dụng nghiệp vụ lắp ghép từ Object, Layout, rule, Process, permission, report, dashboard và App menu của hai tầng dưới. Object và quy trình nêu trong file này là **mô hình tham khảo**, không phải cam kết mọi workspace đã có sẵn cùng tên hoặc cùng schema. Trước khi hướng dẫn hoặc triển khai: `$app-menu-manager` đọc App/menu hiện có, `$object-info` đọc Object/field thật, rồi chỉ gọi các skill chuyên trách cần cho change set đã xác định.

Project chưa có skill chuyên biệt để triển khai nghiệp vụ đóng gói riêng của Omni Channel, Sales, Finance, Inventory, Service, Manufacture hoặc Goal. Với Sales, Finance, Inventory, Manufacture và Omni Channel, dùng danh mục tính năng chuẩn (link ở từng mục) để hiểu phạm vi nghiệp vụ và tên Object; vẫn phải đọc state và contract thật của workspace trước khi thay đổi. Nền tảng chung thiết kế bằng các skill Object/Layout/Process/Permission/Report/Dashboard/App Menu; không suy đoán contract triển khai.

## Sales (CRM)

Vòng đời từ khách hàng tiềm năng đến khách hàng, cơ hội, hợp đồng và chăm sóc sau bán: hồ sơ khách hàng và người liên hệ; lead, cơ hội, đối thủ và đối tác; báo giá, hợp đồng, sản phẩm, bảng giá và đơn bán hàng; yêu cầu hỗ trợ (ticket); chiến dịch tiếp thị; nhóm đơn vị tính và đơn vị tính. Danh mục [tính năng Sales](sales-app-features.md): tính năng, vị trí trong menu và Object liên quan.

`$object-info` xác minh Object, field và option trạng thái thật; `$object-transition-rule`, `$process-creator`, `$report-builder` và `$dashboard-builder` khi cần kiểm soát lifecycle, tự động hóa hoặc phân tích pipeline.

## Inventory (WMS)

Danh mục hàng hóa, đơn vị tính, kho, giao dịch nhập/xuất và số liệu tồn: cấu hình kho, vị trí và tuyến cung ứng; theo dõi tồn theo số lượng/lô/serial; đơn vị tính và combo; vòng đời phiếu nhập/xuất/điều chuyển; phân bổ FIFO/LIFO/FEFO; nhập Excel; đồng bộ đơn hàng; kiểm kê; tổng hợp tồn; sổ kho; định giá và báo cáo. Danh mục [tính năng Inventory](inventory-app-features.md).

Thiết kế phải xác định rõ cách tính tồn, thời điểm ghi nhận, đơn vị quy đổi, âm kho, điều chỉnh và tính nhất quán khi nhiều giao dịch chạy đồng thời. Không mặc định "tồn kho thời gian thực" chỉ bằng một Formula; chọn Process và report sau khi chốt nguồn sự thật.

## People (HRM)

Khai thác cơ cấu Personnel, Department và Position để vận hành hồ sơ nhân sự và các quy trình nội bộ. `$user-permission` cho cơ cấu tổ chức, User, Personnel, Department, Position và Role; Object nghiệp vụ như Employee profile, Leave request, Expense claim hoặc Onboarding task tạo bằng `$object-info`; `$process-creator` cho xin nghỉ, onboarding, offboarding hoặc phê duyệt. Không giả định Object hệ thống sửa được schema giống Object nghiệp vụ; đọc contract của skill tương ứng.

## Process (BPM)

Thiết kế, kích hoạt, theo dõi và kiểm thử quy trình bằng BPMN với Manual, Normal, Scheduled, Triggered và Sequence Flow ([Object Process ở Tầng 2](tang2-business-logic.md#object-process)). `$process-creator` là nguồn chuẩn cho node, resource, permission và payload; Process đưa vào một App nghiệp vụ thì phối hợp `$app-menu-manager` và `$user-permission` kiểm tra khả năng truy cập.

## Omni Channel

Quản lý tin nhắn đa kênh tập trung (chat nội bộ, Live Chat, Facebook, Zalo OA, WhatsApp, TikTok và AI Chat): hợp nhất nhiều kênh chat; vòng đời, thành viên và hồ sơ khách hàng của hội thoại; chuyển người phụ trách và hàng đợi; AI Agent; danh sách và phân quyền; nhãn, chưa đọc và lịch sử; nhắn tin đa định dạng, tương tác và tìm kiếm; nghiệp vụ Facebook; xem tệp an toàn; cập nhật thời gian thực và thông báo đa thiết bị. Danh mục [tính năng Omni Channel](omni-channel-app-features.md): kênh, thao tác, luồng hội thoại và Object liên quan.

Omni Message trong `$process-creator` là một node Process được hỗ trợ; không đồng nhất node này với toàn bộ hộp thư Omni Channel. Đọc state và contract thật trước khi cấu hình kết nối kênh hoặc nghiệp vụ inbox.

## Finance

Kiểm soát tài chính, ngân sách và báo cáo: hóa đơn khách hàng và nhà cung cấp, mua hàng và đề nghị thanh toán, phiếu thu/chi, lịch thanh toán, đặt cọc, công nợ, tạm ứng/quyết toán, kiểm soát ngân sách, dự báo dòng tiền, sao kê và một số tiện ích tích hợp. Danh mục [tính năng Finance](finance-app-features.md).

Danh mục không thay thế contract API, state workspace, hệ thống kế toán hoặc yêu cầu tuân thủ chuyên ngành; xác minh scope, chuẩn dữ liệu và tích hợp trước khi triển khai.

## Service (Contact Center, Call Center)

Tiếp nhận, định tuyến và theo dõi tương tác khách hàng. Khung thiết kế tham khảo: Object Queue, Interaction/Call, Customer, Agent assignment, Ticket, SLA và Disposition; logic phân loại nhu cầu, gán agent, chuyển tuyến, follow-up, escalation và đóng yêu cầu; giao diện hàng đợi, màn hình tương tác, lịch sử khách hàng và danh sách việc cần làm; phân tích thời gian chờ, thời gian xử lý, tỷ lệ bỏ cuộc, SLA và kết quả xử lý. Tích hợp tổng đài, routing thời gian thực và media cần contract chuyên biệt; các skill chung chỉ bao phủ phần Object/Layout/Process/Permission/Report/App.

## Manufacture

Kế hoạch sản xuất, nguyên vật liệu và định mức: BOM nhiều cấp; tạo và điều phối lệnh sản xuất; nguyên vật liệu theo lô/serial; cấp phát, tiêu thụ, công đoạn, sản lượng và nhập thành phẩm; lệnh sửa chữa và luồng linh kiện. Bản chuẩn còn có tiện ích nhập đơn Shopee, tự động xử lý đóng gói/hóa đơn, đối soát thu hộ, tạo phiếu thu, nhập bảng giá và xuất mẫu serial nhập kho. Danh mục [tính năng Manufacture](manufacture-app-features.md).

Phải chốt đơn vị tính, phiên bản BOM, truy xuất lô/serial, cách ghi nhận dở dang và tích hợp kho trước khi thay đổi cấu hình.

## Goal

Thiết lập, theo dõi và đo lường mục tiêu theo thời gian thực với chỉ số minh bạch. Khung tham khảo: Object Goal, Key result, Measurement, Check-in, Period, Owner và Alignment relation; logic thiết lập mục tiêu, phê duyệt, check-in định kỳ, cập nhật tiến độ, cảnh báo trễ và đóng kỳ; quyền phân biệt mục tiêu cá nhân, nhóm, đơn vị và phạm vi công khai/hạn chế; phân tích tiến độ theo kỳ, mục tiêu có rủi ro, mức độ liên kết và lịch sử check-in. Chốt công thức tiến độ, đơn vị đo, nguồn cập nhật và quy tắc roll-up trước khi thiết kế Formula/report.

## Các miền mở rộng

Hướng giải pháp có thể mô hình hóa; không phải bằng chứng workspace đích đã có module hoặc kết nối chuyên biệt.

| Miền | Phạm vi mô hình tham khảo |
|---|---|
| Order Management | Đơn hàng, dòng hàng, trạng thái xử lý, giao nhận và hoàn tất |
| Warranty | Gói bảo hành, tài sản/sản phẩm, yêu cầu và lịch sử xử lý |
| Reseller | Đại lý, nhóm/chính sách, đơn hàng và công nợ nghiệp vụ |
| E-Commerce | Đơn sàn, dòng hàng, tồn, giao dịch và đối soát |
| Purchasing | Yêu cầu mua, nhà cung cấp, PO, nhận hàng và đối chiếu |
| Ticket | Tiếp nhận, phân loại, phân bổ, SLA, escalation và đóng phiếu |
| Task | Công việc, người thực hiện, deadline, trạng thái và tiến độ |

Kết nối vận chuyển, mạng xã hội, email/SMS, portal hoặc tích hợp mobile ngoài ứng dụng Cogover chuẩn phải xác minh riêng; không khẳng định connector có sẵn nếu project chưa có skill hoặc contract tương ứng. Khả năng của ứng dụng mobile chuẩn: [Ứng dụng mobile Android và iOS](../SKILL.md#ứng-dụng-mobile-android-và-ios).

## Custom Frontend Module

Màn hình hoặc trải nghiệm riêng cho ứng dụng, ví dụ màn hình tra cứu, biểu mẫu nghiệp vụ hoặc báo cáo tùy chỉnh. Chọn frontend thuần hay kết hợp Custom Backend Module theo [Custom Module](../SKILL.md#custom-module); [$cogover-custom-module](../../cogover-custom-module/SKILL.md) khảo sát, thiết kế, lập trình, kiểm thử và publish cả hai lựa chọn. Link frontend yêu cầu phiên đăng nhập Workspace; không đặt secret trong mã frontend. Nếu chỉ cần thay đổi layout của Object, dùng `$object-layout` và `$layout-scripting`.
