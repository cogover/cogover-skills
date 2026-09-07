# Omni Message Task

Đọc file này khi gửi message qua nhiều provider theo thứ tự fallback.

## Nhận diện đặc biệt

| Thuộc tính | Giá trị |
|---|---|
| renderKey | `OMNI_MESSAGE_TASK` |
| BPMN element | `bpmn2:sendTask` |
| Marker extension | `elEx:omniMessageTask` |
| Action type | `OMNI_MESSAGE` |
| Kiểu `action.data` | **JSON string** |

Không tạo `<elEx:omniMessageTask>` làm BPMN node. Tạo `bpmn2:sendTask`, rồi thêm marker trong `extensionElements`.

## Data trước khi stringify

```json
{
  "to": { "type": 1, "value": "+84901234567" },
  "continueOnAllFailed": true,
  "trackingIdPrefix": "order_notice",
  "methods": [
    {
      "id": "00000000-0000-4000-8000-000000000147",
      "order": 1,
      "enabled": true,
      "type": "ZALO_ZBS",
      "timeoutSeconds": 60,
      "successCriteria": "SENT",
      "oaId": { "type": 1, "value": "ZALO_OA_ID" },
      "templateId": { "type": 1, "value": "ZBS_TEMPLATE_ID" },
      "deliveryMethod": "PHONE",
      "sendingMode": 1,
      "templateData": {}
    }
  ]
}
```

Serialize toàn bộ object trên bằng `JSON.stringify` rồi đặt chuỗi kết quả vào `action.data`.

Quy tắc:

- `to.type` chỉ nhận `1` raw hoặc `4` resource.
- Bắt buộc ít nhất một method enabled; `order` bắt đầu từ 1 và không trùng.
- `timeoutSeconds`: lớn hơn 0, tối đa 86400.
- `successCriteria`: `SENT` hoặc `DELIVERED`.
- `trackingIdPrefix`: tối đa 32 ký tự, chỉ chữ, số và `_`.
- Hỗ trợ `ZALO_ZBS` và `WHATSAPP`. Không sinh `SMS_BRANDNAME` vì UI đang disable.
- Zalo: dùng `oaId`, `templateId`, `deliveryMethod` (`PHONE`, `HASH_PHONE`, `UID`), `sendingMode` (`1`, `3`).
- WhatsApp: dùng `pageId`, `templateId`, `language`, `templateData`; không thêm delivery/sending mode của Zalo.

## ID integration và xác minh runtime

- `oaId`, `pageId` và `templateId` phải là ID thật của integration/template đang active trong đúng workspace. Không dùng các giá trị `ZALO_OA_ID`, `ZBS_TEMPLATE_ID` hoặc ID QA trong sample để tạo process thật.
- Nếu chưa có skill/API contract chuyên trách để list các ID này, hỏi người dùng cung cấp ID đã xác minh hoặc dừng ở bản nháp chưa sẵn sàng runtime. Không đoán endpoint và không tuyên bố gửi được message chỉ vì process API trả `isValid: true`.
- Chỉ xác nhận khả năng gửi thật sau khi provider/template được kiểm tra và có một lần chạy thử theo yêu cầu của người dùng. Việc POST/GET process thành công chỉ xác minh contract lưu cấu hình.

## Canonicalization sau GET

Contract request và contract response không hoàn toàn giống nhau:

- Trước POST/PUT, `action.data` phải là JSON string và XML request phải có marker `<elEx:omniMessageTask />`.
- Khi GET-back, server có thể parse `action.data` thành object và bỏ marker rỗng, nhưng vẫn giữ `renderKey="OMNI_MESSAGE_TASK"` và action `type: "OMNI_MESSAGE"`.
- Hậu kiểm theo semantic: sendTask/renderKey, recipient, danh sách method, order, enabled, timeout, success criteria và output resources. Không PUT hoặc recreate chỉ để khôi phục string/marker representation của request.

## Output resources

Tạo `startAt`, `endAt` và `output`. `output` là RECORD gồm các trường success và danh sách `attempts`; mỗi attempt chứa method/provider status, IDs, error và timestamps. Dùng `isList: true` cho `attempts`.

## XML

```xml
<bpmn2:sendTask id="NOOMNI00000001" name="Send omni message">
  <bpmn2:extensionElements>
    <elEx:omniMessageTask />
    <configEx:elementInfo renderKey="OMNI_MESSAGE_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>FLFLOW00000001</bpmn2:incoming>
  <bpmn2:outgoing>FLFLOW00000002</bpmn2:outgoing>
</bpmn2:sendTask>
```

Xem `samples/sample_omni_message.json`.
