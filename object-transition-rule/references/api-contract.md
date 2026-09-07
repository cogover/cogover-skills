# API contract cho Object Transition Rule

## Mục lục

- [Xác thực](#xác-thực)
- [Danh sách endpoint](#danh-sách-endpoint)
- [Transition rule schema](#transition-rule-schema)
- [Flow và graph metadata](#flow-và-graph-metadata)
- [Conditions, personnel và post-actions](#conditions-personnel-và-post-actions)
- [Payload mẫu](#payload-mẫu)
- [Response và mã lỗi](#response-và-mã-lỗi)
- [Semantics quan trọng](#semantics-quan-trọng)

Tài liệu này là contract tự đủ cho skill công khai. Chỉ xác minh hành vi bằng endpoint và response được mô tả tại đây; không mở source code, repository, file dự án, test, database, log nội bộ, browser bundle hoặc source map. Nếu contract không bao phủ một trường hợp, báo giới hạn thay vì truy tìm implementation.

## Xác thực

Toàn bộ endpoint trong tài liệu này dùng `/api/v1`, vì vậy phải dùng phiên Web App. Bắt buộc dùng `$cogover-api-auth` để:

1. Gọi `POST /bapi/v1/auth-token` bằng API Key Bearer.
2. Lấy `HttpSessionId`, `XSRF-TOKEN`, `AuthToken`.
3. Gửi mọi request bên dưới với:

```http
Cookie: HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
Content-Type: application/json
```

Không dùng `Authorization: Bearer {API_KEY}` cho bất kỳ endpoint `/api/v1` nào.

## Danh sách endpoint

| Thao tác | Method | URI | Request |
|---|---|---|---|
| List theo Object | `GET` | `/api/v1/object_security/transition_rule?objectSlug={slug}` | Không body |
| Detail theo ID | `GET` | `/api/v1/object_security/transition_rule?id={id}` | Không body |
| List theo Object ID | `GET` | `/api/v1/object_security/transition_rule?objectTypeId={id}` | Không body |
| Search nâng cao | `POST` | `/api/v1/object_security/transition_rule/get` | `GetTransitionRuleRequest` |
| Create | `POST` | `/api/v1/object_security/transition_rule/create` | `TransitionRuleRequest` |
| Update một rule | `POST` | `/api/v1/object_security/transition_rule/update` | `TransitionRuleRequest` có `id` |
| Update nhiều/status | `POST` | `/api/v1/object_security/transition_rule/updateMultiple` | `{"data":[TransitionRuleRequest],"statusChanged":0|1}` |
| Delete một | `POST` | `/api/v1/object_security/transition_rule/delete` | `{"id":"{id}"}` |
| Delete nhiều | `POST` | `/api/v1/object_security/transition_rule/deleteMultiple` | `{"data":[{"id":"{id}"}]}` |

Ưu tiên GET theo `objectSlug` cho list, GET theo `id` cho detail, `updateMultiple` cho active/inactive và `deleteMultiple` cho xóa.

`POST /get` hỗ trợ các trường `id`, `objectTypeId`, `objectSlug`, `objectFieldId`, `name`, `created`, `updated`, `createdBy`, `updatedBy`, `filterFieldsNotIn`, `withDetails`, `withPersonnelInfo`, `page`, `limit`, `order`, `sort`. Ưu tiên GET theo `id`/`objectSlug` cho workflow thông thường vì nó trả chi tiết flows.

## Transition rule schema

### Request create/update

| Trường | Kiểu | Create | Ghi chú |
|---|---|---|---|
| `id` | string | Bỏ | Bắt buộc cho update/delete; server sinh khi create |
| `objectFieldId` | string | Bắt buộc | ID field thật; endpoint update giữ field cũ |
| `name` | string | Bắt buộc | 1–255; unique trên Object |
| `slug` | string | Bắt buộc | UI: 2–100, `[A-Za-z0-9_]+`, không `__`; unique trên Object |
| `description` | string | Tùy chọn | Tối đa 1000 |
| `status` | integer | Tùy chọn | `0` inactive, `1` active; create bỏ trống thì server dùng `0` |
| `flows` | array | Bắt buộc, khác rỗng | Khi update, mảng khác rỗng thay toàn bộ flows |
| `metaData` | string | Bắt buộc theo skill | JSON string chứa UI-safe `nodes` và `viewport`; metadata tối giản có thể làm UI React Flow không an toàn |
| `sort` | integer | Tùy chọn | Bỏ trống khi create để server dùng max sort của field + 1 |
| `shouldFilterRecord` | boolean | Tùy chọn | Mặc định `false` |
| `recordFilter` | object | Có điều kiện | Chỉ dùng khi `shouldFilterRecord: true` |
| `cloneTargetValue` | string/null | Tùy phiên bản | Contract UI hiện có; chỉ là target của flow từ `_initial` |

Server-managed fields như `workspaceId`, `objectTypeId`, `created`, `updated`, `createdBy`, `updatedBy` chỉ dùng để đọc/xác minh. Không cần đưa vào payload create.

### Record filter

```json
{
  "logicType": "AND",
  "logic": "",
  "conditions": [
    {
      "field": "{fieldSlug}",
      "op": "=",
      "params": "{optionSlug}"
    }
  ],
  "type": 1,
  "index": 0
}
```

Resolve field/operator/params từ metadata thật. Dùng `params: null` cho `is null`/`not null`; dùng option slug cho field choice. Không tự sáng tạo operator.

## Flow và graph metadata

### Flow request

```json
{
  "name": "Create",
  "slug": "create",
  "originValue": "_initial",
  "targetValue": "{optionSlug}",
  "conditionBlocks": {
    "description": "",
    "allowUndo": false,
    "logicType": "AND",
    "logic": "",
    "personnelFilters": [],
    "filters": [],
    "postActions": []
  },
  "metaData": "{...JSON string...}"
}
```

Quy tắc:

- `originValue` và `targetValue` phải là option slug của field; `_initial` chỉ hợp lệ ở `originValue` theo UI.
- Mỗi flow phải có name không rỗng, tối đa 255 ký tự. Luôn dùng action name bằng tiếng Anh như `Create`, `Activate`, `Start packing`, `Complete`, `Request cancellation`; không dùng mẫu `{Origin} to {Target}` như `Draft to Activated`.
- Dùng slug flow 2–100 ký tự theo cùng quy tắc `[A-Za-z0-9_]+`, không `__` của UI; không dùng trùng slug trong cùng rule. Sinh slug từ action name theo `lower_snake_case`; nếu cần phân biệt cùng action từ nhiều origin, thêm context vào slug thay vì đổi display name thành cặp trạng thái.
- Flow bắt đầu từ `_initial` phải có `allowUndo: false` và không có post-action trong UI.
- Flow thường có thể dùng `allowUndo: true` nếu nghiệp vụ cho phép.
- `conditionBlocks.logicType` là `AND`, `OR` hoặc `CUSTOM`. Dùng `logic: ""` cho `AND`/`OR`; với `CUSTOM`, dùng biểu thức đánh số block như `1 AND (2 OR 3)`.
- UI cho phép tối đa 20 condition blocks trong một flow và tối đa 10 filter items trong record filter.

### Rule-level metadata

`metaData` là JSON string của object:

```json
{
  "nodes": [
    {
      "id": "_initial",
      "type": "_initial",
      "position": { "x": 100, "y": 100 },
      "data": {
        "label": "",
        "nodeSubtype": "_initial",
        "isActive": false,
        "isConnectionSource": false,
        "isConnectionTarget": false
      },
      "selected": false,
      "measured": { "width": 48, "height": 48 },
      "dragging": false
    },
    {
      "id": "node-{optionSlug}",
      "type": "custom",
      "position": { "x": 320, "y": 100 },
      "data": {
        "label": "{localizedOptionLabel}",
        "nodeSubtype": "{optionSlug}",
        "isActive": false,
        "isConnectionSource": false,
        "isConnectionTarget": false
      },
      "selected": false,
      "measured": { "width": 120, "height": 48 },
      "dragging": false
    }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 }
}
```

Mỗi option slug chỉ xuất hiện trong một node. `data.nodeSubtype` là giá trị nghiệp vụ; `label` chỉ là hiển thị và nên dùng translation theo locale hiện tại nếu có. Dùng `height: 48`; với custom node, tính width từ nhãn dài nhất giữa value gốc và mọi translation có thể hiển thị theo `clamp(82, 40 + 8 * số ký tự, 240)`. Không chỉ đo nhãn tiếng Anh khi UI có thể hiển thị locale dài hơn. `className` là key tùy chọn theo phiên bản.

### Flow-level metadata

`flow.metaData` là JSON string:

```json
{
  "edge": {
    "id": "edge-create",
    "source": "_initial",
    "sourceHandle": "source",
    "target": "node-{optionSlug}",
    "targetHandle": null,
    "type": "smoothstep",
    "label": "Create",
    "data": {
      "conditionBlocks": {
        "name": "Create",
        "slug": "create",
        "description": "",
        "allowUndo": false,
        "logicType": "AND",
        "logic": "",
        "personnelFilters": [],
        "filters": [],
        "postActions": []
      },
      "isSelected": false,
      "isDimmed": false,
      "isGroupHighlighted": false,
      "sourceColor": "var(--gray-80)"
    },
    "selected": false,
    "animated": false,
    "style": { "opacity": 1 }
  },
  "sourceId": "_initial",
  "targetId": "node-{optionSlug}"
}
```

Giữ `edge.data.conditionBlocks` đồng bộ với `flow.conditionBlocks`; mirror `flow.name`/`flow.slug` vào metadata để UI có thể khôi phục đúng action label, đặc biệt với flow không bắt đầu từ `_initial`.

- Dùng `sourceHandle: "source"` cho `_initial` khi deployment yêu cầu handle riêng của Start. Với custom node, có thể dùng `left`, `right`, `top`, `bottom` theo hướng layout đã xác minh trên UI; dùng `null` chỉ cho graph đơn giản chưa có routing chắc chắn. Không gán `"source"` cho mọi node.
- Dùng `right -> left` cho cạnh trái→phải, `left -> right` cho phải→trái và `bottom -> top` cho trên→dưới. Với hai cạnh ngược chiều giữa cùng hai node, route cạnh ngược bằng cặp khác như `top -> top` hoặc `left -> left` để tách edge và label.
- Gán cùng `sourceColor` cho mọi edge cùng source node; dùng `var(--gray-80)` cho `_initial` và màu hex hợp lệ, ổn định cho custom node.
- Không tự thêm `controlPoint`; chỉ giữ nó khi update edge đã được UI route thủ công. Không coi `markerEnd` là key bắt buộc nếu response hiện tại không có nó.
- Khi create, khởi tạo UI state trung tính: tất cả node/edge `selected: false`, `isActive: false`, `isSelected: false`, `isDimmed: false`, `isGroupHighlighted: false`, `animated: false`, `style.opacity: 1`. Không sao chép selection/dimming tạm thời từ một graph mà người dùng đang chọn node.

### Layout geometry UI-safe

Schema hợp lệ chưa đủ: React Flow vẫn có thể hiển thị node và action label chồng lên nhau. Trước create/update graph, áp dụng các bước sau:

1. Ước lượng action label width theo `clamp(72, 32 + 8.5 * số ký tự, 260)` và height khoảng 32 graph units để có đệm. Trên cạnh chính, yêu cầu khoảng trống giữa hai node theo hướng đi ít nhất `actionLabelWidth + 120`.
2. Với từ 8 node hoặc 12 flow, chia graph thành nhiều hàng/lane. Dùng layout hai hàng dạng snake cho chuỗi chính dài; đặt nhánh chờ, hủy và trả/hoàn ở lane riêng thay vì kéo toàn bộ chuỗi trên một hàng.
3. Nếu chưa đo được canvas thực tế, giữ bounds mục tiêu không quá khoảng `2200 x 1300` graph units ở min zoom `0.5`; nếu đo được canvas/min zoom khác thì tính lại theo kích thước thực.
4. Tính rectangle cho mọi node từ `position` và `measured`. Tính rectangle gần đúng cho label quanh midpoint/routing point của edge. Không mutation nếu có node-node, label-node hoặc label-label intersection; dùng ít nhất 16 graph units đệm giữa các label hội tụ.
5. Với nhiều edge cùng target, làm lệch midpoint theo cả trục x hoặc y; không đặt các nguồn cách đều trên một hàng hẹp khiến label lặp lại nằm chung một lane. Với edge hai chiều, dùng directional handles khác nhau.
6. Giữ `controlPoint` hiện có khi update. Không tự thêm `controlPoint` chỉ để chữa overlap nếu directional handles và bố trí lane đã đủ; chỉ thêm khi đã xác minh chính xác schema/routing của deployment.
7. Khi visual QA bằng browser, chờ `nodeCount = optionCount + 1` và `edgeLabelCount = flowCount` trước khi đo DOM. Trạng thái chỉ có Start trong lúc tải không phải graph thật. Yêu cầu bounding box thực tế không có collision và mọi node nằm trong rectangle của `.react-flow`.

### Checklist metadata UI sau khi ghi

1. Parse được rule `metaData` và tất cả `flow.metaData` bằng JSON parser; không chỉ kiểm tra chuỗi không rỗng.
2. Xác minh rule metadata có `nodes[]` và `viewport` số hợp lệ. Mỗi node phải có `id`, `type`, `position.x/y`, `data.label`, `data.nodeSubtype`, ba Boolean `isActive`, `isConnectionSource`, `isConnectionTarget`, `selected`, `measured.width/height` và `dragging`.
3. Xác minh có đúng một `_initial` node và một node cho mỗi option; không có node trùng `nodeSubtype`. Mọi `sourceId`/`targetId` và `edge.source`/`edge.target` phải trỏ tới node thật và khớp nhau.
4. Mỗi edge phải có `id`, `source`, `sourceHandle`, `target`, `targetHandle`, `type`, action `label`, `data.conditionBlocks`, bốn UI state trong `data`, `selected`, `animated` và `style.opacity`. `controlPoint` và các key styling theo phiên bản là tùy chọn.
5. Xác minh `edge.data.conditionBlocks.name/slug` khớp `flow.name/slug`, action name là tiếng Anh và không theo mẫu `{Origin} to {Target}`.
6. Chạy kiểm tra hình học ở mục **Layout geometry UI-safe** trên metadata đọc lại; với yêu cầu sửa lỗi hiển thị và browser sẵn có, đo thêm bounding box DOM sau khi graph tải đủ.
7. Nếu API mutation trả `r: 0` nhưng read-back thiếu key baseline, sai kiểu hoặc còn collision, coi thao tác chưa hoàn tất về UI. Không báo thành công cho tới khi metadata read-back đạt checklist.

## Conditions, personnel và post-actions

Chỉ dùng các cấu trúc nâng cao khi người dùng yêu cầu và đã resolve đủ ID liên quan.

### Filter block

```json
{
  "type": 6,
  "index": 0,
  "logicType": "AND",
  "logic": "",
  "scopeCondition": 1,
  "conditions": [
    { "field": "{fieldSlug}", "op": "not null", "params": null }
  ]
}
```

Loại block của UI:

| `type` | Ý nghĩa | ID bổ sung |
|---|---|---|
| `1` | Nhân sự | Dùng `personnelFilters`, không dùng `filters` |
| `6` | Record hiện tại | Không cần ID liên kết |
| `7` | Record qua lookup field | `fieldLookUp` là field ID thật |
| `8` | Record trong related list | `relatedListId` là related-list ID thật |

`scopeCondition`: `1` all, `2` any, `3` none. Flow khởi tạo từ `_initial` chỉ hiện loại personnel trong UI.

### Personnel filter

```json
{
  "type": 1,
  "op": "all",
  "index": 0
}
```

`op` chỉ là `all`, `include`, `exclude`. Tùy `type`, resolve và gửi đúng một hay nhiều ID trong `personnelId`, `departmentId`, `positionId`, `roleId`, `fieldId`. Không trộn các ID không thuộc cùng workspace/Object.

### Post-action

| `type` | Ý nghĩa | Bắt buộc |
|---|---|---|
| `1` | Kiểm tra field | `name`; metadata check-fields hợp lệ |
| `2` | Tạo record | `name`, `referenceObjectId`, `layoutId` |
| `3` | Cập nhật record | `name`, `referenceObjectId`, `referenceFieldId`, `layoutId` |

UI serialize `fieldsCopy` hoặc `checkFields` vào `metaData` JSON string. Resolve Object/field/layout/related-list trước khi ghi. Nếu không có mẫu thật cùng action type để đối chiếu, dừng và làm rõ thay vì phát minh metadata.

## Payload mẫu

### Create active rule tối thiểu

Trong ví dụ này, giá trị của `metaData` phải được serialize từ các object mẫu ở phần graph, không gửi literal `{...}`.

```json
{
  "objectFieldId": "{objectFieldId}",
  "name": "Order status flow",
  "slug": "order_status_flow",
  "description": "",
  "status": 1,
  "shouldFilterRecord": false,
  "flows": [
    {
      "name": "Create",
      "slug": "create",
      "originValue": "_initial",
      "targetValue": "{optionSlug}",
      "conditionBlocks": {
        "description": "",
        "allowUndo": false,
        "logicType": "AND",
        "logic": "",
        "personnelFilters": [],
        "filters": [],
        "postActions": []
      },
      "metaData": "{serializedFlowMetadata}"
    }
  ],
  "metaData": "{serializedRuleMetadata}"
}
```

### Update status nhiều rule

```json
{
  "data": [
    { "id": "{ruleId1}", "status": 1 },
    { "id": "{ruleId2}", "status": 1 }
  ],
  "statusChanged": 1
}
```

`statusChanged` là trường UI gửi để biểu diễn thao tác batch; từng item trong `data` vẫn phải có `status`.

### Delete nhiều rule

```json
{
  "data": [
    { "id": "{ruleId1}" },
    { "id": "{ruleId2}" }
  ]
}
```

## Response và mã lỗi

### Success envelope

Create:

```json
{
  "r": 0,
  "msg": "Success",
  "data": [{ "id": "{ruleId}" }]
}
```

Update/delete có thể không có `data`. Read trả `data` là mảng và `meta` có `total`, `currentPage`, `lastPage`, `perPage`.

Read-back có thể được chuẩn hóa khác payload ghi:

- Detail có thể trả `objectSlug: null`; dùng `objectTypeId` cùng list theo Object để xác minh ownership.
- Thứ tự `flows` không ổn định; so theo flow ID/slug hoặc cặp có hướng `originValue -> targetValue`.
- Boolean `false` như `allowUndo: false` có thể bị bỏ khỏi `flow.conditionBlocks` nhưng vẫn còn trong `flow.metaData.edge.data.conditionBlocks`. Chỉ coi là lệch khi cả hai representation đều mâu thuẫn với trạng thái dự kiến.

### Error thường gặp

| `r` | Ý nghĩa thực tế | Cách xử lý |
|---|---|---|
| `400` | Object field/type không hợp lệ | Resolve lại Object và field |
| `402` | Field/lookup/related-list ID không hợp lệ | Không retry; resolve lại ID |
| `405` | Thiếu/sai rule ID | View/list lại mục tiêu |
| `406` | Filter không hợp lệ | Kiểm tra type/logic/conditions |
| `407` | Name invalid hoặc trùng | Chọn name unique trên Object |
| `408`, `411` | Personnel filter/type/op không hợp lệ | Resolve type/ID và dùng `all/include/exclude` |
| `413` | Status không hợp lệ | Dùng `0` hoặc `1` |
| `434` | Description không hợp lệ | Giới hạn 1000 |
| `435` | Slug invalid hoặc trùng | Tuân regex/length và unique trên Object |
| `436` | `originValue` không hợp lệ | Dùng `_initial` hoặc option slug thật |
| `437` | `targetValue` không hợp lệ | Dùng option slug thật |
| `438` | Flows rỗng hoặc thiếu logic | Gửi ít nhất một flow và đủ `logicType`/`logic` |
| `439` | Post-action không hợp lệ | Kiểm tra type và reference IDs |
| `445` | `cloneTargetValue` không hợp lệ ở bản API có tính năng này | Dùng target của flow `_initial` hoặc `null` |
| `501` | Rule không tồn tại | Dừng mutation, list lại |
| `506` | Object/field context không tồn tại | Resolve lại metadata |
| `524` | Vượt giới hạn rule/active rule | Giảm số rule hoặc deactivate trước |
| `600` | Filter service lỗi | Báo `msg`, không retry mutation mù |
| `700` | Lỗi nội bộ | Re-read để xác định kết quả trước khi thử lại |

HTTP validation thường là `422`; lỗi nội bộ thường là `500`. Luôn đọc cả `r` và `msg`.

## Semantics quan trọng

- Name và slug unique theo **Object**, không chỉ theo field.
- Tối đa 50 transition rules trên Object và 5 active rules trên Object.
- Lần đầu tạo transition rule cho field có thể tạo thêm field hệ thống lưu giá trị single-choice trước đó.
- Update không cho chuyển rule sang `objectFieldId` khác; field hiện tại được giữ nguyên.
- Với update, `flows` khác rỗng là replace-all và flow IDs có thể được tạo lại. Bỏ `flows` hoặc gửi `[]` sẽ giữ flows hiện tại.
- Với scalar update, trường `null` thường có nghĩa là giữ giá trị cũ, không phải xóa. Dùng chuỗi rỗng chỉ khi endpoint/UI cho phép và người dùng muốn xóa description.
- `shouldFilterRecord: false` vô hiệu hóa phạm vi filter; không suy luận filter record đã bị xóa vật lý.
- Create/update graph phải giữ ba lớp đồng bộ: rule fields, `flows`, metadata React Flow. API có thể lưu nghiệp vụ dù metadata bị lệch, nhưng UI sẽ hiển thị sai hoặc không thể sửa an toàn.
