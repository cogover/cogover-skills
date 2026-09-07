# App and Menu model

## Mục lục

- [App](#app)
- [ACL write shape](#acl-write-shape)
- [Menu action](#menu-action)
- [Cây menu](#cây-menu)
- [Default item](#default-item)
- [Validation](#validation)

## App

| Field | Values |
|---|---|
| `type` | `1` standard, `2` custom |
| `status` | `1` active, `0` inactive |
| `platform` | `1` All, `2` Web, `3` Mobile |
| `newRecordUiAction` | `1` enabled, `0` disabled |

Chỉ create/delete custom App. Standard App do hệ thống/marketplace quản lý; không mutate trừ khi user yêu cầu rõ và contract cho phép.

## ACL write shape

```json
{
  "functions": ["VIEW", "ADD", "EDIT", "DELETE", "EXECUTE"],
  "option": 1,
  "items": [],
  "type": "personnel"
}
```

Các `type` được hỗ trợ: `personnel`, `position`, `department`, `role`.

- `option = 1`: áp dụng tất cả trong type; `items` có thể rỗng.
- `option = 2`: áp dụng các ID trong `items`; không để rỗng.
- App permissions: `VIEW`, `ADD`, `EDIT`, `DELETE`, `EXECUTE`.
- Menu Item thường dùng `EXECUTE`.
- Thêm `DELETE` nếu App ACL có `EDIT` để giữ đúng contract quyền.

Không gửi ACL read fields như `id`, `workspaceId`, `tableName`, `rowId`, `functionsInt`, `functionsBinary`, timestamps, creator/updater.

## Menu action

| `actionType` | Ý nghĩa | Field liên quan |
|---:|---|---|
| `0` | Không điều hướng | `actionContent: ""` |
| `1` | Điều hướng đến Object | `actionContent = object slug`, `actionFilter = filter slug/id` |
| `2` | Điều hướng đến Workflow | `actionContent = workflow/process ID`, `actionTab` |
| `6` | Tạo Workflow run | `actionContent = workflow/process ID` |
| `34` | Điều hướng URL | `actionContent`, `actionUrlType`, `actionUrlOption` |

`actionTab`: `0` cần chạy, `1` đang chạy, `2` theo dõi.

URL type: `3` inside workspace, `4` outside workspace, `5` outside with input params.

URL option: `1` iframe, `2` redirect, `3` new tab, `4` new window.

Với action không phải Object, đặt `showCount: 0`. Với URL trong workspace, dùng path/query khi phù hợp; với external URL type `4`, validate URL tuyệt đối.

### Route saved report trong App

Saved report có hai bề mặt URL khác nhau; Menu Item trong custom App phải dùng bề mặt runtime:

| Mục đích | Route | Dùng cho App Menu |
|---|---|---|
| Xem/chạy report trong Workspace | `/reports/{reportSlug}` | Có |
| Quản trị cấu hình report | `/settings/reports/{reportSlug}` | Không |

Write shape chuẩn:

```json
{
  "actionType": 34,
  "actionContent": "/reports/projects_by_health",
  "actionUrlType": 3,
  "actionUrlOption": 2,
  "showCount": 0
}
```

Trước create/update batch, kiểm tra mọi item có `actionContent` chứa `/reports/`; từ chối bất kỳ item nào bắt đầu bằng `/settings/reports/`. Sau mutation, list/tree read-back phải trả exact runtime route `/reports/{reportSlug}`.

## Cây menu

- `parentId` rỗng hoặc `null` nghĩa là root.
- Parent phải thuộc cùng `appId`.
- Tối đa 10 level.
- Không đặt parent là chính item hoặc descendant của item.
- `index` là zero-based trong từng nhóm sibling.
- Khi đổi parent, đọc lại tree để lấy level/index backend đã chuẩn hoá.
- `defaultOpen`: `1` mở mặc định, `0` đóng.
- `fillIconColor`: chuẩn hoá thành number.
- `showCount`: `1` hiển thị count, `0` ẩn; chỉ có ý nghĩa cho Object action.
- `platform`: `1` All, `2` Web, `3` Mobile.

## Default item

Không chọn default item khi:

- Item có children.
- URL action trỏ ra ngoài workspace và dùng redirect/new tab/new window.
- Item inactive hoặc không thể execute với ACL hiện tại.

Chỉ có một default item trong App. Đọc lại tree sau khi set default và xác minh đúng một node `isDefault` truthy.

## Validation

- Name: trim, 2–100 ký tự cho Menu Item.
- Mobile name: optional, nếu có thì 2–100.
- Slug: bắt buộc, ít nhất 2; kiểm tra unique trong App.
- Description: tối đa 255.
- URL external: URL tuyệt đối hợp lệ.
- Object action: object tồn tại và chưa vi phạm rule `existsObject` của App.
- Workflow action: workflow/process ID tồn tại; `actionTab` hợp lệ khi cần.
- ACL selected (`option = 2`): `items` không rỗng.
