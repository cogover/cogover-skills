---
name: document-template
description: "Quản lý document template Cogover qua `/api/v1/import-export` (phiên Web App): phân loại Word/Excel, mapping dữ liệu mẫu sang object fields, chuyển DOCX/XLSX thành Velocity template, CRUD, upload, HTML; sau create bắt buộc kiểm thử export end-to-end bằng Chrome; tùy chọn tạo Object Button xuất gắn layout Xem/Sửa qua $object-button và $object-layout."
metadata:
  author: cogover
  version: "1.0.2"
---

# Document Template

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Quản lý document template của Cogover qua `POST /api/v1/import-export` (service `12`–`17`) và endpoint upload v2, với hai mode: upload file Word `.docx`/Excel `.xlsx`, hoặc lưu trực tiếp nội dung HTML. Mọi cấu hình template, fixture và lệnh export đi qua API; không thao tác UI để tạo/sửa cấu hình. Không suy đoán endpoint, service code, định dạng file, giới hạn dung lượng hay trường payload ngoài [references/api-contract.md](references/api-contract.md); đọc toàn bộ file này trước khi tạo request.

## Điều kiện môi trường

- Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Mọi endpoint của skill thuộc `/api/v1` nên dùng phiên Web App; API Key chỉ để gọi `POST /bapi/v1/auth-token`, không gửi API Key Bearer trực tiếp.
- Kiểm thử export end-to-end sau create cần công cụ điều khiển trình duyệt (Chrome) sẵn có của môi trường, không phụ thuộc tên plugin cố định, giữ được phiên Workspace đã đăng nhập, giữ tab mở và theo dõi được download; chỉ dùng nó để mở record test, giữ Web App nhận websocket và lấy file Web App tự tải. Thiếu công cụ này: hoàn tất phần chuẩn bị/cấu hình đã được phép, bàn giao các bước kiểm thử thủ công và ghi rõ export end-to-end chưa được xác minh; không báo PASS, không tiếp tục bước phụ thuộc kết quả đó.

## Quy trình bắt buộc

1. Xác định workspace domain, thao tác, object slug đích và mode template.
2. Create/update bằng file: làm đủ mục **Kiểm tra và chuẩn bị file mẫu** trước khi upload.
3. Mọi create: làm mục **Xác nhận gộp trước khi tạo** sau khi có bảng mapping/biến và trước khi sửa file hoặc gọi API create; không hỏi xác nhận button thành một lượt riêng.
4. Update/delete: đọc detail (service `15`) trước; giữ nguyên trường người dùng không yêu cầu thay đổi.
5. Kiểm tra payload theo mode và ma trận định dạng (mục **Quy tắc dữ liệu và lỗi**) rồi gọi API theo workflow tương ứng.
6. Đọc lại detail sau create/update; sau delete, xác minh item không còn trong list hoặc detail không còn trả về bản ghi.
7. Sau mọi create: làm đủ mục **Kiểm thử export end-to-end sau create**. Kiểm thử đạt và người dùng đã chọn Có → **Tạo button xuất và đưa vào layout đã chọn**; chọn Không → kết thúc, không gọi `$object-button` hoặc `$object-layout` để ghi.

## Kiểm tra và chuẩn bị file mẫu

Làm trước workflow upload DOCX/XLSX, kể cả khi người dùng gọi file là "template". Đọc đầy đủ [references/template-syntax.md](references/template-syntax.md) trước khi phân loại hoặc sửa file; khi file có `#foreach`, `#if`, lookup nhiều cấp, `.format(...)` hoặc vùng dòng/bảng động, đọc thêm đầy đủ [references/template-examples.md](references/template-examples.md) trước khi lập mapping hoặc sửa file. Chỉ dùng cấu trúc của ví dụ; resolve lại mọi slug bằng `$object-info`, không sao chép slug minh họa sang workspace khác.

1. **Mở và đọc file thật** bằng skill Word/spreadsheet khả dụng: nội dung, bảng, sheet, công thức, bố cục, cả text hiển thị lẫn cấu trúc OOXML có thể làm vỡ token. Không phân loại chỉ từ tên file, extension, mô tả của người dùng hoặc preview một trang.
2. **Phân loại theo bằng chứng trong file:** `Đã là template` (vị trí dữ liệu động đã dùng cú pháp Velocity được server hỗ trợ và field path hợp lệ); `Template một phần` (có cả token/directive hợp lệ và dữ liệu mẫu còn hard-code); `File dữ liệu mẫu` (vị trí động vẫn là tên, ngày, số tiền, dòng sản phẩm... của một hồ sơ thực tế). `{{...}}`, `${...}`, merge field của hệ khác, token bị Word chia vụn hoặc field path không tồn tại là **chưa sẵn sàng**, không phải Cogover template hợp lệ.
3. **File đã là template:** dùng `$object-info` resolve object/field/related-list thật; kiểm tra toàn bộ path, cân bằng directive, vị trí loop và khả năng render theo reference. Chỉ sửa lỗi nếu cần; không thay token hợp lệ bằng dữ liệu mẫu.
4. **Template một phần hoặc file dữ liệu mẫu: lập mapping trước khi sửa file.**
   - Dùng `$object-info` lấy object đích với fields, options, metadata và related lists. Hiểu ngữ nghĩa bằng cách đối chiếu `name`, `slug`, `nameTranslations`/bản dịch, description, `fieldType`, options và object quan hệ; không match chỉ vì chuỗi giống nhau.
   - Đọc nhãn, ngữ cảnh, vị trí, định dạng và giá trị mẫu trong file; phân biệt dữ liệu của record chính, current user, lookup và danh sách liên quan.
   - Trình bày bảng đề xuất tối thiểu gồm cột `Vị trí trong file` (sheet/page, cell/table/paragraph), `Nội dung mẫu/nhãn`, `Diễn giải`, `Nguồn` (`record`/`currentUser`/`relatedList`/`object`), `Object/related list`, `Field path`, `Cú pháp đề xuất` (Velocity), `Độ tin cậy/Ghi chú` (cao/vừa/thấp kèm lý do hoặc câu hỏi). Giữ nguyên slug kỹ thuật trong bảng.
   - Mapping mơ hồ: nêu rõ ứng viên hoặc câu hỏi; không tự chọn một field khi có nhiều khả năng hợp lý.
5. **Chốt bảng mapping trước khi sửa file.** Create: chưa hỏi xác nhận riêng, đưa bảng vào **Xác nhận gộp trước khi tạo** để người dùng duyệt mapping/biến, quyết định button và chọn layout trong cùng một lượt. Update: yêu cầu người dùng xác nhận bảng mapping. Người dùng đổi mapping → cập nhật bảng và chỉ chuyển file sau khi bảng hiện tại được xác nhận rõ.
6. **Chuyển trên bản sao, không ghi đè file gốc.** Thay đúng các giá trị mẫu đã duyệt bằng biến/directive theo hai reference trên. Giữ nguyên logo, style, kích thước, merge cell, công thức và nội dung tĩnh ngoài mapping. Với một vùng lặp, giữ một dòng mẫu và bọc bằng `#foreach`/`#end`; không lặp lại nhiều dòng hard-code.
7. **Kiểm tra file sau chuyển đổi** theo [Kiểm tra trước upload](references/template-syntax.md#kiểm-tra-trước-upload): mở lại, render/preview bố cục bằng skill Word/spreadsheet, trích lại text/token; file không hỏng, không còn dữ liệu mẫu tại các vị trí đã mapping, không còn placeholder của hệ khác, mọi path tồn tại, `#if`/`#foreach` có `#end`, token không bị chia vụn, loop row/table đúng cấu trúc. Chỉ render thử với một record khi có API render đã được chứng minh trong ngữ cảnh; không tự suy đoán endpoint preview.
8. **Chỉ upload bản đã kiểm tra** (file đã chuyển hoặc file template hợp lệ ban đầu) theo workflow **Tạo từ DOCX/XLSX**, rồi mới gọi API create/update.

## Xác nhận gộp trước khi tạo

Áp dụng cho mọi create bằng DOCX, XLSX hoặc HTML: chỉ gửi **một yêu cầu xác nhận** chứa cả mapping/biến và lựa chọn tạo button; không duyệt mapping trước rồi hỏi button ở một lượt khác.

1. Bảng dữ liệu động: file dữ liệu mẫu hoặc template một phần → bảng mapping ở mục trên; file đã là template → bảng kiểm tra các biến/directive hiện có, tối thiểu gồm `Vị trí`, `Cú pháp hiện tại`, `Nguồn`, `Object/related list`, `Field path`, `Kết quả resolve`, `Ghi chú`; HTML → bảng mapping/biến tương đương từ nội dung HTML dự kiến, mọi field path vẫn phải resolve bằng `$object-info`.
2. Bảng layout: dùng `$object-layout` lấy danh sách layout của đúng `related_object`; chỉ đưa vào lựa chọn các layout hỗ trợ xem/sửa (`functionLayout: 2`, hoặc `functionLayout: 3` có quyền `VIEW_EDIT`), hiển thị tối thiểu `ID`, `Tên`, `functionLayout`, `Web/Mobile`, `Trạng thái` và phạm vi access control. Không tự chọn tất cả layout active, không dùng layout của object khác, không dùng layout chỉ có chức năng Tạo.
3. Button đề xuất theo quy tắc của `$object-button`: tên tiếng Anh mặc định nếu người dùng chưa đặt tên, `slug` tiếng Anh dạng `snake_case` đã tra trùng, `status: 1`, `isBulk: 0`, cùng cấu hình UI theo bảng ở mục **Tạo button xuất và đưa vào layout đã chọn** với `Mẫu văn bản tải xuống` là document template đang chuẩn bị tạo. Không tự đổi tên/slug sau khi đã được xác nhận.
4. Trong cùng một câu trả lời trình bày ba phần trên và một yêu cầu trả lời gộp: xác nhận mapping/biến, chọn **Có/Không** tạo button và, nếu Có, chọn chính xác layout ID đích. Chỉ chấp nhận nhiều layout khi người dùng chủ động liệt kê rõ từng ID.
5. Xác nhận chỉ hoàn tất khi người dùng đã duyệt bảng mapping/biến, trả lời Có/Không và cung cấp layout ID nếu chọn Có. Không có layout đủ điều kiện: nêu rõ không thể gắn button và không tự tạo layout mới; lựa chọn Có bị chặn cho tới khi có layout đích hợp lệ.
6. Sau xác nhận gộp, không hỏi thêm lượt xác nhận cho create template, create button hoặc update layout. Người dùng thay đổi mapping, tên/slug button hay layout đích sau đó: thay thế đề xuất cũ và yêu cầu duyệt lại **toàn bộ đề xuất gộp hiện hành**; không dùng một xác nhận cũ cho cấu hình đã thay đổi.

## Liệt kê hoặc xem chi tiết

- Service `13`: liệt kê, lọc hoặc tìm ID. Pagination: chuyển tiếp `searchAfter` từ response vào `search_after` của trang kế tiếp; không tự chế offset.
- Service `15` với `id`: trạng thái chuẩn trước update/delete và xác minh sau ghi.

## Tạo từ DOCX/XLSX

1. Chỉ nhận file đã hoàn tất **Kiểm tra và chuẩn bị file mẫu** và **Xác nhận gộp trước khi tạo**; không upload file dữ liệu mẫu chưa chuyển hoặc file còn chờ xác nhận mapping/biến/button/layout.
2. Kiểm tra extension cuối tên file, không phân biệt hoa thường: `Tai_len_file_Word` yêu cầu `.docx`; `Tai_len_file_Excel` yêu cầu `.xlsx`.
3. Upload file bằng multipart endpoint v2 với đúng một part tên `file`.
4. Lấy nguyên object `data` của response upload làm `content_upload`; không chỉ lấy URL hoặc `file_id`, không dùng URL tạm làm payload thay cho toàn bộ object upload. Không từ chối response chỉ vì thiếu `temp_url` hoặc `fileType` không phải MIME: các key này thay đổi theo file-server/deployment. Không gọi create nếu upload thất bại, `data` không phải object, extension/tên file không khớp, hoặc object không có server reference nào để lưu.
5. Gọi service `12` với JSON metadata và `content_upload`; lấy ID từ `body.data.id`, xác minh bằng service `15`, rồi làm **Kiểm thử export end-to-end sau create**.

## Tạo từ HTML

1. Resolve bảng mapping/biến của HTML và hoàn tất **Xác nhận gộp trước khi tạo**.
2. `file_format: "Tai_len_file_Html"`; `download_format` là `PDF` hoặc `IMAGE`; gửi `content_html` không rỗng; không gọi upload và không gửi `content_upload` của file cũ.
3. Field path là chuỗi các field slug nối bằng dấu chấm lấy từ object metadata. Chỉ bọc path bằng delimiter placeholder khi contract template hiện hành đã chứng minh cú pháp; nếu chưa, không tự bịa delimiter.
4. Gọi service `12`, đọc lại bằng service `15`, rồi làm **Kiểm thử export end-to-end sau create**.

## Kiểm thử export end-to-end sau create

Bắt buộc cho mọi create DOCX, XLSX hoặc HTML sau khi service `15` đã trả đúng template; create/detail thành công không phải bằng chứng template render đúng. Kiểm thử từng fixture tuần tự để ghép đúng request với file trình duyệt (Chrome) vừa tải.

1. **Ma trận bao phủ** từ bảng mapping/biến đã duyệt: placeholder, lookup path, `currentUser`, nhánh `#if`, vùng `#foreach`, related list, format ngày/số/tiền và trường hợp rỗng. Chọn số fixture ít nhất nhưng bao phủ nhiều nhất; dùng nhiều record khi một record không thể đồng thời đi qua các nhánh đối lập hoặc các trường hợp 0/1/nhiều dòng.
2. **Tạo fixture bằng API:** `$object-info` lấy fields, kiểu dữ liệu, required fields, lookup và toàn bộ related lists thật của đúng `related_object`; `$object-record` tạo record chính cùng các record lookup/related cần thiết, điền dữ liệu đại diện cho mọi biến có thể kiểm tra, marker duy nhất dạng `codex-document-template-test-{timestamp}-{case}`; đọc lại từng record và lưu toàn bộ Object slug/record ID đã tạo. Không dùng dữ liệu nghiệp vụ có sẵn làm fixture khi có thể tạo dữ liệu test riêng.
3. **Chuẩn bị Web App nhận file:** dùng công cụ trình duyệt mở record chính tại `https://{WORKSPACE_DOMAIN}/settings/o/{OBJECT_SLUG}/{OBJECT_RECORD_ID}`, chờ trang sẵn sàng và giữ tab mở để Web App nhận websocket rồi tự tải file export. Nhiều fixture: mở đúng record sắp test trước mỗi request.
4. **`related_list_sorts` từ metadata:** chỉ dùng related-list slug và field sort do `$object-info` trả về và cần cho template; đối chiếu chiều `asc`/`desc` với thứ tự mong đợi trong file; không cần sort thì gửi object rỗng thay vì bịa slug; không sao chép slug minh họa sang object khác.
5. **Gọi export service `17`:** `POST /api/v1/import-export`, `x-req-service: 17`, `x-req-type: 1`, payload gồm `document_template_id`, `object_record_id`, `object_slug`, `related_list_sorts` theo api-contract. Kiểm tra HTTP status và mã nghiệp vụ nếu có; request bất đồng bộ nên response thành công chỉ chứng minh job đã được nhận, chưa chứng minh file đúng. Không retry mù quáng khi timeout hoặc kết quả nhận job chưa rõ vì có thể tạo download trùng.
6. **Chờ và nhận đúng file:** chờ có giới hạn, theo dõi download mới trong trình duyệt kể từ lúc gửi request và cập nhật tiến độ nếu phải chờ; ghép file theo thời điểm request, fixture và format mong đợi, không lấy một file cũ trong Downloads. Hết thời gian hợp lý mà không có file: ghi nhận test thất bại với nguyên nhân `không nhận được file export`, không suy diễn rằng template đúng.
7. **Mở và kiểm tra file đầu ra** bằng skill phù hợp định dạng (Word cho DOCX, spreadsheet cho XLSX, PDF cho PDF, kiểm tra ảnh cho IMAGE); render/preview toàn bộ trang/sheet và đối chiếu với fixture cùng bảng mapping đã duyệt:
   - file mở được, không rỗng, đúng định dạng và không hỏng;
   - mọi placeholder/path đã được thay bằng đúng dữ liệu record, lookup, related list hoặc `currentUser`; không còn token/directive chưa render hay placeholder của hệ khác;
   - `#if` chọn đúng nhánh; `#foreach` sinh đúng số dòng, không lặp dòng mẫu và đúng thứ tự `related_list_sorts`;
   - ngày, số, tiền tệ, option label, công thức/tổng và trường hợp null/rỗng hiển thị đúng yêu cầu;
   - nội dung tĩnh, logo, style, merge cell, bảng, ngắt trang, kích thước và bố cục vẫn đúng; không tràn, cắt hoặc chồng nội dung.
8. **Ghi kết quả theo từng fixture:** bảng tối thiểu gồm `Case`, `Object/Record ID`, `Biến/nhánh được bao phủ`, `File đầu ra`, `Kết quả`, `Sai khác`. Chỉ đánh dấu đạt khi mọi case bắt buộc đạt. Lỗi: báo rõ template đã tồn tại nhưng workflow kiểm thử chưa hoàn tất, không tạo button/gắn layout, nêu chính xác file, vị trí, giá trị mong đợi/thực tế; chỉ sửa rồi chạy lại khi thay đổi vẫn thuộc phạm vi người dùng đã cho phép; đổi mapping/biến đã duyệt thì quay lại **Xác nhận gộp trước khi tạo**.
9. **Quản lý fixture:** báo toàn bộ record test và record liên quan đã tạo; không tự xóa. Người dùng yêu cầu dọn dẹp: dùng quy trình xác nhận/xóa của `$object-record`, rồi xác minh từng ID không còn.

## Tạo button xuất và đưa vào layout đã chọn

Chỉ khi người dùng đã chọn **Có**, document template vừa tạo đã được đọc lại thành công bằng service `15` và **Kiểm thử export end-to-end sau create** đã đạt.

1. Dùng `$object-button` tạo một custom record-level button trên đúng object của template, với name/slug đã duyệt trong xác nhận gộp và mapping UI/API:

   | Cấu hình UI | Giá trị API |
   |---|---|
   | `Loại hành động = Xuất dữ liệu` | `actionType: 8` |
   | Object sở hữu/nguồn | `objectTypeSlug` và `sourceObjectSlug` đều bằng slug của `related_object` |
   | `Kiểu xuất dữ liệu = Xuất theo mẫu văn bản` | `fileDownloadType: 1` |
   | `Mẫu văn bản tải xuống` | `documentTemplate: "{document-template-id-vừa-tạo}"` |
   | Trạng thái/phạm vi | `status: 1`, `isBulk: 0` |

   Thực hiện đầy đủ bước kiểm tra trùng, create và view lại của `$object-button`; chỉ tiếp tục khi view trả đúng `objectTypeSlug`, `sourceObjectSlug`, `actionType: 8`, `fileDownloadType: 1` và `documentTemplate` bằng ID mẫu vừa tạo.
2. Dùng `$object-layout` đưa button vừa xác minh vào layout ID người dùng đã chọn qua `pageSettings.buttons.listButton`: giữ nguyên mọi button hiện có và thứ tự của chúng, chống trùng theo `buttonId`; không tạo component `fieldType: "button_group"`, không thêm vào layout khác, không hỏi xác nhận lần nữa. View lại layout; chỉ báo hoàn tất khi button xuất hiện đúng một lần, layout vẫn thuộc đúng object và vẫn hỗ trợ xem/sửa.
3. Create button thất bại: không update layout. Button đã tạo nhưng update/xác minh layout thất bại: không tự xóa button; báo rõ template và button đã tồn tại nhưng button chưa được gắn thành công vào layout để người dùng quyết định bước tiếp theo.

## Cập nhật

1. Gọi service `15`; nếu `content_upload` của response cũ là chuỗi JSON, parse trên bản sao để kiểm tra; merge đúng thay đổi được yêu cầu và giữ nguyên representation gốc nếu không thay file.
2. Thay DOCX/XLSX: upload file mới trước, thay toàn bộ `content_upload` bằng object upload mới. Chuyển sang HTML: gửi `content_html` và bỏ metadata upload không còn áp dụng; chuyển từ HTML sang file: gửi `content_upload` và bỏ `content_html`.
3. Gọi service `14` với `id` và trạng thái đầy đủ sau merge; đọc lại detail và so sánh các trường đã đổi.
4. Không đổi `related_object` qua update (UI khóa trường này khi item đã tồn tại) nếu chưa có contract server bổ sung chứng minh thao tác được hỗ trợ.

## Xóa

1. Đọc detail, hiển thị chính xác mẫu sắp xóa và yêu cầu xác nhận nếu người dùng chưa xác nhận rõ hành động phá hủy này.
2. Gọi service `16` với `id`. Response lỗi chứa `body.data[id]`: mẫu đang được interface/button tham chiếu, liệt kê `name` của các tham chiếu; không retry hoặc cố gỡ liên kết ngoài phạm vi.
3. Chỉ báo thành công sau khi xác minh item đã biến mất.

## Quy tắc dữ liệu và lỗi

- `related_object` là object slug, không dùng display name. `category`, `file_format`, `download_format` lấy từ metadata object `document_template` khi cần; không dịch label UI thành slug bằng phỏng đoán.
- Ma trận format: Excel → `XLSX`; Word → `DOCX`, `PDF` hoặc `IMAGE`; HTML → `PDF` hoặc `IMAGE`.
- Trim `name`, 2–100 ký tự; `description` null/rỗng được nhưng tối đa 1000 ký tự.
- Gửi đúng trường nội dung của mode hiện tại; khi chủ động đổi mode, bỏ trường nội dung cũ khỏi payload để tránh dữ liệu stale.
- `body.r: 436` là trùng tên: không tự đổi tên; báo người dùng hoặc dùng tên mới mà họ đã chỉ định.
- Kiểm tra cả HTTP status và mã nghiệp vụ (`body.r` hoặc `r` tùy endpoint); HTTP 2xx kèm mã nghiệp vụ báo lỗi không phải thành công.
- Không tuyên bố giới hạn dung lượng/MIME chưa được chứng minh: front-end chỉ kiểm tra extension cho template và đặt timeout upload 3 phút; lỗi server phải được giữ nguyên và báo lại.

## Kết quả cần trả

- Workspace, operation, document template ID/name và mode đã xử lý; với file, kết quả upload nêu riêng với kết quả create/update; cách đã xác minh hậu điều kiện.
- Create: ma trận kiểm thử, fixture Object/record IDs, file export đã kiểm tra, mức bao phủ, pass/fail từng case và mọi fixture còn tồn tại; quyết định button và, nếu đã tạo, button ID/name/slug, layout ID/name cùng kết quả view xác minh cả button lẫn `pageSettings.buttons.listButton`.
