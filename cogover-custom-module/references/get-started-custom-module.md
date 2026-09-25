# Các loại Custom Module và dạng Custom Frontend Module

Snapshot tài liệu sản phẩm tiếng Việt ngày `2026-09-15`, bổ sung bảng chọn nhanh và câu hỏi xác định cho agent. Ví dụ, slug, slot và ID chỉ minh họa; không thay dữ liệu thật của Workspace.

## Chọn loại module

| Loại | Dùng khi | Ví dụ |
|---|---|---|
| **Custom Backend Module** | Cần xử lý nghiệp vụ phía server, đọc/ghi Object, kiểm tra quyền, giữ bí mật tích hợp hoặc cung cấp API riêng. | Tính giá đơn hàng, đồng bộ dữ liệu với hệ thống kế toán, API tổng hợp tồn kho. |
| **Custom Frontend Module** | Cần một màn hình hoặc thành phần giao diện riêng nhưng không cần thêm logic server. Có ba dạng: single page app, custom component và Federation Page. | Dashboard chỉ đọc từ API có sẵn, khối kiểm tra mã giảm giá trên form đơn hàng, trang công cụ trong menu ứng dụng. |
| **Kết hợp Backend + Frontend** | Giao diện cần gọi logic hoặc dữ liệu đã được xử lý riêng ở backend. | Trang CRM tìm 5 Account lâu năm nhất và đánh dấu chúng là `Heritage Account`. |

Không đặt secret trong Custom Frontend Module vì mã frontend được tải xuống trình duyệt. Logic nhạy cảm, quyền nâng cao và credential tích hợp phải nằm ở backend.

Ghi chú cho agent: dashboard hoặc API có số liệu tổng hợp từ một hoặc nhiều Object (ví dụ dashboard vận hành, API tổng hợp tồn kho) phải kiểm tra saved report của `$report-builder` trước khi thiết kế backend quét record; xem [Tận dụng báo cáo cho số liệu tổng hợp](report-data-reuse.md).

## Ba dạng Custom Frontend Module

Cả ba dạng đều được tạo, publish và kích hoạt như một Custom Frontend Module trên Workspace: cùng API quản lý, cùng Cogover Dev CLI, cùng `cogover.json` với `projectType: "frontend"` và cùng `slugSlot`. Điểm khác nằm ở việc code có phụ thuộc bộ khung của Cogover hay không và Cogover hiển thị kết quả ở đâu.

| Dạng | Bộ khung | Cogover hiển thị ở đâu | Giao tiếp với Cogover |
|---|---|---|---|
| **Single page app** | Tự chọn; không phụ thuộc bộ khung Cogover | Mở trực tiếp qua `/{slugSlot}/index.html` | Gọi API Cogover bằng cookie/session của người dùng đang đăng nhập |
| **Custom component** | Template React `custom-frontend-module-template` của Cogover, expose qua Module Federation | Nhúng vào layout của Object qua item **Federation component** với đường dẫn `{slugSlot}/Components/<TênComponent>` | Giao tiếp hai chiều với layout qua API Form Builder (`formBuilder.execScript`) và Layout Scripting |
| **Federation Page** | Cùng template React, expose qua khóa `./CustomApp` | Trang trong ứng dụng Cogover tại `/{APP_SLUG}/c{N}/{PATH}`, gắn được vào menu ứng dụng | Không giao tiếp với layout; dùng chung React, `@cogover/client-sdk` và định tuyến với Cogover |

### 1. Single page app

Ứng dụng web độc lập: tự chọn công nghệ (Vite, React, Vue, Angular hoặc TypeScript thuần), build thành static asset rồi upload. Code không phụ thuộc bộ khung của Cogover; Cogover phục vụ nguyên trạng các file đã build dưới `slugSlot` được cấp, ví dụ `https://{WORKSPACE_DOMAIN}/_cm_1/index.html`. Trang có giao diện, điều hướng và vòng đời riêng, không nằm trong khung ứng dụng Cogover.

Trang chạy cùng origin với Workspace nên gọi được API Cogover như một trang Cogover bình thường: trình duyệt tự gửi cookie session, request chạy với đúng quyền người dùng, truy cập được record Object hoặc gọi Custom Backend Module. Request ghi dữ liệu cần CSRF header lấy từ cookie session; xem [Full-stack integration](full-stack-integration.md). Cogover không có server fallback về `index.html`, nên client-side routing phải dùng hash routing.

Chọn khi đội phát triển đã có stack riêng, muốn tái sử dụng ứng dụng có sẵn, hoặc cần toàn quyền kiểm soát giao diện mà không cần đồng nhất với khung Cogover. Trường hợp thường gặp:

1. **Đưa công cụ nội bộ có sẵn lên Workspace**, ví dụ công cụ xếp ca viết bằng Vue: đổi lớp gọi API sang đọc/ghi record Cogover, giữ nguyên giao diện.
2. **Dashboard vận hành toàn màn hình** dùng thư viện biểu đồ đội đã quen, tự làm mới định kỳ, mở trên màn hình lớn.
3. **Màn hình thao tác tại hiện trường** cho tablet hoặc máy quét cầm tay: quét mã để nhập, xuất, kiểm kê rồi tạo/cập nhật record qua API.

Hướng dẫn: [Frontend quick start](get-started-custom-frontend-module.md).

### 2. Custom component

Thành phần giao diện được nhúng ngay trong layout của một Object và giao tiếp hai chiều với layout đó: layout truyền dữ liệu sang component, component đọc hoặc cập nhật giá trị field, thao tác trên Related List rồi trả kết quả về biểu mẫu. Component phải được phát triển trong template do Cogover cung cấp ([`custom-frontend-module-template`](https://github.com/cogover/custom-frontend-module-template), xây dựng trên ReactJS) để dùng chung React, bộ component `@cogover/client-sdk` và API Form Builder với Cogover. Sau khi viết xong, component được khai báo trong `exposes` của cấu hình build bằng Module Federation, rồi được thêm vào layout qua item **Federation component** với đường dẫn dạng `_cm_1/Components/<TênComponent>`. Phần thao tác trên biểu mẫu dùng `formBuilder.execScript` với cú pháp Layout Scripting.

Chọn khi cần bổ sung một thao tác hoặc một khối hiển thị ngay trên form chuẩn của Cogover mà không thay thế toàn bộ form. Trường hợp thường gặp:

1. **Kiểm tra và áp dụng mã giảm giá trên đơn hàng**: người dùng nhập mã, component kiểm tra tại chỗ hoặc qua Custom Backend Module rồi cập nhật chiết khấu cho đúng dòng sản phẩm.
2. **Chọn địa chỉ có gợi ý và bản đồ**: tích hợp dịch vụ bản đồ; khi người dùng chọn, các field tỉnh/thành, quận/huyện và tọa độ được điền tự động.
3. **Cảnh báo trùng khách hàng khi nhập liệu**: trên form Lead hoặc Account, đọc số điện thoại/email vừa nhập, tìm record trùng và hiển thị cảnh báo kèm liên kết trước khi lưu.

Hướng dẫn: [Custom component quick start](get-started-custom-component.md).

### 3. Federation Page

Trang riêng hoạt động độc lập nhưng vẫn nằm trong ứng dụng Cogover: xuất hiện dưới đường dẫn của ứng dụng dạng `https://{WORKSPACE_DOMAIN}/{APP_SLUG}/c{N}/{PATH}` và gắn được vào menu ứng dụng như một trang bình thường. Trang cũng được phát triển trong cùng template với custom component. Module đóng vai trò remote trong Module Federation và expose ứng dụng qua khóa `./CustomApp`; ứng dụng Cogover đóng vai trò host, tải `CustomApp` từ version đã publish, còn router trong module chọn page theo `path` đã khai báo trong `src/routes.tsx`. Trang không cần expose riêng và không giao tiếp với layout nào.

Chọn khi cần một màn hình nghiệp vụ riêng, đồng nhất giao diện với Cogover và đặt trong menu ứng dụng, thay vì nhúng vào một form cụ thể hoặc chạy tách biệt khỏi khung ứng dụng. Trường hợp thường gặp:

1. **Trang công cụ nghiệp vụ trong ứng dụng**: kiểm tra mã giảm giá, tra cứu bảng giá và chính sách, đặt trong menu ứng dụng Bán hàng.
2. **Trang nhập liệu hàng loạt**: tải file Excel, xem trước và đối chiếu, sửa lỗi ngay trên trang rồi tạo/cập nhật nhiều record.
3. **Trang tổng quan 360° của khách hàng**: gộp Account, đơn hàng, ticket và dữ liệu hệ thống ngoài do Custom Backend Module xử lý vào một trang.

Hướng dẫn: [Federation Page quick start](get-started-federation-page.md).

### Một project chứa nhiều dạng

Cùng một project theo template có thể expose đồng thời `./CustomApp` (Federation Page) và một hoặc nhiều `./Components/<Tên>` (custom component); single page app luôn là project riêng vì không dùng template. Chỉ gộp khi cùng nghiệp vụ, cùng nhóm bảo trì và cùng lịch phát hành: mỗi lần activate version mới ảnh hưởng mọi component và page trong project đó.

## Bảng chọn nhanh cho agent

| Câu hỏi cần trả lời từ yêu cầu và khảo sát | Kết luận |
|---|---|
| Kết quả hiển thị ở đâu? | Trong form/layout của một Object → custom component. Trang riêng trong menu ứng dụng Cogover → Federation Page. URL riêng, toàn màn hình, tablet/kiosk, ngoài khung ứng dụng → single page app. |
| Có cần đọc/ghi field, Related List hoặc hành vi của form đang mở? | Có → custom component; đây là dạng duy nhất có `formBuilder.execScript`. |
| Có cần đồng nhất giao diện, theme, i18n và điều hướng với Cogover? | Có → custom component hoặc Federation Page (template React, `@cogover/client-sdk`). Không bắt buộc → single page app. |
| Đã có ứng dụng hoặc stack riêng cần tái sử dụng (Vue, Angular, thư viện biểu đồ...)? | Có → single page app; template chỉ hỗ trợ React. |
| Cần nhiều màn hình, route và deep-link bên trong ứng dụng Cogover? | Federation Page với `src/routes.tsx`. Single page app cũng làm được nhưng phải hash routing và không nằm trong menu ứng dụng như trang Cogover. |
| Cần logic server, secret hoặc quyền nâng cao? | Không dạng frontend nào thay được: thêm Custom Backend Module và chọn dạng frontend theo các câu trên. |

Quy tắc áp dụng:

- Yêu cầu chỉ nói "màn hình riêng" hoặc "trang riêng" chưa đủ để chọn dạng. Hỏi nơi mở và mức tương tác với form trước khi đề xuất; không suy đoán.
- Đề xuất luôn kèm dạng thay thế gần nhất và lý do không chọn; lựa chọn phải được người dùng xác nhận theo mục 1A của `SKILL.md` trước khi tạo Project, clone template hoặc code.
- Người dùng đã nêu rõ dạng mong muốn nhưng phân tích cho thấy dạng khác phù hợp hơn: nêu khác biệt một lần, rồi làm theo quyết định của người dùng.
- Chức năng chuẩn của Cogover đáp ứng trọn vẹn thì không tạo module; giải thích và dùng skill chuyên trách.

## Bắt đầu

1. [Backend quick start](get-started-custom-backend-module.md)
2. [Frontend quick start](get-started-custom-frontend-module.md) (single page app)
3. [Custom component quick start](get-started-custom-component.md)
4. [Federation Page quick start](get-started-federation-page.md)
5. [Full-stack integration](full-stack-integration.md)
