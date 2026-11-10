# RPC Callbot

Các action tạo/sửa callbot, tool, giọng, mô phỏng và lịch sử phiên đã được kiểm chứng trên Workspace thật. Một số mã lỗi hiếm gặp liệt kê theo response của service, chưa gặp trực tiếp. Ví dụ dùng placeholder.

## Endpoint và xác thực

```http
POST /api/v1/call-center
x-req-type: 9
x-req-service: 17
Content-Type: application/json
Cookie: AuthToken={AuthToken}; HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF}
x-csrf-token: {XSRF}
x-xsrf-token: {XSRF}
```

Phiên lấy từ `POST /bapi/v1/auth-token` với `Authorization: Bearer {tokenId}-{secretToken}`, theo [$cogover-api-auth](../../cogover-api-auth/SKILL.md). Workspace và nhân sự thao tác lấy từ phiên, không gửi trong body.

Body:

```json
{"action": "get_callbot", "callbotId": "{CALLBOT_ID}", "toolId": "...", "simId": "...", "sessionId": "...", "body": {}, "query": {}}
```

Chỉ gửi các khoá action cần. `callbotId` là chuỗi số (`^[1-9][0-9]{0,9}$`); `query` là object giá trị chuỗi.

## Response và lỗi

Thành công: `{"r": 0, "msg": "OK", "data": ...}`. Lỗi: `r` là mã kiểu HTTP, `msg` là mã lỗi, `data.message` là mô tả; HTTP status có thể vẫn là 200.

| `r` / `msg` | Ý nghĩa |
|---|---|
| `403 forbidden` | Người thao tác không phải admin của tài khoản Call Center gắn với Workspace (áp dụng cho mọi action, kể cả đọc) |
| `403 config_forbidden` | Action ghi khi người thao tác không phải Super Admin |
| `403 run_as_forbidden` | `runAsPersonnelId` không phải nhân sự đang hoạt động của Workspace |
| `403 byo_disabled` | Gửi key/SIP URI/project riêng khi Workspace không cho phép |
| `404 no_portal`, `404 no_project`, `409 multiple_portals` | Workspace chưa gắn (hoặc gắn nhiều hơn một) tài khoản Call Center |
| `400 invalid_params` | Tham số sai định dạng, kèm mô tả trường (ví dụ `voice is not supported by sarvam`, `callerScopeField is required for search`) |
| `400 invalid_action` | Action không tồn tại |
| `400 no_phone_number` | `test_call` khi hồ sơ nhân sự của người thao tác chưa có số điện thoại |
| `401 unauthorized` | Phiên hết hạn: request bị từ chối, chưa thực thi; đổi phiên rồi gửi lại một lần |
| `404 not_found` | Callbot/tool/phiên không thuộc Workspace |
| `409 duplicate_name` | Trùng tên tool trong callbot |
| `409 version_conflict` | `update_callbot` với `version` cũ: đọc lại rồi gộp thay đổi |
| `429 rate_limited` | Vượt giới hạn tần suất của API, của mô phỏng (10 phiên/giờ) hoặc của gọi thử; chờ rồi thử lại thao tác đọc |
| `409 simulation_ended`, `409 turn_limit`, `410 simulation_expired` | Phiên mô phỏng đã kết thúc, quá 30 lượt, hoặc đã hết hạn sau một thời gian không dùng: tạo phiên mới |
| `400 simulation_not_supported`, `400 no_api_key` | Provider không mô phỏng được (`sarvam_agent`), hoặc môi trường chưa cấu hình model dùng cho mô phỏng |
| `400 callbot_disabled`, `400 no_hotline` | Gọi thử khi callbot đang tắt, hoặc project không có hotline gọi ra |
| `503 callbot_admin_disabled` | Môi trường chưa bật API quản trị Callbot |

Thao tác ghi và gọi ra ngoài (`create_*`, `update_*`, `delete_*`, `put_*_secret(s)`, `sync_callbot`, `set_callbot_status`, `test_call`, `start_simulation`, `send_simulation_message`) không tự gửi lại khi timeout: đọc lại trạng thái trước khi thử lại để tránh tạo trùng hoặc gọi trùng.

## Action

Mọi action cần người thao tác là admin của tài khoản Call Center gắn với Workspace. Đọc: `list_callbots`, `get_callbot`, `get_callbot_settings`, `list_tools`, `list_voices`, `list_sessions`, `get_session`. Mọi action còn lại cần thêm quyền Super Admin của Workspace, kể cả mô phỏng và gọi thử.

| Action | Khoá | `body` / `query` | `data` |
|---|---|---|---|
| `list_callbots` | — | — | Mảng callbot (không có `instructions`) |
| `get_callbot_settings` | — | — | `{byoAllowed, managed: {provider: true}}` |
| `get_callbot` | `callbotId` | — | Callbot đầy đủ, `version`, `secrets` (chỉ trạng thái) |
| `create_callbot` | — | Callbot input | `{id, version}` |
| `update_callbot` | `callbotId` | Trường cần đổi + `version` hiện tại | `{id, version}` |
| `set_callbot_status` | `callbotId` | `{"status": "active" \| "disabled"}` | `{id, version}` |
| `delete_callbot` | `callbotId` | — | `{id, version}` |
| `put_callbot_secrets` | `callbotId` | `{apiKey, expectedProvider}` (chỉ khi `byoAllowed`) | `{id, version}` |
| `list_voices` | — | `query: {provider, model, callbotId?}` | `{voices: [{id, name, gender?, language?}], source}` |
| `list_tools` | `callbotId` | — | Mảng tool |
| `create_tool` / `update_tool` | `callbotId` (+ `toolId`) | Tool input | `{id}` |
| `delete_tool` | `callbotId`, `toolId` | — | `{id}` |
| `put_tool_secret` | `callbotId`, `toolId` | `{value}` (tool `http` có auth) | `{id}` |
| `test_call` | `callbotId` | `{}` | `{requestId, callId}` |
| `start_simulation` | `callbotId` | `{}` hoặc `{"variables": {...}}` | `{simId, reply}` |
| `send_simulation_message` | `simId` | `{"text": "..."}` | `{reply, replies[], toolCalls[], ended, turns}` |
| `end_simulation` | `simId` | — | `{simId}` |
| `list_sessions` | — | `query: {callbotId?, from?, to?, endReason?, cursor?, limit?}` (epoch ms) | `{items[], nextCursor?}` |
| `get_session` | `sessionId` | — | Phiên + `transcript[]`, `toolCalls[]`, `variables`, `securityFlags[]` |

## Callbot input

| Trường | Ràng buộc | Ghi chú |
|---|---|---|
| `name` | 1–100, bắt buộc khi tạo | |
| `instructions` | 1–16.000, bắt buộc khi tạo (trừ `sarvam_agent`) | Kịch bản; biến `{{system.*}}` |
| `welcomeMessage` | 0–500 | Câu đầu bot nói, nguyên văn |
| `provider` | `openai_realtime`, `gemini_live`, `qwen_omni_rt`, `elevenlabs_sip`, `sarvam`, `sarvam_agent` | |
| `engine` | `service` | |
| `model`, `voice` | Theo provider | Xem dưới |
| `transcriptionModel` | OpenAI: `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, `whisper-1`; `null` để tắt | Provider khác bỏ trống |
| `providerOptions` | Object ≤ 10 khoá, giá trị chuỗi/số | Thay toàn bộ khi gửi; GET trả dạng chuỗi |
| `companyName` | 1–100 | Tên trong câu công bố khi gọi ra; mặc định tên callbot |
| `recordEnabled` | boolean | Ghi âm |
| `runAsPersonnelId` | ID nhân sự đang hoạt động | Danh tính của tool `cogover_object` |
| `maxDurationSec` | 30–1800 | |
| `silenceTimeoutSec` | 5–120 | |
| `maxToolCalls` | 1–50 | Giới hạn số lần gọi tool mỗi cuộc |
| `maxConcurrent` | 0–100 | Số cuộc đồng thời |

Chuỗi không được chứa ký tự điều khiển (trừ xuống dòng, tab). Tạo callbot `openai_realtime` (hoặc không gửi `provider`) có thể bị từ chối nếu thiếu `openaiProjectSipUri`; khi đó chọn provider có trong `managed` hoặc hỏi quản trị môi trường.

## Provider, model và giọng

| Provider | Đường kết nối | `model` | `voice` | `providerOptions` |
|---|---|---|---|---|
| `openai_realtime` | SIP | `gpt-realtime` (mặc định), `gpt-realtime-mini` | `alloy`, `ash`, `ballad`, `cedar`, `coral`, `echo`, `marin`, `sage`, `shimmer`, `verse` | `language` (ngôn ngữ nhận dạng giọng khách) |
| `gemini_live` | WebSocket | `gemini-3.8-live` (mặc định) | Tên giọng Gemini (ví dụ `Kore`) | `language`, `silenceMs` |
| `elevenlabs_sip` | SIP | LLM của agent (ví dụ `gemini-2.5-flash`) | voice_id ElevenLabs (`list_voices`) | `language`, `ttsModel` |
| `qwen_omni_rt` | WebSocket | `qwen3.8-omni-flash-realtime`... | Theo model (`list_voices`) | `silenceMs` |
| `sarvam` | WebSocket | `sarvam-105b` (mặc định), `glm5.3-flash`, `gemma4`, `deepseekv4.1-flash-1017` | Giọng Bulbul theo `ttsModel` | `language`, `ttsModel`, `sttModel`, `sttMode`, `silenceMs` |
| `sarvam_agent` | WebSocket | `samvaad` | — | Agent cấu hình trên Sarvam: `orgId`, `workspaceId`, `appId`, `version` bắt buộc |

`sarvam`:

- `language`: `hi-IN` (mặc định), `en-IN`, `bn-IN`, `ta-IN`, `te-IN`, `kn-IN`, `ml-IN`, `mr-IN`, `gu-IN`, `pa-IN`, `or-IN`, `auto`. Với `auto`, mỗi câu khách nói được nhận dạng kèm ngôn ngữ và giọng đọc chuyển sang ngôn ngữ đó; lời chào đọc bằng `hi-IN`.
- `ttsModel`: `bulbul:v3` (mặc định; giọng đa ngôn ngữ `shubh`, `priya`, `ritu`, `neha`, `kavya`, `rahul`...), `bulbul:v4-flash` (giọng gắn ngôn ngữ và phong cách, ví dụ `roopa_bn_conversational`, `ritu_hi_banking`). Giọng phải thuộc `ttsModel` đã chọn.
- `sttModel`: `saaras:v3-realtime` (mặc định), `saaras:v4`. `sttMode`: `transcribe` (mặc định) hoặc `codemix`.
- `silenceMs`: 200–2000.
- `list_voices` cho Sarvam: gửi `model` là LLM (ví dụ `sarvam-105b`) để nhận danh sách giọng `bulbul:v3`; giá trị có dấu `:` như `bulbul:v3` bị từ chối ở bước kiểm tra tham số.

Workspace có `byoAllowed: false` không được gửi API key, SIP URI hay project riêng (`403 byo_disabled`). Lúc tạo, service không kiểm tra provider có nằm trong `managed` hay không: chọn provider ngoài `managed` vẫn lưu được nhưng cuộc gọi sẽ lỗi vì thiếu key. Luôn đối chiếu với `get_callbot_settings` trước.
