# Changelog

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
