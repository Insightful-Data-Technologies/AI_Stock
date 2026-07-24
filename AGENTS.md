# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
Primary product: a Python **AI Stock Analysis agent** that calls LLMs (GitHub Models,
Azure OpenAI, etc.) to analyze stocks, generate strategies, and optimize portfolios.
Entry points: `demo_ai_agent.py`, `simple_test.py`, `test_ai_agent.py`. Core code lives in
`agents/` (client + stock agent) and `config/ai_models_config.py` (model registry).

Secondary/aux (not runnable in this VM, see below): the Streamlit tools in `tools/` and the
static marketing site in `website/`.

### Environment
- Python is 3.12. The startup update script installs the working dependency subset
  **system-wide** with `pip install --break-system-packages`, so just run project code with
  `python3` directly (no virtualenv needed). Invoke dev tools via `python3 -m <tool>`.
- `requirements.txt` is aspirational and **does not install on Python 3.12** (pins like
  `numpy==1.24.3`, `tensorflow==2.15.0`, `torch==2.1.2` have no cp312 wheels, and the heavy
  ML/DB deps are not imported by the runnable core). The update script installs only the
  working subset actually needed to run/lint/test the agent:
  `aiohttp python-dotenv pandas ruff black pytest pytest-asyncio`.

### Run / lint / test (from repo root)
- Run the app (demo): `python3 demo_ai_agent.py`
- Quick Azure-only check: `python3 simple_test.py` (see credential note below)
- Lint: `python3 -m ruff check .` and format check `python3 -m black --check .`
  (CI mirror: `.github/workflows/lint.yml`; ruff/pyproject/pre-commit configs live under `.github/`).
- There is **no real pytest suite** — the `test_*.py` files are runnable demo scripts (async
  `main()` that hit live AI APIs), not assertion-based unit tests.

### Credentials (important gotcha)
Running the agent end-to-end requires a valid LLM credential; none of the credentials shipped
in the committed `.env` work in this VM:
- The Azure endpoint in `.env` (`chana-...cognitiveservices.azure.com`) no longer resolves
  (resource deleted) — `DEFAULT_AI_MODEL=azure_gpt5` and `simple_test.py` will fail with DNS errors.
- The committed `OPENAI_API_KEY` returns 401 (revoked); the local `GITHUB_TOKEN` is a placeholder.
- `AIAgentClient` only implements the `github`, `azure_foundry`, and `azure_openai` providers
  (no OpenAI-direct path), so the free path is **GitHub Models** — set a real
  `GITHUB_TOKEN` (a PAT with GitHub Models access) in the environment/secrets, then
  `.venv/bin/python demo_ai_agent.py`. Model keys map to `openai/gpt-5*`, `openai/o3`,
  `deepseek/deepseek-r1` at `https://models.github.ai/inference/`.

Egress is open in this environment, so once a valid token is provided the calls go through.

### Out of scope in this VM
- `tools/*.py` (Streamlit apps) require an on-prem SQL Server (`.env` `DB_SERVER=LAPTOP-...`,
  a private hostname) and are not reachable here.
- `website/` is a redirect stub; `website/canva_original.html` references a `_assets/` folder
  that is not committed, so the full site does not render locally.
