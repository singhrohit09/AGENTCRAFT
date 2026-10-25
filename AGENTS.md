# AGENTS.md — Agent Guidelines & Repository Directives

Welcome to **AgentCraft**, the autonomous AI agent platform developed for the **AGENTCRAFT 2026 National AI Agent Challenge**.

Any AI coding assistant, pair programmer, or automated tool operating within this repository must adhere strictly to these principles.

---

## 1. Project Naming & Brand Integrity

- **Official Name**: Always use **AgentCraft** consistently in code, comments, documentation, test names, and application headers.
- **Forbidden Identifiers**: Do not use "Meghdoot" or reuse unrelated legacy domain features.

---

## 2. Architectural Conventions

1. **AI Engine Isolation (`ai/`)**:
   - The reasoning loop lives in `ai/agent.py`.
   - All tools must reside in `ai/tools/` and subclass `BaseTool` (`ai/tools/base.py`).
   - Every tool must specify formal `ToolParameter` definitions and return typed `ToolResult` objects.

2. **Verification Gates (`VerifierTool`)**:
   - Never consider a multi-step task complete until all intermediate verification assertions have executed and reported `verified: true`.
   - Never suppress or bypass assertion failures.

3. **Backend Service (`backend/`)**:
   - Built on FastAPI with Pydantic v2 schemas.
   - All endpoints must include descriptive docstrings, type annotations, and structured HTTP error responses (400, 404, 422, 500).
   - Use `model_dump()` instead of deprecated `dict()` on Pydantic models.

4. **Frontend Mission Control (`frontend/`)**:
   - Modern React with Vite and Vanilla CSS.
   - Maintain the cyberpunk-glass dark aesthetic without adding conflicting CSS utility frameworks unless explicitly requested.

---

## 3. Testing Mandate

- Every new tool or API endpoint must include unit tests in `ai/tests/` or `backend/tests/`.
- All tests must pass cleanly:
  ```bash
  .\.venv\Scripts\python.exe -m pytest ai/tests backend/tests -v
  ```
- No test should rely on live external internet access; use mock responses or `allow_network=False` for deterministic execution.

---

## 4. Git & Version Control Hygiene

- Never force-push or modify git repository configuration without explicit user consent.
- Keep secrets in `.env` (derived from `.env.example`); never commit secrets, tokens, or credential files.
