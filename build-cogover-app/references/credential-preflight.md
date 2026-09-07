# Credential Preflight

## Mục lục

1. [Mục tiêu](#mục-tiêu)
2. [Resolve credential](#resolve-credential)
3. [Quy trình xác thực](#quy-trình-xác-thực)
4. [Điều kiện thành công](#điều-kiện-thành-công)
5. [Trạng thái lỗi](#trạng-thái-lỗi)
6. [Evidence và tái xác thực](#evidence-và-tái-xác-thực)

## Mục tiêu

Chứng minh API key dùng được cho đúng Workspace đích và đủ quyền đọc tối thiểu để khảo sát. Đây là read-only authentication gate, không cấp quyền mutation.

## Resolve credential

1. Chuẩn hóa Workspace từ alias, URL hoặc domain; giữ target host và Workspace ID kỳ vọng nếu đã biết.
2. Nhận API key qua secret field, scoped environment, secret manager, credential broker hoặc cơ chế bí mật tương đương của runtime. Không quy định một hệ điều hành, CLI hay kho bí mật riêng.
3. Chỉ cấp key cho process thực hiện authentication probe; không echo, serialize, ghi file hoặc đưa vào command literal có thể bị log.
4. Nếu runtime chưa có credential, yêu cầu người dùng cung cấp qua secret input/kênh bí mật phù hợp; không yêu cầu dán key vào artifact hoặc nội dung trò chuyện khi có kênh bí mật.
5. Không fallback sang browser session, credential của Workspace khác hoặc key lưu trong file/repository.

## Quy trình xác thực

### 1. Authentication probe

Dùng `$cogover-api-auth` gọi trên chính target host:

```http
POST /bapi/v1/auth-token
Authorization: Bearer <secret API key>
Content-Type: application/json
```

Không log header, cookies hoặc response `data`. Chỉ giữ các trường đã redacted cần cho verification.

Kiểm tra:

- HTTP `200`, business result `r: 0` và message thành công.
- `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` không rỗng.
- `HttpSessionExpiresAt` và `AuthTokenExpiresAt` còn hiệu lực theo clock hiện tại.
- `workspaceDomain` và `workspaceId` có giá trị hợp lệ; `personnelId` không rỗng khi response contract trả trường này.

### 2. Workspace binding

Chuẩn hóa và đối chiếu target với response:

- Bỏ protocol, path, port không liên quan và dấu `/` cuối khỏi FQDN.
- Nếu response trả tenant label, so với label đầu của hostname; ví dụ `tenant-a` khớp `tenant-a.example.com`.
- Nếu đã biết Workspace ID, yêu cầu `workspaceId` khớp chính xác.
- Dừng ngay nếu domain/label hoặc Workspace ID chỉ ra Workspace khác. Không thử dùng key đó trên Workspace khác.

### 3. Discovery access probes

Sau khi auth và binding đạt, chạy probe đọc tối thiểu bằng đúng credential/session:

1. Dùng `$app-menu-manager` list App hoặc endpoint đọc tương đương; không mutation.
2. Dùng `$object-info` list Object hoặc endpoint đọc tương đương; không mutation.
3. Yêu cầu response thành công, không `401/403`, không business permission error và có cấu trúc response đúng contract. Danh sách rỗng hợp lệ nếu API trả thành công và Workspace thực sự chưa có resource.

Không mở rộng sang khảo sát đầy đủ ở bước này. Probe chỉ chứng minh credential đủ dùng để bắt đầu discovery.

### 4. Super Admin claim

- Nếu API/read state có trường role/permission đáng tin cậy, xác minh key thuộc Super Admin và ghi `SUPER_ADMIN_VERIFIED` hoặc `INSUFFICIENT_PRIVILEGE`.
- Nếu contract không cho phép chứng minh role, ghi `SUPER_ADMIN_UNVERIFIED`; có thể bắt đầu discovery khi auth, binding và discovery probes đều đạt, nhưng phải xác minh quyền đặc thù trước mutation.
- Nếu state chứng minh không phải Super Admin trong khi phase sau yêu cầu quyền đó, dừng trước work item tương ứng và yêu cầu credential đúng quyền.

## Điều kiện thành công

Gate chỉ đạt `VERIFIED` khi đồng thời:

1. Credential đã được resolve qua kênh bí mật.
2. Authentication probe thành công và session còn hiệu lực.
3. Workspace binding khớp target.
4. App-list và Object-list discovery probes thành công.

Không dùng “key có đúng format” hoặc “auth-token trả 200” một mình làm bằng chứng đủ.

## Trạng thái lỗi

| Status | Điều kiện | Xử lý |
|---|---|---|
| `MISSING` | Không có key hoặc secret store không truy cập được | Dừng; yêu cầu cung cấp/khôi phục credential qua kênh bí mật |
| `INVALID` | `401`, business auth failure, token/session thiếu hoặc hết hạn ngay | Dừng; yêu cầu key còn hiệu lực |
| `WORKSPACE_MISMATCH` | Domain/label hoặc Workspace ID khác target | Dừng; yêu cầu key đúng Workspace; không fallback |
| `INSUFFICIENT_DISCOVERY_ACCESS` | Auth thành công nhưng App/Object probe bị từ chối | Dừng; yêu cầu key đủ quyền khảo sát |
| `INSUFFICIENT_PRIVILEGE` | State chứng minh không có quyền Super Admin cần thiết | Dừng trước phase/work item cần quyền đó |
| `UNVERIFIED_TRANSIENT` | Timeout, DNS, `5xx` hoặc lỗi tạm thời không chứng minh key sai | Có thể retry có giới hạn; nếu vẫn lỗi thì dừng, không gắn nhãn `INVALID` |

Chỉ `VERIFIED` cho phép Phase 1 bắt đầu.

## Evidence và tái xác thực

Giữ evidence đã redacted:

- Verification time và verifier/task ID.
- Target alias/hostname, response `workspaceDomain`/`workspaceId` và personnel ID nếu cần.
- Auth result, expiry check và kết quả hai discovery probes.
- Super Admin status: `SUPER_ADMIN_VERIFIED`, `SUPER_ADMIN_UNVERIFIED` hoặc `INSUFFICIENT_PRIVILEGE`.

Không giữ API key, `HttpSessionId`, `XSRF-TOKEN`, `AuthToken`, cookies, Authorization header hoặc raw response chứa chúng.

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
