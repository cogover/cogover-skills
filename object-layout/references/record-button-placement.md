# Đặt Object Button lên layout xem/sửa

Cách làm một record-level Object Button xuất hiện trên màn hình xem/sửa bản ghi. Mẫu đã ẩn danh từ response `POST /bapi/v1/layouts_v2/view`; mọi ID chỉ minh hoạ. Quy trình tổng thể và điều kiện chọn layout: mục "Đặt Object Button lên layout xem/sửa" trong [SKILL.md](../SKILL.md).

## Nguyên tắc

- Object Buttons API lưu định nghĩa và hành vi của button; Layouts V2 quyết định record-level button nào xuất hiện trên từng layout xem/sửa.
- Button vừa tạo không tự xuất hiện trên màn hình bản ghi. Với button không thuộc loại màn danh sách, phải thêm entry tham chiếu vào layout xem/sửa phù hợp của cùng Object.
- Một Object có nhiều layout theo quyền truy cập, chức năng, web/mobile hoặc nhóm người dùng; thêm button vào một layout không làm nó xuất hiện trên layout khác.

## Vị trí JSON

Response view: `data.pageSettings.buttons.listButton`; payload update bỏ tiền tố `data`: `pageSettings.buttons.listButton`.

Không nhầm với component `content[*] ... components[*].fieldType == "button_group"`: `pageSettings.buttons` là cụm action của trang; `button_group` là component nhúng trong một group của nội dung layout, chỉ tạo khi người dùng chủ động yêu cầu đặt nhóm nút bên trong bố cục.

## Mẫu thực tế

Layout `LO00000000004` "View 2 columns", Object `customer_invoice`, `functionLayout: 2`, bật cả web và mobile, ba button theo thứ tự Create a replacement invoice, Create receipt voucher, Create Payment voucher:

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

Khi `customName` là `null`, tên hiển thị resolve từ định nghĩa Object Button; không sao chép tên vào entry nếu không có yêu cầu đổi tên riêng trên layout.

## Schema

`pageSettings.buttons`:

| Trường | Ý nghĩa |
|---|---|
| `buttonPosition` | `left`, `right` hoặc `center` |
| `combineAction` | `true` gom thành menu, `false` hiển thị riêng |
| `menuIcon` | Icon menu khi gom; mẫu dùng `ellipsis-vertical` |
| `gap` | Khoảng cách giữa các button; mẫu dùng `10` |
| `listButton` | Danh sách entry có thứ tự |
| `status` | Trạng thái cụm button; mẫu dùng `1` |
| `id`, `slug` | Mẫu để `null`; giữ nguyên giá trị hiện tại khi update |

Entry trong `listButton`:

| Trường | Nguồn/ý nghĩa |
|---|---|
| `buttonId` | ID thật của Object Button; khoá chống trùng |
| `slug` | Slug thật của Object Button |
| `type` | Kiểu hiển thị; mẫu record header dùng `gray` |
| `size` | Mẫu dùng `medium` |
| `useIcon` | Từ `useIcon` của Object Button, chuẩn hoá boolean |
| `onlyShowIcon` | Từ `iconOnly` của Object Button, chuẩn hoá boolean |
| `icon`, `iconDarkMode` | Từ Object Button hoặc `null` |
| `customName` | Tên riêng trên layout; `null` để dùng tên button |

Không áp enum `contained`/`outlined`/`text` của component `button_group` cho record header khi mẫu UI hiện tại dùng `gray`. Cần kiểu khác: đọc một layout được UI lưu cùng kiểu mong muốn trước khi ghi.

Khởi tạo tối thiểu khi `pageSettings.buttons` chưa tồn tại:

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

## Quy trình cập nhật

1. View Object Button và layout ngay trước khi sửa; xác minh `layout.objectTypeSlug == button.objectTypeSlug`, layout hỗ trợ xem/sửa và đúng web/mobile/access control cần áp dụng.
2. Sao chép nguyên `pageSettings.buttons` hiện tại (hoặc khởi tạo tối thiểu). Tìm entry theo `buttonId`: có rồi thì không append, chỉ cập nhật thuộc tính được yêu cầu; chưa có thì append hoặc chèn vào vị trí được yêu cầu.
3. Dựng payload theo allowlist Layouts V2, chỉ thay `pageSettings.buttons`; giữ nguyên `content`, `title`, access control và mọi key khác trong `pageSettings`; không gửi raw response.
4. `PUT /bapi/v1/layouts_v2/{LAYOUT_ID}` rồi view lại.

Dựng phần `pageSettings` bằng `jq` từ response layout mới nhất và một entry `$entry` đã xác minh:

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

Không tạo file tạm chứa API key; payload tạm chỉ chứa JSON layout không có credential và xoá an toàn sau khi dùng.

## Kiểm tra và lỗi thường gặp

- Entry mới xuất hiện đúng một lần theo `buttonId`; mọi entry cũ và thứ tự cũ vẫn còn.
- `slug`, icon, `type`, `size`, `customName` đã lưu đúng; `content`, `title`, script và các key `pageSettings` khác không đổi.
- Không chọn layout của Object khác dù tên layout giống nhau.
- Không tự thêm vào mọi layout active khi người dùng chưa xác định phạm vi.
- Không coi update thành công chỉ dựa vào HTTP status hoặc `r: 0`; luôn view lại.
- Không xoá Object Button chỉ để gỡ nó khỏi một layout.
