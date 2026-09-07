#!/usr/bin/env python3
"""Read-only release checks. Never print matched secrets or call Workspace APIs."""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import yaml

TEXT_SUFFIXES = {'.md', '.json', '.yaml', '.yml', '.py', '.svg', '.txt', '.toml'}
PRIVATE_NAMES = {'AGENTS.md', 'CLAUDE.md', '.DS_Store'}
PREFIXES = 'AC|AT|BU|DC|DE|DO|FI|FL|JO|LE|LO|NC|NO|OF|OP|OS|OT|PE|PI|PO|PR|RL|RO|RQ|RS|SC|SL|SR|TI|TR|US|WH|WS'
OPAQUE_ID = re.compile(r'(?<![A-Za-z0-9])(?:' + PREFIXES + r')[A-Za-z0-9]{8,23}(?![A-Za-z0-9])')
SYNTHETIC_ID = re.compile(r'0000|SAMPLE|EXAMPLE|XXXX')
SECRET_PATTERNS = {
    'JWT': re.compile(r'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}'),
    'PRIVATE_KEY': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'PROVIDER_TOKEN': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{25,}|AKIA[A-Z0-9]{16}|xox[baprs]-[A-Za-z0-9-]{20,})'),
    'PERSONAL_PATH': re.compile(r'/(?:Users|home)/[^\s/"<>]+/'),
    'PRIVATE_SOURCE_REFERENCE': re.compile(r'/path/to/private[/]source|contract\s+nội\s+bộ|Source\s+UI'),
}
UUID = re.compile(r'\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b', re.I)
EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b')
TENANT = re.compile(r'https?://([a-z0-9-]+)\.cogover\.(?:net|com)\b', re.I)
SECRET_KEY = re.compile(r'^(?:secret(?:AllVersions|Key|Token)?|api[_-]?key|access[_-]?token|refresh[_-]?token|password|basicPassword|authorization|cookie)$', re.I)


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True)


def scan_text(text: str, label: str) -> list[str]:
    issues = []
    for code, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(text):
            issues.append(f'{label}:{text.count(chr(10), 0, match.start()) + 1}: {code} (value redacted)')
    for match in EMAIL.finditer(text):
        domain = match.group(1).lower()
        if not any(domain == d or domain.endswith('.' + d) for d in ('example.com', 'example.org', 'example.net')):
            issues.append(f'{label}: NON_EXAMPLE_EMAIL (value redacted)')
    for match in TENANT.finditer(text):
        # Public example origin used in the repository README.
        if match.group(0).lower() == 'https://tennant.cogover.com':
            continue
        if match.group(1).lower() not in {'www', 'docs', 'help', 'developer', 'developers'}:
            issues.append(f'{label}: CONCRETE_WORKSPACE_HOST (value redacted)')
    for match in OPAQUE_ID.finditer(text):
        value = match.group()
        if any(c.isdigit() for c in value) and not SYNTHETIC_ID.search(value):
            issues.append(f'{label}: NON_SYNTHETIC_ID (value redacted)')
    for match in UUID.finditer(text):
        if not match.group().startswith('00000000-'):
            issues.append(f'{label}: NON_SYNTHETIC_UUID (value redacted)')
    return sorted(set(issues))


def scan_json(value, label: str) -> list[str]:
    issues = []
    if isinstance(value, dict):
        for key, item in value.items():
            if SECRET_KEY.fullmatch(key) and isinstance(item, str) and item:
                placeholder = re.search(r'[<{]|\$|SAMPLE|EXAMPLE|runtime credential|your[_ -]', item, re.I)
                if not placeholder:
                    issues.append(f'{label}: NON_PLACEHOLDER_CREDENTIAL (value redacted)')
            issues.extend(scan_json(item, label))
    elif isinstance(value, list):
        for item in value:
            issues.extend(scan_json(item, label))
    elif isinstance(value, str) and value.lstrip().startswith(('{', '[')):
        try:
            issues.extend(scan_json(json.loads(value), label))
        except (ValueError, RecursionError):
            pass
    return sorted(set(issues))


def scan_blob(data: bytes, label: str) -> list[str]:
    issues = []
    if data.startswith(b'PK\x03\x04'):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for entry in archive.infolist():
                    if entry.file_size > 20_000_000:
                        issues.append(f'{label}: ARCHIVE_ENTRY_TOO_LARGE_FOR_SCAN')
                        continue
                    name = entry.filename
                    payload = archive.read(name)
                    if re.search(r'(?:comments\d*\.xml|threadedComments/|persons/|vmlDrawing|vmldrawing)', name):
                        issues.append(f'{label}: OFFICE_COMMENT_OR_AUTHOR_PART')
                    if name.endswith(('.xml', '.rels')):
                        try:
                            element = ET.fromstring(payload)
                            issues.extend(scan_text(' '.join(element.itertext()), label + ' [Office text]'))
                        except ET.ParseError:
                            issues.append(f'{label}: INVALID_OFFICE_XML')
                    issues.extend(scan_text(payload.decode('utf-8', 'ignore'), label + ' [archive]'))
        except (zipfile.BadZipFile, RuntimeError):
            issues.append(f'{label}: UNREADABLE_ARCHIVE')
    else:
        text = data.decode('utf-8', 'ignore')
        issues.extend(scan_text(text, label))
        if text.lstrip().startswith(('{', '[')):
            try:
                issues.extend(scan_json(json.loads(text), label))
            except (ValueError, RecursionError):
                pass
    return sorted(set(issues))


def version_tuple(value) -> tuple[int, int, int]:
    if not isinstance(value, str) or not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError('version must be a quoted MAJOR.MINOR.PATCH string')
    return tuple(map(int, value.split('.')))


def frontmatter(text: str) -> dict:
    if not text.startswith('---\n'):
        raise ValueError('missing frontmatter')
    return yaml.safe_load(text.split('---', 2)[1])


def release_version(text: str) -> str:
    match = re.search(r'Version:\s*`([^`]+)`', text)
    if not match:
        raise ValueError('missing release version')
    version_tuple(match.group(1))
    return match.group(1)


def check_versions(root: Path, skills: list[Path]) -> list[str]:
    issues = []
    today = dt.date.today()
    for skill in skills:
        label = skill.name + '/SKILL.md'
        try:
            text = (skill / 'SKILL.md').read_text()
            fm = frontmatter(text)
            metadata = fm.get('metadata', {})
            version = metadata.get('version')
            version_tuple(version)
            if fm.get('name') != skill.name or not fm.get('description') or not metadata.get('author'):
                raise ValueError('missing or inconsistent name/description/author')
            visible = re.search(r'\*\*Phiên bản:\*\*\s*`([^`]+)`', text)
            date = re.search(r'\*\*Ngày phát hành:\*\*\s*`([^`]+)`', text)
            if not visible or visible.group(1) != version or not date:
                raise ValueError('version display/date missing or inconsistent')
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date.group(1)) or dt.date.fromisoformat(date.group(1)) > today:
                raise ValueError('invalid release date')
        except (ValueError, KeyError, TypeError, AttributeError, yaml.YAMLError) as error:
            issues.append(f'{label}: METADATA_ERROR ({type(error).__name__})')
    try:
        release = (root / 'VERSION.md').read_text()
        release_version(release)
        date = re.search(r'Release date:\s*`([^`]+)`', release).group(1)
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date) or dt.date.fromisoformat(date) > today:
            raise ValueError('invalid release date')
    except (ValueError, AttributeError, OSError):
        issues.append('VERSION.md: INVALID_RELEASE_METADATA')
    return issues


def check_changes(root: Path, baseline: str, files: list[str]) -> list[str]:
    listing = git(root, 'ls-tree', '-r', '--name-only', baseline)
    if listing.returncode:
        return ['BASE_REF_UNAVAILABLE']
    old_files = set(listing.stdout.decode().splitlines())
    old_skills = {str(Path(p).parent) for p in old_files if p.count('/') == 1 and p.endswith('/SKILL.md')}
    current_skills = {p.name for p in root.iterdir() if p.is_dir() and (p / 'SKILL.md').is_file()}
    changed = set()
    issues = []
    for name in old_skills | current_skills:
        names = {p for p in old_files | set(files) if p.startswith(name + '/')}
        for path in names:
            previous = git(root, 'show', baseline + ':' + path)
            current = root / path
            if previous.returncode or not current.is_file() or previous.stdout != current.read_bytes():
                changed.add(name)
                break
    for name in changed & old_skills & current_skills:
        old = frontmatter(git(root, 'show', baseline + ':' + name + '/SKILL.md').stdout.decode())
        new_text = (root / name / 'SKILL.md').read_text()
        new = frontmatter(new_text)
        if version_tuple(new['metadata']['version']) <= version_tuple(old['metadata']['version']):
            issues.append(name + ': SKILL_VERSION_NOT_BUMPED')
        old_text = git(root, 'show', baseline + ':' + name + '/SKILL.md').stdout.decode()
        old_date = re.search(r'\*\*Ngày phát hành:\*\*\s*`([^`]+)`', old_text)
        new_date = re.search(r'\*\*Ngày phát hành:\*\*\s*`([^`]+)`', new_text)
        if not new_date or (old_date and new_date.group(1) < old_date.group(1)):
            issues.append(name + ': SKILL_DATE_REGRESSED')
    if changed:
        previous = git(root, 'show', baseline + ':VERSION.md')
        current = (root / 'VERSION.md').read_text()
        if previous.returncode == 0 and version_tuple(release_version(current)) <= version_tuple(release_version(previous.stdout.decode())):
            issues.append('VERSION.md: RELEASE_VERSION_NOT_BUMPED')
        if previous.returncode == 0:
            old_date = re.search(r'Release date:\s*`([^`]+)`', previous.stdout.decode())
            new_date = re.search(r'Release date:\s*`([^`]+)`', current)
            if not new_date or (old_date and new_date.group(1) < old_date.group(1)):
                issues.append('VERSION.md: RELEASE_DATE_REGRESSED')
    return issues


def history_checks(root: Path) -> tuple[list[str], int]:
    if git(root, 'rev-parse', '--verify', 'HEAD').returncode:
        return [], 0
    revisions = git(root, 'rev-list', '--objects', '--all')
    issues, count = [], 0
    for line in revisions.stdout.splitlines():
        parts = line.split(b' ', 1)
        oid = parts[0].decode()
        if git(root, 'cat-file', '-t', oid).stdout.strip() != b'blob':
            continue
        count += 1
        # Object id locates a historic finding without printing sensitive filenames.
        label = 'git-blob:' + oid[:12]
        data = git(root, 'cat-file', 'blob', oid).stdout
        issues.extend(scan_blob(data, label))
        if len(parts) == 2:
            name = parts[1].decode('utf-8', 'replace')
            if Path(name).name in PRIVATE_NAMES or Path(name).suffix == '.pyc' or Path(name).name == '.env':
                issues.append(label + ': PRIVATE_OR_CACHE_FILE_IN_HISTORY')
    return issues, count


def is_public_path(root: Path, path: Path, files: set[str]) -> bool:
    """An existing ignored file cannot satisfy a public package dependency."""
    try:
        name = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return False
    if path.is_file():
        return name in files
    if path.is_dir():
        prefix = '' if name == '.' else name + '/'
        return any(item.startswith(prefix) for item in files)
    return False


def check(root: Path, baseline: str | None = None, history: bool = False) -> tuple[list[str], dict]:
    listing = git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z')
    if listing.returncode:
        return ['NOT_A_GIT_WORKTREE'], {}
    files = sorted(set(p.decode() for p in listing.stdout.split(b'\0') if p))
    public_files = set(files)
    issues = []
    skills = sorted(p for p in root.iterdir() if p.is_dir() and (p / 'SKILL.md').is_file())
    for required in ['README.md', 'LICENSE', 'CONTRIBUTING.md', 'SECURITY.md', 'THIRD_PARTY_NOTICES.md', 'CHANGELOG.md', 'VERSION.md']:
        if not (root / required).is_file() or not is_public_path(root, root / required, public_files):
            issues.append(required + ': REQUIRED_FILE_MISSING')
    for name in files:
        p = root / name
        if not p.is_file():
            continue  # tracked deletion, not part of the new package
        if p.name in PRIVATE_NAMES or p.suffix == '.pyc' or '__pycache__' in p.parts or p.name == '.env' or (p.name.startswith('.env.') and p.name != '.env.example'):
            issues.append(name + ': PRIVATE_OR_CACHE_FILE_IN_RELEASE')
        data = p.read_bytes()
        issues.extend(scan_blob(data, name))
        try:
            if p.suffix == '.json':
                issues.extend(scan_json(json.loads(data), name))
            elif p.suffix in {'.yaml', '.yml'}:
                yaml.safe_load(data)
            elif p.suffix == '.py':
                ast.parse(data)
            elif p.suffix == '.svg':
                ET.fromstring(data)
        except (ValueError, SyntaxError, ET.ParseError, yaml.YAMLError):
            issues.append(name + ': INVALID_SYNTAX')
        if p.suffix == '.md':
            # Ignore fenced code and regex examples when checking actual links.
            text = re.sub(r'```.*?```', '', data.decode(), flags=re.S)
            text = re.sub(r'`[^`\n]*`', '', text)
            for target in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)', text):
                target = target.split('#')[0]
                if target and ':' not in target and not is_public_path(root, p.parent / target, public_files):
                    issues.append(name + ': BROKEN_RELATIVE_LINK')
            for target in re.findall(r'`(skills/[a-z-]+/[^`]+)`', text):
                if not (root / target).exists():
                    issues.append(name + ': STALE_RESOURCE_PATH')
    issues.extend(check_versions(root, skills))
    if baseline:
        try:
            issues.extend(check_changes(root, baseline, files))
        except (ValueError, KeyError, TypeError, yaml.YAMLError):
            issues.append('BASELINE_METADATA_ERROR')
    samples = sorted((root / 'process-creator/samples').glob('*.json'))
    for sample in samples:
        result = subprocess.run([sys.executable, str(root / 'process-creator/scripts/validate_bpmn_geometry.py'), str(sample), '--mode', 'response'], capture_output=True)
        if result.returncode:
            issues.append(str(sample.relative_to(root)) + ': BPMN_GEOMETRY_FAILED')
    result = subprocess.run([sys.executable, str(root / 'create-cogover-objects/scripts/validate_record_name.py'), str(root / 'create-cogover-objects/assets/Objects_for_CRM.xlsx')], capture_output=True)
    if result.returncode:
        issues.append('Objects_for_CRM.xlsx: RECORD_NAME_VALIDATION_FAILED')
    history_count = 0
    if history:
        found, history_count = history_checks(root)
        issues.extend(found)
    return sorted(set(issues)), {'public_files': len(files), 'skills': len(skills), 'bpmn_samples': len(samples), 'history_blobs': history_count}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--base-ref', help='Compare changed skill/release versions with this commit')
    parser.add_argument('--history', action='store_true', help='Scan all reachable Git blobs, including Office packages')
    args = parser.parse_args()
    issues, counts = check(args.root.resolve(), args.base_ref, args.history)
    print(json.dumps({'ok': not issues, **counts, 'issues': issues}, ensure_ascii=False, indent=2))
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
