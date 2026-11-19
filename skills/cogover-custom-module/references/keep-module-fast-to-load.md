# Giữ module nạp nhanh: tách phần theo điểm vào

Snapshot tài liệu `@cogover/sdk` `0.18.0`, Cogover Dev CLI `0.22.0` và Backend API Reference ngày `2026-11-20`. Đọc khi tổ chức source của Custom Backend Module (mọi project), quyết định có khai báo `entryPointParts` hay không, đọc **Load profile** sau khi publish, và khi review code của project đã khai báo `entryPointParts: true`. Contract chi tiết: mục [Tổ chức route theo nhóm](cogover-sdk-usage-guide.md#tổ-chức-route-theo-nhóm) và [Giữ module nạp nhanh](cogover-sdk-usage-guide.md#giữ-module-nạp-nhanh) của SDK usage guide, [`router.route()`](cogover-sdk-api-reference.md#routerrouteprefix-string-router-scriptroutertschema-scriptroutertschema) của SDK API reference, [Hồ sơ nạp](custom-backend-module-api-reference.md#hồ-sơ-nạp) của Backend API Reference, [Phần theo điểm vào và Load profile](cli-session-and-delivery.md#phần-theo-điểm-vào-và-load-profile) của CLI reference. Tên file, Object và số liệu bên dưới chỉ minh hoạ.

## 1. Vì sao

- Mọi lần thực thi (HTTP route, record trigger, background job, Custom Module Action) bắt đầu bằng việc nạp code của module trong sandbox. Module lớn nạp lâu, rõ nhất ở lượt gọi đầu tiên sau khi publish hoặc sau một thời gian rảnh. Thời gian nạp sát giới hạn thời gian của lần thực thi để lại rất ít thời gian cho handler, đặc biệt với trigger before-change (`timeoutMs` mặc định 2 giây, tối đa 3 giây, hết giờ thì chặn thao tác ghi).
- Khi publish, ngoài module biên dịch đầy đủ (*merged bundle*), Cogover dựng thêm các module nhỏ gọi là **phần** (*part*): trigger, job hoặc action được định nghĩa và export từ file riêng (không phải `src/main.ts`) có phần chỉ chứa code file đó cần; router con tạo trong file riêng và gắn bằng `router.route()` có phần cho các route của nó. `@cogover/sdk` là module dùng chung, nạp trước phần. Một lần thực thi chạy bằng phần thì chỉ nạp SDK và phần của nó.
- Module đầy đủ luôn được dựng và là đường dự phòng: điểm vào không có phần, phần không dựng được hoặc version không chạy bằng phần đều dùng module đầy đủ như trước.
- Chạy bằng phần chỉ an toàn khi code chạy lúc file được nạp không tác động ra ngoài file đó (mục 4), vì phần chỉ nạp một tập file. Vì vậy tác giả phải khai báo (mục 5); không khai báo thì theo mặc định của nền tảng, hiện là module đầy đủ.

## 2. Điều kiện phiên bản và môi trường

| Việc | Cần | Chưa đủ điều kiện thì |
|---|---|---|
| Mỗi trigger/job/action một file, `src/main.ts` chỉ gom lại; route xử lý bằng hàm ở file riêng; quy tắc "lệnh ở đầu file" | Mọi phiên bản SDK, CLI, Workspace | Vẫn làm: vô hại và sẵn sàng cho khi Workspace hỗ trợ |
| `router.route(prefix, childRouter)` | `@cogover/sdk` từ `0.18.0` trong project **và** Workspace chạy Runtime hỗ trợ | Không dùng: đăng ký route thẳng trên router chính (mục 3.3). Workspace build version bằng `@cogover/sdk` của chính nó (ZIP chỉ chứa `src/`), nên trên Workspace chưa hỗ trợ, publish code có `router.route()` thất bại dù project đã cài SDK mới; SDK cũ thì typecheck báo `Property 'route' does not exist` |
| `"entryPointParts"` trong `cogover.json`, `cogover-dev publish --parts`/`--no-parts` | Dev CLI từ `0.22.0`; Workspace hỗ trợ | CLI cũ bỏ qua key này trong `cogover.json` (không gửi khai báo) và từ chối `--parts`/`--no-parts` với `CLI_USAGE`; Workspace chưa hỗ trợ bỏ qua khai báo |
| CLI in Load profile sau publish | Dev CLI từ `0.22.0`; Workspace hỗ trợ | Đọc `loadProfile` qua API chi tiết version; Workspace chưa hỗ trợ không trả field này |

Kiểm trước khi dùng `router.route()` hoặc khai báo:

1. Phiên bản project và công cụ: `npm ls @cogover/sdk` (hoặc `package.json`), `cogover-dev --version`; bản mới nhất đã phát hành: `npm view @cogover/sdk version`, `npm view @cogover/dev-cli version`. Chưa có bản `0.18.0`/`0.22.0` trên npm thì chưa đủ điều kiện; không cài SDK hay CLI từ nguồn khác npm.
2. Workspace: sau một lần publish (version `READY`), output của `cogover-dev publish` có khối `Load profile` kèm dòng `Runs on:`, hoặc response [Đọc một version](custom-backend-module-api-reference.md#đọc-một-version) có `loadProfile` khác `null` với `entryPointParts.effective` là boolean. `loadProfile` vắng mặt ở version vừa `READY` nghĩa là Workspace chưa hỗ trợ (`null` cũng gặp ở version cũ hoặc chưa build xong, nên kiểm trên version mới publish). Project mới chưa publish lần nào: đọc chi tiết version mới nhất của một backend Project khác trên cùng Workspace (chỉ đọc), hoặc publish bản đầu theo cách cũ (không `router.route()`) rồi kiểm.
3. Chưa đủ cả hai: viết theo cách cũ, không dùng `router.route()`, không khai báo `entryPointParts`, ghi lý do trong báo cáo bàn giao. Khi đủ điều kiện về sau, chuyển route sang router con theo mục 3.3 là thay đổi nhỏ trong `src/main.ts` và các file router.

## 3. Tổ chức code

### 3.1. Bố cục gợi ý

```text
src/
├── main.ts                 # chỉ import, gom export, gắn router con
├── workspace.d.ts
├── triggers/
│   └── order-credit-check.ts
├── jobs/
│   └── order-reminder.ts
├── actions/
│   └── score-lead.ts
├── routers/
│   └── orders.ts           # chỉ createRouter() và các dòng đăng ký route
├── handlers/
│   └── orders.ts           # hàm xử lý route
├── lib/                    # logic dùng chung, hàm thuần
└── data/                   # bảng tra cứu lớn, mỗi bảng một file
```

Tên thư mục không bắt buộc; điều kiện là ranh giới file. Một file có thể chứa một nhóm nhỏ trigger/job/action liên quan (export từng cái hoặc trong một mảng được export): mọi điểm vào trong file dùng chung một phần, nên chỉ gom những điểm vào cần cùng code.

### 3.2. Trigger, job và action

Điểm vào định nghĩa ngay trong `src/main.ts` không có phần riêng (`NOT_LOCATED`). Trước:

```typescript
// src/main.ts (TRƯỚC): mọi thứ trong một file
import { createRouter, defineJob, defineTrigger } from "@cogover/sdk";

const creditCheck = defineTrigger({ key: "order_credit_check", object: "order", timing: "beforeChange",
  operations: ["create", "update"], fields: ["amount", "customer"] }, async ({ records, data }) => { /* ... */ });
const orderReminder = defineJob({ key: "order_reminder", schedule: { cron: "0 8 * * *", timezone: "Asia/Ho_Chi_Minh" } },
  async ({ data }) => { /* ... */ });

export const triggers = [creditCheck];
export const jobs = [orderReminder];
const router = createRouter();
export default router.toHandler();
```

Sau: mỗi điểm vào định nghĩa và export từ file của nó; logic nghiệp vụ là hàm thuần ở `lib/`.

```typescript
// src/triggers/order-credit-check.ts
import { defineTrigger } from "@cogover/sdk";
import { exceedsCreditLimit } from "../lib/credit.js";

export const orderCreditCheck = defineTrigger({
  key: "order_credit_check", object: "order", timing: "beforeChange",
  operations: ["create", "update"], fields: ["amount", "customer"],
}, async ({ records, data }) => { /* đọc một lần, gọi exceedsCreditLimit, record.addError */ });
```

```typescript
// src/jobs/order-reminder.ts
import { defineJob } from "@cogover/sdk";

export const orderReminder = defineJob({
  key: "order_reminder",
  schedule: { cron: "0 8 * * *", timezone: "Asia/Ho_Chi_Minh" },
}, async ({ data, notifications }) => { /* ... */ });
```

```typescript
// src/main.ts (SAU): chỉ import và gom lại
import { createRouter } from "@cogover/sdk";
import { orderCreditCheck } from "./triggers/order-credit-check.js";
import { orderReminder } from "./jobs/order-reminder.js";
import { scoreLead } from "./actions/score-lead.js";

export const triggers = [orderCreditCheck];
export const jobs = [orderReminder];
export const actions = [scoreLead];

const router = createRouter();
// gắn router con ở mục 3.3
export default router.toHandler();
```

`key`, cấu hình và handler giữ nguyên khi chuyển file; manifest của version không đổi.

### 3.3. Nhóm route trong router con

Route đăng ký thẳng trên router chính luôn chạy bằng module đầy đủ. Mỗi nhóm route liên quan là một router con tạo bằng `createRouter()` trong **file riêng chỉ chứa `createRouter()` và các dòng đăng ký route**; hàm xử lý và logic dùng chung đặt ở file khác; chỉ `src/main.ts` import file router và gắn bằng `router.route(prefix, childRouter)`. Không đặt router chung file với hàm xử lý mà job, trigger hay route khác import: phần của chúng sẽ kéo theo cả nhóm route.

Cần `@cogover/sdk` từ `0.18.0` và Workspace hỗ trợ (mục 2). Ví dụ ba route đơn hàng:

```typescript
// src/handlers/orders.ts: hàm xử lý, job hay route khác import được
import { NotFoundError, ValidationError, type ScriptHandler } from "@cogover/sdk";

const ORDER_FIELDS = ["name", "status", "amount"] as const;
type Handler = ScriptHandler<unknown, unknown>;

export const listOrders: Handler = async ({ data }) => {
  const page = await data.object("order").records.list({ fields: ORDER_FIELDS, limit: 50 });
  return { orders: page.records };
};

export const getOrder: Handler = async ({ request, data }) => {
  const order = await data.object("order").records.get(request.params.orderId ?? "", { fields: ORDER_FIELDS });
  if (!order) throw new NotFoundError("order", request.params.orderId ?? "");
  return { order };
};

export const confirmOrder: Handler = async ({ request, data }) => {
  const orderId = request.params.orderId;
  if (!orderId) throw new ValidationError("orderId is required");
  await data.object("order").records.update(orderId, { status: "confirmed" });
  return { orderId, status: "confirmed" };
};
```

```typescript
// src/routers/orders.ts: chỉ createRouter() và đăng ký route
import { createRouter } from "@cogover/sdk";
import { confirmOrder, getOrder, listOrders } from "../handlers/orders.js";

export const ordersRouter = createRouter();
ordersRouter.get("/", listOrders);                         // GET  /orders
ordersRouter.get("/:orderId", getOrder);                   // GET  /orders/:orderId
ordersRouter.post("/:orderId/confirm", confirmOrder);      // POST /orders/:orderId/confirm
```

```typescript
// src/main.ts
import { createRouter } from "@cogover/sdk";
import { ordersRouter } from "./routers/orders.js";

const router = createRouter();
router.route("/orders", ordersRouter);
export default router.toHandler();
```

Chưa đủ điều kiện mục 2 (cách cũ): giữ `src/handlers/orders.ts`, bỏ `src/routers/orders.ts`, đăng ký thẳng trên router chính `router.get("/orders", listOrders)`, `router.get("/orders/:orderId", getOrder)`, `router.post("/orders/:orderId/confirm", confirmOrder)`. Khi Workspace hỗ trợ thì chỉ cần thêm file router và đổi ba dòng này thành `router.route(...)`.

Quy tắc của `router.route()`:

- `prefix` theo cùng quy tắc path của route, có thể có param (`/customers/:customerId`, giá trị nằm trong `request.params` cùng param của route); `"/"` gắn route giữ nguyên path; route `/` của router con trả lời tại chính `prefix`. Webhook vẫn phải nằm dưới `/hooks/`, ví dụ `router.route("/hooks/payments", paymentsRouter)`.
- Router con phải tạo bằng `createRouter()`, không là chính router đó; mỗi router gắn tối đa 64 lần, gắn lồng sâu tối đa 8 cấp, tổng tối đa 2.048 route, mỗi router vẫn tối đa 256 route; một router có thể gắn dưới nhiều prefix và hai nhóm dùng chung prefix được nếu route không trùng. Vi phạm ném `ValidationError` khi gọi `route()` hoặc `toHandler()`.
- Route của router con được đọc khi gọi `toHandler()` và được chọn như thể đăng ký trên router chính tại vị trí gọi `route()`: route tĩnh trùng path được ưu tiên, còn lại route khớp đầu tiên xử lý. Route của router con bị route đứng trước trên router chính che mất thì Load profile báo `ROUTE_SHADOWED`.

### 3.4. Giữ phần nhỏ

- Import đúng thứ cần từ đúng file; tránh file "barrel" (`index.ts` re-export mọi thứ) và file tiện ích khổng lồ mà mọi điểm vào đều import, vì phần nào import nó cũng mang theo toàn bộ.
- Dữ liệu và bảng tra cứu lớn tách file riêng, chỉ điểm vào cần mới import; tạo chỉ mục từ dữ liệu đó trong hàm (khởi tạo lười), không ở cấp cao nhất khi dữ liệu import từ file JSON (mục 4).
- Code chạy lúc nạp của file dùng chung giữ ở mức khai báo hằng số và hàm.

## 4. Quy tắc "lệnh ở đầu file"

Code chạy lúc file được nạp là mọi câu lệnh ở cấp cao nhất của file (ngoài thân hàm và handler), kể cả lời gọi hàm từ đó.

**Được làm:** tính giá trị và tạo đối tượng của chính file: gọi hàm và static method của project (kể cả ở file khác) mà code của chúng cũng theo các quy tắc này, `.map()`, `.filter()`, vòng lặp, `if`, `try`, `throw`, hàm gọi ngay, `new Intl.Collator()`, đăng ký route trên router do chính file tạo, thêm vào mảng, đối tượng hoặc `Map` do chính file tạo (kể cả từ hàm của chính file), gọi `defineTrigger`/`defineJob`/`defineAction`.

**Không được làm:**

- Thay đổi gì bên ngoài file: ghi vào biến hoặc đối tượng của file khác (registry được import, đối tượng cấu hình, danh sách mà một hàm trả về), đăng ký vào registry dùng chung, sửa tham số của hàm, sửa biến của file khác qua một hàm của file đó (ví dụ `configure(...)`, `setLocale(...)`, `initX()` của thư viện hay module dùng chung).
- Sửa global hay đối tượng dựng sẵn: polyfill (`URL`, `TextEncoder`), vá prototype, gán lên `globalThis`.
- Cho kết quả khác nhau giữa các lần nạp: `Date.now()`, `new Date()` không đối số, `Intl.DateTimeFormat#format()` không có ngày, `Math.random()`, `performance`, `globalThis`, global do runtime định nghĩa, dịch vụ SDK (`fetch`, `crypto`, `limits`...).
- Thứ Cogover không kiểm được lúc publish (bị tính như thay đổi bên ngoài): gọi tham số, hàm bị gán nhiều lần, phương thức của giá trị không lần ra được là code của project hay kiểu built-in (chỉ nhận phương thức chỉ đọc thông dụng như `map`, `filter`, `includes`, `join`, `slice`, `split`, `trim`, `toString`), hàm `async` hay generator, `console.log()`, `Object.defineProperty()`, `Object.setPrototypeOf()`, `Object.create(prototype)`, `new Object(value)`, built-in gọi với đối số spread (`Math.max(...values)` thì được), phương thức hay chuyển đổi dữ liệu import từ file JSON, getter/setter/`toString`/`toJSON`/phương thức `Symbol` có tác động ra ngoài trong đối tượng hay class tạo lúc nạp.
- Lời gọi phương thức của đối tượng hay class của project (`Config.select()`, `registry.get()`) chỉ được tính là an toàn khi không chỗ nào trong project, kể cả trong handler, đưa đối tượng hay class đó ra chỗ khác hoặc sửa nó: truyền vào hàm, gán sang biến khác, spread, đặt vào đối tượng/mảng khác, trả về, ghi một thành viên (`registry.get = ...`), tạo thể hiện (`new Config()`), đọc `prototype`, chuyển thành chuỗi hay JSON.

Hậu quả khi vi phạm (Cogover đọc code lúc publish, không chạy):

| Vi phạm ở | Kết quả | Mã trong Load profile |
|---|---|---|
| Một file bất kỳ (trừ `src/main.ts`) | File đó và những gì nó import được nạp cùng mọi điểm vào: phần lớn hơn cần thiết | `REQUIRED_MODULES` (kèm câu lệnh và chuỗi `via`) |
| `src/main.ts` | Version không có phần nào, mọi điểm vào dùng module đầy đủ | `MAIN_TOP_LEVEL_EFFECT` |
| Ghi global/đối tượng built-in ở bất kỳ đâu, hoặc module đầy đủ đổi chúng lúc nạp | Không có phần | `PART_GLOBALS_MODIFIED` |

Cogover không bảo đảm bắt được mọi vi phạm. Giới hạn đã biết (thuộc trách nhiệm của khai báo `true`):

- `.name` của class hay hàm (cả `constructor.name`, `error.name`) có thể khác giữa module đầy đủ và phần khi hai file định nghĩa class hay hàm cấp module trùng tên: không dựa vào nó, tự đặt `name` ở chỗ cần (ví dụ `class OrderError extends Error { name = "OrderError"; }`).
- Giá trị không lần ra được (tham số, kết quả một lời gọi) có phương thức trùng tên phương thức built-in chỉ đọc được nhận (`map`, `filter`, `includes`, `join`...), hoặc có getter, setter, `Proxy`, iterator, `toString`, `valueOf`, `toJSON`, phương thức `Symbol` chạy khi code lúc nạp đọc hay chuyển đổi nó: không được kiểm.
- Đối tượng built-in bị sửa qua tên khác (`const p = Array.prototype; p.x = ...`) rồi hoàn tác trong lúc nạp: không được thấy.
- Code lúc nạp phụ thuộc ngày giờ chạy như vào ngày publish.

### 4.1. Ví dụ sai và đúng

Cấu hình thư viện lúc nạp (file khác import `formatMoney` có thể chạy khi chưa cấu hình):

```typescript
// SAI: src/lib/setup.ts, chạy khi file được nạp, sửa biến của src/lib/i18n.ts
import { configure } from "./i18n.js";
configure({ locale: "vi" });
```

```typescript
// ĐÚNG: khởi tạo lười, gọi từ handler cần nó
import { configure } from "./i18n.js";
let configured = false;
export function ensureI18n(): void {
  if (configured) return;
  configure({ locale: "vi" });
  configured = true;
}
// trong handler: ensureI18n(); rồi mới định dạng
```

Đăng ký vào registry dùng chung:

```typescript
// SAI: src/plugins/audit.ts đẩy vào mảng của file khác lúc nạp
import { registerPlugin } from "../lib/plugins.js";
registerPlugin(auditPlugin);
```

```typescript
// ĐÚNG: plugin chỉ export; file dùng tự dựng danh sách của chính nó
// src/plugins/audit.ts
export const auditPlugin = { name: "audit", run: (input: AuditInput) => { /* ... */ } };
// src/lib/run-plugins.ts
import { auditPlugin } from "../plugins/audit.js";
const PLUGINS = [auditPlugin];   // mảng do chính file này tạo
```

Kiểm tra quyền phải luôn có hiệu lực (sai ở đây làm một điểm vào chạy mà không có quy tắc quyền):

```typescript
// SAI: src/auth/setup.ts đặt quy tắc vào module dùng chung lúc nạp
import { setApproverRoles } from "./guard.js";
setApproverRoles(["ROLE_ID_EXAMPLE"]);
```

```typescript
// ĐÚNG: quy tắc là hằng số, handler truyền vào hàm kiểm tra
// src/auth/rules.ts
export const APPROVER_ROLE_IDS = ["ROLE_ID_EXAMPLE"] as const;
// trong handler
if (!hasAnyRole(invocation, APPROVER_ROLE_IDS)) return response.json({ error: "Forbidden" }, { status: 403 });
```

Polyfill và giá trị theo thời điểm nạp:

```typescript
// SAI
globalThis.structuredClone ??= (value) => JSON.parse(JSON.stringify(value));
const LOADED_AT = Date.now();
```

```typescript
// ĐÚNG: dùng hàm của project; lấy thời gian trong handler
export function deepCopy<T>(value: T): T { return JSON.parse(JSON.stringify(value)) as T; }
// trong handler: const now = Date.now();
```

Dữ liệu import từ JSON:

```typescript
// SAI: chuyển đổi dữ liệu JSON ở cấp cao nhất
import rates from "../data/rates.json";
const RATE_BY_CODE = new Map(rates.map((r) => [r.code, r.rate]));
```

```typescript
// ĐÚNG: dựng chỉ mục lười trong hàm (hoặc khai báo dữ liệu bằng file .ts với hằng số)
import rates from "../data/rates.json";
let rateByCode: Map<string, number> | undefined;
export function rateOf(code: string): number | undefined {
  rateByCode ??= new Map(rates.map((r) => [r.code, r.rate]));
  return rateByCode.get(code);
}
```

Được phép ở cấp cao nhất:

```typescript
const STATUS_LABELS = new Map([["draft", "Draft"], ["confirmed", "Confirmed"]]);
const ACTIVE = ["draft", "confirmed"].filter((s) => STATUS_LABELS.has(s));
export const ordersRouter = createRouter();
ordersRouter.get("/", listOrders);
```

### 4.2. Checklist rà soát

Dùng khi project sắp khai báo hoặc đã khai báo `entryPointParts: true`, cho mọi file trong `src/`:

- [ ] `src/main.ts` chỉ có import, các mảng export (`triggers`, `jobs`, `actions`), `createRouter()`, đăng ký route/`router.route()` trên router của chính nó và `export default router.toHandler()`.
- [ ] Không câu lệnh cấp cao nhất nào gọi `configure`/`setX`/`initX`/`register*`, ghi vào đối tượng import từ file khác, hay `push`/`set` vào mảng/`Map` của file khác.
- [ ] Không polyfill, vá prototype, gán `globalThis` ở bất kỳ đâu trong project (kể cả trong handler: `PART_GLOBALS_MODIFIED` xét cả project).
- [ ] Không `Date.now()`, `new Date()`, `Math.random()`, `console.log()`, `fetch`, `crypto`, `limits` hay dịch vụ SDK khác ở cấp cao nhất.
- [ ] Code kiểm tra quyền, role, Super Admin, policy nghiệp vụ không phụ thuộc trạng thái do file khác đặt lúc nạp; quy tắc là hằng số hoặc đọc trong handler.
- [ ] Không dựa vào `.name`, `constructor.name`, `error.name` của class/hàm; class lỗi tự đặt `name`.
- [ ] Không chuyển đổi dữ liệu import từ JSON ở cấp cao nhất; không dùng getter/setter/`Proxy`/`toJSON` có tác động ra ngoài trong đối tượng tạo lúc nạp.
- [ ] `requiredModules` của Load profile (mục 6) rỗng, hoặc từng mục đã được đọc và chắc chắn vô hại; `mainTopLevelEffect` là `null`.

## 5. Khai báo `entryPointParts`

| Cách khai báo | Ý nghĩa |
|---|---|
| `"entryPointParts": true` trong `cogover.json`, hoặc `cogover-dev publish --parts` | Tác giả xác nhận project tuân quy tắc mục 4; version chạy điểm vào bằng phần ở nơi nền tảng đã bật phần |
| `"entryPointParts": false`, hoặc `--no-parts` | Mọi lần thực thi của version dùng module đầy đủ |
| Không khai báo | Theo mặc định của nền tảng: hiện là module đầy đủ, trừ khi nền tảng quy định khác |

- Option của lệnh ghi đè `cogover.json` cho lần publish đó; chỉ áp cho backend (frontend: `PROJECT_CONFIG_INVALID` hoặc `CLI_USAGE`). Publish qua API: field `entryPointParts` (`true`/`false`, bỏ trống hoặc `null` là không khai báo; giá trị khác trả `400` `entryPointParts must be a boolean`).
- Khai báo gắn với version: đổi thì publish version mới. Phần vẫn được dựng và đo trong mọi trường hợp, nên Load profile của version không khai báo cũng cho biết phần mang lại gì. `effective` có thể đổi theo thiết lập của nền tảng mà không cần publish lại.
- Khai báo `true` nghĩa là tác giả chịu trách nhiệm về khác biệt nếu vi phạm: một điểm vào có thể chạy thiếu cấu hình mà file khác đặt lúc nạp, **kể cả kiểm tra quyền do project tự viết**. Cogover kiểm hết mức có thể lúc publish (file vi phạm được nạp cùng mọi điểm vào, các trường hợp nặng dùng module đầy đủ) nhưng không bảo đảm bắt hết.

Mặc định của skill:

1. **Luôn** tổ chức code theo mục 3.1–3.2 và mục 4, mọi phiên bản; router con (mục 3.3) chỉ khi đủ điều kiện mục 2.
2. Chỉ khai báo `true` khi đủ cả ba: đủ điều kiện phiên bản và Workspace (mục 2); đã rà checklist mục 4.2 trên commit sẽ publish (sub-agent Review bảo mật xác nhận ở bước 8 khi có code kiểm quyền); và module đủ lớn để có lợi (Load profile có `LOAD_TIME_HIGH`, `coldLoadMs` của module đầy đủ đáng kể so với `timeoutMs` của trigger before-change hay thời gian phản hồi mong muốn, hoặc nhiều điểm vào) hoặc người dùng yêu cầu. Nêu quyết định và lý do trong yêu cầu xác nhận publish và trong báo cáo bàn giao.
3. Cách làm an toàn: publish không khai báo, đọc Load profile (phần được dựng, `requiredModules`, `mainTopLevelEffect`, lý do của từng điểm vào); sửa tới khi sạch; rồi publish version mới với `--parts` (hoặc `true` trong `cogover.json`) và activate version đó sau khi kiểm thử lại. Xác nhận publish/activate theo bước 9 của skill như mọi version.

Không khai báo `true` khi:

- Chưa đủ điều kiện mục 2, hoặc không chắc project tuân quy tắc ("không chắc thì đừng khai báo").
- `requiredModules` có file sửa đối tượng của file khác, hoặc có lời gọi Cogover không phân giải được, mà chưa chứng minh được là vô hại.
- Project dùng thư viện cấu hình bằng lời gọi lúc nạp, plugin tự đăng ký, polyfill, hay quy tắc quyền đặt lúc nạp mà chưa chuyển sang khởi tạo lười.
- Code dựa vào `.name` của class/hàm, hoặc dựa vào ngày giờ lúc nạp.
- Module nhỏ, Load profile không có cảnh báo thời gian nạp và người dùng không yêu cầu: lợi ích không đáng so với trách nhiệm.

Gỡ khai báo: activate lại version trước, hoặc publish version mới với `--no-parts` rồi activate.

## 6. Đọc Load profile

`cogover-dev publish` (CLI từ `0.22.0`) in Load profile khi version `READY` và Workspace có đo; `--json` trả kèm `loadProfile`. API: field `loadProfile` trong response [Đọc một version](custom-backend-module-api-reference.md#đọc-một-version), ý nghĩa từng field ở mục [Hồ sơ nạp](custom-backend-module-api-reference.md#hồ-sơ-nạp). Ví dụ (số liệu tổng hợp):

```text
Published version 4 (TSVXXXXXXXXXXXX) is READY.
Load profile (measured at publish, warning threshold 1000 ms):
  Merged bundle: 1.6 MiB, cold load 1180 ms
  Shared SDK: 182.4 KiB, cold load 53 ms
  Parts: 6; entry points with a part: triggers 3/4, jobs 2/2, actions 1/1, routes 3/5
  Runs on: merged bundle (entryPointParts not declared)
    To run on the parts above, first read "Keep the module fast to load" in the @cogover/sdk usage guide: ...
  Modules in every part, because they run code while they load (1, 4.1 KiB of source with their imports):
    src/lib/setup.ts:3 changes a module-level variable from a function: configure({ locale: "vi" });
      via src/lib/setup.ts:3: configure({ locale: "vi" });
      via src/lib/i18n.ts:4: locale = options.locale;
  Slowest parts (cold load without the SDK):
    210 ms  src/jobs/order-sync.ts (380.2 KiB; 1 job)
    95 ms  src/routers/orders.ts (120.4 KiB; 3 routes)
    60 ms  src/triggers/order-credit-check.ts (40.0 KiB; 1 trigger)
  Entry points without a part of their own file (1):
    trigger order_inline -> merged bundle: It is not exported from a file other than src/main.ts. [NOT_LOCATED]
    Hint (NOT_LOCATED): Define and export each entry point from its own file, then collect it in src/main.ts.
  Warnings (3):
    LOAD_TIME_HIGH: The merged bundle took 1180 ms to load (threshold 1000 ms).
      Hint: Put each group of routes in a router of its own file (createRouter() and its routes only) and mount it in src/main.ts with router.route(prefix, router).
    REQUIRED_MODULES: 1 module(s) run code while they load, so every part includes them (...).
      Hint: Move code that runs while a module loads into handlers, or into files that only the entry points needing it import.
    ENTRY_POINTS_IN_BUNDLE: 1 entry point(s) run on the merged bundle: order_inline.
Next: cogover-dev activate TSVXXXXXXXXXXXX
```

- `Merged bundle` / `Shared SDK`: kích thước và thời gian nạp nguội của module đầy đủ và của SDK. Số đo dao động khoảng ±25% giữa các lần, có thể chậm tới khoảng gấp đôi khi Workspace tải cao: so xu hướng, không so tuyệt đối từng ms.
- `Parts`: số phần và, theo từng loại, số điểm vào có phần trên tổng (`routes 3/5`: hai route còn đăng ký thẳng trên router chính).
- `Runs on:` cho biết version đang chạy bằng gì:

| Dòng `Runs on:` | Nghĩa và việc cần làm |
|---|---|
| `entry-point parts (entryPointParts: true at publish)` | Đang chạy bằng phần theo khai báo |
| `entry-point parts (the platform default)` | Không khai báo nhưng nền tảng mặc định chạy bằng phần: project vẫn phải tuân mục 4 |
| `entry-point parts for HTTP routes (...); triggers, jobs and actions on the merged bundle` (hoặc ngược lại) | Nền tảng mới bật phần cho một loại điểm vào (`effectiveFor`) |
| `merged bundle (entryPointParts not declared)` | Phần đã dựng nhưng chưa khai báo; quyết định theo mục 5 |
| `merged bundle (entryPointParts: false at publish)` | Theo khai báo `false` |
| `merged bundle (entry-point parts are not enabled on this platform yet)` | Đã khai báo `true` nhưng nền tảng chưa bật phần; không cần sửa code |
| `merged bundle (no part could be built)` | Không dựng được phần: xem lý do và cảnh báo |
| Không có dòng `Runs on:` | Workspace chưa hỗ trợ khai báo (mục 2) |

- `Modules in every part` (`requiredModules`): file vi phạm mục 4, kèm câu lệnh cấp cao nhất và chuỗi `via` tới chỗ gây thay đổi. Sửa theo mục 4.1 hoặc chuyển vào file mà chỉ điểm vào cần nó import.
- `Slowest parts`: phần nạp chậm nhất (không tính SDK). Phần lớn: giảm import, tách bảng dữ liệu, bỏ barrel (mục 3.4).
- `No part, src/main.ts runs code while it loads` (`mainTopLevelEffect`): đưa câu lệnh đó ra khỏi `src/main.ts`.

Lý do (`reason` của `entryPoints[]`) và cảnh báo (`warnings[].code`) thường gặp:

| Mã | Cách xử lý |
|---|---|
| `NOT_LOCATED` | Điểm vào viết trong `src/main.ts` hoặc không export từ file định nghĩa nó: chuyển sang file riêng, export, gom lại trong `src/main.ts` (mục 3.2) |
| `MAIN_TOP_LEVEL_EFFECT` | `src/main.ts` tác động ra ngoài lúc nạp (xem `mainTopLevelEffect`): giữ `src/main.ts` chỉ gồm import, mảng export và đăng ký route; chuyển câu lệnh vào handler hoặc file mà điểm vào cần nó import |
| `REQUIRED_MODULES` | Đọc từng mục `requiredModules` (`file`, `line`, `statement`, `reason`, `via`): chuyển code lúc nạp vào handler (khởi tạo lười) hoặc vào file chỉ điểm vào cần mới import. Còn mục chưa chắc vô hại thì không khai báo `true` |
| `PART_GLOBALS_MODIFIED` | Project ghi vào global/đối tượng built-in (`message` nêu file và dòng): bỏ polyfill, vá prototype, gán `globalThis`; nếu bắt buộc thì làm trong handler. Còn lại thì mọi điểm vào dùng module đầy đủ |
| `PART_GLOBAL_STATE_UNKNOWN` | Code lúc nạp đưa quá nhiều vào global để so: thu nhỏ code lúc nạp |
| `LOAD_TIME_HIGH` | Module đầy đủ (hoặc SDK cộng một phần) nạp lâu hơn `thresholdMillis`. Module đầy đủ: tách điểm vào và nhóm route ra file riêng/router con. Một phần (`message` bắt đầu bằng `Part`): import ít hơn từ file dùng chung, xử lý `requiredModules` |
| `ENTRY_POINTS_IN_BUNDLE` | Liệt kê điểm vào dùng module đầy đủ; xử lý theo `reason` của từng điểm vào |
| `ROUTE_SHADOWED` | Route của router con không bao giờ được gọi vì route đứng trước trên router chính trả lời cùng request: đổi thứ tự hoặc đổi path |
| `PART_NOT_SMALLER` | File import gần như cả module: import ít hơn từ file dùng chung |
| `ROUTE_MATCH_MISMATCH`, `PART_REJECTED`, `PART_ORDER_MISMATCH`, `PARTS_LIMIT`, `PARTS_TIMEOUT`, `PARTS_BUILD_FAILED`, `PARTS_PLAN_MISMATCH` | Điểm vào bị ảnh hưởng dùng module đầy đủ; không cần sửa code để module chạy đúng. Lặp lại qua nhiều lần publish thì báo người dùng kèm mã và `message` |

`level` của điểm vào là `KIND` khi nó dùng phần chung của mọi trigger, job hoặc action của version, `BUNDLE` khi dùng module đầy đủ. Load profile chỉ để tham khảo: cảnh báo không bao giờ làm publish thất bại.

Publish chậm hơn trước vì dựng và đo phần: vài giây với module nhỏ, khoảng 10–20 giây với module lớn, tối đa 45 giây; quá thời gian đó version vẫn được publish nhưng không có phần (`PARTS_TIMEOUT`). Đặt thời gian chờ publish có dư địa.

## 7. Giới hạn kích thước

Tổng dung lượng source file mà `src/main.ts` import tới tối đa **6 MiB**, bundle JavaScript sau khi compile vẫn tối đa **4 MiB** (`TYPESCRIPT_COMPILE_FAILED`); bảng đầy đủ ở mục [Giới hạn kích thước](custom-backend-module-api-reference.md#giới-hạn-kích-thước). Tách file không làm module đầy đủ nhỏ đi: dữ liệu lớn vẫn tính vào cả hai giới hạn.

## 8. Kiểm thử và bàn giao

- Unit test không đổi: hàm thuần và handler import từ file của chúng. Chạy `npm test`/máy chủ local trước publish như thường (`defineTrigger`/`defineJob`/`defineAction` validate khi module được nạp).
- Sau publish: lưu Load profile (output CLI hoặc `loadProfile` của version) vào bằng chứng; kiểm thử chức năng chạy trên đúng version sẽ activate (đã khai báo hay chưa). Đổi khai báo là version mới: chạy lại ca chức năng chính, đặc biệt ca từ chối quyền và trigger before-change, trên version chạy bằng phần.
- Đo hiệu năng: so `coldLoadMs` của module đầy đủ với phần của điểm vào cần đo, và thời gian phản hồi lượt gọi đầu tiên sau activate với các lượt sau, theo [Kiểm thử hiệu năng](performance-testing.md).
- Bàn giao: phiên bản SDK/CLI, Workspace hỗ trợ hay chưa (bằng chứng), bố cục `src/`, có dùng `router.route()` không, khai báo `entryPointParts` (`true`/`false`/không khai báo) và lý do, dòng `Runs on:`, kích thước và `coldLoadMs` của module đầy đủ, số phần và độ phủ, `requiredModules` còn lại, cảnh báo còn lại và lý do chấp nhận.
