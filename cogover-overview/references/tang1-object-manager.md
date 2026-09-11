# Tầng 1: Object Manager

Thiết kế Object mới từ mô tả nghiệp vụ: [Phương pháp thiết kế Object](object-design-method.md). Chọn loại field và quan hệ: [Các loại Object Field](object-fields.md). Skill chuyên trách từng module: [bản đồ điều phối skill](../SKILL.md#bản-đồ-điều-phối-skill).

## Khái niệm Object

Object Manager là Database trực quan: **Object** = bảng (kèm sẵn giao diện, phân quyền và module quản trị), **Field** = cột, **Record** = dòng. Ví dụ: Object Lead (Tên, Email, Điện thoại, Trạng thái), Contact (Họ tên, Email, lookup đến Account), Opportunity (Tên, Giai đoạn, Doanh thu dự kiến).

Khi tạo custom Object, contract có thể khởi tạo standard field, layout, button và filter theo cấu hình; quyền CRUD và phạm vi record vẫn phải thiết kế, cấu hình và kiểm thử riêng.

## Định nghĩa Object & Field

Object có 20+ loại field (Short text, Email, Phone... Lookup, Formula, Auto number); cách chọn tại [object-fields.md](object-fields.md), sau đó dùng `$object-info` đọc và thay đổi schema thật.

Quy trình tạo Object: xác định Object cần quản lý → xác định field (mỗi thông tin = 1 field với loại phù hợp) → kiểm tra quan hệ (Object đích của lookup phải tồn tại trước) → tạo Object qua giao diện định nghĩa field.

Quy tắc đặt tên:

- Tên hiển thị: tên nghiệp vụ rõ nghĩa, nhất quán ngôn ngữ (ví dụ `Expense category`). Không dùng dấu `*` trong tên field để biểu diễn bắt buộc; cấu hình thuộc tính `required` theo `$object-info`. Tên field file đặt theo ngữ nghĩa nghiệp vụ, không áp một tên cố định cho mọi Object.
- Tên kỹ thuật: phân biệt tên hiển thị với `slug`; resolve và kiểm tra tính duy nhất trên workspace. Không tự suy diễn slug; không đổi tên field/Object đang được layout, process, formula, filter hoặc report tham chiếu.

Field đặc thù:

- Mã do hệ thống tự sinh: `auto_number`, không dùng `short_text` nhập tay.
- Owner (người sở hữu): `lookup_normal` → Personnel, default thường gặp `$currentUser`; luôn đọc metadata thật trước khi tạo hoặc sửa.

Workspace CRM có thể đã có Lead, Opportunity, Contact, Account, Contract, Activity, Ticket, Product: dùng `$object-info` kiểm tra state thật trước khi tái sử dụng, mở rộng hoặc tạo Object mới.

## Layout Builder

Thiết kế giao diện bằng kéo thả; ba loại layout theo `functionLayout`:

1. **Tạo bản ghi (Create form)**: kéo field từ danh sách bên trái vào vùng thiết kế; chia Section và Group; 1, 2 hoặc 3 cột. Ví dụ Lead: section "Thông tin khách hàng tiềm năng" (Tiêu đề, Họ, Tên, Trạng thái, Người sở hữu) và "Thông tin bổ sung" (Công ty, Doanh thu hàng năm).
2. **Xem/Sửa bản ghi (View/Edit form)**: phức tạp hơn với nhiều Layout Row, Layout Column, Section dạng Tab; hiển thị đầy đủ bản ghi kèm Activities, Related records. Ví dụ Lead: phần trên avatar, tiêu đề, trạng thái, field chính; phần dưới tab Activities và tab Related; sidebar phải Người sở hữu, Công ty, Doanh thu.
3. **Kết hợp Tạo/Xem/Sửa**: một layout phục vụ cả ba ngữ cảnh.

- Với layout tạo record, `isForm` phân biệt layout tạo nội bộ và public form. Luôn dùng `$object-layout` đọc support matrix, kiểm tra state hiện có và merge thay đổi an toàn.
- Độc lập với chức năng, layout dùng riêng cho **Web**, riêng cho **Mobile** hoặc chung cả hai qua `isWeb`/`isMobile`; `$object-layout` đọc và cấu hình đúng layout đích; dùng chung thì đánh giá bố cục trên cả Web và Mobile.
- Layout có thể chứa JavaScript tại `pageSettings.script`: `$layout-scripting` triển khai rule ẩn/hiện, bắt buộc, chỉ đọc, giới hạn options, tự động điền giá trị, truy vấn record hoặc xử lý related list. Thêm/sửa script trên layout hiện có: bắt buộc lấy script hiện tại qua `$object-layout` trước và patch đúng phạm vi để không mất logic cũ.

Cấu trúc: Layout Row → Layout Column (có thể nhiều cột) → Section (có thể chia Tab) → Tab → Group → Field; mỗi Group cấu hình `numberOfColumns` để field hiển thị theo grid.

## Hành động & Chuỗi hành động

- **Hành động (Action)**: thao tác tuỳ chỉnh trên bản ghi ngoài Tạo/Sửa/Xoá mặc định, ví dụ "Chuyển đổi Lead thành Contact" (tạo Contact từ dữ liệu Lead), "Gửi email chào mừng" khi tạo bản ghi mới, "Tính lại tổng đơn hàng" (cập nhật trường Formula).
- **Chuỗi hành động (Action Sequence)**: nối nhiều hành động thành workflow tự động; hành động sau tự chạy khi hành động trước hoàn thành, ví dụ Tạo Lead → Gửi email xác nhận → Gán cho nhân viên sales → Tạo reminder follow-up.

Triển khai bằng `$object-button`; phối hợp `$object-layout` khi đặt action lên giao diện, `$object-filter` khi giới hạn theo filter, `$cogover-icon` khi gắn icon.

## Quy tắc giao diện

UI Rules điều khiển giao diện động theo điều kiện dữ liệu. Ba loại: hiển thị/ẩn trường (ví dụ "Lý do từ chối" chỉ hiện khi Trạng thái = "Từ chối"), bắt buộc/không bắt buộc ("Ngày hết hạn" bắt buộc khi Loại = "Hợp đồng có thời hạn"), chỉ đọc (không cho sửa "Giá trị" khi Trạng thái = "Đã phê duyệt"). Mỗi rule gồm điều kiện (trường A = X, trường B > Y...), logic kết hợp AND/OR/CUSTOM và hành động (ẩn, bắt buộc hoặc chỉ đọc).

Rule đơn giản cấu hình trực tiếp; project chưa có skill declarative UI Rules riêng, không suy đoán contract UI Rules từ overview. Nghiệp vụ phức tạp hoặc logic thực hiện bằng client script: `$layout-scripting` cùng `$object-layout`.

## Quy tắc bảo mật dữ liệu

Data Security Rules phân quyền ở cấp bản ghi (record-level), bổ sung cho phân quyền cấp Object: theo Owner (chỉ người sở hữu thấy/sửa), theo phòng ban (cùng phòng mới thấy bản ghi của phòng), theo vai trò (Manager thấy bản ghi của cấp dưới) và chia sẻ bản ghi cụ thể cho nhân sự khác với quyền xem/sửa. Ví dụ: sales chỉ thấy Lead/Opportunity của mình, Manager thấy cả team; agent chỉ thấy Ticket được gán, Supervisor thấy tất cả; nhân sự chỉ thấy hồ sơ của mình, HR Manager thấy tất cả.

`$user-permission` đọc và cấu hình Role, Object permission và Data Security Rule; luôn snapshot quyền hiện có trước khi thay đổi.

## Quy tắc chuyển trạng thái

Transition Rules kiểm soát trạng thái nào được chuyển sang trạng thái nào, ai được chuyển và điều gì xảy ra khi chuyển:

1. Chuyển đổi cho phép: ví dụ Lead "Mới" chuyển sang "Đang làm việc" hoặc "Không hợp lệ", không nhảy thẳng sang "Đã chuyển đổi".
2. Điều kiện trước chuyển đổi: ví dụ chỉ chuyển Opportunity sang "Đã đóng thắng" khi Doanh thu > 0.
3. Hành động trước/sau chuyển đổi: ví dụ Lead sang "Đã chuyển đổi" → tự tạo Contact mới.

`$object-transition-rule` là nguồn chuẩn để đọc, tạo và kiểm thử transition; `$object-path-component` khi cần hiển thị tiến trình trạng thái trên layout.

## Quy tắc trùng lặp dữ liệu

Duplicate Rules phát hiện và xử lý bản ghi trùng theo trường so sánh do admin chọn (Email, Số điện thoại, Tên + Công ty...), so khớp chính xác hoặc gần đúng; khi trùng: cảnh báo người dùng, chặn tạo bản ghi hoặc merge. Ví dụ: Lead trùng Email/Số điện thoại; Contact trùng Email trong cùng Account; sản phẩm trùng mã SKU.

Bộ skill chưa có skill chuyên trách cho Duplicate Rules: chỉ mô tả yêu cầu phát hiện trùng và tiêu chí so sánh ở mức khái niệm cho đến khi có tài liệu sản phẩm hoặc API chính thức được hỗ trợ; không suy đoán thao tác hoặc endpoint, không khẳng định có thể triển khai tự động từ project này.

## Lịch sử thay đổi trường dữ liệu

Field Change History phù hợp khi Object cần audit trail, truy vết trách nhiệm hoặc theo dõi vòng đời một số field quan trọng; không cần bật cho mọi Object hoặc mọi field. Admin chọn trường theo dõi; mỗi khi giá trị đổi, hệ thống ghi giá trị trước, giá trị sau, ngày giờ và người thực hiện, hiển thị ngay trong giao diện xem bản ghi.

Use case: Lead status (đánh giá tốc độ phản hồi sales), Opportunity stage (phân tích pipeline, tìm bottleneck), Ticket status (số trạng thái đã qua, thời gian mỗi trạng thái, SLA), Task status (hiệu suất nhân viên), Order status (minh bạch với khách hàng), Approval status (audit trail tuân thủ), giá trị hợp đồng/đơn hàng (ai đổi, từ bao nhiêu sang bao nhiêu), Owner (chuyển giao giữa nhân viên).

Đánh giá bật khi: người dùng hỏi về theo dõi, giám sát, audit trail; Object có trường trạng thái (Single choice với start/intermediate/end state); cần biết "ai đã thay đổi gì, khi nào"; cần đo thời gian ở mỗi trạng thái; cần tuân thủ quy định (compliance, SOX, ISO...). Dùng `$object-history-tracking` đọc cấu hình hiện có, bật tracking đúng Object/field và xác minh kết quả.
