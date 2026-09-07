# Mô hình hóa Report Type và quan hệ object

## Mục lục

1. [Từ câu hỏi nghiệp vụ đến object graph](#từ-câu-hỏi-nghiệp-vụ-đến-object-graph)
2. [Chọn primary object](#chọn-primary-object)
3. [Chọn join và kiểm tra cardinality](#chọn-join-và-kiểm-tra-cardinality)
4. [Khám phá relation](#khám-phá-relation)
5. [Payload relation và metadata](#payload-relation-và-metadata)
6. [Section và report field](#section-và-report-field)
7. [Ví dụ một object](#ví-dụ-một-object)
8. [Ví dụ nhiều object](#ví-dụ-nhiều-object)

## Từ câu hỏi nghiệp vụ đến object graph

Tách yêu cầu thành:

| Thành phần | Câu hỏi cần trả lời |
|---|---|
| Population | Những record nào tạo thành tập gốc? |
| Dimension | Group theo field nào? |
| Metric | Count/sum/avg/min/max/median field nào? |
| Event | Điều gì tạo tử số hoặc trạng thái thành công? |
| Filter | Khoảng thời gian, trạng thái, owner hoặc điều kiện nào? |
| Grain | Một row đại diện record nào? |
| Output | Cần detail list, summary, pivot hay tỷ lệ? |

Chỉ thêm object khi field/record của object đó cần cho một hàng, dimension, metric hoặc filter. Luôn dùng `$object-info` để xác minh object ID, slug, field type, lookup/reference và related list thực tế.

## Chọn primary object

Chọn object đại diện population hoặc grain chính:

- “Khách hàng tiềm năng theo nguồn”: primary object là Lead.
- “Doanh thu theo đơn hàng”: primary object thường là Order.
- “Tỷ lệ Lead tạo thành Opportunity”: primary object thường là Lead nếu mẫu số là toàn bộ Lead.

Không chọn object chỉ vì nó có metric dễ aggregate. Primary object sai có thể loại record chưa match hoặc tạo duplicate trước khi group.

## Chọn join và kiểm tra cardinality

Mapping cố định của Report API:

- `relation_type: 1` — Inner Join: chỉ giữ record có match.
- `relation_type: 2` — Left Join: giữ toàn bộ record bên trái.

Chọn join theo semantics, không theo thói quen:

- Dùng Inner khi câu hỏi chỉ quan tâm record đã liên kết.
- Dùng Left khi cần cả record chưa liên kết, đặc biệt population/mẫu số của conversion.

Trước aggregate, kiểm tra cardinality:

| Quan hệ | Rủi ro |
|---|---|
| one-to-one | Count thường ổn nếu key không null |
| many-to-one | Record nguồn vẫn giữ grain nếu join đúng chiều |
| one-to-many | Record nguồn có thể bị nhân bản; count/sum có thể tăng sai |
| many-to-many | Cần đặc biệt cảnh giác; thường cần distinct/pre-aggregation |

Aggregate catalog hiện không nêu `count_distinct`. Với conversion one-to-many, không tính `count(opportunity) / count(lead)` rồi tuyên bố chính xác nếu lead bị lặp. Xác minh ràng buộc một-một, dùng field/snapshot đã precompute, hoặc báo giới hạn.

## Khám phá relation

Thực hiện theo thứ tự:

1. Gọi `$object-info` cho object ứng viên với fields, related lists và metadata.
2. Xác minh lookup/reference field nối hai object.
3. Gọi service `223` để lấy relation có thể dùng và `object_relation_id` thật khi dữ liệu từ `object-info` không cung cấp ID dạng relation.
4. Xác minh chiều source/destination theo response, không suy ra từ tên field.
5. Tách chiều vật lý của relation khỏi chiều cha–con trên graph. `src_object_id` luôn là object sở hữu lookup field; node cha có thể là source hoặc destination.
6. Tạo graph liên thông từ primary object, không cycle, tối đa 4 relation/5 object.

Không biến `RL...` related-list ID thành `OR...` relation ID. Không dùng ID quan hệ từ workspace mẫu ở workspace khác.

## Payload relation và metadata

Tạo Report Type bằng service `212` mà không gửi `meta_data`:

```json
{
  "report_type_name": "<REPORT_TYPE_NAME>",
  "report_type_slug": "<REPORT_TYPE_SLUG>",
  "primary_object": "<PRIMARY_OBJECT_ID>"
}
```

Không gửi `meta_data: "{}"` hoặc root graph ở `212`; tạo graph bằng service `202` sau khi Report Type đã tồn tại.

Sau `212`, luôn gọi service `202`. Với một object:

```json
{
  "report_id": "<REPORT_TYPE_ID>",
  "relations": [],
  "src_object_id": "<PRIMARY_OBJECT_ID>",
  "meta_data": "{\"nodes\":[{\"id\":\"<PRIMARY_OBJECT_ID>\",\"type\":\"nodeRoot\",\"position\":{\"x\":0,\"y\":0},\"data\":{\"title\":\"Đối tượng chính\",\"content\":\"<PRIMARY_OBJECT_DISPLAY_NAME>\"},\"selected\":false}],\"edges\":[],\"viewport\":{\"x\":0,\"y\":0,\"zoom\":1}}"
}
```

Lấy primary object display name từ `name` đã được object API trả về theo display context; chỉ dùng translation metadata làm fallback. Không tự dịch.

### Hướng lookup trong graph UI

Relation từ service `223` mô tả lookup vật lý:

```text
relation source.field -> relation destination.id
```

Graph UI cần thêm `lookup_type` và `source_name` để biết relation được gắn vào node cha theo chiều nào:

| Node cha trên graph | `lookup_type` | UI | Node con | Biểu thức |
|---|---:|---|---|---|
| relation source | `2` | Tra cứu từ `<source_name>` | relation destination | `source.field = destination.id` |
| relation destination | `1` | Tra cứu tới `<source_name>` | relation source | `source.field = destination.id` |

`source_name` là alias chữ cái của node cha theo thứ tự node trong graph: root là `A`, node tiếp theo là `B`, rồi `C`, `D`, `E`. Thiếu `lookup_type` có thể làm UI đảo chiều lookup, hiển thị sai object con và dựng sai biểu thức JOIN dù service `221` vẫn trả `src_object_id`/`dst_object_id` đúng.

Ví dụ chuỗi `Opportunity (A) -> Lead (B) -> Campaign (C)` dùng hai lookup từ node cha, nên cả hai edge có `lookup_type: 2`; `source_name` lần lượt là `A` và `B`.

### Payload nhiều object

Gửi toàn bộ relations và graph đầy đủ trong cùng lần gọi `202`:

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
  "meta_data": "<JSON_STRING_CỦA_GRAPH_ROOT_CHILD_EDGE>"
}
```

Không gửi literal placeholder trên. Dựng graph đầy đủ theo shape Public API dưới đây, serialize graph thành JSON string rồi dùng làm `meta_data`:

- Root node:
  - `id`: primary object ID.
  - `type`: `nodeRoot`.
  - `position`: `{x,y}`.
  - `data.title`, `data.content`.
- Child node:
  - `id`: unique node ID; ưu tiên UUID như UI.
  - `type`: `nodeHeader`.
  - `data.parent_object_id`, `data.current_object_id`, `data.relation_type`, `data.level`, `data.content`.
  - `parentId`: parent node ID.
  - `data.content`: `<OBJECT_DISPLAY_NAME> (<LOOKUP_FIELD_DISPLAY_NAME>)`.
  - Với node lồng từ level 2 trở lên, thêm `data.parent_id` bằng object ID của node cha để tương thích state UI.
- Edge:
  - `id`, `source`, `target`, `type: "customSmoothStep"`.
  - Ưu tiên `id` bằng child node ID như UI tạo tay; `source` là parent node ID, `target` là child node ID.
  - `data.src_object_id`, `data.dst_object_id`, `data.relation_type`, `data.object_relation_id`, `data.field_slug`.
  - Bắt buộc có `data.lookup_type` theo bảng hướng lookup và `data.source_name` là alias của parent node.
  - Có thể thêm `animated: false` để khớp state UI; không dùng key này để suy luận nghiệp vụ.
- Viewport: `{x,y,zoom}`.

Đặt `selected: false` cho node đã lưu. Không tự thêm `measured`, `dragging` hoặc kích thước runtime vào graph mới. Khi update graph hiện có, giữ mọi key chưa biết và chỉ thay đổi các key thuộc contract đã xác minh.

Graph parsed tối thiểu cho lookup từ A:

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

Trước mutation, chạy `scripts/report_api.py` ở chế độ dry-run. Validator phải chứng minh mỗi edge khớp đúng một relation, `source_name` khớp alias parent, và `lookup_type` khớp hướng parent/child. Sau `202`, đọc `215.meta_data` và `221`; tự dựng lại biểu thức UI cho từng edge để xác nhận `source.field = destination.id`. Không coi preview dữ liệu đúng là đủ vì execution engine và UI có thể đọc hai phần state khác nhau.

Không bỏ qua `202` khi không có relation: bước này khởi tạo Report Config cần cho các service field tiếp theo.

## Section và report field

Sau `202`, đọc service `211` và `222` trước khi tạo field. Dùng state backend trả về làm nguồn xác minh:

- Default section persisted với `section_index: 0` có sẵn sau create config; không gọi `208` để tái tạo section này.
- Khi cần section bổ sung, gọi `208` với `section_index: 1000` thay vì tự tính index persisted.
- `section_type: 1` cho section hiển thị; `0` cho ẩn.

Tái sử dụng default section cho field nghiệp vụ. Chỉ thêm section khi report contract thực sự cần phân nhóm field riêng.

Payload service `227`:

```json
{
  "report_type_id": "<REPORT_TYPE_ID>",
  "field": {
    "object_type_id": "<OBJECT_ID>",
    "field_name": "<DISPLAY_NAME>",
    "section_id": "<SECTION_ID>",
    "field_slug": "<OBJECT_FIELD_SLUG_OR_CONFIRMED_PATH>",
    "field_type": 0,
    "status": 0,
    "index_in_section": 0
  }
}
```

Quy tắc field:

- Field trực tiếp của primary hoặc related object: `field_type: 0`, `object_type_id` của object sở hữu field, slug trực tiếp.
- Field đi qua lookup path lồng nhau: `field_type: 1` và dotted `field_slug`; chỉ dùng path mà object metadata hoặc Public Report API đã trả về.
- `field_name`: dùng display `name` mà object API trả về; chỉ dùng translation metadata làm fallback, không tự dịch hoặc đổi nhãn.
- `field_data_type` là dữ liệu response, không thay thế discriminator `field_type` 0/1.
- Chỉ lấy object field active.
- Ghi lại mapping `{object_id, object_field_slug} → report_field_id` từ response `227`/service `222`.

Service `222` có thể trả field hệ thống như `workspace_id` và `object_type` sau `202`. Không biến chúng thành object field giả và không gọi `227` để tái tạo. Mặc định loại chúng khỏi display, group, filter và aggregate.

## Ví dụ một object

Yêu cầu: “Tạo báo cáo khách hàng tiềm năng theo nguồn”.

Phân tích:

- Primary object: Lead.
- Dimension: `lead_source`.
- Metric: count một field định danh Lead không null.
- Relation: không có.
- Group: report field tương ứng `lead_source`.
- Detail: tùy yêu cầu; không bắt buộc hiển thị mọi field.

Thứ tự:

```text
object-info → 215 kiểm tra trùng → 212 (không metadata) → 202 (relations [], src object, root metadata) →
211/222 lấy default state → 227 (source + record key chưa tồn tại) →
222 resolve report field IDs → 239 → 201 → 229 → 207 → 200
```

## Ví dụ nhiều object

Yêu cầu: “Chiến dịch marketing nào có tỷ lệ chuyển đổi Lead sang Opportunity cao nhất?”.

Phân tích ban đầu:

- Primary object: Lead nếu mẫu số là toàn bộ Lead.
- Dimension: campaign nguồn trên Lead.
- Event: Opportunity liên kết qua field/relationship đã xác minh.
- Join: thường cần Left Join để giữ Lead chưa chuyển đổi, nhưng phải xác nhận định nghĩa nghiệp vụ.
- Cardinality: kiểm tra một Lead có thể sinh nhiều Opportunity hay không.

Không dùng ngay công thức tỷ lệ nếu API không thể đếm distinct Lead. Trước mutation, chốt một trong các phương án:

1. Quan hệ thực tế một-một và count thông thường là đúng.
2. Workspace có field conversion/precomputed metric đáng tin cậy.
3. Dùng snapshot/object tổng hợp khác.
4. Báo rõ giới hạn và chỉ tạo report numerator/denominator riêng để kiểm chứng.
