# Hai cơ chế xác thực Cogover API

## Quản lý credential

1. Resolve Workspace đích từ yêu cầu hoặc cấu hình đã được người dùng chọn. Chuẩn hoá domain bằng cách bỏ protocol và dấu `/` cuối rồi gọi qua `https://{workspace-domain}`; không tự đổi Workspace.
2. Ưu tiên credential đã cấp cho đúng Workspace trong phiên làm việc, tiếp theo là scoped environment hoặc secret store của môi trường. Dùng `COGOVER_API_KEY` và `COGOVER_BASE_URL` làm tên cấu hình chung; `API_KEY`, `WORKSPACE_DOMAIN`, `COGOVER_WORKSPACE_DOMAIN` là tên tương thích trong các ví dụ cũ. Nếu các giá trị cùng tồn tại nhưng chỉ tới Workspace/key khác nhau, dừng để giải quyết xung đột, không chọn ngẫu nhiên.
3. Không dò repository, file dự án hoặc lịch sử shell để tìm secret. Chỉ đọc `.env` cụ thể nếu người dùng đã chủ động chọn file đó hoặc CLI được tài liệu sản phẩm mô tả yêu cầu nó. File phải nằm ngoài gói public, được Git ignore và có quyền truy cập hạn chế. Không yêu cầu một CLI hoặc kho bí mật cá nhân không được đóng gói cùng skill.
4. Chỉ yêu cầu credential qua kênh nhập bí mật khi chưa có hoặc không truy cập được. Không yêu cầu gửi lại key đã có; không đặt key trong prompt cho sub-agent, log, URL, source, ví dụ, báo cáo hoặc câu trả lời.
5. Truyền secret qua cơ chế bí mật/scoped environment của tiến trình cần dùng. Lọc token, cookie và secret khỏi response/debug trước khi hiển thị hoặc lưu bằng chứng. Không in raw response tạo phiên.
6. Kiểm tra binding Workspace theo response tạo phiên ở phần dưới. `401`/`403` không phải lý do dùng key của Workspace khác hoặc tự nâng quyền.

Quy trình chọn credential của một CLI có thể khác thứ tự chung; áp dụng đúng tài liệu của CLI đó và giữ cùng Workspace. Phiên Web App và Workspace API Key không thay thế lẫn nhau tùy ý.

## Quy ước request, response và lỗi chung

Áp dụng cho mọi skill trong bộ; từng skill chỉ ghi thêm ngoại lệ riêng.

- Request `/bapi/v{N}` gửi `Authorization: Bearer {API_KEY}` và `Content-Type: application/json`; request `/api/v{N}` gửi cookie phiên và hai header CSRF/XSRF như mục 3.
- Response có `r` (số, `0` là thành công), `msg` và `data`. Chỉ coi thao tác thành công khi HTTP status phù hợp và `r: 0`.
- Khi HTTP 4xx/422 hoặc `r` khác `0`: hiển thị `r`, `msg` và chi tiết lỗi đã lọc secret, rồi dừng; không đổi endpoint, phiên bản API hay cơ chế xác thực để thử lại.
- `401`/`403`: key không hợp lệ, hết hạn hoặc thiếu quyền; yêu cầu người dùng kiểm tra credential/quyền. Riêng `/api/v{N}`: khi `401`/`403` hoặc lỗi CSRF, tạo lại phiên từ API Key theo mục 3 và thử lại đúng một lần trước khi kết luận; không lặp lại mutation có thể đã có side effect. HTTP 5xx: báo lỗi server, thử lại sau.
- HTTP thành công chưa chứng minh thay đổi nghiệp vụ đúng: đọc lại tài nguyên (view/list) sau khi ghi và so với payload; nếu không khớp, báo rõ và dừng.
- Yêu cầu chỉ xem/phân tích thì không gọi endpoint ghi. Resolve ID/slug thật từ API trước khi ghi; không đoán ID từ tên hiển thị.
- Không đưa API key, cookie, token hoặc response thô chứa secret vào câu trả lời, log, file bàn giao hay prompt cho sub-agent.

## Mục lục

- [Quy ước request, response và lỗi chung](#quy-ước-request-response-và-lỗi-chung)
- [1. Chọn cơ chế theo URI](#1-chọn-cơ-chế-theo-uri)
- [2. Cơ chế API Key cho `/bapi/v{N}`](#2-cơ-chế-api-key-cho-bapivn)
- [3. Cơ chế phiên Web App cho `/api/v{N}`](#3-cơ-chế-phiên-web-app-cho-apivn)
- [4. Vòng đời phiên](#4-vòng-đời-phiên)

## 1. Chọn cơ chế theo URI

Cogover phân biệt hai nhóm API theo tiền tố URI:

| Dạng URI | Cơ chế xác thực |
|---|---|
| `/bapi/v{N}/...` | API Key qua header `Authorization: Bearer {tokenId}-{secretToken}` |
| `/api/v{N}/...` | Phiên Web App qua các cookie `HttpSessionId`, `XSRF-TOKEN`, `AuthToken` và hai header CSRF/XSRF |

Không dùng API Key trực tiếp cho `/api/v{N}`. Nếu chức năng chỉ có endpoint `/api/v{N}`, đổi API Key thành bộ thông tin phiên bằng `POST /bapi/v1/auth-token` rồi dùng phiên đó như Web App trên trình duyệt.

## 2. Cơ chế API Key cho `/bapi/v{N}`

Gửi API Key của workspace trong header:

```http
Authorization: Bearer {tokenId}-{secretToken}
```

API Key phải còn hiệu lực và có quyền truy cập workspace tương ứng.

Ví dụ:

```bash
curl --location 'https://{workspace-domain}/bapi/v1/{resource}' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json'
```

## 3. Cơ chế phiên Web App cho `/api/v{N}`

### 3.1. Tạo phiên từ API Key

Gọi endpoint sau bằng API Key:

```http
POST /bapi/v1/auth-token
Authorization: Bearer {tokenId}-{secretToken}
Content-Type: application/json
```

Request không yêu cầu dữ liệu đầu vào; có thể gửi JSON rỗng `{}`.

```bash
curl --location --request POST 'https://{workspace-domain}/bapi/v1/auth-token' \
  --header 'Authorization: Bearer {tokenId}-{secretToken}' \
  --header 'Content-Type: application/json' \
  --data '{}'
```

Response thành công có HTTP status `200 OK`:

```json
{
  "r": 0,
  "msg": "Success",
  "data": {
    "HttpSessionId": "{HttpSessionId}",
    "HttpSessionExpiresAt": 1786672800,
    "XSRF-TOKEN": "{XSRF-TOKEN}",
    "AuthToken": "{AuthToken}",
    "AuthTokenExpiresAt": 1817694862
  },
  "workspaceId": "{workspaceId}",
  "workspaceDomain": "{workspaceDomain}",
  "personnelId": "{personnelId}"
}
```

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `r` | Integer | `0` nghĩa là thành công |
| `msg` | String | Thông báo kết quả |
| `data.HttpSessionId` | String | ID phiên HTTP |
| `data.HttpSessionExpiresAt` | Integer | Thời điểm phiên HTTP hết hạn, Unix timestamp theo giây |
| `data.XSRF-TOKEN` | String | Token bảo vệ request khỏi giả mạo CSRF |
| `data.AuthToken` | String | Token xác thực workspace |
| `data.AuthTokenExpiresAt` | Integer | Thời điểm AuthToken hết hạn, Unix timestamp theo giây; bằng claim `exp` trong JWT |
| `workspaceId` | String | ID workspace của phiên |
| `workspaceDomain` | String | Định danh domain của workspace; một số deployment trả tenant label như `tenant-a` thay vì FQDN đầy đủ |
| `personnelId` | String | ID nhân sự tương ứng với tài khoản trong workspace |

Response đồng thời thiết lập ba cookie `HttpSessionId`, `XSRF-TOKEN` và `AuthToken`.

Không yêu cầu `workspaceDomain` phải bằng nguyên văn hostname đã gọi. Chuẩn hóa trước khi đối chiếu:

- Nếu response là FQDN, bỏ protocol và dấu `/` cuối rồi so hostname.
- Nếu response là tenant label, so với label đầu của hostname workspace, ví dụ `tenant-a` khớp `tenant-a.example.com`.
- Khi đã biết `workspaceId`, đối chiếu thêm ID này. Dừng nếu label/FQDN hoặc workspace ID chỉ ra workspace khác.

### 3.2. Gọi `/api/v{N}` bằng phiên

Gửi đủ ba cookie và đặt giá trị `XSRF-TOKEN` vào cả hai header:

```http
Cookie: HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}
x-csrf-token: {XSRF-TOKEN}
x-xsrf-token: {XSRF-TOKEN}
```

Hai header phải có cùng giá trị và giá trị đó phải bằng cookie `XSRF-TOKEN`.

Ví dụ:

```bash
curl --url 'https://{workspace-domain}/api/v1/accounts?limit=20&order=last_join_time&sort=desc&status=ACTIVE,INVITED' \
  --header 'accept: application/json, text/plain, */*' \
  --cookie 'HttpSessionId={HttpSessionId}; XSRF-TOKEN={XSRF-TOKEN}; AuthToken={AuthToken}' \
  --header 'x-csrf-token: {XSRF-TOKEN}' \
  --header 'x-xsrf-token: {XSRF-TOKEN}'
```

Trình duyệt tự gửi cookie đã lưu tới đúng workspace. Web App đọc cookie `XSRF-TOKEN` và đặt cùng giá trị vào hai header trước khi gửi request.

## 4. Vòng đời phiên

- Tạo lại phiên trước `HttpSessionExpiresAt`.
- Không tiếp tục dùng `AuthToken` sau `AuthTokenExpiresAt`.
- Phiên có thể được gia hạn khi người dùng tiếp tục hoạt động; ưu tiên giá trị mới nhất do API trả về khi gọi lại endpoint tạo phiên.
