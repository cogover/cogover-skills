---
name: cogover-icon
description: "Tạo, kiểm tra, tra cứu, tái sử dụng và upload icon SVG cho Cogover Button (cặp light/dark) và App Menu (18×18) qua thư viện icon Workspace `/api/v1/objects/icon`. Dùng khi cần icon cho Object Button, button trên layout, nhóm App Menu, hoặc icon bị cắt, quá đậm, sai màu, mất ở dark mode. Không dùng cho module icon hay app launcher."
metadata:
  author: cogover
  version: "1.0.2"
---

# Cogover Icon

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Sinh và kiểm tra SVG icon theo hai profile **Button** và **App Menu**; tra cứu, tái sử dụng và upload icon trong thư viện Workspace qua `/api/v1` bằng phiên Web App. Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md).

## Phạm vi

- Mặc định chỉ sinh và trả file SVG. Không upload, không cập nhật Object Button, layout hoặc tài khoản khi người dùng chưa yêu cầu rõ. Khi được yêu cầu cài icon lên hệ thống: upload theo [upload-icon-image-to-workspace-library.md](references/upload-icon-image-to-workspace-library.md), rồi cài bằng `$object-button`/`$object-layout` (Button) hoặc `$app-menu-manager` (App Menu); giữ nguyên mọi cấu hình ngoài icon.
- Chỉnh SVG bằng mã vector: không dùng ImageGen cho icon kiểu này, không biến raster thành SVG giả bằng cách nhúng bitmap.
- Giấy phép: đọc [assets/NOTICE.md](assets/NOTICE.md) khi dùng hoặc phân phối SVG đi kèm. Hai icon hoàn thành `complete_icon_v4*.svg` có nguồn Font Awesome Free và giữ attribution CC BY 4.0; bốn SVG còn lại là hình học tự vẽ theo MIT. Không lấy icon không rõ quyền phân phối làm asset mẫu.

## Chọn profile

| Profile | Dùng cho | Hợp đồng |
|---|---|---|
| **Button** | Object Button, action button, button trên layout | [Hợp đồng đầu ra: Button](#hợp-đồng-đầu-ra-button): canvas vuông, cặp file light/dark |
| **App Menu** | Icon nhóm menu theo mẫu `18 × 18` (không tự áp dụng cho module icon, app launcher hoặc icon điều hướng khác) | Đọc toàn bộ [app-menu-icons.md](references/app-menu-icons.md): canvas `18 × 18`, stroke cố định, một file |

Chọn profile trước khi thiết kế và không trộn hợp đồng hai loại. Vị trí hiển thị không rõ thuộc loại nào: kiểm tra DOM hoặc cấu hình đích trước khi tạo, không suy đoán từ tên icon.

## Asset chuẩn

Đọc asset cần thiết trước khi thiết kế:

| Asset | Vai trò |
|---|---|
| [delete_icon.svg](assets/delete_icon.svg), [copy_icon.svg](assets/copy_icon.svg) | Mẫu vector tự vẽ cho thao tác xóa và sao chép. Dùng `currentColor` vì chỉ là tham khảo hình học; không sao chép `currentColor` vào file production của Cogover Button |
| [complete_icon_v4.svg](assets/complete_icon_v4.svg), [complete_icon_v4_dark.svg](assets/complete_icon_v4_dark.svg) | Mẫu production light/dark; chuẩn để xuất file Button thực tế |
| [menu_app_budget_sample.svg](assets/menu_app_budget_sample.svg), [menu_app_advance_settlement_sample.svg](assets/menu_app_advance_settlement_sample.svg) | Mẫu production App Menu "Ngân sách" và "Tạm ứng & Hoàn ứng"; chuẩn hình học và màu của App Menu |

## Thư viện icon Workspace

- Đọc, tìm, tái sử dụng hoặc upload icon/ảnh: đọc toàn bộ và làm theo [upload-icon-image-to-workspace-library.md](references/upload-icon-image-to-workspace-library.md) (`GET /api/v1/objects/icon` để liệt kê; upload file rồi `POST /api/v1/objects/icon/add-multiple`). URL icon để cài vào cấu hình đích nằm ở `data[].data` của response list, nhưng ở `data[].id` của response `add-multiple`; không nhầm hai shape.
- Resolve bằng ID hoặc name chính xác; nhiều kết quả phù hợp hoặc cùng name nhưng URL khác nhau thì dừng và làm rõ, không tự chọn. Trước khi upload với một library item name dự kiến, đọc danh sách và kiểm tra trùng name; tái sử dụng URL hiện có khi đúng asset mong muốn, không tạo bản sao không cần thiết.

## Hành vi render đã kiểm chứng của Cogover Button

Icon button được render bằng `<img>` trỏ tới file SVG, trong wrapper tương đương:

```html
<span class="... w-[16px] h-[16px] overflow-hidden">
  <img class="w-[20px] h-[20px] object-contain" ...>
</span>
```

1. SVG là tài liệu ảnh riêng: `currentColor` bên trong không kế thừa màu chữ của button dù computed color của `<img>` có vẻ đúng, và có thể rơi về đen 100%, đậm hơn icon built-in ở light mode.
2. Dark mode của Cogover là trạng thái theme nội bộ, không nhất thiết đổi `prefers-color-scheme` của trình duyệt; media query trong SVG có thể vẫn nhận light mode.
3. Khi chuyển dark mode, Cogover có thể chọn riêng trường `iconDarkMode`; trường này trống thì giao diện có thể không render thẻ `<img>` nào, thay vì fallback sang icon light. Vì vậy luôn sinh hai file và cấu hình đủ icon light lẫn dark khi người dùng muốn icon hoạt động trên cả hai theme.
4. `<img>` còn có thể chịu `max-width: 100%`. SVG không vuông render vượt wrapper `overflow-hidden`: với `viewBox="0 0 384 512"`, ảnh thực tế có thể thành `16 × 20px` trong wrapper `16 × 16px`, phần trên/dưới bị cắt và nét bị phóng lớn khoảng 25%, trông đậm dù màu đúng.

## Hợp đồng đầu ra: Button

Mỗi icon xuất hai file vật lý `<base_name>.svg` (light) và `<base_name>_dark.svg` (dark), trừ khi người dùng yêu cầu tên khác:

```xml
<!-- <base_name>.svg; <base_name>_dark.svg giống hệt, chỉ đổi fill="#ffffff" fill-opacity="0.70" -->
<svg aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 512 512">
  <path fill="#000000" fill-opacity="0.65" d="..."/>
</svg>
```

- Giữ nguyên giữa hai file: `viewBox`, toàn bộ path và thuộc tính hình học, kích thước, tỷ lệ, ý nghĩa thị giác. Chỉ thay `fill` và `fill-opacity`, đặt trực tiếp trên từng `path`; không dùng `currentColor` hoặc `@media (prefers-color-scheme: dark)`.
- Light `#000000`/`0.65`, dark `#ffffff`/`0.70` là mặc định đã kiểm chứng; chỉ đổi khi người dùng yêu cầu hoặc ảnh đối chiếu chứng minh cần điều chỉnh.
- Canvas vuông, thường `viewBox="0 0 512 512"`. Hình học vốn vuông như `circle-check`: giữ `viewBox` gốc. Hình học không vuông: đặt path vào canvas vuông, căn giữa, chừa khoảng an toàn ở các cạnh (chi tiết nhận diện không chạm mép); không ép path về một kích thước tùy tiện. Mẫu đã kiểm chứng cho nguồn `384 × 512`: canvas `512 × 512` và `transform="matrix(1 0 0 0.9375 64 16)"`.
- Giữ tỷ lệ hình học gốc; chỉ hiệu chỉnh quang học nhỏ khi ảnh đối chiếu ở `16 × 16px` chứng minh cần. Mục tiêu: nội dung ảnh không vượt wrapper `16 × 16px`.
- Icon vừa bị cắt vừa trông quá đậm: sửa canvas/viewBox và tỷ lệ render trước; không dùng opacity để che lỗi phóng hình học.

## Hợp đồng đầu ra: App Menu

Theo [app-menu-icons.md](references/app-menu-icons.md): mặc định một file `<base_name>.svg`, `width="18" height="18" viewBox="0 0 18 18" fill="none"`, mọi path `stroke="#45556C" stroke-width="1.3125"` với linecap/linejoin `round`; kiểm tra ở `18 × 18px` và ở kích thước sidebar thật `20 × 20px` trong slot `40 × 20px`. Không tự sinh file dark hoặc áp màu/opacity của Button khi chưa có yêu cầu hay bằng chứng cấu hình.

## Quy trình

1. **Ngữ nghĩa.** Từ tên, hành động và ngữ cảnh nghiệp vụ, chọn biểu tượng dễ nhận biết ở kích thước nhỏ. Button: hoàn thành → check trong vòng tròn, sao chép → hai tài liệu chồng, xóa → thùng rác. App Menu: một ẩn dụ đại diện cả nhóm menu, đối chiếu hai asset `menu_app_*_sample.svg`. Ngữ nghĩa đã rõ thì tự chọn phương án hợp lý, không hỏi lại chỉ để xác nhận một lựa chọn hiển nhiên.
2. **Hình học.** Button: ưu tiên style outline với outline rõ, đầu nét và khoảng âm nhất quán với `delete_icon.svg` và `copy_icon.svg`; ưu tiên một `path` khi nguồn hỗ trợ; không tự thêm nền, vòng tròn hoặc hiệu ứng trang trí ngoài ngữ nghĩa; canvas theo hợp đồng Button. App Menu: hình học stroke trên canvas `18 × 18` theo reference, cho phép nhiều path.
3. **Sinh file.** Button: cùng một path cho cả hai file, chỉ đổi cấu hình màu. App Menu: một file, toàn bộ thuộc tính stroke đặt trực tiếp trên từng path. Không dùng `<style>` khi thuộc tính SVG trực tiếp biểu đạt được cùng kết quả.
4. **Kiểm tra.** App Menu: chạy đầy đủ phần kiểm tra trong [app-menu-icons.md](references/app-menu-icons.md). Button:

   ```bash
   xmllint --noout path/to/icon.svg path/to/icon_dark.svg
   xmllint --xpath 'concat(string(//*[local-name()="path"]/@fill)," / ",string(//*[local-name()="path"]/@fill-opacity))' path/to/icon.svg
   xmllint --xpath 'concat(string(//*[local-name()="path"]/@fill)," / ",string(//*[local-name()="path"]/@fill-opacity))' path/to/icon_dark.svg
   light_path=$(xmllint --xpath 'string(//*[local-name()="path"]/@d)' path/to/icon.svg)
   dark_path=$(xmllint --xpath 'string(//*[local-name()="path"]/@d)' path/to/icon_dark.svg)
   [ "$light_path" = "$dark_path" ]
   ```

   Icon nhiều path: so toàn bộ path theo đúng thứ tự, không chỉ path đầu tiên. Rồi kiểm tra ở kích thước production: render đúng `16 × 16px` (không chỉ preview lớn); đủ góc, nếp gấp và khoảng âm, không phần nào bị wrapper cắt; độ dày thị giác so với icon built-in đứng cạnh, quá đậm thì kiểm tra kích thước render và canvas trước rồi mới cân nhắc opacity. Icon đã cấu hình: đọc DOM, so `getBoundingClientRect()` của wrapper và `<img>`; không chấp nhận chiều rộng hoặc chiều cao ảnh vượt wrapper `overflow-hidden`.
5. **Bàn giao.** Button: link cả file light và dark, nêu màu và opacity đã dùng. App Menu: link file SVG, nêu canvas, màu stroke và độ dày nét. Không tuyên bố dark mode hoạt động chỉ vì SVG hợp lệ; khi đã cấu hình lên Cogover, kiểm tra cả hai trường icon và hai chế độ hiển thị.

## Lỗi cần tránh

| Lỗi | Hậu quả | Cách tránh |
|---|---|---|
| `fill="currentColor"` trong SVG upload | Icon rơi về đen 100%, không khớp màu chữ | Màu và opacity trực tiếp trên `path` |
| Chỉ tạo hoặc chỉ cấu hình icon light | Dark mode có thể bỏ hẳn `<img>` | Tạo và cấu hình cả file `_dark.svg` |
| `@media (prefers-color-scheme: dark)` | Không đổi màu khi Cogover chuyển theme nội bộ | Tách hai file vật lý |
| Icon đen cho dark mode | Chìm vào nền tối | Trắng 70% cho file dark |
| Một file trắng cho cả hai mode | Quá nhạt hoặc mất trên nền sáng | Cặp light/dark riêng |
| Đổi path hoặc viewBox giữa hai biến thể | Icon nhảy kích thước/hình khi đổi theme | Chỉ thay `fill` và `fill-opacity` |
| Upload trực tiếp SVG dọc canvas `384 × 512` | Có thể render thành `16 × 20px`, cắt trên/dưới | Canvas vuông, căn giữa, chừa khoảng an toàn |
| Giảm opacity ngay khi icon trông quá đậm | Che triệu chứng, không sửa lỗi phóng/cắt | Kiểm tra wrapper, kích thước `<img>` và viewBox trước |
| Chỉ xem preview lớn | Bỏ sót mất góc và nét dày ở kích thước thật | Kiểm tra thêm ở `16 × 16px`, so với icon built-in |
| CSS phức tạp trong SVG | Sanitizer hoặc renderer có thể bỏ qua | Thuộc tính SVG trực tiếp |
| Tự upload hoặc sửa layout khi chỉ được yêu cầu sinh file | Vượt phạm vi ý định người dùng | Chỉ ghi hệ thống khi có yêu cầu rõ |
| Trộn quy tắc Button với App Menu | Sai canvas, màu, số file và cách render | Chọn profile trước; App Menu phải đọc `app-menu-icons.md` |

## Chẩn đoán icon đã cấu hình

- So sánh DOM light/dark: button có `<img>` hay không, URL file nào đang được tải. Phân biệt "SVG được tải nhưng màu sai" với "Cogover không render `<img>`", hai lỗi xử lý khác nhau: dark mode không có `<img>` thì bổ sung `iconDarkMode`, đừng tiếp tục chỉnh opacity của file light.
- Đo wrapper và `<img>`: wrapper `16 × 16px`, ảnh `16 × 20px` và wrapper `overflow-hidden` thì lỗi mất góc đến từ tỷ lệ canvas/render, không phải path bị hỏng. Màu đã đúng nhưng icon vẫn đậm hơn built-in: kiểm tra hình học có bị render ở `20px` rồi cắt xuống `16px` không, trước khi đổi opacity.
- Kiểm tra cấu hình light và dark ở nguồn dữ liệu trước khi sửa SVG lần nữa.
