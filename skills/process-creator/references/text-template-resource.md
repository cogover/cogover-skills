# Text Template (Mẫu văn bản)

Text Template là custom resource (`type: 4`) tạo nội dung văn bản/HTML có biến động bằng Apache Velocity Template Language (VTL): biến, điều kiện, vòng lặp. Thường dùng làm body/tiêu đề email thay vì viết HTML trực tiếp trong action. Cú pháp đầy đủ: [text-template-api-reference-vi.md](../text-template-api-reference-vi.md). Mẫu: `samples/sample_process_text_template.json` (Send Email với Text Template dùng biến VTL).

## Cú pháp VTL tóm tắt

```
$userTask.Root.chon_lead.last_first_name      ## biến, kể cả trường con của lookup
$flow.instance.name

#if($userTask.Root.chon_lead.company)
  Công ty: $userTask.Root.chon_lead.company
#elseif($userTask.Root.chon_lead.last_first_name)
  Cá nhân: $userTask.Root.chon_lead.last_first_name
#else
  Không có thông tin
#end

#foreach($item in $userTask.Root.danh_sach)
  - $item.name
#end

#set($greeting = "Xin chào")
$greeting $userTask.Root.chon_lead.last_first_name
```

## Cấu trúc trong `resources.custom`

```json
{
  "absoluteSlug": "$flow.{text_template_slug}",
  "parentMetadata": "",
  "defaultValue": "<div>Nội dung HTML với biến VTL, ví dụ: $userTask.Root.chon_lead.last_first_name</div>",
  "editable": true,
  "dataType": "TEXT",
  "description": "",
  "type": 4,
  "isList": false,
  "parentId": "{PROCESS_ID}",
  "assignable": false,
  "availableForInput": false,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "{TEXT_TEMPLATE_NAME}",
  "metaDataType": {
    "convertNullNumberToZero": true,
    "richText": 1,
    "convertNullStringToEmpty": true
  },
  "availableForOutput": false,
  "absolutePath": "workflow_resource:list.textTemplate / {TEXT_TEMPLATE_NAME}",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "resourcesUsedIn": [],
  "slug": "{text_template_slug}"
}
```

| Trường | Giá trị | Mô tả |
|---|---|---|
| `type` | `4` | Text Template |
| `dataType` | `"TEXT"` | Luôn TEXT |
| `absoluteSlug` | `$flow.{slug}` | Đường dẫn tham chiếu |
| `absolutePath` | `workflow_resource:list.textTemplate / {Name}` | Tên hiển thị |
| `defaultValue` | HTML/VTL | Nội dung mẫu |
| `metaDataType.richText` | `1` | Hỗ trợ HTML/rich text |
| `metaDataType.convertNullNumberToZero` | `true` | Số null → 0 |
| `metaDataType.convertNullStringToEmpty` | `true` | Chuỗi null → rỗng |
| `assignable` | `false` | Không ghi bằng Assignment |
| `parentTable` | `"process"` | |
| `isStandard` | `false` | |
| `id` | prefix `RS` + suffix chữ-số duy nhất | ví dụ `RS00000000041` |

## Dùng trong action

Send Email: `content` dùng `type: 2` với `value: "$flow.{text_template_slug}"` ([nodes/send-email-task.md](../nodes/send-email-task.md)); HTTP request body cũng nhận `type: 2` ([nodes/send-http-request-task.md](../nodes/send-http-request-task.md)).

## `resourcesUsedIn` và `externalResourcesUsedIn`

Text Template được dùng trong action (ví dụ Send Email): thêm vào `resourcesUsedIn` của Text Template:

```json
{
  "resourcesUsedIn": [
    { "actionType": "SEND_EMAIL", "name": "Gửi email cho Lead đã chọn ở Root", "count": 1, "id": "{ACTION_ID}", "parentTable": "action", "slug": "{action_slug}" }
  ]
}
```

Trường của userTask được dùng trong nội dung Text Template (ví dụ `$userTask.Root.chon_lead`): `resourcesUsedIn` của resource trường đó có 2 entry, một cho action dùng Text Template và một cho chính Text Template:

```json
{
  "resourcesUsedIn": [
    { "actionType": "SEND_EMAIL", "name": "Gửi email cho Lead đã chọn ở Root", "count": 2, "id": "{ACTION_ID}", "parentTable": "action", "slug": "{action_slug}" },
    { "dataType": "TEXT", "name": "Body email", "count": 2, "id": "{TEXT_TEMPLATE_RESOURCE_ID}", "parentTable": "resource", "slug": "{text_template_slug}" }
  ]
}
```

Trường con của lookup dùng trong Text Template (ví dụ `$userTask.Root.chon_lead.last_first_name`, `$userTask.Root.chon_lead.company`): thêm mỗi trường vào `externalResourcesUsedIn` ở root level. `parentId` = ID resource lookup (`chon_lead`); `parentTable: "screen_component"` (trường con của component trong screen; Formula dùng `"resource"`); `absolutePath` theo `workflow_resource:list.userTask / {TaskName} / {LookupFieldName} / {SubFieldName}`.

```json
{
  "externalResourcesUsedIn": [
    {
      "absoluteSlug": "$userTask.Root.chon_lead.last_first_name",
      "parentMetadata": "",
      "dataType": "TEXT",
      "type": 1,
      "isList": false,
      "parentId": "{LOOKUP_RESOURCE_ID}",
      "isSystem": false,
      "availableForInput": false,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "name": "Last first name",
      "availableForOutput": false,
      "absolutePath": "workflow_resource:list.userTask / Root / Chọn Lead / Last first name",
      "parentTable": "screen_component",
      "slug": "last_first_name"
    },
    {
      "absoluteSlug": "$userTask.Root.chon_lead.company",
      "parentMetadata": "",
      "dataType": "TEXT",
      "type": 1,
      "isList": false,
      "parentId": "{LOOKUP_RESOURCE_ID}",
      "isSystem": false,
      "availableForInput": false,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "name": "Company",
      "availableForOutput": false,
      "absolutePath": "workflow_resource:list.userTask / Root / Chọn Lead / Company",
      "parentTable": "screen_component",
      "slug": "company"
    }
  ]
}
```

## Hiển thị giá trị field cho người đọc

Áp dụng cho tiêu đề và nội dung Send Email, Send Notification, Push Message, `display_text` của User Task và Text Template. Quy tắc: chỉ in field có nội dung đã sẵn sàng hiển thị. Simple Renderer (`type: 5`) in nguyên giá trị lưu trữ và không thực thi hàm: `$number.format(...)` trong chuỗi type 5 không có tác dụng.

| Dữ liệu | In trực tiếp sẽ thấy | Cách làm |
|---|---|---|
| Lookup nhân sự (`submittedBy`, `owner`, `created_by`, lookup tuỳ chỉnh tới `personnel`) | `.name` là mã tự sinh | Không dùng `.name`; in trường họ tên theo dòng `personnel` ở [object-info](../../object-info/SKILL.md#object-đặc-biệt-của-workspace-cần-nắm), ví dụ `$userTask.Root.submittedBy.first_last_name` |
| Số, tiền (`decimal`, `currency`, `rollup_summary`, formula số) | `1000000` hoặc `1.0E8` | Field formula text trên Object trả chuỗi đã định dạng kèm đơn vị, template trỏ tới field đó và không in thêm đơn vị (*đã sửa và chạy đúng*). Formula resource `TEXT` hoặc `$number.format` trong Text Template (`type: 2`): *chưa kiểm chứng*; chạy thử và đọc nội dung đã render trước khi dùng |
| `single_choice`, `multi_choices` | JSON `{"multiChoice":false,"options":[...]}` | Field formula text trả nhãn option đã chọn |
| Field có thể trống | Chữ `null` | Giá trị mặc định ở field/formula, hoặc `#if` trong Text Template |
| Ngày có thể trống đi qua formula | `01/01/1970` | Formula kiểm tra trống trước khi định dạng |
| `name` đã có tiền tố (`REQ-0001`) | `REQ REQ-0001` khi ghép thêm tiền tố | In nguyên `name` |

- Cách viết field formula hiển thị (định dạng tiền, nhãn lựa chọn, ngày trống, đơn vị ở một nơi, chuỗi trông giống số): [bẫy Formula của object-info](../../object-info/references/formula-validation.md#bẫy-thường-gặp-khi-viết-formula).
- Link tới bản ghi: dùng route runtime trong App theo [app-menu-manager](../../app-menu-manager/references/app-menu-model.md#route-runtime-trong-app). Đổi App chứa Object thì quét link trong mọi process liên quan, liệt kê process và version sẽ thay, hỏi người dùng xác nhận theo Quy tắc an toàn rồi sửa bằng version mới; mở thử một link đã render.
- Sau khi tạo hoặc sửa process, quét mọi chuỗi nội dung (action `data`, `defaultValue` của `display_text` và Text Template): không còn `.name` của nhân sự, số/tiền thô, field lựa chọn hay field có thể trống in trực tiếp. Khi kiểm thử, đọc nội dung đã render (hộp thư, thông báo hoặc `Process_Debug_data` của node) và đối chiếu từng giá trị.

## Ví dụ nội dung

```html
<div>Chào anh/chị $userTask.Root.chon_lead.last_first_name,</div>
<div>&nbsp;</div>
<div>Qua tìm hiểu, em thấy $userTask.Root.chon_lead.company đang mở rộng đội sales.</div>
<ul>
	<li>Quy trình phân tán, nhiều file Excel / phần mềm rời rạc.</li>
	<li>CRM hoặc ERP khó tùy chỉnh theo thực tế vận hành.</li>
</ul>
<div>Trân trọng,</div>
```
