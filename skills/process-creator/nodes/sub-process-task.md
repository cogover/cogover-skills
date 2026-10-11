## Sub Process (Task Gọi Quy Trình Con)

Task hệ thống khởi chạy một quy trình con từ quy trình cha, truyền biến vào (input) và nhận biến trả về (output); dùng để tái sử dụng quy trình có sẵn như một bước. Quy trình con thường là Normal Flow: [normal-flow.md](normal-flow.md). Mẫu: `samples/sample_process_call_sub_process.json` (quy trình con `manual_flow`). Tiêu chí PASS runtime: [runtime-validation.md](runtime-validation.md#tiêu-chí-observable-theo-node).

### BPMN XML

```xml
<elEx:subProcess id="{SUB_PROCESS_NODE_ID}" name="{SUB_PROCESS_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="SUB_PROCESS" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:subProcess>
```

Element `elEx:subProcess`; khai báo `xmlns:elEx="http://element-ex/schema"` trong `bpmn2:definitions` ([namespace](../references/bpmn-xml-and-diagram.md#namespace-và-kết-nối-logic)).

### `actions` trong JSON

```json
{
  "actions": [
    {
      "data": {
        "actionType": "SUB_PROCESS",
        "subWorkflowId": "{SUB_WORKFLOW_PROCESS_ID}",
        "processInfoId": "{SUB_WORKFLOW_PROCESS_INFO_ID}",
        "async": false,
        "startSubProcessError": "ERROR",
        "input": {
          "{BIEN_QUY_TRINH_CON_1}": {
            "dataType": "{DATA_TYPE}",
            "raw": false,
            "value": "{BIEN_HOAC_RESOURCE_QUY_TRINH_CHA}"
          }
        },
        "output": {
          "{BIEN_QUY_TRINH_CON_2}": "{BIEN_QUY_TRINH_CHA}"
        },
        "valueInputForFE": [
          {
            "absoluteSlug": "{BIEN_QUY_TRINH_CON_1}",
            "dataType": "{DATA_TYPE}",
            "raw": false,
            "valuePathName": "{DISPLAY_PATH_CUA_BIEN_QUY_TRINH_CHA}",
            "valueDataType": "{DATA_TYPE}",
            "value": "{BIEN_HOAC_RESOURCE_QUY_TRINH_CHA}"
          }
        ],
        "valueOutputForFE": [
          {
            "absoluteSlug": "{BIEN_QUY_TRINH_CON_2}",
            "valuePathName": "{DISPLAY_PATH_CUA_BIEN_QUY_TRINH_CHA}",
            "valueDataType": "{DATA_TYPE}",
            "value": "{BIEN_QUY_TRINH_CHA}"
          }
        ],
        "starterPersonnelId": { "raw": false, "value": "{SUBMITTED_BY_RESOURCE}" },
        "starterPersonnelIdForFe": {
          "raw": false,
          "valuePathName": "{DISPLAY_PATH_CUA_SUBMITTED_BY}",
          "valueDataType": "RECORD",
          "value": "{SUBMITTED_BY_RESOURCE}"
        },
        "recordId": { "raw": false, "value": "{RECORD_RESOURCE}" },
        "recordIdForFe": {
          "raw": false,
          "valuePathName": "{DISPLAY_PATH_CUA_RECORD}",
          "valueDataType": "RECORD",
          "value": "{RECORD_RESOURCE}"
        },
        "webhookInputBody": { "raw": false, "value": "{WEBHOOK_BODY_RESOURCE}" },
        "webhookInputBodyForFE": {
          "raw": false,
          "valuePathName": "{DISPLAY_PATH_CUA_WEBHOOK_BODY}",
          "valueDataType": "TEXT",
          "value": "{WEBHOOK_BODY_RESOURCE}"
        }
      },
      "processId": "{PROCESS_ID}",
      "name": "{SUB_PROCESS_NAME}",
      "description": "",
      "id": "{ACTION_ID}",
      "type": "SUB_PROCESS",
      "nodeId": "{SUB_PROCESS_NODE_ID}",
      "slug": "{sub_process_slug}"
    }
  ]
}
```

### Các trường trong `data`

| Trường | Mô tả |
|---|---|
| `actionType` | Luôn `"SUB_PROCESS"` |
| `subWorkflowId` | Process ID (`PE...`) của quy trình con: BẮT BUỘC là ID thật đã tồn tại, KHÔNG tự sinh |
| `processInfoId` | Process Info ID (`PI...`) của quy trình con: BẮT BUỘC ID thật, KHÔNG tự sinh. Hai ID độc lập, không suy ra từ nhau; hỏi người dùng cung cấp cả hai |
| `async` | `false` đồng bộ (chờ quy trình con hoàn thành); `true` bất đồng bộ |
| `startSubProcessError` | `"ERROR"` dừng quy trình cha khi khởi chạy con lỗi; `"IGNORE"` bỏ qua lỗi, tiếp tục cha |
| `input` | Object truyền biến vào con: key = biến/tài nguyên **quy trình con** (`$flow.bien_o_quy_trinh_con`), value `{dataType, raw, value}`; `dataType` `NUMBER`/`TEXT`/`BOOLEAN`/`DATE`/`DATE_TIME`/`RECORD`...; `raw: false` → `value` là biến/tài nguyên cha (ví dụ `$userTask.Root.so`), `raw: true` → giá trị thuần |
| `output` | Object nhận biến trả về: key = biến **quy trình con**, value = biến **quy trình cha** nhận giá trị (`{"$flow.bien_o_quy_trinh_con_1": "$flow.bien_o_quy_trinh_cha_1"}`). **Chỉ có khi `async: false`**; `async: true` không chờ con nên không nhận output — không thêm `output` và `valueOutputForFE` |
| `valueInputForFE` | Mảng mô tả input cho giao diện: `{absoluteSlug (biến con), dataType, raw, valuePathName, valueDataType, value}` |
| `valueOutputForFE` | Mảng mô tả output cho giao diện: `{absoluteSlug, valuePathName, valueDataType, value}`; chỉ khi `async: false` |
| `starterPersonnelId` + `starterPersonnelIdForFe` | Nhân sự giả lập khởi chạy quy trình con: `{raw, value}` và `{raw, valuePathName, valueDataType: "RECORD", value}` (ví dụ `$userTask.Root.submittedBy`, `workflow_resource:list.userTask / Root / Submitted By`); **bắt buộc** khi con là `manual_flow` hoặc `sequence_flow` |
| `recordId` + `recordIdForFe` | Bản ghi kết nối khi khởi chạy con, cùng cấu trúc (ví dụ `$userTask.Root.contact`); **bắt buộc chỉ khi** con là `sequence_flow` |
| `webhookInputBody` + `webhookInputBodyForFE` | Body gửi cho webhook trigger (`valueDataType: "TEXT"`); **bắt buộc chỉ khi** con là `triggered_flow` (webhook). Key FE viết hoa `ForFE`, khác `starterPersonnelIdForFe`/`recordIdForFe` viết `Fe` |

| Loại quy trình con | `starterPersonnelId` | `recordId` | `webhookInputBody` | `output` |
|---|---|---|---|---|
| `manual_flow` | Bắt buộc | Không | Không | Chỉ khi `async: false` |
| `normal_flow` | Không | Không | Không | Chỉ khi `async: false` |
| `sequence_flow` | Bắt buộc | Bắt buộc | Không | Chỉ khi `async: false` |
| `triggered_flow` | Không | Không | Bắt buộc | Chỉ khi `async: false` |
| `scheduled_flow` | Không | Không | Không | Chỉ khi `async: false` |

Cặp `ForFe`/`ForFE` bắt buộc cùng trường chính. Trường không bắt buộc cho loại con đó thì không gửi (`normal_flow`: chỉ mapping `input`/`output`).

### Điều kiện gán biến giữa cha và con (input lẫn output)

1. Cùng kiểu dữ liệu (NUMBER/TEXT/...; RECORD phải cùng objectTypeId).
2. Biến/tài nguyên ở quy trình con có `availableForInput: true` và `availableForOutput: true`; biến cha nhận output cũng cần `availableForInput: true` và `availableForOutput: true`.
3. Cùng `isList` (`true` cả hai hoặc `false` cả hai).

### Resources của action (`resources.actions[]`)

| Resource | Mô tả | dataType | isList |
|---|---|---|---|
| `startAt` | Thời điểm bắt đầu chạy quy trình con | DATE_TIME | false |
| `endAt` | Thời điểm kết thúc quy trình con | DATE_TIME | false |
| `output` | Kết quả trả về; children `status` (TEXT, trạng thái kết thúc) và `result` (RECORD, bản ghi kết quả) | RECORD | false |

`absolutePath` dùng prefix `workflow_resource:list.subProcess` (Send Email dùng `list.sendEmail`, Wait dùng `list.wait`); resource `output` có `actionType: "SUB_PROCESS"` (resource khác không có); children của `output` dùng `parentTable: "resource"` (resource gốc dùng `"action"`).

```json
{
  "processId": "{PROCESS_ID}",
  "name": "{SUB_PROCESS_NAME}",
  "description": "",
  "resources": [
    {
      "absoluteSlug": "$action.{sub_process_slug}.startAt",
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
      "metaDataType": { "defaultValueCurrent": false, "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" }, "timeZone": "Asia/Saigon" },
      "availableForOutput": true,
      "absolutePath": "workflow_resource:list.subProcess / {SUB_PROCESS_NAME} / StartAt",
      "id": "{RESOURCE_ID_1}",
      "parentTable": "action",
      "slug": "startAt"
    },
    {
      "absoluteSlug": "$action.{sub_process_slug}.endAt",
      "name": "End At",
      "absolutePath": "workflow_resource:list.subProcess / {SUB_PROCESS_NAME} / End At",
      "id": "{RESOURCE_ID_2}",
      "slug": "endAt",
      "...": "các key còn lại giống startAt"
    },
    {
      "absoluteSlug": "$action.{sub_process_slug}.output",
      "parentMetadata": "",
      "editable": false,
      "dataType": "RECORD",
      "type": 1,
      "isList": false,
      "parentId": "{ACTION_ID}",
      "assignable": false,
      "actionType": "SUB_PROCESS",
      "availableForInput": true,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "children": [
        {
          "absoluteSlug": "$action.{sub_process_slug}.output.status",
          "parentMetadata": "",
          "editable": false,
          "dataType": "TEXT",
          "type": 1,
          "isList": false,
          "parentId": "{RESOURCE_ID_3}",
          "assignable": false,
          "availableForInput": true,
          "isStandard": true,
          "processId": "{PROCESS_ID}",
          "name": "Status",
          "metaDataType": { "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" }, "richText": "false" },
          "availableForOutput": true,
          "absolutePath": "workflow_resource:list.subProcess / {SUB_PROCESS_NAME} / Output / Status",
          "parentTable": "resource",
          "slug": "status"
        },
        {
          "absoluteSlug": "$action.{sub_process_slug}.output.result",
          "dataType": "RECORD",
          "name": "Result",
          "metaDataType": { "multipleLimit": { "min": 0, "max": 30, "warning": "warning limit note" }, "linkField": "id" },
          "absolutePath": "workflow_resource:list.subProcess / {SUB_PROCESS_NAME} / Output / Result",
          "parentTable": "resource",
          "slug": "result",
          "...": "các key còn lại giống status"
        }
      ],
      "name": "Output",
      "metaDataType": { "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" }, "richText": "false" },
      "availableForOutput": true,
      "absolutePath": "workflow_resource:list.subProcess / {SUB_PROCESS_NAME} / Output",
      "id": "{RESOURCE_ID_3}",
      "parentTable": "action",
      "slug": "output"
    }
  ],
  "id": "{ACTION_ID}",
  "type": "SUB_PROCESS",
  "nodeId": "{SUB_PROCESS_NODE_ID}",
  "slug": "{sub_process_slug}"
}
```

### `resourcesUsedIn`

Biến/tài nguyên của quy trình cha dùng trong `input` (ví dụ `$userTask.Root.so`) thêm entry:

```json
{
  "resourcesUsedIn": [
    { "actionType": "SUB_PROCESS", "name": "{SUB_PROCESS_NAME}", "count": 1, "id": "{ACTION_ID}", "parentTable": "action", "slug": "{sub_process_slug}" }
  ]
}
```
