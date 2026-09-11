# Dựng payload PUT cho Layouts V2

Áp dụng cho mọi cập nhật layout: nội dung, script, `pageSettings.buttons`, Path Component. Allowlist, trường server-managed và quy tắc xác minh nằm ở mục "Layouts V2 API" trong [SKILL.md](../SKILL.md).

## Mẫu PUT

```bash
curl --silent --location --request PUT 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/{LAYOUT_ID}' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{
    "name": "Current Layout",
    "objectTypeSlug": "{OBJECT_SLUG}",
    "status": 1,
    "type": 2,
    "updateRecordMode": 4,
    "accessControls": [ ... giữ nguyên từ layout hiện tại ... ],
    "hasComponentPath": "<giữ nguyên giá trị hiện tại, kể cả null>",
    "content": [ ... giữ nguyên hoặc chỉ sửa phần được yêu cầu ... ],
    "title": { ... giữ nguyên ... },
    "pageSettings": {
      "...": "... giữ nguyên các key hiện tại ...",
      "script": "SCRIPT_MOI_DA_ESCAPE"
    },
    "functionLayout": 2,
    "isWeb": true,
    "isMobile": false
  }'
```

## Cập nhật script bằng jq

`jq --rawfile` giữ nguyên xuống dòng và dấu nháy trong JavaScript; ưu tiên cách này thay vì escape thủ công. File tạm chỉ chứa script/payload layout, không chứa API key; xoá sau khi dùng.

```bash
SCRIPT_FILE="/tmp/layout-script.js"

curl --silent --location 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/view' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data '{"id":"{LAYOUT_ID}"}' \
| jq --rawfile script "$SCRIPT_FILE" '
    .data
    | {
        name,
        objectTypeSlug,
        status,
        type,
        updateRecordMode,
        accessControls,
        hasComponentPath,
        content,
        title,
        pageSettings: ((.pageSettings // {}) + {script: $script}),
        functionLayout,
        isWeb: (.isWeb == true or .isWeb == 1),
        isMobile: (.isMobile == true or .isMobile == 1)
      }
  ' \
> /tmp/layout-update.json

curl --silent --location --request PUT 'https://{WORKSPACE_DOMAIN}/bapi/v1/layouts_v2/{LAYOUT_ID}' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {API_KEY}' \
  --data @/tmp/layout-update.json
```

Xoá script: thay `$script` bằng `""` hoặc `null` theo payload hiện tại của hệ thống. Sau `PUT`, view lại và so sánh `data.pageSettings.script` với script đã gửi.
