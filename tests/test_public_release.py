import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
import io
import datetime as dt
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release', Path(__file__).resolve().parents[1] / 'scripts/check_public_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def test_release_day_uses_vietnam_midnight(self):
        cases = [
            ('2026-09-10T16:59:59+00:00', '2026-09-10'),
            ('2026-09-10T17:00:00+00:00', '2026-09-11'),
            ('2026-09-11T00:00:00+00:00', '2026-09-11'),
        ]
        for timestamp, expected in cases:
            instant = dt.datetime.fromisoformat(timestamp)
            with self.subTest(timestamp=timestamp), patch.object(release.dt, 'datetime') as clock:
                clock.now.side_effect = lambda tz: instant.astimezone(tz)
                self.assertEqual(release.release_today().isoformat(), expected)

    def test_release_dates_accept_today_but_reject_future_and_invalid_dates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / 'example-skill'
            skill.mkdir()
            for date, valid in [('2026-09-11', True), ('2026-09-12', False), ('2026-02-30', False)]:
                with self.subTest(date=date):
                    (skill / 'SKILL.md').write_text(
                        '---\nname: example-skill\ndescription: Example\nmetadata:\n'
                        '  author: example\n  version: "1.0.0"\n---\n\n# Example\n\n'
                        '- **Phiên bản:** `1.0.0`\n'
                        f'- **Ngày phát hành:** `{date}`\n'
                    )
                    (root / 'VERSION.md').write_text(f'- Version: `1.0.0`\n- Release date: `{date}`\n')
                    with patch.object(release, 'release_today', return_value=dt.date(2026, 9, 11)):
                        issues = release.check_versions(root, [skill])
                    if valid:
                        self.assertEqual(issues, [])
                    else:
                        self.assertEqual(len(issues), 2)
                        self.assertIn('VERSION.md: INVALID_RELEASE_METADATA', issues)
                        self.assertTrue(any('METADATA_ERROR' in issue for issue in issues))

    def test_public_paths_exclude_ignored_local_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'README.md').write_text('Public')
            (root / 'private.md').write_text('Local only')
            (root / 'docs').mkdir()
            (root / 'docs' / 'guide.md').write_text('Public guide')
            files = {'README.md', 'docs/guide.md'}
            self.assertTrue(release.is_public_path(root, root / 'README.md', files))
            self.assertTrue(release.is_public_path(root, root / 'docs', files))
            self.assertTrue(release.is_public_path(root, root / 'docs/../README.md', files))
            self.assertFalse(release.is_public_path(root, root / 'private.md', files))
            self.assertFalse(release.is_public_path(root, root / 'missing.md', files))
            self.assertFalse(release.is_public_path(root, root.parent, files))

    def test_token_in_nested_json_is_redacted(self):
        token = 'eyJ' + 'a' * 25 + '.' + 'b' * 25 + '.' + 'c' * 25
        data = json.dumps({'body': json.dumps({'secret': token})}).encode()
        issues = release.scan_blob(data, 'fixture.json')
        self.assertTrue(any('JWT' in x for x in issues))
        self.assertNotIn(token, '\n'.join(issues))

    def test_office_text_and_comments_are_checked(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('xl/sharedStrings.xml', '<sst><si><t>user@' + 'private.invalid</t></si></sst>')
            archive.writestr('xl/comments1.xml', '<comments/>')
        issues = release.scan_blob(output.getvalue(), 'fixture.xlsx')
        self.assertTrue(any('NON_EXAMPLE_EMAIL' in x for x in issues))
        self.assertTrue(any('OFFICE_COMMENT' in x for x in issues))

    def test_synthetic_references_are_allowed(self):
        self.assertEqual([], release.scan_text('NO00000000001 user@example.com https://tenant.example.com', 'sample'))
        self.assertEqual([], release.scan_text('https://tennant.cogover.com', 'sample'))
        for host in ('customer-fixture', 'tennant'):
            issues = release.scan_text('https://' + host + '.cogover.net', 'sample')
            self.assertTrue(any('CONCRETE_WORKSPACE_HOST' in issue for issue in issues))
        self.assertEqual([], release.scan_json({'secret': '{WEBHOOK_SECRET_FROM_RUNTIME}'}, 'sample'))

    def test_history_finds_removed_credential(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                subprocess.run(['git', '-C', directory, *args], check=True, capture_output=True)
            git('init'); git('config', 'user.name', 'Example'); git('config', 'user.email', 'user@example.com')
            token = 'ghp_' + 'A' * 30
            (root / 'old.txt').write_text(token)
            git('add', '.'); git('commit', '-m', 'fixture')
            (root / 'old.txt').unlink(); git('add', '-u'); git('commit', '-m', 'remove fixture')
            issues, count = release.history_checks(root)
            self.assertGreater(count, 0)
            self.assertTrue(any('PROVIDER_TOKEN' in x for x in issues))
            self.assertNotIn(token, '\n'.join(issues))

    def test_changed_reference_requires_skill_and_release_bumps(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); skill = root / 'example-skill'; skill.mkdir()
            text = '---\nname: example-skill\ndescription: Example\nmetadata:\n  author: example\n  version: "1.0.0"\n---\n\n# Example\n\n- **Phiên bản:** `1.0.0`\n- **Ngày phát hành:** `2026-01-01`\n'
            (skill / 'SKILL.md').write_text(text); (skill / 'reference.md').write_text('old')
            (root / 'VERSION.md').write_text('- Version: `1.0.0`\n- Release date: `2026-01-01`\n')
            def git(*args):
                subprocess.run(['git', '-C', directory, *args], check=True, capture_output=True)
            git('init'); git('config', 'user.name', 'Example'); git('config', 'user.email', 'user@example.com'); git('add', '.'); git('commit', '-m', 'fixture')
            (skill / 'reference.md').write_text('new')
            issues = release.check_changes(root, 'HEAD', ['example-skill/SKILL.md', 'example-skill/reference.md', 'VERSION.md'])
            self.assertIn('example-skill: SKILL_VERSION_NOT_BUMPED', issues)
            self.assertIn('VERSION.md: RELEASE_VERSION_NOT_BUMPED', issues)


if __name__ == '__main__':
    unittest.main()
