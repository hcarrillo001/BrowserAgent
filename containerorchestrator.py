#!/usr/bin/env python3
"""
Orchestrator — spins up one Docker container per instruction file.
Usage:
  python containerorchestrator.py task1.txt task2.txt task3.txt
  python containerorchestrator.py --all
  python containerorchestrator.py --all --concurrency 5
"""

import os
import sys
import threading
import subprocess
import argparse
from datetime import datetime
from dotenv import load_dotenv

IMAGE_NAME = "pw-agent:latest"
TESTCASES_DIR = "testcases"
RESULTS_DIR = "containertestcaseresults"

_print_lock = threading.Lock()
_semaphore = None  # set in main()

def tprint(agent_id: int, msg: str):
    with _print_lock:
        print(f"[Agent {agent_id}] {msg}", flush=True)

def run_container(filename: str, agent_id: int, run_dir: str):
    with _semaphore:
        tprint(agent_id, f"Starting → {filename}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = os.path.splitext(filename)[0]
        log_file = os.path.join(run_dir, f"agent_{agent_id}_{stem}_{timestamp}.txt")

        cmd = [
            "docker", "run",
            "--rm",
            "--platform", "linux/amd64",
            "--cap-add=SYS_ADMIN",
            "--name", f"pw_agent_{agent_id}",
            "-e", f"ANTHROPIC_API_KEY={os.getenv('ANTHROPIC_API_KEY')}",
            "-e", "HEADLESS=true",
            "-v", f"{os.path.abspath('.')}:/app/tasks",
            IMAGE_NAME,
            "python", "aiagentcontroller.py", f"tasks/{TESTCASES_DIR}/{filename}"
        ]

        try:
            with open(log_file, "w") as f:
                subprocess.run(cmd, text=True, stdout=f, stderr=f)
            tprint(agent_id, f"Output saved to {log_file}")
        except Exception as e:
            tprint(agent_id, f"Error: {e}")
        finally:
            tprint(agent_id, "Done.")

def run_agents_parallel(filenames: list[str], run_dir: str):
    threads = []
    for i, filename in enumerate(filenames, start=1):
        t = threading.Thread(target=run_container, args=(filename, i, run_dir), daemon=True)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

def get_all_testcases() -> list[str]:
    path = os.path.join(os.path.abspath('.'), TESTCASES_DIR)
    if not os.path.exists(path):
        print(f"Error: '{TESTCASES_DIR}' directory not found.")
        sys.exit(1)
    files = [f for f in os.listdir(path) if f.endswith(".txt")]
    if not files:
        print(f"Error: No .txt files found in '{TESTCASES_DIR}'.")
        sys.exit(1)
    return sorted(files)

def build_image():
    print("Building Docker image...")
    result = subprocess.run([
        "docker", "build",
        "--platform", "linux/amd64",
        "-t", IMAGE_NAME, "."
    ])
    if result.returncode != 0:
        print("Docker build failed.")
        sys.exit(1)
    print("Image built.\n")

def main():
    global _semaphore

    load_dotenv()

    parser = argparse.ArgumentParser(description="BrowserAgent Orchestrator")
    parser.add_argument("--all", action="store_true", help="Run all test cases in testcases/")
    parser.add_argument("--concurrency", type=int, default=5, help="Max parallel containers (default: 5)")
    parser.add_argument("files", nargs="*", help="Specific test case files to run")
    args = parser.parse_args()

    if not args.all and not args.files:
        print("Usage:")
        print("  python containerorchestrator.py --all")
        print("  python containerorchestrator.py --all --concurrency 5")
        print("  python containerorchestrator.py task1.txt task2.txt ...")
        sys.exit(1)

    _semaphore = threading.Semaphore(args.concurrency)

    filenames = get_all_testcases() if args.all else args.files
    print(f"Found {len(filenames)} test cases | concurrency: {args.concurrency}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RESULTS_DIR, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"Run directory: {run_dir}\n")

    build_image()
    print(f"Spinning up containers (max {args.concurrency} at a time)...\n")
    run_agents_parallel(filenames, run_dir)
    print("\nAll agents finished.")

    print("\nGenerating test report...")
    subprocess.run([
        "pytest", "testcases/",
        f"--html={run_dir}/report_{timestamp}.html",
        "--self-contained-html",
        "-v",
        "--tb=short"
    ])
    print(f"\nAll results saved to {run_dir}/")

if __name__ == "__main__":
    main()