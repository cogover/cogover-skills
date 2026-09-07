# Bắt đầu với Custom Frontend Module

Trong hướng dẫn này, chúng ta sẽ tạo một trang TypeScript đơn giản bằng Vite, build thành static asset, publish và mở trang đó trong Cogover.

## Yêu cầu

- Node.js 20 trở lên.
- Quyền tạo và publish Custom Frontend Module trong Workspace.

## 1. Tạo project frontend

```bash
npm create vite@latest hello-frontend -- --template vanilla-ts
cd hello-frontend
npm install
```

Tạo `vite.config.ts`. `base: "./"` rất quan trọng vì module được phục vụ dưới `slugSlot` như `/_cm_1/`:

```typescript
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
});
```

## 2. Viết sample đầu tiên

Thay nội dung `src/main.ts`:

```typescript
import "./style.css";

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) throw new Error("App root not found");

app.innerHTML = `
  <main class="card">
    <p class="eyebrow">Cogover Custom Module</p>
    <h1>Hello from our first frontend module</h1>
    <p>This page was built with TypeScript and deployed on Cogover.</p>
  </main>
`;
```

Thay nội dung `src/style.css`:

```css
:root {
  font-family: Inter, system-ui, sans-serif;
  color: #172033;
  background: #f4f7fb;
}

body { margin: 0; }

.card {
  max-width: 720px;
  margin: 80px auto;
  padding: 40px;
  border-radius: 20px;
  background: white;
  box-shadow: 0 16px 48px rgb(23 32 51 / 10%);
}

.eyebrow {
  color: #5267df;
  font-weight: 700;
  text-transform: uppercase;
}
```

Chạy local:

```bash
npm run dev
```

## 3. Build và đóng gói

```bash
npm run build
zip -r hello-frontend.zip dist
```

Archive phải có layout sau, không đặt `index.html` trực tiếp ở root:

```text
dist/
├── index.html
└── assets/
```

Không đưa source, `node_modules`, source map hoặc secret vào ZIP. Mọi mã frontend đều có thể được người dùng xem trong trình duyệt.

## 4. Upload lên Cogover

Chúng ta có thể dùng giao diện hoặc Cogover Dev CLI. Cả hai cách đều publish một
version mới rồi activate version đó; chỉ cần chọn một cách.

### Cách 1: Thủ công bằng giao diện

Trong màn hình quản lý Custom Module:

1. Tạo **Custom Frontend Module** với name `Hello frontend` và slug `hello_frontend`. Nếu đã có Project, mở Project đó thay vì tạo lại.
2. Tạo version mới và upload `hello-frontend.zip` ở chế độ private.
3. Chờ version chuyển thành `READY`, sau đó activate version.
4. Ghi lại `slugSlot` được Cogover cấp, ví dụ `_cm_1`.

### Cách 2: Dùng Cogover Dev CLI

Dùng Cogover Dev CLI mới nhất và **Workspace API key** có quyền quản lý Custom
Frontend Module. Lấy key từ quản trị viên Workspace. Không cần Project key hay
chạy `cogover-dev login`; Workspace API key khác với Project key dùng để phát
triển backend local.

```bash
npm install --global @cogover/dev-cli
cogover-dev --version
```

Tạo Custom Frontend Module trên giao diện như cách 1 nếu chưa có, rồi ghi lại
Project ID và `slugSlot`. CLI chỉ publish/activate Project đã tồn tại, không tạo
Project mới. Nếu đã được cung cấp Project ID, dùng trực tiếp ID đó.

Tại thư mục `hello-frontend` chứa `package.json`, tạo `cogover.json`:

```json
{
  "version": 1,
  "runtimeUrl": "https://<WORKSPACE_DOMAIN>",
  "projectId": "<FRONTEND_PROJECT_ID>",
  "projectType": "frontend"
}
```

Thay `<WORKSPACE_DOMAIN>` bằng hostname đầy đủ, ví dụ `example.cogover.net`, và
`<FRONTEND_PROJECT_ID>` bằng Project ID dạng `FEP...`. Phải đặt
`"projectType": "frontend"`; nếu bỏ qua, CLI mặc định dùng backend. `slugSlot`
như `_cm_1` dùng để mở trang ở bước 5, không phải Project ID hay project slug và
không cần đưa vào cấu hình này.

CLI tìm `COGOVER_API_KEY` trong `.env` của Project trước, rồi trong credential
store của hệ điều hành. Nếu chưa có, CLI hỏi Workspace API key qua prompt ẩn.
Sau khi xác thực thành công, key nhập qua prompt được lưu vào native store nếu
có; nếu không, CLI lưu vào `.env` và thêm file này vào `.gitignore`. Trong
Docker hoặc CI không có terminal tương tác, cần cung cấp trước file `.env`
riêng tư chứa `COGOVER_API_KEY` ở thư mục Project. Không commit, đưa vào ZIP,
hoặc chia sẻ key/file này.

Sau khi build ở bước 3, chạy:

```bash
cogover-dev publish
```

CLI yêu cầu `dist/index.html`, tự ZIP thư mục `dist/`, upload ở chế độ private,
tạo version và chờ `READY` hoặc `FAILED`. CLI không chạy build; khi thay đổi
source, cần chạy lại `npm run build` trước khi publish. ZIP do CLI tự tạo được
xóa sau khi lệnh kết thúc, còn thư mục `dist/` được giữ nguyên. Nếu dùng cách
này, có thể bỏ qua lệnh `zip` ở bước 3.

Nếu đã tạo ZIP ở bước 3, có thể dùng thay thế:

```bash
cogover-dev publish hello-frontend.zip
```

File ZIP truyền vào vẫn phải có layout `dist/index.html` như bước 3 và không bị
CLI xóa. Không chạy cả hai lệnh publish nếu chỉ muốn tạo một version.

Khi publish thành công, CLI in version ID dạng `FEV...` cùng lệnh activate.
Chạy đúng version ID vừa nhận, không dùng Project ID `FEP...`:

```bash
cogover-dev activate <VERSION_ID>
```

CLI kiểm tra version thuộc đúng frontend Project và đang `READY` trước khi
activate. Nếu publish báo `FAILED`, đọc lỗi, sửa source, build rồi publish
version mới; không activate version lỗi. Sau khi activate thành công, dùng
`slugSlot` của Project để mở module ở bước 5. Việc publish/activate bằng CLI
không tự đăng nhập Workspace cho trình duyệt.

## 5. Test module đã deploy

Đăng nhập Workspace trên trình duyệt và mở:

```text
https://<WORKSPACE_DOMAIN>/<SLUG_SLOT>/index.html
```

Ví dụ:

```text
https://tenant.example.com/_cm_1/index.html
```

Cogover không tự fallback về `index.html` cho SPA. Nếu dùng client-side routing, hãy dùng hash routing hoặc bảo đảm thao tác refresh không phụ thuộc vào server fallback. Dùng tên file có content hash để tránh cache asset cũ sau khi activate version mới.

## Sample project hoàn chỉnh

Chúng ta có thể tải hoặc clone [get-started-custom-frontend-module](https://github.com/cogover/get-started-custom-frontend-module) để tham khảo phiên bản hoàn chỉnh của sample trong bài, gồm source TypeScript, cấu hình Vite và test trên trình duyệt.

Làm theo README trong repo để chạy local, build và deploy bằng giao diện hoặc CLI. Khi deploy, dùng Workspace, Project ID và `slugSlot` đang triển khai; repo chỉ chứa cấu hình mẫu, không chứa credential.
