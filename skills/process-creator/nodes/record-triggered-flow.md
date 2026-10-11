# Record Triggered Flow — Triggered Flow loại `"record"`

Quy trình khởi chạy khi bản ghi của một Object Type được tạo/cập nhật/xóa. Mẫu: `samples/sample_triggered_flow.json`.

## Các trường metadata

- `type`: BẮT BUỘC `"record"`
- `trigger`: loại sự kiện kích hoạt: `1` tạo mới (create), `2` cập nhật (update), `3` tạo mới hoặc cập nhật, `4` xóa (delete)
- `object`: ID của Object Type được theo dõi, BẮT BUỘC lấy qua `$object-info` (xem [Chuẩn bị](../SKILL.md#chuẩn-bị))
- `name`: `"Start"`
- `runFlowWhenRecordsAreUpdatedStrategy` (áp dụng khi có `conditions`): `1` chỉ chạy lần đầu bản ghi thoả điều kiện; bản ghi từng thoả rồi thoả lại (gửi duyệt lại sau từ chối, huỷ lần hai) không sinh lượt mới. `2` sinh lượt mới ở những lần sau (*đã sửa và chạy đúng* cho kịch bản gửi lại; nghĩa khi bản ghi thoả điều kiện qua nhiều lần cập nhật liên tiếp *cần kiểm chứng*). Luồng duyệt cho phép gửi lại dùng `2` kèm [thiết kế trigger cho luồng duyệt](#thiết-kế-trigger-cho-luồng-duyệt)
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

Hai điều kiện đầu đặt trên field `formula`. Chỉ formula tính khi lưu mới dùng làm điều kiện/lọc được; formula tính khi đọc không khớp khi lọc ([object-info](../../object-info/references/api-object-fields.md#formula-tính-khi-đọc-và-khi-lưu)). Kiểm tra `calculation_mode` bằng `$object-info` trước khi đặt điều kiện trigger trên formula, hoặc dùng field lưu; hành vi riêng của điều kiện trigger trên formula *cần kiểm chứng*.

## System resources đặc biệt (loại record)

Có thêm `$flow.input` với 2 children, cả hai có `metaDataType` trỏ đến object type được theo dõi:

- `$flow.input.oldRecord` (id `OLD_RECORD_DATA`, parentId `TRIGGERED_INPUT`): bản ghi cũ trước khi thay đổi
- `$flow.input.newRecord` (id `NEW_RECORD_DATA`, parentId `TRIGGERED_INPUT`): bản ghi mới sau khi thay đổi

## Dữ liệu bản ghi trong lượt chạy

- `$flow.input.newRecord` và `$flow.input.oldRecord` là ảnh chụp tại thời điểm trigger: không tự làm mới sau Update Record, sau User Task hoặc khi người dùng, backend hay process khác sửa bản ghi trong lúc lượt chờ. Field do backend hoặc rollup tính bất đồng bộ có thể còn trống lúc trigger.
- Trước gateway, trước node ghi phụ thuộc giá trị hiện tại và trước node soạn nội dung: thêm Get Records theo `id` rồi dùng `$action.{slug}.output.record.<field>` (*đã sửa và chạy đúng*):

  ```json
  {"resultType": 1, "logicType": "AND", "logic": "", "conditions": [
    {"field": "id", "op": "=", "fieldType": "short_text", "params": null, "isRaw": false, "name": "",
     "resourceDataType": "TEXT", "resourceSlug": "$flow.input.newRecord.id",
     "resourcePathName": "workflow_resource:list.resource / Input / New Record / ID"}]}
  ```

- Backend hoặc process khác ghi lại field ngay sau khi bản ghi được tạo/cập nhật: thêm [Wait](wait-task.md) ngắn trước Get Records; đo khoảng chờ bằng lượt chạy thật, không đoán.
- Lý do, ý kiến và người duyệt của một bước: đọc từ resource của User Task (`$userTask.{task_slug}.{field}`, `$userTask.{task_slug}.submittedBy`), không từ `newRecord`.

## Chặn khi bản ghi bị huỷ hoặc đổi ngoài luồng

User Task đang chờ không tự huỷ khi bản ghi đổi trạng thái. Sau mỗi User Task duyệt, trước Update Record hoặc gửi thông báo:

1. Get Records bản mới nhất như trên.
2. Exclusive Gateway có outcome "Đã huỷ" xếp trước (`outcomeOrder: 0`), điều kiện `$action.{get_slug}.output.record.status` `IS_ONE_OF` `value` option huỷ (ví dụ `["cancelled"]`), đi thẳng tới End Process: không cập nhật trạng thái, không gửi thông báo.
3. Lượt còn treo ở User Task của bản ghi đã huỷ: huỷ bằng service `5` ([api-process-runtime.md mục 5](../api-process-runtime.md#5-đổi-trạng-thái-và-xoá-lượt-chạy)) sau khi liệt kê ID và hỏi xác nhận.

Kiểm thử: huỷ bản ghi khi đang chờ từng bước duyệt rồi submit "Đồng ý"; PASS khi lượt đi nhánh "Đã huỷ" và trạng thái bản ghi giữ nguyên (*đã sửa và chạy đúng*).

## Thiết kế trigger cho luồng duyệt

- Giới hạn field kích hoạt: `onObjectFieldUpdateOption: 2`, `triggeredUpdateFields` chỉ gồm field trạng thái và field nghiệp vụ cần (ví dụ `["status", "amount"]`). Option `1` chạy ở mọi lần lưu, kể cả lần chính process ghi bản ghi. Cần chạy lại theo yêu cầu thì thêm field "yêu cầu tính lại" (ví dụ `example_recalc_requested_at`) vào `triggeredUpdateFields` (*đã sửa và chạy đúng*).
- Chống kích hoạt lại khi process tự ghi bản ghi (trả về bước trước, khôi phục trạng thái): thêm điều kiện chỉ đúng ở lần gửi thật, ví dụ `example_approval_step` `is null` hoặc `in ["draft", "returned"]`, hoặc field người duyệt `is null`. Kiểm thử kịch bản trả về và đếm lượt chạy trên bản ghi: phải đúng 1.
- Toán tử: ưu tiên `=`, `in`, `is null` trên field lựa chọn, số, trạng thái. `startsWith` trên `short_text` không khớp trong một lần thử (*quan sát, cần kiểm chứng*); cần so tiền tố thì kiểm tra ở gateway sau Start.
- Hai cập nhật cùng bản ghi cách nhau dưới khoảng 3 giây đã chỉ sinh một lượt (*quan sát*). Khi kiểm thử, giãn các lần cập nhật vài giây và tìm lượt theo record ID cùng thời điểm.
