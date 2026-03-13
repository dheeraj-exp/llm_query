# Selenium LLM Runner (ChatGPT first)

This project:

1. Reads `query.csv` and expands it into `generated_queries.csv`
2. Runs each generated query against one or more websites (ChatGPT first)
3. Saves results to `responses.csv` as query/response pairs

## Input CSV format (`query.csv`)

Each row:

- Column 1: a template string containing `%s`
- Column 2..N: replacement values

Example row:

`The temperature in %s may,India,SriLanka,Pakistan`

Generates:

- `The temperature in India may`
- `The temperature in SriLanka may`
- `The temperature in Pakistan may`

## Setup

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### If `python -m venv` fails on Ubuntu/Debian

Install the OS package that provides `venv`:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv
```

## Run

1) Put your templates into `query.csv` (in this folder).

2) Generate queries:

```bash
python -m llm_runner.generate_queries --input query.csv --output generated_queries.csv
```

3) Run automation (ChatGPT):

```bash
python -m llm_runner.run --site chatgpt --queries generated_queries.csv --out responses.csv --headful
```

### First-time ChatGPT login

ChatGPT requires authentication. The runner uses a persistent browser profile directory (`.browser_profiles/chatgpt`) so you login once, then future runs reuse the session.

If you see the login page, complete login manually in the opened browser window; the script will continue once the prompt box is detected.

## Notes

- This is designed to be extended: add new site adapters in `llm_runner/sites/`.
- Selectors on LLM sites can change; ChatGPT adapter uses multiple fallbacks.
