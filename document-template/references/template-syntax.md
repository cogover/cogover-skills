# Cú pháp template DOCX/XLSX được server hỗ trợ

## Mục lục

- [Nguồn và phạm vi](#nguồn-và-phạm-vi)
- [Biến dữ liệu](#biến-dữ-liệu)
- [Directive điều kiện và lặp](#directive-điều-kiện-và-lặp)
- [Format giá trị](#format-giá-trị)
- [Quy tắc riêng cho DOCX](#quy-tắc-riêng-cho-docx)
- [Quy tắc riêng cho XLSX](#quy-tắc-riêng-cho-xlsx)
- [Kiểm tra trước upload](#kiểm-tra-trước-upload)

## Nguồn và phạm vi

Server `import-export-server` render DOCX/XLSX bằng Apache Velocity Engine 2.3. Hướng dẫn này chỉ khuyến nghị cú pháp được code hiện tại trích biến, nạp context và xử lý cấu trúc file. Không suy rộng rằng mọi tính năng Velocity 2.3 đều an toàn trong OOXML.

Renderer hiện dùng:

- `ProcessTemplateDocxUtil` cho `.docx`;
- `ProcessTemplateXlsxUtil` cho `.xlsx`;
- `ExtractTextVariableUtil` để phát hiện biến và quyết định dữ liệu cần nạp.

Vì bộ trích biến chỉ nhận các root/path dưới đây, không đổi sang `{{field}}`, `${record.field}`, `$!record.field` hoặc merge-field của hệ khác dù Velocity có thể hiểu một phần cú pháp đó.

## Biến dữ liệu

Chỉ dùng slug đã resolve từ `$object-info`.

| Mục đích | Cú pháp | Ví dụ |
|---|---|---|
| Field của record chính | `$record.<field_slug>` | `$record.invoice_number` |
| Field qua lookup | `$record.<lookup_slug>.<field_slug>` | `$record.customer.name` |
| Field nhiều cấp | tiếp tục nối slug bằng `.` | `$record.customer.address.city` |
| Current user/personnel | `$currentUser.<field_slug>` | `$currentUser.full_name` |
| Danh sách liên quan | `$relatedList.<related_list_slug>` | `$relatedList.invoice_items` |
| Field trong phần tử lặp | `$<loop_var>.<field_slug>` | `$item.product.name` |

Dùng tên biến lặp gọn, ASCII, ví dụ `$item`. Không dùng display name/bản dịch thay slug. Lookup path phải đi qua field lookup thật; related-list path phải bắt đầu bằng related-list slug thật, không phải object slug của item.

Mảng/list dùng như một giá trị field thông thường được server nối khi hiển thị. Chỉ dùng `#foreach` cho related list hoặc list được truy vấn rõ ràng.

### Truy vấn object nâng cao

Server có context `$object` để lấy records hoặc options khi template thực sự cần danh sách không phải related list:

```velocity
#foreach($row in $object.product.where("status", "equals", "active").sort("name", "asc").list())
$row.name
#end
```

Lấy options của một field lựa chọn:

```velocity
#foreach($option in $object.order.field("status").list())
$option.value
#end
```

Chỉ dùng `.where(...)`, `.sort(...)`, `.field(...)`, `.list()` theo chuỗi trên. Ưu tiên `$record` và `$relatedList` cho mapping file mẫu vì chúng gắn trực tiếp với record đang render.

## Directive điều kiện và lặp

Code hiện nhận và xử lý các directive `#if`, `#elseif`, `#else`, `#foreach`, `#end`.

### Điều kiện

```velocity
#if($record.tax_code)
Mã số thuế: $record.tax_code
#else
Chưa có mã số thuế
#end
```

Giữ directive cân bằng và lồng nhau rõ ràng. Dùng dấu nháy thẳng ASCII `"`; không dùng smart quotes trong biểu thức.

### Related list

Không sắp xếp tại template:

```velocity
#foreach($item in $relatedList.invoice_items)
$item.product.name | $item.quantity | $item.amount.format()
#end
```

Sắp xếp rõ ràng:

```velocity
#foreach($item in $relatedList.invoice_items.sort("line_number", "asc"))
$item.product.name | $item.quantity
#end
```

`.sort()` dùng `created desc`; `.sort("field")` dùng field đó theo `desc`; `.sort("field", "asc|desc")` là dạng rõ ràng nên dùng. Khi không gọi `.sort(...)`, thứ tự lấy từ request nếu client đã truyền, nếu không dùng `updated desc`. Server giới hạn tổng related records được nạp cho một list ở 2.000.

Không khuyến nghị `#include`, `#parse`, macro tùy biến hoặc directive khác: code xử lý DOCX/XLSX không có logic bảo toàn cấu trúc cho chúng.

## Format giá trị

Gọi `.format()` trên field để server dùng field metadata và cấu hình workspace:

```velocity
$record.amount.format()
$record.invoice_date.format()
$record.duration.format()
```

Dùng pattern khi có yêu cầu hiển thị rõ:

```velocity
$record.amount.format("#,##0.00")
$record.total.format("currency")
$record.invoice_date.format("dd/MM/yyyy")
$record.created.format("dd/MM/yyyy HH:mm")
```

Quy tắc:

- Dùng Java `DecimalFormat` pattern cho số; các alias server hỗ trợ gồm `numeric`, `decimal`, `currency`, `integer`, `percent`.
- Dùng Java `SimpleDateFormat` pattern cho ngày/giờ.
- Dùng dấu nháy thẳng ASCII quanh pattern. Renderer tự escape `#` bên trong method argument; không tự thêm `\#` vào file.
- Chỉ thêm `.format()` khi field đó được resolve từ metadata. Nếu gọi trên field không được nhận diện, server có thể không nạp đúng formatter/context.

## Quy tắc riêng cho DOCX

1. Chỉ đặt token/directive trong main document body, gồm paragraph và table. Renderer hiện không process header, footer, comment hoặc text box như main body. Nếu dữ liệu mẫu nằm ở vùng không được hỗ trợ, di chuyển vào body hoặc báo giới hạn; không chèn token rồi coi là đã xong.
2. Giữ toàn bộ một token/directive trong một run hoặc các run có cùng style. Word có thể tách `$record.name` thành nhiều XML run; server chỉ gộp các run tương thích. Sau khi sửa, trích text/XML để chắc chắn token liền mạch.
3. Với table loop, dùng một row chỉ chứa `#foreach(...)`, một row mẫu ở giữa và một row chỉ chứa `#end`. Server đánh dấu và xóa row directive rỗng sau render.
4. Với block nội dung thường, đặt directive ở paragraph riêng khi có thể. Tránh bọc một phần XML phức tạp bằng directive nằm giữa các run khác style.
5. Giữ hyperlink tĩnh trừ khi ngữ cảnh đã chứng minh context cho URL động; bộ trích biến không quét relationship URL như text body.

Ví dụ cấu trúc table:

| Dòng | Nội dung |
|---|---|
| 1 | `#foreach($item in $relatedList.invoice_items.sort("line_number", "asc"))` |
| 2 | `$item.product.name` · `$item.quantity` · `$item.amount.format("#,##0.00")` |
| 3 | `#end` |

## Quy tắc riêng cho XLSX

1. Đặt token/directive trong cell của worksheet. Renderer duyệt tất cả sheet và xử lý worksheet XML; không coi comment, chart, shape hoặc metadata workbook là vị trí template đã được hỗ trợ.
2. Với loop theo row, tạo một row chỉ chứa `#foreach(...)`, một row mẫu ở giữa và một row chỉ chứa `#end`. Renderer xóa hai row directive và đánh lại row/cell references cho các row clone.
3. Đặt directive trong một cell riêng của row directive; để các cell khác trống. Không trộn `#foreach` và `#end` trong cùng row nếu mục tiêu là nhân bản row mẫu.
4. Kiểm tra công thức, merged cells, named ranges và tham chiếu sau loop. Renderer có logic cập nhật row index và merge cell, nhưng file phức tạp vẫn phải được mở/render để xác minh.
5. Giữ một row mẫu cho related item. Xóa các row dữ liệu mẫu còn lại trong vùng loop sau khi đã chuyển các cột sang `$item.<field_slug>`.

Ví dụ cấu trúc sheet:

| Row | A | B | C |
|---:|---|---|---|
| 5 | `#foreach($item in $relatedList.invoice_items.sort("line_number", "asc"))` | | |
| 6 | `$item.product.name` | `$item.quantity` | `$item.amount.format("#,##0.00")` |
| 7 | `#end` | | |

## Kiểm tra trước upload

1. Mở lại file đã lưu và render trang/sheet để phát hiện file hỏng hoặc layout thay đổi.
2. Trích text từ main body DOCX hoặc từ tất cả worksheet XLSX; liệt kê mọi token/directive.
3. Đối chiếu từng `$record`, `$currentUser`, `$relatedList` và lookup path với metadata thật.
4. Kiểm tra từng loop variable được khai báo bởi `#foreach` và chỉ dùng trong block của nó.
5. Kiểm tra số block mở/đóng và thứ tự `#if`/`#elseif`/`#else`/`#foreach`/`#end`.
6. Tìm và loại bỏ `{{...}}`, `${...}`, merge field cũ, token bị tách hoặc giá trị mẫu còn sót tại các vị trí đã duyệt.
7. Kiểm tra các method argument dùng dấu nháy thẳng ASCII và `asc`/`desc` hợp lệ.
8. Chỉ chuyển file sang bước upload sau khi tất cả kiểm tra trên đạt.
