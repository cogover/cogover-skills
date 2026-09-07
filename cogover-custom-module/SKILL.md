---
name: cogover-custom-module
description: "Thiết kế, lập trình, kiểm thử và publish Cogover Custom Frontend Module, Custom Backend Module hoặc cả hai từ yêu cầu nghiệp vụ và Workspace đích. Khảo sát App/Object hiện có, thiết kế phần schema thiếu để duyệt bằng Excel, phối hợp Process khi cần trigger/lịch, cấu hình project/policy/key và bàn giao link frontend hoặc cURL backend qua Cogover Dev CLI. Dùng khi cần xây mới hoặc sửa Custom Module; không thay thế skill chuyên trách cho tác vụ cấu hình Object/Process đơn lẻ."
metadata:
  author: cogover
  version: "1.3.1"
---

# Cogover Custom Module

- **Phiên bản:** `1.3.1`
- **Ngày phát hành:** `2026-09-07`

## Tổng quan và phạm vi

Workflow điều phối cần môi trường có sub-agent, shell/HTTP, công cụ build/test và trình duyệt khi làm frontend. Nếu môi trường không có sub-agent, hoàn tất phần tư vấn/chuẩn bị có thể làm độc lập và nêu rõ điều kiện còn thiếu trước các bước bắt buộc giao agent; không giả lập một đánh giá độc lập bằng cách tự nhận vai reviewer. Credential theo `$cogover-api-auth`; lựa chọn nguồn credential riêng của Cogover Dev CLI theo tài liệu CLI đi kèm.

Custom Module dành cho nghiệp vụ mà các module có sẵn như Cogover Object hoặc Cogover Process chưa đáp ứng đủ. Có thể viết logic phía server, giao diện riêng hoặc cả hai, đồng thời tiếp tục sử dụng dữ liệu và quyền của Workspace. Nguồn tổng quan: [get-started-custom-module.md](references/get-started-custom-module.md).

| Loại | Chọn khi | Ví dụ |
|---|---|---|
| Custom Frontend Module | Cần màn hình riêng; các API hiện có đã đáp ứng dữ liệu và logic với quyền người dùng | Dashboard, màn hình tra cứu hoặc biểu mẫu tùy chỉnh |
| Custom Backend Module | Cần xử lý phía server, tổng hợp/ghi Object, API riêng hoặc tích hợp có thông tin bí mật | Tính giá, đồng bộ dữ liệu, API tổng hợp tồn kho |
| Cả hai | Màn hình riêng cần gọi logic riêng phía backend | Màn hình xử lý đơn hàng gọi API tính giá và cập nhật đơn |

Skill này điều phối vòng đời Custom Module. Dùng `$cogover-overview` làm nguồn kiến thức nền, không chuyển vòng về một orchestrator khác khi yêu cầu hiện tại đã thuộc Custom Module. Chỉ dùng public API, metadata Workspace và tài liệu sản phẩm để xác định khả năng; không yêu cầu truy cập mã nguồn/hạ tầng của Cogover.

## Đầu vào

- `WORKSPACE_DOMAIN`: hostname đầy đủ hoặc HTTPS origin của Workspace. Chấp nhận tên đầu vào viết nhầm `WORKSAPCE_DOMAIN`, chuẩn hóa về `WORKSPACE_DOMAIN`. Không tự nối domain suffix, không giữ path/query trong origin.
- **Workspace API Key**: dùng key đã được cung cấp hoặc credential store/secret manager của môi trường; chỉ hỏi khi thiếu hoặc không truy cập được. Không yêu cầu người dùng gửi lại key đã có. CLI dùng tên `COGOVER_API_KEY`.
- **Yêu cầu người dùng**: luồng nghiệp vụ, người sử dụng, dữ liệu vào/ra, thao tác đọc/ghi, UI, trigger/lịch/tích hợp nếu có và kết quả mong đợi. Tái sử dụng thông tin đã có; chỉ làm rõ phần chưa biết có ảnh hưởng thiết kế.
- Khi sửa dự án: nhận hoặc tra project ID/slug, thư mục source và version đang active. Resolve đúng project trước khi sửa.

Không ghi key/secret vào source, `cogover.json`, frontend bundle, archive, log hoặc báo cáo. Không hardcode credential tích hợp ngay cả trong source backend; chỉ dùng cơ chế secret được tài liệu sản phẩm hỗ trợ. Backend không mặc nhiên có mọi API của Node.js.

## Tài liệu theo nhánh

Đọc bản hiện tại của mỗi skill được gọi và các reference bắt buộc trước khi thao tác; truyền lại Workspace và yêu cầu đã xác định, không hỏi lặp đầu vào.

| Khi thực hiện | Tài liệu cần đọc |
|---|---|
| Mọi request xác thực, quản lý hoặc bàn giao cURL | [$cogover-api-auth](../cogover-api-auth/SKILL.md) và [CLI, session và bàn giao](references/cli-session-and-delivery.md) |
| Thiết kế quyền và tạo security rules cho Object mới | [$user-permission](../user-permission/SKILL.md) và [Object Security Rules API](../user-permission/references/api-object-security-rules.md), gồm rule giữ chỗ không chọn nhân sự |
| Quản lý backend, policy, key, version, production/preview | [Custom Backend Module API Reference](references/custom-backend-module-api-reference.md), phần tương ứng thao tác |
| Quản lý frontend, version và asset URL | [Custom Frontend Module API Reference](references/custom-frontend-module-api-reference.md), phần tương ứng thao tác |
| Viết hoặc sửa code backend, chọn API đặc biệt | [Cogover SDK API reference](references/api-reference.md): đọc nền tảng handler/router/request/response, errors và các mục capability đang dùng |
| Khởi tạo/code/test backend local | [Backend quick start](references/get-started-custom-backend-module.md) |
| Khởi tạo/build/test frontend local | [Frontend quick start](references/get-started-custom-frontend-module.md) |
| Frontend gọi backend | [Full-stack integration](references/full-stack-integration.md) |
| Preview/apply, ghi hàng loạt, tính decimal hoặc concurrency | [Batch writes và checkpoint](references/batch-writes-and-checkpoints.md), cùng contract state/locks/records trong SDK |

Hai API reference là nguồn chuẩn cho HTTP contract. Quick start cung cấp cách làm với CLI và sample; ID, field slug, policy và dữ liệu mẫu không thay thế dữ liệu thật của Workspace. Bản [SDK API reference](references/api-reference.md) được đóng gói từ tài liệu tiếng Việt của `@cogover/sdk` phiên bản `0.5.0`, đối chiếu ngày `2026-09-06`. Trước khi code, đọc các phần nền tảng và capability liên quan trong file này; nếu SDK cài đặt khác phiên bản, đối chiếu thêm tài liệu public đi kèm package. Không suy ra API từ tên gọi hoặc dùng API không được hỗ trợ. Hai HTTP API reference và ba quick start đóng gói cùng skill là snapshot tài liệu sản phẩm tiếng Việt ngày `2026-09-06`; mọi ID/metadata mẫu chỉ minh họa.

## Workflow

### Điều phối sub-agent

Agent chính giữ yêu cầu, quyết định kiến trúc, schema đã duyệt, contract tích hợp và nghiệm thu cuối. Phân công theo nhánh thực sự cần:

| Sub-agent | Phạm vi chịu trách nhiệm |
|---|---|
| Khảo sát | Bước 1, mục 2–3: khảo sát chung App/Menu, Object và Process hiện có; bàn giao metadata, bằng chứng và phần chưa xác minh cho agent chính |
| Thiết kế dữ liệu/Excel | Bước 2, khi cần bổ sung schema: một sub-agent khác với agent khảo sát thiết kế phần thiếu và bàn giao workbook `.xlsx` đã kiểm tra cùng tóm tắt delta cho agent chính |
| Security | Bước 2A: sub-agent riêng dùng `$user-permission` tạo và xác minh bộ security rules cho từng Object mới; agent chính phải chờ và nghiệm thu trước khi cho backend/frontend khởi tạo hoặc code |
| Process | Bước 3: dùng `$process-creator` thiết kế, tạo và kiểm thử Process cần thiết; tiếp tục phần phụ thuộc sau khi backend sẵn sàng ở bước 9 |
| Backend | Toàn bộ phần backend ở bước 7 và 8: khởi tạo local, code, unit tests/coverage và kiểm thử tích hợp backend |
| Frontend | Toàn bộ phần frontend ở bước 7 và 8: khởi tạo local, code, unit tests/coverage và kiểm thử browser |

- Dùng một sub-agent riêng cho mỗi nhánh; backend và frontend không giao chung cho một sub-agent. Tái sử dụng sub-agent phụ trách xuyên suốt bước 7–8 và các vòng sửa lỗi. Không tạo sub-agent cho nhánh đã xác định bỏ qua.
- Mỗi giao việc phải đủ đầu vào phù hợp giai đoạn: yêu cầu/tiêu chí nghiệm thu, đường dẫn skill và reference cần đọc, Workspace origin, metadata đã có, phạm vi đọc/ghi và file được sửa, đầu ra bàn giao, trạng thái phê duyệt cùng dependency còn chờ. Với nhánh triển khai, bổ sung metadata Object/field đã xác minh, project ID/slug/slot, contract route/input/output/error và fixture được sửa. Không yêu cầu kết quả khảo sát hoặc project chưa tạo làm đầu vào của chính bước khảo sát. Chỉ truyền cách truy cập credential an toàn hoặc tên profile; không chép secret vào prompt, báo cáo hay source. Sub-agent phải đọc skill hiện tại trước khi làm.
- Khảo sát → agent chính kiểm tra bằng chứng, chốt phạm vi → thiết kế dữ liệu/Excel nếu cần. Không bắt đầu thiết kế workbook khi còn thiếu metadata có ảnh hưởng tới schema. Agent chính giữ quyết định kiến trúc, rà soát workbook, trình người dùng duyệt và thực hiện ghi/đọc lại schema ở bước 2, mục 6–7.
- Nếu có Object mới, thứ tự bắt buộc là schema được duyệt → tạo/đọc lại schema → sub-agent Security hoàn tất bước 2A → agent chính nghiệm thu → khởi tạo/code backend và frontend. Trong lúc chờ chỉ tiếp tục khảo sát, thiết kế contract, ma trận quyền và kế hoạch test; không dựng source, scaffold, interface code hoặc test bằng fixture để đi trước bước Security.
- Sau khi đáp ứng bước 2A nếu có, chốt contract chung rồi cho các nhánh độc lập chạy song song trong thư mục riêng. Frontend có thể dùng fixture theo contract trong lúc chờ backend; kết quả này chưa thay thế test tích hợp thật. Điều phối lịch test ghi khi dùng chung dữ liệu để các agent không reset hoặc sửa fixture của nhau.
- Agent chính thực hiện bước 4–6 để cung cấp project/policy/key đúng nhánh, tổng hợp yêu cầu duyệt còn thiếu và phụ trách bước 9–10. Chỉ giao quyền thao tác Workspace đã được phép; delegation không thay thế duyệt Excel hoặc duyệt Process.
- Nhận lại source, lệnh build/test, báo cáo coverage riêng từng project, kết quả kiểm thử và dependency còn thiếu. Kiểm tra bằng chứng, giao lại lỗi cho sub-agent phụ trách và nghiệm thu tích hợp; không coi thông báo “xong” là bằng chứng PASS. Nếu môi trường không hỗ trợ sub-agent, báo rõ giới hạn, hoàn thành phần độc lập và không tuyên bố đã đáp ứng yêu cầu phân công này.

### 1. Khảo sát và chọn frontend/backend

1. Đọc [$cogover-overview](../cogover-overview/SKILL.md), rồi các reference tính năng của miền nghiệp vụ liên quan.
2. **Giao một sub-agent khảo sát thực hiện cả mục 2–3, chỉ đọc cấu hình và metadata Workspace.** Truyền yêu cầu nghiệp vụ, phạm vi khảo sát và kết quả đọc overview ở mục 1. Sub-agent dùng [$app-menu-manager](../app-menu-manager/SKILL.md) cùng `$cogover-api-auth` để liệt kê App thật trên Workspace (`GET /api/v1/apps`, phân trang `page`/`limit` theo contract), đọc detail/menu của các App liên quan. Ghi nhận ID, slug, standard/custom, trạng thái, phạm vi quyền và các chức năng có sẵn. App bị ẩn/thiếu quyền hoặc list chưa đủ trang không chứng minh App chưa cài; phân biệt chưa có, inactive và chưa xác minh được.
3. Cùng sub-agent khảo sát dùng [$object-info](../object-info/SKILL.md) đọc Objects, fields, options, metadata, related lists liên quan. Khi có automation cũ, khảo sát Process theo `$process-creator` trước khi đề xuất thêm. Bàn giao cho agent chính báo cáo gồm App/Menu và chức năng có sẵn; mapping Object/field/option/quan hệ đã xác minh; Process liên quan nếu có; phần thiếu dự kiến; nguồn bằng chứng API/metadata, phạm vi phân trang và các điểm chưa xác minh kèm lý do. Không đưa credential vào báo cáo.
4. Agent chính kiểm tra báo cáo, giao lại phần khảo sát thiếu hoặc mâu thuẫn trước khi chốt quyết định phụ thuộc vào phần đó. Lập bảng ngắn: yêu cầu → khả năng chuẩn và bằng chứng trên Workspace → phần thiếu → nơi xử lý (cấu hình chuẩn/frontend/backend/Process). Chọn loại module theo phần thiếu thực tế. Nếu chức năng chuẩn đáp ứng trọn vẹn, giải thích và dùng skill chuyên trách; không tạo project rỗng chỉ để đủ bước. Nếu người dùng yêu cầu rõ trải nghiệm riêng, vẫn thiết kế phần custom cần thiết.
5. Chốt contract nghiệp vụ dự kiến: routes/methods, input/output, caller, dữ liệu thay đổi và tiêu chí nghiệm thu. Không coi danh mục App trong overview là danh sách App đã cài.

### 2. Thiết kế dữ liệu và duyệt Excel

Agent chính dùng kết quả khảo sát đã kiểm tra và phạm vi nghiệp vụ đã chốt để xác định có cần bổ sung schema. Nếu cần, **giao một sub-agent thiết kế dữ liệu/Excel riêng, khác sub-agent khảo sát**, thực hiện mục 1–4 với vai trò chuyên gia thiết kế cơ sở dữ liệu. Truyền báo cáo khảo sát, mapping metadata, yêu cầu dữ liệu/quyền/truy vấn và phạm vi delta dự kiến; sub-agent đối chiếu và hoàn thiện thiết kế trước khi tạo workbook. Agent chính phụ trách rà soát, trình duyệt và ghi schema ở mục 5–7. Nếu schema đã đủ, ghi kết luận và bỏ qua sub-agent Excel, workbook và tạo Object.

1. Xác định thực thể, nguồn dữ liệu chuẩn, quan hệ một-nhiều/nhiều-nhiều, vòng đời, khóa nghiệp vụ, yêu cầu chống trùng, field bắt buộc, kiểu số/ngày/tiền, quyền và truy vấn chính. Tái sử dụng Object nền tảng và Object nghiệp vụ đã có; không tạo bản sao chỉ vì khác tên hiển thị.
2. Phân loại: tái sử dụng nguyên trạng, bổ sung field/option/quan hệ hoặc tạo Object mới. Chỉ thêm phần thiếu, ghi rõ lý do và tác động với dữ liệu/cấu hình đang dùng.
   Với mỗi Object mới, lập ma trận Create/View/Edit/Delete: người dùng nào được thao tác trực tiếp, phạm vi record/field và action nào chỉ backend được thực hiện. Object do backend quản lý đóng vai trò bảng dữ liệu cho logic ứng dụng, có thể chặn toàn bộ hoặc một phần CRUD trực tiếp; không nhầm loại này với Object nền tảng có sẵn. Đưa ma trận quyền vào bản tóm tắt thiết kế kèm workbook để agent chính chốt trước khi tạo rules.
3. Nếu đối chiếu cho thấy schema đã đủ, sub-agent báo lại kết luận và lý do cho agent chính, không tạo workbook rỗng. Nếu cần bổ sung, sub-agent dùng [$create-cogover-objects](../create-cogover-objects/SKILL.md) tạo workbook `.xlsx` cho phần schema đề xuất. Phân biệt Object mới và delta trên Object hiện có, chỉ rõ lookup tới Object đã tồn tại để không tạo trùng. Theo hướng dẫn spreadsheet và validator của skill đó; sửa mọi lỗi trước khi bàn giao. Trả file `.xlsx` tại đường dẫn agent chính truy cập được, tóm tắt delta/lý do/tác động, mapping lookup và kết quả kiểm tra cùng các điểm còn cần quyết định; không tạo hoặc sửa schema trên Workspace.
4. Mỗi Object có đúng một record-name slug `name`, type Short text hoặc Auto number; tiền dạng số dùng Decimal. Giữ slug/ID tham chiếu thật và không tạo lại field hệ thống.
5. Agent chính mở workbook, đối chiếu nội dung với yêu cầu, metadata đã khảo sát và bằng chứng kiểm tra; giao lại sub-agent thiết kế sửa nếu thiếu hoặc sai. **Bắt buộc đưa file Excel đã rà soát cùng bản tóm tắt delta và ma trận quyền để người dùng duyệt trước khi ghi schema.** Yêu cầu chung “tạo module” chưa thay thế việc duyệt workbook này. Trong lúc chờ chỉ hoàn thiện thiết kế và kế hoạch test; chưa tạo Object/field hoặc viết code. Khi có Object mới, tiếp tục chờ hoàn tất bước 2A trước khi khởi tạo/code.
6. Sau khi workbook được duyệt, dùng `$object-info` đọc lại state mới nhất, tạo Object/field theo dependency và đúng bản đã duyệt. Đối với quan hệ vòng, tạo Object trước rồi thêm lookup sau khi đã có ID. Nếu delta thay đổi do Workspace đã đổi, chỉ xin duyệt lại phần thay đổi thực chất.
7. Đọc lại toàn bộ schema đã ghi, so với workbook; ghi mapping ID/slug/options dùng cho code và Process. Nếu thao tác dở dang, liệt kê phần đã tạo, tra lại trước retry, không tự xóa để làm lại.

### 2A. Tạo security rules cho từng Object mới trước khi code

**Bắt buộc khi bước 2 tạo Object mới; giao một sub-agent Security riêng thực hiện.** Nếu chỉ tái sử dụng Object hoặc bổ sung field, không tự tạo lại bộ rules hay thay đổi quyền ngoài phạm vi yêu cầu; đánh giá quyền hiện có và xử lý delta được yêu cầu bằng `$user-permission`.

1. Agent chính giao mapping Object/field đã đọc lại, ma trận quyền đã chốt, phạm vi thao tác được phép và cách truy cập credential an toàn. Sub-agent đọc bản hiện tại của `$user-permission`, Object Security Rules API và `$cogover-api-auth`; đọc rules/Role liên quan trước khi ghi để tránh trùng khi retry và phát hiện quyền đã được cấp. Không tự mở rộng Role để làm test thành công.
2. Mỗi Object mới có bộ mặc định **bốn rules riêng: một Create, một View, một Edit, một Delete**, kể cả action không cho người dùng thực hiện trực tiếp. Create dùng `type: 1` với duy nhất scope `create`; ba action còn lại dùng `type: 2`, chỉ cấp scope của action chính và đặt các scope khác thành `none`/`no`. Theo contract của `$user-permission`; không gộp action. Có thể bổ sung rule cùng action khi audience, điều kiện record hoặc field scope khác nhau.
3. Với action chỉ backend được thực hiện, tạo rule giữ chỗ active (`status: 1`) với đúng `personnelFilters: [{"type": 1, "op": "include", "personnelId": null}]`. Giữ scope hợp lệ của action đó. Audience này không khớp nhân sự nào nên không cấp quyền cho ai; rule vừa giữ slot action vừa giúp Object duy trì chế độ mặc định từ chối. Đây không phải lệnh cấm có ưu tiên cao hơn quyền do rule khác cấp: phải kiểm tra mọi active rule để chắc không rule nào cấp lại action đang muốn chặn. Không bỏ rule, thay `null` bằng ID giả hoặc tắt rule giữ chỗ để biểu diễn chặn truy cập. Xem ví dụ và scope trong `$user-permission`.
4. Ví dụ Object “Lượt khuyến mãi đã sử dụng”: View rule cấp đọc cho audience và phạm vi record/field đã chốt; Create/Edit/Delete là ba rule giữ chỗ không chọn nhân sự. Nếu toàn bộ CRUD chỉ dành cho backend, cả bốn rules dùng audience giữ chỗ. Khi không có rule active, lớp bảo mật chi tiết không hạn chế record/field và quyền qua Role áp dụng trên toàn bộ dữ liệu; không diễn giải thành mọi user tự có đủ CRUD.
5. Sub-agent tạo rules trong phạm vi đã được phép, đọc lại danh sách không lọc trạng thái và detail của từng rule. Bàn giao Object ID/slug → rule ID/action/type/status/audience/filter/scopes, đối chiếu ma trận quyền, kết quả kiểm thử trực tiếp theo `$user-permission` và phần chưa kiểm thử. Rule giữ chỗ phải còn active và `personnelId` phải là JSON `null`; xác minh không có grant ngoài ý muốn từ rule khác. Nếu request dở dang, đọc lại trước retry, không tạo bốn rule mới chồng lên bộ đã có.
6. **Agent chính phải chờ sub-agent hoàn tất và nghiệm thu cấu hình trước khi chuyển sang bước 7–8:** mọi Object mới có đủ bốn slot action active, phạm vi quyền khớp thiết kế và có bằng chứng đọc lại. Thiếu rule, cấu hình sai, thao tác lỗi hoặc sub-agent chưa hoàn tất thì chưa được code. Không có công cụ sub-agent thì báo rõ dependency và dừng trước bước code. Kiểm tra cấu hình không thay thế kiểm thử runtime; nếu thiếu credential/fixture thì ghi rõ giới hạn và theo dõi ca test còn thiếu. Kiểm thử đường backend dùng quyền hệ thống được thực hiện sau khi backend sẵn sàng ở bước 8–9, không yêu cầu backend tồn tại để hoàn tất bước cấu hình này.

### 3. Bổ sung Process khi thực sự cần

- Khi cần chạy theo sự kiện record hoặc theo lịch độc lập với người mở trang/gọi API, **giao một sub-agent Process riêng** dùng [$process-creator](../process-creator/SKILL.md) thực hiện bước này. Sub-agent xác định event, conditions, timezone/lịch, chống lặp và output cần kiểm chứng, rồi thiết kế Triggered Flow hoặc Scheduled Flow phù hợp.
- Nếu Custom Module xử lý trọn vẹn yêu cầu trong request hiện tại, bỏ qua Process. Không mặc định backend tự đăng ký trigger/cron; không dùng timer trình duyệt hoặc tiến trình local thay cho lịch chạy trên Workspace.
- Sub-agent gửi flow cụ thể cho agent chính tổng hợp bước xác nhận của `$process-creator`; tái sử dụng xác nhận đã có cho đúng flow. Sau khi đủ phê duyệt, sub-agent tạo, đọc lại, kích hoạt và kiểm thử theo skill đó, trả Process ID/link, instance và bằng chứng hiệu ứng nghiệp vụ.
- Nếu Process phải gọi backend chưa publish, chuẩn bị thiết kế ở bước này, hoàn tất cấu hình phụ thuộc và kích hoạt sau bước 9. Không kích hoạt flow có URL/ID giả hoặc dependency chưa sẵn sàng.
- Chỉ nối Process → backend khi contract hỗ trợ cách gọi và danh tính cần thiết. Project key không dùng để gọi production; session export ngắn hạn không phải credential bền vững để nhúng vào lịch Process. Nếu chưa có cơ chế được hỗ trợ, báo chính xác dependency còn thiếu và hoàn thành các phần độc lập.

### 4. Tạo Project trên Workspace

1. Đọc API reference đúng nhánh. Qua phiên Workspace dùng service `4`, list tất cả trang cần thiết để kiểm tra trùng slug, rồi create hoặc tái sử dụng đúng project đã được chỉ định.
2. Backend: `POST /api/v1/ts-projects`. Frontend: `POST /api/v1/ts-projects/frontend`. Body gồm `name`, `slug`, `description` khi cần.
3. Module slug bất biến, theo `[A-Za-z_][A-Za-z0-9_]{0,99}`; không áp regex slug Process một cách máy móc. ID do server cấp.
4. Đọc lại project vừa tạo. Ghi backend `projectId`/`slug`; frontend `projectId`/`slug`/**`slugSlot`**. Hai project full-stack có cấu hình riêng. CLI publish/activate không tạo Project.

### 5. Cấu hình Project policy nếu cần

- Đối với frontend thuần: bỏ qua; frontend không có identity-policy endpoint trong contract này.
- Backend dùng quyền caller mặc định và không gọi `data.asSystem()`/`data.asUser()`: không tạo policy vô cớ. Các API đặc biệt khác phải được kiểm tra theo SDK contract, không cho rằng identity policy mở được mọi capability.
- Với action bị chặn trực tiếp trên Object do backend quản lý ở bước 2A, backend dùng `data.asSystem()` và policy giới hạn đúng caller/Object/operation cần thiết. Code chạy phía backend không tự vượt security rules khi vẫn dùng quyền caller. Trước khi dùng quyền hệ thống, backend phải kiểm tra người gọi có quyền thực hiện nghiệp vụ; policy không thay thế kiểm tra này.
- Nếu dùng quyền ủy quyền, đọc mục Identity policy trong Backend API Reference. Thiết kế schema version `2`, giới hạn caller personnel, Object và operation cần thiết; `data.asUser` còn giới hạn personnel đích. Resolve ID/slug thật, giữ grant ngoài phạm vi khi sửa.
- Lưu editable policy → đọc lại → activate policy cho nhu cầu phát triển. Phân biệt policy đang chỉnh sửa với snapshot bất biến đã duyệt cho từng version; sửa policy đưa editable policy về `DRAFT`.
- Sau publish có version `READY`, approve policy cho **đúng version** rồi đọc snapshot, kiểm tra revision/hash/grants theo reference. Activate version không tự duyệt policy. Một policy được approve trước đây không mặc nhiên áp dụng cho version mới.
- Policy không cấp quyền chạy module nói chung và không thay thế quyền của user đích; permission ceiling của Project key chỉ thu hẹp quyền. Không thêm grant rộng để che lỗi `403`.

### 6. Tạo Project key nếu backend local cần kết nối Workspace

1. Frontend bỏ qua bước này. Backend xử lý thuần túy có thể test bằng fixture không cần key; backend local cần gọi SDK capability thật thì cần key.
2. Đọc mục Project key; resolve caller personnel, hạn dùng và `permissionCeiling` schema version `1` theo hành vi test. Cho phép writes/asSystem/asUser chỉ khi cần trong phạm vi bài toán.
3. Tạo key bằng `POST /api/v1/ts-projects/{projectId}/keys`, hoặc tái sử dụng key còn hiệu lực đúng project/caller và quyền. Không rotate key đang được người khác dùng chỉ để lấy lại secret.
4. Giá trị `projectKey` chỉ trả một lần lúc create/rotate. Chuyển trực tiếp vào credential store hoặc prompt ẩn của CLI qua kênh an toàn; không in raw response. Lưu metadata key ID/caller/hạn dùng để kiểm chứng, không lưu secret vào tài liệu.
5. Dùng `cogover-dev login --profile <PROFILE>` và `doctor` theo reference CLI. Không dùng Workspace API key thay Project key, hoặc ngược lại.

### 7. Khởi tạo local để build/test

- Nếu có Object mới, chỉ giao khởi tạo sau khi agent chính đã nghiệm thu bước 2A và cung cấp mapping rules/quyền cho sub-agent backend/frontend. Không dùng fixture để bỏ qua điều kiện này.
- **Backend — giao sub-agent backend riêng:** làm theo Backend quick start; dùng starter public được liên kết, tạo `cogover.json` với Workspace origin, Project ID/slug thật và `projectType: "backend"`. `src/main.ts` là entrypoint default export; `local/` chỉ là local runner, không import từ `src/` và không upload. Sub-agent này tiếp tục code/test backend ở bước 8.
- **Frontend — giao sub-agent frontend riêng:** làm theo Frontend quick start; tạo Vite TypeScript hoặc stack phù hợp yêu cầu. Đặt `base: "./"`, build ra `dist/index.html`, dùng hash routing nếu có SPA. `cogover.json` phải ghi `projectType: "frontend"` (bỏ qua sẽ mặc định backend). Sub-agent này tiếp tục code/test frontend ở bước 8.
- Mỗi sub-agent cấu hình unit-test runner và coverage phù hợp stack ngay khi khởi tạo project, có lệnh tái chạy được (ví dụ `npm run test:unit:coverage`) và ngưỡng **line coverage >= 70% cho riêng project đó**. Lệnh phải trả exit code khác 0 nếu có unit test thất bại hoặc coverage dưới ngưỡng.
- Kiểm tra Node.js >= 20, CLI version/help và dependency thực tế. `auth session` cần CLI >= 0.9.0. Dùng Workspace origin đã xác định, không để CLI rơi về runtime mặc định.
- Full-stack có hai thư mục/cấu hình độc lập; proxy frontend local tới backend loopback theo [Full-stack integration](references/full-stack-integration.md).

### 8. Code và test local

Sub-agent backend thực hiện phần backend; sub-agent frontend thực hiện phần frontend. Mỗi sub-agent viết unit tests cùng lúc code và tự sửa lỗi tới khi đạt điều kiện bên dưới; agent chính phối hợp kiểm thử xuyên hai project.

1. Code theo contract nghiệp vụ và schema đã xác minh. Backend dùng public `@cogover/sdk`, chỉ import package được hỗ trợ và local source; không đưa Node built-in, local runner, dynamic import hoặc `require()` vào code publish. Đọc [SDK API reference](references/api-reference.md) cho router, data, identity và API tích hợp thực sự sử dụng. Sinh `workspace.d.ts` từ metadata Workspace theo mục Khai báo Workspace; sau thay đổi schema phải sinh lại. SDK Schema API chỉ đọc; tạo/sửa schema vẫn qua `$object-info`. Với HTTP ngoài, ưu tiên import `fetch` từ SDK để local không âm thầm dùng native fetch; Project state không dùng lưu secret. Đọc mục state/locks khi cần checkpoint hoặc concurrency; lock không tạo transaction hay exactly-once. Thông báo API trả client dùng tiếng Anh.
2. Dùng caller identity mặc định, kiểm tra input, chỉ đọc field cần thiết và xử lý kết quả thiếu/null, phân trang, lỗi từng phần. Không tin `personnelId` do client gửi để tự nâng quyền.
3. Test logic, input không hợp lệ, thiếu record, quyền được phép/bị từ chối và ghi lặp khi liên quan. Với decimal, preview/apply hoặc ghi hàng loạt, đọc [Batch writes và checkpoint](references/batch-writes-and-checkpoints.md), kiểm tra làm tròn, request đồng thời, preview cũ và lỗi từng phần. Chạy typecheck/build và các test phù hợp dự án.
4. Backend có dữ liệu thật chạy qua `COGOVER_LOCAL_PORT=<PORT> cogover-dev run --profile <PROFILE> --allow-writes=false -- npm run dev` cho test đọc. Với test ghi đã nằm trong phạm vi yêu cầu, dùng `--allow-writes=true` và fixture có marker/ID theo dõi. CLI mặc định cho writes; chạy local không đồng nghĩa mock hay dry-run.
5. Test frontend trên browser: loading, empty, error, thao tác chính, khả năng dùng bàn phím và kích thước màn hình liên quan. Full-stack phải test xuyên frontend → backend → dữ liệu.
6. Khi ghi có thể đã thành công trước khi lỗi, đọc lại state trước retry; nhiều lệnh ghi không mặc nhiên là transaction. Lưu kết quả test và fixture đã chạm tới, không lưu credential.

**Điều kiện bắt buộc cho từng project trước khi kết thúc bước 8:**

- Toàn bộ unit tests phải PASS, số test thất bại bằng 0, có test thực sự được chạy; không dùng suite rỗng hoặc skip/todo để thay thế các ca cần kiểm chứng. Typecheck/build và các test tích hợp/browser thuộc phạm vi cũng phải thành công.
- **Line coverage >= 70% riêng backend và >= 70% riêng frontend** nếu có cả hai. Không lấy trung bình hoặc gộp coverage hai project để bù cho nhau; không dùng branch/function/statement coverage thay line coverage.
- Đo coverage từ unit-test suite trên toàn bộ source ứng dụng của project, kể cả file chưa được test import. Chỉ loại trừ dependency, test/fixture, build output, code sinh tự động, declaration và cấu hình/local runner không thuộc code ứng dụng; ghi rõ cấu hình include/exclude. Không loại bỏ code nghiệp vụ, entrypoint hay UI cần chạy chỉ để đạt ngưỡng. Backend test logic/validation/error/side effect bằng dependency được kiểm soát; frontend test logic và component/hành vi UI phù hợp stack.
- Lưu lệnh test, số test pass/fail, số dòng covered/total, phần trăm lines và đường dẫn báo cáo coverage cho **mỗi project**, khớp source cuối sẽ publish. Không cộng E2E/integration coverage vào kết quả unit tests để đạt ngưỡng. Sau sửa code, chạy lại unit tests với coverage của project bị ảnh hưởng.
- Agent chính kiểm tra báo cáo và ngưỡng, yêu cầu sub-agent sửa nếu chưa đạt. Không chuyển project chưa đạt sang publish; coverage chưa đo hoặc thiếu báo cáo là chưa đạt, không tự coi là 70%.

### 9. Publish, activate và test trên Workspace thật

1. Agent chính xác minh test local và điều kiện bước 8: mỗi project có toàn bộ unit tests PASS, line coverage >= 70% cùng báo cáo đúng source cuối. Chưa đạt thì giao lại sub-agent phụ trách sửa trước publish. Ghi nhận active version hiện tại cho từng project và các thay đổi schema liên quan. Kiểm tra archive không có secret, `.env`, session file, source map hoặc dependency/local runner ngoài phạm vi.
2. Dùng `cogover-dev publish` tại đúng thư mục project. Backend ZIP chứa `src/main.ts`; frontend phải build trước, ZIP chứa `dist/index.html` (giữ thư mục `dist/`). CLI không build frontend. Nếu publish qua API trực tiếp, upload ZIP private và dùng file metadata thật cùng `idempotencyKey` theo reference; không đoán upload endpoint.
3. Chờ version `READY` hoặc `FAILED` có thời hạn, không coi HTTP `202` là hoàn tất. Khi timeout, đọc version đã tạo trước khi publish lại; khi `FAILED`, sửa nguyên nhân rồi tạo version mới. Ghi version ID và build error an toàn nếu có.
4. Backend có policy: approve/read snapshot đúng version theo bước 5. Có thể dùng preview service `6`, chỉ rõ version ID và `READ_ONLY`/`READ_WRITE`; preview mặc định `READ_WRITE`, ghi thật và không rollback theo nhóm.
5. Activate đúng version bằng CLI, đọc lại project xác nhận `ACTIVE` và `activeVersionId`. Full-stack: backend sẵn sàng trước frontend phụ thuộc nó; hoàn tất Process còn chờ dependency.
6. Backend: gọi production service `3` bằng session do CLI tạo, theo [mẫu cURL](references/cli-session-and-delivery.md). Kiểm tra HTTP/body và đọc lại dữ liệu nghiệp vụ; không lấy preview hoặc `READY` làm bằng chứng production PASS. Route dùng query string phải test filter có kết quả/không có kết quả và cursor trên production; nếu local khác Workspace, áp dụng mục tương thích trong [Full-stack integration](references/full-stack-integration.md).
7. Frontend: mở `https://{WORKSPACE_DOMAIN}/{slugSlot}/index.html` trong browser đã đăng nhập, xác minh asset/load/refresh và luồng nghiệp vụ với API thật. CLI publish không đăng nhập browser. Link frontend yêu cầu session Workspace, không phải trang công khai vô danh.
8. Xác minh quyền bằng caller phù hợp. Session từ Workspace API key không bảo đảm cùng user với Project key và không giả lập được user tùy ý; chưa test user thường thì báo đúng giới hạn.
   Với Object do backend quản lý, phối hợp sub-agent Security kiểm chứng action trực tiếp bị từ chối, action được phép (ví dụ View) vẫn hoạt động đúng phạm vi, và đường backend hợp lệ thực hiện được thao tác hệ thống. Kiểm thử cả caller không được phép gọi nghiệp vụ; không coi thành công dưới `data.asSystem()` là bằng chứng caller có quyền CRUD trực tiếp. Hoàn tất các ca runtime còn thiếu từ bước 2A trước khi tuyên bố quyền đã được kiểm thử end-to-end.
9. Với Process, kiểm chứng instance và hiệu ứng nghiệp vụ theo `$process-creator`, phục hồi lịch và quyền test tạm. Với module lỗi sau activate, ưu tiên activate lại version cũ còn hợp lệ trong phạm vi phục hồi; đọc lại xác nhận. Rollback version không hoàn tác schema/record writes hay side effect.
10. Phục hồi cấu hình test tạm, xóa file session export do tác vụ tạo khi dùng xong; fixture Workspace xử lý theo skill dữ liệu và phạm vi đã được phép. Báo rõ phần còn lại. Không tự xóa Project, schema hoặc Process để “cleanup”.

### 10. Bàn giao

- **Frontend:** link thật theo `slugSlot`, project/version đang active và kết quả browser test.
- **Backend:** lệnh `cogover-dev auth session --format curl --output ...` và **cURL hoàn chỉnh** tới production theo reference bàn giao. Điền domain, slug, method, route, payload đã kiểm thử; không đưa cookie/token thật vào câu trả lời. Kèm response mong đợi và cách tạo lại session khi hết hạn.
- **Cả hai:** bàn giao cả hai mục trên cùng mapping frontend → backend và thư mục source/lệnh build/test/publish để bảo trì.
- **Kiểm thử từng project:** kèm số unit tests pass/fail, line coverage (covered/total và %), lệnh tái chạy và đường dẫn báo cáo; nêu rõ sub-agent phụ trách backend/frontend/Process đã thực hiện phần nào. Không gộp hai project thành một chỉ số coverage.
- **Security:** kèm ma trận quyền, mapping bốn slot rule của từng Object mới và rules bổ sung nếu có, action chỉ backend được thực hiện, bằng chứng đọc lại/nghiệm thu của sub-agent Security và kết quả runtime cùng giới hạn còn lại. Phân biệt cấu hình đã xác minh với quyền đã kiểm thử end-to-end.
- Kèm phần schema đã tạo/tái sử dụng, workbook đã duyệt nếu có, Process/link/instance nếu có, policy/key ở mức metadata và bằng chứng kiểm thử. Báo `PASS`, `PARTIAL`, `FAIL` hoặc `BLOCKED` theo kết quả quan sát; liệt kê thiếu quyền/dependency/fixture còn lại. Chỉ gọi hoàn tất khi local và Workspace test đáp ứng tiêu chí của bài toán.
