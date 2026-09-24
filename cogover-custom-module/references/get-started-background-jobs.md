# Bắt đầu với background job

Tạo một job lưu lời nhắn, chạy trên Cogover và đọc lại kết quả. Sau đó, thử cơ chế retry và chạy theo lịch. Ví dụ dùng Project state nên bạn không cần tạo Object hay kết nối dịch vụ bên ngoài.

## Chuẩn bị

- Cài Node.js 20 trở lên và Git.
- Có Workspace đã bật background job và tài khoản được phép tạo Project, publish, activate và quản lý job.
- Có Workspace API key để dùng CLI. Project key chỉ cần cho phần phát triển local ở cuối bài; đây là hai loại khóa khác nhau.

Nếu chưa quen việc tạo Project, xem [Bắt đầu với Custom Backend Module](get-started-custom-backend-module.md).

## 1. Tạo Project

Trong Cogover, mở **Custom Backend Module**, tạo Project tên `Job demo` với slug `job_demo`. Sao chép Project ID.

Mở terminal và chạy:

```bash
git clone https://github.com/cogover/custom-backend-module-starter-project.git job-demo
cd job-demo
npm install --global @cogover/dev-cli@latest
npm install
npm install @cogover/sdk@latest
cogover-dev --version
npm ls @cogover/sdk
cp cogover.example.json cogover.json
```

Dùng CLI từ 0.13.1 và SDK từ 0.8.0. Sửa `cogover.json`, thay các phần trong ngoặc nhọn bằng hostname của Workspace (ví dụ `example.cogover.net`) và Project ID:

```json
{
  "version": 1,
  "runtimeUrl": "https://{WORKSPACE_DOMAIN}",
  "projectId": "{PROJECT_ID}",
  "projectSlug": "job_demo"
}
```

Tạo file `.env` trong cùng thư mục, thay phần trong ngoặc nhọn bằng Workspace API key của bạn:

```dotenv
COGOVER_API_KEY={WORKSPACE_API_KEY}
```

CLI đọc file này khi publish và chạy các lệnh quản lý job. Không đưa `.env` vào Git; starter đã có cấu hình bỏ qua file này.

Chạy các lệnh còn lại trong thư mục này.

## 2. Viết job và route

Tạo file `src/main.ts` với nội dung sau:

```typescript
import { createRouter, defineJob, RetryableError } from "@cogover/sdk";

const helloJob = defineJob({
  key: "hello_job",
  timeoutMs: 10_000,
  maxAttempts: 3,
}, async ({ job, payload, state, log }) => {
  if (payload !== null && (typeof payload !== "object" || Array.isArray(payload))) {
    throw new Error("Payload must be an object");
  }
  const input = (payload ?? {}) as Record<string, unknown>;
  const message = input.message ?? "Hello from a background job";
  if (typeof message !== "string") throw new Error("message must be a string");

  // Fail the first attempt only, so the retry can be observed.
  if (input.simulateFailure === true && job.attempt === 1) {
    throw new RetryableError("Temporary failure for this demo");
  }

  await state.namespace("job_results").set(job.id, {
    message,
    attempt: job.attempt,
  }, { ttlSeconds: 3600 });
  log.info("Job completed", { runId: job.id, attempt: job.attempt });
});

export const jobs = [helloJob];

const router = createRouter();
router.post("/hello", async ({ request, jobs, response }) => {
  const result = await jobs.enqueue("hello_job", request.body);
  return response.json(result, { status: 202 });
});
router.get("/results/:runId", async ({ request, state }) => {
  const result = await state.namespace("job_results").get(request.params.runId ?? "");
  return { result: result?.value ?? null };
});

export default router.toHandler();
```

`hello_job` lưu kết quả trong một giờ, dùng run ID làm khóa. Route POST đưa một lần chạy vào hàng đợi và trả ID ngay; route GET đọc kết quả đã lưu. Named export `jobs` giúp Cogover nhận diện job khi bạn publish.

## 3. Publish và activate

```bash
npm run build
cogover-dev publish
```

Chờ CLI báo version đã `READY`, rồi activate bằng version ID vừa được in ra:

```bash
cogover-dev activate {VERSION_ID}
```

Lúc này job mới có thể chạy. Publish chưa tự activate version. Ví dụ chỉ dùng state và log nên không cần identity policy để truy cập record.

## 4. Chạy job và đọc kết quả

Tạo file payload rồi đưa job vào hàng đợi:

```bash
printf '%s\n' '{"message":"My first background job"}' > payload.json
cogover-dev jobs enqueue hello_job --payload-file payload.json --idempotency-key demo:first
```

CLI in một run ID bắt đầu bằng `TSJ`. Thay `{RUN_ID}` bên dưới bằng ID đó:

```bash
cogover-dev jobs runs --job hello_job
cogover-dev jobs run {RUN_ID}
```

Nếu trạng thái còn là `PENDING` hoặc `RUNNING`, kiểm tra lại sau vài giây. Kết quả mong đợi là `SUCCEEDED` và `Attempt: 1/3`. Chạy lại lệnh enqueue với `demo:first` sẽ trả về run cũ, không tạo thêm run.

Để đọc lời nhắn, tạo file Workspace session rồi gọi route lấy kết quả. Thay `{WORKSPACE_DOMAIN}` và `{RUN_ID}`:

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
curl -s --config .cogover-session.curl \
  'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/job_demo/results/{RUN_ID}' \
  -H 'x-req-type: 9' -H 'x-req-service: 3'
```

Response chứa:

```json
{ "result": { "message": "My first background job", "attempt": 1 } }
```

`result: null` nghĩa là ID này chưa có kết quả, hoặc kết quả đã hết thời hạn lưu một giờ. Không đưa `.cogover-session.curl` vào Git và xóa file khi dùng xong.

Bạn cũng có thể khởi chạy job qua route POST:

```bash
curl -s --config .cogover-session.curl -X POST \
  'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/job_demo/hello' \
  -H 'x-req-type: 9' -H 'x-req-service: 3' \
  -H 'Content-Type: application/json' --data '{"message":"Started from a route"}'
```

Route trả HTTP `202`, với `runId` và `duplicate`. Mỗi lần gọi route này tạo một run mới vì code không truyền idempotency key.

## 5. Tự chạy lại khi gặp lỗi tạm thời (retry)

Handler `helloJob` có điều kiện sau để mô phỏng lỗi tạm thời ở lần thử đầu:

```typescript
if (input.simulateFailure === true && job.attempt === 1) {
  throw new RetryableError("Temporary failure for this demo");
}
```

Gửi payload có `"simulateFailure": true` để thử:

```bash
printf '%s\n' '{"message":"Retried successfully","simulateFailure":true}' > payload.json
cogover-dev jobs enqueue hello_job --payload-file payload.json --idempotency-key demo:retry
cogover-dev jobs runs --job hello_job
```

Run diễn ra theo các bước sau:

1. Cogover bắt đầu lần thử đầu tiên với `job.attempt = 1`.
2. Điều kiện trên đúng, nên handler báo `RetryableError` trước khi lưu kết quả.
3. Cogover đưa cùng run đó vào hàng đợi để thử lại. Run ID giữ nguyên.
4. Ở lần thử thứ hai, `job.attempt = 2`. Điều kiện trên không còn đúng, nên handler lưu kết quả và hoàn thành.

Bạn chỉ enqueue một lần; Cogover tự xử lý việc retry. Cấu hình `maxAttempts: 3` trong ví dụ cho phép thử tối đa ba lần, tính cả lần đầu. Khi một lần thử thành công, Cogover dừng retry.

Xem run bằng `cogover-dev jobs run {RUN_ID}`, dùng ID mà lệnh enqueue trả về. Giữa hai lần thử, run ở trạng thái `PENDING` với lỗi `RETRYABLE`. Kết quả cuối cần là `SUCCEEDED`, `Attempt: 2/3` và `attempt: 2` trong kết quả đã lưu. Nếu job chạy nhanh, bạn có thể chỉ kịp thấy trạng thái cuối.

## 6. Đợi trước khi chạy lần đầu (chạy trễ)

Tùy chọn `--delay-ms 10000` tạo run ngay và yêu cầu đợi ít nhất mười giây trước lần chạy đầu tiên. Ghi lại `payload.json` bằng payload không có `simulateFailure` để ví dụ này chỉ thử việc chạy trễ:

```bash
printf '%s\n' '{"message":"Hello after 10 seconds"}' > payload.json
cogover-dev jobs enqueue hello_job --payload-file payload.json --delay-ms 10000 --idempotency-key demo:delayed
```

Idempotency key mới tạo một run riêng với run ở ví dụ retry. Xem ID mới bằng `cogover-dev jobs run {RUN_ID}`: run ban đầu ở trạng thái `PENDING`, rồi được chạy sau khoảng trễ. Kết quả mong đợi là `SUCCEEDED` và `Attempt: 1/3`. Route đọc kết quả ở bước 4 cần trả về `message: "Hello after 10 seconds"` và `attempt: 1`.

Mười giây là thời gian chờ tối thiểu; khi hệ thống bận, run có thể bắt đầu muộn hơn. Nếu giữ `"simulateFailure": true` trong payload, run sẽ đợi mười giây, chạy lần đầu và báo lỗi, rồi tự retry như bước 5.

Khi chạy production, truyền `delayMs` vào tham số thứ ba của `jobs.enqueue()`. Nó tương ứng với tùy chọn `--delay-ms` của CLI. Ví dụ, để các run tạo từ POST `/hello` cũng chạy trễ, bạn có thể sửa route đó thành:

```typescript
router.post("/hello", async ({ request, jobs, response }) => {
  const result = await jobs.enqueue("hello_job", request.body, {
    delayMs: 10_000,
  });
  return response.json(result, { status: 202 });
});
```

Sau khi publish và activate thay đổi này, mỗi POST tạo một run và trả HTTP `202` cùng `runId` ngay khi enqueue xong. Cogover đợi ít nhất mười giây rồi mới chạy; request HTTP không cần chờ hết khoảng trễ. Handler `helloJob` giữ nguyên. Nếu chỉ muốn thử chạy trễ qua CLI, bạn giữ route ban đầu.

## 7. Chạy theo lịch

Trong `src/main.ts`, tìm `const helloJob = defineJob(...)` và thêm `schedule` ngay sau dòng `maxAttempts: 3,`. Toàn bộ khai báo `helloJob` sau khi thêm sẽ như sau; phần xử lý trong handler giữ nguyên:

```typescript
const helloJob = defineJob({
  key: "hello_job",
  timeoutMs: 10_000,
  maxAttempts: 3,
  schedule: {
    cron: "*/5 * * * *",
    timezone: "Asia/Ho_Chi_Minh",
  },
}, async ({ job, payload, state, log }) => {
  if (payload !== null && (typeof payload !== "object" || Array.isArray(payload))) {
    throw new Error("Payload must be an object");
  }
  const input = (payload ?? {}) as Record<string, unknown>;
  const message = input.message ?? "Hello from a background job";
  if (typeof message !== "string") throw new Error("message must be a string");

  // Fail the first attempt only, so the retry can be observed.
  if (input.simulateFailure === true && job.attempt === 1) {
    throw new RetryableError("Temporary failure for this demo");
  }

  await state.namespace("job_results").set(job.id, {
    message,
    attempt: job.attempt,
  }, { ttlSeconds: 3600 });
  log.info("Job completed", { runId: job.id, attempt: job.attempt });
});
```

Giữ nguyên `export const jobs = [helloJob]` và các route bên dưới. Sau khi activate version mới, lịch `*/5 * * * *` tạo run vào các mốc phút chia hết cho 5, ví dụ 09:00, 09:05, 09:10 theo giờ Việt Nam. Route POST `/hello` vẫn có thể enqueue thêm run khi cần.

Publish và activate version mới:

```bash
npm run build
cogover-dev publish
cogover-dev activate {NEW_VERSION_ID}
cogover-dev jobs schedules
```

Sau khi activate version, Cogover tự chạy job mỗi 5 phút theo các mốc của lịch, kể cả khi bạn đóng terminal hoặc tắt máy. Lịch tiếp tục chạy cho đến khi bạn deactivate Project hoặc activate một version mới không còn khai báo `schedule` cho job này. Lịch có hiệu lực từ lúc activate.

Hai lệnh kiểm tra:

- `cogover-dev jobs schedules`: xem danh sách các lịch của Project.
- `cogover-dev jobs runs --job hello_job`: xem các lượt chạy (run) của job `hello_job`, gồm lượt chạy theo lịch và lượt được enqueue qua CLI hoặc code.

Cả hai lệnh chỉ xem thông tin, không tạo lượt chạy hay bật lịch.

Sau khi thử xong, dừng lịch theo một trong hai cách trên rồi xóa `payload.json` và `.cogover-session.curl` sau khi thử xong. Lời nhắn hết hạn sau một giờ; lịch sử run được giữ bảy ngày.

## Cách job hoạt động

Job là một handler có tên. Run là một yêu cầu chạy job; attempt là một lần thực thi của run đó. Khi retry, `job.id` giữ nguyên và `job.attempt` tăng lên.

`jobs.enqueue()` trả về khi Cogover nhận việc vào hàng đợi. Job chạy riêng, dùng version đang active tại thời điểm thực thi. Quy tắc này cũng áp dụng cho run chạy trễ và retry, nên hãy giữ key và định dạng payload tương thích khi publish version mới. Dùng job để cập nhật hàng loạt, đồng bộ ERP, nhắc việc hoặc xử lý webhook. Việc cần trả kết quả ngay trong HTTP response nên nằm trong route.

### Cấu hình và giới hạn

| Thiết lập | Ý nghĩa |
|---|---|
| `key` | Bắt buộc, giữ ổn định trong Project. Bắt đầu bằng chữ cái ASCII; sau đó là chữ cái, chữ số hoặc `_`. Tối đa 100 ký tự, duy nhất không phân biệt hoa thường. |
| `name` | Tên hiển thị tùy chọn, tối đa 250 ký tự. Mặc định bằng key. |
| `timeoutMs` | Thời gian mỗi lần thử: từ 1.000 đến 60.000 ms; mặc định 30.000. |
| `maxAttempts` | Tổng số lần thử, tính cả lần đầu: từ 1 đến 10; mặc định 5. |
| `schedule` | Cron năm trường và múi giờ IANA, không bắt buộc. Múi giờ mặc định là `UTC`. |

Một Project khai báo tối đa 50 job. `defineJob` kiểm tra cấu hình khi module được nạp; chỉ chạy kiểm tra TypeScript thì chưa phát hiện được biểu thức cron sai.

Các trường cron lần lượt là phút, giờ, ngày trong tháng, tháng và thứ. Dùng giá trị số, `*`, khoảng, danh sách và bước nhảy. Tên như `MON` và macro như `@daily` không được hỗ trợ. Ví dụ `0 2 * * *` chạy hằng ngày lúc 02:00 theo múi giờ đã cấu hình. Các mốc bị lỡ khi Project không active sẽ không được chạy bù.

Handler nhận `job`, `payload` và các API của SDK như `data`, `state`, `locks`, `jobs`, `log`. Bạn cần tự kiểm tra payload; kiểu TypeScript không kiểm tra JSON đầu vào. Giá trị trả về của handler bị bỏ qua, vì vậy ví dụ lưu kết quả vào state.

### Tùy chọn enqueue

Trong route, trigger after-change hoặc job khác, dùng API `jobs` từ context:

```typescript
const { runId, duplicate } = await jobs.enqueue("hello_job", { message: "Later" }, {
  delayMs: 60_000,
  idempotencyKey: "hello:batch-1",
});
```

- Payload phải là JSON, tối đa 64 KiB. Với dữ liệu lớn hơn, truyền ID bản ghi.
- Dùng `delayMs` hoặc `runAt` (Unix millisecond), tối đa 30 ngày tới.
- `idempotencyKey` dùng lại run cùng job nếu run đó còn được lưu, kể cả khi đã kết thúc. Key tối đa 128 ký tự: bắt đầu bằng chữ cái hoặc chữ số; tiếp theo là chữ cái, chữ số, `.`, `_`, `:` hoặc `-`.
- Trigger before-change không được enqueue. Khi gọi từ code local, Development Session cũng phải cho phép ghi.
- Giới hạn là 50 lần enqueue mỗi invocation và 10.000 run đang chờ hoặc đang chạy mỗi Project.

Enqueue sau các thao tác ghi record mà job phụ thuộc. Chúng không nằm trong cùng transaction: enqueue thất bại không hoàn tác các thao tác ghi trước đó. Không thể hủy riêng một run đã enqueue; handler chạy trễ nên đọc lại dữ liệu và bỏ qua việc không còn cần làm.

### Retry và xử lý trùng

| Kết quả một lần thử | Trạng thái run |
|---|---|
| Handler kết thúc bình thường | `SUCCEEDED` |
| Handler ném `RetryableError`, bị timeout hoặc gặp lỗi thực thi tạm thời | Trở về `PENDING` nếu còn lần thử; nếu hết thì `FAILED` |
| Handler ném lỗi khác | `FAILED` ngay |

Thời gian chờ tăng dần giữa các lần retry. Run đã kết thúc ở `FAILED` không tự chạy lại; sau khi sửa nguyên nhân, enqueue một run mới với idempotency key mới.

Một run có thể thực thi nhiều lần, kể cả sau khi bị gián đoạn. Hãy viết handler để chạy lại vẫn an toàn: kiểm tra record đã có giá trị mong muốn chưa, và dùng `job.id` làm idempotency key khi gọi dịch vụ ngoài có hỗ trợ. Key lúc enqueue ngăn tạo run trùng; nó không ngăn các lần thử lặp lại trong cùng run.

### Quyền truy cập record

| Nơi khởi chạy | Danh tính dùng để truy cập record |
|---|---|
| Route hoặc trigger after-change | Người gọi hoặc người đã thay đổi record |
| CLI hoặc management API | Người dùng Workspace đứng sau API key hoặc session |
| Job khác | Danh tính của run đã enqueue |
| Lịch hoặc inbound webhook | Danh tính system |
| Code local qua `cogover-dev run` | Người dùng của Project key |

Với job theo lịch hoặc webhook có đọc/ghi record, cấu hình **Identity policy** của Project với `allowInternalSystem: true` và grant giới hạn vào các Object, thao tác cần dùng. Duyệt policy cho từng version mới publish trước khi activate. `data.asSystem()` và `data.asUser()` cũng cần grant đã duyệt. Xem [tài liệu identity policy](custom-backend-module-api-reference.md#identity-policy-1).

### Xử lý nhiều bản ghi và chạy đồng thời

Mỗi run xử lý một trang, tối đa 200 bản ghi, rồi ghi bằng `batchUpdate`. Sắp xếp theo field ổn định. Nếu còn trang tiếp theo, truyền cursor cho một run mới và dùng `${job.id}:next` làm idempotency key. Dừng khi hết trang.

Các run không được bảo đảm thứ tự và có thể chạy đồng thời, kể cả run theo lịch. Dùng `locks.withLock` cho đoạn chỉ được một run thực hiện tại một thời điểm; `waitMs: 0` báo `LockUnavailableError` ngay nếu lock đang bị giữ. Gia hạn lease nếu công việc kéo dài quá thời hạn của nó. Dù có lock, handler vẫn phải xử lý được retry.

Thao tác ghi record kích hoạt automation của Object và mang theo ngân sách tự động hóa từ lời gọi ban đầu (10 bước với run theo lịch và run từ management API). Enqueue không tiêu hao bước nào, nên job tự enqueue chính nó phải có điều kiện dừng.

## Phát triển local

Để thử các HTTP route của ví dụ trên máy, đăng nhập bằng Project key cho phép ghi:

```bash
cogover-dev login --profile job_demo
cogover-dev doctor --profile job_demo
COGOVER_LOCAL_PORT=3100 cogover-dev run --profile job_demo -- npm run dev
```

Trong terminal khác:

```bash
curl -s -X POST 'http://127.0.0.1:3100/api/v1/ts-projects/job_demo/hello' \
  -H 'Content-Type: application/json' --data '{"message":"Started locally"}'
```

Route chạy trên máy bạn. Lệnh `jobs.enqueue()` của nó tạo một run thật trên Cogover, nơi code job của version đã publish đang active được thực thi. Khi sửa handler của job, hãy publish và activate trước khi thử theo cách này. Response từ route local có cùng dạng với khi gọi qua Workspace.

Máy chủ local không tự chạy job hay lịch cron. Với logic cần thử trước khi publish, tách thành các hàm thuần để kiểm tra trên máy; kiểm chứng retry, lịch và danh tính truy cập record trên Cogover. Session mở với `--allow-writes=false` sẽ từ chối enqueue.

## Xử lý sự cố

| Vấn đề | Cần kiểm tra |
|---|---|
| `JOBS_DISABLED` | Nhờ quản trị viên bật background job cho Workspace. |
| `JOB_NOT_DEFINED` hoặc `not defined by the active version` | Đưa job vào export `jobs`, publish và activate đúng version. |
| `PERMISSION_DENIED` khi truy cập record | Kiểm tra quyền người gọi; với run system, kiểm tra policy và phê duyệt cho version active. |
| `JOB_ACTOR_UNAVAILABLE` | Người dùng đã enqueue run không còn thuộc Workspace. |
| `JOB_TIMEOUT` | Giảm công việc mỗi run hoặc tăng `timeoutMs`, tối đa 60.000. |
| `RateLimitError` | Giảm số enqueue mỗi invocation hoặc chờ hàng đợi xử lý bớt. |
| Enqueue trả về run cũ | Đổi idempotency key khi cần bắt đầu công việc mới. |
| Không thấy run theo lịch | Kiểm tra activation, cron và múi giờ bằng `cogover-dev jobs schedules`; chờ một chút để lịch xuất hiện sau activation. |
| `Job run not found` | Kiểm tra Project và ID; lịch sử run đã kết thúc hết hạn sau bảy ngày. |
| Enqueue từ local thất bại | Dùng CLI từ 0.13.1, session cho phép ghi và job có trong version active. |

Khi cần xử lý kết quả bằng chương trình, thêm `--json` vào lệnh `cogover-dev jobs`. Dùng `jobs runs --status FAILED` để tìm run lỗi và `jobs run {RUN_ID}` để xem số lần thử, lỗi cuối. Các lệnh này hiển thị kích thước payload, không trả nội dung payload.

## Đọc thêm

- [API background job của SDK](cogover-sdk-api-reference.md#background-job): đầy đủ kiểu dữ liệu và tùy chọn.
- [API quản lý background job](custom-backend-module-api-reference.md#background-job): liệt kê, xem và enqueue run qua HTTP.
- [Record Trigger](get-started-record-trigger.md): khởi chạy job sau khi record thay đổi.
- [Secrets và credentials](get-started-secrets-and-credentials.md), [inbound webhook](get-started-inbound-webhooks.md) và [mật mã](get-started-crypto.md): kết nối job với dịch vụ ngoài.
