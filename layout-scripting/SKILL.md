---
name: layout-scripting
description: Sinh hoặc sửa code clientScript cho Layout Rule của form builder Cogover. Dùng khi user mô tả nghiệp vụ tiếng Việt và muốn code paste-ready để dán vào ô "Cấu hình script" của layout. Khi sửa script layout hiện có, bắt buộc dùng skill object-layout để lấy `pageSettings.script` hiện tại trước, giữ logic cũ không liên quan và hỏi lại nếu ranh giới sửa chưa rõ. Bắt buộc kích hoạt decision tree 3 câu hỏi khi nghiệp vụ có thao tác SET giá trị (tránh re-render loop + wipe user edit).
metadata:
  author: cogover
  version: "1.0.2"
---

# layout-scripting — sinh code Layout Rule Script

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-07`

## Mission

User mô tả nghiệp vụ bằng tiếng Việt → output code JavaScript paste-ready cho `pageSettings.script` của layout. Đối tượng user **không biết code** → mọi rủi ro (re-render loop, wipe data, idempotency) phải được skill chặn bằng guard + hỏi tự nhiên.

API runtime: xem `reference/api-cheatsheet.md`.

---

## 🚨🚨🚨 RULE §-1 — LUÔN LẤY SCRIPT HIỆN TẠI TRƯỚC KHI SỬA (CRITICAL)

Khi user yêu cầu **sửa / thêm / thay đổi / cập nhật script** cho một layout đã có, PHẢI dùng skill `object-layout` để lấy script hiện tại của layout trước khi viết hoặc output script mới.

Script hiện tại nằm ở `pageSettings.script` của layout. Dùng khả năng "Lấy script đang có sẵn trên layout" trong skill `object-layout`:

1. Lấy chi tiết layout bằng API view.
2. Đọc `data.pageSettings.script`.
3. Nếu script rỗng/null, ghi nhận rõ layout hiện chưa có script.
4. Nếu script đã có nội dung, coi yêu cầu của user là **patch vào script hiện tại**, không phải viết lại từ đầu.

### Nguyên tắc bảo toàn logic cũ

- **KHÔNG xoá, rewrite, reorder lớn, hoặc "dọn dẹp" các logic cũ** nếu chúng không liên quan trực tiếp đến phần user yêu cầu sửa.
- Chỉ thay đúng block/nhánh/field/related list/business rule mà user yêu cầu.
- Nếu cần thêm logic mới, ưu tiên chèn thành block rõ ràng bên cạnh logic liên quan, giữ nguyên phần còn lại.
- Nếu script cũ có lỗi nghiêm trọng (vd `return`, set `.value` không guard) nhưng nằm ngoài phạm vi user yêu cầu, báo rõ rủi ro và hỏi user có muốn sửa luôn không; KHÔNG tự ý sửa rộng.
- Nếu không xác định chắc block nào trong script cũ là phần cần sửa, PHẢI confirm với user trước khi output script mới.

### Khi thiếu thông tin để lấy script hiện tại

Nếu user chưa cung cấp layout ID/slug hoặc chưa rõ layout nào cần sửa, hỏi lại trước. Không được sinh script thay thế khi chưa lấy được script hiện tại, trừ khi user xác nhận đây là script mới hoàn toàn cho layout chưa có script.

---

## 🚨🚨🚨 RULE §0 — TUYỆT ĐỐI KHÔNG DÙNG TỪ KHOÁ `return` (CRITICAL)

**Đây là rule QUAN TRỌNG NHẤT của skill. Vi phạm = script lỗi.**

Mọi script Layout Rule được runtime gom vào **CÙNG 1 hàm async duy nhất**. Nếu script này có `return` → các script khác user paste bên dưới (gộp từ nhiều nguồn / nghiệp vụ) sẽ **BỊ CHẶN không chạy**.

### TUYỆT ĐỐI CẤM:

```js
// ❌ SAI — chặn mọi logic phía dưới
if (!customerId) return;
const item = screen.get("address", "FORM_ITEM");
item.value = ...;

// ❌ SAI — early return dù có lý do
if (formType === "view") return;

// ❌ SAI — return trong if-else
if (type === "A") {
    // ...
} else {
    return;
}
```

### LUÔN DÙNG `if (condition) { ... }` block:

```js
// ✅ ĐÚNG — bao bằng if-block, logic phía dưới vẫn chạy
if (customerId) {
    const item = screen.get("address", "FORM_ITEM");
    item.value = ...;
}

// ✅ ĐÚNG — đảo điều kiện
if (formType !== "view") {
    // ... logic chỉ chạy ở create mode
}

// ✅ ĐÚNG — chỉ vào nhánh khi điều kiện thoả
if (type === "A") {
    // ...
} else if (type === "B") {
    // ...
}
// (không có else { return; } — script tự kết thúc)
```

### Vì sao QUAN TRỌNG

User có thể paste **nhiều script từ nhiều nguồn** vào cùng 1 ô "Cấu hình script" của layout (skill này sinh + các script user copy từ task trước + script đồng nghiệp viết). Runtime gom hết → 1 hàm. `return` ở script đầu = các script sau không chạy → user debug khổ.

### Chỉ ngoại lệ duy nhất: `continue` trong loop

```js
// ✅ OK — continue chỉ skip iteration, không thoát script
for (const c of changedRowCells || []) {
    if (c.relatedListSlug !== "order_lines") continue;
    // ...
}
```

### Áp dụng cho TẤT CẢ guard

Mọi guard cũ (`if (formType === "view") return;`, `if (!changedFields["X"]) return;`, `if (rows.length > 0) return;`) **PHẢI** đảo thành `if (condition_đúng) { ... }` block. Xem `safety-rules.md` đã refactor.

---

## 🚨🚨🚨 RULE §1 — TRÁNH VÒNG LẶP VÔ TẬN KHI SET VALUE (CRITICAL)

**Đây là rule QUAN TRỌNG THỨ NHÌ. Vi phạm = browser freeze / crash, mất data, user mất niềm tin.**

### Cơ chế re-trigger (PHẢI NHỚ)

Script Layout Rule **tự re-run** khi 1 trong các điều xảy ra:

1. **Bất kỳ field nào trên form thay đổi value** (`changedFields[slug] = true`)
2. **Bất kỳ cell nào trong related list thay đổi value** (`changedRowCells` populate)

→ Nghĩa là: **script tự set value rồi tự bị trigger lại bởi chính value đó** = INFINITE LOOP.

### Kịch bản infinite loop điển hình

```js
// ❌ SAI — vòng lặp vô tận
const totalItem = screen.get("total", "FORM_ITEM");
totalItem.value = sum;
// → value đổi → script re-run → set lại → re-run → ... → freeze
```

```js
// ❌ SAI — set cell trong loop không guard
for (const row of rows) {
    const priceCell = row.get("price");
    priceCell.value = computePrice(row);
    // → cell đổi → script re-run → loop tiếp
}
```

### LUÔN DÙNG `if (current !== new) { ... }` TRƯỚC KHI SET

**MỌI** lệnh set `.value` (field hoặc cell) PHẢI có so sánh trước:

```js
// ✅ ĐÚNG — field cha
const totalItem = screen.get("total", "FORM_ITEM");
if (totalItem.value !== sum) {
    totalItem.value = sum;
}

// ✅ ĐÚNG — cell trong related list
const priceCell = row.get("price");
const newPrice = computePrice(row);
if (priceCell.value !== newPrice) {
    priceCell.value = newPrice;
}
```

### Reset value về null cũng phải so sánh

```js
// ❌ SAI — re-set null mỗi lần script chạy (vẫn loop ngầm nếu trigger khác)
applyTypeItem.value = null;

// ✅ ĐÚNG — chỉ reset khi đang có value
if (applyTypeItem.value) {
    applyTypeItem.value = null;
}
```

### Trường hợp KHÔNG cần guard (an toàn)

| API | Trigger re-run? | Cần guard? |
|---|---|---|
| `field.value =` / `cell.value =` | ✅ CÓ | 🚨 **BẮT BUỘC** so sánh |
| `field.limitedOptions =` | ❌ KHÔNG | Optional (so sánh để tránh re-render thừa) |
| `field.display =` | ❌ KHÔNG | Optional |
| `field.readOnly =` | ❌ KHÔNG | Optional |
| `field.required =` | ❌ KHÔNG | Optional |
| `cell.displayHtml =` | ❌ KHÔNG | Optional (cosmetic) |
| `rl.setData(...)` | ⚠️ Có thể | Guard `rows.length === 0` + idempotent payload |

> **Built-in safety net**: runtime có `markParentScriptStart/End` + 200ms debounce cho cell value channel — đỡ 1 phần, nhưng KHÔNG đủ để dựa. Luôn tự guard.

### Multi-field SET → so sánh từng cái

```js
// ✅ ĐÚNG — mỗi field 1 so sánh riêng
if (totalItem.value !== sum) {
    totalItem.value = sum;
}
if (qtyItem.value !== qty) {
    qtyItem.value = qty;
}
```

### Khi SET payload phức tạp (object/array) → so sánh shallow đủ

```js
// ✅ ĐÚNG — array of string IDs, so sánh shallow
const ids = records.map((r) => r.id);
const current = item.limitedOptions || [];
const same = current.length === ids.length && current.every((v, i) => v === ids[i]);
if (!same) {
    item.limitedOptions = ids;
}
```

### Vì sao QUAN TRỌNG

- Browser freeze → user mất data đang nhập.
- React DevTools báo "Maximum update depth exceeded" → user không biết script nào gây ra.
- Có thể không lộ ngay (run 50 lần / giây vẫn smooth ở máy mạnh) → ship production rồi mới phát hiện.
- Debug khó: stack trace chỉ về runtime, không chỉ về script user viết.

→ Phòng từ đầu bằng `if (current !== new)` rẻ hơn debug nhiều lần.

---

## 🚨 RULE §1.5 — RELATED LIST BULK STATE: LỆNH CHẠY SAU THẮNG

Related list hỗ trợ set trạng thái ở nhiều cấp:

- `rl.readOnly = bool` — áp cho toàn bảng.
- `await rl.getCol("field_slug")` — lấy 1 cột; có thể set `readOnly`, `required`, `value`.
- `await rl.getRow(index)` — lấy 1 hàng; có thể set `readOnly`, `required`.
- `row.get("field_slug")` — lấy 1 cell; có thể set `readOnly`, `required`, `value`, `limitedOptions`, `displayHtml`.

### Nguyên tắc ưu tiên

**Tất cả trạng thái `readOnly`/`required` cuối cùng đều quy về từng cell. Runtime KHÔNG ưu tiên theo API table > column > row > cell. Runtime ưu tiên theo THỨ TỰ CHẠY CODE: lệnh nào chạy sau thì thắng cho cell bị ảnh hưởng.**

```js
// ✅ ĐÚNG — khoá cả bảng, sau đó mở riêng dòng index 1
const rl = screen.get("order_lines", "RELATED_LIST");
rl.readOnly = true;

const row = await rl.getRow(1);
if (row) {
    row.readOnly = false;
}
```

Với script trên, dòng index 1 **không readOnly**, vì `row.readOnly = false` chạy sau `rl.readOnly = true`.

```js
// ✅ ĐÚNG — khoá cột product, sau đó mở riêng cell product của dòng index 1
const rl = screen.get("order_lines", "RELATED_LIST");
const productCol = await rl.getCol("product");
if (productCol) {
    productCol.readOnly = true;
}

const row = await rl.getRow(1);
if (row) {
    row.get("product").readOnly = false;
}
```

Cell `product` của dòng index 1 **không readOnly**, vì cell override chạy sau column override.

### Rule khi dùng getCol/getRow

- `rl.getCol("slug")` là async và chờ bảng ready → PHẢI `await`.
- `await rl.getCol("bad_slug")` trả `null` → PHẢI check `if (col) { ... }`.
- `rl.getRow(index)` là async và có thể trả `null` → PHẢI `await` + check `if (row) { ... }`.
- `row.value = ...` KHÔNG tồn tại, vì mỗi cell trong row có thể khác fieldType. Muốn set value trong row thì dùng `row.get("field_slug").value = ...`.
- `col.value = value` ghi đè cùng một giá trị cho toàn bộ cell hiện có trong cột đó. Đây là thao tác ghi hàng loạt, không phải trạng thái chung có thể đọc để so sánh: `col.value` không đại diện cho các giá trị hiện tại của cột. Runtime đã chặn thay đổi cell do script form cha tự tạo nên không cần guard chống lặp kiểu `if (col.value !== value)`. Chỉ dùng khi user xác nhận muốn ghi đè toàn cột; nếu cần giữ giá trị khác nhau hoặc chỉ sửa cell phù hợp điều kiện, dùng `await rl.rows()` rồi kiểm tra từng `row.get("field_slug").value`.
- `col.readOnly/required` áp cho cell hiện có và các row mới phát sinh sau đó trong cùng cột.

---

## Nguyên tắc tối thượng — CODE PHẢI DỄ HIỂU KHI MỚI ĐỌC

User là **non-coder**, sau này sẽ phải tự đọc lại / sửa script. Mọi dòng code phải readable ngay từ lần đọc đầu tiên — KHÔNG được trade clarity lấy "elegance" hay "smart code".

### Các quy tắc cụ thể

1. **Tên biến nói tiếng người**, không viết tắt tối nghĩa:
   - ✅ `const orderId = $record.order;`
   - ❌ `const oid = $record.order;` / `const x = $record.order;`

2. **Mỗi dòng làm 1 việc**, không gom nhiều bước thành 1 expression dài:
   - ✅ ```js
     const { records } = await filterRecords("customer", { filterItems: [...] });
     const customer = records[0];
     const address = customer?.defaultAddress ?? "";
     ```
   - ❌ ```js
     const address = (await filterRecords("customer", { filterItems: [...] })).records[0]?.defaultAddress ?? "";
     ```

3. **Tránh ternary lồng nhau / optional chaining sâu**. Chia thành if-block rõ ràng:
   - ✅ ```js
     if (customerId) {
         const item = screen.get("address", "FORM_ITEM");
         if (!item.value) {  // chưa có địa chỉ → mới fill
             item.value = ...;
         }
     }
     ```
   - ❌ ```js
     screen.get("address", "FORM_ITEM").value ||
       (customerId && (screen.get("address", "FORM_ITEM").value = await ...));
     ```

4. **KHÔNG dùng functional combinators (`reduce`/`flatMap`/curry/pipe)** khi `for...of` đơn giản đủ dùng. User đọc `for (const row of rows) { ... }` dễ hơn `rows.reduce((acc, row) => ...)`.

5. **KHÔNG abstract sớm**. 1 script chỉ chạy 1 nghiệp vụ — đừng tạo helper function `applyOverride()`, `withGuard()`, factory… trừ khi có **lý do bắt buộc** (vd dùng lại 3+ lần trong cùng script).

6. **Comment giải thích WHY khi guard / pass-through không hiển nhiên**:
   - ✅ `if (existingRows.length === 0) { /* bảng còn rỗng → mới seed, tránh ghi đè data user */ }`
   - ✅ `rl.setData(records);  // records từ filterRecords đã ở API shape, pass thẳng — converter xử`
   - ❌ Comment giải thích cái code đã tự nói: `// set value vào field` (thừa)

7. **Comment header `⚠️`** đầu script là BẮT BUỘC khi có set value — liệt kê 3 dòng: chạy khi nào / KHÔNG chạy khi / KHÔNG ghi đè. Đây là thứ user xem trước tiên khi mở lại script.

8. **Hardcode rõ ràng > config thông minh**. Slug field, slug bảng, threshold → viết thẳng làm string literal, đừng tạo `const CONFIG = { ... }` cho 1-2 hằng.

9. **Đừng "phòng thủ" cho case không tồn tại**. Vd nếu đã bao logic trong `if (orderId) { ... }` rồi thì không cần `customerId?.toString() ?? ""` ở dòng tiếp.

10. **Output ngắn tốt hơn output đầy đủ-nhưng-rườm-rà**. Nếu cùng nghiệp vụ làm được trong 15 dòng → đừng viết 40 dòng.

> **Test "dễ đọc"**: trước khi output, đọc lại script với mindset của user non-coder. Nếu có 1 dòng phải đọc lần 2 mới hiểu → viết lại.

---

## Workflow (làm theo đúng thứ tự)

### Bước 0 — Lấy script hiện tại nếu đang sửa layout đã có

Nếu yêu cầu là sửa/thêm/cập nhật script trên layout hiện có:

1. Dùng skill `object-layout` để lấy `pageSettings.script` hiện tại của layout.
2. Đọc script cũ trước khi thiết kế thay đổi.
3. Xác định block liên quan đến yêu cầu user.
4. Nếu block liên quan không rõ, hỏi user confirm ranh giới sửa.
5. Khi output, trả về script hoàn chỉnh sau khi patch, trong đó các logic cũ không liên quan được giữ nguyên.

Chỉ bỏ qua bước này khi user nói rõ đây là script mới hoàn toàn hoặc layout hiện chưa có script.

### Bước 1 — Đọc API cheatsheet
Luôn `Read` file `reference/api-cheatsheet.md` đầu tiên. Đây là knowledge base bắt buộc — không sinh code mà chưa đọc.

Khi cần viết log để debug/check lỗi, dùng mục **"Debug bằng `logger`"** trong cheatsheet. Không sinh `console.log`; mặc định dùng `logger.log(...)`, chỉ bật `logger.forceShowLog = true` tạm thời khi user cần xem log ngoài chế độ nhà phát triển.

Nếu script có dùng `filterRecords()` hoặc đọc dữ liệu record trả về từ API, **bắt buộc đọc lại mục "Record từ filterRecords + lookup expand 1 cấp" trong `reference/api-cheatsheet.md`** trước khi viết code. Đây là điểm rất dễ sai kiểu dữ liệu:
- Lookup cấp 1 trong record từ `filterRecords()` có thể là `RecordItem` object có `id`, `name` và các field khác tuỳ object/config.
- Lookup lồng bên trong lookup cấp 1 (cấp 2 trở đi) **không expand object nữa**; chỉ là `string` ID hoặc `string[]` ID.
- Khi set vào `field.value` / `cell.value` vẫn phải dùng SCRIPT shape: lookup = string ID, không phải object.

### Bước 2 — Parse mô tả của user
Trích 4 entity:
- **Target**: field/cell/related-list/path-component nào (slug nếu user nói; nếu không nói → placeholder + nhắc trong output).
- **Trigger**: khi nào script chạy (mount / changedFields / changedRowCells).
- **Action**: set value / show-hide / readOnly / required / submit / block submit / displayHtml / fetch.
- **Pattern**: seed / reactive / one-shot / aggregate / validate.
- **Nguồn dữ liệu fetch**: nếu dùng `filterRecords()`, xác định field nào là lookup cấp 1, field nào là nested lookup cấp 2 để không đọc nhầm object.

### Bước 2.5 — Hỏi technical info còn thiếu (BẮT BUỘC)

Code script cần đúng **slug** và **fieldType** kỹ thuật. Nếu user mô tả nghiệp vụ chung (vd "khi đổi khách hàng thì fill địa chỉ") mà chưa cho biết slug/type → **bắt buộc** hỏi trước khi đi tiếp.

Các info phải biết để sinh code đúng:

| Info | Khi nào cần | Ví dụ |
|---|---|---|
| **Object slug** (đang config layout) | Luôn — để biết script chạy trên object nào | `return_order`, `order`, `customer` |
| **Field slug** + **fieldType** | Mỗi field nhắc trong mô tả (target SET, trigger field, field đọc data) | `customer` (lookup), `address` (short_text), `quantity` (number), `delivery_date` (date) |
| **Related list slug TRONG LAYOUT** | Khi nghiệp vụ đụng tới bảng (related list) | ⚠️ Xem cảnh báo dưới |

#### ⚠️ Cảnh báo CỰC QUAN TRỌNG về related list slug

**Slug của related list trong layout KHÁC slug của object liên kết.**

- Khi designer kéo related list vào layout → đặt 1 slug riêng cho related list đó **trong phạm vi layout này**.
- Vd: layout `return_order` có related list trỏ tới object `order_line`, designer đặt slug bảng đó là `return_order_lines` (HOẶC `lines`, HOẶC bất kỳ tên gì designer chọn).
- **Trong script PHẢI dùng slug của related list trong layout**, không phải slug của object đích (`order_line`).
- Sai slug → `screen.get("order_line", "RELATED_LIST")` trả `null` → script silent fail.

Khi hỏi user, **luôn** nhấn mạnh:
> "Slug của related list **trong layout** là gì? Đây là slug designer đặt khi kéo bảng vào layout. Vào trang Sửa giao diện → click vào bảng → check field 'slug'. KHÔNG phải slug của object kia."

#### Pattern hỏi (gộp 1 lần nếu thiếu nhiều info)

Dùng `AskUserQuestion` với 1-3 câu hỏi (mỗi câu cover 1 cluster info), HOẶC hỏi text trực tiếp với checklist:

```
Để sinh code chính xác, cho mình biết các slug và type:

1. **Object** đang config layout: slug là gì? (vd: `return_order`)
2. **Field "khách hàng"**: slug? fieldType? (vd: slug=`customer`, type=`lookup`)
3. **Field "địa chỉ"**: slug? fieldType? (vd: slug=`address`, type=`short_text`)
4. **Bảng "chi tiết đơn"**: slug **TRONG LAYOUT** là gì? ⚠️ KHÔNG phải slug của object kia.
   (Vào Sửa giao diện → click vào bảng → xem field 'slug')
```

Nếu user trả lời thiếu → hỏi lại đúng item còn thiếu. KHÔNG đoán slug. KHÔNG dùng placeholder `/* SLUG */` nữa — phải có slug thực tế hoặc dừng workflow.

### Bước 3 — Detect DANGER MODE (BẮT BUỘC)

Mô tả có 1 trong các keyword sau → đi vào **DANGER MODE**:
- "set", "gán", "đổi giá trị", "fill", "tự động điền"
- "lấy từ X đổ vào Y", "copy", "sao chép", "lấy data"
- "seed", "tự động lưu", "tự động submit"
- "khi chọn X thì set/đổi/fill Y"

→ Mở `reference/safety-rules.md` + đi qua **Decision tree** bên dưới. **Không skip dù mô tả có vẻ đầy đủ.**

Mô tả KHÔNG có set value (chỉ show/hide/readOnly/highlight hoặc `submitBlocked`/`submitBlockedStages` để disable nút submit Path Component) → skip decision tree, đi thẳng Bước 5.

### Bước 4 — Decision tree (chỉ khi DANGER MODE)

Dùng `AskUserQuestion` lần lượt 3 câu sau. Format option phải có **ví dụ cụ thể tiếng Việt**, không dùng thuật ngữ kỹ thuật:

#### Q1 — Khi nào chạy?
Header: "Khi nào chạy"
Question: "Script này nên chạy khi nào?"
Options:
1. "Khi user vừa mở form" — Ví dụ: cứ mở form ra là script chạy, dù form mới hay form đã lưu.
2. "Khi user mới tạo bản ghi" — Ví dụ: chỉ chạy ở trang Tạo mới, KHÔNG chạy khi vào form đã lưu để xem/sửa.
3. "Khi user đổi 1 ô cụ thể" — Ví dụ: khi user đổi ô 'Khách hàng' → tự fill địa chỉ. Sẽ hỏi tên ô ở câu sau.
4. "Khi user gõ vào ô trong bảng" — Ví dụ: khi user gõ vào ô 'Tên SP' trong dòng → tự fill ô 'Giá' cùng dòng.

#### Q2 — Re-run on edit? (CHỈ hỏi nếu Q1 = option 1)
Header: "Mở form đã lưu"
Question: "Khi user mở lại form đã lưu trước đó để xem/sửa, script có cần chạy lại không?"
Options:
1. "KHÔNG cần chạy lại (an toàn nhất)" — Ví dụ: form Return Order đã lưu, user mở ra xem → KHÔNG tự seed lại order_lines, giữ nguyên data đã save.
2. "Có cần chạy lại" — Cảnh báo: chỉ chọn khi chắc chắn muốn ghi đè, có thể xoá thay đổi user đã làm.

#### Q3 — Overwrite policy?
Header: "Ghi đè data"
Question: "Trước khi script đổi giá trị, target (ô hoặc bảng) có thể đã có sẵn data user nhập không?"
Options:
1. "Có thể có — KHÔNG được ghi đè" — Ví dụ: bảng order_lines có thể có dòng user tự thêm, script không được xoá.
2. "Chắc chắn rỗng — overwrite được" — Ví dụ: field tự động luôn rỗng lúc đầu, fill cái mới vào không vấn đề.
3. "Luôn overwrite" — Cảnh báo: sẽ xoá data user nhập tay nếu có. Chỉ chọn khi business yêu cầu reset.

#### Q4 (follow-up tuỳ) — Tên trigger field/cell (CHỈ khi Q1 = 3 hoặc 4 và user chưa cho biết slug)
Hỏi text trực tiếp (không AskUserQuestion):
- Q1=3 → "Tên slug của field user đổi là gì?" (vd `order`, `customer`)
- Q1=4 → "Tên slug bảng + slug ô là gì?" (vd bảng `order_lines`, ô `product`)

### Bước 5 — Map answers → recipe + guard variant

Đọc `reference/recipes.md` để chọn recipe. Áp guard theo bảng (từ `safety-rules.md`).

> ⚠️ **NHẮC LẠI RULE §0**: TUYỆT ĐỐI KHÔNG dùng `return`. Mọi guard dưới đây dùng `if (positive_condition) { ... }` block bao quanh logic, KHÔNG được dùng `if (negative_condition) return;`.

| Q1 | Q2 | Q3 | Guard wrapper (if-block) |
|---|---|---|---|
| 1 mọi lần mở | 1 không re-seed | 1 không overwrite | `if (formType !== "view") { if (rows.length === 0) { ... } }` + (optional) `$ref.seeded` |
| 1 mọi lần mở | 1 không re-seed | 2 chắc chắn rỗng | `if (formType !== "view") { ... }` |
| 1 mọi lần mở | 2 có re-seed | 3 luôn overwrite | banner ⚠️ — chạy thẳng, không cần guard |
| 2 chỉ tạo mới | n/a | 1 không overwrite | `if (formType !== "view") { if (rows.length === 0) { ... } }` |
| 2 chỉ tạo mới | n/a | 2 chắc chắn rỗng | `if (formType !== "view") { ... }` |
| 3 user đổi field X | n/a | 1 không overwrite | `if (changedFields["X"]) { if (!target.value) { ... } }` |
| 3 user đổi field X | n/a | 2 chắc chắn rỗng | `if (changedFields["X"]) { ... }` |
| 3 user đổi field X | n/a | 3 luôn overwrite | `if (changedFields["X"]) { ... }` + ⚠️ banner |
| 4 user gõ cell | n/a | bất kỳ | `for (const c of changedRowCells \|\| []) { if (c.relatedListSlug === "X" && c.fieldSlug === "Y") { ... } }` — KHÔNG dùng `continue` trừ khi loop body có nhiều bước |

### Bước 6 — Sinh code với guard + so sánh trước khi set

> ⚠️ **NHẮC LẠI RULE §0**: TUYỆT ĐỐI KHÔNG dùng `return`. Bao toàn bộ logic bằng `if (positive_condition) { ... }` block.

**Mọi set value field cha** bắt buộc kèm so sánh:
```js
const item = screen.get("X", "FORM_ITEM");
if (item.value !== newValue) {
    item.value = newValue;  // tránh re-render loop
}
```

**Mọi rl.setData(...)** bắt buộc check `existingRows.length === 0` (bằng if-block) trừ khi Q3=3.

**Header comment tự động** (auto-prepend khi có DANGER MODE):
```js
/**
 * ⚠️ SCRIPT NÀY THAY ĐỔI DỮ LIỆU FORM TỰ ĐỘNG
 *
 * Chạy khi: <Q1 answer>
 * KHÔNG chạy khi: <Q2 logic>
 * KHÔNG ghi đè: <Q3 logic>
 *
 * Nếu sửa script này, GIỮ NGUYÊN các điều kiện `if (...)` bao quanh logic.
 * TUYỆT ĐỐI KHÔNG thêm `return` — script này nằm chung 1 hàm với
 * các script khác, `return` sẽ chặn chúng không chạy.
 */
```

### Bước 7 — Verify checklist trước khi output

Tự kiểm toàn bộ checklist:

0. 🚨 **TUYỆT ĐỐI KHÔNG có từ khoá `return`** ở bất kỳ đâu trong script (kể cả trong if-else, kể cả "có lý do chính đáng"). Script chạy chung 1 hàm với scripts khác — `return` chặn hết. Grep code vừa sinh xem có `return` không. CÓ → fix bằng cách bao if-block. Ngoại lệ duy nhất: `continue` trong `for` loop.
0.5. 🚨 **Nếu đang sửa script layout hiện có, đã lấy `pageSettings.script` hiện tại bằng skill `object-layout` chưa?** Script output có giữ nguyên toàn bộ logic cũ không liên quan không? Nếu chưa lấy được script cũ hoặc không rõ block cần sửa → hỏi user, không output script thay thế.
1. 🚨 **MỌI SET `.value` (field hoặc cell) PHẢI có `if (current !== new) { current = new; }`** — RULE §1. Re-trigger script là tự động → set value không guard = infinite loop. Grep code: tìm mọi dòng có `.value =` (cả `field.value`, `cell.value`, `item.value`, `row.get(...).value`) → check ngay phía trên có `if (... !== ...)` không. Set `null` cũng phải so sánh `if (item.value) { item.value = null; }`.
2. Mọi `rl.row/rows/getRow/getCol/findRow/submit/filterRecords` có `await` chưa?
3. Value SET cho `row.get(slug).value` / `field.value` có khớp **§7 SCRIPT shape** không? (date → `Date`, time → ms, range → `{ gte, lte }`, lookup → **string ID** — KHÔNG phải `{ id, ... }`)
4. `rl.setData(records)` có dùng **§7B API record shape** không? (date → **epoch ms number** — KHÔNG `Date` object; lookup → chấp `RecordItem | string | array`). KHÔNG nhầm 2 shape.
5. SET bảng có guard `if (rows.length === 0) { rl.setData(...) }` (trừ khi user chọn overwrite)? Payload setData có idempotent (cùng input → cùng output) không?
6. `await rl.getCol("slug")` / `await rl.getRow(index)` đã null-check chưa? Có đang dùng đúng rule lệnh chạy sau thắng cho `readOnly/required` chưa?
6.5. Không có `row.value = ...` chứ? Row không hỗ trợ set value toàn hàng; phải dùng `row.get("field_slug").value`.
6.6. Nếu dùng `col.value = ...`, user đã xác nhận muốn ghi đè toàn bộ cell hiện có bằng cùng một giá trị chưa? Không đọc `col.value` để guard vì nó không đại diện cho các giá trị hiện tại của cột. Nếu cần giữ giá trị khác nhau hoặc chỉ sửa cell phù hợp điều kiện, phải dùng `await rl.rows()` và xử lý từng cell.
7. Guard wrapper theo bảng Bước 5 đã có? (if-block, KHÔNG phải `if (...) return;`)
8. Không lưu kết quả `filterRecords` dài hạn vào `$ref` để bỏ qua việc đọc dữ liệu. Record có thể thay đổi; tái sử dụng kết quả bằng biến local trong cùng lần chạy.
9. **Nếu dùng `filterRecords()` và đọc field lookup trong record trả về: đã áp dụng rule lookup expand 1 cấp chưa?** Lookup cấp 1 có thể là object/string; nested lookup cấp 2 trở đi chỉ là `string` hoặc `string[]` ID. Không được đọc `record.customer.owner.name` nếu `owner` là nested lookup; phải fetch tiếp bằng ID.
10. **Code dễ đọc khi mới nhìn** (xem "Nguyên tắc tối thượng" đầu file): tên biến nói tiếng người, mỗi dòng 1 việc, không ternary lồng, không helper function thừa, không abstract sớm, không "phòng thủ" cho case không tồn tại. Đọc lại script với mindset user non-coder — nếu phải đọc 1 dòng tới lần 2 mới hiểu → viết lại.
11. **KHÔNG dùng `screen.changeLayout(...)`** trong script. API chuyển layout không được phép dùng trong output của skill này.
12. **`triggerButton`** có guard chống loop nếu có thể tự kích hoạt lại script?
13. **Log debug có dùng `logger.log(...)` thay cho `console.log` không?** Nếu có `logger.forceShowLog = true`, đã nói rõ đây là cờ bật tạm và cần xoá/tắt sau khi debug chưa?
14. **Nếu dùng `submitBlockedStages` cho Path Component, giá trị trong mảng là `stage.value` chưa?** Không dùng label/name hiển thị của stage.

Lỗi → fix in-place. Không output code chưa pass toàn bộ checklist. **Điểm 0, 0.5 hoặc 1 sai = REJECT toàn bộ code.**

### Bước 8 — Output

Format BẮT BUỘC (4 phần):

```markdown
## Code

[code block JavaScript đầy đủ — paste vào ô Cấu hình script]

## Script này làm gì

[3-5 dòng tiếng Việt thân thiện: chạy khi nào, kiểm tra gì, đổi gì, có gì để bảo vệ data user]

## 🧪 Bắt buộc test trước khi đưa lên production

1. [test case 1 cụ thể với business]
2. [test case 2]
3. [test case 3]
4. [test case 4 — chú ý edge case Q2/Q3 user đã chọn]

## 📖 Thuật ngữ trong code

[Glossary cá nhân hoá: CHỈ in những thuật ngữ thực sự xuất hiện trong code lần này. Tra từ Glossary Dictionary bên dưới.]
```

---

## Glossary Dictionary (để skill tra cứu khi build output)

Khi output, scan code vừa sinh, **chỉ in** entries match những từ xuất hiện:

| Trong code | Giải thích tiếng Việt |
|---|---|
| `changedFields["X"]` | "user vừa đổi field tên X" (true/false) |
| `changedRowCells` | "danh sách các ô bảng user vừa gõ" (mảng) |
| `await` | "đợi" — đứng trước hàm cần đợi xong mới chạy tiếp |
| `$record` | "bản ghi đang sửa" — chứa giá trị các field |
| `$record.id` | "ID của bản ghi" — nếu có nghĩa là form đã lưu rồi |
| `formType` | "loại form đang mở" — `"create"` = Tạo mới, `"view"` = đã lưu (xem/sửa) |
| `$parentRecord` | "bản ghi cha" — khi form con (modal/related list) |
| `$currentPersonnel` | "nhân viên đang đăng nhập" |
| `$ref` | "bộ nhớ tạm của script" — giữ qua các lần script chạy lại trong 1 session |
| `screen.get(slug, "FORM_ITEM")` | "lấy field có slug = X" |
| `screen.get(slug, "RELATED_LIST")` | "lấy bảng (related list) có slug = X" |
| `screen.get(slug, "PATH_COMPONENT")` | "lấy Path Component có slug = X" |
| `screen.triggerButton(slug)` | "tự động bấm button có slug = X" |
| `field.value` | "giá trị của field" — đọc và ghi được |
| `field.display = false` | "ẩn field đi, không hiển thị" |
| `field.readOnly = true` | "khoá field, không cho sửa" |
| `field.required = true` | "bắt buộc nhập field này" |
| `field.limitedOptions` | "giới hạn option chọn (cho select)" |
| `rl.setData([...])` | "ghi đè toàn bộ dòng trong bảng bằng mảng record mới (theo API record shape — xem §7B cheatsheet, KHÁC SCRIPT shape của `row.get().value`)" |
| `rl.rows()` | "lấy danh sách dòng hiện có trong bảng" |
| `rl.row(i)` | "lấy dòng thứ i (0 là dòng đầu)" |
| `rl.getRow(i)` | "lấy dòng thứ i (0 là dòng đầu)" |
| `rl.getCol(slug)` | "lấy cả cột có slug = X trong bảng" — cần `await` |
| `rl.findRow(predicate)` | "tìm 1 dòng theo điều kiện" |
| `rl.submit()` | "tự động lưu bảng — không cần user bấm nút Lưu" |
| `row.get(slug)` | "lấy ô có slug = X trong dòng" |
| `col.readOnly = true` | "khoá toàn bộ ô trong cột này" |
| `col.required = true` | "bắt buộc nhập toàn bộ ô trong cột này" |
| `col.value = X` | "ghi đè toàn bộ ô hiện có trong cột bằng cùng giá trị X" — chỉ dùng khi nghiệp vụ xác nhận muốn ghi đè toàn cột; không đọc `col.value` để guard |
| `row.readOnly = true` | "khoá toàn bộ ô trong dòng này" |
| `row.required = true` | "bắt buộc nhập toàn bộ ô trong dòng này" |
| `cell.displayHtml` | "đổi cách hiển thị ô (chỉ visual, không lưu data)" |
| `filterRecords(slug, params)` | "query danh sách bản ghi từ object khác" |
| `isDirtyForm` | "form có thay đổi chưa lưu hay không" |
| `new Date()` | "ngày giờ hiện tại" |
| `logger.log(...)` | "ghi dữ liệu debug ra console" — chỉ hiện khi workspace bật chế độ nhà phát triển hoặc bật cờ ép log |
| `logger.forceShowLog` | "cờ ép hiện log" — mặc định `false`, chỉ bật tạm để debug |
| `path.submitBlocked = true` | "khoá toàn bộ nút submit của các stage trong Path Component" |
| `path.submitBlockedStages` | "danh sách stage value bị khoá nút submit; chỉ stage trong danh sách bị disabled" |

---

## Reference files

| File | Khi nào đọc |
|---|---|
| `reference/api-cheatsheet.md` | LUÔN — Bước 1 |
| `reference/safety-rules.md` | Khi vào DANGER MODE — Bước 3+5 |
| `reference/recipes.md` | Bước 5 — chọn template |
| `reference/case-studies.md` | Khi user mô tả khớp 1 case study đã có (vd "set order_line từ order") — đọc để clone pattern |

---

## Anti-patterns (CẤM)

00. 🚨 **SỬA SCRIPT LAYOUT MÀ KHÔNG LẤY SCRIPT HIỆN TẠI TRƯỚC** — CỰC KỲ NGHIÊM TRỌNG. Dùng skill `object-layout` lấy `pageSettings.script`, patch đúng phần user yêu cầu, giữ nguyên logic cũ không liên quan. Không rõ block cần sửa thì hỏi user, không đoán.
0. 🚨 **DÙNG `return` TRONG SCRIPT** — CỰC KỲ NGHIÊM TRỌNG. Script Layout Rule chạy chung 1 hàm async với các script khác user paste vào. `return` ở script này → chặn mọi logic phía dưới (kể cả script đồng nghiệp viết, script copy từ task khác). LUÔN dùng `if (positive_condition) { ... }` block. Ngoại lệ duy nhất: `continue` trong `for` loop. Xem RULE §0 đầu file.
0.5. 🚨 **SET `.value` không có `if (current !== new)` guard** — TẠO VÒNG LẶP VÔ TẬN. Re-trigger script là cơ chế built-in: mỗi lần value field/cell thay đổi → script chạy lại. Set value mà không so sánh → infinite loop → browser freeze. Áp dụng cho mọi `field.value =`, `item.value =`, `row.get(...).value =`, `cell.value =`. Xem RULE §1 đầu file.
1. **Sinh code khi chưa biết đầy đủ slug + fieldType + related list slug**. Đoán = sai. Luôn hỏi.
2. **Nhầm slug related list trong layout với slug object đích**. Phải nhắc user "slug trong layout, không phải object kia" mỗi lần hỏi.
3. **Sinh code mà chưa hỏi Q1/Q2/Q3** khi nghiệp vụ có set value. Dù user nói chi tiết, vẫn phải hỏi để confirm intent.
4. **Bỏ comment header `⚠️`** khi script có set value. User maintain sau sẽ không biết guard tại sao có.
5. **Output code thiếu test checklist**. User cần biết phải test gì.
6. **Set value field cha không kèm `if (item.value !== ...)`**. Trigger re-render loop.
7. **rl.setData không kèm `rows.length === 0`** trừ khi user chọn overwrite explicit.
8. **Dùng thuật ngữ kỹ thuật trong câu hỏi**. User non-coder. Luôn nói "khi user mở form / khi user đổi ô" thay vì "trigger", "mount", "changedFields".
9. **Sinh > 1 script trong cùng output**. 1 turn = 1 script. Nếu user mô tả 2 nghiệp vụ → hỏi tách hoặc gộp.
10. **Giữ kết quả `filterRecords` dài hạn trong `$ref`** (vd `if ($ref.products) return;`). Cách này có thể giữ dữ liệu cũ sau khi record thay đổi. Gọi `filterRecords` khi cần và dùng biến local trong cùng lần chạy. `$ref` dành cho trạng thái script như `seeded`, `submitted`, counter hoặc layout-id để chống loop.
11. **Nhầm shape `rl.setData(records)` với SCRIPT shape của `row.get().value`**. `setData` nhận **API record shape** (§7B): `date` = epoch ms number, `lookup` = `RecordItem | string | array`. `row.get().value` nhận **SCRIPT shape** (§7): `date` = `Date`, `lookup` = string ID. Đừng truyền `new Date(...)` cho field date trong setData → blank. Mặc định: nếu records lấy từ `filterRecords` → pass thẳng, KHÔNG map thủ công.
12. **Đọc nested lookup trong record từ `filterRecords()` như object đã expand**. Lookup cấp 1 có thể là object có nhiều field tuỳ object/config, nhưng lookup bên trong lookup cấp 1 chỉ là `string` ID hoặc `string[]` ID. Sai: `order.customer.owner.name`. Đúng: lấy `ownerId = order.customer.owner`, rồi `filterRecords("personnel", ...)` nếu cần tên/chức danh.
13. **Code "thông minh" khó đọc** — gom nhiều bước vào 1 expression dài, ternary lồng nhau, optional chaining sâu 4+ tầng, dùng `reduce`/`flatMap`/curry khi `for...of` đủ dùng, tạo helper function chỉ dùng 1 lần, abstract sớm (factory, hooks-style trong script), tên biến viết tắt tối nghĩa (`oid`, `c`, `x`). User non-coder sẽ không hiểu, không sửa được, hỏng business. Xem "Nguyên tắc tối thượng" đầu file.
14. **Dùng `console.log` để debug Layout Script**. Production có thể chặn log và nó không đi theo chế độ nhà phát triển của workspace. Dùng `logger.log(...)`; `logger.forceShowLog` mặc định `false` và chỉ được bật tạm khi cần ép hiện log.
15. **Không `await` hoặc không null-check `rl.getCol(...)` / `await rl.getRow(...)`**. `getCol` và `getRow` đều chờ bảng ready; sai slug hoặc row chưa load có thể trả `null`. Luôn dùng `const col = await rl.getCol("slug"); if (col) { ... }` / `if (row) { ... }`.
16. **Nghĩ `readOnly/required` ưu tiên theo API table > column > row > cell**. Sai. Related list quy về cell state và **lệnh chạy sau thắng**. Muốn mở 1 row/cell sau khi khoá bảng/cột thì đặt lệnh mở ở phía sau.
17. **Dùng `row.value = ...`**. Row không có value chung vì mỗi cell trong row có thể khác kiểu dữ liệu. Muốn set value thì set từng cell bằng `row.get("field_slug").value`.
18. **Dùng `col.value = ...` khi chưa xác nhận ghi đè toàn cột hoặc cố đọc `col.value` để guard**. Cột không có một giá trị hiện tại chung vì mỗi cell có thể khác nhau. Chỉ dùng thao tác ghi hàng loạt này khi nghiệp vụ muốn mọi cell hiện có nhận cùng giá trị; nếu không, lấy `await rl.rows()` và xử lý từng cell theo điều kiện.
19. **Nhầm `submitBlockedStages` với stage label/name**. Runtime so với `stage.value`; dùng label/name hiển thị sẽ không disabled đúng stage. Đúng: `path.submitBlockedStages = ["review"]` nếu stage value là `"review"`.
