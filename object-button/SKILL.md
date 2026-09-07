---
name: object-button
description: Phân tích bài toán nghiệp vụ và quản lý Object Button của Cogover qua Object Buttons API. Sử dụng khi cần biến một thao tác người dùng trên bản ghi/danh sách thành button có ngữ cảnh, tạo hoặc cập nhật bản ghi đích với dữ liệu điền sẵn, chuyển đổi dữ liệu giữa các Object, điều phối chuỗi hành động phụ thuộc đầu ra, đặt record-level button hoặc Button chain vào layout xem/sửa, cấu hình icon light/dark của button trên layout bằng URL ảnh trong thư viện Workspace, hoặc khi cần xem danh sách/chi tiết, tạo, cập nhật, xóa button; cấu hình create/update/duplicate/delete/export, autofill, group button, action chain, Call API, Export and Merge PDF, filter, layout và kết quả sau action.
metadata:
  author: cogover
  version: "1.0.1"
---

# Object Button

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

Biến ý định nghiệp vụ của người dùng thành một hành động có ngữ cảnh trên Cogover Object, rồi quản lý cấu hình đó qua `/bapi/v1/object-buttons`. Một Object Button có thể mở nhanh một thao tác đã điền sẵn dữ liệu, tác động lên bản ghi hiện tại hoặc Object khác, hay điều phối nhiều action theo thứ tự và truyền kết quả giữa các bước.

## Mô hình nghiệp vụ

Phân tích button theo sáu thành phần:

1. **Điểm kích hoạt và vị trí hiển thị:** button thuộc Object nào, xuất hiện trên màn hình bản ghi hay danh sách và được gắn vào layout/filter nào.
2. **Ý định:** người dùng muốn hoàn thành nghiệp vụ gì bằng một lần bấm, ví dụ thu tiền cho hóa đơn hoặc chuyển đổi Lead.
3. **Hành động:** tạo, cập nhật, tạo-hoặc-cập nhật, xóa, export, gọi API, group hay chain.
4. **Dữ liệu vào:** bản ghi hiện tại, hằng số, field của bản ghi hiện tại hoặc output của bước trước.
5. **Kết quả:** Object/bản ghi đích, các field được điền hoặc cập nhật và liên kết được tạo.
6. **Trải nghiệm:** layout, modal, field ẩn/khóa/cho sửa, bước bắt buộc/được bỏ qua và dữ liệu hiển thị sau action.

Chọn cấu trúc nhỏ nhất đáp ứng đúng nghiệp vụ:

- Dùng action `11`, `12` hoặc `13` khi một lần bấm thực hiện một thao tác chính trên một bản ghi đích và có thể cần autofill.
- Dùng action chain `14` khi có nhiều bước tuần tự, bước sau cần output của bước trước, hoặc người dùng cần hoàn thành một giao dịch nghiệp vụ gồm nhiều bản ghi.
- Dùng group button `15` khi chỉ cần gom nhiều lệnh độc lập để tổ chức giao diện; group không biểu diễn luồng dữ liệu hay thứ tự thực thi.
- Không dùng button để thay thế một automation hoàn toàn chạy theo sự kiện và không cần người dùng kích hoạt. Có thể dùng button làm điểm bắt đầu cho một luồng như vậy nếu đó là chủ ý nghiệp vụ.

Đọc [references/business-use-cases.md](references/business-use-cases.md) khi cần giải thích ý nghĩa, thiết kế button từ yêu cầu nghiệp vụ, tạo nhanh bản ghi có dữ liệu điền sẵn hoặc xây chuỗi chuyển đổi nhiều Object. Tệp này phân tích hai mẫu thực tế; JSON request-oriented đi kèm nằm tại [references/example-create-receipt-voucher.json](references/example-create-receipt-voucher.json) và [references/example-convert-lead.json](references/example-convert-lead.json).

## Chuẩn bị

1. Resolve `WORKSPACE_DOMAIN` và API Key theo mục quản lý credential của `$cogover-api-auth`: ưu tiên credential đã được cấp cho đúng Workspace, scoped environment hoặc secret store; không dò file dự án để tìm secret. Chỉ hỏi qua kênh an toàn khi chưa có hoặc không truy cập được.
2. Không in, ghi log hoặc đưa `API_KEY` hay credential của action Call API vào câu trả lời.
3. Chuẩn hóa `WORKSPACE_DOMAIN`: bỏ protocol và dấu `/` cuối nếu có, rồi gọi API qua `https://{WORKSPACE_DOMAIN}`.
4. Xác định thao tác, Object và button đích. Nếu người dùng chỉ đưa tên, tra danh sách để lấy đúng ID; không đoán ID.
5. Đọc [references/api-object-buttons.md](references/api-object-buttons.md) trước khi dựng payload hoặc gọi endpoint. Đây là nguồn chuẩn cho endpoint, schema, action type, ràng buộc và ví dụ cURL.
6. Dùng `$object-info` để lấy Object, field slug, `fieldType`, options và related lists khi button tham chiếu Object hoặc field. Dùng `$object-layout` để tra layout thật và đặt record-level button vào `pageSettings.buttons.listButton` của layout xem/sửa. Khi entry trên layout cần icon, dùng icon người dùng cung cấp hoặc dùng `$cogover-icon` để tạo cặp icon Button light/dark, rồi upload chúng vào thư viện Workspace theo quy trình bắt buộc ở bước tạo button. Dùng `$object-filter` để tra filter thật cho `filterIds`.
7. Tra button được tham chiếu bằng chính Object Buttons API trước khi tạo chain, group hoặc `parentId`. Mọi Object, layout, filter, button và related list được tham chiếu phải tồn tại trong cùng workspace.
8. Khi API reference chưa xác định đủ một mapping lồng nhau, ưu tiên list/view một custom button cùng action type và quan hệ Object tương tự để đối chiếu payload do UI lưu. Nếu không có mẫu tin cậy, nêu giả định và chờ làm rõ trước khi ghi; không tự phát minh key hoặc ngữ nghĩa.
9. Phân biệt yêu cầu đọc/phân tích với yêu cầu ghi. Nếu người dùng chỉ yêu cầu xem, giải thích hoặc lấy mẫu, chỉ gọi endpoint read-only; không tạo, cập nhật hoặc xóa button.

## Quy trình chung

1. Thu thập tối thiểu thông tin còn thiếu cho đúng thao tác. Tận dụng API read-only và ngữ cảnh trước khi hỏi người dùng.
2. Chọn đúng `actionType` theo ý nghĩa nghiệp vụ, rồi lấy metadata của Object nguồn, Object đích, fields, layouts, filters và buttons mà action cần. Không dùng `actionType: 9`.
3. Kiểm tra payload theo phần dùng chung và phần riêng của action trong API reference. Đặc biệt kiểm tra:
   - `name` và `slug` không dài quá 100 ký tự; `slug` chỉ gồm chữ cái, chữ số và `_`.
   - `status` là `0` hoặc `1`; `popupDisplayType`, `fileDownloadType`, `modalWidthUnit` và các cờ có giá trị hợp lệ.
   - Không gửi trường chỉ đọc hoặc server-managed như `id`, `workspaceId`, `objectTypeId`, `type`, audit fields hoặc `isTargetCurrentRecord`.
   - Field slug, `valueDataType`, option, related-list ID, layout ID, filter ID và button ID đều lấy từ API, không tự suy đoán.
4. Dùng công cụ tạo JSON như `jq` khi có `metadata.body`, giá trị autofill dạng JSON string hoặc cấu trúc lồng nhau; không escape thủ công JSON phức tạp.
5. Gọi API với `Authorization: Bearer {API_KEY}` và `Content-Type: application/json`.
6. Chỉ coi thao tác thành công khi HTTP status phù hợp và response có `r: 0`.
7. Sau create hoặc update, luôn gọi view bằng ID để kiểm tra trạng thái đầy đủ đã lưu. Không dựa vào resource rút gọn của create hoặc số đếm của update/delete.
8. Trình bày kết quả bằng tên, ID, slug, Object, action type, trạng thái và tóm tắt cấu hình quan trọng.

## Xem danh sách

Gọi `POST /bapi/v1/object-buttons/list`.

- Nếu biết Object, lọc bằng `objectTypeSlug`; thêm operator cụ thể khi cần.
- Dùng `getDetail: 1` khi cần `listSourceObject`, `autofill` hoặc `actionChain`; dùng `group: 1` khi cần `children`.
- Khi dùng `IN` hoặc `NOT_IN`, gửi giá trị lọc dưới dạng chuỗi phân tách bằng dấu phẩy.
- Phân trang đến khi đủ phạm vi người dùng yêu cầu; mặc định bắt đầu với `page: 1`, `limit: 20`, `order: "updated"`, `sort: "desc"`.
- Hiển thị tối thiểu ID, name, slug, Object, action type, standard/custom, status, bulk, parent và thứ tự nếu có.
- Nếu tìm theo tên mà có nhiều kết quả trùng hoặc gần giống, đưa danh sách ứng viên thay vì tự chọn.

## Xem chi tiết

Gọi `POST /bapi/v1/object-buttons/view` với `id`.

- Thêm `group: 1` khi xem group button để nạp button con.
- Nếu `metadata` được trả về dưới dạng JSON string, parse an toàn trước khi phân tích hoặc sửa.
- Phân biệt standard button (`type: 1`) với custom button (`type: 2`).
- Không tự sửa dữ liệu trong thao tác chỉ yêu cầu xem.

## Tạo button

1. Dùng tên tiếng Anh theo mặc định. Chỉ dùng ngôn ngữ khác khi người dùng yêu cầu hoặc đã cung cấp rõ tên.
2. Sinh `slug` tiếng Anh dạng `snake_case`, kiểm tra đúng regex và tra list theo Object + slug để tránh trùng.
3. Xác minh `objectTypeSlug` của Object sở hữu button và lấy toàn bộ tài nguyên theo action trước khi dựng payload. Nếu người dùng không chỉ định, dùng `status: 1` và `isBulk: 0`; bỏ qua các cấu hình tùy chọn còn lại thay vì tự đoán.
4. Ưu tiên action configurable `11`, `12` hoặc `13` cho luồng create/update mới khi phù hợp; chỉ dùng action basic/legacy `4` hoặc `5` khi người dùng hoặc hệ thống hiện có yêu cầu.
5. Áp dụng cấu hình theo action:
   - Với create/update configurable và list action (`11`, `12`, `13`, `16`, `19`), thiết lập `listSourceObject` theo thứ tự thật; dùng `"$currentRecord"` cho bản ghi hiện tại. Chỉ đặt target và layout sau khi đã resolve Object/layout tương ứng.
   - Với autofill, lấy `field` và `valueDataType` từ đúng Object. Serialize `value` của `targetCreate`, `targetUpdate` và `source` thành JSON string tương thích UI; đặt `isVariable` đúng với giá trị hằng hoặc tham chiếu. Chỉ thêm `objectTypeSlug` hoặc key mapping khác khi nguồn biến đã được xác định từ API reference hay một button UI tương tự. Xác minh mọi related list trước khi dùng `syncRelatedList` hoặc `autofillRelatedList`.
   - Với button list (`16`, `19`), resolve toàn bộ `filterIds`, `buttonIndex`, layout/display và autofill cần thiết; dùng `popupDisplayType: 0` chỉ cho luồng chuyển đến trang tạo của action `16`.
   - Với export (`8`), chọn đúng một cấu hình layout (`fileDownloadType: 0`) hoặc document template (`fileDownloadType: 1`).
   - Với Export and Merge PDF (`20`), bắt buộc có `metadata.fileFieldSlug` là field thật; chỉ thêm `identifierFieldSlug` khi cần.
   - Với Call API (`21`), kiểm tra URL, method, headers và biến `$record`; không gửi body cho GET. Khi có body, serialize thành JSON string biểu diễn object hoặc array. Không tự chèn credential bí mật mà người dùng chưa cung cấp.
6. Với action chain (`14`):
   - Resolve từng `actionButtonId` và giữ thứ tự thực thi rõ ràng. Ưu tiên action `11`, `12`, `13` làm bước trong chain.
   - Dùng ít nhất một action. Chỉ tham chiếu output của bước đứng trước; `sourceButtonIndex` bắt đầu từ `0`, còn bản ghi hiện tại dùng `isCurrentRecord: 1` và `sourceButtonIndex: -1`.
   - Xem `inputs` của mỗi bước là danh sách input slot có thứ tự. Trong action con, `$input_2` trỏ tới slot thứ hai của chính action đó; không mặc định đồng nghĩa với output của chain step số 2. Đối chiếu `listSourceObject`, thứ tự `inputs` và `sourceButtonIndex` cùng nhau.
   - Bảo đảm mọi token `$input_N` có input slot tương ứng và slot đó được chain cấp từ bản ghi hiện tại hoặc output của một bước trước. Nếu một bước cung cấp input có thể bị bỏ qua, xử lý rõ tác động đến các bước phụ thuộc.
   - Chỉ dùng `stopWhenCreate` hoặc `stopWhenUpdate` với action trước đó phù hợp. Không tạo tham chiếu tiến, tham chiếu vòng hoặc ID không tồn tại.
   - Cung cấp `title` và cấu hình modal hợp lý để tương thích giao diện quản lý.
7. Với group button (`15`), resolve ít nhất một child ID, loại group button khỏi danh sách child và không tạo group lồng nhau. Gửi `children`, không gửi trường form frontend `listButton`.
8. Chỉ bật `showRecordAfterAction` cho action `11`, `12`, `13` hoặc `14`. Với mỗi mục bật trong `displayFields`, dùng `actionIndex` hợp lệ và ít nhất một field slug thuộc output của action tương ứng.
9. Gọi `POST /bapi/v1/object-buttons`. Thành công mong đợi HTTP `201` và `r: 0`.
10. Lấy ID từ response, gọi view lại; dùng `group: 1` cho group button. So sánh mọi trường mục tiêu, đặc biệt `listSourceObject`, autofill, `actionChain`, `children`, `filterIds`, metadata và cấu hình hiển thị kết quả.
11. Hoàn tất vị trí hiển thị sau khi button đã được xác minh:
   - Nếu button được thiết kế cho màn danh sách, ví dụ action `16`/`19` hoặc luồng list/bulk tương ứng, hoàn tất cấu hình list/filter; không gắn vào record layout chỉ để hiển thị.
   - Nếu button được thiết kế cho màn hình xem một bản ghi, button tồn tại trong Object Buttons API vẫn chưa đủ để người dùng nhìn thấy. Dùng `$object-layout` để đặt button vào một layout có chức năng xem/sửa của cùng `objectTypeSlug`, thông qua `pageSettings.buttons.listButton`.
   - Không nhầm `pageSettings.buttons` với component `fieldType: "button_group"` trong `content`: trường đầu là cụm action ở header của màn hình bản ghi; trường sau là một component nhúng trong bố cục.
12. Nếu có nhiều layout xem/sửa đang hoạt động, không tự thêm button vào tất cả. Xác định đúng layout theo ID người dùng cung cấp, access control và kênh web/mobile; nếu vẫn còn nhiều ứng viên tương đương, yêu cầu người dùng chọn.
13. Khi gắn button vào layout, giữ nguyên toàn bộ button hiện có và thứ tự của chúng; chống trùng theo `buttonId`; thêm entry mới bằng ID và slug thật của button. Với Button chain, dùng ID và slug của chính button `actionType: 14` ở entry trên layout, không dùng ID của từng action con.
14. Khi người dùng yêu cầu hoặc thiết kế cần icon cho Button/Button chain trên layout, thực hiện đúng thứ tự sau:
   1. Dùng file icon người dùng cung cấp. Nếu chưa có file phù hợp, dùng `$cogover-icon` với profile **Button** để tạo cặp light/dark; không tự dựng icon ngoài hợp đồng của skill đó.
   2. Đọc toàn bộ và làm theo [hướng dẫn upload icon/ảnh vào thư viện Workspace](../cogover-icon/references/upload-icon-image-to-workspace-library.md). Upload riêng từng file light/dark, thêm chúng vào thư viện và lấy URL do response `add-multiple` trả về. Không gán đường dẫn local, `file_id`, URL ngoài chưa được đưa vào thư viện hoặc URL tự ghép.
   3. Trong entry tương ứng của `pageSettings.buttons.listButton`, đặt `useIcon: true`, gán URL light vào `icon` và URL dark vào `iconDarkMode`. Giữ nguyên `onlyShowIcon` trừ khi người dùng yêu cầu chỉ hiển thị icon. Ví dụ:

      ```json
      {
        "buttonId": "BU...",
        "slug": "convert_lead_chain",
        "useIcon": true,
        "onlyShowIcon": false,
        "icon": "https://WORKSPACE_DOMAIN/files/FILE_ID/original/icon.svg?redirect=true",
        "iconDarkMode": "https://WORKSPACE_DOMAIN/files/FILE_ID_DARK/original/icon_dark.svg?redirect=true"
      }
      ```

15. Tuân theo quy trình update/xác minh của `$object-layout`, rồi view lại layout. Kiểm tra entry mục tiêu xuất hiện đúng một lần theo `buttonId`, `icon` và `iconDarkMode` đúng nguyên URL thư viện đã nhận, `useIcon` là `true`, đồng thời mọi button cũ và thứ tự của chúng vẫn được giữ nguyên.

## Cập nhật button

1. Gọi view ngay trước khi sửa để lấy trạng thái mới nhất. Từ chối update standard button.
2. Không đổi `slug`, `objectTypeSlug`, `type` hoặc trường server-managed.
3. Chỉ thay đổi phần người dùng yêu cầu. Không gửi nguyên raw response làm payload.
4. Coi `autofill`, `autofillFields`, `actionChain`, `children` và `filterIds` là cấu hình thay thế toàn bộ:
   - Khi sửa một cấu trúc, gửi lại toàn bộ giá trị hiện tại kèm thay đổi.
   - Không gửi mảng/object rỗng trừ khi người dùng muốn xóa toàn bộ cấu hình đó.
   - Khi đổi `actionType`, dựng lại và xác minh toàn bộ cấu hình bắt buộc của action mới; không giữ các trường riêng của action cũ nếu không còn hợp lệ.
5. Parse `metadata` nếu response trả JSON string, cập nhật đúng key rồi gửi object hợp lệ.
6. Ưu tiên payload update tối thiểu gồm trường cần đổi và toàn bộ cấu trúc lồng nhau bị tác động. Chỉ thêm các trường dùng chung hiện tại khi validation của endpoint yêu cầu; lấy nguyên giá trị từ view mới nhất.
7. Gọi `PUT /bapi/v1/object-buttons/{button_id}`. Thành công mong đợi HTTP `200`, `r: 0`, thường có `data: 1`.
8. Gọi view lại và so sánh trạng thái trước/sau. Báo chính xác phần đã đổi và phần giữ nguyên.

## Xóa button

1. Resolve tất cả ID và gọi view từng button. Hiển thị tên, ID, Object, action type và standard/custom trước khi xóa.
2. Từ chối toàn bộ thao tác nếu có standard button, ID không tồn tại hoặc ID không thuộc workspace. Việc kiểm tra trước là bắt buộc vì backend có thể xóa các custom ID hợp lệ dù một số ID khác không tồn tại.
3. Kiểm tra button có đang được chain, group hoặc cấu hình khác tham chiếu nếu có thể xác định từ API. Cảnh báo tác động trước khi tiếp tục.
4. Yêu cầu người dùng xác nhận rõ danh sách button vì thao tác không thể hoàn tác. Chỉ tiếp tục sau khi xác nhận.
5. Gọi `POST /bapi/v1/object-buttons/delete` với `ids`.
6. Không diễn giải `data` là số button chắc chắn đã xóa. Gọi list hoặc view để xác minh từng ID không còn truy cập được.

## An toàn và xử lý lỗi

- Dùng tên trường `camelCase` cho mọi request public.
- Không đoán ID, slug, field, layout, filter, child hoặc action button từ tên hiển thị.
- Không lặp mù quáng request ghi khi timeout hoặc lỗi mạng. Với create có kết quả không rõ, tra lại Object + slug trước khi thử để tránh tạo trùng.
- Với HTTP `401`, yêu cầu API key hợp lệ; với `429`, tôn trọng thời gian retry của server; với `500`, báo lỗi và chỉ thử lại có kiểm soát khi an toàn.
- Khi `r != 0`, nêu `msg` và trường/cấu hình gây lỗi; không coi HTTP status riêng lẻ là thành công.
- Không thực thi endpoint ngoài phạm vi chỉ vì action Call API chứa URL bên ngoài; skill này chỉ cấu hình Object Button theo yêu cầu.

## Trả kết quả

- Với read, trả bảng hoặc danh sách gọn kèm tổng số và thông tin phân trang nếu có.
- Với phân tích nghiệp vụ, mô tả rõ điểm kích hoạt, action type, Object nguồn/đích, mapping dữ liệu, quan hệ phụ thuộc giữa các bước, trải nghiệm người dùng và điều kiện/lỗi cần lưu ý.
- Với create/update, trả trạng thái đã được endpoint view xác minh, không chỉ response của thao tác ghi. Với record-level button, nêu thêm layout ID/name đã gắn button hoặc cảnh báo button chưa xuất hiện vì chưa có layout đích được chọn/cập nhật.
- Với delete, nêu các ID đã gửi, kết quả xác minh từng ID và cảnh báo rõ nếu còn button truy cập được.
- Với lỗi validation, chỉ rõ trường payload gây lỗi và đề xuất giá trị hợp lệ dựa trên API reference cùng metadata thật của workspace.
