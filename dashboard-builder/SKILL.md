---
name: dashboard-builder
description: Tạo, đọc, cấu hình, cập nhật, nhân bản và xoá dashboard Cogover qua Web App API `/api/v{N}/dashboard-server`, gồm metadata, bố cục, component/biểu đồ và dashboard filter. Sử dụng khi người dùng yêu cầu quản lý dashboard Cogover bằng API, chuyển một saved report thành biểu đồ dashboard, sửa chart/layout/filter hiện có, hoặc chẩn đoán dashboard không hiển thị đúng; bắt buộc phối hợp với `$cogover-api-auth` vì API `/api/v{N}` không nhận API Key trực tiếp.
metadata:
  author: cogover
  version: "1.0.0"
---

# Dashboard Builder

- **Phiên bản:** `1.0.0`
- **Ngày phát hành:** `2026-08-23`

Quản lý dashboard bằng API, không thao tác UI. Xử lý theo chuỗi: xác nhận workspace → tạo phiên Web App → đọc state → lập payload đầy đủ → mutation → đọc lại và kiểm chứng.

## Đọc tài liệu theo tác vụ

- Luôn đọc [references/api-contract.md](references/api-contract.md) trước khi gọi API.
- Đọc [references/dashboard-model.md](references/dashboard-model.md) trước khi thêm/sửa component, chart, layout hoặc dashboard filter.
- Dùng `$report-builder` trước khi dashboard cần saved report hoặc report field chưa tồn tại.

## Quy tắc bắt buộc

1. Gọi và tuân thủ `$cogover-api-auth` trước mọi request. Endpoint dashboard là `/api/v1/...`; không gửi API Key trực tiếp đến endpoint này.
2. Dùng API Key chỉ cho `POST /bapi/v1/auth-token`, sau đó gửi đủ cookie `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` và hai header `x-csrf-token`, `x-xsrf-token` cho `/api/v1/dashboard-server`.
3. Chỉ dùng contract đóng gói trong skill, tài liệu API chính thức do người dùng cung cấp và response API thực tế. Không đọc hoặc tìm kiếm source code, repository, bundle JavaScript, source map hay mã ứng dụng để khám phá contract.
4. Không dùng browser hoặc UI để suy ra request. URL `/settings/dashboards` chỉ là deep-link trả cho người dùng.
5. Không ghi, echo hoặc commit API key, cookie hay token. Nhận bí mật qua biến môi trường hoặc secret manager.
6. Kiểm tra trùng `slug` và `name` trước create. Sau timeout của mutation, list lại theo `slug`/`id` trước khi retry.
7. Update là thay thế cấu hình dashboard ở mức payload. Luôn đọc detail mới nhất, sửa trên bản sao đầy đủ và giữ nguyên component/filter/key chưa định thay đổi.
8. Không tự dựng config chart phức tạp từ phỏng đoán. Dùng contract trong reference, saved report thực tế và ưu tiên clone config cùng loại đã chạy đúng từ API response.
9. Không coi HTTP 200 là thành công. Kiểm tra `r`/`msg` ở cả top-level và `body`, rồi xác minh postcondition bằng service list/detail.
10. Delete chỉ khi người dùng yêu cầu rõ dashboard đích. Resolve ID từ slug/name, trình bày đúng danh sách ID sẽ xoá, rồi mới gọi service `5`.
11. Không tự rollback bằng delete. Nếu workflow dừng giữa chừng, giữ resource và báo ID/slug/trạng thái.

## Quy trình

### 1. Chuẩn hoá yêu cầu

Xác định:

- Workspace base URL/domain.
- Tạo mới, sửa, nhân bản hay xoá.
- Tên, slug, mô tả, số cột (`9` hoặc `12`) và color palette.
- Component cần có, saved report nguồn, field dùng cho group/measure/filter.
- Bố cục mong muốn và tiêu chí nghiệm thu.

Hỏi lại trước mutation nếu dashboard đích, report nguồn, metric, filter hoặc phạm vi xoá còn mơ hồ.

### 2. Tạo và kiểm tra phiên

1. Dùng `$cogover-api-auth` để đổi API Key thành phiên Web App.
2. Đối chiếu `workspaceDomain`/`workspaceId` trong response auth với workspace đích.
3. Gọi service `6` như probe chỉ đọc. Dừng khi `401/403`, `r != 0`, workspace lệch hoặc response không có contract mong đợi.

Nếu dùng helper script, thiết lập base URL và API Key bằng biến môi trường hoặc secret manager rồi chạy script đi kèm:

```bash
python3 scripts/dashboard_api.py \
  --service 6 --payload '{"size":20,"page":1,"filters":[]}' --execute
```

### 3. Đọc state và resolve ID

- List: service `6` với pagination, sort và filters.
- Detail theo slug: service `6` với `getDetail: true` và filter `slug = ...`.
- Detail theo ID: service `6` với `getDetail: true` và filter `id = ...`.

Resolve đúng một dashboard. Nếu tên khớp nhiều resource, dừng và yêu cầu chọn bằng ID/slug.

### 4. Chuẩn bị saved report và chart

Với chart dựa trên báo cáo:

1. Dùng `$report-builder` để tìm/tạo saved report đã preview đúng.
2. Đọc saved report detail và lấy ID/slug cùng report field ID thật.
3. Chọn `TypeChart` và lập config theo [references/dashboard-model.md](references/dashboard-model.md).
4. Với config phức tạp, lấy một component cùng loại đã chạy đúng từ API response làm base, rồi thay tối thiểu `reportId`, field IDs, tiêu đề, filter và palette.
5. Tạo UUID riêng cho `chartId`; đặt `location.i` đúng bằng `chartId`.

Không gán object field ID vào nơi yêu cầu report field ID.

### 5. Tạo dashboard

1. Kiểm tra trùng slug/name bằng service `6`.
2. Chuẩn hoá slug chữ thường; dùng `layoutSize` là số nguyên `9` hoặc `12`.
3. Với dashboard trống, gửi `components: []`, `filterData: null`.
4. Với dashboard có chart, kiểm tra mọi `chartId`, `type`, `location`, `config` và tham chiếu saved report.
5. Gọi service `3`; sau đó list detail theo slug và đối chiếu toàn bộ metadata/component.

### 6. Sửa dashboard

1. Đọc detail mới nhất bằng service `6`.
2. Deep-copy response và loại field server-managed như `created`, `updated`, `createdBy`, `updatedBy` khỏi write payload.
3. Chỉ sửa phần người dùng yêu cầu; giữ component/filter/config/key chưa biết.
4. Đảm bảo payload có `id` và toàn bộ các field create bắt buộc.
5. Gọi service `4`, đọc lại detail và so sánh postcondition.

Khi xoá một chart khỏi dashboard, chỉ bỏ component tương ứng khỏi `components`; không xoá saved report nguồn trừ khi người dùng yêu cầu riêng.

### 7. Xoá dashboard

1. Resolve ID và đọc detail cuối cùng.
2. Xác nhận đúng phạm vi, đặc biệt khi có nhiều ID.
3. Gọi service `5` với `{ "ids": ["..."] }`.
4. Gọi service `6` theo từng ID/slug để xác minh không còn resource.

### 8. Trả kết quả

Trả ngắn gọn nhưng đủ audit:

- Workspace domain, không kèm token.
- Operation, dashboard ID, name, slug.
- Layout, palette, số component và mapping chart → saved report.
- Filter/config chính đã thay đổi.
- Kết quả postcondition và warning còn lại.
- Deep-link: `https://{WORKSPACE_DOMAIN}/settings/dashboards/{DASHBOARD_SLUG}`.

## Xử lý lỗi

| Lỗi thường gặp | Hướng xử lý ngắn |
|---|---|
| `Can not found processor for request: service=...` | Thử lại đúng request bằng literal `curl` thay cho `urllib`. Nếu `curl` PASS, phân loại lỗi client transport và tiếp tục bằng `curl`; chỉ kết luận processor không khả dụng khi `curl` cũng lỗi. Không đổi service number bằng thử ngẫu nhiên. |

- `401/403`: tạo lại phiên hoặc kiểm tra quyền; không retry mutation.
- HTTP 200 nhưng `r != 0`: coi là lỗi nghiệp vụ; đọc `msg`, không tiếp tục.
- `r = 5001` hoặc “Can not found processor”: áp dụng bảng trên trước; không đổi service number bằng thử ngẫu nhiên. Nếu literal `curl` vẫn lỗi, dừng và báo endpoint, service/type cùng workspace.
- `Slug already exists`/`Name already exists`: đọc resource trùng trước khi đề xuất slug/name mới.
- Timeout ở read: retry tối đa một lần. Timeout ở mutation: đọc lại theo slug/ID trước mọi retry.
- Response shape lạ: lưu bản redacted, dừng mutation và không đoán ID.
