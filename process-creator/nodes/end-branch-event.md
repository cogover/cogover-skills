# End Branch Event

Đọc file này khi một nhánh cần dừng mà không kết thúc toàn bộ process instance.

## Nhận diện

| Thuộc tính | End Branch | End Process |
|---|---|---|
| BPMN element | `bpmn2:endEvent` | `bpmn2:endEvent` |
| renderKey | `END_BRANCH_EVENT` | `END_EVENT` |
| Ý nghĩa | Kết thúc token/nhánh hiện tại | Kết thúc toàn process |

Hai node dùng cùng BPMN type; luôn giữ đúng `configEx:elementInfo.renderKey` để runtime phân biệt semantics.

## XML

```xml
<bpmn2:endEvent id="NO000000000102" name="End branch">
  <bpmn2:extensionElements>
    <configEx:elementInfo renderKey="END_BRANCH_EVENT" />
  </bpmn2:extensionElements>
  <bpmn2:incoming>FLFLOW00000001</bpmn2:incoming>
</bpmn2:endEvent>
```

Quy tắc:

- Chỉ khai báo incoming; không tạo outgoing.
- Tạo `BPMNShape` và `BPMNLabel` như End Process.
- Không thêm entry vào `actions`, `userTasks`, `loops` hoặc `gateWays` cho End Branch.
- Dùng End Branch khi các nhánh khác còn phải tiếp tục. Dùng End Process khi muốn terminate process instance.
- Đảm bảo mọi nhánh mở đều đi tới End Branch hoặc End Process hợp lệ.

Xem `samples/sample_end_branch.json` để thấy một parallel split có một nhánh kết thúc cục bộ và một nhánh đi tới End Process.
