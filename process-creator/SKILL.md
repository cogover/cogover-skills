---
name: process-creator
description: "Thiết kế, tạo, kích hoạt và xác minh end-to-end Cogover Process qua `/bapi/v1/processes` (Manual, Normal, Scheduled, Triggered record/webhook, Sequence): BPMN XML, User Task, gateway, loop, action gồm AI Agent, Variable/Formula/Text Template, quyền; phối hợp $object-info, $object-record, $cogover-api-auth. Dùng khi tạo, sửa, kiểm thử hoặc đánh giá workflow/process."
metadata:
  author: cogover
  version: "1.2.4"
---

# Cogover Process Creator

- **Phiên bản:** `1.2.4`
- **Ngày phát hành:** `2026-09-11`

Trước khi dùng JSON mẫu, đọc [quy ước fixture và giới hạn kiểm thử](samples/README.md). Resolve ID và tài nguyên của Workspace đích; không coi snapshot response hoặc metadata kiểm tra cũ là kết quả validation cho lần triển khai mới.

## Quy tắc an toàn

- Xoá quy trình (DELETE): PHẢI hỏi xác nhận người dùng trước khi gọi API xoá; không bao giờ tự ý xoá khi chưa có đồng ý rõ ràng. Xoá record test: theo quy tắc xác nhận xoá của `$object-record`.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Skill này dùng nhóm `/bapi/v1/processes` (API Key Bearer) theo contract [api-process-builder.md](api-process-builder.md); riêng tạo lượt chạy Sequence Flow gọi `/api/v1/run-workflow-server` bằng phiên Web App đổi từ API Key qua `POST /bapi/v1/auth-token` (mục 4.6). `WORKSPACE_DOMAIN` của khách hàng là base URL cho mọi API call và link kết quả. Workspace kiểm thử dùng chứng chỉ self-signed: chỉ bỏ qua kiểm tra TLS (`curl -k`/`--insecure`, `NODE_TLS_REJECT_UNAUTHORIZED=0`) khi người dùng xác nhận đó là môi trường nội bộ; không dùng cho Workspace production.
- Thông tin Object thật: BẮT BUỘC lấy qua `$object-info` trước khi dựng JSON (trả về objectTypeId, slug, name và fields gồm field slug, name, fieldType, fieldMetaData, options). `objectTypeId`, object slug/name, field slug, `fieldType`, field options trong tài liệu này và samples (ví dụ `OT00000000011` Lead, `OT00000000007` Contact) chỉ là minh hoạ, thay đổi theo từng Workspace; không sao chép để dùng trực tiếp. Nơi cần: field `lookup_normal` (`object`, `object_slug` đối tượng đích); `CREATE_RECORD`/`UPDATE_RECORD` (`objectTypeId`, `objectTypeSlug`, field slug + `fieldType` + `fieldMetaData`); `GET_RECORD` (`objectTypeId`, `objectTypeSlug`); hiển thị bản ghi trong User Task; Triggered record (`metadata.object`; loại webhook không cần `object`); Sequence (`metadata.objectTypeId`, `objectTypeSlug`); điều kiện kiểu RECORD (`leftObjectTypeId`); Variable RECORD, Loop `variableMetadata`, Organization (theo `filterType`) và output resources của GET_RECORD/CREATE_RECORD/Organization (`metaDataType.object`, `metaDataType.objectSlug`).
- Bản ghi test và dữ liệu nghiệp vụ: `$object-record`. Document template cho Export Record: `$document-template`. Quyền/vị trí/phòng ban tạm khi kiểm thử: `$user-permission`.
- Tài liệu trong skill đọc theo việc cần làm: bảng ở mục [File tham khảo](#file-tham-khảo).

## Các loại quy trình

Chọn theo cách quy trình được kích hoạt:

| Câu hỏi | Loại quy trình |
|---|---|
| Người dùng cần điền form để khởi tạo? | `manual_flow` |
| Process cha gọi qua Sub Process hoặc module khác gọi, không cần Root form? | `normal_flow` (cách dùng phổ biến) |
| Người dùng chạy process trực tiếp, không cần Root form? | `normal_flow` (vẫn hỗ trợ, ít dùng độc lập) |
| Chạy định kỳ theo lịch? | `scheduled_flow` |
| Chạy khi bản ghi được tạo/cập nhật/xoá? | `triggered_flow`, `metadata.type: "record"` |
| Chạy khi nhận HTTP POST từ bên ngoài? | `triggered_flow`, `metadata.type: "webhook"` |
| Người dùng liên kết (connect) bản ghi với quy trình? | `sequence_flow` |

| `type` | Start `renderKey` | `metadata` | `permissions` | `processInstanceAccessControls[].functions` | System resources | Chi tiết, mẫu |
|---|---|---|---|---|---|---|
| `manual_flow` | `START_MANUAL_EVENT` | `{}` | `["VIEW", "ADD", "EDIT", "DELETE", "START_INSTANCE"]` | `["START_INSTANCE"]` | chỉ `$client`, `$currentUser`, `$flow.instance` | `samples/sample_process_1.json` (3 node), `samples/sample_process_2.json` (4 node) |
| `normal_flow` | `START_NORMAL_EVENT` | `{}` | `VIEW`, `ADD`, `EDIT`, `DELETE`, `START_INSTANCE` và quyền participant người dùng chọn | gồm `START_INSTANCE` cho actor được phép chạy | base tiêu chuẩn | [nodes/normal-flow.md](nodes/normal-flow.md), `samples/sample_normal_flow.json` |
| `scheduled_flow` | `START_SCHEDULED_EVENT` | `scheduleRules` | `["VIEW", "ADD", "EDIT", "DELETE", "VIEW_INSTANCE_PROGRESS", "VIEW_INSTANCE_FULL", "CANCEL_INSTANCE", "DELETE_INSTANCE", "DO_EVERY_TASK_IN_SEQUENCE", "ASSIGN_TASK"]` | `["CANCEL_INSTANCE", "DELETE_INSTANCE", "VIEW_INSTANCE_PROGRESS", "VIEW_INSTANCE_FULL", "DO_EVERY_TASK_IN_SEQUENCE", "ASSIGN_TASK"]` | chỉ `$client`, `$currentUser`, `$flow.instance` | [nodes/scheduled-start-event.md](nodes/scheduled-start-event.md), `samples/sample_scheduled_flow_1.json` |
| `triggered_flow` | `START_TRIGGERED_EVENT` | cấu hình trigger `record` hoặc `webhook` | như `scheduled_flow` | như `scheduled_flow` | record: thêm `$flow.input.oldRecord`, `$flow.input.newRecord`; webhook: `$flow.input.*` theo `parseToDataType`, không có `oldRecord`/`newRecord` | [nodes/record-triggered-flow.md](nodes/record-triggered-flow.md), `samples/sample_triggered_flow.json`; [nodes/webhook-triggered-flow.md](nodes/webhook-triggered-flow.md), `samples/Webhook_triggered_flow.json` |
| `sequence_flow` | `START_SEQUENCE_EVENT` | `{"objectTypeId": "...", "objectTypeSlug": "..."}` từ `$object-info` | `["VIEW", "ADD", "EDIT", "DELETE", "CANCEL_INSTANCE", "CONNECT_SEQUENCE", "DO_EVERY_TASK_IN_SEQUENCE", "ASSIGN_TASK"]` | `["CONNECT_SEQUENCE", "CANCEL_INSTANCE", "DO_EVERY_TASK_IN_SEQUENCE", "ASSIGN_TASK"]` | thêm `$flow.input` (id `SEQUENCE_INPUT`) với child `$flow.input.record` (id `RECORD_DATA`, bản ghi được liên kết) và `$flow.instance.starter` | `samples/sample_sequence_flow.json` |

Khác biệt cốt lõi:

- **Manual:** User Task đầu tiên ngay sau Start là form người dùng submit để kích hoạt (Root, `isRoot: true`; ví dụ form "Đề nghị mua sắm", "Xin nghỉ phép"). Chỉ loại này bắt buộc Root; các loại khác không tự tạo Root và Start có thể nối thẳng tới action, gateway hoặc End Process.
- **Normal:** thường để process cha gọi qua node Sub Process hoặc module khác gọi (ví dụ module SLA phát hiện vi phạm rồi gọi Normal Flow tạo cảnh báo, gửi email, thông báo quản lý). Người có `START_INSTANCE` vẫn chủ động chạy được, nhưng không thiết kế quanh thao tác bấm chạy khi bên gọi dự kiến là process cha/module.
- **Scheduled:** `metadata.scheduleRules[]` gồm `triggerInterval` (`type` ∈ `SECONDS` | `MINUTES` | `HOURS` | `DAYS` | `WEEKS` | `MONTHS` | `YEARS` | `CRON` và field theo chu kỳ), `start`/`end` (timestamp ms hoặc `null`), `maxRun` (`0` không giới hạn), `maxRunTypeFE` (`UNLIMITED` hoặc `CUSTOM`, không `LIMITED`), `id` prefix `SR` + suffix chữ-số. Field bắt buộc của từng chu kỳ, mapping `daysOfWeek`, `daysOfMonth`/`nth`, `atDays`, `cronExpression` (Quartz, không `between`), payload front-end (`daysOfMonth` kèm `daysOfWeek: []`; không gửi `temporaryExecutionHours`/`temporaryExecutionMinutes`): [nodes/scheduled-start-event.md](nodes/scheduled-start-event.md).
- **Triggered record:** `metadata` gồm `type: "record"`, `trigger` (`1` tạo, `2` cập nhật, `3` tạo hoặc cập nhật, `4` xoá), `object`, `triggerConditions` (`1` khi `trigger` là `1`/`4`; `3` khi `2`/`3`), `onObjectFieldUpdateOption`, `triggeredUpdateFields`, `conditions` + `logicType` + `logic`, `applyConditionsForRecords: true`, `runFlowWhenRecordsAreUpdatedStrategy: 1`, `name: "Start"`. Phần tử `conditions` (`field`, `op`, `params`, `fieldType`) theo [danh mục điều kiện của object-record](../object-record/records_filter_conditions.md#dùng-trong-process-process-creator).
- **Triggered webhook:** chạy khi nhận HTTP POST tới URL webhook; body request parse thành `$flow.input.*` theo `parseToDataType`. `authType`/`authTypeAllVersions` ∈ `bearer` | `apiKey` | `basic`; Bearer/API Key đặt `isAutoGenerate: true` để server sinh secret, `false` thì truyền secret người dùng cung cấp (bộ `*AllVersions` tương tự); Basic bắt buộc `basicUsername`/`basicPassword` (`basicUsernameAllVersions`/`basicPasswordAllVersions`). `url`/`urlAllVersions`, webhook ID và secret do server sinh: không sao chép URL/secret từ response hoặc sample sang create payload. Response body bằng Text Template dùng `documentSampleSlug: {"type": 2, "value": "$flow..."}`, không `documentSampleId`.
- **Sequence:** người dùng chủ động chọn bản ghi (ví dụ một Lead) để liên kết với quy trình. `participantPermission`: `ANY_PERFORMER_CAN_VIEW_PROGRESS_OF_SEQUENCE: true`, `ANY_PERFORMER_CAN_REASSIGN_TASK: true`.

## Hướng dẫn

### Bước 1: Thu thập thông tin và xác nhận luồng

KHÔNG dựng JSON ngay. Hỏi và chốt:

1. Tên quy trình; slug (tự sinh từ tên theo quy tắc slug ở Bước 2 nếu không cung cấp, ví dụ `quy_trinh_xin_nghi_phep`).
2. Loại quy trình theo bảng trên. Scheduled: chu kỳ trong 8 loại, field theo chu kỳ, thời gian hiệu lực, `UNLIMITED` hay `CUSTOM`. Triggered webhook: xác thực cho version hiện tại và tất cả version (`bearer`/`apiKey`/`basic`), auto-generate secret hay nhập tay, response timing/body/status, input sample/schema.
3. Danh sách node theo thứ tự từ Bắt đầu đến Kết thúc. Chỉ Manual Flow bắt buộc node đầu tiên sau Start là Root (`isRoot: true`); Normal/Scheduled/Triggered/Sequence có thể nối Start trực tiếp tới action, gateway hoặc End Process. Phân biệt End Branch (chỉ kết thúc nhánh hiện tại) và End Process (kết thúc toàn process) ở từng nhánh.
4. Thông tin theo node/resource có dùng:

| Node/resource | Cần hỏi |
|---|---|
| Gateway | Loại (Exclusive, Parallel, Inclusive), các nhánh và điều kiện mỗi nhánh |
| Loop | Danh sách duyệt (ví dụ trường lookup nhiều giá trị trong User Task trước), hướng duyệt (`1` từ bản ghi đầu đến cuối, `2` từ cuối đến đầu), các task trong nhánh "For each item" |
| Variable | Tên, slug; kiểu `TEXT`/`NUMBER`/`BOOLEAN`/`DATE`/`DATE_TIME`/`RECORD`; `isList`; giá trị mặc định (tĩnh hoặc tham chiếu như `$userTask.Root.so_a`); `availableForInput` (nhập khi bắt đầu quy trình); `availableForOutput`; RECORD: object type slug và ID |
| Assignment | Tên, slug; từng phép gán: biến đích, giá trị nguồn, toán tử `=`, `+=`, `-=`, `count` |
| Organization | Tên, slug; `filterType` `manager`/`personnel`/`department`/`position`; nhân sự đầu vào (biến như `$userTask.Root.submittedBy` hoặc ID cụ thể); với `manager`: phép so sánh cấp bậc `gte`/`equals` và giá trị; trường cần lưu (ví dụ `account_email`) và biến đích; lưu giá trị đầu tiên `FIELD_OF_FIRST_RECORD` hay tất cả `FIELD_OF_LIST_RECORDS` |
| Wait | Event: sau một khoảng thời gian hoặc email open/reply/link click; đọc [nodes/wait-task.md](nodes/wait-task.md) trước khi đề xuất event khác vì backend hiện tại không thực thi mọi lựa chọn trên UI. Time event: khoảng thời gian và đơn vị `seconds`/`minutes`/`hours`/`days`; timer runtime bắt buộc nhóm `maximumWaitTimeValue` + `maximumWaitTimeUnit`. Email event: Send Email Task nguồn và maximum wait theo khoảng thời gian |
| Sub Process | Process Info ID (`PI...`) và Process ID `subWorkflowId` (`PE...`) của quy trình con: hai ID độc lập, BẮT BUỘC là ID thật đã tồn tại, không tự sinh hay suy ra từ nhau, hỏi người dùng cung cấp cả hai; loại quy trình con (`manual_flow`/`normal_flow`/`sequence_flow`/`triggered_flow`/`scheduled_flow`, quyết định field bắt buộc); biến input (tên ở quy trình con, kiểu, giá trị từ cha); biến output (tên ở con, biến cha nhận); `async` false/true |
| Formula | Tên, slug; kiểu trả về `TEXT`/`NUMBER`/`BOOLEAN`/`DATE`/`DATE_TIME`; nội dung code Cogover Scripting; resource/biến được tham chiếu; nơi dùng (body Send HTTP Request, giá trị Assignment...) |
| To Do | Chỉ Sequence Flow: assignee, title/content, priority, due date, reminder, maximum wait time |
| Phone Call | Hotline, số nhận, recording/TTS; automatic/manual nếu là Sequence Flow |
| Export Record | Object, record ID, document template thật: list/detail hoặc tạo qua `$document-template` rồi lấy ID đã verify; không đoán ID, không dùng Object Type ID làm `templateId` |
| Push Message | Push type, recipient type và các field theo mode |
| Omni Message | Recipient, các Zalo/WhatsApp method theo thứ tự, timeout, success criteria |
| AI Agent | Đọc [nodes/ai-agent-task.md](nodes/ai-agent-task.md); agent đang hoạt động trong Workspace, instruction và nguồn ngữ cảnh, phiên mới/nối tiếp, cấu trúc kết quả, danh tính chạy, chính sách tool, timeout, số vòng tối đa, nhánh xử lý lỗi. Kiểm tra phiên bản Process API/editor hỗ trợ node trước khi lưu; không tự suy ra agent ID hoặc bật `AUTO_APPROVE` khi chưa nằm trong phạm vi người dùng yêu cầu |
| Respond to Webhook, JSON to Object | Báo node chưa có runtime action trên backend hiện tại; chỉ thu thập schema khi người dùng đang migrate/đọc payload cũ, không tạo executable flow |

5. Trình bày lại luồng chi tiết (loại, tên, các bước/node, gateway, loop, variable, action...) và hỏi: "Luồng quy trình trên đã đúng chưa? Bạn muốn điều chỉnh gì không?". CHỈ khi người dùng đồng ý mới sang Bước 2; muốn sửa thì điều chỉnh và hỏi xác nhận lần nữa.

### Bước 2: Dựng cấu trúc

#### Quy tắc slug (bắt buộc)

- Mọi `slug` người dùng có thể chỉnh trên front-end do skill tạo (process, User Task, action, gateway, loop, variable/formula/text template/resource, field/component, layout node) dài ít nhất 2 ký tự và khớp `^[A-Za-z](?!.*__)[A-Za-z0-9_]*[^_]$`: bắt đầu bằng chữ cái, chỉ chữ Latin/chữ số/`_`, không có `__`, không kết thúc bằng `_`. Tên hiển thị vẫn có thể chứa Unicode, khoảng trắng, dấu câu.
- Tự sinh từ tên: bỏ dấu tiếng Việt (`đ` → `d`), thay mỗi chuỗi ký tự không hợp lệ bằng `_`, gộp nhiều `_`, bỏ `_` đầu/cuối, thêm suffix số bằng `_` khi cần chống trùng. Không sinh kebab-case.
- Giữ nguyên reference do API/skill khác trả về (`objectTypeSlug`, field slug, provider/template ID); không sửa một reference thật để ép regex. Hệ thống ngoài trả giá trị không hợp lệ cho trường `slug` do process sở hữu: dừng và báo lỗi.
- Trước POST, duyệt mọi slug thuộc entity người dùng chỉnh được và bắt chúng khớp regex. Không áp regex cho slug hệ thống cố định: decision outcome mặc định `_default`, `optionConfig.slug` khi schema cho phép rỗng, `validateMessage.slug` server-owned; không gửi `validateMessage` trong create request.

#### Quy tắc ID

- Prefix theo entity: `PE` process, `NO` node, `FL` flow, `NC` node config, `RS` resource, `PI` process info, `DO` decision outcome, `DOC` condition, `SC` screen. Suffix là chuỗi chữ-số ngẫu nhiên đủ entropy, duy nhất trong payload; không mô tả suffix chỉ gồm chữ số hay bắt buộc một độ dài cố định (ID canonical hiện có là alphanumeric, độ dài do server/library quyết định).
- Create payload: action do front-end tạo dùng cùng ID với BPMN element, `action.id === action.nodeId === node.id`. Skill sinh node ID theo convention `NO...`; payload từ BPMN modeler có thể dùng `Activity_*`. Không tự sinh `AC...` riêng; không đổi prefix của payload đang sửa. Trong node doc, `{ACTION_ID}` luôn bằng `{..._NODE_ID}` tương ứng.
- Response hoặc sample legacy có thể chứa action ID `AC...` do server remap. Khi sửa payload đã GET, giữ nguyên ID và reference nhất quán; không áp quy tắc create để đổi ID response một cách cơ học.
- Khai báo mọi ID (node, flow, action, gateway, ...) thành biến/hằng dùng chung từ đầu và dùng nhất quán trong cả XML lẫn JSON; ID sinh rời rạc ở nhiều chỗ gây lỗi `NODE_HAS_NO_CONNECT_TO_ANYTHING`.

#### BPMN XML và sơ đồ

Template XML, quy tắc bố cục, công thức waypoint và `BPMNLabel`: [references/bpmn-xml-and-diagram.md](references/bpmn-xml-and-diagram.md). Kiểm tra hình học bằng script và bố cục gọn: [nodes/bpmn-geometry-validation.md](nodes/bpmn-geometry-validation.md). Ràng buộc bắt buộc:

- Chỉ dùng prefix `bpmn2:` cho element BPMN-spec (namespace duy nhất được khai báo); `bpmn:` không khai báo và có thể bị server silent-strip khi CREATE. Giữ nguyên `elEx:`, `configEx:`, `bpmndi:`, `dc:`, `di:`, `bioc:`, `xsi:`. Node dùng `elEx:` cần `xmlns:elEx="http://element-ex/schema"` trong `bpmn2:definitions`.
- Mọi `sequenceFlow` nằm trong `bpmn2:process`, `sourceRef`/`targetRef` trỏ đúng `id` node; mỗi node liệt kê đủ `incoming`/`outgoing` (Start chỉ có outgoing, End chỉ có incoming).
- Mỗi node có tọa độ riêng theo cấu trúc flow (không xếp tất cả trên một hàng); mỗi `BPMNEdge` có waypoint tính từ bounds thật của node nguồn/đích, không hardcode; mỗi `BPMNShape` chứa `BPMNLabel` có `dc:Bounds`. Thiếu label: API vẫn trả `r: 0`, `isValid: true` nhưng node biến mất khỏi sơ đồ khi người dùng Save trong editor (silent fail).
- Sau khi sinh XML, chạy `scripts/validate_bpmn_geometry.py --mode request` trước POST (mục 4.1).

#### User Task

`pageSettings`, `content` (`layoutRow → layoutColumn → section → tab → group → components`), nhóm nút và thuộc tính chung của field: [references/user-task-templates.md](references/user-task-templates.md). Loại field và ràng buộc `required`/`readOnly`/`canSendData`: [nodes/user-task-form-fields.md](nodes/user-task-form-fields.md). Nhãn nút tiếng Việt: "Hoàn tác", "Hủy", "Thực hiện". Chỉ User Task Root của Manual Flow có `isRoot: true`; mọi User Task khác `isRoot: false`.

#### Resource tuỳ chỉnh: Variable, Formula, Text Template

Cả ba nằm trong `resources.custom`, `absoluteSlug` `$flow.{slug}`, `id` prefix `RS`, `parentTable: "process"`, `isStandard: false`, `editable: true`.

| | Variable (`type: 1`) | Formula (`type: 3`) | Text Template (`type: 4`) |
|---|---|---|---|
| Mục đích | Lưu trữ giá trị | Tính toán, xử lý dữ liệu | Tạo nội dung văn bản/HTML |
| Ngôn ngữ | Không (giá trị tĩnh/gán) | Cogover Scripting (Apache JEXL) | Apache Velocity (VTL) |
| `assignable` | `true` | `false` | `false` |
| `defaultValue` | Giá trị tĩnh hoặc tham chiếu | Mã nguồn scripting | Nội dung HTML/VTL |
| `absolutePath` | `workflow_resource:list.variable / {Name}` | `workflow_resource:list.formula / {Name}` | `workflow_resource:list.textTemplate / {Name}` |
| Kiểu trả về | `TEXT`, `NUMBER`, `BOOLEAN`, `DATE`, `DATE_TIME`, `RECORD` | `TEXT`, `NUMBER`, `BOOLEAN`, `DATE`, `DATE_TIME` | Luôn `TEXT` |
| Ghi bằng Assignment | Có | Không | Không |
| Đọc | [references/variables.md](references/variables.md) | [references/formula-resource.md](references/formula-resource.md); cú pháp: [Cogover Scripting API](../object-info/references/cogover-scripting-api-vi.md) | [references/text-template-resource.md](references/text-template-resource.md); cú pháp: [text-template-api-reference-vi.md](text-template-api-reference-vi.md) |

Tham chiếu resource trong action dùng `{"type": 4, "value": "$flow.{slug}", "valueDataType": ..., "valuePathName": ...}` (`type: 4` = lấy từ resource, không phải giá trị cố định); Text Template trong Send Email hoặc HTTP body dùng `type: 2`. Resource/field được dùng ở nơi khác phải có `resourcesUsedIn` tương ứng; trường con của lookup dùng trong Formula, Text Template hoặc Loop `currentItem` phải nằm trong `externalResourcesUsedIn` ở root level (chi tiết trong từng file).

### Chi tiết các loại Node

Khi cần tạo node cụ thể, đọc file tương ứng trong `nodes/`:

| Node | File | renderKey | XML Element | Mô tả ngắn |
|------|------|-----------|-------------|-------------|
| Manual Flow Start | Mục `Các loại quy trình` trong file này | `START_MANUAL_EVENT` | `bpmn2:startEvent` | Start cố định của `manual_flow` |
| Normal Flow Start | `nodes/normal-flow.md` | `START_NORMAL_EVENT` | `bpmn2:startEvent` | Start Event của `normal_flow`, không có Root User Task bắt buộc. Mẫu: `samples/sample_normal_flow.json` |
| Scheduled Flow Start | `nodes/scheduled-start-event.md` | `START_SCHEDULED_EVENT` | `bpmn2:startEvent` | Start cố định của `scheduled_flow`; hỗ trợ 8 kiểu chu kỳ |
| Triggered Flow Start | `nodes/record-triggered-flow.md`, `nodes/webhook-triggered-flow.md` | `START_TRIGGERED_EVENT` | `bpmn2:startEvent` | Start cố định của `triggered_flow`, loại record hoặc webhook |
| Sequence Flow Start | Mục `Các loại quy trình` trong file này | `START_SEQUENCE_EVENT` | `bpmn2:startEvent` | Start cố định của `sequence_flow` |
| Gateway | `nodes/gateway.md` | `EXCLUSIVE_GATEWAY`, `INCLUSIVE_GATEWAY`, `PARALLEL_GATEWAY` | `bpmn2:exclusiveGateway`, `bpmn2:inclusiveGateway`, `bpmn2:parallelGateway` | Phân nhánh có/không điều kiện. Mẫu: `samples/sample_process_exclusive_gw.json`, `samples/sample_inclusive_gateway.json`, `samples/sample_process_parallel_gw.json` |
| User Task Form Fields | `nodes/user-task-form-fields.md` | `USER_TASK` | `bpmn2:userTask` | Các loại trường form active, gồm short/long text, regex, display_text, select_record_table, numeric/decimal, date/date_time, email, phone, boolean, file, lookup, select list, percent, currency, label và URL |
| Send Email | `nodes/send-email-task.md` | `SEND_EMAIL_TASK` | `bpmn2:sendTask` | Gửi email tự động với subject, content (raw/template/variable), to/cc/bcc, attachments |
| Send HTTP Request | `nodes/send-http-request-task.md` | `SEND_HTTP_TASK` | `elEx:httpTask` | Gửi HTTP request (GET/POST/PUT/PATCH/DELETE/HEAD) với headers và body |
| Send Notification | `nodes/send-notification-task.md` | `SEND_NOTIFICATION_TASK` | `elEx:sendNotificationTask` | Gửi thông báo đến personnel |
| Get Records | `nodes/get-records-task.md` | `GET_RECORD_TASK` | `elEx:getRecordTask` | Lấy bản ghi từ đối tượng với điều kiện lọc và sắp xếp |
| Create Record | `nodes/create-record-task.md` | `CREATE_RECORD_TASK` | `elEx:createRecordTask` | Tạo bản ghi mới cho đối tượng |
| Update Record | `nodes/update-record-task.md` | `CREATE_RECORD_TASK` | `elEx:createRecordTask` | Cập nhật bản ghi (cùng XML element với Create, khác `actionType`) |
| Loop | `nodes/loop-task.md` | `LOOP_TASK` | `elEx:loopTask` | Duyệt danh sách, có 2 nhánh: for_each_item và after_last_item |
| Assignment | `nodes/assignment-task.md` | `ASSIGNMENT` | `elEx:assignment` | Gán giá trị cho biến (=, +=, -=, count) |
| Organization | `nodes/organization-task.md` | `ORGANIZATION_TASK` | `elEx:organizationTask` | Truy vấn cấu trúc tổ chức (manager, personnel, department, position) |
| Wait | `nodes/wait-task.md` | `WAIT_TASK` | `elEx:waitTask` | Runtime hiện hỗ trợ timer tương đối và email open/reply/link; đọc compatibility table trước khi dùng event khác |
| Sub Process | `nodes/sub-process-task.md` | `SUB_PROCESS` | `elEx:subProcess` | Gọi quy trình con, truyền/nhận biến |
| To Do | `nodes/todo-task.md` | `TODO_TASK` | `elEx:todoTask` | Tạo activity To Do; chỉ dùng trong Sequence Flow. Mẫu: `samples/sample_sequence_flow_todo.json` |
| Phone Call | `nodes/phone-call-task.md` | `PHONE_CALL_TASK` | `elEx:phoneCallTask` | Gọi từ hotline bằng recording hoặc TTS. Mẫu: `samples/sample_phone_call.json` |
| Export Record | `nodes/export-record-task.md` | `EXPORT_TASK` | `elEx:exportRecordTask` | Xuất record bằng document template. Mẫu: `samples/sample_export_record.json` |
| Respond to Webhook | `nodes/response-webhook-task.md` | `RESPONSE_WEBHOOK_TASK` | `elEx:responseWebhookTask` | Schema-only trên backend hiện tại; runtime chưa đăng ký action |
| Push Message | `nodes/push-message-task.md` | `PUSH_MESSAGE_TASK` | `elEx:pushMessageTask` | Gửi refresh/toast/background message. Mẫu: `samples/sample_push_message.json` |
| JSON to Object | `nodes/parse-to-object-task.md` | `PARSE_TO_OBJECT_TASK` | `elEx:parseToObjectTask` | Schema-only trên backend hiện tại; runtime chưa đăng ký action |
| Omni Message | `nodes/omni-message-task.md` | `OMNI_MESSAGE_TASK` | `bpmn2:sendTask` + `elEx:omniMessageTask` marker | Gửi Zalo ZBS/WhatsApp theo thứ tự fallback. Mẫu: `samples/sample_omni_message.json` |
| AI Agent | `nodes/ai-agent-task.md` | `AI_AGENT_TASK` | `bpmn2:sendTask` + `elEx:aiAgentTask` marker | Gọi agent, chờ kết quả, dùng output ở bước sau. Mẫu: `samples/sample_ai_agent.json`; kiểm tra tương thích API/editor trước khi lưu |
| End Branch | `nodes/end-branch-event.md` | `END_BRANCH_EVENT` | `bpmn2:endEvent` | Kết thúc nhánh hiện tại, không kết thúc toàn process. Mẫu: `samples/sample_end_branch.json` |
| End Process | `references/bpmn-xml-and-diagram.md` | `END_EVENT` | `bpmn2:endEvent` | Kết thúc toàn process; workflow phải có ít nhất một End Event |

Ghi chú theo node chưa có trong node doc: resource của Wait Task dùng `absolutePath` prefix `workflow_resource:list.wait` (ví dụ `workflow_resource:list.wait / Wait 1 / StartAt`).

### Support matrix node theo workflow type

| Mục | Manual | Normal | Scheduled | Triggered | Sequence | Điều kiện |
|---|---:|---:|---:|---:|---:|---|
| `START_MANUAL_EVENT` | ✓ | — | — | — | — | Start cố định, không thêm từ palette |
| `START_NORMAL_EVENT` | — | ✓ | — | — | — | Start cố định, không thêm từ palette |
| `START_SCHEDULED_EVENT` | — | — | ✓ | — | — | Start cố định, cấu hình `scheduleRules` |
| `START_TRIGGERED_EVENT` | — | — | — | ✓ | — | Start cố định, loại record/webhook |
| `START_SEQUENCE_EVENT` | — | — | — | — | ✓ | Start cố định, không thêm từ palette |
| To Do | — | — | — | — | ✓ | Sequence-only |
| Phone Call | ✓ | ✓ | ✓ | ✓ | ✓ | Sequence có automatic/manual |
| Export Record | ✓ | ✓ | ✓ | ✓ | ✓ | UI canonical dùng document template thật lấy qua `$document-template` |
| Respond to Webhook | ✗ | ✗ | ✗ | ✗ | ✗ | Payload/editor có schema nhưng runtime Process hiện chưa đăng ký action; không tạo cho flow cần chạy |
| Push Message | ✓ | ✓ | ✓ | ✓ | ✓ | Field phụ thuộc push/recipient type |
| JSON to Object | ✗ | ✗ | ✗ | ✗ | ✗ | Payload/editor có schema nhưng runtime Process hiện chưa đăng ký action; không tạo cho flow cần chạy |
| Omni Message | ✓ | ✓ | ✓ | ✓ | ✓ | Chỉ Zalo ZBS và WhatsApp đang active |
| AI Agent | △ | △ | △ | △ | △ | Có khả năng thực thi; cần Process API/editor hỗ trợ `AI_AGENT`, agent hoạt động và danh tính chạy hợp lệ. Flow tự động cần kiểm tra người khởi tạo hoặc chọn `PERSONNEL` |
| End Branch | ✓ | ✓ | ✓ | ✓ | ✓ | Dùng trong nhánh song song/phân nhánh |
| End Process | ✓ | ✓ | ✓ | ✓ | ✓ | Kết thúc toàn process; bắt buộc có ít nhất một End Event |

### Runtime compatibility và tiêu chí kiểm thử

`△` là hỗ trợ có điều kiện trên Workspace đích, chưa phải bằng chứng kiểm thử end-to-end. Với AI Agent, đọc `nodes/ai-agent-task.md` để kiểm tra khả năng lưu/mở lại node, output và nhánh xử lý lỗi; không suy ra khả năng tạo node chỉ từ khả năng thực thi.

Support matrix trên là contract cho backend runtime đang được dùng cùng skill này, không chỉ là danh sách node của palette. Trước khi tạo process có Wait, User Task, Formula hoặc một action tích hợp, đọc `nodes/runtime-validation.md` và file node tương ứng.

- Không suy luận PASS từ `isValid:true`, `ACTIVATED`, `isPublished:true` hoặc instance `COMPLETED`; phải chứng minh hiệu ứng nghiệp vụ/output/nhánh downstream.
- Các node có schema create nhưng chưa có runtime action được đánh dấu `✗`. Không sinh chúng cho quy trình được yêu cầu chạy.
- Nếu phiên bản backend thay đổi, phải kiểm tra lại runtime registration và chạy black-box test trước khi đổi matrix.

### Bước 3: Tạo JSON hoàn chỉnh

Payload gồm: `metadata` (theo loại flow), `participantPermission`, `processInstanceAccessControls`, `xmlString` (BPMN XML đã escape), `overviewScreen` (bắt buộc là object, không `null`; không có màn hình tổng quan tuỳ chỉnh thì dùng `{"layout": [], "permissionGeneralInfo": []}`), `type`, `permissions` (theo loại flow), `accessControls`, `progressStatus: "DRAFT"`, `processInfoId` (`PI...`), `userTasks`, `gateWays`, `resources` (`system`, `custom`, `userTasks`, `actions`, `loops`), `actions`, `loops` (cấu hình Loop nằm ở đây, không trong `actions`), `starterPermission`, `version: "V1"`, `name`, `slug`, `status: 2`.

- `processInstanceAccessControls[]` và `accessControls[]` dùng `"functions"` (mảng), không dùng `"action"` (chuỗi): `{"functions": ["START_INSTANCE"], "type": "personnel", "items": [""], "option": 1}` và `{"functions": ["VIEW"], "type": "personnel", "items": [""], "option": 1}`. Sai → lỗi `JSONArray[0] is not a JSONArray`.
- `userTasks[].taskPerformer` là mảng lồng mảng `taskPerformer[group_index][performer_index]`, mỗi performer có `field`, `isRawValue`, `value`, `option`: `[[{"field": "account", "isRawValue": true, "value": [], "option": 3}]]`; không dùng mảng đơn `[{"type": "personnel", ...}]`. Sai → cùng lỗi trên.
- Không để một key xuất hiện nhiều lần trong cùng JSON object, nhất là khi thay thế resource (ví dụ đổi `dataType` TEXT → SELECT_LIST phải thay hết key cũ). Sai → lỗi `Cannot parse request`.
- Exclusive Gateway: chỉ fork/open (`isOpen: true`, 1 incoming, nhiều outgoing) có nhánh mặc định trong `decisionOutcomes` và thuộc tính `default` trong XML; merge-only (`isOpen: false`, nhiều incoming, 1 outgoing) không có `default` và dùng `decisionOutcomes: []`. Outcome mặc định: `isDefault: true`, `outcomeOrder: -1`, `conditions: []`, `customConditionLogic: ""`, `slug: "_default"`, `color: "#939393"`, `flowId` = flow ID mà `default` trong XML trỏ tới; nhánh có điều kiện `isDefault: false`, `outcomeOrder` từ `0`, màu khác (ví dụ `#4CAF50`). Chi tiết và ràng buộc merge/fork: [nodes/gateway.md](nodes/gateway.md).
- Nhiều nhánh kết thúc: chọn rõ `END_BRANCH_EVENT` (chỉ kết thúc nhánh) hay `END_EVENT` (kết thúc toàn process); End Branch không có entry trong `actions`, `userTasks`, `loops`, `gateWays`.

### Bước 4: Gọi API tạo quy trình

KHÔNG tạo file JSON; gọi API tạo quy trình trực tiếp trên hệ thống.

#### 4.1. Sanity check XML trước khi POST (BẮT BUỘC)

`isValid: true` từ server KHÔNG đảm bảo XML hợp lệ ở mọi mặt: server chỉ validate kết nối logic giữa các node, không validate đầy đủ BPMNDiagram. Trước khi POST, kiểm tra `xmlString` đã sinh:

| # | Kiểm tra | Cách check (regex/đếm) |
|---|---|---|
| 1 | Số lượng `<bpmndi:BPMNShape>` = số node trong `<bpmn2:process>` | `xml.count('<bpmndi:BPMNShape')` |
| 2 | **Mỗi `<bpmndi:BPMNShape>` đều có `<bpmndi:BPMNLabel>` chứa `<dc:Bounds>`** | regex `<bpmndi:BPMNShape[^>]*>.*?<bpmndi:BPMNLabel>.*?<dc:Bounds[^/]*/>.*?</bpmndi:BPMNLabel>.*?</bpmndi:BPMNShape>` phải khớp với mọi shape |
| 3 | Số lượng `<bpmndi:BPMNEdge>` = số `<bpmn2:sequenceFlow>` | `xml.count('<bpmndi:BPMNEdge') == xml.count('<bpmn2:sequenceFlow')` |
| 4 | KHÔNG có tag prefix `<bpmn:` (chỉ dùng `<bpmn2:`) — namespace `bpmn` không được khai báo | `xml.count('<bpmn:') == 0` và `xml.count('</bpmn:') == 0` |
| 5 | Mọi node (trừ Start/End) đều có cả `<bpmn2:incoming>` và `<bpmn2:outgoing>` | duyệt từng node trong `<bpmn2:process>` |
| 6 | Mọi `<bpmn2:sequenceFlow>` có `sourceRef` và `targetRef` trỏ vào `id` node thực sự tồn tại | đối chiếu với danh sách node ID |
| 7 | Mọi slug user-editable dài ≥ 2 và khớp `^[A-Za-z](?!.*__)[A-Za-z0-9_]*[^_]$` | kiểm tra theo schema entity; cho phép các slug hệ thống cố định như `_default` |
| 8 | `overviewScreen` là object | `typeof overviewScreen == "object"`, không phải `null`/array; dùng `{ "layout": [], "permissionGeneralInfo": [] }` nếu không tùy chỉnh |
| 9 | Field User Task bắt buộc + chỉ đọc phải bật Gửi dữ liệu | với mọi component có `required` và `readOnly` truthy, yêu cầu `component.canSendData === true`; đây là cờ đưa giá trị field vào payload submit form |
| 10 | Mỗi node/flow có đúng một shape/edge tương ứng; waypoint đầu/cuối bám đúng biên node nguồn/đích; đường nối không đi xuyên node | chạy `scripts/validate_bpmn_geometry.py --mode request` theo [hướng dẫn kiểm tra hình học](nodes/bpmn-geometry-validation.md); yêu cầu exit code `0` và `ok: true` |

Bất kỳ check nào fail: sửa trong code sinh XML rồi mới POST; không POST rồi sửa vì process đã kích hoạt khó update (mục 4.4). Áp dụng kiểm tra này trước cả request cập nhật XML; đếm đủ edge hoặc reference đúng không thay thế kiểm tra hình học; validator không thay thế các kiểm tra metadata/form/nghiệp vụ còn lại trong bảng.

#### 4.2. Gọi API

Theo [api-process-builder.md](api-process-builder.md): `POST /bapi/v1/processes` với body là JSON ở Bước 3. Chỉ coi là thành công khi đồng thời `r = 0`, `data` là object, `data.id` và `data.processInfoId` đều là chuỗi không rỗng; một số lỗi filter trả `r:0` kèm `msg` lỗi và không có `data/id`, đó vẫn là create thất bại. Thành công: lấy `id` (process ID) và `processInfoId` từ `data`.

#### 4.3. Trả link cho khách hàng

`https://{WORKSPACE_DOMAIN}/settings/processes/{id}/{processInfoId}` với `{id}` = `data.id`, `{processInfoId}` = `data.processInfoId`.

#### 4.4. Sửa lỗi cho quy trình đã ACTIVATED

`PUT /bapi/v1/processes/{id}` trên process đang `progressStatus: ACTIVATED` (hoặc `isPublished: true`) trả `r: 414` "process is not in the right progress status for save", kể cả khi body có `progressStatus: "DRAFT"` và `isPublished: false`. Cách xử lý:

1. Hỏi xác nhận khách hàng trước khi xoá (Quy tắc an toàn).
2. Được đồng ý: lấy bản hiện tại qua `POST /bapi/v1/processes/view` với `{"id": "PE..."}`, fix XML, strip các trường server-managed (`id`, `processInfoId`, `version`, `versionNumber`, `status`, `created`, `updated`, ... theo api-process-builder.md) khỏi body.
3. `POST /bapi/v1/processes/delete` với `{"id": "PE...", "processInfoId": "PI..."}`: xoá toàn bộ versions cùng processInfoId.
4. `POST /bapi/v1/processes` với body đã fix; process mới mang `id`/`processInfoId` mới.
5. Trả link mới và giải thích nguyên nhân.

List/find process theo slug: `POST /bapi/v1/processes/list` với `{"page": 1, "limit": 50, "keywords": ["<slug_or_name_keyword>"]}`; tham số phân trang là `limit`, không phải `pageSize` hay `per_page`.

#### 4.5. Verify sau khi POST

Sau khi nhận `r:0`, gọi `POST /bapi/v1/processes/view` với `{"id": "<new id>"}` và kiểm tra hậu điều kiện:

1. Xác nhận `progressStatus`, `isPublished`, `isValid`, workflow `type`, action type/renderKey và các cấu hình nghiệp vụ chính.
2. So sánh số node, flow, `BPMNShape`, `BPMNEdge`, label và topology với payload trước POST. Server thật sự strip node/shape/edge hoặc làm hỏng reference nghiệp vụ thì báo lỗi; không dựa riêng vào `isValid:true`.
   - Chạy lại `scripts/validate_bpmn_geometry.py --mode response` trên dữ liệu vừa đọc; chỉ so giống payload trước POST là chưa đủ vì waypoint có thể đã sai từ payload ban đầu.
   - ID bị remap: đối chiếu node theo slug cấu hình + loại node; chỉ dùng tên + loại khi tổ hợp đó duy nhất. So các cặp nguồn–đích, nhánh mặc định/điều kiện và hình học theo mapping này; mapping mơ hồ phải được làm rõ, không tự ghép theo thứ tự mảng.
3. Workflow Server có thể serialize `incoming`, `outgoing`, `sequenceFlow` từ `bpmn2:` thành `bpmn:` trong response GET dù request dùng đúng `bpmn2:` (canonicalization phía server). Khi hậu kiểm, đếm tag theo local name hoặc cho phép cả hai prefix; không PUT/DELETE/recreate chỉ để đổi prefix response. Request create/update do skill sinh vẫn chỉ dùng `bpmn2:`.
4. Server có thể remap Node ID. Với `RESPONSE_WEBHOOK` nguồn Start, bắt buộc kiểm tra `action.data.waitActionSlug` bằng đúng Start Event ID sau GET; lệch thì process chưa sẵn sàng dù `isValid:true`. Không lặp PUT để đuổi theo ID vì mỗi lần save có thể remap lại; làm theo `nodes/response-webhook-task.md`.
5. Omni Message: server có thể bỏ marker rỗng `<elEx:omniMessageTask />` và parse `action.data` từ JSON string thành object. Xác minh bằng `renderKey: OMNI_MESSAGE_TASK`, action type và cấu hình methods; không PUT chỉ để khôi phục representation của request.
6. Duyệt lại mọi field User Task: còn component `required && readOnly` chưa có `canSendData: true` thì version chưa đạt, kể cả khi `isValid: true`.

Không PUT toàn bộ body vừa GET về: XML response có thể dùng prefix canonical `bpmn:`; round-trip nguyên trạng có thể làm server strip flow. Khi cần sửa DRAFT, dựng lại request hợp lệ dùng `bpmn2:` và chỉ thay đổi phần đã chủ đích.

#### 4.6. Kích hoạt và xác nhận process end-to-end (BẮT BUỘC)

Sau mọi lần tạo process, chạy vòng xác nhận dưới đây; không coi công việc hoàn tất chỉ vì API create trả `r: 0`, GET-back trả `isValid: true` hoặc process đã được kích hoạt. Đọc `nodes/runtime-validation.md` trước khi chạy.

Không hỏi xác nhận riêng trước khi chạy test: xác nhận luồng ở Bước 1 là quyền thực hiện trọn vòng triển khai trong phạm vi đã mô tả, gồm create, GET-back verify, kích hoạt, xuất bản, tạo lượt chạy và runtime test. Tiếp tục tự động, không dừng để hỏi "có chạy test không?". Vẫn phải hỏi trước khi DELETE process/record, hoặc khi chính sách an toàn cấp hệ thống yêu cầu xác nhận tại thời điểm thực hiện một side effect cụ thể (gửi thông điệp thật, truyền dữ liệu nhạy cảm): hoàn tất mọi bước không bị chặn trước, rồi chỉ hỏi xác nhận hẹp cho đúng hành động đó.

##### Bước 1: Kích hoạt process

1. Mở process bằng Chrome trong đúng session workspace của người dùng: `https://{WORKSPACE_DOMAIN}/process/processes/{PROCESS_ID}/{PROCESS_INFO_ID}`.
2. Kích hoạt. Giao diện có bước **Xuất bản** riêng thì xuất bản luôn để version sinh lượt chạy ổn định.
3. Đọc lại và xác nhận tối thiểu `progressStatus: "ACTIVATED"`, `isPublished: true`, `isValid: true`, đúng `PROCESS_ID` và `PROCESS_INFO_ID` vừa tạo.

##### Bước 2: Tạo lượt chạy theo loại flow

- **Manual, Normal:** vào link process ở Bước 1 và nhấn **Tạo lượt chạy**. Nút không xuất hiện hoặc gửi thất bại: kiểm tra trạng thái kích hoạt/xuất bản, quyền `START_INSTANCE` trong `processInstanceAccessControls` và quyền `VIEW` trong `accessControls`.
- **Scheduled:** trước khi thay đổi, lưu snapshot chính xác `scheduleRules` theo yêu cầu người dùng. Tạm đặt thời gian bắt đầu gần thời điểm kiểm tra, kích hoạt/xuất bản version test, quan sát trên Chrome xem instance có được sinh đúng thời điểm không. Trong cleanup bắt buộc, khôi phục nguyên cấu hình lịch người dùng yêu cầu, kích hoạt/xuất bản lại nếu việc lưu tạo version mới, rồi GET-back đối chiếu với snapshot. Không để lịch test tiếp tục chạy.
- **Triggered record:** dùng `$object-record` tạo bản ghi test phù hợp Object, event và conditions của trigger; trigger cần update thì cập nhật đúng field/giá trị để đưa bản ghi qua điều kiện kích hoạt. Dùng marker test duy nhất và theo dõi mọi record ID. Trigger delete: tuân thủ quy tắc xác nhận xoá của `$object-record`, chỉ xoá record test sau khi đã liệt kê ID cụ thể và người dùng xác nhận.
- **Triggered webhook:** lấy URL Webhook thực của process và gửi request với body hợp lệ theo `sampleData`/`parseToDataType` cùng đúng cơ chế xác thực đã cấu hình. Kiểm tra cả HTTP response và instance được sinh. Chỉ giữ token/secret trong tiến trình cần cho request; không đưa cookie, secret hoặc token vào file, log, commentary hay báo cáo.
- **Sequence:** chọn hoặc tạo bằng `$object-record` một bản ghi thật thuộc `metadata.objectTypeId`/`objectTypeSlug`, rồi gọi API dưới với ID thật. Trước khi gọi `/api/v1/run-workflow-server`, bắt buộc dùng `$cogover-api-auth` đổi API Key thành phiên Web App qua `POST /bapi/v1/auth-token`; không đọc cookie/local storage từ Browser và không thay API call bằng thao tác **Sequence → Kết nối** trên UI. Chỉ tiếp tục khi auth trả HTTP 200, `r: 0`, đúng workspace và đủ `HttpSessionId`, `AuthToken`, `XSRF-TOKEN`. Giữ ba giá trị trong tiến trình tạm, dùng chính `XSRF-TOKEN` cho cả hai header CSRF/XSRF, không ghi hoặc in credential ra file/log/commentary/final.

  ```bash
  curl --url 'https://{WORKSPACE_DOMAIN}/api/v1/run-workflow-server' \
    -H 'accept: application/json, text/plain, */*' \
    -H 'content-type: application/json' \
    -b 'HttpSessionId={HTTP_SESSION_ID}; AuthToken={AUTH_TOKEN}; XSRF-TOKEN={XSRF_TOKEN}' \
    -H 'x-csrf-token: {XSRF_TOKEN}' \
    -H 'x-req-service: 7' \
    -H 'x-req-type: 6' \
    -H 'x-xsrf-token: {XSRF_TOKEN}' \
    --data-raw '{"list":[{"processId":"{PROCESS_ID}","flowObjectRecordId":"{FLOW_OBJECT_RECORD_ID}"}]}'
  ```

  Lỗi `Can not found processor for request: service=...`: thử lại đúng request bằng literal `curl` thay cho `urllib`. `curl` PASS thì phân loại lỗi client transport và tiếp tục bằng `curl`; chỉ kết luận processor không khả dụng khi `curl` cũng lỗi. Không đổi service number bằng thử ngẫu nhiên.

##### Bước 3: Quan sát và đánh giá lượt chạy

1. Bảo đảm người test hiện tại có quyền xem instance của process. Cần cấp quyền/vị trí/phòng ban tạm: lưu snapshot trước thay đổi và dùng `$user-permission`; không nới quyền rộng hơn mức cần để kiểm thử.
2. Mở `https://{WORKSPACE_DOMAIN}/process/process-instances?filter=all`, xác định đúng instance mới bằng process ID, thời gian bắt đầu và dữ liệu test; không nhầm với instance cũ hoặc instance do người khác tạo.
3. Mở instance, quan sát diagram, trạng thái từng node, output và Debug. Instance tới **User Task đầu tiên**: nhập dữ liệu hợp lý, đúng kiểu và phù hợp kịch bản nghiệp vụ rồi submit. Task chỉ cho một số vị trí/phòng ban thực hiện: dùng `$user-permission` phân tạm vị trí/phòng ban cho người test, xác minh quan hệ đã có hiệu lực, bắt buộc rollback về snapshot sau test.
4. Đối chiếu với yêu cầu bài toán: nhánh đi đúng, task đúng người, dữ liệu/action/output/side effect đúng giá trị mong đợi. Đọc, tạo hoặc đối chiếu dữ liệu nghiệp vụ bằng `$object-record`; không suy ra PASS chỉ từ trạng thái `COMPLETED`.
5. Debug sâu: dùng `$object-record` đọc Object có slug chính xác `Process_Debug_data`, lọc theo process/instance/thời điểm hoặc marker test dựa trên schema thực tế; không đoán field slug.
6. Đánh giá theo tiêu chí observable và phân loại `PASS`, `PARTIAL`, `FAIL_SKILL`, `FAIL_RUNTIME` hoặc `BLOCKED_ENV` trong `nodes/runtime-validation.md`. Lỗi thuộc payload/skill và sửa được an toàn: sửa rồi chạy lại toàn bộ vòng xác nhận. Sửa process đã activated buộc phải xoá/tạo lại: theo mục 4.4 và hỏi xác nhận trước khi xoá.

##### Cleanup và báo cáo

- Luôn phục hồi lịch Scheduled Flow và mọi quyền/vị trí/phòng ban tạm, kể cả khi lượt chạy lỗi hoặc kiểm thử bị gián đoạn; đọc lại để xác nhận trạng thái cuối khớp snapshot/yêu cầu người dùng.
- Theo dõi dữ liệu test bằng marker/ID. Xoá fixture phải theo quy tắc xác nhận xoá của `$object-record`; chưa được phép xoá thì báo rõ Object và ID còn lại thay vì tuyên bố đã dọn sạch.
- Báo link process, ID instance, loại flow/cách kích hoạt, trạng thái cuối, bằng chứng nghiệp vụ, dữ liệu Debug đã dùng, các thay đổi tạm đã rollback và mọi fixture còn tồn đọng. Không báo credential hoặc secret.

## Ví dụ

Người dùng: "Quy trình xin nghỉ phép": `Bắt đầu -> Root -> Exclusive Gateway`; nhánh "Số ngày > 5" (điều kiện `$userTask.Root.so_ngay_xin_nghi >= 5`) `-> User Task 1 -> Kết thúc`; nhánh "Mặc định" `-> User Task 2 -> Kết thúc (2)`.

Trợ lý trình bày lại luồng (Bắt đầu → Root → Exclusive; Exclusive → "Số ngày xin nghỉ > 5" → User Task 1 → Kết thúc quy trình; Exclusive → "Mặc định" → User Task 2 → Kết thúc quy trình (2)), người dùng đồng ý; trợ lý dựng JSON, gọi `POST /bapi/v1/processes`, GET-back verify, kích hoạt, chạy một kịch bản cho từng nhánh cần chứng minh và chỉ sau khi đối chiếu đúng instance và kết quả nghiệp vụ mới báo kết quả kèm link process, instance ID và trạng thái PASS/PARTIAL/FAIL/BLOCKED.

## File tham khảo

Một số sample là snapshot response/legacy: có thể chứa action ID đã được server remap (`AC...`) hoặc field chỉ có trong response. Khi dùng để tạo mới, lấy contract trong `SKILL.md`, `nodes/*.md`, `references/*.md` làm canonical, bỏ response envelope/field server-owned và đặt `action.id === action.nodeId ===` BPMN node ID. Quy ước fixture: [samples/README.md](samples/README.md).

| Khi làm gì | Đọc |
|---|---|
| Dựng `xmlString`: template XML, namespace, bố cục node, waypoint, `BPMNLabel` | [references/bpmn-xml-and-diagram.md](references/bpmn-xml-and-diagram.md); kiểm tra hình học, bố cục gọn: [nodes/bpmn-geometry-validation.md](nodes/bpmn-geometry-validation.md), `scripts/validate_bpmn_geometry.py` |
| Dựng User Task: `pageSettings`, `content`, nhóm nút, thuộc tính chung của field | [references/user-task-templates.md](references/user-task-templates.md); loại field, `canSendData`: [nodes/user-task-form-fields.md](nodes/user-task-form-fields.md); mẫu `samples/sample_process_user_task_full.json` (nhiều loại trường), `samples/sample_process_1.json`, `samples/sample_process_2.json` |
| Variable: kiểu, `metaDataType`, default từ resource, dùng làm default cho component | [references/variables.md](references/variables.md); mẫu `samples/sample_process_variable.json` |
| Formula | [references/formula-resource.md](references/formula-resource.md); cú pháp: [Cogover Scripting API](../object-info/references/cogover-scripting-api-vi.md); mẫu `samples/sample_formula.json` |
| Text Template | [references/text-template-resource.md](references/text-template-resource.md); cú pháp VTL: [text-template-api-reference-vi.md](text-template-api-reference-vi.md); mẫu `samples/sample_process_text_template.json` |
| Start theo loại flow | Normal: [nodes/normal-flow.md](nodes/normal-flow.md), `samples/sample_normal_flow.json`; Scheduled: [nodes/scheduled-start-event.md](nodes/scheduled-start-event.md) (8 chu kỳ, validation từng loại), `samples/sample_scheduled_flow_1.json`; Triggered record: [nodes/record-triggered-flow.md](nodes/record-triggered-flow.md), `samples/sample_triggered_flow.json`; webhook: [nodes/webhook-triggered-flow.md](nodes/webhook-triggered-flow.md), `samples/Webhook_triggered_flow.json`; Sequence: `samples/sample_sequence_flow.json` |
| Gateway | [nodes/gateway.md](nodes/gateway.md); mẫu `samples/sample_process_exclusive_gw.json` (2 nhánh), `samples/sample_process_gw_conditions.json` (điều kiện chi tiết), `samples/sample_inclusive_gateway.json`, `samples/sample_process_parallel_gw.json` |
| Task/action cụ thể | File trong bảng "Chi tiết các loại Node". Mẫu: Send Email `samples/sample_process_usertask_send_email.json`; HTTP `samples/sample_send_http_request.json`; Notification `samples/sample_process_send_notification.json`; Get Record `samples/sample_process_usertask_get_records.json`; Create Record `samples/sample_process_user_task_create_record.json`; Update Record `samples/sample_process_user_task_update_record.json`; Loop `samples/sample_process_loop.json` (duyệt danh sách Leads); Assignment `samples/sample_process_assignment.json`; Organization `samples/sample_process_organization.json` (quản lý trực tiếp); Wait `samples/sample_process_wait.json` (Send Email + Wait `EMAIL_REPLY`, `LINK_WAS_CLICKED`; đọc runtime compatibility trong `nodes/wait-task.md`, không suy ra mọi event trên UI đều chạy được); Sub Process `samples/sample_process_call_sub_process.json` (quy trình con `manual_flow`, truyền/nhận biến); To Do `samples/sample_sequence_flow_todo.json`; Phone Call `samples/sample_phone_call.json` (TTS); Export Record `samples/sample_export_record.json`; Push Message `samples/sample_push_message.json` (TOAST); Omni Message `samples/sample_omni_message.json` (Zalo ZBS, action data JSON string); AI Agent `samples/sample_ai_agent.json` (Normal Flow → AI Agent → End Process; agent ID placeholder, `action.data` JSON string, chưa chạy trên Workspace); End Branch `samples/sample_end_branch.json` (parallel split); Respond to Webhook `samples/sample_respond_to_webhook.json` và JSON to Object `samples/sample_parse_to_object.json` (schema/migration only, backend chưa chạy) |
| Gọi API tạo/cập nhật/xoá/list/view, lỗi `r: 414`, canonicalization của response view | [api-process-builder.md](api-process-builder.md) |
| Kích hoạt, tạo lượt chạy, tiêu chí PASS theo node, email workspace, backend limitations, phân loại báo cáo | [nodes/runtime-validation.md](nodes/runtime-validation.md) |
