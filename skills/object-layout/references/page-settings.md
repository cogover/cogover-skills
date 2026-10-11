# pageSettings

Cấu hình trang của layout, gồm `settingPage` (toàn bộ trang, vùng nền bao quanh nội dung) và `settingContentPage` (vùng chứa Row/Column/Section bên trong trang).

## Cấu trúc

```json
{
  "id": "<uuid>",
  "slug": "page_setting_<timestamp>",
  "fieldType": "page_settings",
  "settingPage": {
    "paddingTop": 0,
    "paddingBottom": 0,
    "paddingLeft": 0,
    "paddingRight": 0,
    "color": "#dcdde9",
    "combinationRatio": 100,
    "css": "",
    "typeColor": "primary",
    "apiUrlSubmit": "",
    "createOtherRecord": false,
    "copyValueType": 0,
    "copyFieldSlugs": []
  },
  "settingContentPage": {
    "paddingTop": 20,
    "paddingBottom": 20,
    "paddingLeft": 20,
    "paddingRight": 20,
    "borderColor": "#dcdde9",
    "isShowBorder": false,
    "color": "#dcdde9",
    "combinationRatio": 100,
    "css": "",
    "typeBorder": "primary",
    "maxWidth": 100,
    "typeColor": "primary",
    "unitMaxWidth": "%"
  },
  "settingBreadcrumbsPageCreate": {
    "isShow": true,
    "isShowTitle": true,
    "typeShowTitle": "default",
    "title": ""
  },
  "settingBreadcrumbsPageViewEdit": {
    "isShow": true,
    "isShowTitle": true,
    "typeShowTitle": "default",
    "title": ""
  },
  "script": "",
  "buttons": {}
}
```

- `script`: JavaScript của layout (`$layout-scripting`); có thể vắng mặt, `null` hoặc `""` khi layout chưa có script. Đọc/ghi theo SKILL.md.
- `buttons`: cụm Object Button trên header/action của layout xem/sửa, danh sách tại `pageSettings.buttons.listButton`; mỗi entry tham chiếu `buttonId`, `slug` và cấu hình hiển thị (`type`, `size`, icon, `customName`). Để `{}` nếu layout không có record-level custom button. Schema và quy trình: [record-button-placement.md](record-button-placement.md).

## settingPage

| Trường | Kiểu | Mô tả |
|---|---|---|
| `paddingTop/Bottom/Left/Right` | Number | Khoảng cách từ mép trang đến phần nội dung (px) |
| `color` | String | Mã HEX của primary color |
| `combinationRatio` | Number | Tỷ lệ pha màu nền (%): `95` = 95% trắng (light) hoặc đen (dark) + 5% primary; `100` = hoàn toàn trắng/đen |
| `typeColor` | String | `"primary"` |
| `css` | String | CSS tùy chỉnh, thường trống |
| `apiUrlSubmit` | String | URL API submit tùy chỉnh, thường trống |
| `createOtherRecord` | Boolean | Tạo bản ghi liên quan ngay sau khi tạo bản ghi chính. Mặc định `false` |
| `copyValueType` | Number | Copy giá trị khi tạo mới từ bản ghi hiện tại: `0` không copy, `1` copy tất cả, `2` chỉ copy field trong `copyFieldSlugs`, `3` copy tất cả trừ `copyFieldSlugs` |
| `copyFieldSlugs` | Array | Slug field đi kèm `copyValueType`; `[]` khi `copyValueType` là `0` hoặc `1` |

## settingContentPage

| Trường | Kiểu | Mô tả |
|---|---|---|
| `paddingTop/Bottom/Left/Right` | Number | Padding phần nội dung (px). Mặc định `20` |
| `maxWidth` | Number | Chiều rộng tối đa phần nội dung, đơn vị theo `unitMaxWidth` |
| `unitMaxWidth` | String | `"px"` hoặc `"%"` (theo chiều rộng trang) |
| `borderColor` | String | Mã HEX viền |
| `isShowBorder` | Boolean | Hiển thị viền bao quanh nội dung |
| `color` | String | Mã HEX |
| `combinationRatio` | Number | Tỷ lệ pha màu nền nội dung (%), thường `100` |
| `typeBorder` | String | `"primary"` |
| `typeColor` | String | `"primary"` |
| `css` | String | CSS tùy chỉnh, thường trống |

## Chọn pageSettings theo loại layout

**Layout Tạo** — mặc định bắt buộc nếu người dùng không yêu cầu khác:

```json
{
  "settingPage": {
    "paddingTop": 0, "paddingBottom": 0, "paddingLeft": 0, "paddingRight": 0,
    "combinationRatio": 100, "color": "#dcdde9", "typeColor": "primary"
  },
  "settingContentPage": {
    "paddingTop": 20, "paddingBottom": 20, "paddingLeft": 20, "paddingRight": 20,
    "maxWidth": 100, "unitMaxWidth": "%",
    "isShowBorder": false, "borderColor": "#dcdde9", "combinationRatio": 100
  }
}
```

Trang không padding ngoài, nền pha 100% trắng/đen theo chế độ giao diện, vùng nội dung chiếm 100% chiều rộng và không border. Độ rộng form thực tế quyết định trên **Layout Row ngoài cùng**, không đổi `settingContentPage` sang `1000px`:

| Layout Tạo | Row ngoài cùng |
|---|---|
| Form thường, không có bảng/component rộng | `"maxWidth": 1000, "unitMaxWidth": "px", "horizontalAlignment": "center"` |
| Có `related_list` `typeView: "list"` hoặc bảng/component rộng | `"maxWidth": 100, "unitMaxWidth": "%", "horizontalAlignment": "center"` |

`assets/sample_layout_create_order.json` chỉ là mẫu field/related list; khi dựng payload phải bổ sung ba thuộc tính Row trên nếu asset chưa có.

**Layout Xem/Sửa** — nội dung full màn hình:

```json
{
  "settingPage": {
    "paddingTop": 0, "paddingBottom": 0, "paddingLeft": 0, "paddingRight": 0,
    "combinationRatio": 100, "color": "#dcdde9", "typeColor": "primary"
  },
  "settingContentPage": {
    "paddingTop": 20, "paddingBottom": 20, "paddingLeft": 20, "paddingRight": 20,
    "maxWidth": 100, "unitMaxWidth": "%",
    "isShowBorder": false, "combinationRatio": 100
  }
}
```
