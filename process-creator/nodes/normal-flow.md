# Normal Flow (`normal_flow`)

Đọc file này khi cần tạo quy trình không có form Root bắt buộc, thường để process cha hoặc module khác gọi. Mẫu: `samples/sample_normal_flow.json`.

## Cách dùng

- Process cha gọi qua node Sub Process: tách các bước xử lý thành quy trình con để process cha gọi và truyền dữ liệu vào; cấu hình quy trình con và mapping input/output theo [sub-process-task.md](sub-process-task.md).
- Module khác gọi: ví dụ module SLA phát hiện một vi phạm rồi gọi Normal Flow để tạo cảnh báo, gửi email hoặc thông báo cho quản lý (module SLA phát hiện, Normal Flow xử lý khi được gọi).
- Chạy độc lập vẫn được hỗ trợ cho người có quyền `START_INSTANCE`, nhưng hiếm dùng. Khi thiết kế, xác định bên gọi dự kiến (process cha, module hay người dùng) và dữ liệu cần nhận/trả; yêu cầu đã nêu process cha hoặc module gọi thì lấy cách gọi đó làm ngữ cảnh chính thay vì mặc định cần người dùng bấm **Tạo lượt chạy**.

Start dùng `renderKey="START_NORMAL_EVENT"`, `metadata: {}`. Không tạo Root User Task tự động (chỉ `manual_flow` bắt buộc Start → Root); Start có thể nối thẳng tới action, gateway hoặc End Process.

## User Task trong Normal Flow

Normal Flow vẫn có thể chứa User Task sau Start/action. Không copy nguyên User Task Root của sample Manual Flow: overview của Manual Flow có thể tham chiếu `$flow.instance.starter` và làm Normal Flow bị từ chối.

Mỗi User Task Normal Flow phải giữ đủ contract canonical của User Task, đặc biệt:

- `approvalScreen: 0` (integer, không được bỏ).
- `participantPermission`, `taskPerformer` dạng mảng lồng và `pageSettings` đầy đủ.
- `content`/layout và nhóm nút submit hợp lệ.
- Ba resource chuẩn `submittedBy`, `startAt`, `endAt` trong `resources.userTasks[]`, cùng resources của các field.
- `overviewScreen: {"layout":[],"permissionGeneralInfo":[]}` nếu không có overview riêng; không tham chiếu starter của Manual Flow.

Với User Task đầu tiên trong Normal Flow, request có thể gửi `isRoot: false` nhưng server canonicalize GET-back thành `isRoot: true`. Nếu topology, overview, form và runtime đúng thì đây là canonicalization, không PUT chỉ để đổi lại cờ; `isRoot` ở đây không biến Normal Flow thành Manual Flow.

Không tự suy ra rằng create lỗi `Integer.intValue()` là lỗi node: trước hết kiểm tra `approvalScreen` và các integer bắt buộc trong `pageSettings`/screen config.

## Quyền mặc định

Cho phép cấu hình các run permissions sau:

```json
[
  "START_INSTANCE",
  "CANCEL_INSTANCE",
  "DELETE_INSTANCE",
  "VIEW_INSTANCE_PROGRESS",
  "VIEW_INSTANCE_FULL"
]
```

Đặt `START_INSTANCE` trong `processInstanceAccessControls[].functions` cho các personnel/role/department/position được phép chạy. Đặt các quyền xem process của performer trong `participantPermission`; không dùng starter-only permission của Manual/Sequence nếu người dùng không yêu cầu.

## XML Start Event

```xml
<bpmn2:startEvent id="NOSTART0000001" name="Start">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="START_NORMAL_EVENT" />
  </bpmn2:extensionElements>
  <bpmn2:outgoing>FLFLOW00000001</bpmn2:outgoing>
</bpmn2:startEvent>
```

Khai báo `xmlns:configEx="http://config-ex/schema"`. Thêm `BPMNShape` và `BPMNLabel` cho Start giống mọi node khác.

## Payload tối thiểu

```json
{
  "type": "normal_flow",
  "metadata": {},
  "overviewScreen": {
    "layout": [],
    "permissionGeneralInfo": []
  },
  "userTasks": [],
  "actions": [],
  "gateWays": [],
  "loops": [],
  "resources": {
    "system": [],
    "custom": [],
    "userTasks": [],
    "actions": [],
    "loops": []
  }
}
```

`overviewScreen` phải là object. API hiện từ chối `null` với lỗi `overviewScreen is not a JSONObject`; dùng object mặc định trên khi không cấu hình overview riêng.

## Chạy thử

Kích hoạt và xuất bản qua API, rồi tạo lượt chạy bằng `/api/v1/run-workflow-server` service `10` với `{"processId", "instanceName"}` theo [SKILL.md mục 4.6](../SKILL.md#46-kích-hoạt-và-xác-nhận-process-end-to-end-bắt-buộc) và [api-process-runtime.md](../api-process-runtime.md); tiêu chí chi tiết tại [runtime-validation.md](runtime-validation.md). API này chỉ nhận `normal_flow` (`r: 205` với loại khác) và yêu cầu version `ACTIVATED` + `isPublished: true` (`r: 206`). Quyền mặc định để mọi personnel hiện tại chạy/xem phải dùng `option: 1`, `items: [""]`.

Nếu Normal Flow được thiết kế để process cha/module gọi, cần kiểm chứng thêm lượt gọi thực tế từ bên gọi đó cùng dữ liệu đầu vào và kết quả mong đợi. Chạy trực tiếp chỉ kiểm tra riêng Normal Flow, chưa chứng minh phần tích hợp với bên gọi hoạt động đúng.
