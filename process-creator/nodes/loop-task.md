## Loop Task (Task Vòng Lặp)

Task hệ thống duyệt một danh sách (ví dụ bản ghi từ trường lookup nhiều giá trị): với mỗi item chạy nhánh "For each item"; duyệt hết thì chạy nhánh "After last item". Mẫu: `samples/sample_process_loop.json` (Root có lookup Lead nhiều giá trị → Loop Leads → Send Notification dùng `$loop.loop_leads.currentItem.name` → quay lại Loop; After last item → End Process).

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

- `elEx:loopTask` (KHÔNG phải `bpmn2:userTask`), cần `xmlns:elEx="http://element-ex/schema"` trong `bpmn2:definitions`; `renderKey="LOOP_TASK"`.
- Nhiều incoming: flow từ task trước VÀ flow quay lại từ nhánh "For each item". Đúng 2 outgoing: "For each item" và "After last item".
- BẮT BUỘC: cả 2 flow outgoing có extension `loopFlowType`; thiếu → lỗi `LoopNode must have exactly 2 outgoing flows: forEachItemFlow and afterLastItemFlow`.

```xml
<!-- Chạy cho mỗi item trong danh sách -->
<bpmn2:sequenceFlow id="{FOR_EACH_FLOW_ID}" name="For each item" sourceRef="{LOOP_NODE_ID}" targetRef="{NEXT_TASK_NODE_ID}">
  <bpmn2:extensionElements>
    <configEx:elementInfo loopFlowType="for_each_item" />
  </bpmn2:extensionElements>
</bpmn2:sequenceFlow>
<!-- Chạy sau khi duyệt hết danh sách -->
<bpmn2:sequenceFlow id="{AFTER_LAST_FLOW_ID}" name="After last item" sourceRef="{LOOP_NODE_ID}" targetRef="{END_NODE_ID}">
  <bpmn2:extensionElements>
    <configEx:elementInfo loopFlowType="after_last_item" />
  </bpmn2:extensionElements>
</bpmn2:sequenceFlow>
<!-- Flow quay lại từ task cuối trong vòng lặp về Loop Task -->
<bpmn2:sequenceFlow id="{LOOP_BACK_FLOW_ID}" name="" sourceRef="{LAST_TASK_IN_LOOP}" targetRef="{LOOP_NODE_ID}">
  <bpmn2:extensionElements />
</bpmn2:sequenceFlow>
```

### Cấu trúc `loops` trong JSON

Cấu hình Loop nằm trong mảng `loops` ở root level (không trong `actions`):

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

- `variable`: đường dẫn đến trường danh sách (thường là trường lookup nhiều giá trị của userTask trước, hoặc output của Get Records...), ví dụ `$userTask.Root.danh_sach_leads`; `variableDataType` thường là `"RECORD"`; `variablePathName` là tên hiển thị đường dẫn.
- `variableMetadata`: metadata của trường danh sách, copy từ `fieldMetaData` của trường lookup tương ứng và đổi key từ snake_case sang camelCase. `objectSlug` và `object` (objectTypeId) BẮT BUỘC lấy qua `$object-info` (xem [Chuẩn bị](../SKILL.md#chuẩn-bị)).
- `direction`: `1` duyệt từ bản ghi đầu tiên đến cuối cùng; `2` từ cuối cùng đến đầu tiên.
- `forEachBranch`/`afterLastItemBranch`: ID của flow "For each item"/"After last item".

#### Loop qua mảng từ Webhook (`$flow.input.<array>`)

Biến loop là mảng object từ webhook (ví dụ `$flow.input.records`) không có `objectTypeId` thực sự: dùng textMeta làm `variableMetadata`, và `currentItem` trong `resources.loops` dùng cùng `metaDataType` textMeta này:

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

Để `$flow.input.records` được nhận ra là list, trong `parseToDataType.children` PHẢI khai báo `isList: true` và có đầy đủ `children` (các trường con).

### Resources của Loop Task

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

- `$loop.{loop_slug}.count`: số thứ tự của item hiện tại (NUMBER).
- `$loop.{loop_slug}.currentItem`: item hiện tại đang được duyệt (RECORD), metadata trùng với object type của danh sách.

### Cập nhật `resourcesUsedIn`

Resource của Loop (ví dụ `$loop.loop_leads.currentItem`) được dùng trong action bên trong vòng lặp → thêm vào `resourcesUsedIn` của resource `currentItem`:

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

Trường danh sách trong userTask (dùng làm biến duyệt) có `resourcesUsedIn` trỏ đến Loop:

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

### Dùng biến Loop trong task thuộc nhánh "For each item"

Biến ghép trong chuỗi dùng `type: 5`, ví dụ tiêu đề thông báo `{"title": {"type": 5, "value": "Lead: $loop.loop_leads.currentItem.name"}}`; nội dung HTML tương tự: `{"content": {"type": "text/html", "content": {"type": 5, "value": "<div>Lead:&nbsp;$loop.loop_leads.currentItem.name</div>"}}}`.

Trường con của `currentItem` (ví dụ `$loop.loop_leads.currentItem.name`) phải có trong mảng `externalResourcesUsedIn` ở root level:

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

### Bố cục trực quan của Loop

Loop tạo vòng lặp nên bố cục đặc biệt: Loop Task trên luồng chính (y=260); nhánh "For each item" đi sang phải đến task xử lý (cùng y=260); flow quay lại từ task xử lý đi lên (y=210) rồi về Loop Task; nhánh "After last item" đi xuống End Event (y=450).

```
Loop Task:        x=360, y=260 (width=60, height=60)
Task xử lý:      x=580, y=260 (width=60, height=60)
End Event:        x=360, y=450 (width=60, height=60)

Flow "For each item":   (420,290) -> (580,290)
Flow quay lại:           (610,260) -> (610,210) -> (390,210) -> (390,260)
Flow "After last item":  (390,320) -> (390,450)
```

### Pattern kiểm thử Loop cho Normal Flow

Không phụ thuộc User Task để tạo list. Dùng Get Records với `resultType: 2` rồi truyền `$action.{get_slug}.output.records` vào Loop. Trong create payload, `variablePathName` có thể dùng `workflow_resource:list.action / {Get Name} / Output / Records`; server có thể canonicalize GET-back thành `workflow_resource:list.getRecord / ...`. Nếu absolute slug, type/list metadata và runtime đúng, không PUT chỉ để đổi display path. Trong nhánh `for_each_item`, dùng một hiệu ứng observable như Send Notification chứa ID/tên của `currentItem`, sau đó flow quay lại Loop; nhánh `after_last_item` đi tới End Process.

- Test `direction: 1` và `direction: 2` bằng hai process/lượt chạy riêng; đối chiếu thứ tự notification với danh sách Get Records có sort cố định.
- Không dùng `$loop.{slug}.count` sau khi Loop kết thúc để chứng minh số vòng: runtime reset count về 0 và currentItem về null khi hết list.
- Nếu cần chứng minh số vòng, tăng một biến accumulator trong nhánh loop hoặc đếm notification/action output observable rồi kiểm tra downstream.
