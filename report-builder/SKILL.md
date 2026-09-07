---
name: report-builder
description: Tạo, cấu hình, cập nhật và kiểm chứng Report Type cùng saved report trên Cogover qua Public Report API. Sử dụng khi người dùng yêu cầu tạo báo cáo một hoặc nhiều object (tối đa 5 object), chọn quan hệ và kiểu join, thêm report field/section, cấu hình cột hiển thị, group, aggregate, filter, sort hoặc formula, chạy preview, sửa báo cáo hiện có, hay chẩn đoán báo cáo Cogover không trả đúng dữ liệu.
metadata:
  author: cogover
  version: "1.0.1"
---

# Report Builder

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

Tạo báo cáo Cogover theo chuỗi phụ thuộc: phân tích nghiệp vụ → khám phá object → Report Type → relation/section/field → saved report → preview và xác minh. Chỉ tạo Dashboard khi người dùng yêu cầu bằng một workflow khác; skill này dừng ở saved report đã chạy đúng.

## Đọc tài liệu theo tác vụ

- Luôn đọc [references/api-contract.md](references/api-contract.md) trước khi gọi Report API.
- Đọc [references/report-modeling.md](references/report-modeling.md) trước khi chọn primary object, relation, join, section hoặc report field.
- Đọc [references/report-settings.md](references/report-settings.md) trước khi tạo/cập nhật `setting`, filter, group, aggregate, formula hoặc gọi service `200`.

Không suy ra contract còn thiếu từ ví dụ. Với endpoint, envelope, payload và ràng buộc, chỉ dùng Public Report API contract; với ID và resource backend tự sinh, ưu tiên response thực tế của workspace mục tiêu. Khi tài liệu và response mâu thuẫn, dừng mutation, nêu rõ phạm vi mâu thuẫn và không tự trộn hai contract.

## Quy tắc bắt buộc

1. Dùng `$object-info` để lấy object, field, option và related list thực tế của workspace. Không dùng ID mẫu trong tài liệu.
2. Ưu tiên Report Type chỉ có 1 object khi object đó đã chứa đủ dữ liệu cần thiết. Chỉ dùng nhiều object khi nghiệp vụ yêu cầu, tối đa 5 object kết nối bằng tối đa 4 relation. Quan hệ bổ sung có thể tăng chi phí truy vấn; đo preview với dữ liệu và bộ lọc đại diện thay vì giả định một tỷ lệ chậm cố định.
3. Dùng service `223` hoặc metadata quan hệ có `object_relation_id` thật để xác minh relation. Không biến ID related-list thành ID relation bằng phỏng đoán.
4. Với Report Type nhiều object, mọi graph edge phải có `lookup_type` và `source_name` đúng chiều UI. Không coi hai key này là metadata trình bày; thiếu chúng có thể đảo “Tra cứu từ” thành “Tra cứu tới” dù service `221` vẫn trả relation đúng.
5. Chỉ dùng `POST https://{WORKSPACE_DOMAIN}/bapi/v1/report` với envelope `{ "service": <number>, "payload": <object> }`.
6. Không gửi `workspace_id`, personnel ID hoặc thông tin xác thực trong `payload`; access token xác định workspace và người dùng.
7. Không ghi, echo hoặc commit API key. Không đưa token thật vào lệnh shell, file payload, `SKILL.md`, reference hay kết quả trả về.
8. Kiểm tra trùng trước mọi create. Sau timeout của mutation, đọc lại state bằng slug/name/ID trước khi quyết định thử lại.
9. Không tự động xóa để rollback. Khi lỗi giữa chừng, giữ nguyên resource đã tạo và báo ID/trạng thái để người dùng quyết định.
10. Không coi HTTP status riêng lẻ là thành công. Kiểm tra cả HTTP status, `r`, `msg` và postcondition bằng API đọc.
11. Không sửa ACL hoặc folder theo kiểu partial. Trước service `207`, đọc detail và gửi lại state cần giữ vì `acl` và `folder_id` có semantics thay thế.
12. Sau khi tạo và xác minh thành công, luôn trả cho người dùng deep-link trực tiếp đến Report Type và saved report. Dùng Report Type ID cùng report slug thực tế, không dùng URL trang danh sách hoặc slug/ID phỏng đoán.

## Quy trình

### 1. Chuẩn hóa yêu cầu báo cáo

Chuyển yêu cầu thành một report contract ngắn:

- Câu hỏi nghiệp vụ và đơn vị đo.
- Population/mẫu số và event/tử số nếu là tỷ lệ.
- Dimension/group theo hàng, group theo cột và kỳ thời gian.
- Metric cùng phép aggregate.
- Cột chi tiết, filter, sort, top-N và yêu cầu hiển thị detail row.
- Quyền xem/sửa và thư mục đích nếu người dùng nêu.
- Tiêu chí nghiệm thu bằng một hoặc hai kết quả mong đợi.

Nêu giả định có thể đảo ngược. Hỏi lại trước mutation khi join, population, công thức tỷ lệ hoặc quyền chia sẻ còn mơ hồ và có thể làm sai kết quả.

### 2. Xác nhận workspace và xác thực

Lấy workspace domain và API key từ ngữ cảnh bảo mật hoặc biến môi trường `COGOVER_WORKSPACE_DOMAIN` và `COGOVER_API_KEY`. Nếu thiếu, yêu cầu người dùng cung cấp qua cơ chế bí mật phù hợp.

Chạy một probe chỉ đọc, ví dụ service `215`, rồi đối chiếu `workspaceDomain` trong response nếu có. Dừng khi domain/token không khớp, HTTP `401/403`, hoặc response không chứng minh được workspace mục tiêu.

### 3. Khám phá object và thiết kế graph

Gọi `$object-info` với `includeFields`, `includeRelatedLists`, `includeOptions` và `includeMetaData`. Thực hiện lần lượt:

1. Xác định object chứa population gốc làm `primary_object`.
2. Kiểm tra trước liệu toàn bộ field cần thiết đã có trên primary object hay chưa. Nếu có, dùng Report Type 1 object; nếu không, chọn số object ít nhất cần thiết để trả lời yêu cầu và không thêm object chỉ vì có relation.
3. Tìm một graph liên thông, không lặp relation, tối đa 4 cạnh.
4. Xác minh `object_relation_id`, chiều `src_object_id → dst_object_id` và field nối bằng service `223` hoặc metadata chính thức.
5. Với từng cạnh, xác định object cha trên graph và chọn `lookup_type`: `2` khi object cha là relation source (“Tra cứu từ alias cha”), `1` khi object cha là relation destination (“Tra cứu tới alias cha”). Gán `source_name` bằng alias của node cha (`A`, `B`, ...).
6. Chọn `INNER = 1` khi chỉ cần bản ghi khớp; chọn `LEFT = 2` khi phải giữ toàn bộ population bên trái. Kiểm tra cardinality trước khi tính count/tỷ lệ.
7. Lập danh sách field tối thiểu cho group, aggregate, filter, sort, công thức và cột hiển thị.

Không tuyên bố tỷ lệ conversion là chính xác nếu quan hệ one-to-many làm trùng mẫu số mà API chỉ hỗ trợ `count`, không có distinct count phù hợp.

### 4. Tìm và tái sử dụng Report Type

Dùng service `215` để tìm Report Type cùng mục đích. Chỉ tái sử dụng khi cùng primary object, relation graph, field cần thiết và trạng thái phù hợp. Xác minh bằng:

- `215`: detail Report Type.
- `221`: relation đã cấu hình.
- `211`: section.
- `222`: report field.

Nếu không tương thích, tạo Report Type mới thay vì làm hỏng báo cáo đang dùng chung.

### 5. Tạo Report Type

Thực hiện theo thứ tự và ghi lại ID sau mỗi bước:

1. Gọi `212` để tạo Report Type. Dùng slug ổn định, `category: "OTHER"` và trạng thái có chủ đích (`0` draft, `1` development, `2` deployed). Public API không nhận `meta_data` trong bước này.
2. Luôn gọi `202` đúng một lần để khởi tạo Report Config. Với một object, gửi `relations: []`, `src_object_id` là primary object và root graph trong `meta_data`. Với nhiều object, gửi toàn bộ `relations` cùng graph node/edge đầy đủ; không gửi `src_object_id` chỉ để thay relation.
3. Không dùng `meta_data: "{}"`; service `202` yêu cầu graph đầy đủ. Root graph tối thiểu phải có `nodeRoot`, `edges: []` và viewport. Graph nhiều object phải theo đầy đủ contract `lookup_type`/`source_name` trong [references/report-modeling.md](references/report-modeling.md).
4. Sau `202`, đọc `211` và `222`. Tái sử dụng default section cùng field hệ thống backend đã tạo; không tự tạo `workspace_id`, `object_type` hoặc pseudo-field tương tự. Chỉ gọi `208` khi thật sự cần thêm section; dùng `section_index: 1000` cho section mới và để backend quyết định index persisted.
5. Gọi `227` cho từng field nghiệp vụ chưa tồn tại và giữ thứ tự `index_in_section`. Lấy `field_name` từ display `name` mà object API trả về; chỉ dùng translation metadata làm fallback, không tự dịch hoặc đổi nhãn. Dùng `field_type: 0` cho field trực tiếp; chỉ dùng `field_type: 1` cùng dotted lookup path được object metadata hoặc Public Report API xác nhận.
6. Đọc lại bằng `215`, `221`, `211`, `222`. Xác minh root metadata, relation, default section, field hệ thống và mapping field nghiệp vụ. Với mỗi edge, kiểm tra `lookup_type`, `source_name`, parent/child object và biểu thức UI tương đương `source.field = destination.id`; không chỉ dựa vào service `221`. Không chuyển sang saved report cho đến khi mọi field nghiệp vụ có ID report field thực (`FRP...` hoặc prefix thực tế của response).

Nếu create response không có schema ID rõ ràng, không đoán đường dẫn. Dùng slug/name ổn định và API list/detail để resolve ID.

### 6. Lập cấu hình saved report

Ánh xạ object field sang report field ID vừa tạo. Tạo `setting` đầy đủ theo [references/report-settings.md](references/report-settings.md), rồi kiểm tra:

- `displayFieldIds` chứa `{ "data": "<REPORT_FIELD_ID>" }` và không chứa field đang group.
- `groupByRows` và `groupByColumns` tối đa 2 field mỗi mảng; chỉ group cột khi có group hàng.
- `groupTypeMap` chỉ dùng field ngày đang group.
- `aggregates` chỉ dùng operation và data type hợp lệ.
- `logicSequence` khớp số thứ tự `filterItems`.
- `rowFormulas`, `summaryFormulas`, cutoff, sort và relation filter thỏa Public API contract.

Không tự sáng tác shape filter. Nếu Public API contract chưa mô tả operator hoặc `params` cho data type cần dùng, dừng trước mutation và nêu chính xác phần contract còn thiếu.

### 7. Tạo và hoàn thiện saved report

1. Kiểm tra slug bằng service `239`; đọc response thực tế thay vì giả định tên field boolean.
2. Gọi `201` với `report_type`, `name`, slug/description và một base `setting` đầy đủ. Chỉ truyền ACL/folder khi đã xác định chính xác.
3. Resolve saved report bằng ID trả về hoặc service `229` theo slug.
4. Đọc detail hiện tại, merge cấu hình cuối cùng vào toàn bộ `setting` hiện có, rồi gọi `207` khi cần cập nhật group/aggregate/filter/view. Giữ cả key chưa biết thay vì dựng lại setting từ base template. Gửi lại `folder_id` và `acl` hiện tại nếu muốn giữ nguyên.
5. Chuyển ACL hiện tại về write shape tương đương về semantics; không sao chép `created`, `updated`, `created_by`, `updated_by`, ACL ID hay field server-managed từ payload mẫu/response vào update.
6. Gọi lại `229` và đối chiếu từng phần của `setting` với report contract.

### 8. Chạy và xác minh dữ liệu

Gọi service `200` với `report_id` là Report Type ID; saved report chỉ cung cấp `setting` và tham chiếu `report_type`. Sau đó kiểm tra:

- Có rows/summary đúng với kiểu báo cáo, kể cả trường hợp kết quả hợp lệ là rỗng.
- Group, aggregate, sort, filter và total khớp Public API contract.
- Không có warning hoặc mã cấu hình không hợp lệ chưa xử lý.
- Kết quả thỏa ví dụ nghiệm thu; với tỷ lệ, kiểm tra numerator/denominator riêng trước khi tính phần trăm.

Nếu service chạy bất đồng bộ, không coi mọi HTTP `400` là lỗi cuối cùng; đọc `r`/`msg` và chỉ theo cơ chế hoàn tất đã được response hoặc contract hiện tại chứng minh.

### 9. Trả kết quả

Trả về ngắn gọn nhưng đủ để audit:

- Workspace domain, không kèm token.
- Report Type: ID, tên, slug, primary object, relation và join.
- Sections và mapping object field → report field ID.
- Saved report: ID, tên, slug, folder/ACL ở mức mô tả.
- Cấu hình: display, group, aggregate, filter, sort, formula, detail row.
- Kết quả preview và warning còn lại.
- Resource đã tạo dở nếu có lỗi.
- Hai URL trực tiếp, bắt buộc khi resource đã được tạo và xác minh:
  - Report Type: `https://{WORKSPACE_DOMAIN}/settings/report-types/{REPORT_TYPE_ID}`
  - Saved report: `https://{WORKSPACE_DOMAIN}/settings/reports/{REPORT_SLUG}`

Chuẩn hóa `WORKSPACE_DOMAIN` thành hostname trước khi ghép URL. Nếu đầu vào là URL đầy đủ như `https://workspace.example.com`, dùng hostname `workspace.example.com` để không tạo URL sai dạng `https://https://...`. Trả các URL dưới dạng link có thể bấm được.

## Dùng công cụ API đi kèm

Dùng [scripts/report_api.py](scripts/report_api.py) để tạo envelope, validate payload cơ bản và gọi Public Report API mà không in token.

```bash
export COGOVER_BASE_URL='https://workspace.example.com'
# Thiết lập COGOVER_API_KEY qua secret store hoặc phiên shell riêng; không paste token vào command/log.

python3 scripts/report_api.py \
  --service 215 \
  --payload '{"page":0,"size":20}' \
  --execute
```

Mặc định script chỉ in dry-run. Thêm `--execute` để gửi request; mutation còn yêu cầu `--apply`:

```bash
python3 scripts/report_api.py \
  --service 212 \
  --payload-file /path/to/report-type.json \
  --execute --apply
```

Không dùng `--apply` như thay thế cho việc kiểm tra precondition. Luôn đọc response thô và xác minh postcondition bằng service đọc.

## Xử lý lỗi và retry

- `401/403`: dừng và yêu cầu token hợp lệ; không retry.
- `429`: tôn trọng `Retry-After`; không tạo vòng retry nhanh.
- Timeout/network error ở read: retry tối đa một lần.
- Timeout ở mutation: không retry ngay; tìm resource bằng slug/name/ID trước.
- `r != 0`: đọc `msg`, giữ nguyên resource đã tạo, sửa đúng payload rồi mới tiếp tục.
- Response shape lạ: lưu output đã redacted, không tự chọn một ID “có vẻ đúng”.
- Delete/rollback: chỉ thực hiện khi người dùng yêu cầu rõ resource ID và đã xác nhận phạm vi ảnh hưởng.
