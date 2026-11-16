# Tool của callbot

Body của `create_tool`/`update_tool`:

```json
{"kind": "cogover_object", "name": "lookup_customer", "description": "...", "params": [], "config": {}}
```

| Trường | Ràng buộc |
|---|---|
| `kind` | `system`, `cogover_object`, `cogover_task`, `http`, `cogover_agent`; không đổi được sau khi tạo (xoá rồi tạo lại, kể cả cùng tên) |
| `name` | `^[a-z][a-z0-9_]{0,63}$`, duy nhất trong callbot; `end_call`, `set_outcome`, `switch_to_consultant` dành cho `system`; `cogover_task` bỏ trống thì là `create_task` |
| `description` | 1–1.000 ký tự: khi nào dùng và kết quả trả về; model chọn tool theo mô tả này |
| `params` | Tối đa 15 `{key, type: "string" \| "number", description ≤ 300}`; `key` theo `^[a-z][a-z0-9_]{0,63}$` (không dùng chữ hoa). Hồ sơ ghi v2 và `cogover_task` bỏ qua `params` gửi lên: tham số sinh từ `config` |

Tối đa 20 tool mỗi callbot. Service trả `params` theo thứ tự khác lúc gửi; so sánh theo `key`. Xem hàm tool đúng như model nhận (tên, mô tả, JSON schema tham số) bằng `rpc get_tool_function --callbot ID --tool TOOL_ID`.

Chọn loại tool ghi:

| Cần | Dùng |
|---|---|
| Tạo một bản ghi bất kỳ (ticket, task, cơ hội, yêu cầu...) với field cố định, field hệ thống tự gắn (khách, số gọi), người phụ trách chọn trong danh sách | **Hồ sơ ghi v2** (`cogover_object`, `v: 2`, `action: create`): mặc định cho mọi lệnh tạo mới |
| Task gọi lại kiểu cũ (tham số cố định `title`, `due_at`, `assignee`...) | `cogover_task` (vẫn chạy; tool mới nên dùng hồ sơ ghi với mẫu Task gọi lại) |
| Sửa bản ghi bot vừa tạo trong chính cuộc gọi bằng tool `create` kiểu cũ | `cogover_object` `update` (không áp dụng cho lead/contact/account; bản ghi tạo bằng hồ sơ ghi không sửa được vì bot không nhận id) |
| Ghi ra hệ thống ngoài | `http` |

Bot **không sửa được lead, contact, account** (hồ sơ khách): `update` trên các Object này bị từ chối khi lưu tool (`400 invalid_params`) và khi chạy. Kết quả cuộc gọi đưa vào `set_outcome` (lưu ở phiên và chiến dịch) hoặc tạo bản ghi riêng (task, ticket...) gắn với khách; cần đổi trạng thái lead theo kết quả thì dùng Process ngoài callbot.

## `cogover_object`

Đọc/ghi một Object cố định qua quyền của `runAsPersonnelId`. Model chỉ điền tham số đã khai báo; không có filter tự do, không có xoá.

```json
{
  "objectSlug": "ticket",
  "action": "search",
  "callerScopeField": "phone_number",
  "paramFields": {},
  "paramOps": {},
  "returnFields": ["serial", "name", "status", "created"],
  "writableFields": [],
  "size": 3
}
```

| Khoá | Ý nghĩa |
|---|---|
| `action` | `search`, `count`, `get`, `create`, `update` |
| `paramFields` | Tham số → field slug; mọi khoá phải là `params[].key` |
| `paramOps` | Chỉ cho `search`/`count`: toán tử theo tham số (`=` mặc định, `!=`, `>`, `>=`, `<`, `<=`, `like`, `startswith`); không dùng toán tử khác `=` trên `callerScopeField` |
| `callerScopeField` | Field điện thoại của khách. Bắt buộc với `search`/`count`; service luôn thêm điều kiện field này bằng số khách, đè lên tham số của model |
| `returnFields` | ≤ 20 field model được thấy (luôn kèm `id`) |
| `writableFields` | ≤ 20 field được ghi; bắt buộc với `create`/`update` kiểu cũ. Tham số map tới field ngoài danh sách bị bỏ qua |
| `size` | 1–5 bản ghi tối đa cho `search` |
| `requiresConfirmation` | Chỉ có nghĩa với `create`/`update` kiểu cũ; mặc định `true` |

Hành vi lúc chạy:

- Số khách: gọi ra là số được gọi, gọi vào là số gọi đến, mô phỏng là số trong hồ sơ nhân sự của người chạy mô phỏng (không có số thì tool trả lỗi tra cứu `adapter_400`). Service gửi nguyên số này làm điều kiện `=` trên field điện thoại. Đã kiểm chứng: số Việt Nam lưu `+84...` khớp khi lọc bằng `84...` hoặc `0...`, nhưng số quốc gia khác thì không (cuộc gọi từ `91...` không tìm thấy bản ghi lưu `+91...`, bot đi nhánh tạo lead mới). Lưu số điện thoại đúng định dạng tổng đài/dialer gửi sang (có thể lưu thêm dạng đó vào field nhiều giá trị) và gọi thử một cuộc từ số thật của quốc gia đó trước khi chạy chiến dịch.
- `search` không có kết quả trả câu "không tìm thấy" như kết quả bình thường; lỗi khi đọc/ghi dữ liệu trả mã dạng `adapter_<r>` ("hệ thống tạm thời không tra cứu được"), ví dụ `adapter_400` khi Object chưa nhận field vừa thêm.
- `update` chỉ sửa bản ghi **bot đã tạo trong chính cuộc gọi bằng tool `create` kiểu cũ** và luôn cần `id` (id tool đó trả về; hồ sơ ghi không trả id nên không sửa được). Không còn tự tìm bản ghi của người gọi theo `callerScopeField`; id lấy từ kết quả tra cứu nhưng không phải bot tạo bị từ chối. `get` chỉ nhận id đã xuất hiện trong phiên.
- `create` kiểu cũ chỉ ghi các field trong `writableFields` mà model gửi; field bắt buộc của Object phải có trong tham số. Gặp lỗi mạng/hết giờ, service gửi lại cùng một khoá chống trùng nên không tạo hai bản ghi cho một lần xác nhận.
- Thiếu `runAsPersonnelId` hoặc thiếu `callerScopeField` ở `search`/`count`: tool trả "chưa được cấu hình".

### Hồ sơ ghi v2 (write profile)

Một tool = **tạo một bản ghi** của một Object cố định. Với mỗi field, chọn nguồn giá trị; service sinh tham số cho model từ các field bot hỏi/chọn, kiểm tra kiểu/độ dài/lựa chọn theo schema Object, và **luôn** đọc lại cho khách xác nhận trước khi tạo (không tắt được). Đây là cách đọc/ghi được kiểm chứng trên Workspace thật cho ticket, task gọi lại (activity) và lead.

```json
{
  "kind": "cogover_object",
  "name": "tao_yeu_cau_ho_tro",
  "description": "Tạo yêu cầu hỗ trợ",
  "config": {
    "v": 2,
    "objectSlug": "ticket",
    "action": "create",
    "objectLabel": "yêu cầu hỗ trợ",
    "maxPerSession": 2,
    "maxPerNumberPerDay": 5,
    "fields": {
      "name": {"source": "bot", "param": "tieu_de", "label": "Tiêu đề", "required": true, "maxLength": 120},
      "description": {"source": "bot", "param": "mo_ta", "label": "Mô tả", "required": true, "maxLength": 500},
      "type": {"source": "bot", "param": "loai", "label": "Loại yêu cầu", "required": true, "options": ["problem", "request", "question"]},
      "status": {"source": "fixed", "value": "new"},
      "origin": {"source": "fixed", "value": "phone"},
      "phone_number": {"source": "server", "value": "call.number"},
      "contact": {"source": "server", "value": "caller.contact"}
    }
  }
}
```

Khoá cấp `config`:

| Khoá | Ràng buộc |
|---|---|
| `v` | `2`. Không dùng chung với `paramFields`/`writableFields` |
| `objectSlug`, `action` | `action` luôn `create` |
| `objectLabel` | Tên bản ghi trong câu đọc lại ("Tạo yêu cầu hỗ trợ: ..."); bỏ trống thì lấy nhãn Object |
| `maxPerSession` | 1–3, mặc định 1: số bản ghi tool này tạo được mỗi cuộc gọi |
| `maxPerNumberPerDay` | 1–20, mặc định 3: số bản ghi mỗi số gọi mỗi ngày (theo múi giờ callbot) |
| `fields` | 1–30 field; tối đa 15 field nguồn `bot`/`choice`; tối đa một field `callSummary` |

Nguồn của từng field:

| `source` | Khoá | Dùng cho |
|---|---|---|
| `bot` | `param` (tên tham số, không phải `id`), `label` (bắt buộc, 1–80 ký tự, không chứa `[ ] { } < >`, đọc cho khách), `required`, `maxLength` (field văn bản, ≤ 1.000 và ≤ giới hạn field), `options` (field lựa chọn: tập con slug option đang bật), `range` (`future`/`past` cho `date`/`date_time`), `sensitive`, `appendCallNumber`, `callSummary` | Thông tin khách nói: văn bản ngắn/dài, email, điện thoại, regex, số, boolean, lựa chọn đơn, ngày, ngày giờ |
| `fixed` | `value`, `label` + `readback: true` nếu muốn đọc cho khách | Giá trị đặt sẵn: trạng thái, kênh, loại task |
| `server` | `value`: `caller.contact`, `caller.lead`, `caller.account` (lookup), `call.number` (`phone`/`short_text`), `session.id`, `now` (`date`/`date_time`), `run_as` (lookup nhân sự) | Gắn khách đang gọi, số gọi, thời điểm; model không điền được |
| `choice` | `param`, `label` (bắt buộc), `choices[]` (1–10 `{key, label, description ≤ 200, value}`), `default` | Bot chọn trong danh sách, ví dụ người phụ trách theo nhu cầu |

- Hai field cùng kiểu (không phải lựa chọn, cùng các cờ `sensitive`/`appendCallNumber`/`callSummary`) dùng chung một `param` thì bot hỏi một lần, ghi vào cả hai: ví dụ `time` và `activity_time` của task, `name` và `last_name` của lead. Giới hạn 15 tính theo số tham số khác nhau. Field `fixed` kiểu `date_time` hoặc lookup không được đọc lại dù bật `readback`.
- `appendCallNumber` (chỉ `short_text`): thêm ` – +84…` (số thật của cuộc gọi) vào cuối giá trị; bot không đọc số này. `callSummary` (chỉ `long_text` hiển thị HTML, như `content` của activity): service ghi tóm tắt gồm số gọi, các thông tin bot đã hỏi, lời khách ở field này, mã phiên và lưu ý "chưa xác minh". Không dùng hai cờ này cùng `sensitive`.
- `sensitive`: giá trị được che trong log, transcript lưu ở callbot và transcript gửi về Cogover; câu đọc lại chỉ đọc 4 ký tự cuối. Bot vẫn có thể nói giá trị trong cuộc gọi, bản ghi tạo ra vẫn chứa giá trị thật.
- Giá trị `fixed`/`choice` theo kiểu field: văn bản là chuỗi, số là số, lựa chọn là slug option, `date` là `YYYY-MM-DD`, `date_time` là epoch ms, `time_duration` là **mili giây** (nhắc trước 15 phút = `900000`, tối đa 30 ngày), lookup nhân sự là `{"personnelEmail": "..."}` (email nhân sự đang hoạt động), lookup khác là `{"recordId": "..."}`.
- Ngày giờ do bot điền là **giờ địa phương theo múi giờ callbot**, dạng `yyyy-MM-ddTHH:mm` (không ghi offset); service quy đổi và kiểm tra giờ không tồn tại khi đổi giờ mùa hè. Field `date` nhận `YYYY-MM-DD`. Không cần ép bot tính epoch hay offset.
- Field bắt buộc của Object (không có giá trị mặc định) phải có trong `fields`, kể cả field bắt buộc riêng của Workspace (ví dụ `currency` của lead): thiếu thì lưu tool bị từ chối và báo tên field.
- Khi lưu tool, service đọc schema Object bằng quyền run-as và lưu kèm (`snapshot`). Đổi field/option của Object sau đó thì lưu lại tool (`apply --resave-tools`). Đọc trước field, kiểu, option đang bật bằng `rpc get_object_fields --callbot ID --object SLUG` (cùng quyền run-as): `403 permission_denied` là run-as không đọc được Object, `404 object_not_found` là sai slug.
- Không tìm được khách (số ẩn, trùng nhiều khách, chưa có hồ sơ) thì field `caller.*` bỏ trống; field đó bắt buộc thì bản ghi không được tạo.
- Sau cuộc gọi, bản ghi đã tạo được gắn vào `call_log` của cuộc gọi nếu Object có lookup tới `call_log` đang trống, và được liệt kê trong NOTE "Callbot" của cuộc gọi.

Luồng chạy: bot gọi tool → service kiểm từng tham số; sai (thiếu, quá dài, sai lựa chọn, ngày đã qua...) thì trả `invalid_args` kèm `message` để bot hỏi lại khách đúng thông tin đó → hợp lệ thì giữ lệnh và trả `need_confirmation` kèm câu đọc lại (nhãn Object, từng field bot hỏi/chọn theo `label`, field `fixed` có `readback`) → bot đọc và hỏi khách một lần → khách đồng ý ở lượt sau thì bot gọi `confirm_pending` → tạo xong bot chỉ nhận "Đã tạo <nhãn>" (không có mã bản ghi). Câu đọc lại quá 800 ký tự bị từ chối: rút bớt field hoặc `maxLength`. Câu trả lời lỗi đã được duyệt: không có quyền/vượt giới hạn thì bot báo chưa ghi được và nhân viên sẽ liên hệ; không rõ kết quả (504) thì bot báo đã ghi nhận và tool bị khoá đến hết cuộc gọi.

Mẫu Task gọi lại (tạo activity như `cogover_task`): `name` ← bot `title` (`appendCallNumber`), `time` + `activity_time` ← bot `due_at` (`range: future`), `content` ← bot `description` (`callSummary`), `task_priority` ← bot `priority`, `activity_type` = `task`, `task_type` = `call` (Workspace không có thì `to_do`), `status` = `todo`, `reminder_before_due` = `900000`, `task_assigned_to` ← `choice` theo email nhân sự, `contacts`/`lead`/`accounts` ← `caller.contact`/`caller.lead`/`caller.account`. Ví dụ chạy được: tool `dat_lich_tu_van` trong [assets/vi-an-phat/an-phat-telesale.spec.json](../assets/vi-an-phat/an-phat-telesale.spec.json).

### Thiết kế field cho callbot

- Giá trị tool đọc trả về đi thẳng vào model: `date` và `date_time` trả về dạng timestamp (ms) nên model không đọc đúng. Thông tin bot phải đọc cho khách (ngày đến hạn...) để ở field văn bản, ví dụ "25 October 2026"; giữ field `date` cho báo cáo và lọc.
- Ghi ngày giờ: dùng hồ sơ ghi v2 (bot gửi giờ địa phương `yyyy-MM-ddTHH:mm`). Tool `create`/`update` kiểu cũ không quy đổi giờ: chỉ ghi `date` bằng `YYYY-MM-DD`, tránh `date_time`.
- Field lựa chọn: hồ sơ ghi v2 tự đưa danh sách slug hợp lệ vào tham số (`options`) và đọc nhãn option khi xác nhận. Với tool kiểu cũ, liệt kê đúng slug trong `description` của tham số, và field quan trọng thì dùng giá trị cố định.
- Mỗi kết quả cần lọc/báo cáo nên là một field riêng của bản ghi tạo ra, hoặc một field của `set_outcome`.
- Dữ liệu dùng để xác minh danh tính (4 số cuối tài khoản...) trả cho model để so khớp; kịch bản cấm đọc ra.

## `cogover_task`

Tạo task gọi lại trong CRM với tham số cố định (`title`, `due_at`, `description`, `assignee`, `priority`, `task_type`, `reminder_before_minutes`, `customer_name`, `callback_number`), luôn cần khách xác nhận. `config`: `assignees` (1–10 `{key, email, description ≤ 200}`), `defaultAssignee`, `maxPerSession` (1–3), `maxPerNumberPerDay` (1–20), `taskType` (mặc định `call`). Tool cũ vẫn chạy; tool mới dùng hồ sơ ghi v2 với mẫu Task gọi lại để chọn được field và Object.

## `system`

| `name` | `config` | Ghi chú |
|---|---|---|
| `end_call` | — | Bot gọi sau khi chào tạm biệt; tham số `reason`: `normal`, `announcement`, `voicemail`, `wrong_person` |
| `set_outcome` | `{"outcomes": [{"value", "description", "campaignAction"}], "fields": [...]}` | `value` theo `^[a-z][a-z0-9_]{0,31}$`, mô tả cắt ở 300 ký tự, ≤ 20 outcome; `campaignAction`: `done`, `callback`, `retry`, `do_not_call`, `none`. `fields` (≤ 10, `key`, `type`: `string`/`number`/`boolean`/`datetime`, `required`, `enum`, `maxLength`, `description`) để trích thêm dữ liệu. `datetime` nhận ISO 8601; không ghi offset (`2026-11-16T15:00`) thì hiểu theo múi giờ callbot. Field `datetime` tên **`callback_at`** (hoặc `callback_time`) là thời điểm chiến dịch gọi lại khi outcome có `campaignAction: callback`; đặt tên khác thì chiến dịch không nhận giờ. Outcome có `campaignAction: do_not_call` chỉ được nhận khi chính khách yêu cầu trong cuộc gọi, và phải qua bước khách xác nhận như thao tác ghi |
| `switch_to_consultant` | `{"queues": ["Tên hàng đợi"]}` (1–20 tên) | Chuyển cuộc gọi sang hàng đợi agent; thiếu `queues` thì không tạo được |

Kết quả `set_outcome` gắn vào phiên (`outcome`) và cập nhật trạng thái khách trong chiến dịch gọi ra theo `campaignAction`. Gọi `set_outcome` với tham số sai (thiếu field `required`, ngoài `enum`) thì cả lệnh bị từ chối và bot nhận `message` lỗi: viết kịch bản rõ giá trị cho từng field, và dặn chỉ gửi field khách đã trả lời.

## `http`

POST tới `url` (HTTPS công khai; địa chỉ nội bộ bị chặn), `auth`: `none`, `basic` (cần `username`, mật khẩu đặt bằng `put_tool_secret`), `hmac` (secret đặt bằng `put_tool_secret`). `timeoutMs` 500–5000. `config`: `{"requiresConfirmation": true, "responseFields": ["data.status"]}`; thiếu `responseFields` thì model chỉ thấy `{status, ok}`. Luôn là thao tác ghi.

## `cogover_agent`

`config`: `{"agentId": "{AGENT_ID}", "waitSeconds": 12}` (0–20, mặc định 12): chuyển câu hỏi cho một AI Agent Cogover (dựng bằng [$agent-builder](../../agent-builder/SKILL.md)) và chờ câu trả lời; `0` là gửi không chờ. Service tự thêm tham số `question` khi `params` để trống.

## Xác nhận thao tác ghi

Tool ghi cần xác nhận không ghi ngay: service trả `need_confirmation` kèm câu đọc lại, bot đọc lại và chờ khách đồng ý rõ, rồi gọi `confirm_pending` (tool do nền tảng tự thêm; mô tả bằng tiếng Anh khi callbot không nói tiếng Việt). Xác nhận ngay trong cùng lượt bị từ chối (`need_caller_reply`); thao tác chờ quá vài lượt hết hạn. Nếu khách đổi giá trị khi đang xác nhận, bot phải gọi lại tool ghi với giá trị mới.

Kinh nghiệm viết kịch bản cho tool ghi (đã gặp khi dựng và mô phỏng):

- Bảo bot gọi tool **ngay khi đủ thông tin bắt buộc**, không tự hỏi "anh có muốn tạo không" hay tự đọc lại trước: hệ thống đã đọc lại. Liệt kê rõ thông tin nào bắt buộc, thông tin nào chỉ là thêm; dặn không hỏi lại điều khách đã nói.
- Cấm nói "em đã ghi nhận", "kỹ thuật sẽ liên hệ" khi tool chưa xác nhận thành công.
- Thời gian hẹn: bắt bot hỏi khách, không tự chọn hay gợi ý sẵn một giờ; quy "thứ Năm", "chiều mai" ra ngày cụ thể và đọc lại.
- Tiêu đề/mô tả do bot tự viết theo lời khách, không chèn tên, danh xưng hay dữ liệu lấy từ tool tra cứu (xem mục dưới).
- Cho bot cách đọc nhãn option bằng ngôn ngữ của khách nếu nhãn option của Object là tiếng khác (ví dụ "Problem = sự cố").

## Chặn theo nguồn dữ liệu (cuộc gọi thật)

Nền tảng coi kết quả tool là dữ liệu không tin cậy (không phải yêu cầu của khách) và có thể từ chối thao tác dựa trên dữ liệu đó (lỗi `blocked_untrusted_data`). Mô phỏng không áp dụng cơ chế này, nên chỉ thấy được khi gọi thật.

- **Ghi lại giá trị lấy từ tool:** lệnh ghi có thể bị chặn khi tham số chép giá trị từ kết quả tool mà khách chưa nói ra trong cuộc gọi. Ví dụ tra cứu trả ngôn ngữ ưu tiên `"bengali"`, rồi bot ghi lại đúng giá trị đó trong khi khách nói bằng chữ Bengali; hoặc tra cứu trả tên khách rồi bot đưa tên vào tiêu đề. Cách thiết kế: tool tra cứu chỉ trả field bot thật sự cần; gắn khách bằng nguồn `server` (`caller.contact`/`caller.lead`) thay vì để bot chép tên/id; tóm tắt do bot tự viết, không chép văn bản từ hồ sơ.
- **Kết thúc ngay sau kết quả tool:** `end_call` trong cùng lượt khách với một kết quả tool có dữ liệu (tra cứu, `create` kiểu cũ, `http`, `cogover_agent`) bị chặn, trừ khi câu cuối của khách là lời chào tạm biệt. Hồ sơ ghi và `set_outcome` không gây chặn. Kịch bản nên ghi kết quả và `set_outcome` trước, hỏi khách còn cần gì, và khi khách chào/không cần gì thêm thì chào ngắn **và** gọi `end_call` ngay trong lượt đó (thiếu câu này bot hay chào mà không kết thúc).

## Giới hạn mỗi cuộc gọi

- Tối đa 3 lệnh ghi được thực thi mỗi cuộc gọi, dùng chung cho mọi tool ghi (`create`/`update`/`http`/`cogover_task`/hồ sơ ghi). Thêm vào đó, mỗi tool hồ sơ ghi/`cogover_task` có `maxPerSession` và `maxPerNumberPerDay` riêng. Thiết kế mỗi cuộc gọi chỉ một lệnh ghi chính, chừa chỗ cho khách đổi ý.
- Tổng số lần gọi tool không vượt `maxToolCalls` của callbot; nền tảng cũng giới hạn tần suất gọi tool và tạm tắt tool khi lỗi lặp lại nhiều lần trong một cuộc gọi.

## Sarvam Voice Agents (`sarvam_agent`)

Tool chạy qua webhook của callbot nhưng phải khai báo bằng tay trên Sarvam: sau khi tạo/sửa tool, lấy hàm bằng `get_tool_function` và tạo API tool **cùng tên** trên Sarvam (`POST <public_base_url>/callbot/v1/providers/sarvamagent/tools/<callbotId>/<tên tool>`, header `Authorization: Bearer <tool token của callbot>`, id phiên qua header `X-Callbot-Session: {{system_session_id}}` hoặc field `system_session_id` trong body, tham số dạng phẳng). Callbot có lệnh ghi cần xác nhận thì tạo thêm tool `confirm_pending` (body chỉ có id phiên) và dặn trong prompt Sarvam: khi tool trả `need_confirmation` thì đọc nguyên văn, chờ khách đồng ý rồi mới gọi `confirm_pending`. Hàm `confirm_pending` lấy bằng `get_tool_function --tool confirm_pending`. Mỗi lần sửa tool trong callbot phải dán lại hàm lên Sarvam.
