# Filters API Reference

Tài liệu tham chiếu cho API xem danh sách, xem chi tiết, tạo, cập nhật và xóa bộ lọc đã lưu của Cogover Object.

## Mục lục

- [Xác thực và response](#xác-thực-và-response)
- [Xem danh sách](#xem-danh-sách)
- [Xem chi tiết](#xem-chi-tiết)
- [Tạo bộ lọc](#tạo-bộ-lọc)
- [Cập nhật bộ lọc](#cập-nhật-bộ-lọc)
- [Xóa bộ lọc](#xóa-bộ-lọc)
- [Cấu trúc resource](#cấu-trúc-resource)
- [Conditions, sorting và access controls](#conditions-sorting-và-access-controls)
- [Validation và lỗi](#validation-và-lỗi)

## Xác thực và response

Mọi request yêu cầu:

```http
Authorization: Bearer {tokenId}-{secretToken}
Content-Type: application/json
```

Response thành công có `r: 0`. Các status thường gặp:

| HTTP | Ý nghĩa |
|---:|---|
| `200` | List, view, update hoặc delete thành công |
| `201` | Create thành công |
| `400` | Lỗi nghiệp vụ hoặc validation; kiểm tra `r` và `msg` |
| `401` | Bearer token thiếu, sai, hết hạn hoặc không hoạt động |
| `429` | Vượt giới hạn request; chờ rồi retry có giới hạn |
| `500` | Lỗi server; không tự động lặp request ghi nếu chưa xác định trạng thái |

Lỗi dịch vụ hoặc kết nối có thể trả `r: 1` và chi tiết trong `msg`. Response có thể chứa `workspaceId`, `workspaceDomain`, `personnelId` và `requestId` để truy vết.

## Xem danh sách

`POST /bapi/v1/filters/list`

```json
{
  "page": 1,
  "limit": 20,
  "objectTypeId": "OT00000000023",
  "objectTypeIdOperator": "IN",
  "order": "created",
  "sort": "desc"
}
```

| Trường | Bắt buộc | Mô tả |
|---|---|---|
| `page` | Không | Số trang, mặc định `1` |
| `limit` | Không | Số item mỗi trang, mặc định `20` |
| `objectTypeId` | Không | Giới hạn theo Object type ID |
| `objectTypeIdOperator` | Không | Dùng `IN` khi lọc theo `objectTypeId` |
| `order` | Không | Field sắp xếp resource, mặc định `created` |
| `sort` | Không | `asc` hoặc `desc`, mặc định `desc` |

```bash
curl --silent --location "https://${WORKSPACE_DOMAIN}/bapi/v1/filters/list" \
  --header "Authorization: Bearer ${API_KEY}" \
  --header 'Content-Type: application/json' \
  --data '{
    "page": 1,
    "limit": 20,
    "objectTypeId": "OT00000000023",
    "objectTypeIdOperator": "IN",
    "order": "created",
    "sort": "desc"
  }'
```

Response:

```json
{
  "r": 0,
  "msg": "Successful",
  "data": [
    {
      "id": "FI00000000001",
      "name": "Unassigned Leads",
      "slug": "unassigned_leads",
      "logicType": "AND",
      "logic": null,
      "conditions": [
        {
          "field": "owner",
          "op": "is null",
          "params": null,
          "fieldType": "lookup_normal"
        }
      ],
      "objectTypeId": "OT00000000023",
      "objectTypeSlug": "lead",
      "status": 1,
      "type": 2,
      "starred": false,
      "accessControlFunctions": ["VIEW", "EDIT", "DELETE"]
    }
  ],
  "meta": {
    "total": 15,
    "limit": 20,
    "currentPage": 1
  }
}
```

## Xem chi tiết

`POST /bapi/v1/filters/view`

```json
{
  "id": "FI00000000002"
}
```

```bash
curl --silent --location "https://${WORKSPACE_DOMAIN}/bapi/v1/filters/view" \
  --header "Authorization: Bearer ${API_KEY}" \
  --header 'Content-Type: application/json' \
  --data '{"id":"FI00000000002"}'
```

`data` là một filter resource đầy đủ theo schema bên dưới.

## Tạo bộ lọc

`POST /bapi/v1/filters`

Payload đầy đủ:

```json
{
  "name": "Bộ lọc khách hàng tiềm năng",
  "objectTypeId": "OT00000000023",
  "description": "Khách hàng đang được chăm sóc",
  "logicType": "AND",
  "logic": "",
  "conditions": [
    {
      "field": "status",
      "op": "in",
      "params": ["working", "nurturing"],
      "fieldType": "single_choice"
    }
  ],
  "sortFields": [
    {
      "field": "created",
      "order": "desc"
    }
  ],
  "limitRecord": 20,
  "accessControls": [
    {
      "functions": ["VIEW"],
      "option": 1,
      "items": [],
      "type": "personnel"
    }
  ],
  "tableSettings": "{\"columns\":[],\"showingColumns\":[],\"pinnedColumns\":{\"left\":[\"name\"],\"right\":[\"actionColumn\"]}}",
  "layoutFilterType": 1,
  "layoutConfig": {
    "objectId": "OT00000000023",
    "name": "Bộ lọc khách hàng tiềm năng",
    "description": "Khách hàng đang được chăm sóc",
    "limitRecord": 20,
    "sortFieldItems": [
      {
        "field": "created",
        "order": "desc"
      }
    ],
    "layoutFilterType": 1,
    "displayTaskMode": 0,
    "assignment": [
      {
        "functions": ["VIEW"],
        "option": 1,
        "items": [],
        "type": "personnel"
      }
    ]
  }
}
```

| Trường | Bắt buộc | Ràng buộc |
|---|---|---|
| `name` | Có | String, tối đa 100 ký tự |
| `objectTypeId` | Có | Object type ID hợp lệ trong workspace |
| `description` | Không | String/null, tối đa 500 ký tự |
| `logicType` | Có | Thường `AND` hoặc `OR` |
| `logic` | Không | String/null; biểu thức tùy chỉnh nếu có |
| `conditions` | Không | Mảng điều kiện |
| `sortFields` | Không | Tối đa 3 quy tắc |
| `limitRecord` | Không | Integer, tối thiểu `1` |
| `accessControls` | Không | Mảng phân quyền |
| `tableSettings` | Không | JSON được serialize thành string |
| `isQuickFilter` | Không | `1` nếu là quick filter, ngược lại `0` |
| `type` | Không | Server chọn mặc định nếu bỏ qua |
| `listItemLayout` | Không | String/null, ID list item layout |
| `itemDetailLayout` | Không | String/null, ID item detail layout |
| `layoutConfig` | Không | JSON object/null |
| `layoutFilterType` | Không | Integer/null |
| `displayTaskMode` | Không | `0` hoặc `1` |

Response create có thể là resource rút gọn. `conditions` hoặc `accessControls` có thể là `null` dù đã lưu. Luôn gọi view với ID vừa tạo để xác minh.

Khi người dùng không chỉ định phạm vi chia sẻ, mặc định chia sẻ quyền xem cho tất cả bằng:

```json
{
  "functions": ["VIEW"],
  "option": 1,
  "items": [],
  "type": "personnel"
}
```

Gửi cấu hình này trong `accessControls` và lặp lại chính xác trong `layoutConfig.assignment` để dữ liệu quyền và cấu hình UI nhất quán.

## Cập nhật bộ lọc

`PUT /bapi/v1/filters/{filter_id}`

Gửi các trường cần cập nhật. Để tránh mất cấu hình khi API thay đổi hành vi merge, workflow của skill phải lấy resource mới nhất và giữ nguyên mọi field không được yêu cầu sửa.

```json
{
  "name": "Bộ lọc khách hàng tiềm năng - Đã cập nhật",
  "objectTypeId": "OT00000000023",
  "description": "Mô tả bộ lọc đã cập nhật",
  "logicType": "AND",
  "logic": "",
  "conditions": [
    {
      "field": "status",
      "op": "in",
      "params": ["working", "nurturing", "qualified"],
      "fieldType": "single_choice"
    }
  ],
  "sortFields": [
    {
      "field": "created",
      "order": "asc"
    }
  ],
  "limitRecord": 20
}
```

```bash
curl --silent --location --request PUT \
  "https://${WORKSPACE_DOMAIN}/bapi/v1/filters/FI00000000004" \
  --header "Authorization: Bearer ${API_KEY}" \
  --header 'Content-Type: application/json' \
  --data @filter-update.json
```

Response update cũng có thể rút gọn; gọi view để xác minh. Gửi `conditions: []` sẽ xóa toàn bộ điều kiện hiện có.

## Xóa bộ lọc

`POST /bapi/v1/filters/delete`

```json
{
  "ids": ["FI00000000004"]
}
```

```bash
curl --silent --location "https://${WORKSPACE_DOMAIN}/bapi/v1/filters/delete" \
  --header "Authorization: Bearer ${API_KEY}" \
  --header 'Content-Type: application/json' \
  --data '{"ids":["FI00000000004"]}'
```

Response mẫu:

```json
{
  "r": 0,
  "msg": "Successful",
  "data": 2
}
```

`data` không nhất thiết bằng số ID đã gửi. Không thể xóa filter standard. Người dùng hiện tại phải có quyền `DELETE` đối với tất cả filter trong request.

## Cấu trúc resource

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | String | ID filter |
| `workspaceId` | String | ID workspace |
| `name` | String | Tên hiển thị |
| `slug` | String | Slug do hệ thống lưu |
| `description` | String/null | Mô tả |
| `logicType` | String | Chế độ kết hợp conditions |
| `logic` | String/null | Biểu thức tùy chỉnh |
| `conditions` | Array | Điều kiện lọc records |
| `objectTypeId` | String | Object type ID |
| `objectTypeSlug` | String | Object type slug |
| `objectType` | Object/null | Tóm tắt Object type |
| `status` | Integer | `1` là active |
| `tableSettings` | String (JSON) | Cài đặt columns/showing/pinned được serialize |
| `starred` | Boolean | Được người dùng hiện tại đánh dấu yêu thích |
| `sortFields` | Array | Quy tắc sắp xếp records |
| `limitRecord` | Integer | Giới hạn records hiển thị |
| `accessControls` | Array | Cấu hình chia sẻ đã lưu |
| `accessControlFunctions` | Array[String] | Quyền hiện tại như `VIEW`, `EDIT`, `DELETE` |
| `isQuickFilter` | Integer | `1` hoặc `0` |
| `type` | Integer | Filter người dùng thường là `2`; standard là `1` |
| `layoutConfig` | Object/null | Cấu hình layout tùy chọn |
| `layoutFilterType` | Integer/null | Loại layout filter |
| `displayTaskMode` | Integer | Chế độ hiển thị task |
| `created`, `updated` | Long | Timestamp mili giây |
| `createdBy`, `updatedBy` | Object/String/null | Người tạo/cập nhật |

## Conditions, sorting và access controls

### Condition

```json
{
  "field": "status",
  "op": "in",
  "params": ["working", "nurturing"],
  "fieldType": "single_choice"
}
```

| Trường | Bắt buộc | Mô tả |
|---|---|---|
| `field` | Có | Slug của Object field |
| `op` | Không | Toán tử so sánh |
| `params` | Tùy operator | Một giá trị, mảng hoặc `null` |
| `fieldType` | Không | Loại Object field |

Toán tử phổ biến: `=`, `!=`, `in`, `not in`, `like`, `not like`, `is null`, `not null`, `<`, `<=`, `>`, `>=`, `between`.

```json
[
  {
    "field": "status",
    "op": "=",
    "params": "working",
    "fieldType": "single_choice"
  },
  {
    "field": "created",
    "op": "between",
    "params": [1782867600000, 1785545999999],
    "fieldType": "date_time"
  },
  {
    "field": "owner",
    "op": "is null",
    "params": null,
    "fieldType": "lookup_normal"
  }
]
```

Kiểu `params` phụ thuộc đồng thời vào `fieldType` và `op`. Lấy metadata Object trước khi dựng condition.

Lookup tới người dùng hiện tại dùng đúng hình dạng sau:

```json
{
  "field": "owner",
  "op": "=",
  "params": "$currentUser",
  "fieldType": "lookup_normal"
}
```

Không thêm `iu` hoặc key ngoài schema vào condition này. JSON có `params: "$currentUser"` là đủ để server giải quyết người dùng hiện tại và để UI hiển thị condition đúng.

Nếu bảng operator ở đây chưa bao phủ `fieldType` cần dùng, đọc [danh mục điều kiện chi tiết của object-record](../../object-record/records_filter_conditions.md). Chỉ lấy quy tắc `fieldType` + `op` + kiểu `params`; vẫn dùng tên trường và cấu trúc payload của Filters API trong tài liệu này.

### Sort field

```json
{
  "field": "created",
  "order": "desc"
}
```

`order` chỉ nhận `asc` hoặc `desc`. Một filter hỗ trợ tối đa ba sort fields.

### Access control

```json
{
  "functions": ["VIEW"],
  "option": 1,
  "items": [],
  "type": "personnel"
}
```

| Trường | Mô tả |
|---|---|
| `functions` | Quyền được cấp như `VIEW`, `EDIT` |
| `option` | Tùy chọn gán quyền |
| `items` | Personnel/group tương ứng với `option` và `type` |
| `type` | Loại đối tượng phân quyền, thường `personnel` |

Không suy diễn rằng `accessControlFunctions` có thể gửi thay cho `accessControls`: trường đầu mô tả quyền hiệu lực của người gọi trong response; trường sau là cấu hình chia sẻ dùng trong payload.

Với `option: 1`, `items: []`, `type: "personnel"` và `functions: ["VIEW"]`, filter được chia sẻ quyền xem cho tất cả. Khi tạo filter, dùng cấu hình này làm mặc định nếu người dùng không yêu cầu phạm vi khác và đặt cùng giá trị trong `layoutConfig.assignment`.

## Validation và lỗi

- ID filter và Object type chỉ có ý nghĩa trong workspace tương ứng.
- `tableSettings` là JSON string; `layoutConfig` là JSON object.
- Create/update dùng field name dạng camelCase.
- Khi create/update trả resource rút gọn, xác minh bằng view trước khi kết luận.
- Với `400`, đọc `msg`, sửa đúng field validation và không retry payload y hệt.
- Với `401`, dừng và yêu cầu credential hợp lệ; không log token.
- Với `429`, tôn trọng thời gian chờ nếu response cung cấp và retry có giới hạn.
- Với timeout sau request ghi, gọi view/list để xác định request đã thành công hay chưa trước khi gửi lại, tránh tạo trùng hoặc ghi đè hai lần.
