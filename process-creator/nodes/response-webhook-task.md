# Respond to Webhook Task

Đọc file này khi webhook không phản hồi ngay mà cần một node chủ động trả response.

> **Runtime compatibility:** Backend `run-workflow-server` hiện chưa đăng ký action `RESPONSE_WEBHOOK` trong runtime factory. Process có thể create/validate nhưng node không chạy được và có thể lỗi `ERROR_SEND_TASK_NOT_SET_TYPE`. Không tạo node này cho process executable. Phần dưới chỉ dùng để nhận diện/migrate schema cũ; test lại runtime registration trước khi đổi trạng thái hỗ trợ.

## Nhận diện

| Thuộc tính | Giá trị |
|---|---|
| renderKey | `RESPONSE_WEBHOOK_TASK` |
| XML element | `elEx:responseWebhookTask` |
| Action type | `RESPONSE_WEBHOOK` |

## Nguồn webhook

Chọn đúng một nguồn chưa được Respond to Webhook node khác sử dụng:

- Webhook Trigger Start: `waitActionType: "start"`, `waitActionSlug` bằng **ID của Start Event**.
- Wait nhận webhook: `waitActionType: "wait"`, `waitActionSlug` bằng **slug của Wait action**.

Với Webhook Trigger Start, đặt `metadata.respondTiming: "USE_RESPOND_TO_WEBHOOK"`.

### Lưu ý khi tạo qua API

Workflow Server có thể remap ID của Start Event khi POST/PUT nhưng không remap `data.waitActionSlug`. Vì vậy một request nguồn Start có thể được lưu với reference stale dù response trả `isValid: true`.

- Trước POST, `waitActionSlug` vẫn phải bằng Start Event ID trong chính XML request.
- Sau POST, gọi `/bapi/v1/processes/view`, lấy Start Event ID trong XML đã lưu và so sánh với `RESPONSE_WEBHOOK.data.waitActionSlug`.
- Chỉ báo thành công khi hai giá trị bằng nhau. Nếu lệch, process **chưa sẵn sàng để response webhook**.
- Không lặp PUT chỉ để chép ID Start mới vào `waitActionSlug`: server có thể remap Start ID lần nữa và tiếp tục tạo reference stale.
- Với payload legacy, nguồn Wait dùng `waitActionType: "wait"` và `waitActionSlug` bằng action slug của Wait. Đây chỉ là quy tắc đọc/migration: Wait Webhook và Respond to Webhook đều chưa executable trên backend hiện tại, nên không dùng nguồn Wait như một workaround. Nếu nguồn Start của payload cũ bị remap, báo reference stale; không kích hoạt và không tuyên bố runtime-ready.

## Action data

```json
{
  "waitActionSlug": "NOSTART0000001",
  "waitActionType": "start",
  "httpRespondCode": { "type": 1, "value": 200 },
  "respondBodyType": "DEFAULT_DATA",
  "documentSampleSlug": { "type": 1, "value": null },
  "redirectUrl": { "type": 1, "value": null }
}
```

`respondBodyType` nhận:

- `DEFAULT_DATA`: trả dữ liệu mặc định của webhook execution.
- `TEXT_TEMPLATE`: bắt buộc `documentSampleSlug`; dùng type `2` cho Text Template hoặc type `4` cho resource phù hợp.
- `REDIRECT_URL`: cấu hình `redirectUrl` bằng URL raw hoặc resource.

Luôn cấu hình `httpRespondCode`. Dùng cấu trúc resource `{type, value, valueDataType?, valuePathName?}`.

## Output resources

Tạo `responseTime` (`DATE_TIME`), `respondForWebhook` (`TEXT`), `redirectUrl` (`TEXT`) và `output` (`RECORD`). `output` có `statusCode` (`TEXT`) và `respond.body` (`TEXT`). Mọi output đều `availableForInput: false`.

## XML

```xml
<elEx:responseWebhookTask id="NORESPONSE00001" name="Respond to webhook">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="RESPONSE_WEBHOOK_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>FLFLOW00000001</bpmn2:incoming>
  <bpmn2:outgoing>FLFLOW00000002</bpmn2:outgoing>
</elEx:responseWebhookTask>
```

Xem `samples/sample_respond_to_webhook.json`.

Sample này minh họa request nguồn Start trước POST. Do giới hạn remap nói trên, luôn thực hiện hậu kiểm; không coi sample là bằng chứng rằng reference sau lưu chắc chắn còn đúng.
