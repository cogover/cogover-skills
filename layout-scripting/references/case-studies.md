# Case Studies: case thật user thường gặp

Case end-to-end với answer Q1/Q2/Q3, slug + fieldType, code và test checklist. Clone khi mô tả của user khớp case; đổi slug theo Bước 3 của SKILL.md. Không `return` (RULE §0).

## Case 1: Set order_lines của Return Order từ Order

- Object đang config: `return_order`; field trigger `order` (lookup → object `order`).
- Related list trong layout: `return_order_lines` (trỏ object `order_line`; slug bảng ≠ slug object đích).
- Field bên `order_line` cần copy: `product` (lookup), `quantity` (number), `price` (currency).
- Yêu cầu: chọn `order` → copy toàn bộ order_lines của đơn đó sang `return_order_lines`.
- Answer: Q1 = 3 (đổi field `order`), Q3 = 1 (bảng đã có dòng thì không xoá, user có thể đã sửa).

```js
/**
 * ⚠️ SCRIPT SET DATA TỰ ĐỘNG — Return Order seed order_lines từ Order
 *
 * Chạy khi: user đổi field "order" (changedFields guard)
 * KHÔNG chạy khi: vào lại form đã lưu (changedFields rỗng khi load)
 * KHÔNG ghi đè: nếu return_order_lines đã có dòng (user có thể đã sửa)
 *
 * Nếu sửa script này, GIỮ NGUYÊN các điều kiện `if (...)` bao quanh logic.
 * KHÔNG thêm `return` — script này nằm chung 1 hàm với scripts khác.
 */
if (changedFields["order"]) {
    const rl = screen.get("return_order_lines", "RELATED_LIST");
    const existingRows = await rl.rows();
    if (existingRows.length === 0) {
        // $record.order là STRING (ID), không phải object — lookup_normal single
        const orderId = $record.order;
        if (orderId) {
            const { records } = await filterRecords("order_line", {
                filterItems: [{ field: "order", op: "=", params: [orderId] }],
                limit: 500,
            });
            // setData nhận API record shape (§7B), KHÁC SCRIPT shape của row.get().value.
            // records từ filterRecords đã ở API shape → pass thẳng, không map thủ công.
            rl.setData(records);
        }
    } else {
        logger.log("return_order_lines đã có dòng — không seed lại");
    }
}
```

Test:
1. Form Tạo mới → chọn order → `return_order_lines` được seed.
2. Lưu → mở lại form edit → không seed lại, giữ nguyên data đã lưu.
3. Form edit, sửa quantity của một dòng → không bị xoá khi mở lại.
4. Form edit, đổi `order` sang đơn khác khi bảng đã có dòng → Guard 2 chặn, không seed lại; muốn seed lại phải xoá hết dòng cũ tay trước.
5. Paste thêm một script khác bên dưới script này → script kia vẫn chạy bình thường (không bị `return` chặn).

## Case 2: Autofill địa chỉ khi chọn khách hàng

- Object `sale_order`; trigger `customer` (lookup → `customer`); target `delivery_address` (short_text) = `customer.defaultAddress`.
- Answer: Q1 = 3, Q3 = 1 (không ghi đè nếu đã có địa chỉ).

```js
/**
 * ⚠️ SCRIPT AUTOFILL
 * Chạy khi: user đổi field "customer"
 * KHÔNG ghi đè: nếu user đã nhập delivery_address
 * KHÔNG dùng return — script chung hàm với scripts khác.
 */
if (changedFields["customer"]) {
    const addrItem = screen.get("delivery_address", "FORM_ITEM");
    if (!addrItem.value) {
        // $record.customer là STRING (ID) — phải filterRecords để lấy defaultAddress
        const customerId = $record.customer;
        if (customerId) {
            const { records } = await filterRecords("customer", {
                filterItems: [{ field: "id", op: "=", params: [customerId] }],
                limit: 1,
            });
            const newAddr = records[0]?.defaultAddress ?? "";
            if (addrItem.value !== newAddr) {
                addrItem.value = newAddr;
            }
        }
    }
}
```

Test:
1. Tạo mới → chọn customer A có địa chỉ "HN" → `delivery_address` = "HN".
2. Đổi sang customer B → vẫn "HN" (đã có giá trị).
3. Xoá tay `delivery_address` → đổi customer → fill địa chỉ của customer mới.
4. Mở lại form edit → không đổi `delivery_address`.

## Case 3: Autofill giá khi chọn sản phẩm trong dòng

- Related list trong layout `order_lines`; trigger cell `product` (lookup → `product`); target cell `price` (currency) = `product.defaultPrice`.
- Answer: Q1 = 4, Q3 = 1.

```js
const rl = screen.get("order_lines", "RELATED_LIST");
for (const c of changedRowCells || []) {
    if (c.relatedListSlug !== "order_lines") continue;  // continue OK trong loop
    if (c.fieldSlug !== "product") continue;
    const row = await rl.findRow((r) => r.recordId === c.recordId);
    if (row) {
        const priceCell = row.get("price");
        if (!priceCell.value) {                          // không overwrite
            // c.newValue của lookup single = string ID (đã convert SCRIPT shape)
            const productId = c.newValue;
            if (productId) {
                // Lookup chỉ có ID — phải filterRecords để lấy defaultPrice
                const { records } = await filterRecords("product", {
                    filterItems: [{ field: "id", op: "=", params: [productId] }],
                    limit: 1,
                });
                const newPrice = Number(records[0]?.defaultPrice ?? 0);
                if (priceCell.value !== newPrice) {
                    priceCell.value = newPrice;
                }
            }
        }
    }
}
```

Test:
1. Thêm dòng mới → chọn product → price được fill.
2. Sửa price tay → đổi product → price không đổi (đã có giá trị).
3. Form edit load row có sẵn → không đổi price.

## Case 4: Tính tổng order_lines vào field total

- Object `order`; related list trong layout `order_lines` (`quantity` number, `price` currency); field cha `total` (currency) = sum(quantity × price).
- Answer: không DANGER MODE (chỉ recompute, không set theo điều kiện business) nhưng vẫn cần guard so sánh khi set `total`.
- Code: [recipe R6](recipes.md#r6-tổng-hợp-bảng-thành-field-cha) với slug trên.

Test:
1. Thêm dòng quantity = 2, price = 10000 → total = 20000.
2. Sửa quantity = 3 → total = 30000.
3. Xoá dòng → total cập nhật.
4. Form edit load → total = tổng hiện tại của order_lines.

## Case 5: Giới hạn lookup theo điều kiện

- Object `task`; field `assignee` (lookup → `personnel`) chỉ cho chọn nhân viên cùng phòng với người đang đăng nhập.
- Answer: không DANGER MODE (chỉ lọc option, không set value).

```js
// $currentPersonnel.department là STRING (ID) — lookup_normal single
const dept = $currentPersonnel?.department;
if (dept) {
    // Đọc dữ liệu khi cần; không giữ kết quả API dài hạn trong $ref.
    const { records } = await filterRecords("personnel", {
        filterItems: [{ field: "department", op: "=", params: [dept] }],
        limit: 200,
    });
    const ids = records.map((r) => r.id);
    const assigneeItem = screen.get("assignee", "FORM_ITEM");
    const current = assigneeItem.limitedOptions || [];
    const same = current.length === ids.length && current.every((v, i) => v === ids[i]);
    if (!same) {
        assigneeItem.limitedOptions = ids;
    }
}
```

Test:
1. Tạo mới → click assignee → chỉ hiện nhân viên cùng phòng.
2. Form edit → assignee vẫn bị giới hạn.
3. Script chạy lại → đọc qua `filterRecords`, so sánh trước khi set, không giữ dữ liệu cũ trong `$ref`; không giả định số request mạng cố định.

## Case 6: Giới hạn option cột single_choice trong bảng theo field cha

- Object đang config `cash_transaction` (Phiếu thu chi), field `type` (single_choice: `receipt` = Phiếu thu, `payment` = Phiếu chi), đọc bằng `$record.type` (slug string).
- Related list "Phân bổ thanh toán": slug trong layout `cash_transaction_applies` (số nhiều) ≠ object đích `cash_transaction_apply`. Soi slug đúng bằng `screen.relatedLists.map((r) => r.slug)`.
- Cell `apply_type` (single_choice; option: vendor_invoice, purchase_order, advance_request, payment_request, advance_settlement, customer_invoice, customer_refund) → `limitedOptions` nhận mảng slug option.
- Yêu cầu: `receipt` → chỉ `customer_invoice`, `advance_settlement`; `payment` → `vendor_invoice`, `purchase_order`, `advance_request`, `payment_request`, `advance_settlement`, `customer_refund`.
- Answer: không DANGER MODE (`limitedOptions` không set value, không trigger re-run, không cần Q1/Q2/Q3).
- Script đặt ở layout CHA (`cash_transaction`).

```js
/**
 * ⚠️ SCRIPT GIỚI HẠN OPTIONS — chỉ lọc danh sách chọn của ô apply_type, KHÔNG đổi giá trị.
 * Chạy ở layout cha (Phiếu thu chi). KHÔNG dùng return.
 */
const rl = screen.get("cash_transaction_applies", "RELATED_LIST"); // slug số nhiều trong layout

let allowed = null;
if ($record.type === "receipt") {
    allowed = ["customer_invoice", "advance_settlement"];
} else if ($record.type === "payment") {
    allowed = [
        "vendor_invoice",
        "purchase_order",
        "advance_request",
        "payment_request",
        "advance_settlement",
        "customer_refund",
    ];
}

if (rl && allowed) {
    const rows = await rl.rows();
    for (const row of rows) {
        row.get("apply_type").limitedOptions = allowed;
    }
}
```

Test:
1. Phiếu thu → dropdown `apply_type` mỗi dòng chỉ 2 option.
2. Phiếu chi → đủ 6 option.
3. Đang chọn option không hợp lệ rồi đổi Loại → giá trị cũ tự bị xoá (hook single_choice tự reset khi value ngoài `limitedOptions`).

Gotcha:
- `await rl.rows()` chỉ áp cho dòng có sẵn lúc script chạy; dòng thêm mới sau cần re-trigger (đổi field cha hoặc gõ một ô) mới được áp.
- Sai slug related list (`cash_transaction_apply` thay vì `cash_transaction_applies`) → `screen.get` vẫn "found" (match qua sourceObjectSlug) nhưng override key sai → không áp. Luôn dùng slug related list trong layout.
- Cell không có `display` (không ẩn từng ô). Muốn lọc lookup cell → `limitedOptions` nhận mảng record ID.
