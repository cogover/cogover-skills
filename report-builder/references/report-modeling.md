# Mô hình hóa Report Type và quan hệ object

## Chọn primary object

Primary object đại diện population hoặc grain chính: "khách hàng tiềm năng theo nguồn" → Lead; "doanh thu theo đơn hàng" → thường là Order; "tỷ lệ Lead tạo thành Opportunity" → Lead nếu mẫu số là toàn bộ Lead. Không chọn object chỉ vì nó có metric dễ aggregate: primary object sai có thể loại record chưa match hoặc tạo duplicate trước khi group. Chỉ thêm object khác khi field/record của nó cần cho một hàng, dimension, metric hoặc filter.

## Chọn join và kiểm tra cardinality

`relation_type: 1` là Inner Join, chỉ giữ record có match: dùng khi câu hỏi chỉ quan tâm record đã liên kết. `relation_type: 2` là Left Join, giữ toàn bộ record bên trái: dùng khi cần cả record chưa liên kết, đặc biệt population/mẫu số của conversion.

| Quan hệ | Rủi ro khi aggregate |
|---|---|
| one-to-one | Count thường ổn nếu key không null |
| many-to-one | Record nguồn vẫn giữ grain nếu join đúng chiều |
| one-to-many | Record nguồn có thể bị nhân bản; count/sum có thể tăng sai |
| many-to-many | Thường cần distinct/pre-aggregation |

Aggregate catalog không có `count_distinct`. Với conversion one-to-many, không tính `count(opportunity) / count(lead)` rồi tuyên bố chính xác nếu lead bị lặp. Trước mutation, chốt một phương án: quan hệ thực tế là một-một nên count thông thường đúng; workspace có field conversion/precomputed metric đáng tin cậy; dùng snapshot/object tổng hợp khác; hoặc báo rõ giới hạn và chỉ tạo report numerator/denominator riêng để kiểm chứng.

## Khám phá relation

1. Gọi `$object-info` cho object ứng viên (fields, related lists, metadata) và xác minh lookup/reference field nối hai object.
2. Gọi service `223` để lấy relation dùng được và `object_relation_id` thật khi `object-info` không cung cấp ID dạng relation. Không biến `RL...` related-list ID thành `OR...` relation ID; không dùng ID quan hệ từ workspace mẫu ở workspace khác.
3. Xác minh chiều source/destination theo response, không suy ra từ tên field. Tách chiều vật lý của relation khỏi chiều cha–con trên graph: `src_object_id` luôn là object sở hữu lookup field; node cha có thể là source hoặc destination.
4. Tạo graph liên thông từ primary object, không cycle, tối đa 4 relation/5 object.

## Hướng lookup trong graph UI

Relation từ service `223` mô tả lookup vật lý `relation source.field -> relation destination.id`. Graph UI cần thêm `lookup_type` và `source_name` trên mỗi edge để biết relation gắn vào node cha theo chiều nào:

| Node cha trên graph | `lookup_type` | UI | Node con | Biểu thức |
|---|---:|---|---|---|
| relation source | `2` | Tra cứu từ `<source_name>` | relation destination | `source.field = destination.id` |
| relation destination | `1` | Tra cứu tới `<source_name>` | relation source | `source.field = destination.id` |

`source_name` là alias chữ cái của node cha theo thứ tự node trong graph: root là `A`, tiếp theo `B`, `C`, `D`, `E`. Ví dụ chuỗi `Opportunity (A) -> Lead (B) -> Campaign (C)` dùng hai lookup từ node cha nên cả hai edge có `lookup_type: 2`, `source_name` lần lượt là `A` và `B`. Thiếu `lookup_type`, UI có thể đảo chiều lookup, hiển thị sai object con và dựng sai biểu thức JOIN dù service `221` vẫn trả `src_object_id`/`dst_object_id` đúng.

## Payload service 202

Service `212` không nhận `meta_data` hay root graph; graph tạo bằng `202` sau khi Report Type đã tồn tại. Payload `202` một object (`relations: []`, `src_object_id`, root graph trong `meta_data`): xem [Khởi tạo Report Config một object](api-contract.md#khởi-tạo-report-config-một-object-202); `data.content` của root là display `name` của primary object theo cùng quy tắc với `field_name`.

### Payload nhiều object

Gửi toàn bộ relation đã xác minh và graph đầy đủ trong cùng lần gọi `202`; `meta_data` là graph serialize thành JSON string, không gửi literal placeholder:

```json
{
  "report_id": "<REPORT_TYPE_ID>",
  "relations": [
    {
      "src_object_id": "<SOURCE_OBJECT_ID>",
      "dst_object_id": "<DESTINATION_OBJECT_ID>",
      "relation_type": 1,
      "object_relation_id": "<OBJECT_RELATION_ID>"
    }
  ],
  "meta_data": "<JSON string của graph bên dưới>"
}
```

Graph parsed tối thiểu cho một lookup từ `A`:

```json
{
  "nodes": [
    {
      "id": "<SOURCE_OBJECT_ID>",
      "type": "nodeRoot",
      "position": { "x": 0, "y": 0 },
      "data": { "title": "Đối tượng chính", "content": "<SOURCE_DISPLAY_NAME>" },
      "selected": false
    },
    {
      "id": "<CHILD_NODE_ID>",
      "type": "nodeHeader",
      "position": { "x": 0, "y": 260 },
      "data": {
        "parent_object_id": "<SOURCE_OBJECT_ID>",
        "current_object_id": "<DESTINATION_OBJECT_ID>",
        "relation_type": 1,
        "level": 1,
        "content": "<DESTINATION_DISPLAY_NAME> (<LOOKUP_FIELD_DISPLAY_NAME>)"
      },
      "parentId": "<SOURCE_OBJECT_ID>",
      "selected": false
    }
  ],
  "edges": [
    {
      "id": "<CHILD_NODE_ID>",
      "source": "<SOURCE_OBJECT_ID>",
      "target": "<CHILD_NODE_ID>",
      "type": "customSmoothStep",
      "animated": false,
      "data": {
        "src_object_id": "<SOURCE_OBJECT_ID>",
        "dst_object_id": "<DESTINATION_OBJECT_ID>",
        "relation_type": 1,
        "object_relation_id": "<OBJECT_RELATION_ID>",
        "field_slug": "<LOOKUP_FIELD_SLUG>",
        "lookup_type": 2,
        "source_name": "A"
      }
    }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 }
}
```

Quy tắc graph:

- Root node: `id` là primary object ID, `type: "nodeRoot"`, `position {x,y}`, `data.title`, `data.content`. Child node: `id` duy nhất (ưu tiên UUID như UI), `type: "nodeHeader"`, `parentId` là node cha, `data.parent_object_id`, `data.current_object_id`, `data.relation_type`, `data.level`, `data.content` dạng `<OBJECT_DISPLAY_NAME> (<LOOKUP_FIELD_DISPLAY_NAME>)`; node lồng từ level 2 trở lên thêm `data.parent_id` bằng object ID của node cha để tương thích state UI.
- Edge: `id` ưu tiên bằng child node ID như UI tạo tay; `source` là node cha, `target` là node con; `type: "customSmoothStep"`; `data` phải có `src_object_id`, `dst_object_id`, `relation_type`, `object_relation_id`, `field_slug`, `lookup_type` (theo bảng trên) và `source_name` (alias node cha). `animated: false` chỉ để khớp state UI, không dùng suy luận nghiệp vụ.
- Viewport `{x,y,zoom}`. `selected: false` cho node đã lưu. Không tự thêm `measured`, `dragging` hoặc kích thước runtime vào graph mới. Khi update graph hiện có, giữ mọi key chưa biết và chỉ đổi key thuộc contract đã xác minh.

Trước mutation, chạy `scripts/report_api.py` ở chế độ dry-run: validator phải chứng minh mỗi edge khớp đúng một relation, `source_name` khớp alias node cha và `lookup_type` khớp hướng parent/child. Sau `202`, đọc `215.meta_data` và `221`, tự dựng lại biểu thức UI cho từng edge để xác nhận `source.field = destination.id`; preview dữ liệu đúng chưa đủ vì execution engine và UI có thể đọc hai phần state khác nhau.

## Ví dụ

### Một object: "Tạo báo cáo khách hàng tiềm năng theo nguồn"

Primary object Lead; dimension `lead_source`; metric là count một field định danh Lead không null; không relation; group theo report field của `lead_source`; detail tùy yêu cầu, không bắt buộc hiển thị mọi field. Thứ tự service:

```text
object-info → 215 kiểm tra trùng → 212 (không meta_data) → 202 (relations [], src_object_id, root graph) →
211/222 lấy default state → 227 (lead_source + field định danh chưa tồn tại) → 222 resolve report field ID →
239 → 201 → 229 → 207 → 200
```

### Nhiều object: "Chiến dịch nào có tỷ lệ chuyển đổi Lead sang Opportunity cao nhất?"

Primary object Lead nếu mẫu số là toàn bộ Lead; dimension là campaign nguồn trên Lead; event là Opportunity liên kết qua field/relationship đã xác minh; join thường là Left để giữ Lead chưa chuyển đổi nhưng phải xác nhận định nghĩa nghiệp vụ; kiểm tra một Lead có thể sinh nhiều Opportunity hay không và chốt phương án ở [Chọn join và kiểm tra cardinality](#chọn-join-và-kiểm-tra-cardinality) trước mutation.
