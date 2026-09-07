---
name: app-menu-manager
description: Tạo, đọc, cập nhật, kích hoạt/vô hiệu hoá và xoá Cogover App cùng Menu Item qua Web App API `/api/v{N}/apps`, đồng thời quản lý cây menu, icon cấp 1, thứ tự, menu mặc định, ACL và thiết lập hiển thị menu. Sử dụng khi người dùng yêu cầu cấu hình App/Menu Cogover bằng API hoặc chẩn đoán App/Menu không hiển thị đúng; bắt buộc phối hợp với `$cogover-api-auth`, và dùng `$cogover-icon` để thiết kế hoặc tiếp nhận, upload rồi cài icon cho menu cấp 1 khi tạo menu.
metadata:
  author: cogover
  version: "1.0.0"
---

# App & Menu Manager

- **Phiên bản:** `1.0.0`
- **Ngày phát hành:** `2026-08-23`

Quản lý App và Menu bằng API, không thao tác UI. Luôn đọc state hiện tại, tạo write payload đúng encoding, mutation có chủ đích, rồi đọc lại để xác minh.

## Đọc tài liệu theo tác vụ

- Luôn đọc [references/api-contract.md](references/api-contract.md) trước khi gọi API.
- Đọc [references/app-menu-model.md](references/app-menu-model.md) trước khi cấu hình ACL, action, platform, cây menu, menu mặc định hoặc display setting.
- Khi tạo menu có item cấp 1, gọi và tuân thủ `$cogover-icon`; đọc đầy đủ [hướng dẫn icon App Menu](../cogover-icon/references/app-menu-icons.md) và [hướng dẫn upload icon/ảnh](../cogover-icon/references/upload-icon-image-to-workspace-library.md) trước khi tạo, upload hoặc cài icon.

## Quy tắc bắt buộc

1. Gọi và tuân thủ `$cogover-api-auth` trước mọi request. Mọi endpoint trong skill này là `/api/v1/...`; không gửi API Key trực tiếp.
2. Dùng API Key chỉ cho `POST /bapi/v1/auth-token`, sau đó gửi đủ ba cookie phiên và hai header CSRF/XSRF cho App/Menu API.
3. Chỉ dùng contract đóng gói trong skill, tài liệu API chính thức do người dùng cung cấp và response API thực tế. Không đọc hoặc tìm kiếm source code, repository, bundle JavaScript, source map hay mã ứng dụng để khám phá contract.
4. Không dùng browser hoặc UI để suy ra request. URL `/settings/apps` chỉ dùng làm deep-link trả cho người dùng.
5. Không ghi, echo hoặc commit API key, cookie hay token. Nhận bí mật qua biến môi trường hoặc secret manager.
6. App create/update dùng `multipart/form-data`; Menu Item create/update dùng JSON. Không đổi encoding giữa hai nhóm.
7. Kiểm tra trùng slug/name trước create. Resolve App bằng ID/slug và Menu Item bằng App ID + item ID/slug; không thao tác trên kết quả mơ hồ.
8. ACL có semantics thay thế. Luôn đọc detail, chuyển read shape sang write shape tối thiểu, giữ nhóm ACL chưa định sửa và không gửi field server-managed.
9. Update dựa trên detail mới nhất. Không dựng lại App/Menu từ một partial response hay dữ liệu không phải response API mới nhất.
10. Không coi HTTP status là đủ. Kiểm tra `r == 0`, `msg`, response data và postcondition bằng API đọc.
11. Delete là destructive: không xoá App hệ thống/standard hoặc default menu item; không cascade hay rollback bằng delete nếu người dùng chưa yêu cầu rõ.
12. Khi tạo cây menu, mặc định mỗi Menu Item cấp 1 cần một icon phù hợp ngữ nghĩa. Trong ngữ cảnh skill này, yêu cầu tạo Menu Item cấp 1 đồng thời cho phép thiết kế icon khi cần, upload vào thư viện Workspace và cài icon; không hỏi xác nhận upload riêng. Không thay bằng icon built-in tùy ý hoặc bỏ trống icon, trừ khi người dùng yêu cầu rõ không dùng icon.
13. Nếu người dùng chưa cung cấp icon, dùng profile **App Menu** của `$cogover-icon` để thiết kế, sinh và kiểm tra SVG production; sau đó upload file vào thư viện Workspace trước khi tạo/cập nhật Menu Item.
14. Nếu người dùng cung cấp icon sẵn, không thiết kế lại, không vector hoá và không thay đổi hình học nếu chưa được yêu cầu. Kiểm tra kỹ thuật cần thiết, upload asset được cung cấp vào thư viện Workspace rồi cài URL/ID trả về cho Menu Item.
15. Chỉ dùng giá trị `data[].id` do API thêm vào thư viện trả về làm `icon`. Không tự dựng URL từ `file_id`, không dùng URL upload tạm và không tạo Menu Item cấp 1 trước khi icon tương ứng đã được thêm vào thư viện thành công.
16. Phân biệt route quản trị và route runtime. Menu điều hướng tới một saved report trong Workspace phải dùng `actionType: 34`, `actionUrlType: 3` và `actionContent: /reports/{reportSlug}`. Tuyệt đối không dùng `/settings/reports/{reportSlug}` vì đó là route quản trị cấu hình report, không phải trang report dành cho App. Trước create/update, canonicalize và kiểm tra tất cả report menu trong batch; helper script phải từ chối payload còn tiền tố `/settings`.

## Quy trình

### 1. Chuẩn hoá yêu cầu

Xác định:

- Workspace base URL/domain.
- App đích hoặc App mới: name, slug, description, logo, platform, ACL.
- Menu Item: parent, action, action content/filter, platform, icon, ACL, status và thứ tự; xác định rõ item cấp 1 nào cần icon.
- Với Menu Item trỏ tới saved report, resolve report slug và dùng runtime route `/reports/{reportSlug}`; không sao chép URL từ trang Settings.
- Với mỗi icon cấp 1: người dùng đã cung cấp asset hay cần `$cogover-icon` thiết kế; tên file/library item và ngữ nghĩa hình ảnh cần thể hiện.
- Có cần đổi default item hoặc display setting không.
- Tiêu chí nghiệm thu và phạm vi delete.

Hỏi lại trước mutation nếu App đích, parent, action target, ACL hoặc resource cần xoá còn mơ hồ.

### 2. Tạo và kiểm tra phiên

1. Dùng `$cogover-api-auth` để đổi API Key thành phiên Web App.
2. Đối chiếu workspace trong auth response.
3. Probe bằng `GET /api/v1/apps?limit=1&page=1`; dừng khi sai workspace, `401/403` hoặc `r != 0`.

Ví dụ helper script:

```bash
python3 scripts/app_menu_api.py \
  --method GET --path /api/v1/apps \
  --query limit=20 --query page=1 --execute
```

Thiết lập base URL và API Key bằng biến môi trường hoặc secret manager. Script mặc định dry-run; request POST/PUT/DELETE còn yêu cầu `--apply`.

### 3. Quản lý App

#### Tạo

1. List theo slug/name để kiểm tra trùng.
2. Lập `multipart/form-data` theo contract; serialize `accessControls` thành JSON string.
3. Nếu ACL chứa `EDIT`, thêm `DELETE` theo contract quyền của App.
4. Gọi `POST /api/v1/apps`.
5. Resolve ID từ response rồi đọc `GET /api/v1/apps/{appId}` để xác minh.

#### Sửa

1. Đọc detail mới nhất.
2. Giữ đầy đủ name/slug/description/platform/ACL chưa đổi; chỉ thay logo khi người dùng yêu cầu.
3. Gọi `POST /api/v1/apps/{appId}` bằng multipart.
4. Đọc lại detail và đối chiếu.

#### Đổi trạng thái hoặc xoá

- Đổi trạng thái: `PUT /api/v1/apps/changeStatus` với `ids` và `status`.
- Xoá: `DELETE /api/v1/apps/delete` với query array `ids[]`.

Chỉ xoá custom App (`type = 2`) sau khi đọc detail và menu tree để trình bày ảnh hưởng. Không tự xoá standard App (`type = 1`).

### 4. Quản lý Menu Item

#### Chuẩn bị icon cấp 1

Thực hiện trước khi tạo Menu Item cấp 1:

1. Xác định ngữ nghĩa của từng nhóm/menu cấp 1 từ tên và các menu con.
2. Nếu chưa có icon do người dùng cung cấp, dùng `$cogover-icon` với profile **App Menu** để tạo SVG riêng, đọc [hướng dẫn icon App Menu](../cogover-icon/references/app-menu-icons.md), đối chiếu asset mẫu và chạy đầy đủ kiểm tra XML, canvas, stroke cùng kích thước render theo skill đó.
3. Nếu người dùng đã cung cấp icon, giữ nguyên thiết kế; chỉ kiểm tra file có thể upload và dùng được cho App Menu. Không tự chỉnh sửa asset để “chuẩn hoá” nếu người dùng chưa yêu cầu.
4. Đọc và làm theo `upload-icon-image-to-workspace-library.md` trong `$cogover-icon`: upload file lên file-server, giữ nguyên metadata response, rồi thêm file vào thư viện Workspace.
5. Chỉ tiếp tục khi cả hai bước upload đều thành công, `r == 0`, có `data.file_id` ở bước upload và mảng `data` không rỗng ở bước thêm thư viện. Lưu `data[].id` theo đúng Menu Item đích.
6. Với một batch menu mới, chuẩn bị và upload xong toàn bộ icon cấp 1 trước khi bắt đầu tạo cây menu để tránh trạng thái dở dang. Không upload lại mù quáng nếu file-server đã nhận file nhưng bước thêm thư viện thất bại.

#### Tạo

1. Đọc App detail và tree mode.
2. Xác minh parent thuộc cùng App, không vượt quá level 10 và slug chưa trùng.
3. Với item cấp 1, resolve đúng icon đã upload; với item con, chỉ gắn icon nếu người dùng yêu cầu hoặc thiết kế menu đòi hỏi rõ.
4. Lập action theo [references/app-menu-model.md](references/app-menu-model.md), đặt `icon` bằng đúng `data[].id` trả về từ thư viện cho item cấp 1.
   - Saved report: `actionType=34`, `actionUrlType=3`, `actionUrlOption=2`, `actionContent=/reports/{reportSlug}`.
   - Dừng nếu actionContent bắt đầu bằng `/settings/reports/`.
5. Gọi `POST /api/v1/apps/{appId}/menuItems` bằng JSON.
6. Đọc detail/list item và tree để xác minh parent/level/index/action, đồng thời đối chiếu `icon` với ID/URL thư viện đã nhận.

#### Sửa

1. Đọc item detail mới nhất.
2. Giữ full mutable state và ACL; không gửi `workspaceId`, timestamps, creator/updater hoặc object `app`.
3. Không đặt parent là chính item hay một descendant của nó.
4. Khi thêm hoặc thay icon, hoàn tất quy trình `$cogover-icon` và upload thư viện trước; merge duy nhất field `icon` vào full mutable state mới nhất.
5. Nếu sửa report target, canonicalize `/settings/reports/{slug}` thành `/reports/{slug}` trong delta đã duyệt; giữ nguyên mọi mutable field/ACL khác.
6. Gọi `PUT /api/v1/apps/{appId}/menuItems/{id}` rồi đọc lại detail/list/tree và xác minh icon/action mới.

#### Đổi trạng thái hoặc xoá

- Đổi trạng thái: `POST .../updateStatus` với `{ "data": [ids], "status": 0|1 }`.
- Xoá: `DELETE .../deleteAll` với query array `data[]`.

Không xoá item có `isDefault = true`. Đổi default sang item hợp lệ khác trước nếu người dùng yêu cầu xoá item hiện tại.

### 5. Cấu hình cây và hiển thị menu

- Đọc cây: `GET .../treeMode`.
- Sắp thứ tự: cập nhật `index` liên tục trong từng nhóm sibling, flatten thành `{id,index}` rồi `POST .../sort`.
- Đặt default: chỉ chọn item hợp lệ theo model, rồi `POST .../{id}/default`.
- Display setting: `PUT /api/v1/apps/{appId}/menuSetting` với full setting hiện tại đã merge.

Sau mỗi thao tác, đọc lại App detail và tree; không dựa vào toast/UI.

### 6. Trả kết quả

Trả ngắn gọn nhưng đủ audit:

- Workspace domain, không kèm token.
- App ID/name/slug/type/status/platform.
- Menu Item ID/name/slug, parent, level, index, action và status.
- Icon của từng menu cấp 1: nguồn do skill tạo hay người dùng cung cấp, tên library item và ID/URL đã được cài.
- ACL ở mức mô tả, default item và display settings.
- Postcondition và warning.
- Deep-links:
  - App detail: `https://{WORKSPACE_DOMAIN}/settings/apps/{APP_ID}`.
  - Menu list: `https://{WORKSPACE_DOMAIN}/settings/apps/{APP_ID}/menu-item`.
  - Display menu: `https://{WORKSPACE_DOMAIN}/settings/apps/{APP_ID}/configure-display-left-menu`.

## Xử lý lỗi

- `401/403`: tạo lại phiên hoặc kiểm tra quyền; không retry mutation.
- `r != 0`: đọc `msg`/`meta`, sửa đúng field gây lỗi rồi mới tiếp tục.
- Trùng name/slug: đọc resource hiện có; không tự thêm suffix nếu người dùng chưa chấp thuận.
- `default_child_menu_item` hoặc lỗi default: đọc lại tree/default item trước khi đề xuất thay đổi.
- Parent invalid/current item/descendant: dừng update và báo quan hệ gây cycle.
- Report route bắt đầu `/settings/reports/`: từ chối payload; dùng runtime route `/reports/{reportSlug}` và đọc lại exact `actionContent` sau mutation.
- Timeout ở mutation: đọc lại bằng ID/slug trước mọi retry.
- Response shape lạ: lưu output redacted, dừng mutation và không đoán ID.
- Upload file thành công nhưng thêm thư viện thất bại: báo `file_id`, không upload lại mù quáng và không tạo/cập nhật menu với URL tự dựng.
- Thêm thư viện thành công nhưng cập nhật menu thất bại: giữ lại ID/URL thư viện, đọc lại menu trước khi retry và không upload bản sao icon.
