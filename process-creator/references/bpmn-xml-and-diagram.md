# BPMN XML và sơ đồ (BPMNDiagram)

Đọc khi dựng hoặc sửa `xmlString`. File này giữ template XML, quy tắc namespace/kết nối, bố cục node, công thức waypoint và `BPMNLabel`. Kiểm tra hình học bằng script, bố cục gọn và khoảng trống cho nhãn: [nodes/bpmn-geometry-validation.md](../nodes/bpmn-geometry-validation.md). XML của từng loại node: `nodes/*.md`.

## Template BPMN XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn2:definitions xmlns:bioc="http://bpmn.io/schema/bpmn/biocolor/1.0" xmlns:bpmn2="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:configEx="http://config-ex/schema" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:color="http://www.omg.org/spec/BPMN/non-normative/color/1.0" id="cogover-diagram" targetNamespace="http://bpmn.io/schema/bpmn" xsi:schemaLocation="http://www.omg.org/spec/BPMN/20100524/MODEL BPMN20.xsd">
  <bpmn2:process id="{PROCESS_ID}">
    <!-- renderKey theo loại quy trình: START_MANUAL_EVENT / START_NORMAL_EVENT / START_SCHEDULED_EVENT / START_TRIGGERED_EVENT / START_SEQUENCE_EVENT -->
    <bpmn2:startEvent id="{START_NODE_ID}" name="Bắt đầu">
      <bpmn2:extensionElements>
        <configEx:elementInfo renderKey="{START_EVENT_RENDER_KEY}" />
      </bpmn2:extensionElements>
      <bpmn2:outgoing>{FIRST_FLOW_ID}</bpmn2:outgoing>
    </bpmn2:startEvent>

    <!-- User Task (lặp lại cho mỗi node) -->
    <bpmn2:userTask id="{USER_TASK_NODE_ID}" name="{NODE_NAME}">
      <bpmn2:extensionElements>
        <configEx:elementInfo renderKey="USER_TASK" />
      </bpmn2:extensionElements>
      <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
      <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
    </bpmn2:userTask>

    <!-- Exclusive Gateway fork (nếu có); merge-only: xem nodes/gateway.md -->
    <bpmn2:exclusiveGateway id="{GATEWAY_NODE_ID}" name="{GATEWAY_NAME}" default="{DEFAULT_FLOW_ID}">
      <bpmn2:extensionElements>
        <configEx:elementInfo openedGateway="true" />
        <configEx:elementInfo renderKey="EXCLUSIVE_GATEWAY" />
      </bpmn2:extensionElements>
      <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
      <bpmn2:outgoing>{OUTGOING_FLOW_1}</bpmn2:outgoing>
      <bpmn2:outgoing>{OUTGOING_FLOW_2}</bpmn2:outgoing>
    </bpmn2:exclusiveGateway>

    <!-- End Process; End Branch dùng renderKey END_BRANCH_EVENT (nodes/end-branch-event.md) -->
    <bpmn2:endEvent id="{END_NODE_ID}" name="Kết thúc quy trình">
      <bpmn2:extensionElements>
        <configEx:elementInfo renderKey="END_EVENT" />
      </bpmn2:extensionElements>
      <bpmn2:incoming>{LAST_FLOW_ID}</bpmn2:incoming>
    </bpmn2:endEvent>

    <!-- Luồng tuần tự (mọi sequenceFlow nằm trong bpmn2:process) -->
    <bpmn2:sequenceFlow id="{FLOW_ID}" name="" sourceRef="{SOURCE_NODE_ID}" targetRef="{TARGET_NODE_ID}">
      <bpmn2:extensionElements />
    </bpmn2:sequenceFlow>

    <!-- Luồng có điều kiện từ Gateway: có name -->
    <bpmn2:sequenceFlow id="{CONDITION_FLOW_ID}" name="{CONDITION_NAME}" sourceRef="{GATEWAY_NODE_ID}" targetRef="{TARGET_NODE_ID}">
      <bpmn2:extensionElements />
    </bpmn2:sequenceFlow>
  </bpmn2:process>

  <bpmndi:BPMNDiagram id="BPMNDiagram_{PROCESS_ID}">
    <bpmndi:BPMNPlane id="BPMNPlane_{PROCESS_ID}" bpmnElement="{PROCESS_ID}">

      <!-- BPMNShape cho MỖI node; BPMNLabel bên trong là bắt buộc -->
      <bpmndi:BPMNShape id="{SHAPE_ID}_di" bpmnElement="{NODE_ID}">
        <dc:Bounds x="{X}" y="{Y}" width="60" height="60" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="{LABEL_X}" y="{LABEL_Y}" width="{LABEL_WIDTH}" height="16" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNShape>

      <!-- BPMNEdge cho MỖI sequenceFlow -->
      <bpmndi:BPMNEdge id="{EDGE_ID}_di" bpmnElement="{FLOW_ID}">
        <di:waypoint x="{SOURCE_X + WIDTH}" y="{SOURCE_Y + HEIGHT/2}" />
        <di:waypoint x="{TARGET_X}" y="{TARGET_Y + HEIGHT/2}" />
      </bpmndi:BPMNEdge>

    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn2:definitions>
```

## Namespace và kết nối logic

- Mọi element BPMN-spec (`process`, `startEvent`, `endEvent`, `sequenceFlow`, `incoming`, `outgoing`, `extensionElements`, `userTask`, `exclusiveGateway`, `inclusiveGateway`, `parallelGateway`, ...) dùng prefix `bpmn2:`; `xmlns:bpmn2` là namespace duy nhất được khai báo. Không dùng `bpmn:`: prefix này không khai báo và một số element có thể bị server silent-strip khi CREATE. Giữ nguyên prefix tuỳ chỉnh `elEx:`, `configEx:`, `bpmndi:`, `dc:`, `di:`, `bioc:`, `xsi:`.
- Node dùng `elEx:` (`elEx:httpTask`, `elEx:getRecordTask`, ...) cần thêm `xmlns:elEx="http://element-ex/schema"` vào `bpmn2:definitions`.
- Response GET có thể serialize `incoming`, `outgoing`, `sequenceFlow` thành `bpmn:` (canonicalization phía server); không PUT/DELETE/recreate chỉ để đổi prefix. Request create/update do skill sinh vẫn chỉ dùng `bpmn2:`.
- Tránh lỗi `NODE_HAS_NO_CONNECT_TO_ANYTHING`: khai báo mọi ID (node, flow, action, gateway, ...) thành biến dùng chung từ đầu và dùng nhất quán trong cả XML lẫn JSON; mỗi `sequenceFlow` có `sourceRef`/`targetRef` trỏ đúng `id` node; mỗi node liệt kê đủ `incoming`/`outgoing` (Start chỉ có outgoing, End chỉ có incoming); mọi `sequenceFlow` nằm bên trong `bpmn2:process`.

## Bố cục node (BPMNDiagram)

Mỗi node có tọa độ riêng phù hợp cấu trúc flow; không đặt tất cả node trên một hàng ngang; không dùng tọa độ cố định hoặc hardcode waypoint.

### Quy tắc chung

- Kích thước mọi node: `width=60, height=60`.
- Luồng chính: `y=260`; node đầu tiên `x=40, y=260`.
- Bước bố trí ban đầu giữa hai node liên tiếp cùng hàng: `x += 160`; tăng khi tên node/tên nhánh cần thêm chỗ. Tính khoảng trống theo cả node và label, không chỉ icon 60×60.
- Trước khi chốt tọa độ, đọc [bố cục gọn và khoảng trống cho nhãn](../nodes/bpmn-geometry-validation.md#bố-cục-gọn-và-khoảng-trống-cho-nhãn): nhánh ngắn đặt gần gateway của nó, nhánh ở vùng x khác nhau có thể dùng chung hàng, không tăng y theo thứ tự gateway trên toàn sơ đồ. `ok: true` của validator hình học chưa chứng minh bố cục dễ đọc.

### Bố trí nhánh gateway

**Exclusive Gateway (2 nhánh):**

- Fork gateway và merge gateway nằm trên luồng chính (`y=260`).
- Một nhánh tiếp tục luồng chính, nhánh còn lại chỉ xử lý ngoại lệ/kết thúc/quay lại: giữ nhánh tiếp tục trên hàng chính, đặt nhánh ngắn phía trên hoặc dưới gần gateway.
- Cả hai nhánh có chuỗi xử lý riêng: nhánh điều kiện ở `y = 100`, nhánh mặc định ở `y = 420` (hoặc đảo phía). Đây là vị trí khởi đầu tương đối với hàng chính, không phải hàng mới dành riêng cho từng gateway.
- Hai chuỗi xử lý trên/dưới cùng vùng x: khoảng cách hàng ban đầu ≥ 200 đơn vị BPMN, tăng theo chiều cao nhãn thực tế. Một nhánh ngắn tách khỏi hàng chính: bắt đầu lệch 160–200 đơn vị rồi kiểm tra vùng trống.

**Parallel Gateway (nhiều nhánh):**

- Fork (open) và merge (close) nằm trên luồng chính (`y=260`).
- Các nhánh trải đều theo chiều dọc, khoảng cách ≥ 160; ví dụ 6 nhánh: `y = -350, -150, 60, 260, 470, 670`. Một nhánh có thể nằm trên luồng chính.
- Merge gateway (close) đặt ở x lớn hơn node cuối cùng của nhánh dài nhất.

**Nhánh con lồng nhau:** exclusive gateway bên trong nhánh parallel bố trí theo vùng trống của cả cụm cha; tăng khoảng cách hàng cha khi cần. Không mặc định lệch y ±80 vì node và nhãn nhiều dòng có thể đè nhau.

Bố cục riêng của Loop (flow quay lại): [nodes/loop-task.md](../nodes/loop-task.md); Inclusive/Parallel: [nodes/gateway.md](../nodes/gateway.md).

### Waypoint cho BPMNEdge

Sinh node bounds và edge từ cùng một bảng node ID → bounds. Chốt vị trí node trước khi tính waypoint; di chuyển node thì tính lại mọi edge liên quan. Hai đầu edge bám đường biên của đúng node theo `sourceRef`/`targetRef`; không dùng tâm node làm điểm nối. Sau khi sinh, chạy validator theo [nodes/bpmn-geometry-validation.md](../nodes/bpmn-geometry-validation.md).

Thuật ngữ với node bounds tại `(x, y)`, kích thước 60×60: right center `(x+60, y+30)`; left center `(x, y+30)`; top center `(x+30, y)`; bottom center `(x+30, y+60)`.

Các công thức 60×60 dưới đây dùng cho node mới. Với process đang sửa, tính tâm/cạnh từ `BPMNShape/Bounds` thực tế; không ép mọi node về 60×60. Case 1–4 giả định target nằm bên phải và tuyến không đi xuyên node; dùng Case 5–6 khi giả định này không đúng.

| Case | Điều kiện | Waypoint |
|---|---|---|
| 1. Cùng hàng, target bên phải | 2 waypoint; ngang khi tâm cùng y, hơi chéo nếu chênh nhỏ | `(sx+60, sy+30) → (tx, ty+30)` |
| 2. Fork gateway → nhánh khác hàng | Target ở trên (`ty < sy`): exit từ top | `(sx+30, sy) → (sx+30, ty+30) → (tx, ty+30)` |
| | Target ở dưới (`ty > sy`): exit từ bottom | `(sx+30, sy+60) → (sx+30, ty+30) → (tx, ty+30)` |
| 3. Nhánh khác hàng → merge gateway | Source ở trên (`sy < ty`): enter từ top | `(sx+60, sy+30) → (tx+30, sy+30) → (tx+30, ty)` |
| | Source ở dưới (`sy > ty`): enter từ bottom | `(sx+60, sy+30) → (tx+30, sy+30) → (tx+30, ty+60)` |
| 4. Khác hàng, không phải gateway | 4 waypoint chữ L qua `mid_x = (sx + 60 + tx) / 2` | `(sx+60, sy+30) → (mid_x, sy+30) → (mid_x, ty+30) → (tx, ty+30)` |
| 5. Cùng cột, nối dọc | Tâm cùng x, không node chắn giữa; ưu tiên hơn Case 4, kể cả khi target là End Process | Target ở trên: `(sx+30, sy) → (tx+30, ty+60)`; ở dưới: `(sx+30, sy+60) → (tx+30, ty)` |
| 6. Quay lại/loop hoặc target bên trái | Cùng hàng, không vật cản: cạnh trái source → cạnh phải target. Đường đi xuyên node: chọn tuyến vòng ngoài bounds, thêm điểm rẽ theo khoảng trống thực tế rồi kiểm tra lại | Không tái dùng công thức source-right → target-left cho mọi hướng; không đổi kết nối logic chỉ để đường vẽ đẹp hơn |

Fork gateway là gateway có `isOpen: true` trong `gateWays`; merge gateway có `isOpen: false`.

### Ví dụ bố cục exclusive gateway

```
Flow: Start → Task1 → EGW_Fork → [BranchA: Task2] / [BranchB: Task3] → EGW_Merge → End

Positions:
  Start:      (40, 260)
  Task1:      (200, 260)
  EGW_Fork:   (360, 260)    ← fork, y=260
  Task2:      (520, 100)    ← nhánh trên
  Task3:      (520, 420)    ← nhánh dưới
  EGW_Merge:  (680, 260)    ← merge, y=260
  End:        (840, 260)

Edges:
  Start→Task1:     (100,290) → (200,290)           [cùng hàng]
  Task1→EGW_Fork:  (260,290) → (360,290)           [cùng hàng]
  EGW_Fork→Task2:  (390,260) → (390,130) → (520,130) [fork → trên]
  EGW_Fork→Task3:  (390,320) → (390,450) → (520,450) [fork → dưới]
  Task2→EGW_Merge: (580,130) → (710,130) → (710,260) [trên → merge top]
  Task3→EGW_Merge: (580,450) → (710,450) → (710,320) [dưới → merge bottom]
  EGW_Merge→End:   (740,290) → (840,290)           [cùng hàng]
```

### Ví dụ bố cục parallel gateway

```
Flow: PGW_Open → [Branch1: TaskA] / [Branch2: TaskB] → PGW_Close

Positions:
  PGW_Open:   (360, 260)   ← fork parallel
  TaskA:      (520, 150)   ← nhánh trên
  TaskB:      (520, 380)   ← nhánh dưới
  PGW_Close:  (720, 260)   ← merge parallel

Edges:
  PGW_Open→TaskA:  (390,260) → (390,180) → (520,180)  [fork → trên]
  PGW_Open→TaskB:  (390,320) → (390,410) → (520,410)  [fork → dưới]
  TaskA→PGW_Close: (580,180) → (750,180) → (750,260)  [trên → merge top]
  TaskB→PGW_Close: (580,410) → (750,410) → (750,320)  [dưới → merge bottom]
```

## BPMNLabel

Mỗi `<bpmndi:BPMNShape>` BẮT BUỘC chứa `<bpmndi:BPMNLabel>` có `<dc:Bounds>`; không self-closing `<bpmndi:BPMNLabel/>` hoặc rỗng.

Symptom khi thiếu/sai: API tạo vẫn trả `r:0` và `isValid:true` (server không validate phần này), nhưng khi người dùng mở quy trình trong editor và bấm Save, node thiếu label biến mất khỏi sơ đồ (thấy rõ với Get Records, Loop, Update Record). Lỗi silent, không có error log phía server.

```xml
<!-- SAI: thiếu BPMNLabel hoặc BPMNLabel rỗng -->
<bpmndi:BPMNShape bpmnElement="NO..." id="Shape_..._di">
  <dc:Bounds x="..." y="..." width="60" height="60"/>
  <bpmndi:BPMNLabel/>
</bpmndi:BPMNShape>

<!-- ĐÚNG -->
<bpmndi:BPMNShape bpmnElement="NO..." id="Shape_..._di">
  <dc:Bounds x="..." y="..." width="60" height="60"/>
  <bpmndi:BPMNLabel>
    <dc:Bounds x="{LABEL_X}" y="{LABEL_Y}" width="{LABEL_WIDTH}" height="{LABEL_HEIGHT}"/>
  </bpmndi:BPMNLabel>
</bpmndi:BPMNShape>
```

- `LABEL_WIDTH` = `max(28, len(name) * 6)`, làm tròn lên số nguyên. Tên dài (> 25 ký tự) có thể xuống 2 dòng → `LABEL_HEIGHT = 32`.
- `LABEL_X` = `X + (NODE_WIDTH / 2) - (LABEL_WIDTH / 2)`: căn giữa label so với node (không dùng `LABEL_X = X`).
- `LABEL_Y` mặc định `Y + 70` (dưới node, cách 10px). Nhãn che đường nối hoặc nhãn khác: dời lên trên/sang bên rồi cập nhật bounds; không giữ công thức mặc định khi có xung đột.
- `LABEL_HEIGHT` = `16` (hoặc `32` nếu 2 dòng).

Edge có `name` (tên nhánh gateway): thêm `BPMNLabel` vào `BPMNEdge`:

```xml
<bpmndi:BPMNEdge id="Edge_1_di" bpmnElement="FL...">
  <di:waypoint x="..." y="..." />
  <di:waypoint x="..." y="..." />
  <bpmndi:BPMNLabel>
    <dc:Bounds x="{MID_X}" y="{MID_Y}" width="60" height="16" />
  </bpmndi:BPMNLabel>
</bpmndi:BPMNEdge>
```

Chọn một đoạn thẳng đủ dài của edge để đặt label sát đoạn đó, chừa khoảng trống với node, tên node và nhãn khác. `MID_X`, `MID_Y` là góc trên trái của bounds nhãn tính từ vị trí đã chọn; không lấy trung điểm hai đầu toàn tuyến gấp khúc vì nhãn có thể rơi xa đường nối. Chưa đủ chỗ: dời nhãn sang đoạn khác hoặc nới bố cục; không thu nhỏ chữ.
