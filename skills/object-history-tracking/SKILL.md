---
name: object-history-tracking
description: "Cấu hình history tracking của Cogover Object qua Web App API `/api/v1/objects/history_tracking/setting`: đọc trạng thái, bật/tắt tracking cấp Object, thêm/bớt/thay thế field được theo dõi, xử lý giới hạn field tracking, xác minh sau khi ghi. Dùng khi cần quản lý lịch sử thay đổi field của Object; không đọc bản ghi lịch sử đã phát sinh."
metadata:
  author: cogover
  version: "1.0.2"
---

# Object History Tracking

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Cấu hình history tracking của Object bằng API, không thao tác UI trình duyệt; không đọc bản ghi lịch sử đã phát sinh. Hai lớp trạng thái: `enabled` quyết định tracking có hoạt động ở cấp Object; `fields` là toàn bộ field slug đã chọn, vẫn được lưu khi `enabled=false` nhưng chưa có hiệu lực tracking. Lịch sử thay đổi field quá **18 tháng** bị hệ thống tự động xoá: khi tư vấn về truy vết hoặc lưu trữ, nêu rõ thời hạn này; không mô tả history tracking là lưu vĩnh viễn.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Skill dùng `/api/v1` (phiên Web App); ngoại lệ riêng ở [Lỗi và edge case](#lỗi-và-edge-case).
- Xác định Object đích và ý định: chỉ bật/tắt, thêm/bớt field, hay đặt lại danh sách chính xác.
- Đọc đầy đủ [references/api-contract.md](references/api-contract.md) trước khi resolve field, dựng payload hoặc gọi mutation. Không suy đoán endpoint, kiểu field, response hay mã lỗi ngoài contract; không đọc source code, repository, bundle hay log nội bộ để suy ra contract; tài liệu và API không đủ thì dừng và báo phần còn thiếu.

## Quy trình

### 1. Resolve Object và field thật

1. `POST /api/v1/objects/object/get-by-slug` với Object slug và `withFields: 1` theo contract. Yêu cầu đúng một Object trong `data[]`, slug trả về bằng slug yêu cầu và `category` là `normal`; không thỏa thì dừng.
2. Field chọn được: có trong response đã lọc hiển thị, `status: 1`, `fieldType` không phải `formula`, `auto_number` hoặc `rollup_summary`. Không loại field chỉ vì `manualModifyAllow=false`.
3. Khớp tên người dùng theo thứ tự: slug chính xác, rồi `originalName`, rồi `name`. Chuẩn hóa tên chỉ để tìm kiếm; luôn gửi slug thật từ API. Nhiều field cùng khớp: đưa các ứng viên kèm slug và yêu cầu làm rõ.

### 2. Đọc trạng thái hiện tại

`GET /api/v1/objects/history_tracking/setting/{objectSlug}` ngay trước khi quyết định thay đổi.

- `data: null`: chưa có bản ghi cấu hình; trạng thái hiệu dụng là tắt với danh sách rỗng, nhưng báo rõ đây là chưa cấu hình.
- `data.enabled`: trạng thái cấp Object. `data.fields`: toàn bộ slug đã lưu, kể cả khi Object đang tắt. Không diễn giải `enabled=false` thành `fields=[]`; không coi field trong `fields` là đang phát sinh lịch sử khi Object tắt.

### 3. Tính trạng thái đích

Mutation là full-state upsert: luôn dựng cả `enabled` và `fields` từ trạng thái mới nhất.

- **Chỉ bật/tắt:** đổi `enabled`; giữ nguyên `fields` từng phần tử và thứ tự.
- **Thêm/bỏ field:** giữ `enabled`; thêm slug đã resolve nếu chưa có, hoặc bỏ đúng slug đó; không làm mất phần tử khác.
- **Đặt danh sách chính xác:** giữ `enabled` trừ khi người dùng cũng yêu cầu đổi; thay toàn bộ `fields` bằng danh sách đã xác nhận và báo rõ các slug sẽ bị bỏ.
- “Bật tracking cho field X” = bật cấp Object (`enabled: 1`) và thêm field đã resolve vào danh sách hiện tại; không hỏi xác nhận riêng dù Object đang tắt hoặc chưa có setting. Chỉ dừng để xác nhận trước mutation khi người dùng chủ động yêu cầu xem lại hoặc xác nhận trước khi ghi. Người dùng chỉ yêu cầu chọn/lưu field nhưng nói rõ giữ Object tắt: giữ `enabled: 0`.
- Slug cũ không còn resolve được: giữ nguyên khi chỉ bật/tắt hoặc thêm/bớt field khác, không âm thầm “dọn”; chỉ loại khi người dùng yêu cầu đặt danh sách chính xác hoặc xác nhận dọn cấu hình.

### 4. Kiểm tra an toàn trước khi ghi

1. Đọc giới hạn hiện hành `limits.historyTrackingFieldsPerObject` qua endpoint subscription trong contract; không hardcode `20`.
2. Đếm toàn bộ phần tử của mảng đích. Loại duplicate do thao tác mới tạo ra; duplicate có sẵn giữ nguyên trong thao tác chỉ bật/tắt nếu chưa được phép dọn.
3. Trạng thái cũ đã vượt giới hạn do thay đổi gói: server vẫn kiểm tra giới hạn cả khi tắt. Không tự gửi `fields: []` để lách lỗi vì sẽ xoá lựa chọn đã lưu; yêu cầu người dùng chọn field cần bỏ.
4. Đọc lại cả Object schema và setting ngay trước mutation. Nếu `updated`, `enabled` hoặc `fields` đã đổi so với lần đọc dùng để tính payload: tính lại trên bản mới nhất hoặc dừng vì xung đột. Field đích không còn active/hợp lệ: không ghi.
5. Trước thao tác ghi phạm vi rộng hoặc thay danh sách chính xác, hiển thị tóm tắt: Object slug, `enabled` trước/sau, field thêm/bớt, tổng field đích.

### 5. Ghi và xác minh

`POST /api/v1/objects/history_tracking/setting/{objectSlug}` với body `{"enabled": 1, "fields": ["status", "owner"]}`: `enabled` là số `1`/`0` như Web App, `fields` là mảng string đầy đủ. Không gửi field ID, tên hiển thị, `null` hoặc payload partial.

Ghi sơ bộ thành công khi HTTP `200`, `r: 0` và `data` chứa ID cấu hình. Sau đó luôn GET setting lại và đối chiếu: `objectSlug` đúng Object đích; `enabled` Boolean tương ứng số đã gửi; `fields` khớp mảng đích, không thiếu hoặc thừa; `updated` phản ánh bản ghi mới nhất. Bật lần đầu có thể tạo Object lịch sử nội bộ và đặt `objectHistorySlug`. Không khớp: báo trạng thái quan sát được và coi thao tác chưa hoàn tất.

## Lỗi và edge case

- `r: 501`: Object không tồn tại hoặc không thuộc workspace phiên; resolve lại slug, không thử slug gần giống.
- `r: 535`: lấy giới hạn từ `msg` và subscription, giữ nguyên cấu hình cũ rồi yêu cầu giảm danh sách đích; không tự cắt mảng theo thứ tự.
- `r: 700`, HTTP `5xx`, timeout hoặc kết quả không rõ sau mutation: báo `requestId`, GET setting để xác định mutation đã áp dụng hay chưa rồi mới cân nhắc retry; không lặp mù mutation có thể đã tạo side effect.
- Không hứa backfill lịch sử cũ, xoá lịch sử đã có hay tự xoá Object lịch sử khi tắt; các hành vi đó không thuộc contract cấu hình này.

## Trả kết quả

Báo Object name/slug, trạng thái cấp Object, danh sách field đã resolve theo `name (slug)`, phần thay đổi, giới hạn hiện hành, ID cấu hình và kết quả GET xác minh.

Sau khi mutation bật tracking (`enabled: 1`) được GET xác minh, luôn trả thêm link Markdown bấm được `https://{WORKSPACE_DOMAIN}/settings/object/{objectSlug}/setting-tracking-field` với hostname workspace đã xác minh và Object slug thật (URL-encode path segment nếu cần). Không dùng hostname mẫu hoặc của workspace khác; không trả link này như bằng chứng thành công khi mutation hoặc GET xác minh chưa hoàn tất.
