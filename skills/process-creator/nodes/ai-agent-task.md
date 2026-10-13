# AI Agent Task — Gọi AI Agent

Đọc khi cần gọi một AI Agent đã có trong Workspace để phân tích, tóm tắt, phân loại hoặc thực hiện công việc bằng các công cụ được cấu hình cho agent. Node gửi instruction và ngữ cảnh, chờ kết quả rồi cung cấp output cho gateway/action tiếp theo. Có block `delivery` thì trong lượt chạy agent còn được chủ động nhắn chat cho một nhân sự (nhắc việc, báo kết quả).

## Phạm vi và điều kiện sử dụng

- Dùng được trong thiết kế Manual, Normal, Scheduled, Triggered và Sequence Flow khi Workspace hỗ trợ node.
- Khả năng thực thi AI Agent không bảo đảm phiên bản Process API và editor hiện tại đã hỗ trợ tạo/lưu node. Trước khi triển khai, xác nhận node **AI Agent** có trong editor hoặc metadata/tài liệu sản phẩm của Workspace; sau khi lưu phải GET-back theo hướng dẫn bên dưới.
- Block `delivery`, nhân sự dạng ActionValue (`runAs.personnelId`, người nhận) và điều kiện gateway trên child của `output` đã lưu và đọc lại được qua Public Process API trên Workspace kiểm thử ngày 2026-10-13. Workspace chạy phiên bản cũ hơn có thể bỏ `delivery` hoặc báo lỗi validate: GET-back mới là bằng chứng, không suy ra từ `r: 0`.
- Editor cũ có thể lưu AI Agent thành loại action khác, chẳng hạn Send Notification. Không mở rồi lưu bằng editor chưa hỗ trợ node. Nếu gặp tình trạng này, dừng chỉnh sửa bằng editor đó, báo giới hạn phiên bản; không đổi action sang loại khác để vượt kiểm tra.
- Lấy `agentId` thật từ danh sách/chọn agent trong giao diện hoặc API đã được công bố cho Workspace. Agent phải thuộc Workspace và đang hoạt động. Không dùng tên, slug, model ID hay ID ví dụ thay cho agent ID; không tự đoán endpoint liệt kê agent.
- Xác nhận agent có công cụ và quyền phù hợp nếu bài toán cần đọc/ghi dữ liệu. Agent chỉ trả lời văn bản chưa chứng minh đã đọc hay thay đổi bản ghi.

## Thông tin cần xác định

Chỉ hỏi những phần chưa có trong yêu cầu: agent, mục tiêu/instruction, nguồn dữ liệu, đầu ra mong muốn và cách dùng ở bước sau; phiên mới hay tiếp tục phiên trước; danh tính chạy; chính sách tool; giới hạn thời gian/số vòng và cách xử lý lỗi. Nếu agent cần chủ động nhắn cho nhân sự: người nhận là ai (cố định, lấy từ dữ liệu hay người đang thao tác), khi nào đáng gửi tin, mở hội thoại mới hay nối hội thoại gần nhất, bước sau làm gì khi tin không được gửi.

Khi dùng record ngữ cảnh, lấy object/field metadata bằng `$object-info` và xác minh record bằng `$object-record`. Khi cần chọn nhân sự chạy hoặc người nhận tin, dùng `$user-permission` để resolve personnel ID thực tế.

## BPMN và action payload

| Thành phần | Giá trị |
|---|---|
| `actions[].type` | `AI_AGENT` |
| `renderKey` | `AI_AGENT_TASK` |
| BPMN request | `bpmn2:sendTask` với marker `elEx:aiAgentTask` trong `extensionElements` |
| `actions[].data` | Chuỗi JSON serialize từ cấu hình bên dưới |
| Resource prefix hiển thị | `workflow_resource:list.aiAgent` |
| Đầu ra | `$action.{action_slug}.output`, kiểu `RECORD` |

Khai báo `xmlns:elEx="http://element-ex/schema"`.

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

Response có thể biểu diễn node bằng `elEx:aiAgentTask`. Kiểm tra loại action, renderKey, topology và cấu hình; không PUT chỉ để đổi cách biểu diễn XML.

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
| `runAs` | `AGENT_DEFAULT`, `PROCESS_STARTER` hoặc `PERSONNEL` kèm `personnelId`; xem [Phiên và danh tính chạy](#phiên-và-danh-tính-chạy) |
| `approvalPolicy` | `DENY` mặc định hoặc `AUTO_APPROVE` trong phạm vi được người dùng cho phép |
| `timeoutInSeconds` | Số nguyên 30–1800, mặc định 300; không gửi field `timeoutSeconds` thay thế |
| `maxTurns` | `null`/bỏ trống = theo agent; nếu đặt thì số nguyên 1–80, còn chịu trần cấu hình của agent |
| `continueOnFailure` | `false` mặc định: dừng với lỗi; `true`: ghi output lỗi và đi tiếp |
| `delivery` | Bỏ field hoặc `null` = agent không nhắn cho ai. Có thì gồm `recipientPersonnelId` (bắt buộc) và `conversationMode` `NEW`/`LATEST`; xem [Chủ động nhắn cho nhân sự](#chủ-động-nhắn-cho-nhân-sự-delivery) |

Không dùng `0` để biểu diễn timeout/số vòng vô hạn. Không cần gửi `mode`; nếu giữ payload cũ thì dùng `AGENT`. `PROMPT` chưa tạo chế độ thực thi riêng, không dùng nó để gọi mô hình trực tiếp thay cho agent. `approvalPolicy: USER_TASK` chưa được hỗ trợ; muốn người duyệt, thiết kế một User Task riêng trong process.

### ActionValue: văn bản và tham chiếu

Áp dụng cho instruction, biến ngữ cảnh, record ID và session ID. Nhân sự chạy (`runAs.personnelId`) và người nhận tin (`delivery.recipientPersonnelId`) chỉ nhận `type` `1` và `4`. Chỉ cần gửi `type` và `value`; với `type: 4` server tự bổ sung `valueDataType`, `valuePathName` khi lưu.

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
  "runAs": {"mode": "PERSONNEL", "personnelId": {"type": 4, "value": "$flow.target_record.owner"}}
}
```

- `CONTINUE`: dùng phiên của node AI Agent đã chạy trước trên đường đi hiện tại, với agent/quyền truy cập phù hợp. Kiểm tra output nguồn trước khi nối phiên. Session ID rỗng có thể làm node tạo phiên mới; ID không tồn tại có thể trả `SESSION_NOT_FOUND`. Không coi việc đi tiếp là đã giữ ngữ cảnh.
- `AGENT_DEFAULT`: dùng nhân sự mặc định được cấu hình cho agent, agent không có thì dùng người khởi tạo lượt chạy. `PROCESS_STARTER`: dùng người khởi tạo.
- `PERSONNEL`: `personnelId` là personnel ID (không phải account ID) ở một trong hai dạng. ID cố định: chuỗi `"{PERSONNEL_ID}"` hoặc `{"type": 1, "value": "{PERSONNEL_ID}"}`; đọc lại luôn là dạng ActionValue. Lấy từ dữ liệu: `{"type": 4, "value": "..."}` trỏ resource `TEXT` chứa personnel ID hoặc resource `RECORD` của Object `personnel`, ví dụ biến, lookup nhân sự của một record (`$flow.target_record.owner`) hay "Current User". Resource danh sách lấy nhân sự đầu tiên.
- "Current User" (`{"type": 4, "value": "$currentUser"}` hoặc `$currentUser.id`) ở node này là người thao tác gần nhất trên lượt chạy: người vừa submit bước User Task trước đó; chưa ai submit thì là người khởi tạo.
- Lượt chạy không có người khởi tạo (Scheduled, Triggered record/webhook, Normal Flow được gọi không kèm người dùng): `AGENT_DEFAULT` dùng nhân sự mặc định của agent, agent chưa cấu hình thì node lỗi `PERSONNEL_NOT_FOUND`; `PROCESS_STARTER` không dùng được (lưu không báo lỗi, node lỗi lúc chạy); "Current User" rỗng nếu chưa có ai submit User Task.
- `PERSONNEL` mà giá trị render rỗng (biến chưa có giá trị, record chưa có người phụ trách, "Current User" rỗng) không rơi về người khởi tạo: node lỗi `VALUE_RESOLVE_FAILED` trước khi gọi agent.
- `DENY` ngăn tool cần phê duyệt thực thi; agent vẫn có thể trả lời và kết thúc `COMPLETED`. Không suy ra rằng mọi tool đều đã chạy. Chỉ dùng `AUTO_APPROVE` khi người dùng đã cho phép tự động thực hiện các hành động liên quan; không tự bật để xử lý lỗi bị từ chối.

### Chủ động nhắn cho nhân sự (`delivery`)

```json
{
  "delivery": {
    "recipientPersonnelId": {"type": 4, "value": "$flow.target_record.owner"},
    "conversationMode": "LATEST"
  }
}
```

- Có `delivery`: trong lượt chạy, agent được gửi tin nhắn chat cho nhân sự đã chỉ định. Tin đến hội thoại AI chat của agent với nhân sự đó; người nhận được thông báo và trả lời ngay tại đó. Bỏ field hoặc `null`: không nhắn cho ai. `{}` hoặc thiếu người nhận vẫn tính là bật và bị báo lỗi khi lưu.
- `recipientPersonnelId`: cùng quy tắc với `personnelId` của `PERSONNEL` ở trên (ID cố định, resource `TEXT`/`RECORD` personnel, "Current User"). Mỗi node một người nhận.
- `conversationMode` viết hoa đúng `NEW` hoặc `LATEST`; bỏ trống được lưu thành `NEW`. `NEW`: tin luôn mở một hội thoại mới. `LATEST`: tin nối vào hội thoại gần nhất của agent với người nhận; mở hội thoại mới khi chưa có hội thoại nào, khi hội thoại đó đang bận một lượt chạy khác hoặc người nhận đã xoá nó. Field khác trong block (ví dụ tên hội thoại) không được lưu.
- `delivery` độc lập với `session`: `session` là ngữ cảnh của lượt chạy tại node, `conversationMode` là hội thoại của người nhận.
- Agent tự viết tin và tự quyết định có gửi hay không: nêu trong `instruction` người nhận cần biết gì và khi nào đáng gửi tin. Câu trả lời cuối (`output.text`) và `output.result` vẫn chỉ trả về cho Process, không tự thành tin nhắn.
- Người nhận phải thuộc Workspace, được quyền dùng agent và có seat AI Agent. Hệ thống kiểm tra khi node bắt đầu gọi agent; không đạt thì node lỗi (mục [Lỗi và nhánh sau AI Agent](#lỗi-và-nhánh-sau-ai-agent)), agent không chạy và không có tin nào được gửi.
- Hội thoại của người nhận tách khỏi lượt chạy: khi người nhận trả lời, agent chạy bằng danh tính và quyền của người nhận, không phải danh tính `runAs` của node.
- Số tin một agent gửi cho một nhân sự trong một lượt chạy và trong một ngày có giới hạn; tin vượt giới hạn không được gửi (`deliveryStatus: BLOCKED`, `deliveryErrorCode: RECIPIENT_RATE_LIMITED`). Node nằm trong Loop hoặc Process chạy theo lịch dày: thiết kế điều kiện để không nhắn lặp cùng một việc.
- Lượt chạy thật gửi tin thật cho người thật, kể cả khi kiểm thử: dùng người nhận đã biết trước việc này.

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

Prefix `absoluteSlug` là `$action.{slug}`; prefix `absolutePath` là `workflow_resource:list.aiAgent / {Tên node}`. Children cố định của output (gồm bốn child `delivery*`) do API cung cấp khi đọc lại, kể cả khi node không có `delivery`; cấu trúc tùy chỉnh gửi qua `data.resultDataType`, không tự thêm Object Type ID cho output.

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
| `output.deliveryStatus` | TEXT | Kết quả gửi tin của node có `delivery`: `SENT` (ít nhất một tin đã tới người nhận), `NOT_SENT` (agent không gửi), `BLOCKED` (bị chặn), `FAILED` (gửi lỗi). `null` khi node không có `delivery` hoặc agent không chạy tới kết quả (lỗi khởi chạy, timeout) |
| `output.deliveryErrorCode` | TEXT | Mã lỗi khi `BLOCKED`/`FAILED`, ví dụ `RECIPIENT_RATE_LIMITED`; `null` trong các trường hợp khác |
| `output.deliveryChatSessionId`, `output.deliveryConversationId` | TEXT | Phiên chat và hội thoại của người nhận khi `SENT`; dùng để đối chiếu, `null` khi không gửi |

Output khi mới nhận chạy chưa phải kết quả cuối. Các chỉ số sử dụng có thể null nếu lỗi xảy ra trước khi chạy; không đổi null thành 0 rồi coi đó là số đo thật.

`output.status` không đổi theo kết quả gửi tin: lượt chạy agent vẫn `COMPLETED` khi agent không gửi hoặc tin không gửi được. Bước sau cần biết tin đã tới người nhận hay chưa thì rẽ nhánh theo `output.deliveryStatus` (mục [Lỗi và nhánh sau AI Agent](#lỗi-và-nhánh-sau-ai-agent)).

Khi một resource được dùng trong instruction/context/session, nhân sự chạy hoặc người nhận tin, thêm `resourcesUsedIn` theo convention chung với `actionType: AI_AGENT`, `parentTable: action`, ID và slug của node tiêu thụ. Với lookup child, bổ sung `externalResourcesUsedIn` theo metadata đã resolve. Với output được node sau tiêu thụ, tracking trỏ tới node sau đó. Các reference phải có nguồn và có giá trị trước khi AI Agent chạy.

## Validate khi lưu

Lưu Process vẫn trả `r: 0` khi cấu hình node sai: lỗi nằm trong `meta.errors[]` (mỗi lỗi có `code`, `slug`, `internalMessage`, `fieldKey`, `detail` tiếng Anh, `nodeId`, `actionName`), `msg` ghi `Data in action is invalid` và Process `isValid: false`, không kích hoạt được.

```json
{"code": 77, "slug": "messages.aiAgentDeliveryInvalid", "internalMessage": "AI Agent delivery is invalid", "fieldKey": "delivery.conversationMode", "detail": "conversationMode must be NEW or LATEST", "nodeId": "{AI_NODE_ID}", "actionName": "Nhắc việc"}
```

| `code` | Tên | `fieldKey` | Khi nào |
|---:|---|---|---|
| 65 | `AI_AGENT_RUN_AS_INVALID` | `runAs.personnelId` | `PERSONNEL` thiếu `personnelId`; resource không phải `TEXT`/`RECORD` của Object `personnel` |
| 77 | `AI_AGENT_DELIVERY_INVALID` | `delivery.recipientPersonnelId` | Có `delivery` mà thiếu hoặc rỗng người nhận; ID cố định không thuộc Workspace; resource không tồn tại hoặc không phải `TEXT`/`RECORD` của Object `personnel`; ActionValue khác `type` 1/4 |
| 77 | `AI_AGENT_DELIVERY_INVALID` | `delivery.conversationMode` | Giá trị khác `NEW`, `LATEST` (kể cả viết thường) |

Lúc lưu chỉ kiểm tra được cấu hình: quyền dùng agent, seat của người nhận và giá trị thật của resource được kiểm tra khi chạy.

## Lỗi và nhánh sau AI Agent

- Node chờ đến khi agent kết thúc hoặc hết thời gian. Không thêm Wait riêng để đợi AI Agent.
- `continueOnFailure: false`: lỗi khởi chạy hoặc trạng thái cuối khác `COMPLETED` làm lượt chạy dừng với lỗi; gateway sau node không có cơ hội xử lý lỗi đó.
- `continueOnFailure: true`: cả lỗi khởi chạy và lỗi lúc thực thi được ghi vào output rồi đi tiếp. Đặt gateway kiểm tra `$action.{slug}.output.status == "COMPLETED"` trước nhánh nghiệp vụ; nhánh mặc định chuyển sang xử lý lỗi/nhân sự xem lại.
- Timeout có thể mất thêm một khoảng ngắn để cập nhật trạng thái. Sau timeout/huỷ/lỗi, không mặc định rằng các tool đã chạy trước đó được hoàn tác. Kiểm tra dữ liệu thực tế trước khi chạy lại để tránh tác động trùng.
- Khi gặp `AGENT_NOT_FOUND`/`AGENT_INACTIVE`, kiểm tra agent đã chọn; `VALUE_RESOLVE_FAILED` kiểm tra instruction/reference/danh tính chạy/người nhận; `PERSONNEL_NOT_FOUND` kiểm tra nhân sự chạy (lượt chạy không có người khởi tạo thì agent phải có nhân sự mặc định); `SESSION_NOT_FOUND` kiểm tra phiên; `QUOTA_EXCEEDED` kiểm tra hạn mức; `RESULT_SCHEMA_MISMATCH` kiểm tra kết quả/schema. Giữ nguyên mã lỗi thực nhận, không tự ánh xạ sang mã số chưa được công bố.

Lỗi của `delivery` trước khi agent chạy là lỗi khởi chạy: `output.status = FAILED`, bốn `delivery*` đều `null`, không có tin nào được gửi, xử lý theo `continueOnFailure` như trên.

| `output.errorCode` | Khi nào | Xử lý |
|---|---|---|
| `VALUE_RESOLVE_FAILED` (`errorMessage` chứa `RECIPIENT_NOT_FOUND`) | Người nhận render rỗng: biến chưa có giá trị, record chưa có người phụ trách, "Current User" rỗng. Agent chưa được gọi | Bảo đảm nguồn có giá trị trước node hoặc rẽ nhánh khi rỗng |
| `RECIPIENT_NOT_FOUND` | Không có nhân sự với ID đó trong Workspace | Kiểm tra nguồn personnel ID |
| `RECIPIENT_ACCESS_DENIED` | Người nhận không được quyền dùng agent | Cấp quyền dùng agent cho người nhận hoặc đổi người nhận |
| `RECIPIENT_AI_SEAT_REQUIRED` | Người nhận chưa có seat AI Agent | Gán seat hoặc đổi người nhận |
| `DELIVERY_UNAVAILABLE` | Lỗi tạm thời khi kiểm tra người nhận | Chạy lại sau, không đổi cấu hình |

Rẽ nhánh theo kết quả gửi tin:

- So sánh `output.deliveryStatus` khi giá trị `null` làm lượt chạy dừng tại gateway với `CAN_NOT_COMPARE_BECAUSE_RESOURCE_VALUE_IS_NULL`. Với `continueOnFailure: true`, đặt outcome `$action.{slug}.output.status != "COMPLETED"` (nhánh lỗi) trước outcome `$action.{slug}.output.deliveryStatus == "SENT"`: outcome được xét theo `outcomeOrder`, nhánh khớp đầu tiên được chọn nên phép so sánh sau không chạy với giá trị `null`. Mẫu: `samples/sample_ai_agent_proactive_chat.json`.
- Nhánh mặc định sau hai outcome trên nhận `NOT_SENT`, `BLOCKED`, `FAILED`: agent chạy xong nhưng không có tin nào tới người nhận. Cần phân biệt thì thêm outcome theo `deliveryStatus` hoặc `deliveryErrorCode`; không coi `NOT_SENT` là lỗi nếu instruction cho phép agent không gửi.
- Node `TIMEOUT`: `deliveryStatus` rỗng kể cả khi agent đã gửi tin trước lúc hết giờ. Không coi rỗng là chưa gửi và không tự nhắn lại ở nhánh lỗi; đặt `timeoutInSeconds` đủ rộng cho việc agent cần làm.
- Không mặc định tin đã gửi được thu hồi khi bước sau lỗi hoặc lượt chạy bị huỷ. Đối chiếu `deliveryStatus` và người nhận của lượt trước rồi mới chạy lại để tránh nhắn trùng.

## Xác minh trước và sau khi lưu

1. Kiểm tra agent hoạt động, danh tính chạy, scope công cụ và mọi reference. Validate ActionValue, key/slug, timeout/maxTurns, session ID nếu `CONTINUE`; serialize `action.data` đúng một lần. Có `delivery`: xác nhận người nhận thuộc Workspace, được quyền dùng agent và có seat AI Agent.
2. Kiểm tra XML/ID/diagram theo `SKILL.md`; dùng mẫu `samples/sample_ai_agent.json` (chỉ gọi agent) hoặc `samples/sample_ai_agent_proactive_chat.json` (có `delivery` và gateway theo kết quả gửi tin) làm cấu trúc khởi đầu. Sample chỉ minh họa, không thay cho kiểm thử trên Workspace đích; phải thay `{AGENT_ID}` bằng ID thật, sinh lại ID process/node/resource khi tạo mới.
3. Tạo qua Public Process API trong `api-process-builder.md`, GET-back và đối chiếu `AI_AGENT`, `AI_AGENT_TASK`, agent ID, instruction, session, runAs, policy, giới hạn, `continueOnFailure`, `delivery` (người nhận, `conversationMode`), ba resources chuẩn và children output (có bốn child `delivery*`); `meta.errors` không có mã `65`/`77`. `data` trả về string thì parse trước khi so sánh. Nếu có schema, kiểm tra cả `action.data.resultDataType.children` và resource `output.result.children`.
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
| Chủ động nhắn nhân sự (`delivery`) | GET-back còn `delivery`; đúng instance có `deliveryStatus = SENT`, `deliveryConversationId` có giá trị và nhánh "đã gửi" chạy; người nhận xác nhận thấy tin trong hội thoại AI chat với agent. Người nhận là biến hoặc "Current User": đối chiếu đúng người mong đợi |
| Agent không gửi | Input không có việc cần báo: `output.status = COMPLETED`, `deliveryStatus = NOT_SENT`, nhánh "không gửi" chạy, người nhận không nhận tin |
| Người nhận không hợp lệ | Người nhận rỗng hoặc không đủ quyền/seat: `output.status = FAILED` với đúng `errorCode`, `deliveryStatus` rỗng, không có tin nào được gửi; lượt chạy dừng hoặc đi nhánh lỗi theo `continueOnFailure`, không dừng tại gateway vì so sánh giá trị rỗng |

Chỉ kiểm thử trường hợp cần cho yêu cầu và nằm trong phạm vi đã được phép. Lượt chạy có `delivery` gửi tin thật: dùng người nhận test đã biết trước, nội dung ghi rõ là dữ liệu kiểm thử, không chạy lặp. Báo process/instance, `runId`, trạng thái, output/hiệu ứng đã đối chiếu; dùng `PARTIAL` hoặc `BLOCKED_ENV` nếu chưa thể quan sát đầy đủ. Không đưa prompt chứa dữ liệu nhạy cảm hoặc secret vào báo cáo.
