---
name: agent-builder
description: "Tạo, cấu hình và kiểm thử Cogover AI Agent: model/reasoning, danh tính thực thi, System Prompt, Skill CORE/EXTENDED, Tool, phân quyền và Data/RAG qua Web App API; kích hoạt và kiểm tra câu trả lời bằng chat/WebSocket. Phối hợp $cogover-api-auth."
metadata:
  author: cogover
  version: "1.1.1"
---

# Agent Builder

- **Phiên bản:** `1.1.1`
- **Ngày phát hành:** `2026-09-13`

## Phạm vi

Xây Agent trong ứng dụng AI Agent của Cogover, từ yêu cầu nghiệp vụ đến hội thoại kiểm thử. “Skill” trong tài liệu này là tài nguyên kỹ năng gắn với Agent trên Workspace, khác với thư mục `SKILL.md` của trợ lý đang cấu hình hệ thống.

## Nguyên tắc dùng API

Thực hiện toàn bộ công việc bằng API: xác thực, tra cứu metadata, tạo/sửa tài nguyên, phân quyền, upload/chuyển đổi/index, kích hoạt, chat, duyệt Tool và đọc lại kết quả nghiệp vụ. Dùng HTTP client và WebSocket client trực tiếp; phiên Web App không có nghĩa là phải mở trình duyệt.

Không dùng trình duyệt, DevTools hoặc thao tác UI làm workflow mặc định hay phương án dự phòng khi thiếu API. Chỉ dùng trình duyệt khi người dùng yêu cầu rõ thao tác đó; giữ phạm vi tối thiểu. Không đoán endpoint, đọc source riêng/bundle hoặc truy cập dịch vụ ngoài API Workspace để suy ra contract.

Khi thiếu API hoặc schema cần thiết, báo người dùng cung cấp contract: thao tác đang bị chặn, endpoint/method hoặc mã service, request/response, xác thực/quyền và ví dụ đã ẩn danh. Tiếp tục các phần độc lập đã đủ API; chỉ dừng phần phụ thuộc, không báo toàn bộ tác vụ hoàn tất. Phân biệt thiếu tài liệu API với lỗi quyền/phiên hoặc giới hạn của script. Đọc [API cần bổ sung](references/api-gaps.md) khi gặp khoảng trống; không yêu cầu cung cấp lại contract đã có trong skill.

## A. Chuẩn bị

1. Dùng [$cogover-api-auth](../cogover-api-auth/SKILL.md), đọc đầy đủ tài liệu xác thực của skill đó. Các endpoint trong skill này dùng phiên Web App: đổi API Key tại `/bapi/v1/auth-token`, sau đó gửi đủ cookie và CSRF/XSRF. Áp dụng quản lý credential, binding Workspace, xử lý lỗi và đọc lại sau ghi của skill xác thực.
2. Xác định Agent phục vụ nhân sự hay khách hàng; nghiệp vụ, nguồn dữ liệu, thao tác được phép và người sử dụng. Chỉ hỏi phần còn thiếu ảnh hưởng trực tiếp đến model, danh tính hoặc phạm vi quyền.
3. Đọc [API cấu hình](references/config-api.md), lấy danh sách Agent, model, Skill và Tool hiện có. Tái sử dụng tài nguyên phù hợp; đọc chi tiết trước khi sửa tài nguyên dùng chung. Không ghi khi người dùng chỉ yêu cầu khảo sát/thiết kế.

## B. Xây Agent

### 1. Tạo Agent và viết System Prompt

- **Model:** chọn từ danh sách thực tế của Workspace. Ưu tiên khả năng làm theo hướng dẫn và gọi công cụ cho nghiệp vụ nhiều bước; cân nhắc độ trễ và chi phí cho chat CSKH. Nêu ngắn lý do chọn; hỏi nếu các lựa chọn có đánh đổi mà yêu cầu chưa làm rõ. Không cố định tên model hoặc tự cấu hình khóa của nhà cung cấp model.
- **Reasoning:** mặc định bật `defaultReasoningSettings.enabled: true` và `allowUserReasoningOverride: true`. Chọn effort/budget hợp lệ theo metadata model; đây là mặc định của workflow này, không phải khẳng định mọi form có sẵn đều bật. Model không hỗ trợ reasoning thì chọn model phù hợp khác hoặc hỏi người dùng nếu họ đã chỉ định model đó. Không gửi trường mà model không hỗ trợ. Xem [reasoning](references/config-api.md#model-và-reasoning).
- **Danh tính thực thi:** Agent nội bộ dùng “Quyền của nhân sự chat với Agent (Agent nội bộ)”, tương ứng `runAsPersonnelId: null`. Agent CSKH chọn một nhân sự có quyền phù hợp. Khi chưa rõ, có thể đề xuất nhân sự của người yêu cầu dựa trên `personnelId` trả về từ bước tạo phiên, rồi chốt lựa chọn trước khi gán quyền cố định. Không coi API Key là bằng chứng người yêu cầu muốn cho khách hàng dùng toàn bộ quyền của mình.
- **System Prompt:** viết đầy đủ vai trò, mục tiêu, phạm vi dữ liệu, quy trình xử lý theo từng nhóm yêu cầu, thông tin cần hỏi thêm, giới hạn thao tác, quy tắc chuyển cho người phụ trách và hình thức trả lời. Không chỉ dùng một câu “bạn là trợ lý hữu ích”. Với RAG, yêu cầu dẫn nguồn và nói rõ khi tài liệu không đủ; với thao tác ghi, chỉ báo thành công sau kết quả công cụ và kiểm tra lại. Mẫu tại [API cấu hình](references/config-api.md#system-prompt-mẫu).
- **Không viết cơ chế Skill/Tool vào System Prompt:** không nhắc `activate_skill`, `deactivate_skill`, loại CORE/EXTENDED, slug Skill hay tên công cụ hệ thống. Lúc chạy, nền tảng tự chèn hướng dẫn của Skill CORE, danh sách Skill EXTENDED và quy tắc kích hoạt vào ngữ cảnh; hướng dẫn cách gọi công cụ chỉ nằm trong `fullInstructions` của Skill. Lặp lại trong System Prompt tạo hai nguồn hướng dẫn, dễ khiến Agent kích hoạt nhầm Skill CORE đã nạp sẵn và lệch khi nền tảng thay đổi. Mô tả nghiệp vụ thay cho cơ chế: yêu cầu nào cần dữ liệu gì, kết quả ra sao, giới hạn nào.
- Giữ nguyên biến template ở cuối prompt; không thay bằng ngày hay danh tính tại lúc cấu hình:

```text
# Thông tin hệ thống
- Thời gian hiện tại: ${system.currentDateTime}
- Người dùng hiện tại: ${system.currentUserInfo}
```

Đặt tên, slug, mô tả, lời chào/lỗi và ngôn ngữ phù hợp. Có thể tạo Agent trước với danh sách Skill rỗng rồi gắn sau; quyền truy cập ban đầu chỉ dành cho nhóm đang cấu hình và kiểm thử. Đọc lại trạng thái sau tạo; không giả định Agent mới luôn tắt.

### 2. Chọn Skill CORE hoặc EXTENDED

Loại nằm trên liên kết `Agent.skills[]`, không nằm trên bản thân Skill.

| Cách gắn | Ngữ cảnh ban đầu | Khi sử dụng |
|---|---|---|
| `CORE` — Kỹ năng cốt lõi | Tên, mô tả, **hướng dẫn chi tiết và công cụ** được nạp ngay | Dùng trực tiếp; phù hợp nghiệp vụ thường xuyên, hướng dẫn luôn cần |
| `EXTENDED` — Kỹ năng mở rộng | Slug và **mô tả** đã có để Agent nhận diện nhu cầu | Agent gọi `activate_skill` với `skill_slug`, sau đó mới dùng hướng dẫn chi tiết/công cụ; có thể được gỡ khỏi ngữ cảnh khi không còn dùng |

Cả hai cơ chế do nền tảng tự vận hành lúc chạy; System Prompt và `fullInstructions` không lặp lại quy tắc kích hoạt. Không mô tả CORE là chỉ nạp mô tả, hoặc EXTENDED là hoàn toàn không xuất hiện lúc đầu. Cùng một Skill có thể là CORE ở Agent này và EXTENDED ở Agent khác. Mỗi Skill chỉ xuất hiện một lần trong danh sách của một Agent. `maxActiveExtendedSkills` là trường cấu hình giới hạn đồng thời, không phải số Skill được phép gắn; dùng giá trị khởi điểm 5 nếu chưa có yêu cầu khác. Việc lưu trường này chưa chứng minh giới hạn được cưỡng chế lúc chat: kiểm thử nếu nghiệp vụ phụ thuộc vào trần này, không dùng nó làm cơ chế phân quyền hay cam kết hạn mức.

### 3. Phân quyền

Đọc [phân quyền](references/config-api.md#phân-quyền). Cấu hình `accessControls` phù hợp cho Agent, Skill, Tool và danh mục Data nếu dùng: người dùng thường cần `VIEW`/`EXECUTE`; nhóm bảo trì mới cần `EDIT`/`DELETE`. Giữ quyền có sẵn khi bổ sung một nhóm.

Quyền dùng Agent, danh tính thực thi và quyền dữ liệu nghiệp vụ là các phần riêng. Việc gắn Tool không tự cấp quyền Object/record/field hay quyền Process. Khi cần resolve nhân sự/role hoặc thay đổi quyền dữ liệu, dùng [$user-permission](../user-permission/SKILL.md); khi cần metadata Object dùng [$object-info](../object-info/SKILL.md). Kiểm thử bằng đúng nhóm người dùng đích, gồm cả tình huống bị từ chối; không suy ra quyền runtime chỉ từ việc thấy Agent trong danh sách.

### 4. Tạo hoặc cập nhật Skill

- `name`/`slug`: diễn đạt một khả năng nghiệp vụ rõ ràng.
- `description`: mô tả **khi nào dùng**, phạm vi, đầu vào và kết quả; đây là tín hiệu nhận diện Skill, kể cả khi EXTENDED chưa kích hoạt. Tránh mô tả quá rộng khiến Agent kích hoạt sai.
- `fullInstructions`: các bước thực hiện, dữ liệu cần lấy, quy tắc quyết định, công cụ cần dùng, cách xử lý thiếu quyền/thiếu dữ liệu và điều kiện hoàn tất. CORE nạp phần này ngay; EXTENDED nạp khi kích hoạt.
- Tạo/chọn Tool rồi gắn bằng `tools: [{toolId, sortOrder}]`. Nếu tạo Skill trước, cập nhật liên kết khi Tool đã tồn tại. Sau đó cập nhật `Agent.skills` với loại CORE/EXTENDED đã chọn, không dựa vào `agentIds` để suy đoán loại.

Giới hạn form: tên/slug 250 ký tự, mô tả 500, hướng dẫn Skill 2.000. Tách các nghiệp vụ lớn thành Skill phù hợp hoặc đưa tài liệu kiến thức vào Data. Đọc lại nội dung và liên kết sau ghi.

### 5. Tạo Tool

Đọc [danh mục và cấu hình Tool](references/tools.md) trước khi tạo. Chọn đúng cặp `category`/`type`, viết mô tả công cụ theo hành động và kết quả, cấu hình phạm vi Object/App/Data rõ ràng. `config` là **chuỗi JSON**, không phải object JSON lồng trực tiếp.

Tách công cụ đọc khỏi công cụ ghi khi cần chính sách khác nhau. Đặt `requiresApproval` theo nghiệp vụ và ý định đã được người dùng cho phép; kiểm thử luồng chấp thuận/từ chối bằng sự kiện WebSocket và API chat service 12 theo [hướng dẫn test](references/chat-testing.md). Không mở thêm thao tác ghi chỉ để khắc phục lỗi thiếu công cụ. Đọc lại Tool, gắn vào Skill và kiểm tra Agent gọi đúng công cụ thực tế.

### 6. Data/RAG khi cần

Đọc [Data và index tài liệu](references/data-rag.md). Quy trình: tạo/chọn danh mục → upload tài liệu → tạo file `CONTENT` → chuyển đổi/duyệt theo trạng thái → gọi index nếu cần → chờ `INDEXED` → cấu hình Tool `KNOWLEDGE_BASE` với slug danh mục trong `allowedCategories` → gắn Tool vào Skill của Agent.

Upload thành công chưa có nghĩa Agent tra cứu được. Không xem `agentIds` trả về của danh mục là cách thay thế Tool liên kết. File loại `SKILL` trong Data cũng không tự tạo tài nguyên Skill hay liên kết CORE/EXTENDED.

## C. Kích hoạt và kiểm thử

1. Đọc lại Agent, Skill, Tool, quyền, model/reasoning và các liên kết; bật tài nguyên cần dùng. Kích hoạt Agent bằng thao tác đổi trạng thái được tài liệu hỗ trợ.
2. Tạo **hội thoại mới** sau thay đổi cấu hình. Đọc [chat và WebSocket](references/chat-testing.md); kết nối WebSocket trước, tạo chat bằng HTTP, đọc phản hồi/công cụ/yêu cầu duyệt từ sự kiện. Dùng script probe cho kiểm tra kết nối cơ bản; test nghiệp vụ bằng HTTP/WebSocket client theo cùng contract, không chuyển sang trình duyệt khi probe chưa hỗ trợ tình huống.
3. Chạy tình huống chính, thiếu dữ liệu, ngoài phạm vi, CORE/EXTENDED (gồm kiểm tra Agent không gọi `activate_skill` cho Skill CORE), quyền không đủ, reasoning mặc định/override; thêm RAG có đáp án/không có đáp án nếu dùng Data. Test ghi chỉ trên dữ liệu thử thuộc phạm vi người dùng cho phép.
4. Kết luận dựa trên nội dung trả lời và kết quả nghiệp vụ. HTTP `r: 0` hoặc thông báo “ACCEPTED” chỉ xác nhận nhận yêu cầu. Với WebSocket cần đúng hội thoại/lượt, câu trả lời cuối và sự kiện hoàn tất không lỗi.

## Bàn giao

Trả link Agent nếu đã có từ API/người dùng hoặc contract URL được tài liệu hỗ trợ; nếu chưa có, bàn giao ID/slug, không mở trình duyệt chỉ để lấy link. Nêu tài nguyên đã tạo hoặc tái sử dụng, model/reasoning, danh tính thực thi, danh sách CORE/EXTENDED và phạm vi Tool/Data. Tóm tắt test đã chạy, kết quả, phần chưa kiểm chứng và API/schema cần người dùng bổ sung nếu có. Không đưa cookie, khóa, raw HAR hay nội dung ngoài phạm vi bàn giao. Không ghi “PASS end-to-end” nếu mới kiểm tra payload hoặc chưa nhận được câu trả lời.
