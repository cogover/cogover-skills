# Thiết kế bảng cho Object Filter

Thứ tự cột, độ rộng và `sortFields` là cấu hình bắt buộc của saved filter, không phải trang trí tùy chọn; thiết kế sau khi đã hiểu Object và nghiệp vụ danh sách.

## Mục lục

- [Nguồn tham khảo](#nguồn-tham-khảo)
- [Phân tích Object](#phân-tích-object)
- [Chọn và sắp cột](#chọn-và-sắp-cột)
- [Chọn trường sắp xếp](#chọn-trường-sắp-xếp)
- [Đặt độ rộng](#đặt-độ-rộng)
- [Dựng tableSettings](#dựng-tablesettings)
- [Kiểm tra sau khi tạo](#kiểm-tra-sau-khi-tạo)

## Nguồn tham khảo

Hai snapshot filter thật đã ẩn danh (bỏ metadata workspace, audit, personnel; giữ conditions, sort, layout và `tableSettings`) để đối chiếu schema, thứ tự và width:

- Sales "My Leads": [sample-filter-my-leads.json](sample-filter-my-leads.json)
- Finance "Tất cả Công nợ phải thu": [sample-filter-accounts-receivable.json](sample-filter-accounts-receivable.json)

Không sao chép máy móc field slug, thứ tự hoặc width từ mẫu sang Object khác. Filter standard có thể dùng width mặc định đồng loạt; filter custom phải thiết kế theo nghiệp vụ.

## Phân tích Object

1. Lấy Object bằng `$object-info`; xác nhận đúng `id`, `name`, `slug`.
2. Từ tên, slug và description, xếp Object vào nhóm: master data (khách hàng, sản phẩm, nhân sự, nhà cung cấp); giao dịch (đơn hàng, hóa đơn, thanh toán, báo giá, hợp đồng); công việc/hoạt động (task, ticket, cuộc gọi, lịch hẹn); dữ liệu tổng hợp/hệ thống (bản ghi tính toán, log, cấu hình).
3. Đọc toàn bộ fields và ý nghĩa, không chỉ slug: field chính, mã/serial, status, owner, lookup nghiệp vụ, tiền/số lượng, deadline, timestamps.
4. Viết câu nghiệp vụ nội bộ "Trong danh sách này, người dùng cần nhìn thấy ... để quyết định ..." và thao tác thường gặp (nhận diện bản ghi, theo dõi trạng thái, phân công, so sánh giá trị, phát hiện quá hạn, mở chi tiết). Chưa viết được từ metadata thì hỏi người dùng làm rõ.

## Chọn và sắp cột

Chỉ hiển thị cột giúp nhận diện hoặc ra quyết định, thường 5–10 cột; không mặc định hiển thị tất cả fields. Thứ tự ưu tiên dưới đây cũng là thứ tự đọc trái sang phải:

1. Mã/serial ngắn.
2. Tên hoặc tiêu đề chính.
3. Trạng thái, giai đoạn, loại hoặc mức ưu tiên.
4. Owner/assignee hoặc lookup chủ thể chính.
5. Field nghiệp vụ quyết định hành động, theo trình tự xử lý: công nợ, hạn xử lý, đối tác, sản phẩm chính.
6. Tiền tệ, số lượng, phần trăm hoặc tổng hợp.
7. Deadline/ngày nghiệp vụ, rồi timestamps hệ thống. `created` (nhãn UI thường là "Tạo lúc") là field hiển thị cuối cùng nếu tồn tại và active, đặt trước cột hành động nếu cột này cũng nằm trong `showingColumns`; chỉ bỏ khi người dùng yêu cầu hoặc nghiệp vụ có lý do rõ. Không mặc định thêm `updated`.
8. Cột hành động ở cuối nếu cấu hình có cột này.

Điều chỉnh theo cách đọc thực tế; ví dụ danh sách công nợ: khách hàng → số chứng từ → số tiền còn lại → ngày đến hạn → trạng thái, không ép mã luôn đứng đầu.

Thường loại bỏ: `id`, `created_by`, `updated_by`; long text, file, metadata kỹ thuật; field trùng ý nghĩa với cột khác; lookup ngược hoặc field chỉ phục vụ liên kết nội bộ; field inactive hoặc không tồn tại trong Object. Không thêm field vào bảng chỉ vì nó nằm trong `conditions`; ngược lại, cột nhận diện chính vẫn cần dù không tham gia điều kiện.

Pinned columns: chỉ pin trái cột nhận diện cần giữ khi cuộn ngang (mã hoặc tên); pin phải `actionColumn` như hai mẫu, không dùng `_action_column` (key của cấu hình related-list/layout khác); không pin nhiều cột làm hẹp vùng dữ liệu.

## Chọn trường sắp xếp

`sortFields` độc lập với `showingColumns`: field nhận diện tốt hoặc đứng đầu bảng chưa chắc là khóa sắp xếp tốt. Đọc `fieldType`, ý nghĩa và dữ liệu dự kiến của field trước khi chọn.

- Mặc định `created desc` khi `created` tồn tại và active. Object giao dịch có thể ưu tiên ngày nghiệp vụ phù hợp rồi `created desc` làm khóa phụ.
- Không mặc định `name asc` chỉ vì Object có field `name` hoặc là master data. `name` có `fieldType` `short_text` là nhãn người dùng nhập, không phải mã tuần tự ổn định. Chỉ sort theo `name` khi người dùng yêu cầu, nghiệp vụ xác nhận cần thứ tự chữ cái, hoặc metadata cho thấy `name` thực chất là mã tuần tự như `auto_number`.
- Khi cập nhật filter hiện có, không thay sort đang hoạt động bằng `name asc` để "chuẩn hóa"; giữ nguyên nếu metadata chưa cho căn cứ tốt hơn.

## Đặt độ rộng

Điểm bắt đầu theo loại nội dung; tăng nếu nhãn hoặc giá trị thường dài, giảm nếu là mã cố định ngắn:

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

- Cấp nhiều không gian nhất cho cột nhận diện; không để cột trạng thái/boolean rộng hơn cột tên nếu không có lý do nghiệp vụ.
- Mỗi field một width theo nội dung dự kiến; không đặt tất cả cột cùng một width như `200px`.
- Ước lượng tổng chiều rộng; bảng quá rộng thì bỏ cột ít giá trị trước khi ép mọi cột quá hẹp.

## Dựng tableSettings

`tableSettings` trong payload là JSON string. Object trước khi serialize có dạng sau (ví dụ hình dạng, không phải payload dùng chung):

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

- `showingColumns` quyết định thứ tự hiển thị. `columns` là danh sách width, có thể chứa cả field đang ẩn; không dựa vào thứ tự `columns` để suy thứ tự UI, nhưng với các cột hiển thị giữ thứ tự key trong `columns` nhất quán với `showingColumns`.
- Mỗi key trong `showingColumns` phải có width tương ứng trong `columns`; mọi key là field slug thật hoặc cột đặc biệt được hệ thống hỗ trợ; width là số nguyên dương.
- `actionColumn` đã pin nên không bắt buộc xuất hiện trong `showingColumns`; giữ cách này cho filter mới trừ khi UI/API workspace yêu cầu khác.

Trước khi gọi create, rà lại: câu nghiệp vụ đã suy ra; `showingColumns` theo thứ tự kèm width; cột nhận diện chính không thiếu hoặc quá hẹp; status/owner/amount/deadline có mặt nếu Object có; `created` ở cuối; từng field trong `sortFields` tồn tại, active và đúng `fieldType` (sort theo `name` phải có lý do rõ, không suy từ slug); tổng số cột đọc được trên màn hình phổ biến.

## Kiểm tra sau khi tạo

Sau khi create và view:

1. Parse `data.tableSettings`; so sánh chính xác thứ tự `showingColumns` và width trong `columns` với thiết kế.
2. So sánh `sortFields` đã lưu với thiết kế; xác nhận không phát sinh `name asc` trên field `short_text` ngoài chủ ý.
3. Xác nhận `created` vẫn là field hiển thị cuối cùng với width ngày giờ phù hợp.
4. Server chuẩn hóa hoặc loại bỏ key thì báo khác biệt; không tuyên bố thành công khi cấu hình chưa được lưu đúng.
