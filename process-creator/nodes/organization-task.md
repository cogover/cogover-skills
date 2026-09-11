## Organization Task (Task Tổ Chức)

Task hệ thống truy vấn cấu trúc tổ chức khi luồng chạy đến; kết quả có thể lưu trường dữ liệu vào Variable. `filterType`:

| `filterType` | Truy vấn |
|---|---|
| `"manager"` | Lấy quản lý trực tiếp, lọc theo cấp bậc |
| `"personnel"` | Lấy nhân sự (theo phòng ban/vị trí của một nhân sự) |
| `"department"` | Lấy phòng ban của một nhân sự |
| `"position"` | Lấy vị trí công việc của một nhân sự |

`metaDataType.object`/`objectSlug` của output lấy theo bullet "Thông tin Object thật" ở [mục Chuẩn bị của SKILL.md](../SKILL.md#chuẩn-bị). Mẫu: `samples/sample_process_organization.json` (quản lý trực tiếp). Tiêu chí PASS runtime: [runtime-validation.md](runtime-validation.md#tiêu-chí-observable-theo-node) (GET-back có thể thêm `field: "personnel"` vào criteria: canonicalization, không PUT để xoá).

### BPMN XML

```xml
<elEx:organizationTask id="{ORGANIZATION_NODE_ID}" name="{ORGANIZATION_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="ORGANIZATION_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:organizationTask>
```

Element `elEx:organizationTask`; khai báo `xmlns:elEx="http://element-ex/schema"` trong `bpmn2:definitions` ([namespace](../references/bpmn-xml-and-diagram.md#namespace-và-kết-nối-logic)).

### Action trong mảng `actions` (root level)

```json
{
  "data": {
    "objectFieldSavings": [
      { "objectFieldSlug": "{FIELD_SLUG}", "resource": "{VARIABLE_ABSOLUTE_SLUG}" }
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

#### `objectFieldSavings` — lưu trường vào biến

| Trường | Bắt buộc | Mô tả |
|---|---|---|
| `objectFieldSlug` | Có | Slug trường trên đối tượng cần lấy (ví dụ `"account_email"`) |
| `resource` | Có | Đường dẫn biến đích (ví dụ `"$flow.manageremail"`) |

`resourceDataType` và `resourcePathName` do backend tự tính khi trả response, KHÔNG gửi lên. Không lưu trường: payload front-end gửi một phần tử rỗng `{"objectFieldSlug": "", "resource": ""}`.

#### `criteria` — điều kiện lọc

Mảng 2 chiều: **giữa các group** (phần tử mảng ngoài) là OR, **trong mỗi group** (các key của object) là AND. Trong object criteria KHÔNG có trường `field`; tên trường lọc chính là key (`"personnel"`, `"department"`, `"departmentOfPersonnel"`, `"position"`).

```json
{
  "criteria": [
    {
      "personnel": { "option": 2, "value": ["..."], "...": "..." },
      "department": { "option": 1, "value": ["..."], "...": "..." }
    },
    { "personnel": { "option": 3, "value": ["..."], "...": "..." } }
  ]
}
```

= (personnel INCLUDING **VÀ** department PERSONNEL_OF_DEPARTMENT) **HOẶC** (personnel EXCLUDING).

Trường chung của mỗi criteria item:

| Trường | Mô tả |
|---|---|
| `isRawValue` | `false`: `value` là tham chiếu biến; `true`: `value` là ID cụ thể |
| `displayOrder` | Thứ tự hiển thị, bắt đầu từ `1` |
| `value` | Mảng: đường dẫn biến (chuỗi) hoặc ID; option ALL có thể là `[]` |
| `option` | Loại lọc theo bảng dưới |
| `valueForFE` | Hiển thị cho front-end: `isRawValue: false` → `[{"valuePathName": "workflow_resource:list.userTask / Root / Submitted By", "valueDataType": "RECORD", "value": "$userTask.Root.submittedBy"}]`; `isRawValue: true` → mảng ID giống `value`, ví dụ `["PER_SAMPLE_USER"]` |

Chỉ `filterType: "manager"` (cả key `personnel` và `department`) có thêm `rankOrderOperation` (`"gte"` lớn hơn hoặc bằng, `"equals"`, `"lte"`), `rankOrder` (cấp bậc so sánh, ví dụ `1`), `levelOfDepartment` (thường `0`).

| `filterType` | Criteria key | `option` | Ý nghĩa |
|---|---|---|---|
| `manager` | `personnel` | `1` | INCLUDING_PERSONNEL — quản lý của các nhân sự được chọn |
| `manager` | `department` | `1` | INCLUDING_DEPARTMENT — quản lý trong phòng ban được chọn |
| `personnel` | `personnel` | `1` / `2` / `3` | ALL_PERSONNEL / INCLUDING_PERSONNEL (chỉ nhân sự được chọn) / EXCLUDING_PERSONNEL (tất cả trừ nhân sự được chọn) |
| `personnel` | `department` | `1` | PERSONNEL_OF_DEPARTMENT — nhân sự thuộc phòng ban |
| `personnel` | `department` | `2` | BELONG_TO_DEPARTMENT_AND_ALL_CHILDREN — thuộc phòng ban và mọi phòng ban con |
| `personnel` | `department` | `3` | SAME_DEPARTMENT_AS_PERSONNEL — cùng phòng ban với nhân sự được chọn |
| `personnel` | `department` | `4` | BELONG_TO_DEPARTMENT_OR_PARENT_DEPARTMENT_OF_PERSONNEL — thuộc phòng ban hoặc phòng ban cha của nhân sự được chọn |
| `personnel` | `position` | `1` / `2` | PERSONNEL_HOLDING_ONE_OF_POSITIONS (giữ một trong các vị trí) / ANY_POSITION_EXCEPT (bất kỳ vị trí nào ngoại trừ) |
| `department` | `department` | `1` / `2` / `3` | ALL_DEPARTMENT / INCLUDING_DEPARTMENT / EXCLUDING_DEPARTMENT |
| `department` | `departmentOfPersonnel` | `1` / `2` / `3` | ALL_PERSONNEL (phòng ban của mọi nhân sự) / INCLUDING_PERSONNEL (của nhân sự được chọn) / EXCLUDING_PERSONNEL |
| `department` | `position` | `1` / `2` | ALL_POSITION / INCLUDING_POSITION |
| `position` | `position` | `1` / `2` / `3` | ALL_POSITION / INCLUDING_POSITION / EXCLUDING_POSITION |
| `position` | `department` | `1` / `2` / `3` | ALL_DEPARTMENT / INCLUDING_DEPARTMENT / EXCLUDING_DEPARTMENT |
| `position` | `personnel` | `1` | ONLY_POSITIONS_APPLY_TO_PERSONNEL — chỉ vị trí áp dụng cho nhân sự được chọn |

#### `outputSaving`

`"FIELD_OF_FIRST_RECORD"` lưu trường của bản ghi đầu tiên (đơn giá trị); `"FIELD_OF_LIST_RECORDS"` lưu trường của tất cả bản ghi tìm được (danh sách).

### Ví dụ: quản lý trực tiếp của người submit, cấp bậc >= 1, lưu email đầu tiên

```json
{
  "data": {
    "objectFieldSavings": [
      { "objectFieldSlug": "account_email", "resource": "$flow.manageremail" }
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

Biến thể: nhân sự cụ thể `"isRawValue": true, "value": ["PER_SAMPLE_USER"], "valueForFE": ["PER_SAMPLE_USER"]`, `"rankOrderOperation": "equals"`, `"outputSaving": "FIELD_OF_LIST_RECORDS"`; nhiều vị trí `"value": ["POS00000000002", "POS00000000001"]`; các `filterType` khác chỉ đổi key/option theo bảng và bỏ ba trường cấp bậc.

### Resources của action (`resources.actions[]`)

Ba resource chuẩn `startAt`, `endAt`, `output`; `output` có 3 resource con:

| Resource con | Mô tả | dataType | isList |
|---|---|---|---|
| `record` | Bản ghi đầu tiên tìm được: `$action.{organization_slug}.output.record` | RECORD | false |
| `records` | Tất cả bản ghi tìm được: `$action.{organization_slug}.output.records` | RECORD | true |
| `total` | Tổng số bản ghi | NUMBER | false |

Đối tượng mà `record`/`records` lookup tới theo `filterType`: `manager` và `personnel` → Personnel (`metaDataType.objectSlug: "personnel"`); `department` → Department (`"department"`); `position` → Position (`"position"`). `metaDataType.objectSlug` và `metaDataType.object` (objectTypeId) của `record`/`records` phải khớp loại đối tượng trả về (ví dụ `filterType: "department"` thì `objectSlug` là `"department"`, không phải `"personnel"`) và lấy từ `$object-info`.

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
      "metaDataType": { "defaultValueCurrent": false, "format": { "date": "dd/MM/yyyy", "time": "hh:mm:ss" }, "timeZone": "Asia/Saigon" },
      "availableForOutput": true,
      "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / StartAt",
      "id": "{RESOURCE_ID_1}",
      "parentTable": "action",
      "slug": "startAt"
    },
    {
      "absoluteSlug": "$action.{organization_slug}.endAt",
      "name": "End At",
      "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / End At",
      "id": "{RESOURCE_ID_2}",
      "slug": "endAt",
      "...": "các key còn lại giống startAt"
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
          "metaDataType": { "linkField": "id", "objectSlug": "personnel", "object": "{PERSONNEL_OBJECT_TYPE_ID}" },
          "availableForOutput": true,
          "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / Output / Record",
          "parentTable": "action",
          "slug": "record"
        },
        {
          "absoluteSlug": "$action.{organization_slug}.output.records",
          "dataType": "RECORD",
          "isList": true,
          "name": "Records",
          "metaDataType": { "linkField": "id", "objectSlug": "personnel", "object": "{PERSONNEL_OBJECT_TYPE_ID}" },
          "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / Output / Records",
          "slug": "records",
          "...": "các key còn lại giống record"
        },
        {
          "absoluteSlug": "$action.{organization_slug}.output.total",
          "dataType": "NUMBER",
          "isList": false,
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
          "absolutePath": "workflow_resource:list.organization / {ORGANIZATION_NAME} / Output / Total",
          "slug": "total",
          "...": "các key còn lại giống record"
        }
      ],
      "name": "Output",
      "metaDataType": { "characterLimit": { "min": 0, "max": 131072, "warning": "warning limit note" }, "richText": "false" },
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

### `resourcesUsedIn`

Resource được dùng trong `criteria` (ví dụ `$userTask.Root.submittedBy`) thêm entry:

```json
{
  "resourcesUsedIn": [
    { "actionType": "ORGANIZATION", "name": "{ORGANIZATION_NAME}", "count": 1, "id": "{ACTION_ID}", "parentTable": "action", "slug": "{organization_slug}" }
  ]
}
```
