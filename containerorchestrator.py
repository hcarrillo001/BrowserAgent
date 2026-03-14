#!/usr/bin/env python3
"""
Orchestrator — spins up one Docker container per instruction file.
Usage:
  python containerorchestrator.py task1.txt task2.txt task3.txt
  python containerorchestrator.py --all
"""

import os
import sys
import threading
import subprocess
from datetime import datetime
from dotenv import load_dotenv

IMAGE_NAME = "pw-agent:latest"
TESTCASES_DIR = "testcases"
RESULTS_DIR = "containertestcaseresults"

_print_lock = threading.Lock()

def tprint(agent_id: int, msg: str):
    with _print_lock:
        print(f"[Agent {agent_id}] {msg}", flush=True)

def run_container(filename: str, agent_id: int, run_dir: str):
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
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python containerorchestrator.py --all")
        print("  python containerorchestrator.py task1.txt task2.txt ...")
        sys.exit(1)

    if sys.argv[1] == "--all":
        filenames = get_all_testcases()
        print(f"Found {len(filenames)} test cases: {filenames}\n")
    else:
        filenames = sys.argv[1:]

    # Create run dir before containers start
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RESULTS_DIR, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"Run directory: {run_dir}\n")

    build_image()
    print(f"Spinning up {len(filenames)} containers...\n")
    run_agents_parallel(filenames, run_dir)
    print("\nAll agents finished.")

    print("\nGenerating test report...")
    subprocess.run([
        "pytest", "testcases/",
        f"--html={run_dir}/report_{timestamp}.html",
        "--self-contained-html",
        "-v",
        f"--tb=short"
    ])
    print(f"\nAll results saved to {run_dir}/")

if __name__ == "__main__":
    main()