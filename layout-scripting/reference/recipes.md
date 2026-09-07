# Recipes — 14 pattern code mẫu

Mỗi recipe có safety variant theo answer Q1/Q2/Q3. Skill chọn variant dựa vào decision tree.

> 🚨 **RULE §0 (xem SKILL.md)**: TUYỆT ĐỐI KHÔNG dùng `return` trong recipe. Mọi guard dùng `if (positive_condition) { ... }` block bao quanh logic. Ngoại lệ duy nhất: `continue` trong `for` loop.

---

## R1 — Seed bảng 1 lần khi mở form mới

**Khi nào**: user muốn pre-fill bảng với data mặc định.

**Variant 1A** (Q1=2 mới-tạo, Q3=1 không-overwrite — DEFAULT)
```js
/**
 * ⚠️ SCRIPT SET DATA TỰ ĐỘNG
 * Chạy khi: form Tạo mới (chưa có id)
 * KHÔNG chạy khi: vào lại form đã lưu
 * KHÔNG ghi đè: nếu bảng đã có dòng
 * Lưu ý: KHÔNG dùng return — script chạy chung hàm với scripts khác.
 */
if (formType !== "view") {
    const rl = screen.get("<RL_SLUG_IN_LAYOUT>", "RELATED_LIST");
    const rows = await rl.rows();
    if (rows.length === 0) {
        rl.setData([
            { /* field slug + value */ },
            { /* ... */ },
        ]);
    }
}
```

**Variant 1B** (Q1=2, Q3=3 luôn-overwrite)
```js
/**
 * ⚠️⚠️⚠️ CẢNH BÁO: SCRIPT NÀY LUÔN GHI ĐÈ DATA NGƯỜI DÙNG NHẬP
 */
if (formType !== "view") {
    const rl = screen.get("<RL_SLUG>", "RELATED_LIST");
    rl.setData([...]);
}
```

---

## R2 — Autofill cell khi user gõ cell khác (cùng dòng)

**Khi nào**: user gõ tên sản phẩm → tự fill giá.

**Variant 2A** (Q1=4, Q3=1 không-overwrite)
```js
const rl = screen.get("<RL_SLUG>", "RELATED_LIST");
for (const c of changedRowCells || []) {
    if (c.relatedListSlug !== "<RL_SLUG>") continue;
    if (c.fieldSlug !== "<TRIGGER_CELL_SLUG>") continue;
    const row = await rl.findRow((r) => r.recordId === c.recordId);
    if (row) {
        const targetCell = row.get("<TARGET_CELL_SLUG>");
        if (!targetCell.value) {                         // không overwrite
            const newVal = /* tính từ c.newValue */;
            targetCell.value = newVal;
        }
    }
}
```

**Variant 2B** (Q3=3 overwrite)
```js
// ... bỏ check `if (!targetCell.value) { ... }`, set thẳng
```

---

## R3 — Ẩn/hiện field theo điều kiện

**Khi nào**: ẩn field discount khi status != 'pending'.

```js
const statusItem = screen.get("status", "FORM_ITEM");
const discountItem = screen.get("discount", "FORM_ITEM");
const shouldShow = statusItem.value === "pending";
if (discountItem.display !== shouldShow) {
    discountItem.display = shouldShow;
}
```

*Không cần Q1/Q2/Q3 vì không set value — chỉ toggle display.*

---

## R4 — Toggle readOnly theo điều kiện

```js
const item = screen.get("<SLUG>", "FORM_ITEM");
const shouldLock = /* condition */;
if (item.readOnly !== shouldLock) {
    item.readOnly = shouldLock;
}
```

---

## R5 — Required theo điều kiện (cross-field validate)

```js
const totalItem = screen.get("total", "FORM_ITEM");
const reasonItem = screen.get("reason", "FORM_ITEM");
const shouldRequire = Number(totalItem.value ?? 0) > 100;
if (reasonItem.required !== shouldRequire) {
    reasonItem.required = shouldRequire;
}
```

---

## R6 — Aggregate bảng → set field cha (sum)

**Khi nào**: tính total = sum(quantity * price) của order_lines.

```js
const rl = screen.get("<RL_SLUG>", "RELATED_LIST");
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

*Set field cha → BẮT BUỘC `if (item.value !== sum) { ... }` chống loop.*

---

## R7 — Auto-submit khi đạt threshold

**Khi nào**: tổng quantity > 100 → tự lưu bảng.

```js
const rl = screen.get("<RL_SLUG>", "RELATED_LIST");
const rows = await rl.rows();
let sum = 0;
for (const row of rows) {
    sum += Number(row.get("quantity").value ?? 0);
}
if (sum > 100 && !$ref.submitted) {              // tránh submit lặp
    $ref.submitted = true;
    try {
        await rl.submit();
    } catch (e) {
        $ref.submitted = false;                  // unblock retry nếu fail
        console.error("auto-submit failed:", e);
    }
}
```

⚠️ Cảnh báo: nguy hiểm. Chỉ dùng khi business chắc chắn muốn auto-save không cần user xác nhận.

---

## R8 — Filter lookup options theo điều kiện

**Khi nào**: lookup product chỉ hiển thị item active.

```js
const { records } = await filterRecords("product", {
    filterItems: [{ field: "status", op: "=", params: ["active"] }],
    limit: 200,
});
const productItem = screen.get("product", "FORM_ITEM");
const ids = records.map((r) => r.id);
const current = productItem.limitedOptions || [];
const same = current.length === ids.length && current.every((v, i) => v === ids[i]);
if (!same) {
    productItem.limitedOptions = ids;
}
```

> Gọi `filterRecords` khi cần dữ liệu; không dùng `$ref.optionsLoaded` để bỏ qua việc cập nhật dữ liệu. So sánh array trước khi set để tránh re-render thừa.

**Biến thể cell trong related list** (giới hạn option 1 cột `single_choice`/`lookup` của bảng, từ script form cha):
```js
const rl = screen.get("<RL_SLUG_TRONG_LAYOUT>", "RELATED_LIST");
const rows = await rl.rows();
for (const row of rows) {
    row.get("<cell_slug>").limitedOptions = ["opt_a", "opt_b"];  // single_choice: slug option; lookup: record ID
}
```
> `cell.limitedOptions` KHÔNG trigger re-run. ⚠️ Dùng đúng **slug related list trong layout** (≠ slug object đích). Xem Case 6 (case-studies.md) — limit `apply_type` theo Loại phiếu thu chi.

---

## R9 — Visual highlight cell (displayHtml)

**Khi nào**: row có price > 1tr → tên hiển thị đỏ.

```js
const rl = screen.get("<RL_SLUG>", "RELATED_LIST");
const rows = await rl.rows();
for (const row of rows) {
    const price = Number(row.get("price").value ?? 0);
    const nameCell = row.get("name");
    if (price > 1000000) {
        nameCell.displayHtml = `<b style="color:red">🔥 ${nameCell.value}</b>`;
    } else {
        nameCell.displayHtml = "";       // reset
    }
}
```

*displayHtml chỉ cosmetic — không lưu xuống server.*

---

## R10 — Validate cross-field (block save bằng required)

```js
const totalItem = screen.get("total", "FORM_ITEM");
const reasonItem = screen.get("reason", "FORM_ITEM");
const needReason = Number(totalItem.value ?? 0) > 100;
if (reasonItem.required !== needReason) {
    reasonItem.required = needReason;
}
```

## R12 — Trigger button programmatically

```js
if (changedFields["order"]) {
    screen.triggerButton("recalculate", false);
}
```

---

## R13 — Reuse data trong cùng 1 lần exec via biến local

**Khi nào**: cần dùng cùng kết quả `filterRecords` ở nhiều đoạn của 1 lần exec.

```js
// Trong cùng một lần chạy, dùng biến local để tái sử dụng kết quả.
// Không giả định thời hạn cache giữa các lần chạy.
const { records: products } = await filterRecords("product", {
    filterItems: [{ field: "status", op: "=", params: ["active"] }],
    limit: 500,
});

const matched = products.find((p) => p.id === $record.product);
const ids = products.map((p) => p.id);
// ... dùng products ở các đoạn khác trong cùng exec ...
```

> Không lưu `products` dài hạn vào `$ref` để bỏ qua việc đọc dữ liệu. Record có thể thay đổi giữa các lần chạy; dùng biến local trong lần chạy hiện tại.
>
> `$ref` chỉ dùng cho **state thật của script** mà cache không xử lý được: flag idempotency (`$ref.seeded`), `$ref.submitted` chống submit lặp, counter, last-layout-id chống loop swap.

---

## R14 — Block nút submit của Path Component

**Khi nào**: user muốn chặn user bấm nút submit/chuyển stage trong Path Component.

**Block toàn bộ stage trong path**
```js
const path = screen.get("<PATH_COMPONENT_SLUG>", "PATH_COMPONENT");
const shouldBlockSubmit = true;
if (path.submitBlocked !== shouldBlockSubmit) {
    path.submitBlocked = shouldBlockSubmit;
}
```

**Chỉ block một số stage**
```js
const path = screen.get("<PATH_COMPONENT_SLUG>", "PATH_COMPONENT");
const blockedStages = ["<STAGE_VALUE>"];
const currentBlockedStages = path.submitBlockedStages || [];
const sameStages =
    currentBlockedStages.length === blockedStages.length &&
    currentBlockedStages.every((stage, index) => stage === blockedStages[index]);

if (!sameStages) {
    path.submitBlockedStages = blockedStages;
}
```

Lưu ý:
1. `submitBlocked = true` block toàn bộ stage trong path.
2. `submitBlockedStages` dùng stage value, không dùng label/name.
3. API này chỉ disabled nút submit, chưa hiển thị message.
4. Đây không phải SET `.value`, nên không vào DANGER MODE.

---

## Lưu ý chung khi build code từ recipe

1. 🚨 **KHÔNG dùng `return`** ở bất kỳ đâu trong script (kể cả guard, kể cả early-exit "an toàn"). Script chung hàm với scripts khác. Bao toàn bộ logic trong `if (positive_condition) { ... }`.
2. **Thay tất cả `<...>` placeholder bằng slug thực** mà user đã cung cấp ở Bước 2.5.
3. **Map fieldType → value shape** theo `api-cheatsheet.md` §7. Đặc biệt:
   - `date` → `new Date(...)` không phải string
   - `time` → ms number
   - `lookup_normal`/`reference`/`embedded`/`children` → **string ID** (KHÔNG phải `{ id, name }`). Muốn đọc field khác của record được link → phải `filterRecords()` fetch lại.
   - `single_choice` → value string (không phải object)
4. **Combine recipe khi nghiệp vụ phức hợp**. VD: "khi đổi customer → fill address + filter lookup product" = R-custom-autofill + R8. Combine = đặt cạnh nhau (không return giữa các block).
5. **Mỗi recipe set value** đều phải pass Verify checklist Bước 7 (no return, await, shape, so sánh, guard).
