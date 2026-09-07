# Object Security Rules API

Đọc toàn bộ tài liệu này trước khi tạo, cập nhật hoặc xoá quy tắc bảo mật chi tiết theo record hoặc field.

Mỗi rule xác định ba phần độc lập: records phù hợp (`filter`), người dùng áp dụng (`personnelFilters`) và quyền được cấp (`scopes`). Cả ba phần phải phù hợp thì rule mới cấp quyền.

Khi audit việc lớp bảo mật đã được bật hay chưa, gọi endpoint danh sách theo Object mà không gửi bộ lọc `status`, rồi kiểm tra trạng thái từng rule. Object chỉ chuyển sang mặc định từ chối khi có ít nhất một rule `status: 1`; rule inactive không kích hoạt lớp bảo mật và không đóng góp quyền. Khi lớp bảo mật đã bật, mọi user, kể cả Super Admin, phải khớp active rule phù hợp để được cấp quyền record/field. Nhiều active rules cùng khớp user và record sẽ cộng dồn scope. `none`, `no` hoặc một rule không khớp không thu hồi quyền do active rule phù hợp khác cấp.

## Endpoint

| Thao tác | Method | Endpoint | Thành công |
|---|---|---|---|
| Danh sách | `POST` | `/bapi/v1/object-security-rules/list` | `200`, `r: 0` |
| Chi tiết | `POST` | `/bapi/v1/object-security-rules/view` | `200`, `r: 0` |
| Tạo | `POST` | `/bapi/v1/object-security-rules` | `201`, `r: 0` |
| Tạo alias | `POST` | `/bapi/v1/object-security-rules/create` | `201`, `r: 0` |
| Cập nhật | `PUT` | `/bapi/v1/object-security-rules/{ruleId}` | `200`, `r: 0` |
| Xoá | `POST` | `/bapi/v1/object-security-rules/delete` | `200`, `r: 0` |

Workspace được lấy từ token; không gửi Workspace ID riêng.

## Chọn loại rule

| `type` | Mục đích | `filter` | Personnel type | Scope bắt buộc |
|---|---|---|---|---|
| `1` | Ai được tạo record và được nhập field nào | Không dùng | `1`–`5` | Chỉ `create` |
| `2` | Ai được xem/sửa/xoá records phù hợp | Bắt buộc | `1`–`10` | Đủ `read`, `edit`, `delete` |

- Không thể đổi `type` sau khi tạo.
- Cần cả quyền tạo và quyền trên record hiện có thì tạo hai rule.
- `status: 1` active, `0` inactive.
- Chỉ cần có ít nhất một rule active là chế độ mặc định từ chối áp dụng cho mọi user, kể cả Super Admin. Super Admin không bypass Object Security Rules.
- Chỉ tạo rule tuỳ chỉnh với `isStandard: 0`.
- Mỗi Object có tối đa 50 rules; tên duy nhất trong Object và tối đa 100 ký tự.

## Filter chọn records

Chỉ dùng cho `type: 2`:

```json
{
  "logicType": "AND",
  "logic": "",
  "conditions": [
    {
      "field": "gross_profit_amount",
      "op": ">",
      "params": 10
    }
  ]
}
```

- `field` là field slug, không phải field ID.
- `logicType` thường là `AND` hoặc `OR`.
- Dùng `logic`, ví dụ `1 AND (2 OR 3)`, khi cần biểu thức nâng cao.
- `params` có thể là một giá trị, mảng hoặc `null` theo operator.
- Operator thường gặp: `=`, `!=`, `>`, `>=`, `<`, `<=`, `in`, `not in`, `is null`, `not null`; xác minh theo field type.
- Dùng `conditions: []` khi rule không giới hạn theo field cụ thể nhưng vẫn cần object `filter`.

Để chọn một record cụ thể, resolve field định danh ổn định và operator được field đó hỗ trợ. Không tự giả định `id` hoặc một slug nghiệp vụ có thể dùng nếu chưa kiểm tra Object metadata/API.

## Personnel filters chọn người dùng

Nhiều phần tử hợp nhất các nhóm người dùng được chọn.

| `type` | Chọn theo | Trường cần có | `op` |
|---:|---|---|---|
| `1` | User/personnel cụ thể | `personnelId`, trừ `all`; `include` với `null` dùng cho rule giữ chỗ không chọn ai | `all`, `include`, `exclude` |
| `2` | Vị trí trong phòng ban | `departmentId`; thêm `positionId` cho `include` | `all`, `include` |
| `3` | Vị trí trong phòng ban và cấp dưới | `departmentId`; thêm `positionId` cho `include` | `all`, `include` |
| `4` | Role | `roleId`, trừ `all` | `all`, `include`, `exclude` |
| `5` | Vị trí toàn tổ chức | `positionId`, trừ `all` | `all`, `include`, `exclude` |
| `6` | Personnel từ field lookup trên record | `fieldId` | `include` |
| `7` | Cùng phòng ban với personnel lookup + vị trí | `fieldId`, `positionId` | `include` |
| `8` | Phòng ban cha của personnel lookup + vị trí | `fieldId`, `positionId` | `include` |
| `9` | Phòng ban từ department lookup + vị trí | `fieldId`, `positionId` | `include` |
| `10` | Phòng ban cha của department lookup + vị trí | `fieldId`, `positionId` | `include` |

Ví dụ chọn một user cụ thể:

```json
[
  {
    "type": 1,
    "op": "include",
    "personnelId": "PER00000000004"
  }
]
```

Ví dụ áp dụng theo Role:

```json
[
  {
    "type": 4,
    "op": "include",
    "roleId": "RO00000000002"
  }
]
```

### Rule giữ chỗ không chọn nhân sự

Dùng `personnelFilters: [{"type": 1, "op": "include", "personnelId": null}]` khi cần giữ slot của action chưa cấp cho người dùng hoặc chặn CRUD trực tiếp trên Object do backend quản lý. Đây là giá trị `null` có chủ đích, không phải thiếu ID cần resolve; không dùng chuỗi `"null"`, ID giả, `op: "all"` hay mảng rỗng thay thế.

- Audience trên không khớp nhân sự nào, kể cả Super Admin; không thêm phần tử khác vào `personnelFilters` của rule giữ chỗ vì các audience được hợp nhất.
- Đặt `status: 1`. Chỉ cần một rule active là Object chuyển sang mặc định từ chối, dù rule đó không chọn nhân sự nào. Rule inactive chỉ giữ cấu hình, không kích hoạt hoặc duy trì chế độ này.
- Rule giữ chỗ không cấp quyền cho ai và không ghi đè quyền do active rule khác cấp. Để chặn một action, phải bảo đảm không có active rule nào khác cấp action đó cho audience cần chặn. Khi cả bốn action chỉ dành cho backend, dùng bốn rule giữ chỗ riêng.
- Nếu không còn rule active, lớp bảo mật chi tiết không hạn chế record/field; các quyền qua Role lại áp dụng trên toàn bộ dữ liệu. Điều này không tự cấp đủ CRUD cho user thiếu quyền Role.
- Rule vẫn phải có scope hợp lệ cho action. Không dùng `create: none` vì scope Create không hỗ trợ `none`. `type` trong personnel filter luôn là `1` cho mẫu này, còn `type` của rule phụ thuộc action.

| Slot action | `type` của rule | `scopes` | `filter` |
|---|---|---|---|
| Create | `1` | `create: all` | Không dùng |
| View | `2` | `read: all`, `edit: none`, `delete: no` | `{"logicType":"AND","logic":"","conditions":[]}` |
| Edit | `2` | `read: none`, `edit: all`, `delete: no` | Như View |
| Delete | `2` | `read: none`, `edit: none`, `delete: yes` | Như View |

Các giá trị `all`/`yes` trên chỉ xác định scope của slot; audience rỗng về mặt người dùng khiến rule không cấp quyền thực tế. Khi chuyển slot thành rule cấp quyền, phải xét lại audience, record filter và field scope theo nghiệp vụ, không chỉ thay `null` một cách máy móc.

Ví dụ payload hoàn chỉnh giữ chỗ Create cho Object “Lượt khuyến mãi đã sử dụng”:

```json
{
  "data": [
    {
      "objectTypeId": "{OBJECT_ID}",
      "isStandard": 0,
      "name": "[App] - Create Promotion Usage - Placeholder",
      "description": "Reserves the create slot for backend-managed promotion usage. Matches no personnel and keeps detailed security active. Grants no direct user access and does not override other rules.",
      "status": 1,
      "personnelFilters": [
        {"type": 1, "op": "include", "personnelId": null}
      ],
      "scopes": [
        {"scope": "create", "op": "all"}
      ],
      "type": 1
    }
  ]
}
```

Với ví dụ cho phép người dùng xem lượt khuyến mãi đã sử dụng, tạo View rule có audience/filter/field scope được phép, còn Create/Edit/Delete là ba rules giữ chỗ active theo bảng. Kiểm tra toàn bộ rules để phát hiện quyền cộng dồn ngoài ý muốn. Sau create/update, đọc lại detail từng rule để xác minh JSON `null`, `status` và scope còn đúng; không coi HTTP thành công là bằng chứng quyền runtime. Đường backend thực hiện nghiệp vụ cần danh tính hệ thống và policy phù hợp theo `$cogover-custom-module`, không tự được cấp quyền từ rule giữ chỗ.

### Semantics của Role `exclude` khi user có nhiều Role

Với personnel filter theo Role (`type: 4`, `op: "exclude"`), không hiểu câu “Tất cả vai trò, ngoại trừ Role A” là “loại mọi user có chứa Role A”. Runtime hiện tại duyệt từng Role được gán cho user và coi user khớp rule ngay khi tìm thấy ít nhất một Role không nằm trong danh sách Role bị loại trừ.

Gọi:

- `U` là tập Role của user;
- `E` là tập `roleId` trong các personnel filter `type: 4`, `op: "exclude"` của rule.

Điều kiện khớp là:

```text
matched = tồn tại role thuộc U nhưng không thuộc E
        = (U - E) không rỗng
```

Ví dụ khi `E = {Role A}`:

| Role của user (`U`) | Kết quả | Giải thích |
|---|---|---|
| `{Role A}` | Không khớp | Role duy nhất nằm trong danh sách loại trừ. |
| `{Role B}` | Khớp | Role B không bị loại trừ. |
| `{Role A, Role B}` | **Khớp** | Role A bị loại trừ nhưng Role B vẫn làm user khớp rule. |
| `{}` | Không khớp | Không có Role không bị loại trừ để làm điều kiện đúng. |

Ví dụ khi `E = {Role A, Role C}`:

| Role của user (`U`) | Kết quả |
|---|---|
| `{Role A, Role C}` | Không khớp |
| `{Role A, Role B}` | **Khớp**, vì Role B không thuộc `E` |

Payload minh hoạ loại trừ Role A:

```json
[
  {
    "type": 4,
    "op": "exclude",
    "roleId": "ROLE_A_ID"
  }
]
```

Do đó, nếu mục tiêu nghiệp vụ là chặn mọi user chỉ cần **có chứa** Role A, không được suy ra rằng payload trên đã thực hiện mục tiêu đó. Hãy ghi rõ hai tập persona khi kiểm thử: user chỉ có Role A và user đồng thời có Role A + một Role khác. Khi phân tích bug hoặc yêu cầu thay đổi hành vi, tách rõ “semantics runtime hiện tại” ở trên khỏi expected behavior được mô tả trong ticket hoặc câu chữ trên UI.

`exclude` ở đây chỉ quyết định user có thuộc audience của chính rule này hay không. Nó không thu hồi quyền do một active rule khác cũng khớp user/record cấp, và cũng không thay thế cổng permission ở mức Object của Role.

Không mặc định Users API `data.id` là `personnelId`. Kiểm tra quan hệ trong chi tiết user; nếu không có, tra Object Personnel theo email/tài khoản và xác minh chính xác trước khi dùng record ID. `personnelId` top-level trong một API response thường biểu thị người gọi request, không phải user mục tiêu. Với type `6`–`10`, field phải thuộc Object được bảo vệ và lookup đúng Object Personnel/Department.

## Scopes cấp quyền và field

| `scope` | Ý nghĩa | `op` |
|---|---|---|
| `create` | Field được nhập khi tạo | `all`, `include`, `exclude` |
| `read` | Field được xem | `all`, `include`, `exclude`, `none` |
| `edit` | Field được sửa | `all`, `include`, `exclude`, `none` |
| `delete` | Có được xoá record | `yes`, `no` |

Với `include` hoặc `exclude`, gửi một phần tử cho mỗi `fieldId` và dùng cùng `op` trong một scope:

```json
[
  {
    "scope": "edit",
    "op": "include",
    "fieldId": "OF00000000025"
  },
  {
    "scope": "edit",
    "op": "include",
    "fieldId": "OF00000000026"
  }
]
```

- Không gửi `fieldId` cho `all`, `none`, `yes` hoặc `no`.
- `type: 1` chỉ chứa scope `create`.
- `type: 2` phải chứa đủ `read`, `edit`, `delete`; dùng `none`/`no` nếu không cấp.
- Với rule `type: 2` chỉ phục vụ Delete, dùng `read: none`, `edit: none`, `delete: yes`; không thêm quyền đọc/sửa chỉ để tạo slot Delete. View/Edit phải có field scope hợp lệ cho action tương ứng.
- Không đưa field tính toán vào `create` hoặc `edit`.

## Tạo rule type 1

```json
{
  "data": [
    {
      "objectTypeId": "OT00000000009",
      "isStandard": 0,
      "name": "Tạo đơn hàng trong phòng Kinh doanh",
      "description": "Quản lý Kinh doanh được tạo đơn hàng",
      "status": 1,
      "scopes": [
        {
          "scope": "create",
          "op": "all"
        }
      ],
      "personnelFilters": [
        {
          "departmentId": "DEP00000000002",
          "positionId": "POS00000000004",
          "op": "include",
          "type": 3
        }
      ],
      "type": 1
    }
  ]
}
```

## Tạo rule type 2

```json
{
  "data": [
    {
      "objectTypeId": "OT00000000009",
      "isStandard": 0,
      "name": "Quyền truy cập đơn hàng giá trị cao",
      "description": "Cho phép người dùng được chọn xử lý đơn hàng giá trị cao",
      "filter": {
        "logicType": "AND",
        "logic": "",
        "conditions": [
          {
            "field": "gross_profit_amount",
            "op": ">",
            "params": 10
          }
        ]
      },
      "status": 1,
      "scopes": [
        {
          "scope": "read",
          "op": "all"
        },
        {
          "scope": "edit",
          "op": "include",
          "fieldId": "OF00000000025"
        },
        {
          "scope": "delete",
          "op": "no"
        }
      ],
      "personnelFilters": [
        {
          "op": "all",
          "type": 1
        }
      ],
      "type": 2
    }
  ]
}
```

Create và delete dùng top-level `data` array và hỗ trợ batch. Nếu một phần tử lỗi, toàn request trả lỗi; đọc lại trạng thái trước khi thử lại.

## Danh sách và chi tiết

```json
{
  "objectTypeId": "OT00000000009",
  "withDetails": true,
  "order": "updated",
  "sort": "desc"
}
```

- Có thể dùng `objectSlug` thay cho `objectTypeId`.
- Bỏ `status` để audit toàn bộ cấu hình, sau đó kiểm tra có ít nhất một rule `status: 1` hay không. Chỉ rule active mới kích hoạt lớp bảo mật và đóng góp quyền; Object chỉ còn rule inactive được xử lý như không có rule active.
- `withDetails: false` trả `filter: null` và mảng chi tiết rỗng; dùng `true` khi cần audit.
- Endpoint chưa phân trang.

Chi tiết:

```json
{
  "id": "OSKDELQESKMSD"
}
```

Response chi tiết dùng array; đọc rule ở `data[0]`. Không tìm thấy vẫn có thể trả thành công với `data: []`.

## Cập nhật

Endpoint nhận đúng một object trong `data`:

```json
{
  "data": [
    {
      "name": "Tên mới",
      "description": "Mô tả mới",
      "status": 1,
      "filter": {
        "logicType": "AND",
        "logic": "",
        "conditions": []
      },
      "personnelFilters": [],
      "scopes": []
    }
  ]
}
```

- `name`, `description`, `status` là partial update.
- Không gửi `objectTypeId`, `type`, `isStandard`; endpoint không đổi các field này.
- Bỏ `filter`, `personnelFilters` hoặc `scopes` để giữ nguyên phần tương ứng.
- Nếu gửi `personnelFilters` hoặc `scopes`, array là toàn bộ trạng thái đích; phần tử cũ không còn sẽ bị xoá.
- Không gửi mảng rỗng trừ khi chủ đích xoá toàn bộ cấu hình đó và đã đánh giá rule còn hợp lệ.
- Đọc chi tiết mới nhất trước update và đọc lại sau update.

## Vô hiệu hoá và xoá

Tạm dừng có thể khôi phục:

```json
{
  "data": [
    {
      "status": 0
    }
  ]
}
```

Xoá vĩnh viễn:

```json
{
  "data": [
    {
      "id": "OS00000000001"
    }
  ]
}
```

Ưu tiên `status: 0` nếu người dùng nói “tạm dừng”, “vô hiệu hoá” hoặc muốn khả năng khôi phục.

Trước khi tắt hoặc xoá rule active cuối cùng, cảnh báo rằng lớp bảo mật chi tiết sẽ bị tắt dù các rule inactive vẫn còn. Khi đó quyền cấp Object lại áp dụng trên toàn bộ records; với Super Admin, cổng quyền Role được coi là đã qua.

## Mã lỗi thường gặp

| `r` | Ý nghĩa |
|---:|---|
| `400` | Object ID thiếu/sai |
| `402` | Field lookup trong personnel filter thiếu/sai |
| `405` | Rule ID thiếu/sai |
| `406` | Filter record thiếu/sai |
| `407` | Tên rule sai hoặc trùng |
| `408` | Personnel filters sai |
| `409` | Scopes sai/thiếu |
| `410`–`412` | Operator hoặc tổ hợp scope sai |
| `413`–`415` | `status`, `isStandard` hoặc `type` sai |
| `424`–`425` | Personnel filter hoặc scope trùng |
| `428`–`430` | Thiếu personnel/department/position/role ID |
| `501` | Không tìm thấy rule |
| `504` | Không tìm thấy field |
| `506` | Không tìm thấy Object |
| `524` | Object đạt giới hạn 50 rules |
| `525`–`527` | Không tìm thấy personnel/department/position/role |
| `528` | Object không cho tạo custom security rule |

Luôn báo HTTP status, `r`, `msg` và `requestId`; không để lộ token.
