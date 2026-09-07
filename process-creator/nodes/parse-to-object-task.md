# JSON to Object Task

Đọc file này khi cần parse một chuỗi JSON thành RECORD resources cho các node sau.

> **Runtime compatibility:** Backend `run-workflow-server` hiện có parser/model cho schema này nhưng chưa đăng ký action `PARSE_TO_OBJECT` trong runtime factory. Process có thể create/validate nhưng khi chạy sẽ lỗi `ERROR_SEND_TASK_NOT_SET_TYPE` (thường được API bọc thành code 213). Không tạo node này cho process executable và không retry bằng biến thể payload. Chỉ dùng phần dưới để nhận diện, đọc hoặc migrate payload cũ; test lại registration trước khi đổi trạng thái hỗ trợ.

## Nhận diện

| Thuộc tính | Giá trị |
|---|---|
| Tên trên UI | JSON to Object |
| renderKey | `PARSE_TO_OBJECT_TASK` |
| XML element | `elEx:parseToObjectTask` |
| Action type | `PARSE_TO_OBJECT` |

## Action data

```json
{
  "inputSource": {
    "type": 1,
    "value": "{\"customer\":{\"name\":\"An\"},\"total\":120000}"
  },
  "sampleResponse": "{\"customer\":{\"name\":\"An\"},\"total\":120000}",
  "parseToDataType": {
    "nameDataType": "string",
    "children": []
  },
  "continueOnError": true
}
```

Quy tắc:

- Dùng `inputSource.type: 1` cho raw JSON.
- Nếu input chứa `$...` hoặc `{{...}}`, payload dùng `type: 4` và thêm `valueDataType`, `valuePathName`.
- Bắt buộc `inputSource`, JSON hợp lệ trong `sampleResponse` và ít nhất một child sau khi parse sample.
- Không dùng sample có array lồng trực tiếp trong array; front-end từ chối cấu trúc đó.
- Tạo `parseToDataType.children` theo schema trả về từ API convert sample. Giữ recursive `children`, `dataType`, `isList`, `metaDataType` và `actionType: "PARSE_TO_OBJECT"`.

## Output resources

Tạo `input` (`TEXT`) và `output` (`RECORD`). Copy schema đã parse vào `output.children`. Mọi resource dùng `availableForInput: false`, `availableForOutput: true`.

## XML

```xml
<elEx:parseToObjectTask id="NOPARSE0000001" name="Parse order JSON">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="PARSE_TO_OBJECT_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>FLFLOW00000001</bpmn2:incoming>
  <bpmn2:outgoing>FLFLOW00000002</bpmn2:outgoing>
</elEx:parseToObjectTask>
```

Xem `samples/sample_parse_to_object.json`.
