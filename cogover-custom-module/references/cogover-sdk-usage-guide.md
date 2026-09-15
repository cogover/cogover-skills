# Hướng dẫn sử dụng `@cogover/sdk`

Snapshot tài liệu `@cogover/sdk` `0.5.0` ngày `2026-09-15`, đi kèm [SDK API reference](cogover-sdk-api-reference.md). Sub-agent backend đọc trước khi code để nắm mẫu handler, filter, fetch, state, lock, chọn danh tính, TypeScript config và router; contract chi tiết theo API reference. Object, field và giá trị trong ví dụ chỉ minh họa.

## Custom Backend Module là gì?

**Custom Backend Module** bổ sung logic nghiệp vụ chạy phía server cho một
Cogover Workspace. Module có thể xử lý request, kiểm tra hoặc chuyển đổi dữ liệu,
tự động hoá thao tác record, cung cấp HTTP route hoặc tích hợp Cogover với dịch
vụ bên ngoài. Đây là loại module khác với Custom Frontend Module, vốn dùng để xây
dựng giao diện người dùng.

Custom Backend Module được viết bằng TypeScript. `@cogover/sdk` cung cấp type và
API để làm việc với execution hiện tại, dữ liệu Workspace, schema metadata,
logging, outbound HTTPS request, state và distributed lock. Cogover thực thi
module theo quyền và giới hạn tài nguyên đã cấu hình cho project.

Quy trình phát triển thông thường:

1. Tạo project TypeScript và cài `@cogover/sdk`.
2. Sinh `workspace.d.ts` để Object và field trong Workspace có type an toàn.
3. Implement default handler của module và typecheck trên máy local.
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
