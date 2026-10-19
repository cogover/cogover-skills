# Dùng `@cogover/client-sdk` ở frontend

`@cogover/client-sdk` là thư viện frontend của Cogover cho Custom Frontend Module. Gói gồm ba phần:

| Phần | Nội dung | Dạng frontend được dùng |
|---|---|---|
| UI component | React component và icon theo giao diện Cogover: `Button`, `TextField`, `Select`, `DatePicker`, `Modal`, `FormItem`, `ListViewTable`, `Pagination`, `ResizableMenu`, `FilterGenerator`... | **Chỉ** custom component và Federation Page (template React) |
| Data hook | Hook React đọc record/Object theo phiên người dùng: `useRecords`, `useInfiniteRecords`, `useRecordDetail`, `useRecordsByIds`, `useObjectDetail`, `useObjectFields`, `useObjectFieldDetail` | **Chỉ** custom component và Federation Page |
| Socket listener | Nhận push của Custom Backend Module (`push.refreshRecords`, `push.toast`, `push.message`): `useSocketListener` (React), `createSocketListener` (JavaScript thuần) | Cả ba dạng; single page app chỉ dùng `createSocketListener` |

Nguồn chuẩn cho props, input và output là `node_modules/@cogover/client-sdk/README.md` của bản đã cài; tài liệu này chỉ nêu cách chọn và quy tắc dùng trong Custom Module. Có khác biệt thì README của bản đang chạy thắng.

## Chọn cách dùng theo dạng frontend

1. **Custom component và Federation Page** (template [`custom-frontend-module-template`](https://github.com/cogover/custom-frontend-module-template)):
   - Template đã cài sẵn gói; chỉ import từ gốc `@cogover/client-sdk`, riêng stylesheet là `@cogover/client-sdk/styles.css`. Không import đường dẫn con (`/ui`, `/data`, `/provider`, `/http`, `/socket`) dù README của gói có ví dụ như vậy: nền tảng chỉ chia sẻ gói gốc, import con bị đóng gói riêng, không thấy `LibraryProvider` của nền tảng và tạo thêm một bản SDK trong bundle.
   - Không tự bọc `LibraryProvider`. Khi nhúng vào Cogover, nền tảng đã đặt sẵn; ở chế độ dev standalone, `src/providers` của template đã bọc.
   - Quy ước chi tiết theo skill trong `.agents/skills` của template đã clone: `custom-module-foundation` (UI component, icon, layout trang), `custom-module-list-page` (màn danh sách), `custom-module-api` (data hook, `FilterGenerator`, nhận push).
2. **Single page app** (HTML, CSS, JavaScript thuần hoặc stack tự chọn, mở qua `/{slugSlot}/index.html`):
   - Không dùng UI component và data hook của SDK; giao diện và lời gọi API do project tự viết.
   - Chỉ được dùng socket listener qua `@cogover/client-sdk/socket`. Entry này không import React nên bundler (ví dụ Vite) chỉ đóng gói phần socket. Project cần bundler để cài gói từ npm; trang HTML tĩnh không có bước build thì không dùng được gói này.

## Phiên bản SDK

1. Custom component và Federation Page: template khai báo `@cogover/client-sdk` trong `shared` của Module Federation mà không đặt `requiredVersion`, nên lúc chạy trong Cogover, module luôn dùng bản SDK của nền tảng, không dùng bản trong `package.json` của project. API chỉ có ở bản mới hơn bản nền tảng đang chạy sẽ không tồn tại khi nhúng dù build local vẫn pass.
   - Trước khi dùng API mới, kiểm tra bản nền tảng trên Workspace đích trong trình duyệt đã đăng nhập: `Object.keys(globalThis.__federation_shared__?.default?.['@cogover/client-sdk'] ?? {})` trả danh sách phiên bản đang được chia sẻ.
   - Nâng `@cogover/client-sdk` trong `package.json` của project không thay được bản của nền tảng; phiên bản đó chỉ quyết định type khi build và chế độ dev standalone.
2. Single page app: bản SDK được đóng gói vào bundle của project, nên phiên bản là bản trong `package.json`.
3. Phiên bản tối thiểu theo tính năng:

| Tính năng | Từ phiên bản |
|---|---|
| `useSocketListener`, `createSocketListener`, entry `@cogover/client-sdk/socket` | `0.3.0` |
| Toast chỉ giữ link an toàn, bỏ frame không có workspace khi đã biết workspace | `0.3.1` |

## UI component (chỉ template React)

1. Dùng component của SDK thay vì tự viết bảng, phân trang, dropdown, date picker, modal, tooltip, toast hoặc panel kéo đổi kích thước; giao diện và hành vi theo đúng Cogover.
2. Nhãn và control trong form dùng `FormItem` (`label`, `component`). Icon dùng icon của SDK; chỉ dùng SVG riêng khi SDK chưa có icon phù hợp.
3. Màn danh sách theo skill `custom-module-list-page` của template: `ListViewTable`, `Pagination`, `ResizableMenu`, `FilterGenerator`.
4. Thông báo trong module dùng `ToastContainer` cùng `showToastMessage`/`ToastMessage` của SDK, không cài thêm thư viện toast.

## Data hook (chỉ template React)

1. Truyền `objectSlug` hoặc `objectId` cho hook record; `id` hoặc `slug` cho hook Object. `objectId` ưu tiên hơn `objectSlug` khi có cả hai.
2. `fields` chỉ gồm slug field giao diện dùng, giống quy tắc đọc record tối thiểu ở backend.
3. Lọc record: `FilterGenerator` sinh điều kiện, truyền thẳng vào `useRecords` (`type`, `logic_sequence`, `filters`). Phân trang dùng `size` và cursor `search_after`/`nextCursor`; danh sách cuộn dài dùng `useInfiniteRecords`.
4. Hook đọc theo phiên người dùng cuối: dữ liệu và quyền xem là của người đang mở trang. Số liệu tổng hợp vẫn lấy từ saved report theo [Tận dụng báo cáo cho số liệu tổng hợp](report-data-reuse.md), không gom bằng `useRecords` qua nhiều trang.
5. Logic nghiệp vụ hoặc thao tác cần quyền của module (ghi theo quy tắc riêng, gọi hệ thống ngoài, dùng secret) nằm ở Custom Backend Module, frontend gọi route theo [Full-stack integration](full-stack-integration.md).

## Nhận push message từ Custom Backend Module

Backend gửi bằng `push.refreshRecords`, `push.toast`, `push.message` (mục [Push message](cogover-sdk-api-reference.md#push-message) của SDK API reference). SDK mở một kết nối socket riêng tới Workspace cho mỗi tab (xác thực bằng phiên trình duyệt) khi handler đầu tiên đăng ký, đóng khi không còn handler; mọi listener trên trang dùng chung kết nối này. Chỉ ba loại push trên được chuyển tới handler, lưu lượng socket khác bị bỏ qua.

### Custom component và Federation Page: `useSocketListener`

```tsx
import { useEffect } from 'react';
import { useRecordDetail, useSocketListener } from '@cogover/client-sdk';
import type { MessagePayload } from '@cogover/client-sdk';

export function OrderPanel({ recordId }: { recordId: string }) {
    const { refetch } = useRecordDetail({ objectSlug: 'order', id: recordId });
    const { subscribe, unsubscribe, status } = useSocketListener();

    useEffect(() => {
        if (!recordId) return; // chưa có record: không đăng ký, tránh nhận push của record khác
        const target = { objectSlug: 'order', recordId };
        const onRefresh = () => refetch();
        const onMessage = (payload: MessagePayload) => {
            const data = payload.data as { event?: string } | null;
            if (data?.event === 'order.synced') refetch();
        };
        subscribe('refreshRecords', onRefresh, target);
        subscribe('message', onMessage, { ...target, source: 'order_sync' });
        return () => {
            unsubscribe('refreshRecords', onRefresh);
            unsubscribe('message', onMessage);
        };
    }, [recordId, refetch, subscribe, unsubscribe]);

    return status === 'unauthorized' ? <p>Phiên đăng nhập đã hết hạn.</p> : null;
}
```

`subscribe` và `unsubscribe` ổn định giữa các lần render, đưa vào dependency của `useEffect` an toàn. Hook tự lấy workspace và tra ID Object theo `objectSlug` từ `LibraryProvider`.

### Single page app: `createSocketListener`

```js
import { createSocketListener } from '@cogover/client-sdk/socket';

const listener = createSocketListener({ workspaceId: '<WORKSPACE_ID>' });
const onMessage = (payload) => {
    if (payload.data?.event === 'order.synced') reloadOrder();
};
listener.subscribe('message', onMessage, { objectId: '<OBJECT_ID>', recordId: '<RECORD_ID>', source: 'order_sync' });
listener.onStatusChange(() => renderStatus(listener.getStatus()));
// Khi rời màn hình:
listener.unsubscribe('message', onMessage);
```

1. `workspaceId` không bắt buộc; có thì frame của workspace khác bị bỏ.
2. Không có `LibraryProvider` nên nhận push theo record phải truyền `objectId`, hoặc truyền `resolveObjectId: async (slug) => objectId` vào `createSocketListener` để dùng `objectSlug` (project tự tra ID qua API). Thiếu cả hai, đăng ký theo record không nhận push gửi `"viewers"` và SDK ghi lỗi ra console.
3. `subscribe` trả về hàm huỷ đăng ký; `onStatusChange` trả về hàm huỷ theo dõi trạng thái.

### Event, payload và tuỳ chọn

| Event | Payload |
|---|---|
| `refreshRecords` | `{ recordId? }` |
| `toast` | `{ title?, content?, position, size, durationSeconds, links, objectSlug?, recordIds? }` |
| `message` | `{ data, content, contentType, recordId? }`; `data` là `JSON.parse(content)` hoặc `null` khi `content` không phải JSON |

| Tuỳ chọn của `subscribe` | Ý nghĩa |
|---|---|
| `objectSlug` + `recordId` (React) hoặc `objectId` + `recordId` (JavaScript thuần) | Đăng ký record đang hiển thị: nhận thêm push gửi `"viewers"` của đúng record đó. Không truyền thì chỉ nhận push gửi đích danh người dùng hiện tại. |
| `source` | Chỉ áp dụng cho `message`: giữ message có `data.source` bằng giá trị này. Backend nên đặt `source` cố định trong JSON `content` để các module trên cùng trang không nhận nhầm message của nhau. |

Trạng thái kết nối (`status` hoặc `getStatus()`): `idle`, `connecting`, `connected`, `unauthorized`. `unauthorized` nghĩa là không có phiên đăng nhập, SDK ngừng kết nối lại; hiển thị thông báo đăng nhập thay vì chờ.

### Quy tắc

1. Đăng ký trong `useEffect` (hoặc khi màn hình JavaScript thuần được mở) và luôn huỷ đăng ký khi rời màn hình hoặc khi `recordId` đổi; truyền đúng hàm handler đã đăng ký vào `unsubscribe`.
2. Màn hình theo record chỉ đăng ký khi đã có `recordId`; push gửi `"viewers"` chỉ tới người đang đăng ký đúng record đó.
3. Trong Cogover, web app đã tự hiển thị toast và tải lại record đang mở; module chỉ xử lý phần riêng của mình (tải lại dữ liệu của module, cập nhật trạng thái), không hiện lại toast lần nữa. Single page app chạy ngoài khung Cogover nên tự hiển thị nếu cần.
4. `data` của `message` đến từ bất kỳ ai gọi được route backend: kiểm tra kiểu và giá trị trước khi dùng, không render thành HTML (`innerHTML`, `dangerouslySetInnerHTML`). `links` của toast đã được SDK lọc chỉ còn `http(s)`, `mailto:` và đường dẫn tương đối, nhưng vẫn render bằng thẻ link, không chèn HTML.
5. Push là best-effort và có thể lặp: handler phải chịu được việc nhận trùng hoặc thiếu push; dữ liệu đúng lấy từ lần đọc lại API, không dựa hoàn toàn vào nội dung push.
6. Custom component và Federation Page cần nền tảng chạy SDK từ `0.3.0` (kiểm tra theo mục Phiên bản SDK); chưa đạt thì không dùng listener và báo người dùng thay vì tự mở WebSocket.

## Kiểm tra trước bàn giao

1. Code template React không có import đường dẫn con của SDK ngoài `styles.css`; single page app chỉ import `@cogover/client-sdk/socket`.
2. Mọi `subscribe` có `unsubscribe` tương ứng trong cleanup; không có listener bị đăng ký lặp mỗi lần render.
3. Trên Workspace, trong trình duyệt đã đăng nhập, gọi route backend gửi đủ các loại push module dùng (gửi `"viewers"` khi đang mở record và gửi đích danh), xác nhận giao diện phản ứng đúng; với Federation Page và custom component, ghi lại phiên bản SDK nền tảng đã kiểm tra.
