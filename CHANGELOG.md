# Changelog

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
