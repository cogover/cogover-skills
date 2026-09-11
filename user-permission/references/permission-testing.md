# Kiểm thử quyền runtime

Thực hiện sau khi cấu hình Role/rule đã được đọc lại và quyền hiệu lực đã được tính theo `SKILL.md`. Thao tác records qua `$object-record`; credential theo [$cogover-api-auth](../../cogover-api-auth/SKILL.md).

## 1. Chọn persona và credential kiểm thử

1. Lập danh sách persona từ yêu cầu: user có/không có Role, thuộc/không thuộc phòng ban, giữ vị trí khác nhau, record khớp/không khớp rule và các tổ hợp Role cần chứng minh quyền cộng dồn.
2. Cần từ hai persona trở lên hoặc rule phụ thuộc Role/phòng ban/vị trí → người dùng xác nhận: những user cụ thể nào dùng để test; người dùng cung cấp API key của từng user hay cho phép AI tạo key tạm; phạm vi Object/action sẽ test và việc tạo rồi xoá records test.
3. Không dùng API key của Super Admin hoặc user cấu hình thay cho user đích: chỉ kiểm thử được quyền của chủ key, không phải persona cần xác minh.
4. Người dùng không cung cấp key và không cho phép tạo key → dừng ở kiểm tra cấu hình; báo rõ quyền runtime chưa được xác minh end-to-end.

## 2. Resolve phòng ban, nhân sự và vị trí

Không dùng `$object-info`, `$object-record` hoặc các Object `department`, `personnel`, `department_personnel` để resolve dữ liệu tổ chức. Dùng API chuyên biệt theo [api-departments.md](api-departments.md), [api-positions.md](api-positions.md), [api-personnels.md](api-personnels.md):

1. Phòng ban: `POST /bapi/v1/departments/list` theo tên/ID/trạng thái; rule phụ thuộc phòng ban con → dùng `type: "tree"` hoặc truy vấn hierarchy để thấy quan hệ cha/con. Khớp chính xác tên, ưu tiên phòng ban active; nhiều kết quả cùng tên → không tự chọn, đối chiếu parent/hierarchy hoặc hỏi người dùng. Gọi `POST /bapi/v1/departments/view` với ID đã chọn trước khi dùng trong personnel filter.
2. Vị trí: `POST /bapi/v1/positions/list` (lọc được theo `department_ids`) rồi `POST /bapi/v1/positions/view` để xác nhận ID và trạng thái. Kiểm tra `is_department_only` và `department_ids`; không gán Position giới hạn theo phòng ban vào Department ngoài phạm vi của Position đó.
3. Nhân sự: `POST /bapi/v1/personnels/list` theo tên, ID, trạng thái, Role, phòng ban hoặc vị trí. API list không có filter email: thu hẹp bằng các filter được hỗ trợ rồi so khớp chính xác với mảng `emails` trong response, phân trang tiếp nếu cần. `POST /bapi/v1/personnels/view` để xác nhận Personnel và quan hệ Department/Position hiện tại; lấy relation ID, `department_id`, `position_id`, `is_primary`, `level` từ dữ liệu mới nhất khi cần cập nhật hoặc hoàn tác.
4. Đối chiếu Personnel với Users API bằng email/account hoặc quan hệ API trả về. Phân biệt workspace user ID, `account_id`, Personnel ID, Department ID, Position ID và relation ID; không hoán đổi các loại ID này.

## 3. Thiết lập phòng ban/vị trí cho nhân sự test

Chỉ khi rule cần kiểm thử phụ thuộc phòng ban/vị trí và persona hiện tại chưa có quan hệ phù hợp. Đây là thay đổi dữ liệu nhân sự, không phải phần ngầm định của việc tạo API key.

1. Xác nhận với người dùng: Personnel nào bị thay đổi, Department/Position đích, thay đổi tạm thời hay lâu dài. Không tự tạo Department, Position hoặc Personnel khi người dùng chỉ yêu cầu chuẩn bị persona test.
2. Trước khi ghi, gọi `personnels/view` và lưu snapshot đầy đủ các quan hệ cần bảo toàn: relation ID, Department, Position, `level`, `is_primary`.
3. Resolve Department và Position như mục 2; xác nhận cả hai đang dùng được và Position hợp lệ cho Department đích.
4. Dùng credential quản trị/kiểm soát gọi `POST /bapi/v1/personnels/departmentPosition`: quan hệ mới gửi `personnel_id`, `department_id`, `position_id`, `level`, `is_primary`, `deleted: false`; quan hệ hiện có gửi đúng relation `id`. Không suy đoán relation ID.
5. Gọi lại `personnels/view`; chỉ tiếp tục khi quan hệ đã lưu đúng, quan hệ chính không bị thay đổi ngoài ý muốn và persona khớp personnel filter của rule. Chỉ sau bước này mới tạo/dùng API key của nhân sự đó và kiểm thử records; không dùng cập nhật quan hệ chưa được xác minh làm căn cứ kết luận quyền.
6. Ghi lại mọi relation đã thêm/sửa và snapshot ban đầu để cleanup; thiết lập tạm phải có bước phục hồi quan hệ sau khi kiểm thử records hoàn tất.

## 4. Tạo API key tạm khi được phép

Chỉ sau khi người dùng cho phép rõ việc AI tạo API key cho danh sách user test; endpoint và payload theo [api-api-keys.md](api-api-keys.md).

1. `accountId` lấy từ `account_id` của active user; không dùng workspace user ID hoặc Personnel ID. Invited user chưa có account thì không tạo được key hợp lệ.
2. Tên duy nhất có tiền tố `codex-permission-test`, mô tả rõ user/Object/mục đích, `isActive: true`.
3. `expiresOn` không muộn hơn thời điểm hiện tại cộng `172800000` ms (48 giờ); không tạo key test không hết hạn.
4. Nhận credential đầy đủ đúng một lần từ `data.secretToken`; chỉ giữ trong bộ nhớ tiến trình cần cho test, không ghi vào repo, file, log, URL, báo cáo hoặc câu trả lời. Ghi riêng key ID, account ID, user, expiry và trạng thái cleanup, không ghi secret.
5. Xoá key tạm sau test bằng credential quản trị ban đầu; không để key tự xoá chính nó. Không cập nhật hoặc xoá API key do người dùng cung cấp.
6. Caller không có quyền quản lý API key → yêu cầu người dùng cung cấp key của persona hoặc chấp nhận chỉ audit cấu hình; không tìm cách mượn danh tính khác.

## 5. Ma trận kiểm thử quyền records

- Một hàng cho mỗi tổ hợp `user × Object × action × record/field`, ghi kết quả mong đợi và nguồn quyền Role/rule. Object có security rules: tối thiểu một record khớp và một record không khớp rule cho từng nhánh cần chứng minh.
- Slot giữ chỗ không chọn nhân sự: không có ca user được phép từ chính rule đó; kiểm thử từ chối trực tiếp và ghi ca backend được phép thành nhánh riêng. Chỉ tạo cặp record khớp/không khớp khi có điều kiện record cần phân biệt (ví dụ phạm vi của View rule); không tạo ca allow giả cho audience `personnelId: null`.
- Persona phụ thuộc Department/Position: không bắt đầu ma trận cho đến khi `personnels/view` xác nhận quan hệ cần thiết. Credential dùng với `$object-record` phải là API key của đúng account gắn với Personnel vừa xác minh, không phải credential quản trị đã thiết lập quan hệ.

Thực hiện bằng `$object-record` dưới credential của đúng user test:

1. **View/read:** lọc theo marker hoặc ID của fixture; record được phép xuất hiện, record bị cấm không xuất hiện/không đọc được. Với field security: field được phép có mặt, field bị cấm không bị lộ.
2. **Create:** tạo record test chỉ với các field được phép, rồi thử riêng một payload chứa field không được phép khi cần kiểm tra field-level create. Không kết luận chỉ từ HTTP response; đọc lại bằng credential kiểm soát để biết record/field có thực sự được lưu.
3. **Edit:** cập nhật một field được phép và một field bị cấm trong hai request tách biệt; đọc lại bằng credential kiểm soát để xác minh giá trị cuối cùng và không nhầm request bị từ chối toàn bộ với update một phần.
4. **Delete:** dùng record test chuyên biệt, không dùng record nghiệp vụ; xác minh cả trường hợp được phép và bị từ chối khi cần chứng minh hai nhánh; sau lần xoá bị từ chối, đọc lại để chắc record vẫn tồn tại.

Quy tắc chung:

- Dùng credential quản trị/kiểm soát để chuẩn bị và đọc lại fixtures khi persona không có quyền tương ứng. Mọi record test có marker duy nhất, ví dụ `codex-permission-test-{timestamp}-{random}`, trong một field tìm kiếm được đã được schema xác nhận. Theo dõi mọi ID được tạo, kể cả record xuất hiện do một thao tác lẽ ra bị từ chối nhưng lại thành công.
- Object do backend quản lý: credential quản trị/Super Admin cũng có thể bị rules chặn. Phối hợp sub-agent backend qua `$cogover-custom-module` dùng đường hệ thống đã được phép để tạo/đọc lại/dọn fixtures, với policy giới hạn đúng Object/action. Không dùng `$object-record` dưới key quản trị như một cách bypass. Đường hệ thống chưa sẵn sàng → ghi ca test còn chờ thay vì mở tạm quyền trực tiếp; chốt cách cleanup trước khi tạo fixture.
- Không thao tác trên record thật của người dùng. Lỗi HTTP không phải bằng chứng duy nhất cho deny và `r: 0` không phải bằng chứng duy nhất cho allow; luôn kiểm tra trạng thái record/field sau request.

## 6. Dọn dẹp bắt buộc

1. Dùng `$object-record` tìm lại toàn bộ records theo marker và hợp nhất với danh sách ID đã theo dõi. Object do backend quản lý không cho credential kiểm soát đọc đủ fixtures → phối hợp backend dùng đường hệ thống đã được phép cho bước tìm và các bước cleanup records bên dưới.
2. Trước khi xoá, liệt kê Object, ID và tên/marker rồi yêu cầu xác nhận theo quy tắc xoá của `$object-record`. Xác nhận kế hoạch test ban đầu không thay thế xác nhận xoá khi đã biết ID cụ thể.
3. Chỉ xoá fixtures của phiên test. Persona không có quyền delete → dùng credential quản trị/kiểm soát có quyền delete thực tế; cleanup không phải bước chứng minh quyền. Object do backend quản lý mà quản trị cũng bị chặn → backend xoá qua đường hệ thống đã được phép, giới hạn đúng ID/marker của phiên test; không tắt rule giữ chỗ hoặc thêm grant trực tiếp để cleanup.
4. Đọc lại theo marker và từng ID để xác minh không còn fixture; Object chặn cả View trực tiếp → kiểm tra qua đường hệ thống đã được phép. Xoá không thành công → báo chính xác Object/ID còn lại và nguyên nhân; không tuyên bố đã dọn sạch.
5. Sau khi cleanup records hoàn tất, phục hồi mọi quan hệ Department/Position đã thiết lập tạm: `personnels/departmentPosition` với `deleted: true` đúng relation ID đã thêm; khôi phục Position, `level`, `is_primary` hoặc quan hệ cũ theo snapshot khi chúng đã bị sửa. Gọi `personnels/view` để so sánh với snapshot ban đầu. Không xoá Department, Position hoặc Personnel chỉ để cleanup, trừ khi chính các entity đó được tạo riêng cho test theo yêu cầu rõ ràng. Phục hồi thất bại → báo Personnel ID, Department ID, Position ID, relation ID và sai khác còn lại.
6. Sau khi cleanup records và quan hệ tổ chức hoàn tất, xoá mọi API key tạm do AI tạo bằng credential quản trị và dùng API danh sách để xác minh key không còn. Xoá thất bại → cập nhật `isActive: false` với nguyên `expiresOn`, báo key ID/expiry và tiếp tục thu hồi sớm nhất có thể. Không xoá key do người dùng cung cấp.
7. Không để record test, thay đổi quan hệ tổ chức tạm hoặc key tạm bị bỏ quên khi test thất bại hay bị gián đoạn; ưu tiên cleanup trước khi kết thúc.

## 7. Báo cáo kết quả

1. Báo cấu hình đã lưu và phép tính quyền hiệu lực, tách riêng khỏi kết quả runtime.
2. Trình bày ma trận theo user/persona, Object, record/field, action, kỳ vọng, HTTP/`r`, trạng thái thực tế sau request và kết luận pass/fail.
3. Báo số records test đã tạo/xoá, kết quả kiểm tra marker sau cleanup, các quan hệ Department/Position đã thay đổi và trạng thái phục hồi, số API key tạm đã tạo/thu hồi cùng mọi ID còn tồn đọng. Không báo secret.
4. Khi lỗi, giữ HTTP status, `r`, `msg`, `meta` và `requestId` để chẩn đoán nhưng loại bỏ mọi credential.
