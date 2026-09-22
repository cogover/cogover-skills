# Bắt đầu với inbound webhook

Trước tiên, nhận một sự kiện, lưu vào Project state và trả về thành công. Thử handler trên local rồi mới publish. Phần hai bổ sung yêu cầu xác thực bằng chữ ký HMAC. Ví dụ không cần tạo Object.

## Chuẩn bị

- Cài Node.js 20 trở lên, Git, `curl` và `jq`.
- Có quyền tạo, publish, activate Project và quản lý inbound access.
- Chuẩn bị Project key cho phép ghi để chạy local và Workspace API key để publish, quản lý inbound access. Đây là hai khóa khác nhau.

Xem cách tạo Project trong [Bắt đầu với Custom Backend Module](get-started-custom-backend-module.md).

## Phần 1. Nhận sự kiện và lưu state

### 1. Tạo Project

Trong Cogover, mở **Custom Backend Module**, tạo Project tên `Webhook demo` với slug `webhook_demo`. Sao chép Project ID, rồi chạy:

```bash
git clone https://github.com/cogover/custom-backend-module-starter-project.git webhook-demo
cd webhook-demo
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
  "projectSlug": "webhook_demo"
}
```

Tạo `.env` trong thư mục này với Workspace API key của bạn:

```dotenv
COGOVER_API_KEY={WORKSPACE_API_KEY}
```

Starter đã bỏ qua `.env` và `cogover.json` trong Git. Không đặt khóa trong source code. Chạy các lệnh còn lại từ thư mục này.

### 2. Viết handler

Tạo file `src/main.ts`:

```typescript
import { createRouter } from "@cogover/sdk";

const router = createRouter();

router.post("/hooks/events", async ({ request, state, response }) => {
  const body = (request.body ?? {}) as { id?: unknown; type?: unknown };
  if (typeof body.id !== "string" || !/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(body.id)
      || typeof body.type !== "string" || body.type.length === 0 || body.type.length > 100) {
    return response.json({ error: "A valid event id and type are required" }, { status: 400 });
  }

  await state.namespace("webhook_events").set(body.id, {
    type: body.type,
    receivedAt: Date.now(),
  }, { ttlSeconds: 7 * 24 * 60 * 60 });
  return { received: true, eventId: body.id };
});

router.get("/events/:eventId", async ({ request, state, response }) => {
  const eventId = request.params.eventId ?? "";
  if (!/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(eventId)) {
    return response.json({ error: "A valid event id is required" }, { status: 400 });
  }
  const entry = await state.namespace("webhook_events").get(eventId);
  if (entry === null) {
    return response.json({ error: "Event not found" }, { status: 404 });
  }
  return { eventId, event: entry.value };
});

export default router.toHandler();
```

Handler kiểm tra `id` và `type`, lưu sự kiện rồi trả HTTP `200`. Event ID được dùng làm khóa state; dữ liệu được giữ bảy ngày. Gửi lại cùng ID sẽ ghi đè giá trị đó. Ở bước này, handler chưa kiểm tra danh tính inbound hay chữ ký nên chạy được qua Development Session trên local.

### 3. Thử trên local

Đăng nhập bằng Project key khi CLI yêu cầu, rồi khởi động máy chủ local:

```bash
cogover-dev login --profile webhook_demo
cogover-dev doctor --profile webhook_demo
COGOVER_LOCAL_PORT=3100 cogover-dev run --profile webhook_demo -- npm run dev
```

Giữ terminal đó chạy. Mở terminal thứ hai và gửi sự kiện:

```bash
curl -s -i -X POST \
  'http://127.0.0.1:3100/api/v1/ts-projects/webhook_demo/hooks/events' \
  -H 'Content-Type: application/json' \
  --data '{"id":"evt-local-1","type":"payment.succeeded"}'
```

Kết quả mong đợi là HTTP `200` và:

```json
{ "received": true, "eventId": "evt-local-1" }
```

Response thành công nghĩa là thao tác lưu state đã hoàn tất. Thử gửi `--data '{}'` để kiểm tra dữ liệu đầu vào; handler trả `400`.

Đọc lại sự kiện vừa lưu bằng route GET `/events/:eventId`:

```bash
curl -s -i \
  'http://127.0.0.1:3100/api/v1/ts-projects/webhook_demo/events/evt-local-1'
```

Kết quả mong đợi là HTTP `200` với dữ liệu đã lưu, ví dụ:

```json
{
  "eventId": "evt-local-1",
  "event": {
    "type": "payment.succeeded",
    "receivedAt": 1790000000000
  }
}
```

`receivedAt` là thời điểm nhận sự kiện, tính bằng Unix mili giây; giá trị thực tế sẽ khác ví dụ. Thay `evt-local-1` trong URL để đọc sự kiện khác. Nếu ID chưa được lưu hoặc state đã hết hạn, route trả `404` với lỗi `Event not found`. Gửi lại POST cùng ID rồi gọi GET sẽ đọc được giá trị mới nhất.

Request local này không cần inbound key hay chữ ký. CLI dùng Project key để xác thực Development Session, còn state được lưu vào Project thật trên Cogover. Bạn vẫn cần kết nối mạng và session cho phép ghi. Bước thử local này chưa cần version đã publish.

### 4. Publish và activate

Tại thư mục dự án, chạy:

```bash
npm run build
cogover-dev publish
```

Khi version ở trạng thái `READY`, activate bằng version ID mà CLI trả về:

```bash
cogover-dev activate {VERSION_ID}
```

Ví dụ chỉ dùng state nên không cần identity policy để truy cập record.

### 5. Gọi webhook đã publish

URL inbound trên Cogover bắt buộc xác thực bằng KEY hoặc HMAC, dù handler phần đầu chưa tự kiểm tra. Bắt đầu với KEY: Cogover kiểm tra khóa trước khi chạy handler. Bên gửi không cần phiên đăng nhập Cogover.

Các bước dưới đây tạo inbound access, tức quyền cho bên gửi gọi webhook bằng key. Bạn chỉ cần tạo access một lần cho mỗi bên gửi, rồi dùng lại URL và key để gửi nhiều sự kiện. Chạy lần lượt trong cùng một terminal; các biến `DEMO_*` được dùng ở những bước sau.

#### 5.1. Đặt địa chỉ Workspace

Thay `{WORKSPACE_DOMAIN}` bằng hostname Workspace, ví dụ `example.cogover.com`. Biến `DEMO_ORIGIN` giữ phần địa chỉ gốc để ghép URL webhook.

```bash
DEMO_ORIGIN='https://{WORKSPACE_DOMAIN}'
```

#### 5.2. Tạo inbound access

Lệnh sau tạo access tên `demo_sender`. CLI dùng Workspace API key trong `.env` để thực hiện thao tác quản lý này.

```bash
DEMO_CREATED=$(cogover-dev inbound create demo_sender --mode key --route-prefix /hooks/events --json)
```

- `--mode key`: bên gửi sẽ xác thực bằng inbound key.
- `--route-prefix /hooks/events`: giới hạn access vào route này và các route con.
- `--json`: trả kết quả dạng JSON để lấy ID, key và URL.

`DEMO_CREATED=$(...)` lưu kết quả vào biến thay vì in ra terminal. Lệnh này chưa gửi sự kiện hay chạy handler.

#### 5.3. Lấy ID của access

`jq` đọc JSON trong `DEMO_CREATED` và lấy trường `inboundId`. Giữ ID này để xoay key hoặc thu hồi access sau đó.

```bash
DEMO_INBOUND_ID=$(printf '%s' "$DEMO_CREATED" | jq -er '.inbound.inboundId')
```

#### 5.4. Lấy key cho bên gửi

Lấy `inboundKey` và giữ trong biến `DEMO_INBOUND_KEY`. Lệnh `curl` bên dưới sẽ dùng key này làm Bearer token.

```bash
DEMO_INBOUND_KEY=$(printf '%s' "$DEMO_CREATED" | jq -er '.inbound.inboundKey')
```

CLI chỉ trả giá trị key khi tạo hoặc xoay key. Với tích hợp thật, lưu key trong kho credential của bên gửi; không đưa vào source code hay in ra log.

#### 5.5. Ghép URL webhook

Lấy đường dẫn `inbound.url` do Cogover trả về rồi ghép với địa chỉ Workspace.

```bash
DEMO_INBOUND_URL="$DEMO_ORIGIN$(printf '%s' "$DEMO_CREATED" | jq -er '.inbound.url')"
```

`DEMO_INBOUND_URL` là URL gốc của access, kết thúc bằng `/hooks/{inboundId}`. Khi gửi sự kiện tới route `/hooks/events`, thêm `/events` vào URL này như lệnh ở bước 5.7.

#### 5.6. Xóa biến tạm và kiểm tra access

Sau khi đã lấy đủ ID, key và URL, xóa biến JSON tạm:

```bash
unset DEMO_CREATED
```

Lệnh trên chỉ xóa `DEMO_CREATED`; ba biến `DEMO_INBOUND_ID`, `DEMO_INBOUND_KEY` và `DEMO_INBOUND_URL` vẫn còn. Xem danh sách access để kiểm tra `demo_sender` đã được tạo:

```bash
cogover-dev inbound list
```

`inbound list` chỉ xem metadata, không trả lại giá trị key. Các biến shell dùng ở đây tồn tại trong terminal hiện tại; trong tích hợp thật, hệ thống gửi cần lưu URL và key để dùng lại.

#### 5.7. Gửi sự kiện

Đây là bước gọi webhook. `printf` truyền header chứa key cho `curl` qua stdin; `curl` gửi JSON tới `$DEMO_INBOUND_URL/events`. Những lần gửi tiếp theo dùng lại URL và key, không cần tạo access mới.

```bash
printf 'Authorization: Bearer %s
' "$DEMO_INBOUND_KEY" | \
  curl -s -i "$DEMO_INBOUND_URL/events" -H @- \
  -H 'Content-Type: application/json' \
  --data '{"id":"evt-prod-1","type":"payment.succeeded"}'
```

```json
{ "received": true, "eventId": "evt-prod-1" }
```

Kết quả mong đợi là HTTP `200`. Nếu thiếu key hoặc key sai, Cogover trả `401` trước khi handler chạy. URL công khai kết thúc bằng `/hooks/{inboundId}/events`; Cogover bỏ inbound ID khi khớp với route `/hooks/events`. Không cần Workspace session hay header `x-req-*`.

## Phần 2. Xác thực bên gửi bằng chữ ký

Với HMAC, bên gửi dùng khóa bí mật dùng chung để ký request. Cogover kiểm tra chữ ký trước khi gọi handler. Phần này tạo access HMAC và cập nhật handler để chỉ nhận request đã được xác thực theo cách đó.

### 6. Cập nhật handler

Thay nội dung `src/main.ts` bằng đoạn sau. Phần kiểm tra mới nằm ở đầu route POST; thao tác lưu state và route GET đọc lại giữ nguyên:

```typescript
import { createRouter } from "@cogover/sdk";

const router = createRouter();

router.post("/hooks/events", async ({ request, invocation, state, response }) => {
  if (invocation.identity !== "inbound" || invocation.inbound.mode !== "HMAC") {
    return response.json({ error: "An HMAC-authenticated inbound call is required" }, { status: 403 });
  }
  const body = (request.body ?? {}) as { id?: unknown; type?: unknown };
  if (typeof body.id !== "string" || !/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(body.id)
      || typeof body.type !== "string" || body.type.length === 0 || body.type.length > 100) {
    return response.json({ error: "A valid event id and type are required" }, { status: 400 });
  }

  await state.namespace("webhook_events").set(body.id, {
    type: body.type,
    receivedAt: Date.now(),
  }, { ttlSeconds: 7 * 24 * 60 * 60 });
  return { received: true, eventId: body.id };
});

router.get("/events/:eventId", async ({ request, state, response }) => {
  const eventId = request.params.eventId ?? "";
  if (!/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(eventId)) {
    return response.json({ error: "A valid event id is required" }, { status: 400 });
  }
  const entry = await state.namespace("webhook_events").get(eventId);
  if (entry === null) {
    return response.json({ error: "Event not found" }, { status: 404 });
  }
  return { eventId, event: entry.value };
});

export default router.toHandler();
```

Cogover đặt `invocation.identity` và `invocation.inbound.mode` sau khi xác thực; bên gửi không thể tự đặt chúng qua JSON body. Điều kiện trên yêu cầu lời gọi đi qua inbound và đã xác thực bằng HMAC. Request dùng KEY hợp lệ hoặc danh tính người dùng thông thường sẽ nhận `403` từ handler này. Chữ ký HMAC sai bị Cogover trả `401` trước khi tới handler.

Máy chủ local không mô phỏng xác thực inbound HMAC, nên route POST `/hooks/events` sau cập nhật trả `403` khi gọi local. Bạn vẫn có thể kiểm thử riêng logic parse và lưu dữ liệu; kiểm thử request có chữ ký trên version đã publish. Publish và activate thay đổi:

```bash
npm run build
cogover-dev publish
cogover-dev activate {NEW_VERSION_ID}
```

Thay `{NEW_VERSION_ID}` bằng ID version mới khi version đã `READY`.

### 7. Tạo access HMAC

Trong terminal còn biến `DEMO_ORIGIN`, tạo khóa bí mật thử nghiệm và truyền cho CLI qua stdin:

```bash
DEMO_HMAC_SECRET=$(node --input-type=module -e 'import { randomBytes } from "node:crypto"; process.stdout.write(randomBytes(32).toString("hex"));')
DEMO_CREATED=$(printf '%s' "$DEMO_HMAC_SECRET" | cogover-dev inbound create demo_signed \
  --mode hmac --route-prefix /hooks/events \
  --hmac-header X-Demo-Signature --hmac-prefix sha256= \
  --hmac-timestamp-header X-Demo-Timestamp --hmac-tolerance 300 \
  --hmac-secret-stdin --json)
DEMO_HMAC_ID=$(printf '%s' "$DEMO_CREATED" | jq -er '.inbound.inboundId')
DEMO_HMAC_URL="$DEMO_ORIGIN$(printf '%s' "$DEMO_CREATED" | jq -er '.inbound.url')"
unset DEMO_CREATED
```

### 8. Ký và gửi sự kiện

Bên gửi ký đúng chuỗi `<timestamp>.<body>`. Lệnh Node.js sau mô phỏng bên gửi trên máy bạn, chạy ngoài Project:

```bash
export DEMO_BODY='{"id":"evt-hmac-1","type":"payment.succeeded"}'
export DEMO_TIMESTAMP=$(date +%s)
DEMO_SIGNATURE=$(printf '%s' "$DEMO_HMAC_SECRET" | node --input-type=module -e '
  import { createHmac } from "node:crypto";
  let key = "";
  for await (const chunk of process.stdin) key += chunk;
  process.stdout.write(createHmac("sha256", key)
    .update(process.env.DEMO_TIMESTAMP + "." + process.env.DEMO_BODY).digest("hex"));
')
curl -s -i "$DEMO_HMAC_URL/events" \
  -H 'Content-Type: application/json' \
  -H "X-Demo-Timestamp: $DEMO_TIMESTAMP" \
  -H "X-Demo-Signature: sha256=$DEMO_SIGNATURE" --data-binary "$DEMO_BODY"
```

Kết quả mong đợi là HTTP `200` và:

```json
{ "received": true, "eventId": "evt-hmac-1" }
```

Đổi body mà không ký lại, hoặc bỏ header chữ ký: Cogover trả `401`. Gửi lại cùng chữ ký kèm timestamp thường cũng nhận `401`. Để gửi lại hợp lệ, chờ sang timestamp mới rồi chạy lại các lệnh ký.

Trong ví dụ đơn giản này, sự kiện được ký lại với cùng ID sẽ ghi đè state đã có. Khi thêm xử lý nghiệp vụ, cần kiểm tra event ID trùng và xử lý lỗi như phần giải thích bên dưới.

### 9. Dọn dữ liệu thử

Thu hồi cả hai access sau khi thử xong. Thu hồi là vĩnh viễn; CLI sẽ hỏi xác nhận:

```bash
cogover-dev inbound revoke "$DEMO_INBOUND_ID"
cogover-dev inbound revoke "$DEMO_HMAC_ID"
unset DEMO_INBOUND_KEY DEMO_HMAC_SECRET DEMO_SIGNATURE DEMO_TIMESTAMP DEMO_BODY
```

State đã lưu hết hạn sau bảy ngày. Nhấn Ctrl+C để dừng máy chủ local nếu vẫn còn chạy.

## Chọn cách xác thực

| Chế độ | Bên gửi cung cấp | Dùng khi |
|---|---|---|
| `KEY` | `Authorization: Bearer <key>` hoặc `X-Cogover-Inbound-Key: <key>` | Bên gửi đặt được header cố định. |
| `HMAC` | Chữ ký HMAC-SHA256 trên raw body, có thể kèm timestamp | Bên gửi hỗ trợ cách ký đã cấu hình. |

Tạo một access cho mỗi hệ thống ngoài và giới hạn `routePrefix` vào các route cần dùng. `/hooks/events` cho phép route đó cùng các route con, nhưng không cho `/hooks/events-extra`. Thêm `--expires-at <ISO-8601>` cho quyền truy cập tạm thời. Inbound credential chỉ dùng tại URL webhook của nó; Workspace session không thay thế được.

Với HMAC, `--hmac-encoding` mặc định là `hex`, hoặc chọn `base64`. Prefix như `sha256=` là tùy chọn. Không có header timestamp thì chỉ ký raw body. Nếu có, ký `<timestamp>.<raw body>` và gửi đúng giá trị timestamp đó. Cogover nhận Unix giây hoặc mili giây; dung sai mặc định 300 giây, có thể đặt từ 1 đến 86.400 giây.

Timestamp giới hạn độ cũ của request, còn Cogover kiểm tra chữ ký kèm timestamp đã được dùng chưa. Việc chặn chữ ký đã dùng không được bảo đảm trong mọi tình huống, nên handler vẫn phải kiểm tra sự kiện trùng. Không có timestamp thì cùng body đã ký có thể được gửi lại vô thời hạn. Đối chiếu đúng định dạng chữ ký của nhà cung cấp: chế độ có sẵn không hỗ trợ mọi cách ký riêng của từng dịch vụ.

### Handler nhận được gì

Khi gọi qua URL inbound đã publish:

| Field | Ý nghĩa |
|---|---|
| `invocation.identity` | `"inbound"`; không có người dùng đăng nhập. |
| `invocation.inbound` | ID, tên và chế độ của access. |
| `request.path` | Route dưới `/hooks`, không chứa inbound ID. |
| `request.body` | JSON object đã parse; bằng `{}` với mảng, form, văn bản hoặc body rỗng. |
| `request.rawBody` | Body gốc dưới dạng chuỗi UTF-8. Dùng khi parse payload không phải object hoặc kiểm tra chữ ký bổ sung. |
| `request.contentType` | Content type gửi tới. |
| `request.headers` | Header an toàn, tên viết thường; inbound key, header chữ ký đã cấu hình, Authorization và cookie bị loại bỏ. |

Không dựng lại body đã ký bằng `JSON.stringify(request.body)`: khoảng trắng và thứ tự key có thể đổi. Trả giá trị thông thường sẽ nhận HTTP `200`; dùng response helper để chọn status khác. Bên gửi nhận kết quả trực tiếp, không có envelope của Workspace.

### Truy cập record và xử lý việc dài

Lời gọi inbound không có người dùng. Để truy cập record, cấu hình **Identity policy** của Project với `allowInternalSystem: true` và grant giới hạn vào các Object, thao tác cần dùng. Duyệt policy cho từng version mới publish. Chỉ activate version thì chưa cấp quyền truy cập record. Xem [tài liệu identity policy](custom-backend-module-api-reference.md#identity-policy).

Giữ handler ngắn: kiểm tra, lưu hoặc enqueue, rồi xác nhận đã nhận. Với việc dài, khai báo và activate một [background job](get-started-background-jobs.md), rồi enqueue bằng event ID ổn định làm idempotency key. Job này chạy với danh tính system và cần cùng policy nếu truy cập record.

Ví dụ ghi đè state khi dùng lại event ID; nó chưa ngăn việc thực hiện nghiệp vụ nhiều lần. Để kiểm tra sự kiện trùng, tạo dấu đã nhận với `expectedVersion: 0` và xử lý `StateConflictError` khi dấu đã tồn tại. Thêm định danh bên gửi vào khóa nếu nhiều bên có thể dùng cùng event ID. Nếu ghi record hoặc gọi dịch vụ ngoài sau khi tạo dấu, cần có cách khôi phục khi các thao tác đó lỗi; dấu đã nhận không chứng minh công việc đã xong.

### Phát triển local và quản lý access

Phần 1 chạy được trên local dưới danh tính người dùng của Project key. Máy chủ local của starter không mô phỏng xác thực inbound, kiểm tra gửi lại, `rawBody` hay `contentType`. Vì vậy, điều kiện HMAC thêm ở phần 2 trả `403` khi gọi local; kiểm chứng phần này qua URL inbound đã publish.

`inbound list` trả metadata, không trả key. `rotate` chỉ dùng cho chế độ KEY và vô hiệu key cũ ngay. HMAC secret được đổi qua thao tác `update` của management API. Thu hồi là vĩnh viễn và không đổi được chế độ xác thực của một access. Xem [API quản lý inbound](custom-backend-module-api-reference.md#inbound-access).

## Xử lý sự cố

| Vấn đề | Cần kiểm tra |
|---|---|
| `401 Inbound authentication failed` | Đúng access ID, key hoặc chữ ký, route prefix, trạng thái active, hạn dùng và timestamp. Response chủ ý không tiết lộ bước kiểm tra nào thất bại. |
| Gửi lại request HMAC nhận `401` | Ký lại bằng timestamp mới; giữ event ID để kiểm tra trùng. |
| `404` | Đúng Project slug, version active và route đã đăng ký. URL công khai phải có inbound ID. |
| Ví dụ trả `400` | Gửi JSON object có `id` hợp lệ và `type` không rỗng. |
| `IDENTITY_NOT_GRANTED` khi truy cập record | Duyệt policy cho phép system truy cập record cho version active. |
| `413` | Toàn bộ script input vượt 256 KiB; cần chừa chỗ cho metadata và gửi payload nhỏ hơn. |
| `429` | Giới hạn 600 request mỗi phút cho mỗi inbound access và mỗi địa chỉ gọi; gộp hoặc giãn request. |
| Local trả `403` sau phần 2 | Máy chủ local không cung cấp danh tính inbound HMAC; thử request có chữ ký trên Cogover. |
| Mất key | Xoay access loại KEY và cập nhật bên gửi; không lấy lại được key cũ. |

## Đọc thêm

- [API inbound của SDK](cogover-sdk-api-reference.md#inbound-webhook) và [API gọi webhook](custom-backend-module-api-reference.md#gọi-inbound-webhook).
- [Background job](get-started-background-jobs.md): xác nhận sớm rồi xử lý sau.
- [Secrets và credentials](get-started-secrets-and-credentials.md): xác thực khi gọi ngược lại hệ thống gửi.
- [Crypto](get-started-crypto.md): cách ký bổ sung và kiểm tra raw body.
