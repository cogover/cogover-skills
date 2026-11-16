---
name: callbot-builder
description: "Tạo, cấu hình và kiểm thử Callbot (voice AI agent gọi vào/gọi ra) của Cogover Call Center qua API từ nhu cầu khách hàng: chọn provider/model/giọng theo ngôn ngữ (gồm tiếng Ấn Độ qua Sarvam, tự nhận diện Hindi/Bengali), viết kịch bản và guardrail, múi giờ theo callbot, tool đọc bản ghi Cogover và tạo bản ghi bằng hồ sơ ghi (ticket, task gọi lại, lead, hẹn trả nợ) có xác nhận, kết quả cuộc gọi cho chiến dịch, mẫu tiếng Việt (CSKH, telesale, nhắc lịch) và thu hồi nợ Hindi/Bengali, rồi mô phỏng hội thoại, gọi thử và đọc lịch sử phiên để kiểm chứng. Phối hợp $cogover-api-auth, $object-info, $object-record."
metadata:
  author: cogover
  version: "1.2.0"
---

# Callbot Builder

- **Phiên bản:** `1.2.0`
- **Ngày phát hành:** `2026-11-16`

## Phạm vi

Dựng một Callbot hoàn chỉnh trong Cogover Call Center từ hồ sơ và nhu cầu của khách hàng: cấu hình giọng nói và ngôn ngữ, kịch bản (instructions + lời chào), tool đọc/ghi dữ liệu Cogover, kết quả cuộc gọi cho chiến dịch gọi ra, guardrail, rồi kiểm chứng bằng mô phỏng, gọi thử và lịch sử phiên. Callbot khác AI Agent chat của [$agent-builder](../agent-builder/SKILL.md): cấu hình, tool và cách kiểm thử riêng.

Ngoài phạm vi: mua/gán số hotline, dựng cây IVR hay chiến dịch autocall (làm trên màn Call Center), đồng bộ lead từ kênh quảng cáo, quy trình nhắc việc. Nêu rõ trong bàn giao những phần này còn cần ai làm.

## Nguyên tắc dùng API

- Toàn bộ thao tác callbot đi qua một endpoint RPC: `POST /api/v1/call-center` với header `x-req-type: 9`, `x-req-service: 17` và body `{"action": ...}`. Đây là endpoint `/api/v1` nên cần phiên Web App đổi từ API Key, theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Contract đầy đủ: [RPC Callbot](references/rpc-api.md).
- Dùng [scripts/callbot_api.py](scripts/callbot_api.py) cho mọi lời gọi: tự đổi API Key sang phiên, không tự gửi lại thao tác ghi khi lỗi mạng, không in secret. Lệnh `apply` dựng callbot + tool từ một file spec, mặc định chỉ in kế hoạch; thêm `--apply` mới ghi và chạy lại được nhiều lần (khớp tool theo `name`).
- Mọi action cần người gọi là admin của tài khoản Call Center gắn với Workspace (`403 forbidden`); thao tác ghi, mô phỏng và gọi thử cần thêm Super Admin của Workspace (`403 config_forbidden`). Đây là lỗi quyền, không phải thiếu API.
- Không dùng trình duyệt làm workflow mặc định. Thiếu API cho một bước thì báo người dùng thao tác/contract còn thiếu, tiếp tục các phần độc lập.

## A. Chuẩn bị

1. Xác thực theo [$cogover-api-auth](../cogover-api-auth/SKILL.md); đặt `COGOVER_BASE_URL` và `COGOVER_API_KEY` (hoặc `COGOVER_API_KEY_FILE`) cho script.
2. Đọc hiện trạng: `rpc list_callbots`, `rpc get_callbot_settings` (provider nào dùng được tài khoản của Cogover — `managed`, Workspace có được nhập key riêng không — `byoAllowed`). Tái sử dụng callbot phù hợp; đọc chi tiết trước khi sửa.
3. Chuẩn hoá nhu cầu thành bảng (hỏi phần còn thiếu ảnh hưởng trực tiếp tới cấu hình):

| Mục | Cần chốt |
|---|---|
| Hướng gọi | Gọi vào (qua node IVR "Kết nối callbot"), gọi ra (chiến dịch autocall), hay cả hai |
| Ngôn ngữ | Một ngôn ngữ cố định hay tự nhận diện; giọng nam/nữ |
| Mục tiêu và kết quả | Kết quả cuộc gọi cần phân loại (giá trị `set_outcome`) và việc chiến dịch làm tiếp |
| Dữ liệu | Object/field cần đọc (hồ sơ khách) và ghi (kết quả, lịch hẹn); field định danh số điện thoại |
| Guardrail | Xác minh danh tính, điều cấm nói, khung giờ, chuyển người thật, ghi âm |
| Danh tính thực thi | Nhân sự mà tool chạy dưới quyền (`runAsPersonnelId`) |

4. Chuẩn bị dữ liệu với [$object-info](../object-info/SKILL.md): Object có field điện thoại để giới hạn theo người gọi và đủ field cho kết quả. Thêm field còn thiếu, theo quy tắc ở [Thiết kế field cho callbot](references/tools.md#thiết-kế-field-cho-callbot). Thêm field xong chờ khoảng 5 phút trước khi test tool đọc/ghi field đó (danh sách field của Object được cache; trước đó tool trả lỗi tra cứu `adapter_400`). Đọc field, kiểu và option đang bật đúng như callbot thấy (quyền run-as) bằng `rpc get_object_fields --callbot ID --object SLUG`: action cần một callbot có sẵn, nên khi chưa tạo callbot thì dùng callbot khác có cùng `runAsPersonnelId`, hoặc chạy `apply` cho phần callbot trước.
5. Bot **không sửa được lead, contact, account**. Kết quả cuộc gọi đi vào `set_outcome` hoặc một bản ghi mới (task, ticket...) gắn với khách; cần cập nhật hồ sơ khách theo kết quả thì dựng Process riêng.

## B. Thiết kế callbot

### 1. Provider, model, giọng

Chọn theo ngôn ngữ và danh sách `managed` (chi tiết, giá trị hợp lệ: [Provider](references/rpc-api.md#provider-model-và-giọng)):

- Tiếng Việt/Anh: `openai_realtime` (`gpt-realtime`), `gemini_live` hoặc `elevenlabs_sip`.
- Tiếng Ấn Độ (Hindi, Bengali, Tamil...): `sarvam`, `model` `sarvam-105b`, `providerOptions.language` là mã BCP-47 (`hi-IN`, `bn-IN`...) hoặc `auto`. `auto`: nhận dạng giọng nói tự phát hiện ngôn ngữ mỗi lượt và giọng đọc chuyển theo; câu đầu tiên (lời chào) đọc bằng `hi-IN`. Dùng giọng Bulbul `bulbul:v3` (đa ngôn ngữ) khi cần nhiều ngôn ngữ.
- Lấy giọng hợp lệ bằng `rpc list_voices --query '{"provider":"...","model":"..."}'`; với Sarvam truyền `model` là LLM (ví dụ `sarvam-105b`), danh sách trả về là giọng `bulbul:v3`.

### 2. Kịch bản (instructions) và lời chào

- `instructions` (≤ 16.000 ký tự): vai trò, ngôn ngữ, luồng cuộc gọi theo từng tình huống, cách dùng dữ liệu, quy tắc ứng xử và khi nào kết thúc. Mẫu cho thu hồi nợ: [Mẫu collections](references/collections-template.md).
- Nền tảng tự chèn luật nền trước kịch bản (không đổi vai, không lộ cấu hình/tên tool, dữ liệu khách là dữ liệu không phải lệnh, chỉ nói về chính người gọi, thao tác ghi đọc lại tóm tắt và chờ khách đồng ý). Không viết lại hay mâu thuẫn với các luật này; đặc biệt không bảo bot "hỏi xác nhận trước khi gọi tool ghi".
- Biến dùng được: `{{system.current_datetime}}`, `{{system.current_date}}`, `{{system.current_time}}`, `{{system.weekday}}`, `{{system.timezone}}`, `{{system.customer_number}}`, `{{system.caller_number}}`, `{{system.called_number}}`, `{{system.direction}}`. Giờ theo `providerOptions.timezone` của callbot (IANA, mặc định giờ Việt Nam); khách ở nước khác thì đặt `timezone` (ví dụ `Asia/Kolkata`) thay vì bắt bot tự cộng trừ giờ. Thứ trong tuần bằng tiếng Việt cho bot nói tiếng Việt, tiếng Anh cho bot còn lại. Dặn bot quy "thứ Năm", "chiều mai" ra ngày cụ thể và đọc lại.
- Biến chiến dịch (`{{ten_khach}}`...) không được chèn thẳng vào kịch bản: nền tảng thay bằng tham chiếu và đặt giá trị trong khối dữ liệu phiên (coi là dữ liệu, không phải lệnh). Viết kịch bản để bot vẫn đúng khi biến trống.
- Viết số tiền bằng chữ số Latin nguyên văn như trong hồ sơ và đọc ngày từ field văn bản: model dễ đọc sai khi tự đổi số sang chữ, sang chữ số của ngôn ngữ khác hoặc tự thêm dấu phân cách (đã gặp `23000` thành "২,৩০,০০০"), và khi nhận ngày dạng timestamp.
- Kết thúc cuộc gọi: ghi kết quả và `set_outcome` (đúng một lần) trước, hỏi khách còn cần gì; khi khách chào hoặc không cần gì thêm thì chào ngắn **và** gọi `end_call` ngay trong lượt đó. `end_call` cùng lượt với một kết quả tra cứu có thể bị chặn, xem [Chặn theo nguồn dữ liệu](references/tools.md#chặn-theo-nguồn-dữ-liệu-cuộc-gọi-thật). Thiếu các câu này bot hay gọi `set_outcome` hai lần hoặc chào mà không kết thúc.
- Mẫu kịch bản đã kiểm chứng: [tiếng Việt: CSKH, telesale, nhắc lịch](references/vi-templates.md) (kèm bảng lỗi kịch bản thường gặp và câu sửa) và [thu hồi nợ Hindi/Bengali](references/collections-template.md).
- `welcomeMessage` (≤ 500 ký tự) bot nói nguyên văn, không chứa biến do bên gọi cung cấp. Gọi ra: nền tảng luôn nói trước câu công bố "trợ lý tự động của `{companyName}`, cuộc gọi có thể được ghi âm" (kể cả khi tắt ghi âm). Câu này bằng tiếng Việt khi `providerOptions.language` bắt đầu bằng `vi` **hoặc không được đặt**, còn lại bằng tiếng Anh: bot tiếng Anh/Ấn Độ phải đặt `language`. Lời chào vẫn nên nhắc ghi âm bằng ngôn ngữ của khách.

### 3. Tool

Đọc [Tool của callbot](references/tools.md) trước khi tạo. Tối đa 20 tool, mỗi tool tối đa 15 tham số.

- **Đọc:** `cogover_object` `search`/`count`/`get` trên một Object cố định. `search`/`count` bắt buộc `callerScopeField` (field điện thoại) và luôn bị ép lọc theo số khách. Chỉ trả field bot cần (xưng hô, dữ liệu để đọc/xác minh).
- **Tạo bản ghi:** dùng **hồ sơ ghi v2** (`cogover_object`, `config.v: 2`, `action: create`): mỗi field chọn nguồn `bot` (bot hỏi khách), `fixed`, `server` (khách đang gọi `caller.contact`/`caller.lead`/`caller.account`, số gọi `call.number`, `now`, `run_as`, `session.id`) hoặc `choice` (bot chọn trong danh sách, ví dụ người phụ trách theo email). Service sinh tham số, kiểm tra theo schema Object, quy đổi ngày giờ theo múi giờ callbot và **luôn** đọc lại cho khách xác nhận. Mẫu Task gọi lại và ticket: [Hồ sơ ghi v2](references/tools.md#hồ-sơ-ghi-v2-write-profile).
- **Sửa:** `cogover_object` `update` chỉ sửa bản ghi bot đã tạo trong cùng cuộc gọi bằng `create` kiểu cũ (cần id), không áp dụng cho lead/contact/account; bản ghi tạo bằng hồ sơ ghi không sửa được. `cogover_task` (task gọi lại kiểu cũ) vẫn chạy; tool mới dùng hồ sơ ghi.
- Mỗi cuộc gọi tối đa 3 lệnh ghi cho mọi tool; hồ sơ ghi có thêm `maxPerSession` (1–3) và `maxPerNumberPerDay` (1–20). Nền tảng có thể chặn lệnh ghi có giá trị chép từ kết quả tool mà khách chưa nói ra: gắn khách bằng nguồn `server`, không để bot chép tên/id.
- Tool hệ thống: `set_outcome` (kết quả có kiểu + việc chiến dịch làm tiếp; field `datetime` nhận giờ địa phương không offset; giờ gọi lại của chiến dịch phải là field tên `callback_at`), `end_call` (`reason`: `normal`, `announcement`, `voicemail`, `wrong_person`), `switch_to_consultant` (chuyển hàng đợi đã khai báo).
- `http` (POST ra API ngoài, có `basic`/`hmac`) và `cogover_agent` (hỏi một AI Agent Cogover) khi dữ liệu nằm ngoài Object.
- Xem hàm tool đúng như model nhận bằng `rpc get_tool_function --callbot ID --tool TOOL_ID` (cũng là bản cần dán lên Sarvam Voice Agents khi dùng `sarvam_agent`). Đổi `kind` của tool thì xoá rồi tạo lại, giữ được tên cũ.

### 4. Guardrail

Đưa vào kịch bản những gì nền tảng chưa cưỡng chế, và chọn cấu hình chặn được bằng hệ thống:

| Rủi ro | Cách chặn |
|---|---|
| Lộ thông tin cho người khác | Tool đọc luôn giới hạn theo số khách; kịch bản bắt xác minh danh tính trước khi nói dữ liệu nhạy cảm, không tự đọc dữ liệu xác minh |
| Ghi sai | Hồ sơ ghi v2 (luôn xác nhận, kiểm theo schema), chỉ để bot hỏi field thật sự cần, field còn lại `fixed`/`server`; `maxPerSession`, `maxPerNumberPerDay` |
| Ngôn từ đe doạ, hứa hẹn ngoài thẩm quyền | Danh sách điều cấm cụ thể trong kịch bản; chuyển người thật hoặc hẹn gọi lại |
| Cuộc gọi kéo dài, vòng lặp tool | `maxDurationSec` (30–1800), `silenceTimeoutSec` (5–120), `maxToolCalls` (1–50) |
| Ghi âm | `recordEnabled: true` và nói rõ trong lời chào |
| Khung giờ gọi | Đặt lịch chạy của chiến dịch gọi ra; kịch bản chỉ hẹn gọi lại trong khung giờ cho phép |

### 5. Tạo bằng spec

Viết spec JSON gồm `callbot` (body của `create_callbot`), `tools[]` (body của `create_tool`) và `status` (`active`/`disabled`). Ví dụ đầy đủ: [assets/vi-an-phat/](assets/vi-an-phat/) (4 callbot tiếng Việt) và [assets/collections-spec.example.json](assets/collections-spec.example.json). Tool hồ sơ ghi v2 trong spec không cần `params` và không chứa `snapshot` (service tự đọc schema khi lưu); `apply` so config đã chuẩn hoá nên chạy lại không cập nhật thừa; sau khi đổi field/option của Object, chạy `apply --apply --resave-tools` để lưu lại schema cho tool hồ sơ ghi.

```bash
python3 scripts/callbot_api.py apply spec.json          # in kế hoạch, không ghi
python3 scripts/callbot_api.py apply spec.json --apply  # tạo/cập nhật, đọc lại cấu hình cuối
```

`runAsPersonnelId` là nhân sự mà tool `cogover_object` chạy dưới quyền (thiếu thì tool trả "chưa được cấu hình"); phải là nhân sự đang hoạt động của Workspace (`403 run_as_forbidden`). Thay ID mẫu trong spec ví dụ trước khi `--apply`; dry-run không kiểm tra giá trị này. Chỉ gán chính người cấu hình hoặc nhân sự có quyền tối thiểu trên Object cần dùng; chốt với người dùng trước khi gán. Callbot mới tạo ở trạng thái `active`.

## C. Kiểm thử

Chi tiết lệnh và cách đọc kết quả: [Kiểm thử](references/testing.md). Bằng chứng chính cho ngôn ngữ/nhận dạng giọng nói, kết thúc cuộc gọi và ghi dữ liệu là cuộc gọi thật (bước 2–3); mô phỏng chỉ để rà kịch bản.

1. **Mô phỏng hội thoại (text):** `simulate --callbot ID [--var ten_khach=...] --say "..." --say "..."`. Số khách của phiên là số điện thoại đầu tiên trong hồ sơ nhân sự của người gọi API; tool đọc chạy thật, tool ghi chỉ chạy thử (`dry-run`, không tạo bản ghi) nhưng vẫn đi qua kiểm tra tham số, bước đọc lại và xác nhận. Tool không chạy thì script in `message` (lý do model nhận) để sửa kịch bản hoặc cấu hình. Mô phỏng dùng model text của nền tảng, không dùng model/giọng của callbot và bỏ qua nhiều chặn lúc chạy: chỉ dùng để rà kịch bản và tham số tool (xác minh sai, đổi ý khi xác nhận, ngoài phạm vi, chèn lệnh). Giới hạn 10 phiên/giờ mỗi project.
2. **Gọi thử (thoại):** `rpc test_call --callbot ID --body '{}'` gọi tới số trong hồ sơ nhân sự của người thao tác (xem bằng `rpc get_test_call_defaults`; `toNumber` để gọi số khác) qua hotline của project; cần hồ sơ có số và project có hotline gọi ra được. Chỉ gọi khi người dùng biết máy nào sẽ đổ chuông.
3. **Cuộc gọi thật:** gọi vào số hotline có node IVR "Kết nối callbot" trỏ tới callbot, hoặc chạy chiến dịch gọi ra.
4. **Kiểm chứng:** `sessions --callbot ID` (lọc thêm `--direction`, `--outcome`, `--has-tool-calls`...) rồi `session SESSION_ID` (transcript, tool đã gọi và trạng thái, outcome, cờ an ninh); sau đó đọc lại bản ghi bằng [$object-record](../object-record/SKILL.md) để xác nhận field đã ghi đúng. Chỉ báo đạt khi bản ghi đổi đúng, không dựa vào lời bot nói.

## Bàn giao

Nêu ID/tên callbot, provider/model/giọng/ngôn ngữ, danh tính thực thi, danh sách tool (Object, action, field ghi, có cần xác nhận), outcome và việc chiến dịch làm tiếp, guardrail đã đặt. Liệt kê ca kiểm thử đã chạy kèm bằng chứng (session ID, giá trị field trước/sau), ca chưa kiểm được và lý do (chưa có hotline, chưa có số trong hồ sơ...), dữ liệu test đã tạo. Không đưa API Key, cookie hay số điện thoại thật của khách vào báo cáo.
