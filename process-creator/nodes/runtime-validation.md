# Runtime Validation

Đọc file này sau mọi lần tạo process và khi người dùng yêu cầu test chức năng node: kiểm thử black-box trên workspace qua API, không chỉ kiểm tra payload create. Trình tự thao tác (POST + GET-back verify, kích hoạt và xuất bản qua API, tạo lượt chạy theo từng loại flow, poll chi tiết lượt chạy, đọc và submit form User Task, quyền/vị trí tạm bằng `$user-permission`, Object `Process_Debug_data`, cleanup và báo cáo): [SKILL.md mục 4.6](../SKILL.md#46-kích-hoạt-và-xác-nhận-process-end-to-end-bắt-buộc); hợp đồng API: [api-process-lifecycle.md](../api-process-lifecycle.md), [api-process-runtime.md](../api-process-runtime.md). File này bổ sung tiêu chí PASS theo node, kịch bản kiểm thử qua API, email workspace, giới hạn backend và cách phân loại kết quả. Với mỗi lượt chạy, ghi lại process ID/PI, instance ID, trạng thái, elapsed time, Debug output và bằng chứng hiệu ứng bên ngoài.

`COMPLETED` chỉ là bằng chứng flow đã kết thúc. Chỉ đánh PASS cho node khi quan sát được semantic tương ứng bên dưới.

## Tiêu chí observable theo node

| Node/case | Bằng chứng PASS tối thiểu |
|---|---|
| End/Exclusive/Inclusive/Parallel/End Branch | Tập node đã qua (`completedTasks`, `submittedNodeIds`, `Process_Debug_data`) khớp đúng nhánh kỳ vọng và không có node ngoài kỳ vọng; với Inclusive phải thấy tất cả nhánh true, với Parallel phải thấy tất cả nhánh |
| Assignment | Gateway downstream kiểm tra giá trị đích. Test riêng `=`, NUMBER/TEXT `+=`, NUMBER `-=`, `count` với list thật |
| Formula | Dùng result trong HTTP echo hoặc gateway downstream. Metadata phải khớp data type; test TEXT và NUMBER riêng |
| Text Template | Gửi result vào HTTP echo/email và đối chiếu nội dung đã render |
| User Task | `runningUserTasks[]` chứa đúng `nodeId`; form đọc được qua API với giá trị mặc định/`readOnly`/`required` đúng thiết kế; submit thiếu field bắt buộc trả `30002`; submit hợp lệ trả `r: 0`, node chuyển sang `completedTasks` và field value dùng được downstream |
| HTTP | Endpoint echo xác nhận method, status, headers/query/body; test ít nhất GET và POST |
| Wait relative time | Node sau Wait không chạy trước mốc, chạy sau mốc; đo elapsed time. Payload runtime phải có `maximumWaitTimeValue`/unit |
| Wait email | Email thực sự được gửi; mở/reply/click đúng email; Exclusive Gateway sau Wait kiểm tra `$action.{wait_slug}.isEventTriggered == true` và đi nhánh EVENT_PASS trước timeout. Node sau Wait chạy đơn thuần không đủ vì timeout cũng tiếp tục flow |
| Send Email | Mail xuất hiện ở mailbox đích với đúng from/subject/body. Với `WORKSPACE_EMAIL`, dùng `emailId` workspace thật; raw recipient được phép |
| Notification / Push Toast | Đúng người nhận thấy badge/toast và đúng nội dung |
| Push Background | Chỉ PASS khi có consumer observable nhận/áp dụng payload; instance Completed một mình là PARTIAL |
| Create Record | Query/UI thấy record mới và field values đúng |
| Get Records | Dùng `$action.{slug}.output.record(s)` ở Update/Loop và thấy đúng record được tiêu thụ; Debug `preparing` không đủ |
| Update Record | Đọc lại cùng record ID và so sánh before/after |
| Loop | List có sort cố định; kiểm tra số vòng và thứ tự bằng notification/accumulator. Test direction 1/2 riêng; không đọc `count` sau loop vì runtime reset về 0 |
| Organization | Gateway downstream kiểm tra `output.total >= 1` và/hoặc lưu field của record thật vào variable; log `preparing` không đủ |
| Sub Process sync | Child instance/action chạy, output mapping về parent và gateway downstream kiểm tra giá trị; chỉ thấy `SUCCESS` mà output trống là PARTIAL |
| Export Record | Output chứa FileValue/file tải được, mở được và thuộc đúng record/template |
| AI Agent | GET-back giữ đúng action `AI_AGENT`, cấu hình và output resources; đúng instance có `output.status = COMPLETED`, câu trả lời đáp ứng instruction và bước sau đọc được output. Nếu yêu cầu tool/record change, phải đối chiếu hiệu ứng thực tế; nếu có schema, kiểm tra `output.result` đúng kiểu và dùng được downstream. Đọc `ai-agent-task.md` cho test phiên nối tiếp, lỗi và timeout |

## Email workspace

- Nếu personnel sender lỗi `USER_DONT_HAVE_EMAIL`, không suy ra rằng địa chỉ trong hồ sơ personnel đủ để gửi. Runtime `PERSONNEL_EMAIL` cần email channel/account tương ứng.
- Khi workspace đã cấu hình sender, dùng `fromType: "WORKSPACE_EMAIL"` và `emailId` thật của sender. Không dùng tên hiển thị hoặc địa chỉ email thay cho ID.
- Dùng một subject duy nhất có timestamp/test token, gửi tới địa chỉ người dùng đã cho phép, rồi kiểm tra hộp thư đích (bằng chứng này không có API trong skill; dùng mail client hoặc trình duyệt). Xác nhận From, To, Subject, body và thời điểm nhận.
- Với Wait EMAIL_OPEN/REPLY/LINK_WAS_CLICKED, tạo mỗi event một lượt chạy rõ ràng. Bắt buộc gateway EVENT_PASS/TIMEOUT dựa trên `isEventTriggered`; dùng token/subject khác nhau cho hai nhánh. Link click nên trỏ tới URL kiểm thử an toàn do người dùng cho phép.

## Backend limitations hiện tại

Không tạo các node/case sau cho executable flow cho tới khi backend registration/handler được test lại:

- `PARSE_TO_OBJECT`: schema có thể valid nhưng runtime action chưa được đăng ký.
- `RESPONSE_WEBHOOK`: runtime action chưa được đăng ký.
- Wait `RECEIVE_EVENT_FROM_WEBHOOK`: chưa có handler giải phóng Wait.
- Wait `AT_A_SPECIFIED_TIME`: absolute timestamp được parse nhưng scheduler không dùng.
- Wait `NUMBER_OF_MATCHING_RECORDS` trong Normal Flow có `process.objectTypeId` rỗng.

Nếu người dùng yêu cầu các case này, giải thích giới hạn runtime cụ thể và đề xuất workflow thay thế hoặc backend change; không tạo một process “valid” rồi gọi đó là PASS.

## Kịch bản kiểm thử qua API

Mỗi kịch bản là một lượt chạy riêng với `instanceName` có marker; API và body theo [api-process-runtime.md](../api-process-runtime.md). Trước khi chạy, tính đường đi kỳ vọng (danh sách node theo thứ tự) từ `xmlString` cho từng kịch bản; PASS khi tập node quan sát được khớp và không có node ngoài kỳ vọng.

| Kịch bản | Cách chạy | Bằng chứng PASS |
|---|---|---|
| Đường đi cơ bản | Tạo lượt chạy (service `10`, hoặc `1` với `instanceId` rỗng cho Manual); poll service `36`/`33` | `currentState`, `runningUserTasks`, `completedTasks`/`submittedNodeIds` khớp đường đi kỳ vọng; elapsed time hợp lý |
| Mỗi nhánh gateway | Một lượt chạy cho mỗi nhánh với dữ liệu form/biến đưa điều kiện về true/false/mặc định | Node của nhánh đúng xuất hiện, node của nhánh khác không xuất hiện |
| Form User Task | Service `29` với `instanceId` + `nodeId` đang chờ | Field, giá trị mặc định (Variable, dữ liệu bước trước), `readOnly`, `required`, nhóm nút đúng thiết kế; `variables` mang giá trị hiện tại theo `slug` |
| Validate submit | Service `1` thiếu field `required`, sai kiểu (text cho `numeric`, `date` không phải `"YYYY-MM-DD"`), gửi field `readOnly` | Trả `30002` với `meta.more.requiredButNotProvidedFields`/`invalidDataTypeFields` đúng field; lượt chạy không được tạo/không chuyển node |
| Submit hợp lệ | Service `1` đủ dữ liệu, đúng `submittedButton` | `r: 0`; sau vài giây `completedTasks` có node vừa submit với `formId`; node kế tiếp vào `runningUserTasks` hoặc `currentState: "COMPLETED"`; giá trị submit đọc được bằng service `2` (`$userTask.{task}.{field}`) và dùng được ở gateway/action sau |
| Rollback User Task | Service `3` với `nodeId` node liền trước và `submittedId` từ `completedTasks[].formId` | `r: 0`; node trước quay lại `runningUserTasks`; submit lại thêm phần tử `completedTasks` mới và đi tiếp bình thường; gọi trên node không liền trước trả `3` |
| Tạm dừng, tiếp tục | Service `5` `state: 4` rồi `state: 2` | Sau tạm dừng `currentState: "PAUSED"`, submit trả `10`, node không tiến; sau tiếp tục `RUNNING` và tiến tiếp; gửi lại cùng trạng thái trả `2`, chuyển không hợp lệ (ví dụ `state: 3`) trả `4` trong `data[]` |
| Huỷ | Service `5` `state: 5` | `currentState: "CANCELED"`; submit trả `10`; tiếp tục sau huỷ trả `3`, huỷ lại trả `2`; không node mới trong `Process_Debug_data` |
| Quyền | Gọi tạo lượt chạy/submit bằng người không có `START_INSTANCE` hoặc không phải performer; service `37` | Trả `9`/`8`; `permission[]` không chứa quyền tương ứng |
| Version | Kích hoạt V1, tạo lượt chạy A; lưu thành version mới (service `24`, XML dùng `bpmn2:`), sửa nếu cần bằng `23`, kích hoạt/xuất bản V2 (service `39`) | Lượt chạy A giữ `processVersion` V1 và submit tiếp được; lượt chạy mới có `processVersion` V2; danh sách version (service `8`): V2 `currentVersion: true` xuất bản, V1 `ACTIVATED` nhưng `isPublished: false`; xuất bản lại V1 (`38`) đảo ngược, `39` trên V1 trả `409` |
| Bỏ xuất bản, vô hiệu hoá | Service `40`, rồi `10` | Normal: tạo lượt chạy mới trả `206` với `meta` ghi trạng thái; sau `10` version `CANCELED`; Scheduled/Triggered không sinh lượt chạy mới; lượt chạy đang chạy vẫn submit tới kết thúc; Manual submit Root vẫn tạo lượt chạy (không dựa vào đây để chặn) |
| Scheduled, Triggered, Webhook | Kích hoạt theo lịch/bản ghi/HTTP POST, tìm lượt chạy bằng service `35` (`process_info_id`, thời điểm) hoặc `Process_Debug_data` | Lượt chạy xuất hiện đúng thời điểm/sự kiện với input (`$flow.input.*`) đúng; cleanup lịch/bản ghi đã khôi phục |

Cleanup: huỷ lượt chạy test còn `RUNNING`/`PAUSED` (service `5`), xoá lượt chạy (service `6`) chỉ khi người dùng đã xác nhận danh sách ID; khôi phục lịch, quyền và fixture theo SKILL.md mục 4.6.

## Phân loại báo cáo

- **PASS:** payload đúng và semantic runtime được quan sát.
- **PARTIAL:** create/run thành công nhưng thiếu bằng chứng semantic hoặc thiếu output mapping/consumer.
- **FAIL_SKILL:** skill tạo payload sai/mâu thuẫn contract; ghi đúng trường/sample cần sửa.
- **FAIL_RUNTIME:** payload đúng theo contract nhưng backend thực thi sai hoặc action/handler thiếu.
- **BLOCKED_ENV:** không thể thử vì phiên Web App/quyền/provider/template/record/mailbox hoặc API trả `5001`; ghi các retry đã làm và thông tin tối thiểu người dùng cần cung cấp.

Không quy lỗi skill cho lỗi thao tác agent hoặc transport HTTP. Không quy PASS từ static GET-back.

Một số response GET-back thêm field dẫn xuất, ví dụ Organization personnel criteria có thể có `field: "personnel"`. Nếu semantic config và runtime đúng, coi đó là server canonicalization; không PUT chỉ để xóa field response-only.
