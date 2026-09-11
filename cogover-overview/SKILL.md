---
name: cogover-overview
description: "Tổng quan Cogover Platform: kiến trúc 3 tầng, tính năng chuẩn của Sales, Finance, Inventory, Manufacture, Omni Channel, Custom Frontend/Backend Module và bản đồ skill chuyên trách. Dùng khi hỏi Cogover/App chuẩn làm được gì hoặc cần chọn skill. Tạo/sửa Custom Module: $cogover-custom-module; dự án App end-to-end từ BRD/SRS: $build-cogover-app."
metadata:
  author: cogover
  version: "1.1.3"
---

# Tổng quan Cogover Platform

- **Phiên bản:** `1.1.3`
- **Ngày phát hành:** `2026-09-11`

Điểm vào và bản đồ điều phối cho mọi bài toán Cogover: xác định yêu cầu thuộc tầng nào, đọc reference tương ứng, rồi gọi skill chuyên trách để đọc state thật, thực hiện thay đổi và xác minh.

## Nguyên tắc

- Không sao chép contract API hoặc hướng dẫn thao tác chi tiết từ overview; skill chuyên trách là nguồn chuẩn.
- Ứng dụng hiện có: khảo sát state thật trước; giữ cấu hình ngoài phạm vi (ưu tiên merge có chủ đích thay vì thay toàn bộ); sau thay đổi đọc lại state và chạy một kịch bản nghiệp vụ tiêu biểu.
- Ứng dụng mới: thiết kế nghiệp vụ và mô hình dữ liệu trước khi tạo cấu hình trên workspace. Mức độ có sẵn và khả năng tùy chỉnh phải được xác minh trên workspace đích trước khi triển khai.
- Tạo hoặc sửa Custom Frontend Module, Custom Backend Module hay cả hai: chuyển thẳng sang [$cogover-custom-module](../cogover-custom-module/SKILL.md) (điều phối khảo sát, thiết kế, lập trình, kiểm thử và publish). Khi được gọi để cung cấp kiến thức nền cho Custom Module, không chuyển vòng sang `$build-cogover-app`.
- Dự án end-to-end từ BRD/SRS (fit-gap, tư vấn App, thiết kế dữ liệu, lập plan, triển khai nhiều loại cấu hình): giao orchestration cho [$build-cogover-app](../build-cogover-app/SKILL.md); overview chỉ cung cấp kiến thức nền và bản đồ skill.

## Kiến trúc 3 tầng

Cogover là nền tảng low-code/no-code để số hoá và quản lý hoạt động kinh doanh; mỗi tầng xây trên tầng bên dưới.

| Tầng | Vai trò | Module / khả năng |
|---|---|---|
| **1 — Object Manager** | Nền tảng cốt lõi: biến mọi dữ liệu thành Object có cấu trúc, tương tự Database nhưng kèm giao diện trực quan, phân quyền sẵn và module quản trị | Object & Field (20+ loại field; Formula bằng Cogover Scripting); Layout Builder; Hành động & Chuỗi hành động; UI Rules; Data Security Rules; Transition Rules; Duplicate Rules; Field Change History |
| **2 — Business Logic** | Xử lý nghiệp vụ trên dữ liệu và giao diện của Tầng 1 | Object Process (BPMN, 5 loại Flow); Quản lý ứng dụng (App/menu); Vai trò & phân quyền; Thông báo; Mẫu văn bản; Assignment Rules; Tích hợp email; Report & Dashboard; Cogover API; Custom Backend Module |
| **3 — Application** | Miền ứng dụng lắp ghép từ hai tầng dưới, cấu hình theo workspace | Sales (CRM), Inventory (WMS), People (HRM), Process (BPM), Omni Channel, Finance, Service (Contact Center, Call Center), Manufacture, Goal; miền mở rộng (Order, Warranty, Reseller, E-Commerce, Purchasing, Ticket, Task Management); Custom Frontend Module |

Liên kết giữa các tầng:

- Tầng 1 → 2: Object là đầu vào của BPMN (ví dụ Object Lead dùng trong Triggered Flow để tự phân bổ Lead mới).
- Tầng 2 → 3: quy trình và cấu hình nghiệp vụ được lắp ghép thành trải nghiệm ứng dụng.
- Tùy chỉnh xuyên tầng: thêm Object, field, layout, Process, App hoặc Custom Frontend/Backend Module; mọi thay đổi phải phân tích dependency và regression để tránh ảnh hưởng ngoài phạm vi.

## Ứng dụng mobile Android và iOS

Ứng dụng Cogover trên **Android và iOS** cho phép người dùng, theo quyền được cấp:

- Tạo, sửa, xem và xoá bản ghi của Object.
- Xem các App trong Workspace.
- Xem, tạo và xoá lượt chạy Process.
- Xem phòng ban, nhân sự và vị trí.
- Nhận push notification từ hệ thống, kể cả khi không mở ứng dụng.

Layout bản ghi có thể thiết kế **riêng cho Web**, **riêng cho Mobile** hoặc **dùng chung cho cả hai**; cấu hình phạm vi nền tảng và bố cục bằng `$object-layout`.

Node **Send Notification** của Process gửi được đến ứng dụng mobile khi **Loại thông báo** là **All** hoặc **In app** (hai bản ghi của Object `notification_channel` với các trường kênh tương ứng được tick; khi **mobile push** được tick, người nhận nhận thêm push notification mà không cần mở ứng dụng). Resolve kênh theo [Thông báo ở Tầng 2](references/tang2-business-logic.md#thông-báo) trước khi cấu hình Process.

## Khi nào đọc file reference nào

| Chủ đề câu hỏi | File cần đọc |
|---|---|
| Object, Field, Layout, Button, UI Rules, Data Security, Transition, Duplicate, Field Change History | [Tầng 1 — Object Manager](references/tang1-object-manager.md) |
| Thiết kế Object và mô hình dữ liệu từ mô tả nghiệp vụ | [Phương pháp thiết kế Object](references/object-design-method.md) |
| Chọn đúng loại field và quan hệ giữa Object | [Các loại Object Field](references/object-fields.md) |
| Process, App/Menu, Role, thông báo, mẫu văn bản, phân bổ, email, API, Custom Backend Module | [Tầng 2 — Business Logic](references/tang2-business-logic.md) |
| Giao diện riêng, logic phía server, API riêng hoặc kết hợp frontend/backend | Mục [Custom Module](#custom-module) bên dưới để chọn loại, rồi [$cogover-custom-module](../cogover-custom-module/SKILL.md) |
| Các app Sales, Inventory, People, Process, Omni Channel, Finance, Service, Manufacture, Goal và miền mở rộng | [Tầng 3 — Application](references/tang3-application.md) |
| Tính năng chuẩn, nhóm menu, Object liên quan của Sales | [Danh sách tính năng Sales](references/sales-app-features.md) |
| Tính năng chuẩn, luồng nghiệp vụ, Object liên quan của Finance | [Danh sách tính năng Finance](references/finance-app-features.md) |
| Tính năng chuẩn, luồng nghiệp vụ, Object liên quan của Inventory | [Danh sách tính năng Inventory](references/inventory-app-features.md) |
| Tính năng chuẩn, luồng sản xuất/sửa chữa, Object liên quan của Manufacture | [Danh sách tính năng Manufacture](references/manufacture-app-features.md) |
| Tính năng chuẩn, kênh chat, hội thoại, tin nhắn, Object liên quan của Omni Channel | [Danh sách tính năng Omni Channel](references/omni-channel-app-features.md) |
| Tổng quan platform, so sánh các tầng, kiến trúc tổng thể | File SKILL.md này là đủ |

Câu hỏi liên quan nhiều tầng: đọc nhiều reference.

## Custom Module

Bổ sung phần nghiệp vụ mà Object, Process hoặc chức năng chuẩn chưa đáp ứng đủ, đồng thời dùng dữ liệu và quyền của Workspace.

| Loại | Chọn khi | Ví dụ |
|---|---|---|
| **Custom Frontend Module** | Cần màn hình riêng; API hiện có đã đáp ứng dữ liệu và logic với quyền người dùng | Màn hình tra cứu, biểu mẫu hoặc báo cáo tùy chỉnh |
| **Custom Backend Module** | Cần logic phía server, tổng hợp/ghi Object, API riêng hoặc tích hợp có thông tin bí mật | Tính giá, đồng bộ dữ liệu, API tổng hợp tồn kho |
| **Frontend + Backend** | Màn hình riêng cần gọi logic riêng phía backend | Màn hình xử lý đơn hàng gọi API tính giá và cập nhật đơn |

- [$cogover-custom-module](../cogover-custom-module/SKILL.md) là nguồn chuẩn cho toàn bộ vòng đời module và bàn giao link frontend hoặc cURL backend.
- Khảo sát chức năng chuẩn trên Workspace trước khi chọn phần custom; nếu chỉ cần cấu hình Object/Layout/Process đã được hỗ trợ, dùng skill chuyên trách tương ứng. Người dùng yêu cầu rõ trải nghiệm riêng: vẫn thiết kế phần custom cần thiết.
- Không đặt secret trong frontend; backend không mặc định vượt quyền dữ liệu. Cần chạy theo sự kiện record hoặc theo lịch: phối hợp `$process-creator` theo contract được hỗ trợ.

## Bản đồ điều phối skill

| Tác vụ | Skill chuyên trách |
|---|---|
| Khảo sát BRD + Workspace, fit-gap, thiết kế và triển khai App end-to-end | [$build-cogover-app](../build-cogover-app/SKILL.md) |
| Thiết kế, tạo, sửa, kiểm thử và publish Custom Frontend/Backend Module | [$cogover-custom-module](../cogover-custom-module/SKILL.md) |
| Khám phá, tạo hoặc sửa Object, Field, option, Formula và quan hệ | [$object-info](../object-info/SKILL.md) |
| Tạo workbook Excel định nghĩa Object | [$create-cogover-objects](../create-cogover-objects/SKILL.md) |
| Đọc, tạo, sửa, xoá record hoặc tạo dữ liệu kiểm thử | [$object-record](../object-record/SKILL.md) |
| Thiết kế và cập nhật layout | [$object-layout](../object-layout/SKILL.md) |
| Viết hoặc sửa client script cho logic giao diện | [$layout-scripting](../layout-scripting/SKILL.md) cùng [$object-layout](../object-layout/SKILL.md) |
| Tạo Button, action hoặc action chain | [$object-button](../object-button/SKILL.md); [$cogover-icon](../cogover-icon/SKILL.md) khi cần icon |
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
