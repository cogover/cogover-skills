# App and Menu model

## App

| Field | Values |
|---|---|
| `type` | `1` standard, `2` custom |
| `status` | `1` active, `0` inactive |
| `platform` | `1` All, `2` Web, `3` Mobile (App và Menu Item) |
| `newRecordUiAction` | `1` enabled, `0` disabled |

Chỉ create/delete custom App. Standard App do hệ thống/marketplace quản lý; không mutate trừ khi người dùng yêu cầu rõ và contract cho phép.

## ACL write shape

```json
{ "functions": ["VIEW", "ADD", "EDIT", "DELETE", "EXECUTE"], "option": 1, "items": [], "type": "personnel" }
```

- `type`: `personnel`, `position`, `department`, `role`.
- `option = 1`: áp dụng tất cả trong type, `items` có thể rỗng; `option = 2`: áp dụng các ID trong `items`, không để rỗng.
- `functions` của App: `VIEW`, `ADD`, `EDIT`, `DELETE`, `EXECUTE`; có `EDIT` thì thêm `DELETE` để đúng contract quyền. Menu Item thường dùng `EXECUTE`.
- Không gửi ACL read fields: `id`, `workspaceId`, `tableName`, `rowId`, `functionsInt`, `functionsBinary`, timestamps, creator/updater.

## Menu action

| `actionType` | Ý nghĩa | Field liên quan |
|---:|---|---|
| `0` | Không điều hướng | `actionContent: ""` |
| `1` | Điều hướng đến Object | `actionContent` = object slug, `actionFilter` = filter slug/id |
| `2` | Điều hướng đến Workflow | `actionContent` = workflow/process ID, `actionTab` |
| `6` | Tạo Workflow run | `actionContent` = workflow/process ID |
| `34` | Điều hướng URL | `actionContent`, `actionUrlType`, `actionUrlOption` |

- `actionTab`: `0` cần chạy, `1` đang chạy, `2` theo dõi.
- `actionUrlType`: `3` inside workspace, `4` outside workspace, `5` outside with input params. URL trong workspace dùng path/query khi phù hợp; type `4` phải là URL tuyệt đối hợp lệ.
- `actionUrlOption`: `1` iframe, `2` redirect, `3` new tab, `4` new window.
- `showCount`: `1` hiển thị count, `0` ẩn; chỉ có ý nghĩa cho Object action, action khác đặt `0`.

### Route saved report trong App

Saved report có hai bề mặt URL. Menu Item phải dùng bề mặt runtime `/reports/{reportSlug}` (xem/chạy report trong Workspace); không dùng `/settings/reports/{reportSlug}` (quản trị cấu hình report). Write shape chuẩn:

```json
{ "actionType": 34, "actionContent": "/reports/projects_by_health", "actionUrlType": 3, "actionUrlOption": 2, "showCount": 0 }
```

Trước create/update batch, kiểm tra mọi item có `actionContent` chứa `/reports/`; từ chối item bắt đầu bằng `/settings/reports/`. Sau mutation, list/tree read-back phải trả exact `/reports/{reportSlug}`.

## Cây menu

- `parentId` rỗng hoặc `null` là root; parent phải thuộc cùng `appId`; tối đa 10 level; không đặt parent là chính item hoặc descendant của nó.
- `index` zero-based trong từng nhóm sibling. Khi đổi parent, đọc lại tree để lấy level/index backend đã chuẩn hoá.
- `defaultOpen`: `1` mở mặc định, `0` đóng. `fillIconColor`: chuẩn hoá thành number.

## Default item

Chỉ có một default item trong App. Không chọn làm default: item có children; item có URL action trỏ ra ngoài workspace và dùng redirect/new tab/new window; item inactive hoặc không thể execute với ACL hiện tại. Sau khi set default, đọc lại tree và xác minh đúng một node `isDefault` truthy.

## Validation

- Menu Item name: trim, 2–100 ký tự; mobile name optional, nếu có 2–100; slug bắt buộc, ít nhất 2, unique trong App; description tối đa 255.
- Object action: object tồn tại và chưa vi phạm rule `existsObject` của App. Workflow action: workflow/process ID tồn tại; `actionTab` hợp lệ khi cần.
