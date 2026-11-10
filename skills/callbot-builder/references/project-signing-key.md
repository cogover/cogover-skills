# Signing key của project Stringee

Mỗi callbot chạy trên một project Stringee gắn với Workspace (`stringee_x.dh_portal.stringee_project`). Service callbot dùng `stringee.dh_account_project.signing_secret_key` của project để ký và kiểm tra luồng media.

Nếu key trống, mọi cuộc gọi vào/ra callbot đều thất bại:
- phiên vẫn được tạo nhưng bot im lặng rồi cúp máy;
- log pod `stringeex-callbot` có `media ws: chu ky NO_SECRET` và `bot_leg_ended rejected: NO_SECRET`.

## Service tự bảo đảm key

Từ image `stringeex-callbot` `2026-11-10-signkey-*`, mỗi khi tạo callbot, sửa callbot hay bật callbot (`status: active`) qua admin API, service tự kiểm tra key của project:

- **Đã có giá trị:** giữ nguyên, không ghi đè.
- **NULL hoặc rỗng:** service sinh 32 ký tự chữ và số bằng `SecureRandom`. Lệnh `UPDATE` chỉ ghi khi key vẫn trống, nên an toàn khi nhiều replica cùng chạy. Ghi xong service đọc lại để xác nhận.
- **Không lộ key:** response và log không chứa key.
- **Hiệu lực:** kết quả "chưa có key" chỉ được cache 15 giây, nên key mới có hiệu lực gần như ngay trên mọi replica. stringee-server còn cache thêm khoảng 1 phút.

Response của `create_callbot`, `update_callbot` và `set_callbot_status` (khi bật) có thêm trường `signingKey`. Lệnh `apply` in giá trị này ở dòng `projectSigningKey`.

| `signingKey` | Ý nghĩa | Việc cần làm |
|---|---|---|
| `existing` | Project đã có key | Báo "đã có" |
| `created` | Vừa tạo key mới, đọc lại thấy có giá trị | Báo "đã tạo mới"; chờ khoảng 1 phút rồi gọi thử |
| `failed` | Ghi không được: thường do user DB `callbot` thiếu quyền `UPDATE (signing_secret_key)` trên `stringee.dh_account_project`, hoặc lỗi DB | Lưu callbot vẫn thành công. Làm theo [Khi service không tự tạo được](#khi-service-không-tự-tạo-được) |
| `project_not_found` | Project không có trong `dh_account_project` | Kiểm tra lại cấu hình portal/project |
| không có trường này | Service đang chạy bản cũ | Kiểm tra bằng helper bên dưới |

Báo người dùng đúng một trong các trạng thái trên ("đã có" / "đã tạo mới" / lỗi). Không in key.

## Khi service không tự tạo được

Áp dụng khi kết quả là `failed`, hoặc môi trường còn chạy service bản cũ.

- **master / vn-release:** được phép xử lý trực tiếp.
  - Cấp quyền: `GRANT UPDATE (signing_secret_key) ON stringee.dh_account_project TO 'callbot'@'%'`. Lệnh cho user này nằm trong runbook của `stringeex-callbot`.
  - Sau đó lưu lại callbot, ví dụ chạy lại `apply`.
  - Hoặc chạy helper ở chế độ `ensure`.
- **Prod** (mọi namespace production, ở mọi vùng): chỉ đọc. Không tự cấp quyền, không tự ghi key. Báo người dùng nhờ quản trị DB làm một trong hai việc:
  - cấp quyền như trên;
  - chạy lệnh ở [Lệnh cho quản trị DB](#lệnh-cho-quản-trị-db).

Domain Workspace không cho biết nó chạy ở cụm nào: Workspace production có thể nằm ở cụm của vùng khác. Để biết chắc:
1. Gọi một action đọc, ví dụ `rpc get_callbot_settings`.
2. Tìm pod `stringeex-callbot` có log `admin api GET /callbot/v1/admin/workspaces/{WS}/...`.
3. Namespace của pod đó cho biết đây là master/vn-release hay prod.

### Helper `scripts/ProjectSigningKey.java`

Helper [scripts/ProjectSigningKey.java](../scripts/ProjectSigningKey.java) chạy **trong** pod `stringeex-callbot` và dùng cấu hình DB/Vault của pod, nên mật khẩu DB và key không rời khỏi pod.

- Tham số là project ID, hoặc Workspace ID (`WS...`); helper tự tra ra project qua `stringee_x.dh_portal`.
- `check` chỉ đọc.
- `ensure` chỉ ghi khi key đang trống, rồi đọc lại. Helper tự từ chối ghi nếu namespace của pod không phải `vn-release`, `master` hay `release`.

Pod chỉ có JRE, không có `javac`, nên phải biên dịch ở máy local với thư viện của `stringeex-callbot` rồi copy file `.class` vào pod:

```bash
LIB=$(ls -d <stringeex-callbot>/build/install/*/lib)       # ./gradlew installDist nếu chưa có
javac --release 25 -d /tmp/skbuild -cp "$LIB/*" scripts/ProjectSigningKey.java
kubectl -n <ns> exec <pod> -- mkdir -p /tmp/sk
kubectl -n <ns> cp /tmp/skbuild/ProjectSigningKey.class <ns>/<pod>:/tmp/sk/ProjectSigningKey.class
kubectl -n <ns> exec <pod> -- sh -c 'cd /app && java -cp "/tmp/sk:/app/lib/*" ProjectSigningKey check WS...'
kubectl -n <ns> exec <pod> -- sh -c 'cd /app && java -cp "/tmp/sk:/app/lib/*" ProjectSigningKey ensure WS...'   # chỉ master/vn-release
kubectl -n <ns> exec <pod> -- rm -f /tmp/sk/ProjectSigningKey.class
```

Kết quả, mỗi lệnh in một dòng, không có key:

| Dòng in ra | Ý nghĩa |
|---|---|
| `status=existing length=N` | Đã có key |
| `status=created length=32` | Vừa tạo key và đọc lại thấy có giá trị |
| `status=missing` (exit 3) | `check`: chưa có key |
| `status=missing write_refused=prod_read_only` (exit 4) | `ensure` trên prod bị chặn |
| `status=project_not_found` / `no_portal` / `ambiguous_or_no_project` | Sai ID, hoặc Workspace chưa gắn đúng một portal/project |
| `status=update_failed` | Ghi xong đọc lại vẫn trống |

## Lệnh cho quản trị DB

Dùng cho prod. Thay `{PROJECT_ID}` rồi chạy trên DB `stringee`. Key được sinh ngay trong DB, không đi qua máy ai.

`RANDOM_BYTES` cần MySQL ≥ 5.6.17 hoặc MariaDB ≥ 10.10. Nếu DB không hỗ trợ, sinh key bằng `openssl rand` hoặc `secrets` rồi nhập trực tiếp.

```sql
UPDATE stringee.dh_account_project
SET signing_secret_key = LEFT(REPLACE(REPLACE(REPLACE(TO_BASE64(RANDOM_BYTES(48)), '+', ''), '/', ''), '=', ''), 32)
WHERE id = {PROJECT_ID} AND (signing_secret_key IS NULL OR signing_secret_key = '');

SELECT id, CHAR_LENGTH(signing_secret_key) AS key_length FROM stringee.dh_account_project WHERE id = {PROJECT_ID};
```

`key_length` phải bằng 32. Sau khi ghi, chờ khoảng 5 phút (cache của service bản cũ) rồi mới gọi thử.
