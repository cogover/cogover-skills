# AI Agent Task — Gọi AI Agent

Đọc khi cần gọi một AI Agent đã có trong Workspace để phân tích, tóm tắt, phân loại hoặc thực hiện công việc bằng các công cụ được cấu hình cho agent. Node gửi instruction và ngữ cảnh, chờ kết quả rồi cung cấp output cho gateway/action tiếp theo.

## Phạm vi và điều kiện sử dụng

- Dùng được trong thiết kế Manual, Normal, Scheduled, Triggered và Sequence Flow khi Workspace hỗ trợ node. Manual vẫn cần Root User Task ngay sau Start.
- Khả năng thực thi AI Agent không bảo đảm phiên bản Process API và editor hiện tại đã hỗ trợ tạo/lưu node. Trước khi triển khai, xác nhận node **AI Agent** có trong editor hoặc metadata/tài liệu sản phẩm của Workspace; sau khi lưu phải GET-back theo hướng dẫn bên dưới.
- Editor cũ có thể lưu AI Agent thành loại action khác, chẳng hạn Send Notification. Không mở rồi lưu bằng editor chưa hỗ trợ node. Nếu gặp tình trạng này, dừng chỉnh sửa bằng editor đó, báo giới hạn phiên bản; không đổi action sang loại khác để vượt kiểm tra.
- Lấy `agentId` thật từ danh sách/chọn agent trong giao diện hoặc API đã được công bố cho Workspace. Agent phải thuộc Workspace và đang hoạt động. Không dùng tên, slug, model ID hay ID ví dụ thay cho agent ID; không tự đoán endpoint liệt kê agent.
- Xác nhận agent có công cụ và quyền phù hợp nếu bài toán cần đọc/ghi dữ liệu. Agent chỉ trả lời văn bản chưa chứng minh đã đọc hay thay đổi bản ghi.

## Thông tin cần xác định

Chỉ hỏi những phần chưa có trong yêu cầu: agent, mục tiêu/instruction, nguồn dữ liệu, đầu ra mong muốn và cách dùng ở bước sau; phiên mới hay tiếp tục phiên trước; danh tính chạy; chính sách tool; giới hạn thời gian/số vòng và cách xử lý lỗi.

Khi dùng record ngữ cảnh, lấy object/field metadata bằng `$object-info` và xác minh record bằng `$object-record`. Khi cần chọn nhân sự chạy, dùng `$user-permission` để resolve personnel ID thực tế. Các ví dụ dưới đây là placeholder, không phải dữ liệu Workspace.

## BPMN và action payload

| Thành phần | Giá trị |
|---|---|
| `actions[].type` | `AI_AGENT` |
| `renderKey` | `AI_AGENT_TASK` |
| BPMN request | `bpmn2:sendTask` với marker `elEx:aiAgentTask` trong `extensionElements` |
| `actions[].data` | Chuỗi JSON serialize từ cấu hình bên dưới |
| Resource prefix hiển thị | `workflow_resource:list.aiAgent` |
| Đầu ra | `$action.{action_slug}.output`, kiểu `RECORD` |

Khai báo `xmlns:elEx="http://element-ex/schema"`. Trong create payload, dùng cùng ID cho `action.id`, `action.nodeId` và BPMN node. Giữ ID đã trả về khi sửa process hiện hữu.

```xml
<bpmn2:sendTask id="{AI_NODE_ID}" name="Tóm tắt yêu cầu">
  <bpmn2:extensionElements>
    <elEx:aiAgentTask />
    <configEx:elementInfo renderKey="AI_AGENT_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</bpmn2:sendTask>
```

Response có thể biểu diễn node bằng `elEx:aiAgentTask`. Kiểm tra loại action, renderKey, topology và cấu hình; không PUT chỉ để đổi cách biểu diễn XML. Request mới theo mẫu trên, có đủ shape/edge/label theo `SKILL.md`.

### Cấu hình tối thiểu và mặc định

Đây là object **trước khi serialize** vào `actions[].data`:

```json
{
  "agentId": "{AGENT_ID}",
  "instruction": {"type": 1, "value": "Tóm tắt yêu cầu thành ba ý ngắn. Chỉ phân tích nội dung được cung cấp."},
  "contextVariables": [],
  "contextRecords": [],
  "session": {"mode": "NEW"},
  "runAs": {"mode": "AGENT_DEFAULT"},
  "approvalPolicy": "DENY",
  "timeoutInSeconds": 300,
  "maxTurns": null,
  "continueOnFailure": false
}
```

| Field | Quy tắc |
|---|---|
| `agentId` | Chuỗi ID thật, bắt buộc |
| `instruction` | ActionValue bắt buộc; sau khi thay biến phải còn nội dung |
| `contextVariables` | Mảng `{key, value}`; mặc định `[]`. Key duy nhất, khớp `^[A-Za-z][A-Za-z0-9_]{0,63}$`; không dùng tiền tố `_` dành cho hệ thống |
| `contextRecords` | Mảng `{objectSlug, recordId}`; `recordId` là ActionValue trỏ ID đơn, không phải cả record/list |
| `session` | `NEW` mặc định; `CONTINUE` cần `sessionId` hợp lệ |
| `resultDataType` | Bỏ khi chỉ cần văn bản; nếu cần kết quả có cấu trúc, gửi object đầy đủ có `children` |
| `runAs` | `AGENT_DEFAULT`, `PROCESS_STARTER` hoặc `PERSONNEL` |
| `approvalPolicy` | `DENY` mặc định hoặc `AUTO_APPROVE` trong phạm vi được người dùng cho phép |
| `timeoutInSeconds` | Số nguyên 30–1800, mặc định 300; không gửi field `timeoutSeconds` thay thế |
| `maxTurns` | `null`/bỏ trống = theo agent; nếu đặt thì số nguyên 1–80, còn chịu trần cấu hình của agent |
| `continueOnFailure` | `false` mặc định: dừng với lỗi; `true`: ghi output lỗi và đi tiếp |

Không dùng `0` để biểu diễn timeout/số vòng vô hạn. Không cần gửi `mode`; nếu giữ payload cũ thì dùng `AGENT`. `PROMPT` chưa tạo chế độ thực thi riêng, không dùng nó để gọi mô hình trực tiếp thay cho agent. `approvalPolicy: USER_TASK` chưa được hỗ trợ; muốn người duyệt, thiết kế một User Task riêng trong process.

### ActionValue: văn bản và tham chiếu

Áp dụng cho instruction, biến ngữ cảnh, record ID và session ID:

| `type` | `value` | Cách dùng |
|---|---|---|
| `1` | Chuỗi thuần | Trả nguyên văn, không thay `$flow...` |
| `5` | Chuỗi inline chứa tham chiếu resource | Thay biến trong prompt, ví dụ `"Tóm tắt: $flow.request_text"` |
| `4` | Đúng một đường dẫn resource | Đọc biến, field, output trước đó; thích hợp cho context và ID |
| `2` | Đường dẫn Text Template đã tồn tại | Nội dung Velocity nằm trong `defaultValue` của resource, không nằm inline trong ActionValue |
| `3` | Đường dẫn Formula đã tồn tại | Tính Formula; không nhúng code trực tiếp vào ActionValue |

`type: 2` với cả câu prompt sẽ bị hiểu là tên resource và có thể lỗi `Resource not found`. Với node sau chèn `$action.ai_summary.output.text` trong một câu, dùng `type: 5` nếu field đó hỗ trợ ActionValue; nếu chỉ lấy đúng output thì dùng `type: 4`.

```json
{
  "instruction": {"type": 5, "value": "Tóm tắt yêu cầu: $flow.request_text"},
  "contextVariables": [
    {"key": "request_text", "value": {"type": 4, "value": "$flow.request_text"}},
    {"key": "language", "value": {"type": 1, "value": "vi"}}
  ],
  "contextRecords": [
    {"objectSlug": "{OBJECT_SLUG}", "recordId": {"type": 4, "value": "$flow.target_record.id"}}
  ]
}
```

Biến ngữ cảnh lấy từ resource giữ số/boolean; record/map/list được chuyển thành chuỗi JSON, giá trị null thành chuỗi rỗng. Giá trị raw `type: 1` là văn bản. Nếu cần agent đọc record, dùng `contextRecords` với object slug và `.id` thật; không dựa vào việc truyền một ID trong prompt để khẳng định agent đã được nạp record. Không để record ID rỗng: mục ngữ cảnh đó có thể bị bỏ qua.

### Phiên và danh tính chạy

```json
{
  "session": {
    "mode": "CONTINUE",
    "sessionId": {"type": 4, "value": "$action.ai_previous.output.sessionId"}
  },
  "runAs": {"mode": "PERSONNEL", "personnelId": "{PERSONNEL_ID}"}
}
```

- `CONTINUE`: dùng phiên của node AI Agent đã chạy trước trên đường đi hiện tại, với agent/quyền truy cập phù hợp. Kiểm tra output nguồn trước khi nối phiên. Session ID rỗng có thể làm node tạo phiên mới; ID không tồn tại có thể trả `SESSION_NOT_FOUND`. Không coi việc đi tiếp là đã giữ ngữ cảnh.
- `AGENT_DEFAULT`: dùng nhân sự được cấu hình cho agent, nếu không có thì người khởi tạo lượt chạy. `PROCESS_STARTER`: dùng người khởi tạo. `PERSONNEL`: dùng `personnelId` là chuỗi ID, không phải ActionValue hay account ID.
- Trước khi gọi agent, lượt chạy vẫn cần xác định được nhân sự: với hai mode đầu, cần người khởi tạo; với `PERSONNEL`, cần ID đã chọn. Vì vậy Scheduled/Triggered hoặc lượt chạy tự động không có starter nên chọn `PERSONNEL` hợp lệ, kể cả khi agent đã cấu hình nhân sự mặc định.
- `DENY` ngăn tool cần phê duyệt thực thi; agent vẫn có thể trả lời và kết thúc `COMPLETED`. Không suy ra rằng mọi tool đều đã chạy. Chỉ dùng `AUTO_APPROVE` khi người dùng đã cho phép tự động thực hiện các hành động liên quan; không tự bật để xử lý lỗi bị từ chối.

### Kết quả có cấu trúc

```json
{
  "resultDataType": {
    "nameDataType": "result",
    "children": [
      {"slug": "summary", "absoluteSlug": "$action.ai_summary.output.result.summary", "dataType": "TEXT", "displayOrder": 1, "required": true, "isList": false, "description": "Tóm tắt bằng tiếng Việt"},
      {"slug": "needs_review", "absoluteSlug": "$action.ai_summary.output.result.needs_review", "dataType": "BOOLEAN", "displayOrder": 2, "required": true, "isList": false},
      {"slug": "tags", "absoluteSlug": "$action.ai_summary.output.result.tags", "dataType": "TEXT", "displayOrder": 3, "required": false, "isList": true}
    ]
  }
}
```

- Kiểu hỗ trợ: `TEXT`, `NUMBER`, `BOOLEAN`, `DATE`, `DATE_TIME`, `RECORD`. `isList: true` tạo danh sách; `RECORD` có `children` lồng. Đây là cấu trúc kết quả, không mặc nhiên là một Object/record đã lưu trong Workspace.
- Slug field phải duy nhất trong cùng object, đúng quy tắc slug của skill. Cập nhật đệ quy mọi `absoluteSlug` khi đổi action slug hoặc cấu trúc lồng.
- `DATE` dùng chuỗi ngày, `DATE_TIME` dùng chuỗi ngày giờ theo schema kết quả; không tự áp timestamp milliseconds của Variable DATE_TIME. `description` hướng dẫn ý nghĩa, không phải ràng buộc enum; nếu chỉ cho phép một tập giá trị, kiểm tra thêm ở gateway hoặc Formula.
- Chỉ lưu `resultDataType` dạng chuỗi slug sẽ không cung cấp cấu trúc kết quả cho lần chạy. GET-back phải còn đầy đủ `children` trong `action.data`; children hiển thị riêng ở resource không thay thế điều kiện này.
- Không có schema thì `output.result` có thể null; đọc `output.text`. Có schema nhưng kết quả không khớp có thể nhận `FAILED` với `RESULT_SCHEMA_MISMATCH`. Chỉ dùng `result.*` sau khi đã kiểm tra trạng thái và dữ liệu thực nhận.

## Resources và đầu ra

Trong `resources.actions`, tạo nhóm cùng `id`, `nodeId`, `type: AI_AGENT`, `name`, `slug` với action. Nhóm chứa `startAt`, `endAt` kiểu `DATE_TIME` và `output` kiểu `RECORD`; mỗi resource có ID riêng, `parentId` là action ID, `parentTable: action`, `type: 1`, `isList: false`, `isStandard: true`, `availableForInput: true`, `availableForOutput: true`. Đây là resource chuẩn của action, không tạo Variable assignable để thay thế output.

Prefix `absoluteSlug` là `$action.{slug}`; prefix `absolutePath` là `workflow_resource:list.aiAgent / {Tên node}`. Children cố định của output do API cung cấp khi đọc lại; cấu trúc tùy chỉnh gửi qua `data.resultDataType`, không tự thêm Object Type ID cho output.

| Đường dẫn sau `$action.{slug}.` | Kiểu | Ý nghĩa |
|---|---|---|
| `startAt`, `endAt` | DATE_TIME | Thời điểm bắt đầu/kết thúc node |
| `output.status` | TEXT | `RUNNING`; khi xong: `COMPLETED`, `FAILED`, `TIMEOUT`, `CANCELLED`, `MAX_TURNS`, `GUARDRAIL_REJECTED`, `APPROVAL_DENIED` |
| `output.text` | TEXT | Câu trả lời cuối, có thể trống khi lỗi |
| `output.sessionId`, `output.runId` | TEXT | Phiên và mã lượt chạy agent do hệ thống cấp; dùng để đối chiếu, không tự điền vào create payload |
| `output.errorCode`, `output.errorMessage` | TEXT | Chi tiết lỗi; có thể null |
| `output.inputTokens`, `output.outputTokens` | NUMBER | Số token được báo cáo |
| `output.iterations`, `output.durationMs` | NUMBER | Số vòng và thời lượng tính bằng milliseconds |
| `output.model` | TEXT | Mô hình thực tế được sử dụng |
| `output.toolCalls` | TEXT | Chuỗi JSON array, không phải list resource; có thể null. Mỗi mục có tên, trạng thái, tóm tắt, thời lượng |
| `output.result` | RECORD | Object theo schema cấu hình hoặc null |

Output khi mới nhận chạy chưa phải kết quả cuối. Các chỉ số sử dụng có thể null nếu lỗi xảy ra trước khi chạy; không đổi null thành 0 rồi coi đó là số đo thật.

Khi một resource được dùng trong instruction/context/session, thêm `resourcesUsedIn` theo convention chung với `actionType: AI_AGENT`, `parentTable: action`, ID và slug của node tiêu thụ. Với lookup child, bổ sung `externalResourcesUsedIn` theo metadata đã resolve. Với output được node sau tiêu thụ, tracking trỏ tới node sau đó. Các reference phải có nguồn và có giá trị trước khi AI Agent chạy.

## Lỗi và nhánh sau AI Agent

- Node chờ đến khi agent kết thúc hoặc hết thời gian. Không thêm Wait riêng để đợi AI Agent.
- `continueOnFailure: false`: lỗi khởi chạy hoặc trạng thái cuối khác `COMPLETED` làm lượt chạy dừng với lỗi; gateway sau node không có cơ hội xử lý lỗi đó.
- `continueOnFailure: true`: cả lỗi khởi chạy và lỗi lúc thực thi được ghi vào output rồi đi tiếp. Đặt gateway kiểm tra `$action.{slug}.output.status == "COMPLETED"` trước nhánh nghiệp vụ; nhánh mặc định chuyển sang xử lý lỗi/nhân sự xem lại.
- Timeout có thể mất thêm một khoảng ngắn để cập nhật trạng thái. Sau timeout/huỷ/lỗi, không mặc định rằng các tool đã chạy trước đó được hoàn tác. Kiểm tra dữ liệu thực tế trước khi chạy lại để tránh tác động trùng.
- Khi gặp `AGENT_NOT_FOUND`/`AGENT_INACTIVE`, kiểm tra agent đã chọn; `VALUE_RESOLVE_FAILED` kiểm tra instruction/reference/danh tính chạy; `PERSONNEL_NOT_FOUND` kiểm tra nhân sự; `SESSION_NOT_FOUND` kiểm tra phiên; `QUOTA_EXCEEDED` kiểm tra hạn mức; `RESULT_SCHEMA_MISMATCH` kiểm tra kết quả/schema. Giữ nguyên mã lỗi thực nhận, không tự ánh xạ sang mã số chưa được công bố.

## Xác minh trước và sau khi lưu

1. Kiểm tra agent hoạt động, danh tính chạy, scope công cụ và mọi reference. Validate ActionValue, key/slug, timeout/maxTurns, session ID nếu `CONTINUE`; serialize `action.data` đúng một lần.
2. Kiểm tra XML/ID/diagram theo `SKILL.md`; dùng mẫu `samples/sample_ai_agent.json` làm cấu trúc khởi đầu. Sample chỉ minh họa, chưa được chạy trên Workspace và phải thay `{AGENT_ID}` bằng ID thật, sinh lại ID process/node/resource khi tạo mới.
3. Tạo qua Public Process API trong `api-process-builder.md`, GET-back và đối chiếu `AI_AGENT`, `AI_AGENT_TASK`, agent ID, instruction, session, runAs, policy, giới hạn, `continueOnFailure`, ba resources chuẩn và children output. `data` trả về string thì parse trước khi so sánh. Nếu có schema, kiểm tra cả `action.data.resultDataType.children` và resource `output.result.children`.
4. Nếu API từ chối action, lưu sai loại node hoặc mất cấu hình/schema, không coi `r: 0`/`isValid: true` là đã sẵn sàng. Báo giới hạn phiên bản quan sát được; không thử ghi lại bằng payload legacy ngẫu nhiên.
5. Kích hoạt và chạy theo `SKILL.md` cùng `runtime-validation.md`; kiểm tra lại cấu hình nếu có bước editor Save/Publish. Không tuyên bố PASS từ việc đọc code, parse JSON/XML hoặc create thành công.

## Kịch bản kiểm thử nghiệp vụ

| Trường hợp | Bằng chứng cần có |
|---|---|
| Phân tích văn bản | Input có marker riêng; đúng instance/node có `COMPLETED`, trả lời đúng nội dung và bước sau đọc được `output.text` |
| Prompt inline + context | Agent nhận giá trị đã thay, không còn nguyên `$flow...`; số/boolean/list được hiểu đúng |
| Có tool/record | Đối chiếu `toolCalls` và dữ liệu thực tế bằng `$object-record`; câu trả lời tự nhận đã cập nhật không đủ |
| Structured result | GET-back còn schema đầy đủ; kết quả có đúng field/type/list và gateway/assignment sau node dùng được `result.*` |
| `CONTINUE` | Hai node nối tiếp; session ID khớp và node sau sử dụng được chi tiết chỉ cung cấp ở node trước |
| Lỗi, `continueOnFailure: true` | Lỗi được ghi vào output, nhánh lỗi chạy; nhánh thành công không chạy |
| Lỗi, `continueOnFailure: false` | Lượt chạy ghi nhận lỗi tại node, node sau không chạy |
| Timeout / giới hạn vòng | Với fixture phù hợp, quan sát đúng trạng thái và nhánh đã thiết kế; không đánh PASS chỉ vì đã chờ đủ thời gian |
| Tool cần phê duyệt với `DENY` | Tool bị từ chối, không phát sinh hiệu ứng tương ứng; `COMPLETED` của agent không thay thế kiểm tra này |

Chỉ kiểm thử trường hợp cần cho yêu cầu và nằm trong phạm vi đã được phép. Báo process/instance, `runId`, trạng thái, output/hiệu ứng đã đối chiếu; dùng `PARTIAL` hoặc `BLOCKED_ENV` nếu chưa thể quan sát đầy đủ. Không đưa prompt chứa dữ liệu nhạy cảm hoặc secret vào báo cáo.
