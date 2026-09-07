# App and Menu API contract

## Mục lục

- [Auth và response](#auth-và-response)
- [App endpoints](#app-endpoints)
- [App payload](#app-payload)
- [Menu Item endpoints](#menu-item-endpoints)
- [Tree và display endpoints](#tree-và-display-endpoints)
- [Array query](#array-query)

## Auth và response

Mọi endpoint là `/api/v1`, vì vậy phải tạo phiên bằng `$cogover-api-auth` và gửi:

```http
Cookie: HttpSessionId=...; XSRF-TOKEN=...; AuthToken=...
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
```

Success envelope thường là:

```json
{ "r": 0, "msg": "Successful", "data": {}, "meta": {}, "requestId": "..." }
```

Chỉ tiếp tục khi `r == 0`.

## App endpoints

| Method | Path | Mục đích | Encoding |
|---|---|---|---|
| GET | `/api/v1/apps` | List/filter App | Query |
| POST | `/api/v1/apps` | Create App | Multipart |
| GET | `/api/v1/apps/{appId}` | Detail App | — |
| POST | `/api/v1/apps/{appId}` | Update App | Multipart |
| PUT | `/api/v1/apps/changeStatus` | Active/inactive | JSON |
| DELETE | `/api/v1/apps/delete` | Delete App | Query |
| PUT | `/api/v1/apps/{appId}/menuSetting` | Menu display setting | JSON |

List query hỗ trợ `id`, `name`, `slug`, `status`, `type`, `createdBy`, `updatedBy`, `sort`, `order`, `page`, `limit` cùng các operator tương ứng. Array status/type được nối comma.

Đổi trạng thái:

```json
{ "ids": ["AP..."], "status": 0 }
```

`status`: `1` active, `0` inactive.

## App payload

Create/update dùng multipart fields:

| Field | Kiểu wire | Ghi chú |
|---|---|---|
| `name` | text | Bắt buộc, trim, tối đa 100 |
| `slug` | text | Bắt buộc, 2–100, bắt đầu bằng chữ, không `__`, không kết thúc `_` |
| `description` | text | Tối đa 255 |
| `logo` | file | Optional; png/jpeg/jpg/gif/svg, tối đa 5 MB |
| `accessControls` | JSON string | Array write shape |
| `newRecordUiAction` | `0`/`1` text | Boolean encoded number |
| `platform` | `1`/`2`/`3` text | All/Web/Mobile |

Ví dụ không kèm logo:

```text
name=Inventory
slug=inventory
description=Inventory operations
accessControls=[{"functions":["EXECUTE"],"option":1,"items":[],"type":"personnel"}]
newRecordUiAction=0
platform=1
```

ACL read response có field server-managed. Chỉ gửi write keys `functions`, `option`, `items`, `type`, và `sort` nếu backend hiện hành yêu cầu.

## Menu Item endpoints

Base: `/api/v1/apps/{appId}/menuItems`.

| Method | Suffix | Mục đích | Encoding |
|---|---|---|---|
| GET | `` | List items | Query |
| POST | `` | Create item | JSON |
| GET | `/{id}` | Detail item | — |
| PUT | `/{id}` | Update item | JSON |
| POST | `/updateStatus` | Active/inactive items | JSON |
| DELETE | `/deleteAll` | Delete items | Query |
| GET | `/treeMode` | Đọc cây | — |
| POST | `/sort` | Sort tree | JSON |
| POST | `/{id}/default` | Đặt item mặc định | Không body |
| GET | `/existsObject` | Object đã được dùng trong App | — |

Create/update JSON write shape:

```json
{
  "appId": "AP...",
  "name": "Products",
  "mobileName": "Products",
  "slug": "products",
  "description": "",
  "icon": "",
  "parentId": "",
  "actionType": 1,
  "actionContent": "product",
  "actionFilter": "all",
  "isDefault": false,
  "accessControls": [
    { "functions": ["EXECUTE"], "option": 1, "items": [], "type": "personnel" }
  ],
  "fillIconColor": 1,
  "platform": 1,
  "defaultOpen": 1,
  "showCount": 0
}
```

Update có thêm `id`. Giữ `icon: null` khi có chủ đích xoá icon; không loại `null` của `icon` như các field optional khác.

Đổi trạng thái:

```json
{ "appId": "AP...", "data": ["MI..."], "status": 0 }
```

## Tree và display endpoints

Sort:

```json
{
  "appId": "AP...",
  "data": [
    { "id": "MI_ROOT_1", "index": 0 },
    { "id": "MI_CHILD_1", "index": 0 },
    { "id": "MI_ROOT_2", "index": 1 }
  ]
}
```

Index được tính trong từng sibling group. Flatten toàn cây sau khi đánh lại index.

Menu setting update:

```json
{
  "id": "AP...",
  "showIconOptions": 1,
  "isCollapsed": 0,
  "showSearchBox": 1
}
```

- `showIconOptions`: `1` all icons, `2` level 1, `3` level 2.
- `isCollapsed`: `1` collapsed, `0` expanded.
- `showSearchBox`: `1` show, `0` hide.

## Array query

Serialize array query theo bracket notation:

```http
DELETE /api/v1/apps/delete?ids[]=AP1&ids[]=AP2
DELETE /api/v1/apps/AP1/menuItems/deleteAll?data[]=MI1&data[]=MI2
```

URL-encode bracket khi client yêu cầu (`ids%5B%5D`). Sau delete, list lại từng ID để xác minh.
