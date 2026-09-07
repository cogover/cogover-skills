## Các loại trường Form trong User Task

Mỗi User Task có thể chứa form với nhiều loại trường khác nhau. Các trường được đặt trong mảng `components` của group.

### Cấu trúc chung của một trường

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "ten_truong",
  "name": "Tên trường",
  "description": "",
  "fieldType": "loai_truong",
  "fieldMetaData": { ... },
  "required": 0,
  "multiple": 0,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_1",
  "disable": null,
  "readOnly": null
}
```

### Ràng buộc bắt buộc giữa Trường bắt buộc, Trường chỉ đọc và Gửi dữ liệu

Ba checkbox trên giao diện map vào payload như sau:

| Checkbox trên UI | Field trong payload |
|---|---|
| Trường bắt buộc | `required` |
| Trường chỉ đọc | `readOnly` |
| Gửi dữ liệu | `canSendData` |

Nếu một field đồng thời có `required: 1` (hoặc `true`) và `readOnly: true` (hoặc `1`) thì **bắt buộc** đặt `canSendData: true` ngay trên component trong `userTasks[].content`.

```json
{
  "id": "{COMPONENT_UUID}",
  "slug": "ma_yeu_cau",
  "required": 1,
  "readOnly": true,
  "canSendData": true
}
```

Trước khi create, update hoặc lưu version mới, duyệt toàn bộ field của mọi User Task và reject payload nếu còn trường hợp `required && readOnly && canSendData !== true`. `canSendData` quyết định field có được đưa vào payload submit form gửi tới `run-workflow-server` hay không. Thuộc tính này độc lập với `availableForOutput` của component/resource và không cần đồng bộ sang `resources.userTasks[].resources[]`. Nếu không bật **Gửi dữ liệu**, server có thể không nhận field chỉ đọc trong dữ liệu submit và trả lỗi thiếu dữ liệu bắt buộc.

### 1. Văn bản ngắn (short_text)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "van_ban_ngan",
  "name": "Văn bản ngắn",
  "description": "",
  "fieldType": "short_text",
  "fieldMetaData": {
    "character_limit": {
      "min": 0,
      "max": 255
    },
    "multiple_limit": {
      "min": 0,
      "max": 30
    }
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_1",
  "disable": null,
  "readOnly": null,
  "defaultTextValueType": 1
}
```

### 2. Văn bản dài (long_text)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "van_ban_dai",
  "name": "Văn bản dài",
  "description": "",
  "fieldType": "long_text",
  "fieldMetaData": {
    "character_limit": {
      "min": 0,
      "max": 131072
    },
    "rich_text": false
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_2",
  "disable": null,
  "readOnly": null,
  "defaultTextValueType": 1
}
```

### 3. URL

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "url",
  "name": "URL",
  "description": "",
  "fieldType": "url",
  "fieldMetaData": {
    "character_limit": {
      "min": 0,
      "max": 2048
    },
    "multiple_limit": {
      "min": 0,
      "max": 30
    },
    "use_display_text": false
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_3",
  "disable": null,
  "readOnly": null
}
```

### 4. Số nguyên (numeric)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "so_nguyen",
  "name": "Số nguyên",
  "description": "",
  "fieldType": "numeric",
  "fieldMetaData": {
    "value_limit": {
      "min": -9999999999,
      "max": 9999999999
    },
    "multiple_limit": {
      "min": 0,
      "max": 30
    },
    "format": {
      "type": 1,
      "format": 3
    },
    "precision": -1,
    "integral_length": 10,
    "fractional_length": 0,
    "display_type": 1,
    "round_rule": 0
  },
  "required": 0,
  "multiple": 0,
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_4",
  "disable": null,
  "readOnly": null,
  "defaultValue": null,
  "min": -9999999999,
  "max": 9999999999,
  "displayType": "integer",
  "format": "# ##0",
  "roundRule": null,
  "precision": -1,
  "numberOfIntegerDigits": 10,
  "numberOfDecimalDigits": 0
}
```

### 5. Số thập phân (decimal)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "so_thap_phan",
  "name": "Số thập phân",
  "description": "",
  "fieldType": "decimal",
  "fieldMetaData": {
    "value_limit": {
      "min": -9999999999.999998,
      "max": 9999999999.999998
    },
    "multiple_limit": {
      "min": 0,
      "max": 30
    },
    "format": {
      "type": 1,
      "format": 5
    },
    "precision": 5,
    "integral_length": 10,
    "fractional_length": 6,
    "display_type": 2,
    "round_rule": 0
  },
  "required": 0,
  "multiple": 0,
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_5",
  "disable": null,
  "readOnly": null,
  "defaultValue": null,
  "min": -9999999999.999998,
  "max": 9999999999.999998,
  "displayType": "decimal",
  "format": "# ##0.0",
  "roundRule": null,
  "precision": 5,
  "numberOfIntegerDigits": 10,
  "numberOfDecimalDigits": 6
}
```

### 6. Phần trăm (percent)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "phan_tram",
  "name": "Phần trăm",
  "description": "",
  "fieldType": "percent",
  "fieldMetaData": {
    "value_limit": {
      "min": -9999999999,
      "max": 9999999999
    },
    "multiple_limit": {
      "min": 0,
      "max": 30
    },
    "format": {
      "type": 1,
      "format": 3
    },
    "precision": -1,
    "integral_length": 10,
    "fractional_length": 0,
    "display_type": 1,
    "round_rule": 0
  },
  "required": 0,
  "multiple": 0,
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_8",
  "disable": null,
  "readOnly": null,
  "defaultValue": null,
  "min": -9999999999,
  "max": 9999999999,
  "displayType": "integer",
  "format": "# ##0",
  "roundRule": null,
  "precision": -1,
  "numberOfIntegerDigits": 10,
  "numberOfDecimalDigits": 0
}
```

### 7. Tiền tệ (currency)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "tien_te_vnd",
  "name": "Tiền tệ (VND)",
  "description": "",
  "fieldType": "currency",
  "fieldMetaData": {
    "value_limit": {
      "min": -9999999999,
      "max": 9999999999
    },
    "multiple_limit": {
      "min": 0,
      "max": 30
    },
    "format": {
      "type": 1,
      "format": 3
    },
    "precision": -1,
    "integral_length": 14,
    "fractional_length": 0,
    "display_type": 1,
    "round_rule": 0,
    "country_code": "vn",
    "unit_position": "after"
  },
  "required": 0,
  "multiple": 0,
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_9",
  "disable": null,
  "readOnly": null,
  "defaultValue": null,
  "min": -9999999999,
  "max": 9999999999,
  "displayType": "integer",
  "format": "# ##0",
  "roundRule": null,
  "precision": -1,
  "numberOfIntegerDigits": 14,
  "numberOfDecimalDigits": 0,
  "countryCode": ["vn"],
  "unitPosition": "after"
}
```

### 8. File (đơn và nhiều)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "file",
  "name": "File",
  "description": "",
  "fieldType": "file",
  "fieldMetaData": {
    "multiple_limit": {
      "min": 0,
      "max": 30
    },
    "max_size": 52428800,
    "file_type": [
      "doc", "docx", "xlsx", "xls", "csv", "ppt", "pptx", "pdf", "txt", "rtf",
      "html", "htm", "zip", "jpg", "jpeg", "png", "svg", "gif", "bmp", "tiff",
      "tif", "webp", "mp4", "avi", "mov", "wmv", "mkv", "qt", "webm", "mp3",
      "aac", "m4a"
    ],
    "file_group_type": "file-media",
    "is_public": false,
    "is_resizable": true,
    "signing_position": [],
    "is_signing_file": false
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_6",
  "hintText": "",
  "disable": null,
  "readOnly": null
}
```

**Lưu ý:** Để cho phép nhiều file, đặt `"multiple": 1`

### 9. Ngày (date)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "ngay",
  "name": "Ngày",
  "description": "",
  "fieldType": "date",
  "fieldMetaData": {
    "value_limit": {
      "from": null,
      "to": null
    },
    "default_value_current": false,
    "format": {
      "format": "workspace"
    },
    "multiple_limit": {
      "min": 0,
      "max": 30
    }
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": null,
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_10"
}
```

### 10. Ngày giờ (date_time)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "ngay_gio",
  "name": "Ngày giờ",
  "description": "",
  "fieldType": "date_time",
  "fieldMetaData": {
    "value_limit": {
      "from": null,
      "to": null
    },
    "default_value_current": false,
    "format": {
      "date": "workspace",
      "time": "workspace"
    },
    "multiple_limit": {
      "min": 0,
      "max": 30
    }
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": null,
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_11"
}
```

### 11. Email

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "email",
  "name": "Email",
  "description": "",
  "fieldType": "email",
  "fieldMetaData": {
    "character_limit": {
      "min": 0,
      "max": 255
    },
    "multiple_limit": {
      "min": 0,
      "max": 30
    }
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_12",
  "disable": null,
  "readOnly": null
}
```

**Lưu ý:** Để cho phép nhiều email, đặt `"multiple": 1`

### 12. Nhãn (label)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "nhan",
  "name": "Nhãn",
  "description": "",
  "fieldType": "label",
  "fieldMetaData": {
    "character_limit": {
      "min": 0,
      "max": 255
    },
    "multiple_limit": {
      "min": 0,
      "max": 30
    }
  },
  "required": 0,
  "multiple": 1,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_13",
  "disable": null,
  "readOnly": null
}
```

### 13. Số điện thoại (phone)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "so_dien_thoai",
  "name": "Số điện thoại",
  "description": "",
  "fieldType": "phone",
  "fieldMetaData": {
    "country_code": ["*"],
    "multiple_limit": {
      "min": 0,
      "max": 30
    }
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_14",
  "disable": null,
  "readOnly": null
}
```

**Lưu ý:** `country_code: ["*"]` cho phép tất cả mã quốc gia. Để cho phép nhiều số, đặt `"multiple": 1`

### 14. Boolean

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "boolean",
  "name": "Boolean",
  "description": "",
  "fieldType": "boolean",
  "fieldMetaData": {
    "true_value": "Yes",
    "false_value": "No"
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": "false",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_17"
}
```

### 15. Tra cứu (lookup_normal)

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "tra_cuu_toi_contact",
  "name": "Tra cứu tới Contact",
  "description": "",
  "fieldType": "lookup_normal",
  "fieldMetaData": {
    "multiple_limit": {
      "min": 0,
      "max": 30
    },
    "link_field": "id",
    "object": "OT00000000007",
    "object_slug": "contact"
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": null,
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_18",
  "defaultValueRecord": 1,
  "minLength": 0,
  "maxLength": 30
}
```

**Lưu ý:**
- `object`: ID của object type để tra cứu — **BẮT BUỘC** sử dụng skill `/object-info` để lấy objectTypeId chính xác. **KHÔNG** dùng ID từ ví dụ (ví dụ `OT00000000007` ở trên chỉ là minh họa, giá trị thực tế thay đổi theo workspace).
- `object_slug`: slug của object type (ví dụ: "contact", "personnel") — cũng cần lấy từ skill `/object-info`.
- Khi tạo trường lookup, **BẮT BUỘC** phải gọi skill `/object-info` để lấy đúng `object` (objectTypeId) và `object_slug` của đối tượng đích trước khi tạo JSON (xem mục 25 trong Lưu ý quan trọng).
- **`defaultValueRecord`**:
  - `1`: Khi trường lookup **không có** giá trị mặc định từ biến/resource (người dùng tự nhập/chọn)
  - `0`: Khi trường lookup **có** giá trị mặc định là biến/resource (ví dụ: `$flow.xxx`, `$action.xxx.output.record`, `$userTask.xxx`)

> **QUAN TRỌNG:** Khi trường lookup dùng `defaultValue` là tham chiếu biến/resource, **bắt buộc** phải set `defaultValueRecord: 0`.


### 16. Danh sách lựa chọn (select_list)

Trường cho phép chọn giá trị từ danh sách tùy chọn. Hỗ trợ chọn một hoặc chọn nhiều, với nhiều kiểu dữ liệu: TEXT, NUMBER, DATE, DATE_TIME.

#### Các kiểu dữ liệu và displayType

| Chế độ chọn | `multiple` | `displayType`     |
|-------------|------------|-------------------|
| Chọn một    | `0`        | `"single_choice"` |
| Chọn nhiều  | `1`        | `"multi_choices"` |

| Kiểu dữ liệu | `dataType`    | `optionConfig.valueDataType` | Kiểu `value` trong option      |
|--------------|---------------|------------------------------|--------------------------------|
| Chữ          | `"TEXT"`      | `"TEXT"`                     | Chuỗi: `"Lua chon 1"`          |
| Số           | `"NUMBER"`    | `"NUMBER"`                   | Số: `1`, `2`, `3`              |
| Ngày         | `"DATE"`      | `"DATE"`                     | Chuỗi ngày: `"2026-02-01"`     |
| Ngày giờ     | `"DATE_TIME"` | `"DATE_TIME"`                | Timestamp hoặc tham chiếu biến |

#### Cấu trúc component

```json
{
  "id": "uuid",
  "status": 1,
  "slug": "lua_chon_nhieu_chu",
  "name": "Lựa chọn nhiều: chữ",
  "description": "",
  "displayType": "multi_choices",
  "fieldType": "select_list",
  "fieldMetaData": {
    "object": "",
    "link_field": "id",
    "object_slug": "",
    "fractional_length": 0
  },
  "required": 0,
  "multiple": 1,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false,
  "label": "",
  "uiSlug": "_1",
  "disable": null,
  "readOnly": null,
  "dataType": "TEXT",
  "useVariableOrResource": 0,
  "optionConfig": {
    "options": [
      {
        "sourceType": "RAW",
        "label": "Lua chon 1",
        "labelPathName": "",
        "labelDataType": "",
        "labelIsRaw": true,
        "slug": "lua_chon_1",
        "isDefault": false,
        "value": "Lua chon 1",
        "valuePathName": "",
        "valueIsRaw": true,
        "objectTypeId": "",
        "logic": "",
        "logicType": "AND",
        "conditions": [],
        "sortFields": []
      },
      {
        "sourceType": "RAW",
        "label": "Lua chon 2",
        "labelPathName": "",
        "labelDataType": "",
        "labelIsRaw": true,
        "slug": "lua_chon_2",
        "isDefault": true,
        "value": "Lua chon 2",
        "valuePathName": "",
        "valueIsRaw": true,
        "objectTypeId": "",
        "logic": "",
        "logicType": "AND",
        "conditions": [],
        "sortFields": []
      }
    ],
    "valueDataType": "TEXT"
  }
}
```

#### Ví dụ: Chọn một, kiểu Số (NUMBER)

```json
{
  "slug": "lua_chon_1_so",
  "name": "Lựa chọn 1: số",
  "displayType": "single_choice",
  "fieldType": "select_list",
  "multiple": 0,
  "dataType": "NUMBER",
  "optionConfig": {
    "options": [
      {
        "sourceType": "RAW",
        "label": "Lựa chọn 1",
        "labelPathName": "",
        "labelDataType": "",
        "labelIsRaw": true,
        "slug": "lua_chon_1",
        "isDefault": false,
        "value": 1,
        "valuePathName": "",
        "valueIsRaw": true,
        "objectTypeId": "",
        "logic": "",
        "logicType": "AND",
        "conditions": [],
        "sortFields": []
      },
      {
        "sourceType": "RAW",
        "label": "Lựa chọn 2",
        "labelPathName": "",
        "labelDataType": "",
        "labelIsRaw": true,
        "slug": "lua_chon_2",
        "isDefault": true,
        "value": 2,
        "valuePathName": "",
        "valueIsRaw": true,
        "objectTypeId": "",
        "logic": "",
        "logicType": "AND",
        "conditions": [],
        "sortFields": []
      }
    ],
    "valueDataType": "NUMBER"
  }
}
```

#### Ví dụ: Chọn một, kiểu Ngày (DATE)

```json
{
  "slug": "lua_chon_1_ngay",
  "name": "Lựa chọn 1: ngày",
  "displayType": "single_choice",
  "fieldType": "select_list",
  "multiple": 0,
  "dataType": "DATE",
  "optionConfig": {
    "options": [
      {
        "sourceType": "RAW",
        "label": "Ngày 1",
        "labelPathName": "",
        "labelDataType": "",
        "labelIsRaw": true,
        "slug": "ngay_1",
        "isDefault": false,
        "value": "2026-02-01",
        "valuePathName": "",
        "valueIsRaw": true,
        "objectTypeId": "",
        "logic": "",
        "logicType": "AND",
        "conditions": [],
        "sortFields": []
      }
    ],
    "valueDataType": "DATE"
  }
}
```

#### Ví dụ: Chọn một, kiểu Ngày giờ (DATE_TIME) với giá trị tham chiếu

Khi `value` là tham chiếu đến biến/resource (không phải giá trị raw):
- `valueIsRaw`: `false`
- `value`: đường dẫn tham chiếu (ví dụ: `$userTask.{task_slug}.submittedBy.created`)
- `valuePathName`: tên hiển thị đường dẫn (ví dụ: `"workflow_resource:list.userTask / {Task Name} / Submitted By / Created"`)
- `valueDataType`: kiểu dữ liệu của giá trị tham chiếu (ví dụ: `"DATE_TIME"`)

```json
{
  "slug": "lua_chon_1_ngay_gio",
  "name": "Lựa chọn 1: ngày giờ",
  "displayType": "single_choice",
  "fieldType": "select_list",
  "multiple": 0,
  "dataType": "DATE_TIME",
  "optionConfig": {
    "options": [
      {
        "sourceType": "RAW",
        "label": "Ngày giờ 1",
        "labelPathName": "",
        "labelDataType": "",
        "labelIsRaw": true,
        "slug": "ngay_gio_1",
        "isDefault": true,
        "value": "$userTask.{task_slug}.submittedBy.created",
        "valuePathName": "workflow_resource:list.userTask / {Task Name} / Submitted By / Created",
        "valueDataType": "DATE_TIME",
        "valueIsRaw": false,
        "objectTypeId": "",
        "logic": "",
        "logicType": "AND",
        "conditions": [],
        "sortFields": []
      },
      {
        "sourceType": "RAW",
        "label": "Ngày giờ 2",
        "labelPathName": "",
        "labelDataType": "",
        "labelIsRaw": true,
        "slug": "ngay_gio_2",
        "isDefault": false,
        "value": "$userTask.{task_slug}.startAt",
        "valuePathName": "workflow_resource:list.userTask / {Task Name} / Start At",
        "valueDataType": "DATE_TIME",
        "valueIsRaw": false,
        "objectTypeId": "",
        "logic": "",
        "logicType": "AND",
        "conditions": [],
        "sortFields": []
      }
    ],
    "valueDataType": "DATE_TIME"
  }
}
```

#### Resource cho select_list (trong `resources.userTasks[].resources[]`)

Resource của select_list có cấu trúc khác biệt so với các trường thông thường:
- `dataType` luôn là `"SELECT_LIST"` (không phải kiểu dữ liệu thực tế)
- Kiểu dữ liệu thực tế nằm trong `selectListDataType`
- Chế độ hiển thị nằm trong `selectListDisplayType`
- `isList`: `true` nếu `multi_choices`, `false` nếu `single_choice`

```json
{
  "absoluteSlug": "$userTask.{task_slug}.{field_slug}",
  "parentMetadata": "",
  "defaultValue": "",
  "dataType": "SELECT_LIST",
  "description": "",
  "type": 1,
  "isList": true,
  "selectListDataType": "TEXT",
  "parentId": "{NODE_CONFIG_ID}",
  "availableForInput": false,
  "isStandard": true,
  "processId": "{PROCESS_ID}",
  "optionConfig": {
    "valueObjectTypeId": "",
    "valueDataTypeId": "",
    "name": "",
    "options": [
      {
        "isDefault": false,
        "sourceType": "RAW",
        "displayOrder": 1,
        "id": "{OPTION_ID_PREFIX_SLO}",
        "label": "Lua chon 1",
        "value": "Lua chon 1",
        "slug": "lua_chon_1",
        "valueIsRaw": true
      },
      {
        "isDefault": true,
        "sourceType": "RAW",
        "displayOrder": 2,
        "id": "{OPTION_ID_PREFIX_SLO}",
        "label": "Lua chon 2",
        "value": "Lua chon 2",
        "slug": "lua_chon_2",
        "valueIsRaw": true
      }
    ],
    "valueDataType": "TEXT",
    "slug": ""
  },
  "selectListDisplayType": "multi_choices",
  "name": "Lựa chọn nhiều: chữ",
  "metaDataType": {
    "link_field": "id",
    "fractional_length": 0,
    "object_slug": "",
    "object": ""
  },
  "availableForOutput": false,
  "absolutePath": "workflow_resource:list.userTask / {Task Name} / {Field Name}",
  "id": "{SCREEN_ID}",
  "parentTable": "node_screen",
  "defaultTextValueType": 0,
  "slug": "{field_slug}",
  "fieldId": "{COMPONENT_UUID}",
  "isComponent": true
}
```

**So sánh option trong component vs resource:**

| Thuộc tính                                                       | Component option    | Resource option   |
|------------------------------------------------------------------|---------------------|-------------------|
| `sourceType`                                                     | `"RAW"`             | `"RAW"`           |
| `label`                                                          | Có                  | Có                |
| `value`                                                          | Có                  | Có                |
| `slug`                                                           | Có                  | Có                |
| `isDefault`                                                      | Có                  | Có                |
| `valueIsRaw`                                                     | Có                  | Có                |
| `displayOrder`                                                   | Không có            | Có (1, 2, 3, ...) |
| `id`                                                             | Không có            | Có (prefix `SLO`) |
| `labelPathName`, `labelDataType`, `labelIsRaw`                   | Có                  | Không có          |
| `objectTypeId`, `logic`, `logicType`, `conditions`, `sortFields` | Có                  | Không có          |
| `valuePathName`, `valueDataType` (option level)                  | Có (khi tham chiếu) | Không có          |

#### externalResourcesUsedIn cho select_list

Khi option của select_list sử dụng giá trị tham chiếu (`valueIsRaw: false`) đến trường con của resource (ví dụ: `$userTask.{task_slug}.submittedBy.created`), cần thêm vào mảng `externalResourcesUsedIn` ở root level:

```json
{
  "externalResourcesUsedIn": [
    {
      "absoluteSlug": "$userTask.{task_slug}.submittedBy.created",
      "parentMetadata": "",
      "dataType": "DATE_TIME",
      "type": 1,
      "isList": false,
      "parentId": "{SUBMITTED_BY_RESOURCE_ID}",
      "isSystem": false,
      "availableForInput": false,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "name": "Created",
      "availableForOutput": false,
      "absolutePath": "workflow_resource:list.userTask / {Task Name} / Submitted By / Created",
      "parentTable": "resource",
      "slug": "created"
    }
  ]
}
```

**Lưu ý quan trọng:**
- `displayType`: `"single_choice"` cho chọn một, `"multi_choices"` cho chọn nhiều (KHÔNG phải "multiple_choice")
- `multiple`: `0` cho chọn một, `1` cho chọn nhiều (liên kết với `displayType`)
- `dataType` và `optionConfig.valueDataType` phải khớp nhau
- `isDefault`: `true` cho lựa chọn được chọn sẵn, `false` cho không chọn sẵn. Có thể có nhiều `isDefault: true` khi `multi_choices`
- Khi `value` là giá trị raw: `valueIsRaw: true`, `valuePathName: ""`
- Khi `value` là tham chiếu: `valueIsRaw: false`, cần có `valuePathName` và `valueDataType` trong option (ở component), và cần thêm `externalResourcesUsedIn` nếu tham chiếu đến trường con
- Resource `dataType` luôn là `"SELECT_LIST"`, kiểu thực tế nằm trong `selectListDataType`
- Resource `isList`: `true` khi `multi_choices`, `false` khi `single_choice`

---

### 17. Văn bản theo biểu thức (`regex`)

`regex` là field nhập TEXT có validation bằng biểu thức chính quy. Resource tương ứng dùng `dataType: "TEXT"`.

```json
{
  "id": "{COMPONENT_UUID}",
  "status": 1,
  "slug": "ma_dinh_danh",
  "name": "Mã định danh",
  "description": "",
  "fieldType": "regex",
  "fieldMetaData": {
    "character_limit": { "min": 0, "max": 255 },
    "multiple_limit": { "min": 0, "max": 30 },
    "regex": "^[A-Z]{3}-[0-9]{4}$"
  },
  "required": 0,
  "multiple": 0,
  "defaultValue": "",
  "isStandard": 0,
  "manualModifyAllow": true,
  "toolTip": "",
  "hintText": "",
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false
}
```

Khi `multiple: 1`, giữ `multiple_limit` hợp lệ và serialize `defaultValue` theo dạng danh sách giống các field text nhiều giá trị.

### 18. Văn bản hiển thị (`display_text`)

`display_text` chỉ hiển thị nội dung, không phải field nhập và không tạo variable/resource User Task. `displayTextType` nhận `"text"`, `"html"` hoặc `"markdown"`.

```json
{
  "id": "{COMPONENT_UUID}",
  "status": 1,
  "slug": "huong_dan",
  "name": "",
  "fieldType": "display_text",
  "displayTextType": "html",
  "fieldMetaData": { "rich_text": true },
  "defaultValue": "<p>Vui lòng kiểm tra thông tin trước khi gửi.</p>",
  "defaultTextValueType": 1,
  "required": 0,
  "multiple": 0,
  "isStandard": 0,
  "manualModifyAllow": true,
  "options": [],
  "unique": false,
  "availableForInput": false,
  "availableForOutput": false
}
```

Nếu nội dung tham chiếu resource, điền thêm `defaultValueDataType`/`defaultValuePathName` và dùng `defaultTextValueType` phù hợp với resource được chọn.

### 19. Bảng chọn bản ghi (`select_record_table`)

`select_record_table` hiển thị bảng record từ một Object Type và hỗ trợ ba `selectionMode`: `"multiple"`, `"single"`, `"display_only"`.

```json
{
  "id": "{COMPONENT_UUID}",
  "status": 1,
  "slug": "chon_khach_hang",
  "name": "Chọn khách hàng",
  "fieldType": "select_record_table",
  "description": "",
  "required": 1,
  "readOnly": 0,
  "disable": 0,
  "isShowName": true,
  "objectId": "{OBJECT_TYPE_ID}",
  "objectSlug": "{OBJECT_TYPE_SLUG}",
  "sourceData": "",
  "searchFields": ["name"],
  "selectionMode": "multiple",
  "minCount": 1,
  "maxCount": 10,
  "defaultValue": "",
  "availableForInput": false,
  "availableForOutput": false,
  "tableSettings": ""
}
```

- Luôn lấy `objectId`, `objectSlug`, search field và table settings từ API/object metadata thật.
- `display_only` không tạo resource vì người dùng không chọn record.
- `single` tạo child resource `selected_row`.
- `multiple` tạo child resources `selected_rows` (`isList: true`) và `first_selected_row` (`isList: false`).
- Resource cha dùng `dataType: "RECORD"`, `isList: false` và chứa các child resource trên.

---
