# Ví dụ bố cục tham khảo

Cây bố cục minh hoạ logic sắp xếp theo quy tắc thiết kế trong [SKILL.md](../SKILL.md). Layout thật của Object Lead/Order trên hệ thống lấy qua API list của Object (`functionLayout: 1` cho tạo, `2` cho xem/sửa); ID thay đổi theo Workspace.

## Layout tạo Lead

1 Row, 1 Column, 2 Section:

```text
Row 0 (1 cột, maxWidth 1000px, căn giữa)
└── Column 0
    ├── Section "Lead Information" (border, hiện tên)
    │   ├── Group 1 cột: Title (trường tiêu đề duy nhất, chiếm toàn bộ chiều rộng)
    │   └── Group 2 cột: Họ, Tên, Trạng thái, Owner, Mức độ, Danh xưng, Chức danh, Nguồn, SĐT, Email, Mô tả, Địa chỉ
    │       (Họ và Tên cùng hàng vì cùng ngữ nghĩa và nội dung ngắn)
    └── Section "Additional Information" (border, hiện tên)
        └── Group 2 cột: Công ty, Doanh thu, Ngành, Số NV, Website, SĐT công ty, Không gọi điện
```

## Layout xem/sửa Lead

2 Row, Row chính 3 cột tỷ lệ 1:2:1:

```text
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

## Layout tạo Đơn hàng

1 Row, 1 Column, 1 Section, có related list editable (mẫu: `assets/sample_layout_create_order.json`):

```text
Row 0 (1 cột, maxWidth 100%, căn giữa vì có bảng related list)
└── Column 0
    └── Section (border)
        ├── Group 2 cột: Owner, Khách hàng, Trạng thái, Bảng giá
        ├── Group 2 cột: Báo giá, Hợp đồng, Địa chỉ thanh toán, Địa chỉ giao hàng
        └── Group 1 cột: Mô tả, Related List "Sản phẩm trong đơn hàng" (typeView: "list")
            └── tableSettings:
                showingColumns: [product, quantity, price_per_unit, unit, discount_by_unit, tax_by_unit, fee_by_unit, total_price, _action_column]
                editableColumns: [product, quantity, price_per_unit, unit, discount_by_unit, tax_by_unit, fee_by_unit]
                (total_price là trường tính toán → KHÔNG editable)
                (cột "order" (lookup về Order) bị loại khỏi showingColumns vì thừa)
```

## Layout xem/sửa Đơn hàng

1 Row, 2 Column tỷ lệ 1:3, có related list editable:

```text
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
            (_action_column KHÔNG cần trong showingColumns khi đã pinned)
            (Có thêm subtotal so với layout tạo)
```
