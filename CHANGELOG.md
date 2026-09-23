# Changelog

## 4.9.0 - 2026-09-23

- Cập nhật `cogover-custom-module` 1.8.0 theo `@cogover/sdk` 0.9.0: bổ sung mã hoá đối xứng AES (`crypto.aesEncrypt`/`aesDecrypt`, AES-128/192/256, GCM mặc định với IV ngẫu nhiên, tag nối cuối ciphertext hoặc `separateTag`, `aad`, CBC khi bên ngoài bắt buộc), mã hoá/giải mã RSA (`rsaEncrypt`/`rsaDecrypt`, OAEP-SHA256 mặc định, OAEP-SHA1, PKCS1, giới hạn kích thước và mã hoá lai với AES) và ký/xác minh RSA, RSA-PSS, ECDSA (`sign`/`verify`, định dạng `der`/`ieee-p1363`, bảng JWT `RS*`/`PS*`/`ES*`); key PEM hoặc `{ secret: name }` (RSA 2048–4096 bit, EC P-256/P-384/P-521), `DECRYPTION_FAILED` khi giải mã thất bại, `verify` trả `false` với chữ ký sai định dạng. SDK API reference (mục Mã hoá và chữ ký tách Hash/HMAC, Key, AES, RSA, chữ ký, Giới hạn), SDK usage guide (mục Mã hoá, giải mã và ký dữ liệu) và Crypto quick start theo bản tài liệu mới; Backend API Reference thêm `POST /api/v1/ts-projects/inbound/list` liệt kê inbound access toàn workspace.
- `SKILL.md`: bảng chọn capability backend thêm dòng mã hoá/chữ ký; bảng tài liệu theo nhánh và điều kiện phiên bản SDK nêu `0.9.0`; bước 1 chốt thuật toán/mode/padding/encoding với bên kia; bước 6A lưu AES key và private key thành secret OPAQUE (PEM qua `--value-file`); bước 8 quy tắc code và kiểm thử round-trip/tương thích; bước 9 kiểm thử crypto trên Workspace; bước 10 bàn giao thuật toán và secret chứa key.

## 4.8.0 - 2026-09-22

- Cập nhật `cogover-custom-module` 1.7.0 theo `@cogover/sdk` 0.8.0 và Dev CLI 0.13.1: bổ sung background job (`defineJob`, named export `jobs`, `jobs.enqueue` với `delayMs`/`runAt`/`idempotencyKey`, lịch cron năm trường với múi giờ IANA, retry bằng `RetryableError`, ít nhất một lần, danh tính system cho run theo lịch/quản trị viên/webhook), secret và credential (`fetch({ credential })` BEARER/BASIC/HEADER với host được phép, `secrets.get` OPAQUE, `crypto.hmacSha256({ secret })`, giới hạn 20 thao tác/invocation), crypto (`sha256`, `hmacSha256`, `randomBytes`, `randomUUID`, `timingSafeEqual`) và inbound webhook (route `/hooks/`, inbound access KEY/HMAC, `invocation.identity === "inbound"`, `request.rawBody`/`contentType`). Thêm bốn quick start `get-started-background-jobs.md`, `get-started-secrets-and-credentials.md`, `get-started-crypto.md`, `get-started-inbound-webhooks.md`; SDK usage guide và SDK API reference lên 0.8.0 (mục Background job, Secret và credential, Mã hoá và chữ ký, Inbound webhook, `InboundInvocationContext`, before-change từ chối thêm `jobs.enqueue`/`secrets.get`/HMAC bằng secret); Backend API Reference thêm mục Secret, Inbound access, Background job, Theo dõi toàn workspace, Gọi inbound webhook và `triggerManifest` của version.
- `SKILL.md`: thêm mục "Chọn capability backend" (route, trigger before/after-change, background job, credential, secret, crypto, inbound webhook, push message, state/locks: khi nào dùng và giới hạn); bảng tài liệu theo nhánh thêm bốn quick start mới và repo mẫu [cogover-sdk-samples](https://github.com/cogover/cogover-sdk-samples) (mỗi file một route theo nhóm API, trigger/job mẫu, catalog `GET /`); bước 1 chốt contract job/secret/inbound; bước 3 đổi thành chọn record trigger, background job hoặc Process (backend có lịch qua `schedule` của job); bước 5 policy `allowInternalSystem` cho run theo lịch/quản trị viên và lời gọi inbound; bước 6 giới hạn Development Session với secret/job/inbound; bước 6A mới tạo secret/credential (`cogover-dev secrets set`) và inbound access (`cogover-dev inbound create`, key chỉ trả một lần); bước 7 điều kiện SDK 0.8.0/CLI 0.13.1 và export `jobs`; bước 8 quy tắc code job/secret/crypto/inbound và giới hạn máy chủ local; bước 9 validate job manifest, lịch khi activate, kiểm thử job (`cogover-dev jobs`), secret và webhook thật; bước 10 bàn giao bảng job, metadata secret/inbound access không kèm giá trị.
- `cli-session-and-delivery.md`: lệnh `secrets`, `inbound`, `jobs`, `auth logout` (CLI 0.13.1) dùng Workspace API key với quyền SuperAdmin, giá trị qua prompt ẩn/stdin/file, inbound key hiển thị một lần. `batch-writes-and-checkpoints.md`: tiếp tục việc dài bằng background job tự enqueue với cursor thay vì quay lại Process.

## 4.7.0 - 2026-09-21

- Cập nhật `cogover-custom-module` 1.6.0: bổ sung push message của `@cogover/sdk` 0.7.0 (`push.refreshRecords` làm mới record đang mở, `push.toast`, `push.message` ngầm; người nhận `"viewers"` hoặc personnel ID, `exclude: ["actor"]`; best-effort, không thu hồi, một capability call mỗi lời gọi, bị từ chối trong trigger before-change và Development Session chỉ đọc, `PUSH_DISABLED`). SDK usage guide và SDK API reference lên 0.7.0 (mục Push message, `push` trong context script/route/trigger); Record trigger quick start theo bản tài liệu mới nhất (response mẫu `objects/list`, ghi chú số thứ tự version, bỏ mục xử lý sự cố `trigger-runner.test.ts`).
- `SKILL.md`: bảng chọn loại module, bảng tài liệu theo nhánh và điều kiện phiên bản SDK nêu push message; bước 8 thêm quy tắc dùng push (after-change gọi `refreshRecords` sau khi sửa record, giới hạn người nhận khi thử trên local, không suy đoán API lắng nghe phía client); bước 9 xác minh push trên trình duyệt; bước 10 bàn giao nơi gọi/loại message/người nhận.

## 4.6.0 - 2026-09-21

- Cập nhật `cogover-custom-module` 1.5.0: bổ sung record trigger của Custom Backend Module (`@cogover/sdk` 0.6.0, Dev CLI 0.10.0): thêm `get-started-record-trigger.md` (khai báo `defineTrigger` và export `triggers`, chạy trigger local qua `/__cogover/triggers/<key>`, publish/activate, kiểm thử bằng thay đổi bản ghi thật với `r: 70` `BEFORE_CHANGE_TRIGGER_REJECTED`, `meta`/`messages`, `$record`, `503` `BEFORE_CHANGE_TRIGGER_FAILED`, `TRIGGER_MANIFEST_INVALID`); cập nhật SDK usage guide và SDK API reference lên 0.6.0 (mục Record trigger, trigger filter, quy tắc before-change chỉ đọc/fail-closed, after-change best-effort/idempotent/`RetryableError`, `records.getMany`, mã lỗi `RETRYABLE`); Backend quick start thêm `trigger-runner.ts`, `npm test` và lệnh chạy thử trigger local.
- `SKILL.md`: bước 3 đổi thành chọn record trigger (quy tắc áp cho mọi nguồn ghi, trước/sau khi lưu) hay Process (luồng có người tham gia, chờ/hẹn giờ, thông báo, AI Agent, lịch); bước 1 chốt contract từng trigger; bước 2 cho phép trigger before-change gán field chỉ backend ghi qua `writableFields`; bước 5 danh tính handler và `allowInternalSystem`; bước 6–8 điều kiện SDK/CLI, quy tắc code trigger, chạy trigger local; bước 9 validate manifest, phạm vi ảnh hưởng khi activate, kiểm thử bằng bản ghi thật và rollback; bước 10 bàn giao bảng trigger.

## 4.5.6 - 2026-09-16

- Cập nhật `object-info` 1.0.4: mục "Cờ tạo và sửa thủ công" trong `api-object-fields.md`: `creatable` (checkbox Cho phép tạo thủ công) chặn request public tạo record có gửi field, `manual_modify_allow` (checkbox Cho phép sửa thủ công) chặn request public cập nhật chạm field, đều `r: 47`; hai cờ độc lập và không tác động ghi nội bộ (`data.asSystem()`, Process); field chỉ backend ghi đặt `creatable: 0` và `manual_modify_allow: false`; `editable` được đồng bộ theo `manual_modify_allow`; `objects/list` không trả `creatable`. Mặc định khi tạo field gửi thêm `creatable: 1`. Kiểm chứng trên Workspace ngày 2026-09-16.
- Cập nhật `cogover-custom-module` 1.4.4: bước ghi schema tạo field chỉ backend ghi với `creatable: 0` và `manual_modify_allow: false`, không thay bằng security rule `exclude`.

## 4.5.5 - 2026-09-16

- Cập nhật `cogover-custom-module` 1.4.3: production trả đúng HTTP status handler đã chọn (`400`, `404`, `409`, `422`...) như local, body lỗi trong transport envelope có `r` bằng HTTP status và `code`; `cli-session-and-delivery.md` (mục xử lý lỗi) và `batch-writes-and-checkpoints.md` bỏ mô tả cũ về việc production trả HTTP 400 cho mọi lỗi handler hoặc 200 cho custom status. Status khác 200 chỉ đi qua production khi body là một JSON object. Kiểm chứng trên Workspace ngày 2026-09-16.

## 4.5.4 - 2026-09-16

- Cập nhật `object-record` 1.0.4: cấu trúc giá trị field `long_text` phụ thuộc số định dạng bật trong `metaData.text_types` (`1` plain text, `2` rich text HTML, `3` markdown), không phụ thuộc field có WYSIWYG hay không: bật đúng 1 định dạng (kể cả metadata kiểu cũ `rich_text: "Yes"`) thì ghi/đọc chuỗi thuần; bật từ 2 định dạng thì ghi object `{"text_type", "value"}` và đọc về chuỗi JSON phải parse; bỏ trống field từ 2 định dạng gửi `{"text_type":1,"value":null}` và khi đọc coi rỗng cả bốn trường hợp. API không validate cấu trúc nên phải đọc lại giá trị sau khi ghi; không ghi vào field bóng `_hidden_<slug>`. Sửa mục A, bảng kiểu trường, mục tạo kèm ảnh, bảng lỗi và `wysiwyg-long-text-images.md` theo quy tắc này. Kiểm chứng trên Workspace ngày 2026-09-16.
- Cập nhật `object-info` 1.0.3: mô tả `text_type`/`text_types` của `long_text` đủ ba định dạng, ý nghĩa số phần tử `text_types` với giá trị record và metadata kiểu cũ thiếu `text_types`.

## 4.5.3 - 2026-09-16

- Cập nhật `user-permission` 1.1.4: mô tả lại Object Security Rules thành hai cổng độc lập theo họ rule: rule `type: 1` giữ cổng tạo record, rule `type: 2` giữ cổng xem/sửa/xoá; mỗi cổng chỉ chuyển sang mặc định từ chối khi họ rule của nó có rule active, cổng còn lại không đổi (chặn tạo bắt buộc có rule type 1 active; rule View một mình đã khoá sửa/xoá). `filter` của rule type 1 được đánh giá trên dữ liệu gửi lên khi tạo (`conditions: []` là mọi dữ liệu; có điều kiện thì chỉ record thoả điều kiện mới được tạo). Sửa mục mô hình đánh giá quyền, bảng bốn rule, rule giữ chỗ, cảnh báo an toàn khi bật/tắt rule, reference API và ma trận kiểm thử. Kiểm chứng trên Workspace ngày 2026-09-16.

## 4.5.2 - 2026-09-16

- Cập nhật `cogover-custom-module` 1.4.2: mọi request `/api/v1/ts-projects/...` (service `3` production, `4` quản lý, `6` preview) phải gửi `x-req-type: 6` cùng `x-req-service`; thiếu `x-req-type: 6` thì service `4` bị Authorization Server xử lý như logout (`deletedTokens`, thu hồi phiên), service `3` trả `r: 5000`, service `6` trả `r: 5001`. Bổ sung header vào mọi ví dụ HTTP/cURL của hai API reference, quick start backend và `cli-session-and-delivery.md`. Kiểm chứng trên Workspace ngày 2026-09-16. Bước 2A ghi rõ rule Create `type: 1` vẫn gửi `filter` rỗng.
- Cập nhật `user-permission` 1.1.3: mọi payload tạo security rule phải có `filter`, kể cả rule Create `type: 1` và rule giữ chỗ Create (server tạo Filter record kèm rule; thiếu thì `r: 600` bọc 422 `logicType required`). Sửa bảng chọn loại rule, bảng bốn rule, bảng slot giữ chỗ và payload mẫu giữ chỗ Create sang `filter: {"logicType":"AND","logic":"","conditions":[]}`; thêm mã lỗi `600`. Kiểm chứng trên hai Workspace ngày 2026-09-16 (rule giữ chỗ active chặn tạo record trực tiếp `r: 36`).

## 4.5.1 - 2026-09-15

- Cập nhật `cogover-custom-module` 1.4.1: đổi tên `api-reference.md` thành `cogover-sdk-api-reference.md` để phân biệt với hai API reference HTTP; thêm `cogover-sdk-usage-guide.md` (hướng dẫn sử dụng `@cogover/sdk` 0.5.0: bắt đầu nhanh, filter/sort, fetch, state, lock, chọn danh tính, TypeScript config, router) và yêu cầu sub-agent backend đọc trước khi code.

## 4.5.0 - 2026-09-15

- Cập nhật `cogover-custom-module` 1.4.0: Custom Frontend Module có ba dạng single page app, custom component (nhúng layout Object qua item Federation component, thao tác form bằng `formBuilder.execScript`) và Federation Page (trang trong ứng dụng tại `/{APP_SLUG}/c{N}/{PATH}`, gắn được vào menu); thêm `get-started-custom-module.md` với bảng chọn nhanh và câu hỏi xác định dạng.
- Thêm bước 1A: agent trình bày lựa chọn loại module/dạng frontend kèm lý do, phương án thay thế và tác động, chờ người dùng xác nhận rõ ràng trước khi tạo Project, clone template hoặc code; đổi dạng giữa chừng phải xác nhận lại.
- Thêm `get-started-custom-component.md` và `get-started-federation-page.md` (snapshot tài liệu sản phẩm ngày 2026-09-15). Với hai dạng này, sub-agent frontend bắt buộc clone `custom-frontend-module-template` và đọc các skill trong `.agents/skills` của template trước khi code; bước 4, 7–10 và `full-stack-integration.md` bổ sung khởi tạo, kiểm thử local, cấu hình layout/menu, gọi backend qua HTTP client của template và bàn giao theo từng dạng.
- Cập nhật `object-layout` 1.1.0: bổ sung component `federation_component` (item Federation component nhúng custom component của Custom Frontend Module, trường `federationUrl` dạng `{slugSlot}/Components/<Tên>`) vào schema, danh mục component đặc biệt, prefix slug và quy trình "Đưa Federation component vào layout"; schema quan sát từ Layouts V2 `view` trên layout Xem/sửa và đã kiểm chứng `PUT` giữ nguyên component. `cogover-custom-module` bước 9 và quick start custom component trỏ sang quy trình này.

## 4.4.1 - 2026-09-14

- Cập nhật `process-creator` 1.3.1: bổ sung định dạng link một lượt chạy `https://{WORKSPACE_DOMAIN}/process/process-instances/{INSTANCE_ID}?processId={PROCESS_ID}&processInfoId={PROCESS_INFO_ID}` (mục 4.3, `api-process-runtime.md`); báo cáo kiểm thử và `runtime-validation.md` yêu cầu kèm link từng lượt chạy bên cạnh link process và instance ID.

## 4.4.0 - 2026-09-13

- Cập nhật `process-creator` 1.3.0: kích hoạt, xuất bản, bỏ xuất bản, vô hiệu hoá và quản lý version (danh sách, lưu thành version mới, đổi version hiện hành, rollback) hoàn toàn qua Web App API; thêm `api-process-lifecycle.md`.
- Thêm `api-process-runtime.md`: tạo lượt chạy Manual/Normal/Sequence, đọc lượt chạy đang ở node nào và đã qua node nào, đọc và submit form User Task, rollback bước, tạm dừng/tiếp tục/huỷ/xoá lượt chạy, đọc giá trị resource, ma trận chuyển trạng thái và mã lỗi.
- Mục 4.4 ưu tiên tạo version mới thay cho xoá/tạo lại process đã kích hoạt; mục 4.6 chuyển toàn bộ vòng kích hoạt và kiểm thử sang API, bỏ các bước thao tác trên Chrome.
- `runtime-validation.md` thêm bảng kịch bản kiểm thử qua API (đường đi kỳ vọng, nhánh gateway, validate form, rollback, tạm dừng/huỷ, quyền, version, bỏ xuất bản).
- Hợp đồng và mã lỗi đã được chạy thử trên Workspace ngày 2026-09-13 với Manual Flow và Normal Flow; `api-process-builder.md` ghi nhận response có thể được bọc trong envelope `body`.

## 4.3.1 - 2026-09-13

- Cập nhật `agent-builder` 1.1.1: System Prompt chỉ mô tả nghiệp vụ, không nhắc `activate_skill`, CORE/EXTENDED, slug Skill hay tên công cụ hệ thống vì nền tảng tự chèn các hướng dẫn này lúc chạy; mẫu System Prompt bỏ dòng "kích hoạt kỹ năng mở rộng".
- Ma trận test bổ sung kiểm tra Agent không gọi `activate_skill` cho Skill CORE đã nạp sẵn.

## 4.3.0 - 2026-09-11

- Cập nhật `agent-builder` 1.1.0: thực hiện workflow qua API/HTTP/WebSocket; bỏ các nhánh tự chuyển sang trình duyệt.
- Hướng dẫn test nghiệp vụ và duyệt Tool qua API, ghi rõ các contract còn thiếu để người dùng bổ sung; phân biệt giới hạn probe với thiếu API.
- Probe báo thiếu contract tương quan lượt hoặc cần quyết định duyệt, không còn hướng dẫn dùng Chrome.

## 4.2.0 - 2026-09-11

- Thêm `agent-builder` 1.0.0: hướng dẫn cấu hình Agent, model/reasoning, danh tính thực thi, System Prompt, Skill CORE/EXTENDED, Tool, phân quyền và Data/RAG.
- Bổ sung contract Web App API, workflow chuyển đổi/duyệt/index tài liệu và kiểm thử chat qua Chrome/WebSocket. Có probe kết nối với self-test offline; phân biệt kiểm tra cấu hình, transport và nghiệp vụ.
- Cập nhật danh mục song ngữ thành 23 skill.

## 4.1.0 - 2026-09-11

Đợt rà soát toàn bộ 22 skill để gọn hơn, ít token hơn và không trùng lặp; mọi hướng dẫn đặc thù Cogover được giữ nguyên ý.

- Mỗi skill nâng PATCH. Tổng dung lượng `SKILL.md` giảm 44% (663 KB → 375 KB), tổng prose giảm 24%, description trong frontmatter giảm 30% và đều dưới 370 ký tự.
- `cogover-api-auth` là nguồn chung mới cho quản lý credential, chuẩn hoá domain và quy ước request/response/lỗi (`r: 0`, 401/403, tạo lại phiên Web App, đọc lại sau khi ghi); các skill khác chỉ còn một dòng link và ngoại lệ riêng.
- Gộp nội dung trùng chéo skill bằng link: tham chiếu Cogover Scripting dùng bản trong `object-info`; danh mục điều kiện lọc dùng bản trong `object-record` (thêm mục "Dùng trong Process"); `process-creator` xoá hai bản sao.
- Tách nội dung tra cứu dài sang `references/`: `object-layout` (5 file), `process-creator` (5 file), `user-permission` (2), `cogover-overview`, `object-info`, `layout-scripting` (đổi thư mục `reference/` thành `references/`).
- `create-cogover-objects`: workbook mẫu `Objects_for_CRM.xlsx` chuẩn hoá theo spec (đủ 15 dòng thuộc tính đúng thứ tự, Object info ở dòng 18-21, Selective field từ dòng 24) và 33 trường tiền đổi từ `Currency` sang `Decimal`.
- Sửa đúng: giá trị `short_text` trong `object-filter`; cờ `--apply` cho mutation trong `dashboard-builder`; validator `state-transitions` của `build-cogover-app` khớp contract 11 cột; lệnh gọi skill lỗi thời; thuật ngữ nội bộ và ID trông như thật trong tài liệu public.
