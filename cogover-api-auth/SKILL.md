---
name: cogover-api-auth
description: "Chọn, giải thích và triển khai đúng cơ chế xác thực cho Cogover API: API Key Bearer cho endpoint `/bapi/v{N}` và phiên Web App bằng cookie kèm CSRF/XSRF cho endpoint `/api/v{N}`. Sử dụng khi thiết kế hoặc viết request Cogover API, chuyển API Key thành phiên qua `/bapi/v1/auth-token`, hoặc xử lý token/cookie hết hạn."
metadata:
  author: cogover
  version: "1.0.1"
---

# Cogover API Auth

- **Phiên bản:** `1.0.1`
- **Ngày phát hành:** `2026-09-07`

## Mục tiêu

Chọn cơ chế xác thực theo URI của endpoint và tạo hướng dẫn hoặc mã mẫu tương ứng. Không giả định rằng API Key có thể gọi trực tiếp endpoint `/api/v{N}`.

## Quy trình

Trước khi gọi API, đọc mục [Quản lý credential](references/authentication-mechanisms.md#quản-lý-credential). Quy tắc này là nguồn chung cho mọi skill trong bộ.

1. Xác định chính xác URI endpoint và workspace domain.
2. Chọn cơ chế xác thực theo tiền tố:
   - Dùng API Key Bearer cho `/bapi/v{N}/...`.
   - Dùng phiên Web App cho `/api/v{N}/...`.
3. Nếu chức năng chỉ có endpoint `/api/v{N}`, dùng API Key gọi `POST /bapi/v1/auth-token` để tạo phiên trước.
4. Đọc [references/authentication-mechanisms.md](references/authentication-mechanisms.md) trước khi viết request hoặc mã tích hợp.
5. Tạo ví dụ với placeholder như `{workspace-domain}`, `{tokenId}-{secretToken}`, `{HttpSessionId}`.
6. Kiểm tra request cuối cùng theo danh sách sau:
   - Đúng tiền tố endpoint và đúng cơ chế xác thực.
   - Phiên Web App gửi đủ ba cookie.
   - Hai header `x-csrf-token` và `x-xsrf-token` cùng bằng cookie `XSRF-TOKEN`.
   - Có chiến lược tạo lại phiên trước khi hết hạn.

## Quy tắc trả lời và triển khai

- Giải thích ngắn gọn vì sao chọn cơ chế tương ứng với URI.
- Với `/bapi`, minh họa header `Authorization` bằng placeholder.
- Với `/api`, trình bày cả bước tạo phiên và bước dùng phiên; không chỉ đưa riêng `AuthToken`.
- Không suy đoán endpoint, thời hạn token hoặc chính sách quyền ngoài tài liệu tham chiếu. Nêu rõ thông tin còn thiếu nếu cần xác minh.

## Kết quả mong đợi

Khi người dùng yêu cầu ví dụ hoặc tích hợp, cung cấp tối thiểu:

1. Cơ chế được chọn và lý do.
2. Request mẫu bằng cURL hoặc ngôn ngữ được yêu cầu.
3. Cách quản lý vòng đời token/cookie.
