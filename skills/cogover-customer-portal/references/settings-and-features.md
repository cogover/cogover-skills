# Cấu hình chung và các tính năng

Mọi khối dưới đây nằm trong `settings` của `PUT config` ([admin-api.md](admin-api.md#put-config)). Nhắc lại hai quy tắc dễ sai:

1. Gửi **cả khối** (đọc `draft.<khối>`, sửa, gửi lại); khối gửi thiếu khoá sẽ mất khoá đó.
2. Lưu chỉ đổi nháp. Khách chỉ thấy thay đổi sau `POST publish`. Ba khối `lookups`, `chat`, `help` chỉ Super Admin được đổi (người khác gửi lại nguyên khối thì được coi là không đổi).

## Mục lục

- [Bảng điều kiện tiên quyết](#bảng-điều-kiện-tiên-quyết)
- [Thương hiệu, ngôn ngữ, phiên, hồ sơ](#thương-hiệu-ngôn-ngữ-phiên-hồ-sơ)
- [Mẫu thư mời](#mẫu-thư-mời)
- [Thông báo email](#thông-báo-email)
- [Công nợ](#công-nợ)
- [Đặt hàng](#đặt-hàng)
- [Việc cần làm](#việc-cần-làm)
- [Xác nhận số dư](#xác-nhận-số-dư)
- [Nhóm phía khách](#nhóm-phía-khách)
- [Tự đăng ký](#tự-đăng-ký)
- [Tra cứu không cần đăng nhập](#tra-cứu-không-cần-đăng-nhập)
- [Chat và AI Agent](#chat-và-ai-agent)
- [Gợi ý bài viết](#gợi-ý-bài-viết)
- [Tên miền riêng](#tên-miền-riêng)

## Bảng điều kiện tiên quyết

| Tính năng | Cần có trước | Không đủ thì gặp |
|---|---|---|
| Hoá đơn, báo giá, đơn hàng, hợp đồng, ticket trên cổng | Object tương ứng (app Finance/Sales) có field lookup tới `account`; layout xem cho khách | Preset `available: false`; xuất bản báo `invalid_account_field`, `invalid_layout` |
| Object tuỳ biến | Field lookup tới `account` (bắt buộc), lookup tới `contact` (nên có) | `invalid_account_field` |
| Trao đổi trên bản ghi | Object có quyền xem trên cổng; gói còn chỗ tạo Object | `conversation_requires_view`, `schema_ensure_failed` |
| Công nợ | Object `accounts_receivable` (Finance) có dữ liệu theo Tài khoản | Trang công nợ trống |
| Thông báo email (hoá đơn mới, ticket được trả lời, đơn được duyệt) | Hộp thư Workspace gửi được (`type` 1–4, `status` 1) | 422 `not_found` khi lưu hộp thư; xuất bản `sender_mailbox_required` |
| Đặt hàng | Object `order` đã ở trên cổng với `accountField = account`; bảng giá (`price_book`) có mục giá thật; sản phẩm `simple` | 422 `required` khi lưu; `ordering_*` khi xuất bản; khách thấy giá 0 hoặc không có hàng |
| Việc cần làm | Gói còn chỗ tạo Object `portal_task`; Process hoặc người tạo việc | `schema_ensure_failed` |
| Xác nhận số dư | Gói còn chỗ tạo Object `balance_confirmation` | 422 `objectSlug: schema_ensure_failed` khi thêm preset |
| Nhóm phía khách | Ít nhất một quản trị viên phía khách (`ADMIN`) | Không ai thấy mục Nhóm |
| Tự đăng ký | Hộp thư gửi được; nhân sự nhận hàng chờ (`defaultAssigneePersonnelId`); captcha của nền tảng | `sender_mailbox_required`, `self_registration_assignee_required` |
| Tra cứu không đăng nhập | Object có mã (`auto_number`/`short_text`) và SĐT hoặc email (trực tiếp hoặc qua lookup Liên hệ/Tài khoản); captcha | `invalid_lookup*` |
| Chat | App Omni Channel, một Trang Live Chat riêng cho cổng | 422 `chat.pageId: required`; khách không thấy nút chat |
| AI Agent trong chat | Agent có danh tính thực thi, đang bật, được router của Trang giao hội thoại | Agent không trả lời |
| Gợi ý bài viết | Site Builder có Site loại tài liệu và tên miền đã xác minh | `help_site_builder_missing`, `help_site_*` |
| Tên miền riêng | Cogover đã bật hạ tầng (`GET domains` → `configured: true`); quyền sửa DNS của tên miền | `CP_DOMAIN_NOT_CONFIGURED` |
| Mọi tính năng tạo Object (`portal_message`, `portal_task`, `balance_confirmation`, yêu cầu đăng ký) | Gói còn chỗ: số Object tuỳ biến và số field trên một Object chưa chạm trần | `schema_ensure_failed` (API không nêu lý do) |

Người thao tác: Super Admin làm được mọi bước. Nhân viên khác cần quyền "Thiết lập Customer Portal" và "Quản lý tài khoản portal" ([phân quyền](customer-access-and-operations.md#phân-quyền-nhân-viên)) và vẫn không được thêm/sửa Object trên cổng hay đổi `lookups`, `chat`, `help`, tên miền.

## Thương hiệu, ngôn ngữ, phiên, hồ sơ

```json
{"displayName": "Công ty Ví Dụ", "primaryColor": "#0E7C66",
 "supportEmail": "support@example.com", "supportPhone": "1900 0000",
 "defaultLanguage": "vi-VN", "languages": ["vi-VN", "en-US"],
 "session": {"idleMinutes": 1440, "maxDays": 30},
 "profile": {"editableFields": ["first_name", "mobile_phones", "job_title"]}}
```

| Khoá | Quy tắc (đã kiểm mã lỗi) |
|---|---|
| `displayName` | 1–100 ký tự, bắt buộc khi xuất bản (`display_name_required`) |
| `primaryColor` | `#RRGGBB` (`"red"` → `invalid_format`) |
| `supportEmail`, `supportPhone` | Hiện ở chân trang cổng; sai dạng → `invalid_format` |
| `languages`, `defaultLanguage` | Chỉ `vi-VN`, `en-US` (`fr-FR` → `invalid_option`) |
| `session` | `idleMinutes` 30–10.080 (mặc định 1.440), `maxDays` 1–90 (mặc định 30) |
| `profile.editableFields` | Field của `contact` khách được tự sửa ở trang Hồ sơ; không gồm `emails`, `account`, `owner`, field hệ thống, `portal_*` (`not_allowed`) |
| Logo | Chỉ qua `POST config/logo` ([admin-api.md](admin-api.md#post-configlogo)) |

## Mẫu thư mời

```json
{"invite": {"templates": {"vi-VN": {"subject": "Mời truy cập cổng {{portal_name}}",
  "body": "Chào {{contact_name}},\n{{account_name}} đã được mở cổng khách hàng.\nĐăng nhập: {{invite_link}}\nHỗ trợ: {{support_phone}}"}}}}
```

Văn bản thuần (thẻ HTML bị bỏ), tiêu đề một dòng ≤ 200 ký tự, thân ≤ 3.000 ký tự, bắt buộc có `{{invite_link}}` (thiếu → `invite.templates.vi-VN: invite_link_missing`). Biến được phép: `{{portal_name}}`, `{{contact_name}}`, `{{account_name}}`, `{{invite_link}}`, `{{support_email}}`, `{{support_phone}}`, `{{expires_at}}`. `{"invite": {"templates": {}}}` dùng mẫu hệ thống. Link mời dùng một lần, hạn 7 ngày.

## Thông báo email

```json
{"notifications": {"senderEmailWorkspaceId": "<MAILBOX_ID>",
  "invoiceNew": {"enabled": true, "objectKey": "invoice", "statuses": ["approved"]},
  "messageReply": {"enabled": true}, "orderReviewed": {"enabled": true}, "registration": {"enabled": true}}}
```

- `senderEmailWorkspaceId`: id hộp thư từ `mailboxes` của script (`sendable: true`). Hộp thư không gửi được → 422 `not_found`. Thông báo bật mà thiếu hộp thư → lưu được nhưng xuất bản 422 `sender_mailbox_required` (đã kiểm).
- `invoiceNew`: thư "hoá đơn mới" cho người dùng đang hoạt động của Tài khoản khi bản ghi của Object `objectKey` (khoá Object trên cổng) chuyển vào một trong `statuses` (slug option của `status`).
- `messageReply`: thư khi nhân viên trả lời công khai trên trao đổi.
- `orderReviewed`: thư khi nhân viên xác nhận/từ chối đơn từ cổng.
- `registration`: thư kết quả duyệt tự đăng ký (mặc định bật).
- Mã đăng nhập (OTP), thư mời và mã xác nhận hành động đi bằng email hệ thống của nền tảng, không cần hộp thư này. Thư không chứa số tiền; khách xem chi tiết trên cổng.
- Không kiểm được trên Workspace không có hộp thư gửi được; khi bàn giao ghi rõ "đã cấu hình, chưa kiểm thư tới khách" nếu chưa nhờ người dùng xác nhận.

## Công nợ

```json
{"statement": {"enabled": true, "label": {"vi-VN": "Công nợ", "en-US": "Statement"}, "menuOrder": 2}}
```

Tính từ `accounts_receivable` của Tài khoản đang chọn (tổng còn phải trả, quá hạn, danh sách theo khoảng ngày). Không phải mục Object; không có preset. Cổng chỉ bật công nợ (không Object nào) vẫn xuất bản được.

## Đặt hàng

```json
{"ordering": {"enabled": true, "orderObjectKey": "order", "defaultPriceBookId": "<PRICE_BOOK_ID>", "showStock": true,
  "productFilter": {"filters": [{"field": "can_be_sold", "op": "=", "params": 1, "fieldType": "boolean"}], "logic": "AND"}},
 "notifications": {"...": "giữ nguyên các khoá cũ", "orderReviewed": {"enabled": false}}}
```

1. Thêm Object `order` lên cổng bằng preset `order` (bộ lọc preset cho khách thấy cả đơn mình vừa gửi: `status not in [draft, creating]` OR `channel_source in [customer_portal]`), chọn layout, xuất bản. Option trạng thái mà bộ lọc này dùng có thể chưa tồn tại trước lần xuất bản đầu bật đặt hàng: lần xuất bản đó cổng tự thêm các option còn thiếu cho đơn hàng.
2. Bảng giá: dùng bảng giá có sẵn hoặc tạo `price_book` + `price_book_entry` bằng [$object-record](../../object-record/SKILL.md) (`price_per_unit`, `discount_percent`, `tax_percent`; field phần trăm lưu dạng phân số: `0.1` = 10%). Giá riêng "rẻ hơn N%": cách chắc chắn là tạo bảng giá riêng với `price_per_unit` đã giảm sẵn (đã kiểm); cách cổng áp `discount_percent` của mục giá chưa được kiểm, không dựa vào nó khi chưa thử với người dùng. Bảng giá riêng cho một Tài khoản: điền `account.portal_price_book` (field do cổng tạo khi bật đặt hàng); không có thì dùng `defaultPriceBookId`. Cần tạo sản phẩm thử: đọc metadata `product` bằng [$object-info](../../object-info/SKILL.md) và một sản phẩm có sẵn để biết field bắt buộc (loại sản phẩm, nhóm đơn vị, đơn vị, chính sách xuất hoá đơn...), không đoán.
3. `productFilter`: điều kiện lọc `product` cùng định dạng bộ lọc lưu ([portal-objects.md](portal-objects.md#điều-kiện-lọc-extrafilter)). Chỉ sản phẩm loại `simple` có giá trong bảng giá mới hiện.
4. `showStock`: hiện Còn/Hết hàng (chỉ hiển thị, hết hàng vẫn đặt được).
5. `orderReviewed.enabled: true` thì bắt buộc hộp thư gửi được; tắt thì không cần.

Lỗi đã kiểm: bật thiếu `orderObjectKey`/`defaultPriceBookId` → 422 `required`; `showStock: "yes"` → `invalid_format`. Khi xuất bản còn có `ordering_order_object_required`, `ordering_price_book_required`, `ordering_schema_unavailable`, `invalid_product_filter`, cảnh báo `ordering_order_filter_hides_portal_orders` (theo hợp đồng).

Đơn khách gửi vào `status = draft`, `channel_source = customer_portal`, chờ nhân viên xác nhận ([vận hành](customer-access-and-operations.md#xác-nhận-hoặc-từ-chối-đơn-từ-cổng)); giá, thuế tính lại ở máy chủ; người phụ trách = người phụ trách Tài khoản.

## Việc cần làm

```json
{"tasks": {"enabled": true, "formFields": ["response", "attachments"]}}
```

- Lần xuất bản đầu có `tasks.enabled` tạo Object `portal_task`. Mỗi bản ghi `portal_task` là một việc giao cho **một** Liên hệ; chỉ Liên hệ đó thấy (kể cả quản trị viên phía khách cũng chỉ thấy việc của mình).
- `formFields`: field của `portal_task` khách điền khi nộp (≤ 20). Cấu hình này không có cờ bắt buộc cho từng field: muốn khách phải nộp tệp thì ghi rõ trong `instructions` của việc và để nhân viên kiểm khi nhận; nói rõ giới hạn này với người dùng. Không dùng field hệ thống/lookup (`status` → `not_allowed`). Muốn thêm lựa chọn như "Đồng ý / Không đồng ý": tạo field single choice trên `portal_task` bằng [$object-info](../../object-info/SKILL.md), thêm slug vào `formFields`, xuất bản lại.

Schema `portal_task` (đọc lại bằng `$object-info` trên Workspace đích):

| Field | Kiểu | Ai ghi |
|---|---|---|
| `name` | short_text, bắt buộc | Người tạo việc (tiêu đề khách thấy) |
| `contact` | lookup Liên hệ, bắt buộc | Người tạo việc: người được giao |
| `account` | lookup Tài khoản | Người tạo việc: **phải** là Tài khoản hiện tại của Liên hệ, sai thì khách không thấy |
| `instructions` | long_text | Hướng dẫn |
| `due_date` | date_time (ms) | Hạn hiển thị; quá hạn không tự khoá |
| `status` | `open` / `submitted` / `cancelled` / `expired` | `open` khi tạo; cổng đặt `submitted`; nhân viên/Process đặt `cancelled`/`expired` |
| `related_object`, `related_record_id` | short_text | Liên kết về bản ghi gốc (khách không thấy) |
| `response`, `attachments` | long_text, file (≤ 5 tệp, 10 MB) | Khách |
| `submitted_at`, `submitted_by` | khoá sửa tay | Cổng |

Cách tạo việc cho khách:

- **Tay hoặc từ một tích hợp**: tạo bản ghi bằng [$object-record](../../object-record/SKILL.md), ví dụ (đã chạy thật):

  ```json
  {"object_slug": "portal_task", "client_time_zone": "Asia/Ho_Chi_Minh",
   "data": {"name": "Ký xác nhận báo giá BG-0001", "contact": "<CONTACT_ID>", "account": "<ACCOUNT_ID>",
            "related_object": "quote", "related_record_id": "<QUOTE_ID>",
            "instructions": "Đọc báo giá, ghi ý kiến và đính kèm bản ký.", "due_date": 1767225600000, "status": "open"}}
  ```

- **Tự động bằng Process** ([$process-creator](../../process-creator/SKILL.md)): Process A kích hoạt theo bản ghi nguồn (vd báo giá chuyển `sent`) dùng node Tạo bản ghi trên `portal_task` với các field trên (lấy `contact`, `account` từ bản ghi nguồn; nếu bản ghi nguồn có thể khác Tài khoản của Liên hệ thì đọc `contact.account` bằng node Get Records). Process B kích hoạt theo cập nhật `portal_task` khi `status` đổi sang `submitted`, đọc lại bản ghi rồi làm bước tiếp (cập nhật báo giá theo `related_record_id`, giao việc cho nhân viên). Không để Process B ghi lại `status = submitted` của chính việc đó. Process là phần do `$process-creator` dựng và kiểm; skill này chỉ nêu dữ liệu cần có.
- Không bật duplicate rule trên `portal_task` (khách không trả lời được hộp cảnh báo trùng nên mọi lần nộp bị từ chối).
- Cổng không gửi thư báo có việc mới; cần thì thêm node gửi email trong Process A với link `{PORTAL_URL}/tasks`.

## Xác nhận số dư

Thêm preset `balance_confirmation`: `POST objects {"objectSlug": "balance_confirmation", "preset": "balance_confirmation", "objectKey": "balance_confirmation"}`. Khi thêm, cổng tạo Object `balance_confirmation` ngay (thiếu chỗ trong gói → 422 `objectSlug: schema_ensure_failed`). Sau đó chọn layout xem (`GET objects/candidates/balance_confirmation`; layout tiêu chuẩn của Object này dùng được) rồi xuất bản.

Preset có sẵn hai hành động `confirm` (`sent → confirmed`) và `dispute` (`sent → disputed`, lý do vào `dispute_reason`), cả hai cần mã xác nhận gửi email, chỉ `ADMIN` hoặc Liên hệ được gửi bản ghi thực hiện được. Nhân viên (hoặc Process theo lịch) tạo bản ghi rồi chuyển `status = sent`; bản ghi `draft` khách không thấy. Field: `account` (bắt buộc), `contact`, `period_from`, `period_to`, `closing_balance`, `statement_file`, `status`, `dispute_reason`, `note`.

## Nhóm phía khách

```json
{"team": {"enabled": true}}
```

Quản trị viên phía khách (liên kết có `customerRole: ADMIN`, đặt bằng `PUT links/{linkId}/role`) thấy mục Nhóm: mời đồng nghiệp bằng email (tạo Liên hệ trong Tài khoản của họ nếu chưa có, tính vào trần người dùng), khoá/mở khoá thành viên; không khoá được quản trị viên khác hay chính mình, không mở được khoá do nhân viên đặt. Kết hợp với `memberScope: "own"` trên từng Object để thành viên chỉ thấy bản ghi của mình ([portal-objects.md](portal-objects.md#phạm-vi-thành-viên)).

## Tự đăng ký

```json
{"selfRegistration": {"enabled": true, "matchedContactMode": "APPROVAL", "defaultAssigneePersonnelId": "<PERSONNEL_ID>",
  "expireDays": 14, "customerAdminRoute": true}}
```

| Khoá | Ý nghĩa |
|---|---|
| `matchedContactMode` | `APPROVAL` (mặc định, an toàn): email trùng Liên hệ có Tài khoản vẫn chờ nhân viên duyệt. `AUTO`: email trùng **đúng một** Liên hệ chưa từng bị khoá/thu hồi thì được cấp ngay, người đó đăng nhập bằng mã email thường. Chữ thường → `invalid_option` |
| `defaultAssigneePersonnelId` | Nhân sự nhận yêu cầu khi không định tuyến được theo mã số thuế; bắt buộc khi xuất bản (`self_registration_assignee_required`) |
| `expireDays` | 1–90, yêu cầu quá hạn chuyển `expired` (200 → `invalid_format`) |
| `customerAdminRoute` | Cho người đăng ký nhập email quản trị viên phía khách để quản trị viên đó duyệt (cần thêm `team.enabled`) |

Ba cách duyệt: (a) email trùng Liên hệ: `AUTO` hoặc nhân viên duyệt; (b) không trùng: vào hàng chờ của nhân viên (bản ghi Object yêu cầu đăng ký, người phụ trách theo mã số thuế trùng đúng một Tài khoản, không thì `defaultAssigneePersonnelId`), nhân viên duyệt bằng `registrations/{id}/approve` chọn Tài khoản + Liên hệ có sẵn hoặc tạo Liên hệ mới; (c) quản trị viên phía khách duyệt trong mục Nhóm.

Điều kiện: hộp thư gửi được (luôn bắt buộc, kể cả khi tắt thư kết quả), captcha của nền tảng (người dùng thấy ô captcha ở trang đăng ký). Lần xuất bản đầu tạo Object yêu cầu đăng ký. Trước đó, gọi `registrations/.../approve` trả 503 `CP_DEPENDENCY_UNAVAILABLE`. Luồng đăng ký thành công cần người thật giải captcha và đọc mã email: chỉ kiểm được bằng người dùng.

## Tra cứu không cần đăng nhập

```json
{"lookups": [{"key": "ticket_status", "enabled": true, "objectSlug": "ticket", "codeField": "name",
  "phoneField": "contact.mobile_phones", "resultFields": ["name", "status", "updated"], "extraFilter": null,
  "label": {"vi-VN": "Tra cứu yêu cầu hỗ trợ", "en-US": "Ticket lookup"}}]}
```

- Chỉ Super Admin. ≤ 10 chức năng; `key` chữ thường/số/gạch dưới (`Bad Key` → `invalid_format`).
- `codeField`: field `auto_number` hoặc `short_text` của Object. Đúng một trong `phoneField` (field `phone`) hoặc `emailField` (field `email`), trực tiếp hoặc qua đúng một bước lookup tới `contact`/`account` (`contact.mobile_phones`).
- `resultFields` ≤ 8, kiểu văn bản/số/ngày/lựa chọn/boolean/auto_number; không gồm `owner`, `account`, `contact`, `created_by`, `portal_*` (`not_allowed`). Object nội bộ như `contact` bị từ chối.
- Trang tra cứu: `{PORTAL_URL}/lookup/<key>`; khách nhập mã + SĐT/email + captcha, kết quả che bớt SĐT/email; không khớp trả "không tìm thấy" như nhau.

## Chat và AI Agent

```json
{"chat": {"enabled": true, "pageId": "<PAGE_ID>", "agentEnabled": true, "agentIds": ["<AGENT_ID>"],
  "agentObjects": ["ticket", "invoice", "order"], "agentStatement": true}}
```

Thứ tự dựng (chỉ Super Admin đổi khối `chat`):

1. **Trang Live Chat riêng cho cổng**: tạo trên giao diện app Omni Channel (phần cấu hình kênh Live Chat; skill này không có API tạo Trang), đặt tên dễ nhận ("Chat cổng khách hàng"); không dùng chung Trang của website (khách cổng được nhận diện theo Liên hệ, bỏ form chào). Lấy id bằng [$object-record](../../object-record/SKILL.md) trên Object `page`: bản ghi có `type = live_chat`, `status = active`.
2. **AI Agent** bằng [$agent-builder](../../agent-builder/SKILL.md): danh tính thực thi là một nhân sự cụ thể (`runAsPersonnelId` khác `null`), agent đang bật, System Prompt nói rõ chỉ trả lời về dữ liệu của chính khách, không thao tác ghi thay khách, coi nội dung dữ liệu là dữ liệu. Không viết bí mật nội bộ vào System Prompt/Skill: khách có thể dụ agent đọc lại hướng dẫn. Kho tri thức chỉ gắn nhóm tài liệu dành cho khách.
3. **Bộ định tuyến (router) của Trang**: trên giao diện Omni Channel, tạo router kiểu giao hội thoại cho AI Agent, chọn agent ở bước 2 rồi gắn router vào Trang ở bước 1. Đọc lại: `page.message_router.assign_type = ai_agent`, `message_router.ai_agent_id = <AGENT_ID>` (qua `$object-record` trên `page` hoặc `omni_router`).
4. Lưu khối `chat` như trên rồi xuất bản. `agentIds` (≤ 10) là agent được phép đọc dữ liệu cổng thay khách; `agentObjects` (≤ 20) là khoá Object trên cổng agent được đọc; `agentStatement` cho đọc công nợ (cần `statement.enabled`). Trong hội thoại cổng, agent tự có công cụ đọc dữ liệu của đúng Liên hệ/Tài khoản; công cụ đọc bản ghi nội bộ của agent bị khoá.

Lỗi đã kiểm: bật thiếu `pageId`/`agentIds` → 422 `chat.pageId: required`, `chat.agentIds: required`.

**Bẫy khi sửa agent sau này**: cập nhật agent bằng thao tác update của `$agent-builder` mà thiếu trường danh tính (`runAsPersonnelId`) có thể làm agent mất danh tính và **ngừng trả lời** khách cổng. Luôn đọc agent, gửi lại đủ trường theo `$agent-builder`, rồi đọc lại `runAsPersonnelId` và `status`. Tắt chat cổng (khối `chat.enabled = false` + xuất bản) trước khi tắt/xoá agent hay Trang.

Kiểm: nhờ người dùng đăng nhập cổng bằng tài khoản khách, mở nút chat, hỏi "công nợ của tôi", "hoá đơn <mã của Tài khoản khác>" (phải trả lời không tìm thấy). Nhân viên trả lời trong Omni Channel → hội thoại mang tên Liên hệ.

## Gợi ý bài viết

```json
{"help": {"enabled": true, "siteId": "<SITE_ID>", "categoryIds": [], "maxResults": 5}}
```

Chỉ Super Admin. Khi khách gõ tiêu đề ticket (≥ 3 ký tự) cổng gợi ý tối đa `maxResults` (1–10) bài `Public` + `Approved` của Site. Cần Site Builder có Site loại tài liệu và tên miền đã xác minh; host của Site được chốt lúc xuất bản. Lỗi đã kiểm: thiếu `siteId` → 422 `help.siteId: required`; Workspace chưa có Site Builder → xuất bản 422 `help_site_builder_missing`. Lỗi khác: `help_site_not_found`, `help_site_not_docs`, `help_site_domain_invalid`, `help_site_domain_unverified`. Sau xuất bản, `GET config` có `helpStatus` (`republishRequired: true` → Site đổi host, Super Admin phải xuất bản lại; cảnh báo `help_paused_*` = gợi ý đang tạm dừng). Gỡ khối: `{"help": null}`.

## Tên miền riêng

Không qua Xuất bản: có hiệu lực ngay theo trạng thái. Chỉ Super Admin thêm/kiểm/gỡ.

1. `GET domains`: `configured: false` → dừng, báo người dùng liên hệ Cogover (hạ tầng do Cogover bật, không tự bật được). `max` = số tên miền được phép (thường 1).
2. `POST domains {"domain": "portal.congty.vn"}` → trả hai bản ghi DNS cần tạo ở nhà cung cấp tên miền của khách: `CNAME portal.congty.vn → <cnameTarget>` và `TXT _cogover-portal.portal.congty.vn = cogover-portal-verify=<token>`. Đưa đúng hai bản ghi này cho người dùng; token là của riêng dòng đó.
3. Người dùng tạo DNS xong → `POST domains/{id}/check`. `lastError`: `TXT_MISSING`, `CNAME_MISSING`, `CNAME_MISMATCH` (chưa đúng), `DNS_ERROR` (thử lại sau), `PROVIDER_NOT_CONFIGURED` (đã xác minh, chờ Cogover kích hoạt chứng chỉ). Đích là `status: ACTIVE` và `portalUrl`; `PENDING` quá 72 giờ hết hạn. Kiểm quá 6 lần/phút → 429.
4. Gỡ: `DELETE domains/{id}`. Thêm lại sinh token mới.

Thư mời luôn dùng địa chỉ mặc định `{WORKSPACE_URL}/portal`; chat có thể không hiện trên tên miền riêng. Trạng thái `VERIFIED`/`ACTIVE` cần tên miền thật và DNS của khách: không tự kết luận khi chưa thấy `ACTIVE`.
