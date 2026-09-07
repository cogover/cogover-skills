# Mẫu nghiệp vụ Object Button

Tài liệu này giải thích Object Button theo góc nhìn nghiệp vụ và phân tích hai cấu hình mẫu đã được ẩn danh. Đây là tài liệu tham khảo; không suy ra rằng ID, layout, field, option hay related list có thể dùng lại ở Workspace khác.

## Mục lục

1. [Object Button dùng để làm gì](#object-button-dùng-để-làm-gì)
2. [Mẫu 1: tạo Phiếu thu chi từ Hóa đơn bán hàng](#mẫu-1-tạo-phiếu-thu-chi-từ-hóa-đơn-bán-hàng)
3. [Mẫu 2: chuyển đổi Lead thành Account, Contact và Opportunity](#mẫu-2-chuyển-đổi-lead-thành-account-contact-và-opportunity)
4. [Cách thiết kế một bài toán mới](#cách-thiết-kế-một-bài-toán-mới)
5. [Cách dùng các tệp JSON](#cách-dùng-các-tệp-json)

## Object Button dùng để làm gì

Object Button là lớp hành động gắn với ngữ cảnh của một Object. Button biến một mục tiêu nghiệp vụ thành thao tác người dùng có thể chủ động kích hoạt ngay tại bản ghi hoặc danh sách đang làm việc.

Button đặc biệt hữu ích khi có một trong các nhu cầu sau:

- Rút ngắn một quy trình lặp lại nhiều lần, ví dụ từ hóa đơn mở form tạo phiếu thu và điền sẵn số tiền còn phải thu.
- Giữ dữ liệu nhất quán bằng cách lấy giá trị trực tiếp từ bản ghi nguồn thay vì để người dùng nhập lại.
- Tạo liên kết truy vết giữa bản ghi nguồn và bản ghi đích.
- Chuyển đổi một bản ghi nghiệp vụ thành nhiều bản ghi thuộc các Object khác nhau.
- Điều phối nhiều action theo thứ tự và cấp output của bước trước làm input cho bước sau.
- Kiểm soát trải nghiệm bằng layout, modal, field ẩn, field khóa, field cho phép sửa và bước có thể bỏ qua.

Có thể xem một button như một đặc tả gồm:

```text
Ngữ cảnh + ý định người dùng + action + input/mapping + kết quả + trải nghiệm
```

Một button đơn phù hợp với một kết quả chính. Một action chain phù hợp khi kết quả của nghiệp vụ gồm nhiều bản ghi hoặc có quan hệ phụ thuộc giữa các bước. Group button chỉ tổ chức nhiều lệnh độc lập trên giao diện và không thay thế action chain.

## Mẫu 1: tạo Phiếu thu chi từ Hóa đơn bán hàng

### Bài toán

Khi đang xem một `customer_invoice`, người dùng cần tạo nhanh một `cash_transaction` để ghi nhận việc thu tiền. Nếu nhập lại số tiền, loại tiền và hóa đơn liên quan bằng tay, thao tác chậm và dễ sai. Button **Create receipt voucher** đưa người dùng thẳng tới form tạo bản ghi đích và điền sẵn dữ liệu từ hóa đơn hiện tại.

### Cấu hình cốt lõi

| Thành phần | Giá trị thực tế | Ý nghĩa |
|---|---|---|
| Button ID | `BU00000000004` | ID của mẫu trong workspace nguồn |
| Object sở hữu | `customer_invoice` | Button được kích hoạt từ Hóa đơn bán hàng hiện tại |
| Action | `11` | Configurable create record |
| Object đích | `cash_transaction` | Tạo một Phiếu thu chi mới |
| Input | `[$currentRecord]` | Dùng hóa đơn đang xem làm ngữ cảnh |
| Layout | `LO00000000010` | Form dùng để tạo Phiếu thu chi |
| Hiển thị | `popupDisplayType: 1` | Mở modal giữa màn hình |

### Mapping dữ liệu

| Field đích | Giá trị | Loại | Cho sửa | Ý nghĩa |
|---|---|---|---:|---|
| `customer_invoice` | `$currentRecord` | Tham chiếu toàn bản ghi | Không | Liên kết phiếu với hóa đơn nguồn |
| `creation_source` | `from_customer_invoice` | Hằng số | Không | Ghi nhận nguồn tạo từ hóa đơn bán hàng |
| `status` | `creating` | Hằng số | Không | Khởi tạo trạng thái của phiếu |
| `amount` | `$currentRecord.remaining_amount` | Field động | Có | Lấy số tiền còn phải thu nhưng cho phép điều chỉnh |
| `currency` | `$currentRecord.currency` | Field động | Không | Giữ loại tiền nhất quán với hóa đơn |

Luồng người dùng:

1. Mở một Hóa đơn bán hàng.
2. Bấm **Create receipt voucher**.
3. Hệ thống mở form tạo Phiếu thu chi bằng layout đã cấu hình.
4. Form đã có liên kết hóa đơn, nguồn tạo, trạng thái, số tiền còn lại và loại tiền.
5. Người dùng kiểm tra hoặc sửa `amount`, rồi lưu.

### Đưa button lên giao diện xem bản ghi

Tạo thành công Object Button chỉ tạo ra định nghĩa hành động; nó không tự xuất hiện trên mọi giao diện xem bản ghi. Mẫu **Create receipt voucher** được đặt trên layout xem/sửa `LO00000000004` của `customer_invoice` tại:

```text
pageSettings.buttons.listButton
```

Layout mẫu giữ ba record-level button theo thứ tự:

1. `Create a replacement invoice`
2. `Create receipt voucher`
3. `Create Payment voucher`

Entry của button này chứa `buttonId: "BU00000000004"`, `slug: "create_receipt_voucher"`, kiểu hiển thị `gray`, kích thước `medium` và không dùng icon. Khi tái sử dụng bài toán, phải resolve layout xem/sửa của Object đích, giữ nguyên các entry hiện có và chống trùng theo `buttonId`.

Điểm kiểm soát quan trọng:

- Cấu hình live được quan sát không có autofill field riêng thể hiện rõ “Loại = Phiếu thu”. Có thể giá trị này đến từ layout/default hoặc một cơ chế khác, nhưng không được tự suy diễn. Khi thiết kế mới, phải xác minh field và option thật rồi mới thêm mapping nếu nghiệp vụ bắt buộc.
- `$currentRecord.remaining_amount` và `$currentRecord.currency` là tham chiếu field nên có `isVariable: 1`.
- `$currentRecord` khi được dùng như tham chiếu toàn bản ghi lookup đang được cấu hình với `isVariable: 0`. Không áp một quy tắc duy nhất cho mọi token bắt đầu bằng `$`.
- `allowEdit: 1` cho `amount` phản ánh quyết định nghiệp vụ: số tiền mặc định là toàn bộ số còn lại nhưng người dùng có thể thu một phần.

JSON request-oriented đã chuẩn hóa từ mẫu này, bao gồm cả entry đặt button vào layout xem/sửa, nằm tại [example-create-receipt-voucher.json](example-create-receipt-voucher.json).

### Các bài toán tương tự

- Từ đơn bán hàng tạo phiếu giao hàng với khách hàng, địa chỉ và danh sách hàng được điền sẵn.
- Từ hóa đơn mua hàng tạo phiếu chi với nhà cung cấp, số tiền và loại tiền tương ứng.
- Từ hợp đồng tạo phụ lục hoặc yêu cầu thanh toán, đồng thời giữ liên kết truy vết về hợp đồng nguồn.
- Từ ticket tạo nhiệm vụ xử lý với người phụ trách, mức ưu tiên và mô tả lấy từ ticket.

## Mẫu 2: chuyển đổi Lead thành Account, Contact và Opportunity

### Bài toán

Khi Lead đủ điều kiện, người dùng cần chuyển dữ liệu sang mô hình bán hàng chính thức: Account, Contact, Opportunity và quan hệ Contact Role. Đây không còn là một thao tác tạo bản ghi đơn vì các bản ghi sau cần tham chiếu bản ghi đã được tạo hoặc cập nhật ở bước trước.

Button **Convert** (`BUS0000000005`) dùng action chain `14` để điều phối bốn action con theo thứ tự.

### Đồ thị phụ thuộc

```text
Lead hiện tại
  ├─ bước 0: tạo/cập nhật Account ──────────────┐
  ├─ bước 1: tạo/cập nhật Contact <── Account ──┼─┐
  ├─ bước 2: tạo/cập nhật Opportunity <─ Account│ │
  └─ bước 3: tạo Contact Role <──── Contact + Opportunity
```

| Chain index | Action button | Loại | Input runtime | Có thể bỏ qua |
|---:|---|---:|---|---:|
| `0` | `BUS0000000002` – Create or update Account | `13` | Lead hiện tại | Không |
| `1` | `BUS0000000001` – Create or update Contact | `13` | Lead hiện tại + output bước `0` | Không |
| `2` | `BUS0000000003` – Create or update Opportunity | `13` | Lead hiện tại + output bước `0` | Có |
| `3` | `BUS0000000004` – Create Contact Role | `11` | Lead hiện tại + output bước `1` + output bước `2` | Có |

### Bước 0: Account

Action lấy dữ liệu công ty từ Lead để tạo hoặc cập nhật `account`:

- `name` ← `lead.company`
- `phones` ← `lead.business_phones`
- `websites` ← `lead.websites`
- `no_of_employees` ← `lead.no_of_employees`
- `annual_revenue` ← `lead.annual_revenue`
- `industry` ← `lead.industry`
- `originating_lead` ← Lead hiện tại

Action đồng thời cập nhật `lead.status` thành `Converted` và đồng bộ một related list từ Lead sang Account. Vì đây là bước nền tảng cho các bước sau, `allowSkip` của chain bằng `0`.

### Bước 1: Contact

Action tạo hoặc cập nhật `contact` từ thông tin cá nhân trên Lead:

- Tên, email, điện thoại, chức danh, địa chỉ, cờ không gọi và xưng hô lấy từ Lead.
- `originating_lead` trỏ về Lead hiện tại.
- `account` nhận `$input_2`, tức input slot thứ hai của action Contact. Trong chain, slot này được cấp từ output bước `0`.
- Một related list được đồng bộ từ Lead sang Contact.

`listSourceObject` của action là `[$currentRecord, account]`, tương ứng với hai input slot: Lead hiện tại và Account.

### Bước 2: Opportunity

Action tạo hoặc cập nhật `opportunity`:

- `name` lấy từ `lead.name`.
- `stage` mặc định là `needs_analysis`.
- `account` nhận `$input_2`, được chain cấp từ output bước `0`.
- `Originating_Lead` trỏ về Lead hiện tại.
- Một related list được đồng bộ từ Lead sang Opportunity.

Bước này có `allowSkip: 1`, phù hợp khi người dùng muốn chuyển đổi Lead nhưng chưa cần tạo Cơ hội.

### Bước 3: Contact Role

Action tạo `opportunity_contact_role` để liên kết Contact và Opportunity:

- `contact` nhận `$input_2`, được chain cấp từ output bước `1`.
- `opportunity` nhận `$input_3`, được chain cấp từ output bước `2`.
- `roles` để trống cho người dùng chọn.

Bước này cũng có `allowSkip: 1`. Vì nó phụ thuộc output Opportunity, nếu bước `2` bị bỏ qua thì phải bỏ qua bước `3` hoặc có cơ chế xử lý input thiếu; không được giả định output vẫn tồn tại.

### Quy tắc input cần nhớ

`sourceButtonIndex` và `$input_N` thuộc hai hệ quy chiếu khác nhau:

- `sourceButtonIndex` là index bắt đầu từ `0` của một bước chain trước đó.
- `$input_N` là slot input bắt đầu từ `1` của action con đang chạy.
- Thứ tự `inputs` của chain cấp dữ liệu cho các slot được mô tả bởi `listSourceObject` của action con.

Ví dụ ở bước Contact:

```json
{
  "listSourceObject": ["$currentRecord", "account"],
  "inputs": [
    {"isCurrentRecord": 1, "sourceButtonIndex": -1},
    {"isCurrentRecord": 0, "sourceButtonIndex": 0}
  ],
  "mapping": {"contact.account": "$input_2"}
}
```

Ở đây `$input_2` là Account vì slot thứ hai được cấp từ output chain step `0`; nó không có nghĩa là output chain step `2`.

JSON request-oriented của toàn bộ mẫu nằm tại [example-convert-lead.json](example-convert-lead.json). Tệp này là một gói tài liệu gồm năm payload riêng; không gửi nguyên cả wrapper tới một endpoint.

### Các bài toán tương tự

- Duyệt báo giá: tạo đơn hàng, lịch giao hàng và các dòng công việc liên quan.
- Onboarding khách hàng: tạo Account, Contact chính, hồ sơ triển khai và nhiệm vụ bàn giao.
- Kết thúc dự án: cập nhật dự án, tạo biên bản nghiệm thu, hóa đơn và nhiệm vụ thu hồi công nợ.
- Xử lý yêu cầu bảo hành: tạo case, lịch hẹn kỹ thuật, phiếu vật tư và liên kết người liên hệ.

## Cách thiết kế một bài toán mới

1. Viết mục tiêu nghiệp vụ dưới dạng: “Từ bản ghi/danh sách nào, người dùng bấm gì, để tạo/cập nhật kết quả gì?”.
2. Liệt kê Object nguồn, Object đích và mọi bản ghi trung gian.
3. Lập bảng mapping từng field: hằng số, field hiện tại, toàn bản ghi hiện tại hay output bước trước.
4. Quyết định button đơn, action chain hay group dựa trên phụ thuộc dữ liệu, không dựa vào số lượng tên gọi trên giao diện.
5. Với chain, vẽ đồ thị phụ thuộc trước; sau đó gán chain index, input slot và `sourceButtonIndex`.
6. Xác định field nào ẩn, khóa hoặc cho sửa dựa trên quyền quyết định của người dùng trong nghiệp vụ.
7. Tra metadata thật của workspace: Object slug, field slug/type, option, layout, related list và button ID.
8. Dựng payload, xác minh không có tham chiếu tiến/vòng và mọi `$input_N` đều có nguồn.
9. Chỉ ghi khi người dùng yêu cầu; sau khi ghi phải view lại để kiểm tra trạng thái đã lưu.

## Cách dùng các tệp JSON

Hai tệp JSON lưu cấu hình theo hướng request để dễ học và tái sử dụng:

- Bỏ các field server-managed, audit và workspace ID.
- Giữ `observedId` ngoài `createPayload` để liên hệ với mẫu thực tế.
- Chuẩn hóa `autofill.*[].value` thành JSON string như endpoint create/update mong đợi.
- Giữ ID layout, related list và button của workspace nguồn chỉ như bằng chứng của mẫu.

Trước khi áp dụng ở workspace khác:

1. Không gửi wrapper tài liệu hoặc `observedId` tới API.
2. Resolve lại mọi Object, field, option, layout, related list và button ID.
3. Tạo hoặc xác minh các action con trước, rồi thay `actionButtonId` trong payload chain bằng ID thật.
4. Xác minh ý nghĩa của `isVariable`, `allowEdit`, `isHidden`, `isOverwrite` và `allowSkip` theo yêu cầu mới.
5. Không tự thêm field “hợp lý” nếu mẫu live không chứa và metadata chưa xác nhận.
