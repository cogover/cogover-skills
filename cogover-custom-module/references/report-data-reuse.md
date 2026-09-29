# Tận dụng báo cáo cho số liệu tổng hợp

Đọc khi yêu cầu có báo cáo, dashboard, KPI, thống kê hoặc bảng tổng hợp (đếm, tổng, trung bình, min/max, trung vị theo nhóm hoặc theo kỳ) lấy từ một hoặc nhiều Object, kể cả khi số liệu hiển thị trong frontend tùy chỉnh hoặc backend cần số liệu để quyết định. Hai nguồn số liệu không quét record: `records.aggregate` của `@cogover/sdk` trong backend và saved report của `$report-builder`; chọn theo [`records.aggregate` hay saved report](#recordsaggregate-hay-saved-report). Contract báo cáo: [$report-builder](../../report-builder/SKILL.md), gồm [Public Report API contract](../../report-builder/references/api-contract.md) (có mục gọi bằng phiên Web App) và [Saved report settings](../../report-builder/references/report-settings.md). ID, slug và payload bên dưới chỉ minh họa.

## 1. Nguyên tắc

- Backend đọc record theo trang (tối đa 200 record mỗi lượt), mỗi lượt tốn thời gian, một capability call và số record đọc trong ngân sách của lần thực thi (mặc định HTTP route 100 capability call, 10.000 record đọc; background job 1.000 và 50.000; xem [Giới hạn của một lần thực thi](cogover-sdk-api-reference.md#giới-hạn-của-một-lần-thực-thi)). Với Object từ vài trăm record trở lên, tổng hợp bằng cách quét record chậm, dễ vượt thời gian chờ và ngân sách; vượt ngân sách ném `RateLimitError` có `details.budget`, chờ hay retry không giúp. `records.aggregate` và báo cáo Cogover đều tính group/aggregate phía nền tảng và trả kết quả đã tổng hợp.
- Mỗi chỉ số tổng hợp phải được xếp vào một trong hai nguồn trên trước khi code: số liệu đơn giản trên một Object mà backend tính theo điều kiện của lời gọi thì dùng `records.aggregate`; còn lại kiểm tra bằng `$report-builder`, báo cáo tính được thì agent đọc `$report-builder` để xây (hoặc tái sử dụng) báo cáo và phân quyền hợp lý, rồi module đọc kết quả báo cáo thay vì quét record. Chỉ quét record khi cả hai không biểu diễn được, kèm lý do cụ thể.
- Module đọc báo cáo **bằng phiên của người dùng cuối đang dùng module**: báo cáo chạy dưới danh tính người gọi, không cần API key hay credential riêng.
- Chỉ cần xem bảng/biểu đồ chuẩn từ saved report: đề xuất dashboard chuẩn qua [$dashboard-builder](../../dashboard-builder/SKILL.md) hoặc mục menu tới `/reports/{reportSlug}` thay vì frontend tùy chỉnh (bước 1 mục 4: chức năng chuẩn đáp ứng trọn vẹn thì không tạo project).
- Không áp dụng cho: logic cần từng record để ghi hoặc điều chỉnh (trigger, ghi hàng loạt), tra vài record theo ID, quy tắc phải dựa trên dữ liệu mới nhất tại thời điểm ghi.

### `records.aggregate` hay saved report

`@cogover/sdk` từ `0.13.0` có `records.aggregate`: backend (route, trigger, job) đếm, tính tổng, trung bình, min/max các record khớp `where` của một Object trong một capability call, không đọc record. Lời gọi chạy dưới danh tính của client đang dùng (người gọi, `data.asUser()`, `data.asSystem()`): chỉ tính record danh tính đó được thấy. Với `data.asUser()` hoặc `data.asSystem()`, mọi field trong `where`, `groupBy` và metric (trừ `"id"`) còn phải được identity policy cho phép; qua `data.object()` không cần policy. Đủ phép tính và `groupBy` chỉ có với người gọi HTTP route hoặc `data.asSystem()`. `data.asUser()`, và `data.object()` khi lần chạy đọc dưới danh tính người dùng khác người gọi HTTP (record trigger cho thay đổi do người dùng, job có người dùng, Development Session của `cogover-dev run`), không group được và chỉ có `count` trên `"id"`, `count`/`sum`/`avg`/`min`/`max` trên field số; metric khác hoặc `groupBy` ném `ValidationError`. Contract đầy đủ: mục [Aggregate](cogover-sdk-api-reference.md#aggregate) của SDK API reference.

| Tiêu chí | `records.aggregate` | Saved report của `$report-builder` |
|---|---|---|
| Object | Một Object | 1–5 Object, relation, join Inner/Left |
| Điều kiện | `where` như `records.list`, dựng động trong script từ request, người gọi, record đang xử lý | Filter nền cấu hình sẵn, tham số người dùng chọn thêm vào `filters` đã xác nhận |
| Phép tính | `count` (`"id"` là số record, field khác là số record có giá trị; nhận field số, ngày, lựa chọn, `boolean`, `lookup_normal`, text, `email`, `phone`, `auto_number`, không nhận `reference`, `file`, `url`, `formula`, `rollup_summary`), `countDistinct` (cùng loại field, xấp xỉ khi tập lớn), `sum`/`avg` field `numeric`, `decimal`, `currency`, `percent`, `min`/`max` field số hoặc `date`/`date_time`; 1–20 metric mỗi lời gọi; không record khớp thì `count`/`sum` là `0`, `avg`/`min`/`max` là `null`; danh tính người dùng ủy quyền chỉ có `count` trên `"id"` và metric trên field số | Thêm `median`, row formula, summary formula |
| Nhóm | `groupBy` 1–3 field kiểu choice (`single_choice`, `multi_choices`, `radio_button`, `checkbox`), `boolean`, `lookup_normal`, `date`/`date_time`, số; không nhận text hay `reference`. Key là giá trị thô (lookup → record ID, choice → option slug, ngày → epoch ms; không gom theo tuần/tháng/quý), record không có giá trị ở field nhóm không thuộc nhóm nào, nhóm nhiều record nhất trước; `limit` 1–5.000 nhóm (mặc định 1.000), `truncated: true` khi bị cắt; chỉ với người gọi HTTP route hoặc `data.asSystem()` | Tối đa 2 group hàng và 2 group cột, group thời gian `date`, `week`, `month`, `quarter`, `year`, sort, top-N, tối đa 10.000 dòng |
| Ai cấu hình, dùng lại | Code module; người dùng không sửa được, không dùng cho dashboard | Người dùng/quản trị viên cấu hình, chia sẻ bằng ACL, dùng lại cho dashboard và báo cáo chuẩn |
| Nơi gọi | Backend, dưới danh tính của lời gọi, nên dùng được làm căn cứ quyết định cần bảo vệ; trong trigger/job chạy dưới danh tính người dùng, nhóm hoặc metric ngoài giới hạn trên phải qua `data.asSystem()` | Frontend bằng phiên người dùng cuối; backend chưa gọi được bằng phiên đó (mục [Giới hạn](#giới-hạn-khi-backend-cần-số-liệu-báo-cáo)) |

- Dùng `records.aggregate` khi chỉ số nằm trên một Object, là đếm/tổng/trung bình/min/max theo điều kiện động của script, không quá 5.000 nhóm và chấp nhận dữ liệu trễ khoảng 1 giây. Ví dụ: tổng giá trị đơn chưa thanh toán của khách hàng trên đơn đang tạo để kiểm hạn mức, số ticket đang mở của người gọi theo trạng thái, doanh thu theo nhân viên phụ trách trong khoảng ngày của request. Thay cho quét record hoặc gọi saved report từ backend. Ví dụ đầu chạy trong trigger before-change cho thay đổi do người dùng: `sum` trên field tiền tệ, không `groupBy`, nên dùng được với danh tính mặc định; hai ví dụ sau cần `groupBy` nên chạy trong HTTP route bằng người gọi, hoặc qua `data.asSystem()` trong trigger/job.
- Dùng saved report khi cần nhiều Object hoặc join, nhóm theo kỳ hoặc theo field text/`reference`, `median` hay formula báo cáo, bảng lớn, hoặc số liệu là báo cáo/dashboard người dùng muốn tự cấu hình, chia sẻ, phân quyền và xem lại; chỉ cần bảng/biểu đồ chuẩn thì dùng dashboard.
- Dữ liệu của `records.aggregate` đọc từ chỉ mục tìm kiếm, trễ khoảng 1 giây sau khi ghi: record vừa ghi có thể chưa được tính, trigger before-change không thấy thay đổi đang ghi, `countDistinct` là xấp xỉ. Không dùng cho quy tắc cần chính xác tuyệt đối tại thời điểm ghi (tồn kho, số thứ tự, chống trùng); chống trùng dùng field unique. Gọi trong before-change được nhưng thao tác ghi của người dùng phải chờ: giữ ít lời gọi.
- Cần số liệu theo tháng/quý từ `records.aggregate`: mỗi kỳ một lời gọi với `where` theo khoảng ngày (mỗi lời gọi là một capability call trong ngân sách của lần thực thi, mặc định route 100, trigger before-change 20); nhiều kỳ hoặc hiển thị lâu dài thì dùng saved report.

## 2. Kiểm tra khả năng bằng `$report-builder`

Sub-agent khảo sát làm ở bước 1, chỉ đọc. Chỉ số thuộc phạm vi `records.aggregate` theo mục 1 thì ghi kết luận đó (Object, `where`, `groupBy`, metric, danh tính gọi) và không cần báo cáo. Các chỉ số còn lại: liệt kê Report Type (service `215`) và saved report (service `220`, detail `229`) liên quan để tái sử dụng, rồi đối chiếu từng chỉ số với giới hạn của báo cáo:

| Khía cạnh | Báo cáo hỗ trợ | Không hỗ trợ hoặc cần xác minh |
|---|---|---|
| Object | 1–5 Object, tối đa 4 relation liên thông từ primary object, join Inner/Left | Hơn 5 Object, graph không liên thông, dữ liệu ngoài Cogover |
| Nhóm | Tối đa 2 field group hàng và 2 field group cột; group thời gian `date`, `week`, `month`, `quarter`, `year` | Nhóm theo giá trị tính từ logic tuỳ ý |
| Phép tính | `sum`, `avg`, `count`, `max`, `min`, `median`; row formula, summary formula | Distinct count: quan hệ một-nhiều làm trùng mẫu số, tỷ lệ conversion không chính xác |
| Lọc, sắp xếp | Filter AND/OR/logic tuỳ chỉnh, sort, top-N (`rows_limit`) | Operator/`params` chưa được contract hoặc response thực tế xác nhận |
| Kích thước | Tối đa 10.000 dòng mỗi lần chạy service `200` | Cần kéo toàn bộ dữ liệu chi tiết lớn về giao diện |

Kết luận cho từng chỉ số, đưa vào bảng ở bước 1 mục 4:

1. Saved report có sẵn đáp ứng: ghi ID/slug, Report Type, field dùng và ACL hiện tại.
2. Tạo được saved report mới (tái sử dụng hoặc tạo Report Type): ghi primary object, relation, group, aggregate, filter nền dự kiến.
3. Báo cáo đáp ứng một phần: phần báo cáo tính được lấy từ báo cáo, phần còn lại module xử lý nhẹ trên kết quả đã tổng hợp (ghép hai báo cáo, tính tỷ lệ từ tử số/mẫu số đã tổng hợp).
4. Không làm được bằng báo cáo: phần nằm trên một Object và thuộc phạm vi `records.aggregate` thì backend tính bằng `records.aggregate`; còn lại nêu lý do cụ thể theo bảng trên và mục 1, rồi mới thiết kế quét record có background job hoặc Object tổng hợp.

Nguồn số liệu từng chỉ số, báo cáo sẽ tạo và đối tượng được xem báo cáo nằm trong đề xuất 1A. Tạo báo cáo là thao tác ghi trên Workspace: chỉ làm sau khi người dùng xác nhận.

## 3. Xây báo cáo và phân quyền (bước 2B)

Giao sub-agent Báo cáo đọc bản hiện tại của `$report-builder` và làm theo đúng workflow của skill đó: report contract, graph, Report Type, report field, saved report, chạy service `200` và kiểm tra với ví dụ nghiệm thu.

1. Chạy sau khi schema liên quan đã ghi và đọc lại ở bước 2, vì report field tham chiếu field thật. Tái sử dụng saved report khi cùng Report Type, field, group, aggregate và filter; không sửa saved report đang dùng chung theo cách làm đổi kết quả của người khác, cần cấu hình khác thì tạo mới.
2. Slug ổn định, mô tả nêu module sử dụng.
3. **Phân quyền báo cáo theo đối tượng dùng module**, đặt ACL trên Report Type và saved report theo mục ACL của [Public Report API contract](../../report-builder/references/api-contract.md#validation-và-semantics-đặc-biệt):
   - Người dùng module: quyền xem/chạy (`VIEW`, thêm `EXECUTE` khi Workspace yêu cầu để chạy), gán theo `role`, `department` hoặc `position` khớp đối tượng người dùng trong contract; chỉ dùng `personnel` cho danh sách cố định nhỏ.
   - Sửa/xoá (`EDIT`, `ADD`, `DELETE`): chỉ người phụ trách cấu hình báo cáo.
   - Không dùng `option: 1` (tất cả) trừ khi mọi user đều là đối tượng của module; không cấp rộng chỉ để test pass. ACL chưa rõ thì hỏi người dùng trước khi ghi.
4. Quyền dữ liệu nguồn: người dùng module phải có quyền View Object/field nguồn theo Role và security rules hiện có. Thiếu quyền thì phối hợp sub-agent Security và `$user-permission` xử lý đúng delta được duyệt, không mở rộng quyền Object chỉ để báo cáo có số liệu.
5. Chạy service `200` bằng phiên của persona đại diện (tối thiểu một người trong ACL có phạm vi record hẹp và một người ngoài ACL, theo [Kiểm thử quyền runtime](../../user-permission/references/permission-testing.md)): ghi lại người trong ACL nhận đúng số liệu trong phạm vi quyền của họ, người ngoài ACL bị từ chối. Service `200` nhận Report Type ID, nên phải chứng minh bằng thực nghiệm ACL nào và quyền record nào được áp khi chạy; kết quả không như thiết kế thì báo agent chính trước khi module dựa vào báo cáo để giới hạn dữ liệu.
6. Đo thời gian chạy với dữ liệu đại diện; lưu payload đã chạy thành công và một mẫu response đã redact làm fixture cho parser của module. Response không cố định schema: parser viết theo mẫu thực tế, không đoán path.
7. Bàn giao cho agent chính: Report Type ID, saved report ID/slug, mapping object field → report field ID, ACL đã đặt, payload service `200`, mẫu response, thời gian chạy, kết quả chạy theo persona, hai link theo mục Trả kết quả của `$report-builder`. Báo cáo không đáp ứng như đánh giá ở bước 1 thì chốt lại nguồn số liệu với người dùng trước khi chuyển sang quét record.

## 4. Module đọc dữ liệu báo cáo

### Gọi báo cáo bằng phiên người dùng cuối

Frontend chạy cùng origin với Workspace nên gọi Report API bằng phiên Web App của người đang đăng nhập:

```http
POST /api/v1/report
Content-Type: application/json
x-req-type: 9
x-req-service: 200
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
```

- Body là chính `payload` của service `200` (không bọc `{service, payload}` như `/bapi/v1/report`), thêm `"setting": true` để chạy đồng bộ. Thiếu cờ này, service `200` trả `r: 32` (`Wait for response`) kèm `data.id` và kết quả không nằm trong response.
- Response là `{ r, msg, data }` ở root, không bọc envelope. Lỗi nghiệp vụ vẫn trả HTTP `200` với `r != 0` (ví dụ `r: 404` Report Type không tồn tại): luôn kiểm tra `r`. Chạy thành công trả `data` gồm `rows`, `summary` và `total`. Không dùng `/api/v1/report-server` hoặc `x-req-type: 6`: kết quả bị bọc trong `{ serviceVersion, service, id, type, body }`.
- Payload: dựng từ saved setting theo [Chuyển setting thành service 200](../../report-builder/references/report-settings.md#chuyển-setting-thành-service-200) một lần ở bước 2B, lưu thành hằng số; `preview: false`, `size` nhỏ nhất đủ dùng (tối đa `10000`). Nhiều chỉ số cùng Report Type thì gom vào một lần chạy (group và nhiều aggregate).
- Tham số do người dùng chọn (kỳ thời gian, giá trị lọc trong danh sách cho phép) chỉ thêm vào `filters` với operator/`params` đã được `$report-builder` xác nhận ở bước 2B. Dữ liệu người dùng được thấy do quyền của chính họ quyết định; bộ lọc trên giao diện chỉ là tiện ích, không phải ranh giới bảo mật.
- Để báo cáo group/aggregate phía nền tảng; giao diện chỉ biến đổi nhẹ kết quả đã tổng hợp (đổi nhãn, tính tỷ lệ, sắp xếp, ghép hai báo cáo). Không kéo hàng nghìn dòng chi tiết về trình duyệt để tự cộng.
- Lỗi: `r != 0` hiển thị trạng thái lỗi kèm nút thử lại; phiên hết hạn hoặc lỗi định tuyến trả HTTP `401` kèm header `x-proxy-error: 1` thì yêu cầu đăng nhập lại; lỗi quyền hiển thị thông báo không có quyền xem báo cáo, không hiển thị số liệu cũ trong cache của người khác.
- Không đưa API key, cookie hay token vào code; trình duyệt tự gửi cookie phiên.

Frontend theo `custom-frontend-module-template` (custom component, Federation Page) gọi qua HTTP client chung với `x-req-type: 9`, theo quy ước của `.agents/skills/custom-module-api` trong bản đã clone. Template chỉ có hằng số `REQUEST_TYPE.TS_PROJECT` mang giá trị `9`; dùng hằng số này cho Report, không dùng `REQUEST_TYPE.REVERSE_PROXY` (`6`), và khai báo response bằng `SuccessResponse` vì kết quả không bọc `body`:

```tsx
// src/apis/report/report.api.ts
import http, { SuccessResponse } from '../apiBase';
import { createServiceHeader, REQUEST_TYPE } from 'src/utils/apiUtils';
import { ReportRunPayload, ReportRunResult } from './report.type';

const URI = '/api/v1/report';

export const reportApi = {
    run(payload: ReportRunPayload) {
        return http.post<SuccessResponse<ReportRunResult>>(URI, { ...payload, setting: true }, {
            // x-req-type 9: kết quả { r, msg, data } ở root, không bọc body.
            headers: createServiceHeader({ service: 200, type: REQUEST_TYPE.TS_PROJECT }),
            // Client chung mặc định chờ 10 giây; tăng theo thời gian đo ở bước 2B khi cần.
        });
    },
};

// Trong queryFn của TanStack Query:
// const result = (await reportApi.run(MONTHLY_SALES)).data;
// if (result.r !== 0) throw new Error(result.msg);
// return toSalesSummary(result.data); // Hàm thuần, viết theo mẫu response đã redact ở bước 2B.
```

Single page app tự chọn stack gọi `fetch('/api/v1/report', { method: 'POST', credentials: 'same-origin', ... })` với cùng header, lấy giá trị `XSRF-TOKEN` từ cookie đặt vào hai header CSRF theo [Full-stack integration](full-stack-integration.md#production).

Tách hàm biến đổi kết quả (`toSalesSummary`) thành hàm thuần, unit test bằng mẫu response đã redact: có dữ liệu, rỗng, `r != 0`, `r: 32`, thiếu field.

### Chọn nơi gọi theo loại module

| Loại module | Nơi gọi báo cáo |
|---|---|
| Chỉ frontend | Frontend gọi `/api/v1/report` bằng phiên người dùng cuối, tổng hợp nhẹ và hiển thị giao diện mong muốn; không cần backend. |
| Frontend và backend, số liệu chỉ để hiển thị hoặc để người dùng tự quyết định | Frontend gọi báo cáo trực tiếp như trên; backend chỉ xử lý phần nghiệp vụ khác. |
| Frontend và backend, backend cần số liệu tổng hợp để ra quyết định (duyệt, tính giá, chặn thao tác) | Số liệu thuộc phạm vi `records.aggregate`: backend tự tính bằng `records.aggregate` dưới danh tính người gọi. Cần saved report: xem mục dưới, backend chưa gọi được báo cáo bằng phiên người dùng cuối. |

### Giới hạn khi backend cần số liệu báo cáo

- Backend không nhận được phiên của người dùng cuối: script không thấy header `authorization`/`cookie` của request, `fetch` của SDK không gửi cookie và từ chối header dành riêng cho Cogover, `@cogover/sdk` chưa có API chạy saved report dưới danh tính người gọi. Không chuyển `AuthToken`, `HttpSessionId` hay cookie từ frontend sang backend để giả phiên.
- Số liệu frontend gửi lên là dữ liệu do client cung cấp: backend không dùng làm căn cứ cho quyết định cần bảo vệ. Khi quyết định phụ thuộc số liệu tổng hợp, trước hết xét `records.aggregate` (SDK từ `0.13.0`, mục 1): số liệu trên một Object thì backend tự tính dưới danh tính người gọi, không cần các phương án dưới. Số liệu cần saved report (nhiều Object, nhóm theo kỳ, formula):
  1. Ưu tiên thu hẹp để backend tự đọc đúng tập record cần thiết bằng quyền của người gọi (lọc chặt, vài trang), khi tập đó nhỏ.
  2. Số liệu cần dùng lặp lại: background job duy trì Object tổng hợp hoặc project state (danh tính system, policy giới hạn), backend đọc lại.
  3. Chỉ khi người dùng chấp nhận số liệu ở danh tính hệ thống thay vì quyền người gọi: backend chạy báo cáo qua `POST https://{WORKSPACE_DOMAIN}/bapi/v1/report` bằng `fetch({ credential })` với credential BEARER (bước 6A) chứa API key của một tài khoản tích hợp quyền tối thiểu; route tự kiểm tra người gọi, cố định Report Type/field/filter, lọc theo phạm vi người gọi lấy từ `invocation`/`org`, gửi `setting: true`, xử lý `r != 0` và `429`. Development Session mặc định chặn credential (`FETCH_BLOCKED`), trigger before-change không `fetch` được, và `fetch` tới chính hostname Workspace phải được chứng minh trên version đã publish trước khi dựa vào.
- Nêu rõ giới hạn này trong đề xuất 1A khi nghiệp vụ rơi vào dòng cuối của bảng, để người dùng chọn phương án.

## 5. Kiểm thử

- Local: unit test hàm biến đổi và parser bằng fixture; frontend single page app chạy local không có phiên Workspace nên dùng fixture hoặc chặn request. `records.aggregate`: tách hàm dựng `where`/metric và hàm xử lý kết quả thành hàm thuần, unit test cả nhóm rỗng, metric `null` (không record nào có giá trị) và `truncated: true`; chạy thật qua `cogover-dev run` với dữ liệu test. Development Session đọc dưới danh tính người dùng của Project key nên `groupBy` và metric ngoài `count` trên `"id"`/field số bị từ chối trên local: kiểm thử phần đó trên version đã publish.
- `records.aggregate` trên Workspace: đối chiếu với số đếm/tổng tính tay trên tập record test nhỏ (chờ vài giây sau khi ghi fixture vì dữ liệu trễ khoảng 1 giây), chạy bằng caller có phạm vi record hẹp để xác nhận chỉ record họ thấy được tính.
- Workspace (bước 9): chạy module bằng phiên của từng persona đã dùng ở bước 2B. Số liệu hiển thị khớp service `200` chạy trực tiếp cùng tham số bằng cùng phiên đó; người ngoài ACL thấy trạng thái không có quyền; người có phạm vi record hẹp chỉ thấy số liệu của phạm vi đó; đo thời gian tải với dữ liệu đại diện. Không kết luận bằng phiên Super Admin.
- E2E: các ca trên nằm trong bộ E2E của sub-agent E2E theo [Kiểm thử E2E frontend](frontend-e2e-testing.md).
- Bàn giao: saved report (ID, slug, link), Report Type, ACL đã đặt, payload đang dùng, nơi gọi (frontend hay backend) và lý do, kết quả theo persona, thời gian tải đo được, chỉ số tính bằng `records.aggregate` (route/trigger/job, Object, metric, danh tính gọi), chỉ số vẫn quét record kèm lý do; nếu dùng credential tài khoản tích hợp thì kèm tên credential, host và tài khoản, không kèm giá trị.
