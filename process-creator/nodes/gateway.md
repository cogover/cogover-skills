## Exclusive Gateway

### Mô tả
Exclusive Gateway (Cổng loại trừ) là loại gateway chỉ cho phép **một nhánh duy nhất** được thực thi dựa trên điều kiện. Nếu không có nhánh nào thỏa mãn điều kiện, nhánh **mặc định** sẽ được chạy.

### Cấu trúc trong BPMN XML
```xml
<bpmn2:exclusiveGateway id="{GATEWAY_NODE_ID}" name="{GATEWAY_NAME}" default="{DEFAULT_FLOW_ID}">
  <bpmn2:extensionElements>
    <configEx:elementInfo openedGateway="true" />
    <configEx:elementInfo renderKey="EXCLUSIVE_GATEWAY" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{DEFAULT_FLOW_ID}</bpmn2:outgoing>
  <bpmn2:outgoing>{CONDITION_FLOW_ID}</bpmn2:outgoing>
</bpmn2:exclusiveGateway>
```

**Lưu ý quan trọng:**
- Thuộc tính `default` chỉ định ID của flow mặc định
- `renderKey="EXCLUSIVE_GATEWAY"`
- `openedGateway="true"` cho biết gateway đã được cấu hình

### Cấu trúc `gateWays` trong JSON
Thêm section `gateWays` vào JSON với cấu trúc sau:
```json
{
  "gateWays": [
    {
      "isOpen": true,
      "sourceNodeId": "{GATEWAY_NODE_ID}",
      "name": "{GATEWAY_NAME}",
      "description": "",
      "slug": "{gateway_slug}",
      "decisionOutcomes": [
        {
          "outcomeOrder": -1,
          "isDefault": true,
          "logicType": "AND",
          "targetId": "{TARGET_NODE_ID}",
          "color": "#939393",
          "customConditionLogic": "",
          "processId": "{PROCESS_ID}",
          "name": "Mặc định",
          "id": "{DECISION_OUTCOME_ID}",
          "flowId": "{DEFAULT_FLOW_ID}",
          "slug": "_default"
        },
        {
          "outcomeOrder": 0,
          "isDefault": false,
          "logicType": "AND|OR|CUSTOM",
          "targetId": "{TARGET_NODE_ID}",
          "color": "{COLOR}",
          "customConditionLogic": "{LOGIC_EXPRESSION}",
          "processId": "{PROCESS_ID}",
          "name": "{CONDITION_NAME}",
          "id": "{DECISION_OUTCOME_ID}",
          "conditions": [
            {
              "leftValueDataType": "{DATA_TYPE}",
              "decisionOutcomeId": "{DECISION_OUTCOME_ID}",
              "processId": "{PROCESS_ID}",
              "leftValue": "{VARIABLE_PATH}",
              "leftValueIsList": false,
              "conditionOrder": 1,
              "rightValue": "{VALUE_DEPENDS_ON_DATA_TYPE_AND_OPERATOR}",
              "valueType": 1,
              "id": "{CONDITION_ID}",
              "leftValueName": "{VARIABLE_DISPLAY_NAME}",
              "leftValueMetaDataType": {"...": "..."},
              "operator": "{OPERATOR_DEPENDS_ON_DATA_TYPE_AND_IS_LIST}"
            }
          ],
          "flowId": "{CONDITION_FLOW_ID}",
          "slug": "{condition_slug}"
        }
      ]
    }
  ]
}
```

**Lưu ý về `logicType` và `customConditionLogic`:**
- `logicType: "AND"` → `customConditionLogic: "1 AND 2 AND ... AND N"`
- `logicType: "OR"` → `customConditionLogic: "1 OR 2 OR ... OR N"`
- `logicType: "CUSTOM"` → `customConditionLogic` do người dùng cung cấp (ví dụ: `"1 AND (2 OR 3) AND 4"`)
- Nhánh mặc định (`isDefault: true`): không có `conditions`, `customConditionLogic` là `""`

### Loại logic điều kiện (logicType) và customConditionLogic

Mỗi `decisionOutcome` (nhánh) có thuộc tính `logicType` xác định cách kết hợp các điều kiện:

#### 1. `logicType: "AND"` - Tất cả điều kiện phải đúng
- `customConditionLogic` tự động sinh: `"1 AND 2 AND 3 AND ... AND N"` (với N = số điều kiện)
- Tất cả các điều kiện phải thỏa mãn thì nhánh mới được chọn

#### 2. `logicType: "OR"` - Ít nhất một điều kiện đúng
- `customConditionLogic` tự động sinh: `"1 OR 2 OR 3 OR ... OR N"` (với N = số điều kiện)
- Chỉ cần một điều kiện thỏa mãn thì nhánh được chọn

#### 3. `logicType: "CUSTOM"` - Logic tùy chỉnh
- `customConditionLogic` do người dùng định nghĩa, ví dụ: `"1 AND (2 OR 3) AND 4"`
- Các số (1, 2, 3, ...) tương ứng với `conditionOrder` của từng điều kiện
- Hỗ trợ kết hợp AND, OR và dấu ngoặc đơn `()` để nhóm logic

**Ví dụ:**
```json
{
  "logicType": "AND",
  "customConditionLogic": "1 AND 2 AND 3",
  "conditions": [
    { "conditionOrder": 1, "..." : "..." },
    { "conditionOrder": 2, "..." : "..." },
    { "conditionOrder": 3, "..." : "..." }
  ]
}
```

```json
{
  "logicType": "CUSTOM",
  "customConditionLogic": "1 AND (2 OR 3) AND 4",
  "conditions": [
    { "conditionOrder": 1, "..." : "..." },
    { "conditionOrder": 2, "..." : "..." },
    { "conditionOrder": 3, "..." : "..." },
    { "conditionOrder": 4, "..." : "..." }
  ]
}
```

### Cấu trúc một điều kiện (condition)

```json
{
  "leftValueDataType": "{DATA_TYPE}",
  "decisionOutcomeId": "{DECISION_OUTCOME_ID}",
  "processId": "{PROCESS_ID}",
  "leftValue": "{VARIABLE_PATH}",
  "leftValueIsList": false,
  "conditionOrder": 1,
  "rightValue": "{VALUE}",
  "valueType": 1,
  "id": "{CONDITION_ID}",
  "leftValueName": "{VARIABLE_DISPLAY_NAME}",
  "leftValueMetaDataType": { "..." : "..." },
  "operator": "{OPERATOR}"
}
```

**Các trường bổ sung theo kiểu dữ liệu:**
- Với `RECORD`: thêm `"leftObjectTypeId": "{OBJECT_TYPE_ID}"` (ID của object type — lấy từ skill `/object-info`, xem mục 25 trong Lưu ý quan trọng)

**Các trường bổ sung khi `valueType` = 2 (giá trị lấy từ resource khác):**
- `"rightValueName": "{RIGHT_VARIABLE_DISPLAY_NAME}"` — tên hiển thị của biến bên phải
- `"rightValueDataType": "{RIGHT_DATA_TYPE}"` — kiểu dữ liệu của biến bên phải
- `"rightValueIsList": false` — biến bên phải có phải danh sách không

**Lưu ý:**
- `conditionOrder` bắt đầu từ 1 và tăng dần
- `valueType`: `1` = giá trị cố định (literal), `2` = giá trị lấy từ resource khác (khi đó cần thêm `rightValueName`, `rightValueDataType`, `rightValueIsList`)
- `rightValue` **không có** khi operator là: `IS_NULL`, `IS_NOT_NULL`, `LIST_IS_EMPTY`, `LIST_IS_NOT_EMPTY`
- `leftValueMetaDataType` copy từ resource metadata của trường tương ứng

### Cú pháp biến điều kiện (leftValue)
- Tham chiếu đến trường trong userTask: `$userTask.{task_slug}.{field_slug}`
  - Ví dụ: `$userTask.Root.so_ngay_xin_nghi`
- Tham chiếu đến output của action: `$action.{action_slug}.output`
  - Ví dụ: `$action.cong_viec_2.output`

### Các toán tử điều kiện (operator) theo kiểu dữ liệu

#### NUMBER (leftValueIsList: false)
| Operator      | Mô tả             | rightValue      |
|---------------|-------------------|-----------------|
| `>=`          | Lớn hơn hoặc bằng | Số (ví dụ: `5`) |
| `<=`          | Nhỏ hơn hoặc bằng | Số (ví dụ: `5`) |
| `>`           | Lớn hơn           | Số (ví dụ: `5`) |
| `<`           | Nhỏ hơn           | Số (ví dụ: `5`) |
| `==`          | Bằng              | Số (ví dụ: `5`) |
| `!=`          | Khác              | Số (ví dụ: `5`) |
| `IS_NULL`     | Là null           | `"null"`        |
| `IS_NOT_NULL` | Không null        | `"null"`        |

#### NUMBER (leftValueIsList: true)
| Operator            | Mô tả                        | rightValue      |
|---------------------|------------------------------|-----------------|
| `LIST_CONTAINS`     | Danh sách chứa giá trị       | Số (ví dụ: `1`) |
| `LIST_NOT_CONTAINS` | Danh sách không chứa giá trị | Số (ví dụ: `1`) |

#### DATE (leftValueIsList: false)
| Operator      | Mô tả             | rightValue                                        |
|---------------|-------------------|---------------------------------------------------|
| `==`          | Bằng              | Chuỗi ngày `"YYYY-MM-DD"` (ví dụ: `"2026-02-01"`) |
| `!=`          | Khác              | Chuỗi ngày `"YYYY-MM-DD"`                         |
| `>=`          | Lớn hơn hoặc bằng | Chuỗi ngày `"YYYY-MM-DD"`                         |
| `<=`          | Nhỏ hơn hoặc bằng | Chuỗi ngày `"YYYY-MM-DD"`                         |
| `>`           | Lớn hơn           | Chuỗi ngày `"YYYY-MM-DD"`                         |
| `<`           | Nhỏ hơn           | Chuỗi ngày `"YYYY-MM-DD"`                         |
| `IS_NULL`     | Là null           | `"null"`                                          |
| `IS_NOT_NULL` | Không null        | `"null"`                                          |

#### DATE (leftValueIsList: true)
| Operator            | Mô tả                     | rightValue                |
|---------------------|---------------------------|---------------------------|
| `LIST_CONTAINS`     | Danh sách chứa ngày       | Chuỗi ngày `"YYYY-MM-DD"` |
| `LIST_NOT_CONTAINS` | Danh sách không chứa ngày | Chuỗi ngày `"YYYY-MM-DD"` |

#### DATE_TIME (leftValueIsList: false)
| Operator      | Mô tả             | rightValue                                     |
|---------------|-------------------|------------------------------------------------|
| `==`          | Bằng              | Timestamp millisecond (ví dụ: `1770570900000`) |
| `!=`          | Khác              | Timestamp millisecond                          |
| `>=`          | Lớn hơn hoặc bằng | Timestamp millisecond                          |
| `<=`          | Nhỏ hơn hoặc bằng | Timestamp millisecond                          |
| `>`           | Lớn hơn           | Timestamp millisecond                          |
| `<`           | Nhỏ hơn           | Timestamp millisecond                          |
| `IS_NULL`     | Là null           | `"null"`                                       |
| `IS_NOT_NULL` | Không null        | `"null"`                                       |

#### BOOLEAN (leftValueIsList: false)
| Operator      | Mô tả      | rightValue          |
|---------------|-----------|---------------------|
| `==`          | Bằng       | `true` hoặc `false` |
| `!=`          | Khác       | `true` hoặc `false` |
| `IS_NULL`     | Là null    | `"null"`            |
| `IS_NOT_NULL` | Không null | `"null"`            |

#### TEXT (leftValueIsList: false)
| Operator            | Mô tả            | rightValue              |
|---------------------|------------------|-------------------------|
| `==`                | Bằng              | Chuỗi (ví dụ: `"abc"`)  |
| `!=`                | Khác              | Chuỗi (ví dụ: `"abc"`)  |
| `TEXT_CONTAINS`     | Chứa chuỗi       | Chuỗi (ví dụ: `"text"`) |
| `TEXT_NOT_CONTAINS` | Không chứa chuỗi | Chuỗi (ví dụ: `"text"`) |
| `STARTS_WITH`       | Bắt đầu bằng     | Chuỗi (ví dụ: `"Abc"`)  |
| `ENDS_WITH`         | Kết thúc bằng    | Chuỗi (ví dụ: `"def"`)  |
| `IS_NULL`           | Là null           | `"null"`                |
| `IS_NOT_NULL`       | Không null        | `"null"`                |

#### TEXT (leftValueIsList: true)
| Operator            | Mô tả                      | rightValue           |
|---------------------|----------------------------|----------------------|
| `LIST_CONTAINS`     | Danh sách chứa chuỗi       | Chuỗi (ví dụ: `"1"`) |
| `LIST_NOT_CONTAINS` | Danh sách không chứa chuỗi | Chuỗi                |

#### SELECT_LIST (leftValueIsList: false) - Lựa chọn đơn
| Operator        | Mô tả                | rightValue                                                         |
|-----------------|----------------------|--------------------------------------------------------------------|
| `==`            | Bằng                 | Giá trị lựa chọn - chuỗi hoặc số (ví dụ: `"Lựa chọn 1"` hoặc `1`)  |
| `!=`            | Khác                 | Giá trị lựa chọn                                                   |
| `IS_ONE_OF`     | Là một trong         | Mảng giá trị (ví dụ: `["Lựa chọn 1", "Lựa chọn 2"]` hoặc `[1, 2]`) |
| `IS_NOT_ONE_OF` | Không phải một trong | Mảng giá trị                                                       |
| `LIST_IS_EMPTY` | Chưa chọn giá trị    | Không có                                                           |

#### SELECT_LIST (leftValueIsList: true) - Lựa chọn nhiều
| Operator                   | Mô tả                                 | rightValue                                        |
|----------------------------|---------------------------------------|---------------------------------------------------|
| `SELECT_LIST_CONTAINS`     | Danh sách chứa giá trị lựa chọn       | Mảng giá trị (ví dụ: `["Lựa chọn 1"]` hoặc `[1]`) |
| `SELECT_LIST_NOT_CONTAINS` | Danh sách không chứa giá trị lựa chọn | Mảng giá trị                                      |
| `LIST_IS_EMPTY`            | Danh sách rỗng                        | Không có                                          |
| `LIST_IS_NOT_EMPTY`        | Danh sách không rỗng                  | Không có                                          |

**Lưu ý:** Khi `leftValueDataType` là `SELECT_LIST` và `leftValueIsList: true`, sử dụng `SELECT_LIST_CONTAINS` / `SELECT_LIST_NOT_CONTAINS` thay vì `LIST_CONTAINS` / `LIST_NOT_CONTAINS`. `rightValue` luôn là mảng.

#### RECORD (leftValueIsList: false) - Tra cứu đơn
| Operator      | Mô tả        | rightValue                             |
|---------------|--------------|----------------------------------------|
| `==`          | Bằng bản ghi | ID bản ghi (ví dụ: `"LE000000000001"`) |
| `IS_NULL`     | Là null      | `"null"`                               |
| `IS_NOT_NULL` | Không null   | `"null"`                               |

**Lưu ý:** Điều kiện RECORD có thêm trường `leftObjectTypeId` chứa ID của object type — **BẮT BUỘC** lấy từ skill `/object-info` (xem mục 25 trong Lưu ý quan trọng).

#### RECORD (leftValueIsList: true) - Tra cứu nhiều
| Operator            | Mô tả                        | rightValue                             |
|---------------------|------------------------------|----------------------------------------|
| `LIST_CONTAINS`     | Danh sách chứa bản ghi       | ID bản ghi (ví dụ: `"LE000000000001"`) |
| `LIST_NOT_CONTAINS` | Danh sách không chứa bản ghi | ID bản ghi                             |

### Ví dụ điều kiện theo từng kiểu dữ liệu

#### NUMBER (đơn giá trị): so >= 5
```json
{
  "leftValueDataType": "NUMBER",
  "leftValue": "$userTask.nhap_nhan_su_onboard.so",
  "leftValueIsList": false,
  "conditionOrder": 1,
  "rightValue": 5,
  "valueType": 1,
  "operator": ">="
}
```

#### NUMBER (nhiều giá trị): so_nhieu chứa 1
```json
{
  "leftValueDataType": "NUMBER",
  "leftValue": "$userTask.nhap_nhan_su_onboard.so_nhieu",
  "leftValueIsList": true,
  "conditionOrder": 6,
  "rightValue": 1,
  "valueType": 1,
  "operator": "LIST_CONTAINS"
}
```

#### DATE (đơn giá trị): ngay == 2026-02-01
```json
{
  "leftValueDataType": "DATE",
  "leftValue": "$userTask.nhap_nhan_su_onboard.ngay",
  "leftValueIsList": false,
  "conditionOrder": 16,
  "rightValue": "2026-02-01",
  "valueType": 1,
  "operator": "=="
}
```

#### DATE_TIME (đơn giá trị): ngay_gio == timestamp
```json
{
  "leftValueDataType": "DATE_TIME",
  "leftValue": "$userTask.nhap_nhan_su_onboard.ngay_gio",
  "leftValueIsList": false,
  "conditionOrder": 10,
  "rightValue": 1770570900000,
  "valueType": 1,
  "operator": "=="
}
```

#### TEXT (đơn giá trị): chu chứa "text"
```json
{
  "leftValueDataType": "TEXT",
  "leftValue": "$userTask.nhap_nhan_su_onboard.chu",
  "leftValueIsList": false,
  "conditionOrder": 26,
  "rightValue": "text",
  "valueType": 1,
  "operator": "TEXT_CONTAINS"
}
```

#### TEXT (đơn giá trị): chu bắt đầu bằng "Abc"
```json
{
  "leftValueDataType": "TEXT",
  "leftValue": "$userTask.nhap_nhan_su_onboard.chu",
  "leftValueIsList": false,
  "conditionOrder": 29,
  "rightValue": "Abc",
  "valueType": 1,
  "operator": "STARTS_WITH"
}
```

#### SELECT_LIST: lua_chon_1 == "Lựa chọn 1"
```json
{
  "leftValueDataType": "SELECT_LIST",
  "leftValue": "$userTask.nhap_nhan_su_onboard.lua_chon_1",
  "leftValueIsList": false,
  "conditionOrder": 2,
  "rightValue": "Lựa chọn 1",
  "valueType": 1,
  "operator": "=="
}
```

#### SELECT_LIST: lua_chon_1 IS_ONE_OF ["Lựa chọn 1", "Lựa chọn 2"]
```json
{
  "leftValueDataType": "SELECT_LIST",
  "leftValue": "$userTask.nhap_nhan_su_onboard.lua_chon_1",
  "leftValueIsList": false,
  "conditionOrder": 4,
  "rightValue": ["Lựa chọn 1", "Lựa chọn 2"],
  "valueType": 1,
  "operator": "IS_ONE_OF"
}
```

#### SELECT_LIST (kiểu số): lua_chon_so IS_ONE_OF [1, 2]
```json
{
  "leftValueDataType": "SELECT_LIST",
  "leftValue": "$userTask.nhap_nhan_su_onboard.lua_chon_so",
  "leftValueIsList": false,
  "conditionOrder": 6,
  "rightValue": [1, 2],
  "valueType": 1,
  "operator": "IS_ONE_OF"
}
```

#### SELECT_LIST (nhiều giá trị): lua_chon_nhieu SELECT_LIST_CONTAINS ["Lựa chọn 1"]
```json
{
  "leftValueDataType": "SELECT_LIST",
  "leftValue": "$userTask.nhap_nhan_su_onboard.lua_chon_nhieu",
  "leftValueIsList": true,
  "conditionOrder": 7,
  "rightValue": ["Lựa chọn 1"],
  "valueType": 1,
  "operator": "SELECT_LIST_CONTAINS"
}
```

#### RECORD (đơn giá trị): tra_cuu_den_lead == record ID
```json
{
  "leftValueDataType": "RECORD",
  "leftObjectTypeId": "OT00000000011",
  "leftValue": "$userTask.nhap_nhan_su_onboard.tra_cuu_den_lead",
  "leftValueIsList": false,
  "conditionOrder": 12,
  "rightValue": "LE000000000001",
  "valueType": 1,
  "operator": "=="
}
```

#### RECORD (nhiều giá trị): tra_cuu_lead_nhieu chứa record
```json
{
  "leftObjectTypeId": "OT00000000011",
  "leftValueDataType": "RECORD",
  "leftValue": "$userTask.nhap_nhan_su_onboard.tra_cuu_lead_nhieu",
  "leftValueIsList": true,
  "conditionOrder": 11,
  "rightValue": "LE000000000001",
  "valueType": 1,
  "operator": "LIST_CONTAINS"
}
```

#### Operator IS_NULL / IS_NOT_NULL (không có rightValue)
```json
{
  "leftValueDataType": "NUMBER",
  "leftValue": "$userTask.nhap_nhan_su_onboard.so",
  "leftValueIsList": false,
  "conditionOrder": 2,
  "rightValue": "null",
  "valueType": 1,
  "operator": "IS_NOT_NULL"
}
```

**Lưu ý:** Với `IS_NULL` và `IS_NOT_NULL`, `rightValue` là chuỗi `"null"`.

#### BOOLEAN (đơn giá trị): da_xac_nhan == true
```json
{
  "leftValueDataType": "BOOLEAN",
  "leftValue": "$userTask.nhap_nhan_su_onboard.da_xac_nhan",
  "leftValueIsList": false,
  "conditionOrder": 1,
  "rightValue": true,
  "valueType": 1,
  "operator": "=="
}
```

#### TEXT (đơn giá trị): chu == "abc"
```json
{
  "leftValueDataType": "TEXT",
  "leftValue": "$userTask.nhap_nhan_su_onboard.chu",
  "leftValueIsList": false,
  "conditionOrder": 1,
  "rightValue": "abc",
  "valueType": 1,
  "operator": "=="
}
```

### Màu sắc nhánh
- Nhánh mặc định: `#939393` (xám)
- Các nhánh có điều kiện sử dụng các màu khác nhau, ví dụ: `#4CAF50` (xanh lá), `#ED5044` (đỏ), `#FAD000` (vàng), v.v.

### Cập nhật Resources khi sử dụng Gateway
Khi một trường được sử dụng trong điều kiện Gateway, cần thêm `resourcesUsedIn` vào resource của trường đó:
```json
{
  "resourcesUsedIn": [
    {
      "name": "{GATEWAY_NAME}",
      "gateWayType": "EXCLUSIVE_GATEWAY",
      "count": 1,
      "id": "{GATEWAY_NODE_ID}",
      "parentTable": "decision_outcome",
      "slug": "{gateway_slug}"
    }
  ]
}
```

---

## ⚠️ RÀNG BUỘC QUAN TRỌNG: Exclusive Gateway không được vừa Merge vừa Fork

**Cogover KHÔNG cho phép** một Exclusive Gateway có **nhiều incoming VÀ nhiều outgoing** cùng lúc (lỗi: `GATEWAY_CAN_NOT_BE_BOTH_MERGE_AND_FORK`).

Một Exclusive Gateway phải là **một trong hai**:
- **Fork** (phân nhánh): 1 incoming, nhiều outgoing — có `default`, có `decisionOutcomes`
- **Merge** (hội tụ): nhiều incoming, 1 outgoing — không có `default`, không có `decisionOutcomes`

### Pattern sai (gây lỗi)

Khi cần "nếu đúng → làm gì đó → tiếp tục", pattern sau **bị lỗi** vì `EGW_B` có 2 incoming + 2 outgoing:

```
EGW_A (fork) → [TRUE] → Task → EGW_B (merge+fork = LỖI)
             → [default] ─────────────────────↗
```

### Pattern đúng: dùng Merge Gateway riêng

Thêm một **Exclusive Gateway merge-only** trước EGW fork tiếp theo:

```
EGW_A (fork) → [TRUE] → Task → MERGE_B (merge: 2 in, 1 out) → EGW_B (fork: 1 in, 2 out)
             → [default] ──────────────────────────────────────↗
```

### Cấu trúc Merge-only Exclusive Gateway

**BPMN XML** (không có `default`, không có `openedGateway`):
```xml
<bpmn2:exclusiveGateway id="{MERGE_NODE_ID}" name="{MERGE_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="EXCLUSIVE_GATEWAY" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_1}</bpmn2:incoming>
  <bpmn2:incoming>{INCOMING_FLOW_2}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW}</bpmn2:outgoing>
</bpmn2:exclusiveGateway>
```

**JSON trong `gateWays`** (`isOpen: false`, `decisionOutcomes: []`):
```json
{
  "isOpen": false,
  "sourceNodeId": "{MERGE_NODE_ID}",
  "name": "{MERGE_NAME}",
  "description": "",
  "slug": "{merge_slug}",
  "decisionOutcomes": []
}
```

### Ví dụ thực tế: kiểm tra boolean từ triggered flow

Khi cần kiểm tra 3 field boolean liên tiếp (`is_a`, `is_b`, `is_c`):

```
Start → EGW_ISA (fork) → [TRUE] → ASS_ISA → MERGE_ISB (merge) → EGW_ISB (fork) → ...
                        → [default] ──────────────────────────────↗
```

Mỗi cặp `EGW_fork → merge → EGW_fork_tiếp` tạo thành một "checkpoint" hội tụ trước khi phân nhánh tiếp theo. Cần N merge gateway cho N lần hội tụ.

---

## Inclusive Gateway

### Mô tả
Inclusive Gateway (Cổng bao gồm) là loại gateway cho phép **nhiều nhánh đúng cùng lúc** và chạy ra theo tất cả các nhánh thỏa mãn điều kiện. Nếu không có nhánh nào thỏa mãn điều kiện, nhánh **mặc định** sẽ được chạy.

Mỗi Inclusive Gateway mở nhánh (`openedGateway="true"`) **bắt buộc** phải có một Inclusive Gateway đóng nhánh (`openedGateway="false"`) tương ứng để đồng bộ các nhánh trước khi tiếp tục quy trình.

**Ngoại lệ:** Nếu tất cả các nhánh đều kết thúc tại End Event (không cần hội tụ), thì **không cần** gateway đóng nhánh.

### Cấu trúc trong BPMN XML

#### Inclusive Gateway mở nhánh (Opening) — không có nhánh mặc định
```xml
<bpmn2:inclusiveGateway id="{GATEWAY_NODE_ID}" name="{GATEWAY_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo openedGateway="true" />
    <configEx:elementInfo renderKey="INCLUSIVE_GATEWAY" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_1}</bpmn2:outgoing>
  <bpmn2:outgoing>{OUTGOING_FLOW_2}</bpmn2:outgoing>
</bpmn2:inclusiveGateway>
```

#### Inclusive Gateway mở nhánh (Opening) — có nhánh mặc định
```xml
<bpmn2:inclusiveGateway default="{DEFAULT_FLOW_ID}" id="{GATEWAY_NODE_ID}" name="{GATEWAY_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo openedGateway="true" />
    <configEx:elementInfo renderKey="INCLUSIVE_GATEWAY" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{DEFAULT_FLOW_ID}</bpmn2:outgoing>
  <bpmn2:outgoing>{CONDITION_FLOW_ID}</bpmn2:outgoing>
</bpmn2:inclusiveGateway>
```

#### Inclusive Gateway đóng nhánh (Closing)
```xml
<bpmn2:inclusiveGateway id="{CLOSING_GATEWAY_NODE_ID}" name="{CLOSING_GATEWAY_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo openedGateway="false" />
    <configEx:elementInfo renderKey="INCLUSIVE_GATEWAY" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_FROM_BRANCH_1}</bpmn2:incoming>
  <bpmn2:incoming>{INCOMING_FLOW_FROM_BRANCH_2}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</bpmn2:inclusiveGateway>
```

**Lưu ý quan trọng:**
- `renderKey="INCLUSIVE_GATEWAY"`
- Gateway mở nhánh: `openedGateway="true"` - có nhiều outgoing flow (mỗi nhánh một flow)
- Gateway đóng nhánh: `openedGateway="false"` - có nhiều incoming flow (từ các nhánh) và một outgoing flow
- Nếu có nhánh mặc định, thêm thuộc tính `default="{DEFAULT_FLOW_ID}"` vào gateway mở nhánh

### Cấu trúc `gateWays` trong JSON
Thêm **2 phần tử** vào mảng `gateWays`: một cho gateway mở nhánh và một cho gateway đóng nhánh.
```json
{
  "gateWays": [
    {
      "isOpen": true,
      "sourceNodeId": "{GATEWAY_NODE_ID}",
      "name": "{GATEWAY_NAME}",
      "description": "",
      "slug": "{gateway_slug}",
      "decisionOutcomes": [
        {
          "outcomeOrder": 0,
          "isDefault": false,
          "logicType": "AND",
          "targetId": "{TARGET_NODE_ID_BRANCH_1}",
          "color": "#4CAF50",
          "customConditionLogic": "",
          "processId": "{PROCESS_ID}",
          "name": "{BRANCH_1_NAME}",
          "id": "{DECISION_OUTCOME_ID_1}",
          "conditions": [
            {
              "leftValueDataType": "{DATA_TYPE}",
              "decisionOutcomeId": "{DECISION_OUTCOME_ID_1}",
              "processId": "{PROCESS_ID}",
              "leftValue": "{VARIABLE_PATH}",
              "leftValueIsList": false,
              "conditionOrder": 1,
              "rightValue": {VALUE},
              "valueType": 1,
              "id": "{CONDITION_ID}",
              "leftValueName": "{VARIABLE_DISPLAY_NAME}",
              "leftValueMetaDataType": {...},
              "operator": "{OPERATOR}"
            }
          ],
          "flowId": "{FLOW_ID_BRANCH_1}",
          "slug": "{branch_1_slug}"
        },
        {
          "outcomeOrder": 1,
          "isDefault": false,
          "logicType": "AND",
          "targetId": "{TARGET_NODE_ID_BRANCH_2}",
          "color": "#ED5044",
          "customConditionLogic": "",
          "processId": "{PROCESS_ID}",
          "name": "{BRANCH_2_NAME}",
          "id": "{DECISION_OUTCOME_ID_2}",
          "conditions": [
            {
              "leftValueDataType": "{DATA_TYPE}",
              "decisionOutcomeId": "{DECISION_OUTCOME_ID_2}",
              "processId": "{PROCESS_ID}",
              "leftValue": "{VARIABLE_PATH}",
              "leftValueIsList": false,
              "conditionOrder": 1,
              "rightValue": {VALUE},
              "valueType": 1,
              "id": "{CONDITION_ID}",
              "leftValueName": "{VARIABLE_DISPLAY_NAME}",
              "leftValueMetaDataType": {...},
              "operator": "{OPERATOR}"
            }
          ],
          "flowId": "{FLOW_ID_BRANCH_2}",
          "slug": "{branch_2_slug}"
        }
      ]
    },
    {
      "isOpen": false,
      "sourceNodeId": "{CLOSING_GATEWAY_NODE_ID}",
      "name": "{CLOSING_GATEWAY_NAME}",
      "description": "",
      "decisionOutcomes": [],
      "slug": "{closing_gateway_slug}"
    }
  ]
}
```

### Ví dụ: Inclusive Gateway có nhánh mặc định (không cần gateway đóng)

Khi tất cả nhánh kết thúc tại End Event, chỉ cần **1 phần tử** trong `gateWays` (không cần gateway đóng).

**Luồng:**
```
Start → Root → IGW (fork) → [Số > 10] → End Process
                           → [Mặc định] → End Process (2)
```

**BPMN XML:**
```xml
<bpmn2:inclusiveGateway default="FL00000000035" id="NO00000000052" name="Check số &gt; 10?">
  <bpmn2:extensionElements>
    <configEx:elementInfo openedGateway="true" />
    <configEx:elementInfo renderKey="INCLUSIVE_GATEWAY" />
  </bpmn2:extensionElements>
  <bpmn:incoming>FL00000000037</bpmn:incoming>
  <bpmn:outgoing>FL00000000035</bpmn:outgoing>
  <bpmn:outgoing>FL00000000036</bpmn:outgoing>
</bpmn2:inclusiveGateway>
```

**JSON `gateWays`:**
```json
{
  "gateWays": [
    {
      "isOpen": true,
      "sourceNodeId": "NO00000000052",
      "name": "Check số > 10?",
      "description": "",
      "slug": "check_so_10",
      "decisionOutcomes": [
        {
          "outcomeOrder": -1,
          "isDefault": true,
          "logicType": "AND",
          "targetId": "NO00000000053",
          "color": "#939393",
          "customConditionLogic": "",
          "processId": "PE00000000014",
          "name": "Mặc định",
          "id": "DO00000000001",
          "conditions": [],
          "flowId": "FL00000000035",
          "slug": "_default"
        },
        {
          "outcomeOrder": 0,
          "isDefault": false,
          "logicType": "AND",
          "targetId": "NO00000000054",
          "color": "#4CAF50",
          "customConditionLogic": "1",
          "processId": "PE00000000014",
          "name": "Số > 10",
          "id": "DO00000000002",
          "conditions": [
            {
              "leftValueDataType": "NUMBER",
              "decisionOutcomeId": "DO00000000002",
              "processId": "PE00000000014",
              "leftValue": "$userTask.Root.so",
              "leftValueIsList": false,
              "conditionOrder": 1,
              "rightValue": 10,
              "valueType": 1,
              "id": "DC00000000001",
              "leftValueName": "So",
              "leftValueMetaDataType": {
                "display_type": 1,
                "round_rule": 0,
                "fractional_length": 0,
                "value_limit": {
                  "min": -9999999999,
                  "max": 9999999999
                },
                "precision": -1,
                "format": {
                  "format": 3,
                  "type": 1
                },
                "integral_length": 10,
                "multiple_limit": {
                  "min": 0,
                  "max": 30
                }
              },
              "operator": ">"
            }
          ],
          "flowId": "FL00000000036",
          "slug": "so_10"
        }
      ]
    }
  ]
}
```

**Lưu ý:**
- Nhánh mặc định: `outcomeOrder: -1`, `isDefault: true`, `conditions: []`, `slug: "_default"`, `color: "#939393"`
- Nhánh có điều kiện: `outcomeOrder` bắt đầu từ `0`, `isDefault: false`
- Khi chỉ có 1 condition thì `customConditionLogic: "1"` (chỉ có condition thứ 1)
- `leftValueMetaDataType` copy nguyên từ `fieldMetaData` / `metaDataType` của resource tương ứng
- Không cần gateway đóng vì cả 2 nhánh đều kết thúc tại End Event

**Cập nhật `resourcesUsedIn` cho field `so`:**
```json
{
  "resourcesUsedIn": [
    {
      "name": "Check số > 10?",
      "gateWayType": "INCLUSIVE_GATEWAY",
      "count": 1,
      "id": "NO00000000052",
      "parentTable": "decision_outcome",
      "slug": "check_so_10"
    }
  ]
}
```

### So sánh với Exclusive Gateway
| Đặc điểm           | Exclusive Gateway        | Inclusive Gateway                                 |
|--------------------|--------------------------|---------------------------------------------------|
| Số nhánh chạy      | Chỉ **1 nhánh** duy nhất | **Nhiều nhánh** có thể chạy cùng lúc              |
| renderKey          | `EXCLUSIVE_GATEWAY`      | `INCLUSIVE_GATEWAY`                               |
| XML tag            | `bpmn2:exclusiveGateway` | `bpmn2:inclusiveGateway`                          |
| Gateway đóng nhánh | Không cần                | **Bắt buộc** phải có gateway đóng nhánh tương ứng |
| Nhánh mặc định     | Tùy chọn                 | Tùy chọn (chạy khi không có nhánh nào đúng)       |
| Điều kiện          | Toán tử, cú pháp biến    | Tương tự Exclusive Gateway                        |

### Điều kiện trong Inclusive Gateway
Các toán tử điều kiện và cú pháp biến giống với Exclusive Gateway (xem phần trên).

Điểm khác biệt: nhiều nhánh có thể thỏa mãn điều kiện cùng lúc, tất cả các nhánh đúng đều được chạy song song.

### Cập nhật Resources khi sử dụng Inclusive Gateway
Khi một trường được sử dụng trong điều kiện Inclusive Gateway, cần thêm `resourcesUsedIn` vào resource của trường đó. **Mỗi nhánh** sử dụng trường đó sẽ tạo một entry riêng:
```json
{
  "resourcesUsedIn": [
    {
      "name": "{GATEWAY_NAME}",
      "gateWayType": "INCLUSIVE_GATEWAY",
      "count": 1,
      "id": "{GATEWAY_NODE_ID}",
      "parentTable": "decision_outcome",
      "slug": "{gateway_slug}"
    },
    {
      "name": "{GATEWAY_NAME}",
      "gateWayType": "INCLUSIVE_GATEWAY",
      "count": 1,
      "id": "{GATEWAY_NODE_ID}",
      "parentTable": "decision_outcome",
      "slug": "{gateway_slug}"
    }
  ]
}
```

### Layout (BPMNDiagram) cho Inclusive Gateway
Các nhánh được bố trí theo chiều dọc, tỏa ra từ gateway mở và hội tụ vào gateway đóng:
- Nhánh phía trên: waypoint đi lên từ gateway mở, rồi đi ngang đến node
- Nhánh phía dưới: waypoint đi xuống từ gateway mở, rồi đi ngang đến node
- Các nhánh hội tụ vào gateway đóng: waypoint đi ngang từ node, rồi đi lên/xuống vào gateway đóng

```
        ┌─→ [Nhánh 1] ─→┐
[GW mở] ┤                ├→ [GW đóng] → ...
        └─→ [Nhánh 2] ─→┘
```

---

## Parallel Gateway

### Mô tả
Parallel Gateway (Cổng song song) là loại gateway cho phép **tất cả các nhánh chạy đồng thời** mà **không cần điều kiện**. Khác với Exclusive Gateway và Inclusive Gateway, các nhánh đi ra từ Parallel Gateway luôn được thực thi song song, không phụ thuộc vào bất kỳ điều kiện nào.

Mỗi Parallel Gateway mở nhánh (`openedGateway="true"`) **bắt buộc** phải có một Parallel Gateway đóng nhánh (`openedGateway="false"`) tương ứng để đồng bộ các nhánh trước khi tiếp tục quy trình.

### Cấu trúc trong BPMN XML

#### Parallel Gateway mở nhánh (Opening)
```xml
<bpmn2:parallelGateway id="{GATEWAY_NODE_ID}" name="{GATEWAY_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo openedGateway="true" />
    <configEx:elementInfo renderKey="PARALLEL_GATEWAY" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_1}</bpmn2:outgoing>
  <bpmn2:outgoing>{OUTGOING_FLOW_2}</bpmn2:outgoing>
</bpmn2:parallelGateway>
```

#### Parallel Gateway đóng nhánh (Closing)
```xml
<bpmn2:parallelGateway id="{CLOSING_GATEWAY_NODE_ID}" name="{CLOSING_GATEWAY_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo openedGateway="false" />
    <configEx:elementInfo renderKey="PARALLEL_GATEWAY" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_FROM_BRANCH_1}</bpmn2:incoming>
  <bpmn2:incoming>{INCOMING_FLOW_FROM_BRANCH_2}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</bpmn2:parallelGateway>
```

**Lưu ý quan trọng:**
- `renderKey="PARALLEL_GATEWAY"`
- Gateway mở nhánh: `openedGateway="true"` - có nhiều outgoing flow (mỗi nhánh một flow)
- Gateway đóng nhánh: `openedGateway="false"` - có nhiều incoming flow (từ các nhánh) và một outgoing flow
- **Không có** thuộc tính `default` (khác với Exclusive/Inclusive Gateway)
- **Không có** điều kiện trên các nhánh - tất cả luôn chạy song song

### Sequence Flow cho các nhánh
Các sequence flow đi ra từ Parallel Gateway mở có tên nhánh nhưng **không cần điều kiện**:
```xml
<bpmn2:sequenceFlow id="{FLOW_ID}" name="{BRANCH_NAME}" sourceRef="{GATEWAY_NODE_ID}" targetRef="{TARGET_NODE_ID}">
  <bpmn2:extensionElements />
</bpmn2:sequenceFlow>
```

### Cấu trúc `gateWays` trong JSON
Thêm **2 phần tử** vào mảng `gateWays`: một cho gateway mở nhánh và một cho gateway đóng nhánh. **Cả hai đều có `decisionOutcomes` rỗng** vì không cần điều kiện.
```json
{
  "gateWays": [
    {
      "isOpen": true,
      "sourceNodeId": "{GATEWAY_NODE_ID}",
      "name": "{GATEWAY_NAME}",
      "description": "",
      "decisionOutcomes": [],
      "slug": "{gateway_slug}"
    },
    {
      "isOpen": false,
      "sourceNodeId": "{CLOSING_GATEWAY_NODE_ID}",
      "name": "{CLOSING_GATEWAY_NAME}",
      "description": "",
      "decisionOutcomes": [],
      "slug": "{closing_gateway_slug}"
    }
  ]
}
```

### So sánh với Exclusive Gateway và Inclusive Gateway
| Đặc điểm           | Exclusive Gateway        | Inclusive Gateway                  | Parallel Gateway                   |
|--------------------|--------------------------|------------------------------------|------------------------------------|
| Số nhánh chạy      | Chỉ **1 nhánh** duy nhất | **Nhiều nhánh** thỏa mãn điều kiện | **Tất cả nhánh** luôn chạy         |
| renderKey          | `EXCLUSIVE_GATEWAY`      | `INCLUSIVE_GATEWAY`                | `PARALLEL_GATEWAY`                 |
| XML tag            | `bpmn2:exclusiveGateway` | `bpmn2:inclusiveGateway`           | `bpmn2:parallelGateway`            |
| Gateway đóng nhánh | Không cần                | **Bắt buộc**                       | **Bắt buộc**                       |
| Nhánh mặc định     | Tùy chọn                 | Tùy chọn                           | **Không có** (không cần)           |
| Điều kiện          | Bắt buộc (trừ mặc định)  | Bắt buộc (trừ mặc định)            | **Không có** (luôn chạy song song) |
| `decisionOutcomes` | Có conditions            | Có conditions                      | **Rỗng `[]`** cho cả mở và đóng    |

---

## ⚠️ RÀNG BUỘC QUAN TRỌNG: Parallel Gateway — số luồng phải khớp

**Cogover BẮT BUỘC** số luồng ra từ gateway mở (fork) phải **bằng đúng** số luồng vào gateway đóng (merge). Lỗi nếu không khớp: `PARALLEL_GATEWAY_FORK_AND_MERGE_HAS_NUMBER_OF_FLOWS_NOT_MATCH`.

### Nhánh có sub-gateway bên trong → PHẢI thêm Merge Gateway cuối nhánh

Nếu một nhánh song song có Exclusive Gateway bên trong (ví dụ: kiểm tra kết quả tìm kiếm), các đường đi khác nhau của nhánh đó sẽ tạo ra nhiều luồng. **Không được** để nhiều luồng từ cùng một nhánh cùng vào `pgw_close`.

**Sai — nhánh có 2 luồng vào pgw_close:**
```
pgw_open → get_per → egw_per → [found] → upd_adv → pgw_close  (2 luồng từ nhánh 1!)
                              → [skip]  ──────────→ pgw_close
```

**Đúng — thêm merge gateway cuối mỗi nhánh:**
```
pgw_open → get_per → egw_per → [found] → upd_adv → merge_per → pgw_close  (1 luồng!)
                              → [skip]  ──────────→ merge_per
```

Trong đó `merge_per` là **Exclusive Gateway merge-only** (xem phần trên): nhiều incoming, 1 outgoing.

### Ví dụ: 6 nhánh song song mỗi nhánh có EGW kiểm tra kết quả

```
pgw_open (6 out) → nhánh 1 → ... → merge_1 (2→1) → pgw_close (6 in)
                 → nhánh 2 → ... → merge_2 (2→1) ↗
                 → nhánh 3 → ... → merge_3 (3→1) ↗  ← nhánh phức tạp hơn
                 → nhánh 4 → ... → merge_4 (2→1) ↗
                 → nhánh 5 → ... → merge_5 (2→1) ↗
                 → nhánh 6 → ... → merge_6 (2→1) ↗
```

Mỗi `merge_N` là một Exclusive Gateway merge-only cần được khai báo trong `gateWays` với `isOpen: false`.

### Layout (BPMNDiagram) cho Parallel Gateway
Bố cục tương tự Inclusive Gateway - các nhánh tỏa ra từ gateway mở và hội tụ vào gateway đóng:
- Nhánh phía trên: waypoint đi lên từ gateway mở, rồi đi ngang đến node
- Nhánh phía dưới: waypoint đi xuống từ gateway mở, rồi đi ngang đến node
- Các nhánh hội tụ vào gateway đóng: waypoint đi ngang từ node, rồi đi lên/xuống vào gateway đóng

```
        ┌─→ [Nhánh 1] ─→┐
[GW mở] ┤                ├→ [GW đóng] → ...
        └─→ [Nhánh 2] ─→┘
```

---
