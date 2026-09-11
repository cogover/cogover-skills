# Ví dụ tên, description và payload security rule

Bổ sung cho mục "Đặt tên và mô tả security rule" trong `SKILL.md`; schema đầy đủ theo [api-object-security-rules.md](api-object-security-rules.md).

## Tên và description theo action

| Action | Ví dụ tên tiếng Anh | Nội dung description phải nêu |
|---|---|---|
| Create | `[Finance App] - Create Cash Transactions` | Audience, fields được nhập và việc rule không cấp quyền trên records đã tồn tại |
| View | `[Finance App] - View Eligible Cash Transactions` | Audience, record filter, fields được xem và không cấp edit/delete |
| Edit | `[Finance App] - Edit Draft Cash Transactions` | Audience, record filter, fields được sửa và không cấp read/delete trong rule này |
| Delete | `[Finance App] - Delete Draft or Cancelled Cash Transactions` | Audience, record filter được xoá và không cấp read/edit |
| Giữ chỗ | `[App] - Create Promotion Usage - Placeholder` | Không chọn nhân sự, giữ slot, duy trì mặc định từ chối, không ghi đè rule khác. Ví dụ: `Reserves the create slot for backend-managed promotion usage. Matches no personnel and keeps detailed security active. Grants no direct user access and does not override other rules.` |

## View rule chỉ cho xem mọi field của records phù hợp

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
    { "scope": "read", "op": "all" },
    { "scope": "edit", "op": "none" },
    { "scope": "delete", "op": "no" }
  ],
  "type": 2
}
```

## Mẫu rules thật của `cash_transaction`

[sample-cash-transaction-security-rules.json](sample-cash-transaction-security-rules.json) là snapshot đã ẩn danh cách tách rules của Object `cash_transaction`: năm rules gồm một Create, một View, một Delete và hai Edit rules (hai ý định sửa khác nhau). Dùng cấu trúc filter/personnel/scopes làm tham khảo; không sao chép các description rỗng trong cấu hình cũ.
