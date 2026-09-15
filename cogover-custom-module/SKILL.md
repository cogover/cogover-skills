---
name: cogover-custom-module
description: "Điều phối vòng đời Cogover Custom Module: khảo sát App/Object, chọn backend/frontend và dạng frontend (single page app, custom component, Federation Page), người dùng xác nhận trước khi code, schema duyệt bằng Excel, security rules, Process, Project/policy/key, code/test theo template, publish qua Dev CLI, bàn giao. Không thay skill cấu hình Object/Process đơn lẻ."
metadata:
  author: cogover
  version: "1.4.1"
---

# Cogover Custom Module

- **Phiên bản:** `1.4.1`
- **Ngày phát hành:** `2026-09-15`

## Tổng quan và phạm vi

Skill điều phối toàn bộ vòng đời Custom Module. Dùng `$cogover-overview` làm kiến thức nền; không chuyển vòng về orchestrator khác khi yêu cầu đã thuộc Custom Module. Chỉ dùng public API, metadata Workspace và tài liệu sản phẩm để xác định khả năng; không yêu cầu mã nguồn/hạ tầng của Cogover.

Custom Module dành cho nghiệp vụ mà Cogover Object/Process chuẩn chưa đáp ứng đủ: logic phía server, giao diện riêng hoặc cả hai, vẫn dùng dữ liệu và quyền của Workspace.

| Loại | Chọn khi | Ví dụ |
|---|---|---|
| Custom Frontend Module | Cần màn hình hoặc thành phần giao diện riêng; API hiện có đã đủ dữ liệu và logic với quyền người dùng. Ba dạng: single page app, custom component nhúng layout Object, Federation Page trong ứng dụng Cogover | Dashboard toàn màn hình, khối kiểm tra mã giảm giá trên form đơn hàng, trang công cụ trong menu ứng dụng |
| Custom Backend Module | Cần xử lý phía server, tổng hợp/ghi Object, API riêng hoặc tích hợp có thông tin bí mật | Tính giá, đồng bộ dữ liệu, API tổng hợp tồn kho |
| Cả hai | Màn hình riêng cần gọi logic riêng phía backend | Màn hình xử lý đơn hàng gọi API tính giá và cập nhật đơn |

Mã frontend được tải xuống trình duyệt: logic nhạy cảm, quyền nâng cao và credential tích hợp phải nằm ở backend.

Ba dạng frontend khác nhau về bộ khung code và nơi hiển thị: single page app dùng stack tự chọn và mở qua `/{slugSlot}/index.html`; custom component và Federation Page bắt buộc dùng template React `custom-frontend-module-template` của Cogover, lần lượt nhúng vào layout Object qua item Federation component và hiển thị tại `/{APP_SLUG}/c{N}/{PATH}`. Chọn theo [Các loại Custom Module và dạng frontend](references/get-started-custom-module.md); lựa chọn phải được người dùng xác nhận theo mục 1A trước khi phát triển.

Môi trường cần sub-agent, shell/HTTP, công cụ build/test và trình duyệt khi làm frontend. Không có sub-agent: hoàn tất phần tư vấn/chuẩn bị làm được độc lập, nêu rõ điều kiện còn thiếu trước các bước bắt buộc giao agent, không tuyên bố đã đáp ứng yêu cầu phân công và không tự nhận vai reviewer để giả lập đánh giá độc lập.

## Đầu vào

- `WORKSPACE_DOMAIN`: hostname đầy đủ hoặc HTTPS origin. Chấp nhận tên viết nhầm `WORKSAPCE_DOMAIN` và chuẩn hóa về `WORKSPACE_DOMAIN`; không tự nối domain suffix, không giữ path/query trong origin.
- Workspace API Key. Credential, header và quy ước response/lỗi chung: theo [$cogover-api-auth](../cogover-api-auth/SKILL.md). Skill dùng cả `/bapi/v1` (API Key Bearer: tạo phiên, metadata) lẫn `/api/v1` (phiên Web App: App, quản lý Project, gọi module); ngoại lệ riêng: quản lý TS Project dùng `POST` với `x-req-service: 4` cho cả đọc/list và trả object trực tiếp, không bắt buộc envelope `r: 0`. Cogover Dev CLI đọc key theo tên `COGOVER_API_KEY` với thứ tự nguồn credential riêng: [CLI, session và bàn giao](references/cli-session-and-delivery.md).
- Yêu cầu người dùng: luồng nghiệp vụ, người sử dụng, dữ liệu vào/ra, thao tác đọc/ghi, UI, trigger/lịch/tích hợp, kết quả mong đợi. Chỉ làm rõ phần chưa biết có ảnh hưởng thiết kế.
- Sửa dự án: tra project ID/slug, thư mục source và version đang active; resolve đúng project trước khi sửa.
- Không ghi key/secret vào source, `cogover.json`, frontend bundle, archive, log hay báo cáo. Không hardcode credential tích hợp kể cả trong source backend; chỉ dùng cơ chế secret được tài liệu sản phẩm hỗ trợ. Backend không mặc nhiên có mọi API của Node.js.

## Tài liệu theo nhánh

Đọc bản hiện tại của mỗi skill được gọi và reference bắt buộc trước khi thao tác; truyền lại Workspace và yêu cầu đã xác định, không hỏi lặp đầu vào.

| Khi thực hiện | Đọc |
|---|---|
| Chọn loại module và dạng frontend, chuẩn bị xác nhận 1A | [Các loại Custom Module và dạng frontend](references/get-started-custom-module.md) |
| Xác thực, quản lý Project hoặc bàn giao cURL | [$cogover-api-auth](../cogover-api-auth/SKILL.md) và [CLI, session và bàn giao](references/cli-session-and-delivery.md) |
| Thiết kế quyền, tạo security rules cho Object mới | [$user-permission](../user-permission/SKILL.md) và [Object Security Rules API](../user-permission/references/api-object-security-rules.md), gồm rule giữ chỗ không chọn nhân sự |
| Quản lý backend, policy, key, version, production/preview | [Custom Backend Module API Reference](references/custom-backend-module-api-reference.md) |
| Quản lý frontend, version và asset URL | [Custom Frontend Module API Reference](references/custom-frontend-module-api-reference.md) |
| Viết hoặc sửa code backend, chọn API đặc biệt | [SDK usage guide](references/cogover-sdk-usage-guide.md) đọc trước khi code (mẫu handler, filter, fetch, state, lock, danh tính, TypeScript config, router), rồi [SDK API reference](references/cogover-sdk-api-reference.md): nền tảng handler/router/request/response, errors và các mục capability đang dùng |
| Khởi tạo/code/test backend local | [Backend quick start](references/get-started-custom-backend-module.md) |
| Khởi tạo/build/test frontend single page app | [Frontend quick start](references/get-started-custom-frontend-module.md) |
| Khởi tạo/code/test custom component nhúng layout | [Custom component quick start](references/get-started-custom-component.md) cùng `README.vi.md`, `.agents/skills/custom-module-foundation`, `.agents/skills/custom-module-form-builder` và `src/types/form-builder.d.ts` trong template đã clone |
| Khởi tạo/code/test Federation Page | [Federation Page quick start](references/get-started-federation-page.md) cùng `README.vi.md`, `.agents/skills/custom-module-foundation` và `.agents/skills/custom-module-api` trong template đã clone |
| Frontend gọi backend | [Full-stack integration](references/full-stack-integration.md) |
| Preview/apply, ghi hàng loạt, decimal hoặc concurrency | [Batch writes và checkpoint](references/batch-writes-and-checkpoints.md), cùng contract state/locks/records trong SDK |

Hai API reference là nguồn chuẩn cho HTTP contract; quick start chỉ là cách làm với CLI và sample. Tất cả là snapshot tài liệu sản phẩm tiếng Việt ngày `2026-09-06`, riêng ba tài liệu về các dạng frontend, custom component và Federation Page ngày `2026-09-15`; SDK usage guide và SDK API reference theo `@cogover/sdk` `0.5.0` (snapshot ngày `2026-09-15`), SDK cài đặt khác phiên bản thì đối chiếu thêm tài liệu public đi kèm package. Với custom component và Federation Page, các skill trong `.agents/skills` của template đã clone là nguồn chuẩn cho quy ước code (expose, routing, `Link`, asset, API client, i18n); skill này quyết định workflow, phê duyệt, kiểm thử và publish. Template thay đổi thì theo bản đã clone, không theo trích dẫn trong quick start. ID, field slug, policy và dữ liệu mẫu chỉ minh họa, không thay dữ liệu thật của Workspace. Không suy ra API từ tên gọi hoặc dùng API không được hỗ trợ.

## Workflow

### Điều phối sub-agent

Agent chính giữ yêu cầu, quyết định kiến trúc, schema đã duyệt, contract tích hợp và nghiệm thu cuối; tự làm bước 4–6 và 9–10, tổng hợp các yêu cầu duyệt còn thiếu. Phân công theo nhánh thực sự cần, mỗi nhánh một sub-agent riêng:

| Sub-agent | Phạm vi |
|---|---|
| Khảo sát | Bước 1 mục 2–3, chỉ đọc cấu hình và metadata Workspace |
| Thiết kế dữ liệu/Excel | Bước 2 mục 1–4 khi cần bổ sung schema; khác sub-agent khảo sát |
| Security | Bước 2A cho từng Object mới, dùng `$user-permission` |
| Process | Bước 3, dùng `$process-creator`; phần phụ thuộc backend hoàn tất sau bước 9 |
| Backend | Bước 7–8 phần backend: khởi tạo local, code, unit tests/coverage, kiểm thử tích hợp |
| Frontend | Bước 7–8 phần frontend theo dạng đã xác nhận ở 1A: khởi tạo local, code, unit tests/coverage, kiểm thử browser. Custom component/Federation Page: clone template và đọc `.agents/skills` trước khi code |

- Backend và frontend không giao chung một sub-agent. Tái sử dụng sub-agent phụ trách xuyên suốt bước 7–8 và các vòng sửa lỗi; không tạo sub-agent cho nhánh đã bỏ qua.
- Gói giao việc: yêu cầu và tiêu chí nghiệm thu; loại module và dạng frontend đã được người dùng xác nhận ở 1A; đường dẫn skill/reference cần đọc; Workspace origin; metadata đã có; phạm vi đọc/ghi và file được sửa; đầu ra bàn giao; trạng thái phê duyệt và dependency còn chờ. Nhánh triển khai thêm metadata Object/field đã xác minh, project ID/slug/slot, contract route/input/output/error và fixture được sửa. Không đòi kết quả khảo sát hoặc project chưa tạo làm đầu vào của chính bước khảo sát. Chỉ truyền cách truy cập credential an toàn hoặc tên profile.
- Thứ tự: khảo sát → agent chính kiểm tra bằng chứng, chốt phạm vi → gửi đề xuất loại module/dạng frontend (1A), song song thiết kế Excel nếu cần và schema không phụ thuộc lựa chọn (không bắt đầu workbook khi còn thiếu metadata ảnh hưởng schema) → người dùng xác nhận 1A và duyệt workbook → agent chính ghi và đọc lại schema. Có Object mới: tiếp → sub-agent Security hoàn tất 2A → agent chính nghiệm thu → khởi tạo/code. Trong lúc chờ chỉ khảo sát, thiết kế contract, ma trận quyền và kế hoạch test; không dựng source, scaffold, interface code hay test bằng fixture để đi trước.
- Sau 2A (nếu có), chốt contract chung rồi cho các nhánh độc lập chạy song song trong thư mục riêng. Frontend có thể dùng fixture theo contract khi chờ backend nhưng chưa thay test tích hợp thật. Điều phối lịch test ghi khi dùng chung dữ liệu để các agent không reset hoặc sửa fixture của nhau.
- Chỉ giao quyền thao tác Workspace đã được phép; delegation không thay thế duyệt Excel hoặc duyệt Process.
- Nhận lại source, lệnh build/test, coverage riêng từng project, kết quả kiểm thử và dependency còn thiếu; kiểm tra bằng chứng, giao lại lỗi cho sub-agent phụ trách, nghiệm thu tích hợp. Thông báo “xong” không phải bằng chứng PASS.

### 1. Khảo sát và chọn frontend/backend

1. Đọc [$cogover-overview](../cogover-overview/SKILL.md) rồi các reference tính năng của miền nghiệp vụ liên quan. Danh mục App trong overview không phải danh sách App đã cài.
2. Giao sub-agent khảo sát mục 2–3; truyền yêu cầu nghiệp vụ, phạm vi khảo sát và kết quả đọc overview. Sub-agent dùng [$app-menu-manager](../app-menu-manager/SKILL.md) cùng `$cogover-api-auth` liệt kê App thật trên Workspace (`GET /api/v1/apps`, phân trang `page`/`limit` theo contract), đọc detail/menu của App liên quan; ghi ID, slug, standard/custom, trạng thái, phạm vi quyền, chức năng có sẵn. App bị ẩn/thiếu quyền hoặc list chưa đủ trang không chứng minh App chưa cài: phân biệt chưa có, inactive và chưa xác minh được.
3. Cùng sub-agent dùng [$object-info](../object-info/SKILL.md) đọc Objects, fields, options, metadata, related lists liên quan; có automation cũ thì khảo sát Process theo `$process-creator` trước khi đề xuất thêm. Báo cáo: App/Menu và chức năng có sẵn; mapping Object/field/option/quan hệ đã xác minh; Process liên quan; phần thiếu dự kiến; nguồn bằng chứng API/metadata, phạm vi phân trang và điểm chưa xác minh kèm lý do; không chứa credential.
4. Agent chính kiểm tra báo cáo, giao lại phần thiếu hoặc mâu thuẫn trước khi chốt quyết định phụ thuộc vào phần đó. Lập bảng: yêu cầu → khả năng chuẩn và bằng chứng trên Workspace → phần thiếu → nơi xử lý (cấu hình chuẩn/frontend/backend/Process). Chọn loại module theo phần thiếu thực tế: chức năng chuẩn đáp ứng trọn vẹn thì giải thích và dùng skill chuyên trách, không tạo project rỗng cho đủ bước; người dùng yêu cầu rõ trải nghiệm riêng thì vẫn thiết kế phần custom cần thiết. Có frontend: chọn dạng single page app, custom component hoặc Federation Page theo bảng chọn nhanh trong [Các loại Custom Module và dạng frontend](references/get-started-custom-module.md), dựa trên nơi hiển thị, mức tương tác với form, yêu cầu đồng nhất giao diện và stack sẵn có; hỏi phần chưa rõ thay vì suy đoán.
5. Chốt contract nghiệp vụ dự kiến: routes/methods, input/output, caller, dữ liệu thay đổi và tiêu chí nghiệm thu. Custom component: Object, layout, slug item Related List/field sẽ thao tác và expose key dự kiến. Federation Page: App/slug, danh sách route và mục menu sẽ gắn.

### 1A. Xác nhận loại module và dạng frontend với người dùng

Bắt buộc trước khi phát triển, kể cả khi yêu cầu ban đầu đã nói "tạo module" hoặc đã nêu sẵn một dạng.

1. Agent chính gửi đề xuất gồm: loại module (frontend, backend hoặc cả hai); với frontend là dạng single page app, custom component hoặc Federation Page; lý do theo bảng chọn nhanh và bằng chứng khảo sát; dạng thay thế gần nhất và lý do không chọn; tác động của lựa chọn (template bắt buộc hay stack tự chọn, nơi hiển thị, cấu hình cần thêm trên layout hoặc menu, cách kiểm thử, giới hạn); câu hỏi còn mở. Người dùng đã chỉ định dạng: vẫn tóm tắt lựa chọn, nêu khác biệt một lần nếu phân tích cho thấy dạng khác phù hợp hơn, rồi theo quyết định của người dùng.
2. Chờ người dùng xác nhận rõ ràng trong hội thoại. Yêu cầu chung ban đầu, im lặng, đồng ý của sub-agent hoặc việc đã duyệt workbook không thay thế xác nhận này. Người dùng chọn phương án khác thì lập lại kế hoạch theo phương án đó trước khi tiếp tục.
3. Trước khi có xác nhận chỉ làm: khảo sát bổ sung, contract, ma trận quyền, kế hoạch test và thiết kế workbook ở bước 2 mục 1–5 khi schema không phụ thuộc lựa chọn; có thể gửi yêu cầu xác nhận 1A cùng yêu cầu duyệt Excel nhưng mỗi mục phải được trả lời riêng. Không tạo Project, không clone template hoặc scaffold, không ghi schema, không tạo policy/key/Process, không viết code.
4. Sau xác nhận: ghi loại module, dạng frontend, lý do và thời điểm xác nhận vào gói giao việc cho sub-agent và báo cáo bàn giao. Đổi dạng giữa chừng, ví dụ custom component sang Federation Page, phải xin xác nhận lại theo cùng cách kể cả khi đã có code.

### 2. Thiết kế dữ liệu và duyệt Excel

Agent chính xác định có cần bổ sung schema. Nếu cần, giao sub-agent thiết kế dữ liệu/Excel (vai chuyên gia thiết kế cơ sở dữ liệu) làm mục 1–4 với báo cáo khảo sát, mapping metadata, yêu cầu dữ liệu/quyền/truy vấn và phạm vi delta dự kiến; agent chính làm mục 5–7. Schema đã đủ thì ghi kết luận, bỏ qua workbook và tạo Object.

1. Xác định thực thể, nguồn dữ liệu chuẩn, quan hệ một-nhiều/nhiều-nhiều, vòng đời, khóa nghiệp vụ, yêu cầu chống trùng, field bắt buộc, kiểu số/ngày/tiền, quyền và truy vấn chính. Tái sử dụng Object nền tảng và Object nghiệp vụ đã có; không tạo bản sao chỉ vì khác tên hiển thị.
2. Phân loại: tái sử dụng nguyên trạng, bổ sung field/option/quan hệ hoặc tạo Object mới; chỉ thêm phần thiếu, ghi rõ lý do và tác động với dữ liệu/cấu hình đang dùng. Mỗi Object mới có ma trận Create/View/Edit/Delete: người dùng nào được thao tác trực tiếp, phạm vi record/field và action nào chỉ backend được thực hiện. Object do backend quản lý là bảng dữ liệu cho logic ứng dụng, có thể chặn toàn bộ hoặc một phần CRUD trực tiếp; không nhầm với Object nền tảng có sẵn.
3. Schema đã đủ: sub-agent báo lại kết luận và lý do, không tạo workbook rỗng. Cần bổ sung: dùng [$create-cogover-objects](../create-cogover-objects/SKILL.md) tạo workbook `.xlsx` theo hướng dẫn spreadsheet và validator của skill đó, sửa mọi lỗi trước khi bàn giao; phân biệt Object mới với delta trên Object hiện có, chỉ rõ lookup tới Object đã tồn tại để không tạo trùng. Bàn giao file `.xlsx` tại đường dẫn agent chính truy cập được, tóm tắt delta/lý do/tác động, ma trận quyền, mapping lookup, kết quả kiểm tra và các điểm còn cần quyết định; không tạo hoặc sửa schema trên Workspace.
4. Mỗi Object có đúng một record-name slug `name`, type Short text hoặc Auto number; tiền dạng số dùng Decimal. Giữ slug/ID tham chiếu thật, không tạo lại field hệ thống.
5. Agent chính mở workbook, đối chiếu với yêu cầu, metadata đã khảo sát và bằng chứng kiểm tra; giao lại sub-agent thiết kế sửa nếu thiếu hoặc sai. **Bắt buộc đưa file Excel đã rà soát cùng tóm tắt delta và ma trận quyền để người dùng duyệt trước khi ghi schema**; yêu cầu chung “tạo module” không thay thế duyệt này. Trong lúc chờ chỉ hoàn thiện thiết kế và kế hoạch test, chưa tạo Object/field hoặc viết code.
6. Sau khi workbook được duyệt: dùng `$object-info` đọc lại state mới nhất, tạo Object/field theo dependency và đúng bản đã duyệt; quan hệ vòng thì tạo Object trước rồi thêm lookup sau khi có ID. Delta thay đổi do Workspace đã đổi thì chỉ xin duyệt lại phần thay đổi thực chất.
7. Đọc lại toàn bộ schema đã ghi, so với workbook; ghi mapping ID/slug/options dùng cho code và Process. Thao tác dở dang: liệt kê phần đã tạo, tra lại trước retry, không tự xóa để làm lại.

### 2A. Tạo security rules cho từng Object mới trước khi code

Bắt buộc khi bước 2 tạo Object mới; giao một sub-agent Security riêng. Chỉ tái sử dụng Object hoặc bổ sung field thì không tự tạo lại bộ rules hay đổi quyền ngoài phạm vi yêu cầu; đánh giá quyền hiện có và xử lý delta được yêu cầu bằng `$user-permission`.

1. Agent chính giao mapping Object/field đã đọc lại, ma trận quyền đã chốt, phạm vi thao tác được phép và cách truy cập credential an toàn. Sub-agent đọc bản hiện tại của `$user-permission` (mục “Object do backend quản lý và rule giữ chỗ”), [Rule giữ chỗ không chọn nhân sự](../user-permission/references/api-object-security-rules.md#rule-giữ-chỗ-không-chọn-nhân-sự) và `$cogover-api-auth`; đọc rules/Role liên quan trước khi ghi để tránh trùng khi retry và phát hiện quyền đã được cấp. Không tự mở rộng Role để làm test thành công.
2. Mỗi Object mới có bộ mặc định **bốn rules riêng: một Create, một View, một Edit, một Delete**, kể cả action không cho người dùng thực hiện trực tiếp; không gộp action, chỉ bổ sung rule cùng action khi audience, điều kiện record hoặc field scope khác nhau. Create dùng `type: 1` với duy nhất scope `create`; ba action còn lại dùng `type: 2`, chỉ cấp scope của action chính, các scope khác `none`/`no`. Action chỉ backend được thực hiện: rule giữ chỗ active (`status: 1`) với đúng `personnelFilters: [{"type": 1, "op": "include", "personnelId": null}]` và scope hợp lệ của action. Audience này không khớp nhân sự nào: rule giữ slot action và duy trì mặc định từ chối nhưng không ghi đè quyền do active rule khác cấp, nên phải rà mọi active rule để chắc không rule nào cấp lại action đang muốn chặn. Không bỏ rule, thay `null` bằng ID giả hoặc tắt rule giữ chỗ để biểu diễn chặn.
3. Sub-agent tạo rules trong phạm vi được phép; đọc lại danh sách không lọc trạng thái và detail của từng rule. Bàn giao mapping Object ID/slug → rule ID/action/type/status/audience/filter/scopes, đối chiếu ma trận quyền, kết quả kiểm thử trực tiếp theo `$user-permission` và phần chưa kiểm thử. Request dở dang: đọc lại trước retry, không tạo bốn rule mới chồng lên bộ đã có.
4. **Agent chính chờ sub-agent hoàn tất và nghiệm thu trước khi chuyển sang bước 7–8:** mọi Object mới đủ bốn slot action active, rule giữ chỗ có `personnelId` là JSON `null`, phạm vi quyền khớp thiết kế, không có grant ngoài ý muốn từ rule khác và có bằng chứng đọc lại. Thiếu rule, cấu hình sai, thao tác lỗi hoặc sub-agent chưa hoàn tất thì chưa được code; không có công cụ sub-agent thì báo rõ dependency và dừng trước bước code. Kiểm tra cấu hình không thay thế kiểm thử runtime: thiếu credential/fixture thì ghi rõ giới hạn và theo dõi ca test còn thiếu. Ca backend dùng quyền hệ thống chạy sau khi backend sẵn sàng ở bước 8–9; không yêu cầu backend tồn tại để hoàn tất bước cấu hình này.

### 3. Bổ sung Process khi thực sự cần

- Cần chạy theo sự kiện record hoặc theo lịch độc lập với người mở trang/gọi API: giao sub-agent Process riêng dùng [$process-creator](../process-creator/SKILL.md) xác định event, conditions, timezone/lịch, chống lặp, output cần kiểm chứng và thiết kế Triggered Flow hoặc Scheduled Flow phù hợp. Custom Module xử lý trọn vẹn yêu cầu trong request hiện tại thì bỏ qua Process.
- Không mặc định backend tự đăng ký trigger/cron; không dùng timer trình duyệt hoặc tiến trình local thay cho lịch chạy trên Workspace.
- Sub-agent gửi flow cụ thể để agent chính tổng hợp bước xác nhận của `$process-creator`, tái sử dụng xác nhận đã có cho đúng flow. Đủ phê duyệt thì sub-agent tạo, đọc lại, kích hoạt và kiểm thử theo skill đó, trả Process ID/link, instance và bằng chứng hiệu ứng nghiệp vụ.
- Process phải gọi backend chưa publish: thiết kế ở bước này, hoàn tất cấu hình phụ thuộc và kích hoạt sau bước 9. Không kích hoạt flow có URL/ID giả hoặc dependency chưa sẵn sàng.
- Chỉ nối Process → backend khi contract hỗ trợ cách gọi và danh tính cần thiết: Project key không dùng để gọi production; session export ngắn hạn không phải credential bền vững để nhúng vào lịch Process. Chưa có cơ chế được hỗ trợ thì báo chính xác dependency còn thiếu và hoàn thành các phần độc lập.

### 4. Tạo Project trên Workspace

1. Đọc API reference đúng nhánh. Qua phiên Workspace với service `4`, list đủ các trang cần thiết để kiểm tra trùng slug, rồi create hoặc tái sử dụng đúng project đã được chỉ định. CLI publish/activate không tạo Project.
2. Backend: `POST /api/v1/ts-projects`. Frontend: `POST /api/v1/ts-projects/frontend`. Body gồm `name`, `slug`, `description` khi cần. Slug bất biến theo `[A-Za-z_][A-Za-z0-9_]{0,99}`, không áp regex slug Process; ID do server cấp.
3. Đọc lại project vừa tạo. Ghi backend `projectId`/`slug`; frontend `projectId`/`slug`/**`slugSlot`**. Full-stack có hai project với cấu hình riêng. Ba dạng frontend dùng cùng loại Project và cùng `slugSlot`: single page app mở `/{slugSlot}/index.html`, custom component dùng `{slugSlot}/Components/<Tên>` trên layout, Federation Page dùng đoạn `c{N}` với `N` lấy từ `_cm_{N}`. Một project theo template có thể chứa đồng thời custom component và Federation Page; single page app là project riêng.

### 5. Cấu hình Project policy nếu cần

- Frontend thuần: bỏ qua, frontend không có identity-policy endpoint trong contract này. Backend dùng quyền caller mặc định và không gọi `data.asSystem()`/`data.asUser()`: không tạo policy vô cớ. Các API đặc biệt khác kiểm tra theo SDK contract; identity policy không mở được mọi capability.
- Action bị chặn trực tiếp trên Object do backend quản lý (bước 2A): backend dùng `data.asSystem()` với policy giới hạn đúng caller/Object/operation cần thiết. Code backend dùng quyền caller không tự vượt security rules; trước khi dùng quyền hệ thống phải kiểm tra người gọi có quyền thực hiện nghiệp vụ, policy không thay thế kiểm tra này.
- Dùng quyền ủy quyền: đọc mục Identity policy trong Backend API Reference. Thiết kế schema version `2`, giới hạn caller personnel, Object và operation cần thiết; `data.asUser` giới hạn thêm personnel đích. Resolve ID/slug thật; khi sửa giữ grant ngoài phạm vi.
- Lưu editable policy → đọc lại → activate policy cho nhu cầu phát triển. Editable policy khác snapshot bất biến đã duyệt cho từng version; mỗi lần sửa đưa editable policy về `DRAFT`.
- Sau publish có version `READY`: approve policy cho **đúng version** rồi đọc snapshot, kiểm tra revision/hash/grants theo reference. Activate version không tự duyệt policy; policy đã approve trước đây không mặc nhiên áp dụng cho version mới.
- Policy không cấp quyền chạy module nói chung và không thay thế quyền của user đích; permission ceiling của Project key chỉ thu hẹp quyền. Không thêm grant rộng để che lỗi `403`.

### 6. Tạo Project key nếu backend local cần kết nối Workspace

1. Frontend bỏ qua. Backend xử lý thuần túy có thể test bằng fixture không cần key; backend local cần gọi SDK capability thật thì cần key.
2. Đọc mục Project key; resolve caller personnel, hạn dùng và `permissionCeiling` schema version `1` theo hành vi test. Cho phép writes/asSystem/asUser chỉ khi cần trong phạm vi bài toán.
3. Tạo key bằng `POST /api/v1/ts-projects/{projectId}/keys`, hoặc tái sử dụng key còn hiệu lực đúng project/caller và quyền. Không rotate key đang được người khác dùng chỉ để lấy lại secret.
4. `projectKey` chỉ trả một lần lúc create/rotate: chuyển trực tiếp vào credential store hoặc prompt ẩn của CLI qua kênh an toàn, không in raw response; lưu metadata key ID/caller/hạn dùng để kiểm chứng, không lưu secret vào tài liệu.
5. `cogover-dev login --profile <PROFILE>` rồi `doctor` theo reference CLI. Không dùng Workspace API key thay Project key, hoặc ngược lại.

### 7. Khởi tạo local để build/test

- Có Object mới: chỉ giao khởi tạo sau khi agent chính đã nghiệm thu 2A và cung cấp mapping rules/quyền cho sub-agent backend/frontend.
- Backend (sub-agent backend, tiếp tục code/test ở bước 8): theo Backend quick start với starter public được liên kết; `cogover.json` có Workspace origin, Project ID/slug thật và `projectType: "backend"`. `src/main.ts` là entrypoint default export; `local/` chỉ là local runner, không import từ `src/` và không upload.
- Frontend single page app (sub-agent frontend, tiếp tục code/test ở bước 8): theo Frontend quick start với Vite TypeScript hoặc stack phù hợp yêu cầu; `base: "./"`, build ra `dist/index.html`, hash routing nếu có SPA. `cogover.json` phải có `projectType: "frontend"` (bỏ qua sẽ mặc định backend).
- Frontend custom component hoặc Federation Page (sub-agent frontend, tiếp tục code/test ở bước 8): **trước khi code, clone `https://github.com/cogover/custom-frontend-module-template` vào thư mục riêng của project, chạy `npm ci`, đọc `README.vi.md` và toàn bộ `.agents/skills/*/SKILL.md` trong bản đã clone** (`custom-module-foundation` bắt buộc; `custom-module-form-builder` cùng `src/types/form-builder.d.ts` cho custom component; `custom-module-api` khi gọi API; `custom-module-i18n` khi có đa ngôn ngữ) và báo lại agent chính các quy tắc ảnh hưởng contract. Không tự dựng project React khác, không sao chép rời rạc vài file của template. Giữ nguyên `'./CustomApp': './src/App.tsx'` trong `exposes`, `base: './'`, route tương đối trong `src/routes.tsx`, `Link` nội bộ, asset trong `src/assets`; không hardcode `_cm_N`; không đưa key/secret vào biến `VITE_*`. `.env.local` chỉ chứa `VITE_WORKSPACE_NAME` (và `VITE_ENVIRONMENT` khi suffix domain khác mặc định của `vite.config.ts`), không commit. `cogover.json` đặt tại root template với `projectType: "frontend"`. Template chưa có unit-test runner: bổ sung runner phù hợp (ví dụ Vitest cùng Testing Library) đạt điều kiện coverage của bước 8; `npm run lint` và `npm run build` (typecheck và Vite build) phải pass.
- Mỗi sub-agent cấu hình unit-test runner và coverage phù hợp stack ngay khi khởi tạo: lệnh tái chạy được (ví dụ `npm run test:unit:coverage`), ngưỡng **line coverage >= 70% cho riêng project đó**, exit code khác 0 khi có unit test thất bại hoặc coverage dưới ngưỡng.
- Kiểm tra Node.js >= 20, CLI version/help và dependency thực tế; `auth session` cần CLI >= 0.9.0. Dùng Workspace origin đã xác định, không để CLI rơi về runtime mặc định.
- Full-stack: hai thư mục/cấu hình độc lập; proxy frontend local tới backend loopback theo [Full-stack integration](references/full-stack-integration.md).

### 8. Code và test local

Sub-agent backend và frontend làm phần của mình, viết unit tests cùng lúc code và tự sửa lỗi tới khi đạt điều kiện bên dưới; agent chính phối hợp kiểm thử xuyên hai project.

1. Code theo contract nghiệp vụ và schema đã xác minh. Backend:
   - Dùng public `@cogover/sdk`, chỉ import package được hỗ trợ và local source; không đưa Node built-in, local runner, dynamic import hoặc `require()` vào code publish. Đọc [SDK usage guide](references/cogover-sdk-usage-guide.md) rồi [SDK API reference](references/cogover-sdk-api-reference.md) cho router, data, identity và API tích hợp thực sự sử dụng; TypeScript config theo mục khuyến nghị trong usage guide.
   - Sinh `workspace.d.ts` từ metadata Workspace theo mục Khai báo Workspace; sinh lại sau mỗi thay đổi schema. SDK Schema API chỉ đọc; tạo/sửa schema vẫn qua `$object-info`.
   - HTTP ngoài: ưu tiên import `fetch` từ SDK để local không âm thầm dùng native fetch. Project state không dùng lưu secret. Cần checkpoint hoặc concurrency thì đọc mục state/locks; lock không tạo transaction hay exactly-once.
   - Dùng caller identity mặc định, kiểm tra input, chỉ đọc field cần thiết, xử lý kết quả thiếu/null, phân trang và lỗi từng phần. Không tin `personnelId` do client gửi để tự nâng quyền. Thông báo API trả client dùng tiếng Anh.
2. Test logic, input không hợp lệ, thiếu record, quyền được phép/bị từ chối và ghi lặp khi liên quan. Decimal, preview/apply hoặc ghi hàng loạt: đọc [Batch writes và checkpoint](references/batch-writes-and-checkpoints.md), kiểm tra làm tròn, request đồng thời, preview cũ và lỗi từng phần. Chạy typecheck/build và các test phù hợp dự án.
3. Backend có dữ liệu thật chạy qua `COGOVER_LOCAL_PORT=<PORT> cogover-dev run --profile <PROFILE> --allow-writes=false -- npm run dev` cho test đọc; test ghi trong phạm vi yêu cầu dùng `--allow-writes=true` với fixture có marker/ID theo dõi. CLI mặc định cho phép writes; chạy local không đồng nghĩa mock hay dry-run.
4. Frontend test trên browser: loading, empty, error, thao tác chính, khả năng dùng bàn phím và kích thước màn hình liên quan. Full-stack phải test xuyên frontend → backend → dữ liệu. Custom component: chạy `npm run build-watch` và `npm run preview`, dán URL `http://localhost:5101/#./Components/<Tên>` do preview in ra vào item Federation component của layout test, kiểm tra trên form thật các ca thiếu `formBuilder`, cập nhật field/ô Related List, lỗi giữa chừng và không tự chạy lặp; slug item lấy từ layout qua `$object-layout`, không dùng slug Object. Federation Page: `npm run dev` với `.env.local` trỏ Workspace test, người dùng tự đăng nhập Cogover trên trình duyệt (agent không nhập credential), kiểm tra từng route, `Link` nội bộ và API qua HTTP client của template. URL localhost trên layout chỉ dùng khi debug và phải thay bằng đường dẫn đã deploy ở bước 9.
5. Ghi có thể đã thành công trước khi lỗi: đọc lại state trước retry; nhiều lệnh ghi không mặc nhiên là transaction. Lưu kết quả test và fixture đã chạm tới, không lưu credential.

Điều kiện bắt buộc cho từng project trước khi kết thúc bước 8:

- Toàn bộ unit tests PASS, số thất bại bằng 0, có test thực sự được chạy; không dùng suite rỗng hoặc skip/todo thay các ca cần kiểm chứng. Typecheck/build và các test tích hợp/browser thuộc phạm vi cũng phải thành công.
- **Line coverage >= 70% riêng backend và >= 70% riêng frontend.** Không lấy trung bình hoặc gộp coverage hai project; không dùng branch/function/statement coverage thay line coverage; không cộng E2E/integration coverage vào kết quả unit tests.
- Đo coverage từ unit-test suite trên toàn bộ source ứng dụng của project, kể cả file chưa được test import. Chỉ loại trừ dependency, test/fixture, build output, code sinh tự động, declaration và cấu hình/local runner không thuộc code ứng dụng; ghi rõ cấu hình include/exclude. Không loại code nghiệp vụ, entrypoint hay UI cần chạy để đạt ngưỡng. Backend test logic/validation/error/side effect bằng dependency được kiểm soát; frontend test logic và component/hành vi UI phù hợp stack.
- Lưu cho mỗi project: lệnh test, số test pass/fail, số dòng covered/total, phần trăm lines và đường dẫn báo cáo coverage, khớp source cuối sẽ publish. Sau khi sửa code, chạy lại unit tests với coverage của project bị ảnh hưởng.
- Agent chính kiểm tra báo cáo và ngưỡng, yêu cầu sub-agent sửa nếu chưa đạt. Coverage chưa đo hoặc thiếu báo cáo là chưa đạt, không tự coi là 70%; không chuyển project chưa đạt sang publish.

### 9. Publish, activate và test trên Workspace thật

1. Ghi nhận active version hiện tại của từng project và các thay đổi schema liên quan. Kiểm tra archive không có secret, `.env`, session file, source map hoặc dependency/local runner ngoài phạm vi.
2. `cogover-dev publish` tại đúng thư mục project: backend ZIP chứa `src/main.ts`; frontend phải build trước, ZIP chứa `dist/index.html` (giữ thư mục `dist/`), CLI không build frontend. Publish qua API trực tiếp: upload ZIP private, dùng file metadata thật cùng `idempotencyKey` theo reference; không đoán upload endpoint.
3. Chờ version `READY` hoặc `FAILED` có thời hạn; HTTP `202` chưa phải hoàn tất. Timeout: đọc version đã tạo trước khi publish lại. `FAILED`: sửa nguyên nhân rồi tạo version mới. Ghi version ID và build error an toàn nếu có.
4. Backend có policy: approve/read snapshot đúng version theo bước 5. Preview service `6` phải chỉ rõ version ID và `READ_ONLY`/`READ_WRITE`; preview mặc định `READ_WRITE`, ghi thật và không rollback theo nhóm.
5. Activate đúng version bằng CLI, đọc lại project xác nhận `ACTIVE` và `activeVersionId`. Full-stack: backend sẵn sàng trước frontend phụ thuộc nó; hoàn tất Process còn chờ dependency.
6. Backend: gọi production service `3` bằng session do CLI tạo theo [mẫu cURL](references/cli-session-and-delivery.md); kiểm tra HTTP/body và đọc lại dữ liệu nghiệp vụ. Preview hoặc `READY` không phải bằng chứng production PASS. Route dùng query string: test filter có kết quả/không có kết quả và cursor trên production; local khác Workspace thì áp dụng mục tương thích trong [Full-stack integration](references/full-stack-integration.md).
7. Frontend theo dạng đã xác nhận, trong browser đã đăng nhập Workspace (CLI publish không đăng nhập browser; link frontend yêu cầu session Workspace, không phải trang công khai vô danh):
   - Single page app: mở `https://{WORKSPACE_DOMAIN}/{slugSlot}/index.html`, xác minh asset/load/refresh và luồng nghiệp vụ với API thật.
   - Custom component: thêm hoặc cập nhật item **Federation component** trên layout đích với đường dẫn `{slugSlot}/Components/<Tên>` khớp chữ hoa/thường với khóa expose; đặt qua `$object-layout` (mục "Đưa Federation component vào layout": component `fieldType: "federation_component"`, trường `federationUrl`) hoặc trình sửa layout, rồi view lại layout để xác minh. Mở form thật, chạy lại các ca ở bước 8, lưu và đọc lại record bằng `$object-record`; thay mọi URL localhost còn sót.
   - Federation Page: mở `https://{WORKSPACE_DOMAIN}/{APP_SLUG}/c{N}/{PATH}` với `N` từ `slugSlot` và App do người dùng chỉ định, đã xác minh qua `$app-menu-manager`; kiểm tra từng route, refresh, deep-link và quyền. Gắn vào menu ứng dụng bằng mục menu điều hướng tới trang trong Workspace với đường dẫn `/{APP_SLUG}/c{N}/{PATH}`; dùng API `$app-menu-manager` chỉ khi contract của skill đó mô tả loại hành động này, nếu không thì cấu hình trên giao diện rồi đọc lại menu.
   - Custom component và Federation Page: sau activate version mới, tải lại cứng, xác nhận không còn lỗi không tìm thấy remote module và asset tải từ `/{slugSlot}/assets/`.
8. Xác minh quyền bằng caller phù hợp: session từ Workspace API key không bảo đảm cùng user với Project key và không giả lập được user tùy ý; chưa test user thường thì báo đúng giới hạn. Object do backend quản lý: phối hợp sub-agent Security kiểm chứng action trực tiếp bị từ chối, action được phép (ví dụ View) vẫn đúng phạm vi, đường backend hợp lệ thực hiện được thao tác hệ thống; kiểm thử cả caller không được phép gọi nghiệp vụ. Thành công dưới `data.asSystem()` không chứng minh caller có quyền CRUD trực tiếp. Hoàn tất các ca runtime còn thiếu từ bước 2A trước khi tuyên bố quyền đã được kiểm thử end-to-end.
9. Process: kiểm chứng instance và hiệu ứng nghiệp vụ theo `$process-creator`, phục hồi lịch và quyền test tạm. Module lỗi sau activate: ưu tiên activate lại version cũ còn hợp lệ trong phạm vi phục hồi và đọc lại xác nhận; rollback version không hoàn tác schema/record writes hay side effect.
10. Phục hồi cấu hình test tạm, xóa file session export do tác vụ tạo khi dùng xong; fixture Workspace xử lý theo skill dữ liệu và phạm vi đã được phép; báo rõ phần còn lại. Không tự xóa Project, schema hoặc Process để “cleanup”.

### 10. Bàn giao

- **Frontend:** project/version đang active, `slugSlot`, dạng đã xác nhận ở 1A, thư mục source và kết quả browser test. Single page app kèm link `/{slugSlot}/index.html`. Custom component kèm danh sách expose key, Object/layout đã gắn item Federation component và đường dẫn `{slugSlot}/Components/<Tên>`. Federation Page kèm URL từng route theo App, mục menu đã gắn và quyền hiển thị.
- **Backend:** lệnh `cogover-dev auth session --format curl --output ...` và **cURL hoàn chỉnh** tới production theo reference bàn giao, điền domain, slug, method, route, payload đã kiểm thử; không đưa cookie/token thật vào câu trả lời. Kèm response mong đợi và cách tạo lại session khi hết hạn.
- **Cả hai:** hai mục trên cùng mapping frontend → backend, thư mục source và lệnh build/test/publish để bảo trì.
- **Kiểm thử:** báo cáo unit tests và line coverage của từng project theo bước 8, không gộp hai project thành một chỉ số; nêu rõ sub-agent phụ trách backend/frontend/Process đã thực hiện phần nào.
- **Security:** ma trận quyền, mapping bốn slot rule của từng Object mới và rules bổ sung nếu có, action chỉ backend được thực hiện, bằng chứng đọc lại/nghiệm thu của sub-agent Security, kết quả runtime cùng giới hạn còn lại. Phân biệt cấu hình đã xác minh với quyền đã kiểm thử end-to-end.
- Kèm phần schema đã tạo/tái sử dụng, workbook đã duyệt nếu có, Process/link/instance nếu có, policy/key ở mức metadata và bằng chứng kiểm thử. Báo `PASS`, `PARTIAL`, `FAIL` hoặc `BLOCKED` theo kết quả quan sát; liệt kê thiếu quyền/dependency/fixture còn lại. Chỉ gọi hoàn tất khi local và Workspace test đáp ứng tiêu chí của bài toán.
