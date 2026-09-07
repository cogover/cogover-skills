---
name: document-template
description: Quản lý và kiểm thử tài liệu mẫu (document template/document sample) của Cogover, gồm đọc và phân loại file Word/Excel, mapping dữ liệu mẫu sang object fields, chuyển DOCX/XLSX thành Apache Velocity template, liệt kê, xem chi tiết, tạo, cập nhật, xóa, upload file, tạo mẫu HTML, tạo fixture đại diện và kiểm thử export end-to-end bằng Chrome sau create. Dùng khi cần tạo document template từ file có dữ liệu thực tế, xác minh placeholder, tự động hóa cấu hình tài liệu mẫu, thay file mẫu, đổi HTML, kiểm tra file export với record thật, liệt kê layout Xem/Sửa hoặc Tạo/Xem/Sửa, hoặc tùy chọn tạo Object Button xuất theo mẫu văn bản và đưa button lên layout đã chọn; ngoài bước hậu kiểm export qua Chrome, mọi cấu hình và dữ liệu đều thao tác qua API.
metadata:
  author: cogover
  version: "1.0.1"
---

# Document Template

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

## Điều kiện môi trường

Cần khả năng gọi HTTP và đọc/ghi file. Kiểm thử export end-to-end còn cần trình duyệt đã đăng nhập, giữ tab mở và lấy được file download. Dùng công cụ browser automation sẵn có của môi trường, không phụ thuộc tên plugin cố định. Nếu thiếu công cụ này, hoàn tất phần chuẩn bị/cấu hình đã được phép, bàn giao các bước kiểm thử thủ công và ghi rõ export end-to-end chưa được xác minh; không báo PASS hoặc tiếp tục bước phụ thuộc kết quả đó.

## Phạm vi

- Dùng API cho cấu hình template, fixture và lệnh export. Chỉ dùng công cụ điều khiển trình duyệt có khả năng giữ phiên Workspace và theo dõi download để mở record test, giữ Web App nhận websocket và lấy file do Web App tự tải trong bước kiểm thử end-to-end sau create; không thao tác UI để tạo/sửa cấu hình.
- Quản lý hai mode đã được front-end hỗ trợ:
  - upload file Word `.docx` hoặc Excel `.xlsx`;
  - lưu trực tiếp nội dung HTML.
- Không suy đoán endpoint, service code, định dạng file, giới hạn dung lượng hay trường payload ngoài [references/api-contract.md](references/api-contract.md).

## Quy trình bắt buộc

1. Đọc toàn bộ [references/api-contract.md](references/api-contract.md) trước khi tạo request.
2. Dùng thêm `$cogover-api-auth` và đọc reference xác thực của skill đó.
3. Dùng API Key chỉ để gọi `POST /bapi/v1/auth-token`. Với mọi endpoint `/api/v{N}/...` trong skill này, gửi phiên Web App gồm ba cookie và hai header CSRF/XSRF; không gửi API Key Bearer trực tiếp.
4. Xác định workspace domain, thao tác, object slug đích và mode template. Không ghi API Key, cookie hoặc token thật vào log, file hay câu trả lời.
5. Đọc hoặc liệt kê dữ liệu hiện tại trước mọi update/delete. Giữ nguyên trường người dùng không yêu cầu thay đổi.
6. Khi create/update bằng file, thực hiện đầy đủ mục **Kiểm tra và chuẩn bị file mẫu** trước khi upload.
7. Với mọi thao tác create, thực hiện mục **Xác nhận gộp trước khi tạo** sau khi đã có bảng mapping/biến và trước khi sửa file hoặc gọi API create. Không hỏi xác nhận button thành một lượt riêng.
8. Kiểm tra payload theo mode và ma trận định dạng trước khi ghi.
9. Thực hiện thao tác theo workflow tương ứng.
10. Đọc lại detail sau create/update; sau delete, xác minh item không còn trong list hoặc detail không còn trả về bản ghi.
11. Sau mọi create, thực hiện đầy đủ mục **Kiểm thử export end-to-end sau create**. Chỉ tạo button và gắn layout sau khi kiểm thử này đạt.

## Chọn workflow

### Kiểm tra và chuẩn bị file mẫu

Thực hiện phần này trước workflow upload DOCX/XLSX, kể cả khi người dùng gọi file là “template”. Đọc đầy đủ [references/template-syntax.md](references/template-syntax.md) trước khi phân loại hoặc sửa file. Khi file có `#foreach`, `#if`, lookup nhiều cấp, `.format(...)` hoặc vùng dòng/bảng động, đọc thêm đầy đủ [references/template-examples.md](references/template-examples.md) trước khi lập mapping hoặc sửa file. Chỉ dùng cấu trúc của ví dụ; resolve lại mọi slug bằng `$object-info`, không sao chép slug minh họa sang workspace khác.

1. **Mở và đọc file thật.** Dùng skill xử lý Word hoặc spreadsheet khả dụng để đọc nội dung, bảng, sheet, công thức và bố cục; không phân loại chỉ từ tên file, extension, mô tả của người dùng hoặc preview một trang. Kiểm tra cả text hiển thị lẫn cấu trúc OOXML có thể làm vỡ token.
2. **Phân loại theo bằng chứng trong file:**
   - `Đã là template`: các vị trí dữ liệu động đã dùng cú pháp Velocity được server hỗ trợ và field path hợp lệ.
   - `Template một phần`: có cả token/directive hợp lệ và dữ liệu mẫu còn hard-code.
   - `File dữ liệu mẫu`: các vị trí động vẫn là tên, ngày, số tiền, dòng sản phẩm... của một hồ sơ thực tế.
   - Xem `{{...}}`, merge field của hệ khác, `${...}`, token bị Word chia vụn hoặc field path không tồn tại là **chưa sẵn sàng**, không coi là Cogover template hợp lệ.
3. **Nếu file đã là template**, dùng `$object-info` để resolve object/field/related-list thật, kiểm tra toàn bộ path, cân bằng directive, vị trí loop và khả năng render theo reference. Chỉ sửa lỗi nếu cần; không thay token hợp lệ bằng dữ liệu mẫu.
4. **Nếu file là template một phần hoặc file dữ liệu mẫu, lập mapping trước khi sửa file:**
   - Dùng `$object-info` lấy object đích với fields, options, metadata và related lists. Hiểu ngữ nghĩa bằng cách đối chiếu `name`, `slug`, `nameTranslations`/bản dịch, description, `fieldType`, options và object quan hệ; không match chỉ vì chuỗi giống nhau.
   - Đọc nhãn, ngữ cảnh, vị trí, định dạng và giá trị mẫu trong file. Phân biệt dữ liệu của record chính, current user, lookup và danh sách liên quan.
   - Trình bày bảng đề xuất tối thiểu gồm: `Vị trí trong file`, `Nội dung mẫu/nhãn`, `Diễn giải`, `Nguồn`, `Object/related list`, `Field path`, `Cú pháp đề xuất`, `Độ tin cậy/Ghi chú`. Giữ nguyên slug kỹ thuật trong bảng.
   - Nêu rõ ứng viên hoặc câu hỏi cho mapping mơ hồ; không tự chọn một field khi có nhiều khả năng hợp lý.

   | Vị trí trong file | Nội dung mẫu/nhãn | Diễn giải | Nguồn | Object/related list | Field path | Cú pháp đề xuất | Độ tin cậy/Ghi chú |
   |---|---|---|---|---|---|---|---|
   | `{sheet/page, cell/table/paragraph}` | `{giá trị hoặc nhãn đọc từ file}` | `{ý nghĩa nghiệp vụ}` | `record/currentUser/relatedList/object` | `{slug}` | `{chuỗi slug}` | `{Velocity}` | `{cao/vừa/thấp + lý do/câu hỏi}` |

5. **Chốt bảng mapping trước khi sửa file.** Với thao tác create, chưa hỏi xác nhận riêng ở bước này; chuyển bảng hiện tại sang mục **Xác nhận gộp trước khi tạo** để người dùng duyệt mapping/biến, quyết định button và chọn layout trong cùng một lượt. Với update, yêu cầu người dùng xác nhận bảng mapping như hiện hành. Nếu người dùng yêu cầu đổi mapping, cập nhật bảng và chỉ chuyển file sau khi bảng hiện tại được xác nhận rõ.
6. **Chuyển trên bản sao, không ghi đè file gốc.** Thay đúng các giá trị mẫu đã duyệt bằng biến/directive trong [references/template-syntax.md](references/template-syntax.md); dùng cấu trúc hoàn chỉnh trong [references/template-examples.md](references/template-examples.md) khi có loop, điều kiện hoặc lookup nhiều cấp. Giữ nguyên logo, style, kích thước, merge cell, công thức và nội dung tĩnh ngoài mapping. Với một vùng lặp, giữ một dòng mẫu và bọc bằng `#foreach`/`#end`; không lặp lại nhiều dòng hard-code.
7. **Kiểm tra file sau chuyển đổi.** Mở lại file, render/preview bố cục bằng skill Word/spreadsheet, trích lại text/token và kiểm tra: file không hỏng; không còn dữ liệu mẫu tại các vị trí đã mapping; không còn placeholder của hệ khác; mọi path tồn tại; `#if`/`#foreach` có `#end`; token không bị chia vụn; loop row/table đúng cấu trúc. Nếu có API render đã được chứng minh trong ngữ cảnh, render thử với một record và kiểm tra kết quả; không tự suy đoán endpoint preview.
8. **Chỉ upload bản đã kiểm tra.** Chuyển sang workflow **Tạo từ DOCX/XLSX**, upload file đã chuyển hoặc file template hợp lệ ban đầu, rồi mới gọi API create/update.

### Xác nhận gộp trước khi tạo

Áp dụng cho mọi create bằng DOCX, XLSX hoặc HTML. Mục tiêu là chỉ gửi **một yêu cầu xác nhận** chứa cả mapping/biến và lựa chọn tạo button; không duyệt mapping trước rồi hỏi button ở một lượt khác.

1. Chuẩn bị bảng dữ liệu động trước khi hỏi:
   - Với file dữ liệu mẫu hoặc template một phần, dùng bảng mapping ở mục trên.
   - Với file đã là template, lập bảng kiểm tra các biến/directive hiện có, tối thiểu gồm `Vị trí`, `Cú pháp hiện tại`, `Nguồn`, `Object/related list`, `Field path`, `Kết quả resolve` và `Ghi chú`.
   - Với HTML, lập bảng mapping/biến tương đương từ nội dung HTML dự kiến; mọi field path vẫn phải được resolve bằng `$object-info`.
2. Dùng `$object-layout` lấy danh sách layout của đúng `related_object`. Chỉ đưa vào danh sách lựa chọn các layout hỗ trợ xem/sửa: `functionLayout: 2`, hoặc `functionLayout: 3` có quyền `VIEW_EDIT`. Hiển thị tối thiểu `ID`, `Tên`, `functionLayout`, `Web/Mobile`, `Trạng thái` và phạm vi access control. Không tự chọn tất cả layout active, không dùng layout của object khác và không dùng layout chỉ có chức năng Tạo.
3. Chuẩn bị trước cấu hình button đề xuất theo quy tắc của `$object-button`: tên tiếng Anh mặc định nếu người dùng chưa đặt tên, `slug` tiếng Anh dạng `snake_case`, `status: 1`, `isBulk: 0`. Tra trùng slug trước khi đưa vào đề xuất; không tự đổi tên/slug sau khi đã được xác nhận.
4. Trong cùng một câu trả lời, trình bày:
   - bảng mapping hoặc bảng kiểm tra biến;
   - bảng layout đủ điều kiện;
   - cấu hình button dự kiến, gồm tên, slug, `Loại hành động = Xuất dữ liệu`, `Kiểu xuất dữ liệu = Xuất theo mẫu văn bản`, `Mẫu văn bản tải xuống = document template đang chuẩn bị tạo`;
   - một yêu cầu trả lời gộp: xác nhận mapping/biến, chọn **Có/Không** tạo button và, nếu Có, chọn chính xác layout ID đích. Chỉ chấp nhận nhiều layout khi người dùng chủ động liệt kê rõ từng ID.
5. Chỉ coi xác nhận hoàn tất khi người dùng đã duyệt bảng mapping/biến, trả lời Có/Không cho button và cung cấp layout ID nếu chọn Có. Nếu không có layout đủ điều kiện, nêu rõ không thể gắn button và không tự tạo layout mới; lựa chọn Có vẫn bị chặn cho tới khi có layout đích hợp lệ.
6. Sau xác nhận gộp, không hỏi thêm một lượt xác nhận cho create template, create button hoặc update layout. Nếu người dùng thay đổi mapping, tên/slug button hay layout đích sau đó, thay thế đề xuất cũ và yêu cầu duyệt lại **toàn bộ đề xuất gộp hiện hành**; không dùng một xác nhận cũ cho cấu hình đã thay đổi.

### Tạo button xuất và đưa vào layout đã chọn

Chỉ thực hiện mục này khi người dùng đã chọn **Có**, document template vừa tạo đã được đọc lại thành công bằng service `15` và mục **Kiểm thử export end-to-end sau create** đã đạt.

1. Dùng `$object-button` tạo một custom record-level button trên đúng object của template. Dùng chính xác mapping UI/API sau:

   | Cấu hình UI | Giá trị API |
   |---|---|
   | `Loại hành động = Xuất dữ liệu` | `actionType: 8` |
   | Object sở hữu/nguồn | `objectTypeSlug` và `sourceObjectSlug` đều bằng slug của `related_object` |
   | `Kiểu xuất dữ liệu = Xuất theo mẫu văn bản` | `fileDownloadType: 1` |
   | `Mẫu văn bản tải xuống` | `documentTemplate: "{document-template-id-vừa-tạo}"` |
   | Trạng thái/phạm vi | `status: 1`, `isBulk: 0` |

   Button tham khảo đã được ẩn danh: `Xuất hợp đồng` (`{button-id}`), với `actionType: 8`, `fileDownloadType: 1` và `documentTemplate` là ID `{document-template-id}` của mẫu văn bản.
2. Dùng đúng name/slug đã được duyệt trong xác nhận gộp. Thực hiện đầy đủ bước kiểm tra trùng, create và view lại của `$object-button`; chỉ tiếp tục khi view trả đúng `objectTypeSlug`, `sourceObjectSlug`, `actionType: 8`, `fileDownloadType: 1` và `documentTemplate` bằng ID mẫu vừa tạo.
3. Dùng `$object-layout` đưa button vừa xác minh vào layout ID người dùng đã chọn qua `pageSettings.buttons.listButton`. Không tạo component `fieldType: "button_group"`, không thêm vào layout khác và không hỏi xác nhận lần nữa.
4. Giữ nguyên mọi button hiện có và thứ tự của chúng, chống trùng theo `buttonId`, rồi view lại layout. Chỉ báo hoàn tất khi button xuất hiện đúng một lần, layout vẫn thuộc đúng object và vẫn hỗ trợ xem/sửa.
5. Nếu create button thất bại, không update layout. Nếu button đã tạo nhưng update/xác minh layout thất bại, không tự xóa button; báo rõ template và button đã tồn tại nhưng button chưa được gắn thành công vào layout để người dùng quyết định bước tiếp theo.

### Kiểm thử export end-to-end sau create

Áp dụng bắt buộc cho mọi create DOCX, XLSX hoặc HTML sau khi service `15` đã trả đúng template. Kiểm thử từng fixture tuần tự để ghép đúng request với file Chrome vừa tải. Không coi việc create/detail thành công là bằng chứng template render đúng.

1. **Lập ma trận bao phủ.** Dựa trên bảng mapping/biến đã duyệt, liệt kê các placeholder, lookup path, `currentUser`, nhánh `#if`, vùng `#foreach`, related list, format ngày/số/tiền và trường hợp rỗng cần kiểm tra. Chọn số fixture ít nhất nhưng bao phủ được nhiều nhất; dùng nhiều record khi một record không thể đồng thời đi qua các nhánh đối lập hoặc các trường hợp 0/1/nhiều dòng.
2. **Tạo fixture bằng API.** Dùng `$object-info` lấy fields, kiểu dữ liệu, required fields, lookup và toàn bộ related lists thật của đúng `related_object`; dùng `$object-record` tạo record chính cùng các record lookup/related cần thiết. Điền dữ liệu đại diện cho mọi biến có thể kiểm tra, dùng marker duy nhất dạng `codex-document-template-test-{timestamp}-{case}`, đọc lại từng record và lưu toàn bộ Object slug/record ID đã tạo. Không dùng dữ liệu nghiệp vụ có sẵn làm fixture khi có thể tạo dữ liệu test riêng.
3. **Chuẩn bị Web App nhận file.** Dùng công cụ điều khiển trình duyệt có khả năng giữ phiên Workspace và theo dõi download mở record chính tại `https://{WORKSPACE_DOMAIN}/settings/o/{OBJECT_SLUG}/{OBJECT_RECORD_ID}` và chờ trang sẵn sàng. Giữ tab workspace mở để Web App nhận websocket và tự tải file export. Với nhiều fixture, mở đúng record sắp test trước mỗi request.
4. **Dựng related-list sorts từ metadata.** Dùng danh sách related list do `$object-info` trả về; không sao chép các slug minh họa sang object khác. Chỉ gửi slug/field sort đã tồn tại và cần cho template; đối chiếu chiều `asc`/`desc` với thứ tự mong đợi trong file. Nếu không cần sort related list, gửi object rỗng thay vì bịa slug.
5. **Gọi export service `17`.** Dùng phiên Web App theo `$cogover-api-auth`, `POST /api/v1/import-export`, `x-req-service: 17`, `x-req-type: 1` và payload gồm `document_template_id`, `object_record_id`, `object_slug`, `related_list_sorts` theo [references/api-contract.md](references/api-contract.md). Kiểm tra HTTP status và mã nghiệp vụ nếu response có; request này bất đồng bộ nên response thành công chỉ chứng minh job đã được nhận, chưa chứng minh file đúng. Không retry mù quáng khi timeout hoặc kết quả nhận job chưa rõ vì có thể tạo download trùng.
6. **Chờ và nhận đúng file.** Chờ có giới hạn, theo dõi download mới trong trình duyệt kể từ lúc gửi request và tiếp tục cập nhật tiến độ nếu phải chờ. Ghép file theo thời điểm request, fixture và format mong đợi; không lấy một file cũ trong Downloads. Nếu hết thời gian hợp lý mà không có file, ghi nhận test thất bại với nguyên nhân `không nhận được file export`, không suy diễn rằng template đúng.
7. **Mở và kiểm tra file đầu ra.** Dùng skill phù hợp với định dạng tải về: Word cho DOCX, spreadsheet cho XLSX, PDF cho PDF, hoặc kiểm tra ảnh cho IMAGE. Render/preview toàn bộ trang/sheet và đối chiếu với fixture cùng bảng mapping đã duyệt:
   - file mở được, không rỗng, đúng định dạng và không hỏng;
   - mọi placeholder/path đã được thay bằng đúng dữ liệu record, lookup, related list hoặc `currentUser`; không còn token/directive chưa render hay placeholder của hệ khác;
   - `#if` chọn đúng nhánh; `#foreach` sinh đúng số dòng, không lặp dòng mẫu và đúng thứ tự `related_list_sorts`;
   - ngày, số, tiền tệ, option label, công thức/tổng và trường hợp null/rỗng hiển thị đúng yêu cầu;
   - nội dung tĩnh, logo, style, merge cell, bảng, ngắt trang, kích thước và bố cục vẫn đúng; không tràn, cắt hoặc chồng nội dung.
8. **Ghi kết quả theo từng fixture.** Lập bảng tối thiểu gồm `Case`, `Object/Record ID`, `Biến/nhánh được bao phủ`, `File đầu ra`, `Kết quả`, `Sai khác`. Chỉ đánh dấu kiểm thử đạt khi mọi case bắt buộc đạt. Nếu lỗi, báo rõ template đã tồn tại nhưng workflow kiểm thử chưa hoàn tất, không tạo button/gắn layout, và nêu chính xác file, vị trí, giá trị mong đợi/thực tế. Chỉ sửa rồi chạy lại khi thay đổi vẫn thuộc phạm vi đã được người dùng cho phép; nếu đổi mapping/biến đã duyệt, quay lại **Xác nhận gộp trước khi tạo**.
9. **Quản lý fixture.** Báo toàn bộ record test và record liên quan đã tạo. Không tự xóa chúng; nếu người dùng yêu cầu dọn dẹp, dùng quy trình xác nhận/xóa của `$object-record`, rồi xác minh từng ID không còn.

### Liệt kê hoặc xem chi tiết

- Dùng service `13` để liệt kê, lọc hoặc tìm ID.
- Dùng service `15` với `id` để lấy trạng thái chuẩn trước update/delete và để xác minh sau ghi.
- Với pagination, chuyển tiếp `searchAfter` từ response vào `search_after` của trang kế tiếp; không tự chế offset.

### Tạo từ DOCX/XLSX

1. Xác nhận file đầu vào đã hoàn tất mục **Kiểm tra và chuẩn bị file mẫu** và người dùng đã hoàn tất **Xác nhận gộp trước khi tạo**; không upload file dữ liệu mẫu chưa chuyển hoặc file còn chờ xác nhận mapping/biến/button/layout.
2. Kiểm tra extension cuối tên file, không phân biệt hoa thường:
   - `Tai_len_file_Word` yêu cầu `.docx`;
   - `Tai_len_file_Excel` yêu cầu `.xlsx`.
3. Upload file bằng multipart endpoint v2 với đúng một part tên `file`.
4. Lấy nguyên object `data` của response upload làm `content_upload`; không chỉ lấy URL hoặc `file_id`. Không từ chối response chỉ vì thiếu `temp_url` hoặc `fileType` không phải MIME: các key này thay đổi theo file-server/deployment.
5. Gọi service `12` với JSON metadata và `content_upload`.
6. Lấy ID tạo mới từ `body.data.id`, rồi gọi service `15` để xác minh.
7. Thực hiện **Kiểm thử export end-to-end sau create**.
8. Nếu kiểm thử đạt và người dùng đã chọn Có, thực hiện **Tạo button xuất và đưa vào layout đã chọn**. Nếu chọn Không, kết thúc sau khi kiểm thử đạt và không gọi `$object-button` hoặc `$object-layout` để ghi.

Không gọi create nếu upload thất bại, `data` không phải object, extension/tên file không khớp, hoặc object không có server reference nào để lưu. Không dùng URL tạm làm payload thay cho toàn bộ object upload.

### Tạo từ HTML

1. Resolve bảng mapping/biến của HTML và hoàn tất **Xác nhận gộp trước khi tạo**.
2. Dùng `file_format: "Tai_len_file_Html"`.
3. Dùng `download_format` là `PDF` hoặc `IMAGE`.
4. Gửi `content_html` không rỗng; không gọi upload và không gửi `content_upload` của file cũ.
5. Có thể dùng field path dạng chuỗi các field slug nối bằng dấu chấm khi đã lấy path từ object metadata. Chỉ bọc path bằng delimiter placeholder khi contract template hiện hành đã chứng minh cú pháp; nếu chưa, không tự bịa delimiter.
6. Gọi service `12`, rồi đọc lại bằng service `15`.
7. Thực hiện **Kiểm thử export end-to-end sau create**.
8. Nếu kiểm thử đạt và người dùng đã chọn Có, thực hiện **Tạo button xuất và đưa vào layout đã chọn**. Nếu chọn Không, không gọi `$object-button` hoặc `$object-layout` để ghi.

### Cập nhật

1. Gọi service `15`, parse bản sao của `content_upload` nếu cần kiểm tra một response cũ dạng chuỗi JSON, rồi merge đúng thay đổi được yêu cầu. Giữ nguyên representation gốc nếu không thay file.
2. Nếu thay DOCX/XLSX, upload file mới trước và thay toàn bộ `content_upload` bằng object upload mới.
3. Nếu chuyển sang HTML, gửi `content_html` và bỏ metadata upload không còn áp dụng; nếu chuyển từ HTML sang file, gửi `content_upload` và bỏ `content_html` không còn áp dụng.
4. Gọi service `14` với `id` và trạng thái đầy đủ sau merge.
5. Đọc lại detail và so sánh các trường đã đổi.

UI khóa `related_object` khi item đã tồn tại. Vì vậy không đổi object liên kết qua update nếu chưa có contract server bổ sung chứng minh thao tác đó được hỗ trợ.

### Xóa

1. Đọc detail, hiển thị chính xác mẫu sắp xóa và yêu cầu xác nhận nếu người dùng chưa xác nhận rõ hành động phá hủy này.
2. Gọi service `16` với `id`.
3. Nếu response lỗi chứa `body.data[id]`, báo mẫu đang được interface/button tham chiếu và liệt kê `name` của các tham chiếu; không retry hoặc cố gỡ liên kết ngoài phạm vi.
4. Chỉ báo thành công sau khi xác minh item đã biến mất.

## Quy tắc dữ liệu và lỗi

- Dùng object slug cho `related_object`, không dùng display name.
- Lấy `category`, `file_format` và `download_format` hợp lệ từ metadata object `document_template` khi cần; không dịch label UI thành slug bằng phỏng đoán.
- Tôn trọng ma trận:
  - Excel → `XLSX`;
  - Word → `DOCX`, `PDF` hoặc `IMAGE`;
  - HTML → `PDF` hoặc `IMAGE`.
- Trim `name`; yêu cầu 2–100 ký tự. Cho phép `description` null/rỗng nhưng tối đa 1000 ký tự.
- Yêu cầu trường nội dung tương ứng với mode hiện tại; khi chủ động đổi mode, bỏ trường nội dung cũ khỏi payload để tránh dữ liệu stale.
- Xử lý `body.r: 436` là trùng tên. Không tự đổi tên; báo người dùng hoặc dùng tên mới mà họ đã chỉ định.
- Kiểm tra cả HTTP status và mã nghiệp vụ (`body.r` hoặc `r` tùy endpoint). Không coi HTTP 2xx là thành công nếu mã nghiệp vụ báo lỗi.
- Không tuyên bố giới hạn dung lượng/MIME chưa được chứng minh. Front-end khảo sát chỉ kiểm tra extension cho template và đặt timeout upload 3 phút; lỗi server phải được giữ nguyên và báo lại.

## Kết quả cần trả

- Nêu workspace, operation, document template ID/name và mode đã xử lý.
- Nêu kết quả upload riêng với kết quả create/update khi dùng file.
- Với create, nêu quyết định button; nếu đã tạo, nêu button ID/name/slug, layout ID/name và kết quả view xác minh cả button lẫn `pageSettings.buttons.listButton`.
- Với create, nêu ma trận kiểm thử, fixture Object/record IDs, file export đã kiểm tra, mức bao phủ, từng pass/fail và mọi fixture còn tồn tại.
- Nêu cách đã xác minh hậu điều kiện.
- Che toàn bộ secret và dữ liệu phiên; không trả lại API Key, cookie hoặc auth-token.
