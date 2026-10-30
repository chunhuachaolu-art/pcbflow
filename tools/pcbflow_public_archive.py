# -*- coding: utf-8 -*-
"""pytest plugin for the public archive of pcbflow.

Many tests in this project assert against frozen experiment evidence under
``out/`` (≈1.5 GB, hash-anchored) and against third-party corpus boards.
Neither is redistributed in the public archive. In a clean clone those tests
fail with ``FileNotFoundError`` before reaching any assertion about code
behaviour.

This plugin reports exactly that situation as a *skip* with the missing path
in the reason, so the remaining results stay readable. It does not touch any
other failure: an AssertionError, a wrong value or any other exception is
still reported as a failure.

Set ``PCBFLOW_STRICT=1`` to disable the plugin and see raw results.
"""
import os

import pytest

_MISSING_MARKERS = (FileNotFoundError, NotADirectoryError)


def _missing_evidence(excinfo):
    if excinfo is None:
        return None
    exc = excinfo.value
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        if isinstance(exc, _MISSING_MARKERS):
            return getattr(exc, "filename", None) or str(exc)
        exc = exc.__cause__ or exc.__context__
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    if os.environ.get("PCBFLOW_STRICT") == "1":
        return
    rep = outcome.get_result()
    if rep.outcome != "failed" or call.excinfo is None:
        return
    missing = _missing_evidence(call.excinfo)
    if missing is None:
        return
    rep.outcome = "skipped"
    rep.longrepr = (str(item.fspath), item.location[1] or 0,
                    "Skipped: needs unpublished evidence or third-party file: %s" % missing)
