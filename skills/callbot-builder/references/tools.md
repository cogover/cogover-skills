# Tool của callbot

Body của `create_tool`/`update_tool`:

```json
{"kind": "cogover_object", "name": "lookup_customer", "description": "...", "params": [], "config": {}}
```

| Trường | Ràng buộc |
|---|---|
| `kind` | `system`, `cogover_object`, `http`, `cogover_agent`; không đổi được sau khi tạo (xoá rồi tạo lại) |
| `name` | `^[a-z][a-z0-9_]{0,63}$`, duy nhất trong callbot; `end_call`, `set_outcome`, `switch_to_consultant` dành cho `system` |
| `description` | 1–1.000 ký tự: khi nào dùng và kết quả trả về; model chọn tool theo mô tả này |
| `params` | Tối đa 15 `{key, type: "string" \| "number", description ≤ 300}`; `key` theo `^[a-z][a-z0-9_]{0,63}$` (không dùng chữ hoa) |

Tối đa 20 tool mỗi callbot. Service trả `params` theo thứ tự khác lúc gửi; so sánh theo `key`.

## `cogover_object`

Đọc/ghi một Object cố định qua quyền của `runAsPersonnelId`. Model chỉ điền tham số đã khai báo; không có filter tự do, không có xoá.

```json
{
  "objectSlug": "lead",
  "action": "update",
  "callerScopeField": "mobile_phones",
  "paramFields": {"ptp_date": "promise_date", "summary": "call_summary"},
  "paramOps": {},
  "returnFields": ["collection_status"],
  "writableFields": ["promise_date", "call_summary"],
  "size": 1,
  "requiresConfirmation": true
}
```

| Khoá | Ý nghĩa |
|---|---|
| `action` | `search`, `count`, `get`, `create`, `update` |
| `paramFields` | Tham số → field slug; mọi khoá phải là `params[].key` |
| `paramOps` | Chỉ cho `search`/`count`: toán tử theo tham số (`=` mặc định, `!=`, `>`, `>=`, `<`, `<=`, `like`, `startswith`); không dùng toán tử khác `=` trên `callerScopeField` |
| `callerScopeField` | Field điện thoại của khách. Bắt buộc với `search`/`count`; service luôn thêm điều kiện field này bằng số khách, đè lên tham số của model |
| `returnFields` | ≤ 20 field model được thấy (luôn kèm `id`) |
| `writableFields` | ≤ 20 field được ghi; bắt buộc với `create`/`update`. Tham số map tới field ngoài danh sách bị bỏ qua |
| `size` | 1–5 bản ghi tối đa cho `search` |
| `requiresConfirmation` | Chỉ có nghĩa với `create`/`update`; mặc định `true` |

Hành vi lúc chạy:

- Số khách: gọi ra là số được gọi, gọi vào là số gọi đến, mô phỏng là số trong hồ sơ nhân sự của người chạy mô phỏng (không có số thì tool trả lỗi tra cứu `adapter_400`). Service gửi nguyên số này làm điều kiện `=` trên field điện thoại. Đã kiểm chứng: số Việt Nam lưu `+84...` khớp khi lọc bằng `84...` hoặc `0...`, nhưng số quốc gia khác thì không (cuộc gọi từ `91...` không tìm thấy bản ghi lưu `+91...`, bot đi nhánh tạo lead mới). Lưu số điện thoại đúng định dạng tổng đài/dialer gửi sang (có thể lưu thêm dạng đó vào field nhiều giá trị) và gọi thử một cuộc từ số thật của quốc gia đó trước khi chạy chiến dịch.
- `search` không có kết quả trả câu "không tìm thấy" như kết quả bình thường; lỗi khi đọc/ghi dữ liệu trả mã dạng `adapter_<r>` ("hệ thống tạm thời không tra cứu được"), ví dụ `adapter_400` khi Object chưa nhận field vừa thêm.
- `update` có `callerScopeField` và model không gửi `id`: service tự tìm bản ghi của chính người gọi (bản ghi cập nhật gần nhất). Không tìm thấy thì báo lỗi, không tạo mới. `get`/`update` với `id` chỉ chấp nhận id đã xuất hiện trong phiên.
- `create` chỉ ghi các field trong `writableFields` mà model gửi; field bắt buộc của Object (ví dụ `name`, `last_name` của Lead) phải có trong tham số. Field điện thoại nhận chuỗi.
- Thiếu `runAsPersonnelId` hoặc thiếu `callerScopeField` ở `search`/`count`: tool trả "chưa được cấu hình".

### Thiết kế field cho callbot

- Giá trị tool trả về đi thẳng vào model: `date` và `date_time` trả về dạng timestamp (ms) nên model không đọc đúng. Thông tin bot phải đọc cho khách (ngày đến hạn...) để ở field văn bản, ví dụ "25 October 2026"; giữ field `date` cho báo cáo và lọc.
- Ghi ngày từ bot vào field `date` bằng chuỗi `YYYY-MM-DD` (tham số `string`). Tránh để bot ghi `date_time` (cần timestamp ms); giờ hẹn để ở field văn bản `HH:mm` hoặc dùng tool `http`/Custom Module để quy đổi.
- Field lựa chọn nhận slug option: liệt kê đúng slug trong `description` của tham số, ví dụ `One of: ptp, callback, paid`. Model có thể điền giá trị ngoài danh sách; field quan trọng thì dùng tham số riêng cho mỗi tool với giá trị cố định trong mô tả ("Always ptp").
- Mỗi kết quả cần lọc/báo cáo một field riêng (trạng thái, ngày hẹn, số tiền); thêm một field `long_text` tóm tắt cuộc gọi.
- Dữ liệu dùng để xác minh danh tính (4 số cuối tài khoản...) trả cho model để so khớp; kịch bản cấm đọc ra.

## `system`

| `name` | `config` | Ghi chú |
|---|---|---|
| `end_call` | — | Bot gọi sau khi chào tạm biệt; tham số `reason`: `normal`, `announcement`, `voicemail`, `wrong_person` |
| `set_outcome` | `{"outcomes": [{"value", "description", "campaignAction"}], "fields": [...]}` | `value` theo `^[a-z][a-z0-9_]{0,31}$`, mô tả cắt ở 300 ký tự, ≤ 20 outcome; `campaignAction`: `done`, `callback`, `retry`, `do_not_call`, `none`. `fields` (≤ 10, `key`, `type`: `string`/`number`/`boolean`/`datetime`, `required`, `enum`, `maxLength`) để trích thêm dữ liệu. Outcome có `campaignAction: do_not_call` chỉ được nhận khi chính khách yêu cầu trong cuộc gọi, và phải qua bước khách xác nhận như thao tác ghi |
| `switch_to_consultant` | `{"queues": ["Tên hàng đợi"]}` (1–20 tên) | Chuyển cuộc gọi sang hàng đợi agent; thiếu `queues` thì không tạo được |

Kết quả `set_outcome` gắn vào phiên (`outcome`) và cập nhật trạng thái khách trong chiến dịch gọi ra theo `campaignAction`.

## `http`

POST tới `url` (HTTPS công khai; địa chỉ nội bộ bị chặn), `auth`: `none`, `basic` (cần `username`, mật khẩu đặt bằng `put_tool_secret`), `hmac` (secret đặt bằng `put_tool_secret`). `timeoutMs` 500–5000. `config`: `{"requiresConfirmation": true, "responseFields": ["data.status"]}`; thiếu `responseFields` thì model chỉ thấy `{status, ok}`. Luôn là thao tác ghi.

## `cogover_agent`

`config`: `{"agentId": "{AGENT_ID}", "waitSeconds": 12}` (0–20, mặc định 12): chuyển câu hỏi cho một AI Agent Cogover (dựng bằng [$agent-builder](../../agent-builder/SKILL.md)) và chờ câu trả lời; `0` là gửi không chờ. Service tự thêm tham số `question` khi `params` để trống.

## Xác nhận thao tác ghi

Tool ghi có `requiresConfirmation` không ghi ngay: service trả bản tóm tắt, bot đọc lại và chờ khách đồng ý rõ, rồi gọi `confirm_pending` (tool do nền tảng tự thêm). Xác nhận ngay trong cùng lượt bị từ chối (`need_caller_reply`); thao tác chờ quá vài lượt hết hạn. Nếu khách đổi giá trị khi đang xác nhận, bot phải gọi lại tool ghi với giá trị mới.

## Chặn theo nguồn dữ liệu (cuộc gọi thật)

Nền tảng coi kết quả tool là dữ liệu không tin cậy (không phải yêu cầu của khách) và có thể từ chối thao tác dựa trên dữ liệu đó (lỗi `blocked_untrusted_data`). Mô phỏng không áp dụng cơ chế này, nên chỉ thấy được khi gọi thật.

- **Ghi lại giá trị lấy từ tool:** lệnh ghi (kể cả `requiresConfirmation: false`) có thể bị chặn khi tham số chép giá trị từ kết quả tool mà khách chưa nói ra trong cuộc gọi. Ví dụ tra cứu trả ngôn ngữ ưu tiên `"bengali"`, rồi bot ghi lại đúng giá trị đó trong khi khách nói bằng chữ Bengali. Cách thiết kế: tool tra cứu chỉ trả field bot thật sự cần; tool ghi để `returnFields: []`; tóm tắt do bot tự viết, không chép văn bản từ hồ sơ.
- **Kết thúc ngay sau kết quả tool:** `end_call` gọi ngay sau một kết quả tool trong cùng lượt khách có thể bị chặn nếu khách chưa thể hiện ý muốn kết thúc. Kịch bản nên ghi kết quả và `set_outcome` trước, chào và chờ khách đáp, rồi mới kết thúc ở lượt sau.

## Giới hạn mỗi cuộc gọi

- Nền tảng giới hạn số lệnh ghi được thực thi trong một cuộc gọi (hiện là 3, tính cả `create`/`update`/`http`). Thiết kế luồng để mỗi cuộc gọi ghi ít lần: ví dụ hẹn trả nợ (1) + ghi kết quả (1), chừa chỗ cho khách đổi ý.
- Tổng số lần gọi tool không vượt `maxToolCalls` của callbot; nền tảng cũng giới hạn tần suất gọi tool và tạm tắt tool khi lỗi lặp lại nhiều lần trong một cuộc gọi.
