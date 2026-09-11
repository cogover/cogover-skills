# Glossary: thuật ngữ trong code cho user non-coder

Dùng ở Bước 8 của SKILL.md: scan code vừa sinh, chỉ in các entry có xuất hiện trong code.

| Trong code | Giải thích tiếng Việt |
|---|---|
| `changedFields["X"]` | "user vừa đổi field tên X" (true/false) |
| `changedRowCells` | "danh sách các ô bảng user vừa gõ" (mảng) |
| `await` | "đợi" — đứng trước hàm cần đợi xong mới chạy tiếp |
| `$record` | "bản ghi đang sửa" — chứa giá trị các field |
| `$record.id` | "ID của bản ghi" — có nghĩa là form đã lưu rồi |
| `formType` | "loại form đang mở" — `"create"` = Tạo mới, `"view"` = đã lưu (xem/sửa) |
| `$parentRecord` | "bản ghi cha" — khi form con (modal/related list) |
| `$currentPersonnel` | "nhân viên đang đăng nhập" |
| `$ref` | "bộ nhớ tạm của script" — giữ qua các lần script chạy lại trong 1 session |
| `screen.get(slug, "FORM_ITEM")` | "lấy field có slug = X" |
| `screen.get(slug, "RELATED_LIST")` | "lấy bảng (related list) có slug = X" |
| `screen.get(slug, "PATH_COMPONENT")` | "lấy Path Component có slug = X" |
| `screen.triggerButton(slug)` | "tự động bấm button có slug = X" |
| `field.value` | "giá trị của field" — đọc và ghi được |
| `field.display = false` | "ẩn field đi, không hiển thị" |
| `field.readOnly = true` | "khoá field, không cho sửa" |
| `field.required = true` | "bắt buộc nhập field này" |
| `field.limitedOptions` | "giới hạn option chọn (cho select)" |
| `rl.setData([...])` | "ghi đè toàn bộ dòng trong bảng bằng mảng record mới" (API record shape §7B cheatsheet, KHÁC SCRIPT shape của `row.get().value`) |
| `rl.rows()` | "lấy danh sách dòng hiện có trong bảng" |
| `rl.row(i)` | "lấy dòng thứ i (0 là dòng đầu)" |
| `rl.getRow(i)` | "lấy dòng thứ i (0 là dòng đầu)" |
| `rl.getCol(slug)` | "lấy cả cột có slug = X trong bảng" — cần `await` |
| `rl.findRow(predicate)` | "tìm 1 dòng theo điều kiện" |
| `rl.submit()` | "tự động lưu bảng — không cần user bấm nút Lưu" |
| `row.get(slug)` | "lấy ô có slug = X trong dòng" |
| `col.readOnly = true` | "khoá toàn bộ ô trong cột này" |
| `col.required = true` | "bắt buộc nhập toàn bộ ô trong cột này" |
| `col.value = X` | "ghi đè toàn bộ ô hiện có trong cột bằng cùng giá trị X" — chỉ dùng khi nghiệp vụ xác nhận muốn ghi đè toàn cột; không đọc `col.value` để guard |
| `row.readOnly = true` | "khoá toàn bộ ô trong dòng này" |
| `row.required = true` | "bắt buộc nhập toàn bộ ô trong dòng này" |
| `cell.displayHtml` | "đổi cách hiển thị ô (chỉ visual, không lưu data)" |
| `filterRecords(slug, params)` | "query danh sách bản ghi từ object khác" |
| `isDirtyForm` | "form có thay đổi chưa lưu hay không" |
| `new Date()` | "ngày giờ hiện tại" |
| `logger.log(...)` | "ghi dữ liệu debug ra console" — chỉ hiện khi workspace bật chế độ nhà phát triển hoặc bật cờ ép log |
| `logger.forceShowLog` | "cờ ép hiện log" — mặc định `false`, chỉ bật tạm để debug |
| `path.submitBlocked = true` | "khoá toàn bộ nút submit của các stage trong Path Component" |
| `path.submitBlockedStages` | "danh sách stage value bị khoá nút submit; chỉ stage trong danh sách bị disabled" |
