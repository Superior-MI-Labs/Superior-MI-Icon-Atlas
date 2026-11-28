"""Build once in this process, then run all existing Python tests with timings."""
from pathlib import Path
from time import perf_counter
import unittest
from tests.site_fixture import fixture

ROOT = Path(__file__).resolve().parents[1]


class TimedResult(unittest.TextTestResult):
    def startTest(self, test):
        self._started = perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        elapsed = perf_counter() - self._started
        self.stream.writeln(f'ATLAS_TIMING test {test.id()} {elapsed:.3f}s')
        super().stopTest(test)


def main():
    # Same output location and build API as the original RUN-ALL.sh.
    # Always execute the build; never reuse an arbitrary on-disk site.
    fixture.prepare(ROOT / 'site')
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2, resultclass=TimedResult).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
