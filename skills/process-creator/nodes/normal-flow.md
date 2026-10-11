# Normal Flow (`normal_flow`)

Đọc file này khi cần tạo quy trình không có form Root bắt buộc, thường để process cha hoặc module khác gọi. Mẫu: `samples/sample_normal_flow.json`.

## Cách dùng

- Process cha gọi qua node Sub Process: tách các bước xử lý thành quy trình con để process cha gọi và truyền dữ liệu vào; cấu hình quy trình con và mapping input/output theo [sub-process-task.md](sub-process-task.md).
- Module khác gọi: ví dụ module SLA phát hiện một vi phạm rồi gọi Normal Flow để tạo cảnh báo, gửi email hoặc thông báo cho quản lý (module SLA phát hiện, Normal Flow xử lý khi được gọi). Custom Backend Module gọi bằng `processes.start`: xem [Được Custom Backend Module khởi chạy](#được-custom-backend-module-khởi-chạy).
- Chạy độc lập vẫn được hỗ trợ cho người có quyền `START_INSTANCE`, nhưng hiếm dùng. Khi thiết kế, xác định bên gọi dự kiến (process cha, module hay người dùng) và dữ liệu cần nhận/trả; yêu cầu đã nêu process cha hoặc module gọi thì lấy cách gọi đó làm ngữ cảnh chính thay vì mặc định cần người dùng bấm **Tạo lượt chạy**.

## Được Custom Backend Module khởi chạy

Custom Backend Module khởi chạy Normal Flow bằng `processes.start(processInfoId, { input, instanceName, idempotencyKey, onComplete })` của `@cogover/sdk` (từ `0.15.0`, code do [$cogover-custom-module](../../cogover-custom-module/SKILL.md) phụ trách). Thiết kế Process cho bên gọi này:

- Bên gọi dùng **Process ID** (`processInfoId`, prefix `PI`), không dùng ID version (`PE...`). Cogover khởi chạy version đã kích hoạt và đã xuất bản; chỉ Normal Flow được nhận. Giữ Process ID ổn định: sửa bằng version mới (mục 4.4 của `SKILL.md`), không xoá rồi tạo lại.
- Dữ liệu vào là các Variable có `availableForInput: true`, truyền theo slug biến (ví dụ `{"lead_id": "..."}`); biến không tồn tại hoặc không đánh dấu input bị từ chối. Kết quả trả cho module là các Variable có `availableForOutput: true` (ví dụ gán bằng Assignment trước End Process): module nhận chúng trong job `onComplete` khi lượt chạy kết thúc với trạng thái `COMPLETED`, `CANCELED`, `DELETED` hoặc `FAILED`. Giá trị output được chuyển như khi ghi field (record thành ID, ngày thành `YYYY-MM-DD`, ngày giờ thành Unix ms); tổng output lớn hơn 48 KiB thì module nhận `null`, nên chỉ trả dữ liệu module cần.
- Lượt chạy mang danh tính người dùng của lần gọi trong module; lời gọi không có người dùng (job theo lịch, webhook) tạo lượt chạy **không có người khởi tạo**: node dùng người khởi tạo (User Task giao cho starter, AI Agent hay Custom Module Action với `PROCESS_STARTER`) phải có phương án khác. Người dùng gọi phải có `START_INSTANCE` trên Process (`processInstanceAccessControls`), identity policy của module phải cho phép Process ID này trong mục `processes`.
- Module không chờ lượt chạy trong request: kiểm thử bằng cách gọi module rồi theo dõi lượt chạy theo [api-process-runtime.md](../api-process-runtime.md), kiểm tra biến output và job nhận kết quả phía module.

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
