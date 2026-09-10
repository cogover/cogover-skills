# Orchestration and Gates

## Mục lục

1. [Nguyên tắc điều phối](#nguyên-tắc-điều-phối)
2. [Các wave](#các-wave)
3. [Reviewer độc lập tùy chọn](#reviewer-độc-lập-tùy-chọn)
4. [Approval gates](#approval-gates)
5. [Dependency và resource lock](#dependency-và-resource-lock)
6. [Snapshot và mutation safety](#snapshot-và-mutation-safety)

## Nguyên tắc điều phối

- Bắt buộc dùng các sub-agent tạo bản đọc `solution_reader`, `data_design_reader`, `plan_reader` theo [contract bản đọc](human-readable-deliverables.md), với context mới chỉ gồm nguồn cần thiết. Đây là tác vụ tạo HTML/Excel, không phải reviewer; vẫn chạy khi `Reviewer mode: OFF`. Các workstream khác chỉ tách khi độc lập, đủ lớn hoặc reviewer đã được người dùng bật; không tạo agent chỉ để lấp slot.
- Mặc định `Reviewer mode: OFF`. Chỉ chuyển sang `ON` khi người dùng yêu cầu rõ “bật các reviewer” hoặc diễn đạt tương đương; không tự bật theo scope, độ phức tạp hoặc mức rủi ro. Khi `OFF`, bỏ qua `solution_reviewer` và `data_design_reviewer` nhưng vẫn chạy validator, coordinator self-check và approval gate.
- Khi đã biết Workspace đích, Gate Credential là barrier đầu tiên. Không khởi chạy discovery/design sub-agent hoặc tạo artifact trước khi credential đạt `VERIFIED`.
- Mọi sub-agent ở phase discovery/design phải nhận `NO WORKSPACE MUTATION` và trả facts/evidence, open questions, findings, proposed rows cùng dependencies/blockers.
- Coordinator pre-scan và sanitize requirement trước khi giao. Chỉ chuyển phần cần thiết, Workspace identifier, snapshot đã redacted và artifact liên quan.
- Không chèn secret vào natural-language prompt. Nếu agent cần gọi API, cấp credential qua secret channel của runtime, khóa theo agent, mode, Workspace, W-ID/resource, read/mutation scope và thời hạn. Nếu không có secret channel, coordinator tự gọi rồi chuyển snapshot redacted.
- Coordinator là single writer cho Markdown chuẩn; mỗi sub-agent tạo bản đọc là single writer cho HTML/Excel được giao. Coordinator kiểm tra và bàn giao bản đọc, không đồng thời sửa file sub-agent đang ghi. Không cho hai agent sửa cùng file hoặc cùng Workspace resource.
- Dùng barrier: baseline upstream phải ổn định, được review/approve khi cần và không drift trước khi downstream bắt đầu.

## Các wave

### Wave A — Discovery

Chỉ bắt đầu sau Gate Credential `VERIFIED`. Coordinator đọc yêu cầu và `$cogover-overview`. Khi scope đủ lớn, có thể chạy song song:

1. `requirements_analyst`: chuẩn hóa `REQ-ID`, provenance, conflict và `Q-ID`.
2. `workspace_auditor`: đọc App/menu/Object/field/relation và impacted config ở `DISCOVERY_ONLY`.
3. `standard_app_analyst`: đối chiếu catalog App chuẩn với requirement; không bắt đầu data design.

Chỉ hợp nhất từ cùng snapshot time/baseline. Hỏi người dùng câu blocking trước Wave B.

### Wave B — Giải pháp và reviewer tùy chọn

1. Coordinator hoặc `solution_architect` tạo bản gần-final gồm hai bảng contract, evidence và disposition.
2. Coordinator self-check, chạy validator và sửa lỗi.
3. Nếu `Reviewer mode: ON`, giao bản gần-final cho `solution_reviewer` độc lập theo protocol bên dưới; nếu `OFF`, ghi `NOT_REQUESTED` và không tạo reviewer.
4. Coordinator disposition từng finding và sửa artifact. Chạy lại validator; chỉ recheck reviewer khi mode `ON` và finding làm đổi recommendation, schema sơ bộ, state hoặc acceptance.
5. Giao `solution_reader` tạo HTML cùng revision, có input theo Q-ID, lưu JSON local và Sáng/Tối; coordinator kiểm tra trước khi giao Markdown + HTML. Khi người dùng báo “đã trả lời”, đọc/đối chiếu JSON theo contract, không coi là approval. Mỗi vòng trả lời tạo revision kế tiếp và sinh lại HTML.
6. Khi không còn blocker, bỏ Bảng 2, tạo lại HTML không còn form câu hỏi, giao revision cuối Markdown + HTML rồi dừng tại Gate Solution.

### Wave C — Data design và reviewer tùy chọn

Chỉ bắt đầu sau Gate Solution:

1. Nghiên cứu pattern liên quan trong tài liệu chính thức SAP, Odoo, Salesforce và Zoho; ẩn danh dữ liệu khách hàng.
2. Coordinator hoặc `data_architect` thiết kế Object/field/relation/state/migration/security.
3. Chỉ chia domain song song sau khi khóa glossary, source of truth và ownership boundary. Coordinator hợp nhất cross-domain relation tuần tự.
4. Coordinator tạo Markdown chuẩn và workbook-scope; giao `data_design_reader` tạo Excel duyệt với Notes/REQ-ID và độ rộng/cố định cột đúng contract, sau đó tạo HTML sơ đồ quan hệ và giải thích Object. Coordinator self-check, đối chiếu các bản và chạy validator `--review-workbook`; chỉ dùng validator `$create-cogover-objects` cho file import riêng khi thực sự cần.
5. Nếu `Reviewer mode: ON`, giao cả hai file cho `data_design_reviewer` độc lập; sửa và recheck phần ảnh hưởng khi cần. Nếu `OFF`, ghi `NOT_REQUESTED` và không tạo reviewer.
6. Giao Markdown thiết kế dữ liệu + Excel duyệt + HTML cùng revision, hoặc `DATA_MODEL_NOT_APPLICABLE` cùng bằng chứng, rồi dừng tại Gate Data Model. Không bắt đầu Wave D trong cùng turn trước khi người dùng xác nhận data model baseline.

### Wave D — Implementation plan

Chỉ lập plan từ solution đã duyệt và data design đã được người dùng xác nhận tại Gate Data Model:

1. Đánh giá automation/process feasibility trước để khóa mechanism và schema dependency.
2. Khi scope đủ lớn, có thể tách planner độc lập: UI configuration, analytics, governance/migration/test.
3. Coordinator hợp nhất WBS, DAG, waves, lock register và test plan.
4. Chạy artifact validator và coordinator preflight. Không cần generic plan reviewer; dùng specialist khi contract cụ thể chưa chắc.
5. Giao `plan_reader` tạo HTML từ Markdown chuẩn, coordinator kiểm tra; giao cả hai rồi dừng tại Gate Plan.

### Wave E — Apply

Sau tất cả approval áp dụng, kiểm tra drift, snapshot cấu hình cũ rồi phát hành work item theo topological wave. Yêu cầu read-back/postcondition trước khi mở downstream wave. Khi từng W-ID đủ điều kiện hoàn tất, cập nhật ngay DONE/[x] và bằng chứng/next step trong checkpoint Markdown, rồi giao `plan_reader` đồng bộ HTML. Ghi checkpoint và nhật ký để Agent khác tiếp tục; lỗi sinh bản đọc không làm chạy lại mutation đã xong.

Với `NEW_APP`, mặc định dựng information architecture `Home` (root group) → `Overview` (child/default) sau khi Dashboard KPI đã được tạo từ report nguồn preview/reconcile PASS. Nếu Dashboard không được capability/runtime hỗ trợ, dùng report/page đã chứng minh làm target fallback và ghi limitation. Không áp mẫu này để tái cấu trúc `CUSTOMIZE_EXISTING_APP` nếu người dùng không yêu cầu rõ.

Với custom App có menu cấp 1, tạo `app_menu_icon_specialist` dùng `$cogover-icon` trước menu mutation. Agent chuyên trách đọc thư viện và ưu tiên tái sử dụng exact asset; chỉ thiết kế/upload SVG App Menu mới khi chưa có asset phù hợp. Agent trả mapping library đã xác minh nhưng không sửa menu tree. `$app-menu-manager` cài icon sau barrier icon PASS và read-back từng root menu; icon-library và menu-tree dùng lock/single-writer riêng.

## Reviewer độc lập tùy chọn

### Chế độ reviewer

- `OFF` là mặc định. Không tạo reviewer và không yêu cầu reviewer task ID, identity check hoặc verdict để mở gate; dùng `NOT_REQUESTED`/`NOT_APPLICABLE` trong artifact.
- `ON` chỉ khi có yêu cầu rõ của người dùng, ví dụ “bật các reviewer”. Ghi yêu cầu kích hoạt trong artifact và áp dụng reviewer độc lập cho cả solution lẫn data design ở các revision tiếp theo, cho đến khi người dùng yêu cầu tắt.
- Việc tắt reviewer không tắt validator, coordinator self-check, traceability, acceptance criteria hoặc approval của người dùng.
- Các mục Identity, checklist, finding và verdict bên dưới chỉ bắt buộc khi mode `ON`.

### Identity và đầu vào

- Reviewer phải khác author/coordinator của artifact. Ghi task/agent ID vào artifact.
- Chỉ giao raw artifact gần-final, requirement đã sanitize, snapshot/evidence redacted và contract cần kiểm tra.
- Không đưa expected verdict, kết luận mong muốn, suspected bug hoặc cách sửa; reviewer phải tự tìm vấn đề.

### Checklist solution

- Mọi `REQ-ID` được hiểu đúng và có disposition/evidence; không false reuse từ tên Object/menu.
- Câu hỏi còn thiếu đã được tạo; không có assumption biến thành fact.
- Giải pháp khả thi qua skill/API/capability đã chứng minh; phân biệt `UNKNOWN`, `NOT_SUPPORTED`, external code và delivery-tooling gap.
- Thiết kế dữ liệu sơ bộ có source of truth, business key, normalization, cardinality, lifecycle, concurrency, quyền, audit và migration.
- State machine không có đường tắt; có cancel/reject/reopen/failure path.
- Dependency, limitation, acceptance và impact cấu hình cũ đủ rõ để lập plan.

### Checklist data design

- Object/field/relation có source of truth, business key, cardinality/optionality, ownership, volume/retention và `REQ-ID`.
- Pattern SAP/Odoo/Salesforce/Zoho được đối chiếu bằng nguồn chính thức và không sao chép mù quáng.
- Normalization, duplicate, data quality/migration, concurrency, permission/audit và impact hiện trạng đã xử lý.
- Mọi lifecycle có transition matrix; actor/precondition/validation/failure/audit đầy đủ.
- Markdown↔workbook nhất quán về Object, record-name, field type/slug, lookup, required/default, option và state type trong phạm vi workbook-scope. Không yêu cầu thêm lại field OMIT_EXISTING/OMIT_SYSTEM vào Excel duyệt; kiểm tra Notes giải thích nghiệp vụ + REQ-ID và HTML bao phủ Object/quan hệ đầy đủ.

### Findings và verdict

Mỗi finding có `ISSUE-ID`, severity `CRITICAL/HIGH/MEDIUM/LOW`, evidence, affected ref và recommendation. Reviewer trả một verdict:

- `ACCEPTED`
- `ACCEPTED_WITH_NON_BLOCKING_FINDINGS`
- `RECHECK_REQUIRED`
- `NON_COMPLIANT`

Coordinator ghi disposition `ACCEPTED`, `REJECTED_WITH_REASON`, `DEFERRED` hoặc `NEEDS_USER_DECISION`. Trong file giải pháp khách hàng, giữ findings bằng danh sách để không tạo bảng thứ ba ngoài hai bảng contract. Không xóa/hạ severity issue đã sửa. `DEFERRED` chỉ hợp lệ khi người dùng xác nhận out-of-scope, owner và target phase/revision.

Khi `Reviewer mode: ON`, không mở gate nếu reviewer chưa chạy, identity `FAIL`, verdict `RECHECK_REQUIRED/NON_COMPLIANT`, còn `OPEN CRITICAL/HIGH`, issue ảnh hưởng recommendation/schema/state/acceptance hoặc `NEEDS_USER_DECISION` chặn gate. Khi `OFF`, các điều kiện riêng của reviewer không áp dụng; blocker do coordinator self-check hoặc validator phát hiện vẫn phải được xử lý.

## Approval gates

### Gate Credential

- Áp dụng ngay khi có Workspace đích; API key là đầu vào bắt buộc.
- Resolve credential qua secret field, scoped environment, secret manager, credential broker hoặc kênh bí mật tương đương của runtime.
- Chỉ đạt `VERIFIED` khi `/bapi/v1/auth-token` thành công, session còn hiệu lực, response khớp đúng Workspace và App/Object discovery probes đều thành công.
- `MISSING`, `INVALID`, `WORKSPACE_MISMATCH`, `INSUFFICIENT_DISCOVERY_ACCESS` và `UNVERIFIED_TRANSIENT` đều chặn mọi wave. Không dùng browser session/key khác làm fallback.
- Gate này không cấp mutation authority và không thay thế kiểm tra Super Admin/quyền đặc thù trước apply.

### Gate Clarity

Không đi qua gate khi còn câu hỏi `BLOCKING` nhắm tới gate đó. Có thể tiếp tục discovery read-only hữu ích nhưng không thiết kế/mutate dựa trên assumption.

### Gate Solution

- Luôn yêu cầu validator `PASS`, coordinator self-check hoàn tất và không còn issue chặn. Chỉ yêu cầu reviewer đạt khi `Reviewer mode: ON`; khi `OFF`, reviewer status là `NOT_REQUESTED`.
- Revision cuối của `danh-sach-yeu-cau-va-giai-phap-so-bo-vN.md` phải bỏ Bảng 2, mọi requirement in-scope là `ĐÃ RÕ`, cột Q-ID là `N/A`.
- Yêu cầu người dùng xác nhận đúng filename/revision và giải pháp cuối; sau khi giao file phải kết thúc turn.
- Thay đổi requirement/solution sau approval làm baseline `STALE` và quay lại review/gate.

### Gate Data Model

- Áp dụng khi có create/extend Object/field/relation/state.
- Giao `data-design-vN.md`, `cogover-objects-vN.xlsx` và `data-design-vN.html` cùng revision sau validator và coordinator self-check đạt; người dùng có thể duyệt qua bản đọc nhưng xác nhận phải gắn với revision Markdown nguồn; chỉ yêu cầu reviewer đạt khi `Reviewer mode: ON`.
- Nếu không có thay đổi data model, yêu cầu xác nhận rõ `DATA_MODEL_NOT_APPLICABLE` cùng bằng chứng.
- Chỉ approval này mới cho phép bắt đầu lập Implementation Plan; không tự cấp quyền mutation hoặc apply.
- Schema/state thay đổi hoặc Workspace drift làm approval `STALE`.

### Gate Plan

- Chỉ mở sau Gate Data Model đã được người dùng xác nhận; plan phải tham chiếu đúng data model filename/revision hoặc quyết định `DATA_MODEL_NOT_APPLICABLE` đã duyệt.
- Chỉ mở sau validator/preflight `PASS`; không còn requirement chưa map, cycle, lock conflict, unresolved decision hoặc `READY` item không đầy đủ.
- Yêu cầu xác nhận đúng `implementation-plan-vN.md`, Workspace/environment và change set; sau khi giao phải kết thúc turn.
- Chỉ W-ID `READY` thuộc đúng revision được duyệt mới được chuyển sang `APPLY_APPROVED_PLAN`.

### Gate hẹp của skill con

Gate Solution/Data Model/Plan không thay thế confirmation tại thời điểm thao tác cho:

- Process flow theo `$process-creator`.
- Delete, delete/recreate và destructive cleanup theo ID cụ thể.
- Full replacement có thể loại bỏ cấu hình ngoài change set.
- Tạo API key tạm, đổi Department/Position, persona/quyền nhạy cảm.
- Publish/activate, gửi email/message thật, gọi hệ thống ngoài hoặc side effect nhạy cảm.

## Dependency và resource lock

### DAG mặc định

```text
Auth + read-only snapshot
  -> Objects không phụ thuộc
  -> Objects/fields/options/relations phụ thuộc
     -> Formula fixture -> runtime validation -> Formula -> read-back
     -> Filters và base layouts
     -> Transition/path/history/security
     -> Report Type -> saved report -> preview/reconciliation -> dashboard
     -> Process prerequisites -> process -> runtime test
     -> Child buttons -> group/chain -> final layout placement
  -> App/menu khi action target đã tồn tại; parent trước child
     -> NEW_APP: Overview dashboard/fallback PASS -> Home root group -> Overview child/default
     -> CUSTOMIZE_EXISTING_APP: preserve existing information architecture unless explicitly in scope
     -> root menu icon library discovery/reuse-or-create/upload -> icon mapping PASS -> menu icon install/read-back
  -> Integration/regression -> UAT -> handoff
```

Điều chỉnh theo dependency thật; không ép resource độc lập chờ nhau.

### Lock key

Dùng `<workspace>/<resource-type>/<id-or-slug>`, ví dụ `tenant-a/object/equipment` hoặc `tenant-a/app/{app-id}/menu-tree`.

Không chạy song song nếu:

- Lock trùng hoặc một lock bao cha lock khác.
- Cả hai update payload full-state/replacement.
- Task sau cần ID/output/postcondition task trước.
- Hai task chạm cùng option list, ACL, layout, dashboard grid, process definition hoặc menu tree.

Mọi full-state/replacement resource dùng single-writer, đọc state mới nhất, merge ngoài scope và read-back sau một mutation có chủ đích.

## Snapshot và mutation safety

### Snapshot contract

Trước sửa resource hiện có, tạo `snapshots/pre-apply-<timestamp>/manifest.md` gồm:

| W-ID | Resource type | ID/slug | Snapshot file | Captured at | SHA-256 | Redaction | Restore/containment note |
|---|---|---|---|---|---|---|---|

Lưu response/config đủ để diff và phục hồi thủ công, không lưu secret hoặc business records không cần thiết. Snapshot là read-only evidence, không phải lời hứa rollback tự động.

### Partial failure

- Khi mutation timeout, đọc lại theo ID/slug trước retry.
- Không auto-delete để rollback. Giữ resource đã tạo/sửa dở, ghi ID/state, chặn downstream và đề xuất containment.
- Chỉ rollback khi plan và skill nguồn chuẩn chứng minh an toàn; destructive rollback cần approval tương ứng.
- Cleanup chỉ áp dụng fixture/tài nguyên tạm do lần chạy tạo hoặc thay đổi; không cleanup record nghiệp vụ có sẵn.

### Evidence tối thiểu cho mỗi W-ID

- Snapshot/diff trước mutation đã redacted.
- Kết quả mutation không chứa secret.
- ID/slug resource thực tế.
- Read-back postcondition.
- Test result/observable side effect.
- Deviation, containment và fixture/tài nguyên tạm còn lại.
