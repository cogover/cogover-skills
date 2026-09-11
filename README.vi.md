# Cogover Skills

[English](README.md) | **Tiếng Việt**

Bộ 23 Agent Skills giúp trợ lý AI khảo sát và cấu hình Cogover Workspace, thiết kế dữ liệu, xây quy trình, AI Agent và phát triển Custom Module. Mỗi skill gồm `SKILL.md` cùng tài liệu API, scripts hoặc dữ liệu mẫu cần thiết.

Release hiện tại: xem [VERSION.md](VERSION.md) và [CHANGELOG.md](CHANGELOG.md). Mỗi skill có version riêng trong frontmatter và dưới tiêu đề.

## Chọn skill

| Nhu cầu | Skill |
|---|---|
| Hiểu nền tảng và chọn khả năng phù hợp | [cogover-overview](cogover-overview/SKILL.md) |
| Điều phối dự án App từ yêu cầu đến triển khai | [build-cogover-app](build-cogover-app/SKILL.md) |
| Xác thực API và quản lý credential | [cogover-api-auth](cogover-api-auth/SKILL.md) |
| Xây AI Agent, Skill, Tool, tra cứu kiến thức và kiểm thử hội thoại | [agent-builder](agent-builder/SKILL.md) |
| Xây frontend/backend tùy chỉnh | [cogover-custom-module](cogover-custom-module/SKILL.md) |
| Thiết kế schema bằng Excel | [create-cogover-objects](create-cogover-objects/SKILL.md) |
| Tra cứu và quản lý Object/field/formula | [object-info](object-info/SKILL.md) |
| Đọc/ghi record, file và ảnh rich text | [object-record](object-record/SKILL.md) |
| Bố cục giao diện Object | [object-layout](object-layout/SKILL.md) |
| Script cho logic giao diện | [layout-scripting](layout-scripting/SKILL.md) |
| Button và chuỗi hành động | [object-button](object-button/SKILL.md) |
| Bộ lọc và cột danh sách | [object-filter](object-filter/SKILL.md) |
| Biểu mẫu thu thập dữ liệu bên ngoài | [object-form](object-form/SKILL.md) |
| Quy tắc chuyển trạng thái | [object-transition-rule](object-transition-rule/SKILL.md) |
| Path Component hướng dẫn theo giai đoạn | [object-path-component](object-path-component/SKILL.md) |
| Cấu hình lịch sử thay đổi field | [object-history-tracking](object-history-tracking/SKILL.md) |
| Thành viên, cơ cấu nhân sự, role và quyền dữ liệu | [user-permission](user-permission/SKILL.md) |
| Process/BPMN và kiểm thử quy trình | [process-creator](process-creator/SKILL.md) |
| Mẫu Word/Excel/HTML và export | [document-template](document-template/SKILL.md) |
| Report Type và báo cáo | [report-builder](report-builder/SKILL.md) |
| Dashboard và biểu đồ | [dashboard-builder](dashboard-builder/SKILL.md) |
| App và menu | [app-menu-manager](app-menu-manager/SKILL.md) |
| Icon Button và App Menu | [cogover-icon](cogover-icon/SKILL.md) |

## Cài đặt và cập nhật

Tải hoặc clone repository này. Mỗi thư mục con chứa `SKILL.md` là một skill; giữ nguyên toàn bộ `references`, `scripts`, `assets` và `agents` đi kèm. Nên cài cả bộ vì các skill tham chiếu chéo và dựa vào cùng contract xác thực.

Với Codex, có thể yêu cầu `$skill-installer` cài các thư mục skill từ URL repository đã public. Hoặc sao chép các thư mục vào vị trí skill được môi trường cấu hình; Codex hỗ trợ `.agents/skills` theo repository và thư mục skill người dùng. Nếu chưa thấy thay đổi, khởi động lại Codex. Xem [hướng dẫn chính thức](https://learn.chatgpt.com/docs/build-skills).

Với agent khác hỗ trợ `SKILL.md`, làm theo cơ chế cài skill của agent đó; cú pháp gọi và công cụ đi kèm có thể khác. Bộ này không tự cài browser, thư viện spreadsheet hay runtime sub-agent.

Khi cập nhật, so sánh version, sao lưu tùy chỉnh riêng rồi thay **toàn bộ từng thư mục skill cùng tên** để không giữ tài nguyên đã bị bỏ. Không trộn hai version cùng tên hoặc ghi đè các skill không thuộc bộ này. Khi gỡ, chỉ xóa các thư mục Cogover đã cài trong bảng trên, không xóa kho skill chung.

## Điều kiện sử dụng

| Khả năng | Khi cần |
|---|---|
| Đọc skill/reference và gọi HTTP | Tất cả thao tác API |
| Workspace HTTPS và credential đúng quyền | Khảo sát hoặc thay đổi Workspace |
| Shell và Python 3.10+ | Scripts API/validator đi kèm, chỉ dùng thư viện chuẩn |
| Đọc/ghi XLSX và kiểm tra nội dung/định dạng | Thiết kế Object, report artifact, document template |
| Trình duyệt có session Workspace, theo dõi download | Kiểm thử document export; kiểm thử frontend |
| Sub-agent và artifact có phạm vi | Các bước điều phối bắt buộc của App/Custom Module |
| Node.js, Cogover Dev CLI và dependencies của starter | Custom Module; đọc tài liệu tương ứng trước khi cài |

Ưu tiên skill spreadsheet/browser của môi trường. Nếu không có skill spreadsheet, dùng công cụ XLSX tương đương và chạy validator. Nếu thiếu browser hoặc sub-agent cần thiết, agent phải báo đúng phần chưa xác minh/thực hiện; không giả lập một kết quả kiểm thử thành công.

## Workspace và xác thực

Nguồn chuẩn: [cogover-api-auth](cogover-api-auth/SKILL.md). Cấu hình origin ví dụ là `https://tennant.cogover.com`. `COGOVER_BASE_URL` và `COGOVER_API_KEY` là tên biến chung; một số ví dụ hỗ trợ tên tương thích được giải thích trong skill auth. Cấp key qua secret store hoặc scoped environment của tiến trình, không dán vào repository hoặc prompt.

| Nhóm API | Xác thực | Phạm vi |
|---|---|---|
| Public API `/bapi/v{N}` | API Key Bearer | Contract và quyền của endpoint được mô tả trong skill |
| Web App API `/api/v{N}` | Phiên Web App gồm cookie và CSRF/XSRF | Dùng khi skill có contract cho chức năng đó; không gửi API Key trực tiếp |

API Key phải có đúng quyền thao tác; không mặc định mọi công việc đều cần Super Admin. Agent đọc trạng thái, xác định phạm vi và tuân thủ cổng duyệt của skill trước thao tác có tác động. HTTP thành công chưa chứng minh thay đổi nghiệp vụ đúng; cần đọc lại và kiểm thử phù hợp.

Version của bộ skill không phải version Cogover server. Khả năng Web App API có thể phụ thuộc phiên bản Workspace. Chỉ dùng endpoint được tài liệu hỗ trợ; khi response không khớp, báo phần contract thiếu thay vì dò source riêng hoặc suy đoán endpoint.

## Bắt đầu

```text
Dùng $cogover-overview giải thích cách quản lý yêu cầu mua hàng trên Cogover.
```

```text
Dùng $object-info liệt kê các field của Object order trên Workspace tôi đã cấu hình.
Chỉ đọc thông tin và nêu những field cần cho báo cáo theo tháng.
```

```text
Dùng $build-cogover-app phân tích yêu cầu quản lý bảo hành, khảo sát Workspace
tôi đã cấu hình và chuẩn bị thiết kế để tôi duyệt trước khi triển khai.
```

## Dữ liệu mẫu và kiểm tra

Các ID và domain ví dụ là dữ liệu tổng hợp, không dùng trực tiếp để gọi Workspace. Resolve lại ID/slug/tài nguyên theo metadata đích. Snapshot response không mặc nhiên là request hợp lệ. Đọc [quy ước mẫu Process](process-creator/samples/README.md) và validator tương ứng.

Từ root repository:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/check_public_release.py
python3 -m unittest discover -s tests
```

Trước public một repo đã có commit, thêm `--history` để kiểm tra nội dung các phiên bản đã lưu trong Git. Bộ kiểm tra này không thay thế kiểm thử API/nghiệp vụ trực tiếp. Xem [CONTRIBUTING.md](CONTRIBUTING.md) và [SECURITY.md](SECURITY.md).

## Giấy phép

Nội dung do dự án cung cấp dùng [MIT](LICENSE), ngoại trừ asset bên thứ ba ghi rõ tại [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Hai SVG hoàn thành giữ license và attribution Font Awesome Free/CC BY 4.0.
