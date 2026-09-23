# Bắt đầu với crypto

Băm một thông điệp, ký bằng HMAC-SHA256 rồi kiểm tra chữ ký. Ví dụ cũng tạo byte ngẫu nhiên và UUID. Bạn có thể chạy mà không cần tạo Object.

## Chuẩn bị

- Cài Node.js 20 trở lên, Git và `curl`.
- Có quyền tạo, publish, activate Custom Backend Module và Workspace API key để dùng CLI.
- Bước tùy chọn dùng Project secret cần Workspace đã bật secrets và API key của Workspace SuperAdmin.

Nếu chưa quen việc tạo Project, xem [Bắt đầu với Custom Backend Module](get-started-custom-backend-module.md).

## 1. Tạo Project

Trong Cogover, mở **Custom Backend Module**, tạo Project tên `Crypto demo` với slug `crypto_demo`. Sao chép Project ID, rồi chạy:

```bash
git clone https://github.com/cogover/custom-backend-module-starter-project.git crypto-demo
cd crypto-demo
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
  "projectSlug": "crypto_demo"
}
```

Tạo `.env` trong thư mục này với Workspace API key của bạn:

```dotenv
COGOVER_API_KEY={WORKSPACE_API_KEY}
```

Starter đã bỏ qua `.env` và `cogover.json` trong Git. Không đặt khóa trong source code. Chạy các lệnh còn lại từ thư mục này.

## 2. Viết route

Tạo `src/main.ts`. `demo-key` là giá trị thử nghiệm công khai; bước 6 thay nó bằng Project secret.

```typescript
import { createRouter, ValidationError } from "@cogover/sdk";

const SIGNING_KEY = "demo-key";
const router = createRouter();

function readText(body: unknown): string {
  const text = (body as { text?: unknown } | null)?.text;
  if (typeof text !== "string" || text.length > 2000) {
    throw new ValidationError("text must be a string of at most 2000 characters");
  }
  return text;
}

router.post("/hash", async ({ request, crypto }) => {
  const text = readText(request.body);
  return {
    hex: await crypto.sha256(text),
    base64: await crypto.sha256(text, "base64"),
  };
});

router.post("/sign", async ({ request, crypto }) => ({
  signature: await crypto.hmacSha256(SIGNING_KEY, readText(request.body)),
}));

router.post("/verify", async ({ request, crypto }) => {
  const text = readText(request.body);
  const signature = (request.body as { signature?: unknown }).signature;
  if (typeof signature !== "string" || !/^[a-fA-F0-9]{64}$/.test(signature)) {
    return { valid: false };
  }
  const expected = await crypto.hmacSha256(SIGNING_KEY, text);
  return { valid: crypto.timingSafeEqual(expected, signature.toLowerCase()) };
});

router.get("/random", async ({ crypto }) => {
  const bytes = await crypto.randomBytes(32);
  return {
    hex: Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join(""),
    uuid: await crypto.randomUUID(),
  };
});

export default router.toHandler();
```

## 3. Publish và activate

```bash
npm run build
cogover-dev publish
```

Khi CLI báo `READY`, activate bằng version ID vừa được in ra:

```bash
cogover-dev activate {VERSION_ID}
```

Ví dụ không truy cập record nên không cần identity policy cho record. Xuất Workspace session để gọi các route:

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
DEMO_BASE='https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/crypto_demo'
```

Thay `{WORKSPACE_DOMAIN}` trước khi chạy. Không đưa file session vào Git. Khi gọi qua domain Workspace, kết quả của route nằm trong `body` của response.

## 4. Băm và ký thông điệp

```bash
curl -s --config .cogover-session.curl "$DEMO_BASE/hash" \
  -H 'x-req-type: 6' -H 'x-req-service: 3' \
  -H 'Content-Type: application/json' --data '{"text":"hello"}'
```

Kết quả mong đợi trong `body`:

```json
{
  "hex": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
  "base64": "LPJNul+wow4m6DsqxbninhsWHlwfp0JecwQzYpOLmCQ="
}
```

Tiếp theo, ký cùng chuỗi đó:

```bash
curl -s --config .cogover-session.curl "$DEMO_BASE/sign" \
  -H 'x-req-type: 6' -H 'x-req-service: 3' \
  -H 'Content-Type: application/json' --data '{"text":"hello"}'
```

Sao chép `body.signature` vào `{SIGNATURE}` bên dưới:

```bash
curl -s --config .cogover-session.curl "$DEMO_BASE/verify" \
  -H 'x-req-type: 6' -H 'x-req-service: 3' \
  -H 'Content-Type: application/json' \
  --data '{"text":"hello","signature":"{SIGNATURE}"}'
```

Kết quả là `body: {"valid":true}`. Giữ nguyên chữ ký và đổi `hello` thành `hello!`: kết quả thành `false`. Phép băm chỉ cần thông điệp; HMAC còn phụ thuộc vào khóa dùng chung.

## 5. Tạo giá trị ngẫu nhiên

```bash
curl -s --config .cogover-session.curl "$DEMO_BASE/random" \
  -H 'x-req-type: 6' -H 'x-req-service: 3'
```

`body.hex` có 64 ký tự hex, biểu diễn 32 byte ngẫu nhiên. `body.uuid` là UUID phiên bản 4. Gọi lại để nhận giá trị mới. Route chỉ tạo giá trị; nó chưa cấp hay lưu token truy cập.

## 6. Dùng Project secret để ký

Khi tích hợp thật, tạo secret loại opaque. CLI hỏi giá trị và không hiển thị nội dung bạn nhập:

```bash
cogover-dev secrets set partner_signing_key --kind opaque
cogover-dev secrets list
```

Thay khai báo `SIGNING_KEY` trong `src/main.ts` bằng:

```typescript
const SIGNING_KEY = { secret: "partner_signing_key" };
```

```bash
npm run build
cogover-dev publish
cogover-dev activate {NEW_VERSION_ID}
```

Gọi lại `/sign` và `/verify` với chữ ký mới. Cogover dùng secret đã lưu và trả về digest; code không nhận giá trị khóa. Những lần cập nhật secret sau đó không cần publish lại. Giới hạn người được gọi route ký theo nhu cầu của tích hợp.

Sau khi thử xong, xóa `.cogover-session.curl`. Nếu secret chỉ dùng cho ví dụ này, xóa bằng `cogover-dev secrets delete partner_signing_key`; CLI sẽ yêu cầu xác nhận.

## Chọn thao tác phù hợp

| API | Dùng để | Lưu ý |
|---|---|---|
| `sha256(data, encoding?)` | Tạo dấu vân tay nội dung | Mặc định trả hex chữ thường; cũng hỗ trợ `base64`. |
| `hmacSha256(key, data, encoding?)` | Ký hoặc kiểm tra thông điệp bằng khóa dùng chung | Nhận chuỗi, `Uint8Array` hoặc `{ secret: "name" }`. |
| `randomBytes(length)` | Tạo token, nonce khó đoán | Trả `Uint8Array`; nhận từ 1 đến 1.024 byte. |
| `randomUUID()` | Tạo ID để theo dõi yêu cầu | Trả UUID phiên bản 4. Dùng lại cùng ID qua các lần retry. |
| `timingSafeEqual(a, b)` | So sánh chữ ký hoặc hash của token | Đồng bộ; khác giá trị hoặc độ dài thì trả `false`. |
| `aesEncrypt(key, data, options?)` / `aesDecrypt(key, ciphertext, options)` | Mã hóa dữ liệu bằng khóa dùng chung | Mặc định AES-GCM, AES-CBC khi yêu cầu. Cần SDK 0.9.0 trở lên. |
| `rsaEncrypt(publicKey, data, options?)` / `rsaDecrypt(privateKey, ciphertext, options?)` | Mã hóa giá trị nhỏ cho bên giữ cặp khóa | Mặc định RSA-OAEP với SHA-256. Cần SDK 0.9.0 trở lên. |
| `sign(algorithm, privateKey, data, options?)` / `verify(algorithm, publicKey, data, signature, options?)` | Chữ ký khóa công khai, như API ngân hàng hoặc JWT | RSA, RSA-PSS và ECDSA. Cần SDK 0.9.0 trở lên. |

Lấy `crypto` từ context của handler hoặc `import { crypto } from "@cogover/sdk"`. Mọi thao tác trừ `timingSafeEqual` đều cần `await`. Chuỗi được xử lý theo UTF-8; mảng byte được dùng nguyên trạng. Sandbox không cung cấp `Buffer` hay `node:crypto` của Node.js.

### Ký đúng thông điệp được gửi

Khoảng trắng, xuống dòng và thứ tự key JSON đều làm thay đổi digest. Tạo body gửi đi một lần, dùng cùng chuỗi đó để ký và gửi. Khi kiểm tra chữ ký inbound, dùng `request.rawBody`; `JSON.stringify(request.body)` có thể tạo byte khác. Chuẩn hóa theo encoding và định dạng chữ ký của bên gửi trước khi so sánh.

HMAC hợp lệ chứng minh thông điệp khớp với khóa dùng chung; bản thân nó không ngăn gửi lại yêu cầu cũ. Áp dụng quy tắc timestamp và event ID của nhà cung cấp. Nếu cách ký của họ khớp chế độ HMAC có sẵn của Cogover, cấu hình [inbound access](get-started-inbound-webhooks.md) để kiểm tra trước khi handler chạy.

### Token và dấu vân tay nội dung

Với token truy cập, tạo byte ngẫu nhiên, chỉ lưu hash kèm thời hạn và so sánh hash bằng `timingSafeEqual`. Với token dùng một lần, cần kiểm tra và vô hiệu hóa token trong cùng một thao tác, ví dụ xóa state có kiểm tra version, để hai yêu cầu đồng thời không cùng sử dụng được.

Hash nội dung giúp nhận diện dữ liệu trùng, nhưng lưu dấu vân tay và cập nhật record là hai thao tác riêng. Cần có cách khôi phục nếu lỗi xảy ra giữa chúng. SHA-256 thuần không che được giá trị dễ đoán như địa chỉ email và không phải thuật toán lưu mật khẩu. Để giữ bí mật một giá trị, hãy mã hóa bằng `aesEncrypt` hoặc `rsaEncrypt`; [tài liệu tham chiếu mã hoá của SDK](cogover-sdk-api-reference.md#mã-hoá-và-chữ-ký) mô tả khóa, mode và định dạng chữ ký JWT.

### Giới hạn và nơi được dùng

SDK nhận tối đa 256 KiB dữ liệu hoặc byte của khóa truyền trực tiếp mỗi lần gọi. Giới hạn request của runtime có thể từ chối đầu vào nhỏ hơn sau khi encode, đặc biệt với mảng byte. Kiểm tra dữ liệu lớn trên version đã publish; không mặc định máy chủ local áp dụng cùng giới hạn. Băm các digest của từng phần là một cách tính khác với SHA-256 của thông điệp gốc.

Mọi thao tác với khóa truyền trực tiếp, phép băm và tạo số ngẫu nhiên dùng được trong trigger before-change. `{ secret: "name" }` cần secret `OPAQUE` đang active và bị từ chối trong trigger before-change. Development Session mặc định không được đọc secret. Mỗi lần `secrets.get` hoặc thao tác `crypto` dùng secret đều tính vào giới hạn 20 thao tác secret mỗi invocation, kể cả khi đã đọc tên đó trước đó.

## Xử lý sự cố

| Vấn đề | Cần kiểm tra |
|---|---|
| Digest hoặc chữ ký không khớp | Byte đầu vào, khóa, timestamp và encoding phải giống nhau. Dùng `printf '%s'` để không thêm ký tự xuống dòng. |
| `SECRETS_NOT_ALLOWED` khi chạy local | Thử bản dùng Project secret trên Cogover, hoặc dùng khóa demo công khai khi chạy local. |
| Secret không tồn tại hoặc không đọc được | Xem `cogover-dev secrets list`: đúng Project, tên, trạng thái active và loại `OPAQUE`. |
| `TRIGGER_READ_ONLY` | Chuyển việc ký bằng secret sang trigger after-change, route hoặc job. |
| `SECRETS_DISABLED` | Nhờ quản trị viên bật secrets. |
| `ValidationError`, `413` hoặc `422` do vượt giới hạn | Kiểm tra kiểu tham số, số byte và hạn mức invocation; giảm đầu vào. |

Để phát triển local, dùng Project key với `cogover-dev login --profile crypto_demo`, rồi chạy `cogover-dev run --profile crypto_demo -- npm run dev`. Thao tác với khóa truyền trực tiếp vẫn cần Development Session. Project key khác Workspace API key đã dùng ở trên.

## Đọc thêm

- [API crypto của SDK](cogover-sdk-api-reference.md#mã-hoá-và-chữ-ký): kiểu dữ liệu và giới hạn.
- [Secrets và credentials](get-started-secrets-and-credentials.md): lưu và xoay khóa ký.
- [Inbound webhook](get-started-inbound-webhooks.md): xác thực có sẵn và raw body.
- [Background job](get-started-background-jobs.md): retry và chống xử lý trùng khi gọi hệ thống ngoài có chữ ký.
