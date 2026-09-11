# Safety Rules: guard cho DANGER MODE

Áp dụng khi SKILL.md Bước 4 vào DANGER MODE; chọn guard theo answer Q1/Q2/Q3 (bảng Bước 5). Mọi guard là `if (điều_kiện_đúng) { ... }` bao quanh logic, không `return` (RULE §0).

## Guard 1: `if (formType !== "view") { ... }`

Chặn script chạy lại khi user vào form đã lưu. Dùng khi Q1 = 2, hoặc Q1 = 1 + Q2 = 1.

```js
// Chỉ chạy ở mode Tạo mới — không re-seed khi user mở form edit/view
if (formType !== "view") {
    // ... toàn bộ logic seed
}
```

`formType` là biến built-in: `"view"` khi `$record.id` có, `"create"` khi chưa có id. Tương đương `if (!$record.id) { ... }` (cách cũ); ưu tiên `formType` vì rõ nghĩa hơn với non-coder.

Cảnh báo: user đổi field sau khi đã lưu → vẫn không chạy (`formType === "view"`). Trường hợp này dùng Guard 4 thay cho Guard 1.

## Guard 2: `if (existingRows.length === 0) { ... }`

Chặn ghi đè bảng đã có dòng. Dùng khi Q3 = 1.

```js
const rl = screen.get("X", "RELATED_LIST");
const existingRows = await rl.rows();
if (existingRows.length === 0) {
    // bảng còn rỗng → mới seed
    rl.setData([...]);
}
```

Cảnh báo: user xoá hết dòng tay → script seed lại. Đa số case chấp nhận được; business cần "một lần duy nhất" → thêm cờ `$ref.seeded`.

## Guard 3: `if (!targetField.value) { ... }`

Chỉ fill khi field còn rỗng. Dùng khi set một field cụ thể, Q3 = 1. Bên trong vẫn so sánh trước khi set (Guard 6). Giá trị mới của lookup phải lấy qua `filterRecords` vì `$record.<lookup>` chỉ là ID (mẫu đầy đủ: [Case 2](case-studies.md#case-2-autofill-địa-chỉ-khi-chọn-khách-hàng)).

```js
const addrItem = screen.get("address", "FORM_ITEM");
if (!addrItem.value) {
    // user chưa nhập → mới fill
    if (addrItem.value !== newAddr) {
        addrItem.value = newAddr;
    }
}
```

## Guard 4: `if (changedFields["X"]) { ... }`

Chỉ chạy khi user VỪA đổi field X; không chạy khi mount/load. Dùng khi Q1 = 3.

```js
// Chỉ chạy khi user vừa đổi field "order"
if (changedFields["order"]) {
    // ... logic phản ứng theo order
}
```

Mở form edit → `changedFields = {}` (không field nào vừa đổi) → block không chạy. Đây là guard chính chặn "set order_lines từ order khi vào lại form edit".

## Guard 5: lọc `changedRowCells` theo `relatedListSlug` + `fieldSlug`

Chỉ react khi user gõ đúng ô của đúng bảng. Dùng khi Q1 = 4. Không loop không filter: sẽ react cả cell của bảng khác và wipe nhầm data.

```js
for (const c of changedRowCells || []) {
    if (c.relatedListSlug === "order_lines" && c.fieldSlug === "product") {
        // ... logic chỉ cho ô "product" trong bảng "order_lines"
    }
}
```

`continue` được phép khi loop body nhiều bước (chỉ skip iteration, không thoát script):

```js
for (const c of changedRowCells || []) {
    if (c.relatedListSlug !== "order_lines") continue;
    if (c.fieldSlug !== "product") continue;
    const row = await rl.findRow((r) => r.recordId === c.recordId);
    if (row) {
        // ... nhiều bước phía sau
    }
}
```

## Guard 6: so sánh trước khi set value

Quy tắc, ví dụ và bảng API cần guard: SKILL.md RULE §1. Bổ sung:

- Cell trong related list: runtime có safety net (debounce 200ms cho kênh cell value) nhưng không đủ để dựa; script chạy lâu hoặc nhiều cell cùng update vẫn có rủi ro → luôn tự so sánh `if (priceCell.value !== newPrice) { priceCell.value = newPrice; }`.
- `rl.readOnly`, `row.readOnly`, `col.readOnly`, `row.required`, `col.required` là property UI quy về cell state, không trigger re-run. `col.value =` là ghi hàng loạt: không cần guard chống lặp nhưng bắt buộc có xác nhận nghiệp vụ (Guard 7).
- `display`/`readOnly`/`required` nên so sánh kiểu `if (item.display !== shouldShow) { ... }` để tránh re-render React thừa (không liên quan loop script).

## Guard 7: related list column/row/cell theo thứ tự chạy

Quy tắc: SKILL.md RULE §1.5 (lệnh sau thắng; `await` + null-check `getCol`/`getRow`; không `row.value`; ngữ nghĩa `col.value`). Áp cho mọi script có `rl.readOnly`, `rl.getCol(...)`, `rl.getRow(...)`, `row.readOnly`, `col.readOnly`, `row.required`, `col.required`.

```js
const rl = screen.get("order_lines", "RELATED_LIST");
const productCol = await rl.getCol("product");
if (productCol) {
    productCol.readOnly = true;
}
const row = await rl.getRow(1);
if (row) {
    row.get("product").readOnly = false;  // cell này mở lại vì chạy sau column override
}
```

Ghi đè toàn cột (user đã xác nhận nghiệp vụ):

```js
const discountCol = await rl.getCol("discount_percent");
if (discountCol) {
    // Nghiệp vụ đã xác nhận: ghi đè mọi ô hiện có trong cột về 0.
    discountCol.value = 0;
}
```

Cần giữ giá trị khác nhau giữa các dòng hoặc chỉ sửa cell thoả điều kiện → không dùng `col.value`, xử lý từng cell:

```js
const rows = await rl.rows();
for (const row of rows) {
    const discountCell = row.get("discount_percent");
    if (discountCell && discountCell.value !== 0) {
        discountCell.value = 0;
    }
}
```

## Combo theo Q1/Q2/Q3

Code mẫu nằm ở recipes/case-studies, không lặp lại ở đây.

| Combo | Q1 / Q2 / Q3 | Guard | Code mẫu |
|---|---|---|---|
| A | 1 / 1 / 1: mở form, seed bảng lần đầu, không re-seed, không overwrite (an toàn nhất) | Guard 1 bao Guard 2 quanh `rl.setData` | [R1](recipes.md#r1-seed-bảng-một-lần-khi-mở-form-mới) |
| B | 2 / – / 1: chỉ khi tạo mới, không overwrite | Guard 1 + Guard 2 | [R1](recipes.md#r1-seed-bảng-một-lần-khi-mở-form-mới) |
| C | 3 (`order`) / – / 1: đổi field → fill bảng | Guard 4 + Guard 2; `filterRecords("order_line", ...)` rồi `rl.setData(records)` | [Case 1](case-studies.md#case-1-set-order_lines-của-return-order-từ-order) |
| D | 3 (`customer`) / – / 1: đổi field → autofill field | Guard 4 + Guard 3 + Guard 6 | [Case 2](case-studies.md#case-2-autofill-địa-chỉ-khi-chọn-khách-hàng) |
| E | 4: gõ ô trong bảng → autofill ô cùng dòng | Guard 5 + `rl.findRow((r) => r.recordId === c.recordId)` + Guard 6 | [R2](recipes.md#r2-autofill-cell-khi-user-gõ-cell-khác-cùng-dòng), [Case 3](case-studies.md#case-3-autofill-giá-khi-chọn-sản-phẩm-trong-dòng) |
| F | Aggregate: user đổi ô trong bảng → set field cha | Guard 6 khi set total; không cần Guard 4 vì script tự re-run khi `changedRowCells` populate | [R6](recipes.md#r6-tổng-hợp-bảng-thành-field-cha), [Case 4](case-studies.md#case-4-tính-tổng-order_lines-vào-field-total) |

## Banner cho overwrite mode

Q3 = 3 (luôn overwrite) → header bắt buộc:

```js
/**
 * ⚠️⚠️⚠️ CẢNH BÁO — SCRIPT NÀY LUÔN OVERWRITE DATA USER NHẬP
 *
 * Mỗi lần script chạy sẽ ghi đè giá trị user đã sửa.
 * Chỉ giữ script này nếu business yêu cầu reset.
 * Nếu user phàn nàn "data tự xoá" → có thể do script này.
 *
 * KHÔNG dùng `return` — script nằm chung hàm với scripts khác.
 */
```
