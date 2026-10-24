# 2026-10-24: Deep dive and plan: extract the safe CLI runner

Status: plan, adopted. Owner decisions recorded in `docs/adr/ADR-001-extracted-from-jervis.md`.
This is the public-repo copy of the extraction plan written the same day in the origin
project (an internal repository, referred to below as "Jervis"; its plan is
`docs/reviews/2026-10-24-deep-dive-and-plan.md` there, its ADR is ADR-038). Every
`file:line` below was re-read today in the origin at commit `a61dcd1`.

## Where the code comes from

The origin is a Python 3.12 FastAPI + LangGraph "AI operations" sidecar whose platform
layers (graph, cache, cost routing, policy) turned out to be simulated or thin; the review
there froze them. The part that is real, reviewed and tested is the CLI provider: a
subprocess runner that executes Claude Code, Codex or OpenCode as a non-agentic LLM call.
That part is what this repository extracts. Copy, not move: the origin keeps its copy and
is not made to depend on this package.

Source files (origin, `src/jervis/`):

| File | Lines | What |
|---|---|---|
| `core/providers/cli_provider.py` | 1,239 | env allowlist `:54`, errors `:73-116`, caps and timeouts `:127-144`, `CliAdapter` `:166`, Claude Code flags `:247-263`, adapters `:331,435,533`, transcript `:546-601`, gate call `:604-619`, `_subprocess_env` `:622-648`, pipe close and killpg `:651-702`, `_CappedRun` `:717-849` (stdin feed `:763-775`, deadline `:787-799`, cap while reading `:801-815`), `CliProvider` `:869-1239` (`_prepare_call` `:966`, own-login env `:1030`, scratch cwd `:1063`, `_spawn` `:1054`, `_check_exit` `:1091`, `_finish_response` `:1098`, `chat` `:1142`, `stream_chat` `:1183`) |
| `core/providers/cli_binary.py` | 231 | `_warned` `:55`, `CliBinaryError` `:62`, `ResolvedCliBinary` `:67`, `configured_binary_path` `:99`, `_directory_problems` `:130`, `binary_problems` `:181`, `resolve_cli_binary` `:193` |
| `core/prompt_injection.py` | 363 | `Severity` `:47`, `InjectionFinding` `:57`, pattern table `:97-262`, invisible codepoints `:263-288`, `normalise` `:288`, `PatternInjectionScanner` `:293`, `enforce_prompt_gate` `:326` |

Test inventory, counted today (`def test_` per file; parametrized cases expand further at
collection):

| Origin test file | Tests | Ports to |
|---|---|---|
| `tests/unit/core/providers/test_cli_binary.py` | 29 | `tests/test_binary.py` (#1) |
| `tests/unit/core/providers/test_cli_provider.py` | 36 | spawn/cap/timeout half to `tests/test_process.py` (#2); provider half to `tests/test_runner.py` (#5) |
| `tests/unit/core/providers/test_cli_provider_process_group.py` | 8 | `tests/test_process.py` (#2) |
| `tests/unit/core/providers/test_cli_streaming.py` | 12 | `tests/test_process.py` / `tests/test_runner.py` (#2) |
| `tests/unit/core/providers/test_cli_injection_gate.py` | 20 | `tests/test_gate.py` (#3) |
| `tests/unit/core/providers/test_cli_adapters.py` | 21 | `tests/test_adapters.py` (#4) |
| subtotal `test_cli_*.py` | **126** | |
| `tests/unit/test_cli_owner_policy.py` | 12 | `tests/test_runner.py` (#5), minus the HTTP 403 cases which are the origin's web layer |
| `tests/unit/core/test_prompt_injection.py` | 10 | `tests/test_gate.py` (#3), the gate's own unit tests |
| `tests/unit/core/providers/fakes.py` | fixtures | `tests/fakes.py` (#2) |

Not ported (stays frozen in the origin): the circuit breaker and fallback chain
(`core/model_fallback.py:76-84,842-856`), the owner allowlist and HTTP 403 client policy
(`providers/__init__.py:84-109`), the Anthropic switch, structured output (`base.py:120`),
and the callers in `api/chat.py`, `api/admin.py`, `core/startup_checks.py`, `core/validation.py`.

## Decision

1. **Extract** `cli_provider.py` + `cli_binary.py` + the dependency-free injection gate into a
   standalone, framework-agnostic, public pip package `safe-cli-runner` (import
   `safe_cli_runner`): a safe runner that executes Claude Code / Codex / Gemini CLI as a
   sandboxed, non-agentic LLM call from any Python program. Copy, do not move.
2. **Freeze** the rest of the origin (its own step 15; not this repo's concern beyond the link).
3. The package assumes **API-key billing** (Anthropic closed third-party use of subscription
   logins in January 2026). Own-login mode stays an explicit, warned, local-only opt-in.
4. Positioning: isolation primitive, not orchestration. The pitch is "`claude -p` as a
   function call that provably cannot touch your machine".

## Extraction map

| Origin symbol (file:line) | New module | Dependency to cut / inject |
|---|---|---|
| `cli_binary.py` whole (`resolve_cli_binary`, `binary_problems`, `ResolvedCliBinary`, `_directory_problems`) `:62-231` | `safe_cli_runner/binary.py` | `config.cli_provider_binary_path_for`, `cli_provider_binary_dir`, `dev_mode` (`:107-113,209,226`) become parameters `pinned_path`, `binary_dir`, `allow_path_lookup`, `strict` |
| `_ENV_ALLOWLIST`, `_subprocess_env` `cli_provider.py:54,622-648` | `safe_cli_runner/process.py` | `config.dev_mode` (`:642`) -> `RunnerConfig.inherit_path: bool` |
| `_close_read_pipes`, `_kill_process_group`, `_CappedRun`, `_REAP_TIMEOUT_SECONDS`, `_MAX_STDOUT_BYTES`, `_READ_CHUNK_BYTES`, `_STDERR_KEEP_BYTES` `:127-144,651-849` | `process.py` | none (asyncio + anyio only); cap and timeout come from `RunnerConfig` instead of `config.cli_provider_timeout` (`:1081`) |
| `_ROLES`, `_TURN_LABEL`, `_validated_role`, `_quote_turn_labels`, `_unquoted_transcript`, `_flatten_prompt` `:546-601` | `safe_cli_runner/transcript.py` | `prompt_injection.normalise` (`:288`) moves with it |
| `check_cli_prompt` `:604-619` + `core/prompt_injection.py` (363 lines) | `safe_cli_runner/gate.py` (optional, on by default) | none; exposed as `RunnerConfig.prompt_gate: Callable[[str], Awaitable[None]] \| None` |
| `CliAdapter`, `CLAUDE_CODE_ADAPTER`, `_claude_*` `:166-344` | `safe_cli_runner/adapters/claude_code.py` | `_CLI_MODELS`/`DEFAULT_MODEL` (`:146,153`) stay as adapter fields; add `lockdown: Lockdown` (FULL) |
| `CODEX_ADAPTER`, `_codex_*` `:347-442`; `OPENCODE_ADAPTER` `:445-540` | `adapters/codex.py`, `adapters/opencode.py` | `lockdown = Lockdown.PARTIAL` -> runnable only under an OS sandbox tier (v0.2); new `adapters/gemini.py` pinned by a live probe (#4) |
| `_CallSpec`, `CliProvider._prepare_call`, `_spawn`, `_check_exit`, `_finish_response`, `chat`, `stream_chat` `:706-715,966-1239` | `safe_cli_runner/runner.py` (`Runner`, `run()`, `stream()`) | `config.cli_provider_enabled` (`:883,984`) dropped; `_credential_for`/`anthropic_enabled` (`:57-70,935`) -> `Credential` passed in; `ModelTier`/`model_for_tier` (`:158-162,947-953`) dropped (host concern); `BaseProvider`/`ProviderResponse`/`StreamDelta` -> `CliResult`, `CliDelta`; `token_budget.count` (`:1116-1117`, tiktoken) -> optional `token_counter` hook, default marks `usage_estimated=True` |
| `CliCredentialError`, `CliUnavailable`, `CliOutputLimitError`, `CliBinaryError` `:73-116`, `cli_binary.py:62` | `safe_cli_runner/errors.py` | `CliUnavailable` codes lose `cli_provider_disabled`/`owner_mode_required`; add `SandboxRequired`, `LockdownViolation` |
| `_cli_semaphore` `core/model_fallback.py:76-84,846` | `Runner` instance attribute | `config.cli_provider_max_concurrency` -> `RunnerConfig.max_concurrency` |
| circuit breaker, owner allowlist, HTTP 403 policy, Anthropic switch, structured output, origin callers | stay in the origin (frozen) | not ported |

## Public API (v0.1)

```python
from safe_cli_runner import Runner, RunnerConfig, ApiKey, OwnLogin, Sandbox, run, stream
from safe_cli_runner.adapters import CLAUDE_CODE, CODEX, GEMINI

@dataclass(frozen=True)
class RunnerConfig:
    binary_path: str | None = None          # pinned absolute path (required unless allow_path_lookup)
    binary_dir: str | None = None
    allow_path_lookup: bool = False         # dev only; also skips strict owner/mode checks
    credential: ApiKey | OwnLogin | None = None   # ApiKey(env="ANTHROPIC_API_KEY", value=...)
    sandbox: Sandbox = Sandbox.FLAGS        # FLAGS | OS | CONTAINER; raises SandboxRequired if unmet
    timeout_s: float = 90.0
    max_stdout_bytes: int = 4 * 1024 * 1024
    max_concurrency: int = 2
    env_passthrough: tuple[str, ...] = ("HOME", "TERM")
    prompt_gate: Callable[[str], Awaitable[None]] | None = gate.default
    token_counter: Callable[[str], int] | None = None
    audit: Callable[[AuditEvent], None] | None = None   # argv, env NAMES, bytes, exit, cost; never text

async def run(messages: list[Message] | str, *, adapter=CLAUDE_CODE, model: str | None = None,
              system_prompt: str = "", config: RunnerConfig | None = None) -> CliResult
async def stream(...) -> AsyncIterator[CliDelta | CliResult]
```

`CliResult`: `content, model, adapter, input_tokens, output_tokens, usage_estimated, cost_usd,
duration_s, sandbox, audit: AuditEvent`. Extras: `[langgraph]` -> `as_langchain_tool()`,
`[pydantic-ai]` -> `as_pydantic_ai_tool()`, `[tiktoken]` for exact local counts. Full text with
module and error tables: `docs/API.md`.

## Sandbox tiers

| Tier | What it is | Status | Makes eligible |
|---|---|---|---|
| `FLAGS` | What exists: `--tools "" --setting-sources "" --strict-mcp-config --safe-mode --no-session-persistence` (`cli_provider.py:247-263`), prompt on stdin (`:763-775`), fresh tmp cwd + own session (`:1063-1075`), env allowlist (`:622-648`), killpg + pipe close (`:651-702`), 4 MiB cap enforced while reading (`:801-815`), deadline (`:787-799`), binary vetting up the directory chain (`cli_binary.py:130-231`), model validated against the catalog (`:1020-1026`), transcript roles/labels (`:546-601`), injection gate (`:604-619`). Plus new: `num_turns`/tool-use check on the result JSON -> `LockdownViolation` if the CLI did anything agentic | v0.1 | Claude Code only (`Lockdown.FULL`). Codex and OpenCode cannot disable tools (`cli_provider.py:347-356,465-471`) and raise `SandboxRequired` |
| `OS` | macOS `sandbox-exec` (seatbelt) profile / Linux `bubblewrap`: read-only bind of the vetted binary dir and interpreter, tmpfs `HOME` holding only the auth file the CLI needs, no writable path but the scratch cwd, network allowed (the provider endpoint). `probe()` reports availability; `sandbox=Sandbox.OS` fails if unavailable | v0.2 | Codex (`--sandbox read-only` inside the OS sandbox), Gemini, OpenCode |
| `CONTAINER` | docker/podman with egress proxy allowlist, CPU/mem limits | v0.3 | hosted / multi-tenant use |

Why FLAGS first: it is what has 126 tests and three months of review behind it, and it is
honest: the README says "flags are not a sandbox" and shows the `OS` tier as the next step. Why
`OS` before `CONTAINER`: zero infrastructure for the user, and bubblewrap/seatbelt is what the
CLI vendors' own sandboxes use. The eligibility rule (`Lockdown.PARTIAL` adapters refuse to run
under `FLAGS`) is the "fail if unavailable" enforcement the package promises.

## Depends on / unblocks

Depends on nothing: the origin's CI stays red and is not repaired; the extraction copies code
into this repo with its own hosted CI (green on the empty package today). Unblocks nothing
elsewhere in the portfolio. Shared conventions (GitHub-hosted runners, PyPI trusted publishing
with the first upload by hand, README top block, one post per launch) come from the portfolio
decisions document in the owner's workspace and are applied here as written.

## First 2 hours (do before anything else)

1. Reserve the name: `uv init --lib safe-cli-runner`, `0.0.1.dev0` to TestPyPI, public repo
   with a README that says in ten lines what it will be and links this document. **Repo,
   README and this document: done 2026-10-24.** TestPyPI upload: manual, owner's token (#10).
2. Write and publish post 1, "Your coding CLI is an LLM API with a shell attached", from the
   existing code and the origin's incident story, linking the empty repo. Short version: 600
   words, one code block showing the flag set. This is the demand check for the whole
   extraction (#11).

**Stop rule.** Four weeks after post 1: no comment of substance, no star or issue on the repo.
Then stop at v0.1 scope at most, or do not build v0.1 at all. Nothing from "Later" before that
gate. (Portfolio-wide threshold for public tools, for reference: 25 stars or 3 external
issues or PRs by day 30.)

## Step-by-step plan

Effort is working hours for one person with an agent. **v0.1 is about 34 h**: bootstrap 2 +
code port 3+4+2 + adapters 3 + runner 5 + lockdown 2 + sandbox tiers 2 + CI 3 + docs 3 +
release 2 + post 1 3 = 34, with the origin-side ADR (2 h) and freeze (1 h) counted in the
origin's plan. Later steps are gated.

| # | Step | How (files, commands) | Done when | h | Issue | State |
|---|---|---|---|---|---|---|
| 1 | ADR in the origin: "Extract the CLI runner; freeze the platform" | origin `docs/adrs/ADR-038-...md`; decisions 1-4, copy-not-move, freeze list | ADR merged, status Accepted | 2 | origin #373 | open |
| 2 | Bootstrap this repo | `uv init --lib`, src layout, hatchling, `requires-python >= 3.12`, Apache-2.0, ruff (lint + format), `mypy --strict`, `pytest-asyncio`, `anyio` only runtime dep, CI + release workflows, dependabot, README, SECURITY, CHANGELOG, this plan, TODO, ADR-001 | `uv run pytest` passes on the empty package; CI green on first push; TestPyPI name reserved | 2 | #15 (tracking), origin #374 | **done 2026-10-24** except the manual TestPyPI upload (#10) |
| 3 | Port `cli_binary.py` | copy to `src/safe_cli_runner/binary.py`; replace the four `config.*` reads with parameters; keep `_warned`; port `test_cli_binary.py` (29) by replacing `monkeypatch.setattr(config, ...)` with explicit arguments | 29 tests green on macOS and Linux | 3 | #1 | open |
| 4 | Port process core and transcript | `process.py` from `cli_provider.py:54,127-144,622-849`; `transcript.py` from `:546-601` + `normalise`; port `fakes.py`, `test_cli_provider_process_group.py` (8), `test_cli_streaming.py` (12), the spawn/cap/timeout half of `test_cli_provider.py` (36) | 56 tests green; no origin import anywhere | 4 | #2 | open |
| 5 | Port the gate | `prompt_injection.py` -> `gate.py`; port `test_cli_injection_gate.py` (20) and the gate's own unit tests (10) | gate tests green; `prompt_gate=None` disables it | 2 | #3 | open |
| 6 | Adapters | `adapters/{claude_code,codex,opencode}.py` from `:166-540` with `lockdown` field; `adapters/gemini.py` pinned by a live `gemini -p` probe (output format, tool-disable flags, auth env), recorded in the module docstring the way `:213-244` does for Claude; port `test_cli_adapters.py` (21) | all adapters parse their pinned fixtures; Gemini lockdown classified FULL or PARTIAL with evidence | 3 | #4 | open |
| 7 | Runner and public API | `runner.py`: `RunnerConfig`, `Runner` (owns the semaphore), `run`, `stream`, `CliResult`, `AuditEvent`; `errors.py`; credential brokering (`ApiKey` injected as the single extra env var, `OwnLogin` adds `own_login_env` and logs a warning, as `:1001-1031`); port the provider half of `test_cli_provider.py` and `test_cli_owner_policy.py` (12, minus the 403 cases) | new tests: config validation, semaphore, audit event has env NAMES only, `OwnLogin` refused unless `allow_own_login=True` | 5 | #5 | open |
| 8 | Lockdown verification | after parse, read `num_turns` and any `tool_use` in the stream; raise `LockdownViolation` and emit the audit event; verify the field names with one live call first | test with a fixture showing a tool call fails closed | 2 | #6 | open |
| 9 | Sandbox tiers v0.1 | `sandbox.py`: `Sandbox` enum, `Lockdown` enum, `probe()` (detects `bwrap`, `sandbox-exec`, `docker`), `SandboxRequired`; FLAGS implemented, OS/CONTAINER raise with the probe result | tests: Codex under FLAGS raises; Claude under FLAGS runs; `probe()` output on both OSes | 2 | #7 | open |
| 10 | Framework adapters: gated, see "Later" | | | 3 | #12 | gated |
| 11 | CI on GitHub-hosted runners | matrix and checks: done today in `ci.yml`. Remaining: `pytest --cov --cov-fail-under=85` once there is code; a `workflow_dispatch` "live smoke" job that `npm i -g @anthropic-ai/claude-code`, pins `binary_dir=/usr/local/bin`, runs one haiku call with `secrets.ANTHROPIC_API_KEY`, asserts `num_turns == 1` and cost > 0 | smoke job proven once manually | 3 | #8 | open (matrix done) |
| 12 | README, SECURITY, CHANGELOG | README done today in planned form. Remaining: one-command install once released, threat-model table (protects against / does not), verify the 30-second example runs; SECURITY.md exists | a reader can run the example in under a minute on a machine with Claude Code installed | 3 | #9 | open (first versions done) |
| 13 | Release v0.1.0 | `release.yml` exists (trusted publishing on tag `v*`, `uv build`, `gh release create --generate-notes`). Remaining: TestPyPI `0.0.1.dev0` by hand, PyPI project + trusted publisher configured, tag `v0.1.0` | `pip install safe-cli-runner==0.1.0` works from a clean venv | 2 | #10 | open |
| 14 | Post 1 only (the demand check) | owner's site; 600 words, one code block | published before step 3 starts | 3 | #11 | open |
| 15 | Freeze the origin | README banner, badges, counts | origin README no longer claims production readiness | 1 | origin #382 | open |
| 16 | v0.2 OS sandbox tier: gated, see "Later" | | | 12 | #13 | gated |
| 17 | v0.3 CONTAINER tier + credential proxy: gated, see "Later" | | | not estimated | #14 | gated |

New tests the package needs beyond the port: config validation, `SandboxRequired`,
`LockdownViolation`, audit-event contents, `OwnLogin` refusal, probe output, integration extras,
one live smoke.

## Decisions the owner must make

Already taken (recorded in ADR-001, do not reopen): package name `safe-cli-runner`, Apache-2.0,
gate on by default (documented as a tripwire), own-login kept as a warned opt-in, API-key
billing as the default, hosted runners, trusted publishing with the first upload by hand.

Still open:

1. **Gemini CLI in v0.1 or v0.2.** Depends on the #4 probe: if Gemini cannot disable tools by
   flag it is `Lockdown.PARTIAL` and waits for the OS tier (#13). Decide after the probe, not
   before.
2. **Where the blog lives.** Default recorded in the portfolio decisions: the owner's site,
   post 1 before the code, posts 2 to 5 later. Confirm the URL when #11 is published.
3. **Origin visibility.** Default: stays private with the freeze banner; this README says
   "extracted from an internal project". Alternative: make it public as the lab notebook
   behind the posts.

## Later, only if demand (gated on the post-1 stop rule, then on v0.1 users)

- Framework adapters (#12, 3 h): `integrations/langgraph.py` (`as_langchain_tool`),
  `integrations/pydantic_ai.py`; optional extras, import guarded; tests run only with the extra
  installed.
- Posts 2 to 5 (~7 h, owner's site): "Killing a subprocess is the easy part" (process groups,
  stdout cap enforced while reading, closing pipes after SIGKILL so `wait()` returns); "Don't
  trust PATH" (pinning and vetting an executable like sshd StrictModes vets keys); "Whose
  credentials?" (API key vs subscription login, January 2026, owner-only mode); "Flags are not
  a sandbox" (seatbelt, bubblewrap, containers; why Codex and OpenCode needed it), with v0.2.
- v0.2 OS sandbox tier (#13, 12 h): `docs/adr/ADR-002-os-sandbox.md`; seatbelt profile + `bwrap`
  argv builder; Codex/Gemini/OpenCode enabled under it; the acceptance test ("read ~/.ssh"
  yields nothing) for every adapter, on both OSes.
- v0.3 (#14): `CONTAINER` tier for hosted use; credential proxy: the CLI gets
  `ANTHROPIC_BASE_URL` pointing at a local broker that holds the key, so the key never enters
  the child environment; per-call spend ceiling using the CLI-reported `total_cost_usd`.
- Only then: re-evaluate whether anything else in the origin (the fallback chain + circuit
  breaker, the gate's pattern set) deserves its own extraction. Nothing in its graph, cache or
  cost layers does.

## Issue index

| Issue | Title | Step |
|---|---|---|
| #15 | v0.1.0: extract the safe CLI runner (2026-10-24 plan) | tracking |
| #1 | Port `cli_binary.py` to `binary.py` with 29 tests | 3 |
| #2 | Port process core and transcript (56 tests) | 4 |
| #3 | Port the injection gate (20 tests) | 5 |
| #4 | Adapters claude_code / codex / opencode + Gemini probe | 6 |
| #5 | Runner, RunnerConfig, public API, errors, credential brokering | 7 |
| #6 | Lockdown verification (num_turns / tool_use) | 8 |
| #7 | Sandbox tiers v0.1 (enum, probe, SandboxRequired) | 9 |
| #8 | CI live smoke job with ANTHROPIC_API_KEY (workflow_dispatch) | 11 |
| #9 | README, SECURITY, threat-model table | 12 |
| #10 | Release v0.1.0 via PyPI trusted publishing + TestPyPI name reservation | 13 |
| #11 | Post 1 "Your coding CLI is an LLM API with a shell attached" | 14 |
| #12 | [later-gated] Framework adapters langgraph / pydantic-ai | 10 |
| #13 | [later-gated] v0.2 OS sandbox tier (seatbelt / bubblewrap) | 16 |
| #14 | [later-gated] v0.3 CONTAINER tier + credential proxy | 17 |
| origin #373, #374, #382, #383 | ADR-038, bootstrap, freeze, origin tracking | 1, 2, 15 |
