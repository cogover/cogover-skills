## Wait (Task Chờ)

### Mô tả

Wait Task tạm dừng execution cho tới khi timer runtime hoặc event listener kết thúc chờ. Palette/front-end hiện hiển thị 7 `eventType`, nhưng backend hiện tại không thực thi đầy đủ cả 7:

| `eventType` | Normal Flow runtime hiện tại | Contract executable |
|---|---|---|
| `AFTER_A_PERIOD_OF_TIME` | Hỗ trợ | Bắt buộc `maximumWaitTimeValue` + `maximumWaitTimeUnit`; có thể giữ `eventTime*` cùng giá trị cho editor |
| `AT_A_SPECIFIED_TIME` | Không hỗ trợ | Field được parse nhưng không có scheduler dùng giá trị tuyệt đối; đổi thành duration tương đối nếu nghiệp vụ cho phép |
| `EMAIL_OPEN` | Hỗ trợ | `sendEmailActionNodeId` thật + relative maximum wait |
| `EMAIL_REPLY` | Hỗ trợ | `sendEmailActionNodeId` thật + relative maximum wait |
| `LINK_WAS_CLICKED` | Hỗ trợ | `sendEmailActionNodeId` thật + relative maximum wait |
| `RECEIVE_EVENT_FROM_WEBHOOK` | Không hỗ trợ | Không có Wait webhook handler tương ứng; không tạo cho executable flow |
| `NUMBER_OF_MATCHING_RECORDS` | Không hỗ trợ cho Normal Flow thông thường | Listener cần process-level `objectTypeId`; Normal Flow có trường này rỗng nên event không tìm thấy instance chờ |

`FILE_WAS_DOWNLOADED` vẫn còn trong enum TypeScript nhưng đã bị loại khỏi danh sách lựa chọn trên UI. Không tạo event này cho payload mới nếu chưa xác minh backend/front-end đã bật lại.

### BPMN XML và action wrapper

```xml
<elEx:waitTask id="{WAIT_NODE_ID}" name="{WAIT_NAME}">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="WAIT_TASK" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
  <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
</elEx:waitTask>
```

```json
{
  "id": "{WAIT_NODE_ID}",
  "nodeId": "{WAIT_NODE_ID}",
  "type": "WAIT",
  "name": "{WAIT_NAME}",
  "slug": "{wait_slug}",
  "description": "",
  "processId": "{PROCESS_ID}",
  "data": {}
}
```

Trong create payload, `action.id === action.nodeId ===` ID của `elEx:waitTask`. Không tự sinh ID `AC...` riêng.

### Resource value

`eventTimeValue`, `eventSpecifiedDateTime`, `specifiedDateTime`, `httpRespondCode`, `documentSampleSlug` và `redirectUrl` dùng resource value theo cấu trúc chung:

```json
{ "type": 1, "value": 5 }
```

- `type: 1`: raw value.
- Loại resource khác chỉ dùng khi đã xác minh resource tương thích trên workspace; giữ đúng `value`, `valueDataType` và `valuePathName` mà front-end/API trả về.
- `maximumWaitTimeValue` là số trực tiếp, không bọc trong resource value. `countOfUpdatesConditions` là raw number hoặc absolute slug kèm metadata resource như mô tả ở phần record.
- Đơn vị runtime hợp lệ cho `maximumWaitTimeUnit`: `seconds`, `minutes`, `hours`, `days`. Nếu người dùng nhập tuần, đổi sang số ngày tương ứng; không gửi `weeks`.

### 1. Chờ sau một khoảng thời gian

```json
{
  "eventType": "AFTER_A_PERIOD_OF_TIME",
  "eventTimeValue": { "type": 1, "value": 30 },
  "eventTimeUnit": "minutes",
  "maxWaitTimeType": "AFTER_A_PERIOD_OF_TIME",
  "maximumWaitTimeValue": 30,
  "maximumWaitTimeUnit": "minutes"
}
```

`eventTimeValue`/`eventTimeUnit` là contract editor, còn scheduler runtime hiện đọc `maximumWaitTimeValue`/`maximumWaitTimeUnit`. Giữ hai cặp cùng giá trị để payload hiển thị đúng và thực sự có timer. Test bằng thời lượng ngắn (ví dụ 2 giây) và đo elapsed time của instance: node sau Wait không được chạy trước mốc và phải chạy ngay sau mốc với dung sai hệ thống hợp lý.

### 2. Chờ tới một thời điểm xác định

```json
{
  "eventType": "AT_A_SPECIFIED_TIME",
  "eventSpecifiedDateTime": {
    "type": 1,
    "value": 1787191200000
  }
}
```

Không dùng payload này cho process cần chạy trên backend hiện tại: `eventSpecifiedDateTime` được parse nhưng không được scheduler sử dụng. Nếu nghiệp vụ cho phép, tính `target - now` ở thời điểm tạo cấu hình và dùng `AFTER_A_PERIOD_OF_TIME` với relative maximum timer; nói rõ đây là xấp xỉ, không phải absolute scheduler.

### 3. Chờ sự kiện email

Áp dụng cho `EMAIL_OPEN`, `EMAIL_REPLY` và `LINK_WAS_CLICKED`. Wait phải đặt sau và tham chiếu một Send Email Task thực tế.

```json
{
  "eventType": "EMAIL_REPLY",
  "sendEmailActionNodeId": "{SEND_EMAIL_NODE_ID}",
  "maxWaitTimeType": "AFTER_A_PERIOD_OF_TIME",
  "maximumWaitTimeValue": 3,
  "maximumWaitTimeUnit": "days"
}
```

Front-end hiện chỉ chọn, lưu và validate `sendEmailActionNodeId`. `sendEmailActionName`/`sendEmailActionSlug` có thể xuất hiện trong payload legacy hoặc response nhưng không được coi là field bắt buộc của create payload.

Khi kiểm thử email event, không nối Wait thẳng tới một node có subject/nội dung “triggered”: runtime cũng tiếp tục flow khi maximum wait hết hạn. Đặt Exclusive Gateway ngay sau Wait:

- Nhánh event: `$action.{wait_slug}.isEventTriggered == true` → notification/email mang token `EVENT_PASS`.
- Nhánh default timeout: notification/email mang token `TIMEOUT`.

UI Debug có thể không render trực tiếp `isEventTriggered`; gateway Debug và nhánh thực thi là bằng chứng phân biệt event thật với timeout. Chỉ đánh PASS event khi nhánh `EVENT_PASS` chạy trước maximum wait.

### 4. Chờ số bản ghi thỏa điều kiện (không dùng cho Normal Flow hiện tại)

```json
{
  "eventType": "NUMBER_OF_MATCHING_RECORDS",
  "objectTypeId": "{VERIFIED_OBJECT_TYPE_ID}",
  "filter": {
    "logic": "",
    "logicType": "AND",
    "conditions": [],
    "sortFields": []
  },
  "breakFilter": {
    "logic": "",
    "logicType": "AND",
    "conditions": [
      {
        "field": "{VERIFIED_FIELD_SLUG}",
        "fieldType": "short_text",
        "op": "=",
        "params": "{BREAK_VALUE}",
        "isRaw": true
      }
    ],
    "sortFields": []
  },
  "countCompare": ">=",
  "countOfUpdatesConditions": 5,
  "updatedFields": ["status"],
  "maxWaitTimeType": "AT_A_SPECIFIED_TIME",
  "specifiedDateTime": {
    "type": 1,
    "value": 1788170400000
  }
}
```

- `countCompare`: `=`, `>=` hoặc `<=`.
- `filter.conditions` có thể rỗng; `breakFilter.conditions` phải có ít nhất một điều kiện đầy đủ theo validation front-end.
- `countOfUpdatesConditions` nhận raw number hoặc absolute slug của resource NUMBER. Khi dùng resource, gửi bộ ba sau (không bọc trong `{ type, value }`):

```json
{
  "countOfUpdatesConditions": "$flow.target_count",
  "countOfUpdatesConditionsPathName": "Flow / Target count",
  "countOfUpdatesConditionsDataType": "NUMBER"
}
```

- Condition dùng keys `field`, `fieldType`, `op`, `params`. Với RHS là resource, đặt `isRaw: false` và gửi thêm `resourceSlug`, `resourcePathName`, `resourceDataType`; không dùng keys legacy `fieldName`/`operator`/`value`.
- Raw DATE_TIME trong `eventSpecifiedDateTime.value` và `specifiedDateTime.value` là Unix epoch milliseconds. Nếu dùng resource DATE_TIME, dùng `type: 4`, absolute slug, `valueDataType: "DATE_TIME"` và `valuePathName`.
- `updatedFields` là danh sách field slug cần theo dõi, có thể rỗng nếu điều kiện không giới hạn theo field cập nhật.
- Lấy `objectTypeId` và field metadata thật từ API; không tái sử dụng ID trong sample.
- Runtime listener còn yêu cầu `process.objectTypeId` ở cấp process và process đang `ACTIVATED`. Normal Flow thông thường lưu `objectTypeId: null`, vì vậy listener return trước khi query waiting instance. Không tạo case này trong Normal Flow executable. Chỉ thử lại trên workflow type có object cấp process sau khi GET-back xác nhận `objectTypeId` không rỗng.

### 5. Chờ webhook (schema-only trên backend hiện tại)

```json
{
  "eventType": "RECEIVE_EVENT_FROM_WEBHOOK",
  "verifySignature": true,
  "httpMethod": "POST",
  "sampleData": "{\"orderId\":\"A-100\"}",
  "parseToDataType": {
    "nameDataType": "input",
    "children": []
  },
  "respondTiming": "IMMEDIATELY",
  "httpRespondCode": { "type": 1, "value": 200 },
  "respondBodyType": "DEFAULT_DATA",
  "maxWaitTimeType": "AFTER_A_PERIOD_OF_TIME",
  "maximumWaitTimeValue": 1,
  "maximumWaitTimeUnit": "days"
}
```

- `httpMethod` hiện là `POST`.
- `webhookUrl` và `secretKey` là giá trị do server cấp. Không bịa, không sao chép credential từ sample và không log secret; sau create phải GET-back để lấy URL/secret nếu cần hiển thị cho người dùng.
- `sampleData` là JSON string dùng để sinh schema; `parseToDataType.children` mô tả body input tương tự Webhook Trigger.
- `respondTiming`: `IMMEDIATELY`, `WHEN_EXECUTION_COMPLETED` hoặc `USE_RESPOND_TO_WEBHOOK`.
- Khi `respondTiming = USE_RESPOND_TO_WEBHOOK`, không gửi `respondBodyType`, `httpRespondCode`, `documentSampleSlug` hoặc `redirectUrl`; phải có một Respond to Webhook Task tham chiếu Wait này.
- Với hai timing còn lại, gửi `httpRespondCode` và `respondBodyType`:
  - `DEFAULT_DATA`: không cần field body bổ sung.
  - `TEXT_TEMPLATE`: bắt buộc `documentSampleSlug`, ví dụ `{ "type": 2, "value": "$flow.template_slug" }`.
  - `REDIRECT_URL`: gửi `redirectUrl` resource value; status mặc định trên UI là 304 nhưng vẫn phải dùng mã phù hợp với luồng.

Backend hiện tại không có handler nhận webhook để giải phóng Wait; endpoint lấy từ resource có thể trả 405. Không tạo event này cho process executable và không kết hợp với Respond to Webhook để né giới hạn.

### Maximum wait cho các event không thuần thời gian

Email events cấu hình giới hạn chờ bằng relative timer:

| `maxWaitTimeType` | Field bắt buộc |
|---|---|
| `AFTER_A_PERIOD_OF_TIME` | `maximumWaitTimeValue` (>= 1) và `maximumWaitTimeUnit` (`seconds`/`minutes`/`hours`/`days`) |
| `AT_A_SPECIFIED_TIME` | Không dùng trên backend hiện tại; `specifiedDateTime` chưa được scheduler đọc |

Không trộn field của hai mode. Riêng time event `AFTER_A_PERIOD_OF_TIME`, vẫn gửi relative maximum fields vì đó là các field scheduler runtime thực sự đọc.

### Validation checklist

- `name`: bắt buộc, 2–250 ký tự và duy nhất trong actions.
- `slug`: theo quy tắc slug chung của skill và duy nhất trong actions.
- `eventType`: chỉ chọn một event được đánh dấu hỗ trợ runtime trong bảng đầu file khi process phải chạy.
- Chỉ gửi nhóm field tương ứng với event và maximum-wait mode đã chọn.
- Event email phải có `sendEmailActionNodeId` của Send Email node; các event khác không gửi `sendEmailAction*`.
- Không tạo Record Wait cho Normal Flow nếu GET-back process-level `objectTypeId` rỗng.
- Không tạo Wait Webhook hoặc absolute-time Wait cho executable flow trên backend hiện tại.

### Resources của Wait Task

Mọi Wait Task có 3 output chuẩn:

| Resource | `dataType` | Absolute slug |
|---|---|---|
| Start At | `DATE_TIME` | `$action.{wait_slug}.startAt` |
| End At | `DATE_TIME` | `$action.{wait_slug}.endAt` |
| Is Event Triggered | `BOOLEAN` | `$action.{wait_slug}.isEventTriggered` |

Khi `eventType = RECEIVE_EVENT_FROM_WEBHOOK`, front-end còn tạo:

- `$action.{wait_slug}.webhookUrl` (`TEXT`).
- `$action.{wait_slug}.input` (`RECORD`) với `headers` và `body`; children của `body` theo `parseToDataType.children`.
- `$action.{wait_slug}.output` (`RECORD`) với `statusCode` và `respond.body`.

Các resource phải dùng `parentTable: "action"`, `nodeId` của Wait và metadata/date-time mặc định nhất quán với các action resource khác.
