## Organization Task (Task Tổ Chức)

### Mô tả
Organization Task là một task hệ thống tự động truy vấn cấu trúc tổ chức khi luồng chạy đến. Hỗ trợ 4 loại truy vấn:
- **Lấy quản lý trực tiếp** (`filterType: "manager"`) - lọc theo cấp bậc
- **Lấy nhân sự cùng phòng** (`filterType: "personnel"`) - theo phòng ban của một nhân sự
- **Lấy phòng ban** (`filterType: "department"`) - phòng ban của một nhân sự
- **Lấy vị trí công việc** (`filterType: "position"`) - vị trí của một nhân sự

Kết quả có thể lưu trường dữ liệu vào biến (Variable).

### Cấu trúc trong BPMN XML
```xml
<elEx:organizationTask id="{ORGANIZATION_NODE_ID}" name="{ORGANIZATION_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="ORGANIZATION_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:organizationTask>
```

**Lưu ý:**
- Sử dụng `elEx:organizationTask` (cần namespace `xmlns:elEx="http://element-ex/schema"`)
- `renderKey="ORGANIZATION_TASK"`
- Node ID dùng prefix `NO` như các node khác

### Cấu trúc Action trong mảng `actions` ở root level

```json
{
  "data": {
    "objectFieldSavings": [
      {
        "objectFieldSlug": "{FIELD_SLUG}",
        "resource": "{VARIABLE_ABSOLUTE_SLUG}"
      }
    ],
    "criteria": [
      {
        "{CRITERIA_KEY}": {
          "isRawValue": false,
          "displayOrder": 1,
          "value": ["{VALUE}"],
          "option": "{OPTION}",
          "valueForFE": ["{VALUE_FOR_FE}"]
        }
      }
    ],
    "outputSaving": "{OUTPUT_SAVING_TYPE}",
    "filterType": "{FILTER_TYPE}"
  },
  "processId": "{PROCESS_ID}",
  "name": "{ORGANIZATION_NAME}",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "ORGANIZATION",
  "nodeId": "{ORGANIZATION_NODE_ID}",
  "slug": "{organization_slug}"
}
```

**Lưu ý:**
- Tùy `filterType`, cấu trúc `criteria` sẽ khác nhau (xem chi tiết bên dưới).
- Trong criteria object, **KHÔNG** có trường `field`. Tên trường lọc chính là **key** của object (ví dụ: `"personnel"`, `"department"`).

### Chi tiết các trường trong `data`

#### `objectFieldSavings` - Lưu trường vào biến
Mảng chứa cấu hình lưu trường từ kết quả vào biến. Backend chỉ yêu cầu 2 trường:

| Trường             | Bắt buộc | Mô tả                                                                    |
|--------------------|----------|--------------------------------------------------------------------------|
| `objectFieldSlug`  | Có       | Slug của trường trên đối tượng cần lấy (ví dụ: `"account_email"`)        |
| `resource`         | Có       | Đường dẫn tham chiếu biến đích (ví dụ: `"$flow.manageremail"`)           |

**Lưu ý:** `resourceDataType` và `resourcePathName` được backend tự tính toán khi trả response, **KHÔNG cần gửi lên**.

#### `filterType` và `criteria` - Loại lọc và điều kiện

##### Cấu trúc criteria: Hỗ trợ OR/AND logic

Criteria là **mảng 2 chiều** (`criteria[][]` - mảng chứa các group):
- **Giữa các group** (outer array): Logic **OR** — chỉ cần 1 group thoả thì thoả
- **Trong mỗi group** (inner object): Logic **AND** — tất cả criteria trong group phải thoả

```json
{
  "criteria": [
    {
      "personnel": { "option": 2, "value": ["..."], "..." : "..." },
      "department": { "option": 1, "value": ["..."], "..." : "..." }
    },
    {
      "personnel": { "option": 3, "value": ["..."], "..." : "..." }
    }
  ]
}
```
Ví dụ trên: (personnel INCLUDING **VÀ** department PERSONNEL_OF_DEPARTMENT) **HOẶC** (personnel EXCLUDING).

##### Các trường chung trong mỗi criteria item

| Trường         | Mô tả                                                                           |
|----------------|---------------------------------------------------------------------------------|
| `isRawValue`   | `false` nếu `value` là tham chiếu biến, `true` nếu `value` là ID cụ thể         |
| `displayOrder` | Thứ tự hiển thị (bắt đầu từ `1`)                                               |
| `value`        | Mảng chứa giá trị: tham chiếu biến (chuỗi) hoặc ID cụ thể                      |
| `option`       | Giá trị option xác định loại lọc (xem bảng chi tiết bên dưới)                   |
| `valueForFE`   | Giá trị hiển thị cho frontend (xem chi tiết bên dưới)                           |

##### Trường bổ sung chỉ cho `filterType: "manager"`

| Trường               | Mô tả                                                                    |
|----------------------|-------------------------------------------------------------------------|
| `rankOrderOperation` | Phép so sánh cấp bậc: `"gte"` (lớn hơn hoặc bằng), `"equals"` (bằng), `"lte"` (nhỏ hơn hoặc bằng) |
| `rankOrder`          | Giá trị cấp bậc để so sánh (ví dụ: `1`)                                 |
| `levelOfDepartment`  | Cấp phòng ban (thường là `0`)                                           |

---

#### Chi tiết criteria theo từng filterType

##### 1. `filterType: "manager"` - Lấy quản lý trực tiếp

Hỗ trợ 2 loại criteria key:

| Criteria key  | Option | Ý nghĩa             |
|---------------|--------|---------------------|
| `personnel`   | `1`    | INCLUDING_PERSONNEL — chỉ lấy quản lý của các nhân sự được chọn |
| `department`  | `1`    | INCLUDING_DEPARTMENT — chỉ lấy quản lý trong phòng ban được chọn |

**Lưu ý:** Cả 2 criteria key đều có thêm các trường: `rankOrderOperation`, `rankOrder`, `levelOfDepartment`.

```json
{
  "criteria": [{
    "personnel": {
      "rankOrderOperation": "gte",
      "isRawValue": false,
      "displayOrder": 1,
      "levelOfDepartment": 0,
      "rankOrder": 1,
      "value": ["$userTask.Root.submittedBy"],
      "option": 1,
      "valueForFE": [{ "valuePathName": "...", "valueDataType": "RECORD", "value": "$userTask.Root.submittedBy" }]
    }
  }]
}
```

##### 2. `filterType: "personnel"` - Lấy nhân sự

Hỗ trợ 3 loại criteria key:

| Criteria key  | Option | Ý nghĩa                                                  |
|---------------|--------|----------------------------------------------------------|
| `personnel`   | `1`    | ALL_PERSONNEL — tất cả nhân sự                           |
| `personnel`   | `2`    | INCLUDING_PERSONNEL — chỉ các nhân sự được chọn          |
| `personnel`   | `3`    | EXCLUDING_PERSONNEL — tất cả trừ các nhân sự được chọn   |
| `department`  | `1`    | PERSONNEL_OF_DEPARTMENT — nhân sự thuộc phòng ban         |
| `department`  | `2`    | BELONG_TO_DEPARTMENT_AND_ALL_CHILDREN — nhân sự thuộc phòng ban và tất cả phòng ban con |
| `department`  | `3`    | SAME_DEPARTMENT_AS_PERSONNEL — nhân sự cùng phòng ban với nhân sự được chọn |
| `department`  | `4`    | BELONG_TO_DEPARTMENT_OR_PARENT_DEPARTMENT_OF_PERSONNEL — nhân sự thuộc phòng ban hoặc phòng ban cha của nhân sự được chọn |
| `position`    | `1`    | PERSONNEL_HOLDING_ONE_OF_POSITIONS — nhân sự giữ một trong các vị trí được chọn |
| `position`    | `2`    | ANY_POSITION_EXCEPT — nhân sự giữ bất kỳ vị trí nào ngoại trừ |

**Lưu ý:** Khi option = ALL (ví dụ `personnel` option `1`), `value` có thể là mảng rỗng `[]`.

```json
{
  "criteria": [{
    "department": {
      "isRawValue": false,
      "displayOrder": 1,
      "value": ["$userTask.Root.submittedBy"],
      "option": 3,
      "valueForFE": [{ "valuePathName": "...", "valueDataType": "RECORD", "value": "$userTask.Root.submittedBy" }]
    }
  }]
}
```

##### 3. `filterType: "department"` - Lấy phòng ban

Hỗ trợ 3 loại criteria key:

| Criteria key            | Option | Ý nghĩa                                                    |
|-------------------------|--------|-------------------------------------------------------------|
| `department`            | `1`    | ALL_DEPARTMENT — tất cả phòng ban                            |
| `department`            | `2`    | INCLUDING_DEPARTMENT — chỉ các phòng ban được chọn           |
| `department`            | `3`    | EXCLUDING_DEPARTMENT — tất cả trừ các phòng ban được chọn    |
| `departmentOfPersonnel` | `1`    | ALL_PERSONNEL — phòng ban của tất cả nhân sự                 |
| `departmentOfPersonnel` | `2`    | INCLUDING_PERSONNEL — phòng ban của các nhân sự được chọn    |
| `departmentOfPersonnel` | `3`    | EXCLUDING_PERSONNEL — phòng ban của tất cả nhân sự trừ       |
| `position`              | `1`    | ALL_POSITION — tất cả vị trí                                 |
| `position`              | `2`    | INCLUDING_POSITION — chỉ các vị trí được chọn               |

**Lưu ý:** Khi option = ALL (ví dụ `department` option `1`), `value` có thể là mảng rỗng `[]`.

```json
{
  "criteria": [{
    "departmentOfPersonnel": {
      "isRawValue": false,
      "displayOrder": 1,
      "value": ["$userTask.Root.submittedBy"],
      "option": 2,
      "valueForFE": [{ "valuePathName": "...", "valueDataType": "RECORD", "value": "$userTask.Root.submittedBy" }]
    }
  }]
}
```

##### 4. `filterType: "position"` - Lấy vị trí công việc

Hỗ trợ 3 loại criteria key:

| Criteria key  | Option | Ý nghĩa                                                    |
|---------------|--------|-------------------------------------------------------------|
| `position`    | `1`    | ALL_POSITION — tất cả vị trí                                |
| `position`    | `2`    | INCLUDING_POSITION — chỉ các vị trí được chọn              |
| `position`    | `3`    | EXCLUDING_POSITION — tất cả trừ các vị trí được chọn       |
| `department`  | `1`    | ALL_DEPARTMENT — tất cả phòng ban                           |
| `department`  | `2`    | INCLUDING_DEPARTMENT — chỉ các phòng ban được chọn          |
| `department`  | `3`    | EXCLUDING_DEPARTMENT — tất cả trừ các phòng ban được chọn   |
| `personnel`   | `1`    | ONLY_POSITIONS_APPLY_TO_PERSONNEL — chỉ vị trí áp dụng cho nhân sự được chọn |

**Lưu ý:** Khi option = ALL (ví dụ `position` option `1`), `value` có thể là mảng rỗng `[]`.

```json
{
  "criteria": [{
    "personnel": {
      "isRawValue": false,
      "displayOrder": 1,
      "value": ["$userTask.Root.submittedBy"],
      "option": 1,
      "valueForFE": [{ "valuePathName": "...", "valueDataType": "RECORD", "value": "$userTask.Root.submittedBy" }]
    }
  }]
}
```

---

##### Khi `isRawValue: false` (tham chiếu biến)
- `value`: Mảng chứa đường dẫn tham chiếu, ví dụ: `["$userTask.Root.submittedBy"]`
- `valueForFE`: Mảng object mô tả chi tiết:
```json
[
  {
    "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
    "valueDataType": "RECORD",
    "value": "$userTask.Root.submittedBy"
  }
]
```

##### Khi `isRawValue: true` (ID cụ thể)
- `value`: Mảng chứa ID, ví dụ: `["PER_SAMPLE_USER"]`
- `valueForFE`: Mảng chứa ID, ví dụ: `["PER_SAMPLE_USER"]`

#### `outputSaving` - Cách lưu kết quả
| Giá trị                    | Mô tả                                                              |
|----------------------------|--------------------------------------------------------------------|
| `"FIELD_OF_FIRST_RECORD"`  | Lưu trường của bản ghi đầu tiên (đơn giá trị)                      |
| `"FIELD_OF_LIST_RECORDS"`  | Lưu trường của tất cả bản ghi tìm được (nhiều giá trị - danh sách) |

### Resources của Organization Task

Trong `resources.actions[]`, mỗi Organization Task có 3 resource chuẩn: `startAt`, `endAt` và `output`.

`output` là resource cha chứa 3 resource con:

| Resource con | Mô tả                             | dataType | isList |
|--------------|-----------------------------------|----------|--------|
| `record`     | Bản ghi đầu tiên tìm được         | RECORD   | false  |
| `records`    | Danh sách tất cả bản ghi tìm được | RECORD   | true   |
| `total`      | Tổng số bản ghi tìm được          | NUMBER   | false  |

#### Chi tiết về 2 đầu ra chính: `record` và `records`

Mỗi Organization Task luôn có 2 đầu ra chính với format:
- `$action.{organization_slug}.output.record` — Bản ghi **đầu tiên** tìm được
- `$action.{organization_slug}.output.records` — **Tất cả** bản ghi tìm được

Đối tượng mà `record`/`records` lookup tới phụ thuộc vào `filterType` của Organization Task:

| filterType     | Mô tả                     | `record` lookup tới                    | `records` lookup tới               | `metaDataType.objectSlug` |
|----------------|---------------------------|----------------------------------------|------------------------------------|---------------------------|
| `"manager"`    | Lấy quản lý trực tiếp     | Personnel (1 nhân sự quản lý đầu tiên) | Personnel (tất cả nhân sự quản lý) | `"personnel"`             |
| `"personnel"`  | Lấy nhân sự cùng phòng    | Personnel (1 nhân sự đầu tiên)         | Personnel (tất cả nhân sự)         | `"personnel"`             |
| `"department"` | Lấy phòng ban của nhân sự | Department (1 phòng ban đầu tiên)      | Department (tất cả phòng ban)      | `"department"`            |
| `"position"`   | Lấy vị trí công việc      | Position (1 vị trí đầu tiên)           | Position (tất cả vị trí)           | `"position"`              |

**Ví dụ cụ thể:**
- Organization "Lấy quản lý" (`filterType: "manager"`, slug: `lay_quan_ly`):
  - `$action.lay_quan_ly.output.record` → 1 nhân sự quản lý đầu tiên lấy được (lookup tới Personnel)
  - `$action.lay_quan_ly.output.records` → tất cả nhân sự quản lý lấy được (lookup tới Personnel)
- Organization "Lấy nhân sự" (`filterType: "personnel"`, slug: `lay_nhan_su`):
  - `$action.lay_nhan_su.output.record` → 1 nhân sự đầu tiên lấy được (lookup tới Personnel)
  - `$action.lay_nhan_su.output.records` → tất cả nhân sự lấy được (lookup tới Personnel)
- Organization "Lấy phòng ban" (`filterType: "department"`, slug: `lay_phong_ban`):
  - `$action.lay_phong_ban.output.record` → 1 phòng ban đầu tiên lấy được (lookup tới Department)
  - `$action.lay_phong_ban.output.records` → tất cả phòng ban lấy được (lookup tới Department)
- Organization "Lấy vị trí" (`filterType: "position"`, slug: `lay_vi_tri`):
  - `$action.lay_vi_tri.output.record` → 1 vị trí đầu tiên lấy được (lookup tới Position)
  - `$action.lay_vi_tri.output.records` → tất cả vị trí lấy được (lookup tới Position)

**Lưu ý quan trọng:** Giá trị `metaDataType.objectSlug` và `metaDataType.object` (objectTypeId) trong resource `record`/`records` phải khớp với loại đối tượng trả về theo `filterType`. Ví dụ: nếu `filterType: "department"` thì `objectSlug` phải là `"department"`, không phải `"personnel"`. Các giá trị `objectSlug` và `object` **BẮT BUỘC** lấy từ skill `/object-info` (xem mục 25 trong Lưu ý quan trọng).

```json
{
  "processId": "{PROCESS_ID}",
  "name": "{ORGANIZATION_NAME}",
  "description": "",
  "resources": [
    {
      "absoluteSlug": "$action.{organization_slug}.startAt",
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
      "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / StartAt",
      "id": "{RESOURCE_ID_1}",
      "parentTable": "action",
      "slug": "startAt"
    },
    {
      "absoluteSlug": "$action.{organization_slug}.endAt",
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
        "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" },
        "timeZone": "Asia/Saigon"
      },
      "availableForOutput": true,
      "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / End At",
      "id": "{RESOURCE_ID_2}",
      "parentTable": "action",
      "slug": "endAt"
    },
    {
      "absoluteSlug": "$action.{organization_slug}.output",
      "parentMetadata": "",
      "editable": false,
      "dataType": "RECORD",
      "type": 1,
      "isList": false,
      "parentId": "{ACTION_ID}",
      "assignable": false,
      "actionType": "ORGANIZATION",
      "availableForInput": true,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "children": [
        {
          "absoluteSlug": "$action.{organization_slug}.output.record",
          "parentMetadata": "",
          "editable": false,
          "dataType": "RECORD",
          "type": 1,
          "isList": false,
          "parentId": "{OUTPUT_RESOURCE_ID}",
          "assignable": false,
          "availableForInput": true,
          "isStandard": true,
          "processId": "{PROCESS_ID}",
          "name": "Record",
          "metaDataType": {
            "linkField": "id",
            "objectSlug": "personnel",
            "object": "{PERSONNEL_OBJECT_TYPE_ID}"
          },
          "availableForOutput": true,
          "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / Output / Record",
          "parentTable": "action",
          "slug": "record"
        },
        {
          "absoluteSlug": "$action.{organization_slug}.output.records",
          "parentMetadata": "",
          "editable": false,
          "dataType": "RECORD",
          "type": 1,
          "isList": true,
          "parentId": "{OUTPUT_RESOURCE_ID}",
          "assignable": false,
          "availableForInput": true,
          "isStandard": true,
          "processId": "{PROCESS_ID}",
          "name": "Records",
          "metaDataType": {
            "linkField": "id",
            "objectSlug": "personnel",
            "object": "{PERSONNEL_OBJECT_TYPE_ID}"
          },
          "availableForOutput": true,
          "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / Output / Records",
          "parentTable": "action",
          "slug": "records"
        },
        {
          "absoluteSlug": "$action.{organization_slug}.output.total",
          "parentMetadata": "",
          "editable": false,
          "dataType": "NUMBER",
          "type": 1,
          "isList": false,
          "parentId": "{OUTPUT_RESOURCE_ID}",
          "assignable": false,
          "availableForInput": true,
          "isStandard": true,
          "processId": "{PROCESS_ID}",
          "name": "Total",
          "metaDataType": {
            "valueLimit": { "min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note" },
            "displayType": 2,
            "multipleLimit": { "min": 1, "max": 30, "warning": "warning limit note" },
            "format": { "format": 2, "type": 1 },
            "integralLength": 10,
            "roundRule": "1",
            "fractionalLength": 6
          },
          "availableForOutput": true,
          "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / Output / Total",
          "parentTable": "action",
          "slug": "total"
        }
      ],
      "name": "Output",
      "metaDataType": {
        "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" },
        "richText": "false"
      },
      "availableForOutput": true,
      "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / Output",
      "id": "{OUTPUT_RESOURCE_ID}",
      "parentTable": "action",
      "slug": "output"
    }
  ],
  "id": "{ACTION_ID}",
  "type": "ORGANIZATION",
  "nodeId": "{ORGANIZATION_NODE_ID}",
  "slug": "{organization_slug}"
}
```

### Cập nhật Resources khi sử dụng Organization Task
Khi một resource (ví dụ: `$userTask.Root.submittedBy`) được sử dụng trong `criteria` của Organization Task, cần thêm `resourcesUsedIn` vào resource đó:
```json
{
  "resourcesUsedIn": [
    {
      "actionType": "ORGANIZATION",
      "name": "{ORGANIZATION_NAME}",
      "count": 1,
      "id": "{ACTION_ID}",
      "parentTable": "action",
      "slug": "{organization_slug}"
    }
  ]
}
```

### Ví dụ 1: Lấy quản lý trực tiếp của người submitted, cấp bậc >= 1, lưu email đầu tiên

```json
{
  "data": {
    "objectFieldSavings": [
      {
        "objectFieldSlug": "account_email",
        "resource": "$flow.manageremail"
      }
    ],
    "criteria": [
      {
        "personnel": {
          "rankOrderOperation": "gte",
          "isRawValue": false,
          "displayOrder": 1,
          "levelOfDepartment": 0,
          "rankOrder": 1,
          "value": ["$userTask.Root.submittedBy"],
          "option": 1,
          "valueForFE": [
            {
              "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
              "valueDataType": "RECORD",
              "value": "$userTask.Root.submittedBy"
            }
          ]
        }
      }
    ],
    "outputSaving": "FIELD_OF_FIRST_RECORD",
    "filterType": "manager"
  },
  "processId": "{PROCESS_ID}",
  "name": "Lấy ra người quản lý và email",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "ORGANIZATION",
  "nodeId": "{ORGANIZATION_NODE_ID}",
  "slug": "lay_ra_nguoi_quan_ly_va_email"
}
```

### Ví dụ 2: Lấy quản lý của nhân sự cụ thể, cấp bậc = 1, lưu email tất cả

```json
{
  "data": {
    "objectFieldSavings": [
      {
        "objectFieldSlug": "account_email",
        "resource": "$flow.emailsofmanagers2"
      }
    ],
    "criteria": [
      {
        "personnel": {
          "rankOrderOperation": "equals",
          "isRawValue": true,
          "displayOrder": 1,
          "levelOfDepartment": 0,
          "rankOrder": 1,
          "value": ["PER_SAMPLE_USER"],
          "option": 1,
          "valueForFE": ["PER_SAMPLE_USER"]
        }
      }
    ],
    "outputSaving": "FIELD_OF_LIST_RECORDS",
    "filterType": "manager"
  },
  "processId": "{PROCESS_ID}",
  "name": "Lấy ra tất cả quản lý và emails",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "ORGANIZATION",
  "nodeId": "{ORGANIZATION_NODE_ID}",
  "slug": "lay_ra_tat_ca_quan_ly_va_emails"
}
```

### Ví dụ 3: Lấy nhân sự cùng phòng với người submitted (filterType: "personnel")

```json
{
  "data": {
    "objectFieldSavings": [
      {
        "objectFieldSlug": "",
        "resource": ""
      }
    ],
    "criteria": [
      {
        "department": {
          "isRawValue": false,
          "displayOrder": 1,
          "value": ["$userTask.Root.submittedBy"],
          "option": 3,
          "valueForFE": [
            {
              "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
              "valueDataType": "RECORD",
              "value": "$userTask.Root.submittedBy"
            }
          ]
        }
      }
    ],
    "outputSaving": "FIELD_OF_FIRST_RECORD",
    "filterType": "personnel"
  },
  "processId": "{PROCESS_ID}",
  "name": "Lay ra nhan su",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "ORGANIZATION",
  "nodeId": "{ORGANIZATION_NODE_ID}",
  "slug": "lay_ra_nhan_su"
}
```

### Ví dụ 4: Lấy phòng ban của nhân sự submitted (filterType: "department")

```json
{
  "data": {
    "objectFieldSavings": [
      {
        "objectFieldSlug": "",
        "resource": ""
      }
    ],
    "criteria": [
      {
        "departmentOfPersonnel": {
          "isRawValue": false,
          "displayOrder": 1,
          "value": ["$userTask.Root.submittedBy"],
          "option": 2,
          "valueForFE": [
            {
              "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
              "valueDataType": "RECORD",
              "value": "$userTask.Root.submittedBy"
            }
          ]
        }
      }
    ],
    "outputSaving": "FIELD_OF_FIRST_RECORD",
    "filterType": "department"
  },
  "processId": "{PROCESS_ID}",
  "name": "Lấy phòng ban",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "ORGANIZATION",
  "nodeId": "{ORGANIZATION_NODE_ID}",
  "slug": "lay_phong_ban"
}
```

### Ví dụ 5: Lấy vị trí công việc của nhân sự submitted (filterType: "position")

```json
{
  "data": {
    "objectFieldSavings": [
      {
        "objectFieldSlug": "",
        "resource": ""
      }
    ],
    "criteria": [
      {
        "personnel": {
          "isRawValue": false,
          "displayOrder": 1,
          "value": ["$userTask.Root.submittedBy"],
          "option": 1,
          "valueForFE": [
            {
              "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
              "valueDataType": "RECORD",
              "value": "$userTask.Root.submittedBy"
            }
          ]
        }
      }
    ],
    "outputSaving": "FIELD_OF_FIRST_RECORD",
    "filterType": "position"
  },
  "processId": "{PROCESS_ID}",
  "name": "Lấy ra vị trí",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "ORGANIZATION",
  "nodeId": "{ORGANIZATION_NODE_ID}",
  "slug": "lay_ra_vi_tri"
}
```

### Ví dụ 6: Nhiều criteria kết hợp AND (filterType: "personnel" - nhân sự thuộc phòng ban VÀ giữ vị trí cụ thể)

```json
{
  "data": {
    "objectFieldSavings": [
      {
        "objectFieldSlug": "",
        "resource": ""
      }
    ],
    "criteria": [
      {
        "department": {
          "isRawValue": false,
          "displayOrder": 1,
          "value": ["$userTask.Root.submittedBy"],
          "option": 3,
          "valueForFE": [
            {
              "valuePathName": "workflow_resource:list.userTask / Root / Submitted By",
              "valueDataType": "RECORD",
              "value": "$userTask.Root.submittedBy"
            }
          ]
        },
        "position": {
          "isRawValue": true,
          "displayOrder": 2,
          "value": ["POS00000000002", "POS00000000001"],
          "option": 1,
          "valueForFE": ["POS00000000002", "POS00000000001"]
        }
      }
    ],
    "outputSaving": "FIELD_OF_LIST_RECORDS",
    "filterType": "personnel"
  },
  "processId": "{PROCESS_ID}",
  "name": "Lấy nhân sự cùng phòng giữ vị trí cụ thể",
  "description": "",
  "id": "{ACTION_ID}",
  "type": "ORGANIZATION",
  "nodeId": "{ORGANIZATION_NODE_ID}",
  "slug": "lay_nhan_su_cung_phong_giu_vi_tri_cu_the"
}
```

---
