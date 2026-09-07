---
name: user-permission
description: >-
  Quản lý quyền truy cập Cogover Workspace qua public API: xem, mời hoặc xoá
  người dùng; resolve, xem hoặc thiết lập Personnel, Department, Position và
  quan hệ phòng ban-vị trí của nhân sự; xem, tạo, sửa hoặc xoá Role; gán hoặc
  gỡ Role khỏi người dùng; cấp quyền tính năng và quyền tạo, xem, sửa, xoá bản
  ghi ở mức Object, từng record hoặc từng field bằng Object Security Rules.
  Sử dụng khi cần quản lý thành viên hoặc cơ cấu nhân sự Workspace, phòng ban,
  vị trí công việc, nhân sự test, vai trò, phân quyền dữ liệu, giới hạn bản
  ghi/trường hoặc thiết lập quy tắc bảo mật.
metadata:
  author: cogover
  version: "1.1.1"
---

# User Permission

- **Phiên bản:** `1.1.1`
- **Ngày phát hành:** `2026-09-07`

Quản lý người dùng, Role, cơ cấu nhân sự gồm Personnel, Department, Position và quan hệ phòng ban–vị trí, cùng quyền dữ liệu trong một Cogover Workspace. Luôn phân loại yêu cầu trước để chọn đúng API quản lý cơ cấu hoặc lớp phân quyền. Chỉ coi Role ở mức Object là đủ khi Object không có security rule active; nếu Object có ít nhất một rule active, mọi quyền record của mọi user, kể cả Super Admin, còn phải được rule phù hợp cấp.

## Chuẩn bị

1. Resolve `WORKSPACE_DOMAIN` và API Key theo mục quản lý credential của `$cogover-api-auth`: ưu tiên credential đã được cấp cho đúng Workspace, scoped environment hoặc secret store; không dò file dự án để tìm secret. Chỉ hỏi qua kênh an toàn khi chưa có hoặc không truy cập được.
2. Chuẩn hoá domain bằng cách bỏ protocol và dấu `/` cuối, rồi gọi `https://{WORKSPACE_DOMAIN}`.
3. Không in, ghi log hoặc đưa `API_KEY` vào câu trả lời. Gửi hai header:

   ```http
   Authorization: Bearer {API_KEY}
   Content-Type: application/json
   ```

4. Phân biệt thao tác đọc và ghi. Nếu người dùng chỉ yêu cầu xem, phân tích hoặc dựng payload, không gọi endpoint tạo, cập nhật, gán, gỡ hoặc xoá.
5. Resolve ID thật trước khi ghi. Không suy đoán user ID, role ID, Object ID, Object slug, field ID, department ID hoặc position ID từ tên hiển thị.
6. Đọc tài liệu phù hợp trước khi dựng request:
   - Quản lý người dùng: [references/api-users.md](references/api-users.md).
   - Quản lý Role, gán/gỡ Role hoặc cấp quyền qua Role: [references/api-roles.md](references/api-roles.md).
   - Phân quyền chi tiết theo record hoặc field: đọc thêm [references/api-object-security-rules.md](references/api-object-security-rules.md).
   - Tham khảo cấu trúc rules thật của `cash_transaction`: [references/sample-cash-transaction-security-rules.json](references/sample-cash-transaction-security-rules.json).
   - Tạo API key tạm cho user kiểm thử: đọc [references/api-api-keys.md](references/api-api-keys.md).
   - Resolve hoặc thiết lập phòng ban, nhân sự và vị trí: đọc [references/api-departments.md](references/api-departments.md), [references/api-personnels.md](references/api-personnels.md) và [references/api-positions.md](references/api-positions.md).
   - Khi cần Object ID, slug, field ID hoặc field type của Object nghiệp vụ sẽ kiểm thử, dùng `$object-info` và kiểm tra trên chính Workspace đích. Không dùng `$object-info` hoặc `$object-record` để resolve Department, Personnel, Position hay quan hệ phòng ban–vị trí; dùng các API chuyên biệt ở dòng trên.

## Mô hình đánh giá quyền hiệu lực

Đánh giá quyền theo thứ tự dưới đây. Không xem Role và Object Security Rule là hai nguồn quyền độc lập ngang hàng: Role mở quyền ở cấp Object trước, còn security rule quyết định phạm vi record/field khi lớp bảo mật của Object đã được kích hoạt.

### 1. Kiểm tra Super Admin

1. Lấy toàn bộ Role của user và đọc thông tin từng Role.
2. Nếu có ít nhất một Role với `isSuperAdmin: 1`, coi user là Super Admin và cho qua cổng quyền Role ở cấp Object. Super Admin không tự động bypass Object Security Rules.
3. Nếu không có Role Super Admin, coi user là non-Super Admin. Mặc định user không có quyền tạo, xem, sửa hoặc xoá record của bất kỳ Object nào cho đến khi có Role cấp action tương ứng.

Khi Object có ít nhất một security rule active, đánh giá Super Admin giống mọi user khác ở lớp record/field: rule phải active, personnel filter phải khớp và record filter phải khớp khi có. Nếu không có rule active phù hợp cấp scope tương ứng, Super Admin cũng bị từ chối action đó.

### 2. Hợp nhất quyền từ nhiều Role

Hợp nhất permission của tất cả Role đang gán cho user theo phép cộng quyền:

- Role A cấp `view` và Role B cấp `edit` trên cùng Object thì user có cả `view` lẫn `edit`.
- Một Role không cấp action không thu hồi action mà Role khác đã cấp.
- Tính riêng theo từng `functionCode`, Object và action. Không lấy quyền của Object này áp dụng cho Object khác.

Gọi tập action Role đã hợp nhất trên Object là `roleActions`. Nếu action không có trong `roleActions`, từ chối action đó ngay cả khi một security rule có scope tương ứng; security rule không được mở rộng vượt quá cổng quyền của Role.

Ánh xạ hai lớp quyền như sau:

| Role action | Security rule cần kiểm tra khi Object có rule |
|---|---|
| `create` | Rule `type: 1`, scope `create` |
| `view` | Rule `type: 2`, scope `read` |
| `edit` | Rule `type: 2`, scope `edit` |
| `delete` | Rule `type: 2`, scope `delete` |

### 3. Xác định chế độ bảo mật của Object

Liệt kê rules của Object mà không lọc `status`, rồi kiểm tra trạng thái từng rule để xác định Object có ít nhất một rule active hay không.

- Nếu Object không có rule active: lớp bảo mật chi tiết không hạn chế quyền record/field. Áp dụng trực tiếp quyền qua cổng Role cho toàn bộ records và fields của Object; Super Admin đi qua cổng Role, còn non-Super Admin dùng `roleActions` đã hợp nhất. Các rule inactive không kích hoạt chế độ mặc định từ chối và không đóng góp quyền.
- Nếu Object có ít nhất một rule active: bật chế độ bảo mật chi tiết và chuyển sang mặc định từ chối đối với mọi user, kể cả Super Admin. Không tự động áp dụng quyền cấp Object cho mọi record; chỉ các rule active khớp user và record mới có thể cộng quyền trở lại.

Hệ quả: khi Object có ít nhất một rule active, nếu không có rule active phù hợp cho quyền tạo thì user không được tạo record; nếu không có rule active phù hợp cho một record hiện có thì user không được xem, sửa hoặc xoá record đó. Quy tắc này áp dụng cả với Super Admin.

Một rule giữ chỗ active với `personnelFilters: [{"type": 1, "op": "include", "personnelId": null}]` cũng kích hoạt chế độ này, dù không khớp nhân sự nào và không cấp quyền cho ai. Dùng để giữ slot action chưa cấp cho người dùng và duy trì mặc định từ chối, đặc biệt với Object do backend quản lý. Không có rule active nghĩa là lớp bảo mật chi tiết không hạn chế dữ liệu; vẫn phải qua cổng Role, không phải mọi user mặc nhiên có đủ CRUD. Đọc mục **Object do backend quản lý và rule giữ chỗ** trước khi dùng cấu hình này.

### 4. Hợp nhất các security rule phù hợp

Chỉ đưa một rule vào tập tính quyền khi rule đang active và khớp đầy đủ:

- Với `type: 1`: user khớp `personnelFilters`; rule không dùng record filter.
- Với `type: 2`: user khớp `personnelFilters` và record đồng thời khớp `filter`.

Nếu một user hoặc record xuất hiện trong nhiều rule, hợp nhất scope của tất cả rule đồng thời khớp user + record theo phép cộng quyền:

- Hợp nhất các field được phép `create`, `read` hoặc `edit` thành một tập hợp lớn hơn.
- Cấp `delete` nếu có ít nhất một rule phù hợp trả `delete: yes` và Role cũng có action `delete`.
- Xem `none` hoặc `no` là rule đó không cộng quyền cho scope tương ứng; không dùng chúng để thu hồi quyền mà rule phù hợp khác đã cấp.
- Không diễn giải chung personnel filter `exclude` thành “user chỉ cần thuộc đối tượng bị loại trừ thì không khớp rule”. Đặc biệt với audience theo Role (`type: 4`, `op: exclude`), runtime hiện tại kiểm tra từng Role của user: user vẫn khớp rule nếu có ít nhất một Role không nằm trong danh sách loại trừ. Chỉ khi tất cả Role của user đều bị loại trừ (hoặc user không có Role để khớp) thì nhánh này không cấp quyền. Đây là điều kiện chọn audience, không phải lệnh cấm ghi đè các rule khác. Đọc phần **Semantics của Role `exclude` khi user có nhiều Role** trong [references/api-object-security-rules.md](references/api-object-security-rules.md) trước khi thiết kế hoặc kiểm thử loại rule này.
- Nếu một rule cấp `all`, kết quả hợp nhất của scope đó là toàn bộ fields. Với `include`/`exclude`, tính tập field mà từng rule cho phép rồi lấy hợp của các tập đó.

Tóm tắt phép tính:

```text
Không có security rule active:
  effectiveActions = quyền qua cổng Role trên mọi record
  (Super Admin đi qua cổng Role; user thường dùng roleActions)

Có ít nhất một security rule active:
  effectiveActions(record, field)
    = quyền qua cổng Role
      giao với
      ánh xạ action từ hợp các scope của mọi active rule khớp user và record
```

Ví dụ: user có Role A cấp `view`, Role B cấp `edit` và `delete` trên `object_a`. `object_a` có hai active rules cùng khớp user và record X: rule 1 cho đọc mọi field, sửa field `amount`, không xoá; rule 2 cho sửa field `status` và cho xoá. Trên record X, user được xem mọi field, sửa `amount` và `status`, đồng thời được xoá. `delete: no` của rule 1 không huỷ `delete: yes` của rule 2. Trên record Y không khớp rule nào, user không có quyền dù tổng Role đã chứa `view`, `edit` và `delete`.

## Phân loại yêu cầu phân quyền

Khi nhận yêu cầu “phân quyền dữ liệu”, “cấp quyền” hoặc “thiết lập quy tắc bảo mật”, chọn trường hợp phù hợp bên dưới, gồm cả chặn CRUD trực tiếp trên Object do backend quản lý.

### 1. Phân quyền tính năng

Tạo hoặc cập nhật Role, rồi gán Role cho user. Cấu hình `permissions[]` của Role để cấp đúng tính năng và action.

1. Xác định user, tính năng và các action cần cấp.
2. Tìm Role phù hợp; chỉ tạo Role mới nếu chưa có Role đáp ứng đúng phạm vi.
3. Không đoán `functionCode` hoặc action của tính năng. Lấy cấu trúc từ Role hiện có đã được xác nhận trên cùng Workspace hoặc từ mã mà người dùng cung cấp.
4. Tạo/cập nhật Role, đọc lại Role để xác minh, rồi gọi `roles/addAccount` nếu user chưa có Role.
5. Đọc lại user để xác minh Role đã được gán.

### 2. Phân quyền toàn bộ records của một Object

Dùng Role khi user cần tạo, xem, sửa hoặc xoá toàn bộ records của một hay nhiều Object và không cần giới hạn theo record hoặc field.

1. Tạo hoặc cập nhật Role.
2. Thêm permission có `functionCode: "record"`, `groupSlug: "object"`, action tương ứng và phạm vi Object trong `values`.
3. Dùng `valueOption: 1` để chỉ áp dụng cho các Object trong `values`; mỗi value phải có Object `id` và `slug` đã resolve.
4. Gán Role cho user.
5. Liệt kê toàn bộ security rules của Object mà không lọc trạng thái và xác định có rule active hay không.
6. Nếu Object không có rule active, dừng ở Role; các action Role đã hợp nhất áp dụng cho mọi record.
7. Nếu Object có ít nhất một rule active, Role một mình chưa đủ. Tạo hoặc cập nhật active rule phạm vi rộng cho user/Role đích:
   - Dùng rule `type: 1` với scope `create` trên toàn bộ field khi cần quyền tạo.
   - Dùng các rules `type: 2` riêng cho View, Edit và Delete, cùng `filter.conditions: []`, khi cần các quyền đó trên mọi record hiện có. Đặt scope không phải mục đích của từng rule thành `none` hoặc `no`.
   - Chỉ cấp những action đã có trong `roleActions`; không dùng rule để vượt quyền Role.

Ví dụ cấp toàn bộ quyền tạo/xem/sửa/xoá records của Ticket:

```json
{
  "functionCode": "record",
  "actions": ["create", "view", "edit", "delete"],
  "groupSlug": "object",
  "values": [
    {
      "id": "OT00000000008",
      "slug": "ticket"
    }
  ],
  "valueOption": 1
}
```

Đọc [references/sample-customer-service-role.json](references/sample-customer-service-role.json) khi cần mẫu Role Ticket đã được ẩn danh. Mẫu có mô tả “Xem/sửa/xoá…” nhưng `permissions[0].actions` chỉ là `["view"]`. Xem `actions` là nguồn sự thật; không suy ra quyền từ tên hoặc mô tả. Muốn cấp xem/sửa/xoá, gửi đủ `["view", "edit", "delete"]`.

### 3. Phân quyền chi tiết theo record hoặc field

Sử dụng Object Security Rule khi cần giới hạn quyền đến từng record, nhóm record hoặc từng field, hoặc khi Object đã có ít nhất một rule active nên mọi quyền record của mọi user, kể cả Super Admin, bắt buộc phải đi qua lớp bảo mật này.

1. Với action cần cấp cho user, đảm bảo user đã có Role với quyền records ở mức Object tương ứng. Object Security Rule là lớp chi tiết bổ sung, không thay thế bước cấp Role theo yêu cầu này. Không cấp thêm Role cho action đang muốn chặn hoặc chỉ tạo rule giữ chỗ.
2. Thiết kế mỗi rule chỉ có một mục đích cấp quyền chính. Khi yêu cầu bao gồm đủ create/view/edit/delete, tạo tối thiểu bốn rules độc lập:
   - **Create rule:** dùng `type: 1`; xác định ai được tạo record và những fields nào được phép nhập qua scope `create`.
   - **View rule:** dùng `type: 2`; xác định ai được xem, records nào được xem qua `filter` và fields nào được xem qua scope `read`. Đặt `edit: none`, `delete: no`.
   - **Edit rule:** dùng `type: 2`; xác định ai được sửa, records nào được sửa và fields nào được sửa qua scope `edit`. Đặt `read: none`, `delete: no` trong chính rule này.
   - **Delete rule:** dùng `type: 2`; xác định ai được xoá và records nào được xoá. Đặt `read: none`, `edit: none`, `delete: yes`; không thêm field ID cho delete.
3. Tạo thêm rules cho cùng một action khi audience, điều kiện record hoặc tập fields khác nhau. Ví dụ, tách “edit selected fields while Status is Creating/Draft” và “edit Status for all records” thành hai Edit rules; không ép hai ý định này vào một filter/scope khó bảo trì.
4. Không gộp View/Edit/Delete vào một rule chỉ để giảm số lượng rules. Việc tách action giúp thay đổi điều kiện, audience hoặc field scope của một quyền mà không vô tình mở rộng hai quyền còn lại. Chỉ duy trì rule gộp khi người dùng yêu cầu rõ vì lý do tương thích với cấu hình legacy.
5. Dùng `personnelFilters` type `1` để chọn user cụ thể hoặc type `4` để chọn user theo Role. Ngoại lệ giữ chỗ không chọn nhân sự dùng type `1`, `op: "include"`, `personnelId: null` như mục 4 bên dưới; không resolve hay thay thế `null` bằng một user. Dùng các type khác chỉ sau khi resolve đúng phòng ban, vị trí hoặc field tra cứu.
6. Với record cụ thể, dùng điều kiện trên field định danh ổn định đã được API Object xác nhận. Không tự giả định field hoặc toán tử hợp lệ.
7. Với field cụ thể, dùng `include` hoặc `exclude` và một phần tử scope cho mỗi `fieldId`. `delete` chỉ nhận `yes` hoặc `no`, không nhận field ID.
8. Kiểm tra tổng số rules trước khi tạo vì mỗi Object có giới hạn 50. Khi gần giới hạn, hợp nhất các rules có cùng action và cùng semantics nếu vẫn dễ hiểu; không gộp các action khác nhau để lách giới hạn mà chưa được người dùng quyết định.

### 4. Object do backend quản lý và rule giữ chỗ

Object do backend quản lý đóng vai trò bảng dữ liệu cho logic ứng dụng; người dùng không được thao tác trực tiếp một phần hoặc toàn bộ Create/View/Edit/Delete. Đây là phân loại theo nghiệp vụ, không phải Object nền tảng có sẵn hoặc giá trị `isStandard`.

1. Chốt ma trận quyền theo từng action: audience nào được thao tác trực tiếp, phạm vi record/field và action nào chỉ backend được thực hiện. Khi phối hợp `$cogover-custom-module` tạo Object mới, tạo bộ mặc định bốn rules riêng Create/View/Edit/Delete; action bị chặn vẫn có một rule giữ chỗ. Chỉ bổ sung rule cùng action khi cần audience/filter/field scope khác nhau; không gộp các action.
2. Với action không cấp cho bất kỳ người dùng nào, dùng rule active có audience duy nhất:

   ```json
   {
     "status": 1,
     "personnelFilters": [
       {"type": 1, "op": "include", "personnelId": null}
     ]
   }
   ```

   Đây là phần cấu hình của rule, không phải payload tạo hoàn chỉnh. Gửi JSON `null` thật, không phải chuỗi `"null"`, ID giả hay mảng rỗng. Giữ `type`, `filter` và `scopes` hợp lệ cho action theo [Object Security Rules API](references/api-object-security-rules.md), mục **Rule giữ chỗ không chọn nhân sự**. `type: 1` trong personnel filter độc lập với `type` của rule.
3. Rule này có hai mục đích: giữ slot cho action để cấu hình sau và kích hoạt/duy trì chế độ mặc định từ chối của Object. Audience không khớp nhân sự nào, kể cả Super Admin, nên scope của rule không cấp quyền cho ai. Rule không phải lệnh cấm có ưu tiên: active rule khác vẫn có thể cộng quyền. Đọc toàn bộ rules để chắc không có rule khác cấp action đang muốn chặn; không thêm audience khác vào rule giữ chỗ.
4. Ví dụ Object “Lượt khuyến mãi đã sử dụng”: View rule cấp đọc theo audience và phạm vi đã chốt; Create/Edit/Delete dùng ba rule giữ chỗ active. Nếu chỉ backend được đọc và ghi toàn bộ, cả bốn rules đều dùng audience giữ chỗ. Không biểu diễn chặn bằng cách bỏ hết rules hoặc tắt hết rules: khi không còn rule active, quyền qua cổng Role lại áp dụng trên mọi record/field.
5. Không cần thêm Role để rule giữ chỗ hoạt động. Backend dùng quyền caller vẫn chịu quyền của caller; rule giữ chỗ không tự cấp quyền cho backend. Nếu dùng Custom Backend Module, phối hợp `$cogover-custom-module` để dùng `data.asSystem()` cùng project policy giới hạn đúng Object/action và kiểm tra quyền nghiệp vụ của caller.
6. Sau khi ghi, đọc lại từng rule và toàn bộ danh sách không lọc trạng thái; xác minh `status: 1`, audience chỉ có bộ giá trị trên, scope đúng action và không có grant xung đột ở rule khác. Báo rõ tác động nếu đây là rule active đầu tiên. Không tắt/xoá rule active cuối cùng khi mục tiêu vẫn là mặc định từ chối. Khi mở một slot cho user, cập nhật audience/filter/scopes theo quyền được yêu cầu rồi tính lại quyền cộng dồn.
7. Kiểm thử CRUD trực tiếp bằng danh tính phù hợp theo phần kiểm thử bên dưới; bao gồm Super Admin khi cần chứng minh không bypass. Tách ca backend được phép thực hiện nghiệp vụ khỏi ca người dùng bị chặn thao tác trực tiếp. Nếu chưa có backend hoặc thiếu credential/fixture hợp lệ, báo cấu hình đã xác minh và các ca runtime còn chờ; không coi readback là PASS end-to-end. Không mở tạm CRUD cho người dùng chỉ để tạo fixture cho Object do backend quản lý; dùng đường hệ thống đã được phép khi sẵn sàng.

### Đặt tên và mô tả security rule

Viết `name` và `description` gốc bằng tiếng Anh cho mọi rule mới hoặc rule được đổi tên:

1. Viết tên ngắn nhưng thể hiện action và phạm vi nghiệp vụ, ví dụ `[Finance App] - Delete Draft or Cancelled Cash Transactions`.
2. Viết description đủ để người không tạo rule vẫn hiểu: audience nào được áp dụng, action được cấp, filter chọn records, field scope và những quyền cố ý không cấp.
3. Giữ `name` không quá 100 ký tự và `description` không quá 500 ký tự.
4. Không dùng description rỗng, không chỉ lặp lại tên và không dùng các mô tả chung như `Allow access`.
5. Với rule giữ chỗ, tên nêu action và mục đích, ví dụ `[App] - Create Promotion Usage - Placeholder`; description giải thích không chọn nhân sự, giữ slot và duy trì mặc định từ chối, không tuyên bố rule ghi đè quyền khác. Ví dụ: `Reserves the create slot for backend-managed promotion usage. Matches no personnel and keeps detailed security active. Grants no direct user access and does not override other rules.`

| Action | Ví dụ tên tiếng Anh | Nội dung description phải nêu |
|---|---|---|
| Create | `[Finance App] - Create Cash Transactions` | Audience, fields được nhập và việc rule không cấp quyền trên records đã tồn tại |
| View | `[Finance App] - View Eligible Cash Transactions` | Audience, record filter, fields được xem và không cấp edit/delete |
| Edit | `[Finance App] - Edit Draft Cash Transactions` | Audience, record filter, fields được sửa và không cấp read/delete trong rule này |
| Delete | `[Finance App] - Delete Draft or Cancelled Cash Transactions` | Audience, record filter được xoá và không cấp read/edit |

Ví dụ một View rule chỉ cho xem mọi field của các records phù hợp:

```json
{
  "objectTypeId": "{OBJECT_ID}",
  "isStandard": 0,
  "name": "[App] - View Eligible Object Records",
  "description": "Allows {AUDIENCE} to view all fields of {OBJECT} records that satisfy {FILTER_SUMMARY}. Grants no edit or delete access.",
  "filter": {
    "logicType": "AND",
    "logic": "",
    "conditions": [
      {
        "field": "{FIELD_SLUG}",
        "op": "=",
        "params": "{VALUE}"
      }
    ]
  },
  "status": 1,
  "personnelFilters": [
    {
      "type": 1,
      "op": "include",
      "personnelId": "{USER_OR_PERSONNEL_ID_REQUIRED_BY_RULE_API}"
    }
  ],
  "scopes": [
    {
      "scope": "read",
      "op": "all"
    },
    {
      "scope": "edit",
      "op": "none"
    },
    {
      "scope": "delete",
      "op": "no"
    }
  ],
  "type": 2
}
```

Đọc [references/sample-cash-transaction-security-rules.json](references/sample-cash-transaction-security-rules.json) để tham khảo mẫu đã ẩn danh cách tách rules của Object `cash_transaction`. Mẫu có năm rules: một Create, một View, một Delete và hai Edit rules. Dùng cấu trúc filter/personnel/scopes làm tham khảo; không sao chép các description rỗng trong cấu hình cũ. Không dùng hoặc lưu API key đã dùng để lấy snapshot.

Không mặc định `workspace user id` và `personnelId` là cùng một ID. Kiểm tra dữ liệu chi tiết user để tìm quan hệ Personnel; nếu response không có quan hệ rõ ràng, tra Object Personnel theo email/tài khoản và xác minh khớp chính xác trước khi dùng ID record. Không sao chép `personnelId` top-level từ snapshot Role mẫu vì đó là người gọi request, không phải user đích.

## Quản lý người dùng

Thực hiện các thao tác sau theo [references/api-users.md](references/api-users.md):

- Xem danh sách hoặc chi tiết user.
- Mời user vào Workspace bằng email, license và ít nhất một Role.
- Xoá quyền truy cập Workspace; phân biệt rõ giữ hồ sơ (`is_delete_personnel: false`) và đánh dấu xoá cả hồ sơ (`true`).

Khi resolve user theo email, ưu tiên khớp chính xác sau khi dùng API tìm kiếm gần đúng. Nếu có nhiều kết quả hoặc nhiều trạng thái, trình bày ứng viên để làm rõ trước khi ghi.

## Quản lý Role và gán Role

Thực hiện các thao tác sau theo [references/api-roles.md](references/api-roles.md):

- Xem danh sách và chi tiết Role.
- Tạo, cập nhật hoặc xoá Role.
- Gán Role bằng `roles/addAccount` và gỡ Role bằng `roles/removeAccount`.

Khi cập nhật Role, đọc chi tiết mới nhất trước, giữ nguyên các permission không được yêu cầu thay đổi, dùng permission `id` cho phần tử hiện có và `status: 0` khi cần xoá một permission. Không coi việc bỏ permission khỏi mảng là thao tác xoá.

## An toàn khi ghi và xoá

1. Trước thao tác ghi, báo rõ Workspace, user/Role/Object/rule mục tiêu và phạm vi quyền sẽ thay đổi.
2. Nếu yêu cầu ghi đã chỉ rõ mục tiêu và thay đổi, thực hiện trong phạm vi đó. Nếu mục tiêu, hành động hoặc chế độ xoá hồ sơ còn mơ hồ, yêu cầu làm rõ.
3. Trước khi xoá user, xác định `is_delete_personnel`; mặc định an toàn là `false` nếu người dùng chỉ muốn gỡ khỏi Workspace.
4. Trước khi xoá Role, kiểm tra user đang được gán Role và ảnh hưởng mất quyền. Không xoá Role quản trị cao nhất hoặc làm Workspace mất quản trị viên cuối cùng.
5. Trước khi xoá Object Security Rule, nhắc rằng xoá là vĩnh viễn; dùng `status: 0` nếu mục tiêu chỉ là tạm dừng.
6. Trước khi tạo hoặc bật rule active đầu tiên của một Object, cảnh báo rằng thao tác sẽ chuyển toàn Object từ quyền cấp Object áp dụng trên mọi record sang mặc định từ chối; mọi user, kể cả Super Admin, có thể mất quyền nếu chưa được bao phủ bởi active rules.
7. Trước khi xoá hoặc tắt rule active cuối cùng của một Object, cảnh báo rằng thao tác sẽ tắt lớp bảo mật chi tiết dù Object vẫn còn rule inactive; quyền qua cổng Role sẽ lại áp dụng cho toàn bộ records và có thể làm tăng quyền ngoài ý muốn.
8. Trước khi sửa rule gộp hiện có, đánh giá việc tách thành các rules theo action; giữ nguyên quyền hiệu lực trong quá trình chuyển đổi và xác minh runtime trước khi xoá rule cũ.
9. Không lặp mù quáng request tạo/gán khi timeout. Đọc lại trạng thái trước khi thử lại để tránh tạo trùng hoặc kết luận sai.

## Xác minh và báo cáo

Xem kiểm thử quyền thực tế trên records là bước xác minh quan trọng nhất. Đọc lại cấu hình Role/rule chỉ chứng minh cấu hình đã được lưu, không chứng minh user thật sự được phép hoặc bị từ chối đúng như yêu cầu.

### 1. Xác minh cấu hình đã lưu

1. Chỉ coi request cấu hình thành công khi HTTP status phù hợp và response có `r: 0`.
2. Sau create/update Role, gọi `roles/view`; response update có thể chứa trạng thái cũ.
3. Sau add/remove Role, gọi `users/view` và đối chiếu trường `role`.
4. Sau create/update Object Security Rule, gọi endpoint chi tiết và đối chiếu `filter`, `personnelFilters`, `scopes`, `status` và `type`.
5. Tính lại trạng thái Super Admin, `roleActions` đã hợp nhất, Object có rule active hay không, các active rules khớp từng user/record và scope hiệu lực cuối cùng. Không loại Super Admin khỏi bước đánh giá security rule.

### 2. Chọn users và credential kiểm thử

1. Lập danh sách persona cần kiểm thử từ yêu cầu: user có/không có Role, thuộc/không thuộc phòng ban, giữ vị trí khác nhau, record khớp/không khớp rule và các tổ hợp Role cần chứng minh quyền cộng dồn.
2. Nếu cần từ hai persona trở lên hoặc rule phụ thuộc Role/phòng ban/vị trí, yêu cầu người dùng xác nhận:
   - những user cụ thể nào sẽ được dùng để test;
   - người dùng sẽ cung cấp API key của từng user hay cho phép AI tạo key tạm;
   - phạm vi Object/action sẽ test và việc tạo rồi xoá records test.
3. Không dùng API key của Super Admin hoặc user cấu hình thay cho user đích; như vậy chỉ kiểm thử quyền của chủ key, không kiểm thử persona cần xác minh.
4. Nếu người dùng không cung cấp key và không cho phép tạo key, dừng ở kiểm tra cấu hình và báo rõ rằng quyền runtime chưa được xác minh end-to-end.

### 3. Resolve phòng ban, nhân sự và vị trí

Không dùng `$object-info`, `$object-record` hoặc các Object `department`, `personnel`, `department_personnel` để resolve dữ liệu tổ chức trong bước này. Dùng các API chuyên biệt và tài liệu tương ứng:

1. Resolve phòng ban bằng Departments API:
   - Dùng `POST /bapi/v1/departments/list` để tìm theo tên/ID/trạng thái. Nếu rule phụ thuộc phòng ban con, dùng `type: "tree"` hoặc truy vấn hierarchy phù hợp để thấy quan hệ cha/con.
   - Khớp chính xác tên và ưu tiên phòng ban active. Khi có nhiều kết quả cùng tên, không tự chọn; đối chiếu parent/hierarchy hoặc yêu cầu người dùng xác nhận.
   - Gọi `POST /bapi/v1/departments/view` với ID đã chọn để xác nhận thông tin mới nhất trước khi dùng trong personnel filter.
2. Resolve vị trí bằng Positions API:
   - Dùng `POST /bapi/v1/positions/list`, có thể lọc theo `department_ids`, rồi gọi `POST /bapi/v1/positions/view` để xác nhận ID và trạng thái.
   - Kiểm tra `is_department_only` và `department_ids`. Không gán một Position giới hạn theo phòng ban vào Department ngoài phạm vi của Position đó.
3. Resolve nhân sự bằng Personnels API:
   - Dùng `POST /bapi/v1/personnels/list` để tìm theo tên, ID, trạng thái, Role, phòng ban hoặc vị trí. API list không có filter email riêng; khi mục tiêu được chỉ định bằng email, thu hẹp bằng các filter được hỗ trợ rồi so khớp chính xác với mảng `emails` trong response, phân trang tiếp nếu cần.
   - Gọi `POST /bapi/v1/personnels/view` để xác nhận Personnel và danh sách quan hệ Department/Position hiện tại. Lấy relation ID, `department_id`, `position_id`, `is_primary` và `level` từ dữ liệu mới nhất khi cần cập nhật hoặc hoàn tác.
4. Đối chiếu Personnel với Users API bằng email/account hoặc quan hệ được API trả về. Phân biệt workspace user ID, `account_id`, Personnel ID, Department ID, Position ID và relation ID; không hoán đổi các loại ID này.

### 4. Thiết lập phòng ban/vị trí cho nhân sự test

Chỉ thay đổi quan hệ tổ chức khi rule cần kiểm thử phụ thuộc phòng ban/vị trí và persona hiện tại chưa có quan hệ phù hợp. Đây là thay đổi dữ liệu nhân sự, không phải một phần ngầm định của việc tạo API key.

1. Xác nhận với người dùng Personnel nào sẽ bị thay đổi, Department/Position đích và thay đổi là tạm thời hay lâu dài. Không tự tạo mới Department, Position hoặc Personnel nếu người dùng chỉ yêu cầu chuẩn bị persona test.
2. Trước khi ghi, gọi `personnels/view` và lưu snapshot đầy đủ các quan hệ hiện có cần bảo toàn, gồm relation ID, Department, Position, `level` và `is_primary`.
3. Resolve Department và Position bằng API chuyên biệt như mục 3; xác nhận cả hai đang dùng được và Position hợp lệ cho Department đích.
4. Dùng credential quản trị/kiểm soát gọi `POST /bapi/v1/personnels/departmentPosition`. Với quan hệ mới, gửi `personnel_id`, `department_id`, `position_id`, `level`, `is_primary` và `deleted: false`; với quan hệ hiện có, gửi đúng relation `id` khi cập nhật. Không suy đoán ID quan hệ.
5. Gọi lại `personnels/view` và chỉ tiếp tục khi quan hệ Department/Position đã lưu đúng, quan hệ chính không bị thay đổi ngoài ý muốn và persona khớp personnel filter của rule.
6. Chỉ sau bước đọc lại thành công mới tạo/sử dụng API key của nhân sự đó và gọi `$object-record` để kiểm thử đọc/tạo/sửa/xoá record. Không dùng kết quả cập nhật quan hệ chưa được xác minh làm căn cứ kết luận quyền.
7. Ghi lại mọi relation được thêm/sửa và snapshot ban đầu để cleanup. Với thiết lập tạm, kế hoạch kiểm thử phải bao gồm phục hồi quan hệ sau khi kiểm thử records hoàn tất.

### 5. Tạo API key tạm khi được phép

Chỉ thực hiện sau khi người dùng cho phép rõ việc AI tạo API key cho danh sách users test.

1. Đọc [references/api-api-keys.md](references/api-api-keys.md) trước khi gọi API.
2. Resolve `accountId` từ `account_id` của active user; không dùng workspace user ID hoặc Personnel ID. Không thể tạo key hợp lệ cho invited user chưa có account.
3. Dùng tên duy nhất có tiền tố `codex-permission-test`, mô tả rõ user/Object/mục đích và `isActive: true`.
4. Đặt `expiresOn` không muộn hơn thời điểm hiện tại cộng `172800000` milliseconds (48 giờ). Không tạo key test không hết hạn.
5. Nhận credential đầy đủ một lần từ `data.secretToken`; chỉ giữ trong bộ nhớ tiến trình cần cho test. Không ghi vào repo, file, log, URL, báo cáo hoặc câu trả lời.
6. Ghi riêng key ID, account ID, user, expiry và trạng thái cleanup nhưng không ghi secret.
7. Dùng credential quản trị ban đầu để xoá key tạm sau test; không để key tự xoá chính nó. Không cập nhật hoặc xoá API key do người dùng cung cấp.

Nếu caller không có quyền quản lý API key, yêu cầu người dùng cung cấp key của persona hoặc chấp nhận chỉ audit cấu hình; không tìm cách mượn danh tính khác.

### 6. Lập ma trận kiểm thử quyền records

Lập một hàng cho mỗi tổ hợp `user × Object × action × record/field` và ghi rõ kết quả mong đợi cùng nguồn quyền Role/rule. Khi Object có security rules, chuẩn bị tối thiểu một record khớp và một record không khớp rule cho từng nhánh cần chứng minh.

Với slot giữ chỗ không chọn nhân sự, không có ca user được phép từ chính rule đó: kiểm thử từ chối trực tiếp và ghi ca backend được phép thành nhánh riêng. Chỉ tạo cặp record khớp/không khớp khi có điều kiện record cần phân biệt, chẳng hạn phạm vi của View rule; không tạo ca allow giả cho audience `personnelId: null`.

Nếu persona phụ thuộc Department/Position, không bắt đầu ma trận cho đến khi `personnels/view` xác nhận quan hệ cần thiết. Credential dùng với `$object-record` phải là API key của đúng account gắn với Personnel vừa xác minh, không phải credential quản trị đã thiết lập quan hệ.

Thực hiện bằng `$object-record` dưới credential của đúng user test:

1. **View/read:** lọc theo marker hoặc ID của fixture; xác minh record được phép xuất hiện và record bị cấm không xuất hiện/không đọc được. Với field security, xác minh field được phép có mặt và field bị cấm không bị lộ.
2. **Create:** tạo record test chỉ với các field được phép, rồi thử riêng một payload chứa field không được phép khi cần kiểm tra field-level create. Không kết luận chỉ từ HTTP response; đọc lại bằng credential kiểm soát để biết record/field có thực sự được lưu.
3. **Edit:** cập nhật một field được phép và một field bị cấm trong các request tách biệt. Đọc lại bằng credential kiểm soát để xác minh giá trị cuối cùng và tránh nhầm một request bị từ chối toàn bộ với update một phần.
4. **Delete:** dùng record test chuyên biệt, không dùng record nghiệp vụ. Xác minh cả trường hợp được phép và bị từ chối khi yêu cầu cần chứng minh hai nhánh; sau lần xoá bị từ chối, đọc lại để chắc record vẫn tồn tại.

Dùng credential quản trị/kiểm soát để chuẩn bị và đọc lại fixtures khi persona không có quyền tương ứng. Mọi record test phải có marker duy nhất, ví dụ `codex-permission-test-{timestamp}-{random}`, trong một field có thể tìm kiếm đã được schema xác nhận. Theo dõi mọi ID được tạo, kể cả record xuất hiện do một thao tác lẽ ra phải bị từ chối nhưng lại thành công.

Với Object do backend quản lý, credential quản trị/Super Admin cũng có thể bị rules chặn. Khi đó phối hợp sub-agent backend qua `$cogover-custom-module` dùng đường hệ thống đã được phép để tạo/đọc lại/dọn fixtures, với policy giới hạn đúng Object/action. Không dùng `$object-record` dưới key quản trị như một cách bypass. Nếu đường hệ thống chưa sẵn sàng, ghi ca test còn chờ thay vì mở tạm quyền trực tiếp; chốt cách cleanup trước khi tạo fixture.

Không thao tác trên record thật của người dùng. Không coi lỗi HTTP là bằng chứng duy nhất cho deny và không coi `r: 0` là bằng chứng duy nhất cho allow; luôn kiểm tra trạng thái record/field sau request.

### 7. Dọn dẹp bắt buộc

1. Dùng `$object-record` tìm lại toàn bộ records theo marker và hợp nhất với danh sách ID đã theo dõi. Nếu Object do backend quản lý không cho credential kiểm soát đọc đủ fixtures, phối hợp backend dùng đường hệ thống đã được phép cho bước tìm này và các bước cleanup records bên dưới.
2. Trước khi xoá, liệt kê Object, ID và tên/marker rồi yêu cầu xác nhận theo quy tắc xoá của `$object-record`. Việc xác nhận kế hoạch test ban đầu không thay thế xác nhận xoá khi đã biết ID cụ thể.
3. Xoá chỉ các fixtures của phiên test. Nếu persona không có quyền delete, dùng credential quản trị/kiểm soát có quyền delete thực tế cho cleanup; cleanup không phải là bước chứng minh quyền. Với Object do backend quản lý mà cả quản trị cũng bị chặn, phối hợp backend xoá qua đường hệ thống đã được phép và giới hạn đúng ID/marker của phiên test; không tắt rule giữ chỗ hoặc thêm grant trực tiếp để cleanup.
4. Đọc lại theo marker và từng ID để xác minh không còn fixture; với Object chặn cả View trực tiếp, dùng đường hệ thống đã được phép để kiểm tra. Nếu xoá không thành công, báo chính xác Object/ID còn lại và nguyên nhân; không tuyên bố đã dọn sạch.
5. Sau khi cleanup records hoàn tất, phục hồi mọi quan hệ Department/Position đã thiết lập tạm: dùng `personnels/departmentPosition`, đặt `deleted: true` với đúng relation ID đã thêm, và khôi phục Position, `level`, `is_primary` hoặc quan hệ cũ theo snapshot khi chúng đã bị sửa.
6. Gọi `personnels/view` để so sánh với snapshot ban đầu. Không xoá Department, Position hoặc Personnel chỉ để cleanup, trừ khi chính các entity đó được tạo riêng cho test theo yêu cầu rõ ràng. Nếu phục hồi thất bại, báo Personnel ID, Department ID, Position ID, relation ID và sai khác còn lại.
7. Sau khi cleanup records và quan hệ tổ chức hoàn tất, xoá mọi API key tạm do AI tạo bằng credential quản trị và dùng API danh sách để xác minh key không còn. Nếu xoá key thất bại, vô hiệu hoá `isActive: false` với nguyên `expiresOn`, báo key ID/expiry và tiếp tục thu hồi sớm nhất có thể.
8. Không xoá key do người dùng cung cấp. Không để record test, thay đổi quan hệ tổ chức tạm hoặc key tạm bị bỏ quên khi test thất bại hay bị gián đoạn; ưu tiên cleanup trước khi kết thúc.

### 8. Báo cáo kết quả

1. Báo cấu hình đã lưu và phép tính quyền hiệu lực, nhưng tách riêng khỏi kết quả runtime.
2. Trình bày ma trận theo user/persona, Object, record/field, action, kỳ vọng, HTTP/`r`, trạng thái thực tế sau request và kết luận pass/fail.
3. Báo số records test đã tạo/xoá, kết quả kiểm tra marker sau cleanup, các quan hệ Department/Position đã thay đổi và trạng thái phục hồi, số API keys tạm đã tạo/thu hồi cùng mọi ID còn tồn đọng. Không báo secret.
4. Sau thao tác user, đọc lại danh sách/chi tiết phù hợp. Với xoá kèm hồ sơ, trạng thái có thể là `DELETED` thay vì biến mất ngay.
5. Khi lỗi, giữ HTTP status, `r`, `msg`, `meta` và `requestId` để chẩn đoán nhưng loại bỏ mọi credential.
