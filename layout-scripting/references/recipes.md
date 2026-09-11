# Recipes: pattern code mẫu

Chọn recipe theo Bước 5 của SKILL.md; biến thể guard theo Q1/Q2/Q3. Khi build code từ recipe:

- Không `return` (RULE §0); mọi set `.value` so sánh trước (RULE §1); recipe có set value vẫn phải qua checklist Bước 7.
- Thay mọi placeholder `<...>` bằng slug thực đã hỏi ở Bước 3.
- Value đúng SCRIPT shape (api-cheatsheet.md §7): `date` → `new Date(...)` (không string); `time` → ms number; `lookup_normal`/`reference`/`embedded`/`children` → string ID (không `{ id, name }`; cần field khác của record được link → `filterRecords()`); `single_choice` → string slug option.
- Nghiệp vụ phức hợp (vd đổi customer → fill address + lọc lookup product = autofill + R8): đặt các recipe cạnh nhau, không `return` giữa các block.

## R1: Seed bảng một lần khi mở form mới

Pre-fill bảng bằng data mặc định. Variant 1A (Q1 = 2, Q3 = 1, mặc định):

```js
/**
 * ⚠️ SCRIPT SET DATA TỰ ĐỘNG
 * Chạy khi: form Tạo mới (chưa có id)
 * KHÔNG chạy khi: vào lại form đã lưu
 * KHÔNG ghi đè: nếu bảng đã có dòng
 * KHÔNG dùng return — script chạy chung hàm với scripts khác.
 */
if (formType !== "view") {
    const rl = screen.get("<RL_SLUG_TRONG_LAYOUT>", "RELATED_LIST");
    const rows = await rl.rows();
    if (rows.length === 0) {
        rl.setData([
            { /* field slug: value theo API record shape §7B */ },
        ]);
    }
}
```

Variant 1B (Q3 = 3, luôn overwrite): banner overwrite (safety-rules.md) + `if (formType !== "view") { rl.setData([...]); }`, bỏ check `rows.length`.

## R2: Autofill cell khi user gõ cell khác cùng dòng

Vd gõ tên sản phẩm → tự fill giá. Variant 2A (Q1 = 4, Q3 = 1):

```js
const rl = screen.get("<RL_SLUG>", "RELATED_LIST");
for (const c of changedRowCells || []) {
    if (c.relatedListSlug !== "<RL_SLUG>") continue;
    if (c.fieldSlug !== "<TRIGGER_CELL_SLUG>") continue;
    const row = await rl.findRow((r) => r.recordId === c.recordId);
    if (row) {
        const targetCell = row.get("<TARGET_CELL_SLUG>");
        if (!targetCell.value) {                 // không overwrite
            const newValue = /* tính từ c.newValue */;
            if (targetCell.value !== newValue) {
                targetCell.value = newValue;
            }
        }
    }
}
```

Variant 2B (Q3 = 3): bỏ `if (!targetCell.value)`, giữ so sánh `!==`.

## R3: Ẩn/hiện field theo điều kiện

Không set value → không cần Q1/Q2/Q3.

```js
const statusItem = screen.get("status", "FORM_ITEM");
const discountItem = screen.get("discount", "FORM_ITEM");
const shouldShow = statusItem.value === "pending";
if (discountItem.display !== shouldShow) {
    discountItem.display = shouldShow;
}
```

## R4: readOnly theo điều kiện

```js
const item = screen.get("<SLUG>", "FORM_ITEM");
const shouldLock = /* điều kiện */;
if (item.readOnly !== shouldLock) {
    item.readOnly = shouldLock;
}
```

## R5: required theo điều kiện (validate chéo field, chặn lưu bằng required)

```js
const totalItem = screen.get("total", "FORM_ITEM");
const reasonItem = screen.get("reason", "FORM_ITEM");
const shouldRequire = Number(totalItem.value ?? 0) > 100;
if (reasonItem.required !== shouldRequire) {
    reasonItem.required = shouldRequire;
}
```

## R6: Tổng hợp bảng thành field cha

Vd `total` = sum(quantity × price) của `order_lines`. Set field cha bắt buộc so sánh (RULE §1); không cần Guard 4 vì script tự chạy lại khi `changedRowCells` populate.

```js
const rl = screen.get("<RL_SLUG>", "RELATED_LIST");
const rows = await rl.rows();
let sum = 0;
for (const row of rows) {
    const quantity = Number(row.get("quantity").value ?? 0);
    const price = Number(row.get("price").value ?? 0);
    sum += quantity * price;
}
const totalItem = screen.get("total", "FORM_ITEM");
if (totalItem.value !== sum) {
    totalItem.value = sum;
}
```

## R7: Auto-submit bảng khi đạt ngưỡng

Nguy hiểm: chỉ dùng khi business chắc chắn muốn tự lưu không cần user xác nhận.

```js
const rl = screen.get("<RL_SLUG>", "RELATED_LIST");
const rows = await rl.rows();
let sum = 0;
for (const row of rows) {
    sum += Number(row.get("quantity").value ?? 0);
}
if (sum > 100 && !$ref.submitted) {      // $ref.submitted chống submit lặp
    $ref.submitted = true;
    try {
        await rl.submit();
    } catch (e) {
        $ref.submitted = false;          // cho phép thử lại nếu lỗi
        logger.log("auto-submit failed:", e);
    }
}
```

## R8: Giới hạn option lookup/select theo điều kiện

Không set value → không DANGER MODE. Gọi `filterRecords` mỗi lần cần dữ liệu (không dùng `$ref.optionsLoaded` để bỏ qua cập nhật); so sánh mảng trước khi set để tránh re-render thừa.

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

Biến thể cột trong bảng (chạy ở script form cha): `await rl.rows()` rồi `row.get("<cell_slug>").limitedOptions = [...]` cho từng row; `single_choice` nhận mảng slug option, `lookup` nhận mảng record ID; `cell.limitedOptions` không trigger re-run; dùng slug related list trong layout (≠ slug object đích). Mẫu đầy đủ: [Case 6](case-studies.md#case-6-giới-hạn-option-cột-single_choice-trong-bảng-theo-field-cha).

## R9: Highlight cell bằng displayHtml

Chỉ cosmetic, không lưu xuống server.

```js
const rl = screen.get("<RL_SLUG>", "RELATED_LIST");
const rows = await rl.rows();
for (const row of rows) {
    const price = Number(row.get("price").value ?? 0);
    const nameCell = row.get("name");
    if (price > 1000000) {
        nameCell.displayHtml = `<b style="color:red">${nameCell.value}</b>`;
    } else {
        nameCell.displayHtml = "";       // reset
    }
}
```

## R10: Bấm button bằng script

```js
if (changedFields["order"]) {
    screen.triggerButton("recalculate", false);
}
```

Button có thể kích hoạt lại script → thêm guard chống loop (checklist Bước 7).

## R11: Tái sử dụng kết quả filterRecords trong cùng lần chạy

Dùng biến local; không lưu vào `$ref` để bỏ qua việc đọc dữ liệu (record có thể đổi giữa các lần chạy). `$ref` chỉ giữ state thật của script: `$ref.seeded`, `$ref.submitted`, counter, last-layout-id chống loop.

```js
const { records: products } = await filterRecords("product", {
    filterItems: [{ field: "status", op: "=", params: ["active"] }],
    limit: 500,
});
const matched = products.find((p) => p.id === $record.product);
const ids = products.map((p) => p.id);
// ... dùng products ở các đoạn khác trong cùng lần chạy
```

## R12: Chặn nút submit của Path Component

Code mẫu cho `path.submitBlocked` (block toàn bộ stage) và `path.submitBlockedStages` (mảng `stage.value`, so sánh shallow trước khi set): api-cheatsheet.md mục "Path Component". API chỉ disable nút submit, chưa hiển thị message. Không phải set `.value` → không vào DANGER MODE.
