# Case Studies — các case thật user thường gặp

5 case end-to-end với answer Q1/Q2/Q3, slug + fieldType cụ thể, code final + test checklist. Dùng làm template clone khi user mô tả khớp case.

> 🚨 **RULE §0 (xem SKILL.md)**: TUYỆT ĐỐI KHÔNG dùng `return` trong code. Mọi guard dùng `if (positive_condition) { ... }` block.

---

## Case 1 — Set order_lines của Return Order từ Order

### Bối cảnh nghiệp vụ
- Object đang config: `return_order` (đơn trả hàng)
- Form Return Order có:
  - Field `order` (lookup → object `order`) — user chọn đơn gốc
  - Related list `return_order_lines` trong layout (trỏ tới object `order_line`) — dòng cần trả
- Yêu cầu: khi user chọn `order` → copy toàn bộ `order_lines` của order đó sang `return_order_lines`.

### Answer decision tree
- Q1: **3** (user đổi field `order`)
- Q2: n/a
- Q3: **1** (không overwrite — nếu bảng đã có dòng, có thể user đã sửa, không xoá)

### Slug & fieldType
- Object slug: `return_order`
- Field trigger: slug=`order`, type=`lookup`
- Related list slug **TRONG LAYOUT**: `return_order_lines` (NOT `order_line`)
- Object đích trong filterRecords: `order_line`
- Field bên `order_line` cần copy: `product` (lookup), `quantity` (number), `price` (currency)

### Code
```js
/**
 * ⚠️ SCRIPT SET DATA TỰ ĐỘNG — Return Order seed order_lines từ Order
 *
 * Chạy khi: user đổi field "order" (changedFields guard)
 * KHÔNG chạy khi: vào lại form đã lưu (changedFields rỗng khi load)
 * KHÔNG ghi đè: nếu return_order_lines đã có dòng (user có thể đã sửa)
 *
 * Nếu sửa script này, GIỮ NGUYÊN các điều kiện `if (...)` bao quanh logic.
 * TUYỆT ĐỐI KHÔNG thêm `return` — script này nằm chung 1 hàm với scripts khác.
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

            // setData nhận API record shape (xem §7B cheatsheet) — KHÁC SCRIPT shape của row.get().value.
            // records từ filterRecords đã ở API shape → pass thẳng, KHÔNG cần map thủ công.
            rl.setData(records);
        }
    } else {
        console.warn("return_order_lines đã có dòng — không seed lại");
    }
}
```

### Test checklist
1. Form **Tạo mới** Return Order → chọn order → check `return_order_lines` được seed ✅
2. Lưu Return Order → vào lại form edit → **KHÔNG** seed lại (giữ nguyên data đã save) ✅
3. Trong form edit, sửa quantity của 1 dòng → **KHÔNG** bị xoá khi mở lại ✅
4. Trong form edit, đổi field `order` sang đơn khác → tuỳ business:
   - Hiện tại Guard 2 (`existingRows.length === 0`) chặn → **không** seed lại
   - Nếu muốn seed lại → user phải xoá hết dòng cũ tay trước
5. **Quan trọng**: paste thêm 1 script khác bên dưới script này → script kia vẫn chạy bình thường (không bị `return` chặn) ✅

---

## Case 2 — Autofill địa chỉ khi chọn khách hàng

### Bối cảnh
- Object: `sale_order`
- Field `customer` (lookup → `customer`) → khi đổi → fill `delivery_address` (short_text) bằng `customer.defaultAddress`.

### Answer
- Q1: **3** (user đổi `customer`)
- Q3: **1** (không overwrite nếu address đã có)

### Slug
- Object: `sale_order`
- Trigger: `customer` (lookup)
- Target: `delivery_address` (short_text)

### Code
```js
/**
 * ⚠️ SCRIPT AUTOFILL
 * Chạy khi: user đổi field "customer"
 * KHÔNG ghi đè: nếu user đã nhập delivery_address
 * Lưu ý: KHÔNG dùng return — script chung hàm với scripts khác.
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

### Test
1. Form Tạo mới → chọn customer A có địa chỉ "HN" → field delivery_address = "HN" ✅
2. Đổi customer sang B → delivery_address vẫn = "HN" (đã có giá trị) ✅
3. Xoá tay delivery_address → đổi customer → fill địa chỉ của customer mới ✅
4. Vào lại form edit → KHÔNG đổi delivery_address ✅

---

## Case 3 — Autofill giá khi chọn sản phẩm trong dòng

### Bối cảnh
- Bảng `order_lines` (slug trong layout) có field `product` (lookup → `product`) và `price` (currency).
- Khi user chọn product → fill price bằng `product.defaultPrice`.

### Answer
- Q1: **4** (user gõ ô trong bảng)
- Q3: **1**

### Slug
- Related list slug trong layout: `order_lines`
- Trigger cell: `product` (lookup)
- Target cell: `price` (currency)

### Code
```js
const rl = screen.get("order_lines", "RELATED_LIST");
for (const c of changedRowCells || []) {
    if (c.relatedListSlug !== "order_lines") continue;  // continue OK trong loop
    if (c.fieldSlug !== "product") continue;
    const row = await rl.findRow((r) => r.recordId === c.recordId);
    if (row) {
        const priceCell = row.get("price");
        if (!priceCell.value) {                          // không overwrite
            // c.newValue cho lookup single = string ID (đã convert SCRIPT shape)
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

### Test
1. Thêm dòng mới → chọn product → price được fill ✅
2. Sửa price tay → đổi product → price KHÔNG đổi (đã có giá trị) ✅
3. Form edit → load row có sẵn → KHÔNG đổi price ✅

---

## Case 4 — Tính tổng order_lines vào field total

### Bối cảnh
- Bảng `order_lines` có `quantity` (number) + `price` (currency).
- Field `total` (currency) trên form cha = sum(quantity * price).

### Answer
- Không vào DANGER MODE (chỉ recompute, không phải set tuỳ điều kiện business). Nhưng vẫn cần loop guard.

### Slug
- Object: `order`
- RL slug trong layout: `order_lines`
- Field cha: `total` (currency)

### Code
```js
const rl = screen.get("order_lines", "RELATED_LIST");
const rows = await rl.rows();
let sum = 0;
for (const row of rows) {
    const q = Number(row.get("quantity").value ?? 0);
    const p = Number(row.get("price").value ?? 0);
    sum += q * p;
}
const totalItem = screen.get("total", "FORM_ITEM");
if (totalItem.value !== sum) {
    totalItem.value = sum;
}
```

### Test
1. Thêm dòng, nhập quantity=2, price=10000 → total = 20000 ✅
2. Sửa quantity = 3 → total = 30000 ✅
3. Xoá dòng → total update ✅
4. Form edit load → total = sum hiện tại của order_lines ✅

---

## Case 5 — Limit lookup theo điều kiện

### Bối cảnh
- Object: `task`
- Field `assignee` (lookup → `personnel`) — chỉ cho chọn nhân viên cùng phòng với người tạo.

### Answer
- Không DANGER MODE (filter options, không set value).

### Slug
- Object: `task`
- Field: `assignee` (lookup)
- Object filter: `personnel`

### Code
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

### Test
1. Form Tạo mới → click vào assignee → chỉ hiện nhân viên cùng phòng ✅
2. Mở form edit → assignee vẫn limit ✅
3. Chạy lại script → đọc kết quả qua `filterRecords`, so sánh trước khi SET và không giữ dữ liệu cũ trong `$ref`. Không giả định số request mạng cố định.

---

## Case 6 — Limit options của 1 cột single_choice trong bảng theo field cha

### Bối cảnh nghiệp vụ
- Object đang config: `cash_transaction` (Phiếu thu chi), có field `type` (single_choice: `receipt`=Phiếu thu / `payment`=Phiếu chi).
- Trong layout có related list "Phân bổ thanh toán" — object đích `cash_transaction_apply`, có cột `apply_type` (single_choice: vendor_invoice, purchase_order, advance_request, payment_request, advance_settlement, customer_invoice, customer_refund).
- Yêu cầu: tùy Loại phiếu → giới hạn options của ô `apply_type` mỗi dòng.
  - `receipt` → chỉ cho `customer_invoice`, `advance_settlement`.
  - `payment` → cho `vendor_invoice`, `purchase_order`, `advance_request`, `payment_request`, `advance_settlement`, `customer_refund`.

### Answer
- KHÔNG DANGER MODE (set `limitedOptions`, không set value → không trigger re-run, không cần Q1/Q2/Q3).

### Slug & fieldType (⚠️ điểm hay sai)
- Object cha: `cash_transaction`; field cha: `type` (single_choice) → đọc bằng `$record.type` (slug string).
- Related list slug **TRONG LAYOUT**: `cash_transaction_applies` (số nhiều!) — **KHÁC** object slug `cash_transaction_apply`. Soi đúng slug bằng `screen.relatedLists.map((r) => r.slug)`.
- Cell slug: `apply_type` (single_choice) → `limitedOptions` nhận **mảng slug option**.

### Code (đặt ở script layout CHA — cash_transaction)
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

### Test
1. Phiếu thu → mở dropdown `apply_type` mỗi dòng → chỉ 2 option ✅
2. Phiếu chi → đủ 6 option ✅
3. Đang chọn option không hợp lệ rồi đổi Loại → giá trị cũ tự bị xoá (hook single_choice tự reset khi value ngoài limitedOptions) ✅

### Gotcha
- `await rl.rows()` chỉ áp cho dòng có sẵn lúc script chạy. Dòng thêm mới sau cần re-trigger (đổi field cha / gõ 1 ô) thì mới áp.
- Sai slug related list (`cash_transaction_apply` thay vì `cash_transaction_applies`) → `screen.get` vẫn "found" (match qua sourceObjectSlug) nhưng override key sai → KHÔNG áp. Luôn dùng slug related list trong layout.
- Cell KHÔNG có `display` (không ẩn từng ô). Muốn lọc lookup cell thì `limitedOptions` nhận mảng record ID.
