import os
import json
import pytest
from datetime import datetime

TESTCASES_DIR = "testcases"
RESULTS_DIR = "containertestcaseresults"

_results = []
_run_dir = None

def get_latest_run_dir():
    if not os.path.exists(RESULTS_DIR):
        return None
    runs = sorted([
        d for d in os.listdir(RESULTS_DIR)
        if os.path.isdir(os.path.join(RESULTS_DIR, d)) and d.startswith("run_")
    ])
    if not runs:
        return None
    return os.path.join(RESULTS_DIR, runs[-1])

def get_run_dir():
    global _run_dir
    if _run_dir is None:
        _run_dir = get_latest_run_dir()
    return _run_dir

def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".txt" and file_path.parent.name == TESTCASES_DIR:
        return TxtTestFile.from_parent(parent, path=file_path)

class TxtTestFile(pytest.File):
    def collect(self):
        yield TxtTestItem.from_parent(self, name=self.path.stem)

class TxtTestItem(pytest.Item):
    def runtest(self):
        stem = self.path.stem
        run_dir = get_run_dir()

        if not run_dir:
            raise AssertionError(f"No run directory found — did you run the orchestrator first?")

        matches = sorted([
            f for f in os.listdir(run_dir)
            if f.endswith(".txt") and stem in f
        ])

        if not matches:
            raise AssertionError(f"No output file found for {stem} in {run_dir}")

        log_file = os.path.join(run_dir, matches[-1])
        with open(log_file) as f:
            content = f.read()

        completed = "Done." in content
        passed = "FINAL_RESULT: PASS" in content

        test_result = {
            "test_case": stem,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "PASS" if passed else "FAIL",
            "completed": completed,
            "log_file": os.path.basename(log_file),
            "summary": "\n".join([l.strip() for l in content.splitlines() if l.strip()][-10:])
        }

        # Save per test JSON
        json_file = os.path.join(run_dir, f"{stem}_result.json")
        with open(json_file, "w") as f:
            json.dump(test_result, f, indent=2)

        # Store on item for report hook
        self._test_result = test_result

        if not completed:
            raise AssertionError(f"Agent did not complete:\n{content[-500:]}")
        if not passed:
            raise AssertionError(f"Test did not pass:\n{content[-500:]}")

    def repr_failure(self, excinfo):
        return str(excinfo.value)

    def reportinfo(self):
        return self.path, 0, f"test case: {self.path.stem}"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and hasattr(item, "_test_result"):
        result = item._test_result
        json_str = json.dumps(result, indent=2)

        status_color = "green" if result["status"] == "PASS" else "red"
        html_block = f"""
        <div style="margin-top:10px;">
            <b>Test Result JSON:</b>
            <pre style="background:#f4f4f4; padding:10px; border-left:4px solid {status_color}; font-size:12px;">{json_str}</pre>
        </div>
        """
        extra = getattr(report, "extras", [])
        try:
            from pytest_html import extras
            extra.append(extras.html(html_block))
        except Exception:
            pass
        report.extras = extra


def pytest_runtest_logreport(report):
    if report.when == "call":
        _results.append({
            "test": report.nodeid.split("/")[-1].replace(".txt::", "_"),
            "status": "PASS" if report.passed else "FAIL",
            "duration_seconds": round(report.duration, 2),
            "error": str(report.longrepr) if report.failed else None
        })


def pytest_sessionfinish(session, exitstatus):
    run_dir = get_run_dir()
    if not run_dir:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(_results),
        "passed": sum(1 for r in _results if r["status"] == "PASS"),
        "failed": sum(1 for r in _results if r["status"] == "FAIL"),
        "results": _results
    }

    json_file = os.path.join(run_dir, f"summary_{timestamp}.json")
    with open(json_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nJSON summary saved to {json_file}")
    print(f"Run directory: {run_dir}")