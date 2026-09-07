## Get Records Task (Task Lấy Bản Ghi)

### Mô tả
Get Records Task là một task hệ thống tự động lấy bản ghi từ một đối tượng (object type) trong hệ thống khi luồng chạy đến. Có thể cấu hình điều kiện lọc, sắp xếp và loại kết quả trả về (đơn hoặc nhiều bản ghi).

### Cấu trúc trong BPMN XML
```xml
<elEx:getRecordTask id="{GET_RECORD_NODE_ID}" name="{TASK_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="GET_RECORD_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:getRecordTask>
```

**Lưu ý quan trọng:**
- Sử dụng `elEx:getRecordTask` (KHÔNG phải `bpmn2:userTask` hay `bpmn2:sendTask`)
- Cần thêm namespace: `xmlns:elEx="http://element-ex/schema"` vào `bpmn2:definitions`
- `renderKey="GET_RECORD_TASK"`

### Cấu trúc `actions` trong JSON
Thêm vào mảng `actions` ở root level:
```json
{
  "actions": [
    {
      "id": "{ACTION_ID}",
      "nodeId": "{GET_RECORD_NODE_ID}",
      "type": "GET_RECORD",
      "name": "{TASK_NAME}",
      "slug": "{task_slug}",
      "description": "",
      "data": {
        "objectTypeId": "{OBJECT_TYPE_ID}",
        "objectTypeSlug": "{object_type_slug}",
        "logic": "",
        "logicType": "NONE",
        "conditions": [],
        "sortFields": [],
        "resultType": 1,
        "outputVariable": ""
      }
    }
  ]
}
```

### Chi tiết các trường cấu hình Get Record

#### 1. Object Type (Đối tượng)
```json
{
  "objectTypeId": "OT00000000011",
  "objectTypeSlug": "lead"
}
```
- `objectTypeId` = ID của loại đối tượng cần lấy bản ghi. **BẮT BUỘC** sử dụng skill `/object-info` để lấy chính xác (xem mục 25 trong Lưu ý quan trọng). Ví dụ trên (`OT00000000011`) chỉ là minh họa.
- `objectTypeSlug` = slug của loại đối tượng — cũng cần lấy từ skill `/object-info`.

#### 2. Logic Type (Kiểu logic lọc)
```json
{
  "logicType": "AND",
  "logic": ""
}
```
- `"NONE"` = không có điều kiện lọc (lấy tất cả)
- `"AND"` = tất cả điều kiện phải thỏa mãn
- `"OR"` = ít nhất một điều kiện thỏa mãn
- `"CUSTOM"` = logic tùy chỉnh, khi đó `logic` sẽ chỉ ra biểu thức, ví dụ: `"1 AND (2 OR 3)"` (số thứ tự tương ứng vị trí trong mảng `conditions`, bắt đầu từ 1)
- Khi có `conditions`, `logicType` phải là `"AND"`, `"OR"` hoặc `"CUSTOM"`

#### 3. Conditions (Điều kiện lọc)

Có thể lọc danh sách bản ghi trả về bằng cách truyền các điều kiện lọc vào mảng `conditions`.

Có **2 loại** điều kiện tùy theo nguồn giá trị so sánh:

##### 3a. Điều kiện với giá trị tĩnh (static) — `isRaw: true`

Dùng khi so sánh với giá trị cố định (số, chuỗi, null, mảng).

```json
{
    "field": "<slug_của_trường>",
    "op": "<toán_tử>",
    "params": "<giá_trị_tĩnh>",
    "fieldType": "<loại_trường>",
    "isRaw": true
}
```

- `params`: Giá trị trực tiếp. Ví dụ: `123`, `"hello"`, `null` (cho `is null`/`not null`), `["a","b"]`.
- `isRaw`: **`true`** — engine dùng `params` trực tiếp làm giá trị so sánh.

**Ví dụ:**
```json
{
    "field": "status",
    "op": "=",
    "params": "active",
    "fieldType": "single_choice",
    "isRaw": true
}
```

##### 3b. Điều kiện với biến workflow (variable reference) — `isRaw: false`

Dùng khi so sánh với giá trị từ biến workflow (`$loop.*`, `$action.*`, `$flow.input.*`, `$userTask.*`, v.v.).

```json
{
    "field": "<slug_của_trường>",
    "op": "<toán_tử>",
    "params": null,
    "fieldType": "<loại_trường>",
    "isRaw": false,
    "name": "",
    "resourceDataType": "<DATA_TYPE>",
    "resourceSlug": "<absolute_slug_của_biến>",
    "resourcePathName": "<đường_dẫn_hiển_thị_của_biến>"
}
```

- `params`: **BẮT BUỘC `null`** — engine KHÔNG đọc giá trị từ `params` mà đọc từ `resourceSlug`.
- `isRaw`: **BẮT BUỘC `false`** — engine sẽ resolve biến động từ `resourceSlug`.
- `resourceSlug`: Đường dẫn tuyệt đối đến biến (ví dụ: `$loop.loop_records.currentItem.source_id`).
- `resourcePathName`: Tên hiển thị đường dẫn biến.
- `resourceDataType`: Kiểu dữ liệu của biến (`NUMBER`, `TEXT`, `DATE`, `RECORD`, ...).
- `name`: Chuỗi rỗng `""`.

**⚠️ LƯU Ý QUAN TRỌNG:**
- **KHÔNG BAO GIỜ** đặt đường dẫn biến vào `params` (ví dụ: `"params": "$loop...currentItem.source_id"` là **SAI**).
- **KHÔNG BAO GIỜ** dùng `isRaw: true` khi dùng biến workflow — sẽ gây lỗi `NullPointerException: Cannot invoke "org.json.JSONArray.length()"`.
- **KHÔNG BAO GIỜ** dùng object dạng `{"type": 4, "value": "..."}` — đó là format của `recordData` trong Create/Update Record, **KHÔNG** áp dụng cho conditions.

**Bảng format `resourceSlug` và `resourcePathName` theo nguồn biến:**

| Nguồn biến | `resourceSlug` | `resourcePathName` |
|---|---|---|
| Loop currentItem | `$loop.<loop_slug>.currentItem.<field>` | `workflow_resource:list.loop / <Loop Name> / Current Item / <field>` |
| Action output | `$action.<action_slug>.output.<field>` | `workflow_resource:list.action / <Action Name> / Output / <field>` |
| Triggered record | `$flow.input.newRecord.<field>` | `workflow_resource:list.resource / Input / newRecord / <field>` |
| User Task field | `$userTask.<task_slug>.<field>` | `workflow_resource:list.userTask / <Task Name> / <field>` |
| Variable | `$flow.<variable_slug>` | `workflow_resource:list.variable / <Variable Name>` |

**Ví dụ: điều kiện với biến loop (trong webhook + loop):**
```json
{
    "field": "source_id",
    "op": "=",
    "params": null,
    "fieldType": "numeric",
    "isRaw": false,
    "name": "",
    "resourceDataType": "NUMBER",
    "resourceSlug": "$loop.loop_records.currentItem.source_id",
    "resourcePathName": "workflow_resource:list.loop / Lặp records / Current Item / source_id"
}
```

**Ví dụ: điều kiện với biến triggered flow (record):**
```json
{
    "field": "source_id",
    "op": "=",
    "params": null,
    "fieldType": "numeric",
    "isRaw": false,
    "name": "",
    "resourceDataType": "NUMBER",
    "resourceSlug": "$flow.input.newRecord.source_id",
    "resourcePathName": "workflow_resource:list.resource / Input / newRecord / source_id"
}
```

**Ví dụ: điều kiện với giá trị tĩnh:**
```json
{
    "field": "status",
    "op": "=",
    "params": "active",
    "fieldType": "single_choice",
    "isRaw": true
}
```

**Bảng chi tiết các điều kiện lọc theo loại trường:**

| Trường dữ liệu `fieldType` | Điều kiện | Giá trị `op` | Kiểu dữ liệu truyền vào `params` |
| --- | --- | --- | --- |
| Văn bản ngắn (`short_text`) | Bằng | `=` | String |
|  | Không bằng | `!=` | String |
|  | Chứa | `like` | String |
|  | Không chứa | `not like` | String |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Bắt đầu với | `startsWith` | String |
|  | Kết thúc với | `endsWith` | String |
|  | Bằng một trong | `in` | Array (String) |
|  | Không bằng bất kỳ | `not in` | Array (String) |
| Văn bản dài (`long_text`) | Chứa (gần đúng) | `contains any` | String |
|  | Không chứa (gần đúng) | `not contains any` | String |
|  | Chứa chính xác | `like` | String |
|  | Không chứa chính xác | `not like` | String |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Số điện thoại (`phone`) | Bằng | `=` | String |
|  | Không bằng | `!=` | String |
|  | Chứa | `like` | String |
|  | Không chứa | `not like` | String |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Bắt đầu với | `startsWith` | String |
|  | Kết thúc với | `endsWith` | String |
|  | Bằng một trong | `in` | Array (String) |
|  | Không bằng bất kỳ | `not in` | Array (String) |
| Boolean (`boolean`) | Bằng | `=` | `1`: true, `0`: false |
|  | Không bằng | `!=` | `1`: true, `0`: false |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Email (`email`) | Bằng | `=` | String |
|  | Không bằng | `!=` | String |
|  | Chứa | `like` | String |
|  | Không chứa | `not like` | String |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Bắt đầu với | `startsWith` | String |
|  | Kết thúc với | `endsWith` | String |
|  | Bằng một trong | `in` | Array (String) |
|  | Không bằng bất kỳ | `not in` | Array (String) |
| Lựa chọn đơn (`single_choice`) | Bằng | `=` | String |
|  | Không bằng | `!=` | String |
|  | Là một trong | `in` | Array (String) |
|  | Không thuộc | `not in` | Array (String) |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Lựa chọn nhiều (`multi_choices`) | Chứa một trong | `in` | Array (String) |
|  | Không chứa bất kỳ | `not in` | Array (String) |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Cây thư mục (`cascading`) | Bằng | `=` | Array (String) |
|  | Không bằng | `!=` | Array (String) |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Ngày (`date`) | Bằng | `=` | String, định dạng `"YYYY-MM-DD"` |
|  | Không bằng | `!=` | String, định dạng `"YYYY-MM-DD"` |
|  | Nhỏ hơn | `<` | String, định dạng `"YYYY-MM-DD"` |
|  | Nhỏ hơn hoặc bằng | `<=` | String, định dạng `"YYYY-MM-DD"` |
|  | Lớn hơn | `>` | String, định dạng `"YYYY-MM-DD"` |
|  | Lớn hơn hoặc bằng | `>=` | String, định dạng `"YYYY-MM-DD"` |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Thuộc khoảng | `between` | Array (String), ví dụ: `["2025-10-14", "2025-10-17"]` |
|  | Hôm qua | `Yesterday` | null |
|  | Hôm nay | `Today` | null |
|  | Ngày mai | `Tomorrow` | null |
|  | Trong n ngày vừa qua | `Last n days` | Int |
|  | Trong n ngày tới | `Next n days` | Int |
|  | n Ngày trước | `n Days ago` | Int |
|  | n Ngày nữa | `n Days from now` | Int |
|  | Tuần trước | `Last week` | null |
|  | Tuần này | `This week` | null |
|  | Tuần sau | `Next week` | null |
|  | Trong n tuần vừa qua | `Last n weeks` | Int |
|  | Trong n tuần tới | `Next n weeks` | Int |
|  | Tháng trước | `Last month` | null |
|  | Tháng này | `This month` | null |
|  | Tháng sau | `Next month` | null |
|  | Trong n tháng vừa qua | `Last n months` | Int |
|  | Trong n tháng tới | `Next n months` | Int |
|  | Quý trước | `Last quarter` | null |
|  | Quý này | `This quarter` | null |
|  | Quý sau | `Next quarter` | null |
|  | Năm ngoái | `Last year` | null |
|  | Năm nay | `This year` | null |
|  | Năm sau | `Next year` | null |
|  | Trong n năm vừa qua | `Last n years` | Int |
|  | Trong n năm tới | `Next n years` | Int |
| Ngày giờ (`date_time`) | Bằng | `=` | Timestamp (milisecond) |
|  | Không bằng | `!=` | Timestamp (milisecond) |
|  | Nhỏ hơn | `<` | Timestamp (milisecond) |
|  | Nhỏ hơn hoặc bằng | `<=` | Timestamp (milisecond) |
|  | Lớn hơn | `>` | Timestamp (milisecond) |
|  | Lớn hơn hoặc bằng | `>=` | Timestamp (milisecond) |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Thuộc khoảng | `between` | Array Timestamp (milisecond), ví dụ: `[1760382900000, 1760725800000]` |
|  | Hôm qua | `Yesterday` | null |
|  | Hôm nay | `Today` | null |
|  | Ngày mai | `Tomorrow` | null |
|  | Trong n ngày vừa qua | `Last n days` | Int |
|  | Trong n ngày tới | `Next n days` | Int |
|  | n Ngày trước | `n Days ago` | Int |
|  | n Ngày nữa | `n Days from now` | Int |
|  | Tuần trước | `Last week` | null |
|  | Tuần này | `This week` | null |
|  | Tuần sau | `Next week` | null |
|  | Trong n tuần vừa qua | `Last n weeks` | Int |
|  | Trong n tuần tới | `Next n weeks` | Int |
|  | Tháng trước | `Last month` | null |
|  | Tháng này | `This month` | null |
|  | Tháng sau | `Next month` | null |
|  | Trong n tháng vừa qua | `Last n months` | Int |
|  | Trong n tháng tới | `Next n months` | Int |
|  | Quý trước | `Last quarter` | null |
|  | Quý này | `This quarter` | null |
|  | Quý sau | `Next quarter` | null |
|  | Năm ngoái | `Last year` | null |
|  | Năm nay | `This year` | null |
|  | Năm sau | `Next year` | null |
|  | Trong n năm vừa qua | `Last n years` | Int |
|  | Trong n năm tới | `Next n years` | Int |
| Thời giờ (`time`) | Bằng | `=` | Timestamp (milisecond, `0` - `86340000`) |
|  | Không bằng | `!=` | Timestamp (milisecond, `0` - `86340000`) |
|  | Nhỏ hơn | `<` | Timestamp (milisecond, `0` - `86340000`) |
|  | Nhỏ hơn hoặc bằng | `<=` | Timestamp (milisecond, `0` - `86340000`) |
|  | Lớn hơn | `>` | Timestamp (milisecond, `0` - `86340000`) |
|  | Lớn hơn hoặc bằng | `>=` | Timestamp (milisecond, `0` - `86340000`) |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Thuộc khoảng | `between` | Array Timestamp (milisecond, `0` - `86340000`), ví dụ: `[0, 1800000]` |
| Thời lượng (`time_duration`) | Bằng | `=` | Timestamp (milisecond) |
|  | Không bằng | `!=` | Timestamp (milisecond) |
|  | Nhỏ hơn | `<` | Timestamp (milisecond) |
|  | Nhỏ hơn hoặc bằng | `<=` | Timestamp (milisecond) |
|  | Lớn hơn | `>` | Timestamp (milisecond) |
|  | Lớn hơn hoặc bằng | `>=` | Timestamp (milisecond) |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Thuộc khoảng | `between` | Array Timestamp (milisecond), ví dụ: `[28800000, 19353600000]` |
| Khoảng ngày (`date_range`) | Chứa | `=` | String, định dạng `"YYYY-MM-DD"` |
|  | Nằm hoàn toàn trong | `rangeWithin` | Array (String), ví dụ: `["2025-10-14", "2025-10-17"]` |
|  | Chứa hoàn toàn | `rangeContains` | Array (String), ví dụ: `["2025-10-14", "2025-10-17"]` |
|  | Có phần giao nhau | `between` | Array (String), ví dụ: `["2025-10-14", "2025-10-17"]` |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Khoảng ngày giờ (`date_time_range`) | Chứa | `=` | Timestamp (milisecond) |
|  | Nằm hoàn toàn trong | `rangeWithin` | Array Timestamp (milisecond), ví dụ: `[1760382900000, 1760725800000]` |
|  | Chứa hoàn toàn | `rangeContains` | Array Timestamp (milisecond), ví dụ: `[1760382900000, 1760725800000]` |
|  | Có phần giao nhau | `between` | Array Timestamp (milisecond), ví dụ: `[1760382900000, 1760725800000]` |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Khoảng giờ (`time_range`) | Chứa | `=` | Timestamp (milisecond, `0` - `86340000`) |
|  | Nằm hoàn toàn trong | `rangeWithin` | Array Timestamp (milisecond, `0` - `86340000`), ví dụ: `[0, 1800000]` |
|  | Chứa hoàn toàn | `rangeContains` | Array Timestamp (milisecond, `0` - `86340000`), ví dụ: `[0, 1800000]` |
|  | Có phần giao nhau | `between` | Array Timestamp (milisecond, `0` - `86340000`), ví dụ: `[0, 1800000]` |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Đường dẫn URL (`url`) | Bằng | `=` | String |
|  | Không bằng | `!=` | String |
|  | Chứa | `like` | String |
|  | Không chứa | `not like` | String |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Bắt đầu với | `startsWith` | String |
|  | Kết thúc với | `endsWith` | String |
|  | Bằng một trong | `in` | Array (String) |
|  | Không bằng bất kỳ | `not in` | Array (String) |
| Số nguyên (`numeric`) | Bằng | `=` | Int |
|  | Không bằng | `!=` | Int |
|  | Nhỏ hơn | `<` | Int |
|  | Nhỏ hơn hoặc bằng | `<=` | Int |
|  | Lớn hơn | `>` | Int |
|  | Lớn hơn hoặc bằng | `>=` | Int |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Thuộc khoảng | `between` | Array (Int) |
| Số thập phân (`decimal`) | Bằng | `=` | Dec |
|  | Không bằng | `!=` | Dec |
|  | Nhỏ hơn | `<` | Dec |
|  | Nhỏ hơn hoặc bằng | `<=` | Dec |
|  | Lớn hơn | `>` | Dec |
|  | Lớn hơn hoặc bằng | `>=` | Dec |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Thuộc khoảng | `between` | Array (Dec) |
| Nhãn (`label`) | Bằng một trong | `in` | Array (String) |
|  | Không bằng bất kỳ | `not in` | Array (String) |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Phần trăm (`percent`) | Bằng | `=` | Dec (`0` = 0%, `1` = 100%) |
|  | Không bằng | `!=` | Dec (`0` = 0%, `1` = 100%) |
|  | Nhỏ hơn | `<` | Dec (`0` = 0%, `1` = 100%) |
|  | Nhỏ hơn hoặc bằng | `<=` | Dec (`0` = 0%, `1` = 100%) |
|  | Lớn hơn | `>` | Dec (`0` = 0%, `1` = 100%) |
|  | Lớn hơn hoặc bằng | `>=` | Dec (`0` = 0%, `1` = 100%) |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Thuộc khoảng | `between` | Array (Dec) (`0` = 0%, `1` = 100%) |
| Tệp tin (`file`) | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Xếp hạng (`rating`) | Bằng | `=` | Int |
|  | Không bằng | `!=` | Int |
|  | Nhỏ hơn | `<` | Int |
|  | Nhỏ hơn hoặc bằng | `<=` | Int |
|  | Lớn hơn | `>` | Int |
|  | Lớn hơn hoặc bằng | `>=` | Int |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Thuộc khoảng | `between` | Array (Int) |
| Tra cứu (`reference`) | Bằng | `=` | Record ID hoặc `"$currentUser"` |
|  | Không bằng | `!=` | Record ID hoặc `"$currentUser"` |
|  | Bằng một trong | `in` | Array (Record ID) |
|  | Không bằng bất kỳ | `not in` | Array (Record ID) |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
| Đánh số tự động (`auto_number`) | Bằng | `=` | String |
|  | Không bằng | `!=` | String |
|  | Chứa | `like` | String |
|  | Không chứa | `not like` | String |
|  | Trống | `is null` | null |
|  | Không trống | `not null` | null |
|  | Bắt đầu với | `startsWith` | String |
|  | Kết thúc với | `endsWith` | String |
|  | Bằng một trong | `in` | Array (String) |
|  | Không bằng bất kỳ | `not in` | Array (String) |
| Công thức (`formula`) | Tương tự các loại trên, tùy vào kiểu dữ liệu trả về của công thức |

**Lưu ý:** Trường kiểu `formula` sử dụng các `op` tương ứng với kiểu dữ liệu mà công thức trả về (text, number, date...).

**Ví dụ 1:** Lọc AND - lấy bản ghi có `last_first_name` không trống VÀ `first_last_name` không chứa 'x':
```json
{
    "logicType": "AND",
    "logic": "",
    "conditions": [
        {
            "field": "last_first_name",
            "op": "not null",
            "params": null,
            "fieldType": "formula",
            "isRaw": true
        },
        {
            "field": "first_last_name",
            "op": "not like",
            "params": "x",
            "fieldType": "formula",
            "isRaw": true
        }
    ]
}
```

**Ví dụ 2:** Lọc OR - lấy bản ghi có `last_first_name` không trống HOẶC `first_last_name` không chứa 'x' HOẶC `status` là một trong "working", "nurturing":
```json
{
    "logicType": "OR",
    "logic": "",
    "conditions": [
        {
            "field": "last_first_name",
            "op": "not null",
            "params": null,
            "fieldType": "formula",
            "isRaw": true
        },
        {
            "field": "first_last_name",
            "op": "not like",
            "params": "x",
            "fieldType": "formula",
            "isRaw": true
        },
        {
            "field": "status",
            "op": "in",
            "params": ["working", "nurturing"],
            "fieldType": "single_choice",
            "isRaw": true
        }
    ]
}
```

**Ví dụ 3:** Lọc CUSTOM - lấy bản ghi thỏa: điều kiện 1 VÀ (điều kiện 2 HOẶC điều kiện 3):
```json
{
    "logicType": "CUSTOM",
    "logic": "1 AND (2 OR 3)",
    "conditions": [
        {
            "field": "last_first_name",
            "op": "not null",
            "params": null,
            "fieldType": "formula",
            "isRaw": true
        },
        {
            "field": "first_last_name",
            "op": "not like",
            "params": "x",
            "fieldType": "formula",
            "isRaw": true
        },
        {
            "field": "status",
            "op": "in",
            "params": ["working", "nurturing"],
            "fieldType": "single_choice",
            "isRaw": true
        }
    ]
}
```

#### 4. Sort Fields (Sắp xếp)
```json
{
  "sortFields": [
    {"field": "id", "order": "asc"},
    {"field": "created", "order": "desc"}
  ]
}
```
- Mỗi phần tử bắt buộc có `field` là field slug thật và `order` là `asc` hoặc `desc`.
- Runtime chuyển `{field, order}` thành object-server sort `{<field>:{order:<order>}}`; không gửi `direction` và không gửi dạng object lồng sẵn.
- Thứ tự phần tử trong mảng là độ ưu tiên sắp xếp. Dùng field ổn định/duy nhất (thường `id`) làm sort cuối để Loop có thứ tự tái lập được.
- Nếu không cần sort, gửi `[]`.

#### 5. Result Type (Loại kết quả)
```json
{
  "resultType": 2,
  "limitRecord": 0
}
```
- `1` = UI intent lấy bản ghi đầu tiên; downstream dùng `output.record`.
- `2` = UI intent lấy tất cả bản ghi; downstream/Loop dùng `output.records`.
- Runtime hiện vẫn tạo cả `record` (phần tử đầu) và `records` (list) trong output cho cả hai mode. Không dựa vào hành vi này để dùng `resultType: 1` cho Loop; cấu hình `2` để request thể hiện đúng nghiệp vụ.
- `limitRecord: 0` dùng giới hạn mặc định của runtime; đặt số dương khi cần giới hạn rõ ràng.

#### 6. Output Variable
```json
{
  "outputVariable": ""
}
```
- Tên biến đầu ra (để trống để dùng mặc định)

### Resources của Get Records Action

Get Records action tạo ra các resources có thể sử dụng trong các bước khác:

```json
{
  "resources": {
    "actions": [
      {
        "id": "{ACTION_ID}",
        "type": "GET_RECORD",
        "name": "{TASK_NAME}",
        "slug": "{task_slug}",
        "nodeId": "{GET_RECORD_NODE_ID}",
        "resources": [
          {
            "absoluteSlug": "$action.{task_slug}.startAt",
            "dataType": "DATE_TIME",
            "name": "Start At",
            "slug": "startAt"
          },
          {
            "absoluteSlug": "$action.{task_slug}.endAt",
            "dataType": "DATE_TIME",
            "name": "End At",
            "slug": "endAt"
          },
          {
            "absoluteSlug": "$action.{task_slug}.output",
            "dataType": "RECORD",
            "name": "Output",
            "slug": "output",
            "children": [
              {
                "absoluteSlug": "$action.{task_slug}.output.record",
                "dataType": "RECORD",
                "name": "Record",
                "slug": "record",
                "metaDataType": {
                  "linkField": "id",
                  "objectSlug": "{object_type_slug}",
                  "object": "{OBJECT_TYPE_ID}"
                }
              },
              {
                "absoluteSlug": "$action.{task_slug}.output.result",
                "dataType": "NUMBER",
                "name": "Result",
                "slug": "result"
              },
              {
                "absoluteSlug": "$action.{task_slug}.output.records",
                "dataType": "RECORD",
                "isList": true,
                "name": "Records",
                "slug": "records",
                "metaDataType": {
                  "linkField": "id",
                  "objectSlug": "{object_type_slug}",
                  "object": "{OBJECT_TYPE_ID}"
                }
              },
              {
                "absoluteSlug": "$action.{task_slug}.output.total",
                "dataType": "NUMBER",
                "name": "Total",
                "slug": "total"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**Chi tiết Output:**
- `output.record` = bản ghi đơn (RECORD), liên kết đến object type đã cấu hình
- `output.result` = mã kết quả (NUMBER)
- `output.records` = danh sách bản ghi (RECORD[], `isList: true`), liên kết đến object type đã cấu hình
- `output.total` = tổng số bản ghi (NUMBER)
- Các giá trị `{OBJECT_TYPE_ID}` và `{object_type_slug}` trong `metaDataType` của output resource **BẮT BUỘC** lấy từ skill `/object-info` (xem mục 25 trong Lưu ý quan trọng)

### Ví dụ quy trình với Get Record Task

**Mô tả:** Start -> Root -> Get Leads -> End Process

```
Bắt đầu -> Root (User Task) -> Get Leads (Get Record Task) -> Kết thúc
```

**Cấu hình:**
- Object Type: Lead (`objectTypeSlug: "lead"`)
- Logic: Không có điều kiện lọc (`logicType: "NONE"`)
- Kết quả: Lấy tất cả bản ghi (`resultType: 2`) nếu output được đưa vào Loop; dùng `1` khi chỉ tiêu thụ `output.record`

### Sử dụng output của Get Record trong các bước sau

Output của Get Record có thể được tham chiếu trong các bước tiếp theo:
- `$action.{slug}.output.record` = bản ghi đơn
- `$action.{slug}.output.records` = danh sách bản ghi
- `$action.{slug}.output.total` = tổng số bản ghi

---
