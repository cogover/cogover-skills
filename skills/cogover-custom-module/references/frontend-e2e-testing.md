# Kiểm thử end-to-end frontend bằng sub-agent độc lập

Đọc khi dự án có Custom Frontend Module ở bất kỳ dạng nào (single page app, custom component, Federation Page), kể cả frontend thuần. Xác thực: [$cogover-api-auth](../../cogover-api-auth/SKILL.md) và [Cơ chế xác thực](../../cogover-api-auth/references/authentication-mechanisms.md); persona: [Kiểm thử quyền runtime](../../user-permission/references/permission-testing.md) của `$user-permission`. Công cụ, lệnh và tên file bên dưới chỉ minh họa.

## 1. Tính độc lập

- Agent chính giao một **sub-agent E2E riêng**, khác sub-agent Frontend và Backend. Agent đã viết code frontend không viết hoặc chấm E2E cho chính code đó; agent chính không tự nhận vai E2E. Không có công cụ sub-agent thì báo rõ yêu cầu E2E độc lập chưa đáp ứng.
- Gói giao việc: contract nghiệp vụ, tiêu chí nghiệm thu, dạng frontend đã xác nhận ở 1A, URL/route, mapping Object/field và record fixture, quy ước selector, danh sách persona, nguồn phiên test (mục 3), phạm vi dữ liệu được ghi, lịch dùng chung fixture với các agent khác. Chỉ truyền cách truy cập credential an toàn, không truyền giá trị.
- Viết test từ contract và tiêu chí nghiệm thu theo kiểu hộp đen, không bám chi tiết cài đặt. Selector dùng role/label accessible hoặc `data-testid` đã thống nhất trong contract; tránh CSS/XPath theo cấu trúc DOM.
- Sub-agent E2E không sửa source ứng dụng; test fail thì báo agent chính kèm bước tái hiện và bằng chứng, agent chính giao sub-agent phụ trách sửa rồi chạy lại E2E. Sub-agent Frontend không sửa, nới assertion, skip hay xoá test E2E để test pass; đổi test chỉ khi contract đổi và được agent chính duyệt.

## 2. Công cụ và cấu trúc

- E2E là script chạy lại được trên trình duyệt thật, không chỉ thao tác tay: thư mục riêng tách khỏi `src/` (ví dụ `e2e/`) hoặc project test riêng, lệnh tái chạy (ví dụ `npm run test:e2e`), exit code khác 0 khi có test fail. Khuyến nghị Playwright với TypeScript và Chromium; công cụ tương đương dùng được nếu chạy trình duyệt thật và tái chạy được. Công cụ điều khiển trình duyệt của môi trường agent chỉ dùng để quan sát hoặc debug, không thay script.
- Cấu hình (base URL, hostname Workspace, record ID fixture, persona) qua biến môi trường hoặc file cấu hình không chứa secret.
- E2E không tính vào line coverage của unit tests. Thư mục E2E, file phiên, báo cáo và artifact test không vào ZIP publish hay commit.

## 3. Xác thực trình duyệt test

Chọn nguồn phiên theo thứ tự:

1. **Người dùng cung cấp tài khoản test:** ưu tiên API key của tài khoản đó và tạo phiên như mục 2 bên dưới. Chỉ có mật khẩu: người dùng tự đăng nhập một lần trên trình duyệt test để lưu trạng thái phiên (ví dụ Playwright `storageState`) vào file cục bộ, hoặc tự đặt biến môi trường cho tiến trình test. Không nhận mật khẩu qua chat; không ghi vào source, log hay báo cáo; agent không tự gõ mật khẩu vào form đăng nhập.
2. **Người dùng không cung cấp tài khoản:** dùng `$cogover-api-auth` đổi Workspace API key đã có thành phiên Web App bằng `POST /bapi/v1/auth-token`, rồi nạp phiên vào browser context:
   - Gọi auth-token từ request context dùng chung cookie store với browser context (Playwright: `context.request.post(...)`), để ba cookie `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` được lưu với đúng thuộc tính do server đặt. Không dùng được cách này thì nạp ba cookie từ `data` của response vào đúng hostname Workspace (`path: "/"`, `secure: true`). Không tự đặt header CSRF trong test: Web App và template đọc cookie `XSRF-TOKEN`.
   - Đối chiếu `workspaceDomain`/`workspaceId` theo `$cogover-api-auth`; ghi `personnelId` làm danh tính của phiên. Không in response tạo phiên.
   - API key đọc từ biến môi trường của tiến trình test (ví dụ `COGOVER_API_KEY`) hoặc credential store; không hardcode, không đặt vào biến `VITE_*`, không commit `.env`.
   - Tạo lại phiên trước `HttpSessionExpiresAt`. File trạng thái phiên (nếu lưu) có mode `0600`, nằm trong `.gitignore` và bị xoá khi xong.

```typescript
// e2e/auth.ts — minh họa với Playwright
import type { BrowserContext } from "@playwright/test";

export async function signInWithApiKey(context: BrowserContext, origin: string): Promise<string> {
  const apiKey = process.env.COGOVER_API_KEY;
  if (!apiKey) throw new Error("COGOVER_API_KEY is not set");
  const res = await context.request.post(`${origin}/bapi/v1/auth-token`, {
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
    data: {},
  });
  const body = await res.json();
  if (!res.ok() || body.r !== 0) throw new Error(`Cannot create a test session (HTTP ${res.status()})`);
  return body.personnelId; // Chỉ trả danh tính, không log cookie hay token.
}
```

Giới hạn của phiên:

- Phiên là danh tính của chủ API key. Không kết luận quyền của user thường hoặc persona khác bằng phiên Super Admin hay phiên quản trị.
- Ca phụ thuộc Role, phòng ban, vị trí hoặc người không có quyền: lấy persona theo [Kiểm thử quyền runtime](../../user-permission/references/permission-testing.md) (người dùng xác nhận user test và cách cấp API key tạm), tạo phiên riêng cho từng persona, mỗi persona một browser context. Không có persona phù hợp thì ghi ca đó là chưa kiểm thử.
- Cookie của domain Workspace không áp dụng cho `localhost`. Single page app chạy local: test UI bằng fixture hoặc chặn request (route mock). Custom component qua `npm run preview` được trang record thật của Workspace tải về nên dùng được phiên đã nạp. Federation Page `npm run dev` chỉ chạy E2E local khi đã xác minh luồng chuyển hướng đăng nhập của template hoàn tất với phiên đã nạp; nếu không, chạy trên Workspace sau khi activate.

## 4. Bảo vệ credential trong artifact

- Trace, HAR, video và screenshot có thể chứa cookie, header và dữ liệu thật. Tắt ghi HAR/network; trace chỉ giữ khi fail, lưu cục bộ và xoá sau khi phân tích; không đính kèm trace/HAR vào báo cáo hay gửi cho người khác.
- Screenshot đưa vào báo cáo chỉ gồm màn hình không có dữ liệu nhạy cảm. Log test không in cookie, header `Authorization` hay response tạo phiên.

## 5. Dữ liệu test

- Chạy trên Workspace test với fixture có marker duy nhất; theo dõi mọi ID được tạo và dọn theo phạm vi đã được phép của skill dữ liệu. Không chạy song song với agent khác trên cùng fixture; agent chính điều phối lịch.
- Sau thao tác ghi, đọc lại record bằng API (`$object-record`) để chứng minh hiệu ứng, không chỉ tin UI.
- Luồng UI kích hoạt notification, email hay push tới người thật: chỉ dùng persona và địa chỉ test đã được người dùng xác nhận.

## 6. Ca kiểm thử

Mỗi tiêu chí nghiệm thu có ít nhất một test. Chung cho mọi dạng: trang tải không có lỗi console/network ngoài dự kiến; trạng thái loading, empty, error; luồng chính tới kết quả; input không hợp lệ; người được phép và người bị từ chối; thao tác bằng bàn phím; kích thước màn hình liên quan; refresh và deep-link.

| Dạng | Ca riêng |
|---|---|
| Single page app | Mở `https://{WORKSPACE_DOMAIN}/{slugSlot}/index.html`; asset tải từ `/{slugSlot}/`; hash routing đúng sau refresh |
| Custom component | Mở record thật có layout chứa item Federation component `{slugSlot}/Components/<Tên>`; thiếu `formBuilder`; cập nhật field và ô Related List; lưu rồi đọc lại record; lỗi giữa chừng; không tự chạy lặp |
| Federation Page | Mở `https://{WORKSPACE_DOMAIN}/{APP_SLUG}/c{N}/{PATH}` cho từng route; `Link` nội bộ; mục menu; refresh, deep-link và quyền |
| Full-stack | Request tới `/api/v1/ts-projects/<BACKEND_PROJECT_SLUG>/...` thành công trên production; lỗi backend hiển thị đúng; không còn gọi `localhost` |
| Số liệu từ báo cáo | Bằng phiên của từng persona: giá trị hiển thị khớp service `200` của saved report chạy trực tiếp cùng tham số bằng cùng phiên đó; người ngoài ACL thấy trạng thái không có quyền; theo [Tận dụng báo cáo](report-data-reuse.md#5-kiểm-thử) |

Sau khi activate version frontend mới: tải lại cứng, không có lỗi không tìm thấy remote module, asset tải từ `/{slugSlot}/assets/`.

## 7. Thời điểm chạy

1. Viết test ngay sau khi chốt contract và xác nhận 1A, song song với code frontend.
2. Bước 8: chạy trên local khi frontend báo sẵn sàng, với các ca chạy được theo mục 3; E2E không thay unit tests.
3. Bước 9: chạy lại toàn bộ trên Workspace sau khi publish/activate; đây là điều kiện nghiệm thu frontend. Chạy lại sau mỗi lần sửa và publish lại.

## 8. Báo cáo

Sub-agent E2E trả cho agent chính: lệnh chạy; môi trường (URL, hostname Workspace, version frontend/backend đang active); trình duyệt và phiên bản; persona (`personnelId`, nguồn phiên, không kèm credential); số test pass/fail/skip; bảng tiêu chí nghiệm thu → test → kết quả; lỗi kèm bước tái hiện và screenshot an toàn; fixture đã tạo và đã dọn; ca chưa chạy được cùng lý do. Test skip/todo không tính PASS. Agent chính kiểm tra bằng chứng; thông báo "đã chạy xong" không phải bằng chứng PASS.
