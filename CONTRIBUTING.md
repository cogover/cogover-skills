# Contributing to Cogover Skills

Thank you for helping improve Cogover Skills. Contributions can include clearer instructions, corrected API examples, fixes to scripts, improved translations, and new skills.

## Report an issue or suggest an improvement

Open an [issue](https://github.com/cogover/cogover-skills/issues) with the affected skill and version, what you expected, and what happened. Include a small, anonymized example when possible. For a new skill or a substantial change, describe the proposed scope in an issue before starting implementation.

Never include API keys, session cookies, webhook secrets, customer data, or real Workspace responses. Use synthetic examples and domains such as `example.com`. For security concerns, follow [SECURITY.md](SECURITY.md) rather than posting sensitive details in a public issue.

## Prepare a pull request

1. Fork the repository and create a branch for your change.
2. Read the affected skill's `SKILL.md` and relevant references.
3. Make a focused change, updating related examples and documentation together.
4. Run the checks below and review the files included in your commit.
5. Open a pull request describing the problem, the resulting behavior, and how you verified it. State any behavior that still needs testing against a Workspace.

Instructions and examples should be understandable without access to private Cogover source code or infrastructure. Use documented APIs, the product interface, and metadata available to the Workspace user. Do not infer undocumented behavior from private implementation details.

## Repository structure

Each skill lives in a directory at the repository root. Its directory name must match `name` in the `SKILL.md` frontmatter. Keep supporting documentation in `references/`, executable helpers in `scripts/`, sample assets in `assets/`, and agent metadata in `agents/` where applicable.

Keep instructions focused on the skill's scope, and link to supporting references instead of duplicating long explanations. Resolve resource links relative to the document containing them. When editing the repository README, keep [English](README.md) and [Vietnamese](README.vi.md) content consistent.

## Versions

Each `SKILL.md` declares `metadata.author` and `metadata.version` in its frontmatter. The visible `Phiên bản` value below the heading must match that version, and `Ngày phát hành` uses `YYYY-MM-DD`.

When changing a skill or any resource within its directory:

- Increase that skill's version and set its release date to the date of the change.
- Use a PATCH increase for compatible fixes, MINOR for compatible additions, and MAJOR for incompatible changes.
- Increase the collection version and update the release date in the root `VERSION.md` once per changeset, even when several skills change.
- Leave versions of unaffected skills unchanged.

Changes limited to repository documentation or validation infrastructure do not require a skill version increase.

## Run checks

Use Python 3.10 or later. From the repository root:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests
python3 scripts/check_public_release.py --history
```

To verify version changes against the branch you started from, use its commit or ref, for example:

```bash
python3 scripts/check_public_release.py --base-ref origin/main
```

The checks inspect public files, references, metadata, sample data, and Git history. They also validate the included Object workbook and BPMN sample geometry. Files excluded by Git cannot satisfy public documentation links or required files.

These checks do not exercise live Workspace APIs. When a change affects API behavior, test it in a Workspace you are authorized to use and describe the results without sharing credentials or sensitive data. Clearly distinguish syntax and fixture checks from live behavior tests. Automated CI must not depend on access to a real Workspace.

## Samples and assets

Use synthetic IDs consistently across JSON, embedded JSON strings, and BPMN XML. A response example is not automatically a valid request payload; document its intended use.

Before adding documents or images, review their contents and embedded metadata, including spreadsheet comments and author information. Do not include backups, environment files, session exports, or generated caches.

Only contribute material you have the right to distribute. Project contributions use the [MIT license](LICENSE); third-party material must retain its applicable license, attribution, and notices in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
