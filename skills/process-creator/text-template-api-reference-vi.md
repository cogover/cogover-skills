# Text Template - API Reference

Text Template cho phép bạn tạo nội dung động bằng cách nhúng biến, điều kiện và vòng lặp vào văn bản. Cú pháp dựa trên [Apache Velocity Template Language (VTL)](https://velocity.apache.org/engine/2.3/user-guide.html).

---

## Mục lục

1. [Các loại dữ liệu](#1-các-loại-dữ-liệu)
2. [Cú pháp sử dụng](#2-cú-pháp-sử-dụng)
3. [Các hàm](#3-các-hàm)
4. [Giới hạn & An toàn](#4-giới-hạn--an-toàn)
5. [Công thức mẫu (Recipes)](#5-công-thức-mẫu-recipes)
6. [Bảng tham chiếu nhanh](#6-bảng-tham-chiếu-nhanh)

---

## 1. Các loại dữ liệu

| Kiểu dữ liệu | Mô tả | Ví dụ giá trị |
|---|---|---|
| **String** | Chuỗi ký tự | `"Nguyễn Văn A"` |
| **Number** | Số (Integer, Long, Double, BigDecimal) | `1234`, `99.5` |
| **Boolean** | Giá trị logic | `true`, `false` |
| **DateField** | Ngày (không có giờ) | `01/03/2026` |
| **DatetimeField** | Ngày và giờ (có timezone) | `2026/03/01 14:30:00` |
| **DateRangeField** | Khoảng ngày (từ ngày - đến ngày) | `["2026-01-01", "2026-12-31"]` |
| **DatetimeRangeField** | Khoảng ngày giờ (từ - đến) | — |
| **SelectListField** | Danh sách lựa chọn (đơn hoặc đa chọn) | — |
| **List** | Danh sách | `["a", "b", "c"]` |
| **Map** | Bảng key-value | `{"name": "A", "age": 25}` |

### Xử lý giá trị null

| Cài đặt | Mặc định | Mô tả |
|---|---|---|
| `convertNullNumberToZero` | `true` | Số null → `0` |
| `convertNullStringToEmpty` | `true` | Chuỗi null → `""` |

---

## 2. Cú pháp sử dụng

### 2.1. Tham chiếu biến

```velocity
## Tham chiếu cơ bản
$flow.hoTen

## Tham chiếu chính thức (khi biến nằm liền kề văn bản)
Xin chào ${flow.hoTen}!

## Giá trị thay thế (nếu biến null hoặc không tồn tại, dùng giá trị mặc định)
${flow.hoTen|'Không có tên'}
${flow.soLuong|0}

## Truy cập phần tử mảng
$flow.danhSach[0]
$flow.danhSach[0].tenSanPham

## Truy cập Map
$flow.thongTin["diaChi"]
```

### 2.2. Gán biến (`#set`)

```velocity
#set($tongTien = 0)
#set($hoTen = "Nguyễn Văn A")
#set($danhSach = ["A", "B", "C"])
#set($tongTien = $flow.donGia * $flow.soLuong)
```

**Lưu ý:** Vế phải của `#set` hỗ trợ: biến, chuỗi, số, phép toán, danh sách, map.

### 2.3. Điều kiện (`#if / #elseif / #else`)

```velocity
#if($flow.soTien > 1000000)
    Đơn hàng lớn
#elseif($flow.soTien > 100000)
    Đơn hàng trung bình
#else
    Đơn hàng nhỏ
#end
```

#### Toán tử so sánh

| Toán tử | Ý nghĩa | Dạng chữ |
|---|---|---|
| `==` | Bằng | `eq` |
| `!=` | Khác | `ne` |
| `<` | Nhỏ hơn | `lt` |
| `>` | Lớn hơn | `gt` |
| `<=` | Nhỏ hơn hoặc bằng | `le` |
| `>=` | Lớn hơn hoặc bằng | `ge` |

#### Toán tử logic

| Toán tử | Ý nghĩa | Dạng chữ |
|---|---|---|
| `&&` | VÀ | `and` |
| `\|\|` | HOẶC | `or` |
| `!` | PHỦ ĐỊNH | `not` |

```velocity
#if($flow.tuoi >= 18 && $flow.quocTich == "VN")
    Đủ điều kiện
#end
```

#### Quy tắc đánh giá true/false

| Kiểu | true | false |
|---|---|---|
| Boolean | `true` | `false` |
| String | Không null VÀ không rỗng | null hoặc `""` |
| Number | Khác 0 | `0` |
| Object | Không null | null |

### 2.4. Vòng lặp (`#foreach`)

```velocity
#foreach($item in $flow.danhSachSanPham)
    $foreach.count. $item.tenSanPham - $item.giaBan
#end
```

#### Biến vòng lặp có sẵn

| Biến | Kiểu | Mô tả |
|---|---|---|
| `$foreach.count` | int | Số thứ tự (bắt đầu từ 1) |
| `$foreach.index` | int | Chỉ số (bắt đầu từ 0) |
| `$foreach.first` | boolean | `true` nếu là phần tử đầu tiên |
| `$foreach.last` | boolean | `true` nếu là phần tử cuối cùng |
| `$foreach.hasNext` | boolean | `true` nếu còn phần tử tiếp theo |

#### Dùng `#break` để thoát sớm

```velocity
#foreach($item in $flow.danhSach)
    #if($foreach.count > 10)
        #break
    #end
    $item.ten
#end
```

#### Dùng Range để lặp số

```velocity
#foreach($i in [1..5])
    Dòng $i
#end
## Kết quả: Dòng 1, Dòng 2, ..., Dòng 5
```

### 2.5. Toán tử số học

```velocity
#set($tong = $flow.a + $flow.b)       ## Cộng
#set($hieu = $flow.a - $flow.b)       ## Trừ
#set($tich = $flow.a * $flow.b)       ## Nhân
#set($thuong = $flow.a / $flow.b)     ## Chia (kết quả nguyên)
#set($du = $flow.a % $flow.b)         ## Chia lấy dư
```

### 2.6. Chuỗi ký tự

```velocity
## Nháy kép: nội suy biến
#set($loiChao = "Xin chào $flow.hoTen")

## Nháy đơn: giữ nguyên
#set($mau = '$flow.hoTen')
## Kết quả: $flow.hoTen (chuỗi gốc, không nội suy)
```

### 2.7. Chú thích (Comments)

```velocity
## Đây là chú thích một dòng

#*
  Đây là chú thích
  nhiều dòng
*#
```

---

## 3. Các hàm

### 3.1. Hàm tiện ích — `$Util`

#### JSON

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$Util.toJsonArray(list)` | Chuyển List thành chuỗi JSON Array | `$Util.toJsonArray(["a","b"])` | `["a", "b"]` |
| `$Util.escapeJson(str)` | Escape ký tự đặc biệt cho JSON | `$Util.escapeJson('Anh "A"')` | `Anh \"A\"` |

> `escapeJson` xử lý: `"` → `\"`, `\` → `\\`, xuống dòng → `\n`, tab → `\t`

#### HTML

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$Util.escapeHtml(str)` | Escape ký tự đặc biệt cho HTML | `$Util.escapeHtml("<b>bold</b>")` | `&lt;b&gt;bold&lt;/b&gt;` |

> `escapeHtml` xử lý: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, `'` → `&#39;`

#### URL

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$Util.urlEncode(str)` | URL encode chuỗi | `$Util.urlEncode("Nguyễn Văn A")` | `Nguy%E1%BB%85n+V%C4%83n+A` |

#### Chuỗi

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$Util.join(list, separator)` | Nối list thành chuỗi | `$Util.join(["A","B","C"], ", ")` | `A, B, C` |

#### Collection

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$Util.size(collection)` | Đếm số phần tử (List, Map, Array) | `$Util.size($flow.items)` | `5` |
| `$Util.sort(list, field)` | Sắp xếp list theo field (tăng dần) | `$Util.sort($flow.items, "ten")` | List đã sắp xếp |

#### Ngày giờ hiện tại

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$Util.today()` | Ngày hiện tại (DateField) | `$Util.today().format("dd/MM/yyyy")` | `04/03/2026` |
| `$Util.now()` | Thời điểm hiện tại (DatetimeField, theo timezone workspace) | `$Util.now().format("HH:mm:ss")` | `14:30:00` |

> `$Util.today()` và `$Util.now()` trả về DateField/DatetimeField, có thể gọi chain tất cả hàm ngày tháng:
> `$Util.today().addDays(30).format("dd/MM/yyyy")` — 30 ngày sau hôm nay

---

### 3.2. Hàm số — `$number`

#### Định dạng số

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$number.format(value)` | Định dạng theo locale workspace | `$number.format(1234567.89)` | `1,234,567.89` hoặc `1.234.567,89` |
| `$number.format(value, thousandSep, decimalSep)` | Tùy chọn dấu phân cách | `$number.format(1234567.89, ".", ",")` | `1.234.567,89` |
| `$number.format(value, thousandSep, decimalSep, decimalPlaces)` | Tùy chọn số chữ số thập phân | `$number.format(1234567.89, ",", ".", 0)` | `1,234,568` |

**Các kiểu locale workspace:**

| Locale | Định dạng | Ví dụ |
|---|---|---|
| Locale 1 (Mỹ/Anh) | `1,234,567.89` | dấu `,` ngăn hàng nghìn, dấu `.` thập phân |
| Locale 2 (Việt Nam/Đức) | `1.234.567,89` | dấu `.` ngăn hàng nghìn, dấu `,` thập phân |

#### Chuyển đổi kiểu số

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$number.toNumber(value)` | Chuyển thành Number | `$number.toNumber("123.45")` | `123.45` |
| `$number.toInteger(value)` | Chuyển thành Integer | `$number.toInteger("123.99")` | `123` |
| `$number.toLong(value)` | Chuyển thành Long | `$number.toLong("9999999999")` | `9999999999` |
| `$number.toDouble(value)` | Chuyển thành Double | `$number.toDouble("123.45")` | `123.45` |

#### Kiểm tra

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$number.isNumber(value)` | Kiểm tra có phải số không | `$number.isNumber("abc")` | `false` |

#### Toán học

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$number.round(value, scale)` | Làm tròn | `$number.round(1234.567, 2)` | `1234.57` |
| `$number.ceil(value)` | Làm tròn lên | `$number.ceil(1234.1)` | `1235` |
| `$number.floor(value)` | Làm tròn xuống | `$number.floor(1234.9)` | `1234` |
| `$number.abs(value)` | Giá trị tuyệt đối | `$number.abs(-5)` | `5.0` |
| `$number.min(a, b)` | Giá trị nhỏ nhất | `$number.min(3, 7)` | `3.0` |
| `$number.max(a, b)` | Giá trị lớn nhất | `$number.max(3, 7)` | `7.0` |

#### Xóa ký tự

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `$number.strip(value)` | Xóa tất cả `,` và `.` | `$number.strip("1,234,567.89")` | `"123456789"` |
| `$number.stripGrouping(value)` | Chỉ xóa dấu `,` (giữ `.`) | `$number.stripGrouping("1,234,567.89")` | `"1234567.89"` |
| `$number.stripChars(value, chars)` | Xóa ký tự tùy chọn | `$number.stripChars("1.234.567,89", ".")` | `"1234567,89"` |

---

### 3.3. Hàm của DateField (Ngày)

Các hàm gọi trên biến kiểu DateField.

#### Định dạng

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `.format(pattern)` | Định dạng ngày theo mẫu | `$flow.ngay.format("dd/MM/yyyy")` | `01/03/2026` |
| `.format(pattern)` | Mẫu khác | `$flow.ngay.format("yyyy-MM-dd")` | `2026-03-01` |

#### Cộng/trừ ngày

| Hàm | Mô tả | Ví dụ |
|---|---|---|
| `.addDays(n)` | Cộng/trừ ngày | `$flow.ngay.addDays(7)` → 7 ngày sau |
| `.addMonths(n)` | Cộng/trừ tháng | `$flow.ngay.addMonths(-1)` → tháng trước |
| `.addYears(n)` | Cộng/trừ năm | `$flow.ngay.addYears(1)` → năm sau |

> Trả về DateField mới, có thể gọi chain: `$flow.ngay.addMonths(1).format("dd/MM/yyyy")`

#### Lấy thành phần ngày

| Hàm | Mô tả | Kết quả ví dụ |
|---|---|---|
| `.getYear()` | Năm | `2026` |
| `.getMonth()` | Tháng (1–12) | `3` |
| `.dayOfMonth()` | Ngày trong tháng (1–31) | `15` |
| `.dayOfYear()` | Ngày trong năm (1–366) | `74` |
| `.dayOfWeek()` | Ngày trong tuần (Thứ 2=1 → CN=7) | `1` |

#### So sánh và tính toán

| Hàm | Mô tả | Ví dụ |
|---|---|---|
| `.diffDays(other)` | Khoảng cách ngày (this − other) | `$flow.ngayKT.diffDays($flow.ngayBD)` → `30` |
| `.isBefore(other)` | Có trước ngày khác? | `$flow.ngay1.isBefore($flow.ngay2)` → `true` |
| `.isAfter(other)` | Có sau ngày khác? | `$flow.ngay1.isAfter($flow.ngay2)` → `false` |
| `.isWeekend()` | Có phải cuối tuần? | `$flow.ngay.isWeekend()` → `false` |

---

### 3.4. Hàm của DatetimeField (Ngày giờ)

Các hàm gọi trên biến kiểu DatetimeField.

#### Định dạng

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `.format(pattern)` | Định dạng theo mẫu (UTC) | `$flow.thoiGian.format("dd/MM/yyyy HH:mm:ss")` | `01/03/2026 14:30:00` |
| `.format()` | Định dạng mặc định workspace | `$flow.thoiGian.format()` | `2026/03/01 14:30:00` |
| `.formatWithAccountTimeZone(pattern)` | Định dạng theo timezone tài khoản | `$flow.thoiGian.formatWithAccountTimeZone("HH:mm")` | `21:30` |
| `.timestamp()` | Lấy timestamp (milliseconds) | `$flow.thoiGian.timestamp()` | `1772195400000` |

#### Cộng/trừ thời gian

| Hàm | Mô tả |
|---|---|
| `.addDays(n)` | Cộng/trừ ngày |
| `.addHours(n)` | Cộng/trừ giờ |
| `.addMinutes(n)` | Cộng/trừ phút |
| `.addMonths(n)` | Cộng/trừ tháng |

> Trả về DatetimeField mới, có thể gọi chain: `$flow.thoiGian.addHours(2).format("HH:mm")`

#### Lấy thành phần

| Hàm | Mô tả |
|---|---|
| `.getYear()` | Năm |
| `.getMonth()` | Tháng (1–12) |
| `.getDayOfMonth()` | Ngày trong tháng |
| `.getHour()` | Giờ (0–23) |
| `.getMinute()` | Phút (0–59) |
| `.getSecond()` | Giây (0–59) |

#### So sánh và tính toán

| Hàm | Mô tả |
|---|---|
| `.diffDays(other)` | Khoảng cách ngày (this − other) |
| `.diffHours(other)` | Khoảng cách giờ |
| `.diffMinutes(other)` | Khoảng cách phút |
| `.isBefore(other)` | Có trước thời điểm khác? |
| `.isAfter(other)` | Có sau thời điểm khác? |

---

### 3.5. Hàm của DateRangeField (Khoảng ngày)

| Hàm | Mô tả | Ví dụ |
|---|---|---|
| `.getStart()` | Lấy ngày bắt đầu (DateField) | `$flow.khoangNgay.getStart().format("dd/MM/yyyy")` |
| `.getEnd()` | Lấy ngày kết thúc (DateField) | `$flow.khoangNgay.getEnd()` |
| `.range()` | Số ngày trong khoảng | `$flow.khoangNgay.range()` → `30` |
| `.isInRange(date)` | Kiểm tra ngày có nằm trong khoảng | `$flow.khoangNgay.isInRange($flow.ngayKiemTra)` → `true` |

---

### 3.6. Hàm của DatetimeRangeField (Khoảng ngày giờ)

| Hàm | Mô tả | Ví dụ |
|---|---|---|
| `.getStart()` | Lấy thời điểm bắt đầu (DatetimeField) | `$flow.khoangTG.getStart().format("HH:mm")` |
| `.getEnd()` | Lấy thời điểm kết thúc (DatetimeField) | `$flow.khoangTG.getEnd()` |
| `.range()` | Khoảng cách (milliseconds) | `$flow.khoangTG.range()` |
| `.isInRange(datetime)` | Kiểm tra thời điểm có nằm trong khoảng | `$flow.khoangTG.isInRange($flow.thoiGianKT)` |

---

### 3.7. Hàm của SelectListField (Danh sách lựa chọn)

| Hàm | Mô tả | Ví dụ |
|---|---|---|
| `.getValue()` | Lấy giá trị đã chọn | `$flow.trangThai.getValue()` → `2` (đơn chọn) hoặc `[2, 3]` (đa chọn) |
| `.getSelectedOption()` | Lấy option đầu tiên đã chọn | `$flow.trangThai.getSelectedOption()` |
| `.getSelectedOptions()` | Lấy tất cả options đã chọn (List) | `$flow.trangThai.getSelectedOptions()` |

```velocity
## Ví dụ: Điều kiện theo giá trị SelectList
#if($flow.trangThai.getValue() == 1)
    Đang xử lý
#elseif($flow.trangThai.getValue() == 2)
    Đã hoàn thành
#else
    Đã hủy
#end
```

---

### 3.8. Hàm của String (Chuỗi)

Các hàm gọi trực tiếp trên biến kiểu String.

| Hàm | Mô tả | Ví dụ | Kết quả |
|---|---|---|---|
| `.toLowerCase()` | Chuyển thành chữ thường | `$flow.email.toLowerCase()` | `"nguyen@example.com"` |
| `.toUpperCase()` | Chuyển thành chữ hoa | `$flow.maSo.toUpperCase()` | `"DH-001"` |
| `.trim()` | Xóa khoảng trắng đầu/cuối | `$flow.ten.trim()` | `"Nguyễn Văn A"` |
| `.replace(old, new)` | Thay thế chuỗi | `$flow.sdt.replace("-", "")` | `"0901234567"` |
| `.contains(str)` | Kiểm tra chứa chuỗi con | `$flow.email.contains("@gmail")` | `true` |
| `.length()` | Độ dài chuỗi | `$flow.ghiChu.length()` | `50` |
| `.substring(start, end)` | Cắt chuỗi (từ vị trí start đến end) | `$flow.maSo.substring(0, 3)` | `"DH-"` |
| `.startsWith(str)` | Kiểm tra bắt đầu bằng | `$flow.sdt.startsWith("09")` | `true` |
| `.endsWith(str)` | Kiểm tra kết thúc bằng | `$flow.file.endsWith(".pdf")` | `true` |
| `.isEmpty()` | Kiểm tra chuỗi rỗng | `$flow.ghiChu.isEmpty()` | `false` |
| `.split(delimiter)` | Tách chuỗi thành mảng | `$flow.tags.split(",")` | `["tag1", "tag2"]` |

```velocity
## Ví dụ: Chuẩn hóa email trước khi gửi
#set($email = $flow.email.trim().toLowerCase())

## Ví dụ: Kiểm tra và hiển thị
#if(!$flow.ghiChu.isEmpty())
    Ghi chú: $flow.ghiChu
#end

## Ví dụ: Tách tags và lặp
#foreach($tag in $flow.tags.split(","))
    - $tag.trim()
#end
```

---

## 4. Giới hạn & An toàn

### 4.1. Chỉ thị bị chặn

Các chỉ thị sau **KHÔNG** được phép sử dụng:

| Chỉ thị | Lý do |
|---|---|
| `#include()` | Không cho phép đọc file |
| `#parse()` | Không cho phép đọc và xử lý file |
| `#macro()` | Không cho phép định nghĩa macro |
| `#define()` | Không cho phép định nghĩa block |
| `#evaluate()` | Không cho phép thực thi template động |
| `#stop()` | Không cho phép dừng toàn bộ rendering |

### 4.2. Phương thức được phép

Chỉ các phương thức nằm trong danh sách trắng (whitelist) mới được gọi. Mọi phương thức không nằm trong danh sách sẽ bị từ chối khi lưu template.

### 4.3. Giới hạn vòng lặp

Số vòng lặp tối đa: **1000**. Nếu vượt quá, template sẽ dừng xử lý.

### 4.4. Không truy cập hệ thống file

Template chạy hoàn toàn trong bộ nhớ (StringResourceLoader), không có khả năng đọc/ghi file trên server.

---

## 5. Công thức mẫu (Recipes)

### 5.1. Thay thế biến cơ bản

```velocity
Kính gửi: $flow.hoTen
Địa chỉ: $flow.diaChi
Số điện thoại: $flow.soDienThoai
```

### 5.2. Nội dung có điều kiện

```velocity
#if($flow.gioiTinh == "Nam")
    Ông $flow.hoTen
#else
    Bà $flow.hoTen
#end
```

### 5.3. Bảng danh sách sản phẩm

```velocity
#set($tongTien = 0)
<table>
  <tr><th>STT</th><th>Sản phẩm</th><th>Đơn giá</th><th>SL</th><th>Thành tiền</th></tr>
  #foreach($sp in $flow.danhSachSP)
    #set($thanhTien = $sp.donGia * $sp.soLuong)
    #set($tongTien = $tongTien + $thanhTien)
    <tr>
      <td>$foreach.count</td>
      <td>$sp.tenSP</td>
      <td>$number.format($sp.donGia)</td>
      <td>$sp.soLuong</td>
      <td>$number.format($thanhTien)</td>
    </tr>
  #end
  <tr><td colspan="4">Tổng cộng</td><td>$number.format($tongTien)</td></tr>
</table>
```

### 5.4. Định dạng số tiền

```velocity
## Theo locale workspace
Số tiền: $number.format($flow.soTien)

## Kiểu Việt Nam: 1.234.567,89
Số tiền: $number.format($flow.soTien, ".", ",") đồng

## Làm tròn
Tổng: $number.format($number.round($flow.soTien, 0), ".", ",") VNĐ
```

### 5.5. Xử lý SelectList

```velocity
#if($flow.loaiKhachHang.getValue() == "VIP")
    Kính gửi Quý khách VIP $flow.hoTen,
    Chúng tôi xin gửi ưu đãi đặc biệt...
#elseif($flow.loaiKhachHang.getValue() == "Regular")
    Kính gửi $flow.hoTen,
    Cảm ơn bạn đã sử dụng dịch vụ...
#end
```

### 5.6. Xử lý ngày tháng

```velocity
## Định dạng ngày
Ngày tạo: $flow.ngayTao.format("dd/MM/yyyy")

## Tính ngày hết hạn (30 ngày sau)
Hạn thanh toán: $flow.ngayTao.addDays(30).format("dd/MM/yyyy")

## Tính số ngày còn lại
Còn $flow.ngayHetHan.diffDays($flow.ngayHienTai) ngày

## Kiểm tra cuối tuần
#if($flow.ngayGiao.isWeekend())
    Lưu ý: Ngày giao rơi vào cuối tuần
#end
```

### 5.7. Xử lý khoảng ngày

```velocity
## Thông tin khoảng ngày
Từ: $flow.khoangNgay.getStart().format("dd/MM/yyyy")
Đến: $flow.khoangNgay.getEnd().format("dd/MM/yyyy")
Tổng: $flow.khoangNgay.range() ngày

## Kiểm tra ngày có nằm trong khoảng
#if($flow.khoangNgay.isInRange($flow.ngayKiemTra))
    Ngày nằm trong khoảng cho phép
#else
    Ngày nằm ngoài khoảng
#end
```

### 5.8. Xử lý ngày giờ

```velocity
## Hiển thị theo timezone tài khoản
Thời gian: $flow.thoiGian.formatWithAccountTimeZone("dd/MM/yyyy HH:mm")

## Tính deadline (thêm 2 giờ)
Deadline: $flow.thoiGian.addHours(2).format("HH:mm")

## Số giờ chênh lệch
Thời gian xử lý: $flow.thoiGianKT.diffHours($flow.thoiGianBD) giờ
```

### 5.9. Truy cập đối tượng lồng nhau

```velocity
## Truy cập field lồng nhau
$flow.khachHang.diaChi.thanhPho

## Truy cập phần tử mảng
$flow.ketQua.choices[0].message.role

## Kết hợp mảng và field
#foreach($record in $action.layDuLieu.output.records)
    $record.maSo - $record.tenKH
#end
```

### 5.10. Tạo JSON Array

```velocity
## Chuyển danh sách thành chuỗi JSON
$Util.toJsonArray($flow.danhSachSDT)
## Kết quả: ["0901234567", "0912345678"]
```

### 5.11. Build JSON body cho HTTP Request

```velocity
{
  "name": "$Util.escapeJson($flow.hoTen)",
  "email": "$flow.email.trim().toLowerCase()",
  "phone": "$flow.sdt.replace("-", "")",
  "amount": $number.toDouble($flow.soTien),
  "created_at": "$Util.now().format("yyyy-MM-dd'T'HH:mm:ss")",
  "tags": $Util.toJsonArray($flow.tags),
  "note": "$Util.escapeJson(${flow.ghiChu|''})"
}
```

### 5.12. Email template HTML

```velocity
<h2>Xác nhận đơn hàng #$flow.maDon</h2>
<p>Kính gửi $flow.hoTen,</p>
<p>Đơn hàng của bạn đã được tiếp nhận ngày $Util.today().format("dd/MM/yyyy").</p>

<table border="1">
  <tr><th>STT</th><th>Sản phẩm</th><th>SL</th><th>Thành tiền</th></tr>
  #foreach($sp in $flow.danhSachSP)
  <tr>
    <td>$foreach.count</td>
    <td>$Util.escapeHtml($sp.tenSP)</td>
    <td>$sp.soLuong</td>
    <td>$number.format($sp.donGia * $sp.soLuong, ".", ",") đ</td>
  </tr>
  #end
</table>

#if(!$flow.ghiChu.isEmpty())
<p><strong>Ghi chú:</strong> $Util.escapeHtml($flow.ghiChu)</p>
#end
```

### 5.13. URL với query parameters

```velocity
https://api.example.com/search?q=$Util.urlEncode($flow.tuKhoa)&page=1
```

### 5.14. Sắp xếp và đếm danh sách

```velocity
## Đếm số phần tử
Tổng: $Util.size($flow.danhSachSP) sản phẩm

## Sắp xếp theo tên
#foreach($sp in $Util.sort($flow.danhSachSP, "tenSP"))
    $foreach.count. $sp.tenSP
#end
```

### 5.15. Ngày giờ hiện tại

```velocity
## Ngày hôm nay
Ngày in: $Util.today().format("dd/MM/yyyy")

## Thời gian hiện tại
Lúc: $Util.now().format("HH:mm dd/MM/yyyy")

## Hạn thanh toán = hôm nay + 30 ngày
Hạn thanh toán: $Util.today().addDays(30).format("dd/MM/yyyy")

## So sánh với ngày hiện tại
#if($flow.ngayHetHan.isBefore($Util.today()))
    ĐÃ HẾT HẠN
#end
```

---

## 6. Bảng tham chiếu nhanh

### Biến hệ thống

| Tiền tố | Mô tả | Ví dụ |
|---|---|---|
| `$flow` | Biến flow | `$flow.hoTen` |
| `$currentUser` | Thông tin người dùng hiện tại | `$currentUser.email` |
| `$userTask` | Dữ liệu màn hình nhập liệu | `$userTask.formNhap.hoTen` |
| `$action` | Kết quả của action | `$action.layDuLieu.output.records` |
| `$loop` | Biến trong vòng lặp workflow | `$loop.xuLyDon.currentItem.maSo` |

### Chỉ thị được phép

| Chỉ thị | Mô tả |
|---|---|
| `#set($var = value)` | Gán biến |
| `#if(condition)` | Điều kiện |
| `#elseif(condition)` | Điều kiện khác |
| `#else` | Nhánh mặc định |
| `#foreach($item in $list)` | Vòng lặp |
| `#break` | Thoát vòng lặp |
| `#end` | Kết thúc khối |
| `## comment` | Chú thích một dòng |
| `#* comment *#` | Chú thích nhiều dòng |

### Tất cả hàm — Tham chiếu nhanh

| Hàm | Đối tượng | Mô tả |
|---|---|---|
| `$Util.toJsonArray(list)` | Util | Chuyển list thành JSON array |
| `$Util.escapeJson(str)` | Util | Escape ký tự cho JSON |
| `$Util.escapeHtml(str)` | Util | Escape ký tự cho HTML |
| `$Util.urlEncode(str)` | Util | URL encode chuỗi |
| `$Util.join(list, sep)` | Util | Nối list thành chuỗi |
| `$Util.size(collection)` | Util | Đếm số phần tử |
| `$Util.sort(list, field)` | Util | Sắp xếp list theo field |
| `$Util.today()` | Util | Ngày hiện tại (DateField) |
| `$Util.now()` | Util | Thời điểm hiện tại (DatetimeField) |
| `$number.format(value, ...)` | number | Định dạng số |
| `$number.toNumber(value)` | number | Chuyển thành Number |
| `$number.toInteger(value)` | number | Chuyển thành Integer |
| `$number.toLong(value)` | number | Chuyển thành Long |
| `$number.toDouble(value)` | number | Chuyển thành Double |
| `$number.isNumber(value)` | number | Kiểm tra có phải số |
| `$number.round(value, scale)` | number | Làm tròn |
| `$number.ceil(value)` | number | Làm tròn lên |
| `$number.floor(value)` | number | Làm tròn xuống |
| `$number.abs(value)` | number | Giá trị tuyệt đối |
| `$number.min(a, b)` | number | Giá trị nhỏ nhất |
| `$number.max(a, b)` | number | Giá trị lớn nhất |
| `$number.strip(value)` | number | Xóa `,` và `.` |
| `$number.stripGrouping(value)` | number | Xóa dấu ngăn hàng nghìn |
| `$number.stripChars(value, chars)` | number | Xóa ký tự tùy chọn |
| `.format(pattern)` | DateField | Định dạng ngày |
| `.addDays(n)` | DateField | Cộng/trừ ngày |
| `.addMonths(n)` | DateField | Cộng/trừ tháng |
| `.addYears(n)` | DateField | Cộng/trừ năm |
| `.getYear()` | DateField | Lấy năm |
| `.getMonth()` | DateField | Lấy tháng |
| `.dayOfMonth()` | DateField | Ngày trong tháng |
| `.dayOfYear()` | DateField | Ngày trong năm |
| `.dayOfWeek()` | DateField | Ngày trong tuần |
| `.diffDays(other)` | DateField | Khoảng cách ngày |
| `.isBefore(other)` | DateField | So sánh trước |
| `.isAfter(other)` | DateField | So sánh sau |
| `.isWeekend()` | DateField | Kiểm tra cuối tuần |
| `.format(pattern)` | DatetimeField | Định dạng ngày giờ |
| `.format()` | DatetimeField | Định dạng mặc định |
| `.formatWithAccountTimeZone(pattern)` | DatetimeField | Định dạng theo TZ tài khoản |
| `.timestamp()` | DatetimeField | Lấy timestamp (ms) |
| `.addDays(n)` | DatetimeField | Cộng/trừ ngày |
| `.addHours(n)` | DatetimeField | Cộng/trừ giờ |
| `.addMinutes(n)` | DatetimeField | Cộng/trừ phút |
| `.addMonths(n)` | DatetimeField | Cộng/trừ tháng |
| `.getYear()` | DatetimeField | Lấy năm |
| `.getMonth()` | DatetimeField | Lấy tháng |
| `.getDayOfMonth()` | DatetimeField | Ngày trong tháng |
| `.getHour()` | DatetimeField | Lấy giờ |
| `.getMinute()` | DatetimeField | Lấy phút |
| `.getSecond()` | DatetimeField | Lấy giây |
| `.diffDays(other)` | DatetimeField | Khoảng cách ngày |
| `.diffHours(other)` | DatetimeField | Khoảng cách giờ |
| `.diffMinutes(other)` | DatetimeField | Khoảng cách phút |
| `.isBefore(other)` | DatetimeField | So sánh trước |
| `.isAfter(other)` | DatetimeField | So sánh sau |
| `.getStart()` | DateRangeField | Ngày bắt đầu |
| `.getEnd()` | DateRangeField | Ngày kết thúc |
| `.range()` | DateRangeField | Số ngày trong khoảng |
| `.isInRange(date)` | DateRangeField | Kiểm tra trong khoảng |
| `.getStart()` | DatetimeRangeField | Thời điểm bắt đầu |
| `.getEnd()` | DatetimeRangeField | Thời điểm kết thúc |
| `.range()` | DatetimeRangeField | Khoảng cách (ms) |
| `.isInRange(datetime)` | DatetimeRangeField | Kiểm tra trong khoảng |
| `.getValue()` | SelectListField | Lấy giá trị đã chọn |
| `.getSelectedOption()` | SelectListField | Lấy option đã chọn |
| `.getSelectedOptions()` | SelectListField | Lấy tất cả options đã chọn |
| `.toLowerCase()` | String | Chuyển thành chữ thường |
| `.toUpperCase()` | String | Chuyển thành chữ hoa |
| `.trim()` | String | Xóa khoảng trắng đầu/cuối |
| `.replace(old, new)` | String | Thay thế chuỗi |
| `.contains(str)` | String | Kiểm tra chứa chuỗi con |
| `.length()` | String | Độ dài chuỗi |
| `.substring(start, end)` | String | Cắt chuỗi |
| `.startsWith(str)` | String | Kiểm tra bắt đầu bằng |
| `.endsWith(str)` | String | Kiểm tra kết thúc bằng |
| `.isEmpty()` | String | Kiểm tra chuỗi rỗng |
| `.split(delimiter)` | String | Tách chuỗi thành mảng |
