# Runtime Validation

Đọc file này sau mọi lần tạo process và khi người dùng yêu cầu test chức năng node: kiểm thử black-box trên workspace, không chỉ kiểm tra payload create. Trình tự thao tác (POST + GET-back verify, mở process trên Chrome, **Kích hoạt** và **Xuất bản**, tạo lượt chạy theo từng loại flow, xác định đúng instance, submit User Task đầu tiên, quyền/vị trí tạm bằng `$user-permission`, Object `Process_Debug_data`, cleanup và báo cáo): [SKILL.md mục 4.6](../SKILL.md#46-kích-hoạt-và-xác-nhận-process-end-to-end-bắt-buộc). File này bổ sung tiêu chí PASS theo node, email workspace, giới hạn backend và cách phân loại kết quả. Với mỗi lượt chạy, ghi lại process ID/PI, instance ID, trạng thái, elapsed time, Debug output và bằng chứng hiệu ứng bên ngoài.

`COMPLETED` chỉ là bằng chứng flow đã kết thúc. Chỉ đánh PASS cho node khi quan sát được semantic tương ứng bên dưới.

## Tiêu chí observable theo node

| Node/case | Bằng chứng PASS tối thiểu |
|---|---|
| End/Exclusive/Inclusive/Parallel/End Branch | Diagram cho thấy đúng nhánh/node đã chạy; với Inclusive phải thấy tất cả nhánh true, với Parallel phải thấy tất cả nhánh |
| Assignment | Gateway downstream kiểm tra giá trị đích. Test riêng `=`, NUMBER/TEXT `+=`, NUMBER `-=`, `count` với list thật |
| Formula | Dùng result trong HTTP echo hoặc gateway downstream. Metadata phải khớp data type; test TEXT và NUMBER riêng |
| Text Template | Gửi result vào HTTP echo/email và đối chiếu nội dung đã render |
| User Task | Instance dừng ở task; form mở được, required validation hoạt động, submit thành công, field value dùng được downstream |
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
- Dùng một subject duy nhất có timestamp/test token, gửi tới địa chỉ người dùng đã cho phép, rồi kiểm tra mailbox trên Chrome. Xác nhận From, To, Subject, body và thời điểm nhận.
- Với Wait EMAIL_OPEN/REPLY/LINK_WAS_CLICKED, tạo mỗi event một lượt chạy rõ ràng. Bắt buộc gateway EVENT_PASS/TIMEOUT dựa trên `isEventTriggered`; dùng token/subject khác nhau cho hai nhánh. Link click nên trỏ tới URL kiểm thử an toàn do người dùng cho phép.

## Backend limitations hiện tại

Không tạo các node/case sau cho executable flow cho tới khi backend registration/handler được test lại:

- `PARSE_TO_OBJECT`: schema có thể valid nhưng runtime action chưa được đăng ký.
- `RESPONSE_WEBHOOK`: runtime action chưa được đăng ký.
- Wait `RECEIVE_EVENT_FROM_WEBHOOK`: chưa có handler giải phóng Wait.
- Wait `AT_A_SPECIFIED_TIME`: absolute timestamp được parse nhưng scheduler không dùng.
- Wait `NUMBER_OF_MATCHING_RECORDS` trong Normal Flow có `process.objectTypeId` rỗng.

Nếu người dùng yêu cầu các case này, giải thích giới hạn runtime cụ thể và đề xuất workflow thay thế hoặc backend change; không tạo một process “valid” rồi gọi đó là PASS.

## Phân loại báo cáo

- **PASS:** payload đúng và semantic runtime được quan sát.
- **PARTIAL:** create/run thành công nhưng thiếu bằng chứng semantic hoặc thiếu output mapping/consumer.
- **FAIL_SKILL:** skill tạo payload sai/mâu thuẫn contract; ghi đúng trường/sample cần sửa.
- **FAIL_RUNTIME:** payload đúng theo contract nhưng backend thực thi sai hoặc action/handler thiếu.
- **BLOCKED_ENV:** không thể thử vì Chrome/session/quyền/provider/template/record/mailbox; ghi các retry đã làm và thông tin tối thiểu người dùng cần cung cấp.

Không quy lỗi skill cho lỗi thao tác agent hoặc transport trình duyệt. Không quy PASS từ static GET-back.

Một số response GET-back thêm field dẫn xuất, ví dụ Organization personnel criteria có thể có `field: "personnel"`. Nếu semantic config và runtime đúng, coi đó là server canonicalization; không PUT chỉ để xóa field response-only.
