# BrowserAgent 🤖

> Browser test automation in plain English — powered by Claude AI

**⚡ Parallel Execution** — Spin up multiple isolated Docker containers simultaneously, one per test case. 10 tests = 10 browsers running at the same time.

**⚡ Why not MCP?** BrowserAgent uses `playwright-cli` directly instead of the Playwright MCP server — making it significantly faster, more token-efficient, and cheaper to run. MCP loads large tool schemas into context on every turn. BrowserAgent doesn't.

**🐳 Fully Containerized** — Every test runs in its own isolated Docker container with its own Chrome browser, filesystem, and network. No shared sessions, no interference.

**📊 Pytest Reporting** — Automatic HTML reports and JSON summaries generated after every run via pytest integration. Every test case gets its own result file.

---

## 🎬 Demo

> Coming soon — YouTube demo link

---

## ✨ What Makes This Different

Traditional browser automation requires:
- Writing code in Selenium, Playwright, or Cypress
- Managing CSS selectors and XPath that break when UI changes
- Developers to write and maintain tests

**BrowserAgent only requires this:**

```txt
1. Navigate to: https://the-internet.herokuapp.com/login
2. Login with username "tomsmith" and password "SuperSecretPassword!"
3. Verify the login was successful by checking for the message "You logged into a secure area!"
4. Logout by clicking the logout button
5. Verify the logout was successful by checking for the message "You logged out of the secure area!"
6. Close the browser.

At the end output either "FINAL_RESULT: PASS" or "FINAL_RESULT: FAIL"
```

That's it. Anyone can write a test — product managers, QA leads, business analysts. No technical knowledge required.

---

## 🐳 Parallel Containers in Action

All 3 agents spinning up simultaneously from a single command — each with its own isolated Chrome browser and CPU resources.

![Terminal Spinning Up Containers](docs/docker_containers.png)

Watch all containers running in Docker Desktop with live CPU and memory stats.

![Docker Containers Running in Parallel](docs/docker_containers.png)

Drill into any individual container to watch the agent's logs stream live.

![Docker Container Logs](docs/docker_logs.png)

---

## 📊 Pytest HTML Report

Every run automatically generates a full HTML report with pass/fail status, duration, and embedded JSON results per test case.

![Pytest HTML Report](docs/report_screenshot.png)

The report shows:
- **Pass/Fail status** per test case with color coding
- **Embedded JSON result** for each test including summary of what the agent did
- **Environment info** — Python version, platform, pytest version
- **Run duration** per test case

---

## 🏗️ Architecture

```
browseragent/
├── aiagentcontroller.py      # Single AI agent — reads a .txt file and drives the browser
├── containerorchestrator.py  # Spins up parallel Docker containers, one per test case
├── conftest.py               # pytest integration — evaluates results and generates reports
├── Dockerfile                # Container definition with Chrome + playwright-cli
├── testcases/                # Drop your .txt test cases here
│   ├── testdescription1.txt
│   ├── testdescription2.txt
│   └── testdescription3.txt
└── containertestcaseresults/ # Auto-generated results directory
    └── run_20260314_213045/
        ├── agent_1_testdescription1_20260314_213045.txt
        ├── agent_2_testdescription2_20260314_213045.txt
        ├── testdescription1_result.json
        ├── testdescription2_result.json
        ├── summary_20260314_213045.json
        └── report_20260314_213045.html
```

### How Parallel Containers Work

Each test case gets its own completely isolated Docker container running simultaneously:

```
containerorchestrator.py
        │
        ├── Container 1 → testdescription1.txt → Chrome browser (isolated)
        ├── Container 2 → testdescription2.txt → Chrome browser (isolated)
        └── Container 3 → testdescription3.txt → Chrome browser (isolated)
                │
                └── All finish → pytest → HTML report + JSON summary
```

- **No shared sessions** — containers never interfere with each other
- **True parallelism** — all containers start at the same time via Python threading
- **Auto scaling** — drop more `.txt` files in `testcases/` and the orchestrator creates the right number of containers automatically
- **Isolated Chrome** — each container has its own Chrome installation, profile, and network stack

### How Pytest Reporting Works

After all containers finish, pytest automatically:
1. Scans the run directory for output files
2. Checks each file for `FINAL_RESULT: PASS` or `FINAL_RESULT: FAIL`
3. Generates a full HTML report with embedded JSON per test case
4. Saves a JSON summary of the entire run

Everything is saved in a timestamped directory so every run is preserved and comparable.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Docker Desktop
- An Anthropic API key ([get one here](https://console.anthropic.com))
- Node.js + npm

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/browseragent.git
cd browseragent

# Install Python dependencies
pip install anthropic python-dotenv pytest pytest-html

# Install playwright-cli
npm install -g @playwright/cli@latest

# Create your .env file
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

---

## ▶️ How To Run

### Option 1 — Run Locally (Headed Browser, Single Test)

Use this when you want to **watch the agent work in real time** on your machine with a visible browser window.

```bash
python aiagentcontroller.py testcases/testdescription1.txt
```

**What happens:**
1. Opens a visible Chrome browser on your Mac
2. Claude AI reads the test case and executes it step by step
3. You can watch every action in the browser in real time
4. After the agent finishes, pytest runs automatically
5. Results saved to `containertestcaseresults/run_timestamp/`

**When to use this:**
- Debugging a test case
- Writing a new test and verifying it works
- Demos and presentations

---

### Option 2 — Run All Tests in Parallel (Docker Containers)

Use this when you want to **run your entire test suite simultaneously** in isolated containers.

```bash
python containerorchestrator.py --all
```

**What happens:**
1. Builds the Docker image with Chrome + playwright-cli
2. Spins up one container per `.txt` file in `testcases/` simultaneously
3. Each container runs headless Chrome in isolation
4. Waits for all containers to finish
5. Runs pytest to evaluate all results
6. Generates HTML report and JSON summary in a timestamped directory

**When to use this:**
- Running your full test suite
- CI/CD pipelines
- Running tests overnight

---

### Option 3 — Run Specific Tests in Parallel (Docker Containers)

Use this when you want to **run a subset of tests** in parallel.

```bash
python containerorchestrator.py testdescription1.txt testdescription2.txt
```

**What happens:**
Same as `--all` but only spins up containers for the files you specify.

**When to use this:**
- Running only the tests relevant to a specific feature
- Quick smoke test with 2-3 key test cases

---

### Stopping All Containers

```bash
docker stop $(docker ps -q --filter "name=pw_agent")
```

---

### Checking Results

After any run, results are saved to a timestamped directory:

```bash
# Open the HTML report in your browser
open containertestcaseresults/run_20260314_213045/report_20260314_213045.html

# View the JSON summary
cat containertestcaseresults/run_20260314_213045/summary_20260314_213045.json

# View a specific test log
cat containertestcaseresults/run_20260314_213045/agent_1_testdescription1_20260314_213045.txt
```

---

## 📝 Example Test Cases

### Test 1 — Add/Remove Elements Challenge

```txt
1. Navigate to: https://the-internet.herokuapp.com/
2. We are going to do the Click on Add/Remove Challenge
3. Add 5 items.
4. Delete 4 of the items.
5. If the final items left is 1 then we consider this a Pass test.
6. At the end of the task output either "FINAL_RESULT: PASS" or "FINAL_RESULT: FAIL"
   based on whether the task was completed successfully or why it failed.
8. Close Browser
```

### Test 2 — NBA Betting Odds Scraper

```txt
Description
1. Navigate to draftkings.com
2. Navigate to the nba section then gamelines section. And get me the betting odds of today.
4. Display the odds for nba game today in json format
5. At the end of the task output either "FINAL_RESULT: PASS" or "FINAL_RESULT: FAIL"
   based on whether the task was completed successfully or why it failed.
6. Close Browser.
```

### Test 3 — Login / Logout Flow

```txt
Description

1. Navigate to: https://the-internet.herokuapp.com/login
2. Login with username "tomsmith" and password "SuperSecretPassword!"
3. Verify the login was successful by checking for the message "You logged into a secure area!"
4. Logout by clicking the logout button
5. Verify the logout was successful by checking for the message "You logged out of the secure area!"
6. Close the browser.

At the end output either "FINAL_RESULT: PASS" or "FINAL_RESULT: FAIL"
based on whether all steps were completed successfully.
```

---

## 📝 Writing Your Own Test Cases

Create a `.txt` file in the `testcases/` directory. Write your test in plain English.

**Template:**
```txt
Description

1. Navigate to: https://your-app.com
2. [Describe what to do in plain English]
3. [Verify something happened]
4. Close the browser.

At the end output either "FINAL_RESULT: PASS" or "FINAL_RESULT: FAIL"
based on whether all steps were completed successfully.
```

**Rules for writing good test cases:**
- Be specific about what to verify — "check for the message X" is better than "verify it worked"
- Always include the `FINAL_RESULT` instruction at the end — this is how pytest evaluates pass/fail
- Always end with "Close the browser"
- Number your steps for clarity

---

## 📊 Test Reports

Every run generates a timestamped directory in `containertestcaseresults/`:

### HTML Report
Open `report_timestamp.html` in any browser for a visual summary of all test results including pass/fail status, duration, and embedded JSON results per test case.

### JSON Summary
`summary_timestamp.json` contains an overview of the entire run:
```json
{
  "timestamp": "2026-03-14 21:30:45",
  "total": 3,
  "passed": 2,
  "failed": 1,
  "results": [
    {
      "test": "testdescription1",
      "status": "PASS",
      "duration_seconds": 45.32,
      "error": null
    }
  ]
}
```

### Per-Test JSON
Each test case gets its own `testname_result.json`:
```json
{
  "test_case": "testdescription3",
  "timestamp": "2026-03-14 16:55:29",
  "status": "PASS",
  "completed": true,
  "log_file": "agent_1_testdescription3_20260314_165353.txt",
  "summary": "Login successful\nLogout successful\nFINAL_RESULT: PASS\nDone."
}
```

---

## 🐳 Docker Architecture

Each container is completely isolated:
- Its own Chrome browser instance
- Its own filesystem
- Its own network stack
- No shared sessions between agents

This means 10 test cases run as 10 independent parallel browsers with no interference between them.

The containers run headless (no visible browser) using Chrome on `linux/amd64`. When running locally with `aiagentcontroller.py` directly, the browser is headed (visible) so you can watch the agent work.

---

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `HEADLESS` | Run browser headless | `false` locally, `true` in containers |

---

## 🛣️ Roadmap

- [ ] Web UI for uploading test cases and viewing results
- [ ] Scheduled test runs (nightly, on deploy)
- [ ] Slack/email notifications on failure
- [ ] CI/CD integration (GitHub Actions, Jenkins)
- [ ] Test history and trend tracking
- [ ] Support for Firefox and Safari

---

## 🤝 Contributing

Pull requests welcome. For major changes please open an issue first.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

## 👤 Author

Built by Hanns Carrillo

---

*If this project helped you, consider giving it a ⭐ on GitHub*
