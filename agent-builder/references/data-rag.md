# Data Library và index tài liệu

## Danh mục

Dùng [giao thức cấu hình](config-api.md#giao-thức-chung): `POST /api/v1/config-server`, `x-req-type: 6`.

| Thao tác | `x-req-service` | Payload |
|---|---:|---|
| Tạo danh mục | 60 | `name`, `slug`, `description`, `status`; tùy chọn `parentId`, `accessControls`, `files` |
| Cập nhật | 61 | `id` và trường cần sửa |
| Xóa | 62 | `ids` |
| List/chi tiết | 63 | `ids`, `slugs`, `parentId`, `rootOnly`, `keyword`, `status`, `page`, `limit`, `order`, `sort` |
| Đổi trạng thái | 64 | `ids`, `status` |

Danh mục mới, chưa có file:

```json
{
  "name":"Chính sách dịch vụ",
  "slug":"service_policies",
  "description":"Tài liệu chính sách dịch vụ đã được phép dùng để trả lời khách hàng.",
  "parentId":null,
  "status":true,
  "accessControls":[{"functions":["VIEW","EXECUTE"],"type":"role","option":2,"items":["{support-role-id}"]}]
}
```

Tạo/chọn đúng danh mục, đọc lại ID và slug. Khi có cây danh mục, liệt kê rõ các slug cần truy xuất; không mặc định chọn cha sẽ bao gồm toàn bộ con. `agentIds` trong response thể hiện quan hệ sử dụng, không phải trường thay thế liên kết Agent → Skill → Tool.

## Upload và tạo tài liệu

1. Chọn file được người dùng cho phép đưa vào Workspace. Với kiến thức tra cứu, dùng loại `CONTENT`; loại file `SKILL` trong Data không đồng nghĩa tài nguyên Skill có `fullInstructions`.
2. Upload bằng phiên Web App:

```http
POST /api/v1/file/upload/v2/client_upload
Content-Type: multipart/form-data; boundary={boundary-do-http-client-tao}
```

Gửi multipart field **`file`** và cookie/CSRF theo skill xác thực; không gửi `x-req-type: 6` của API cấu hình. Để HTTP client tự tạo boundary. Response có `r`, `msg`, `data` ở root; giữ `data.url` và serialize **nguyên object `data`** làm `fileServerInfo`, không chỉ giữ URL hoặc tự tạo `file_id`.

3. Tạo tài nguyên file bằng thao tác **70**, type 6 tại `/api/v1/config-server`:

```json
{
  "dataLibraryId":"{data-library-id}",
  "type":"CONTENT",
  "name":"Chính sách bảo hành",
  "slug":"warranty_policy",
  "description":"Điều kiện và thủ tục bảo hành theo tài liệu đã phê duyệt.",
  "filePath":"{upload-response.data.url}",
  "fileServerInfo":"{JSON-stringify-upload-response.data}",
  "isAutoConvert":false,
  "isAutoApprove":false
}
```

Các placeholder cuối phải được thay bằng dữ liệu upload thật trong bộ nhớ trước khi gửi. Chỉ bật tự chuyển đổi/tự duyệt khi workflow đã cho phép dùng bản chuyển đổi mà không cần người duyệt. Mặc định minh họa ở trên giữ bước rà soát.

Form tài liệu nhận MD, TXT, CSV, XLSX, XLSM, DOCX, DOC, PDF, JPG/JPEG, PNG, WEBP, GIF, tối đa 10 MiB. Việc nhận file không bảo đảm nội dung được chuyển đổi/index chính xác; đối chiếu nội dung sau xử lý, đặc biệt file ảnh và bảng.

## Trạng thái và thao tác file

| Trạng thái số | Ý nghĩa | Bước tiếp theo |
|---:|---|---|
| -1 | `PENDING_CONVERSION` | Chuyển đổi bằng 74 nếu chưa tự chuyển đổi |
| -2 | `PENDING_APPROVAL` | Đọc nội dung chuyển đổi qua API rồi duyệt bằng 75 khi đã được phép |
| 0 | `NOT_INDEXED` | Bắt đầu index theo mục dưới |
| 1 | `INDEXING` | Chờ và đọc lại; không gửi index lặp |
| 2 | `INDEXED` | Có thể test truy xuất; vẫn cần kiểm tra đáp án |
| 3 | `DELETING_INDEX` | Chờ thao tác đang chạy hoàn tất |

Các thao tác file trên `/api/v1/config-server`, type 6:

- **71** cập nhật: `id` và trường cần sửa; không giả định có thể đổi `dataLibraryId` bằng API cập nhật file.
- **73** List/chi tiết: `{"ids":["{file-id}"],"page":1,"limit":1}` hoặc lọc `dataLibraryId`.
- **74** chuyển đổi, **75** duyệt, **76** gỡ index, **77** index lại: `{"ids":["{file-id}"]}`. Dùng đúng hành động khả dụng theo trạng thái; đặc biệt 77 dùng cho file ở trạng thái chưa index, không mặc định gọi thẳng lên file đang/đã index.
- **72** xóa tài liệu: `ids`. Không tự xóa dữ liệu/tài liệu người dùng để dọn test.

API index một tài liệu đã sẵn sàng:

```http
POST /api/v1/ai-agent
Content-Type: application/json
x-req-type: 1
x-req-service: 20

{"fileId":"{file-id}"}
```

Endpoint này dùng cùng cookie/CSRF của phiên, không nhận API Key trực tiếp. `fileId` là ID tài nguyên file từ thao tác 70/73, **không phải** `file_id` từ upload. Bắt đầu index trả về ngay; kiểm tra cả envelope thành công và dữ liệu trạng thái nếu có. Chỉ gọi khi file đã qua chuyển đổi/duyệt và đang `NOT_INDEXED`; không dùng API này để bỏ qua duyệt.

Theo dõi bằng 73 với thời hạn chờ phù hợp kích thước file. Nếu quay lại 0, chưa thể kết luận thành công; báo index thất bại/chưa hoàn tất và đọc thông tin lỗi được API trả về. Nếu response không đủ để chẩn đoán, yêu cầu contract API chi tiết lỗi; không mở UI để xem lỗi. Khi đã ở 2, muốn thay nội dung hoặc index lại thì dùng 76 gỡ index → chờ 0 qua 73 → cập nhật nội dung nếu cần theo contract → index; không xóa/tạo lại tài liệu một cách mù quáng.

Contract hiện tại chưa mô tả trường/endpoint đọc đầy đủ nội dung đã chuyển đổi để rà soát, hoặc chi tiết lỗi conversion/index. Khi bước duyệt hay chẩn đoán cần thông tin đó, báo người dùng cung cấp [API còn thiếu](api-gaps.md). Không đoán URL tải nội dung và không duyệt 75 khi workflow yêu cầu rà soát mà chưa đọc được bản chuyển đổi. Vẫn tiếp tục các phần cấu hình độc lập.

## Gắn vào Agent và xác minh

Tạo/chọn Tool KNOWLEDGE_BASE theo [cấu hình Tool](tools.md#web-search-và-kiến-thức), đặt `allowedCategories` chứa slug danh mục. Gắn Tool vào Skill và Skill vào Agent, rồi tạo chat mới qua HTTP và nhận kết quả bằng WebSocket theo [hướng dẫn test](chat-testing.md). Chạy một câu hỏi có đáp án cụ thể trong tài liệu và một câu hỏi không có đáp án. Kiểm tra nguồn trích dẫn, nội dung, phạm vi danh mục và trường hợp người dùng không có quyền.

Không coi quyền quản lý danh mục là bằng chứng file đã được cô lập cho từng khách hàng. Nếu cần cách ly dữ liệu theo người dùng/khách hàng, kiểm thử dữ liệu ngoài phạm vi bằng đúng danh tính đích trước khi đưa Agent vào sử dụng.
