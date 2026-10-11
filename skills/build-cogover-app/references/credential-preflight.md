# Credential Preflight

Chứng minh API key dùng được cho đúng Workspace đích và đủ quyền đọc tối thiểu để khảo sát. Đây là read-only authentication gate, không cấp quyền mutation. Cách resolve, truyền và bảo vệ credential nói chung theo [Quản lý credential](../../cogover-api-auth/references/authentication-mechanisms.md#quản-lý-credential) của `$cogover-api-auth`; phần dưới chỉ nêu quy tắc riêng của gate này.

## Resolve credential

- Chuẩn hóa Workspace từ alias, URL hoặc domain; giữ target host và Workspace ID kỳ vọng nếu đã biết.
- Nhận API key qua secret field, scoped environment, secret manager, credential broker hoặc cơ chế bí mật tương đương của runtime; không quy định một hệ điều hành, CLI hay kho bí mật riêng. Runtime chưa có credential thì yêu cầu người dùng cung cấp qua secret input/kênh bí mật, không dán vào artifact hoặc chat khi có kênh bí mật.
- Không fallback sang browser session, credential của Workspace khác hoặc key lưu trong file/repository.

## Quy trình xác thực

### 1. Authentication probe

Dùng `$cogover-api-auth` gọi `POST /bapi/v1/auth-token` trên chính target host. Không log header, cookies hoặc response `data`; chỉ giữ các trường đã redacted cần cho verification. Kiểm tra:

- HTTP `200`, `r: 0` và message thành công.
- `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` không rỗng; `HttpSessionExpiresAt` và `AuthTokenExpiresAt` còn hiệu lực theo clock hiện tại.
- `workspaceDomain` và `workspaceId` có giá trị hợp lệ; `personnelId` không rỗng khi response contract trả trường này.

### 2. Workspace binding

- Bỏ protocol, path, port không liên quan và dấu `/` cuối khỏi FQDN trước khi so.
- Response trả tenant label thì so với label đầu của hostname; ví dụ `tenant-a` khớp `tenant-a.example.com`.
- Đã biết Workspace ID thì yêu cầu `workspaceId` khớp chính xác.
- Dừng ngay nếu domain/label hoặc Workspace ID chỉ ra Workspace khác; không thử dùng key đó trên Workspace khác.

### 3. Discovery access probes

Sau khi auth và binding đạt, chạy probe đọc tối thiểu bằng đúng credential/session, không mutation:

1. `$app-menu-manager` list App hoặc endpoint đọc tương đương.
2. `$object-info` list Object hoặc endpoint đọc tương đương.

Yêu cầu response thành công, không `401/403`, không business permission error và đúng cấu trúc contract. Danh sách rỗng hợp lệ nếu API trả thành công và Workspace thực sự chưa có resource. Không mở rộng sang khảo sát đầy đủ ở bước này.

### 4. Super Admin claim

- API/read state có trường role/permission đáng tin cậy: xác minh key thuộc Super Admin, ghi `SUPER_ADMIN_VERIFIED` hoặc `INSUFFICIENT_PRIVILEGE`.
- Contract không cho phép chứng minh role: ghi `SUPER_ADMIN_UNVERIFIED`; vẫn bắt đầu discovery khi auth, binding và discovery probes đều đạt, nhưng phải xác minh quyền đặc thù trước mutation.
- State chứng minh không phải Super Admin trong khi phase sau cần quyền đó: dừng trước work item tương ứng và yêu cầu credential đúng quyền.

## Điều kiện thành công

Gate chỉ đạt `VERIFIED` khi đồng thời: credential resolve qua kênh bí mật; authentication probe thành công và session còn hiệu lực; Workspace binding khớp target; App-list và Object-list discovery probes thành công. Không dùng “key đúng format” hoặc “auth-token trả 200” một mình làm bằng chứng đủ. Chỉ `VERIFIED` cho phép Phase 1 bắt đầu.

## Trạng thái lỗi

| Status | Điều kiện | Xử lý |
|---|---|---|
| `MISSING` | Không có key hoặc secret store không truy cập được | Dừng; yêu cầu cung cấp/khôi phục credential qua kênh bí mật |
| `INVALID` | `401`, business auth failure, token/session thiếu hoặc hết hạn ngay | Dừng; yêu cầu key còn hiệu lực |
| `WORKSPACE_MISMATCH` | Domain/label hoặc Workspace ID khác target | Dừng; yêu cầu key đúng Workspace; không fallback |
| `INSUFFICIENT_DISCOVERY_ACCESS` | Auth thành công nhưng App/Object probe bị từ chối | Dừng; yêu cầu key đủ quyền khảo sát |
| `INSUFFICIENT_PRIVILEGE` | State chứng minh không có quyền Super Admin cần thiết | Dừng trước phase/work item cần quyền đó |
| `UNVERIFIED_TRANSIENT` | Timeout, DNS, `5xx` hoặc lỗi tạm thời không chứng minh key sai | Retry có giới hạn; vẫn lỗi thì dừng, không gắn nhãn `INVALID` |

## Evidence và tái xác thực

Giữ evidence đã redacted: verification time và verifier/task ID; target alias/hostname, response `workspaceDomain`/`workspaceId` và personnel ID nếu cần; auth result, expiry check và kết quả hai discovery probes; Super Admin status (`SUPER_ADMIN_VERIFIED`, `SUPER_ADMIN_UNVERIFIED` hoặc `INSUFFICIENT_PRIVILEGE`). Không giữ API key, `HttpSessionId`, `XSRF-TOKEN`, `AuthToken`, cookies, Authorization header hoặc raw response chứa chúng.

Trong solution artifact, thêm marker và metadata:

```markdown
<!-- cogover-api-key-preflight:VERIFIED -->
- Credential preflight: VERIFIED
- Credential verified at:
- Verified Workspace domain/ID:
- Discovery access probes: PASS
- Super Admin status:
```

Tái xác thực khi target Workspace/key thay đổi, credential bị rotate/revoke, phiên hết hạn, probe bắt đầu trả auth/permission error hoặc ngay trước apply khi verification evidence không còn mới.
