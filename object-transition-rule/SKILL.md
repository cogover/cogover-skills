---
name: object-transition-rule
description: "Quản lý transition rule cho field single-choice của Cogover Object qua `/api/v1/object_security/transition_rule` (phiên Web App): list, tạo, sửa, bật/tắt, xóa; thiết kế flow giữa option (tên hành động tiếng Anh, graph UI-safe), condition/record filter/post-action, verify sau ghi; thiếu cặp chuyển thì tự thiết kế từ ngữ nghĩa Object/field/option."
metadata:
  author: cogover
  version: "1.0.2"
---

# Object Transition Rule

- **Phiên bản:** `1.0.2`
- **Ngày phát hành:** `2026-09-11`

Quản lý transition rule của field trạng thái (single-choice) qua `/api/v1/object_security/transition_rule` bằng phiên Web App; thao tác hoàn toàn bằng API, không qua giao diện trình duyệt. Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Skill dành cho người dùng bên ngoài: chỉ dùng tài liệu đi kèm skill, thông tin người dùng cung cấp và response API; không đọc source code, browser bundle hay source map để suy ra contract; tài liệu và API không đủ thì dừng và báo rõ phần còn thiếu. Gọi `$cogover-api-auth` và `$object-info` qua interface công khai của chúng, không mở file triển khai.

## Chuẩn bị

- Phạm vi: Object có trường trạng thái mà record phải đi theo lộ trình đã thiết lập, không cho chuyển tùy tiện (đơn hàng, hóa đơn, phiếu thu chi, phiếu nhập kho, lead và chứng từ tương tự).
- Đọc [references/api-contract.md](references/api-contract.md) trước khi gọi API hoặc dựng payload: nguồn chuẩn cho endpoint, schema, graph metadata, validation, response và mã lỗi. Cần đối chiếu một rule hoàn chỉnh thì đọc [mẫu JSON inventory transaction](references/inventory-transaction-rule-sample.json) (read-only, chỉ tham khảo schema, flow và graph metadata; không tái sử dụng ID, workspace metadata, timestamp hoặc giá trị nghiệp vụ của mẫu).
- Bắt buộc `$object-info` để lấy Object, field và option thật trước khi dựng payload hoặc mutation. Field điều khiển: active, single-choice, khớp chính xác; người dùng chưa nêu field thì ưu tiên slug `status`, không chọn field khác chỉ dựa vào tên hiển thị; không xác định chắc chắn được thì xác nhận với người dùng trước mutation. Dùng `field.id` làm `objectFieldId`, option `slug` làm `originValue`/`targetValue`, option `value` chỉ làm nhãn.
- Khi phải tự thiết kế flow, thu thập thêm Object name/slug/description, field name/slug, option `value`, `slug`, translations, `isDefault`, status và thứ tự nếu API có; không suy luận chỉ từ một slug khi nhãn hoặc bản dịch cho ngữ cảnh rõ hơn.
- Resolve rule: list theo `objectSlug`, chọn bằng `id` hoặc name/slug khớp chính xác; nhiều ứng viên thì không tự chọn. Ngay trước mutation, kiểm tra field và mọi option slug vẫn tồn tại.
- Condition, personnel filter, record filter và post-action: chỉ cấu hình khi người dùng yêu cầu và đã resolve đủ ID; schema theo [Conditions, personnel và post-actions](references/api-contract.md#conditions-personnel-và-post-actions).
- Dựng JSON bằng `jq` hoặc tương đương; không escape thủ công `metaData` lồng nhau.

## Tự thiết kế flow khi người dùng không cung cấp cặp chuyển

1. Đóng vai chuyên gia thiết kế hệ thống quản trị doanh nghiệp: phân tích vòng đời thực tế của Object từ metadata đã resolve và ngữ nghĩa nghiệp vụ thông thường, tự dựng toàn bộ flow rồi tiếp tục tạo rule; không yêu cầu người dùng liệt kê hay thiết kế thay chỉ vì yêu cầu ban đầu thiếu các cặp `origin -> target`.
2. Phân loại option theo vai trò ngữ nghĩa, không theo vị trí trong mảng: khởi tạo/nháp; chuỗi xử lý chính; chờ/tạm dừng; yêu cầu hủy và kết quả hủy; yêu cầu trả và chuỗi trả/hoàn; thành công; thất bại/từ chối/đóng. Dùng cả tên Object để phân biệt cùng một nhãn trong các ngữ cảnh khác nhau.
3. Dựng graph nhỏ nhất nhưng hoàn chỉnh:
   - `_initial` nối tới option default nếu option đó hợp lý là trạng thái bắt đầu; nếu không, tới option có ngữ nghĩa sớm nhất trong vòng đời.
   - Chuỗi chính theo chiều tiến triển nghiệp vụ (ví dụ nháp/mới → xác nhận/kích hoạt → đang xử lý → đã xử lý → đang giao → đã giao → hoàn tất) khi các option thực tế mang nghĩa đó.
   - Nhánh hủy chỉ từ trạng thái còn có thể hủy, ưu tiên qua trạng thái yêu cầu hủy nếu có; không hủy từ trạng thái đã trả, đã thất bại hoặc kết thúc.
   - Nhánh trả/hoàn chỉ từ trạng thái cho thấy hàng hóa/giao dịch đã phát sinh; ưu tiên chuỗi yêu cầu trả → đang trả → đã trả khi có đủ option.
   - Hoàn tất, hủy, trả xong, từ chối, đóng là terminal theo mặc định: không tạo outgoing flow trừ khi option khác thể hiện rõ thao tác mở lại, thử lại hoặc hoàn tác.
   - Trạng thái chờ/tạm dừng chỉ có lối vào/ra khi xác định được điểm tiếp tục hợp lý; không nối nó với mọi option.
4. Không tạo graph "mọi trạng thái đến mọi trạng thái"; không tạo bước lùi, reopen, retry hoặc undo nếu ngữ nghĩa option không thể hiện rõ chủ ý đó. Ràng buộc kết nối chung ở mục **Ràng buộc graph và bố trí không chồng lấn**.
5. Không tự thêm personnel filter, record filter, validation hoặc post-action (cần ID và chính sách doanh nghiệp cụ thể): dùng condition rỗng, `shouldFilterRecord: false` và `allowUndo: false`.
6. Nhiều graph đều hợp lý thì chọn graph bảo thủ có ít quyền chuyển hơn và nêu rõ giả định trong kết quả. Chỉ dừng để hỏi khi metadata không đủ về mặt kỹ thuật (không có option active hợp lệ, không resolve được duy nhất Object/field); không dừng chỉ vì người dùng chưa thiết kế flow.

## Đặt tên flow theo hành động

- `flow.name` luôn bằng tiếng Anh dù người dùng hoặc option dùng ngôn ngữ khác: cụm động từ ngắn mô tả hành động nghiệp vụ làm phát sinh chuyển trạng thái, ví dụ `Activate`, `Start packing`, `Finish packing`, `Ship`, `Complete`, `Put on hold`, `Resume`, `Request cancellation`, `Cancel`, `Request return`, `Confirm return`. Không đặt theo mẫu `{Origin} to {Target}` (`Draft to Activated`), `Change to {Target} status` hoặc raw slug.
- Flow `_initial -> option`: `Create`, `Initialize` hoặc `Start`; ưu tiên `Create` khi record được tạo ở trạng thái draft/new.
- `flow.slug` sinh từ action name theo ASCII `lower_snake_case`, duy nhất trong rule; nhiều origin dùng cùng action name thì thêm ngữ cảnh kỹ thuật vào slug (`request_cancellation_from_draft`), không biến display name thành cặp trạng thái.
- Mirror chính xác action name và slug vào `flow.metaData.edge.data.conditionBlocks`; dùng action name làm `edge.label`.

## Ràng buộc graph và bố trí không chồng lấn

Áp dụng cho create và mọi update có sửa graph.

- Kết nối: mỗi option là đúng một node; không self-loop, không target `_initial`, không trùng cặp có hướng.
- Thiết kế vị trí node và routing edge trước khi serialize metadata; không xếp cả graph trên một hàng chỉ vì chuỗi chính tuyến tính. Từ 8 node hoặc 12 flow: dùng nhiều hàng/lane, tách chuỗi chính, nhánh chờ, hủy, trả/hoàn và terminal vào lane khác nhau; chuỗi dài vượt ngân sách chiều rộng thì dùng hai hàng dạng snake.
- Kích thước: node `height: 48`, width `clamp(82, 40 + 8 * số ký tự, 240)` tính theo nhãn dài nhất giữa `value` và mọi translation có thể hiển thị; action label width `clamp(72, 32 + 8.5 * số ký tự, 260)`. Trên cạnh chính, khoảng trống giữa hai node ít nhất `actionLabelWidth + 120`; không dùng bước cố định nhỏ như 180px.
- Label: nhiều edge cùng target thì làm lệch midpoint của label; các label box không giao nhau và có ít nhất 16 graph units đệm. Hai edge ngược chiều giữa cùng hai node dùng route/handle khác nhau.
- Handle theo hướng layout đã xác minh: trái→phải `right -> left`, phải→trái `left -> right`, trên→dưới `bottom -> top`; edge ngược chiều dùng cặp khác như `top -> top` hoặc `left -> left`. Không gán cùng một handle mặc định cho mọi edge.
- Bounds: giữ trong ngân sách viewport tại min zoom; chưa đo được canvas thực tế thì dùng `2200 x 1300` graph units ở min zoom `0.5`.
- Trước mutation, kiểm tra hình học tối thiểu: node-node, edge-label–node và edge-label–edge-label không giao nhau; mọi node nằm trong bounds dự kiến. Sau mutation, đọc lại metadata và kiểm tra lại theo [Layout geometry UI-safe](references/api-contract.md#layout-geometry-ui-safe).
- Browser (khi người dùng báo lỗi hiển thị hoặc browser sẵn có) chỉ dùng để QA read-only; không tạo/sửa/lưu rule trên UI. Chỉ đo bounding box sau khi UI nạp đủ `optionCount + 1` node và `flowCount` edge label; chỉ báo đã sửa UI khi không còn collision và không node nào nằm ngoài canvas.

## Verify sau khi ghi

- Sau mọi create/update/status/delete, đọc lại bằng ID rồi so sánh trước/sau; không dựa riêng vào response mutation.
- So flows theo ID/slug hoặc cặp `originValue -> targetValue`, không yêu cầu giữ nguyên thứ tự mảng. Read-back không echo một key Boolean `false` thì kiểm tra bản mirror trong `metaData` trước khi báo lệch.
- Sau create/update, parse và validate schema UI của rule-level và tất cả flow-level `metaData` theo [Checklist metadata UI sau khi ghi](references/api-contract.md#checklist-metadata-ui-sau-khi-ghi). API có thể trả `r: 0` cho metadata tối giản nhưng UI React Flow vẫn lỗi khi thiếu state của node/edge; không báo hoàn tất khi checklist schema và hình học UI chưa đạt.

## Xem danh sách hoặc chi tiết

- `GET /api/v1/object_security/transition_rule?objectSlug={objectSlug}`: các rule của Object. `GET /api/v1/object_security/transition_rule?id={ruleId}`: chi tiết mới nhất kèm `flows`.
- Parse `metaData` chỉ khi cần phân tích graph; giữ nguyên chuỗi gốc để update an toàn.
- Một số deployment trả `objectSlug: null` trong detail: xác minh ownership bằng `objectTypeId` đã resolve và list theo Object; không coi `null` là bằng chứng rule thuộc sai Object.

## Tạo rule

1. Xác định từng cặp `originValue -> targetValue`: người dùng đã cung cấp thì tôn trọng các cặp đó sau khi validation; chưa cung cấp thì tự dựng theo mục **Tự thiết kế flow khi người dùng không cung cấp cặp chuyển** và tiếp tục tạo rule.
2. name và slug unique theo Object, không chỉ theo field; độ dài và regex theo contract. Đếm tổng số rule và số rule active của Object trước create: backend giới hạn 50 rule và 5 rule active trên một Object; đạt giới hạn thì dừng và báo lỗi, không tự hạ xuống inactive để lách.
3. Tạo ít nhất một flow, đặt tên theo mục **Đặt tên flow theo hành động**. `_initial` chỉ làm `originValue` cho transition khởi tạo; mọi giá trị khác phải là option slug thật.
4. `status: 1` (active) theo mặc định, kể cả khi flow do skill tự thiết kế; `status: 0` (inactive) chỉ khi người dùng yêu cầu rõ.
5. Rule-level `metaData` và từng flow-level `metaData` (đều là JSON string) nhất quán với `flows`, theo UI-safe baseline và yêu cầu hình học trong contract. Mỗi flow phải có `conditionBlocks.logicType` và `conditionBlocks.logic`, kể cả khi không có condition. Không dùng metadata tối giản chỉ có `id/type/position/data` cho node hoặc `source/target/type/data` cho edge.
6. Chỉ bật `shouldFilterRecord` khi đã xác minh toàn bộ condition bằng field metadata thật; khi false, không tự tạo `recordFilter`.
7. Gọi `POST /api/v1/object_security/transition_rule/create`, lấy ID từ `data[0].id`, rồi view lại theo ID.

## Cập nhật rule hoặc flows

1. View theo ID ngay trước update; xác nhận rule thuộc đúng Object và field.
2. Không đổi `objectFieldId`; backend giữ field hiện tại khi update. Cần field khác thì tạo rule mới.
3. Scalar (name, description, status, sort): gửi payload tối thiểu gồm `id` và trường cần đổi. Không hứa slug đã đổi cho tới khi view lại xác nhận, vì một số bản backend validate nhưng không persist slug update.
4. `flows` là cấu hình thay thế toàn bộ: sửa một flow thì gửi lại **toàn bộ** flows đã merge với thay đổi. Mảng khác rỗng xóa/tạo lại flows phía server; `null`, bỏ trống hoặc `[]` không phải cách xóa tất cả.
5. Sửa graph: cập nhật đồng thời `flows`, rule `metaData` và từng flow `metaData`; giữ nguyên condition/personnel/post-action không liên quan và metadata UI hợp lệ ngoài phạm vi thay đổi; bổ sung mọi key baseline còn thiếu; kiểm tra lại theo mục **Ràng buộc graph và bố trí không chồng lấn**.
6. `cloneTargetValue` chỉ nhận option slug là target trực tiếp của một flow từ `_initial`; không còn hợp lệ thì gửi `null`.
7. Gọi `POST /api/v1/object_security/transition_rule/update`, rồi view lại và so sánh từng trường/flow mục tiêu.

## Bật hoặc tắt rule

1. View các ID đích; chỉ giữ rule cần đổi trạng thái. Trước khi active, đếm rule active của Object (giới hạn 5).
2. `status: 1` cho active, `status: 0` cho inactive. Không gửi `status: 2`: đó là trạng thái draft chỉ dùng trong UI trước khi create.
3. Gọi `POST /api/v1/object_security/transition_rule/updateMultiple` với `data: [{id,status}]` và `statusChanged` cùng giá trị.
4. View lại từng ID; không cho rằng batch thành công một phần nếu response không chỉ rõ.

## Xóa rule

1. Resolve và view từng ID; trình bày name, ID, Object, field, status và số flow. Cảnh báo rule active có thể đang chặn/cho phép chuyển trạng thái của record.
2. Chỉ sau khi người dùng xác nhận rõ danh sách ID (xóa không thể hoàn tác), gọi `POST /api/v1/object_security/transition_rule/deleteMultiple` với `{"data":[{"id":"..."}]}`.
3. View lại từng ID và list lại theo Object; chỉ báo đã xóa khi các ID không còn xuất hiện.

## Guardrail và xử lý lỗi đặc thù

- Không retry mù mutation khi timeout hoặc lỗi mạng. Create không rõ kết quả: list theo Object và tra slug/name trước khi thử lại.
- HTTP `422` hoặc `r != 0`: dừng mutation, đối chiếu [bảng mã lỗi](references/api-contract.md#error-thường-gặp) của contract.

## Trả kết quả

- Read: danh sách gọn (tối thiểu ID, name, slug, status, field ID/name, sort, số flow, thời gian update) kèm Object/field và các cặp flow.
- Create/update/status: ID, name, slug, status, field và trạng thái đã view lại; nêu rõ trường nào server không persist. Flow do skill tự suy luận: liệt kê các cặp đã tạo, tóm tắt logic nghiệp vụ và các giả định bảo thủ.
- Create đã view lại thành công: trả thêm link cấu hình rule dạng Markdown `[https://{WORKSPACE_DOMAIN}/settings/transition/{objectSlug}/rule/{RULE_ID}](https://{WORKSPACE_DOMAIN}/settings/transition/{objectSlug}/rule/{RULE_ID})` với hostname workspace đã chuẩn hóa, Object slug thật và ID do create trả về; không dựng hoặc trả link khi create chưa được xác minh thành công hay chưa có rule ID.
- Delete: danh sách ID đã gửi và kết quả xác minh từng ID.
