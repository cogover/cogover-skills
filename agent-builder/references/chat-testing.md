# Kích hoạt và kiểm thử chat

## HTTP chat

Đọc [$cogover-api-auth](../../cogover-api-auth/SKILL.md). Dùng phiên Web App, đủ cookie/CSRF:

```http
POST https://{workspace-domain}/api/v1/ai-agent
Content-Type: application/json
x-req-type: 1
x-req-service: 10

{"agentId":"{agent-id}","message":"Reply exactly AGENT_BUILDER_OK. Do not call tools or change data."}
```

API chat trả `r`, `msg`, `data` ở **root**, khác `body` của API cấu hình. Response tạo hội thoại:

```json
{"r":0,"msg":"OK","data":{"chatSessionId":"{chat-session-id}","chatServerConvId":"{conversation-id}","reasoningSettings":{}}}
```

`chatSessionId` dùng cho request Agent; `chatServerConvId` dùng để đối chiếu hội thoại và URL giao diện. Chúng không thể dùng thay nhau. Response không chứa câu trả lời cuối. Lắng nghe WebSocket **trước** khi gửi request để không bỏ lỡ câu trả lời nhanh.

| `x-req-service` | Thao tác | Payload |
|---:|---|---|
| 10 | Bắt đầu chat và gửi tin nhắn đầu | `agentId`, `message`; tùy chọn `reasoning` |
| 11 | Gửi lượt tiếp theo | `chatSessionId`, `message`; tùy chọn `reasoning` |
| 12 | Trả lời yêu cầu duyệt công cụ | `chatSessionId`, `toolUseId`, `approved` |
| 13 | Hủy một lượt đang chạy | `chatSessionId`, `turnId` |

Request tiếp theo được chấp nhận có thể trả `status: "ACCEPTED"` và `turnId`; tiếp tục chờ sự kiện cuối. Không gửi đồng thời nhiều câu hỏi trong cùng hội thoại khi đang xác minh.

### Reasoning lúc chat

Bỏ `reasoning` để test mặc định của Agent. Để test override, gửi cấu hình nằm trong khả năng model **và** policy Agent, ví dụ `"reasoning":{"enabled":true,"effort":"medium"}`. `reasoningEffort` là trường tương thích cũ; không gửi hai kiểu cấu hình cùng lúc. Đọc `reasoningSettings` thực tế, không suy ra hiệu lực chỉ từ payload yêu cầu.

### Test bằng HTTP và WebSocket

1. Đọc trạng thái/quyền Agent bằng API cấu hình; kích hoạt tài nguyên cần dùng qua các thao tác đổi trạng thái đã có contract. Probe không thực hiện bước này.
2. Lấy phiên theo skill xác thực, kết nối và đăng nhập WebSocket như mục dưới, rồi gọi HTTP service 10 để tạo hội thoại mới. Đọc câu trả lời cuối và sự kiện hoàn tất đúng hội thoại/lượt.
3. Với kiểm tra nghiệp vụ, dùng HTTP/WebSocket client gửi câu hỏi thực tế qua service 10/11 và giữ kết nối để đọc các sự kiện. Đối chiếu công cụ được gọi, kết quả, nguồn RAG và dữ liệu nghiệp vụ qua API tương ứng. Nếu thiếu schema sự kiện để xác minh một điều kiện, báo cần bổ sung contract; không suy ra PASS từ lời tự báo của Agent.
4. Khi nhận `TOOL_APPROVAL_REQUEST`, lấy `data.toolUseId`, trình bày thao tác cần duyệt dựa trên dữ liệu sự kiện và áp dụng quyết định đã được người dùng cho phép. Gửi service 12 với `chatSessionId`, `toolUseId`, `approved: true/false`; tiếp tục chờ kết quả và `LOOP_COMPLETE`. Không coi HTTP chấp nhận quyết định là bằng chứng công cụ đã chạy. Chỉ yêu cầu xác nhận với thao tác chưa được cho phép; không thêm vòng duyệt lặp vào việc đã được ủy quyền.
5. Khi timeout/mất kết nối, giữ các ID đã nhận và báo phần chưa xác minh. Không tự gửi lại yêu cầu tạo chat hoặc tin nhắn có thể gây thao tác ghi. Khôi phục kết quả chỉ khi có contract lịch sử/replay; xem [API cần bổ sung](api-gaps.md).

URL hội thoại có thể có dạng `/{app-slug}/agent-chat?agentConversation={chatServerConvId}`. Chỉ dùng App slug đã biết qua metadata API hoặc người dùng; URL dùng để bàn giao, không cần mở trình duyệt để test. Nếu chưa đủ thông tin URL, trả ID hội thoại.

## WebSocket của Workspace

Kết nối `wss://{workspace-domain}/websocket` với phiên cùng Workspace và Origin tương ứng. Không dùng URL máy chủ hay cổng triển khai riêng. Gửi cookie phiên trong handshake của WebSocket client, không đặt secret vào query string. Không cần mở trình duyệt.

Đăng nhập giao thức sau khi socket mở:

```json
{"id":1,"type":2,"serviceVersion":1,"service":1,"from":"web-{client-id}","body":{"isVisitor":false}}
```

Đợi response cùng `id`, `type: 2`, `service: 1`, `body.r: 0`; kiểm tra Workspace của response. Đây là client nhân sự đã xác thực, không phải contract đăng nhập khách truy cập ngoài Workspace.

Heartbeat ứng dụng nhận `{"type":1,"serviceVersion":1,"service":0}`; trả frame `type: 1`, `service: 0`, `serviceVersion: 1`, `id` mới, `from` của client và `body: null`. Không nhầm heartbeat với phản hồi Agent.

Message mới có `type: 2`, `service: 116`, `body.object_type: "message"` và `body.messages[]`. Chỉ lấy message của Agent (`part_type: 3`), bỏ message của nhân sự (`part_type: 1`). Mỗi message chứa `conversation_id`, `id`, `seq`, `text`, `custom_data`; `custom_data` thường là **chuỗi JSON** cần parse thêm:

```json
{
  "chatSessionId":"{chat-session-id}",
  "turnId":"{turn-id}",
  "agentMessageType":"LOOP_OUTPUT",
  "isFinalResponse":true,
  "data":{"type":"TEXT","text":"AGENT_BUILDER_OK"}
}
```

| `agentMessageType` | Cách xử lý |
|---|---|
| `LOOP_STARTED` | Ghi nhận lượt bắt đầu |
| `LOOP_OUTPUT` | Có thể là text, reasoning hoặc tool. Chỉ `data.type: TEXT` và `isFinalResponse: true` được dùng làm câu trả lời cuối |
| `TOOL_APPROVAL_REQUEST` | Chờ quyết định được phép; lấy `data.toolUseId`. Không tự duyệt chỉ để test đi tiếp |
| `LOOP_ERROR` | Ghi nhận lỗi, không kết luận PASS |
| `LOOP_COMPLETE` | Lượt kết thúc; cần trạng thái hoàn tất, không lỗi và câu trả lời cuối đúng kỳ vọng |

`LOOP_COMPLETE` có thể có `isFinalResponse: false` và text rỗng — đây là bình thường; câu trả lời ở frame TEXT trước đó. Không dùng số lượng frame, độ dài nội dung hay sự xuất hiện reasoning làm tiêu chí PASS.

Lọc đúng `conversation_id` **và** `custom_data.chatSessionId`, sau đó `turnId` khi có. Khử trùng theo message `id`; không ghép một hội thoại khác hoặc frame cập nhật danh sách hội thoại vào câu trả lời. Với deployment cũ thiếu `turnId`, chỉ dùng `userMsgChatServerId`/sequence khi đã có contract xác định tương quan lượt; nếu chưa có, yêu cầu người dùng cung cấp trước khi kết luận test. Không tự ghép sự kiện theo thời gian đến. Không giả định có streaming từng token; có thể nhận cả block văn bản.

## Probe kèm skill

`scripts/chat_probe.py` tạo đúng một hội thoại mới, dùng câu hỏi kiểm tra kết nối không yêu cầu Tool, chờ TEXT cuối và `LOOP_COMPLETE`. Script không kích hoạt Agent, sửa quyền, duyệt Tool hay tự gửi lại tin nhắn khi kết nối lỗi. Nếu cần test nghiệp vụ/ghi/RAG hoặc duyệt Tool, dùng HTTP/WebSocket client theo luồng trên và ma trận phía dưới. Giới hạn của probe không phải thiếu API và không phải lý do mở trình duyệt.

Yêu cầu Python 3.10+; chạy live cần thư viện **websocket-client** trong môi trường Python đang dùng. Dùng thư viện đã có; nếu thiếu, cài theo quy định môi trường (package này không được đóng gói trong skill). `--self-test` chỉ dùng thư viện chuẩn, không gọi mạng:

```bash
python3 scripts/chat_probe.py --self-test
python3 scripts/chat_probe.py --agent-id '{agent-id}' --timeout 120
```

Chạy từ thư mục skill hoặc thay đường dẫn script bằng đường dẫn đã resolve. Credential `COGOVER_BASE_URL` và `COGOVER_API_KEY` được cung cấp qua scoped environment/secret store như skill xác thực; không điền literal key vào lệnh, prompt hoặc file. Có thể thêm `--reasoning-effort` với giá trị hợp lệ để test override; bỏ cờ để test mặc định.

Probe trả kết quả JSON và exit code khác 0 nếu lỗi, chờ duyệt, hết hạn hoặc đáp án không khớp. Script chỉ kiểm tra kết nối/câu trả lời, không chứng minh quyền nghiệp vụ, chất lượng model, hiệu lực giới hạn Skill, Tool hay RAG. Probe trả `TURN_ID_MISSING_API_CONTRACT_REQUIRED` khi không có `turnId`: cần contract tương quan lượt phù hợp để viết client bổ sung. `TOOL_APPROVAL_REQUIRED` nghĩa là probe không tự duyệt; API duyệt service 12 đã có trong tài liệu, không cần xin lại API này. Cả hai trường hợp đều không tự chuyển sang trình duyệt.

## Ma trận xác minh

| Tình huống | Bằng chứng cần có |
|---|---|
| Kết nối cơ bản | Câu trả lời kỳ vọng + kết thúc thành công đúng hội thoại/lượt |
| CORE | Agent làm đúng hướng dẫn cốt lõi và sử dụng công cụ đã gắn |
| EXTENDED | Có bước kích hoạt đúng Skill trước công cụ của Skill; không kích hoạt Skill không liên quan hoặc Skill CORE đã nạp sẵn (lỗi `Unknown skill_slug` cho slug CORE là dấu hiệu System Prompt đang lặp lại cơ chế kích hoạt) |
| Thiếu thông tin | Agent hỏi đúng dữ liệu cần thiết, chưa thực hiện thay đổi sai |
| Ngoài phạm vi/thiếu quyền | Agent từ chối hoặc hướng dẫn đúng; không lộ dữ liệu không được phép |
| Tool cần duyệt | Nhận đúng sự kiện/yêu cầu, gửi quyết định qua service 12; từ chối không tạo side effect; chỉ test chấp thuận khi được phép |
| Reasoning | Mặc định bật, override hợp lệ được nhận, lựa chọn ngoài policy bị từ chối/không khả dụng |
| RAG có/không có đáp án | Có nguồn đúng khi tìm thấy; không bịa khi không tìm thấy |
| Ghi dữ liệu | Đọc lại record/Process và so kết quả, không chỉ tin câu trả lời Agent |

Ghi rõ từng phần “đã kiểm tra cấu hình”, “đã chạy chat”, “đã kiểm thử nghiệp vụ” hoặc “chưa kiểm thử”. Nếu có lỗi do thiếu khả năng trên Workspace, giữ phần đã hoàn tất và báo đúng phần chưa thực hiện; không tự đổi danh tính hay mở rộng quyền để vượt lỗi.
