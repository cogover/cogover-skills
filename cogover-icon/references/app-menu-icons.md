# Icon App Menu

## Mẫu đã kiểm chứng

Đọc hai asset trước khi tạo icon App Menu: [menu_app_budget_sample.svg](../assets/menu_app_budget_sample.svg) (Ngân sách, dạng lịch/kế hoạch) và [menu_app_advance_settlement_sample.svg](../assets/menu_app_advance_settlement_sample.svg) (Tạm ứng & Hoàn ứng, dạng ví). Hai file là mẫu vector tự vẽ cho bộ skill, giữ canvas, màu và stroke của profile App Menu; nguồn và giấy phép: [NOTICE.md](../assets/NOTICE.md).

## Hành vi hiển thị đã kiểm chứng

Trên sidebar Cogover Finance:

- SVG có kích thước tự nhiên `18 × 18`, nhưng `<img class="w-5">` hiển thị ở `20 × 20px`; canvas vuông được phóng đều từ `18px` lên `20px`, không méo hoặc cắt.
- `<img>` có `max-width: 100%`, `opacity: 1`, không có `filter`; màu nhìn thấy đến trực tiếp từ `stroke="#45556C"` trong SVG.
- Icon nằm trong slot rộng `40px`, cao `20px`; hàng tiêu đề nhóm menu cao `40px` và căn giữa theo chiều dọc.
- Stroke nguồn `1.3125` hiển thị tương đương khoảng `1.46px` sau khi phóng lên `20px`, phù hợp độ dày thị giác của sidebar.
- Trạng thái chọn nằm ở menu con; icon tiêu đề nhóm giữ màu stroke cố định trong trạng thái quan sát được.

## Hợp đồng production

Mặc định một file SVG cho mỗi icon App Menu:

```xml
<svg xmlns="http://www.w3.org/2000/svg"
  width="18" height="18" viewBox="0 0 18 18" fill="none">
  <path d="..."
    stroke="#45556C"
    stroke-width="1.3125"
    stroke-linecap="round"
    stroke-linejoin="round"/>
</svg>
```

- Canvas vuông `18 × 18` gồm cả `width`, `height` và `viewBox="0 0 18 18"`; hình học outline với `fill="none"` ở root.
- Đặt trực tiếp `stroke="#45556C"`, `stroke-width="1.3125"`, `stroke-linecap="round"`, `stroke-linejoin="round"` nhất quán trên mọi path; không dùng `currentColor` khi chưa có bằng chứng renderer hỗ trợ.
- Chừa khoảng an toàn quanh hình: hai mẫu giữ tọa độ chính trong khoảng xấp xỉ `1.5` đến `16.5`, đủ an toàn khi phóng lên `20px`. Ưu tiên tọa độ theo lưới `0.75` để nét cân ở `18px`; chỉ dùng số lẻ chi tiết khi đường cong cần thiết.
- Cho phép nhiều path khi giúp hình học rõ và dễ bảo trì.
- Không áp màu fill/opacity, canvas `512 × 512` hoặc hợp đồng hai file light/dark của Button cho App Menu. Chỉ tạo biến thể dark khi người dùng yêu cầu hoặc cấu hình App Menu đích chứng minh có trường dark riêng.

## Quy trình tạo

1. Đọc tên menu và chọn một ẩn dụ duy nhất, nhận ra được ở `18px`; đối chiếu độ phức tạp, khoảng âm và độ dày với hai asset mẫu.
2. Vẽ bằng path stroke; tránh vùng fill lớn, chi tiết trang trí và nét nhỏ hơn chuẩn.
3. Render ở `18 × 18px`, sau đó kiểm tra lại ở kích thước hiển thị thực tế `20 × 20px` cạnh một icon App Menu mẫu.
4. Kiểm tra XML và toàn bộ thuộc tính stroke (mục dưới) trước khi bàn giao.

## Kiểm tra kỹ thuật

```bash
xmllint --noout path/to/menu_icon.svg

xmllint --xpath \
  'concat(string(/*[local-name()="svg"]/@width)," × ",string(/*[local-name()="svg"]/@height)," / ",string(/*[local-name()="svg"]/@viewBox)," / fill=",string(/*[local-name()="svg"]/@fill))' \
  path/to/menu_icon.svg

xmllint --xpath \
  'count(//*[local-name()="path" and @stroke="#45556C" and @stroke-width="1.3125" and @stroke-linecap="round" and @stroke-linejoin="round"]) = count(//*[local-name()="path"])' \
  path/to/menu_icon.svg
```

Kết quả mong đợi của hai lệnh XPath lần lượt là `18 × 18 / 0 0 18 18 / fill=none` và `true`. Sau đó xác nhận trên DOM rằng `<img>` là `20 × 20px`, không bị méo/cắt và nằm trong slot icon `40 × 20px`.
