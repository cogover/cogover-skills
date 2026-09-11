---
name: user-permission
description: "Quản lý user, Personnel/Department/Position, Role và quyền dữ liệu Cogover Workspace qua `/bapi/v1` (Users, Roles, Personnels, Departments, Positions, Object Security Rules, API Keys): mời/xoá user, gán/gỡ Role, cấp quyền tính năng và quyền record/field, rule giữ chỗ cho Object do backend quản lý, kiểm thử quyền runtime bằng persona test."
metadata:
  author: cogover
  version: "1.1.2"
---

# User Permission

- **Phiên bản:** `1.1.2`
- **Ngày phát hành:** `2026-09-11`

Quản lý người dùng, Role, cơ cấu nhân sự (Personnel, Department, Position, quan hệ phòng ban–vị trí) và quyền dữ liệu trong một Cogover Workspace. Phân loại yêu cầu trước để chọn đúng API cơ cấu hoặc lớp phân quyền. Role ở mức Object chỉ đủ khi Object không có security rule active; có ít nhất một rule active thì mọi quyền record của mọi user, kể cả Super Admin, còn phải được rule phù hợp cấp.

## Chuẩn bị

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Skill này chỉ dùng nhóm `/bapi/v1` (API Key Bearer).
- Object ID, slug, field ID và field type của Object nghiệp vụ: lấy qua `$object-info` trên chính Workspace đích. Không dùng `$object-info`, `$object-record` hay các Object `department`, `personnel`, `department_personnel` để resolve Department, Personnel, Position và quan hệ phòng ban–vị trí; dùng API chuyên biệt trong bảng dưới.
- Tài liệu trong skill, đọc đúng bước cần dùng:

| Khi làm gì | Đọc |
|---|---|
| Xem, mời, xoá user | [references/api-users.md](references/api-users.md) |
| Xem, tạo, sửa, xoá, gán/gỡ Role; cấp quyền qua Role | [references/api-roles.md](references/api-roles.md); mẫu Role Ticket đã ẩn danh [references/sample-customer-service-role.json](references/sample-customer-service-role.json) |
| Phân quyền theo record/field bằng Object Security Rules | [references/api-object-security-rules.md](references/api-object-security-rules.md); mẫu rules thật của `cash_transaction` [references/sample-cash-transaction-security-rules.json](references/sample-cash-transaction-security-rules.json); ví dụ tên, description, payload [references/security-rule-examples.md](references/security-rule-examples.md) |
| Resolve hoặc thiết lập phòng ban, nhân sự, vị trí | [references/api-departments.md](references/api-departments.md), [references/api-personnels.md](references/api-personnels.md), [references/api-positions.md](references/api-positions.md) |
| Tạo API key tạm cho user kiểm thử | [references/api-api-keys.md](references/api-api-keys.md) |
| Kiểm thử quyền runtime: persona, phòng ban/vị trí test, key tạm, ma trận, dọn dẹp, báo cáo | [references/permission-testing.md](references/permission-testing.md) |

## Mô hình đánh giá quyền hiệu lực

Đánh giá theo thứ tự dưới đây. Role và Object Security Rule không phải hai nguồn quyền độc lập ngang hàng: Role mở cổng quyền ở cấp Object trước; security rule quyết định phạm vi record/field khi lớp bảo mật của Object đã bật.

### 1. Kiểm tra Super Admin

- Lấy toàn bộ Role của user và đọc từng Role. Có ít nhất một Role `isSuperAdmin: 1` → user là Super Admin, qua cổng quyền Role ở cấp Object. Super Admin không tự động bypass Object Security Rules.
- Không có Role Super Admin → mặc định user không có quyền tạo, xem, sửa, xoá record của bất kỳ Object nào cho đến khi có Role cấp action tương ứng.
- Object có ít nhất một rule active: đánh giá Super Admin như mọi user ở lớp record/field (rule active, khớp personnel filter, khớp record filter khi có); không có rule active phù hợp cấp scope tương ứng thì Super Admin cũng bị từ chối action đó.

### 2. Hợp nhất quyền từ nhiều Role

Cộng quyền của mọi Role đang gán: Role A cấp `view`, Role B cấp `edit` trên cùng Object → user có cả hai; Role không cấp action không thu hồi action Role khác đã cấp. Tính riêng theo từng `functionCode`, Object và action; không lấy quyền của Object này áp dụng cho Object khác.

`roleActions` = tập action Role đã hợp nhất trên Object. Action không có trong `roleActions` thì từ chối ngay cả khi một security rule có scope tương ứng; rule không mở rộng vượt cổng Role.

| Role action | Security rule cần kiểm tra khi Object có rule |
|---|---|
| `create` | Rule `type: 1`, scope `create` |
| `view` | Rule `type: 2`, scope `read` |
| `edit` | Rule `type: 2`, scope `edit` |
| `delete` | Rule `type: 2`, scope `delete` |

### 3. Xác định chế độ bảo mật của Object

Liệt kê rules của Object không lọc `status`, kiểm tra trạng thái từng rule:

- Không có rule active: lớp bảo mật chi tiết không hạn chế; quyền qua cổng Role áp dụng cho toàn bộ records và fields (Super Admin qua cổng Role, user thường dùng `roleActions`). Rule inactive không kích hoạt mặc định từ chối và không đóng góp quyền.
- Có ít nhất một rule active: mặc định từ chối với mọi user, kể cả Super Admin; quyền cấp Object không tự áp dụng cho record. Không có rule active phù hợp cho tạo → không được tạo record; record hiện có không khớp rule active phù hợp → không được xem, sửa, xoá record đó. Chỉ rule active khớp user và record mới cộng quyền trở lại.
- Rule giữ chỗ active với `personnelFilters: [{"type": 1, "op": "include", "personnelId": null}]` cũng kích hoạt chế độ này dù không khớp nhân sự nào và không cấp quyền cho ai; dùng để giữ slot action chưa cấp và duy trì mặc định từ chối, đặc biệt với Object do backend quản lý (đọc [Object do backend quản lý và rule giữ chỗ](#4-object-do-backend-quản-lý-và-rule-giữ-chỗ) trước khi dùng). Không có rule active nghĩa là lớp chi tiết không hạn chế dữ liệu, vẫn phải qua cổng Role; không phải mọi user mặc nhiên có đủ CRUD.

### 4. Hợp nhất các security rule phù hợp

Chỉ đưa rule vào tập tính quyền khi rule active và khớp đầy đủ: `type: 1` → user khớp `personnelFilters` (không dùng record filter); `type: 2` → user khớp `personnelFilters` và record khớp `filter`.

Nhiều rule đồng thời khớp user + record thì cộng quyền:

- Hợp các field được phép `create`, `read`, `edit`; một rule cấp `all` → scope đó là toàn bộ field; `include`/`exclude` → tính tập field từng rule cho phép rồi lấy hợp.
- Cấp `delete` khi có ít nhất một rule phù hợp `delete: yes` và Role cũng có `delete`.
- `none`/`no` chỉ nghĩa là rule đó không cộng quyền cho scope tương ứng; không dùng để thu hồi quyền mà rule phù hợp khác đã cấp.
- Personnel filter `exclude` không phải "user thuộc đối tượng bị loại trừ thì không khớp rule". Với audience theo Role (`type: 4`, `op: exclude`), runtime duyệt từng Role của user: user vẫn khớp nếu có ít nhất một Role không nằm trong danh sách loại trừ; chỉ khi mọi Role đều bị loại trừ (hoặc user không có Role) thì nhánh này không cấp quyền. Đây là điều kiện chọn audience, không phải lệnh cấm ghi đè rule khác. Đọc [Semantics của Role `exclude` khi user có nhiều Role](references/api-object-security-rules.md#semantics-của-role-exclude-khi-user-có-nhiều-role) trước khi thiết kế hoặc kiểm thử loại rule này.

```text
Không có rule active:  effectiveActions = quyền qua cổng Role trên mọi record
Có rule active:        effectiveActions(record, field) = quyền qua cổng Role
                       ∩ ánh xạ action từ hợp scope của mọi active rule khớp user và record
```

Ví dụ: Role A cấp `view`, Role B cấp `edit` và `delete` trên `object_a`; hai active rule cùng khớp user và record X: rule 1 đọc mọi field, sửa `amount`, `delete: no`; rule 2 sửa `status`, `delete: yes`. Trên X, user xem mọi field, sửa `amount` và `status`, được xoá (`delete: no` của rule 1 không huỷ `delete: yes` của rule 2). Trên record Y không khớp rule nào, user không có quyền dù Role đã có `view`, `edit`, `delete`.

## Phân loại yêu cầu phân quyền

Yêu cầu "phân quyền dữ liệu", "cấp quyền" hoặc "thiết lập quy tắc bảo mật" (kể cả chặn CRUD trực tiếp trên Object do backend quản lý): chọn một trường hợp dưới đây.

### 1. Phân quyền tính năng

Tạo hoặc cập nhật Role với `permissions[]` cấp đúng tính năng và action, rồi gán Role cho user:

1. Xác định user, tính năng và action cần cấp. Tìm Role phù hợp; chỉ tạo Role mới khi chưa có Role đáp ứng đúng phạm vi.
2. Không đoán `functionCode` hoặc action; lấy từ Role hiện có đã xác nhận trên cùng Workspace hoặc từ mã người dùng cung cấp.
3. Tạo/cập nhật Role, đọc lại bằng `roles/view`; gọi `roles/addAccount` nếu user chưa có Role; đọc lại user để xác minh Role đã gán.

### 2. Phân quyền toàn bộ records của một Object

Dùng Role khi user cần tạo, xem, sửa hoặc xoá toàn bộ records của một hay nhiều Object, không giới hạn theo record/field:

1. Tạo hoặc cập nhật Role với permission `functionCode: "record"`, `groupSlug: "object"`, `actions` cần cấp, `valueOption: 1` (chỉ áp dụng cho các Object trong `values`) và `values` gồm `id` + `slug` của Object đã resolve (schema: [Permission schema](references/api-roles.md#permission-schema)). Gán Role cho user.
2. Liệt kê toàn bộ security rules của Object không lọc trạng thái. Không có rule active → dừng ở Role; `roleActions` áp dụng cho mọi record.
3. Có rule active → Role một mình chưa đủ; tạo hoặc cập nhật active rule phạm vi rộng cho user/Role đích: rule `type: 1` scope `create` toàn bộ field khi cần tạo; các rule `type: 2` riêng cho View, Edit, Delete với `filter.conditions: []` khi cần quyền trên mọi record hiện có, scope không phải mục đích của rule đặt `none`/`no`. Chỉ cấp action đã có trong `roleActions`.

Mẫu Role Ticket ([sample-customer-service-role.json](references/sample-customer-service-role.json)) mô tả "Xem/sửa/xoá…" nhưng `permissions[0].actions` chỉ là `["view"]`: `actions` là nguồn sự thật, không suy ra quyền từ tên hoặc mô tả; muốn cấp xem/sửa/xoá phải gửi đủ `["view", "edit", "delete"]`.

### 3. Phân quyền chi tiết theo record hoặc field

Dùng Object Security Rule khi cần giới hạn đến từng record, nhóm record hoặc từng field, hoặc khi Object đã có rule active (mọi quyền record của mọi user, kể cả Super Admin, phải đi qua lớp này).

1. Với action cần cấp, user phải đã có Role cấp quyền records ở mức Object; rule là lớp chi tiết bổ sung, không thay thế Role. Không cấp thêm Role cho action đang muốn chặn hoặc khi chỉ tạo rule giữ chỗ.
2. Mỗi rule một mục đích cấp quyền chính. Yêu cầu đủ create/view/edit/delete → tối thiểu bốn rule độc lập:

   | Rule | `type` | `scopes` | Ghi chú |
   |---|---|---|---|
   | Create | `1` | `create`: fields được nhập | Ai được tạo qua `personnelFilters`; không dùng `filter` |
   | View | `2` | `read`: fields được xem; `edit: none`, `delete: no` | Records được xem qua `filter` |
   | Edit | `2` | `edit`: fields được sửa; `read: none`, `delete: no` | Records được sửa qua `filter` |
   | Delete | `2` | `delete: yes`; `read: none`, `edit: none` | `delete` chỉ nhận `yes`/`no`, không nhận field ID |

3. Cùng action nhưng audience, điều kiện record hoặc tập field khác nhau → tách rule (ví dụ "edit selected fields while Status is Creating/Draft" và "edit Status for all records" là hai Edit rule). Không gộp View/Edit/Delete vào một rule chỉ để giảm số lượng; chỉ giữ rule gộp khi người dùng yêu cầu rõ vì tương thích cấu hình legacy.
4. `personnelFilters`: type `1` chọn user cụ thể, type `4` chọn theo Role; rule giữ chỗ dùng type `1`, `op: "include"`, `personnelId: null` (không resolve hay thay `null` bằng một user). Các type khác chỉ dùng sau khi resolve đúng phòng ban, vị trí hoặc field tra cứu.
5. Record cụ thể: điều kiện trên field định danh ổn định đã được API Object xác nhận; không tự giả định field hoặc toán tử hợp lệ. Field cụ thể: `include`/`exclude` với một phần tử scope cho mỗi `fieldId`.
6. Mỗi Object tối đa 50 rules; kiểm tra tổng số trước khi tạo. Gần giới hạn: hợp nhất rule cùng action và cùng semantics nếu vẫn dễ hiểu; không gộp action khác nhau để lách giới hạn khi người dùng chưa quyết định.
7. Đặt `name`/`description` theo [Đặt tên và mô tả security rule](#đặt-tên-và-mô-tả-security-rule).

### 4. Object do backend quản lý và rule giữ chỗ

Object do backend quản lý là bảng dữ liệu cho logic ứng dụng; người dùng không được thao tác trực tiếp một phần hoặc toàn bộ Create/View/Edit/Delete. Đây là phân loại nghiệp vụ, không phải Object nền tảng có sẵn hay giá trị `isStandard`.

1. Chốt ma trận quyền theo từng action: audience được thao tác trực tiếp, phạm vi record/field, action chỉ backend thực hiện. Khi phối hợp `$cogover-custom-module` tạo Object mới: bộ mặc định bốn rule riêng Create/View/Edit/Delete, action bị chặn vẫn có một rule giữ chỗ; chỉ thêm rule cùng action khi cần audience/filter/field scope khác; không gộp action.
2. Action không cấp cho bất kỳ người dùng nào: rule active (`status: 1`) có audience duy nhất `personnelFilters: [{"type": 1, "op": "include", "personnelId": null}]`. Gửi JSON `null` thật, không phải chuỗi `"null"`, ID giả hay mảng rỗng; `type: 1` của personnel filter độc lập với `type` của rule. `type`, `filter`, `scopes` theo action lấy từ bảng ở [Rule giữ chỗ không chọn nhân sự](references/api-object-security-rules.md#rule-giữ-chỗ-không-chọn-nhân-sự).
3. Rule giữ chỗ giữ slot action để cấu hình sau và kích hoạt/duy trì mặc định từ chối; audience không khớp ai, kể cả Super Admin, nên không cấp quyền cho ai. Rule không phải lệnh cấm có ưu tiên: active rule khác vẫn có thể cộng quyền. Đọc toàn bộ rules để chắc không rule nào khác cấp action đang muốn chặn; không thêm audience khác vào rule giữ chỗ.
4. Ví dụ Object "Lượt khuyến mãi đã sử dụng": View rule cấp đọc theo audience và phạm vi đã chốt; Create/Edit/Delete là ba rule giữ chỗ active. Chỉ backend đọc và ghi → cả bốn rule dùng audience giữ chỗ. Không biểu diễn chặn bằng cách bỏ hết hoặc tắt hết rules: không còn rule active thì quyền qua cổng Role lại áp dụng trên mọi record/field.
5. Không cần thêm Role để rule giữ chỗ hoạt động. Backend dùng quyền caller vẫn chịu quyền của caller; rule giữ chỗ không cấp quyền cho backend. Với Custom Backend Module, phối hợp `$cogover-custom-module` dùng `data.asSystem()` cùng project policy giới hạn đúng Object/action và kiểm tra quyền nghiệp vụ của caller.
6. Sau khi ghi: đọc lại từng rule và danh sách không lọc trạng thái; xác minh `status: 1`, audience chỉ có bộ giá trị trên, scope đúng action và không có grant xung đột ở rule khác. Báo rõ tác động nếu đây là rule active đầu tiên. Không tắt/xoá rule active cuối cùng khi mục tiêu vẫn là mặc định từ chối. Khi mở một slot cho user: cập nhật audience/filter/scopes theo quyền được yêu cầu rồi tính lại quyền cộng dồn.
7. Kiểm thử CRUD trực tiếp bằng danh tính phù hợp theo [Kiểm thử quyền runtime](#kiểm-thử-quyền-runtime), gồm Super Admin khi cần chứng minh không bypass; tách ca backend được phép thực hiện nghiệp vụ khỏi ca người dùng bị chặn. Chưa có backend hoặc thiếu credential/fixture hợp lệ → báo cấu hình đã xác minh và các ca runtime còn chờ; readback không phải PASS end-to-end. Không mở tạm CRUD cho người dùng chỉ để tạo fixture; dùng đường hệ thống đã được phép khi sẵn sàng.

### Đặt tên và mô tả security rule

Viết `name` và `description` gốc bằng tiếng Anh cho mọi rule mới hoặc rule được đổi tên:

- Tên ngắn, nêu action và phạm vi nghiệp vụ, ví dụ `[Finance App] - Delete Draft or Cancelled Cash Transactions`; rule giữ chỗ nêu action và mục đích, ví dụ `[App] - Create Promotion Usage - Placeholder`.
- Description đủ để người không tạo rule vẫn hiểu: audience được áp dụng, action được cấp, filter chọn records, field scope và những quyền cố ý không cấp. Với rule giữ chỗ: nêu không chọn nhân sự, giữ slot, duy trì mặc định từ chối; không tuyên bố rule ghi đè quyền khác.
- `name` không quá 100 ký tự, `description` không quá 500 ký tự. Không để description rỗng, không chỉ lặp lại tên, không dùng mô tả chung như `Allow access`.
- Ví dụ tên/description theo từng action, payload View rule mẫu và ghi chú về mẫu `cash_transaction`: [references/security-rule-examples.md](references/security-rule-examples.md).

Không mặc định workspace user ID và `personnelId` là cùng một ID: kiểm tra chi tiết user để tìm quan hệ Personnel; nếu response không có quan hệ rõ, tra Object Personnel theo email/tài khoản và xác minh khớp chính xác trước khi dùng record ID. Không sao chép `personnelId` top-level từ snapshot Role mẫu vì đó là người gọi request, không phải user đích.

## Quản lý người dùng

Theo [references/api-users.md](references/api-users.md): xem danh sách hoặc chi tiết; mời user bằng email, license và ít nhất một Role; xoá quyền truy cập Workspace với `is_delete_personnel: false` (giữ hồ sơ) hoặc `true` (đánh dấu xoá cả hồ sơ). Resolve user theo email: dùng API tìm kiếm gần đúng rồi ưu tiên khớp chính xác; nhiều kết quả hoặc nhiều trạng thái → trình bày ứng viên để làm rõ trước khi ghi. Sau thao tác, đọc lại danh sách/chi tiết; với xoá kèm hồ sơ, trạng thái có thể là `DELETED` thay vì biến mất ngay.

## Quản lý Role và gán Role

Theo [references/api-roles.md](references/api-roles.md): xem danh sách và chi tiết; tạo, cập nhật, xoá Role; gán bằng `roles/addAccount`, gỡ bằng `roles/removeAccount`. Khi cập nhật Role: đọc chi tiết mới nhất trước, giữ nguyên các permission không được yêu cầu thay đổi, dùng permission `id` cho phần tử hiện có và `status: 0` khi cần xoá một permission; bỏ permission khỏi mảng không phải thao tác xoá.

## An toàn khi ghi và xoá

1. Trước thao tác ghi, báo rõ Workspace, user/Role/Object/rule mục tiêu và phạm vi quyền sẽ thay đổi. Yêu cầu đã chỉ rõ mục tiêu và thay đổi → thực hiện trong phạm vi đó; mục tiêu, hành động hoặc chế độ xoá hồ sơ còn mơ hồ → yêu cầu làm rõ.
2. Xoá user: xác định `is_delete_personnel`; mặc định an toàn là `false` khi người dùng chỉ muốn gỡ khỏi Workspace.
3. Xoá Role: kiểm tra user đang được gán và ảnh hưởng mất quyền; không xoá Role quản trị cao nhất hoặc làm Workspace mất quản trị viên cuối cùng.
4. Xoá Object Security Rule là vĩnh viễn; dùng `status: 0` nếu mục tiêu chỉ là tạm dừng.
5. Tạo hoặc bật rule active đầu tiên của một Object: cảnh báo toàn Object chuyển từ quyền cấp Object áp dụng trên mọi record sang mặc định từ chối; mọi user, kể cả Super Admin, có thể mất quyền nếu chưa được active rules bao phủ.
6. Xoá hoặc tắt rule active cuối cùng: cảnh báo lớp bảo mật chi tiết sẽ tắt dù Object vẫn còn rule inactive; quyền qua cổng Role lại áp dụng cho toàn bộ records và có thể làm tăng quyền ngoài ý muốn.
7. Sửa rule gộp hiện có: đánh giá tách thành các rule theo action; giữ nguyên quyền hiệu lực trong quá trình chuyển đổi và xác minh runtime trước khi xoá rule cũ.
8. Timeout khi tạo/gán: đọc lại trạng thái trước khi thử lại để tránh tạo trùng hoặc kết luận sai.

## Xác minh và báo cáo

Kiểm thử quyền thực tế trên records là bước xác minh quan trọng nhất; đọc lại cấu hình Role/rule chỉ chứng minh cấu hình đã được lưu, không chứng minh user thật sự được phép hoặc bị từ chối đúng yêu cầu.

### Xác minh cấu hình đã lưu

- Sau create/update Role gọi `roles/view` (response update có thể chứa trạng thái cũ). Sau add/remove Role gọi `users/view` và đối chiếu trường `role`. Sau create/update rule gọi endpoint chi tiết và đối chiếu `filter`, `personnelFilters`, `scopes`, `status`, `type`.
- Tính lại trạng thái Super Admin, `roleActions` đã hợp nhất, Object có rule active hay không, các active rule khớp từng user/record và scope hiệu lực cuối cùng. Không loại Super Admin khỏi bước đánh giá security rule.

### Kiểm thử quyền runtime

Quy trình đầy đủ ở [references/permission-testing.md](references/permission-testing.md). Điều kiện bắt buộc:

1. Kiểm thử dưới credential của đúng user đích; không dùng API key của Super Admin hoặc user cấu hình thay cho persona (chỉ kiểm thử được quyền của chủ key). Cần từ hai persona trở lên hoặc rule phụ thuộc Role/phòng ban/vị trí → người dùng xác nhận user test, cách cấp key (người dùng cung cấp hay cho phép AI tạo key tạm), phạm vi Object/action và việc tạo rồi xoá records test. Không có key và không được phép tạo key → dừng ở kiểm tra cấu hình, báo rõ quyền runtime chưa được xác minh end-to-end.
2. Resolve Department, Personnel, Position bằng Departments/Personnels/Positions API; không hoán đổi workspace user ID, `account_id`, Personnel ID, Department ID, Position ID và relation ID. Chỉ thay đổi quan hệ phòng ban/vị trí khi rule phụ thuộc và persona chưa có quan hệ phù hợp: xác nhận với người dùng, snapshot bằng `personnels/view`, ghi bằng `personnels/departmentPosition` với credential quản trị, đọc lại trước khi dùng key của persona, phục hồi sau kiểm thử.
3. API key tạm chỉ khi người dùng cho phép rõ: `accountId` lấy từ `account_id` của active user, tên có tiền tố `codex-permission-test`, `expiresOn` không quá hiện tại + `172800000` ms, secret chỉ giữ trong bộ nhớ, xoá bằng credential quản trị sau test; không sửa/xoá key do người dùng cung cấp.
4. Ma trận một hàng cho mỗi tổ hợp `user × Object × action × record/field` với kỳ vọng và nguồn quyền Role/rule; Object có rule cần record khớp và không khớp cho từng nhánh. Chạy bằng `$object-record` dưới credential persona; đọc lại bằng credential kiểm soát sau mỗi request; lỗi HTTP không phải bằng chứng duy nhất cho deny, `r: 0` không phải bằng chứng duy nhất cho allow. Mọi record test mang marker duy nhất `codex-permission-test-{timestamp}-{random}` trong field tìm kiếm được; không thao tác trên record thật.
5. Object do backend quản lý: credential quản trị/Super Admin cũng có thể bị chặn; phối hợp `$cogover-custom-module` dùng đường hệ thống đã được phép để tạo/đọc/dọn fixture; không dùng `$object-record` dưới key quản trị như cách bypass; đường hệ thống chưa sẵn sàng → ghi ca test còn chờ.
6. Dọn dẹp bắt buộc theo thứ tự records (xác nhận xoá theo quy tắc `$object-record` khi đã biết ID cụ thể) → quan hệ phòng ban/vị trí tạm (`deleted: true` đúng relation ID, khôi phục theo snapshot) → API key tạm; đọc lại để xác minh; không bỏ quên khi test thất bại hoặc bị gián đoạn.
7. Báo cáo tách cấu hình đã lưu và phép tính quyền hiệu lực khỏi kết quả runtime; kèm số records test, quan hệ tổ chức và key tạm đã tạo/thu hồi cùng mọi ID còn tồn đọng; không báo secret. Khi lỗi, giữ HTTP status, `r`, `msg`, `meta` và `requestId`.
