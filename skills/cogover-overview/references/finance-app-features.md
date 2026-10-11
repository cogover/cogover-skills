# Danh sách tính năng app Finance

Phiên bản app: 1.6.9 (17/08/2026). Cột **Object liên quan** ghi slug chuẩn của Object lưu trữ hoặc cung cấp dữ liệu cho tính năng.

## Bán hàng, hóa đơn khách hàng và trả hàng

| Tính năng | Mô tả ngắn | Object liên quan |
|---|---|---|
| Tạo hóa đơn từ đơn bán hàng | Tự động điền thông tin hóa đơn, sao chép các dòng hàng còn được phép xuất hóa đơn theo chính sách của sản phẩm và chuyển hóa đơn sang trạng thái Nháp. | `customer_invoice`, `customer_invoice_item`, `order`, `order_product_line`, `product`, `account`, `contract` |
| Tạo hóa đơn từ đơn trả hàng | Khi đơn trả hàng đã có hiệu lực, tự động điền hóa đơn và tạo các dòng âm theo số lượng trả chưa được xuất hóa đơn điều chỉnh. | `customer_invoice`, `customer_invoice_item`, `return_order`, `return_order_item`, `order`, `account` |
| Tạo hóa đơn điều chỉnh hoặc thay thế | Sao chép thông tin chung và các dòng từ hóa đơn gốc sang hóa đơn Điều chỉnh hoặc Thay thế, tránh tạo trùng dòng. | `customer_invoice`, `customer_invoice_item` |
| Duyệt hóa đơn và ghi nhận phải thu | Khi hóa đơn được duyệt, cập nhật số đã thu/còn lại, tạo công nợ phải thu nếu chưa có, tính bù trừ và áp dụng các khoản thu hoặc đặt cọc hiện hữu. | `customer_invoice`, `accounts_receivable`, `cash_transaction`, `cash_transaction_apply`, `customer_deposit`, `customer_deposit_apply` |
| Xử lý hóa đơn thay thế đã duyệt | Đánh dấu hóa đơn gốc là đã thay thế, hủy công nợ cũ, chuyển các phân bổ phiếu thu sang hóa đơn mới và dựng lại trạng thái thanh toán/công nợ. | `customer_invoice`, `accounts_receivable`, `cash_transaction`, `cash_transaction_apply`, `customer_deposit_apply` |
| Đồng bộ hóa đơn với đơn bán hàng | Tính lại số lượng đã xuất hóa đơn trên từng dòng, trạng thái xuất hóa đơn và trạng thái thanh toán của đơn hàng khi hóa đơn hoặc dòng hóa đơn thay đổi. | `customer_invoice`, `customer_invoice_item`, `order`, `order_product_line`, `product` |
| Xử lý đơn trả hàng trên hóa đơn | Cộng dồn số lượng trả vào dòng đơn hàng; với hóa đơn nháp thì tạo lại phần còn hợp lệ và hủy hóa đơn cũ, với hóa đơn đã ghi nhận thì tạo hóa đơn điều chỉnh. | `return_order`, `return_order_item`, `order`, `order_product_line`, `customer_invoice`, `customer_invoice_item` |
| Đồng bộ trạng thái đơn trả hàng | Tính số lượng đã lập hóa đơn điều chỉnh, trạng thái cần/đủ/vượt hóa đơn và trạng thái hoàn tiền của đơn trả hàng. | `return_order`, `return_order_item`, `customer_invoice`, `customer_invoice_item` |

## Mua hàng, hóa đơn nhà cung cấp và đề nghị thanh toán

| Tính năng | Mô tả ngắn | Object liên quan |
|---|---|---|
| Tạo đơn mua từ đề nghị mua | Tự động sao chép thông tin chung và các dòng chưa được sao chép từ đề nghị mua sang đơn mua, sau đó chuyển đơn mua sang trạng thái Nháp. | `purchase_request`, `purchase_request_item`, `purchase_order`, `purchase_order_item` |
| Tạo hóa đơn nhà cung cấp từ đơn mua | Tự động sao chép nhà cung cấp, phòng ban, tiền thuế/phí/chiết khấu và các dòng hàng từ đơn mua sang hóa đơn nhà cung cấp. | `purchase_order`, `purchase_order_item`, `vendor_invoice`, `vendor_invoice_item` |
| Hoàn thiện đề nghị thanh toán theo nguồn | Khi tạo đề nghị thanh toán từ hóa đơn nhà cung cấp, công nợ phải trả hoặc đơn mua, tự điền loại, số tiền, tiền tệ, nhà cung cấp và nội dung còn thiếu. | `payment_request`, `vendor_invoice`, `accounts_payable`, `purchase_order` |
| Duyệt hóa đơn nhà cung cấp và ghi nhận phải trả | Khi hóa đơn được duyệt, tạo công nợ phải trả nếu chưa có và đồng bộ số đã trả, số còn lại cùng trạng thái thanh toán. | `vendor_invoice`, `accounts_payable`, `payment_request`, `cash_transaction`, `cash_transaction_apply` |
| Cấn trừ đặt cọc nhà cung cấp | Phân bổ các khoản đặt cọc đã chi theo hợp đồng mua vào hóa đơn nhà cung cấp mới, hỗ trợ tách một dòng phân bổ khi chỉ dùng một phần. | `purchase_contract`, `payment_request`, `cash_transaction`, `cash_transaction_apply`, `vendor_invoice` |
| Bù trừ công nợ phải trả | Bù trừ các khoản phải trả dương/âm thuộc cùng nhóm giao dịch; có xét hóa đơn phát sinh từ trả hàng mua và cập nhật trạng thái hóa đơn liên quan. | `accounts_payable`, `vendor_invoice`, `purchase_order_return` |
| Đồng bộ thanh toán và trạng thái đơn mua | Tính tổng đã thanh toán từ đề nghị thanh toán, phiếu chi và công nợ; kết hợp tình trạng nhận hàng để cập nhật trạng thái đơn mua. | `purchase_order`, `purchase_order_item`, `vendor_invoice`, `payment_request`, `cash_transaction`, `cash_transaction_apply`, `accounts_payable` |
| Theo dõi số đã thanh toán của đề nghị mua | Cộng dồn thanh toán qua các đơn mua, đề nghị thanh toán, hóa đơn nhà cung cấp và công nợ liên quan. | `purchase_request`, `purchase_order`, `payment_request`, `vendor_invoice`, `cash_transaction`, `cash_transaction_apply`, `accounts_payable` |
| Theo dõi giá trị hợp đồng mua | Tính số đã trả và giá trị còn lại của hợp đồng mua từ đơn mua, hóa đơn nhà cung cấp, đề nghị thanh toán và phiếu chi. | `purchase_contract`, `purchase_order`, `vendor_invoice`, `payment_request`, `cash_transaction`, `cash_transaction_apply`, `accounts_payable` |

## Phiếu thu/chi và lịch thanh toán

| Tính năng | Mô tả ngắn | Object liên quan |
|---|---|---|
| Tạo phiếu thu/chi theo chứng từ nguồn | Tự động điền loại giao dịch, đối tượng, số tiền, tiền tệ và tạo dòng phân bổ khi phiếu được tạo từ đề nghị thanh toán, kỳ thanh toán, tạm ứng/quyết toán, hóa đơn hoặc công nợ. | `cash_transaction`, `cash_transaction_apply`, `payment_request`, `payment_installment_schedule`, `advance_request`, `advance_settlement`, `customer_invoice`, `vendor_invoice`, `accounts_receivable`, `accounts_payable` |
| Hoàn thành phiếu thu/chi | Kiểm tra quyền, trạng thái, tiền tệ, hạn mức phân bổ và tính hợp lệ của chứng từ nguồn; cập nhật số dư quỹ, số đã phân bổ, số chưa phân bổ và các chứng từ liên quan. Yêu cầu gửi lặp không làm ghi nhận giao dịch hai lần. | `cash_transaction`, `cash_transaction_apply`, `fund_account`, `customer_invoice`, `vendor_invoice`, `accounts_receivable`, `accounts_payable`, `payment_request`, `advance_request`, `advance_settlement`, `payment_installment_schedule`, `customer_deposit` |
| Tự động hoàn thành phiếu thu/chi | Nếu phiếu nháp bật chế độ tự động hoàn thành, hệ thống thực hiện cùng quy trình kiểm tra và cập nhật như khi người dùng hoàn thành phiếu. | `cash_transaction`, `cash_transaction_apply`, `fund_account`, `customer_invoice`, `vendor_invoice`, `accounts_receivable`, `accounts_payable`, `payment_request`, `advance_request`, `advance_settlement`, `payment_installment_schedule`, `customer_deposit` |
| Hủy phiếu thu/chi nháp | Chỉ cho phép người có quyền hủy phiếu đang ở trạng thái Nháp và ngăn việc hủy diễn ra đồng thời với hoàn thành phiếu. | `cash_transaction` |
| Phân bổ một phiếu cho nhiều chứng từ | Cho phép một phiếu thu/chi thanh toán nhiều hóa đơn, công nợ hoặc đề nghị thanh toán và tính lại trạng thái của từng chứng từ đích. | `cash_transaction`, `cash_transaction_apply`, `customer_invoice`, `vendor_invoice`, `accounts_receivable`, `accounts_payable`, `payment_request` |
| Thanh toán theo lịch nhiều kỳ | Chuyển dòng chỉ dẫn theo lịch thành các dòng phân bổ thực tế theo thứ tự kỳ, kiểm tra chiều thu/chi và tiền tệ, rồi cập nhật số đã trả/trạng thái từng kỳ. | `payment_installment_schedule`, `cash_transaction`, `cash_transaction_apply`, `accounts_receivable`, `accounts_payable`, `customer_invoice`, `vendor_invoice`, `order`, `purchase_order`, `contract`, `purchase_contract` |

## Đặt cọc khách hàng và công nợ

| Tính năng | Mô tả ngắn | Object liên quan |
|---|---|---|
| Ghi nhận đặt cọc khách hàng | Khi hoàn thành phiếu thu được đánh dấu là đặt cọc, tạo khoản đặt cọc và dòng liên kết với phiếu thu, sau đó có thể tự áp dụng vào công nợ mở. | `cash_transaction`, `cash_transaction_apply`, `customer_deposit`, `customer_deposit_apply`, `accounts_receivable` |
| Hoàn đặt cọc khách hàng | Kiểm tra số dư đặt cọc khả dụng, phân bổ khoản hoàn theo các khoản đặt cọc phù hợp và tạo liên kết với phiếu chi hoàn tiền. | `cash_transaction`, `cash_transaction_apply`, `customer_deposit`, `customer_deposit_apply`, `account`, `contact` |
| Tự động áp dụng đặt cọc | Tìm các khoản đặt cọc cùng khách hàng, tiền tệ và còn hiệu lực để tự phân bổ vào công nợ/hóa đơn; cập nhật số dư và trạng thái hai phía. | `customer_deposit`, `customer_deposit_apply`, `accounts_receivable`, `customer_invoice`, `account`, `contact` |
| Tổng hợp số dư đặt cọc theo khách hàng | Tính lại tổng tiền đặt cọc khả dụng theo khách hàng hoặc người liên hệ khi khoản đặt cọc/phân bổ thay đổi. | `customer_deposit`, `account`, `contact` |
| Bù trừ công nợ phải thu | Bù trừ công nợ dương/âm thuộc cùng nhóm hóa đơn điều chỉnh hoặc thay thế và đồng bộ số còn lại về hóa đơn. | `accounts_receivable`, `customer_invoice` |
| Tổng hợp công nợ theo đối tượng | Tính tổng phải thu, phải trả và số dư ròng theo khách hàng hoặc người liên hệ mỗi khi công nợ thay đổi. | `accounts_receivable`, `accounts_payable`, `account`, `contact` |

## Tạm ứng và quyết toán tạm ứng

| Tính năng | Mô tả ngắn | Object liên quan |
|---|---|---|
| Theo dõi thanh toán tạm ứng | Cộng dồn các phiếu chi hoàn tất đã phân bổ vào đề nghị tạm ứng và cập nhật số đã trả, số còn lại, trạng thái thanh toán. | `advance_request`, `cash_transaction`, `cash_transaction_apply` |
| Cảnh báo tạm ứng cũ chưa quyết toán | Kiểm tra theo người đề nghị để đánh dấu một đề nghị mới có tồn tại khoản tạm ứng cũ chưa được quyết toán hay không. | `advance_request` |
| Tính lại phiếu quyết toán | Tổng hợp các dòng quyết toán, số tạm ứng, số phải thu thêm/chi thêm và các khoản đã thanh toán để cập nhật phiếu quyết toán và đề nghị tạm ứng liên quan. | `advance_settlement`, `advance_settlement_line`, `advance_request`, `cash_transaction`, `cash_transaction_apply` |
| Đổi trạng thái quyết toán | Kiểm tra quyền và dữ liệu chi tiết, đặt hoặc giải phóng phần ngân sách giữ chỗ khi gửi duyệt, đồng thời chỉ hoàn tất quyết toán khi chênh lệch đã được xử lý hợp lệ. | `advance_settlement`, `advance_settlement_line`, `advance_request`, `budget_amount`, `budget_commitment`, `budget_control_object`, `budget_version`, `fiscal_period` |

## Kiểm soát ngân sách

| Tính năng | Mô tả ngắn | Object liên quan |
|---|---|---|
| Xác định ngân sách áp dụng | Ghép chứng từ với kỳ tài chính, phiên bản ngân sách và đối tượng kiểm soát theo ngày, phòng ban, danh mục chi phí và tiền tệ; hỗ trợ mức kiểm soát cứng/mềm. | `fiscal_period`, `budget_version`, `budget_control_object`, `budget_amount`, `department`, `expense_category` |
| Giữ chỗ và giải phóng ngân sách | Tạo/cập nhật/đóng cam kết ngân sách khi đề nghị mua, đơn mua, đề nghị thanh toán hoặc đề nghị tạm ứng thay đổi trạng thái, số tiền hay bị xóa. | `budget_amount`, `budget_commitment`, `purchase_request`, `purchase_request_item`, `purchase_order`, `purchase_order_item`, `payment_request`, `advance_request` |
| Chuyển ngân sách cam kết sang đã sử dụng | Khi thanh toán phát sinh, chuyển đúng phần cam kết thành đã sử dụng theo nguồn mua hàng, hóa đơn nhà cung cấp, đề nghị thanh toán, tạm ứng hoặc dòng quyết toán. | `budget_amount`, `budget_commitment`, `purchase_request`, `purchase_order`, `payment_request`, `vendor_invoice`, `advance_request`, `advance_settlement`, `advance_settlement_line` |
| Kiểm soát ngân sách chênh lệch quyết toán | Đánh giá từng dòng quyết toán, cảnh báo hoặc chặn nếu vượt ngân sách, giữ chỗ lúc gửi duyệt và chuyển sang đã sử dụng khi hoàn tất. | `advance_settlement`, `advance_settlement_line`, `budget_amount`, `budget_commitment`, `budget_control_object`, `budget_version`, `fiscal_period`, `department`, `expense_category` |

## Dự báo dòng tiền

| Tính năng | Mô tả ngắn | Object liên quan |
|---|---|---|
| Tạo dự báo dòng tiền | Tổng hợp số dư đầu kỳ, phải thu/phải trả, lịch thanh toán, đơn hàng, hóa đơn chưa duyệt, doanh thu/chi phí định kỳ, dòng thống kê và điều chỉnh để tạo dự báo cho một hoặc nhiều kỳ. | `cash_forecast_preference`, `department`, `fund_account`, `accounts_receivable`, `accounts_payable`, `payment_installment_schedule`, `order`, `purchase_order`, `customer_invoice`, `customer_invoice_item`, `vendor_invoice`, `recurring_revenue`, `recurring_expense`, `cash_flow_category`, `cash_flow_category_line`, `cash_flow_category_setting`, `cash_forecast_adjustment`, `revenue_category`, `expense_category`, `cash_transaction`, `cash_transaction_apply`, `payment_request` |
| Dòng dự báo thống kê và linh hoạt | Tính dòng tiền theo cấu hình danh mục, lịch lặp, xu hướng lịch sử, cây danh mục doanh thu/chi phí và các khoản điều chỉnh thủ công. | `cash_flow_category`, `cash_flow_category_line`, `cash_flow_category_setting`, `cash_forecast_adjustment`, `revenue_category`, `expense_category`, `recurring_revenue`, `recurring_expense`, `customer_invoice`, `customer_invoice_item`, `vendor_invoice`, `cash_transaction`, `cash_transaction_apply` |
| Quản lý dự báo nhiều kỳ | Lưu riêng từng lần lập dự báo và chỉ công bố kết quả mới sau khi toàn bộ các kỳ đã được tính thành công, tránh hiển thị dữ liệu chưa hoàn chỉnh. | `cash_forecast_preference`, `fund_account`, `accounts_receivable`, `accounts_payable`, `payment_installment_schedule`, `order`, `purchase_order`, `customer_invoice`, `vendor_invoice`, `recurring_revenue`, `recurring_expense`, `cash_flow_category`, `cash_forecast_adjustment` |
| Tự động làm mới dự báo | Định kỳ kiểm tra các không gian làm việc đã cấu hình, xác định công ty/phòng ban cần dự báo và cập nhật lại kết quả mà không xử lý trùng. | `cash_forecast_preference`, `department`, `fund_account`, `accounts_receivable`, `accounts_payable`, `payment_installment_schedule`, `order`, `purchase_order`, `customer_invoice`, `vendor_invoice`, `recurring_revenue`, `recurring_expense`, `cash_flow_category`, `cash_forecast_adjustment` |
| Xem dự báo và chi tiết nguồn | Hiển thị tổng hợp theo kỳ, từng dòng thu/chi và các chứng từ cấu thành mỗi số liệu dự báo. | `cash_forecast_preference`, `fund_account`, `accounts_receivable`, `accounts_payable`, `payment_installment_schedule`, `order`, `purchase_order`, `customer_invoice`, `vendor_invoice`, `recurring_revenue`, `recurring_expense`, `cash_flow_category`, `cash_forecast_adjustment` |
| Xuất dự báo và chi tiết | Xuất bảng dự báo hoặc danh sách chứng từ chi tiết ra Excel/CSV, lưu file an toàn và gửi đường dẫn tải khi hoàn tất. | `cash_forecast_preference`, `fund_account`, `accounts_receivable`, `accounts_payable`, `payment_installment_schedule`, `order`, `purchase_order`, `customer_invoice`, `vendor_invoice`, `recurring_revenue`, `recurring_expense`, `cash_flow_category`, `cash_forecast_adjustment` |

## Báo cáo, tích hợp và tiện ích nền tảng

| Tính năng | Mô tả ngắn | Object liên quan |
|---|---|---|
| Xuất sao kê công nợ khách hàng | Tạo file Excel cho từng khách hàng hoặc người liên hệ, gồm công nợ, hóa đơn, phiếu thu, đặt cọc/hoàn đặt cọc và chi tiết sản phẩm; lưu file an toàn và gửi đường dẫn tải khi hoàn tất. | `account`, `contact`, `accounts_receivable`, `customer_invoice`, `customer_invoice_item`, `product`, `cash_transaction`, `cash_transaction_apply`, `customer_deposit`, `customer_deposit_apply` |
| Thông báo hóa đơn được hoàn thiện tự động | Khi hệ thống tự điền hóa đơn và tạo dòng thành công, gửi thông báo tích hợp để các hệ thống liên quan nhận biết kết quả. | `customer_invoice`, `order`, `return_order` |
