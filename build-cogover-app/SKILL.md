---
name: build-cogover-app
description: "Điều phối dự án triển khai Cogover end-to-end từ Workspace đích và yêu cầu khách hàng: bắt buộc xác thực API key đúng Workspace trước khảo sát, đọc App/Object hiện có, làm rõ nghiệp vụ, fit-gap với khả năng chuẩn, thiết kế Object/field/state machine, tạo workbook Object, lập kế hoạch có dependency và triển khai/kiểm thử sau các cổng duyệt. Chỉ dùng khi người dùng gọi cụ thể $build-cogover-app hoặc đã đồng ý rõ sau khi AI đề xuất sử dụng. Phù hợp khi cần xây App Cogover mới, tùy chỉnh nhiều thành phần của App hiện có, hoặc chuyển BRD/SRS thành solution blueprint có thể triển khai. Không dùng cho một thay đổi Cogover đơn lẻ đã rõ phạm vi hoặc câu hỏi tổng quan; dùng skill Cogover chuyên trách hoặc $cogover-overview tương ứng."
metadata:
  author: cogover
  version: "3.0.0"
---

# Build Cogover App

- **Phiên bản:** `3.0.0`
- **Ngày phát hành:** `2026-09-11`

## Vai trò và nguồn chuẩn

Workflow điều phối cần môi trường hỗ trợ sub-agent và chia sẻ artifact có phạm vi. Nếu thiếu năng lực này, chỉ hoàn tất phần tư vấn/chuẩn bị không phụ thuộc điều phối, ghi rõ bước chưa thực hiện và điều kiện để tiếp tục; không tự tuyên bố đã chạy review độc lập. Công cụ XLSX có thể là skill spreadsheet sẵn có hoặc thư viện tương đương giữ đúng schema và vượt qua validator.

Đóng vai solution architect, database architect và chuyên gia phần mềm quản trị doanh nghiệp. Thiết kế cấu hình khả thi trên Cogover; không xử lý như một dự án phần mềm độc lập và không bắt đầu từ API payload.

## Chính sách kích hoạt

Skill này chạy kỹ và có thể mất nhiều thời gian, vì vậy không được tự kích hoạt:

- Chỉ bắt đầu dùng skill khi người dùng gọi cụ thể `$build-cogover-app` hoặc nhắc rõ tên `build-cogover-app` với ý định sử dụng.
- AI có thể đề xuất skill khi nhận thấy yêu cầu là dự án Cogover end-to-end, nhưng phải giải thích ngắn gọn phạm vi/thời gian và chờ người dùng **đồng ý sử dụng** trước khi tải hoặc thực hiện workflow của skill.
- Một yêu cầu chung như “xây App Cogover”, “phân tích BRD” hoặc “tư vấn triển khai” không tự động là sự đồng ý. Trước khi có xác nhận, dùng skill chuyên trách phù hợp cho tác vụ đơn lẻ hoặc chỉ trả lời ở mức tư vấn chung.
- Sau khi đã được kích hoạt rõ trong task/chat hiện tại, không cần xin lại cho từng phase; các Gate Solution, Data Model, Plan và gate hẹp vẫn áp dụng độc lập.

Luôn đọc:

- [$cogover-overview](../cogover-overview/SKILL.md) cùng reference liên quan để hiểu Platform, App chuẩn và định tuyến skill.
- [Credential preflight](references/credential-preflight.md) trước mọi khảo sát khi đã biết Workspace đích.
- [Artifact contracts](references/artifact-contracts.md) trước khi tạo hoặc sửa file bàn giao.
- [Orchestration and gates](references/orchestration-and-gates.md) trước khi giao sub-agent, mở cổng duyệt hoặc thay đổi Workspace.
- [Bản đọc HTML/Excel và tiếp nhận câu trả lời](references/human-readable-deliverables.md) trước khi tạo bản người dùng đọc, nhận thông báo “đã trả lời” hoặc cập nhật tiến độ thực thi.

Dùng response mới nhất của Workspace và skill chuyên trách làm nguồn chuẩn cho trạng thái/capability cụ thể. Không coi một Object, menu hoặc tên App tồn tại là bằng chứng tính năng end-to-end đã hoạt động.

### Khả năng chuẩn trên Mobile cần đưa vào giải pháp

- Cogover có ứng dụng cho **Android và iOS**: tạo/sửa/xem/xoá bản ghi Object; xem App; xem/tạo/xoá lượt chạy Process; xem phòng ban/nhân sự/vị trí; nhận thông báo đẩy (push notification) từ hệ thống. Thiết kế phạm vi thao tác theo quyền của từng persona.
- Layout bản ghi có thể thiết kế **riêng cho Web**, **riêng cho Mobile** hoặc **dùng chung**. Ghi lựa chọn này trong giải pháp và chuyển cấu hình `isWeb`/`isMobile` cùng bố cục cho `$object-layout`.
- Node **Send Notification** trong Process có thể gửi đến ứng dụng mobile khi **Loại thông báo** là **All** hoặc **In app**. Đây là hai bản ghi của Object `notification_channel` với các trường kênh tương ứng được tick; khi **mobile push** được tick, người nhận nhận thêm push notification mà không cần mở ứng dụng. Dùng `$object-info` và `$object-record` đọc schema/bản ghi kênh thật, rồi `$process-creator` cấu hình node; không đoán ID hoặc slug trường kênh. Xem [Thông báo ở Tầng 2](../cogover-overview/references/tang2-business-logic.md#thông-báo).

Khi yêu cầu nằm trong các khả năng trên, ưu tiên ứng dụng Cogover chuẩn trong fit-gap; xác minh cấu hình và quyền trên Workspace đích trước triển khai.

## Chế độ thực thi và nguyên tắc bất biến

Ghi rõ mode trong mọi lời gọi skill con:

1. `DISCOVERY_ONLY`: chỉ đọc state; một API đọc có thể dùng `POST`, phân loại theo side effect chứ không theo HTTP verb.
2. `DESIGN_ONLY`: chỉ phân tích và tạo artifact cục bộ.
3. `APPLY_APPROVED_PLAN`: chỉ thực hiện work item `READY` trong đúng plan revision đã được duyệt.

Mặc định dùng `DISCOVERY_ONLY`. Trước Gate Plan, luôn truyền cho skill con/sub-agent:

> Chỉ đọc/phân tích. Không create, update, delete, upload, activate, publish tài nguyên Workspace, gửi thông báo, chạy process hay thay đổi Workspace; được tạo file bàn giao local đã được giao ở DESIGN_ONLY.

Reviewer độc lập là tùy chọn để giảm thời gian chạy:

- Mặc định `Reviewer mode: OFF`: không tạo `solution_reviewer` hoặc `data_design_reviewer`; validator, coordinator self-check và các approval gate vẫn bắt buộc.
- Chỉ chuyển thành `Reviewer mode: ON` khi người dùng yêu cầu rõ **“bật các reviewer”** hoặc diễn đạt tương đương rằng muốn dùng reviewer độc lập. Không tự bật dựa trên độ lớn, độ phức tạp hoặc mức rủi ro của dự án.
- Khi `ON`, áp dụng reviewer cho cả solution và data design theo protocol trong [Orchestration and gates](references/orchestration-and-gates.md), đồng thời ghi bằng chứng yêu cầu của người dùng trong artifact. Giữ mode này cho các revision tiếp theo của dự án cho đến khi người dùng yêu cầu tắt.
- Khi `OFF`, ghi `NOT_REQUESTED`/`NOT_APPLICABLE` vào các trường reviewer tương ứng; không coi việc thiếu reviewer hoặc reviewer verdict là lỗi chặn gate.

Tuân thủ các nguyên tắc:

- Không đoán thông tin nghiệp vụ đang chặn một quyết định. Dùng `TBD`/`UNKNOWN`, hỏi người dùng và dừng đúng gate.
- Khi đã có Workspace đích, không bắt đầu Phase 1, không tạo artifact và không giao sub-agent cho đến khi Gate Credential đạt `VERIFIED`.
- Không xem việc có API key, duyệt giải pháp hay duyệt data model là quyền mutation.
- Chỉ dùng capability Cogover đã được chứng minh. Nếu không khả thi, ghi `NOT_SUPPORTED` hoặc đề xuất hạng mục code/tích hợp cho team khác; không tự code nghiệp vụ hoặc tích hợp Workspace trong skill này. Mã HTML/JavaScript phục vụ bản đọc local và lưu câu trả lời theo contract bản đọc được phép.
- Không ghi approval giả. Chỉ lưu nội dung xác nhận thực tế của người dùng kèm revision.
- Không ghi secret, cookie, token hoặc API key vào prompt tự nhiên, file, lệnh shell literal, log, commentary hay câu trả lời.
- Với `NEW_APP`, mặc định thiết kế một Menu Item cấp 1 dạng nhóm `Home` và một Menu Item cấp 2 `Overview` làm menu mặc định, trỏ tới Dashboard tổng quan các KPI quan trọng của App. Chỉ tạo/wire Dashboard sau khi report/KPI nguồn đã preview và đối soát thành công. Nếu Dashboard không được Workspace/runtime hỗ trợ, dùng Overview dạng report/page đã được chứng minh làm fallback và ghi limitation; không tạo Dashboard rỗng hoặc giả. Với `CUSTOMIZE_EXISTING_APP`, giữ nguyên information architecture/menu hiện có trừ khi người dùng yêu cầu rõ việc tái cấu trúc.
- Với custom App, mọi Menu Item cấp 1 nên có icon App Menu phù hợp ngữ nghĩa. Chỉ bỏ icon khi người dùng yêu cầu rõ hoặc capability/runtime chứng minh không hỗ trợ; ghi quyết định đó vào solution/plan. Không coi menu tree hoàn tất nếu root-menu icon chưa được resolve, cài và read-back.

## Đầu vào và nơi lưu artifact

### Bản chuẩn cho AI và bản để người dùng đọc

- Các file **Markdown (.md) là nguồn chuẩn để AI phân tích, triển khai và bàn giao cho Agent khác**. Viết phần yêu cầu/giải pháp và kế hoạch bằng tiếng Việt dễ hiểu cho người không chuyên kỹ thuật, giải thích rõ việc cần làm, lý do và kết quả; hạn chế tiếng Anh và thuật ngữ chuyên ngành. Giữ mã `REQ-ID`, `Q-ID`, `W-ID`, slug, tên skill/API và enum cần cho máy; giải thích thuật ngữ bắt buộc ở lần đầu, đặt chi tiết kỹ thuật ở phần riêng.
- Mỗi giai đoạn giao **một sub-agent chuyên tạo bản đọc**, với context mới chỉ gồm Markdown nguồn và tài liệu cần thiết: `solution_reader` tạo HTML yêu cầu/giải pháp; `data_design_reader` tạo Excel rồi HTML thiết kế dữ liệu; `plan_reader` tạo HTML kế hoạch. Các agent này bắt buộc ngay cả khi `Reviewer mode: OFF`; chúng không phải reviewer. Chỉ cấp quyền ghi file đầu ra được giao, không sửa Markdown nguồn hoặc thay đổi Workspace.
- Coordinator giữ quyền ghi Markdown chuẩn và kiểm tra bản đọc khớp nguồn trước khi giao. HTML/Excel có tên nguồn, revision và thời điểm tạo rõ ràng; không dùng chúng thay Markdown ở bước AI tiếp theo. Câu trả lời JSON do HTML xuất là dữ liệu đầu vào, phải được kiểm tra rồi nhập vào revision Markdown mới.

Thu thập tối thiểu:

- Workspace đích bằng alias, URL/domain hoặc identifier; xác định `sandbox`, `UAT` hay `production`.
- Yêu cầu nghiệp vụ chi tiết và version/ngày của nguồn; xác định `NEW_APP`, `CUSTOMIZE_EXISTING_APP` hoặc kết hợp.
- Phạm vi MVP/future phase, ưu tiên và tiêu chí thành công.
- API key của Super Admin qua secret field, scoped environment, secret manager, credential broker hoặc cơ chế bí mật do runtime cung cấp. Khi đã có Workspace đích, key là đầu vào bắt buộc; không nhận hoặc lưu key trong artifact, repository hay log.

## Phase 0 — Gate Credential bắt buộc

Khi người dùng đã cung cấp Workspace đích:

1. Resolve URL canonical và API key bằng kênh bí mật trung lập với môi trường theo [Credential preflight](references/credential-preflight.md). Nếu runtime không có credential, yêu cầu người dùng cung cấp key qua secret input hoặc kênh bí mật phù hợp.
2. Dùng `$cogover-api-auth` gọi `POST /bapi/v1/auth-token` trên chính Workspace đích. Đây là authentication probe read-only; không dùng browser session hoặc key Workspace khác làm fallback.
3. Chỉ coi key hợp lệ khi response authentication thành công, session fields cần thiết còn hiệu lực, `workspaceDomain`/`workspaceId` khớp Workspace đích và các probe đọc tối thiểu cho App/Object không bị từ chối quyền.
4. Ghi evidence đã redacted: thời điểm, target host/alias, workspace domain/ID trả về, personnel ID nếu cần, kết quả auth và discovery probes. Không ghi key, token, cookie hoặc raw response chứa secret.
5. Chỉ chuyển trạng thái sang `VERIFIED` khi tất cả điều kiện đạt. Với `MISSING`, `INVALID`, `WORKSPACE_MISMATCH`, `INSUFFICIENT_DISCOVERY_ACCESS` hoặc `UNVERIFIED_TRANSIENT`, dừng toàn bộ workflow và báo cách khắc phục; không đọc/phân tích yêu cầu, tạo artifact hoặc khởi chạy sub-agent.

Việc auth thành công không tự chứng minh quyền Super Admin cho mutation. Xác minh quyền đặc thù trước work item cần quyền đó. Xác thực lại khi Workspace/key thay đổi, credential bị rotate/revoke, phiên hết hạn hoặc trước `APPLY_APPROVED_PLAN` nếu evidence không còn mới.

Nếu chưa có nơi lưu, dùng `artifacts/cogover-implementation/<project-slug>/`. Mỗi lần người dùng trả lời một vòng câu hỏi, tạo revision `vN+1`; không ghi đè revision đã giao.

Tạo theo thứ tự:

1. `danh-sach-yeu-cau-va-giai-phap-so-bo-vN.md` và bản đọc cùng tên `.html`; câu trả lời lưu trong `answers/` theo reference bản đọc.
2. `data-design-vN.md`, `cogover-objects-vN.xlsx` để người dùng duyệt và `data-design-vN.html` có sơ đồ quan hệ khi có thay đổi mô hình dữ liệu.
3. `implementation-plan-vN.md` và bản đọc cùng tên `.html`, đồng bộ trạng thái từng việc trong quá trình thực hiện.
4. `snapshots/pre-apply-<timestamp>/` trước mutation cấu hình hiện có
5. `test-handover-vN.md` sau triển khai

## Phase 1 — Đọc yêu cầu, Cogover và Workspace

Chỉ bắt đầu sau Gate Credential `VERIFIED` khi đã có Workspace đích.

### 1.1 Chuẩn hóa yêu cầu

1. Đọc toàn bộ nguồn bằng capability phù hợp; giữ nội dung từ bảng, sheet, sơ đồ, phụ lục và comment liên quan.
2. Sanitize secret/PII không cần thiết trước khi chuyển cho sub-agent hoặc nghiên cứu web.
3. Tạo `REQ-001`, `REQ-002`, ...; với mỗi yêu cầu tách actor, trigger, input, business rule, output, exception, priority và acceptance criterion.
4. Ghi provenance theo file/page/heading/sheet/dòng khi có thể. Ghi mâu thuẫn và nội dung thiếu; không tự lấp chỗ trống.

### 1.2 Hiểu Platform và App chuẩn

1. Dùng `$cogover-overview`; đọc reference Tầng 1, Tầng 2, Tầng 3 và catalog của mọi App ứng viên.
2. Lập danh sách capability/Object/process chuẩn liên quan. Không khẳng định catalog đầy đủ khi chưa có reference hoặc bằng chứng Workspace.
3. Phân biệt `native configuration`, `custom Object/configuration`, `external integration/code` và `unknown`.

### 1.3 Khảo sát Workspace ở `DISCOVERY_ONLY`

1. Dùng `$app-menu-manager` đọc App, menu tree, action target, ACL và trạng thái.
   - Đồng thời dùng `$cogover-icon` đọc thư viện icon Workspace và ghi rõ root menu nào đã có asset phù hợp để tái sử dụng, root menu nào cần tạo mới; không tạo trùng asset.
2. Dùng `$object-info` đọc Object, field, option, metadata, lookup và related list; phân trang đến hết phạm vi.
3. Với thành phần liên quan, đọc sâu bằng skill tương ứng: filter, layout/script, form, button, transition/path, history, permission, process, template, report/dashboard và menu.
4. Ghi ID/slug thật, timestamp, evidence và confidence. Không lưu raw response có secret hoặc dữ liệu khách hàng không cần thiết.

Tiếp tục discovery read-only nếu còn việc hữu ích; không hỏi người dùng thông tin có thể lấy an toàn từ Workspace.

## Phase 2 — Làm rõ và chốt giải pháp

### 2.1 Hỏi chi tiết, không đoán

Tạo `Q-001`, `Q-002`, ... và hỏi theo nhóm ưu tiên. Bắt buộc làm rõ khi ảnh hưởng đến:

- Mục tiêu, in-scope/out-of-scope, actor/owner/quyền, acceptance criterion.
- As-is/to-be flow, happy path, exception, cancel/reopen/retry và SLA.
- Master/transaction data, source of truth, business key, cardinality, volume, retention và migration.
- Validation, duplicate, formula, audit/history và dữ liệu nhạy cảm.
- Trigger, approval, process node, schedule, notification, idempotency và concurrency.
- Create/view/edit layout, mobile/web, filter, button, bulk action và public form.
- Nếu có phạm vi Mobile: persona dùng Android/iOS nào, thao tác cần hỗ trợ, layout riêng hay dùng chung; với Send Notification, làm rõ người nhận, kênh `All`/`In app` và nhu cầu nhận thêm mobile push khi không mở ứng dụng.
- Report population, metric, dimension, aggregate, drill-down và quyền xem.
- Với `NEW_APP`: KPI nào xuất hiện trên `Home → Overview`, nguồn report/filter của từng KPI, persona được xem và hành vi drill-down. Không hỏi/tái cấu trúc `CUSTOMIZE_EXISTING_APP` chỉ để áp mẫu Home/Overview nếu yêu cầu không đụng information architecture.
- Integration, credential owner, error handling, NFR và tiêu chí test.

Mỗi câu hỏi phải map về `REQ-ID`, nêu decision bị chặn và mức `BLOCKING`/`NON_BLOCKING`. Nếu còn câu `BLOCKING`, không chốt giải pháp cho requirement đó.

### 2.2 Fit-gap và giải pháp cho từng yêu cầu

Với từng `REQ-ID`, so sánh ba lớp bằng chứng: yêu cầu khách hàng, state Workspace, capability/App chuẩn Cogover. Dùng một disposition:

- `REUSE_AS_IS`
- `CONFIGURE`
- `EXTEND`
- `INSTALL_STANDARD_APP`
- `BUILD_CUSTOM`
- `EXTERNAL_INTEGRATION`
- `NOT_SUPPORTED`
- `UNKNOWN`

Giải pháp phải nêu rõ Object/module/process/layout/report/template nào được tái sử dụng hoặc thay đổi, dependency, limitation, acceptance và bằng chứng. Ví dụ mapping hợp lệ:

- Quản lý lead đa nguồn → ưu tiên App Sales/Object Lead nếu Workspace và catalog chứng minh đủ capability.
- Lead chuyển `converted` → Triggered Flow; lấy trưởng phòng qua node Organization; gửi email cho owner và trưởng phòng, sau khi `$process-creator` xác nhận node/contract.
- Quan hệ máy lọc–lõi lọc → cân nhắc Product + junction Object có cardinality rõ; automation cảnh báo chỉ chốt sau feasibility check.
- Số tiền bằng chữ trên hóa đơn → Formula nếu `$object-info` xác nhận runtime; template/button/layout qua `$document-template`, `$object-button`, `$object-layout`.

Không gọi một gap là “có sẵn” chỉ vì tên Object tương tự. Khi Cogover không đáp ứng, ghi lý do chính xác và chỉ đề xuất phần code/tích hợp ngoài phạm vi.

### 2.3 Thiết kế dữ liệu sơ bộ đúng chuẩn

Khi giải pháp cần Object/field/relation:

1. Xác định source of truth, business key, normalization, cardinality/optionality, lookup lifecycle, owner, volume, quyền, audit và migration.
2. Với pattern doanh nghiệp liên quan, nghiên cứu tài liệu chính thức của SAP, Odoo, Salesforce và Zoho trước thiết kế cuối. Chỉ dùng mô tả nghiệp vụ đã ẩn danh; ghi pattern áp dụng, điểm sửa đổi và `N/A` có lý do nếu hệ thống không có pattern tương ứng.
3. Với Object có lifecycle/status, định nghĩa initial/terminal state, mọi transition hợp lệ, actor, precondition, cancel/reject/reopen/undo, failure/retry và audit. Không chỉ liệt kê option.
4. Ưu tiên tái sử dụng Object chuẩn khi semantics, ownership và lifecycle thực sự tương thích; không ép tái sử dụng gây sai mô hình.

### 2.3.1 Quản lý sản phẩm theo số serial hoặc số lô khi chưa cài Inventory

Nếu yêu cầu có quản lý sản phẩm theo **số serial**, **số lô** hoặc **cả hai**, và Workspace đích **chưa cài App Inventory**, thiết kế Object lưu thông tin serial/lô với slug chính xác **`product_batch`**. Đọc bắt buộc [Schema tối thiểu Product batch cho serial và lô](references/product-batch-serial.md) để đưa danh sách trường, kiểu dữ liệu, options và quan hệ vào giải pháp, data design và workbook Object.

- Dùng `$app-menu-manager` xác minh App Inventory đã cài hay chưa; không suy ra chưa cài chỉ vì tài khoản không nhìn thấy menu. Dùng `$object-info` kiểm tra `product_batch` và `product` hiện có, kể cả khi Inventory chưa được cài.
- Nếu `product_batch` đã tồn tại và tương thích, tái sử dụng/bổ sung phần thiếu; không tạo Object lưu serial/lô trùng chức năng. Nếu cùng slug nhưng khác semantics/schema, nêu xung đột để chốt giải pháp, không tự thay thế hoặc đổi slug.
- Với thiết kế mới, dùng đủ 10 trường nghiệp vụ trong reference; giữ `name` là record-name kiểu `short_text`, `product` là `reference` bắt buộc tới `product`, còn `serial_number` và `batch_number` là hai trường riêng. Resolve hoặc thiết kế `product` trước `product_batch`.
- Chốt mỗi bản ghi đại diện cho một đơn vị sản phẩm có serial hay một lô sản phẩm; nếu quản lý cả hai, chốt cách gắn serial với lô. Quy tắc bắt buộc và phạm vi duy nhất phải theo chế độ quản lý; không bắt buộc serial cho sản phẩm chỉ quản lý theo lô, không cấm nhiều serial cùng số lô. Không coi schema này là đã triển khai tồn kho, nhập/xuất hoặc định giá Inventory.
- Đây là quy tắc thiết kế; chỉ tạo/bổ sung schema sau Gate Data Model và Gate Plan, bằng skill chuyên trách. Khi Inventory đã cài, khảo sát và tái sử dụng cấu hình Inventory hiện có thay vì áp fallback này.

### 2.4 Kiểm tra giải pháp và reviewer tùy chọn

Trước khi giao mỗi revision giải pháp:

1. Luôn chạy coordinator self-check về coverage, false reuse, feasibility, capability chưa chứng minh, thiết kế dữ liệu, cardinality, state loophole, permission/audit, dependency, acceptance và câu hỏi còn thiếu.
2. Nếu `Reviewer mode: ON`, tạo một sub-agent `solution_reviewer` độc lập với author. Chỉ giao requirement đã sanitize, Workspace snapshot/evidence và bản gần-final; không đưa kết luận mong đợi.
3. Khi reviewer được bật, xử lý từng finding. Không mở gate nếu reviewer chưa chạy, verdict `RECHECK_REQUIRED`, còn finding `CRITICAL/HIGH` hoặc finding ảnh hưởng recommendation/schema/acceptance chưa giải quyết.
4. Nếu `Reviewer mode: OFF`, bỏ qua bước tạo/recheck reviewer và ghi `NOT_REQUESTED`; coordinator vẫn phải xử lý mọi finding phát hiện trong self-check.
5. Chạy validator theo [Artifact contracts](references/artifact-contracts.md).

Tạo `danh-sach-yeu-cau-va-giai-phap-so-bo-vN.md` với đúng hai bảng cốt lõi:

- Bảng 1: `Mã yêu cầu | Mô tả yêu cầu | Trạng thái làm rõ | Mã câu hỏi cần trả lời | Giải pháp sơ bộ/cuối cùng`.
- Bảng 2: `Mã câu hỏi | Mã yêu cầu | Nội dung câu hỏi | Nội dung trả lời`.

Sau mỗi vòng trả lời, tạo `vN+1`, cập nhật cả hai bảng và kiểm tra lại phần ảnh hưởng; nếu `Reviewer mode: ON`, reviewer recheck theo protocol. Giao `solution_reader` tạo HTML từ Markdown đã kiểm tra: mỗi câu hỏi có ô nhập gắn `Q-ID`, nút lưu câu trả lời ra file JSON local bằng JavaScript và nút Sáng/Tối. Khi người dùng chat “đã trả lời”, đọc file theo quy trình trong reference bản đọc; không coi thao tác lưu hoặc câu chat này là phê duyệt giải pháp.

Khi tất cả yêu cầu đã rõ, tạo revision cuối với trạng thái `PENDING_USER_CONFIRMATION`, đổi cột giải pháp thành giải pháp cuối và bỏ hoàn toàn Bảng 2. Sub-agent tạo lại HTML cùng revision, không còn form câu hỏi cũ. Giao cả Markdown và HTML, yêu cầu người dùng xác nhận rõ đúng filename/revision rồi kết thúc turn.

### Gate Solution

Chỉ đi tiếp ở turn sau khi người dùng xác nhận revision cuối. Gate luôn yêu cầu validator `PASS`, không còn blocker và người dùng xác nhận; chỉ yêu cầu reviewer verdict khi `Reviewer mode: ON`. Mọi thay đổi yêu cầu/giải pháp sau đó làm approval `STALE`, tăng revision và quay lại bước kiểm tra/gate tương ứng.

## Phase 3 — Thiết kế chi tiết và kế hoạch

Chỉ bắt đầu từ solution revision đã xác nhận.

### 3.1 Data design

1. Tạo `data-design-vN.md` làm nguồn chuẩn gồm Object, field, relation, option, state machine, security/audit, data quality/migration và impact lên cấu hình hiện có. Giữ đủ thông tin trường đang có cần cho AI; ghi phạm vi trường đưa vào Excel theo contract.
2. Giao `data_design_reader` ở `DESIGN_ONLY` dùng skill spreadsheet/công cụ XLSX tạo `cogover-objects-vN.xlsx` để người dùng đọc. Mỗi trường có `Notes` giải thích chi tiết lý do cần, nghiệp vụ phục vụ và mã `REQ-ID`; bỏ trường đã có không cần sửa, trừ trường rất quan trọng cần đưa vào để duyệt. Cột `Field name` đứng đầu bên trái, cố định khi cuộn, rộng 100px; các cột khác không quá 160px, xuống dòng và đủ chiều cao để đọc nội dung. Đây là workbook duyệt, không phải file import đầy đủ; xem profile trong reference bản đọc.
3. Sau Excel, chính `data_design_reader` tạo `data-design-vN.html` từ Markdown chuẩn, có sơ đồ quan hệ giữa các Object và bảng giải thích từng Object dùng làm gì, nghiệp vụ chi tiết và `REQ-ID`. Coordinator đối chiếu Markdown↔Excel↔HTML và chạy validator chế độ `--review-workbook`; không áp validator import yêu cầu mọi trường hiện có lên bản duyệt đã lọc. Nếu cần file import, tạo riêng bằng `$create-cogover-objects` từ Markdown đã duyệt và dùng validator import tương ứng.
4. Nếu `Reviewer mode: ON`, tạo sub-agent `data_design_reviewer` độc lập để kiểm tra cả Markdown lẫn workbook; sửa và recheck finding ảnh hưởng schema/state/acceptance. Nếu `OFF`, bỏ qua reviewer, ghi `NOT_REQUESTED` và hoàn tất coordinator self-check trước gate.
5. Nếu không cần Object/field/relation mới hoặc sửa đổi, ghi `DATA_MODEL_NOT_APPLICABLE` cùng bằng chứng và bỏ workbook.

### Gate Data Model

Sau khi data design đã qua validator và coordinator self-check, đồng thời qua reviewer nếu `Reviewer mode: ON`, giao `data-design-vN.md` + `cogover-objects-vN.xlsx` + `data-design-vN.html` cùng revision, hoặc `DATA_MODEL_NOT_APPLICABLE` cùng bằng chứng. Người dùng có thể đọc Excel/HTML để duyệt; xác nhận phải gắn với revision Markdown nguồn, Workspace/environment và data model. Sau đó kết thúc turn.

Chỉ bắt đầu mục 3.2 ở turn sau khi Gate Data Model đã được người dùng xác nhận. Mọi thay đổi schema/state hoặc requirement ảnh hưởng data model sau approval làm baseline `STALE`; tăng revision, kiểm tra lại và quay lại Gate Data Model trước khi lập hoặc sửa kế hoạch triển khai. Chỉ recheck reviewer khi `Reviewer mode: ON`.

### 3.2 Kế hoạch triển khai

Chỉ lập kế hoạch từ data model revision đã được người dùng xác nhận, hoặc quyết định `DATA_MODEL_NOT_APPLICABLE` đã được xác nhận.

Tạo `implementation-plan-vN.md` bằng cách định tuyến từng work item tới skill nguồn chuẩn:

| Hạng mục | Skill chính |
|---|---|
| Object/field/option/formula/relation | `$object-info` |
| Record/fixture/migration nhỏ | `$object-record` |
| Filter/list view | `$object-filter` |
| Layout/UI script/form | `$object-layout`, `$layout-scripting`, `$object-form` |
| Button/action chain | `$object-button` |
| Transition/path/history | `$object-transition-rule`, `$object-path-component`, `$object-history-tracking` |
| Role/data security | `$user-permission` |
| Process | `$process-creator` |
| Document template | `$document-template` |
| Report/dashboard | `$report-builder`, rồi `$dashboard-builder` |
| App/menu/icon | `$app-menu-manager`, `$cogover-icon` |

Mỗi `W-ID` phải có `REQ-ID`, current→target delta, skill, dependency `W-ID`, parallel group, resource lock, acceptance, read-back, test và rollback/containment. Tính DAG thực tế theo các quy tắc:

- Object/field/option/relation và base fields luôn ở wave đầu; lookup target trước lookup phụ thuộc.
- Formula sau base field và runtime validation; status/options trước transition/path/process condition.
- Filter/layout/button/report/process chỉ chạy sau schema mà chúng tham chiếu.
- Với phạm vi Mobile, work item layout phải ghi rõ Web/Mobile/dùng chung; work item Send Notification phải resolve bản ghi `notification_channel` và các trường kênh trước khi cấu hình node. Bổ sung test theo persona trên Android/iOS trong phạm vi, gồm nhận thông báo trong ứng dụng và nhận thêm push khi không mở ứng dụng nếu có yêu cầu mobile push.
- Saved report phải preview đúng trước dashboard; App/menu sau khi action target tồn tại.
- Với `NEW_APP`, thêm chuỗi phụ thuộc `KPI/report source → preview/reconciliation PASS → Overview Dashboard → Home/Overview menu wiring`. `Home` là menu cấp 1 dạng nhóm; `Overview` là menu cấp 2 và là default target. Nếu Dashboard `NOT_SUPPORTED`, thay đúng target Overview bằng report/page fallback đã chứng minh, giữ traceability và limitation. Không áp chuỗi tái cấu trúc này cho `CUSTOMIZE_EXISTING_APP` nếu người dùng không yêu cầu.
- Với App có Menu Item cấp 1, thêm work item icon riêng trước work item tạo/cập nhật menu: `library discovery → reuse exact asset hoặc generate SVG App Menu → technical validation → upload library → resolve returned library URL/ID → set menu icon → read-back`. Root menu parent/icon phải hoàn tất trước các menu con phụ thuộc khi API/menu builder yêu cầu.
- Chỉ đánh dấu song song khi dependency đã hoàn tất và lock không trùng/bao nhau. Cấu hình replacement/full-state luôn single-writer.

Kế hoạch bắt buộc có requirement traceability, execution waves, dependency DAG, lock register, snapshot strategy, test/UAT cases, unsupported/external items, rollout và containment. Chạy validator và coordinator preflight; không mở gate khi còn requirement không map, dependency cycle, lock conflict, `READY` item chứa `TBD/UNKNOWN` hoặc test không quan sát được.

Viết diễn giải kế hoạch bằng tiếng Việt dễ hiểu như phần yêu cầu/giải pháp. Sau khi Markdown đã kiểm tra, giao `plan_reader` tạo `implementation-plan-vN.html` từ đúng nguồn để người dùng xem; có danh sách việc, mã `W-ID`, trạng thái và dấu hoàn thành tương ứng. Markdown vẫn là nguồn chuẩn cho thực thi.

### Gate Plan

Giao `implementation-plan-vN.md` và HTML cùng revision được lập từ đúng data model baseline đã duyệt. Yêu cầu người dùng duyệt rõ filename/revision Markdown nguồn, Workspace/environment và change set; sau đó kết thúc turn. Duyệt data model và plan không thay thế confirmation hẹp của `$process-creator`, delete, replacement, publish/activate, quyền nhạy cảm hoặc side effect bên ngoài.

## Phase 4 — Thực thi, kiểm thử và bàn giao

Chỉ chạy `APPLY_APPROVED_PLAN` sau khi Gate Data Model đã qua trước, rồi Gate Plan cũng đã qua:

1. Xác thực lại credential theo Gate Credential, xác minh Workspace/environment và kiểm tra drift so với snapshot trong plan. Nếu credential không còn `VERIFIED` hoặc drift ảnh hưởng delta/dependency, dừng và revise/reapprove khi cần.
2. Trước khi sửa bất kỳ Object/field/App/layout/filter/button/transition/report/dashboard/process/menu/quyền cũ nào, lưu snapshot redacted đủ để diff/khôi phục thủ công vào `snapshots/pre-apply-<timestamp>/`; tạo manifest gồm resource ID/slug, thời điểm, hash và plan `W-ID`.
3. Thực hiện theo topological wave. Chỉ giao sub-agent các `W-ID` độc lập; một single-writer cho mỗi lock key. Không truyền secret trong prompt; cấp credential qua secret channel theo Workspace/W-ID/quyền/thời hạn.
   - Khi work item App/Menu có Menu Item cấp 1, tạo sub-agent chuyên trách `app_menu_icon_specialist` và yêu cầu dùng `$cogover-icon` profile **App Menu**. Agent này phải: đọc thư viện hiện có trước; tái sử dụng exact asset phù hợp khi không mơ hồ; nếu chưa có thì thiết kế SVG `18×18`, kiểm tra XML/stroke/render, upload file và thêm vào thư viện; trả mapping `menu slug → source(REUSE/CREATE) → library name → library item ID/URL`. Agent không được sửa menu tree. Coordinator hoặc executor `$app-menu-manager` là single writer cài mapping icon vào menu sau barrier icon PASS.
   - Tách lock `workspace/icon-library/<asset-name>` khỏi lock `workspace/app/<app-id>/menu-tree`; không cho hai agent cùng upload/cài một asset hoặc cùng sửa menu. Chuẩn bị xong toàn bộ icon cấp 1 trước batch menu mutation để tránh cây menu dở dang.
4. Sau mỗi mutation, đọc lại resource và so postcondition trước khi mở dependency downstream. Khi timeout, read-back trước retry.
   - Khi hoàn tất từng `W-ID` và đủ read-back/test đã duyệt, cập nhật ngay `DONE` và `[x]` trong Markdown, rồi giao `plan_reader` đồng bộ dấu hoàn thành trên HTML. Chưa đủ bằng chứng thì giữ trạng thái phù hợp, không tick trước. Ghi thời điểm, Agent thực hiện, ID tài nguyên, bằng chứng, phần còn lại và bước tiếp theo để Agent khác tiếp tục; dùng quy trình checkpoint trong reference bản đọc. Lỗi tạo HTML không làm chạy lại việc đã hoàn tất.
   - Với `NEW_APP`, read-back phải chứng minh `Home` là root group, `Overview` là child/default target, action trỏ đúng Dashboard đã reconciled hoặc fallback đã ghi trong plan; ACL Dashboard/report/menu phải nhất quán theo persona. Với `CUSTOMIZE_EXISTING_APP`, regression check phải chứng minh cây menu cũ không bị tái cấu trúc ngoài change set.
   - Với icon menu, read-back phải chứng minh từng Menu Item cấp 1 có đúng icon URL/ID từ thư viện; không dùng `file_id`, URL upload tạm hoặc asset không resolve được. Regression check giữ nguyên action, parent, order, default, ACL, platform và status ngoài field `icon`.
5. Không auto-delete để rollback. Khi partial failure, giữ ID/state, chặn downstream, containment và xin approval nếu recovery có tính destructive.
6. Chạy test theo persona và acceptance, regression các cấu hình bị ảnh hưởng, cleanup đúng fixture do lần chạy tạo và giữ evidence đã redacted.
   - Với phạm vi Mobile, ghi riêng kết quả thao tác và bố cục trên Android/iOS được yêu cầu. Với Send Notification, đối chiếu bản ghi kênh và các trường được tick, kiểm tra nhận trong ứng dụng và mobile push khi không mở ứng dụng; không coi node chạy thành công là bằng chứng đã nhận push. Nếu chưa có thiết bị hoặc evidence, ghi rõ chưa kiểm thử phần đó.
7. Tạo `test-handover-vN.md` map `REQ → W → T`, ghi actual resource IDs, PASS/FAIL, deviation, limitation, residual risk và UAT/handoff.

Không tuyên bố hoàn tất nếu chưa có read-back và test evidence tương ứng.
