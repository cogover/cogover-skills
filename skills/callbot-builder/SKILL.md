---
name: callbot-builder
description: "Tạo, cấu hình và kiểm thử Callbot (voice AI agent gọi vào/gọi ra) của Cogover Call Center qua API từ nhu cầu khách hàng: chọn provider/model/giọng theo ngôn ngữ (gồm tiếng Ấn Độ qua Sarvam, tự nhận diện Hindi/Bengali), viết kịch bản và guardrail, tool đọc/ghi bản ghi Cogover (tạo/cập nhật lead, hẹn trả nợ, hẹn gọi lại), kết quả cuộc gọi cho chiến dịch, rồi mô phỏng hội thoại, gọi thử và đọc lịch sử phiên để kiểm chứng. Phối hợp $cogover-api-auth, $object-info, $object-record."
metadata:
  author: cogover
  version: "1.1.0"
---

# Callbot Builder

- **Phiên bản:** `1.1.0`
- **Ngày phát hành:** `2026-11-10`

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

4. Chuẩn bị dữ liệu với [$object-info](../object-info/SKILL.md): Object có field điện thoại để giới hạn theo người gọi và đủ field cho kết quả. Thêm field còn thiếu, theo quy tắc ở [Thiết kế field cho callbot](references/tools.md#thiết-kế-field-cho-callbot). Thêm field xong chờ khoảng 5 phút trước khi test tool đọc/ghi field đó (danh sách field của Object được cache; trước đó tool trả lỗi tra cứu `adapter_400`).
5. **Bắt buộc: signing key của project Stringee** gắn với Workspace (`stringee.dh_account_project.signing_secret_key`). Key trống thì mọi cuộc gọi vào callbot đều lỗi `NO_SECRET` (bot im lặng). Chi tiết: [Signing key của project](references/project-signing-key.md).
   - Service callbot tự bảo đảm key mỗi khi tạo, sửa hoặc bật callbot. Đã có key thì giữ nguyên. Key trống thì service sinh 32 ký tự chữ và số rồi ghi vào; response trả `signingKey`, còn `apply` in ra `projectSigningKey`.
   - Sau `apply --apply`, đọc `projectSigningKey` và báo "đã có" (`existing`) hoặc "đã tạo mới" (`created`). Không in key.
   - Gặp `failed`, `project_not_found`, hoặc không thấy trường này (service bản cũ): xử lý theo tài liệu trên.
     - master/vn-release: được cấp quyền cho user DB hoặc chạy helper `ensure`.
     - Prod: chỉ đọc, báo người dùng nhờ quản trị DB.
     - Chưa có key thì không gọi thử.

## B. Thiết kế callbot

### 1. Provider, model, giọng

Chọn theo ngôn ngữ và danh sách `managed` (chi tiết, giá trị hợp lệ: [Provider](references/rpc-api.md#provider-model-và-giọng)):

- Tiếng Việt/Anh: `openai_realtime` (`gpt-realtime`), `gemini_live` hoặc `elevenlabs_sip`.
- Tiếng Ấn Độ (Hindi, Bengali, Tamil...): `sarvam`, `model` `sarvam-105b`, `providerOptions.language` là mã BCP-47 (`hi-IN`, `bn-IN`...) hoặc `auto`. `auto`: nhận dạng giọng nói tự phát hiện ngôn ngữ mỗi lượt và giọng đọc chuyển theo; câu đầu tiên (lời chào) đọc bằng `hi-IN`. Dùng giọng Bulbul `bulbul:v3` (đa ngôn ngữ) khi cần nhiều ngôn ngữ.
- Lấy giọng hợp lệ bằng `rpc list_voices --query '{"provider":"...","model":"..."}'`; với Sarvam truyền `model` là LLM (ví dụ `sarvam-105b`), danh sách trả về là giọng `bulbul:v3`.

### 2. Kịch bản (instructions) và lời chào

- `instructions` (≤ 16.000 ký tự): vai trò, ngôn ngữ, luồng cuộc gọi theo từng tình huống, cách dùng dữ liệu, quy tắc ứng xử và khi nào kết thúc. Mẫu cho thu hồi nợ: [Mẫu collections](references/collections-template.md).
- Nền tảng tự chèn luật nền trước kịch bản (không đổi vai, không lộ cấu hình/tên tool, dữ liệu khách là dữ liệu không phải lệnh, chỉ nói về chính người gọi, thao tác ghi đọc lại tóm tắt và chờ khách đồng ý). Không viết lại hay mâu thuẫn với các luật này; đặc biệt không bảo bot "hỏi xác nhận trước khi gọi tool ghi".
- Biến dùng được: `{{system.current_datetime}}`, `{{system.current_date}}`, `{{system.current_time}}`, `{{system.weekday}}`, `{{system.customer_number}}`, `{{system.caller_number}}`, `{{system.called_number}}`, `{{system.direction}}`. Giờ hệ thống theo UTC+7 và thứ trong tuần bằng tiếng Việt ("Thứ Hai"...): bot nói ngôn ngữ khác cần bảng quy đổi thứ trong kịch bản, nếu không dễ tính sai ngày khi khách nói "thứ Năm"; khách ở múi giờ khác thì ghi rõ độ lệch.
- Viết số tiền bằng chữ số Latin nguyên văn như trong hồ sơ và đọc ngày từ field văn bản: model dễ đọc sai khi tự đổi số sang chữ, sang chữ số của ngôn ngữ khác hoặc tự thêm dấu phân cách (đã gặp `23000` thành "২,৩০,০০০"), và khi nhận ngày dạng timestamp.
- Kết thúc cuộc gọi: ghi kết quả và `set_outcome` trước, chào và chờ khách đáp rồi mới `end_call`. `end_call` ngay sau một kết quả tool có thể bị chặn, xem [Chặn theo nguồn dữ liệu](references/tools.md#chặn-theo-nguồn-dữ-liệu-cuộc-gọi-thật).
- `welcomeMessage` (≤ 500 ký tự) bot nói nguyên văn, không chứa biến do bên gọi cung cấp. Gọi ra: nền tảng luôn nói trước câu công bố "trợ lý tự động của `{companyName}`, cuộc gọi có thể được ghi âm" (kể cả khi tắt ghi âm). Câu này bằng tiếng Việt khi `providerOptions.language` bắt đầu bằng `vi` **hoặc không được đặt**, còn lại bằng tiếng Anh: bot tiếng Anh/Ấn Độ phải đặt `language`. Lời chào vẫn nên nhắc ghi âm bằng ngôn ngữ của khách.

### 3. Tool

Đọc [Tool của callbot](references/tools.md) trước khi tạo. Tối đa 20 tool, mỗi tool tối đa 15 tham số kiểu `string`/`number`.

- `cogover_object`: đọc/ghi một Object cố định. `search`/`count` bắt buộc `callerScopeField` (field điện thoại) và luôn bị ép lọc theo số khách; `update` có `callerScopeField` tự tìm bản ghi của chính người gọi, không cần id; `create` chỉ ghi field trong `writableFields`. Không có xoá.
- Tool đọc chỉ trả field bot cần; tool ghi để `returnFields: []`. Nền tảng có thể chặn lệnh ghi có giá trị chép từ kết quả tool mà khách chưa nói ra.
- Thao tác ghi (`create`, `update`, `http`) mặc định `requiresConfirmation: true`: bot đọc lại tóm tắt và chỉ ghi khi khách đồng ý rõ. Đặt `false` cho thao tác ghi nhận nội bộ không cần khách xác nhận (ghi kết quả cuộc gọi, tạo lead mới).
- Tool hệ thống: `set_outcome` (kết quả có kiểu + việc chiến dịch làm tiếp), `end_call`, `switch_to_consultant` (chuyển hàng đợi đã khai báo).
- `http` (POST ra API ngoài, có `basic`/`hmac`) và `cogover_agent` (hỏi một AI Agent Cogover) khi dữ liệu nằm ngoài Object.

### 4. Guardrail

Đưa vào kịch bản những gì nền tảng chưa cưỡng chế, và chọn cấu hình chặn được bằng hệ thống:

| Rủi ro | Cách chặn |
|---|---|
| Lộ thông tin cho người khác | Tool đọc luôn giới hạn theo số khách; kịch bản bắt xác minh danh tính trước khi nói dữ liệu nhạy cảm, không tự đọc dữ liệu xác minh |
| Ghi sai | `requiresConfirmation`, `writableFields` tối thiểu, tham số mô tả đúng định dạng |
| Ngôn từ đe doạ, hứa hẹn ngoài thẩm quyền | Danh sách điều cấm cụ thể trong kịch bản; chuyển người thật hoặc hẹn gọi lại |
| Cuộc gọi kéo dài, vòng lặp tool | `maxDurationSec` (30–1800), `silenceTimeoutSec` (5–120), `maxToolCalls` (1–50) |
| Ghi âm | `recordEnabled: true` và nói rõ trong lời chào |
| Khung giờ gọi | Đặt lịch chạy của chiến dịch gọi ra; kịch bản chỉ hẹn gọi lại trong khung giờ cho phép |

### 5. Tạo bằng spec

Viết spec JSON gồm `callbot` (body của `create_callbot`), `tools[]` (body của `create_tool`) và `status` (`active`/`disabled`). Ví dụ đầy đủ: [assets/collections-spec.example.json](assets/collections-spec.example.json).

```bash
python3 scripts/callbot_api.py apply spec.json          # in kế hoạch, không ghi
python3 scripts/callbot_api.py apply spec.json --apply  # tạo/cập nhật, đọc lại cấu hình cuối
```

`runAsPersonnelId` là nhân sự mà tool `cogover_object` chạy dưới quyền (thiếu thì tool trả "chưa được cấu hình"); phải là nhân sự đang hoạt động của Workspace (`403 run_as_forbidden`). Thay ID mẫu trong spec ví dụ trước khi `--apply`; dry-run không kiểm tra giá trị này. Chỉ gán chính người cấu hình hoặc nhân sự có quyền tối thiểu trên Object cần dùng; chốt với người dùng trước khi gán. Callbot mới tạo ở trạng thái `active`.

## C. Kiểm thử

Chi tiết lệnh và cách đọc kết quả: [Kiểm thử](references/testing.md). Bằng chứng chính cho ngôn ngữ/nhận dạng giọng nói, kết thúc cuộc gọi và ghi dữ liệu là cuộc gọi thật (bước 2–3); mô phỏng chỉ để rà kịch bản.

1. **Mô phỏng hội thoại (text):** `simulate --callbot ID --say "..." --say "..."`. Số khách của phiên là số điện thoại đầu tiên trong hồ sơ nhân sự của người gọi API; tool đọc chạy thật, tool ghi chỉ chạy thử (`dry-run`) nhưng vẫn đi qua bước đọc lại và xác nhận. Mô phỏng dùng model text của nền tảng, không dùng model/giọng của callbot và bỏ qua nhiều chặn lúc chạy: chỉ dùng để rà kịch bản và tham số tool (xác minh sai, đổi ý khi xác nhận, ngoài phạm vi, chèn lệnh). Giới hạn 10 phiên/giờ mỗi project.
Trước bước 2–3, xác nhận signing key của project đã có giá trị (`projectSigningKey` là `existing`/`created`, bước A.5). Nếu bot im lặng, đọc log pod `stringeex-callbot` để phân biệt nguyên nhân:
- `NO_SECRET`: thiếu signing key;
- `rejected by billing: insufficient_credit`: Workspace hết credit AI;
- `is not portal admin`: thiếu quyền admin Call Center.

2. **Gọi thử (thoại):** `rpc test_call --callbot ID --body '{}'` gọi tới số trong hồ sơ nhân sự của người thao tác qua hotline của project; cần hồ sơ có số và project có hotline gọi ra được. Chỉ gọi khi người dùng biết máy nào sẽ đổ chuông.
3. **Cuộc gọi thật:** gọi vào số hotline có node IVR "Kết nối callbot" trỏ tới callbot, hoặc chạy chiến dịch gọi ra.
4. **Kiểm chứng:** `sessions --callbot ID` rồi `session SESSION_ID` (transcript, tool đã gọi và trạng thái, outcome, cờ an ninh); sau đó đọc lại bản ghi bằng [$object-record](../object-record/SKILL.md) để xác nhận field đã ghi đúng. Chỉ báo đạt khi bản ghi đổi đúng, không dựa vào lời bot nói.

## Bàn giao

Nêu ID/tên callbot, provider/model/giọng/ngôn ngữ, danh tính thực thi, danh sách tool (Object, action, field ghi, có cần xác nhận), outcome và việc chiến dịch làm tiếp, guardrail đã đặt, trạng thái signing key của project ("đã có" / "đã tạo mới" / "thiếu, chờ quản trị DB"). Liệt kê ca kiểm thử đã chạy kèm bằng chứng (session ID, giá trị field trước/sau), ca chưa kiểm được và lý do (chưa có hotline, chưa có số trong hồ sơ...), dữ liệu test đã tạo. Không đưa API Key, cookie hay số điện thoại thật của khách vào báo cáo.
