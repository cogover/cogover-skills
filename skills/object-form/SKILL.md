---
name: object-form
description: "Quản lý Object Form/Lead Form Cogover (form công khai thu thập dữ liệu) qua Web App API `/api/v1/objects/forms`: tìm/xem, tạo, sửa, publish, nhân bản, xoá, layout `isForm`, success action, ngôn ngữ/thông báo/chặn email, URL public, URL nội bộ, mã nhúng, đọc responses. Tự gọi $object-layout tạo layout `isForm` khi thiếu; chỉ dùng API công khai."
metadata:
  author: cogover
  version: "1.0.2"
---

# Object Form

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Object Form có ba nhóm cấu hình tương ứng Web App: **General** (`name`, `slug`, `description`, `status`); **Layout** (layout nhập liệu, hành động sau submit, layout/URL thành công); **Settings** (ngôn ngữ, người nhận thông báo, chặn email).

Form không lưu danh sách field hay style riêng: `objectLayoutId` quyết định field, validation và style; `successLayoutId` quyết định trang thành công. Đổi cấu trúc field/style: dùng `$object-layout` rồi gắn ID layout vào form; không đưa cấu hình layout vào payload form.

## Giới hạn public-safe

- Chỉ dùng tài liệu trong skill, API công khai đã mô tả, response API, thông tin người dùng cung cấp và cấu hình/metadata ngoài code đã xác minh.
- Tuyệt đối không đọc, tải, tìm kiếm, phân tích hay reverse-engineer mã nguồn ứng dụng, frontend bundle, source map, static JavaScript/CSS, HTML (để truy vết asset/code), repository, container hay filesystem máy chủ; không dùng chúng để suy ra endpoint, payload, domain hoặc hành vi backend.
- Tài liệu/API công khai không đủ: dừng ở precondition liên quan và yêu cầu người dùng cung cấp hoặc xác nhận; không soi code để lách blocker.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Skill này chỉ dùng nhóm `/api/v1` (phiên Web App), chủ yếu `/api/v1/objects/forms`; ngoại lệ riêng ở [Retry và đối soát](#retry-và-đối-soát).
- `SITE_DOMAIN` (host link public `form.{SITE_DOMAIN}`) là domain đăng ký gốc (`eTLD+1`) của hostname workspace, không phải toàn bộ hostname: `tenant.example.com` → `example.com`, `tenant.example.co.uk` → `example.co.uk`; không lấy máy móc hai label cuối khi public suffix có nhiều label. Hostname là IP, `localhost` hoặc không chắc domain gốc: yêu cầu người dùng cung cấp `SITE_DOMAIN`.
- Đọc toàn bộ [references/api-contract.md](references/api-contract.md) (endpoint, schema, payload mẫu, mã lỗi) trước khi dựng request.

## Quy trình

### 1. Resolve tài nguyên thật

- Object: resolve bằng slug; đầu vào là tên hiển thị thì liệt kê/tìm Object và yêu cầu khớp duy nhất, không đoán slug.
- `objectLayoutId`: layout của đúng Object (API layout trong contract) có `isForm: true` hoặc numeric `isForm: 1`. Với `successAction: 1`, `successLayoutId` là layout cùng Object có khả năng View (`functionLayout: 2` hoặc `3`).
- Cần kiểm tra field, content hoặc style: đọc detail layout; không đoán field nằm trong form chỉ vì field tồn tại trên Object.
- `notifyRelatedUsers`, `notifyOtherUsers`: ID record Personnel thật; không thay bằng email, account ID hay tên hiển thị.

Không có layout `isForm` hợp lệ: **bắt buộc gọi `$object-layout` tạo layout nhập liệu trước**, rồi mới create form.

1. Truyền đúng workspace, `objectTypeSlug` đã resolve và yêu cầu tạo layout Web active cho Object Form: `functionLayout: 1`, quyền `ADD`, `isForm: 1`, `content` hợp lệ.
2. Người dùng đã mô tả field/bố cục: chuyển nguyên yêu cầu đó; chưa mô tả: để `$object-layout` dựng layout mặc định hợp lý từ các field có thể nhập của Object. Yêu cầu tạo form là đủ quyền tạo precondition này: không hỏi lại thông tin đã có, không hỏi xác nhận bổ sung.
3. Không sửa hoặc dùng tạm layout hiện có `isForm: 0`; luôn tạo layout mới.
4. Nhận ID xong, đọc lại layout bằng API trên đúng Object; chỉ dùng khi `objectTypeSlug` khớp exact, `isForm` là `true`/`1`, `functionLayout: 1` và `status: 1`.
5. Tạo layout hoặc post-check thất bại: dừng trước create form và báo rõ bước layout chưa hoàn tất; không create form với layout không hợp lệ.

### 2. Đọc trạng thái hiện tại

- List: `POST /api/v1/objects/forms/search`, `objectSlug` bắt buộc. Có ID: luôn `GET /api/v1/objects/forms/{id}` trước khi sửa, nhân bản hoặc xoá.
- Đối chiếu cả `id`, `objectSlug`, `name` và `slug`; dừng khi không có kết quả hoặc có nhiều kết quả phù hợp.

### 3. Lập payload

- Create: kiểm tra `name`/`slug` qua `POST /api/v1/objects/forms/{objectSlug}/check-exists`, kiểm tra layout, rồi gửi payload đầy đủ theo [schema cấu hình](references/api-contract.md#4-schema-cấu-hình).
- Update: `PATCH` là partial theo field; trường bỏ qua được giữ nguyên, `null` thường cũng không xoá giá trị. Đổi nhiều nhóm: đọc detail rồi merge trên allowlist cấu hình. Không gửi trường server quản lý hay `accessControls`.
- Xoá chuỗi tùy chọn bằng `""`, danh sách bằng `[]`. Đổi success action thì xoá trường nhánh cũ: action `1` đặt `successRedirectUrl: ""`; action `2` đặt `successLayoutId: ""`.
- `autoCreateRecord`: giữ nguyên khi không được yêu cầu đổi (luồng tạo mới Web App mặc định `1` nhưng không có control riêng).
- Không đổi `slug` qua update; backend giữ slug hiện tại. Muốn slug khác: tạo hoặc nhân bản form mới với slug mới khi người dùng yêu cầu rõ.

### 4. Ghi và xác minh

- Create `POST .../create`; update `PATCH .../{id}`; nhân bản `POST .../{id}/duplicate`. Publish/unpublish là `PATCH {"status":1}` / `{"status":0}`; không có endpoint publish riêng.
- Sau mutation, đọc lại detail và so sánh chính xác các trường được yêu cầu; create/duplicate lấy `id` từ `data[0].id` rồi đọc detail. Không dùng public layout endpoint để post-check thông thường (mỗi lần đọc tăng `viewCount`).
- Create/duplicate post-check xong: thực hiện ngay bước Chia sẻ và trả cả hai link, không chờ người dùng hỏi.

### 5. Chia sẻ và truy cập nội bộ

- Link public: `code = Base64("{workspaceId}&{formId}")` rồi ghép `https://form.{SITE_DOMAIN}/{code}`; chỉ dựng sau khi đọc detail có `workspaceId`, `formId`. `status: 1` mới gọi là link truy cập được; `status: 0` vẫn trả URL nhưng nêu rõ chưa truy cập được cho đến khi publish. Chưa chắc `SITE_DOMAIN`: dừng trước create/duplicate và yêu cầu người dùng cung cấp, trừ khi họ yêu cầu rõ vẫn tiếp tục mà chưa có link.
- Link cấu hình nội bộ: `https://{WORKSPACE_DOMAIN}/sales/object/{objectSlug}/form/{formId}` (hostname workspace, sau khi resolve exact `objectSlug` và post-check form). Không phụ thuộc `status` nhưng chỉ truy cập được khi đã đăng nhập workspace và có quyền phù hợp; không gọi đây là link public.
- Embed code theo [mẫu trong contract](references/api-contract.md#6-responses-và-chia-sẻ). Chia sẻ chỉ là dựng URL/HTML; không có API share riêng.

### 6. Xoá an toàn

- Chỉ xoá khi người dùng yêu cầu rõ. Đọc lại mọi ID, bảo đảm cùng `objectSlug`, đọc số response hiện có, nêu danh sách form và ảnh hưởng truy cập sẽ xoá; không mở rộng selection.
- Body gửi một chuỗi ID phân cách bằng dấu phẩy. Sau đó search/detail xác minh không còn form.
- Không xoá form responses chỉ vì xoá hoặc sửa cấu hình form; không tuyên bố response bị cascade hay được giữ lại khi API/tài liệu công khai chưa xác nhận chính sách dữ liệu của deployment.

## Retry và đối soát

- Read timeout/network error: retry tối đa một lần. `429`: tôn trọng `Retry-After`.
- Sau `401`/`403` (tạo lại phiên theo `$cogover-api-auth`) hoặc timeout của create/duplicate/delete/update: không lặp request ghi mù; đối soát bằng search/detail (create/duplicate: tìm theo cặp exact `objectSlug` + `slug`/`name` để tránh tạo trùng) và chỉ retry khi chứng minh mutation chưa áp dụng.
- `r != 0`: đọc `msg`, sửa đúng precondition hoặc payload; không đổi ID/layout ngẫu nhiên để thử tiếp.

## Kết quả bàn giao

Trả operation, Object slug, form ID/name/slug, trạng thái trước/sau, các trường đã đổi và kết quả post-check. Sau create/duplicate luôn kèm hai link Markdown nhãn `Link truy cập biểu mẫu từ bên ngoài` và `Link cấu hình biểu mẫu nội bộ`; thao tác khác trả link public, link nội bộ hoặc embed code khi người dùng yêu cầu. Nêu rõ mọi phần chưa thực hiện do thiếu domain, quyền, ID duy nhất hoặc `SITE_DOMAIN`.
