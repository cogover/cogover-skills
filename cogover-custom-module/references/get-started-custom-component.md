# Tạo custom component kiểm tra mã giảm giá trên đơn hàng

Khác với việc phát triển một Custom Frontend Module độc lập chạy dưới dạng "single page app" (ứng dụng một trang, được mở qua đường dẫn riêng và tự quản lý toàn bộ giao diện của mình), có những trường hợp bạn cần một thành phần giao diện được nhúng ngay trong layout của Cogover và giao tiếp hai chiều với layout đó: layout truyền dữ liệu sang component, component đọc hoặc cập nhật giá trị các field, thao tác trên Related List rồi trả kết quả về cho biểu mẫu,... Với nhu cầu này, bạn cần phát triển theo dạng **custom component** (thành phần giao diện tùy chỉnh).

Về mặt quản lý, dự án chứa custom component vẫn là một Custom Frontend Module trên Workspace; điểm khác nằm ở cách xây dựng và cách sử dụng:

- Component phải được phát triển trong bộ khung do Cogover cung cấp ([`custom-frontend-module-template`](https://github.com/cogover/custom-frontend-module-template/), xây dựng trên ReactJS) để dùng chung React, bộ component `@cogover/client-sdk` và API Form Builder với Cogover.
- Sau khi viết xong, component được khai báo (expose) trong cấu hình build bằng công nghệ Module Federation. Nhờ đó, Cogover layout có thể tải component từ dự án đã publish và hiển thị nó thông qua item **Federation component**.

Bài viết dưới đây đi qua toàn bộ quy trình: chuẩn bị dự án, viết component, expose, publish và đưa component vào layout đơn hàng.

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
> 2. Đọc `README.vi.md` (hoặc `README.md`) và **toàn bộ skill trong thư mục `.agents/skills/` của bản đã clone**: `custom-module-foundation` (bắt buộc), `custom-module-form-builder` (bắt buộc, cùng `src/types/form-builder.d.ts`), `custom-module-api` (khi gọi API hoặc Custom Backend Module), `custom-module-i18n` (khi có đa ngôn ngữ). Các skill này là nguồn chuẩn cho quy ước code của template (expose, routing, `Link`, asset, API client, i18n, kiểm tra trước bàn giao); nội dung template có thể mới hơn trích dẫn trong tài liệu này. Báo lại cho agent chính các quy tắc ảnh hưởng tới contract hoặc kế hoạch test.
> 3. Giữ nguyên `'./CustomApp': './src/App.tsx'` trong `exposes` và `base: './'` của `vite.config.ts`; không hardcode `_cm_N`; không đưa key/secret vào biến `VITE_*`; `.env.local` chỉ chứa cấu hình workspace local theo `.env.sample` và không commit.
> 4. Trong workflow của `SKILL.md`, Project trên Workspace được tạo ở bước 4 qua API (`POST /api/v1/ts-projects/frontend`) và `slugSlot` lấy từ response; các bước tạo dự án trên giao diện dưới đây là cách thay thế. Chỉ bắt đầu clone và code sau khi người dùng đã xác nhận dạng module theo mục 1A.
> 5. Template chưa cấu hình unit-test runner: bổ sung runner phù hợp (ví dụ Vitest cùng Testing Library) để đạt điều kiện coverage của bước 8; `npm run lint` và `npm run build` phải pass trước khi publish.
> 6. Debug component trên form thật trước khi publish: chạy `npm run build-watch` rồi `npm run preview` ở terminal khác; preview in URL dạng `http://localhost:5101/#./Components/<TenComponent>` dưới mục **Federation components**, dán URL đó vào trường URL của item Federation component trên layout test. Chỉ dùng URL localhost khi debug; sau khi publish và activate phải thay bằng `{slugSlot}/Components/<TenComponent>` và không bàn giao layout còn URL localhost.
> 7. Slug dùng trong `execScript` là slug của item trên layout (đọc qua `$object-layout`), không phải slug Object hay Related List; xác minh trước khi code. Trên layout, item **Federation component** là component `fieldType: "federation_component"` với `federationUrl` = `{slugSlot}/Components/<TenComponent>`: thêm bằng `$object-layout` (mục "Đưa Federation component vào layout") hoặc trình sửa layout theo phần 5, rồi view lại layout để xác minh.

## 1. Nêu bài toán

Khi lập đơn hàng, nhân viên cần nhập mã giảm giá và áp dụng mức chiết khấu cho đúng sản phẩm. Thay vì tìm từng dòng và sửa thủ công, người dùng chỉ cần nhập mã rồi bấm **Kiểm tra**.

Nếu mã hợp lệ, các dòng sản phẩm tương ứng sẽ được cập nhật chiết khấu. Nếu mã không hợp lệ hoặc đơn hàng không có sản phẩm phù hợp, biểu mẫu hiển thị thông báo để người dùng biết.

Bài viết hướng dẫn tạo một custom component (thành phần giao diện tùy chỉnh) để thực hiện thao tác này ngay trên đơn hàng.

## 2. Chuẩn bị dự án

### 2.1. Lấy mã nguồn mẫu

Tải hoặc clone (sao chép kho mã nguồn) [`custom-frontend-module-template`](https://github.com/cogover/custom-frontend-module-template/) do Cogover cung cấp. Mở terminal (cửa sổ dòng lệnh) tại thư mục dự án và cài các thư viện:

```bash
npm install
```

Template đã có React, cấu hình build (biên dịch), `@cogover/client-sdk` và kiểu dữ liệu Form Builder.

### 2.2. Tạo dự án trên Workspace

1. Đăng nhập Workspace và mở đường dẫn `/settings/custom-project-fe`.
2. Bấm **Tạo dự án**.
3. Nhập tên, ví dụ **Kiểm tra mã giảm giá**; kiểm tra slug được tạo tự động và bổ sung mô tả nếu cần.
4. Bấm **Tạo dự án**, sau đó mở trang chi tiết.
5. Ghi lại **Vị trí trên máy chủ**, ví dụ `_cm_1`, để cấu hình đường dẫn component ở phần 5.

### 2.3. Chuẩn bị các field và item trên layout

Ví dụ dùng cấu hình sau:

| Thành phần | Giá trị minh họa |
|---|---|
| Object đơn hàng | `order` |
| Object dòng sản phẩm | `order_product_line` |
| Slug item Related List trong layout đơn hàng | `order_product_lines` |
| Field sản phẩm trong dòng | `product`, lookup đơn tới sản phẩm |
| Field chiết khấu trong dòng | `discount_percent`, kiểu phần trăm |

Trong trang sửa layout, chọn item Related List (thành phần bảng liên quan) và xem slug của item đó. **Code phải dùng slug của item Related List trong layout, không phải slug của Related List hay Object liên kết.**

Field `discount_percent` cần cho phép chỉnh sửa. Trong ví dụ, giá trị ô `10` tương ứng 10% trên form; kiểm tra quy ước của field bạn sử dụng trước khi thay cấu hình.

## 3. Thực hiện code

### 3.1. Tạo component

Trong bài này, việc kiểm tra mã được **mô phỏng bằng dữ liệu cố định** trong component để bạn dễ thực hành. Thực tế, bạn có thể tạo một dự án Custom Backend (mô-đun xử lý phía máy chủ) để viết nghiệp vụ kiểm tra mã, hoặc gọi API (giao diện trao đổi dữ liệu) của hệ thống khác. Khi đó, thay phần tìm mã trong danh sách bằng lời gọi API để nhận sản phẩm và phần trăm chiết khấu.

Tạo file `src/components/PromotionCodeChecker.tsx` với nội dung sau. Kiểu `FormBuilderComponentProps` đã có trong `src/types/form-builder.d.ts`, không cần khai báo lại.

```tsx
import { Button, TextField } from '@cogover/client-sdk';
import '@cogover/client-sdk/styles.css';
import { useState } from 'react';
import type { FormBuilderComponentProps } from 'src/types/form-builder';
import cx from 'src/utils/cx';

const promotions = [
    { code: 'SALE10', product_id: 'PRODUCT_A_ID', discount_percent: 10 },
    { code: 'SALE20', product_id: 'PRODUCT_B_ID', discount_percent: 20 },
];

type Promotion = (typeof promotions)[number];

export default function PromotionCodeChecker({ formBuilder }: FormBuilderComponentProps) {
    const [code, setCode] = useState('');
    const [message, setMessage] = useState('Nhập mã khuyến mãi để kiểm tra.');
    const [isChecking, setIsChecking] = useState(false);

    const applyPromotion = async (promotion: Promotion) => {
        if (!formBuilder?.execScript) {
            throw new Error('Hãy mở component trong biểu mẫu đơn hàng.');
        }

        let matchedRows = 0;
        await formBuilder.execScript(async ({ screen }) => {
            const lines = screen.get('order_product_lines', 'RELATED_LIST');
            if (!lines?.rows) throw new Error('Không tìm thấy danh sách sản phẩm.');

            for (const row of await lines.rows()) {
                const productCell = row.get('product');
                if (productCell?.value === promotion.product_id) {
                    const discountCell = row.get('discount_percent');
                    if (!discountCell) {
                        throw new Error('Không tìm thấy ô chiết khấu của sản phẩm.');
                    }
                    if (discountCell.value !== promotion.discount_percent) {
                        discountCell.value = promotion.discount_percent;
                    }
                    matchedRows += 1;
                }
            }
        });
        return matchedRows;
    };

    const handleCheckPromotion = async () => {
        const promotionCode = code.trim().toUpperCase();
        if (!promotionCode || !formBuilder?.execScript) {
            setMessage('Vui lòng nhập mã khuyến mãi trong Form Builder.');
            return;
        }

        setIsChecking(true);
        try {
            // Giả lập kiểm tra mã; thay phần này bằng lời gọi API khi cần.
            const promotion = promotions.find((item) => item.code === promotionCode);
            if (!promotion) {
                setMessage('Mã khuyến mãi không hợp lệ.');
            } else {
                const matchedRows = await applyPromotion(promotion);
                if (matchedRows === 0) {
                    setMessage('Không có dòng sản phẩm phù hợp với mã khuyến mãi.');
                } else {
                    setMessage(`Đã áp dụng mã ${promotionCode} cho ${matchedRows} dòng. Hãy lưu bảng để ghi nhận.`);
                }
            }
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Không kiểm tra được mã khuyến mãi.');
        } finally {
            setIsChecking(false);
        }
    };

    return (
        <section
            className={cx(
                'flex w-full max-w-[28rem] flex-col gap-[1rem] rounded-[1rem]',
                'border border-divider-primary bg-background-default p-[1.5rem] shadow-secondary',
            )}
        >
            <div>
                <h2 className={cx('prose-h6 text-typo-primary')}>Mã khuyến mãi</h2>
                <p className={cx('mt-[0.25rem] prose-body2 text-typo-secondary')}>
                    Kiểm tra mã và áp dụng chiết khấu cho sản phẩm tương ứng trong đơn hàng.
                </p>
            </div>

            <div className={cx('flex items-center gap-[0.5rem]')}>
                <TextField
                    aria-label='Mã khuyến mãi'
                    value={code}
                    fullWidth
                    disabled={isChecking}
                    placeholder='Mã khuyến mãi'
                    onChange={(event) => setCode(event.target.value)}
                    onKeyDown={(event) => {
                        if (event.key === 'Enter') {
                            event.preventDefault();
                            if (!isChecking) void handleCheckPromotion();
                        }
                    }}
                />

                <Button
                    type='button'
                    loading={isChecking}
                    disabled={isChecking || !formBuilder?.execScript || !code.trim()}
                    onClick={() => void handleCheckPromotion()}
                >
                    Kiểm tra
                </Button>
            </div>

            <p role='status' aria-live='polite' className={cx('prose-body2 text-typo-secondary')}>
                {message}
            </p>
        </section>
    );
}
```

Thay `PRODUCT_A_ID`, `PRODUCT_B_ID` bằng ID sản phẩm thật. Nếu layout của bạn dùng slug khác, sửa `order_product_lines`, `product` và `discount_percent` tương ứng.

### 3.2. Giải thích phần kiểm tra và áp dụng mã

Các đoạn dưới đây trích từ hai hàm `handleCheckPromotion` và `applyPromotion` ở mục 3.1.

#### a. Nhận mã người dùng nhập

Khi bấm **Kiểm tra** hoặc nhấn Enter, `handleCheckPromotion` bỏ khoảng trắng đầu/cuối và đổi mã sang chữ hoa. Nếu chưa nhập mã hoặc chưa có API Form Builder, component hiển thị thông báo.

```ts
const promotionCode = code.trim().toUpperCase();
if (!promotionCode || !formBuilder?.execScript) {
    setMessage('Vui lòng nhập mã khuyến mãi trong Form Builder.');
    return;
}
```

#### b. Giả lập kiểm tra mã

Tìm mã trong danh sách cố định `promotions`. Phần này mô phỏng kiểm tra mã; khi kết nối Custom Backend hoặc hệ thống khác, thay thao tác tìm trong mảng bằng lời gọi API.

```ts
const promotion = promotions.find((item) => item.code === promotionCode);
```

Nếu không tìm thấy, báo mã không hợp lệ. Nếu có, chuyển sản phẩm và chiết khấu tới `applyPromotion`.

```ts
if (!promotion) {
    setMessage('Mã khuyến mãi không hợp lệ.');
} else {
    const matchedRows = await applyPromotion(promotion);
    if (matchedRows === 0) {
        setMessage('Không có dòng sản phẩm phù hợp với mã khuyến mãi.');
    } else {
        setMessage(`Đã áp dụng mã ${promotionCode} cho ${matchedRows} dòng. Hãy lưu bảng để ghi nhận.`);
    }
}
```

#### c. Thực thi Layout Script để áp dụng chiết khấu

`applyPromotion` gọi `formBuilder.execScript` để thao tác trên biểu mẫu. **Phần code trong `execScript` dùng cú pháp và API [Layout Scripting](../../layout-scripting/SKILL.md) của Cogover**, gồm `screen.get(...)`, `lines.rows()`, `row.get(...)` và `cell.value`.

Dưới đây là toàn bộ hàm áp dụng:

```ts
const applyPromotion = async (promotion: Promotion) => {
        if (!formBuilder?.execScript) {
            throw new Error('Hãy mở component trong biểu mẫu đơn hàng.');
        }

        let matchedRows = 0;
        await formBuilder.execScript(async ({ screen }) => {
            const lines = screen.get('order_product_lines', 'RELATED_LIST');
            if (!lines?.rows) throw new Error('Không tìm thấy danh sách sản phẩm.');

            for (const row of await lines.rows()) {
                const productCell = row.get('product');
                if (productCell?.value === promotion.product_id) {
                    const discountCell = row.get('discount_percent');
                    if (!discountCell) {
                        throw new Error('Không tìm thấy ô chiết khấu của sản phẩm.');
                    }
                    if (discountCell.value !== promotion.discount_percent) {
                        discountCell.value = promotion.discount_percent;
                    }
                    matchedRows += 1;
                }
            }
        });
        return matchedRows;
    };
```

`order_product_lines` là **slug của item Related List trong layout**. Hàm duyệt các dòng, so sánh giá trị ô `product` với `promotion.product_id`, rồi cập nhật `discount_percent` cho tất cả dòng khớp.

Ô đã có đúng phần trăm chiết khấu được giữ nguyên; ô có giá trị khác được thay thế. Hàm trả số dòng phù hợp để phần kiểm tra mã hiển thị kết quả. Việc cập nhật này chưa tự lưu bảng.

#### d. Trạng thái xử lý và lỗi

Trước khi kiểm tra, bật `isChecking` để khóa ô nhập và nút:

```ts
setIsChecking(true);
```

Phần cuối khối xử lý hiển thị lỗi nếu có và kết thúc trạng thái đang kiểm tra:

```ts
} catch (error) {
    setMessage(error instanceof Error ? error.message : 'Không kiểm tra được mã khuyến mãi.');
} finally {
    setIsChecking(false);
}
```

### 3.3. Khai báo component để Cogover tải

Trong `vite.config.ts`, thêm khóa vào `exposes` (danh sách component công khai), giữ lại `./CustomApp` và các khóa khác nếu đã có:

```ts
exposes: {
    './CustomApp': './src/App.tsx',
    './Components/PromotionCodeChecker': './src/components/PromotionCodeChecker.tsx',
},
```

## 4. Publish dự án

### 4.1. Kiểm tra và build

Chạy tại thư mục dự án:

```bash
npx prettier --write src/components/PromotionCodeChecker.tsx vite.config.ts
npm run lint
npm run build
```

Chờ build hoàn tất. Kết quả nằm trong thư mục `dist`.

### 4.2. Đóng gói

Nén thư mục `dist` vừa build thành file ZIP để tải lên Cogover.

### 4.3. Tải lên và kích hoạt

Có thể tải lên bằng giao diện hoặc bằng Cogover Dev CLI. Cả hai cách đều publish một phiên bản mới rồi kích hoạt phiên bản đó; chỉ cần chọn một cách.

#### Cách 1: Thủ công bằng giao diện

1. Mở trang chi tiết dự án đã tạo ở phần 2.
2. Tại **Phát hành phiên bản mới**, bấm **Chọn tệp** và chọn ZIP.
3. Bấm **Tải lên và phát hành**.
4. Trong **Lịch sử phiên bản**, chờ phiên bản mới ở trạng thái **Sẵn sàng**.
5. Mở menu thao tác của đúng phiên bản đó và chọn **Kích hoạt**.
6. Kiểm tra phiên bản được đánh dấu **Đang dùng**.

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

Thay `<WORKSPACE_DOMAIN>` bằng hostname đầy đủ, ví dụ `example.cogover.net`, và `<FRONTEND_PROJECT_ID>` bằng Project ID dạng `FEP...`. Phải đặt `"projectType": "frontend"`; nếu bỏ qua, CLI mặc định dùng backend. **Vị trí trên máy chủ** như `_cm_1` chỉ dùng để cấu hình đường dẫn component ở phần 5, không phải Project ID hay slug dự án và không cần đưa vào cấu hình này.

CLI tìm `COGOVER_API_KEY` trong `.env` của dự án trước, rồi trong credential store của hệ điều hành. Nếu chưa có, CLI hỏi Workspace API key qua prompt ẩn. Sau khi xác thực thành công, key nhập qua prompt được lưu vào native store nếu có; nếu không, CLI lưu vào `.env` và thêm file này vào `.gitignore`. Trong Docker hoặc CI không có terminal tương tác, cần cung cấp trước file `.env` riêng tư chứa `COGOVER_API_KEY` ở thư mục dự án. Không commit, đưa vào ZIP, hoặc chia sẻ key/file này.

Sau khi build ở mục 4.1, chạy:

```bash
cogover-dev publish
```

CLI yêu cầu `dist/index.html`, tự ZIP thư mục `dist/`, tải lên ở chế độ private, tạo phiên bản và chờ trạng thái `READY` (tương ứng **Sẵn sàng** trên giao diện) hoặc `FAILED`. CLI không chạy build; khi thay đổi source, cần chạy lại `npm run build` trước khi publish. ZIP do CLI tự tạo được xóa sau khi lệnh kết thúc, còn thư mục `dist/` được giữ nguyên. Nếu dùng cách này, có thể bỏ qua bước đóng gói ở mục 4.2.

Nếu đã tạo ZIP ở mục 4.2, có thể dùng thay thế:

```bash
cogover-dev publish <ZIP_FILE>
```

Thay `<ZIP_FILE>` bằng đường dẫn tới file ZIP đó. File ZIP truyền vào vẫn phải chứa `dist/index.html` với thư mục `dist` được giữ nguyên và không bị CLI xóa. Không chạy cả hai lệnh publish nếu chỉ muốn tạo một phiên bản.

Khi publish thành công, CLI in ID phiên bản dạng `FEV...` cùng lệnh kích hoạt. Chạy đúng ID phiên bản vừa nhận, không dùng Project ID `FEP...`:

```bash
cogover-dev activate <VERSION_ID>
```

CLI kiểm tra phiên bản thuộc đúng dự án frontend và đang `READY` trước khi kích hoạt. Nếu publish báo `FAILED`, đọc lỗi, sửa source, build rồi publish phiên bản mới; không kích hoạt phiên bản lỗi. Sau khi kích hoạt thành công, có thể mở **Lịch sử phiên bản** trên giao diện để kiểm tra phiên bản được đánh dấu **Đang dùng**, rồi tiếp tục phần 5.

## 5. Xem kết quả

### 5.1. Đưa component vào layout đơn hàng

1. Mở trang sửa layout của Object `order`.
2. Thêm thành phần **Federation component** và điền đường dẫn component.
3. Nếu **Vị trí trên máy chủ** của dự án là `_cm_1`, dùng:

```text
_cm_1/Components/PromotionCodeChecker
```

4. Nếu dự án được cấp `_cm_2`, thay phần đầu thành `_cm_2`.
5. Lưu layout.

Phần `Components/PromotionCodeChecker` phải khớp chữ hoa/thường với khóa expose đã khai báo.

### 5.2. Thử mã giảm giá

Mở đơn hàng có các dòng sản phẩm A và B đã khai báo ở phần 3. Nhập mã rồi bấm **Kiểm tra** hoặc nhấn Enter. Sau đó thử:

| Thao tác | Kết quả mong đợi |
|---|---|
| Nhập `SALE10`, bấm **Kiểm tra** | Các dòng sản phẩm A có chiết khấu 10% |
| Nhập `SALE20`, bấm **Kiểm tra** | Các dòng sản phẩm B có chiết khấu 20% |
| Nhập ` sale10 ` | Vẫn nhận diện là `SALE10` |
| Nhập mã không tồn tại | Báo mã không hợp lệ, không cập nhật chiết khấu |
| Dùng mã hợp lệ nhưng không có sản phẩm tương ứng | Báo không có dòng phù hợp |
| Một sản phẩm có nhiều dòng | Cập nhật tất cả dòng khớp sản phẩm |
| Dòng đã có chiết khấu khác | Thay bằng phần trăm của mã vừa áp dụng |

Sau khi kiểm tra kết quả trên form, bấm **Lưu** của bảng sản phẩm để ghi nhận chiết khấu. Mở lại đơn hàng để xem giá trị đã lưu.
