# Process Builder API

API quản lý quy trình (process/workflow) thông qua Workflow Server.

## Xác thực

Header `Authorization: Bearer {token}` (định dạng: `{tokenId}-{secretToken}`).

## Quy ước Response

Tất cả response đều chứa trường `r` (result code):
- `r = 0`: Thành công
- `r != 0`: Thất bại (kèm `msg` mô tả lỗi)

---

## 1. Tạo quy trình

**Endpoint:** `POST /bapi/v1/processes`

**Request Body:** JSON object chứa thông tin quy trình cần tạo (cấu trúc do Workflow Server định nghĩa).

Ba validation bắt buộc trước khi gửi:

- Mọi slug user-editable do process tạo phải dài ít nhất 2 ký tự và khớp `^[A-Za-z](?!.*__)[A-Za-z0-9_]*[^_]$`: bắt đầu bằng chữ cái, không có `__` và không kết thúc bằng `_`. Cho phép các slug hệ thống cố định như decision outcome `_default`.
- `overviewScreen` phải là object; không gửi `null`. Khi không có overview tùy chỉnh, dùng `{"layout":[],"permissionGeneralInfo":[]}`.
- Với mọi field User Task có `required` và `readOnly` truthy, bắt buộc `canSendData: true` ngay trên component trong `userTasks[].content`. Đây là checkbox **Gửi dữ liệu**, quyết định field có được đưa vào payload submit form gửi tới `run-workflow-server` hay không. Không dùng `availableForOutput` và không đồng bộ cờ này sang resource.

**Response:**
- `201` - Tạo thành công (`r = 0`)
- `400` - Lỗi nghiệp vụ (`r != 0`)
- `500` - Lỗi hệ thống

### Response thành công (201)

```json
{
  "r": 0,
  "msg": "Success",
  "data": {
    "id": "PE00000000026",
    "processInfoId": "PI00000000021",
    "name": "Quy trinh 1",
    "slug": "quy_trinh_1",
    "type": "manual_flow",
    "workspaceId": "WS_SAMPLE_TENANT_B",
    "progressStatus": "DRAFT",
    "isPublished": false,
    "isValid": true,
    "isNewestVersion": true,
    "currentVersion": true,
    "version": "V1",
    "versionNumber": 1,
    "versionLabel": "",
    "status": 2,
    "created": 1772726756273,
    "updated": 1772726756273,
    "createdBy": { ... },
    "updatedBy": { ... },
    "metadata": {},
    "xmlString": "...",
    "participantPermission": { ... },
    "starterPermission": { ... },
    "accessControls": [ ... ],
    "processInstanceAccessControls": [ ... ],
    "permissions": [],
    "userTasks": [ ... ],
    "overviewScreen": { ... },
    "resources": { ... }
  }
}
```

### Mô tả các trường chính trong `data`

| Field | Type | Mô tả |
|---|---|---|
| `id` | String | ID của quy trình |
| `processInfoId` | String | ID thông tin quy trình |
| `name` | String | Tên quy trình |
| `slug` | String | Slug định danh |
| `type` | String | `manual_flow`, `normal_flow`, `scheduled_flow`, `triggered_flow` hoặc `sequence_flow` |
| `workspaceId` | String | ID workspace |
| `progressStatus` | String | Trạng thái tiến trình: `DRAFT`, ... |
| `isPublished` | Boolean | Đã publish hay chưa |
| `isValid` | Boolean | Quy trình có hợp lệ không |
| `isNewestVersion` | Boolean | Có phải phiên bản mới nhất |
| `currentVersion` | Boolean | Có phải phiên bản hiện tại |
| `version` | String | Nhãn phiên bản (ví dụ: `V1`) |
| `versionNumber` | Integer | Số thứ tự phiên bản |
| `versionLabel` | String | Nhãn tùy chỉnh cho phiên bản |
| `status` | Integer | Trạng thái quy trình |
| `created` | Long | Timestamp tạo (ms) |
| `updated` | Long | Timestamp cập nhật (ms) |
| `createdBy` | Object | Thông tin người tạo (`id`, `first_name`, `last_name`, `_full_name`, `avatar`) |
| `updatedBy` | Object | Thông tin người cập nhật (cấu trúc giống `createdBy`) |
| `metadata` | Object | Metadata tùy chỉnh |
| `xmlString` | String | Chuỗi BPMN XML mô tả sơ đồ quy trình |
| `participantPermission` | Object | Quyền của người tham gia (xem bên dưới) |
| `starterPermission` | Object | Quyền của người khởi tạo (xem bên dưới) |
| `accessControls` | Array | Danh sách quyền truy cập quy trình |
| `processInstanceAccessControls` | Array | Quyền truy cập instance (ví dụ: `START_INSTANCE`) |
| `permissions` | Array | Danh sách quyền bổ sung |
| `userTasks` | Array | Danh sách các user task trong quy trình |
| `overviewScreen` | Object | Cấu hình màn hình tổng quan (layout, fields, permissions) |
| `resources` | Object | Tài nguyên quy trình (`system`, `custom`, `loops`, `userTasks`, `actions`) |

### `participantPermission`

| Field | Type | Mô tả |
|---|---|---|
| `VIEW_INSTANCE_PROGRESS` | Boolean | Cho phép xem tiến trình instance |
| `VIEW_INSTANCE_FULL` | Boolean | Cho phép xem đầy đủ instance |
| `ANY_PERFORMER_CAN_VIEW_PROGRESS_OF_SEQUENCE` | Boolean | Bất kỳ người thực hiện nào cũng có thể xem tiến trình |
| `ANY_PERFORMER_CAN_REASSIGN_TASK` | Boolean | Bất kỳ người thực hiện nào cũng có thể gán lại task |

### `starterPermission`

| Field | Type | Mô tả |
|---|---|---|
| `VIEW_INSTANCE_PROGRESS` | Boolean | Cho phép xem tiến trình instance |
| `VIEW_INSTANCE_FULL` | Boolean | Cho phép xem đầy đủ instance |
| `SEQUENCE_STARTER_CAN_ASSIGN_TASK` | Boolean | Người khởi tạo có thể gán task |
| `SEQUENCE_STARTER_CAN_EXECUTE_EVERY_TASK` | Boolean | Người khởi tạo có thể thực hiện mọi task |
| `SEQUENCE_STARTER_CAN_DISCONNECT` | Boolean | Người khởi tạo có thể ngắt kết nối |

### `accessControls[]`

| Field | Type | Mô tả |
|---|---|---|
| `type` | String | Loại quyền: `owner`, `personnel` |
| `functions` | Array\<String\> | Danh sách quyền: `VIEW`, `ADD`, `EDIT`, `DELETE` |
| `items` | Array\<String\> | Danh sách ID đối tượng được gán quyền |
| `option` | Integer | Tùy chọn quyền (1: tất cả, 2: chỉ định) |

### `userTasks[]`

| Field | Type | Mô tả |
|---|---|---|
| `id` | String | ID của user task |
| `nodeId` | String | ID node trong sơ đồ BPMN |
| `name` | String | Tên task |
| `slug` | String | Slug định danh |
| `isRoot` | Boolean | Có phải task gốc không |
| `processId` | String | ID quy trình chứa task |
| `approvalScreen` | Integer | Loại màn hình phê duyệt |
| `taskPerformer` | Array | Cấu hình người thực hiện task |
| `content` | Array | Cấu hình layout/UI của task (chi tiết bỏ qua) |
| `pageSettings` | Object | Cấu hình giao diện trang. Với `userTask`, mặc định padding trang bằng `0`, `settingPage.typeColor = "primary"`, `settingPage.combinationRatio = 100`; xem template đầy đủ trong `SKILL.md` |
| `participantPermission` | Object | Quyền người tham gia riêng cho task |

---

## 2. Cập nhật quy trình

**Endpoint:** `PUT /bapi/v1/processes/{id}`

| Path Param | Mô tả |
|---|---|
| `id` | ID của quy trình cần cập nhật |

**Request Body:** JSON object chứa thông tin cần cập nhật.

**Response:**
- `200` - Cập nhật thành công (`r = 0`)
- `400` - Lỗi nghiệp vụ (`r != 0`)
- `500` - Lỗi hệ thống

Response trả về cấu trúc tương tự như response khi tạo quy trình (xem mục 1), kèm thêm trường `meta`:

| Field | Type | Mô tả |
|---|---|---|
| `meta.errors` | Array | Danh sách lỗi (rỗng khi thành công) |

### Lỗi `r: 414` "process is not in the right progress status for save"

Xảy ra khi quy trình đang ở `progressStatus: ACTIVATED` hoặc `isPublished: true`. Không thể PUT trực tiếp, **kể cả khi body có** `progressStatus: "DRAFT"` và `isPublished: false`.

**Cách xử lý:**
1. Hỏi xác nhận khách hàng trước khi xoá.
2. Lấy bản XML hiện tại qua `POST /bapi/v1/processes/view` với `{"id": "PE..."}`, fix lỗi trong `xmlString`/`resources`/...
3. Strip các trường server-managed khỏi body: `id`, `processInfoId`, `version`, `versionNumber`, `versionLabel`, `currentVersion`, `isNewestVersion`, `status`, `created`, `updated`, `createdBy`, `updatedBy`, `workspaceId`, `progressStatus`, `isPublished`, `isValid`, `validationMessage`.
4. `POST /bapi/v1/processes/delete` với `{"id": "PE...", "processInfoId": "PI..."}` — xoá toàn bộ versions cùng processInfoId.
5. `POST /bapi/v1/processes` với body đã fix — tạo lại. Process mới sẽ mang `id`/`processInfoId` mới.

---

## 3. Xóa quy trình

**Endpoint:** `POST /bapi/v1/processes/delete`

**Request Body:** JSON object chứa thông tin quy trình cần xóa.

**Response:**
- `200` - Xóa thành công (`r = 0`)
- `400` - Lỗi nghiệp vụ (`r != 0`)
- `500` - Lỗi hệ thống

### Response thành công (200)

```json
{
  "r": 0,
  "msg": "Success",
  "data": {
    "id": "PE00000000026",
    "processInfoId": "PI00000000021",
    "name": "Quy trinh 1",
    "slug": "quy_trinh_1",
    "type": "manual_flow",
    "workspaceId": "WS_SAMPLE_TENANT_B",
    "status": 2,
    "isPublished": false,
    "isValid": true,
    "currentVersion": true,
    "version": "null1",
    "created": 1772726756273,
    "updated": 1772731163652,
    "metadata": {}
  }
}
```

Response xóa trả về thông tin cơ bản của quy trình đã xóa (không bao gồm `xmlString`, `userTasks`, `resources`, `overviewScreen`, ...).

---

## 4. Danh sách quy trình

**Endpoint:** `POST /bapi/v1/processes/list`

**Request Body:** JSON object chứa tham số lọc/phân trang.

| Tham số | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `page` | Integer | (bắt buộc) | Số trang, bắt đầu từ `1`. Thiếu sẽ trả lỗi `Page must be greater than 0` |
| `limit` | Integer | — | Số bản ghi mỗi trang. **Phải dùng `limit`, KHÔNG dùng `pageSize` hoặc `per_page`** — các tên khác bị server bỏ qua, response sẽ trả `data: []` dù `meta.total > 0` |
| `keywords` | Array\<String\> | `[]` | Tìm kiếm mờ theo `name` hoặc `slug` |

**Ví dụ body đúng:**
```json
{ "page": 1, "limit": 50, "keywords": ["payment_milestone_reminder"] }
```

**Response:**
- `200` - Thành công
- `400` - Lỗi nghiệp vụ (`r != 0`)
- `500` - Lỗi hệ thống

### Response thành công (200)

```json
{
  "r": 0,
  "msg": "Success",
  "data": [
    {
      "id": "PE00000000028",
      "processInfoId": "PI00000000023",
      "name": "Quy trình Onboarding nhân sự mới",
      "slug": "quy_trinh_onboarding_nhan_su_moi",
      "type": "manual_flow",
      "workspaceId": "WS_SAMPLE_TENANT_B",
      "status": 1,
      "isPublished": true,
      "isValid": false,
      "validationMessage": "",
      "currentVersion": true,
      "version": "V1",
      "created": 1772728761454,
      "updated": 1772731149763,
      "createdBy": { ... },
      "updatedBy": { ... },
      "metadata": {},
      "description": ""
    }
  ],
  "meta": {
    "per_page": 20,
    "total": 8,
    "last_page": 1,
    "current_page": 1
  }
}
```

> `data` là một **mảng** các quy trình (khác với create/update/view trả về object đơn).

### Mô tả các trường chính trong mỗi phần tử `data[]`

| Field | Type | Mô tả |
|---|---|---|
| `id` | String | ID của quy trình |
| `processInfoId` | String | ID thông tin quy trình |
| `name` | String | Tên quy trình |
| `slug` | String | Slug định danh |
| `type` | String | `manual_flow`, `normal_flow`, `scheduled_flow`, `triggered_flow` hoặc `sequence_flow` |
| `workspaceId` | String | ID workspace |
| `status` | Integer | Trạng thái quy trình |
| `isPublished` | Boolean | Đã publish hay chưa |
| `isValid` | Boolean | Quy trình có hợp lệ không |
| `validationMessage` | String | Thông báo lỗi validation (rỗng nếu hợp lệ) |
| `currentVersion` | Boolean | Có phải phiên bản hiện tại |
| `version` | String | Nhãn phiên bản |
| `created` | Long | Timestamp tạo (ms) |
| `updated` | Long | Timestamp cập nhật (ms) |
| `createdBy` | Object | Thông tin người tạo |
| `updatedBy` | Object | Thông tin người cập nhật |
| `metadata` | Object | Metadata (chứa cấu hình trigger cho `triggered_flow`) |
| `description` | String | Mô tả quy trình |

### Phân trang `meta`

| Field | Type | Mô tả |
|---|---|---|
| `per_page` | Integer | Số lượng mỗi trang |
| `total` | Integer | Tổng số quy trình |
| `last_page` | Integer | Số trang cuối |
| `current_page` | Integer | Trang hiện tại |

---

## 5. Xem chi tiết quy trình

**Endpoint:** `POST /bapi/v1/processes/view`

**Request Body:** JSON object chứa thông tin quy trình cần xem (ví dụ: `id` của process).

**Response:**
- `200` - Thành công (`r = 0`)
- `400` - Lỗi nghiệp vụ (`r != 0`)
- `500` - Lỗi hệ thống

Response trả về cấu trúc tương tự như response khi tạo quy trình (xem mục 1).

### Canonicalization của response view

Response view có thể khác representation của request:

- server có thể remap Node ID;
- một số BPMN tag `incoming`, `outgoing`, `sequenceFlow` có thể được serialize với prefix `bpmn:` thay vì `bpmn2:`;
- Omni Message có thể mất marker rỗng và `action.data` có thể được parse từ string thành object.

Khi verify, so sánh topology và semantic thay vì PUT chỉ để khôi phục representation. Riêng Respond to Webhook nguồn Start phải so `waitActionSlug` với Start ID sau GET; lệch nghĩa là cấu hình chưa sẵn sàng dù `isValid:true`.

---

## 6. Other (Thao tác tùy chỉnh)

**Endpoint:** `POST /bapi/v1/processes/other`

**Header bổ sung:**

| Header | Type | Mặc định | Mô tả |
|---|---|---|---|
| `x-req-service` | String (số) | `"0"` | Mã service type tùy chỉnh gửi sang Workflow Server |

**Request Body:** JSON object tùy theo `serviceType`.

**Response:**
- `200` - Thành công
- `400` - Lỗi nghiệp vụ (`r != 0`)
- `500` - Lỗi hệ thống
