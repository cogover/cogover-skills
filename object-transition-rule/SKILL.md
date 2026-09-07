---
name: object-transition-rule
description: Quản lý quy tắc chuyển trạng thái cho field single-choice của Cogover Object qua Web App API `/api/v1/object_security/transition_rule`. Sử dụng cho các đối tượng có trạng thái phải đi theo lộ trình được thiết lập sẵn như đơn hàng, hóa đơn, phiếu thu chi, phiếu nhập kho, lead; hoặc khi cần tra cứu, tạo, sửa, nhân bản, bật/tắt, xóa transition rule, thiết kế flow giữa option, cấu hình điều kiện/phạm vi record/validation/post-action và kiểm tra rule sau khi ghi. Khi người dùng yêu cầu tạo rule nhưng không cung cấp các cặp chuyển, tự phân tích ngữ nghĩa Object, field và option để thiết kế luồng nghiệp vụ phù hợp.
metadata:
  author: cogover
  version: "1.0.1"
---

# Object Transition Rule

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

Quản lý transition rule bằng API, không thao tác giao diện trình duyệt. Luôn resolve Object, field, option và rule từ dữ liệu thật của workspace trước khi dựng payload.

Skill này dành cho người dùng bên ngoài. Chỉ dùng tài liệu đi kèm skill, thông tin người dùng cung cấp, cơ chế credential an toàn có sẵn và response API của workspace. Không tìm hoặc đọc source code, repository, file dự án, test, migration, database, log nội bộ, browser bundle hay source map để suy ra contract. Nếu tài liệu và API không đủ thông tin, dừng và báo rõ phần còn thiếu.

## Phạm vi nghiệp vụ

- Dùng transition rule cho Object có trường trạng thái và cần bắt buộc record đi theo một lộ trình đã thiết lập, không cho chuyển trạng thái tùy tiện. Các trường hợp thường gặp gồm đơn hàng, hóa đơn, phiếu thu chi, phiếu nhập kho, lead và các chứng từ/quy trình tương tự.
- Trường điều khiển thường là field single-choice có slug `status`. Không mặc định chọn field khác chỉ dựa vào tên hiển thị. Nếu người dùng chưa chỉ rõ field và không thể xác định chắc chắn một field active, single-choice có slug `status`, phải xác nhận với người dùng cần thiết lập rule trên field nào trước khi mutation.
- Khi cần đối chiếu cấu trúc một rule hoàn chỉnh, đọc [mẫu JSON inventory transaction](references/inventory-transaction-rule-sample.json). Dùng mẫu read-only để tham khảo schema, flow và graph metadata; không tái sử dụng ID, workspace metadata, timestamp hoặc giá trị nghiệp vụ của mẫu trong payload mới.

## Chuẩn bị xác thực

1. Lấy `WORKSPACE_DOMAIN` và `API_KEY` từ thông tin người dùng cung cấp hoặc cơ chế credential an toàn có sẵn. Không đọc file dự án để tìm secret; nếu vẫn thiếu, yêu cầu người dùng cung cấp qua kênh an toàn.
2. Chuẩn hóa domain thành `https://{workspace-domain}`; không tự đổi workspace.
3. **Bắt buộc gọi `$cogover-api-auth`** trước request đầu tiên và tuân theo interface công khai của skill đó; không mở file triển khai của skill khác.
4. Dùng API Key Bearer **chỉ** cho `POST /bapi/v1/auth-token` để đổi sang phiên Web App. Với mọi endpoint `/api/v{N}/...`, gửi đủ ba cookie `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` và hai header `x-csrf-token`, `x-xsrf-token` cùng bằng `XSRF-TOKEN`.
5. Tuyệt đối không gửi `Authorization: Bearer {API_KEY}` trực tiếp tới `/api`, không in hoặc ghi log secret/cookie/token.
6. Tạo lại phiên theo thời hạn do auth response trả về. Không dùng phiên của domain khác.

## Nạp contract

Đọc [references/api-contract.md](references/api-contract.md) trước khi gọi API hoặc dựng payload. Dùng tài liệu đó làm nguồn chuẩn cho endpoint, schema, graph metadata, validation, response và mã lỗi.

## Resolve Object, field và options

1. **Bắt buộc gọi `$object-info`** qua interface công khai để lấy chi tiết Object, field và options thật của workspace trước khi dựng payload hoặc mutation; không mở file triển khai của skill đó.
2. Chọn field active, single-choice khớp chính xác; nếu người dùng chưa nêu field thì ưu tiên kiểm tra slug `status` và phải xác nhận khi không chắc chắn. Dùng `field.id` làm `objectFieldId`, dùng option `slug` cho giá trị flow và chỉ dùng `value` làm nhãn.
3. Khi cần tự thiết kế flow, thu thập thêm Object name/slug/description, field name/slug, option `value`, `slug`, translations, `isDefault`, status và thứ tự nếu API có. Không suy luận chỉ từ một slug khi nhãn hoặc bản dịch cung cấp ngữ cảnh rõ hơn.

## Tự thiết kế flow khi người dùng không cung cấp

1. Đóng vai chuyên gia thiết kế hệ thống phần mềm quản trị doanh nghiệp. Phân tích vòng đời thực tế của Object từ metadata đã resolve và ngữ nghĩa nghiệp vụ thông thường; không yêu cầu người dùng liệt kê flow chỉ vì yêu cầu ban đầu bị thiếu các cặp `origin -> target`.
2. Phân loại option theo vai trò ngữ nghĩa, không theo vị trí mảng: trạng thái khởi tạo/nháp; chuỗi xử lý chính; chờ/tạm dừng; yêu cầu và kết quả hủy; yêu cầu và chuỗi trả/hoàn; thành công; thất bại/từ chối/đóng. Dùng cả tên Object để phân biệt cùng một nhãn trong các ngữ cảnh khác nhau.
3. Dựng graph nhỏ nhất nhưng hoàn chỉnh:
   - Nối `_initial` tới option default nếu option đó hợp lý là trạng thái bắt đầu; nếu không, chọn option có ngữ nghĩa sớm nhất trong vòng đời.
   - Nối chuỗi chính theo chiều tiến triển nghiệp vụ, ví dụ nháp/mới → xác nhận/kích hoạt → đang xử lý → đã xử lý → đang giao → đã giao → hoàn tất khi các option thực tế mang các nghĩa đó.
   - Chỉ nối nhánh hủy từ các trạng thái còn có thể hủy; ưu tiên qua trạng thái yêu cầu hủy nếu có. Không hủy từ trạng thái đã trả, đã thất bại hoặc kết thúc mà ngữ nghĩa không cho phép.
   - Chỉ nối nhánh trả/hoàn từ trạng thái cho thấy hàng hóa/giao dịch đã phát sinh; ưu tiên chuỗi yêu cầu trả → đang trả → đã trả khi có đủ option.
   - Xem các trạng thái hoàn tất, hủy, trả xong, từ chối hoặc đóng là terminal theo mặc định. Không tạo outgoing flow từ terminal trừ khi option khác thể hiện rõ thao tác mở lại, thử lại hoặc hoàn tác.
   - Chỉ tạo lối vào/ra cho trạng thái chờ/tạm dừng khi có thể xác định điểm tiếp tục hợp lý; không nối nó với mọi option.
4. Không tạo graph “mọi trạng thái đến mọi trạng thái”. Không tạo self-loop, target `_initial`, cặp trùng, bước lùi, reopen, retry hoặc undo nếu ngữ nghĩa option không thể hiện rõ chủ ý đó.
5. Khi tự suy luận, không tự thêm personnel filter, record filter, validation hoặc post-action; dùng condition rỗng, `shouldFilterRecord: false` và `allowUndo: false`. Các thành phần này cần ID và chính sách doanh nghiệp cụ thể, không thể suy ra an toàn chỉ từ tên option.
6. Nếu nhiều graph đều hợp lý, chọn graph bảo thủ có ít quyền chuyển hơn và nêu rõ các giả định trong kết quả. Vẫn tạo rule `active` theo mặc định; chỉ tạo `inactive` khi người dùng yêu cầu rõ. Chỉ dừng để hỏi khi metadata không đủ về mặt kỹ thuật, ví dụ không có option active hợp lệ hoặc không resolve được duy nhất Object/field; không dừng chỉ vì người dùng chưa thiết kế flow.

## Đặt tên flow theo hành động

1. Luôn đặt `flow.name` bằng tiếng Anh, dù người dùng hoặc option dùng ngôn ngữ khác. Dùng cụm động từ ngắn gọn mô tả hành động nghiệp vụ làm phát sinh chuyển trạng thái.
2. Không đặt name theo mẫu `{Origin} to {Target}`, `Change to {Target} status` hoặc bằng raw slug. Ví dụ dùng `Activate`, `Start packing`, `Finish packing`, `Ship`, `Complete`, `Put on hold`, `Resume`, `Request cancellation`, `Cancel`, `Request return`, `Start return shipping`, `Confirm return` thay cho `Draft to Activated`, `Packing to Packed`.
3. Với flow `_initial -> option`, dùng hành động khởi tạo phù hợp như `Create`, `Initialize` hoặc `Start`; ưu tiên `Create` khi record được tạo ở trạng thái draft/new.
4. Tạo `flow.slug` từ action name theo ASCII `lower_snake_case`. Giữ slug duy nhất trong rule; khi nhiều origin dùng cùng một action name, thêm context kỹ thuật vào slug như `request_cancellation_from_draft` mà không biến display name thành cặp trạng thái.
5. Mirror chính xác action name và slug vào `flow.metaData.edge.data.conditionBlocks`; dùng action name làm `edge.label`.

## Bố trí graph không chồng lấn

1. Thiết kế vị trí node và routing edge trước khi serialize metadata; không xếp cả graph trên một hàng chỉ vì chuỗi chính là tuyến tính. Với graph từ 8 node hoặc 12 flow, ưu tiên nhiều hàng/lane để giữ bounds gọn.
2. Tính kích thước node theo **nhãn dài nhất** giữa `value` và mọi translation có thể hiển thị, không chỉ theo nhãn gốc. Ước lượng width `clamp(82, 40 + 8 * số ký tự, 240)` và dùng `height: 48`.
3. Ước lượng width action label `clamp(72, 32 + 8.5 * số ký tự, 260)`. Trên một cạnh chính, chừa khoảng trống giữa hai node ít nhất `actionLabelWidth + 120`; không dùng bước cố định nhỏ như 180px.
4. Tách chuỗi chính, nhánh chờ, hủy, trả/hoàn và terminal vào các lane khác nhau. Với nhiều edge cùng target, làm lệch midpoint của label; yêu cầu các label box không giao nhau và có ít nhất 16 graph units đệm. Với hai edge ngược chiều giữa cùng hai node, dùng route/handle khác nhau.
5. Gán handle theo hướng layout đã xác minh: trái→phải dùng `right -> left`, phải→trái dùng `left -> right`, trên→dưới dùng `bottom -> top`. Dùng cặp handle thay thế như `top -> top` hoặc `left -> left` cho edge ngược chiều để tách route. Không gán cùng một handle mặc định cho mọi edge.
6. Giữ bounds graph trong ngân sách viewport tại min zoom. Nếu chưa đo được canvas thực tế, dùng `2200 x 1300` graph units ở min zoom `0.5` như ngưỡng bảo thủ; dùng layout hai hàng dạng snake nếu chuỗi dài vượt ngân sách chiều rộng.
7. Trước mutation, kiểm tra hình học tối thiểu: node-node, edge-label–node và edge-label–edge-label không giao nhau; mọi node nằm trong bounds dự kiến. Sau mutation, đọc lại metadata và lặp lại kiểm tra.
8. Khi người dùng báo lỗi hiển thị hoặc browser sẵn có, chỉ dùng browser để QA read-only; không tạo/sửa/lưu rule trên UI. Chờ UI nạp đủ `optionCount + 1` node và `flowCount` edge label trước khi đo bounding box, tránh kết luận từ trạng thái Start-only tạm thời. Chỉ báo đã sửa UI khi không còn collision và node không nằm ngoài canvas.

## Quy trình chung

1. Phân biệt yêu cầu read và mutation. Không ghi dữ liệu khi người dùng chỉ yêu cầu xem, phân tích hoặc lấy mẫu.
2. Gọi list theo `objectSlug`, resolve rule bằng `id` hoặc name/slug khớp chính xác. Nếu có nhiều ứng viên, không tự chọn.
3. Kiểm tra field và tất cả option slug vẫn tồn tại ngay trước mutation.
4. Dựng JSON bằng công cụ như `jq`; không escape thủ công `metaData` lồng nhau.
5. Chỉ coi request thành công khi HTTP thành công **và** response có `r: 0`.
6. Sau mọi create/update/status/delete, đọc lại bằng ID và so sánh trước/sau. Không dựa riêng vào response mutation. Khi read-back không echo một key Boolean `false`, kiểm tra bản mirror trong `metaData` trước khi báo lệch; so flows theo ID/slug hoặc cặp `originValue -> targetValue`, không yêu cầu giữ nguyên thứ tự mảng.
7. Parse và validate schema UI của rule-level và tất cả flow-level `metaData` sau create/update. API có thể trả `r: 0` cho metadata tối giản nhưng UI React Flow vẫn lỗi khi thiếu state của node/edge; không báo hoàn tất nếu checklist schema và hình học UI trong API contract chưa đạt.

## Xem danh sách hoặc chi tiết

- Gọi `GET /api/v1/object_security/transition_rule?objectSlug={objectSlug}` để xem các rule của Object.
- Gọi `GET /api/v1/object_security/transition_rule?id={ruleId}` để lấy chi tiết mới nhất, bao gồm `flows`.
- Hiển thị tối thiểu ID, name, slug, status, field ID/name, sort, số flow và thời gian update.
- Parse `metaData` chỉ khi cần phân tích graph; giữ nguyên chuỗi gốc để update an toàn.
- Một số deployment trả `objectSlug: null` trong detail. Khi đó xác minh ownership bằng `objectTypeId` đã resolve và list theo Object; không coi `null` là bằng chứng rule thuộc sai Object.

## Tạo rule

1. Xác định từng quan hệ `originValue -> targetValue`. Nếu người dùng đã cung cấp flow, tôn trọng các cặp đó sau khi validation. Nếu chưa cung cấp, tự dựng toàn bộ flow theo mục **Tự thiết kế flow khi người dùng không cung cấp** và tiếp tục tạo rule mà không yêu cầu người dùng thiết kế thay.
2. Kiểm tra name/slug chưa trùng trong toàn Object. Tuân theo validation UI: name 1–255 ký tự; slug 2–100 ký tự chỉ gồm chữ, số, `_` và không có `__`; description tối đa 1000 ký tự. Đếm cả tổng số rule và số rule active trước create.
3. Tạo ít nhất một flow và đặt tên theo mục **Đặt tên flow theo hành động**. Dùng `_initial` chỉ làm `originValue` cho transition khởi tạo; mọi giá trị khác phải là option slug thật.
4. Dùng `status: 1` (active) theo mặc định. Chỉ dùng `status: 0` (inactive) khi người dùng yêu cầu rõ. Trước create active, xác minh Object hiện có dưới 5 rule active; nếu đã đạt giới hạn, dừng và báo lỗi thay vì âm thầm hạ xuống inactive.
5. Tạo rule-level `metaData` và flow-level `metaData` nhất quán với `flows`; cả hai là JSON string và phải theo **UI-safe baseline** cùng yêu cầu hình học trong API contract. Mỗi flow phải có `conditionBlocks.logicType` và `conditionBlocks.logic`, kể cả khi không có condition. Không dùng metadata tối giản chỉ có `id/type/position/data` cho node hoặc `source/target/type/data` cho edge.
6. Chỉ bật `shouldFilterRecord` khi đã xác minh toàn bộ condition bằng field metadata thật. Khi false, không tự tạo `recordFilter`.
7. Gọi `POST /api/v1/object_security/transition_rule/create`, lấy ID từ `data[0].id`, rồi view lại theo ID.

## Cập nhật rule hoặc flows

1. View theo ID ngay trước update. Xác nhận rule thuộc đúng Object và field.
2. Không đổi `objectFieldId`; backend giữ field hiện tại khi update. Nếu cần field khác, tạo rule mới.
3. Với scalar như name, description, status, sort, gửi payload tối thiểu có `id` và trường cần đổi. Không hứa slug đã đổi cho tới khi view lại xác nhận, vì một số bản backend validate nhưng không persist slug update.
4. Coi `flows` là cấu hình thay thế toàn bộ: nếu thay một flow, gửi lại **toàn bộ** flows đã merge với thay đổi. Gửi mảng khác rỗng sẽ xóa/tạo lại flows phía server; `null`, bỏ trống hoặc `[]` không phải cách xóa tất cả.
5. Khi sửa graph, cập nhật đồng thời `flows`, rule `metaData` và từng flow `metaData`. Giữ nguyên condition/personnel/post-action không liên quan; giữ nguyên metadata UI hợp lệ không thuộc phạm vi thay đổi và bổ sung mọi key baseline còn thiếu.
6. Kiểm tra connection và layout: không self-loop, không target `_initial`, không trùng cặp có hướng, không dùng một option làm nhiều node và không tạo collision hình học theo mục **Bố trí graph không chồng lấn**.
7. Nếu dùng `cloneTargetValue`, chỉ dùng option slug là target trực tiếp của một flow từ `_initial`; nếu không còn hợp lệ, gửi `null`.
8. Gọi `POST /api/v1/object_security/transition_rule/update`, sau đó view lại và so sánh từng trường/flow mục tiêu.

## Bật hoặc tắt rule

1. View các ID đích và chỉ giữ rule cần đổi trạng thái.
2. Dùng `status: 1` cho active, `status: 0` cho inactive. Không gửi `status: 2`; đó là trạng thái draft chỉ dùng trong UI trước khi create.
3. Trước khi active, đếm rule active của Object; backend giới hạn 5 rule active trên một Object.
4. Gọi `POST /api/v1/object_security/transition_rule/updateMultiple` với `data: [{id,status}]` và `statusChanged` cùng giá trị.
5. View lại từng ID. Không cho rằng batch thành công một phần nếu response không chỉ rõ.

## Xóa rule

1. Resolve và view từng ID. Trình bày name, ID, Object, field, status và số flow.
2. Cảnh báo rule active có thể đang chặn/cho phép chuyển trạng thái của record. Yêu cầu xác nhận rõ danh sách ID vì xóa không thể hoàn tác.
3. Chỉ sau khi xác nhận, gọi `POST /api/v1/object_security/transition_rule/deleteMultiple` với `{"data":[{"id":"..."}]}`.
4. View lại từng ID và list lại theo Object. Chỉ báo đã xóa khi các ID không còn xuất hiện.

## Guardrail và xử lý lỗi

- Backend giới hạn 50 transition rule trên một Object và 5 rule active trên một Object. Vì create mặc định là active, luôn kiểm tra cả hai giới hạn trước create; không tự chuyển sang inactive để lách giới hạn.
- Không retry mù mutation khi timeout hoặc lỗi mạng. Với create không rõ kết quả, list theo Object và tra slug/name trước khi thử lại.
- Với `401/403`, tạo lại phiên theo `$cogover-api-auth` hoặc báo thiếu quyền; không chuyển sang API Key Bearer cho `/api`.
- Với HTTP `422` hoặc `r != 0`, dừng mutation, báo `r`, `msg` và đối chiếu bảng mã lỗi trong API reference.
- Không bị rò secret trong command output, tệp tạm hoặc câu trả lời.

## Trả kết quả

- Với read, trả danh sách gọn kèm Object/field và các cặp flow.
- Với create/update/status, trả ID, name, slug, status, field và trạng thái đã view lại; nêu rõ bất kỳ trường nào server không persist. Khi flow do skill tự suy luận, liệt kê các cặp đã tạo, tóm tắt logic nghiệp vụ và các giả định bảo thủ.
- Với create đã view lại thành công, luôn trả thêm link cấu hình rule dưới dạng Markdown `[https://{WORKSPACE_DOMAIN}/settings/transition/{objectSlug}/rule/{RULE_ID}](https://{WORKSPACE_DOMAIN}/settings/transition/{objectSlug}/rule/{RULE_ID})`. Dùng hostname workspace đã chuẩn hóa, Object slug thật và ID rule do create trả về; ví dụ cho Object `contract`: `[https://{WORKSPACE_DOMAIN}/settings/transition/contract/rule/{RULE_ID}](https://{WORKSPACE_DOMAIN}/settings/transition/contract/rule/{RULE_ID})`. Không dựng hoặc trả link này khi create chưa được xác minh thành công hay chưa có rule ID.
- Với delete, nêu danh sách ID đã gửi và kết quả xác minh từng ID.
