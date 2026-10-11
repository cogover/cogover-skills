# Đọc record hiệu quả

Một route thường chỉ cần vài field của record, tên của record liên kết, hoặc một con số tổng trên nhiều record. Hướng dẫn này chỉ cách đọc đúng phần đó: mỗi lần đọc nêu rõ các field code dùng, record liên kết chỉ được đọc khi cần tên hoặc field của nó, và Cogover tự đếm, tính tổng bằng `records.aggregate` thay vì code đọc từng record rồi cộng lại. Ví dụ đọc hai Object chuẩn `opportunity` và `account`, không ghi dữ liệu nào.

Đọc hướng dẫn này khi bạn viết một lần đọc mới, khi nâng Project lên `@cogover/sdk` 0.13.0, khi một lookup trả về `name` rỗng, hoặc khi một route đọc nhiều record chỉ để đếm hay tính tổng.

## Chuẩn bị

- Cài Node.js 20 trở lên, Git, `curl` và `jq`.
- Dùng Workspace có hai Object chuẩn của Sales là `opportunity` và `account`, cùng vài opportunity liên kết với account, ở các giai đoạn khác nhau và có doanh thu dự kiến. Nếu chưa có, tạo ba hoặc bốn opportunity trong Cogover, ở ít nhất hai giai đoạn đang mở. Người dùng của bạn phải đọc được cả hai Object.
- Có quyền tạo, publish và activate Project.
- Chuẩn bị Project key để chạy local và Workspace API key để publish. Đây là hai khóa khác nhau. Ví dụ chỉ đọc dữ liệu nên Project key chỉ đọc là đủ.

Xem cách tạo Project trong [Bắt đầu với Custom Backend Module](get-started-custom-backend-module.md).

Ví dụ dùng các field sau:

| Object | Field | Loại | Dùng để |
|---|---|---|---|
| `opportunity` | `name` | Văn bản | Hiển thị |
| `opportunity` | `stage` | Lựa chọn đơn: `needs_analysis`, `proposal`, `negotiation`, `closed_won`, `closed_lost` | Lọc và nhóm |
| `opportunity` | `est_revenue` | Số thập phân | Tính tổng và sắp xếp |
| `opportunity` | `account` | Lookup tới `account` | Record liên kết |
| `opportunity` | `owner` | Lookup tới `personnel` | Record liên kết |
| `account` | `name`, `industry` | Văn bản, lựa chọn đơn | Field của record liên kết |

## Phần 1. Chỉ đọc field cần dùng

### 1. Tạo Project

Trong Cogover, mở **Custom Backend Module**, tạo Project tên `Records demo` với slug `records_demo`. Sao chép Project ID, rồi chạy:

```bash
git clone https://github.com/cogover/custom-backend-module-starter-project.git records-demo
cd records-demo
npm install --global @cogover/dev-cli@latest
npm install
npm install @cogover/sdk@latest
cogover-dev --version
npm ls @cogover/sdk typescript
cp cogover.example.json cogover.json
```

Dùng SDK từ 0.13.0 và TypeScript từ 5.0; starter đã cài sẵn phiên bản TypeScript phù hợp. SDK cũ hơn chưa có `expandLookups` và `records.aggregate`. Sửa `cogover.json` cho giống nội dung dưới đây, với hostname của Workspace (ví dụ `example.cogover.net`) và Project ID của bạn. Đặt `projectSlug` là `records_demo`: mọi URL trong tài liệu này dùng slug đó.

```json
{
  "version": 1,
  "runtimeUrl": "https://{WORKSPACE_DOMAIN}",
  "projectId": "{PROJECT_ID}",
  "projectSlug": "records_demo"
}
```

Tạo `.env` trong thư mục này với Workspace API key của bạn:

```dotenv
COGOVER_API_KEY={WORKSPACE_API_KEY}
```

Starter đã bỏ qua `.env` và `cogover.json` trong Git. Không đặt khóa trong source code. Chạy các lệnh còn lại từ thư mục này.

### 2. Sinh kiểu cho Workspace

Khi biết cấu trúc Object, TypeScript kiểm tra được slug field, giá trị option và các field mà một lần đọc trả về. Tải metadata của hai Object bằng Workspace API key, rồi sinh `src/workspace.d.ts`. Thay `{WORKSPACE_DOMAIN}`:

```bash
set -a; . ./.env; set +a
curl -sSf -X POST 'https://{WORKSPACE_DOMAIN}/bapi/v1/objects/list' \
  -H "Authorization: Bearer $COGOVER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"slugs":["opportunity","account"],"includeFields":true}' \
  -o objects.json \
  && npx cogover-generate-workspace-types objects.json src/workspace.d.ts \
  && rm objects.json
```

Lệnh đầu nạp `.env` vào shell; chỉ chạy lệnh này trong terminal của chính bạn. Trình sinh không in gì khi thành công, và lệnh cuối xóa `objects.json`, file chỉ dùng làm đầu vào của trình sinh. Khi tải thất bại, curl in HTTP status, ví dụ `curl: (22) The requested URL returned error: 401` với key sai, và không có gì được sinh; con số trong ngoặc tùy phiên bản curl. File sinh ra khai báo mọi field của hai Object. Một đoạn trích:

```typescript
declare module "@cogover/sdk" {
  interface WorkspaceObjects {
    // ...
    opportunity: {
      account: RecordReference<"account">;
      est_revenue: number | null;
      name: string;
      owner: RecordReference<"personnel"> | null;
      stage: "closed_won" | "negotiation" | "closed_lost" | "needs_analysis" | "proposal";
      // ...
    };
  }
}
```

Lookup là một `RecordReference` tới Object đích, lựa chọn là hợp của các slug option, và field không bắt buộc nhận thêm `null`. Sinh lại file khi Object thay đổi. File do SDK cũ hơn 0.13.0 sinh ra phải được sinh lại: file đó gán kiểu `any` cho field lookup, file và URL, làm mất các kiểm tra ở dưới.

### 3. Viết các route đọc

Tạo file `src/main.ts`:

```typescript
import { createRouter } from "@cogover/sdk";

const router = createRouter();
const ID_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;
const OPEN_STAGES = ["needs_analysis", "proposal", "negotiation"] as const;
const OPPORTUNITY_FIELDS = ["name", "stage", "est_revenue", "account"] as const;

router.get("/opportunities", async ({ data }) => {
  const opportunities = data.object("opportunity");
  const page = await opportunities.records.list({
    fields: OPPORTUNITY_FIELDS,
    where: opportunities.fields.stage.in(OPEN_STAGES),
    orderBy: [opportunities.fields.est_revenue.desc()],
    limit: 3,
  });
  return {
    total: page.total,
    opportunities: page.items.map(item => ({
      id: item.id,
      name: item.fields.name,
      stage: item.fields.stage,
      estRevenue: item.fields.est_revenue,
      account: item.fields.account,
    })),
  };
});

router.get("/opportunities/:opportunityId", async ({ data, request, response }) => {
  const opportunityId = request.params.opportunityId ?? "";
  if (!ID_PATTERN.test(opportunityId)) {
    return response.json({ error: "A valid opportunity id is required" }, { status: 400 });
  }
  const opportunity = await data.object("opportunity").records.get(opportunityId, {
    fields: OPPORTUNITY_FIELDS,
  });
  if (opportunity === null) {
    return response.json({ error: "Opportunity not found" }, { status: 404 });
  }
  return opportunity;
});

export default router.toHandler();
```

- `GET /opportunities` trả ba opportunity đang mở có doanh thu dự kiến lớn nhất, cùng số opportunity đang mở trong `total`.
- `GET /opportunities/:opportunityId` trả một opportunity đúng như SDK đọc được, để bạn thấy hình dạng của một record. ID không tồn tại cho `404`.

Mọi lời gọi `get`, `getMany` và `list` đều nêu `fields`, và record chỉ chứa các field đó. `fields` là danh sách slug field hoặc `"*"`, nghĩa là mọi field mà danh tính đang dùng được đọc. Chỉ dùng `"*"` khi code cần mọi field: với Object có nhiều field, một trang 200 record có thể vượt giới hạn 1 MiB của một lời gọi. `where` và `orderBy` dùng được field không nằm trong `fields`.

Kiểu kết quả đi theo `fields`, nên đọc một field không được yêu cầu sẽ không biên dịch được. Để thấy điều đó, trong callback `map` của `GET /opportunities`, thêm `probability: item.fields.probability,` ngay dưới dòng `estRevenue: item.fields.est_revenue,` rồi chạy:

```bash
npm run build
```

TypeScript từ chối dòng đó vì `probability` không nằm trong `OPPORTUNITY_FIELDS` (đã rút gọn):

```text
src/main.ts(23,32): error TS2339: Property 'probability' does not exist on type 'Readonly<Pick<{ ... }, "account" | ... 2 more ... | "est_revenue">>'.
```

Xóa dòng vừa thêm. Lần đọc thiếu `fields` cũng không biên dịch được (`Expected 2 arguments, but got 1` với `get` và `getMany`, `Property 'fields' is missing` với `list`). Code bỏ qua bước kiểm tra kiểu vẫn lỗi: SDK ném `ValidationError` với message `fields is required: pass field slugs or "*" (@cogover/sdk 0.13.0+)` trước khi gửi request, và Cogover từ chối lần đọc như vậy với cùng message.

### 4. Thử trên local

Đăng nhập bằng Project key khi CLI yêu cầu, rồi khởi động máy chủ local. `--allow-writes=false` mở session chỉ đọc; tùy chọn này bắt buộc với Project key chỉ đọc và đủ cho ví dụ này:

```bash
cogover-dev login --profile records_demo
cogover-dev doctor --profile records_demo
COGOVER_LOCAL_PORT=3100 cogover-dev run --profile records_demo --allow-writes=false -- npm run dev
```

Trên hệ thống không có kho lưu credential, như nhiều máy chủ Linux, `login` lưu Project key vào `.env` cạnh Workspace API key và thêm quy tắc bỏ qua vào `.gitignore`. Không đưa `.env` vào Git, và commit `.gitignore` đã được cập nhật.

Giữ terminal đó chạy. Mở terminal thứ hai và liệt kê các opportunity đang mở:

```bash
curl -s 'http://127.0.0.1:3100/api/v1/ts-projects/records_demo/opportunities' | jq
```

Kết quả mong đợi tương tự như sau. Các ví dụ trong tài liệu này lấy từ một Workspace có vài opportunity mẫu với tên bắt đầu bằng `RRE-`; tên, ID và số liệu của bạn sẽ khác, thứ tự key cũng có thể khác:

```json
{
  "total": 9,
  "opportunities": [
    {
      "id": "OPPXXXXXXXXXX01",
      "name": "RRE-Acme POS rollout",
      "stage": "proposal",
      "estRevenue": 120000000,
      "account": {
        "name": "",
        "id": "ACCXXXXXXXXXX01",
        "objectSlug": "account"
      }
    },
    {
      "id": "OPPXXXXXXXXXX02",
      "name": "RRE-Acme loyalty app",
      "stage": "negotiation",
      "estRevenue": 80000000,
      "account": {
        "name": "",
        "id": "ACCXXXXXXXXXX01",
        "objectSlug": "account"
      }
    },
    {
      "id": "OPPXXXXXXXXXX03",
      "name": "RRE-Blue River warehouse sensors",
      "stage": "proposal",
      "estRevenue": 60000000,
      "account": {
        "name": "",
        "id": "ACCXXXXXXXXXX02",
        "objectSlug": "account"
      }
    }
  ]
}
```

Sao chép `id` của opportunity đầu tiên; phần còn lại của tài liệu gọi giá trị này là `{OPPORTUNITY_ID}`. Đọc opportunity đó:

```bash
curl -s 'http://127.0.0.1:3100/api/v1/ts-projects/records_demo/opportunities/{OPPORTUNITY_ID}' | jq
```

```json
{
  "system": {
    "createdAt": 1790659225126,
    "createdBy": {
      "name": "",
      "id": "PERXXXXXXXXXXXX"
    },
    "updatedAt": 1790659923000
  },
  "id": "OPPXXXXXXXXXX01",
  "fields": {
    "stage": "proposal",
    "name": "RRE-Acme POS rollout",
    "est_revenue": 120000000,
    "account": {
      "name": "",
      "id": "ACCXXXXXXXXXX01",
      "objectSlug": "account"
    }
  }
}
```

`fields` chỉ chứa bốn field đã yêu cầu. `name` của account rỗng, `name` của `system.createdBy` cũng vậy: một lần đọc không tra các record mà lookup trỏ tới, trừ khi yêu cầu. Lookup nhiều giá trị cũng vậy, đó là mảng các giá trị như trên. Field `reference` thì khác: tên được lưu kèm trong record nên vẫn còn `name`. Phần 2 đọc các record liên kết.

Máy chủ local đọc dữ liệu thật của Workspace qua Development Session, dưới danh tính nhân sự được cấp Project key. Bước thử này chưa cần version đã publish.

## Phần 2. Đọc record liên kết

### 5. Mở rộng account của từng opportunity

Danh sách cần tên và ngành của từng account. Trong route `GET /opportunities`, thêm dòng `expandLookups` vào tùy chọn của `records.list`, để lời gọi thành:

```typescript
  const page = await opportunities.records.list({
    fields: OPPORTUNITY_FIELDS,
    expandLookups: { account: ["industry"] },
    where: opportunities.fields.stage.in(OPEN_STAGES),
    orderBy: [opportunities.fields.est_revenue.desc()],
    limit: 3,
  });
```

Máy chủ local tự khởi động lại khi bạn lưu `src/main.ts`. Liệt kê lại các opportunity:

```bash
curl -s 'http://127.0.0.1:3100/api/v1/ts-projects/records_demo/opportunities' | jq '.opportunities[0]'
```

```json
{
  "id": "OPPXXXXXXXXXX01",
  "name": "RRE-Acme POS rollout",
  "stage": "proposal",
  "estRevenue": 120000000,
  "account": {
    "name": "RRE-Acme Retail",
    "id": "ACCXXXXXXXXXX01",
    "objectSlug": "account",
    "fields": {
      "industry": "retail"
    }
  }
}
```

Giá trị đã mở rộng có `name` của record liên kết và object `fields` gồm các field được liệt kê cho nó. Mỗi key của `expandLookups` phải là field lookup hoặc `reference` cũng nằm trong `fields`, và giá trị là danh sách slug field của Object liên kết hoặc `"*"`. Với kiểu đã sinh, key không phải lookup đã chọn, hay slug mà Object liên kết không có, đều là lỗi biên dịch. Muốn chỉ đọc tên, liệt kê `["name"]`.

Lần đọc vẫn là một lời gọi, nhưng Cogover đọc thêm từng Object liên kết, việc này tốn thời gian. Chỉ mở rộng những lookup mà code dùng tên hoặc field.

### 6. Mở rộng mọi lookup với `true`

Thêm route sau vào `src/main.ts`, ngay trên dòng `export default router.toHandler();`:

```typescript
router.get("/opportunities/:opportunityId/summary", async ({ data, org, request, response }) => {
  const opportunityId = request.params.opportunityId ?? "";
  if (!ID_PATTERN.test(opportunityId)) {
    return response.json({ error: "A valid opportunity id is required" }, { status: 400 });
  }
  const opportunity = await data.object("opportunity").records.get(opportunityId, {
    fields: ["name", "account", "owner"],
    expandLookups: true,
  });
  if (opportunity === null) {
    return response.json({ error: "Opportunity not found" }, { status: 404 });
  }
  const { account, owner } = opportunity.fields;
  const createdBy = opportunity.system.createdBy;
  const creator = createdBy === undefined
    ? null
    : await org.personnel.get(createdBy.id, { withDisplay: true });
  return {
    name: opportunity.fields.name,
    account: {
      name: account.name,
      industry: account.fields?.industry ?? null,
      fieldsRead: Object.keys(account.fields ?? {}).length,
    },
    owner: owner?.name ?? null,
    createdBy: {
      name: createdBy?.name ?? null,
      displayName: creator?.display?.name ?? null,
    },
  };
});
```

`expandLookups: true` mở rộng mọi field lookup và `reference` trong các field trả về, ở đây là `account` và `owner`, mỗi field lấy mọi field được phép đọc của record liên kết. Gọi route:

```bash
curl -s 'http://127.0.0.1:3100/api/v1/ts-projects/records_demo/opportunities/{OPPORTUNITY_ID}/summary' | jq
```

```json
{
  "name": "RRE-Acme POS rollout",
  "account": {
    "name": "RRE-Acme Retail",
    "industry": "retail",
    "fieldsRead": 26
  },
  "owner": "PERSONNEL-0000000002-13/09/2026",
  "createdBy": {
    "name": "PERSONNEL-0000000002-13/09/2026",
    "displayName": "An Nguyen"
  }
}
```

- `fieldsRead` cho thấy chi phí của `true`: route chỉ dùng một field của account nhưng đã đọc 26 field. Nên dùng danh sách field khi bạn biết code dùng field nào.
- Khi có `expandLookups` ở bất kỳ dạng nào, `system.createdBy.name` cũng được điền.
- Tên của nhân sự, trong lookup như `owner` hay trong `createdBy`, là field `name` của record nhân sự. Ở nhiều Workspace, field này chứa mã tự sinh như trên. Để có tên hiển thị cho người xem, dùng `org.personnel.get` hoặc `getMany` với `withDisplay: true`, như route làm với người tạo.

Record liên kết được đọc bằng cùng danh tính với lần đọc chính: người gọi, `data.asUser()` hoặc `data.asSystem()`, với cùng quyền:

- Record liên kết mà danh tính không đọc được, hoặc đã bị xóa, giữ nguyên dạng chưa mở rộng: `{ id, name: "", objectSlug }`, không có `fields`.
- Với `data.asUser()` hoặc `data.asSystem()`, identity policy của Project còn phải cấp quyền cho Object liên kết. Với `true` hoặc `"*"`, Object liên kết mà policy không cấp quyền giữ nguyên dạng chưa mở rộng. Với danh sách field, lần đọc ném `PermissionDeniedError`; `details.objectSlug` là Object liên kết, và `details.fieldSlug` là field khi một field không được cấp quyền.
- Chỉ mở rộng một cấp: lookup bên trong `fields` của record liên kết không được mở rộng.
- Mỗi lời gọi mở rộng tối đa 1.000 record liên kết khác nhau; vượt quá sẽ ném `ValidationError` và không đọc gì. Kết quả, kể cả record liên kết, phải nằm trong 1 MiB.

## Phần 3. Đếm và tính tổng bằng `records.aggregate`

### 7. Thêm các route aggregate

Con số tổng trên nhiều record không cần đọc các record đó. `records.aggregate` đếm, tính tổng, trung bình, tìm giá trị nhỏ nhất và lớn nhất của các record khớp `where`, trong một lời gọi, có thể chia theo nhóm.

Thay dòng đầu tiên của `src/main.ts` bằng:

```typescript
import { createRouter, ValidationError, type ResponseApi } from "@cogover/sdk";
```

Sau đó thêm đoạn sau ngay trên dòng `export default router.toHandler();`:

```typescript
// Answers HTTP 400 with the reason when Cogover refuses the options of a call.
async function explainRefusal<T>(response: ResponseApi, run: () => Promise<T>) {
  try {
    return await run();
  } catch (error) {
    if (error instanceof ValidationError) {
      return response.json({ error: error.message }, { status: 400 });
    }
    throw error;
  }
}

router.get("/pipeline", async ({ data }) => {
  const opportunities = data.object("opportunity");
  const result = await opportunities.records.aggregate({
    where: opportunities.fields.stage.in(OPEN_STAGES),
    metrics: {
      opportunities: { count: "id" },
      revenue: { sum: "est_revenue" },
      averageRevenue: { avg: "est_revenue" },
      largestRevenue: { max: "est_revenue" },
    },
  });
  return result.values;
});

router.get("/pipeline/by-stage", ({ data, response }) => explainRefusal(response, async () => {
  const result = await data.object("opportunity").records.aggregate({
    groupBy: ["stage"],
    metrics: {
      opportunities: { count: "id" },
      revenue: { sum: "est_revenue" },
      accounts: { countDistinct: "account" },
    },
  });
  return {
    stages: result.groups.map(group => ({ stage: group.key.stage, ...group.values })),
    truncated: result.truncated,
  };
}));

router.get("/pipeline/top-accounts", ({ data, response }) => explainRefusal(response, async () => {
  const opportunities = data.object("opportunity");
  const result = await opportunities.records.aggregate({
    where: opportunities.fields.stage.in(OPEN_STAGES),
    groupBy: ["account"],
    metrics: {
      opportunities: { count: "id" },
      revenue: { sum: "est_revenue" },
    },
    limit: 2,
  });
  const accountIds = result.groups.map(group => group.key.account);
  const { records } = await data.object("account").records.getMany(accountIds, {
    fields: ["name"],
  });
  const nameById = new Map(records.map(record => [record.id, record.fields.name]));
  return {
    accounts: result.groups.map(group => ({
      id: group.key.account,
      name: nameById.get(group.key.account) ?? null,
      ...group.values,
    })),
    truncated: result.truncated,
  };
}));
```

- `GET /pipeline` trả số opportunity đang mở, tổng và trung bình doanh thu dự kiến của chúng, cùng giá trị lớn nhất. Không có `groupBy`, kết quả là `{ values }` với một giá trị cho mỗi tên metric.
- `GET /pipeline/by-stage` nhóm mọi opportunity theo giai đoạn và đếm thêm số account khác nhau trong mỗi giai đoạn.
- `GET /pipeline/top-accounts` nhóm các opportunity đang mở theo account. `limit: 2` giữ hai nhóm có nhiều record nhất, và `truncated` cho biết còn nhóm khác hay không. Key nhóm của lookup là ID record, nên route đọc tên account bằng một lần `getMany` field `name`.
- `explainRefusal` chuyển `ValidationError` thành HTTP `400` kèm message của lỗi. Không có hàm này, người gọi chỉ nhận message `VALIDATION_ERROR` chung. Bước tiếp theo dùng đến nó.

Tên metric, như `revenue`, do bạn đặt; kết quả dùng đúng các tên đó và TypeScript biết kiểu của chúng.

### 8. Thử trên local: tổng chạy được, nhóm bị từ chối

Đọc các con số tổng của pipeline:

```bash
curl -s 'http://127.0.0.1:3100/api/v1/ts-projects/records_demo/pipeline' | jq
```

```json
{
  "revenue": 355000000,
  "averageRevenue": 39444444.44444445,
  "largestRevenue": 120000000,
  "opportunities": 9
}
```

Giờ yêu cầu số liệu theo giai đoạn:

```bash
curl -s -i 'http://127.0.0.1:3100/api/v1/ts-projects/records_demo/pipeline/by-stage'
```

Máy chủ local trả HTTP `400`:

```json
{"error":"aggregate with groupBy is not supported for the default identity of this invocation, which reads as a delegated user; use asSystem()"}
```

Đây là kết quả mong đợi. Máy chủ local đọc dưới danh tính nhân sự của Project key, thay mặt người dùng đó, chứ không phải một người gọi HTTP. Với danh tính như vậy, `records.aggregate` không nhóm được, và metric chỉ gồm `count` trên `"id"` cùng `count`, `sum`, `avg`, `min`, `max` trên field số. `/pipeline` nằm trong giới hạn này; `countDistinct`, hay `min` và `max` trên field ngày, bị từ chối với message bắt đầu bằng `metrics.<name>:`. `/pipeline/top-accounts` bị từ chối cùng lý do. Bước 9 chạy phần nhóm trên version đã publish, nơi người gọi là người đọc.

Muốn nhóm trước khi publish, route có thể dùng `data.asSystem().object("opportunity")` thay thế. Cách này cần identity policy cấp quyền đọc `opportunity` qua `data.asSystem()` và đang `ACTIVE`, cùng Project key cho phép `asSystem`; khởi động lại `cogover-dev run` sau khi đổi policy. Quyền hệ thống đếm mọi record, bất kể người gọi được xem gì, nên chỉ dùng cho những con số mà mọi người gọi đều được biết.

### 9. Publish và gọi phần nhóm

Nhấn Ctrl+C để dừng máy chủ local. Tại thư mục dự án, chạy:

```bash
npm run build
cogover-dev publish
```

`publish` upload `src/`, chờ tới khi version ở trạng thái `READY`, rồi in số thứ tự và ID của version:

```text
Published version 8 (TSVXXXXXXXXXXXX) is READY.
Next: cogover-dev activate TSVXXXXXXXXXXXX
```

Số thứ tự đếm các version của Project, nên lần publish đầu tiên của bạn in version 1. Activate bằng version ID vừa được in ra:

```bash
cogover-dev activate {VERSION_ID}
```

```text
Activated version TSVXXXXXXXXXXXX.
```

Các route đọc dưới danh tính người gọi nên Project không cần identity policy cho ví dụ này.

Tạo file Workspace session bằng CLI, rồi gọi số liệu theo giai đoạn trên version đang active. CLI không bao giờ ghi đè file đã có, nên hãy xóa `.cogover-session.curl` cũ trước, ví dụ khi session đã hết hạn. Thay `{WORKSPACE_DOMAIN}`:

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
curl -s --config .cogover-session.curl \
  'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/records_demo/pipeline/by-stage' \
  -H 'x-req-type: 9' -H 'x-req-service: 3' | jq
```

```json
{
  "stages": [
    {
      "stage": "proposal",
      "revenue": 230000000,
      "accounts": 4,
      "opportunities": 4
    },
    {
      "stage": "needs_analysis",
      "revenue": 45000000,
      "accounts": 3,
      "opportunities": 3
    },
    {
      "stage": "negotiation",
      "revenue": 80000000,
      "accounts": 2,
      "opportunities": 2
    },
    {
      "stage": "closed_lost",
      "revenue": 30000000,
      "accounts": 1,
      "opportunities": 1
    },
    {
      "stage": "closed_won",
      "revenue": 150000000,
      "accounts": 1,
      "opportunities": 1
    }
  ],
  "truncated": false
}
```

Nhóm có nhiều record nhất đứng trước. Key của field lựa chọn là slug của option. Session thuộc về người dùng của Workspace API key, và chỉ những record người dùng đó xem được mới được đếm.

Gọi danh sách account dẫn đầu:

```bash
curl -s --config .cogover-session.curl \
  'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/records_demo/pipeline/top-accounts' \
  -H 'x-req-type: 9' -H 'x-req-service: 3' | jq
```

```json
{
  "accounts": [
    {
      "id": "ACCXXXXXXXXXX01",
      "name": "RRE-Acme Retail",
      "revenue": 200000000,
      "opportunities": 2
    },
    {
      "id": "ACCXXXXXXXXXX02",
      "name": "RRE-Blue River Logistics",
      "revenue": 105000000,
      "opportunities": 2
    }
  ],
  "truncated": true
}
```

`truncated: true` nghĩa là số account có opportunity đang mở nhiều hơn hai account được trả về.

Gọi các con số tổng trên version đã publish:

```bash
curl -s --config .cogover-session.curl \
  'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/records_demo/pipeline' \
  -H 'x-req-type: 9' -H 'x-req-service: 3' | jq
```

```json
{
  "revenue": 355000000,
  "averageRevenue": 39444444.44444445,
  "largestRevenue": 120000000,
  "opportunities": 9
}
```

Các con số giống ở bước 8. Aggregate theo sau thao tác ghi record một khoảng ngắn, thường khoảng một giây, nên opportunity vừa lưu có thể chưa được đếm.

### 10. Dọn dữ liệu thử

Xóa file session khi thử xong:

```bash
rm -f .cogover-session.curl
```

Khi không còn làm việc với Project này trên máy này, xóa luôn Project key đã lưu và Workspace API key trong `.env`:

```bash
cogover-dev logout --profile records_demo
cogover-dev auth logout
```

Ví dụ không ghi dữ liệu nào. Deactivate Project trong Cogover nếu không cần dùng nữa.

## Metric và nhóm

`metrics` gồm 1 đến 20 metric. Tên metric bắt đầu bằng chữ cái và dài tối đa 64 ký tự gồm chữ, số hoặc dấu gạch dưới. Mỗi metric là một trong các dạng:

| Metric | Field | Giá trị | Khi không record nào khớp |
|---|---|---|---|
| `{ count: "id" }` | | Số record khớp | `0` |
| `{ count: field }` | Field số, ngày, lựa chọn, `boolean`, `lookup_normal`, text, `email`, `phone` và `auto_number`; không nhận `reference`, `file`, `url`, `formula` và `rollup_summary` | Số record khớp có giá trị ở field | `0` |
| `{ countDistinct: field }` | Các field mà `count` nhận | Số giá trị khác nhau; xấp xỉ với tập lớn | `0` |
| `{ sum: field }` | `numeric`, `decimal`, `currency`, `percent` | Tổng | `0` |
| `{ avg: field }` | Các loại số ở trên | Trung bình | `null` |
| `{ min: field }`, `{ max: field }` | Các loại số ở trên, `date`, `date_time` | Giá trị nhỏ nhất hoặc lớn nhất; epoch mili giây với field ngày | `null` |

`avg`, `min` và `max` cũng bằng `null` khi không record khớp nào có giá trị ở field.

`groupBy` gồm 1 đến 3 field thuộc loại `single_choice`, `multi_choices`, `radio_button`, `checkbox`, `boolean`, `lookup_normal`, `date`, `date_time`, `numeric`, `decimal`, `currency` hoặc `percent`. Nhóm theo field văn bản hoặc `reference` bị từ chối, ví dụ với `groupBy does not support field 'name' of type short_text`. Key là ID record với lookup, slug của option với lựa chọn, `true` hoặc `false`, một số, hoặc epoch mili giây với field ngày. Record không có giá trị ở một field `groupBy` không thuộc nhóm nào. `limit`, chỉ dùng cùng `groupBy`, từ 1 đến 5.000 nhóm, mặc định 1.000.

Chỉ những record mà danh tính đang dùng xem được mới được đếm. Với `data.asUser()` hoặc `data.asSystem()`, identity policy của Project còn phải cấp quyền cho Object và mọi field trong `where`, `groupBy` và `metrics`, trừ `"id"`. `records.aggregate` đếm từ chỉ mục tìm kiếm, không từ chính các record: không dùng cho quy tắc cần giá trị chính xác ngay lúc ghi, như tồn kho hay số thứ tự.

## Nơi `records.aggregate` nhóm được

`data.object()` đọc dưới danh tính của lần chạy. `records.aggregate` có đủ mọi metric và `groupBy` chỉ khi danh tính đó là người gọi HTTP hoặc hệ thống:

| Nơi code chạy | `data.object()` đọc dưới danh tính | `groupBy` và mọi metric |
|---|---|---|
| Version đã publish được gọi bằng Workspace session, hoặc Preview | Người gọi | Có |
| Development Session trên local (`cogover-dev run`) | Nhân sự của Project key | Không |
| Record trigger cho thay đổi do người dùng thực hiện | Người dùng đó | Không |
| Lần chạy background job có người dùng, ví dụ job do quản trị viên enqueue | Người dùng đó | Không |
| Lần chạy không có người dùng, ví dụ job theo lịch, khi policy đã duyệt đặt `allowInternalSystem: true` | Hệ thống | Có |
| `data.asUser(personnelId)` | Nhân sự đó | Không |
| `data.asSystem()`, khi policy đã duyệt cấp quyền | Hệ thống | Có |

"Không" nghĩa là chỉ có `count` trên `"id"` cùng `count`, `sum`, `avg`, `min` và `max` trên field số. `groupBy` ném `ValidationError`: `aggregate with groupBy is not supported for asUser(); use the caller or asSystem()` với `data.asUser()`, và message ở bước 8 với các danh tính còn lại. Ở nơi không nhóm được, gọi `data.asSystem()` khi policy cho phép, hoặc chuyển phần tổng theo nhóm sang một route HTTP.

## Đọc dữ liệu trong record trigger

Giá trị `new` và `old` mà record trigger nhận được đã có tên của lookup, nên trigger không cần `expandLookups` để hiển thị tên. Các lần đọc qua `data` trong trigger theo đúng quy tắc của tài liệu này: phải nêu `fields`, và lookup có `name: ""` nếu không được mở rộng.

Ví dụ, trigger before-change sau từ chối opportunity có doanh thu dự kiến lớn hơn doanh thu năm của account. Trigger đọc một field của mọi account bằng một lần `getMany`, và lấy tên account từ `record.new`:

```typescript
import { defineTrigger } from "@cogover/sdk";

export const triggers = [
  defineTrigger({
    key: "revenue_within_account",
    object: "opportunity",
    timing: "beforeChange",
    operations: ["create", "update"],
    fields: ["account", "est_revenue"],
    changedFields: ["account", "est_revenue"],
  }, async ({ records, data }) => {
    const accountIds = records.flatMap(record => {
      const account = record.new.account;
      return typeof account === "object" && account !== null ? [account.id] : [];
    });
    const { records: accounts } = await data.object("account").records.getMany(accountIds, {
      fields: ["annual_revenue"],
    });
    const annualRevenue = new Map(accounts.map(account => [account.id, account.fields.annual_revenue]));
    for (const record of records) {
      const { account, est_revenue: estRevenue } = record.new;
      if (typeof account !== "object" || account === null || typeof estRevenue !== "number") continue;
      const limit = annualRevenue.get(account.id);
      if (typeof limit === "number" && estRevenue > limit) {
        record.addError("est_revenue", "ABOVE_ACCOUNT_REVENUE",
          `The estimated revenue is above the annual revenue of ${account.name}.`);
      }
    }
  }),
];
```

- Giá trị trong `record.new` cũng có thể là ID do handler gán, nên code kiểm tra `account` là object trước khi đọc `id` và `name`.
- Với thay đổi do người dùng thực hiện, `data.object()` đọc dưới danh tính người dùng đó: account mà người dùng không đọc được sẽ vắng mặt trong kết quả `getMany`, và `records.aggregate` không nhóm được. Nhóm qua `data.asSystem()` khi policy đã duyệt cho phép.
- Thao tác ghi của người dùng phải chờ trong lúc trigger before-change đọc dữ liệu. Mỗi lookup được mở rộng đọc thêm một Object, và `records.aggregate` không đếm thay đổi đang được lưu. Giữ ít lời gọi như vậy.
- Trigger này kiểm tra mọi thay đổi opportunity trong Workspace khi version của nó đang active; trigger không thuộc ví dụ. Bộ chạy trigger local của starter đọc record đã lưu, nên lookup của nó có `name: ""`; để thử message có dùng tên, gửi lookup trong `changes` dưới dạng `{"id": "...", "name": "..."}`.

Xem [Bắt đầu với Record Trigger](get-started-record-trigger.md) để khai báo, chạy và publish trigger.

## `records.aggregate` hay saved report

| Nhu cầu | Dùng |
|---|---|
| Đếm, tổng, trung bình, giá trị nhỏ nhất hoặc lớn nhất trên một Object, với điều kiện code dựng từ request, người gọi hoặc record đang xử lý | `records.aggregate` |
| Con số quyết định việc code làm, như hạn mức kiểm tra trước khi ghi | `records.aggregate`, dưới danh tính người gọi hoặc hệ thống |
| Nhóm theo giá trị lựa chọn, lookup, boolean, ngày hoặc số, tối đa 5.000 nhóm | `records.aggregate` |
| Nhiều Object nối với nhau, nhóm theo tuần, tháng, quý hoặc năm, trung vị hay công thức báo cáo, hoặc bảng lớn | Saved report |
| Số liệu người dùng tự cấu hình, chia sẻ và xem lại trên dashboard | Saved report |

Saved report được cấu hình trong Cogover và chia sẻ theo quyền truy cập riêng của báo cáo. SDK không có lời gọi chạy saved report, nên Custom Backend Module không đọc được báo cáo dưới danh tính người gọi. Khi route cần số liệu theo tháng, mỗi tháng một lời gọi `records.aggregate` với khoảng ngày trong `where` dùng được cho vài tháng; nhiều hơn, hoặc số liệu mọi người xem thường xuyên, thì dùng báo cáo.

## Nâng Project lên SDK 0.13.0

Version được publish trước khi Cogover chuyển sang SDK 0.13.0 giữ SDK mà nó được publish cùng, và có hai thay đổi với version đó:

- Lần đọc thiếu `fields` lỗi `ValidationError` với message `fields is required: pass field slugs or "*" (@cogover/sdk 0.13.0+)`. Nếu route không bắt lỗi, người gọi nhận HTTP `400` với `code: "VALIDATION_ERROR"`.
- Lookup đọc qua `data` có `name: ""`, và `system.createdBy.name` là `""`. SDK cũ không có `expandLookups`, nên version đó không lấy lại được tên.

Cách nâng cấp:

1. Chạy `npm install @cogover/sdk@latest`. Kiểm tra bằng `npm ls typescript` rằng TypeScript từ 5.0 trở lên.
2. Sinh lại `workspace.d.ts` như ở bước 2 nếu file do SDK cũ sinh ra.
3. Chạy `npm run build` và sửa mọi lỗi: thêm `fields` vào mỗi lần đọc, thêm vào `fields` các field code dùng, và thêm `expandLookups` ở nơi code dùng tên lookup hoặc field của record liên kết.
4. Thử trên local, rồi publish và activate version mới.

## Xử lý sự cố

| Vấn đề | Cần kiểm tra |
|---|---|
| Bước 2 in `The requested URL returned error: 401` | Workspace API key trong `.env` không hợp lệ với Workspace này. Sửa key rồi chạy lại các lệnh. |
| `cogover-generate-workspace-types` lỗi `Object metadata must contain an items array` | File đưa vào trình sinh không phải metadata của Object, ví dụ response lỗi được lưu khi tải không có `-f`. Tải lại bằng các lệnh ở bước 2. |
| `npm run build` báo `Expected 2 arguments, but got 1` hoặc `Property 'fields' is missing` | Thêm `fields` vào lần đọc. |
| `npm run build` báo một property không tồn tại trên kiểu `Readonly<Pick<...>>` | Thêm field đó vào `fields`. |
| `npm run build` báo `Cannot find name 'RecordReference'`, hoặc field lookup có kiểu `any` | Sinh lại `workspace.d.ts` bằng SDK từ 0.13.0. |
| Không có `expandLookups` hoặc `records.aggregate` | Cài SDK từ 0.13.0 bằng `npm install @cogover/sdk@latest`. |
| Route trả HTTP `400` với `VALIDATION_ERROR` và `The input or operation parameters are invalid.` | Một `ValidationError` không được bắt. Bắt lỗi và trả `error.message`, như `explainRefusal`, để xem lý do. Version publish trước SDK 0.13.0 mà đọc thiếu `fields` cũng lỗi như vậy: nâng cấp rồi publish lại. |
| `name` của lookup hoặc `system.createdBy.name` là `""` | Đúng như mong đợi khi không có `expandLookups`. Mở rộng lookup đó, hoặc liệt kê `["name"]` cho nó. |
| Tên nhân sự là mã như `PERSONNEL-0000000002-13/09/2026` | Đó là field `name` của record nhân sự. Dùng `org.personnel.get` với `withDisplay: true`. |
| Lookup đã mở rộng không có `fields` | Danh tính không đọc được record liên kết, record đã bị xóa, hoặc, với `true` hay `"*"`, policy không cấp quyền cho Object liên kết. |
| `expandLookups.account names a field that object 'account' does not have: ...` | Sửa slug field. |
| `PermissionDeniedError` với `This project has not been granted permission to access object '...' through data.asSystem().` | Với `data.asSystem()` hoặc `data.asUser()`, danh sách trong `expandLookups` cần identity policy cấp quyền cho Object liên kết và các field được liệt kê; `details.objectSlug` là Object đó. |
| `aggregate with groupBy is not supported for the default identity of this invocation, which reads as a delegated user; use asSystem()` | Code chạy trên local, trong trigger cho thay đổi của người dùng, hoặc trong job có người dùng. Gọi version đã publish, hoặc dùng `data.asSystem()`. |
| `metrics.<name>: the default identity of this invocation (a delegated user) supports only count on id and count, sum, avg, min and max on number fields; use asSystem()` | Cùng nguyên nhân; ở đó chỉ dùng các metric này. |
| `groupBy does not support field '...' of type ...` | Nhóm theo field lựa chọn, boolean, lookup, ngày hoặc số. |
| HTTP `403` với `The Project policy does not allow data.asSystem().` | Cấp quyền đọc qua `data.asSystem()` trong identity policy và duyệt policy cho version. Trên local, policy phải `ACTIVE` và Project key phải cho phép `asSystem`. |
| HTTP `401` với `DEVELOPMENT_SESSION_INVALIDATED` | Policy đã thay đổi. Khởi động lại `cogover-dev run`. |
| Route đã publish trả văn bản thuần `Cogover`, và `jq` báo lỗi parse | Gửi đủ `-H 'x-req-type: 9'` và `-H 'x-req-service: 3'`. Thiếu hai header này, request không tới Project. |
| `PERMISSION_DENIED` khi khởi động máy chủ local | Project key chỉ đọc cần `--allow-writes=false`. |
| Record vừa lưu chưa được đếm | Aggregate chậm hơn thao tác ghi khoảng một giây. Gọi lại. |
| `truncated` là `true` | Số nhóm nhiều hơn `limit`. Tăng `limit`, tối đa 5.000, hoặc thu hẹp `where`. |

## Toàn bộ `src/main.ts`

```typescript
import { createRouter, ValidationError, type ResponseApi } from "@cogover/sdk";

const router = createRouter();
const ID_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;
const OPEN_STAGES = ["needs_analysis", "proposal", "negotiation"] as const;
const OPPORTUNITY_FIELDS = ["name", "stage", "est_revenue", "account"] as const;

router.get("/opportunities", async ({ data }) => {
  const opportunities = data.object("opportunity");
  const page = await opportunities.records.list({
    fields: OPPORTUNITY_FIELDS,
    expandLookups: { account: ["industry"] },
    where: opportunities.fields.stage.in(OPEN_STAGES),
    orderBy: [opportunities.fields.est_revenue.desc()],
    limit: 3,
  });
  return {
    total: page.total,
    opportunities: page.items.map(item => ({
      id: item.id,
      name: item.fields.name,
      stage: item.fields.stage,
      estRevenue: item.fields.est_revenue,
      account: item.fields.account,
    })),
  };
});

router.get("/opportunities/:opportunityId", async ({ data, request, response }) => {
  const opportunityId = request.params.opportunityId ?? "";
  if (!ID_PATTERN.test(opportunityId)) {
    return response.json({ error: "A valid opportunity id is required" }, { status: 400 });
  }
  const opportunity = await data.object("opportunity").records.get(opportunityId, {
    fields: OPPORTUNITY_FIELDS,
  });
  if (opportunity === null) {
    return response.json({ error: "Opportunity not found" }, { status: 404 });
  }
  return opportunity;
});

router.get("/opportunities/:opportunityId/summary", async ({ data, org, request, response }) => {
  const opportunityId = request.params.opportunityId ?? "";
  if (!ID_PATTERN.test(opportunityId)) {
    return response.json({ error: "A valid opportunity id is required" }, { status: 400 });
  }
  const opportunity = await data.object("opportunity").records.get(opportunityId, {
    fields: ["name", "account", "owner"],
    expandLookups: true,
  });
  if (opportunity === null) {
    return response.json({ error: "Opportunity not found" }, { status: 404 });
  }
  const { account, owner } = opportunity.fields;
  const createdBy = opportunity.system.createdBy;
  const creator = createdBy === undefined
    ? null
    : await org.personnel.get(createdBy.id, { withDisplay: true });
  return {
    name: opportunity.fields.name,
    account: {
      name: account.name,
      industry: account.fields?.industry ?? null,
      fieldsRead: Object.keys(account.fields ?? {}).length,
    },
    owner: owner?.name ?? null,
    createdBy: {
      name: createdBy?.name ?? null,
      displayName: creator?.display?.name ?? null,
    },
  };
});

// Answers HTTP 400 with the reason when Cogover refuses the options of a call.
async function explainRefusal<T>(response: ResponseApi, run: () => Promise<T>) {
  try {
    return await run();
  } catch (error) {
    if (error instanceof ValidationError) {
      return response.json({ error: error.message }, { status: 400 });
    }
    throw error;
  }
}

router.get("/pipeline", async ({ data }) => {
  const opportunities = data.object("opportunity");
  const result = await opportunities.records.aggregate({
    where: opportunities.fields.stage.in(OPEN_STAGES),
    metrics: {
      opportunities: { count: "id" },
      revenue: { sum: "est_revenue" },
      averageRevenue: { avg: "est_revenue" },
      largestRevenue: { max: "est_revenue" },
    },
  });
  return result.values;
});

router.get("/pipeline/by-stage", ({ data, response }) => explainRefusal(response, async () => {
  const result = await data.object("opportunity").records.aggregate({
    groupBy: ["stage"],
    metrics: {
      opportunities: { count: "id" },
      revenue: { sum: "est_revenue" },
      accounts: { countDistinct: "account" },
    },
  });
  return {
    stages: result.groups.map(group => ({ stage: group.key.stage, ...group.values })),
    truncated: result.truncated,
  };
}));

router.get("/pipeline/top-accounts", ({ data, response }) => explainRefusal(response, async () => {
  const opportunities = data.object("opportunity");
  const result = await opportunities.records.aggregate({
    where: opportunities.fields.stage.in(OPEN_STAGES),
    groupBy: ["account"],
    metrics: {
      opportunities: { count: "id" },
      revenue: { sum: "est_revenue" },
    },
    limit: 2,
  });
  const accountIds = result.groups.map(group => group.key.account);
  const { records } = await data.object("account").records.getMany(accountIds, {
    fields: ["name"],
  });
  const nameById = new Map(records.map(record => [record.id, record.fields.name]));
  return {
    accounts: result.groups.map(group => ({
      id: group.key.account,
      name: nameById.get(group.key.account) ?? null,
      ...group.values,
    })),
    truncated: result.truncated,
  };
}));

export default router.toHandler();
```

## Đọc thêm

- [API record của SDK: Chọn field](cogover-sdk-api-reference.md#chọn-field), [Record liên kết](cogover-sdk-api-reference.md#record-liên-kết) và [Aggregate](cogover-sdk-api-reference.md#aggregate): mọi tùy chọn, giới hạn và kiểu dữ liệu.
- [Khai báo Workspace](cogover-sdk-api-reference.md#khai-báo-workspace): cách trình sinh ánh xạ loại field.
- [Bắt đầu với cơ cấu tổ chức](get-started-organization-structure.md): tên hiển thị của nhân sự với `withDisplay`.
- [Bắt đầu với Record Trigger](get-started-record-trigger.md): kiểm tra record trước khi lưu.
- [Bắt đầu với background job](get-started-background-jobs.md): chạy việc dài bên ngoài request.
- [Identity policy](custom-backend-module-api-reference.md#identity-policy-1): cấp quyền `data.asSystem()` và `allowInternalSystem`.
