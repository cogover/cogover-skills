# Thiết kế bảng cho Object Filter

Thiết kế `tableSettings` sau khi đã hiểu Object và nghiệp vụ danh sách. Thứ tự và độ rộng cột là cấu hình bắt buộc, không phải phần trang trí tùy chọn.

## Mục lục

- [Nguồn tham khảo](#nguồn-tham-khảo)
- [Phân tích Object](#phân-tích-object)
- [Chọn cột](#chọn-cột)
- [Sắp thứ tự cột](#sắp-thứ-tự-cột)
- [Chọn trường sắp xếp](#chọn-trường-sắp-xếp)
- [Đặt độ rộng](#đặt-độ-rộng)
- [Dựng tableSettings](#dựng-tablesettings)
- [Kiểm tra trước và sau khi tạo](#kiểm-tra-trước-và-sau-khi-tạo)

## Nguồn tham khảo

Đối chiếu schema, thứ tự và width với hai filter thực tế:

- Sales filter “My Leads”: [JSON snapshot đã ẩn danh](sample-filter-my-leads.json)
- Finance filter “Tất cả Công nợ phải thu”: [JSON snapshot đã ẩn danh](sample-filter-accounts-receivable.json)

Các snapshot đã bỏ metadata workspace, audit và personnel không ảnh hưởng tới cấu hình filter; các field chức năng, conditions, sort, layout và `tableSettings` được giữ lại. Không sao chép máy móc field slug, thứ tự hoặc width từ mẫu sang Object khác. Filter standard có thể dùng width mặc định đồng loạt; filter custom vẫn phải được thiết kế theo nghiệp vụ.

## Phân tích Object

Trước khi chọn cột:

1. Lấy Object bằng `$object-info`; xác nhận đúng `id`, `name` và `slug`.
2. Đọc tên, slug và description của Object. Xác định Object thuộc nhóm nào:
   - Master data: khách hàng, sản phẩm, nhân sự, nhà cung cấp.
   - Giao dịch: đơn hàng, hóa đơn, thanh toán, báo giá, hợp đồng.
   - Công việc/hoạt động: task, ticket, cuộc gọi, lịch hẹn.
   - Dữ liệu tổng hợp/hệ thống: bản ghi tính toán, log, cấu hình.
3. Đọc toàn bộ fields và ý nghĩa của chúng, không chỉ slug. Chú ý field chính, mã/serial, status, owner, lookup nghiệp vụ, tiền/số lượng, deadline và timestamps.
4. Viết ra một câu nghiệp vụ nội bộ: “Trong danh sách này, người dùng cần nhìn thấy ... để quyết định ...”. Nếu chưa viết được câu này từ metadata, hỏi người dùng làm rõ.
5. Xác định thao tác thường gặp: nhận diện bản ghi, theo dõi trạng thái, phân công, so sánh giá trị, phát hiện quá hạn hay mở chi tiết.

## Chọn cột

Chỉ hiển thị các cột giúp người dùng nhận diện hoặc ra quyết định. Thường dùng 5–10 cột; có thể ít hoặc nhiều hơn nếu nghiệp vụ thực sự cần.

Ưu tiên:

1. Mã/serial và tên/tiêu đề giúp nhận diện bản ghi.
2. Trạng thái, giai đoạn, loại hoặc mức ưu tiên.
3. Owner/assignee hoặc lookup chủ thể chính.
4. Các field nghiệp vụ quyết định hành động: số tiền, số lượng, công nợ, hạn xử lý, đối tác, sản phẩm chính.
5. Ngày nghiệp vụ quan trọng; thêm `created` theo mặc định ở cuối và chỉ dùng `updated` khi thực sự hữu ích.

Với filter mới, mặc định thêm `created` (nhãn UI thường là “Tạo lúc”) làm cột hiển thị cuối cùng nếu field này tồn tại và đang active. Chỉ bỏ cột này khi người dùng yêu cầu hoặc nghiệp vụ có lý do rõ ràng; không mặc định thêm `updated`.

Thường loại bỏ:

- Field hệ thống ít dùng như `id`, `created_by`, `updated_by`.
- Long text, file hoặc metadata kỹ thuật nếu không cần để quét danh sách.
- Field trùng ý nghĩa với cột khác.
- Lookup ngược hoặc field chỉ phục vụ liên kết nội bộ nhưng không giúp quyết định.
- Field inactive hoặc không tồn tại trong Object hiện tại.

Không tự động thêm một field vào bảng chỉ vì field đó xuất hiện trong `conditions`. Một field lọc có thể không cần hiển thị; ngược lại, cột nhận diện chính thường vẫn cần dù không tham gia điều kiện.

## Sắp thứ tự cột

Sắp theo luồng đọc từ trái sang phải:

1. Mã/serial ngắn.
2. Tên hoặc tiêu đề chính.
3. Trạng thái/giai đoạn/mức ưu tiên.
4. Owner/assignee hoặc chủ thể liên quan chính.
5. Các field nghiệp vụ quan trọng theo trình tự xử lý.
6. Giá trị tiền tệ, số lượng, phần trăm hoặc tổng hợp.
7. Deadline/ngày nghiệp vụ rồi mới đến timestamps hệ thống; đặt `created` ở cuối danh sách field hiển thị mặc định.
8. Cột hành động ở cuối nếu cấu hình của hệ thống có cột này.

Điều chỉnh quy tắc chung theo nghiệp vụ. Ví dụ, danh sách công nợ có thể cần khách hàng → số chứng từ → số tiền còn lại → ngày đến hạn → trạng thái; không ép mã luôn đứng đầu nếu cách đọc thực tế khác.

Khi dùng pinned columns:

- Chỉ pin trái cột nhận diện cần giữ khi cuộn ngang, thường là mã hoặc tên.
- Với saved filter trong hai mẫu, dùng `actionColumn` và pin bên phải. Không dùng `_action_column`; key này thuộc cấu hình related-list/layout khác.
- Không pin quá nhiều cột làm giảm vùng xem dữ liệu.

## Chọn trường sắp xếp

Chọn `sortFields` độc lập với `showingColumns`: field nhận diện tốt hoặc đứng đầu bảng chưa chắc là khóa sắp xếp tốt. Luôn đọc `fieldType`, ý nghĩa và dữ liệu dự kiến của field trước khi chọn sort.

- Không mặc định dùng `name asc` chỉ vì Object có field `name` hoặc thuộc nhóm master data.
- Khi `name.fieldType` là `short-text`, coi đây là nhãn do người dùng nhập, không phải mã tuần tự ổn định. Không dùng `name` làm sort mặc định.
- Chỉ sắp xếp theo `name` khi người dùng yêu cầu, nghiệp vụ xác nhận cần thứ tự chữ cái, hoặc metadata cho thấy `name` thực chất là mã tuần tự như `auto_number`.
- Nếu không có yêu cầu nghiệp vụ khác, ưu tiên `created desc` khi field `created` tồn tại và active. Với Object giao dịch, có thể ưu tiên ngày nghiệp vụ phù hợp rồi dùng `created desc` làm khóa phụ.
- Khi cập nhật filter hiện có, không thay sort đang hoạt động bằng `name asc` chỉ để “chuẩn hóa”. Giữ nguyên nếu metadata chưa cung cấp căn cứ tốt hơn.

## Đặt độ rộng

Đặt width theo nội dung thực tế và nhãn hiển thị. Dùng các khoảng sau làm điểm bắt đầu, rồi tăng/giảm theo tên field và dữ liệu dự kiến:

| Loại nội dung | Width gợi ý |
|---|---:|
| Mã/serial, `auto_number` | 90–120 px |
| Tên/tiêu đề chính | 260–380 px |
| Short text phụ | 160–240 px |
| Status/single choice/rating | 120–160 px |
| Multi choices/label | 180–240 px |
| Owner/personnel lookup | 150–190 px |
| Lookup nghiệp vụ khác | 180–240 px |
| Phone/email/URL | 190–260 px |
| Boolean | 90–110 px |
| Numeric/quantity | 110–150 px |
| Currency/decimal | 140–180 px |
| Percent | 100–130 px |
| Date | 140–170 px |
| Date time | 170–210 px |
| `created` / “Tạo lúc” | 200–230 px |
| Long text nếu buộc hiển thị | 240–340 px |
| File/attachment | 160–200 px |
| Cột hành động `actionColumn` | 32 px |

Quy tắc điều chỉnh:

- Tăng width nếu nhãn dài hoặc giá trị thường dài; giảm nếu nội dung là mã cố định ngắn.
- Cấp nhiều không gian nhất cho cột dùng để nhận diện bản ghi.
- Không đặt tất cả cột cùng `200px`.
- Không làm cột trạng thái/boolean rộng hơn cột tên nếu không có lý do nghiệp vụ.
- Ước lượng tổng chiều rộng; nếu bảng quá rộng, ưu tiên bỏ cột ít giá trị trước khi ép mọi cột quá hẹp.

## Dựng tableSettings

`tableSettings` trong payload filter là JSON string. Object trước khi serialize có dạng:

```json
{
  "columns": [
    {"key": "serial", "width": 100},
    {"key": "name", "width": 320},
    {"key": "status", "width": 140},
    {"key": "owner", "width": 170},
    {"key": "amount", "width": 160},
    {"key": "due_date", "width": 160},
    {"key": "created", "width": 220},
    {"key": "actionColumn", "width": 32}
  ],
  "showingColumns": [
    "serial",
    "name",
    "status",
    "owner",
    "amount",
    "due_date",
    "created"
  ],
  "pinnedColumns": {
    "left": ["serial"],
    "right": ["actionColumn"]
  }
}
```

Đây là ví dụ hình dạng, không phải payload dùng chung. `actionColumn` được pin nên không bắt buộc xuất hiện trong `showingColumns`; giữ cách này cho filter mới trừ khi UI/API workspace yêu cầu khác.

Bảo đảm:

- Mỗi key trong `showingColumns` có cấu hình width tương ứng trong `columns`.
- Dùng `showingColumns` làm nguồn quyết định thứ tự hiển thị. `columns` là danh sách cấu hình width và có thể chứa cả field đang ẩn; không dựa vào thứ tự `columns` để suy ra thứ tự trên UI.
- Mọi key là field slug thật hoặc cột đặc biệt được hệ thống hỗ trợ.
- Width là số nguyên dương.
- JSON object parse được trước khi serialize và JSON string parse ngược lại ra đúng object.

## Kiểm tra trước và sau khi tạo

Trước khi gọi create:

1. Tóm tắt Object và câu nghiệp vụ đã suy ra.
2. Liệt kê `showingColumns` theo thứ tự cùng width.
3. Kiểm tra field nhận diện chính không bị thiếu hoặc quá hẹp.
4. Kiểm tra status/owner/amount/deadline phù hợp nghiệp vụ nếu Object có các field này.
5. Kiểm tra `created` nằm ở cuối `showingColumns` nếu field tồn tại và người dùng không yêu cầu bỏ.
6. Kiểm tra từng field trong `sortFields` tồn tại, active và phù hợp `fieldType`; nếu sort theo `name`, xác nhận rõ lý do thay vì suy ra từ slug.
7. Kiểm tra tổng số cột và khả năng đọc trên màn hình phổ biến.

Sau khi gọi create và view:

1. Parse `data.tableSettings`.
2. So sánh chính xác thứ tự `showingColumns` và width trong `columns` với thiết kế.
3. So sánh `sortFields` đã lưu với thiết kế và xác nhận không phát sinh `name asc` trên field `short-text` ngoài chủ ý.
4. Xác nhận `created` vẫn là field hiển thị cuối cùng và có width ngày giờ phù hợp.
5. Nếu server chuẩn hóa hoặc loại bỏ key, báo khác biệt; không tuyên bố thành công khi cấu hình UX chưa được lưu đúng.
