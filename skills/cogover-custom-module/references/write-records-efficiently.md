# Ghi record hiệu quả

Một route đọc vài record rồi ghi thêm nhiều record khác dành phần lớn thời gian để chờ Cogover. Khi mỗi SDK call đều được `await` xong mới bắt đầu call tiếp theo, các khoảng chờ đó cộng dồn: route chậm dần theo từng record được ghi, và một client gọi route nhiều lần liên tiếp sẽ tạo hàng đợi trong Workspace. Hướng dẫn này viết lại một route như vậy để nó gọi ít call hơn và bắt đầu các call độc lập cùng lúc: các lần đọc không phụ thuộc nhau chạy bằng `Promise.all`, nhiều record của một Object được ghi bằng một `records.batchInsert`, và các thao tác ghi độc lập được gửi cùng lúc. Sau đó, hướng dẫn chỉ cách client nên xử lý khi Workspace đang bận, và khi nào nên chuyển việc sang background job.

Đọc hướng dẫn này khi một route ghi nhiều record trong mỗi lần gọi, khi route được một công cụ tự động hay một hệ thống tích hợp gọi, hoặc khi bên gọi nhận HTTP `429`.

## Ví dụ: kích hoạt bảo hành

Một công ty dịch vụ kích hoạt bảo hành cho thiết bị khi kỹ thuật viên đóng phiếu lắp đặt. Một route nhận `{ "jobId": "...", "serial": "..." }` và:

1. đọc phiếu dịch vụ và thiết bị có số serial đó;
2. đọc các mẫu linh kiện theo model của thiết bị, ví dụ sáu linh kiện;
3. tạo một sự kiện bảo hành, chuyển thiết bị sang trạng thái đang bảo hành kèm ngày bắt đầu và kết thúc, đánh dấu phiếu dịch vụ đã kích hoạt, và tạo một linh kiện lắp đặt cho mỗi mẫu.

Ví dụ dùng các Object sau:

| Object | Field dùng đến |
|---|---|
| `service_job` | `asset` (lookup tới `asset`), `status` (`new`, `activated`), `activated_at` (ngày giờ) |
| `asset` | `serial` (văn bản), `model` (văn bản), `status` (`inactive`, `active`), `warranty_start`, `warranty_end` (ngày giờ) |
| `component_template` | `model` (văn bản), `component_code` (văn bản), `quantity` (số) |
| `warranty_event` | `asset`, `service_job` (lookup), `event_type` (`activation`, `claim`), `event_at` (ngày giờ) |
| `installed_component` | `asset`, `service_job` (lookup), `component_code` (văn bản), `quantity` (số), `installed_at` (ngày giờ) |

Để chạy code, tạo các Object này trong một Workspace thử nghiệm, tạo Project có slug `warranty` như trong [Bắt đầu với Custom Backend Module](get-started-custom-backend-module.md), rồi sinh `src/workspace.d.ts` cho năm Object như bước 2 của [Đọc record hiệu quả](read-records-efficiently.md). Dùng `@cogover/sdk` 0.13.0 trở lên: mọi lần đọc đều nêu `fields`.

## 1. Phiên bản tuần tự

Cách viết thẳng nhất `await` từng call trước khi bắt đầu call tiếp theo:

```typescript
import { createRouter } from "@cogover/sdk";

const YEAR_MS = 365 * 24 * 60 * 60 * 1000;
const router = createRouter();

// Sequential: every call waits for the previous one. Input validation is left out here.
router.post("/activate", async ({ data, request, response }) => {
  const { jobId, serial } = request.body as { jobId: string; serial: string };
  const jobs = data.object("service_job");
  const assets = data.object("asset");
  const events = data.object("warranty_event");
  const templates = data.object("component_template");
  const components = data.object("installed_component");

  const job = await jobs.records.get(jobId, { fields: ["asset", "status"] });
  if (job === null) return response.json({ error: "Service job not found" }, { status: 404 });
  const assetPage = await assets.records.list({
    where: assets.fields.serial.eq(serial),
    fields: ["serial"],
    limit: 1,
  });
  const assetId = assetPage.items[0]?.id;
  if (assetId === undefined) return response.json({ error: "Asset not found" }, { status: 404 });
  const asset = await assets.records.get(assetId, { fields: ["model", "status"] });
  const model = asset?.fields.model ?? "";
  const templatePage = await templates.records.list({
    where: templates.fields.model.eq(model),
    fields: ["name"],
    limit: 200,
  });
  const templateRows = [];
  for (const item of templatePage.items) {
    const template = await templates.records.get(item.id, { fields: ["component_code", "quantity"] });
    if (template !== null) templateRows.push(template);
  }

  const now = Date.now();
  const eventId = await events.records.create({
    name: `Activation ${serial}`,
    asset: assetId,
    service_job: job.id,
    event_type: "activation",
    event_at: now,
  });
  await assets.records.update(assetId, { status: "active", warranty_start: now, warranty_end: now + YEAR_MS });
  await jobs.records.update(job.id, { status: "activated", activated_at: now });
  const componentIds = [];
  for (const template of templateRows) {
    componentIds.push(await components.records.create({
      name: `${serial} ${template.fields.component_code ?? ""}`.trim(),
      asset: assetId,
      service_job: job.id,
      component_code: template.fields.component_code,
      quantity: template.fields.quantity ?? 1,
      installed_at: now,
    }));
  }
  return { eventId, componentIds };
});

export default router.toHandler();
```

Kết quả đúng, nhưng với model có sáu linh kiện, route gọi 19 capability call lần lượt từng call: 10 lần đọc (đọc thiết bị hai lần, và đọc lại từng mẫu theo ID) và 9 lần ghi. Mỗi call chờ một lượt đi về tới Cogover, nên thời gian tăng theo từng linh kiện. Ngân sách của một HTTP route là 100 capability call (xem [Giới hạn của một lần thực thi](cogover-sdk-api-reference.md#giới-hạn-của-một-lần-thực-thi)): với code này, model có khoảng 50 linh kiện sẽ thất bại với `RateLimitError` trước khi chạy xong, và khi Workspace chậm, route có thể chạm giới hạn 8 giây còn sớm hơn.

## 2. Đọc bằng ít call hơn, cùng lúc

Ba thay đổi giảm phần đọc từ 10 call còn 3:

- Phiếu dịch vụ và thiết bị không phụ thuộc nhau, nên đọc cùng lúc bằng `Promise.all`.
- `records.list` trả về các field được yêu cầu. Yêu cầu luôn `model` và `status` khi liệt kê thiết bị, thay vì liệt kê ID rồi đọc lại thiết bị.
- Yêu cầu `component_code` và `quantity` khi liệt kê mẫu linh kiện, thay vì đọc lại từng mẫu theo ID. Khi đã có sẵn danh sách ID, dùng một `records.getMany` (tối đa 200 ID) thay cho mỗi ID một `records.get`.

```typescript
// Wait 1: the service job and the asset do not depend on each other.
const [job, assetPage] = await Promise.all([
  jobs.records.get(jobId, { fields: ["asset", "status"] }),
  assets.records.list({
    where: assets.fields.serial.eq(serial),
    fields: ["model", "status"],
    limit: 1,
  }),
]);

// ... checks ...

// Wait 2: one list returns every template of the model with the fields the components need.
const templatePage = await templates.records.list({
  where: templates.fields.model.eq(model),
  fields: ["component_code", "quantity"],
  limit: 200,
});
```

Danh sách mẫu linh kiện phụ thuộc vào model của thiết bị, nên nó phải chờ hai lần đọc đầu. Chỉ bắt đầu các call cùng lúc khi chúng không cần kết quả của nhau.

## 3. Ghi bằng một batch, cùng lúc

Bốn thao tác ghi không phụ thuộc nhau, và sáu linh kiện thuộc cùng một Object:

- Tạo mọi linh kiện lắp đặt bằng một `records.batchInsert`, nhận từ 1 đến 200 record và chỉ là một capability call.
- Gửi sự kiện, hai thao tác cập nhật và batch cùng lúc bằng `Promise.all`.

```typescript
// Wait 3: four independent writes; the components are one batch.
const [eventId, , , inserted] = await Promise.all([
  events.records.create({ /* ... */ }),
  assets.records.update(asset.id, { status: "active", warranty_start: now, warranty_end: now + YEAR_MS }),
  jobs.records.update(job.id, { status: "activated", activated_at: now }),
  componentRows.length > 0 ? components.records.batchInsert(componentRows) : null,
]);
```

`batchInsert` cần ít nhất một record, nên code bỏ qua call này khi model không có mẫu nào. Batch xử lý best-effort theo từng dòng: kiểm tra `success` và từng dòng của `results` (xem [Data client và operation](cogover-sdk-api-reference.md#data-client-và-operation)).

Giờ toàn bộ route chỉ gọi 7 capability call trong 3 lần chờ, và vẫn là 7 với model có 200 linh kiện. Route vẫn ghi đúng 9 record, được tính vào ngân sách record ghi như trước. Sau khi publish, route thường trả lời nhanh hơn phiên bản tuần tự nhiều lần, và thời gian không còn tăng theo số linh kiện.

## 4. Toàn bộ route

Tạo `src/main.ts`. Phần kích hoạt là một hàm riêng để background job ở bước 7 dùng lại:

```typescript
import { createRouter, defineJob } from "@cogover/sdk";
import type { DataApi } from "@cogover/sdk";

const ID_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;
const YEAR_MS = 365 * 24 * 60 * 60 * 1000;

type Activation =
  | { status: 200; body: { eventId: string; componentIds: string[] } }
  | { status: 404 | 409; body: { error: string } }
  | { status: 500; body: { error: string; failedRows: string[] } };

export async function activateWarranty(data: DataApi, jobId: string, serial: string): Promise<Activation> {
  const jobs = data.object("service_job");
  const assets = data.object("asset");
  const events = data.object("warranty_event");
  const templates = data.object("component_template");
  const components = data.object("installed_component");

  // Wait 1: the service job and the asset do not depend on each other.
  const [job, assetPage] = await Promise.all([
    jobs.records.get(jobId, { fields: ["asset", "status"] }),
    assets.records.list({
      where: assets.fields.serial.eq(serial),
      fields: ["model", "status"],
      limit: 1,
    }),
  ]);
  const asset = assetPage.items[0];
  if (job === null) return { status: 404, body: { error: "Service job not found" } };
  if (asset === undefined) return { status: 404, body: { error: "Asset not found" } };
  if (job.fields.asset !== null && job.fields.asset.id !== asset.id) {
    return { status: 409, body: { error: "The service job belongs to another asset" } };
  }
  if (job.fields.status === "activated" || asset.fields.status === "active") {
    return { status: 409, body: { error: "The warranty is already activated" } };
  }
  const model = asset.fields.model;
  if (!model) return { status: 409, body: { error: "The asset has no model" } };

  // Wait 2: one list returns every template of the model with the fields the components need.
  const templatePage = await templates.records.list({
    where: templates.fields.model.eq(model),
    fields: ["component_code", "quantity"],
    limit: 200,
  });
  if (templatePage.total > templatePage.items.length) {
    return { status: 409, body: { error: "The model has more than 200 component templates" } };
  }

  // Wait 3: four independent writes; the components are one batch.
  const now = Date.now();
  const componentRows = templatePage.items.map(template => ({
    name: `${serial} ${template.fields.component_code ?? ""}`.trim(),
    asset: asset.id,
    service_job: job.id,
    component_code: template.fields.component_code,
    quantity: template.fields.quantity ?? 1,
    installed_at: now,
  }));
  const [eventId, , , inserted] = await Promise.all([
    events.records.create({
      name: `Activation ${serial}`,
      asset: asset.id,
      service_job: job.id,
      event_type: "activation",
      event_at: now,
    }),
    assets.records.update(asset.id, {
      status: "active",
      warranty_start: now,
      warranty_end: now + YEAR_MS,
    }),
    jobs.records.update(job.id, { status: "activated", activated_at: now }),
    componentRows.length > 0 ? components.records.batchInsert(componentRows) : null,
  ]);

  const rows = inserted?.results ?? [];
  const failedRows = rows.filter(row => !row.success).map(row => row.referenceId);
  if (inserted !== null && (!inserted.success || failedRows.length > 0)) {
    return { status: 500, body: { error: "Some installed components were not saved", failedRows } };
  }
  return { status: 200, body: { eventId, componentIds: rows.flatMap(row => (row.id ? [row.id] : [])) } };
}

interface ActivationItem {
  jobId: string;
  serial: string;
}

function readItem(value: unknown): ActivationItem | null {
  if (typeof value !== "object" || value === null) return null;
  const { jobId, serial } = value as { jobId?: unknown; serial?: unknown };
  if (typeof jobId !== "string" || !ID_PATTERN.test(jobId)) return null;
  if (typeof serial !== "string" || serial.trim() === "" || serial.length > 100) return null;
  return { jobId, serial: serial.trim() };
}

const activateWarrantiesJob = defineJob<{ items: ActivationItem[] }>({
  key: "activate_warranties",
  timeoutMs: 60_000,
}, async ({ payload, data, log }) => {
  const results: { jobId: string; status: number }[] = [];
  for (const item of payload?.items ?? []) {
    const result = await activateWarranty(data, item.jobId, item.serial);
    results.push({ jobId: item.jobId, status: result.status });
  }
  log.info("Warranty activations finished", { results });
});

export const jobs = [activateWarrantiesJob];

const router = createRouter();

router.post("/activate", async ({ data, request, response }) => {
  const item = readItem(request.body);
  if (item === null) {
    return response.json({ error: "A valid jobId and serial are required" }, { status: 400 });
  }
  const result = await activateWarranty(data, item.jobId, item.serial);
  return response.json(result.body, { status: result.status });
});

router.post("/activate-many", async ({ jobs, request, response }) => {
  const body = request.body as { items?: unknown } | null;
  const items = Array.isArray(body?.items) ? body.items.map(readItem) : [];
  if (items.length === 0 || items.length > 50 || items.some(item => item === null)) {
    return response.json({ error: "items must list 1 to 50 valid { jobId, serial } pairs" }, { status: 400 });
  }
  const { runId } = await jobs.enqueue("activate_warranties", { items });
  return response.json({ runId }, { status: 202 });
});

export default router.toHandler();
```

- Các bước kiểm tra từ chối phiếu của thiết bị khác và bảo hành đã được kích hoạt, nên gọi route hai lần cho cùng một phiếu không tạo thêm bộ linh kiện thứ hai.
- Các thao tác ghi không phải transaction, ở phiên bản này cũng như phiên bản tuần tự. Khi một call trong `Promise.all` cuối cùng ném lỗi, các call khác vẫn chạy và dữ liệu chúng ghi vẫn được giữ; khi batch báo có dòng thất bại, route trả `500` kèm chỉ số các dòng đó. Hãy kiểm tra dữ liệu trước khi kích hoạt lại cùng phiếu.
- Route đọc bằng quyền của người gọi, nên người gọi cần quyền đọc và ghi năm Object.

## 5. Chạy thử và publish

Chạy route trên local bằng Cogover Dev CLI, rồi publish và activate như trong [Bắt đầu với Custom Backend Module](get-started-custom-backend-module.md). Trên local, CLI chạy các SDK call của một lần gọi lần lượt từng call: kết quả giống trên Cogover, nhưng server local không cho thấy lợi ích của call song song. Hãy so sánh hai phiên bản trên Project đã publish, ví dụ bằng `curl -w '%{time_total}\n'`:

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
curl -s --config .cogover-session.curl -w '\n%{time_total}\n' \
  -X POST 'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/warranty/activate' \
  -H 'x-req-type: 9' -H 'x-req-service: 3' -H 'Content-Type: application/json' \
  --data '{"jobId":"{SERVICE_JOB_ID}","serial":"{SERIAL}"}'
```

`limits.usage()` cho biết một lần gọi đã dùng bao nhiêu capability call và record, mà bản thân nó không tốn capability call nào (xem [Đọc giới hạn trong code](cogover-sdk-api-reference.md#đọc-giới-hạn-trong-code)).

## 6. Khi Workspace đang bận: HTTP 429

Mỗi Workspace chỉ chạy đồng thời một số lần gọi nhất định; các lần gọi khác phải chờ. Khi một client gửi dồn nhiều request, ví dụ một công cụ kích hoạt hàng trăm phiếu trong một vòng lặp mà không chờ, hàng đợi sẽ dài ra. Request không thể bắt đầu kịp bị từ chối ngay, trước khi chạy bất cứ gì:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3
Content-Type: application/json

{
  "r": 429,
  "code": "RATE_LIMITED",
  "msg": "The request limit has been exceeded. Please try again later.",
  "writesMayHaveCompleted": false,
  "retryAfterMillis": 2400
}
```

Chưa có gì chạy, nên client có thể gửi lại nguyên request. Client nên:

- chờ ít nhất `Retry-After` giây (hoặc `retryAfterMillis`) trước lần gửi tiếp theo, và khi không có hai giá trị này thì chờ lâu dần sau mỗi lần bị từ chối;
- gửi `Idempotency-Key` với mọi request ghi dữ liệu, để lần gửi lại sau khi mất response trả lại kết quả đầu tiên thay vì ghi hai lần. Request bị từ chối không chiếm key của nó;
- chỉ giữ vài request đang chạy cùng lúc thay vì gửi cả danh sách một lần.

Route ngắn hơn cũng giúp ích: mỗi lần gọi xong càng sớm thì lần gọi kế tiếp bắt đầu càng sớm. Ví dụ một client Node.js 20:

```javascript
const BASE = "https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/warranty";

// sessionHeaders: the Cookie and X-Csrf-Token headers of a Workspace session.
async function activate(item, sessionHeaders) {
  for (let attempt = 1; ; attempt++) {
    const response = await fetch(`${BASE}/activate`, {
      method: "POST",
      headers: {
        ...sessionHeaders,
        "x-req-type": "9",
        "x-req-service": "3",
        "Content-Type": "application/json",
        "Idempotency-Key": `activate-${item.jobId}`,
      },
      body: JSON.stringify(item),
    });
    if (response.status !== 429 || attempt === 5) return response;
    const seconds = Number(response.headers.get("Retry-After"));
    const delayMs = seconds > 0 ? seconds * 1000 : 1000 * 2 ** attempt;
    await new Promise(resolve => setTimeout(resolve, delayMs + Math.random() * 500));
  }
}

// Three requests in flight at a time.
async function activateAll(items, sessionHeaders, concurrency = 3) {
  const queue = [...items];
  await Promise.all(Array.from({ length: concurrency }, async () => {
    for (let item = queue.shift(); item; item = queue.shift()) {
      const response = await activate(item, sessionHeaders);
      console.log(item.jobId, response.status);
    }
  }));
}
```

Không tự động gửi lại với các lỗi khác: lỗi `4xx` khác `429` sẽ lại thất bại, còn `422` hoặc `5xx` có thể đến sau khi một số thao tác ghi đã hoàn tất. Xem [Gọi module production](custom-backend-module-api-reference.md#gọi-module-production) để biết các header của request và quy tắc `Idempotency-Key`.

## 7. Kích hoạt hàng loạt: dùng background job

Khi việc cần làm là một danh sách, ví dụ kích hoạt mọi phiếu đóng trong ngày, gọi route hàng trăm lần sẽ khiến Workspace bận liên tục và mọi bên gọi phải chờ. Thay vào đó, hãy gửi danh sách một lần và để background job xử lý. Route `activate-many` ở bước 4 kiểm tra tối đa 50 cặp và enqueue một lần chạy `activate_warranties`, job này kích hoạt lần lượt từng cặp bằng cùng một hàm:

```bash
curl -s --config .cogover-session.curl \
  -X POST 'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/warranty/activate-many' \
  -H 'x-req-type: 9' -H 'x-req-service: 3' -H 'Content-Type: application/json' \
  --data '{"items":[{"jobId":"{SERVICE_JOB_ID_1}","serial":"{SERIAL_1}"},{"jobId":"{SERVICE_JOB_ID_2}","serial":"{SERIAL_2}"}]}'
```

```json
{ "runId": "TSJXXXXXXXXXXXX" }
```

- Job có ngân sách lớn hơn route, trong đó có 1.000 capability call, và tối đa 60 giây cho mỗi lần thử. Mỗi lần kích hoạt gọi tối đa 7 call, nên 50 cặp vừa trong một lần chạy; danh sách dài hơn thì chia thành nhiều lần chạy.
- Lần chạy thực thi với danh tính và quyền của người đã gọi `activate-many`.
- Job có thể được chạy lại, ví dụ sau một lỗi tạm thời. Các bước kiểm tra trong `activateWarranty` giúp việc này an toàn: cặp đã kích hoạt trả `409` và không ghi gì.

Xem [Bắt đầu với background job](get-started-background-jobs.md) để publish job và xem các lần chạy.

## Lời gọi song song: cần biết

- Các call bắt đầu cùng lúc chạy song song, tối đa một số call đồng thời do nền tảng đặt; call vượt quá sẽ chờ tới khi có chỗ. Call được `await` trước khi call tiếp theo bắt đầu thì chạy riêng.
- Mỗi call đều tính vào ngân sách của lần gọi, dù chạy riêng hay song song. Giảm số call bằng `records.getMany` và `records.batchInsert` hoặc `records.batchUpdate` hiệu quả hơn chạy song song.
- Call được bắt đầu mà không `await` vẫn chạy xong trước khi lần gọi kết thúc.
- Thứ tự của các call song song không cố định. Push message và notification gửi cùng lúc có thể tới theo thứ tự bất kỳ. `push.refreshRecords` nằm trong cùng `Promise.all` với thao tác cập nhật mà nó báo có thể tới người dùng trước khi cập nhật được lưu: hãy `await` thao tác ghi rồi mới refresh.
- Hai lời gọi `state.set` cùng key không có `expectedVersion` thì giá trị còn lại là một trong hai.
- Không dùng cùng một `idempotencyKey` cho hai call trong cùng một `Promise.all`.
- Trên local, Cogover Dev CLI chạy các call lần lượt từng call, kết quả như nhau.

## Xử lý sự cố

| Vấn đề | Cần kiểm tra |
|---|---|
| `RateLimitError` với `details.budget: "capabilityCalls"` | Route gọi quá nhiều call. Đọc bằng `records.list` hoặc `records.getMany` thay cho mỗi record một `get`, ghi bằng `records.batchInsert` hoặc `records.batchUpdate`, hoặc chuyển việc sang background job. |
| `ValidationError` `batchInsert() requires at least one record` | Danh sách dòng rỗng. Bỏ qua call như bước 4. |
| `ValidationError` `batchInsert() supports at most 200 records` | Chia các dòng thành từng batch 200, hoặc dùng background job. |
| Response là `200` nhưng thiếu một số linh kiện | Batch không ném lỗi khi một dòng bị từ chối. Kiểm tra `success` và từng dòng của `results`. |
| Người dùng thấy record đã refresh nhưng chưa có thay đổi mới nhất | `push.refreshRecords` được bắt đầu cùng lúc với thao tác ghi. Hãy `await` thao tác ghi trước. |
| Bên gọi nhận HTTP `429` với `code: "RATE_LIMITED"` | Workspace có quá nhiều lần gọi đang chờ. Gửi lại sau `Retry-After`, giữ ít request chạy cùng lúc hơn, rút ngắn route, hoặc gửi danh sách cho background job. |
| Server local không nhanh hơn sau khi sửa | Đúng như dự kiến: Cogover Dev CLI chạy các call lần lượt. Hãy so sánh trên các phiên bản đã publish. |

## Đọc thêm

- [Lời gọi song song](cogover-sdk-api-reference.md#lời-gọi-song-song) và [Giới hạn của một lần thực thi](cogover-sdk-api-reference.md#giới-hạn-của-một-lần-thực-thi): quy tắc và ngân sách của một lần gọi.
- [API record của SDK](cogover-sdk-api-reference.md#record-api): `getMany`, `batchInsert`, `batchUpdate` và giới hạn của chúng.
- [Đọc record hiệu quả](read-records-efficiently.md): nêu field cần đọc, đọc record liên kết và đếm bằng `records.aggregate`.
- [Bắt đầu với background job](get-started-background-jobs.md): chạy việc dài hoặc hàng loạt bên ngoài request.
- [Gọi module production](custom-backend-module-api-reference.md#gọi-module-production): header của request, `429` và `Idempotency-Key`.
