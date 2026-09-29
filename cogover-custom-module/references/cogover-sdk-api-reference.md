# API reference: `@cogover/sdk`

`@cogover/sdk` là contract TypeScript công khai để phát triển Custom Backend Module
trên Cogover. Thông tin xác thực của Cogover không bao giờ được đưa vào code của
module; các capability call bị giới hạn bởi quyền và hạn mức đã cấu hình cho
project.

## `defineScript`

```typescript
function defineScript<
  Input = unknown,
  Output = unknown,
  Schema extends object = EffectiveWorkspaceObjects,
>(handler: ScriptHandler<Input, Output, Schema>): SandboxHandler;
```

Các type public liên quan:

```typescript
type SandboxHandler = (inputJson: string) => Promise<string | null>;

type ScriptHandler<Input, Output, Schema extends object = EffectiveWorkspaceObjects> =
  (context: ScriptContext<Input, Schema>) =>
    Output | ScriptResponse<unknown> | null |
    Promise<Output | ScriptResponse<unknown> | null>;

interface ScriptContext<Input, Schema extends object = EffectiveWorkspaceObjects> {
  readonly input: Input;
  readonly request: ScriptRequest<Input>;
  readonly invocation: InvocationContext;
  readonly data: DataApi<Schema>;
  readonly schema: SchemaApi<Schema>;
  readonly log: ScriptLogger;
  readonly response: ResponseApi;
  readonly state: ProjectState;
  readonly locks: DistributedLocks;
  readonly push: PushApi<Schema>;
  readonly notifications: NotificationsApi;
  readonly email: EmailApi<Schema>;
  readonly jobs: JobsApi;
  readonly secrets: SecretsApi;
  readonly crypto: CryptoApi;
  readonly org: OrgApi;
}
```

`defineScript` ném `ValidationError` nếu handler không phải function. Handler kết
quả ném lỗi nếu input không phải JSON hợp lệ hoặc output không serialize được sang
JSON. Trả `null` tạo kết quả null; trả `undefined` là không hợp lệ.

Hàm wrapper parse input JSON, cung cấp `input`, `request`, `invocation`, `response`, `data`, `schema`, `log`, `state`, `locks`,
`push`, `notifications`, `email`, `jobs`, `secrets`, `crypto`, `org`, chờ kết quả async và serialize output thành
JSON.

## HTTP router và request context

`ScriptContext<TInput, TSchema>` cung cấp `input`, `request`, `invocation`, `response`, `data`, `schema`,
`log`, `state`, `locks`, `push`, `notifications`, `email`, `jobs`, `secrets`, `crypto` và `org` cho cả script
handler lẫn route handler. `input`
giữ input invocation hiện có. Nên dùng `request.body` cho dữ liệu nghiệp vụ: body không chứa invocation
metadata và các field transport/xác thực đã được Cogover loại bỏ.

```typescript
type RequestMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
type ScriptQuery = Readonly<Record<string, string | readonly string[]>>;
type ScriptHeaders = Readonly<Record<string, string>>;
type ScriptPathParams = Readonly<Record<string, string>>;

interface ScriptRequest<TBody = unknown> {
  readonly method: RequestMethod;
  readonly path: string;   // Tương đối với /api/v1/ts-projects/{projectSlug}
  readonly params: ScriptPathParams;
  readonly query: ScriptQuery;
  readonly headers: ScriptHeaders;
  readonly body: TBody;
  readonly rawBody?: string;      // Chỉ có với lời gọi webhook
  readonly contentType?: string;  // Chỉ có với lời gọi webhook
}
```

Request descriptor và các map metadata được freeze; body không bị deep-freeze.
Method, path, query và header trong allowlist đến từ Cogover, không lấy từ field
nghiệp vụ. Query lặp tên trở thành readonly array. Tên header được đổi sang chữ
thường; credential như `authorization` và `cookie` không bao giờ lộ vào script.
Path param được percent-decode sau khi route an toàn đã khớp. Kiểu TypeScript không
validate input nghiệp vụ lúc chạy.

`rawBody` và `contentType` chỉ có mặt với lời gọi đi vào project qua inbound webhook
(xem [Inbound webhook](#inbound-webhook)): `rawBody` là request body đúng như đã
nhận, dưới dạng chuỗi UTF-8, và `contentType` là header `Content-Type` của request.
Với mọi lời gọi khác, cả hai field đều vắng mặt.

## Danh tính invocation và workspace hiện tại

`context.invocation` là snapshot đồng bộ, bất biến được tạo từ metadata mà Cogover
đã xác thực và nạp sẵn cho lần thực thi hiện tại. Đọc property này không gửi yêu
cầu tới Data API.

```typescript
type InvocationContext = UserInvocationContext | SystemInvocationContext | InboundInvocationContext;

interface CurrentWorkspace {
  readonly id: string;
  readonly name?: string;
  readonly domain?: string;
  readonly language?: string;
  readonly timezone?: string;
  readonly dateFormat?: string;
  readonly timeFormat?: string;
  readonly numberFormat?: string;
}

interface CurrentWorkspaceRole {
  readonly id: string;
  readonly name: string;
}

interface CurrentWorkspaceMembership {
  readonly personnelId?: string;
  readonly language?: string;
  readonly timezone?: string;
  readonly isSuperAdmin: boolean;                  // Có role Super Admin của workspace
  readonly roles: readonly CurrentWorkspaceRole[]; // Sắp xếp theo tên
}

interface CurrentUser {
  readonly accountId: string;
  readonly email?: string;
  readonly firstName?: string;
  readonly lastName?: string;
  readonly avatar?: string;
  readonly language?: string;
  readonly timezone?: string;
  readonly membership: CurrentWorkspaceMembership;
}

interface UserInvocationContext {
  readonly identity: "user";
  readonly workspace: CurrentWorkspace;
  readonly user: CurrentUser;
}

interface SystemInvocationContext {
  readonly identity: "system";
  readonly workspace: CurrentWorkspace;
  readonly user: null;
}

interface InboundInvocationContext {
  readonly identity: "inbound";
  readonly workspace: CurrentWorkspace;
  readonly user: null;
  readonly inbound: {
    readonly id: string;             // Nằm trong URL webhook
    readonly name: string;
    readonly mode: "KEY" | "HMAC";   // Cách lời gọi đã được xác thực
  };
}
```

Mọi field đều readonly. Các field profile/workspace optional có thể không tồn tại,
vì vậy script không được giả định chúng luôn có giá trị.

`identity` là `"user"` với lời gọi của người dùng Workspace đã xác thực, `"system"`
với lần thực thi không có người dùng, ví dụ job chạy theo lịch, và `"inbound"` với
lời gọi webhook được xác thực bằng một inbound access của project (xem
[Inbound webhook](#inbound-webhook)). Invocation inbound không có user; `inbound`
định danh inbound access đã xác thực lời gọi.

```typescript
export default defineScript(({ invocation }) => {
  if (invocation.identity === "system") {
    return {workspaceId: invocation.workspace.id, user: null};
  }
  if (invocation.identity === "inbound") {
    return {workspaceId: invocation.workspace.id, inbound: invocation.inbound.name};
  }
  return {
    workspaceId: invocation.workspace.id,
    accountId: invocation.user.accountId,
    personnelId: invocation.user.membership.personnelId,
  };
});
```

Cogover bỏ qua invocation metadata do caller tự gửi và dựng snapshot từ request
context đã xác thực. Raw authentication data, token, inbound key và credential
không được đưa vào. Handler gọi bên ngoài Cogover không có invocation snapshot đã
xác thực.

### Role của người dùng hiện tại trong Workspace

`user.membership` mô tả tư cách thành viên của người gọi trong Workspace hiện tại:

- `isSuperAdmin` là `true` khi một trong các role của người dùng là role quản trị
  cao nhất (Super Admin) của Workspace, ngược lại là `false`.
- `roles` liệt kê các role được gán cho người dùng trong Workspace hiện tại, sắp
  xếp theo tên. Mỗi `CurrentWorkspaceRole` chỉ có `id` và `name`; danh sách rỗng
  khi người dùng không có role nào. Quyền của role không được cung cấp.

So sánh role theo `id`: role có thể được đổi tên, và cùng một tên role có `id`
khác nhau ở mỗi Workspace. Quyền truy cập record và field vẫn do Cogover kiểm soát
theo danh tính của người dùng, vì vậy hãy dùng các field này cho quy tắc nghiệp
vụ, chẳng hạn ai được duyệt đơn hàng, chứ không thay thế cho quy tắc bảo mật.

```typescript
const APPROVER_ROLE_ID = "RO0000000001";

export default defineScript(({ invocation }) => {
  const user = invocation.user;
  const canApprove = user !== null && (user.membership.isSuperAdmin
    || user.membership.roles.some((role) => role.id === APPROVER_ROLE_ID));
  return {canApprove};
});
```

Invocation HTTP phản ánh role của người dùng tại thời điểm gửi request. Record
trigger và background job có thể nhận thay đổi role chậm tối đa khoảng một phút.
Khi phát triển local bằng Cogover Dev CLI, các giá trị được lấy lúc development
session bắt đầu; hãy khởi động lại `cogover-dev` để nhận thay đổi role. Invocation
`system` hoặc `inbound` có `user: null` nên không có membership.

### `createRouter<TSchema = EffectiveWorkspaceObjects>(): ScriptRouter<TSchema>`

Tạo router độc lập. `TSchema extends object` mặc định là schema workspace hiệu lực,
giữ suy luận `WorkspaceObjects` qua module augmentation cho data và schema API.
Route phân biệt hoa/thường theo method và path tĩnh/động; route tĩnh được ưu tiên
hơn route động. Khi nhiều route động cùng method khớp một path, ví dụ `/orders/:id` và
`/:collection/new` với `/orders/new`, route được đăng ký trước sẽ xử lý. `/` ứng với URL
project canonical
không có route suffix.
`/index` là route riêng, phải đăng ký rõ ràng. `defineScript()` vẫn dùng cho `/`;
gọi đường dẫn con sẽ ném `NotFoundError` trước khi handler của script chạy.

### `router.addRoute<TInput = unknown, TOutput = unknown>(method: RequestMethod, path: string, handler: ScriptHandler<TInput, TOutput, TSchema>): ScriptRouter<TSchema>`

Đăng ký handler và trả lại chính router để gọi nối tiếp. Hỗ trợ `GET`, `POST`,
`PUT`, `PATCH`, `DELETE`. Path là `/` hoặc các segment tĩnh/động như
`/orders/:orderId`. Segment tĩnh bắt đầu bằng chữ ASCII hoặc số và có thể chứa
chữ, số, `_`, `-`, dài tối đa 100 ký tự. Tên param bắt đầu bằng chữ ASCII, có thể
chứa chữ, số, `_`, dài tối đa 64 ký tự và không được lặp trong cùng route. Toàn bộ
path dài tối đa 1.024 ký tự. Dấu `/` cuối đường dẫn con, segment rỗng, `.`,
`..`, percent escape trong template, `?`, `#` và wildcard bị từ chối. Route trùng
hoặc mơ hồ về cấu trúc trong cùng method, handler sai hoặc vượt 256 route đều ném
`ValidationError`.

Handler là hàm `ScriptHandler` thông thường, không phải hàm đã bọc bằng
`defineScript()`. Handler nhận cùng data/schema/log API, input và request context.
Có thể đăng ký cùng một handler cho nhiều path.

### `router.get/post/put/patch/delete(path, handler): ScriptRouter<TSchema>`

Cách viết ngắn theo từng method của `addRoute()`, cùng validation, giá trị trả về và lỗi.

### `router.toHandler(): SandboxHandler`

Trả về handler để default-export, chụp lại danh sách route hiện tại.
Đăng ký thêm sau đó không thay đổi handler đã tạo. Handler parse input, chọn đúng
một route, chờ kết quả và serialize như `defineScript()`.
`null` giữ nguyên null; kết quả undefined ném `ValidationError`. Route không tồn tại
ném `NotFoundError` (HTTP 404), kể cả path chỉ được đăng ký cho method khác: router
không trả 405 khi sai method. Invocation dùng method chưa hỗ trợ có
`CogoverApiError` với `code: "METHOD_NOT_ALLOWED"` (HTTP 405).
Metadata invocation sai ném `ValidationError`.
Khi gọi trực tiếp mà không có request metadata của Cogover, handler mặc định là POST `/`.

Route kế thừa xác thực, quyền và giới hạn runtime của project. Đăng ký route không
cấp thêm quyền hay tạo ranh giới bảo mật riêng. Idempotency replay có phạm vi theo
method/path cùng phiên bản project và người gọi; dùng key mới cho mỗi thao tác
nghiệp vụ khác nhau.

## HTTP response API

Trả về giá trị JSON bình thường vẫn giữ hành vi tương thích `200 application/json`.
Dùng helper `response` trong context khi cần điều khiển status, header, content type
hoặc dạng body. Chỉ response do các helper này tạo mới làm được việc đó: giá trị được
trả về luôn được gửi như dữ liệu JSON với HTTP 200, kể cả khi có hình dạng giống
envelope response nội bộ của Cogover, ví dụ request body được route trả lại nguyên vẹn.

```typescript
router.post("/orders", ({ response }) => response.json({ id: "ORD-1" }, {
  status: 201,
  headers: { location: "/orders/ORD-1", "x-request-state": "created" },
}));

router.get("/files/:fileId", ({ response }) =>
  response.bytes(new Uint8Array([0, 1, 255]), { contentType: "application/octet-stream" }));
```

```typescript
type ResponseHeaderValue = string | readonly string[];

interface ResponseInit {
  readonly status?: number;
  readonly headers?: Readonly<Record<string, ResponseHeaderValue>>;
}

interface BinaryResponseInit extends ResponseInit {
  readonly contentType?: string;
}

interface ResponseApi {
  json<T>(body: T, init?: ResponseInit): ScriptResponse<T>;
  text(body: string, init?: ResponseInit): ScriptResponse<string>;
  bytes(body: Uint8Array, init?: BinaryResponseInit): ScriptResponse<Uint8Array>;
  empty(init?: ResponseInit): ScriptResponse<null>;
  redirect(location: string, status?: 301 | 302 | 303 | 307 | 308): ScriptResponse<null>;
}

response.json(body, init?)
response.text(body, init?)
response.bytes(body: Uint8Array, { status?, headers?, contentType? }?)
response.empty(init?)                 // mặc định status 204
response.redirect(location, status?) // mặc định status 302
```

Status phải là số nguyên từ 200 đến 599. Giá trị header là một string hoặc readonly
string array. Hop-by-hop header, header đặt credential và header dành riêng cho
Cogover bị từ chối. Tên/giá trị header không được chứa newline;
tối đa 50 header. Tên header dài tối đa 128 ký tự và mỗi giá trị tối đa 8.192 ký tự.
Content type mặc định lần lượt là
`application/json; charset=utf-8`, `text/plain; charset=utf-8` và
`application/octet-stream`. Redirect chỉ nhận 301, 302, 303, 307 hoặc 308; giá trị khác
ném `ValidationError`. Helper
trả `ScriptResponse` opaque; code ứng dụng không được tự tạo transport envelope.
Redirect location phải khác rỗng, dài tối đa 4.096 ký tự và không chứa newline.
`response.json()` không nhận `undefined`; `response.text()` yêu cầu string và
`response.bytes()` yêu cầu `Uint8Array`.

## Record trigger

Record trigger chạy code của project khi record của một Object được tạo, cập nhật
hoặc xoá. Khai báo từng trigger bằng `defineTrigger` và liệt kê kết quả trong named
export `triggers` của project. Default export vẫn là HTTP handler và trở thành tuỳ
chọn với project chỉ khai báo trigger.

Ví dụ này giả định `workspace.d.ts` đã khai báo Object `order` và các field được
sử dụng bên dưới.

```typescript
import { defineTrigger } from "@cogover/sdk";

export const triggers = [
  defineTrigger({
    key: "order_credit_check",
    object: "order",
    timing: "beforeChange",
    operations: ["create", "update"],
    fields: ["status", "amount", "customer"],
    changedFields: ["status", "amount"],
    when: { op: "=", field: "status", params: "confirmed" },
    writableFields: ["approval_level"],
  }, async ({ records }) => {
    for (const record of records) {
      if ((record.new.amount ?? 0) > 1_000_000_000) {
        record.addError("amount", "AMOUNT_TOO_LARGE", "Amount exceeds the approval limit.");
        continue;
      }
      record.new.approval_level = "high";
    }
  }),
];
```

Trigger có một trong hai thời điểm chạy. Trigger **before-change** chạy trước khi
thay đổi được lưu: có thể từ chối record và điều chỉnh giá trị sẽ được lưu. Trigger
**after-change** chạy bất đồng bộ sau khi thay đổi đã được lưu: không thể từ chối hay
sửa thay đổi đó, nhưng được ghi record và gọi `fetch`. Xem
[Quy tắc thực thi before-change](#quy-tắc-thực-thi-before-change) và
[Quy tắc thực thi after-change](#quy-tắc-thực-thi-after-change).

Cogover đọc cấu hình trigger khi một version của project được publish và áp dụng
cấu hình đó trong thời gian version ấy đang active. Deactivate project sẽ gỡ các
trigger của project. Một project khai báo tối đa 50 trigger; một Object có tối đa
20 trigger before-change đang hoạt động; version khai báo nhiều hơn trên một Object sẽ
publish thất bại.

### `defineTrigger(config, handler): TriggerDefinition`

```typescript
function defineTrigger<
  ObjectSlug extends keyof Schema & string,
  Operation extends TriggerOperation,
  Schema extends object = EffectiveWorkspaceObjects,
>(
  config: TriggerConfig<ObjectSlug, Operation, Schema>,
  handler: TriggerHandler<ObjectSlug, Operation, Schema>,
): TriggerDefinition;
```

Các type argument được suy luận từ `config.object` và `config.operations`. Khi có
`workspace.d.ts` được sinh từ Workspace, object slug, mọi field slug trong cấu hình
và giá trị của `record.new`, `record.old` đều được kiểm tra theo Object đã khai báo.
Khi chưa có khai báo Workspace, slug là string và giá trị field có type `unknown`.

`defineTrigger` validate cấu hình ngay lập tức và ném `ValidationError` với mọi vi
phạm, với key cấu hình không xác định hoặc khi handler không phải function. Hàm trả
về một `TriggerDefinition` đã freeze.

```typescript
type TriggerTiming = "beforeChange" | "afterChange";
type TriggerOperation = "create" | "update" | "delete";
type TriggerRunWhen = "always" | "onEnter";

interface TriggerConfig<
  ObjectSlug extends string = string,
  Operation extends TriggerOperation = TriggerOperation,
  Schema extends object = EffectiveWorkspaceObjects,
> {
  readonly key: string;
  readonly name?: string;
  readonly object: ObjectSlug;
  readonly timing: TriggerTiming;
  readonly operations: readonly Operation[];
  readonly fields: readonly FieldSlug[];          // field slug của Object
  readonly changedFields?: readonly FieldSlug[];
  readonly when?: TriggerFilter;
  readonly runWhen?: TriggerRunWhen;
  readonly writableFields?: readonly FieldSlug[];
  readonly order?: number;
  readonly timeoutMs?: number;
}
```

| Option | Bắt buộc | Quy tắc và ý nghĩa |
|---|---|---|
| `key` | Có | Định danh trigger trong project. Bắt đầu bằng chữ ASCII, chỉ chứa chữ, số hoặc `_`; tối đa 100 ký tự. Giữ ổn định giữa các version: key mới là một trigger khác. |
| `name` | Không | Tên hiển thị, tối đa 250 ký tự. Mặc định là `key`. |
| `object` | Có | Slug của Object có record chạy trigger. |
| `timing` | Có | `"beforeChange"` chạy trước khi thay đổi được lưu, có thể từ chối hoặc điều chỉnh thay đổi. `"afterChange"` chạy bất đồng bộ sau khi thay đổi đã được lưu. |
| `operations` | Có | Danh sách không rỗng gồm `"create"`, `"update"`, `"delete"`, không trùng lặp. |
| `fields` | Có | 1–200 field slug không trùng. `record.new` và `record.old` chỉ chứa các field này và `id`. |
| `changedFields` | Không | 1–200 field slug không trùng; yêu cầu có operation `"update"`. Thao tác cập nhật chỉ chạy trigger khi ít nhất một field trong danh sách thay đổi. Không ảnh hưởng tới tạo và xoá. |
| `when` | Không | Một `TriggerFilter`. Chỉ record khớp filter mới chạy trigger. |
| `runWhen` | Không | `"always"` (mặc định) hoặc `"onEnter"`. `"onEnter"` yêu cầu có `when`. |
| `writableFields` | Không | Tối đa 100 field slug không trùng mà handler được sửa. Chỉ dùng cho `"beforeChange"`; phải rỗng khi `"delete"` là operation duy nhất. Field formula, auto number, rollup summary hoặc field chỉ đọc khác làm version publish thất bại. Mặc định `[]`. |
| `order` | Không | Số nguyên từ 1000 đến 8999; mặc định `5000`. Các trigger của một Object chạy theo thứ tự tăng dần. Các giá trị khác dành riêng cho Cogover. Không dựa vào thứ tự tương đối giữa các trigger có cùng giá trị. |
| `timeoutMs` | Không | Số nguyên từ 100 đến 3000; mặc định `2000`. Thời gian tối đa cho một lần gọi handler. |

Object slug và field slug bắt đầu bằng chữ ASCII hoặc `_`, chỉ chứa chữ, số hoặc
`_` và dài tối đa 355 ký tự. `changedFields` và `writableFields` không bắt buộc phải
nằm trong `fields`.

### Trigger filter

```typescript
interface TriggerFilterCondition {
  readonly op: FilterOperator;
  readonly field: string;
  readonly params?: unknown;
}

interface TriggerFilterGroup {
  readonly op: "and" | "or";
  readonly conditions: readonly TriggerFilter[];
}

type TriggerFilter = TriggerFilterCondition | TriggerFilterGroup;
```

```typescript
when: {
  op: "and",
  conditions: [
    { op: "=", field: "status", params: "confirmed" },
    { op: "or", conditions: [
      { op: ">=", field: "amount", params: 1_000_000 },
      { op: "in", field: "priority", params: ["high", "urgent"] },
    ] },
  ],
}
```

Một condition so sánh một field bằng một `FilterOperator`. `params` là giá trị so
sánh dạng JSON: bắt buộc với mọi operator trừ `"is null"` và `"not null"` (hai
operator này không nhận giá trị). `"in"` và `"not in"` nhận một mảng không rỗng;
`"between"` nhận đúng hai giá trị. Một group kết hợp một danh sách filter không
rỗng. Filter lồng tối đa 8 cấp và chứa tối đa 50 condition. Trigger filter là
object thuần: biểu thức tạo bằng `and()`, `or()` hoặc field reference dành cho
`records.list` và bị từ chối ở đây.

`when` được đánh giá trên giá trị mới, hoặc trên giá trị cũ khi record bị xoá. Với
`runWhen: "onEnter"`, trigger chỉ chạy khi trước thay đổi record không khớp `when`
và sau thay đổi thì khớp; record đang được tạo được coi là chưa khớp trước đó, và
`runWhen` bị bỏ qua với thao tác xoá.

Cogover quyết định những trigger nào sẽ chạy đúng một lần, trước trigger đầu tiên
của một thay đổi, dựa trên giá trị do bên ghi gửi lên cùng giá trị mặc định của
field. Giá trị do trigger chạy trước sửa không làm đổi danh sách trigger sẽ chạy,
nhưng trigger chạy sau vẫn thấy giá trị đó trong `record.new`.

### `TriggerDefinition` và `TriggerManifest`

```typescript
interface TriggerManifest {
  readonly key: string;
  readonly name?: string;
  readonly object: string;
  readonly timing: TriggerTiming;
  readonly operations: readonly TriggerOperation[];
  readonly fields: readonly string[];
  readonly changedFields?: readonly string[];
  readonly when?: TriggerFilter;
  readonly runWhen: TriggerRunWhen;
  readonly writableFields: readonly string[];
  readonly order: number;
  readonly timeoutMs: number;
}

type TriggerSandboxHandler = (inputJson: string) => Promise<string>;

interface TriggerDefinition {
  readonly key: string;
  readonly config: TriggerManifest;
  readonly __cogoverTriggerHandler: TriggerSandboxHandler;
}
```

`config` là cấu hình đã chuẩn hoá ở dạng JSON thuần, được deep-freeze và đã áp dụng
mọi giá trị mặc định: `runWhen: "always"`, `writableFields: []`, `order: 5000` và
`timeoutMs: 2000`. Các thiết lập tuỳ chọn không được khai báo sẽ không xuất hiện.
`config` tách rời khỏi object truyền vào `defineTrigger`, nên sửa object đó về sau
không có tác dụng. `__cogoverTriggerHandler` dành riêng cho Cogover; code của
project không gọi hàm này.

### Context của trigger handler

```typescript
type TriggerHandler<
  ObjectSlug extends string = string,
  Operation extends TriggerOperation = TriggerOperation,
  Schema extends object = EffectiveWorkspaceObjects,
> = (context: TriggerContext<ObjectSlug, Operation, Schema>) => void | Promise<void>;

interface TriggerContext<
  ObjectSlug extends string = string,
  Operation extends TriggerOperation = TriggerOperation,
  Schema extends object = EffectiveWorkspaceObjects,
> {
  readonly records: readonly TriggerRecord<Fields, Operation>[]; // Fields của ObjectSlug
  readonly trigger: TriggerInfo<Operation>;
  readonly invocation: InvocationContext;
  readonly data: DataApi<Schema>;
  readonly schema: SchemaApi<Schema>;
  readonly log: ScriptLogger;
  readonly push: PushApi<Schema>;
  readonly notifications: NotificationsApi;
  readonly email: EmailApi<Schema>;
  readonly jobs: JobsApi;
  readonly secrets: SecretsApi;
  readonly crypto: CryptoApi;
  readonly org: OrgApi;
}

interface TriggerInfo<Operation extends TriggerOperation = TriggerOperation> {
  readonly id: string;
  readonly key: string;
  readonly timing: TriggerTiming;
  readonly operation: Operation;
  readonly objectSlug: string;
  readonly changeId: string;
}

interface TriggerRecord<Fields = Record<string, unknown>, Operation extends TriggerOperation = TriggerOperation> {
  readonly key: string;
  readonly id: CogoverRecordId | null;
  readonly new: TriggerNewValues<Fields> | null;
  readonly old: TriggerOldValues<Fields> | null;
  readonly changedFields: readonly (keyof Fields & string)[];
  addError(field: (keyof Fields & string) | null, code: string, message?: string): void;
}

type TriggerNewValues<Fields> = {
  -readonly [K in keyof Fields]?: Fields[K] | UpdateFields<Fields>[K];
};

type TriggerOldValues<Fields> = {
  readonly [K in keyof Fields]?: Fields[K];
};
```

Handler có thể đồng bộ hoặc bất đồng bộ; giá trị trả về bị bỏ qua. Một lần gọi nhận
toàn bộ record của cùng một thay đổi có chạy trigger, tối đa 200 record và 200 KiB,
nên batch write hoặc import gọi handler một lần cho mỗi nhóm record chứ không gọi
cho từng record. Hãy giữ `fields` ngắn gọn và đọc dữ liệu liên quan cho cả danh sách
bằng một lời gọi `records.getMany` thay vì đọc riêng cho từng record.

`data`, `schema`, `log`, `invocation`, `push`, `notifications`, `email`, `jobs`, `secrets`,
`crypto` và `org` là chính các API mà script nhận được. Trigger context không có `input`,
`request`, `response`, `state` hay `locks`; `push`, `notifications` và `email` bị từ chối trong
trigger before-change. `trigger.operation`
là operation của lần gọi hiện tại, `trigger.id` định danh đăng ký của trigger và
`trigger.changeId` định danh thay đổi record đã gây ra lần gọi.

Mỗi `TriggerRecord` mô tả một record:

- `key` dùng để ghép record với kết quả của nó. Đây không phải record ID.
- `id` là record ID, hoặc `null` khi record đang được tạo chưa có ID. Trong trigger
  after-change, `id` luôn có giá trị.
- `new` chứa giá trị sau thay đổi, là object thuần có thể sửa trực tiếp. `new` là
  `null` khi record bị xoá.
- `old` chứa giá trị trước thay đổi và đã được deep-freeze. `old` là `null` khi
  record được tạo.
- `changedFields` là danh sách đã freeze gồm slug các field thay đổi. Với record được
  tạo, danh sách gồm mọi field có giá trị. Với thao tác cập nhật, danh sách có thể gồm cả
  field hệ thống mà Cogover đặt ở mọi lần ghi, như `updated`.

`operations` đã khai báo thu hẹp các type này: `new` không bao giờ là `null` trừ khi
có khai báo `"delete"`, `old` không bao giờ là `null` trừ khi có khai báo `"create"`,
và trigger chỉ khai báo `"delete"` có `new: null`. `TriggerNewValues` và
`TriggerOldValues` để mọi field là optional vì field không nằm trong `fields`, hoặc
không có giá trị, sẽ là `undefined`.

Giá trị lookup và reference trong `new` và `old` có `name` của record liên kết. Điều này
khác với record đọc qua `data`, có giá trị lookup với `name: ""` trừ khi lệnh đọc dùng
`expandLookups` (xem [Record liên kết](#record-liên-kết)). Lệnh đọc qua `data`
trong trigger tuân theo cùng quy tắc như trong script, kể cả `fields` bắt buộc. Với thay
đổi do người dùng thực hiện, `data.object()` đọc dưới danh tính người đó, nên
`records.aggregate` của nó có giới hạn của `data.asUser()`: dùng `data.asSystem()` để
nhóm (xem [Aggregate](#aggregate)).

### Validate và sửa record

Mục này áp dụng cho trigger before-change. Trong trigger after-change, thay đổi đã
được lưu: `addError` chỉ ghi nhận vào log của project và không được sửa `record.new`
(xem [Quy tắc thực thi after-change](#quy-tắc-thực-thi-after-change)).

`record.addError(field, code, message?)` từ chối record. `field` là field slug, hoặc
`null` với lỗi của cả record. `code` bắt đầu bằng chữ ASCII in hoa, chỉ chứa chữ in
hoa, số hoặc `_`; tối đa 64 ký tự, ví dụ `AMOUNT_TOO_LARGE`. `message` là đoạn văn
bản tiếng Anh tuỳ chọn, tối đa 500 ký tự, được Cogover hiển thị cho người dùng cuối
khi chưa có bản dịch cho mã lỗi; message rỗng bị bỏ qua. Đối số không hợp lệ ném
`ValidationError`. Một record có thể nhận nhiều lỗi.

Record bị từ chối sẽ không được lưu, và mọi thay đổi handler đã thực hiện trên record
đó bị huỷ bỏ. Bên ghi nhận HTTP 400 với `msg: "BEFORE_CHANGE_TRIGGER_REJECTED"`, các
mã lỗi trong `meta` theo field slug (`$record` với lỗi của cả record) và các đoạn văn
bản tuỳ chọn trong `messages` theo mã lỗi. Thao tác ghi một record bị từ chối sẽ dừng
ở trigger đầu tiên báo lỗi. Trong batch write, chỉ các dòng bị từ chối thất bại, và
dòng đã bị từ chối không được chuyển tới các trigger chạy sau.

Khi bên ghi là script của một Custom Backend Module, không có gì được lưu và lời gọi
`records.create`, `records.update` hoặc thao tác ghi khác của script ném:

- `ValidationError` có `details.reason` là `"TRIGGER_REJECTED"` và `details.r` là `70`
  khi một trigger từ chối record. `details` còn có `operation`, `objectSlug`, và
  `triggerKey` khi Cogover biết trigger nào từ chối. Khi Cogover nhận được mã lỗi và đoạn
  văn bản của trigger, `details.fieldErrors` ánh xạ từng field slug (`$record` với cả
  record) tới mã lỗi và `details.messages` liệt kê các đoạn văn bản; đừng dựa vào việc
  chúng luôn có mặt.
- `RetryableError` có `details.reason` là `"TRIGGER_FAILED"` và `details.r` là `71` khi
  trigger không đưa ra được quyết định, ví dụ vì ném lỗi hoặc vượt `timeoutMs`. Thao tác
  ghi có thể thành công khi thực hiện lại sau; trong trigger after-change hoặc job, để
  lỗi này thoát ra sẽ khiến Cogover chạy lại handler.

Lời từ chối trong `batchInsert` hoặc `batchUpdate` không ném lỗi: chỉ các row bị từ chối
thất bại, và kết quả của mỗi row đó có `r` là `70` cùng `fieldErrors` và `messages` như
trên. `deleteMany` xoá các record không bị trigger nào từ chối, liệt kê từng ID bị từ chối
trong `notDeleted` và `recordErrors`; lời gọi chỉ ném lỗi khi mọi record đều bị từ chối
(xem [Record API](#record-api)).

Để sửa giá trị sẽ được lưu, hãy gán field của `record.new`:

```typescript
record.new.approval_level = "high";
record.new.customer = "ACC-1";   // cùng định dạng với input của records.update()
record.new.note = null;          // xoá giá trị của field
```

- Chỉ các field trong `writableFields` được thay đổi. Khi handler kết thúc, SDK so
  sánh từng field cấp cao nhất của `record.new` với snapshot được chụp trước khi
  handler chạy, bằng phép so sánh sâu theo JSON. Sửa bất kỳ field nào khác, kể cả
  `id`, sẽ ném `ValidationError` nêu tên field và thao tác ghi thất bại.
- Giá trị được gán dùng cùng định dạng với input của `records.update` và phải là dữ
  liệu JSON. `NaN`, function, `Map`, `Set` và class instance bị từ chối; `Date` được
  gửi dưới dạng chuỗi ISO 8601. Field `date_time` nhận epoch milliseconds và field
  `date` nhận chuỗi `"yyyy-MM-dd"`; chuỗi ISO, như một `Date`, ghi vào field `date_time`
  được lưu đúng thời điểm đó, còn ghi vào field `date` được lưu thành ngày theo UTC.
  Gán `null` sẽ xoá giá trị của field; gán `undefined` hoặc xoá
  field có cùng tác dụng.
- Thay đổi bên trong giá trị dạng mảng hoặc object được phát hiện và toàn bộ giá trị
  của field sẽ được gửi đi.
- Không thể thay thế chính `record.new`, và record đang bị xoá không có gì để sửa.
- Cogover validate lại giá trị cuối cùng trước khi lưu, gồm kiểu dữ liệu và các quy
  tắc required, unique, duplicate. Với các field do trigger sửa, thiết lập cho phép
  tạo/sửa thủ công của field và quyền sửa field của bên ghi không được áp dụng.
  Field read-only như formula, auto number, rollup và field hệ thống luôn bị từ chối.

### Quy tắc thực thi before-change

Trigger before-change chạy cho mọi nguồn ghi: ứng dụng web Cogover, API key, import,
automation process, Custom Backend Module khác và thao tác ghi qua `data.asUser()`
hoặc `data.asSystem()`. Các thao tác ghi bảo trì do chính Cogover thực hiện — tính
lại field formula và rollup, merge record chạy nền, cascade delete — không chạy
trigger before-change; request chỉ validate input mà không lưu cũng vậy.

- **Chỉ đọc.** Trigger before-change được đọc record và schema, nhưng mọi thao tác
  ghi record, `fetch`, lock, ghi state, push message, notification, email (kể cả
  `email.senders()`), `jobs.enqueue`, `secrets.get` và mọi thao tác `crypto` với key
  `{ secret }` đều bị từ chối bằng
  `PermissionDeniedError` có `details.reason` là `"TRIGGER_READ_ONLY"`. Quy tắc này
  áp dụng cho mọi danh tính, kể cả `data.asSystem()`. Mọi thao tác `crypto` với key
  truyền trực tiếp trong lời gọi vẫn dùng được, cùng với `crypto.sha256`,
  `crypto.randomBytes`, `crypto.randomUUID`, `crypto.timingSafeEqual` và mọi thao tác
  đọc [`org`](#cơ-cấu-tổ-chức).
- **Danh tính.** `data.object()` thực hiện dưới danh tính người đã tạo ra thay đổi,
  với quyền của người đó, và `invocation` mô tả chính người này. Khi thay đổi không
  có người dùng, `invocation.identity` là `"system"` và `data.object()` chỉ hoạt động
  nếu identity policy đã duyệt của project đặt `allowInternalSystem: true`; nếu
  không, các lời gọi của nó ném `PermissionDeniedError` có `details.reason` là
  `"IDENTITY_NOT_GRANTED"` trong khi handler vẫn nhận `records`. `data.asUser()` và
  `data.asSystem()` tuân theo identity policy của project như thông thường.
- **Fail closed.** Khi handler ném lỗi, vượt `timeoutMs`, vượt giới hạn runtime hoặc
  không thể chạy, thao tác ghi bị từ chối và không có gì được lưu. Bên ghi nhận
  `msg: "BEFORE_CHANGE_TRIGGER_FAILED"`, không kèm chi tiết nội bộ.
- **Thời gian.** Mỗi lần gọi phải hoàn tất trong `timeoutMs`. Mọi trigger
  before-change của một thao tác ghi dùng chung tổng thời gian 8 giây.
- **Lệnh đọc làm chậm thao tác ghi.** Thao tác ghi của người dùng phải chờ trong lúc
  handler đọc. Mỗi lookup được mở rộng đọc thêm một Object, còn `records.aggregate`,
  được phép dùng, tính từ search index chậm khoảng một giây: nó không tính thay đổi đang
  được ghi và có thể thiếu các thay đổi vừa lưu ngay trước đó. Hạn chế số lời gọi như vậy.

### Quy tắc thực thi after-change

Trigger after-change (`timing: "afterChange"`) chạy bất đồng bộ, ngay sau khi thay
đổi đã được lưu. Dùng trigger này cho các việc tiếp theo như tạo hoặc cập nhật record
liên quan, hoặc thông báo cho hệ thống khác. Trigger chạy cho cùng các nguồn ghi như
trigger before-change, với cùng các ngoại lệ.

```typescript
import { defineTrigger, fetch, RetryableError } from "@cogover/sdk";

export const triggers = [
  defineTrigger({
    key: "order_confirmed_notify",
    object: "order",
    timing: "afterChange",
    operations: ["create", "update"],
    fields: ["status", "amount"],
    changedFields: ["status"],
    when: { op: "=", field: "status", params: "confirmed" },
    runWhen: "onEnter",
  }, async ({ records, trigger }) => {
    for (const record of records) {
      const response = await fetch("https://erp.example.com/orders", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          // Cùng một thay đổi của cùng một record luôn tạo ra cùng một key.
          "idempotency-key": `${trigger.changeId}:${record.id}`,
        },
        body: JSON.stringify({ id: record.id, amount: record.new.amount }),
      });
      if (response.status >= 500) {
        throw new RetryableError("The ERP is temporarily unavailable");
      }
    }
  }),
];
```

- **Không thể chặn hay sửa record đã lưu.** Bên ghi đã nhận response. Không được
  khai báo `writableFields`, và sửa `record.new` làm lần gọi thất bại với
  `ValidationError`. `record.addError()` không từ chối gì cả: các lỗi được báo chỉ
  được ghi vào log của project. Để sửa record, hãy gọi `records.update`; đó là một
  thao tác ghi mới và sẽ chạy lại các trigger.
- **Giá trị đã lưu.** `record.id` luôn có giá trị. `record.new` chứa giá trị đúng như
  đã lưu, gồm record ID và các giá trị được gán trong lúc lưu, ví dụ auto number. Với
  record bị xoá, `record.new` là `null` và `record.old` chứa giá trị cuối cùng.
- **Được ghi và gọi ra ngoài.** Ghi record, `fetch`, `push`, `notifications`, `email`,
  `jobs.enqueue`, `secrets.get` và `crypto` hoạt động như trong script, với cùng các giới
  hạn runtime.
  `data.object()` thực hiện dưới danh tính người đã tạo ra thay đổi, và các quy tắc
  danh tính khác của trigger before-change cũng được áp dụng. Context của trigger
  không có `state` và `locks`; `push` là cách thông thường để làm mới các record
  handler đã sửa cho mọi người đang mở chúng, còn việc dài hơn, hoặc việc cần
  `state`/`locks`, thì enqueue một [background job](#background-job).
- **Best-effort.** Cogover không bảo đảm handler after-change chạy đúng một lần.
  Handler đôi khi có thể chạy nhiều hơn một lần cho cùng một thay đổi, hoặc không
  chạy. Hãy viết mọi handler theo kiểu idempotent: `trigger.changeId` cùng với
  `record.id` xác định một thay đổi của một record. Không bao giờ để trigger
  after-change là bảo đảm duy nhất cho một quy tắc quan trọng; hãy áp các quy tắc đó
  trong trigger before-change.
- **Retry.** Ném `RetryableError` khi handler thất bại vì lý do tạm thời, ví dụ dịch
  vụ bên ngoài không sẵn sàng. Cogover sẽ chạy lại handler sau: mặc định tối đa thêm
  5 lần, mỗi lần chờ lâu hơn, từ khoảng một giây đến khoảng mười phút. Lần gọi vượt
  `timeoutMs`, hoặc lần gọi Cogover không chạy được vì lý do tạm thời, cũng được thử
  lại theo cách đó. Mọi lỗi khác không được retry: lỗi được ghi log và handler không
  chạy lại cho thay đổi đó. Khi đã hết số lần retry, handler cũng không chạy lại cho
  thay đổi đó.
- **Vòng lặp luôn kết thúc.** Thao tác ghi do trigger thực hiện sẽ chạy lại các
  trigger, có thể gồm chính trigger đó. Cogover giới hạn các chuỗi như vậy: mỗi thao
  tác ghi tự động dùng một bước trong một ngân sách cố định (10 bước với thay đổi do
  người dùng hoặc API client thực hiện trực tiếp), và trigger after-change không còn
  chạy khi ngân sách đã hết. Dùng `changedFields`, `when` và `runWhen: "onEnter"` để
  thao tác ghi của chính handler không kích hoạt lại nó.
- **Thứ tự và thời gian.** Mỗi lần gọi phải hoàn tất trong `timeoutMs`. Các trigger
  after-change của một thay đổi chạy độc lập với nhau: không dựa vào thứ tự tương đối
  giữa chúng. Lần gọi được retry có thể chạy sau khi một thay đổi mới hơn của cùng
  record đã được xử lý, vì vậy hãy đọc lại record khi cần giá trị mới nhất.

## Background job

Background job chạy code của project ngoài một HTTP request: được enqueue bởi
script, trigger, job khác hoặc quản trị viên, hoặc được khởi chạy theo lịch cron.
Khai báo từng job bằng `defineJob` và liệt kê kết quả trong named export `jobs`
của project. Default export vẫn là HTTP handler và trở thành tuỳ chọn với project
chỉ khai báo job và trigger.

Ví dụ này giả định `workspace.d.ts` đã khai báo Object `order` và các field được
sử dụng bên dưới.

```typescript
import { defineJob } from "@cogover/sdk";

interface RecalcPayload {
  cursor?: string;
}

export const jobs = [
  // Được enqueue từ route hoặc trigger; duyệt toàn bộ order, mỗi lần chạy một trang.
  defineJob<RecalcPayload>({
    key: "recalc_totals",
    name: "Recalculate order totals",
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
      // Tiếp tục trang kế tiếp trong một lần chạy mới thay vì một lần chạy dài.
      await jobs.enqueue("recalc_totals", { cursor: page.nextCursor });
      return;
    }
    log.info("Order totals recalculated");
  }),

  // Chạy hằng ngày lúc 02:00 theo múi giờ đã cho.
  defineJob({
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
  }),
];
```

Cogover đọc cấu hình job khi một version của project được publish và áp dụng cấu
hình đó trong thời gian version ấy đang active: `jobs.enqueue` chỉ nhận các key do
version active khai báo, và lịch chỉ chạy khi version của nó đang active. Deactivate
project sẽ gỡ các lịch của project. Một project khai báo tối đa 50 job.

### `defineJob(config, handler): JobDefinition`

```typescript
function defineJob<
  Payload = unknown,
  Schema extends object = EffectiveWorkspaceObjects,
>(config: JobConfig, handler: JobHandler<Payload, Schema>): JobDefinition;
```

`Payload` là kiểu của giá trị truyền cho `jobs.enqueue`; giá trị này không được
validate lúc chạy, nên hãy xử lý payload như input của request. `defineJob`
validate cấu hình ngay lập tức và ném `ValidationError` với mọi vi phạm, với key cấu
hình không xác định hoặc với handler không phải function. Hàm trả về một
`JobDefinition` đã freeze.

```typescript
interface JobConfig {
  readonly key: string;
  readonly name?: string;
  readonly timeoutMs?: number;
  readonly maxAttempts?: number;
  readonly schedule?: JobSchedule;
}

interface JobSchedule {
  readonly cron: string;
  readonly timezone?: string;
}
```

| Tuỳ chọn | Bắt buộc | Quy tắc và ý nghĩa |
|---|---|---|
| `key` | Có | Định danh job trong project. Bắt đầu bằng chữ cái ASCII, chứa chữ cái, chữ số hoặc `_`; tối đa 100 ký tự; duy nhất trong project không phân biệt hoa thường. Giữ key ổn định giữa các version: key mới là một job khác. |
| `name` | Không | Tên hiển thị tối đa 250 ký tự. Mặc định là `key`. |
| `timeoutMs` | Không | Số nguyên từ 1000 đến 60000; mặc định `30000`. Thời gian cho một lần thử. |
| `maxAttempts` | Không | Số nguyên từ 1 đến 10; mặc định `5`. Tổng số lần thử của một lần chạy, tính cả lần đầu. |
| `schedule` | Không | Chạy job tự động. `cron` có năm trường — phút, giờ, ngày trong tháng, tháng, thứ — và `timezone` là IANA time zone ID tối đa 64 ký tự, mặc định `"UTC"`. |

Một trường cron là `*`, một số, khoảng `a-b`, danh sách `a,b`, bước `*/n` hoặc
khoảng có bước `a-b/n`; các trường nhận phút 0–59, giờ 0–23, ngày 1–31, tháng 1–12
và thứ 0–7 trong đó cả 0 và 7 đều là Chủ nhật. Tên như `MON`, các ký tự `L`, `W`,
`#`, `?` và macro như `@daily` không được hỗ trợ. Chu kỳ ngắn nhất là một phút.
Khoảng trắng giữa các trường được chuẩn hoá thành một dấu cách trong manifest, và biểu
thức sau khi chuẩn hoá dài tối đa 128 ký tự; biểu thức dài hơn ném `ValidationError`.
Cogover lưu time zone ở dạng chuẩn hoá, nên offset như `UTC+7` được liệt kê là
`UTC+07:00` trong danh sách lịch của project.

### `JobDefinition` và `JobManifest`

```typescript
interface JobManifest {
  readonly key: string;
  readonly name?: string;
  readonly timeoutMs: number;
  readonly maxAttempts: number;
  readonly schedule?: { readonly cron: string; readonly timezone: string };
}

interface JobDefinition {
  readonly key: string;
  readonly config: JobManifest;
  readonly __cogoverJobHandler: SandboxHandler;
}
```

`config` là cấu hình đã chuẩn hoá dưới dạng JSON thuần được deep-freeze, với mọi
giá trị mặc định đã áp dụng: `timeoutMs: 30000`, `maxAttempts: 5` và
`schedule.timezone: "UTC"`. Các thiết lập tuỳ chọn không được cung cấp sẽ vắng mặt.
`config` tách khỏi object đã truyền cho `defineJob`, nên sửa object đó về sau không
có tác dụng. `__cogoverJobHandler` dành riêng cho Cogover; code của project không
gọi nó.

### Context của job handler

```typescript
type JobHandler<
  Payload = unknown,
  Schema extends object = EffectiveWorkspaceObjects,
> = (context: JobContext<Payload, Schema>) => void | Promise<void>;

interface JobContext<Payload = unknown, Schema extends object = EffectiveWorkspaceObjects> {
  readonly job: JobInfo;
  readonly payload: Payload | null;
  readonly invocation: InvocationContext;
  readonly data: DataApi<Schema>;
  readonly schema: SchemaApi<Schema>;
  readonly log: ScriptLogger;
  readonly state: ProjectState;
  readonly locks: DistributedLocks;
  readonly notifications: NotificationsApi;
  readonly email: EmailApi<Schema>;
  readonly jobs: JobsApi;
  readonly secrets: SecretsApi;
  readonly crypto: CryptoApi;
  readonly org: OrgApi;
}

interface JobInfo {
  readonly id: string;
  readonly key: string;
  readonly attempt: number;
  readonly maxAttempts: number;
  readonly source: "enqueue" | "schedule";
  readonly runAt: number;
  readonly enqueuedAt?: number;
}
```

Handler có thể đồng bộ hoặc bất đồng bộ; giá trị trả về bị bỏ qua. `data`,
`schema`, `log`, `invocation`, `state`, `locks`, `notifications`, `email`, `jobs`,
`secrets`, `crypto` và `org` là chính các API mà script nhận được. Job context không có
`input`, `request`, `response` hay `push`.

- `job.id` định danh lần chạy và không đổi qua các lần thử; dùng nó làm idempotency
  key cho các lời gọi ra ngoài. `job.attempt` bắt đầu từ 1.
- `job.source` là `"enqueue"` với lần chạy do `jobs.enqueue` hoặc quản trị viên tạo
  và `"schedule"` với lần chạy do lịch của job tạo. `job.runAt` là thời điểm lần
  chạy đến hạn và `job.enqueuedAt` là thời điểm được enqueue; cả hai là Unix
  millisecond, và `enqueuedAt` vắng mặt với lần chạy theo lịch.
- `payload` là giá trị JSON đã truyền cho `jobs.enqueue`, hoặc `null` khi không
  truyền gì hoặc lần chạy theo lịch. Đây là dữ liệu thuần, có thể sửa.

### `jobs.enqueue(jobKey, payload?, options?): Promise<EnqueueResult>`

```typescript
interface JobsApi {
  enqueue(jobKey: string, payload?: unknown, options?: EnqueueOptions): Promise<EnqueueResult>;
}

interface EnqueueOptions {
  readonly delayMs?: number;
  readonly runAt?: number;
  readonly idempotencyKey?: string;
}

interface EnqueueResult {
  readonly runId: string;
  readonly duplicate: boolean;
}
```

```typescript
const { runId, duplicate } = await jobs.enqueue("sync_order", { orderId: order.id }, {
  delayMs: 60_000,
  idempotencyKey: `sync_order:${order.id}:${order.system.updatedAt}`,
});
```

`jobKey` phải là job do version active khai báo; nếu không, Cogover ném
`ValidationError`. `payload` là giá trị JSON bất kỳ, tối đa 65.536 byte UTF-8 của dạng
`JSON.stringify`, trong đó dấu ngoặc kép, dấu gạch chéo ngược hoặc ký tự điều khiển được
tính theo chuỗi escape của nó; `undefined` và `null` enqueue lần chạy không có payload. Giá trị mà
JSON sẽ âm thầm thay đổi, như `NaN` hoặc instance của class, bị từ chối bằng
`ValidationError`. `delayMs` là số nguyên từ 0 đến 2.592.000.000 (30 ngày) và
`runAt` là thời điểm Unix millisecond không quá 30 ngày tới; truyền một trong hai
hoặc không truyền, không truyền cả hai. `idempotencyKey` bắt đầu bằng chữ cái hoặc
chữ số, chứa chữ cái, chữ số, `.`, `_`, `:` hoặc `-`, tối đa 128 ký tự: lần enqueue
thứ hai của cùng job với cùng key khi lần chạy trước còn được lưu sẽ trả về lần
chạy đó với `duplicate: true` thay vì tạo thêm. Lịch sử lần chạy được giữ 7 ngày.

`enqueue` hoạt động trong script và route, trigger after-change, job và lời gọi
inbound webhook. Trigger before-change bị từ chối bằng `PermissionDeniedError`
(`details.reason === "TRIGGER_READ_ONLY"`), phiên phát triển local không có quyền
ghi cũng vậy (`"DEVELOPMENT_SESSION_READ_ONLY"`). Một invocation enqueue tối đa
50 lần chạy, và một project có tối đa 10.000 lần chạy đang chờ hoặc đang chạy; vượt
quá sẽ ném `RateLimitError`. HTTP route hoặc trigger sẽ dùng hết ngân sách 20
capability call trước (xem [Giới hạn của một lần thực thi](#giới-hạn-của-một-lần-thực-thi)),
nên ở đó không chạm tới giới hạn 50 lần enqueue. Khi job chưa được bật cho Workspace,
lỗi là `CogoverApiError` với `code: "JOBS_DISABLED"`.

### Quy tắc thực thi job

- **Danh tính.** Lần chạy được enqueue từ script, route hoặc trigger chạy dưới danh
  tính người dùng của invocation đó: `invocation` mô tả người dùng ấy và
  `data.object()` thực hiện với quyền của người ấy. Lần chạy do Super Admin enqueue
  qua API quản lý job cũng chạy dưới danh tính Super Admin đó, và lịch sử lần chạy ghi
  `enqueuedBy: "management"`. Lần chạy theo lịch và lần chạy được enqueue từ lời gọi
  inbound webhook không có người dùng: `invocation.identity` là `"system"`, và `data.object()` chỉ hoạt động
  nếu identity policy đã duyệt của project đặt `allowInternalSystem: true`; nếu
  không, các lời gọi của nó ném `PermissionDeniedError` có `details.reason` là
  `"IDENTITY_NOT_GRANTED"`. `data.asUser()` và `data.asSystem()` tuân theo identity
  policy như thông thường. Trong lần chạy có người dùng, `records.aggregate` qua
  `data.object()` có giới hạn của `data.asUser()`; dùng `data.asSystem()` để nhóm (xem
  [Aggregate](#aggregate)).
- **Capability.** Job được đọc và ghi record, gọi `fetch`, dùng `state` và `locks`,
  gửi notification và email, enqueue job, đọc secret và dùng `crypto`, trong giới hạn
  runtime của làn job.
- **Thời gian.** Mỗi lần thử phải hoàn tất trong `timeoutMs`. Việc cần lâu hơn phải
  được chia nhỏ: xử lý một trang, lưu cursor và enqueue lại chính job đó với cursor
  trong payload, như ví dụ ở trên.
- **Ít nhất một lần.** Cogover không bảo đảm một lần chạy được thực thi đúng một
  lần: lần thử bị gián đoạn, ví dụ do restart, sẽ được bắt đầu lại. Hãy viết mọi
  handler theo kiểu idempotent. `job.id` định danh lần chạy qua các lần thử, và
  `idempotencyKey` của `enqueue` ngăn tạo lần chạy trùng.
- **Retry.** Ném `RetryableError` khi handler thất bại vì lý do tạm thời, ví dụ dịch
  vụ bên ngoài không sẵn sàng. Cogover sẽ thử lại sau, mỗi lần chờ lâu hơn, từ vài
  giây đến khoảng nửa giờ, cho đến khi đã thử đủ `maxAttempts` lần. Lần thử vượt
  `timeoutMs`, hoặc lần thử Cogover không chạy được vì lý do tạm thời, cũng được thử
  lại theo cách đó. Mọi lỗi khác kết thúc lần chạy với trạng thái thất bại: lỗi được
  ghi log và handler không chạy lại cho lần chạy đó.
- **Thứ tự và đồng thời.** Các lần chạy thực thi không theo thứ tự bảo đảm, và hai
  lần chạy của cùng project, kể cả cùng job, có thể thực thi cùng lúc. Dùng `locks`
  khi một đoạn không được chạy đồng thời, và trì hoãn bằng `delayMs` hoặc `runAt`
  thay vì chờ bên trong handler.
- **Vòng lặp luôn kết thúc.** Thao tác ghi record do một lần chạy thực hiện mang
  ngân sách tự động hoá của invocation đã enqueue nó (lần chạy theo lịch và lần
  enqueue của quản trị viên bắt đầu với đủ ngân sách 10 bước), nên chuỗi job và
  trigger khởi phát từ thao tác ghi record kết thúc giống chuỗi trigger. Enqueue job
  không dùng bước nào: job tự enqueue chính nó phải tự dừng, ví dụ khi hết cursor.

Job theo lịch tạo một lần chạy cho mỗi thời điểm lịch khớp, theo múi giờ của lịch;
lần chạy có thể bắt đầu muộn hơn phút đã lên lịch một chút khi tải cao. Thời điểm bị
bỏ lỡ trong lúc project không active sẽ không được chạy bù. Lần chạy vẫn được tạo
khi lần chạy theo lịch trước đó chưa xong, nên lịch có việc có thể kéo dài hơn chu kỳ
của nó nên tự bảo vệ bằng lock.

## Outbound HTTP `fetch`

```typescript
function fetch(input: string, init?: CogoverFetchInit): Promise<CogoverFetchResponse>;

interface CogoverFetchInit {
  readonly method?: "GET" | "HEAD" | "POST" | "PUT" | "PATCH" | "DELETE";
  readonly headers?: Readonly<Record<string, string>>;
  readonly body?: string;
  readonly timeoutMs?: number;
  readonly credential?: string;
}

interface CogoverFetchHeaders {
  get(name: string): string | null;
  has(name: string): boolean;
  entries(): IterableIterator<[string, string]>;
  [Symbol.iterator](): IterableIterator<[string, string]>;
}

interface CogoverFetchResponse {
  readonly ok: boolean;
  readonly status: number;
  readonly statusText: string;
  readonly url: string;
  readonly redirected: false;
  readonly headers: CogoverFetchHeaders;
  readonly bodyUsed: boolean;
  text(): Promise<string>;
  json<T = unknown>(): Promise<T>;
}
```

Cogover cài đặt global `fetch()` trong hosted runtime. Import `{ fetch }` từ
`@cogover/sdk` khi muốn khai báo dependency tường minh; cách này cũng ngăn Node.js
trên máy local âm thầm dùng native `fetch` không bị giới hạn khi chạy test. Hàm
`fetch` của SDK yêu cầu Cogover runtime và luôn dùng lớp network do Cogover quản
lý. `input` phải là URL HTTPS public tuyệt đối, không chứa userinfo, fragment hoặc
IP literal, trên port 443 hoặc trên origin đã được duyệt cho project (xem
[Port khác](#port-khác)). `body` chỉ nhận string; dùng `JSON.stringify()` cho JSON.
`timeoutMs` phải là số nguyên dương và luôn bị giới hạn bởi hạn mức của platform.
Giá trị này không kéo dài lần thực thi: HTTP route mặc định có tổng cộng 8 giây, nên ở
đó server chậm hơn sẽ kết thúc toàn bộ lần thực thi (xem
[Giới hạn của một lần thực thi](#giới-hạn-của-một-lần-thực-thi)).

```typescript
import { fetch } from "@cogover/sdk";

const response = await fetch("https://api.example.com/v1/orders", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ id: "ORD-1" }),
  timeoutMs: 5_000,
});
```

`CogoverFetchResponse` có `ok`, `status`, `statusText`, `url`, `redirected` (luôn
`false`), `headers`, `bodyUsed`, `text()` và `json<T>()`. Body được buffer có giới
hạn và chỉ được đọc một lần. `headers.get(name)`, `has(name)`, `entries()` và iterator
không phân biệt hoa/thường.

V1 không tự follow redirect, không lưu/gửi cookie, không streaming request/response,
không WebSocket và không nhận `signal`, `credentials`, `redirect`, proxy, dispatcher,
agent, DNS resolver hay TLS configuration. Không hỗ trợ URL HTTP, port khác 443 mà
project chưa được duyệt, userinfo hoặc IP-literal host. Header framing/hop-by-hop/proxy/forwarding và header
request dành riêng cho Cogover bị từ chối. Request/response, header, thời gian, số call, destination
và concurrency đều có quota.

- Request `GET` hoặc `HEAD` có `body` thất bại với `FETCH_BLOCKED`.
- Response nén, tức có `Content-Encoding` khác `identity`, thất bại với `FETCH_BLOCKED`.
- Body của response được giải mã theo UTF-8: byte không hợp lệ theo UTF-8 thành U+FFFD,
  nên không đọc chính xác được nội dung nhị phân.
- Host name phân giải ra địa chỉ không phải public thất bại với `FETCH_FAILED`.
- Các lời gọi bắt đầu cùng lúc, ví dụ bằng `Promise.all`, được gửi lần lượt từng lời gọi.
- Trigger before-change không được gọi `fetch`: lời gọi ném `PermissionDeniedError` có
  `details.reason` là `"TRIGGER_READ_ONLY"`. Preview version chế độ chỉ đọc chỉ cho phép
  `GET` và `HEAD` không có `credential`, các lời gọi khác bị từ chối bằng
  `PermissionDeniedError`.

Lỗi được ném dưới dạng `CogoverApiError` với code `FETCH_DISABLED`, `FETCH_BLOCKED`,
`FETCH_REQUEST_TOO_LARGE`, `FETCH_RESPONSE_TOO_LARGE`, `FETCH_TIMEOUT` hoặc
`FETCH_FAILED`; quota dùng `RateLimitError`. Một lần thực thi gọi `fetch` tối đa 20 lần;
HTTP route hoặc trigger dùng hết ngân sách 20 capability call trước, và điều đó cũng
được báo bằng `RateLimitError` (xem
[Giới hạn của một lần thực thi](#giới-hạn-của-một-lần-thực-thi)). Với POST/PUT/PATCH/DELETE bị timeout
hoặc mất response, remote server có thể đã xử lý request. Hãy dùng idempotency key
của API đích và không retry mù.

### Port khác

Hệ thống chỉ công bố trên port khác, ví dụ `https://erp.example.com:9899`, gọi được
sau khi quản trị viên Workspace duyệt đúng origin đó trong mục `fetch` của identity
policy của project. Việc duyệt chỉ áp dụng cho các origin `https://host:port` được
liệt kê; port khác của cùng host vẫn bị chặn. Mọi quy tắc khác trong mục này vẫn áp
dụng cho origin đã duyệt: HTTPS với chứng chỉ hợp lệ cho host, chỉ địa chỉ public,
không follow redirect và cùng các giới hạn. URL trên port chưa được duyệt thất bại với
`FETCH_BLOCKED`. Request rời Cogover từ các địa chỉ outbound dùng chung với Workspace
khác, nên whitelist các địa chỉ đó trên firewall không xác định được Workspace của bạn:
hệ thống đích cần xác thực request, ví dụ bằng credential.

```typescript
// Chỉ gọi được sau khi "https://erp.example.com:9899" được duyệt cho project này.
const orders = await fetch("https://erp.example.com:9899/api/orders?status=new");
```

### Xác thực bằng credential

`credential` là tên một credential mà quản trị viên đã lưu cho project (xem
[Secret và credential](#secret-và-credential)). Cogover thêm header xác thực của
credential vào request, nên code của project không bao giờ chạm tới giá trị:

```typescript
const response = await fetch("https://erp.example.com/v1/orders", {
  method: "POST",
  credential: "erp_api",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ id: "ORD-1" }),
});
```

Tuỳ cách credential được tạo, Cogover gửi `Authorization: Bearer <value>`,
`Authorization: Basic <base64 của value>` hoặc một header với tên đã cấu hình. Tên
phải bắt đầu bằng chữ cái và chứa tối đa 64 chữ cái, chữ số hoặc dấu gạch dưới.
Credential chỉ được gửi tới các host mà quản trị viên cho phép. Host ghi không kèm
port chỉ cho phép port 443; để dùng credential với origin đã duyệt trên port khác,
quản trị viên ghi `host:port`, ví dụ `erp.example.com:9899`. Request tới host hoặc
port khác, request tự đặt cùng header, hoặc tên không phải credential đang active sẽ
thất bại với `FETCH_BLOCKED`. Redirect không bao giờ được follow, nên credential
không bao giờ rời khỏi host được phép.

## Secret và credential

Quản trị viên lưu secret cho project qua management API của Cogover. Mỗi secret
hoặc là **secret** có giá trị được code đọc bằng `secrets.get`, hoặc là
**credential** chỉ dùng cho `fetch` (xem
[Xác thực bằng credential](#xác-thực-bằng-credential)); giá trị của credential
không bao giờ đọc được từ code. Giá trị được lưu mã hoá và không bao giờ được
management API trả về, ghi log hay đưa vào thông báo lỗi.

```typescript
interface SecretsApi {
  get(name: string): Promise<string>;
}
```

```typescript
const token = await secrets.get("erp_token");
const response = await fetch("https://erp.example.com/v1/orders", {
  headers: { authorization: `Bearer ${token}` },
});
```

### `secrets.get(name): Promise<string>`

Trả về giá trị hiện tại của secret. `name` bắt đầu bằng chữ cái và chứa tối đa 64
chữ cái, chữ số hoặc dấu gạch dưới; tên khác ném `ValidationError` trước khi gọi.
Secret không tồn tại hoặc đã bị disable ném `ValidationError` với thông báo
`Secret '<name>' is not available`, còn credential ném `ValidationError` với
`Secret '<name>' is a credential and cannot be read`.

`secrets.get` hoạt động trong script và route, trigger after-change, job và lời gọi
inbound webhook. Trigger before-change bị từ chối bằng `PermissionDeniedError`
(`details.reason === "TRIGGER_READ_ONLY"`); phiên phát triển local chỉ đọc được
secret khi quản trị viên cho phép, nếu không reason là `"SECRETS_NOT_ALLOWED"`.
Một invocation đọc secret tối đa 20 lần; mọi lần đọc đều được tính, kể cả đọc lại cùng
tên và thao tác `crypto` dùng key `{ secret: name }`, và lần thứ 21 ném `RateLimitError`.
Trong HTTP route hoặc trigger, ngân sách 20 capability call sẽ hết trước (xem
[Giới hạn của một lần thực thi](#giới-hạn-của-một-lần-thực-thi)). Khi secret chưa được bật cho Workspace, lỗi là `CogoverApiError`
với `code: "SECRETS_DISABLED"`. Không bao giờ ghi giá trị secret vào log, record,
state hay response. Để ký, mã hoá hoặc giải mã bằng secret mà không đọc giá trị,
truyền `{ secret: name }` làm key của một thao tác [`crypto`](#mã-hoá-và-chữ-ký).

## Mã hoá và chữ ký

`crypto` cung cấp hash, message authentication, số ngẫu nhiên, mã hoá AES và RSA,
cùng chữ ký RSA và ECDSA qua implementation do Cogover quản lý. Import từ
`@cogover/sdk` hoặc đọc từ `context.crypto`; cả hai là cùng một object đã freeze.

```typescript
const crypto: CryptoApi;

type BinaryEncoding = "base64" | "base64url" | "hex";
type DecryptOutput = "utf8" | "bytes" | BinaryEncoding;

interface SecretKeyReference {
  readonly secret: string;
}
type AesKey =
  | string
  | Uint8Array
  | (SecretKeyReference & { readonly encoding?: "utf8" | "base64" | "hex" });
type AsymmetricKey = string | SecretKeyReference;

interface CryptoApi {
  sha256(data: string | Uint8Array, encoding?: "hex" | "base64"): Promise<string>;
  hmacSha256(
    key: string | Uint8Array | { readonly secret: string },
    data: string | Uint8Array,
    encoding?: "hex" | "base64",
  ): Promise<string>;
  randomBytes(length: number): Promise<Uint8Array>;
  randomUUID(): Promise<string>;
  timingSafeEqual(a: string | Uint8Array, b: string | Uint8Array): boolean;

  aesEncrypt(key: AesKey, data: string | Uint8Array, options?: AesEncryptOptions): Promise<AesEncryptResult>;
  aesDecrypt(key: AesKey, ciphertext: string | Uint8Array, options: AesDecryptOptions): Promise<string>;
  aesDecrypt(
    key: AesKey,
    ciphertext: string | Uint8Array,
    options: AesDecryptOptions & { readonly output: "bytes" },
  ): Promise<Uint8Array>;
  rsaEncrypt(publicKey: AsymmetricKey, data: string | Uint8Array, options?: RsaEncryptOptions): Promise<string>;
  rsaDecrypt(privateKey: AsymmetricKey, ciphertext: string | Uint8Array, options?: RsaDecryptOptions): Promise<string>;
  rsaDecrypt(
    privateKey: AsymmetricKey,
    ciphertext: string | Uint8Array,
    options: RsaDecryptOptions & { readonly output: "bytes" },
  ): Promise<Uint8Array>;
  sign(
    algorithm: SignatureAlgorithm,
    privateKey: AsymmetricKey,
    data: string | Uint8Array,
    options?: SignatureOptions,
  ): Promise<string>;
  verify(
    algorithm: SignatureAlgorithm,
    publicKey: AsymmetricKey,
    data: string | Uint8Array,
    signature: string | Uint8Array,
    options?: SignatureOptions,
  ): Promise<boolean>;
}
```

`aesDecrypt` và `rsaDecrypt` trả về chuỗi, trừ khi `output` là `"bytes"`; khi
`output` chỉ được biết là một `DecryptOutput`, kiểu kết quả là
`string | Uint8Array`.

```typescript
import { crypto } from "@cogover/sdk";

const digest = await crypto.sha256(JSON.stringify(payload));
const signature = await crypto.hmacSha256({ secret: "webhook_secret" }, request.rawBody ?? "");
if (!crypto.timingSafeEqual(signature, request.headers["x-signature"] ?? "")) {
  return response.empty({ status: 401 });
}
const token = await crypto.randomUUID();
```

### Hash, HMAC và số ngẫu nhiên

- `sha256(data, encoding?)` trả về digest SHA-256 của `data`. Chuỗi được hash dưới
  dạng UTF-8; `Uint8Array` được hash nguyên trạng. `encoding` là `"hex"` (mặc định)
  hoặc `"base64"`.
- `hmacSha256(key, data, encoding?)` trả về HMAC-SHA256 của `data`. Key là chuỗi
  không rỗng (UTF-8), `Uint8Array` không rỗng, hoặc `{ secret: name }` để dùng một
  secret của project mà không đọc giá trị.
- `randomBytes(length)` trả về `length` byte ngẫu nhiên an toàn cho mật mã;
  `length` là số nguyên từ 1 đến 1024.
- `randomUUID()` trả về UUID version 4 ngẫu nhiên như
  `"00000000-0000-4000-8000-000000000000"`. Byte ngẫu nhiên được lấy mỗi lần
  1.024 byte, nên một capability call đủ cho 64 UUID.
- `timingSafeEqual(a, b)` so sánh hai chuỗi hoặc hai mảng byte trong thời gian
  hằng và trả về `false` khi độ dài khác nhau. Chuỗi được so sánh dưới dạng byte
  UTF-8. Mỗi giá trị giới hạn 256 KiB, chuỗi tính theo số byte UTF-8; giá trị lớn
  hơn ném `ValidationError`. Dùng hàm này cho mọi phép so sánh chữ ký, token hoặc
  key.

### Key

Mọi key có thể truyền trực tiếp trong lời gọi hoặc dưới dạng `{ secret: name }`.
Key từ secret do Cogover resolve và giá trị không bao giờ tới code của project;
secret được đặt tên phải đọc được bằng `secrets.get` trong cùng context và được
tính là một lần đọc secret. Hãy lưu mọi private key và mọi AES key thành secret của
project; key viết trong source code hiển thị với mọi người đọc được project.

- **AES key** dài 16, 24 hoặc 32 byte (AES-128, AES-192, AES-256). Chuỗi được dùng
  theo byte UTF-8 của nó, `Uint8Array` được dùng nguyên trạng. Với secret,
  `encoding` cho biết giá trị secret chứa key ra sao: `"utf8"` (mặc định) dùng chính
  văn bản đó, còn `"base64"` hoặc `"hex"` giải mã trước, bỏ qua khoảng trắng ở hai
  đầu.
- **RSA key và EC key** (`AsymmetricKey`) là văn bản PEM, hoặc phần thân base64 của
  PEM không có các dòng `-----BEGIN` (DER dạng `PUBLIC KEY` cho public key và dạng
  `PRIVATE KEY` cho private key). Văn bản đứng trước khối PEM và khối
  `EC PARAMETERS` được bỏ qua.

| Key | Loại PEM được chấp nhận |
|---|---|
| Public key (`rsaEncrypt`, `verify`) | `PUBLIC KEY` (SubjectPublicKeyInfo), `RSA PUBLIC KEY` (PKCS #1), `CERTIFICATE` (X.509; chỉ dùng public key của nó) |
| Private key (`rsaDecrypt`, `sign`) | `PRIVATE KEY` (PKCS #8), `RSA PRIVATE KEY` (PKCS #1), `EC PRIVATE KEY` (SEC1) |

RSA key phải dài 2048 đến 4096 bit. EC key phải dùng curve P-256, P-384 hoặc P-521.
Private key đã mã hoá (`ENCRYPTED PRIVATE KEY`, hoặc PEM có header `Proc-Type`) và
key OpenSSH không được hỗ trợ; hãy lưu private key PKCS #8 chưa mã hoá thành secret.
Văn bản key giới hạn 16.384 ký tự. Certificate không được kiểm tra hạn dùng, thu hồi
hay bên phát hành: nó chỉ là vật chứa public key.

### `crypto.aesEncrypt(key, data, options?): Promise<AesEncryptResult>`

```typescript
type AesMode = "GCM" | "CBC";

interface AesEncryptOptions {
  readonly mode?: AesMode;              // Mặc định "GCM"
  readonly iv?: string | Uint8Array;    // Mặc định: ngẫu nhiên
  readonly aad?: string | Uint8Array;   // Chỉ GCM
  readonly separateTag?: boolean;       // Chỉ GCM, mặc định false
  readonly encoding?: BinaryEncoding;   // Mặc định "base64"
}

interface AesEncryptResult {
  readonly ciphertext: string;
  readonly iv: string;
  readonly tag?: string;                // Chỉ khi có separateTag
}
```

Mã hoá `data` (chuỗi được mã hoá dạng UTF-8) và trả về ciphertext cùng IV theo
`encoding`.

- `"GCM"` (mặc định) là mã hoá có xác thực: khi giải mã sẽ phát hiện mọi thay đổi
  của ciphertext, IV, tag hoặc `aad`. `ciphertext` là dữ liệu đã mã hoá, nối tiếp
  bởi authentication tag 16 byte, đúng dạng mà Java, .NET và Web Crypto dùng. Với
  `separateTag: true`, tag được trả riêng trong `tag`, như các hệ thống xây trên
  Node.js hoặc OpenSSL thường yêu cầu.
- `"CBC"` dùng padding PKCS #7. Mode này không phát hiện thay đổi của ciphertext;
  chỉ dùng khi hệ thống bên ngoài bắt buộc, và xác thực ciphertext bằng cách khác,
  ví dụ `hmacSha256`.
- Khi không truyền `iv`, một IV ngẫu nhiên được tạo: 12 byte cho GCM và 16 byte cho
  CBC. `iv` truyền vào phải dài 12 đến 16 byte với GCM và đúng 16 byte với CBC;
  `iv` dạng chuỗi được giải mã theo `encoding`. **Không bao giờ dùng lại cùng một IV
  với cùng một key GCM**: việc đó phá vỡ cả tính bảo mật lẫn khả năng xác thực.
  Chỉ truyền IV khi hệ thống bên ngoài quy định.
- `aad` là dữ liệu bổ sung được xác thực nhưng không mã hoá, ví dụ ID của record;
  chuỗi được mã hoá dạng UTF-8. Khi giải mã phải truyền đúng `aad` đó.

### `crypto.aesDecrypt(key, ciphertext, options): Promise<string | Uint8Array>`

```typescript
interface AesDecryptOptions {
  readonly mode?: AesMode;              // Mặc định "GCM"
  readonly iv: string | Uint8Array;
  readonly tag?: string | Uint8Array;   // Chỉ GCM, khi tag không nối vào ciphertext
  readonly aad?: string | Uint8Array;   // Chỉ GCM
  readonly encoding?: BinaryEncoding;   // Của ciphertext, iv và tag dạng chuỗi; mặc định "base64"
  readonly output?: DecryptOutput;      // Mặc định "utf8"
}
```

Giải mã một ciphertext AES. `iv` là bắt buộc. Ở mode GCM, 16 byte cuối của
`ciphertext` là tag, trừ khi truyền `tag`. `output` chọn dạng kết quả: `"utf8"`
(mặc định) giải mã plaintext thành văn bản UTF-8 và ném `ValidationError` nếu nó
không phải UTF-8 hợp lệ, `"bytes"` trả về `Uint8Array`, còn `"base64"`,
`"base64url"` hoặc `"hex"` trả về byte của plaintext theo encoding đó.

Sai key, IV, tag hoặc `aad`, ciphertext bị sửa, hoặc padding CBC không hợp lệ đều
ném `CogoverApiError` với `code: "DECRYPTION_FAILED"`. Lỗi giống nhau cho mọi
nguyên nhân để kết quả không làm lộ thông tin về key hay plaintext.

```typescript
import { crypto, CogoverApiError, defineScript } from "@cogover/sdk";

export default defineScript(async ({ request }) => {
  const { data, iv, tag } = request.body as { data: string; iv: string; tag: string };
  try {
    const json = await crypto.aesDecrypt({ secret: "partner_aes_key", encoding: "base64" }, data, { iv, tag });
    return { payment: JSON.parse(json) };
  } catch (error) {
    if (error instanceof CogoverApiError && error.code === "DECRYPTION_FAILED") {
      return { r: 1001, msg: "The payload could not be decrypted." };
    }
    throw error;
  }
});
```

### `crypto.rsaEncrypt(publicKey, data, options?)` và `crypto.rsaDecrypt(privateKey, ciphertext, options?)`

```typescript
type RsaPadding = "OAEP-SHA256" | "OAEP-SHA1" | "PKCS1";

interface RsaEncryptOptions {
  readonly padding?: RsaPadding;        // Mặc định "OAEP-SHA256"
  readonly encoding?: BinaryEncoding;   // Của ciphertext; mặc định "base64"
}

interface RsaDecryptOptions {
  readonly padding?: RsaPadding;        // Mặc định "OAEP-SHA256"
  readonly encoding?: BinaryEncoding;   // Của ciphertext dạng chuỗi; mặc định "base64"
  readonly output?: DecryptOutput;      // Mặc định "utf8"
}
```

`rsaEncrypt` mã hoá `data` (chuỗi được mã hoá dạng UTF-8) bằng RSA public key và
trả về ciphertext theo `encoding`. `rsaDecrypt` giải mã bằng private key tương ứng
và trả về plaintext theo `output`, giống `aesDecrypt`.

- `"OAEP-SHA256"` (mặc định) là RSA-OAEP với SHA-256, và hàm sinh mask MGF1 cũng
  dùng SHA-256, như Web Crypto, Node.js và OpenSSL. `"OAEP-SHA1"` dùng SHA-1 cho
  cả hai. Một số code Java viết `OAEPWithSHA-256AndMGF1Padding` vẫn để MGF1 dùng
  SHA-1 và không tương thích với cả hai lựa chọn; hãy hỏi hệ thống bên kia MGF1 của
  họ dùng digest nào.
- `"PKCS1"` là padding PKCS #1 v1.5. Chỉ dùng khi hệ thống bên ngoài bắt buộc.
- RSA chỉ mã hoá được lượng dữ liệu nhỏ: tối đa bằng kích thước key tính theo byte
  trừ 66 byte với `"OAEP-SHA256"`, trừ 42 với `"OAEP-SHA1"` và trừ 11 với
  `"PKCS1"` — tức 190, 214 và 245 byte với key 2048 bit. Dữ liệu lớn hơn ném
  `ValidationError`. Để gửi nhiều hơn, mã hoá dữ liệu bằng `aesEncrypt` với một key
  ngẫu nhiên từ `randomBytes(32)` và chỉ mã hoá key đó bằng `rsaEncrypt`.
- Giải mã thất bại vì bất kỳ lý do nào đều ném `CogoverApiError` với
  `code: "DECRYPTION_FAILED"`.

```typescript
const cardToken = await crypto.rsaEncrypt({ secret: "bank_public_key" }, "4111111111111111");
const plain = await crypto.rsaDecrypt({ secret: "our_private_key" }, request.body.data as string);
```

### `crypto.sign(algorithm, privateKey, data, options?)` và `crypto.verify(algorithm, publicKey, data, signature, options?)`

```typescript
type SignatureAlgorithm =
  | "RSA-SHA1" | "RSA-SHA256" | "RSA-SHA384" | "RSA-SHA512"
  | "RSA-PSS-SHA256" | "RSA-PSS-SHA384" | "RSA-PSS-SHA512"
  | "ECDSA-SHA256" | "ECDSA-SHA384" | "ECDSA-SHA512";

interface SignatureOptions {
  readonly encoding?: BinaryEncoding;                // Của chữ ký; mặc định "base64"
  readonly signatureFormat?: "der" | "ieee-p1363";   // Chỉ ECDSA; mặc định "der"
}
```

`sign` ký `data` (chuỗi được mã hoá dạng UTF-8) bằng private key và trả về chữ ký
theo `encoding`. `verify` trả về `true` khi `signature` là chữ ký hợp lệ của `data`
với public key, và `false` trong mọi trường hợp khác, kể cả khi chữ ký không giải
mã được hoặc sai độ dài; chữ ký thường đến từ chính bên cần xác minh nên chữ ký sai
định dạng không phải là lỗi. Chữ ký dài hơn 2.048 ký tự, hoặc 1.024 byte khi là
`Uint8Array`, được coi là không hợp lệ mà không được gửi đi. Key hoặc thuật toán không
hợp lệ vẫn ném `ValidationError`, bất kể chữ ký.

- `RSA-SHA*` là RSASSA-PKCS1-v1_5 và cần RSA key. `RSA-SHA1` chỉ để xác minh chữ ký
  của các hệ thống còn dùng nó; không dùng cho chữ ký mới.
- `RSA-PSS-SHA*` là RSASSA-PSS với MGF1 cùng digest và salt dài bằng digest (32, 48
  hoặc 64 byte), và cần RSA key.
- `ECDSA-SHA*` cần EC key. `signatureFormat` là `"der"` (ASN.1, dùng bởi OpenSSL và
  Java) hoặc `"ieee-p1363"` (dạng `r || s` độ dài cố định, dùng bởi JWT và Web
  Crypto); tuỳ chọn này bị từ chối với thuật toán RSA.

| JWT `alg` | `algorithm` | Options |
|---|---|---|
| `RS256`, `RS384`, `RS512` | `RSA-SHA256`, `RSA-SHA384`, `RSA-SHA512` | `{ encoding: "base64url" }` |
| `PS256`, `PS384`, `PS512` | `RSA-PSS-SHA256`, `RSA-PSS-SHA384`, `RSA-PSS-SHA512` | `{ encoding: "base64url" }` |
| `ES256`, `ES384`, `ES512` | `ECDSA-SHA256`, `ECDSA-SHA384`, `ECDSA-SHA512` | `{ encoding: "base64url", signatureFormat: "ieee-p1363" }` |

```typescript
// Xác minh JWT ES256 do đối tác phát hành. Kiểm tra thêm claim (exp, iss, aud) trước khi tin cậy.
const [header, payload, signature] = token.split(".");
const valid = await crypto.verify("ECDSA-SHA256", { secret: "partner_jwt_public_key" },
  `${header}.${payload}`, signature ?? "", { encoding: "base64url", signatureFormat: "ieee-p1363" });
if (!valid) return response.empty({ status: 401 });

// Ký request gửi ngân hàng yêu cầu SHA256withRSA dạng base64.
const body = JSON.stringify(order);
const bankSignature = await crypto.sign("RSA-SHA256", { secret: "bank_signing_key" }, body);
```

### Giới hạn và phạm vi sử dụng

`data`, `aad` và HMAC key tường minh giới hạn 256 KiB, ciphertext giới hạn 256 KiB
cộng tag; giá trị lớn hơn và đối số không hợp lệ ném `ValidationError` trước khi
gọi. Toàn bộ lời gọi cũng phải vừa một capability request, mặc định 262.144 byte (xem
[Giới hạn của một lần thực thi](#giới-hạn-của-một-lần-thực-thi)): mọi đối số
được gửi trong một request đã mã hoá JSON, và `Uint8Array` được gửi dạng base64, lớn
hơn một phần ba. Vì vậy dữ liệu nhị phân lớn hơn khoảng 190 KiB, hoặc dữ liệu text gần
256 KiB cùng các đối số khác, sẽ ném `ValidationError` trước khi gọi dù từng giá trị vẫn
trong giới hạn riêng của nó. Các lỗi về key, thuật toán và tuỳ chọn do Cogover phát hiện, như key sai kích
thước hoặc sai loại, cũng ném `ValidationError`. Mọi thao tác trừ `timingSafeEqual`
là một capability call và được tính vào giới hạn của invocation; `randomUUID` gọi một
lần cho mỗi 64 UUID.

Các thao tác hoạt động trong mọi context, kể cả trigger before-change, khi key được
truyền trực tiếp trong lời gọi. Key `{ secret }` tuân theo quy tắc của
`secrets.get`: trigger before-change bị từ chối bằng `PermissionDeniedError`
(`details.reason === "TRIGGER_READ_ONLY"`), còn phiên phát triển local không có
quyền đọc secret bị từ chối với `details.reason === "SECRETS_NOT_ALLOWED"`.

## Inbound webhook

Quản trị viên có thể tạo **inbound access** cho project để một hệ thống bên ngoài
gọi route mà không cần phiên người dùng Cogover. Hệ thống bên ngoài nhận URL có dạng

```text
https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/{projectSlug}/hooks/{inboundId}/{route}
```

và xác thực mỗi lời gọi bằng inbound key hoặc chữ ký HMAC đã cấu hình cho inbound
access. Cogover kiểm tra key hoặc chữ ký, áp dụng rate limit và từ chối lời gọi
trước khi bất kỳ code nào của project chạy. Route handler thấy lời gọi như vậy với
`request.path === "/hooks/{route}"`: đăng ký route webhook dưới `/hooks/`, và
inbound ID không nằm trong path.

```typescript
import { createRouter } from "@cogover/sdk";

const router = createRouter();
router.post("/hooks/payments", async ({ request, invocation, crypto, jobs, response }) => {
  if (invocation.identity !== "inbound") return response.empty({ status: 403 });

  // Tuỳ chọn: kiểm tra chữ ký riêng của hệ thống bên ngoài trên raw body.
  const expected = await crypto.hmacSha256({ secret: "payment_signing_secret" }, request.rawBody ?? "");
  if (!crypto.timingSafeEqual(expected, request.headers["x-payment-signature"] ?? "")) {
    return response.empty({ status: 401 });
  }

  const event = request.body as { id: string; orderId: string };
  await jobs.enqueue("sync_payment", event, { idempotencyKey: `payment:${event.id}` });
  return response.json({ received: true }, { status: 202 });
});
export default router.toHandler();
```

- **Danh tính.** `invocation.identity` là `"inbound"`, `invocation.user` là `null`
  và `invocation.inbound` chứa `id`, `name` và `mode` xác thực của inbound access.
  `data.object()` thực hiện dưới danh tính system và chỉ hoạt động nếu identity
  policy đã duyệt của project đặt `allowInternalSystem: true`; khi đó nó có cùng quyền
  truy cập như trong job chạy theo lịch, không bị thu hẹp bởi các object được cấp cho
  `data.asSystem()`. Nếu không, các lời gọi của nó ném `PermissionDeniedError` có
  `details.reason` là `"IDENTITY_NOT_GRANTED"`. `data.asUser()` và `data.asSystem()` chỉ
  tuân theo quyền được cấp trong identity policy khi `allowInternalSystem` là `true`;
  nếu không, chúng cũng bị từ chối như vậy, kể cả với object đã được cấp.
- **Body.** Request body giới hạn 256 KiB. Khi body là JSON object, nó là
  `request.body`; body dạng form, text hoặc dạng khác để `request.body` rỗng (`{}`).
  `request.rawBody` luôn chứa body đúng như đã nhận, dưới dạng chuỗi UTF-8, và
  `request.contentType` là `Content-Type` của request, nên handler có thể kiểm tra
  chữ ký hoặc tự parse định dạng khác.
- **Response.** Giá trị trả về của handler và các helper `response` hoạt động như
  với mọi route. Giữ handler ngắn: xác nhận sự kiện rồi enqueue một job cho việc
  thực sự, để hệ thống bên ngoài nhận trả lời nhanh và các lần retry không chồng
  lên xử lý chậm.
- **Retry.** Hệ thống bên ngoài thường gửi lại webhook không nhận được response
  2xx, nên handler có thể thấy cùng một sự kiện nhiều lần. Dùng định danh riêng của
  sự kiện làm `idempotencyKey` cho job được enqueue, hoặc làm key trong state.
  Header `Idempotency-Key` hoạt động như với mọi route. Khi inbound access kiểm tra chữ
  ký HMAC có timestamp, mỗi chữ ký chỉ được chấp nhận một lần, trước khi handler chạy:
  lần retry lặp lại cùng chữ ký bị từ chối với HTTP 401, kể cả khi lần đầu thất bại, nên
  bên gửi phải ký lại cho mỗi lần retry.

## Record API

```typescript
const orders = data.object("order");
await orders.records.get(id, { fields, expandLookups });
await orders.records.getMany(ids, { fields, expandLookups });
await orders.records.list({ where, orderBy, fields, limit, cursor, expandLookups });
await orders.records.aggregate({ where, groupBy, metrics, limit });
await orders.records.create(fields);
await orders.records.update(id, fields);
await orders.records.batchInsert(records);
await orders.records.batchUpdate(records);
await orders.records.upsertByUniqueField(matchBy, fields);
await orders.records.deleteMany(ids);
```

Mọi lệnh đọc phải nêu các field cần trả về: `fields` là bắt buộc với `get`, `getMany` và
`list` (xem [Chọn field](#chọn-field)). Lookup không được mở rộng trừ khi lệnh đọc yêu
cầu bằng `expandLookups` (xem [Record liên kết](#record-liên-kết)).

### Giá trị và kết quả record

```typescript
type CogoverRecordId = string & {
  readonly __cogoverRecordIdBrand: unique symbol;
};

interface RecordReference<ObjectSlug extends string = string> {
  readonly id: CogoverRecordId;
  // "" trừ khi lệnh đọc mở rộng lookup này; field `reference` giữ tên được lưu sẵn.
  readonly name: string;
  readonly objectSlug?: ObjectSlug;
  // Chỉ có khi lệnh đọc mở rộng lookup này và đọc được record liên kết.
  readonly fields?: ObjectSlug extends keyof WorkspaceObjects
    ? Readonly<Partial<WorkspaceObjects[ObjectSlug]>>
    : Readonly<Record<string, unknown>>;
}

interface UrlValue {
  readonly url: string;
  readonly alias?: string;
}

interface FileValue {
  readonly id: string;
  readonly name: string;
  readonly size?: number;
  readonly contentType?: string;
  readonly url?: string;
}

interface CogoverRecord<Fields> {
  readonly id: CogoverRecordId;
  readonly fields: Readonly<Fields>;
  readonly system: {
    readonly createdAt: number;
    readonly updatedAt: number;
    // `name` là "" trừ khi lệnh đọc dùng `expandLookups`.
    readonly createdBy?: { readonly id: string; readonly name: string };
  };
}

interface RecordPage<Fields> {
  readonly items: CogoverRecord<Fields>[];
  readonly total: number;
  readonly nextCursor?: string;
}

interface GetManyResult<Fields> {
  readonly records: CogoverRecord<Fields>[];
  readonly missingIds: CogoverRecordId[];
}

interface DeleteResult {
  readonly deleted: CogoverRecordId[];
  readonly notDeleted: CogoverRecordId[];
  readonly recordErrors?: Readonly<Record<CogoverRecordId, {
    readonly reason: "TRIGGER_REJECTED";
    readonly fieldErrors?: Readonly<Record<string, string>>;
    readonly messages?: readonly string[];
  }>>;
}

interface BatchWriteRowResult {
  readonly referenceId: string;
  readonly id?: CogoverRecordId;
  readonly r: number;
  readonly msg?: string;
  readonly success: boolean;
  readonly fieldErrors?: Readonly<Record<string, string>>;
  readonly messages?: readonly string[];
}

interface BatchWriteResponse {
  readonly r: number;
  readonly msg?: string;
  readonly results: readonly BatchWriteRowResult[];
  readonly success: boolean;
}

interface BatchUpdateItem<Fields> {
  readonly id: CogoverRecordId;
  readonly fields: UpdateFields<Fields>;
}

interface UpsertResult {
  readonly id: CogoverRecordId;
  readonly created: boolean;
}
```

`CogoverRecordId` là string có brand và được SDK trả về. `get` vẫn nhận string để
tra cứu theo ID. `CreateFields<Fields>` và `UpdateFields<Fields>` là mapped type
partial trên các field của workspace. Reference nhận string, `CogoverRecordId` hoặc
`RecordReference` đúng object; field dạng mảng nhận readonly array.
`UpsertFields<Fields, MatchBy>` yêu cầu match field tồn tại và không null.

### Data client và operation

```typescript
type FieldSelection<Fields> = "*" | readonly (keyof Fields & string)[];

type SelectedFields<Fields, Selection extends FieldSelection<Fields>> =
  Selection extends "*" ? Fields
  : Selection extends readonly (infer Slug)[] ? Pick<Fields, Slug & keyof Fields>
  : Fields;

type ExpandLookups<Fields> =
  | boolean
  | {
      // LookupFieldSlug: các field lookup và reference của Fields. LinkedFieldSlug: field slug
      // của Object liên kết, hoặc string bất kỳ khi Object đó chưa được khai báo.
      readonly [Slug in LookupFieldSlug<Fields>]?: "*" | readonly LinkedFieldSlug<Fields[Slug]>[];
    };

interface GetRecordOptions<Fields, Selection extends FieldSelection<Fields> = FieldSelection<Fields>> {
  readonly fields: Selection;
  readonly expandLookups?: ExpandLookups<SelectedFields<Fields, Selection>>;
}

interface GetManyOptions<Fields, Selection extends FieldSelection<Fields> = FieldSelection<Fields>> {
  readonly fields: Selection;
  readonly expandLookups?: ExpandLookups<SelectedFields<Fields, Selection>>;
}

interface ListOptions<Fields, Selection extends FieldSelection<Fields> = FieldSelection<Fields>> {
  readonly where?: FilterExpression;
  readonly orderBy?: readonly SortExpression[];
  readonly fields: Selection;
  readonly limit?: number;
  readonly cursor?: string;
  readonly expandLookups?: ExpandLookups<SelectedFields<Fields, Selection>>;
}

type AggregateMetric<Fields> =
  | { readonly count: "id" | CountableFieldSlug<Fields> }
  | { readonly countDistinct: CountableFieldSlug<Fields> }
  | { readonly sum: NumberFieldSlug<Fields> }
  | { readonly avg: NumberFieldSlug<Fields> }
  | { readonly min: NumberOrTextFieldSlug<Fields> }
  | { readonly max: NumberOrTextFieldSlug<Fields> };
// CountableFieldSlug: mọi field trừ field file và URL. NumberFieldSlug: các field có kiểu
// `number`. NumberOrTextFieldSlug: các field có kiểu `number` hoặc `string` (`date` là
// string). Mỗi loại là string bất kỳ khi Fields chưa được khai báo.

type AsUserAggregateMetric<Fields> =
  | { readonly count: "id" | NumberFieldSlug<Fields> }
  | { readonly sum: NumberFieldSlug<Fields> }
  | { readonly avg: NumberFieldSlug<Fields> }
  | { readonly min: NumberFieldSlug<Fields> }
  | { readonly max: NumberFieldSlug<Fields> };

type AggregateMetrics<Fields> = Readonly<Record<string, AggregateMetric<Fields>>>;
type AsUserAggregateMetrics<Fields> = Readonly<Record<string, AsUserAggregateMetric<Fields>>>;

interface AggregateOptions<
  Fields,
  Metrics extends AggregateMetrics<Fields> | AsUserAggregateMetrics<Fields> = AggregateMetrics<Fields>,
> {
  readonly where?: FilterExpression;
  readonly metrics: Metrics;
  readonly groupBy?: never;
  readonly limit?: never;
}

interface GroupedAggregateOptions<
  Fields,
  Metrics extends AggregateMetrics<Fields> = AggregateMetrics<Fields>,
  GroupBy extends readonly (keyof Fields & string)[] = readonly (keyof Fields & string)[],
> {
  readonly where?: FilterExpression;
  readonly groupBy: GroupBy;
  readonly metrics: Metrics;
  readonly limit?: number;
}

type AggregateValues<Metrics> = {
  readonly [Name in keyof Metrics]:
    Metrics[Name] extends
      | { readonly count: string }
      | { readonly countDistinct: string }
      | { readonly sum: string }
      ? number
      : number | null;
};

type AggregateGroupKey<Fields, Slug extends keyof Fields & string> = {
  // CogoverRecordId với lookup, option slug với choice, boolean, number, và epoch
  // milliseconds (`number`) với field ngày: không nhóm được theo text nên field `string` là ngày.
  readonly [K in Slug]: GroupKeyValue<Fields[K]>;
};

interface AggregateResult<Values = Readonly<Record<string, number | null>>> {
  readonly values: Values;
}

interface AggregateGroup<
  Key = Readonly<Record<string, string | number | boolean>>,
  Values = Readonly<Record<string, number | null>>,
> {
  readonly key: Key;
  readonly values: Values;
}

interface AggregateGroupResult<
  Key = Readonly<Record<string, string | number | boolean>>,
  Values = Readonly<Record<string, number | null>>,
> {
  readonly groups: AggregateGroup<Key, Values>[];
  readonly truncated: boolean;
}

interface RecordWritesApi<Fields> {
  create(fields: CreateFields<Fields>): Promise<CogoverRecordId>;
  update(id: CogoverRecordId, fields: UpdateFields<Fields>): Promise<void>;
  batchInsert(records: readonly CreateFields<Fields>[]): Promise<BatchWriteResponse>;
  batchUpdate(records: readonly BatchUpdateItem<Fields>[]): Promise<BatchWriteResponse>;
  upsertByUniqueField<MatchBy extends keyof Fields & string>(
    matchBy: MatchBy,
    fields: UpsertFields<Fields, MatchBy>,
  ): Promise<UpsertResult>;
  deleteMany(ids: readonly CogoverRecordId[]): Promise<DeleteResult>;
}

interface AsUserRecordsApi<Fields> extends RecordWritesApi<Fields> {
  get<const Selection extends FieldSelection<Fields>>(
    id: string,
    options: GetRecordOptions<Fields, Selection>,
  ): Promise<CogoverRecord<SelectedFields<Fields, Selection>> | null>;
  getMany<const Selection extends FieldSelection<Fields>>(
    ids: readonly string[],
    options: GetManyOptions<Fields, Selection>,
  ): Promise<GetManyResult<SelectedFields<Fields, Selection>>>;
  list<const Selection extends FieldSelection<Fields>>(
    options: ListOptions<Fields, Selection>,
  ): Promise<RecordPage<SelectedFields<Fields, Selection>>>;
  aggregate<const Metrics extends AsUserAggregateMetrics<Fields>>(
    options: AggregateOptions<Fields, Metrics>,
  ): Promise<AggregateResult<AggregateValues<Metrics>>>;
}

interface RecordsApi<Fields> extends AsUserRecordsApi<Fields> {
  aggregate<const Metrics extends AggregateMetrics<Fields>>(
    options: AggregateOptions<Fields, Metrics>,
  ): Promise<AggregateResult<AggregateValues<Metrics>>>;
  aggregate<
    const Metrics extends AggregateMetrics<Fields>,
    const GroupBy extends readonly (keyof Fields & string)[],
  >(
    options: GroupedAggregateOptions<Fields, Metrics, GroupBy>,
  ): Promise<AggregateGroupResult<AggregateGroupKey<Fields, GroupBy[number]>, AggregateValues<Metrics>>>;
}

interface WriteObjectClient<Fields> {
  readonly slug: string;
  readonly fields: FieldReferences<Fields>;
  readonly records: RecordWritesApi<Fields>;
}

interface ObjectClient<Fields> extends WriteObjectClient<Fields> {
  readonly records: RecordsApi<Fields>;
}

interface AsUserObjectClient<Fields> extends WriteObjectClient<Fields> {
  readonly records: AsUserRecordsApi<Fields>;
}

interface AsUserDataApi<Schema extends object = EffectiveWorkspaceObjects> {
  object<Slug extends keyof Schema & string>(slug: Slug): AsUserObjectClient<Schema[Slug]>;
}

interface DataApi<Schema extends object = EffectiveWorkspaceObjects> {
  object<Slug extends keyof Schema & string>(slug: Slug): ObjectClient<Schema[Slug]>;
  asUser(personnelId: string): AsUserDataApi<Schema>;
  asSystem(): DataApi<Schema>;
}
```

`get` trả record hoặc `null`; `list` trả `RecordPage`; kiểu field của kết quả được
thu hẹp theo `fields`.

`getMany(ids, { fields })` đọc tối đa 200 record theo ID bằng một capability call duy
nhất. `fields` là bắt buộc như mọi lệnh đọc (xem [Chọn field](#chọn-field)). ID được trim
và loại trùng theo đúng thứ tự ban đầu; nhiều hơn 200 ID duy nhất, ID rỗng hoặc danh
sách `fields` không hợp lệ sẽ ném `ValidationError` trước khi gửi request. Mảng `ids`
rỗng trả ngay `{ records: [], missingIds: [] }` mà không gửi request. Kết quả gồm
`records` đọc được và `missingIds`: mọi ID được yêu cầu nhưng không đọc được, do
record không tồn tại hoặc danh tính đang dùng không nhìn thấy record đó. ID không bao
giờ bị âm thầm bỏ qua. Thứ tự của `records` không bảo đảm trùng với `ids`, vì vậy hãy
tra cứu theo `id`:

```typescript
const accounts = data.object("account");
const { records, missingIds } = await accounts.records.getMany(accountIds, { fields: ["credit_limit"] });
const accountById = new Map(records.map(record => [record.id, record]));
```

Dùng `getMany` thay cho việc gọi `get` trong vòng lặp. Mỗi capability call đều được
tính vào hạn mức của project, và một record trigger có thể nhận 200 record cùng lúc.

SDK chuẩn hoá boolean `0/1` thành `true/false`. Giá trị lookup hoặc reference là
`RecordReference` gồm `id`, `name` và `objectSlug`. `name` là `""` trừ khi lệnh đọc mở
rộng lookup đó, ngoại trừ field `reference` vì tên được lưu kèm record; giá trị được mở
rộng có thêm `fields` của record liên kết (xem [Record liên kết](#record-liên-kết)). Giá
trị `new` và `old` của [record trigger](#record-trigger) luôn có tên lookup. Khi
ghi, developer có thể truyền record ID hoặc `RecordReference`; chỉ ID được gửi xuống
Record API.

Field `file` được đọc thành object `FileValue`: một `FileValue`, hoặc `null`, với file
field đơn và một mảng với file field nhiều giá trị. `url` chỉ có khi Cogover có URL tuyệt
đối đầy đủ cho file.

Lệnh ghi nhận `FileValue` đọc từ một record, nên có thể copy file sang record khác. Mọi
file được ghi phải là file đã tải lên cho một file field của Workspace này; nếu không, lệnh
ghi ném `ValidationError` (`details.r` 626) và không lưu gì.

Field `date` được đọc thành chuỗi `"yyyy-MM-dd"`, field `date_time` thành epoch
milliseconds. Khi ghi, Cogover nhận cùng các dạng đó và cả chuỗi ISO 8601, là dạng mà
một `Date` được chuyển thành: ghi vào field `date_time` được lưu đúng thời điểm đó, ghi
vào field `date` được lưu thành ngày theo UTC. Chuỗi khác cho các field này ném
`ValidationError` có `details.reason` là `"INVALID_FIELD_VALUE"`.

`create` và `update` yêu cầu object field không rỗng. `batchInsert` nhận 1–200
object field; `batchUpdate` nhận 1–200 phần tử `{ id, fields }`. Batch là
best-effort theo từng row, không phải `allOrNone`; luôn kiểm tra `success` hoặc
từng phần tử `results`. `referenceId` là index đầu vào bắt đầu từ 0, dạng chuỗi.
Xung đột unique key, kể cả hai row trong cùng batch có cùng giá trị unique, làm toàn bộ
batch bị từ chối thay vì một row: lời gọi ném `ValidationError` có `details.reason` là
`"UNIQUE_KEY_VIOLATION"` và không trả kết quả theo row. Thao tác ghi bị record trigger
before-change từ chối ném `ValidationError` có `details.reason` là `"TRIGGER_REJECTED"`,
còn thao tác ghi mà trigger không kiểm tra được ném `RetryableError` có `details.reason`
là `"TRIGGER_FAILED"` (xem [Record trigger](#validate-và-sửa-record)).
Với `batchInsert` và `batchUpdate`, trigger từ chối từng row chứ không từ chối cả lời
gọi: row bị từ chối có `r` là `70` và `success` là `false`, và khi Cogover nhận được,
`fieldErrors` ánh xạ từng field slug (`$record` với cả record) tới mã lỗi của trigger,
còn `messages` liệt kê các đoạn văn bản của trigger.

`deleteMany` yêu cầu 1–200 record ID không rỗng và trả hai mảng `deleted`,
`notDeleted`. Khi record trigger before-change từ chối một số record, các record còn
lại vẫn bị xoá, ID bị từ chối nằm trong `notDeleted`, và `recordErrors` ánh xạ từng ID
bị từ chối tới `{ reason: "TRIGGER_REJECTED", fieldErrors?, messages? }`. Khi trigger từ
chối mọi record, không có gì bị xoá và lời gọi ném `ValidationError` có
`details.reason` là `"TRIGGER_REJECTED"`. Record ID, object slug, option của `get`,
`getMany`, `list` và `aggregate`, và `matchBy` của `upsertByUniqueField` được validate
trước khi gửi; Cogover kiểm tra field slug có tồn tại hay không.

Giá trị field bị Cogover từ chối ném `ValidationError` có `details.fieldSlug` là field
đó: `details.reason` là `"REQUIRED_FIELD_MISSING"` khi field bắt buộc không có giá trị và
`"INVALID_FIELD_VALUE"` khi giá trị không hợp với kiểu của field. Field formula, auto
number, rollup summary và field có metadata `readOnly: true` không bao giờ ghi được, với
mọi danh tính: ghi vào field như vậy ném `ValidationError` có `details.reason` là
`"FIELD_NOT_WRITABLE"`.

`upsertByUniqueField(matchBy, fields)` yêu cầu `matchBy` là slug của một field đã
được cấu hình thành single-field unique key và field đó phải có giá trị trong
`fields`. Kết quả `{ id, created }` cho biết record vừa được tạo hay cập nhật.
Cogover yêu cầu đồng thời quyền tạo và cập nhật record cho upsert.

Xung đột unique key được trả thành `ValidationError`
với `details.reason === "UNIQUE_KEY_VIOLATION"`, `objectSlug` và `fieldSlug`.
Public error không trả lại giá trị business key bị trùng.

### Chọn field

`get`, `getMany` và `list` chỉ trả các field được nêu trong `fields`, nên một lệnh đọc
không tốn hơn những gì script dùng. `fields` là bắt buộc và là một trong hai dạng:

- danh sách field slug không rỗng, được trim và loại trùng theo đúng thứ tự ban đầu;
- chuỗi `"*"` đứng riêng: mọi field mà danh tính đang dùng được đọc. Với
  `data.asUser()` hoặc `data.asSystem()`, `"*"` chỉ gồm các field được identity policy
  của project cho phép: khi policy chỉ cho phép một số field, `"*"` là các field đó,
  không phải mọi field của Object.

Thiếu `fields`, hoặc truyền `null`, danh sách rỗng, `["*"]` hay giá trị không phải field
slug, sẽ ném `ValidationError` trước khi gửi request, với message:

```text
fields is required: pass field slugs or "*" (@cogover/sdk 0.13.0+)
```

Cogover cũng từ chối lệnh đọc như vậy với cùng message, nên một phiên bản project đã
publish bằng SDK cũ và đọc không có `fields` sẽ lỗi theo cùng cách: thêm `fields` vào các
lệnh đọc rồi publish lại.

Có thể liệt kê các slug hệ thống `id`, `created`, `updated` và `created_by`; giá trị của
chúng luôn được trả trong `id` và `system`, không nằm trong `fields`. `where` và `orderBy`
được dùng field không có trong `fields`. Với `data.asUser()` hoặc `data.asSystem()`, mọi
field trong `fields`, `where` và `orderBy` phải được identity policy của project cho phép,
nếu không lệnh đọc ném `PermissionDeniedError`; lệnh đọc qua `data.object()` không cần
policy và theo quyền của danh tính đang dùng. Slug không có trong Object ném
`ValidationError`.

Kiểu kết quả đi theo `fields`. Khi có khai báo workspace, `fields: ["code", "amount"]`
trả `CogoverRecord<Pick<Fields, "code" | "amount">>`, nên đọc một field không được yêu
cầu là lỗi compile, còn `"*"` trả mọi field đã khai báo:

```typescript
const order = await orders.records.get(orderId, { fields: ["code", "amount"] });
const amount = order?.fields.amount; // number | null | undefined
// order?.fields.status không compile được: `status` không được yêu cầu.
const full = await orders.records.get(orderId, { fields: "*" });
```

Kết quả của một capability call giới hạn 1.048.576 byte (xem
[Giới hạn của một lần thực thi](#giới-hạn-của-một-lần-thực-thi)). `"*"` trên Object có nhiều field
hoặc field dài có thể vượt giới hạn này, nhất là với `getMany` hoặc một trang `list` 200
record; khi đó lời gọi ném `ValidationError` có `details.limit`. Hãy nêu đúng các field
script cần, hoặc đọc ít record hơn mỗi lần.

### Record liên kết

Lệnh đọc không tra cứu record mà field lookup trỏ tới, trừ khi được yêu cầu:

- giá trị `lookup_normal` là `{ id, name: "", objectSlug }`, hoặc mảng các giá trị đó với
  lookup nhiều giá trị;
- giá trị `reference` giữ `name` vì record lưu sẵn tên;
- `system.createdBy` là `{ id, name: "" }`.

Dùng `expandLookups` khi script cần tên hoặc field của record liên kết:

```typescript
const page = await orders.records.list({
  fields: ["code", "customer", "owner"],
  expandLookups: { customer: ["credit_limit", "tier"], owner: "*" },
  limit: 50,
});
const customer = page.items[0]?.fields.customer;
// { id: "...", name: "ABC Company", objectSlug: "account",
//   fields: { credit_limit: 5000000, tier: "gold" } }
```

- `true` mở rộng mọi field lookup và reference trong các field được trả về, mỗi field lấy
  `"*"` của Object liên kết.
- Object chỉ mở rộng các field được nêu. Mỗi key phải là field lookup hoặc reference có
  trong `fields`; giá trị là `"*"` hoặc danh sách field slug không rỗng của Object liên
  kết.
- `false`, hoặc không truyền, không mở rộng gì.

Giá trị được mở rộng là `{ id, name, objectSlug, fields }`, trong đó `fields` chứa các
field đã chọn của record liên kết. Khi có khai báo workspace, `fields` của một
`RecordReference<"account">` có kiểu partial của các field thuộc `account`. Khi có
`expandLookups`, `system.createdBy.name` cũng được điền bằng field `name` của record nhân
sự đã tạo record, có thể là một mã được sinh tự động thay vì họ tên; để lấy tên hiển
thị, dùng
[`org.personnel.get`](#orgpersonnelgetid-options-và-orgpersonnelgetmanyids-options)
với `withDisplay: true`.

Record liên kết được đọc bằng cùng danh tính với lệnh đọc: người gọi, `data.asUser()`
hoặc `data.asSystem()`. Với `data.object()`, record liên kết theo quyền của danh tính
đang dùng. Với `data.asUser()` hoặc `data.asSystem()`, identity policy của project còn
phải cho phép đọc Object liên kết:

- Với `true` hoặc `"*"`, chỉ các field liên kết được policy cho phép mới được trả. Khi
  policy không cho đọc Object liên kết, giá trị trỏ tới Object đó không được mở rộng.
- Với danh sách field, mọi field được liệt kê phải được cho phép, nếu không lệnh đọc ném
  `PermissionDeniedError` có `details.objectSlug` là Object liên kết và, với field không
  được cho phép, `details.fieldSlug` là field đó; slug không có trong Object liên kết ném
  `ValidationError`.
- Record liên kết không đọc được, vì danh tính không được xem hoặc record đã bị xoá, không
  được mở rộng và không có `fields`.

Giá trị không được mở rộng là `{ id, name: "", objectSlug }` trong field lookup; trong
field `reference`, giá trị giữ tên mà record lưu sẵn.

Chỉ mở rộng một cấp: lookup bên trong `fields` của record liên kết là
`{ id, name: "", objectSlug }`. Mỗi lời gọi mở rộng tối đa 1.000 record liên kết khác
nhau; vượt quá sẽ ném `ValidationError` (`expandLookups can resolve at most 1000 linked
records per call`) và không đọc gì. Lệnh đọc vẫn chỉ là một capability call, nhưng
Cogover phải đọc thêm từng Object liên kết nên tốn thời gian: chỉ mở rộng lookup mà
script dùng tên hoặc field. Kết quả, kể cả record liên kết, phải nằm trong giới hạn
1.048.576 byte.

`expandLookups` sai cấu trúc ném `ValidationError` trước khi gửi request: object rỗng,
key không phải field slug hoặc không có trong `fields`, hay giá trị không phải `"*"` và
cũng không phải danh sách field slug không rỗng.

### Aggregate

`records.aggregate(options)` đếm, tính tổng, trung bình, giá trị nhỏ nhất và lớn nhất
trên các record khớp `where`, bằng một capability call và không đọc record:

```typescript
const totals = await orders.records.aggregate({
  where: orders.fields.status.eq("paid"),
  metrics: { orders: { count: "id" }, revenue: { sum: "amount" } },
});
// { values: { orders: 120, revenue: 530000000 } }

const byStatus = await orders.records.aggregate({
  groupBy: ["status"],
  metrics: { orders: { count: "id" }, revenue: { sum: "amount" } },
  limit: 100,
});
// { groups: [{ key: { status: "paid" }, values: { orders: 120, revenue: 530000000 } }],
//   truncated: false }
```

`metrics` đặt tên cho 1 đến 20 metric. Tên metric là một chữ cái, theo sau tối đa 63 chữ
cái, chữ số hoặc dấu gạch dưới; mỗi metric là đúng một trong các dạng:

| Metric | Field | Giá trị |
|---|---|---|
| `{ count: "id" }` | | số record khớp |
| `{ count: field }` | field số, ngày, lựa chọn, `boolean`, `lookup_normal`, text, `email`, `phone` và `auto_number`; không nhận `reference`, `file`, `url`, `formula` và `rollup_summary` | số record khớp có giá trị ở field |
| `{ countDistinct: field }` | các field mà `count` nhận | số giá trị khác nhau, xấp xỉ với tập lớn |
| `{ sum: field }` | `numeric`, `decimal`, `currency`, `percent` | tổng |
| `{ avg: field }` | các kiểu số ở trên | trung bình; `null` khi không record khớp nào có giá trị |
| `{ min: field }`, `{ max: field }` | các kiểu số ở trên, `date`, `date_time` | giá trị nhỏ nhất hoặc lớn nhất; `null` khi không record khớp nào có giá trị; epoch milliseconds với field ngày |

Số lượng và tổng là `0` khi không có record nào khớp.

`where` hoạt động như trong `list`. Không có `groupBy`, kết quả là `{ values }` với một
giá trị cho mỗi tên metric. Có `groupBy`, là danh sách 1 đến 3 field slug, kết quả là
`{ groups, truncated }`: mỗi tổ hợp giá trị là một phần tử `{ key, values }`, nhóm nhiều
record nhất đứng trước. `groupBy` nhận field có kiểu `single_choice`, `multi_choices`,
`radio_button`, `checkbox`, `boolean`, `lookup_normal`, `date`, `date_time`, `numeric`,
`decimal`, `currency` và `percent`; field khác, như field text hoặc `reference`, ném
`ValidationError`. `key` ánh xạ từng field `groupBy` tới giá trị: record ID với lookup,
option slug với choice, `true` hoặc `false`, số, hoặc epoch milliseconds với `date` và
`date_time`. Giá trị của key không bao giờ là `null`: record không có giá trị ở một field
`groupBy` không thuộc nhóm nào.

`limit`, chỉ dùng cùng `groupBy`, là số nhóm tối đa được trả: 1 đến 5.000, mặc định
1.000. `truncated` là `true` khi còn nhóm khác và chỉ `limit` nhóm đầu được trả.

Với `data.asUser()` hoặc `data.asSystem()`, mọi field trong `where`, `groupBy` và
`metrics`, trừ `"id"`, phải được identity policy của project cho phép, nếu không lời gọi
ném `PermissionDeniedError`. Chỉ các record mà danh tính đang dùng nhìn thấy mới được
tính.

Client của `data.asUser()` có giới hạn hẹp hơn:

- Không nhóm được. Kiểu của nó không nhận `groupBy`, và nếu vẫn truyền thì lời gọi ném
  `ValidationError` (`aggregate with groupBy is not supported for asUser(); use the
  caller or asSystem()`).
- Metric chỉ gồm `count` trên `"id"`, và `count`, `sum`, `avg`, `min`, `max` trên field số
  (`AsUserAggregateMetric`). Metric khác ném `ValidationError` (`metrics.<name>: asUser()
  without groupBy supports only count on id and count, sum, avg, min and max on number
  fields; use the caller or asSystem()`).

Các giới hạn này cũng áp dụng cho `data.object()` khi lần thực thi đọc dưới danh tính một
người dùng không phải người gọi HTTP: trong record trigger cho thay đổi do người dùng thực
hiện, trong lần chạy job có người dùng, hoặc trong Development Session local do
`cogover-dev run` khởi động. Nhóm ở đó ném `ValidationError` (`aggregate with groupBy is not
supported for the default identity of this invocation, which reads as a delegated user;
use asSystem()`). Hãy dùng `data.asSystem()` ở đó, hoặc danh tính người gọi trong HTTP
route, để nhóm và dùng các metric khác.

Option không hợp lệ ném `ValidationError` trước khi gửi request: không có metric hoặc
nhiều hơn 20, tên metric sai, metric không đúng một trong các dạng trên, `groupBy` rỗng
hoặc nhiều hơn 3 field, `limit` không có `groupBy`, hoặc `limit` ngoài khoảng 1 đến 5.000.

Aggregate được tính từ search index cập nhật theo các lệnh ghi record sau một khoảng
trễ ngắn, thường khoảng một giây, nên record vừa ghi có thể chưa được tính. Được dùng
`aggregate` trong record trigger before-change, nhưng lệnh ghi của người dùng phải chờ
trong lúc nó chạy: hạn chế số lời gọi, và đừng dựa vào nó để thấy các record đang được
ghi.

## Filter và sort

```typescript
type FilterOperator =
  | "=" | "!=" | ">" | ">=" | "<" | "<="
  | "like" | "not like" | "startsWith" | "endsWith"
  | "in" | "not in" | "is null" | "not null" | "between";

interface FilterCondition {
  readonly kind: "condition";
  readonly field: string;
  readonly operator: FilterOperator;
  readonly value?: unknown;
}

interface FilterGroup {
  readonly kind: "group";
  readonly operator: "and" | "or";
  readonly expressions: readonly FilterExpression[];
}

type FilterExpression = FilterCondition | FilterGroup;

interface SortExpression {
  readonly field: string;
  readonly direction: "asc" | "desc";
}

interface FieldReference<Value> {
  readonly slug: string;
  eq(value: NonNullable<Value>): FilterCondition;
  neq(value: NonNullable<Value>): FilterCondition;
  gt(value: NonNullable<Value>): FilterCondition;
  gte(value: NonNullable<Value>): FilterCondition;
  lt(value: NonNullable<Value>): FilterCondition;
  lte(value: NonNullable<Value>): FilterCondition;
  like(value: string): FilterCondition;
  notLike(value: string): FilterCondition;
  startsWith(value: string): FilterCondition;
  endsWith(value: string): FilterCondition;
  in(values: readonly (
    NonNullable<Value> extends readonly (infer Item)[] ? NonNullable<Item> : NonNullable<Value>
  )[]): FilterCondition;
  notIn(values: readonly (
    NonNullable<Value> extends readonly (infer Item)[] ? NonNullable<Item> : NonNullable<Value>
  )[]): FilterCondition;
  isNull(): FilterCondition;
  notNull(): FilterCondition;
  between(from: NonNullable<Value>, to: NonNullable<Value>): FilterCondition;
  asc(): SortExpression;
  desc(): SortExpression;
}
```

Mỗi `FieldReference<Value>` có `slug`, `eq`, `neq`, `gt`, `gte`, `lt`, `lte`,
`like`, `notLike`, `startsWith`, `endsWith`, `in`, `notIn`, `isNull`, `notNull`,
`between`, `asc` và `desc`. `FieldReferences<Fields>` cung cấp reference cho field
workspace và các field hệ thống `id`, `created`, `updated`, `created_by`.
`and(...expressions)` và `or(...expressions)` trả `FilterGroup`, yêu cầu ít nhất
một biểu thức. Với field dạng array, `in` và `notIn` nhận type của phần tử trong
array. Cogover xử lý metadata field và response transport.

## Danh tính thực hiện thao tác record

`data.object(slug)` kế thừa danh tính invocation. Invocation public đã xác thực dùng
quyền người gọi; invocation hệ thống giữ quyền hệ thống.

### `data.asUser(personnelId: string): AsUserDataApi<TSchema>`

Trả client immutable mới để đọc và ghi theo ID nhân sự được chỉ định (không phải account ID),
trong cùng workspace. `personnelId` được trim; giá trị không phải string hoặc rỗng
gây `ValidationError`. `object(slug)` trả `AsUserObjectClient<TFields>`, có
`records: AsUserRecordsApi<TFields>` gồm toàn bộ API đọc/ghi (kể cả `getMany` và
`aggregate`), batch và upsert, giữ nguyên kiểu tham số và kết quả của Record API mặc
định, ngoại trừ `aggregate` không nhóm được.

`get(id, options)` trả record hoặc `null`, `list(options)` trả `RecordPage`, cả hai được
thu hẹp theo `fields`. Chọn field, `expandLookups`, filter, sort và cursor hoạt động như
client mặc định. Đọc, kể cả record liên kết, áp dụng quyền của nhân sự được chọn và giới
hạn field của project đã duyệt. Truy vấn thành công nhưng không có record trả `null`; lỗi server được
ném ra, không bị coi là record không tồn tại hoặc trang rỗng.

```typescript
const delegatedOrders = data.asUser(personnelId).object("order");
const order = await delegatedOrders.records.get(recordId, { fields: ["description"] });
const page = await delegatedOrders.records.list({
  fields: ["description"],
  where: delegatedOrders.fields.description.eq("Pending review"),
  limit: 20,
});
```

### `data.asSystem(): DataApi<TSchema>`

Trả client immutable mới để truy cập record bằng hệ thống, kể cả trong invocation
public đã xác thực. Hỗ trợ toàn bộ Record API, gồm `getMany`, `aggregate` (có nhóm), batch
và upsert. Quyền hệ
thống không áp dụng quyền record của người gọi; vẫn áp dụng giới hạn project được
duyệt, validation field, ranh giới workspace và quota runtime. Không thay đổi người
khởi tạo invocation hoặc các client đã tạo.

```typescript
const orders = data.object("order");
await orders.records.update(order.id, { description: "Caller update" });
await data.asUser(personnelId).object("order").records.update(order.id, { description: "Delegated update" });
await data.asSystem().object("order").records.update(order.id, { description: "System update" });
```

Chọn danh tính cần quản trị viên cấp quyền theo phiên bản project, người gọi, nhân
sự đích, object, thao tác và field. Việc chọn client không tự cấp quyền. Thao tác
không được phép ném `PermissionDeniedError`; danh tính sai hoặc không resolve được
không fallback sang hệ thống hay người gọi. Nhân sự không có tài khoản người dùng đang
hoạt động trong workspace ném `PermissionDeniedError` có `details.reason` là
`"IDENTITY_NOT_RESOLVED"`. Lỗi server giữ `CogoverApiError.r` gốc.
Các method không nhận credential hay workspace override. Schema API không thay đổi.
Mỗi lần ghi độc lập; ba lời gọi minh hoạ trên không phải một transaction.

## Project state

State là JSON bền vững, có phạm vi theo workspace, project, namespace và key. State
không gắn với một version nên vẫn còn khi publish version project mới.

```typescript
interface StateEntry<T> {
  readonly value: T;
  readonly version: number;
  readonly expiresAt?: number;
  readonly createdAt: number;
  readonly updatedAt: number;
}

interface StateWriteOptions {
  readonly expectedVersion?: number;
  readonly ttlSeconds?: number;
}

interface StateDeleteOptions {
  readonly expectedVersion?: number;
}

interface StateNamespace {
  readonly name: string;
  get<T>(key: string): Promise<StateEntry<T> | null>;
  set<T>(key: string, value: T, options?: StateWriteOptions): Promise<StateEntry<T>>;
  delete(key: string, options?: StateDeleteOptions): Promise<boolean>;
}

interface ProjectState {
  namespace(name: string): StateNamespace;
}
```

```typescript
const progress = state.namespace("inventory-sync");
const current = await progress.get<{ cursor: string }>("cursor");

const saved = await progress.set("cursor", { cursor: "next-page" }, {
  expectedVersion: current?.version ?? 0,
  ttlSeconds: 3600,
});

await progress.delete("cursor", { expectedVersion: saved.version });
```

### `state.namespace(name): StateNamespace`

Tạo client immutable cho namespace. Namespace dài tối đa 128 ký tự; key dài tối
đa 255 ký tự. Cả hai phải bắt đầu bằng chữ hoặc số ASCII và chỉ chứa chữ, số,
`.`, `_`, `:`, `/`, `-`.

### `namespace.get<T>(key): Promise<StateEntry<T> | null>`

Trả `null` khi không có hoặc đã hết hạn. Entry gồm `value`, `version`, `createdAt`,
`updatedAt` và `expiresAt` tuỳ chọn; timestamp là Unix milliseconds.

### `namespace.set<T>(key, value, options?): Promise<StateEntry<T>>`

Ghi một giá trị JSON tối đa 32 KiB: 32.768 byte UTF-8 của dạng `JSON.stringify`,
trong đó dấu ngoặc kép, dấu gạch chéo ngược hoặc ký tự điều khiển được tính theo
chuỗi escape của nó. `ttlSeconds`
từ 1 giây đến 365 ngày; bỏ qua để state không tự hết hạn. Hai option phải là safe
integer. `expectedVersion` áp dụng
compare-and-set: `0` chỉ tạo khi chưa tồn tại, số dương chỉ ghi đúng version, bỏ qua
để upsert vô điều kiện. Xung đột ném `StateConflictError`; entry trả về chứa version mới.
Mỗi project giữ tối đa 100.000 entry chưa hết hạn: `set` tạo thêm entry mới khi đã đủ
sẽ ném `RateLimitError` và không ghi gì, còn cập nhật key đã có vẫn hoạt động bình
thường. Entry hết hạn được tự động xoá và không tính vào giới hạn.

Version đếm số lần ghi kể từ khi entry được tạo. Sau `delete` hoặc khi hết hạn, lần
`set` tiếp theo tạo entry mới có version bắt đầu lại từ 1, nên một version đã đọc trước
khi xoá có thể khớp với một entry mới không liên quan (vấn đề ABA). Khi điều này quan
trọng, hãy lưu thêm một token duy nhất của bạn trong value và so sánh cả token đó.

### `namespace.delete(key, options?): Promise<boolean>`

Xoá và trả `true` nếu entry tồn tại. Có thể dùng `expectedVersion` như khi `set`.
State hết hạn được xem như không tồn tại. State API không tạo transaction với Record
API; không dùng để lưu secret, file hoặc dữ liệu lớn.

## Distributed locks

Lock là lease phân tán theo workspace, project, namespace và key, dùng để ngăn các
execution đồng thời chạy cùng một đoạn xử lý. Cách an toàn mặc định là `withLock`:

```typescript
interface LockOptions {
  readonly namespace?: string;
  readonly waitMs?: number;
  readonly leaseMs?: number;
}

interface LockLease {
  readonly id: string;
  readonly key: string;
  readonly namespace: string;
  readonly fencingToken: number;
  readonly expiresAt: number;
  renew(leaseMs?: number): Promise<void>;
  release(): Promise<void>;
}

interface DistributedLocks {
  acquire(key: string, options?: LockOptions): Promise<LockLease | null>;
  withLock<T>(key: string, callback: (lease: LockLease) => T | Promise<T>): Promise<T>;
  withLock<T>(key: string, options: LockOptions,
    callback: (lease: LockLease) => T | Promise<T>): Promise<T>;
}
```

```typescript
await locks.withLock("INV-1", { namespace: "invoice", waitMs: 500 }, async lease => {
  await processInvoice("INV-1", lease.fencingToken);
  // Chỉ cần renew khi công việc có thể tiến gần thời điểm expiresAt.
  // await lease.renew(30_000);
});
```

### `locks.acquire(key, options?): Promise<LockLease | null>`

Trả lease hoặc `null` khi không lấy được trong `waitMs`. Namespace mặc định là
`default`; `waitMs` từ 0 đến 10.000 ms; `leaseMs` từ 5.000 đến 60.000 ms và mặc
định 30.000 ms. Mỗi invocation giữ tối đa 16 lock; lấy lock thứ 17 ném
`ValidationError`. Key dài tối đa 255 ký tự, namespace tối đa 128 và dùng cùng quy tắc
ký tự như tên state. Numeric option phải là safe integer.

Thời gian chờ được tính vào wall-clock của lần thực thi. Trong HTTP route, mặc định
có tổng cộng 8 giây (xem [Giới hạn của một lần thực thi](#giới-hạn-của-một-lần-thực-thi)),
`waitMs` gần bằng hoặc lớn hơn thời gian còn lại sẽ kết thúc toàn bộ lần thực thi với
response HTTP 422 chung thay vì trả `null`; hãy giữ `waitMs` nhỏ hơn nhiều so với thời
gian còn lại.

Lease có `id`, `key`, `namespace`, `fencingToken`, `expiresAt`, cùng
`renew(leaseMs?)` và `release()`. Cogover renew và release lease theo `id` trong phạm vi
project đã lấy lock: mọi lần thực thi của cùng project biết `id` đều có thể renew hoặc
release lease đó, còn project khác thì không. Hãy giữ `id` riêng tư và không trả nó cho
caller. Lease mất hoặc hết hạn ném `LockLostError`. `release()` lặp lại trên cùng object
lease là no-op sau lần thành công.

### `locks.withLock(key, callback)` / `locks.withLock(key, options, callback)`

Lấy lock, chạy callback rồi release lease. Nếu không lấy được lock, hàm ném
`LockUnavailableError`. Khi callback ném lỗi, lease được release và lỗi của callback
được ném lại; nếu việc release đó cũng lỗi thì lỗi release bị bỏ qua và lease hết hạn
sau `leaseMs`. Khi callback thành công nhưng release lỗi, ví dụ `LockLostError` vì lease
đã hết hạn trong lúc callback chạy, lỗi đó được ném thay cho kết quả của callback. Hàm
không tự renew; callback dài phải gọi `lease.renew()` trước khi `expiresAt`.

Lock chỉ bảo đảm một lease hợp lệ tại một thời điểm; timeout, pause hoặc lỗi mạng có
thể làm execution cũ tiếp tục sau khi lease hết hạn. Khi hệ thống đích hỗ trợ,
hãy lưu/kiểm tra `fencingToken` và từ chối token cũ. Lock không thay thế idempotency,
không tạo exactly-once và không gộp Record API với state thành một transaction.

## Push message

`push` gửi message tới web client của workspace: yêu cầu tải lại record, một toast,
hoặc một message chạy ngầm mà client tự xử lý. Đây là cùng cơ chế với action
"Push Message" của Workflow, nên trang record chuẩn phản ứng mà không cần code
client. Gửi là best-effort: lời gọi hoàn tất khi message đã được bàn giao cho
Cogover, không phải khi client nhận được.

```typescript
type PushRecipients = "viewers" | readonly string[];

interface PushOptions {
  readonly recipients?: PushRecipients;
  readonly exclude?: readonly string[];
}

type ToastPosition = "TOP_LEFT" | "TOP_CENTER" | "TOP_RIGHT"
  | "BOTTOM_LEFT" | "BOTTOM_CENTER" | "BOTTOM_RIGHT";
type ToastSize = "SMALL" | "MEDIUM" | "LARGE";

interface ToastLink {
  readonly label: string;
  readonly url: string;
}

interface ToastMessage<ObjectSlug extends string = string> {
  readonly title?: string;
  readonly content?: string;
  readonly links?: readonly ToastLink[];
  readonly position?: ToastPosition;
  readonly size?: ToastSize;
  readonly durationSeconds?: number;
  readonly object?: ObjectSlug;
  readonly recordIds?: readonly string[];
}

type BackgroundContentType = "text" | "template";

interface BackgroundMessage<ObjectSlug extends string = string> {
  readonly content: string;
  readonly contentType?: BackgroundContentType;
  readonly object?: ObjectSlug;
  readonly recordIds?: readonly string[];
}

interface PushApi<Schema extends object = EffectiveWorkspaceObjects> {
  refreshRecords(object: StringKeyOf<Schema>, recordIds: readonly string[],
    options?: PushOptions): Promise<void>;
  toast(message: ToastMessage<StringKeyOf<Schema>>, options?: PushOptions): Promise<void>;
  message(message: BackgroundMessage<StringKeyOf<Schema>>, options?: PushOptions): Promise<void>;
}
```

```typescript
// Trigger after-change: handler đã sửa record nên mọi người đang mở record phải tải
// lại, kể cả người vừa lưu và làm trigger chạy.
await data.object("order").records.batchUpdate(items);
await push.refreshRecords("order", items.map(item => item.id));
```

### Người nhận

Mọi method nhận cùng `options`. `recipients` mặc định là `"viewers"`: mọi người đang
mở một trong các record đích sẽ nhận message, vì vậy `object` và `recordIds` là bắt
buộc. Danh sách personnel ID gửi tới đúng những người đó dù họ đang ở đâu trong
workspace; khi đó `object` và `recordIds` là tuỳ chọn với `toast` và `message`, và nếu
có thì cho client biết message nói về record nào. `exclude` liệt kê personnel ID không
bao giờ nhận message; giá trị đặc biệt `"actor"` là người dùng có hành động khởi đầu
execution hiện tại (người gọi HTTP script, người lưu record làm trigger chạy).
Execution hệ thống không có actor nên `"actor"` không loại ai. Personnel chưa có tài
khoản người dùng được bỏ qua; personnel ID hoặc object slug không tồn tại ném
`NotFoundError` trước khi gửi bất kỳ message nào. `recordIds` nhận tối đa 200 record ID
khác nhau, còn `recipients` và `exclude` mỗi danh sách tối đa 200 phần tử, đếm trước khi
loại trùng; sau đó ID trùng được loại bỏ. Cogover không kiểm tra record ID có tồn tại hay
không: message về record không tồn tại sẽ không tới ai đang xem.

### `push.refreshRecords(object, recordIds, options?): Promise<void>`

Yêu cầu các client đang hiển thị những record này tải lại chúng. Trang record của
web app tự xử lý yêu cầu. `recordIds` nhận 1 đến 200 ID.

### `push.toast(message, options?): Promise<void>`

Hiển thị một thông báo ngắn. Cần ít nhất một trong `title` (tối đa 200 ký tự) và
`content` (tối đa 4.000 ký tự). `links` chứa tối đa 5 mục với `url` là URL tuyệt đối
`http` hoặc `https`. `position` mặc định `"TOP_RIGHT"`, `size` mặc định `"MEDIUM"` và
`durationSeconds` mặc định 5 (từ 1 đến 60). Khi có `object` và `recordIds`, client chỉ
hiển thị toast trong lúc một trong các record đó đang mở.

### `push.message(message, options?): Promise<void>`

Gửi một message mà client xử lý không kèm thông báo hiển thị, ví dụ một custom
component đang lắng nghe. `content` là bắt buộc (tối đa 16.384 ký tự); `contentType`
là `"text"` (mặc định) hoặc `"template"`.

### Quy tắc

- Mỗi lời gọi tốn một capability call bất kể số record hay người nhận; khi người nhận
  là `"viewers"`, mỗi record được gửi một message.
- Input được SDK kiểm tra và Cogover kiểm tra lại; input không hợp lệ ném
  `ValidationError` trước khi gửi bất kỳ message nào.
- `push` có trong script, route, trigger after-change và Development Session. Trigger
  before-change là chỉ đọc và nhận `PermissionDeniedError` với reason
  `TRIGGER_READ_ONLY`; Development Session chỉ đọc cũng từ chối.
- Khi deployment tắt push message, mọi lời gọi ném `CogoverApiError` với code
  `PUSH_DISABLED`; HTTP route không bắt lỗi này sẽ trả response HTTP 422 chung.
- Message đã gửi không thể thu hồi, và chạy lại một execution thất bại có thể gửi
  lại message.

## Notification

`notifications` lưu một notification vào danh sách thông báo (biểu tượng chuông) của
từng người nhận và gửi nó trong web app, qua web push, mobile push và một bản sao
email, theo các kênh thông báo (notification channel) của workspace. Khác với
[push message](#push-message), notification vẫn nằm trong danh sách sau khi đã được
gửi, nên phù hợp với việc một người cần xử lý sau, ví dụ yêu cầu phê duyệt. Việc gửi
diễn ra bất đồng bộ và là best-effort: lời gọi hoàn tất khi Cogover đã tiếp nhận
notification, không phải khi nó tới thiết bị hay hộp thư.

```typescript
type NotificationContentType = "text" | "html";
type NotificationDisplay = "SIMPLE" | "FULL";
type NotificationSender = "workspace" | "actor";
type NotificationLinkTarget = "SAME_TAB" | "NEW_TAB";

interface NotificationLink {
  readonly url: string;
  readonly openIn?: NotificationLinkTarget;
}

interface NotificationMessage {
  readonly to: readonly string[];
  readonly exclude?: readonly string[];
  readonly title: string;
  readonly content: string;
  readonly contentType?: NotificationContentType;
  readonly subtitle?: string;
  readonly display?: NotificationDisplay;
  readonly link?: NotificationLink;
  readonly sender?: NotificationSender;
  readonly channel?: string;
  readonly email?: boolean;
  readonly idempotencyKey?: string;
}

interface NotificationResult {
  readonly requestId: string;
  readonly notified: number;
  readonly skippedPersonnelIds: readonly string[];
  readonly duplicate: boolean;
}

interface NotificationsApi {
  send(message: NotificationMessage): Promise<NotificationResult>;
}
```

```typescript
const result = await notifications.send({
  to: approverIds,
  exclude: ["actor"],
  title: "Leave request waiting for your approval",
  content: "A leave request of 3 days was submitted and needs your decision.",
  link: { url: `/app/leave_request/${recordId}` },
  channel: approvalChannelId,
  idempotencyKey: `leave-approval:${recordId}`,
});
// result.notified: số tài khoản được gửi; result.skippedPersonnelIds: personnel chưa có tài khoản
```

### `notifications.send(message): Promise<NotificationResult>`

**Người nhận.** `to` liệt kê từ 1 đến 200 personnel ID; ID trùng được loại bỏ.
Notification được gửi tới tài khoản người dùng của từng personnel. Personnel chưa có
tài khoản người dùng được bỏ qua và trả về trong `skippedPersonnelIds`, còn
`notified` là số tài khoản được gửi sau khi đã loại trừ. `exclude` liệt kê personnel ID
không bao giờ nhận notification; giá trị đặc biệt `"actor"` là người dùng có hành động
khởi đầu execution hiện tại (người gọi HTTP route, người lưu record làm trigger chạy,
người có lời gọi đã enqueue lần chạy job). Execution không có người dùng thì không có
actor, nên `"actor"` không loại ai. Personnel ID trong `to` không tồn tại ném
`NotFoundError` với `resource` là `"personnel"` trước khi gửi bất cứ gì. Khi mọi người
nhận đều bị loại trừ hoặc bỏ qua, không có gì được gửi và `notified` là `0`.

**Nội dung và cách hiển thị.**

- `title` (bắt buộc, tối đa 200 ký tự) là tiêu đề của notification và là subject của
  bản sao email.
- `content` (bắt buộc, tối đa 16.384 ký tự) là nội dung. Với `contentType: "text"`
  (mặc định), đây là văn bản thuần. Với `"html"`, nội dung được rút gọn về định dạng
  cơ bản trước khi lưu — đoạn văn, tiêu đề, danh sách, bảng, liên kết và nhấn mạnh;
  script, style và hình ảnh bị loại bỏ — và vẫn phải còn chữ hiển thị được, nếu không
  sẽ ném `ValidationError`.
- `subtitle` (tối đa 200 ký tự) chỉ hiển thị ở chế độ `"FULL"`. `display` mặc định là
  `"FULL"` khi có subtitle và `"SIMPLE"` khi không có; subtitle đi kèm
  `display: "SIMPLE"` ném `ValidationError`.
- `link` là trang được mở khi người nhận bấm vào notification. `url` là một path của
  web app Cogover bắt đầu bằng `/`, hoặc một URL tuyệt đối `http` hay `https`, tối đa
  2.048 ký tự. `openIn` là `"SAME_TAB"` hoặc `"NEW_TAB"`; mặc định `"SAME_TAB"` với
  path và `"NEW_TAB"` với URL tuyệt đối.
- `sender` là `"workspace"` (mặc định) hoặc `"actor"`, hiển thị tên và ảnh đại diện
  của người dùng có hành động khởi đầu execution. `"actor"` trong execution không có
  người dùng ném `ValidationError`.

**Kênh thông báo và bản sao email.** `channel` là record ID của một notification
channel của workspace. Kênh quyết định hình thức gửi nào được bật — trong web app,
web push, mobile push và email — và mỗi người dùng có thể ghi đè lựa chọn đó trong
cài đặt thông báo của riêng mình. Không có `channel` thì mọi hình thức gửi đều được
bật. Kênh không tồn tại ném `NotFoundError` với `resource` là `"notificationChannel"`;
workspace chưa thiết lập notification ném `NotFoundError` với `resource` là
`"object"` và `resourceId` là `"notification_channel"`.

`email: false` bỏ bản sao email kể cả khi kênh bật email. Bản sao dùng `title` làm
subject và `content` làm nội dung, được gửi từ một địa chỉ thông báo của Cogover chứ
không phải từ hộp thư của workspace, và được tính vào hạn mức email thông báo hằng
ngày theo gói của workspace. Để gửi email từ hộp thư của workspace, dùng
[`email.send`](#email).

**Idempotency.** `idempotencyKey` bắt đầu bằng chữ cái hoặc chữ số và chứa tối đa 128
chữ cái, chữ số, `.`, `_`, `:` hoặc `-`. Lời gọi có key mà project đã dùng cho một
notification trong 7 ngày gần nhất sẽ không gửi gì và trả về kết quả của lời gọi đầu
tiên với `duplicate: true`. Lời gọi thực hiện trong lúc lời gọi đầu tiên cùng key vẫn
đang gửi ném `CogoverApiError` với `code: "DUPLICATE_IN_PROGRESS"`; hãy thử lại sau
giây lát. Lời gọi thất bại không giữ key, nên có thể thử lại. Key thuộc về project và
tách biệt với key của `email.send`. Trong trigger after-change hoặc job, vốn có thể
chạy nhiều hơn một lần, hãy tạo key từ `trigger.changeId` và `record.id`, hoặc từ
`job.id` hay một key nghiệp vụ. Cogover không so sánh nội dung: lời gọi dùng lại key với
người nhận hoặc nội dung khác vẫn trả về kết quả đầu tiên và không gửi gì.

### Quy tắc

- `notifications` có trong script, route, trigger after-change, background job, lời
  gọi inbound webhook và Development Session có quyền ghi. Trigger before-change là
  chỉ đọc và nhận `PermissionDeniedError` có `details.reason` là
  `"TRIGGER_READ_ONLY"`; preview chỉ đọc và Development Session chỉ đọc cũng từ chối.
- Notification không cần grant trong identity policy: project được gửi notification
  tới mọi personnel của workspace.
- Mặc định mỗi project được gửi tới tối đa 5.000 người nhận mỗi giờ. Lời gọi làm vượt
  hạn mức này ném `RateLimitError` và không gửi gì.
- Input được SDK kiểm tra và Cogover kiểm tra lại; input không hợp lệ ném
  `ValidationError` trước khi gửi bất cứ gì. Mỗi lời gọi tính một capability call.
- Khi deployment tắt notification, mọi lời gọi ném `CogoverApiError` với code
  `NOTIFICATIONS_DISABLED`.
- Notification đã gửi không thể thu hồi. Chạy lại một execution thất bại có thể gửi
  lại notification nếu lời gọi không dùng `idempotencyKey`.

## Email

`email` gửi email từ hộp thư của workspace: một hộp thư dùng chung của workspace, hoặc
hộp thư cá nhân mặc định của người dùng có hành động khởi đầu execution. Identity
policy đã duyệt của Project quyết định project được dùng những hộp thư nào. Khi có
`record`, email còn được ghi nhận là một hoạt động email trên timeline của record đó,
giống email gửi từ trang record. Việc gửi diễn ra bất đồng bộ: lời gọi hoàn tất khi
Cogover đã tiếp nhận email để gửi, và lỗi gửi xảy ra sau đó không được báo lại cho
script.

```typescript
type EmailSender = { readonly mailbox: string } | "actor";

type EmailRecipient =
  | string
  | { readonly email: string; readonly name?: string }
  | { readonly personnelId: string };

interface EmailRecordLink<ObjectSlug extends string = string> {
  readonly object: ObjectSlug;
  readonly recordId: string;
}

interface EmailAttachment<ObjectSlug extends string = string> {
  readonly object: ObjectSlug;
  readonly recordId: string;
  readonly field: string;
}

type EmailMessage<ObjectSlug extends string = string> = {
  readonly from: EmailSender;
  readonly to?: readonly EmailRecipient[];
  readonly cc?: readonly EmailRecipient[];
  readonly bcc?: readonly EmailRecipient[];
  readonly subject: string;
  readonly record?: EmailRecordLink<ObjectSlug>;
  readonly recordEmailFields?: readonly string[];
  readonly attachments?: readonly EmailAttachment<ObjectSlug>[];
  readonly appendSignature?: boolean;
  readonly idempotencyKey?: string;
} & (
  | { readonly html: string; readonly text?: never }
  | { readonly text: string; readonly html?: never }
);

type EmailDelivery = "activity" | "direct";

interface EmailSendResult {
  readonly requestId: string;
  readonly delivery: EmailDelivery;
  readonly recipients: number;
  readonly duplicate: boolean;
}

type EmailSenderKind = "workspace" | "actor";

interface EmailSenderInfo {
  readonly id: string;
  readonly kind: EmailSenderKind;
  readonly email: string;
  readonly displayName: string;
}

interface EmailApi<Schema extends object = EffectiveWorkspaceObjects> {
  send(message: EmailMessage<StringKeyOf<Schema>>): Promise<EmailSendResult>;
  senders(): Promise<readonly EmailSenderInfo[]>;
}
```

```typescript
const result = await email.send({
  from: { mailbox: "EMWXXXXXXXXXXXX" },
  bcc: ["sales-archive@example.com"],
  subject: `Quote ${quote.fields.code}`,
  html: "<p>Dear customer,</p><p>Please find our quote attached.</p>",
  record: { object: "quote", recordId: quote.id },
  recordEmailFields: ["contact_email"],
  attachments: [{ object: "quote", recordId: quote.id, field: "quote_pdf" }],
  idempotencyKey: `quote-email:${quote.id}`,
});
// result.delivery === "activity": email xuất hiện trên timeline của báo giá.
```

### `email.send(message): Promise<EmailSendResult>`

**Người gửi.** `from: { mailbox: id }` gửi từ một hộp thư dùng chung của workspace;
`from: "actor"` gửi từ hộp thư cá nhân mặc định của người dùng có hành động khởi đầu
execution. Người gửi phải được phép trong mục `email` của identity policy đã duyệt
của Project: `workspaceMailboxIds` liệt kê các hộp thư dùng chung và
`allowActorMailbox` cho phép `"actor"`. Giống phần còn lại của policy, mục này chỉ áp
dụng cho các caller được chọn trong `callerPersonnelIds`, và cho execution không có
người dùng chỉ khi policy đặt `allowInternalSystem: true`. Project có policy không có
mục `email` thì không gửi được email. Người gửi không được phép ném
`PermissionDeniedError` có `details.reason` là `"EMAIL_SENDER_NOT_GRANTED"`; bước kiểm
tra này diễn ra trước mọi bước tra cứu khác. Hộp thư không tồn tại hoặc đã bị vô hiệu
hoá, và actor không có hộp thư cá nhân đang hoạt động, ném `NotFoundError` với
`resource` là `"mailbox"`. `"actor"` trong execution không có người dùng ném
`ValidationError`.

**Người nhận.**

- `to`, `cc` và `bcc` nhận một chuỗi địa chỉ, `{ email, name? }` hoặc
  `{ personnelId }`. Personnel được đổi thành email công việc của họ, hoặc email của
  tài khoản người dùng khi không có email công việc; personnel không có cả hai ném
  `ValidationError`, và personnel không tồn tại ném `NotFoundError` với `resource` là
  `"personnel"`.
- Địa chỉ trùng được loại bỏ trong từng danh sách, không phân biệt hoa thường. Ba danh
  sách cộng lại nhận tối đa 50 người nhận. `name` là một dòng, tối đa 200 ký tự.
- `to` phải có ít nhất một người nhận, trừ khi có `recordEmailFields`.

**Nội dung.** `subject` là bắt buộc: một dòng, tối đa 255 ký tự. Cung cấp đúng một
trong `html` và `text`; nội dung tối đa 192 KB (196.608 byte) theo UTF-8, đo trên dạng
đã mã hoá JSON: mỗi dấu ngoặc kép, dấu gạch chéo ngược hoặc ký tự điều khiển như xuống
dòng được tính theo chuỗi escape của nó (`\"` là 2 byte, `\n` là 2 byte, `\u0001` là 6
byte). Nội dung dài hơn ném `ValidationError` trước khi gọi.

**Record.** `record: { object, recordId }` ghi nhận email là một hoạt động email trên
timeline của record đó: Cogover theo dõi lượt mở và lượt bấm liên kết, gom các thư
trả lời vào cùng luồng, và `result.delivery` là `"activity"`. Record phải đọc được
bằng danh tính mặc định của execution: record không tồn tại ném `NotFoundError` với
`resource` là `"record"`, còn record mà danh tính đó không có quyền đọc ném
`PermissionDeniedError`. Không có `record` thì email chỉ được gửi từ hộp thư và
`delivery` là `"direct"`. Các tuỳ chọn sau cần `record`; thiếu `record` chúng ném
`ValidationError`:

- `recordEmailFields` liệt kê tối đa 20 field email của record đó, địa chỉ trong các
  field này được thêm vào `to`. Field không phải field email ném `ValidationError`.
- `attachments` đính kèm mọi file lưu trong file field `field` của từng record được
  liệt kê: tối đa 10 file và tổng cộng 20 MB. Các record phải đọc được bằng danh tính
  mặc định; field không phải file field ném `ValidationError`.
- `appendSignature: true` thêm chữ ký email mặc định của người gửi. Tuỳ chọn này cần
  hộp thư cá nhân, tức `from: "actor"`; nếu không sẽ ném `ValidationError`.

**Kết quả.** `requestId` định danh lần gửi. `recipients` đếm các địa chỉ trong `to`,
`cc` và `bcc` sau khi loại trùng; địa chỉ của `recordEmailFields` được xác định sau
nên không được đếm. `duplicate` là `true` khi một lời gọi trước đó cùng
`idempotencyKey` đã gửi email.

**Idempotency.** `idempotencyKey` theo cùng quy tắc với
[notification](#notification): lời gọi lặp lại cùng key trong 7 ngày trả về kết quả
đầu tiên với `duplicate: true` thay vì gửi lại, và lời gọi lặp lại trong lúc lời gọi
đầu tiên vẫn đang gửi ném `CogoverApiError` với `code: "DUPLICATE_IN_PROGRESS"`. Key
của email tách biệt với key của notification. Giống notification, nội dung không được
so sánh: dùng lại key cho một email khác vẫn trả về kết quả đầu tiên và không gửi gì.

### `email.senders(): Promise<readonly EmailSenderInfo[]>`

Trả về các hộp thư đang hoạt động mà execution này được dùng để gửi: một mục
`kind: "workspace"` cho mỗi hộp thư dùng chung đang hoạt động được policy áp dụng liệt
kê trong `workspaceMailboxIds`, dùng dưới dạng `{ mailbox: id }`, và, khi policy đặt
`allowActorMailbox` và actor có hộp thư cá nhân đang hoạt động, tối đa một mục
`kind: "actor"` mô tả hộp thư mà `from: "actor"` sử dụng. Danh sách rỗng khi policy
không cấp người gửi nào cho execution này. Dùng method này để hiển thị các người gửi
khả dụng hoặc chọn người gửi theo địa chỉ `email` thay vì hard-code ID. Method không
gửi gì, nên cũng dùng được trong preview chỉ đọc và Development Session chỉ đọc.

### Quy tắc

- `email` có trong script, route, trigger after-change, background job, lời gọi
  inbound webhook và Development Session. Trigger before-change nhận
  `PermissionDeniedError` có `details.reason` là `"TRIGGER_READ_ONLY"` với cả hai
  method; preview chỉ đọc và Development Session chỉ đọc từ chối `email.send`.
- Mặc định mỗi project được gửi tối đa 500 email mỗi giờ; vượt quá sẽ ném
  `RateLimitError` và không gửi gì. Một lời gọi là một email, bất kể có bao nhiêu
  người nhận.
- Input được SDK kiểm tra và Cogover kiểm tra lại; input không hợp lệ ném
  `ValidationError` trước khi gửi bất cứ gì. Mỗi lời gọi tính một capability call.
- Khi deployment tắt email, mọi lời gọi ném `CogoverApiError` với code
  `EMAIL_DISABLED`.
- Email đã gửi không thể thu hồi. Chạy lại một execution thất bại có thể gửi lại email
  nếu lời gọi không dùng `idempotencyKey`.

## Cơ cấu tổ chức

`org` đọc phòng ban, vị trí và nhân sự của workspace: ai thuộc phòng ban nào, vị trí
nào áp dụng ở đâu và ai quản lý ai. Mọi method đều chỉ đọc. Câu trả lời về cấu trúc
được lấy từ bản sao cơ cấu tổ chức đã cache nên rất nhanh; thay đổi thực hiện trong
Cogover sẽ có hiệu lực sau vài giây. Thêm `withDisplay: true` để nhận thêm tên phòng
ban, vị trí theo ngôn ngữ và, với nhân sự, tên hiển thị, email, avatar và mã nhân sự.
Các field khác của nhân sự như số điện thoại hay custom field được đọc bằng
`data.object("personnel")`, nơi quyền record được áp dụng.

```typescript
interface OrgApi {
  readonly personnel: OrgPersonnelApi;
  readonly departments: OrgDepartmentsApi;
  readonly positions: OrgPositionsApi;
  me(options?: OrgReadOptions): Promise<OrgPersonnel | null>;
  isInDepartment(personnelId: string, departmentId: string,
    options?: OrgIsInDepartmentOptions): Promise<boolean>;
  isManagerOf(managerId: string, personnelId: string,
    options?: OrgIsManagerOfOptions): Promise<boolean>;
}

interface OrgPersonnelApi {
  get(id: string, options?: OrgReadOptions): Promise<OrgPersonnel | null>;
  getMany(ids: readonly string[], options?: OrgReadOptions):
    Promise<OrgGetManyResult<OrgPersonnel>>;
  managerChain(id: string, options?: OrgPersonnelChainOptions):
    Promise<readonly OrgManagerChain[]>;
}

interface OrgDepartmentsApi {
  get(id: string, options?: OrgReadOptions): Promise<OrgDepartment | null>;
  tree(options?: OrgTreeOptions): Promise<readonly OrgDepartmentNode[]>;
  ancestors(id: string, options?: OrgReadOptions): Promise<readonly OrgDepartment[]>;
  members(id: string, options?: OrgDepartmentMembersOptions): Promise<OrgPage<OrgMember>>;
  managers(id: string, options?: OrgManagerOptions): Promise<readonly OrgManagerTier[]>;
  managerChain(id: string, options?: OrgManagerOptions): Promise<OrgManagerChain>;
}

interface OrgPositionsApi {
  list(options?: OrgReadOptions): Promise<readonly OrgPosition[]>;
  get(id: string, options?: OrgReadOptions): Promise<OrgPosition | null>;
  members(id: string, options?: OrgPositionMembersOptions): Promise<OrgPage<OrgMember>>;
}
```

Mọi method trả dữ liệu đều có overload thứ hai: khi `options.withDisplay` là literal
`true`, kiểu kết quả là biến thể `<true>` của các kiểu bên dưới và các field hiển thị
luôn có mặt. Khi không có option này, các field hiển thị không tồn tại trên kiểu.

```typescript
interface OrgReadOptions {
  readonly withDisplay?: boolean;
  readonly language?: string;       // ví dụ "vi-VN"; mặc định là ngôn ngữ của invocation
}

interface OrgPageOptions extends OrgReadOptions {
  readonly includeSubDepartments?: boolean;
  readonly accountOnly?: boolean;
  readonly limit?: number;          // mặc định 500, tối đa 2000; 200 khi có withDisplay
  readonly cursor?: string;
}
interface OrgDepartmentMembersOptions extends OrgPageOptions { readonly positionId?: string; }
interface OrgPositionMembersOptions extends OrgPageOptions { readonly departmentId?: string; }
interface OrgManagerOptions extends OrgReadOptions { readonly accountOnly?: boolean; }
interface OrgPersonnelChainOptions extends OrgManagerOptions { readonly departmentId?: string; }
interface OrgTreeOptions extends OrgReadOptions {
  readonly rootId?: string;
  readonly depth?: number;          // 1 đến 100; mặc định lấy mọi cấp
}
interface OrgIsInDepartmentOptions { readonly includeSubDepartments?: boolean; }
interface OrgIsManagerOfOptions {
  readonly departmentId?: string;
  readonly directOnly?: boolean;
}

interface OrgPersonnelDisplay {
  readonly name: string;
  readonly email: string | null;
  readonly avatar: string | null;   // URL công khai
  readonly code: string | null;
}
interface OrgNameDisplay { readonly name: string; }

type OrgMembership<D extends boolean = false> = {
  readonly personnelId: string;
  readonly departmentId: string;
  readonly positionId: string | null;
  readonly level: number;           // 0 nhân viên, 1 cấp quản lý cao nhất, 2 cao nhì, ...
  readonly primary: boolean;
} & (D extends true
  ? { readonly departmentName: string | null; readonly positionName: string | null }
  : {});

type OrgPersonnel<D extends boolean = false> = {
  readonly id: string;
  readonly accountId: string | null;          // null: chưa có tài khoản workspace
  readonly memberships: readonly OrgMembership<D>[];
} & (D extends true ? { readonly display: OrgPersonnelDisplay | null } : {});

type OrgMember<D extends boolean = false> = OrgMembership<D> & {
  readonly accountId: string | null;
} & (D extends true ? { readonly display: OrgPersonnelDisplay | null } : {});

type OrgDepartment<D extends boolean = false> = {
  readonly id: string;
  readonly parentId: string | null;
  readonly level: number;                     // 1 với phòng ban gốc
  readonly childIds: readonly string[];
  readonly positionIds: readonly string[];
} & (D extends true ? { readonly display: OrgNameDisplay | null } : {});

type OrgDepartmentNode<D extends boolean = false> = OrgDepartment<D> & {
  readonly children: readonly OrgDepartmentNode<D>[];
};

type OrgPosition<D extends boolean = false> = {
  readonly id: string;
  readonly departmentOnly: boolean;
  readonly departmentIds: readonly string[];
  readonly excludedDepartmentIds: readonly string[];
} & (D extends true ? { readonly display: OrgNameDisplay | null } : {});

type OrgManagerTier<D extends boolean = false> = {
  readonly departmentId: string;
  readonly level: number;
  readonly distance: number;                  // 0 phòng xuất phát, 1 phòng cha, ...
  readonly personnelIds: readonly string[];
} & (D extends true ? {
  readonly departmentName: string | null;
  readonly personnel: readonly { readonly id: string; readonly display: OrgPersonnelDisplay | null }[];
} : {});

interface OrgManagerChain<D extends boolean = false> {
  readonly fromDepartmentId: string;
  readonly personnelLevel: number;
  readonly tiers: readonly OrgManagerTier<D>[];
  readonly vacantDepartmentIds: readonly string[];
  readonly truncated: boolean;
}

interface OrgPage<T> {
  readonly items: readonly T[];
  readonly total: number;
  readonly nextCursor?: string;
}

interface OrgGetManyResult<T> {
  readonly items: readonly T[];
  readonly missingIds: readonly string[];
}
```

```typescript
export default defineScript(async ({ org, input }) => {
  const order = input as { ownerId: string; departmentId: string };
  // Chỉ cần cấu trúc: trả lời mà không đọc record.
  const [chain] = await org.personnel.managerChain(order.ownerId, {
    departmentId: order.departmentId,
    accountOnly: true,
  });
  const approverIds = chain?.tiers[0]?.personnelIds ?? [];

  // Cần tên để hiển thị: thêm tối đa một lần đọc cho mỗi loại dữ liệu.
  const me = await org.me({ withDisplay: true });
  return {
    approverIds,
    greeting: me?.display?.name,
    departments: me?.memberships.map(m => m.departmentName) ?? [],
  };
});
```

### Dữ liệu hiển thị

- `withDisplay` thêm `display` vào nhân sự, phòng ban và vị trí, và thêm
  `departmentName`/`positionName` vào membership. Giá trị là `null` khi không đọc
  được record tương ứng, ví dụ record vừa bị xoá.
- `language` chọn bản dịch tên phòng ban và vị trí, ví dụ `"vi-VN"` hoặc `"en-US"`;
  tag không có vùng (`"vi"`) khớp với bản dịch đầu tiên của ngôn ngữ đó. Mặc định là
  ngôn ngữ trong membership của user thực hiện invocation, sau đó đến ngôn ngữ của
  user, rồi của workspace; nếu không có bản dịch phù hợp thì dùng tên đã lưu.
- `name` của nhân sự là họ tên đầy đủ mà workspace hiển thị; `email` là email tài
  khoản, nếu không có thì là email công việc; `avatar` là URL ảnh công khai.
- Dữ liệu hiển thị chỉ gồm các field trên và mọi thành viên workspace đều xem được,
  giống như trong ô chọn người dùng. Mỗi lần gọi tốn tối đa một lần đọc cho mỗi loại
  dữ liệu và mỗi 200 ID; các giá trị vừa đọc được cache.

### `org.me(options?)`

Trả nhân sự của user thực hiện invocation, hoặc `null` với invocation `system` hay
`inbound`. Method này tương đương `org.personnel.get` với
`invocation.user.membership.personnelId`.

### `org.personnel.get(id, options?)` và `org.personnel.getMany(ids, options?)`

`get` trả một nhân sự đang hoạt động kèm mọi membership phòng ban, phòng ban chính
đứng đầu, hoặc `null` khi ID không phải nhân sự đang hoạt động của workspace.
`getMany` đọc tối đa 200 ID trong một lời gọi: ID trùng được gộp, `items` giữ thứ tự
request và ID không tồn tại được liệt kê trong `missingIds`. Nhân sự chưa có tài
khoản workspace có `accountId: null`; người đã rời workspace không được trả về.

### `org.departments.get(id, options?)`, `tree(options?)` và `ancestors(id, options?)`

- `get` trả một phòng ban đang hoạt động hoặc `null`. `childIds` theo thứ tự hiển thị;
  `positionIds` là các vị trí áp dụng cho phòng ban.
- `tree` trả các phòng ban gốc (hoặc chỉ `rootId`) kèm phòng ban con. `depth: 1` chỉ
  trả phòng gốc; dưới độ sâu yêu cầu, `children` rỗng nhưng `childIds` vẫn liệt kê
  phòng con. Cây có hơn 5000 phòng ban sẽ ném `ValidationError`; hãy thu hẹp bằng
  `rootId` hoặc `depth`.
- `ancestors` trả phòng cha trước, phòng gốc sau cùng.
- Phòng ban có phòng cha đã ngừng hoạt động hoặc đã xoá được trả như phòng gốc
  (`parentId: null`).

### `org.departments.members(id, options?)` và `org.positions.members(id, options?)`

Trả một trang membership: quản lý trước theo cấp, sau đó đến nhân viên. Nhân sự thuộc
nhiều phòng ban trong phạm vi được liệt kê một lần cho mỗi phòng ban.
`includeSubDepartments` thêm mọi phòng con theo thứ tự cây, `positionId` chỉ giữ
người giữ vị trí đó, `departmentId` giới hạn người giữ vị trí trong một phòng ban, và
`accountOnly` chỉ giữ nhân sự có tài khoản workspace. Truyền `nextCursor` làm
`cursor` để đọc trang tiếp; `total` đếm mọi trang. Kích thước trang mặc định 500 và
tối đa 2000, hoặc tối đa 200 khi có `withDisplay`.

### `org.positions.list(options?)` và `org.positions.get(id, options?)`

Trả các vị trí đang hoạt động, vị trí tạo trước đứng trước. Vị trí chỉ áp dụng cho
phòng ban riêng (`departmentOnly: true`) áp dụng cho `departmentIds`; vị trí còn lại
áp dụng cho mọi phòng ban trừ `excludedDepartmentIds`.

### Quản lý và chuỗi quản lý

`level` của membership đánh dấu quản lý: `0` là nhân viên, `1` là cấp quản lý cao
nhất của phòng ban, `2` là cấp cao nhì, và cứ thế tiếp. Nhiều người có thể cùng cấp.

- `org.departments.managers(id, options?)` trả quản lý của riêng phòng ban đó, mỗi
  cấp một tier, cấp `1` đứng đầu.
- `org.departments.managerChain(id, options?)` trả các quản lý phía trên một nhân
  viên của phòng ban, gần nhất trước, đến tận phòng ban gốc.
- `org.personnel.managerChain(id, options?)` trả một chuỗi cho mỗi phòng ban của nhân
  sự, phòng ban chính đứng đầu; `departmentId` chỉ giữ chuỗi bắt đầu từ phòng ban đó.
  Kết quả rỗng với nhân sự không tồn tại.

Chuỗi được tạo theo các quy tắc:

1. Trong phòng ban xuất phát, quản lý của nhân sự là những người có số cấp nhỏ hơn cấp
   của chính nhân sự đó (mọi quản lý nếu là nhân viên), gần nhất trước: cấp `3`, rồi
   `2`, rồi `1`. Trưởng phòng không có quản lý trong phòng của mình.
2. Sau đó mỗi phòng cha đến tận phòng gốc thêm mọi quản lý của mình, số cấp lớn nhất
   trước. Mọi quản lý của phòng cha đều đứng trên mọi quản lý của các phòng con.
3. Mỗi nhân sự chỉ xuất hiện một lần, ở tier gần nhất, và nhân sự xuất phát không bao
   giờ được liệt kê.
4. `accountOnly: true` bỏ qua nhân sự chưa có tài khoản workspace, ví dụ khi chuỗi
   dùng để chọn người duyệt.
5. `vacantDepartmentIds` liệt kê các phòng ban đi qua mà không có quản lý hợp lệ nào;
   chuỗi tiếp tục với phòng cha của chúng. Phòng của chính trưởng phòng không bị coi
   là trống.
6. `truncated` là `true` khi một phòng cha đã ngừng hoạt động, nên chuỗi dừng trước
   phòng gốc thực sự.

Ví dụ, với ban lãnh đạo công ty (CEO cấp `1`, phó CEO cấp `2`), khối Kỹ thuật bên
dưới (giám đốc cấp `1`) và phòng Kiểm thử thuộc khối Kỹ thuật (trưởng phòng `1`, phó
phòng `2`, trưởng nhóm `3`), chuỗi của một tester là: trưởng nhóm, phó phòng, trưởng
phòng, giám đốc khối, phó CEO, CEO. Chuỗi của phó phòng Kiểm thử là: trưởng phòng,
giám đốc khối, phó CEO, CEO.

### `org.isInDepartment(personnelId, departmentId, options?)` và `org.isManagerOf(managerId, personnelId, options?)`

`isInDepartment` cho biết nhân sự có thuộc phòng ban, hoặc một phòng con của nó khi
có `includeSubDepartments`. `isManagerOf` cho biết `managerId` có xuất hiện trong một
chuỗi quản lý của `personnelId` hay không; `departmentId` chỉ xét chuỗi bắt đầu từ
phòng ban đó và `directOnly` chỉ xét tier gần nhất. Cả hai trả `false` với ID không
tồn tại.

### Quy tắc

- `org` dùng được trong script, route, record trigger ở cả hai thời điểm, background
  job và Development Session.
- `org` đi theo danh tính mặc định của lần thực thi: lần thực thi có user hoặc danh
  tính system đều đọc được. Lần thực thi không có user (background job, inbound
  webhook, hoặc record trigger do một thao tác ghi của hệ thống gây ra) chỉ đọc được
  khi identity policy đã duyệt của project đặt `allowInternalSystem: true`; nếu không,
  mọi lời gọi trừ `org.me()` ném `PermissionDeniedError` có `details.reason` là
  `"IDENTITY_NOT_GRANTED"`. Khi đó `org.me()` trả `null` mà không thực hiện capability
  call, vì lần thực thi không có user.
- Mọi lời gọi trong cùng một lần thực thi đọc cùng một phiên bản cơ cấu tổ chức.
- ID được SDK kiểm tra và Cogover kiểm tra lại; ID hoặc option không hợp lệ ném
  `ValidationError`. Mọi method đều trả về promise, và đối số không hợp lệ làm promise đó
  bị reject thay vì ném lỗi ngay khi gọi method. Các method `get` trả `null` với ID không tồn tại; `members`,
  `managers`, `managerChain`, `ancestors` và `tree({ rootId })` ném `NotFoundError`
  với `resource` là `"department"` hoặc `"position"`.
- Khi không đọc được cơ cấu tổ chức, lời gọi ném `CogoverApiError` với code
  `ORGANIZATION_UNAVAILABLE`.
- Dùng `getMany` hoặc `members` thay vì gọi `get` trong vòng lặp: mỗi lời gọi là một
  capability call.

## Schema API

`SchemaApi<Schema>.object(slug)` đọc metadata Object và trả:

```typescript
interface ObjectMetadata {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly fields: readonly {
    readonly id: string;
    readonly name: string;
    readonly slug: string;
    readonly fieldType: string;
    readonly required: boolean;
    readonly multiple: boolean;
    readonly readOnly: boolean;
    readonly manualModifyAllow?: boolean;
    readonly creatable?: boolean;
    readonly metaData?: Readonly<Record<string, unknown>>;
    readonly options?: readonly {
      readonly id: string;
      readonly slug: string;
      readonly value: string;
      readonly isDefault?: boolean;
    }[];
  }[];
}

interface SchemaApi<Schema extends object = EffectiveWorkspaceObjects> {
  object<Slug extends keyof Schema & string>(slug: Slug): Promise<ObjectMetadata>;
}
```

`manualModifyAllow` là `false` khi người dùng không được sửa field khi chỉnh sửa record,
và `creatable` là `false` khi họ không được đặt giá trị field khi tạo record. Thao tác
ghi đặt giá trị cho field như vậy dưới danh tính người gọi hoặc qua `data.asUser()` ném
`ValidationError`; `data.asSystem()` được phép đặt giá trị đó.

Schema API chỉ đọc. SDK không public thao tác tạo, sửa hoặc xoá Object/field/option.
Object slug không hợp lệ ném `ValidationError`.

## Logging

`context.log` implement `ScriptLogger`:

```typescript
interface ScriptLogger {
  debug(message: string, details?: unknown): void;
  info(message: string, details?: unknown): void;
  warn(message: string, details?: unknown): void;
  error(message: string, details?: unknown): void;
}
```

Mỗi lời gọi ghi một dòng vào standard output của lần thực thi, với mọi level:
`[LEVEL] message`, sau đó là một dấu cách và `details` dạng JSON khi có `details`, ví dụ
`[WARN] Stock is low {"sku":"A-1","left":2}`. `details` là string được ghi trong dấu
ngoặc kép. Chuỗi JSON bị cắt ở 8.192 ký tự và khi đó kết thúc bằng `…[truncated]`.
Giá trị JSON không biểu diễn được sẽ được ghi ở dạng dễ đọc thay vì gây lỗi: tham chiếu
lặp lại tới một object bao ngoài thành `"[Circular]"`, `bigint` thành chuỗi số thập phân,
`Error` thành `{"name":…,"message":…}` không kèm stack, `Map` thành object và `Set` thành
mảng. Khi hoàn toàn không serialize được `details`, ví dụ vì `toJSON()` ném lỗi, dòng
log kết thúc bằng `[unserializable]`; lời gọi log không bao giờ ném lỗi. Không đưa
credential, token, dữ liệu cá nhân hoặc secret khác vào bất kỳ đối số nào.

## Errors

```typescript
class CogoverApiError extends Error {
  readonly code: string;
  readonly r: number | undefined;
  readonly details?: unknown;
  constructor(code: string, message: string, details?: unknown);
}

class NotFoundError extends CogoverApiError {
  readonly resource: string;
  readonly resourceId: string;
  constructor(resource: string, resourceId: string, message?: string, details?: unknown);
}

class ValidationError extends CogoverApiError {
  constructor(message: string, details?: unknown);
}

class PermissionDeniedError extends CogoverApiError {
  constructor(message: string, details?: unknown);
}

class RateLimitError extends CogoverApiError {
  constructor(message: string, details?: unknown);
}

class RetryableError extends CogoverApiError {
  constructor(message: string, details?: unknown);
}

class StateConflictError extends CogoverApiError {
  constructor(message: string, details?: unknown);
}

class LockUnavailableError extends CogoverApiError {
  constructor(key: string, message?: string, details?: unknown);
}

class LockLostError extends CogoverApiError {
  constructor(message: string, details?: unknown);
}
```

Các lỗi dịch vụ được SDK map sang các error trên. Các error giữ:

- `error.code`: nhóm lỗi SDK, ví dụ `PERMISSION_DENIED`.
- `error.r`: mã `r` gốc từ server, ví dụ `37`; là `undefined` nếu không có response
  từ server (như lỗi validation trong SDK).
- `error.message`: thông báo gốc; `error.details` giữ chi tiết kèm theo, gồm `r`.

`RetryableError` (`code: "RETRYABLE"`) báo một lỗi tạm thời. SDK ném lỗi này cho thao
tác ghi record mà trigger before-change không kiểm tra được (`details.reason` là
`"TRIGGER_FAILED"`, xem [Record trigger](#validate-và-sửa-record)), và
code của project tự ném lỗi này. Handler của trigger after-change hoặc job handler ném
lỗi này để báo một lỗi tạm thời, và Cogover sẽ chạy lại handler sau (xem
[Quy tắc thực thi after-change](#quy-tắc-thực-thi-after-change) và
[Quy tắc thực thi job](#quy-tắc-thực-thi-job)). Ở những nơi khác lỗi này không có
ý nghĩa đặc biệt: script để lỗi thoát ra sẽ trả HTTP 422, và trigger before-change
ném lỗi này sẽ làm thao tác ghi bị từ chối như mọi lỗi khác.

Lệnh đọc record (`get`, `getMany` hoặc `list`) không có option `fields` hợp lệ ném
`ValidationError` với message `fields is required: pass field slugs or "*"
(@cogover/sdk 0.13.0+)`. Cogover trả cùng lỗi này cho phiên bản project đã publish bằng
SDK cũ mà đọc không có `fields` (xem [Chọn field](#chọn-field)).

`jobs.enqueue`, `secrets.get` và `crypto` thất bại với `ValidationError`,
`PermissionDeniedError` hoặc `RateLimitError` như mô tả trong mục của chúng, và với
`CogoverApiError` có `code` là `JOBS_DISABLED` hoặc `SECRETS_DISABLED` khi tính
năng chưa được bật cho Workspace. `crypto.aesDecrypt` và `crypto.rsaDecrypt` ném
`CogoverApiError` với `code: "DECRYPTION_FAILED"` khi không giải mã được ciphertext.

`notifications.send` và `email.send` thất bại với `ValidationError`, `NotFoundError`,
`PermissionDeniedError` hoặc `RateLimitError` như mô tả trong mục của chúng, với
`CogoverApiError` có `code` là `NOTIFICATIONS_DISABLED` hoặc `EMAIL_DISABLED` khi tính
năng bị tắt, và với `CogoverApiError` có `code` là `DUPLICATE_IN_PROGRESS` trong lúc
một lời gọi trước đó cùng `idempotencyKey` vẫn đang gửi. Hộp thư gửi không được
Project policy cho phép được báo bằng `PermissionDeniedError` có `details.reason` là
`"EMAIL_SENDER_NOT_GRANTED"`.

Script có thể bắt lỗi và tự chọn mã/thông báo trả cho client, không cần forward lỗi gốc.
Thông báo public trong `msg`, `message` và các field tương tự luôn phải viết bằng
tiếng Anh, kể cả khi tài liệu hoặc giao diện sử dụng ngôn ngữ khác.

```typescript
try {
  await orders.records.update(id, fields);
} catch (error) {
  if (error instanceof CogoverApiError && error.r === 37) {
    return { r: 1001, msg: "You do not have permission to update this order." };
  }
  throw error;
}
```

Import `CogoverApiError` từ `@cogover/sdk`. JSON do script `return` vẫn là response
do script tự định nghĩa với HTTP 200.

Với lỗi SDK thoát khỏi `defineScript`, endpoint HTTP trả lỗi có `r` bằng HTTP
status, `code` và `msg` an toàn:

| SDK code | HTTP / `r` |
|---|---|
| `PERMISSION_DENIED` | 403 |
| `NOT_FOUND` | 404 |
| `METHOD_NOT_ALLOWED` | 405 |
| `VALIDATION_ERROR` | 400 |
| `RATE_LIMITED` | 429 |
| `STATE_CONFLICT` | 409 |
| `LOCK_NOT_ACQUIRED` | 409 |
| `LOCK_LOST` | 409 |
| `STATE_SERVICE_UNAVAILABLE` | 503 |
| `LOCK_SERVICE_UNAVAILABLE` | 503 |
| `ORGANIZATION_UNAVAILABLE` | 503 |
| `FETCH_DISABLED` | 503 |
| `FETCH_BLOCKED` | 400 |
| `FETCH_REQUEST_TOO_LARGE` | 413 |
| `FETCH_RESPONSE_TOO_LARGE` | 502 |
| `FETCH_TIMEOUT` | 504 |
| `FETCH_FAILED` | 502 |
| `COGOVER_API_ERROR` | 422 |
| `RETRYABLE` | 422 |

Thiếu phê duyệt danh tính được chọn trả thêm `reason: "IDENTITY_NOT_GRANTED"`;
không có nghĩa nhân sự đích đã bị từ chối truy cập một bản ghi cụ thể.
Không trả thông báo lỗi gốc, stack trace hoặc details tuỳ ý.
`writesMayHaveCompleted` là true nếu lần thực thi đã gửi ít nhất một lời gọi có thể
thay đổi dữ liệu bên ngoài, kể cả khi thao tác sau đó thất bại: ghi record,
`state.set` hoặc `state.delete`, mọi lời gọi `locks` (kể cả `acquire` trả `null`), push
message, `notifications.send`, `email.send`, hoặc `fetch` có method khác `GET` và `HEAD`.
Vì vậy `LockUnavailableError` thoát khỏi script luôn báo `true`. Đây là cảnh báo thận
trọng, không xác nhận ghi thành công.
Lỗi không xác định và lỗi giới hạn tài nguyên vẫn trả HTTP 422 chung.
Các phản hồi này không rollback thao tác ghi trước đó; không tự động retry ghi.

## Giới hạn của một lần thực thi

Mỗi lần thực thi chạy trong giới hạn của nền tảng. Các giá trị dưới đây là mặc định;
chúng do nền tảng thiết lập và có thể khác giữa các môi trường.

- Một HTTP route và một record trigger được gọi tối đa 20 capability call. Mỗi lời gọi
  `data`, `schema`, `state`, `locks`, `push`, `notifications`, `email`, `jobs`,
  `secrets`, `crypto`, `org` hoặc `fetch` tính một lần. Một background job được gọi 200.
  Lời gọi vượt ngân sách và mọi lời gọi sau đó ném `RateLimitError` (`details.limit` là
  ngân sách) mà không được gửi đi, nên script có thể bắt được.
- Một HTTP route có 8 giây wall-clock, tính từ lúc handler bắt đầu chạy, kể cả thời gian
  chờ capability call, chờ lock hoặc chờ server bên ngoài. Record trigger dùng
  `timeoutMs` của nó, background job dùng `timeoutMs` của job. Vượt thời gian sẽ kết thúc
  toàn bộ lần thực thi: script không bắt được, và HTTP route trả response HTTP 422 chung.
- Một capability request, đã mã hoá JSON cùng tham số, không được vượt quá 262.144
  byte. Request lớn hơn bị từ chối trước khi gửi bằng `ValidationError`, hoặc
  `CogoverApiError` có `code: "FETCH_REQUEST_TOO_LARGE"` với `fetch`; `details.limit` là
  giới hạn. Kết quả capability lớn hơn 1.048.576 byte cũng bị giữ lại theo cách đó
  (`FETCH_RESPONSE_TOO_LARGE` với `fetch`): hãy yêu cầu ít record hơn, hoặc nêu field
  thay cho `"*"`. Bản thân
  thao tác vẫn đã chạy, nên thao tác ghi có thể đã hoàn tất.
- Khi Workspace đã có quá nhiều lần thực thi đang chờ, lời gọi HTTP mới bị từ chối với
  HTTP 429 và `code: "RATE_LIMITED"` trước khi chạy bất cứ gì; hãy thử lại sau.

Khi một API có quota riêng cho mỗi lần thực thi không nhỏ hơn ngân sách lời gọi, như 20
lời gọi `fetch` hoặc 20 lần đọc secret, ngân sách lời gọi sẽ hết trước trong route hoặc
trigger; cả hai đều được báo bằng `RateLimitError`.

## Khai báo Workspace

`WorkspaceObjects` là open interface. Khi chưa augmentation, object/field slug là
string và giá trị field có type `unknown`. Sinh declaration theo workspace và đưa
file đó vào TypeScript project:

```bash
npx cogover-generate-workspace-types objects.json workspace.d.ts
```

Generator đọc Object metadata, sắp xếp object/field slug và map type như sau:

| Object field type | TypeScript type được sinh |
|---|---|
| `short_text`, `long_text`, `phone`, `email`, `regex`, `auto_number`, `date` | `string` |
| `boolean` | `boolean` |
| `numeric`, `decimal`, `currency`, `percent`, `rating`, `time`, `date_time`, `time_duration` | `number` |
| `single_choice` | union các option slug, hoặc `string` |
| `multi_choices`, `label`, `cascading` | readonly array các option slug, hoặc string |
| `url` | `UrlValue` |
| `file` | `FileValue` |
| `lookup_normal`, `reference` | `RecordReference<ObjectSlug>` khi biết object đích |
| `date_range` | `readonly [string, string]` |
| `date_time_range`, `time_range` | `readonly [number, number]` |
| field type chưa biết | `unknown` |

Field không required có thêm `null`; metadata `multiple` trở thành readonly array
trừ khi base type đã là array. Khi Object đích của lookup cũng được khai báo, `fields`
của `RecordReference` có kiểu theo Object đó, và `expandLookups` chỉ nhận field slug của
Object đó. Đưa file được sinh vào TypeScript compilation và
không sửa thủ công.

File được sinh import các kiểu SDK mà field của nó dùng (`RecordReference`, `FileValue`,
`UrlValue`) bằng `import type`. File sinh bởi `@cogover/sdk` trước 0.13.0 không import
các kiểu này: với `skipLibCheck: false` nó lỗi `Cannot find name 'RecordReference'`, còn
với `skipLibCheck: true` các field lookup, file và URL âm thầm có kiểu `any`, làm mất cả
việc kiểm tra `fields`, `expandLookups` và `aggregate` trên các field đó. Hãy sinh lại
file như vậy.

## Helper tương thích

```typescript
function createGreeting(name: string): string;
```

`createGreeting("Cogover")` trả `"Hello Cogover"`. Hàm được giữ để tương thích SDK
0.1.x và không thuộc Data API.
