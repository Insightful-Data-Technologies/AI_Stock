# AGENTS.md

## Cursor Cloud specific instructions

This repo is a Python (async) **AI Stock Analysis** project plus a few Streamlit utilities and a static redirect website. The VM runs **Python 3.12**.

### Dependencies
- **Do NOT run `pip install -r requirements.txt`.** Its pins are incompatible with Python 3.12 (e.g. `numpy==1.24.3`, `tensorflow==2.15.0`, `torch==2.1.2` fail to build). The startup update script instead installs a curated, compatible subset sufficient to run/lint/test the products. The heavy ML libs (torch/tensorflow/transformers/langchain) are not needed to run the core agent or the Streamlit tools.
- `pip` installs console scripts to `~/.local/bin`, which is **not on `PATH`**. Invoke tools via the module form: `python3 -m ruff`, `python3 -m black`, `python3 -m pytest`, `python3 -m streamlit`.

### Core product: AI Stock Analysis agent
- Code: `agents/ai_agent_client.py`, `agents/stock_ai_agent.py`, `config/ai_models_config.py`; entrypoints `demo_ai_agent.py`, `simple_test.py`, `test_ai_agent.py`.
- **Requires a live AI credential to make real calls.** The shipped `.env` credentials are dead in this environment: the Azure endpoint host (`chana-...cognitiveservices.azure.com`) no longer resolves, and the `OPENAI_API_KEY` returns 401. The default `gh auth token` has **no GitHub Models inference access** (403 `no_access`).
- Working path: the **GitHub Models** provider (`models.github.ai`, models `gpt5`/`gpt5_mini`/`o3`/etc.) is fully implemented in `AIAgentClient`. Set a valid `GITHUB_TOKEN` (a PAT with GitHub Models access) to run end-to-end. `demo_ai_agent.py` gates on `GITHUB_TOKEN`; `simple_test.py`/`test_ai_agent.py` target the (dead) `azure_gpt5` model.
- The code path itself is verified working up to the network boundary (config load, request build, auth header, HTTP call) — failures are external credential/DNS issues, not code/env issues.

### Streamlit tools (`tools/`)
- `streamlit_he_en_auto_fix.py` is fully **self-contained** (no DB/creds) — the easiest app to run and demo. `file_scanner_app.py` needs a SQL Server (`DB_SERVER` points at an unreachable local machine). `ai_agent.py` needs Streamlit + an OpenAI key.
- Run: `python3 -m streamlit run tools/streamlit_he_en_auto_fix.py --server.port 8501 --server.address 0.0.0.0 --server.headless true`.

### Lint & tests
- Lint (as CI does): `python3 -m ruff check . --config .github/ruff.toml` and `python3 -m black --check .`. The repo currently has many **pre-existing** ruff/black findings — do not treat these as regressions.
- Tests: the root `test_*.py` / `simple_test.py` files are **async integration scripts that hit external APIs** (Azure/GoDaddy), not offline unit tests. `python3 -m pytest` runs, but the async tests need pytest-asyncio config + live credentials to pass. There is no offline unit-test suite.

### Website
- `website/*.html` is static (`index.html` just redirects to a Canva site). No server needed; serve with `python3 -m http.server` from `website/` if desired.
