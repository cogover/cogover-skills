# Bổ sung Activity cho một Object nghiệp vụ

Cho phép người dùng cùng thảo luận, ghi chú và theo dõi hoạt động trên một Object nghiệp vụ bằng cách nối Object `activity` tới Object đó. Ví dụ với Object `contract`:

1. Dùng Phần 1 của `SKILL.md` đọc Object `activity` và `contract` thật; chỉ tiếp tục khi `activity` chưa có field lookup phù hợp và `contract` chưa có Related List tương ứng. Không tạo trùng quan hệ đã tồn tại.
2. Trên Object `activity`, tạo field `lookup_normal` trỏ tới Object `contract` theo quy trình tạo field của `SKILL.md`: slug kỹ thuật `contract`, `related_list_name` có ý nghĩa theo contract của Object Fields API, Object ID thật, translations và metadata đúng quy trình; không suy đoán ID.
3. Đọc lại cả hai Object. Chỉ tiếp tục khi field `activity.contract` tồn tại đúng type/metadata và `contract.relatedLists` đã có Related List nguồn `activity`. Lấy `relatedListId`, `originSlug`, tên, slug và lookup field thật từ response; không tự tạo hoặc đoán Related List ID.
4. Dùng `$object-layout` đọc layout Xem/Sửa hiện tại của `contract` (`functionLayout: 2`, quyền `VIEW_EDIT`). Đặt component `fieldType: "related_list"` vào đúng hierarchy `layoutRow → layoutColumn → section → tab → group → components`; ưu tiên một tab/section “Activities” trên cột nội dung chính. Giữ nguyên toàn bộ cấu hình ngoài phạm vi và view lại layout sau update.
5. Với Activity, ưu tiên `typeView: "timeline"`, `listAction: [{"value":"CREATE"}]` và `isAllTabActivity: true` để người dùng xem và tạo hoạt động ngay trên bản ghi. Nếu giới hạn loại hoạt động, chỉ dùng các giá trị đã xác minh trên Workspace; layout Lead mẫu hỗ trợ `note`, `email`, `call`, `task`, `meeting`, `sms`, `chat_zalo_fb` và `chat`.
