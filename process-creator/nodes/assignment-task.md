## Assignment Task (Task Gán Biến)

### Mô tả
Assignment Task là một task hệ thống tự động thực hiện các phép gán giá trị cho biến (Variable) khi luồng chạy đến. Cho phép gán giá trị từ biến/resource khác, thực hiện phép tính (cộng, trừ, nhân, chia), nối chuỗi, hoặc đếm số phần tử trong danh sách.

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

**Lưu ý:**
- Sử dụng `elEx:assignment` (cần namespace `xmlns:elEx="http://element-ex/schema"`)
- `renderKey="ASSIGNMENT"` — **QUAN TRỌNG: KHÔNG phải `ASSIGNMENT_TASK`**. Đây là ngoại lệ so với các action khác (GET_RECORD_TASK, LOOP_TASK, SEND_EMAIL_TASK, v.v. đều có hậu tố `_TASK`).
- Node ID dùng prefix `NO` như các node khác

### Cấu trúc Action trong mảng `actions` ở root level

**QUAN TRỌNG:** `data` sử dụng format array (mảng `assignments`), KHÔNG phải format object map.

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

### Validation (bắt buộc)

| Trường          | Yêu cầu                                                              |
|-----------------|----------------------------------------------------------------------|
| `name`          | Bắt buộc, tối thiểu 1 ký tự, tối đa theo giới hạn hệ thống         |
| `slug`          | Bắt buộc, format slug (snake_case), không trùng với action khác      |
| `left.value`    | Bắt buộc — phải chọn biến đích                                       |
| `operator`      | Bắt buộc — phải chọn toán tử                                         |
| `right.value`   | Bắt buộc — không được null/rỗng                                      |
| `right.raw`     | **Bắt buộc** (boolean) — backend parse bằng `getBoolean`, thiếu sẽ lỗi |

### Chi tiết các trường trong `data.assignments[]`

Mỗi phép gán là một phần tử trong mảng `assignments`:

| Trường                | Mô tả                                                                                            |
|-----------------------|--------------------------------------------------------------------------------------------------|
| `left`                | Biến đích (biến được gán giá trị)                                                                |
| `left.value`          | **Bắt buộc.** Đường dẫn tham chiếu biến đích (ví dụ: `$flow.bien_so`)                            |
| `left.valueDataType`  | Kiểu dữ liệu của biến đích (NUMBER, TEXT, BOOLEAN, DATE, DATE_TIME, RECORD, FILE, URL, SELECT_LIST) |
| `left.valuePathName`  | Tên hiển thị đường dẫn biến đích (ví dụ: `workflow_resource:list.variable / Biến số`)            |
| `index`               | Thứ tự phép gán (bắt đầu từ 0, tăng dần theo thứ tự trong mảng)                                 |
| `right`               | Giá trị nguồn (giá trị dùng để gán)                                                              |
| `right.raw`           | **Bắt buộc.** `true` nếu giá trị là hằng số nhập tay, `false` nếu là tham chiếu biến/resource    |
| `right.value`         | **Bắt buộc.** Khi `raw=true`: kiểu giá trị phụ thuộc biến đích — NUMBER gửi number (`1`, `3.14`), TEXT gửi string (`"abc"`). Khi `raw=false`: gửi đường dẫn tham chiếu string (`"$userTask.Root.so_b"`, `"$flow.bien_so"`) |
| `right.valueDataType` | Kiểu dữ liệu của giá trị nguồn                                                                   |
| `right.valuePathName` | Tên hiển thị đường dẫn nguồn (chỉ cần khi `raw=false`, tức tham chiếu biến/resource)              |
| `operator`            | **Bắt buộc.** Toán tử gán                                                                        |

### Cách sinh `valuePathName` và `valueDataType`

**`valuePathName`** — Đường dẫn hiển thị, dùng để người dùng đọc được tên biến/resource. Quy tắc sinh:

| Loại resource       | Format `valuePathName`                                                        | Ví dụ                                              |
|----------------------|-------------------------------------------------------------------------------|-----------------------------------------------------|
| Variable (custom)    | `workflow_resource:list.variable / {Tên biến}`                                | `workflow_resource:list.variable / Biến số`          |
| UserTask field       | `workflow_resource:list.userTask / {Tên userTask} / {Tên field}`              | `workflow_resource:list.userTask / Root / Số B`      |
| Action resource      | `workflow_resource:list.action / {Tên action} / {Tên resource}`               | `workflow_resource:list.action / Get Lead / Status`  |
| Assignment resource  | `workflow_resource:list.assignment / {Tên assignment} / {Tên resource}`        | `workflow_resource:list.assignment / Gán biến / Start At` |

**`valueDataType`** — Lấy từ `dataType` của resource/variable tương ứng. Các giá trị: `NUMBER`, `TEXT`, `BOOLEAN`, `DATE`, `DATE_TIME`, `RECORD`, `FILE`, `URL`, `SELECT_LIST`.

**Lưu ý:** Khi `right.raw` = `true` (hằng số nhập tay), `right.valuePathName` và `right.valueDataType` không cần thiết.

### Các toán tử gán (operator)

| Toán tử | Ý nghĩa       | Kiểu dữ liệu hỗ trợ | Mô tả                                              | Ví dụ                                                             |
|---------|---------------|-----------------------|----------------------------------------------------|------------------------------------------------------------------|
| `=`     | Gán           | Tất cả                | Gán giá trị nguồn cho biến đích                    | `Biến số 2 = Biến số`                                            |
| `+=`    | Cộng/Nối chuỗi | NUMBER, TEXT          | NUMBER: cộng giá trị nguồn vào biến đích. TEXT: nối chuỗi nguồn vào sau biến đích | `Biến số += Số B` hoặc `Tên += " Nguyễn"`                        |
| `-=`    | Trừ và gán    | NUMBER                | Trừ giá trị nguồn khỏi biến đích                   | `Biến số 3 -= Số A` (tương đương `Biến số 3 = Biến số 3 - Số A`) |
| `count` | Đếm           | Biến đích: NUMBER, Nguồn: danh sách (isList=true) | Đếm số phần tử trong danh sách (list size) | `Biến số 4 = count(Leads)`                                       |

**Lưu ý về `+=` với TEXT:** Khi biến đích có `valueDataType` là `TEXT`, toán tử `+=` sẽ nối chuỗi (string concatenation) thay vì cộng số.

**Lưu ý về `count`:** Giá trị nguồn (right) phải là một resource dạng danh sách (isList=true). Khi dùng `count`, phía front-end KHÔNG hiển thị ô nhập giá trị nguồn dạng input mà hiển thị dropdown chọn resource dạng list.

Chỉ sinh bốn operator `=`, `+=`, `-=`, `count` đã có nhánh xử lý runtime. Không suy rộng từ validation UI sang `*=` hoặc `/=`.

### Kiểm thử runtime

Không chỉ kiểm tra instance Completed. Đặt một Exclusive Gateway ngay sau Assignment để rẽ nhánh theo giá trị mong đợi:

- `+=` NUMBER: khởi tạo 5, cộng 2, kiểm tra bằng 7.
- `+=` TEXT: khởi tạo `A`, nối `B`, kiểm tra bằng `AB`.
- `-=` NUMBER: khởi tạo 8, trừ 3, kiểm tra bằng 5.
- `count`: nguồn phải là list thật; kiểm tra biến đích bằng số record đã biết.

Diagram phải cho thấy nhánh PASS đã chạy và nhánh default FAIL không chạy. Mỗi operator cần bằng chứng riêng; không suy rộng từ operator `=`.

### Resources của Assignment

Trong `resources.actions[]`, mỗi Assignment có 2 resource chuẩn:

```json
{
  "processId": "{PROCESS_ID}",
  "name": "{ASSIGNMENT_NAME}",
  "description": "",
  "resources": [
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
        "format": {
          "date": "dd/MM/yyyy",
          "time": "hh:mm:ss"
        },
        "timeZone": "Asia/Saigon"
      },
      "availableForOutput": true,
      "absolutePath": "workflow_resource:list.assignment / {ASSIGNMENT_NAME} / StartAt",
      "id": "{RESOURCE_ID}",
      "parentTable": "action",
      "slug": "startAt"
    },
    {
      "absoluteSlug": "$action.{assignment_slug}.endAt",
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
      "name": "End At",
      "metaDataType": {
        "defaultValueCurrent": false,
        "format": {
          "date": "dd/MM/yyyy",
          "time": "hh:mm:ss"
        },
        "timeZone": "Asia/Saigon"
      },
      "availableForOutput": true,
      "absolutePath": "workflow_resource:list.assignment / {ASSIGNMENT_NAME} / End At",
      "id": "{RESOURCE_ID}",
      "parentTable": "action",
      "slug": "endAt"
    }
  ],
  "id": "{ACTION_ID}",
  "type": "ASSIGNMENT",
  "nodeId": "{ASSIGNMENT_NODE_ID}",
  "slug": "{assignment_slug}"
}
```

**Lưu ý:**
- `absolutePath` dùng format `workflow_resource:list.assignment / {Name} / ...` (khác với các action khác dùng `list.action`)
- `parentTable` = `"action"`
- Trong create payload, action dùng cùng ID với BPMN node (`NO...` do skill sinh hoặc `Activity_*` từ modeler); resource dùng prefix `RS`. Response legacy có thể remap action ID thành `AC...`.

### resourcesUsedIn cho biến và resource dùng trong Assignment

Khi một biến (Variable) hoặc resource (trường trong userTask) được sử dụng trong Assignment, cần thêm `resourcesUsedIn`:

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

**Lưu ý:**
- `actionType` = `"ASSIGNMENT"` (phân biệt với các action type khác)
- `parentTable` = `"action"`
- `count` = số lần biến/resource xuất hiện trong tất cả các phép gán (cả left và right)
- Thêm vào cả Variable (trong `resources.custom`) và resource của userTask (trong `resources.userTasks[].resources[]`)

### Ví dụ đầy đủ

**Mô tả:** Start -> Root -> Gán Biến số bằng Số A cộng số B -> End Process

Với các phép gán:
1. `Biến số += Số B` (Biến số = Biến số + $userTask.Root.so_b)
2. `Biến số 2 = Biến số` (Biến số 2 = $flow.bien_so)
3. `Biến số 3 -= Số A` (Biến số 3 = Biến số 3 - $userTask.Root.so_a)
4. `Biến số 4 = count(Leads)` (Biến số 4 = Số lượng giá trị của $userTask.Root.leads)

**Action trong mảng `actions`:**
```json
{
  "data": {
    "assignments": [
      {
        "left": {
          "valuePathName": "workflow_resource:list.variable / Biến số",
          "valueDataType": "NUMBER",
          "value": "$flow.bien_so"
        },
        "index": 0,
        "right": {
          "raw": false,
          "valuePathName": "workflow_resource:list.userTask / Root / Số B",
          "valueDataType": "NUMBER",
          "value": "$userTask.Root.so_b"
        },
        "operator": "+="
      },
      {
        "left": {
          "valuePathName": "workflow_resource:list.variable / Biến số 2",
          "valueDataType": "NUMBER",
          "value": "$flow.bien_so_2"
        },
        "index": 1,
        "right": {
          "raw": false,
          "valuePathName": "workflow_resource:list.variable / Biến số",
          "valueDataType": "NUMBER",
          "value": "$flow.bien_so"
        },
        "operator": "="
      },
      {
        "left": {
          "valuePathName": "workflow_resource:list.variable / Biến số 3",
          "valueDataType": "NUMBER",
          "value": "$flow.bien_so_3"
        },
        "index": 2,
        "right": {
          "raw": false,
          "valuePathName": "workflow_resource:list.userTask / Root / Số A",
          "valueDataType": "NUMBER",
          "value": "$userTask.Root.so_a"
        },
        "operator": "-="
      },
      {
        "left": {
          "valuePathName": "workflow_resource:list.variable / Biến số 4",
          "valueDataType": "NUMBER",
          "value": "$flow.bien_so_4"
        },
        "index": 3,
        "right": {
          "raw": false,
          "valuePathName": "workflow_resource:list.userTask / Root / Leads",
          "valueDataType": "RECORD",
          "value": "$userTask.Root.leads"
        },
        "operator": "count"
      }
    ]
  },
  "processId": "{PROCESS_ID}",
  "name": "Gán Biến số bằng Số A cộng số B",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "ASSIGNMENT",
  "nodeId": "{ASSIGNMENT_NODE_ID}",
  "slug": "gan_bien_so_bang_so_a_cong_so_b"
}
```

**Ví dụ gán hằng số (raw=true):**
```json
{
  "left": {
    "valuePathName": "workflow_resource:list.variable / Tên khách",
    "valueDataType": "TEXT",
    "value": "$flow.ten_khach"
  },
  "index": 0,
  "right": {
    "raw": true,
    "value": "Nguyễn Văn A"
  },
  "operator": "="
}
```

**Lưu ý:** Khi `right.raw` = `true` (hằng số nhập tay), `right.valuePathName` và `right.valueDataType` không cần thiết.

**resourcesUsedIn cho Biến số (xuất hiện 2 lần: left trong phép gán 1 + right trong phép gán 2):**
```json
{
  "resourcesUsedIn": [
    {
      "actionType": "ASSIGNMENT",
      "name": "Gán Biến số bằng Số A cộng số B",
      "count": 2,
      "id": "{ACTION_ID}",
      "parentTable": "action",
      "slug": "gan_bien_so_bang_so_a_cong_so_b"
    }
  ]
}
```

---
