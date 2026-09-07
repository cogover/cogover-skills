---
name: process-creator
description: Thiết kế, tạo, kích hoạt, chạy thử và xác minh JSON BPMN cho Cogover Process, gồm Manual, Normal, Scheduled, Triggered và Sequence Flow cùng các task (gồm AI Agent), gateway, event, resource và quyền liên quan. Dùng khi người dùng muốn tạo, sửa, kiểm tra, triển khai hoặc đánh giá end-to-end một Cogover workflow/process.
metadata:
  author: cogover
  version: "1.2.2"
---

# Cogover Process Creator

- **Phiên bản:** `1.2.2`
- **Ngày phát hành:** `2026-09-07`

## Kích hoạt

Trước khi dùng JSON mẫu, đọc [quy ước fixture và giới hạn kiểm thử](samples/README.md). Resolve ID và tài nguyên của Workspace đích; không coi snapshot response hoặc metadata kiểm tra cũ là kết quả validation cho lần triển khai mới.
- Lệnh: `/cogover-process-creator`
- Người dùng có thể gọi: có

## Mô tả
Kỹ năng này tạo các file JSON quy trình BPMN cho hệ thống workflow Cogover. Nó tạo cấu trúc JSON hoàn chỉnh bao gồm BPMN XML, userTasks, gateWays, resources và tất cả metadata cần thiết.

## Quy tắc an toàn
- **Xoá quy trình (DELETE):** PHẢI hỏi xác nhận người dùng trước khi gọi API xoá. KHÔNG BAO GIỜ tự ý xoá quy trình mà không có sự đồng ý rõ ràng từ người dùng.

## Các loại quy trình và cách chọn loại quy trình

Hệ thống hỗ trợ 5 loại quy trình. Khi người dùng mô tả nhu cầu, hãy xác định loại phù hợp dựa trên cách quy trình được kích hoạt.

### 1. Manual Flow (`manual_flow`) - Quy trình thông thường
- **Kích hoạt bởi:** Người dùng submit một form (màn hình), ví dụ: form "Đề nghị mua sắm", "Xin nghỉ phép"
- **Đặc điểm:** User Task đầu tiên ngay sau Node Start chính là form mà người dùng cần submit để kích hoạt quy trình
- **Start Event renderKey:** `START_MANUAL_EVENT`
- **`metadata`:** `{}`
- **`permissions`:** `["VIEW", "ADD", "EDIT", "DELETE", "START_INSTANCE"]`
- **`processInstanceAccessControls` functions:** `["START_INSTANCE"]`
- **System resources đặc biệt:** Không có (chỉ có `$client`, `$currentUser`, `$flow.instance`)
- **File mẫu:** `samples/sample_process_1.json`, `samples/sample_process_2.json`

### 2. Normal Flow (`normal_flow`) - Quy trình không có Root form, thường được gọi từ bên ngoài
- **Cách dùng phổ biến:** Process cha gọi qua node **Sub Process**, hoặc một module khác gọi để thực hiện các bước xử lý. Ví dụ: module SLA phát hiện vi phạm rồi gọi Normal Flow để tạo cảnh báo, gửi email hoặc thông báo cho quản lý.
- **Chạy độc lập:** Hiếm khi dùng như một process độc lập, nhưng người có quyền `START_INSTANCE` vẫn có thể chủ động chạy. Không mặc định thiết kế Normal Flow quanh thao tác người dùng bấm chạy khi bên gọi dự kiến là process cha/module khác.
- **Đặc điểm:** Không tạo Root User Task bắt buộc; Start có thể nối trực tiếp tới action, gateway hoặc End Process
- **Start Event renderKey:** `START_NORMAL_EVENT`
- **`metadata`:** `{}`
- **`permissions`:** `VIEW`, `ADD`, `EDIT`, `DELETE`, `START_INSTANCE` và các quyền participant được người dùng chọn
- **`processInstanceAccessControls` functions:** Bao gồm `START_INSTANCE` cho các actor được phép chạy
- **System resources đặc biệt:** Không có (dùng resource base tiêu chuẩn)
- **Chi tiết:** `nodes/normal-flow.md`
- **File mẫu:** `samples/sample_normal_flow.json`

### 3. Scheduled Flow (`scheduled_flow`) - Quy trình tự động theo thời gian
- **Kích hoạt bởi:** Lịch trình định kỳ hoặc N lần quy định, vào khoảng thời gian trong ngày/tuần/tháng/năm
- **Đặc điểm:** Quy trình tự khởi chạy theo cron schedule, không cần người dùng thao tác
- **Start Event renderKey:** `START_SCHEDULED_EVENT`
- **`metadata`:** Chứa `scheduleRules` với cấu hình lịch trình

  **Cấu trúc chung của `scheduleRules`:**
  ```json
  {
    "metadata": {
      "scheduleRules": [
        {
          "triggerInterval": {
            "type": "SECONDS | MINUTES | HOURS | DAYS | WEEKS | MONTHS | YEARS | CRON",
            "between": 1,
            "atHour": 9,
            "atMinute": 0,
            "atSecond": 0
          },
          "start": null,
          "end": null,
          "maxRun": 0,
          "id": "SR...",
          "maxRunTypeFE": "UNLIMITED"
        }
      ]
    }
  }
  ```

  **Giải thích các trường:**
  - `triggerInterval.type`: loại chu kỳ — `"SECONDS"`, `"MINUTES"`, `"HOURS"`, `"DAYS"`, `"WEEKS"`, `"MONTHS"`, `"YEARS"`, `"CRON"`
  - `triggerInterval.between`: khoảng cách giữa các lần chạy (ví dụ: `2` với type `"WEEKS"` = mỗi 2 tuần)
  - `triggerInterval.atHour` / `atMinute` / `atSecond`: thời điểm chạy dạng số
  - `triggerInterval.daysOfWeek`: mảng số thứ tự ngày trong tuần (chỉ dùng khi type = `"WEEKS"`). Giá trị: `1` = Chủ nhật, `2` = Thứ 2, `3` = Thứ 3, `4` = Thứ 4, `5` = Thứ 5, `6` = Thứ 6, `7` = Thứ 7
  - `triggerInterval.daysOfMonth`: mảng chuỗi ngày trong tháng (chỉ dùng khi type = `"MONTHS"`). Ví dụ: `["1", "6"]` = ngày 1 và ngày 6
  - `start` / `end`: timestamp (milliseconds) khoảng thời gian hiệu lực của lịch trình. Nếu người dùng không chỉ định thời điểm bắt đầu/kết thúc, để giá trị `null`
  - `maxRun`: số lần chạy tối đa (`0` = không giới hạn)
  - `maxRunTypeFE`: `"UNLIMITED"` hoặc `"CUSTOM"`; không dùng `"LIMITED"`
  - `id`: ID duy nhất của schedule rule, prefix `SR` và suffix chữ-số
  - `triggerInterval.atDays`: mảng `{ "month": 1..12, "dayOfMonth": "..." }` khi type = `"YEARS"`
  - `triggerInterval.cronExpression`: biểu thức Quartz cron khi type = `"CRON"`; không dùng `between`
  - Với `"MONTHS"`, chọn ngày tuyệt đối bằng `daysOfMonth` hoặc ngày tương đối bằng `daysOfWeek[].dayOfWeek` + `daysOfWeek[].nth`

  **Ví dụ theo từng loại chu kỳ:**

  **a) Theo giờ (`HOURS`)** — Lặp lại mỗi 5 giờ, vào phút 11:
  ```json
  {
    "triggerInterval": {
      "atMinute": 11,
      "atSecond": 0,
      "type": "HOURS",
      "between": 5
    },
    "start": null,
    "end": null,
    "maxRun": 0,
    "id": "SR000000001",
    "maxRunTypeFE": "UNLIMITED"
  }
  ```

  **b) Theo ngày (`DAYS`)** — Lặp lại mỗi 1 ngày, lúc 09:00:00:
  ```json
  {
    "triggerInterval": {
      "atMinute": 0,
      "atSecond": 0,
      "type": "DAYS",
      "atHour": 9,
      "between": 1
    },
    "start": null,
    "end": null,
    "maxRun": 0,
    "id": "SR000000002",
    "maxRunTypeFE": "UNLIMITED"
  }
  ```

  **c) Theo tuần (`WEEKS`)** — Lặp lại mỗi 2 tuần, vào Thứ 2, Thứ 3, Thứ 4, lúc 10:00:00:
  ```json
  {
    "triggerInterval": {
      "atMinute": 0,
      "atSecond": 0,
      "type": "WEEKS",
      "daysOfWeek": [2, 3, 4],
      "atHour": 10,
      "between": 2
    },
    "start": null,
    "end": null,
    "maxRun": 0,
    "id": "SR000000003",
    "maxRunTypeFE": "UNLIMITED"
  }
  ```
  > `daysOfWeek`: `1` = CN, `2` = T2, `3` = T3, `4` = T4, `5` = T5, `6` = T6, `7` = T7

  **d) Theo tháng (`MONTHS`)** — Lặp lại mỗi 1 tháng, vào Ngày 1 và Ngày 6, lúc 08:45:00:
  ```json
  {
    "triggerInterval": {
      "atMinute": 45,
      "atSecond": 0,
      "daysOfMonth": ["1", "6"],
      "type": "MONTHS",
      "atHour": 8,
      "between": 1,
      "daysOfWeek": []
    },
    "start": null,
    "end": null,
    "maxRun": 0,
    "id": "SR000000004",
    "maxRunTypeFE": "UNLIMITED"
  }
  ```
  > `daysOfMonth` là mảng chuỗi. Khi type = `"MONTHS"`, `daysOfWeek` để rỗng `[]`.

  **Các chu kỳ bổ sung:**
  - `SECONDS`: cần `between`
  - `MINUTES`: cần `between`
  - `YEARS`: cần `between`, `atDays`, `atHour`, `atMinute`, `atSecond`
  - `CRON`: cần `cronExpression`; không cần `between`

  **Chi tiết và payload canonical:** đọc `nodes/scheduled-start-event.md`. Các field `temporaryExecutionHours` và `temporaryExecutionMinutes` chỉ phục vụ form front-end, không đưa vào payload.

- **`permissions`:** `["VIEW", "ADD", "EDIT", "DELETE", "VIEW_INSTANCE_PROGRESS", "VIEW_INSTANCE_FULL", "CANCEL_INSTANCE", "DELETE_INSTANCE", "DO_EVERY_TASK_IN_SEQUENCE", "ASSIGN_TASK"]`
- **`processInstanceAccessControls` functions:** `["CANCEL_INSTANCE", "DELETE_INSTANCE", "VIEW_INSTANCE_PROGRESS", "VIEW_INSTANCE_FULL", "DO_EVERY_TASK_IN_SEQUENCE", "ASSIGN_TASK"]`
- **System resources đặc biệt:** Không có (chỉ có `$client`, `$currentUser`, `$flow.instance`)
- **File mẫu:** `samples/sample_scheduled_flow_1.json`

### 4. Triggered Flow (`triggered_flow`) - Quy trình tự động theo điều kiện
- **Kích hoạt bởi:** Một điều kiện được thỏa mãn: bản ghi được tạo/cập nhật/xóa, hoặc app nhận HTTP request đến URL webhook của quy trình
- **Đặc điểm:** Quy trình tự khởi chạy khi sự kiện trigger xảy ra
- **Start Event renderKey:** `START_TRIGGERED_EVENT`
- **`metadata`:** Chứa cấu hình trigger:
  ```json
  {
    "metadata": {
      "logicType": "AND",
      "applyConditionsForRecords": true,
      "trigger": 1,
      "triggerConditions": 1,
      "logic": "",
      "runFlowWhenRecordsAreUpdatedStrategy": 1,
      "type": "record",
      "conditions": [],
      "onObjectFieldUpdateOption": 1,
      "triggeredUpdateFields": [],
      "object": "OT00000000011",
      "name": "Start"
    }
  }
  ```
  - `type`: `"record"` (trigger khi bản ghi thay đổi) hoặc `"webhook"` (trigger khi nhận HTTP request). Xem chi tiết từng loại bên dưới.

  #### 4a. Triggered Flow loại `"record"` — Trigger khi bản ghi thay đổi

  Khi `type` = `"record"`, quy trình khởi chạy khi bản ghi của một Object Type được tạo/cập nhật/xóa.

  **Chi tiết đầy đủ:** Xem file `nodes/record-triggered-flow.md` — bao gồm giải thích các trường metadata (`trigger`, `object`, `triggerConditions`, `onObjectFieldUpdateOption`, `conditions`, `logicType`, ...), 8 ví dụ JSON, và bảng điều kiện lọc.

  **Tóm tắt metadata record:**
  ```json
  {
    "metadata": {
      "type": "record",
      "trigger": 1,
      "object": "<objectTypeId từ skill /object-info>",
      "conditions": [],
      "logicType": "AND",
      "logic": "",
      "applyConditionsForRecords": true,
      "triggerConditions": 1,
      "onObjectFieldUpdateOption": 1,
      "triggeredUpdateFields": [],
      "runFlowWhenRecordsAreUpdatedStrategy": 1,
      "name": "Start"
    }
  }
  ```

  **Lưu ý quan trọng:**
  - `trigger`: `1` = tạo, `2` = cập nhật, `3` = tạo hoặc cập nhật, `4` = xóa
  - `object`: **BẮT BUỘC** lấy từ skill `/object-info`
  - `triggerConditions`: `1` khi `trigger` = `1` hoặc `4`. `3` khi `trigger` = `2` hoặc `3`
  - Điều kiện lọc (`conditions`): xem `records_filter_conditions.md`
  - System resources: có thêm `$flow.input.oldRecord` và `$flow.input.newRecord`
  - **File mẫu:** `samples/sample_triggered_flow.json`

  ---

  #### 4b. Triggered Flow loại `"webhook"` — Trigger khi nhận HTTP request

  Khi `type` = `"webhook"`, quy trình sẽ khởi chạy khi hệ thống nhận được HTTP POST request đến URL webhook. Dữ liệu trong body request được parse thành các biến `$flow.input.*` theo cấu hình `parseToDataType`.

  **Chi tiết đầy đủ:** Xem file `nodes/webhook-triggered-flow.md` — bao gồm cấu trúc metadata, giải thích các trường (`sampleData`, `parseToDataType`, `respondTiming`, `verifySignature`, ...), ví dụ JSON cho từng kiểu dữ liệu (TEXT, NUMBER, RECORD/mảng, DATE, DATE_TIME, FILE, URL), bảng tổng hợp `transformationType`, và system resources.

  **Tóm tắt metadata webhook:**
  ```json
  {
    "metadata": {
      "type": "webhook",
      "sampleData": "<chuỗi JSON mẫu của body request>",
      "dataTypeSlug": "TriggeredHookData_<ID tự sinh>__input",
      "respondTiming": "IMMEDIATELY",
      "respondBodyType": "DEFAULT_DATA",
      "httpRespondCode": { "type": 1, "value": 200 },
      "verifySignature": true,
      "authType": "bearer",
      "isAutoGenerate": true,
      "verifySignatureAllVersions": true,
      "authTypeAllVersions": "bearer",
      "isAutoGenerateAllVersions": true,
      "parseToDataType": {
        "nameDataType": "input",
        "children": [...]
      }
    }
  }
  ```

  **Lưu ý quan trọng:**
  - `authType` và `authTypeAllVersions` nhận `"bearer"`, `"apiKey"` hoặc `"basic"`
  - Với Bearer/API Key: đặt `isAutoGenerate: true` để server sinh secret; nếu `false`, phải truyền secret do người dùng cung cấp. Áp dụng tương tự cho bộ field `*AllVersions`
  - Với Basic Authentication: bắt buộc truyền `basicUsername`/`basicPassword`; bộ tất cả phiên bản dùng `basicUsernameAllVersions`/`basicPasswordAllVersions`
  - `url`/`urlAllVersions` và webhook ID do server tự sinh. Không sao chép URL hoặc secret từ response/sample sang create payload
  - Khi response body dùng Text Template, field canonical là `documentSampleSlug` dạng `{ "type": 2, "value": "$flow..." }`, không dùng `documentSampleId`
  - Webhook flow **KHÔNG** có `$flow.input.oldRecord`/`$flow.input.newRecord`, thay vào đó `$flow.input` chứa trực tiếp các trường từ body request
  - **File mẫu:** `samples/Webhook_triggered_flow.json`

  ---

  #### Tổng kết Triggered Flow — Chọn loại record hay webhook

  | Câu hỏi | Loại |
  |---|---|
  | Quy trình chạy khi bản ghi thay đổi (tạo/sửa/xóa)? | `type: "record"` |
  | Quy trình chạy khi nhận HTTP POST từ bên ngoài? | `type: "webhook"` |

- **`permissions`:** `["VIEW", "ADD", "EDIT", "DELETE", "VIEW_INSTANCE_PROGRESS", "VIEW_INSTANCE_FULL", "CANCEL_INSTANCE", "DELETE_INSTANCE", "DO_EVERY_TASK_IN_SEQUENCE", "ASSIGN_TASK"]`
- **`processInstanceAccessControls` functions:** `["CANCEL_INSTANCE", "DELETE_INSTANCE", "VIEW_INSTANCE_PROGRESS", "VIEW_INSTANCE_FULL", "DO_EVERY_TASK_IN_SEQUENCE", "ASSIGN_TASK"]`
- **File mẫu:** `samples/sample_triggered_flow.json` (record), `samples/Webhook_triggered_flow.json` (webhook)

### 5. Sequence Flow (`sequence_flow`) - Chuỗi hành động
- **Kích hoạt bởi:** Người dùng liên kết (connect) quy trình với một bản ghi của một đối tượng nhất định
- **Đặc điểm:** Người dùng chủ động chọn bản ghi để liên kết với quy trình, ví dụ liên kết một Lead với quy trình
- **Start Event renderKey:** `START_SEQUENCE_EVENT`
- **`metadata`:** Chứa thông tin object type được liên kết — `objectTypeId` và `objectTypeSlug` **BẮT BUỘC** lấy từ skill `/object-info` (xem mục 25 trong Lưu ý quan trọng):
  ```json
  {
    "metadata": {
      "objectTypeId": "OT00000000011",
      "objectTypeSlug": "lead"
    }
  }
  ```
- **`permissions`:** `["VIEW", "ADD", "EDIT", "DELETE", "CANCEL_INSTANCE", "CONNECT_SEQUENCE", "DO_EVERY_TASK_IN_SEQUENCE", "ASSIGN_TASK"]`
- **`processInstanceAccessControls` functions:** `["CONNECT_SEQUENCE", "CANCEL_INSTANCE", "DO_EVERY_TASK_IN_SEQUENCE", "ASSIGN_TASK"]`
- **`participantPermission`:** `ANY_PERFORMER_CAN_VIEW_PROGRESS_OF_SEQUENCE: true`, `ANY_PERFORMER_CAN_REASSIGN_TASK: true`
- **System resources đặc biệt:** Có thêm:
  - `$flow.input` (id: `SEQUENCE_INPUT`) với child `$flow.input.record` (id: `RECORD_DATA`) — bản ghi được liên kết
  - `$flow.instance.starter` — người khởi tạo quy trình
- **File mẫu:** `samples/sample_sequence_flow.json`

### Cách chọn loại quy trình

| Câu hỏi                                                | Loại quy trình     |
|--------------------------------------------------------|--------------------|
| Người dùng cần điền form để khởi tạo?                  | **Manual Flow**    |
| Cần quy trình để process cha gọi qua Sub Process hoặc module khác gọi, không cần Root form? | **Normal Flow** — cách dùng phổ biến |
| Người dùng chạy process trực tiếp, không cần Root form? | **Normal Flow** — vẫn hỗ trợ, nhưng ít dùng độc lập |
| Quy trình chạy định kỳ theo lịch?                      | **Scheduled Flow** |
| Quy trình chạy khi bản ghi thay đổi?                   | **Triggered Flow** (`type: "record"`) |
| Quy trình chạy khi nhận HTTP POST từ bên ngoài?        | **Triggered Flow** (`type: "webhook"`) |
| Người dùng liên kết bản ghi với quy trình?             | **Sequence Flow**  |

---

## Hướng dẫn

Khi người dùng kích hoạt kỹ năng này, thực hiện các bước sau:

### Bước 0: Xác định Workspace Domain

**Hỏi khách hàng WORKSPACE_DOMAIN** trước khi bắt đầu. Đây là domain workspace của khách hàng, có dạng:
- `tenant-a.example.com`
- `tenant-b.example.org`
- `company.example.com`

WORKSPACE_DOMAIN sẽ được dùng làm base URL cho tất cả các API call trong suốt quy trình:
- Lấy thông tin đối tượng: sử dụng skill `/object-info`
- Thao tác bản ghi: sử dụng skill `/object-record`
- Gọi API tạo quy trình (api-process-builder.md): `https://{WORKSPACE_DOMAIN}/bapi/v1/processes`
- Trả link kết quả: `https://{WORKSPACE_DOMAIN}/settings/processes/{id}/{processInfoId}`

**Lưu ý:** Khi gọi API, sử dụng flag bỏ qua lỗi SSL self-signed certificate (ví dụ: `curl -k` hoặc `--insecure`, hoặc `NODE_TLS_REJECT_UNAUTHORIZED=0` nếu dùng Node.js).

### Bước 1: Thu thập thông tin và xác nhận luồng quy trình

**QUAN TRỌNG: KHÔNG tạo JSON ngay. Phải xác nhận với khách hàng trước khi sang Bước 2.**

Hỏi người dùng các thông tin sau:
1. **Tên quy trình** (ví dụ: "Quy trình xin nghỉ phép")
2. **Slug quy trình** (tự động tạo từ tên nếu không cung cấp, ví dụ: `quy_trinh_xin_nghi_phep`). Slug phải dài ít nhất 2 ký tự, bắt đầu bằng chữ cái, chỉ chứa chữ Latin/chữ số/`_`, không có `__` và không kết thúc bằng `_`.
3. **Loại quy trình:** `manual_flow`, `normal_flow`, `scheduled_flow`, `triggered_flow` hoặc `sequence_flow`
   - Với Scheduled Flow: hỏi chu kỳ trong 8 loại `SECONDS`, `MINUTES`, `HOURS`, `DAYS`, `WEEKS`, `MONTHS`, `YEARS`, `CRON`; các field theo chu kỳ; thời gian hiệu lực; và `UNLIMITED` hay `CUSTOM`
   - Với Triggered Webhook: hỏi xác thực cho version hiện tại và tất cả version (`bearer`, `apiKey`, `basic`), auto-generate secret hay nhập tay, response timing/body/status và input sample/schema
4. **Danh sách các node** theo thứ tự từ Bắt đầu đến Kết thúc
   - Chỉ Manual Flow bắt buộc node đầu tiên sau Start là "Root" (`isRoot: true`)
   - Normal/Scheduled/Triggered/Sequence có thể nối Start trực tiếp tới action, gateway hoặc End Process
   - Phân biệt rõ End Branch và End Process ở từng nhánh
5. **Có sử dụng Gateway không?** Nếu có, hỏi thêm:
   - Loại Gateway (Exclusive Gateway, Parallel Gateway, etc.)
   - Các nhánh và điều kiện cho mỗi nhánh
6. **Có sử dụng Loop không?** Nếu có, hỏi thêm:
   - Danh sách duyệt (ví dụ: trường lookup nhiều giá trị trong userTask trước đó)
   - Hướng duyệt (1: từ bản ghi đầu đến cuối, 2: từ bản ghi cuối đến đầu)
   - Các task xử lý trong vòng lặp (nhánh "For each item")
7. **Có sử dụng Variable (Biến) không?** Nếu có, hỏi thêm:
   - Tên biến và slug
   - Kiểu dữ liệu: TEXT, NUMBER, BOOLEAN, DATE, DATE_TIME, RECORD
   - Đơn giá trị hay nhiều giá trị (isList: false/true)
   - Giá trị mặc định (nếu có): có thể là giá trị tĩnh hoặc tham chiếu đến biến/resource khác (ví dụ: `$userTask.Root.so_a`)
   - Có cho phép nhập khi bắt đầu quy trình không (availableForInput)
   - Có cho phép xuất kết quả không (availableForOutput)
   - Nếu kiểu RECORD: object type slug và object type ID để tra cứu
8. **Có sử dụng Assignment (Gán biến) không?** Nếu có, hỏi thêm:
   - Tên task assignment và slug
   - Danh sách các phép gán: biến đích, giá trị nguồn, toán tử (=, +=, -=, count)
9. **Có sử dụng Organization (Tổ chức) không?** Nếu có, hỏi thêm:
   - Tên task organization và slug
   - Loại lọc (filterType): quản lý (`"manager"`), nhân sự cùng phòng (`"personnel"`), phòng ban (`"department"`), hay vị trí công việc (`"position"`)
   - Nhân sự đầu vào: tham chiếu biến (ví dụ: `$userTask.Root.submittedBy`) hoặc ID nhân sự cụ thể
   - Nếu filterType là `"manager"`: phép so sánh cấp bậc (`gte`/`equals`) và giá trị cấp bậc
   - Trường cần lưu từ kết quả (ví dụ: `account_email`) và biến đích
   - Lưu giá trị đầu tiên (`FIELD_OF_FIRST_RECORD`) hay tất cả (`FIELD_OF_LIST_RECORDS`)
10. **Có sử dụng Wait (Chờ) không?** Nếu có, hỏi thêm:
   - Event: sau một khoảng thời gian hoặc email open/reply/link click. Đọc `nodes/wait-task.md` trước khi đề xuất event khác vì backend hiện tại không thực thi mọi lựa chọn đang hiện trên UI.
   - Với time event: khoảng thời gian và đơn vị (`seconds`/`minutes`/`hours`/`days`); runtime timer bắt buộc nhóm `maximumWaitTimeValue` + `maximumWaitTimeUnit`.
   - Với email event: Send Email Task nguồn và maximum wait theo khoảng thời gian.
11. **Có sử dụng Sub Process (Gọi quy trình con) không?** Nếu có, hỏi thêm:
    - **Process Info ID** của quy trình con (format `PI` + ký tự, ví dụ: `PI00000000020`) — **BẮT BUỘC** phải là ID thực tế của quy trình con đã tồn tại trong hệ thống
    - **Process ID** (subWorkflowId) của quy trình con (format `PE` + ký tự, ví dụ: `PE00000000024`) — **BẮT BUỘC** phải là ID thực tế, **KHÔNG ĐƯỢC** tự sinh hoặc suy ra từ processInfoId. Đây là 2 ID độc lập, cần hỏi người dùng cung cấp cả hai
    - Loại quy trình con: `manual_flow`, `normal_flow`, `sequence_flow`, `triggered_flow`, `scheduled_flow` (ảnh hưởng đến các field bắt buộc)
    - Danh sách biến cần truyền vào quy trình con (input): tên biến ở quy trình con, kiểu dữ liệu, giá trị từ quy trình cha
    - Danh sách biến cần nhận về từ quy trình con (output): tên biến ở quy trình con, biến ở quy trình cha sẽ nhận giá trị
    - Đồng bộ hay bất đồng bộ (`async`: false/true)
12. **Có sử dụng Formula / Scripting (Công thức tính) không?** Nếu có, hỏi thêm:
    - Tên formula và slug
    - Kiểu dữ liệu trả về: TEXT, NUMBER, BOOLEAN, DATE, DATE_TIME
    - Nội dung code (Cogover Scripting / Apache JEXL) — tham khảo `FORMULA_API_REFERENCE-VI.md`
    - Các resource/biến được tham chiếu trong code (ví dụ: `$userTask.Root.text_1`, `$userTask.Root.submittedBy.account_email`)
    - Formula sẽ được dùng ở đâu (ví dụ: làm body cho Send HTTP Request, giá trị cho Assignment, ...)
13. **Có sử dụng To Do không?** Chỉ cho Sequence Flow; hỏi assignee, title/content, priority, due date, reminder và maximum wait time
14. **Có sử dụng Phone Call không?** Hỏi hotline, số nhận, recording/TTS và automatic/manual nếu là Sequence Flow
15. **Có sử dụng Export Record không?** Hỏi object, record ID và document template thực tế. Dùng `$document-template` để list/detail hoặc tạo template, rồi lấy ID đã verify; không đoán ID và không dùng Object Type ID làm `templateId`
16. **Có sử dụng Respond to Webhook không?** Báo node này chưa có runtime action trên backend hiện tại; chỉ thu thập schema khi người dùng đang migrate/đọc payload cũ, không tạo executable flow
17. **Có sử dụng Push Message không?** Hỏi push type, recipient type và các field theo mode
18. **Có sử dụng JSON to Object không?** Báo node này chưa có runtime action trên backend hiện tại; chỉ thu thập schema khi người dùng đang migrate/đọc payload cũ, không tạo executable flow
19. **Có sử dụng Omni Message không?** Hỏi recipient, các Zalo/WhatsApp method theo order, timeout và success criteria
20. **Nhánh nào dùng End Branch?** Chỉ dùng khi muốn kết thúc nhánh hiện tại; dùng End Process để kết thúc toàn process
21. **Có sử dụng AI Agent không?** Đọc `nodes/ai-agent-task.md`; xác định agent đang hoạt động trong Workspace, instruction và nguồn ngữ cảnh, phiên mới/nối tiếp, cấu trúc kết quả, danh tính chạy, chính sách tool, timeout, số vòng tối đa và nhánh xử lý lỗi. Kiểm tra phiên bản Process API/editor hỗ trợ node trước khi lưu; không tự suy ra agent ID hoặc bật `AUTO_APPROVE` khi chưa nằm trong phạm vi người dùng yêu cầu.

**Sau khi thu thập đủ thông tin, trình bày lại luồng quy trình chi tiết cho khách hàng xác nhận:**
- Tóm tắt loại quy trình, tên, các bước/node, gateway, loop, variable, action...
- Hỏi khách hàng: "Luồng quy trình trên đã đúng chưa? Bạn muốn điều chỉnh gì không?"
- **CHỈ khi khách hàng đồng ý/xác nhận mới chuyển sang Bước 2.**
- Nếu khách hàng muốn sửa, điều chỉnh lại và hỏi xác nhận lần nữa.

### Bước 2: Tạo cấu trúc JSON

Sử dụng các template và quy tắc sau:

#### Quy tắc slug bắt buộc

- Mọi `slug` **người dùng có thể chỉnh trên front-end** do skill này tạo phải dài ít nhất 2 ký tự và khớp regex `^[A-Za-z](?!.*__)[A-Za-z0-9_]*[^_]$`: bắt đầu bằng chữ cái, chỉ chứa chữ Latin/chữ số/`_`, không có `__`, không kết thúc bằng `_`. Áp dụng cho process, User Task, action, gateway, loop, variable/formula/text template/resource, field/component và layout node.
- Tên hiển thị vẫn có thể chứa Unicode, khoảng trắng và dấu câu; chỉ `slug` bị giới hạn.
- Khi tự sinh từ tên: bỏ dấu tiếng Việt (`đ` → `d`), thay mỗi chuỗi ký tự không hợp lệ bằng `_`, gộp nhiều `_`, bỏ `_` ở đầu/cuối và thêm suffix số bằng `_` khi cần chống trùng. Không sinh kebab-case.
- Giữ nguyên các reference do API/skill khác trả về như `objectTypeSlug`, field slug hoặc provider/template ID. Không tự sửa một reference thật để ép regex; nếu hệ thống ngoài trả một giá trị không hợp lệ cho trường `slug` do process sở hữu, dừng và báo lỗi.
- Trước POST, duyệt các `slug` thuộc entity người dùng có thể chỉnh và bắt chúng khớp regex trên. Không áp dụng regex này cho slug hệ thống cố định như decision outcome mặc định `_default`, `optionConfig.slug` tùy chọn khi schema cho phép rỗng hoặc `validateMessage.slug` server-owned; không gửi `validateMessage` trong create request.

#### Quy tắc tạo ID
- Dùng đúng prefix theo entity: `PE` process, `NO` node, `FL` flow, `NC` node config, `RS` resource, `PI` process info, `DO` decision outcome, `DOC` condition và `SC` screen.
- Suffix là chuỗi chữ-số ngẫu nhiên đủ entropy và duy nhất trong payload. Không mô tả suffix là chỉ gồm chữ số hoặc bắt buộc một độ dài cố định; các ID canonical hiện có là alphanumeric và độ dài có thể do server/library quyết định.
- Trong **create payload**, action do front-end tạo dùng cùng ID với BPMN element: `action.id === action.nodeId === node.id`. Skill có thể sinh node ID theo convention `NO...`; payload lấy từ BPMN modeler có thể dùng `Activity_*`. Không tự sinh một `AC...` riêng và không đổi prefix của payload đang sửa.
- Response hoặc sample legacy có thể chứa action ID `AC...` do server remap. Khi sửa payload đã GET, giữ nguyên các ID và reference nhất quán; không áp quy tắc create để đổi ID response một cách cơ học.

#### Template cấu trúc BPMN XML
```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn2:definitions xmlns:bioc="http://bpmn.io/schema/bpmn/biocolor/1.0" xmlns:bpmn2="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:configEx="http://config-ex/schema" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:color="http://www.omg.org/spec/BPMN/non-normative/color/1.0" id="cogover-diagram" targetNamespace="http://bpmn.io/schema/bpmn" xsi:schemaLocation="http://www.omg.org/spec/BPMN/20100524/MODEL BPMN20.xsd">
  <bpmn2:process id="{PROCESS_ID}">
    <!-- Sự kiện Bắt đầu -->
    <!-- renderKey theo loại quy trình: START_MANUAL_EVENT / START_NORMAL_EVENT / START_SCHEDULED_EVENT / START_TRIGGERED_EVENT / START_SEQUENCE_EVENT -->
    <bpmn2:startEvent id="{START_NODE_ID}" name="Bắt đầu">
      <bpmn2:extensionElements>
        <configEx:elementInfo renderKey="{START_EVENT_RENDER_KEY}" />
      </bpmn2:extensionElements>
      <bpmn2:outgoing>{FIRST_FLOW_ID}</bpmn2:outgoing>
    </bpmn2:startEvent>

    <!-- User Tasks (lặp lại cho mỗi node) -->
    <bpmn2:userTask id="{USER_TASK_NODE_ID}" name="{NODE_NAME}">
      <bpmn2:extensionElements>
        <configEx:elementInfo renderKey="USER_TASK" />
      </bpmn2:extensionElements>
      <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
      <bpmn2:outgoing>{OUTGOING_FLOW_ID}</bpmn2:outgoing>
    </bpmn2:userTask>

    <!-- Exclusive Gateway (nếu có) -->
    <bpmn2:exclusiveGateway id="{GATEWAY_NODE_ID}" name="{GATEWAY_NAME}" default="{DEFAULT_FLOW_ID}">
      <bpmn2:extensionElements>
        <configEx:elementInfo openedGateway="true" />
        <configEx:elementInfo renderKey="EXCLUSIVE_GATEWAY" />
      </bpmn2:extensionElements>
      <bpmn2:incoming>{INCOMING_FLOW_ID}</bpmn2:incoming>
      <bpmn2:outgoing>{OUTGOING_FLOW_1}</bpmn2:outgoing>
      <bpmn2:outgoing>{OUTGOING_FLOW_2}</bpmn2:outgoing>
    </bpmn2:exclusiveGateway>

    <!-- Sự kiện Kết thúc -->
    <bpmn2:endEvent id="{END_NODE_ID}" name="Kết thúc quy trình">
      <bpmn2:extensionElements>
        <configEx:elementInfo renderKey="END_EVENT" />
      </bpmn2:extensionElements>
      <bpmn2:incoming>{LAST_FLOW_ID}</bpmn2:incoming>
    </bpmn2:endEvent>

    <!-- Luồng tuần tự (kết nối tất cả các node) -->
    <bpmn2:sequenceFlow id="{FLOW_ID}" name="" sourceRef="{SOURCE_NODE_ID}" targetRef="{TARGET_NODE_ID}">
      <bpmn2:extensionElements />
    </bpmn2:sequenceFlow>

    <!-- Luồng có điều kiện từ Gateway -->
    <bpmn2:sequenceFlow id="{CONDITION_FLOW_ID}" name="{CONDITION_NAME}" sourceRef="{GATEWAY_NODE_ID}" targetRef="{TARGET_NODE_ID}">
      <bpmn2:extensionElements />
    </bpmn2:sequenceFlow>
  </bpmn2:process>

  <!-- Sơ đồ BPMN (bố cục trực quan) -->
  <bpmndi:BPMNDiagram id="BPMNDiagram_{PROCESS_ID}">
    <bpmndi:BPMNPlane id="BPMNPlane_{PROCESS_ID}" bpmnElement="{PROCESS_ID}">

      <!-- BPMNShape cho MỖI node (startEvent, userTask, gateway, endEvent) -->
      <!-- QUAN TRỌNG: Mỗi BPMNShape PHẢI có <bpmndi:BPMNLabel> bên trong, nếu thiếu sẽ gây lỗi -->
      <bpmndi:BPMNShape id="{SHAPE_ID}_di" bpmnElement="{NODE_ID}">
        <dc:Bounds x="{X}" y="{Y}" width="60" height="60" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="{LABEL_X}" y="{LABEL_Y}" width="{LABEL_WIDTH}" height="16" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNShape>

      <!-- BPMNEdge cho MỖI sequenceFlow -->
      <bpmndi:BPMNEdge id="{EDGE_ID}_di" bpmnElement="{FLOW_ID}">
        <di:waypoint x="{SOURCE_X + WIDTH}" y="{SOURCE_Y + HEIGHT/2}" />
        <di:waypoint x="{TARGET_X}" y="{TARGET_Y + HEIGHT/2}" />
      </bpmndi:BPMNEdge>

    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn2:definitions>
```

#### Tính toán vị trí cho bố cục trực quan (BPMNDiagram)

**QUAN TRỌNG - ĐÂY LÀ QUY TẮC BẮT BUỘC:** Mỗi node phải có tọa độ (x, y) riêng biệt phù hợp với cấu trúc flow. Mỗi edge phải có waypoint tính toán dựa trên vị trí thực của node source/target. **KHÔNG ĐƯỢC** dùng tọa độ cố định hoặc hardcode waypoint.

##### Quy tắc chung
- Kích thước tất cả node: `width=60, height=60`
- Luồng chính (main flow): `y=260`
- Node đầu tiên: `x=40, y=260`
- Khoảng cách giữa 2 node liên tiếp trên cùng hàng: `x += 160` (có thể điều chỉnh tùy độ phức tạp)

##### Quy tắc bố trí nhánh (Gateway branching)

**Exclusive Gateway (2 nhánh):**
- Fork gateway và merge gateway nằm trên luồng chính (y=260)
- Nhánh điều kiện (condition branch): đặt phía **trên** luồng chính, `y = 100` (hoặc y chênh lệch -160 so với main)
- Nhánh mặc định (default branch): đặt phía **dưới** luồng chính, `y = 420` (hoặc y chênh lệch +160 so với main)
- Hoặc ngược lại tùy ngữ cảnh, miễn 2 nhánh cách nhau đủ xa (≥ 200px theo chiều dọc)

**Parallel Gateway (nhiều nhánh):**
- Fork gateway (open) và merge gateway (close) nằm trên luồng chính (y=260)
- Các nhánh trải đều theo chiều dọc, khoảng cách giữa các nhánh ≥ 160px
- Ví dụ 6 nhánh: y = -350, -150, 60, 260, 470, 670
- Một nhánh có thể nằm trên luồng chính (y=260) nếu phù hợp
- Merge gateway (close) phải đặt ở vị trí x lớn hơn node cuối cùng của nhánh dài nhất

**Nhánh con lồng nhau (sub-branches):**
- Nếu trong nhánh parallel có exclusive gateway phân nhánh tiếp, nhánh con đặt lệch y ±80 so với nhánh cha

##### Quy tắc tính waypoint cho BPMNEdge

Mỗi `BPMNEdge` phải có waypoint tính toán dựa trên vị trí thực của source node và target node. **KHÔNG BAO GIỜ** dùng tọa độ cố định.

Sinh node bounds và edge từ cùng một bảng node ID → bounds. Chốt vị trí node trước khi tính waypoint; nếu di chuyển node, tính lại mọi edge liên quan. Hai đầu edge phải bám đường biên của đúng node theo `sourceRef`/`targetRef`, không dùng tâm node làm điểm nối. Trước khi tạo/sửa XML, đọc [nodes/bpmn-geometry-validation.md](nodes/bpmn-geometry-validation.md) và chạy validator được hướng dẫn ở đó.

**Thuật ngữ vị trí (node bounds tại x, y, kích thước 60x60):**
- Right center: `(x+60, y+30)` — điểm giữa cạnh phải
- Left center: `(x, y+30)` — điểm giữa cạnh trái
- Top center: `(x+30, y)` — điểm giữa cạnh trên
- Bottom center: `(x+30, y+60)` — điểm giữa cạnh dưới

Các công thức 60×60 dưới đây dùng cho node mới theo kích thước mặc định. Với process đang sửa, tính tâm/cạnh từ `BPMNShape/Bounds` thực tế; không ép mọi node về 60×60. Case 1–4 giả định target nằm bên phải và tuyến không đi xuyên node; áp dụng case nối dọc hoặc quay lại bên dưới khi giả định này không đúng.

**Case 1 — Cùng hàng, target bên phải:** 2 waypoint; ngang khi tâm hai node cùng y, hơi chéo nếu chênh y nhỏ
```
waypoints: (sx+60, sy+30) → (tx, ty+30)
```

**Case 2 — Fork gateway → nhánh (source là fork gateway, target ở hàng khác):**
3 waypoint, exit từ top/bottom gateway rồi rẽ ngang đến target

- Target ở **trên** (ty < sy): exit từ top
  ```
  waypoints: (sx+30, sy) → (sx+30, ty+30) → (tx, ty+30)
  ```
- Target ở **dưới** (ty > sy): exit từ bottom
  ```
  waypoints: (sx+30, sy+60) → (sx+30, ty+30) → (tx, ty+30)
  ```

**Case 3 — Nhánh → merge gateway (target là merge gateway, source ở hàng khác):**
3 waypoint, đi ngang rồi rẽ dọc vào merge

- Source ở **trên** (sy < ty): enter từ top
  ```
  waypoints: (sx+60, sy+30) → (tx+30, sy+30) → (tx+30, ty)
  ```
- Source ở **dưới** (sy > ty): enter từ bottom
  ```
  waypoints: (sx+60, sy+30) → (tx+30, sy+30) → (tx+30, ty+60)
  ```

**Case 4 — Khác (không phải gateway, khác hàng):** 4 waypoint, đường L qua midpoint
```
mid_x = (sx + 60 + tx) / 2
waypoints: (sx+60, sy+30) → (mid_x, sy+30) → (mid_x, ty+30) → (tx, ty+30)
```

**Case 5 — Cùng cột, nối dọc:** nếu tâm hai node cùng x và không có node chắn giữa, nối cạnh đối diện trực tiếp. Target ở trên: `(sx+30, sy) → (tx+30, ty+60)`; target ở dưới: `(sx+30, sy+60) → (tx+30, ty)`. Ưu tiên case này thay vì Case 4, kể cả khi target là End Process.

**Case 6 — Quay lại/loop hoặc target bên trái:** nếu cùng hàng và không có vật cản, nối cạnh trái source tới cạnh phải target. Nếu đường đi xuyên node, chọn tuyến vòng ngoài bounds của các node, thêm điểm rẽ theo khoảng trống thực tế rồi kiểm tra lại. Không tái dùng công thức source-right → target-left cho mọi hướng; không đổi kết nối logic chỉ để làm đường vẽ đẹp hơn.

**Cách xác định fork/merge gateway:**
- Fork gateway: gateway có `isOpen: true` trong mảng `gateWays`
- Merge gateway: gateway có `isOpen: false` trong mảng `gateWays`

##### Ví dụ bố cục cho flow có exclusive gateway

```
Flow: Start → Task1 → EGW_Fork → [BranchA: Task2] / [BranchB: Task3] → EGW_Merge → End

Positions:
  Start:      (40, 260)
  Task1:      (200, 260)
  EGW_Fork:   (360, 260)    ← fork, y=260
  Task2:      (520, 100)    ← nhánh trên
  Task3:      (520, 420)    ← nhánh dưới
  EGW_Merge:  (680, 260)    ← merge, y=260
  End:        (840, 260)

Edges:
  Start→Task1:     (100,290) → (200,290)           [cùng hàng]
  Task1→EGW_Fork:  (260,290) → (360,290)           [cùng hàng]
  EGW_Fork→Task2:  (390,260) → (390,130) → (520,130) [fork → trên]
  EGW_Fork→Task3:  (390,320) → (390,450) → (520,450) [fork → dưới]
  Task2→EGW_Merge: (580,130) → (710,130) → (710,260) [trên → merge top]
  Task3→EGW_Merge: (580,450) → (710,450) → (710,320) [dưới → merge bottom]
  EGW_Merge→End:   (740,290) → (840,290)           [cùng hàng]
```

##### Ví dụ bố cục cho flow có parallel gateway

```
Flow: PGW_Open → [Branch1: TaskA] / [Branch2: TaskB] → PGW_Close

Positions:
  PGW_Open:   (360, 260)   ← fork parallel
  TaskA:      (520, 150)   ← nhánh trên
  TaskB:      (520, 380)   ← nhánh dưới
  PGW_Close:  (720, 260)   ← merge parallel

Edges:
  PGW_Open→TaskA:  (390,260) → (390,180) → (520,180)  [fork → trên]
  PGW_Open→TaskB:  (390,320) → (390,410) → (520,410)  [fork → dưới]
  TaskA→PGW_Close: (580,180) → (750,180) → (750,260)  [trên → merge top]
  TaskB→PGW_Close: (580,410) → (750,410) → (750,320)  [dưới → merge bottom]
```

##### BPMNLabel

**QUAN TRỌNG:** Mỗi `<bpmndi:BPMNShape>` **BẮT BUỘC** phải chứa `<bpmndi:BPMNLabel>` bên trong, và `<bpmndi:BPMNLabel>` **PHẢI** chứa `<dc:Bounds>` (KHÔNG được self-closing `<bpmndi:BPMNLabel/>` hoặc rỗng).

**Symptom khi thiếu/sai BPMNLabel:** API tạo quy trình vẫn trả `r:0` và `isValid:true` (server không validate phần này), nhưng khi người dùng mở quy trình trong editor và bấm Save, các node thiếu label sẽ **biến mất khỏi sơ đồ BPMN** (đặc biệt thấy rõ với Get Records, Loop, Update Record). Đây là lỗi silent, không có error log từ phía server.

❌ SAI (gây mất node khi save):
```xml
<bpmndi:BPMNShape bpmnElement="NO..." id="Shape_..._di">
  <dc:Bounds x="..." y="..." width="60" height="60"/>
</bpmndi:BPMNShape>
```

❌ SAI (BPMNLabel rỗng/self-closing):
```xml
<bpmndi:BPMNShape bpmnElement="NO..." id="Shape_..._di">
  <dc:Bounds x="..." y="..." width="60" height="60"/>
  <bpmndi:BPMNLabel/>
</bpmndi:BPMNShape>
```

✅ ĐÚNG:
```xml
<bpmndi:BPMNShape bpmnElement="NO..." id="Shape_..._di">
  <dc:Bounds x="..." y="..." width="60" height="60"/>
  <bpmndi:BPMNLabel>
    <dc:Bounds x="{LABEL_X}" y="{LABEL_Y}" width="{LABEL_WIDTH}" height="{LABEL_HEIGHT}"/>
  </bpmndi:BPMNLabel>
</bpmndi:BPMNShape>
```

- `LABEL_WIDTH` = ước lượng chiều rộng label dựa trên độ dài tên node: `max(28, len(name) * 6)` (làm tròn lên số nguyên). Với text dài (>25 ký tự) có thể xuống 2 dòng → `LABEL_HEIGHT = 32`
- `LABEL_X` = `X + (NODE_WIDTH / 2) - (LABEL_WIDTH / 2)` — **căn giữa** label so với node (KHÔNG dùng `LABEL_X = X`)
- `LABEL_Y` = `Y + 70` (label nằm dưới node, cách 10px)
- `LABEL_HEIGHT` = `16` (hoặc `32` nếu text xuống 2 dòng)

**BPMNLabel cho Edge có tên:** Nếu sequenceFlow có `name` (ví dụ: tên nhánh gateway), thêm BPMNLabel vào BPMNEdge:
```xml
<bpmndi:BPMNEdge id="Edge_1_di" bpmnElement="FL...">
  <di:waypoint x="..." y="..." />
  <di:waypoint x="..." y="..." />
  <bpmndi:BPMNLabel>
    <dc:Bounds x="{MID_X}" y="{MID_Y}" width="60" height="16" />
  </bpmndi:BPMNLabel>
</bpmndi:BPMNEdge>
```
Trong đó `MID_X`, `MID_Y` là trung điểm giữa waypoint đầu và waypoint cuối.

#### Template pageSettings của userTask

Mọi `userTask` mặc định dùng cấu hình trang bên dưới. Trang không có padding và nền dùng màu chính pha 100% trắng. Phần nội dung vẫn giữ padding 20px, viền hiển thị và chiều rộng tối đa 1000px:

```json
{
  "settingPage": {
    "typeColor": "primary",
    "css": "",
    "paddingBottom": 0,
    "color": "#dcdde9",
    "paddingRight": 0,
    "paddingTop": 0,
    "combinationRatio": 100,
    "paddingLeft": 0
  },
  "id": "{UUID}",
  "settingContentPage": {
    "typeColor": "primary",
    "borderColor": "#dcdde9",
    "css": "",
    "color": "#dcdde9",
    "paddingRight": 20,
    "unitMaxWidth": "px",
    "combinationRatio": 100,
    "typeBorder": "primary",
    "paddingBottom": 20,
    "paddingTop": 20,
    "isShowBorder": true,
    "paddingLeft": 20,
    "maxWidth": 1000
  },
  "slug": "page_setting_{USER_TASK_SLUG}"
}
```

#### Template nội dung userTask

Mỗi userTask cần một mảng `content` với cấu trúc layout. **QUAN TRỌNG:** Mỗi node layout (`layoutRow`, `layoutColumn`, `section`, `group`) phải có đầy đủ các thuộc tính như mẫu bên dưới, nếu thiếu sẽ gây lỗi hiển thị. Tất cả node `section` của `userTask` phải bật viền bằng `"isBorder": true`:
```json
{
  "paddingBottom": 0,
  "numberOfColumns": 1,
  "children": [
    {
      "colSpan": 1,
      "isShowChildren": true,
      "paddingRight": 0,
      "type": "layoutColumn",
      "isBorder": false,
      "isShowName": false,
      "paddingBottom": 0,
      "children": [
        {
          "isShowChildren": true,
          "paddingRight": 20,
          "type": "section",
          "typeSection": "normal",
          "isBorder": true,
          "isShowName": false,
          "paddingBottom": 24,
          "children": [
            {
              "children": [
                {
                  "components": [/* các trường form */],
                  "canCollapse": false,
                  "isShowChildren": true,
                  "paddingRight": 0,
                  "type": "group",
                  "isBorder": false,
                  "isShowName": false,
                  "paddingBottom": 0,
                  "numberOfColumns": 2,
                  "gap": 12,
                  "name": "",
                  "id": "{UUID}",
                  "paddingTop": 0,
                  "tabKey": 1,
                  "paddingLeft": 0,
                  "slug": "group_expand_0_{TIMESTAMP}"
                },
                {
                  "components": [/* nhóm nút */],
                  "canCollapse": false,
                  "isShowChildren": true,
                  "paddingRight": 0,
                  "type": "group",
                  "isBorder": false,
                  "isShowName": false,
                  "paddingBottom": 0,
                  "numberOfColumns": 2,
                  "gap": 12,
                  "name": "",
                  "id": "{UUID}",
                  "paddingTop": 0,
                  "tabKey": 1,
                  "paddingLeft": 0,
                  "slug": "group_expand_1_{TIMESTAMP}"
                }
              ],
              "isShowChildren": true,
              "name": "Tab 1",
              "id": "{UUID}",
              "slug": "tab_{TIMESTAMP}"
            }
          ],
          "gap": 20,
          "name": "",
          "id": "{UUID}",
          "paddingTop": 24,
          "numberOfTabs": 1,
          "paddingLeft": 20,
          "slug": "section_{TIMESTAMP}"
        }
      ],
      "gap": 20,
      "name": "",
      "id": "{UUID}",
      "paddingTop": 0,
      "paddingLeft": 0,
      "slug": "layout_column_{TIMESTAMP}"
    }
  ],
  "isShowChildren": true,
  "paddingRight": 0,
  "gap": 20,
  "id": "{UUID}",
  "paddingTop": 0,
  "type": "layoutRow",
  "paddingLeft": 0,
  "slug": "layout_row_{TIMESTAMP}",
  "isBorder": false
}
```

**Checklist thuộc tính bắt buộc theo node type:**

| Node type      | Thuộc tính bắt buộc (ngoài `type`, `children`)                                                                                                                                                  |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `layoutRow`    | `paddingBottom`, `numberOfColumns`, `isShowChildren`, `paddingRight`, `gap`, `id`, `paddingTop`, `paddingLeft`, `slug`, `isBorder`                                                              |
| `layoutColumn` | `colSpan`, `isShowChildren`, `paddingRight`, `isBorder`, `isShowName`, `paddingBottom`, `gap`, `name`, `id`, `paddingTop`, `paddingLeft`, `slug`                                                |
| `section`      | `isShowChildren`, `paddingRight`, `typeSection`, `isBorder`, `isShowName`, `paddingBottom`, `gap`, `name`, `id`, `paddingTop`, `numberOfTabs`, `paddingLeft`, `slug`                            |
| `group`        | `canCollapse`, `isShowChildren`, `paddingRight`, `isBorder`, `isShowName`, `paddingBottom`, `numberOfColumns`, `gap`, `name`, `id`, `paddingTop`, `tabKey`, `paddingLeft`, `slug`, `components` |

#### Template nhóm nút
Bao gồm các nút tiêu chuẩn cho mỗi userTask:
- Nhóm nút trái: "Hoàn tác" (rollback)
- Nhóm nút phải: "Hủy" (cancel) + "Thực hiện" (accept)

---


## Chi tiết các loại Node

Khi cần tạo node cụ thể, đọc file tương ứng trong `nodes/`:

| Node | File | renderKey | XML Element | Mô tả ngắn |
|------|------|-----------|-------------|-------------|
| Manual Flow Start | Phần `Manual Flow` trong file này | `START_MANUAL_EVENT` | `bpmn2:startEvent` | Start cố định của `manual_flow` |
| Normal Flow Start | `nodes/normal-flow.md` | `START_NORMAL_EVENT` | `bpmn2:startEvent` | Start Event của `normal_flow`, không có Root User Task bắt buộc. Mẫu: `samples/sample_normal_flow.json` |
| Scheduled Flow Start | `nodes/scheduled-start-event.md` | `START_SCHEDULED_EVENT` | `bpmn2:startEvent` | Start cố định của `scheduled_flow`; hỗ trợ 8 kiểu chu kỳ |
| Triggered Flow Start | `nodes/record-triggered-flow.md`, `nodes/webhook-triggered-flow.md` | `START_TRIGGERED_EVENT` | `bpmn2:startEvent` | Start cố định của `triggered_flow`, loại record hoặc webhook |
| Sequence Flow Start | Phần `Sequence Flow` trong file này | `START_SEQUENCE_EVENT` | `bpmn2:startEvent` | Start cố định của `sequence_flow` |
| Gateway | `nodes/gateway.md` | `EXCLUSIVE_GATEWAY`, `INCLUSIVE_GATEWAY`, `PARALLEL_GATEWAY` | `bpmn2:exclusiveGateway`, `bpmn2:inclusiveGateway`, `bpmn2:parallelGateway` | Phân nhánh có/không điều kiện. Mẫu: `samples/sample_process_exclusive_gw.json`, `samples/sample_inclusive_gateway.json`, `samples/sample_process_parallel_gw.json` |
| User Task Form Fields | `nodes/user-task-form-fields.md` | `USER_TASK` | `bpmn2:userTask` | Các loại trường form active, gồm short/long text, regex, display_text, select_record_table, numeric/decimal, date/date_time, email, phone, boolean, file, lookup, select list, percent, currency, label và URL |
| Send Email | `nodes/send-email-task.md` | `SEND_EMAIL_TASK` | `bpmn2:sendTask` | Gửi email tự động với subject, content (raw/template/variable), to/cc/bcc, attachments |
| Send HTTP Request | `nodes/send-http-request-task.md` | `SEND_HTTP_TASK` | `elEx:httpTask` | Gửi HTTP request (GET/POST/PUT/PATCH/DELETE/HEAD) với headers và body |
| Send Notification | `nodes/send-notification-task.md` | `SEND_NOTIFICATION_TASK` | `elEx:sendNotificationTask` | Gửi thông báo đến personnel |
| Get Records | `nodes/get-records-task.md` | `GET_RECORD_TASK` | `elEx:getRecordTask` | Lấy bản ghi từ đối tượng với điều kiện lọc và sắp xếp |
| Create Record | `nodes/create-record-task.md` | `CREATE_RECORD_TASK` | `elEx:createRecordTask` | Tạo bản ghi mới cho đối tượng |
| Update Record | `nodes/update-record-task.md` | `CREATE_RECORD_TASK` | `elEx:createRecordTask` | Cập nhật bản ghi (cùng XML element với Create, khác `actionType`) |
| Loop | `nodes/loop-task.md` | `LOOP_TASK` | `elEx:loopTask` | Duyệt danh sách, có 2 nhánh: for_each_item và after_last_item |
| Assignment | `nodes/assignment-task.md` | `ASSIGNMENT` | `elEx:assignment` | Gán giá trị cho biến (=, +=, -=, count) |
| Organization | `nodes/organization-task.md` | `ORGANIZATION_TASK` | `elEx:organizationTask` | Truy vấn cấu trúc tổ chức (manager, personnel, department, position) |
| Wait | `nodes/wait-task.md` | `WAIT_TASK` | `elEx:waitTask` | Runtime hiện hỗ trợ timer tương đối và email open/reply/link; đọc compatibility table trước khi dùng event khác |
| Sub Process | `nodes/sub-process-task.md` | `SUB_PROCESS` | `elEx:subProcess` | Gọi quy trình con, truyền/nhận biến |
| To Do | `nodes/todo-task.md` | `TODO_TASK` | `elEx:todoTask` | Tạo activity To Do; chỉ dùng trong Sequence Flow. Mẫu: `samples/sample_sequence_flow_todo.json` |
| Phone Call | `nodes/phone-call-task.md` | `PHONE_CALL_TASK` | `elEx:phoneCallTask` | Gọi từ hotline bằng recording hoặc TTS. Mẫu: `samples/sample_phone_call.json` |
| Export Record | `nodes/export-record-task.md` | `EXPORT_TASK` | `elEx:exportRecordTask` | Xuất record bằng document template. Mẫu: `samples/sample_export_record.json` |
| Respond to Webhook | `nodes/response-webhook-task.md` | `RESPONSE_WEBHOOK_TASK` | `elEx:responseWebhookTask` | Schema-only trên backend hiện tại; runtime chưa đăng ký action |
| Push Message | `nodes/push-message-task.md` | `PUSH_MESSAGE_TASK` | `elEx:pushMessageTask` | Gửi refresh/toast/background message. Mẫu: `samples/sample_push_message.json` |
| JSON to Object | `nodes/parse-to-object-task.md` | `PARSE_TO_OBJECT_TASK` | `elEx:parseToObjectTask` | Schema-only trên backend hiện tại; runtime chưa đăng ký action |
| Omni Message | `nodes/omni-message-task.md` | `OMNI_MESSAGE_TASK` | `bpmn2:sendTask` + `elEx:omniMessageTask` marker | Gửi Zalo ZBS/WhatsApp theo thứ tự fallback. Mẫu: `samples/sample_omni_message.json` |
| AI Agent | `nodes/ai-agent-task.md` | `AI_AGENT_TASK` | `bpmn2:sendTask` + `elEx:aiAgentTask` marker | Gọi agent, chờ kết quả, dùng output ở bước sau. Mẫu: `samples/sample_ai_agent.json`; kiểm tra tương thích API/editor trước khi lưu |
| End Branch | `nodes/end-branch-event.md` | `END_BRANCH_EVENT` | `bpmn2:endEvent` | Kết thúc nhánh hiện tại, không kết thúc toàn process. Mẫu: `samples/sample_end_branch.json` |
| End Process | Phần BPMN XML trong file này | `END_EVENT` | `bpmn2:endEvent` | Kết thúc toàn process; workflow phải có ít nhất một End Event |

**Lưu ý:** Các node dùng `elEx:` cần thêm namespace `xmlns:elEx="http://element-ex/schema"` vào `bpmn2:definitions`.

**Quy ước placeholder action:** Trong các node doc, `{ACTION_ID}` của create payload phải dùng cùng giá trị với `{..._NODE_ID}` tương ứng, bất kể node dùng `NO...` hay `Activity_*`. `AC...` chỉ có thể xuất hiện trong response/legacy payload đã được server remap.

### Support matrix node theo workflow type

| Mục | Manual | Normal | Scheduled | Triggered | Sequence | Điều kiện |
|---|---:|---:|---:|---:|---:|---|
| `START_MANUAL_EVENT` | ✓ | — | — | — | — | Start cố định, không thêm từ palette |
| `START_NORMAL_EVENT` | — | ✓ | — | — | — | Start cố định, không thêm từ palette |
| `START_SCHEDULED_EVENT` | — | — | ✓ | — | — | Start cố định, cấu hình `scheduleRules` |
| `START_TRIGGERED_EVENT` | — | — | — | ✓ | — | Start cố định, loại record/webhook |
| `START_SEQUENCE_EVENT` | — | — | — | — | ✓ | Start cố định, không thêm từ palette |
| To Do | — | — | — | — | ✓ | Sequence-only |
| Phone Call | ✓ | ✓ | ✓ | ✓ | ✓ | Sequence có automatic/manual |
| Export Record | ✓ | ✓ | ✓ | ✓ | ✓ | UI canonical dùng document template thật lấy qua `$document-template` |
| Respond to Webhook | ✗ | ✗ | ✗ | ✗ | ✗ | Payload/editor có schema nhưng `run-workflow-server` hiện chưa đăng ký action runtime; không tạo cho flow cần chạy |
| Push Message | ✓ | ✓ | ✓ | ✓ | ✓ | Field phụ thuộc push/recipient type |
| JSON to Object | ✗ | ✗ | ✗ | ✗ | ✗ | Payload/editor có schema nhưng `run-workflow-server` hiện chưa đăng ký action runtime; không tạo cho flow cần chạy |
| Omni Message | ✓ | ✓ | ✓ | ✓ | ✓ | Chỉ Zalo ZBS và WhatsApp đang active |
| AI Agent | △ | △ | △ | △ | △ | Có khả năng thực thi; cần Process API/editor hỗ trợ `AI_AGENT`, agent hoạt động và danh tính chạy hợp lệ. Flow tự động cần kiểm tra người khởi tạo hoặc chọn `PERSONNEL` |
| End Branch | ✓ | ✓ | ✓ | ✓ | ✓ | Dùng trong nhánh song song/phân nhánh |
| End Process | ✓ | ✓ | ✓ | ✓ | ✓ | Kết thúc toàn process; bắt buộc có ít nhất một End Event |

### Runtime compatibility và tiêu chí kiểm thử

`△` là hỗ trợ có điều kiện trên Workspace đích, chưa phải bằng chứng kiểm thử end-to-end. Với AI Agent, đọc `nodes/ai-agent-task.md` để kiểm tra khả năng lưu/mở lại node, output và nhánh xử lý lỗi; không suy ra khả năng tạo node chỉ từ khả năng thực thi.

Support matrix trên là contract cho backend runtime đang được dùng cùng skill này, không chỉ là danh sách node của palette. Trước khi tạo process có Wait, User Task, Formula hoặc một action tích hợp, đọc `nodes/runtime-validation.md` và file node tương ứng.

- Không suy luận PASS từ `isValid:true`, `ACTIVATED`, `isPublished:true` hoặc instance `COMPLETED`; phải chứng minh hiệu ứng nghiệp vụ/output/nhánh downstream.
- Các node có schema create nhưng chưa có runtime action được đánh dấu `✗`. Không sinh chúng cho quy trình được yêu cầu chạy.
- Nếu phiên bản backend thay đổi, phải kiểm tra lại runtime registration và chạy black-box test trước khi đổi matrix.

---

### Bước 3: Tạo JSON hoàn chỉnh
Xây dựng JSON hoàn chỉnh với tất cả các phần:
1. `metadata`: {}
2. `participantPermission`: đối tượng quyền tiêu chuẩn
3. `processInstanceAccessControls`: kiểm soát truy cập tiêu chuẩn (xem template bên dưới)
4. `xmlString`: chuỗi BPMN XML đã escape
5. `overviewScreen`: **bắt buộc là JSON object**, không dùng `null`. Khi không có màn hình tổng quan tùy chỉnh, dùng `{"layout": [], "permissionGeneralInfo": []}`
6. `type`: loại quy trình (`"manual_flow"`, `"normal_flow"`, `"scheduled_flow"`, `"triggered_flow"`, hoặc `"sequence_flow"` — xem mục "Các loại quy trình và cách chọn loại quy trình")
7. `permissions`: mảng quyền tương ứng với loại quy trình (xem mục "Các loại quy trình và cách chọn loại quy trình")
8. `accessControls`: kiểm soát truy cập tiêu chuẩn (xem template bên dưới)
9. `progressStatus`: "DRAFT"
10. `processInfoId`: ID PI được tạo
11. `userTasks`: mảng cấu hình task (xem template `taskPerformer` bên dưới)
12. `gateWays`: mảng cấu hình gateway (nếu có)
13. `resources`: system resources, custom resources, userTasks resources, actions resources
14. `actions`: mảng cấu hình action (Assignment, Send Email, etc.) (nếu có)
15. `starterPermission`: quyền khởi tạo tiêu chuẩn
16. `version`: "V1"
17. `name`: tên quy trình
18. `slug`: slug quy trình
19. `status`: 2

#### Template `processInstanceAccessControls`
**QUAN TRỌNG:** Sử dụng `"functions"` (mảng) thay vì `"action"` (chuỗi):
```json
{
  "processInstanceAccessControls": [
    {
      "functions": ["START_INSTANCE"],
      "type": "personnel",
      "items": [""],
      "option": 1
    }
  ]
}
```

#### Template `accessControls`
**QUAN TRỌNG:** Sử dụng `"functions"` (mảng) thay vì `"action"` (chuỗi):
```json
{
  "accessControls": [
    {
      "functions": ["VIEW"],
      "type": "personnel",
      "items": [""],
      "option": 1
    }
  ]
}
```

#### Template `taskPerformer` trong userTask
**QUAN TRỌNG:** `taskPerformer` là **mảng lồng mảng** `[[{...}]]`, KHÔNG phải mảng đơn `[{...}]`:
```json
{
  "taskPerformer": [
    [
      {
        "field": "account",
        "isRawValue": true,
        "value": [],
        "option": 3
      }
    ]
  ]
}
```
- Cấu trúc: `taskPerformer[group_index][performer_index]`
- Mỗi phần tử cấp 1 là một mảng (group) chứa các performer
- Mỗi performer có `field`, `isRawValue`, `value`, `option`

### Bước 4: Gọi API tạo quy trình

**KHÔNG tạo file JSON.** Thay vào đó, gọi API để tạo quy trình trực tiếp trên hệ thống.

#### 4.1. Sanity check XML trước khi POST (BẮT BUỘC)

`isValid: true` từ server **KHÔNG đảm bảo** XML hợp lệ ở mọi mặt — server chỉ validate kết nối logic giữa các node, **KHÔNG validate** đầy đủ phần BPMNDiagram (bố cục trực quan). Trước khi POST, kiểm tra `xmlString` đã sinh:

| # | Kiểm tra | Cách check (regex/đếm) |
|---|---|---|
| 1 | Số lượng `<bpmndi:BPMNShape>` = số node trong `<bpmn2:process>` | `xml.count('<bpmndi:BPMNShape')` |
| 2 | **Mỗi `<bpmndi:BPMNShape>` đều có `<bpmndi:BPMNLabel>` chứa `<dc:Bounds>`** (xem section BPMNLabel) | regex `<bpmndi:BPMNShape[^>]*>.*?<bpmndi:BPMNLabel>.*?<dc:Bounds[^/]*/>.*?</bpmndi:BPMNLabel>.*?</bpmndi:BPMNShape>` phải khớp với mọi shape |
| 3 | Số lượng `<bpmndi:BPMNEdge>` = số `<bpmn2:sequenceFlow>` | `xml.count('<bpmndi:BPMNEdge') == xml.count('<bpmn2:sequenceFlow')` |
| 4 | KHÔNG có tag prefix `<bpmn:` (chỉ dùng `<bpmn2:`) — namespace `bpmn` không được khai báo | `xml.count('<bpmn:') == 0` và `xml.count('</bpmn:') == 0` |
| 5 | Mọi node (trừ Start/End) đều có cả `<bpmn2:incoming>` và `<bpmn2:outgoing>` | duyệt từng node trong `<bpmn2:process>` |
| 6 | Mọi `<bpmn2:sequenceFlow>` có `sourceRef` và `targetRef` trỏ vào `id` node thực sự tồn tại | đối chiếu với danh sách node ID |
| 7 | Mọi slug user-editable dài ≥ 2 và khớp `^[A-Za-z](?!.*__)[A-Za-z0-9_]*[^_]$` | kiểm tra theo schema entity; cho phép các slug hệ thống cố định như `_default` |
| 8 | `overviewScreen` là object | `typeof overviewScreen == "object"`, không phải `null`/array; dùng `{ "layout": [], "permissionGeneralInfo": [] }` nếu không tùy chỉnh |
| 9 | Field User Task bắt buộc + chỉ đọc phải bật Gửi dữ liệu | với mọi component có `required` và `readOnly` truthy, yêu cầu `component.canSendData === true`; đây là cờ đưa giá trị field vào payload submit form |
| 10 | Mỗi node/flow có đúng một shape/edge tương ứng; waypoint đầu/cuối bám đúng biên node nguồn/đích; đường nối không đi xuyên node | chạy `scripts/validate_bpmn_geometry.py --mode request` theo [hướng dẫn kiểm tra hình học](nodes/bpmn-geometry-validation.md); yêu cầu exit code `0` và `ok: true` |

Nếu bất kỳ check nào fail, FIX trong code sinh XML rồi mới POST. **KHÔNG** POST rồi mới sửa, vì process activated khó update lại (xem mục 4.4). Áp dụng kiểm tra này trước cả request cập nhật XML; đếm đủ edge hoặc reference đúng không thay thế kiểm tra hình học. Validator không thay thế các kiểm tra metadata/form/nghiệp vụ còn lại trong bảng.

#### 4.2. Gọi API

1. Đọc tài liệu API: `api-process-builder.md`
2. Gọi API tạo quy trình: `POST /bapi/v1/processes` với body là JSON đã tạo ở Bước 3
3. Kiểm tra response:
   - Chỉ coi là thành công khi đồng thời `r = 0`, `data` là object, `data.id` và `data.processInfoId` đều là chuỗi không rỗng. Một số lỗi filter trả `r:0` nhưng có `msg` lỗi và không có `data/id`; đó vẫn là create thất bại.
   - Khi thành công: lấy `id` (process ID) và `processInfoId` từ `data`.
   - Nếu thất bại: thông báo lỗi cho khách hàng

#### 4.3. Trả link cho khách hàng

```
https://{WORKSPACE_DOMAIN}/settings/processes/{id}/{processInfoId}
```
Trong đó:
- `{WORKSPACE_DOMAIN}`: domain workspace của khách hàng (lấy từ biến môi trường hoặc hỏi khách hàng)
- `{id}`: giá trị `data.id` từ response API
- `{processInfoId}`: giá trị `data.processInfoId` từ response API

#### 4.4. Sửa lỗi cho quy trình đã ACTIVATED

Khi quy trình đã được tạo nhưng phát hiện lỗi XML (ví dụ: node biến mất khi save do thiếu BPMNLabel), KHÔNG thể PUT trực tiếp:

- `PUT /bapi/v1/processes/{id}` trên process đang `progressStatus: ACTIVATED` (hoặc `isPublished: true`) sẽ trả `r: 414` với message **"process is not in the right progress status for save"** — kể cả khi body có `progressStatus: "DRAFT"` và `isPublished: false`.
- **Cách xử lý:**
  1. **Hỏi xác nhận khách hàng** trước khi xoá (theo Quy tắc an toàn ở đầu skill).
  2. Nếu được đồng ý: lấy bản XML cũ qua `POST /bapi/v1/processes/view` với `{"id": "PE..."}`, fix XML, strip các trường `id`/`processInfoId`/`version`/`versionNumber`/`status`/`created`/`updated`/... khỏi body, rồi:
  3. `POST /bapi/v1/processes/delete` với `{"id": "PE...", "processInfoId": "PI..."}` — xoá toàn bộ versions cùng processInfoId.
  4. `POST /bapi/v1/processes` với body đã fix — tạo lại. Process mới sẽ mang `id`/`processInfoId` mới.
  5. Trả link mới cho khách hàng và giải thích nguyên nhân.

**Note: list/find process theo slug:** dùng `POST /bapi/v1/processes/list` với body `{"page":1,"limit":50,"keywords":["<slug_or_name_keyword>"]}`. Tham số phân trang là `limit`, KHÔNG phải `pageSize` hay `per_page`.

#### 4.5. Verify sau khi POST

Sau khi nhận `r:0`, gọi `POST /bapi/v1/processes/view` với `{"id":"<new id>"}` và kiểm tra hậu điều kiện:

1. Xác nhận `progressStatus`, `isPublished`, `isValid`, workflow `type`, action type/renderKey và các cấu hình nghiệp vụ chính.
2. So sánh số node, flow, `BPMNShape`, `BPMNEdge`, label và topology với payload trước POST. Nếu server thật sự strip node/shape/edge hoặc làm hỏng reference nghiệp vụ thì báo lỗi; không dựa riêng vào `isValid:true`.
   - Chạy lại `scripts/validate_bpmn_geometry.py --mode response` trên dữ liệu vừa đọc; chỉ so sánh giống payload trước POST là chưa đủ, vì waypoint có thể đã sai từ payload ban đầu.
   - Nếu ID bị remap, đối chiếu node theo slug cấu hình + loại node; chỉ dùng tên + loại khi tổ hợp đó duy nhất. So các cặp nguồn–đích, nhánh mặc định/điều kiện và hình học theo mapping này. Mapping mơ hồ phải được làm rõ, không tự ghép theo thứ tự mảng.
3. Workflow Server hiện có thể serialize `incoming`, `outgoing`, `sequenceFlow` từ `bpmn2:` thành `bpmn:` trong response GET dù request trước POST dùng đúng `bpmn2:`. Đây là canonicalization phía server. Khi hậu kiểm, đếm tag theo local name hoặc cho phép cả hai prefix; **không PUT/DELETE/recreate chỉ để đổi prefix response**. Request create/update do skill sinh vẫn bắt buộc chỉ dùng `bpmn2:`.
4. Server có thể remap Node ID. Đối với `RESPONSE_WEBHOOK` nguồn Start, bắt buộc kiểm tra `action.data.waitActionSlug` bằng đúng Start Event ID sau GET; nếu lệch, process chưa sẵn sàng dù `isValid:true`. Không lặp PUT để đuổi theo ID vì mỗi lần save có thể remap lại; làm theo `nodes/response-webhook-task.md`.
5. Với Omni Message, server có thể bỏ marker rỗng `<elEx:omniMessageTask />` và parse `action.data` từ JSON string thành object ở response. Xác minh bằng `renderKey: OMNI_MESSAGE_TASK`, action type và cấu hình methods; không PUT chỉ để khôi phục representation của request.
6. Duyệt lại mọi field User Task. Không coi version là đạt nếu còn component `required && readOnly` mà chưa có `canSendData: true`, kể cả khi process trả `isValid: true`.

#### 4.6. Kích hoạt và xác nhận process end-to-end (BẮT BUỘC)

Sau **mọi lần tạo process**, phải chạy vòng xác nhận dưới đây. Không coi công việc hoàn tất chỉ vì API create trả `r: 0`, GET-back trả `isValid: true` hoặc process đã được kích hoạt. Đọc `nodes/runtime-validation.md` trước khi chạy.

**Không hỏi xác nhận riêng trước khi chạy test:** Khi người dùng đã xác nhận luồng ở Bước 1 và yêu cầu tạo process, xem xác nhận đó là quyền thực hiện trọn vòng triển khai trong phạm vi đã mô tả, gồm create, GET-back verify, kích hoạt, xuất bản, tạo lượt chạy và runtime test. Tiếp tục tự động, không dừng để hỏi thêm một câu “có chạy test không?”. Quy tắc này không thay thế các xác nhận bắt buộc khác: vẫn phải hỏi trước khi DELETE process/record hoặc khi chính sách an toàn cấp hệ thống yêu cầu xác nhận tại thời điểm thực hiện một side effect cụ thể như gửi thông điệp thật hay truyền dữ liệu nhạy cảm. Trong trường hợp đó, hoàn tất mọi bước không bị chặn trước, rồi chỉ hỏi xác nhận hẹp cho đúng hành động bắt buộc.

##### Bước 1: Kích hoạt process

1. Mở process bằng Chrome trong đúng session workspace của người dùng:
   `https://{WORKSPACE_DOMAIN}/process/processes/{PROCESS_ID}/{PROCESS_INFO_ID}`
2. Kích hoạt process. Nếu giao diện có bước **Xuất bản** riêng, xuất bản luôn để version có thể sinh lượt chạy ổn định.
3. Đọc lại và xác nhận tối thiểu `progressStatus: "ACTIVATED"`, `isPublished: true`, `isValid: true`, đúng `PROCESS_ID` và `PROCESS_INFO_ID` vừa tạo.

##### Bước 2: Tạo lượt chạy process theo loại flow

- **Manual Flow, Normal Flow:** vào link process ở Bước 1 và nhấn **Tạo lượt chạy**. Nếu nút không xuất hiện hoặc gửi thất bại, kiểm tra trạng thái kích hoạt/xuất bản, quyền `START_INSTANCE` trong `processInstanceAccessControls` và quyền `VIEW` trong `accessControls`.
- **Scheduled Flow:** trước khi thay đổi, lưu snapshot chính xác `scheduleRules` theo yêu cầu người dùng. Tạm đặt thời gian bắt đầu gần thời điểm kiểm tra, kích hoạt/xuất bản version test, rồi quan sát trên Chrome xem instance có được sinh đúng thời điểm hay không. Trong khối cleanup bắt buộc, khôi phục nguyên cấu hình lịch người dùng yêu cầu, kích hoạt/xuất bản lại nếu việc lưu tạo version mới, rồi GET-back để đối chiếu với snapshot. Không để lịch test tiếp tục chạy.
- **Triggered Flow loại `record`:** dùng skill `$object-record` để tạo bản ghi test phù hợp với Object, event và conditions của trigger; nếu trigger cần update thì cập nhật đúng field/giá trị để đưa bản ghi qua điều kiện kích hoạt. Dùng marker test duy nhất và theo dõi mọi record ID. Với trigger delete, phải tuân thủ quy tắc xác nhận xoá của `$object-record`: chỉ xoá record test sau khi đã liệt kê ID cụ thể và người dùng xác nhận.
- **Triggered Flow loại `webhook`:** lấy URL Webhook thực của process và gửi request với body hợp lệ theo `sampleData`/`parseToDataType` cùng đúng cơ chế xác thực đã cấu hình. Kiểm tra cả HTTP response và instance được sinh. Chỉ giữ token/secret trong tiến trình cần cho request; không đưa cookie, secret hoặc token vào file, log, commentary hay báo cáo.
- **Sequence Flow:** chọn hoặc tạo bằng `$object-record` một bản ghi thật sự thuộc `metadata.objectTypeId`/`objectTypeSlug`, rồi gọi API sau với ID thật. Trước khi gọi `/api/v1/run-workflow-server`, bắt buộc dùng skill `$cogover-api-auth` để đổi API Key thành phiên Web App qua `POST /bapi/v1/auth-token`; không đọc cookie/local storage từ Browser và không thay API call bằng thao tác **Sequence → Kết nối** trên UI. Chỉ tiếp tục khi auth trả HTTP 200, `r: 0`, đúng workspace và có đủ `HttpSessionId`, `AuthToken`, `XSRF-TOKEN`. Giữ ba giá trị trong tiến trình tạm, dùng chính `XSRF-TOKEN` cho cả hai header CSRF/XSRF, không ghi hoặc in credential ra file/log/commentary/final:

  ```bash
  curl --url 'https://{WORKSPACE_DOMAIN}/api/v1/run-workflow-server' \
    -H 'accept: application/json, text/plain, */*' \
    -H 'content-type: application/json' \
    -b 'HttpSessionId={HTTP_SESSION_ID}; AuthToken={AUTH_TOKEN}; XSRF-TOKEN={XSRF_TOKEN}' \
    -H 'x-csrf-token: {XSRF_TOKEN}' \
    -H 'x-req-service: 7' \
    -H 'x-req-type: 6' \
    -H 'x-xsrf-token: {XSRF_TOKEN}' \
    --data-raw '{"list":[{"processId":"{PROCESS_ID}","flowObjectRecordId":"{FLOW_OBJECT_RECORD_ID}"}]}'
  ```

  | Lỗi thường gặp | Hướng xử lý ngắn |
  |---|---|
  | `Can not found processor for request: service=...` | Thử lại đúng request bằng literal `curl` thay cho `urllib`. Nếu `curl` PASS, phân loại lỗi client transport và tiếp tục bằng `curl`; chỉ kết luận processor không khả dụng khi `curl` cũng lỗi. Không đổi service number bằng thử ngẫu nhiên. |

##### Bước 3: Quan sát và đánh giá lượt chạy

1. Trước khi quan sát, bảo đảm người test hiện tại có quyền xem instance của process. Nếu cần cấp quyền/vị trí/phòng ban tạm, lưu snapshot trước thay đổi và dùng `$user-permission`; không nới quyền rộng hơn mức cần để kiểm thử.
2. Mở `https://{WORKSPACE_DOMAIN}/process/process-instances?filter=all`, xác định đúng instance mới bằng process ID, thời gian bắt đầu và dữ liệu test; không nhầm với instance cũ hoặc instance do người khác tạo.
3. Mở instance, quan sát diagram, trạng thái từng node, output và Debug. Khi instance tới **User Task đầu tiên**, nhập dữ liệu hợp lý, đúng kiểu và phù hợp kịch bản nghiệp vụ rồi submit. Nếu task chỉ cho một số vị trí/phòng ban thực hiện, dùng `$user-permission` để phân tạm vị trí/phòng ban cần thiết cho người test hiện tại, xác minh quan hệ đã có hiệu lực, và bắt buộc rollback về snapshot sau khi test.
4. Đối chiếu kết quả với yêu cầu bài toán: nhánh đi đúng, task đúng người, dữ liệu/action/output/side effect đúng giá trị mong đợi. Khi cần đọc, tạo hoặc đối chiếu dữ liệu nghiệp vụ, dùng `$object-record`; không suy ra PASS chỉ từ trạng thái `COMPLETED`.
5. Khi cần debug sâu, dùng `$object-record` đọc Object có slug chính xác `Process_Debug_data`. Lọc theo process/instance/thời điểm hoặc marker test dựa trên schema thực tế; không đoán field slug.
6. Đánh giá theo tiêu chí observable và phân loại `PASS`, `PARTIAL`, `FAIL_SKILL`, `FAIL_RUNTIME` hoặc `BLOCKED_ENV` trong `nodes/runtime-validation.md`. Nếu phát hiện lỗi thuộc payload/skill và có thể sửa an toàn, sửa rồi chạy lại toàn bộ vòng xác nhận. Nếu sửa process đã activated buộc phải xoá/tạo lại, tuân thủ mục 4.4 và hỏi xác nhận trước khi xoá.

##### Cleanup và báo cáo

- Luôn phục hồi lịch Scheduled Flow và mọi quyền/vị trí/phòng ban tạm, kể cả khi lượt chạy lỗi hoặc việc kiểm thử bị gián đoạn; đọc lại để xác nhận trạng thái cuối khớp snapshot/yêu cầu người dùng.
- Theo dõi dữ liệu test bằng marker/ID. Muốn xoá fixture phải làm theo quy tắc xác nhận xoá của `$object-record`; nếu chưa được phép xoá, báo rõ Object và ID còn lại thay vì tuyên bố đã dọn sạch.
- Báo link process, ID instance, loại flow/cách kích hoạt, trạng thái cuối, bằng chứng nghiệp vụ, dữ liệu Debug đã dùng, các thay đổi tạm đã rollback và mọi fixture còn tồn đọng. Không báo credential hoặc secret.

Không PUT toàn bộ body vừa GET về: XML response có thể dùng prefix canonical `bpmn:`; round-trip nguyên trạng có thể làm server strip flow. Khi cần sửa DRAFT, dựng lại request hợp lệ dùng `bpmn2:` và chỉ thay đổi phần đã chủ đích.

---

## Ví dụ sử dụng

### Ví dụ 1: Quy trình đơn giản (không có Gateway)

Người dùng: "Tạo quy trình phê duyệt mua sắm"

Trợ lý hỏi:
1. Tên quy trình?
2. Danh sách các node (phân cách bằng dấu phẩy hoặc mũi tên)?

Người dùng cung cấp:
- Tên: "Quy trình phê duyệt mua sắm"
- Các node: "Root -> Trưởng phòng duyệt -> Giám đốc duyệt"

Trợ lý xác nhận luồng:
> Luồng quy trình: Bắt đầu -> Root -> Trưởng phòng duyệt -> Giám đốc duyệt -> Kết thúc quy trình
> Bạn xác nhận luồng này đúng chưa?

Người dùng: "OK"

Trợ lý tạo JSON, gọi API `POST /bapi/v1/processes`, GET-back verify, kích hoạt và chạy thử theo mục 4.6. Chỉ sau khi đối chiếu đúng instance và kết quả nghiệp vụ, trợ lý mới báo kết quả cuối cùng kèm link process, instance ID và trạng thái PASS/PARTIAL/FAIL/BLOCKED.

### Ví dụ 2: Quy trình có Exclusive Gateway

Người dùng cung cấp:
- Tên: "Quy trình xin nghỉ phép"
- Cấu trúc:
  ```
  Bắt đầu -> Root -> Exclusive Gateway

  Exclusive Gateway có 2 nhánh:
  - Nhánh "Số ngày > 5": điều kiện $userTask.Root.so_ngay_xin_nghi >= 5
    -> User Task 1 -> Kết thúc
  - Nhánh "Mặc định":
    -> User Task 2 -> Kết thúc (2)
  ```

Trợ lý xác nhận luồng, người dùng đồng ý, trợ lý tạo JSON, gọi API, kích hoạt, chạy một kịch bản cho từng nhánh cần chứng minh và báo bằng chứng runtime:
- Bắt đầu -> Root -> Exclusive
- Exclusive -> "Số ngày xin nghỉ > 5" -> User Task 1 -> Kết thúc quy trình
- Exclusive -> "Mặc định" -> User Task 2 -> Kết thúc quy trình (2)

---

## Thuộc tính chung quan trọng

| Thuộc tính | Mô tả                                    |
|------------|------------------------------------------|
| `required` | 0 = không bắt buộc, 1 = bắt buộc         |
| `multiple` | 0 = đơn giá trị, 1 = nhiều giá trị       |
| `unique`   | true/false - giá trị có cần unique không |
| `readOnly` | null hoặc true - chỉ đọc                 |
| `disable`  | null hoặc true - vô hiệu hóa             |
| `canSendData` | false/true - đưa giá trị field vào payload khi submit form; checkbox **Gửi dữ liệu** |
| `uiSlug`   | Định danh UI, format: "_1", "_2", ...    |

**Ràng buộc runtime của field User Task:** Nếu một component đồng thời là **Trường bắt buộc** (`required: 1` hoặc `true`) và **Trường chỉ đọc** (`readOnly: true` hoặc `1`) thì bắt buộc bật **Gửi dữ liệu** (`canSendData: true`) ngay trên component trong `userTasks[].content`. `canSendData` quyết định field có được đưa vào payload submit form gửi tới `run-workflow-server` hay không; nó độc lập với `availableForOutput` của component/resource. Nếu thiếu, server có thể trả lỗi thiếu dữ liệu bắt buộc. Xem ví dụ và thuật toán kiểm tra trong `nodes/user-task-form-fields.md`.

---
## Variable (Biến)

### Mô tả
Variable (Biến) là các biến cấp quy trình (process-level) dùng để lưu trữ và truyền dữ liệu giữa các bước trong quy trình. Biến có thể được dùng làm giá trị mặc định cho các trường trong userTask, làm tham số cho action, hoặc làm điều kiện trong gateway. Có thể đọc, ghi giá trị vào biến.

### Các kiểu dữ liệu biến

| Kiểu dữ liệu        | dataType    | Mô tả                                 | Ví dụ defaultValue                         |
|---------------------|-------------|---------------------------------------|--------------------------------------------|
| Chữ (Text)          | `TEXT`      | Chuỗi văn bản                         | `"Giá trị chữ mặc định"`                   |
| Số (Number)         | `NUMBER`    | Số nguyên hoặc thập phân              | `"9"`                                      |
| Boolean             | `BOOLEAN`   | Đúng/Sai                              | `"true"` hoặc `"false"`                    |
| Ngày (Date)         | `DATE`      | Ngày (không có giờ)                   | `"2026-02-11"`                             |
| Ngày giờ (DateTime) | `DATE_TIME` | Ngày và giờ                           | `"1770573600000"` (timestamp milliseconds) |
| Bản ghi (Record)    | `RECORD`    | Tham chiếu đến bản ghi trong hệ thống | (không có defaultValue)                    |

### Đơn giá trị vs Nhiều giá trị

- **Đơn giá trị** (`isList: false`): biến chứa một giá trị duy nhất
- **Nhiều giá trị** (`isList: true`): biến chứa mảng nhiều giá trị

### Cấu trúc Variable trong `resources.custom`

Variable được lưu trong mảng `resources.custom` với `type: 1`:

```json
{
  "resources": {
    "custom": [
      {
        "absoluteSlug": "$flow.{variable_slug}",
        "parentMetadata": "",
        "defaultValue": "{GIA_TRI_MAC_DINH hoặc DUONG_DAN_THAM_CHIEU}",
        "editable": true,
        "dataType": "{DATA_TYPE}",
        "description": "",
        "refAbsoluteSlug": "{DUONG_DAN_THAM_CHIEU nếu defaultValue là biến/resource}",
        "refAbsolutePath": "{TEN_HIEN_THI_DUONG_DAN nếu defaultValue là biến/resource}",
        "type": 1,
        "isList": false,
        "parentId": "{PROCESS_ID}",
        "assignable": true,
        "availableForInput": true,
        "isStandard": false,
        "processId": "{PROCESS_ID}",
        "name": "{TEN_BIEN}",
        "metaDataType": { ... },
        "availableForOutput": true,
        "absolutePath": "workflow_resource:list.variable / {TEN_BIEN}",
        "id": "{RESOURCE_ID}",
        "parentTable": "process",
        "slug": "{variable_slug}"
      }
    ]
  }
}
```

### Chi tiết các trường quan trọng

| Trường               | Giá trị                                    | Mô tả                                                   |
|----------------------|--------------------------------------------|---------------------------------------------------------|
| `type`               | `1`                                        | Loại resource: Variable (khác với Text Template là `4`) |
| `absoluteSlug`       | `$flow.{slug}`                             | Đường dẫn tham chiếu (prefix `$flow.`)                  |
| `absolutePath`       | `workflow_resource:list.variable / {Name}` | Tên hiển thị đường dẫn                                  |
| `defaultValue`       | Tùy kiểu dữ liệu                           | Giá trị mặc định: có thể là giá trị tĩnh (ví dụ: `"9"`) hoặc tham chiếu biến/resource (ví dụ: `"$userTask.Root.so_a"`) |
| `refAbsoluteSlug`    | `$userTask.{slug}.{field}` (nếu có)        | Đường dẫn tham chiếu nguồn khi defaultValue là biến/resource |
| `refAbsolutePath`    | `workflow_resource:list.userTask / ...` (nếu có) | Tên hiển thị đường dẫn nguồn khi defaultValue là biến/resource |
| `editable`           | `true`                                     | Có thể chỉnh sửa                                        |
| `assignable`         | `true`                                     | Có thể gán giá trị                                      |
| `availableForInput`  | `true`/`false`                             | Cho phép nhận giá trị từ quy trình cha                  |
| `availableForOutput` | `true`/`false`                             | Cho phép quy trình cha truy xuất giá trị                |
| `isList`             | `true`/`false`                             | Đơn giá trị hoặc nhiều giá trị                          |
| `parentTable`        | `"process"`                                | Thuộc về process                                        |
| `isStandard`         | `false`                                    | Không phải resource chuẩn                               |
| `id`                 | prefix `RS` + suffix chữ-số duy nhất        | ID resource                                             |

### Template theo từng kiểu dữ liệu

#### 1. Biến chữ (TEXT) - đơn giá trị
```json
{
  "absoluteSlug": "$flow.bien_chu_text_mot_gia_tri",
  "parentMetadata": "",
  "defaultValue": "Giá trị chữ mặc định",
  "editable": true,
  "dataType": "TEXT",
  "description": "",
  "type": 1,
  "isList": false,
  "parentId": "{PROCESS_ID}",
  "assignable": true,
  "availableForInput": true,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "Biến chữ (text): một gía trị",
  "metaDataType": {
    "characterLimit": {
      "min": 0,
      "max": 131072,
      "warning": "warning limit note"
    },
    "richText": "false"
  },
  "availableForOutput": true,
  "absolutePath": "workflow_resource:list.variable / Biến chữ (text): một gía trị",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "slug": "bien_chu_text_mot_gia_tri"
}
```

#### 2. Biến chữ (TEXT) - nhiều giá trị
```json
{
  "absoluteSlug": "$flow.bien_chu_text_nhieu_gia_tri",
  "parentMetadata": "",
  "defaultValue": "",
  "editable": true,
  "dataType": "TEXT",
  "description": "",
  "type": 1,
  "isList": true,
  "parentId": "{PROCESS_ID}",
  "assignable": true,
  "availableForInput": true,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "Biến chữ (text): nhiều gía trị",
  "metaDataType": {
    "characterLimit": {
      "min": 0,
      "max": 131072,
      "warning": "warning limit note"
    },
    "richText": "false"
  },
  "availableForOutput": true,
  "absolutePath": "workflow_resource:list.variable / Biến chữ (text): nhiều gía trị",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "slug": "bien_chu_text_nhieu_gia_tri"
}
```

#### 3. Biến số (NUMBER) - đơn giá trị
```json
{
  "absoluteSlug": "$flow.bien_so_number_mot_gia_tri",
  "parentMetadata": "",
  "defaultValue": "9",
  "editable": true,
  "dataType": "NUMBER",
  "description": "",
  "type": 1,
  "isList": false,
  "parentId": "{PROCESS_ID}",
  "assignable": true,
  "availableForInput": true,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "Biến số (number): một gía trị",
  "metaDataType": {
    "valueLimit": {
      "min": -9999999999.999998,
      "max": 9999999999.999998,
      "warning": "warning limit note"
    },
    "displayType": 2,
    "multipleLimit": {
      "min": 1,
      "max": 30,
      "warning": "warning limit note"
    },
    "format": {
      "format": 2,
      "type": 1
    },
    "integralLength": 14,
    "roundRule": "1"
  },
  "availableForOutput": true,
  "absolutePath": "workflow_resource:list.variable / Biến số (number): một gía trị",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "slug": "bien_so_number_mot_gia_tri"
}
```

#### 4. Biến số (NUMBER) - nhiều giá trị
Giống biến số đơn giá trị nhưng `isList: true`.

#### 5. Biến boolean (BOOLEAN) - đơn giá trị
```json
{
  "absoluteSlug": "$flow.bien_boolean_1_gia_tri",
  "parentMetadata": "",
  "defaultValue": "true",
  "editable": true,
  "dataType": "BOOLEAN",
  "description": "",
  "type": 1,
  "isList": false,
  "parentId": "{PROCESS_ID}",
  "assignable": true,
  "availableForInput": true,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "Biến boolean 1 giá trị",
  "metaDataType": {
    "falseValue": "Không",
    "trueValue": "Có",
    "language": "vi-VN"
  },
  "availableForOutput": true,
  "absolutePath": "workflow_resource:list.variable / Biến boolean 1 giá trị",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "slug": "bien_boolean_1_gia_tri"
}
```

#### 6. Biến boolean (BOOLEAN) - nhiều giá trị
Giống biến boolean đơn giá trị nhưng `isList: true`.

#### 7. Biến ngày (DATE) - đơn giá trị
```json
{
  "absoluteSlug": "$flow.bien_ngay_date_1_gia_tri",
  "parentMetadata": "",
  "defaultValue": "2026-02-11",
  "editable": true,
  "dataType": "DATE",
  "description": "",
  "type": 1,
  "isList": false,
  "parentId": "{PROCESS_ID}",
  "assignable": true,
  "availableForInput": true,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "Biến ngày (date): 1 giá trị",
  "metaDataType": {
    "defaultValueCurrent": false,
    "multipleLimit": {
      "min": 0,
      "max": 30,
      "warning": "warning limit note"
    },
    "format": {
      "format": "dd/MM/yyyy"
    }
  },
  "availableForOutput": true,
  "absolutePath": "workflow_resource:list.variable / Biến ngày (date): 1 giá trị",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "slug": "bien_ngay_date_1_gia_tri"
}
```

#### 8. Biến ngày giờ (DATE_TIME) - đơn giá trị
```json
{
  "absoluteSlug": "$flow.bien_ngay_gio_datetime_1_gia_tri",
  "parentMetadata": "",
  "defaultValue": "1770573600000",
  "editable": true,
  "dataType": "DATE_TIME",
  "description": "",
  "type": 1,
  "isList": false,
  "parentId": "{PROCESS_ID}",
  "assignable": true,
  "availableForInput": true,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "Biến ngày giờ (datetime): 1 gía trị",
  "metaDataType": {
    "defaultValueCurrent": false,
    "format": {
      "date": "dd/MM/yyyy",
      "time": "hh:mm:ss"
    },
    "timeZone": "Asia/Saigon"
  },
  "availableForOutput": true,
  "absolutePath": "workflow_resource:list.variable / Biến ngày giờ (datetime): 1 gía trị",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "slug": "bien_ngay_gio_datetime_1_gia_tri"
}
```

#### 9. Biến bản ghi (RECORD) - đơn giá trị
```json
{
  "absoluteSlug": "$flow.bien_ban_ghi_lead_1_gia_tri",
  "parentMetadata": "",
  "editable": true,
  "dataType": "RECORD",
  "description": "",
  "type": 1,
  "isList": false,
  "parentId": "{PROCESS_ID}",
  "assignable": true,
  "availableForInput": true,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "Biến bản ghi Lead: 1 giá trị",
  "metaDataType": {
    "linkField": "id",
    "objectSlug": "lead",
    "object": "OT00000000011"
  },
  "availableForOutput": true,
  "absolutePath": "workflow_resource:list.variable / Biến bản ghi Lead: 1 giá trị",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "slug": "bien_ban_ghi_lead_1_gia_tri"
}
```

**Lưu ý:**
- Biến RECORD không có `defaultValue` (vì giá trị là tham chiếu đến bản ghi).
- `metaDataType.object` (objectTypeId) và `metaDataType.objectSlug` **BẮT BUỘC** lấy từ skill `/object-info` (xem mục 25 trong Lưu ý quan trọng). Ví dụ `OT00000000011`/`lead` ở trên chỉ là minh họa.

#### 10. Biến bản ghi (RECORD) - nhiều giá trị
Giống biến RECORD đơn giá trị nhưng `isList: true`.

### Giá trị mặc định từ biến/resource

Variable có thể nhận giá trị mặc định từ một biến hoặc resource khác (ví dụ: từ trường trong userTask). Khi đó, cần thêm 2 trường:
- `refAbsoluteSlug`: đường dẫn tham chiếu nguồn (giống `defaultValue`)
- `refAbsolutePath`: tên hiển thị đường dẫn nguồn

#### Ví dụ: Biến số nhận giá trị mặc định từ trường Số A trong userTask Root
```json
{
  "absoluteSlug": "$flow.bien_so",
  "parentMetadata": "",
  "defaultValue": "$userTask.Root.so_a",
  "editable": true,
  "dataType": "NUMBER",
  "description": "",
  "refAbsoluteSlug": "$userTask.Root.so_a",
  "refAbsolutePath": "workflow_resource:list.userTask / Root / Số A",
  "type": 1,
  "isList": false,
  "parentId": "{PROCESS_ID}",
  "assignable": true,
  "availableForInput": false,
  "isStandard": false,
  "processId": "{PROCESS_ID}",
  "name": "Biến số",
  "metaDataType": {
    "valueLimit": {
      "min": -9999999999.999998,
      "max": 9999999999.999998,
      "warning": "warning limit note"
    },
    "displayType": 2,
    "multipleLimit": {
      "min": 1,
      "max": 30,
      "warning": "warning limit note"
    },
    "format": {
      "format": 2,
      "type": 1
    },
    "integralLength": 14,
    "roundRule": "1"
  },
  "availableForOutput": false,
  "absolutePath": "workflow_resource:list.variable / Biến số",
  "id": "{RESOURCE_ID}",
  "parentTable": "process",
  "slug": "bien_so"
}
```

**Lưu ý:**
- `defaultValue` = đường dẫn tham chiếu (ví dụ: `$userTask.Root.so_a`, `$flow.bien_khac`)
- `refAbsoluteSlug` = giống giá trị `defaultValue`
- `refAbsolutePath` = tên hiển thị đường dẫn theo format `workflow_resource:list.{loại} / {Tên nguồn} / {Tên trường}`
- Khi biến tham chiếu đến trường trong userTask: `refAbsolutePath` = `workflow_resource:list.userTask / {TaskName} / {FieldName}`
- Khi biến tham chiếu đến biến khác: `refAbsolutePath` = `workflow_resource:list.variable / {TênBiến}`
- Resource của trường nguồn (trong `resources.userTasks[].resources[]`) cần có `resourcesUsedIn` trỏ đến biến đó:
```json
{
  "resourcesUsedIn": [
    {
      "dataType": "NUMBER",
      "name": "Biến số",
      "count": 1,
      "id": "{VARIABLE_RESOURCE_ID}",
      "parentTable": "resource",
      "slug": "bien_so"
    }
  ]
}
```

### Sử dụng Variable làm giá trị mặc định trong userTask

Khi một trường trong userTask dùng Variable làm giá trị mặc định, cần cấu hình:

#### Trong component của userTask (mảng `content`)
Thêm các trường sau vào component:
```json
{
  "defaultValue": "$flow.{variable_slug}",
  "defaultValueDataType": "{DATA_TYPE}",
  "defaultValuePathName": "workflow_resource:list.variable / {TEN_BIEN}"
}
```

- `defaultValue`: đường dẫn tham chiếu biến, format `$flow.{variable_slug}`
- `defaultValueDataType`: kiểu dữ liệu của biến (TEXT, NUMBER, BOOLEAN, DATE, DATE_TIME, RECORD)
- `defaultValuePathName`: tên hiển thị đường dẫn, format `workflow_resource:list.variable / {Tên biến}`

#### Giá trị `defaultTextValueType` trong resource của component
Khi resource của component (trong `resources.userTasks[].resources[]`) có defaultValue từ biến:
- `defaultTextValueType: 4` cho trường text (short_text, long_text) khi giá trị đến từ biến
- `defaultTextValueType: 0` cho các trường không phải text (numeric, boolean, date, date_time, lookup_normal)

#### Giá trị `defaultValueRecord` cho trường lookup
Khi trường `lookup_normal` có `defaultValue` là biến/resource:
- **`defaultValueRecord: 0`**: giá trị mặc định đến từ biến/resource (ví dụ: `$flow.xxx`, `$action.xxx.output.record`)
- **`defaultValueRecord: 1`**: không có giá trị mặc định từ biến (người dùng tự nhập/chọn)

> Nếu set sai `defaultValueRecord: 1` cho trường lookup có defaultValue từ biến, layout sẽ bị lỗi hiển thị.

#### Ví dụ component với Variable làm giá trị mặc định

**Trường text với biến TEXT:**
```json
{
  "manualModifyAllow": true,
  "defaultValue": "$flow.bien_chu_text_mot_gia_tri",
  "description": "",
  "uiSlug": "_1",
  "required": 0,
  "defaultValueDataType": "TEXT",
  "defaultValuePathName": "workflow_resource:list.variable / Biến chữ (text): một gía trị",
  "availableForInput": false,
  "fieldMetaData": {
    "character_limit": { "min": 0, "max": 255 },
    "multiple_limit": { "min": 0, "max": 30 }
  },
  "options": [],
  "id": "uuid",
  "defaultTextValueType": 4,
  "slug": "van_ban_ngan",
  "multiple": 0,
  "toolTip": "",
  "readOnly": null,
  "label": "",
  "isStandard": 0,
  "hintText": "",
  "disable": null,
  "unique": false,
  "name": "Van ban ngan",
  "availableForOutput": false,
  "fieldType": "short_text",
  "status": 1
}
```

**Trường số với biến NUMBER:**
```json
{
  "manualModifyAllow": true,
  "defaultValue": "$flow.bien_so_number_mot_gia_tri",
  "defaultValueDataType": "NUMBER",
  "defaultValuePathName": "workflow_resource:list.variable / Biến số (number): một gía trị",
  "fieldType": "numeric",
  ...
}
```

**Trường boolean với biến BOOLEAN:**
```json
{
  "manualModifyAllow": true,
  "defaultValue": "$flow.bien_boolean_1_gia_tri",
  "defaultValueDataType": "BOOLEAN",
  "defaultValuePathName": "workflow_resource:list.variable / Biến boolean 1 giá trị",
  "fieldType": "boolean",
  ...
}
```

**Trường lookup với biến RECORD:**
```json
{
  "manualModifyAllow": true,
  "defaultValue": "$flow.bien_ban_ghi_lead_1_gia_tri",
  "defaultValueDataType": "RECORD",
  "defaultValuePathName": "workflow_resource:list.variable / Biến bản ghi Lead: 1 giá trị",
  "fieldType": "lookup_normal",
  "defaultValueRecord": 0,
  ...
}
```

**Trường date với biến DATE:**
```json
{
  "manualModifyAllow": true,
  "defaultValue": "$flow.bien_ngay_date_1_gia_tri",
  "defaultValueDataType": "DATE",
  "defaultValuePathName": "workflow_resource:list.variable / Biến ngày (date): 1 giá trị",
  "fieldType": "date",
  ...
}
```

**Trường datetime với biến DATE_TIME:**
```json
{
  "manualModifyAllow": true,
  "defaultValue": "$flow.bien_ngay_gio_datetime_1_gia_tri",
  "defaultValueDataType": "DATE_TIME",
  "defaultValuePathName": "workflow_resource:list.variable / Biến ngày giờ (datetime): 1 gía trị",
  "fieldType": "date_time",
  ...
}
```

### Resource của component khi dùng Variable

Trong `resources.userTasks[].resources[]`, resource của component cũng lưu thông tin defaultValue:
```json
{
  "absoluteSlug": "$userTask.Root.van_ban_ngan",
  "parentMetadata": "",
  "defaultValue": "$flow.bien_chu_text_mot_gia_tri",
  "dataType": "TEXT",
  "description": "",
  "type": 1,
  "isList": false,
  "parentId": "{NODE_CONFIG_ID}",
  "availableForInput": false,
  "isStandard": true,
  "processId": "{PROCESS_ID}",
  "name": "Van ban ngan",
  "metaDataType": { ... },
  "availableForOutput": false,
  "absolutePath": "workflow_resource:list.userTask / Root / Van ban ngan",
  "id": "{SCREEN_ID}",
  "parentTable": "node_screen",
  "defaultTextValueType": 4,
  "slug": "van_ban_ngan",
  "fieldId": "{COMPONENT_UUID}",
  "isComponent": true
}
```

### resourcesUsedIn của Variable

Khi một Variable được sử dụng làm giá trị mặc định cho component trong userTask, cần thêm `resourcesUsedIn` vào Variable đó:

```json
{
  "resourcesUsedIn": [
    {
      "name": "{USER_TASK_NAME}",
      "count": 1,
      "id": "{NODE_CONFIG_ID}",
      "parentTable": "node_screen",
      "slug": "{user_task_slug}"
    }
  ]
}
```

**Ví dụ:** Khi biến `$flow.bien_chu_text_mot_gia_tri` được dùng trong component "Van ban ngan" ở task Root:
```json
{
  "resourcesUsedIn": [
    {
      "name": "Root",
      "count": 1,
      "id": "NC00000000004",
      "parentTable": "node_screen",
      "slug": "Root"
    }
  ]
}
```

**Lưu ý:**
- `parentTable` = `"node_screen"` (vì được sử dụng trong screen của user task)
- `id` = ID cấu hình node (NC prefix) của userTask
- Nếu biến được sử dụng trong nhiều userTask, có nhiều entry trong mảng `resourcesUsedIn`

---

## Formula / Scripting (Công thức tính)

### Mô tả
Formula (Công thức) là một resource tùy chỉnh (custom resource) cho phép viết các đoạn mã kịch bản (scripting) để tính toán, xử lý dữ liệu và logic nghiệp vụ. Formula sử dụng cú pháp dựa trên **Apache JEXL** (Cogover Scripting), cho phép:
- Nhận biến/dữ liệu từ các resource khác trong quy trình (userTask fields, system variables, action outputs, ...)
- Thực hiện tính toán, xử lý chuỗi, xử lý ngày tháng, thao tác JSON, ...
- Trả về một giá trị với kiểu dữ liệu được định nghĩa sẵn (TEXT, NUMBER, BOOLEAN, DATE, DATE_TIME)

Formula thường được dùng khi cần xử lý dữ liệu phức tạp mà các biến (Variable) hoặc phép gán (Assignment) đơn giản không đáp ứng được. Ví dụ: tạo JSON body cho HTTP request, tính toán công thức nghiệp vụ, ghép chuỗi có logic điều kiện.

### Cú pháp Cogover Scripting

Tham khảo đầy đủ: `FORMULA_API_REFERENCE-VI.md`

#### Biến từ resource
```javascript
$userTask.Root.text_1           // Trường text_1 từ User Task "Root"
$userTask.Root.number_1         // Trường number_1 từ User Task "Root"
$userTask.Root.submittedBy.account_email  // Trường con của lookup
$flow.instance.name             // System resource
$action.send_http.output.body   // Output của action
```

#### Khai báo biến và return
```javascript
var data = {
    "name": $userTask.Root.text_1,
    "age": $userTask.Root.number_1,
    "submittedByEmail": $userTask.Root.submittedBy.account_email
};
return Json.stringify(data);
```

#### Hàm hỗ trợ (ví dụ)
```javascript
// Text
Text.concat("Hello", " ", "World")
Text.upper($userTask.Root.text_1)

// Number & Math
Math.round(3.7)
Math.max(10, 20)

// Date
Date.now()
Date.format($userTask.Root.ngay, "dd/MM/yyyy")

// JSON
Json.stringify(data)
Json.parse(jsonString)

// Điều kiện
if ($userTask.Root.number_1 > 10) { return "Lớn"; } else { return "Nhỏ"; }

// Vòng lặp
for (var item : list) { ... }
```

### Cấu trúc Formula trong `resources.custom`

Formula được lưu trong mảng `resources.custom` với `type: 3`:

```json
{
  "resources": {
    "custom": [
      {
        "absoluteSlug": "$flow.{formula_slug}",
        "parentMetadata": "",
        "defaultValue": "var data = {\n    \"name\": $userTask.Root.text_1,\n    \"age\": $userTask.Root.number_1\n};\nreturn Json.stringify(data);",
        "editable": true,
        "dataType": "TEXT",
        "description": "",
        "type": 3,
        "isList": false,
        "parentId": "{PROCESS_ID}",
        "assignable": false,
        "availableForInput": false,
        "isStandard": false,
        "processId": "{PROCESS_ID}",
        "name": "{FORMULA_NAME}",
        "metaDataType": {
          "convertNullNumberToZero": true,
          "richText": 1,
          "convertNullStringToEmpty": true
        },
        "availableForOutput": false,
        "absolutePath": "workflow_resource:list.formula / {FORMULA_NAME}",
        "id": "{RESOURCE_ID}",
        "parentTable": "process",
        "resourcesUsedIn": [],
        "slug": "{formula_slug}"
      }
    ]
  }
}
```

### Chi tiết các trường quan trọng

| Trường                                  | Giá trị                                     | Mô tả                                      |
|-----------------------------------------|---------------------------------------------|---------------------------------------------|
| `type`                                  | `3`                                         | Loại resource: Formula/Scripting            |
| `dataType`                              | `"TEXT"`, `"NUMBER"`, `"BOOLEAN"`, `"DATE"`, `"DATE_TIME"` | Kiểu dữ liệu trả về của công thức |
| `absoluteSlug`                          | `$flow.{slug}`                              | Đường dẫn tham chiếu (prefix `$flow.`)      |
| `absolutePath`                          | `workflow_resource:list.formula / {Name}`   | Tên hiển thị đường dẫn                      |
| `defaultValue`                          | Mã nguồn Cogover Scripting (JEXL)           | Nội dung công thức (code)                   |
| `metaDataType`                          | Metadata đúng với `dataType`                 | Không dùng metadata TEXT cho NUMBER/BOOLEAN/DATE/DATE_TIME |
| `assignable`                            | `false`                                     | Không thể gán giá trị (chỉ đọc, tính toán) |
| `availableForInput`                     | `false`                                     | Không nhận giá trị đầu vào                  |
| `availableForOutput`                    | `false`                                     | Không trả giá trị đầu ra cho quy trình cha |
| `parentTable`                           | `"process"`                                 | Thuộc về process                            |
| `isStandard`                            | `false`                                     | Không phải resource chuẩn                   |
| `id`                                    | prefix `RS` + suffix chữ-số duy nhất         | ID resource                                |

### Quy tắc tạo ID
- ID Formula Resource dùng prefix `RS` và suffix chữ-số duy nhất (ví dụ: `RS00000000094`).

### Metadata Formula theo kiểu trả về

Ví dụ trên là Formula `TEXT`; chỉ `TEXT` dùng `richText`, `convertNullStringToEmpty` và `convertNullNumberToZero`. Với kiểu khác, dùng metadata canonical của đúng data type, giống một Variable cùng kiểu trên workspace:

- `NUMBER`: dùng metadata số như dưới đây; không gửi `richText`:

  ```json
  {
    "valueLimit": {"min": -9999999999.999998, "max": 9999999999.999998, "warning": "warning limit note"},
    "displayType": 2,
    "multipleLimit": {"min": 1, "max": 30, "warning": "warning limit note"},
    "format": {"format": 2, "type": 1},
    "integralLength": 14,
    "roundRule": "1"
  }
  ```
- `BOOLEAN`: metadata boolean canonical; không gửi metadata text hoặc number.
- `DATE`/`DATE_TIME`: metadata ngày/giờ canonical gồm format/timezone phù hợp; không gửi `richText`.

Trước POST, đối chiếu `dataType` và `metaDataType`. Lỗi `Config object field metadata for resource is invalid` là lỗi metadata type, không phải lỗi code Formula.

### Sử dụng Formula trong các action

Formula được tham chiếu bằng cú pháp `$flow.{formula_slug}`. Ví dụ khi dùng làm request body cho Send HTTP Request:

```json
{
  "requestBody": {
    "valuePathName": "workflow_resource:list.formula / Formula 1",
    "valueDataType": "TEXT",
    "type": 4,
    "value": "$flow.formula_1"
  }
}
```

**Lưu ý:** `type: 4` trong `requestBody` nghĩa là giá trị lấy từ resource (biến/formula/text template), không phải giá trị cố định.

### resourcesUsedIn của Formula

Khi Formula được sử dụng trong một action (ví dụ: Send HTTP Request), cần thêm `resourcesUsedIn`:

```json
{
  "resourcesUsedIn": [
    {
      "actionType": "SEND_HTTP_REQUEST",
      "name": "Send http",
      "count": 1,
      "id": "{ACTION_ID}",
      "parentTable": "action",
      "slug": "{action_slug}"
    }
  ]
}
```

### resourcesUsedIn của trường được dùng trong Formula

Khi một trường của userTask được sử dụng trong nội dung Formula (ví dụ: `$userTask.Root.text_1`), cần thêm `resourcesUsedIn` vào resource của trường đó:

```json
{
  "resourcesUsedIn": [
    {
      "dataType": "TEXT",
      "name": "Formula 1",
      "count": 1,
      "id": "{FORMULA_RESOURCE_ID}",
      "parentTable": "resource",
      "slug": "{formula_slug}"
    }
  ]
}
```

### externalResourcesUsedIn

Khi sử dụng các trường con của lookup trong Formula (ví dụ: `$userTask.Root.submittedBy.account_email`), cần thêm vào mảng `externalResourcesUsedIn` ở root level:

```json
{
  "externalResourcesUsedIn": [
    {
      "absoluteSlug": "$userTask.Root.submittedBy.account_email",
      "parentMetadata": "",
      "dataType": "TEXT",
      "type": 1,
      "isList": false,
      "parentId": "{LOOKUP_RESOURCE_ID}",
      "isSystem": false,
      "availableForInput": false,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "name": "Account email",
      "availableForOutput": false,
      "absolutePath": "workflow_resource:list.userTask / Root / Submitted By / Account email",
      "parentTable": "resource",
      "slug": "account_email"
    }
  ]
}
```

**Lưu ý:**
- `parentId` = ID của resource lookup cha (ví dụ: ID của resource `submittedBy`)
- `parentTable` = `"resource"` (vì là trường con của resource lookup, không phải screen component)
- `absolutePath` theo format: `workflow_resource:list.userTask / {TaskName} / {LookupFieldName} / {SubFieldName}`

### So sánh Formula với Variable và Text Template

| Đặc điểm         | Variable (`type: 1`)          | Formula (`type: 3`)                    | Text Template (`type: 4`)        |
|-------------------|-------------------------------|----------------------------------------|----------------------------------|
| Mục đích          | Lưu trữ giá trị              | Tính toán, xử lý dữ liệu              | Tạo nội dung văn bản/HTML        |
| Ngôn ngữ          | Không có (giá trị tĩnh/gán)  | Cogover Scripting (Apache JEXL)        | Apache Velocity Template (VTL)   |
| `assignable`      | `true`                        | `false`                                | `false`                          |
| `defaultValue`    | Giá trị tĩnh hoặc tham chiếu | Mã nguồn scripting                     | Nội dung HTML/VTL                |
| `absolutePath`    | `list.variable / {Name}`     | `list.formula / {Name}`               | `list.textTemplate / {Name}`    |
| Kiểu dữ liệu trả về | Tùy chọn                  | Tùy chọn (TEXT, NUMBER, BOOLEAN, ...) | Luôn là TEXT                     |
| Có thể ghi bằng Assignment | Có               | Không                                  | Không                            |

### File mẫu
- Mẫu Formula: `samples/sample_formula.json` (User Task → Send HTTP Request với post body là Formula)

---

## Text Template (Mẫu Văn Bản)

### Mô tả
Text Template là một resource tùy chỉnh (custom resource) cho phép tạo nội dung văn bản/HTML có hỗ trợ biến động. Text Template sử dụng cú pháp **Apache Velocity Template Language (VTL)** để render biến, điều kiện, vòng lặp.

Text Template thường được dùng làm nội dung body, tiêu đề của email, thay vì viết nội dung HTML trực tiếp trong action email.

### Cú pháp Apache Velocity Template Language

Tham khảo đầy đủ: `text-template-api-reference-vi.md`

#### 1. Biến (Variables)
```
$userTask.Root.chon_lead.last_first_name
$userTask.Root.chon_lead.company
$flow.instance.name
```

#### 2. If / ElseIf / Else
```
#if($userTask.Root.chon_lead.company)
  Công ty: $userTask.Root.chon_lead.company
#elseif($userTask.Root.chon_lead.last_first_name)
  Cá nhân: $userTask.Root.chon_lead.last_first_name
#else
  Không có thông tin
#end
```

#### 3. Foreach Loop
```
#foreach($item in $userTask.Root.danh_sach)
  - $item.name
#end
```

#### 4. Set (Gán biến)
```
#set($greeting = "Xin chào")
$greeting $userTask.Root.chon_lead.last_first_name
```

### Cấu trúc Text Template trong `resources.custom`

Text Template được lưu trong mảng `resources.custom` ở JSON:

```json
{
  "resources": {
    "custom": [
      {
        "absoluteSlug": "$flow.{text_template_slug}",
        "parentMetadata": "",
        "defaultValue": "<div>Nội dung HTML với biến VTL, ví dụ: $userTask.Root.chon_lead.last_first_name</div>",
        "editable": true,
        "dataType": "TEXT",
        "description": "",
        "type": 4,
        "isList": false,
        "parentId": "{PROCESS_ID}",
        "assignable": false,
        "availableForInput": false,
        "isStandard": false,
        "processId": "{PROCESS_ID}",
        "name": "{TEXT_TEMPLATE_NAME}",
        "metaDataType": {
          "convertNullNumberToZero": true,
          "richText": 1,
          "convertNullStringToEmpty": true
        },
        "availableForOutput": false,
        "absolutePath": "workflow_resource:list.textTemplate / {TEXT_TEMPLATE_NAME}",
        "id": "{RESOURCE_ID}",
        "parentTable": "process",
        "resourcesUsedIn": [],
        "slug": "{text_template_slug}"
      }
    ]
  }
}
```

### Chi tiết các trường quan trọng

| Trường                                  | Giá trị                                        | Mô tả                                  |
|-----------------------------------------|------------------------------------------------|----------------------------------------|
| `type`                                  | `4`                                            | Loại resource: Text Template           |
| `dataType`                              | `"TEXT"`                                       | Kiểu dữ liệu                           |
| `absoluteSlug`                          | `$flow.{slug}`                                 | Đường dẫn tham chiếu (prefix `$flow.`) |
| `absolutePath`                          | `workflow_resource:list.textTemplate / {Name}` | Tên hiển thị đường dẫn                 |
| `defaultValue`                          | Nội dung HTML/VTL                              | Nội dung mẫu với biến VTL              |
| `metaDataType.richText`                 | `1`                                            | Hỗ trợ HTML/rich text                  |
| `metaDataType.convertNullNumberToZero`  | `true`                                         | Chuyển số null thành 0                 |
| `metaDataType.convertNullStringToEmpty` | `true`                                         | Chuyển chuỗi null thành rỗng           |
| `parentTable`                           | `"process"`                                    | Thuộc về process                       |
| `isStandard`                            | `false`                                        | Không phải resource chuẩn              |
| `id`                                    | prefix `RS` + suffix chữ-số duy nhất            | ID resource                            |

### Quy tắc tạo ID
- ID Text Template Resource dùng prefix `RS` và suffix chữ-số duy nhất (ví dụ: `RS00000000041`).

### resourcesUsedIn của Text Template

Khi Text Template được sử dụng trong một action (ví dụ: Send Email), cần thêm `resourcesUsedIn`:

```json
{
  "resourcesUsedIn": [
    {
      "actionType": "SEND_EMAIL",
      "name": "Gửi email cho Lead đã chọn ở Root",
      "count": 1,
      "id": "{ACTION_ID}",
      "parentTable": "action",
      "slug": "{action_slug}"
    }
  ]
}
```

### resourcesUsedIn của trường được dùng trong Text Template

Khi một trường của userTask được sử dụng trong nội dung Text Template (ví dụ: `$userTask.Root.chon_lead`), cần thêm `resourcesUsedIn` vào resource của trường đó với 2 entry:

1. Entry cho action sử dụng Text Template:
```json
{
  "actionType": "SEND_EMAIL",
  "name": "Gửi email cho Lead đã chọn ở Root",
  "count": 2,
  "id": "{ACTION_ID}",
  "parentTable": "action",
  "slug": "{action_slug}"
}
```

2. Entry cho chính Text Template:
```json
{
  "dataType": "TEXT",
  "name": "Body email",
  "count": 2,
  "id": "{TEXT_TEMPLATE_RESOURCE_ID}",
  "parentTable": "resource",
  "slug": "{text_template_slug}"
}
```

### externalResourcesUsedIn

Khi sử dụng các trường con của lookup trong Text Template (ví dụ: `$userTask.Root.chon_lead.last_first_name`, `$userTask.Root.chon_lead.company`), cần thêm vào mảng `externalResourcesUsedIn` ở root level:

```json
{
  "externalResourcesUsedIn": [
    {
      "absoluteSlug": "$userTask.Root.chon_lead.last_first_name",
      "parentMetadata": "",
      "dataType": "TEXT",
      "type": 1,
      "isList": false,
      "parentId": "{LOOKUP_RESOURCE_ID}",
      "isSystem": false,
      "availableForInput": false,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "name": "Last first name",
      "availableForOutput": false,
      "absolutePath": "workflow_resource:list.userTask / Root / Chọn Lead / Last first name",
      "parentTable": "screen_component",
      "slug": "last_first_name"
    },
    {
      "absoluteSlug": "$userTask.Root.chon_lead.company",
      "parentMetadata": "",
      "dataType": "TEXT",
      "type": 1,
      "isList": false,
      "parentId": "{LOOKUP_RESOURCE_ID}",
      "isSystem": false,
      "availableForInput": false,
      "isStandard": true,
      "processId": "{PROCESS_ID}",
      "name": "Company",
      "availableForOutput": false,
      "absolutePath": "workflow_resource:list.userTask / Root / Chọn Lead / Company",
      "parentTable": "screen_component",
      "slug": "company"
    }
  ]
}
```

**Lưu ý:**
- `parentId` = ID của resource lookup (ví dụ: ID của resource `chon_lead`)
- `parentTable` = `"screen_component"` (vì là trường con của component trong screen)
- `absolutePath` theo format: `workflow_resource:list.userTask / {TaskName} / {LookupFieldName} / {SubFieldName}`

### Ví dụ nội dung Text Template

```html
<div>Chào anh/chị $userTask.Root.chon_lead.last_first_name,</div>

<div>&nbsp;</div>

<div>Qua tìm hiểu, em thấy $userTask.Root.chon_lead.company đang mở rộng đội sales.</div>

<ul>
	<li>Quy trình phân tán, nhiều file Excel / phần mềm rời rạc.</li>
	<li>CRM hoặc ERP khó tùy chỉnh theo thực tế vận hành.</li>
</ul>

<div>Trân trọng,</div>
```

---


## File tham khảo

Một số sample là snapshot response/legacy và có thể chứa action ID đã được server remap (`AC...`) hoặc field chỉ có trong response. Khi dùng để tạo mới, lấy contract trong `SKILL.md`/`nodes/*.md` làm canonical, bỏ response envelope/field server-owned và đặt `action.id === action.nodeId ===` BPMN node ID.

- Mẫu Manual Flow 1: samples/sample_process_1.json (3 node + bắt đầu/kết thúc)
- Mẫu Manual Flow 2: samples/sample_process_2.json (4 node + bắt đầu/kết thúc)
- Mẫu Exclusive Gateway: samples/sample_process_exclusive_gw.json (Exclusive Gateway với 2 nhánh)
- Mẫu Exclusive Gateway Conditions: samples/sample_process_gw_conditions.json (Exclusive Gateway với điều kiện chi tiết)
- Mẫu Inclusive Gateway: samples/sample_inclusive_gateway.json (Inclusive Gateway)
- Mẫu Parallel Gateway: samples/sample_process_parallel_gw.json (Parallel Gateway)
- Mẫu User Task Full: samples/sample_process_user_task_full.json (User Task với form chứa nhiều loại trường)
- Mẫu Send Email: samples/sample_process_usertask_send_email.json (User Task -> Send Email Task)
- Mẫu Send HTTP: samples/sample_send_http_request.json (User Task -> Send HTTP Request Task)
- Mẫu Send Notification: samples/sample_process_send_notification.json (User Task -> Send Notification Task)
- Mẫu Get Record: samples/sample_process_usertask_get_records.json (User Task -> Get Record Task)
- Mẫu Create Record: samples/sample_process_user_task_create_record.json (User Task -> Create Record Task)
- Mẫu Update Record: samples/sample_process_user_task_update_record.json (User Task -> Update Record Task)
- Mẫu Loop: samples/sample_process_loop.json (Loop Task duyệt danh sách Leads)
- Mẫu Text Template: samples/sample_process_text_template.json (Send Email với Text Template sử dụng biến VTL)
- Mẫu Variable: samples/sample_process_variable.json (Variable các kiểu dữ liệu + dùng làm giá trị mặc định cho component)
- Mẫu Assignment: samples/sample_process_assignment.json (Assignment Task gán giá trị cho biến)
- Mẫu Organization: samples/sample_process_organization.json (Organization Task lấy nhân sự quản lý trực tiếp)
- Mẫu Wait email: samples/sample_process_wait.json (Send Email Task + Wait Task với EMAIL_REPLY và LINK_WAS_CLICKED); đọc runtime compatibility trong `nodes/wait-task.md`, không suy ra mọi event trên UI đều chạy được
- Mẫu Sub Process: samples/sample_process_call_sub_process.json (Gọi quy trình con là manual_flow, truyền/nhận biến giữa quy trình cha và con)
- Scheduled Start canonical: nodes/scheduled-start-event.md (8 chu kỳ và validation theo từng loại)
- Mẫu Scheduled Flow: samples/sample_scheduled_flow_1.json (Scheduled Flow)
- Mẫu Triggered Flow (record): samples/sample_triggered_flow.json (Triggered Flow kích hoạt bởi thay đổi bản ghi)
- Mẫu Triggered Flow (webhook): samples/Webhook_triggered_flow.json (Triggered Flow kích hoạt bởi HTTP POST webhook)
- Mẫu Sequence Flow: samples/sample_sequence_flow.json (Sequence Flow)
- Mẫu Formula: samples/sample_formula.json (User Task → Send HTTP Request với post body là Formula/Scripting)
- Mẫu Normal Flow: samples/sample_normal_flow.json (Normal Flow không có Root User Task)
- Mẫu To Do: samples/sample_sequence_flow_todo.json (Sequence Flow với To Do)
- Mẫu Phone Call: samples/sample_phone_call.json (Phone Call bằng text-to-speech)
- Mẫu Export Record: samples/sample_export_record.json (Xuất record bằng document template)
- Mẫu Respond to Webhook: samples/sample_respond_to_webhook.json (schema/migration only; backend hiện chưa chạy action này)
- Mẫu Push Message: samples/sample_push_message.json (Push Message loại TOAST)
- Mẫu JSON to Object: samples/sample_parse_to_object.json (schema/migration only; backend hiện chưa chạy action này)
- Mẫu Omni Message: samples/sample_omni_message.json (Zalo ZBS, action data dạng JSON string)
- Mẫu AI Agent: samples/sample_ai_agent.json (Normal Flow → AI Agent → End Process; agent ID là placeholder, `action.data` dạng JSON string; chưa phải kết quả chạy trên Workspace)
- Mẫu End Branch: samples/sample_end_branch.json (Parallel split với End Branch và End Process)

---

## Lưu ý quan trọng
1. Luôn escape chuỗi XML đúng cách khi nhúng vào JSON
2. Tạo ID duy nhất cho mọi phần tử
3. Chỉ Manual Flow bắt buộc userTask đầu tiên sau Start có `isRoot: true`; Normal/Scheduled/Triggered/Sequence không tự tạo Root
4. Tất cả userTask khác có `isRoot: false`
5. Sử dụng nhãn tiếng Việt cho các nút (Hoàn tác, Hủy, Thực hiện)
6. Sử dụng định dạng timestamp phù hợp cho các trường created/updated
7. Với Exclusive Gateway:
   - Quy tắc nhánh mặc định chỉ áp dụng cho **fork/open gateway** (`isOpen: true`, 1 incoming, nhiều outgoing): bắt buộc có nhánh mặc định trong `decisionOutcomes` và thuộc tính `default` trong XML.
   - **Merge-only gateway** (`isOpen: false`, nhiều incoming, 1 outgoing) không có `default` và dùng `decisionOutcomes: []`; đọc `nodes/gateway.md`.
   - Nhánh mặc định trong `decisionOutcomes`: `isDefault: true`, `outcomeOrder: -1`, `conditions: []`, `customConditionLogic: ""`, `slug: "_default"`, `color: "#939393"`, `flowId` trỏ đến flow ID mặc định
   - Nhánh có điều kiện: `isDefault: false`, `outcomeOrder` bắt đầu từ `0`, `color: "#4CAF50"`
   - Thuộc tính `default` trong XML phải trỏ đến flow ID của nhánh mặc định (cùng flow ID với `flowId` trong default outcome)
8. Khi quy trình có nhiều nhánh kết thúc, chọn rõ `END_BRANCH_EVENT` để chỉ kết thúc nhánh hoặc `END_EVENT` để kết thúc toàn process
9. Với Send Email Task:
   - Sử dụng `bpmn2:sendTask` trong XML
   - `renderKey="SEND_EMAIL_TASK"`
   - Cấu hình email trong mảng `actions` ở root level
   - `id` và `nodeId` trong action phải trùng với ID của sendTask trong XML
10. Với Send HTTP Request Task:
    - Sử dụng `elEx:httpTask` trong XML (cần namespace `xmlns:elEx="http://element-ex/schema"`)
    - `renderKey="SEND_HTTP_TASK"`
    - Cấu hình HTTP trong mảng `actions` ở root level
    - Action có `type: "SEND_HTTP_REQUEST"`
    - Output của request có thể truy cập qua `$action.{slug}.output`
11. Với Send Notification Task:
    - Sử dụng `elEx:sendNotificationTask` trong XML (cần namespace `xmlns:elEx="http://element-ex/schema"`)
    - `renderKey="SEND_NOTIFICATION_TASK"`
    - Cấu hình notification trong mảng `actions` ở root level
    - Action có `type: "SEND_NOTIFICATION"`
    - Người nhận (`to`) có thể là personnel từ biến (type: 4) hoặc ID trực tiếp (type: 1)
    - Tiêu đề và nội dung hỗ trợ cả giá trị raw và biến
12. Với Get Record Task:
    - Sử dụng `elEx:getRecordTask` trong XML (cần namespace `xmlns:elEx="http://element-ex/schema"`)
    - `renderKey="GET_RECORD_TASK"`
    - Cấu hình trong mảng `actions` ở root level
    - Action có `type: "GET_RECORD"`
    - Cần chỉ định `objectTypeId` và `objectTypeSlug` để xác định đối tượng cần lấy bản ghi
    - Output có 4 trường: `record` (bản ghi đơn), `result` (mã kết quả), `records` (danh sách bản ghi, `isList: true`), `total` (tổng số)
13. Với Create Record Task:
    - Sử dụng `elEx:createRecordTask` trong XML (cần namespace `xmlns:elEx="http://element-ex/schema"`)
    - `renderKey="CREATE_RECORD_TASK"`
    - Cấu hình trong mảng `actions` ở root level
    - Action có `type: "CREATE_RECORD"`; trong create payload, `id` và `nodeId` cùng bằng ID của BPMN node (`NO...` do skill sinh hoặc `Activity_*` từ modeler). Response legacy có thể được server remap sang `AC...`
    - Cần chỉ định `objectTypeId` và `layoutId` để xác định đối tượng cần tạo bản ghi
    - `recordData` là mảng chứa một đối tượng với các trường dữ liệu (key = field slug)
    - Mỗi trường có `type: 1` (giá trị cố định) hoặc `type: 4` (giá trị từ biến)
    - Trường có nhiều giá trị cần đặt `isList: true`
    - Output có 2 trường: `record` (bản ghi đã tạo), `result` (mã kết quả)
    - Khi dùng biến từ userTask (type: 4) trong recordData, cần thêm `resourcesUsedIn` vào resource tương ứng
14. Với Update Record Task:
    - Sử dụng cùng element `elEx:createRecordTask` và `renderKey="CREATE_RECORD_TASK"` giống Create Record
    - Action `type` ở root level vẫn là `"CREATE_RECORD"`, nhưng `data.actionType` là `"UPDATE_RECORD"`
    - Khác biệt chính: có `outputVariable` chỉ định bản ghi cần cập nhật (ví dụ: `$userTask.Root.lead`)
    - `outputVariable` thường tham chiếu đến trường lookup trong userTask trước đó
    - `outputVariableDataType` luôn là `"RECORD"`
    - `recordData` có cấu trúc giống Create Record nhưng có thêm các trường `isRaw`, `dataType`, `slug`
    - `resourcesUsedIn` dùng `actionType: "CREATE_RECORD"` (không phải `"UPDATE_RECORD"`)
15. Với Loop Task:
    - Sử dụng `elEx:loopTask` trong XML (cần namespace `xmlns:elEx="http://element-ex/schema"`)
    - `renderKey="LOOP_TASK"`
    - Loop Task có nhiều incoming (từ task trước + flow quay lại) và 2 outgoing (for_each_item + after_last_item)
    - Flow "For each item" cần `<configEx:elementInfo loopFlowType="for_each_item" />`
    - Flow "After last item" cần `<configEx:elementInfo loopFlowType="after_last_item" />`
    - Cấu hình loop trong mảng `loops` ở root level (không phải `actions`)
    - `variable` trỏ đến trường lookup nhiều giá trị trong userTask trước (ví dụ: `$userTask.Root.danh_sach_leads`)
    - `direction`: 1 = duyệt từ đầu đến cuối, 2 = duyệt từ cuối đến đầu
    - Resources loop (`$loop.{slug}.count` và `$loop.{slug}.currentItem`) nằm trong `resources.loops`
    - Khi dùng trường con của currentItem (ví dụ: `$loop.loop_leads.currentItem.name`), cần thêm vào `externalResourcesUsedIn`
16. Với Variable (Biến):
    - Variable là custom resource (`type: 1`) lưu trong `resources.custom`
    - ID dùng prefix `RS` (ví dụ: `RS00000000069`)
    - `absoluteSlug` dùng prefix `$flow.` (ví dụ: `$flow.bien_chu_text_mot_gia_tri`)
    - `absolutePath` theo format: `workflow_resource:list.variable / {Name}`
    - Các kiểu dữ liệu: TEXT, NUMBER, BOOLEAN, DATE, DATE_TIME, RECORD
    - `isList: false` cho đơn giá trị, `isList: true` cho nhiều giá trị
    - `editable: true` và `assignable: true` (luôn luôn)
    - `availableForInput` và `availableForOutput` cấu hình theo nhu cầu
    - Khi dùng làm defaultValue cho component trong userTask, component cần có `defaultValueDataType` và `defaultValuePathName`
    - `defaultTextValueType: 4` cho trường text, `defaultTextValueType: 0` cho trường không phải text (khi lấy giá trị từ biến)
    - Biến RECORD cần có `metaDataType` với `linkField`, `objectSlug`, `object`
    - Khi biến được sử dụng trong userTask, cần thêm `resourcesUsedIn` với `parentTable: "node_screen"`
    - `defaultValue` có thể là giá trị tĩnh hoặc tham chiếu biến/resource (ví dụ: `$userTask.Root.so_a`)
    - Khi `defaultValue` là tham chiếu, cần thêm `refAbsoluteSlug` và `refAbsolutePath`
17. Với Assignment Task:
    - Sử dụng `elEx:assignment` trong XML (cần namespace `xmlns:elEx="http://element-ex/schema"`)
    - `renderKey="ASSIGNMENT"` — **KHÔNG phải `ASSIGNMENT_TASK`** (ngoại lệ, các action khác đều có hậu tố `_TASK`)
    - Cấu hình trong mảng `actions` ở root level
    - Action có `type: "ASSIGNMENT"`
    - `data.assignments` là một mảng phép gán canonical; không dùng object map legacy
    - Mỗi phép gán có `left` (biến đích), `right` (giá trị nguồn), `operator` (toán tử), `index` (thứ tự)
    - Toán tử: `=` (gán), `+=` (cộng gán), `-=` (trừ gán), `count` (đếm số phần tử danh sách)
    - Resource của assignment có `absolutePath` format: `workflow_resource:list.assignment / {Name} / ...`
    - Biến/resource dùng trong assignment cần có `resourcesUsedIn` với `actionType: "ASSIGNMENT"` và `parentTable: "action"`
18. Với Text Template:
    - Text Template là custom resource (`type: 4`) lưu trong `resources.custom`
    - ID dùng prefix `RS` (ví dụ: `RS00000000041`)
    - `absoluteSlug` dùng prefix `$flow.` (ví dụ: `$flow.body_email`)
    - `absolutePath` theo format: `workflow_resource:list.textTemplate / {Name}`
    - `metaDataType` phải có `richText: 1`, `convertNullNumberToZero: true`, `convertNullStringToEmpty: true`
    - Nội dung (`defaultValue`) hỗ trợ cú pháp Apache Velocity Template Language (biến, if/else, foreach) — tham khảo `text-template-api-reference-vi.md`
    - Khi dùng trong Send Email, content dùng `type: 2` với `value: "$flow.{slug}"`
    - Khi dùng trường con của lookup trong template, cần thêm `externalResourcesUsedIn` ở root level
    - Resource của trường được dùng trong template cần có `resourcesUsedIn` trỏ đến cả action và text template
19. Với Formula / Scripting (Công thức tính):
    - Formula là custom resource (`type: 3`) lưu trong `resources.custom`
    - ID dùng prefix `RS` (ví dụ: `RS00000000094`)
    - `absoluteSlug` dùng prefix `$flow.` (ví dụ: `$flow.formula_1`)
    - `absolutePath` theo format: `workflow_resource:list.formula / {Name}`
    - `metaDataType` phải khớp `dataType`; bộ `richText`/convert chỉ dành cho Formula TEXT, không tái dùng cho NUMBER/BOOLEAN/DATE/DATE_TIME
    - Nội dung (`defaultValue`) là mã nguồn Cogover Scripting (Apache JEXL) — tham khảo `FORMULA_API_REFERENCE-VI.md`
    - `assignable: false` — không thể ghi giá trị bằng Assignment (chỉ tính toán)
    - `dataType` là kiểu dữ liệu trả về (TEXT, NUMBER, BOOLEAN, DATE, DATE_TIME)
    - Khi dùng trong action (ví dụ: Send HTTP Request body), tham chiếu bằng `type: 4` với `value: "$flow.{slug}"`
    - Khi dùng trường con của lookup trong formula, cần thêm `externalResourcesUsedIn` ở root level
    - Resource của trường được dùng trong formula cần có `resourcesUsedIn` trỏ đến formula resource (`parentTable: "resource"`)
20. Với Organization Task:
    - Sử dụng `elEx:organizationTask` trong XML (cần namespace `xmlns:elEx="http://element-ex/schema"`)
    - `renderKey="ORGANIZATION_TASK"`
    - Cấu hình trong mảng `actions` ở root level
    - Action có `type: "ORGANIZATION"`
    - 4 loại `filterType`: `"manager"` (quản lý), `"personnel"` (nhân sự cùng phòng), `"department"` (phòng ban), `"position"` (vị trí công việc)
    - Mỗi `filterType` có cấu trúc `criteria` riêng: key, field, option khác nhau (xem bảng tổng hợp trong section Organization)
    - Chỉ `filterType: "manager"` có thêm `rankOrderOperation`, `rankOrder`, `levelOfDepartment` trong criteria
    - `isRawValue: false` khi value là tham chiếu biến (ví dụ: `$userTask.Root.submittedBy`), `isRawValue: true` khi value là ID nhân sự cụ thể
    - `outputSaving: "FIELD_OF_FIRST_RECORD"` lưu trường của bản ghi đầu tiên, `"FIELD_OF_LIST_RECORDS"` lưu trường của tất cả bản ghi
    - `objectFieldSavings` cấu hình trường nào cần lưu vào biến nào (có thể để trống nếu không cần lưu)
    - Output có 3 trường: `record` (bản ghi đơn), `records` (danh sách bản ghi, `isList: true`), `total` (tổng số)
    - Resource dùng trong criteria cần có `resourcesUsedIn` với `actionType: "ORGANIZATION"` và `parentTable: "action"`
21. Với Wait Task:
    - Sử dụng `elEx:waitTask` trong XML (cần namespace `xmlns:elEx="http://element-ex/schema"`)
    - `renderKey="WAIT_TASK"`
    - Cấu hình trong mảng `actions` ở root level
    - Action có `type: "WAIT"`
    - Runtime hiện hỗ trợ đáng tin cậy timer tương đối và email events; các event còn xuất hiện trên UI không đồng nghĩa đã có đường thực thi ở backend
    - Chỉ ba email event mới phải liên kết Send Email Task; create payload front-end bắt buộc `sendEmailActionNodeId`, còn `sendEmailActionName`/`sendEmailActionSlug` chỉ có thể gặp ở payload legacy/response
    - Timer runtime bắt buộc `maximumWaitTimeValue` + `maximumWaitTimeUnit`; unit runtime là `seconds`, `minutes`, `hours`, `days` (đổi tuần thành ngày)
    - `AT_A_SPECIFIED_TIME`, Wait Webhook và Wait Record trong Normal Flow hiện không được skill tạo như case executable; đọc bảng compatibility trong `nodes/wait-task.md`
    - Resources có 3 trường: `startAt`, `endAt` (DATE_TIME) và `isEventTriggered` (BOOLEAN)
    - `absolutePath` dùng prefix `workflow_resource:list.wait` (ví dụ: `workflow_resource:list.wait / Wait 1 / StartAt`)
    - Chi tiết field matrix và ví dụ: `nodes/wait-task.md`
22. Với `processInstanceAccessControls` và `accessControls`:
    - **PHẢI** dùng `"functions": ["START_INSTANCE"]` (mảng), **KHÔNG** dùng `"action": "START_INSTANCE"` (chuỗi)
    - Tương tự: `"functions": ["VIEW"]`, **KHÔNG** dùng `"action": "VIEW"`
    - Nếu sai sẽ gây lỗi: `JSONArray[0] is not a JSONArray`
23. Với `taskPerformer` trong userTask:
    - **PHẢI** là mảng lồng mảng: `[[{ "field": "account", "isRawValue": true, "value": [], "option": 3 }]]`
    - **KHÔNG** dùng mảng đơn: `[{ "type": "personnel", ... }]`
    - Cấu trúc: `taskPerformer[group_index][performer_index]`
    - Nếu sai sẽ gây lỗi: `JSONArray[0] is not a JSONArray`
24. **KHÔNG được có key trùng lặp** trong cùng một JSON object:
    - Khi tạo hoặc chỉnh sửa JSON, **TUYỆT ĐỐI** không được có cùng một key xuất hiện nhiều lần trong cùng object
    - Ví dụ SAI: `{ "absoluteSlug": "...", "parentMetadata": "", "absoluteSlug": "...", "parentMetadata": "" }`
    - Ví dụ ĐÚNG: `{ "absoluteSlug": "...", "parentMetadata": "" }`
    - Đặc biệt chú ý khi thay thế hoặc cập nhật resource (ví dụ: thay đổi dataType từ TEXT sang SELECT_LIST) - phải đảm bảo các key cũ được thay thế hoàn toàn, không bị giữ lại và trùng với key mới
    - Nếu sai sẽ gây lỗi: `Cannot parse request`
25. **BẮT BUỘC sử dụng skill `/object-info` để lấy thông tin đối tượng thực tế:**
    - Các `objectTypeId`, `object type slug`, `object name`, `field slug`, `fieldType`, `field options` trong tài liệu này và các file sample chỉ là **ví dụ minh họa**, **KHÔNG PHẢI** giá trị thực tế. Các giá trị này **thay đổi theo từng workspace** của người dùng.
    - **LUÔN LUÔN** sử dụng skill `/object-info` để lấy thông tin chính xác **TRƯỚC KHI** tạo JSON, trong **TẤT CẢ** các trường hợp cần thông tin đối tượng:
      - **Tạo trường `lookup_normal`**: cần lấy đúng `object` (objectTypeId) và `object_slug` của đối tượng đích
      - **Tạo/cập nhật bản ghi** (`CREATE_RECORD`, `UPDATE_RECORD`): cần lấy đúng `objectTypeId`, `objectTypeSlug`, các `field slug` + `fieldType` + `fieldMetaData` của đối tượng
      - **Lấy bản ghi** (`GET_RECORD`): cần lấy đúng `objectTypeId` và `objectTypeSlug`
      - **Hiển thị bản ghi** trong User Task: cần lấy đúng `object` và `object_slug` cho trường lookup
      - **Triggered Flow (record)**: `object` trong trigger config cần đúng objectTypeId
      - **Triggered Flow (webhook)**: metadata cần `type: "webhook"`, cấu hình `parseToDataType` với schema body request, KHÔNG cần `object`
      - **Sequence Flow**: `metadata.objectTypeId` và `metadata.objectTypeSlug` cần chính xác
      - **Điều kiện (Conditions)** với kiểu RECORD: `leftObjectTypeId` cần đúng objectTypeId
      - **Biến RECORD (Variable)**: `metaDataType.object` và `metaDataType.objectSlug` cần chính xác
      - **Loop Task**: `variableMetadata.object` và `variableMetadata.objectSlug` cần chính xác
      - **Organization Task**: `metaDataType.objectSlug` và `metaDataType.object` trong output resources cần khớp với filterType
      - **Output resources** (GET_RECORD, CREATE_RECORD, Organization): `metaDataType.object` và `metaDataType.objectSlug` cần chính xác
    - **KHÔNG ĐƯỢC** sao chép objectTypeId, object slug, field slug, field options từ sample files hoặc từ ví dụ trong tài liệu này để dùng trực tiếp. Ví dụ: `OT00000000011` (Lead), `OT00000000007` (Contact) trong tài liệu chỉ là minh họa.
    - Skill `/object-info` sẽ gọi API và trả về danh sách đối tượng với đầy đủ: objectTypeId, slug, name, và danh sách fields (bao gồm field slug, field name, fieldType, fieldMetaData, options).
26. Với Sub Process:
    - Sử dụng `elEx:subProcess` trong XML (cần namespace `xmlns:elEx="http://element-ex/schema"`)
    - `renderKey="SUB_PROCESS"`
    - Cấu hình trong mảng `actions` ở root level
    - Action có `type: "SUB_PROCESS"`, `data.actionType: "SUB_PROCESS"`
    - `subWorkflowId` (PE...) và `processInfoId` (PI...) là 2 ID độc lập của quy trình con — **BẮT BUỘC** phải là ID thực tế đã tồn tại, **KHÔNG ĐƯỢC** tự sinh hoặc suy ra từ nhau. Cần hỏi người dùng cung cấp cả hai
    - `input`: key = biến quy trình con, value = object với `dataType`, `raw`, `value` (biến/resource quy trình cha)
    - `output`: key = biến quy trình con, value = biến quy trình cha nhận giá trị trả về
    - Ở cả `input` và `output`, key luôn là biến/tài nguyên của quy trình con
    - Biến quy trình cha dùng cho output cần `availableForInput: true` và `availableForOutput: true`
    - Khi quy trình con là `manual_flow` hoặc `sequence_flow`: **bắt buộc** có `starterPersonnelId` và `starterPersonnelIdForFe`
    - Khi quy trình con là `normal_flow`: không gửi `starterPersonnelId`, `recordId` hoặc `webhookInputBody`
    - Điều kiện gán biến giữa quy trình cha và con: cùng kiểu dữ liệu, cùng `isList`, biến quy trình con có `availableForInput/Output: true`
    - Resources có 3 trường: `startAt`, `endAt` (DATE_TIME) và `output` (RECORD với children: `status`, `result`)
    - `absolutePath` dùng prefix `workflow_resource:list.subProcess`
27. **BPMN XML — Quy tắc bắt buộc để tránh lỗi NODE_HAS_NO_CONNECT_TO_ANYTHING:**
    - **PHẢI** khai báo tất cả ID (node, flow, action, gateway, ...) thành các biến/hằng số dùng chung từ đầu, rồi dùng lại nhất quán trong cả XML lẫn JSON. **KHÔNG** sinh ID rời rạc ở nhiều chỗ khác nhau
    - Mỗi `<bpmn2:sequenceFlow>` PHẢI có `sourceRef` và `targetRef` trỏ đúng vào `id` của node tương ứng
    - Mỗi node PHẢI có `<bpmn2:incoming>` và `<bpmn2:outgoing>` liệt kê đầy đủ các flow ID kết nối vào/ra nó; trừ node Start chỉ có flow đi ra, node End chỉ có flow đi vào.
    - Tất cả `<bpmn2:sequenceFlow>` PHẢI nằm **bên trong** `<bpmn2:process>`, KHÔNG nằm ngoài
28. **BPMNDiagram — Quy tắc bắt buộc về bố cục và waypoint:**
    - **KHÔNG ĐƯỢC** đặt tất cả node trên cùng một hàng ngang. Phải bố trí node theo cấu trúc flow (nhánh gateway, parallel branches tách ra theo chiều dọc)
    - **KHÔNG ĐƯỢC** dùng waypoint cố định/hardcode cho BPMNEdge. Mỗi edge phải có waypoint tính toán dựa trên tọa độ thực của source node và target node
    - Mỗi `BPMNShape` **BẮT BUỘC** phải chứa `BPMNLabel`, và `BPMNLabel` PHẢI chứa `<dc:Bounds>` (KHÔNG được self-closing rỗng). Thiếu sẽ làm node biến mất khỏi diagram khi user save — silent fail, server vẫn trả `isValid:true`
    - Xem chi tiết quy tắc tính toán tọa độ và waypoint tại section **"Tính toán vị trí cho bố cục trực quan (BPMNDiagram)"** trong Bước 2
29. **BPMN namespace — chỉ dùng `bpmn2:`:**
    - Mọi BPMN-spec element (`process`, `startEvent`, `endEvent`, `sequenceFlow`, `incoming`, `outgoing`, `extensionElements`, `userTask`, `exclusiveGateway`, `inclusiveGateway`, `parallelGateway`, ...) **PHẢI** dùng prefix `bpmn2:` — vì namespace `xmlns:bpmn2` là namespace duy nhất được khai báo trong `<bpmn2:definitions>`. KHÔNG dùng `bpmn:` (prefix này không khai báo, một số element có thể bị server silent-strip ở thời điểm CREATE).
    - Custom prefix giữ nguyên: `elEx:`, `configEx:`, `bpmndi:`, `dc:`, `di:`, `bioc:`, `xsi:`.
30. **Trước khi POST: chạy sanity check XML** — xem mục 4.1 trong Bước 4. Sau khi POST nhận `isValid:true`, vẫn cần verify lại theo mục 4.5 vì server không validate đầy đủ phần BPMNDiagram.
31. **Sửa quy trình đã ACTIVATED:** không PUT trực tiếp được (lỗi `r:414`). Phải DELETE rồi POST mới — xem mục 4.4 trong Bước 4. PHẢI hỏi xác nhận trước khi xoá.
32. **Normal Flow:** dùng `type: "normal_flow"`, `START_NORMAL_EVENT`, `metadata: {}` và quyền `START_INSTANCE`; đọc `nodes/normal-flow.md`.
33. **To Do:** chỉ tạo trong Sequence Flow; dùng `elEx:todoTask`, renderKey `TODO_TASK`, action `TO_DO`; đọc `nodes/todo-task.md`.
34. **Phone Call:** dùng `elEx:phoneCallTask`, renderKey `PHONE_CALL_TASK`, action `PHONE_CALL`; phân biệt recording/TTS và Sequence automatic/manual. Với `MANUAL`, vẫn gửi `from: ""`, `to: {type:1,value:""}` và `content: {type:1,value:""}` để tránh lỗi server; đọc `nodes/phone-call-task.md`.
35. **Export Record:** dùng `elEx:exportRecordTask`, renderKey `EXPORT_TASK`, action `EXPORT_RECORD`; payload UI canonical hiện dùng document template. Bắt buộc dùng `$document-template` list/detail hoặc create rồi lấy ID đã verify; không dùng ID minh họa; đọc `nodes/export-record-task.md`.
36. **Respond to Webhook:** backend runtime hiện chưa đăng ký `RESPONSE_WEBHOOK`; không tạo node này cho process cần chạy. File `nodes/response-webhook-task.md` chỉ giữ schema để nhận diện/migration.
37. **Push Message:** dùng `elEx:pushMessageTask`, renderKey `PUSH_MESSAGE_TASK`, action `PUSH_MESSAGE`; field bắt buộc phụ thuộc push type và recipient type; đọc `nodes/push-message-task.md`.
38. **JSON to Object:** backend runtime hiện chưa đăng ký `PARSE_TO_OBJECT`; không tạo node này cho process cần chạy. File `nodes/parse-to-object-task.md` chỉ giữ schema để nhận diện/migration.
39. **Omni Message:** request BPMN phải là `bpmn2:sendTask` có marker `<elEx:omniMessageTask />`; request `action.data` phải là JSON string; không sinh SMS Brandname. Chỉ dùng OA/page/template ID thật; GET có thể bỏ marker và trả `data` thành object nên hậu kiểm theo semantic; đọc `nodes/omni-message-task.md`.
40. **End Branch:** dùng `bpmn2:endEvent` với renderKey `END_BRANCH_EVENT`; không tạo action payload; đọc `nodes/end-branch-event.md`.
41. **Slug:** mọi slug user-editable do process tạo phải dài ít nhất 2 ký tự và khớp `^[A-Za-z](?!.*__)[A-Za-z0-9_]*[^_]$`; bắt đầu bằng chữ cái, không có `__`, không kết thúc bằng `_`, không dùng dấu `-`, dấu chấm, khoảng trắng hoặc ký tự có dấu. Giữ nguyên slug hệ thống cố định như `_default`.
42. **Overview screen:** không gửi `overviewScreen: null`; dùng object đầy đủ hoặc mặc định `{ "layout": [], "permissionGeneralInfo": [] }`.
43. **Field User Task bắt buộc và chỉ đọc:** khi `required` và `readOnly` cùng truthy, bắt buộc `canSendData: true` trên component. Đây là checkbox **Gửi dữ liệu** dùng để đưa field vào payload submit form gửi tới `run-workflow-server`; không dùng `availableForOutput` và không đồng bộ cờ này sang resource. Đọc `nodes/user-task-form-fields.md`.
44. **AI Agent:** dùng action `AI_AGENT`, request `bpmn2:sendTask` với marker `elEx:aiAgentTask` và renderKey `AI_AGENT_TASK`; serialize `action.data` thành JSON string. Instruction inline có biến dùng `type: 5`; `type: 2` chỉ trỏ Text Template đã tồn tại. Nếu cần kết quả có cấu trúc, giữ đầy đủ `resultDataType.children` sau khi lưu. `continueOnFailure: true` phải đi kèm kiểm tra `output.status` trước khi dùng kết quả. Đọc `nodes/ai-agent-task.md` cho cấu hình, resources và giới hạn tương thích.
