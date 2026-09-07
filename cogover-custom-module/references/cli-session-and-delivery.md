# Cogover Dev CLI, session và bàn giao

Hướng dẫn thao tác được tổng hợp từ tài liệu public Cogover Dev CLI và [Backend quick start](get-started-custom-backend-module.md). Package là `@cogover/dev-cli`, executable là **`cogover-dev`**, không phải `cogover-cli`.

## Mục lục

- [Cấu hình và credential](#cấu-hình-và-credential)
- [Quản lý Project trước khi có cấu hình local](#quản-lý-project-trước-khi-có-cấu-hình-local)
- [Lệnh local và publish](#lệnh-local-và-publish)
- [Tạo session cho cURL](#tạo-session-cho-curl)
- [Mẫu bàn giao backend](#mẫu-bàn-giao-backend)
- [Xử lý lỗi và retry](#xử-lý-lỗi-và-retry)

## Cấu hình và credential

```bash
npm install --global @cogover/dev-cli
cogover-dev --version
cogover-dev --help
```

Node.js >= 20; lệnh `auth session` có từ CLI `0.9.0`. Kiểm tra help của bản đang cài trước khi dùng option. Mỗi thư mục backend/frontend có `cogover.json` riêng:

```json
{
  "version": 1,
  "runtimeUrl": "https://<WORKSPACE_DOMAIN>",
  "projectId": "<PROJECT_ID>",
  "projectSlug": "<PROJECT_SLUG>",
  "projectType": "backend"
}
```

Frontend đổi `projectType` thành `frontend` và dùng Project ID frontend. CLI tìm cấu hình gần nhất từ thư mục hiện tại lên cha. Không trộn ID `TSP`/`TSV` backend với `FEP`/`FEV` frontend; slug không phải ID, `slugSlot` không phải slug.

| Thao tác | Credential |
|---|---|
| Backend `login`, `doctor`, `run` | Project key gắn project và caller personnel |
| Backend/frontend `publish`, `activate`, `auth session` | Workspace API key |
| HTTP `/api/v1/ts-projects/...` | Workspace session, CSRF/XSRF và routing header |
| HTTP `/bapi/v1/...` | Workspace API key Bearer |

`publish`/`activate`/`auth session` tìm `COGOVER_API_KEY` trong `.env` của project, rồi native credential store (service `cogover.api-key`, account là hostname Workspace), sau đó prompt ẩn nếu chưa có. Biến môi trường do helper bên ngoài cung cấp không mặc nhiên được CLI đọc như `.env`; theo cơ chế đã tài liệu hóa. Không ghi đè `.env` có sẵn, không in giá trị để kiểm tra. Trong môi trường có sẵn credential store, dùng key đã lưu. Khi thực sự cần fallback `.env`, giữ file riêng tư, ignored và ngoài artifact.

`login --profile <PROFILE>` nhận Project key qua prompt ẩn, ưu tiên native store. Nếu native store không có, CLI dùng entry riêng cho profile trong `.env`, đặt quyền hạn chế và thêm `/.env` vào `.gitignore`. Không truyền raw key qua argv. Nếu không có kênh nhập ẩn phù hợp, chuẩn bị xong cấu hình rồi hướng dẫn bước nhập credential cụ thể; không yêu cầu paste secret vào chat.

## Quản lý Project trước khi có cấu hình local

CLI chỉ publish/activate project đã tồn tại. Để khảo sát App và tạo Project/policy/key trước bước khởi tạo local, dùng [$cogover-api-auth](../../cogover-api-auth/SKILL.md) đổi Workspace API key qua `POST /bapi/v1/auth-token`, giữ session trong tiến trình thực hiện request. Xác minh Workspace và hạn dùng theo auth reference; không cần Project key cho thao tác quản lý này.

TS Project management dùng **POST** với service `4`, kể cả đọc/list; không áp method đó cho App/Object API. Những API trả project/version object trực tiếp không bắt buộc có envelope `r: 0`. Kiểm tra đúng HTTP status, shape và ID theo từng reference. Nếu deployment trả transport envelope, kiểm tra lỗi ở cả envelope lẫn body rồi đối chiếu body với contract.

## Lệnh local và publish

Backend cần SDK capability thật:

```bash
cogover-dev login --profile <PROFILE>
cogover-dev doctor --profile <PROFILE>
COGOVER_LOCAL_PORT=<PORT> cogover-dev run --profile <PROFILE> --allow-writes=false -- npm run dev
```

`--allow-writes=false` tạo session chỉ đọc; test ghi được phép dùng `--allow-writes=true`. Không viết `--allow-writes false`. Cả hai vẫn dùng dữ liệu Workspace thật. Local HTTP runner phải chỉ listen loopback; giữ cùng handler với bản publish.

Build và publish tại đúng thư mục project:

```bash
npm run build
cogover-dev publish
cogover-dev activate <VERSION_ID_FROM_PUBLISH>
```

Backend starter build chỉ typecheck; publish tự đóng gói `src/`. Frontend build phải sinh `dist/index.html`; CLI tự đóng gói `dist/`, không build hộ. CLI giới hạn ZIP upload 10 MiB, archive tự tạo còn giới hạn 10 MiB uncompressed; server có thể có ràng buộc bổ sung. Publish chờ `READY`/`FAILED`, không tự activate. Archive chỉ có source backend cần thiết hoặc static asset frontend, không có key, session, `.env`, `node_modules`, `local/` hay source map.

## Tạo session cho cURL

Chạy trong project có `cogover.json` trỏ tới Workspace đích:

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
```

Luôn dùng `--output` trong tác vụ của agent. Chạy `auth session` không có `--output` sẽ xuất credential ra stdout; không thu output đó vào tool log/câu trả lời. Không dùng shell redirection thay `--output`.

CLI ghi file mới mode `0600` trên POSIX, thêm rule `.gitignore`, chứa ba cookie `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` cùng hai header CSRF/XSRF bằng `XSRF-TOKEN`. CLI từ chối ghi đè file đã có, symlink và file tracked. Nếu tên đã tồn tại, chọn tên mới và dùng nhất quán ở cURL, hoặc chỉ xóa file session cũ do chính tác vụ tạo khi đã dùng xong.

File này chứa **session thật**, chỉ gửi đến đúng origin đã tạo phiên. Không đính kèm, mở/in nội dung, commit hay đưa vào ZIP; xóa sau khi dùng. CLI không tự refresh file export. Tạo file mới trước thời điểm hết hạn CLI báo, hoặc khi phiên bị revoke. Auth expiry tính theo giây, khác timestamps project/version tính theo millisecond.

Session là danh tính do Workspace API key xác thực; không thể chọn tùy ý user và không mặc nhiên trùng caller của Project key. Không kết luận quyền user thường bằng test với phiên admin.

## Mẫu bàn giao backend

Điền domain/slug/route/method và payload thực sự đã kiểm thử. Ví dụ dưới đây dùng route POST `/lookup`; chỉ dùng nếu backend đã đăng ký route tương ứng. Tạo `request.json` theo input schema, không kèm secret. Request tới root project bỏ toàn bộ `/lookup`, không thêm dấu `/` cuối.

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

Không dùng `--location`, `--verbose` hoặc `--trace` cho request này để tránh chuyển tiếp/lộ credential. Routing không nằm trong file export; truyền theo endpoint:

| Mục đích | `x-req-service` |
|---|---:|
| Production active version | `3` |
| Project/version/policy/key management | `4` |
| Preview chính xác version | `6` |

`x-req-type: 6` không phải `x-req-service: 6`. Request production ở trên giữ service `3`. Quick start mô tả kết quả qua transport envelope có `body`; không tự bọc `body` vào request production. Preview dùng envelope riêng gồm `input`, `versionId`, `mode`, `showDebugData` theo Backend API Reference.

Nếu route ghi dữ liệu, thêm `Idempotency-Key` riêng cho thao tác đó. Giữ key khi retry cùng thao tác; dùng key mới cho thao tác khác. Ghi rõ mẫu cURL ghi dữ liệu thật và output dự kiến. Với GET dùng query/params theo contract route; không gửi POST/body mẫu một cách máy móc. Với response text/binary, bàn giao cách đọc/lưu đúng content type.

Bàn giao cả lệnh tạo session và lệnh cURL, không bàn giao file session chứa credential. Backend đã deploy không cần chạy local server hoặc đăng nhập Project key để dùng cURL production.

## Xử lý lỗi và retry

- CLI im lặng chờ credential quá thời hạn hợp lý (ví dụ hơn 60 giây), trong khi đọc key trực tiếp từ native store vẫn thành công: không mặc định key sai. Kiểm tra prompt/credential service; dừng lệnh đang chờ, đọc project/version để xác định có mutation hay chưa, rồi dùng fallback `.env` riêng tư chứa `COGOVER_API_KEY` đúng như CLI hỗ trợ. Chuyển key trong tiến trình an toàn, không in secret và không truyền literal key trong shell command. Giữ nguyên entry có sẵn, hạn chế quyền file (0600 trên POSIX), bảo đảm Git ignore và không đóng gói file; chỉ dọn entry/file do tác vụ thêm khi kết thúc. Nếu đã có version hoặc trạng thái publish chưa rõ, theo dõi version đó thay vì publish thêm. Đây là xử lý lỗi credential store của môi trường, không phải lý do tắt TLS hoặc xin key mới.
- Python HTTPS client báo thiếu CA nhưng system curl xác minh TLS bình thường: dùng curl hoặc CA bundle phù hợp, không tự tắt TLS toàn cục.
- `401`: đối chiếu origin, hạn phiên và tạo lại phiên; không xin lại Workspace API key trước khi kiểm tra credential đã có.
- `403`: kiểm tra caller, quyền dữ liệu, quyền SuperAdmin cho management/preview, key ceiling và policy snapshot theo thao tác. Không sửa quyền rộng để làm test xanh.
- `409`: đọc project/version/idempotency state; không lặp create/publish vô hạn hoặc thay key để né xung đột chưa rõ.
- `READY` nhưng invocation thất bại: kiểm tra active version, route/method, identity approval, input và SDK capability.
- Timeout hoặc `writesMayHaveCompleted`: đối chiếu bản ghi/hiệu ứng bên ngoài trước retry; HTTP lỗi không bảo đảm chưa ghi. Idempotency không tạo transaction cho nhiều writes.
- HTTP status và mã lỗi body không khớp: đã quan sát missing record trả HTTP 400 nhưng transport `body.r: 404`, `body.code: NOT_FOUND`, trong khi local trả HTTP 404. Ghi riêng cả hai lớp, báo khác biệt với public contract; client phải nhận diện đây là lỗi và không xử lý body như dữ liệu thành công. Không suy ra quy tắc đổi mọi HTTP 400 thành 404. Kiểm thử semantic error và HTTP contract riêng; nếu downstream yêu cầu chính xác HTTP status, đánh dấu phần tích hợp đó chưa đạt.
- Custom response cũng cần kiểm chứng: đã quan sát handler yêu cầu HTTP 409 cho preview cũ nhưng production trả HTTP 200 kèm output nghiệp vụ `ok: false`, `code: STALE_PREVIEW`; local trả HTTP 409. `response.ok` của HTTP client chưa đủ xác định thành công. Kiểm tra thêm contract nghiệp vụ đã định nghĩa sau khi unwrap đúng transport envelope; không coi mọi field tên `ok` hoặc `code` trong dữ liệu bất kỳ là quy tắc lỗi chung.
- Local khác production: kiểm tra SDK/CLI version, caller, mode và response envelope trước khi kết luận lỗi nghiệp vụ.
