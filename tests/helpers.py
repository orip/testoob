import os, sys, warnings
def in_development_mode():
    "True if we're in development mode, False if we're deployed"
    return "TESTOOB_DEVEL_TEST" in os.environ

def project_subpath(*components):
    from os.path import dirname, join, normpath
    return normpath(join(dirname(__file__), "..", *components))

def module_path():
    return project_subpath("src")

def which(executable):
    import procutils
    results = procutils.which(executable)
    if len(results) == 0:
        raise RuntimeError("Executable %r not found in the path" % executable)
    if len(results) > 1:
        warnings.warn("Found more than one instance of %r in the path, using %r, options are %s" % (executable, results[0], results))
    return results[0]

def executable_path():
    if in_development_mode():
        return project_subpath("src", "testoob", "testoob")
    else:
        return which("testoob")

def add_module_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)

if in_development_mode():
    print "Development mode: adding %r to sys.path" % module_path()
    add_module_path( module_path() )

from testoob.reporting.base import BaseReporter
class ReporterWithMemory(BaseReporter):
    "A reporter that remembers info on the test fixtures run"
    def __init__(self):
        BaseReporter.__init__(self)
        self.started = []
        self.finished = []
        self.stdout = ""
        self.stderr = ""

        self.has_started = False
        self.is_done = False

    def _append_test(self, l, test_info):
        # TODO: use test_info.methodname()
        l.append(str(test_info).split()[0])

    def start(self):
        self.has_started = True
    def done(self):
        self.is_done = True
    def startTest(self, test_info):
        self._append_test(self.started, test_info)
    def stopTest(self, test_info):
        self._append_test(self.finished, test_info)
    def addError(self, test_info, err_info):
        self._append_test(self.errors, test_info)
    def addFailure(self, test_info, err_info):
        self._append_test(self.failures, test_info)
    def addSuccess(self, test_info):
        self._append_test(self.successes, test_info)
    def addAssert(self, test_info, assertName, varList, exception):
        self.asserts[str(test_info).split()[0]] = (assertName, exception.__class__)

    def __str__(self):
        attrs = ("started","successes","errors","failures","finished","stdout","stderr")
        return "\n".join(["%s = %s" % (attr, getattr(self,attr)) for attr in attrs])

class TestoobRunnerWithMemory:
    def __init__(self):
        self.reporter = ReporterWithMemory()

    def run(self, **kwargs):
        testoob.running.run(reporters=[self.reporter], **kwargs)

    def check_reporter(self, **kwargs):
        for attr, expected in kwargs.items():
            actual = getattr(self.reporter, attr)
            if type(expected) == type([]):
                expected.sort()
                actual.sort()
            from testoob.testing import assert_equals
            assert_equals(expected, actual)

import unittest
import testoob.running
class TestoobBaseTestCase(unittest.TestCase):
    def setUp(self):
        self.runner = TestoobRunnerWithMemory()
    def tearDown(self):
        del self.runner
    def _check_reporter(self, **kwargs):
        self.runner.check_reporter(**kwargs)
    def _run(self, **kwargs):
        self.runner.run(**kwargs)

def ensure_coverage_support():
    from testoob import coverage, testing
    if not coverage.supported():
        testing.skip(reason="No coverage support")
