---
name: dashboard-builder
description: "Quản lý dashboard Cogover qua Web App API `/api/v{N}/dashboard-server` (phiên Web App từ $cogover-api-auth, không nhận API Key trực tiếp): tạo, đọc, cập nhật, nhân bản, xoá; component/biểu đồ từ saved report của $report-builder, layout, dashboard filter; chẩn đoán dashboard không hiển thị đúng. Dùng khi cấu hình dashboard bằng API."
metadata:
  author: cogover
  version: "1.0.1"
---

# Dashboard Builder

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-11`

Quản lý dashboard bằng API, không thao tác UI, theo chuỗi: xác nhận workspace → tạo phiên Web App → đọc state → lập payload đầy đủ → mutation → đọc lại và kiểm chứng. Saved report và report field cho chart do `$report-builder` tạo và preview trước; skill này không tạo report.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Mọi thao tác gọi `POST /api/v1/dashboard-server` bằng phiên Web App đổi từ API Key; không gửi API Key trực tiếp tới endpoint này. Ngoại lệ riêng: kiểm tra mã nghiệp vụ ở cả `r` top-level và `body.r` ([Response và kiểm chứng](references/api-contract.md#response-và-kiểm-chứng)); lỗi đặc thù ở [Xử lý lỗi](#xử-lý-lỗi).
- Đọc [references/api-contract.md](references/api-contract.md) (service, payload, ràng buộc field) trước khi gọi API; đọc [references/dashboard-model.md](references/dashboard-model.md) trước khi thêm hoặc sửa component, chart, layout, dashboard filter.
- Contract chỉ lấy từ tài liệu trong skill, tài liệu API chính thức do người dùng cung cấp và response API thực tế; không đọc source code, repository, bundle JavaScript hay source map; không dùng browser/UI để suy ra request (`/settings/dashboards` chỉ là deep-link trả cho người dùng).
- Sau khi tạo phiên, probe chỉ đọc bằng service `6`; dừng khi `401/403`, `r != 0`, workspace lệch hoặc response khác contract.
- Helper script [scripts/dashboard_api.py](scripts/dashboard_api.py): base URL và API Key qua biến môi trường hoặc secret manager; mặc định dry-run, thêm `--execute` để gửi, mutation (service `3`, `4`, `5`, `20`) thêm `--apply`.

  ```bash
  python3 scripts/dashboard_api.py --service 6 --payload '{"size":20,"page":1,"filters":[]}' --execute
  ```

## Quy trình

### 1. Chuẩn hoá yêu cầu

Xác định workspace; thao tác (tạo, sửa, nhân bản, xoá); `name`, `slug`, `description`, `layoutSize` (`9` hoặc `12`), `colorPalette`; component cần có, saved report nguồn và field dùng cho group/measure/filter; bố cục và tiêu chí nghiệm thu. Dashboard đích, report nguồn, metric, filter hoặc phạm vi xoá còn mơ hồ: hỏi trước mutation.

### 2. Đọc state và resolve ID

Service `6`: list với pagination, sort, filters; detail với `getDetail: true` và filter `slug = ...` hoặc `id = ...` ([List và detail](references/api-contract.md#list-và-detail)). Chỉ thao tác khi resolve đúng một dashboard; tên khớp nhiều resource thì dừng và yêu cầu chọn bằng ID/slug.

### 3. Chuẩn bị saved report và chart

Với chart dựa trên báo cáo:

1. Dùng `$report-builder` tìm hoặc tạo saved report và preview đúng trước khi tạo chart; đọc saved report detail lấy ID/slug và report field ID thật. Không gán object field ID vào nơi yêu cầu report field ID.
2. Chọn `type` và lập `config` theo [references/dashboard-model.md](references/dashboard-model.md). Không tự dựng config phức tạp từ phỏng đoán: deep-copy một component cùng `type` đang chạy đúng từ API response làm base, chỉ thay `reportId`, field ID, tiêu đề, filter, palette; giữ key chưa biết.
3. Tạo UUID mới cho `chartId`; `location.i` và `config.chartId` bằng đúng `chartId`.

### 4. Tạo dashboard

1. Kiểm tra trùng `slug`/`name` bằng service `6`; lập payload theo [Create và update](references/api-contract.md#create-và-update).
2. Dashboard có chart: validate trước khi gửi — không trùng `chartId`; mỗi component đủ `type`, `location`, `config`; layout không vượt grid; saved report tham chiếu tồn tại.
3. Gọi service `3`, rồi đọc detail theo slug và đối chiếu toàn bộ metadata/component.

### 5. Sửa dashboard

Service `4` thay thế toàn bộ cấu hình theo payload, không partial:

1. Đọc detail mới nhất (service `6`, `getDetail: true`); deep-parse chuỗi JSON nếu gateway trả serialized JSON.
2. Deep-copy response, loại field server-managed ở root (`created`, `updated`, `createdBy`, `updatedBy`, `workspaceId`); payload gửi đủ `id` và mọi field create bắt buộc.
3. Chỉ đổi phần người dùng yêu cầu, áp lên đúng component theo `chartId` (không theo array index); giữ nguyên `components[].id`, `slug`, config, filter và layout key chưa sửa.
4. Validate như bước 4.2, gọi service `4`, đọc lại detail và so sánh postcondition.

Xoá một chart: chỉ bỏ component tương ứng khỏi `components`; không xoá saved report nguồn trừ khi người dùng yêu cầu riêng.

### 6. Nhân bản dashboard

Service `20` với `id` nguồn cùng `name`/`slug` mới đã kiểm tra trùng ([Delete và duplicate](references/api-contract.md#delete-và-duplicate)); backend sao chép component/filter, không nhân bản bằng update. Đọc detail theo slug mới để xác minh.

### 7. Xoá dashboard

1. Resolve ID, đọc detail cuối cùng và trình bày đúng danh sách ID sẽ xoá; chỉ tiếp tục khi người dùng yêu cầu rõ dashboard đích và xác nhận phạm vi, nhất là khi có nhiều ID.
2. Gọi service `5` với `{ "ids": [...] }`, rồi service `6` theo từng ID/slug để xác minh không còn resource.
3. Không dùng delete để rollback thao tác dở dang: giữ resource và báo ID/slug/trạng thái.

### 8. Chẩn đoán dashboard không hiển thị đúng

Đọc detail và đối chiếu từng component với [references/dashboard-model.md](references/dashboard-model.md) (định danh `chartId`/`location.i`/`config.chartId`; layout trong grid và kích thước tối thiểu; `reportId` và report field ID thật; filter `isDynamic`, `params`, `fieldId`/`filtersReplace`), preview lại saved report nguồn bằng `$report-builder`, rồi sửa theo bước 5.

### 9. Trả kết quả

- Workspace domain; operation; dashboard ID, name, slug; layout, palette, số component và mapping chart → saved report; filter/config chính đã thay đổi; kết quả postcondition và warning còn lại.
- Deep-link `https://{WORKSPACE_DOMAIN}/settings/dashboards/{DASHBOARD_SLUG}`; chỉ mở deep-link để kiểm chứng UI khi người dùng yêu cầu.

## Xử lý lỗi

| Lỗi | Cách xử lý |
|---|---|
| `r = 5001` / `Can not found processor for request: service=...` | Thử lại đúng request bằng literal `curl` thay cho `urllib`. `curl` PASS: lỗi client transport, tiếp tục bằng `curl`. `curl` cũng lỗi: dừng, báo endpoint, service/type và workspace. Không đổi service number bằng thử ngẫu nhiên. |
| `Slug already exists` / `Name already exists` | Đọc resource trùng trước khi đề xuất slug/name mới. |
| Timeout | Read: retry tối đa một lần. Mutation: list lại theo slug/ID trước mọi retry. |
| Response khác contract | Dừng mutation, lưu bản đã lọc secret; không đoán ID. |
