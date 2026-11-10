# Signing key của project Stringee

Mỗi callbot chạy trên project Stringee gắn với Workspace (`stringee_x.dh_portal.stringee_project`). Service callbot dùng `stringee.dh_account_project.signing_secret_key` của project để ký và kiểm tra luồng media. Key trống thì cuộc gọi vào/ra callbot thất bại:

- Phiên được tạo nhưng bot im lặng, rồi cuộc gọi bị cúp.
- Log của pod `stringeex-callbot` có `media ws: chu ky NO_SECRET` (WebSocket media trả 401) và `bot_leg_ended rejected: NO_SECRET`.

Nhiều project, nhất là project cũ trên prod, chưa có key. Vì vậy **luôn kiểm tra key trước khi gọi thử** (bước A.5 trong [SKILL.md](../SKILL.md)).

## Quy tắc

- **Đã có giá trị:** giữ nguyên, không ghi đè.
- **NULL hoặc rỗng:** sinh ngẫu nhiên chuỗi **32 ký tự chữ và số** từ nguồn ngẫu nhiên an toàn (`SecureRandom`; nếu sinh ngoài pod thì dùng `secrets` của Python hoặc `openssl rand`), rồi cập nhật vào project.
- **Không lộ key:** không in key ra output, log, transcript hay báo cáo. Không truyền key qua tham số dòng lệnh. Chỉ báo "đã có" hoặc "đã tạo mới".
- **Xác nhận trước khi test:** sau khi cập nhật, đọc lại để chắc giá trị không còn trống. Chờ cache hết hạn rồi mới gọi kiểm tra:
  - service callbot cache key 5 phút, kể cả kết quả trống;
  - stringee-server cache 1 phút.
- **Chỉ ghi trên môi trường thử nghiệm.** Không có API công khai hay API của Cogover/StringeeX để đặt key: cách duy nhất là ghi thẳng DB `stringee.dh_account_project`. Được phép trên **master / vn-release** (namespace `vn-release`, `master`, `release`).
- **Prod chỉ đọc** (mọi namespace production, ở mọi vùng). Thiếu key trên prod thì dừng bước gọi thử và báo người dùng nhờ quản trị DB chạy lệnh ở [Lệnh cho quản trị DB](#lệnh-cho-quản-trị-db). Cấu hình callbot và mô phỏng vẫn làm được.

## Xác định môi trường

Domain Workspace không nói lên cụm. Cách chắc chắn:
1. Gọi một action đọc (ví dụ `rpc get_callbot_settings`).
2. Tìm pod `stringeex-callbot` có log admin API của Workspace đó (`admin api GET /callbot/v1/admin/workspaces/{WS}/...`).

Workspace production có thể chạy ở cụm của vùng khác. Namespace của pod đó cho biết đó là master/vn-release hay prod.

## Kiểm tra / tạo bằng helper

[scripts/ProjectSigningKey.java](../scripts/ProjectSigningKey.java) chạy **trong** pod `stringeex-callbot`. Nó dùng cấu hình DB và Vault sẵn có của pod, nên mật khẩu DB và key không bao giờ rời pod.

- Tham số là project ID, hoặc Workspace ID (`WS...`, helper tự tra ra project qua `stringee_x.dh_portal`).
- `check`: chỉ đọc.
- `ensure`: chỉ ghi khi key trống, dùng `UPDATE ... WHERE signing_secret_key IS NULL OR = ''`, rồi đọc lại. Helper tự từ chối ghi nếu namespace của pod không thuộc `vn-release`/`master`/`release`.

Pod chỉ có JRE (không có `javac`): biên dịch ở máy local với thư viện của `stringeex-callbot`, rồi copy file `.class` vào pod.

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

| Dòng in ra | Ý nghĩa | Báo người dùng |
|---|---|---|
| `status=existing length=N` | Đã có key | "đã có" |
| `status=created length=32` | Vừa tạo và đọc lại thấy có giá trị | "đã tạo mới"; chờ 5 phút rồi mới gọi |
| `status=missing` (exit 3) | `check`: chưa có key | Chạy `ensure` (master/vn-release) hoặc báo quản trị DB (prod) |
| `status=missing write_refused=prod_read_only` (exit 4) | `ensure` trên prod bị chặn | Báo quản trị DB |
| `status=project_not_found`, `no_portal`, `ambiguous_or_no_project` | Sai ID, hoặc Workspace chưa gắn đúng một portal hay project | Kiểm tra lại Workspace/portal |
| `status=update_failed` | Ghi xong đọc lại vẫn trống | Dừng, báo lỗi |

Nhớ xoá file `.class` khỏi pod sau khi chạy xong. Không sửa code hay ảnh của service.

## Lệnh cho quản trị DB

Dùng cho prod hoặc khi không chạy được helper. Quản trị DB chạy trên DB `stringee`, thay `{PROJECT_ID}`. Key được sinh ngay trong DB, không đi qua máy ai. `RANDOM_BYTES` cần MySQL ≥ 5.6.17 hoặc MariaDB ≥ 10.10; DB không hỗ trợ thì sinh key bằng `openssl rand` / `secrets` rồi nhập trực tiếp.

```sql
UPDATE stringee.dh_account_project
SET signing_secret_key = LEFT(REPLACE(REPLACE(REPLACE(TO_BASE64(RANDOM_BYTES(48)), '+', ''), '/', ''), '=', ''), 32)
WHERE id = {PROJECT_ID} AND (signing_secret_key IS NULL OR signing_secret_key = '');

SELECT id, CHAR_LENGTH(signing_secret_key) AS key_length FROM stringee.dh_account_project WHERE id = {PROJECT_ID};
```

`key_length` phải bằng 32. Chờ 5 phút rồi mới gọi thử.
