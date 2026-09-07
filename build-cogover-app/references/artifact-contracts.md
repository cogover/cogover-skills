# Artifact Contracts

## Mục lục

1. [Quy tắc chung](#quy-tắc-chung)
2. [Danh sách yêu cầu và giải pháp](#danh-sach-yeu-cau-va-giai-phap-so-bo-vnmd)
3. [Data design](#data-design-vnmd)
4. [Cogover Objects workbook](#cogover-objects-vnxlsx)
5. [Automation feasibility](#automation-feasibility-vnmd)
6. [Implementation plan](#implementation-plan-vnmd)
7. [Test handover](#test-handover-vnmd)

## Quy tắc chung

- Dùng revision tăng dần `v1`, `v2`, ... cho mỗi baseline được bàn giao.
- Ghi `DRAFT`, `PENDING_USER_CONFIRMATION`, `APPROVED`, `STALE` hoặc `SUPERSEDED`.
- Ghi nguồn bằng `REQ-ID`, trang/section/sheet, Workspace resource ID/slug và timestamp khi có.
- Không ghi API key, session, cookie, secret, dữ liệu nhạy cảm không cần thiết hoặc raw response chưa redacted.
- Dùng ID ổn định: `REQ`, `Q`, `DEC`, `OBJ`, `REL`, `FLD`, `TR`, `MIG`, `ISSUE`, `AUT`, `GAP`, `W`, `T`.
- Không để một cell trống gây mơ hồ; dùng `N/A`, `TBD`, `UNKNOWN` hoặc lý do cụ thể.
- Các heading và tên cột trong code block dưới đây chỉ quy định cấu trúc. Dịch mọi nhãn human-readable sang `Artifact language`; giữ nguyên filename contract, stable ID, slug, API/skill name, code và enum/status kỹ thuật.
- Giữ nguyên comment `<!-- cogover-table:<table-id> -->` ngay trước bảng tương ứng. Đây là marker machine-readable để validator định vị bảng dù heading/tên cột đã dịch; không đổi table ID hoặc thứ tự cột contract.
- Mọi solution artifact có Workspace đích phải chứa đúng marker `<!-- cogover-api-key-preflight:VERIFIED -->`. Không tạo solution artifact khi credential chưa đạt Gate Credential.
- Ghi `Reviewer mode: OFF/ON` trong solution và data-design artifact. Mặc định `OFF`; chỉ dùng `ON` khi có yêu cầu rõ “bật các reviewer” hoặc diễn đạt tương đương từ người dùng. Khi `OFF`, dùng `NOT_REQUESTED`/`NOT_APPLICABLE` cho reviewer task, identity và verdict; validator và coordinator self-check vẫn bắt buộc.
- Chạy `scripts/validate_artifacts.py` trước mỗi Gate Solution, Gate Data Model và Gate Plan; ghi validator version/result vào artifact. Validator kiểm tra cấu trúc/cross-reference, không thay thế đánh giá correctness nghiệp vụ.

## `danh-sach-yeu-cau-va-giai-phap-so-bo-vN.md`

```markdown
# Danh sách yêu cầu và giải pháp sơ bộ

<!-- cogover-api-key-preflight:VERIFIED -->

## Metadata
- Artifact language:
- Workspace URL/domain/identifier:
- Environment: sandbox/UAT/production
- Work types: NEW_APP/CUSTOMIZE_EXISTING_APP or both
- Execution mode: DISCOVERY_ONLY/DESIGN_ONLY
- Requirement sources and versions:
- Workspace snapshot time:
- Scope and exclusions:
- Credential preflight: VERIFIED
- Credential verified at:
- Verified Workspace domain/ID:
- Discovery access probes: PASS
- Super Admin status: SUPER_ADMIN_VERIFIED/SUPER_ADMIN_UNVERIFIED
- Reviewer mode: OFF/ON
- Reviewer activation evidence: NOT_REQUESTED, hoặc yêu cầu thực tế của người dùng khi ON
- Validator version/result:
- Revision/status:

## Bảng 1 — Danh sách yêu cầu và giải pháp sơ bộ/cuối cùng
<!-- cogover-table:requirements-solutions -->
| Mã yêu cầu | Mô tả yêu cầu | Trạng thái làm rõ | Mã câu hỏi cần trả lời | Giải pháp sơ bộ/cuối cùng |
|---|---|---|---|---|

## Bảng 2 — Danh sách câu hỏi
<!-- cogover-table:questions -->
| Mã câu hỏi | Mã yêu cầu | Nội dung câu hỏi | Nội dung trả lời |
|---|---|---|---|

## Nguồn bằng chứng và hiện trạng liên quan
- REQ-...: requirement provenance; Workspace App/Object/config ID/slug + snapshot time; Cogover catalog/skill evidence.

## QA findings and resolution
- `ISSUE-ID` — nguồn phát hiện (reviewer task ID khi ON hoặc coordinator self-check khi OFF); severity; REQ/decision affected; finding/evidence gap; resolution; disposition; issue status; deferral decision/owner/target phase or revision.

## Solution quality assurance
- Artifact author/coordinator task ID:
- Reviewer mode: OFF/ON
- Independent solution reviewer task ID: task ID khi ON; NOT_REQUESTED khi OFF
- Identity separation check: PASS/FAIL khi ON; NOT_APPLICABLE khi OFF
- Automated validator/version/result:
- Reviewed revision/evidence baseline:
- QA verdict: ACCEPTED/ACCEPTED_WITH_NON_BLOCKING_FINDINGS/RECHECK_REQUIRED/NON_COMPLIANT khi ON; NOT_REQUESTED khi OFF
- Remaining blocking issues:

## Solution approval
- Revision:
- Status: DRAFT while questions remain; PENDING_USER_CONFIRMATION only on the final revision
- Confirmation evidence: empty until user confirms
```

### Quy tắc hai bảng

- Dòng Bảng 1 phải bắt đầu bằng `REQ-ID`. Cột giải pháp phải chứa disposition, mapping Cogover, delta, dependency/limitation, acceptance và evidence đủ truy nguyên; không được để trống.
- File dành cho khách hàng chỉ dùng hai bảng contract ở trên; trình bày QA findings bằng danh sách, không tạo bảng thứ ba.
- Cột trạng thái chỉ dùng `CẦN LÀM RÕ`, `ĐÃ RÕ`, `OUT_OF_SCOPE` hoặc `UNKNOWN`. Mọi `Q-ID` trong cột câu hỏi phải có đúng một dòng ở Bảng 2.
- Mỗi dòng Bảng 2 bắt đầu bằng `Q-ID`, tham chiếu một hoặc nhiều `REQ-ID` đã định nghĩa và không để trống nội dung câu hỏi. Mapping Q↔REQ trong hai bảng phải khớp chính xác. Dùng `TBD` cho câu chưa trả lời.
- Mỗi vòng trả lời của người dùng tạo một revision mới; không sửa đè file đã giao.
- Revision cuối phải có mọi requirement in-scope ở trạng thái `ĐÃ RÕ`, cột câu hỏi là `N/A`, dùng “giải pháp cuối cùng” và **bỏ hoàn toàn marker/heading/Bảng 2**. Chỉ yêu cầu reviewer verdict đạt khi `Reviewer mode: ON`; khi `OFF`, ghi `NOT_REQUESTED`.
- Không dùng một score duy nhất để che gap. Nếu có score, công khai trọng số và giữ bằng chứng ở cấp requirement.

Severity dùng `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`; Disposition dùng `ACCEPTED`, `REJECTED_WITH_REASON`, `DEFERRED`, `NEEDS_USER_DECISION`; Issue status dùng `OPEN`, `RESOLVED`, `OUT_OF_SCOPE_CONFIRMED`. Không xóa hoặc hạ severity issue đã sửa. `DEFERRED` chỉ hợp lệ khi có quyết định out-of-scope của người dùng, owner và target phase/revision. Gate luôn yêu cầu validator `PASS`, không còn issue chặn và không có deferral không hợp lệ; chỉ yêu cầu independent reviewer verdict đạt khi `Reviewer mode: ON`.

## `data-design-vN.md`

```markdown
# Data Design

## Metadata and approved inputs
- Artifact language:
- Workspace/environment:
- Requirement sources and versions:
- Requirement baseline:
- Approved solution-list filename/revision and reviewer verdict, hoặc NOT_REQUESTED khi Reviewer mode OFF:
- User-approval evidence for the final solution revision:
- Workspace snapshot time:
- Evidence sources:
- Reviewer mode: OFF/ON
- Reviewer activation evidence: NOT_REQUESTED, hoặc yêu cầu thực tế của người dùng khi ON
- Validator version/result:
- Revision/status:

## Design principles and decisions
| DEC-ID | Decision | Reason | REQ-ID | Alternatives rejected | Evidence |

## External pattern benchmark
| Business pattern | Official system/source | Observed pattern | Adopted principle | Rejected/modified aspect |

Với mỗi pattern dữ liệu doanh nghiệp liên quan, thêm dòng cho tài liệu chính thức của SAP, Odoo, Salesforce và Zoho. Dùng `N/A` kèm lý do khi một hệ thống không có pattern tương ứng; không dùng nguồn marketing/third-party thay tài liệu chính thức khi kết luận cấu trúc dữ liệu.

## Object catalog
<!-- cogover-table:object-catalog -->
| OBJ-ID | Object name | Object slug | REUSE/EXTEND/CREATE | Master/transaction/junction/config/log | Purpose/source of truth | Business key/record name | Owner | Volume/retention | REQ-ID | Workspace evidence |
|---|---|---|---|---|---|---|---|---|---|---|

## Relationships
<!-- cogover-table:relationships -->
| REL-ID | Source | Target | Cardinality/optionality | Cogover mapping | Required | Child lifecycle/delete assumption | REQ-ID | Evidence |
|---|---|---|---|---|---|---|---|---|

## Fields
<!-- cogover-table:fields -->
| FLD-ID | Object | Field name | Field slug | Type | Multiple/min/max | Required/default | Translations | Unique/options/lookup | Editable by | Sensitive/history | REQ-ID | Rationale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## State machines
### <Object name/slug>
- State field:
- Initial state:
- Terminal states:
- Cancel/reject policy:
- Reopen/undo policy:
- Invalid transitions:

<!-- cogover-table:state-transitions -->
| TR-ID | From | To | Actor | Trigger | Preconditions | Validation | Before/after action | Failure/retry | Audit | REQ-ID |
|---|---|---|---|---|---|---|---|---|---|---|

## Data quality, migration and retention
| MIG-ID | Source | Target | Transform/default | Duplicate strategy | Validation/reconciliation | Failure handling | Owner |

## Security and audit model
| Object/field | Owner | Create | Read | Edit | Delete | Transition | History/retention | REQ-ID |

## Impact on current configuration
| Resource ID/slug | Dependency | Impact | Required follow-up | Risk |

## QA findings and resolution
<!-- cogover-table:data-design-findings -->
| ISSUE-ID | Raised by agent/task ID | Severity | Finding | Resolution | Disposition | Issue status | QA verdict | Affected refs | Deferral decision/owner/target phase or revision |
|---|---|---|---|---|---|---|---|---|---|

## Data-design quality assurance
- Artifact author/coordinator task ID:
- Reviewer mode: OFF/ON
- Independent data-design reviewer task ID: task ID khi ON; NOT_REQUESTED khi OFF
- Identity separation check: PASS/FAIL khi ON; NOT_APPLICABLE khi OFF
- Automated validator/version/result:
- Reviewed Markdown/workbook revisions and evidence baseline:
- QA verdict: ACCEPTED/ACCEPTED_WITH_NON_BLOCKING_FINDINGS/RECHECK_REQUIRED/NON_COMPLIANT khi ON; NOT_REQUESTED khi OFF
- Remaining blocking issues:

Severity, Disposition và Issue status dùng cùng enum/rule của solution ledger. Gate rule: validator `PASS`, coordinator self-check hoàn tất, không còn issue `OPEN` `CRITICAL`/`HIGH`, issue ảnh hưởng schema/acceptance, `NEEDS_USER_DECISION` hoặc deferral không hợp lệ. Chỉ yêu cầu independent reviewer status đạt khi `Reviewer mode: ON`; khi `OFF`, ghi `NOT_REQUESTED`. Không xóa hoặc hạ severity issue đã sửa.

## Markdown-to-Excel consistency
| Check | Result | Notes |

Required checks: Object name/plural/record-name/disposition; field name/slug/type semantic mapping/multiple/min/max/required/default/translations; options/state type; lookup target and dependency order.

## Approval
- Revision:
- Status: PENDING_USER_CONFIRMATION
- Workbook filename/revision:
- Workbook SHA-256:
- Workbook generator/version if known:
- Validator version/result:
- Confirmation evidence: empty until user confirms
```

Mỗi Object có status/lifecycle phải có transition matrix. Không chỉ liệt kê options.

## `cogover-objects-vN.xlsx`

Tạo bằng `$create-cogover-objects` và tuân thủ template của skill đó. Workbook là thiết kế/import specification, không phải bằng chứng schema đã được tạo trên Workspace.

Dùng `Artifact language` của `data-design-vN.md` cho display label, plural label, description và translation phù hợp; giữ Object/Field slug, type, enum kỹ thuật và giá trị contract không đổi. Nếu cần workbook song ngữ, ghi rõ ngôn ngữ chính và mapping translation trước khi tạo.

Đối chiếu với `data-design-vN.md`:

- Object name, plural name, record-name field và disposition.
- Field name/slug/type, multiple, required/default và translations.
- Lookup target và thứ tự dependency.
- Options cùng state type.
- Notes cho `REUSE`, `EXTEND`, `CREATE`, limitation và field hệ thống bị loại.

Nếu workbook không biểu diễn đủ một delta của Object hiện có, giữ Markdown làm nguồn quyết định và ghi giới hạn workbook rõ ràng; không biến sheet partial thành lệnh tạo lại Object.

Không thêm cover/metadata sheet nếu contract import chỉ cho phép mỗi sheet là một Object. Ghi filename, revision, hash, generator skill version nếu biết và consistency result trong phần Approval/consistency của `data-design-vN.md`.

## `automation-feasibility-vN.md`

```markdown
# Automation Feasibility

## Metadata
- Artifact language:
- Workspace/environment:
- Requirement sources and versions:
- Workspace snapshot time:
- Revision/status:
- Evidence sources:

## Approved baseline
- Data design revision and approval evidence:
- Workspace snapshot/drift check:

## Automation register
<!-- cogover-table:automation-register -->
| AUT-ID | REQ-ID | Trigger | Preliminary flow | Primary Cogover mechanism | Required nodes/resources | Support status | Evidence | Constraint | Alternative | Test oracle |
|---|---|---|---|---|---|---|---|---|---|---|

## Flow detail
### AUT-...
- Workflow type:
- Actor and permission:
- Inputs/outputs:
- Happy path:
- Gateway/branches:
- Exception/timeout/retry:
- Idempotency/concurrency:
- Side effects:
- Test data and observable result:

## Schema changes discovered
| Finding | Affected OBJ/FLD/TR | Requires return to Data Model Gate? | Decision |
```

Support status chỉ dùng:

- `SUPPORTED_NATIVE`
- `SUPPORTED_WITH_CONSTRAINTS`
- `PARTIAL_EXTERNAL_COMPONENT`
- `NOT_SUPPORTED`
- `UNKNOWN_NEEDS_VALIDATION`

## `implementation-plan-vN.md`

```markdown
# Implementation Plan

<!-- cogover-data-model-gate:APPROVED -->

## Metadata and approved baselines
- Artifact language:
- Workspace/environment:
- Requirement sources and versions:
- Workspace snapshot time:
- Evidence sources:
- Approved solution-list filename/revision and reviewer verdict, hoặc NOT_REQUESTED khi Reviewer mode OFF:
- User-approval evidence for the final solution revision:
- Data Model Gate status: APPROVED/DATA_MODEL_NOT_APPLICABLE
- Approved data-design filename/revision and user-approval evidence, or approved N/A evidence:
- Automation feasibility revision:
- Workspace snapshot/drift status:
- Validator version/result:
- Coordinator preflight result:
- Plan revision/status:

## Requirement traceability
<!-- cogover-table:requirement-traceability -->
| REQ-ID | Design refs | AUT refs | Work items | Test cases | Coverage status | Gap/defer reason |
|---|---|---|---|---|---|---|

## Work breakdown
<!-- cogover-table:work-breakdown -->
| W-ID | Status | REQ-ID | Design/AUT refs | Resource + current→target delta | Action | Skill | Depends on | Parallel group | Lock key | Acceptance criterion | Postcondition/read-back | Test | Risk/rollback |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Dependency DAG
<Mermaid diagram derived from the actual work items>

## Execution waves
| Wave | Work items | Why parallel/sequential | Entry criteria | Exit criteria |

## Resource lock register
<!-- cogover-table:lock-register -->
| Lock key | Work items | Single writer | Required order | Replacement semantics? |
|---|---|---|---|---|

## Test and UAT plan
<!-- cogover-table:test-plan -->
| T-ID | REQ-ID | Scenario/persona | Preconditions | Steps | Expected result | Evidence to retain |
|---|---|---|---|---|---|---|

## Unsupported, unknown and external capabilities
| GAP-ID | REQ-ID | Status | Needed behavior | Layer checked/evidence | Exact reason | Business impact | Workaround | Decision owner |

## Rollout, containment and rollback
- Change window:
- Feature activation order:
- Backup/snapshot evidence:
- Containment for partial failure:
- Rollback constraints:

## Handoff
- Admin/operator guide needed:
- Training/data migration:
- Open decisions:

## Automated validation and coordinator preflight
- Validator command/version:
- Validator result: PASS/FAIL
- Validated baseline revisions:
- Traceability check: PASS/FAIL
- DAG/dependency check: PASS/FAIL
- Parallel lock check: PASS/FAIL
- READY completeness check: PASS/FAIL
- Side-effect and child-gate check: PASS/FAIL
- Coordinator task ID:
- Coordinator preflight result: PASS/FAIL
- Remaining blocking issues:

## Approval
- Revision:
- Status: PENDING_USER_CONFIRMATION
- Confirmation evidence: empty until user confirms
```

Marker của plan chỉ dùng một trong hai giá trị:

- `<!-- cogover-data-model-gate:APPROVED -->` khi data design/workbook đã được người dùng xác nhận.
- `<!-- cogover-data-model-gate:DATA_MODEL_NOT_APPLICABLE -->` khi người dùng đã xác nhận data model không áp dụng.

Không tạo hoặc phát hành plan trước Gate Data Model. Marker phải khớp metadata và bằng chứng approval thực tế; không tự ghi approval giả.

Implementation Plan do coordinator preflight và validator kiểm tra. Không mở Gate Plan khi validator hoặc coordinator preflight chưa `PASS`, còn `NEEDS_USER_DECISION`, deferral không hợp lệ, requirement chưa mapping hoặc W-ID chưa đủ điều kiện `READY`.

### Work item rules

- Mỗi `REQ-ID` in-scope phải xuất hiện trong traceability.
- Mỗi `W-ID` phải có ít nhất một `REQ-ID`; không tạo work item “nice to have” ngoài scope.
- Dùng `DRAFT`, `BLOCKED`, `READY`, `IN_PROGRESS`, `DONE`, `FAILED` cho Status. Gate Plan chỉ cho apply `READY`; plan mới phát hành thường chỉ dùng `DRAFT`, `BLOCKED` hoặc `READY`.
- `Depends on` dùng ID, không dùng mô tả mơ hồ.
- `Parallel group` chỉ được gán sau khi kiểm tra lock và dependency.
- `Postcondition` phải là state có thể đọc lại hoặc hành vi có thể quan sát.
- `Rollback` không được mặc định là delete; nêu rõ khi chỉ có containment/manual recovery.
- Tách hoặc liệt kê rõ mọi side effect ngầm của skill con: layout mặc định, icon upload, activation/publish, runtime fixture, quyền/persona/schedule tạm và cleanup. Không để chúng ẩn trong một W-ID chung không có lock/postcondition.
- Với Formula, plan phải thể hiện `base fields → marked fixture hoặc approved existing record → syntax/runtime validation → Formula mutation → read-back`; chỉ tạo cleanup W-ID cho fixture do lần chạy tạo/thay đổi và không cleanup business record có sẵn.

## `test-handover-vN.md`

```markdown
# Test and Handover

## Metadata
- Artifact language:
- Workspace/environment:
- Requirement sources and versions:
- Workspace snapshot time/final snapshot time:
- Artifact revision/status:
- Evidence sources:

## Deployment baseline
| Plan revision | Workspace | Execution window | Final state snapshot |

## Work item results
<!-- cogover-table:work-item-results -->
| W-ID | Planned action | Actual resource ID/slug | Result | Read-back evidence | Deviation |
|---|---|---|---|---|---|

## Requirement test results
<!-- cogover-table:requirement-test-results -->
| T-ID | REQ-ID | Persona/scenario | Expected | Actual | PASS/PARTIAL/FAIL_CONFIG/FAIL_SKILL/FAIL_RUNTIME/BLOCKED_ENV | Evidence |
|---|---|---|---|---|---|---|

## Traceability closure
| REQ-ID | Design | Work items | Tests | Final coverage |

## Cleanup and restoration
| Fixture/key/permission/schedule/relation | ID/marker | Cleanup expected | Actual state | Evidence |

## Limitations and residual risks
| GAP-ID | Status | Impact | Workaround/owner | Next action |

## Handoff checklist
- Admin links/resources:
- Data migration reconciliation:
- UAT sign-off:
- Training/operations notes:
- Outstanding IDs or temporary resources:
```
