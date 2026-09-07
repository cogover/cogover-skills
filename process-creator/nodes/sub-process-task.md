## Sub Process (Task Gọi Quy Trình Con)

### Mô tả
Sub Process là một task hệ thống cho phép khởi chạy một quy trình con từ quy trình cha. Nó hỗ trợ truyền biến từ quy trình cha vào quy trình con (input) và nhận biến trả về từ quy trình con (output). Sub Process thường được dùng khi cần tái sử dụng một quy trình đã có sẵn như một bước trong quy trình khác.

### Cấu trúc trong BPMN XML
```xml
<elEx:subProcess id="{SUB_PROCESS_NODE_ID}" name="{SUB_PROCESS_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="SUB_PROCESS" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:subProcess>
```

**Lưu ý quan trọng:**
- Sử dụng `elEx:subProcess` (cần namespace `xmlns:elEx="http://element-ex/schema"`)
- `renderKey="SUB_PROCESS"`
- Node ID dùng prefix `NO` như các node khác

### Cấu trúc `actions` trong JSON
Thêm vào mảng `actions` ở root level với cấu trúc sau:
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
        "starterPersonnelId": {
          "raw": false,
          "value": "{SUBMITTED_BY_RESOURCE}"
        },
        "starterPersonnelIdForFe": {
          "raw": false,
          "valuePathName": "{DISPLAY_PATH_CUA_SUBMITTED_BY}",
          "valueDataType": "RECORD",
          "value": "{SUBMITTED_BY_RESOURCE}"
        },
        "recordId": {
          "raw": false,
          "value": "{RECORD_RESOURCE}"
        },
        "recordIdForFe": {
          "raw": false,
          "valuePathName": "{DISPLAY_PATH_CUA_RECORD}",
          "valueDataType": "RECORD",
          "value": "{RECORD_RESOURCE}"
        },
        "webhookInputBody": {
          "raw": false,
          "value": "{WEBHOOK_BODY_RESOURCE}"
        },
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

### Chi tiết các trường cấu hình Sub Process

| Trường                    | Mô tả                                                                                                               |
|---------------------------|---------------------------------------------------------------------------------------------------------------------|
| `actionType`              | Luôn là `"SUB_PROCESS"`                                                                                             |
| `subWorkflowId`           | Process ID (PE...) của quy trình con — **BẮT BUỘC** phải là ID thực tế đã tồn tại trong hệ thống, **KHÔNG ĐƯỢC** tự sinh. Cần hỏi người dùng cung cấp cả `subWorkflowId` và `processInfoId` vì đây là 2 ID độc lập, không thể suy ra từ nhau |
| `processInfoId`           | Process Info ID (PI...) của quy trình con — **BẮT BUỘC** phải là ID thực tế đã tồn tại trong hệ thống, **KHÔNG ĐƯỢC** tự sinh |
| `async`                   | `false` = đồng bộ (chờ quy trình con hoàn thành), `true` = bất đồng bộ                                              |
| `startSubProcessError`    | Hành vi khi khởi chạy quy trình con lỗi: `"ERROR"` = dừng quy trình cha nếu khởi chạy quy trình con lỗi, `"IGNORE"` = bỏ qua lỗi và tiếp tục chạy quy trình cha |
| `input`                   | Object truyền biến từ quy trình cha vào quy trình con. Key = biến quy trình con, value = cấu hình giá trị           |
| `output`                  | Object nhận biến trả về từ quy trình con. Key = biến quy trình con, value = biến quy trình cha. **Chỉ có khi `async: false`** (đồng bộ, chờ quy trình con hoàn thành mới nhận được output) |
| `valueInputForFE`         | Mảng mô tả input cho hiển thị trên giao diện (FE)                                                                   |
| `valueOutputForFE`        | Mảng mô tả output cho hiển thị trên giao diện (FE). **Chỉ có khi `async: false`**                                   |
| `starterPersonnelId`      | Chỉ định nhân sự sẽ khởi chạy quy trình con (**bắt buộc** khi quy trình con là `manual_flow` hoặc `sequence_flow`)  |
| `starterPersonnelIdForFe` | Thông tin hiển thị FE của starterPersonnelId (**bắt buộc** khi quy trình con là `manual_flow` hoặc `sequence_flow`) |
| `recordId`                | Chỉ định bản ghi sẽ kết nối khi khởi chạy quy trình con (**bắt buộc** chỉ khi quy trình con là `sequence_flow`)     |
| `recordIdForFe`           | Thông tin hiển thị FE của recordId (**bắt buộc** chỉ khi quy trình con là `sequence_flow`)                           |
| `webhookInputBody`        | Nội dung body gửi cho webhook trigger (**bắt buộc** chỉ khi quy trình con là `triggered_flow`)                       |
| `webhookInputBodyForFE`   | Thông tin hiển thị FE của webhookInputBody (**bắt buộc** chỉ khi quy trình con là `triggered_flow`). **Lưu ý:** key dùng chữ hoa `ForFE` (khác với `starterPersonnelIdForFe` và `recordIdForFe` dùng chữ thường `Fe`) |

### Chi tiết cấu trúc `input` (Truyền biến vào quy trình con)

Trong `input`, **key luôn là biến/tài nguyên của quy trình con**, value là object mô tả giá trị từ quy trình cha:

```json
{
  "input": {
    "$flow.bien_o_quy_trinh_con": {
      "dataType": "NUMBER",
      "raw": false,
      "value": "$userTask.Root.so"
    }
  }
}
```

| Trường     | Mô tả                                                                                          |
|------------|------------------------------------------------------------------------------------------------|
| `dataType` | Kiểu dữ liệu: `"NUMBER"`, `"TEXT"`, `"BOOLEAN"`, `"DATE"`, `"DATE_TIME"`, `"RECORD"`, v.v.     |
| `raw`      | `false` = giá trị ở `value` lấy từ biến/tài nguyên quy trình cha; `true` = giá trị thuần (raw) |
| `value`    | Biến/tài nguyên quy trình cha (khi `raw=false`) hoặc giá trị thuần (khi `raw=true`)            |

### Ràng buộc `output` — chỉ khi `async: false`

**Quan trọng:** `output` và `valueOutputForFE` chỉ có ý nghĩa và chỉ được thêm vào JSON khi `async: false` (đồng bộ — quy trình cha chờ quy trình con hoàn thành). Khi `async: true` (bất đồng bộ), quy trình cha không chờ quy trình con nên **không thể nhận output** — không thêm `output` và `valueOutputForFE`.

### Chi tiết cấu trúc `output` (Nhận biến trả về từ quy trình con)

Trong `output`, **key luôn là biến/tài nguyên của quy trình con**, value là biến/tài nguyên của quy trình cha sẽ nhận giá trị trả về:

```json
{
  "output": {
    "$flow.bien_o_quy_trinh_con_1": "$flow.bien_o_quy_trinh_cha_1",
    "$flow.bien_o_quy_trinh_con_2": "$flow.bien_o_quy_trinh_cha_2"
  }
}
```

**Lưu ý:** Biến/tài nguyên quy trình cha dùng trong output cần có `availableForInput: true` và `availableForOutput: true`.

### Điều kiện để gán biến giữa quy trình cha và con

Để gán giá trị giữa quy trình cha và con (cả input lẫn output), cần đủ **3 điều kiện**:

1. **Cùng kiểu dữ liệu**: Biến/tài nguyên ở quy trình cha có cùng kiểu dữ liệu với biến/tài nguyên ở quy trình con (ví dụ: cùng là NUMBER/TEXT/..., nếu là RECORD thì cùng objectTypeId)
2. **Cấu hình availableForInput/Output**: Biến/tài nguyên ở quy trình con cần được cấu hình `availableForInput: true` và `availableForOutput: true`
3. **Cùng isList**: Biến/tài nguyên ở quy trình cha và quy trình con phải cùng là `isList: true` hoặc cùng là `isList: false`

### starterPersonnelId (Dành cho manual_flow và sequence_flow)

Khi quy trình con là `manual_flow` hoặc `sequence_flow`, cần chỉ định nhân sự giả lập khởi chạy quy trình con qua `starterPersonnelId` và `starterPersonnelIdForFe`:

```json
{
  "starterPersonnelId": {
    "raw": false,
    "value": "$userTask.Root.submittedBy"
  },
  "starterPersonnelIdForFe": {
    "raw": false,
    "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
    "valueDataType": "RECORD",
    "value": "$userTask.Root.submittedBy"
  }
}
```

**Lưu ý:** Nếu quy trình con **không phải** `manual_flow` hay `sequence_flow` (`normal_flow`, `triggered_flow`, `scheduled_flow`), thì **không cần** `starterPersonnelId` và `starterPersonnelIdForFe`.

### recordId (Dành cho sequence_flow)

Khi quy trình con là `sequence_flow`, **bắt buộc** chỉ định bản ghi sẽ kết nối qua `recordId` và `recordIdForFe`:

```json
{
  "recordId": {
    "raw": false,
    "value": "$userTask.Root.contact"
  },
  "recordIdForFe": {
    "raw": false,
    "valuePathName": "workflow_resource:list.userTask / Root / Contact",
    "valueDataType": "RECORD",
    "value": "$userTask.Root.contact"
  }
}
```

**Lưu ý:** `recordId` chỉ cần khi quy trình con là `sequence_flow`. Các loại khác (`manual_flow`, `normal_flow`, `triggered_flow`, `scheduled_flow`) **không cần** `recordId` và `recordIdForFe`.

### webhookInputBody (Dành cho triggered_flow)

Khi quy trình con là `triggered_flow` (webhook), **bắt buộc** cung cấp nội dung body cho webhook qua `webhookInputBody` và `webhookInputBodyForFE`:

```json
{
  "webhookInputBody": {
    "raw": false,
    "value": "{WEBHOOK_BODY_RESOURCE}"
  },
  "webhookInputBodyForFE": {
    "raw": false,
    "valuePathName": "{DISPLAY_PATH_CUA_WEBHOOK_BODY}",
    "valueDataType": "TEXT",
    "value": "{WEBHOOK_BODY_RESOURCE}"
  }
}
```

**Lưu ý:**
- `webhookInputBody` chỉ cần khi quy trình con là `triggered_flow`. Các loại khác **không cần**.
- Key FE dùng chữ hoa `webhookInputBodyForFE` (khác với `starterPersonnelIdForFe` và `recordIdForFe` dùng chữ thường `Fe`).

### Bảng tổng hợp fields bắt buộc theo loại quy trình con

| Loại quy trình con | `starterPersonnelId` | `recordId` | `webhookInputBody` | `output` (nhận biến trả về) |
|---------------------|----------------------|------------|---------------------|-----------------------------|
| `manual_flow`       | **Bắt buộc**         | Không cần  | Không cần           | Chỉ khi `async: false`     |
| `normal_flow`       | Không cần            | Không cần  | Không cần           | Chỉ khi `async: false`     |
| `sequence_flow`     | **Bắt buộc**         | **Bắt buộc** | Không cần         | Chỉ khi `async: false`     |
| `triggered_flow`    | Không cần            | Không cần  | **Bắt buộc**        | Chỉ khi `async: false`     |
| `scheduled_flow`    | Không cần            | Không cần  | Không cần           | Chỉ khi `async: false`     |

**Lưu ý:** Mỗi trường có cặp `ForFe`/`ForFE` tương ứng cũng bắt buộc khi trường chính bắt buộc.

Với `normal_flow`, chỉ cấu hình mapping `input`/`output` theo nhu cầu. Không gửi `starterPersonnelId`, `recordId` hoặc `webhookInputBody` cùng các field FE tương ứng.

### Resources của Sub Process

Trong `resources.actions[]`, mỗi Sub Process có 3 resource chuẩn: `startAt`, `endAt` và `output`.

| Resource  | Mô tả                                | dataType  | isList |
|-----------|--------------------------------------|-----------|--------|
| `startAt` | Thời điểm bắt đầu chạy quy trình con | DATE_TIME | false  |
| `endAt`   | Thời điểm kết thúc quy trình con     | DATE_TIME | false  |
| `output`  | Kết quả trả về từ quy trình con      | RECORD    | false  |

Resource `output` có 2 children:

| Child    | Mô tả                                              | dataType |
|----------|----------------------------------------------------|----------|
| `status` | Trạng thái kết thúc quy trình con                  | TEXT     |
| `result` | Bản ghi kết quả (dùng để truy xuất dữ liệu trả về) | RECORD   |

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
      "metaDataType": {
        "defaultValueCurrent": false,
        "format": {
          "date": "dd/MM/yyyy",
          "time": "hh:mm:ss"
        },
        "timeZone": "Asia/Saigon"
      },
      "availableForOutput": true,
      "absolutePath": "workflow_resource:list.subProcess / {SUB_PROCESS_NAME} / StartAt",
      "id": "{RESOURCE_ID_1}",
      "parentTable": "action",
      "slug": "startAt"
    },
    {
      "absoluteSlug": "$action.{sub_process_slug}.endAt",
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
      "absolutePath": "workflow_resource:list.subProcess / {SUB_PROCESS_NAME} / End At",
      "id": "{RESOURCE_ID_2}",
      "parentTable": "action",
      "slug": "endAt"
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
          "metaDataType": {
            "characterLimit": {
              "min": 0,
              "max": 131072,
              "warning": "warning limit note"
            },
            "richText": "false"
          },
          "availableForOutput": true,
          "absolutePath": "workflow_resource:list.subProcess / {SUB_PROCESS_NAME} / Output / Status",
          "parentTable": "resource",
          "slug": "status"
        },
        {
          "absoluteSlug": "$action.{sub_process_slug}.output.result",
          "parentMetadata": "",
          "editable": false,
          "dataType": "RECORD",
          "type": 1,
          "isList": false,
          "parentId": "{RESOURCE_ID_3}",
          "assignable": false,
          "availableForInput": true,
          "isStandard": true,
          "processId": "{PROCESS_ID}",
          "name": "Result",
          "metaDataType": {
            "multipleLimit": {
              "min": 0,
              "max": 30,
              "warning": "warning limit note"
            },
            "linkField": "id"
          },
          "availableForOutput": true,
          "absolutePath": "workflow_resource:list.subProcess / {SUB_PROCESS_NAME} / Output / Result",
          "parentTable": "resource",
          "slug": "result"
        }
      ],
      "name": "Output",
      "metaDataType": {
        "characterLimit": {
          "min": 0,
          "max": 131072,
          "warning": "warning limit note"
        },
        "richText": "false"
      },
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

**Lưu ý:**
- `absolutePath` dùng prefix `workflow_resource:list.subProcess` (khác với Send Email dùng `list.sendEmail`, Wait dùng `list.wait`)
- Resource `output` có `actionType: "SUB_PROCESS"` (các resource khác không có trường này)
- Children của `output` có `parentTable: "resource"` (khác với resource gốc dùng `parentTable: "action"`)

### Cập nhật resourcesUsedIn

Khi biến/tài nguyên của quy trình cha được dùng trong input của Sub Process, cần thêm `resourcesUsedIn` vào resource tương ứng:

```json
{
  "absoluteSlug": "$userTask.Root.so",
  ...
  "resourcesUsedIn": [
    {
      "actionType": "SUB_PROCESS",
      "name": "{SUB_PROCESS_NAME}",
      "count": 1,
      "id": "{ACTION_ID}",
      "parentTable": "action",
      "slug": "{sub_process_slug}"
    }
  ]
}
```

### Biến quy trình cha dùng cho output

Biến ở quy trình cha nhận giá trị trả về từ quy trình con cần có `availableForInput: true` và `availableForOutput: true`:

```json
{
  "absoluteSlug": "$flow.so_tren_quy_trinh_cha",
  "editable": true,
  "dataType": "NUMBER",
  "type": 1,
  "isList": false,
  "assignable": true,
  "availableForInput": true,
  "availableForOutput": true,
  ...
}
```

### Ví dụ đầy đủ

**Ví dụ: Quy trình cha gọi quy trình con là manual_flow, truyền biến số và record, nhận biến trả về:**

```json
{
  "data": {
    "output": {
      "$flow.bien_number_o_quy_trinh_con_1": "$flow.so_tren_quy_trinh_cha",
      "$flow.bien_record_o_quy_trinh_con_1": "$flow.record_tren_quy_trinh_cha"
    },
    "async": false,
    "input": {
      "$flow.bien_number_o_quy_trinh_con_2": {
        "dataType": "NUMBER",
        "raw": false,
        "value": "$userTask.Root.so"
      },
      "$flow.bien_record_o_quy_trinh_con_2": {
        "dataType": "RECORD",
        "raw": false,
        "value": "$userTask.Root.contact"
      }
    },
    "actionType": "SUB_PROCESS",
    "subWorkflowId": "PE00000000001",
    "startSubProcessError": "ERROR",
    "processInfoId": "PI00000000001",
    "valueInputForFE": [
      {
        "absoluteSlug": "$flow.bien_number_o_quy_trinh_con_2",
        "dataType": "NUMBER",
        "raw": false,
        "valuePathName": "workflow_resource:list.userTask / Root / So",
        "valueDataType": "NUMBER",
        "value": "$userTask.Root.so"
      },
      {
        "absoluteSlug": "$flow.bien_record_o_quy_trinh_con_2",
        "dataType": "RECORD",
        "raw": false,
        "valuePathName": "workflow_resource:list.userTask / Root / Contact",
        "valueDataType": "RECORD",
        "value": "$userTask.Root.contact"
      }
    ],
    "valueOutputForFE": [
      {
        "absoluteSlug": "$flow.bien_number_o_quy_trinh_con_1",
        "valuePathName": "workflow_resource:list.variable / Số trên quy trình cha",
        "valueDataType": "NUMBER",
        "value": "$flow.so_tren_quy_trinh_cha"
      },
      {
        "absoluteSlug": "$flow.bien_record_o_quy_trinh_con_1",
        "valuePathName": "workflow_resource:list.variable / Record trên quy trình cha",
        "valueDataType": "RECORD",
        "value": "$flow.record_tren_quy_trinh_cha"
      }
    ],
    "starterPersonnelId": {
      "raw": false,
      "value": "$userTask.Root.submittedBy"
    },
    "starterPersonnelIdForFe": {
      "raw": false,
      "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
      "valueDataType": "RECORD",
      "value": "$userTask.Root.submittedBy"
    }
  },
  "processId": "{PROCESS_ID}",
  "name": "Goi quy trinh con la manual_flow",
  "description": "",
  "id": "AC00000000001",
  "type": "SUB_PROCESS",
  "nodeId": "NO00000000004",
  "slug": "goi_quy_trinh_con_la_manual_flow"
}
```

---
