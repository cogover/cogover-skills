# Bắt đầu với Custom Frontend Module

Hướng dẫn tạo một trang TypeScript đơn giản bằng Vite, build thành static asset, publish và mở trang đó trong Cogover. Yêu cầu Node.js 20 trở lên và quyền tạo, publish Custom Frontend Module trong Workspace.

## 1. Tạo project frontend

```bash
npm create vite@latest hello-frontend -- --template vanilla-ts
cd hello-frontend
npm install
```

Tạo `vite.config.ts` với `base: "./"`; bắt buộc vì module được phục vụ dưới `slugSlot` như `/_cm_1/`:

```typescript
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
});
```

## 2. Viết sample đầu tiên

Thay nội dung `src/main.ts` (giữ hoặc tự viết `src/style.css` của template):

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

Chạy local bằng `npm run dev`.

## 3. Build và đóng gói

```bash
npm run build
zip -r hello-frontend.zip dist
```

Archive phải có layout `dist/index.html` và `dist/assets/`; không đặt `index.html` trực tiếp ở root. Không đưa source, `node_modules`, source map hoặc secret vào ZIP: mọi mã frontend đều có thể được người dùng xem trong trình duyệt.

## 4. Upload lên Cogover

Dùng giao diện hoặc Cogover Dev CLI; cả hai đều publish một version mới rồi activate version đó, chỉ cần chọn một cách.

### Cách 1: Thủ công bằng giao diện

Trong màn hình quản lý Custom Module:

1. Tạo **Custom Frontend Module** với name `Hello frontend` và slug `hello_frontend`; đã có Project thì mở Project đó thay vì tạo lại.
2. Tạo version mới và upload `hello-frontend.zip` ở chế độ private.
3. Chờ version chuyển thành `READY`, sau đó activate version.
4. Ghi lại `slugSlot` được Cogover cấp, ví dụ `_cm_1`.

### Cách 2: Dùng Cogover Dev CLI

Dùng Cogover Dev CLI mới nhất và **Workspace API key** có quyền quản lý Custom Frontend Module (lấy từ quản trị viên Workspace). Không cần Project key hay chạy `cogover-dev login`; Workspace API key khác với Project key dùng để phát triển backend local.

```bash
npm install --global @cogover/dev-cli
cogover-dev --version
```

CLI chỉ publish/activate Project đã tồn tại, không tạo Project mới: tạo Custom Frontend Module trên giao diện như cách 1 nếu chưa có, rồi ghi lại Project ID và `slugSlot`; đã được cung cấp Project ID thì dùng trực tiếp ID đó. Tại thư mục `hello-frontend` chứa `package.json`, tạo `cogover.json`:

```json
{
  "version": 1,
  "runtimeUrl": "https://<WORKSPACE_DOMAIN>",
  "projectId": "<FRONTEND_PROJECT_ID>",
  "projectType": "frontend"
}
```

`<WORKSPACE_DOMAIN>` là hostname đầy đủ (ví dụ `example.cogover.net`), `<FRONTEND_PROJECT_ID>` là Project ID dạng `FEP...`. Phải đặt `"projectType": "frontend"`; nếu bỏ qua, CLI mặc định dùng backend. `slugSlot` như `_cm_1` chỉ dùng để mở trang ở mục 5, không phải Project ID hay project slug và không cần đưa vào cấu hình này.

CLI tìm `COGOVER_API_KEY` trong `.env` của Project, rồi credential store của hệ điều hành; chưa có thì hỏi qua prompt ẩn và sau khi xác thực lưu vào native store nếu có, không thì lưu vào `.env` và thêm file này vào `.gitignore`. Docker hoặc CI không có terminal tương tác: cung cấp trước file `.env` riêng tư chứa `COGOVER_API_KEY` ở thư mục Project. Không commit, đưa vào ZIP hoặc chia sẻ key/file này.

Sau khi build ở mục 3, chạy:

```bash
cogover-dev publish
```

CLI yêu cầu `dist/index.html`, tự ZIP thư mục `dist/`, upload ở chế độ private, tạo version và chờ `READY` hoặc `FAILED`. CLI không chạy build: khi thay đổi source, chạy lại `npm run build` trước khi publish. ZIP do CLI tự tạo được xóa sau khi lệnh kết thúc, còn thư mục `dist/` được giữ nguyên; dùng cách này thì có thể bỏ qua lệnh `zip` ở mục 3. Đã tạo ZIP ở mục 3 thì có thể dùng `cogover-dev publish hello-frontend.zip` (file vẫn phải có layout `dist/index.html` và không bị CLI xóa); không chạy cả hai lệnh publish nếu chỉ muốn tạo một version.

Khi publish thành công, CLI in version ID dạng `FEV...` cùng lệnh activate. Chạy đúng version ID vừa nhận, không dùng Project ID `FEP...`:

```bash
cogover-dev activate <VERSION_ID>
```

CLI kiểm tra version thuộc đúng frontend Project và đang `READY` trước khi activate. Nếu publish báo `FAILED`, đọc lỗi, sửa source, build rồi publish version mới; không activate version lỗi. Sau khi activate thành công, dùng `slugSlot` của Project để mở module ở mục 5. Publish/activate bằng CLI không tự đăng nhập Workspace cho trình duyệt.

## 5. Test module đã deploy

Đăng nhập Workspace trên trình duyệt và mở `https://<WORKSPACE_DOMAIN>/<SLUG_SLOT>/index.html`, ví dụ `https://tenant.example.com/_cm_1/index.html`.

Cogover không tự fallback về `index.html` cho SPA: nếu dùng client-side routing, dùng hash routing hoặc bảo đảm thao tác refresh không phụ thuộc vào server fallback. Dùng tên file có content hash để tránh cache asset cũ sau khi activate version mới.

## Sample project hoàn chỉnh

[cogover/get-started-custom-frontend-module](https://github.com/cogover/get-started-custom-frontend-module) là phiên bản hoàn chỉnh của sample trong bài, gồm source TypeScript, cấu hình Vite và test trên trình duyệt. Làm theo README trong repo để chạy local, build và deploy bằng giao diện hoặc CLI; khi deploy, dùng Workspace, Project ID và `slugSlot` đang triển khai. Repo chỉ chứa cấu hình mẫu, không chứa credential.
