# Tầng 1: Object Manager — Chi tiết đầy đủ

## Mục lục
1. [Skill chuyên trách](#skill-chuyên-trách)
2. [Phương pháp thiết kế Object](#phương-pháp-thiết-kế-object)
3. [Khái niệm Object](#khái-niệm-object)
4. [Định nghĩa Object & Field](#định-nghĩa-object--field)
5. [Layout Builder](#layout-builder)
6. [Hành động & Chuỗi hành động](#hành-động--chuỗi-hành-động)
7. [Quy tắc giao diện](#quy-tắc-giao-diện)
8. [Quy tắc bảo mật dữ liệu](#quy-tắc-bảo-mật-dữ-liệu)
9. [Quy tắc chuyển trạng thái](#quy-tắc-chuyển-trạng-thái)
10. [Quy tắc trùng lặp dữ liệu](#quy-tắc-trùng-lặp-dữ-liệu)
11. [Lịch sử thay đổi trường dữ liệu](#lịch-sử-thay-đổi-trường-dữ-liệu)

---

## Skill chuyên trách

| Nhu cầu | Skill nguồn chuẩn |
|---|---|
| Object, field, option, Formula, lookup và schema thật | [$object-info](../../object-info/SKILL.md) |
| Record và dữ liệu kiểm thử | [$object-record](../../object-record/SKILL.md) |
| Layout và form công khai | [$object-layout](../../object-layout/SKILL.md), [$object-form](../../object-form/SKILL.md) |
| Client script cho logic giao diện | [$layout-scripting](../../layout-scripting/SKILL.md) |
| Button, action chain và icon | [$object-button](../../object-button/SKILL.md), [$cogover-icon](../../cogover-icon/SKILL.md) |
| Saved filter và cấu hình bảng danh sách | [$object-filter](../../object-filter/SKILL.md) |
| Transition và Path Component | [$object-transition-rule](../../object-transition-rule/SKILL.md), [$object-path-component](../../object-path-component/SKILL.md) |
| Field history | [$object-history-tracking](../../object-history-tracking/SKILL.md) |
| User, Role, cơ cấu tổ chức và Data Security | [$user-permission](../../user-permission/SKILL.md) |

Bộ skill chưa có skill chuyên trách cho Duplicate Rules. Chỉ thiết kế ở mức khái niệm cho đến khi có tài liệu sản phẩm hoặc API chính thức được hỗ trợ; không suy đoán thao tác hoặc endpoint.

## Phương pháp thiết kế Object (Database-First Approach)

**Đây là phương pháp bắt buộc khi người dùng mô tả nghiệp vụ ứng dụng và yêu cầu thiết kế Object.** Hãy đóng vai trò chuyên gia thiết kế database trước, phân tích kỹ rồi mới mapping sang Cogover.

### Bước 1: Phân tích nghiệp vụ — Xác định Entity

Từ mô tả nghiệp vụ của người dùng, trích xuất các **entity** (thực thể dữ liệu) chính. Đặt câu hỏi:
- Hệ thống cần quản lý những **đối tượng** nào? (Mỗi đối tượng = 1 entity)
- Mỗi đối tượng có những **thuộc tính** gì? (Mỗi thuộc tính = 1 cột/field)
- Có những **hành vi/trạng thái** nào? (Workflow, lifecycle)

**Ví dụ**: Người dùng mô tả "quản lý dự án xây dựng":
→ Entities: Dự án (Project), Công việc (Task), Nhà thầu phụ (Subcontractor), Hợp đồng (Contract), Giai đoạn (Phase), Vấn đề (Issue)

### Bước 2: Thiết kế Database Schema — Xác định quan hệ

Vẽ mô hình quan hệ giữa các entity, giống thiết kế database truyền thống:

**Các loại quan hệ cần xác định:**

| Quan hệ DB | Ý nghĩa | Mapping sang Cogover |
|---|---|---|
| **1-N (One-to-Many)** | 1 bản ghi cha có nhiều bản ghi con | Object con dùng `lookup_normal` hoặc `reference` đến Object cha |
| **1-N phụ thuộc (cha-con chặt)** | Bản ghi con không tồn tại nếu thiếu cha | Dùng `reference`; xác minh hành vi xoá thật trước khi triển khai |
| **1-N tham chiếu (liên kết lỏng)** | Bản ghi con vẫn có ý nghĩa khi thiếu cha | Dùng `lookup_normal` |
| **N-N (Many-to-Many)** | Nhiều-nhiều | **Cách 1**: `lookup_normal` có nhiều giá trị. **Cách 2**: Tạo Object trung gian nếu quan hệ có thuộc tính riêng |
| **1-1 (One-to-One)** | 1-1 | `lookup_normal` và ràng buộc nghiệp vụ phù hợp; thường cân nhắc gộp cùng Object |

**Quy tắc chọn `reference` hay `lookup_normal`:**
- Xoá bản ghi cha → bản ghi con có còn ý nghĩa không?
  - **Không** → cân nhắc `reference`, ví dụ Order line gắn chặt với Order.
  - **Có** → dùng `lookup_normal`, ví dụ Contact vẫn có thể tồn tại độc lập với Account.
- Không mặc định suy ra cascade delete; đọc schema và contract thật bằng `$object-info`.

### Bước 3: Xác định kiểu dữ liệu cho từng cột

Với mỗi thuộc tính đã xác định, chọn kiểu dữ liệu phù hợp nhất:

| Loại dữ liệu | Cogover Field Type | Ghi chú |
|---|---|---|
| Tên, tiêu đề, chuỗi ngắn | `short_text` | Tối đa theo metadata và contract field |
| Mô tả, ghi chú dài | `long_text` | Cấu hình rich text bằng metadata khi phù hợp |
| Mã tự sinh (PK surrogate) | `auto_number` | Không dùng `short_text` nếu mã phải do hệ thống tự sinh |
| Số nguyên | `numeric` | Số lượng, đếm |
| Số thập phân | `decimal` | Hệ số, khối lượng có phần lẻ |
| Tiền tệ | `currency` | Xác minh metadata đơn vị trên workspace |
| Tính toán từ trường khác | `formula` | Cogover Scripting có cú pháp gần Java, dùng cho logic tính toán phức tạp |
| Ngày | `date` | Ngày sinh, ngày hết hạn |
| Ngày + giờ | `date_time` | Thời điểm cụ thể, lịch hẹn |
| Email, SĐT, URL | `email` / `phone` / `url` | Dữ liệu liên hệ có metadata chuyên biệt |
| Trạng thái, phân loại (chọn 1) | `single_choice` | Định nghĩa options + state types |
| Tags, kỹ năng (chọn nhiều) | `multi_choices` | Cho phép chọn nhiều |
| Cờ bật/tắt | `boolean` | TRUE/FALSE |
| File đính kèm | `file` | Cấu hình multiple trong metadata nếu cần |
| FK đến entity khác | `lookup_normal` hoặc `reference` | Xem Bước 2 |
| FK đến user/nhân sự | `lookup_normal` → Personnel | Xác minh metadata/default bằng `$object-info` |

### Bước 4: Mapping sang Cogover Object — Thứ tự tạo

**Quan trọng**: Tạo Object theo thứ tự phụ thuộc — Object được lookup đến phải tạo trước.

```
1. Xác định thứ tự: Object nào không phụ thuộc ai → tạo trước
2. Object nào có Lookup đến Object khác → tạo sau Object đích
3. Object nào dùng `reference` → tạo sau Object cha
```

**Ví dụ thứ tự tạo cho hệ thống quản lý đơn hàng:**
1. `Customer` (không phụ thuộc)
2. `Product` (không phụ thuộc)
3. `Order` (`lookup_normal` → Customer)
4. `Order line item` (`reference` → Order, `lookup_normal` → Product)

### Bước 5: Bổ sung Cogover-Specific Features

Sau khi mapping database schema xong, bổ sung thêm các tính năng mà database thuần không có:

| Tính năng Cogover | Khi nào bổ sung |
|---|---|
| **Owner** (`lookup_normal` → Personnel) | Khi nghiệp vụ cần người sở hữu; xác minh default thực tế |
| **Transition Rules** | Khi Object có trường trạng thái (Single choice với state types) |
| **UI Rules** | Khi cần ẩn/hiện/bắt buộc trường theo điều kiện |
| **Data Security Rules** | Khi cần phân quyền xem bản ghi theo owner/phòng ban/vai trò |
| **Duplicate Rules** | Khi cần kiểm tra trùng lặp (Email, SĐT, Mã,...) |
| **Field Change History** | Khi cần audit trail cho trường trạng thái, giá trị, owner |
| **Layout Builder** | Luôn luôn — thiết kế form tạo/xem/sửa bản ghi |
| **Actions & Sequences** | Khi có hành động tuỳ chỉnh trên bản ghi |

### Bước 6: Trình bày kết quả cho người dùng

Khi trình bày thiết kế Object, hãy theo format:

1. **Phân tích nghiệp vụ**: Tóm tắt các entity đã xác định và lý do
2. **Sơ đồ quan hệ**: Mô tả quan hệ giữa các entity (dùng text hoặc diagram)
3. **Chi tiết từng Object**: Liệt kê các trường, kiểu dữ liệu, lookup, options
4. **Thứ tự tạo Object**: Từ Object độc lập → Object phụ thuộc
5. **Module bổ trợ**: Đề xuất Transition Rules, UI Rules, Data Security, Flow,...

### Ví dụ minh hoạ: Thiết kế hệ thống "Quản lý bảo trì thiết bị"

**Nghiệp vụ**: Công ty sản xuất cần quản lý thiết bị, lịch bảo trì định kỳ, và các yêu cầu sửa chữa.

**Bước 1 — Entity:**
- Thiết bị (Equipment), Loại thiết bị (Equipment category), Yêu cầu bảo trì (Maintenance request), Lịch bảo trì (Maintenance schedule), Phụ tùng (Spare part), Phụ tùng sử dụng (Part usage)

**Bước 2 — Quan hệ:**
- Equipment category → Equipment (1-N, `lookup_normal`)
- Equipment → Maintenance request (1-N, `lookup_normal`)
- Equipment → Maintenance schedule (1-N, `reference`, vì lịch bảo trì gắn chặt với thiết bị)
- Maintenance request → Part usage (1-N, `reference`)
- Part usage → Spare part (N-1, `lookup_normal`)

**Bước 3 — Kiểu dữ liệu:**
- Equipment: Mã thiết bị (`auto_number`), Tên (`short_text`), Loại (`lookup_normal` → Equipment category), Vị trí (`short_text`), Ngày mua (`date`), Trạng thái (`single_choice`), Owner (`lookup_normal` → Personnel)
- Maintenance request: Mã yêu cầu (`auto_number`), Thiết bị (`lookup_normal` → Equipment), Mô tả (`long_text`), Mức ưu tiên (`single_choice`), Trạng thái (`single_choice`), Người yêu cầu (`lookup_normal` → Personnel), Files (`file`, multiple)

**Bước 4 — Thứ tự tạo:**
1. Equipment category → 2. Spare part → 3. Equipment → 4. Maintenance schedule → 5. Maintenance request → 6. Part usage

**Bước 5 — Cogover features:**
- Transition Rules cho Equipment.Trạng thái (chỉ cho chuyển Hoạt động↔Bảo trì, Bảo trì→Hỏng)
- Data Security (kỹ thuật viên thấy yêu cầu được gán, manager thấy tất cả)
- Field Change History cho Equipment.Trạng thái và Maintenance request.Trạng thái
- Triggered Flow khi yêu cầu mới được tạo → thông báo kỹ thuật viên
- Scheduled Flow nhắc bảo trì định kỳ

---

## Khái niệm Object

Object Manager là tầng nền tảng của Cogover Platform, giúp biến mọi loại dữ liệu thành Object có cấu trúc. Có thể hiểu Object Manager như một Database trực quan:

- **Object** = Bảng (Table) trong Database, nhưng có sẵn giao diện, phân quyền, và nhiều module quản trị
- **Field** = Cột (Column) trong bảng
- **Record** = Dòng (Row) / Bản ghi

**Ví dụ thực tế:**
- Dữ liệu "Khách hàng tiềm năng" → Object "Lead" với các trường: Tên, Email, Điện thoại, Trạng thái,...
- Dữ liệu "Khách hàng cá nhân" → Object "Contact" với các trường: Họ tên, Email, Tài khoản (lookup đến Account),...
- Dữ liệu "Cơ hội bán hàng" → Object "Opportunity" với các trường: Tên, Giai đoạn, Doanh thu dự kiến,...

Khi tạo custom Object, contract có thể khởi tạo standard field, layout, button và filter theo cấu hình. Quyền CRUD và phạm vi record vẫn phải được thiết kế, cấu hình và kiểm thử riêng.

## Định nghĩa Object & Field

### Quy trình tạo Object

1. **Xác định cần Object nào** — dựa trên dữ liệu doanh nghiệp cần quản lý
2. **Xác định các trường** — mỗi thông tin = 1 trường với loại dữ liệu phù hợp
3. **Kiểm tra quan hệ** — nếu có trường lookup, Object đích phải tồn tại trước
4. **Tạo Object** — hệ thống cung cấp giao diện tạo Object với form định nghĩa trường

### Quy tắc đặt tên

**Tên hiển thị:**
- Dùng tên nghiệp vụ rõ nghĩa và nhất quán ngôn ngữ, ví dụ `Expense category` hoặc bản dịch tương ứng.
- Không dùng dấu `*` trong tên field để biểu diễn bắt buộc; cấu hình thuộc tính `required` theo `$object-info`.
- Chọn tên file field theo ngữ nghĩa nghiệp vụ, không áp một tên cố định cho mọi Object.

**Tên kỹ thuật:**
- Phân biệt tên hiển thị với `slug`; resolve và kiểm tra tính duy nhất trên workspace.
- Không tự suy diễn slug hoặc đổi tên field/Object đang được layout, process, formula, filter hoặc report tham chiếu.

### Trường tự sinh

Khi cần mã do hệ thống tự sinh để phân biệt bản ghi, dùng `auto_number` thay vì `short_text` nhập tay.

### Trường Owner (Người sở hữu)

Object có nghiệp vụ sở hữu có thể dùng trường Owner:
- Loại: `lookup_normal` → Personnel
- Default thường gặp: `$currentUser`; luôn đọc metadata thật trước khi tạo hoặc sửa

### Object có sẵn trong hệ thống

Một workspace CRM có thể đã có các Object như Lead, Opportunity, Contact, Account, Contract, Activity, Ticket hoặc Product. Luôn dùng `$object-info` kiểm tra state thật trước khi quyết định tái sử dụng, mở rộng hoặc tạo Object mới.

Xem [hướng dẫn chọn Object Field](object-fields.md), sau đó dùng `$object-info` để đọc và thay đổi schema thật.

---

## Layout Builder

Layout Builder cho phép admin thiết kế giao diện bằng cách kéo thả. Cogover có 3 loại layout theo `functionLayout`.

Ngoài bố cục kéo thả, layout có thể chứa JavaScript tại `pageSettings.script`. Dùng `$layout-scripting` để triển khai rule giao diện phức tạp như ẩn/hiện, bắt buộc, chỉ đọc, giới hạn options, tự động điền giá trị, truy vấn record hoặc xử lý related list. Khi thêm hoặc sửa script trên layout hiện có, bắt buộc dùng `$object-layout` lấy script hiện tại trước và patch đúng phạm vi để không làm mất logic cũ.

### 1. Giao diện Tạo bản ghi (Create Form)

- Admin vào Layout Builder, kéo các trường từ danh sách bên trái vào vùng thiết kế
- Chia giao diện thành các **Section** (phần) và **Group** (nhóm)
- Cấu hình số cột hiển thị (1, 2, 3 cột)
- Người dùng cuối sẽ thấy form tạo bản ghi với bố cục đã thiết kế

**Ví dụ**: Giao diện tạo Lead có thể chia thành:
- Section "Thông tin khách hàng tiềm năng": Tiêu đề, Họ, Tên, Trạng thái, Người sở hữu,...
- Section "Thông tin bổ sung": Công ty, Doanh thu hàng năm,...

### 2. Giao diện Xem/Sửa bản ghi (View/Edit Form)

- Thiết kế tương tự nhưng phức tạp hơn — hỗ trợ nhiều Layout Row, nhiều Layout Column
- Có thể có Section dạng Tab (nhiều tab trong 1 section)
- Hiển thị đầy đủ thông tin bản ghi với Activities, Related records,...

**Ví dụ**: Giao diện xem Lead có:
- Phần trên: Avatar, Tiêu đề, Trạng thái, các trường chính
- Phần dưới: Tab Activities (hoạt động), Tab Related (liên quan)
- Sidebar phải: Thông tin khác (Người sở hữu, Công ty, Doanh thu,...)

### 3. Giao diện kết hợp Tạo/Xem/Sửa

Dùng khi một layout cần phục vụ cả ba ngữ cảnh. Với layout tạo record, thuộc tính `isForm` còn phân biệt layout tạo record nội bộ và public form. Luôn dùng `$object-layout` để đọc support matrix, kiểm tra state hiện có và merge thay đổi an toàn.

### Cấu trúc Layout

```
Layout Row
├── Layout Column (có thể nhiều cột)
│   ├── Section (phần - có thể có tab)
│   │   ├── Tab 1
│   │   │   ├── Group 1 (nhóm trường)
│   │   │   │   ├── Field 1
│   │   │   │   ├── Field 2
│   │   │   │   └── ...
│   │   │   └── Group 2
│   │   └── Tab 2
│   └── Section 2
└── Layout Column 2
```

Mỗi Group có thể cấu hình số cột (numberOfColumns) để các trường hiển thị theo grid.

---

## Hành động & Chuỗi hành động

### Hành động (Action)

Hành động là các thao tác có thể thực hiện trên bản ghi của Object. Cogover cho phép định nghĩa hành động tuỳ chỉnh ngoài các hành động mặc định (Tạo, Sửa, Xoá).

**Ví dụ hành động tuỳ chỉnh:**
- "Chuyển đổi Lead thành Contact" — tạo Contact từ dữ liệu Lead
- "Gửi email chào mừng" — tự động gửi email khi tạo bản ghi mới
- "Tính lại tổng đơn hàng" — cập nhật trường Formula

### Chuỗi hành động (Action Sequence)

Chuỗi hành động nối nhiều hành động lại thành workflow tự động. Khi hành động đầu tiên hoàn thành, hành động tiếp theo tự động chạy.

**Ví dụ chuỗi hành động:**
1. Tạo Lead mới → 2. Gửi email xác nhận → 3. Gán cho nhân viên sales → 4. Tạo reminder follow-up

Triển khai bằng `$object-button`; phối hợp `$object-layout`, `$object-filter` và `$cogover-icon` khi action cần được đặt lên giao diện, giới hạn theo filter hoặc gắn icon.

---

## Quy tắc giao diện

Quy tắc giao diện (UI Rules) cho phép điều khiển hiển thị giao diện động dựa trên điều kiện dữ liệu. Rule đơn giản có thể cấu hình trực tiếp; nghiệp vụ phức tạp có thể dùng JavaScript qua `$layout-scripting`.

### Các loại quy tắc

1. **Hiển thị/Ẩn trường**: Trường chỉ hiển thị khi điều kiện được thoả mãn
   - Ví dụ: Trường "Lý do từ chối" chỉ hiện khi Trạng thái = "Từ chối"

2. **Bắt buộc/Không bắt buộc**: Trường trở thành bắt buộc khi điều kiện thoả mãn
   - Ví dụ: Trường "Ngày hết hạn" bắt buộc khi Loại = "Hợp đồng có thời hạn"

3. **Chỉ đọc**: Trường không cho sửa khi điều kiện thoả mãn
   - Ví dụ: Không cho sửa "Giá trị" khi Trạng thái = "Đã phê duyệt"

### Cấu trúc quy tắc

Mỗi quy tắc gồm:
- **Điều kiện**: Khi nào quy tắc áp dụng (trường A = giá trị X, trường B > giá trị Y,...)
- **Logic kết hợp**: AND (tất cả điều kiện đúng) hoặc OR (ít nhất 1 đúng) hoặc CUSTOM
- **Hành động**: Ẩn trường, bắt buộc trường, hoặc chỉ đọc trường

Project chưa có skill declarative UI Rules riêng. Khi logic được thực hiện bằng client script, dùng `$layout-scripting` cùng `$object-layout`; không suy đoán contract của UI Rules từ overview.

---

## Quy tắc bảo mật dữ liệu

Quy tắc bảo mật dữ liệu kiểm soát ai được xem/sửa/xoá bản ghi nào. Đây là tầng phân quyền ở cấp bản ghi (record-level security), bổ sung cho phân quyền cấp Object.

### Các khả năng chính

1. **Phân quyền theo Owner**: Chỉ người sở hữu bản ghi mới thấy/sửa được
2. **Phân quyền theo phòng ban**: Chỉ nhân viên cùng phòng mới thấy bản ghi của phòng
3. **Phân quyền theo vai trò**: Manager thấy bản ghi của cấp dưới
4. **Chia sẻ bản ghi**: Cho phép chia sẻ bản ghi cụ thể cho nhân sự khác với quyền tuỳ chỉnh (xem/sửa)

### Ứng dụng thực tế

- **Sales**: Mỗi nhân viên sales chỉ thấy Lead/Opportunity của mình, Manager thấy tất cả của team
- **Support**: Agent chỉ thấy Ticket được gán, Supervisor thấy tất cả
- **HR**: Nhân sự chỉ thấy hồ sơ của mình, HR Manager thấy tất cả

Dùng `$user-permission` để đọc và cấu hình Role, Object permission và Data Security Rule; luôn snapshot quyền hiện có trước khi thay đổi.

---

## Quy tắc chuyển trạng thái

Quy tắc chuyển trạng thái (Transition Rules) kiểm soát luồng chuyển đổi giữa các trạng thái của bản ghi — trạng thái nào được phép chuyển sang trạng thái nào, ai được phép chuyển, và điều gì xảy ra khi chuyển.

### Các thành phần

1. **Chuyển đổi cho phép**: Định nghĩa A → B được phép, A → C không được phép
   - Ví dụ: Lead "Mới" có thể chuyển sang "Đang làm việc" hoặc "Không hợp lệ", nhưng không thể nhảy thẳng sang "Đã chuyển đổi"

2. **Điều kiện trước chuyển đổi**: Kiểm tra điều kiện trước khi cho phép chuyển
   - Ví dụ: Chỉ cho chuyển Opportunity sang "Đã đóng thắng" khi Doanh thu > 0

3. **Hành động trước/sau chuyển đổi**: Tự động thực hiện hành động khi chuyển trạng thái
   - Ví dụ: Khi chuyển Lead sang "Đã chuyển đổi" → tự động tạo Contact mới

Dùng `$object-transition-rule` làm nguồn chuẩn để đọc, tạo và kiểm thử transition. Dùng thêm `$object-path-component` khi cần hiển thị tiến trình trạng thái trên layout.

---

## Quy tắc trùng lặp dữ liệu

Quy tắc trùng lặp phát hiện và xử lý bản ghi trùng lặp dựa trên các trường so sánh do admin cấu hình.

### Cách hoạt động

1. **Chọn trường so sánh**: Admin chọn trường nào dùng để phát hiện trùng (Email, Số điện thoại, Tên + Công ty,...)
2. **Logic so sánh**: Trùng chính xác hoặc trùng gần đúng
3. **Hành động khi trùng**: Cảnh báo người dùng, chặn tạo bản ghi, hoặc merge bản ghi

### Ứng dụng thực tế

- **CRM**: Phát hiện Lead trùng lặp dựa trên Email hoặc Số điện thoại
- **Contact**: Không cho tạo Contact trùng Email trong cùng Account
- **Sản phẩm**: Phát hiện sản phẩm trùng mã SKU

Project chưa có skill chuyên trách cho Duplicate Rules. Chỉ mô tả yêu cầu phát hiện trùng và tiêu chí so sánh; chưa được khẳng định có thể triển khai tự động từ project này.

---

## Lịch sử thay đổi trường dữ liệu (Field Change History)

Lịch sử thay đổi phù hợp khi Object có yêu cầu audit trail, truy vết trách nhiệm hoặc theo dõi vòng đời của một số field quan trọng. Không cần bật cho mọi Object hoặc mọi field.

### Cách hoạt động

Admin chọn các trường muốn hệ thống theo dõi. Sau khi bật, mỗi khi giá trị trường thay đổi, hệ thống tự động ghi nhận:
- **Giá trị trước** khi thay đổi
- **Giá trị sau** khi thay đổi
- **Ngày giờ** thực hiện thay đổi
- **Người thực hiện** thao tác

Dữ liệu lịch sử được hiển thị ngay trong giao diện xem bản ghi, giúp người dùng tra cứu nhanh.

### Trường hợp sử dụng phổ biến

Tính năng này có thể áp dụng cho Object có trường cần giám sát, không chỉ giới hạn ở CRM:

- **Lead status**: Biết Lead chuyển từ "Mới" sang "Đang làm việc" lúc nào, do ai → đánh giá tốc độ phản hồi sales
- **Opportunity stage**: Lịch sử di chuyển qua các giai đoạn bán hàng → phân tích pipeline, tìm bottleneck
- **Ticket status**: Biết ticket đã qua bao nhiêu trạng thái, mất bao lâu ở mỗi trạng thái → đánh giá SLA
- **Task status**: Theo dõi task chuyển từ "Chờ" → "Đang làm" → "Hoàn thành" → đánh giá hiệu suất nhân viên
- **Order status**: Theo dõi đơn hàng qua từng trạng thái xử lý → minh bạch với khách hàng
- **Approval status**: Theo dõi phê duyệt chi phí, hợp đồng → audit trail tuân thủ quy định
- **Giá trị hợp đồng/đơn hàng**: Biết ai đã thay đổi giá trị, từ bao nhiêu sang bao nhiêu → kiểm soát rủi ro
- **Người sở hữu (Owner)**: Theo dõi khi bản ghi được chuyển giao giữa nhân viên

### Khi nào nên đánh giá tính năng này

Đánh giá bật Lịch sử thay đổi trường khi:
- Người dùng hỏi về theo dõi, giám sát, audit trail
- Thiết kế Object có trường trạng thái (Single choice với start/intermediate/end state)
- Yêu cầu "biết ai đã thay đổi gì, khi nào"
- Cần đánh giá hiệu suất (thời gian ở mỗi trạng thái)
- Cần tuân thủ quy định (compliance, SOX, ISO,...)

Dùng `$object-history-tracking` để đọc cấu hình hiện có, bật tracking cho đúng Object/field và xác minh kết quả.
