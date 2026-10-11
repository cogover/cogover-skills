## Get Records Task (Task Lấy Bản Ghi)

Task hệ thống lấy bản ghi từ một đối tượng (object type) khi luồng chạy đến; cấu hình được điều kiện lọc, sắp xếp và loại kết quả (một hoặc nhiều bản ghi). `objectTypeId`/`objectTypeSlug` và `metaDataType.object`/`objectSlug` của output lấy theo bullet "Thông tin Object thật" ở [mục Chuẩn bị của SKILL.md](../SKILL.md#chuẩn-bị); `OT00000000011`/`lead` trong ví dụ chỉ minh hoạ. Duyệt kết quả bằng Loop: [loop-task.md](loop-task.md). Mẫu: `samples/sample_process_usertask_get_records.json`. Tiêu chí PASS runtime: [runtime-validation.md](runtime-validation.md#tiêu-chí-observable-theo-node).

### BPMN XML

```xml
<elEx:getRecordTask id="{GET_RECORD_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="GET_RECORD_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:getRecordTask>
```

Element `elEx:getRecordTask` (không phải `bpmn2:userTask`/`bpmn2:sendTask`); khai báo `xmlns:elEx="http://element-ex/schema"` trong `bpmn2:definitions` ([namespace](../references/bpmn-xml-and-diagram.md#namespace-và-kết-nối-logic)).

### `actions` trong JSON

```json
{
  "actions": [
    {
      "id": "{ACTION_ID}",
      "nodeId": "{GET_RECORD_NODE_ID}",
      "type": "GET_RECORD",
      "name": "{TASK_NAME}",
      "slug": "{task_slug}",
      "description": "",
      "data": {
        "objectTypeId": "{OBJECT_TYPE_ID}",
        "objectTypeSlug": "{object_type_slug}",
        "logic": "",
        "logicType": "NONE",
        "conditions": [],
        "sortFields": [],
        "resultType": 1,
        "outputVariable": ""
      }
    }
  ]
}
```

### Chi tiết các trường trong `data`

#### 1. `objectTypeId`, `objectTypeSlug`

ID và slug của loại đối tượng cần lấy bản ghi (ví dụ `"OT00000000011"`, `"lead"`), BẮT BUỘC lấy qua `$object-info`.

#### 2. `logicType`, `logic`

- `"NONE"`: không có điều kiện lọc (lấy tất cả).
- `"AND"`: mọi điều kiện phải thoả; `"OR"`: ít nhất một điều kiện thoả; `"CUSTOM"`: `logic` chứa biểu thức, ví dụ `"1 AND (2 OR 3)"` (số = vị trí trong mảng `conditions`, bắt đầu từ 1). Chế độ khác để `logic: ""`.
- Có `conditions` thì `logicType` phải là `"AND"`, `"OR"` hoặc `"CUSTOM"`.

#### 3. `conditions`

Mỗi phần tử là điều kiện `{"field", "op", "params", "fieldType"}` theo [danh mục điều kiện của object-record](../../object-record/records_filter_conditions.md#các-điều-kiện) (bảng `op` và kiểu `params` theo `fieldType`; boolean dùng `1` = true, `0` = false; cách bọc `conditions`/`logicType`/`logic` ở mục [Dùng trong Process](../../object-record/records_filter_conditions.md#dùng-trong-process-process-creator)). Khác biệt riêng của node:

- `op` `is null`/`not null`: `params: null`.
- `fieldType: "formula"`: dùng `op` theo kiểu dữ liệu mà công thức trả về (text, number, date...).
- Thêm `isRaw` để phân biệt hai nguồn giá trị so sánh:

**3a. Giá trị tĩnh — `isRaw: true`:** `params` là giá trị trực tiếp (`123`, `"hello"`, `null`, `["a","b"]`); engine dùng `params` làm giá trị so sánh.

```json
{ "field": "status", "op": "=", "params": "active", "fieldType": "single_choice", "isRaw": true }
```

**3b. Biến workflow — `isRaw: false`:** so sánh với `$loop.*`, `$action.*`, `$flow.input.*`, `$userTask.*`...; engine resolve giá trị từ `resourceSlug`, không đọc `params`.

```json
{
  "field": "source_id",
  "op": "=",
  "params": null,
  "fieldType": "numeric",
  "isRaw": false,
  "name": "",
  "resourceDataType": "NUMBER",
  "resourceSlug": "$loop.loop_records.currentItem.source_id",
  "resourcePathName": "workflow_resource:list.loop / Lặp records / Current Item / source_id"
}
```

- `params`: BẮT BUỘC `null`; `isRaw`: BẮT BUỘC `false`; `name`: `""`; `resourceDataType`: kiểu của biến (`NUMBER`, `TEXT`, `DATE`, `RECORD`, ...); `resourceSlug`: absolute slug của biến; `resourcePathName`: tên hiển thị đường dẫn.
- KHÔNG BAO GIỜ đặt đường dẫn biến vào `params` (`"params": "$loop...currentItem.source_id"` là SAI). KHÔNG BAO GIỜ dùng `isRaw: true` với biến workflow: gây lỗi `NullPointerException: Cannot invoke "org.json.JSONArray.length()"`. KHÔNG dùng object `{"type": 4, "value": "..."}`: đó là format `recordData` của Create/Update Record, không áp dụng cho `conditions`.

| Nguồn biến | `resourceSlug` | `resourcePathName` |
|---|---|---|
| Loop currentItem | `$loop.<loop_slug>.currentItem.<field>` | `workflow_resource:list.loop / <Loop Name> / Current Item / <field>` |
| Action output | `$action.<action_slug>.output.<field>` | `workflow_resource:list.action / <Action Name> / Output / <field>` |
| Triggered record | `$flow.input.newRecord.<field>` | `workflow_resource:list.resource / Input / newRecord / <field>` |
| User Task field | `$userTask.<task_slug>.<field>` | `workflow_resource:list.userTask / <Task Name> / <field>` |
| Variable | `$flow.<variable_slug>` | `workflow_resource:list.variable / <Variable Name>` |

Ví dụ CUSTOM — điều kiện 1 VÀ (2 HOẶC 3), trường formula và lựa chọn đơn:

```json
{
  "logicType": "CUSTOM",
  "logic": "1 AND (2 OR 3)",
  "conditions": [
    { "field": "last_first_name", "op": "not null", "params": null, "fieldType": "formula", "isRaw": true },
    { "field": "first_last_name", "op": "not like", "params": "x", "fieldType": "formula", "isRaw": true },
    { "field": "status", "op": "in", "params": ["working", "nurturing"], "fieldType": "single_choice", "isRaw": true }
  ]
}
```

Ví dụ trên chỉ dùng điều kiện tĩnh. Field `formula` chỉ lọc đúng khi là formula tính khi lưu ([object-info](../../object-info/references/api-object-fields.md#formula-tính-khi-đọc-và-khi-lưu)). Logic `CUSTOM`/`OR` có điều kiện biến phải kiểm chứng bằng lượt chạy trước khi dùng ([giới hạn đã quan sát](#giới-hạn-đã-quan-sát-khi-chạy)).

#### 4. `sortFields`

```json
{ "sortFields": [ { "field": "id", "order": "asc" }, { "field": "created", "order": "desc" } ] }
```

- Mỗi phần tử bắt buộc có `field` là field slug thật và `order` là `asc` hoặc `desc`; runtime chuyển `{field, order}` thành sort của backend `{<field>:{order:<order>}}` — không gửi `direction`, không gửi dạng object lồng sẵn.
- Thứ tự phần tử là độ ưu tiên sắp xếp. Dùng field ổn định/duy nhất (thường `id`) làm sort cuối để Loop có thứ tự tái lập được. Không cần sort: `[]`.

#### 5. `resultType`, `limitRecord`

- `1`: UI intent lấy bản ghi đầu tiên; downstream dùng `output.record`.
- `2`: UI intent lấy tất cả bản ghi; downstream/Loop dùng `output.records`.
- Runtime hiện vẫn tạo cả `record` (phần tử đầu) và `records` (list) cho cả hai mode; không dựa vào đó để dùng `resultType: 1` cho Loop — cấu hình `2` để request thể hiện đúng nghiệp vụ.
- `limitRecord: 0` dùng giới hạn mặc định của runtime; đặt số dương khi cần giới hạn rõ ràng.

#### 6. `outputVariable`

Tên biến đầu ra; `""` dùng mặc định.

### Giới hạn đã quan sát khi chạy

- `sortFields` theo field formula làm node lỗi `NullPointerException`. Sort theo field lưu; cần sort theo giá trị tính toán thì process ghi giá trị đó vào field số/text trước (*đã sửa và chạy đúng*).
- Formula resource đọc `$action.{slug}.output.records` chỉ thấy `id` của từng bản ghi. Cần field khác: Loop qua `output.records`, đọc `$loop.{loop_slug}.currentItem.<field>` và cộng dồn bằng Assignment, hoặc trong Formula gọi `Workspace.getInstance().getRecord(objectSlug, id)` ([Cogover Scripting API](../../object-info/references/cogover-scripting-api-vi.md#132-getrecordobjectslug-id)) (*đã sửa và chạy đúng*).
- Điều kiện `isRaw: false` so field lựa chọn với biến lựa chọn (ví dụ `$flow.input.newRecord.<single_choice>`) không khớp vì giá trị runtime của biến là danh sách option ID. Lưu một field text khoá do process ghi (ví dụ `"grade|purpose"`) ở bản ghi cần tìm và so sánh text, hoặc dùng `params` tĩnh (*đã sửa và chạy đúng*).
- `logicType` `OR`/`CUSTOM` trộn nhiều điều kiện, hoặc hai điều kiện cùng tham chiếu một resource, đã cho kết quả sai trong một lần thử (*quan sát, cần kiểm chứng*): kiểm chứng bằng lượt chạy trước khi dùng; ưu tiên `AND`, tách trường hợp bằng nhiều Get Records và Exclusive Gateway (`output.total == 0` đi nhánh mặc định).

### Resources của action (`resources.actions[]`)

```json
{
  "id": "{ACTION_ID}",
  "type": "GET_RECORD",
  "name": "{TASK_NAME}",
  "slug": "{task_slug}",
  "nodeId": "{GET_RECORD_NODE_ID}",
  "resources": [
    { "absoluteSlug": "$action.{task_slug}.startAt", "dataType": "DATE_TIME", "name": "Start At", "slug": "startAt" },
    { "absoluteSlug": "$action.{task_slug}.endAt", "dataType": "DATE_TIME", "name": "End At", "slug": "endAt" },
    {
      "absoluteSlug": "$action.{task_slug}.output",
      "dataType": "RECORD",
      "name": "Output",
      "slug": "output",
      "children": [
        {
          "absoluteSlug": "$action.{task_slug}.output.record",
          "dataType": "RECORD",
          "name": "Record",
          "slug": "record",
          "metaDataType": { "linkField": "id", "objectSlug": "{object_type_slug}", "object": "{OBJECT_TYPE_ID}" }
        },
        { "absoluteSlug": "$action.{task_slug}.output.result", "dataType": "NUMBER", "name": "Result", "slug": "result" },
        {
          "absoluteSlug": "$action.{task_slug}.output.records",
          "dataType": "RECORD",
          "isList": true,
          "name": "Records",
          "slug": "records",
          "metaDataType": { "linkField": "id", "objectSlug": "{object_type_slug}", "object": "{OBJECT_TYPE_ID}" }
        },
        { "absoluteSlug": "$action.{task_slug}.output.total", "dataType": "NUMBER", "name": "Total", "slug": "total" }
      ]
    }
  ]
}
```

Output dùng ở các bước sau: `$action.{slug}.output.record` bản ghi đơn (RECORD, liên kết object type đã cấu hình); `$action.{slug}.output.records` danh sách bản ghi (RECORD, `isList: true`); `$action.{slug}.output.total` tổng số bản ghi (NUMBER); `output.result` mã kết quả (NUMBER). `{OBJECT_TYPE_ID}`/`{object_type_slug}` trong `metaDataType` lấy từ `$object-info`. Mẫu Get Records lấy bản mới nhất của bản ghi trigger: [record-triggered-flow.md](record-triggered-flow.md#dữ-liệu-bản-ghi-trong-lượt-chạy).
