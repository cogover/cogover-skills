# Hướng dẫn sử dụng `@cogover/sdk`

Snapshot tài liệu `@cogover/sdk` `0.10.0` ngày `2026-09-24`, đi kèm [SDK API reference](cogover-sdk-api-reference.md). Sub-agent backend đọc trước khi code để nắm mẫu handler, filter, fetch, secret/credential, mã hoá/giải mã và chữ ký (AES, RSA, ECDSA), state, lock, push message (làm mới record, toast, message ngầm), background job (enqueue, lịch cron, retry), chọn danh tính, cho phép thao tác theo role của người gọi (Super Admin, danh sách role), record trigger (before-change và after-change), TypeScript config, router và nhận webhook; contract chi tiết theo API reference. Object, field và giá trị trong ví dụ chỉ minh họa.

## Custom Backend Module là gì?

**Custom Backend Module** bổ sung logic nghiệp vụ chạy phía server cho một
Cogover Workspace. Module có thể xử lý request, kiểm tra hoặc chuyển đổi dữ liệu,
tự động hoá thao tác record, kiểm tra hoặc điều chỉnh record trước khi lưu, cung
cấp HTTP route hoặc tích hợp Cogover với dịch vụ bên ngoài. Đây là loại module khác với Custom Frontend Module, vốn dùng để xây
dựng giao diện người dùng.

Custom Backend Module được viết bằng TypeScript. `@cogover/sdk` cung cấp type và
API để làm việc với execution hiện tại, dữ liệu Workspace, schema metadata,
logging, outbound HTTPS request, state, distributed lock, push message tới web
client, background job, secret, mã hoá và inbound webhook. Cogover thực thi module
theo quyền và giới hạn tài nguyên đã cấu hình cho project.

Quy trình phát triển thông thường:

1. Tạo project TypeScript và cài `@cogover/sdk`.
2. Sinh `workspace.d.ts` để Object và field trong Workspace có type an toàn.
3. Implement default handler và các record trigger của module, rồi typecheck trên
   máy local.
4. Publish module lên Cogover, cấu hình quyền và gọi module qua trigger hoặc HTTP
   route phù hợp.

## Cài đặt và typecheck

```bash
npm install @cogover/sdk
npx tsc --noEmit
```

Đặt declaration `workspace.d.ts` được sinh từ Object metadata cạnh source của
script trong project TypeScript.

## Bắt đầu nhanh

Ví dụ này giả định `workspace.d.ts` đã khai báo Object `order` và các field được
sử dụng bên dưới.

```typescript
import { defineScript, NotFoundError } from "@cogover/sdk";

interface Input { recordId: string }
interface Output { recordId: string; total: number }

export default defineScript<Input, Output>(async ({ input, data, log }) => {
  const orders = data.object("order");
  const order = await orders.records.get(input.recordId, {
    fields: ["subtotal", "tax", "status"],
  });
  if (!order) throw new NotFoundError("order", input.recordId);

  const total = (order.fields.subtotal ?? 0) + (order.fields.tax ?? 0);
  await orders.records.update(order.id, { status: "processed", total });
  log.info("Order processed", { recordId: order.id, total });
  return { recordId: order.id, total };
});
```

Sinh `workspace.d.ts` từ Object Info metadata và đưa file này vào project
TypeScript của module. Thông tin xác thực của Cogover không được đưa vào code của
module. Quyền truy cập dữ liệu và dịch vụ bên ngoài tuân theo quyền và giới hạn đã
cấu hình cho project.

Runtime áp dụng quyền theo Object, operation và field, hạn mức số capability call,
dung lượng dữ liệu và thời gian chạy cho toàn bộ vòng đời async của handler.

## Đọc danh tính hiện tại và Workspace

Dùng snapshot bất biến `invocation` khi logic cần danh tính hoặc Workspace mà
Cogover đã xác định. Thao tác này không gửi yêu cầu tới Data API:

```typescript
export default defineScript(({ invocation }) => {
  const {workspace} = invocation;
  if (invocation.identity === "system") {
    return {workspaceId: workspace.id, user: null};
  }
  return {
    workspaceId: workspace.id,
    workspaceName: workspace.name,
    accountId: invocation.user.accountId,
    personnelId: invocation.user.membership.personnelId,
  };
});
```

Chỉ dùng Record API khi cần các field nghiệp vụ Personnel đầy đủ và mới nhất như
phòng ban, chức danh, quản lý hoặc custom field. Snapshot chỉ chứa các field đã
được tài liệu hoá, không chứa thông tin xác thực thô hay credential của Cogover.

### Cho phép thao tác theo role trong Workspace

`invocation.user.membership` còn cho biết người gọi có phải Super Admin của
Workspace hiện tại hay không và đang giữ những role nào trong Workspace đó. Ví dụ,
chỉ cho phép duyệt khi người dùng là Super Admin hoặc có role người duyệt:

```typescript
const APPROVER_ROLE_ID = "RO0000000001";

export default defineScript(({ invocation }) => {
  const user = invocation.user;
  const canApprove = user !== null && (user.membership.isSuperAdmin
    || user.membership.roles.some((role) => role.id === APPROVER_ROLE_ID));
  if (!canApprove) {
    return {approved: false, reason: "Only approvers can approve this order"};
  }
  return {approved: true};
});
```

- Các giá trị mô tả role của người gọi trong Workspace hiện tại. Mỗi role chỉ có
  `id` và `name`; quyền của role không được cung cấp.
- So sánh role theo `id`, không theo tên: role có thể được đổi tên và `id` của
  role khác nhau giữa các Workspace.
- Cogover vẫn kiểm soát quyền truy cập record và field theo danh tính của người
  dùng. Hãy dùng các field này cho quy tắc nghiệp vụ, không thay thế cho quy tắc
  bảo mật.
- Invocation HTTP phản ánh role tại thời điểm gửi request. Record trigger và
  background job có thể nhận thay đổi role chậm tối đa khoảng một phút.
- Khi phát triển local bằng Cogover Dev CLI, các giá trị được lấy lúc development
  session bắt đầu. Hãy khởi động lại `cogover-dev` để nhận thay đổi role.
- Invocation `system` và `inbound` có `user: null` nên không có membership.

## Lọc và sắp xếp record

```typescript
import { and, defineScript } from "@cogover/sdk";

export default defineScript(async ({ data }) => {
  const orders = data.object("order");
  return orders.records.list({
    where: and(
      orders.fields.status.in(["new", "nurturing"]),
      orders.fields.is_active.eq(true),
      orders.fields.total.gte(1_000_000),
    ),
    orderBy: [orders.fields.updated.desc()],
    limit: 50,
  });
});
```

## Đọc nhiều record theo ID

`records.getMany` đọc tối đa 200 record bằng một capability call. `fields` là bắt
buộc, và các ID không đọc được sẽ được báo lại thay vì bị bỏ qua:

```typescript
const accounts = data.object("account");
const { records, missingIds } = await accounts.records.getMany(accountIds, {
  fields: ["name", "credit_limit"],
});
const accountById = new Map(records.map(record => [String(record.id), record]));
if (missingIds.length > 0) log.warn("Accounts could not be read", { missingIds });
```

ID trùng chỉ được gửi một lần. Thứ tự của `records` không bảo đảm trùng với `ids`, vì
vậy hãy tra cứu record theo `id`. Nên dùng `getMany` thay cho việc gọi `get` trong
vòng lặp: mỗi capability call đều được tính vào hạn mức của project.

## Gọi API ngoài bằng `fetch`

```typescript
import { defineScript, fetch } from "@cogover/sdk";

interface Input {
  externalToken: string;
  orderId: string;
}

export default defineScript<Input>(async ({ input }) => {
  const response = await fetch("https://api.example.com/v1/orders", {
    method: "POST",
    headers: {
      authorization: `Bearer ${input.externalToken}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({ id: input.orderId }),
    timeoutMs: 5_000,
  });
  if (!response.ok) return { status: response.status };
  return response.json();
});
```

API tương thích Fetch này dùng lớp network do Cogover quản lý, không cung cấp quyền
network Node.js không giới hạn. Chỉ URL HTTPS public port 443 được hỗ trợ. V1 không follow
redirect, không cookie jar, không streaming/WebSocket, không IP literal/URL userinfo
và không cho cấu hình proxy, dispatcher, agent, DNS hoặc TLS. Request và response
đều có giới hạn. Với thao tác ghi ra API ngoài, dùng idempotency key của API đích;
timeout hoặc mất response không chứng minh remote chưa xử lý request.

## Dùng secret và credential

Không đặt API token trong source code hay trong input của request. Quản trị viên
lưu chúng cho project qua management API của Cogover, dưới một trong hai dạng:

- **Credential** chỉ dùng cho `fetch`. Ghi tên vào `credential` và Cogover thêm
  header xác thực — `Authorization: Bearer …`, `Authorization: Basic …` hoặc một
  header tuỳ chỉnh — vào request. Code không bao giờ thấy giá trị, và credential chỉ
  được gửi tới các host mà quản trị viên cho phép.
- **Secret** được đọc bằng `secrets.get` khi code cần chính giá trị đó, ví dụ để
  tạo chữ ký hoặc header không chuẩn.

```typescript
import { defineScript, fetch } from "@cogover/sdk";

export default defineScript<{ orderId: string }>(async ({ input, secrets, crypto }) => {
  // Nên dùng: token do Cogover thêm vào và không bao giờ đi vào code.
  const response = await fetch("https://erp.example.com/v1/orders", {
    method: "POST",
    credential: "erp_api",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ id: input.orderId }),
  });

  // Khi cần chính giá trị, đọc secret và ký bằng nó.
  const body = await response.text();
  const signature = await crypto.hmacSha256({ secret: "partner_signing_key" }, body);
  const apiKey = await secrets.get("partner_api_key");
  await fetch("https://partner.example.com/events", {
    method: "POST",
    headers: { "x-api-key": apiKey, "x-signature": signature },
    body,
  });
  return { status: response.status };
});
```

`crypto.hmacSha256({ secret: name }, data)` ký bằng secret mà không cần đọc giá
trị, đủ cho hầu hết chữ ký. Không bao giờ ghi secret vào log, record, state hay
response, và ưu tiên credential thay vì `secrets.get` mỗi khi giá trị chỉ cần cho
một HTTP header. Secret và credential không dùng được trong trigger before-change.

## Mã hoá, giải mã và ký dữ liệu

`crypto` còn mã hoá và ký bằng các key nằm trong secret của project. Truyền
`{ secret: name }` làm key: Cogover resolve key đó và giá trị không bao giờ đi vào
code.

```typescript
import { createRouter, crypto, fetch } from "@cogover/sdk";

const router = createRouter();
router.post("/payments", async ({ request, response }) => {
  // AES-256-GCM với IV ngẫu nhiên; đối tác nhận ciphertext và IV.
  const aesKey = { secret: "partner_aes_key", encoding: "base64" } as const;
  const sealed = await crypto.aesEncrypt(aesKey, JSON.stringify(request.body));

  // RSA: mã hoá giá trị nhỏ bằng public key của đối tác, ký bằng private key của mình.
  const cardToken = await crypto.rsaEncrypt({ secret: "partner_public_key" }, "4111111111111111");
  const body = JSON.stringify({ ...sealed, cardToken });
  const signature = await crypto.sign("RSA-SHA256", { secret: "our_signing_key" }, body);
  const reply = await fetch("https://partner.example.com/payments", {
    method: "POST",
    headers: { "content-type": "application/json", "x-signature": signature },
    body,
  });

  // Xác minh chữ ký ECDSA của đối tác trước khi tin phản hồi.
  const replyBody = await reply.text();
  const valid = await crypto.verify("ECDSA-SHA256", { secret: "partner_public_key_ec" }, replyBody,
    reply.headers.get("x-signature") ?? "");
  return valid ? response.json(JSON.parse(replyBody)) : response.empty({ status: 502 });
});
export default router.toHandler();
```

- `aesEncrypt`/`aesDecrypt` mặc định dùng AES-GCM; `mode: "CBC"` dành cho các hệ
  thống bắt buộc dùng nó. Không truyền `iv` để mỗi lần mã hoá dùng một IV ngẫu
  nhiên mới.
- `rsaEncrypt`/`rsaDecrypt` mặc định dùng RSA-OAEP với SHA-256 và chỉ mã hoá được
  tối đa vài trăm byte; dữ liệu lớn hơn hãy mã hoá bằng AES và chỉ mã hoá AES key
  bằng RSA.
- `sign`/`verify` hỗ trợ RSA (PKCS #1 v1.5 và PSS) và ECDSA, kể cả dạng `base64url`
  và `ieee-p1363` mà JWT dùng. `verify` trả về `false` với chữ ký sai định dạng thay
  vì ném lỗi.
- Giải mã thất bại ném `CogoverApiError` với `code: "DECRYPTION_FAILED"`.
- Key là văn bản PEM lưu trong secret: private key lưu chưa mã hoá ở dạng PKCS #8,
  PKCS #1 hoặc SEC1; public key có thể là certificate. RSA key phải dài 2048 đến
  4096 bit, EC key dùng P-256, P-384 hoặc P-521.

Khi key lấy từ secret, các thao tác này tuân theo quy tắc của secret và không dùng
được trong trigger before-change. API reference mô tả mọi tuỳ chọn và tên thuật
toán JWT tương ứng.

## Quyền và giới hạn

- Thông tin xác thực của Cogover không được đưa vào code của module; quyền truy cập
  được giới hạn theo Object, operation và field đã cấu hình.
- TypeScript types không thay thế validation lúc chạy.
- Cogover giới hạn số lần gọi, kích thước request/response và thời gian thực thi.
- Request ghi không được tự retry khi timeout vì kết quả commit có thể chưa rõ.

## Lưu tiến độ nhỏ bằng state

Dùng state cho cursor đồng bộ, checkpoint hoặc cờ điều phối nhỏ cần tồn tại qua
nhiều execution và version deploy. Mỗi giá trị là JSON tối đa 32 KiB:

```typescript
export default defineScript(async ({ state }) => {
  const sync = state.namespace("inventory-sync");
  const current = await sync.get<{ cursor: string }>("cursor");
  const nextCursor = await fetchNextPage(current?.value.cursor);

  const saved = await sync.set("cursor", { cursor: nextCursor }, {
    expectedVersion: current?.version ?? 0,
    ttlSeconds: 86_400,
  });
  return { version: saved.version };
});
```

`expectedVersion` tránh ghi đè thay đổi từ execution khác. Khi gặp
`StateConflictError`, đọc lại rồi quyết định merge/retry ở cấp nghiệp vụ. State
không phải nơi lưu secret hoặc dữ liệu lớn và không nằm chung transaction với record.

## Chống chạy đồng thời bằng distributed lock

```typescript
export default defineScript(async ({ locks }) =>
  locks.withLock("daily-import", { namespace: "inventory", waitMs: 500 }, async lease => {
    await runImport({ fencingToken: lease.fencingToken });
    return { completed: true };
  }));
```

`withLock` luôn thử release trong `finally`; nếu không lấy được sẽ ném
`LockUnavailableError`. Lease mặc định 30 giây và không tự renew. Với đoạn xử lý
dài, kiểm tra `expiresAt` và gọi `renew()` trước khi hết hạn. Dùng fencing token ở
hệ thống đích nếu có thể để chặn writer cũ. Lock không thay thế idempotency hay
bảo đảm exactly-once.

## Yêu cầu trang record đang mở tải lại

```typescript
export default defineTrigger({
  key: "recalculate_totals",
  object: "order",
  timing: "afterChange",
  operations: ["update"],
  fields: ["subtotal", "tax"],
}, async ({ records, data, push }) => {
  const items = records.flatMap(record => record.id === null ? [] : [{
    id: record.id,
    fields: { total: (record.new.subtotal ?? 0) + (record.new.tax ?? 0) },
  }]);
  await data.object("order").records.batchUpdate(items);
  // Mọi người đang mở một trong các đơn hàng này sẽ tải lại, kể cả người vừa lưu.
  await push.refreshRecords("order", items.map(item => item.id));
});
```

`push` còn hiển thị toast (`push.toast`) hoặc gửi message ngầm (`push.message`) tới
những người đang xem record chỉ định hoặc tới danh sách personnel ID (`recipients`);
`exclude: ["actor"]` bỏ qua người gây ra execution. Gửi là best-effort và mỗi lời gọi
tính một capability call. API reference liệt kê giới hạn và các trường của message.
## Chạy việc nền bằng job

HTTP route hoặc trigger có thời gian rất ngắn. Hãy chuyển việc dài hơn — duyệt
nhiều record, gọi API ngoài chậm, bảo trì hằng đêm — vào **background job**. Khai
báo job bằng `defineJob` và liệt kê trong named export `jobs`; enqueue một lần chạy
từ route, trigger hoặc job khác bằng `jobs.enqueue`, hoặc để `schedule` cron khởi
chạy.

```typescript
import { defineJob } from "@cogover/sdk";

interface RecalcPayload {
  cursor?: string;
}

// Xử lý một trang mỗi lần chạy và tự enqueue lại với cursor kế tiếp.
export const recalcTotals = defineJob<RecalcPayload>({
  key: "recalc_totals",
  timeoutMs: 60_000,
}, async ({ payload, data, jobs, log }) => {
  const orders = data.object("order");
  const page = await orders.records.list({
    fields: ["subtotal", "tax"],
    limit: 200,
    ...(payload?.cursor ? { cursor: payload.cursor } : {}),
  });
  for (const order of page.items) {
    await orders.records.update(order.id, {
      total: (order.fields.subtotal ?? 0) + (order.fields.tax ?? 0),
    });
  }
  if (page.nextCursor) {
    await jobs.enqueue("recalc_totals", { cursor: page.nextCursor });
    return;
  }
  log.info("Order totals recalculated");
});

// Chạy hằng đêm lúc 02:00 theo múi giờ đã cho, không có payload.
export const cancelStaleOrders = defineJob({
  key: "cancel_stale_orders",
  schedule: { cron: "0 2 * * *", timezone: "Asia/Ho_Chi_Minh" },
}, async ({ data }) => {
  const orders = data.object("order");
  const stale = await orders.records.list({
    where: orders.fields.status.eq("new"),
    fields: ["status"],
    limit: 200,
  });
  for (const order of stale.items) {
    await orders.records.update(order.id, { status: "cancelled" });
  }
});

export const jobs = [recalcTotals, cancelStaleOrders];
```

Khởi chạy batch từ một route:

```typescript
router.post("/recalculate", async ({ jobs, response }) => {
  const { runId } = await jobs.enqueue("recalc_totals", {}, { idempotencyKey: "recalc:daily" });
  return response.json({ runId }, { status: 202 });
});
```

- Job handler nhận `job` (run ID, key, lần thử, nguồn), `payload` đã truyền cho
  `enqueue` (hoặc `null`) và cùng các API `data`, `schema`, `log`, `state`,
  `locks`, `jobs`, `secrets`, `crypto` như script. Giá trị trả về bị bỏ qua.
- Lần chạy được enqueue từ route hoặc trigger thực hiện dưới danh tính người dùng
  của lời gọi đó. Lần chạy theo lịch không có người dùng: `data.object()` chỉ hoạt
  động khi identity policy cho phép danh tính system, nên hãy duyệt
  `allowInternalSystem` cho project có lịch.
- Lần chạy được giao ít nhất một lần: lần chạy bị gián đoạn do restart sẽ được bắt
  đầu lại, và lỗi tạm thời báo bằng `RetryableError` (hoặc timeout) được thử lại với
  thời gian chờ tăng dần tối đa `maxAttempts` lần. Hãy viết handler idempotent và
  dùng `job.id` hoặc một key nghiệp vụ làm idempotency key cho các lời gọi ra ngoài.
  Mọi lỗi khác làm lần chạy thất bại mà không retry.
- Mỗi lần thử phải hoàn tất trong `timeoutMs` (tối đa 60 giây). Chia việc dài hơn
  thành từng trang và enqueue trang kế tiếp như ví dụ: enqueue không tiêu tốn ngân
  sách tự động hoá, nên chuỗi chỉ bị giới hạn bởi điều kiện dừng của chính handler.
  Thao tác ghi record do job thực hiện vẫn dùng ngân sách và chạy trigger như mọi
  thao tác ghi khác.
- `idempotencyKey` làm lần enqueue lặp lại trả về lần chạy hiện có với
  `duplicate: true`; `delayMs` hoặc `runAt` hoãn lần chạy tối đa 30 ngày. Payload là
  JSON tối đa 64 KiB.

Xem [tài liệu tham chiếu background job](cogover-sdk-api-reference.md#background-job) để biết
mọi tuỳ chọn và quy tắc.

## Chọn danh tính cho thao tác record

Tiếp tục dùng `data.object("order")` để kế thừa danh tính người gọi. Khi quản trị
viên đã duyệt project và người gọi được chọn danh tính, dùng:

```typescript
const orders = data.object("order");
const order = await orders.records.get(input.recordId, { fields: ["description"] });
if (!order) throw new NotFoundError("order", input.recordId);

// Chọn một thao tác theo yêu cầu nghiệp vụ:
await data.asUser(personnelId).object("order").records.update(order.id, { description: "Delegated update" });
// Hoặc: await data.asSystem().object("order").records.update(order.id, { description: "System update" });
```

`asUser` nhận ID nhân sự, hỗ trợ cả đọc và ghi. `asSystem` hỗ trợ cả đọc và dùng được trong script public
mà không thay đổi người gọi đã xác thực. Cả hai trả client mới, giữ suy luận kiểu
workspace và không ảnh hưởng client đã tạo.

Để đọc theo nhân sự được chọn, dùng cùng client cho `get` và `list`:

```typescript
const delegatedOrders = data.asUser(personnelId).object("order");
const record = await delegatedOrders.records.get(input.recordId, { fields: ["description"] });
const page = await delegatedOrders.records.list({ fields: ["description"], limit: 20 });
// Lấy trang tiếp theo với cùng danh tính:
if (page.nextCursor) {
  await delegatedOrders.records.list({ fields: ["description"], limit: 20, cursor: page.nextCursor });
}
```

Quản trị viên cần cấp quyền đọc riêng với quyền ghi. Các lời gọi đọc áp dụng quyền
của nhân sự được chọn; khi thất bại không tự thử lại bằng hệ thống.

Lỗi quyền không được bắt trả HTTP 403 với `code: "PERMISSION_DENIED"`.
`reason: "IDENTITY_NOT_GRANTED"` nghĩa là project chưa được duyệt để chọn danh tính
đó. Kiểm tra `writesMayHaveCompleted` trước khi cân nhắc retry: các lần ghi trước không
bị rollback. Xem [tham chiếu phản hồi lỗi](cogover-sdk-api-reference.md#errors).

Lựa chọn chưa được cấp quyền bị từ chối, không tự fallback. Project có quyền nâng
cao phải kiểm tra caller được yêu cầu xử lý những record nào; nhìn thấy một record
chưa đủ để kết luận được phép thực hiện nghiệp vụ. Không dùng input request để cấp
quyền hệ thống. Không đưa Cogover API key hoặc đối tượng xác thực vào code của
module; không ghi log hoặc trả về credential của dịch vụ bên ngoài. Xem
[API reference](cogover-sdk-api-reference.md#danh-tính-thực-hiện-thao-tác-record).

## Record trigger

Record trigger chạy code của bạn khi record của một Object được tạo, cập nhật hoặc
xoá. Trigger **before-change** chạy trước khi thay đổi được lưu: trigger có thể từ
chối thay đổi bằng lỗi validation và có thể điều chỉnh giá trị sẽ được lưu. Trigger
**after-change** chạy sau khi thay đổi đã được lưu, dành cho các việc tiếp theo như
cập nhật record liên quan hoặc thông báo cho hệ thống khác; xem
[Trigger after-change](#trigger-after-change). Trigger
chạy cho mọi nguồn ghi — ứng dụng web Cogover, API key, import, automation process
và Custom Backend Module khác — nên quy tắc đặt trong trigger không thể bị vượt qua
bằng cách chọn một đường ghi khác. Các thao tác ghi bảo trì do chính Cogover thực
hiện, như tính lại field formula và rollup, merge record chạy nền và cascade delete,
không chạy trigger.

Khai báo trigger bằng `defineTrigger` và liệt kê trong named export `triggers`.
Default export vẫn là HTTP handler và là tuỳ chọn với project chỉ có trigger. Ví dụ
này giả định `workspace.d.ts` đã khai báo các Object và field được sử dụng.

```typescript
import { defineTrigger, type RecordReference } from "@cogover/sdk";

const referenceId = (value: string | RecordReference | null | undefined): string | undefined =>
  typeof value === "string" ? value : value?.id;

export const triggers = [
  defineTrigger({
    key: "order_credit_check",
    name: "Order credit check",
    object: "order",
    timing: "beforeChange",
    operations: ["create", "update"],
    fields: ["status", "amount", "customer"],
    changedFields: ["status", "amount", "customer"],
    when: { op: "=", field: "status", params: "confirmed" },
    writableFields: ["approval_level"],
  }, async ({ records, data }) => {
    // One read for the whole list, never one read per record.
    const customerIds = records.flatMap(record => referenceId(record.new.customer) ?? []);
    const customers = await data.object("account").records.getMany(customerIds, {
      fields: ["credit_limit"],
    });
    const limitById = new Map<string, number>(
      customers.records.map(customer => [customer.id, customer.fields.credit_limit ?? 0]),
    );

    for (const record of records) {
      const amount = record.new.amount ?? 0;
      const limit = limitById.get(referenceId(record.new.customer) ?? "");
      if (limit === undefined) {
        record.addError("customer", "CUSTOMER_NOT_AVAILABLE", "Select a customer that you can access.");
        continue;
      }
      if (amount > limit) {
        record.addError("amount", "CREDIT_LIMIT_EXCEEDED", "Amount exceeds the customer's credit limit.");
        continue;
      }
      record.new.approval_level = amount > 100_000_000 ? "high" : "standard";
    }
  }),
];
```

Cogover áp dụng các trigger của version project đang active. Ý nghĩa từng thiết lập:

- `fields` chọn các giá trị được đưa vào `record.new` và `record.old`. Chỉ các field
  này và `id` có mặt, nên field không được liệt kê sẽ là `undefined`. Chỉ liệt kê
  những gì handler cần đọc: một lần gọi bị giới hạn 200 KiB.
- `operations` chọn `"create"`, `"update"` và `"delete"`. `record.old` là `null` với
  record được tạo và `record.new` là `null` với record bị xoá; kiểu TypeScript đi
  theo các operation bạn khai báo.
- `changedFields` khiến thao tác cập nhật chỉ chạy trigger khi ít nhất một field
  trong danh sách thay đổi. `record.changedFields` cho handler biết field nào đã đổi.
- `when` chỉ chạy trigger với record khớp điều kiện. Đây là object thuần như
  `{ op: "=", field: "status", params: "confirmed" }`, kết hợp bằng
  `{ op: "and", conditions: [...] }` hoặc `{ op: "or", conditions: [...] }`.
  `runWhen: "onEnter"` chỉ chạy trigger khi record bắt đầu khớp `when`, thay vì chạy
  ở mọi lần ghi có khớp.
- `writableFields` liệt kê các field handler được sửa (chỉ với before-change).
- `order` (1000–8999, mặc định 5000) xác định vị trí của trigger giữa các trigger của
  cùng Object. Trigger chạy sau thấy giá trị do trigger chạy trước đã sửa.
- `timeoutMs` (100–3000, mặc định 2000) là thời gian tối đa của một lần gọi.

**Validate.** Gọi `record.addError(field, code, message?)` để từ chối một record;
truyền `null` làm field với lỗi của cả record. Mã lỗi là định danh viết hoa như
`CREDIT_LIMIT_EXCEEDED`. Message tuỳ chọn là đoạn văn bản tiếng Anh tối đa 500 ký tự,
được Cogover hiển thị cho người dùng cuối khi chưa có bản dịch cho mã lỗi. Record bị
từ chối sẽ không được lưu. Trong batch write, các dòng khác vẫn tiếp tục.

**Sửa giá trị.** Gán field của `record.new`, ví dụ
`record.new.approval_level = "high"`. Chỉ `writableFields` được thay đổi; sửa bất kỳ
field nào khác làm thao tác ghi thất bại với `ValidationError` nêu tên field. Giá trị
được gán dùng cùng định dạng với input của `records.update`, nên field reference nhận
record ID và field date nhận `"yyyy-MM-dd"`. Gán `null` sẽ xoá giá trị của field. Cogover validate lại giá trị cuối cùng trước khi lưu. Trigger
có thể điền field đã tắt nhập thủ công, nhưng không bao giờ sửa được field read-only
như formula, auto number hoặc rollup.

**Xử lý cả danh sách.** Handler nhận tối đa 200 record trong một lần gọi: batch write
hoặc import gọi handler một lần cho mỗi nhóm record, không gọi cho từng record.
Không đọc dữ liệu bên trong vòng lặp. Hãy gom các ID, gọi `records.getMany` một lần
rồi tra cứu kết quả từ một `Map` như ví dụ trên.

**Chỉ đọc.** Trigger before-change được đọc record và schema. Thao tác ghi record,
`fetch`, lock, ghi state và push message bị từ chối bằng `PermissionDeniedError`
(`details.reason === "TRIGGER_READ_ONLY"`) với mọi danh tính. Trigger context có
`records`, `trigger`, `invocation`, `data`, `schema`, `log` và `push`; không có
`request`, `response`, `state` hay `locks`.

**Danh tính.** `data.object()` thực hiện dưới danh tính người đã tạo ra thay đổi, với
quyền của người đó, nên một lời gọi đọc có thể không trả về record mà người này không
nhìn thấy. `data.asUser()` và `data.asSystem()` cần quản trị viên phê duyệt giống
như trong script.

**Thời gian và lỗi.** Một lần gọi phải hoàn tất trong `timeoutMs`, và mọi trigger
before-change của một thao tác ghi dùng chung 8 giây. Trigger before-change hoạt
động theo nguyên tắc fail closed: khi handler ném lỗi, hết thời gian hoặc không thể
chạy, thao tác ghi bị từ chối và không có gì được lưu. Hãy giữ handler ngắn gọn và
có kết quả xác định. Xem [tham chiếu record trigger](cogover-sdk-api-reference.md#record-trigger).

### Trigger after-change

Đặt `timing: "afterChange"` để chạy code sau khi thay đổi đã được lưu. Handler chạy
bất đồng bộ, ngay sau thao tác ghi: bên ghi không chờ handler, và handler không thể
từ chối hay sửa thay đổi đã lưu. Khác với trigger before-change, handler được ghi
record, gọi `fetch`, đọc secret và enqueue background job như một script.

```typescript
import { defineTrigger, fetch, RetryableError } from "@cogover/sdk";

export const triggers = [
  defineTrigger({
    key: "order_confirmed_followup",
    object: "order",
    timing: "afterChange",
    operations: ["create", "update"],
    fields: ["status", "amount", "customer"],
    changedFields: ["status"],
    when: { op: "=", field: "status", params: "confirmed" },
    runWhen: "onEnter",
  }, async ({ records, trigger, data }) => {
    for (const record of records) {
      // record.new holds the saved values; record.id is always set after the save.
      const response = await fetch("https://erp.example.com/orders", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "idempotency-key": `${trigger.changeId}:${record.id}`,
        },
        body: JSON.stringify({ id: record.id, amount: record.new.amount }),
      });
      if (response.status >= 500) {
        // Temporary problem: ask Cogover to run this handler again later.
        throw new RetryableError("The ERP is temporarily unavailable");
      }
      if (!response.ok) continue; // Permanent problem: retrying would not help.

      await data.object("order_activity").records.create({
        order: record.id,
        activity: "Sent to ERP",
      });
    }
  }),
];
```

- **Giá trị đã lưu.** `record.new` chứa giá trị đúng như đã lưu, gồm record ID và các
  giá trị được gán trong lúc lưu, ví dụ auto number. `record.old` chứa giá trị trước
  thay đổi. Record bị xoá có `record.new === null`.
- **Không chặn, không sửa.** Không được khai báo `writableFields` và không được sửa
  `record.new`. Ở đây `record.addError()` không từ chối gì cả; các lỗi chỉ được ghi
  vào log của project. Để sửa record, hãy gọi `records.update`.
- **Best-effort.** Cogover không bảo đảm handler chạy đúng một lần: handler đôi khi
  có thể chạy nhiều hơn một lần cho cùng một thay đổi, hoặc không chạy. Hãy viết
  handler theo kiểu idempotent — `trigger.changeId` cùng với `record.id` xác định một
  thay đổi của một record — và không bao giờ coi trigger after-change là bảo đảm duy
  nhất cho một quy tắc quan trọng. Hãy đặt các quy tắc đó trong trigger before-change.
- **Retry.** Ném `RetryableError` với lỗi tạm thời. Cogover sẽ chạy lại handler sau,
  mặc định tối đa thêm 5 lần với thời gian chờ tăng dần từ khoảng một giây đến khoảng
  mười phút. Lần gọi hết thời gian cũng được thử lại theo cách đó. Mọi lỗi khác được
  ghi log và không retry, vì vậy hãy bắt các lỗi bạn xử lý được và quyết định lỗi nào
  đáng được retry.
- **Vòng lặp luôn kết thúc.** Thao tác ghi do handler thực hiện sẽ chạy lại các
  trigger, có thể gồm chính trigger đó. Cogover giới hạn các chuỗi như vậy: mỗi thao
  tác ghi tự động dùng một bước trong một ngân sách cố định (10 bước với thay đổi do
  người dùng hoặc API client thực hiện trực tiếp), và trigger after-change ngừng chạy
  khi ngân sách đã hết. Thu hẹp trigger bằng `changedFields`, `when` và
  `runWhen: "onEnter"` để thao tác ghi của chính nó không kích hoạt lại nó.
- **Thứ tự.** Các trigger after-change của một thay đổi chạy độc lập; không dựa vào
  thứ tự tương đối giữa chúng, và hãy đọc lại record khi cần giá trị mới nhất.

Xem [Quy tắc thực thi after-change](cogover-sdk-api-reference.md#quy-tắc-thực-thi-after-change).

## TypeScript config khuyến nghị

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*.ts", "workspace.d.ts"]
}
```

Chỉ import từ `@cogover/sdk` và local source nằm trong project root. Runtime chặn
Node built-in, package chưa duyệt, URL import, `require()` và dynamic `import()`.

## HTTP route và response đầy đủ

```typescript
import { createRouter } from "@cogover/sdk";

const router = createRouter();
router.get("/orders/:orderId", ({ request, response }) => response.json({
  orderId: request.params.orderId,
  expand: request.query.expand,
}));
router.post<{ description: string }, object>("/orders", ({ request, response }) =>
  response.json({ description: request.body.description }, { status: 201 }));
router.put("/orders/:orderId", ({ request }) => ({ orderId: request.params.orderId }));
router.patch("/orders/:orderId", ({ request }) => ({ orderId: request.params.orderId }));
router.delete("/orders/:orderId", ({ response }) => response.empty());
export default router.toHandler();
```

Route hỗ trợ GET, POST, PUT, PATCH và DELETE. `request` có `method`, `path`, `params`
đã decode, `query` hỗ trợ tên lặp, `headers` an toàn dạng chữ thường và JSON `body`.
Header xác thực không bao giờ lộ vào script. Giá trị trả trực tiếp là JSON HTTP 200.
Các helper `response.json`, `text`, `bytes`, `empty`, `redirect` cho phép đặt status,
response header an toàn và body text/binary. Route thiếu trả 404; method không hỗ trợ
trả 405. Project `defineScript()` cũ tiếp tục chạy tại `/`. Cần validate mọi input
nghiệp vụ. Xem [router API reference](cogover-sdk-api-reference.md#http-router-và-request-context).

## Nhận webhook

Hệ thống bên ngoài có thể gọi một route mà không cần phiên người dùng Cogover thông
qua **inbound access** do quản trị viên tạo cho project. Quản trị viên đưa cho hệ
thống bên ngoài URL có dạng
`https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/{projectSlug}/hooks/{inboundId}/{route}`
cùng với một inbound key hoặc một HMAC signing secret. Cogover xác thực từng lời
gọi và từ chối lời gọi không hợp lệ trước khi module chạy; module thấy lời gọi tại
`/hooks/{route}` với `invocation.identity === "inbound"`.

```typescript
import { createRouter, defineJob } from "@cogover/sdk";

interface PaymentEvent { id: string; orderId: string; status: "succeeded" | "failed" }

const router = createRouter();
router.post("/hooks/payments", async ({ request, invocation, crypto, jobs, response }) => {
  if (invocation.identity !== "inbound") return response.empty({ status: 403 });

  // Tuỳ chọn: nhà cung cấp này còn ký "<timestamp>.<raw body>" bằng secret riêng của họ.
  const timestamp = request.headers["x-payment-timestamp"] ?? "";
  const expected = await crypto.hmacSha256(
    { secret: "payment_signing_secret" }, `${timestamp}.${request.rawBody ?? ""}`);
  if (!crypto.timingSafeEqual(`sha256=${expected}`, request.headers["x-payment-signature"] ?? "")) {
    return response.empty({ status: 401 });
  }

  const event = request.body as Partial<PaymentEvent>;
  if (typeof event.id !== "string" || typeof event.orderId !== "string") {
    return response.json({ error: "Invalid event" }, { status: 400 });
  }
  await jobs.enqueue("sync_payment", event, { idempotencyKey: `payment:${event.id}` });
  return response.json({ received: true }, { status: 202 });
});
export default router.toHandler();

export const jobs = [
  defineJob<PaymentEvent>({ key: "sync_payment" }, async ({ payload, data }) => {
    if (!payload) return;
    // ID từ bên ngoài là chuỗi thường: đọc record trước, rồi cập nhật qua ID của chính record.
    const orders = data.object("order");
    const order = await orders.records.get(payload.orderId, { fields: ["status"] });
    if (!order) return;
    await orders.records.update(order.id, {
      status: payload.status === "succeeded" ? "processed" : "cancelled",
    });
  }),
];
```

- `request.rawBody` là body đúng như đã nhận và `request.contentType` là content
  type của nó, nên handler có thể kiểm tra chữ ký của bên gửi hoặc parse body không
  phải JSON. `request.body` chứa JSON object đã parse, hoặc `{}` với body dạng khác.
- Lời gọi inbound không có người dùng. `data.object()` dùng danh tính system và chỉ
  hoạt động khi identity policy cho phép; `data.asUser()` và `data.asSystem()` tuân
  theo policy như thông thường. Nên xác nhận nhanh rồi enqueue job — job cũng chạy
  dưới danh tính system.
- Nhà cung cấp gửi lại webhook không nhận được trả lời 2xx, nên hãy dùng ID riêng
  của sự kiện làm `idempotencyKey` của job.

Xem [Inbound webhook](cogover-sdk-api-reference.md#inbound-webhook) để biết đầy đủ quy tắc.
