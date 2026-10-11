# Cú pháp template DOCX/XLSX được server hỗ trợ

Server render DOCX/XLSX bằng Apache Velocity Engine 2.3 nhưng chỉ trích biến, nạp context và bảo toàn cấu trúc file cho các cú pháp dưới đây; không suy rộng rằng mọi tính năng Velocity 2.3 đều an toàn trong OOXML. Bộ trích biến chỉ nhận các root/path ở mục Biến dữ liệu, nên không đổi sang `{{field}}`, `${record.field}`, `$!record.field` hoặc merge-field của hệ khác dù Velocity có thể hiểu một phần cú pháp đó.

## Biến dữ liệu

Chỉ dùng slug đã resolve từ `$object-info`; không dùng display name/bản dịch thay slug.

| Mục đích | Cú pháp | Ví dụ |
|---|---|---|
| Field của record chính | `$record.<field_slug>` | `$record.invoice_number` |
| Field qua lookup; nhiều cấp thì tiếp tục nối slug bằng `.` (mỗi đoạn phải là field lookup thật) | `$record.<lookup_slug>.<field_slug>` | `$record.customer.name`, `$record.customer.address.city` |
| Current user/personnel | `$currentUser.<field_slug>` | `$currentUser.full_name` |
| Danh sách liên quan; path bắt đầu bằng related-list slug thật, không phải object slug của item | `$relatedList.<related_list_slug>` | `$relatedList.invoice_items` |
| Field trong phần tử lặp; tên biến lặp gọn, ASCII | `$<loop_var>.<field_slug>` | `$item.product.name` |

Mảng/list dùng như một giá trị field thông thường được server nối khi hiển thị. Chỉ dùng `#foreach` cho related list hoặc list được truy vấn rõ ràng bằng `$object`.

### Truy vấn object nâng cao

Context `$object` lấy records hoặc options khi template thực sự cần danh sách không phải related list. Chỉ dùng `.where(...)`, `.sort(...)`, `.field(...)`, `.list()` theo chuỗi dưới đây; ưu tiên `$record` và `$relatedList` cho mapping file mẫu vì chúng gắn trực tiếp với record đang render.

```velocity
#foreach($row in $object.product.where("status", "equals", "active").sort("name", "asc").list())
$row.name
#end
#foreach($option in $object.order.field("status").list())
$option.value
#end
```

## Directive điều kiện và lặp

Code hiện nhận và xử lý `#if`, `#elseif`, `#else`, `#foreach`, `#end`. Giữ directive cân bằng và lồng nhau rõ ràng; dùng dấu nháy thẳng ASCII `"` trong biểu thức, không dùng smart quotes.

```velocity
#if($record.tax_code)
Mã số thuế: $record.tax_code
#else
Chưa có mã số thuế
#end

#foreach($item in $relatedList.invoice_items.sort("line_number", "asc"))
$item.product.name | $item.quantity | $item.amount.format()
#end
```

Sắp xếp related list: `.sort("field", "asc|desc")` là dạng rõ ràng nên dùng; `.sort("field")` dùng field đó theo `desc`; `.sort()` dùng `created desc`. Khi không gọi `.sort(...)`, thứ tự lấy từ request nếu client đã truyền, nếu không dùng `updated desc`. Server giới hạn tổng related records được nạp cho một list ở 2.000.

## Format giá trị

`.format()` không tham số để server dùng field metadata và cấu hình workspace (`$record.amount.format()`, `$record.invoice_date.format()`, `$record.duration.format()`); dùng pattern khi có yêu cầu hiển thị rõ:

```velocity
$record.amount.format("#,##0.00")
$record.total.format("currency")
$record.invoice_date.format("dd/MM/yyyy")
$record.created.format("dd/MM/yyyy HH:mm")
```

- Số: Java `DecimalFormat` pattern hoặc alias server hỗ trợ `numeric`, `decimal`, `currency`, `integer`, `percent`. Ngày/giờ: Java `SimpleDateFormat` pattern.
- Dùng dấu nháy thẳng ASCII quanh pattern. Renderer tự escape `#` bên trong method argument; không tự thêm `\#` vào file.
- Chỉ thêm `.format()` khi field đó được resolve từ metadata; gọi trên field không được nhận diện thì server có thể không nạp đúng formatter/context.

## Quy tắc riêng cho DOCX

1. Chỉ đặt token/directive trong main document body, gồm paragraph và table. Renderer không process header, footer, comment hoặc text box như main body; dữ liệu mẫu ở vùng không được hỗ trợ phải chuyển vào body hoặc báo giới hạn, không chèn token rồi coi là đã xong.
2. Giữ toàn bộ một token/directive trong một run hoặc các run có cùng style. Word có thể tách `$record.name` thành nhiều XML run; server chỉ gộp các run tương thích. Sau khi sửa, trích text/XML để chắc chắn token liền mạch.
3. Table loop: một row chỉ chứa `#foreach(...)`, một row mẫu ở giữa và một row chỉ chứa `#end`; server đánh dấu và xóa row directive rỗng sau render. Cấu trúc đầy đủ: [Loop bảng DOCX](template-examples.md#loop-bảng-docx).
4. Block nội dung thường: đặt directive ở paragraph riêng khi có thể; tránh bọc một phần XML phức tạp bằng directive nằm giữa các run khác style.
5. Giữ hyperlink tĩnh trừ khi ngữ cảnh đã chứng minh context cho URL động; bộ trích biến không quét relationship URL như text body.

## Quy tắc riêng cho XLSX

1. Đặt token/directive trong cell của worksheet. Renderer duyệt tất cả sheet và xử lý worksheet XML; comment, chart, shape hoặc metadata workbook không phải vị trí template được hỗ trợ.
2. Row loop: một row chỉ chứa `#foreach(...)` trong một cell riêng (các cell khác trống), một row mẫu duy nhất cho related item, một row chỉ chứa `#end`; renderer xóa hai row directive và đánh lại row/cell references cho các row clone. Không trộn `#foreach` và `#end` trong cùng row. Xóa các row dữ liệu mẫu còn lại trong vùng loop sau khi đã chuyển các cột sang `$item.<field_slug>`. Cấu trúc đầy đủ: [Loop dòng XLSX](template-examples.md#loop-dòng-xlsx).
3. Kiểm tra công thức, merged cells, named ranges và tham chiếu sau loop. Renderer có logic cập nhật row index và merge cell, nhưng file phức tạp vẫn phải được mở/render để xác minh.

## Mẫu sai hoặc chưa được hỗ trợ

| Không dùng | Lý do/cách thay |
|---|---|
| `{{record.name}}` | Placeholder của hệ khác; dùng `$record.name`. |
| `${record.name}` | Không thuộc dạng extractor hiện hỗ trợ; dùng `$record.name`. |
| `$!record.name` | Silent reference chưa được extractor hỗ trợ; dùng `$record.name`. |
| `$foreach.count`, `$velocityCount` | Counter chưa được contract chứng minh; resolve field thứ tự thật hoặc hỏi người dùng. |
| `#set`, `#macro`, `#include`, `#parse` | Không nằm trong nhóm directive được renderer DOCX/XLSX bảo toàn cấu trúc. |
| `#foreach(...) ... #end` trong cùng một row | Không tạo đúng block row clone; dùng ba row riêng. |
| Token nằm trong DOCX header/footer/text box | Renderer chỉ process main document body. |
| `$record.Tên khách hàng` | Display name/bản dịch không phải slug; resolve và dùng path kỹ thuật. |
| Token bị chia thành các run khác style | Có thể không được gộp; ghi lại token liền mạch và kiểm tra XML. |

## Kiểm tra trước upload

1. Mở lại file đã lưu và render trang/sheet để phát hiện file hỏng hoặc layout thay đổi.
2. Trích text từ main body DOCX hoặc từ tất cả worksheet XLSX; liệt kê mọi token/directive.
3. Đối chiếu từng `$record`, `$currentUser`, `$relatedList` và lookup path với metadata thật.
4. Mỗi loop variable được khai báo bởi `#foreach` và chỉ dùng trong block của nó; loop row/table đúng cấu trúc ba row.
5. Số block mở/đóng và thứ tự `#if`/`#elseif`/`#else`/`#foreach`/`#end` cân bằng.
6. Không còn `{{...}}`, `${...}`, merge field cũ, token bị tách hoặc giá trị mẫu còn sót tại các vị trí đã duyệt.
7. Các method argument dùng dấu nháy thẳng ASCII và `asc`/`desc` hợp lệ.
8. Chỉ chuyển file sang bước upload sau khi tất cả kiểm tra trên đạt.
