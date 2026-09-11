---
name: object-button
description: "Phân tích nghiệp vụ và quản lý Object Button qua Object Buttons API `/bapi/v1/object-buttons`: list, view, tạo, cập nhật, xóa; cấu hình create/update/export, autofill, action chain, group, Call API, Export and Merge PDF, filter, kết quả sau action; đặt button/Button chain lên layout xem/sửa và icon light/dark qua $object-layout, $cogover-icon."
metadata:
  author: cogover
  version: "1.0.2"
---

# Object Button

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Biến ý định nghiệp vụ thành một hành động có ngữ cảnh trên Cogover Object và quản lý cấu hình đó qua `/bapi/v1/object-buttons` (API Key Bearer): list, view, create, update, delete. Một Object Button có thể mở nhanh một thao tác đã điền sẵn dữ liệu, tác động lên bản ghi hiện tại hoặc Object khác, hay điều phối nhiều action theo thứ tự và truyền kết quả giữa các bước. Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md).

## Mô hình nghiệp vụ

Phân tích button theo sáu thành phần:

1. **Điểm kích hoạt và vị trí hiển thị:** button thuộc Object nào, xuất hiện trên màn hình bản ghi hay danh sách, gắn vào layout/filter nào.
2. **Ý định:** nghiệp vụ cần hoàn thành bằng một lần bấm, ví dụ thu tiền cho hóa đơn hoặc chuyển đổi Lead.
3. **Hành động:** tạo, cập nhật, tạo-hoặc-cập nhật, xóa, export, gọi API, group hay chain.
4. **Dữ liệu vào:** bản ghi hiện tại, hằng số, field của bản ghi hiện tại hoặc output của bước trước.
5. **Kết quả:** Object/bản ghi đích, field được điền hoặc cập nhật, liên kết được tạo.
6. **Trải nghiệm:** layout, modal, field ẩn/khóa/cho sửa, bước bắt buộc/được bỏ qua, dữ liệu hiển thị sau action.

Chọn cấu trúc nhỏ nhất đáp ứng đúng nghiệp vụ:

- Action `11`, `12` hoặc `13`: một lần bấm thực hiện một thao tác chính trên một bản ghi đích, có thể kèm autofill.
- Action chain `14`: nhiều bước tuần tự, bước sau cần output của bước trước, hoặc một giao dịch nghiệp vụ gồm nhiều bản ghi.
- Group button `15`: chỉ gom nhiều lệnh độc lập để tổ chức giao diện; không biểu diễn luồng dữ liệu hay thứ tự thực thi.
- Không dùng button thay cho automation chạy hoàn toàn theo sự kiện, không cần người dùng kích hoạt; button có thể là điểm bắt đầu của luồng đó nếu đúng chủ ý nghiệp vụ.

Đọc [references/business-use-cases.md](references/business-use-cases.md) khi cần giải thích ý nghĩa, thiết kế button từ yêu cầu nghiệp vụ, tạo nhanh bản ghi có dữ liệu điền sẵn hoặc xây chuỗi chuyển đổi nhiều Object: hai mẫu thực tế kèm JSON request-oriented [example-create-receipt-voucher.json](references/example-create-receipt-voucher.json) và [example-convert-lead.json](references/example-convert-lead.json).

## Chuẩn bị

- Đọc [references/api-object-buttons.md](references/api-object-buttons.md) (endpoint, schema, action type, ràng buộc, ví dụ cURL) trước khi dựng payload hoặc gọi endpoint.
- Người dùng chỉ đưa tên button: tra list để lấy ID; nhiều kết quả trùng hoặc gần giống thì đưa danh sách ứng viên thay vì tự chọn.
- Lấy metadata thật trước khi dựng payload: `$object-info` cho Object, field slug, `fieldType`, options và related lists khi button tham chiếu Object hoặc field; `$object-filter` cho filter thật của `filterIds`; `$object-layout` cho layout thật và để đặt record-level button vào `pageSettings.buttons.listButton` của layout xem/sửa; chính Object Buttons API cho button được tham chiếu trong chain, group hoặc `parentId`. Mọi Object, layout, filter, button và related list được tham chiếu phải tồn tại trong cùng workspace.
- API reference chưa xác định đủ một mapping lồng nhau: list/view một custom button cùng action type và quan hệ Object tương tự để đối chiếu payload do UI lưu. Không có mẫu tin cậy thì nêu giả định và chờ làm rõ trước khi ghi; không tự phát minh key hoặc ngữ nghĩa.

## Quy tắc payload

- Tên trường `camelCase`. Dựng JSON bằng `jq` hoặc tương đương khi có `metadata.body`, giá trị autofill dạng JSON string hoặc cấu trúc lồng nhau; không escape thủ công.
- `name` và `slug` tối đa 100 ký tự; `slug` chỉ gồm chữ cái, chữ số và `_`. `status` là `0` hoặc `1`; `popupDisplayType`, `fileDownloadType`, `modalWidthUnit` và các cờ dùng giá trị hợp lệ trong API reference. Không dùng `actionType: 9`.
- Không gửi trường chỉ đọc hoặc server-managed: `id`, `workspaceId`, `objectTypeId`, `type`, audit fields, `isTargetCurrentRecord`.
- Field slug, `valueDataType`, option, related-list ID, layout ID, filter ID, child và action button ID đều lấy từ API; không suy đoán từ tên hiển thị.
- `metadata` có thể được trả về dạng JSON string: parse an toàn trước khi phân tích hoặc sửa; khi cập nhật, sửa đúng key rồi gửi object hợp lệ.
- Sau create hoặc update luôn view lại bằng ID: response create là resource rút gọn, response update/delete chỉ là số đếm.
- Không lặp mù request ghi khi timeout hoặc lỗi mạng; create có kết quả không rõ thì tra list theo Object + slug trước khi thử lại để tránh tạo trùng. `429`: tôn trọng thời gian retry của server; `500` sau request ghi: chỉ thử lại có kiểm soát khi an toàn.
- Không thực thi URL trong cấu hình Call API dù là URL bên ngoài; skill chỉ cấu hình Object Button.

## Xem danh sách và chi tiết

- `POST /bapi/v1/object-buttons/list`: biết Object thì lọc bằng `objectTypeSlug`, thêm operator cụ thể khi cần; `getDetail: 1` khi cần `listSourceObject`, `autofill` hoặc `actionChain`; `group: 1` khi cần `children`; phân trang đến khi đủ phạm vi người dùng yêu cầu.
- `POST /bapi/v1/object-buttons/view` với `id`; thêm `group: 1` khi xem group button. Standard button `type: 1`, custom button `type: 2`.

## Tạo button

1. `name` tiếng Anh theo mặc định; ngôn ngữ khác chỉ khi người dùng yêu cầu hoặc đã cung cấp rõ tên. `slug` tiếng Anh `snake_case`, tra list theo Object + slug để tránh trùng.
2. Xác minh `objectTypeSlug` của Object sở hữu button và resolve toàn bộ tài nguyên theo action trước khi dựng payload. Người dùng không chỉ định thì `status: 1`, `isBulk: 0`; bỏ qua các cấu hình tùy chọn còn lại thay vì tự đoán.
3. Ưu tiên action configurable `11`, `12`, `13` cho luồng create/update mới; chỉ dùng action basic/legacy `4` hoặc `5` khi người dùng hoặc hệ thống hiện có yêu cầu.
4. Cấu hình theo action:
   - `11`, `12`, `13`, `16`, `19`: `listSourceObject` theo thứ tự thật, `"$currentRecord"` cho bản ghi hiện tại; chỉ đặt target và layout sau khi đã resolve Object/layout tương ứng.
   - Autofill: `field` và `valueDataType` từ đúng Object; `value` của `targetCreate`, `targetUpdate`, `source` serialize thành JSON string tương thích UI; `isVariable` đúng với giá trị hằng hoặc tham chiếu; chỉ thêm `objectTypeSlug` hoặc key mapping khác khi nguồn biến đã xác định từ API reference hay một button UI tương tự; xác minh mọi related list trước khi dùng `syncRelatedList` hoặc `autofillRelatedList`.
   - List button `16`, `19`: resolve toàn bộ `filterIds`, `buttonIndex`, layout/display và autofill; `popupDisplayType: 0` chỉ cho luồng chuyển đến trang tạo của action `16`.
   - Export `8`: đúng một cấu hình, layout (`fileDownloadType: 0`) hoặc document template (`fileDownloadType: 1`).
   - Export and Merge PDF `20`: bắt buộc `metadata.fileFieldSlug` là field thật; chỉ thêm `identifierFieldSlug` khi cần.
   - Call API `21`: kiểm tra URL, method, headers và biến `$record`; không gửi body cho GET; body serialize thành JSON string biểu diễn object hoặc array; không tự chèn credential bí mật mà người dùng chưa cung cấp.
   - Action chain `14`: resolve từng `actionButtonId` (ưu tiên `11`, `12`, `13` làm bước), ít nhất một action, thứ tự thực thi rõ ràng; cung cấp `title` và cấu hình modal hợp lý để tương thích giao diện quản lý. Chỉ tham chiếu output của bước đứng trước: `sourceButtonIndex` bắt đầu từ `0`, bản ghi hiện tại dùng `isCurrentRecord: 1` và `sourceButtonIndex: -1`. `inputs` của mỗi bước là danh sách input slot có thứ tự: trong action con, `$input_2` trỏ tới slot thứ hai của chính action đó, không mặc định là output của chain step số 2; đối chiếu `listSourceObject`, thứ tự `inputs` và `sourceButtonIndex` cùng nhau. Mọi token `$input_N` phải có slot tương ứng được chain cấp từ bản ghi hiện tại hoặc output của một bước trước; nếu bước cung cấp input có thể bị bỏ qua, xử lý rõ tác động đến các bước phụ thuộc. `stopWhenCreate`/`stopWhenUpdate` chỉ với action trước đó phù hợp; không tạo tham chiếu tiến, tham chiếu vòng hoặc ID không tồn tại.
   - Group button `15`: ít nhất một child ID, loại group button khỏi danh sách child, không tạo group lồng nhau; gửi `children`, không gửi trường form frontend `listButton`.
   - `showRecordAfterAction` chỉ bật cho `11`, `12`, `13` hoặc `14`; mỗi mục bật trong `displayFields` dùng `actionIndex` hợp lệ và ít nhất một field slug thuộc output của action tương ứng.
5. Gọi `POST /bapi/v1/object-buttons` (thành công: HTTP `201`, `r: 0`), lấy ID và view lại (`group: 1` với group button); so sánh mọi trường mục tiêu, đặc biệt `listSourceObject`, autofill, `actionChain`, `children`, `filterIds`, metadata và cấu hình hiển thị kết quả.
6. Hoàn tất vị trí hiển thị sau khi button đã được xác minh:
   - Button cho màn danh sách (action `16`/`19` hoặc luồng list/bulk tương ứng): hoàn tất cấu hình list/filter; không gắn vào record layout chỉ để hiển thị.
   - Button cho màn hình xem một bản ghi: tồn tại trong Object Buttons API chưa đủ để người dùng nhìn thấy. Dùng `$object-layout` đặt button vào một layout có chức năng xem/sửa của cùng `objectTypeSlug` qua `pageSettings.buttons.listButton`; không nhầm với component `fieldType: "button_group"` trong `content` (trường đầu là cụm action ở header màn hình bản ghi, trường sau là component nhúng trong bố cục).
   - Nhiều layout xem/sửa đang hoạt động: không tự thêm vào tất cả; xác định theo ID người dùng cung cấp, access control và kênh web/mobile; còn nhiều ứng viên tương đương thì yêu cầu người dùng chọn.
   - Giữ nguyên toàn bộ button hiện có và thứ tự của chúng; chống trùng theo `buttonId`; entry mới dùng ID và slug thật của button. Với Button chain, entry dùng ID và slug của chính button `actionType: 14`, không dùng ID của từng action con.
7. Icon cho Button/Button chain trên layout, khi người dùng yêu cầu hoặc thiết kế cần, theo đúng thứ tự:
   1. Dùng file icon người dùng cung cấp; chưa có thì dùng `$cogover-icon` với profile **Button** để tạo cặp light/dark, không tự dựng icon ngoài hợp đồng của skill đó.
   2. Đọc toàn bộ và làm theo [hướng dẫn upload icon/ảnh vào thư viện Workspace](../cogover-icon/references/upload-icon-image-to-workspace-library.md): upload riêng từng file light/dark, thêm vào thư viện và lấy URL do response `add-multiple` trả về. Không gán đường dẫn local, `file_id`, URL ngoài chưa được đưa vào thư viện hoặc URL tự ghép.
   3. Trong entry tương ứng của `pageSettings.buttons.listButton`: `useIcon: true`, URL light vào `icon`, URL dark vào `iconDarkMode`; giữ nguyên `onlyShowIcon` trừ khi người dùng yêu cầu chỉ hiển thị icon:

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

   4. Cập nhật và xác minh theo quy trình của `$object-layout`, rồi view lại layout: entry mục tiêu xuất hiện đúng một lần theo `buttonId`, `icon` và `iconDarkMode` đúng nguyên URL thư viện đã nhận, `useIcon` là `true`, mọi button cũ và thứ tự của chúng vẫn giữ nguyên.

## Cập nhật button

1. View ngay trước khi sửa; từ chối update standard button. Không đổi `slug`, `objectTypeSlug`, `type` hoặc trường server-managed.
2. Chỉ thay đổi phần người dùng yêu cầu; không gửi nguyên raw response làm payload. Payload tối thiểu gồm trường cần đổi và toàn bộ cấu trúc lồng nhau bị tác động; chỉ thêm các trường dùng chung khi validation của endpoint yêu cầu, lấy nguyên giá trị từ view mới nhất.
3. `autofill`, `autofillFields`, `actionChain`, `children`, `filterIds` là cấu hình thay thế toàn bộ: gửi lại toàn bộ giá trị hiện tại kèm thay đổi; không gửi mảng/object rỗng trừ khi người dùng muốn xóa toàn bộ cấu hình đó. Đổi `actionType`: dựng lại và xác minh toàn bộ cấu hình bắt buộc của action mới, không giữ trường riêng của action cũ nếu không còn hợp lệ.
4. Gọi `PUT /bapi/v1/object-buttons/{button_id}` (thành công: HTTP `200`, `r: 0`, thường `data: 1`), rồi view lại và so sánh trạng thái trước/sau.

## Xóa button

1. Resolve mọi ID và view từng button; hiển thị tên, ID, Object, action type, standard/custom trước khi xóa.
2. Từ chối toàn bộ thao tác nếu có standard button, ID không tồn tại hoặc ID không thuộc workspace; kiểm tra trước là bắt buộc vì backend có thể xóa các custom ID hợp lệ dù một số ID khác không tồn tại.
3. Kiểm tra button có đang được chain, group hoặc cấu hình khác tham chiếu nếu xác định được từ API; cảnh báo tác động trước khi tiếp tục.
4. Chỉ gọi `POST /bapi/v1/object-buttons/delete` với `ids` sau khi người dùng xác nhận rõ danh sách (thao tác không hoàn tác).
5. Không diễn giải `data` là số button chắc chắn đã xóa; gọi list hoặc view để xác minh từng ID không còn truy cập được.

## Trả kết quả

- Read: bảng hoặc danh sách gọn, tối thiểu ID, name, slug, Object, action type, standard/custom, status, bulk, parent và thứ tự nếu có; kèm tổng số và phân trang.
- Phân tích nghiệp vụ: điểm kích hoạt, action type, Object nguồn/đích, mapping dữ liệu, quan hệ phụ thuộc giữa các bước, trải nghiệm người dùng, điều kiện/lỗi cần lưu ý.
- Create/update: trạng thái đã được view xác minh (tên, ID, slug, Object, action type, trạng thái, tóm tắt cấu hình quan trọng), không chỉ response của thao tác ghi; update nêu phần đã đổi và phần giữ nguyên; record-level button nêu thêm layout ID/name đã gắn hoặc cảnh báo button chưa xuất hiện vì chưa có layout đích được chọn/cập nhật.
- Delete: các ID đã gửi, kết quả xác minh từng ID, cảnh báo rõ nếu còn button truy cập được.
