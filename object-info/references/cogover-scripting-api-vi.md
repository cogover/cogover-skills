# Cogover Scripting - API Reference

> Tài liệu tham chiếu đầy đủ cho Cogover Scripting Engine.

---

## Mục lục

1. [Giới thiệu](#1-giới-thiệu)
2. [Các loại dữ liệu](#2-các-loại-dữ-liệu)
3. [Toán tử](#3-toán-tử)
4. [Cú pháp sử dụng](#4-cú-pháp-sử-dụng)
5. [Hàm Text](#5-hàm-text)
6. [Hàm Number & Math](#6-hàm-number--math)
7. [Hàm Date](#7-hàm-date)
8. [Hàm Datetime](#8-hàm-datetime)
9. [Hàm DateRange & DatetimeRange](#9-hàm-daterange--datetimerange)
10. [Hàm JSON](#10-hàm-json)
11. [Hàm SelectList](#11-hàm-selectlist)
12. [Array, List & Map](#12-array-list--map)
13. [Hàm Workspace](#13-hàm-workspace)
14. [Giới hạn & An toàn](#14-giới-hạn--an-toàn)
15. [Công thức mẫu](#15-công-thức-mẫu-recipes)

---

## 1. Giới thiệu

Cogover Scripting là ngôn ngữ kịch bản cho phép viết các công thức tính toán, xử lý dữ liệu và logic nghiệp vụ. Ngôn ngữ hỗ trợ các kiểu dữ liệu phong phú bao gồm Text, Number, Date, Datetime, JSON, SelectList cùng với các cấu trúc điều khiển như vòng lặp và điều kiện.

---

## 2. Các loại dữ liệu

### 2.1. Kiểu cơ bản

| Kiểu | Mô tả | Ví dụ |
|------|--------|-------|
| **Number** | Số nguyên hoặc số thực | `42`, `3.14`, `-100` |
| **Text (String)** | Chuỗi ký tự, đặt trong dấu nháy đơn hoặc nháy kép | `"Hello"`, `'World'` |
| **Boolean** | Giá trị logic đúng/sai | `true`, `false` |
| **null** | Giá trị rỗng | `null` |

**Quy tắc chuyển đổi sang Boolean:**

| Kiểu gốc | Giá trị `false` | Giá trị `true` |
|-----------|-----------------|-----------------|
| Text | `""` (chuỗi rỗng), `null` | Các chuỗi khác |
| Number | `0` | Các số khác 0 |

### 2.2. Kiểu tập hợp

#### Array (Mảng cố định)

Khai báo **không có** dấu phẩy ở cuối. Kích thước cố định, không thể thêm/xóa phần tử.

```javascript
var array1 = ["A", 10.1, "C"];
```

#### List (Danh sách động)

Khai báo **có dấu phẩy và `...`** ở cuối. Có thể thêm/xóa phần tử.

```javascript
var list1 = ["A", 10.1, "C", "D",...];
```

#### Map (Bảng key-value)

```javascript
var map1 = {
    "name": "Nguyen Van A",
    "age": 30,
    "tags": ["vip", "active"]
};
```

### 2.3. Kiểu đặc biệt

| Kiểu | Mô tả | Cách tạo |
|------|--------|----------|
| **Date** | Ngày (không có giờ) | `Date.today()`, `Date.date(2024, 3, 15)` |
| **Datetime** | Ngày và giờ (có timezone) | `Datetime.now()`, `Datetime.valueOf("2024-03-15 10:00:00")` |
| **DateRange** | Khoảng ngày (bắt đầu - kết thúc) | `DateRange.of(startDate, endDate)` |
| **DatetimeRange** | Khoảng ngày giờ | `DatetimeRange.of(startDatetime, endDatetime)` |
| **SelectList** | Danh sách lựa chọn | `SelectedList.create()` |

---

## 3. Toán tử

### 3.1. Toán tử số học

| Toán tử | Mô tả | Ví dụ | Kết quả |
|---------|--------|-------|---------|
| `+` | Cộng / Nối chuỗi | `10 + 5` | `15` |
| `-` | Trừ | `10 - 5` | `5` |
| `*` | Nhân | `10 * 5` | `50` |
| `/` | Chia | `10 / 3` | `3` |
| `%` | Chia lấy dư | `10 % 3` | `1` |

> **Lưu ý:** Phép chia hai số nguyên cho kết quả số nguyên (bỏ phần dư). Để có kết quả số thực, dùng ít nhất một toán hạng kiểu thực: `10.0 / 3` → `3.3333...`

### 3.2. Toán tử so sánh

| Toán tử | Mô tả | Ví dụ | Kết quả |
|---------|--------|-------|---------|
| `==` | Bằng | `5 == 5` | `true` |
| `!=` | Khác | `5 != 3` | `true` |
| `>` | Lớn hơn | `5 > 3` | `true` |
| `>=` | Lớn hơn hoặc bằng | `5 >= 5` | `true` |
| `<` | Nhỏ hơn | `3 < 5` | `true` |
| `<=` | Nhỏ hơn hoặc bằng | `3 <= 5` | `true` |

### 3.3. Toán tử logic

| Toán tử | Mô tả | Ví dụ | Kết quả |
|---------|--------|-------|---------|
| `&&` | VÀ (AND) | `true && false` | `false` |
| `\|\|` | HOẶC (OR) | `true \|\| false` | `true` |
| `!` | PHỦ ĐỊNH (NOT) | `!true` | `false` |

### 3.4. Toán tử ba ngôi (Ternary)

```javascript
var result = (age >= 18) ? "Người lớn" : "Trẻ em";
```

### 3.5. Nối chuỗi

Dùng toán tử `+` để nối chuỗi:

```javascript
var greeting = "Xin chào, " + name + "!";
```

---

## 4. Cú pháp sử dụng

### 4.1. Khai báo biến

```javascript
var name = "Nguyen Van A";
var age = 30;
var isActive = true;
var today = Date.today();
```

### 4.2. Câu lệnh điều kiện - if / else

```javascript
if (age >= 18) {
    return "Đủ tuổi";
} else if (age >= 15) {
    return "Gần đủ tuổi";
} else {
    return "Chưa đủ tuổi";
}
```

### 4.3. Vòng lặp for

```javascript
// Vòng lặp for truyền thống
var sum = 0;
for (var i = 0; i < 10; i++) {
    sum += i;
}
return sum;  // 45
```

### 4.4. Vòng lặp for-each

```javascript
// Duyệt qua từng phần tử trong mảng/danh sách
var list = ["A", "B", "C",...];
var result = "";
for (var item : list) {
    result += item;
}
return result;  // "ABC"
```

### 4.5. Vòng lặp while

```javascript
var i = 0;
var sum = 0;
while (i < 5) {
    sum += i;
    i += 1;
}
return sum;  // 10
```

### 4.6. Vòng lặp lồng nhau

```javascript
var sum = 0;
for (var i = 0; i < 5; i++) {
    for (var j = 0; j < 5; j++) {
        sum += 1;
    }
}
return sum;  // 25
```

### 4.7. Break & Continue

```javascript
// break: thoát khỏi vòng lặp
for (var i = 0; i < 10; i++) {
    if (i == 5) {
        break;
    }
}

// continue: bỏ qua lần lặp hiện tại, chuyển sang lần tiếp theo
for (var i = 0; i < 10; i++) {
    if (i % 2 == 0) {
        continue;
    }
    // Chỉ xử lý số lẻ
}
```

### 4.8. Câu lệnh return

```javascript
// Trả về kết quả từ script
return "Kết quả: " + result;
```

---

## 5. Hàm Text

### 5.1. Hàm tĩnh (Static Functions)

Gọi thông qua `Text.<tên_hàm>(...)`.

---

#### `Text.begins(text, prefix)`

Kiểm tra chuỗi có bắt đầu bằng tiền tố hay không (phân biệt hoa/thường).

| Tham số | Kiểu | Mô tả |
|---------|------|--------|
| `text` | String | Chuỗi cần kiểm tra |
| `prefix` | String | Tiền tố cần tìm |

**Trả về:** `Boolean`

```javascript
Text.begins("Hello ABC", "Hello")    // true
Text.begins("Hello ABC", "hello")    // false
```

---

#### `Text.contains(text, search)`

Kiểm tra chuỗi có chứa chuỗi con hay không.

| Tham số | Kiểu | Mô tả |
|---------|------|--------|
| `text` | String | Chuỗi cần kiểm tra |
| `search` | String | Chuỗi con cần tìm |

**Trả về:** `Boolean`

```javascript
Text.contains("DD Hello ABC", "Hello")    // true
Text.contains("Hello ABC", "1hello")      // false
```

---

#### `Text.find(text, find [, start])`

Tìm vị trí xuất hiện đầu tiên của chuỗi con. Trả về `-1` nếu không tìm thấy.

| Tham số | Kiểu | Mô tả |
|---------|------|--------|
| `text` | String | Chuỗi gốc |
| `find` | String | Chuỗi cần tìm |
| `start` | int (tùy chọn) | Vị trí bắt đầu tìm (mặc định: 0) |

**Trả về:** `int` - Vị trí tìm thấy (bắt đầu từ 0), hoặc `-1`

```javascript
Text.find("DD Hello ABC", "Hello")       // 3
Text.find("Hello ABC", "1hello")         // -1
Text.find("DD Hello ABC", "Hello", 4)    // -1
Text.find("DD Hello ABC", "Hello", 1)    // 3
```

---

#### `Text.length(text)`

Trả về độ dài chuỗi.

| Tham số | Kiểu | Mô tả |
|---------|------|--------|
| `text` | String | Chuỗi cần đo |

**Trả về:** `int`

```javascript
Text.length("Hello")    // 5
```

---

#### `Text.lower(text)`

Chuyển chuỗi thành chữ thường.

```javascript
Text.lower("Hello")    // "hello"
```

---

#### `Text.upper(text)`

Chuyển chuỗi thành chữ HOA.

```javascript
Text.upper("Hello")    // "HELLO"
```

---

#### `Text.trim(text)`

Xóa khoảng trắng ở đầu và cuối chuỗi.

```javascript
Text.trim("  Hello  ")    // "Hello"
```

---

#### `Text.subString(text, start, length)`

Trích xuất chuỗi con.

| Tham số | Kiểu | Mô tả |
|---------|------|--------|
| `text` | String | Chuỗi gốc |
| `start` | int | Vị trí bắt đầu (từ 0) |
| `length` | int | Số ký tự cần lấy |

**Trả về:** `String`

```javascript
Text.subString("Hello", 1, 2)     // "el"
Text.subString("Hello", 1, 5)     // "ello"
Text.subString("Hello", 6, 5)     // ""
```

---

#### `Text.left(text, n)`

Lấy `n` ký tự đầu tiên từ bên trái.

```javascript
Text.left("Hello World", 5)    // "Hello"
Text.left("Hi", 10)            // "Hi"
Text.left("Hello", 0)          // ""
```

---

#### `Text.right(text, n)`

Lấy `n` ký tự cuối cùng từ bên phải.

```javascript
Text.right("Hello World", 5)    // "World"
Text.right("Hi", 10)            // "Hi"
Text.right("Hello", 0)          // ""
```

---

#### `Text.replace(text, search, replacement)`

Thay thế **tất cả** lần xuất hiện của chuỗi tìm kiếm.

```javascript
Text.replace("Hello World", "World", "Java")    // "Hello Java"
Text.replace("a-a-a", "a", "b")                 // "b-b-b"
Text.replace("Hello World", " ", "")             // "HelloWorld"
```

---

#### `Text.isBlank(text)`

Kiểm tra chuỗi có rỗng hoặc chỉ chứa khoảng trắng hay không.

```javascript
Text.isBlank(null)      // true
Text.isBlank("")        // true
Text.isBlank("   ")     // true
Text.isBlank("abc")     // false
```

---

#### `Text.endsWith(text, suffix)`

Kiểm tra chuỗi có kết thúc bằng hậu tố hay không.

```javascript
Text.endsWith("test.pdf", ".pdf")    // true
Text.endsWith("test.pdf", ".doc")    // false
```

---

#### `Text.split(text, delimiter)`

Tách chuỗi thành danh sách (List) theo ký tự phân tách.

**Trả về:** `List<String>`

```javascript
var arr = Text.split("a,b,c", ",");
arr.size()     // 3
arr[0]         // "a"
arr[1]         // "b"
arr[2]         // "c"
```

---

#### `Text.join(list, separator)`

Nối các phần tử trong danh sách thành chuỗi, ngăn cách bằng ký tự chỉ định.

```javascript
var list = ["a", "b", "c",...];
Text.join(list, ", ")              // "a, b, c"

var arr = Text.split("a,b,c", ",");
Text.join(arr, "-")                // "a-b-c"
```

---

#### `Text.lpad(text, length, padChar)`

Thêm ký tự vào bên **trái** cho đến khi đạt độ dài mong muốn.

```javascript
Text.lpad("42", 5, "0")        // "00042"
Text.lpad("12345", 5, "0")     // "12345" (đã đủ dài)
Text.lpad("123456", 5, "0")    // "123456" (dài hơn, giữ nguyên)
```

---

#### `Text.rpad(text, length, padChar)`

Thêm ký tự vào bên **phải** cho đến khi đạt độ dài mong muốn.

```javascript
Text.rpad("AB", 5, "-")        // "AB---"
Text.rpad("ABCDE", 5, "-")     // "ABCDE" (đã đủ dài)
```

---

#### `Text.matches(text, regex)`

Kiểm tra chuỗi có khớp với biểu thức chính quy (regex) hay không.

```javascript
Text.matches("abc@example.com", ".*@.*\\.com")    // true
Text.matches("abc", "\\d+")                 // false
Text.matches("12345", "\\d+")               // true
```

---

#### `Text.repeat(text, n)`

Lặp lại chuỗi `n` lần.

```javascript
Text.repeat("*", 3)       // "***"
Text.repeat("=-", 3)      // "=-=-=-"
Text.repeat("abc", 0)     // ""
```

---

#### `Text.valueOf(value)`

Chuyển đổi giá trị bất kỳ thành chuỗi.

```javascript
Text.valueOf(1234)     // "1234"
Text.valueOf(3.14)     // "3.14"
Text.valueOf(true)     // "true"
Text.valueOf(null)     // null
```

---

### 5.2. Hàm instance (Gọi trên chuỗi)

Các hàm này gọi trực tiếp trên giá trị chuỗi.

| Hàm | Mô tả | Ví dụ | Kết quả |
|-----|--------|-------|---------|
| `.toLowerCase()` | Chuyển thành chữ thường | `"Hello".toLowerCase()` | `"hello"` |
| `.toUpperCase()` | Chuyển thành chữ HOA | `"Hello".toUpperCase()` | `"HELLO"` |
| `.substring(start, end)` | Trích xuất chuỗi con (start bao gồm, end không bao gồm) | `"Hello, World!".substring(4, 8)` | `"o, W"` |
| `.concat(text)` | Nối chuỗi | `"Hello".concat(" World")` | `"Hello World"` |
| `.contains(text)` | Kiểm tra chứa chuỗi con | `"Hello".contains("ell")` | `true` |
| `.indexOf(text)` | Tìm vị trí chuỗi con | `"Hello".indexOf("llo")` | `2` |
| `.startsWith(prefix)` | Kiểm tra bắt đầu bằng | `"Hello World".startsWith("Hello")` | `true` |
| `.endsWith(suffix)` | Kiểm tra kết thúc bằng | `"test.pdf".endsWith(".pdf")` | `true` |
| `.isEmpty()` | Kiểm tra chuỗi rỗng | `"".isEmpty()` | `true` |
| `.length()` | Độ dài chuỗi | `"Hello".length()` | `5` |
| `.equals(text)` | So sánh chính xác | `"abc".equals("aBC")` | `false` |
| `.equalsIgnoreCase(text)` | So sánh không phân biệt hoa/thường | `"abc".equalsIgnoreCase("aBC")` | `true` |
| `.charAt(index)` | Lấy ký tự tại vị trí | `"Hello".charAt(0)` | `"H"` |
| `.replace(old, new)` | Thay thế chuỗi | `"a-b-c".replace("-", "+")` | `"a+b+c"` |
| `.replaceAll(regex, replacement)` | Thay thế theo regex | `"a1b2c3".replaceAll("\\d", "")` | `"abc"` |
| `.matches(regex)` | Kiểm tra khớp regex | `"abc@example.com".matches(".*@.*")` | `true` |
| `.split(regex)` | Tách chuỗi theo regex | `"a,b,c".split(",")` | `["a","b","c"]` |
| `.trim()` | Xóa khoảng trắng đầu/cuối | `"  hi  ".trim()` | `"hi"` |
| `.strip()` | Xóa khoảng trắng (Unicode-aware) | `"  hi  ".strip()` | `"hi"` |
| `.isBlank()` | Kiểm tra rỗng hoặc chỉ khoảng trắng | `"  ".isBlank()` | `true` |
| `.compareTo(text)` | So sánh thứ tự (<0, 0, >0) | `"a".compareTo("b")` | `-1` |
| `.lastIndexOf(text)` | Tìm vị trí xuất hiện cuối | `"abcabc".lastIndexOf("abc")` | `3` |
| `.toCharArray()` | Chuyển thành mảng ký tự | `"abc".toCharArray()` | `['a','b','c']` |
| `.codePointAt(index)` | Lấy mã Unicode tại vị trí | `"A".codePointAt(0)` | `65` |

> **Lưu ý:** `.substring(start, end)` khác với `Text.subString(text, start, length)`:
> - `.substring(0, 3)` lấy từ vị trí 0 đến vị trí 3 (không bao gồm 3)
> - `Text.subString("Hello", 0, 3)` lấy 3 ký tự bắt đầu từ vị trí 0

> **Lưu ý:** Vì Text chính là `java.lang.String`, bạn có thể gọi bất kỳ hàm public nào của Java String. Bảng trên liệt kê các hàm thường dùng nhất.

---

## 6. Hàm Number & Math

### 6.1. Hàm Math (Toán học)

Gọi thông qua `Math.<tên_hàm>(...)`.

#### Các hằng số

| Hằng số | Mô tả | Giá trị |
|---------|--------|---------|
| `Math.PI` hoặc `Math.PI()` | Số Pi | `3.141592653589793` |
| `Math.E` | Số Euler | `2.718281828459045` |

#### Các hàm cơ bản

| Hàm | Mô tả | Ví dụ | Kết quả |
|-----|--------|-------|---------|
| `Math.abs(n)` | Giá trị tuyệt đối | `Math.abs(-15.0)` | `15.0` |
| `Math.round(n, places)` | Làm tròn đến `places` chữ số thập phân | `Math.round(3.14159, 2)` | `3.14` |
| `Math.ceil(n)` | Làm tròn **lên** | `Math.ceil(1234.1)` | `1235.0` |
| `Math.floor(n)` | Làm tròn **xuống** | `Math.floor(1234.9)` | `1234.0` |
| `Math.sqrt(n)` | Căn bậc hai | `Math.sqrt(16)` | `4.0` |
| `Math.pow(base, exp)` | Lũy thừa | `Math.pow(3, 4)` | `81.0` |
| `Math.mod(a, b)` | Chia lấy dư | `Math.mod(10, 3)` | `1.0` |
| `Math.max(n1, n2, ...)` | Giá trị lớn nhất | `Math.max(1, 100, 3)` | `100.0` |
| `Math.min(n1, n2, ...)` | Giá trị nhỏ nhất | `Math.min(1, 100, 3)` | `1.0` |
| `Math.sign(n)` | Dấu của số (-1, 0, 1) | `Math.sign(-42)` | `-1.0` |
| `Math.random()` | Số ngẫu nhiên [0, 1) | `Math.random()` | `0.xxx...` |

#### Hàm logarithm & mũ

| Hàm | Mô tả | Ví dụ | Kết quả |
|-----|--------|-------|---------|
| `Math.ln(n)` | Logarit tự nhiên (base e) | `Math.ln(Math.E)` | `1.0` |
| `Math.log(n)` | Logarit cơ số 10 | `Math.log(100)` | `2.0` |
| `Math.exp(n)` | Hàm mũ e^n | `Math.exp(0)` | `1.0` |

#### Hàm lượng giác

| Hàm | Mô tả | Ví dụ | Kết quả |
|-----|--------|-------|---------|
| `Math.sin(n)` | Sin (radian) | `Math.sin(Math.PI / 2)` | `1.0` |
| `Math.cos(n)` | Cos (radian) | `Math.cos(0)` | `1.0` |
| `Math.tan(n)` | Tan (radian) | `Math.tan(0)` | `0.0` |
| `Math.asin(n)` | Arcsin | `Math.asin(1)` | `1.5707...` |
| `Math.acos(n)` | Arccos | `Math.acos(1)` | `0.0` |
| `Math.atan(n)` | Arctan | `Math.atan(0)` | `0.0` |

---

### 6.2. Hàm Number (Định dạng & Chuyển đổi số)

Gọi thông qua `Number.<tên_hàm>(...)`.

---

#### `Number.format(number, groupingSeparator, decimalSeparator [, decimalPlaces])`

Định dạng số với dấu phân cách tùy chỉnh.

| Tham số | Kiểu | Mô tả |
|---------|------|--------|
| `number` | double | Số cần định dạng |
| `groupingSeparator` | String | Dấu phân cách hàng nghìn (VD: `","`, `"."`, `""`) |
| `decimalSeparator` | String | Dấu phân cách thập phân (VD: `"."`, `","`) |
| `decimalPlaces` | int (tùy chọn) | Số chữ số thập phân |

**Trả về:** `String`

```javascript
// Định dạng quốc tế (US)
Number.format(123456789.123, ",", ".")        // "123,456,789.123"

// Định dạng Việt Nam
Number.format(123456789.123, ".", ",")        // "123.456.789,123"

// Không có dấu phân cách hàng nghìn
Number.format(123456789.123, "", ",")         // "123456789,123"

// Chỉ định số chữ số thập phân
Number.format(1234567.89, ",", ".", 2)        // "1,234,567.89"
Number.format(1234567.89, ".", ",", 2)        // "1.234.567,89"
Number.format(1234.5, ",", ".", 3)            // "1,234.500"
Number.format(1234567.89, ",", ".", 0)        // "1,234,568"
```

---

#### `Number.toNumber(value)`

Chuyển đổi giá trị thành số (Integer, Long, hoặc Double tùy thuộc vào giá trị).

```javascript
Number.toNumber("1234")       // 1234
Number.toNumber("1234.56")    // 1234.56
Number.toNumber("-42.5")      // -42.5
Number.toNumber("abc")        // null
Number.toNumber(null)         // null
```

---

#### `Number.toInteger(value)`

Chuyển đổi thành số nguyên Integer (cắt bỏ phần thập phân).

```javascript
Number.toInteger("1234")       // 1234
Number.toInteger("1234.56")    // 1234
Number.toInteger("-42")        // -42
Number.toInteger("abc")        // null
```

---

#### `Number.toLong(value)`

Chuyển đổi thành số nguyên Long (cho số lớn).

```javascript
Number.toLong("1234567890")     // 1234567890
Number.toLong("9999999999")     // 9999999999
Number.toLong("abc")            // null
```

---

#### `Number.toDouble(value)`

Chuyển đổi thành số thực Double.

```javascript
Number.toDouble("1234.56")    // 1234.56
Number.toDouble("1234")       // 1234.0
Number.toDouble("abc")        // null
```

---

#### `Number.isNumber(value)`

Kiểm tra giá trị có phải là số hợp lệ hay không.

```javascript
Number.isNumber("123")       // true
Number.isNumber("123.45")    // true
Number.isNumber("-99.9")     // true
Number.isNumber("abc")       // false
Number.isNumber("")          // false
Number.isNumber(null)        // false
```

---

#### `Number.strip(value)`

Xóa **tất cả** ký tự không phải chữ số (giữ lại dấu `-` ở đầu).

```javascript
Number.strip("1,234,567.89")    // "123456789"
Number.strip("1.234.567,89")    // "123456789"
Number.strip("-123,456")        // "-123456"
Number.strip(null)              // null
```

---

#### `Number.stripGrouping(value)`

Xóa dấu phẩy (`,`) phân cách hàng nghìn.

```javascript
Number.stripGrouping("1,234,567.89")    // "1234567.89"
Number.stripGrouping("1234567.89")      // "1234567.89"
Number.stripGrouping(null)              // null
```

---

#### `Number.stripChars(value, chars)`

Xóa các ký tự được chỉ định khỏi chuỗi.

```javascript
Number.stripChars("1.234.567,89", ".")      // "1234567,89"
Number.stripChars("1.234.567,89", ".,")     // "123456789"
Number.stripChars(null, ".")                // null
```

**Ví dụ kết hợp:** Chuyển số Việt Nam sang số:

```javascript
// "1.234.567,89" -> 1234567.89
var s = Number.stripChars("1.234.567,89", ".");
s = s.replace(",", ".");
var result = Number.toDouble(s);    // 1234567.89
```

---

### 6.3. Hàm instance trên giá trị số

Khi giá trị là kiểu số (`Integer`, `Long`, `Double`), bạn có thể gọi các hàm Java:

| Hàm | Mô tả | Ví dụ | Kết quả |
|-----|--------|-------|---------|
| `.intValue()` | Chuyển sang int | `(3.14).intValue()` | `3` |
| `.longValue()` | Chuyển sang long | `(42).longValue()` | `42` |
| `.doubleValue()` | Chuyển sang double | `(42).doubleValue()` | `42.0` |
| `.toString()` | Chuyển sang chuỗi | `(42).toString()` | `"42"` |
| `.compareTo(n)` | So sánh (<0, 0, >0) | `(5).compareTo(3)` | `1` |

---

## 7. Hàm Date

### 7.1. Hàm tĩnh (Static Functions)

---

#### `Date.today()`

Trả về ngày hiện tại (theo timezone tài khoản).

**Trả về:** `Date`

```javascript
var today = Date.today();
today.format("dd/MM/yyyy")    // "15/03/2024"
```

---

#### `Date.date(year, month, day)`

Tạo giá trị Date từ năm, tháng, ngày.

| Tham số | Kiểu | Mô tả |
|---------|------|--------|
| `year` | int | Năm |
| `month` | int | Tháng (1-12) |
| `day` | int | Ngày (1-31) |

**Trả về:** `Date`

```javascript
var d = Date.date(2024, 3, 15);
d.format("dd/MM/yyyy")    // "15/03/2024"
```

---

#### `Date.valueOf(dateText [, format])`

Chuyển chuỗi thành Date. Format mặc định: `"yyyy-MM-dd"`.

| Tham số | Kiểu | Mô tả |
|---------|------|--------|
| `dateText` | String | Chuỗi ngày cần chuyển |
| `format` | String (tùy chọn) | Định dạng ngày (mặc định: `"yyyy-MM-dd"`) |

**Trả về:** `Date`

```javascript
Date.valueOf("2024-03-15")                         // Mặc định yyyy-MM-dd
Date.valueOf("15/03/2024", "dd/MM/yyyy")           // Tùy chỉnh format
Date.valueOf("2024-03-15").format("dd/MM/yyyy")    // "15/03/2024"
```

---

#### `Date.fromTimestamp(timestamp)`

Tạo Date từ timestamp (milliseconds).

```javascript
var d = Date.fromTimestamp(1710460800000);
```

---

### 7.2. Hàm instance (Gọi trên giá trị Date)

---

#### `date.format(format)`

Định dạng ngày thành chuỗi.

| Ký hiệu | Mô tả | Ví dụ |
|----------|--------|-------|
| `dd` | Ngày (2 chữ số) | `01`, `15`, `31` |
| `MM` | Tháng (2 chữ số) | `01`, `03`, `12` |
| `yyyy` | Năm (4 chữ số) | `2024` |
| `EEE` | Tên thứ viết tắt | `Mon`, `Tue`, `Sun` |

```javascript
var d = Date.date(1987, 8, 30);
d.format("dd/MM/yyyy")          // "30/08/1987"
d.format("EEE dd/MM/yyyy")     // "Sun 30/08/1987"
d.format("yyyy-MM-dd")         // "1987-08-30"
```

---

#### `date.addDays(days)`

Cộng/trừ số ngày. **Trả về Date mới**, không thay đổi đối tượng gốc. Hỗ trợ chuỗi (chainable).

```javascript
var d = Date.valueOf("2024-03-15");
d.addDays(7).format("dd/MM/yyyy")      // "22/03/2024"  (d vẫn là 15/03/2024)
d.addDays(-10).format("dd/MM/yyyy")    // "05/03/2024"  (d vẫn là 15/03/2024)
d.addDays(20).format("dd/MM/yyyy")     // "04/04/2024"  (qua tháng, d vẫn là 15/03/2024)
```

---

#### `date.addMonths(months)`

Cộng/trừ số tháng. **Trả về Date mới**, không thay đổi đối tượng gốc.

```javascript
var d = Date.date(2024, 8, 30);
d.addMonths(5).format("dd/MM/yyyy")    // "30/01/2025"  (d vẫn là 30/08/2024)
```

---

#### `date.addYears(years)`

Cộng/trừ số năm. **Trả về Date mới**, không thay đổi đối tượng gốc.

```javascript
var d = Date.valueOf("2024-03-15");
d.addYears(2).format("dd/MM/yyyy")     // "15/03/2026"  (d vẫn là 15/03/2024)
d.addYears(-5).format("dd/MM/yyyy")    // "15/03/2019"  (d vẫn là 15/03/2024)
```

---

#### `date.diffDays(otherDate)`

Tính số ngày chênh lệch giữa hai ngày (`this - other`).

```javascript
var d1 = Date.valueOf("2024-03-01");
var d2 = Date.valueOf("2024-03-31");
d2.diffDays(d1)    // 30
d1.diffDays(d2)    // -30
```

---

#### `date.isBefore(otherDate)`

Kiểm tra ngày có trước ngày khác không.

```javascript
var d1 = Date.valueOf("2024-01-01");
var d2 = Date.valueOf("2024-12-31");
d1.isBefore(d2)    // true
d2.isBefore(d1)    // false
```

---

#### `date.isAfter(otherDate)`

Kiểm tra ngày có sau ngày khác không.

```javascript
var d1 = Date.valueOf("2024-01-01");
var d2 = Date.valueOf("2024-12-31");
d2.isAfter(d1)    // true
d1.isAfter(d2)    // false
```

---

#### `date.isWeekend()`

Kiểm tra ngày có phải cuối tuần (Thứ 7 hoặc Chủ nhật) không.

```javascript
Date.valueOf("2024-03-16").isWeekend()    // true  (Thứ 7)
Date.valueOf("2024-03-17").isWeekend()    // true  (Chủ nhật)
Date.valueOf("2024-03-18").isWeekend()    // false (Thứ 2)
```

---

#### Các hàm truy vấn thông tin ngày

| Hàm | Mô tả | Ví dụ (ngày 30/08/1987) | Kết quả |
|-----|--------|-------------------------|---------|
| `date.dayOfMonth()` | Ngày trong tháng (1-31) | `d.dayOfMonth()` | `30` |
| `date.dayOfYear()` | Ngày trong năm (1-366) | `d.dayOfYear()` | `242` |
| `date.dayOfWeek()` | Ngày trong tuần (1=Thứ 2, 7=CN) | `d.dayOfWeek()` | `7` |
| `date.getMonth()` | Tháng (1-12) | `d.getMonth()` | `8` |
| `date.getYear()` | Năm | `d.getYear()` | `1987` |

---

#### Chuỗi hàm (Chaining)

Các hàm `addDays`, `addMonths`, `addYears` trả về **Date mới** nên có thể nối tiếp nhau. Đối tượng gốc **không bị thay đổi**:

```javascript
var d = Date.valueOf("2024-03-15");
d.addDays(1).isWeekend()    // true (16/03/2024 là Thứ 7), d vẫn là 15/03/2024

// Muốn lưu kết quả, gán vào biến mới:
var nextDay = d.addDays(1);    // nextDay = 16/03/2024, d vẫn = 15/03/2024

var start = Date.valueOf("2024-01-01");
var end = Date.valueOf("2024-12-31");
end.diffDays(start)    // 365
```

---

## 8. Hàm Datetime

### 8.1. Hàm tĩnh (Static Functions)

---

#### `Datetime.now()`

Trả về ngày giờ hiện tại (theo timezone tài khoản).

**Trả về:** `Datetime`

```javascript
var now = Datetime.now();
now.format("dd-MM-yyyy HH:mm:ss")    // "15/03/2024 10:30:00"
```

---

#### `Datetime.valueOf(datetimeText [, format])`

Chuyển chuỗi thành Datetime. **Mặc định UTC timezone**, format mặc định: `"yyyy-MM-dd HH:mm:ss"`.

| Tham số | Kiểu | Mô tả |
|---------|------|--------|
| `datetimeText` | String | Chuỗi ngày giờ |
| `format` | String (tùy chọn) | Định dạng (mặc định: `"yyyy-MM-dd HH:mm:ss"`) |

**Trả về:** `Datetime`

```javascript
Datetime.valueOf("2024-07-27 10:59:59")
Datetime.valueOf("2024/07/27 10:59:59", "yyyy/MM/dd HH:mm:ss")
```

---

#### `Datetime.valueOfWithAccountTimeZone(datetimeText [, format])`

Chuyển chuỗi thành Datetime, sử dụng **timezone của tài khoản** (thay vì UTC).

```javascript
// Nếu tài khoản ở Asia/Ho_Chi_Minh (UTC+7):
var dt = Datetime.valueOfWithAccountTimeZone("2024-07-27 10:59:59");
dt.format("dd-MM-yyyy HH:mm:ss")    // "27-07-2024 03:59:59" (UTC)
```

---

#### `Datetime.fromTimestamp(timestamp)`

Tạo Datetime từ timestamp (milliseconds).

```javascript
var dt = Datetime.fromTimestamp(1710460800000);
```

---

### 8.2. Hàm instance (Gọi trên giá trị Datetime)

---

#### `datetime.format(format)`

Định dạng datetime thành chuỗi (**UTC timezone**).

| Ký hiệu | Mô tả | Ví dụ |
|----------|--------|-------|
| `dd` | Ngày | `01`, `15`, `31` |
| `MM` | Tháng | `01`, `03`, `12` |
| `yyyy` | Năm | `2024` |
| `HH` | Giờ (24h) | `00`, `13`, `23` |
| `mm` | Phút | `00`, `30`, `59` |
| `ss` | Giây | `00`, `45`, `59` |

```javascript
var dt = Datetime.valueOf("2024-07-27 10:59:59");
dt.format("dd-MM-yyyy HH:mm:ss")    // "27-07-2024 10:59:59"
```

---

#### `datetime.formatWithAccountTimeZone(format)`

Định dạng datetime theo **timezone tài khoản**.

```javascript
// Tài khoản ở Asia/Ho_Chi_Minh (UTC+7):
var dt = Datetime.valueOf("2024-07-27 10:59:59");    // UTC
dt.formatWithAccountTimeZone("dd-MM-yyyy HH:mm:ss")  // "27-07-2024 17:59:59"
```

---

#### `datetime.timestamp()`

Trả về timestamp dạng milliseconds.

```javascript
var now = Datetime.now();
var ts = now.timestamp();    // 1710500000000 (ví dụ)
```

---

#### Cộng/trừ thời gian

Tất cả các hàm cộng/trừ **trả về Datetime mới**, không thay đổi đối tượng gốc.

| Hàm | Mô tả | Ví dụ |
|-----|--------|-------|
| `datetime.addDays(n)` | Cộng/trừ ngày | `dt.addDays(5)`, `dt.addDays(-10)` |
| `datetime.addHours(n)` | Cộng/trừ giờ | `dt.addHours(5)`, `dt.addHours(-3)` |
| `datetime.addMinutes(n)` | Cộng/trừ phút | `dt.addMinutes(90)`, `dt.addMinutes(-30)` |
| `datetime.addMonths(n)` | Cộng/trừ tháng | `dt.addMonths(2)` |

```javascript
var dt = Datetime.valueOf("2024-03-15 10:00:00");

dt.addDays(5).format("yyyy-MM-dd HH:mm:ss")       // "2024-03-20 10:00:00"  (dt không đổi)
dt.addHours(5).format("yyyy-MM-dd HH:mm:ss")      // "2024-03-15 15:00:00"  (dt không đổi)
dt.addMinutes(90).format("yyyy-MM-dd HH:mm:ss")   // "2024-03-15 11:30:00"  (dt không đổi)
dt.addMonths(2).format("yyyy-MM-dd HH:mm:ss")     // "2024-05-15 10:00:00"  (dt không đổi)

// Qua ngày
var dt2 = Datetime.valueOf("2024-03-15 22:00:00");
dt2.addHours(5).format("yyyy-MM-dd HH:mm:ss")     // "2024-03-16 03:00:00"

// Chuỗi hàm (Chaining)
dt.addHours(3).addMinutes(30).format("HH:mm")     // "13:30"
```

---

#### Tính chênh lệch

| Hàm | Mô tả | Đơn vị |
|-----|--------|--------|
| `datetime.diffDays(other)` | Chênh lệch ngày | Ngày |
| `datetime.diffHours(other)` | Chênh lệch giờ | Giờ |
| `datetime.diffMinutes(other)` | Chênh lệch phút | Phút |

```javascript
var dt1 = Datetime.valueOf("2024-03-15 10:00:00");
var dt2 = Datetime.valueOf("2024-03-17 10:00:00");

dt2.diffDays(dt1)       // 2
dt2.diffHours(dt1)      // 48
dt2.diffMinutes(dt1)    // 2880
dt1.diffDays(dt2)       // -2  (kết quả âm)
```

---

#### So sánh

| Hàm | Mô tả |
|-----|--------|
| `datetime.isBefore(other)` | Kiểm tra có trước không |
| `datetime.isAfter(other)` | Kiểm tra có sau không |

```javascript
var dt1 = Datetime.valueOf("2024-03-15 10:00:00");
var dt2 = Datetime.valueOf("2024-03-15 12:00:00");

dt1.isBefore(dt2)    // true
dt1.isAfter(dt2)     // false
dt2.isAfter(dt1)     // true
```

---

#### Truy vấn thông tin

| Hàm | Mô tả | Phạm vi |
|-----|--------|---------|
| `datetime.getHour()` | Giờ (theo timezone tài khoản) | 0-23 |
| `datetime.getMinute()` | Phút | 0-59 |
| `datetime.getSecond()` | Giây | 0-59 |
| `datetime.getMonth()` | Tháng | 1-12 |
| `datetime.getYear()` | Năm | - |
| `datetime.getDayOfMonth()` | Ngày trong tháng | 1-31 |

```javascript
var dt = Datetime.valueOf("2024-03-15 10:30:45");
dt.getHour()        // 17 (nếu timezone tài khoản là UTC+7)
dt.getMinute()      // 30
dt.getSecond()      // 45
dt.getMonth()       // 3
dt.getYear()        // 2024
dt.getDayOfMonth()  // 15
```

---

## 9. Hàm DateRange & DatetimeRange

### 9.1. DateRange (Khoảng ngày)

---

#### `DateRange.of(startDate, endDate)`

Tạo khoảng ngày từ ngày bắt đầu đến ngày kết thúc.

```javascript
var start = Date.date(2024, 7, 20);
var end = Date.date(2024, 7, 25);
var range = DateRange.of(start, end);
```

---

#### `dateRange.getStart()` / `dateRange.getEnd()`

Lấy ngày bắt đầu / kết thúc.

```javascript
var s = range.getStart();    // Date: 20/07/2024
var e = range.getEnd();      // Date: 25/07/2024
```

---

#### `dateRange.range()`

Trả về số ngày trong khoảng.

```javascript
range.range()    // 5
```

---

#### `dateRange.isInRange(date)`

Kiểm tra ngày có nằm trong khoảng không (bao gồm ngày bắt đầu và kết thúc: **không bao gồm ngày kết thúc**).

```javascript
var start = Date.date(2024, 7, 20);
var end = Date.date(2024, 7, 22);
var range = DateRange.of(start, end);

range.isInRange(Date.date(2024, 7, 19))    // false
range.isInRange(Date.date(2024, 7, 20))    // true  (bao gồm start)
range.isInRange(Date.date(2024, 7, 21))    // true
range.isInRange(Date.date(2024, 7, 22))    // true  (bao gồm end)
range.isInRange(Date.date(2024, 7, 23))    // false
```

---

### 9.2. DatetimeRange (Khoảng ngày giờ)

---

#### `DatetimeRange.of(startDatetime, endDatetime)`

Tạo khoảng ngày giờ.

```javascript
var start = Datetime.valueOf("2024-07-11 15:30:45");
var end = Datetime.valueOf("2024-07-12 15:30:45");
var range = DatetimeRange.of(start, end);
```

---

#### `datetimeRange.range()`

Trả về chênh lệch tính bằng **milliseconds**.

```javascript
range.range()    // 86400000 (= 24 giờ)
```

---

#### `datetimeRange.isInRange(datetime)`

Kiểm tra datetime có nằm trong khoảng không.

```javascript
var start = Datetime.valueOf("2024-07-11 15:30:45");
var end = Datetime.valueOf("2024-07-13 15:30:45");
var range = DatetimeRange.of(start, end);

range.isInRange(Datetime.valueOf("2024-07-11 15:30:44"))    // false
range.isInRange(Datetime.valueOf("2024-07-11 15:30:45"))    // true (bao gồm start)
range.isInRange(Datetime.valueOf("2024-07-12 15:30:45"))    // true
range.isInRange(Datetime.valueOf("2024-07-13 15:30:45"))    // true (bao gồm end)
range.isInRange(Datetime.valueOf("2024-07-13 15:30:46"))    // false
```

---

## 10. Hàm JSON

### 10.1. Hàm tĩnh

---

#### `Json.parse(jsonText)`

Chuyển chuỗi JSON thành đối tượng Map hoặc List.

**Trả về:** `Map` (nếu JSON Object), `List` (nếu JSON Array), `null` (nếu null hoặc rỗng)

```javascript
// Parse JSON Object -> Map
var data = Json.parse('{"name":"John","age":30}');
data.name    // "John"
data.age     // 30

// Parse JSON Array -> List
var arr = Json.parse("[1,2,3]");
arr[0]       // 1
arr.size()   // 3

// Parse JSON lồng nhau
var text = '{"body":{"content":[{"type":"text","text":"hello world"}]}}';
var json = Json.parse(text);
json.body.content[0].text    // "hello world"

// Xử lý null
Json.parse(null)    // null
Json.parse("")      // null
```

---

#### `Json.stringify(obj)`

Chuyển đối tượng Map hoặc List thành chuỗi JSON.

**Trả về:** `String`

```javascript
var map = {"name": "John", "age": 30};
Json.stringify(map)     // '{"name":"John","age":30}'

Json.stringify(null)    // "null"
```

---

### 10.2. Ví dụ thực tế

```javascript
// Xử lý API response
var content = Json.parse($responseBody);
var text = content.content[0].text;
return text;

// Parse và truy cập dữ liệu
var jsonText = '{"message":"success","code":200}';
var data = Json.parse(jsonText);
return data.message;    // "success"
```

---

## 11. Hàm SelectList

### 11.1. Hàm tĩnh

---

#### `SelectedList.create()`

Tạo một SelectList mới (rỗng).

**Trả về:** `SelectList`

```javascript
var selectList = SelectedList.create();
```

---

### 11.2. Hàm instance

---

#### `selectList.addOption(id, slug, value)`

Thêm một tùy chọn vào danh sách.

| Tham số | Kiểu | Mô tả |
|---------|------|--------|
| `id` | String | ID duy nhất của option |
| `slug` | String | Slug (định danh) |
| `value` | String | Giá trị hiển thị |

```javascript
var sl = SelectedList.create();
sl.addOption("1", "option-1", "Option 1");
sl.addOption("2", "option-2", "Option 2");
sl.addOption("3", "option-3", "Option 3");
```

---

#### `selectList.containsOptionValue(value)`

Kiểm tra danh sách có chứa giá trị hay không.

**Trả về:** `Boolean`

```javascript
sl.containsOptionValue("Option 1")    // true
sl.containsOptionValue("Option 99")   // false
```

---

#### `selectList.removeOption(id)`

Xóa option theo ID.

```javascript
sl.removeOption("1");
```

---

#### `selectList.removeOptionBySlug(slug)`

Xóa option theo slug.

```javascript
sl.removeOptionBySlug("option-1");
```

---

#### `selectList.removeOptionByValue(value)`

Xóa option theo giá trị.

```javascript
sl.removeOptionByValue("Option 1");
```

---

#### `selectList.clearOptions()`

Xóa tất cả options.

```javascript
sl.clearOptions();
sl.containsOptionValue("Option 1")    // false
```

---

### 11.3. Ví dụ đầy đủ

```javascript
var sl = SelectedList.create();
sl.addOption("1", "opt-1", "Option 1");
sl.addOption("2", "opt-2", "Option 2");
sl.addOption("3", "opt-3", "Option 3");

// Kiểm tra và xử lý
if (sl.containsOptionValue("Option 3")) {
    sl.removeOptionByValue("Option 2");
    sl.addOption("4", "opt-4", "Option 4");
}

return sl.containsOptionValue("Option 4");    // true
```

---

## 12. Array, List & Map

### 12.1. Array (Mảng cố định)

Khai báo **không có** dấu phẩy cuối. Không thể thay đổi kích thước.

```javascript
var arr = ["A", 10.1, "C"];
```

| Thao tác | Cú pháp | Ví dụ | Kết quả |
|----------|---------|-------|---------|
| Truy cập phần tử | `arr[index]` hoặc `arr.get(index)` | `arr[0]` | `"A"` |
| Kích thước | `arr.size()` | `arr.size()` | `3` |
| Duyệt | `for (var item : arr)` | - | - |

```javascript
// Ví dụ duyệt mảng
var arr = ["A", 10.1, "C"];
var result = "";
for (var item : arr) {
    result += item + "-";
}
return result;    // "A-10.1-C-"
```

---

### 12.2. List (Danh sách động)

Khai báo **có dấu phẩy và `...`** ở cuối. Có thể thêm/xóa phần tử.

```javascript
var list = ["A", 10.1, "C", "D",...];
```

| Thao tác | Cú pháp | Ví dụ | Kết quả |
|----------|---------|-------|---------|
| Truy cập | `list[index]` hoặc `list.get(index)` | `list[0]` | `"A"` |
| Kích thước | `list.size()` | `list.size()` | `4` |
| Thêm vào vị trí | `list.add(index, value)` | `list.add(1, 1000)` | - |
| Xóa theo vị trí | `list.remove(index)` | `list.remove(2)` | - |
| Tìm vị trí | `list.indexOf(value)` | `list.indexOf("C")` | `2` |
| Phần tử đầu | `list.getFirst()` | `list.getFirst()` | `"A"` |
| Phần tử cuối | `list.getLast()` | `list.getLast()` | `"D"` |
| Thêm đầu | `list.addFirst(value)` | `list.addFirst("X")` | - |
| Thêm cuối | `list.addLast(value)` | `list.addLast("Y")` | - |
| Duyệt | `for (var item : list)` | - | - |

```javascript
// Ví dụ thêm/xóa
var list = ["A", 10.1, "C", "D",...];
list.add(1, 1000);     // ["A", 1000, 10.1, "C", "D"]
list.remove(2);        // ["A", 1000, "C", "D"]
return list[0] + "-" + list[1] + "-" + list[2];    // "A-1000-C"
```

#### Các hàm Java List bổ sung

Vì List là `java.util.ArrayList`, bạn có thể gọi thêm các hàm sau:

| Thao tác | Cú pháp | Mô tả |
|----------|---------|--------|
| Kiểm tra chứa | `list.contains(value)` | Kiểm tra phần tử có trong list không |
| Kiểm tra rỗng | `list.isEmpty()` | Kiểm tra list có rỗng không |
| Gán giá trị | `list.set(index, value)` | Gán giá trị tại vị trí (thay thế phần tử) |
| Xóa tất cả | `list.clear()` | Xóa toàn bộ phần tử |
| Vị trí cuối | `list.lastIndexOf(value)` | Tìm vị trí xuất hiện cuối cùng |
| Chứa tất cả | `list.containsAll(otherList)` | Kiểm tra chứa tất cả phần tử của list khác |
| Thêm tất cả | `list.addAll(otherList)` | Thêm toàn bộ phần tử từ list khác |
| Danh sách con | `list.subList(from, to)` | Lấy danh sách con (from bao gồm, to không bao gồm) |
| Sắp xếp | `list.sort(null)` | Sắp xếp tăng dần (phần tử cùng kiểu) |
| Chuyển mảng | `list.toArray()` | Chuyển list thành mảng |

```javascript
var list = [3, 1, 4, 1, 5,...];

// Kiểm tra
list.contains(4)          // true
list.isEmpty()            // false

// Thay thế phần tử
list.set(0, 99);          // [99, 1, 4, 1, 5]

// Tìm vị trí cuối
list.lastIndexOf(1)       // 3

// Danh sách con
var sub = list.subList(1, 3);    // [1, 4]

// Sắp xếp
list.sort(null);          // [1, 1, 3, 4, 5]

// Gộp 2 list
var list2 = [10, 20,...];
list.addAll(list2);       // [1, 1, 3, 4, 5, 10, 20]
```

---

### 12.3. Map (Bảng key-value)

```javascript
var map = {
    "a": "A",
    "b": 1000,
    "c": ["c1", "c2", 3]
};
```

| Thao tác | Cú pháp | Ví dụ | Kết quả |
|----------|---------|-------|---------|
| Truy cập (dấu chấm) | `map.key` | `map.a` | `"A"` |
| Truy cập (hàm) | `map.get("key")` | `map.get("a")` | `"A"` |
| Thêm/cập nhật | `map.put("key", value)` | `map.put("d", "D")` | - |
| Xóa | `map.remove("key")` | `map.remove("b")` | - |
| Kiểm tra key | `map.containsKey("key")` | `map.containsKey("b")` | `true` |

```javascript
// Ví dụ
var map = {"a": "A", "b": 1000, "c": ["c1", "c2", 3]};
map.put("a1", "A1");
map.remove("b");
return map.a + "-" + map.get("a1") + "-" + map.containsKey("b");
// "A-A1-false"
```

#### Các hàm Java Map bổ sung

Vì Map là `java.util.HashMap`, bạn có thể gọi thêm các hàm sau:

| Thao tác | Cú pháp | Mô tả |
|----------|---------|--------|
| Kiểm tra value | `map.containsValue(value)` | Kiểm tra giá trị có tồn tại không |
| Kích thước | `map.size()` | Số lượng cặp key-value |
| Kiểm tra rỗng | `map.isEmpty()` | Kiểm tra map có rỗng không |
| Xóa tất cả | `map.clear()` | Xóa toàn bộ |
| Lấy danh sách key | `map.keySet()` | Trả về tập hợp các key |
| Lấy danh sách value | `map.values()` | Trả về tập hợp các value |
| Lấy danh sách entries | `map.entrySet()` | Trả về tập hợp các cặp key-value |
| Giá trị mặc định | `map.getOrDefault("key", defaultVal)` | Lấy giá trị, trả về mặc định nếu không có key |
| Thêm nếu chưa có | `map.putIfAbsent("key", value)` | Chỉ thêm nếu key chưa tồn tại |
| Gộp map | `map.putAll(otherMap)` | Thêm toàn bộ từ map khác |

```javascript
var map = {"name": "Nguyen Van A", "age": 30, "city": "HCM"};

// Kiểm tra
map.containsValue("HCM")            // true
map.size()                           // 3
map.isEmpty()                        // false

// Giá trị mặc định
map.getOrDefault("phone", "N/A")     // "N/A"
map.getOrDefault("name", "N/A")      // "Nguyen Van A"

// Chỉ thêm nếu chưa có
map.putIfAbsent("name", "New Name")  // Không thay đổi (key đã tồn tại)
map.putIfAbsent("email", "a@example.com")  // Thêm mới

// Duyệt các key
var keys = map.keySet();
for (var key : keys) {
    // key: "name", "age", "city", "email"
}

// Duyệt các value
var vals = map.values();
for (var val : vals) {
    // val: "Nguyen Van A", 30, "HCM", "a@example.com"
}
```

---

## 13. Hàm Workspace

Đối tượng `Workspace` cung cấp các phương thức để tương tác với bản ghi (record) trong workspace hiện tại. Bạn có thể tạo, đọc, cập nhật và xóa bản ghi của bất kỳ loại đối tượng nào thông qua slug.

### Lấy instance Workspace

```javascript
var ws = Workspace.getInstance();
```

### 13.1. createRecord(objectSlug, data)

Tạo bản ghi mới cho loại đối tượng chỉ định.

**Tham số:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `objectSlug` | String | Slug của loại đối tượng (vd: `"lead"`, `"contact"`, `"deal"`) |
| `data` | Map | Map chứa các cặp field slug - giá trị cho bản ghi mới |

**Trả về:** `Map` với các key `r` (mã kết quả), `msg` (thông báo), `recordId` (ID bản ghi được tạo).

**Ví dụ:**

```javascript
var ws = Workspace.getInstance();
var record = ws.createRecord("lead", {
    "name": "Lead moi",
    "last_name": "Nguyen",
    "first_name": "Van A",
    "status": "new",
    "owner": "PER_SAMPLE_CREATOR"
});
return record;
```

### 13.2. getRecord(objectSlug, id)

Lấy một bản ghi theo ID.

**Tham số:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `objectSlug` | String | Slug của loại đối tượng |
| `id` | String | ID của bản ghi |

**Trả về:** `Map` với các key `r` (mã kết quả), `msg` (thông báo), `recordData` (map chứa giá trị các trường của bản ghi).

**Ví dụ:**

```javascript
var ws = Workspace.getInstance();
var record = ws.getRecord("lead", "PER_SAMPLE_CREATOR");
return record;
```

### 13.3. updateRecord(objectSlug, data)

Cập nhật bản ghi đã tồn tại. Trường `id` là **bắt buộc** trong map data.

**Tham số:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `objectSlug` | String | Slug của loại đối tượng |
| `data` | Map | Map chứa `id` (ID bản ghi) và các trường cần cập nhật |

**Trả về:** `Map` với các key `r` (mã kết quả), `msg` (thông báo), `recordId`.

**Ví dụ:**

```javascript
var ws = Workspace.getInstance();
var record = ws.updateRecord("lead", {
    "id": "PER_SAMPLE_CREATOR",
    "name": "Lead da cap nhat",
    "status": "contacted"
});
return record;
```

### 13.4. deleteRecord(objectSlug, id)

Xóa bản ghi theo ID.

**Tham số:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `objectSlug` | String | Slug của loại đối tượng |
| `id` | String | ID của bản ghi (phải có độ dài 10-20 ký tự) |

**Trả về:** `Map` với các key `r` (mã kết quả), `msg` (thông báo), `recordId`.

**Ví dụ:**

```javascript
var ws = Workspace.getInstance();
var record = ws.deleteRecord("lead", "PER_SAMPLE_CREATOR");
return record;
```

---

## 14. Giới hạn & An toàn

### 13.1. Thời gian thực thi

Mỗi script có giới hạn **tối đa 10 giây**. Nếu vượt quá, script sẽ bị dừng và báo lỗi timeout.

### 13.2. Giới hạn vòng lặp

Tổng số lần lặp của tất cả vòng lặp trong một script **không được vượt quá 10,000 lần**. Giới hạn này áp dụng cho `for`, `while`, và `for-each`.

```javascript
// OK: 100 lần lặp
for (var i = 0; i < 100; i++) {
    // ...
}

// OK: 5000 lần lặp
for (var i = 0; i < 5000; i++) {
    // ...
}

// LOI: Vuot qua 10,000 lan lap
for (var i = 0; i < 999999; i++) {
    // Se bao loi: "Loop iteration limit exceeded"
}
```

### 13.3. Sandbox (Hộp cát)

Script chạy trong môi trường cách ly, chỉ có thể sử dụng các hàm và kiểu dữ liệu được liệt kê trong tài liệu này. Không thể truy cập hệ thống file, mạng, hoặc các tài nguyên bên ngoài.

---

## 15. Công thức mẫu (Recipes)

### 15.1. Tính tuổi từ ngày sinh

```javascript
var today = Date.today();
var birthday = Date.valueOf("1990-05-15");
var age = today.getYear() - birthday.getYear();

// Điều chỉnh nếu chưa đến sinh nhật trong năm
if (today.getMonth() < birthday.getMonth()
    || (today.getMonth() == birthday.getMonth()
        && today.dayOfMonth() < birthday.dayOfMonth())) {
    age = age - 1;
}
return age;
```

### 15.2. Định dạng tiền tệ Việt Nam

```javascript
var amount = 1234567890;
return Number.format(amount, ".", ",", 0) + " VND";
// "1.234.567.890 VND"
```

### 15.3. Định dạng tiền tệ quốc tế (USD)

```javascript
var amount = 1234567.89;
return "$" + Number.format(amount, ",", ".", 2);
// "$1,234,567.89"
```

### 15.4. Kiểm tra SLA (Service Level Agreement)

```javascript
var created = Datetime.valueOf("2024-03-15 10:00:00");
var completed = Datetime.valueOf("2024-03-16 18:00:00");
var hours = completed.diffHours(created);

if (hours <= 48) {
    return "Dat SLA";
} else {
    return "Vuot SLA - " + hours + " gio";
}
```

### 15.5. Xử lý JSON response từ API

```javascript
var response = Json.parse($responseBody);
var message = response.body.content[0].text;
return message;
```

### 15.6. Tạo mã hóa đơn tự động

```javascript
var num = 42;
var code = "HD" + Text.lpad(Text.valueOf(num), 5, "0");
return code;    // "HD00042"
```

### 15.7. Tách và nối chuỗi

```javascript
// Tách email domain
var email = "user@example.com";
var parts = Text.split(email, "@");
var domain = parts[1];    // "example.com"

// Chuyển đổi format
var fullName = "Nguyen Van A";
var words = Text.split(fullName, " ");
return Text.join(words, "-");    // "Nguyen-Van-A"
```

### 15.8. Kiểm tra email hợp lệ (đơn giản)

```javascript
var email = "user@example.com";
var isValid = Text.matches(email, ".*@.*\\..*");
return isValid;    // true
```

### 15.9. Tính số ngày làm việc trong khoảng

```javascript
var start = Date.valueOf("2024-03-01");
var end = Date.valueOf("2024-03-31");
var totalDays = end.diffDays(start);
var workDays = 0;

for (var i = 0; i <= totalDays; i++) {
    var current = start.addDays(i);
    if (!current.isWeekend()) {
        workDays += 1;
    }
}
return workDays;
```

### 15.10. Xử lý SelectList có điều kiện

```javascript
// Kiểm tra và cập nhật danh sách lựa chọn
if (selectListField.containsOptionValue("VIP")) {
    selectListField.removeOptionByValue("Standard");
    selectListField.addOption("99", "priority", "Priority Support");
}
return selectListField;
```

### 15.11. Chuyển số từ định dạng Việt Nam sang số

```javascript
var vnNumber = "1.234.567,89";
var s = Number.stripChars(vnNumber, ".");
s = s.replace(",", ".");
var result = Number.toDouble(s);    // 1234567.89
return result;
```

### 15.12. Kiểm tra ngày có trong khoảng hay không

```javascript
var start = Date.valueOf("2024-01-01");
var end = Date.valueOf("2024-12-31");
var range = DateRange.of(start, end);

var checkDate = Date.today();
if (range.isInRange(checkDate)) {
    return "Trong nam 2024";
} else {
    return "Ngoai nam 2024";
}
```

---

> **Phiên bản tài liệu:** 1.13.0
