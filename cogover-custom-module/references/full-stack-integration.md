# Kết nối frontend và backend

Tổng hợp phần kết nối từ hướng dẫn sản phẩm `build-full-stack-custom-module.md`. Dùng cùng [Backend quick start](get-started-custom-backend-module.md), [Frontend quick start](get-started-custom-frontend-module.md) và [SDK API reference](api-reference.md). Ví dụ route, field và port chỉ minh họa; thay bằng contract dự án đã xác minh.

## Local

Giữ `backend/` và `frontend/` độc lập. Chạy backend bằng Cogover Dev CLI, port loopback riêng. Frontend Vite proxy route API sang local runner:

```typescript
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  server: {
    proxy: {
      "/api/v1/ts-projects": {
        target: "http://127.0.0.1:3100",
        changeOrigin: true,
      },
    },
  },
});
```

Đối chiếu port với `COGOVER_LOCAL_PORT` thật. Đây là proxy tới backend **local**, không phải proxy mang API key vào browser để gọi Workspace. Chỉ backend local qua CLI mới có Development Session. Frontend không cần Project key. Không dùng `VITE_*` chứa Workspace key/Project key/cookie/credential vì biến build có thể bị đưa vào bundle.

Frontend thuần chưa có browser session trên Workspace có thể test UI bằng fixture và kiểm thử API trên Workspace ở bước deploy; không lách xác thực bằng cách nhúng key vào source. Báo rõ giới hạn nếu local chưa kiểm thử được dữ liệu thật.

## Production

1. Publish/approve policy nếu cần/activate backend trước.
2. Frontend gọi URL tương đối `/api/v1/ts-projects/<BACKEND_PROJECT_SLUG>/<ROUTE>` cùng origin Workspace, dùng `credentials: "same-origin"`.
3. Dùng `x-req-service: 3` và `x-req-type: 6` theo quick start. Cho request cần CSRF, đọc cookie `XSRF-TOKEN` và đặt cùng giá trị vào `x-csrf-token`, `x-xsrf-token`. Browser tự gửi cookie; không đọc/chép `AuthToken` hay `HttpSessionId` vào code, không hardcode bất kỳ token nào. Khi thiếu phiên, hiển thị yêu cầu đăng nhập lại.
4. Local runner không cần các routing/auth header production. Dùng nhánh cấu hình build/dev rõ ràng; không để logic production gọi `localhost`.
5. Xử lý transport envelope một cách có chủ đích: production mẫu có `body`, local trả trực tiếp handler result. Kiểm tra status/error và shape theo mode/contract, không chỉ thấy một property `body` là unwrap vì output nghiệp vụ cũng có thể có field đó. Custom response text/binary dùng parser theo content type đã định nghĩa.
6. Mỗi thao tác ghi có idempotency key riêng; retry thao tác đang pending giữ nguyên key. Vô hiệu hóa nút khi đang gửi để hạn chế thao tác trùng, nhưng kiểm soát ghi lặp vẫn ở backend.

API frontend được gọi bằng quyền người dùng đang đăng nhập; ẩn nút trên UI không thay thế kiểm tra quyền. Dùng `textContent` hoặc cơ chế escape của framework khi render dữ liệu Workspace.

## Kiểm thử trên Workspace

- Mở đúng `https://<WORKSPACE_DOMAIN>/<SLUG_SLOT>/index.html`, không dùng project slug hoặc project ID thay `slugSlot`.
- Kiểm tra đăng nhập, tải dữ liệu, thao tác ghi được phép và đọc lại record đã thay đổi; dùng caller có/không có quyền nếu yêu cầu phân quyền.
- Refresh/deep-link: static hosting không có SPA fallback; dùng hash routing hoặc URL file tồn tại. Asset có content hash tránh cache version cũ.
- Xác minh frontend và backend đang chạy đúng version đã kiểm thử; kết quả thành công một phía chưa chứng minh toàn luồng.

## Kiểm tra query string khi chuyển từ local sang Workspace

Đã quan sát một deployment trả cùng danh sách mặc định cho nhiều giá trị query string khác nhau, trong khi local runner lọc đúng. Đây là khác biệt tương thích cần kiểm chứng trên Workspace đích; SDK contract vẫn có `request.query`, không kết luận mọi Workspace đều thiếu khả năng này.

Trước khi bàn giao route tìm kiếm/phân trang dùng query string, gọi production với ít nhất một giá trị có kết quả, một giá trị chắc chắn không khớp fixture và hai trang dữ liệu. So sánh input, tổng số, ID và cursor với local; HTTP 200 không chứng minh filter được áp dụng.

Nếu tái hiện query bị bỏ qua, giữ request/response đã ẩn dữ liệu nhạy cảm để báo lỗi. Có thể dùng route POST tìm kiếm với JSON body (`request.body`) chứa filter/limit/cursor đã validate, cập nhật đồng bộ frontend và cURL, publish version mới rồi chạy lại test local + production. Chỉ dùng workaround này khi phù hợp contract nghiệp vụ; không nhét credential hoặc metadata xác thực vào body, không âm thầm bỏ filter, không đánh dấu PASS cho version còn lỗi. Nếu người dùng bắt buộc giữ GET contract, báo giới hạn runtime thay vì tự đổi public contract đã cam kết.
