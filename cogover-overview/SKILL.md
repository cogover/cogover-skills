---
name: cogover-overview
description: "Cung cấp kiến thức tổng quan về Cogover Platform, kiến trúc 3 tầng, danh mục tính năng chuẩn của Sales, Finance, Inventory, Manufacture và Omni Channel, khả năng mở rộng bằng Custom Frontend/Backend Module và bản đồ skill chuyên trách. Dùng khi người dùng hỏi Cogover/App chuẩn có thể làm gì, cần hiểu một capability hoặc chọn skill phù hợp. Chuyển yêu cầu tạo/sửa Custom Module sang $cogover-custom-module; dự án App end-to-end từ BRD/SRS, fit-gap, thiết kế dữ liệu đến triển khai thuộc $build-cogover-app."
metadata:
  author: cogover
  version: "1.1.2"
---

# Tổng quan Cogover Platform

- **Phiên bản:** `1.1.2`
- **Ngày phát hành:** `2026-09-11`

## Vai trò của skill

Dùng skill này làm điểm vào và bản đồ điều phối cho mọi bài toán Cogover. Trước tiên xác định yêu cầu thuộc tầng nào, đọc reference tổng quan phù hợp, rồi gọi skill chuyên trách trong project để đọc state thật, thực hiện thay đổi và xác minh.

- Không sao chép contract API hoặc hướng dẫn thao tác chi tiết từ overview khi skill chuyên trách đã là nguồn chuẩn.
- Với ứng dụng hiện có, luôn khảo sát state thật trước, giữ cấu hình ngoài phạm vi và xác minh sau thay đổi.
- Với ứng dụng mới, luôn thiết kế nghiệp vụ và mô hình dữ liệu trước khi tạo cấu hình trên workspace.
- Với yêu cầu tạo hoặc sửa Custom Frontend Module, Custom Backend Module hay cả hai, chuyển trực tiếp sang [$cogover-custom-module](../cogover-custom-module/SKILL.md). Skill đó điều phối khảo sát, thiết kế, lập trình, kiểm thử và publish; khi được gọi để cung cấp kiến thức nền cho Custom Module, overview không chuyển vòng sang `$build-cogover-app`.
- Với dự án end-to-end bắt đầu từ BRD/SRS, cần fit-gap, tư vấn App, thiết kế dữ liệu, lập plan hoặc triển khai nhiều loại cấu hình, giao orchestration cho [$build-cogover-app](../build-cogover-app/SKILL.md); overview chỉ cung cấp kiến thức nền và bản đồ skill để tránh vòng điều phối.

## Tổng quan kiến trúc

Cogover Platform là nền tảng low-code/no-code giúp doanh nghiệp số hoá và quản lý toàn bộ hoạt động kinh doanh. Nền tảng được thiết kế theo kiến trúc 3 tầng, mỗi tầng xây dựng trên tầng bên dưới:

**Tầng 1 — Object Manager (Quản lý đối tượng dữ liệu)**
Là nền tảng cốt lõi, biến mọi loại dữ liệu thành Object có cấu trúc — tương tự Database nhưng đi kèm giao diện trực quan, phân quyền sẵn, và nhiều module quản trị mạnh mẽ. Đây là tầng quan trọng nhất, mọi thứ bắt đầu từ đây.

**Tầng 2 — Business Logic (Xử lý nghiệp vụ)**
Xây dựng trên Tầng 1, cung cấp các khả năng xử lý nghiệp vụ: quy trình BPMN, quản lý ứng dụng, vai trò và phân quyền, thông báo, mẫu văn bản, quy tắc phân bổ, tích hợp email, report/dashboard, API và logic phía server bằng Custom Backend Module.

**Tầng 3 — Application (Miền ứng dụng)**
Các miền ứng dụng được lắp ghép từ hai tầng dưới và cấu hình theo workspace: Sales, Inventory, People, Process, Omni Channel, Finance, Service, Manufacture và Goal. Có thể bổ sung màn hình riêng bằng Custom Frontend Module, sử dụng API có sẵn hoặc kết hợp Custom Backend Module.

## Ứng dụng mobile Android và iOS

Cogover có ứng dụng mobile cho **Android và iOS**, cho phép người dùng theo quyền được cấp:

- Tạo, sửa, xem và xoá bản ghi của Object.
- Xem các App trong Workspace.
- Xem, tạo và xoá lượt chạy Process.
- Xem phòng ban, nhân sự và vị trí.
- Nhận thông báo đẩy (push notification) từ hệ thống, kể cả khi không mở ứng dụng.

Layout bản ghi có thể được thiết kế **riêng cho Web**, **riêng cho Mobile** hoặc **dùng chung cho cả hai**. Dùng `$object-layout` để cấu hình phạm vi nền tảng và bố cục phù hợp.

Node **Send Notification** của Process có thể gửi thông báo đến ứng dụng mobile khi chọn **Loại thông báo** là **All** hoặc **In app**. Đây là hai bản ghi của Object `notification_channel`, với các trường kênh tương ứng được tick; khi **mobile push** được tick, người nhận nhận thêm push notification mà không cần mở ứng dụng. Đọc [Thông báo ở Tầng 2](references/tang2-business-logic.md#thông-báo) để resolve kênh trước khi cấu hình Process.

## Khi nào đọc file reference nào

| Chủ đề câu hỏi | File cần đọc |
|---|---|
| Object, Field, Layout, Button, UI logic, bảo mật, trạng thái, trùng lặp, lịch sử thay đổi | [Tầng 1 — Object Manager](references/tang1-object-manager.md) |
| Chọn đúng loại field và quan hệ giữa Object | [Các loại Object Field](references/object-fields.md) |
| Process, App/Menu, Role, thông báo, mẫu văn bản, phân bổ, email và API | [Tầng 2 — Business Logic](references/tang2-business-logic.md) |
| Giao diện riêng, logic phía server, API riêng hoặc kết hợp frontend/backend | [$cogover-custom-module](../cogover-custom-module/SKILL.md); dùng mục Custom Module bên dưới để phân biệt các lựa chọn |
| Các app Sales, Inventory, People, Process, Omni Channel, Finance, Service, Manufacture, Goal và module mở rộng | [Tầng 3 — Application](references/tang3-application.md) |
| Tính năng chuẩn, nhóm menu hoặc Object liên quan của app Sales | [Danh sách tính năng chuẩn của Sales](references/sales-app-features.md) |
| Tính năng chuẩn, luồng nghiệp vụ hoặc Object liên quan của app Finance | [Danh sách tính năng chuẩn của Finance](references/finance-app-features.md) |
| Tính năng chuẩn, luồng nghiệp vụ hoặc Object liên quan của app Inventory | [Danh sách tính năng chuẩn của Inventory](references/inventory-app-features.md) |
| Tính năng chuẩn, luồng sản xuất/sửa chữa hoặc Object liên quan của app Manufacture | [Danh sách tính năng chuẩn của Manufacture](references/manufacture-app-features.md) |
| Tính năng chuẩn, kênh chat, hội thoại, tin nhắn hoặc Object liên quan của app Omni Channel | [Danh sách tính năng chuẩn của Omni Channel](references/omni-channel-app-features.md) |
| Tổng quan platform, so sánh các tầng, kiến trúc tổng thể | Đọc file SKILL.md này là đủ |

Nếu câu hỏi liên quan đến nhiều tầng, đọc nhiều reference.

## Chi tiết từng tầng (Tóm tắt)

### Tầng 1: Object Manager — 8 module chính

1. **Object & Field Definition**: Định nghĩa Object (tương tự bảng trong DB) với 20+ loại trường dữ liệu khác nhau — từ Short text, Email, Phone đến Lookup, Formula, Auto number. Đặc biệt, field `formula` dùng **Cogover Scripting** với cú pháp gần Java, hỗ trợ biểu thức, điều kiện, vòng lặp, kiểu dữ liệu và hàm nghiệp vụ để tạo các trường tính toán phức tạp. Dùng `$object-info` để viết, kiểm tra cú pháp và chạy thử Formula trên record thật trước khi lưu. Xem chi tiết tại [các loại Object Field](references/object-fields.md).

2. **Layout Builder**: Kéo thả để thiết kế 3 loại giao diện theo chức năng:
   - Giao diện Tạo bản ghi mới (Create form)
   - Giao diện Xem/Sửa bản ghi (View/Edit form)
   - Giao diện kết hợp Tạo/Xem/Sửa

   Admin kéo thả các trường vào layout, chia thành Section và Group, tuỳ chỉnh số cột hiển thị. Ngoài cấu hình kéo thả, `$layout-scripting` cho phép viết **JavaScript** trong `pageSettings.script` để xử lý các rule giao diện phức tạp như ẩn/hiện, bắt buộc, chỉ đọc, giới hạn lựa chọn, tự động điền giá trị và thao tác với related list. Khi sửa layout hiện có, phối hợp `$object-layout` để đọc script hiện tại và giữ nguyên logic ngoài phạm vi.

3. **Hành động & Chuỗi hành động**: Định nghĩa các hành động (action) có thể thực hiện trên bản ghi Object, và nối chúng thành chuỗi hành động tự động.

4. **Quy tắc giao diện (UI Rules)**: Thiết lập logic hiển thị/ẩn trường, bắt buộc/không bắt buộc, chỉ đọc,... dựa trên điều kiện dữ liệu.

5. **Quy tắc bảo mật dữ liệu (Data Security Rules)**: Kiểm soát ai được xem/sửa/xoá bản ghi nào, chia sẻ bản ghi cho nhân sự cụ thể.

6. **Quy tắc chuyển trạng thái (Transition Rules)**: Định nghĩa bản ghi được phép chuyển từ trạng thái A sang trạng thái B với điều kiện gì, và hành động gì xảy ra trước/sau khi chuyển.

7. **Quy tắc trùng lặp dữ liệu (Duplicate Rules)**: Phát hiện và xử lý bản ghi trùng lặp dựa trên các trường so sánh.

8. **Lịch sử thay đổi trường dữ liệu (Field Change History)**: Ghi nhận ai thay đổi trường nào, vào thời điểm nào và giá trị trước/sau; phù hợp khi nghiệp vụ cần audit trail hoặc theo dõi vòng đời trạng thái.

### Tầng 2: Business Logic — 10 nhóm khả năng chính

1. **Object Process (BPMN)**: Hỗ trợ 5 loại quy trình:
   - **Manual Flow**: Kích hoạt bằng form (ví dụ: đề nghị mua sắm, xin nghỉ phép)
   - **Normal Flow**: Người có quyền chủ động chạy, không bắt buộc Root form
   - **Scheduled Flow**: Chạy tự động theo lịch (cron)
   - **Triggered Flow**: Chạy khi bản ghi thay đổi hoặc nhận webhook
   - **Sequence Flow**: Liên kết bản ghi với quy trình tuần tự

   Các thành phần tiêu biểu gồm User Task, Gateway, Loop, Variable, Assignment, Organization, Wait, Sub Process, Send Email, Send HTTP Request, Send Notification, Get/Create/Update Record, To Do, Phone Call, Omni Message và Export Record. Dùng `$process-creator` làm nguồn chuẩn cho support matrix thực tế.

2. **Quản lý Ứng dụng**: Tạo và cấu hình app với menu, submenu tuỳ chỉnh. Mỗi app gom nhóm các Object và module liên quan.

3. **Quản lý vai trò & Phân quyền**: Tạo vai trò, gán quyền CRUD cho từng Object, gán quyền truy cập module cho từng vai trò.

4. **Quản lý thông báo**: Cấu hình thông báo tự động gửi đến nhân sự khi có sự kiện xảy ra; Send Notification hỗ trợ gửi đến ứng dụng mobile và push theo cấu hình `notification_channel`. Xem [Thông báo ở Tầng 2](references/tang2-business-logic.md#thông-báo).

5. **Quản lý mẫu văn bản**: Tạo template văn bản có chèn biến động, dùng cho email, báo cáo, hợp đồng,...

6. **Quy tắc phân bổ (Assignment Rules)**: Tự động phân bổ bản ghi mới cho nhân sự dựa trên điều kiện, lịch làm việc, round-robin,...

7. **Tích hợp Email**: Kết nối email workspace hoặc email cá nhân nhân sự để gửi/nhận email trực tiếp trong hệ thống.

8. **Report & Dashboard**: Tạo saved report từ dữ liệu Object, kiểm thử kết quả rồi bố trí các report thành dashboard theo dõi.

9. **Cogover API**: Cho phép các hệ thống bên ngoài làm việc với tài nguyên Cogover. `/bapi/v{N}` dùng API Key Bearer; `/api/v{N}` dùng phiên Web App với cookie và CSRF/XSRF theo `$cogover-api-auth`.

10. **Custom Backend Module**: Viết logic nghiệp vụ phía server, đọc/ghi Object, tổng hợp dữ liệu hoặc cung cấp API riêng khi khả năng chuẩn chưa đáp ứng đủ. Dùng [$cogover-custom-module](../cogover-custom-module/SKILL.md) để thiết kế, lập trình, kiểm thử và publish theo dữ liệu, quyền và API được Workspace hỗ trợ.

### Tầng 3: Application — Các miền ứng dụng

Cung cấp các miền ứng dụng có thể được đóng gói và tùy chỉnh theo workspace:
- **Sales (CRM)**: Quản lý khách hàng và người liên hệ, lead, cơ hội, đối thủ, đối tác, báo giá, hợp đồng, sản phẩm, bảng giá, đơn bán hàng, ticket, chiến dịch và đơn vị tính. Đọc [danh sách tính năng chuẩn của Sales](references/sales-app-features.md) để tra cứu nhóm menu, tính năng và Object liên quan.
- **Inventory (WMS)**: Quản lý cấu hình kho và tuyến cung ứng, tồn theo số lượng/lô/serial, phiếu nhập/xuất/điều chuyển, kiểm kê, sổ kho, giá vốn và báo cáo. Đọc [danh sách tính năng chuẩn của Inventory](references/inventory-app-features.md) để tra cứu tính năng và Object liên quan.
- **People (HRM)**: Quản lý nhân sự, phòng ban, chức vụ,...
- **Process (BPM)**: Quản lý quy trình nghiệp vụ,...
- **Omni Channel**: Hợp nhất hội thoại, phân công, phân quyền, nhãn, trạng thái đã đọc, tin nhắn và tương tác trên chat nội bộ, Live Chat, Facebook, Zalo, WhatsApp, TikTok và AI Chat. Đọc [danh sách tính năng chuẩn của Omni Channel](references/omni-channel-app-features.md) để tra cứu kênh, tính năng và Object liên quan.
- **Finance**: Quản lý hóa đơn bán/mua, công nợ, thu/chi, đặt cọc, tạm ứng/quyết toán, ngân sách, dự báo dòng tiền và báo cáo. Đọc [danh sách tính năng chuẩn của Finance](references/finance-app-features.md) để tra cứu tính năng và Object liên quan.
- **Service**: Phần mềm Contact Center, Call Center.
- **Manufacture**: Quản lý BOM nhiều cấp, lệnh và công đoạn sản xuất, cấp phát nguyên vật liệu, nhập thành phẩm, sửa chữa; đồng thời cung cấp các tiện ích đơn hàng, đối soát, thu tiền, bảng giá và nhập serial. Đọc [danh sách tính năng chuẩn của Manufacture](references/manufacture-app-features.md) để tra cứu tính năng và Object liên quan.
- **Goal**: Thiết lập, theo dõi và đo lường mục tiêu theo thời gian thực với chỉ số minh bạch.

Ngoài ra có thể mô hình hóa các miền mở rộng như Order Management, Warranty Management, Reseller Management, E-Commerce Management, Purchasing Management, Ticket Management và Task Management. Các kết nối vận chuyển, mạng xã hội, portal hoặc tích hợp mobile ngoài ứng dụng Cogover chuẩn phải được xác minh theo contract của workspace và skill chuyên trách hiện có.

Mức độ có sẵn và khả năng tùy chỉnh cụ thể phải được xác minh trên workspace đích trước khi triển khai.

## Custom Module — Mở rộng giao diện và nghiệp vụ

Custom Module cho phép bổ sung phần nghiệp vụ mà Object, Process hoặc các chức năng chuẩn chưa đáp ứng đủ, đồng thời sử dụng dữ liệu và quyền của Workspace.

| Loại | Chọn khi | Ví dụ |
|---|---|---|
| **Custom Frontend Module** | Cần màn hình riêng; API hiện có đã đáp ứng dữ liệu và logic với quyền người dùng | Màn hình tra cứu, biểu mẫu hoặc báo cáo tùy chỉnh |
| **Custom Backend Module** | Cần logic phía server, tổng hợp/ghi Object, API riêng hoặc tích hợp có thông tin bí mật | Tính giá, đồng bộ dữ liệu, API tổng hợp tồn kho |
| **Frontend + Backend** | Màn hình riêng cần gọi logic riêng phía backend | Màn hình xử lý đơn hàng gọi API tính giá và cập nhật đơn |

Dùng [$cogover-custom-module](../cogover-custom-module/SKILL.md) làm nguồn chuẩn cho toàn bộ vòng đời module và bàn giao link frontend hoặc cURL backend. Khảo sát chức năng chuẩn trên Workspace trước khi chọn phần custom; nếu chỉ cần cấu hình Object/Layout/Process đã được hỗ trợ, dùng skill chuyên trách tương ứng. Khi người dùng yêu cầu rõ trải nghiệm riêng, vẫn thiết kế phần custom cần thiết.

Không đặt secret trong frontend hoặc mặc định backend vượt quyền dữ liệu. Nếu cần chạy theo sự kiện record hoặc theo lịch, skill Custom Module phối hợp `$process-creator` theo contract được hỗ trợ.

## Mối liên kết giữa các tầng

Điểm mạnh của Cogover nằm ở sự liên kết chặt chẽ giữa 3 tầng:

- **Tầng 1 → Tầng 2**: Object được định nghĩa ở Tầng 1 trở thành đầu vào cho quy trình BPMN ở Tầng 2. Ví dụ: Object "Lead" được dùng trong Triggered Flow để tự động phân bổ Lead mới.
- **Tầng 2 → Tầng 3**: Các quy trình và cấu hình nghiệp vụ ở Tầng 2 được lắp ghép thành trải nghiệm ứng dụng ở Tầng 3.
- **Tùy chỉnh xuyên tầng**: Có thể thêm Object, field, layout, Process, App hoặc Custom Frontend/Backend Module; mọi thay đổi phải được phân tích dependency và regression để tránh ảnh hưởng ngoài phạm vi.

## Bản đồ điều phối skill

| Tác vụ | Skill chuyên trách cần dùng |
|---|---|
| Khảo sát BRD + Workspace, fit-gap, thiết kế và triển khai App end-to-end | [$build-cogover-app](../build-cogover-app/SKILL.md) |
| Thiết kế, tạo, sửa, kiểm thử và publish Custom Frontend Module, Custom Backend Module hoặc cả hai | [$cogover-custom-module](../cogover-custom-module/SKILL.md) |
| Khám phá, tạo hoặc sửa Object, Field, option, Formula và quan hệ | [$object-info](../object-info/SKILL.md) |
| Tạo workbook Excel định nghĩa Object | [$create-cogover-objects](../create-cogover-objects/SKILL.md) |
| Đọc, tạo, sửa, xoá hoặc tạo dữ liệu kiểm thử | [$object-record](../object-record/SKILL.md) |
| Thiết kế và cập nhật layout | [$object-layout](../object-layout/SKILL.md) |
| Viết hoặc sửa client script cho logic giao diện | [$layout-scripting](../layout-scripting/SKILL.md) cùng [$object-layout](../object-layout/SKILL.md) |
| Tạo Button, action hoặc action chain | [$object-button](../object-button/SKILL.md); dùng [$cogover-icon](../cogover-icon/SKILL.md) khi cần icon |
| Tạo saved filter và cấu hình bảng danh sách | [$object-filter](../object-filter/SKILL.md) |
| Tạo form công khai thu thập dữ liệu | [$object-form](../object-form/SKILL.md) cùng [$object-layout](../object-layout/SKILL.md) |
| Cấu hình transition và Path Component | [$object-transition-rule](../object-transition-rule/SKILL.md), [$object-path-component](../object-path-component/SKILL.md) |
| Bật và chọn field history tracking | [$object-history-tracking](../object-history-tracking/SKILL.md) |
| User, Personnel, Department, Position, Role và Data Security | [$user-permission](../user-permission/SKILL.md) |
| Thiết kế, tạo và kiểm thử BPMN | [$process-creator](../process-creator/SKILL.md) |
| Tạo và kiểm thử mẫu văn bản | [$document-template](../document-template/SKILL.md) |
| Tạo saved report | [$report-builder](../report-builder/SKILL.md) |
| Tạo dashboard từ report đã kiểm thử | [$dashboard-builder](../dashboard-builder/SKILL.md) sau [$report-builder](../report-builder/SKILL.md) |
| Tạo App, menu, ACL và icon menu | [$app-menu-manager](../app-menu-manager/SKILL.md), [$cogover-icon](../cogover-icon/SKILL.md) |
| Chọn xác thực đúng cho `/bapi` và `/api` | [$cogover-api-auth](../cogover-api-auth/SKILL.md) |
