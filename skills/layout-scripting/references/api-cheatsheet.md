# API Cheatsheet — Layout Rule Script

Knowledge base bắt buộc khi sinh code cho Layout Rule Script.

## 1. Biến global (sẵn có, không khai báo)

| Biến | Kiểu | Mô tả |
|---|---|---|
| `screen` | object | Snapshot màn hình hiện tại |
| `initScreen` | object | Snapshot lúc load lần đầu |
| `$record` | object | Field slug → value của bản ghi đang sửa. **`$record.id`** có → form đã lưu |
| `$parentRecord` | object | Bản ghi cha (khi form con) |
| `$currentPersonnel` | object | User đang đăng nhập |
| `changedFields` | object | `{ slug: true }` cho field user vừa đổi |
| `changedRowCells` | array | `[{ relatedListSlug, rowIndex, recordId, fieldSlug, newValue }, ...]`. `newValue` đã được convert sang SCRIPT shape — đồng nhất với `row.get(slug).value` / `$record.X` (vd lookup single → string ID, date → Date, time → ms). |
| `isDirtyForm` | boolean | Form có thay đổi chưa lưu |
| `locale` | string | `vi`, `en`, ... |
| `$ref` | object | Bộ nhớ tạm script — giữ qua các lần exec trong cùng instance |
| `formType` | `"view" \| "create"` | Auto compute: `"view"` nếu `$record.id` có, `"create"` nếu không. Dùng gate logic theo mode. |
| `filterRecords(slug, params)` | async fn | Query record từ object khác |
| `logger` | object | Logger dành cho Layout Script: `logger.log(...)`, `logger.forceShowLog` |

### Debug bằng `logger` (không dùng `console.log`)

```js
logger.log("[order-layout] input", {
    changedFields,
    orderId: $record.order,
});
```

- `logger.log(...data)` chỉ hiện trên console khi workspace bật chế độ nhà phát triển.
- `logger.forceShowLog` mặc định là `false`. Chỉ bật tạm khi cần debug ở workspace không bật chế độ nhà phát triển:

```js
logger.forceShowLog = true;
logger.log("[order-layout] forced debug", $record);
```

- Giá trị `forceShowLog` được giữ qua các lần script chạy lại trong cùng form. Sau khi debug, xoá dòng bật cờ hoặc gán lại `false` để tránh lộ log không cần thiết.
- Dùng nhãn ổn định như `[object-layout]` và log dữ liệu đầu vào/kết quả quanh nhánh nghi ngờ. Không log token, credential hoặc dữ liệu nhạy cảm.
- Không dùng `console.log`: môi trường production có thể chặn nó, còn `logger.log` dùng đúng cơ chế debug của Layout Script.

## 2. screen.get(slug, type)

```js
screen.get("name", "FORM_ITEM")      // 1 field
screen.get("items", "RELATED_LIST")  // 1 bảng
screen.get("section_1", "SECTION")   // container
screen.get("sales_path", "PATH_COMPONENT") // 1 path component
```

Type khác: `ROW`, `COLUMN`, `GROUP`, `DISPLAY_BOX`, `BUTTON`, `BUTTON_GROUP`, `PATH_COMPONENT`, `TAB`.

Action:
```js
screen.triggerButton(buttonSlug, requiredFlag);
```

## 2B. Path Component

| Property | R/W | Mô tả |
|---|---|---|
| `slug` | R | |
| `display` | R/W | true=hiện, false=ẩn path component |
| `submitBlocked` | R/W | true=disable toàn bộ nút submit của các stage trong path này |
| `submitBlockedStages` | R/W | mảng `stage.value`; chỉ disable nút submit của các stage có value trong mảng |

```js
const path = screen.get("sales_path", "PATH_COMPONENT");

// Block toàn bộ nút submit của path
if (path.submitBlocked !== true) {
    path.submitBlocked = true;
}

// Chỉ block nút submit của stage "review"
const blockedStages = ["review"];
const currentBlockedStages = path.submitBlockedStages || [];
const sameStages =
    currentBlockedStages.length === blockedStages.length &&
    currentBlockedStages.every((stage, index) => stage === blockedStages[index]);

if (!sameStages) {
    path.submitBlockedStages = blockedStages;
}
```

Lưu ý:
1. `submitBlocked = true` block toàn bộ stage, không cần quan tâm `submitBlockedStages`.
2. `submitBlockedStages` so với `stage.value`, không phải label/name hiển thị.
3. API này chỉ disabled nút submit, chưa render message.

## 3. Form Item (field)

| Property | R/W | Mô tả |
|---|---|---|
| `slug` | R | |
| `display` | R/W | true=hiện, false=ẩn |
| `readOnly` | R/W | true=khoá |
| `required` | R/W | true=bắt buộc |
| `value` | R/W | giá trị (SCRIPT shape, xem §6) |
| `limitedOptions` | R/W | mảng option cho select |

## 4. Container (row/column/section/...)

| Property | R/W |
|---|---|
| `slug`, `display` | R/`display` cũng R/W |

## 5. Related List

| API | Sync/Async | Mô tả |
|---|---|---|
| `rl.display = bool` | sync | hiện/ẩn bảng |
| `rl.readOnly = bool` | sync | khoá bảng |
| `rl.creatableNewRecord = bool` | sync | cho thêm dòng mới |
| `rl.setData(records)` | sync | thay toàn bộ dòng (id tự gen nếu không truyền) |
| `await rl.rows()` | async | snapshot all rows `[{ rowIndex, recordId, get(slug) }]` |
| `await rl.row(i)` | async | row index i hoặc null |
| `await rl.getRow(i)` | async | alias lấy row index i hoặc null; PHẢI `await` + null-check |
| `await rl.getCol(slug)` | async | đợi bảng ready rồi lấy cột theo field slug hoặc null; PHẢI `await` + null-check |
| `await rl.findRow(pred)` | async | tìm theo predicate |
| `await rl.submit()` | async | tự lưu bảng (batchCreate + batchUpdate + handleDelete) |

### Related list bulk state: table/column/row/cell

`readOnly` và `required` ở cấp bảng/cột/hàng đều được runtime áp xuống từng cell. **Không có ưu tiên cứng theo API. Lệnh chạy sau thắng cho cell bị ảnh hưởng.**

```js
const rl = screen.get("order_lines", "RELATED_LIST");
rl.readOnly = true;

const row = await rl.getRow(1);
if (row) {
    row.readOnly = false;  // dòng index 1 mở lại vì lệnh này chạy sau
}
```

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

| API | Mô tả |
|---|---|
| `col.readOnly = bool` | set readOnly cho toàn bộ cell trong cột, gồm row mới phát sinh sau đó |
| `col.required = bool` | set required cho toàn bộ cell trong cột, gồm row mới phát sinh sau đó |
| `col.value = value` | ghi đè cùng value cho toàn bộ cell hiện có trong cột; value phải đúng SCRIPT shape |
| `row.readOnly = bool` | set readOnly cho toàn bộ cell trong hàng hiện tại |
| `row.required = bool` | set required cho toàn bộ cell trong hàng hiện tại |

> `rl.getCol("bad_slug")` trả `null`. `await rl.getRow(index)` có thể trả `null`. Luôn bao bằng `if (col) { ... }` / `if (row) { ... }`.
>
> `row.value = ...` KHÔNG tồn tại vì một hàng có nhiều cell khác fieldType. Muốn set value thì dùng `row.get("field_slug").value`.
>
> `col.value` KHÔNG phải giá trị hiện tại chung của cột và không dùng để guard. `col.value = X` là thao tác ghi hàng loạt: runtime ghi đè mọi cell hiện có trong cột bằng `X` và đã chặn thay đổi cell do script form cha tự tạo, nên không cần guard chống lặp kiểu `if (col.value !== X)`. Chỉ dùng khi nghiệp vụ xác nhận muốn ghi đè toàn cột. Nếu cần giữ giá trị khác nhau hoặc chỉ sửa cell phù hợp điều kiện, dùng `await rl.rows()` rồi kiểm tra từng cell.

## 6. Cell (row.get(slug))

Cell có **đủ các key của FORM_ITEM trừ `display`**, cộng key mở rộng `displayHtml`:

| Property | R/W |
|---|---|
| `slug` | R |
| `value` | R/W (SCRIPT shape) |
| `readOnly` | R/W |
| `required` | R/W |
| `limitedOptions` | R/W (giới hạn option `single_choice`/`lookup` của ô — mảng **slug option** cho single_choice, mảng **record ID** cho lookup). KHÔNG trigger re-run script. |
| `displayHtml` | R/W (cosmetic only — sanitize DOMPurify) |

> ⚠️ **`display` KHÔNG có ở cell** (không ẩn được từng ô trong bảng). Các key còn lại giống FORM_ITEM.
>
> Ví dụ giới hạn option `single_choice` của 1 cột trong bảng (chạy ở script form CHA):
> ```js
> const rl = screen.get("<RL_SLUG_TRONG_LAYOUT>", "RELATED_LIST");
> const rows = await rl.rows();
> for (const row of rows) {
>     row.get("<cell_slug>").limitedOptions = ["opt_a", "opt_b"];  // slug option
> }
> ```
> 🚨 **Slug related list TRONG LAYOUT ≠ slug object đích** (vd object `cash_transaction_apply` nhưng related list trong layout là `cash_transaction_applies`). Dùng sai slug → override key sai → không áp. Soi slug đúng bằng `screen.relatedLists.map((r) => r.slug)`.

## 7. Value shape theo fieldType (CRITICAL)

> ⚠️ **2 SHAPE KHÁC NHAU** — đừng nhầm:
> - **§7 dưới đây = SCRIPT shape** (cho `row.get(slug).value`, `field.value`, `$record.X`, `changedRowCells[i].newValue`, `screen.formItems[i].value`).
> - **§7B = API record shape** (cho `rl.setData(records)`). Khác hẳn — vd `date` cần `number` (epoch ms) thay vì `Date`, `lookup` chấp nhận cả object/string/array.

### Single (multiple=false)

| fieldType | Shape |
|---|---|
| `short_text`, `long_text`, `email`, `regex`, `phone`, `url` | `string` |
| `number`, `percent`, `currency`, `duration`, `auto_number` | `number` |
| `boolean` | `boolean` |
| `single_choice`, `radio_button` | `string` (slug của option) |
| `date`, `date_time` | `Date \| null` — dùng `new Date(...)` |
| `time` | `number \| null` — milliseconds từ 00:00. VD 09:30 = `(9*60+30)*60*1000` |
| `date_range`, `date_time_range` | `{ gte: Date \| null, lte: Date \| null }` |
| `time_range` | `{ gte: number \| null, lte: number \| null }` |
| `lookup_normal`, `reference`, `embedded`, `children` | **`string`** (chỉ ID của record, KHÔNG phải object) |
| `label`, `cascading` | `string` (slug/value) |
| `file` | `UploadFile` object (RHF array item đầu) |
| `lookup_parent`, `lookup_peer2peer`, `link` | RHF raw (fallthrough — hiếm dùng trong script) |
| `formula`, `rollup_summary` | string/number (read-only) |

### Multi (multiple=true)

| fieldType | Shape |
|---|---|
| text/number family (`short_text`, `number`, `email`, `phone`, `url`, ...) | `string[]` / `number[]` |
| `boolean` | `boolean[]` |
| `multi_choices`, `checkbox` | `string[]` |
| `date`, `date_time` | `(Date \| null)[]` |
| `time` | `(number \| null)[]` |
| `lookup_normal`, `reference`, `embedded`, `children` | **`string[]`** (mảng ID, KHÔNG phải mảng object) |
| `label`, `cascading` | `string[]` |
| `file` | `UploadFile[]` |

### ⚠️ Quan trọng — lookup KHÔNG có .name / .displayFields

Lookup field trong script value chỉ là **ID string**. Để đọc field khác của record được link, phải `filterRecords()` fetch lại:

```js
// SAI — $record.customer là string, không có .defaultAddress
const addr = $record.customer?.defaultAddress;   // → undefined

// ĐÚNG — fetch record bằng filterRecords
const customerId = $record.customer;
if (customerId) {
    const { records } = await filterRecords("customer", {
        filterItems: [{ field: "id", op: "=", params: [customerId] }],
        limit: 1,
    });
    const addr = records[0]?.defaultAddress ?? "";
}
```

### Sai shape = render blank
```js
// SAI
row.get("date").value = "2026-05-26";              // → blank
row.get("time").value = "09:30";                   // → blank
row.get("lookup_field").value = { id: "abc-id" };  // → blank (chờ string)

// ĐÚNG
row.get("date").value = new Date("2026-05-26");
row.get("time").value = (9 * 60 + 30) * 60 * 1000;
row.get("lookup_field").value = "abc-id";          // chỉ cần ID string
```

## 7B. Value shape cho `rl.setData(records)` (KHÁC §7)

`rl.setData(records: RecordItem[])` chạy qua converter **API record shape → RHF shape**, KHÔNG dùng SCRIPT shape của §7. Mỗi record có dạng `{ id: string, [fieldSlug]: <API-shape-value> }`.

### Single (multiple=false)

| fieldType | Shape cho `record[slug]` trong setData | Lưu ý |
|---|---|---|
| `short_text`, `email`, `regex`, `label` | `string` | |
| `phone` | `string` | converter auto thêm `+` nếu thiếu |
| `name` (system) | `string` | |
| `long_text` | `{ value: string, text_type: 1 \| 2 }` hoặc plain `string` (legacy) | |
| `numeric`, `decimal`, `currency`, `auto_number` | `number` | |
| `percent` | `number` **ratio** (0.75 = 75%) — KHÔNG nhân 100 sẵn | converter sẽ x100 nếu `hasMulPercentValue=true` |
| `boolean`, `checkbox` (single) | `boolean` hoặc truthy/falsy (coerce `!!`) | |
| `single_choice`, `radio_button` | `string` (slug option) | |
| `date` | **`number` (epoch ms)** — vd `1776145500000`. ⚠️ ISO string `"2026-04-15"` → blank (default `convertDateToUTC=false`) | KHÁC §7 |
| `date_time` | **`number` (epoch ms)** | |
| `time` | `number` (ms-of-day từ 00:00) | giống §7 |
| `time_duration` | `number` (tổng ms) | |
| `date_range`, `date_time_range` | `{ gte, lte, start, end }` epoch ms (gte/start, lte/end fallback) | KHÁC §7 |
| `time_range` | `{ gte, lte, start, end }` ms-of-day | |
| `url` | `{ url: string, alias: string }` hoặc plain `string` (auto wrap) | |
| `lookup_normal`, `reference`, `embedded`, `children` | **`RecordItem` (object có `.id`) HOẶC `string` (id thẳng) HOẶC array của 2 dạng** | converter tự extract `.id` |
| `cascading` | `string[]` (luôn array, kể cả single = 1 leaf) | |
| `file` | object metadata `{ fileName, file_id, fileExt, url, ... }` (xem RULE-RECORD-06) | |
| `rating` | `number` | |
| `data_table` | `array` hoặc JSON string | |
| `formula`, `rollup_summary` | (read-only, BE tự compute) | bỏ qua khi setData |

### Multi (multiple=true)

| fieldType | Shape |
|---|---|
| text/number family (`short_text`, `email`, `phone`, `numeric`, ...) | mảng raw `string[]` / `number[]` (converter wrap mỗi item thành `[{data: ...}]` cho RHF) |
| `multi_choices`, `checkbox` | `string[]` (slug) |
| `date`, `date_time` | **`number[]`** (epoch ms array) |
| `time` | `number[]` (ms-of-day array) |
| `lookup_normal`, `reference`, `embedded`, `children` | mảng — mỗi item `RecordItem \| string` |
| `label` | `string[]` |
| `file` | array các object metadata |

### Ví dụ paste-ready

```js
// records từ filterRecords → API shape sẵn → pass thẳng cho setData, không map gì
const { records } = await filterRecords("order_line", {
    filterItems: [{ field: "order", op: "=", params: [orderId] }],
    limit: 500,
});
rl.setData(records);   // ✅ works — converter handle mọi field types

// Hoặc build record thủ công
rl.setData([
    {
        id: "tmp-1",                        // id required theo TS, runtime sẽ override bằng UUID
        product: "prod-uuid-1",             // lookup: pass string ID
        quantity: 5,
        price: 100000,
        delivery_date: 1776145500000,       // date: EPOCH MS (KHÔNG phải Date object)
        delivery_time: (14 * 60 + 30) * 60 * 1000,  // time: ms-of-day
        is_priority: true,
        tags: ["urgent", "fragile"],        // multi_choices: string[]
    },
]);
```

### Sai shape phổ biến

```js
// SAI — Date object cho date field qua setData
rl.setData([{ id: "tmp", delivery_date: new Date("2026-05-30") }]);
// → converter Number(Date object) = NaN → null → blank

// SAI — ISO string "YYYY-MM-DD" cho date
rl.setData([{ id: "tmp", delivery_date: "2026-05-30" }]);
// → Number("2026-05-30") = NaN → blank (vì convertDateToUTC=false default)

// ĐÚNG
rl.setData([{ id: "tmp", delivery_date: new Date("2026-05-30").getTime() }]);
// hoặc dayjs("2026-05-30").valueOf()
```

## 8. filterRecords

```js
const { records, total, meta } = await filterRecords("product", {
    filterItems: [
        { field: "status", op: "=", params: ["active"] },
        { field: "price", op: ">", params: [100000] },
    ],
    limit: 20,
});
```

### 🚨 Record từ filterRecords + lookup expand 1 cấp (CRITICAL)

Mỗi item trong `records` là **API record shape**: `{ id: string, [fieldSlug]: value }`.

Khi record có field lookup:

1. **Lookup cấp 1** có thể là:
   - `string` ID
   - `string[]` ID nếu multiple
   - `RecordItem` object có `.id`, `.name` và các field khác tuỳ cấu hình/object
   - `RecordItem[]` nếu multiple
2. **Lookup lồng trong lookup cấp 1 (cấp 2 trở đi) KHÔNG expand object nữa**:
   - Chỉ là `string` ID hoặc `string[]` ID
   - KHÔNG có `.name`
   - KHÔNG có field con của object đó

Ví dụ `filterRecords("order", ...)` trả về `order.customer` là lookup cấp 1:

```js
const order = records[0];

// Có thể đúng: customer là object cấp 1 đã expand
const customer = order.customer;
const customerId = typeof customer === "string" ? customer : customer?.id;
const customerName = typeof customer === "string" ? "" : customer?.name ?? "";

// CỰC KỲ QUAN TRỌNG:
// Nếu customer.owner cũng là lookup field, owner chỉ là ID string/string[].
// Server không expand tiếp thành { id, name, ... } ở cấp 2.
const ownerId = typeof customer === "string" ? "" : customer?.owner;
```

Sai phổ biến:

```js
// ❌ SAI — owner là nested lookup cấp 2, chỉ là ID string/string[]
const ownerName = order.customer.owner.name;
```

Đúng:

```js
const customer = order.customer;
const ownerId = typeof customer === "string" ? "" : customer?.owner;

if (ownerId && typeof ownerId === "string") {
    const { records: owners } = await filterRecords("personnel", {
        filterItems: [{ field: "id", op: "=", params: [ownerId] }],
        limit: 1,
    });
    const ownerName = owners[0]?.name ?? "";
}
```

Khi set ngược vào `field.value` / `cell.value`, vẫn dùng **SCRIPT shape** ở §7:

```js
const customerItem = screen.get("customer", "FORM_ITEM");
const customer = order.customer;
const customerId = typeof customer === "string" ? customer : customer?.id;
if (customerItem.value !== customerId) {
    customerItem.value = customerId; // lookup field.value cần string ID, KHÔNG phải object
}
```

> `filterRecords` quản lý việc lấy dữ liệu và cache của nó. Không phụ thuộc vào thời hạn cache hoặc giả định gọi lại cùng params luôn tránh được request mạng; kết quả phụ thuộc trạng thái dữ liệu của phiên làm việc.
>
> Không lưu kết quả API dài hạn vào `$ref` khi chưa có cơ chế làm mới: dữ liệu có thể cũ sau khi record thay đổi. Gọi `filterRecords` khi cần dữ liệu; dùng biến local để tái sử dụng kết quả trong cùng lần chạy.

## 13. Anti-patterns

| Anti-pattern | Vì sao sai | Đúng |
|---|---|---|
| Lưu kết quả `filterRecords` dài hạn trong `$ref` | Không tự phản ánh record thay đổi, có thể giữ dữ liệu cũ. | Gọi `filterRecords` khi cần; tái sử dụng biến local trong cùng lần chạy. |
| SET field cha không so sánh `if (item.value !== ...)` | Trigger re-render loop vì value changed → script re-run → set lại. | Luôn so sánh trước khi set. |
| `rl.setData(...)` không check `existingRows.length === 0` | Ghi đè data user nhập tay. | Guard bằng `if (existingRows.length === 0) { ... }` trừ khi business yêu cầu overwrite. |
| Đọc `$record.<lookup>.<field>` để lấy data record được link | `$record.<lookup>` là string ID, không có `.field`. | `filterRecords(objectSlug, { filterItems: [{ field: "id", op: "=", params: [id] }] })`. |
| Đọc nested lookup từ record `filterRecords()` như object expand nhiều cấp | Server chỉ expand lookup cấp 1; nested lookup cấp 2 trở đi là `string`/`string[]` ID. | Lấy ID nested lookup rồi gọi `filterRecords()` tiếp nếu cần field của record đó. |
| Dùng `c.newValue` mà nghĩ là RHF raw | Đã convert SCRIPT shape (từ SPT-2033). Cùng shape với `row.get(slug).value`. | Tin tưởng dùng thẳng. |
| Quên `await` cho `rl.row/rows/getRow/getCol/findRow/submit/filterRecords` | Nhận Promise thay vì kết quả → mọi check sau đó sai. | Luôn `await`. |
| Không `await`/null-check `rl.getCol(...)` hoặc không null-check `await rl.getRow(...)` | Bảng chưa ready, sai slug hoặc row không tồn tại có thể trả `null`; thiếu `await` sẽ nhận Promise thay vì cột. | `const col = await rl.getCol("product"); if (col) { ... }` |
| Nghĩ table/column/row/cell readOnly có ưu tiên cứng | Runtime quy về cell state, lệnh chạy sau thắng. | Đặt override cụ thể ở sau override rộng. |
| Dùng `row.value = ...` | Row không có value chung vì các cell khác fieldType. | Set từng cell: `row.get("field_slug").value = ...` |
| Đọc `col.value` để guard hoặc dùng `col.value = ...` khi cần giữ giá trị khác nhau giữa các dòng | Cột không có một giá trị hiện tại chung; phép gán sẽ ghi đè mọi cell hiện có. | Chỉ dùng khi xác nhận muốn ghi đè toàn cột; nếu không, lấy `await rl.rows()` và xử lý từng cell. |
| Dùng `console.log` để debug Layout Script | Production có thể chặn log và không tuân theo chế độ nhà phát triển của workspace. | Dùng `logger.log`; chỉ bật tạm `logger.forceShowLog = true` khi thật sự cần. |

## 9. Async detection

Script tự wrap async nếu chứa `await`. **Dùng `await` cho mọi `rl.row/rows/getRow/getCol/findRow/submit/filterRecords`** — không sẽ nhận `Promise` thay vì kết quả.

## 10. Re-run trigger

Script chạy lại khi:
- Field cha thay đổi (`changedFields[slug]` = true)
- Cell related list thay đổi (`changedRowCells` buffer)
- Layout id đổi

Debounce 50ms — multiple changes liên tiếp → 1 exec.

## 11. Loop guard

Khi script form cha SET giá trị cell qua API, runtime chặn thay đổi cell do chính lần chạy đó tạo ra để tránh tự kích hoạt lại. Vì vậy `col.value = X` không cần guard chống lặp; rủi ro cần xác nhận là ghi đè toàn bộ cell hiện có. SET field cha vẫn có thể kích hoạt chạy lại nếu giá trị mới khác giá trị cũ — phải tự kiểm tra `if (item.value !== newValue)` trong code.

## 12. waitReady timeout

`rl.rows/row/getRow/getCol/findRow/submit` đợi bảng mount + load. Timeout 10s → trả `null`/`[]` hoặc kết thúc `submit` mà không lưu. Script vẫn tiếp tục, nhưng kết quả không có. Bao logic phía sau bằng `if (row) { ... }` / `if (col) { ... }` sau mỗi await, KHÔNG dùng early return.
