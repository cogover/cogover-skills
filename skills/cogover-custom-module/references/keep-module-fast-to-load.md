# Giữ module nạp nhanh: tách phần theo điểm vào

Snapshot tài liệu `@cogover/sdk` `0.18.0`, Cogover Dev CLI `0.22.0` và Backend API Reference ngày `2026-11-22`. Đọc khi tổ chức source của Custom Backend Module (mọi project), quyết định có khai báo `entryPointParts` hay không, đọc **Load profile** sau khi publish, và khi review code của project đã khai báo `entryPointParts: true`. Contract chi tiết: mục [Tổ chức route theo nhóm](cogover-sdk-usage-guide.md#tổ-chức-route-theo-nhóm) và [Giữ module nạp nhanh](cogover-sdk-usage-guide.md#giữ-module-nạp-nhanh) của SDK usage guide, [`router.route()`](cogover-sdk-api-reference.md#routerrouteprefix-string-router-scriptroutertschema-scriptroutertschema) của SDK API reference, [Hồ sơ nạp](custom-backend-module-api-reference.md#hồ-sơ-nạp) của Backend API Reference, [Phần theo điểm vào và Load profile](cli-session-and-delivery.md#phần-theo-điểm-vào-và-load-profile) của CLI reference. Tên file, Object và số liệu bên dưới chỉ minh hoạ.

## 1. Vì sao

- Mọi lần thực thi (HTTP route, record trigger, background job, Custom Module Action) bắt đầu bằng việc nạp code của module trong sandbox. Module lớn nạp lâu, rõ nhất ở lượt gọi đầu tiên sau khi publish hoặc sau một thời gian rảnh. Thời gian nạp sát giới hạn thời gian của lần thực thi để lại rất ít thời gian cho handler, đặc biệt với trigger before-change (`timeoutMs` từ 100 đến 3.000 ms, mặc định 2.000 ms; mọi trigger before-change của một thao tác ghi dùng chung tổng 8 giây; hết giờ thì thao tác ghi bị chặn).
- Khi publish, ngoài module biên dịch đầy đủ (*merged bundle*), Cogover dựng thêm các module nhỏ gọi là **phần** (*part*): trigger, job hoặc action được định nghĩa và export từ file riêng (không phải `src/main.ts`) có phần chỉ chứa code file đó cần; router con tạo trong file riêng và gắn bằng `router.route()` có phần cho các route của nó. `@cogover/sdk` là module dùng chung, nạp trước phần. Một lần thực thi chạy bằng phần thì chỉ nạp SDK và phần của nó.
- Module đầy đủ luôn được dựng và là đường dự phòng: điểm vào không có phần, phần không dựng được hoặc version không chạy bằng phần đều dùng module đầy đủ như trước.
- Lợi ích phụ thuộc kích thước module: một lần chạy bằng phần vẫn phải nạp SDK dùng chung (thường vài chục tới khoảng 100 ms). Module nhỏ (bundle đầy đủ vài trăm KiB) nạp đầy đủ chỉ mất xấp xỉ thời gian nạp SDK, nên chạy bằng phần gần như không nhanh hơn; ví dụ đo thật với bundle khoảng 177 KiB: bundle đầy đủ 83–104 ms, chạy bằng phần = SDK 63–87 ms + phần 4 ms. Lợi ích chỉ rõ khi module lớn dần; code đã tổ chức theo mục 3 từ đầu thì lúc đó chỉ cần khai báo (mục 5).
- Kích thước cũng quan trọng, không chỉ thời gian nạp: một phần hay module đầy đủ được nạp nhiều lần (vài trăm lượt gọi trở lên, như trigger hay route được gọi dày) được môi trường chạy tối ưu thêm. Với code lớn, việc này tốn nhiều bộ nhớ tới mức môi trường chạy của Workspace bị khởi động lại, và lượt gọi kế tiếp của Workspace nạp nguội lại từ đầu. Vì vậy Load profile cảnh báo khi một phần từ **400 KB** (`PART_SIZE_HIGH`) hoặc module đầy đủ từ **500 KB** (`BUNDLE_SIZE_HIGH`); cách giữ kích thước ở mục 3.5.
- Chạy bằng phần chỉ an toàn khi code chạy lúc file được nạp không tác động ra ngoài file đó (mục 4), vì phần chỉ nạp một tập file. Vì vậy tác giả phải khai báo (mục 5); không khai báo thì theo mặc định của nền tảng, hiện là module đầy đủ.

## 2. Điều kiện phiên bản và môi trường

Workspace luôn build version bằng `@cogover/sdk` của chính Runtime của nó (ZIP publish chỉ chứa `src/`). `@cogover/sdk` cài trong project chỉ phục vụ kiểu khi typecheck, chạy local và unit test. Vì vậy SDK cục bộ mới hơn Runtime cho typecheck đạt nhưng publish vẫn thất bại khi code dùng API Runtime chưa có, như `router.route()`: phải kiểm cả phiên bản cục bộ lẫn Workspace.

| Việc | Cần | Chưa đủ điều kiện thì |
|---|---|---|
| Mỗi trigger/job/action một file, `src/main.ts` chỉ gom lại; route xử lý bằng hàm ở file riêng; quy tắc "lệnh ở đầu file" | Không cần gì: mọi phiên bản SDK, CLI, Workspace | Vẫn làm: vô hại và sẵn sàng cho khi Workspace hỗ trợ |
| `router.route(prefix, childRouter)` | `@cogover/sdk` từ `0.18.0` trong project (để typecheck và chạy local) **và** Workspace hỗ trợ | Không dùng: đăng ký route thẳng trên router chính (mục 3.3). SDK cục bộ cũ: typecheck báo `Property 'route' does not exist`. Workspace chưa hỗ trợ: publish thất bại dù typecheck đạt |
| Khai báo `entryPointParts` (`cogover.json`, `cogover-dev publish --parts`/`--no-parts`) | Dev CLI từ `0.22.0` **và** Workspace hỗ trợ | Không khai báo. CLI cũ bỏ qua key này trong `cogover.json` (không gửi khai báo) và từ chối `--parts`/`--no-parts` với `CLI_USAGE`; Workspace chưa hỗ trợ bỏ qua khai báo |
| Xem Load profile | Workspace hỗ trợ; CLI từ `0.22.0` để `publish` in ra | CLI cũ: đọc `loadProfile` qua API [Đọc một version](custom-backend-module-api-reference.md#đọc-một-version) |

`router.route()`, khai báo `entryPointParts` và Load profile thuộc cùng một bản Runtime: Workspace có Load profile thì hỗ trợ cả ba, không có thì không hỗ trợ cái nào.

Thủ tục kiểm (làm theo thứ tự, dừng ở bước có kết luận):

1. Công cụ cục bộ: `npm ls @cogover/sdk`, `cogover-dev --version`; bản phát hành mới nhất: `npm view @cogover/sdk version`, `npm view @cogover/dev-cli version`. Nâng project lên SDK từ `0.18.0` và CLI từ `0.22.0` khi npm đã có (không cài từ nguồn khác npm). Kết luận riêng từng công cụ: SDK cục bộ dưới `0.18.0` → không dùng `router.route()`; CLI dưới `0.22.0` → không khai báo `entryPointParts`. Vẫn làm bước 2–3 để biết Workspace có Load profile.
2. Workspace, bằng chứng có sẵn (chỉ đọc): liệt kê version bằng `POST /api/v1/ts-projects/{projectId}/versions/list` của project này hoặc của một backend Project khác trên cùng Workspace (liệt kê module theo [Backend API Reference](custom-backend-module-api-reference.md#liệt-kê-module)), rồi đọc chi tiết một version bằng `POST /api/v1/ts-projects/{projectId}/versions/{versionId}` và xem JSON thô của response (ví dụ `jq 'has("loadProfile")'`; không dùng công cụ tự bỏ field `null`):
   - Response chi tiết **có** field `loadProfile`, kể cả khi giá trị là `null` → **Workspace hỗ trợ**, sang bước 4. Workspace chưa hỗ trợ không trả field này.
   - Response **không có** field `loadProfile` → **chưa hỗ trợ**, sang bước 4.
   - Chưa có version nào để đọc → sang bước 3.
3. Workspace, bằng lần publish kế tiếp: viết theo cách cũ (route đăng ký thẳng trên router chính, không `router.route()`, không khai báo `entryPointParts`) và publish như bình thường ở bước 9 của skill (lần publish đầu của project mới chính là lần kiểm này; vẫn xin xác nhận như mọi lần publish, chưa cần activate). Khi version `READY`, đọc chi tiết version như bước 2 và áp cùng quy tắc. CLI từ `0.22.0` in khối `Load profile` kèm dòng `Runs on:` khi có profile; CLI cũ không in kể cả khi Workspace hỗ trợ, nên luôn kết luận bằng API.

`loadProfile` là `null` (field vẫn có mặt) trong các trường hợp nguồn nêu: version chưa build xong; version publish trước khi Workspace có hồ sơ nạp (nên mọi version cũ đều `null`); và khi không có hồ sơ cho version đó (trường hợp hiếm, ví dụ không lưu hoặc đọc được hồ sơ). Version mới `READY` trên Workspace hỗ trợ bình thường luôn có `loadProfile` khác `null`, kể cả khi không dựng được phần nào (khi đó `parts` rỗng và có mã lý do). Version mới `READY` mà vẫn `null`: đọc lại sau vài giây; còn `null` thì publish lại một lần; lần đó vẫn `null` thì coi version không có hồ sơ: Workspace vẫn hỗ trợ `router.route()`, nhưng không khai báo `entryPointParts` (bảng mục 5.1 cần Load profile) và báo người dùng.
4. Hành động:
   - Workspace hỗ trợ và SDK cục bộ từ `0.18.0`: chuyển route sang router con (mục 3.3). Workspace hỗ trợ và CLI từ `0.22.0`: quyết định khai báo theo bảng mục 5.1. Thay đổi nào cũng publish thành version mới.
   - Workspace chưa hỗ trợ: giữ cách cũ, không `router.route()`, không khai báo, dù SDK/CLI cục bộ đã mới; vẫn tổ chức file theo mục 3.1–3.2 và mục 4. Ghi kết luận và bằng chứng trong báo cáo bàn giao. Khi đủ điều kiện về sau, chuyển route sang router con chỉ là thay đổi nhỏ ở `src/main.ts` và các file router.

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
import { NotFoundError, ValidationError, type CogoverRecordId, type ScriptHandler } from "@cogover/sdk";

const ORDER_FIELDS = ["name", "status", "amount"] as const;
const ID_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;
type Handler = ScriptHandler<unknown, unknown>;

function orderIdOf(value: string | undefined): CogoverRecordId {
  if (!value || !ID_PATTERN.test(value)) throw new ValidationError("A valid orderId is required");
  return value as CogoverRecordId;
}

export const listOrders: Handler = async ({ data }) => {
  const page = await data.object("order").records.list({ fields: ORDER_FIELDS, limit: 50 });
  return { orders: page.items, nextCursor: page.nextCursor ?? null };
};

export const getOrder: Handler = async ({ request, data }) => {
  const orderId = orderIdOf(request.params.orderId);
  const order = await data.object("order").records.get(orderId, { fields: ORDER_FIELDS });
  if (!order) throw new NotFoundError("order", orderId);
  return { order };
};

export const confirmOrder: Handler = async ({ request, data }) => {
  const orderId = orderIdOf(request.params.orderId);
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

### 3.5. Giữ kích thước phần và module đầy đủ dưới ngưỡng

Ngưỡng cảnh báo của Load profile (cảnh báo không làm publish thất bại):

| Mã | Khi nào | Đo bằng |
|---|---|---|
| `PART_SIZE_HIGH` | Một phần lớn bằng hoặc hơn **400 KB** | `parts[].bytes`: phần không tính SDK dùng chung, đã gồm `requiredModules` |
| `BUNDLE_SIZE_HIGH` | Module đầy đủ lớn bằng hoặc hơn **500 KB** | `bundle.bytes`: gồm cả `@cogover/sdk` (khoảng 190 KB), nên code của project chỉ còn khoảng 310 KB trước khi chạm ngưỡng |

- Đơn vị: KB thập phân (1 KB = 1.000 byte), đúng như trong `message`. CLI in kích thước theo KiB (1 KiB = 1.024 byte): `390.6 KiB` đã là 400 KB, `488.3 KiB` là 500 KB. So bằng byte trong JSON khi sát ngưỡng.
- Ngưỡng do Workspace cấu hình: đọc `loadProfile.partSizeThresholdBytes` và `bundleSizeThresholdBytes` (`0` là Workspace không cảnh báo loại đó). Workspace có Load profile nhưng chưa có hai field này thì chưa có cảnh báo kích thước: tự so `parts[].bytes` và `bundle.bytes` với 400.000 và 500.000 byte.
- `BUNDLE_SIZE_HIGH` không báo khi module đầy đủ chỉ còn là đường dự phòng: version khai báo `entryPointParts: true`, mọi trigger/job/action và mọi route đều có phần, nền tảng đang chạy cả hai loại bằng phần (`effectiveFor`), và `src/main.ts` không export default một handler không phải `router.toHandler()` (handler đó luôn chạy bằng module đầy đủ). Không khai báo hoặc khai báo `false` thì vẫn báo, vì khi đó mọi lần thực thi nạp module đầy đủ.
- Cộng dồn: cảnh báo xét từng phần riêng, nhưng nhiều phần cỡ vừa cùng được gọi dày cũng cộng dồn: trong phép đo, hai phần khoảng 400 KB cùng nóng đã chạm giới hạn ở một trong hai lần, ba phần thì chạm ở mọi lần. Phần của điểm vào gọi dày (trigger, route chính) càng nhỏ càng tốt; hai phần trở lên từ khoảng 300 KB cùng được gọi dày thì xử lý như đã có cảnh báo.

Bố cục file quyết định kích thước phần, vì phần chứa mọi thứ file khai báo điểm vào import tới:

- Không gom điểm vào thành một file "registry" (ví dụ `triggers/registry.ts` import trigger của mọi Object rồi export một mảng; một file router đăng ký route của mọi nhóm): mọi điểm vào trong file dùng chung một phần chứa code của tất cả. Ví dụ đo thật: một file registry gom trigger của nhiều Object cho phần 616 KB, một file chứa nhiều job cùng hàm dựng dữ liệu của chúng cho phần 455 KB. Mỗi điểm vào (hoặc nhóm nhỏ cần cùng code) một file; chỉ `src/main.ts` gom lại.
- Nhóm route có phần từ 400 KB: tách thành nhiều router con theo nhóm hàm xử lý, mỗi file router chỉ import hàm xử lý của nhóm đó (mục 3.3).
- Import hàm từ đúng file của nó, không qua barrel; file tiện ích lớn tách theo chủ đề để mỗi điểm vào chỉ kéo theo phần nó dùng; thư viện lớn gói vào bundle chỉ import ở file điểm vào cần nó.
- Xử lý `requiredModules` (mục 4.1): các file đó nằm trong **mọi** phần, nên chúng làm mọi phần lớn lên cùng lúc.
- Dữ liệu viết thành object hay mảng literal tốn bộ nhớ khi tối ưu như code cùng kích thước (đo: khoảng 600 KB object literal tốn gần bằng code thật); một chuỗi lớn hay thân hàm lớn thì tốn ít hơn nhiều. Cảnh báo chỉ đo byte nên báo như nhau cho cả ba. Đây là sự thật để cân nhắc, không phải mẹo: đừng đổi dữ liệu sang chuỗi chỉ để giảm cảnh báo nếu code khó đọc hay khó kiểm hơn. Bảng tra cứu lớn ưu tiên đưa ra Object hay file của Workspace và đọc khi cần; giữ trong code thì tách file riêng chỉ điểm vào cần mới import, và ghi lý do chấp nhận cảnh báo còn lại vào bàn giao.

Đọc kích thước sau publish: CLI in kích thước module đầy đủ (`Merged bundle`), 3 phần chậm nhất kèm KiB (`Slowest parts`) và các dòng `PART_SIZE_HIGH: Part <số> (<file>) is <x> KB (threshold 400 KB): ...`; danh sách đầy đủ ở `loadProfile.parts[]` (`no`, `source`, `bytes`) qua API hoặc `cogover-dev publish --json`. `Slowest parts` xếp theo thời gian nạp, không theo kích thước, nên phần lớn nhất có thể không có trong đó.

Kiểm trước khi bàn giao:

- [ ] Không có `PART_SIZE_HIGH`; hoặc có lý do chấp nhận (phần đó ít được gọi) đã ghi vào bàn giao.
- [ ] Không có `BUNDLE_SIZE_HIGH`; hoặc module đã tổ chức theo điểm vào và quyết định khai báo theo mục 5.1, phần còn lại ghi lý do.
- [ ] Không có hai phần trở lên từ khoảng 300 KB cùng phục vụ điểm vào gọi dày.
- [ ] Không có file registry hay router gom điểm vào của nhiều nhóm.

## 4. Quy tắc "lệnh ở đầu file"

Code chạy lúc file được nạp là mọi câu lệnh ở cấp cao nhất của file (ngoài thân hàm và handler), kể cả lời gọi hàm từ đó.

**Được làm:** tính giá trị và tạo đối tượng của chính file: gọi hàm và static method của project (kể cả ở file khác) mà code của chúng cũng theo các quy tắc này, `.map()`, `.filter()`, vòng lặp, `if`, `try`, `throw`, hàm gọi ngay, `new Intl.Collator()`, đăng ký route trên router do chính file tạo, thêm vào mảng, đối tượng hoặc `Map` do chính file tạo (kể cả từ hàm của chính file), gọi `defineTrigger`/`defineJob`/`defineAction`.

**Không được làm:**

- Thay đổi gì bên ngoài file: ghi vào biến hoặc đối tượng của file khác (registry được import, đối tượng cấu hình, danh sách mà một hàm trả về), đăng ký vào registry dùng chung, sửa tham số của hàm, sửa biến của file khác qua một hàm của file đó (ví dụ `configure(...)`, `setLocale(...)`, `initX()` của thư viện hay module dùng chung).
- Sửa global hay đối tượng dựng sẵn: polyfill (`URL`, `TextEncoder`), vá prototype, gán lên `globalThis`.
- Cho kết quả khác nhau giữa các lần nạp: `Date.now()`, `new Date()` không đối số, `Intl.DateTimeFormat#format()` không có ngày, `Math.random()`, `performance`, `globalThis`, global do runtime định nghĩa, dịch vụ SDK (`fetch`, `crypto`, `limits`...).
- Thứ Cogover không kiểm được lúc publish (bị tính như thay đổi bên ngoài): gọi tham số, hàm bị gán nhiều lần, phương thức của giá trị không lần ra được là code của project hay kiểu built-in (chỉ nhận phương thức chỉ đọc thông dụng như `map`, `filter`, `includes`, `join`, `slice`, `split`, `trim`, `toString`), hàm `async` hay generator, `console.log()`, `Object.defineProperty()`, `Object.setPrototypeOf()`, `Object.create(prototype)`, `new Object(value)`, built-in gọi với đối số spread (`Math.max(...values)` thì được), phương thức hay chuyển đổi dữ liệu import từ file JSON, getter/setter/`toString`/`toJSON`/phương thức `Symbol` có tác động ra ngoài trong đối tượng hay class tạo lúc nạp.
- Lời gọi phương thức của đối tượng hay class của project (`Config.select()`, `registry.get()`) chỉ được tính là an toàn khi không chỗ nào trong project, kể cả trong handler, đưa đối tượng hay class đó ra chỗ khác hoặc sửa nó: truyền vào hàm, gán sang biến khác, spread, đặt vào đối tượng/mảng khác, trả về, ghi một thành viên (`registry.get = ...`), tạo thể hiện (`new Config()`), đọc `prototype`, chuyển thành chuỗi hay JSON.

Hậu quả của vi phạm mà Cogover **phát hiện** được lúc publish (đọc code, không chạy). Cả ba trường hợp đều an toàn về hành vi; cái giá chỉ là kích thước và thời gian nạp:

| Vi phạm ở | Kết quả | Mã trong Load profile |
|---|---|---|
| Một file bất kỳ trừ `src/main.ts` (kể cả `Date.now()`, `Math.random()`, `console.log()` hay lời gọi không phân tích được ở cấp cao nhất của file đó) | File đó cùng những gì nó import được đưa vào **mọi** phần, đúng thứ tự nạp như module đầy đủ, nên hiệu ứng lúc nạp của nó vẫn xảy ra ở mọi điểm vào. Hành vi giữ nguyên; phần to hơn và nạp chậm hơn | `REQUIRED_MODULES` (`requiredModules` kèm câu lệnh và chuỗi `via`, `requiredBytes`) |
| `src/main.ts` (cùng các loại câu lệnh trên, kể cả `Date.now()` hay giá trị không tất định ở cấp cao nhất của `src/main.ts`) | Version không có phần nào, mọi điểm vào dùng module đầy đủ | `MAIN_TOP_LEVEL_EFFECT` (`mainTopLevelEffect`) |
| Ghi global/đối tượng built-in ở bất kỳ đâu trong project, kể cả trong handler, hoặc module đầy đủ đổi chúng lúc nạp | Version không có phần nào | `PART_GLOBALS_MODIFIED` |

Rủi ro thật của khai báo `true` nằm ở vi phạm Cogover **không phát hiện** được: khi đó file gây hiệu ứng không được đưa vào mọi phần, và một điểm vào có thể chạy thiếu cấu hình hay quy tắc (kể cả quy tắc quyền) mà file đó đặt lúc nạp. Cogover không bảo đảm bắt được mọi vi phạm. Giới hạn đã biết (thuộc trách nhiệm của khai báo `true`, là thứ checklist mục 4.2 phải tìm):

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
export interface AuditInput { recordId: string }
export const auditPlugin = { name: "audit", run: (input: AuditInput): string => `audit:${input.recordId}` };
```

```typescript
// src/lib/run-plugins.ts
import { auditPlugin } from "../plugins/audit.js";

const PLUGINS = [auditPlugin];   // mảng do chính file này tạo
export function runPlugins(recordId: string): string[] {
  return PLUGINS.map((plugin) => plugin.run({ recordId }));   // chạy trong hàm, không lúc nạp
}
```

Kiểm tra quyền phải luôn có hiệu lực (sai ở đây làm một điểm vào chạy mà không có quy tắc quyền):

```typescript
// SAI: src/auth/setup.ts đặt quy tắc vào module dùng chung lúc nạp
import { setApproverRoles } from "./guard.js";
setApproverRoles(["ROLE_ID_EXAMPLE"]);
```

```typescript
// ĐÚNG: quy tắc là hằng số, handler truyền vào phép kiểm tra
// src/auth/rules.ts
export const APPROVER_ROLE_IDS: readonly string[] = ["ROLE_ID_EXAMPLE"];
```

```typescript
// src/handlers/approve.ts
import type { ScriptHandler } from "@cogover/sdk";
import { APPROVER_ROLE_IDS } from "../auth/rules.js";

export const approveOrder: ScriptHandler<unknown, unknown> = async ({ invocation, response }) => {
  const roles = invocation.user?.membership.roles ?? [];
  if (!roles.some((role) => APPROVER_ROLE_IDS.includes(role.id))) {
    return response.json({ error: "Forbidden" }, { status: 403 });
  }
  return { approved: true };
};
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
// SAI: chuyển đổi dữ liệu JSON ở cấp cao nhất (import JSON cần "resolveJsonModule": true trong tsconfig)
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
// src/lib/status.ts: các câu lệnh cấp cao nhất được phép
const STATUS_LABELS = new Map([["draft", "Draft"], ["confirmed", "Confirmed"]]);
export const ACTIVE_STATUSES = ["draft", "confirmed"].filter((status) => STATUS_LABELS.has(status));
export function labelOf(status: string): string {
  return STATUS_LABELS.get(status) ?? status;
}
```

Đăng ký route trên router do chính file tạo (file router ở mục 3.3) và gọi `defineTrigger`/`defineJob`/`defineAction` cũng được phép.

### 4.2. Checklist rà soát

Dùng khi project sắp khai báo hoặc đã khai báo `entryPointParts: true`, cho mọi file trong `src/`:

- [ ] `src/main.ts` chỉ có import, các mảng export (`triggers`, `jobs`, `actions`), `createRouter()`, đăng ký route/`router.route()` trên router của chính nó và `export default router.toHandler()`.
- [ ] Không câu lệnh cấp cao nhất nào gọi `configure`/`setX`/`initX`/`register*`, ghi vào đối tượng import từ file khác, hay `push`/`set` vào mảng/`Map` của file khác.
- [ ] Không polyfill, vá prototype, gán `globalThis` ở bất kỳ đâu trong project (kể cả trong handler: `PART_GLOBALS_MODIFIED` xét cả project).
- [ ] Không `Date.now()`, `new Date()`, `Math.random()`, `console.log()`, `fetch`, `crypto`, `limits` hay dịch vụ SDK khác ở cấp cao nhất.
- [ ] Code kiểm tra quyền, role, Super Admin, policy nghiệp vụ không phụ thuộc trạng thái do file khác đặt lúc nạp; quy tắc là hằng số hoặc đọc trong handler.
- [ ] Không dựa vào `.name`, `constructor.name`, `error.name` của class/hàm; class lỗi tự đặt `name`.
- [ ] Không chuyển đổi dữ liệu import từ JSON ở cấp cao nhất; không dùng getter/setter/`Proxy`/`toJSON` có tác động ra ngoài trong đối tượng tạo lúc nạp.
- [ ] Mục đích của checklist là tìm vi phạm **không** có trong `requiredModules`/cảnh báo của Load profile (đặc biệt code cấu hình quyền, registry, khởi tạo thư viện, và các giới hạn đã biết ở mục 4). Mục đã có trong `requiredModules` không cần chứng minh gì thêm: chúng đã được đưa vào mọi phần.
- [ ] Mỗi file trong `requiredModules` cho thấy project có kiểu code cấu hình lúc nạp: tìm code cùng kiểu ở file khác mà Load profile không liệt kê (ví dụ cùng gọi một hàm `configure`/`register` qua tham số hay biến được gán lại) và sửa theo mục 4.1.
- [ ] `mainTopLevelEffect` là `null` và không có `PART_GLOBALS_MODIFIED` (nếu có thì version không có phần, khai báo không có tác dụng).

## 5. Khai báo `entryPointParts`

| Cách khai báo | Ý nghĩa |
|---|---|
| `"entryPointParts": true` trong `cogover.json`, hoặc `cogover-dev publish --parts` | Tác giả xác nhận project tuân quy tắc mục 4; version chạy điểm vào bằng phần ở nơi nền tảng đã bật phần |
| `"entryPointParts": false`, hoặc `--no-parts` | Mọi lần thực thi của version dùng module đầy đủ |
| Không khai báo | Theo mặc định của nền tảng: hiện là module đầy đủ, trừ khi nền tảng quy định khác |

- Option của lệnh ghi đè `cogover.json` cho lần publish đó; chỉ áp cho backend (frontend: `PROJECT_CONFIG_INVALID` hoặc `CLI_USAGE`). Publish qua API: field `entryPointParts` (`true`/`false`, bỏ trống hoặc `null` là không khai báo; giá trị khác trả `400` `entryPointParts must be a boolean`).
- Khai báo gắn với version: đổi thì publish version mới. Phần vẫn được dựng và đo trong mọi trường hợp, nên Load profile của version không khai báo cũng cho biết phần mang lại gì. `effective` có thể đổi theo thiết lập của nền tảng mà không cần publish lại.
- Khai báo `true` nghĩa là tác giả chịu trách nhiệm về khác biệt nếu vi phạm: một điểm vào có thể chạy thiếu cấu hình mà file khác đặt lúc nạp, **kể cả kiểm tra quyền do project tự viết**. Cogover kiểm hết mức có thể lúc publish (file vi phạm được nạp cùng mọi điểm vào, các trường hợp nặng dùng module đầy đủ) nhưng không bảo đảm bắt hết.

### 5.1. Quyết định khai báo

Tổ chức code theo mục 3.1–3.2 và mục 4 **luôn** làm, mọi phiên bản; router con (mục 3.3) khi đủ điều kiện mục 2. Khai báo `entryPointParts` là quyết định riêng, theo bảng sau (xét từ trên xuống, dừng ở dòng đầu tiên khớp):

| Điều kiện | Hành động |
|---|---|
| Chưa đủ điều kiện mục 2 | Không khai báo |
| Chưa có Load profile của đúng code sẽ publish (thay đổi chỉ ở `cogover.json`/`cogover.example.json` không tính) | Publish không khai báo trước, đọc Load profile, rồi xét lại bảng này |
| `mainTopLevelEffect` khác `null` hoặc có `PART_GLOBALS_MODIFIED` (version không có phần nào) | Không khai báo (không có tác dụng). Sửa code theo mục 4.1 nếu muốn có phần, rồi publish lại không khai báo và xét lại bảng |
| Checklist mục 4.2 chưa được sub-agent Review bảo mật rà trên đúng code sẽ publish (ở bước 8 của skill; mọi project có code đều qua review này) | Không khai báo cho tới khi đã rà |
| Có cảnh báo `LOAD_TIME_HIGH` của module đầy đủ (`message` bắt đầu bằng `The merged bundle`), có `BUNDLE_SIZE_HIGH` (module đầy đủ từ 500 KB, mục 3.5), hoặc **lợi ích ước tính từ 200 ms trở lên** (công thức dưới; `requiredModules` không rỗng vẫn được, vì số đo của phần đã gồm module bắt buộc) | Khai báo `true` |
| Người dùng **yêu cầu tường minh** bật chạy bằng phần sau khi đã được xem số đo và nghĩa của khai báo (mục 5) | Khai báo `true` |
| Các trường hợp còn lại | Không khai báo; báo người dùng số đo, lợi ích ước tính và khi nào nên bật |

Lợi ích ước tính, lấy từ cùng một Load profile:

```text
lợi ích = coldLoadMs của Merged bundle − (coldLoadMs của Shared SDK + coldLoadMs của phần chứa điểm vào cần nhanh)
```

- Loại điểm vào cần nhanh: trigger before-change nếu có (giới hạn thời gian ngắn), nếu không thì route HTTP người dùng chờ, rồi action.
- Phần cần lấy là phần của **file chứa** điểm vào đó: trong `loadProfile.parts[]` (API, hoặc `cogover-dev publish --json`), tìm phần `kind: "FILE"` có `source` là file định nghĩa trigger/job/action (hoặc file router chứa route) và `entryPoints` đếm loại tương ứng; lấy `coldLoadMs` của phần đó (không gồm SDK, đã gồm module bắt buộc). Output thường của CLI chỉ in 3 phần chậm nhất, nên đọc `parts[]` khi file cần tìm không có trong danh sách đó. Có nhiều điểm vào cần nhanh thì lấy phần chậm nhất trong số các phần của chúng.
- Điểm vào nằm trong `entryPoints[]` của Load profile thì không có phần riêng theo file: `level: "KIND"` nghĩa là nó chạy bằng phần dùng chung của cả loại (phần `kind: "KIND"` có `source` là `triggers`, `jobs` hoặc `actions`; lấy `coldLoadMs` của phần đó), `level: "BUNDLE"` nghĩa là nó chạy bằng module đầy đủ (lợi ích bằng 0). `reason` đi kèm cho biết vì sao (bảng mã ở mục 6); tài liệu công khai không nêu thêm điều kiện để rơi vào `KIND`.
- SDK dùng chung thường vài chục tới khoảng 100 ms, nên ngưỡng 200 ms thường tương ứng với bundle đầy đủ nạp nguội từ khoảng 300 ms trở lên.
- Số đo dao động khoảng ±25% giữa các lần: chỉ so các số trong cùng một profile. Lợi ích dưới 200 ms (kể cả sát ngưỡng) thì không khai báo, ghi số đo và xét lại ở lần publish sau; không publish thêm chỉ để đo lại.
- Ví dụ: bundle đầy đủ 95 ms, SDK 75 ms, phần chậm nhất 4 ms → lợi ích khoảng 16 ms: không khai báo. Bundle đầy đủ 1.180 ms, SDK 53 ms, phần của trigger 60 ms → lợi ích khoảng 1.067 ms (và có `LOAD_TIME_HIGH`): khai báo khi các dòng trên của bảng đã qua.
- `PART_SIZE_HIGH` không phải lý do để không khai báo: phần luôn nhỏ hơn module đầy đủ chứa nó. Sửa bố cục theo mục 3.5 trước khi khai báo nếu được; chưa sửa thì ghi phần nào, kích thước và mức độ được gọi vào bàn giao.

Yêu cầu chung chung như "làm cho module nạp nhanh", "theo khuyến nghị mới nhất", "tối ưu hiệu năng" **không** phải yêu cầu khai báo. Với yêu cầu đó: tổ chức code theo quy ước, báo số đo Load profile (bundle đầy đủ, SDK, phần chậm nhất, lợi ích ước tính, dòng `Runs on:`) và nêu điều kiện nên bật; chỉ khai báo khi bảng trên cho kết quả khai báo.

Nêu quyết định, số đo và lý do trong yêu cầu xác nhận publish và trong báo cáo bàn giao. Khi khai báo: đặt `true` trong `cogover.json` và `cogover.example.json` (mục 5.2), publish version mới, đọc lại dòng `Runs on:`, kiểm thử lại theo mục 8; xác nhận publish/activate theo bước 9 của skill như mọi version.

Không khai báo `true` khi còn một trong các điều sau, kể cả khi lợi ích lớn:

- Không chắc project tuân quy tắc ("không chắc thì đừng khai báo").
- Checklist mục 4.2 tìm thấy code cấu hình lúc nạp (quyền, registry, khởi tạo thư viện) mà Load profile không liệt kê, chưa sửa.
- Project dùng thư viện cấu hình bằng lời gọi lúc nạp, plugin tự đăng ký, polyfill, hay quy tắc quyền đặt lúc nạp mà chưa chuyển sang khởi tạo lười.
- Code dựa vào `.name` của class/hàm, hoặc dựa vào ngày giờ lúc nạp.

Hướng dẫn SDK khuyên đừng khai báo khi `requiredModules` có file sửa đối tượng của file khác hay lời gọi không phân giải được mà bạn không chắc là vô hại. Hiểu theo nghĩa: file đã liệt kê không gây sai hành vi (đã nằm trong mọi phần), nhưng nó cho thấy project có kiểu code cấu hình lúc nạp, nên phải rà checklist 4.2 để chắc không còn code cùng kiểu mà Cogover không phát hiện.

### 5.2. Giữ khai báo trong repository

CLI đọc khai báo từ `cogover.json`, nhưng starter đưa `cogover.json` vào `.gitignore` và chỉ commit `cogover.example.json` ([Backend quick start](get-started-custom-backend-module.md#3-cấu-hình-project-local)). Để người publish sau (hoặc máy khác) không vô tình bỏ mất khai báo:

- Ghi cùng giá trị `"entryPointParts"` vào cả `cogover.json` và `cogover.example.json`, commit `cogover.example.json`.
- Ghi quyết định, lý do và số đo vào `docs/` của repository backend (hoặc README) và báo cáo bàn giao.
- Đổi khai báo thì sửa cả hai file trong cùng commit. `--parts`/`--no-parts` chỉ dùng cho một lần publish thử; version sẽ activate publish bằng giá trị trong `cogover.json` để khớp với repository.

Gỡ khai báo: activate lại version trước, hoặc đặt `false` (hoặc bỏ key) trong `cogover.json` và `cogover.example.json`, publish version mới rồi activate.

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
  Warnings (4):
    LOAD_TIME_HIGH: The merged bundle took 1180 ms to load (threshold 1000 ms).
      Hint: Put each group of routes in a router of its own file (createRouter() and its routes only) and mount it in src/main.ts with router.route(prefix, router).
    REQUIRED_MODULES: 1 module(s) run code while they load, so every part includes them (...).
      Hint: Move code that runs while a module loads into handlers, or into files that only the entry points needing it import.
    ENTRY_POINTS_IN_BUNDLE: 1 entry point(s) run on the merged bundle: order_inline.
    BUNDLE_SIZE_HIGH: The merged bundle is 1678 KB (threshold 500 KB): a bundle this large that loads often can make the runtime of the Workspace restart, so that the next call loads cold. Declare each entry point in a file of its own and publish with entryPointParts: true, so that every entry point runs on a small part.
Next: cogover-dev activate TSVXXXXXXXXXXXX
```

- `Merged bundle` / `Shared SDK`: kích thước và thời gian nạp nguội của module đầy đủ và của SDK. Số đo dao động khoảng ±25% giữa các lần, có thể chậm tới khoảng gấp đôi khi Workspace tải cao: so xu hướng, không so tuyệt đối từng ms.
- `Parts`: số phần và, theo từng loại, số điểm vào có phần trên tổng (`routes 3/5`: hai route còn đăng ký thẳng trên router chính).
- `Runs on:` cho biết version đang chạy bằng gì:

| Dòng `Runs on:` | Nghĩa và việc cần làm |
|---|---|
| `entry-point parts (entryPointParts: true at publish)` | Đang chạy bằng phần theo khai báo |
| `entry-point parts (the platform default)` | Không khai báo nhưng nền tảng mặc định chạy bằng phần: project vẫn phải tuân mục 4 |
| `entry-point parts for HTTP routes (...); triggers, jobs and actions on the merged bundle` (hoặc ngược lại) | Nền tảng mới bật phần cho một loại điểm vào (`effectiveFor`); điểm vào loại kia vẫn chạy bằng module đầy đủ |
| `merged bundle (entryPointParts not declared)` | Phần đã dựng nhưng chưa khai báo; quyết định theo mục 5 |
| `merged bundle (entryPointParts: false at publish)` | Theo khai báo `false`. Có phần đã dựng thì CLI in thêm `; publish with --parts to use the parts`; không có hậu tố đó nghĩa là version không có phần nào |
| `merged bundle (entry-point parts are not enabled on this platform yet)` | Đã khai báo `true` nhưng nền tảng chưa bật phần; không cần sửa code |
| `merged bundle (no part could be built)` | Version không có phần nào (khai báo `true` hoặc không khai báo): xem `MAIN_TOP_LEVEL_EFFECT` (kèm dòng `No part, src/main.ts runs code while it loads: ...`), `PART_GLOBALS_MODIFIED`, `PART_GLOBAL_STATE_UNKNOWN` hoặc mã `PARTS_*` trong cảnh báo |
| Không có dòng `Runs on:` và không có khối `Load profile` | CLI dưới `0.22.0`, Workspace chưa hỗ trợ, hoặc version không có hồ sơ: kết luận theo field `loadProfile` của API như mục 2 |

- Đọc qua API: `loadProfile.entryPointParts.effective` (`true` khi ít nhất một loại điểm vào đang chạy bằng phần) là field quyết định; đọc nó trước. `effectiveFor` (`entryPoints` cho trigger/job/action, `http` cho route) chỉ chi tiết theo loại và có thể vắng trên Workspace chạy bản Runtime sớm hơn: vắng thì chỉ dựa vào `effective`. `requested` là giá trị đã khai báo (`true`, `false` hoặc `null`).
- `Modules in every part` (`requiredModules`): file chạy code tác động ra ngoài lúc nạp mà Cogover phát hiện, kèm câu lệnh cấp cao nhất và chuỗi `via`; số trong ngoặc là số file và `requiredBytes` (kích thước nguồn mọi phần phải mang thêm). Hành vi an toàn (mục 4); nên sửa theo mục 4.1 để phần nhỏ lại, không bắt buộc phải rỗng mới được khai báo.
- `Slowest parts`: phần nạp chậm nhất (không tính SDK). Phần lớn: giảm import, tách bảng dữ liệu, bỏ barrel (mục 3.4, 3.5).
- CLI `0.22.0` in `PART_SIZE_HIGH` và `BUNDLE_SIZE_HIGH` như mọi cảnh báo (`MÃ: message`) nhưng chưa có dòng `Hint:` riêng cho hai mã này; cách xử lý ở bảng dưới và mục 3.5.
- `No part, src/main.ts runs code while it loads: <file:dòng lý do: câu lệnh>` (`mainTopLevelEffect`): version không có phần; đưa câu lệnh đó ra khỏi `src/main.ts`.

Lý do (`reason` của `entryPoints[]`) và cảnh báo (`warnings[].code`) thường gặp:

| Mã | Cách xử lý |
|---|---|
| `NOT_LOCATED` | Điểm vào viết trong `src/main.ts` hoặc không export từ file định nghĩa nó: chuyển sang file riêng, export, gom lại trong `src/main.ts` (mục 3.2) |
| `MAIN_TOP_LEVEL_EFFECT` | `src/main.ts` có câu lệnh cấp cao nhất tác động ra ngoài, không tất định (`Date.now()`, `Math.random()`...) hoặc không phân tích được (xem `mainTopLevelEffect`); version không có phần: giữ `src/main.ts` chỉ gồm import, mảng export và đăng ký route; chuyển câu lệnh vào handler hoặc file mà điểm vào cần nó import |
| `REQUIRED_MODULES` | An toàn về hành vi: các file trong `requiredModules` đã được đưa vào mọi phần. Cái giá là kích thước (`requiredBytes`) và thời gian nạp của mọi phần. Nên sửa (chuyển code lúc nạp vào hàm gọi từ handler, hoặc vào file chỉ điểm vào cần mới import) để phần nhỏ lại; không bắt buộc trước khi khai báo, quyết định theo lợi ích ở mục 5.1 |
| `PART_GLOBALS_MODIFIED` | Project ghi vào global/đối tượng built-in ở đâu đó (`message` nêu file và dòng); Cogover xét cả project, kể cả code trong handler, nên chuyển vào handler không giải quyết được. Bỏ polyfill/vá prototype/gán `globalThis`, thay bằng hàm của project (mục 4.1); không bỏ được thì chấp nhận chạy bằng module đầy đủ (không khai báo) |
| `PART_GLOBAL_STATE_UNKNOWN` | Code lúc nạp đưa quá nhiều vào global để so: thu nhỏ code lúc nạp |
| `LOAD_TIME_HIGH` | Module đầy đủ (hoặc SDK cộng một phần) nạp lâu hơn `thresholdMillis`. Module đầy đủ: tách điểm vào và nhóm route ra file riêng/router con. Một phần (`message` bắt đầu bằng `Part`): import ít hơn từ file dùng chung, xử lý `requiredModules` |
| `PART_SIZE_HIGH` | Một phần từ `partSizeThresholdBytes` (400 KB) trở lên; `message` nêu số thứ tự, file và kích thước. Phần lớn được nạp nhiều lần có thể làm môi trường chạy của Workspace khởi động lại. Tách file khai báo điểm vào của phần đó (bỏ file registry, chia router con), import ít hơn, xử lý `requiredModules`, dữ liệu lớn ra khỏi code (mục 3.5) |
| `BUNDLE_SIZE_HIGH` | Module đầy đủ từ `bundleSizeThresholdBytes` (500 KB) trở lên và có lần thực thi còn chạy bằng nó. Tổ chức mọi điểm vào theo mục 3 (route trong router con) rồi quyết định khai báo `true` theo mục 5.1; cảnh báo hết khi mọi điểm vào chạy bằng phần (điều kiện ở mục 3.5) |
| `ENTRY_POINTS_IN_BUNDLE` | Liệt kê điểm vào dùng module đầy đủ; xử lý theo `reason` của từng điểm vào |
| `ROUTE_SHADOWED` | Route của router con không bao giờ được gọi vì route đứng trước trên router chính trả lời cùng request: đổi thứ tự hoặc đổi path |
| `PART_NOT_SMALLER` | File import gần như cả module: import ít hơn từ file dùng chung |
| `ROUTE_MATCH_MISMATCH`, `PART_REJECTED`, `PART_ORDER_MISMATCH`, `PARTS_LIMIT`, `PARTS_TIMEOUT`, `PARTS_BUILD_FAILED`, `PARTS_PLAN_MISMATCH` | Điểm vào bị ảnh hưởng dùng module đầy đủ; không cần sửa code để module chạy đúng. Lặp lại qua nhiều lần publish thì báo người dùng kèm mã và `message` |

`level` của điểm vào trong `entryPoints[]` là `KIND` khi nó không có phần theo file mà chạy bằng phần dùng chung của cả loại (mọi trigger, mọi job hoặc mọi action của version), `BUNDLE` khi dùng module đầy đủ. Load profile chỉ để tham khảo: cảnh báo không bao giờ làm publish thất bại.

Publish chậm hơn trước vì dựng và đo phần, tuỳ kích thước: module nhỏ (vài trăm KiB) thêm vài giây; module vài MB với khoảng 100 điểm vào thêm khoảng 10–25 giây; bước này dừng ở 45 giây, quá thì version vẫn được publish nhưng không có phần (`PARTS_TIMEOUT`). Đặt thời gian chờ publish có dư địa.

## 7. Giới hạn kích thước

Tổng dung lượng source file mà `src/main.ts` import tới tối đa **6 MiB**, bundle JavaScript sau khi compile cũng tối đa **6 MiB** (`TYPESCRIPT_COMPILE_FAILED`); bảng đầy đủ ở mục [Giới hạn kích thước](custom-backend-module-api-reference.md#giới-hạn-kích-thước). Bundle chứa cả `@cogover/sdk` (source thì không tính SDK), nên source sát 6 MiB vẫn có thể vượt giới hạn bundle. Tách file không làm module đầy đủ nhỏ đi: dữ liệu lớn vẫn tính vào cả hai giới hạn.

6 MiB là trần để publish được, không phải kích thước nên nhắm tới:

- Bundle càng lớn nạp càng lâu: mọi lần thực thi không chạy bằng phần đều nạp cả bundle (mục 1).
- Bước kiểm bundle lúc publish cũng có giới hạn thời gian xử lý, nên bundle nhiều **code** cỡ vài MB có thể bị từ chối ở bước kiểm bundle lúc publish (version `FAILED`) trước khi chạm 6 MiB. Bundle nặng **dữ liệu** (bảng tra cứu lớn) ít gặp trường hợp này hơn.
- Kích thước nên nhắm tới thấp hơn nhiều: module đầy đủ dưới 500 KB và mỗi phần dưới 400 KB (mục 3.5); lớn hơn thì Load profile báo `BUNDLE_SIZE_HIGH`/`PART_SIZE_HIGH`.
- Module lớn: tổ chức theo điểm vào (mục 3) và chạy bằng phần khi bảng mục 5.1 cho phép; dữ liệu lớn tách file riêng chỉ điểm vào cần mới import, hoặc đưa ra Object hay file của Workspace và đọc khi cần; theo dõi `LOAD_TIME_HIGH`, `PART_SIZE_HIGH` và `BUNDLE_SIZE_HIGH` trong Load profile sau mỗi lần publish.

## 8. Kiểm thử và bàn giao

- Unit test không đổi: hàm thuần và handler import từ file của chúng. Chạy `npm test`/máy chủ local trước publish như thường (`defineTrigger`/`defineJob`/`defineAction` validate khi module được nạp).
- Sau publish: lưu Load profile (output CLI hoặc `loadProfile` của version) vào bằng chứng; kiểm thử chức năng chạy trên đúng version sẽ activate (đã khai báo hay chưa). Đổi khai báo là version mới, kiểm thử lại trên chính version đó: trước khi activate, gọi các route chính qua preview service `6` chỉ rõ version ID (`READ_ONLY` khi route chỉ đọc), gồm ca từ chối quyền; sau khi activate, chạy lại ca trigger (đặc biệt before-change), job và action vì chúng chỉ chạy trên version active. Ca nào khác kết quả của version trước thì activate lại version trước và xử lý theo mục 4.
- Đo hiệu năng: tính lợi ích ước tính theo mục 5.1 (bundle đầy đủ so với SDK cộng phần của điểm vào cần đo), và thời gian phản hồi lượt gọi đầu tiên sau activate với các lượt sau, theo [Kiểm thử hiệu năng](performance-testing.md).
- Bàn giao: phiên bản SDK/CLI, Workspace hỗ trợ hay chưa (bằng chứng), bố cục `src/`, có dùng `router.route()` không, khai báo `entryPointParts` (`true`/`false`/không khai báo), lý do theo bảng mục 5.1 và nơi lưu khai báo (mục 5.2), dòng `Runs on:`, lợi ích ước tính, kích thước và `coldLoadMs` của module đầy đủ, số phần và độ phủ, kích thước các phần lớn nhất (theo `parts[].bytes`) và của phần phục vụ điểm vào gọi dày, `requiredModules` còn lại, cảnh báo còn lại (đặc biệt `PART_SIZE_HIGH`, `BUNDLE_SIZE_HIGH`) và lý do chấp nhận.
