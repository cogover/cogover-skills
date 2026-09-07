# Record Triggered Flow — Triggered Flow loại `"record"`

Khi `type` = `"record"`, quy trình sẽ khởi chạy khi bản ghi của một Object Type được tạo/cập nhật/xóa.

## Giải thích các trường metadata

- `type`: **BẮT BUỘC** `"record"`
- `trigger`: loại sự kiện kích hoạt:
  - `1` = tạo mới (create)
  - `2` = cập nhật (update)
  - `3` = tạo mới hoặc cập nhật (create or update)
  - `4` = xóa (delete)
- `object`: ID của Object Type được theo dõi — **BẮT BUỘC** lấy từ skill `/object-info` (xem mục 25 trong Lưu ý quan trọng)
- `name`: `"Start"`
- `runFlowWhenRecordsAreUpdatedStrategy`: `1`
- `triggerConditions`: `1` khi `trigger` = `1` (chỉ tạo mới) hoặc `4` (xóa). `3` khi `trigger` = `2` (cập nhật) hoặc `3` (tạo mới hoặc cập nhật)
- `onObjectFieldUpdateOption`: tuỳ chọn trường kích hoạt, **chỉ áp dụng khi `trigger` = `2` hoặc `3`** (liên quan đến cập nhật):
  - `1`: chạy khi **bất kỳ trường nào** được cập nhật (mặc định)
  - `2`: chỉ chạy khi **một trong các trường chỉ định** được cập nhật
  - `3`: chạy khi **bất kỳ trường nào ngoại trừ các trường chỉ định** được cập nhật
- `triggeredUpdateFields`: mảng slug của các trường liên quan đến `onObjectFieldUpdateOption`. Để `[]` khi `onObjectFieldUpdateOption` = `1`. Chứa danh sách slug trường khi `onObjectFieldUpdateOption` = `2` hoặc `3`
- `applyConditionsForRecords`: `true` — áp dụng điều kiện lọc cho bản ghi
- `conditions`: mảng điều kiện lọc bản ghi. Mỗi phần tử gồm:
  - `field`: slug của trường dữ liệu
  - `op`: toán tử so sánh (xem bảng chi tiết trong file `records_filter_conditions.md`)
  - `params`: giá trị so sánh (kiểu dữ liệu phụ thuộc vào `op` và `fieldType`)
  - `fieldType`: loại trường dữ liệu
- `logicType`: logic kết hợp các điều kiện:
  - `"AND"`: tất cả điều kiện phải thoả mãn (mặc định)
  - `"OR"`: chỉ cần một điều kiện thoả mãn
  - `"CUSTOM"`: logic tuỳ chỉnh, khi đó trường `logic` sẽ chỉ ra biểu thức kết hợp
- `logic`: biểu thức logic tuỳ chỉnh khi `logicType` là `"CUSTOM"`. Sử dụng số thứ tự của điều kiện (bắt đầu từ 1) kết hợp với `AND`, `OR` và ngoặc đơn. Ví dụ: `"1 AND (2 OR 3)"`. Để trống `""` khi `logicType` là `"AND"` hoặc `"OR"`

## Các ví dụ metadata

**Ví dụ 1 — Khi bản ghi được tạo mới** (`trigger: 1`, `triggerConditions: 1`):
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

**Ví dụ 2 — Khi bản ghi được cập nhật** (`trigger: 2`, `triggerConditions: 3`):
```json
{
  "metadata": {
    "logicType": "AND",
    "applyConditionsForRecords": true,
    "trigger": 2,
    "logic": "",
    "type": "record",
    "conditions": [],
    "object": "OT00000000014",
    "name": "Start",
    "triggerConditions": 3,
    "onObjectFieldUpdateOption": 1,
    "triggeredUpdateFields": []
  }
}
```

**Ví dụ 3 — Khi bản ghi được tạo mới hoặc cập nhật** (`trigger: 3`, `triggerConditions: 3`):
```json
{
  "metadata": {
    "logicType": "AND",
    "triggerConditions": 3,
    "applyConditionsForRecords": true,
    "triggeredUpdateFields": [],
    "trigger": 3,
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

**Ví dụ 4 — Khi bản ghi bị xóa** (`trigger: 4`, `triggerConditions: 1`):
```json
{
  "metadata": {
    "logicType": "AND",
    "triggerConditions": 1,
    "applyConditionsForRecords": true,
    "triggeredUpdateFields": [],
    "trigger": 4,
    "logic": "",
    "type": "record",
    "conditions": [],
    "onObjectFieldUpdateOption": 1,
    "object": "OT00000000014",
    "name": "Start"
  }
}
```

**Ví dụ 5 — Chỉ chạy khi cập nhật các trường chỉ định** (`onObjectFieldUpdateOption: 2`, VD: trường 'Kiểu' và 'Nguồn gốc'):
```json
{
  "metadata": {
    "logicType": "AND",
    "triggerConditions": 3,
    "applyConditionsForRecords": true,
    "triggeredUpdateFields": ["origin", "type"],
    "trigger": 3,
    "logic": "",
    "runFlowWhenRecordsAreUpdatedStrategy": 1,
    "type": "record",
    "conditions": [],
    "onObjectFieldUpdateOption": 2,
    "object": "OT00000000014",
    "name": "Start"
  }
}
```

**Ví dụ 6 — Chạy khi cập nhật bất kỳ trường nào, ngoại trừ các trường chỉ định** (`onObjectFieldUpdateOption: 3`, VD: ngoại trừ 'Kiểu' và 'Nguồn gốc'):
```json
{
  "metadata": {
    "logicType": "AND",
    "triggerConditions": 3,
    "applyConditionsForRecords": true,
    "triggeredUpdateFields": ["origin", "type"],
    "trigger": 3,
    "logic": "",
    "runFlowWhenRecordsAreUpdatedStrategy": 1,
    "type": "record",
    "conditions": [],
    "onObjectFieldUpdateOption": 3,
    "object": "OT00000000014",
    "name": "Start"
  }
}
```

**Ví dụ 7 — Điều kiện lọc với logicType AND:** Kích hoạt khi Họ tên trống VÀ Tên họ không chứa 'x' VÀ trạng thái là một trong: Đang nuôi dưỡng, Không có nhu cầu, Đã xác định
```json
{
  "metadata": {
    "type": "record",
    "object": "OT00000000012",
    "trigger": 1,
    "conditions": [
      { "field": "last_first_name", "op": "is null", "params": null, "fieldType": "formula" },
      { "field": "first_last_name", "op": "not like", "params": "x", "fieldType": "formula" },
      { "field": "status", "op": "in", "params": ["nurturing", "unqualified", "qualified"], "fieldType": "single_choice" }
    ],
    "logic": "",
    "logicType": "AND",
    "applyConditionsForRecords": true,
    "name": "Start"
  }
}
```

**Ví dụ 8 — Điều kiện lọc với logicType CUSTOM:** Kích hoạt khi Họ tên trống VÀ (Tên họ không chứa 'x' HOẶC trạng thái là một trong: Đang nuôi dưỡng, Không có nhu cầu, Đã xác định)
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

## Bảng chi tiết các điều kiện lọc theo loại trường

Xem file `records_filter_conditions.md` để biết chi tiết đầy đủ các `fieldType`, `op`, và kiểu `params`.

## System resources đặc biệt (loại record)

Có thêm `$flow.input` với 2 children:
- `$flow.input.oldRecord` (id: `OLD_RECORD_DATA`, parentId: `TRIGGERED_INPUT`) — bản ghi cũ trước khi thay đổi
- `$flow.input.newRecord` (id: `NEW_RECORD_DATA`, parentId: `TRIGGERED_INPUT`) — bản ghi mới sau khi thay đổi
- Cả hai đều có `metaDataType` trỏ đến object type được theo dõi

## File mẫu

`samples/sample_triggered_flow.json`
