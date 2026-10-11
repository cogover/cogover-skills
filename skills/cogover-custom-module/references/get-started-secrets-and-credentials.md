# Bắt đầu với secrets và credentials

Lưu một Bearer credential, dùng nó gọi API rồi xoay giá trị mà không publish code mới. Bạn cũng sẽ thử đọc secret loại opaque. Ví dụ gọi `httpbin.org` bằng giá trị thử nghiệm và không cần Object.

## Chuẩn bị

- Cài Node.js 20 trở lên, Git và `curl`.
- Có Workspace đã bật secrets cho Custom Backend Module.
- Có API key của Workspace SuperAdmin và quyền tạo, publish, activate Project. Chỉ có Project key thì không quản lý được secret.

Dùng giá trị thử nghiệm trong bài này: credential sẽ được gửi tới dịch vụ kiểm thử công khai `httpbin.org`. Nếu chưa quen việc tạo Project, xem [Bắt đầu với Custom Backend Module](get-started-custom-backend-module.md).

## 1. Tạo Project

Trong Cogover, mở **Custom Backend Module**, tạo Project tên `Secrets demo` với slug `secrets_demo`. Sao chép Project ID, rồi chạy:

```bash
git clone https://github.com/cogover/custom-backend-module-starter-project.git secrets-demo
cd secrets-demo
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
  "projectSlug": "secrets_demo"
}
```

Tạo `.env` trong thư mục này với Workspace API key của bạn:

```dotenv
COGOVER_API_KEY={WORKSPACE_API_KEY}
```

Starter đã bỏ qua `.env` và `cogover.json` trong Git. Không đặt khóa trong source code. Chạy các lệnh còn lại từ thư mục này.

## 2. Lưu credential và secret

Chạy các lệnh sau. Tại mỗi ô nhập ẩn, nhập giá trị thử nghiệm ghi bên dưới:

```bash
cogover-dev secrets set demo_api --kind bearer --allowed-host httpbin.org
cogover-dev secrets set demo_secret --kind opaque
cogover-dev secrets list
```

Nhập `demo-token-v1` cho `demo_api` và `demo-value-v1` cho `demo_secret`. Đây là giá trị thử nghiệm công khai, không phải khóa thật. Kết quả mong đợi là hai mục có trạng thái `ACTIVE`, value version bằng `1`.

`demo_api` cho phép Cogover thêm header Authorization khi gọi `httpbin.org`. `demo_secret` là giá trị code có thể đọc. Danh sách chỉ hiển thị metadata, không trả lại giá trị đã lưu.

## 3. Viết route

Tạo `src/main.ts`:

```typescript
import { createRouter, fetch } from "@cogover/sdk";

const router = createRouter();

router.get("/credential-check", async ({ response }) => {
  const upstream = await fetch("https://httpbin.org/bearer", {
    credential: "demo_api",
    timeoutMs: 10_000,
  });
  if (!upstream.ok) {
    return response.json({ ok: false, upstreamStatus: upstream.status }, { status: 502 });
  }
  const result = await upstream.json<{ authenticated?: boolean }>();
  // The upstream body also contains the token. Return only the boolean.
  return { authenticated: result.authenticated === true, upstreamStatus: upstream.status };
});

router.get("/secret-check", async ({ secrets }) => {
  const value = await secrets.get("demo_secret");
  return { configured: value.length > 0 };
});

export default router.toHandler();
```

Route credential chỉ dùng tên `demo_api`; Cogover thêm `Authorization: Bearer ...`. Route còn lại đọc `demo_secret` và chỉ trả việc đã có giá trị hay chưa. Cả hai route đều không trả hay ghi log giá trị secret.

## 4. Publish và activate

```bash
npm run build
cogover-dev publish
```

Khi CLI báo `READY`, activate bằng version ID vừa được in ra:

```bash
cogover-dev activate {VERSION_ID}
```

Secret thuộc Project và được dùng bởi version đang active. Ví dụ không truy cập record nên không cần identity policy cho record.

## 5. Gọi thử hai route

Xuất Workspace session và đặt URL, thay `{WORKSPACE_DOMAIN}`:

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
DEMO_BASE='https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/secrets_demo'
curl -s --config .cogover-session.curl "$DEMO_BASE/credential-check" \
  -H 'x-req-type: 9' -H 'x-req-service: 3'
```

Kết quả mong đợi:

```json
{ "authenticated": true, "upstreamStatus": 200 }
```

```bash
curl -s --config .cogover-session.curl "$DEMO_BASE/secret-check" \
  -H 'x-req-type: 9' -H 'x-req-service: 3'
```

```json
{ "configured": true }
```

Không đưa `.cogover-session.curl` vào Git. `httpbin.org/bearer` kiểm tra có header Bearer; nó không xác thực token với một tài khoản.

## 6. Xoay giá trị và thử giới hạn host

Cập nhật credential hiện có. Nhập `demo-token-v2` tại ô nhập ẩn:

```bash
cogover-dev secrets set demo_api
cogover-dev secrets list
```

Loại credential và host được phép giữ nguyên; value version tăng lên. Gọi lại `/credential-check`: route vẫn thành công, không cần build, publish hay activate. Metadata xác nhận đã cập nhật; endpoint kiểm thử công khai này không chứng minh token cụ thể nào đã được dùng.

Tiếp theo, thay host được phép. Nhập lại cùng token thử nghiệm khi được hỏi:

```bash
cogover-dev secrets set demo_api --allowed-host example.com
```

Gọi lại `/credential-check`. Kết quả là lỗi `FETCH_BLOCKED`: `httpbin.org` không còn được phép, nên Cogover chặn trước khi gửi request. Khôi phục host và nhập lại token thử nghiệm:

```bash
cogover-dev secrets set demo_api --allowed-host httpbin.org
```

Sau khi thử xong, xóa các mục demo và file session. Mỗi lệnh xóa sẽ yêu cầu xác nhận:

```bash
cogover-dev secrets delete demo_api
cogover-dev secrets delete demo_secret
rm -f .cogover-session.curl
```

## Chọn loại secret

| Loại | Giá trị lưu | Cách dùng trong code |
|---|---|---|
| `BEARER` | Token | `fetch(url, { credential: "name" })` thêm `Authorization: Bearer ...`. |
| `BASIC` | `user:password` | Cùng tùy chọn `fetch` thêm header Basic đã encode. |
| `HEADER` | Giá trị header, kèm tên header được cấu hình | Cùng tùy chọn `fetch` thêm header như `X-Api-Key`. |
| `OPAQUE` | Chuỗi code cần đọc hoặc khóa ký | `secrets.get("name")`, hoặc HMAC với `{ secret: "name" }`. |

Dùng credential khi thông tin xác thực nằm trong HTTP header. Dùng opaque secret khi dịch vụ yêu cầu giá trị trong body hoặc định dạng khác mà credential không biểu diễn được. Với HMAC, truyền trực tiếp tên secret:

```typescript
const signature = await crypto.hmacSha256({ secret: "partner_signing_key" }, body);
```

Code chỉ nhận chữ ký, không nhận giá trị khóa. `secrets.get` và HMAC dùng secret đều từ chối các mục `BEARER`, `BASIC`, `HEADER`.

Để tạo các loại credential khác, chạy lệnh dưới đây rồi nhập giá trị tại ô nhập ẩn. Thay host minh họa bằng host dịch vụ bạn dùng:

```bash
cogover-dev secrets set partner_api --kind basic --allowed-host api.partner.example
cogover-dev secrets set gateway_api --kind header --header-name X-Api-Key --allowed-host api.gateway.example
```

### Host và request gửi ra ngoài

Credential cần danh sách host được phép không rỗng. Host cụ thể như `api.example.com` chỉ cho phép host đó; `*.example.com` cho phép các tên miền con, không gồm `example.com`. Lặp `--allowed-host` để cho phép nhiều host. Khi cập nhật, danh sách truyền vào thay thế danh sách cũ.

`fetch` nhận URL HTTPS công khai trên cổng 443 và không theo redirect. Khi dùng credential, không tự đặt `authorization` hoặc header trùng với header đã cấu hình. Body của request phải là chuỗi, thường được tạo bằng `JSON.stringify`.

Giá trị credential được gửi đến dịch vụ ngoài đã cho phép; dịch vụ đó có thể trả lại nó trong response. Chỉ trả những field người gọi cần, như ví dụ trên. Không ghi log toàn bộ response của dịch vụ ngoài hay sao chép nó vào record. Opaque secret không có giới hạn host sau khi code đã đọc giá trị.

`401` hoặc `500` từ dịch vụ ngoài là response bình thường của `fetch`: kiểm tra `response.ok` và `response.status`. Timeout không chứng minh thao tác ghi đã thất bại; dùng cơ chế chống xử lý trùng của dịch vụ trước khi thử ghi lại.

### Tên, giá trị và quyền sử dụng

Tên bắt đầu bằng chữ cái, chứa tối đa 64 chữ cái, chữ số hoặc dấu gạch dưới. Giá trị tối đa 8 KiB; giá trị credential phải nằm trên một dòng. Cùng tên ở hai Project hoặc Workspace có thể chứa giá trị khác nhau, nên source code dùng được cùng tên giữa các môi trường.

Route, trigger after-change, job và inbound handler được dùng secret. Trigger before-change không được đọc secret hay gọi `fetch`. Development Session mặc định từ chối secret, kể cả `fetch` có credential và HMAC với `{ secret }`; hãy thử trên version đã publish nếu quản trị viên chưa bật quyền dùng local.

Mỗi invocation được tối đa 20 thao tác `secrets.get` hoặc HMAC dùng secret. Gọi lại cùng tên vẫn tính vào giới hạn. Đọc opaque secret một lần trước vòng lặp. Giá trị đã đọc được cache trong invocation đó; sau khi xoay, invocation tiếp theo đọc giá trị mới. Secret thuộc Project, không thuộc từng người gọi, nên cần giới hạn những việc route cho phép người gọi thực hiện với nó.

### Xoay giá trị và quản lý

Với dịch vụ thật, tạo token mới trong khi token cũ còn dùng được, cập nhật credential theo tên hiện có, gọi thử rồi thu hồi token cũ ở nhà cung cấp. Tránh xóa và tạo lại credential khi xoay vì các lời gọi giữa hai bước sẽ không tìm thấy nó.

`secrets set` luôn gửi giá trị và tăng `valueVersion` khi cập nhật. Thiết lập không truyền vào được giữ nguyên. Trong script hoặc CI, dùng `--value-stdin` hay `--value-file`; không có tùy chọn truyền giá trị trực tiếp trên dòng lệnh. `list --json` chỉ trả metadata, còn `delete --yes` bỏ qua bước xác nhận tương tác.

Management API còn cho phép tắt một mục bằng `status: "DISABLED"` hoặc sửa metadata mà không gửi giá trị mới. Mục đã tắt có thể bật lại; xóa thì không khôi phục được. Đổi loại cần giá trị mới, nên credential đang lưu không thể trở thành mục đọc được mà giữ nguyên giá trị cũ. Xem [API quản lý secret](custom-backend-module-api-reference.md#secret).

## Xử lý sự cố

| Vấn đề | Cần kiểm tra |
|---|---|
| `SECRETS_DISABLED` | Nhờ quản trị viên bật secrets cho Workspace. |
| `SECRETS_NOT_ALLOWED` hoặc credential bị từ chối khi chạy local | Thử trên version đã publish, hoặc nhờ quản trị viên cấp quyền dùng secret ở local. |
| Secret không khả dụng | Kiểm tra đúng Project, tên và trạng thái `ACTIVE` trong `cogover-dev secrets list`. |
| Không đọc được credential | Dùng `fetch` với `credential`; chỉ dùng `OPAQUE` khi code cần giá trị. |
| `FETCH_BLOCKED` | Host được phép, loại credential đang active và header xác thực bị trùng. |
| Dịch vụ ngoài trả `401` | Token hết hạn, sai giá trị hoặc sai kiểu xác thực. |
| `FETCH_TIMEOUT` hoặc `FETCH_FAILED` | Kiểm tra dịch vụ ngoài và mạng; dịch vụ demo công khai có thể không khả dụng. |
| Vượt giới hạn invocation | Giảm số thao tác secret; không đọc lặp lại secret trong vòng lặp. |
| Management API trả `403` | Dùng tài khoản Workspace SuperAdmin; Project key không đủ quyền. |
| Session trả `401` | Tạo lại bằng `cogover-dev auth session` và dùng file session mới. |

## Đọc thêm

- [API secrets và credentials của SDK](cogover-sdk-api-reference.md#secret-và-credential) và [outbound HTTP](cogover-sdk-api-reference.md#outbound-http-fetch): đầy đủ quy tắc API.
- [Crypto](get-started-crypto.md): HMAC bằng khóa ký đã lưu.
- [Inbound webhook](get-started-inbound-webhooks.md): xác thực hệ thống ngoài gọi vào Project.
- [Background job](get-started-background-jobs.md): thử lại lời gọi dịch vụ ngoài mà không giữ HTTP request chờ.
