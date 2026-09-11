# Bắt đầu với Custom Backend Module

Hướng dẫn tạo một Project Custom Backend Module nhận `leadId`, đọc một record từ Cogover Object `lead`, cung cấp API HTTP để test trên local, sau đó upload và activate trên Cogover.

## Yêu cầu

- Node.js 20 trở lên.
- Quyền tạo Project và publish version trong tính năng Custom Backend Module.
- Project key do quản trị viên Workspace cấp; thêm Workspace API key nếu dùng CLI để publish và activate ở mục 8. Hai credential khác nhau, không thể dùng thay thế lẫn nhau.
- Workspace có Object slug `lead`; tài khoản gắn với Project key có quyền đọc Object này.

## 1. Tạo Project trên Cogover

Mở tính năng **Custom Backend Module**, tạo Project với Name `Get lead`, Slug `get_lead`. Lưu `projectId` và `slug` trên trang chi tiết Project; slug dùng trong URL gọi Project và không thể đổi sau khi tạo.

Runtime URL là HTTPS origin của Workspace, `https://{WORKSPACE_DOMAIN}`, với `WORKSPACE_DOMAIN` là hostname đầy đủ (ví dụ `example.cogover.net`); không nối thêm path hoặc domain suffix khác.

## 2. Tải và cài đặt starter project

Tải [cogover/custom-backend-module-starter-project](https://github.com/cogover/custom-backend-module-starter-project) (**Code → Download ZIP**, giải nén, mở terminal tại thư mục chứa `package.json`; có thể đổi tên thư mục thành `get-lead`) hoặc clone:

```bash
git clone https://github.com/cogover/custom-backend-module-starter-project.git get-lead
cd get-lead
```

Starter chạy cùng một business handler dưới dạng API local và trên Cogover; ban đầu chưa có code sample trong `src/`. Cấu trúc sau khi hoàn thành mục 3–4:

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

- `src/`: code chạy trên Cogover, là thư mục sẽ được upload.
- `local/`: HTTP runner dành riêng cho máy local; không được import từ `src/` và không được upload.
- `cogover.json`: metadata Project, không chứa Project key hoặc credential.

Cài Cogover Dev CLI và dependency của starter:

```bash
npm install --global @cogover/dev-cli
cogover-dev --version
npm install
```

Tự dựng starter thay vì tải về thì cài `npm install @cogover/sdk` và `npm install --save-dev typescript tsx nodemon @types/node`. Các script quan trọng trong `package.json`:

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

`cp cogover.example.json cogover.json` rồi điền thông tin của Project vừa tạo (`{PROJECT_SLUG}` trong hướng dẫn này là `get_lead`):

```json
{
  "version": 1,
  "runtimeUrl": "https://{WORKSPACE_DOMAIN}",
  "projectId": "{PROJECT_ID}",
  "projectSlug": "{PROJECT_SLUG}"
}
```

Ignore `cogover.json` để tránh commit nhầm metadata môi trường; chỉ commit `cogover.example.json`:

```gitignore
node_modules/
cogover.json
/.env
npm-debug.log*
```

## 4. Viết sample đọc Lead

`src/workspace.d.ts` để TypeScript hiểu schema dùng trong sample:

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

`src/lead-script.ts`:

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

`src/main.ts`, entry point dùng chung cho local runner và Runtime Server:

```typescript
import { createRouter } from "@cogover/sdk";
import { getLeadHandler } from "./lead-script.js";

const router = createRouter();
router.post("/", getLeadHandler);

export default router.toHandler();
```

`records.get()` chỉ yêu cầu 5 field cần hiển thị và trả `null` nếu Lead không tồn tại. Các message do sample trả về luôn dùng tiếng Anh.

## 5. Đăng nhập bằng Cogover Dev CLI

Đăng nhập bằng Project key; CLI yêu cầu nhập key qua prompt và không hiển thị giá trị:

```bash
cogover-dev login --profile {PROJECT_SLUG}
cogover-dev doctor --profile {PROJECT_SLUG}
```

CLI ưu tiên lưu Project key trong credential store của hệ điều hành. Nếu native credential store không khả dụng, CLI tự tạo hoặc cập nhật `.env` tại thư mục chứa `cogover.json`, lưu entry riêng cho profile, đặt quyền file hạn chế trên POSIX và thêm `/.env` vào `.gitignore`. Vì vậy chạy `login` trong thư mục Project, kiểm tra `.env` vẫn untracked và không commit hoặc chia sẻ file này. Không đặt key trong `cogover.json`, source code hoặc command line.

## 6. Start API trên local

Chọn một port chưa được sử dụng (ví dụ `3100`) và chạy đúng lệnh sau:

```bash
COGOVER_LOCAL_PORT={PORT} cogover-dev run --profile {PROJECT_SLUG} -- npm run dev
```

Khi thành công, terminal hiển thị URL local dạng `Cogover local project server listening at http://127.0.0.1:3100/api/v1/ts-projects/get_lead`.

Không chạy `npm run dev` trực tiếp: `cogover-dev run` tạo Development Session và bridge cần thiết để code local gọi Cogover Data API bằng danh tính của Project key.

## 7. Gọi API local và xem kết quả

Giữ terminal chạy server, mở terminal khác và gọi root route của Project:

```bash
curl -i -X POST \
  'http://127.0.0.1:{PORT}/api/v1/ts-projects/{PROJECT_SLUG}' \
  -H 'Content-Type: application/json' \
  --data '{"leadId":"{LEAD_ID}"}'
```

API local không cần cookie, CSRF token hoặc `x-req-service`; Cogover Dev CLI đã quản lý Development Session. Response thành công có `HTTP/1.1 200 OK`, `Content-Type: application/json; charset=utf-8` và body:

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

`403`: kiểm tra Project và caller có quyền `RECORD_READ` trên Object `lead` cùng 5 field đã chọn. `404`: kiểm tra lại `LEAD_ID`.

## 8. Build, đóng gói và upload

Chỉ thực hiện sau khi API local trả kết quả đúng. Trong starter này, `npm run build` chỉ typecheck bằng `tsc --noEmit`: không tạo file dùng để upload và không bắt buộc đối với `cogover-dev publish`, nhưng nên chạy để phát hiện lỗi TypeScript trước khi upload và compile trên Cogover.

### Cách 1: Dùng Cogover Dev CLI

Chạy tại thư mục chứa `cogover.json`:

```bash
cogover-dev publish
```

Khi không truyền file, CLI kiểm tra `src/main.ts`, tự tạo ZIP từ toàn bộ thư mục `src/`, upload ở chế độ private, tạo version và chờ đến khi version chuyển sang `READY` hoặc `FAILED`; ZIP tạm luôn được xóa sau khi lệnh kết thúc. Đã có archive thì truyền file đó cho CLI (CLI không xóa file ZIP do người dùng truyền vào):

```bash
zip -r get-lead.zip src
cogover-dev publish get-lead.zip
```

Archive phải chứa `src/main.ts` tại đúng path. Không đưa `local/`, `node_modules`, `cogover.json`, `.env`, Project key hoặc Workspace API key vào ZIP.

`publish` và `activate` dùng Workspace API key (lấy từ quản trị viên Workspace), tách biệt với Project key của `login` và `run`; thứ tự tìm `COGOVER_API_KEY` (`.env` của Project, rồi credential store, rồi prompt bảo mật) theo [Cấu hình và credential](cli-session-and-delivery.md#cấu-hình-và-credential). Không truyền key trên command line hoặc ghi vào source.

Khi version đã `READY`, output của `publish` hiển thị version ID và lệnh activate tương ứng. Chạy đúng version ID đó; CLI kiểm tra version thuộc đúng Project trong `cogover.json` và đang ở trạng thái `READY` trước khi activate:

```bash
cogover-dev activate <VERSION_ID>
```

### Cách 2: Thao tác trên giao diện

Tạo archive bằng `zip -r get-lead.zip src`, rồi trong trang chi tiết Project:

1. Tạo version mới và upload `get-lead.zip` ở chế độ private.
2. Chờ version chuyển thành `READY`. Nếu là `FAILED`, đọc build error, sửa source và upload bằng version mới.
3. Activate version vừa publish.

## 9. Test Project đã deploy

Dùng Preview của Cogover với method `POST`, route `/` và input `{"leadId":"{LEAD_ID}"}`, hoặc gọi active version qua Workspace origin:

```bash
curl -X POST 'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/{PROJECT_SLUG}' \
  -H 'x-req-service: 3' \
  -H 'Content-Type: application/json' \
  -H 'x-csrf-token: {CSRF_TOKEN}' \
  -H 'cookie: HttpSessionId={SESSION_ID}; AuthToken={AUTH_TOKEN}' \
  --data '{"leadId":"{LEAD_ID}"}'
```

Không đưa session, token, Project key hoặc secret vào source code hay repository.

### Sinh session bằng CLI rồi gọi curl như end-user

Chưa có bộ cookie/header để điền vào mẫu thủ công trên thì dùng `cogover-dev auth session` (CLI từ `0.9.0`) sinh sẵn file cấu hình cho curl. Đây là cách kiểm thử **production caller**: request gọi active version đã deploy với phiên người dùng Workspace, không gọi API local và không dùng chế độ Preview; không cần chạy `npm run dev` hay đăng nhập bằng Project key.

Tại thư mục chứa `cogover.json`, kiểm tra `runtimeUrl` trỏ tới đúng Workspace rồi chạy:

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
```

CLI dùng **Workspace API key**, không phải Project key ở mục 5 (thứ tự tìm key như mục 8; key phải được cấp cho Workspace cần test), gọi `POST /bapi/v1/auth-token` để nhận phiên Web App rồi ghi vào `.cogover-session.curl` ba cookie `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` cùng hai header `x-csrf-token`, `x-xsrf-token` bằng cookie `XSRF-TOKEN`. Curl nhờ đó xác thực như người dùng đã đăng nhập Web App mà không cần sao chép cookie từ trình duyệt; **session vẫn là phiên thật** với danh tính do Cogover cấp khi xác thực Workspace API key: không chọn được tùy ý user, không tự cấp thêm quyền và không bảo đảm trùng caller của Project key dùng test local. Kiểm thử quyền của một end-user cụ thể cần phiên hợp lệ của chính người đó; không dùng phiên quản trị viên để kết luận người dùng thông thường cũng có cùng quyền.

Chạy từ cùng thư mục; thay `{WORKSPACE_DOMAIN}` bằng hostname đúng với `runtimeUrl`, `{PROJECT_SLUG}` bằng slug của Project đã activate và `{LEAD_ID}` bằng ID Lead cần đọc:

```bash
curl -i --config .cogover-session.curl \
  -X POST 'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/{PROJECT_SLUG}' \
  -H 'x-req-type: 6' \
  -H 'x-req-service: 3' \
  -H 'Content-Type: application/json' \
  --data '{"leadId":"{LEAD_ID}"}'
```

`--config` nạp trọn bộ cookie/header xác thực; không thêm lại các placeholder cookie/CSRF từ mẫu thủ công. Caller của session phải có quyền đọc Object `lead`, bản ghi và các field được yêu cầu. Khác với API local ở mục 7, response production được bọc trong transport envelope và kết quả của handler nằm tại `body` (giá trị metadata của envelope chỉ minh họa, có thể khác theo request):

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

`401`: kiểm tra phiên còn hiệu lực và đang gọi đúng Workspace; `403`: kiểm tra quyền thực tế của caller. Đây là request production thật, không phải dry-run: thay sample bằng code ghi dữ liệu thì thao tác ghi sẽ tác động dữ liệu thật.

## Sample project hoàn chỉnh

[cogover/get-started-custom-backend-module](https://github.com/cogover/get-started-custom-backend-module) là phiên bản hoàn chỉnh của sample trong bài, gồm source code, local HTTP runner và test; đây là sample đã có sẵn code, khác với starter project ở mục 2. Làm theo README trong repo để cài đặt, cấu hình Project đang dùng, chạy thử và deploy; repo không chứa credential hay dữ liệu Workspace thật.
