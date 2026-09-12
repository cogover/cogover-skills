# Web App API vòng đời Process

Kích hoạt, xuất bản, bỏ xuất bản, vô hiệu hoá và quản lý version của một Process bằng API, không thao tác trên giao diện. Nhóm này dùng phiên Web App; tạo, sửa DRAFT, xoá, list và view vẫn dùng `/bapi/v1/processes` theo [api-process-builder.md](api-process-builder.md). Hành vi dưới đây đã được chạy thử trên Workspace ngày 2026-09-13; mã service có thể thay đổi theo phiên bản nền tảng.

## 1. Endpoint, xác thực và envelope

- Endpoint chung: `POST https://{WORKSPACE_DOMAIN}/api/v1/workflow`. Mọi thao tác dùng cùng URL và body JSON; thao tác được chọn bằng hai header `x-req-type: 1` và `x-req-service: {SERVICE}`.
- Xác thực: phiên Web App đổi từ API Key qua `POST /bapi/v1/auth-token` theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Gửi đủ ba cookie `HttpSessionId`, `AuthToken`, `XSRF-TOKEN`; hai header `x-csrf-token` và `x-xsrf-token` cùng bằng giá trị cookie `XSRF-TOKEN`. Tạo phiên một lần cho cả vòng kích hoạt, tạo lượt chạy và kiểm thử; không đọc cookie từ trình duyệt; không ghi giá trị phiên ra file, log hay báo cáo.
- Envelope response: body HTTP là `{"serviceVersion", "service", "id", "type", "body": {"r", "msg", "data", "meta"}}`. Thành công khi `body.r = 0`. Lỗi nghiệp vụ thường vẫn trả HTTP 200 với `body.r != 0`, có thể kèm `body._httpStatusCode` (ví dụ `403`); một số lỗi trả HTTP 400 với cùng envelope. Luôn đọc `body.r`, `body.msg`, `body.meta`, không dựa vào HTTP status. `/bapi/v1/processes/*` trên cùng nền tảng cũng có thể trả envelope này thay vì `{r, msg, data}` phẳng: bóc `body` khi có.
- `r: 5001` kèm `Can not found processor for request` nghĩa là sai `x-req-service` hoặc `x-req-type` cho endpoint đó. Dừng và đối chiếu lại bảng dưới; không dò số ngẫu nhiên.

Mẫu curl dùng chung, thay `{SERVICE}` và `{BODY}`:

```bash
curl --url 'https://{WORKSPACE_DOMAIN}/api/v1/workflow' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'content-type: application/json' \
  -b 'HttpSessionId={HTTP_SESSION_ID}; AuthToken={AUTH_TOKEN}; XSRF-TOKEN={XSRF_TOKEN}' \
  -H 'x-csrf-token: {XSRF_TOKEN}' \
  -H 'x-xsrf-token: {XSRF_TOKEN}' \
  -H 'x-req-type: 1' \
  -H 'x-req-service: {SERVICE}' \
  --data-raw '{BODY}'
```

## 2. Bảng thao tác

`{PROCESS_ID}` là `id` của một version (`PE...`), `{PROCESS_INFO_ID}` là `processInfoId` (`PI...`) chung cho mọi version của cùng process.

| Thao tác | `x-req-service` | Body | Kết quả mong đợi |
|---|---|---|---|
| Xem chi tiết một version | `4` | `{"id": "{PROCESS_ID}", "processInfoId": "{PROCESS_INFO_ID}"}` | `body.data` cùng cấu trúc với response create của `/bapi/v1/processes`: `progressStatus`, `isPublished`, `isValid`, `version`, `versionNumber`, `currentVersion`, `isNewestVersion`, `xmlString`, `userTasks`, `resources`, ...; `body.meta.errors[]` liệt kê lỗi validation |
| Danh sách version | `8` | `{"slug": "{PROCESS_SLUG}", "processInfoId": "{PROCESS_INFO_ID}"}` | Mảng version mới nhất trước: `id`, `version`, `versionNumber`, `versionLabel`, `name`, `progressStatus`, `isPublished`, `status` (`1` active, `2` inactive), `currentVersion`, `created`, `createdBy` |
| Kích hoạt | `9` | `{"id": "{PROCESS_ID}", "processInfoId": "{PROCESS_INFO_ID}"}` | `progressStatus: "ACTIVATED"`; version đã `ACTIVATED` trả `r: 409` "process is already active" |
| Kích hoạt và xuất bản | `39` | như trên | `ACTIVATED` và `isPublished: true`; trở thành version hiện hành (`currentVersion: true`); version hiện hành cũ bị bỏ xuất bản nhưng vẫn `ACTIVATED` |
| Xuất bản | `38` | như trên | `isPublished: true` và trở thành version hiện hành; version hiện hành cũ bị bỏ xuất bản |
| Bỏ xuất bản | `40` | như trên | `isPublished: false`, vẫn `ACTIVATED` |
| Vô hiệu hoá | `10` | như trên | `progressStatus: "CANCELED"`, `status: 2`; version đang xuất bản trả `r: 424` "process is published" |
| Lưu thành version mới | `24` | Toàn bộ process (như body `PUT /bapi/v1/processes/{id}`) kèm `id`, `processInfoId` của version gốc, `version`, `type`, `metadata`, `xmlString`, `resources` | Version mới `DRAFT`, `id` mới, cùng `processInfoId`, `versionNumber` tăng, `isNewestVersion: true`, `currentVersion: false`; `body.meta.errors[]` rỗng khi hợp lệ |
| Cập nhật version DRAFT | `23` | như `24` với `id` của version DRAFT | Giữ `id`; `body.meta.errors[]` rỗng và `isValid: true` khi hợp lệ |

`body.data` của `9`, `10`, `38`, `39`, `40` là bản ghi rút gọn (có thể thiếu `progressStatus`, `version` không chuẩn); đọc lại bằng `POST /bapi/v1/processes/view` với `{"id": "{PROCESS_ID}"}` hoặc service `4` để xác nhận trạng thái, không suy ra từ `r: 0`.

## 3. Quy trình chuẩn

### 3.1. Kích hoạt và xuất bản sau khi tạo

1. Tạo process bằng `POST /bapi/v1/processes`, GET-back verify theo SKILL.md mục 4.5.
2. Gọi service `39` với `id`, `processInfoId` vừa tạo. Nếu Workspace tách hai bước, gọi `9` rồi `38`.
3. Đọc lại và xác nhận tối thiểu `progressStatus: "ACTIVATED"`, `isPublished: true`, `isValid: true`, đúng `id` và `processInfoId`.
4. Lượt chạy Normal chỉ tạo được khi cả `ACTIVATED` và `isPublished: true` (thiếu một trong hai trả `r: 206` `PROCESS_NOT_ACTIVE`). Lượt chạy Manual qua submit form Root không bị chặn bởi trạng thái version (xem [api-process-runtime.md mục 2](api-process-runtime.md#2-tạo-lượt-chạy-theo-loại-flow)).

### 3.2. Sửa process đã ACTIVATED bằng version mới

`PUT /bapi/v1/processes/{id}` trên version `ACTIVATED` hoặc `isPublished: true` trả `r: 414`. Thay vì xoá và tạo lại:

1. Lấy body hiện tại qua `POST /bapi/v1/processes/view`, sửa `xmlString`/`resources`/cấu hình cần đổi, strip các trường server-managed (`created`, `updated`, `createdBy`, `updatedBy`, `workspaceId`, `status`, `isValid`, `validationMessage`, `isPublished`, `progressStatus`, `currentVersion`, `isNewestVersion`, `versionNumber`, `versionLabel`) nhưng giữ `id`, `processInfoId`, `version`, `type`, `slug`, `name`.
2. Đổi mọi prefix `bpmn:` trong `xmlString` của response về `bpmn2:` trước khi gửi. Gửi nguyên response làm server strip toàn bộ sequence flow: version mới có `isValid: false`, `meta.errors` gồm `START_EVENT_HAS_NO_OUTGOING_FLOW`, `TASK_MUST_HAS_INCOMING_FLOW`, `NODE_HAS_NO_CONNECT_TO_ANYTHING`, và kích hoạt trả `r: 402`. Chạy sanity check XML (SKILL.md mục 4.1).
3. Gọi service `24`. Response trả version mới `DRAFT` với `id` mới, node ID có thể được server remap; `processInfoId` không đổi nên link, quyền và lịch sử lượt chạy được giữ. Version mới còn lỗi thì sửa bằng service `23` với `id` mới cho tới khi `meta.errors` rỗng.
4. GET-back verify version mới, rồi gọi `39` trên `id` mới. Đọc lại danh sách version (service `8`): version mới `ACTIVATED`, xuất bản, `currentVersion: true`; version cũ vẫn `ACTIVATED` nhưng `isPublished: false`, `currentVersion: false`.
5. Lượt chạy đã tạo trước đó tiếp tục theo version cũ (`processVersion` giữ nguyên, submit vẫn được); lượt chạy mới dùng version mới. Xoá và tạo lại (mục 4.4 SKILL.md) chỉ là phương án cuối khi không thể tạo version mới, và phải hỏi xác nhận trước khi xoá.

### 3.3. Đổi version hiện hành, rollback

1. Service `8` để lấy danh sách version và trạng thái từng version.
2. Version đích đang `DRAFT` hoặc `CANCELED`: gọi `39`. Version đích đã `ACTIVATED` nhưng không xuất bản (trường hợp version cũ sau khi có version mới): gọi `38`; gọi `9`/`39` sẽ trả `r: 409`.
3. Đọc lại danh sách version: chỉ version đích `isPublished: true`, `currentVersion: true`; version hiện hành trước đó bị bỏ xuất bản nhưng vẫn `ACTIVATED`. Muốn version cũ không còn chạy lịch/trigger thì gọi `10` trên nó.
4. Rollback là trường hợp riêng của bước trên với version cũ; không sửa nội dung version cũ, nếu cần sửa thì tạo version mới từ nó theo 3.2.

### 3.4. Ngừng nhận lượt chạy mới, vô hiệu hoá

- Bỏ xuất bản (`40`) giữ `ACTIVATED`, chặn tạo lượt chạy Normal (`r: 206`). Vô hiệu hoá (`10`) đưa version về `CANCELED`; version đang xuất bản trả `r: 424`, gọi `40` trước rồi `10`. Kích hoạt lại bằng `9` (chưa xuất bản) hoặc `39`.
- Lượt chạy đang `RUNNING`/`PAUSED` không bị ảnh hưởng bởi bỏ xuất bản hay vô hiệu hoá: vẫn submit và chạy tới kết thúc. API không nhận tuỳ chọn xử lý lượt chạy dở; xử lý riêng bằng API đổi trạng thái instance trong [api-process-runtime.md mục 5](api-process-runtime.md#5-đổi-trạng-thái-và-xoá-lượt-chạy); liệt kê ID trước và hỏi xác nhận khi huỷ.
- Manual Flow: submit form Root vẫn tạo lượt chạy mới trên version chưa xuất bản hoặc đã vô hiệu hoá (quan sát trên Workspace kiểm thử). Không dựa vào bỏ xuất bản/vô hiệu hoá để chặn người có quyền Root submit qua API; thu hồi `START_INSTANCE`/performer của Root nếu cần chặn.
- Sau mỗi thao tác, đọc lại `progressStatus`, `isPublished` và thử tạo lượt chạy để chứng minh hiệu lực; không kết luận từ `r: 0`.

## 4. Quy tắc an toàn

- Vô hiệu hoá, bỏ xuất bản, đổi version hiện hành trên process đang có lượt chạy hoặc đang được người dùng thật sử dụng: nêu tác động và hỏi xác nhận trước khi gọi, trừ process test do chính phiên này tạo.
- Version đã tạo không xoá riêng được; chỉ tạo version mới khi thật sự cần sửa, và mô tả rõ trong `description` để phân biệt.
- Xoá process: theo Quy tắc an toàn của SKILL.md.
- Mã `x-req-service` là hợp đồng của Web App và có thể thay đổi theo phiên bản nền tảng. Gặp `r: 5001` hoặc response khác cấu trúc mong đợi: dừng, báo phiên bản Workspace và thao tác bị ảnh hưởng; không thử số khác.

## 5. Lỗi thường gặp

| `r` | Ý nghĩa | Xử lý |
|---|---|---|
| `402` | Kích hoạt version không hợp lệ; `msg` chứa danh sách lỗi validation (`code`, `internalMessage`, `nodeId`) | Sửa version DRAFT bằng service `23` tới khi `meta.errors` rỗng |
| `409` | Kích hoạt version đã `ACTIVATED` | Dùng `38` để xuất bản/đổi version hiện hành |
| `410` | Không có quyền đọc form (`_httpStatusCode: 403`), thường vì version chưa kích hoạt hoặc người gọi không phải performer | Kích hoạt trước; kiểm tra `taskPerformer` và `processInstanceAccessControls` |
| `414` | PUT `/bapi/v1/processes/{id}` trên version đang `ACTIVATED`/xuất bản | Tạo version mới (3.2) |
| `424` | Vô hiệu hoá version đang xuất bản | Bỏ xuất bản (`40`) trước |
| `5001` | Không có processor cho `x-req-service` | Đối chiếu bảng mục 2, kiểm tra `x-req-type: 1` |
| HTTP 401/403 | Phiên hết hạn hoặc thiếu quyền | Tạo lại phiên theo `$cogover-api-auth`; kiểm tra quyền `EDIT` trong `accessControls` |
