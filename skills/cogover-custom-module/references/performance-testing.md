# Kiểm thử hiệu năng bằng sub-agent độc lập

Đọc khi Custom Module có một trong các trường hợp:

- Route, Custom Module Action, record trigger hoặc background job đọc/ghi nhiều record hay gọi nhiều capability.
- Record trigger before-change: có giới hạn thời gian, lỗi hoặc hết giờ thì chặn mọi thao tác ghi liên quan.
- Báo cáo, dashboard hoặc số liệu tổng hợp.
- Frontend tải hoặc hiển thị nhiều dữ liệu.

Module ngoài các trường hợp trên không cần sub-agent này; ngân sách vẫn được soát trong review backend và unit test khối lượng lớn ở bước 8. Contract nền tảng: [Giới hạn của một lần thực thi](cogover-sdk-api-reference.md#giới-hạn-của-một-lần-thực-thi), [Preview chính xác một version](custom-backend-module-api-reference.md#preview-chính-xác-một-version), [lần chạy job](custom-backend-module-api-reference.md#liệt-kê-hoặc-đọc-lần-chạy-job). Công cụ, lệnh và tên file bên dưới chỉ minh họa.

Fixture nhỏ của unit test và E2E không lộ vấn đề hiệu năng. Ngân sách thuộc từng lần thực thi và không hồi phục khi chạy lại, nên vượt ngân sách trên dữ liệu thật là lỗi chức năng, không chỉ là chậm.

## 1. Tính độc lập

- Agent chính giao một **sub-agent Hiệu năng**, khác sub-agent Backend và Frontend; có thể giao cùng sub-agent Review backend hoặc E2E nhưng báo cáo hiệu năng riêng. Agent chính không tự nhận vai đo. Không có công cụ sub-agent thì báo rõ yêu cầu đo hiệu năng độc lập chưa đáp ứng.
- Gói giao việc: ngưỡng đã chốt (mục 2), khối lượng dữ liệu lớn nhất dự kiến cho từng ca, version ID đang active, route/action/trigger/job/trang cần đo, phạm vi dữ liệu test được tạo hoặc ghi, lịch dùng chung dữ liệu với agent khác. Chỉ truyền cách truy cập credential an toàn.
- Sub-agent không sửa source ứng dụng, không commit, không publish/activate. Script đo đặt trong `e2e/` của repository tương ứng (ví dụ `e2e/perf/`) theo [Bố cục repository](cli-session-and-delivery.md#bố-cục-repository). Ca không đạt báo agent chính kèm số đo và vị trí nghi ngờ (lời gọi trong vòng lặp, đọc thừa field, quét record); agent chính giao sub-agent phụ trách sửa.

## 2. Ngưỡng

Ngưỡng nằm trong contract ở bước 1 mục 5 và được người dùng xác nhận cùng 1A. Người dùng chưa nêu ngưỡng thì đề xuất mặc định sau rồi xin xác nhận:

| Ca | Ngưỡng đề xuất với khối lượng lớn nhất dự kiến |
|---|---|
| Route, Custom Module Action, record trigger after-change | Mỗi loại ngân sách (capability call, lời gọi cục bộ, record đọc, record ghi) dùng không quá 70% `limit`; thời gian xử lý không quá 50% giới hạn thời gian của loại lần thực thi (`timeLimitMs` trong `limits.usage()`, `timeoutMs` của action) |
| Record trigger before-change | Lô lớn nhất dự kiến (tới 200 record) xong trong 50% `timeoutMs`; ca không cần kiểm tra thoát sớm, không đọc thêm |
| Background job | Mỗi lần thử dùng không quá 70% ngân sách job và 50% `timeoutMs`; tổng thời gian tới trang cuối phù hợp lịch chạy hoặc kỳ vọng nghiệp vụ |
| Báo cáo, dashboard | Thời gian chạy service `200` và thời gian hiển thị số liệu theo kỳ vọng người dùng nêu |
| Frontend | Thời gian tới khi nội dung chính hiển thị và số request API mỗi lần tải theo kỳ vọng người dùng nêu; không có request lặp cho cùng dữ liệu |

- Khối lượng lớn nhất dự kiến lấy từ yêu cầu, hoặc từ số record hiện có trên Workspace thật cộng dư địa tăng trưởng được người dùng xác nhận; không lấy kích thước fixture.
- Ca không có kỳ vọng từ người dùng (báo cáo, frontend): ghi số đo làm mốc trong bàn giao, không kết luận `FAIL` chỉ vì không có ngưỡng.

## 3. Dữ liệu và môi trường

- Đo trên Workspace test, trên version đã activate và đã PASS kiểm thử chức năng (Review backend, E2E). Code đổi sau khi đo thì đo lại ca liên quan.
- Dữ liệu đại diện: ưu tiên dữ liệu test có sẵn đủ khối lượng; thiếu thì tạo fixture có marker bằng `$object-record` trong phạm vi ghi người dùng đã đồng ý (Object, số record), ghi lại ID và dọn theo bước 9 mục 12 của skill. Workspace đang có người dùng thật: chỉ đo thao tác đọc trên dữ liệu hiện có, lời gọi tuần tự, sau khi người dùng đồng ý.
- Không chạy load test hay stress test: lời gọi tuần tự; chỉ chạy song song khi contract có yêu cầu đồng thời, và tối đa vài lời gọi. Gặp HTTP `429` thì dừng, ghi lại, không tăng tải.

## 4. Cách đo

- **Route:** preview service `6` với `showDebugData` trên đúng version (`READ_ONLY` khi route chỉ đọc; preview mặc định `READ_WRITE` ghi thật) để lấy `usage`, `operations` (chỉ ra lời gọi lặp hoặc lời gọi chạm giới hạn) và `durationMs`. Sau đó gọi production service `3` ít nhất 5 lần tuần tự, ghi riêng lần đầu sau activate, ghi trung vị và giá trị lớn nhất của thời gian phản hồi.
- **Custom Module Action:** chạy qua node Process hoặc tool AI Agent dùng thật, đọc `durationMs` trong output của node (`$action.<slug>.output`). Mức dùng ngân sách đo bằng cách chạy cùng logic trên local qua Dev CLI với dữ liệu đại diện (ngân sách của route), hoặc đọc `limits.usage()` mà handler ghi vào log nếu code có ghi.
- **Record trigger before-change:** trên local, chạy trigger runner với lô lớn nhất dưới Dev CLI áp ngân sách before-change. Trên Workspace, thực hiện thao tác ghi ở khối lượng lớn nhất dự kiến (import, cập nhật hàng loạt hoặc ghi từ Process), xác nhận không có `BEFORE_CHANGE_TRIGGER_FAILED` và ghi thời gian phản hồi so với cùng thao tác trên record không phải kiểm tra.
- **Record trigger after-change:** thời gian từ khi ghi tới khi đọc lại thấy hiệu ứng, không có lỗi ngân sách; việc dài phải đã chuyển sang job.
- **Background job:** `cogover-dev jobs run {RUN_ID}` đọc `durationMs` và `usage` của lần thử gần nhất (CLI từ `0.19.0`). Job chia trang: đo từng trang và tổng thời gian tới trang cuối.
- **Báo cáo:** thời gian chạy service `200` bằng phiên của persona với dữ liệu đại diện, theo mục [Kiểm thử](report-data-reuse.md#5-kiểm-thử) của Tận dụng báo cáo.
- **Frontend:** script trình duyệt (cùng runner E2E) mở trang sau khi tải lại cứng, đo thời gian tới khi nội dung chính hiển thị, đếm request API và request lặp; so kích thước file trong `dist/` với giới hạn upload (20 MiB mỗi file, 80 MiB tổng). Phiên test theo [Xác thực trình duyệt test](frontend-e2e-testing.md#3-xác-thực-trình-duyệt-test); không ghi HAR, theo quy tắc bảo vệ credential trong artifact.

## 5. Kết luận và vòng sửa

- Ca `PASS` khi mọi số đo nằm trong ngưỡng, `FAIL` khi vượt. Vượt ngân sách nền tảng hoặc hết giờ ở khối lượng dự kiến (`RateLimitError` có `details.budget`, `TIMEOUT`, `BEFORE_CHANGE_TRIGGER_FAILED`) là `FAIL` bất kể ngưỡng đã chốt.
- Tối đa **2 vòng sửa** cho mỗi đợt đo. Một vòng gồm:
  1. Sub-agent phụ trách sửa: giảm lời gọi, `fields` tối thiểu, `getMany` thay `get` trong vòng lặp, `records.aggregate` hoặc saved report thay quét record, chia trang sang job, bỏ request lặp ở frontend.
  2. Publish và activate version mới, xin người dùng xác nhận theo bước 9 mục 1 của skill.
  3. Sub-agent Review backend/E2E chạy lại các ca chức năng bị ảnh hưởng.
  4. Sub-agent Hiệu năng đo lại ca không đạt cùng ca liên quan.
- Hết 2 vòng vẫn còn `FAIL`: dừng sửa, báo người dùng số đo trước/sau từng vòng, nguyên nhân còn lại và phương án (chấp nhận ngưỡng mới, thu hẹp khối lượng hoặc phạm vi, đổi thiết kế lớn). Không tự nới ngưỡng, không báo hoàn tất. Còn ca vượt ngân sách nền tảng thì kết quả bàn giao là `FAIL` hoặc `PARTIAL` cho tới khi người dùng chọn phương án.

## 6. Báo cáo

Gồm: version ID đã đo; script và lệnh chạy trong `e2e/`; dữ liệu đại diện (Object, số record, marker, đã dọn hay chưa); bảng ca → khối lượng → ngưỡng → số đo (trung vị, lớn nhất, `usage` từng loại so với `limit`, `durationMs`) → nguồn số đo → `PASS`/`FAIL`; lời gọi lặp hoặc chạm giới hạn thấy trong `operations`; số đo trước/sau mỗi vòng sửa; ca chưa đo được và lý do.
