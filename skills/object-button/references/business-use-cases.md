# Mẫu nghiệp vụ Object Button

Hai cấu hình mẫu đã ẩn danh, phân tích theo góc nhìn nghiệp vụ. Đây là tài liệu tham khảo: không suy ra rằng ID, layout, field, option hay related list trong mẫu dùng lại được ở Workspace khác.

## Object Button dùng để làm gì

Object Button là lớp hành động gắn với ngữ cảnh của một Object: biến một mục tiêu nghiệp vụ thành thao tác người dùng chủ động kích hoạt ngay tại bản ghi hoặc danh sách đang làm việc. Dùng button khi cần:

- Rút ngắn một quy trình lặp lại nhiều lần, ví dụ từ hóa đơn mở form tạo phiếu thu đã điền sẵn số tiền còn phải thu.
- Giữ dữ liệu nhất quán bằng cách lấy giá trị từ bản ghi nguồn thay vì nhập lại, và tạo liên kết truy vết giữa bản ghi nguồn và bản ghi đích.
- Chuyển đổi một bản ghi thành nhiều bản ghi thuộc các Object khác nhau, hoặc điều phối nhiều action theo thứ tự với output bước trước làm input bước sau.
- Kiểm soát trải nghiệm bằng layout, modal, field ẩn, field khóa, field cho phép sửa và bước có thể bỏ qua.

Chọn button đơn, action chain hay group button theo [Mô hình nghiệp vụ](../SKILL.md#mô-hình-nghiệp-vụ).

## Mẫu 1: tạo Phiếu thu chi từ Hóa đơn bán hàng

Khi đang xem một `customer_invoice`, người dùng bấm **Create receipt voucher** để mở thẳng form tạo `cash_transaction` đã điền sẵn dữ liệu từ hóa đơn, thay vì nhập lại số tiền, loại tiền và hóa đơn liên quan.

| Thành phần | Giá trị thực tế | Ý nghĩa |
|---|---|---|
| Button ID | `BU00000000004` | ID của mẫu trong workspace nguồn |
| Object sở hữu | `customer_invoice` | Kích hoạt từ Hóa đơn bán hàng hiện tại |
| Action | `11` | Configurable create record |
| Object đích | `cash_transaction` | Tạo một Phiếu thu chi mới |
| Input | `[$currentRecord]` | Hóa đơn đang xem làm ngữ cảnh |
| Layout | `LO00000000010` | Form tạo Phiếu thu chi |
| Hiển thị | `popupDisplayType: 1` | Modal giữa màn hình |

Mapping dữ liệu (`autofill.targetCreate`):

| Field đích | Giá trị | Loại | `isVariable` | `allowEdit` | Ý nghĩa |
|---|---|---|---:|---:|---|
| `customer_invoice` | `$currentRecord` | Tham chiếu toàn bản ghi (lookup) | `0` | `0` | Liên kết phiếu với hóa đơn nguồn |
| `creation_source` | `from_customer_invoice` | Hằng số | `0` | `0` | Ghi nhận nguồn tạo từ hóa đơn bán hàng |
| `status` | `creating` | Hằng số | `0` | `0` | Trạng thái khởi tạo của phiếu |
| `amount` | `$currentRecord.remaining_amount` | Field động | `1` | `1` | Mặc định toàn bộ số còn phải thu; người dùng có thể sửa để thu một phần |
| `currency` | `$currentRecord.currency` | Field động | `1` | `0` | Loại tiền nhất quán với hóa đơn |

Điểm kiểm soát:

- Tham chiếu field (`$currentRecord.remaining_amount`, `$currentRecord.currency`) có `isVariable: 1`; `$currentRecord` dùng như tham chiếu toàn bản ghi lookup lại có `isVariable: 0`. Không áp một quy tắc duy nhất cho mọi token bắt đầu bằng `$`.
- Cấu hình live không có autofill field thể hiện rõ "Loại = Phiếu thu"; giá trị này có thể đến từ layout/default hoặc một cơ chế khác, không được tự suy diễn. Thiết kế mới phải xác minh field và option thật rồi mới thêm mapping nếu nghiệp vụ bắt buộc.

Hiển thị trên màn bản ghi: button không tự xuất hiện sau khi tạo. Mẫu này được đặt trên layout xem/sửa `LO00000000004` của `customer_invoice` tại `pageSettings.buttons.listButton`, là entry thứ hai trong ba record-level button theo thứ tự `Create a replacement invoice`, `Create receipt voucher`, `Create Payment voucher`; entry gồm `buttonId: "BU00000000004"`, `slug: "create_receipt_voucher"`, kiểu hiển thị `gray`, kích thước `medium`, không dùng icon.

JSON request-oriented đã chuẩn hóa, gồm cả entry đặt button vào layout xem/sửa: [example-create-receipt-voucher.json](example-create-receipt-voucher.json).

Bài toán cùng dạng: từ đơn bán hàng tạo phiếu giao hàng (khách hàng, địa chỉ, danh sách hàng điền sẵn); từ hóa đơn mua hàng tạo phiếu chi (nhà cung cấp, số tiền, loại tiền); từ hợp đồng tạo phụ lục hoặc yêu cầu thanh toán giữ liên kết truy vết về hợp đồng nguồn; từ ticket tạo nhiệm vụ với người phụ trách, mức ưu tiên và mô tả lấy từ ticket.

## Mẫu 2: chuyển đổi Lead thành Account, Contact và Opportunity

Khi Lead đủ điều kiện, người dùng chuyển dữ liệu sang Account, Contact, Opportunity và quan hệ Contact Role. Đây không còn là một thao tác tạo bản ghi đơn vì các bản ghi sau cần tham chiếu bản ghi đã được tạo hoặc cập nhật ở bước trước: button **Convert** (`BUS0000000005`) dùng action chain `14` điều phối bốn action con theo thứ tự.

| Chain index | Action button | Loại | Input runtime | `allowSkip` |
|---:|---|---:|---|---:|
| `0` | `BUS0000000002` – Create or update Account | `13` | Lead hiện tại | `0` |
| `1` | `BUS0000000001` – Create or update Contact | `13` | Lead hiện tại + output bước `0` | `0` |
| `2` | `BUS0000000003` – Create or update Opportunity | `13` | Lead hiện tại + output bước `0` | `1` |
| `3` | `BUS0000000004` – Create Contact Role | `11` | Lead hiện tại + output bước `1` + output bước `2` | `1` |

- **Bước 0, Account:** `name` ← `lead.company`, `phones` ← `lead.business_phones`; `websites`, `no_of_employees`, `annual_revenue`, `industry` lấy field cùng tên của Lead; `originating_lead` ← Lead hiện tại. Action đồng thời cập nhật `lead.status` thành `Converted` (`autofill.source`) và đồng bộ một related list từ Lead sang Account (`syncRelatedList`). Là bước nền cho các bước sau nên `allowSkip: 0`.
- **Bước 1, Contact:** tên, email, điện thoại, chức danh, địa chỉ, cờ không gọi và xưng hô lấy từ Lead; `originating_lead` ← Lead hiện tại; `account` nhận `$input_2`, tức input slot thứ hai của action Contact, được chain cấp từ output bước `0`; một related list đồng bộ từ Lead sang Contact. `listSourceObject` của action là `["$currentRecord", "account"]`, tương ứng hai slot: Lead hiện tại và Account.
- **Bước 2, Opportunity:** `name` ← `lead.name`; `stage` mặc định `needs_analysis`; `account` nhận `$input_2` từ output bước `0`; `Originating_Lead` ← Lead hiện tại; một related list đồng bộ từ Lead sang Opportunity. `allowSkip: 1`: chuyển đổi Lead mà chưa cần tạo Cơ hội.
- **Bước 3, Contact Role (`opportunity_contact_role`):** `contact` nhận `$input_2` từ output bước `1`; `opportunity` nhận `$input_3` từ output bước `2`; `roles` để trống cho người dùng chọn. `allowSkip: 1`; vì phụ thuộc output Opportunity, nếu bước `2` bị bỏ qua thì phải bỏ qua bước `3` hoặc có cơ chế xử lý input thiếu, không được giả định output vẫn tồn tại.

Quy tắc input: `sourceButtonIndex` là index bắt đầu từ `0` của một bước chain đứng trước; `$input_N` là slot input bắt đầu từ `1` của action con đang chạy; thứ tự `inputs` của chain cấp dữ liệu cho các slot mà `listSourceObject` của action con mô tả. Ở bước Contact, `inputs` là `[{"isCurrentRecord": 1, "sourceButtonIndex": -1}, {"isCurrentRecord": 0, "sourceButtonIndex": 0}]` nên `$input_2` là Account lấy từ output chain step `0`, không phải output chain step `2`. Ví dụ JSON đầy đủ: [Quan hệ giữa input của Chain và `$input_N`](api-object-buttons.md#quan-hệ-giữa-input-của-chain-và-input_n).

JSON request-oriented của toàn bộ mẫu: [example-convert-lead.json](example-convert-lead.json), một gói tài liệu gồm năm payload riêng (`creationOrder`: bốn action con rồi mới đến chain); không gửi nguyên cả wrapper tới một endpoint.

Bài toán cùng dạng: duyệt báo giá (tạo đơn hàng, lịch giao hàng, các dòng công việc liên quan); onboarding khách hàng (Account, Contact chính, hồ sơ triển khai, nhiệm vụ bàn giao); kết thúc dự án (cập nhật dự án, biên bản nghiệm thu, hóa đơn, nhiệm vụ thu hồi công nợ); xử lý yêu cầu bảo hành (case, lịch hẹn kỹ thuật, phiếu vật tư, liên kết người liên hệ).

## Cách thiết kế một bài toán mới

1. Viết mục tiêu dạng "Từ bản ghi/danh sách nào, người dùng bấm gì, để tạo/cập nhật kết quả gì?"; liệt kê Object nguồn, Object đích và mọi bản ghi trung gian.
2. Lập bảng mapping từng field: hằng số, field hiện tại, toàn bản ghi hiện tại hay output bước trước.
3. Quyết định button đơn, action chain hay group dựa trên phụ thuộc dữ liệu, không dựa vào số lượng tên gọi trên giao diện. Với chain, vẽ đồ thị phụ thuộc trước, sau đó gán chain index, input slot và `sourceButtonIndex`.
4. Xác định field nào ẩn, khóa hoặc cho sửa dựa trên quyền quyết định của người dùng trong nghiệp vụ.
5. Tra metadata thật của workspace (Object slug, field slug/type, option, layout, related list, button ID); dựng payload và xác minh không có tham chiếu tiến/vòng, mọi `$input_N` đều có nguồn.
6. Chỉ ghi khi người dùng yêu cầu; sau khi ghi view lại để kiểm tra trạng thái đã lưu.

## Cách dùng các tệp JSON

Hai tệp JSON lưu cấu hình theo hướng request: đã bỏ field server-managed, audit và workspace ID; giữ `observedId` ngoài `createPayload` để liên hệ với mẫu thực tế; `autofill.*[].value` đã chuẩn hóa thành JSON string như endpoint create/update mong đợi; ID layout, related list và button của workspace nguồn chỉ là bằng chứng của mẫu.

Trước khi áp dụng ở workspace khác:

1. Không gửi wrapper tài liệu hoặc `observedId` tới API; resolve lại mọi Object, field, option, layout, related list và button ID.
2. Tạo hoặc xác minh các action con trước, rồi thay `actionButtonId` trong payload chain bằng ID thật.
3. Xác minh ý nghĩa của `isVariable`, `allowEdit`, `isHidden`, `isOverwrite` và `allowSkip` theo yêu cầu mới; không tự thêm field "hợp lý" nếu mẫu live không chứa và metadata chưa xác nhận.
