from __future__ import annotations

import datetime as dt
import html
import io
import os
import sys
import unittest
from pathlib import Path


class _BufferResult(unittest.TextTestResult):
    pass


def _build_html(result: unittest.TestResult, started_at: dt.datetime, duration: float) -> str:
    passed = result.testsRun - len(result.failures) - len(result.errors)
    rows = []
    for test, err in result.failures:
        rows.append(("FAILED", str(test), err))
    for test, err in result.errors:
        rows.append(("ERROR", str(test), err))

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Phase 7 Test Report</title>
<style>
body{{font-family:Arial,sans-serif;background:#0b1020;color:#e2e8f0;padding:24px}}
.ok{{color:#34d399}} .bad{{color:#f87171}} table{{width:100%;border-collapse:collapse;margin-top:16px}}
td,th{{border:1px solid #334155;padding:8px;vertical-align:top}}
pre{{white-space:pre-wrap}}
</style></head><body>
<h1>Phase 7 - Smoke Test Report</h1>
<p>Started: {started_at.isoformat()}</p>
<p>Duration: {duration:.2f}s</p>
<p>Total: {result.testsRun} | <span class="ok">Passed: {passed}</span> | <span class="bad">Failed+Errors: {len(result.failures)+len(result.errors)}</span></p>
<h2>Failure Details</h2>
<table><thead><tr><th>Status</th><th>Test</th><th>Trace</th></tr></thead><tbody>
{''.join(f'<tr><td>{s}</td><td>{html.escape(t)}</td><td><pre>{html.escape(e)}</pre></td></tr>' for s,t,e in rows) if rows else '<tr><td colspan="3">No failures</td></tr>'}
</tbody></table>
</body></html>"""


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    started = dt.datetime.now(dt.UTC)
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromName("tests.test_api_smoke"))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromName("tests.test_pipeline_smoke"))
    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=_BufferResult)
    result = runner.run(suite)
    duration = (dt.datetime.now(dt.UTC) - started).total_seconds()

    report_dir = Path("tests") / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "phase7-report.html"
    report_path.write_text(_build_html(result, started, duration), encoding="utf-8")

    print(stream.getvalue())
    print(f"HTML report: {report_path.resolve()}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())

