---
name: cogover-customer-portal
description: "Thiết lập và vận hành Cogover Customer Portal (cổng khách hàng tại `{WORKSPACE_URL}/portal`) qua Web App API `/api/v1/workspace/customer-portal`: khảo sát và hỏi lại yêu cầu, điều kiện tiên quyết, thương hiệu, Object hiển thị (hoá đơn, báo giá, đơn hàng, ticket, Object tuỳ biến; layout, related list, PDF, phạm vi thành viên, hành động có mã xác nhận), công nợ, đặt hàng theo bảng giá, việc cần làm, xác nhận số dư, nhóm, tự đăng ký, tra cứu công khai, thông báo email, chat + AI Agent, gợi ý bài viết, tên miền riêng, lưu nháp/xuất bản, cấp quyền cho Liên hệ, vận hành của nhân viên, kiểm chứng và xử lý sự cố. Phối hợp $cogover-api-auth, $object-info, $object-record, $object-layout, $agent-builder, $process-creator, $user-permission, $app-menu-manager."
metadata:
  author: cogover
  version: "1.0.0"
---

# Cogover Customer Portal

- **Phiên bản:** `1.0.0`
- **Ngày phát hành:** `2026-11-22`

## Customer Portal là gì

Cổng có thương hiệu của Workspace để **khách hàng doanh nghiệp tự phục vụ**: xem chứng từ (hoá đơn, báo giá, hợp đồng, đơn hàng, Object tuỳ biến), tải PDF, xem công nợ, gửi và trao đổi yêu cầu hỗ trợ kèm tệp, chấp nhận/từ chối chứng từ bằng mã xác nhận, đặt hàng theo bảng giá, nộp việc được giao, xác nhận số dư, chat với nhân viên hoặc AI Agent.

| Tác nhân | Là ai | Làm gì |
|---|---|---|
| Người thiết lập | Super Admin, hoặc nhân viên có quyền "Thiết lập Customer Portal" / "Quản lý tài khoản portal" | Cấu hình, xuất bản, cấp quyền. Chỉ Super Admin thêm/sửa Object trên cổng, đổi chat, gợi ý bài viết, tra cứu, tên miền |
| Nhân viên nghiệp vụ | Người có quyền trên bản ghi | Trả lời trao đổi, xác nhận đơn, giao việc, duyệt đăng ký |
| Người dùng cổng | Một email gắn với **Liên hệ** (`contact`) của một **Tài khoản** (`account`) | Thấy dữ liệu của Tài khoản đó (quy tắc duy nhất: bản ghi thuộc Tài khoản nào thì người của Tài khoản đó thấy) |
| Quản trị viên phía khách | Người dùng cổng có vai trò `ADMIN` | Thấy mọi dữ liệu của Tài khoản, quản lý thành viên (khi bật Nhóm); thành viên (`MEMBER`) có thể bị giới hạn chỉ thấy bản ghi của mình |

URL khách: `{WORKSPACE_URL}/portal` (hoặc tên miền riêng). Đăng nhập không mật khẩu bằng mã 6 số gửi email hoặc link thư mời. Ngôn ngữ: `vi-VN`, `en-US`. Cài đặt trên giao diện: `{WORKSPACE_URL}/settings/customer-portal` (Cài đặt → Hệ thống → Customer Portal).

## Nguyên tắc

- Xác thực theo [$cogover-api-auth](../cogover-api-auth/SKILL.md): API quản trị là `/api/v1/...` nên phải đổi API Key thành phiên Web App. Dùng script [`scripts/customer_portal_api.py`](scripts/customer_portal_api.py) (Python chuẩn, đọc `COGOVER_BASE_URL`, `COGOVER_API_KEY`, không in bí mật, ghi phải có `--apply`). `python3 scripts/customer_portal_api.py --help` để xem lệnh: `status`, `get`, `mailboxes`, `settings`, `object-update`, `publish`, `unpublish`, `logo`, `grant`, `call`, `batch`.
- Đọc trước, ghi sau, đọc lại sau mỗi lần ghi. Không ghi khi người dùng chỉ hỏi/khảo sát. Mỗi lần chạy script tạo một phiên; `auth-token` giới hạn 120 phiên/giờ/tài khoản: gom thao tác, dùng `batch` cho chuỗi dài (một phiên; `{{steps.N.data.id}}` lấy ID của bước trước; `--out <file>` ghi kết quả JSON hợp lệ: [định dạng](references/admin-api.md#quy-ước-response-và-lỗi)).
- **Lưu là nháp, Xuất bản mới tới khách.** Mọi thay đổi cấu hình chỉ hiện trên cổng sau `publish`; xuất bản lỗi thì bản đang chạy giữ nguyên.
- `PUT config` thay **cả khối** cấp một: đọc `draft.<khối>`, sửa, gửi lại nguyên khối.
- Không gọi API của trang khách (`/portal-api/...`) thay khách, không đọc hộp thư của khách. Kiểm phía khách bằng cách nhờ người dùng đăng nhập ([kịch bản](references/troubleshooting.md#kịch-bản-để-người-dùng-tự-thử-trên-cổng)).
- Chỉ dùng endpoint trong tài liệu của skill này và các skill được dẫn; không suy đoán endpoint khác. Response lạ: dừng, báo người dùng.
- Mọi thứ khách thấy đều do cấu hình quyết định: layout chi tiết, cột danh sách, mẫu PDF. Chọn layout dành riêng cho khách để không lộ field nội bộ.

## Tài liệu theo bước

| Khi làm gì | Đọc |
|---|---|
| Endpoint, request/response, mã lỗi | [references/admin-api.md](references/admin-api.md) |
| Thương hiệu, thông báo, công nợ, đặt hàng, việc cần làm, xác nhận số dư, nhóm, tự đăng ký, tra cứu, chat + AI Agent, gợi ý bài viết, tên miền; bảng điều kiện tiên quyết | [references/settings-and-features.md](references/settings-and-features.md) |
| Đưa Object lên cổng: preset, layout, related list, bộ lọc, khách tạo bản ghi, phạm vi thành viên, trao đổi, PDF, hành động | [references/portal-objects.md](references/portal-objects.md) |
| Cấp quyền cho khách, vai trò, khoá/thu hồi; nhân viên trả lời, duyệt đơn, duyệt đăng ký; phân quyền nhân viên; mục menu | [references/customer-access-and-operations.md](references/customer-access-and-operations.md) |
| Checklist kiểm chứng, kịch bản cho người dùng, mã issue/cảnh báo, sự cố | [references/troubleshooting.md](references/troubleshooting.md) |
| Công thức đầu-cuối và báo cáo bàn giao | [references/recipes.md](references/recipes.md) |

## Quy trình

### 1. Khảo sát hiện trạng (chỉ đọc)

1. `status` (tóm tắt `GET config`): `status`, `portalUrl`, `dirty`, khối đang bật, Object trên cổng. Cổng đang chạy: rà field khách đang thấy của từng Object theo [bảng mức độ](references/portal-objects.md#đánh-giá-field-khách-đang-thấy) và báo người dùng. `dirty: true` ngay từ đầu = có người đang sửa dở: hỏi người dùng trước khi xuất bản đè.
2. `get usage`, `get "users?limit=20"`, `get domains`; hộp thư gửi: lệnh riêng `mailboxes` của script (không phải đường dẫn dùng được trong `get`/`batch`).
3. `get objects/presets` (`available`) và [$object-info](../object-info/SKILL.md) cho các Object nghiệp vụ dự kiến (có lookup `account`/`contact` không, slug option trạng thái).
4. Super Admin hay không: thử `get objects/presets` (403 = không phải Super Admin, các bước Object/chat/tra cứu/tên miền phải nhờ Super Admin).

### 2. Chốt yêu cầu với người dùng

Hỏi gọn trong một lượt những gì chưa rõ; phần còn lại tự quyết theo mặc định an toàn và ghi vào báo cáo.

| Phải hỏi | Tự quyết được (mặc định) |
|---|---|
| Khách được xem gì (Object nào, trạng thái nào được thấy: vd chỉ hoá đơn đã duyệt) | Cột danh sách, sắp xếp `created desc`, field lọc/tìm theo preset |
| Khách được làm gì: tạo ticket, trao đổi, chấp nhận báo giá, đặt hàng, nộp việc, xác nhận số dư | Bắt mã xác nhận cho mọi hành động đổi trạng thái |
| Thành viên của khách thấy toàn bộ dữ liệu công ty hay chỉ của mình; ai là quản trị viên phía khách | `memberScope: account`; không ai là `ADMIN` cho tới khi người dùng chỉ định |
| Đặt hàng: bảng giá mặc định, giá riêng theo Tài khoản, nhóm sản phẩm bán | Hiện Còn/Hết hàng |
| Chat: có cần, nhân viên trả lời hay AI Agent, agent được đọc gì | Không bật chat nếu chưa được yêu cầu |
| Thương hiệu: tên cổng, màu, logo, email/hotline hỗ trợ | Ngôn ngữ mặc định `vi-VN`, có `en-US` |
| Thông báo email: có muốn, hộp thư nào | Tắt khi chưa có hộp thư gửi được |
| Mời ai (danh sách Liên hệ/Tài khoản), lúc nào gửi thư mời | Không gửi thư mời thật khi chưa được xác nhận danh sách email |
| Tự đăng ký, tra cứu công khai, tên miền riêng | Tắt |

### 3. Kiểm điều kiện tiên quyết

Đối chiếu [bảng điều kiện](references/settings-and-features.md#bảng-điều-kiện-tiên-quyết) cho từng tính năng đã chốt: Object nền, hộp thư gửi được, Omni Channel + Trang Live Chat + AI Agent, Site Builder, hạ tầng tên miền (do Cogover bật), captcha của nền tảng, chỗ trống trong gói cho các Object cổng tự tạo, quyền của người thao tác. Thiếu điều kiện nào thì báo người dùng cách bổ sung, làm tiếp các phần độc lập, không bật phần đó.

### 4. Đường vào trên giao diện

Nếu người dùng muốn tự xem/sửa trên giao diện mà Workspace chưa có mục Cài đặt → Hệ thống → Customer Portal, thêm bằng [$app-menu-manager](../app-menu-manager/SKILL.md) theo [thông số mục menu](references/customer-access-and-operations.md#mục-menu-cài-đặt--customer-portal). Không bắt buộc cho API.

### 5. Cấu hình bằng API

Làm theo thứ tự; sau mỗi bước đọc lại (`status` hoặc `get objects/{configId}`):

1. **Thương hiệu**: `settings` với `displayName`, `primaryColor`, `supportEmail`, `supportPhone`, `defaultLanguage`, `languages`; `logo <file>`; mẫu thư mời nếu cần ([chi tiết](references/settings-and-features.md#thương-hiệu-ngôn-ngữ-phiên-hồ-sơ)).
2. **Object hiển thị**: preset hoặc tuỳ biến → layout dành cho khách (layout mới phải tạo ẩn khỏi bộ chọn `isShowInPicker: 0`, nếu không nó thành layout Xem mặc định của nhân viên: [quy trình an toàn](references/portal-objects.md#chọn-layout-chi-tiết)) → related list → quyền xem/tạo, `createFields` → phạm vi thành viên → trao đổi → mẫu PDF → hành động có mã ([portal-objects.md](references/portal-objects.md#quy-trình-thêm-một-object)).
3. **Công nợ** → **đặt hàng** → **việc cần làm** (và cách tạo việc: bản ghi `portal_task` bằng [$object-record](../object-record/SKILL.md) hoặc Process bằng [$process-creator](../process-creator/SKILL.md)) → **xác nhận số dư** → **nhóm** → **tự đăng ký** → **tra cứu** → **thông báo email** → **chat + AI Agent** (Trang Live Chat, agent bằng [$agent-builder](../agent-builder/SKILL.md), router, rồi khối `chat`) → **gợi ý bài viết** → **tên miền riêng** ([settings-and-features.md](references/settings-and-features.md)).
4. **Xuất bản**: lệnh `publish` của script in kết quả (`configVersion`, `warnings`) rồi khối `after` (`dirty: false`, `configVersion` +1); trong `batch`, bước `POST publish` chỉ trả `configVersion`, `warnings`, nên thêm bước `GET config` ngay sau để đọc `dirty`. Lỗi 422 `CP_PUBLISH_INVALID` thì sửa từng mục `meta.issues` ([mã issue](references/troubleshooting.md#mã-issue-và-cảnh-báo-khi-xuất-bản)) rồi xuất bản lại. Lần đầu bật trao đổi/việc cần làm/đặt hàng/tự đăng ký, cổng tự tạo Object/field (không gắn App); gói hết chỗ → `schema_ensure_failed`.
5. **Tắt cổng** khi người dùng yêu cầu: `unpublish` (khách không vào được ngay; cấu hình, người dùng giữ nguyên).

### 6. Cấp quyền cho khách

`get "contacts/status?contactIds=..."` → cho người dùng xem email sẽ nhận thư → `grant <CONTACT_ID>... --language vi-VN --apply` → đọc `outcome` từng dòng. Đặt quản trị viên phía khách, gửi lại thư mời, khoá/mở, thu hồi, huỷ phiên: [customer-access-and-operations.md](references/customer-access-and-operations.md#cấp-quyền).

### 7. Vận hành phía nhân viên

Trả lời trao đổi (công khai/nội bộ), xác nhận/từ chối đơn từ cổng, duyệt tự đăng ký, đọc nhật ký, phân quyền nhân viên không phải Super Admin bằng [$user-permission](../user-permission/SKILL.md): [customer-access-and-operations.md](references/customer-access-and-operations.md#trả-lời-trao-đổi-của-khách).

### 8. Kiểm chứng

Chạy [checklist](references/troubleshooting.md#checklist-kiểm-chứng): `dirty: false`, `published` của từng Object không có field nội bộ, người dùng đúng trạng thái/vai trò. Sau đó đưa người dùng [kịch bản tự thử trên `/portal`](references/troubleshooting.md#kịch-bản-để-người-dùng-tự-thử-trên-cổng), gồm ca cô lập dữ liệu giữa hai Tài khoản. Không báo "đã kiểm phía khách" khi người dùng chưa xác nhận.

### 9. Bàn giao

Theo [mẫu báo cáo](references/recipes.md#báo-cáo-bàn-giao): cấu hình hiệu lực, người dùng đã cấp, cảnh báo, phần đã kiểm và chưa kiểm, việc người dùng/Cogover cần làm tiếp. Không đưa API key, cookie, mã đăng nhập, link mời vào báo cáo.

## Mẫu nhanh

| Nhu cầu | Công thức |
|---|---|
| Khách gửi yêu cầu hỗ trợ và trao đổi | [Cổng hỗ trợ tối thiểu](references/recipes.md#công-thức-1-cổng-hỗ-trợ-tối-thiểu) |
| Khách xem hoá đơn, công nợ, báo giá (chấp nhận báo giá) | [Hoá đơn + công nợ + báo giá](references/recipes.md#công-thức-2-hoá-đơn-công-nợ-báo-giá) |
| Đại lý/khách B2B tự đặt hàng theo bảng giá | [Đặt hàng B2B](references/recipes.md#công-thức-3-đặt-hàng-b2b) |

## Lỗi hay gặp

| Gặp | Làm |
|---|---|
| 422 `CP_VALIDATION_FAILED` | Sửa đúng field trong `meta.errors`; không có gì được ghi |
| 422 `CP_CONFLICT` | Đọc lại `config`, áp lại thay đổi của mình |
| 422 `CP_PUBLISH_INVALID` | Sửa từng `meta.issues`, xuất bản lại |
| `sender_mailbox_required` | `mailboxes` → chọn hộp thư `sendable` hoặc tắt thông báo/tự đăng ký/thư duyệt đơn |
| `schema_ensure_failed` | Gói đã chạm trần số Object tuỳ biến hoặc số field trên một Object: tắt tính năng đó, báo người dùng dọn bớt hoặc nâng gói ([sự cố](references/troubleshooting.md#sự-cố-thường-gặp)) |
| 403 khi sửa Object/chat/tra cứu/tên miền | Cần Super Admin |
| 429 | Chờ `retryAfter` / `Retry-After`; không lặp dồn dập |
| Khách không thấy dữ liệu | Kiểm Tài khoản trên bản ghi, `extraFilter`, `memberScope` ([sự cố](references/troubleshooting.md#sự-cố-thường-gặp)) |
