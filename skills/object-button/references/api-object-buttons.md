# Object Buttons API

API dùng để xem danh sách, xem chi tiết, tạo, cập nhật và xóa button của object, button trên danh sách, group button và button chain.

Tất cả tên trường trong request và response public đều sử dụng `camelCase`.

## Xác thực

Mọi request phải có header:

```http
Authorization: Bearer {tokenId}-{secretToken}
```

Với request có JSON body, gửi thêm:

```http
Content-Type: application/json
```

## Danh sách endpoint

| Thao tác | Method và endpoint |
|---|---|
| Xem danh sách button | `POST /bapi/v1/object-buttons/list` |
| Xem chi tiết button | `POST /bapi/v1/object-buttons/view` |
| Tạo button | `POST /bapi/v1/object-buttons` |
| Cập nhật button | `PUT /bapi/v1/object-buttons/{button_id}` |
| Xóa button | `POST /bapi/v1/object-buttons/delete` |

---

## 1. Xem danh sách Button

**Endpoint:** `POST /bapi/v1/object-buttons/list`

Endpoint public này dùng `POST` nhưng chỉ thực hiện thao tác đọc danh sách.

### Request Body

```json
{
  "page": 1,
  "limit": 20,
  "objectTypeSlug": "object_a",
  "actionType": "11,12,13,14",
  "actionTypeOperator": "IN",
  "getDetail": 1,
  "group": 1,
  "order": "updated",
  "sort": "desc"
}
```

### Tham số danh sách

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `page` | Integer | Không | Số trang. Mặc định: `1` |
| `limit` | Integer | Không | Số bản ghi tối đa trên một trang. Mặc định: `20` |
| `id` | String | Không | Lọc theo ID button |
| `idOperator` | String | Không | Toán tử của `id`, thường dùng `IN` hoặc `NOT_IN` |
| `name` | String | Không | Lọc theo tên button |
| `nameOperator` | String | Không | Toán tử của `name` |
| `slug` | String | Không | Lọc theo slug button |
| `slugOperator` | String | Không | Toán tử của `slug` |
| `actionType` | Integer/String | Không | Loại hành động hoặc chuỗi nhiều loại phân tách bằng dấu phẩy khi dùng `IN`/`NOT_IN` |
| `actionTypeOperator` | String | Không | Toán tử của `actionType`, thường dùng `IN` hoặc `NOT_IN` |
| `type` | Integer/String | Không | Loại button: `1` = standard, `2` = custom |
| `typeOperator` | String | Không | Toán tử của `type` |
| `status` | Integer/String | Không | Trạng thái: `0` = ngừng hoạt động, `1` = hoạt động |
| `statusOperator` | String | Không | Toán tử của `status` |
| `objectTypeId` | String | Không | Lọc theo ID object sở hữu button |
| `objectTypeIdOperator` | String | Không | Toán tử của `objectTypeId` |
| `objectTypeSlug` | String | Không | Lọc theo slug object sở hữu button |
| `objectTypeSlugOperator` | String | Không | Toán tử của `objectTypeSlug` |
| `sourceObjectId` | String | Không | Lọc theo source object ID |
| `sourceObjectIdOperator` | String | Không | Toán tử của `sourceObjectId` |
| `sourceObjectSlug` | String | Không | Lọc theo source object slug |
| `sourceObjectSlugOperator` | String | Không | Toán tử của `sourceObjectSlug` |
| `parentId` | String | Không | Lọc các button con của một group button |
| `parentIdOperator` | String | Không | Toán tử của `parentId` |
| `createdBy` | String | Không | Lọc theo personnel ID của người tạo |
| `updatedBy` | String | Không | Lọc theo personnel ID của người cập nhật cuối |
| `startCreatedAt` | Long/String | Không | Cận dưới của thời gian tạo, tính bằng mili giây |
| `endCreatedAt` | Long/String | Không | Cận trên của thời gian tạo, tính bằng mili giây |
| `startUpdatedAt` | Long/String | Không | Cận dưới của thời gian cập nhật, tính bằng mili giây |
| `endUpdatedAt` | Long/String | Không | Cận trên của thời gian cập nhật, tính bằng mili giây |
| `isBulk` | Integer | Không | Cờ hành động hàng loạt: `0` hoặc `1` |
| `isBulkOperator` | String | Không | Toán tử của `isBulk` |
| `filterFieldsNotIn` | String | Không | Danh sách trường lọc loại trừ phân tách bằng dấu phẩy do giao diện quản lý sử dụng; nên ưu tiên truyền operator cụ thể cho từng trường |
| `getDetail` | Integer/Boolean | Không | Dùng `1` để trả thêm `listSourceObject`, `autofill` và `actionChain` |
| `canBeChildButton` | Integer/Boolean | Không | Dùng `1` để loại group button (`actionType = 15`) khỏi kết quả |
| `group` | Integer/Boolean | Không | Dùng `1` để nạp `children` của group button |
| `translate` | Integer/Boolean | Không | Dùng `1` để trả về tên/tiêu đề đã dịch khi có dữ liệu dịch |
| `order` | String | Không | Trường sắp xếp, ví dụ `updated`, `created`, `name` hoặc `buttonIndex`. Mặc định: `updated` |
| `sort` | String | Không | Chiều sắp xếp: `asc` hoặc `desc`. Mặc định: `desc` |

Khi dùng `IN` hoặc `NOT_IN`, truyền các giá trị dưới dạng chuỗi phân tách bằng dấu phẩy. Ví dụ:

```json
{
  "actionType": "11,12,13,14",
  "actionTypeOperator": "IN"
}
```

### Ví dụ cURL

```bash
curl --location 'https://{workspace-domain}/bapi/v1/object-buttons/list' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "page": 1,
    "limit": 20,
    "objectTypeSlug": "object_a",
    "getDetail": 1,
    "group": 1,
    "order": "updated",
    "sort": "desc"
  }'
```

### Response thành công (200)

```json
{
  "r": 0,
  "msg": "Successful",
  "data": [
    {
      "id": "BU00000000002",
      "name": "Test button 1",
      "slug": "test_button_1",
      "workspaceId": "WSkClIFqhHsvg",
      "actionType": 11,
      "type": 2,
      "title": null,
      "tooltip": null,
      "objectTypeId": "OT00000000020",
      "objectTypeSlug": "object_a",
      "sourceObjectId": null,
      "sourceObjectSlug": null,
      "targetObjectTypeId": "OT00000000010",
      "targetObjectTypeSlug": "accounts_receivable",
      "isTargetCurrentRecord": 0,
      "layoutSourceObject": "LO00000000008",
      "popupDisplayType": 1,
      "useIcon": false,
      "iconOnly": false,
      "icon": null,
      "iconDarkMode": null,
      "children": [],
      "filterIds": [],
      "status": 1,
      "isBulk": 0,
      "listSourceObject": ["$currentRecord"],
      "created": "1785143339751",
      "updated": "1785143339751"
    }
  ],
  "meta": {
    "total": 1,
    "limit": 20,
    "currentPage": 1
  },
  "requestId": "d7a2281c-000206567-00000000-0000-4000-8000-000000000428"
}
```

`listSourceObject`, `autofill` và `actionChain` là các trường chi tiết theo từng action. Truyền `getDetail: 1` khi cần các trường này trong response danh sách.

---

## 2. Xem chi tiết Button

**Endpoint:** `POST /bapi/v1/object-buttons/view`

### Request Body

```json
{
  "id": "BU_CHAIN_1",
  "group": 1
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `id` | String | Có | ID button |
| `group` | Integer/Boolean | Không | Dùng `1` để trả thêm button con khi xem group button |

### Ví dụ cURL

```bash
curl --location 'https://{workspace-domain}/bapi/v1/object-buttons/view' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "id": "BU_CHAIN_1",
    "group": 1
  }'
```

### Response thành công (200)

```json
{
  "r": 0,
  "msg": "Successful",
  "data": {
    "id": "BU_CHAIN_1",
    "name": "Create and update receivable",
    "slug": "create_and_update_receivable",
    "workspaceId": "WSkClIFqhHsvg",
    "actionType": 14,
    "type": 2,
    "title": "Action result",
    "tooltip": "Run two actions in sequence",
    "objectTypeId": "OT00000000020",
    "objectTypeSlug": "object_a",
    "modalWidth": 800,
    "modalWidthUnit": "px",
    "actionChain": [
      {
        "id": "BC_ACTION_1",
        "actionButtonId": "BU_CREATE_1",
        "buttonIndex": 0,
        "allowSkip": 0,
        "isBackground": 0,
        "inputs": [
          {
            "isCurrentRecord": 1,
            "sourceButtonIndex": -1
          }
        ]
      },
      {
        "id": "BC_ACTION_2",
        "actionButtonId": "BU_UPDATE_1",
        "buttonIndex": 1,
        "allowSkip": 0,
        "isBackground": 0,
        "inputs": [
          {
            "isCurrentRecord": 0,
            "sourceButtonIndex": 0
          }
        ]
      }
    ],
    "children": [],
    "status": 1,
    "created": "1785143339751",
    "updated": "1785143339751"
  },
  "requestId": "d7a2281c-000206567-00000000-0000-4000-8000-000000000428"
}
```

Các object trong `actionChain` thực tế có thể chứa thêm ID được sinh tự động, workspace ID và các trường audit.

---

## 3. Tạo Button

**Endpoint:** `POST /bapi/v1/object-buttons`

### Các trường request dùng chung

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `name` | String | Có | Tên button, tối đa 100 ký tự |
| `slug` | String | Có | Tối đa 100 ký tự; chỉ chấp nhận chữ cái, chữ số và dấu gạch dưới |
| `actionType` | Integer | Có | Loại hành động. Xem [Các loại action](#các-loại-action) |
| `status` | Integer | Có | `0` = ngừng hoạt động, `1` = hoạt động |
| `objectTypeSlug` | String | Có | Slug của object sở hữu button |
| `title` | String/null | Không | Tiêu đề popup/kết quả, tối đa 255 ký tự; giao diện quản lý yêu cầu trường này với button chain |
| `tooltip` | String/null | Không | Tooltip, tối đa 255 ký tự |
| `sourceObjectSlug` | String/null | Theo action | Slug object nguồn |
| `targetObjectTypeSlug` | String/null | Theo action | Slug object đích, `$currentRecord` hoặc tham chiếu `$currentRecord.<field>` được hỗ trợ |
| `listSourceObject` | Array[String] | Theo action | Danh sách object nguồn có thứ tự. Dùng `"$currentRecord"` cho bản ghi hiện tại |
| `popupDisplayType` | Integer/null | Theo action | Kiểu popup/hiển thị. Xem [Các kiểu hiển thị](#các-kiểu-hiển-thị) |
| `layoutSourceObject` | String/null | Theo action | Layout ID dùng cho create, update, duplicate, list hoặc export theo layout |
| `createLayoutSourceObject` | String/null | Theo action | Create layout ID cho action create-or-update |
| `updateLayoutSourceObject` | String/null | Theo action | Update layout ID cho action create-or-update |
| `popupMessage` | String/null | Theo action | Nội dung xác nhận cho action xóa bản ghi |
| `fileDownloadType` | Integer/null | Theo action | Kiểu export: `0` = layout, `1` = document template |
| `documentTemplate` | String/null | Theo action | Định danh/nội dung template khi `fileDownloadType = 1` |
| `autofillFields` | Array | Theo action | Cấu hình autofill create-record kiểu basic/legacy (`actionType = 4`) |
| `autofill` | Object | Theo action | Cấu hình autofill cho create/update/list dạng configurable |
| `actionChain` | Array | Theo action | Danh sách action có thứ tự cho `actionType = 14` |
| `children` | Array[String] | Theo action | ID các button con cho `actionType = 15` |
| `filterIds` | Array[String]/null | Không | Các filter mà list button sẽ hiển thị trên đó |
| `buttonIndex` | Integer/null | Không | Thứ tự hiển thị, chủ yếu dùng cho list button |
| `useIcon` | Boolean/Integer | Không | Button có dùng icon hay không |
| `iconOnly` | Boolean/Integer | Không | Chỉ hiển thị icon hay không |
| `icon` | String/null | Không | Định danh icon ở light mode |
| `iconDarkMode` | String/null | Không | Định danh icon ở dark mode |
| `isBackground` | Boolean/Integer | Không | Chạy nền với action có hỗ trợ |
| `modalWidth` | Integer/null | Không | Chiều rộng modal tùy chỉnh |
| `modalWidthUnit` | String/null | Không | Giao diện quản lý hỗ trợ `px` và `%` |
| `showRecordAfterAction` | Integer/Boolean | Không | `1` để hiển thị các bản ghi chịu tác động sau khi chạy action |
| `showRecordAfterActionConfig` | Object/null | Không | Cấu hình hiển thị bản ghi kết quả |
| `parentId` | String/null | Không | ID group button cha |
| `isBulk` | Integer/Boolean | Không | Cờ hành động hàng loạt; mặc định: `0` |
| `metadata` | Object/null | Theo action | Cấu hình cho export-merge-PDF hoặc call-API |

Server tự sinh `id`, `workspaceId`, `objectTypeId`, các trường audit và `type`. Button được tạo qua endpoint này là custom button (`type = 2`).

`slug` phải là duy nhất trong object sở hữu button của workspace.

### Ví dụ: Tạo Configurable Create-Record Button

```bash
curl --location 'https://{workspace-domain}/bapi/v1/object-buttons' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "name": "Test button 1",
    "slug": "test_button_1",
    "status": 1,
    "actionType": 11,
    "objectTypeSlug": "object_a",
    "targetObjectTypeSlug": "accounts_receivable",
    "listSourceObject": ["$currentRecord"],
    "layoutSourceObject": "LO00000000008",
    "popupDisplayType": 1,
    "isBackground": 0,
    "showRecordAfterAction": 0,
    "autofill": {
      "targetCreate": [],
      "source": [],
      "syncRelatedList": [],
      "autofillRelatedList": []
    },
    "useIcon": false,
    "iconOnly": false,
    "icon": null,
    "iconDarkMode": null
  }'
```

### Response thành công (201)

```json
{
  "r": 0,
  "msg": "Successful",
  "data": {
    "id": "BU00000000002",
    "name": "Test button 1",
    "slug": "test_button_1",
    "workspaceId": "WSkClIFqhHsvg",
    "actionType": 11,
    "type": 2,
    "objectTypeId": "OT00000000020",
    "objectTypeSlug": "object_a",
    "targetObjectTypeId": "OT00000000010",
    "targetObjectTypeSlug": "accounts_receivable",
    "layoutSourceObject": "LO00000000008",
    "popupDisplayType": 1,
    "children": [],
    "status": 1,
    "created": "1785143339751",
    "updated": "1785143339751"
  },
  "requestId": "d7a2281c-000206567-00000000-0000-4000-8000-000000000428"
}
```

> **Lưu ý:** Response của thao tác tạo là resource rút gọn và có thể chưa chứa dữ liệu quan hệ đã lưu như `listSourceObject`, `autofill`, `actionChain`, `filterIds` hoặc `children` đã được nạp. Gọi `POST /bapi/v1/object-buttons/view` với ID vừa tạo để lấy trạng thái đầy đủ.

### Ví dụ: Tạo Button Chain

Các action button được tham chiếu phải tồn tại trước. Để tương thích với hành vi của giao diện quản lý, nên dùng configurable create/update action (`actionType` `11`, `12` hoặc `13`) làm các bước trong chain.

```bash
curl --location 'https://{workspace-domain}/bapi/v1/object-buttons' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "name": "Create and update receivable",
    "slug": "create_and_update_receivable",
    "actionType": 14,
    "status": 1,
    "objectTypeSlug": "object_a",
    "title": "Action result",
    "tooltip": "Run two actions in sequence",
    "modalWidth": 800,
    "modalWidthUnit": "px",
    "actionChain": [
      {
        "actionButtonId": "BU_CREATE_1",
        "allowSkip": 0,
        "isBackground": 0,
        "inputs": [
          {
            "isCurrentRecord": 1,
            "sourceButtonIndex": -1
          }
        ]
      },
      {
        "actionButtonId": "BU_UPDATE_1",
        "stopWhenCreate": "BU_CREATE_1",
        "allowSkip": 0,
        "isBackground": 0,
        "inputs": [
          {
            "isCurrentRecord": 0,
            "sourceButtonIndex": 0
          }
        ]
      }
    ],
    "showRecordAfterAction": 1,
    "showRecordAfterActionConfig": {
      "title": "Created and updated records",
      "displayFields": [
        {
          "actionIndex": 0,
          "enabled": true,
          "fields": ["name", "status"],
          "avatarFieldSlug": null
        },
        {
          "actionIndex": 1,
          "enabled": true,
          "fields": ["name", "amount"],
          "avatarFieldSlug": null
        }
      ]
    }
  }'
```

---

## 4. Cập nhật Button

**Endpoint:** `PUT /bapi/v1/object-buttons/{button_id}`

### Path Parameters

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `button_id` | String | Có | ID button cần cập nhật |

Request update chấp nhận các trường dùng chung có thể sửa và các trường theo từng action được mô tả trong tài liệu này. Các trường sau không thể sửa qua endpoint này:

- `slug`
- `objectTypeSlug`
- `type`
- ID được sinh tự động, thông tin workspace và các trường audit

Không thể cập nhật standard button (`type = 1`).

### Cách cập nhật cấu hình lồng nhau

Hãy coi các mảng/object sau là cấu hình đầy đủ thay vì bản vá từng phần:

- `autofill`
- `autofillFields`
- `actionChain`
- `children`
- `filterIds`

Khi sửa button dùng một trong các cấu trúc này, hãy gửi toàn bộ giá trị hiện tại kèm phần thay đổi. Cách này tránh dữ liệu quan hệ bị xóa hoặc giữ ở trạng thái không đồng nhất do trường bị bỏ qua.

### Ví dụ cURL: Cập nhật Button Chain

```bash
curl --location --request PUT 'https://{workspace-domain}/bapi/v1/object-buttons/BU_CHAIN_1' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "name": "Create and update receivable - v2",
    "actionType": 14,
    "status": 1,
    "title": "Updated action result",
    "actionChain": [
      {
        "actionButtonId": "BU_CREATE_1",
        "allowSkip": 0,
        "isBackground": 0,
        "inputs": [
          {
            "isCurrentRecord": 1,
            "sourceButtonIndex": -1
          }
        ]
      },
      {
        "actionButtonId": "BU_UPDATE_1",
        "allowSkip": 1,
        "isBackground": 0,
        "inputs": [
          {
            "isCurrentRecord": 0,
            "sourceButtonIndex": 0
          }
        ]
      }
    ]
  }'
```

### Response thành công (200)

```json
{
  "r": 0,
  "msg": "Successful",
  "data": 1,
  "requestId": "d7a2281c-000206567-00000000-0000-4000-8000-000000000428"
}
```

`data` là số bản ghi đã cập nhật và thông thường bằng `1` khi cập nhật thành công. Response update không chứa Button Resource đã cập nhật. Hãy gọi endpoint chi tiết sau khi cập nhật để lấy trạng thái chuẩn đầy đủ, bao gồm `autofill`, `actionChain`, `children` và các dữ liệu quan hệ khác.

---

## 5. Xóa Button

**Endpoint:** `POST /bapi/v1/object-buttons/delete`

### Request Body

```json
{
  "ids": ["BU00000000002", "BU_CHAIN_1"]
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `ids` | Array[String] | Có | Danh sách ID button cần xóa |

### Ví dụ cURL

```bash
curl --location 'https://{workspace-domain}/bapi/v1/object-buttons/delete' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{
    "ids": ["BU00000000002", "BU_CHAIN_1"]
  }'
```

### Response thành công (200)

```json
{
  "r": 0,
  "msg": "Success",
  "data": 2,
  "requestId": "d7a2281c-000206567-00000000-0000-4000-8000-000000000428"
}
```

Kết quả xóa trong `data` phụ thuộc implementation và không được đảm bảo bằng số ID đã gửi.

Không thể xóa standard button (`type = 1`). Nếu request chứa standard button, toàn bộ thao tác xóa bị từ chối. Nếu không có ID nào tồn tại trong workspace hiện tại, API trả lỗi not-found.

Nếu có ít nhất một custom-button ID tồn tại, backend hiện sẽ xóa các button khớp ngay cả khi một số ID khác trong request không tồn tại. Client cần kiểm tra tất cả ID theo nguyên tắc all-or-nothing nên xác minh trước bằng API list/detail.

---

## Các trường của Button Resource

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | String | ID button |
| `name` | String | Tên button |
| `slug` | String | Slug button |
| `workspaceId` | String | ID workspace |
| `actionType` | Integer | Loại hành động |
| `type` | Integer | `1` = standard, `2` = custom |
| `title` | String/null | Tiêu đề popup hoặc kết quả |
| `tooltip` | String/null | Nội dung tooltip |
| `objectTypeId` | String | ID object sở hữu button |
| `objectTypeSlug` | String | Slug object sở hữu button |
| `sourceObjectId` | String/null | ID object nguồn |
| `sourceObjectSlug` | String/null | Slug object nguồn |
| `targetObjectTypeId` | String/null | ID object đích |
| `targetObjectTypeSlug` | String/null | Slug object đích hoặc tham chiếu bản ghi hiện tại |
| `isTargetCurrentRecord` | Integer/Boolean/null | Cờ suy ra cho biết target có bắt đầu bằng `$currentRecord`; đây không phải input có tính quyết định |
| `layoutSourceObject` | String/null | Main layout ID |
| `createLayoutSourceObject` | String/null | Create layout ID cho create-or-update |
| `updateLayoutSourceObject` | String/null | Update layout ID cho create-or-update |
| `popupDisplayType` | Integer/null | Kiểu popup/hiển thị |
| `popupMessage` | String/null | Nội dung popup hoặc xác nhận xóa |
| `documentTemplate` | String/null | Document template dùng khi export |
| `fileDownloadType` | Integer/null | Kiểu export |
| `useIcon` | Boolean/Integer/null | Cờ sử dụng icon; response đọc có thể trả `0` hoặc `1` |
| `iconOnly` | Boolean/Integer/null | Cờ chỉ hiển thị icon; response đọc có thể trả `0` hoặc `1` |
| `icon` | String/null | Icon light mode |
| `iconDarkMode` | String/null | Icon dark mode |
| `isBackground` | Boolean/Integer/null | Cờ chạy nền |
| `modalWidth` | Integer/null | Chiều rộng modal |
| `modalWidthUnit` | String/null | Đơn vị chiều rộng modal |
| `showRecordAfterAction` | Integer/Boolean/null | Có hiển thị bản ghi chịu tác động sau khi chạy hay không |
| `showRecordAfterActionConfig` | Object/null | Cấu hình hiển thị bản ghi kết quả |
| `parentId` | String/null | ID group button cha |
| `children` | Array | Các button con; được nạp khi yêu cầu mở rộng group |
| `filterIds` | Array[String]/null | Các filter liên kết với list button |
| `buttonIndex` | Integer/null | Thứ tự hiển thị |
| `status` | Integer | `0` = ngừng hoạt động, `1` = hoạt động |
| `isBulk` | Integer/Boolean | Cờ hành động hàng loạt |
| `metadata` | Object/String/null | Metadata theo action; một số response có thể serialize thành JSON string |
| `listSourceObject` | Array[String]/null | Danh sách object nguồn có thứ tự; trả về cho action hỗ trợ khi đã nạp chi tiết |
| `autofillFields` | Array/null | Các trường autofill create-record basic/legacy |
| `autofill` | Object/null | Dữ liệu autofill configurable; trả về khi đã nạp chi tiết |
| `actionChain` | Array/null | Các bước trong chain; trả về cho button chain khi đã nạp chi tiết |
| `created` | Long/String | Timestamp tạo tính bằng mili giây |
| `updated` | Long/String | Timestamp cập nhật cuối tính bằng mili giây |
| `createdBy` | Object/String/null | Thông tin người tạo |
| `updatedBy` | Object/String/null | Thông tin người cập nhật cuối |

## Các loại Action

| Giá trị | Tên | Cấu hình chính |
|---:|---|---|
| `1` | Submit / Perform | Không có cấu hình bổ sung bắt buộc ở server |
| `2` | Reset | Không có cấu hình bổ sung bắt buộc ở server |
| `3` | Cancel | Không có cấu hình bổ sung bắt buộc ở server |
| `4` | Create record (basic/legacy) | `popupDisplayType`, `layoutSourceObject`; `autofillFields` không bắt buộc |
| `5` | Update record (basic/legacy) | `sourceObjectSlug`, `popupDisplayType`, `layoutSourceObject` |
| `6` | Duplicate record | `sourceObjectSlug`, `popupDisplayType`, `layoutSourceObject` |
| `7` | Delete record | `popupMessage` |
| `8` | Export | `sourceObjectSlug` và cấu hình layout hoặc template |
| `10` | Custom | Không có cấu hình bổ sung bắt buộc ở server |
| `11` | Configurable create record | `listSourceObject`; thông thường có `targetObjectTypeSlug`, layout/display và `autofill` |
| `12` | Configurable update record | `listSourceObject`; thông thường có target/layout/display và `autofill` |
| `13` | Create or update record | `listSourceObject`; thông thường có target, create/update layout và `autofill` |
| `14` | Action chain | `actionChain` có ít nhất một action |
| `15` | Group button | `children` có ít nhất một child button ID |
| `16` | Create record on list | `listSourceObject`; thường có layout/display, `filterIds`, `buttonIndex` và `autofill.targetCreate` |
| `17` | Connect to action chain/sequence | Không có cấu hình bổ sung bắt buộc ở server |
| `18` | Disconnect/delete from action chain/sequence | Không có cấu hình bổ sung bắt buộc ở server |
| `19` | Update record on list | `listSourceObject`; thường có layout/display, `filterIds`, `buttonIndex` và `autofill.source` |
| `20` | Export and merge PDF | `metadata.fileFieldSlug`; `metadata.identifierFieldSlug` không bắt buộc |
| `21` | Call API | Object `metadata` chứa cấu hình HTTP request |

`actionType = 9` không hợp lệ ở backend và không được gửi.

## Cấu trúc theo từng Action

### Các kiểu hiển thị

| Giá trị | Ý nghĩa |
|---:|---|
| `0` | Chuyển đến trang tạo; dùng cho create-on-list (`actionType = 16`) |
| `1` | Modal ở giữa |
| `2` | Modal bên trái |
| `3` | Modal bên phải |
| `4` | Modal toàn màn hình |

### Cấu hình Export (`actionType = 8`)

Export theo layout:

```json
{
  "actionType": 8,
  "sourceObjectSlug": "object_a",
  "fileDownloadType": 0,
  "layoutSourceObject": "LO_EXPORT_1"
}
```

Export theo template:

```json
{
  "actionType": 8,
  "sourceObjectSlug": "object_a",
  "fileDownloadType": 1,
  "documentTemplate": "DOCUMENT_TEMPLATE_1"
}
```

### Các trường Autofill Basic/Legacy (`actionType = 4`)

```json
{
  "autofillFields": [
    {
      "field": "name",
      "value": "Default name",
      "valueDataType": "short_text",
      "isVariable": 0
    }
  ]
}
```

`field`, `value` và `valueDataType` là string khi được truyền. `isVariable` nhận `0` hoặc `1`.

### Cấu trúc Autofill

`autofill` có thể chứa các mảng sau:

| Key | Mục đích |
|---|---|
| `targetCreate` | Các giá trị được gán khi tạo bản ghi đích |
| `targetUpdate` | Các giá trị được gán khi cập nhật bản ghi đích |
| `source` | Các giá trị đọc từ hoặc áp dụng vào bản ghi nguồn |
| `syncRelatedList` | Cấu hình đồng bộ related list |
| `autofillRelatedList` | Mapping trường để tạo/cập nhật bản ghi related list |

Ví dụ:

```json
{
  "autofill": {
    "targetCreate": [
      {
        "field": "status",
        "value": "{\"value\":\"pending\"}",
        "valueDataType": "single_choice",
        "isVariable": 0,
        "isOverwrite": 0,
        "overwriteType": 1,
        "allowEdit": 1
      }
    ],
    "source": [
      {
        "field": "customer",
        "value": "{\"value\":\"$currentRecord.customer\"}",
        "valueDataType": "lookup_normal",
        "isVariable": 1,
        "objectTypeSlug": "$currentRecord",
        "allowEdit": 0
      }
    ],
    "syncRelatedList": [
      {
        "sourceRelatedListId": "RL_SOURCE_1",
        "targetRelatedListId": "RL_TARGET_1",
        "isOverwrite": 1,
        "overwriteType": 1
      }
    ],
    "autofillRelatedList": [
      {
        "targetRelatedListId": "RL_TARGET_2",
        "sourceRelatedListId": "RL_SOURCE_2",
        "isOverwrite": 0,
        "overwriteType": 2,
        "fields": [
          {
            "field": "amount",
            "value": 1000,
            "valueDataType": "currency",
            "isVariable": 0,
            "isLoop": 0
          }
        ]
      }
    ]
  }
}
```

Với `targetCreate`, `targetUpdate` và `source`, giao diện quản lý serialize giá trị hằng/biến thành JSON string như `"{\"value\":\"pending\"}"`. Nên dùng định dạng này để tương thích với màn hình xem/sửa chi tiết.

Không suy ra `isVariable` chỉ từ việc `value` bắt đầu bằng `$`. Các mẫu thực tế cho thấy:

- Tham chiếu field như `$currentRecord.remaining_amount` dùng `isVariable: 1`.
- Tham chiếu toàn bản ghi như `$currentRecord` và input slot như `$input_2` có thể dùng `isVariable: 0`.
- Hằng số dùng `isVariable: 0`.

Khi dựng payload mới, lấy quy ước từ metadata và một button cùng kiểu đã được UI lưu; không chuẩn hóa mù quáng mọi token `$...` thành cùng một giá trị `isVariable`.

Các trường thường gặp của một autofill item:

| Trường | Kiểu | Mô tả |
|---|---|---|
| `field` | String/null | Slug trường của object |
| `value` | String/Any/null | Giá trị. Autofill thông thường cần JSON string; trường related-list có thể chứa giá trị thô |
| `objectTypeSlug` | String/null | Object nguồn của source-value mapping |
| `valueDataType` | String/null | Kiểu dữ liệu của trường |
| `isVariable` | Integer | `1` nếu `value` là tham chiếu biến, ngược lại là `0` |
| `isHidden` | Integer | Cờ ẩn trường |
| `allowEdit` | Integer | Có cho phép người dùng sửa giá trị hay không |
| `isOverwrite` | Integer/Boolean | Có cho phép ghi đè giá trị hiện tại hay không |
| `overwriteType` | Integer | `0` = không cho phép, `1` = thay thế, `2` = thêm mới |
| `isLoop` | Integer | Cờ lặp cho related list |

### Cấu trúc Action Chain (`actionType = 14`)

```json
{
  "actionChain": [
    {
      "actionButtonId": "BU_CREATE_1",
      "stopWhenCreate": null,
      "stopWhenUpdate": null,
      "allowSkip": 0,
      "isBackground": 0,
      "inputs": [
        {
          "isCurrentRecord": 1,
          "sourceButtonIndex": -1
        }
      ]
    }
  ]
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `actionButtonId` | String | Có | Button đã tồn tại được thực thi ở bước này |
| `stopWhenCreate` | String/null | Không | Action button trước đó có kết quả create làm điều kiện dừng bước này |
| `stopWhenUpdate` | String/null | Không | Action button trước đó có kết quả update làm điều kiện dừng bước này |
| `allowSkip` | Integer/Boolean | Không | Người dùng có được bỏ qua action này hay không |
| `isBackground` | Integer/Boolean | Không | Bước trong chain có chạy nền hay không |
| `inputs` | Array | Có | Các mapping nguồn input có thứ tự |
| `inputs[].isCurrentRecord` | Integer | Không | `1` nếu input đến từ bản ghi hiện tại |
| `inputs[].sourceButtonIndex` | Integer/null | Không | Index bắt đầu từ `0` của action trước đó; giao diện quản lý dùng `-1` để biểu diễn bản ghi hiện tại |

Action ID phải tồn tại. Bước đầu tiên do giao diện quản lý tạo dùng bản ghi hiện tại làm input; các bước sau có thể dùng output của action trước đó theo index bắt đầu từ `0`.

### Quan hệ giữa input của Chain và `$input_N`

Mỗi phần tử `inputs` cấp một input slot cho action con theo thứ tự. `sourceButtonIndex` xác định nguồn runtime của slot, còn `$input_N` trong autofill của action con đọc slot thứ `N` (đếm từ `1`). Vì vậy `$input_2` không tự động có nghĩa là output của chain step `2`.

Đối chiếu ba cấu hình cùng nhau:

1. `listSourceObject` của action con mô tả ý nghĩa các slot.
2. `inputs` của chain cấp bản ghi hiện tại hoặc output bước trước cho từng slot.
3. `$input_N` trong autofill đọc slot tương ứng.

Ví dụ:

```json
{
  "childAction": {
    "listSourceObject": ["$currentRecord", "account"],
    "autofill": {
      "targetCreate": [
        {
          "field": "account",
          "value": "{\"value\":\"$input_2\"}",
          "isVariable": 0
        }
      ]
    }
  },
  "chainStep": {
    "inputs": [
      {"isCurrentRecord": 1, "sourceButtonIndex": -1},
      {"isCurrentRecord": 0, "sourceButtonIndex": 0}
    ]
  }
}
```

Trong ví dụ này slot `2` là Account và được lấy từ output chain step `0`. Chỉ cấp output của bước đã đứng trước; nếu một bước nguồn có thể bị bỏ qua, phải xử lý rõ các bước phụ thuộc input đó.

Xem [business-use-cases.md](business-use-cases.md) và [example-convert-lead.json](example-convert-lead.json) để tham khảo chuỗi chuyển đổi Lead thực tế có nhiều input slot.

### Cấu trúc Group Button (`actionType = 15`)

```json
{
  "actionType": 15,
  "children": ["BU_CHILD_1", "BU_CHILD_2"]
}
```

Các child ID phải tồn tại trong workspace hiện tại. Không thể lồng một group button làm con của group button khác.

### Hiển thị bản ghi sau khi chạy Action

Giao diện quản lý cung cấp tính năng này cho các action type `11`, `12`, `13` và `14`.

```json
{
  "showRecordAfterAction": 1,
  "showRecordAfterActionConfig": {
    "title": "Processed records",
    "displayFields": [
      {
        "actionIndex": 0,
        "enabled": true,
        "fields": ["name", "status"],
        "avatarFieldSlug": "avatar"
      }
    ]
  }
}
```

`actionIndex` bắt đầu từ `0`. Với một action đơn, giá trị là `0`; với chain, trường này xác định bước tương ứng. Khi `enabled` là true, hãy cung cấp ít nhất một field slug.

### Metadata Export and Merge PDF (`actionType = 20`)

```json
{
  "metadata": {
    "fileFieldSlug": "generated_pdf",
    "identifierFieldSlug": "invoice_number"
  }
}
```

`fileFieldSlug` là bắt buộc. `identifierFieldSlug` không bắt buộc.

### Metadata Call API (`actionType = 21`)

```json
{
  "metadata": {
    "url": "https://example.com/customers/$record.customer_id",
    "method": "POST",
    "headers": [
      {
        "key": "Authorization",
        "value": "Bearer $record.api_token"
      }
    ],
    "body": "{\"recordId\":$record.id,\"name\":$record.name}",
    "reloadCurrentRecord": true
  }
}
```

Để tương thích với giao diện quản lý:

- `url` phải bắt đầu bằng `http://`, `https://` hoặc `/`.
- `method` phải là `GET`, `POST`, `PUT` hoặc `DELETE`.
- `GET` không sử dụng `body`.
- `body`, nếu có, là JSON string biểu diễn một object hoặc array.
- Header key chỉ dùng chữ cái, chữ số, dấu gạch ngang hoặc dấu gạch dưới.
- `$record.<fieldSlug>` và `$record["fieldSlug"]` là tham chiếu biến của bản ghi hiện tại được UI hỗ trợ.

## Quy ước Response và lỗi

Response có thể chứa `workspaceId`, `workspaceDomain` và `personnelId` để xác định workspace và người dùng của request.

| HTTP Status | Ý nghĩa |
|---:|---|
| `200` | Thao tác list, detail, update hoặc delete thành công |
| `201` | Tạo button thành công |
| `400` | Lỗi nghiệp vụ hoặc validation (`r != 0`) |
| `401` | Bearer token thiếu, sai, hết hạn hoặc không hoạt động |
| `429` | Vượt quá giới hạn tần suất request |
| `500` | Lỗi server không mong muốn |

Các lỗi nghiệp vụ thường gặp:

- Thiếu trường dùng chung hoặc trường bắt buộc theo action.
- Trùng `slug` trong cùng object.
- Object slug, layout ID, button ID, filter ID hoặc child ID không tồn tại.
- Action type, status, popup type hoặc export type không hợp lệ.
- Cố cập nhật hoặc xóa standard button.
- Button chain tham chiếu action button không tồn tại.
- Group chứa button con không hợp lệ hoặc chứa một group button khác.

Lỗi forward hoặc lỗi mạng trả về `r = 1` và chi tiết trong `msg`.

## Ghi chú

- ID, slug, object type, layout, filter và button được tham chiếu đều thuộc phạm vi workspace.
- Object Buttons API lưu định nghĩa hành động nhưng không tự đặt record-level button lên giao diện xem bản ghi. Sau khi tạo button không thuộc loại màn danh sách, dùng Layouts V2 API để thêm một entry vào `pageSettings.buttons.listButton` của layout xem/sửa cùng Object; giữ nguyên các entry hiện có và view lại layout để xác minh.
- Request tạo và cập nhật dùng tên trường `camelCase`.
- Dùng `targetObjectTypeSlug: "$currentRecord"` để trỏ đến bản ghi hiện tại. `isTargetCurrentRecord` được suy ra trong response đọc và không thay thế cho `targetObjectTypeSlug`.
- Tham chiếu `$currentRecord.<field>` được chấp nhận trong các luồng tham chiếu object có hỗ trợ.
- `listButton` chỉ là trường form của frontend. Khi gọi API tạo group button, hãy gửi `children`.
- Request tạo public luôn tạo custom button (`type = 2`). Không thể cập nhật hoặc xóa standard button qua API này.
- Gọi endpoint chi tiết sau khi tạo/cập nhật nếu cần dữ liệu quan hệ đầy đủ.
