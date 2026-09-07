# Cogover Skills

**English** | [Tiếng Việt](README.vi.md)

A collection of 22 Agent Skills that help AI assistants explore and configure Cogover Workspaces, design data models, build workflows, and develop Custom Modules. Each skill includes a `SKILL.md` file along with the API documentation, scripts, or sample data it needs.

For the current release, see [VERSION.md](VERSION.md) and [CHANGELOG.md](CHANGELOG.md). Each skill has its own version in its frontmatter and below its heading.

## Choose a skill

| Need | Skill |
|---|---|
| Understand the platform and choose the right capabilities | [cogover-overview](cogover-overview/SKILL.md) |
| Coordinate an App project from requirements to deployment | [build-cogover-app](build-cogover-app/SKILL.md) |
| Authenticate API requests and manage credentials | [cogover-api-auth](cogover-api-auth/SKILL.md) |
| Build custom frontends and backends | [cogover-custom-module](cogover-custom-module/SKILL.md) |
| Design schemas in Excel | [create-cogover-objects](create-cogover-objects/SKILL.md) |
| Look up and manage Objects, fields, and formulas | [object-info](object-info/SKILL.md) |
| Read and write records, files, and rich text images | [object-record](object-record/SKILL.md) |
| Configure Object layouts | [object-layout](object-layout/SKILL.md) |
| Write scripts for interface logic | [layout-scripting](layout-scripting/SKILL.md) |
| Configure Buttons and action chains | [object-button](object-button/SKILL.md) |
| Configure filters and list columns | [object-filter](object-filter/SKILL.md) |
| Create forms for collecting external submissions | [object-form](object-form/SKILL.md) |
| Configure status transition rules | [object-transition-rule](object-transition-rule/SKILL.md) |
| Provide stage guidance with a Path Component | [object-path-component](object-path-component/SKILL.md) |
| Configure field history tracking | [object-history-tracking](object-history-tracking/SKILL.md) |
| Manage members, organizational structure, roles, and data permissions | [user-permission](user-permission/SKILL.md) |
| Build and test Process/BPMN workflows | [process-creator](process-creator/SKILL.md) |
| Create Word, Excel, and HTML templates and export documents | [document-template](document-template/SKILL.md) |
| Configure Report Types and reports | [report-builder](report-builder/SKILL.md) |
| Configure dashboards and charts | [dashboard-builder](dashboard-builder/SKILL.md) |
| Manage Apps and menus | [app-menu-manager](app-menu-manager/SKILL.md) |
| Manage Button and App Menu icons | [cogover-icon](cogover-icon/SKILL.md) |

## Install and update

Download or clone this repository. Each subdirectory containing a `SKILL.md` file is a skill; keep all accompanying `references`, `scripts`, `assets`, and `agents` directories intact. Installing the full collection is recommended because the skills reference one another and share the same authentication contract.

In Codex, you can ask `$skill-installer` to install the skill directories from the published repository URL. Alternatively, copy the directories into the skill location configured for your environment; Codex supports repository-level `.agents/skills` directories and a user-level skills directory. Restart Codex if changes do not appear. See the [official guide](https://learn.chatgpt.com/docs/build-skills).

For other agents that support `SKILL.md`, follow their skill installation instructions; invocation syntax and available tools may differ. This collection does not install a browser, spreadsheet libraries, or a sub-agent runtime automatically.

When updating, compare versions, back up your customizations, and replace **each entire skill directory with the same name** so that obsolete resources are removed. Do not mix versions of the same skill or overwrite skills outside this collection. To uninstall, remove only the installed Cogover directories listed above, not the shared skills directory.

## Requirements

| Capability | When needed |
|---|---|
| Read skills and references, and make HTTP requests | All API operations |
| An HTTPS Workspace and credentials with appropriate permissions | Exploring or modifying a Workspace |
| A shell and Python 3.10+ | Included API scripts and validators, which use only the standard library |
| Read and write XLSX files, and inspect their contents and formatting | Object design, report artifacts, and document templates |
| A browser with an active Workspace session and download tracking | Testing document exports and frontends |
| Sub-agents and artifacts with defined scopes | Required orchestration steps for Apps and Custom Modules |
| Node.js, Cogover Dev CLI, and starter dependencies | Custom Modules; read the relevant documentation before installing |

Prefer the spreadsheet and browser skills available in your environment. If no spreadsheet skill is available, use equivalent XLSX tools and run the validator. If a required browser or sub-agent capability is missing, the agent must identify what it could not verify or perform; it must not fabricate a successful test result.

## Workspace and authentication

The authoritative reference is [cogover-api-auth](cogover-api-auth/SKILL.md). An example origin is `https://tenant.example.com`. `COGOVER_BASE_URL` and `COGOVER_API_KEY` are the shared variable names; some examples support compatibility names explained in the authentication skill. Supply keys through a secret store or a scoped process environment, never through repository files or prompts.

| API group | Authentication | Scope |
|---|---|---|
| Public API `/bapi/v{N}` | Bearer API Key | The endpoint contract and permissions documented in the skill |
| Web App API `/api/v{N}` | A Web App session with cookies and CSRF/XSRF | Use when the skill documents a contract for that capability; do not send an API Key directly |

An API Key must have the permissions required for the operation; do not assume every task requires Super Admin access. Before making changes, the agent reads the current state, determines the scope, and follows the skill's approval requirements. A successful HTTP response does not prove that the intended business change is correct; read the result back and run appropriate tests.

The skill collection version is separate from the Cogover server version. Web App API capabilities may depend on the Workspace version. Use only documented endpoints; if a response does not match the contract, report the documentation gap instead of inspecting private source code or guessing endpoints.

## Get started

```text
Use $cogover-overview to explain how to manage purchase requests in Cogover.
```

```text
Use $object-info to list the fields of the order Object in my configured Workspace.
Only read information and identify the fields needed for a monthly report.
```

```text
Use $build-cogover-app to analyze warranty management requirements, explore my
configured Workspace, and prepare a design for my approval before implementation.
```

## Sample data and validation

Example IDs and domains are synthetic and must not be used directly in Workspace requests. Resolve IDs, slugs, and resources from the target metadata. A response snapshot is not necessarily a valid request payload. Read the [Process sample conventions](process-creator/samples/README.md) and use the relevant validator.

From the repository root:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/check_public_release.py
python3 -m unittest discover -s tests
```

Before publishing a repository that already has commits, add `--history` to scan the content of versions stored in Git. These checks do not replace live API and business behavior tests. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

Content provided by this project is licensed under [MIT](LICENSE), except for third-party assets listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The two completion SVGs retain their Font Awesome Free/CC BY 4.0 license and attribution.
