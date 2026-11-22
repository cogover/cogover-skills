# Object trên cổng

Mỗi Object khách được xem là một dòng cấu hình (`configId`) với khoá menu `objectKey`. Cấu hình nằm trong `draft`; khách thấy bản chụp lúc xuất bản (`published`). Sửa layout, bản dịch field sau đó **không** có hiệu lực tới khi xuất bản lại.

Thêm/sửa/bỏ Object trên cổng chỉ Super Admin làm được. API: [admin-api.md](admin-api.md#object-trên-cổng).

## Mục lục

- [Quy tắc chia sẻ dữ liệu](#quy-tắc-chia-sẻ-dữ-liệu)
- [Preset có sẵn](#preset-có-sẵn)
- [Schema cấu hình Object](#schema-cấu-hình-object)
- [Trạng thái `enabled` / `published`](#trạng-thái-enabled--published)
- [Chọn layout chi tiết](#chọn-layout-chi-tiết)
- [Đánh giá field khách đang thấy](#đánh-giá-field-khách-đang-thấy)
- [Related list](#related-list)
- [Điều kiện lọc `extraFilter`](#điều-kiện-lọc-extrafilter)
- [Khách tạo bản ghi](#khách-tạo-bản-ghi)
- [Phạm vi thành viên](#phạm-vi-thành-viên)
- [Trao đổi trên bản ghi](#trao-đổi-trên-bản-ghi)
- [Mẫu in PDF](#mẫu-in-pdf)
- [Hành động của khách](#hành-động-của-khách)
- [Quy trình thêm một Object](#quy-trình-thêm-một-object)

## Quy tắc chia sẻ dữ liệu

Khách chỉ thấy bản ghi có `accountField` = Tài khoản của Liên hệ đang đăng nhập **và** khớp `extraFilter`. Cổng tự thêm điều kiện này ở máy chủ; khách không đổi được. Một người có Liên hệ ở nhiều Tài khoản chọn từng Tài khoản, dữ liệu không trộn. Quyền đi theo Liên hệ: đổi `contact.account` thì khách thấy dữ liệu Tài khoản mới (phiên cũ bị huỷ, quản trị viên phía khách bị hạ về thành viên).

Object không đưa lên cổng được: `account`, `contact`, `personnel`, Object nội bộ (hoạt động, lịch sử, email, phòng ban, vị trí...), `accounts_receivable` (dùng khối công nợ), `portal_task` (dùng khối việc cần làm), Object do cổng tự tạo để lưu trao đổi/đăng ký. Đã kiểm: `objectSlug: account` → 422 `not_allowed`.

## Preset có sẵn

`GET objects/presets` (đã kiểm trên Workspace có Sales + Finance):

| `preset` / `objectSlug` | `accountField` | `contactField` | Quyền | Mặc định đáng chú ý |
|---|---|---|---|---|
| `quote` (Báo giá) | `account` | `contact` | xem | ẩn `status = draft`; related list dòng báo giá |
| `contract` (Hợp đồng) | `account` | `customer_signed_by` | xem | ẩn `draft`, `in_approval_process` |
| `order` (Đơn hàng) | `account` | `contact` | xem | ẩn `draft`, `creating` NGOẠI TRỪ đơn khách đặt từ cổng (`logic: CUSTOM`, `1 OR 2`) |
| `customer_invoice` (Hoá đơn) | `customer` | `contact` | xem | chỉ `status = approved` |
| `ticket` (Yêu cầu hỗ trợ) | `account` | `contact` | xem + tạo | tạo với `name` (bắt buộc), `type`, `priority`, `description`; mặc định `status = new`; bật trao đổi |
| `balance_confirmation` (Xác nhận số dư) | `account` | `contact` | xem | ẩn `draft`; hai hành động có mã xác nhận (xem [settings-and-features.md](settings-and-features.md#xác-nhận-số-dư)) |

`available: false` = Workspace thiếu Object đó. Preset chỉ là giá trị khởi tạo; vẫn phải chọn layout trước khi xuất bản. `defaultSort` của preset là `created desc`.

Slug trạng thái trong bảng là giá trị thường gặp của app chuẩn, không phải danh sách cố định: trước khi viết `extraFilter`, `actions`, `notifications.invoiceNew.statuses` hay hỏi người dùng "trạng thái nào được thấy", đọc option thật của field `status` bằng [$object-info](../../object-info/SKILL.md). Khi tìm bản ghi bằng [$object-record](../../object-record/SKILL.md), dùng đúng `fieldType` và toán tử của skill đó (vd `short_text` tìm gần đúng là `like`, không phải `contains`).

## Schema cấu hình Object

```json
{
  "label": {"vi-VN": "Hoá đơn", "en-US": "Invoices"},
  "icon": "file-invoice",
  "accountField": "customer",
  "contactField": "contact",
  "permissions": {"view": true, "create": false},
  "listColumns": ["name", "invoice_date", "due_date", "grand_total", "remaining_amount", "payment_status"],
  "defaultSort": {"field": "created", "dir": "desc"},
  "filterableFields": ["payment_status", "invoice_date"],
  "searchFields": ["name"],
  "extraFilter": {"filters": [{"field": "status", "op": "in", "params": ["approved"], "fieldType": "single_choice"}], "logic": "AND"},
  "detailLayoutId": "<LAYOUT_ID>",
  "relatedLists": [{"id": "<RELATED_LIST_ID>", "columns": []}],
  "createFields": [],
  "createDefaults": {},
  "documentTemplateIds": [],
  "conversation": {"enabled": false},
  "memberScope": "account",
  "actions": []
}
```

| Khoá | Quy tắc | Issue khi xuất bản |
|---|---|---|
| `accountField` | Field `lookup_normal` tới `account` (lấy từ `candidates.accountFields`) | `invalid_account_field` |
| `contactField` | Lookup tới `contact` (`candidates.contactFields`), tuỳ chọn nhưng cần cho phạm vi thành viên và hành động | `invalid_contact_field` |
| `listColumns` | Field có thật, kiểu hỗ trợ (`candidates.fields[].supported`) | `invalid_list_columns` |
| `filterableFields`, `searchFields` | Tập con của `listColumns`; `searchFields` là field văn bản | `invalid_filterable_fields`, `invalid_search_fields` |
| `defaultSort` | `{field, dir: asc/desc}`; field sắp xếp được: văn bản ngắn, số, tiền, ngày, auto_number, lựa chọn | |
| `detailLayoutId` | Layout xem của chính Object, đang bật | `invalid_layout`, `layout_has_no_visible_fields`, `standard_layout_not_supported` |
| `objectKey` (ngoài `config`) | `^[a-z][a-z0-9_]*`, duy nhất, không bắt đầu `bapi`; khoá dành riêng `tasks`, `statement`, `shop`, `cart`, `team`, `profile` (`reserved`) | `invalid_object_key`, `reserved_object_key`, `duplicate_object_key` |
| `label`, `icon` | Nhãn menu vi/en; tên icon | |
| `sortOrder` (ngoài `config`) | Thứ tự menu | |

Các cờ phải là boolean JSON. Không có Object nào bật và công nợ/việc cần làm cũng tắt → `no_content_enabled`.

## Trạng thái `enabled` / `published`

Đọc ở `GET objects` (đã kiểm từng tổ hợp):

| `enabled` | `published` | `publishedVersion` | Nghĩa | Làm gì |
|---|---|---|---|---|
| `true` | `false` | `null` | Mới thêm hoặc vừa bật lại, chưa xuất bản: khách chưa thấy | Xuất bản |
| `true` | `true` | số | Đang hiện trên cổng (bản chụp của lần xuất bản đó) | |
| `false` | `true` | số | Đã `DELETE` (hoặc tắt) nhưng chưa xuất bản: khách **vẫn** thấy | Xuất bản để gỡ |
| `false` | `false` | `null` | Đã gỡ khỏi cổng; cấu hình nháp còn giữ | Bật lại hoặc `DELETE` lần nữa để xoá hẳn |

- Bật lại một Object đã tắt: `PUT objects/{configId}` với `{"enabled": true, "config": {...draft...}}` (script: `object-update <CONFIG_ID> --enabled true --apply`) rồi xuất bản. Đã kiểm: `enabled` thành `true`, sau xuất bản `published: true`.
- `preset: null` chỉ nghĩa là dòng cấu hình được thêm không kèm `preset` (Object tuỳ biến, hoặc Object chuẩn thêm theo cách tuỳ biến); không ảnh hưởng hoạt động.
- Bản `published` dùng tên khoá khác bản nháp: `extraFilterTree` (cây đã biên dịch) thay `extraFilter`, `documentTemplates` thay `documentTemplateIds`, không có `detailLayoutId` (layout đã được chụp thành `detailSections`, `viewFields`), có thêm `viewFields`, `fieldMeta`, `sortableFields`, `_draft`. Đọc/sửa cấu hình luôn ở `draft`; khoá vắng trong `published` không có nghĩa cấu hình bị mất.

## Chọn layout chi tiết

**Mọi field trên layout chi tiết đều thành field khách xem được** (đã kiểm: layout xem chuẩn của Hợp đồng đưa cả `owner`, giá trị hợp đồng nội bộ lên cổng; cổng tự thêm `id`, `name`, `created`, `contactField` và cột danh sách). Bị bỏ: field ẩn, field kiểu không hỗ trợ (cảnh báo `unsupported_type_skipped`), display box, nút, path component, script, báo cáo, component tuỳ biến. Component QR chuyển khoản được giữ nếu nội dung chỉ dùng field có trên layout. Layout tiêu chuẩn (`isStandard`) của Object thường không có nội dung cố định → `standard_layout_not_supported` (thành lỗi nếu có hành động); Object do cổng tạo (Xác nhận số dư) dùng layout tiêu chuẩn được.

Nếu một layout xem có sẵn chỉ chứa field cho khách thì chọn luôn. Không có thì tạo layout riêng cho cổng bằng [$object-layout](../../object-layout/SKILL.md) theo đúng quy trình dưới. Lý do (đã kiểm): **layout mới tạo được xếp sau cùng nên trở thành layout Xem mặc định của nhân viên** khi mở bản ghi trên Web App, kể cả khi quyền layout chỉ giao cho một nhân sự khác (Super Admin vẫn nhận layout đó làm mặc định). Cờ `isShowInPicker: 0` (ẩn khỏi bộ chọn layout) làm layout không bao giờ được chọn làm mặc định và không hiện trong bộ chọn, trong khi cổng vẫn dùng được: cổng đọc layout không qua quyền layout của nhân viên (đã kiểm với layout chỉ giao cho một nhân sự không liên quan: vẫn có trong `candidates.layouts` và xuất bản đúng `viewFields`).

Quy trình an toàn:

1. Chụp hiện trạng: `POST /bapi/v1/layouts_v2/list` của Object (ghi lại id, tên, `sort`, `isShowInPicker`), và `view` layout xem đang dùng làm mẫu. Giữ bản sao `content` của layout mẫu.
2. Tạo layout mới (theo `$object-layout`): `functionLayout: 2`, `isWeb: true`, tên rõ ("Customer Portal view"), `content` chỉ gồm field dành cho khách (lấy từ layout mẫu, bỏ field nội bộ), và hai khoá sau:

   ```json
   {"isShowInPicker": 0,
    "accessControls": [{"functions": ["VIEW_EDIT"], "option": 2, "items": ["<PERSONNEL_ID_NGUOI_CAU_HINH>"], "type": "personnel"}]}
   ```

   `items` khi ghi là **mảng ID dạng chuỗi** (nhân sự/phòng ban/chức vụ/role tương ứng `type`). Response `view` trả `items` dạng object đầy đủ (vd option 1 trả `[{"id": "all", ...}]`): không gửi lại dạng object đó với `option: 2` (nhân sự → 400 `r: 43201`; role → lưu "thành công" nhưng hỏng danh sách layout, xem bước 4). `option: 1` (mọi nhân sự) vẫn dùng được nhờ `isShowInPicker: 0`, nhưng giới hạn cho người cấu hình gọn hơn.
3. Đọc lại ngay: `view` layout mới (`isShowInPicker: 0`, `accessControls` đúng) **và** `list` layout của Object.
4. Nếu `list` hoặc `view` trả HTTP 200 nhưng `msg: "Internal Server Error"` và không có khoá `data`: layout vừa ghi có `accessControls` sai dạng, mọi màn hình layout của Object đang lỗi. Xoá ngay layout đó bằng `POST /bapi/v1/layouts_v2/delete {"data": ["<LAYOUT_ID>"]}` rồi đọc lại `list` (đã kiểm: hết lỗi). Lỗi do `PUT` lên layout đang dùng: sửa bằng `PUT` lại đủ payload với `items` là ID chuỗi (cần bản `content` đã chụp ở bước 1). Chỉ thử nghiệm trên Object tạm, không trên Object chuẩn đang dùng.
5. `GET objects/candidates/{objectSlug}?layoutId=<LAYOUT_ID>` → layout có trong `layouts`, related list cần dùng có `onLayout: true`.
6. Gắn `detailLayoutId`, xuất bản, đọc `published.viewFields`.
7. Nếu người dùng mở bản ghi trên Web App: layout Xem mặc định của nhân viên vẫn như trước (layout cổng không hiện trong bộ chọn). Layout tạo trước đây cho cổng mà chưa ẩn: `PUT` đủ payload kèm `isShowInPicker: 0` (đã kiểm: màn hình mặc định trở về layout cũ).

## Đánh giá field khách đang thấy

Khi khảo sát cổng đang chạy (hoặc sau mỗi lần xuất bản), với từng Object: `GET objects/{configId}` → so `published.viewFields` và `published.listColumns` với nhãn field (`$object-info`). Xếp mức:

| Mức | Ví dụ field | Báo người dùng |
|---|---|---|
| Cao | Giá vốn, lợi nhuận, chiết khấu nội bộ, ghi chú nội bộ, field tài chính/nhân sự | Đang lộ cho khách; đề xuất sửa ngay |
| Trung bình | `owner`, `assignee`, `approved_by`, `created_by`, phòng ban, người duyệt | Lộ tên nhân viên nội bộ; hỏi người dùng có chấp nhận không |
| Thấp | `created`, `updated`, mã nội bộ không nhạy cảm | Ghi nhận |

Cách sửa: tạo layout riêng cho khách theo [quy trình trên](#chọn-layout-chi-tiết) (hoặc bỏ field khỏi `listColumns`), đổi `detailLayoutId`, **xuất bản lại** (bản đang chạy giữ field cũ tới khi xuất bản). Mẫu PDF (`documentTemplateIds`) có thể in field ngoài layout: rà cả mẫu. Không tự sửa cổng đang chạy khi người dùng chỉ yêu cầu khảo sát.

## Related list

- `GET objects/candidates/{objectSlug}?layoutId=<LAYOUT_ID>` → `relatedLists[]` có `selectable`, `reason` (`forbidden_child` = Object con nội bộ, không bật được), `onLayout` (có component trên layout), `columns`.
- Bật tường minh: `"relatedLists": [{"id": "<RELATED_LIST_ID>", "columns": []}]`. `columns: []` để máy chủ chốt theo cột của layout (đã kiểm: trả lại danh sách cột đã chốt). Related list chỉ hiện khi đồng thời được bật ở đây **và** có trên layout chi tiết.
- Lỗi/cảnh báo: `related_list_forbidden`, `related_list_skipped` (không phải dạng bảng), `related_list_columns_unset`, `related_list_column_removed`, `invalid_related_list_columns`.

## Điều kiện lọc `extraFilter`

Định dạng như saved filter (danh sách điều kiện + logic):

```json
{"filters": [
  {"field": "status", "op": "not in", "params": ["draft", "creating"], "fieldType": "single_choice"},
  {"field": "channel_source", "op": "in", "params": ["customer_portal"], "fieldType": "single_choice"}],
 "logic": "CUSTOM", "logicSequence": "1 OR 2"}
```

`logic`: `AND`, `OR` hoặc `CUSTOM` + `logicSequence`. `params` của lựa chọn là slug option (lấy bằng [$object-info](../../object-info/SKILL.md)). Không dùng biến người dùng hiện tại (`$currentUser`...) → `invalid_extra_filter`. `null` = không lọc thêm. Cùng định dạng dùng cho `ordering.productFilter`.

## Khách tạo bản ghi

```json
{"permissions": {"view": true, "create": true},
 "createFields": [{"field": "name", "required": true}, {"field": "description", "required": false}, {"field": "attachment_files", "required": false}],
 "createDefaults": {"status": "new"}}
```

- `createFields`: field `writable` trong `candidates.fields` (văn bản, số, ngày, lựa chọn, boolean, email, điện thoại, url, file); không field hệ thống, không `owner`, không field Tài khoản/Liên hệ, không formula/auto_number (`invalid_create_fields`).
- `createDefaults`: giá trị mặc định cho field lựa chọn, boolean, văn bản (slug option phải tồn tại).
- Máy chủ tự gán Tài khoản, Liên hệ của khách và `portal_created_by`; giá trị khách gửi cho các field này bị bỏ. Lần xuất bản đầu có quyền tạo, cổng thêm field `portal_created_by` (lookup Liên hệ) vào Object.
- **Cho khách đính kèm tệp**: preset `ticket` mặc định **không** có field tệp trong `createFields`. Lấy slug field `file` của Object từ `candidates.fields` (`type: "file"`, `writable: true`; bỏ field bắt đầu bằng `_`), ví dụ Object ticket chuẩn có `attachment_files`, rồi thêm `{"field": "attachment_files", "required": false}`. Giới hạn tệp lấy từ metadata của field đó bằng `$object-info` (`file_type`, `max_size` tính bằng byte, `multiple_limit.max`; vd field trên Object ticket chuẩn: tài liệu văn phòng/pdf/zip, 50 MB, tối đa 10 tệp, riêng tư); cổng còn có trần riêng: tối đa 5 tệp mỗi bản ghi và 25 MB mỗi tệp (trần này chưa được kiểm bằng tệp thật; báo người dùng thử một tệp lớn nếu nghiệp vụ cần). Field tệp cũng nên có trên layout chi tiết để khách xem lại tệp đã gửi.
- Field `file` trên layout/`createFields`: thiếu dung lượng tối đa → cảnh báo `file_max_size_missing`; field công khai → cảnh báo `file_field_public` (ai có link đều tải được: đổi field sang riêng tư bằng `$object-info`).

## Phạm vi thành viên

`"memberScope": "account"` (mặc định): mọi người của Tài khoản thấy mọi bản ghi. `"own"`: thành viên (`MEMBER`) chỉ thấy bản ghi "của mình", tức bản ghi có field Liên hệ `contactField` là chính Liên hệ của họ, hoặc bản ghi họ tạo trên cổng (`portal_created_by`). Bản ghi nhân viên tạo mà để trống `contactField` thì chỉ quản trị viên phía khách (`ADMIN`) thấy; `ADMIN` luôn thấy hết. `contactField` của từng preset: `quote`, `order`, `customer_invoice`, `ticket`, `balance_confirmation` → `contact`; `contract` → `customer_signed_by`. Nên nhắc người dùng: muốn thành viên thấy chứng từ của mình thì nhân viên phải điền field này khi tạo chứng từ. `own` cần `contactField` hợp lệ hoặc quyền tạo, không thì `member_scope_requires_owner_field` (đã kiểm). Bật kèm `team.enabled` để quản trị viên phía khách quản lý thành viên.

## Trao đổi trên bản ghi

`"conversation": {"enabled": true}` (cần `permissions.view`, không thì `conversation_requires_view`). Lần xuất bản đầu bật trao đổi tạo Object lưu tin và một field liên kết về Object này (không gắn vào App nào); gói hết chỗ Object → `schema_ensure_failed`. Khách gửi tin kèm tệp; nhân viên trả lời bằng khối "Trao đổi với khách" trên trang bản ghi của Web App hoặc API ([vận hành](customer-access-and-operations.md#trả-lời-trao-đổi-của-khách)). Khách chỉ thấy tin công khai.

## Mẫu in PDF

`"documentTemplateIds": ["<TEMPLATE_ID>"]`: mẫu tài liệu của chính Object (tạo/tra bằng [$document-template](../../document-template/SKILL.md)); khách có nút tải PDF cho từng mẫu. Mẫu có thể in field không có trên layout: chỉ chọn mẫu dành cho khách. Id không hợp lệ → `invalid_document_templates`.

## Hành động của khách

Cho khách đổi trạng thái chứng từ (chấp nhận/từ chối báo giá, xác nhận số dư):

```json
{"actions": [
  {"key": "accept", "label": {"vi-VN": "Chấp nhận", "en-US": "Accept"}, "statusField": "status",
   "from": ["sent"], "to": "approved", "requireReason": false, "requireOtp": true,
   "confirmText": {"vi-VN": "Bạn chấp nhận báo giá này?"}, "allowedRoles": ["ADMIN"]},
  {"key": "reject", "label": {"vi-VN": "Từ chối", "en-US": "Reject"}, "statusField": "status",
   "from": ["sent"], "to": "rejected", "requireReason": true, "reasonField": "<LONG_TEXT_FIELD>",
   "requireOtp": true, "allowedRoles": ["ADMIN", "MEMBER"]}]}
```

| Khoá | Quy tắc |
|---|---|
| `key` | Chữ thường/số/gạch dưới, duy nhất (`Accept!` → 422 `config.actions[0].key: invalid_format`; trùng → `duplicate`) |
| `statusField` | Field single choice có trên layout, không phải field do cổng ghi (`portal_*`) |
| `from` (≥ 1), `to` | Slug option của `statusField` |
| `requireReason` + `reasonField` | `requireReason: true` bắt buộc có `reasonField` (thiếu → 422 `config.actions[0].reasonField: required` khi lưu). `reasonField` là field văn bản (nên `long_text`) **có trên layout chi tiết**, không nằm trong `createFields`; không có trên layout → xuất bản 422 `invalid_actions` (`field: actions.<key>.reasonField`). Đã kiểm cả ba trường hợp |
| `requireOtp` | Vắng = `true`: khách phải nhập mã 6 số gửi tới email của mình (hạn 10 phút, dùng một lần) |
| `allowedRoles` | `["ADMIN"]` hoặc `["ADMIN","MEMBER"]` (rỗng → `invalid_option`); Liên hệ được gửi bản ghi (`contactField`) luôn thực hiện được |
| `visibleWhen` | Điều kiện hiện nút, cùng định dạng `extraFilter` (tuỳ chọn) |
| `confirmText` | Câu hỏi xác nhận vi/en |

- Object không có field phù hợp để lưu lý do (vd báo giá chỉ có field văn bản ngắn mang nghĩa khác): hỏi người dùng rồi chọn một trong hai: (1) bỏ lý do (`requireReason: false`); (2) tạo field `long_text` mới (vd "Lý do của khách") bằng `$object-info`, thêm field đó vào layout chi tiết dành cho khách, rồi đặt làm `reasonField`. Không mượn field có nghĩa khác (tên người nhận, địa chỉ...) để lưu lý do.
- ≤ 10 hành động/Object. Lần xuất bản đầu có hành động thêm `portal_action_by`, `portal_action_at` vào Object; nhật ký lưu người làm, IP, nội dung đã chấp nhận.
- Field trạng thái chưa có transition rule → cảnh báo `action_no_transition_rule` (cổng vẫn chỉ cho chuyển theo hành động đã khai). Muốn cả nhân viên cũng theo luồng này: [$object-transition-rule](../../object-transition-rule/SKILL.md).
- Nội dung chứng từ đổi sau khi khách mở trang → khách phải tải lại rồi bấm lại.

## Quy trình thêm một Object

1. `$object-info`: xác nhận Object có lookup `account` (và `contact`), các field và slug option sẽ dùng.
2. `GET objects/presets`; có preset phù hợp thì `POST objects {"objectSlug", "preset", "objectKey"}` (đọc `sortOrder` trả về: nếu trùng với Object hay mục menu đang có thì đặt lại bằng `PUT objects/{configId}` kèm `"sortOrder"`), không thì `POST objects {"objectSlug", "objectKey", "config": {label, accountField, contactField, permissions, listColumns}}`.
3. `GET objects/candidates/{slug}` → chọn layout có sẵn chỉ chứa field cho khách, hoặc tạo layout ẩn theo [quy trình an toàn](#chọn-layout-chi-tiết) → `GET ...?layoutId=` → chọn related list.
4. `PUT objects/{configId}` với **đủ** cấu hình (`object-update` của script tự gộp với `draft`).
5. `POST publish`, đọc `warnings`; mở `GET objects/{configId}` xem `published.viewFields` để chắc không có field nội bộ.
6. Bỏ Object: `DELETE objects/{configId}` → xuất bản → (tuỳ chọn) `DELETE` lần nữa để xoá dòng cấu hình.
