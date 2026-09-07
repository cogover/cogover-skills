# Đặt Object Button lên layout xem/sửa

Tài liệu này mô tả cách làm một record-level Object Button xuất hiện trên màn hình xem/sửa bản ghi. Mẫu đã được ẩn danh từ response của endpoint `POST /bapi/v1/layouts_v2/view`; mọi ID chỉ là dữ liệu minh hoạ.

## Mục lục

1. [Nguyên tắc](#nguyên-tắc)
2. [Vị trí JSON](#vị-trí-json)
3. [Mẫu thực tế](#mẫu-thực-tế)
4. [Schema](#schema)
5. [Quy trình cập nhật](#quy-trình-cập-nhật)
6. [Kiểm tra và lỗi thường gặp](#kiểm-tra-và-lỗi-thường-gặp)

## Nguyên tắc

Tạo Object Button và đặt button lên giao diện là hai thao tác khác nhau:

1. Object Buttons API lưu định nghĩa và hành vi của button.
2. Layouts V2 API quyết định record-level button nào xuất hiện trên từng layout xem/sửa.

Button vừa được tạo sẽ không tự xuất hiện trên mọi màn hình bản ghi. Với button không thuộc loại hiển thị trên màn danh sách, phải thêm một entry tham chiếu button vào layout xem/sửa phù hợp của cùng Object.

Một Object có thể có nhiều layout theo quyền truy cập, chức năng, web/mobile hoặc nhóm người dùng. Việc thêm button vào một layout không làm nó xuất hiện trên các layout còn lại.

## Vị trí JSON

Cụm button trên header/action area của màn hình bản ghi nằm tại:

```text
data.pageSettings.buttons.listButton
```

Trong payload update, bỏ tiền tố `data`:

```text
pageSettings.buttons.listButton
```

Không nhầm vị trí này với component sau:

```text
content[*] ... components[*].fieldType == "button_group"
```

`pageSettings.buttons` là cụm action của trang. `button_group` là component được nhúng trong một group cụ thể của nội dung layout. Chỉ tạo component `button_group` khi người dùng chủ động yêu cầu đặt nhóm nút bên trong bố cục.

## Mẫu thực tế

Layout `LO00000000004` có:

- Tên: `View 2 columns`
- Object: `customer_invoice`
- `functionLayout: 2` — xem/sửa
- Web và mobile đều bật
- Ba button theo thứ tự: Create a replacement invoice, Create receipt voucher, Create Payment voucher

JSON rút gọn được quan sát:

```json
{
  "pageSettings": {
    "buttons": {
      "menuIcon": "ellipsis-vertical",
      "gap": 10,
      "combineAction": false,
      "id": null,
      "slug": null,
      "buttonPosition": "right",
      "listButton": [
        {
          "onlyShowIcon": false,
          "size": "medium",
          "buttonId": "BU00000000003",
          "useIcon": false,
          "icon": null,
          "iconDarkMode": null,
          "customName": null,
          "type": "gray",
          "slug": "create_a_replacement_invoice"
        },
        {
          "onlyShowIcon": false,
          "size": "medium",
          "buttonId": "BU00000000004",
          "useIcon": false,
          "icon": null,
          "iconDarkMode": null,
          "customName": null,
          "type": "gray",
          "slug": "create_receipt_voucher"
        },
        {
          "onlyShowIcon": false,
          "size": "medium",
          "buttonId": "BU00000000001",
          "useIcon": false,
          "icon": null,
          "iconDarkMode": null,
          "customName": null,
          "type": "gray",
          "slug": "create_payment_voucher"
        }
      ],
      "status": 1
    }
  }
}
```

Tên hiển thị có thể được resolve từ định nghĩa Object Button khi `customName` là `null`. Không cần sao chép tên vào entry nếu không có yêu cầu đổi tên riêng trên layout.

## Schema

### `pageSettings.buttons`

| Trường | Ý nghĩa |
|---|---|
| `buttonPosition` | Căn cụm button: `left`, `right` hoặc `center` |
| `combineAction` | `true` để gom thành menu, `false` để hiển thị riêng |
| `menuIcon` | Icon của menu khi gom action; mẫu dùng `ellipsis-vertical` |
| `gap` | Khoảng cách giữa các button; mẫu dùng `10` |
| `listButton` | Danh sách entry có thứ tự |
| `status` | Trạng thái cụm button; mẫu dùng `1` |
| `id`, `slug` | Mẫu header button có thể để `null`; giữ nguyên giá trị hiện tại khi update |

### Entry trong `listButton`

| Trường | Nguồn/ý nghĩa |
|---|---|
| `buttonId` | ID thật của Object Button; dùng để chống trùng |
| `slug` | Slug thật của Object Button |
| `type` | Kiểu hiển thị; mẫu record header dùng `gray` |
| `size` | Kích thước; mẫu dùng `medium` |
| `useIcon` | Lấy từ `useIcon` của Object Button và chuẩn hóa về boolean |
| `onlyShowIcon` | Lấy từ `iconOnly` của Object Button và chuẩn hóa về boolean |
| `icon`, `iconDarkMode` | Lấy từ Object Button hoặc để `null` |
| `customName` | Tên riêng trên layout; `null` để dùng tên button |

Không áp enum `contained`/`outlined`/`text` của component `button_group` cho record header nếu mẫu UI hiện tại dùng `gray`. Khi cần kiểu khác, đọc một layout được UI lưu cùng kiểu mong muốn trước khi ghi.

## Quy trình cập nhật

1. View Object Button và layout ngay trước khi sửa.
2. Xác minh `layout.objectTypeSlug == button.objectTypeSlug`.
3. Xác minh layout hỗ trợ xem/sửa và đúng web/mobile/access control cần áp dụng.
4. Sao chép nguyên `pageSettings.buttons` hiện tại.
5. Tìm entry theo `buttonId`:
   - Có rồi: không append; chỉ cập nhật thuộc tính được yêu cầu.
   - Chưa có: append hoặc chèn vào vị trí được yêu cầu.
6. Nếu `pageSettings.buttons` chưa tồn tại, có thể khởi tạo tối thiểu:

```json
{
  "menuIcon": "ellipsis-vertical",
  "gap": 10,
  "combineAction": false,
  "id": null,
  "slug": null,
  "buttonPosition": "right",
  "listButton": [],
  "status": 1
}
```

7. Dựng payload update bằng allowlist của Layouts V2 và giữ nguyên `content`, `title`, access control cùng mọi key khác trong `pageSettings`.
8. Chỉ thay đổi `pageSettings.buttons`; không gửi raw response vì có trường server-managed.
9. Gọi `PUT /bapi/v1/layouts_v2/{LAYOUT_ID}` rồi view lại.

Ví dụ dùng `jq` để dựng phần `pageSettings` trong bộ nhớ từ response layout mới nhất và một entry đã được xác minh:

```jq
.data.pageSettings
| .buttons = (
    (.buttons // {
      menuIcon: "ellipsis-vertical",
      gap: 10,
      combineAction: false,
      id: null,
      slug: null,
      buttonPosition: "right",
      listButton: [],
      status: 1
    })
    | if any(.listButton[]?; .buttonId == $entry.buttonId)
      then .
      else .listButton += [$entry]
      end
  )
```

Không tạo file tạm chứa API key. Nếu cần tạo payload tạm, chỉ lưu JSON layout không chứa credential và xóa an toàn sau khi dùng.

## Kiểm tra và lỗi thường gặp

- Kiểm tra entry mới xuất hiện đúng một lần theo `buttonId`.
- Kiểm tra mọi entry cũ và thứ tự cũ vẫn còn.
- Kiểm tra `slug`, icon, `type`, `size` và `customName` đã lưu đúng.
- Kiểm tra `content`, `title`, script và các key `pageSettings` khác không đổi.
- Không chọn layout của Object khác dù tên layout giống nhau.
- Không tự thêm vào mọi layout active nếu người dùng chưa xác định phạm vi.
- Không coi update thành công chỉ dựa vào HTTP status hoặc `r: 0`; luôn view lại.
- Không xóa Object Button chỉ để gỡ nó khỏi một layout.
