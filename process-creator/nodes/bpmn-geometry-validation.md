# Kiểm tra hình học đường nối BPMN

Đọc khi tạo/sửa `xmlString`, kiểm tra sơ đồ hoặc so sánh process trước–sau. Kết nối logic nằm ở `sequenceFlow.sourceRef/targetRef` và `incoming/outgoing`; đường nối hiển thị nằm ở `BPMNEdge/waypoint`. Logic đúng vẫn có thể hiển thị sai khi waypoint thuộc hàng hoặc node khác.

## Quy trình kiểm tra

1. Dựng một bảng node ID → bounds và danh sách flow ID → source/target. Chốt bố cục rồi tính tất cả waypoint từ bảng này, dùng cả chiều rộng/chiều cao thực tế.
2. Chạy [validator](../scripts/validate_bpmn_geometry.py) trên payload cuối trước khi gọi API tạo/cập nhật. Nếu lỗi, sửa bộ sinh waypoint/bố cục và chạy lại; không sửa `sourceRef/targetRef` để che lỗi đường vẽ.
3. Đọc lại process qua API và chạy validator lần nữa ở mode `response`. Giữ nguyên response gốc để đối chiếu. Không tự ghi lại process chỉ để chuẩn hóa namespace.
4. Chỉ kết luận phần kiểm tra này đạt khi exit code `0` và `ok: true`. Nếu còn lỗi trong bản đã lưu, báo rõ flow/node và xử lý theo phạm vi sửa được phép; không tự xóa/tạo lại process.
5. Kiểm tra riêng độ gọn và khả năng đọc theo mục dưới, trước khi gửi XML và sau khi mở lại bản đã lưu. Đây là kiểm tra bố cục/hiển thị; validator hiện chưa tự kiểm tra khoảng cách quá lớn hoặc nhãn chồng lấn.

## Bố cục gọn và khoảng trống cho nhãn

Ưu tiên nhánh ngắn gần gateway sở hữu nó, đồng thời giữ đủ khoảng trống để đọc và phân biệt từng đường nối. Các số dưới đây là điểm khởi đầu theo đơn vị tọa độ BPMN, không phải pixel sau zoom hoặc giới hạn cứng cho mọi sơ đồ.

1. **Tính vùng chiếm chỗ trước khi xếp hàng.** Dùng bounds thực tế của node và toàn bộ tên node, kể cả nhãn nhiều dòng. Chừa thêm khoảng đệm ban đầu khoảng 20–32 đơn vị quanh cụm node + nhãn để tách khỏi cụm khác; tính thêm bounds tên nhánh khi chọn tuyến. Ước lượng chiều rộng bằng số ký tự chỉ là bước đầu: kiểm tra chữ có dấu, xuống dòng và font khi hiển thị. Không cắt tên hay giảm cỡ chữ chỉ để sơ đồ nhỏ hơn.
2. **Bố trí từng nhánh theo gateway của nó.** Với node 60×60, có thể bắt đầu bằng bước ngang 160 và độ lệch hàng nhánh ngắn 160–200. Chọn hàng gần nhất còn đủ khoảng trống; tăng khoảng cách khi nhãn dài, nhánh lồng hoặc vật cản cần thêm chỗ. Không cấp hàng y tăng dần cho mọi gateway độc lập, và không áp một giới hạn độ dài edge cho đường quay lại hoặc nhánh dài hợp lệ.
3. **Tái sử dụng hàng có điều kiện.** Hai nhánh ngắn của các gateway khác nhau có thể nằm cùng hàng nếu vùng chiếm chỗ theo x không giao nhau, tính cả node, nhãn, đoạn nối và khoảng đệm. Nếu xung đột, thử tăng khoảng cách ngang, chọn phía trên/dưới khác hoặc thêm hàng cục bộ. Không ép các nhánh song song cùng vùng x hay nhánh lồng nhau về cùng hàng chỉ để giảm chiều cao.
4. **Chừa chỗ cho tên nhánh.** Đặt tên nhánh cạnh một đoạn nối dễ nhận diện, tránh góc rẽ, mũi tên, node và nhãn khác; đường nối không đi xuyên chữ. Với đường nối dọc đi xuống, tên gateway có thể đặt phía trên gateway hoặc lệch sang bên để không che đường. Nếu nhãn không vừa, tăng khoảng trống hoặc đổi tuyến rồi tính lại waypoint theo bounds mới.
5. **Tách các đường quay lại.** Khi nhiều edge quay về cùng node, chọn các tuyến ngoài cụm node với khoảng cách đủ cho nhãn để người đọc theo được từng nhánh. Có thể dùng chung đoạn cuối vào node đích nếu vẫn rõ hướng và nguồn; tránh chồng cả tuyến khiến hai nhánh trông như một.
6. **Kiểm tra cả tổng thể và cận cảnh.** Ở chế độ vừa màn hình, xem nhánh có bị đẩy xa bởi khoảng trắng không cần thiết hay không. Ở mức zoom đọc được chữ (ví dụ 100%), kiểm tra tên node/tên nhánh không chồng nhau, không bị cắt và không bị đường nối che. Với sơ đồ lớn, kiểm tra từng vùng; không yêu cầu mọi chữ đều đọc được khi thu nhỏ toàn sơ đồ. Đối chiếu lại sau khi lưu vì editor có thể sắp lại nhãn. Nếu chưa quan sát bản render, báo rõ chưa kiểm tra hiển thị; không dùng kết quả validator thay thế.

Ví dụ tổng hợp: hai gateway trên cùng luồng chính, cách nhau theo chiều ngang, mỗi gateway có một nhánh ngắn phía dưới. Thử đặt hai nhánh cùng hàng cách luồng chính khoảng 180 đơn vị. Nếu tên node dài khiến hai vùng chiếm chỗ giao nhau, nới ngang hoặc tách hàng cho đúng cụm bị xung đột; không tiếp tục tăng y cho tất cả nhánh về sau. Ví dụ này là hướng dẫn bố trí, không phải bằng chứng kiểm thử runtime.

## Sử dụng script

Yêu cầu Python 3.9+; chỉ dùng thư viện chuẩn. Chạy từ thư mục skill hoặc resolve đường dẫn script theo vị trí skill đã cài:

```bash
# Payload JSON hoặc XML được truyền qua stdin, không bắt buộc tạo file.
python3 scripts/validate_bpmn_geometry.py --mode request -

# Đọc một bản snapshot đã có, không ghi thay đổi vào file.
python3 scripts/validate_bpmn_geometry.py --mode response process.json
```

Có thể gọi ngay trong bộ sinh payload để tránh bỏ qua kết quả:

```python
check = subprocess.run(
    ["python3", str(skill_dir / "scripts/validate_bpmn_geometry.py"), "--mode", "request", "-"],
    input=json.dumps(payload), text=True, capture_output=True, check=False,
)
report = json.loads(check.stdout)
if check.returncode != 0 or not report["ok"]:
    raise ValueError(report["errors"])
# Chỉ tiếp tục gửi chính payload đã kiểm tra khi đạt.
```

Ví dụ Python giả định đã import `json`, `subprocess`, và `skill_dir` là đường dẫn skill được resolve trong môi trường hiện tại. Truyền JSON process, không truyền header xác thực/cookie. Script không gọi mạng, không tự chỉnh sửa XML và không in toàn bộ payload.

Input hỗ trợ XML trực tiếp, object có `xmlString`, hoặc response có `data`/`body` bọc ngoài. Output JSON gồm `ok`, `counts`, `errors`, `warnings`; mỗi lỗi có mã và ID liên quan. Dung sai mặc định `1px` dành cho làm tròn tọa độ; không tăng dung sai để che một edge lệch node.

- Mode `request`: yêu cầu prefix `bpmn2:` cho các phần tử BPMN chuẩn.
- Mode `response`: đọc theo namespace; nếu API trả alias `bpmn:` chưa khai báo, chỉ bổ sung declaration vào bản sao trong bộ nhớ và trả warning `RESPONSE_BPMN_ALIAS`. Đây không phải lý do tự sửa bản trên Workspace.

## Các lỗi validator phát hiện

| Mã | Ý nghĩa / cách sửa |
|---|---|
| `MISSING_DI`, `DUPLICATE_DI_REFERENCE`, `UNKNOWN_DI_REFERENCE` | Mỗi node phải có đúng một shape, mỗi flow đúng một edge theo `bpmnElement`; không chỉ so tổng số lượng |
| `DUPLICATE_ID`, `UNKNOWN_NODE_REFERENCE`, `FLOW_DECLARATION_MISMATCH` | Dùng bảng ID chung; đối chiếu đầy đủ và đúng chiều incoming/outgoing |
| `INVALID_BOUNDS`, `INVALID_WAYPOINTS`, `ZERO_LENGTH_SEGMENT` | Bounds phải hữu hạn và có kích thước dương; mỗi edge có ít nhất hai điểm hữu hạn, không có đoạn liên tiếp dài bằng 0 |
| `ENDPOINT_OFF_NODE` | Điểm đầu phải bám biên source, điểm cuối bám biên target; tâm gateway/event không phải điểm nối hợp lệ |
| `SEGMENT_THROUGH_NODE` | Chọn tuyến khác: một đoạn đang đi xuyên node, kể cả xuyên chính source/target do chọn sai cạnh |
| `INVALID_INPUT`, `REQUEST_BPMN_PREFIX`, `UNSUPPORTED_STRUCTURE`, `UNSUPPORTED_NODE` | Kiểm tra input/namespace/phạm vi hỗ trợ; không bỏ qua lỗi để gửi payload |

Geometry dùng hình thoi cho gateway, ellipse xấp xỉ 128 cạnh cho event, hình chữ nhật bounds cho task. Chạm biên không bị coi là đi xuyên node. Đường chéo hợp lệ được chấp nhận nếu bám đúng node và không xuyên node; không ép mọi edge phải cùng số waypoint.

## Ca hồi quy cần giữ

Dùng dữ liệu giả, ID/tên tổng quát; không chép snapshot Workspace vào sample public:

- Nhánh dưới: node ở hàng dưới nhưng waypoint vẫn dùng y của hàng chính → phải lỗi; tính lại theo tâm/cạnh node → đạt.
- Gateway → nhánh khác hàng: ra từ cạnh trên/dưới gateway, rẽ tới cạnh target; không xuất phát ở tâm gateway.
- Node → End Process cùng cột: nối dọc từ hai cạnh đối diện; không tạo đoạn ngang trong node End.
- Đường quay lại/loop: chọn cạnh/tuyến vòng đúng hướng, tránh đi xuyên các node giữa đường.
- Đủ số edge nhưng lặp `bpmnElement`, thiếu edge của flow khác → phải lỗi.

## Giới hạn

Validator dành cho một process phẳng với các node Cogover, bao gồm node gọi Sub Process; không hỗ trợ BPMN subprocess lồng diagram, lane hay nhiều process trong cùng XML. Nó không kiểm tra quyền, action data, điều kiện gateway, nội dung label, label chồng lấn, edge chồng lên edge hay kết quả runtime. Task dùng bounds chữ nhật nên vùng góc bo tròn cần kiểm tra trực quan nếu đặt cổng nối tại đó. Bố cục còn mơ hồ hoặc nhãn che đường nối vẫn cần được kiểm tra trước khi bàn giao; `ok: true` chỉ chứng minh các invariant được script kiểm tra.
