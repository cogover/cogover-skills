# Bắt đầu với cơ cấu tổ chức

Trước tiên, xem người gọi làm việc ở đâu và những ai thuộc một phòng ban. Sau đó, tìm các quản lý có quyền duyệt yêu cầu của một người. Thử toàn bộ trên local rồi mới publish. Ví dụ chỉ đọc cơ cấu tổ chức nên không cần tạo Object và không ghi dữ liệu nào.

## Chuẩn bị

- Cài Node.js 20 trở lên, Git, `curl` và `jq`.
- Dùng Workspace đã thiết lập phòng ban, vị trí và nhân sự, trong đó nhân sự của bạn thuộc ít nhất một phòng ban.
- Có quyền tạo, publish và activate Project.
- Chuẩn bị Project key để chạy local và Workspace API key để publish. Đây là hai khóa khác nhau. Ví dụ chỉ đọc dữ liệu nên Project key chỉ đọc là đủ.

Xem cách tạo Project trong [Bắt đầu với Custom Backend Module](get-started-custom-backend-module.md).

## Phần 1. Đọc cơ cấu tổ chức

### 1. Tạo Project

Trong Cogover, mở **Custom Backend Module**, tạo Project tên `Org demo` với slug `org_demo`. Sao chép Project ID, rồi chạy:

```bash
git clone https://github.com/cogover/custom-backend-module-starter-project.git org-demo
cd org-demo
npm install --global @cogover/dev-cli@latest
npm install
npm install @cogover/sdk@latest
cogover-dev --version
npm ls @cogover/sdk
cp cogover.example.json cogover.json
```

Dùng CLI từ 0.14.0 và SDK từ 0.11.0; SDK cũ hơn chưa có `org`. Sửa `cogover.json` cho giống nội dung dưới đây, với hostname của Workspace (ví dụ `example.cogover.net`) và Project ID của bạn. Đặt `projectSlug` là `org_demo`: mọi URL trong tài liệu này dùng slug đó.

```json
{
  "version": 1,
  "runtimeUrl": "https://{WORKSPACE_DOMAIN}",
  "projectId": "{PROJECT_ID}",
  "projectSlug": "org_demo"
}
```

Tạo `.env` trong thư mục này với Workspace API key của bạn:

```dotenv
COGOVER_API_KEY={WORKSPACE_API_KEY}
```

Starter đã bỏ qua `.env` và `cogover.json` trong Git. Không đặt khóa trong source code. Chạy các lệnh còn lại từ thư mục này.

### 2. Viết handler

Tạo file `src/main.ts`:

```typescript
import { createRouter, NotFoundError, type OrgDepartmentNode } from "@cogover/sdk";

const router = createRouter();
const ID_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;

router.get("/me", async ({ org, response }) => {
  const me = await org.me({ withDisplay: true });
  if (me === null) {
    return response.json({ error: "This call has no signed-in personnel" }, { status: 403 });
  }
  return {
    personnelId: me.id,
    name: me.display?.name ?? me.id,
    memberships: me.memberships.map(membership => ({
      departmentId: membership.departmentId,
      department: membership.departmentName,
      position: membership.positionName,
      level: membership.level,
      primary: membership.primary,
    })),
  };
});

router.get("/departments", async ({ org }) => {
  const roots = await org.departments.tree({ withDisplay: true });
  const departments: { id: string; name: string; level: number }[] = [];
  const visit = (nodes: readonly OrgDepartmentNode<true>[]) => {
    for (const node of nodes) {
      departments.push({ id: node.id, name: node.display?.name ?? node.id, level: node.level });
      visit(node.children);
    }
  };
  visit(roots);
  return { departments };
});

router.get("/departments/:departmentId/members", async ({ org, request, response }) => {
  const departmentId = request.params.departmentId ?? "";
  if (!ID_PATTERN.test(departmentId)) {
    return response.json({ error: "A valid department id is required" }, { status: 400 });
  }
  try {
    const page = await org.departments.members(departmentId, { withDisplay: true, limit: 50 });
    return {
      departmentId,
      total: page.total,
      members: page.items.map(member => ({
        personnelId: member.personnelId,
        name: member.display?.name ?? member.personnelId,
        position: member.positionName,
        level: member.level,
        hasAccount: member.accountId !== null,
      })),
    };
  } catch (error) {
    if (error instanceof NotFoundError) {
      return response.json({ error: "Department not found" }, { status: 404 });
    }
    throw error;
  }
});

export default router.toHandler();
```

Handler có ba route chỉ đọc:

- `GET /me` trả nhân sự của người gọi cùng mọi phòng ban người đó thuộc về. `org.me()` trả `null` khi lời gọi không có người dùng đăng nhập, nên route trả `403`.
- `GET /departments` đọc toàn bộ cây phòng ban rồi trải phẳng theo thứ tự hiển thị. `level` là độ sâu trong cây: `1` là phòng ban gốc.
- `GET /departments/:departmentId/members` liệt kê 50 thành viên đầu tiên của một phòng ban: quản lý trước, nhân viên sau. Phòng ban không tồn tại sẽ ném `NotFoundError`, route chuyển thành `404`.

Mỗi lời gọi `org` đọc ID, phòng ban và cấp quản lý từ bản cơ cấu đã được lưu đệm. `withDisplay: true` thêm tên theo ngôn ngữ của người gọi, email và avatar; mỗi loại dữ liệu tốn thêm tối đa một lần đọc. Không có tùy chọn này, kết quả có ID và cấp nhưng không có tên, email hay avatar.

`level` trong membership là cấp quản lý, không phải độ sâu của cây: `0` là nhân viên, `1` là quản lý cao nhất của phòng ban, `2` là cấp kế tiếp, và cứ thế. Phần 2 dùng giá trị này để tìm người duyệt.

### 3. Thử trên local

Đăng nhập bằng Project key khi CLI yêu cầu, rồi khởi động máy chủ local. `--allow-writes=false` mở session chỉ đọc; tùy chọn này bắt buộc với Project key chỉ đọc và đủ cho ví dụ này:

```bash
cogover-dev login --profile org_demo
cogover-dev doctor --profile org_demo
COGOVER_LOCAL_PORT=3100 cogover-dev run --profile org_demo --allow-writes=false -- npm run dev
```

Trên hệ thống không có kho lưu credential, như nhiều máy chủ Linux, `login` lưu Project key vào `.env` cạnh Workspace API key và thêm quy tắc bỏ qua vào `.gitignore`. Không đưa `.env` vào Git, và commit `.gitignore` đã được cập nhật.

Giữ terminal đó chạy. Mở terminal thứ hai và xem vị trí của bạn trong tổ chức:

```bash
curl -s -i 'http://127.0.0.1:3100/api/v1/ts-projects/org_demo/me'
```

Kết quả mong đợi là HTTP `200` với body tương tự như sau, đã được định dạng lại. Máy chủ local chạy dưới danh tính nhân sự được cấp Project key. ID và tên lấy từ Workspace của bạn; tài liệu này dùng một công ty ví dụ nhỏ xuyên suốt:

```json
{
  "personnelId": "PERGIANG",
  "name": "Hồ Giang",
  "memberships": [
    {
      "departmentId": "DEPQA",
      "department": "Phòng Kiểm thử",
      "position": "Phó phòng",
      "level": 2,
      "primary": true
    }
  ]
}
```

Nhân sự làm ở nhiều phòng ban có một membership cho mỗi phòng: phòng ban chính đứng đầu, sau đó theo thứ tự cây. `primary` chỉ bằng `true` khi Workspace đánh dấu phòng ban chính. Mảng `memberships` rỗng nghĩa là nhân sự chưa được gán vào phòng ban nào.

Xem danh sách phòng ban. `jq` định dạng response:

```bash
curl -s 'http://127.0.0.1:3100/api/v1/ts-projects/org_demo/departments' | jq
```

```json
{
  "departments": [
    { "id": "DEPBOARD", "name": "Hội đồng quản trị", "level": 1 },
    { "id": "DEPEXEC", "name": "Ban Giám đốc", "level": 2 },
    { "id": "DEPENG", "name": "Khối Kỹ thuật", "level": 3 },
    { "id": "DEPQA", "name": "Phòng Kiểm thử", "level": 4 },
    { "id": "DEPSALES", "name": "Phòng Kinh doanh", "level": 3 }
  ]
}
```

Mỗi phòng ban đứng sau phòng cha, các phòng con giữ thứ tự đã đặt trong Cogover. `jq` in mỗi field trên một dòng; kết quả ở trên đã được thu gọn.

Sao chép một `departmentId` từ response của `/me`, nên chọn phòng có cả đồng nghiệp, rồi xem thành viên của phòng đó. ID bất kỳ từ `/departments` cũng dùng được. Thay `{DEPARTMENT_ID}`:

```bash
curl -s 'http://127.0.0.1:3100/api/v1/ts-projects/org_demo/departments/{DEPARTMENT_ID}/members' | jq
```

```json
{
  "departmentId": "DEPQA",
  "total": 5,
  "members": [
    { "personnelId": "PERDUNG", "name": "Võ Dung", "position": "Trưởng phòng", "level": 1, "hasAccount": true },
    { "personnelId": "PERGIANG", "name": "Hồ Giang", "position": "Phó phòng", "level": 2, "hasAccount": true },
    { "personnelId": "PERHOA", "name": "Đỗ Hoa", "position": "Trưởng nhóm", "level": 3, "hasAccount": true },
    { "personnelId": "PERKHOA", "name": "Bùi Khoa", "position": "Kiểm thử viên", "level": 0, "hasAccount": true },
    { "personnelId": "PERMINH", "name": "Đặng Minh", "position": "Kiểm thử viên", "level": 0, "hasAccount": false }
  ]
}
```

Quản lý đứng trước theo cấp, sau đó là nhân viên. `hasAccount: false` là hồ sơ nhân sự chưa có tài khoản Workspace nên không đăng nhập được. `total` đếm mọi thành viên, kể cả ngoài 50 người đầu. Thay ID bằng `DEP-UNKNOWN` và thêm `-i` vào `curl` để thấy status `404`.

Máy chủ local dùng cơ cấu thật của Workspace qua Development Session. Bước thử này chưa cần version đã publish.

## Phần 2. Tìm người có quyền duyệt

### 4. Thêm route duyệt

Thêm hai route sau vào `src/main.ts`, ngay trên dòng `export default router.toHandler();`:

```typescript
router.get("/personnel/:personnelId/approvers", async ({ org, request, response }) => {
  const personnelId = request.params.personnelId ?? "";
  if (!ID_PATTERN.test(personnelId)) {
    return response.json({ error: "A valid personnel id is required" }, { status: 400 });
  }
  const chains = await org.personnel.managerChain(personnelId, { accountOnly: true, withDisplay: true });
  if (chains.length === 0) {
    return response.json({ error: "Personnel not found in any department" }, { status: 404 });
  }
  return {
    personnelId,
    chains: chains.map(chain => ({
      fromDepartmentId: chain.fromDepartmentId,
      personnelLevel: chain.personnelLevel,
      approvers: chain.tiers.map(tier => ({
        department: tier.departmentName ?? tier.departmentId,
        level: tier.level,
        distance: tier.distance,
        names: tier.personnel.map(person => person.display?.name ?? person.id),
      })),
      vacantDepartmentIds: chain.vacantDepartmentIds,
      truncated: chain.truncated,
    })),
  };
});

router.post("/approvals/check", async ({ org, invocation, request, response }) => {
  const body = (request.body ?? {}) as { ownerId?: unknown; departmentId?: unknown };
  const { ownerId, departmentId } = body;
  if (typeof ownerId !== "string" || !ID_PATTERN.test(ownerId)
      || (departmentId !== undefined && (typeof departmentId !== "string" || !ID_PATTERN.test(departmentId)))) {
    return response.json({ error: "A valid ownerId is required; departmentId is optional" }, { status: 400 });
  }
  const approverId = invocation.user?.membership.personnelId;
  if (approverId === undefined) {
    return response.json({ error: "This call has no signed-in personnel" }, { status: 403 });
  }
  const canApprove = await org.isManagerOf(approverId, ownerId,
    departmentId === undefined ? {} : { departmentId });
  return { approverId, ownerId, canApprove };
});
```

- `GET /personnel/:personnelId/approvers` trả các quản lý phía trên một nhân sự, gần nhất trước, lên tới cấp cao nhất của tổ chức. `org.personnel.managerChain` trả một chuỗi cho mỗi phòng ban của nhân sự và mảng rỗng khi nhân sự không tồn tại. `accountOnly: true` bỏ qua người chưa có tài khoản vì họ không thể duyệt.
- `POST /approvals/check` cho biết người gọi có quản lý người tạo yêu cầu hay không, ví dụ một đề nghị thanh toán. `org.isManagerOf` trả `true` khi người gọi nằm trong một chuỗi quản lý của người tạo; `departmentId` giới hạn việc kiểm tra vào chuỗi bắt đầu từ phòng ban đó.

Cả hai kết quả đều lấy từ bản cơ cấu đã lưu đệm. Chỉ `withDisplay` ở route đầu đọc thêm tên.

### 5. Thử danh sách người duyệt trên local

Máy chủ local tự khởi động lại khi bạn lưu `src/main.ts`. Chọn `personnelId` của một đồng nghiệp trong danh sách thành viên ở bước 3 rồi xem người duyệt của họ. Nhân viên (level `0`) có chuỗi dài nhất; nếu phòng ban chỉ có quản lý, các chuỗi sẽ ngắn hơn. Thay `{PERSONNEL_ID}`:

```bash
curl -s 'http://127.0.0.1:3100/api/v1/ts-projects/org_demo/personnel/{PERSONNEL_ID}/approvers' | jq
```

Với một kiểm thử viên trong công ty ví dụ:

```json
{
  "personnelId": "PERKHOA",
  "chains": [
    {
      "fromDepartmentId": "DEPQA",
      "personnelLevel": 0,
      "approvers": [
        { "department": "Phòng Kiểm thử", "level": 3, "distance": 0, "names": ["Đỗ Hoa"] },
        { "department": "Phòng Kiểm thử", "level": 2, "distance": 0, "names": ["Hồ Giang"] },
        { "department": "Phòng Kiểm thử", "level": 1, "distance": 0, "names": ["Võ Dung"] },
        { "department": "Khối Kỹ thuật", "level": 1, "distance": 1, "names": ["Phạm Chi"] },
        { "department": "Ban Giám đốc", "level": 2, "distance": 2, "names": ["Lê Bình"] },
        { "department": "Ban Giám đốc", "level": 1, "distance": 2, "names": ["Nguyễn An"] },
        { "department": "Hội đồng quản trị", "level": 1, "distance": 3, "names": ["Trần Linh"] }
      ],
      "vacantDepartmentIds": [],
      "truncated": false
    }
  ]
}
```

Đọc chuỗi từ trên xuống: `approvers[0]` là quản lý trực tiếp, mỗi tier sau cao hơn một bậc. `distance` đếm số phòng ban phía trên phòng xuất phát: `0` là phòng của chính người đó, `1` là phòng cha, và cứ thế. Nhiều người cùng cấp nằm chung một tier. Người quản lý nhiều phòng ban trên đường đi chỉ xuất hiện một lần, ở tier gần nhất, nên chuỗi có thể kết thúc dưới phòng ban cao nhất.

Giờ dùng `personnelId` của chính bạn từ `/me`. Mỗi chuỗi của bạn bắt đầu từ cấp cao hơn cấp của bạn trong phòng ban đó: phó phòng nhận trưởng phòng trước, trưởng phòng nhận các quản lý của phòng cha. Một chuỗi không có `approvers` khi người đó đứng đầu phòng xuất phát và không còn ai khác quản lý các phòng phía trên, như trưởng một phòng ban gốc hoặc CEO kiêm chủ tịch hội đồng quản trị. Cùng người đó vẫn có thể có người duyệt ở phòng ban mà họ giữ cấp thấp hơn.

`vacantDepartmentIds` liệt kê các phòng ban đi qua mà không ai duyệt được cho người này: không có quản lý nào có tài khoản ngoài chính người đó, hoặc ở phòng xuất phát thì không có ai cấp cao hơn người đó. Phòng của chính trưởng phòng không bao giờ bị liệt kê, và chuỗi tiếp tục với phòng cha của phòng trống. Người là quản lý duy nhất của một phòng cha, ví dụ CEO đồng thời là chủ tịch duy nhất của hội đồng quản trị, sẽ thấy phòng đó trong danh sách dù không thiếu ai. `truncated: true` nghĩa là một phòng cha đã ngừng hoạt động, nên chuỗi dừng trước khi tới cấp cao nhất thật.

Kiểm tra bạn có được duyệt yêu cầu của người khác không. Thay `{PERSONNEL_ID}` bằng ID của một đồng nghiệp:

```bash
curl -s -X POST 'http://127.0.0.1:3100/api/v1/ts-projects/org_demo/approvals/check' \
  -H 'Content-Type: application/json' \
  --data '{"ownerId":"{PERSONNEL_ID}"}'
```

```json
{ "approverId": "PERGIANG", "ownerId": "PERKHOA", "canApprove": true }
```

`canApprove` bằng `true` khi bạn nằm trong một chuỗi quản lý của người tạo. Trong ví dụ, phó phòng được duyệt cho kiểm thử viên nhưng không được duyệt cho trưởng phòng: với `"ownerId":"PERDUNG"`, `canApprove` bằng `false`. Không có `departmentId`, mọi phòng ban của người tạo đều được xét: ai quản lý người tạo ở bất kỳ phòng nào cũng nhận `true`, kể cả khi người tạo xếp trên họ ở phòng khác. Với yêu cầu thật, thêm `"departmentId":"{DEPARTMENT_ID}"` là phòng ban của yêu cầu, để chỉ xét chuỗi bắt đầu từ phòng đó. Phòng ban mà người tạo không thuộc về sẽ cho `false`. Thử gửi `{}` để kiểm tra dữ liệu đầu vào; route trả `400`.

### 6. Publish và activate

Nhấn Ctrl+C để dừng máy chủ local. Tại thư mục dự án, chạy:

```bash
npm run build
cogover-dev publish
```

Khi version ở trạng thái `READY`, activate bằng version ID mà CLI trả về:

```bash
cogover-dev activate {VERSION_ID}
```

Các route chỉ đọc cơ cấu tổ chức nên Project không cần identity policy cho ví dụ này.

### 7. Gọi Project đã publish

Tạo file Workspace session bằng CLI, rồi gọi `/me` trên version đang active. CLI cũng thêm file session vào `.gitignore`. CLI không bao giờ ghi đè file đã có, nên hãy xóa `.cogover-session.curl` cũ trước, ví dụ khi session đã hết hạn. Thay `{WORKSPACE_DOMAIN}`:

```bash
cogover-dev auth session --format curl --output .cogover-session.curl
curl -s --config .cogover-session.curl \
  'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/org_demo/me' \
  -H 'x-req-type: 9' -H 'x-req-service: 3' | jq '.'
```

Response chính là kết quả của route, với các field giống bước 3. Session thuộc về người dùng của Workspace API key, nên `/me` hiển thị nhân sự của người dùng đó. Nhân sự này có thể khác nhân sự được cấp Project key.

Chạy kiểm tra quyền duyệt dưới danh tính người dùng đó. Thay `{PERSONNEL_ID}`:

```bash
curl -s --config .cogover-session.curl -X POST \
  'https://{WORKSPACE_DOMAIN}/api/v1/ts-projects/org_demo/approvals/check' \
  -H 'x-req-type: 9' -H 'x-req-service: 3' \
  -H 'Content-Type: application/json' --data '{"ownerId":"{PERSONNEL_ID}"}' | jq '.'
```

Kết quả có các field như ở bước 5, với `approverId` là nhân sự của người dùng trong session.

### 8. Dọn dữ liệu thử

Xóa file session khi thử xong:

```bash
rm -f .cogover-session.curl
```

Ví dụ không ghi dữ liệu nào. Deactivate Project trong Cogover nếu không cần dùng nữa.

## Dữ liệu cấu trúc và dữ liệu hiển thị

| Dữ liệu cần đọc | Chi phí |
|---|---|
| ID, cây phòng ban, membership, cấp quản lý, vị trí, chuỗi quản lý | Trả từ bản cơ cấu đã lưu đệm; không đọc record nào. |
| Tên, email, avatar và mã nhân sự (`withDisplay: true`) | Tối đa thêm một lần đọc cho mỗi loại dữ liệu (nhân sự, phòng ban, vị trí) và mỗi 200 ID; giá trị vừa đọc được dùng lại. |
| Field nhân sự khác, như số điện thoại hoặc field tùy chỉnh | Đọc Object `personnel` bằng `data.object("personnel")`, có áp dụng quyền record. |

`withDisplay` thêm `display` vào nhân sự, phòng ban và vị trí, thêm `departmentName`/`positionName` vào membership. Giá trị hiển thị bằng `null` khi không đọc được record tương ứng, ví dụ record vừa bị xóa. Dữ liệu hiển thị chỉ gồm các field trên và mọi thành viên Workspace đều xem được, giống ô chọn người dùng.

Tên phòng ban và vị trí mặc định theo ngôn ngữ của người gọi: ngôn ngữ trong Workspace membership của người dùng, rồi của người dùng, rồi của Workspace. Truyền `language`, ví dụ `"vi-VN"` hoặc `"en-US"`, để chọn bản dịch khác. Nếu không có bản dịch phù hợp, Cogover dùng tên đã lưu.

Thay đổi trong Cogover, như thêm phòng ban hoặc chuyển nhân sự, hiển thị sau vài giây. Mọi lời gọi `org` trong một lần chạy đọc cùng một phiên bản cơ cấu, nên một request không bao giờ trộn hai phiên bản.

## Cách dựng chuỗi quản lý

`level` trong membership đánh dấu quản lý: `0` là nhân viên, `1` là cấp quản lý cao nhất của phòng ban, `2` là cấp kế tiếp. Nhiều người có thể cùng cấp.

1. Trong phòng xuất phát, quản lý là những người có số cấp nhỏ hơn cấp của nhân sự, gần nhất trước. Nhân viên (`0`) nhận mọi quản lý của phòng. Trưởng phòng (`1`) không có quản lý nào trong phòng mình.
2. Mỗi phòng cha tới cấp cao nhất thêm mọi quản lý của nó, số cấp lớn trước. Mọi quản lý của phòng cha đứng trên mọi quản lý của các phòng con.
3. Mỗi nhân sự chỉ xuất hiện một lần, ở tier gần nhất; nhân sự xuất phát không bao giờ xuất hiện.
4. `accountOnly: true` bỏ qua nhân sự chưa có tài khoản Workspace.
5. `vacantDepartmentIds` liệt kê các phòng ban đi qua mà không có quản lý hợp lệ. Quản lý hợp lệ là người không phải nhân sự xuất phát, có tài khoản nếu dùng `accountOnly`, và nếu ở phòng xuất phát thì có cấp cao hơn nhân sự đó. Quản lý đã xuất hiện ở tier gần hơn vẫn được tính, nên phòng đó không bị coi là trống. Phòng của trưởng phòng không bị coi là trống.
6. `truncated` bằng `true` khi một phòng cha đã ngừng hoạt động, nên chuỗi dừng trước cấp cao nhất thật.

Các hàm liên quan:

| Hàm | Trả về |
|---|---|
| `org.personnel.managerChain(id, options?)` | Một chuỗi cho mỗi phòng ban của nhân sự, phòng chính trước, sau đó theo thứ tự cây. `departmentId` chỉ giữ chuỗi bắt đầu từ phòng đó. |
| `org.departments.managerChain(id, options?)` | Chuỗi phía trên một nhân viên của phòng ban đó. |
| `org.departments.managers(id, options?)` | Chỉ các quản lý của phòng ban đó, mỗi cấp một tier, cấp `1` trước. |
| `org.isManagerOf(managerId, personnelId, options?)` | `managerId` có nằm trong một chuỗi của `personnelId` hay không. `directOnly: true` chỉ xét tier gần nhất. |
| `org.isInDepartment(personnelId, departmentId, options?)` | Nhân sự có thuộc phòng ban hay không, hoặc thuộc một phòng con khi có `includeSubDepartments: true`. |

## Nơi dùng được `org`

`org` có trong route, script, record trigger ở cả hai thời điểm, background job và Development Session trên local. Quyền đọc theo danh tính của lần chạy:

| Lần chạy | Đọc được `org` | `org.me()` |
|---|---|---|
| Người dùng đăng nhập gọi, Preview hoặc Development Session trên local | Có | Nhân sự của người gọi |
| Record trigger do thay đổi của người dùng | Có | Người đã thực hiện thay đổi |
| Background job, inbound webhook hoặc record trigger do thay đổi của hệ thống | Chỉ khi identity policy đã duyệt có `allowInternalSystem: true` | `null` |

Không có policy đó, mọi lời gọi `org` trong lần chạy không có người dùng đều ném `PermissionDeniedError` với `details.reason` là `"IDENTITY_NOT_GRANTED"`. Duyệt policy cho từng version mới publish. Xem [tài liệu identity policy](custom-backend-module-api-reference.md#identity-policy-1).

## Kết quả và lỗi

| Tình huống | Kết quả |
|---|---|
| `get` với ID không tồn tại | `null` |
| `getMany` với ID không tồn tại | Liệt kê trong `missingIds` |
| `personnel.managerChain` với nhân sự không tồn tại | Mảng rỗng |
| `isInDepartment` hoặc `isManagerOf` với ID không tồn tại | `false` |
| `departments.members`, `managers`, `managerChain` của phòng ban, `ancestors` hoặc `tree({ rootId })` với phòng ban không tồn tại, hoặc `positions.members` với vị trí không tồn tại | `NotFoundError`, `resource` là `"department"` hoặc `"position"` |
| ID hoặc tùy chọn không hợp lệ, hoặc cây có hơn 5.000 phòng ban | `ValidationError` |
| Lần chạy không có người dùng và không có policy ở trên | `PermissionDeniedError` |
| Tạm thời không đọc được cơ cấu | `CogoverApiError` với code `ORGANIZATION_UNAVAILABLE`; nếu không bắt lỗi, người gọi nhận HTTP `503` |

Kích thước trang: `members` mặc định trả 500 phần tử, tối đa 2.000; khi có `withDisplay`, mặc định và tối đa đều là 200. Truyền `nextCursor` vào `cursor` để đọc trang tiếp theo. Dùng `getMany` hoặc `members` thay vì gọi `get` trong vòng lặp: mỗi lời gọi là một request riêng tới Cogover.

## Xử lý sự cố

| Vấn đề | Cần kiểm tra |
|---|---|
| `npm run build` báo `org` không tồn tại | Cài SDK từ 0.11.0 bằng `npm install @cogover/sdk@latest`. |
| `PERMISSION_DENIED` khi khởi động máy chủ local | Project key chỉ đọc cần `--allow-writes=false`. |
| `/me` trả `403` | Lời gọi không có người dùng đăng nhập, hoặc người dùng đó không có nhân sự đang hoạt động trong Workspace này. |
| `memberships` rỗng | Gán nhân sự vào một phòng ban trong Cogover. |
| Route thành viên hoặc người duyệt trả `404` | Dùng ID phòng ban hoặc nhân sự đang hoạt động của Workspace này. |
| Tên bằng `null` | Record đã bị xóa hoặc không đọc được; các field cấu trúc vẫn đúng. |
| Tên sai ngôn ngữ | Truyền `language` hoặc thêm bản dịch trong Cogover. |
| `approvers` rỗng | Bình thường khi nhân sự đứng đầu phòng xuất phát và không còn ai khác quản lý các phòng phía trên; các phòng đó, nếu có, được liệt kê trong `vacantDepartmentIds`. Các trường hợp khác, xem `truncated` và `vacantDepartmentIds`. |
| `PermissionDeniedError` trong job, inbound webhook hoặc trigger | Duyệt identity policy có `allowInternalSystem: true` cho version đang active. |
| HTTP `503` với `ORGANIZATION_UNAVAILABLE` | Lỗi tạm thời; thử lại sau. |
| Chưa thấy thay đổi vừa làm | Chờ vài giây rồi gửi lại request. |

## Đọc thêm

- [API cơ cấu tổ chức của SDK](cogover-sdk-api-reference.md#cơ-cấu-tổ-chức): mọi hàm, tùy chọn và kiểu dữ liệu.
- [Bắt đầu với record trigger](get-started-record-trigger.md): kiểm tra record dựa trên cơ cấu tổ chức trước khi lưu.
- [Background job](get-started-background-jobs.md): chạy việc dài, như gửi thông báo cho từng người duyệt, bên ngoài request.
