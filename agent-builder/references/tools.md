# Danh mục và cấu hình Tool

Đọc [API cấu hình](config-api.md) trước khi gửi request. Tool tạo/cập nhật qua thao tác 40/41, List qua 43; `config` luôn là chuỗi JSON. List hỗ trợ `ids`, `keyword`, `types`, `categories`, `requiresApproval`, `status`, phân trang và sắp xếp.

## Chọn category và type

Các lựa chọn dưới đây tương ứng form tạo Tool. Không coi mọi tên công cụ có thể xuất hiện trong chat là một loại Tool cho phép tự tạo; các công cụ như `activate_skill` do Agent cung cấp khi có Skill mở rộng.

| `category` | `type` | Chức năng và cấu hình |
|---|---|---|
| `RECORD` | `CREATE`, `GET`, `UPDATE`, `DELETE`, `LIST` | Thao tác bản ghi của các Object đã chọn. Có `app`, `object_slug` hoặc `object_slugs` |
| `ACTIVITY` | `CREATE`, `GET`, `UPDATE`, `DELETE`, `LIST` | Thao tác công việc/hoạt động. `app` cung cấp ngữ cảnh App khi tạo/cập nhật; không coi đó là bộ lọc bảo mật cho mọi lệnh đọc |
| `PROCESS` | Xem bảng dưới | Tìm Process, bắt đầu và quản lý lượt chạy, xem/hoàn thành User Task; cấu hình cơ bản `{}` |
| `HTTP` | `HTTP_REQUEST` | Gọi API HTTPS với URL, method và xác thực đã cấu hình |
| `WEB_SEARCH` | `PERPLEXITY`, `GEMINI` | Tìm thông tin trên web; `systemInstruction` hướng dẫn phạm vi tìm kiếm và cách tổng hợp |
| `KNOWLEDGE_BASE` | `QDRANT` | Tra cứu tài liệu đã index trong Data của Workspace; cấu hình danh mục và ngưỡng truy xuất |
| `DEEP_RESEARCH` | `DEEP_RESEARCH` | Nghiên cứu/tổng hợp sâu dựa trên công cụ kiến thức; cần Tool KNOWLEDGE_BASE khả dụng cùng lúc |

`RECORD`, `ACTIVITY`, `PROCESS` nhận `type` là mảng để chọn nhiều thao tác; các category còn lại dùng một chuỗi. Khi tái sử dụng Tool, giữ nguyên định dạng hợp lệ được trả về. Không trộn type của các category trong một Tool.

| Type PROCESS | Ý nghĩa |
|---|---|
| `SEARCH` | Tìm Process phù hợp |
| `START_INSTANCE` | Bắt đầu luồng Manual có thể chạy bởi người dùng |
| `LIST_INSTANCES`, `VIEW_INSTANCE` | Liệt kê/xem lượt chạy |
| `PAUSE_INSTANCE`, `RESUME_INSTANCE` | Tạm dừng/tiếp tục lượt chạy |
| `CANCEL_INSTANCE`, `DELETE_INSTANCE` | Hủy/xóa lượt chạy, khác nhau về tác động dữ liệu |
| `MY_PENDING_TASKS`, `MY_COMPLETED_TASKS` | Công việc đang chờ/đã hoàn thành của nhân sự thực thi |
| `VIEW_USER_TASK`, `SUBMIT_USER_TASK` | Xem và gửi kết quả User Task |

Các lệnh này không tạo/sửa định nghĩa Process. Khi cần thiết kế quy trình, dùng [$process-creator](../../process-creator/SKILL.md).

Nếu Workspace trả Tool có category/type khác bảng, chỉ tái sử dụng sau khi xác minh mô tả, schema đầu vào và hoạt động qua metadata API/tài liệu API tương ứng. Nếu chưa đủ contract, báo người dùng cung cấp trước khi tạo hoặc sử dụng; không tự tạo payload hoặc mở UI để dò.

## RECORD và ACTIVITY

Một Object:

```json
{"app":"{app-slug}","object_slug":"{object-slug}"}
```

Nhiều Object:

```json
{"app":"{app-slug}","object_slugs":["{object-slug-a}","{object-slug-b}"]}
```

- Resolve App/Object bằng metadata và các skill tương ứng trước khi ghi.
- Ưu tiên chọn Object tường minh. Khi có `object_slugs`, trường này được ưu tiên kể cả mảng rỗng. Mảng rỗng không có nghĩa “tất cả”.
- Nếu chỉ đặt `app`, phạm vi có thể dựa vào Object truy cập được qua App; nó không thay thế quyền record/field. Không dùng config rỗng để mong cấp toàn Workspace.
- Công cụ RECORD có thể được gộp theo thao tác khi chạy. `slug` cấu hình không nhất thiết là tên công cụ hiển thị trong chat; kiểm tra tool thực tế và phạm vi Object, không chỉ so tên.
- ACTIVITY dùng `{"app":"{app-slug}"}`. Không thay thế thao tác Activity chuyên biệt bằng RECORD nếu nghiệp vụ cần hành vi Activity.

Ví dụ Tool chỉ đọc, thao tác 40:

```json
{
  "name":"Tra cứu phiếu hỗ trợ",
  "slug":"support_ticket_read",
  "description":"Tìm và xem phiếu hỗ trợ trong phạm vi quyền của nhân sự thực thi; không sửa hoặc xóa phiếu.",
  "category":"RECORD",
  "type":["LIST","GET"],
  "config":"{\"app\":\"{app-slug}\",\"object_slug\":\"{ticket-object-slug}\"}",
  "requiresApproval":false,
  "status":true,
  "accessControls":[{"functions":["VIEW","EXECUTE"],"type":"role","option":2,"items":["{operator-role-id}"]}]
}
```

Tạo Tool ghi riêng nếu cần xác nhận. Tránh nhiều Tool cùng loại ACTIVITY/PROCESS với cấu hình hoặc yêu cầu duyệt mâu thuẫn trong cùng Agent; không giả định chúng chạy thành các bản độc lập. Với RECORD cũng kiểm tra lại hành vi khi nhiều Skill cấp cùng thao tác.

## HTTP

Config dưới đây là JSON **trước khi serialize** vào chuỗi `config`:

```json
{"url":"https://api.example.com/catalog","method":"GET","auth":{"type":"none"}}
```

Form hỗ trợ các cơ chế xác thực:

| `auth.type` | Trường bổ sung |
|---|---|
| `none` | Không có |
| `bearer_token` | `value` |
| `api_key_header` | `header_name`, `value` |
| `query_param` | `param_name`, `value` |
| `basic` | `username`, `password` |
| `oauth2_client_credentials` | `token_url`, `client_id`, `client_secret` |

Điền secret bằng kênh credential được phép; không đưa vào mô tả, Skill, prompt hay file public. Nếu sửa Tool dùng chung, không thay toàn bộ `config` bằng một mẫu làm mất cấu hình/credential hiện hữu. Kiểm tra URL, method và API đích trước khi gọi, không cho phép người chat tự đổi đích gửi credential.

**Giới hạn cần biết:** contract tạo/cập nhật Tool hiện nêu trong tài liệu này không có trường khai báo parameter schema. Chỉ có `description` hoặc nhét `parameters` tùy ý vào payload không bảo đảm Agent có schema đầu vào. Với HTTP cần tham số động, ưu tiên Tool đã có schema đúng; nếu cần tạo schema mới, báo người dùng cung cấp [contract schema HTTP Tool](api-gaps.md). Không chuyển sang trình duyệt hoặc tự thêm trường không được tài liệu hỗ trợ. Không tuyên bố tích hợp có tham số đã hoàn tất khi mới lưu URL/auth. HTTP không tham số vẫn phải test request và phản hồi thực tế.

## Web search và kiến thức

WEB_SEARCH config:

```json
{"systemInstruction":"Tìm nguồn chính thức liên quan câu hỏi; phân biệt thông tin đã xác minh với suy luận và trả đường dẫn nguồn."}
```

KNOWLEDGE_BASE config gợi ý theo form:

```json
{
  "allowedCategories":["{data-library-slug}"],
  "rerankEnabled":true,
  "rerankCandidateTopK":40,
  "rerankFinalTopK":5,
  "rerankScoreThreshold":0.2,
  "noRerankMinScore":0.5,
  "topK":5
}
```

`allowedCategories` dùng **slug danh mục**, không dùng ID danh mục/file. Rỗng hoặc thiếu trường này nghĩa là không giới hạn category; một phần tử áp dụng trực tiếp, nhiều phần tử cho phép chọn trong tập đó. Chọn tường minh cho Agent CSKH. Không cấu hình tên kho lưu trữ để đổi Workspace; dữ liệu tra cứu thuộc Workspace của phiên.

Rerank sắp xếp lại ứng viên; `rerankCandidateTopK` là lượng ứng viên, `rerankFinalTopK` là số kết quả giữ lại. Ngưỡng cao hơn có thể giảm kết quả không liên quan nhưng cũng bỏ sót tài liệu. Test với câu hỏi biết trước đáp án trước khi chỉnh ngưỡng. Các giá trị trên là điểm khởi đầu, không phải bằng chứng truy xuất đạt chất lượng.

DEEP_RESEARCH dùng config cơ bản `{}`. Gắn cùng KNOWLEDGE_BASE vào Skill CORE khi cần sử dụng ổn định ngay từ đầu; kiểm tra Tool khả dụng trước khi test. Chỉ bật khi cần nghiên cứu sâu và chấp nhận thời gian xử lý dài hơn. Nhu cầu tra cứu tài liệu thông thường dùng KNOWLEDGE_BASE. Tránh nhiều Tool KNOWLEDGE_BASE cùng type nhưng phạm vi khác nhau trong cùng Agent; dùng một cấu hình danh mục rõ ràng, kiểm thử lại sau khi thêm Skill.
