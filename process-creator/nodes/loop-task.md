## Loop Task (Task Vòng Lặp)

### Mô tả
Loop Task là một task hệ thống cho phép duyệt qua một danh sách (ví dụ: danh sách bản ghi từ trường lookup nhiều giá trị). Khi luồng chạy đến Loop Task, nó sẽ lặp qua từng item trong danh sách và thực thi nhánh "For each item" cho mỗi item. Sau khi duyệt hết tất cả item, nhánh "After last item" sẽ được thực thi.

### Cấu trúc trong BPMN XML
```xml
<elEx:loopTask id="{LOOP_NODE_ID}" name="{LOOP_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="LOOP_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:incoming>{LOOP_BACK_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{FOR_EACH_FLOW_ID}</bpmn2:outgoing>
  <bpmn2:outgoing>{AFTER_LAST_FLOW_ID}</bpmn2:outgoing>
</elEx:loopTask>
```

**Lưu ý quan trọng:**
- Sử dụng `elEx:loopTask` (KHÔNG phải `bpmn2:userTask`)
- Cần thêm namespace: `xmlns:elEx="http://element-ex/schema"` vào `bpmn2:definitions`
- `renderKey="LOOP_TASK"`
- Loop Task có **nhiều incoming**: flow từ task trước VÀ flow quay lại từ nhánh "For each item"
- Loop Task có **2 outgoing**: flow "For each item" và flow "After last item"
- ⚠️ **BẮT BUỘC**: Cả 2 flow outgoing của Loop Task **PHẢI có extension `loopFlowType`**. Thiếu extension này → lỗi `LoopNode must have exactly 2 outgoing flows: forEachItemFlow and afterLastItemFlow`

### Cấu trúc Flow đặc biệt của Loop

Loop Task có 2 flow đi ra với extension đặc biệt:

**Flow "For each item" (chạy cho mỗi item trong danh sách):**
```xml
<bpmn2:sequenceFlow id="{FOR_EACH_FLOW_ID}" name="For each item" sourceRef="{LOOP_NODE_ID}" targetRef="{NEXT_TASK_NODE_ID}">
  <bpmn2:extensionElements>
    <configEx:elementInfo loopFlowType="for_each_item" />
  </bpmn2:extensionElements>
</bpmn2:sequenceFlow>
```

**Flow "After last item" (chạy sau khi duyệt hết danh sách):**
```xml
<bpmn2:sequenceFlow id="{AFTER_LAST_FLOW_ID}" name="After last item" sourceRef="{LOOP_NODE_ID}" targetRef="{END_NODE_ID}">
  <bpmn2:extensionElements>
    <configEx:elementInfo loopFlowType="after_last_item" />
  </bpmn2:extensionElements>
</bpmn2:sequenceFlow>
```

**Flow quay lại Loop (từ task cuối trong vòng lặp quay về Loop Task):**
```xml
<bpmn2:sequenceFlow id="{LOOP_BACK_FLOW_ID}" name="" sourceRef="{LAST_TASK_IN_LOOP}" targetRef="{LOOP_NODE_ID}">
  <bpmn2:extensionElements />
</bpmn2:sequenceFlow>
```

### Cấu trúc `loops` trong JSON
Thêm section `loops` vào JSON root level:
```json
{
  "loops": [
    {
      "forEachBranch": "{FOR_EACH_FLOW_ID}",
      "variableDataType": "RECORD",
      "name": "{LOOP_NAME}",
      "variable": "$userTask.{task_slug}.{field_slug}",
      "description": "",
      "variableMetadata": {
        "multipleLimit": {"min": 0, "max": 30, "warning": ""},
        "linkField": "id",
        "objectSlug": "{object_slug}",
        "object": "{OBJECT_TYPE_ID}"
      },
      "nodeId": "{LOOP_NODE_ID}",
      "afterLastItemBranch": "{AFTER_LAST_FLOW_ID}",
      "slug": "{loop_slug}",
      "direction": 1,
      "variablePathName": "workflow_resource:list.userTask / {TaskName} / {FieldName}"
    }
  ]
}
```

### Chi tiết các trường cấu hình Loop

#### 1. Variable (Danh sách duyệt)
```json
{
  "variable": "$userTask.Root.danh_sach_leads",
  "variableDataType": "RECORD",
  "variablePathName": "workflow_resource:list.userTask / Root / Danh sách Leads",
  "variableMetadata": {
    "multipleLimit": {"min": 0, "max": 30, "warning": ""},
    "linkField": "id",
    "objectSlug": "lead",
    "object": "OT00000000011"
  }
}
```
- `variable` = đường dẫn đến trường danh sách (thường là trường lookup nhiều giá trị trong userTask trước, hoặc output của get records action,...)
- `variableDataType` = kiểu dữ liệu (thường là `"RECORD"` cho danh sách lookup)
- `variableMetadata` = metadata của trường danh sách (copy từ `fieldMetaData` của trường lookup tương ứng, đổi key từ snake_case sang camelCase). Giá trị `objectSlug` và `object` (objectTypeId) **BẮT BUỘC** lấy từ skill `/object-info` (xem mục 25 trong Lưu ý quan trọng)

##### Trường hợp đặc biệt: Loop qua mảng từ Webhook (`$flow.input.<array>`)

Khi biến loop là mảng object từ webhook (ví dụ: `$flow.input.records`), không có `objectTypeId` thực sự. Dùng `textMeta` làm `variableMetadata`:

```json
{
  "variable": "$flow.input.records",
  "variableDataType": "RECORD",
  "variablePathName": "workflow_resource:list.resource / Input / records",
  "variableMetadata": {
    "characterLimit": {"min": 0, "max": 131072, "warning": "warning limit note"},
    "richText": "false"
  }
}
```

Và `currentItem` trong resources.loops dùng cùng `metaDataType: textMeta`:

```json
{
  "absoluteSlug": "$loop.loop_records.currentItem",
  "dataType": "RECORD",
  "metaDataType": {
    "characterLimit": {"min": 0, "max": 131072, "warning": "warning limit note"},
    "richText": "false"
  },
  "slug": "currentItem"
}
```

⚠️ Để `$flow.input.records` được nhận ra là list, trong `parseToDataType.children` PHẢI khai báo `isList: true` và có đầy đủ `children` (các trường con).
- `variablePathName` = tên hiển thị đường dẫn

#### 2. Direction (Hướng duyệt)
```json
{
  "direction": 1
}
```
- `1` = duyệt từ bản ghi đầu tiên đến bản ghi cuối cùng
- `2` = duyệt từ bản ghi cuối cùng đến bản ghi đầu tiên

#### 3. Branches (Các nhánh)
```json
{
  "forEachBranch": "{FOR_EACH_FLOW_ID}",
  "afterLastItemBranch": "{AFTER_LAST_FLOW_ID}"
}
```
- `forEachBranch` = ID của flow "For each item" (flow chạy cho mỗi item)
- `afterLastItemBranch` = ID của flow "After last item" (flow chạy sau khi duyệt hết)

### Resources của Loop Task

Loop Task tạo ra các resources đặc biệt có thể sử dụng trong các task bên trong vòng lặp:

```json
{
  "resources": {
    "loops": [
      {
        "forEachBranch": "{FOR_EACH_FLOW_ID}",
        "name": "{LOOP_NAME}",
        "variable": "$userTask.{task_slug}.{field_slug}",
        "description": "",
        "resources": [
          {
            "absoluteSlug": "$loop.{loop_slug}.count",
            "parentMetadata": "",
            "editable": false,
            "dataType": "NUMBER",
            "type": 1,
            "isList": false,
            "parentId": "{LOOP_NODE_ID}",
            "assignable": false,
            "availableForInput": true,
            "isStandard": true,
            "processId": "{PROCESS_ID}",
            "name": "Count",
            "metaDataType": {
              "valueLimit": {"min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note"},
              "displayType": 2,
              "multipleLimit": {"min": 1, "max": 30, "warning": "warning limit note"},
              "format": {"format": 2, "type": 1},
              "integralLength": 10,
              "roundRule": "1",
              "fractionalLength": 6
            },
            "availableForOutput": true,
            "absolutePath": "workflow_resource:list.loop / {LOOP_NAME} / Count",
            "id": "{RESOURCE_ID_COUNT}",
            "parentTable": "loop",
            "slug": "count"
          },
          {
            "absoluteSlug": "$loop.{loop_slug}.currentItem",
            "parentMetadata": "",
            "editable": false,
            "dataType": "RECORD",
            "type": 1,
            "isList": false,
            "parentId": "{LOOP_NODE_ID}",
            "assignable": false,
            "availableForInput": true,
            "isStandard": true,
            "processId": "{PROCESS_ID}",
            "name": "Current Item",
            "metaDataType": {
              "multipleLimit": {"min": 0, "max": 30, "warning": ""},
              "linkField": "id",
              "objectSlug": "{object_slug}",
              "object": "{OBJECT_TYPE_ID}"
            },
            "availableForOutput": true,
            "absolutePath": "workflow_resource:list.loop / {LOOP_NAME} / Current Item",
            "id": "{RESOURCE_ID_CURRENT_ITEM}",
            "parentTable": "loop",
            "slug": "currentItem"
          }
        ],
        "nodeId": "{LOOP_NODE_ID}",
        "afterLastItemBranch": "{AFTER_LAST_FLOW_ID}",
        "slug": "{loop_slug}",
        "direction": 1
      }
    ]
  }
}
```

**Chi tiết Resources:**
- `$loop.{loop_slug}.count` = số thứ tự của item hiện tại (NUMBER)
- `$loop.{loop_slug}.currentItem` = item hiện tại đang được duyệt (RECORD), có metadata trùng với object type của danh sách

### Cập nhật resourcesUsedIn

Khi resource của Loop (ví dụ: `$loop.loop_leads.currentItem`) được sử dụng trong action bên trong vòng lặp, cần thêm `resourcesUsedIn` vào resource `currentItem`:

```json
{
  "resourcesUsedIn": [
    {
      "actionType": "SEND_NOTIFICATION",
      "name": "Gửi thông báo",
      "count": 2,
      "id": "{ACTION_ID}",
      "parentTable": "action",
      "slug": "gui_thong_bao"
    }
  ]
}
```

Tương tự, trường danh sách trong userTask (dùng làm biến duyệt) cần có `resourcesUsedIn` trỏ đến Loop:
```json
{
  "resourcesUsedIn": [
    {
      "name": "{LOOP_NAME}",
      "count": 1,
      "id": "{LOOP_NODE_ID}",
      "parentTable": "loop",
      "slug": "{loop_slug}"
    }
  ]
}
```

### Sử dụng biến Loop trong các task bên trong vòng lặp

Các task nằm trong nhánh "For each item" có thể sử dụng biến của Loop:

**Ví dụ sử dụng trong tiêu đề thông báo (type: 5 = biến ghép trong chuỗi):**
```json
{
  "title": {
    "type": 5,
    "value": "Lead: $loop.loop_leads.currentItem.name"
  }
}
```

**Ví dụ sử dụng trong nội dung thông báo:**
```json
{
  "content": {
    "type": "text/html",
    "content": {
      "type": 5,
      "value": "<div>Lead:&nbsp;$loop.loop_leads.currentItem.name</div>"
    }
  }
}
```

**Lưu ý:** `type: 5` dùng khi biến được ghép trong chuỗi (ví dụ: `"Lead: $loop.loop_leads.currentItem.name"`).

### externalResourcesUsedIn

Khi sử dụng các trường con của `currentItem` (ví dụ: `$loop.loop_leads.currentItem.name`), cần thêm vào mảng `externalResourcesUsedIn` ở root level:

```json
{
  "externalResourcesUsedIn": [
    {
      "absoluteSlug": "$loop.{loop_slug}.currentItem.name",
      "parentMetadata": "",
      "dataType": "TEXT",
      "type": 1,
      "isList": false,
      "parentId": "{RESOURCE_ID_CURRENT_ITEM}",
      "isSystem": false,
      "availableForInput": false,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "name": "Title",
      "availableForOutput": false,
      "absolutePath": "workflow_resource:list.loop / {LOOP_NAME} / Current Item / Title",
      "parentTable": "resource",
      "slug": "name"
    }
  ]
}
```

### Tính toán vị trí cho bố cục trực quan của Loop

Loop có bố cục đặc biệt do tạo vòng lặp:
- Loop Task: nằm trên luồng chính (y=260)
- Nhánh "For each item": đi sang phải đến task xử lý (cùng y=260)
- Flow quay lại: từ task xử lý đi lên trên (y=210) rồi quay về Loop Task
- Nhánh "After last item": đi xuống dưới đến End Event (y=450)

**Ví dụ vị trí:**
```
Loop Task:        x=360, y=260 (width=60, height=60)
Task xử lý:      x=580, y=260 (width=60, height=60)
End Event:        x=360, y=450 (width=60, height=60)

Flow "For each item":   (420,290) -> (580,290)
Flow quay lại:           (610,260) -> (610,210) -> (390,210) -> (390,260)
Flow "After last item":  (390,320) -> (390,450)
```

### Ví dụ quy trình với Loop Task

**Mô tả:** Start -> Root -> Loop Leads -> (For each item) -> Gửi thông báo -> Loop Leads / (After last item) -> End Process

```
Bắt đầu -> Root (User Task) -> Loop Leads (Loop Task)
  Loop Leads:
    Nhánh "For each item" -> Gửi thông báo (Send Notification) -> quay lại Loop Leads
    Nhánh "After last item" -> Kết thúc quy trình
```

**Cấu hình:**
- User Task "Root" có trường "Danh sách Leads" kiểu lookup tới Lead, nhiều giá trị (`multiple: true`)
- Loop "Loop Leads":
  - variable: `$userTask.Root.danh_sach_leads`
  - direction: `1` (từ đầu đến cuối)
- Trong nhánh "For each item": Send Notification sử dụng `$loop.loop_leads.currentItem.name` để lấy tên lead hiện tại

### Pattern kiểm thử Loop cho Normal Flow

Không phụ thuộc User Task để tạo list. Dùng Get Records với `resultType: 2` rồi truyền `$action.{get_slug}.output.records` vào Loop. Trong create payload, `variablePathName` có thể dùng `workflow_resource:list.action / {Get Name} / Output / Records`; server có thể canonicalize GET-back thành `workflow_resource:list.getRecord / ...`. Nếu absolute slug, type/list metadata và runtime đúng, không PUT chỉ để đổi display path. Trong nhánh `for_each_item`, dùng một hiệu ứng observable như Send Notification chứa ID/tên của `currentItem`, sau đó flow quay lại Loop; nhánh `after_last_item` đi tới End Process.

- Test `direction: 1` và `direction: 2` bằng hai process/lượt chạy riêng; đối chiếu thứ tự notification với danh sách Get Records có sort cố định.
- Không dùng `$loop.{slug}.count` sau khi Loop kết thúc để chứng minh số vòng: runtime reset count về 0 và currentItem về null khi hết list.
- Nếu cần chứng minh số vòng, tăng một biến accumulator trong nhánh loop hoặc đếm notification/action output observable rồi kiểm tra downstream.

---
