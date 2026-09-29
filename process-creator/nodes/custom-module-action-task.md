# Custom Module Action Task — Gọi action của Custom Backend Module

Đọc khi một bước của Process cần gọi logic riêng của Workspace đã viết trong Custom Backend Module: tính toán, kiểm tra điều kiện, đọc hoặc ghi dữ liệu theo quy tắc riêng rồi trả kết quả có cấu trúc cho bước sau. Node gửi input theo schema của action, chờ kết quả (tối đa `timeoutMs` của action, không quá 8 giây) rồi cung cấp output cho gateway/action tiếp theo. Viết, sửa hoặc publish action thuộc [$cogover-custom-module](../../cogover-custom-module/SKILL.md); skill này chỉ cấu hình node.

## Phạm vi và điều kiện sử dụng

- Action là một khai báo `defineAction` trong version **đang active** của một Custom Backend Module, có `exposeTo` chứa `"process"`. Node luôn gọi version active tại thời điểm chạy; deactivate module, bỏ action hoặc bỏ `"process"` khỏi `exposeTo` làm node lỗi.
- Lấy action từ danh mục của Workspace bằng phiên Web App (mọi thành viên đang hoạt động đều đọc được), không đoán `projectSlug`, `actionKey` hay tự viết schema:

  ```http
  GET https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/actions?consumer=process
  x-req-type: 9
  x-req-service: 4
  ```

  Route chi tiết `GET /api/v1/ts-projects/actions/{projectSlug}/{actionKey}?consumer=process` trả một phần tử trong `data.action` hoặc `404` `ACTION_NOT_FOUND`. Mỗi phần tử có `projectSlug`, `key`, `label`, `description`, `effect`, `exposeTo`, `timeoutMs`, `inputSchema`, `outputSchema`; contract đầy đủ ở mục [Custom Module Action](../../cogover-custom-module/references/custom-backend-module-api-reference.md#custom-module-action-1) của Backend API Reference.
- Tính năng phụ thuộc phiên bản Workspace. Route danh mục không tồn tại, Process API không nhận `CUSTOM_MODULE_ACTION` hoặc editor không có node **Custom Module Action** thì báo giới hạn phiên bản; không đổi sang loại action khác để vượt kiểm tra.
- Không thay node này bằng Send HTTP Request gọi URL của module: module production cần phiên người dùng, còn Project key và session export không phải credential cho Process.
- Action chỉ chạy ngắn và đồng bộ. Việc dài hơn do module tự chuyển sang background job; node chỉ nhận kết quả action trả về, không chờ job đó. Module khởi chạy ngược một Process thì Process đó là Normal Flow, xem [normal-flow.md](normal-flow.md#được-custom-backend-module-khởi-chạy).

## Thông tin cần xác định

Chỉ hỏi phần chưa có: action (project và key theo danh mục); nguồn của từng input (biến, field của record, output node trước, giá trị cố định); danh tính chạy; dừng hay đi tiếp khi lỗi và nhánh xử lý; output nào dùng ở bước sau. Nếu action chưa có hoặc thiếu input/output cần thiết, chuyển yêu cầu sang `$cogover-custom-module` trước khi dựng node.

Resolve Object/field bằng `$object-info`, record test bằng `$object-record`, nhân sự chạy bằng `$user-permission`.

## BPMN và action payload

| Thành phần | Giá trị |
|---|---|
| `actions[].type` | `CUSTOM_MODULE_ACTION` |
| `renderKey` | `CUSTOM_MODULE_ACTION_TASK` |
| BPMN request | `bpmn2:sendTask` với marker `elEx:customModuleActionTask` trong `extensionElements` |
| `actions[].data` | Chuỗi JSON serialize một lần từ cấu hình bên dưới |
| Resource prefix hiển thị | `workflow_custom_module_action:list.customModuleAction` |
| Đầu ra | `$action.{action_slug}.output`, kiểu `RECORD` |

Khai báo `xmlns:elEx="http://element-ex/schema"`.

```xml
<bpmn2:sendTask id="{CMA_NODE_ID}" name="Chấm điểm lead">
  <bpmn2:extensionElements>
    <elEx:customModuleActionTask />
    <configEx:elementInfo renderKey="CUSTOM_MODULE_ACTION_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</bpmn2:sendTask>
```

### Cấu hình

Đây là object **trước khi serialize** vào `actions[].data`; hai schema chép nguyên từ danh mục:

```json
{
  "projectSlug": "{PROJECT_SLUG}",
  "actionKey": "{ACTION_KEY}",
  "inputs": [
    {"key": "leadId", "value": {"type": 4, "value": "$flow.lead_id"}},
    {"key": "strict", "value": {"type": 1, "value": "true"}}
  ],
  "runAs": {"mode": "PROCESS_STARTER"},
  "continueOnFailure": false,
  "inputSchema": {
    "type": "object",
    "properties": {
      "leadId": {"type": "string", "x-cogover-object": "lead", "description": "ID of the lead to score"},
      "strict": {"type": "boolean"}
    },
    "required": ["leadId"],
    "additionalProperties": false
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "found": {"type": "boolean"},
      "score": {"type": "number"},
      "tier": {"type": "string", "enum": ["A", "B", "C"]}
    },
    "required": ["found", "score", "tier"],
    "additionalProperties": false
  }
}
```

| Field | Quy tắc |
|---|---|
| `projectSlug` | Slug của module, `^[A-Za-z_][A-Za-z0-9_]{0,99}$`, lấy từ danh mục |
| `actionKey` | `key` của action, `^[a-z][a-z0-9_]{0,63}$` |
| `inputs` | Mảng `{key, value}`: `key` là property cấp một của `inputSchema`, không trùng; `value` là ActionValue. Mọi property trong `required` phải có input khác rỗng. Property không có trong `inputs` hoặc render ra rỗng thì không được gửi |
| `runAs` | `{"mode": "PROCESS_STARTER"}` (mặc định khi thiếu), `{"mode": "PERSONNEL", "personnelId": ...}` hoặc `{"mode": "SYSTEM"}`; xem mục Danh tính chạy |
| `continueOnFailure` | Boolean, mặc định `false` |
| `inputSchema`, `outputSchema` | Snapshot JSON Schema lúc thiết kế, gốc `type: "object"`. Dùng để kiểm tra input khi lưu, dựng form và `output.result`. Lúc chạy module dùng schema của version active; snapshot cũ không làm node lỗi nhưng input thiếu theo schema mới sẽ lỗi `INPUT_INVALID` |

- Serialize `data` đúng một lần. Server lưu nguyên chuỗi đã gửi nên thứ tự property trong schema giữ nguyên; GET-back trả `data` dạng object và thứ tự property có thể khác. Khi cần thứ tự khai báo (form, `displayOrder` của `output.result`), lấy lại từ danh mục.
- Đổi action, đổi schema ở module hoặc thêm input bắt buộc: cập nhật lại `inputs`, hai schema và mọi node sau đọc `output.result.*` bằng version mới của Process.

### ActionValue và ép kiểu input

| `type` | `value` | Cách dùng |
|---|---|---|
| `1` | Chuỗi thuần | Giá trị cố định, luôn là chuỗi (`"true"`, `"5"`) rồi được ép theo schema |
| `2` | Đường dẫn Text Template đã tồn tại | Nội dung render từ template |
| `3` | Đường dẫn Formula đã tồn tại | Giá trị Formula tính ra |
| `4` | Đúng một đường dẫn resource | Biến, field, output của node trước; giữ kiểu gốc |
| `5` | Chuỗi inline chứa tham chiếu `$...` | Ghép văn bản, ví dụ `"tier $action.score.output.result.tier"` |

Giá trị sau khi render được ép theo kiểu của property trong `inputSchema`:

| Schema | Giá trị gửi |
|---|---|
| `string`, `enum`, `x-cogover-object` | Chuỗi; resource `RECORD` (bản ghi, nhân sự) được chuyển thành `id` của record |
| `number`, `integer` | Số |
| `boolean` | `true`/`false`, nhận cả chuỗi `"true"`/`"false"` |
| `string` + `format: date` | `YYYY-MM-DD` |
| `integer` + `format: x-epoch-ms` | Unix millisecond |
| `object` | Resource `RECORD` thành object JSON; chuỗi JSON được parse |
| `array` | Resource dạng danh sách hoặc chuỗi JSON mảng |

Giá trị không ép được vẫn được gửi để module báo `INPUT_INVALID`, không bị âm thầm sửa. Số quá lớn (hơn 100 chữ số hoặc số mũ vượt 400) không được gửi. Không đưa secret vào input của node.

### Danh tính chạy

| `runAs.mode` | Action chạy dưới | Ràng buộc |
|---|---|---|
| `PROCESS_STARTER` | Người khởi tạo lượt chạy | Không dùng được với `scheduled_flow` và `triggered_flow` (record, webhook): lưu báo mã `75` |
| `PERSONNEL` | Nhân sự chỉ định: ID cố định (chuỗi hoặc ActionValue `type: 1`) hoặc ActionValue `type: 4` trỏ resource `TEXT` hay `RECORD` của Object `personnel` | Nhân sự phải thuộc Workspace, đang hoạt động và có tài khoản; resource danh sách lấy phần tử đầu. Trong Triggered webhook, không lấy từ `$flow.input`, `$flow.webhook` hay giá trị suy ra từ chúng (mã `76`): bên gọi webhook không được chọn người mà action chạy dưới quyền |
| `SYSTEM` | Không có người dùng | Module phải có identity policy đã duyệt cho version active với `allowInternalSystem: true`; nếu không node nhận `SYSTEM_IDENTITY_NOT_ALLOWED` |

- Action dùng quyền của đúng danh tính đó; node không cấp thêm quyền. Handler của module thấy mode đã dùng, nên chọn theo contract của module thay vì chọn `SYSTEM` để né lỗi quyền.
- Không xác định được người chạy (không có người khởi tạo, `personnelId` rỗng, nhân sự không có tài khoản): node `FAILED` với `RUN_AS_REQUIRED` và không gọi module.
- Triggered record: nhân sự lấy từ field của record do người sửa record kiểm soát; chỉ dùng khi module đã chấp nhận điều đó.

## Resources và đầu ra

Trong `resources.actions`, tạo nhóm cùng `id`, `nodeId`, `type: CUSTOM_MODULE_ACTION`, `name`, `slug` với action, chứa `startAt`, `endAt` kiểu `DATE_TIME` và `output` kiểu `RECORD`: mỗi resource có ID riêng, `parentId` là action ID, `parentTable: action`, `type: 1`, `isList: false`, `isStandard: true`, `availableForOutput: true`; `output` có `availableForInput: false`. Prefix `absoluteSlug` là `$action.{slug}`, prefix `absolutePath` là `workflow_custom_module_action:list.customModuleAction / {Tên node}`. Server tự dựng children của `output` (kể cả `result` theo `outputSchema`) mỗi lần lưu và khi đọc; không gửi `resultDataType`, không tạo Variable thay cho output. Server cũng tự ghi nhận tham chiếu resource của `inputs[].value` và `runAs.personnelId`.

| Đường dẫn sau `$action.{slug}.` | Kiểu | Ý nghĩa |
|---|---|---|
| `startAt`, `endAt` | DATE_TIME | Thời điểm bắt đầu/kết thúc node |
| `output.status` | TEXT | `RUNNING` khi đang chờ; khi xong `COMPLETED` hoặc `FAILED` |
| `output.result` | RECORD | Output của action, mỗi property của `outputSchema` là một child; `null` khi `FAILED` |
| `output.errorCode`, `output.errorMessage` | TEXT | Mã lỗi và thông báo tiếng Anh cố định theo mã |
| `output.runId` | TEXT | Mã lượt gọi `{instanceId}:{nodeId}:{lần}`, tăng khi node chạy lại (loop, rollback) |
| `output.durationMs` | NUMBER | Thời gian chạy action |

Kiểu child của `output.result` theo `outputSchema`:

| JSON Schema | Kiểu Process |
|---|---|
| `string`, `enum`, `x-cogover-object` | TEXT |
| `number`, `integer` | NUMBER |
| `boolean` | BOOLEAN |
| `string` + `format: date` | DATE |
| `integer` + `format: x-epoch-ms` | DATE_TIME |
| `object` | RECORD, child lồng |
| `array` | Kiểu của `items`, `isList: true`; mảng lồng mảng thành danh sách TEXT |

Đọc child bằng `$action.{slug}.output.result.tier`, phần tử danh sách `$action.{slug}.output.result.items[0].sku`. Tham chiếu tới field không còn trong `outputSchema` báo `RESOURCE_NOT_FOUND` (mã `28`) khi lưu.

## Validate khi lưu

Lưu Process luôn trả kết quả; lỗi của node được ghi vào `meta.errors[]` (mỗi lỗi có `code`, `slug`, `nodeId`, `fieldKey`, `detail` tiếng Anh) và Process `isValid: false`, không kích hoạt được.

| `code` | `slug` | Khi nào |
|---:|---|---|
| 70 | `CUSTOM_MODULE_ACTION_CONFIG_INVALID` | `data` không phải JSON object hoặc sai kiểu; `projectSlug`/`actionKey` rỗng hoặc sai định dạng; thiếu schema hoặc schema không phải `type: object`; `inputs[]` thiếu/trùng `key` hoặc ActionValue sai; ActionValue `type: 2`/`3` không trỏ Text Template/Formula; `continueOnFailure` không phải boolean |
| 71 | `CUSTOM_MODULE_ACTION_NOT_FOUND` | Không có module, version active hoặc action |
| 72 | `CUSTOM_MODULE_ACTION_NOT_EXPOSED` | Action có nhưng không mở cho Process |
| 73 | `CUSTOM_MODULE_ACTION_INPUT_INVALID` | `inputs[].key` không thuộc `properties` của schema input |
| 74 | `CUSTOM_MODULE_ACTION_REQUIRED_INPUT_MISSING` | Property `required` không có input khác rỗng |
| 75 | `CUSTOM_MODULE_ACTION_RUN_AS_REQUIRED` | `scheduled_flow` hoặc `triggered_flow` chọn `PROCESS_STARTER` |
| 76 | `CUSTOM_MODULE_ACTION_RUN_AS_INVALID` | `mode` không hợp lệ; `PERSONNEL` thiếu `personnelId`, ID không thuộc Workspace, resource không tồn tại hoặc không phải `TEXT`/`RECORD` `personnel`, ActionValue khác `type` 1/4; Triggered webhook lấy nhân sự từ dữ liệu webhook |
| 28 | `RESOURCE_NOT_FOUND` | ActionValue tham chiếu resource không còn |

- Input được kiểm theo schema hiện tại của module khi đọc được, không thì theo snapshot. Module tạm thời không trả lời thì Process vẫn được lưu mà không kiểm 71/72; kiểm tra lại bằng GET-back hoặc lúc xuất bản.
- Xuất bản kiểm tra lại: action đã bị gỡ hoặc không còn mở cho Process thì xuất bản bị từ chối (HTTP `400`, mã `71`/`72`) và không version nào đổi trạng thái; module không trả lời thì vẫn xuất bản và node sẽ báo lỗi lúc chạy.
- Kiểu giá trị input so với schema và biến trong ActionValue `type: 5` không được kiểm khi lưu: kiểm thử bằng lượt chạy.

## Chạy và lỗi

- Node gửi input rồi chờ kết quả mà không chặn lượt chạy khác. Lỗi tạm thời hoặc không nhận được trả lời trong khoảng 60 giây: node tự gửi lại cùng `runId` (module trả kết quả đã lưu, không chạy action hai lần); hết lượt thử thì `FAILED` với `RUNTIME_UNAVAILABLE`.
- `continueOnFailure: false`: `FAILED` dừng lượt chạy với lỗi tại node, bước sau không chạy. `continueOnFailure: true`: ghi output rồi đi tiếp; đặt Exclusive Gateway kiểm tra `$action.{slug}.output.status` bằng `COMPLETED` trước nhánh nghiệp vụ, nhánh mặc định xử lý lỗi hoặc giao nhân sự xem lại.
- Output chỉ có `errorCode` và thông báo cố định: lỗi mà handler ném luôn là `SCRIPT_ERROR`, không mang message riêng. Kết quả dự kiến (không tìm thấy, không đủ điều kiện) phải nằm trong `output.result` (ví dụ `found`, `reason`) để gateway rẽ nhánh; thiếu thì yêu cầu bổ sung ở module qua `$cogover-custom-module`.
- Action có `effect: "write"` đã ghi dữ liệu trước khi lỗi xảy ra không được hoàn tác. Kiểm tra dữ liệu thực tế trước khi chạy lại lượt chạy.
- Mỗi lần gọi và mỗi lần module ghi record dùng một phần ngân sách tự động hoá của lượt chạy; chuỗi Process → action → Process/trigger lặp lại sẽ dừng với `MAX_HOP_EXCEEDED`. Không dựa vào giới hạn này thay cho điều kiện dừng của thiết kế.

| `output.errorCode` | Ý nghĩa, xử lý |
|---|---|
| `CONFIG_INVALID` | Cấu hình node sai; sửa `data` |
| `RUN_AS_REQUIRED` | Không xác định được người chạy; chọn `PERSONNEL` hợp lệ hoặc `SYSTEM` theo contract |
| `VALUE_RESOLVE_FAILED` | Không render được input (resource không tồn tại hoặc rỗng) |
| `RUNTIME_UNAVAILABLE`, `WAIT_PERSIST_FAILED` | Module hoặc Process tạm thời không sẵn sàng; chạy lại sau, không đổi cấu hình |
| `MAX_HOP_EXCEEDED` | Chuỗi tự động hoá gọi lẫn nhau đã hết ngân sách |
| `ACTION_NOT_FOUND`, `PROJECT_NOT_FOUND`, `ACTION_NOT_EXPOSED` | Module bị deactivate, action bị gỡ, đổi key hoặc không còn mở cho Process |
| `ACTOR_NOT_ALLOWED` | Người chạy không còn là thành viên đang hoạt động |
| `SYSTEM_IDENTITY_NOT_ALLOWED` | `SYSTEM` khi policy đã duyệt của module không bật `allowInternalSystem` |
| `IDEMPOTENCY_CONFLICT` | Mã lượt gọi đã dùng với input hoặc danh tính khác |
| `INPUT_INVALID` | Input không khớp schema của version active; module trả danh sách lỗi theo đường dẫn |
| `OUTPUT_INVALID` | Action trả kết quả không khớp `outputSchema`; lỗi của module |
| `SCRIPT_ERROR` | Handler ném lỗi hoặc dùng hết giới hạn tài nguyên |
| `TIMEOUT` | Action vượt `timeoutMs` |
| `RATE_LIMITED` | Action vượt ngân sách của một lần thực thi |
| `PERMISSION_DENIED` | Action bị từ chối một thao tác (ví dụ ghi trong action `effect: "read"`, thiếu quyền của danh tính chạy) |
| `INTERNAL_ERROR` | Lỗi khác; giữ nguyên mã khi báo cáo |

## Xác minh trước và sau khi lưu

1. Đọc action từ danh mục, đối chiếu `effect` (ghi hay chỉ đọc) và `timeoutMs` với yêu cầu. Kiểm tra mọi property `required` có input, resource nguồn tồn tại trước node, danh tính chạy hợp lệ với loại Process; serialize `data` một lần.
2. Kiểm tra XML/ID/diagram theo `SKILL.md`; dùng `samples/sample_custom_module_action.json` làm cấu trúc khởi đầu. Sample chỉ minh họa: thay `projectSlug`, `actionKey`, input và hai schema bằng dữ liệu của danh mục, sinh lại ID khi tạo mới.
3. Tạo qua Public Process API theo `api-process-builder.md`, GET-back và đối chiếu `CUSTOM_MODULE_ACTION`, `CUSTOM_MODULE_ACTION_TASK`, `projectSlug`, `actionKey`, `inputs`, `runAs`, `continueOnFailure`, ba resource chuẩn và `output.result.children` sinh từ `outputSchema`; không có `meta.errors` mã 70–76 hoặc 28.
4. Kích hoạt, xuất bản và chạy theo `SKILL.md` cùng `runtime-validation.md`. Không tuyên bố PASS từ `r: 0`, `isValid: true` hay việc lưu thành công.

## Kịch bản kiểm thử nghiệp vụ

| Trường hợp | Bằng chứng cần có |
|---|---|
| Thành công | Đúng instance có `output.status = COMPLETED`, `output.result.*` đúng giá trị mong đợi và bước sau (gateway, assignment, action khác) dùng được; action ghi dữ liệu thì đọc lại record bằng `$object-record` |
| Kết quả dự kiến khác | Input dẫn tới nhánh như không tìm thấy/không đủ điều kiện; `result` báo đúng và gateway chọn đúng nhánh |
| Input sai | Thiếu hoặc sai kiểu (ví dụ raw `"abc"` cho số): `FAILED` `INPUT_INVALID`, action không tạo hiệu ứng |
| Lỗi, `continueOnFailure: true` | Lỗi được ghi vào output, nhánh lỗi chạy, nhánh thành công không chạy |
| Lỗi, `continueOnFailure: false` | Lượt chạy dừng tại node, node sau không chạy |
| Danh tính | Mỗi mode dùng thật cho kết quả đúng người (module trả hoặc ghi lại danh tính); `SYSTEM` bị từ chối khi module chưa bật `allowInternalSystem` nếu đó là ca cần chứng minh |
| Action chỉ đọc | Action `effect: "read"` không tạo thay đổi dữ liệu nào |
| Module thay đổi | Sau khi module đổi schema hoặc gỡ action, lượt chạy mới báo đúng mã và node được cập nhật bằng version mới của Process |

Chỉ kiểm thử trường hợp cần cho yêu cầu và nằm trong phạm vi đã được phép. Báo process/instance, `runId`, trạng thái, output và hiệu ứng đã đối chiếu; dùng `PARTIAL` hoặc `BLOCKED_ENV` khi chưa quan sát đầy đủ.
