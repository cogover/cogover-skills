# Ghi hàng loạt, số thập phân và checkpoint

Đọc khi nghiệp vụ có preview/apply, ghi nhiều record, retry, nhiều request đồng thời hoặc ghi field mà backend khác cũng cập nhật. Contract nền tảng: [SDK API reference](cogover-sdk-api-reference.md), các mục Project state, Distributed locks, Record API, Background job và errors. Đây là hướng dẫn thiết kế ứng dụng, không phải cam kết transaction của nền tảng. "Job" trong mục preview/apply bên dưới là job nghiệp vụ của ứng dụng (snapshot có ID, checkpoint trong state), khác background job của SDK dùng để chạy việc nền.

## Số thập phân

- Đọc kiểu field, khả năng ghi, số chữ số thập phân và giới hạn từ metadata thật; không tự suy ra ý nghĩa một mã `round_rule` nếu tài liệu chưa định nghĩa.
- `fractional_length` không phải bằng chứng API tự làm tròn dữ liệu ghi: đã quan sát API giữ thêm chữ số ngoài độ chính xác hiển thị. Kiểm chứng bằng fixture và đọc lại; ứng dụng cần làm tròn thì công bố quy tắc nghiệp vụ cụ thể và áp dụng nhất quán ở backend trước khi ghi.
- Không kiểm tra số chữ số bằng phép so sánh chính xác như `Math.round(percent * 10000) === percent * 10000`: `0.07 * 10000` có thể thành `700.0000000000001`. Dùng kiểm tra biểu diễn decimal chuẩn hóa hoặc phép tính decimal/rational được môi trường hỗ trợ; quyết định rõ cách xử lý scientific notation.
- Kiểm thử phần trăm lẻ, phần trăm âm, biên min/max, số tại điểm nửa đơn vị làm tròn và tổng sau làm tròn từng dòng. Không cộng trực tiếp số thực rồi mặc định tổng bằng tổng các giá trị người dùng thấy.

## Preview và áp dụng một lần trong phạm vi job

1. Backend tạo snapshot có ID ổn định, chủ sở hữu lấy từ invocation, danh sách record, giá trị cũ/mới, dấu thời gian hoặc revision thực sự có và quy tắc tính. Validate lại quyền, số lượng, ID trùng và giới hạn giá trị; không tin snapshot hoặc danh tính gửi từ browser.
2. Project state có thể lưu job/checkpoint trong giới hạn 32 KiB mỗi giá trị. State tồn tại qua version mới nhưng không phải Object nghiệp vụ có sẵn quyền, báo cáo hay lịch sử record: tự kiểm tra quyền truy cập job; nghiệp vụ cần Object bền vững để báo cáo/quan hệ thì quay lại bước thiết kế schema và duyệt Excel.
3. Dùng `expectedVersion: 0` khi tạo mới và CAS version khi chuyển trạng thái. Lưu trạng thái đã nhận xử lý trước thao tác ghi đầu tiên; request lặp lại cùng job đọc trạng thái/kết quả, không tự bắt đầu lại phép tính.
4. Phạm vi lock bao phủ tài nguyên có thể xung đột, không chỉ mỗi job khi nhiều job cùng sửa record. Kiểm tra giới hạn số lock và lease theo SDK. `withLock` không tự renew: renew trước khi hết lease và dừng ghi nếu không còn giữ lease.
5. Đọc lại các record trước apply để từ chối preview cũ; ghi nhiều dòng thì kiểm tra lại từng dòng trước khi ghi. Ghi giá trị đích tuyệt đối đã duyệt, không nhân tiếp giá trị hiện tại khi retry.
6. Lưu checkpoint trước/sau mỗi side effect và đọc lại record. Phân biệt dòng đã xác minh thành công, chưa chạy, dữ liệu đã đổi và chưa rõ kết quả do lỗi ghi/read-back. Không biết request đã ghi hay chưa thì không tự retry ghi hoặc đánh dấu thành công.
7. UI hiển thị trạng thái toàn job và từng dòng, cho tra cứu lại bằng job ID sau refresh hoặc mất kết nối. Khóa nút khi pending chỉ hỗ trợ UX; backend vẫn phải kiểm soát request lặp.

CAS chỉ bảo vệ state; lock chỉ bảo vệ các execution tuân thủ cùng cơ chế trong phạm vi project; Record API và state không được gộp thành transaction. Đọc rồi ghi vẫn có khoảng đua với tác nhân khác; timestamp có độ phân giải hữu hạn không phải revision nguyên tử. Không tuyên bố chống mọi lost update hoặc exactly-once nếu đích không có conditional write/fencing tương ứng; người dùng yêu cầu bảo đảm mạnh hơn contract hỗ trợ thì báo giới hạn cụ thể.

## Khi local chạy được nhưng production dừng giữa chừng

Đã quan sát một luồng đọc/ghi/checkpoint tuần tự chạy được local nhưng production trả HTTP `422`, `body.r: 422` với thông báo `Script execution failed or exceeded its limits`, sau khi một phần record đã đổi. Thông báo này không phân biệt được lỗi script và vượt giới hạn thực thi; không suy đoán nguyên nhân gốc hoặc một con số timeout/quota chưa được tài liệu xác nhận. Lời gọi vượt ngân sách của lần thực thi (capability call, record đọc/ghi) là `RateLimitError` có `details.budget`, HTTP `429` khi không bắt, không phải `422` chung; để định vị, chạy preview với `showDebugData` và đọc `usage`, `operations`, `durationMs`, hoặc ghi `limits.usage()` vào log sau mỗi batch.

1. Giữ job ID, version và response đã loại credential; đọc checkpoint và record thật trước mọi quyết định retry. Invocation lỗi không chứng minh các side effect đã rollback. Execution bị ngắt trước cleanup thì lock có thể còn hiệu lực tới lúc lease hết hạn; không đổi namespace hoặc nới quyền để lách lock đang giữ.
2. Giảm roundtrip khi contract hỗ trợ: đọc nhiều record bằng `records.getMany` (tối đa 200 ID) hoặc `records.list` với filter và đúng phân trang, chỉ lấy `fields` cần dùng; dùng `records.batchUpdate` cho nhóm ghi thay vì đọc/ghi/checkpoint từng dòng không giới hạn. Giới hạn SDK 1–200 dòng mỗi batch không bảo đảm mọi batch hoàn tất trong một invocation; test kích thước thực tế của bài toán trên production.
3. Lưu CAS claim/checkpoint trước batch. Batch là best-effort: ánh xạ từng `results` bằng `referenceId` (index đầu vào dạng chuỗi), kiểm tra thành công từng dòng rồi batch read-back. Response HTTP thành công hoặc aggregate `success` không phải bằng chứng mọi giá trị đúng; không nhận được kết quả thì giữ trạng thái chưa xác minh, không tự gửi lại ghi.
4. Chia nhiều invocation thì lưu tiến độ bền vững và tiếp tục bằng background job (`@cogover/sdk` từ `0.8.0`, Workspace đã bật job): route kiểm tra input rồi `jobs.enqueue` và trả `202` với `runId`; mỗi run xử lý một trang (tối đa 200 record, sắp xếp ổn định) trong `timeoutMs` rồi `jobs.enqueue` chính nó với cursor và idempotency key `${job.id}:next`, có điều kiện dừng; handler idempotent vì run có thể chạy lại. Xem [Background job quick start](get-started-background-jobs.md). Không dựa vào timer trình duyệt cho công việc phải tự chạy. Nghiệp vụ định kỳ dùng `schedule` của job; luồng cần người tham gia, thông báo hoặc AI Agent quay lại bước Process. Workspace chưa bật job và không có cơ chế tiếp tục phù hợp thì báo phần chưa hoàn tất.
5. Publish bản sửa, xác nhận active version, chạy lại local và production cho apply/read-back, replay, concurrency, stale và browser. Chỉ ghi workaround thành công sau kiểm chứng; giữ sự cố version cũ trong báo cáo. Không thay đổi nghĩa atomicity hoặc exactly-once để che giới hạn nền tảng.

## Ghi số liệu do backend khác duy trì

Áp dụng khi module ghi field mà backend của App chuẩn hoặc hệ thống khác cũng cập nhật, ví dụ số tổng trên record tổng do cả hai bên cộng/trừ. Đo hành vi của backend đó trước theo bước 1 mục 6 của skill; mục này không thay việc đo. Mục 1–4 *đã sửa và chạy đúng* trên một module; mục 5 là khuyến nghị, chưa chạy; mục 6 là rủi ro chưa xử lý.

1. **Ghi delta trên field lưu sẵn.** Field tổng do backend cộng/trừ theo delta (không phải rollup/formula) thì module cũng ghi delta: đọc giá trị hiện tại ngay trước khi ghi rồi cộng đúng phần chênh module đã ghi vào record chi tiết. Không ghi giá trị tuyệt đối tính lại từ tổng record chi tiết: lệnh đó xoá luôn lệch có từ trước mà người dùng chưa quyết định và đè thay đổi backend vừa ghi (khác bước 5 của Preview, nơi field do chính ứng dụng quản lý). Field lưu sẵn không tự tính lại, nên module đổi record chi tiết thì tự ghi cả record tổng.
2. **Lấy khoá → đọc lại → tính → ghi.** Khoá theo thứ tự cố định (record chi tiết rồi record tổng) để không deadlock; mọi giá trị dùng để tính đọc **sau khi** giữ đủ khoá, dữ liệu đọc trước đó chỉ để biết cần khoá nào. Đọc lại thấy record không còn đủ điều kiện thì không ghi; lập lại kế hoạch ở lần chạy sau hoặc ném `RetryableError`. Lock chỉ chặn execution của project, không chặn backend của App: đọc sát lúc ghi chỉ thu hẹp cửa sổ va chạm, phần còn lại do đối soát (mục 5) phát hiện.
3. **Nhật ký nhiều bước.** Ghi hai record thì trước lệnh ghi đầu lưu state bằng CAS (ví dụ khoá `op:<recordId>` với `jobId`, `delta`, `stage: "pending"`), chuyển `detail_done` sau khi ghi record chi tiết và `done` sau khi ghi record tổng. Retry đọc nhật ký trước mọi quyết định, kể cả khi record chi tiết không còn thoả điều kiện chọn, để hoàn tất bước còn thiếu; `pending` không xác minh được đã ghi hay chưa thì dừng, log `error` và để đối soát hoặc xử lý tay, không tự lập kế hoạch rồi ghi chồng. Record tổng có field ghi chú phù hợp thì đưa job ID vào cùng lệnh ghi để retry phân biệt đã ghi hay chưa, thay vì so số có thể đã bị backend đổi tiếp.
4. **Vết trên record.** Nối dòng vết (thời điểm, giá trị cũ → mới, job ID) vào field ghi chú của record chi tiết trong cùng lệnh ghi, để kiểm thử và đối soát đối chiếu từng lần ghi với lần chạy job mà không phụ thuộc log.
5. **Đối soát và chạy bù (khuyến nghị).** After-change có thể không chạy và job có thể hết retry: route chỉ đọc dành cho Super Admin trả kế hoạch (giá trị hiện tại, giá trị đích, delta) và so record tổng với tổng record chi tiết; job theo lịch chạy lại phép tính idempotent (không đổi gì khi đã khớp) cho record thay đổi gần đây. Lệch có từ trước chỉ báo, không tự sửa; backfill dữ liệu cũ chỉ chạy sau khi người dùng duyệt kế hoạch.
6. **Rủi ro: before-change chặn, job ghi sau.** Before-change kiểm tra theo số đang lưu trên record tổng không thấy delta của job chưa chạy, nên hai thay đổi gần nhau trên cùng record tổng có thể cùng lọt. Ghi rõ là rủi ro chấp nhận, hoặc cộng phần đang chờ vào phép kiểm tra (chưa kiểm chứng).

Ví dụ minh họa mục 1–4, kiểu field lấy từ `workspace.d.ts` của Object giả định; đã typecheck với `@cogover/sdk` `0.15.0`:

```typescript
// Minh họa: Object `allocation` (chi tiết, lookup `pool`) và `pool` (tổng) là giả định.
import { defineJob, RetryableError, type CogoverRecordId } from "@cogover/sdk";

type Op = { jobId: string; delta: number; stage: "pending" | "detail_done" | "done" };

export const applyAllocation = defineJob<{ allocationId: string }>(
  { key: "apply_allocation", timeoutMs: 30_000, maxAttempts: 5 },
  async ({ payload, data, locks, state, job, log }) => {
    if (!payload?.allocationId) return;
    const sys = data.asSystem();
    const id = payload.allocationId as CogoverRecordId;
    // Đọc trước khi khoá chỉ để biết cần khoá record tổng nào.
    const hint = await sys.object("allocation").records.get(id, { fields: ["pool"] });
    const poolId = hint?.fields.pool?.id;
    if (!poolId) return;
    // Khoá theo thứ tự cố định: record chi tiết rồi record tổng.
    const a = await locks.acquire(`allocation:${id}`, { namespace: "alloc", waitMs: 5_000 });
    if (a === null) throw new RetryableError("Allocation is locked");
    try {
      const b = await locks.acquire(`pool:${poolId}`, { namespace: "alloc", waitMs: 5_000 });
      if (b === null) throw new RetryableError("Pool is locked");
      try {
        const ops = state.namespace("alloc");
        const prev = await ops.get<Op>(`op:${id}`);
        let op = prev?.value;
        let version = prev?.version ?? 0;
        if (op?.stage === "pending") {
          // Không biết lệnh ghi đầu đã chạy chưa: dừng, để đối soát hoặc xử lý tay.
          log.error("Unverified pending step", { allocationId: id, jobId: op.jobId });
          return;
        }
        if (op?.stage !== "detail_done") {
          // Đọc lại mọi input sau khi đã giữ đủ khoá, ngay trước khi ghi.
          const alloc = await sys.object("allocation").records.get(id, {
            fields: ["status", "amount", "target_amount", "pool", "notes"],
          });
          const f = alloc?.fields;
          if (!f || f.status !== "approved" || f.pool?.id !== poolId) return;
          const from = f.amount ?? 0;
          const to = f.target_amount ?? 0; // giá trị đích lấy từ record nguồn, không từ rollup vừa đổi
          if (to === from) return;
          op = { jobId: job.id, delta: to - from, stage: "pending" };
          version = (await ops.set(`op:${id}`, op, { expectedVersion: version })).version;
          await sys.object("allocation").records.update(id, {
            amount: to,
            notes: `${f.notes ?? ""}\n[${new Date().toISOString()}] ${from} -> ${to} (job ${job.id})`,
          });
          op = { ...op, stage: "detail_done" };
          version = (await ops.set(`op:${id}`, op, { expectedVersion: version })).version;
        }
        if (!op) return;
        // Ghi delta lên giá trị hiện tại của record tổng, không ghi giá trị tuyệt đối.
        const pool = await sys.object("pool").records.get(poolId, { fields: ["allocated_amount"] });
        await sys.object("pool").records.update(poolId, {
          allocated_amount: (pool?.fields.allocated_amount ?? 0) + op.delta,
        });
        await ops.set(`op:${id}`, { ...op, stage: "done" }, { expectedVersion: version });
      } finally {
        await b.release();
      }
    } finally {
      await a.release();
    }
  },
);
```

## Bằng chứng nghiệm thu

- Local và production: preview đúng phép tính; apply rồi đọc record thật; apply lặp cùng job không cộng dồn; hai request đồng thời cùng job không ghi trùng; sửa fixture sau preview rồi xác minh apply từ chối; tra cứu lại job sau refresh.
- Kiểm thử input ngoài phạm vi và quyền bằng fixture/caller được phép. Chỉ có một caller hoặc ít fixture thì báo giới hạn số lượng/danh tính đã test.
- Kiểm thử lỗi giữa chừng bằng dependency giả lập có kiểm soát nếu không có cách tạo lỗi thật an toàn; xác minh checkpoint và số lần gọi write khi replay. Ghi rõ đây là test mô phỏng; không gộp vào số ca production hoặc tuyên bố đã kiểm chứng lỗi hạ tầng thật.
- Ghi cả HTTP status và mã nghiệp vụ. Một response lock conflict có thể là hành vi đúng khi request khác đang chạy; phải đọc job và record sau đó để kết luận không ghi trùng.
