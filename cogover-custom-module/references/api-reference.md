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
}
```

`defineScript` ném `ValidationError` nếu handler không phải function. Handler kết
quả ném lỗi nếu input không phải JSON hợp lệ hoặc output không serialize được sang
JSON. Trả `null` tạo kết quả null; trả `undefined` là không hợp lệ.

Hàm wrapper parse input JSON, cung cấp `input`, `request`, `invocation`, `response`, `data`, `schema`, `log`, `state`, `locks`, chờ kết
quả async và serialize output thành JSON.

## HTTP router và request context

`ScriptContext<TInput, TSchema>` cung cấp `input`, `request`, `invocation`, `response`, `data`, `schema`,
`log`, `state` và `locks` cho cả script handler lẫn route handler. `input` giữ input invocation hiện có.
Nên dùng `request.body` cho dữ liệu nghiệp vụ: body không chứa invocation metadata
và các field transport/xác thực đã được Cogover loại bỏ.

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
}
```

Request descriptor và các map metadata được freeze; body không bị deep-freeze.
Method, path, query và header trong allowlist đến từ Cogover, không lấy từ field
nghiệp vụ. Query lặp tên trở thành readonly array. Tên header được đổi sang chữ
thường; credential như `authorization` và `cookie` không bao giờ lộ vào script.
Path param được percent-decode sau khi route an toàn đã khớp. Kiểu TypeScript không
validate input nghiệp vụ lúc chạy.

## Danh tính invocation và workspace hiện tại

`context.invocation` là snapshot đồng bộ, bất biến được tạo từ metadata mà Cogover
đã xác thực và nạp sẵn cho lần thực thi hiện tại. Đọc property này không gửi yêu
cầu tới Data API.

```typescript
type InvocationContext = UserInvocationContext | SystemInvocationContext;

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

interface CurrentWorkspaceMembership {
  readonly personnelId?: string;
  readonly language?: string;
  readonly timezone?: string;
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
```

Mọi field đều readonly. Các field profile/workspace optional có thể không tồn tại,
vì vậy script không được giả định chúng luôn có giá trị.

```typescript
export default defineScript(({ invocation }) => {
  if (invocation.identity === "system") {
    return {workspaceId: invocation.workspace.id, user: null};
  }
  return {
    workspaceId: invocation.workspace.id,
    accountId: invocation.user.accountId,
    personnelId: invocation.user.membership.personnelId,
  };
});
```

Cogover bỏ qua invocation metadata do caller tự gửi và dựng snapshot từ request
context đã xác thực. Raw authentication data, token và credential không được đưa
vào. Handler gọi bên ngoài Cogover không có invocation snapshot đã xác thực.

### `createRouter<TSchema = EffectiveWorkspaceObjects>(): ScriptRouter<TSchema>`

Tạo router độc lập. `TSchema extends object` mặc định là schema workspace hiệu lực,
giữ suy luận `WorkspaceObjects` qua module augmentation cho data và schema API.
Route phân biệt hoa/thường theo method và path tĩnh/động; route tĩnh được ưu tiên
hơn route động. `/` ứng với URL project canonical
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
ném `NotFoundError` (HTTP 404). Invocation dùng method chưa hỗ trợ có
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
hoặc dạng body:

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
`application/octet-stream`. Redirect chỉ nhận 301, 302, 303, 307 hoặc 308. Helper
trả `ScriptResponse` opaque; code ứng dụng không được tự tạo transport envelope.
Redirect location phải khác rỗng, dài tối đa 4.096 ký tự và không chứa newline.
`response.json()` không nhận `undefined`; `response.text()` yêu cầu string và
`response.bytes()` yêu cầu `Uint8Array`.

## Outbound HTTP `fetch`

```typescript
function fetch(input: string, init?: CogoverFetchInit): Promise<CogoverFetchResponse>;

interface CogoverFetchInit {
  readonly method?: "GET" | "HEAD" | "POST" | "PUT" | "PATCH" | "DELETE";
  readonly headers?: Readonly<Record<string, string>>;
  readonly body?: string;
  readonly timeoutMs?: number;
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
lý. `input` phải là URL HTTPS public tuyệt đối, port 443 và không chứa userinfo,
fragment hoặc IP literal. `body` chỉ nhận string; dùng `JSON.stringify()` cho JSON.
`timeoutMs` phải là số nguyên dương và luôn bị giới hạn bởi hạn mức của platform.

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
agent, DNS resolver hay TLS configuration. Không hỗ trợ URL HTTP, port khác 443,
userinfo hoặc IP-literal host. Header framing/hop-by-hop/proxy/forwarding và header
request dành riêng cho Cogover bị từ chối. Request/response, header, thời gian, số call, destination
và concurrency đều có quota.

Lỗi được ném dưới dạng `CogoverApiError` với code `FETCH_DISABLED`, `FETCH_BLOCKED`,
`FETCH_REQUEST_TOO_LARGE`, `FETCH_RESPONSE_TOO_LARGE`, `FETCH_TIMEOUT` hoặc
`FETCH_FAILED`; quota dùng `RateLimitError`. Với POST/PUT/PATCH/DELETE bị timeout
hoặc mất response, remote server có thể đã xử lý request. Hãy dùng idempotency key
của API đích và không retry mù.

## Record API

```typescript
const orders = data.object("order");
await orders.records.get(id, { fields });
await orders.records.list({ where, orderBy, fields, limit, cursor });
await orders.records.create(fields);
await orders.records.update(id, fields);
await orders.records.batchInsert(records);
await orders.records.batchUpdate(records);
await orders.records.upsertByUniqueField(matchBy, fields);
await orders.records.deleteMany(ids);
```

### Giá trị và kết quả record

```typescript
type CogoverRecordId = string & {
  readonly __cogoverRecordIdBrand: unique symbol;
};

interface RecordReference<ObjectSlug extends string = string> {
  readonly id: CogoverRecordId;
  readonly name: string;
  readonly objectSlug?: ObjectSlug;
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
    readonly createdBy?: { readonly id: string; readonly name: string };
  };
}

interface RecordPage<Fields> {
  readonly items: CogoverRecord<Fields>[];
  readonly total: number;
  readonly nextCursor?: string;
}

interface DeleteResult {
  readonly deleted: CogoverRecordId[];
  readonly notDeleted: CogoverRecordId[];
}

interface BatchWriteRowResult {
  readonly referenceId: string;
  readonly id?: CogoverRecordId;
  readonly r: number;
  readonly msg?: string;
  readonly success: boolean;
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
interface GetRecordOptions<Fields> {
  readonly fields?: readonly (keyof Fields & string)[];
}

interface ListOptions<Fields> {
  readonly where?: FilterExpression;
  readonly orderBy?: readonly SortExpression[];
  readonly fields?: readonly (keyof Fields & string)[];
  readonly limit?: number;
  readonly cursor?: string;
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

interface RecordsApi<Fields> extends RecordWritesApi<Fields> {
  get(id: string, options?: GetRecordOptions<Fields>): Promise<CogoverRecord<Fields> | null>;
  list(options?: ListOptions<Fields>): Promise<RecordPage<Fields>>;
}

interface WriteObjectClient<Fields> {
  readonly slug: string;
  readonly fields: FieldReferences<Fields>;
  readonly records: RecordWritesApi<Fields>;
}

interface ObjectClient<Fields> extends WriteObjectClient<Fields> {
  readonly records: RecordsApi<Fields>;
}

interface AsUserDataApi<Schema extends object = EffectiveWorkspaceObjects> {
  object<Slug extends keyof Schema & string>(slug: Slug): ObjectClient<Schema[Slug]>;
}

interface DataApi<Schema extends object = EffectiveWorkspaceObjects> {
  object<Slug extends keyof Schema & string>(slug: Slug): ObjectClient<Schema[Slug]>;
  asUser(personnelId: string): AsUserDataApi<Schema>;
  asSystem(): DataApi<Schema>;
}
```

`get` trả `CogoverRecord<Fields> | null`; `list` trả `RecordPage<Fields>`.

SDK chuẩn hoá boolean `0/1` thành `true/false`. Lookup/reference chỉ public
`id`, `name`, `objectSlug`, không chuyển tiếp các field lồng từ record được lookup.
Khi ghi, developer có thể truyền record ID hoặc `RecordReference`; chỉ ID được gửi
xuống Record API.

`create` và `update` yêu cầu object field không rỗng. `batchInsert` nhận 1–200
object field; `batchUpdate` nhận 1–200 phần tử `{ id, fields }`. Batch là
best-effort theo từng row, không phải `allOrNone`; luôn kiểm tra `success` hoặc
từng phần tử `results`. `referenceId` là index đầu vào bắt đầu từ 0, dạng chuỗi.

`deleteMany` yêu cầu ít nhất một record ID không rỗng và trả hai mảng `deleted`,
`notDeleted`. Record ID, object slug và field slug được validate trước khi gửi.

`upsertByUniqueField(matchBy, fields)` yêu cầu `matchBy` là slug của một field đã
được cấu hình thành single-field unique key và field đó phải có giá trị trong
`fields`. Kết quả `{ id, created }` cho biết record vừa được tạo hay cập nhật.
Cogover yêu cầu đồng thời quyền tạo và cập nhật record cho upsert.

Xung đột unique key được trả thành `ValidationError`
với `details.reason === "UNIQUE_KEY_VIOLATION"`, `objectSlug` và `fieldSlug`.
Public error không trả lại giá trị business key bị trùng.

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
gây `ValidationError`. `object(slug)` trả `ObjectClient<TFields>`, có
`records: RecordsApi<TFields>` gồm toàn bộ API đọc/ghi, batch và upsert, giữ nguyên
kiểu tham số và kết quả của Record API mặc định.

`get(id, options?)` trả `CogoverRecord<TFields> | null`; `list(options?)` trả
`RecordPage<TFields>`. Chọn field, filter, sort và cursor hoạt động như client
mặc định. Đọc áp dụng quyền của nhân sự được chọn và giới hạn field của project
đã duyệt. Truy vấn thành công nhưng không có record trả `null`; lỗi server được
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
public đã xác thực. Hỗ trợ toàn bộ Record API, gồm batch và upsert. Quyền hệ
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
không fallback sang hệ thống hay người gọi. Lỗi server giữ `CogoverApiError.r` gốc.
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

Ghi một giá trị JSON tối đa 32 KiB (32.768 byte UTF-8 sau serialize). `ttlSeconds`
từ 1 giây đến 365 ngày; bỏ qua để state không tự hết hạn. Hai option phải là safe
integer. `expectedVersion` áp dụng
compare-and-set: `0` chỉ tạo khi chưa tồn tại, số dương chỉ ghi đúng version, bỏ qua
để upsert vô điều kiện. Xung đột ném `StateConflictError`; entry trả về chứa version mới.

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
định 30.000 ms. Mỗi invocation giữ tối đa 16 lock. Key dài tối đa 255 ký tự,
namespace tối đa 128 và dùng cùng quy tắc ký tự như tên state. Numeric option phải
là safe integer.

Lease có `id`, `key`, `namespace`, `fencingToken`, `expiresAt`, cùng
`renew(leaseMs?)` và `release()`. `renew`/`release` xác minh quyền sở hữu bằng token
do Cogover quản lý; token đó không lộ cho script. Lease mất hoặc hết hạn ném
`LockLostError`. `release()` lặp lại trên cùng object lease là no-op sau lần thành công.

### `locks.withLock(key, callback)` / `locks.withLock(key, options, callback)`

Lấy lock, chạy callback và release trong `finally`. Nếu không lấy được lock, hàm
ném `LockUnavailableError`. Hàm không tự renew; callback dài phải gọi `lease.renew()`
trước khi `expiresAt`.

Lock chỉ bảo đảm một lease hợp lệ tại một thời điểm; timeout, pause hoặc lỗi mạng có
thể làm execution cũ tiếp tục sau khi lease hết hạn. Khi hệ thống đích hỗ trợ,
hãy lưu/kiểm tra `fencingToken` và từ chối token cũ. Lock không thay thế idempotency,
không tạo exactly-once và không gộp Record API với state thành một transaction.

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

`details` được ghi tách khỏi message. Không đưa credential, token, dữ liệu cá nhân
hoặc secret khác vào bất kỳ đối số nào.

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
| `FETCH_DISABLED` | 503 |
| `FETCH_BLOCKED` | 400 |
| `FETCH_REQUEST_TOO_LARGE` | 413 |
| `FETCH_RESPONSE_TOO_LARGE` | 502 |
| `FETCH_TIMEOUT` | 504 |
| `FETCH_FAILED` | 502 |
| `COGOVER_API_ERROR` | 422 |

Thiếu phê duyệt danh tính được chọn trả thêm `reason: "IDENTITY_NOT_GRANTED"`;
không có nghĩa nhân sự đích đã bị từ chối truy cập một bản ghi cụ thể.
Không trả thông báo lỗi gốc, stack trace hoặc details tuỳ ý.
`writesMayHaveCompleted` là true nếu đã gửi ít nhất một thao tác ghi record, kể cả
khi thao tác sau đó thất bại. Đây là cảnh báo thận trọng, không xác nhận ghi thành công.
Lỗi không xác định và lỗi giới hạn tài nguyên vẫn trả HTTP 422 chung.
Các phản hồi này không rollback thao tác ghi trước đó; không tự động retry ghi.

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
trừ khi base type đã là array. Đưa file được sinh vào TypeScript compilation và
không sửa thủ công.

## Helper tương thích

```typescript
function createGreeting(name: string): string;
```

`createGreeting("Cogover")` trả `"Hello Cogover"`. Hàm được giữ để tương thích SDK
0.1.x và không thuộc Data API.
