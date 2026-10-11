## Gateway (Exclusive, Inclusive, Parallel)

Ba loại gateway dùng chung cấu trúc `gateWays[]`, condition và `resourcesUsedIn` mô tả ở Exclusive; Inclusive và Parallel chỉ nêu phần khác. `{OBJECT_TYPE_ID}` trong điều kiện RECORD lấy theo bullet "Thông tin Object thật" ở [mục Chuẩn bị của SKILL.md](../SKILL.md#chuẩn-bị). ID (`DO` decision outcome, `DOC` condition), nhánh mặc định trong XML/JSON và End Branch/End Process: [SKILL.md Bước 2–3](../SKILL.md#quy-tắc-id). Bố cục nhánh và waypoint fork/merge: [references/bpmn-xml-and-diagram.md](../references/bpmn-xml-and-diagram.md#bố-cục-node-bpmndiagram).

## Exclusive Gateway

Chỉ **một nhánh** chạy; không nhánh nào thoả điều kiện thì chạy nhánh **mặc định**.

### BPMN XML (fork)

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

`default` = ID flow mặc định; `openedGateway="true"` = gateway đã cấu hình (fork). Merge-only: xem [ràng buộc merge/fork](#ràng-buộc-exclusive-không-vừa-merge-vừa-fork).

### `gateWays` trong JSON

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

- Nhánh mặc định: `outcomeOrder: -1`, `isDefault: true`, không `conditions` (hoặc `conditions: []`), `customConditionLogic: ""`, `slug: "_default"`, `color: "#939393"`, `flowId` = flow mà `default` trong XML trỏ tới. Nhánh có điều kiện: `outcomeOrder` từ `0`, `isDefault: false`.
- `logicType` quyết định `customConditionLogic`: `"AND"` → `"1 AND 2 AND ... AND N"`; `"OR"` → `"1 OR 2 OR ... OR N"`; `"CUSTOM"` → biểu thức người dùng cung cấp, ví dụ `"1 AND (2 OR 3) AND 4"` (số = `conditionOrder`; hỗ trợ `AND`, `OR`, ngoặc đơn). Chỉ có 1 condition: `customConditionLogic: "1"`.
- Màu nhánh có điều kiện tuỳ chọn, ví dụ `#4CAF50` (xanh lá), `#ED5044` (đỏ), `#FAD000` (vàng).

### Điều kiện (`conditions[]`)

- `conditionOrder` bắt đầu từ `1`, tăng dần.
- `valueType`: `1` = giá trị cố định trong `rightValue`; `2` = giá trị lấy từ resource khác, thêm `rightValueName`, `rightValueDataType`, `rightValueIsList`.
- `leftValue`: trường User Task `$userTask.{task_slug}.{field_slug}` (ví dụ `$userTask.Root.so_ngay_xin_nghi`) hoặc output action `$action.{action_slug}.output`.
- `leftValueMetaDataType`: copy nguyên từ `fieldMetaData`/`metaDataType` của resource tương ứng.
- `leftValueDataType: "RECORD"`: thêm `"leftObjectTypeId": "{OBJECT_TYPE_ID}"` (objectTypeId từ `$object-info`).
- `IS_NULL`/`IS_NOT_NULL`: `rightValue` là chuỗi `"null"`. `LIST_IS_EMPTY`/`LIST_IS_NOT_EMPTY`: không có `rightValue`.

Toán tử theo `leftValueDataType` và `leftValueIsList` (`rightValue` ghi đúng kiểu JSON như ví dụ):

| `leftValueDataType` | `leftValueIsList` | `operator` | `rightValue` |
|---|---|---|---|
| `NUMBER` | `false` | `>=`, `<=`, `>`, `<`, `==`, `!=`, `IS_NULL`, `IS_NOT_NULL` | số, ví dụ `5` |
| `NUMBER` | `true` | `LIST_CONTAINS`, `LIST_NOT_CONTAINS` | số, ví dụ `1` |
| `DATE` | `false` | `==`, `!=`, `>=`, `<=`, `>`, `<`, `IS_NULL`, `IS_NOT_NULL` | chuỗi `"YYYY-MM-DD"`, ví dụ `"2026-02-01"` |
| `DATE` | `true` | `LIST_CONTAINS`, `LIST_NOT_CONTAINS` | chuỗi `"YYYY-MM-DD"` |
| `DATE_TIME` | `false` | `==`, `!=`, `>=`, `<=`, `>`, `<`, `IS_NULL`, `IS_NOT_NULL` | timestamp millisecond, ví dụ `1770570900000` |
| `BOOLEAN` | `false` | `==`, `!=`, `IS_NULL`, `IS_NOT_NULL` | `true` hoặc `false` |
| `TEXT` | `false` | `==`, `!=`, `TEXT_CONTAINS`, `TEXT_NOT_CONTAINS`, `STARTS_WITH`, `ENDS_WITH`, `IS_NULL`, `IS_NOT_NULL` | chuỗi, ví dụ `"abc"` |
| `TEXT` | `true` | `LIST_CONTAINS`, `LIST_NOT_CONTAINS` | chuỗi, ví dụ `"1"` |
| `SELECT_LIST` | `false` | `==`, `!=` | `value` của một option: chuỗi `"approve"` hoặc số `1` |
| `SELECT_LIST` | `false` | `IS_ONE_OF`, `IS_NOT_ONE_OF` | mảng `value`, ví dụ `["approve", "return"]` hoặc `[1, 2]` |
| `SELECT_LIST` | `false` | `LIST_IS_EMPTY` (chưa chọn) | không có |
| `SELECT_LIST` | `true` | `SELECT_LIST_CONTAINS`, `SELECT_LIST_NOT_CONTAINS` (không dùng `LIST_CONTAINS`/`LIST_NOT_CONTAINS`) | luôn là mảng `value`, ví dụ `["approve"]` hoặc `[1]` |
| `SELECT_LIST` | `true` | `LIST_IS_EMPTY`, `LIST_IS_NOT_EMPTY` | không có |
| `RECORD` | `false` | `==`, `IS_NULL`, `IS_NOT_NULL` | ID bản ghi, ví dụ `"LE000000000001"` |
| `RECORD` | `true` | `LIST_CONTAINS`, `LIST_NOT_CONTAINS` | ID bản ghi |

`rightValue` của `SELECT_LIST` là `value` của option, không phải `label`. Option dùng để rẽ nhánh đặt `value` là mã ổn định không dấu ([user-task-form-fields.md](user-task-form-fields.md#select_list-danh-sách-lựa-chọn)); `samples/sample_process_gw_conditions.json` có `value` trùng nhãn (`"Lựa chọn 1"`) nên đổi nhãn ở đó sẽ phải sửa cả điều kiện.

Ví dụ điều kiện RECORD (các kiểu khác chỉ khác `leftValueDataType`, `operator`, `rightValue` và không có `leftObjectTypeId`):

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

### Điều kiện an toàn khi chạy

- So sánh (`==`, `>=`, ...) khi resource vế trái null làm lượt chạy dừng với `CAN_NOT_COMPARE_BECAUSE_RESOURCE_VALUE_IS_NULL`. Field của User Task thuộc nhánh chưa chạy, field không bắt buộc, field do backend tính chậm đều có thể null: đặt outcome `IS_NULL` lên trước, hoặc so sánh Formula resource null-safe trả `NUMBER` 0/1 với `== 1` (*đã sửa và chạy đúng*).
- `leftValueDataType` phải đúng kiểu thật của resource: khai báo `NUMBER` cho field formula trả boolean (hoặc ngược lại) gây lỗi lúc chạy `Boolean cannot be cast to Number`; lưu process có thể báo `meta.errors` code `15` khi hai vế khác kiểu. Chưa chắc kiểu trả về thì dùng formula 0/1 và `NUMBER ==` (*đã sửa và chạy đúng*).
- `SELECT_LIST` so sánh theo `value` của option (xem ghi chú dưới bảng toán tử).
- Field `rollup_summary` trong điều kiện gateway hoặc `recordData` của Create Record đã gây lỗi một lần, chưa rõ lúc lưu hay lúc chạy (*quan sát, cần kiểm chứng*): chép sang field formula số rồi dùng field đó. Điều kiện tạo và độ trễ tính lại của rollup: [object-info `rollup_summary`](../../object-info/references/api-object-fields.md#rollup_summary).

### `resourcesUsedIn` của trường dùng trong điều kiện

Resource của trường được dùng trong điều kiện gateway thêm entry (Inclusive: `gateWayType: "INCLUSIVE_GATEWAY"`, mỗi nhánh dùng trường tạo một entry riêng):

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

### Ràng buộc: Exclusive không vừa merge vừa fork

Một Exclusive Gateway có **nhiều incoming VÀ nhiều outgoing** bị từ chối với lỗi `GATEWAY_CAN_NOT_BE_BOTH_MERGE_AND_FORK`. Mỗi Exclusive phải là một trong hai:

- **Fork**: 1 incoming, nhiều outgoing; có `default` và `decisionOutcomes`.
- **Merge**: nhiều incoming, 1 outgoing; không `default`, không `decisionOutcomes`.

Pattern "nếu đúng → làm gì đó → tiếp tục": `EGW_A (fork) → [TRUE] → Task → EGW_B` với nhánh `[default]` cũng nối vào `EGW_B` làm `EGW_B` vừa merge vừa fork → lỗi. Sửa: thêm Exclusive **merge-only** `MERGE_B` (2 in, 1 out) trước `EGW_B` (1 in, 2 out); cần N merge gateway cho N lần hội tụ (ví dụ kiểm tra liên tiếp `is_a`, `is_b`, `is_c`: mỗi cặp `EGW_fork → merge → EGW_fork tiếp` là một checkpoint).

Merge-only trong XML (không `default`, không `openedGateway`) và JSON (`isOpen: false`, `decisionOutcomes: []`):

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

## Inclusive Gateway

**Nhiều nhánh** có thể đúng cùng lúc và chạy song song; không nhánh nào thoả thì chạy nhánh mặc định (tuỳ chọn). Điều kiện, toán tử và cú pháp biến giống Exclusive.

Mỗi Inclusive mở nhánh (`openedGateway="true"`) **bắt buộc** có một Inclusive đóng nhánh (`openedGateway="false"`) để đồng bộ trước khi tiếp tục. Ngoại lệ: mọi nhánh đều kết thúc tại End Event thì không cần gateway đóng và `gateWays` chỉ có 1 phần tử.

```xml
<!-- Mở nhánh: bỏ thuộc tính default nếu không có nhánh mặc định -->
<bpmn2:inclusiveGateway default="{DEFAULT_FLOW_ID}" id="{GATEWAY_NODE_ID}" name="{GATEWAY_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo openedGateway="true" />
    <configEx:elementInfo renderKey="INCLUSIVE_GATEWAY" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{DEFAULT_FLOW_ID}</bpmn2:outgoing>
  <bpmn2:outgoing>{CONDITION_FLOW_ID}</bpmn2:outgoing>
</bpmn2:inclusiveGateway>

<!-- Đóng nhánh -->
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

`gateWays` có **2 phần tử**: gateway mở (`isOpen: true`, `decisionOutcomes` như Exclusive; các nhánh điều kiện `outcomeOrder` `0`, `1`, ...) và gateway đóng:

```json
{
  "isOpen": false,
  "sourceNodeId": "{CLOSING_GATEWAY_NODE_ID}",
  "name": "{CLOSING_GATEWAY_NAME}",
  "description": "",
  "decisionOutcomes": [],
  "slug": "{closing_gateway_slug}"
}
```

## Parallel Gateway

**Tất cả nhánh** chạy đồng thời, **không có điều kiện** và không có nhánh mặc định. Gateway mở (`openedGateway="true"`) bắt buộc có gateway đóng (`openedGateway="false"`).

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

Gateway đóng: cùng element và `renderKey`, `openedGateway="false"`, nhiều incoming, 1 outgoing. Không có thuộc tính `default`. `sequenceFlow` đi ra từ gateway mở có `name` nhánh nhưng không có điều kiện.

Hai User Task song song cùng ghi một field của bản ghi và được submit gần như cùng lúc đã làm mất một giá trị một lần (field lựa chọn; *quan sát, cần kiểm chứng*). Mỗi nhánh ghi field riêng; sau gateway đóng, đọc lại bản ghi bằng Get Records rồi mới đánh giá kết quả.

`gateWays` có **2 phần tử** (mở `isOpen: true`, đóng `isOpen: false`), **cả hai** `decisionOutcomes: []`:

```json
{
  "gateWays": [
    { "isOpen": true, "sourceNodeId": "{GATEWAY_NODE_ID}", "name": "{GATEWAY_NAME}", "description": "", "decisionOutcomes": [], "slug": "{gateway_slug}" },
    { "isOpen": false, "sourceNodeId": "{CLOSING_GATEWAY_NODE_ID}", "name": "{CLOSING_GATEWAY_NAME}", "description": "", "decisionOutcomes": [], "slug": "{closing_gateway_slug}" }
  ]
}
```

### Ràng buộc: số luồng vào/ra phải khớp

Số luồng ra từ gateway mở (fork) phải **bằng đúng** số luồng vào gateway đóng (merge); sai → lỗi `PARALLEL_GATEWAY_FORK_AND_MERGE_HAS_NUMBER_OF_FLOWS_NOT_MATCH`. Nhánh song song có Exclusive Gateway bên trong (ví dụ kiểm tra kết quả tìm kiếm) sinh nhiều đường đi; **không** để nhiều luồng từ cùng một nhánh cùng vào gateway đóng. Thêm một Exclusive merge-only cuối mỗi nhánh như vậy (khai báo trong `gateWays` với `isOpen: false`) để mỗi nhánh chỉ có 1 luồng vào gateway đóng:

```
Sai:  pgw_open → get_per → egw_per → [found] → upd_adv → pgw_close   (2 luồng từ nhánh 1)
                                    → [skip]  ─────────→ pgw_close
Đúng: pgw_open → get_per → egw_per → [found] → upd_adv → merge_per → pgw_close   (1 luồng)
                                    → [skip]  ─────────→ merge_per
```

## So sánh ba loại

| Đặc điểm | Exclusive | Inclusive | Parallel |
|---|---|---|---|
| Số nhánh chạy | chỉ 1 | mọi nhánh thoả điều kiện | tất cả |
| `renderKey` / XML | `EXCLUSIVE_GATEWAY` / `bpmn2:exclusiveGateway` | `INCLUSIVE_GATEWAY` / `bpmn2:inclusiveGateway` | `PARALLEL_GATEWAY` / `bpmn2:parallelGateway` |
| Gateway đóng nhánh | không cần (merge-only khi cần hội tụ) | bắt buộc (trừ khi mọi nhánh kết thúc ở End Event) | bắt buộc |
| Nhánh mặc định | tuỳ chọn | tuỳ chọn | không có |
| Điều kiện | bắt buộc (trừ mặc định) | bắt buộc (trừ mặc định) | không có |
| `decisionOutcomes` | có conditions | có conditions | `[]` cho cả mở và đóng |

## Bố cục Inclusive/Parallel

Các nhánh bố trí theo chiều dọc, toả ra từ gateway mở và hội tụ vào gateway đóng: nhánh phía trên đi lên từ gateway mở rồi ngang tới node, nhánh phía dưới đi xuống rồi ngang; hội tụ đi ngang từ node rồi lên/xuống vào gateway đóng. Khoảng cách hàng và công thức waypoint (Case 2 fork → nhánh, Case 3 nhánh → merge): [references/bpmn-xml-and-diagram.md](../references/bpmn-xml-and-diagram.md#waypoint-cho-bpmnedge).
