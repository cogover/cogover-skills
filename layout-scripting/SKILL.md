---
name: layout-scripting
description: "Sinh hoặc sửa clientScript cho Layout Rule (`pageSettings.script`) của form builder Cogover từ mô tả nghiệp vụ tiếng Việt; output code paste-ready vào ô \"Cấu hình script\". Sửa script có sẵn: bắt buộc lấy script hiện tại qua $object-layout, giữ logic cũ, hỏi khi ranh giới chưa rõ. Nghiệp vụ có SET giá trị: bắt buộc decision tree 3 câu hỏi."
metadata:
  author: cogover
  version: "1.0.3"
---

# layout-scripting — sinh code Layout Rule Script

- **Phiên bản:** `1.0.3`
- **Ngày phát hành:** `2026-09-11`

Sinh JavaScript paste-ready cho `pageSettings.script` (ô "Cấu hình script") của layout Cogover từ mô tả nghiệp vụ tiếng Việt. User là non-coder: mọi rủi ro runtime (re-render loop, ghi đè data, idempotency) phải được chặn bằng guard trong code và hỏi bằng ngôn ngữ tự nhiên. Đọc/ghi `pageSettings.script` trên layout qua [$object-layout](../object-layout/SKILL.md).

Tài liệu trong skill, đọc đúng bước:

| File | Khi đọc |
|---|---|
| [references/api-cheatsheet.md](references/api-cheatsheet.md) | Luôn, Bước 1: biến global, API screen/field/related list/path component, value shape §7 và §7B, `filterRecords`, `logger` |
| [references/safety-rules.md](references/safety-rules.md) | DANGER MODE, Bước 4-6: định nghĩa Guard 1-7, combo theo Q1/Q2/Q3, banner overwrite |
| [references/recipes.md](references/recipes.md) | Bước 5: chọn template |
| [references/case-studies.md](references/case-studies.md) | Mô tả của user khớp case có sẵn (vd "set order_line từ order", "giới hạn option cột theo loại phiếu"): clone pattern |
| [references/glossary.md](references/glossary.md) | Bước 8: dựng mục "Thuật ngữ trong code" |

## Quy tắc runtime bắt buộc

### RULE §-1: lấy script hiện tại trước khi sửa

Yêu cầu sửa/thêm/thay đổi/cập nhật script của layout đã có:

1. Dùng [$object-layout](../object-layout/SKILL.md#lấy-script-đang-có-sẵn-trên-layout) view layout và đọc `data.pageSettings.script`. Rỗng/`null` → ghi nhận layout chưa có script. Có nội dung → yêu cầu của user là **patch** vào script hiện tại, không viết lại từ đầu.
2. Chưa có layout ID/slug hoặc chưa rõ layout nào → hỏi trước. Không sinh script thay thế khi chưa lấy được script hiện tại, trừ khi user xác nhận đây là script mới hoàn toàn cho layout chưa có script.
3. Bảo toàn logic cũ: chỉ thay đúng block/nhánh/field/related list/business rule được yêu cầu; không xoá, rewrite, reorder lớn hay "dọn dẹp" phần không liên quan; logic mới chèn thành block rõ ràng cạnh logic liên quan. Output là script hoàn chỉnh sau khi patch.
4. Script cũ có lỗi nghiêm trọng ngoài phạm vi (vd `return`, set `.value` không guard): báo rủi ro và hỏi user có muốn sửa luôn không; không tự sửa rộng.
5. Không xác định chắc block nào cần sửa → confirm với user trước khi output.

### RULE §0: không dùng `return`

Runtime gom mọi script Layout Rule của layout vào **cùng một hàm async**; `return` ở script này chặn mọi script user paste bên dưới (copy từ task khác, đồng nghiệp viết) không chạy. Bao logic bằng `if (điều_kiện_đúng) { ... }`; không `else { return; }`. Ngoại lệ duy nhất: `continue` trong loop (chỉ skip iteration, không thoát script).

```js
// SAI — chặn mọi logic phía dưới
if (!customerId) return;
item.value = ...;

// ĐÚNG — bao bằng if-block
if (customerId) {
    item.value = ...;
}
```

Áp cho mọi guard: `if (formType === "view") return;`, `if (!changedFields["X"]) return;`, `if (rows.length > 0) return;` đều đảo thành if-block.

### RULE §1: so sánh trước khi set `.value`

Script tự chạy lại khi bất kỳ field trên form đổi value (`changedFields[slug] = true`) hoặc bất kỳ cell related list đổi value (`changedRowCells` populate). Set value không so sánh → script tự trigger chính nó → infinite loop: browser freeze, "Maximum update depth exceeded", có thể không lộ ngay trên máy mạnh, stack trace không chỉ về script.

```js
// SAI — loop
totalItem.value = sum;

// ĐÚNG — mọi field.value, item.value, cell.value, row.get(...).value
if (totalItem.value !== sum) {
    totalItem.value = sum;
}
```

- Reset về null cũng so sánh: `if (item.value) { item.value = null; }`.
- Nhiều field → so sánh từng field. Payload object/array (vd `limitedOptions`) → so sánh shallow (`length` + `every`) rồi mới set.
- Runtime có safety net cho cell value nhưng không đủ để dựa; luôn tự guard (chi tiết: [Guard 6](references/safety-rules.md#guard-6-so-sánh-trước-khi-set-value)).

| API | Trigger re-run | Guard |
|---|---|---|
| `field.value =`, `cell.value =` | Có | Bắt buộc so sánh |
| `limitedOptions`, `display`, `readOnly`, `required`, `cell.displayHtml` | Không | Optional, so sánh để tránh re-render thừa |
| `rl.setData(...)` | Có thể | `rows.length === 0` + payload idempotent |

### RULE §1.5: related list, lệnh chạy sau thắng

Cấp state: `rl.readOnly = bool` (toàn bảng); `await rl.getCol("field_slug")` → cột (`readOnly`, `required`, `value`); `await rl.getRow(index)` → hàng (`readOnly`, `required`); `row.get("field_slug")` → cell (`readOnly`, `required`, `value`, `limitedOptions`, `displayHtml`).

- `readOnly`/`required` cuối cùng quy về từng cell. Runtime không ưu tiên table > column > row > cell mà theo **thứ tự chạy code**: lệnh sau thắng cho cell bị ảnh hưởng. Muốn mở một row/cell sau khi khoá bảng/cột → đặt lệnh mở phía sau.
- `getCol`/`getRow` là async, chờ bảng ready, có thể trả `null` (sai slug, row chưa load) → `await` + `if (col) { ... }` / `if (row) { ... }`.
- `row.value = ...` không tồn tại (mỗi cell trong row khác fieldType); set từng cell qua `row.get("field_slug").value`.
- `col.value = X` ghi đè cùng giá trị cho mọi cell hiện có trong cột (ghi hàng loạt). `col.value` không đại diện giá trị hiện tại của cột nên không dùng để guard; runtime đã chặn thay đổi cell do script form cha tạo nên không cần guard chống lặp. Chỉ dùng khi user xác nhận muốn ghi đè toàn cột; cần giữ giá trị khác nhau hoặc chỉ sửa cell thoả điều kiện → `await rl.rows()` và xử lý từng `row.get("field_slug").value`.
- `col.readOnly`/`col.required` áp cho cell hiện có và row mới phát sinh sau đó trong cột.

```js
const rl = screen.get("order_lines", "RELATED_LIST");
rl.readOnly = true;
const row = await rl.getRow(1);
if (row) {
    row.readOnly = false; // dòng index 1 mở lại vì lệnh này chạy sau
}
```

### Code cho non-coder

User sẽ tự đọc lại và sửa script. Tên biến theo nghĩa/slug (`orderId`, không `oid`, `x`); mỗi dòng một việc; `for...of` thay `reduce`/`flatMap`; không ternary lồng, optional chaining sâu, helper function hay abstract sớm; không "phòng thủ" cho case đã bị `if` bao; slug field/bảng và threshold viết thẳng string literal, không `const CONFIG`. Comment giải thích WHY cho guard hoặc pass-through không hiển nhiên (vd `// bảng còn rỗng → mới seed, tránh ghi đè data user`). Trước khi output, đọc lại với mindset non-coder: dòng nào phải đọc hai lần mới hiểu → viết lại.

## Workflow

### Bước 0: script hiện tại

Sửa/thêm/cập nhật script trên layout đã có → làm RULE §-1 trước, xác định block liên quan rồi mới thiết kế thay đổi. Chỉ bỏ qua khi user nói rõ đây là script mới hoàn toàn hoặc layout chưa có script.

### Bước 1: đọc API cheatsheet

Đọc [references/api-cheatsheet.md](references/api-cheatsheet.md) trước khi sinh code. Riêng:

- Log debug: theo mục "Debug bằng `logger`". Không sinh `console.log`; mặc định `logger.log(...)`; `logger.forceShowLog = true` chỉ bật tạm khi user cần xem log ngoài chế độ nhà phát triển và phải nói rõ cần xoá/tắt sau khi debug.
- Script dùng `filterRecords()` hoặc đọc record từ API: đọc lại mục "Record từ filterRecords + lookup expand 1 cấp". Lookup cấp 1 có thể là `RecordItem` object (`id`, `name`, field khác tuỳ object/config); lookup lồng từ cấp 2 trở đi không expand, chỉ là `string` hoặc `string[]` ID. Set vào `field.value`/`cell.value` vẫn dùng SCRIPT shape: lookup = string ID, không phải object.

### Bước 2: parse mô tả

Trích: **Target** (field/cell/related list/path component; slug nếu user nói, chưa có thì hỏi ở Bước 3), **Trigger** (mount / `changedFields` / `changedRowCells`), **Action** (set value, show/hide, readOnly, required, submit, block submit, displayHtml, fetch), **Pattern** (seed / reactive / one-shot / aggregate / validate), **nguồn fetch** (nếu dùng `filterRecords()`: field nào là lookup cấp 1, field nào là nested cấp 2 để không đọc nhầm object).

### Bước 3: hỏi technical info còn thiếu

Code cần slug và fieldType thật. Thiếu thì hỏi trước khi đi tiếp; không đoán slug; không dùng placeholder `/* SLUG */`, phải có slug thực hoặc dừng. User trả lời thiếu → hỏi lại đúng mục thiếu.

| Info | Khi nào cần |
|---|---|
| Object slug đang config layout | Luôn |
| Field slug + fieldType | Mỗi field trong mô tả (target SET, field trigger, field đọc data) |
| Related list slug **trong layout** | Nghiệp vụ đụng tới bảng |

Slug related list trong layout **khác** slug object đích: designer đặt slug riêng khi kéo bảng vào layout (layout `return_order` có bảng trỏ object `order_line` nhưng slug bảng có thể là `return_order_lines`, `lines`, ...). Script phải dùng slug trong layout; sai slug → `screen.get(..., "RELATED_LIST")` trả `null` hoặc match nhầm qua object đích nhưng override không áp → script silent fail. Khi hỏi, luôn nhấn mạnh:

> "Slug của related list **trong layout** là gì? Đây là slug designer đặt khi kéo bảng vào layout. Vào trang Sửa giao diện → click vào bảng → xem field 'slug'. KHÔNG phải slug của object kia."

Hỏi gộp một lần bằng `AskUserQuestion` (1-3 câu, mỗi câu một cụm info) hoặc text checklist:

```text
Để sinh code chính xác, cho mình biết các slug và type:
1. Object đang config layout: slug? (vd `return_order`)
2. Field "khách hàng": slug? fieldType? (vd `customer`, `lookup`)
3. Field "địa chỉ": slug? fieldType? (vd `address`, `short_text`)
4. Bảng "chi tiết đơn": slug TRONG LAYOUT? (Sửa giao diện → click bảng → field 'slug'; KHÔNG phải slug object kia)
```

### Bước 4: DANGER MODE và decision tree

Mô tả có "set", "gán", "đổi giá trị", "fill", "tự động điền", "lấy từ X đổ vào Y", "copy", "sao chép", "lấy data", "seed", "tự động lưu", "tự động submit", "khi chọn X thì set/đổi/fill Y" → DANGER MODE: mở [references/safety-rules.md](references/safety-rules.md) và hỏi decision tree; không skip dù mô tả có vẻ đầy đủ (vẫn hỏi để confirm intent). Không set value (chỉ show/hide, readOnly, highlight, hoặc `submitBlocked`/`submitBlockedStages` của Path Component) → bỏ qua, sang Bước 5.

Hỏi lần lượt bằng `AskUserQuestion`; option phải có ví dụ cụ thể tiếng Việt, nói "khi user mở form / khi user đổi ô" thay vì "trigger", "mount", "changedFields".

**Q1, header "Khi nào chạy":** "Script này nên chạy khi nào?"
1. "Khi user vừa mở form" — cứ mở form ra là chạy, dù form mới hay đã lưu.
2. "Khi user mới tạo bản ghi" — chỉ chạy ở trang Tạo mới, không chạy khi vào form đã lưu để xem/sửa.
3. "Khi user đổi 1 ô cụ thể" — vd đổi ô 'Khách hàng' → tự fill địa chỉ (hỏi tên ô ở câu sau).
4. "Khi user gõ vào ô trong bảng" — vd gõ ô 'Tên SP' trong dòng → tự fill ô 'Giá' cùng dòng.

**Q2, header "Mở form đã lưu"** (chỉ khi Q1 = 1): "Khi user mở lại form đã lưu trước đó để xem/sửa, script có cần chạy lại không?"
1. "KHÔNG cần chạy lại (an toàn nhất)" — vd form Return Order đã lưu, mở ra xem → không tự seed lại order_lines, giữ nguyên data đã lưu.
2. "Có cần chạy lại" — cảnh báo: chỉ chọn khi chắc chắn muốn ghi đè, có thể xoá thay đổi user đã làm.

**Q3, header "Ghi đè data":** "Trước khi script đổi giá trị, ô hoặc bảng đích có thể đã có sẵn data user nhập không?"
1. "Có thể có — KHÔNG được ghi đè" — vd bảng order_lines có dòng user tự thêm, script không được xoá.
2. "Chắc chắn rỗng — overwrite được" — vd field tự động luôn rỗng lúc đầu, fill vào không vấn đề.
3. "Luôn overwrite" — cảnh báo: sẽ xoá data user nhập tay nếu có; chỉ chọn khi business yêu cầu reset.

**Q4** (chỉ khi Q1 = 3 hoặc 4 và user chưa cho slug; hỏi text, không `AskUserQuestion`): Q1 = 3 → slug field user đổi (vd `order`, `customer`); Q1 = 4 → slug bảng + slug ô (vd bảng `order_lines`, ô `product`).

### Bước 5: map answer thành recipe + guard

Chọn recipe trong [references/recipes.md](references/recipes.md); áp guard theo bảng dưới (định nghĩa Guard 1-7 và combo mẫu: [references/safety-rules.md](references/safety-rules.md)). Mọi guard là if-block bao logic (RULE §0).

| Q1 | Q2 | Q3 | Guard wrapper |
|---|---|---|---|
| 1 mọi lần mở | 1 không re-seed | 1 không overwrite | `if (formType !== "view") { if (rows.length === 0) { ... } }` (+ optional `$ref.seeded`) |
| 1 mọi lần mở | 1 không re-seed | 2 chắc chắn rỗng | `if (formType !== "view") { ... }` |
| 1 mọi lần mở | 2 có re-seed | 3 luôn overwrite | Banner cảnh báo, chạy thẳng không guard |
| 2 chỉ tạo mới | – | 1 không overwrite | `if (formType !== "view") { if (rows.length === 0) { ... } }` |
| 2 chỉ tạo mới | – | 2 chắc chắn rỗng | `if (formType !== "view") { ... }` |
| 3 user đổi field X | – | 1 không overwrite | `if (changedFields["X"]) { if (!target.value) { ... } }` |
| 3 user đổi field X | – | 2 chắc chắn rỗng | `if (changedFields["X"]) { ... }` |
| 3 user đổi field X | – | 3 luôn overwrite | `if (changedFields["X"]) { ... }` + banner |
| 4 user gõ cell | – | bất kỳ | `for (const c of changedRowCells \|\| []) { if (c.relatedListSlug === "X" && c.fieldSlug === "Y") { ... } }`; `continue` chỉ khi loop body nhiều bước |

### Bước 6: sinh code

- Mọi set `.value` kèm so sánh (RULE §1). Mọi `rl.setData(...)` nằm trong `if (existingRows.length === 0) { ... }` trừ khi Q3 = 3.
- Nghiệp vụ phức hợp = đặt các block recipe cạnh nhau, không `return` giữa các block. Một lượt output một script; user mô tả hai nghiệp vụ → hỏi tách hay gộp.
- DANGER MODE → prepend header (bắt buộc; đây là thứ user đọc đầu tiên khi mở lại script):

```js
/**
 * ⚠️ SCRIPT NÀY THAY ĐỔI DỮ LIỆU FORM TỰ ĐỘNG
 *
 * Chạy khi: <Q1>
 * KHÔNG chạy khi: <Q2>
 * KHÔNG ghi đè: <Q3>
 *
 * Nếu sửa script này, GIỮ NGUYÊN các điều kiện `if (...)` bao quanh logic.
 * KHÔNG thêm `return` — script nằm chung 1 hàm với các script khác, `return` sẽ chặn chúng.
 */
```

- Q3 = 3 → dùng [banner overwrite](references/safety-rules.md#banner-cho-overwrite-mode) thay header trên.

### Bước 7: verify checklist

Tự kiểm trước khi output; lỗi → sửa tại chỗ, không output code chưa pass. Sai mục 1, 2 hoặc 3 = loại toàn bộ code.

1. Không có `return` ở bất kỳ đâu, kể cả trong if-else (grep code vừa sinh); ngoại lệ chỉ `continue` trong `for`.
2. Sửa layout có sẵn: đã lấy `pageSettings.script` qua `$object-layout`; logic cũ không liên quan còn nguyên. Chưa lấy được hoặc không rõ block cần sửa → hỏi user, không output script thay thế.
3. Mọi dòng `.value =` (`field`, `item`, `cell`, `row.get(...)`) có `if (current !== new)` ngay trên; set `null` cũng `if (item.value) { item.value = null; }`.
4. `await` cho `rl.row/rows/getRow/getCol/findRow/submit/filterRecords`.
5. Value set vào `field.value`/`row.get(slug).value` đúng SCRIPT shape §7: date → `Date`, time → ms, range → `{ gte, lte }`, lookup → string ID (không `{ id, ... }`).
6. `rl.setData(records)` đúng API record shape §7B: date → epoch ms number (không `Date`), lookup nhận `RecordItem | string | array`. Records từ `filterRecords` → pass thẳng, không map thủ công. Không nhầm hai shape.
7. Set bảng có `if (rows.length === 0) { rl.setData(...) }` trừ khi user chọn overwrite; payload setData idempotent (cùng input → cùng output).
8. `await rl.getCol(...)`/`await rl.getRow(...)` có null-check; `readOnly`/`required` đặt đúng thứ tự "lệnh sau thắng"; không có `row.value = ...`; `col.value = ...` chỉ khi user đã xác nhận ghi đè toàn cột và không đọc `col.value` để guard.
9. Guard wrapper đúng bảng Bước 5 (if-block, không `if (...) return;`).
10. Không lưu kết quả `filterRecords` dài hạn vào `$ref` (vd `if ($ref.products) ...`) vì record có thể đổi; tái sử dụng bằng biến local trong cùng lần chạy. `$ref` chỉ giữ state script: `seeded`, `submitted`, counter, layout-id chống loop.
11. Đọc lookup trong record từ `filterRecords()` đúng rule expand 1 cấp: không `record.customer.owner.name`; lấy `ownerId = record.customer.owner` rồi `filterRecords("personnel", ...)` nếu cần.
12. Code đọc được với non-coder (mục "Code cho non-coder").
13. Không dùng `screen.changeLayout(...)`: API chuyển layout không được phép trong output của skill này.
14. `screen.triggerButton(...)` có guard chống loop nếu button có thể kích hoạt lại script.
15. Log dùng `logger.log(...)`, không `console.log`; có `logger.forceShowLog = true` thì ghi rõ là cờ tạm, cần xoá/tắt sau khi debug.
16. `submitBlockedStages` chứa `stage.value`, không phải label/name hiển thị (vd `["review"]` khi stage value là `"review"`).

### Bước 8: output

Bốn phần bắt buộc:

```markdown
## Code
[code block JavaScript đầy đủ — paste vào ô Cấu hình script]

## Script này làm gì
[3-5 dòng tiếng Việt thân thiện: chạy khi nào, kiểm tra gì, đổi gì, bảo vệ data user thế nào]

## 🧪 Bắt buộc test trước khi đưa lên production
1. [test case 1 cụ thể theo nghiệp vụ]
2. [test case 2]
3. [test case 3]
4. [test case 4: edge case theo Q2/Q3 user đã chọn]

## 📖 Thuật ngữ trong code
[chỉ các thuật ngữ thực sự xuất hiện trong code lần này, giải thích theo references/glossary.md]
```
