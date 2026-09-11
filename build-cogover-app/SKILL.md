---
name: build-cogover-app
description: "Điều phối dự án Cogover end-to-end: xác thực API key đúng Workspace, khảo sát App/Object, làm rõ và fit-gap yêu cầu BRD/SRS, thiết kế Object/state machine, kế hoạch có dependency, triển khai qua các cổng duyệt. Chỉ dùng khi người dùng gọi $build-cogover-app hoặc đã đồng ý rõ; thay đổi đơn lẻ dùng skill chuyên trách hoặc $cogover-overview."
metadata:
  author: cogover
  version: "3.0.1"
---

# Build Cogover App

- **Phiên bản:** `3.0.1`
- **Ngày phát hành:** `2026-09-11`

Đóng vai solution architect, database architect và chuyên gia phần mềm quản trị doanh nghiệp: thiết kế cấu hình khả thi trên Cogover, không xử lý như một dự án phần mềm độc lập và không bắt đầu từ API payload.

Workflow cần môi trường hỗ trợ sub-agent và chia sẻ artifact có phạm vi. Nếu thiếu, chỉ hoàn tất phần tư vấn/chuẩn bị không phụ thuộc điều phối, ghi rõ bước chưa thực hiện và điều kiện để tiếp tục; không tự tuyên bố đã chạy review độc lập. Công cụ XLSX là skill spreadsheet sẵn có hoặc thư viện tương đương giữ đúng schema và vượt qua validator.

## Chính sách kích hoạt

Skill chạy kỹ và mất nhiều thời gian nên không được tự kích hoạt:

- Chỉ bắt đầu khi người dùng gọi `$build-cogover-app` hoặc nhắc rõ tên `build-cogover-app` với ý định sử dụng. AI có thể đề xuất skill khi nhận thấy dự án Cogover end-to-end, nhưng phải nêu ngắn phạm vi/thời gian và chờ người dùng **đồng ý sử dụng** trước khi tải hoặc thực hiện workflow.
- Yêu cầu chung như “xây App Cogover”, “phân tích BRD”, “tư vấn triển khai” không tự động là sự đồng ý; trước khi có xác nhận, dùng skill chuyên trách cho tác vụ đơn lẻ hoặc chỉ trả lời ở mức tư vấn chung.
- Đã kích hoạt rõ trong task/chat hiện tại thì không xin lại cho từng phase; Gate Solution, Data Model, Plan và gate hẹp vẫn áp dụng độc lập.

## Nguồn chuẩn và tài liệu

Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Skill này không có endpoint riêng: probe credential dùng `POST /bapi/v1/auth-token` (API Key Bearer) qua `$cogover-api-auth`; thao tác Workspace khác thực hiện qua các skill chuyên trách được định tuyến ở mục 3.2. Không đưa API key, cookie, token vào prompt sub-agent, file bàn giao, lệnh shell literal, log hay câu trả lời; cấp credential cho sub-agent qua secret channel của runtime theo [Orchestration and gates](references/orchestration-and-gates.md#nguyên-tắc-điều-phối).

| Khi làm gì | Đọc |
|---|---|
| Hiểu Platform, App chuẩn và định tuyến skill | [$cogover-overview](../cogover-overview/SKILL.md) cùng reference liên quan |
| Đã biết Workspace đích, trước mọi khảo sát | [Credential preflight](references/credential-preflight.md) |
| Tạo hoặc sửa file bàn giao | [Artifact contracts](references/artifact-contracts.md) |
| Giao sub-agent, mở cổng duyệt, thay đổi Workspace | [Orchestration and gates](references/orchestration-and-gates.md) |
| Tạo bản HTML/Excel cho người dùng, nhận thông báo “đã trả lời”, cập nhật tiến độ thực thi | [Bản đọc HTML/Excel](references/human-readable-deliverables.md) |
| Yêu cầu quản lý sản phẩm theo serial/lô khi chưa cài App Inventory | [Product batch](references/product-batch-serial.md) |

Dùng response mới nhất của Workspace và skill chuyên trách làm nguồn chuẩn cho trạng thái/capability. Không coi một Object, menu hoặc tên App tồn tại là bằng chứng tính năng end-to-end đã hoạt động.

### Khả năng chuẩn trên Mobile cần đưa vào giải pháp

- Cogover có ứng dụng **Android và iOS**: tạo/sửa/xem/xoá bản ghi Object; xem App; xem/tạo/xoá lượt chạy Process; xem phòng ban/nhân sự/vị trí; nhận push notification. Thiết kế phạm vi thao tác theo quyền của từng persona.
- Layout bản ghi có thể **riêng cho Web**, **riêng cho Mobile** hoặc **dùng chung**; ghi lựa chọn trong giải pháp và chuyển cấu hình `isWeb`/`isMobile` cùng bố cục cho `$object-layout`.
- Node **Send Notification** trong Process gửi đến mobile khi **Loại thông báo** là **All** hoặc **In app** — hai bản ghi của Object `notification_channel` với các trường kênh tương ứng được tick; khi **mobile push** được tick, người nhận nhận thêm push mà không cần mở ứng dụng. Dùng `$object-info` và `$object-record` đọc schema/bản ghi kênh thật, rồi `$process-creator` cấu hình node; không đoán ID hoặc slug trường kênh. Xem [Thông báo ở Tầng 2](../cogover-overview/references/tang2-business-logic.md#thông-báo).

Yêu cầu nằm trong các khả năng trên: ưu tiên ứng dụng Cogover chuẩn trong fit-gap; xác minh cấu hình và quyền trên Workspace đích trước triển khai.

## Chế độ thực thi và nguyên tắc bất biến

Ghi rõ mode trong mọi lời gọi skill con:

1. `DISCOVERY_ONLY`: chỉ đọc state; một API đọc có thể dùng `POST`, phân loại theo side effect chứ không theo HTTP verb.
2. `DESIGN_ONLY`: chỉ phân tích và tạo artifact cục bộ.
3. `APPLY_APPROVED_PLAN`: chỉ thực hiện work item `READY` trong đúng plan revision đã được duyệt.

Mặc định `DISCOVERY_ONLY`. Trước Gate Plan, luôn truyền cho skill con/sub-agent:

> Chỉ đọc/phân tích. Không create, update, delete, upload, activate, publish tài nguyên Workspace, gửi thông báo, chạy process hay thay đổi Workspace; được tạo file bàn giao local đã được giao ở DESIGN_ONLY.

Reviewer độc lập là tùy chọn để giảm thời gian chạy:

- Mặc định `Reviewer mode: OFF`: không tạo `solution_reviewer` hoặc `data_design_reviewer`; validator, coordinator self-check và các approval gate vẫn bắt buộc. Ghi `NOT_REQUESTED`/`NOT_APPLICABLE` vào các trường reviewer; thiếu reviewer hoặc reviewer verdict không phải lỗi chặn gate.
- Chỉ chuyển `Reviewer mode: ON` khi người dùng yêu cầu rõ **“bật các reviewer”** hoặc diễn đạt tương đương; không tự bật theo độ lớn, độ phức tạp hay mức rủi ro. Khi `ON`, áp dụng reviewer cho cả solution và data design theo [protocol reviewer](references/orchestration-and-gates.md#reviewer-độc-lập-tùy-chọn), ghi bằng chứng yêu cầu của người dùng trong artifact và giữ mode cho các revision tiếp theo đến khi người dùng yêu cầu tắt.

Nguyên tắc:

- Không đoán thông tin nghiệp vụ đang chặn một quyết định: dùng `TBD`/`UNKNOWN`, hỏi người dùng và dừng đúng gate.
- Đã có Workspace đích: không bắt đầu Phase 1, không tạo artifact, không giao sub-agent cho đến khi Gate Credential đạt `VERIFIED`.
- Có API key, duyệt giải pháp hay duyệt data model đều không phải quyền mutation.
- Chỉ dùng capability Cogover đã được chứng minh. Không khả thi thì ghi `NOT_SUPPORTED` hoặc đề xuất hạng mục code/tích hợp cho team khác; không tự code nghiệp vụ hoặc tích hợp Workspace trong skill này. Mã HTML/JavaScript cho bản đọc local và lưu câu trả lời theo contract bản đọc được phép.
- Không ghi approval giả; chỉ lưu nội dung xác nhận thực tế của người dùng kèm revision.
- `NEW_APP`: mặc định thiết kế Menu Item cấp 1 dạng nhóm `Home` và Menu Item cấp 2 `Overview` làm menu mặc định, trỏ tới Dashboard tổng quan các KPI quan trọng của App. Chỉ tạo/wire Dashboard sau khi report/KPI nguồn đã preview và đối soát thành công. Dashboard không được Workspace/runtime hỗ trợ thì dùng Overview dạng report/page đã chứng minh làm fallback và ghi limitation; không tạo Dashboard rỗng hoặc giả. `CUSTOMIZE_EXISTING_APP`: giữ nguyên information architecture/menu hiện có trừ khi người dùng yêu cầu rõ tái cấu trúc.
- Custom App: mọi Menu Item cấp 1 nên có icon App Menu phù hợp ngữ nghĩa; chỉ bỏ icon khi người dùng yêu cầu rõ hoặc capability/runtime chứng minh không hỗ trợ, và ghi quyết định vào solution/plan. Menu tree chưa hoàn tất nếu root-menu icon chưa được resolve, cài và read-back.

## Đầu vào và nơi lưu artifact

Markdown (.md) là nguồn chuẩn để AI phân tích, triển khai và bàn giao cho Agent khác; HTML/Excel chỉ là bản để người dùng đọc, do sub-agent `solution_reader`, `data_design_reader`, `plan_reader` tạo từ đúng revision Markdown (bắt buộc kể cả khi `Reviewer mode: OFF`). Cách viết, phân công, kiểm tra và tiếp nhận câu trả lời: [Bản đọc HTML/Excel](references/human-readable-deliverables.md#nguồn-chuẩn-cách-viết-và-phân-công).

Thu thập tối thiểu:

- Workspace đích bằng alias, URL/domain hoặc identifier; xác định `sandbox`, `UAT` hay `production`.
- Yêu cầu nghiệp vụ chi tiết và version/ngày của nguồn; xác định `NEW_APP`, `CUSTOMIZE_EXISTING_APP` hoặc kết hợp.
- Phạm vi MVP/future phase, ưu tiên và tiêu chí thành công.
- API key của Super Admin qua secret field, scoped environment, secret manager, credential broker hoặc cơ chế bí mật của runtime. Đã có Workspace đích thì key là đầu vào bắt buộc; không nhận hoặc lưu key trong artifact, repository hay log.

Nơi lưu mặc định nếu chưa có: `artifacts/cogover-implementation/<project-slug>/`. Mỗi lần người dùng trả lời một vòng câu hỏi, tạo revision `vN+1`; không ghi đè revision đã giao. Tạo theo thứ tự:

1. `danh-sach-yeu-cau-va-giai-phap-so-bo-vN.md` và bản đọc cùng tên `.html`; câu trả lời lưu trong `answers/`.
2. `data-design-vN.md`, `cogover-objects-vN.xlsx` để người dùng duyệt và `data-design-vN.html` có sơ đồ quan hệ, khi có thay đổi mô hình dữ liệu.
3. `implementation-plan-vN.md` và bản đọc cùng tên `.html`, đồng bộ trạng thái từng việc trong quá trình thực hiện.
4. `snapshots/pre-apply-<timestamp>/` trước mutation cấu hình hiện có.
5. `test-handover-vN.md` sau triển khai.

## Phase 0 — Gate Credential bắt buộc

Khi người dùng đã cung cấp Workspace đích, làm theo [Credential preflight](references/credential-preflight.md):

1. Resolve URL canonical và API key qua kênh bí mật; runtime chưa có credential thì yêu cầu người dùng cung cấp qua secret input.
2. Dùng `$cogover-api-auth` gọi `POST /bapi/v1/auth-token` trên chính Workspace đích (probe read-only); không dùng browser session hoặc key Workspace khác làm fallback.
3. Chỉ chuyển `VERIFIED` khi auth thành công, session còn hiệu lực, `workspaceDomain`/`workspaceId` khớp Workspace đích và probe đọc tối thiểu App/Object không bị từ chối quyền; ghi evidence đã redacted theo reference.
4. `MISSING`, `INVALID`, `WORKSPACE_MISMATCH`, `INSUFFICIENT_DISCOVERY_ACCESS` hoặc `UNVERIFIED_TRANSIENT`: dừng toàn bộ workflow và báo cách khắc phục; không đọc/phân tích yêu cầu, tạo artifact hoặc khởi chạy sub-agent.

Auth thành công không tự chứng minh quyền Super Admin cho mutation; xác minh quyền đặc thù trước work item cần quyền đó. Xác thực lại khi Workspace/key thay đổi, credential bị rotate/revoke, phiên hết hạn hoặc trước `APPLY_APPROVED_PLAN` nếu evidence không còn mới.

## Phase 1 — Đọc yêu cầu, Cogover và Workspace

### 1.1 Chuẩn hóa yêu cầu

1. Đọc toàn bộ nguồn bằng capability phù hợp; giữ nội dung từ bảng, sheet, sơ đồ, phụ lục và comment liên quan. Sanitize secret/PII không cần thiết trước khi chuyển cho sub-agent hoặc nghiên cứu web.
2. Tạo `REQ-001`, `REQ-002`, ...; mỗi yêu cầu tách actor, trigger, input, business rule, output, exception, priority và acceptance criterion.
3. Ghi provenance theo file/page/heading/sheet/dòng khi có thể. Ghi mâu thuẫn và nội dung thiếu; không tự lấp chỗ trống.

### 1.2 Hiểu Platform và App chuẩn

1. Dùng `$cogover-overview`; đọc reference Tầng 1, Tầng 2, Tầng 3 và catalog của mọi App ứng viên.
2. Lập danh sách capability/Object/process chuẩn liên quan; không khẳng định catalog đầy đủ khi chưa có reference hoặc bằng chứng Workspace.
3. Phân biệt `native configuration`, `custom Object/configuration`, `external integration/code` và `unknown`.

### 1.3 Khảo sát Workspace ở `DISCOVERY_ONLY`

1. `$app-menu-manager` đọc App, menu tree, action target, ACL và trạng thái. Đồng thời `$cogover-icon` đọc thư viện icon Workspace, ghi rõ root menu nào đã có asset phù hợp để tái sử dụng, root menu nào cần tạo mới; không tạo trùng asset.
2. `$object-info` đọc Object, field, option, metadata, lookup và related list; phân trang đến hết phạm vi.
3. Thành phần liên quan đọc sâu bằng skill tương ứng: filter, layout/script, form, button, transition/path, history, permission, process, template, report/dashboard và menu.
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
- Create/view/edit layout, mobile/web, filter, button, bulk action và public form. Có phạm vi Mobile: persona dùng Android/iOS nào, thao tác cần hỗ trợ, layout riêng hay dùng chung; với Send Notification: người nhận, kênh `All`/`In app` và nhu cầu nhận thêm mobile push khi không mở ứng dụng.
- Report population, metric, dimension, aggregate, drill-down và quyền xem. `NEW_APP`: KPI nào trên `Home → Overview`, nguồn report/filter của từng KPI, persona được xem và drill-down. Không hỏi/tái cấu trúc `CUSTOMIZE_EXISTING_APP` chỉ để áp mẫu Home/Overview nếu yêu cầu không đụng information architecture.
- Integration, credential owner, error handling, NFR và tiêu chí test.

Mỗi câu hỏi map về `REQ-ID`, nêu decision bị chặn và mức `BLOCKING`/`NON_BLOCKING`. Còn câu `BLOCKING` thì không chốt giải pháp cho requirement đó.

### 2.2 Fit-gap và giải pháp cho từng yêu cầu

Với từng `REQ-ID`, so sánh ba lớp bằng chứng: yêu cầu khách hàng, state Workspace, capability/App chuẩn Cogover. Dùng một disposition: `REUSE_AS_IS`, `CONFIGURE`, `EXTEND`, `INSTALL_STANDARD_APP`, `BUILD_CUSTOM`, `EXTERNAL_INTEGRATION`, `NOT_SUPPORTED`, `UNKNOWN`.

Giải pháp nêu rõ Object/module/process/layout/report/template nào được tái sử dụng hoặc thay đổi, dependency, limitation, acceptance và bằng chứng. Ví dụ mapping hợp lệ:

- Quản lý lead đa nguồn → ưu tiên App Sales/Object Lead nếu Workspace và catalog chứng minh đủ capability.
- Lead chuyển `converted` → Triggered Flow; lấy trưởng phòng qua node Organization; gửi email cho owner và trưởng phòng, sau khi `$process-creator` xác nhận node/contract.
- Quan hệ máy lọc–lõi lọc → Product + junction Object có cardinality rõ; automation cảnh báo chỉ chốt sau feasibility check.
- Số tiền bằng chữ trên hóa đơn → Formula nếu `$object-info` xác nhận runtime; template/button/layout qua `$document-template`, `$object-button`, `$object-layout`.

Không gọi một gap là “có sẵn” chỉ vì tên Object tương tự. Cogover không đáp ứng thì ghi lý do chính xác và chỉ đề xuất phần code/tích hợp ngoài phạm vi.

### 2.3 Thiết kế dữ liệu sơ bộ đúng chuẩn

Khi giải pháp cần Object/field/relation:

1. Xác định source of truth, business key, normalization, cardinality/optionality, lookup lifecycle, owner, volume, quyền, audit và migration.
2. Với pattern doanh nghiệp liên quan, nghiên cứu tài liệu chính thức của SAP, Odoo, Salesforce và Zoho trước thiết kế cuối; chỉ dùng mô tả nghiệp vụ đã ẩn danh; ghi pattern áp dụng, điểm sửa đổi và `N/A` có lý do khi hệ thống không có pattern tương ứng.
3. Object có lifecycle/status: định nghĩa initial/terminal state, mọi transition hợp lệ, actor, precondition, cancel/reject/reopen/undo, failure/retry và audit; không chỉ liệt kê option.
4. Ưu tiên tái sử dụng Object chuẩn khi semantics, ownership và lifecycle thực sự tương thích; không ép tái sử dụng gây sai mô hình.

### 2.3.1 Quản lý sản phẩm theo số serial hoặc số lô khi chưa cài Inventory

Yêu cầu có quản lý sản phẩm theo **số serial**, **số lô** hoặc **cả hai** và Workspace đích **chưa cài App Inventory**: thiết kế Object lưu serial/lô với slug chính xác **`product_batch`** theo [schema tối thiểu Product batch](references/product-batch-serial.md) (danh sách trường, kiểu, options, quan hệ đưa vào giải pháp, data design và workbook).

- Dùng `$app-menu-manager` xác minh App Inventory đã cài hay chưa; không suy ra chưa cài chỉ vì tài khoản không nhìn thấy menu. Dùng `$object-info` kiểm tra `product_batch` và `product` hiện có, kể cả khi Inventory chưa được cài.
- `product_batch` đã tồn tại và tương thích: tái sử dụng/bổ sung phần thiếu, không tạo Object trùng chức năng. Cùng slug nhưng khác semantics/schema: nêu xung đột để chốt giải pháp, không tự thay thế hoặc đổi slug.
- Thiết kế mới: đủ 10 trường nghiệp vụ trong reference; `name` là record-name kiểu `short_text`, `product` là `reference` bắt buộc tới `product`, `serial_number` và `batch_number` là hai trường riêng. Resolve hoặc thiết kế `product` trước `product_batch`.
- Chốt mỗi bản ghi đại diện cho một đơn vị sản phẩm có serial hay một lô; quản lý cả hai thì chốt cách gắn serial với lô. Quy tắc bắt buộc và phạm vi duy nhất theo chế độ quản lý: không bắt buộc serial cho sản phẩm chỉ quản lý theo lô, không cấm nhiều serial cùng số lô. Không coi schema này là đã triển khai tồn kho, nhập/xuất hoặc định giá Inventory.
- Đây là quy tắc thiết kế: chỉ tạo/bổ sung schema sau Gate Data Model và Gate Plan, bằng skill chuyên trách. Inventory đã cài thì khảo sát và tái sử dụng cấu hình Inventory hiện có thay vì áp fallback này.

### 2.4 Kiểm tra giải pháp và reviewer tùy chọn

Trước khi giao mỗi revision giải pháp:

1. Luôn chạy coordinator self-check về coverage, false reuse, feasibility, capability chưa chứng minh, thiết kế dữ liệu, cardinality, state loophole, permission/audit, dependency, acceptance và câu hỏi còn thiếu; xử lý mọi finding phát hiện.
2. `Reviewer mode: ON`: tạo `solution_reviewer` độc lập với author và xử lý finding theo [protocol reviewer](references/orchestration-and-gates.md#reviewer-độc-lập-tùy-chọn); `OFF`: bỏ qua bước reviewer và ghi `NOT_REQUESTED`.
3. Chạy validator theo [Artifact contracts](references/artifact-contracts.md).

`danh-sach-yeu-cau-va-giai-phap-so-bo-vN.md` chỉ có đúng hai bảng contract: Bảng 1 yêu cầu/giải pháp và Bảng 2 câu hỏi (cột và quy tắc trong [Artifact contracts](references/artifact-contracts.md#danh-sach-yeu-cau-va-giai-phap-so-bo-vnmd)). Sau mỗi vòng trả lời, tạo `vN+1`, cập nhật cả hai bảng và kiểm tra lại phần ảnh hưởng (reviewer recheck khi `ON`). Giao `solution_reader` tạo HTML từ Markdown đã kiểm tra: mỗi câu hỏi có ô nhập gắn `Q-ID`, nút lưu câu trả lời ra file JSON local bằng JavaScript và nút Sáng/Tối. Khi người dùng chat “đã trả lời”, đọc file theo [quy trình tiếp nhận](references/human-readable-deliverables.md#khi-người-dùng-nói-đã-trả-lời); thao tác lưu hoặc câu chat này không phải phê duyệt giải pháp.

Khi tất cả yêu cầu đã rõ: tạo revision cuối với trạng thái `PENDING_USER_CONFIRMATION`, đổi cột giải pháp thành giải pháp cuối và bỏ hoàn toàn Bảng 2; sub-agent tạo lại HTML cùng revision, không còn form câu hỏi. Giao cả Markdown và HTML, yêu cầu người dùng xác nhận rõ đúng filename/revision rồi kết thúc turn.

### Gate Solution

Chỉ đi tiếp ở turn sau khi người dùng xác nhận revision cuối. Điều kiện gate: validator `PASS`, không còn blocker, người dùng xác nhận; reviewer verdict chỉ yêu cầu khi `Reviewer mode: ON` (chi tiết: [Approval gates](references/orchestration-and-gates.md#approval-gates)). Mọi thay đổi yêu cầu/giải pháp sau đó làm approval `STALE`: tăng revision và quay lại bước kiểm tra/gate tương ứng.

## Phase 3 — Thiết kế chi tiết và kế hoạch

Chỉ bắt đầu từ solution revision đã xác nhận.

### 3.1 Data design

1. Tạo `data-design-vN.md` làm nguồn chuẩn gồm Object, field, relation, option, state machine, security/audit, data quality/migration và impact lên cấu hình hiện có. Giữ đủ thông tin trường đang có cần cho AI; ghi phạm vi trường đưa vào Excel bằng bảng `workbook-scope` theo contract.
2. Giao `data_design_reader` ở `DESIGN_ONLY` tạo `cogover-objects-vN.xlsx` — workbook duyệt theo từng trường, không phải file import — theo [profile workbook duyệt](references/human-readable-deliverables.md#excel-thiết-kế-dữ-liệu-để-duyệt): chỉ trường mới/cần sửa/rất quan trọng, mỗi trường có `Notes` giải thích lý do, nghiệp vụ và `REQ-ID`, cột `Field name` đứng đầu và cố định. Sau Excel, cùng sub-agent tạo `data-design-vN.html` có sơ đồ quan hệ và bảng giải thích từng Object.
3. Coordinator đối chiếu Markdown↔Excel↔HTML và chạy validator `--review-workbook`; không áp validator import lên bản duyệt đã lọc. Cần file import thì tạo riêng bằng `$create-cogover-objects` từ Markdown đã duyệt và dùng validator import tương ứng.
4. `Reviewer mode: ON`: `data_design_reviewer` độc lập kiểm tra cả Markdown lẫn workbook; sửa và recheck finding ảnh hưởng schema/state/acceptance. `OFF`: ghi `NOT_REQUESTED`, hoàn tất coordinator self-check trước gate.
5. Không cần Object/field/relation mới hoặc sửa đổi: ghi `DATA_MODEL_NOT_APPLICABLE` cùng bằng chứng và bỏ workbook.

### Gate Data Model

Sau validator và coordinator self-check (và reviewer nếu `ON`), giao `data-design-vN.md` + `cogover-objects-vN.xlsx` + `data-design-vN.html` cùng revision, hoặc `DATA_MODEL_NOT_APPLICABLE` cùng bằng chứng, rồi kết thúc turn. Người dùng có thể đọc Excel/HTML để duyệt, nhưng xác nhận phải gắn với revision Markdown nguồn, Workspace/environment và data model.

Chỉ bắt đầu 3.2 ở turn sau khi Gate Data Model đã được xác nhận. Thay đổi schema/state hoặc requirement ảnh hưởng data model sau approval làm baseline `STALE`: tăng revision, kiểm tra lại (reviewer recheck chỉ khi `ON`) và quay lại Gate Data Model trước khi lập hoặc sửa kế hoạch.

### 3.2 Kế hoạch triển khai

Tạo `implementation-plan-vN.md` từ data model revision (hoặc quyết định `DATA_MODEL_NOT_APPLICABLE`) đã được người dùng xác nhận, định tuyến từng work item tới skill nguồn chuẩn:

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

Mỗi `W-ID` có `REQ-ID`, current→target delta, skill, dependency `W-ID`, parallel group, resource lock, acceptance, read-back, test và rollback/containment. Tính DAG thực tế theo:

- Object/field/option/relation và base fields ở wave đầu; lookup target trước lookup phụ thuộc.
- Formula sau base field và runtime validation; status/options trước transition/path/process condition.
- Filter/layout/button/report/process chỉ chạy sau schema mà chúng tham chiếu. Saved report phải preview đúng trước dashboard; App/menu sau khi action target tồn tại.
- Phạm vi Mobile: work item layout ghi rõ Web/Mobile/dùng chung; work item Send Notification resolve bản ghi `notification_channel` và các trường kênh trước khi cấu hình node. Bổ sung test theo persona trên Android/iOS trong phạm vi, gồm nhận thông báo trong ứng dụng và nhận thêm push khi không mở ứng dụng nếu có yêu cầu mobile push.
- `NEW_APP`: thêm chuỗi `KPI/report source → preview/reconciliation PASS → Overview Dashboard → Home/Overview menu wiring`; `Home` là menu cấp 1 dạng nhóm, `Overview` là menu cấp 2 và default target. Dashboard `NOT_SUPPORTED`: thay đúng target Overview bằng report/page fallback đã chứng minh, giữ traceability và limitation. Không áp chuỗi này cho `CUSTOMIZE_EXISTING_APP` nếu người dùng không yêu cầu.
- App có Menu Item cấp 1: thêm work item icon riêng trước work item tạo/cập nhật menu: `library discovery → reuse exact asset hoặc generate SVG App Menu → technical validation → upload library → resolve returned library URL/ID → set menu icon → read-back`. Root menu parent/icon hoàn tất trước các menu con phụ thuộc khi API/menu builder yêu cầu.
- Chỉ đánh dấu song song khi dependency đã hoàn tất và lock không trùng/bao nhau; cấu hình replacement/full-state luôn single-writer (xem [Dependency và resource lock](references/orchestration-and-gates.md#dependency-và-resource-lock)).

Kế hoạch bắt buộc có requirement traceability, execution waves, dependency DAG, lock register, snapshot strategy, test/UAT cases, unsupported/external items, rollout và containment; diễn giải bằng tiếng Việt dễ hiểu như phần yêu cầu/giải pháp. Chạy validator và coordinator preflight; không mở gate khi còn requirement không map, dependency cycle, lock conflict, `READY` item chứa `TBD/UNKNOWN` hoặc test không quan sát được. Sau khi Markdown đã kiểm tra, giao `plan_reader` tạo `implementation-plan-vN.html` (danh sách việc, `W-ID`, trạng thái, dấu hoàn thành); Markdown vẫn là nguồn chuẩn cho thực thi.

### Gate Plan

Giao `implementation-plan-vN.md` và HTML cùng revision, lập từ đúng data model baseline đã duyệt. Yêu cầu người dùng duyệt rõ filename/revision Markdown nguồn, Workspace/environment và change set; sau đó kết thúc turn. Duyệt data model và plan không thay thế confirmation hẹp của `$process-creator`, delete, replacement, publish/activate, quyền nhạy cảm hoặc side effect bên ngoài ([gate hẹp của skill con](references/orchestration-and-gates.md#gate-hẹp-của-skill-con)).

## Phase 4 — Thực thi, kiểm thử và bàn giao

Chỉ chạy `APPLY_APPROVED_PLAN` sau khi Gate Data Model đã qua trước, rồi Gate Plan cũng đã qua:

1. Xác thực lại credential theo Gate Credential, xác minh Workspace/environment và kiểm tra drift so với snapshot trong plan. Credential không còn `VERIFIED` hoặc drift ảnh hưởng delta/dependency: dừng và revise/reapprove khi cần.
2. Trước khi sửa bất kỳ Object/field/App/layout/filter/button/transition/report/dashboard/process/menu/quyền cũ nào, lưu snapshot redacted vào `snapshots/pre-apply-<timestamp>/` kèm manifest theo [snapshot contract](references/orchestration-and-gates.md#snapshot-và-mutation-safety).
3. Thực hiện theo topological wave. Chỉ giao sub-agent các `W-ID` độc lập; một single-writer cho mỗi lock key; cấp credential qua secret channel theo Workspace/W-ID/quyền/thời hạn.
   - Work item App/Menu có Menu Item cấp 1: tạo sub-agent `app_menu_icon_specialist` dùng `$cogover-icon` profile **App Menu**. Agent này đọc thư viện hiện có trước; tái sử dụng exact asset phù hợp khi không mơ hồ; chưa có thì thiết kế SVG `18×18`, kiểm tra XML/stroke/render, upload file và thêm vào thư viện; trả mapping `menu slug → source(REUSE/CREATE) → library name → library item ID/URL`; không được sửa menu tree. Coordinator hoặc executor `$app-menu-manager` là single writer cài mapping icon vào menu sau barrier icon PASS.
   - Tách lock `workspace/icon-library/<asset-name>` khỏi lock `workspace/app/<app-id>/menu-tree`; không cho hai agent cùng upload/cài một asset hoặc cùng sửa menu. Chuẩn bị xong toàn bộ icon cấp 1 trước batch menu mutation để tránh cây menu dở dang.
4. Sau mỗi mutation, đọc lại resource và so postcondition trước khi mở dependency downstream; timeout thì read-back trước retry.
   - Hoàn tất từng `W-ID` với đủ read-back/test đã duyệt: cập nhật ngay `DONE` và `[x]` trong Markdown rồi giao `plan_reader` đồng bộ HTML theo [quy trình checkpoint](references/human-readable-deliverables.md#html-kế-hoạch-checkpoint-và-bàn-giao-agent); chưa đủ bằng chứng thì không tick trước. Lỗi tạo HTML không làm chạy lại việc đã hoàn tất.
   - `NEW_APP`: read-back phải chứng minh `Home` là root group, `Overview` là child/default target, action trỏ đúng Dashboard đã reconciled hoặc fallback đã ghi trong plan; ACL Dashboard/report/menu nhất quán theo persona. `CUSTOMIZE_EXISTING_APP`: regression check chứng minh cây menu cũ không bị tái cấu trúc ngoài change set.
   - Icon menu: read-back chứng minh từng Menu Item cấp 1 có đúng icon URL/ID từ thư viện; không dùng `file_id`, URL upload tạm hoặc asset không resolve được. Regression check giữ nguyên action, parent, order, default, ACL, platform và status ngoài field `icon`.
5. Không auto-delete để rollback. Partial failure: giữ ID/state, chặn downstream, containment và xin approval nếu recovery có tính destructive ([partial failure](references/orchestration-and-gates.md#partial-failure)).
6. Chạy test theo persona và acceptance, regression các cấu hình bị ảnh hưởng, cleanup đúng fixture do lần chạy tạo và giữ evidence đã redacted.
   - Phạm vi Mobile: ghi riêng kết quả thao tác và bố cục trên Android/iOS được yêu cầu. Send Notification: đối chiếu bản ghi kênh và các trường được tick, kiểm tra nhận trong ứng dụng và mobile push khi không mở ứng dụng; node chạy thành công không phải bằng chứng đã nhận push. Chưa có thiết bị hoặc evidence thì ghi rõ chưa kiểm thử phần đó.
7. Tạo `test-handover-vN.md` map `REQ → W → T`, ghi actual resource IDs, PASS/FAIL, deviation, limitation, residual risk và UAT/handoff.

Không tuyên bố hoàn tất nếu chưa có read-back và test evidence tương ứng.
