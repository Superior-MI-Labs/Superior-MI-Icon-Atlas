"""Fast negative and positive checks for fixture lifecycle, no real site builds."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from tests.site_fixture import SiteFixture


class SiteFixtureTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def build(dest):
            self.calls.append(dest)
            dest.mkdir(parents=True, exist_ok=True)
            (dest/'public-catalog.json').write_text('{}')
            (dest/'guide.md').write_text('original')
            return 2073
        self.fixture = SiteFixture(build)
        self.addCleanup(self.fixture.close)

    def test_build_once_and_preserve_count(self):
        with self.fixture.shared() as first:
            with self.fixture.shared() as second:
                self.assertEqual(first, second)
            self.assertEqual(self.fixture.build_count, 2073)
        self.assertEqual(len(self.calls), 1)

    def test_mutation_copy_does_not_change_shared_site(self):
        with self.fixture.shared() as base:
            with self.fixture.isolated_copy() as copy:
                (copy/'guide.md').write_text('modified')
                (copy/'public-catalog.json').unlink()
            self.assertFalse(copy.exists())
            self.assertEqual((base/'guide.md').read_text(), 'original')
            self.assertTrue((base/'public-catalog.json').is_file())
        self.assertEqual(len(self.calls), 1)

    def test_existing_destination_is_rebuilt_and_other_dest_rejected(self):
        with TemporaryDirectory() as tmp:
            dest = Path(tmp)/'site'
            dest.mkdir()
            (dest/'public-catalog.json').write_text('stale')
            (dest/'obsolete.txt').write_text('stale')
            self.assertEqual(self.fixture.prepare(dest), dest.resolve())
            self.assertEqual((dest/'public-catalog.json').read_text(), '{}')
            self.assertFalse((dest/'obsolete.txt').exists())
            with self.assertRaises(RuntimeError):
                self.fixture.prepare(Path(tmp)/'other')
        self.assertEqual(len(self.calls), 1)

    def test_missing_catalog_fails_closed(self):
        broken = SiteFixture(lambda dest: 2073)
        self.addCleanup(broken.close)
        with self.assertRaises(RuntimeError):
            broken.prepare()
        with self.fixture.shared() as site:
            (site/'public-catalog.json').unlink()
            with self.assertRaises(RuntimeError):
                self.fixture.prepare()

    def test_failed_candidate_preserves_previous_site(self):
        broken = SiteFixture(lambda dest: 2073)
        self.addCleanup(broken.close)
        with TemporaryDirectory() as tmp:
            dest = Path(tmp)/'site'
            dest.mkdir()
            (dest/'public-catalog.json').write_text('previous')
            with self.assertRaises(RuntimeError):
                broken.prepare(dest)
            self.assertEqual((dest/'public-catalog.json').read_text(), 'previous')

    def test_build_failure_can_never_be_used_as_evidence(self):
        def fail(dest):
            raise ValueError('bad build')
        broken = SiteFixture(fail)
        self.addCleanup(broken.close)
        with self.assertRaises(ValueError):
            broken.prepare()
        with self.assertRaises(ValueError):
            broken.prepare()


if __name__ == '__main__':
    unittest.main()
