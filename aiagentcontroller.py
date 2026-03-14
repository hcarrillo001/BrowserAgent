#!/usr/bin/env python3
"""
Playwright-CLI Agent
Give it plain English instructions → it drives the browser using playwright-cli.

Usage:
  python aiagentcontroller.py instructions.txt

Setup:
  npm install -g @playwright/cli@latest
  pip install anthropic
  export ANTHROPIC_API_KEY=your_key
"""

import os
import sys
import subprocess
import anthropic
from datetime import datetime
from dotenv import load_dotenv


SKILL = """
# Browser Automation with playwright-cli

## Core workflow
1. Navigate: `playwright-cli open https://example.com`
2. Run `playwright-cli snapshot` to see the page and element refs (e1, e2, ...)
3. Interact using those refs
4. Re-snapshot after changes to get updated refs

## Commands

### Navigation
playwright-cli open <url>
playwright-cli go-back
playwright-cli go-forward
playwright-cli reload
playwright-cli close

### Interaction
playwright-cli snapshot                    # see page + element refs
playwright-cli click <ref>                 # e.g. playwright-cli click e5
playwright-cli fill <ref> "<text>"         # fill input field
playwright-cli type "<text>"               # type into focused element
playwright-cli press <Key>                 # e.g. Enter, Tab, ArrowDown
playwright-cli check <ref>
playwright-cli uncheck <ref>
playwright-cli select <ref> "<value>"
playwright-cli hover <ref>
playwright-cli dblclick <ref>

### Output
playwright-cli screenshot                  # saves screenshot
playwright-cli pdf                         # saves PDF
playwright-cli eval "document.title"       # run JS
playwright-cli console                     # show console logs
playwright-cli network                     # show network requests

### Tabs
playwright-cli tab-new <url>
playwright-cli tab-list
playwright-cli tab-select <index>
playwright-cli tab-close
"""

SYSTEM = f"""You are a browser automation agent. The user gives you plain English instructions.
You execute them step by step using playwright-cli commands.

{SKILL}

Rules:
- Always start with `playwright-cli open <url>` then `playwright-cli snapshot`
- Use snapshot output to find element refs before clicking/filling
- Re-snapshot after page changes to get fresh refs
- Print a brief note before each command explaining what you're doing
- When done, summarize what was accomplished
"""

tools = [{
    "name": "run",
    "description": "Run a playwright-cli shell command and return its output",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The playwright-cli command to run"},
            "reason": {"type": "string", "description": "What this command does"}
        },
        "required": ["command", "reason"]
    }
}]

def run(command: str) -> str:
    if "playwright-cli open" in command:
        if "--headed" not in command and os.getenv("HEADLESS") != "true":
            command = command + " --headed"
        if "--browser" not in command:
            command = command + " --browser chrome"
        if os.getenv("HEADLESS") == "true" and "--no-sandbox" not in command:
            command = command + " --no-sandbox"

    print(f"\n  $ {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if output:
        if len(output) > 3000:
            output = output[:3000] + "\n... (truncated)"
        print(f"  {output}")
    return output or "(no output)"

def run_agent(instructions: str):
    load_dotenv()
    print(f"\nTask: {instructions}\n{'─'*50}")
    api_key_from_env = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key_from_env)
    messages = [{"role": "user", "content": instructions}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=SYSTEM,
            tools=tools,
            messages=messages
        )

        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"\nAgent: {block.text}")

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n→ {block.input.get('reason', '')}")
                    output = run(block.input["command"])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    print(f"\n{'─'*50}\nDone.")

def read_from_file(file_name):
    try:
        with open(file_name, "r") as file:
            content = file.read()
            return content
    except FileNotFoundError:
        print(f"Error: File '{file_name}' was not found.")
        return None

def main():
    load_dotenv()

    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = os.path.join("testcases", "testdescription1.txt")

    test_description = read_from_file(file_name)
    if not test_description:
        return

    # Create run dir
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = "containertestcaseresults"
    run_dir = os.path.join(results_dir, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)

    stem = os.path.splitext(os.path.basename(file_name))[0]
    log_file = os.path.join(run_dir, f"agent_1_{stem}_{timestamp}.txt")

    # Tee output to both terminal and log file
    original_stdout = sys.stdout

    class Tee:
        def write(self, data):
            original_stdout.write(data)
            f.write(data)
        def flush(self):
            original_stdout.flush()
            f.flush()

    with open(log_file, "w") as f:
        sys.stdout = Tee()
        run_agent(test_description)
        sys.stdout = original_stdout

    print(f"\nLog saved to {log_file}")

    # Run pytest and generate report
    print("\nGenerating test report...")
    subprocess.run([
        "pytest", f"testcases/{os.path.basename(file_name)}",
        f"--html={run_dir}/report_{timestamp}.html",
        "--self-contained-html",
        "-v"
    ])
    print(f"\nResults saved to {run_dir}/")

if __name__ == "__main__":
    main()