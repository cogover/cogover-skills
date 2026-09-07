---
name: object-form
description: "Cấu hình biểu mẫu Cogover dùng để thu thập dữ liệu bên ngoài vào một Object bằng Web App API `/api/v{N}`: tìm kiếm/xem chi tiết, tạo, sửa, bật/tắt, nhân bản, xoá, chọn layout nhập liệu và trang thành công, tự gọi `$object-layout` tạo layout `isForm` khi còn thiếu, thiết lập ngôn ngữ/thông báo/chặn email, tạo URL public, URL cấu hình nội bộ hoặc mã nhúng, và đọc phản hồi để chẩn đoán. Sử dụng khi cần quản lý Object Form/Lead Form, form công khai, form thu thập dữ liệu, trạng thái publish, success action hoặc response của form mà không thao tác trình duyệt. Chỉ dùng tài liệu và API công khai; không đọc hoặc reverse-engineer mã nguồn ứng dụng."
metadata:
  author: cogover
  version: "1.0.1"
---

# Object Form

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

## Phạm vi

Quản lý cấu hình Object Form bằng API, không thao tác UI trình duyệt. Cấu hình có ba nhóm tương ứng Web App:

1. **General**: `name`, `slug`, `description`, `status`.
2. **Layout**: layout nhập liệu, hành động sau submit và layout/URL thành công.
3. **Settings**: ngôn ngữ, người nhận thông báo và chặn email.

Form không lưu danh sách field hay style riêng. `objectLayoutId` quyết định field, validation và style của form; `successLayoutId` quyết định trang thành công. Khi yêu cầu thay đổi cấu trúc field hoặc style, dùng `$object-layout` rồi gắn ID layout vào form. Không tự đưa cấu hình layout vào payload form.

### Giới hạn public-safe

- Chỉ dùng tài liệu trong skill, API công khai đã được mô tả, response API, thông tin người dùng cung cấp và cấu hình/metadata ngoài code đã được xác minh.
- Tuyệt đối không đọc, tải, tìm kiếm, phân tích hoặc reverse-engineer mã nguồn ứng dụng; frontend bundle, source map, static JavaScript/CSS; HTML để truy vết asset/code; repository; container hay filesystem máy chủ. Không dùng các nguồn này để suy ra endpoint, payload, domain hoặc hành vi backend.
- Khi tài liệu/API công khai không cung cấp thông tin cần thiết, dừng ở precondition liên quan và yêu cầu người dùng cung cấp hoặc xác nhận; không soi code để lách blocker.

## Chuẩn bị bắt buộc

1. Lấy `WORKSPACE_DOMAIN`, API Key, Object đích và ý định đọc/ghi từ ngữ cảnh; chuẩn hoá domain thành hostname chữ thường, không protocol, port, path hay dấu `/` cuối. Từ hostname workspace, lấy domain đăng ký gốc (`registrable domain`/`eTLD+1`) làm `SITE_DOMAIN`; ví dụ `tenant.example.com` → `example.com`, `tenant.example.co.uk` → `example.co.uk`. Không đơn giản lấy hai label cuối khi public suffix có nhiều label. Nếu hostname là IP, `localhost` hoặc không thể xác định chắc domain gốc, yêu cầu người dùng cung cấp `SITE_DOMAIN`; không đọc code để tìm domain. Không in hoặc lưu API Key/token/cookie.
2. **Bắt buộc gọi `$cogover-api-auth`** và đọc reference của skill đó trước mọi request. Các endpoint quản trị trong skill này dùng `/api/v1/...`; không gửi API Key trực tiếp dưới dạng Bearer tới chúng.
3. Dùng API Key gọi `POST /bapi/v1/auth-token`, rồi gửi đủ cookie `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` và hai header `x-csrf-token`, `x-xsrf-token` theo `$cogover-api-auth`.
4. Đọc toàn bộ [references/api-contract.md](references/api-contract.md) trước khi dựng request. Chỉ coi thao tác thành công khi HTTP phù hợp và response có `r: 0`.

## Quy trình

### 1. Resolve tài nguyên thật

- Resolve Object bằng slug; nếu đầu vào là tên hiển thị, liệt kê/tìm Object và yêu cầu khớp duy nhất. Không đoán slug.
- Resolve layout bằng API layout trên đúng Object. Chọn `objectLayoutId` từ layout có `isForm: true` hoặc numeric `isForm: 1`.
- Khi `successAction: 1`, chọn `successLayoutId` từ layout cùng Object có khả năng View (`functionLayout: 2` hoặc `3`).
- Đọc chi tiết layout khi cần kiểm tra field, content hoặc style. Không đoán field nằm trong form chỉ vì field tồn tại trên Object.
- Resolve `notifyRelatedUsers` và `notifyOtherUsers` thành ID record Personnel thật; không gửi email, account ID hay tên hiển thị thay cho ID.

Nếu không có layout `isForm` hợp lệ, **bắt buộc gọi `$object-layout` để tạo layout nhập liệu trước**, rồi mới tiếp tục create form:

1. Truyền đúng workspace, `objectTypeSlug` đã resolve và yêu cầu tạo layout Web active dành cho Object Form. Layout mới phải có `functionLayout: 1`, quyền `ADD`, `isForm: 1` và `content` hợp lệ; giữ mọi API key/token trong cơ chế credential an toàn hiện tại.
2. Nếu người dùng đã mô tả field/bố cục, chuyển nguyên yêu cầu đó cho `$object-layout`. Nếu chưa mô tả, để `$object-layout` dựng layout form mặc định hợp lý từ các field có thể nhập của Object; coi yêu cầu tạo form là đủ quyền tạo precondition này, không hỏi xác nhận bổ sung.
3. Không sửa hoặc dùng tạm layout hiện có có `isForm: 0`. Tạo layout mới để tránh thay đổi hành vi của layout đang được màn hình khác sử dụng.
4. Sau khi `$object-layout` trả ID, đọc lại layout bằng API trên đúng Object và chỉ dùng khi `objectTypeSlug` khớp exact, `isForm` là `true`/`1`, `functionLayout` là `1` và `status` là `1`.
5. Nếu tạo layout hoặc post-check thất bại, dừng trước create form và báo rõ bước layout chưa hoàn tất; không gọi create form để thử với layout không hợp lệ.

### 2. Đọc trạng thái hiện tại

- Liệt kê form bằng `POST /api/v1/objects/forms/search` với `objectSlug` bắt buộc.
- Nếu có ID, luôn đọc `GET /api/v1/objects/forms/{id}` trước khi sửa, nhân bản hoặc xoá.
- Đối chiếu cả `id`, `objectSlug`, `name` và `slug`; dừng khi không có kết quả hoặc có nhiều kết quả phù hợp.

### 3. Lập payload

- Với create, kiểm tra trước `name`/`slug` qua `POST /api/v1/objects/forms/{objectSlug}/check-exists`, kiểm tra layout, rồi gửi payload đầy đủ theo reference.
- Với update, hiểu rằng `PATCH` là field-wise partial: trường bị bỏ qua được giữ nguyên, `null` thường cũng không xoá giá trị. Tuy vậy, trước thay đổi nhiều nhóm, đọc detail rồi merge trên allowlist cấu hình để tránh mất ý định. Không gửi các trường server quản lý hoặc `accessControls`.
- Dùng `""` để xoá chuỗi tùy chọn và `[]` để xoá danh sách. Khi chuyển success action, xoá trường của nhánh cũ: action `1` đặt `successRedirectUrl: ""`; action `2` đặt `successLayoutId: ""`.
- Giữ nguyên `autoCreateRecord` khi người dùng không yêu cầu đổi. Luồng tạo mới Web App mặc định `1` nhưng không có control riêng cho trường này.
- Không cố đổi `slug` qua update; backend giữ slug hiện tại. Muốn slug khác, tạo/nhân bản form mới với slug mới sau khi người dùng yêu cầu rõ.

### 4. Ghi và xác minh

- Create bằng `POST .../create`; update bằng `PATCH .../{id}`; nhân bản bằng `POST .../{id}/duplicate`.
- Bật/publish bằng `PATCH {"status":1}`; tắt/unpublish bằng `PATCH {"status":0}`. Không có endpoint publish riêng.
- Sau mutation, đọc lại detail và so sánh chính xác các trường được yêu cầu. Với create/duplicate, lấy `id` từ `data[0].id` rồi đọc detail.
- Sau create/duplicate post-check thành công, bắt buộc thực hiện bước Chia sẻ và trả cả link truy cập biểu mẫu từ bên ngoài lẫn link cấu hình form nội bộ; không chờ người dùng hỏi riêng về link.
- Không dùng public layout endpoint để post-check thông thường vì mỗi lần đọc làm tăng `viewCount`.

### 5. Chia sẻ và truy cập nội bộ

- Với create/duplicate, link public là đầu ra bắt buộc. Dựng `SITE_DOMAIN` từ domain đăng ký gốc (`eTLD+1`) của `WORKSPACE_DOMAIN` theo Bước Chuẩn bị, không đọc frontend bundle, source map, static asset, HTML hay repository. Nếu không xác định chắc domain gốc, dừng trước create/duplicate và yêu cầu người dùng cung cấp `SITE_DOMAIN`, trừ khi họ yêu cầu rõ vẫn tiếp tục mà chưa có link.
- Chỉ dựng link sau khi đã đọc detail và có `workspaceId`, `formId`. Xác nhận `status: 1` để gọi đó là link truy cập được; nếu `status: 0`, vẫn trả URL đã dựng nhưng nêu rõ form chưa thể truy cập cho đến khi publish.
- Tạo `code = Base64("{workspaceId}&{formId}")`, rồi ghép `https://form.{SITE_DOMAIN}/{code}`. `SITE_DOMAIN` là domain đăng ký gốc của workspace, không phải toàn bộ hostname workspace; ví dụ workspace `tenant.example.com` tạo link trên host `form.example.com`.
- Tạo link cấu hình nội bộ bằng `https://{WORKSPACE_DOMAIN}/sales/object/{objectSlug}/form/{formId}` sau khi đã resolve exact `objectSlug` và post-check form. Link này không phụ thuộc `status`, nhưng chỉ truy cập được khi người dùng đã đăng nhập workspace và có quyền phù hợp; không gọi đây là link public.
- Sau create/duplicate, trả hai URL bằng link Markdown có nhãn `Link truy cập biểu mẫu từ bên ngoài` và `Link cấu hình biểu mẫu nội bộ`, cùng form ID/name/slug và trạng thái post-check.
- Tạo embed code theo mẫu trong reference. Chia sẻ chỉ là phép dựng URL/HTML; không có API share riêng.

### 6. Xoá an toàn

- Chỉ xoá khi người dùng yêu cầu rõ. Đọc lại mọi ID, bảo đảm chúng thuộc cùng `objectSlug`, đọc số response hiện có, nêu danh sách form và ảnh hưởng truy cập sẽ xoá, rồi không mở rộng selection.
- Gửi một chuỗi ID phân cách bằng dấu phẩy trong body. Sau đó search/detail để xác minh không còn form.
- Không xoá form responses chỉ vì xoá hoặc sửa cấu hình form. Không tuyên bố response sẽ bị cascade hay giữ lại nếu API/tài liệu công khai chưa xác nhận chính sách dữ liệu của deployment.

## Retry và đối soát

- Với read timeout/network error: retry tối đa một lần.
- Với `401/403`: tạo lại phiên theo `$cogover-api-auth`; không lặp request ghi trước khi đối soát trạng thái.
- Với `429`: tôn trọng `Retry-After`.
- Với timeout của create/duplicate/delete/update: không retry mù quáng. Đối soát bằng search/detail; chỉ retry khi chứng minh mutation chưa áp dụng.
- Với `r != 0`: đọc `msg`, sửa đúng precondition hoặc payload; không đổi ID/layout ngẫu nhiên để thử tiếp.
- Với create/duplicate không chắc kết quả: tìm theo cặp exact `objectSlug` + `slug`/`name` trước khi gọi lại để tránh tạo trùng.

## Kết quả bàn giao

Trả về operation, Object slug, form ID/name/slug, trạng thái trước/sau, các trường đã đổi và kết quả post-check. Sau create/duplicate, luôn trả cả `Link truy cập biểu mẫu từ bên ngoài` và `Link cấu hình biểu mẫu nội bộ`; với thao tác khác, trả link public, link nội bộ hoặc embed code khi người dùng yêu cầu. Không tiết lộ cookie/token. Nêu rõ mọi phần chưa thực hiện do thiếu domain, quyền, ID duy nhất hoặc `SITE_DOMAIN`.
