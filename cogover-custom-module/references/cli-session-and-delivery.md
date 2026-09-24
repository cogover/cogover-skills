# Cogover Dev CLI, session và bàn giao

Tổng hợp từ tài liệu public Cogover Dev CLI và [Backend quick start](get-started-custom-backend-module.md). Package là `@cogover/dev-cli`, executable là **`cogover-dev`**, không phải `cogover-cli`.

## Cấu hình và credential

```bash
npm install --global @cogover/dev-cli
cogover-dev --version
cogover-dev --help
```

Node.js >= 20; lệnh `auth session` có từ CLI `0.9.0`, chạy trigger local từ `0.10.0`, các lệnh `secrets`, `inbound`, `jobs` và `auth logout` từ `0.13.1`, truyền `invocation.user.membership.isSuperAdmin`/`roles` vào script local từ `0.14.0` (giá trị lấy lúc development session bắt đầu, đổi role thì khởi động lại `cogover-dev`), đọc `org` trên local từ `0.14.0`, xếp `notifications.send` và `email.send` là thao tác ghi từ `0.15.0`. Kiểm tra help của bản đang cài trước khi dùng option. Mỗi thư mục backend/frontend có `cogover.json` riêng; CLI tìm cấu hình gần nhất từ thư mục hiện tại lên cha:

```json
{
  "version": 1,
  "runtimeUrl": "https://<WORKSPACE_DOMAIN>",
  "projectId": "<PROJECT_ID>",
  "projectSlug": "<PROJECT_SLUG>",
  "projectType": "backend"
}
```

Frontend đổi `projectType` thành `frontend` và dùng Project ID frontend. Không trộn ID `TSP`/`TSV` backend với `FEP`/`FEV` frontend; slug không phải ID, `slugSlot` không phải slug.

| Thao tác | Credential |
|---|---|
| Backend `login`, `doctor`, `run` | Project key gắn project và caller personnel |
| Backend/frontend `publish`, `activate`, `auth session` | Workspace API key |
| Backend `secrets`, `inbound`, `jobs` | Workspace API key của người dùng có quyền Workspace SuperAdmin; Project key không đủ |
| HTTP `/api/v1/ts-projects/...` | Workspace session, CSRF/XSRF và routing header |
| HTTP `/api/v1/ts-projects/{slug}/hooks/{inboundId}/...` | Inbound key hoặc chữ ký HMAC của inbound access; không session, không routing header |
| HTTP `/bapi/v1/...` | Workspace API key Bearer |

- `publish`/`activate`/`auth session`/`secrets`/`inbound`/`jobs` tìm `COGOVER_API_KEY` trong `.env` của project, rồi native credential store (service `cogover.api-key`, account là hostname Workspace), rồi prompt ẩn nếu chưa có; `auth logout` xoá key đã lưu ở cả hai nơi. Biến môi trường do helper bên ngoài cung cấp không mặc nhiên được CLI đọc như `.env`. Có credential store thì dùng key đã lưu; không ghi đè `.env` có sẵn, không in giá trị để kiểm tra. Khi thực sự cần fallback `.env`: giữ file riêng tư, ignored và ngoài artifact.
- `login --profile <PROFILE>` nhận Project key qua prompt ẩn, ưu tiên native store; không có native store thì CLI dùng entry riêng cho profile trong `.env`, đặt quyền hạn chế và thêm `/.env` vào `.gitignore`. Không truyền raw key qua argv. Không có kênh nhập ẩn phù hợp: chuẩn bị xong cấu hình rồi hướng dẫn bước nhập credential cụ thể, không yêu cầu paste secret vào chat.

## Quản lý Project trước khi có cấu hình local

CLI chỉ publish/activate project đã tồn tại. Khảo sát App và tạo Project/policy/key trước bước khởi tạo local: dùng [$cogover-api-auth](../../cogover-api-auth/SKILL.md) đổi Workspace API key qua `POST /bapi/v1/auth-token`, giữ session trong tiến trình thực hiện request; xác minh Workspace và hạn dùng theo auth reference. Không cần Project key cho thao tác quản lý này.

Mọi request `/api/v1/ts-projects/...` qua Authorization Server gửi `x-req-type: 6` cùng `x-req-service` tương ứng (thiếu `x-req-type: 6` thì service `4` bị Authorization Server xử lý như logout, trả `deletedTokens` và thu hồi phiên, service `3` trả `r: 5000`, service `6` trả `r: 5001`). TS Project management dùng **POST** với service `4`, kể cả đọc/list; không áp method đó cho App/Object API. API trả project/version object trực tiếp không bắt buộc có envelope `r: 0`: kiểm tra đúng HTTP status, shape và ID theo từng reference. Nếu deployment trả transport envelope, kiểm tra lỗi ở cả envelope lẫn body rồi đối chiếu body với contract.

## Lệnh local và publish

Backend cần SDK capability thật:

```bash
cogover-dev login --profile <PROFILE>
cogover-dev doctor --profile <PROFILE>
COGOVER_LOCAL_PORT=<PORT> cogover-dev run --profile <PROFILE> --allow-writes=false -- npm run dev
```

`--allow-writes=false` tạo session chỉ đọc, bắt buộc khi Project key chỉ đọc; test ghi được phép dùng `--allow-writes=true`; không viết `--allow-writes false`. Cả hai vẫn dùng dữ liệu Workspace thật. Session ghi được tạo hiệu ứng thật: ngoài ghi record, state và lock, push message, notification (`notifications.send`) và email (`email.send`) tới người thật trong hoặc ngoài Workspace; session chỉ đọc từ chối tất cả, nhưng vẫn đọc được `org` và `email.senders()`. Local HTTP runner chỉ listen loopback và giữ cùng handler với bản publish.

Build và publish tại đúng thư mục project:

```bash
npm run build
cogover-dev publish
cogover-dev activate <VERSION_ID_FROM_PUBLISH>
```

Backend starter `build` chỉ typecheck; publish tự đóng gói `src/`. Frontend `build` phải sinh `dist/index.html`; CLI tự đóng gói `dist/`, không build hộ. CLI giới hạn ZIP upload 10 MiB, archive tự tạo còn giới hạn 10 MiB uncompressed; server có thể có ràng buộc bổ sung. Publish chờ `READY`/`FAILED`, không tự activate. Archive chỉ có source backend cần thiết hoặc static asset frontend, không có key, session, `.env`, `node_modules`, `local/` hay source map.

## Lệnh secrets, inbound và jobs

Ba nhóm lệnh thao tác trên backend Project của `cogover.json` gần nhất, cần Workspace API key có quyền SuperAdmin và Workspace đã bật tính năng tương ứng (`SECRETS_DISABLED`, `JOBS_DISABLED` thì báo dependency). Cách dùng đầy đủ: [Secrets và credentials quick start](get-started-secrets-and-credentials.md), [Inbound webhook quick start](get-started-inbound-webhooks.md), [Background job quick start](get-started-background-jobs.md).

```bash
cogover-dev secrets set <name> [--kind opaque|bearer|basic|header] [--header-name <Header>] [--allowed-host <host>]... [--value-stdin | --value-file <path>]
cogover-dev secrets list [--json]
cogover-dev secrets delete <name> [--yes]

cogover-dev inbound create <name> [--mode key|hmac] [--route-prefix /hooks/<route>] [--expires-at <ISO-8601>] \
  [--hmac-header <Header> --hmac-prefix <prefix> --hmac-timestamp-header <Header> --hmac-tolerance <seconds> --hmac-encoding hex|base64 --hmac-secret-stdin] [--json]
cogover-dev inbound list [--json]
cogover-dev inbound rotate <inbound-id>
cogover-dev inbound revoke <inbound-id> [--yes]

cogover-dev jobs runs [--job <key>] [--status PENDING|RUNNING|SUCCEEDED|FAILED] [--page <n>] [--page-size <n>] [--json]
cogover-dev jobs run <run-id> [--json]
cogover-dev jobs enqueue <key> [--payload-file <path>] [--delay-ms <n>] [--idempotency-key <key>]
cogover-dev jobs schedules [--json]
```

- Giá trị secret và HMAC secret chỉ đi qua prompt ẩn, stdin hoặc file; không có option truyền giá trị trên dòng lệnh và không in ra. `secrets set` tạo mới hoặc cập nhật giá trị của mục cùng tên (tăng `valueVersion`, giữ thiết lập không truyền); `list` chỉ trả metadata.
- `inbound create` in URL webhook; ở chế độ `key`, `inboundKey` chỉ hiển thị đúng một lần khi create/rotate (dạng JSON với `--json`). Không thu vào tool log, chat hay báo cáo; chuyển cho bên gửi qua kênh an toàn. `revoke` là vĩnh viễn.
- `jobs enqueue` tạo run thật trên version active; `jobs runs`/`jobs run` chỉ trả metadata và kích thước payload, không trả nội dung payload. Thêm `--json` khi cần xử lý kết quả bằng chương trình.

## Tạo session cho cURL

Chạy trong project có `cogover.json` trỏ tới Workspace đích:

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
```

- Luôn dùng `--output` trong tác vụ của agent: không có `--output`, credential xuất ra stdout và không được thu vào tool log/câu trả lời; không dùng shell redirection thay `--output`.
- CLI ghi file mới mode `0600` trên POSIX và thêm rule `.gitignore`; file chứa ba cookie `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` cùng hai header CSRF/XSRF bằng `XSRF-TOKEN`. CLI từ chối ghi đè file đã có, symlink và file tracked: tên đã tồn tại thì chọn tên mới dùng nhất quán ở cURL, hoặc chỉ xóa file session cũ do chính tác vụ tạo khi đã dùng xong.
- File chứa **session thật**, chỉ gửi đến đúng origin đã tạo phiên. Không đính kèm, mở/in nội dung, commit hay đưa vào ZIP; xóa sau khi dùng. CLI không tự refresh file export: tạo file mới trước thời điểm hết hạn CLI báo hoặc khi phiên bị revoke. Auth expiry tính theo giây, khác timestamps project/version tính theo millisecond.
- Session là danh tính do Workspace API key xác thực: không thể chọn tùy ý user và không mặc nhiên trùng caller của Project key. Không kết luận quyền user thường bằng test với phiên admin.

## Mẫu bàn giao backend

Điền domain/slug/route/method và payload thực sự đã kiểm thử. Ví dụ dùng route POST `/lookup`, chỉ hợp lệ khi backend đã đăng ký route đó; request tới root project bỏ toàn bộ `/lookup`, không thêm dấu `/` cuối. Tạo `request.json` theo input schema, không kèm secret.

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
curl --silent --show-error --include \
  --config .cogover-session.curl \
  --request POST 'https://<WORKSPACE_DOMAIN>/api/v1/ts-projects/<PROJECT_SLUG>/lookup' \
  --header 'x-req-type: 6' \
  --header 'x-req-service: 3' \
  --header 'Content-Type: application/json' \
  --data-binary @request.json
```

- Không dùng `--location`, `--verbose` hoặc `--trace` cho request này (chuyển tiếp/lộ credential).
- Routing không nằm trong file export, truyền theo endpoint: `x-req-service` `3` cho production active version, `4` cho quản lý project/version/policy/key, `6` cho preview chính xác version. `x-req-type: 6` bắt buộc với cả ba service và không phải `x-req-service: 6`; request production giữ service `3`.
- Quick start mô tả kết quả production qua transport envelope có `body`; không tự bọc `body` vào request production. Preview dùng envelope riêng gồm `input`, `versionId`, `mode`, `showDebugData` theo Backend API Reference.
- Route ghi dữ liệu: thêm `Idempotency-Key` riêng cho từng thao tác, giữ key khi retry cùng thao tác và dùng key mới cho thao tác khác; ghi rõ mẫu cURL ghi dữ liệu thật và output dự kiến. GET dùng query/params theo contract route, không gửi POST/body mẫu một cách máy móc. Response text/binary: bàn giao cách đọc/lưu đúng content type.
- Bàn giao cả lệnh tạo session và lệnh cURL, không bàn giao file session chứa credential. Backend đã deploy không cần chạy local server hoặc đăng nhập Project key để dùng cURL production.

## Xử lý lỗi và retry

- CLI im lặng chờ credential quá thời hạn hợp lý (ví dụ hơn 60 giây) trong khi đọc key trực tiếp từ native store vẫn thành công: không mặc định key sai. Kiểm tra prompt/credential service; dừng lệnh đang chờ, đọc project/version để xác định có mutation hay chưa, rồi dùng fallback `.env` riêng tư chứa `COGOVER_API_KEY` đúng như CLI hỗ trợ: chuyển key trong tiến trình an toàn, không in secret, không truyền literal key trong shell command; giữ nguyên entry có sẵn, hạn chế quyền file (0600 trên POSIX), bảo đảm Git ignore, không đóng gói file; chỉ dọn entry/file do tác vụ thêm khi kết thúc. Đã có version hoặc trạng thái publish chưa rõ thì theo dõi version đó thay vì publish thêm. Đây là lỗi credential store của môi trường, không phải lý do tắt TLS hoặc xin key mới.
- Python HTTPS client báo thiếu CA nhưng system curl xác minh TLS bình thường: dùng curl hoặc CA bundle phù hợp, không tự tắt TLS toàn cục.
- `401`: đối chiếu origin, hạn phiên và tạo lại phiên; không xin lại Workspace API key trước khi kiểm tra credential đã có.
- `403`: kiểm tra caller, quyền dữ liệu, quyền SuperAdmin cho management/preview, key ceiling và policy snapshot theo thao tác. Không sửa quyền rộng để làm test xanh.
- `409`: đọc project/version/idempotency state; không lặp create/publish vô hạn hoặc thay key để né xung đột chưa rõ.
- `READY` nhưng invocation thất bại: kiểm tra active version, route/method, identity approval, input và SDK capability.
- Timeout hoặc `writesMayHaveCompleted`: đối chiếu bản ghi/hiệu ứng bên ngoài trước retry; HTTP lỗi không bảo đảm chưa ghi. Idempotency không tạo transaction cho nhiều writes.
- HTTP status và mã lỗi body: production trả đúng HTTP status handler đã chọn (`400`, `404`, `409`, `422`...) như local; body lỗi nằm trong `body` của transport envelope, có `r` bằng HTTP status và `code` (ví dụ `NOT_FOUND`, `VALIDATION_ERROR`). Kiểm tra cả HTTP status lẫn `body.code`, không xử lý body lỗi như dữ liệu thành công. Status khác `200` chỉ đi qua production khi body là một JSON object; body text, bytes, mảng hoặc rỗng kèm status khác `200` chưa mang được status, nên response lỗi và custom status dùng JSON object.
- Custom response cũng cần kiểm chứng: `response.json(body, { status })` giữ status trên production như local khi body là JSON object. `response.ok` của HTTP client chưa đủ xác định thành công: kiểm tra thêm contract nghiệp vụ đã định nghĩa sau khi unwrap đúng transport envelope; không coi mọi field tên `ok` hoặc `code` trong dữ liệu bất kỳ là quy tắc lỗi chung.
- Local khác production: kiểm tra SDK/CLI version, caller, mode và response envelope trước khi kết luận lỗi nghiệp vụ.
