# Bắt đầu với Record Trigger

Trong hướng dẫn này, chúng ta bổ sung record trigger vào một Project của tính năng Custom Backend Module. Record trigger chạy code của Project khi bản ghi của một Cogover Object được tạo, cập nhật hoặc xoá, bất kể nguồn ghi là gì: giao diện web Cogover, API, import, Process hay một Custom Backend Module khác. Vì vậy một quy tắc đặt trong trigger không thể bị bỏ qua bằng cách ghi bản ghi theo đường khác.

Sample khai báo ba trigger trên Object `review`:

| Trigger | Thời điểm | Thao tác | Việc làm |
|---|---|---|---|
| `grade_by_point` | before-change | create, update | Điền `grade` còn trống từ `point`, và từ chối `grade` cao hơn mức mà `point` cho phép. |
| `block_delete_completed` | before-change | delete | Từ chối xoá review có `status` là `completed`. |
| `note_when_completed` | after-change | create, update | Khi review trở thành `completed`, ghi thời điểm vào `notes`. |

Trigger **before-change** chạy trước khi thay đổi được lưu: có thể từ chối bản ghi bằng lỗi validation và điều chỉnh giá trị sẽ được lưu. Trigger **after-change** chạy bất đồng bộ sau khi thay đổi đã được lưu, dành cho việc xử lý tiếp theo; nó không thể từ chối hay sửa thay đổi đó.

Chúng ta viết code, kiểm tra, chạy trigger trên local, publish và activate Project, rồi xác minh từng trigger bằng các thay đổi bản ghi thật. Các bước tạo Project, cài starter và publish giống [Bắt đầu với Custom Backend Module](get-started-custom-backend-module.md); hướng dẫn này chỉ nhắc lại ngắn gọn và tập trung vào trigger.

## Yêu cầu

- Node.js 20 trở lên, và Cogover Dev CLI 0.10.0 trở lên.
- Quyền tạo Project và publish version trong tính năng Custom Backend Module.
- Project key do quản trị viên Workspace cấp, dùng ở mục 6 để chạy trigger trên local. Muốn thử trigger after-change trên local, key phải cho phép ghi.
- Workspace API key do quản trị viên Workspace cấp, dùng để publish và activate ở mục 7 và để test trigger ở mục 8. Đây là credential khác với Project key và không thể dùng thay thế lẫn nhau.
- `@cogover/sdk` 0.6.0 trở lên; các phiên bản cũ hơn chưa có record trigger. Bước 2 sẽ cập nhật package.
- Workspace có Object slug `review` với các field sau:

  | Field | Slug | Kiểu |
  |---|---|---|
  | Name | `name` | Short text (tên bản ghi) |
  | Point | `point` | Numeric |
  | Grade | `grade` | Single choice với các option `poor`, `average`, `good`, `excellent` |
  | Status | `status` | Single choice với các option `new` (mặc định) và `completed` |
  | Notes | `notes` | Long text |

  Tài khoản gắn với Workspace API key phải có quyền tạo, cập nhật và xoá bản ghi của Object này. Nếu Object trong Workspace của bạn có slug khác, thay `review` ở hai chỗ được nêu trong bước 4 (khai báo trong `workspace.d.ts` và hằng `OBJECT`), trong mảng `slugs` ở bước 8.1 và trong `object_slug` của các lệnh gọi API còn lại ở mục 8; các response mẫu ở mục 6 khi đó hiển thị slug của bạn ở `object` và `objectSlug`. Slug của các field phải khớp bảng trên.

## 1. Tạo Project trên Cogover

Mở tính năng **Custom Backend Module** và tạo một Project:

- Name: `Review triggers`
- Slug: `review_triggers`

Lưu lại `projectId` và `slug` trên trang chi tiết Project. Slug không thể đổi sau khi tạo.

Runtime URL chính là HTTPS origin của Workspace:

```text
https://{WORKSPACE_DOMAIN}
```

`WORKSPACE_DOMAIN` là hostname đầy đủ, ví dụ `example.cogover.net`. Không nối thêm path hoặc domain suffix khác.

## 2. Tải và cài đặt starter project

Tải starter project tại [cogover/custom-backend-module-starter-project](https://github.com/cogover/custom-backend-module-starter-project): chọn **Code → Download ZIP**, giải nén và mở terminal tại thư mục chứa `package.json`. Có thể đổi tên thư mục thành `review-triggers` để khớp ví dụ bên dưới.

Hoặc, nếu đã cài Git, clone trực tiếp:

```bash
git clone https://github.com/cogover/custom-backend-module-starter-project.git review-triggers
cd review-triggers
```

Cài Cogover Dev CLI và dependency của starter, rồi kiểm tra phiên bản SDK:

```bash
npm install --global @cogover/dev-cli
cogover-dev --version
npm install
npm ls @cogover/sdk
```

Lệnh cuối phải hiển thị `@cogover/sdk@0.6.0` trở lên, phiên bản đầu tiên có `defineTrigger`. Nếu hiển thị phiên bản cũ hơn, chạy `npm install @cogover/sdk@latest`; việc cập nhật cũng ghi phiên bản mới vào `package.json` và `package-lock.json`.

Starter ban đầu chưa có code sample trong `src/`; chúng ta sẽ tạo `cogover.json` ở bước 3 và các file sample ở bước 4. Cấu trúc chính sau khi hoàn thành bước 3–4:

```text
review-triggers/
├── cogover.example.json
├── cogover.json
├── package.json
├── tsconfig.json
├── local/
│   ├── cli.ts
│   ├── local-server.ts
│   ├── trigger-runner.ts
│   └── trigger-runner.test.ts
└── src/
    ├── main.ts
    ├── review-rules.ts
    ├── review-triggers.ts
    └── workspace.d.ts
```

- `src/` chứa code chạy trên Cogover và là thư mục sẽ được upload.
- `local/` chứa HTTP runner chỉ dùng trên local và runner chạy trigger local dùng ở mục 6, cùng test của chúng (`npm test` chạy các test này). Thư mục này không được import từ `src/` và không được upload.
- `cogover.json` chứa metadata Project, không chứa Project key hoặc credential.

## 3. Cấu hình Project local

Tạo `cogover.json` từ file mẫu:

```bash
cp cogover.example.json cogover.json
```

Cập nhật nội dung bằng thông tin của Project vừa tạo:

```json
{
  "version": 1,
  "runtimeUrl": "https://{WORKSPACE_DOMAIN}",
  "projectId": "{PROJECT_ID}",
  "projectSlug": "{PROJECT_SLUG}"
}
```

Trong hướng dẫn này, `{PROJECT_SLUG}` là `review_triggers`. Không đưa `cogover.json` vào Git, chỉ commit `cogover.example.json`; `.gitignore` của starter đã liệt kê file này cùng với `.env`.

## 4. Viết trigger

### 4.1. Khai báo schema của Object

Tạo `src/workspace.d.ts` để TypeScript kiểm tra slug Object, slug field và giá trị field mà trigger sử dụng:

```typescript
declare module "@cogover/sdk" {
  interface WorkspaceObjects {
    review: {
      name: string;
      point: number | null;
      grade: "poor" | "average" | "good" | "excellent" | null;
      status: "new" | "completed" | null;
      notes: string | null;
    };
  }
}

export {};
```

### 4.2. Viết quy tắc nghiệp vụ

Tạo `src/review-rules.ts`. Đây là các hàm thuần không phụ thuộc Cogover nên dễ viết unit test, và không nhắc tới slug của Object:

```typescript
export type Grade = "poor" | "average" | "good" | "excellent";

export const GRADE_TOO_HIGH_FOR_POINT = "GRADE_TOO_HIGH_FOR_POINT";
export const COMPLETED_RECORD_CANNOT_BE_DELETED = "COMPLETED_RECORD_CANNOT_BE_DELETED";

/** Lowest point that allows each grade, from the lowest grade to the highest. */
const GRADE_THRESHOLDS: readonly { grade: Grade; minPoint: number }[] = [
  { grade: "poor", minPoint: 0 },
  { grade: "average", minPoint: 5 },
  { grade: "good", minPoint: 7 },
  { grade: "excellent", minPoint: 9 },
];

/** The highest grade that a point allows. */
export function gradeForPoint(point: number): Grade {
  let result: Grade = "poor";
  for (const { grade, minPoint } of GRADE_THRESHOLDS) {
    if (point >= minPoint) result = grade;
  }
  return result;
}

/** Lowest point required by a grade. */
export function minPointForGrade(grade: Grade): number {
  return GRADE_THRESHOLDS.find(threshold => threshold.grade === grade)?.minPoint ?? 0;
}

/** A reviewer may grade lower than the point allows, never higher. */
export function isGradeAllowed(grade: Grade, point: number): boolean {
  return point >= minPointForGrade(grade);
}

export function completionNote(now: Date): string {
  return `Completed at ${now.toISOString()}`;
}
```

### 4.3. Khai báo trigger

Tạo `src/review-triggers.ts`. Mỗi trigger được khai báo bằng `defineTrigger(config, handler)`:

```typescript
import { defineTrigger } from "@cogover/sdk";
import {
  COMPLETED_RECORD_CANNOT_BE_DELETED,
  GRADE_TOO_HIGH_FOR_POINT,
  completionNote,
  gradeForPoint,
  isGradeAllowed,
  minPointForGrade,
} from "./review-rules.js";

// Slug of the Object whose records run these triggers.
const OBJECT = "review";

/**
 * Before-change, create and update: fill an empty grade from the point, and reject a grade
 * that is higher than the point allows. Runs only when point or grade changed, so an update
 * of other fields does not call it.
 */
export const gradeByPoint = defineTrigger({
  key: "grade_by_point",
  name: "Fill and validate grade by point",
  object: OBJECT,
  timing: "beforeChange",
  operations: ["create", "update"],
  fields: ["point", "grade"],
  changedFields: ["point", "grade"],
  writableFields: ["grade"],
}, ({ records, trigger, log }) => {
  let filled = 0;
  let rejected = 0;
  for (const record of records) {
    const point = record.new.point;
    if (typeof point !== "number") continue; // no point yet: nothing to check or fill

    const grade = record.new.grade;
    if (!grade) {
      record.new.grade = gradeForPoint(point);
      filled++;
    } else if (!isGradeAllowed(grade, point)) {
      record.addError("grade", GRADE_TOO_HIGH_FOR_POINT,
        `Grade ${grade} requires at least ${minPointForGrade(grade)} points.`);
      rejected++;
    }
  }
  log.info("grade_by_point finished", {
    operation: trigger.operation, records: records.length, filled, rejected,
  });
});

/** Before-change, delete: a completed review must stay. The error is about the whole record. */
export const blockDeleteCompleted = defineTrigger({
  key: "block_delete_completed",
  name: "Block deleting completed reviews",
  object: OBJECT,
  timing: "beforeChange",
  operations: ["delete"],
  fields: ["status"],
}, ({ records }) => {
  for (const record of records) {
    // A record that is being deleted has no `new`; its stored values are in `old`.
    if (record.old.status !== "completed") continue;
    record.addError(null, COMPLETED_RECORD_CANNOT_BE_DELETED, "A completed review cannot be deleted.");
  }
});

/**
 * After-change: once a review has been saved with status completed, write the time into notes.
 * `runWhen: "onEnter"` limits it to the change that makes the review completed, so the notes
 * write of this handler does not start it again.
 */
export const noteWhenCompleted = defineTrigger({
  key: "note_when_completed",
  name: "Write a note when a review is completed",
  object: OBJECT,
  timing: "afterChange",
  operations: ["create", "update"],
  fields: ["status"],
  when: { op: "=", field: "status", params: "completed" },
  runWhen: "onEnter",
}, async ({ records, trigger, data, log }) => {
  const note = completionNote(new Date());
  // After the save every record has an ID; the check only narrows the type.
  const items = records.flatMap(record =>
    record.id === null ? [] : [{ id: record.id, fields: { notes: note } }],
  );
  if (items.length === 0) return;

  // One write for the whole list, never one write per record.
  const response = await data.object(OBJECT).records.batchUpdate(items);
  const failed = response.results.filter(row => !row.success);
  for (const row of failed) {
    log.warn("note_when_completed could not write notes", { referenceId: row.referenceId, r: row.r, msg: row.msg });
  }
  log.info("note_when_completed finished", {
    operation: trigger.operation, changeId: trigger.changeId, records: records.length, failed: failed.length,
  });
});
```

Ý nghĩa của cấu hình:

- `key` định danh trigger bên trong Project. Giữ key ổn định giữa các version: key mới là một trigger khác.
- `object` là slug của Object có bản ghi chạy trigger. Nếu Object của bạn có slug khác, đổi hằng `OBJECT` tại đây và key của khai báo trong `workspace.d.ts`; đó là hai chỗ duy nhất nêu tên Object.
- `timing` là `"beforeChange"` hoặc `"afterChange"`; `operations` liệt kê `"create"`, `"update"` và `"delete"`.
- `fields` chọn các giá trị được đưa vào `record.new` và `record.old`. Chỉ các field này và `id` có mặt. Chỉ liệt kê những gì handler cần đọc.
- `changedFields` làm cho update chỉ chạy trigger khi ít nhất một field được liệt kê thay đổi. Create và delete không bị ảnh hưởng.
- `writableFields` liệt kê các field mà handler before-change được phép sửa qua `record.new`. Sửa field khác làm thao tác ghi thất bại.
- `when` chỉ chạy trigger cho bản ghi khớp điều kiện. Với `runWhen: "onEnter"`, trigger chỉ chạy khi bản ghi bắt đầu khớp `when`; ở đây là đúng thay đổi làm review trở thành `completed`. Nếu không có nó, lệnh ghi `notes` của handler after-change sẽ chạy lại chính trigger đó.

Handler làm gì:

- `record.new` chứa giá trị sau thay đổi và có thể sửa đối với các field trong `writableFields`; `record.old` chứa giá trị trước thay đổi. Với bản ghi được tạo, `old` là `null`; với bản ghi bị xoá, `new` là `null`. Kiểu TypeScript đi theo `operations` đã khai báo.
- `record.addError(field, code, message?)` từ chối một bản ghi. Truyền `null` làm field cho lỗi cấp toàn bản ghi. Code là định danh viết hoa; message tuỳ chọn là câu tiếng Anh mà Cogover hiển thị cho end-user khi không có bản dịch cho code. Bản ghi bị từ chối không được lưu; trong thao tác ghi hàng loạt, các dòng còn lại vẫn tiếp tục.
- Handler nhận toàn bộ bản ghi của một thay đổi, tối đa 200 bản ghi mỗi lần gọi, nên ghi hàng loạt hoặc import gọi handler một lần cho mỗi lô. Xử lý cả danh sách và không bao giờ đọc hay ghi từng bản ghi trong vòng lặp; handler after-change ghi `notes` cho mọi bản ghi bằng một lệnh `batchUpdate`.
- Handler before-change chỉ đọc: được đọc bản ghi và schema, nhưng mọi lệnh ghi bản ghi, `fetch`, lock và ghi state đều bị từ chối. Handler phải kết thúc trong `timeoutMs` (mặc định 2 giây); khi ném lỗi hoặc hết thời gian, thao tác ghi bị từ chối.
- Handler after-change chạy sau khi người ghi đã nhận response. Nó được ghi bản ghi và gọi `fetch`, với quyền của người dùng đã thực hiện thay đổi. Việc giao nhận là best-effort: handler đôi khi có thể chạy hơn một lần cho cùng một thay đổi, hoặc không chạy, nên hãy giữ handler idempotent và đặt quy tắc quan trọng trong trigger before-change.

### 4.4. Export trigger

Tạo `src/main.ts`. Cogover nhận diện record trigger qua named export `triggers`; default export vẫn là HTTP handler và là tuỳ chọn với Project chỉ khai báo trigger. Sample giữ một route nhỏ liệt kê các trigger đã khai báo; mục 6 gọi route này trên local:

```typescript
import { createRouter } from "@cogover/sdk";
import { blockDeleteCompleted, gradeByPoint, noteWhenCompleted } from "./review-triggers.js";

// Cogover discovers record triggers through this named export.
export const triggers = [gradeByPoint, blockDeleteCompleted, noteWhenCompleted];

// Optional HTTP route: lists the triggers declared by the version that answers.
const router = createRouter();
router.post("/", () => ({
  triggers: triggers.map(trigger => ({
    key: trigger.key,
    timing: trigger.config.timing,
    operations: trigger.config.operations,
  })),
}));

export default router.toHandler();
```

Các message do sample trả về luôn dùng tiếng Anh.

## 5. Kiểm tra code

Typecheck Project trước khi đi tiếp:

```bash
npm run typecheck
```

TypeScript đối chiếu slug Object, slug field và giá trị field với `workspace.d.ts`: ví dụ gán một grade không thuộc bốn option, hoặc dùng một slug field chưa khai báo ở đó, sẽ được báo tại đây. Nếu bước kiểm tra báo lỗi trong `local/trigger-runner.test.ts` mà không có lỗi trong `src/`, xem mục Xử lý sự cố trước khi tiếp tục; local server ở mục 6 chạy cùng bước kiểm tra này. TypeScript không kiểm tra danh sách `fields` của trigger: field mà handler đọc nhưng không liệt kê trong `fields` chỉ đơn giản là vắng mặt lúc chạy. `defineTrigger` cũng validate cấu hình khi module được nạp, nên `key`, `order` hoặc `timeoutMs` không hợp lệ sẽ ném `ValidationError` ở bước 6 hoặc lúc publish.

## 6. Chạy trigger trên local

Cogover chỉ gửi sự kiện thay đổi bản ghi thật tới version đã publish và đang active của Project, nên trigger trong bản đang viết chưa được thay đổi bản ghi nào kích hoạt. Local server của starter bù vào chỗ này: nó nạp export `triggers` và chạy một trigger theo yêu cầu, với bản ghi thật được đọc qua Development Session, nên handler có thể được debug trước khi publish.

Đăng nhập bằng Project key. CLI yêu cầu nhập key qua prompt và không hiển thị giá trị:

```bash
cogover-dev login --profile review_triggers
cogover-dev doctor --profile review_triggers
```

CLI ưu tiên credential store của hệ điều hành. Nếu native credential store không khả dụng, CLI lưu entry riêng cho profile trong `.env` cạnh `cogover.json`, đặt quyền file hạn chế và bảo đảm `.gitignore` liệt kê `/.env` cùng các file tạm của nó; Git khi đó có thể báo `.gitignore` bị sửa, và nên giữ thay đổi này. Không commit hoặc chia sẻ `.env`, và không đặt key trong `cogover.json`, source code hay command line.

Start local server với Development Session chỉ đọc. Handler before-change chỉ được đọc trên Cogover, nhưng Development Session local không ép buộc điều đó; `--allow-writes=false` làm cho một lệnh ghi vô ý trong handler before-change cũng thất bại trên local:

```bash
COGOVER_LOCAL_PORT=3100 cogover-dev run --profile review_triggers --allow-writes=false -- npm run dev
```

Khi khởi động xong, terminal hiển thị, cùng với một số dòng khác:

```text
Cogover local project server listening at http://127.0.0.1:3100/api/v1/ts-projects/review_triggers
Record triggers: grade_by_point, block_delete_completed, note_when_completed
Run a trigger locally: POST http://127.0.0.1:3100/__cogover/triggers/<key>
```

Giữ terminal này mở và dùng terminal khác cho các lệnh gọi bên dưới. Các route dưới `/__cogover/` chỉ tồn tại trên local server; chúng không bao giờ là một phần của Project đã publish.

### 6.1. Liệt kê trigger đã khai báo

```bash
curl -s 'http://127.0.0.1:3100/__cogover/triggers'
```

Response liệt kê mọi trigger trong export `triggers` cùng cấu hình đã chuẩn hoá, tức là đã áp dụng các giá trị mặc định. Dưới đây là phần tử đầu tiên; hai trigger còn lại có cùng cấu trúc, với `writableFields: []` khi không khai báo, không có `changedFields` khi không khai báo, và có bộ lọc `when` ở trigger after-change:

```json
{
  "triggers": [
    {
      "key": "grade_by_point",
      "name": "Fill and validate grade by point",
      "object": "review",
      "timing": "beforeChange",
      "operations": ["create", "update"],
      "fields": ["point", "grade"],
      "changedFields": ["point", "grade"],
      "runWhen": "always",
      "writableFields": ["grade"],
      "order": 5000,
      "timeoutMs": 2000
    }
  ]
}
```

HTTP route của `main.ts` cũng trả lời:

```bash
curl -s -X POST 'http://127.0.0.1:3100/api/v1/ts-projects/review_triggers' \
  -H 'Content-Type: application/json' \
  --data '{}'
```

```json
{
  "triggers": [
    { "key": "grade_by_point", "timing": "beforeChange", "operations": ["create", "update"] },
    { "key": "block_delete_completed", "timing": "beforeChange", "operations": ["delete"] },
    { "key": "note_when_completed", "timing": "afterChange", "operations": ["create", "update"] }
  ]
}
```

### 6.2. Chạy trigger before-change cho bản ghi mới

Chạy `grade_by_point` như thể một review 3 điểm với grade `good` đang được tạo. Với `create`, `changes` chứa giá trị field của bản ghi mới, bản ghi này chưa có ID:

```bash
curl -s -X POST 'http://127.0.0.1:3100/__cogover/triggers/grade_by_point' \
  -H 'Content-Type: application/json' \
  --data '{"operation":"create","changes":{"point":3,"grade":"good"}}'
```

```json
{
  "trigger": { "key": "grade_by_point", "timing": "beforeChange", "operation": "create", "objectSlug": "review", "changeId": "00000000-0000-4000-8000-000000000001" },
  "input": {
    "records": [
      { "key": "0", "id": null, "new": { "point": 3, "grade": "good" }, "old": null, "changedFields": ["point", "grade"] }
    ]
  },
  "results": [
    { "key": "0", "errors": [ { "field": "grade", "code": "GRADE_TOO_HIGH_FOR_POINT", "message": "Grade good requires at least 7 points." } ] }
  ],
  "warnings": [
    "Before-change handlers are read-only in Cogover, but a local Development Session does not enforce this. Start cogover-dev run with --allow-writes=false to catch writes."
  ]
}
```

- `input.records` đúng là những gì handler nhận được.
- `results` là những gì handler trả về cho Cogover với từng bản ghi: `errors` từ `addError`, và `changes` gồm các field handler đã gán. Bản ghi không có lỗi hay thay đổi thì không xuất hiện.
- `warnings` liệt kê những gì runner không kiểm tra được trên local. Cảnh báo về `--allow-writes=false` xuất hiện ở mọi lần chạy before-change, kể cả khi server đã được khởi động với cờ đó.

Giờ chạy cho một review 7 điểm không có grade:

```bash
curl -s -X POST 'http://127.0.0.1:3100/__cogover/triggers/grade_by_point' \
  -H 'Content-Type: application/json' \
  --data '{"operation":"create","changes":{"point":7}}'
```

Lần này `results` mang grade mà handler đã điền:

```json
"results": [ { "key": "0", "changes": { "grade": "good" } } ]
```

### 6.3. Chạy trigger cho bản ghi đã lưu

Với `update` và `delete`, truyền `recordId` của một review có sẵn. Runner đọc bản ghi đó qua Development Session, giới hạn theo `fields` của trigger, vào `record.old`; với `update`, nó phủ `changes` lên trên để tạo `record.new`.

Bước này cần một review đang tồn tại trong Workspace với status `completed`. Tạo review đó trên giao diện web Cogover, hoặc bằng Records API: đặt Workspace API key vào `.env` ngay bây giờ như mô tả ở mục 7, chạy hai lệnh shell nạp key ở đầu mục 8, tạo review bằng lệnh ở bước 8.3 và đặt status thành `completed` bằng lệnh ở bước 8.5. Chưa có trigger nào active nên cả hai đều là thao tác ghi bình thường. Lưu ID làm `{RECORD_ID}` và xoá review này ở cuối bằng hai lệnh của bước 8.7. Chạy trigger chặn xoá cho bản ghi đó:

```bash
curl -s -X POST 'http://127.0.0.1:3100/__cogover/triggers/block_delete_completed' \
  -H 'Content-Type: application/json' \
  --data '{"operation":"delete","recordId":"{RECORD_ID}"}'
```

Với review có status `completed`, `results` chứa lỗi cấp toàn bản ghi với `field` bằng `null`:

```json
"input": { "records": [ { "key": "0", "id": "REPLACE_WITH_RECORD_ID", "new": null, "old": { "id": "REPLACE_WITH_RECORD_ID", "status": "completed" }, "changedFields": [] } ] },
"results": [ { "key": "0", "errors": [ { "field": null, "code": "COMPLETED_RECORD_CANNOT_BE_DELETED", "message": "A completed review cannot be deleted." } ] } ]
```

Với review có status `new`, `results` là `[]`: handler cho phép xoá. ID không tồn tại, hoặc danh tính của Development Session không đọc được, trả HTTP `404` với code `RECORD_NOT_FOUND`.

### 6.4. Những gì lần chạy local không làm

- `when`, `changedFields` và `runWhen` không được đánh giá: trigger chạy cho các bản ghi bạn gửi, và `warnings` cho biết khi nào Cogover sẽ bỏ qua nó.
- Field trong `changes` không có trong `fields` bị bỏ qua và được báo trong `warnings`, vì Cogover sẽ không đưa nó vào `record.new`.
- Thao tác mà trigger không khai báo trả HTTP `400` với code `TRIGGER_OPERATION_NOT_SUPPORTED`; key không tồn tại trả HTTP `404` với `TRIGGER_NOT_FOUND`. Gửi `records: [{"recordId": "...", "changes": {...}}, ...]` thay cho dạng rút gọn một bản ghi để chạy một lần gọi cho tối đa 200 bản ghi.
- Handler after-change có ghi dữ liệu, như `note_when_completed`, cần Development Session ghi được. Với `--allow-writes=false`, lần chạy thất bại với HTTP `403`, code `PERMISSION_DENIED` và reason `DEVELOPMENT_SESSION_READ_ONLY`. Muốn thử, dừng server bằng `Ctrl+C`, khởi động lại không có `--allow-writes=false` (Project key phải cho phép ghi) và chạy trigger cho một review đã lưu:

  ```bash
  curl -s -X POST 'http://127.0.0.1:3100/__cogover/triggers/note_when_completed' \
    -H 'Content-Type: application/json' \
    --data '{"operation":"update","recordId":"{RECORD_ID}","changes":{"status":"completed"}}'
  ```

  Handler khi đó ghi `notes` của review đó thật sự, qua Development Session, và `results` là `[]` vì trigger after-change không trả về thay đổi; `warnings` báo rằng `when` và `runWhen` không được đánh giá. Đọc lại review bằng lệnh liệt kê ở bước 8.3: `notes` chứa `Completed at` kèm thời điểm chạy.

Dừng local server bằng `Ctrl+C` trước khi tiếp tục.

## 7. Publish và activate

Chạy bước kiểm tra local rồi publish bằng Cogover Dev CLI tại thư mục chứa `cogover.json`:

```bash
npm run build
cogover-dev publish
```

`publish` và `activate` dùng Workspace API key. CLI tìm `COGOVER_API_KEY` trong `.env` của Project, sau đó trong credential store của hệ điều hành, và yêu cầu nhập qua prompt bảo mật nếu chưa có. Để không phải nhập qua prompt, ví dụ trong terminal không hiển thị được prompt, thêm dòng sau vào `.env` của Project trước khi publish; mục 8 đọc cùng dòng này:

```text
COGOVER_API_KEY={WORKSPACE_API_KEY}
```

Không truyền key trên command line hoặc ghi vào source.

CLI tạo ZIP từ thư mục `src/`, upload, tạo version và chờ đến khi version chuyển sang `READY` hoặc `FAILED`. Khi build version, Cogover evaluate export `triggers`, ghi cấu hình của từng trigger thành trigger manifest của version và validate: Object cùng mọi slug field phải tồn tại trong Workspace, `writableFields` không được chứa field chỉ đọc, và key không được trùng. Vi phạm làm version kết thúc ở `FAILED` với build error code `TRIGGER_MANIFEST_INVALID` và message nêu key hoặc slug sai; sửa code rồi publish lại.

Khi version đã `READY`, `publish` in ra version ID và lệnh activate tương ứng. Số thứ tự version tăng sau mỗi lần publish của Project, kể cả các version bị xoá về sau:

```text
Published version {N} ({VERSION_ID}) is READY.
Next: cogover-dev activate {VERSION_ID}
```

Chạy lệnh activate với đúng version ID đó:

```bash
cogover-dev activate <VERSION_ID>
```

Activate một version áp dụng trigger manifest của nó: từ thời điểm đó, các trigger chạy cho mọi thao tác create, update, delete trên Object, từ mọi nguồn. Activate version khác thay bằng trigger của version đó, còn deactivate Project gỡ toàn bộ trigger. Các thao tác này cũng thực hiện được trên giao diện quản lý Project: upload ZIP ở chế độ private, chờ `READY` rồi activate.

## 8. Test trigger bằng thay đổi bản ghi thật

Trigger giờ chạy cho mọi thao tác ghi, nên có thể xác minh ngay trên giao diện web Cogover bằng cách tạo, sửa và xoá bản ghi Review. Các bước dưới đây làm điều tương tự qua Records API bằng curl để dễ đối chiếu response. Đây là các thao tác ghi thật trên Workspace, không phải dry-run.

Đặt Workspace API key vào `.env` của Project (cùng file mà Cogover Dev CLI đọc) nếu chưa có, dưới dạng dòng `COGOVER_API_KEY={WORKSPACE_API_KEY}`, rồi nạp vào shell:

```bash
set -a; . ./.env; set +a
WORKSPACE_DOMAIN={WORKSPACE_DOMAIN}
```

Lệnh đầu cũng export các entry khác trong `.env`, chẳng hạn entry profile do `login` ghi; chỉ chạy lệnh này trong terminal của chính bạn.

Các response bên dưới lược bỏ các field metadata Workspace mà mọi response của Records API đều có.

### 8.1. Lấy Object ID

Xoá bản ghi cần Object ID:

```bash
curl -s -X POST "https://$WORKSPACE_DOMAIN/bapi/v1/objects/list" \
  -H "Authorization: Bearer $COGOVER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"slugs":["review"]}'
```

Lưu `items[0].id` làm `{OBJECT_ID}`.

### 8.2. Grade quá cao bị từ chối

Tạo review 3 điểm với grade `good`, mức cần 7 điểm:

```bash
curl -s -X POST "https://$WORKSPACE_DOMAIN/bapi/v1/records" \
  -H "Authorization: Bearer $COGOVER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"object_slug":"review","data":{"name":"Review A","point":3,"grade":"good"}}'
```

Trigger before-change từ chối bản ghi và không có gì được lưu. Response có HTTP status `400`:

```json
{
  "r": 70,
  "msg": "BEFORE_CHANGE_TRIGGER_REJECTED",
  "data": { "trigger": { "key": "grade_by_point", "owner_type": "CUSTOM" } },
  "meta": { "grade": "GRADE_TOO_HIGH_FOR_POINT" },
  "messages": { "GRADE_TOO_HIGH_FOR_POINT": "Grade good requires at least 7 points." }
}
```

`meta` ánh xạ từng slug field tới mã lỗi đã truyền cho `addError`, và `messages` ánh xạ mã lỗi tới nội dung message. Giao diện web Cogover hiển thị cùng lỗi này ngay trên field của form.

### 8.3. Grade trống được điền

Tạo review 7 điểm không có grade:

```bash
curl -s -X POST "https://$WORKSPACE_DOMAIN/bapi/v1/records" \
  -H "Authorization: Bearer $COGOVER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"object_slug":"review","data":{"name":"Review B","point":7}}'
```

Response có HTTP status `201` và ID bản ghi mới; lưu lại làm `{RECORD_ID}`:

```json
{ "r": 0, "msg": "OK", "data": { "id": "REPLACE_WITH_RECORD_ID" } }
```

Đọc lại bản ghi:

```bash
curl -s -X POST "https://$WORKSPACE_DOMAIN/bapi/v1/records/list" \
  -H "Authorization: Bearer $COGOVER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"object_slug":"review","type":1,"logic_sequence":"","size":1,"search_after":[],"order_direction":"next","sorts":[{"updated":{"order":"desc"}}],"show_detail_on_record":false,"filters":[{"field":"id","op":"=","params":"{RECORD_ID}","fieldType":"short_text"}]}'
```

`data.rows[0]` chứa giá trị đã lưu: trigger đã điền `grade` trước khi bản ghi được lưu, còn `status` mang giá trị mặc định. Field chưa có giá trị không xuất hiện trong dòng, nên `notes` chưa có mặt. Dòng còn chứa các field hệ thống như `created`, `updated`, `created_by` và `updated_by`, không hiển thị ở đây; hai field cuối là bản ghi nhân sự đầy đủ chứa dữ liệu cá nhân, nên không dán response thô vào ticket hay chat.

```json
{ "id": "REPLACE_WITH_RECORD_ID", "name": "Review B", "point": 7, "grade": "good", "status": "new" }
```

### 8.4. Quy tắc cũng áp dụng khi cập nhật

Thử nâng grade lên `excellent`, mức cần 9 điểm:

```bash
curl -s -X PUT "https://$WORKSPACE_DOMAIN/bapi/v1/records/{RECORD_ID}" \
  -H "Authorization: Bearer $COGOVER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"object_slug":"review","data":{"grade":"excellent"}}'
```

Cập nhật bị từ chối với HTTP status `400`, `r: 70` và `meta.grade` bằng `GRADE_TOO_HIGH_FOR_POINT`; grade đã lưu vẫn là `good`.

### 8.5. Hoàn thành review chạy trigger after-change

Đặt status thành `completed`:

```bash
curl -s -X PUT "https://$WORKSPACE_DOMAIN/bapi/v1/records/{RECORD_ID}" \
  -H "Authorization: Bearer $COGOVER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"object_slug":"review","data":{"status":"completed"}}'
```

Response là HTTP status `200` ngay lập tức: người ghi không chờ trigger after-change.

```json
{ "r": 0, "msg": "OK", "data": {} }
```

Cập nhật này không đổi `point` hay `grade` nên `grade_by_point` không chạy. Vài giây sau, đọc lại bản ghi bằng lệnh ở bước 8.3:

```json
{ "id": "REPLACE_WITH_RECORD_ID", "name": "Review B", "point": 7, "grade": "good", "status": "completed", "notes": "Completed at 2026-09-20T18:16:41.000Z" }
```

`notes` được `note_when_completed` ghi bằng một lệnh ghi riêng sau khi lưu. Nếu `notes` vẫn trống, chờ thêm một chút rồi đọc lại; trigger after-change chạy nền ngay sau thay đổi. Chính lệnh ghi `notes` là một update trên bản ghi đã khớp `when`, nên với `runWhen: "onEnter"` nó không kích hoạt lại trigger.

### 8.6. Review đã hoàn thành không thể xoá

```bash
curl -s -X POST "https://$WORKSPACE_DOMAIN/bapi/v1/records/delete" \
  -H "Authorization: Bearer $COGOVER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"object_type":"{OBJECT_ID}","ids":["{RECORD_ID}"]}'
```

Thao tác xoá bị từ chối với HTTP status `400`. Lỗi cấp toàn bản ghi dùng key `$record` trong `meta`:

```json
{
  "r": 70,
  "msg": "BEFORE_CHANGE_TRIGGER_REJECTED",
  "data": { "trigger": { "key": "block_delete_completed", "owner_type": "CUSTOM" } },
  "meta": { "$record": "COMPLETED_RECORD_CANNOT_BE_DELETED" },
  "messages": { "COMPLETED_RECORD_CANNOT_BE_DELETED": "A completed review cannot be deleted." }
}
```

### 8.7. Dọn dẹp

Đặt status về `new` (response giống bước 8.5) rồi xoá review. Trigger chặn xoá chạy lại, thấy review chưa hoàn thành và cho phép xoá:

```bash
curl -s -X PUT "https://$WORKSPACE_DOMAIN/bapi/v1/records/{RECORD_ID}" \
  -H "Authorization: Bearer $COGOVER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"object_slug":"review","data":{"status":"new"}}'

curl -s -X POST "https://$WORKSPACE_DOMAIN/bapi/v1/records/delete" \
  -H "Authorization: Bearer $COGOVER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"object_type":"{OBJECT_ID}","ids":["{RECORD_ID}"]}'
```

```json
{ "r": 0, "msg": "Success", "data": { "deleted": ["REPLACE_WITH_RECORD_ID"], "not_deleted": [] } }
```

## 9. Thay đổi trigger

Muốn đổi quy tắc, sửa code, publish version mới và activate; trigger của version mới thay thế trigger của version trước. Trigger giữ danh tính qua `key`, nên hãy giữ key ổn định và gỡ một trigger bằng cách bỏ nó khỏi export `triggers`. Deactivate Project gỡ toàn bộ trigger của Project.

## Xử lý sự cố

- **`npm run typecheck` báo lỗi trong `local/trigger-runner.test.ts`.** Bản starter của bạn có trước thay đổi làm cho test của starter không phụ thuộc `workspace.d.ts`. Cho tới khi bản starter bạn tải về có test đã cập nhật, thêm `"exclude": ["local/**/*.test.ts"]` ở cấp cao nhất, cạnh `include`, trong `tsconfig.json`; `npm run typecheck`, `npm run dev` và `npm test` khi đó đều chạy được.
- **Version ở trạng thái `FAILED` với `TRIGGER_MANIFEST_INVALID`.** Build error message nêu key hoặc slug sai: slug Object hoặc field không tồn tại trong Workspace, field chỉ đọc hoặc field hệ thống trong `writableFields`, hoặc hai trigger trùng key. Đối chiếu slug với Object trên Workspace rồi publish lại.
- **Thao tác ghi trả HTTP `400` với `r: 70` và `BEFORE_CHANGE_TRIGGER_REJECTED`.** Một trigger before-change đã chủ động từ chối bản ghi; `data.trigger.key` cho biết trigger nào và `meta` liệt kê mã lỗi.
- **Thao tác ghi trả HTTP `503` với `BEFORE_CHANGE_TRIGGER_FAILED`.** Handler before-change ném lỗi, hết thời gian, hoặc cố ghi dữ liệu, gọi `fetch` hay một thao tác bị từ chối khác. Trigger before-change fail-closed, nên thao tác ghi bị từ chối cho đến khi code được sửa và version mới được activate.
- **Thao tác ghi bị từ chối trước khi trigger nào chạy.** Cogover kiểm tra field bắt buộc, kiểu dữ liệu và giới hạn giá trị cấu hình trên field trước; trigger chỉ nhận giá trị đã qua các kiểm tra đó. Dùng trigger cho những quy tắc mà cấu hình field không diễn đạt được.
- **`notes` không được ghi.** Trigger after-change chạy nền ngay sau thay đổi, nên đọc lại bản ghi sau vài giây. Kiểm tra bản ghi thực sự đã đi vào điều kiện `when`: update một review vốn đã `completed` không chạy trigger có `runWhen: "onEnter"`. Handler ghi với quyền của người dùng đã thực hiện thay đổi; nếu người dùng đó không được cập nhật `notes`, lệnh ghi thất bại và lỗi được ghi vào log của Project.
- **Thao tác ghi thất bại với `ValidationError` nêu tên một field.** Handler đã sửa một field không có trong `writableFields`. Thêm field vào `writableFields` hoặc bỏ việc sửa.

Danh sách đầy đủ các tuỳ chọn, kiểu dữ liệu và quy tắc thực thi có trong mục Record trigger của [SDK usage guide](cogover-sdk-usage-guide.md#record-trigger) và [SDK API reference](cogover-sdk-api-reference.md#record-trigger) của `@cogover/sdk`.
