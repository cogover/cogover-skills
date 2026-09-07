---
name: object-layout
description: "Quản lý layout (bố cục giao diện) cho Cogover Object qua Layouts V2 API, gồm tạo layout thường hoặc layout nhập liệu cho Object Form (`isForm: 1`), xem, cập nhật, xoá layout, thiết kế row/column/section/tab/group/component, đưa Path Component vào layout Xem/sửa, lấy hoặc cập nhật `pageSettings.script`, và đặt Object Button vào `pageSettings.buttons.listButton` của layout xem/sửa để button xuất hiện trên màn hình bản ghi."
metadata:
  author: cogover
  version: "1.0.1"
---

# Layout Creator

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

## Kích hoạt
- Lệnh: `/object-layout`
- Người dùng có thể gọi: có

## Mô tả
Skill quản lý layout cho Cogover Object thông qua API. Hỗ trợ tạo, xem, cập nhật và xoá layout, bao gồm layout nhập liệu được Object Form sử dụng; đưa Path Component vào layout Xem/sửa; đặt Object Button lên header của màn hình xem/sửa; và quản lý script của layout. Layout mô tả giao diện hiển thị chi tiết bản ghi hoặc giao diện tạo bản ghi, gồm row, column, section, tab section, group, component và cấu hình trang.

Đọc [references/record-button-placement.md](references/record-button-placement.md) trước khi thêm, sắp xếp hoặc gỡ Object Button khỏi layout xem/sửa.

## Yêu cầu
- **API_KEY** và **WORKSPACE_DOMAIN**: resolve theo `$cogover-api-auth`, từ credential đã được cấp, scoped environment hoặc secret store của môi trường. Không dò file dự án để tìm secret.
- **Thông tin đối tượng**: Cần biết `objectTypeSlug` và danh sách fields của đối tượng. Sử dụng skill `/object-info` để lấy.

## Hướng dẫn thực hiện

### Bước 1: Đọc cấu hình
- Dùng credential đã resolve cho đúng Workspace; chỉ hỏi qua kênh an toàn khi chưa có hoặc không truy cập được.
- Nếu thiếu, hỏi người dùng.

### Nguyên tắc xác nhận

- **Mặc định không hỏi xác nhận bổ sung** cho thao tác tạo, cập nhật, đặt/gỡ Object Button hoặc xoá layout khi người dùng đã yêu cầu rõ thao tác và đích cần tác động. Sau khi đã resolve đúng tài nguyên, kiểm tra payload hợp lệ và đủ quyền, thực hiện ngay rồi xác minh kết quả.
- Chỉ hiển thị bản xem trước/tóm tắt và chờ người dùng xác nhận khi người dùng **chủ động yêu cầu** xem trước, phê duyệt hoặc xác nhận trước khi ghi.
- Nếu đích hoặc phạm vi thay đổi còn mơ hồ và các lựa chọn có thể dẫn đến kết quả khác nhau đáng kể, hỏi làm rõ phạm vi; không gọi câu hỏi làm rõ đó là bước xác nhận mặc định.
- Với thao tác xoá, vẫn phải resolve chính xác ID, nêu rõ tính không thể hoàn tác và kiểm tra tác động trước khi gọi API; không tạo thêm một lượt xác nhận nếu yêu cầu xoá đã rõ và người dùng không yêu cầu quy trình phê duyệt.

### Bước 2: Thu thập yêu cầu
Hỏi người dùng:
1. **Đối tượng nào?** (ví dụ: Lead, Product, Order...)
2. **Mô tả layout mong muốn**: bao nhiêu hàng, cột, section, tab, group và field nào ở đâu.
3. **Tên layout**: thu thập mục đích/tên mong muốn, sau đó chuẩn hoá hoặc dịch sang tiếng Anh trước khi dựng payload. Nếu người dùng không chỉ định tên, tự đặt tên tiếng Anh theo chức năng, ví dụ `Create`, `View/Edit`, `Create Order`.

Khi được `$object-form` gọi vì chưa có layout `isForm` hợp lệ, không hỏi lại các thông tin đã có và không yêu cầu xác nhận bổ sung. Dùng đúng Object đã resolve, tạo layout tên tiếng Anh theo form/Object và tự thiết kế bố cục mặc định hợp lý từ các field có thể nhập nếu người dùng chưa mô tả chi tiết. Trường hợp này bắt buộc tạo layout Web active với `functionLayout: 1`, quyền `ADD` và `isForm: 1`.

### Bước 3: Lấy thông tin đối tượng
- Gọi skill `/object-info` để lấy danh sách fields của đối tượng đã chọn.
- Từ kết quả, xác định `id`, `name`, `slug`, `fieldType`, `description` và các thuộc tính của từng field mà người dùng muốn đặt vào layout.

### Bước 4: Thiết kế bố cục giao diện (UI/UX Design)

**QUAN TRỌNG:** Trước khi xây dựng JSON, hãy đóng vai trò **chuyên gia thiết kế giao diện Web/Mobile App** để lên kế hoạch bố trí các thành phần trên layout một cách hợp lý, thuận tiện cho người dùng.

Tuân thủ các quy tắc thiết kế UI/UX sau:

#### 4.1. Hiểu ngữ cảnh trước khi thiết kế

- **Luôn đọc kỹ**: `field name`, `field slug`, `field description` + `object name/slug` để hiểu ý nghĩa và mục đích của từng trường, cũng như object dùng để làm gì.
- **Đối tượng người dùng**: Người thao tác trên giao diện bản ghi là nhân viên doanh nghiệp sử dụng hệ thống CRM, HRM, ERP,... Giao diện cần **thuận tiện, dễ thao tác, trực quan** — không cần hoa mỹ nhưng phải logic và hiệu quả.
- **Cân nhắc quy trình làm việc**: Sắp xếp các trường theo thứ tự mà người dùng thường nhập/đọc trong quy trình nghiệp vụ thực tế.

#### 4.2. Quy tắc cho Layout Tạo bản ghi (`functionLayout: 1` hoặc `3`)

- **Layout dành cho Object Form:** Khi được `$object-form` gọi để bổ sung layout nhập liệu còn thiếu, dùng `functionLayout: 1`, access control có `ADD`, `isForm: 1`, `status: 1` và `isWeb: true`. Không dùng `functionLayout: 3` cho fallback tự động này và không chuyển layout hiện có từ `isForm: 0` sang `1`.

- **Phân biệt khung trang và khung form**: Giữ `settingPage.paddingTop/Bottom/Left/Right: 0`, `settingPage.typeColor: "primary"`, `settingPage.combinationRatio: 100`; giữ `settingContentPage.maxWidth: 100`, `unitMaxWidth: "%"`, `isShowBorder: false`. `settingContentPage` vẫn chiếm toàn bộ vùng nội dung; giới hạn độ rộng form bằng thuộc tính của **Layout Row ngoài cùng**, không đổi `settingContentPage` sang `1000px`.
- **Tính độ rộng Layout Row ngoài cùng trước khi dựng JSON**:
  - Layout Tạo dạng form thông thường, không có bảng danh sách liên quan hoặc component cần nhiều không gian ngang: mặc định dùng `maxWidth: 1000`, `unitMaxWidth: "px"`, `horizontalAlignment: "center"`. `1000px` thường đủ rộng cho group 2-3 cột mà không làm input bị kéo dài quá mức; có thể chọn độ rộng khác khi số cột, loại field hoặc yêu cầu UI thực tế chứng minh cần thiết.
  - Layout Tạo có `related_list` với `typeView: "list"` để nhập danh sách con, hoặc có bảng/component rộng tương tự: dùng `maxWidth: 100`, `unitMaxWidth: "%"`, `horizontalAlignment: "center"` để giảm cuộn ngang và dành không gian cho các cột.
  - Không dùng `100%` cho form thông thường chỉ vì có nhiều field; ưu tiên chia Section/Group hợp lý và để Row ngoài cùng giới hạn, căn giữa.
- **Cấu trúc đơn giản**: Chỉ nên có **1 Layout Row** và trong Layout Column chỉ nên có **1 Layout Column**; trừ khi có lý do rõ ràng hoặc người dùng yêu cầu.
- **Gom nhóm bằng Section**: Trong Layout Column, tạo 1 hoặc nhiều Section tùy theo việc có nên gom nhóm các trường thành các khối hay không. Mỗi Section là 1 khối có border (`isBorder: true`), nên có tiêu đề (`isShowName: true`) để người dùng nhận biết. Ví dụ: layout tạo Lead có 2 section "Lead Information" và "Additional Information".
- **Trường quan trọng lên trên cùng**: Các trường chính, quan trọng nhất (tên, tiêu đề, trạng thái,...) phải nằm ở vị trí đầu tiên trong section đầu tiên.
- **Trường bắt buộc (required) ưu tiên nằm trên**: Giúp người dùng nhanh chóng điền xong các thông tin bắt buộc.
- **Bố trí cột trong Group**:
  - Trường có nội dung dài (tiêu đề, mô tả,...) → đặt trong Group có `numberOfColumns: 1` để chiếm toàn bộ chiều ngang.
  - Trường có nội dung ngắn (số điện thoại, email, trạng thái, select,...) → đặt trong Group có `numberOfColumns: 2` hoặc `3`.
  - **Các trường có ngữ nghĩa liên quan và nội dung ngắn nên nằm cùng hàng**: Ví dụ Họ và Tên là 2 trường luôn đi cùng nhau, nội dung ngắn → đặt chung trong Group `numberOfColumns: 2` thay vì tách Họ ra Group 1 cột riêng. Tương tự cho các cặp trường liên quan khác (ví dụ: Quốc gia + Thành phố, Ngày bắt đầu + Ngày kết thúc,...).
  - Hiểu rằng trong 1 Group có N cột, các trường sẽ sắp xếp **từ trái qua phải**, hết 1 hàng ngang thì trường sẽ **xuống dòng tiếp theo**.
- **Trường mô tả/ghi chú (`long_text`)**: Thường đặt ở cuối section hoặc cuối group, vì nội dung dài và không phải thông tin chính.
- **Trường boolean**: Có thể gom chung với các trường khác trong group nhiều cột; chú ý `labelPlacement: "right"` cho boolean.
- **Không đưa trường chỉ đọc/tự động vào layout tạo**: Các trường `manualModifyAllow: false`, `auto_number`, `created`, `updated`, `created_by`, `updated_by` không nên đặt vào layout tạo bản ghi (chúng sẽ tự động ẩn nếu `functionLayout: 3`, nhưng nên tránh cho gọn gàng).
- **Related list dạng bảng editable trên layout tạo bản ghi:**
  Khi object cha có object con phụ thuộc mà người dùng cần nhập ngay khi tạo bản ghi (ví dụ: Đơn hàng → Sản phẩm trong đơn hàng, Báo giá → Sản phẩm trong báo giá), cần đặt related_list với `typeView: "list"` và cấu hình `tableSettings` có `editableColumns` để người dùng có thể nhập/sửa trực tiếp trên bảng.
  - **Khi nào dùng**: Object cha có nghiệp vụ "tạo bản ghi cha kèm danh sách bản ghi con" — ví dụ tạo Đơn hàng cần nhập danh sách Sản phẩm, tạo Báo giá cần nhập danh sách Sản phẩm báo giá.
  - **Độ rộng**: Giữ `settingContentPage.maxWidth: 100`, `unitMaxWidth: "%"`, `isShowBorder: false`; đồng thời đặt **Layout Row ngoài cùng** thành `maxWidth: 100`, `unitMaxWidth: "%"`, `horizontalAlignment: "center"` để bảng có đủ chiều ngang. Không giới hạn Row này ở `1000px` trừ khi người dùng yêu cầu rõ hoặc bảng đã được chứng minh vẫn hiển thị tốt ở độ rộng đó.
  - **Vị trí đặt related list**: Đặt trong Group `numberOfColumns: 1` ở cuối section (sau các trường thông tin cơ bản của object cha).
  - **Cấu hình `editableColumns`**: Chỉ đưa các cột mà người dùng cần nhập/sửa vào `editableColumns`. **KHÔNG** đưa cột tính toán tự động (`formula`, trường có `manualModifyAllow: false`), cột hệ thống, hoặc cột lookup trỏ về object cha.
  - **Cấu hình `showingColumns`**: Loại bỏ cột lookup trỏ về object cha (vì đang tạo bản ghi cha rồi, cột này thừa). Loại bỏ cột hệ thống (`id`, `name` nếu là auto_number, `created`, `updated`, `created_by`, `updated_by`). Ưu tiên hiển thị: cột editable trước, cột tính toán/tổng sau.
  - **Tham khảo file mẫu**: `assets/sample_layout_create_order.json` — layout tạo Đơn hàng với bảng Sản phẩm trong đơn hàng có editable columns.

#### 4.3. Quy tắc cho Layout Xem/Sửa bản ghi (`functionLayout: 2` hoặc `3`)

- **Có thể tạo nhiều Layout Row** nếu cần, thông thường nên tạo 1-2 Row.
- **Bố cục nhiều cột**: 1 Layout Row có thể có N cột với tỷ lệ linh hoạt. Các mẫu phổ biến:
  - **2 cột** (sidebar + main): colSpan `1` : `2` hoặc `1` : `3` — sidebar bên trái chứa thông tin tổng quan, cột chính bên phải chứa nội dung chi tiết.
  - **3 cột** (sidebar + main + sidebar): colSpan `1` : `2` : `1` — bên trái thông tin liên hệ/tóm tắt, giữa nội dung chính + tab, bên phải thông tin bổ sung/metadata.
- **Cột sidebar (cột hẹp)**:
  - Thường chứa: avatar/ảnh (display_box), thông tin liên hệ cơ bản (họ tên, email, SĐT), thông tin tóm tắt.
  - Hoặc chứa: người sở hữu (owner), metadata (ngày tạo, ngày cập nhật, tạo bởi, cập nhật bởi), thông tin phụ.
  - Các trường trong sidebar nên dùng Group `numberOfColumns: 1` vì cột đã hẹp.
- **Cột chính (cột rộng)**:
  - Chứa trường tiêu đề/tên ở đầu (Group 1 cột).
  - Tiếp theo là các trường chính (Group 2 cột).
  - Dưới cùng có thể có **Tab-section** (`typeSection: "menu"`) chứa các danh sách liên quan (related_list), hoạt động (activities), lịch sử,...
- **Sử dụng Tab-section cho related list**: Khi có nhiều danh sách liên quan, nên gom vào 1 tab-section. Mỗi tab chứa 1 nhóm related list liên quan. Ví dụ: layout View Lead có tab "Activities", "Converted to", "Marketing Campaign".
- **Path Component:** Layout hiển thị Path Component phải là layout Xem/sửa (`functionLayout: 2`, quyền `VIEW_EDIT`); không đưa Path Component vào layout Tạo. Khi người dùng yêu cầu đưa Path Component vào layout nhưng không chỉ định vị trí, mặc định gợi ý đặt nó trong Layout Row đầu tiên; Row này thường chỉ có 1 Layout Column để Path chiếm đủ chiều ngang. Đây là gợi ý UI/UX, không phải ràng buộc schema: có thể đặt ở Row/Column khác nếu người dùng yêu cầu hoặc bố cục vẫn cấp đủ độ rộng. Với Row riêng mặc định, dùng `numberOfColumns: 1`, Column `colSpan: 1`, Group `numberOfColumns: 1`; Section thường không border và không hiện tên.
- **Trường hệ thống (metadata)**: `created`, `updated`, `created_by`, `updated_by`, `last_activity_time` nên gom vào 1 section riêng hoặc đặt ở sidebar/cột phụ, phía dưới cùng.
- **Related list dạng bảng editable trên layout xem/sửa bản ghi:**
  Tương tự layout tạo, layout xem/sửa cũng có thể chứa related list dạng bảng cho phép sửa trực tiếp (ví dụ: xem Đơn hàng và sửa Sản phẩm trong đơn hàng ngay trên bảng). Điểm khác biệt so với layout tạo:
  - **`showingColumns`**: Có thể hiển thị thêm cột tính toán/tổng kết (ví dụ: `subtotal`) so với layout tạo. Lưu ý: `_action_column` **không cần** đưa vào `showingColumns` nếu đã nằm trong `pinnedColumns.right` (cột pinned tự động hiển thị).
  - **`editableColumns`**: Giống với layout tạo — chỉ các cột người dùng cần nhập/sửa.
  - **`orderBy`**: Nên dùng `"created"` (sắp xếp theo thứ tự tạo) thay vì `"updated"` để giữ thứ tự dòng sản phẩm ổn định.
  - **Vị trí**: Đặt related list trong section riêng trên cột chính (colSpan lớn), cùng với trường lookup liên quan phía trên (ví dụ: Bảng giá nằm trên bảng Sản phẩm).
  - **Tham khảo**: Layout xem Đơn hàng `LOVDYZQENLCCE` — bố cục 2 cột (1:3), cột phải chứa bảng "Sản phẩm trong đơn hàng" editable.
- **Record-level Object Button:** Đặt các button cần xuất hiện ở header màn hình bản ghi trong `pageSettings.buttons.listButton`. Chỉ dùng button thuộc cùng `objectTypeSlug`; giữ nguyên các button hiện có; chống trùng theo `buttonId`; và view lại layout sau update. Không thêm button dạng màn danh sách vào đây.

#### 4.4. Quy tắc chung cho mọi loại layout

- **Nhóm trường theo ngữ nghĩa**: Các trường liên quan đến cùng một chủ đề nên nằm cùng 1 section hoặc cùng 1 group. Ví dụ:
  - Thông tin cá nhân: họ, tên, danh xưng, chức danh.
  - Thông tin liên lạc: email, điện thoại, di động, địa chỉ.
  - Thông tin công ty: tên công ty, ngành, doanh thu, số nhân viên, website.
- **Thứ tự ưu tiên trường**:
  1. Trường định danh (tên, tiêu đề, mã).
  2. Trường trạng thái/phân loại (status, rating, type).
  3. Trường nghiệp vụ chính (owner, giá trị, số lượng,...).
  4. Trường liên hệ (email, SĐT, địa chỉ).
  5. Trường mô tả/ghi chú (description, notes).
  6. Trường hệ thống (ngày tạo, ngày cập nhật, tạo bởi,...).
- **Không tạo group/section trống**: Mỗi group phải có ít nhất 1 field, mỗi section phải có ý nghĩa.
- **Section nên có tiêu đề rõ ràng** (`isShowName: true`) khi có từ 2 section trở lên, để người dùng phân biệt các khối thông tin. Nếu chỉ có 1 section duy nhất, có thể ẩn tiêu đề.
- **Trường lookup quan trọng (owner, assigned_to,...)**: Nên đặt ở vị trí dễ thấy — trong layout tạo thì ở section chính, trong layout xem thì ở sidebar.
- **Trường file/ảnh**: Nếu là ảnh đại diện (avatar), đặt ở đầu sidebar. Nếu là file đính kèm, đặt ở cuối section hoặc section riêng.

#### 4.5. Ví dụ tham khảo

Khi thiết kế layout, có thể tham khảo các layout mẫu đã có trên hệ thống bằng cách:
1. Gọi API list layouts của object tương tự để xem cách bố trí.
2. Gọi API view layout của object Lead để tham khảo (layout ID có thể thay đổi, cần lấy từ API list layouts của object `lead`, tìm layout có `functionLayout: 1` cho layout tạo và `functionLayout: 2` cho layout xem/sửa).
3. Dưới đây là ví dụ minh hoạ cấu trúc layout Lead để tham khảo logic bố trí:

**Không sao chép mù quáng `content` từ layout tham khảo:** Layout lấy qua API chỉ dùng để tham khảo cấu trúc. Trước khi tái sử dụng bất kỳ phần nào của `content`, phải xác minh đó là array không rỗng và có đủ chuỗi phân cấp `layoutRow → layoutColumn → section → tab → group → component`. Nếu `content` là `null`, không phải array, `[]`, hoặc có cấp con rỗng, không dùng nó làm payload tạo mới; phải dựng layout hợp lệ từ fields của object và asset mẫu.

**Layout tạo Lead** (1 Row, 1 Column, 2 Section):
```
Row 0 (1 cột, maxWidth 1000px, căn giữa)
└── Column 0
    ├── Section "Lead Information" (border, hiện tên)
    │   ├── Group 1 cột: Title (trường tiêu đề duy nhất - chiếm toàn bộ chiều rộng)
    │   └── Group 2 cột: Họ, Tên, Trạng thái, Owner, Mức độ, Danh xưng, Chức danh, Nguồn, SĐT, Email, Mô tả, Địa chỉ
    │       (Lưu ý: Họ và Tên nằm cùng hàng trong Group 2 cột vì cùng ngữ nghĩa và nội dung ngắn)
    └── Section "Additional Information" (border, hiện tên)
        └── Group 2 cột: Công ty, Doanh thu, Ngành, Số NV, Website, SĐT công ty, Không gọi điện
```

**Layout xem/sửa Lead** (2 Row, Row chính 3 cột tỷ lệ 1:2:1):
```
Row 0 (1 cột) — Path component
Row 1 (3 cột, colSpan 1:2:1)
├── Column trái (sidebar liên hệ)
│   └── Section (border): Display box, Họ, Tên, Công ty, Chức danh, Danh xưng, Email, SĐT, Không gọi điện, Địa chỉ, Nguồn, Mô tả
├── Column giữa (nội dung chính)
│   ├── Section: Title (1 cột), Trạng thái + Mức độ (2 cột)
│   └── Tab-section: [Activities] [Converted to] [Marketing Campaign]
└── Column phải (thông tin bổ sung)
    └── Section "Other Information": Owner, Công ty, Ngành, Doanh thu, Số NV, SĐT công ty, Website, Last activity, Tạo lúc, Cập nhật lúc, Tạo bởi, Cập nhật bởi
```

**Layout tạo Đơn hàng** (1 Row, 1 Column, 1 Section — có related list editable):
```
Row 0 (1 cột, maxWidth 100%, căn giữa vì có bảng related list)
└── Column 0
    └── Section (border)
        ├── Group 2 cột: Owner, Khách hàng, Trạng thái, Bảng giá
        ├── Group 2 cột: Báo giá, Hợp đồng, Địa chỉ thanh toán, Địa chỉ giao hàng
        └── Group 1 cột: Mô tả, Related List "Sản phẩm trong đơn hàng" (typeView: "list")
            └── tableSettings:
                showingColumns: [product, quantity, price_per_unit, unit, discount_by_unit, tax_by_unit, fee_by_unit, total_price, _action_column]
                editableColumns: [product, quantity, price_per_unit, unit, discount_by_unit, tax_by_unit, fee_by_unit]
                (Lưu ý: total_price là trường tính toán → KHÔNG editable)
                (Lưu ý: cột "order" (lookup về Order) bị loại khỏi showingColumns vì thừa)
```
Tham khảo: `assets/sample_layout_create_order.json`

**Layout xem/sửa Đơn hàng** (1 Row, 2 Column tỷ lệ 1:3 — có related list editable):
```
Row 0 (2 cột, colSpan 1:3)
├── Column trái (sidebar)
│   ├── Section (border): Mã đơn hàng, Owner, Hợp đồng, Báo giá, Khách hàng, Cơ hội, Thời điểm kích hoạt, Ngày hiệu lực, Ngày kết thúc
│   └── Section (border): Mô tả, Địa chỉ giao hàng, Địa chỉ thanh toán, Cập nhật lúc, Cập nhật bởi, Tạo lúc, Tạo bởi
└── Column phải (nội dung chính)
    ├── Section (border): Group 2 cột — Status, Liên hệ vận chuyển, Liên hệ thanh toán, Ủy quyền công ty, Ủy quyền KH, Ngày ủy quyền
    └── Section (border): Bảng giá, Related List "Sản phẩm trong đơn hàng" (typeView: "list")
        └── tableSettings:
            showingColumns: [product, quantity, price_per_unit, unit, discount_by_unit, tax_by_unit, fee_by_unit, subtotal, total_price]
            editableColumns: [product, unit, quantity, price_per_unit, discount_by_unit, tax_by_unit, fee_by_unit]
            listAction: [CREATE_PRODUCT_LINE, DELETE]
            orderBy: "created"
            (Lưu ý: _action_column KHÔNG cần trong showingColumns khi đã pinned)
            (Lưu ý: Có thêm subtotal so với layout tạo)
```
Tham khảo: Layout ID `LOVDYZQENLCCE` trên hệ thống (object `order`).

### Bước 5: Xây dựng JSON layout
- Đọc file mẫu tại `assets/sample_layout_1.json` để tham khảo cấu trúc JSON thực tế.
- Xây dựng JSON layout theo cấu trúc bên dưới, **tuân thủ các quy tắc UI/UX ở Bước 4**.
- **QUAN TRỌNG: KHÔNG tạo file JSON.** JSON layout chỉ được xây dựng trong bộ nhớ (biến) để gửi qua API ở Bước 7. Mục tiêu cuối cùng luôn là gọi API tạo/cập nhật layout trên hệ thống, không phải tạo file cục bộ.
- **Tên layout (`name`) bắt buộc luôn bằng tiếng Anh.** Không có ngoại lệ theo ngôn ngữ đầu vào: nếu người dùng cung cấp tên không phải tiếng Anh, tự dịch sang tên tiếng Anh tự nhiên trước khi gọi API. Giữ tên ngắn gọn, mô tả đúng chức năng, ví dụ `Create`, `View/Edit`, `Create Order`; không gửi tên như `Tạo`, `Xem`, `Chỉnh sửa` trong payload.
- **Mọi slug do skill sinh phải bằng tiếng Anh**, dùng chữ thường và `snake_case`, kể cả khi tên layout hoặc tên hiển thị của thành phần dùng ngôn ngữ khác. Không dịch hoặc tự đổi các slug tham chiếu đã tồn tại trên hệ thống như Object Field slug, `originSlug`, `dashboardSlug` hoặc `pathComponentSlug`.
- **Đặt `isForm` có chủ đích:** Dùng `isForm: 1` chỉ khi người dùng yêu cầu layout cho Object Form hoặc khi `$object-form` gọi fallback; các layout khác dùng `isForm: 0` hoặc giữ mặc định backend. Không suy diễn layout Add thông thường là layout form-compatible.

### Bước 6: Hoàn tất và kiểm tra layout
- Kiểm tra lại cấu trúc layout và payload trước khi gọi API.
- **Bắt buộc chặn payload rỗng trước API:** Chỉ gọi `POST /bapi/v1/layouts_v2` khi `content` là array và `content.length > 0`. Kiểm tra đệ quy mỗi `layoutRow` có ít nhất 1 `layoutColumn`, mỗi `layoutColumn` có ít nhất 1 `section`, mỗi `section` có ít nhất 1 `tab`, mỗi `tab` có ít nhất 1 `group`, và mỗi `group` có ít nhất 1 `component`.
- **Bắt buộc kiểm tra độ rộng Layout Row ngoài cùng cho layout Tạo:** Nếu không có component bảng rộng, xác nhận Row ngoài cùng thường có `maxWidth: 1000`, `unitMaxWidth: "px"`, `horizontalAlignment: "center"`; nếu có `related_list.typeView: "list"` hoặc bảng rộng tương tự, xác nhận Row ngoài cùng có `maxWidth: 100`, `unitMaxWidth: "%"`, `horizontalAlignment: "center"`. Không nhầm các thuộc tính này với `pageSettings.settingContentPage`.
- **Bắt buộc kiểm tra tên layout:** Trước mọi request tạo layout hoặc request có thay đổi `name`, xác nhận `name` là tiếng Anh. Nếu đầu vào là ngôn ngữ khác, dịch sang tiếng Anh trước khi gửi; không coi việc người dùng cung cấp tên không phải tiếng Anh là ngoại lệ.
- **Bắt buộc kiểm tra layout cho Object Form:** Khi được `$object-form` gọi, xác nhận payload có `functionLayout: 1`, access control `ADD`, `isForm: 1`, `status: 1` và `isWeb: true`. Sau create, view/list lại layout và chỉ trả ID cho `$object-form` khi các giá trị này cùng `objectTypeSlug` đều khớp.
- Nếu layout tham khảo trả `content: null`, `content: []` hoặc có cấp con rỗng, không gửi payload đó và không thử lại cùng payload. Dựng `content` mới từ thông tin fields của object theo cấu trúc trong asset mẫu, sau đó chạy lại toàn bộ kiểm tra ở bước này.
- **Mặc định không hỏi người dùng xác nhận**: sau khi đã có đủ thông tin và payload hợp lệ, chuyển ngay sang Bước 7 để tạo layout.
- Chỉ hiển thị bản xem trước/tóm tắt và chờ xác nhận nếu người dùng **chủ động yêu cầu** xem trước hoặc xác nhận trước khi tạo. Khi đó, chỉ gọi API sau khi người dùng đồng ý.

### Bước 7: Gọi API tạo layout
- Gọi API `POST /bapi/v1/layouts_v2` để tạo layout trên hệ thống.
- Hiển thị kết quả (ID, tên, slug của layout vừa tạo).
- Gửi link truy cập layout cho người dùng: `https://{WORKSPACE_DOMAIN}/settings/object/{OBJECT_SLUG}/layout/{LAYOUT_ID}` (trong đó `OBJECT_SLUG` là slug đối tượng, `LAYOUT_ID` là ID layout vừa tạo).

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "objectTypeSlug": "{OBJECT_SLUG}",
    "name": "Create",
    "functionLayout": 3,
    "isForm": 0,
    "content": [ ... ],
    "pageSettings": { ... }
  }'
```

Khi request này được gọi để bổ sung layout cho `$object-form`, thay bằng `functionLayout: 1`, `isForm: 1`, access control `ADD`, `status: 1` và `isWeb: true` như các bước kiểm tra ở trên.

---

## Các khả năng bổ sung

### Khả năng B: Xem danh sách layout của đối tượng

Sử dụng khi người dùng muốn xem các layout hiện có của một đối tượng.

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/list' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "objectTypeSlug": "{OBJECT_SLUG}",
    "limit": 2000,
    "page": 1
  }'
```

Hiển thị kết quả dạng bảng: ID, tên, slug, functionLayout, isWeb, isMobile, status.

### Khả năng C: Xem chi tiết layout

Sử dụng khi người dùng muốn xem chi tiết một layout cụ thể.

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/view' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "id": "{LAYOUT_ID}"
  }'
```

### Khả năng D: Lấy script đang có sẵn trên layout

Sử dụng khi người dùng muốn xem/lấy script hiện tại của một layout. Script nằm tại `pageSettings.script`.

**Quy trình:**
1. Lấy chi tiết layout hiện tại bằng API view.
2. Đọc `data.pageSettings.script`.
3. Nếu giá trị là `null`, rỗng hoặc không tồn tại, trả lời rõ: layout hiện chưa có script.
4. Chỉ hiển thị nội dung script, không tự chỉnh sửa layout.

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/view' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "id": "{LAYOUT_ID}"
  }'
```

Ví dụ trích xuất script bằng `jq`:

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/view' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{"id":"{LAYOUT_ID}"}' \
| jq -r '.data.pageSettings.script // ""'
```

### Khả năng E: Cập nhật script cho một layout

Sử dụng khi người dùng muốn thêm, thay hoặc xoá script của một layout. Chỉ thay đổi tham số `pageSettings.script`, không thay đổi `content`, `title`, quyền truy cập hoặc các cấu hình khác nếu người dùng không yêu cầu.

**Quy trình bắt buộc:**
1. Lấy chi tiết layout hiện tại bằng API view.
2. Từ `data` vừa nhận, dựng payload update theo đúng allowlist của API v2: `name`, `objectTypeSlug`, `status`, `type`, `updateRecordMode`, `accessControls`, `hasComponentPath`, `content`, `title`, `pageSettings`, `functionLayout`, `isWeb`, `isMobile`. Không gửi nguyên raw `data` vì response có các trường server-managed mà API update không nhận.
3. Giữ nguyên giá trị hiện tại của tất cả trường trong allowlist, chỉ cập nhật `pageSettings.script` bằng script mới. Nếu người dùng muốn xoá script, set `pageSettings.script` thành `""` hoặc `null` theo payload hiện tại của hệ thống.
4. Gửi payload qua `PUT /bapi/v1/layouts_v2/{LAYOUT_ID}`. Không tự tạo lại `content` từ đầu và không gửi payload rút gọn chỉ gồm `name`, `content`, `pageSettings`.
5. Gọi lại API view và kiểm tra `data.pageSettings.script` đã đúng script mới.
6. Nếu API v2 lỗi xác thực, không nhận payload hoặc không lưu đúng script, báo nguyên nhân và thông báo lỗi từ response cho người dùng rồi dừng. Không đổi sang endpoint hoặc cơ chế xác thực khác.

**Endpoint update duy nhất cho script:**

Chỉ sử dụng `PUT /bapi/v1/layouts_v2/{LAYOUT_ID}` với `Authorization: Bearer {API_KEY}`.

```bash
curl --silent --location --request PUT 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/{LAYOUT_ID}' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "name": "Current Layout",
    "objectTypeSlug": "{OBJECT_SLUG}",
    "status": 1,
    "type": 2,
    "updateRecordMode": 4,
    "accessControls": [ ... giữ nguyên từ layout hiện tại ... ],
    "hasComponentPath": "<giữ nguyên giá trị hiện tại>",
    "content": [ ... giữ nguyên từ layout hiện tại ... ],
    "title": { ... giữ nguyên từ layout hiện tại ... },
    "pageSettings": {
      "...": "... giữ nguyên các key hiện tại ...",
      "script": "SCRIPT_MOI_DA_ESCAPE"
    },
    "functionLayout": 2,
    "isWeb": true,
    "isMobile": false
  }'
```

**Cách build payload an toàn bằng `jq`:**

```bash
SCRIPT_FILE="/tmp/layout-script.js"

curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/view' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{"id":"{LAYOUT_ID}"}' \
| jq --rawfile script "$SCRIPT_FILE" '
    .data
    | {
        name,
        objectTypeSlug,
        status,
        type,
        updateRecordMode,
        accessControls,
        hasComponentPath,
        content,
        title,
        pageSettings: ((.pageSettings // {}) + {script: $script}),
        functionLayout,
        isWeb: (.isWeb == true or .isWeb == 1),
        isMobile: (.isMobile == true or .isMobile == 1)
      }
  ' \
> /tmp/layout-update.json

curl --silent --location --request PUT 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/{LAYOUT_ID}' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data @/tmp/layout-update.json
```

**Lưu ý quan trọng:**
- Luôn cập nhật trên layout hiện tại vừa lấy từ API để tránh ghi đè thay đổi mới của người khác.
- Không gửi payload chỉ có `pageSettings.script` hoặc payload rút gọn chỉ gồm `name`, `content`, `pageSettings`; API v2 cần các trường trong allowlist nêu trên.
- Không gửi nguyên raw `data` của response view; loại bỏ các trường server-managed như `id`, `slug`, `created`, `updated`, `createdBy`, `updatedBy`, `workspaceId`, `objectTypeId`, `contentCompiled`.
- Không sửa escape thủ công nếu có thể dùng `jq --rawfile`; cách này giữ nguyên xuống dòng và dấu nháy trong JavaScript.
- Sau khi update, bắt buộc đọc lại layout và so sánh `pageSettings.script`.
- Nếu update hoặc bước xác minh thất bại, báo lỗi cho người dùng và dừng; không fallback sang endpoint hoặc cơ chế xác thực khác.

### Khả năng F: Cập nhật layout

Sử dụng khi người dùng muốn sửa một layout đã có.

**Quy trình:**
1. Lấy chi tiết layout hiện tại bằng API view.
2. Hiển thị cấu trúc hiện tại cho người dùng.
3. Thu thập yêu cầu thay đổi.
4. Xây dựng JSON layout mới.
5. **Mặc định cập nhật ngay** sau khi yêu cầu đã rõ và payload hợp lệ; không hỏi xác nhận bổ sung. Chỉ hiển thị tóm tắt và chờ xác nhận nếu người dùng chủ động yêu cầu xem trước hoặc phê duyệt trước khi ghi.
6. Dựng payload theo allowlist giống mục cập nhật script; giữ nguyên các trường cấu hình không được yêu cầu thay đổi và không gửi các trường server-managed từ response view.
7. Sau khi update, gọi API view để xác minh các thay đổi đã được lưu đúng. Nếu API v2 trả lỗi hoặc kết quả xác minh sai, báo lỗi cho người dùng và dừng.

```bash
curl --silent --location --request PUT 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/{LAYOUT_ID}' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "name": "Updated Layout",
    "objectTypeSlug": "{OBJECT_SLUG}",
    "status": 1,
    "type": 2,
    "updateRecordMode": 4,
    "accessControls": [ ... giữ nguyên hoặc cập nhật theo yêu cầu ... ],
    "hasComponentPath": "<giữ nguyên giá trị hiện tại>",
    "content": [ ... ],
    "title": { ... },
    "pageSettings": { ... },
    "functionLayout": 3,
    "isWeb": true,
    "isMobile": false
  }'
```

### Khả năng G: Xoá layout

Sử dụng khi người dùng muốn xoá một layout.

**Quy trình:**
1. Hiển thị thông tin layout sẽ bị xoá (ID, tên, slug, đối tượng).
2. **Cảnh báo rõ ràng rằng hành động này không thể hoàn tác.**
3. Nếu yêu cầu xoá và đích đã rõ, gọi API ngay sau các bước kiểm tra bắt buộc; không hỏi xác nhận bổ sung. Chỉ chờ xác nhận khi người dùng chủ động yêu cầu quy trình xem trước/phê duyệt, hoặc hỏi làm rõ khi có nhiều layout có thể khớp và chưa thể resolve an toàn.

```bash
curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/delete' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "data": ["{LAYOUT_ID}"]
  }'
```

Sau khi API trả thành công, gọi API list hoặc view để xác minh layout không còn tồn tại. Nếu xóa thất bại, báo lỗi cho người dùng; không đổi sang endpoint khác.

### Khả năng H: Đặt Object Button lên layout xem/sửa

Sử dụng khi một record-level Object Button đã tồn tại nhưng cần xuất hiện trên giao diện xem một bản ghi.

**Quy trình bắt buộc:**

1. Gọi Object Buttons API `view` để xác minh button, lấy `id`, `slug`, `objectTypeSlug`, trạng thái và icon. Không đoán ID/slug từ tên.
2. Xác nhận button không phải loại chỉ hiển thị trên màn danh sách. Với list action như `16`/`19` hoặc luồng list/bulk tương ứng, cấu hình ở màn danh sách/filter thay vì record layout.
3. Resolve layout đích bằng ID hoặc list layout của Object. Chỉ chọn layout cùng `objectTypeSlug` và có chức năng xem/sửa (`functionLayout: 2`, hoặc `3` có quyền `VIEW_EDIT`). Nếu có nhiều layout theo quyền hoặc web/mobile, không tự cập nhật tất cả; yêu cầu người dùng chọn khi chưa đủ ngữ cảnh.
4. Gọi `POST /bapi/v1/layouts_v2/view` ngay trước khi sửa. Đọc `pageSettings.buttons`; nếu chưa có, khởi tạo theo schema trong [references/record-button-placement.md](references/record-button-placement.md).
5. Kiểm tra `listButton` theo `buttonId`. Nếu đã có, không thêm bản sao; chỉ đổi cấu hình hiển thị khi người dùng yêu cầu.
6. Giữ nguyên thứ tự và toàn bộ entry hiện có. Chèn entry mới ở vị trí người dùng yêu cầu; nếu không chỉ định, append vào cuối. Dùng ID, slug và icon thật của button; dùng mặc định quan sát được `type: "gray"`, `size: "medium"`, `customName: null` khi người dùng không yêu cầu kiểu khác.
7. Hiển thị tóm tắt layout đích, vị trí và entry sẽ thêm khi hữu ích, rồi mặc định tiếp tục cập nhật ngay. Chỉ chờ xác nhận nếu người dùng chủ động yêu cầu xem trước hoặc phê duyệt trước khi ghi.
8. Dựng payload update từ trạng thái layout mới nhất theo allowlist: `name`, `objectTypeSlug`, `status`, `type`, `updateRecordMode`, `accessControls`, `hasComponentPath`, `content`, `title`, `pageSettings`, `functionLayout`, `isWeb`, `isMobile`. Chỉ thay đổi `pageSettings.buttons`; không gửi raw response và không làm lại `content`.
9. Gọi `PUT /bapi/v1/layouts_v2/{LAYOUT_ID}`, sau đó view lại layout. Chỉ báo thành công khi đúng `pageSettings.buttons.listButton` chứa một entry duy nhất có `buttonId` mục tiêu và các button cũ vẫn được giữ nguyên.

Việc gỡ button khỏi layout chỉ làm button không còn hiển thị trên layout đó; không xóa định nghĩa Object Button. Ngược lại, xóa Object Button không tự bảo đảm mọi layout đã loại bỏ tham chiếu, nên phải kiểm tra các layout liên quan trước khi xóa.

### Khả năng I: Đưa Path Component vào layout Xem/sửa

Sử dụng khi Path Component đã tồn tại trên Object và người dùng muốn hiển thị nó trong layout của màn hình bản ghi.

**Nguyên tắc bắt buộc:**

- Layout đích phải là layout Xem/sửa: `functionLayout: 2` và access control có `VIEW_EDIT`. Không đưa Path Component vào layout Tạo (`functionLayout: 1`) hoặc layout Tạo/Xem/Sửa (`functionLayout: 3`).
- Path Component phải active và thuộc cùng `objectTypeSlug` với layout. Dùng `$object-path-component` ở thao tác read để resolve Path theo ID/URL/slug; không đoán slug.
- Layout component **không lưu Path ID** dạng `PC...`. Nó lưu slug thật của Path trong `pathComponentSlug`. Nếu người dùng cung cấp URL hoặc ID Path, phải resolve detail rồi lấy `path.slug`.
- `id` của component trong layout là UUID v4 mới, không phải Path ID và không phải Object Field ID. Path Component không cần `fieldMetaData`.
- Duyệt đệ quy toàn bộ `content` trước khi thêm. Nếu đã có đúng một component với cùng `pathComponentSlug`, coi thao tác là idempotent và không thêm bản sao. Nếu có nhiều bản sao hoặc có Path khác tại vị trí đích, báo rõ; không tự xóa hay thay thế component hiện có.
- Giữ nguyên `hasComponentPath` đúng như layout detail vừa trả về, kể cả khi giá trị là `null`. Không tự set `1`: layout thật có Path Component trong `content` đã được quan sát với `hasComponentPath: null`.

**Gợi ý vị trí khi người dùng không chỉ định:**

- Chèn một Layout Row mới ở đầu `content`.
- Row thường có 1 Layout Column; Column chứa Section `normal`, 1 Tab, 1 Group `numberOfColumns: 1`, và Group chứa Path Component.
- Row/Column/Section/Group thường không border, không hiện tên và không padding để Path có đủ chiều ngang.
- Cấu trúc trên là gợi ý UI/UX, không phải ràng buộc schema. Nếu người dùng chỉ định vị trí khác, hoặc layout hiện có Row/Column đủ rộng, đặt Path tại đó và vẫn tuân thủ hierarchy `Row → Column → Section → Tab → Group → components`.

**Schema component đã quan sát từ Layouts V2:**

```json
{
  "useLayouts": [2],
  "pathComponentSlug": "contract_status_path",
  "isPinned": false,
  "name": "path_component",
  "uiSlug": "path_component_contract_status_1",
  "id": "<uuid-v4>",
  "label": "path_component",
  "fieldType": "path_component",
  "slug": "path_component_contract_status",
  "status": 1
}
```

- `pathComponentSlug` phải giữ nguyên slug thật đã resolve; trong ví dụ trên là `contract_status_path`.
- `slug` và `uiSlug` là identity của **layout component**, không phải slug của Path. Khi tạo mới, sinh slug tiếng Anh, `snake_case`, có tiền tố `path_component_`, kiểm tra unique toàn hệ thống và sinh `uiSlug` tương ứng. Khi di chuyển component hiện có, giữ nguyên `id`, `slug` và `uiSlug`.
- `useLayouts: [2]` và `status: 1` là cấu hình đã xác minh cho Path Component trên layout Xem/sửa; `isPinned` mặc định là `false` nếu người dùng không yêu cầu khác.

**Cấu trúc Row mặc định tối giản:**

```json
{
  "id": "<row-uuid>",
  "type": "layoutRow",
  "numberOfColumns": 1,
  "gap": 20,
  "slug": "layout_row_contract_status_path",
  "isShowChildren": true,
  "isBorder": false,
  "paddingLeft": 0,
  "paddingRight": 0,
  "paddingTop": 0,
  "paddingBottom": 0,
  "children": [
    {
      "id": "<column-uuid>",
      "type": "layoutColumn",
      "colSpan": 1,
      "name": null,
      "slug": "layout_column_contract_status_path",
      "isShowName": false,
      "isShowChildren": true,
      "isBorder": false,
      "paddingLeft": 0,
      "paddingRight": 0,
      "paddingTop": 0,
      "paddingBottom": 0,
      "gap": 20,
      "children": [
        {
          "id": "<section-uuid>",
          "type": "section",
          "typeSection": "normal",
          "numberOfTabs": 1,
          "name": null,
          "slug": "section_contract_status_path",
          "isShowName": false,
          "isShowChildren": true,
          "isBorder": false,
          "paddingLeft": 0,
          "paddingRight": 0,
          "paddingTop": 0,
          "paddingBottom": 0,
          "gap": 20,
          "displayUnderline": false,
          "children": [
            {
              "id": "<tab-uuid>",
              "name": null,
              "slug": "tab_contract_status_path",
              "isShowChildren": true,
              "children": [
                {
                  "id": "<group-uuid>",
                  "type": "group",
                  "name": null,
                  "slug": "group_contract_status_path",
                  "numberOfColumns": 1,
                  "canCollapse": false,
                  "isShowName": false,
                  "isShowChildren": true,
                  "isBorder": false,
                  "paddingLeft": 0,
                  "paddingRight": 0,
                  "paddingTop": 0,
                  "paddingBottom": 0,
                  "gap": 12,
                  "tabKey": 1,
                  "components": [
                    {
                      "id": "<component-uuid>",
                      "fieldType": "path_component",
                      "status": 1,
                      "slug": "path_component_contract_status",
                      "name": "path_component",
                      "label": "path_component",
                      "uiSlug": "path_component_contract_status_1",
                      "useLayouts": [2],
                      "pathComponentSlug": "contract_status_path",
                      "isPinned": false
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**Quy trình update bắt buộc:**

1. Resolve Path detail và layout detail mới nhất. Xác minh Path active, cùng Object; layout `functionLayout: 2`, có `VIEW_EDIT` và `content` hợp lệ.
2. Duyệt tất cả `group.components` để kiểm tra trùng `pathComponentSlug` và thu thập mọi `id`, `slug`, `uiSlug` đang tồn tại.
3. Dựng component theo schema trên. Nếu người dùng không chỉ định vị trí, dựng Row mới và prepend vào `content`; nếu có vị trí cụ thể, merge component vào Group đích mà không dựng lại phần còn lại.
4. Kiểm tra hierarchy không rỗng, UUID và slug unique, và mỗi `pathComponentSlug` mục tiêu chỉ xuất hiện một lần. Không áp dụng yêu cầu Object Field ID/`fieldMetaData` cho Path Component.
5. Dựng payload update theo allowlist: `name`, `objectTypeSlug`, `status`, `type`, `updateRecordMode`, `accessControls`, `hasComponentPath`, `content`, `title`, `pageSettings`, `functionLayout`, `isWeb`, `isMobile`. Giữ nguyên mọi giá trị không được yêu cầu thay đổi, đặc biệt là `hasComponentPath`; không gửi các field server-managed.
6. Gọi `PUT /bapi/v1/layouts_v2/{LAYOUT_ID}` bằng API Key Bearer.
7. View lại layout ngay sau update. Chỉ báo thành công khi: layout vẫn là `functionLayout: 2`; có đúng một component active với `fieldType: "path_component"` và `pathComponentSlug` mục tiêu; component nằm đúng vị trí; và các Row/component cũ cùng các top-level setting không bị thay đổi ngoài diff đã dự kiến.

---

## Phân loại Layout theo chức năng

| Loại | `functionLayout` | `accessControls.functions` | Mô tả |
|------|-------------------|---------------------------|--------|
| **Xem/Sửa** | `2` | `["VIEW_EDIT"]` | Dùng để xem và cập nhật 1 bản ghi |
| **Tạo** | `1` | `["ADD"]` | Dùng để tạo 1 bản ghi mới |
| **Tạo/Xem/Sửa** | `3` | `["ADD", "VIEW_EDIT"]` | Dùng chung cho cả tạo, xem và cập nhật bản ghi. Với loại này, các trường chỉ đọc (`manualModifyAllow: false`) và trường auto_number sẽ tự động ẩn khi tạo bản ghi |

---

## Cấu trúc JSON Layout

### Cấu trúc tổng quan (top-level)

```json
{
  "name": "Create",
  "objectTypeSlug": "slug_doi_tuong",
  "status": 1,
  "type": 2,
  "updateRecordMode": 4,
  "accessControls": [
    {
      "functions": ["ADD", "VIEW_EDIT"],
      "option": 1,
      "items": [],
      "type": "personnel"
    }
  ],
  "hasComponentPath": 0,
  "content": [ /* mảng các layoutRow */ ],
  "title": {
    "id": "<uuid>",
    "slug": "title_<timestamp>",
    "value": "",
    "valueType": "html",
    "valueIsRaw": false,
    "valuePathName": "",
    "valueDataType": "",
    "isShowTitle": true,
    "isShowHelpText": false,
    "helpText": ""
  },
  "pageSettings": { /* xem mục Page Settings */ },
  "functionLayout": 3,
  "isWeb": true,
  "isMobile": false,
  "isForm": 0
}
```

**Giải thích các trường top-level:**

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `name` | String | Tên hiển thị của layout; bắt buộc bằng tiếng Anh |
| `objectTypeSlug` | String | Slug của đối tượng (ví dụ: `product`, `lead`) |
| `status` | Number | Trạng thái: `1` = active |
| `type` | Number | Loại layout: `0` = Custom layout, `1` = Standard layout, `2` = record detail. Mặc định: `2` |
| `updateRecordMode` | Number | Chế độ cập nhật: `4` = mặc định |
| `accessControls` | Array | Quyền truy cập. Hỗ trợ 4 loại `type`: `"personnel"` (theo nhân sự), `"position"` (theo chức vụ), `"department"` (theo phòng ban), `"role"` (theo vai trò). `option: 1` = tất cả, `option: 2` = chỉ định cụ thể (kèm `items`) |
| `hasComponentPath` | Number/null | Metadata top-level có thể là `0`, `1` hoặc `null`. Không suy diễn sự hiện diện của Path Component chỉ từ trường này: layout thật có `path_component` trong `content` có thể vẫn trả `hasComponentPath: null`. Khi update, giữ nguyên giá trị response hiện tại; không tự đổi thành `1` hoặc chuẩn hoá `null` thành `0` chỉ vì thêm Path Component. Xác định Path bằng cách duyệt `content` tìm `fieldType: "path_component"`. |
| `content` | Array | Mảng các `layoutRow` - nội dung chính của layout |
| `title` | Object | Cấu hình tiêu đề trang. Gồm: `value` (nội dung), `valueType` (`"text"`, `"html"`, `"react"`, `"markdown"`), `valueIsRaw` (nội dung raw), `valuePathName` (tham chiếu data path), `valueDataType` (kiểu dữ liệu), `isShowTitle` (hiển thị tiêu đề), `isShowHelpText` (hiển thị help text), `helpText` (nội dung help text) |
| `pageSettings` | Object | Cấu hình trang (padding, màu sắc, breadcrumb, ...) |
| `functionLayout` | Number | Loại layout: `1` = Tạo, `2` = Xem/Sửa, `3` = Tạo/Xem/Sửa (xem mục "Phân loại Layout theo chức năng") |
| `isWeb` | Boolean | Dùng cho web |
| `isMobile` | Boolean | Dùng cho mobile |
| `isForm` | Number/Boolean | `1`/`true` = layout nhập liệu có thể được Object Form chọn; `0`/`false` = layout thường. Khi `$object-form` gọi fallback, bắt buộc đặt `1` và post-check lại |

---

### Phân cấp layout (hierarchy)

```
content (mảng)
└── layoutRow
    └── layoutColumn
        └── section / tab-section
            └── tab
                └── group
                    └── components (mảng field)
```

---

### ⚠️ CÁC LỖI THƯỜNG GẶP KHI XÂY DỰNG JSON LAYOUT (BẮT BUỘC ĐỌC)

**Khi xây dựng JSON layout, PHẢI tuân thủ đúng format sau. Không tuân thủ sẽ gây lỗi "Cannot read properties of undefined (reading 'map')" trên giao diện.**

#### Quy tắc bắt buộc:

1. **Dùng `type` cho container, KHÔNG dùng `fieldType`:**
   - ✅ `"type": "layoutRow"` / `"type": "layoutColumn"` / `"type": "section"` / `"type": "group"`
   - ❌ `"fieldType": "layoutRow"` / `"fieldType": "layoutColumn"` / `"fieldType": "section"` / `"fieldType": "group"`

2. **Dùng `children` để chứa phần tử con, KHÔNG dùng tên riêng:**
   - ✅ layoutRow → `"children": [layoutColumn, ...]`
   - ✅ layoutColumn → `"children": [section, ...]`
   - ✅ section → `"children": [tab, ...]`
   - ✅ tab → `"children": [group, ...]`
   - ❌ `"layoutColumns": [...]` / `"sections": [...]` / `"tabs": [...]` / `"groups": [...]`

3. **Group dùng `components` (KHÔNG phải `children`) để chứa field:**
   - ✅ group → `"components": [field1, field2, ...]`

4. **Field nằm TRỰC TIẾP trong mảng `components`, KHÔNG bọc trong object `component`:**
   - ✅ `"components": [{"id": "OF...", "name": "Name", "fieldType": "short_text", ...}]`
   - ❌ `"components": [{"component": {"fieldName": "Name", ...}, "fieldType": "component"}]`

5. **`id` của Object Field là Object Field ID (dạng `OF...`), KHÔNG phải UUID:**
   - ✅ `"id": "OF00000000002"`
   - ❌ `"id": "00000000-0000-4000-8000-000000000050"`
   - Ngoại lệ: component đặc biệt không phải Object Field, như `path_component`, dùng UUID v4 riêng và không cần `fieldMetaData`.

6. **`id` của container (layoutRow, layoutColumn, section, tab, group) là UUID v4:**
   - ✅ `"id": "00000000-0000-4000-8000-000000000431"`

#### Ví dụ cấu trúc đúng (tối giản):

```json
{
  "content": [
    {
      "id": "<uuid>",
      "type": "layoutRow",
      "numberOfColumns": 2,
      "gap": 20,
      "slug": "layout_row_main_content",
      "isShowChildren": true,
      "isBorder": false,
      "paddingLeft": 0, "paddingRight": 0, "paddingTop": 0, "paddingBottom": 0,
      "children": [
        {
          "id": "<uuid>",
          "type": "layoutColumn",
          "colSpan": 1,
          "name": "",
          "slug": "layout_column_main_information",
          "isShowName": false,
          "isShowChildren": true,
          "isBorder": false,
          "paddingLeft": 0, "paddingRight": 0, "paddingTop": 0, "paddingBottom": 0,
          "gap": 20,
          "children": [
            {
              "id": "<uuid>",
              "type": "section",
              "typeSection": "normal",
              "numberOfTabs": 1,
              "name": "Section Name",
              "slug": "section_system_information",
              "isShowName": true,
              "isShowChildren": true,
              "isBorder": true,
              "paddingLeft": 20, "paddingRight": 20, "paddingTop": 24, "paddingBottom": 24,
              "gap": 20,
              "displayUnderline": false,
              "children": [
                {
                  "id": "<uuid>",
                  "name": "",
                  "slug": "tab_basic_information",
                  "isShowChildren": true,
                  "children": [
                    {
                      "id": "<uuid>",
                      "type": "group",
                      "name": "",
                      "numberOfColumns": 2,
                      "canCollapse": false,
                      "slug": "group_system_fields",
                      "isShowName": false,
                      "isShowChildren": true,
                      "isBorder": false,
                      "paddingLeft": 0, "paddingRight": 0, "paddingTop": 0, "paddingBottom": 0,
                      "gap": 12,
                      "tabKey": 1,
                      "components": [
                        {
                          "id": "OF...",
                          "name": "Field Name",
                          "status": 1,
                          "slug": "field_slug",
                          "fieldType": "short_text",
                          "required": 0,
                          "manualModifyAllow": true,
                          "showLabel": true,
                          "showIcon": true,
                          "isLinkRedirect": true,
                          "labelPlacement": "top",
                          "labelAlign": "left",
                          "enabledAISearch": false,
                          "label": "Field Label",
                          "uiSlug": "field_slug_1"
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**Luôn tham khảo file mẫu `assets/sample_layout_1.json` trước khi xây dựng JSON.**

---

### Phân loại thành phần layout

Layout gồm 2 loại thành phần:

#### 1. Loại Container (chứa các thành phần khác)

| Thành phần | Mô tả |
|------------|--------|
| **Section** | Khu vực chứa group, `typeSection: "normal"`, `numberOfTabs: 1` |
| **Tab-section** | Section có hệ thống tab, `typeSection: "menu"`, `numberOfTabs: ≥2` |
| **Group** | Nhóm chứa các field, bố trí field theo `numberOfColumns`. Có 3 loại: `"group"` (mặc định), `"accountGroup"` (group cho account), `"departmentPositionGroup"` (group cho phòng ban/chức vụ) |
| **Display Box** | Hộp hiển thị nội dung tùy chỉnh (HTML, ReactJS, Text hoặc Markdown), `fieldType: "display_box"`. Phải nằm trong Group. Thường dùng cho avatar card, banner, hoặc nội dung UI phức tạp |
| **Button Group** | Nhóm chứa các nút hành động, `fieldType: "button_group"`. Cấu hình vị trí nút, danh sách nút, icon |

#### 2. Loại Field (hiển thị dữ liệu)

| Thành phần | Mô tả |
|------------|--------|
| **Các trường của Object** | Trường dữ liệu thuộc Object (short_text, boolean, lookup_normal, file, ...) |
| **Bảng danh sách liên quan** | `fieldType: "related_list"` — hiển thị danh sách bản ghi từ Object khác có trường lookup trỏ về Object hiện tại (xem chi tiết bên dưới) |
| **Report** | `fieldType: "report"` — nhúng báo cáo vào layout với bộ lọc tùy chỉnh |
| **Dashboard** | `fieldType: "dashboard"` — nhúng dashboard vào layout |
| **Tracking History** | `fieldType: "tracking_history"` — hiển thị lịch sử thay đổi/hoạt động của bản ghi |
| **Up Next Task** | `fieldType: "up_next_task"` — hiển thị task tiếp theo cần thực hiện |
| **Path Component** | `fieldType: "path_component"` — hiển thị đường dẫn/breadcrumb của bản ghi (ví dụ: trạng thái pipeline) |
| **Smart Paste** | `fieldType: "smart_paste"` — cho phép dán thông minh từ clipboard vào các trường |
| **Workflow Button** | `fieldType: "workflow_button"` — nút kích hoạt workflow |
| **Display Text** | `fieldType: "display_text"` — hiển thị nội dung text tĩnh |

#### 3. Loại Field đặc biệt (Lookup & Relationship)

| Thành phần | Mô tả |
|------------|--------|
| **lookup_normal** | Trường lookup tiêu chuẩn |
| **lookup_parent** | Trường lookup cha (quan hệ cha-con) |
| **lookup_peer2peer** | Trường lookup ngang hàng |
| **embedded** | Bản ghi nhúng — hiển thị bản ghi con trực tiếp trong layout cha |
| **reference** | Trường tham chiếu tới bản ghi khác |
| **children** | Hiển thị danh sách bản ghi con |
| **department_personnel_select** | Trường chọn nhân sự/phòng ban |

**Quy tắc quan trọng:** Loại field **bắt buộc phải nằm bên trong 1 Group**. Không được đặt field trực tiếp vào section hoặc tab mà không qua group.

---

### layoutRow

Một hàng ngang chứa các cột.

```json
{
  "id": "<uuid>",
  "type": "layoutRow",
  "numberOfColumns": 2,
  "gap": 20,
  "maxWidth": 1000,
  "unitMaxWidth": "px",
  "horizontalAlignment": "center",
  "slug": "layout_row_main_content",
  "name": "",
  "isShowChildren": true,
  "isBorder": false,
  "paddingLeft": 0,
  "paddingRight": 0,
  "paddingTop": 0,
  "paddingBottom": 0,
  "children": [ /* mảng layoutColumn */ ]
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `id` | String | UUID duy nhất |
| `type` | String | Luôn là `"layoutRow"` |
| `numberOfColumns` | Number | Số cột trong hàng (ví dụ: `1`, `2`, `3`) |
| `gap` | Number | Khoảng cách giữa các cột (px). Mặc định: `20` |
| `maxWidth` | Number | Chiều rộng tối đa của Row; kết hợp với `unitMaxWidth`. Với layout Tạo dạng form thông thường, mặc định `1000`; với Row chứa bảng rộng, dùng `100` |
| `unitMaxWidth` | String | Đơn vị của `maxWidth`: `"px"` cho form giới hạn chiều rộng hoặc `"%"` cho Row cần chiếm toàn bộ chiều ngang |
| `horizontalAlignment` | String | Căn chỉnh Row trong vùng nội dung. Dùng `"center"` cho Layout Row ngoài cùng của layout Tạo |
| `slug` | String | Slug có ý nghĩa, mặc định `layout_row_<meaningful_name>`; chỉ thêm `_<index>` khi bị trùng |
| `name` | String | Tên hiển thị (thường để trống) |
| `isShowChildren` | Boolean | Hiển thị children. Mặc định: `true` |
| `isBorder` | Boolean | Có viền. Mặc định: `false` |
| `paddingLeft/Right/Top/Bottom` | Number | Padding (px). Mặc định: `0` |
| `children` | Array | Mảng các `layoutColumn` |

---

### layoutColumn

Một cột trong hàng. Tỷ lệ chiều rộng dựa trên `colSpan`.

```json
{
  "id": "<uuid>",
  "type": "layoutColumn",
  "colSpan": 1,
  "name": "",
  "slug": "layout_column_main_information",
  "isShowName": false,
  "isShowChildren": true,
  "isBorder": false,
  "paddingLeft": 0,
  "paddingRight": 0,
  "paddingTop": 0,
  "paddingBottom": 0,
  "gap": 20,
  "children": [ /* mảng section */ ]
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `id` | String | UUID duy nhất |
| `type` | String | Luôn là `"layoutColumn"` |
| `colSpan` | Number | Tỷ lệ chiều rộng. Ví dụ: Row có 2 column với colSpan `1` và `3` → tỷ lệ 1:3 (cột 1 chiếm 1/4, cột 2 chiếm 3/4) |
| `name` | String | Tên cột (thường để trống) |
| `slug` | String | Slug có ý nghĩa, mặc định `layout_column_<meaningful_name>`; chỉ thêm `_<index>` khi bị trùng |
| `isShowName` | Boolean | Hiển thị tên cột. Mặc định: `false` |
| `isShowChildren` | Boolean | Hiển thị children. Mặc định: `true` |
| `isBorder` | Boolean | Có viền. Mặc định: `false` |
| `paddingLeft/Right/Top/Bottom` | Number | Padding (px). Mặc định: `0` |
| `gap` | Number | Khoảng cách giữa các section (px). Mặc định: `20` |
| `children` | Array | Mảng các `section` |

**Quy tắc tỷ lệ cột:**
- Tỷ lệ chiều rộng = `colSpan` của cột / tổng `colSpan` của tất cả cột trong cùng row.
- Ví dụ: 2 cột colSpan `1` và `3` → cột 1 = 25%, cột 2 = 75%.
- Ví dụ: 2 cột colSpan `1` và `1` → mỗi cột = 50%.
- Ví dụ: 3 cột colSpan `1`, `1`, `1` → mỗi cột = 33.3%.

---

### section

Một khu vực trong cột, có thể chứa tab hoặc không.

```json
{
  "id": "<uuid>",
  "type": "section",
  "typeSection": "normal",
  "numberOfTabs": 1,
  "name": "Section 1",
  "slug": "section_system_information",
  "isShowName": false,
  "isShowChildren": true,
  "isBorder": true,
  "paddingLeft": 20,
  "paddingRight": 20,
  "paddingTop": 24,
  "paddingBottom": 24,
  "gap": 20,
  "displayUnderline": false,
  "children": [ /* mảng tab */ ]
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `id` | String | UUID duy nhất |
| `type` | String | Luôn là `"section"` |
| `typeSection` | String | `"normal"` = section bình thường, `"menu"` = section có hệ thống tab (menu chuyển tab) |
| `numberOfTabs` | Number | Số tab. `1` = không có tab (section thường), `≥2` = có tab |
| `name` | String | Tên section |
| `slug` | String | Slug có ý nghĩa, mặc định `section_<meaningful_name>`; chỉ thêm `_<index>` khi bị trùng |
| `isShowName` | Boolean | Hiển thị tên section. Mặc định: `false` |
| `isShowChildren` | Boolean | Hiển thị children. Mặc định: `true` |
| `isBorder` | Boolean | Có viền. Mặc định: `true` |
| `paddingLeft/Right` | Number | Padding ngang (px). Mặc định: `20` |
| `paddingTop/Bottom` | Number | Padding dọc (px). Mặc định: `24` |
| `gap` | Number | Khoảng cách giữa các group (px). Mặc định: `20` |
| `displayUnderline` | Boolean | Hiển thị gạch dưới tab. Mặc định: `false` |
| `children` | Array | Mảng các `tab` |

**Quy tắc typeSection:**
- `"normal"` + `numberOfTabs: 1` → Section không có tab, chỉ chứa 1 tab ẩn chứa các group.
- `"menu"` + `numberOfTabs: ≥2` → Section có hệ thống tab, mỗi tab là một trang riêng.

---

### tab

Một tab trong section.

```json
{
  "id": "<uuid>",
  "name": "Tab 1",
  "slug": "tab_activities",
  "isShowChildren": true,
  "children": [ /* mảng group */ ]
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `id` | String | UUID duy nhất |
| `name` | String | Tên tab. Nếu section `numberOfTabs: 1` thì tên thường để trống hoặc "Tab 1" |
| `slug` | String | Slug có ý nghĩa, mặc định `tab_<meaningful_name>`; chỉ thêm `_<index>` khi bị trùng |
| `isShowChildren` | Boolean | Hiển thị children. Mặc định: `true` |
| `children` | Array | Mảng các `group` |

---

### group

Một nhóm field, có thể bố trí field theo số cột.

```json
{
  "id": "<uuid>",
  "type": "group",
  "name": "Group 1",
  "numberOfColumns": 2,
  "canCollapse": false,
  "slug": "group_system_fields",
  "isShowName": false,
  "isShowChildren": true,
  "isBorder": false,
  "paddingLeft": 0,
  "paddingRight": 0,
  "paddingTop": 0,
  "paddingBottom": 0,
  "gap": 12,
  "tabKey": 1,
  "components": [ /* mảng field/component */ ]
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `id` | String | UUID duy nhất |
| `type` | String | Loại group: `"group"` (mặc định), `"accountGroup"` (group cho account), `"departmentPositionGroup"` (group cho phòng ban/chức vụ) |
| `name` | String | Tên nhóm |
| `numberOfColumns` | Number | Số cột bố trí field. `1` = 1 cột, `2` = 2 cột ngang, `3` = 3 cột ngang |
| `canCollapse` | Boolean | Cho phép thu gọn group. Mặc định: `false` |
| `slug` | String | Slug có ý nghĩa, mặc định `group_<meaningful_name>`; chỉ thêm `_<index>` khi bị trùng |
| `isShowName` | Boolean | Hiển thị tên group. Mặc định: `false` |
| `isShowChildren` | Boolean | Hiển thị children. Mặc định: `true` |
| `isBorder` | Boolean | Có viền. Mặc định: `false` |
| `paddingLeft/Right/Top/Bottom` | Number | Padding (px). Mặc định: `0` |
| `gap` | Number | Khoảng cách giữa các field (px). Mặc định: `12` |
| `tabKey` | Number | Index tab chứa group (bắt đầu từ `0` hoặc `1` tùy context) |
| `components` | Array | Mảng các field/component |

---

### component (field)

Một trường dữ liệu hiển thị trên layout. Các thuộc tính phụ thuộc vào `fieldType`.

#### Các trường chung cho mọi component

```json
{
  "id": "OF...",
  "name": "Tên field",
  "status": 1,
  "slug": "field_slug",
  "fieldType": "short_text",
  "required": 0,
  "disabled": 0,
  "readOnly": 0,
  "manualModifyAllow": true,
  "showLabel": true,
  "showIcon": true,
  "isLinkRedirect": true,
  "labelPlacement": "top",
  "labelAlign": "left",
  "customName": "",
  "enabledAISearch": false,
  "fieldVariableSlug": "",
  "isAllowVariable": false,
  "label": "Nhãn hiển thị",
  "uiSlug": "field_slug_1"
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `id` | String | ID field từ Object definition (dạng `OF...`) |
| `name` | String | Tên field gốc |
| `status` | Number | `1` = active |
| `slug` | String | Slug field gốc |
| `fieldType` | String | Loại field (xem bảng field types ở skill `objects-info-agent`) |
| `required` | Number | `0` = không bắt buộc, `1` = bắt buộc. Không khả dụng cho `formula`, `auto_number` |
| `disabled` | Number | `0` = bình thường, `1` = vô hiệu hóa (field hiển thị nhưng không tương tác được) |
| `readOnly` | Number | `0` = cho phép sửa, `1` = chỉ đọc (field hiển thị nhưng không chỉnh sửa được) |
| `manualModifyAllow` | Boolean | Cho phép chỉnh sửa thủ công |
| `showLabel` | Boolean | Hiển thị nhãn. Mặc định: `true` |
| `showIcon` | Boolean | Hiển thị icon. Mặc định: `true` |
| `isLinkRedirect` | Boolean | Cho phép nhấn để chuyển trang. Mặc định: `true` |
| `labelPlacement` | String | Vị trí nhãn: `"top"` (trên), `"left"` (trái), `"right"` (phải), `"bottom"` (dưới) |
| `labelAlign` | String | Căn lề nhãn: `"left"`, `"right"`, `"center"` |
| `customName` | String | Tên hiển thị tùy chỉnh (ghi đè tên gốc trên giao diện) |
| `enabledAISearch` | Boolean | Bật tìm kiếm AI (khả dụng cho: `short_text`, `phone`, `email`, `url`). Mặc định: `false` |
| `fieldVariableSlug` | String | Slug biến tham chiếu (dùng khi field lấy giá trị từ biến) |
| `isAllowVariable` | Boolean | Cho phép thay thế biến trong giá trị field. Mặc định: `false` |
| `label` | String | Nhãn hiển thị tùy chỉnh (có thể khác `name`) |
| `uiSlug` | String | Slug giao diện, format: `{slug}_{số thứ tự}` (ví dụ: `name_1`) |
| `useLayouts` | Array | *(Dùng cho component đặc biệt: report, dashboard, tracking_history, path_component)* Mảng functionLayout mà component hỗ trợ. Ví dụ: `[2]` = chỉ view/edit, `[3, 2]` = tạo + view/edit. Với các field thường của Object thì không cần trường này |

### QUAN TRỌNG - Object Field component PHẢI có field ID và fieldMetaData đầy đủ

Khi đặt Object Field vào layout, component **BẮT BUỘC** phải bao gồm:

1. `id`: Field ID thực từ Object definition (dạng `OF...`). Lấy từ API `/bapi/v1/objects/list` với `includeFields: true`.
2. `fieldMetaData`: Chuỗi JSON chứa đầy đủ metadata của field (lấy từ trường `metaData` trong Object definition, stringify thành chuỗi JSON).

Quy tắc này không áp dụng cho component đặc biệt không phải Object Field như `path_component`; Path Component dùng UUID v4 và `pathComponentSlug` theo schema riêng bên dưới.

Nếu Object Field thiếu `id` hoặc `fieldMetaData`, layout sẽ tạo được nhưng:
- Không thể chỉnh sửa/di chuyển/xóa các field đã có trong layout editor UI
- Chỉ có thể thêm mới field từ palette bên trái

Ví dụ component **ĐÚNG** (có đầy đủ id + fieldMetaData):
```json
{
  "id": "OF00000000024",
  "slug": "owner",
  "fieldType": "lookup_normal",
  "name": "Owner",
  "label": "Người sở hữu",
  "uiSlug": "owner_1",
  "status": 1,
  "required": 0,
  "manualModifyAllow": true,
  "readOnly": 0,
  "showLabel": true,
  "labelPlacement": "top",
  "labelAlign": "left",
  "showIcon": true,
  "isLinkRedirect": true,
  "fieldMetaData": "{\"link_field\":\"id\",\"object_slug\":\"personnel\",\"object\":\"OT00000000021\"}",
  "typeView": "field",
  "showFieldName": "{$record.first_name} {$record.last_name}",
  "isAddRecord": true,
  "isHoverShowRecord": true,
  "multiple": 0
}
```

#### Thuộc tính bổ sung theo fieldType

**lookup_normal / lookup_dependency:**

> **Lưu ý về `showFieldName`:** Giá trị mặc định là `"$record.name"`, hiển thị trường `name` của bản ghi được lookup. Tuy nhiên, nếu trường lookup trỏ tới object **Personnel** (slug: `personnel`), cần đổi thành `"{$record.first_name} {$record.last_name}"` để hiển thị đầy đủ họ tên nhân sự. Tương tự, với các object khác có cách hiển thị tên đặc biệt, cần điều chỉnh `showFieldName` cho phù hợp.

```json
{
  "isAddRecord": true,
  "typeView": "field",
  "layoutViewId": "",
  "showFieldName": "$record.name",
  "listAction": [{"value": "Value 1"}],
  "fieldMetaData": "{\"object\":\"OT...\",\"object_slug\":\"...\"}",
  "combineAction": false,
  "menuAction": [],
  "numberRecord": 1,
  "numberColumn": 1,
  "showBorder": true,
  "showLine": true,
  "gap": 20,
  "useHeight": false,
  "heightList": 100,
  "orderBy": "updated",
  "orderType": "asc",
  "allowSort": true,
  "isHoverShowRecord": true,
  "isWrapText": true,
  "layoutHover": "",
  "popupWidth": 350,
  "popupHeight": 450,
  "multiple": 0
}
```

**file:**
```json
{
  "fieldMetaData": "{\"file_type\":[\"jpg\",\"jpeg\",\"png\"],\"is_public\":false,\"multiple_limit\":{\"min\":1,\"max\":10},\"file_group_type\":\"avatar\",\"max_size\":5242880,\"is_resizable\":false}",
  "radius": "50%",
  "size": 75,
  "objectFit": "cover",
  "altField": [{"value": "OF..."}]
}
```

**long_text:**
```json
{
  "maxHeight": 400
}
```

**select:**
```json
{
  "displayTypeOptions": 2,
  "fieldMetaData": "{\"option_display_type\":2}"
}
```

**boolean:**
```json
{
  "labelPlacement": "right"
}
```

**phone:**
```json
{
  "showButtonCall": true,
  "showWhenHover": true
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `showButtonCall` | Boolean | Hiển thị nút gọi điện bên cạnh trường. Mặc định: `true` |
| `showWhenHover` | Boolean | Chỉ hiển thị nút gọi khi hover chuột vào trường. Mặc định: `true` |

**rating:**
```json
{
  "type": "horizontal",
  "sizeIcon": 24
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `type` | String | Hướng hiển thị: `"horizontal"` (ngang) hoặc `"vertical"` (dọc). Mặc định: `"horizontal"` |
| `sizeIcon` | Number | Kích thước icon rating (px). Mặc định: `24` |

**lookup_normal / lookup_dependency (thuộc tính bổ sung):**

> Ngoài các thuộc tính đã liệt kê ở trên, lookup còn hỗ trợ thêm:

```json
{
  "showFieldAvatar": "",
  "layoutHover": "",
  "popupWidth": 350,
  "popupHeight": 450
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `showFieldAvatar` | String | ID field avatar để hiển thị bên cạnh tên bản ghi lookup. Để trống nếu không dùng |
| `layoutHover` | String | ID layout dùng cho popup preview khi hover vào bản ghi lookup. Để trống nếu không dùng |
| `popupWidth` | Number | Chiều rộng popup preview (px). Mặc định: `350` |
| `popupHeight` | Number | Chiều cao popup preview (px). Mặc định: `450` |

**report (nhúng báo cáo):**

Report cho phép nhúng một báo cáo trực tiếp vào layout. Cần cung cấp `reportId` — ID báo cáo trên hệ thống (lấy từ danh sách báo cáo).

```json
{
  "id": "<uuid>",
  "fieldType": "report",
  "status": 1,
  "slug": "report_sales_performance",
  "name": "report",
  "label": "report",
  "uiSlug": "report_sales_performance_1",
  "useLayouts": [2],
  "reportId": "RV...",
  "reportTypeId": "RTV...",
  "logicSequence": null,
  "filterItems": [],
  "reportHeight": 300,
  "isShowName": true,
  "customName": null
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `useLayouts` | Array | Mảng functionLayout mà component này hỗ trợ. Ví dụ: `[2]` = chỉ view/edit, `[3, 2]` = cả tạo và view/edit |
| `reportId` | String | **Bắt buộc.** ID báo cáo cần nhúng (dạng `RV...`). Lấy từ danh sách báo cáo trên hệ thống |
| `reportTypeId` | String/null | ID loại báo cáo (dạng `RTV...`). `null` = mặc định |
| `logicSequence` | String/null | Biểu thức logic lọc dữ liệu (ví dụ: `"1 AND 2 OR 3"`). `null` = không lọc |
| `filterItems` | Array | Danh sách bộ lọc. Xem mục "Filter Operators" bên dưới |
| `reportHeight` | Number | Chiều cao hiển thị báo cáo (px). Mặc định: `300` |
| `isShowName` | Boolean | Hiển thị tên báo cáo trên layout. Mặc định: `true` |
| `customName` | String/null | Tên tùy chỉnh thay thế tên gốc. `null` = dùng tên gốc |

**Các Filter Operators hỗ trợ cho Report:**

`=`, `!=`, `<`, `>`, `<=`, `>=`, `like`, `not like`, `contains any`, `not contains any`, `is null`, `not null`, `startsWith`, `endsWith`, `in`, `not in`, `between`, `rangeWithin`, `rangeContains`

Filter ngày tháng: `Yesterday`, `Today`, `Tomorrow`, `Last n days`, `Next n days`, `n Days ago`, `n Days from now`, `Last week`, `This week`, `Next week`, `Last n weeks`, `Next n weeks`, `Last month`, `This month`, `Next month`, `Last n months`, `Next n months`, `Last quarter`, `This quarter`, `Next quarter`, `Last year`, `This year`, `Next year`, `Last n years`, `Next n years`

**dashboard (nhúng dashboard):**

Dashboard cho phép nhúng một dashboard trực tiếp vào layout. Cần cung cấp `dashboardSlug` — slug dashboard trên hệ thống (lấy từ danh sách dashboard).

```json
{
  "id": "<uuid>",
  "fieldType": "dashboard",
  "status": 1,
  "slug": "dashboard_sales_overview",
  "name": "dashboard",
  "label": "dashboard",
  "uiSlug": "dashboard_sales_overview_1",
  "useLayouts": [2],
  "dashboardSlug": "inbound_calls",
  "dashboardHeight": 300,
  "reportFilters": [],
  "isShowName": true,
  "customName": null
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `useLayouts` | Array | Mảng functionLayout mà component này hỗ trợ. Ví dụ: `[2]` = chỉ view/edit |
| `dashboardSlug` | String | **Bắt buộc.** Slug dashboard cần nhúng (ví dụ: `"inbound_calls"`). Lấy từ danh sách dashboard trên hệ thống |
| `dashboardHeight` | Number | Chiều cao hiển thị dashboard (px). Mặc định: `300` |
| `reportFilters` | Array | Danh sách bộ lọc cho các report trong dashboard. Mặc định: `[]` |
| `isShowName` | Boolean | Hiển thị tên dashboard trên layout. Mặc định: `true` |
| `customName` | String/null | Tên tùy chỉnh thay thế tên gốc. `null` = dùng tên gốc |

**button_group (nhóm nút hành động):**

Button Group cho phép đặt nhóm nút hành động trên layout. Các nút (button) được lấy từ danh sách button đã cấu hình trên object.

> **Phân biệt:** Component `fieldType: "button_group"` nằm trong `content` và được nhúng tại một vị trí cụ thể của bố cục. Cụm action mặc định trên header màn hình xem/sửa nằm tại `pageSettings.buttons`. Khi mục tiêu chỉ là làm record-level button xuất hiện trên giao diện xem bản ghi, cập nhật `pageSettings.buttons.listButton`; không tự tạo component `button_group` trong `content`.

```json
{
  "id": "<uuid>",
  "fieldType": "button_group",
  "status": 1,
  "slug": "button_group_primary_actions",
  "name": "button_group",
  "label": "button_group",
  "uiSlug": "button_group_primary_actions_1",
  "buttonPosition": "right",
  "combineAction": false,
  "menuIcon": "ellipsis-vertical",
  "gap": 8,
  "listButton": [
    {
      "buttonId": "BU...",
      "type": "contained",
      "size": "medium",
      "useIcon": false,
      "onlyShowIcon": false,
      "icon": null,
      "slug": "convert",
      "iconDarkMode": null
    }
  ]
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `buttonPosition` | String | Vị trí căn nút: `"left"`, `"right"`, `"center"`. Mặc định: `"right"` |
| `combineAction` | Boolean | Gom các nút thành menu dropdown. Mặc định: `false` |
| `menuIcon` | String | Icon cho menu dropdown (khi `combineAction: true`). Mặc định: `"ellipsis-vertical"` |
| `gap` | Number | Khoảng cách giữa các nút (px). Mặc định: `8` |
| `listButton` | Array | Danh sách các nút. Mỗi nút gồm các thuộc tính bên dưới |

**Thuộc tính mỗi nút trong `listButton`:**

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `buttonId` | String | ID button trên hệ thống (dạng `BU...`). **Bắt buộc** — lấy từ danh sách button của object |
| `type` | String | Kiểu hiển thị nút: `"contained"` (nền đặc), `"outlined"` (viền), `"text"` (chỉ text) |
| `size` | String | Kích thước: `"small"`, `"medium"`, `"large"`. Mặc định: `"medium"` |
| `useIcon` | Boolean | Sử dụng icon cho nút. Mặc định: `false` |
| `onlyShowIcon` | Boolean | Chỉ hiển thị icon (ẩn text). Mặc định: `false` |
| `icon` | String/null | Đường dẫn hoặc tên icon. `null` = dùng icon mặc định |
| `slug` | String | Slug button (ví dụ: `"convert"`, `"cancel"`) |
| `iconDarkMode` | String/null | Icon cho dark mode. `null` = dùng chung icon |

**tracking_history (lịch sử hoạt động):**

Tracking History hiển thị lịch sử thay đổi và hoạt động trên bản ghi.

```json
{
  "id": "<uuid>",
  "fieldType": "tracking_history",
  "status": 1,
  "slug": "tracking_history_<timestamp>",
  "name": "tracking_history",
  "label": "tracking_history",
  "uiSlug": "tracking_history_<timestamp>_1",
  "useLayouts": [3, 2],
  "recordCount": 10
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `useLayouts` | Array | Mảng functionLayout mà component này hỗ trợ. `[3, 2]` = dùng cho cả tạo+xem và xem/sửa |
| `recordCount` | Number | Số bản ghi lịch sử hiển thị. Mặc định: `10` |

**up_next_task (task tiếp theo):**

```json
{
  "id": "<uuid>",
  "fieldType": "up_next_task",
  "status": 1,
  "slug": "up_next_task_<timestamp>",
  "name": "up_next_task",
  "label": "Up Next Task",
  "uiSlug": "up_next_task_<timestamp>_1"
}
```

**path_component (Lộ trình / đường dẫn trạng thái):**

Path Component hiển thị lộ trình trạng thái (pipeline stages) của bản ghi. Component này chỉ dùng trên layout Xem/sửa (`functionLayout: 2`) và cần cung cấp `pathComponentSlug` — slug thật của Lộ trình đã được cấu hình trên cùng object. Xem quy trình resolve, merge và verify ở **Khả năng I: Đưa Path Component vào layout Xem/sửa**.

```json
{
  "id": "<uuid>",
  "fieldType": "path_component",
  "status": 1,
  "slug": "path_component_sales_stage",
  "name": "path_component",
  "label": "path_component",
  "uiSlug": "path_component_sales_stage_1",
  "useLayouts": [2],
  "pathComponentSlug": "sales_stage_path",
  "isPinned": false
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `id` | String | UUID v4 riêng của layout component; không dùng Path ID `PC...` hoặc Object Field ID `OF...` |
| `useLayouts` | Array | Bắt buộc `[2]` vì Path Component chỉ hiển thị trên layout Xem/sửa |
| `pathComponentSlug` | String | **Bắt buộc.** Slug thật của Path đã resolve trên cùng object; không điền Path ID `PC...` |
| `slug` | String | Slug unique của layout component, có tiền tố `path_component_`; không phải `pathComponentSlug` |
| `uiSlug` | String | UI identity của component, sinh từ component `slug` và phải unique trong layout |
| `isPinned` | Boolean | Trạng thái ghim component; mặc định `false` nếu người dùng không yêu cầu khác |

Path Component là component đặc biệt, không phải Object Field, nên không cần `fieldMetaData`.

**workflow_button (nút workflow):**

```json
{
  "id": "<uuid>",
  "fieldType": "workflow_button",
  "status": 1,
  "slug": "workflow_button_approval_actions",
  "name": "workflow_button",
  "label": "Workflow Button",
  "uiSlug": "workflow_button_approval_actions_1"
}
```

**display_box (hộp hiển thị tùy chỉnh):**

Display Box là component hiển thị nội dung tùy chỉnh dạng HTML, ReactJS, Text thuần hoặc Markdown. **Display Box bắt buộc phải nằm trong 1 Group** (giống các field khác).

```json
{
  "id": "<uuid>",
  "fieldType": "display_box",
  "status": 1,
  "slug": "display_box_contact_summary",
  "displayBoxType": "react",
  "content": "<code ReactJS hoặc HTML>",
  "name": "display_box",
  "label": "display_box",
  "uiSlug": "display_box_contact_summary_1",
  "displayBoxFields": [{"slug": "avatar", "size": 98}]
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `id` | String | UUID duy nhất (sinh UUID v4, không phải ID field từ Object) |
| `fieldType` | String | Luôn là `"display_box"` |
| `status` | Number | `1` = active |
| `slug` | String | Slug có ý nghĩa, mặc định `display_box_<meaningful_name>`; chỉ thêm `_<index>` khi bị trùng |
| `displayBoxType` | String | Loại nội dung: `"react"` = code ReactJS, `"html"` = code HTML, `"text"` = nội dung text thuần, `"markdown"` = nội dung Markdown |
| `content` | String | Code ReactJS hoặc HTML (xem chi tiết bên dưới) |
| `name` | String | Tên component. Thường là `"display_box"` |
| `label` | String | Nhãn hiển thị. Thường là `"display_box"` |
| `uiSlug` | String | Slug giao diện, format: `{component_slug}_{số thứ tự}`, ví dụ `display_box_contact_summary_1` |
| `displayBoxFields` | Array | Danh sách các field được sử dụng trong code (dùng component `<Field />`). Mỗi phần tử gồm `slug` và các props truyền vào. Nếu không dùng `<Field />` thì để mảng rỗng `[]` |

**Viết code cho Display Box:**

- Biến `$record` là giá trị bản ghi hiện tại (dạng object). Truy cập trường: `$record.field_slug` hoặc `$record?.field_slug` (tránh lỗi null).
- **Với `displayBoxType: "react"`:** Code phải kết thúc bằng `render(<App />);`. Ví dụ:
  ```jsx
  const App = () => {
      return (
          <div style={{ padding: "16px" }}>
              <p>{$record?.name || ""}</p>
          </div>
      );
  };
  render(<App />);
  ```
- **Component `<Field />`:** Hệ thống hỗ trợ component `<Field slug="field_slug" />` để render field đặc biệt (ví dụ: avatar). Props phổ biến: `slug` (bắt buộc), `size` (kích thước px), `alt` (text thay thế). Khi dùng `<Field />`, phải khai báo field đó trong `displayBoxFields`.
- **CSS variables hệ thống:** Có thể dùng các biến CSS của hệ thống như `var(--primary-main)`, `var(--typography-primary)`, `var(--typography-secondary)`.
- **Với `displayBoxType: "text"`:** Nội dung text thuần, không cần code. Có thể dùng biến `$record.field_slug` trong nội dung.
- **Với `displayBoxType: "markdown"`:** Nội dung Markdown chuẩn. Có thể dùng biến `$record.field_slug` trong nội dung.
- **Lưu ý:** Nội dung `content` trong JSON phải escape các ký tự đặc biệt (dấu `"` thành `\"`, xuống dòng thành `\n`).

**Ví dụ Display Box hiển thị avatar + thông tin nhân sự (ReactJS):**

```json
{
  "id": "00000000-0000-4000-8000-000000000402",
  "fieldType": "display_box",
  "status": 1,
  "slug": "display_box_person_profile",
  "displayBoxType": "react",
  "content": "const App = () => {\n    return (\n        <div style={{ borderRadius: \"4px\", overflow: \"hidden\", paddingBottom: \"73px\", position: \"relative\" }}>\n            <div style={{ backgroundColor: \"var(--primary-main)\", height: \"90px\", position: \"relative\" }}>\n                <img\n                    src=\"/images/personal-cover-bg.png\"\n                    style={{ position: \"absolute\", top: 0, left: 0, width: \"100%\", height: \"100%\", objectFit: \"cover\" }}\n                />\n                <div style={{ position: \"absolute\", top: \"100%\", left: \"24px\", transform: \"translateY(-50%)\" }}>\n                    <Field slug=\"avatar\" size={98} alt={$record?.first_name} />\n                </div>\n            </div>\n            <div style={{ position: \"absolute\", left: \"137px\", top: \"100px\", maxWidth: \"calc(100% - 156px)\" }}>\n                <p\n                    style={{\n                        fontSize: \"14px\",\n                        fontWeight: 700,\n                        lineHeight: \"142.857%\",\n                        color: \"var(--typography-primary)\",\n                        maxWidth: \"100%\",\n                        overflowWrap: \"break-word\",\n                    }}\n                >\n                    {$record?.name || \"\"} {$record?.first_name || \"\"}\n                </p>\n                <p\n                    style={{\n                        color: \"var(--typography-secondary)\",\n                        fontSize: \"14px\",\n                        fontWeight: 400,\n                        lineHeight: \"142.857%\",\n                        maxWidth: \"100%\",\n                        overflowWrap: \"break-word\",\n                    }}\n                >\n                    {$record?.account_email || $record?.work_email || $record?.emails?.[0] || \"\"}\n                </p>\n            </div>\n        </div>\n    );\n};\nrender(<App />);",
  "name": "display_box",
  "label": "display_box",
  "uiSlug": "display_box_person_profile_1",
  "displayBoxFields": [{"slug": "avatar", "size": 98}]
}
```

**related_list (danh sách liên quan):**

Danh sách liên quan hiển thị các bản ghi từ Object con có trường lookup trỏ về Object hiện tại.

**Cơ chế hoạt động:**
Khi Object B có 1 trường lookup trỏ tới Object A, hệ thống tự tạo 1 "danh sách liên quan" (Related List) trên Object A. Khi đặt related_list vào layout của Object A, nó sẽ hiển thị danh sách tất cả bản ghi Object B có trường lookup trỏ về bản ghi Object A đang xem.

**Ví dụ:**
- Object "Order Product Line" có trường `order` (lookup) trỏ tới Object "Order".
- Hệ thống tạo Related List với slug `Order_Product_lines` trên Object "Order".
- Trong layout của Object "Order", kéo related_list này vào → hiển thị danh sách các "Order Product Line" thuộc đơn hàng đang xem.

**Các trường quan trọng:**

| Trường | Mô tả |
|--------|--------|
| `relatedListId` | ID của danh sách liên quan (dạng `RL...`), lấy từ API `/objects/list` |
| `originSlug` | Slug của Object con (Object chứa trường lookup). Ví dụ: `order_product_line` |
| `slug` | Slug có ý nghĩa, mặc định `related_list_<meaningful_name>`; chỉ thêm `_<index>` khi bị trùng |
| `showFieldName` | Trường hiển thị của bản ghi. Ví dụ: `{$record.name}` |

```json
{
  "fieldType": "related_list",
  "slug": "related_list_order_items",
  "relatedListId": "RL...",
  "fePlaceholder": false,
  "originSlug": "slug_object_con",
  "status": 1,
  "showFieldName": "{$record.name}",
  "typeView": "field",
  "label": "Tên hiển thị"
}
```

**Các giá trị `typeView` cho related_list:**

| Giá trị | Mô tả | Yêu cầu thêm |
|---------|--------|---------------|
| `"field"` | Hiển thị dạng field đơn giản | Không |
| `"list"` | Hiển thị dạng bảng (table) | Cần `tableSettings` |
| `"card"` | Hiển thị dạng thẻ (card) | Cần `layoutViewId` (ID layout dùng để render thẻ) |
| `"layout_create"` | Hiển thị dạng form tạo bản ghi nhúng | Cần `layoutViewId` (ID layout tạo bản ghi) |
| `"timeline"` | Hiển thị dạng timeline/dòng thời gian | Cần `activityTypeAllow` nếu `isAllTabActivity: false` |

**Thuộc tính bổ sung khi `typeView: "list"` (hiển thị dạng bảng):**

Khi related_list hiển thị dạng bảng (`typeView: "list"`), cần cấu hình thêm các thuộc tính sau:

```json
{
  "typeView": "list",
  "listAction": [{"value": "CREATE"}],
  "combineAction": false,
  "menuAction": [],
  "hideWhenNoData": false,
  "numberRecord": 1,
  "numberColumn": 1,
  "showBorder": true,
  "showLine": true,
  "gap": 20,
  "useHeight": false,
  "heightList": 100,
  "orderBy": "updated",
  "orderType": "asc",
  "allowSort": true,
  "isAddRecord": true,
  "tableSettings": "<chuỗi JSON — xem hướng dẫn bên dưới>"
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `typeView` | String | Kiểu hiển thị: `"list"` = dạng bảng, `"field"` = dạng field, `"card"` = dạng thẻ (cần `layoutViewId`), `"layout_create"` = dạng form tạo nhúng (cần `layoutViewId`), `"timeline"` = dạng timeline |
| `listAction` | Array | Các hành động trên danh sách. `[{"value": "CREATE"}]` = cho phép tạo bản ghi mới |
| `combineAction` | Boolean | Gom các hành động lại. Mặc định: `false` |
| `menuAction` | Array | Các hành động trong menu. Mặc định: `[]` |
| `hideWhenNoData` | Boolean | Ẩn khi không có dữ liệu. Mặc định: `false` |
| `numberRecord` | Number | Số bản ghi hiển thị mỗi trang. Mặc định: `1` |
| `numberColumn` | Number | Số cột bố trí. Mặc định: `1` |
| `showBorder` | Boolean | Hiển thị viền. Mặc định: `true` |
| `showLine` | Boolean | Hiển thị đường kẻ giữa các dòng. Mặc định: `true` |
| `gap` | Number | Khoảng cách (px). Mặc định: `20` |
| `useHeight` | Boolean | Sử dụng chiều cao cố định. Mặc định: `false` |
| `heightList` | Number | Chiều cao danh sách (px) khi `useHeight: true`. Mặc định: `100` |
| `orderBy` | String | Trường sắp xếp. Mặc định: `"updated"` |
| `orderType` | String | Chiều sắp xếp: `"asc"` hoặc `"desc"`. Mặc định: `"asc"` |
| `allowSort` | Boolean | Cho phép người dùng sắp xếp. Mặc định: `true` |
| `isAddRecord` | Boolean | Cho phép thêm bản ghi. Mặc định: `true` |
| `isAllTabActivity` | Boolean | Hiển thị tất cả tab hoạt động (dùng cho related_list dạng timeline/activity). Mặc định: `true` |
| `activityTypeAllow` | Array | Danh sách loại hoạt động cho phép hiển thị. Mảng rỗng = tất cả. Ít nhất 1 phần tử nếu `isAllTabActivity: false` |
| `tableSettings` | String | **Cấu hình bảng dạng chuỗi JSON** — chỉ dùng khi `typeView: "list"` (xem chi tiết bên dưới) |

**Cấu hình `tableSettings` (QUAN TRỌNG):**

`tableSettings` là một **chuỗi JSON** (string, không phải object) mô tả cấu hình bảng hiển thị. Cấu trúc bên trong:

```json
{
  "columns": [
    {"key": "field_slug", "width": 150},
    {"key": "_action_column", "width": 40}
  ],
  "pinnedColumns": {
    "left": [],
    "right": ["_action_column"]
  },
  "showingColumns": ["field_slug_1", "field_slug_2", "_action_column"],
  "editableColumns": []
}
```

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `columns` | Array | Danh sách TẤT CẢ các cột có thể hiển thị, mỗi cột gồm `key` (slug trường) và `width` (độ rộng px) |
| `pinnedColumns` | Object | Cột ghim cố định. `left`: ghim bên trái, `right`: ghim bên phải. Thường ghim `_action_column` bên phải |
| `showingColumns` | Array | Danh sách slug các cột **thực sự hiển thị**. Chỉ các cột có trong mảng này mới xuất hiện trên bảng. Thứ tự trong mảng quyết định thứ tự cột hiển thị |
| `editableColumns` | Array | Danh sách slug các cột cho phép chỉnh sửa trực tiếp trên bảng. Mặc định: `[]`. **Xem hướng dẫn chi tiết bên dưới** |

**Cột đặc biệt `_action_column`:**
- Cột hành động (xem, sửa, xoá bản ghi), luôn có `"width": 40`.
- Luôn thêm vào cuối `columns`, cuối `showingColumns`, và trong `pinnedColumns.right`.

**Quy tắc thiết kế tableSettings (vai trò chuyên gia UI/UX):**

1. **Chọn cột hiển thị hợp lý (`showingColumns`):**
   - Chỉ hiển thị các cột **thực sự cần thiết** cho nghiệp vụ, KHÔNG hiển thị tất cả.
   - **Loại bỏ cột thừa**: Nếu related_list nằm trên layout của Object A, thì cột lookup trỏ về Object A là **thừa** (vì đang xem bản ghi A rồi). Ví dụ: related_list Ticket trên layout Contact → loại bỏ cột `contact`.
   - **Ưu tiên cột quan trọng**: Mã/serial, tên/tiêu đề, trạng thái, người phụ trách, loại, mức ưu tiên.
   - **Loại bỏ cột hệ thống ít dùng**: `id`, `created_by`, `updated_by`, `last_activity_time`, `call_id` thường không cần hiển thị trên bảng danh sách liên quan.
   - **Cân nhắc ngữ cảnh**: Tuỳ vào object liên quan và nghiệp vụ cụ thể mà chọn cột phù hợp.
   - Số lượng cột hiển thị nên từ **5-10 cột** để bảng không quá rộng.

2. **Thiết lập độ rộng cột (`width`) hợp lý:**
   - **Cột mã/serial** (auto_number): `80-100px` — nội dung ngắn.
   - **Cột tên/tiêu đề** (short_text, là trường chính): `250-400px` — cần rộng để đọc được nội dung.
   - **Cột trạng thái/select** (select, status): `100-140px` — hiển thị badge/tag.
   - **Cột lookup** (lookup_normal): `150-200px` — hiển thị tên bản ghi liên kết.
   - **Cột người phụ trách** (lookup tới personnel): `130-160px` — hiển thị tên người.
   - **Cột ngày tháng** (datetime, date): `160-200px` — cần đủ rộng cho format ngày giờ.
   - **Cột boolean**: `80-100px` — chỉ hiển thị checkbox/icon.
   - **Cột mô tả** (long_text): `200-300px` — nếu cần hiển thị.
   - **Cột file/đính kèm**: `150-200px`.
   - **Cột hành động** (`_action_column`): luôn `40px`.

3. **Thứ tự cột trong `showingColumns`:**
   - Cột mã/serial → Cột tên → Cột trạng thái → Cột người phụ trách → Các cột nghiệp vụ → Cột ngày tháng → `_action_column`

4. **Lưu ý format:** `tableSettings` phải được chuyển thành **chuỗi JSON** (escape quotes). Ví dụ:
   ```json
   "tableSettings": "{\"columns\":[{\"key\":\"serial\",\"width\":90},{\"key\":\"name\",\"width\":300},...],\"pinnedColumns\":{\"left\":[],\"right\":[\"_action_column\"]},\"showingColumns\":[\"serial\",\"name\",...,\"_action_column\"],\"editableColumns\":[]}"
   ```

5. **Quy tắc thiết lập `editableColumns` (QUAN TRỌNG cho layout tạo bản ghi có related list):**

   Khi related list cần cho phép người dùng nhập/sửa dữ liệu trực tiếp trên bảng (đặc biệt trên layout tạo bản ghi), cần cấu hình `editableColumns` hợp lý:

   - **Cột NÊN đưa vào `editableColumns`**: Các cột mà người dùng cần nhập giá trị — ví dụ: sản phẩm (lookup), số lượng, đơn giá, đơn vị, chiết khấu, thuế, phí,...
   - **Cột KHÔNG đưa vào `editableColumns`**:
     - Cột tính toán tự động (`formula`, `rollup_summary`) — ví dụ: thành tiền, tổng giá, tổng phụ.
     - Cột hệ thống (`id`, `name` nếu là `auto_number`, `created`, `updated`, `created_by`, `updated_by`).
     - Cột chỉ đọc (`manualModifyAllow: false`, `readOnly: true`).
     - Cột lookup trỏ về object cha (vì giá trị này được tự động gán khi tạo bản ghi con từ bản ghi cha).
   - **Ví dụ**: Layout tạo Đơn hàng có bảng "Sản phẩm trong đơn hàng":
     - `editableColumns`: `["product", "quantity", "price_per_unit", "unit", "discount_by_unit", "tax_by_unit", "fee_by_unit"]`
     - `showingColumns`: gồm các cột editable + cột tính toán chỉ xem (`total_price`) + `_action_column`
     - Cột `order` (lookup về Order) bị loại khỏi `showingColumns` vì thừa.
   - **Tham khảo file mẫu**: `assets/sample_layout_create_order.json`

---

### pageSettings

Cấu hình trang layout. Gồm 2 phần chính: **settingPage** (cấu hình toàn bộ trang) và **settingContentPage** (cấu hình phần nội dung bên trong trang).

```json
{
  "id": "<uuid>",
  "slug": "page_setting_<timestamp>",
  "fieldType": "page_settings",
  "settingPage": {
    "paddingTop": 0,
    "paddingBottom": 0,
    "paddingLeft": 0,
    "paddingRight": 0,
    "color": "#dcdde9",
    "combinationRatio": 100,
    "css": "",
    "typeColor": "primary",
    "apiUrlSubmit": "",
    "createOtherRecord": false,
    "copyValueType": 0,
    "copyFieldSlugs": []
  },
  "settingContentPage": {
    "paddingTop": 20,
    "paddingBottom": 20,
    "paddingLeft": 20,
    "paddingRight": 20,
    "borderColor": "#dcdde9",
    "isShowBorder": false,
    "color": "#dcdde9",
    "combinationRatio": 100,
    "css": "",
    "typeBorder": "primary",
    "maxWidth": 100,
    "typeColor": "primary",
    "unitMaxWidth": "%"
  },
  "settingBreadcrumbsPageCreate": {
    "isShow": true,
    "isShowTitle": true,
    "typeShowTitle": "default",
    "title": ""
  },
  "settingBreadcrumbsPageViewEdit": {
    "isShow": true,
    "isShowTitle": true,
    "typeShowTitle": "default",
    "title": ""
  },
  "buttons": {}
}

> **Lưu ý về `buttons`:** Đây là cấu hình các Object Button hiển thị trên vùng action/header của layout xem/sửa. Danh sách nằm tại `pageSettings.buttons.listButton`; mỗi entry tham chiếu button bằng `buttonId` và `slug`, đồng thời chứa cấu hình hiển thị như `type`, `size`, icon và `customName`. Để `{}` nếu layout không có record-level custom button. Xem [references/record-button-placement.md](references/record-button-placement.md) để biết schema và quy trình update an toàn.
```

#### Giải thích chi tiết settingPage (cấu hình toàn bộ trang)

`settingPage` quy định thuộc tính của **toàn bộ trang** — tức vùng nền bao quanh phần nội dung.

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `paddingTop` | Number | Khoảng cách từ mép trên trang đến phần nội dung (px) |
| `paddingBottom` | Number | Khoảng cách từ mép dưới trang đến phần nội dung (px) |
| `paddingLeft` | Number | Khoảng cách từ mép trái trang đến phần nội dung (px) |
| `paddingRight` | Number | Khoảng cách từ mép phải trang đến phần nội dung (px) |
| `color` | String | Mã màu HEX của primary color |
| `combinationRatio` | Number | Tỷ lệ pha trộn màu nền (%). Ví dụ: `95` = 95% màu trắng (light mode) hoặc đen (dark mode) + 5% primary color. `100` = hoàn toàn trắng/đen, không pha màu |
| `typeColor` | String | Loại màu: `"primary"` |
| `css` | String | CSS tùy chỉnh (thường để trống) |
| `apiUrlSubmit` | String | URL API submit tùy chỉnh (thường để trống) |
| `createOtherRecord` | Boolean | Cho phép tạo bản ghi liên quan ngay sau khi tạo bản ghi chính. Mặc định: `false` |
| `copyValueType` | Number | Chế độ copy giá trị khi tạo bản ghi mới từ bản ghi hiện tại: `0` = không copy, `1` = copy tất cả, `2` = chỉ copy các field trong `copyFieldSlugs`, `3` = copy tất cả ngoại trừ các field trong `copyFieldSlugs` |
| `copyFieldSlugs` | Array | Danh sách slug các field liên quan đến `copyValueType`. Mảng rỗng nếu `copyValueType` là `0` hoặc `1` |

#### Giải thích chi tiết settingContentPage (cấu hình phần nội dung)

`settingContentPage` quy định thuộc tính của **phần nội dung trang** — tức vùng chứa các Row/Column/Section, nằm bên trong vùng trang (`settingPage`).

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| `paddingTop` | Number | Padding trên của phần nội dung (px). Mặc định: `20` |
| `paddingBottom` | Number | Padding dưới của phần nội dung (px). Mặc định: `20` |
| `paddingLeft` | Number | Padding trái của phần nội dung (px). Mặc định: `20` |
| `paddingRight` | Number | Padding phải của phần nội dung (px). Mặc định: `20` |
| `maxWidth` | Number | Chiều rộng tối đa của phần nội dung. Đơn vị phụ thuộc vào `unitMaxWidth` |
| `unitMaxWidth` | String | Đơn vị của `maxWidth`: `"px"` (pixel) hoặc `"%"` (phần trăm chiều rộng trang) |
| `borderColor` | String | Mã màu HEX của viền |
| `isShowBorder` | Boolean | Hiển thị viền bao quanh phần nội dung |
| `color` | String | Mã màu HEX |
| `combinationRatio` | Number | Tỷ lệ pha trộn màu nền phần nội dung (%). Thường để `100` |
| `typeBorder` | String | Loại viền: `"primary"` |
| `typeColor` | String | Loại màu: `"primary"` |
| `css` | String | CSS tùy chỉnh (thường để trống) |

#### Hướng dẫn chọn pageSettings theo loại layout

**Layout Tạo bản ghi — pageSettings mặc định bắt buộc nếu người dùng không yêu cầu khác:**
```json
{
  "settingPage": {
    "paddingTop": 0, "paddingBottom": 0, "paddingLeft": 0, "paddingRight": 0,
    "combinationRatio": 100, "color": "#dcdde9", "typeColor": "primary"
  },
  "settingContentPage": {
    "paddingTop": 20, "paddingBottom": 20, "paddingLeft": 20, "paddingRight": 20,
    "maxWidth": 100, "unitMaxWidth": "%",
    "isShowBorder": false, "borderColor": "#dcdde9", "combinationRatio": 100
  }
}
```
→ Trang không có padding ngoài, nền dùng màu chính kết hợp 100% trắng/đen theo chế độ giao diện, vùng nội dung chiếm 100% chiều rộng và không có border. Đây là cấu hình của `pageSettings`; độ rộng form thực tế phải được quyết định riêng trên Layout Row ngoài cùng.

**Layout Row ngoài cùng của layout Tạo dạng form thông thường:**
```json
{
  "maxWidth": 1000,
  "unitMaxWidth": "px",
  "horizontalAlignment": "center"
}
```
→ Dùng làm mặc định cho form không có bảng rộng để input không bị kéo dài không cần thiết.

**Layout Row ngoài cùng của layout Tạo có bảng danh sách liên quan hoặc component rộng:**
```json
{
  "maxWidth": 100,
  "unitMaxWidth": "%",
  "horizontalAlignment": "center"
}
```
→ Dành toàn bộ chiều ngang cho bảng, giảm nhu cầu cuộn ngang. `sample_layout_create_order.json` chỉ là mẫu cấu trúc field/related list; khi dựng payload phải bổ sung cấu hình Row theo quy tắc này nếu asset chưa có đủ ba thuộc tính.

**Layout Xem/Sửa bản ghi** (nội dung full màn hình):
```json
{
  "settingPage": {
    "paddingTop": 0, "paddingBottom": 0, "paddingLeft": 0, "paddingRight": 0,
    "combinationRatio": 100, "color": "#dcdde9", "typeColor": "primary"
  },
  "settingContentPage": {
    "paddingTop": 20, "paddingBottom": 20, "paddingLeft": 20, "paddingRight": 20,
    "maxWidth": 100, "unitMaxWidth": "%",
    "isShowBorder": false, "combinationRatio": 100
  }
}
```
→ Trang không padding, nền trắng/đen thuần, nội dung chiếm 100% chiều rộng.

---

## Quy tắc sinh UUID và slug

1. **UUID**: Sinh UUID v4 chuẩn cho tất cả các `id` của layoutRow, layoutColumn, section, tab, group và component đặc biệt không phải Object Field như `path_component`.
2. **Slug có ý nghĩa cho container và component được sinh mới**:
   - Áp dụng format mặc định `{type_prefix}_{meaningful_name}` cho `layoutRow`, `layoutColumn`, `section`, `tab`, `group`, `related_list`, `display_box`, `report`, `dashboard`, `button_group`, `path_component` và `workflow_button`.
   - Slug phải bắt đầu bằng đúng tiền tố loại thành phần: `layout_row_`, `layout_column_`, `section_`, `tab_`, `group_`, `related_list_`, `display_box_`, `report_`, `dashboard_`, `button_group_`, `path_component_` hoặc `workflow_button_`.
   - Đặt `meaningful_name` theo chức năng hoặc nội dung của thành phần; **bắt buộc dùng tiếng Anh**, chữ thường và `snake_case`. Quy tắc này không thay đổi theo ngôn ngữ của tên layout hoặc tên hiển thị. Tránh tên chung chung như `section_1`, `group_new` khi có thể suy ra ý nghĩa.
   - Nếu thành phần không có tên hiển thị, suy ra tên từ vai trò, vị trí hoặc các field bên trong, ví dụ `layout_column_contact_sidebar`, `section_system_information`, `group_address_fields`.
   - **Không thêm timestamp** vào slug của các loại trên.
   - **Không thêm index nếu base slug chưa bị trùng.** Chỉ khi base slug đã tồn tại, thêm hậu tố số nhỏ nhất tạo được slug duy nhất, ví dụ `section_system_information_2`, rồi `_3`, `_4`,...
   - Kiểm tra trùng với các slug đã có trên hệ thống và tất cả slug trong payload đang xây dựng. Nếu API vẫn trả lỗi slug đã tồn tại, tăng hậu tố số và gọi lại.
   - Ví dụ slug không trùng: `layout_row_main_content`, `tab_activities`, `related_list_order_items`, `display_box_contact_summary`, `report_sales_performance`.
3. **uiSlug** cho component:
   - Với Object Field, dùng format `{field_slug}_{số thứ tự}`, ví dụ `name_1`, `status_1`.
   - Với component được sinh mới, dùng format `{component_slug}_{số thứ tự}`, ví dụ `display_box_contact_summary_1`, `dashboard_sales_overview_1`.
4. **QUAN TRỌNG - Slug phải GLOBALLY UNIQUE**: Mỗi slug phải duy nhất trên **TOÀN BỘ hệ thống** (không chỉ trong 1 layout). Khi tạo nhiều layout cùng lúc hoặc liên tiếp:
   - Ưu tiên base slug có ý nghĩa và không có hậu tố số.
   - Chỉ thêm index khi có xung đột thực tế; không tự động thêm index cho mọi element.
   - Dùng số tăng dần nhỏ nhất chưa bị sử dụng cho cùng base slug. Ví dụ: `group_address_fields`, `group_address_fields_2`, `group_address_fields_3`.

## Quy tắc tạo layout

1. **`content` bắt buộc là array không rỗng**: `content.length > 0`. `null`, kiểu dữ liệu khác array hoặc `[]` đều là payload không hợp lệ và không được gửi tới API.
2. **Mỗi layoutRow** phải có ít nhất 1 layoutColumn.
3. **Mỗi layoutColumn** phải có ít nhất 1 section.
4. **Mỗi section** phải có ít nhất 1 tab (kể cả section `"normal"` cũng có 1 tab ẩn).
5. **Mỗi tab** phải có ít nhất 1 group.
6. **Mỗi group** phải có ít nhất 1 component.
7. **Object Field component `id`** phải khớp với `id` của field trong Object definition (lấy từ API `/objects/list`). Component đặc biệt như `path_component` dùng UUID v4 theo schema riêng.
8. **Không được duplicate field**: Mỗi field chỉ xuất hiện 1 lần trong toàn bộ layout (trừ khi nằm ở tab khác nhau trong section `"menu"`).
9. **colSpan** quyết định tỷ lệ chiều rộng cột. Tổng colSpan của các cột = `numberOfColumns` của layoutRow.
10. **Layout cho Object Form** phải có `functionLayout: 1`, quyền `ADD`, `isForm: 1`, `status: 1`, `isWeb: true` và content hợp lệ. Sau create, view/list lại và chỉ bàn giao ID khi `objectTypeSlug` cùng các thuộc tính trên khớp chính xác.

## Ví dụ sử dụng

### Ví dụ 1: Tạo layout đơn giản
```
Người dùng: /layout-creator
Agent: Bạn muốn tạo layout cho đối tượng nào?
Người dùng: Product
Agent: [Gọi /object-info để lấy fields của Product]
Agent: Đối tượng Product có N fields. Bạn mô tả layout mong muốn:
Người dùng: 1 hàng, 2 cột tỷ lệ 1:3. Cột 1 chứa field "active". Cột 2 chứa "name" và "code" nằm ngang.
Agent: [Xây dựng và kiểm tra JSON layout → gọi API tạo layout ngay → hiển thị kết quả]
```

### Ví dụ 2: Tạo layout có tab
```
Người dùng: Tạo layout cho Lead có 1 section dạng tab, Tab 1 chứa thông tin cơ bản, Tab 2 chứa hoạt động.
Agent: [Tạo section với typeSection: "menu", numberOfTabs: 2, mỗi tab chứa group tương ứng → kiểm tra payload → gọi API tạo ngay]
```

### Ví dụ 3: Cập nhật layout
```
Người dùng: Sửa layout "Create" của Product, thêm field "description" vào group đầu tiên.
Agent: [Gọi API view layout → hiển thị cấu trúc hiện tại → xây dựng layout mới]
Agent: [Kiểm tra payload hợp lệ → gọi API update layout ngay → view lại để xác minh]
```

### Ví dụ 4: Xoá layout
```
Người dùng: Xoá layout "Test Layout" của Product.
Agent: [Resolve chính xác layout "Test Layout" (ID: LOXXXXX) → nêu rõ thao tác không thể hoàn tác → kiểm tra tác động → gọi API delete → xác minh layout không còn tồn tại]
```

## Xử lý lỗi

| Lỗi | Cách xử lý |
|-----|------------|
| Field ID không tìm thấy | Thông báo field không tồn tại trong Object, hỏi lại |
| Object không tồn tại | Thông báo và hỏi lại slug đối tượng |
| Mô tả layout không rõ ràng | Hỏi lại chi tiết: bao nhiêu row, column, section, field nào ở đâu |
| Layout tham khảo có `content: null`, `content: []` hoặc cấp con rỗng | Không dùng làm payload và không gọi API. Dựng `content` mới từ fields của object cùng asset mẫu, rồi kiểm tra lại toàn bộ hierarchy |
| Chưa có credential phù hợp | Resolve theo `$cogover-api-auth`; chỉ hỏi qua kênh an toàn khi chưa có hoặc không truy cập được |
| HTTP 401 / 403 | API_KEY không hợp lệ, hết hạn hoặc không đủ quyền. Hiển thị lỗi và yêu cầu người dùng cung cấp lại hoặc kiểm tra quyền; không thử cơ chế xác thực khác |
| HTTP 422 hoặc API trả `r` khác `0` | Payload không được API v2 chấp nhận. Hiển thị `r`, `msg` và chi tiết lỗi an toàn từ response; dừng thao tác, không đổi endpoint |
| HTTP 500 | Lỗi server. Thông báo người dùng thử lại sau; không đổi endpoint |
| Update trả thành công nhưng view xác minh không khớp | Báo rõ dữ liệu chưa được lưu đúng và dừng; không fallback sang endpoint khác |

Mọi thao tác layout trong skill này chỉ được gọi qua `/bapi/v1/layouts_v2` với `Authorization: Bearer {API_KEY}`. Nếu API v2 không thực hiện được yêu cầu, phải báo lỗi rõ cho người dùng và dừng; không đổi endpoint hoặc cơ chế xác thực.
