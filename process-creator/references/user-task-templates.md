# Template User Task: pageSettings, content, nhóm nút

Đọc khi dựng `userTasks[]`. Loại field form, `fieldMetaData` từng loại và ràng buộc `required`/`readOnly`/`canSendData`: [nodes/user-task-form-fields.md](../nodes/user-task-form-fields.md). Dùng Variable làm giá trị mặc định cho component: [variables.md](variables.md). Contract chung của User Task (`approvalScreen: 0`, `taskPerformer`, ba resource chuẩn `submittedBy`/`startAt`/`endAt`): [nodes/normal-flow.md](../nodes/normal-flow.md#user-task-trong-normal-flow) và `samples/sample_process_1.json`.

## Thuộc tính chung của field

| Thuộc tính | Mô tả |
|---|---|
| `required` | `0` không bắt buộc, `1` bắt buộc |
| `multiple` | `0` đơn giá trị, `1` nhiều giá trị |
| `unique` | `true`/`false` |
| `readOnly` | `null` hoặc `true` |
| `disable` | `null` hoặc `true` |
| `canSendData` | `false`/`true`: đưa giá trị field vào payload khi submit form; checkbox **Gửi dữ liệu** |
| `uiSlug` | Định danh UI: `"_1"`, `"_2"`, ... |

Component vừa bắt buộc (`required: 1` hoặc `true`) vừa chỉ đọc (`readOnly: true` hoặc `1`) phải có `canSendData: true` ngay trên component trong `userTasks[].content`. `canSendData` quyết định field có được đưa vào payload submit form gửi tới runtime Process hay không; độc lập với `availableForOutput` của component/resource và không đồng bộ sang resource. Thiếu thì server có thể trả lỗi thiếu dữ liệu bắt buộc.

## Template `pageSettings`

Mọi `userTask` mặc định dùng cấu hình dưới đây: trang không padding, nền màu chính pha 100% trắng; phần nội dung padding 20px, hiện viền, rộng tối đa 1000px.

```json
{
  "settingPage": {
    "typeColor": "primary",
    "css": "",
    "paddingBottom": 0,
    "color": "#dcdde9",
    "paddingRight": 0,
    "paddingTop": 0,
    "combinationRatio": 100,
    "paddingLeft": 0
  },
  "id": "{UUID}",
  "settingContentPage": {
    "typeColor": "primary",
    "borderColor": "#dcdde9",
    "css": "",
    "color": "#dcdde9",
    "paddingRight": 20,
    "unitMaxWidth": "px",
    "combinationRatio": 100,
    "typeBorder": "primary",
    "paddingBottom": 20,
    "paddingTop": 20,
    "isShowBorder": true,
    "paddingLeft": 20,
    "maxWidth": 1000
  },
  "slug": "page_setting_{USER_TASK_SLUG}"
}
```

## Template `content`

Mỗi userTask có mảng `content` theo chuỗi `layoutRow → layoutColumn → section → tab → group → components`. Mỗi node layout (`layoutRow`, `layoutColumn`, `section`, `group`) phải có đầy đủ thuộc tính như mẫu, thiếu sẽ lỗi hiển thị. Mọi `section` của userTask bật viền `"isBorder": true`.

```json
{
  "paddingBottom": 0,
  "numberOfColumns": 1,
  "children": [
    {
      "colSpan": 1,
      "isShowChildren": true,
      "paddingRight": 0,
      "type": "layoutColumn",
      "isBorder": false,
      "isShowName": false,
      "paddingBottom": 0,
      "children": [
        {
          "isShowChildren": true,
          "paddingRight": 20,
          "type": "section",
          "typeSection": "normal",
          "isBorder": true,
          "isShowName": false,
          "paddingBottom": 24,
          "children": [
            {
              "children": [
                {
                  "components": [/* các trường form */],
                  "canCollapse": false,
                  "isShowChildren": true,
                  "paddingRight": 0,
                  "type": "group",
                  "isBorder": false,
                  "isShowName": false,
                  "paddingBottom": 0,
                  "numberOfColumns": 2,
                  "gap": 12,
                  "name": "",
                  "id": "{UUID}",
                  "paddingTop": 0,
                  "tabKey": 1,
                  "paddingLeft": 0,
                  "slug": "group_expand_0_{TIMESTAMP}"
                },
                {
                  "components": [/* nhóm nút */],
                  "canCollapse": false,
                  "isShowChildren": true,
                  "paddingRight": 0,
                  "type": "group",
                  "isBorder": false,
                  "isShowName": false,
                  "paddingBottom": 0,
                  "numberOfColumns": 2,
                  "gap": 12,
                  "name": "",
                  "id": "{UUID}",
                  "paddingTop": 0,
                  "tabKey": 1,
                  "paddingLeft": 0,
                  "slug": "group_expand_1_{TIMESTAMP}"
                }
              ],
              "isShowChildren": true,
              "name": "Tab 1",
              "id": "{UUID}",
              "slug": "tab_{TIMESTAMP}"
            }
          ],
          "gap": 20,
          "name": "",
          "id": "{UUID}",
          "paddingTop": 24,
          "numberOfTabs": 1,
          "paddingLeft": 20,
          "slug": "section_{TIMESTAMP}"
        }
      ],
      "gap": 20,
      "name": "",
      "id": "{UUID}",
      "paddingTop": 0,
      "paddingLeft": 0,
      "slug": "layout_column_{TIMESTAMP}"
    }
  ],
  "isShowChildren": true,
  "paddingRight": 0,
  "gap": 20,
  "id": "{UUID}",
  "paddingTop": 0,
  "type": "layoutRow",
  "paddingLeft": 0,
  "slug": "layout_row_{TIMESTAMP}",
  "isBorder": false
}
```

Checklist thuộc tính bắt buộc theo node type (ngoài `type`, `children`):

| Node type | Thuộc tính bắt buộc |
|---|---|
| `layoutRow` | `paddingBottom`, `numberOfColumns`, `isShowChildren`, `paddingRight`, `gap`, `id`, `paddingTop`, `paddingLeft`, `slug`, `isBorder` |
| `layoutColumn` | `colSpan`, `isShowChildren`, `paddingRight`, `isBorder`, `isShowName`, `paddingBottom`, `gap`, `name`, `id`, `paddingTop`, `paddingLeft`, `slug` |
| `section` | `isShowChildren`, `paddingRight`, `typeSection`, `isBorder`, `isShowName`, `paddingBottom`, `gap`, `name`, `id`, `paddingTop`, `numberOfTabs`, `paddingLeft`, `slug` |
| `group` | `canCollapse`, `isShowChildren`, `paddingRight`, `isBorder`, `isShowName`, `paddingBottom`, `numberOfColumns`, `gap`, `name`, `id`, `paddingTop`, `tabKey`, `paddingLeft`, `slug`, `components` |

## Nhóm nút

Mỗi userTask có các nút tiêu chuẩn với nhãn tiếng Việt, đặt trong group nhóm nút (`group_expand_1_...`):

- Nhóm nút trái: "Hoàn tác" (rollback).
- Nhóm nút phải: "Hủy" (cancel) + "Thực hiện" (accept).

Cấu trúc component nhóm nút (`fieldType: "button_group"`, `buttonPosition` `left`/`right`, `listButton[]` với `buttonCategory` `rollback`/`cancel`/`accept`): lấy nguyên mẫu từ `samples/sample_process_1.json`.

## Người thực hiện (`taskPerformer`)

`taskPerformer[group_index][performer_index]`; mỗi phần tử có `field`, `isRawValue`, `value`, `option`.

| Mục đích | Phần tử |
|---|---|
| Nhân sự cố định | `{"field": "account", "isRawValue": true, "value": ["{PERSONNEL_ID}"], "option": 2}` |
| Nhân sự từ resource (lookup nhân sự của bản ghi trigger) | `{"field": "account", "isRawValue": false, "value": [{"value": "$flow.input.newRecord.{lookup_slug}", "valueDataType": "RECORD", "valuePathName": "workflow_resource:list.resource / Input / New Record / {Field Name}"}], "option": 2}` |
| Output của Organization | Như dòng trên với `value` `$action.{org_slug}.output.records`, `valuePathName` `workflow_resource:list.organization / {Org Name} / Output / Records` |

- `option` (*quan sát, cần kiểm chứng*): `2` chỉ định nhân sự trong `value`, `1` tất cả. Có thể tương ứng bảng `criteria` của [Organization](../nodes/organization-task.md#criteria--điều-kiện-lọc) (`1` ALL, `2` INCLUDING, `3` EXCLUDING): mẫu `option: 3` với `value: []` khi đó là mọi người, không dùng thay cho chỉ định người duyệt.
- Không trộn performer từ resource và performer ID cố định trong cùng group: người được chỉ định bị từ chối khi submit (`r: 8`). Tách mỗi loại một group: `[[{performer từ resource}], [{performer cố định}]]` (*đã sửa và chạy đúng*).
- Performer dự phòng (ví dụ admin để hoàn thành kiểm thử khi persona chưa kích hoạt) đặt ở group riêng, ghi vào báo cáo là cấu hình tạm và bỏ bằng version mới trước khi bàn giao. Người không phải performer, kể cả admin, không đọc được form task của Triggered Flow trong lần thử (*quan sát*).
- Xác minh đúng người: service `36` (`runningUserTasks[].canPerformThisTask`) và submit bằng phiên của chính người thực hiện; persona chưa chấp nhận lời mời chưa đăng nhập được (xem `$user-permission`).
