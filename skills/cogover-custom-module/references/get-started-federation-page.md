# Tạo Federation Page kiểm tra mã giảm giá

Khác với việc phát triển một Custom Frontend Module độc lập chạy dưới dạng "single page app" (ứng dụng một trang, được mở qua đường dẫn riêng và tự quản lý toàn bộ giao diện của mình), và cũng khác với custom component được nhúng vào layout để giao tiếp hai chiều với biểu mẫu, có những trường hợp bạn chỉ cần một trang riêng hoạt động độc lập nhưng vẫn nằm trong ứng dụng Cogover: trang xuất hiện dưới đường dẫn của ứng dụng và có thể gắn vào menu ứng dụng như một trang bình thường. Với nhu cầu này, bạn phát triển theo dạng **Federation Page**.

Về mặt quản lý, dự án chứa Federation Page vẫn là một Custom Frontend Module trên Workspace; điểm khác nằm ở cách xây dựng và cách Cogover tải trang:

- Trang phải được phát triển trong bộ khung do Cogover cung cấp ([`custom-frontend-module-template`](https://github.com/cogover/custom-frontend-module-template/), xây dựng trên ReactJS) để dùng chung React, bộ component `@cogover/client-sdk` và cơ chế định tuyến (routing) với Cogover.
- Module đóng vai trò remote trong Module Federation và expose ứng dụng của mình qua khóa `./CustomApp`. Ứng dụng Cogover đóng vai trò host: khi người dùng mở đường dẫn dạng `{appSlug}/cN/...`, host tải `CustomApp` từ phiên bản đã publish, còn ứng dụng của bạn tự chọn page theo `path` đã khai báo trong `src/routes.tsx`. Trang không cần expose riêng và không giao tiếp với layout nào.

Bài viết dưới đây đi qua toàn bộ quy trình: chuẩn bị dự án, viết page, khai báo đường dẫn, publish và mở trang trong ứng dụng.

## Yêu cầu

- Node.js 20 trở lên.
- Quyền tạo và publish Custom Frontend Module trong Workspace.

> **Lưu ý cho agent (bổ sung ngoài tài liệu sản phẩm, snapshot ngày `2026-09-15`).** Dạng này bắt buộc dùng template React của Cogover. Trước khi viết bất kỳ dòng code nào, sub-agent frontend phải:
>
> 1. Clone template vào thư mục riêng của project và cài dependency:
>
>    ```bash
>    git clone https://github.com/cogover/custom-frontend-module-template.git <TEN_THU_MUC_PROJECT>
>    cd <TEN_THU_MUC_PROJECT>
>    npm ci
>    ```
>
> 2. Đọc `README.vi.md` (hoặc `README.md`) và **toàn bộ skill trong thư mục `.agents/skills/` của bản đã clone**: `custom-module-foundation` (bắt buộc), `custom-module-api` (khi gọi API hoặc Custom Backend Module), `custom-module-i18n` (khi có đa ngôn ngữ); `custom-module-form-builder` chỉ khi project đồng thời có custom component. Các skill này là nguồn chuẩn cho quy ước code của template (expose, routing, `Link`, asset, API client, i18n, kiểm tra trước bàn giao); nội dung template có thể mới hơn trích dẫn trong tài liệu này. Báo lại cho agent chính các quy tắc ảnh hưởng tới contract hoặc kế hoạch test.
> 3. Giữ nguyên `'./CustomApp': './src/App.tsx'` trong `exposes` và `base: './'` của `vite.config.ts`; không hardcode `_cm_N`; không đưa key/secret vào biến `VITE_*`; `.env.local` chỉ chứa cấu hình workspace local theo `.env.sample` và không commit.
> 4. Trong workflow của `SKILL.md`, Project trên Workspace được tạo ở bước 4 qua API (`POST /api/v1/ts-projects/frontend`) và `slugSlot` lấy từ response; các bước tạo dự án trên giao diện dưới đây là cách thay thế. Chỉ bắt đầu clone và code sau khi người dùng đã xác nhận dạng module theo mục 1A.
> 5. Template chưa cấu hình unit-test runner: bổ sung runner phù hợp (ví dụ Vitest cùng Testing Library) để đạt điều kiện coverage của bước 8; `npm run lint` và `npm run build` phải pass trước khi publish.
> 6. Chạy local bằng `npm run dev` (cổng `5100`) với `.env.local` trỏ tới Workspace test; trang tự chuyển tới đăng nhập Cogover và quay lại localhost, người dùng tự đăng nhập trên trình duyệt, agent không nhập mật khẩu. E2E tự động dùng phiên theo [Xác thực trình duyệt test](frontend-e2e-testing.md#3-xác-thực-trình-duyệt-test) và chỉ chạy local khi đã xác minh luồng chuyển hướng này hoàn tất với phiên đã nạp. Ở standalone `useAppSlug()` trả chuỗi rỗng; mọi điều hướng nội bộ dùng `Link` của template.
> 7. Đường dẫn production là `https://{WORKSPACE_DOMAIN}/{APP_SLUG}/c{N}/{PATH}` với `N` lấy từ `slugSlot` `_cm_{N}` và `{APP_SLUG}` là slug App đã xác minh qua `$app-menu-manager`. Gắn menu theo phần 5.2 bằng giao diện; chỉ dùng API `$app-menu-manager` khi contract của skill đó mô tả loại hành động điều hướng tới trang trong Workspace, không đoán mã hành động.

## 1. Nêu bài toán

Nhân viên cần một trang riêng để kiểm tra mã giảm giá. Người dùng nhập mã, bấm **Kiểm tra** và nhận thông báo mã hợp lệ hoặc không hợp lệ.

Bài viết hướng dẫn tạo Federation Page (trang được tải từ module giao diện tùy chỉnh) chạy trong ứng dụng Cogover. Việc kiểm tra dùng dữ liệu mẫu ngay trong Frontend (phần giao diện), không cần tạo Backend (phần xử lý phía máy chủ).

## 2. Chuẩn bị dự án

### 2.1. Lấy mã nguồn mẫu

Clone (sao chép) repo template [`custom-frontend-module-template`](https://github.com/cogover/custom-frontend-module-template/) về máy. Mở terminal tại thư mục dự án và cài thư viện:

```bash
npm ci
```

Template đã có React, cấu hình Module Federation và thư viện `@cogover/client-sdk`.

Tham khảo skill (hướng dẫn dành cho công cụ hỗ trợ lập trình) `custom-module-foundation` tại `.agents/skills/custom-module-foundation/SKILL.md` để biết các quy tắc về cấu trúc trang, đường dẫn và tài nguyên tĩnh.

### 2.2. Tạo dự án trên Workspace

1. Mở **Module Frontend tùy chỉnh** tại `/settings/custom-project-fe`.
2. Bấm **Tạo dự án**.
3. Nhập tên, ví dụ **Trang kiểm tra mã giảm giá**, rồi bấm **Tạo dự án**.
4. Mở trang chi tiết và ghi lại **Vị trí trên máy chủ**, ví dụ `_cm_1`.

## 3. Viết trang kiểm tra mã

### 3.1. Tạo page

Tạo file `src/pages/PromotionCheckPage.tsx`:

```tsx
import { Button, TextField } from '@cogover/client-sdk';
import '@cogover/client-sdk/styles.css';
import { useState } from 'react';
import cx from 'src/utils/cx';

const promotionCodes = ['SALE10', 'SALE20'];

export default function PromotionCheckPage() {
    const [code, setCode] = useState('');
    const [message, setMessage] = useState('Nhập mã giảm giá để kiểm tra.');

    const handleCheck = () => {
        const normalizedCode = code.trim().toUpperCase();

        if (!normalizedCode) {
            setMessage('Vui lòng nhập mã giảm giá.');
            return;
        }

        setMessage(
            promotionCodes.includes(normalizedCode)
                ? `Mã ${normalizedCode} hợp lệ.`
                : 'Mã giảm giá không hợp lệ.',
        );
    };

    return (
        <main className={cx('w-full p-[1.5rem]', 'bg-background-default text-typo-primary')}>
            <section className={cx('mx-auto flex max-w-[32rem] flex-col gap-[1rem]')}>
                <h1 className={cx('prose-h4')}>Kiểm tra mã giảm giá</h1>
                <p className={cx('prose-body2 text-typo-secondary')}>
                    Nhập mã rồi bấm Kiểm tra để xem mã có hợp lệ không.
                </p>

                <form
                    className={cx('flex flex-col gap-[0.75rem]')}
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleCheck();
                    }}
                >
                    <TextField
                        aria-label='Mã giảm giá'
                        placeholder='Ví dụ: SALE10'
                        value={code}
                        fullWidth
                        onChange={(event) => {
                            setCode(event.target.value);
                            setMessage('Bấm Kiểm tra để kiểm tra mã vừa nhập.');
                        }}
                    />
                    <div>
                        <Button type='submit'>Kiểm tra</Button>
                    </div>
                </form>

                <p role='status' aria-live='polite' className={cx('prose-body2')}>
                    {message}
                </p>
            </section>
        </main>
    );
}
```

Danh sách `promotionCodes` chứa hai mã mẫu `SALE10` và `SALE20`. Khi người dùng bấm **Kiểm tra** hoặc nhấn Enter, trang bỏ khoảng trắng đầu/cuối và chuyển mã sang chữ hoa trước khi kiểm tra.

Trang chỉ thông báo tính hợp lệ của mã; không áp dụng chiết khấu hay cập nhật đơn hàng.

### 3.2. Khai báo đường dẫn

Trong `src/routes.tsx`, thêm khai báo tải page cùng các page đang có:

```tsx
const PromotionCheckPage = lazy(() => import('./pages/PromotionCheckPage'));
```

File mẫu đã import `lazy` từ React. Thêm phần tử sau vào mảng `APP_ROUTES`, giữ các phần tử hiện có:

```tsx
{
    key: 'promotion-check',
    path: 'promotions',
    element: <PromotionCheckPage />,
},
```

`promotions` là đường dẫn tương đối trong module. Không thêm tên Workspace, slug ứng dụng hoặc `c1` vào `path` này; Cogover quản lý phần đường dẫn bên ngoài module.

### 3.3. Giữ cấu hình xuất ứng dụng

Trong `vite.config.ts`, giữ nguyên mapping (ánh xạ) sau trong `exposes`:

```tsx
'./CustomApp': './src/App.tsx',
```

**Không xóa hoặc thay đổi khóa `./CustomApp` và đường dẫn `./src/App.tsx`.** Giữ các expose khác nếu đã có. Không cần thêm expose riêng cho `PromotionCheckPage`: Cogover tải `CustomApp`, sau đó ứng dụng chọn page theo đường dẫn đã khai báo.

Giữ `base: './'` trong cấu hình Vite để tài nguyên được tải đúng theo địa chỉ phục vụ module.

## 4. Phát hành dự án

### 4.1. Kiểm tra và build

Chạy các lệnh sau tại thư mục dự án:

```bash
npx prettier --write src/pages/PromotionCheckPage.tsx src/routes.tsx
npm run lint
npm run build
```

Chờ build (biên dịch) hoàn tất. Kết quả nằm trong thư mục `dist`.

### 4.2. Đóng gói và kích hoạt

Có thể tải lên bằng giao diện hoặc bằng Cogover Dev CLI. Cả hai cách đều publish một phiên bản mới rồi kích hoạt phiên bản đó; chỉ cần chọn một cách.

#### Cách 1: Thủ công bằng giao diện

1. Nén thư mục `dist` thành file ZIP. Các tệp trong ZIP phải nằm dưới `dist/`.
2. Mở trang chi tiết dự án Frontend đã tạo.
3. Tại **Phát hành phiên bản mới**, bấm **Chọn tệp** và chọn file ZIP.
4. Bấm **Tải lên và phát hành**.
5. Chờ phiên bản có trạng thái **Sẵn sàng**, mở menu thao tác của phiên bản đó và chọn **Kích hoạt**.
6. Kiểm tra phiên bản được đánh dấu **Đang dùng**.

Khi sửa code, build lại, tải ZIP mới lên và kích hoạt phiên bản mới để cập nhật trang.

#### Cách 2: Dùng Cogover Dev CLI

Dùng Cogover Dev CLI mới nhất và **Workspace API key** có quyền quản lý Custom Frontend Module. Lấy key từ quản trị viên Workspace. Không cần Project key hay chạy `cogover-dev login`; Workspace API key khác với Project key dùng để phát triển backend local.

```bash
npm install --global @cogover/dev-cli
cogover-dev --version
```

CLI chỉ publish/kích hoạt dự án đã tồn tại, không tạo dự án mới. Mở trang chi tiết dự án đã tạo ở phần 2 và ghi lại Project ID dạng `FEP...`. Nếu đã được cung cấp Project ID, dùng trực tiếp ID đó.

Tại thư mục dự án chứa `package.json`, tạo `cogover.json`:

```json
{
  "version": 1,
  "runtimeUrl": "https://<WORKSPACE_DOMAIN>",
  "projectId": "<FRONTEND_PROJECT_ID>",
  "projectType": "frontend"
}
```

Thay `<WORKSPACE_DOMAIN>` bằng hostname đầy đủ, ví dụ `example.cogover.net`, và `<FRONTEND_PROJECT_ID>` bằng Project ID dạng `FEP...`. Phải đặt `"projectType": "frontend"`; nếu bỏ qua, CLI mặc định dùng backend. **Vị trí trên máy chủ** như `_cm_1` chỉ dùng để xác định đoạn `cN` trong đường dẫn ở phần 5, không phải Project ID hay slug dự án và không cần đưa vào cấu hình này.

CLI tìm `COGOVER_API_KEY` trong `.env` của dự án trước, rồi trong credential store của hệ điều hành. Nếu chưa có, CLI hỏi Workspace API key qua prompt ẩn. Sau khi xác thực thành công, key nhập qua prompt được lưu vào native store nếu có; nếu không, CLI lưu vào `.env` và thêm file này vào `.gitignore`. Trong Docker hoặc CI không có terminal tương tác, cần cung cấp trước file `.env` riêng tư chứa `COGOVER_API_KEY` ở thư mục dự án. Không commit, đưa vào ZIP, hoặc chia sẻ key/file này.

Sau khi build ở mục 4.1, chạy:

```bash
cogover-dev publish
```

CLI yêu cầu `dist/index.html`, tự ZIP thư mục `dist/`, tải lên ở chế độ private, tạo phiên bản và chờ trạng thái `READY` (tương ứng **Sẵn sàng** trên giao diện) hoặc `FAILED`. CLI không chạy build; khi thay đổi source, cần chạy lại `npm run build` trước khi publish. ZIP do CLI tự tạo được xóa sau khi lệnh kết thúc, còn thư mục `dist/` được giữ nguyên. Nếu dùng cách này, không cần nén thủ công thư mục `dist` như bước 1 của cách 1.

Nếu đã tạo ZIP như bước 1 của cách 1, có thể dùng thay thế:

```bash
cogover-dev publish <ZIP_FILE>
```

Thay `<ZIP_FILE>` bằng đường dẫn tới file ZIP đó. File ZIP truyền vào vẫn phải chứa `dist/index.html` với thư mục `dist` được giữ nguyên và không bị CLI xóa. Không chạy cả hai lệnh publish nếu chỉ muốn tạo một phiên bản.

Khi publish thành công, CLI in ID phiên bản dạng `FEV...` cùng lệnh kích hoạt. Chạy đúng ID phiên bản vừa nhận, không dùng Project ID `FEP...`:

```bash
cogover-dev activate <VERSION_ID>
```

CLI kiểm tra phiên bản thuộc đúng dự án frontend và đang `READY` trước khi kích hoạt. Nếu publish báo `FAILED`, đọc lỗi, sửa source, build rồi publish phiên bản mới; không kích hoạt phiên bản lỗi. Sau khi kích hoạt thành công, có thể mở trang chi tiết dự án trên giao diện để kiểm tra phiên bản được đánh dấu **Đang dùng**, rồi tiếp tục phần 5.

Khi sửa code, build lại, chạy lại `cogover-dev publish` rồi kích hoạt phiên bản mới để cập nhật trang.

## 5. Mở trang và kiểm tra

### 5.1. Đường dẫn truy cập

Trang có cấu trúc đường dẫn:

```text
https://{WORKSPACE_DOMAIN}/{APP_SLUG}/c{N}/promotions
```

1. `{WORKSPACE_DOMAIN}` là hostname đầy đủ của Workspace.
2. `{APP_SLUG}` là slug (định danh trong URL) của ứng dụng dùng để mở trang.
3. `c{N}` tương ứng với **Vị trí trên máy chủ** của dự án: `_cm_1` dùng `c1`, `_cm_2` dùng `c2`.
4. `promotions` khớp với `path` đã khai báo trong `src/routes.tsx`.

Ví dụ slug ứng dụng là `sales`, vị trí dự án là `_cm_1`:

```text
https://{WORKSPACE_DOMAIN}/sales/c1/promotions
```

Đăng nhập Workspace rồi mở đường dẫn tương ứng với cấu hình thực tế của bạn.

### 5.2. Gắn trang vào menu ứng dụng

Trong **Quản lý Ứng dụng**, mở ứng dụng muốn gắn trang, vào **Danh sách mục menu** và tạo mục menu mới. Chọn **Điều hướng tới URL**, loại **Tới một trang trong Workspace**, rồi điền đường dẫn trang tương ứng, ví dụ `/sales/c1/promotions`. Hoàn tất cách điều hướng và phân quyền hiển thị theo nhu cầu của ứng dụng.

### 5.3. Thử mã mẫu

| Thao tác | Kết quả mong đợi |
| --- | --- |
| Nhập `SALE10`, bấm **Kiểm tra** | Mã SALE10 hợp lệ |
| Nhập `SALE20`, nhấn Enter | Mã SALE20 hợp lệ |
| Nhập ` sale10 ` | Nhận diện là SALE10 và báo hợp lệ |
| Nhập `INVALID` | Báo mã giảm giá không hợp lệ |
| Để trống hoặc chỉ nhập khoảng trắng | Yêu cầu nhập mã giảm giá |

Việc kiểm tra chạy trực tiếp trong page với danh sách mã mẫu đã khai báo.
