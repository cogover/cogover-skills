# Kiểm chứng sau thiết lập và xử lý sự cố

## Mục lục

- [Checklist kiểm chứng](#checklist-kiểm-chứng)
- [Kịch bản để người dùng tự thử trên cổng](#kịch-bản-để-người-dùng-tự-thử-trên-cổng)
- [Mã issue và cảnh báo khi xuất bản](#mã-issue-và-cảnh-báo-khi-xuất-bản)
- [Sự cố thường gặp](#sự-cố-thường-gặp)

## Checklist kiểm chứng

Chạy sau mỗi lần xuất bản; ghi kết quả vào báo cáo bàn giao.

1. `status` (script) → `status: PUBLISHED`, `dirty: false`, `configVersion` tăng đúng một so với trước khi xuất bản.
2. `features` đúng yêu cầu đã chốt (công nợ, đặt hàng, việc cần làm, nhóm, tự đăng ký, chat, gợi ý); `lookups` đúng danh sách.
3. `GET objects` → mọi Object cần có `enabled: true`, `published: true`; Object đã bỏ không còn.
4. Với từng Object: `GET objects/{configId}` → `published.viewFields`, `published.listColumns`, `published.relatedLists[].key`, `published.actions[].key` đúng ý; **không** có field nội bộ (giá vốn, người phụ trách nội bộ, ghi chú nội bộ...). Thấy field nội bộ: đánh giá và báo theo [bảng mức độ](portal-objects.md#đánh-giá-field-khách-đang-thấy). Nếu đã tạo layout riêng cho cổng: `list` layout của Object vẫn đọc được và layout cổng có `isShowInPicker: 0` ([quy trình](portal-objects.md#chọn-layout-chi-tiết)).
5. `warnings` của lần xuất bản: đã giải thích hoặc xử lý từng mục ([bảng dưới](#mã-issue-và-cảnh-báo-khi-xuất-bản)).
6. Người dùng: `GET users` → các liên kết đã cấp ở `INVITED`/`ACTIVE`, đúng Tài khoản, đúng vai trò; `GET usage` còn chỗ.
7. Chat (nếu bật): `published.chat` có `pageId`, `agentIds`; agent đang bật và có danh tính thực thi (đọc bằng `$agent-builder`); router của Trang giao cho agent (đọc `page` bằng `$object-record`).
8. Tên miền (nếu có): `GET domains` → trạng thái từng tên; chỉ báo xong khi `ACTIVE`, còn lại báo đang chờ ở bước nào.
9. Nhật ký: `GET audit-logs?limit=20` có `config_published`, `grant_invited` của lượt vừa làm.
10. Giao diện: API chỉ chứng minh cấu hình đã lưu. Chưa xem được trên trình duyệt thì ghi "đã lưu, chưa kiểm tra trên giao diện cổng".

## Kịch bản để người dùng tự thử trên cổng

AI không đọc được hộp thư của khách nên không tự đăng nhập cổng. Không gọi API của trang khách thay khách. Nhờ người dùng (hoặc một đồng nghiệp) dùng một email họ đọc được:

1. Chuẩn bị (AI làm): một Tài khoản thử "A" với Liên hệ có email người dùng đọc được (ví dụ địa chỉ có dấu `+` của chính họ, nếu hộp thư hỗ trợ), một Tài khoản "B" với Liên hệ khác; vài bản ghi thử ở mỗi Tài khoản (hoá đơn đã duyệt, báo giá đã gửi, ticket); cấp quyền cho cả hai Liên hệ.
2. Người dùng mở thư mời (hoặc `{WORKSPACE_URL}/portal/login`, nhập email, nhập mã 6 số trong thư) → vào cổng: thấy tên, màu, logo, hotline đúng.
3. Menu đúng thứ tự; danh sách mỗi Object chỉ có bản ghi của Tài khoản A và khớp bộ lọc (báo giá nháp không hiện).
4. Mở chi tiết: chỉ field dành cho khách; tải PDF (nếu có mẫu); trang công nợ khớp số liệu.
5. Tạo ticket kèm tệp (nếu bật tạo) → nhân viên thấy ticket với Tài khoản/Liên hệ đúng; trả lời công khai + một ghi chú nội bộ → khách chỉ thấy câu trả lời công khai.
6. Hành động có mã (nếu có): bấm "Chấp nhận" → nhập mã trong email → trạng thái đổi.
7. Đặt hàng (nếu bật): thấy đúng giá theo bảng giá của Tài khoản; gửi đơn → nhân viên xác nhận/từ chối → khách thấy trạng thái, lý do.
8. **Cô lập**: AI đưa người dùng URL chi tiết một bản ghi của Tài khoản B (`{WORKSPACE_URL}/portal/o/<objectKey>/r/<RECORD_ID>`); đăng nhập bằng Liên hệ A dán URL đó → phải là "không tìm thấy".
9. Chat (nếu bật): hỏi "công nợ của tôi" và hỏi mã chứng từ của Tài khoản B → agent không tiết lộ.
10. Nhận kết quả từng bước từ người dùng, ghi vào báo cáo. Dọn dữ liệu thử theo yêu cầu của người dùng (thu hồi liên kết trước, rồi xoá bản ghi thử bằng `$object-record` sau khi người dùng xác nhận).

Mã đăng nhập có giới hạn số lần xin/nhập theo email và theo IP; xin quá nhiều sẽ phải giải captcha hoặc chờ. Ưu tiên link trong thư mời, không xin mã liên tục.

## Mã issue và cảnh báo khi xuất bản

Issue (`meta.issues`, chặn xuất bản):

| `issue` | Nguyên nhân | Sửa |
|---|---|---|
| `display_name_required` | Thiếu tên cổng | Đặt `displayName` |
| `no_content_enabled` | Không có Object, công nợ hay việc cần làm nào bật | Bật ít nhất một |
| `invalid_account_field` / `invalid_contact_field` | Field không phải lookup tới `account` / `contact` | Chọn từ `candidates.accountFields` / `contactFields` |
| `invalid_layout` | Chưa chọn layout hoặc layout không thuộc Object / đã tắt | Chọn layout xem trong `candidates.layouts` |
| `layout_has_no_visible_fields`, `standard_layout_not_supported` | Layout không còn field hiển thị được / layout tiêu chuẩn dùng cho Object có hành động | Tạo layout xem riêng cho khách bằng `$object-layout` |
| `invalid_list_columns`, `invalid_filterable_fields`, `invalid_search_fields` | Field không tồn tại/không hỗ trợ, hoặc không thuộc `listColumns` | Sửa danh sách |
| `invalid_extra_filter` | Bộ lọc sai field/option hoặc dùng biến người dùng | Sửa theo metadata `$object-info` |
| `invalid_create_fields`, `invalid_document_templates`, `invalid_actions` | Field tạo/mẫu in/hành động không hợp lệ | Xem [portal-objects.md](portal-objects.md) |
| `conversation_requires_view` | Bật trao đổi khi không có quyền xem | Bật `permissions.view` |
| `member_scope_requires_owner_field` | `memberScope: own` khi không có `contactField` và không cho tạo | Thêm `contactField` hoặc để `account` |
| `related_list_forbidden`, `invalid_related_list_columns` | Related list Object nội bộ / cột sai | Bỏ related list đó; `columns: []` |
| `sender_mailbox_required` | Thông báo/tự đăng ký/thư duyệt đơn bật mà chưa có hộp thư gửi được | Chọn hộp thư `sendable`, hoặc tắt các thông báo đó |
| `invalid_invite_template`, `invalid_profile_fields` | Mẫu thư mời/field hồ sơ sai | Sửa khối tương ứng |
| `schema_ensure_failed` | Cổng không tạo được Object/field cần cho tính năng (số Object tuỳ biến hoặc số field trên một Object đã chạm trần của gói) | Xem [sự cố](#sự-cố-thường-gặp) |
| `ordering_order_object_required`, `ordering_price_book_required`, `ordering_schema_unavailable`, `invalid_product_filter` | Thiếu Object đơn hàng trên cổng (`accountField = account`), bảng giá, field `order.channel_source`, bộ lọc sản phẩm sai | Xem [đặt hàng](settings-and-features.md#đặt-hàng) |
| `invalid_task_form_fields` | `tasks.formFields` có field không ghi được | Chỉ field khách điền |
| `invalid_lookup`, `invalid_lookup_code_field`, `invalid_lookup_verify_field`, `invalid_lookup_result_fields` | Cấu hình tra cứu sai | Xem [tra cứu](settings-and-features.md#tra-cứu-không-cần-đăng-nhập) |
| `self_registration_assignee_required` | Thiếu nhân sự nhận yêu cầu | Đặt `defaultAssigneePersonnelId` |
| `help_site_builder_missing`, `help_site_not_found`, `help_site_not_docs`, `help_site_domain_invalid`, `help_site_domain_unverified` | Site Builder/Site không dùng được | Cài/đổi Site hoặc tắt `help` |

Cảnh báo (`data.warnings`, vẫn xuất bản):

| `issue` | Nghĩa |
|---|---|
| `unsupported_type_skipped` | Một field/cột kiểu không hỗ trợ bị bỏ (thường cột số thứ tự dòng) |
| `action_no_transition_rule` | Field trạng thái của hành động chưa có transition rule; cổng vẫn chỉ cho chuyển theo hành động |
| `action_transition_rule_staff_condition` | Transition rule có điều kiện theo nhân sự, không áp cho thao tác từ cổng |
| `file_max_size_missing`, `file_field_public` | Field tệp thiếu dung lượng tối đa / đang công khai |
| `related_list_skipped`, `related_list_columns_unset`, `related_list_column_removed` | Related list không phải dạng bảng / chưa chốt cột / có cột đã bị bỏ |
| `ordering_order_filter_hides_portal_orders` | Bộ lọc Object đơn hàng làm khách không thấy đơn vừa gửi |
| `help_paused_*` | Gợi ý bài viết tạm dừng (Site đổi host, tên miền chưa xác minh...): Super Admin xử lý rồi xuất bản lại |

## Sự cố thường gặp

| Hiện tượng | Nguyên nhân hay gặp | Cách xử lý |
|---|---|---|
| Khách đăng nhập được nhưng danh sách trống | Bản ghi không có `accountField` = Tài khoản của Liên hệ; `extraFilter` loại hết (vd hoá đơn chưa `approved`); Object `memberScope: own` và khách là thành viên | Đọc bản ghi bằng `$object-record` kiểm field Tài khoản/trạng thái; đối chiếu `published.extraFilterTree`, `memberScope` |
| Khách thấy field không nên thấy | Field đó nằm trên layout chi tiết hoặc trong `listColumns` | Tạo layout riêng cho khách ([quy trình an toàn](portal-objects.md#chọn-layout-chi-tiết)), đổi `detailLayoutId`, xuất bản lại |
| Nhân viên mở bản ghi trên Web App thấy layout của cổng thay cho layout quen dùng | Layout cổng tạo mới, chưa ẩn khỏi bộ chọn: layout mới nhất thành layout Xem mặc định | `PUT` layout cổng đủ payload kèm `isShowInPicker: 0` ([chi tiết](portal-objects.md#chọn-layout-chi-tiết)) |
| `list`/`view` layout của một Object trả HTTP 200 kèm `msg: "Internal Server Error"`, không có `data` | Một layout của Object có `accessControls.items` sai dạng (gửi object thay vì ID chuỗi) | Xoá layout vừa tạo/sửa hoặc `PUT` lại với `items` là ID chuỗi ([bước 4](portal-objects.md#chọn-layout-chi-tiết)) |
| Thành viên không thấy mục Nhóm | Mục Nhóm chỉ hiện cho quản trị viên phía khách (`ADMIN`) khi `team.enabled` đã xuất bản | Đặt người đó làm `ADMIN` nếu người dùng muốn |
| Khách đã được mời nhưng chưa vào được | Liên kết vẫn `INVITED`: chưa bấm link, link mời quá 7 ngày hoặc đã dùng, thư vào spam | `GET users?q=<email>` xem trạng thái; gửi lại thư mời (chờ `retryAfter`); hoặc khách tự vào `{WORKSPACE_URL}/portal/login`, nhập email, nhập mã 6 số. Nhật ký các lần xin mã/nhập sai là ẩn danh: lọc `audit-logs?action=login_otp_requested` / `login_otp_failed` theo thời gian, không lọc theo người dùng được |
| Một mục/Object biến mất khỏi cổng | Object bị tắt (`DELETE` hoặc `enabled: false`) rồi xuất bản; cổng bị `unpublish`; chưa xuất bản sau khi thêm | `status` (cổng `PUBLISHED`?), `GET objects` (đọc [tổ hợp `enabled`/`published`](portal-objects.md#trạng-thái-enabled--published)); bật lại rồi xuất bản. `config_published` trong nhật ký không ghi Object nào bị gỡ |
| Đổi layout/nhãn mà cổng không đổi | Cổng dùng bản chụp lúc xuất bản | Xuất bản lại |
| Không nhận thư mời/mã | Sai email đầu tiên của Liên hệ; thư vào spam; gửi lại quá nhanh (429) | `contacts/status` xem email dùng; gửi lại sau `retryAfter`; nhờ người dùng kiểm spam |
| Không nhận thư thông báo (hoá đơn mới, trả lời) | Chưa bật cờ tương ứng; không có hộp thư gửi được; hộp thư mất kết nối | `mailboxes` → chọn hộp thư `sendable`; bật cờ; xuất bản |
| `schema_ensure_failed` khi xuất bản/thêm preset | Gói đã chạm trần số Object tuỳ biến, hoặc trần số field trên một Object (API không nêu lý do nào). Ở trường hợp trần field, Object của cổng (ví dụ `portal_task`, `balance_confirmation`) có thể đã được tạo nhưng thiếu field | Đếm Object tuỳ biến và số field của Object liên quan bằng `$object-info`; đưa tính năng đó về tắt để phần còn lại xuất bản được; báo người dùng dọn Object/field không dùng hoặc nâng gói với Cogover, rồi bật và xuất bản lại. Bản đang chạy giữ nguyên khi xuất bản lỗi |
| Nút hành động không hiện | Trạng thái không thuộc `from`; `visibleWhen` không khớp; khách là `MEMBER` mà hành động chỉ `ADMIN`; `statusField` không có trên layout | Kiểm bản ghi và cấu hình `actions` |
| Khách bấm hành động báo nội dung đã đổi | Chứng từ (hoặc dòng con) đổi sau khi khách mở | Khách tải lại trang rồi bấm lại |
| Đặt hàng: không có sản phẩm / giá 0 | Bảng giá không có mục giá cho sản phẩm/đơn vị; sản phẩm không phải `simple`; `productFilter` loại hết; `account.portal_price_book` trỏ bảng giá khác | Kiểm `price_book_entry` bằng `$object-record`; sửa bộ lọc |
| Đơn khách gửi "biến mất" khỏi danh sách | `extraFilter` của Object đơn hàng ẩn đơn nháp | Dùng bộ lọc của preset (`OR channel_source in [customer_portal]`) |
| Việc cần làm không hiện với khách | `portal_task.account` khác Tài khoản hiện tại của Liên hệ; giao cho Liên hệ khác; `tasks.enabled` chưa xuất bản | Sửa bản ghi việc; xuất bản |
| Chat: không có nút chat | `chat.enabled` chưa xuất bản, thiếu `pageId`; đang dùng tên miền riêng | Kiểm `published.chat` |
| Chat: agent không trả lời | Agent tắt; mất danh tính thực thi sau khi cập nhật thiếu trường; router của Trang không giao cho agent; agent không có trong `agentIds` | Đọc agent (`$agent-builder`), đọc `page.message_router`; sửa rồi mở hội thoại mới |
| 428 / captcha khi đăng nhập, đăng ký, tra cứu | Xin mã nhiều lần hoặc tính năng bắt buộc captcha | Người dùng giải captcha trên trang; chờ rồi thử lại |
| 429 khi gọi API quản trị | Gửi lại thư mời quá nhanh; kiểm tên miền quá dày; tạo phiên `auth-token` quá 120 lần/giờ trên cùng tài khoản | Chờ `retryAfter`/`Retry-After`; gom thao tác (lệnh `batch`) |
| 403 khi thêm Object / đổi chat / tên miền | Người gọi không phải Super Admin | Dùng API Key của Super Admin hoặc nhờ Super Admin |
| `CP_CONFLICT` khi lưu | Người khác vừa lưu | Đọc lại `config`, áp lại đúng phần mình đổi |
| Không thấy mục Cài đặt → Customer Portal | Workspace cũ chưa có mục menu | Thêm bằng `$app-menu-manager` ([hướng dẫn](customer-access-and-operations.md#mục-menu-cài-đặt--customer-portal)) |
| Tên miền dừng ở `PENDING` | DNS chưa đúng (`TXT_MISSING`, `CNAME_MISSING`, `CNAME_MISMATCH`) hoặc chưa lan truyền | Đưa lại đúng hai bản ghi, chờ, `check` lại; quá 72 giờ thì gỡ và thêm lại |
| Tên miền `VERIFIED` mà không `ACTIVE` (`PROVIDER_NOT_CONFIGURED`) | Phần chứng chỉ do Cogover kích hoạt | Báo người dùng liên hệ Cogover; cổng vẫn chạy ở địa chỉ mặc định |
