# Review và kiểm thử backend bằng sub-agent độc lập

Đọc khi Custom Backend Module có record trigger, background job, Custom Module Action `effect: "write"` hoặc route ghi dữ liệu. Contract nền tảng: [SDK API reference](cogover-sdk-api-reference.md), [Backend API Reference](custom-backend-module-api-reference.md); module ghi số liệu do backend khác duy trì: [Ghi số liệu do backend khác duy trì](batch-writes-and-checkpoints.md#ghi-số-liệu-do-backend-khác-duy-trì). Công cụ, lệnh và tên file bên dưới chỉ minh họa.

Unit test do sub-agent Backend tự viết theo cách hiểu của chính nó nên coverage cao vẫn có thể bỏ sót đường ghi, đua dữ liệu với backend khác hoặc thiếu cơ chế tự phục hồi; review đọc code và kiểm thử trên Workspace độc lập đã phát hiện lỗi như vậy trước khi chạy với dữ liệu thật.

## 1. Tính độc lập

- Agent chính giao một **sub-agent Review backend**, khác sub-agent Backend; agent chính không tự nhận vai này. Phần review code và phần kiểm thử trên Workspace có thể giao một hoặc hai sub-agent, đều khác sub-agent Backend. Không có công cụ sub-agent thì báo rõ yêu cầu review độc lập chưa đáp ứng.
- Gói giao việc: contract và tiêu chí nghiệm thu; thiết kế (bất biến, công thức, bảng trigger/job/route); kết quả khảo sát và spike nếu có; đường dẫn source và commit đã dựng version; version ID đang active; identity policy ở mức metadata; phạm vi dữ liệu test được ghi; lịch dùng chung dữ liệu với agent khác. Chỉ truyền cách truy cập credential an toàn.
- Sub-agent không sửa source, không commit, không publish/activate, không sửa identity policy. Lỗi báo agent chính kèm bằng chứng; agent chính giao sub-agent Backend sửa rồi giao review/kiểm thử lại phần sửa.

## 2. Review code

- Review đúng commit đã dựng version (working tree sạch). Chạy lại typecheck, `npm test` và lệnh coverage; ghi số test, coverage, và báo khi `npm test` không chạy test nghiệp vụ.
- Ghi phạm vi đã kiểm là đúng (công thức, idempotency key, thứ tự khoá, danh tính, field ghi), rồi bảng phát hiện: mức (Cao, Trung bình, Thấp, Thông tin), file:dòng, mô tả, kịch bản lỗi bằng số cụ thể, đề xuất sửa. Phát hiện phụ thuộc hành vi nền tảng chưa đo thì ghi `PLAUSIBLE` kèm cách đo.
- Điểm cần soát:
  - Mọi đường làm đổi giá trị được kiểm soát có trigger: record con làm đổi rollup/formula của record cha, xoá, chuyển trạng thái do Process hoặc backend của App chuẩn ghi (bước 1 mục 5 của skill).
  - Input đọc trước khi lấy khoá rồi dùng để ghi; trigger/job dựa vào rollup/formula vừa đổi; retry gặp bước ghi dở dang; after-change không chạy mà không có đối soát.
  - Before-change đọc tuần tự nhiều Object, không thoát sớm, có thể hết `timeoutMs` và chặn thao tác ghi (fail-closed).
  - Policy rộng hơn thao tác code thực sự làm; ngân sách lần thực thi với khối lượng lớn nhất dự kiến; test còn thiếu cho các ca trên.

## 3. Kiểm thử end-to-end trên Workspace

- Chạy sau khi version cần kiểm thử đã activate, trên dữ liệu test có marker, bằng script chạy lại được với log máy đọc được và file lưu ID record đã tạo. Dữ liệu test theo [Dữ liệu kiểm thử](../../object-record/SKILL.md#dữ-liệu-kiểm-thử) của `$object-record`; snapshot record tổng hợp bị ảnh hưởng trước, giữa và sau.
- Đi luồng như người dùng và hệ thống thật: đổi trạng thái giống thao tác trên giao diện, để Process và backend của App chuẩn chạy thật, submit User Task bằng phiên của người thực hiện. After-change và job: đọc lại sau vài giây, ghi run/job ID cùng giá trị đọc lại.
- Mỗi tiêu chí nghiệm thu có ca thường và ca biên (đúng bằng giới hạn, vượt một đơn vị). Thêm:
  - Chạy lặp: gọi lại cùng route hoặc enqueue lại cùng job, số liệu không đổi lần hai.
  - Đồng thời: nhiều lời gọi song song cùng lúc với trigger, delta chỉ áp một lần.
  - Mọi nguồn ghi (giao diện, API, Process, backend của App chuẩn) không sinh `BEFORE_CHANGE_TRIGGER_FAILED`; số run `FAILED` bằng 0.
  - Route chỉ dành cho Super Admin/role trả `403` với persona không có quyền.
  - Ca bị transition rule hoặc khoá field chặn ghi `BLOCKED`, kèm mã lỗi và cách kiểm chứng gián tiếp.
- Không sửa tay số liệu do module hoặc backend khác duy trì, không xoá record. Ca cần sửa tay để tiếp tục thì dừng và báo agent chính. Ca làm lệch số được đưa về bằng chính đường ghi nghiệp vụ (sửa lại record nguồn) và ghi lại.
- Dọn dẹp và báo phần dư theo bước 9 mục 11 của skill.

## 4. Báo cáo

Gồm: commit/version đã review và kiểm thử; kết quả lệnh; bảng phát hiện; bảng tiêu chí (bước, kỳ vọng, thực tế, run ID, `PASS`/`FAIL`/`BLOCKED`); snapshot record tổng hợp; dọn dẹp và phần dư không hoàn tác; giới hạn (ca chưa thử, đường ghi chưa thử trực tiếp). Sau mỗi version sửa lỗi, thêm mục retest với ca lỗi và ca hồi quy.
