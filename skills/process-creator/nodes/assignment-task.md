## Assignment Task (Task Gán Biến)

Task hệ thống gán giá trị cho Variable khi luồng chạy đến: gán từ biến/resource khác, cộng/trừ, nối chuỗi hoặc đếm phần tử danh sách. Mẫu: `samples/sample_process_assignment.json`.

### Cấu trúc trong BPMN XML

```xml
<elEx:assignment id="{ASSIGNMENT_NODE_ID}" name="{ASSIGNMENT_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="ASSIGNMENT" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:assignment>
```

- `elEx:assignment` cần `xmlns:elEx="http://element-ex/schema"` trong `bpmn2:definitions`.
- `renderKey="ASSIGNMENT"`, KHÔNG phải `ASSIGNMENT_TASK`: ngoại lệ so với các action khác (`GET_RECORD_TASK`, `LOOP_TASK`, `SEND_EMAIL_TASK`... đều có hậu tố `_TASK`).

### Cấu trúc Action trong mảng `actions` ở root level

`data` dùng mảng `assignments`, KHÔNG phải object map.

```json
{
  "data": {
    "assignments": [
      {
        "left": {
          "valuePathName": "{VARIABLE_DISPLAY_PATH}",
          "valueDataType": "{DATA_TYPE}",
          "value": "{VARIABLE_ABSOLUTE_SLUG}"
        },
        "index": 0,
        "right": {
          "raw": false,
          "valuePathName": "{SOURCE_DISPLAY_PATH}",
          "valueDataType": "{SOURCE_DATA_TYPE}",
          "value": "{SOURCE_ABSOLUTE_SLUG}"
        },
        "operator": "{OPERATOR}"
      }
    ]
  },
  "processId": "{PROCESS_ID}",
  "name": "{ASSIGNMENT_NAME}",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "ASSIGNMENT",
  "nodeId": "{ASSIGNMENT_NODE_ID}",
  "slug": "{assignment_slug}"
}
```

| Trường | Yêu cầu |
|---|---|
| `name` | Bắt buộc, tối thiểu 1 ký tự, tối đa theo giới hạn hệ thống |
| `slug` | Bắt buộc, format slug (snake_case), không trùng với action khác |
| `left.value` | Bắt buộc. Đường dẫn tham chiếu biến đích, ví dụ `$flow.bien_so` |
| `left.valueDataType` | Kiểu dữ liệu biến đích: `NUMBER`, `TEXT`, `BOOLEAN`, `DATE`, `DATE_TIME`, `RECORD`, `FILE`, `URL`, `SELECT_LIST` |
| `left.valuePathName` | Tên hiển thị đường dẫn biến đích (bảng dưới) |
| `index` | Thứ tự phép gán, bắt đầu từ `0`, tăng dần theo thứ tự trong mảng |
| `right.raw` | Bắt buộc, boolean: `true` nếu giá trị là hằng số nhập tay, `false` nếu là tham chiếu biến/resource. Backend parse bằng `getBoolean`, thiếu sẽ lỗi |
| `right.value` | Bắt buộc, không null/rỗng. `raw: true`: kiểu giá trị theo biến đích (NUMBER gửi number `1`, `3.14`; TEXT gửi string `"abc"`). `raw: false`: chuỗi đường dẫn tham chiếu (`"$userTask.Root.so_b"`, `"$flow.bien_so"`) |
| `right.valueDataType`, `right.valuePathName` | Chỉ cần khi `raw: false`; không cần khi `raw: true`. `valueDataType` lấy từ `dataType` của resource/biến nguồn |
| `operator` | Bắt buộc, một trong bốn toán tử dưới |

`valuePathName` theo loại resource:

| Loại resource | Format | Ví dụ |
|---|---|---|
| Variable (custom) | `workflow_resource:list.variable / {Tên biến}` | `workflow_resource:list.variable / Biến số` |
| Field của User Task | `workflow_resource:list.userTask / {Tên userTask} / {Tên field}` | `workflow_resource:list.userTask / Root / Số B` |
| Resource của action | `workflow_resource:list.action / {Tên action} / {Tên resource}` | `workflow_resource:list.action / Get Lead / Status` |
| Resource của Assignment | `workflow_resource:list.assignment / {Tên assignment} / {Tên resource}` | `workflow_resource:list.assignment / Gán biến / Start At` |

### Các toán tử gán (operator)

| `operator` | Kiểu dữ liệu hỗ trợ | Mô tả | Ví dụ |
|---|---|---|---|
| `=` | Tất cả | Gán giá trị nguồn cho biến đích | `Biến số 2 = Biến số` |
| `+=` | NUMBER, TEXT | NUMBER: cộng giá trị nguồn vào biến đích. TEXT: nối chuỗi nguồn vào sau biến đích | `Biến số += Số B`, `Tên += " Nguyễn"` |
| `-=` | NUMBER | Trừ giá trị nguồn khỏi biến đích | `Biến số 3 -= Số A` |
| `count` | Biến đích NUMBER; nguồn là resource dạng danh sách (`isList: true`, `raw: false`) | Gán số phần tử của danh sách (list size); front-end hiển thị dropdown chọn resource dạng list thay vì ô nhập giá trị | `Biến số 4 = count(Leads)` |

Chỉ sinh bốn toán tử trên (đã có nhánh xử lý runtime); không suy rộng từ validation UI sang `*=` hoặc `/=`.

Ví dụ phép gán `count` với nguồn là lookup nhiều giá trị (`valueDataType: "RECORD"`) và phép gán hằng số (`raw: true`):

```json
[
  {
    "left": { "valuePathName": "workflow_resource:list.variable / Biến số 4", "valueDataType": "NUMBER", "value": "$flow.bien_so_4" },
    "index": 0,
    "right": { "raw": false, "valuePathName": "workflow_resource:list.userTask / Root / Leads", "valueDataType": "RECORD", "value": "$userTask.Root.leads" },
    "operator": "count"
  },
  {
    "left": { "valuePathName": "workflow_resource:list.variable / Tên khách", "valueDataType": "TEXT", "value": "$flow.ten_khach" },
    "index": 1,
    "right": { "raw": true, "value": "Nguyễn Văn A" },
    "operator": "="
  }
]
```

### Kiểm thử runtime

Không chỉ kiểm tra instance Completed. Đặt một Exclusive Gateway ngay sau Assignment để rẽ nhánh theo giá trị mong đợi: `+=` NUMBER khởi tạo 5, cộng 2, kiểm tra bằng 7; `+=` TEXT khởi tạo `A`, nối `B`, kiểm tra bằng `AB`; `-=` NUMBER khởi tạo 8, trừ 3, kiểm tra bằng 5; `count` nguồn phải là list thật, kiểm tra biến đích bằng số record đã biết. Diagram phải cho thấy nhánh PASS đã chạy và nhánh default FAIL không chạy. Mỗi operator cần bằng chứng riêng; không suy rộng từ operator `=`.

### Resources của Assignment

Trong `resources.actions[]`, mỗi Assignment là một nhóm `{"processId", "name", "description": "", "resources": [...], "id": "{ACTION_ID}", "type": "ASSIGNMENT", "nodeId": "{ASSIGNMENT_NODE_ID}", "slug": "{assignment_slug}"}` với 2 resource chuẩn:

```json
{
  "absoluteSlug": "$action.{assignment_slug}.startAt",
  "parentMetadata": "",
  "editable": false,
  "dataType": "DATE_TIME",
  "type": 1,
  "isList": false,
  "parentId": "{ACTION_ID}",
  "assignable": false,
  "availableForInput": true,
  "isStandard": true,
  "processId": "{PROCESS_ID}",
  "name": "Start At",
  "metaDataType": {
    "defaultValueCurrent": false,
    "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
    "timeZone": "Asia/Saigon"
  },
  "availableForOutput": true,
  "absolutePath": "workflow_resource:list.assignment / {ASSIGNMENT_NAME} / StartAt",
  "id": "{RESOURCE_ID}",
  "parentTable": "action",
  "slug": "startAt"
}
```

Resource thứ hai giống hệt, chỉ khác `absoluteSlug: "$action.{assignment_slug}.endAt"`, `name: "End At"`, `absolutePath: "workflow_resource:list.assignment / {ASSIGNMENT_NAME} / End At"`, `slug: "endAt"` và `id` riêng (prefix `RS`). `absolutePath` dùng format `workflow_resource:list.assignment / {Name} / ...` (khác các action khác dùng `list.action`); `parentTable` = `"action"`.

### `resourcesUsedIn` cho biến và resource dùng trong Assignment

Biến (Variable trong `resources.custom`) và resource trường userTask (`resources.userTasks[].resources[]`) được dùng trong Assignment phải có:

```json
{
  "resourcesUsedIn": [
    {
      "actionType": "ASSIGNMENT",
      "name": "{ASSIGNMENT_NAME}",
      "count": {SỐ_LẦN_SỬ_DỤNG},
      "id": "{ACTION_ID}",
      "parentTable": "action",
      "slug": "{assignment_slug}"
    }
  ]
}
```

`count` = số lần biến/resource xuất hiện trong tất cả các phép gán, tính cả `left` và `right` (ví dụ Biến số ở `left` phép gán 1 và `right` phép gán 2 → `count: 2`).
