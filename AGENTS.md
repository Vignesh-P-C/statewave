# AGENTS.md — guide for contributors and coding agents

A short orientation for humans and AI coding agents (GitHub Copilot, Claude,
Cursor, …) working in the **statewave** core repo. For the full contribution
process and licensing, start with [CONTRIBUTING.md](CONTRIBUTING.md).

## What this repo is

Statewave is an open-source memory/context service for AI agents: it records
episodes, compiles them into durable memories, and serves compact, ranked,
token-bounded context over a `/v1` API. This repo is the server and reference
implementation. For the big picture, see the
[architecture overview](https://github.com/smaramwbc/statewave-docs/blob/main/architecture/overview.md).

## Setup, build, test

The canonical steps live in
[CONTRIBUTING.md](CONTRIBUTING.md#development-setup) and the
[README quick start](README.md#quick-start) — don't duplicate them, follow
them. In short:

```bash
docker compose up db -d
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,llm]"
alembic upgrade head
pytest tests/
```

Run `ruff` and the test suite before opening a PR; `make test-cold` validates a
full fresh-install path.

**Tip for agents:** unit tests are hermetic with stub providers — run them
without external services via:

```bash
STATEWAVE_EMBEDDING_PROVIDER=stub STATEWAVE_COMPILER_TYPE=heuristic \
  pytest tests/ --ignore=tests/integration
```

## Conventions

- **Code style & testing:** see
  [statewave-docs/dev/conventions.md](https://github.com/smaramwbc/statewave-docs/blob/main/dev/conventions.md).
- **Packages version independently.** The server, the Python SDK (`statewave`),
  and the TypeScript SDK (`@statewavedev/sdk`) version on separate cadences; the
  compatibility axis is the `/v1` API contract, not a shared number. Don't try
  to align version strings across packages.
- **Some "proof" numbers are mirrored across repos** — test counts, eval
  assertion/test counts, and the support-workflow benchmark score. They have a
  single source of truth and a consistency check in `statewave-docs` that runs
  at release time. If you change one of these numbers, keep every surface in
  sync rather than editing a single file.
- **Keep claims accurate and modest.** Describe what the code does; back any
  performance or benchmark claim with a reproducible source, and avoid
  unqualified superlatives.

## Pull requests

See [CONTRIBUTING.md](CONTRIBUTING.md#pull-request-process). Keep PRs focused,
add tests for behavior changes, and make sure `ruff` and `pytest` pass.

## Optional: give your agent memory of this repo (with Statewave itself)

This project dogfoods Statewave. If you'd like your coding assistant to recall
this repo's decisions, history, and conventions instead of re-reading files
each session, serve it through the Statewave MCP server:

1. **Run a Statewave instance** — self-host via `docker compose up` (see the
   [README quick start](README.md#quick-start)).
2. **Ingest this repo** into a subject using the GitHub or Markdown connector.
   The recommended subject is `repo:smaramwbc/statewave` (per the
   [subject strategy](https://github.com/smaramwbc/statewave-docs/blob/main/connectors/subject-strategy.md)).
   See the
   [connectors quickstart](https://github.com/smaramwbc/statewave-docs/blob/main/connectors/quickstart.md)
   and
   [GitHub connector](https://github.com/smaramwbc/statewave-docs/blob/main/connectors/github.md).
3. **Point your MCP client** (Copilot, Claude, Cursor, custom agents) at the
   [Statewave MCP server](https://github.com/smaramwbc/statewave-docs/blob/main/connectors/mcp.md)
   (`@statewavedev/mcp-server`). Your agent can then call `statewave_get_context`
   with subject `repo:smaramwbc/statewave` for compact, ranked repo context.

This is optional — it needs a running Statewave instance — but it's a good way
to see the product work on a real codebase.
