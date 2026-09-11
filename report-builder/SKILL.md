---
name: report-builder
description: "Tạo, cấu hình, cập nhật và kiểm chứng Report Type cùng saved report Cogover qua Public Report API `/bapi/v1/report`: báo cáo 1–5 object, chọn relation và kiểu join, report field/section, cột hiển thị, group, aggregate, filter, sort, formula, preview và xác minh dữ liệu; chẩn đoán báo cáo không trả đúng dữ liệu. Phối hợp $object-info."
metadata:
  author: cogover
  version: "1.0.2"
---

# Report Builder

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Tạo và kiểm chứng báo cáo Cogover qua Public Report API: mọi service gọi `POST https://{WORKSPACE_DOMAIN}/bapi/v1/report` (API Key Bearer) với envelope `{ "service": <number>, "payload": <object> }`. Chuỗi phụ thuộc: phân tích nghiệp vụ → khám phá object → Report Type → relation/section/field → saved report → preview và xác minh. Skill dừng ở saved report đã chạy đúng; dashboard thuộc `$dashboard-builder` và chỉ làm khi người dùng yêu cầu.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Riêng skill này: xác nhận workspace bằng một probe chỉ đọc (ví dụ service `215`) và đối chiếu `workspaceDomain` trong response nếu có; dừng khi domain/token không khớp hoặc response không chứng minh được workspace mục tiêu. Không gửi `workspace_id`, personnel ID hay thông tin xác thực trong `payload`: token đã xác định workspace và người dùng.
- Đọc [references/api-contract.md](references/api-contract.md) trước khi gọi Report API; [references/report-modeling.md](references/report-modeling.md) trước khi chọn primary object, relation, join hoặc dựng graph `meta_data`; [references/report-settings.md](references/report-settings.md) trước khi dựng/cập nhật `setting`, filter, group, aggregate, formula hoặc gọi service `200`.
- Endpoint, envelope, payload và ràng buộc: chỉ theo Public Report API contract, không suy từ ví dụ. ID và resource backend tự sinh: theo response thực tế của workspace mục tiêu. Tài liệu và response mâu thuẫn: dừng mutation, nêu rõ phạm vi mâu thuẫn, không tự trộn hai contract.
- Object, field, option và related list thực tế: lấy qua `$object-info` (`includeFields`, `includeRelatedLists`, `includeOptions`, `includeMetaData`); không dùng ID mẫu trong tài liệu.
- Kiểm tra trùng trước mọi create. Không tự xóa để rollback: lỗi giữa chừng thì giữ nguyên resource đã tạo và báo ID/trạng thái để người dùng quyết định; delete chỉ khi người dùng nêu rõ resource ID và đã xác nhận phạm vi ảnh hưởng.

## Quy trình

### 1. Chuẩn hóa yêu cầu

Chuyển yêu cầu thành report contract ngắn: câu hỏi nghiệp vụ và đơn vị đo; population/mẫu số và event/tử số nếu là tỷ lệ; grain (một row đại diện record nào); dimension group theo hàng, theo cột và kỳ thời gian; metric cùng phép aggregate; cột chi tiết, filter, sort, top-N và detail row; dạng output (detail list, summary, pivot hay tỷ lệ); quyền xem/sửa và thư mục đích nếu người dùng nêu; tiêu chí nghiệm thu bằng một hoặc hai kết quả mong đợi.

Nêu giả định có thể đảo ngược. Hỏi lại trước mutation khi join, population, công thức tỷ lệ hoặc quyền chia sẻ còn mơ hồ và có thể làm sai kết quả.

### 2. Khám phá object và thiết kế graph

Theo [references/report-modeling.md](references/report-modeling.md):

1. `primary_object` là object chứa population gốc. Primary object đã đủ field cần thiết thì dùng Report Type 1 object; nếu không, chọn số object ít nhất đủ trả lời yêu cầu, không thêm object chỉ vì có relation. Tối đa 5 object nối bằng tối đa 4 relation; graph liên thông từ primary object, không lặp relation. Quan hệ bổ sung có thể tăng chi phí truy vấn: đo bằng preview với dữ liệu và bộ lọc đại diện, không giả định một tỷ lệ chậm cố định.
2. Xác minh `object_relation_id`, chiều `src_object_id → dst_object_id` và field nối bằng service `223` hoặc metadata quan hệ chính thức; không biến ID related-list thành ID relation bằng phỏng đoán.
3. Với từng cạnh, xác định object cha trên graph rồi gán `lookup_type` và `source_name` theo [Hướng lookup trong graph UI](references/report-modeling.md#hướng-lookup-trong-graph-ui). Thiếu hai key này, UI có thể đảo "Tra cứu từ" thành "Tra cứu tới" dù service `221` vẫn trả relation đúng.
4. Chọn `relation_type`: `1` Inner khi chỉ cần bản ghi khớp, `2` Left khi phải giữ toàn bộ population bên trái. Kiểm tra cardinality trước khi tính count/tỷ lệ: API chỉ hỗ trợ `count`, không có distinct count, nên không tuyên bố tỷ lệ conversion chính xác khi quan hệ one-to-many làm trùng mẫu số.
5. Lập danh sách field tối thiểu cho group, aggregate, filter, sort, công thức và cột hiển thị.

### 3. Tìm và tái sử dụng Report Type

Dùng service `215` tìm Report Type cùng mục đích. Chỉ tái sử dụng khi cùng primary object, relation graph, field cần thiết và trạng thái phù hợp, xác minh bằng `215` (detail), `221` (relation), `211` (section), `222` (report field). Không tương thích thì tạo Report Type mới thay vì làm hỏng báo cáo đang dùng chung.

### 4. Tạo Report Type

Theo thứ tự, ghi lại ID sau mỗi bước:

1. `212` tạo Report Type: slug ổn định, `category: "OTHER"`, trạng thái có chủ đích (`0` draft, `1` development, `2` deployed). Public API không nhận `meta_data` ở bước này.
2. `202` khởi tạo Report Config, gọi đúng một lần kể cả khi không có relation. Một object: `relations: []`, `src_object_id` là primary object, root graph trong `meta_data`. Nhiều object: toàn bộ `relations` cùng graph node/edge đầy đủ; không gửi `src_object_id` chỉ để thay relation. Không dùng `meta_data: "{}"`: root graph tối thiểu có `nodeRoot`, `edges: []` và viewport; graph nhiều object theo [Payload nhiều object](references/report-modeling.md#payload-nhiều-object).
3. Đọc `211` và `222`. Tái sử dụng default section và field hệ thống backend đã tạo (`workspace_id`, `object_type`): không tự tạo pseudo-field hay gọi `227` tái tạo chúng, mặc định loại chúng khỏi display, group, filter và aggregate. Chỉ gọi `208` khi thật sự cần thêm section, với `section_index: 1000` và để backend quyết định index persisted.
4. `227` cho từng field nghiệp vụ chưa tồn tại, giữ thứ tự `index_in_section`; chỉ lấy object field active. `field_name` là display `name` mà object API trả về (translation metadata chỉ làm fallback; không tự dịch hoặc đổi nhãn). `field_type: 0` cho field trực tiếp, với `object_type_id` của object sở hữu field và slug trực tiếp; `field_type: 1` chỉ với dotted lookup path được object metadata hoặc Public Report API xác nhận. `field_data_type` trong response không thay thế discriminator `field_type`. Ghi mapping `{object_id, object_field_slug} → report_field_id` từ response `227`/`222`.
5. Đọc lại `215`, `221`, `211`, `222`: xác minh root metadata, relation, default section, field hệ thống và mapping field nghiệp vụ. Với mỗi edge kiểm tra `lookup_type`, `source_name`, parent/child object và biểu thức UI tương đương `source.field = destination.id`; không chỉ dựa vào `221`. Chỉ sang saved report khi mọi field nghiệp vụ có ID report field thực (`FRP...` hoặc prefix thực tế của response).

Create response không có ID ở path rõ ràng: không đoán path; resolve bằng slug/name ổn định qua API list/detail.

### 5. Dựng setting cho saved report

Ánh xạ object field sang report field ID vừa tạo, dựng `setting` đầy đủ theo [references/report-settings.md](references/report-settings.md) và rà [Checklist](references/report-settings.md#checklist). Operator/`params` của filter, key sort hoặc formula chưa được contract hay response thực tế xác nhận: dừng trước mutation và nêu chính xác phần contract còn thiếu, không tự sáng tác shape.

### 6. Tạo và hoàn thiện saved report

1. Kiểm tra slug bằng service `239`; đọc response thực tế thay vì giả định tên field boolean.
2. `201` với `report_type`, `name`, slug/description và base `setting` đầy đủ. Chỉ truyền ACL/folder khi đã xác định chính xác.
3. Resolve saved report bằng ID trả về hoặc `229` theo slug.
4. Khi cần cập nhật group/aggregate/filter/view: đọc detail hiện tại, merge cấu hình cuối vào toàn bộ `setting` hiện có (giữ cả key chưa biết, không dựng lại từ base template) rồi gọi `207`. `acl` và `folder_id` có semantics thay thế: gửi lại giá trị hiện tại nếu muốn giữ nguyên, ACL chuyển về write shape tương đương về semantics; không sao chép `created`, `updated`, `created_by`, `updated_by`, ACL ID hay field server-managed từ response/payload mẫu vào update.
5. Gọi lại `229` và đối chiếu từng phần của `setting` với report contract.

### 7. Chạy và xác minh dữ liệu

Gọi service `200` với `report_id` là Report Type ID (saved report chỉ cung cấp `setting` và tham chiếu `report_type`); payload chuyển đổi theo [Chuyển setting thành service 200](references/report-settings.md#chuyển-setting-thành-service-200). Kiểm tra: rows/summary đúng với kiểu báo cáo, kể cả khi kết quả hợp lệ là rỗng; group, aggregate, sort, filter và total khớp contract; không còn warning hoặc mã cấu hình không hợp lệ chưa xử lý; kết quả thỏa ví dụ nghiệm thu, với tỷ lệ thì kiểm tra numerator/denominator riêng trước khi tính phần trăm.

### 8. Trả kết quả

Ngắn gọn nhưng đủ audit: workspace domain (không kèm token); Report Type (ID, tên, slug, primary object, relation, join); section và mapping object field → report field ID; saved report (ID, tên, slug, folder/ACL ở mức mô tả); cấu hình display, group, aggregate, filter, sort, formula, detail row; kết quả preview và warning còn lại; resource đã tạo dở nếu có lỗi. Khi resource đã tạo và xác minh, bắt buộc kèm hai link bấm được, dùng Report Type ID và report slug thực tế (không dùng URL trang danh sách hay giá trị phỏng đoán) và ghép từ hostname đã chuẩn hóa để không sinh `https://https://...`:

- Report Type: `https://{WORKSPACE_DOMAIN}/settings/report-types/{REPORT_TYPE_ID}`
- Saved report: `https://{WORKSPACE_DOMAIN}/settings/reports/{REPORT_SLUG}`

## Dùng công cụ API đi kèm

[scripts/report_api.py](scripts/report_api.py) dựng envelope, validate payload (key bắt buộc theo service; `relation_type`, `lookup_type`, `filter_type`, `size`, số relation/group; graph `meta_data`: mỗi edge khớp đúng một relation, `source_name` khớp alias node cha, `lookup_type` khớp hướng parent/child) rồi gọi API với output đã redact token.

- Tham số: `--service <số>`; `--payload '<JSON>'` hoặc `--payload-file <path|->` (`-` đọc stdin); `--workspace-domain` (mặc định lấy `COGOVER_BASE_URL`, rồi `COGOVER_WORKSPACE_DOMAIN`; chỉ nhận `https://<host>`, không path/query); `--timeout` giây (mặc định 60); `--execute` để gửi thật, mặc định chỉ dry-run in `endpoint`, `request`, `warnings`; `--apply` bắt buộc thêm với mọi service ngoài nhóm đọc (gồm `200`, `211`, `215`, `220`, `221`, `222`, `223`, `229`, `230`, `239`, `246`). `COGOVER_API_KEY` đọc từ môi trường khi `--execute`; đặt qua secret store hoặc phiên shell riêng, không paste vào command/log.
- Exit code: `0` thành công; `2` payload/cấu hình không hợp lệ; `3` HTTP lỗi hoặc `r != 0`; `4` lỗi mạng.
- Warning dry-run phải xử lý trước khi gửi: `212` có `meta_data`; `207` thiếu `folder_id`/`acl`; `202`/`231` có relation nhưng thiếu `meta_data`; `200` `filter_type: 3` thiếu `logic_sequence`.
- `--apply` không thay thế kiểm tra precondition. Luôn đọc response thô và xác minh postcondition bằng service đọc.

```bash
export COGOVER_BASE_URL='https://workspace.example.com'
python3 scripts/report_api.py --service 215 --payload '{"page":0,"size":20}' --execute
python3 scripts/report_api.py --service 212 --payload-file /path/to/report-type.json --execute --apply
```

## Xử lý lỗi và retry

Ngoài quy ước chung của `$cogover-api-auth`:

- `429`: chờ theo `Retry-After`; không đổi payload, không gửi song song, không tạo vòng retry nhanh.
- Timeout/network khi đọc: retry tối đa một lần. Timeout khi ghi (`201`, `202`, `207`, `208`, `212`, `227`...): không retry ngay; tìm resource bằng slug/name/ID và kiểm tra relation/field trước khi gọi lại.
- `r != 0`: đọc `msg`, giữ nguyên resource đã tạo, sửa đúng payload rồi mới tiếp tục.
- Response shape lạ: lưu output đã redacted; không tự chọn một ID "có vẻ đúng".
- Service `200` chạy bất đồng bộ: không coi mọi HTTP `400` là lỗi cuối cùng; đọc `r`/`msg` và chỉ theo cơ chế hoàn tất mà response hoặc contract hiện tại chứng minh.
