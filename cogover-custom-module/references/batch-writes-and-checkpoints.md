# Ghi hàng loạt, số thập phân và checkpoint

Đọc khi nghiệp vụ có preview/apply, ghi nhiều record, retry hoặc nhiều request đồng thời. Contract nền tảng: [SDK API reference](api-reference.md), các mục Project state, Distributed locks, Record API và errors. Đây là hướng dẫn thiết kế ứng dụng, không phải cam kết transaction của nền tảng.

## Số thập phân

- Đọc kiểu field, khả năng ghi, số chữ số thập phân và giới hạn từ metadata thật; không tự suy ra ý nghĩa một mã `round_rule` nếu tài liệu chưa định nghĩa.
- `fractional_length` không phải bằng chứng API tự làm tròn dữ liệu ghi: đã quan sát API giữ thêm chữ số ngoài độ chính xác hiển thị. Kiểm chứng bằng fixture và đọc lại; ứng dụng cần làm tròn thì công bố quy tắc nghiệp vụ cụ thể và áp dụng nhất quán ở backend trước khi ghi.
- Không kiểm tra số chữ số bằng phép so sánh chính xác như `Math.round(percent * 10000) === percent * 10000`: `0.07 * 10000` có thể thành `700.0000000000001`. Dùng kiểm tra biểu diễn decimal chuẩn hóa hoặc phép tính decimal/rational được môi trường hỗ trợ; quyết định rõ cách xử lý scientific notation.
- Kiểm thử phần trăm lẻ, phần trăm âm, biên min/max, số tại điểm nửa đơn vị làm tròn và tổng sau làm tròn từng dòng. Không cộng trực tiếp số thực rồi mặc định tổng bằng tổng các giá trị người dùng thấy.

## Preview và áp dụng một lần trong phạm vi job

1. Backend tạo snapshot có ID ổn định, chủ sở hữu lấy từ invocation, danh sách record, giá trị cũ/mới, dấu thời gian hoặc revision thực sự có và quy tắc tính. Validate lại quyền, số lượng, ID trùng và giới hạn giá trị; không tin snapshot hoặc danh tính gửi từ browser.
2. Project state có thể lưu job/checkpoint trong giới hạn 32 KiB mỗi giá trị. State tồn tại qua version mới nhưng không phải Object nghiệp vụ có sẵn quyền, báo cáo hay lịch sử record: tự kiểm tra quyền truy cập job; nghiệp vụ cần Object bền vững để báo cáo/quan hệ thì quay lại bước thiết kế schema và duyệt Excel.
3. Dùng `expectedVersion: 0` khi tạo mới và CAS version khi chuyển trạng thái. Lưu trạng thái đã nhận xử lý trước thao tác ghi đầu tiên; request lặp lại cùng job đọc trạng thái/kết quả, không tự bắt đầu lại phép tính.
4. Phạm vi lock bao phủ tài nguyên có thể xung đột, không chỉ mỗi job khi nhiều job cùng sửa record. Kiểm tra giới hạn số lock và lease theo SDK. `withLock` không tự renew: renew trước khi hết lease và dừng ghi nếu không còn giữ lease.
5. Đọc lại các record trước apply để từ chối preview cũ; ghi nhiều dòng thì kiểm tra lại từng dòng trước khi ghi. Ghi giá trị đích tuyệt đối đã duyệt, không nhân tiếp giá trị hiện tại khi retry.
6. Lưu checkpoint trước/sau mỗi side effect và đọc lại record. Phân biệt dòng đã xác minh thành công, chưa chạy, dữ liệu đã đổi và chưa rõ kết quả do lỗi ghi/read-back. Không biết request đã ghi hay chưa thì không tự retry ghi hoặc đánh dấu thành công.
7. UI hiển thị trạng thái toàn job và từng dòng, cho tra cứu lại bằng job ID sau refresh hoặc mất kết nối. Khóa nút khi pending chỉ hỗ trợ UX; backend vẫn phải kiểm soát request lặp.

CAS chỉ bảo vệ state; lock chỉ bảo vệ các execution tuân thủ cùng cơ chế trong phạm vi project; Record API và state không được gộp thành transaction. Đọc rồi ghi vẫn có khoảng đua với tác nhân khác; timestamp có độ phân giải hữu hạn không phải revision nguyên tử. Không tuyên bố chống mọi lost update hoặc exactly-once nếu đích không có conditional write/fencing tương ứng; người dùng yêu cầu bảo đảm mạnh hơn contract hỗ trợ thì báo giới hạn cụ thể.

## Khi local chạy được nhưng production dừng giữa chừng

Đã quan sát một luồng đọc/ghi/checkpoint tuần tự chạy được local nhưng production trả HTTP 400, mã nghiệp vụ 422 với thông báo `Script execution failed or exceeded its limits`, sau khi một phần record đã đổi. Thông báo này không phân biệt được lỗi script và vượt giới hạn thực thi; không suy đoán nguyên nhân gốc hoặc một con số timeout/quota chưa được tài liệu xác nhận.

1. Giữ job ID, version và response đã loại credential; đọc checkpoint và record thật trước mọi quyết định retry. Invocation lỗi không chứng minh các side effect đã rollback. Execution bị ngắt trước cleanup thì lock có thể còn hiệu lực tới lúc lease hết hạn; không đổi namespace hoặc nới quyền để lách lock đang giữ.
2. Giảm roundtrip khi contract hỗ trợ: đọc nhiều record bằng `records.list` với filter ID và đúng phân trang; dùng `records.batchUpdate` cho nhóm ghi thay vì đọc/ghi/checkpoint từng dòng không giới hạn. Giới hạn SDK 1–200 dòng mỗi batch không bảo đảm mọi batch hoàn tất trong một invocation; test kích thước thực tế của bài toán trên production.
3. Lưu CAS claim/checkpoint trước batch. Batch là best-effort: ánh xạ từng `results` bằng `referenceId` (index đầu vào dạng chuỗi), kiểm tra thành công từng dòng rồi batch read-back. Response HTTP thành công hoặc aggregate `success` không phải bằng chứng mọi giá trị đúng; không nhận được kết quả thì giữ trạng thái chưa xác minh, không tự gửi lại ghi.
4. Chia nhiều invocation thì lưu tiến độ bền vững và dùng cơ chế tiếp tục được hỗ trợ; không dựa vào timer trình duyệt cho công việc phải tự chạy. Nghiệp vụ nền/định kỳ cần quay lại bước Process. Chưa có cơ chế tiếp tục phù hợp thì báo phần chưa hoàn tất.
5. Publish bản sửa, xác nhận active version, chạy lại local và production cho apply/read-back, replay, concurrency, stale và browser. Chỉ ghi workaround thành công sau kiểm chứng; giữ sự cố version cũ trong báo cáo. Không thay đổi nghĩa atomicity hoặc exactly-once để che giới hạn nền tảng.

## Bằng chứng nghiệm thu

- Local và production: preview đúng phép tính; apply rồi đọc record thật; apply lặp cùng job không cộng dồn; hai request đồng thời cùng job không ghi trùng; sửa fixture sau preview rồi xác minh apply từ chối; tra cứu lại job sau refresh.
- Kiểm thử input ngoài phạm vi và quyền bằng fixture/caller được phép. Chỉ có một caller hoặc ít fixture thì báo giới hạn số lượng/danh tính đã test.
- Kiểm thử lỗi giữa chừng bằng dependency giả lập có kiểm soát nếu không có cách tạo lỗi thật an toàn; xác minh checkpoint và số lần gọi write khi replay. Ghi rõ đây là test mô phỏng; không gộp vào số ca production hoặc tuyên bố đã kiểm chứng lỗi hạ tầng thật.
- Ghi cả HTTP status và mã nghiệp vụ. Một response lock conflict có thể là hành vi đúng khi request khác đang chạy; phải đọc job và record sau đó để kết luận không ghi trùng.
