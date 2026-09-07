# Safety Rules — 6 guard pattern bắt buộc

Khi DANGER MODE bật, áp dụng guard theo answer của decision tree.

> 🚨 **RULE §0 (xem SKILL.md)**: TUYỆT ĐỐI KHÔNG dùng `return` trong script. Mọi guard dưới đây dùng `if (positive_condition) { ... }` block bao quanh logic. `return` chặn các script khác chạy chung 1 hàm.

---

## Guard 1 — `if (formType !== "view") { ... }`

**Chặn**: script chạy lại khi user vào form đã lưu.

**Khi nào dùng**:
- Q1 = 2 (chỉ form Tạo mới)
- Q1 = 1 + Q2 = 1 (mở mọi lần nhưng không re-seed)

```js
// Chỉ chạy ở mode Tạo mới — không re-seed khi user mở form edit/view
if (formType !== "view") {
    // ... toàn bộ logic seed ở đây
}
```

`formType` là biến built-in: `"view"` nếu `$record.id` có, `"create"` nếu chưa có id.

Tương đương `if (!$record.id) { ... }` (cũ) — khuyến nghị dùng `formType` vì rõ nghĩa hơn cho non-coder.

**Cảnh báo**: nếu user **đổi** field sau khi đã save → vẫn KHÔNG chạy (vì `formType === "view"`). Trường hợp này phải dùng Guard 4 (changedFields) thay vì Guard 1.

---

## Guard 2 — `if (existingRows.length === 0) { ... }`

**Chặn**: ghi đè bảng đã có dòng.

**Khi nào dùng**: Q3 = 1 (không overwrite).

```js
const rl = screen.get("X", "RELATED_LIST");
const existingRows = await rl.rows();
if (existingRows.length === 0) {
    // bảng còn rỗng → mới seed
    rl.setData([...]);
} else {
    console.warn("Bảng X đã có dòng — không seed lại");
}
```

**Cảnh báo**: nếu user xoá hết dòng tay → script seed lại. Đa số case OK, nhưng nếu business cần "1 lần duy nhất" → combo thêm `$ref.seeded`.

---

## Guard 3 — `if (!targetField.value) { ... }` (field rỗng mới fill)

**Chặn**: ghi đè field đã có giá trị.

**Khi nào dùng**: set 1 field cụ thể, Q3 = 1.

```js
const addrItem = screen.get("address", "FORM_ITEM");
if (!addrItem.value) {
    // user chưa nhập → mới fill
    const newAddr = $record.customer?.defaultAddress ?? "";
    if (addrItem.value !== newAddr) {
        addrItem.value = newAddr;
    }
}
```

---

## Guard 4 — `if (changedFields["X"]) { ... }`

**Chặn**: chỉ chạy khi user VỪA đổi field X (KHÔNG chạy khi mount/load).

**Khi nào dùng**: Q1 = 3 (user đổi field X).

```js
// Chỉ chạy khi user vừa đổi field "order"
if (changedFields["order"]) {
    // ... toàn bộ logic phản ứng theo order
}
```

**Quan trọng**: đây là guard chính chặn "set order_lines từ order khi vào lại form edit". Khi user mở form edit → `changedFields = {}` (không có field nào vừa đổi) → if-block không chạy.

---

## Guard 5 — `filter changedRowCells theo relatedListSlug + fieldSlug`

**Chặn**: chỉ react khi user gõ ô cụ thể trong bảng cụ thể.

**Khi nào dùng**: Q1 = 4.

```js
for (const c of changedRowCells || []) {
    if (c.relatedListSlug === "order_lines" && c.fieldSlug === "product") {
        // ... logic chỉ cho ô "product" trong bảng "order_lines"
    }
}
```

**Ngoại lệ về `continue`**: Vì `continue` chỉ skip 1 iteration của loop (không thoát script), nó **OK** dùng nếu loop body có nhiều bước:

```js
for (const c of changedRowCells || []) {
    if (c.relatedListSlug !== "order_lines") continue;  // OK — chỉ skip iteration
    if (c.fieldSlug !== "product") continue;
    const row = await rl.findRow((r) => r.recordId === c.recordId);
    if (row) {
        // ... nhiều bước phía sau
    }
}
```

**KHÔNG được** loop không filter → react cả cell của bảng khác → wipe nhầm data.

---

## Guard 6 — `if (item.value !== newValue) { item.value = newValue; }`

**Chặn**: vòng lặp vô tận (RULE §1).

**Khi nào dùng**: **MỌI** set `.value` — field cha (FORM_ITEM) HOẶC cell trong related list (`row.get(...)`).

### Vì sao bắt buộc

Runtime tự re-trigger script khi:
- Bất kỳ field nào trên form đổi value (`changedFields[slug]` populate)
- Bất kỳ cell nào trong related list đổi value (`changedRowCells` populate)

→ SET `.value` mà không so sánh = chính script đó tự trigger lại chính nó → infinite loop → browser freeze.

### Cho field cha

```js
// SAI — trigger re-run vô tận
screen.get("total", "FORM_ITEM").value = sum;

// ĐÚNG
const totalItem = screen.get("total", "FORM_ITEM");
if (totalItem.value !== sum) {
    totalItem.value = sum;
}
```

### Cho cell trong related list

Runtime có safety net cho cell (`markParentScriptStart/End` + 200ms debounce) nhưng **KHÔNG đủ để dựa** — phải tự guard:

```js
// SAI — dù có safety net, vẫn risk khi script chạy lâu hoặc nhiều cell cùng update
priceCell.value = computePrice(row);

// ĐÚNG
const newPrice = computePrice(row);
if (priceCell.value !== newPrice) {
    priceCell.value = newPrice;
}
```

### Set null cũng phải guard

```js
// SAI — re-set null mỗi lần script chạy
applyTypeItem.value = null;

// ĐÚNG
if (applyTypeItem.value) {
    applyTypeItem.value = null;
}
```

### Các API KHÔNG cần Guard 6

| API | Vì sao không cần |
|---|---|
| `field.limitedOptions =` | UI config, không trigger re-run |
| `field.display =` / `readOnly =` / `required =` | Property UI, không trigger re-run |
| `cell.displayHtml =` | Cosmetic only |
| `rl.readOnly =` / `row.readOnly =` / `col.readOnly =` | Property UI quy về cell state, không trigger re-run |
| `row.required =` / `col.required =` | Property UI quy về cell state, không trigger re-run |
| `col.value =` | Ghi hàng loạt vào toàn bộ cell hiện có; runtime chặn thay đổi cell do script form cha tự tạo. Không cần guard chống lặp, nhưng bắt buộc xác nhận nghiệp vụ muốn ghi đè toàn cột. |

(Nhưng nên so sánh `if (field.display !== shouldShow) { ... }` để tránh re-render React thừa, không liên quan loop script.)

---

## Guard 7 — Related list column/row/cell override theo thứ tự chạy

**Chặn**: hiểu sai ưu tiên `readOnly`/`required` giữa bảng, cột, hàng, cell.

**Khi nào dùng**: mọi script có `rl.readOnly`, `rl.getCol(...)`, `rl.getRow(...)`, `row.readOnly`, `col.readOnly`, `row.required`, `col.required`.

### Vì sao bắt buộc

Runtime cuối cùng lưu trạng thái `readOnly`/`required` theo từng cell. Vì vậy **lệnh nào chạy sau thì thắng cho cell bị ảnh hưởng**, không ưu tiên theo API.

```js
const rl = screen.get("order_lines", "RELATED_LIST");
rl.readOnly = true;

const row = await rl.getRow(1);
if (row) {
    row.readOnly = false;  // dòng index 1 mở lại vì chạy sau
}
```

### Null-check bắt buộc

```js
const productCol = await rl.getCol("product");
if (productCol) {
    productCol.required = true;
}

const row = await rl.getRow(1);
if (row) {
    row.get("product").readOnly = false;
}
```

### Set value theo cột là ghi đè toàn cột, không áp Guard 6

`col.value` không đại diện cho các giá trị hiện tại của cột vì mỗi cell có thể khác nhau. Không dùng `if (col.value !== newValue)` để guard. Phép gán `col.value = ...` ghi đè cùng một giá trị cho toàn bộ cell hiện có; runtime đã chặn thay đổi cell do script form cha tự tạo nên không cần Guard 6 chống lặp.

Chỉ dùng khi user xác nhận nghiệp vụ muốn ghi đè toàn cột:

```js
const discountCol = await rl.getCol("discount_percent");
if (discountCol) {
    // Nghiệp vụ đã xác nhận: ghi đè mọi ô hiện có trong cột về 0.
    discountCol.value = 0;
}
```

Nếu cần giữ giá trị khác nhau hoặc chỉ sửa cell phù hợp điều kiện, không dùng `col.value`; xử lý từng cell:

```js
const rows = await rl.rows();
for (const row of rows) {
    const discountCell = row.get("discount_percent");
    if (discountCell && discountCell.value !== 0) {
        discountCell.value = 0;
    }
}
```

> Không dùng `row.value = ...`. Row không có value chung vì mỗi cell trong row có thể khác fieldType.

---

## Combo theo Q1/Q2/Q3

> ⚠️ Tất cả combo dưới đây **bao toàn bộ logic trong if-block**, KHÔNG dùng `return`.

### Combo A: "Khi user mở form, lần đầu seed bảng" + không re-seed + không overwrite (an toàn nhất)
Q1=1, Q2=1, Q3=1
```js
if (formType !== "view") {                        // Guard 1
    const rl = screen.get("X", "RELATED_LIST");
    const rows = await rl.rows();
    if (rows.length === 0) {                      // Guard 2
        rl.setData([...]);
    }
}
```

### Combo B: "Khi user mới tạo bản ghi" + không overwrite
Q1=2, Q3=1
```js
if (formType !== "view") {                        // Guard 1 (chặn view mode)
    const rl = screen.get("X", "RELATED_LIST");
    const rows = await rl.rows();
    if (rows.length === 0) {                      // Guard 2
        rl.setData([...]);
    }
}
```

### Combo C: "Khi user đổi field X → fill bảng" + không overwrite (case order/return-order)
Q1=3 (field="order"), Q3=1
```js
if (changedFields["order"]) {                     // Guard 4
    const rl = screen.get("order_lines", "RELATED_LIST");
    const rows = await rl.rows();
    if (rows.length === 0) {                      // Guard 2
        const orderId = $record.order;
        if (orderId) {
            const { records } = await filterRecords("order_line", {
                filterItems: [{ field: "order", op: "=", params: [orderId] }],
                limit: 500,
            });
            rl.setData(records);
        }
    }
}
```

### Combo D: "Khi user đổi field X → autofill field Y" + không overwrite
Q1=3 (field="customer"), Q3=1 (Y="address")
```js
if (changedFields["customer"]) {                  // Guard 4
    const addr = screen.get("address", "FORM_ITEM");
    if (!addr.value) {                            // Guard 3
        const newAddr = $record.customer?.defaultAddress ?? "";
        if (addr.value !== newAddr) {             // Guard 6
            addr.value = newAddr;
        }
    }
}
```

### Combo E: "Khi user gõ ô trong bảng → autofill ô khác cùng dòng"
Q1=4
```js
const rl = screen.get("order_lines", "RELATED_LIST");
for (const c of changedRowCells || []) {
    if (c.relatedListSlug !== "order_lines") continue;   // Guard 5 — continue OK trong loop
    if (c.fieldSlug !== "product") continue;             // Guard 5
    const row = await rl.findRow((r) => r.recordId === c.recordId);
    if (row) {
        const priceCell = row.get("price");
        const newPrice = (c.newValue && c.newValue.defaultPrice) || 0;
        if (priceCell.value !== newPrice) {              // Guard 6
            priceCell.value = newPrice;
        }
    }
}
```

### Combo F: Aggregate (sum quantity → set total)
Q1=4 (user đổi quantity trong bảng), action: set field cha
```js
const rl = screen.get("order_lines", "RELATED_LIST");
const rows = await rl.rows();
let sum = 0;
for (const row of rows) {
    sum += Number(row.get("quantity").value ?? 0);
}
const totalItem = screen.get("total", "FORM_ITEM");
if (totalItem.value !== sum) {                   // Guard 6
    totalItem.value = sum;
}
```
*Không cần Guard 4 vì script tự re-run khi `changedRowCells` populate.*

---

## Banner ⚠️ cho overwrite mode

Khi Q3 = 3 (luôn overwrite), bắt buộc header:

```js
/**
 * ⚠️⚠️⚠️ CẢNH BÁO — SCRIPT NÀY LUÔN OVERWRITE DATA USER NHẬP
 *
 * Mỗi lần script chạy sẽ ghi đè giá trị user đã sửa.
 * Chỉ giữ script này nếu business yêu cầu reset.
 * Nếu user phàn nàn "data tự xoá" → có thể do script này.
 *
 * Lưu ý: KHÔNG dùng `return` — script nằm chung hàm với scripts khác.
 */
```
