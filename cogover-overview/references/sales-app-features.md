# Sales App Feature List

Cột **Object liên quan** ghi slug chuẩn của Object lưu trữ hoặc cung cấp dữ liệu cho tính năng.

| Nhóm menu | Tính năng | Mô tả ngắn | Object liên quan |
|---|---|---|---|
| Khách hàng | Khách hàng và tổ chức | Quản lý hồ sơ doanh nghiệp, tổ chức và khách hàng có giao dịch với doanh nghiệp. | `account` |
| Khách hàng | Người liên hệ | Quản lý thông tin người liên hệ thuộc khách hàng hoặc tổ chức. | `contact`, `account` |
| Khách hàng | Chuyển người phụ trách liên hệ | Chuyển người phụ trách liên hệ để phân công lại trách nhiệm chăm sóc khách hàng. | `contact`, `personnel` |
| Bán hàng | Khách hàng tiềm năng | Quản lý khách hàng tiềm năng từ khi tiếp nhận đến khi đủ điều kiện chuyển đổi. | `lead` |
| Bán hàng | Cơ hội bán hàng | Quản lý cơ hội bán hàng, giá trị dự kiến, giai đoạn và khả năng thành công. | `opportunity`, `opportunity_product_line`, `opportunity_contact_role`, `opportunity_competitor`, `opportunity_partner`, `account`, `contact`, `lead`, `product` |
| Bán hàng | Đối thủ cạnh tranh | Quản lý thông tin đối thủ cạnh tranh phục vụ phân tích và xây dựng chiến lược bán hàng. | `account`, `opportunity_competitor`, `opportunity` |
| Bán hàng | Đối tác | Quản lý đối tác tham gia giới thiệu, phân phối hoặc hỗ trợ hoạt động bán hàng. | `account`, `opportunity_partner`, `opportunity` |
| Tài liệu bán hàng | Báo giá | Tạo và quản lý báo giá gửi cho khách hàng trong quá trình tư vấn và thương lượng. | `quote`, `quote_line_item`, `account`, `contact`, `opportunity`, `product`, `price_book`, `unit` |
| Tài liệu bán hàng | Hợp đồng | Quản lý hợp đồng bán hàng, thời hạn và trạng thái thực hiện. | `contract`, `contract_product_line`, `account`, `contact`, `opportunity`, `product`, `price_book`, `unit` |
| Tài liệu bán hàng | Sản phẩm | Quản lý danh mục sản phẩm và dịch vụ được sử dụng trong hoạt động bán hàng. | `product`, `unit_group`, `unit`, `price_book`, `price_book_entry` |
| Tài liệu bán hàng | Bảng giá | Quản lý các bảng giá áp dụng cho từng nhóm khách hàng, kênh bán hoặc giai đoạn kinh doanh. | `price_book`, `price_book_entry`, `product`, `unit` |
| Tài liệu bán hàng | Đơn bán hàng | Quản lý đơn bán hàng từ khi tạo, xác nhận đến khi hoàn tất hoặc huỷ. | `order`, `order_product_line`, `order_delivery`, `order_delivery_line`, `account`, `contact`, `quote`, `contract`, `opportunity`, `product`, `price_book`, `price_book_entry`, `unit` |
| Dịch vụ | Yêu cầu hỗ trợ | Tiếp nhận và theo dõi yêu cầu hỗ trợ, vấn đề hoặc phản hồi của khách hàng. | `ticket`, `account`, `contact`, `product`, `department`, `personnel` |
| Tiếp thị | Chiến dịch tiếp thị | Lập và quản lý chiến dịch marketing nhằm tiếp cận khách hàng tiềm năng và hỗ trợ bán hàng. | `campaign`, `campaign_member`, `lead`, `contact` |
| Thiết lập | Nhóm đơn vị tính | Quản lý các nhóm đơn vị tính dùng cho sản phẩm. | `unit_group`, `unit` |
| Thiết lập | Đơn vị tính | Quản lý đơn vị tính và cách sử dụng đơn vị cho sản phẩm. | `unit`, `unit_group`, `unit_conversion`, `product` |
