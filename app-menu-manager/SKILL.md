---
name: app-menu-manager
description: "Quản lý Cogover App và Menu Item qua Web App API `/api/v{N}/apps`: tạo, đọc, cập nhật, đổi trạng thái, xoá; cây menu, thứ tự, menu mặc định, ACL, thiết lập hiển thị và icon cấp 1. Dùng khi cấu hình App/Menu bằng API hoặc chẩn đoán App/Menu không hiển thị; bắt buộc phối hợp $cogover-api-auth, dùng $cogover-icon cho icon menu cấp 1."
metadata:
  author: cogover
  version: "1.0.1"
---

# App & Menu Manager

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-11`

Quản lý App và Menu Item qua API `/api/v1/apps` (phiên Web App đổi từ API Key; không gửi API Key trực tiếp), không thao tác UI. Luôn đọc state hiện tại, mutation có chủ đích với đúng encoding, rồi đọc lại để xác minh.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Ngoại lệ riêng: sau khi tạo phiên và đối chiếu Workspace, probe `GET /api/v1/apps?limit=1&page=1`; dừng khi sai Workspace, `401/403` hoặc `r != 0`.
- Contract: đọc [references/api-contract.md](references/api-contract.md) trước khi gọi API. Chỉ dùng contract này, tài liệu API chính thức do người dùng cung cấp và response thực tế; không đọc hoặc tìm source code, repository, bundle JavaScript, source map để khám phá contract; không dùng browser/UI để suy ra request. URL `/settings/apps` chỉ dùng làm deep-link trả người dùng.
- Đọc [references/app-menu-model.md](references/app-menu-model.md) trước khi cấu hình ACL, action, platform, cây menu, default item hoặc display setting. Menu có item cấp 1: làm theo [Icon cấp 1](#icon-cấp-1).
- Xác định trước khi ghi: App đích hoặc App mới (name, slug, description, logo, platform, ACL); Menu Item (parent, action và action content/filter, platform, icon, ACL, status, thứ tự); item cấp 1 nào cần icon và với mỗi icon: người dùng đã cung cấp asset hay cần `$cogover-icon` thiết kế, tên file/library item, ngữ nghĩa cần thể hiện; report slug của menu trỏ saved report; có đổi default item hoặc display setting không; phạm vi delete. Hỏi lại trước mutation nếu App đích, parent, action target, ACL hoặc resource cần xoá còn mơ hồ.
- Helper script (mặc định dry-run; POST/PUT/DELETE cần thêm `--apply`; base URL và API Key qua biến môi trường hoặc secret manager): `python3 scripts/app_menu_api.py --method GET --path /api/v1/apps --query limit=20 --query page=1 --execute`.

## Quy tắc chung

- Encoding: App create/update dùng `multipart/form-data` (`accessControls` serialize thành JSON string); Menu Item create/update dùng JSON. Không đổi encoding giữa hai nhóm.
- Kiểm tra trùng slug/name trước create; trùng thì đọc resource hiện có, không tự thêm suffix khi người dùng chưa chấp thuận. Resolve App bằng ID/slug, Menu Item bằng App ID + item ID/slug; không thao tác trên kết quả mơ hồ.
- ACL có semantics thay thế: đọc detail mới nhất, chuyển read shape sang [write shape](references/app-menu-model.md#acl-write-shape) tối thiểu, giữ nhóm ACL chưa định sửa, không gửi field server-managed.
- Update dựa trên detail mới nhất; không dựng lại App/Menu từ partial response hay dữ liệu không phải response API mới nhất.
- Sau mỗi mutation đọc lại App detail, item detail/list và tree để xác minh postcondition; không dựa vào toast/UI.
- Delete là destructive: chỉ xoá custom App (`type = 2`) sau khi đọc detail và menu tree để trình bày ảnh hưởng; không tự xoá standard App (`type = 1`) hay item `isDefault = true`; không cascade hoặc rollback bằng delete khi người dùng chưa yêu cầu rõ.
- Saved report: menu điều hướng tới saved report dùng route runtime `actionType: 34`, `actionUrlType: 3`, `actionUrlOption: 2`, `actionContent: /reports/{reportSlug}` (resolve report slug, không sao chép URL từ trang Settings). Tuyệt đối không dùng route quản trị `/settings/reports/{reportSlug}`. Trước create/update, canonicalize và kiểm tra mọi report menu trong batch; dừng nếu còn tiền tố `/settings/reports/` (helper script cũng từ chối); sau mutation đọc lại exact `actionContent`. Chi tiết: [Route saved report](references/app-menu-model.md#route-saved-report-trong-app).

## Icon cấp 1

Mặc định mỗi Menu Item cấp 1 cần một icon phù hợp ngữ nghĩa. Trong skill này, yêu cầu tạo Menu Item cấp 1 đồng thời cho phép thiết kế icon khi cần, upload vào thư viện Workspace và cài icon; không hỏi xác nhận upload riêng. Không thay bằng icon built-in tuỳ ý hoặc bỏ trống icon, trừ khi người dùng yêu cầu rõ không dùng icon. Item con chỉ gắn icon khi người dùng yêu cầu hoặc thiết kế menu đòi hỏi rõ.

Đọc đầy đủ hai hướng dẫn được link dưới đây trước khi tạo, upload hoặc cài icon. Hoàn tất các bước sau trước khi tạo/cập nhật Menu Item cấp 1; với batch menu mới, chuẩn bị và upload xong toàn bộ icon cấp 1 rồi mới bắt đầu tạo cây menu:

1. Xác định ngữ nghĩa từng nhóm/menu cấp 1 từ tên và các menu con.
2. Người dùng chưa cung cấp icon: dùng `$cogover-icon` profile **App Menu** thiết kế và sinh SVG riêng theo [hướng dẫn icon App Menu](../cogover-icon/references/app-menu-icons.md); đối chiếu asset mẫu, chạy đầy đủ kiểm tra XML, canvas, stroke và kích thước render của skill đó.
3. Người dùng đã cung cấp icon: giữ nguyên thiết kế, không vector hoá hay thay đổi hình học, không tự chỉnh sửa asset để "chuẩn hoá" khi chưa được yêu cầu; chỉ kiểm tra kỹ thuật file có thể upload và dùng được cho App Menu.
4. Upload theo [hướng dẫn upload icon/ảnh](../cogover-icon/references/upload-icon-image-to-workspace-library.md): upload file lên file-server, giữ nguyên metadata response, rồi thêm vào thư viện Workspace. Chỉ tiếp tục khi cả hai bước trả `r == 0`, bước upload có `data.file_id` và bước thêm thư viện có mảng `data` không rỗng; lưu `data[].id` theo đúng Menu Item đích.
5. Cài `icon` bằng đúng `data[].id` do bước thêm thư viện trả về. Không tự dựng URL từ `file_id`, không dùng URL upload tạm, không tạo Menu Item cấp 1 trước khi icon đã vào thư viện thành công.

## App

- Tạo: list theo slug/name để kiểm tra trùng; lập multipart theo contract, ACL theo [ACL write shape](references/app-menu-model.md#acl-write-shape) (có `EDIT` thì thêm `DELETE`); `POST /api/v1/apps`; resolve ID từ response rồi `GET /api/v1/apps/{appId}` để xác minh.
- Sửa: đọc detail mới nhất; giữ đầy đủ name/slug/description/platform/ACL chưa đổi, chỉ thay logo khi người dùng yêu cầu; `POST /api/v1/apps/{appId}` (multipart); đọc lại detail và đối chiếu.
- Đổi trạng thái: `PUT /api/v1/apps/changeStatus` với `ids` và `status`. Xoá: `DELETE /api/v1/apps/delete` với query array `ids[]`.

## Menu Item

Base: `/api/v1/apps/{appId}/menuItems`.

- Tạo: đọc App detail và cây (`GET .../treeMode`); xác minh parent thuộc cùng App, không vượt level 10, slug chưa trùng; lập action theo [Menu action](references/app-menu-model.md#menu-action), icon cấp 1 theo mục trên; `POST .../menuItems` (JSON); đọc lại detail/list item và tree để xác minh parent/level/index/action, đối chiếu `icon` với ID/URL thư viện đã nhận.
- Sửa: đọc item detail mới nhất; giữ full mutable state và ACL, không gửi `workspaceId`, timestamps, creator/updater hoặc object `app`; không đặt parent là chính item hay descendant của nó; thêm/thay icon thì hoàn tất quy trình icon trước rồi merge duy nhất field `icon`; sửa report target thì canonicalize `/settings/reports/{slug}` thành `/reports/{slug}` trong delta đã duyệt, giữ nguyên mutable field/ACL khác; `PUT .../menuItems/{id}` rồi đọc lại detail/list/tree, xác minh icon/action mới.
- Đổi trạng thái: `POST .../updateStatus` với `{ "data": [ids], "status": 0|1 }`. Xoá: `DELETE .../deleteAll` với query array `data[]`; người dùng muốn xoá item `isDefault = true` thì đổi default sang item hợp lệ khác trước.

## Cây, default item và hiển thị

- Sắp thứ tự: đánh lại `index` liên tục trong từng nhóm sibling, flatten toàn cây thành `{id,index}` rồi `POST .../sort`.
- Default item: chỉ chọn item hợp lệ theo [Default item](references/app-menu-model.md#default-item), rồi `POST .../{id}/default`.
- Display setting: `PUT /api/v1/apps/{appId}/menuSetting` với full setting hiện tại đã merge.

## Trả kết quả

Ngắn gọn nhưng đủ audit: Workspace domain; App ID/name/slug/type/status/platform; Menu Item ID/name/slug, parent, level, index, action, status; icon từng menu cấp 1 (nguồn do skill tạo hay người dùng cung cấp, tên library item, ID/URL đã cài); ACL ở mức mô tả, default item, display settings; postcondition và warning. Deep-links: App detail `https://{WORKSPACE_DOMAIN}/settings/apps/{APP_ID}`, menu list `https://{WORKSPACE_DOMAIN}/settings/apps/{APP_ID}/menu-item`, display menu `https://{WORKSPACE_DOMAIN}/settings/apps/{APP_ID}/configure-display-left-menu`.

## Xử lý lỗi

- `r != 0`: sửa đúng field gây lỗi theo `msg`/`meta` rồi mới tiếp tục.
- `default_child_menu_item` hoặc lỗi default: đọc lại tree/default item trước khi đề xuất thay đổi.
- Parent invalid, là chính item hoặc descendant: dừng update và báo quan hệ gây cycle.
- Timeout ở mutation: đọc lại bằng ID/slug trước mọi retry. Response shape lạ: lưu output redacted, dừng mutation, không đoán ID.
- Upload file thành công nhưng thêm thư viện thất bại: báo `file_id`, không upload lại mù quáng, không tạo/cập nhật menu với URL tự dựng.
- Thêm thư viện thành công nhưng cập nhật menu thất bại: giữ ID/URL thư viện, đọc lại menu trước khi retry, không upload bản sao icon.
