# Record Triggered Flow — Triggered Flow loại `"record"`

Quy trình khởi chạy khi bản ghi của một Object Type được tạo/cập nhật/xóa. Mẫu: `samples/sample_triggered_flow.json`.

## Các trường metadata

- `type`: BẮT BUỘC `"record"`
- `trigger`: loại sự kiện kích hoạt: `1` tạo mới (create), `2` cập nhật (update), `3` tạo mới hoặc cập nhật, `4` xóa (delete)
- `object`: ID của Object Type được theo dõi, BẮT BUỘC lấy qua `$object-info` (xem [Chuẩn bị](../SKILL.md#chuẩn-bị))
- `name`: `"Start"`
- `runFlowWhenRecordsAreUpdatedStrategy`: `1`
- `triggerConditions`: `1` khi `trigger` = `1` (chỉ tạo mới) hoặc `4` (xóa); `3` khi `trigger` = `2` (cập nhật) hoặc `3` (tạo mới hoặc cập nhật)
- `onObjectFieldUpdateOption`: tuỳ chọn trường kích hoạt, chỉ áp dụng khi `trigger` = `2` hoặc `3`: `1` chạy khi bất kỳ trường nào được cập nhật (mặc định); `2` chỉ chạy khi một trong các trường chỉ định được cập nhật; `3` chạy khi bất kỳ trường nào ngoại trừ các trường chỉ định được cập nhật
- `triggeredUpdateFields`: mảng slug trường đi với `onObjectFieldUpdateOption`; `[]` khi option = `1`, danh sách slug khi option = `2` hoặc `3`
- `applyConditionsForRecords`: `true` (áp dụng điều kiện lọc cho bản ghi)
- `conditions`: mảng điều kiện lọc bản ghi; mỗi phần tử gồm `field` (slug trường), `op` (toán tử), `params` (giá trị so sánh, kiểu phụ thuộc `op` và `fieldType`), `fieldType` (loại trường). Chi tiết `fieldType`, `op`, kiểu `params`: [danh mục điều kiện của object-record](../../object-record/records_filter_conditions.md#dùng-trong-process-process-creator)
- `logicType`: `"AND"` tất cả điều kiện phải thoả (mặc định); `"OR"` chỉ cần một; `"CUSTOM"` logic tuỳ chỉnh theo `logic`
- `logic`: biểu thức khi `logicType` là `"CUSTOM"`, dùng số thứ tự điều kiện (từ 1) kết hợp `AND`, `OR` và ngoặc đơn, ví dụ `"1 AND (2 OR 3)"`; để `""` khi `logicType` là `"AND"` hoặc `"OR"`

## Ví dụ metadata

Kích hoạt khi bản ghi được tạo mới (`trigger: 1`, `triggerConditions: 1`), không điều kiện lọc:

```json
{
  "metadata": {
    "logicType": "AND",
    "triggerConditions": 1,
    "applyConditionsForRecords": true,
    "triggeredUpdateFields": [],
    "trigger": 1,
    "logic": "",
    "runFlowWhenRecordsAreUpdatedStrategy": 1,
    "type": "record",
    "conditions": [],
    "onObjectFieldUpdateOption": 1,
    "object": "OT00000000014",
    "name": "Start"
  }
}
```

Biến thể theo sự kiện (các trường còn lại như ví dụ trên):

| Sự kiện | `trigger` | `triggerConditions` | `onObjectFieldUpdateOption` | `triggeredUpdateFields` |
|---|---|---|---|---|
| Bản ghi được cập nhật | `2` | `3` | `1` | `[]` |
| Bản ghi được tạo mới hoặc cập nhật | `3` | `3` | `1` | `[]` |
| Bản ghi bị xóa | `4` | `1` | `1` | `[]` |
| Chỉ chạy khi cập nhật các trường chỉ định (ví dụ 'Kiểu', 'Nguồn gốc') | `3` | `3` | `2` | `["origin", "type"]` |
| Chạy khi cập nhật bất kỳ trường nào, ngoại trừ các trường chỉ định | `3` | `3` | `3` | `["origin", "type"]` |

Điều kiện lọc với `logicType: "CUSTOM"`: kích hoạt khi Họ tên trống VÀ (Tên họ không chứa 'x' HOẶC trạng thái là một trong: Đang nuôi dưỡng, Không có nhu cầu, Đã xác định). Cùng ba điều kiện với `logicType: "AND"` (tất cả phải thoả) thì `logic: ""`.

```json
{
  "metadata": {
    "logicType": "CUSTOM",
    "applyConditionsForRecords": true,
    "trigger": 1,
    "logic": "1 AND (2 OR 3)",
    "type": "record",
    "conditions": [
      { "field": "last_first_name", "op": "is null", "params": null, "fieldType": "formula" },
      { "field": "first_last_name", "op": "not like", "params": "x", "fieldType": "formula" },
      { "field": "status", "op": "in", "params": ["nurturing", "unqualified", "qualified"], "fieldType": "single_choice" }
    ],
    "object": "OT00000000012",
    "name": "Start"
  }
}
```

## System resources đặc biệt (loại record)

Có thêm `$flow.input` với 2 children, cả hai có `metaDataType` trỏ đến object type được theo dõi:

- `$flow.input.oldRecord` (id `OLD_RECORD_DATA`, parentId `TRIGGERED_INPUT`): bản ghi cũ trước khi thay đổi
- `$flow.input.newRecord` (id `NEW_RECORD_DATA`, parentId `TRIGGERED_INPUT`): bản ghi mới sau khi thay đổi
