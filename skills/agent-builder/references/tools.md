# Danh mục và cấu hình Tool

Đọc [API cấu hình](config-api.md) trước khi gửi request. Tool tạo/cập nhật qua thao tác 40/41, List qua 43; `config` luôn là chuỗi JSON. List hỗ trợ `ids`, `keyword`, `types`, `categories`, `requiresApproval`, `status`, phân trang và sắp xếp.

## Chọn category và type

Các lựa chọn dưới đây tương ứng form tạo Tool. Không coi mọi tên công cụ có thể xuất hiện trong chat là một loại Tool cho phép tự tạo; các công cụ như `activate_skill` do Agent cung cấp khi có Skill mở rộng.

| `category` | `type` | Chức năng và cấu hình |
|---|---|---|
| `RECORD` | `CREATE`, `GET`, `UPDATE`, `DELETE`, `LIST` | Thao tác bản ghi của các Object đã chọn. Có `app`, `object_slug` hoặc `object_slugs` |
| `ACTIVITY` | `CREATE`, `GET`, `UPDATE`, `DELETE`, `LIST` | Thao tác công việc/hoạt động. `app` cung cấp ngữ cảnh App khi tạo/cập nhật; không coi đó là bộ lọc bảo mật cho mọi lệnh đọc |
| `PROCESS` | Xem bảng dưới | Tìm Process, bắt đầu và quản lý lượt chạy, xem/hoàn thành User Task; cấu hình cơ bản `{}` |
| `HTTP` | `HTTP_REQUEST` | Gọi API HTTPS với URL, method và xác thực đã cấu hình |
| `WEB_SEARCH` | `PERPLEXITY`, `GEMINI` | Tìm thông tin trên web; `systemInstruction` hướng dẫn phạm vi tìm kiếm và cách tổng hợp |
| `KNOWLEDGE_BASE` | `QDRANT` | Tra cứu tài liệu đã index trong Data của Workspace; cấu hình danh mục và ngưỡng truy xuất |
| `DEEP_RESEARCH` | `DEEP_RESEARCH` | Nghiên cứu/tổng hợp sâu dựa trên công cụ kiến thức; cần Tool KNOWLEDGE_BASE khả dụng cùng lúc |
| `CUSTOM_MODULE` | `INVOKE_ACTION` | Gọi một Custom Module Action: logic riêng của Workspace viết trong Custom Backend Module, có schema input/output. Config `{"projectSlug","actionKey"}`; xem [CUSTOM_MODULE](#custom_module) |
| `PERSONNEL_CHAT` | `SEND_MESSAGE` | Agent chủ động gửi tin nhắn chat cho một nhân sự, vào hội thoại chat AI của người đó với Agent. Config `{"conversationMode"}`; xem [PERSONNEL_CHAT](#personnel_chat) |

`RECORD`, `ACTIVITY`, `PROCESS` nhận `type` là mảng để chọn nhiều thao tác; các category còn lại dùng một chuỗi. Khi tái sử dụng Tool, giữ nguyên định dạng hợp lệ được trả về. Không trộn type của các category trong một Tool.

| Type PROCESS | Ý nghĩa |
|---|---|
| `SEARCH` | Tìm Process phù hợp |
| `START_INSTANCE` | Bắt đầu luồng Manual có thể chạy bởi người dùng |
| `LIST_INSTANCES`, `VIEW_INSTANCE` | Liệt kê/xem lượt chạy |
| `PAUSE_INSTANCE`, `RESUME_INSTANCE` | Tạm dừng/tiếp tục lượt chạy |
| `CANCEL_INSTANCE`, `DELETE_INSTANCE` | Hủy/xóa lượt chạy, khác nhau về tác động dữ liệu |
| `MY_PENDING_TASKS`, `MY_COMPLETED_TASKS` | Công việc đang chờ/đã hoàn thành của nhân sự thực thi |
| `VIEW_USER_TASK`, `SUBMIT_USER_TASK` | Xem và gửi kết quả User Task |

Các lệnh này không tạo/sửa định nghĩa Process. Khi cần thiết kế quy trình, dùng [$process-creator](../../process-creator/SKILL.md).

Nếu Workspace trả Tool có category/type khác bảng, chỉ tái sử dụng sau khi xác minh mô tả, schema đầu vào và hoạt động qua metadata API/tài liệu API tương ứng. Nếu chưa đủ contract, báo người dùng cung cấp trước khi tạo hoặc sử dụng; không tự tạo payload hoặc mở UI để dò.

## RECORD và ACTIVITY

Một Object:

```json
{"app":"{app-slug}","object_slug":"{object-slug}"}
```

Nhiều Object:

```json
{"app":"{app-slug}","object_slugs":["{object-slug-a}","{object-slug-b}"]}
```

- Resolve App/Object bằng metadata và các skill tương ứng trước khi ghi.
- Ưu tiên chọn Object tường minh. Khi có `object_slugs`, trường này được ưu tiên kể cả mảng rỗng. Mảng rỗng không có nghĩa “tất cả”.
- Nếu chỉ đặt `app`, phạm vi có thể dựa vào Object truy cập được qua App; nó không thay thế quyền record/field. Không dùng config rỗng để mong cấp toàn Workspace.
- Công cụ RECORD có thể được gộp theo thao tác khi chạy. `slug` cấu hình không nhất thiết là tên công cụ hiển thị trong chat; kiểm tra tool thực tế và phạm vi Object, không chỉ so tên.
- ACTIVITY dùng `{"app":"{app-slug}"}`. Không thay thế thao tác Activity chuyên biệt bằng RECORD nếu nghiệp vụ cần hành vi Activity.

Ví dụ Tool chỉ đọc, thao tác 40:

```json
{
  "name":"Tra cứu phiếu hỗ trợ",
  "slug":"support_ticket_read",
  "description":"Tìm và xem phiếu hỗ trợ trong phạm vi quyền của nhân sự thực thi; không sửa hoặc xóa phiếu.",
  "category":"RECORD",
  "type":["LIST","GET"],
  "config":"{\"app\":\"{app-slug}\",\"object_slug\":\"{ticket-object-slug}\"}",
  "requiresApproval":false,
  "status":true,
  "accessControls":[{"functions":["VIEW","EXECUTE"],"type":"role","option":2,"items":["{operator-role-id}"]}]
}
```

Tạo Tool ghi riêng nếu cần xác nhận. Tránh nhiều Tool cùng loại ACTIVITY/PROCESS với cấu hình hoặc yêu cầu duyệt mâu thuẫn trong cùng Agent; không giả định chúng chạy thành các bản độc lập. Với RECORD cũng kiểm tra lại hành vi khi nhiều Skill cấp cùng thao tác.

## HTTP

Config dưới đây là JSON **trước khi serialize** vào chuỗi `config`:

```json
{"url":"https://api.example.com/catalog","method":"GET","auth":{"type":"none"}}
```

Form hỗ trợ các cơ chế xác thực:

| `auth.type` | Trường bổ sung |
|---|---|
| `none` | Không có |
| `bearer_token` | `value` |
| `api_key_header` | `header_name`, `value` |
| `query_param` | `param_name`, `value` |
| `basic` | `username`, `password` |
| `oauth2_client_credentials` | `token_url`, `client_id`, `client_secret` |

Điền secret bằng kênh credential được phép; không đưa vào mô tả, Skill, prompt hay file public. Nếu sửa Tool dùng chung, không thay toàn bộ `config` bằng một mẫu làm mất cấu hình/credential hiện hữu. Kiểm tra URL, method và API đích trước khi gọi, không cho phép người chat tự đổi đích gửi credential.

**Giới hạn cần biết:** contract tạo/cập nhật Tool HTTP hiện nêu trong tài liệu này không có trường khai báo parameter schema. Chỉ có `description` hoặc nhét `parameters` tùy ý vào payload không bảo đảm Agent có schema đầu vào. Với HTTP cần tham số động, ưu tiên Tool đã có schema đúng; nếu cần tạo schema mới, báo người dùng cung cấp [contract schema HTTP Tool](api-gaps.md). Không chuyển sang trình duyệt hoặc tự thêm trường không được tài liệu hỗ trợ. Không tuyên bố tích hợp có tham số đã hoàn tất khi mới lưu URL/auth. HTTP không tham số vẫn phải test request và phản hồi thực tế. Khi logic cần tham số thuộc về Workspace (tính toán, kiểm tra, đọc/ghi dữ liệu theo quy tắc riêng, gọi hệ thống ngoài bằng secret của Workspace), dùng Tool [CUSTOM_MODULE](#custom_module): action khai báo schema input chặt và Agent nhận schema đó.

## Web search và kiến thức

WEB_SEARCH config:

```json
{"systemInstruction":"Tìm nguồn chính thức liên quan câu hỏi; phân biệt thông tin đã xác minh với suy luận và trả đường dẫn nguồn."}
```

KNOWLEDGE_BASE config gợi ý theo form:

```json
{
  "allowedCategories":["{data-library-slug}"],
  "rerankEnabled":true,
  "rerankCandidateTopK":40,
  "rerankFinalTopK":5,
  "rerankScoreThreshold":0.2,
  "noRerankMinScore":0.5,
  "topK":5
}
```

`allowedCategories` dùng **slug danh mục**, không dùng ID danh mục/file. Rỗng hoặc thiếu trường này nghĩa là không giới hạn category; một phần tử áp dụng trực tiếp, nhiều phần tử cho phép chọn trong tập đó. Chọn tường minh cho Agent CSKH. Không cấu hình tên kho lưu trữ để đổi Workspace; dữ liệu tra cứu thuộc Workspace của phiên.

Rerank sắp xếp lại ứng viên; `rerankCandidateTopK` là lượng ứng viên, `rerankFinalTopK` là số kết quả giữ lại. Ngưỡng cao hơn có thể giảm kết quả không liên quan nhưng cũng bỏ sót tài liệu. Test với câu hỏi biết trước đáp án trước khi chỉnh ngưỡng. Các giá trị trên là điểm khởi đầu, không phải bằng chứng truy xuất đạt chất lượng.

DEEP_RESEARCH dùng config cơ bản `{}`. Gắn cùng KNOWLEDGE_BASE vào Skill CORE khi cần sử dụng ổn định ngay từ đầu; kiểm tra Tool khả dụng trước khi test. Chỉ bật khi cần nghiên cứu sâu và chấp nhận thời gian xử lý dài hơn. Nhu cầu tra cứu tài liệu thông thường dùng KNOWLEDGE_BASE. Tránh nhiều Tool KNOWLEDGE_BASE cùng type nhưng phạm vi khác nhau trong cùng Agent; dùng một cấu hình danh mục rõ ràng, kiểm thử lại sau khi thêm Skill.

## CUSTOM_MODULE

Tool gọi một **Custom Module Action**: thao tác ngắn khai báo bằng `defineAction` trong Custom Backend Module của Workspace, có schema input/output. Dùng khi Agent cần logic riêng của Workspace (tính giá, chấm điểm, kiểm tra điều kiện, đọc/ghi dữ liệu theo quy tắc nghiệp vụ, gọi hệ thống ngoài bằng secret của Workspace) mà RECORD/PROCESS/HTTP không đáp ứng. Viết, sửa và publish action thuộc [$cogover-custom-module](../../cogover-custom-module/SKILL.md); mục này chỉ tạo Tool.

### Chọn action

Action phải thuộc version **đang active** của module và có `exposeTo` chứa `"agent"`. Liệt kê bằng cùng phiên Web App (mọi thành viên đang hoạt động đọc được):

```http
GET https://{workspace-domain}/api/v1/ts-projects/actions?consumer=agent
x-req-type: 9
x-req-service: 4
```

Route chi tiết `GET /api/v1/ts-projects/actions/{projectSlug}/{actionKey}?consumer=agent` trả `data.action` hoặc `404` `ACTION_NOT_FOUND`. Mỗi action có `projectSlug`, `key`, `label`, `description`, `effect` (`read` chỉ đọc, `write` được ghi), `timeoutMs`, `inputSchema`, `outputSchema`; contract đầy đủ ở mục [Custom Module Action](../../cogover-custom-module/references/custom-backend-module-api-reference.md#custom-module-action-1) của Backend API Reference. Không đoán `projectSlug`/`actionKey`; action cần chưa có hoặc thiếu input thì chuyển yêu cầu sang `$cogover-custom-module`.

### Tạo Tool

Thao tác 40, `config` là chuỗi JSON:

```json
{
  "name":"Chấm điểm lead",
  "slug":"score_lead_tool",
  "description":"",
  "category":"CUSTOM_MODULE",
  "type":"INVOKE_ACTION",
  "config":"{\"projectSlug\":\"{project-slug}\",\"actionKey\":\"{action-key}\"}",
  "status":true,
  "accessControls":[{"functions":["VIEW","EXECUTE"],"type":"role","option":2,"items":["{operator-role-id}"]}]
}
```

- `projectSlug` khớp `^[A-Za-z_][A-Za-z0-9_]{0,99}$`, `actionKey` khớp `^[a-z][a-z0-9_]{0,63}$`; thiếu key trả `4020`, sai định dạng trả `4021`; key lạ bị bỏ.
- Server kiểm tra action khi tạo, hoặc khi sửa/nhân bản đổi action hay category, rồi lưu `config` là `{"projectSlug","actionKey","effect"}`: `effect` do server đặt theo action (giá trị client gửi bị bỏ). Đọc lại config bằng thao tác 43.
- Không dùng `parameters`: agent nhận `inputSchema` của action lúc chạy, gồm cả `description` của từng property. Chất lượng gọi Tool phụ thuộc mô tả action và các đoạn `describe` trong schema; mô tả chưa đủ thì sửa ở module.
- `description` của Tool không bắt buộc với category này. Để trống thì Agent đọc mô tả của action; chỉ điền khi cần giới hạn thêm cách dùng trong Agent này, không lặp lại hay mâu thuẫn với mô tả action. Tên công cụ Agent thấy lấy từ `slug` của Tool.
- `requiresApproval` không gửi: `true` nếu action có `effect: "write"`, `false` nếu `"read"`. Gửi giá trị thì dùng giá trị đó; tắt phê duyệt cho action ghi chỉ khi người dùng đã cho phép Agent tự thực hiện thao tác đó. Nếu action đổi từ `read` sang `write` sau khi lưu Tool, Agent vẫn bắt phê duyệt dù `requiresApproval: false` (chậm nhất khoảng một phút).

| Lỗi khi lưu | HTTP | Body | Xử lý |
|---|---:|---|---|
| Action không có, module không có version active, hoặc action không mở cho AI Agent | 400 | `{"r":4047,"data":{"errorCode":"CUSTOM_MODULE_ACTION_NOT_FOUND"}}` | Kiểm tra danh mục `consumer=agent`; sửa `exposeTo`/publish/activate ở module |
| Không kiểm tra được action (dịch vụ module tạm thời không sẵn sàng) | 503 | `{"r":503,"data":{"errorCode":"CUSTOM_MODULE_ACTION_UNAVAILABLE"}}` | Thử lại sau; không đổi cấu hình |

Cả hai trường hợp Tool không được lưu. Sửa tên, mô tả, phê duyệt, trạng thái mà giữ action không kiểm tra lại action: Tool trỏ action đã bị gỡ vẫn lưu được, nên đối chiếu danh mục trước khi bàn giao.

### Khi chạy

- Mỗi lần Agent gọi Tool là một lần chạy action (tối đa `timeoutMs` của action, không quá 8 giây). Input do mô hình sinh luôn được kiểm tra theo `inputSchema` trước khi action chạy.
- Action chạy dưới danh tính mà Agent đang dùng: nhân sự `runAsPersonnelId` của Agent; Agent nội bộ (`runAsPersonnelId: null`) dùng người đang chat; lượt chạy nền theo danh tính đã chọn cho lượt chạy đó. Agent CSKH chạy bằng một nhân sự cố định cho mọi người chat dùng quyền của nhân sự đó; module nhận thêm ID nhân sự của người đang chat hoặc người khởi chạy lượt chạy (`initiatorPersonnelId`) để tự kiểm tra khi action chỉ được làm điều người đó được phép. Quyết định này thuộc thiết kế module, không thay bằng System Prompt.
- Kết quả trả Agent: `COMPLETED` là JSON output của action; `FAILED` là lỗi `{"error":{"code","message","details"}}` với `code` như `INPUT_INVALID` (kèm `details.errors[]` theo đường dẫn để Agent sửa input), `OUTPUT_INVALID`, `SCRIPT_ERROR`, `TIMEOUT`, `RATE_LIMITED`, `PERMISSION_DENIED`; bị từ chối trước khi chạy trả mã như `ACTION_NOT_FOUND`, `ACTION_NOT_EXPOSED`, `ACTOR_NOT_ALLOWED`, `MAX_HOP_EXCEEDED`. Message luôn là tiếng Anh cố định theo mã, không chứa message riêng của handler; kết quả dự kiến (không tìm thấy, không đủ điều kiện) nên nằm trong output để Agent trả lời đúng.
- Không xác định được danh tính chạy thì Tool trả lỗi `ACTOR_NOT_RESOLVED`. Dịch vụ module không trả lời sau khi đã tự gửi lại thì Tool trả `RUNTIME_UNAVAILABLE` hoặc `IN_PROGRESS` (chưa biết kết quả; kiểm tra dữ liệu trước khi cho gọi lại).
- Action bị gỡ, không còn mở cho AI Agent hoặc module bị deactivate thì Tool không được đưa vào Agent ở hội thoại mới và lời gọi đang dở trả `ACTION_NOT_FOUND`. Đổi schema action làm thay đổi cách Agent điền input: chạy lại kiểm thử sau mỗi version module có thay đổi action.

### Kiểm thử

Gắn Tool vào Skill, cập nhật Agent, tạo hội thoại mới theo [chat và WebSocket](chat-testing.md): câu hỏi cần action phải làm Agent gọi đúng Tool với input hợp lệ và trả lời dựa trên output; câu hỏi thiếu dữ liệu làm Agent hỏi lại thay vì gọi với giá trị bịa. Action `write` cần phê duyệt: nhận `TOOL_APPROVAL_REQUEST`, từ chối không tạo thay đổi, chấp thuận tạo đúng thay đổi (đọc lại bằng [$object-record](../../object-record/SKILL.md)). Module kiểm tra theo người đang chat thì test bằng hai người có quyền khác nhau.

### Agent do Custom Backend Module khởi chạy

Module có thể chạy Agent nền bằng `agents.start` (không phải Tool). Khi thiết kế Agent cho cách gọi này: người dùng mà module chạy thay phải có quyền `EXECUTE` trên Agent; lời gọi không có người dùng hoặc `runAs: "agent"` cần Agent có `runAsPersonnelId`; `approvalPolicy` mặc định từ chối mọi Tool cần phê duyệt, nên Tool ghi mà lượt chạy nền phải dùng cần được thiết kế lại hoặc module phải được phép `autoApprove`. Agent khởi chạy lẫn nhau qua module được lồng tối đa 3 cấp. Code và identity policy của module thuộc `$cogover-custom-module`.

Lượt chạy nền có thể chỉ định sẵn người nhận tin: `deliverTo` của `agents.start` (SDK từ `0.16.0`, xem `$cogover-custom-module`) hoặc cấu hình người nhận tin chủ động trên node AI Agent của Process (xem [$process-creator](../../process-creator/SKILL.md)). Khi đó Agent có một công cụ gửi tin tới **đúng người nhận đã chỉ định** và tự quyết định có gửi hay không; Agent **không cần** gắn Tool `PERSONNEL_CHAT`. Người nhận vẫn phải đạt điều kiện ở mục [PERSONNEL_CHAT](#personnel_chat) (tồn tại trong Workspace, quyền `EXECUTE` trên Agent, seat AI Agent), không đạt thì lượt chạy bị từ chối ngay khi khởi chạy. Chỉ gắn Tool `PERSONNEL_CHAT` khi Agent phải tự chọn người nhận.

## PERSONNEL_CHAT

Tool cho Agent **chủ động nhắn tin chat cho một nhân sự**: tin đến hội thoại chat AI của người đó với chính Agent này, người nhận được thông báo và trả lời ngay tại đó, không cần họ nhắn trước. Dùng khi Agent tự chọn người nhận trong lúc làm việc: chuyển lời theo yêu cầu của người đang chat, nhắc việc, cảnh báo cho người phụ trách. Người nhận đã được module hoặc Process chỉ định sẵn thì không cần Tool này, xem [Agent do Custom Backend Module khởi chạy](#agent-do-custom-backend-module-khởi-chạy).

### Tạo Tool

Thao tác 40, `config` là chuỗi JSON:

```json
{
  "name":"Nhắn tin cho nhân sự",
  "slug":"message_personnel",
  "description":"Nhắn cho nhân sự phụ trách khi phiếu hỗ trợ quá hạn xử lý, hoặc khi người dùng nhờ chuyển lời tới một nhân sự cụ thể. Mỗi việc chỉ nhắn một lần.",
  "category":"PERSONNEL_CHAT",
  "type":"SEND_MESSAGE",
  "config":"{\"conversationMode\":\"NEW\"}",
  "requiresApproval":false,
  "status":true,
  "accessControls":[{"functions":["VIEW","EXECUTE"],"type":"role","option":2,"items":["{operator-role-id}"]}]
}
```

- `conversationMode` bắt buộc, phân biệt hoa thường: `NEW` mở hội thoại mới cho mỗi tin; `LATEST` nối tin vào hội thoại gần nhất của Agent với người nhận. Thiếu key trả `4020`, giá trị khác trả `4021`; key lạ bị bỏ. Người cấu hình chọn chế độ, mô hình không chọn và không đổi được lúc chạy.
- `type` là một chuỗi; type khác trả `4019`. Không dùng `parameters`: Agent nhận schema input cố định ở mục Khi chạy.
- `description` bắt buộc (thiếu trả `4012`) và được đưa cho Agent như hướng dẫn của người cấu hình về **khi nào nên nhắn**: ghi điều kiện gửi, người nhận phù hợp và điều không được làm.
- `requiresApproval` do người cấu hình chọn, không gửi thì `false`. Bật khi mỗi tin cần người đang chat duyệt trước khi gửi.
- Tên công cụ Agent thấy luôn là `send_chat_to_personnel`, không lấy theo `slug`. Agent có nhiều Tool loại này thì chỉ Tool đầu tiên đang bật được dùng: mỗi Agent chỉ nên gắn một Tool.

### Khi chạy

Input do mô hình điền:

| Trường | Ý nghĩa |
|---|---|
| `personnel_id` | Bắt buộc. ID bản ghi nhân sự của người nhận |
| `message` | Bắt buộc. Nội dung tin, tối đa 4.000 ký tự, cho phép Markdown |
| `title` | Tên hội thoại khi mở hội thoại mới, tối đa 80 ký tự; bỏ trống thì lấy 40 ký tự đầu của tin |
| `handoff_note` | Ghi chú Agent để lại cho chính nó trong hội thoại của người nhận (người nhận không thấy). Chỉ có tác dụng ở lượt chạy nền; bị bỏ khi có người đang chat |

- **Người nhận:** Agent tự chọn và cần đúng ID nhân sự. ID đến từ ngữ cảnh (người chat nêu, `${system.currentUserInfo}`, trường nhân sự của bản ghi Agent đọc được); khi chỉ biết tên hoặc email, Agent tra bằng Tool đọc dữ liệu nhân sự đã gắn. Không có nguồn ID thì gắn thêm Tool đọc phù hợp và ghi cách tra trong `fullInstructions`, không để Agent đoán ID.
- **Điều kiện người nhận:** tồn tại trong Workspace, có quyền `EXECUTE` trên Agent và có seat AI Agent. Không đạt thì công cụ trả lỗi cho Agent, không mở hội thoại và không gửi gì. Trong lượt chat, Agent chỉ nhận một lý do chung (ID sai hoặc người đó chưa được thiết lập để dùng Agent), nên người chat không dò được nhân sự nào tồn tại hay có quyền.
- **Hội thoại:** `LATEST` vẫn mở hội thoại mới khi Agent và người nhận chưa có hội thoại, người nhận đã xoá hội thoại gần nhất, hội thoại đó đang chạy một lượt khác hoặc có thêm người khác tham gia.
- **Tin gửi từ một lượt chat** mở đầu bằng dòng “Tin nhắn gửi theo yêu cầu của {tên người đang chat}:” (Workspace tiếng Anh: “Sent at the request of {name}:”), để người nhận biết ai nhờ gửi. Tin từ lượt chạy nền không có dòng này.
- **Người nhận trả lời** ngay trong hội thoại đó như một cuộc chat AI của chính họ: Agent chạy theo danh tính áp dụng cho người nhận (Agent nội bộ dùng quyền của người nhận), chỉ biết tin đã gửi và ai nhờ gửi, không mang nội dung cuộc chat hay quyền của người yêu cầu.
- **Giới hạn mặc định** (ngày tính theo UTC): một Agent gửi tối đa 30 tin mỗi ngày cho một nhân sự; một người được nhờ Agent gửi tối đa 30 tin mỗi ngày trong các lượt chat của mình, tính chung mọi Agent và người nhận; một lượt chạy nền gửi tối đa 20 tin, trong đó tối đa 3 tin cho một nhân sự. Vượt giới hạn thì tin không được gửi và công cụ báo `RECIPIENT_RATE_LIMITED`.
- **Hội thoại với khách hàng:** Agent đang trả lời khách trên kênh chat không có công cụ này, dù Tool đã gắn.
- **Phê duyệt:** với `requiresApproval: true`, người đang chat nhận yêu cầu duyệt cho từng tin, gồm ID người nhận, tên hội thoại (nếu có) và toàn bộ nội dung tin; từ chối thì không gửi. Lượt chạy nền không có người duyệt nên tin bị từ chối theo `approvalPolicy` mặc định.
- **Tắt Tool hoặc đổi `conversationMode`** có hiệu lực ở lần gọi kế tiếp, kể cả trong hội thoại đang mở: hội thoại mới không còn công cụ, hội thoại đang mở nhận lỗi công cụ đã bị tắt. Thay đổi khác (mô tả, phê duyệt) kiểm thử trên hội thoại mới.

### Kiểm thử

Gắn Tool vào Skill, cập nhật Agent, tạo hội thoại mới theo [chat và WebSocket](chat-testing.md) và các ca ở mục [Tool PERSONNEL_CHAT](chat-testing.md#tool-personnel_chat): yêu cầu nhắn cho một nhân sự hợp lệ làm Agent gọi `send_chat_to_personnel` và báo đã gửi; ID sai hoặc người nhận chưa đủ điều kiện làm Agent báo không gửi được, không báo thành công giả; bật phê duyệt thì từ chối không gửi tin, chấp thuận gửi đúng nội dung đã duyệt. Mỗi lần gửi thử là **tin thật** tới người nhận và tính vào giới hạn ngày: dùng người nhận đã biết trước việc kiểm thử, gửi ít lần nhất có thể.
