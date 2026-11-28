"""Suite-owned generated site. Never adopt an existing site as test evidence."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
import atexit
import shutil


class SiteFixture:
    def __init__(self, builder, *, emit_timings=False):
        self._builder = builder
        self._emit_timings = emit_timings
        self._temp = None
        self._path = None
        self._count = None

    def prepare(self, dest=None):
        if self._path is not None:
            if dest is not None and Path(dest).resolve() != self._path:
                raise RuntimeError('Test site already built at a different location')
            if not (self._path / 'public-catalog.json').is_file():
                raise RuntimeError('Shared test site is missing or was mutated')
            return self._path
        if dest is None:
            self._temp = TemporaryDirectory(prefix='atlas-test-site-')
            dest = Path(self._temp.name) / 'site'
        dest = Path(dest).absolute()
        started = perf_counter()
        try:
            if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
                raise RuntimeError('Refusing to replace non-directory or linked site')
            if dest.exists() and not (dest / 'public-catalog.json').is_file():
                raise RuntimeError('Refusing to replace an unrecognized output directory')
            # Always build into a fresh sibling. The previous generated site is
            # not evidence, and must survive an unsuccessful candidate build.
            with TemporaryDirectory(prefix='.atlas-build-', dir=dest.parent) as tmp:
                candidate = Path(tmp) / 'candidate'
                count = self._builder(candidate)
                if not (candidate / 'public-catalog.json').is_file():
                    raise RuntimeError('Build did not generate a public catalog')
                backup = Path(tmp) / 'previous'
                if dest.exists():
                    dest.rename(backup)
                try:
                    candidate.rename(dest)
                except BaseException:
                    if backup.exists():
                        backup.rename(dest)
                    raise
        except BaseException:
            self.close()
            raise
        self._path, self._count = dest.resolve(), count
        if self._emit_timings:
            print(f'ATLAS_TIMING site_build {perf_counter()-started:.3f}s', flush=True)
        return dest

    @property
    def build_count(self):
        self.prepare()
        return self._count

    @contextmanager
    def shared(self):
        """For read-only assertions only; writers must use isolated_copy."""
        yield self.prepare()

    @contextmanager
    def isolated_copy(self):
        with TemporaryDirectory(prefix='atlas-test-mutation-') as tmp:
            # No hard links: pruning rewrites documentation as well as deleting files.
            target = Path(tmp) / 'site'
            started = perf_counter()
            shutil.copytree(self.prepare(), target)
            if self._emit_timings:
                print(f'ATLAS_TIMING site_copy {perf_counter()-started:.3f}s', flush=True)
            yield target

    def close(self):
        if self._temp is not None:
            self._temp.cleanup()
        self._temp = self._path = self._count = None


def _build(dest):
    from tools.build_site import build
    return build(dest)


fixture = SiteFixture(_build, emit_timings=True)
atexit.register(fixture.close)
shared_site = fixture.shared
copied_site = fixture.isolated_copy
