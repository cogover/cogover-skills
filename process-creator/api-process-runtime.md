# Web App API lượt chạy

Tạo lượt chạy, theo dõi lượt chạy đang ở node nào, đọc và submit form User Task, quay lại bước trước, tạm dừng, tiếp tục, huỷ và xoá lượt chạy bằng API, không thao tác trên giao diện. Hành vi dưới đây đã được chạy thử trên Workspace ngày 2026-09-13 với Manual Flow và Normal Flow; mã service có thể thay đổi theo phiên bản nền tảng.

## 1. Endpoint, xác thực và envelope

- Hai endpoint, cùng phiên Web App và cùng envelope như [api-process-lifecycle.md mục 1](api-process-lifecycle.md#1-endpoint-xác-thực-và-envelope):
  - `POST /api/v1/run-workflow-server` với `x-req-type: 6`: tạo lượt chạy, submit form, rollback, đổi trạng thái, xoá, đọc giá trị resource.
  - `POST /api/v1/workflow` với `x-req-type: 1`: đọc chi tiết lượt chạy, form User Task, quyền, danh sách lượt chạy và việc cần làm.
- Thành công khi `body.r = 0`. Với thao tác nhận mảng `instances`, `body.r = 0` chỉ nghĩa là request được xử lý; kết quả từng phần tử nằm trong `body.data[]` với `r` riêng.
- Thay `{SERVICE}`, `{TYPE}` và `{BODY}` trong mẫu curl ở [api-process-lifecycle.md](api-process-lifecycle.md#1-endpoint-xác-thực-và-envelope), đổi URL theo endpoint tương ứng.
- ID lượt chạy do server sinh, không có prefix cố định; luôn lấy từ `body.data.instanceId` của lệnh tạo.

## 2. Tạo lượt chạy theo loại flow

Đặt `instanceName` chứa marker duy nhất (ví dụ `TEST-{YYYYMMDD-HHMM}`) để tìm lại đúng lượt chạy.

| Loại | Endpoint, `x-req-service` | Body | Kết quả |
|---|---|---|---|
| Normal | run-workflow-server, `10` | `{"processId": "{PROCESS_ID}", "instanceName": "{INSTANCE_NAME}"}` | `body.data`: `{"processId", "instanceId"}`; `instanceName` rỗng thì server tự đặt tên. Yêu cầu version `ACTIVATED` + `isPublished: true` và `START_INSTANCE` |
| Manual | run-workflow-server, `1` (submit form Root với `instanceId` rỗng) | Xem mục 2.1 | `body.data`: `{"processId", "instanceId"}`. Không kiểm tra trạng thái xuất bản/kích hoạt của version; chỉ kiểm tra quyền thực hiện Root |
| Sequence | run-workflow-server, `7` | `{"list": [{"processId": "{PROCESS_ID}", "flowObjectRecordId": "{RECORD_ID}"}]}` | Một lượt chạy cho mỗi bản ghi được liên kết; cần `CONNECT_SEQUENCE` |
| Scheduled | Không có API tạo trực tiếp | Kích hoạt theo `scheduleRules`; theo dõi bằng mục 3 | |
| Triggered record / webhook | Không có API tạo trực tiếp | Tạo/cập nhật bản ghi bằng `$object-record` hoặc gửi HTTP POST tới URL webhook; theo dõi bằng mục 3 | |

Lỗi tạo lượt chạy Normal: `4` process không tồn tại; `205` không phải `normal_flow` (`meta.processType`); `206` chưa `ACTIVATED`/chưa xuất bản/đã xoá (`meta` ghi `progressStatus`, `isPublished`, `isDeleted`); `5` không có node sau Start; `3` chưa xác thực; `9` không có quyền `START_INSTANCE`; `207` lưu dữ liệu khởi tạo thất bại.

### 2.1. Manual Flow: đọc form Root rồi submit

1. Đọc form Root bằng `/api/v1/workflow`, service `29`:

   ```json
   {"processId": "{PROCESS_ID}", "processInfoId": "{PROCESS_INFO_ID}", "instanceId": "", "nodeId": "", "forDebug": false}
   ```

   `body.data` gồm `nodeId` (Root), `nodeScreenId`, `nodeScreenSlug`, `content` (layout `layoutRow → ... → components`; mỗi component có `slug`, `fieldType`, `required` (`0`/`1`), `readOnly`, `defaultValue`, `fieldMetaData`), `buttons` (nhóm nút; có thể rỗng), `variables` (giá trị hiện tại theo `slug`, kèm các key phụ `{slug}.toolTip`, `{slug}.hintText`), `pageSettings`, `title`, `approve`, `permission`, `processVersion`; `instanceId` và `instanceState` là `null` vì chưa có lượt chạy. Version chưa kích hoạt trả `r: 410` (`_httpStatusCode: 403`).
2. Dựng `data` từ `content`: key là `slug` của component, giá trị đúng kiểu của `fieldType` ([nodes/user-task-form-fields.md](nodes/user-task-form-fields.md)); field `required` bắt buộc có giá trị; field `readOnly` không gửi trừ khi bật `canSendData`. Field `date` nhận chuỗi `"YYYY-MM-DD"`; epoch millis, ISO 8601 hay `DD/MM/YYYY` bị từ chối. Field không bắt buộc có thể bỏ khỏi `data`.
3. `submittedButton` là `slug` của nút trong `buttons`/`content`. Server không bắt buộc nút tồn tại: form không có nút thì gửi một chuỗi bất kỳ (ví dụ `"submit"`); form có nút approve/reject hoặc nút gán resource thì phải gửi đúng slug để chạy logic của nút đó.
4. Submit bằng run-workflow-server, service `1`:

   ```json
   {
     "processId": "{PROCESS_ID}",
     "instanceId": "",
     "nodeId": "{ROOT_NODE_ID}",
     "instanceName": "{INSTANCE_NAME}",
     "submittedButton": "{BUTTON_SLUG}",
     "data": {"{FIELD_SLUG}": "..."},
     "dataForDisplay": []
   }
   ```

   `dataForDisplay` là danh sách key trong `variables` cần hiển thị lại ở màn hình đã submit (có thể rỗng). `nodeId` rỗng thì server lấy node ngay sau Start. Thành công: `msg` "Process instance was started successfully", `body.data.instanceId` là lượt chạy mới.

Lỗi riêng của Manual: `201` không phải `manual_flow`; `202` node submit không phải Root; `204` không có Root; các lỗi validate ở mục 4.

## 3. Theo dõi lượt chạy

| Mục đích | Endpoint, `x-req-service` | Body | Trường cần đọc trong `body.data` |
|---|---|---|---|
| Chi tiết lượt chạy, node đang chờ, node đã qua | `/api/v1/workflow`, `36` | `{"processId": "{PROCESS_ID}", "instanceId": "{INSTANCE_ID}"}` | `currentState` (`NOT_STARTED`/`RUNNING`/`COMPLETED`/`PAUSED`/`CANCELED`/`DELETED`); `runningUserTasks[]` (`id`, `nodeId`, `name`, `canPerformThisTask`, `performerConfig`, `deadline`); `completedTasks[]` mới nhất trước (`id` = nodeId, `nodeId`, `name`, `formId`, `completedTime`, `buttonName`, `rollback`, `actionType`); `processVersion`; `instanceName`; `starter`; `processInfoId`; `processStatus`; `xmlString`; `permission[]` |
| Trạng thái process của lượt chạy | `/api/v1/workflow`, `33` | `{"id": "{PROCESS_ID}", "processInfoId": "{PROCESS_INFO_ID}", "instanceId": "{INSTANCE_ID}"}` | `processStatus`, `xmlString`; `submittedNodeIds` không có trong response quan sát được, dùng `completedTasks` của service `36` |
| Quyền của người gọi với lượt chạy | `/api/v1/workflow`, `37` | `{"processId": "{PROCESS_ID}", "instanceId": "{INSTANCE_ID}"}` | `permission[]`: `START_INSTANCE`, `VIEW_INSTANCE_PROGRESS`, `VIEW_INSTANCE_FULL`, `CANCEL_INSTANCE`, `DELETE_INSTANCE`, `DO_EVERY_TASK_IN_SEQUENCE` |
| Danh sách lượt chạy người gọi thấy | `/api/v1/workflow`, `35` | `{"process_info_id": "{PROCESS_INFO_ID}", "size": 20}`; thêm `search_after` từ `meta` để lấy trang kế | Mảng `instanceId`, `instanceName`, `instanceStatus`, `currentRunningNodes`, `processId`, `processInfoId`, `processName`, `processVersion`, `stater`, `created`, `updated`; `meta.total`, `meta.search_after`. Response quan sát được không lọc theo `process_info_id`: lọc phía client theo `processId`/`processInfoId`, `instanceName` (marker) và `created` |
| Việc cần làm của người gọi | `/api/v1/workflow`, `27` | `{"size": 20}` | Mảng User Task đang chờ người gọi: `instanceId`, `nodeId`, `nodeScreenId`, `nameInstance`, `nameProcess`, `nameTask`, `version`, `startAt`, `id` (`{instanceId}_{nodeId}`); `meta.next_page`, `meta.search_after`, `meta.total` |
| Giá trị resource trong lượt chạy | run-workflow-server, `2` | `{"requestResources": [{"processId": "{PROCESS_ID}", "instanceId": "{INSTANCE_ID}", "resources": [{"slug": "$userTask.Root.{field_slug}", "calc": false}]}]}` | `requestResourcesValues[]`: `r`, `instanceId`, `resourceValues` (`{slug: value}`); `calc: true` để tính lại Formula; dùng cho `$flow.{slug}`, `$userTask.{task}.{field}`, `$action.{slug}.output...` |

Cách đọc "đang ở node nào, đã qua node nào":

- User Task: `runningUserTasks[].nodeId` là node đang chờ; `completedTasks[].nodeId` là các User Task đã qua theo `completedTime` giảm dần; một node được submit nhiều lần (sau rollback) xuất hiện nhiều phần tử với `formId` khác nhau.
- Action, gateway, loop không xuất hiện trong `completedTasks`; đối chiếu bằng Object `Process_Debug_data` (SKILL.md mục 4.6) hoặc bằng hiệu ứng nghiệp vụ của action theo [nodes/runtime-validation.md](nodes/runtime-validation.md).
- Chi tiết lượt chạy cập nhật trễ: ngay sau tạo lượt chạy hay submit, service `36` có thể vẫn trả node cũ và `completedTasks` chưa đủ trong vài giây; sau huỷ, `runningUserTasks` có thể vẫn liệt kê node cũ. Poll mỗi 2–5 giây tới khi `currentState`/`runningUserTasks` đổi, tối đa theo thời gian chờ hợp lý của flow (Wait, AI Agent, HTTP). Ghi elapsed time; `currentState: "COMPLETED"` chỉ chứng minh flow đã kết thúc.

## 4. Form User Task đang chờ: đọc và submit

1. Lấy `nodeId` đang chờ từ `runningUserTasks[]` (service `36`) hoặc từ danh sách việc cần làm (service `27`).
2. Đọc form bằng service `29` với `instanceId` và `nodeId` đó: `content` mang cấu hình và giá trị mặc định của từng field, `variables` mang giá trị hiện tại theo `slug` (chỉ field của chính form này; dữ liệu bước trước không tự xuất hiện trừ khi form tham chiếu), `instanceState`, `submitAgainAllowed`, `permission`. Thêm `"formSubmitId": "{completedTasks[].formId}"` để xem lại form đã submit.
3. Submit bằng service `1` với `instanceId` của lượt chạy, `nodeId` của User Task, `submittedButton`, `data`, `dataForDisplay` (cùng cấu trúc mục 2.1). Thành công: `msg` "Continue an Process Instance ok!". Sau đó poll service `36` để xác nhận `completedTasks` có node vừa submit và `runningUserTasks` chuyển sang node kế tiếp (hoặc `currentState: "COMPLETED"`).
4. Quay lại bước trước (rollback) bằng service `3`:

   ```json
   {"processId": "{PROCESS_ID}", "instanceId": "{INSTANCE_ID}", "nodeId": "{PREVIOUS_NODE_ID}", "submittedId": "{completedTasks[].formId}"}
   ```

   `submittedId` là `formId` của lần submit cần đánh dấu đã hoàn tác; bỏ trống vẫn rollback được nhưng `completedTasks[].rollback` không được cập nhật. Chỉ hợp lệ khi lượt chạy `RUNNING`, `nodeId` là node ngay trước node đang chờ và người gọi có quyền thực hiện node đó. Thành công: `msg` "Successfully", node đó quay lại `runningUserTasks`; submit lại tạo thêm một phần tử `completedTasks`. `r` khác `0`: `1` không tìm thấy, `2` không `RUNNING`, `3` không phải node liền trước, `8` không có quyền node.

Lỗi khi submit:

| `r` | Ý nghĩa |
|---|---|
| `30002` | "Error in fields", `meta.errorType: TASK_VALIDATION_ERROR`, `meta.element` (node), `meta.more` gồm `invalidDataTypeFields` (sai kiểu, ví dụ text cho `numeric`, sai định dạng `date`), `requiredButNotProvidedFields` (thiếu bắt buộc), `requireListButProvidedSingleValueFields` (field nhiều giá trị nhận đơn) |
| `30001`, `30003`, `30004`, `30005` | Mã validate khác của cùng nhóm (sai kiểu, gửi field chỉ đọc, field phải là danh sách, node không phải node đang chờ); response quan sát được gộp lỗi field vào `30002` |
| `10` | Lượt chạy đã `COMPLETED`/`CANCELED`/`PAUSED` |
| `8` | Không có quyền thực hiện node, kể cả khi `nodeId` trỏ tới node không phải User Task |
| `5` | `nodeId` không tồn tại |
| `4` | `processId` hoặc `instanceId` không tồn tại (lượt chạy sai trả `PROCESS_NOT_FOUND`, không phải `6`) |

## 5. Đổi trạng thái và xoá lượt chạy

Endpoint run-workflow-server. Body nhận mảng để xử lý nhiều lượt chạy; đọc `r` từng phần tử trong `body.data[]`.

| Thao tác | `x-req-service` | Body |
|---|---|---|
| Tạm dừng | `5` | `{"instances": [{"processId": "{PROCESS_ID}", "instanceId": "{INSTANCE_ID}", "state": 4}]}` |
| Tiếp tục | `5` | như trên với `"state": 2` |
| Huỷ | `5` | như trên với `"state": 5` |
| Xoá | `6` | `{"instances": [{"processId": "{PROCESS_ID}", "instanceId": "{INSTANCE_ID}"}]}` |

Mã `state`: `1` NOT_STARTED, `2` RUNNING, `3` COMPLETED, `4` PAUSED, `5` CANCELED, `6` DELETED. Chuyển trạng thái hợp lệ: `RUNNING → PAUSED`, `RUNNING → CANCELED`, `PAUSED → RUNNING`, `PAUSED → CANCELED`. Không chuyển được từ `COMPLETED`, `CANCELED`, `DELETED`; không đặt trực tiếp `COMPLETED` hay `DELETED`.

`r` từng phần tử của service `5` (`body.r` luôn `0`, `msg` "Update Process instance state successfully"): `0` thành công (`msg: "OK"`); `1` không tìm thấy lượt chạy; `2` trạng thái không đổi (kể cả huỷ lại lượt đã huỷ); `3` lượt chạy đã `COMPLETED`/`CANCELED`/`DELETED`; `4` chuyển trạng thái không hợp lệ (`error: "Invalid state transition"`); `40` không có quyền; `50` lỗi tra cứu tổ chức. Quyền: người khởi tạo khi `starterPermission` cho phép huỷ, hoặc `CANCEL_INSTANCE` trong `processInstanceAccessControls` (quyền này bao gồm tạm dừng, tiếp tục, huỷ). Xoá cần `DELETE_INSTANCE` hoặc người khởi tạo được phép xoá; dữ liệu form đã submit của lượt chạy bị xoá bất đồng bộ sau khi trả `r: 0`.

Sau tạm dừng, submit trả `10` và `currentState: "PAUSED"`; tiếp tục từ `PAUSED` làm lượt chạy chạy tiếp ngay từ node đang chờ. Huỷ hoặc xoá: liệt kê `instanceId` cụ thể và hỏi xác nhận trước, trừ lượt chạy test do chính phiên này tạo và người dùng đã cho phép dọn dẹp.

## 6. Mã lỗi chung của run-workflow-server

| `r` | Ý nghĩa |
|---|---|
| `0` | Thành công |
| `1` | Lỗi không xác định |
| `2` | Body JSON không parse được |
| `3` | Chưa xác thực; kiểm tra phiên Web App |
| `4` | Không tìm thấy process hoặc lượt chạy |
| `5` | Không tìm thấy node |
| `6` | Không tìm thấy lượt chạy (ít gặp, xem `4`) |
| `7` | Lỗi tra cứu tổ chức khi kiểm tra quyền |
| `8` | Không có quyền với node |
| `9` | Không có quyền với process |
| `10` | Lượt chạy đã `COMPLETED`/`CANCELED`/`PAUSED` |
| `11` | Sequence Flow thiếu ID bản ghi |
| `12` | `submittedButton` không tồn tại (hiện không được kiểm tra) |
| `201`–`207` | Sai loại flow hoặc process chưa sẵn sàng (mục 2) |
| `30001`–`30005` | Lỗi validate form (mục 4) |
| `5001` | Sai `x-req-service`/`x-req-type` |

Mã `x-req-service` là hợp đồng của Web App và có thể thay đổi theo phiên bản nền tảng; gặp `5001` hoặc response khác cấu trúc mong đợi thì dừng và báo, không dò số.
