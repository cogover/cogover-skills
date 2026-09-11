# Export Record Task

Đọc file này khi xuất một record thành file từ document template.

## Nhận diện

| Thuộc tính | Giá trị |
|---|---|
| renderKey | `EXPORT_TASK` |
| XML element | `elEx:exportRecordTask` |
| Action type | `EXPORT_RECORD` |

## Action data canonical

```json
{
  "objectSlug": "lead",
  "recordId": "$flow.input.record.id",
  "exportType": "template",
  "layoutId": "",
  "templateId": "DOCUMENT_TEMPLATE_ID"
}
```

Quy tắc:

- Lấy `objectSlug` thật từ `$object-info`; không sao chép object slug trong sample.
- `recordId` **bắt buộc là absolute resource slug**. Runtime luôn resolve chuỗi này qua resource registry trước khi export; gửi ID raw như `QU...` sẽ lỗi `RESOURCE_NOT_VALID`.
- Resource có thể trả về RECORD (`{"id":"..."}`) hoặc TEXT chứa record ID. Nếu người dùng chỉ có ID cố định, tạo Variable TEXT có `defaultValue` là ID thật rồi dùng `$flow.{variable_slug}`; không đặt ID trực tiếp vào `data.recordId`.
- Payload được hỗ trợ trong mẫu này dùng `exportType: "template"`. Không sinh `exportType: "layout"` khi chưa có tài liệu sản phẩm và kiểm chứng API cho mode đó.
- Khi `exportType` là `template`, bắt buộc `templateId` thật đã được xác minh.

## Lấy Document Template thật

Bắt buộc dùng skill `$document-template`; không gọi `/records/list`, không lấy Object Type ID `OT...` làm `templateId` và không sao chép ID minh họa trong sample.

1. Đọc và làm theo `$document-template`, gồm reference API/auth mà skill đó yêu cầu.
2. Dùng workflow list/search của `$document-template` để lọc `related_object` theo đúng `objectSlug`; lấy candidate ID từ kết quả.
3. Dùng workflow detail của `$document-template` để xác minh ID, tên, `related_object`, `file_format`, `download_format` và nội dung template tồn tại.
4. Nếu chưa có template phù hợp, chỉ tạo mới thông qua `$document-template` và tuân thủ bước mapping/xác nhận của skill đó; không tự dựng template trong `process-creator`.
5. Chỉ sau detail thành công mới đặt ID vào `data.templateId`. Nếu không lấy hoặc tạo được template thật, dừng tạo Export Record và hỏi người dùng; không dùng ID QA giả.

`DOCUMENT_TEMPLATE_ID` trong snippet và ID trong sample chỉ minh họa cấu trúc, không phải giá trị có thể tái sử dụng giữa các workspace.

## Output resources

Tạo `$action.{slug}.output` kiểu `RECORD`, chứa child `file` kiểu `FILE`. Đặt output và child `availableForInput: false`, `availableForOutput: true`.

## Kiểm thử runtime

Sau publish/run, Debug không được có `RESOURCE_NOT_VALID`. Xác nhận output `file` là FileValue thật, tải file, mở được và nội dung khớp đúng record/template. Instance Completed mà chưa tải/mở file chỉ là PARTIAL.

## XML

```xml
<elEx:exportRecordTask id="NOEXPORT000001" name="Export lead">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="EXPORT_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>FLFLOW00000001</bpmn2:incoming>
  <bpmn2:outgoing>FLFLOW00000002</bpmn2:outgoing>
</elEx:exportRecordTask>
```

Xem `samples/sample_export_record.json`.
