---
name: cogover-icon
description: Sinh, chỉnh sửa, tra cứu và upload icon/ảnh trong thư viện Workspace dành cho Cogover Button và App Menu theo các asset production chuẩn. Dùng khi cần liệt kê, tìm, resolve, tái sử dụng, tạo hoặc upload icon cho Object Button, action button, button trên layout hoặc nhóm App Menu; khi icon bị cắt, mất góc, quá đậm, sai màu, không kế thừa màu, biến mất ở dark mode; hoặc khi cần chuẩn hóa kích thước và theme. Không dùng cho module icon, app launcher hay icon điều hướng khác khi chưa có mẫu chuẩn.
metadata:
  author: cogover
  version: "1.0.1"
---

# Cogover Icon

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

## Phạm vi

- Xử lý hai profile: **Button** và **App Menu**. Chọn đúng profile trước khi thiết kế và không trộn hợp đồng của hai loại.
- App Menu trong skill này là icon nhóm menu theo mẫu `18 × 18`; không tự áp dụng cho module icon, app launcher hoặc icon điều hướng khác.
- Mặc định chỉ sinh và trả file SVG. Không upload file, không cập nhật Object Button, layout hoặc tài khoản nếu người dùng chưa yêu cầu rõ.
- Khi cần đọc, tìm, tái sử dụng hoặc upload icon/ảnh trong thư viện Workspace, đọc toàn bộ và làm theo [upload-icon-image-to-workspace-library.md](references/upload-icon-image-to-workspace-library.md).
- Khi người dùng yêu cầu cài icon lên hệ thống, dùng thêm skill quản lý Button/layout hoặc cấu hình App Menu phù hợp và giữ nguyên mọi cấu hình ngoài icon.
- Chỉnh SVG bằng mã vector. Không dùng ImageGen cho icon kiểu này.

## Tra cứu thư viện Workspace

- Dùng phiên Web App từ `$cogover-api-auth` gọi `GET /api/v1/objects/icon`; không gửi API Key trực tiếp.
- Chỉ coi kết quả hợp lệ khi HTTP thành công, `r == 0` và `data` là mảng.
- Trong response list, dùng `data[].id` để nhận diện bản ghi thư viện và dùng `data[].data` làm URL icon để cài vào cấu hình đích. Không nhầm với response của `POST .../icon/add-multiple`, nơi `data[].id` là URL icon.
- Resolve bằng ID hoặc name chính xác. Nếu có nhiều kết quả phù hợp hoặc cùng name nhưng URL khác nhau, dừng và làm rõ; không tự chọn kết quả mơ hồ.
- Trước khi upload với một library item name dự kiến, đọc danh sách hiện tại và kiểm tra trùng name. Tái sử dụng URL hiện có khi đúng asset mong muốn; không tạo bản sao không cần thiết.

## Chọn profile

- Chọn **Button** cho Object Button, action button và button trên layout. Dùng canvas vuông production, màu light/dark trực tiếp và xuất một cặp file.
- Chọn **App Menu** cho icon nhóm menu. Đọc toàn bộ [app-menu-icons.md](references/app-menu-icons.md), dùng canvas `18 × 18`, `fill="none"`, stroke cố định và mặc định xuất một file.
- Nếu vị trí hiển thị không rõ thuộc loại nào, kiểm tra DOM hoặc cấu hình đích trước khi tạo; không suy đoán từ tên icon.

## Nguồn và giấy phép

Đọc [assets/NOTICE.md](assets/NOTICE.md) khi dùng hoặc phân phối SVG đi kèm. Hai icon hoàn thành có nguồn Font Awesome Free và giữ attribution CC BY 4.0; bốn SVG còn lại là hình học tự vẽ theo MIT. Không lấy icon không rõ quyền phân phối làm asset mẫu.

## Asset chuẩn

Đọc các file cần thiết trước khi thiết kế:

- [delete_icon.svg](assets/delete_icon.svg): mẫu vector tự vẽ cho thao tác xóa.
- [copy_icon.svg](assets/copy_icon.svg): mẫu vector tự vẽ cho thao tác sao chép.
- [complete_icon_v4.svg](assets/complete_icon_v4.svg): mẫu production cho light mode.
- [complete_icon_v4_dark.svg](assets/complete_icon_v4_dark.svg): mẫu production cho dark mode.
- [menu_app_budget_sample.svg](assets/menu_app_budget_sample.svg): mẫu production App Menu “Ngân sách”.
- [menu_app_advance_settlement_sample.svg](assets/menu_app_advance_settlement_sample.svg): mẫu production App Menu “Tạm ứng & Hoàn ứng”.

`delete_icon.svg` và `copy_icon.svg` dùng `currentColor` vì là asset tham khảo hình học. Không sao chép `currentColor` vào file production của Cogover Button. Cặp `complete_icon_v4*` là chuẩn để xuất file thực tế.

Hai asset `menu_app_*_sample.svg` là chuẩn hình học và màu cho App Menu. Không chuyển chúng sang hợp đồng fill/opacity của Button.

## Ràng buộc kích thước — Button

Cogover đã được quan sát render icon button theo cấu trúc tương đương:

```html
<span class="... w-[16px] h-[16px] overflow-hidden">
  <img class="w-[20px] h-[20px] object-contain" ...>
</span>
```

`img` còn có thể chịu `max-width: 100%`. Với SVG dọc `viewBox="0 0 384 512"`, ảnh thực tế có thể thành `16 × 20px` trong wrapper `16 × 16px`: phần trên/dưới bị cắt và nét bị phóng lớn khoảng 25%.

Vì vậy:

- Xuất canvas vuông cho icon button production khi nguồn hình học không vuông; thường dùng `viewBox="0 0 512 512"`.
- Căn hình học vào giữa canvas và chừa khoảng an toàn ở các cạnh. Không để chi tiết nhận diện chạm mép.
- Giữ tỷ lệ hình học gốc theo mặc định; chỉ dùng hiệu chỉnh quang học nhỏ khi ảnh đối chiếu ở `16 × 16px` chứng minh cần thiết.
- Với hình học nguồn `384 × 512`, mẫu đã kiểm chứng là canvas `512 × 512` và `transform="matrix(1 0 0 0.9375 64 16)"`.
- Kiểm tra kích thước render thật. Mục tiêu là nội dung ảnh không vượt wrapper `16 × 16px`.
- Khi icon vừa bị cắt vừa trông quá đậm, sửa canvas/viewBox và tỷ lệ render trước khi giảm opacity. Không dùng opacity để che lỗi phóng hình học.

## Hợp đồng đầu ra — Button

Tạo hai file vật lý cho mỗi icon, trừ khi người dùng yêu cầu tên khác:

```text
<base_name>.svg
<base_name>_dark.svg
```

Giữ nguyên giữa hai file:

- `viewBox`;
- toàn bộ path và thuộc tính hình học;
- kích thước và tỷ lệ;
- ý nghĩa thị giác.

Chỉ thay cấu hình màu:

```xml
<!-- Light mode -->
<path fill="#000000" fill-opacity="0.65" d="..."/>

<!-- Dark mode -->
<path fill="#ffffff" fill-opacity="0.70" d="..."/>
```

Dùng hai mức opacity trên làm mặc định đã kiểm chứng. Chỉ đổi khi người dùng yêu cầu hoặc ảnh đối chiếu chứng minh cần điều chỉnh.

## Hợp đồng đầu ra — App Menu

Đọc và làm theo [app-menu-icons.md](references/app-menu-icons.md). Tóm tắt bắt buộc:

- Mặc định tạo một file `<base_name>.svg`.
- Dùng `width="18"`, `height="18"`, `viewBox="0 0 18 18"` và `fill="none"`.
- Dùng `stroke="#45556C"`, `stroke-width="1.3125"`, `stroke-linecap="round"` và `stroke-linejoin="round"` trên mọi path.
- Kiểm tra cả kích thước thiết kế `18 × 18px` và kích thước sidebar thực tế `20 × 20px`; icon nằm trong slot `40 × 20px`.
- Không tự sinh file dark hoặc áp màu/opacity của Button nếu chưa có yêu cầu hay bằng chứng cấu hình.

## Quy trình

### 1. Xác định loại icon và ngữ nghĩa

- Xác định profile Button hoặc App Menu từ vị trí và cấu hình đích.
- Đọc tên, hành động và ngữ cảnh nghiệp vụ.
- Chọn biểu tượng dễ nhận biết ở kích thước nhỏ. Với Button: hoàn thành → check trong vòng tròn; sao chép → hai tài liệu chồng; xóa → thùng rác.
- Với App Menu, chọn một ẩn dụ đại diện cho cả nhóm menu và đối chiếu hai asset `menu_app_*_sample.svg`.
- Nếu ngữ nghĩa đã rõ, tự chọn phương án hợp lý; không hỏi lại chỉ để xác nhận một lựa chọn hiển nhiên.

### 2. Chọn hình học

- Với Button, ưu tiên style **outline**: outline rõ, đầu nét và khoảng âm nhất quán với `delete_icon.svg` và `copy_icon.svg`.
- Ưu tiên một `path` khi nguồn icon hỗ trợ; không tự thêm nền, vòng tròn hoặc hiệu ứng trang trí ngoài ngữ nghĩa.
- Với Button, giữ tỷ lệ và ý nghĩa của hình học nguồn, nhưng chuẩn hóa canvas production thành vuông khi renderer `16 × 16px` của Cogover có thể cắt SVG không vuông. Không ép path về một kích thước tùy tiện; đặt path vào canvas vuông và căn giữa.
- Với hình học Button vốn đã vuông như `circle-check`, giữ `viewBox="0 0 512 512"` gốc.
- Với App Menu, dùng hình học stroke trên canvas `18 × 18` theo [app-menu-icons.md](references/app-menu-icons.md); cho phép nhiều path.
- Không biến raster thành SVG giả bằng cách nhúng bitmap.

### 3. Sinh file production

- Với Button, dùng cùng một path cho cả hai file và chỉ đổi cấu hình màu.
- Với Button, đặt `fill` và `fill-opacity` trực tiếp trên từng `path`; không dùng `currentColor` hoặc `@media (prefers-color-scheme: dark)`.
- Với App Menu, mặc định xuất một file và đặt toàn bộ thuộc tính stroke trực tiếp trên từng path theo reference.
- Không dùng `<style>` nếu thuộc tính SVG trực tiếp có thể biểu đạt cùng kết quả.

Mẫu tối giản:

```xml
<svg aria-hidden="true" focusable="false"
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 512 512">
  <path fill="#000000" fill-opacity="0.65" d="..."/>
</svg>
```

### 4. Kiểm tra kỹ thuật

Các lệnh dưới đây áp dụng cho Button. Với App Menu, chạy đầy đủ phần kiểm tra trong [app-menu-icons.md](references/app-menu-icons.md).

Kiểm tra XML của cả hai file:

```bash
xmllint --noout path/to/icon.svg path/to/icon_dark.svg
```

Kiểm tra màu:

```bash
xmllint --xpath 'concat(string(//*[local-name()="path"]/@fill)," / ",string(//*[local-name()="path"]/@fill-opacity))' path/to/icon.svg
xmllint --xpath 'concat(string(//*[local-name()="path"]/@fill)," / ",string(//*[local-name()="path"]/@fill-opacity))' path/to/icon_dark.svg
```

Kiểm tra path của hai biến thể giống nhau:

```bash
light_path=$(xmllint --xpath 'string(//*[local-name()="path"]/@d)' path/to/icon.svg)
dark_path=$(xmllint --xpath 'string(//*[local-name()="path"]/@d)' path/to/icon_dark.svg)
[ "$light_path" = "$dark_path" ]
```

Nếu icon có nhiều path, kiểm tra toàn bộ path theo đúng thứ tự thay vì chỉ path đầu tiên.

Kiểm tra thêm kích thước production:

- Render hoặc xem icon ở đúng `16 × 16px`, không chỉ xem preview lớn.
- Xác nhận đủ góc, nếp gấp và khoảng âm; không có phần nào bị wrapper cắt.
- So sánh độ dày thị giác với icon built-in đứng cạnh. Nếu quá đậm, kiểm tra kích thước render và canvas trước, sau đó mới cân nhắc opacity.
- Khi icon đã được cấu hình, đọc DOM để so sánh `getBoundingClientRect()` của wrapper và `<img>`. Không chấp nhận chiều rộng hoặc chiều cao ảnh vượt wrapper có `overflow-hidden`.

### 5. Bàn giao

- Với Button, trả link tới cả file light và dark; nêu màu và opacity đã dùng.
- Với App Menu, trả link file SVG; nêu canvas, màu stroke và độ dày nét.
- Không tuyên bố dark mode hoạt động chỉ vì SVG hợp lệ; khi đã cấu hình lên Cogover, phải kiểm tra cả hai trường icon và hai chế độ hiển thị.

## Hành vi theme của Cogover Button

Ghi nhớ các quan sát đã kiểm chứng trên Cogover:

1. Icon button được render dưới dạng `<img>` trỏ tới file SVG. SVG là tài liệu ảnh riêng, nên `currentColor` bên trong không kế thừa màu chữ của button dù computed color của `<img>` có vẻ đúng.
2. `currentColor` trong SVG upload có thể rơi về đen 100%, làm icon đậm hơn các icon built-in ở light mode.
3. Dark mode của Cogover là trạng thái theme nội bộ. Nó không nhất thiết thay đổi `prefers-color-scheme` của trình duyệt; media query trong SVG có thể vẫn nhận light mode.
4. Khi chuyển sang dark mode, Cogover có thể chọn riêng trường `iconDarkMode`. Nếu trường này trống, giao diện có thể không render thẻ `<img>` nào cho icon, thay vì fallback sang icon light.
5. Vì vậy, luôn sinh hai file và cấu hình đủ cả icon light lẫn icon dark khi người dùng muốn icon hoạt động trên cả hai theme.
6. Wrapper icon button có thể cố định `16 × 16px` và `overflow-hidden`, trong khi `<img>` khai báo `20 × 20px`. SVG không vuông có thể render vượt wrapper, gây cắt góc và làm nét trông đậm dù màu đúng.

## Lỗi cần tránh

| Lỗi | Hậu quả | Cách tránh |
|---|---|---|
| Dùng `fill="currentColor"` trong SVG upload | Icon rơi về đen 100% và không khớp màu chữ | Dùng màu và opacity trực tiếp trên `path` |
| Chỉ tạo hoặc chỉ cấu hình icon light | Dark mode có thể bỏ hẳn `<img>` | Tạo và cấu hình cả file `_dark.svg` |
| Dùng `@media (prefers-color-scheme: dark)` | Không đổi màu khi Cogover chuyển theme nội bộ | Tách hai file vật lý |
| Dùng icon đen cho dark mode | Icon chìm vào nền tối | Dùng trắng 70% cho file dark |
| Dùng một file trắng cho cả hai mode | Icon quá nhạt hoặc mất trên nền sáng | Dùng cặp light/dark riêng |
| Đổi path hoặc viewBox giữa hai biến thể | Icon nhảy kích thước/hình khi đổi theme | Chỉ thay `fill` và `fill-opacity` |
| Upload SVG dọc trực tiếp với canvas `384 × 512` | Có thể render thành `16 × 20px`, bị cắt trên/dưới | Đặt hình học vào canvas vuông, căn giữa và chừa khoảng an toàn |
| Giảm opacity ngay khi icon trông quá đậm | Che triệu chứng nhưng không sửa lỗi phóng/cắt | Kiểm tra wrapper, kích thước `<img>` và viewBox trước |
| Chỉ xem preview lớn | Bỏ sót mất góc và nét dày ở kích thước thật | Kiểm tra thêm ở `16 × 16px` và so với icon built-in |
| Dùng CSS phức tạp trong SVG | Có thể bị sanitizer hoặc renderer bỏ qua | Ưu tiên thuộc tính SVG trực tiếp |
| Tự upload hoặc sửa layout khi chỉ được yêu cầu sinh file | Mở rộng phạm vi ngoài ý định người dùng | Chỉ ghi hệ thống khi có yêu cầu rõ |
| Trộn quy tắc Button với App Menu | Sai canvas, màu, số file và cách render | Chọn profile trước; App Menu phải đọc `app-menu-icons.md` |

## Khi cần chẩn đoán icon đã cấu hình

- So sánh DOM light/dark: kiểm tra button có `<img>` hay không và URL file nào đang được tải.
- Phân biệt “SVG được tải nhưng màu sai” với “Cogover không render `<img>`”. Hai lỗi này có cách xử lý khác nhau.
- Đo wrapper và `<img>`. Nếu wrapper là `16 × 16px`, ảnh là `16 × 20px` và wrapper dùng `overflow-hidden`, kết luận lỗi mất góc đến từ tỷ lệ canvas/render, không phải path bị hỏng.
- Nếu màu đã đúng nhưng icon vẫn đậm hơn icon built-in, kiểm tra xem hình học có đang bị render ở `20px` rồi cắt xuống `16px` hay không trước khi đổi opacity.
- Kiểm tra cấu hình light và dark ở nguồn dữ liệu trước khi sửa SVG lần nữa.
- Nếu dark mode không có `<img>`, bổ sung `iconDarkMode`; đừng tiếp tục chỉnh opacity của file light.
