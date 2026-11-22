# Mẫu triển khai nhanh và báo cáo bàn giao

Lệnh dưới dùng script với biến môi trường `COGOVER_BASE_URL`, `COGOVER_API_KEY` (đọc [$cogover-api-auth](../../cogover-api-auth/SKILL.md)). `cp` là viết tắt của `python3 scripts/customer_portal_api.py`. Mọi ID trong ví dụ là placeholder: thay bằng ID đọc được trên Workspace đích. Body tiếng Việt ghi ra file JSON UTF-8 rồi dùng `--json-file`.

## Mục lục

- [Công thức 1: cổng hỗ trợ tối thiểu](#công-thức-1-cổng-hỗ-trợ-tối-thiểu)
- [Công thức 2: hoá đơn, công nợ, báo giá](#công-thức-2-hoá-đơn-công-nợ-báo-giá)
- [Công thức 3: đặt hàng B2B](#công-thức-3-đặt-hàng-b2b)
- [Báo cáo bàn giao](#báo-cáo-bàn-giao)

## Công thức 1: cổng hỗ trợ tối thiểu

Khách gửi yêu cầu hỗ trợ kèm tệp, trao đổi với nhân viên, xem trạng thái.

1. Đọc hiện trạng: `cp status`; `$object-info` xác nhận Object `ticket` có `account`, `contact`.
2. Thương hiệu (file `brand.json`):

   ```json
   {"displayName": "Hỗ trợ khách hàng Công ty Ví Dụ", "primaryColor": "#0E7C66",
    "supportEmail": "support@example.com", "supportPhone": "1900 0000",
    "defaultLanguage": "vi-VN", "languages": ["vi-VN", "en-US"]}
   ```

   `cp --apply settings --json-file brand.json`; logo: `cp --apply logo logo.png`.
3. Thêm ticket từ preset: `cp --apply call POST objects --json '{"objectSlug":"ticket","preset":"ticket","objectKey":"ticket"}'` → ghi lại `data.id` (`<TICKET_CONFIG_ID>`). Preset này bật trao đổi và cho khách tạo ticket: lần xuất bản đầu cổng tạo Object lưu tin và field `portal_created_by` (cần gói còn chỗ tạo Object).
4. Layout: `cp get objects/candidates/ticket` → chọn layout xem chỉ chứa field cho khách, hoặc tạo layout ẩn theo [quy trình an toàn](portal-objects.md#chọn-layout-chi-tiết) (không thì nhân viên sẽ thấy layout cổng làm layout mặc định) → `cp --apply object-update <TICKET_CONFIG_ID> --json '{"detailLayoutId":"<LAYOUT_ID>"}'`. Muốn mỗi thành viên chỉ thấy ticket của mình: thêm `"memberScope":"own"` (ticket "của mình" = field `contact` là chính họ hoặc họ tạo trên cổng).
5. Cho khách đính kèm tệp (preset không có sẵn): lấy slug field `file` từ `candidates.fields` (Object ticket chuẩn: `attachment_files`), gửi **cả** danh sách `createFields`:

   ```bash
   cp --apply object-update <TICKET_CONFIG_ID> --json '{"createFields":[{"field":"name","required":true},{"field":"type","required":false},{"field":"priority","required":false},{"field":"description","required":false},{"field":"attachment_files","required":false}]}'
   ```

   Đặt field tệp lên layout chi tiết của cổng để khách xem lại tệp đã gửi. Giới hạn tệp: [portal-objects.md](portal-objects.md#khách-tạo-bản-ghi).
6. Xuất bản: `cp --apply publish` → đọc `warnings`, `after.dirty = false`.
7. Cấp quyền: `cp get "contacts/status?contactIds=<CONTACT_ID>"` → `cp --apply grant <CONTACT_ID> --language vi-VN`.
8. Kiểm: checklist + kịch bản người dùng ([troubleshooting.md](troubleshooting.md)).

Muốn có thư báo "ticket được trả lời": `cp mailboxes` → chọn hộp thư `sendable`, bật `notifications.messageReply` (gửi cả khối `notifications`), xuất bản.

## Công thức 2: hoá đơn, công nợ, báo giá

1. Như công thức 1 bước 1–2.
2. Thêm preset `customer_invoice` (key `invoice`) và `quote` (key `quote`); chọn layout từng Object; bật related list dòng hàng:

   ```bash
   cp get "objects/candidates/customer_invoice?layoutId=<INVOICE_LAYOUT_ID>"   # lấy id related list dòng hoá đơn
   cp --apply object-update <INVOICE_CONFIG_ID> --json '{"detailLayoutId":"<INVOICE_LAYOUT_ID>","relatedLists":[{"id":"<INVOICE_LINES_RL_ID>","columns":[]}]}'
   ```

3. Mẫu PDF (tuỳ chọn): `"documentTemplateIds": ["<TEMPLATE_ID>"]` (tra bằng `$document-template`).
4. Công nợ: đọc `draft.statement` rồi gửi `{"statement": {"enabled": true, "label": {"vi-VN": "Công nợ", "en-US": "Statement"}, "menuOrder": 2}}`.
5. Khách chấp nhận/từ chối báo giá: thêm `actions` cho Object báo giá ([portal-objects.md](portal-objects.md#hành-động-của-khách)); hỏi người dùng slug option trạng thái nguồn/đích và field lưu lý do.
6. Thư "hoá đơn mới" (cần hộp thư): `notifications.invoiceNew = {"enabled": true, "objectKey": "invoice", "statuses": ["approved"]}`.
7. Xác nhận số dư (tuỳ chọn): thêm preset `balance_confirmation`, chọn layout.
8. Xuất bản, cấp quyền, đặt quản trị viên phía khách: `cp --apply call PUT links/<LINK_ID>/role --json '{"customerRole":"ADMIN"}'` (thêm `ADMIN`, không hạ `ADMIN` cũ).
9. Dữ liệu để người dùng tự thử: cần hoá đơn đã duyệt, báo giá đã gửi của Tài khoản thử. **Hỏi người dùng trước khi tạo**: duyệt hoá đơn thường sinh công nợ phải thu và bút toán trong Finance, khó hoàn tác (không xoá được chứng từ đã duyệt); ưu tiên dùng chứng từ có sẵn của một khách thử, hoặc Workspace thử. Báo giá thử có thể kết thúc bằng trạng thái từ chối/huỷ thay vì xoá ([$object-record](../../object-record/SKILL.md#dữ-liệu-kiểm-thử)).

## Công thức 3: đặt hàng B2B

1. Kiểm dữ liệu: sản phẩm `simple` đang bán, bảng giá có mục giá thật (`$object-record` trên `price_book`, `price_book_entry`); Tài khoản có người phụ trách (đơn sẽ giao cho người đó).
2. Thêm preset `order` (key `order`), chọn layout có field `portal_reject_reason` (field này có sau lần xuất bản đầu bật đặt hàng; thêm vào layout sau bằng `$object-layout` rồi xuất bản lại) để khách thấy lý do từ chối.
3. Bật đặt hàng (gửi cả khối):

   ```json
   {"ordering": {"enabled": true, "orderObjectKey": "order", "defaultPriceBookId": "<PRICE_BOOK_ID>", "showStock": true,
     "productFilter": {"filters": [{"field": "can_be_sold", "op": "=", "params": 1, "fieldType": "boolean"}], "logic": "AND"}}}
   ```

4. Thư "đơn được xác nhận/từ chối": cần hộp thư gửi được + `notifications.orderReviewed.enabled = true`; không có hộp thư thì để `false`.
5. Xuất bản; xử lý issue `ordering_*` nếu có. Lần này cổng tạo các field `portal_*` của đơn, option `customer_portal` của `order.channel_source` và field `account.portal_price_book`.
6. Giá riêng: với Tài khoản cần giá riêng, ghi `account.portal_price_book = <PRICE_BOOK_ID_RIENG>` bằng `$object-record` (có hiệu lực ngay, không cần xuất bản).
7. Vận hành: nhân viên lọc đơn `channel_source = customer_portal`, `portal_review_status = pending`, xác nhận/từ chối ([vận hành](customer-access-and-operations.md#xác-nhận-hoặc-từ-chối-đơn-từ-cổng)).
8. Kiểm với người dùng: khách Tài khoản có giá riêng thấy giá riêng, khách khác thấy giá mặc định; gửi đơn; nhân viên xác nhận; khách thấy trạng thái.

## Báo cáo bàn giao

Gửi người dùng, không kèm API key, cookie, mã đăng nhập hay link mời:

1. Workspace, URL cổng (`portalUrl`), trạng thái, `configVersion`, `dirty`.
2. Thương hiệu, ngôn ngữ, hotline/email hỗ trợ.
3. Bảng Object trên cổng: khoá menu, Object, layout dùng, quyền xem/tạo, phạm vi thành viên, related list, mẫu PDF, hành động, trao đổi.
4. Tính năng bật/tắt (công nợ, đặt hàng + bảng giá, việc cần làm + cách tạo việc, xác nhận số dư, nhóm, tự đăng ký, tra cứu, thông báo + hộp thư, chat + Trang + agent, gợi ý bài viết, tên miền) và lý do tắt nếu có (thiếu hộp thư, thiếu Site Builder, hạ tầng tên miền...).
5. Người dùng đã cấp: Liên hệ, Tài khoản, trạng thái, vai trò; `usage`.
6. Cảnh báo xuất bản còn lại và giải thích.
7. Đã kiểm gì bằng API, người dùng đã tự thử gì trên cổng (kết quả từng bước), phần **chưa kiểm** (thư tới khách, đăng nhập của khách, chat, tên miền chưa `ACTIVE`...).
8. Việc người dùng/Cogover cần làm tiếp (gán Role nhân viên, tạo DNS, nâng gói, mở hộp thư, dọn dữ liệu thử).
9. Đường vào: `{WORKSPACE_URL}/settings/customer-portal` (cài đặt), `{WORKSPACE_URL}/portal` (khách).
