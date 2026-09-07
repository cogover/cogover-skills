# Bắt đầu với Custom Backend Module

Trong hướng dẫn này, chúng ta sẽ tạo một Project trong tính năng Custom Backend Module. Project nhận `leadId`, đọc một record từ Cogover Object `lead`, cung cấp API HTTP để test trên local, sau đó được upload và activate trên Cogover.

## Yêu cầu

- Node.js 20 trở lên.
- Quyền tạo Project và publish version trong tính năng Custom Backend Module.
- Project key do quản trị viên Workspace cấp.
- Workspace API key do quản trị viên Workspace cấp nếu dùng CLI để publish và
  activate ở mục 8. Đây là credential khác với Project key và không thể dùng
  thay thế lẫn nhau.
- Workspace có Object slug `lead`; tài khoản gắn với Project key có quyền đọc Object này.

## 1. Tạo Project trên Cogover

Mở tính năng **Custom Backend Module** và tạo một Project:

- Name: `Get lead`
- Slug: `get_lead`

Lưu lại `projectId` và `slug` trên trang chi tiết Project. Slug được dùng trong URL gọi Project và không thể đổi sau khi tạo.

Runtime URL chính là HTTPS origin của Workspace:

```text
https://{WORKSPACE_DOMAIN}
```

`WORKSPACE_DOMAIN` là hostname đầy đủ, ví dụ `example.cogover.net`. Không nối thêm path hoặc domain suffix khác.

## 2. Tải và cài đặt starter project

Tải starter project tại [cogover/custom-backend-module-starter-project](https://github.com/cogover/custom-backend-module-starter-project): chọn **Code → Download ZIP**, giải nén và mở terminal tại thư mục chứa `package.json`. Có thể đổi tên thư mục thành `get-lead` để khớp ví dụ bên dưới.

Hoặc, nếu đã cài Git, clone trực tiếp:

```bash
git clone https://github.com/cogover/custom-backend-module-starter-project.git get-lead
cd get-lead
```

Starter hỗ trợ chạy cùng business handler dưới dạng API local và trên Cogover. Starter ban đầu chưa có code sample trong `src/`; chúng ta sẽ tạo `cogover.json` ở bước 3 và các file sample ở bước 4.

Cấu trúc chính sau khi hoàn thành bước 3–4:

```text
get-lead/
├── cogover.example.json
├── cogover.json
├── package.json
├── tsconfig.json
├── local/
│   ├── cli.ts
│   └── local-server.ts
└── src/
    ├── lead-script.ts
    ├── main.ts
    └── workspace.d.ts
```

- `src/` chứa code chạy trên Cogover và là thư mục sẽ được upload.
- `local/` chứa HTTP runner dành riêng cho máy local, không được import từ `src/` và không được upload.
- `cogover.json` chứa metadata Project, không chứa Project key hoặc credential.

Cài Cogover Dev CLI và dependency của starter:

```bash
npm install --global @cogover/dev-cli
cogover-dev --version
npm install
```

Nếu tự dựng starter thay vì tải về, cài các package sau:

```bash
npm install @cogover/sdk
npm install --save-dev typescript tsx nodemon @types/node
```

Các script quan trọng trong `package.json`:

```json
{
  "type": "module",
  "scripts": {
    "prestart": "npm run typecheck",
    "start": "node --import tsx local/cli.ts --entry ./src/main.ts",
    "dev": "nodemon --watch src --watch local --ext ts --signal SIGTERM --exec \"./node_modules/.bin/tsc -p tsconfig.json --noEmit && node --import tsx local/cli.ts --entry ./src/main.ts || exit 1\"",
    "build": "npm run typecheck",
    "typecheck": "tsc -p tsconfig.json --noEmit"
  }
}
```

`npm run dev` typecheck trước khi mở port và tự restart khi file trong `src/` hoặc `local/` thay đổi.

## 3. Cấu hình Project local

Nếu starter chỉ có file mẫu, tạo `cogover.json`:

```bash
cp cogover.example.json cogover.json
```

Cập nhật nội dung bằng thông tin của Project vừa tạo:

```json
{
  "version": 1,
  "runtimeUrl": "https://{WORKSPACE_DOMAIN}",
  "projectId": "{PROJECT_ID}",
  "projectSlug": "{PROJECT_SLUG}"
}
```

Trong hướng dẫn này, `{PROJECT_SLUG}` là `get_lead`. Nên ignore `cogover.json` để tránh commit nhầm metadata môi trường; chỉ commit `cogover.example.json`:

```gitignore
node_modules/
cogover.json
/.env
npm-debug.log*
```

## 4. Viết sample đọc Lead

Tạo `src/workspace.d.ts` để TypeScript hiểu schema được dùng trong sample:

```typescript
declare module "@cogover/sdk" {
  interface WorkspaceObjects {
    lead: {
      name: string;
      first_name: string | null;
      last_name: string;
      status: string | null;
      emails: string[] | null;
    };
  }
}

export {};
```

Tạo `src/lead-script.ts`:

```typescript
import {
  NotFoundError,
  ValidationError,
  type CogoverRecord,
  type ScriptHandler,
  type WorkspaceObjects,
} from "@cogover/sdk";

type LeadFields = WorkspaceObjects["lead"];

interface GetLeadInput {
  leadId: string;
}

interface GetLeadOutput {
  lead: CogoverRecord<LeadFields>;
}

const READ_FIELDS = [
  "name",
  "first_name",
  "last_name",
  "status",
  "emails",
] as const;

function requireLeadId(value: unknown): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new ValidationError("leadId is required");
  }
  return value.trim();
}

export const getLeadHandler: ScriptHandler<GetLeadInput, GetLeadOutput> =
  async ({ input, data, log }) => {
    const leadId = requireLeadId(input?.leadId);
    const lead = await data.object("lead").records.get(leadId, {
      fields: READ_FIELDS,
    });

    if (!lead) throw new NotFoundError("lead", leadId);

    log.info("Lead loaded", { leadId: lead.id });
    return { lead };
  };
```

Tạo `src/main.ts`. Đây là entry point dùng chung cho local runner và Runtime Server:

```typescript
import { createRouter } from "@cogover/sdk";
import { getLeadHandler } from "./lead-script.js";

const router = createRouter();
router.post("/", getLeadHandler);

export default router.toHandler();
```

`records.get()` chỉ yêu cầu 5 field cần hiển thị và trả `null` nếu Lead không tồn tại. Các message do sample trả về luôn dùng tiếng Anh.

## 5. Đăng nhập bằng Cogover Dev CLI

Đăng nhập bằng Project key. CLI yêu cầu nhập key qua prompt và không hiển thị giá trị:

```bash
cogover-dev login --profile {PROJECT_SLUG}
cogover-dev doctor --profile {PROJECT_SLUG}
```

Với Project trong hướng dẫn này:

```bash
cogover-dev login --profile get_lead
cogover-dev doctor --profile get_lead
```

CLI ưu tiên lưu Project key trong credential store của hệ điều hành. Nếu native
credential store không khả dụng, CLI tự tạo hoặc cập nhật `.env` tại thư mục chứa
`cogover.json`, lưu entry riêng cho profile, đặt quyền file hạn chế trên hệ điều
hành hỗ trợ POSIX và thêm `/.env` vào `.gitignore`. Vì vậy, hãy chạy `login` trong
thư mục Project, kiểm tra `.env` vẫn untracked và tuyệt đối không commit hoặc chia
sẻ file này. Không đặt key trong `cogover.json`, source code hoặc command line.

## 6. Start API trên local

Chọn một port chưa được sử dụng và chạy đúng lệnh sau:

```bash
COGOVER_LOCAL_PORT={PORT} cogover-dev run --profile {PROJECT_SLUG} -- npm run dev
```

Ví dụ chạy Project `get_lead` tại port `3100`:

```bash
COGOVER_LOCAL_PORT=3100 cogover-dev run --profile get_lead -- npm run dev
```

Khi thành công, terminal hiển thị URL local tương tự:

```text
Cogover local project server listening at http://127.0.0.1:3100/api/v1/ts-projects/get_lead
```

Không chạy `npm run dev` trực tiếp. `cogover-dev run` tạo Development Session và bridge cần thiết để code local gọi Cogover Data API bằng danh tính của Project key.

## 7. Gọi API local và xem kết quả

Giữ terminal chạy server, mở terminal khác và gọi root route của Project:

```bash
curl -i -X POST \
  'http://127.0.0.1:{PORT}/api/v1/ts-projects/{PROJECT_SLUG}' \
  -H 'Content-Type: application/json' \
  --data '{"leadId":"{LEAD_ID}"}'
```

Ví dụ:

```bash
curl -i -X POST \
  'http://127.0.0.1:3100/api/v1/ts-projects/get_lead' \
  -H 'Content-Type: application/json' \
  --data '{"leadId":"REPLACE_WITH_LEAD_ID"}'
```

API local không cần cookie, CSRF token hoặc `x-req-service`; Cogover Dev CLI đã quản lý Development Session. Response thành công có dạng:

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
```

```json
{
  "lead": {
    "id": "REPLACE_WITH_LEAD_ID",
    "fields": {
      "name": "Nguyen An",
      "first_name": "An",
      "last_name": "Nguyen",
      "status": "new",
      "emails": ["an.nguyen@example.com"]
    },
    "system": {
      "createdAt": 1788023000000,
      "updatedAt": 1788023000000
    }
  }
}
```

Nếu nhận `403`, kiểm tra Project và caller có quyền `RECORD_READ` trên Object `lead` cùng 5 field đã chọn. Nếu nhận `404`, kiểm tra lại `LEAD_ID`.

## 8. Build, đóng gói và upload

Chỉ thực hiện bước này sau khi API local trả kết quả đúng.

Có thể chạy bước kiểm tra local sau trước khi publish:

```bash
npm run build
```

Trong starter này, `npm run build` chỉ typecheck bằng `tsc --noEmit`; lệnh không
tạo file dùng để upload và không bắt buộc đối với `cogover-dev publish`. Nên chạy
lệnh để phát hiện lỗi TypeScript trước khi upload và compile trên Cogover.

Có thể publish và activate bằng Cogover Dev CLI hoặc thao tác bằng tay trên giao
diện quản lý Project.

### Cách 1: Dùng Cogover Dev CLI

Chạy lệnh sau tại thư mục chứa `cogover.json`:

```bash
cogover-dev publish
```

Khi không truyền file, CLI kiểm tra `src/main.ts`, tự tạo ZIP từ toàn bộ thư mục
`src/`, upload file ở chế độ private, tạo version và chờ đến khi version chuyển
sang `READY` hoặc `FAILED`. ZIP tạm luôn được xóa sau khi lệnh kết thúc.

Nếu đã có archive, có thể truyền file đó cho CLI:

```bash
zip -r get-lead.zip src
cogover-dev publish get-lead.zip
```

Archive phải chứa `src/main.ts` tại đúng path. Không đưa `local/`,
`node_modules`, `cogover.json`, `.env`, Project key hoặc Workspace API key vào
ZIP. CLI không xóa file ZIP do người dùng truyền vào.

`publish` và `activate` dùng Workspace API key, tách biệt với Project key của
`login` và `run`. CLI tìm `COGOVER_API_KEY` trong `.env` của Project, sau đó tìm
trong credential store của hệ điều hành, và yêu cầu nhập qua prompt bảo mật nếu
chưa có. Lấy Workspace API key từ quản trị viên Workspace; không truyền key trên
command line hoặc ghi vào source.

Khi version đã `READY`, output của `publish` hiển thị version ID và lệnh activate
tương ứng. Chạy đúng version ID đó:

```bash
cogover-dev activate <VERSION_ID>
```

CLI kiểm tra version thuộc đúng Project trong `cogover.json` và đang ở trạng thái
`READY` trước khi activate.

### Cách 2: Thao tác trên giao diện

Tạo archive trước:

```bash
zip -r get-lead.zip src
```

Trong trang chi tiết Project:

1. Tạo version mới và upload `get-lead.zip` ở chế độ private.
2. Chờ version chuyển thành `READY`. Nếu là `FAILED`, đọc build error, sửa source và upload bằng version mới.
3. Activate version vừa publish.

## 9. Test Project đã deploy

Dùng Preview của Cogover với method `POST`, route `/` và input:

```json
{"leadId":"{LEAD_ID}"}
```

Hoặc gọi active version qua Workspace origin:

```bash
curl -X POST 'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/{PROJECT_SLUG}' \
  -H 'x-req-service: 3' \
  -H 'Content-Type: application/json' \
  -H 'x-csrf-token: {CSRF_TOKEN}' \
  -H 'cookie: HttpSessionId={SESSION_ID}; AuthToken={AUTH_TOKEN}' \
  --data '{"leadId":"{LEAD_ID}"}'
```

Không đưa session, token, Project key hoặc secret vào source code hay repository.

### Lựa chọn bổ sung: Sinh session bằng CLI rồi gọi curl như end-user

Nếu chưa có bộ cookie/header để điền vào mẫu thủ công phía trên, có thể dùng
`cogover-dev auth session` (CLI từ `0.9.0`) để sinh sẵn file cấu hình cho curl.
Đây là cách kiểm thử **production caller**: request gọi active version đã deploy
với phiên người dùng Workspace, không gọi API local và không dùng chế độ Preview.
Không cần chạy `npm run dev` hay đăng nhập bằng Project key cho cách này.

Tại thư mục chứa `cogover.json`, kiểm tra `runtimeUrl` trỏ tới đúng Workspace rồi
chạy:

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
```

CLI dùng **Workspace API key**, không phải Project key ở bước 5. Giống bước 8,
CLI tìm `COGOVER_API_KEY` trong `.env` của Project trước, rồi trong credential
store của hệ điều hành; nếu chưa có, CLI yêu cầu nhập qua prompt ẩn. Workspace
API key phải được cấp cho Workspace cần test.

CLI dùng key gọi `POST /bapi/v1/auth-token` để nhận phiên Web App, rồi ghi vào
file `.cogover-session.curl`:

- Ba cookie: `HttpSessionId`, `XSRF-TOKEN`, `AuthToken`.
- Hai header: `x-csrf-token` và `x-xsrf-token`, cùng bằng cookie `XSRF-TOKEN`.

Vì vậy curl có thể xác thực như một người dùng đã đăng nhập trên Web App mà
không cần sao chép cookie từ trình duyệt. “Giả lập end-user” ở đây là dùng cùng
luồng gọi production; **session vẫn là phiên thật**, với danh tính do Cogover
cấp khi xác thực Workspace API key. Lệnh không cho phép chọn tùy ý một user,
không tự cấp thêm quyền và không bảo đảm danh tính này trùng với caller của
Project key dùng để test local. Muốn kiểm thử quyền của một end-user cụ thể,
cần phiên hợp lệ của chính người đó; không dùng phiên quản trị viên để kết luận
rằng người dùng thông thường cũng có cùng quyền.

Sau khi sinh file, chạy từ cùng thư mục; thay `{WORKSPACE_DOMAIN}` bằng hostname
đúng với `runtimeUrl`, `{PROJECT_SLUG}` bằng slug của Project đã activate và
`{LEAD_ID}` bằng ID Lead cần đọc:

```bash
curl -i --config .cogover-session.curl \
  -X POST 'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/{PROJECT_SLUG}' \
  -H 'x-req-type: 6' \
  -H 'x-req-service: 3' \
  -H 'Content-Type: application/json' \
  --data '{"leadId":"{LEAD_ID}"}'
```

`--config` nạp trọn bộ cookie/header xác thực; không thêm lại các placeholder
cookie/CSRF từ mẫu thủ công.

Với sample này, caller của session phải có quyền đọc Object `lead`, bản ghi và
các field được yêu cầu. Khác với API local ở bước 7, response production được
bọc trong transport envelope và kết quả của handler nằm tại `body`:

```json
{
  "serviceVersion": 1,
  "service": 3,
  "id": 123,
  "type": 6,
  "body": {
    "lead": {
      "id": "REPLACE_WITH_LEAD_ID",
      "fields": {
        "name": "Nguyen An",
        "first_name": "An",
        "last_name": "Nguyen",
        "status": "new",
        "emails": ["an.nguyen@example.com"]
      },
      "system": {
        "createdAt": 1788023000000,
        "updatedAt": 1788023000000
      }
    }
  }
}
```

Các giá trị metadata của envelope chỉ mang tính minh họa và có thể khác theo
request. Nếu nhận `401`, kiểm tra phiên còn hiệu lực và đang gọi đúng Workspace;
nếu nhận `403`, kiểm tra quyền thực tế của caller. Đây là request production
thật, không phải dry-run: nếu thay sample bằng code ghi dữ liệu, thao tác ghi sẽ
tác động dữ liệu thật.

## Sample project hoàn chỉnh

Chúng ta có thể tải hoặc clone [get-started-custom-backend-module](https://github.com/cogover/get-started-custom-backend-module) để tham khảo phiên bản hoàn chỉnh của sample trong bài, gồm source code, local HTTP runner và test.

Đây là sample đã có sẵn code, khác với starter project ở bước 2. Làm theo README trong repo để cài đặt, cấu hình Project đang dùng, chạy thử và deploy; repo không chứa credential hay dữ liệu Workspace thật.
