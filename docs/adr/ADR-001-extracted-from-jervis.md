# ADR-001: Extract the safe CLI runner from Jervis as a standalone package

Status: Accepted (2026-10-24)

## Context

The subprocess runner that executes Claude Code, Codex or OpenCode as a non-agentic LLM call
grew inside an internal Python project ("Jervis", a FastAPI + LangGraph sidecar). A review on
2026-10-24 found that the rest of that project is simulated or thin, while the runner has 126
unit tests (plus 12 owner-policy tests) and three months of review. The review decided to
freeze the platform and extract the runner. The origin's record of the same decision is its
ADR-038; this ADR is the record in the new repository.

## Decision

1. **Extract** `cli_provider.py`, `cli_binary.py` and the dependency-free injection gate
   `prompt_injection.py` into a standalone, framework-agnostic, public pip package
   `safe-cli-runner` (import `safe_cli_runner`), licensed Apache-2.0, built with hatchling,
   `requires-python >= 3.12`, `anyio` the only runtime dependency.
2. **Copy, do not move.** The origin keeps its own copy and is not made to depend on this
   package. Fixes flow one way, into this repository; the origin is frozen.
3. **API-key billing is the assumption.** Anthropic closed third-party use of subscription
   logins in January 2026. The default and tested credential path is an API key passed as a
   single environment variable into an otherwise empty child environment. Own-login mode
   (`OwnLogin`) stays in the package as an explicit, warned, local-only opt-in whose warning
   text cites the vendor terms.
4. **Positioning: isolation primitive, not orchestration.** The package does not plan, retry,
   route or keep state. Paperclip and OpenAI Symphony own orchestration; this is the thing
   they would call. The pitch is "`claude -p` as a function call that provably cannot touch
   your machine".
5. **Prompt gate on by default**, documented as a tripwire, not a control. `prompt_gate=None`
   disables it.
6. **Sandbox tiers are explicit and fail closed.** `FLAGS` (v0.1) is what exists and is
   honest about being flags, not a sandbox; adapters whose lockdown is partial (Codex,
   OpenCode) raise `SandboxRequired` under it. `OS` (seatbelt / bubblewrap) is v0.2,
   `CONTAINER` is v0.3, each gated on demand.

## Consequences

- Jervis-specific concerns are cut at the boundary: the `config` object becomes `RunnerConfig`
  parameters, the credential becomes a value passed in, the model tier mapping, circuit
  breaker, owner allowlist and HTTP 403 policy stay in the origin.
- The package carries its own hosted CI (GitHub-hosted runners, ubuntu and macOS, Python 3.12
  and 3.13) and publishes to PyPI with trusted publishing; the first upload is manual.
- The origin is referred to publicly as "an internal project"; its visibility is an open
  owner decision and does not block this repository.
- A demand check (post 1, stop rule of four weeks) gates everything beyond v0.1 scope.

## References

- `docs/reviews/2026-10-24-deep-dive-and-plan.md` (this repo)
- Origin ADR-038 "Extract the CLI runner; freeze the platform" (private, ai-jervis-python#373)
- Tracking issue #15
