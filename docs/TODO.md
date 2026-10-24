# TODO

Flat, ordered checklist for the extraction. Plan and rationale:
[`reviews/2026-10-24-deep-dive-and-plan.md`](reviews/2026-10-24-deep-dive-and-plan.md).
Tracking issue: [#15](https://github.com/UnityInFlow/safe-cli-runner/issues/15).
Board: https://github.com/orgs/UnityInFlow/projects/14. Effort in working hours.

## Done 2026-10-24

- [x] Choose the name, licence, toolchain; bootstrap the public repo with `uv init --lib`, hatchling, ruff, `mypy --strict`, `pytest-asyncio`, `anyio` only runtime dep ([#15](https://github.com/UnityInFlow/safe-cli-runner/issues/15), 2 h)
- [x] CI matrix ubuntu-latest + macos-latest x py 3.12, 3.13 on GitHub-hosted runners (`.github/workflows/ci.yml`) (part of [#8](https://github.com/UnityInFlow/safe-cli-runner/issues/8))
- [x] Release workflow with PyPI trusted publishing on tag `v*` (`.github/workflows/release.yml`) (part of [#10](https://github.com/UnityInFlow/safe-cli-runner/issues/10))
- [x] README (planned API, tier table, "flags are not a sandbox"), SECURITY.md, CHANGELOG.md, LICENSE, dependabot (part of [#9](https://github.com/UnityInFlow/safe-cli-runner/issues/9))
- [x] Plan doc, this TODO, `docs/API.md`, ADR-001
- [x] Issues #1 to #15 created, board linked, origin tracking issue notified

## First 2 hours (remaining)

- [ ] Upload `0.0.1.dev0` to TestPyPI to reserve the name (manual, needs the owner's PyPI token: `uv build && uv publish --publish-url https://test.pypi.org/legacy/`) ([#10](https://github.com/UnityInFlow/safe-cli-runner/issues/10), 0.25 h)
- [ ] Write and publish post 1, "Your coding CLI is an LLM API with a shell attached", 600 words, one code block with the flag set, link the repo (manual, owner's site) ([#11](https://github.com/UnityInFlow/safe-cli-runner/issues/11), 3 h)
- [ ] Accept ADR-038 in the origin project (ai-jervis-python#373) (manual, 2 h, counted in the origin's plan)
- [ ] Start the four-week stop-rule clock on the day post 1 goes out; note the date in [#15](https://github.com/UnityInFlow/safe-cli-runner/issues/15)

## v0.1.0

- [ ] Port `cli_binary.py` to `src/safe_cli_runner/binary.py`, 29 tests green on both OSes ([#1](https://github.com/UnityInFlow/safe-cli-runner/issues/1), 3 h)
- [ ] Port process core and transcript (`process.py`, `transcript.py`, `fakes.py`), 56 tests green, no origin import ([#2](https://github.com/UnityInFlow/safe-cli-runner/issues/2), 4 h)
- [ ] Port the injection gate to `gate.py`, 20 + 10 tests, `prompt_gate=None` disables ([#3](https://github.com/UnityInFlow/safe-cli-runner/issues/3), 2 h)
- [ ] Adapters claude_code / codex / opencode with `lockdown` field; live `gemini -p` probe and `adapters/gemini.py`; 21 tests ([#4](https://github.com/UnityInFlow/safe-cli-runner/issues/4), 3 h)
- [ ] Decide Gemini in v0.1 or v0.2 from the probe evidence (owner, after [#4](https://github.com/UnityInFlow/safe-cli-runner/issues/4))
- [ ] Runner, `RunnerConfig`, `run`, `stream`, `CliResult`, `AuditEvent`, `errors.py`, credential brokering; 12 owner-policy tests minus 403 cases; new config / semaphore / audit / `OwnLogin` tests ([#5](https://github.com/UnityInFlow/safe-cli-runner/issues/5), 5 h)
- [ ] Lockdown verification: `num_turns` / `tool_use` check, `LockdownViolation`, fixture test fails closed; verify field names with one live call ([#6](https://github.com/UnityInFlow/safe-cli-runner/issues/6), 2 h)
- [ ] Sandbox tiers v0.1: `Sandbox`, `Lockdown`, `probe()`, `SandboxRequired`; Codex under FLAGS raises ([#7](https://github.com/UnityInFlow/safe-cli-runner/issues/7), 2 h)
- [ ] CI: add `--cov --cov-fail-under=85`; `workflow_dispatch` live smoke job with `secrets.ANTHROPIC_API_KEY`, prove once manually ([#8](https://github.com/UnityInFlow/safe-cli-runner/issues/8), 3 h)
- [ ] README: install line, verified 30-second example, threat-model table; SECURITY review ([#9](https://github.com/UnityInFlow/safe-cli-runner/issues/9), 3 h)
- [ ] Set up the PyPI project and trusted publisher for `UnityInFlow/safe-cli-runner`, workflow `release.yml`, environment `pypi` (manual, owner's PyPI account) ([#10](https://github.com/UnityInFlow/safe-cli-runner/issues/10), 0.5 h)
- [ ] Bump to `0.1.0`, update CHANGELOG, tag `v0.1.0`, confirm `pip install safe-cli-runner==0.1.0` from a clean venv ([#10](https://github.com/UnityInFlow/safe-cli-runner/issues/10), 1.25 h)
- [ ] Freeze the origin README (ai-jervis-python#382) (manual, 1 h, counted in the origin's plan)

## Later, only if demand

Gated on the stop rule (four weeks after post 1: a comment of substance, a star or an issue),
then on v0.1 users.

- [ ] Framework adapters `integrations/langgraph.py`, `integrations/pydantic_ai.py` as optional extras ([#12](https://github.com/UnityInFlow/safe-cli-runner/issues/12), 3 h)
- [ ] v0.2 OS sandbox tier: ADR-002, seatbelt profile + `bwrap` argv builder, Codex / Gemini / OpenCode enabled, "read ~/.ssh yields nothing" test on both OSes ([#13](https://github.com/UnityInFlow/safe-cli-runner/issues/13), 12 h)
- [ ] Posts 2 to 5 (manual, owner's site, ~7 h)
- [ ] v0.3 CONTAINER tier + credential proxy (`ANTHROPIC_BASE_URL` broker) + per-call spend ceiling ([#14](https://github.com/UnityInFlow/safe-cli-runner/issues/14), not estimated)
