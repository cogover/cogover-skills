# Cấp quyền cho khách và vận hành của nhân viên

API chi tiết: [admin-api.md](admin-api.md#người-dùng-cổng). Mọi thao tác ở đây chỉ chạy khi cổng đã `PUBLISHED`.

## Mục lục

- [Người dùng cổng là ai](#người-dùng-cổng-là-ai)
- [Cấp quyền](#cấp-quyền)
- [Vòng đời liên kết](#vòng-đời-liên-kết)
- [Vai trò phía khách](#vai-trò-phía-khách)
- [Một người thuộc nhiều Tài khoản](#một-người-thuộc-nhiều-tài-khoản)
- [Trả lời trao đổi của khách](#trả-lời-trao-đổi-của-khách)
- [Xác nhận hoặc từ chối đơn từ cổng](#xác-nhận-hoặc-từ-chối-đơn-từ-cổng)
- [Duyệt yêu cầu tự đăng ký](#duyệt-yêu-cầu-tự-đăng-ký)
- [Nhật ký và hạn mức](#nhật-ký-và-hạn-mức)
- [Phân quyền nhân viên](#phân-quyền-nhân-viên)
- [Mục menu Cài đặt → Customer Portal](#mục-menu-cài-đặt--customer-portal)

## Người dùng cổng là ai

- Mỗi người dùng cổng là một **email** trong Workspace; mỗi **liên kết** (`linkId`) nối email đó với một **Liên hệ** (`contact`) thuộc một **Tài khoản** (`account`). Người dùng cổng không phải nhân sự, không chiếm ghế người dùng của Workspace; trần riêng xem ở `GET usage`.
- Đăng nhập không mật khẩu: nhập email → nhận mã 6 số (hạn 10 phút) hoặc bấm link trong thư mời (một lần, hạn 7 ngày). Mã và thư mời đi bằng email hệ thống của nền tảng.
- Liên hệ đủ điều kiện: có ít nhất một email (email đầu tiên là email đăng nhập) và đã gắn Tài khoản. Người cấp phải xem được Liên hệ và Tài khoản đó.

## Cấp quyền

1. Tìm Liên hệ bằng [$object-record](../../object-record/SKILL.md) (lọc theo Tài khoản, email). Thiếu email/Tài khoản thì bổ sung trước (cần người dùng đồng ý nếu là dữ liệu thật).
2. Kiểm điều kiện: `GET contacts/status?contactIds=<ID1>,<ID2>` → `eligible`, `reason` (`NO_EMAIL`, `NO_ACCOUNT`, `CONTACT_NOT_FOUND`), `email` sẽ dùng để đăng nhập. Cho người dùng xem danh sách email sẽ nhận thư mời trước khi gửi.
3. Cấp: `POST grants {"contactIds": [...≤ 100], "language": "vi-VN"}` (script: `grant <ID>... --language vi-VN --apply`). Mỗi dòng có `outcome` riêng:

| `outcome` | `reason` | Nghĩa |
|---|---|---|
| `INVITED` | | Đã gửi thư mời, liên kết `INVITED`, `contact.portal_status = invited` |
| `ALREADY_INVITED` | | Đã mời trước đó (không gửi thêm; dùng gửi lại thư mời) |
| `ALREADY_ACTIVE` | | Khách đã kích hoạt |
| `SKIPPED` | `NO_EMAIL` / `NO_ACCOUNT` / `CONTACT_NOT_FOUND` / `LINK_LOCKED` / `QUOTA_EXCEEDED` | Không làm gì với dòng đó |

4. Đọc lại: `GET users?q=<tên hoặc email>` hoặc `contacts/status`.

Tìm `linkId`/`userId` để thao tác tiếp (gửi lại thư, khoá, vai trò, thu hồi): `GET users?q=<một phần tên Liên hệ hoặc email>` (đã kiểm: `q=Contact A1` trả đúng dòng), thêm `&accountId=<ACCOUNT_ID>` hoặc `&status=INVITED|ACTIVE|LOCKED` để thu hẹp; hoặc `contacts/status?contactIds=<CONTACT_ID>` → `linkId`. `userId` (một email) dùng cho huỷ phiên; `linkId` (một Liên hệ) dùng cho mọi thao tác còn lại.

Trên giao diện: nút "Customer Portal" trên trang Liên hệ và hành động hàng loạt trên danh sách Liên hệ làm cùng việc này.

## Vòng đời liên kết

Mọi thao tác dưới đây có hiệu lực ngay (không cần xuất bản), ở request kế tiếp của khách.

| Trạng thái | Từ đâu | Thao tác tiếp |
|---|---|---|
| `INVITED` | Cấp quyền | Khách bấm link mời hoặc đăng nhập bằng mã → `ACTIVE`; gửi lại thư mời `POST links/{id}/resend-invite` (cách nhau ≥ khoảng 60 giây, ≤ 5 lần/ngày; quá → 429 `resend_cooldown`, chờ `meta.retryAfter`) |
| `ACTIVE` | Khách đã vào | Khoá, đổi vai trò, thu hồi |
| `LOCKED` | `POST links/{id}/lock {"reason"}` | Mở khoá `POST links/{id}/unlock` → về `ACTIVE` (đã từng vào) hoặc `INVITED` |
| `NOT_GRANTED` | `DELETE links/{id}` (thu hồi) | Cấp lại bằng `grants` |

- Huỷ mọi phiên đăng nhập của một người (mọi Tài khoản): `POST users/{userId}/revoke-sessions`. Thu hồi liên kết cuối cùng cũng huỷ phiên.
- Khoá có hiệu lực ở request kế tiếp của khách. Nhân viên đổi email hoặc Tài khoản của Liên hệ cũng làm liên kết mất hiệu lực/chuyển Tài khoản.
- `contact.portal_status` phản ánh trạng thái (chỉ đọc).

## Vai trò phía khách

`PUT links/{linkId}/role {"customerRole": "ADMIN"}` (hoặc `"MEMBER"`, chữ hoa), có hiệu lực ngay, không cần xuất bản. Một Tài khoản có thể có **nhiều** `ADMIN` (đã kiểm: đặt thêm một liên kết làm `ADMIN` trong khi liên kết `ADMIN` cũ của cùng Tài khoản vẫn giữ nguyên). Vì vậy "đặt X làm quản trị viên" là **thêm**, không tự hạ người cũ: hỏi người dùng có muốn thay người cũ không; nếu có thì đặt người cũ về `MEMBER` bằng lệnh riêng. Đọc lại bằng `GET users?accountId=<ACCOUNT_ID>` (`customerRole` là vai trò hiệu lực; `storedCustomerRole` khác `null` khi vai trò đã lưu không còn hiệu lực, vd Liên hệ đã chuyển Tài khoản). Quản trị viên phía khách: thấy toàn bộ dữ liệu Tài khoản kể cả Object `memberScope: own`, quản lý mục Nhóm khi `team.enabled`, mặc định là người duy nhất thực hiện được hành động có mã xác nhận. Vai trò gắn với Tài khoản lúc đặt: Liên hệ chuyển Tài khoản thì tự hạ về `MEMBER`. Người đặt phải sửa được Liên hệ và xem được Tài khoản.

## Một người thuộc nhiều Tài khoản

Cùng một email ở nhiều Liên hệ (mỗi Liên hệ một Tài khoản) → một người dùng, nhiều liên kết; khách chọn Tài khoản sau khi đăng nhập và đổi trên thanh đầu trang, dữ liệu từng Tài khoản tách riêng. Cấp quyền cho từng Liên hệ. Lưu ý: Workspace có quy tắc chống trùng email trên Liên hệ sẽ chặn tạo Liên hệ thứ hai cùng email (`/bapi` trả `r: 49`); khi đó hỏi người dùng muốn nới quy tắc hay dùng email khác.

## Trả lời trao đổi của khách

- Trên giao diện: trang bản ghi (vd ticket) trong Web App có khối "Trao đổi với khách": chọn "Gửi cho khách" (công khai) hoặc "Nội bộ" (ghi chú, khách không thấy). Mặc định sau khi gửi quay về Nội bộ.
- Bằng API: `GET records/{objectSlug}/{recordId}/conversation` để đọc; `POST` cùng đường dẫn `{"content": "Văn bản thuần", "isPublic": true}` (201). Không đính tệp, không dán link tệp nội bộ (422 `file_link_not_allowed`). Thư báo cho khách chỉ gửi khi `notifications.messageReply.enabled` và có hộp thư.
- Quyền: nhân viên phải xem được bản ghi; gửi tin cần quyền sửa bản ghi cha và quyền tạo trên Object lưu tin của cổng (thiếu → 403; `GET` trả `canReply: false`, không thấy nội dung khi `canRead: false`).

## Xác nhận hoặc từ chối đơn từ cổng

Đơn khách gửi có `channel_source = customer_portal`, `portal_review_status = pending`, `status = draft`. Nhân viên lọc danh sách đơn theo hai field này (có thể tạo saved filter bằng [$object-filter](../../object-filter/SKILL.md)), sửa đơn nếu cần bằng giao diện chuẩn, rồi:

- Xác nhận: `POST orders/{orderId}/confirm {}` → đơn `activated`, `portalReviewStatus: confirmed`.
- Từ chối: `POST orders/{orderId}/reject {"reason": "Hết hàng, sẽ báo lại"}` → đơn `canceled`, lý do hiện cho khách.
- Trên giao diện: panel "Đơn hàng từ Customer Portal" trên trang đơn.
- Lỗi đã kiểm: đơn không phải từ cổng hoặc đã xử lý → 422 `CP_TRANSITION_NOT_ALLOWED`; thiếu lý do → 422 `reason: required`; không thấy đơn → 404. Nhân viên cần quyền sửa `order`. Khách tự huỷ được khi đơn còn chờ.

## Duyệt yêu cầu tự đăng ký

Yêu cầu nằm trong Object yêu cầu đăng ký do cổng tạo (lọc `status = pending`, người phụ trách theo định tuyến). Trên giao diện: panel "Duyệt đăng ký" trên trang yêu cầu. Bằng API:

- Duyệt: `POST registrations/{recordId}/approve {"accountId": "<ACCOUNT_ID>", "contactId": "<CONTACT_ID>"}` hoặc thay `contactId` bằng `"createContact": {"name": "..."}`. Liên hệ chọn phải thuộc Tài khoản đó; email người đăng ký được thêm vào Liên hệ nếu chưa có. Liên kết thành `ACTIVE`, người đăng ký đăng nhập bằng mã email.
- Từ chối: `POST registrations/{recordId}/reject {"reason": "..."}`.
- Gặp 503 `CP_DEPENDENCY_UNAVAILABLE`: Workspace chưa có Object yêu cầu (tự đăng ký chưa từng được xuất bản).

## Nhật ký và hạn mức

- `GET audit-logs?action=<mã>&from=&to=&accountId=&limit=` → ai làm gì, lúc nào, IP. Không truyền `from`/`to`: trả từ mới nhất về cũ, không giới hạn thời gian; `nextCursor` là `id` của dòng cuối, truyền `cursor=<id>` để lấy trang cũ hơn (đã kiểm). `from`/`to` (ms) cách nhau quá 93 ngày → 422 `to: invalid`. Tham số lọc không được hỗ trợ (vd `actorType`) bị bỏ qua, không báo lỗi.
- Giới hạn cần biết: `config_published.detail` chỉ có `{objects: <số Object trên cổng>, configVersion}`, không cho biết Object nào được thêm/gỡ (so `GET objects` trước/sau để biết). Sự kiện trước khi khách vào được cổng (`login_otp_requested`, `login_otp_failed`, `invite_accepted` thất bại, `lookup_performed`) là **ẩn danh** (`actorType: ANONYMOUS`, không có người dùng/Tài khoản), nên lọc theo `portalUserId`/`accountId` không thấy; chỉ lọc theo `action` và thời gian (đã kiểm). Sự kiện do hệ thống (`actorType: SYSTEM`) có `detail.reason` như `contact_account_changed`, `contact_email_removed`, `contact_deleted`. Mã thường gặp: `config_published`, `config_unpublished`, `grant_invited`, `grant_skipped`, `invite_resent`, `link_locked`, `link_unlocked`, `link_revoked`, `link_role_changed`, `session_revoked`, `login_success`, `record_created`, `record_action`, `message_posted`, `order_submitted`, `order_confirmed`, `order_rejected`, `task_submitted`, `registration_*`, `domain_*`, `chat_token_issued`, `agent_data_read`. `detail` bị lược theo quyền xem bản ghi của người đọc.
- `GET usage` → `{used, max}`. Hết trần → `grants` trả `SKIPPED`/`QUOTA_EXCEEDED`; trần do gói Cogover quyết định.

## Phân quyền nhân viên

Hai nhóm quyền của cổng trong Role:

| Mã quyền (`functionCode`) | Thao tác (`actions`) | Mở được |
|---|---|---|
| `customer_portal_setting` | `view`, `edit` | Xem/sửa cấu hình, xuất bản, tắt cổng, xem tên miền |
| `customer_portal_user` | `view`, `create`, `edit`, `delete`, `approve` | Người dùng cổng: xem, cấp, sửa (gửi lại, khoá, vai trò, huỷ phiên), thu hồi, duyệt đăng ký; xem nhật ký, hạn mức |

Gán bằng [$user-permission](../../user-permission/SKILL.md) (`/bapi/v1/roles`). Payload đã kiểm (tạo, đọc lại, xoá Role thử):

```json
{"name": "Quản trị cổng khách hàng", "description": "Cấu hình và cấp quyền Customer Portal",
 "permissions": [
  {"functionCode": "customer_portal_setting", "actions": ["view", "edit"], "groupSlug": "object", "values": [], "valueOption": 3},
  {"functionCode": "customer_portal_user", "actions": ["view", "create", "edit", "delete", "approve"], "groupSlug": "object", "values": [], "valueOption": 3}]}
```

- Workspace phiên bản cũ có thể từ chối với `actions: action 'view' invalid`: khi đó gán hai nhóm quyền "Thiết lập Customer Portal" và "Quản lý tài khoản portal" trên màn Role của giao diện (nhờ người dùng), rồi đọc lại Role bằng `$user-permission`.
- Dù có hai quyền này, người không phải Super Admin **không** được: thêm/sửa/bỏ Object trên cổng, đọc preset/candidates, đổi `lookups`/`chat`/`help`, thêm/kiểm/gỡ tên miền (403). Họ đọc được các khối đó.
- Nhân viên nghiệp vụ không cần quyền cổng: trả lời trao đổi, duyệt đơn dùng quyền record sẵn có (xem/sửa bản ghi, quyền trên `order`, Object lưu tin của cổng). Việc cần làm và Xác nhận số dư là bản ghi chuẩn (`portal_task`, `balance_confirmation`): cấp quyền xem/tạo/sửa các Object này cho người giao việc.
- Kiểm bằng persona thật theo `$user-permission` nếu nghiệp vụ phụ thuộc phân quyền.

## Mục menu Cài đặt → Customer Portal

Màn cài đặt ở `{WORKSPACE_URL}/settings/customer-portal`. Workspace tạo từ trước có thể chưa có mục menu. Kiểm và thêm bằng [$app-menu-manager](../../app-menu-manager/SKILL.md) trên App `settings` (đọc cây menu trước; đã có mục `actionContent = /customer-portal` thì thôi). Thông số mục menu như các mục cài đặt hệ thống khác:

```json
{"appId": "<SETTINGS_APP_ID>", "parentId": "<SYSTEM_GROUP_ITEM_ID>", "name": "Customer Portal", "mobileName": "Customer Portal",
 "slug": "customer_portal", "description": "", "icon": "", "actionType": 34, "actionContent": "/customer-portal",
 "actionUrlType": 3, "actionUrlOption": 2, "isDefault": false, "platform": 1, "defaultOpen": 1, "showCount": 0, "fillIconColor": 1,
 "accessControls": [{"functions": ["EXECUTE"], "option": 1, "items": [], "type": "personnel"}]}
```

`<SYSTEM_GROUP_ITEM_ID>` là mục cha nhóm "System" (slug `system`) trong App `settings`; sao chép `actionUrlType`, `actionUrlOption`, `accessControls` từ một mục cài đặt hệ thống có sẵn cùng nhóm nếu khác. Thiếu mục menu không chặn API: chỉ ảnh hưởng đường vào trên giao diện. Quyền vào trang vẫn theo hai nhóm quyền ở trên.
