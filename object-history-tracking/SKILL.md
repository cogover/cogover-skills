---
name: object-history-tracking
description: Cấu hình history tracking của Cogover Object qua Web App API, gồm đọc trạng thái, bật hoặc tắt tracking cấp Object, chọn thêm/bớt/thay thế các field được theo dõi và xác minh cấu hình sau khi ghi. Sử dụng khi cần quản lý lịch sử thay đổi field của một Object, kiểm tra field nào đang được tracking, hoặc xử lý giới hạn field tracking; không dùng để đọc các bản ghi lịch sử đã phát sinh.
metadata:
  author: cogover
  version: "1.0.1"
---

# Object History Tracking

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-11`

Quản lý cấu hình history tracking bằng API, không thao tác UI trình duyệt. Phân biệt hai lớp trạng thái:

- `enabled` quyết định tracking có hoạt động ở cấp Object hay không.
- `fields` là toàn bộ danh sách field slug được chọn; danh sách này vẫn được lưu khi `enabled=false` nhưng chưa có hiệu lực tracking.

**Thời hạn lưu lịch sử mặc định:** Dữ liệu lịch sử thay đổi field quá **18 tháng** sẽ được hệ thống tự động xoá. Khi tư vấn về khả năng truy vết hoặc lưu trữ lịch sử, nêu rõ thời hạn này; không mô tả history tracking là lưu lịch sử vĩnh viễn.

Skill này dành cho người dùng bên ngoài. Chỉ dùng tài liệu đi kèm skill, thông tin người dùng cung cấp, cơ chế credential an toàn có sẵn và response API của workspace. Không tìm hoặc đọc source code, repository, file dự án, test, migration, database, log nội bộ, browser bundle hay source map để suy ra contract. Nếu tài liệu và API không đủ thông tin, dừng và báo rõ phần còn thiếu.

## Chuẩn bị

1. Xác định chính xác `WORKSPACE_DOMAIN`, `API_KEY`, Object đích và ý định: chỉ bật/tắt, thêm/bớt field, hay đặt lại danh sách chính xác. Lấy workspace và credential từ thông tin người dùng cung cấp hoặc cơ chế credential an toàn có sẵn; không đọc file dự án để tìm secret. Không in, log hoặc ghi secret vào file.
2. Bắt buộc dùng `$cogover-api-auth` để đổi API Key thành phiên Web App trước khi gọi bất kỳ endpoint `/api/v{N}/...` nào. API Key Bearer chỉ được dùng cho `POST /bapi/v1/auth-token`; tuyệt đối không gửi Bearer trực tiếp tới `/api/v1/...`.
3. Gửi đủ cookie `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` và hai header `x-csrf-token`, `x-xsrf-token` bằng đúng giá trị cookie `XSRF-TOKEN`, theo `$cogover-api-auth`. Tạo lại phiên khi hết hạn.
4. Đọc đầy đủ [references/api-contract.md](references/api-contract.md) trước khi resolve field, dựng payload hoặc gọi mutation. Không suy đoán endpoint, kiểu field, response hay mã lỗi ngoài contract.

## Quy trình

### 1. Resolve Object và field thật

1. Gọi `POST /api/v1/objects/object/get-by-slug` với Object slug và `withFields: 1` theo contract.
2. Yêu cầu đúng một Object trong `data[]`; xác nhận response slug bằng slug yêu cầu và `category` là `normal`. Dừng nếu không tìm thấy, có sai lệch, hoặc Object không thuộc category này.
3. Chỉ coi field là có thể chọn khi field đó xuất hiện trong response đã lọc hiển thị, có `status: 1`, và `fieldType` không phải `formula`, `auto_number` hoặc `rollup_summary`. Không loại field chỉ vì `manualModifyAllow=false`.
4. Resolve tên người dùng theo thứ tự: slug khớp chính xác, rồi tên gốc `originalName`, rồi tên hiển thị `name`. Chuẩn hóa tên chỉ để tìm kiếm; luôn gửi slug thật từ API. Nếu nhiều field cùng khớp tên, đưa các ứng viên kèm slug và yêu cầu làm rõ.

### 2. Đọc trạng thái hiện tại

Gọi `GET /api/v1/objects/history_tracking/setting/{objectSlug}` ngay trước khi quyết định thay đổi.

- `data: null`: chưa có bản ghi cấu hình; diễn giải trạng thái hiệu dụng là tắt với danh sách rỗng, nhưng vẫn báo rõ đây là trạng thái chưa cấu hình.
- `data.enabled`: trạng thái cấp Object.
- `data.fields`: toàn bộ danh sách field slug đã lưu, kể cả khi Object đang tắt.

Không diễn giải `enabled=false` thành `fields=[]`. Không coi field có mặt trong `fields` là đang phát sinh lịch sử nếu Object đang tắt.

### 3. Tính trạng thái đích

Mutation là full-state upsert. Luôn dựng cả hai key `enabled` và `fields` từ trạng thái mới nhất:

- **Chỉ bật/tắt:** đổi `enabled`, giữ nguyên `fields` từng phần tử và thứ tự.
- **Thêm field:** giữ `enabled`, thêm slug đã resolve nếu chưa có, không làm mất phần tử hiện tại.
- **Bỏ field:** giữ `enabled`, bỏ đúng slug đã resolve, giữ các phần tử khác.
- **Đặt danh sách chính xác:** giữ `enabled` trừ khi người dùng cũng yêu cầu đổi; thay toàn bộ `fields` bằng danh sách đã xác nhận và báo rõ các slug sẽ bị bỏ.

Nếu người dùng nói “bật tracking cho field X”, diễn giải đây là yêu cầu bật cấp Object (`enabled: 1`) đồng thời thêm field đã resolve vào danh sách hiện tại; không yêu cầu xác nhận riêng dù Object đang tắt hoặc chưa có setting. Chỉ dừng để xác nhận trước mutation khi người dùng chủ động yêu cầu xem lại hoặc xác nhận trước khi ghi. Nếu người dùng chỉ yêu cầu chọn/lưu field nhưng nói rõ phải giữ Object tắt, giữ `enabled: 0`.

Giữ nguyên slug cũ không còn resolve được khi thao tác chỉ bật/tắt hoặc thêm/bớt field khác. Không âm thầm “dọn” slug lạ; chỉ loại chúng khi người dùng yêu cầu đặt danh sách chính xác hoặc xác nhận dọn cấu hình.

### 4. Kiểm tra an toàn trước khi ghi

1. Đọc giới hạn hiện hành `limits.historyTrackingFieldsPerObject` qua endpoint subscription trong contract; không hardcode `20`.
2. Đếm toàn bộ phần tử của mảng đích. Loại duplicate do thao tác mới tạo ra, nhưng không thay đổi duplicate có sẵn trong thao tác chỉ bật/tắt nếu chưa được phép.
3. Nếu trạng thái cũ đã vượt giới hạn do thay đổi gói, lưu ý server vẫn kiểm tra giới hạn cả khi tắt. Không tự gửi `fields: []` để lách lỗi vì sẽ xoá lựa chọn đã lưu; yêu cầu người dùng chọn field cần bỏ.
4. Đọc lại cả Object schema và setting ngay trước mutation. Nếu setting `updated`, `enabled` hoặc `fields` đã đổi kể từ lần đọc dùng để tính payload, tính lại thay đổi trên bản mới nhất hoặc dừng vì xung đột. Nếu field đích không còn active/hợp lệ, không ghi.
5. Hiển thị tóm tắt Object slug, trạng thái `enabled` trước/sau, field thêm/bớt và tổng field đích trước khi thực hiện thao tác ghi có phạm vi rộng hoặc thay danh sách chính xác.

### 5. Ghi và xác minh

Gọi `POST /api/v1/objects/history_tracking/setting/{objectSlug}` với:

```json
{
  "enabled": 1,
  "fields": ["status", "owner"]
}
```

Dùng số `1` hoặc `0` cho `enabled` như Web App và luôn gửi `fields` là mảng string đầy đủ. Không gửi field ID, tên hiển thị, `null`, hoặc payload partial.

Chỉ coi response ghi sơ bộ thành công khi HTTP `200`, `r: 0`, và `data` chứa ID cấu hình. Sau đó luôn GET setting lại và đối chiếu:

- `objectSlug` đúng Object đích;
- `enabled` Boolean tương ứng với số đã gửi;
- `fields` khớp mảng đích, không thiếu hoặc thừa;
- `updated` phản ánh bản ghi mới nhất khi response có dữ liệu.

Bật lần đầu có thể tạo Object lịch sử nội bộ và đặt `objectHistorySlug`. Nếu request timeout hoặc kết quả không rõ, GET setting trước khi quyết định retry; không lặp mù quáng mutation có thể đã tạo side effect.

## Lỗi và edge case

- Với `r: 501`, báo Object không tồn tại hoặc không thuộc workspace phiên; resolve lại slug, không thử slug gần giống.
- Với `r: 535`, lấy giới hạn từ `msg` và subscription, giữ nguyên cấu hình cũ, rồi yêu cầu giảm danh sách đích. Không tự cắt mảng theo thứ tự.
- Với `r: 700` hoặc HTTP `5xx`, báo `requestId`, đọc lại setting để xác định mutation có áp dụng hay chưa rồi mới cân nhắc retry.
- Với HTTP `401`/`403` hoặc lỗi CSRF, dùng `$cogover-api-auth` tạo lại phiên và kiểm tra đủ cookie/header; không chuyển sang Bearer cho `/api`.
- Nếu mutation trả `r: 0` nhưng GET không khớp, báo trạng thái quan sát được và coi thao tác chưa hoàn tất.
- Không hứa backfill lịch sử cũ, xoá lịch sử đã có, hay tự xoá Object lịch sử khi tắt; các hành vi đó không thuộc contract cấu hình này.

## Trả kết quả

Báo Object name/slug, trạng thái cấp Object, danh sách field đã resolve theo `name (slug)`, phần thay đổi, giới hạn hiện hành, ID cấu hình và kết quả GET xác minh. Với thao tác chỉ đọc, không gọi mutation.

Sau khi mutation bật tracking (`enabled: 1`) đã được GET xác minh thành công, luôn trả thêm link Markdown bấm được để người dùng mở trang cấu hình field tracking:

```text
https://{WORKSPACE_DOMAIN}/settings/object/{objectSlug}/setting-tracking-field
```

Dùng hostname workspace đã xác minh và Object slug thật đã resolve; URL-encode path segment nếu cần. Không dùng hostname mẫu hoặc hostname của workspace khác. Không trả link này như bằng chứng thành công nếu mutation hoặc GET xác minh chưa hoàn tất.
