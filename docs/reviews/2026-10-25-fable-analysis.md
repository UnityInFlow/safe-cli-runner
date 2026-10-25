# safe-cli-runner: Fable analysis (2026-10-25)

Author: Claude Fable 5.1 (model id claude-fable-5-1), working with the owner in Claude Code.
Status: opinion document. A second opinion from Claude Opus is requested; the prompt for it is in the appendix.
Inputs: repo at `5969650`, the extraction plan `docs/reviews/2026-10-24-deep-dive-and-plan.md`, the origin code in ai-jervis-python (read only, at `a61dcd1`), web research on 2026-10-25 (links inline).

## Summary in ten lines

1. Verdict: build v0.1, but narrower and in a different order than the plan says. Claude Code only, API key only at the top level, code before the post.
2. The risk that can kill it: Anthropic's `claude-agent-sdk` (0.2.174, uploaded 2026-10-24, 8,346 stars) already gives `tools=[]`, `setting_sources=[]`, `strict_mcp_config=True`, `max_turns=1`, `max_budget_usd`, a bundled pinned CLI and a typed result with `num_turns` and `total_cost_usd`. That is roughly 70 percent of the FLAGS tier, maintained by the vendor.
3. What the SDK does not do, verified in its source: it inherits the whole parent environment (`subprocess_cli.py:819-825`), kills only the direct child with SIGTERM then SIGKILL (`:1030-1046`), caps one JSON message at 1 MiB rather than total output (`:36,947,1112`), vets nothing about the binary beyond "exists", and knows only Claude Code.
4. What makes the package worth doing anyway: the 30 percent is exactly the part that incidents are about (process trees, environments, output floods, unvetted binaries), it has 126 tests, and no PyPI package covers it: the closest, `claude-subprocess` 0.1.3, has 0 stars and routes through a subscription gateway.
5. The honest pitch is therefore not "Agent SDK alternative" but "the hardening the SDK leaves to you, for Claude Code, Codex and Gemini, with an audit event".
6. Two changes to the FLAGS tier cost an afternoon and raise its real value: pass `--max-turns 1` in argv, and give the child a fresh `HOME` in API-key mode.
7. The env allowlist is hygiene, not a boundary, on both OSes: a same-uid child can read `/proc/<ppid>/environ` on Linux and `ps -Eww` output on macOS. Say so in the README; the OS tier is where that stops.
8. Lockdown verification should be a hard failure that withholds the content; a flag invites ignoring it.
9. I disagree with the plan on three points: post 1 before any code, `OwnLogin` at the top-level import, and the gate on by default. Details in "Fable's opinion".
10. Stop rule: use the portfolio threshold (25 stars or 3 external issues or PRs by day 30 after post 1), not the plan's softer "one comment or star". If missed, ship v0.1.0 as-is and stop.

## Where it stands

Repo facts verified today (`git log`, `gh issue list`, `gh repo view`):

| Fact | Value |
|---|---|
| HEAD | `5969650 ci: set UV_PYTHON per matrix job so uv run keeps the synced venv` (5 commits total, all 2026-10-24) |
| Code | `src/safe_cli_runner/__init__.py` (docstring + `__version__ = "0.0.1.dev0"`), `py.typed`; nothing ported |
| Tests | `tests/test_version.py`, 3 tests (PEP 440, metadata match, asyncio wiring) |
| CI | `ci.yml`: ubuntu-latest + macos-latest x py3.12, 3.13; ruff check, ruff format, `mypy --strict src`, pytest; uv 0.11.32 by script; checkout pinned to SHA `3d3c42e5...` (v7.0.1) |
| Release | `release.yml`: tag `v*`, `uv build`, `uv publish --trusted-publishing always`, `gh release create`; environment `pypi`; tag-equals-version check |
| Issues | #2 to #16 open, created 2026-10-24 18:40 to 18:42; #1 is Dependabot; 0 stars; repo created 2026-10-24T18:35Z |
| Lock | `uv.lock` committed (revision 3); Dependabot for actions and uv, monthly |
| Deviation | Portfolio convention says `macos-14`; `ci.yml` uses `macos-latest` |

Origin facts (ai-jervis-python at `a61dcd1`, `wc -l` and `grep -c "def test_"` today): `cli_provider.py` 1,239 lines, `cli_binary.py` 231, `prompt_injection.py` 363. Tests: `test_cli_binary.py` 29, `test_cli_provider.py` 36, `test_cli_provider_process_group.py` 8, `test_cli_streaming.py` 12, `test_cli_injection_gate.py` 20, `test_cli_adapters.py` 21 (126), plus `test_cli_owner_policy.py` 12 and `test_prompt_injection.py` 10. The plan's line numbers match the file. Only 6 `monkeypatch.setattr(config, ...)` calls in `test_cli_binary.py` need rewriting. Two files already skip on `win32` (`test_cli_provider_process_group.py:36`, `test_cli_streaming.py:300`).

Local CLI evidence (this machine): Claude Code 2.1.310 has `--tools` ("" disables all), `--safe-mode`, `--setting-sources`, `--strict-mcp-config`, `--no-session-persistence`, `--bare`, `--max-budget-usd`. Codex CLI 0.162.0 has `--sandbox`, `--ephemeral`, `--ignore-user-config`, `--skip-git-repo-check`. Gemini CLI, `srt` and `bwrap` are not installed here; `/usr/bin/sandbox-exec` is.

## Market and alternatives

| Name | What it does | What it lacks vs this package | Evidence |
|---|---|---|---|
| `claude-agent-sdk` (Python, Anthropic) | `query()` with `ClaudeAgentOptions`: `tools=[]` emits `--tools ""`, `disallowed_tools`, `setting_sources=[]`, `strict_mcp_config`, `max_turns`, `max_budget_usd`, `permission_mode="dontAsk"`, `cwd`, `user`, `cli_path`, `sandbox: SandboxSettings`; bundles the CLI binary (`_bundled/`), falls back to `shutil.which("claude")` | Env is `os.environ` plus overrides, no allowlist (`subprocess_cli.py:819-825`); no process-group kill (`:1030-1046`); 1 MiB cap is per JSON message, not total stdout; no binary vetting; `sandbox` applies to the Bash tool only, irrelevant when tools are off; Claude only; no audit event; no credential brokering (`ANTHROPIC_API_KEY` inherited from the parent) | [PyPI](https://pypi.org/project/claude-agent-sdk/), [docs](https://code.claude.com/docs/en/agent-sdk/python), [source](https://github.com/anthropics/claude-agent-sdk-python) |
| Claude Code CLI flags | `--tools ""`, `--setting-sources ""`, `--strict-mcp-config`, `--safe-mode`, `--no-session-persistence`, `--bare`, `--max-turns`, `--max-budget-usd`, `--disallowedTools "*"` (removes every tool including MCP), new `--restricted` (v2.1.248+: removes command tools and WebFetch, confines file tools, loads only managed settings, refuses `bypassPermissions`) | Flags only; everything the child inherits from the parent process | [CLI reference](https://code.claude.com/docs/en/cli-reference) |
| Claude Code built-in sandbox | Seatbelt on macOS, bubblewrap + socat on Linux, domain-allowlist proxy; `sandbox.enabled`, `failIfUnavailable` (default false: runs unsandboxed silently), `filesystem.denyRead` | Bash tool only; off by default; reads of `~/.ssh` allowed unless denied; Ubuntu 24.04 AppArmor blocks bwrap by default; nothing for `-p` with tools off | [Sandboxing docs](https://code.claude.com/docs/en/sandboxing), [engineering post](https://anthropic.com/engineering/claude-code-sandboxing) |
| `@anthropic-ai/sandbox-runtime` (`srt`) | OS-level wrapper for any process, 6,536 stars, Apache-2.0, research preview; TS library and CLI | npm only; no Python API; not a "pure completion" runner; the OS tier of this package should probably call it rather than re-implement it | [GitHub](https://github.com/anthropic-experimental/sandbox-runtime) |
| `py-sandboxrt` 0.2.0, `sandbox-runtime` 0.2.0 (PyPI), `nono-py` 0.16.0 | Python ports of srt (0 and 1 stars, last release Feb and Dec) and Landlock bindings (38 stars, Aug 2026) | Generic sandboxes; no CLI contract, no result parsing, no audit; two of three look abandoned | [py-sandboxrt](https://pypi.org/project/py-sandboxrt/), [sandbox-runtime](https://pypi.org/project/sandbox-runtime/), [nono-py](https://pypi.org/project/nono-py/) |
| `claude-subprocess` 0.1.3 (2026-10-15) | Wraps `claude -p` with `--tools '' --disable-slash-commands --setting-sources user --strict-mcp-config --mcp-config mcp-empty.json --no-session-persistence`; stdlib only; JSON extraction, cache | Subscription OAuth via an `omniroute` gateway, no API-key mode; loads `--setting-sources user` (hooks); no env allowlist, pinning, cap, killpg; 0 stars | [PyPI](https://pypi.org/project/claude-subprocess/), [repo](https://github.com/octrow/claude-cli) |
| `claude-code-python-wrapper` 0.3.0 (Jul 2025), `claude-wrapper` 0.1.dev15 (Aug 2025) | Thin async wrappers | Dead (repo 404, one dev release) | [PyPI](https://pypi.org/project/claude-code-python-wrapper/), [PyPI](https://pypi.org/project/claude-wrapper/) |
| OpenAI Codex CLI + SDKs | `--sandbox` with `read-only`, `workspace-write` or `danger-full-access`; Seatbelt on macOS, bwrap on Linux; `@openai/codex-sdk` (TS, bundles runtime), `openai-codex` (Python, beta, JSON-RPC to app-server, `Sandbox` enum) | "read-only" still lets the agent run commands and read the whole filesystem (origin comment `cli_provider.py:347-356`); no tool-disable flag | [Codex sandboxing](https://learn.chatgpt.com/docs/sandboxing), [Codex SDK](https://developers.openai.com/codex/sdk) |
| Gemini CLI | `-p`, `--output-format json`, `-s/--sandbox` with `GEMINI_SANDBOX=docker|podman|sandbox-exec`, Seatbelt profile default `permissive-open`, `--allowed-mcp-server-names`, policy files | No documented flag to disable built-in tools (unverified: the #5 probe decides); sandbox is container or seatbelt, not a completion lockdown | [Gemini sandbox docs](https://geminicli.com/docs/cli/sandbox.md) |
| E2B, Daytona, Modal | Hosted microVM or gVisor sandboxes | Infrastructure, not a library primitive; Daytona reportedly went closed source in June 2026 (single source) | [comparison](https://www.alexcloudstar.com/blog/sandboxing-ai-generated-code-execution-2026/) |

The hard answer on the SDK: for a Claude-only user who trusts their own environment, `query("...", ClaudeAgentOptions(tools=[], setting_sources=[], strict_mcp_config=True, max_turns=1, permission_mode="dontAsk", cwd=tmp))` is good enough, and the README should say so in the "what it is not" block. The remaining 30 percent is worth doing because every item in it is a thing that went wrong in public in the last twelve months (see demand below), and because nobody else packages it for Python.

Demand signals, last twelve months:

- Incidents: Claude Code deleted about 48,000 files and a Git object store in September 2026 ([TechRadar](https://techradar.com/pro/security/i-broke-something-a-claude-code-ai-agent-deleted-48-000-files-in-just-over-100-seconds-then-apologized-for-doing-so)); a December 2025 `rm -rf ... ~/` home-directory wipe ([Docker blog](https://www.docker.com/blog/coding-agent-horror-stories-the-rm-rf-incident/)); Codex GPT-5.6 ran `rm -rf /Users/<home>` and a `TRUNCATE TABLE users CASCADE` in July 2026 ([CyberSecurityNews](https://cybersecuritynews.com/gpt-5-6-codex-delete-files/)). "Show HN: Claude-File-Recovery" got 99 points in February 2026 ([HN](https://news.ycombinator.com/item?id=47182387)).
- Supply chain and injection: ClawHavoc poisoned the OpenClaw skill market, 341 of 2,857 skills flagged in January 2026, later counts near 900 to 1,184 ([Unit 42](https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/), [Antiy](https://www.antiy.net/p/clawhavoc-analysis-of-large-scale-poisoning-campaign-targeting-the-openclaw-skill-market-for-ai-agents/)); CVE-2026-32920, code execution from a cloned repository via workspace plugin auto-discovery ([Vulners](https://vulners.com/cvelist/CVELIST:CVE-2026-32920)); CSA research note on README and `CLAUDE.md` instruction injection, March 2026 ([CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-readme-instruction-injection-ai-coding-age/)); "Anthropic Claude Code sandbox bypass allows second data exfiltration exploit", May 2026 ([HN](https://news.ycombinator.com/item?id=48211229)).
- Terms: Anthropic's legal page says OAuth is "intended exclusively for purchasers" of subscription plans and that developers "including those using the Agent SDK, should use API key authentication"; it "reserves the right to take measures to enforce these restrictions and may do so without prior notice" ([legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)). Enforcement began 2026-01-09, the docs changed 2026-02-19, a customer email on 2026-04-04 extended it to all third-party harnesses ([lilting.ch](https://lilting.ch/en/articles/anthropic-claude-code-openclaw-third-party-paygo), [Gigazine](https://gigazine.net/gsc_news/en/20260220-anthropic-third-party-block)). This confirms ADR-001 decision 3 and argues against exporting `OwnLogin` prominently.
- What people ask for: HN threads "Coding Agents Degrade Sandboxes to Security Theater" (April 2026) and "Coding Agent Sandboxes Don't Solve Credential Authorization" (June 2026) got little traction (2 to 5 points) while "Show HN: Pi pod, run your coding agent in sandboxes on your own server" got 121 points in October 2026 ([HN](https://news.ycombinator.com/item?id=49937304)). Readers reward a runnable thing, not an essay. Simon Willison's framing ("lethal trifecta": private data, untrusted content, exfiltration channel) is the vocabulary to borrow ([post](https://simonwillison.net/2025/Oct/22/living-dangerously-with-claude/)).

## Design

Critique of `docs/API.md`, with concrete changes.

1. Dataclass config is right; a builder would add nothing for 12 fields. Keep `RunnerConfig` frozen, but validate in `__post_init__` (negative timeout, cap below 64 KiB, `binary_path` not absolute) and raise `ConfigError`, not at first `run()`.
2. `allow_path_lookup` "also skips strict owner/mode checks" fuses two decisions (where to find the binary, whether to trust it). Split them:

```python
@dataclass(frozen=True)
class RunnerConfig:
    binary_path: str | None = None
    binary_dir: str | None = None
    allow_path_lookup: bool = False            # dev only: shutil.which
    vetting: Literal["strict", "warn"] = "strict"
    credential: ApiKey                          # required, no default
    home: Literal["scratch", "inherit"] = "scratch"   # new, see 5
    ...
```

3. `credential: ApiKey | OwnLogin | None = None`. `None` has no safe meaning (origin refuses without a key unless owner mode, `cli_provider.py:1001-1013`), so make it required and typed `ApiKey` at the top level. `ApiKey` must redact its `repr` (a frozen dataclass with `value` would print the key in tracebacks and pytest output):

```python
@dataclass(frozen=True)
class ApiKey:
    env: str
    value: str = field(repr=False)
    def __repr__(self) -> str: return f"ApiKey(env={self.env!r}, value=<redacted>)"
```

4. `OwnLogin`: keep the code (owner decision), but expose it as `safe_cli_runner.credentials.OwnLogin`, not in `__init__`, with a constructor argument the caller must spell out (`OwnLogin(plan_holder_only=True)`) and the terms URL in the warning. It also forces `HOME` and `USER` through (origin `:328-331`), which on macOS means Keychain access from the child; document that it is incompatible with `home="scratch"`.
5. Fresh `HOME` in API-key mode (new). Today `HOME` is inherited (`_ENV_ALLOWLIST`, `cli_provider.py:54`), so the child sees `~/.claude`, `~/.claude.json`, and writes debug logs there outside the stdout cap. Setting `HOME` (or `CLAUDE_CONFIG_DIR`) to the scratch directory makes the user's dotfiles invisible for free. Risk: first-run onboarding behaviour of the CLI with an empty `HOME`; verify in the #9 live smoke before making it the default.
6. `max_concurrency` on the config but the semaphore on `Runner` means the module-level `run()` cannot honour it. Either `run()` uses a process-wide default `Runner` keyed by config, or document that concurrency applies only through `Runner`. Prefer the latter and say so in the docstring.
7. Sync wrapper: add `run_sync(...)` built on `asyncio.Runner`, raising `RuntimeError` if a loop is already running. Scripts and CI jobs are the first users; they are not async.
8. Errors: `CliUnavailable` is a dataclass in the origin (`:81-96`), not an exception, yet API.md lists it as raised. Give the package one base and one exception per outcome: `SafeCliError`; `CliBinaryError`; `CliCredentialError`; `CliExitError(returncode, stderr_tail)`; `CliTimeout(SafeCliError, TimeoutError)`; `CliOutputLimitError`; `PromptRefused(pattern_ids)`; `ModelNotInCatalog`; `SandboxRequired`; `LockdownViolation(audit)`. Keep `Runner.check() -> list[str]` for the readiness-report use the origin had. No exception message may contain prompt or completion text; `stderr_tail` may echo the prompt on CLI errors, so truncate it and say so.
9. Audit event: add `binary_real_path`, `binary_sha256` (hash once per `Runner`, cache by path, size, mtime), `cli_version` (one `--version` probe per `Runner`), `num_turns`, `is_error`, `lockdown_verified: bool`, `credential_mode`, `pid`, `started_at`, `kill_reason: Literal["none","deadline","cap","cancelled","abandoned"]`. Provide `AuditEvent.to_json()`. Deliver it also on failure paths (attach to every `SafeCliError`).
10. System prompt: the origin flattens it into stdin as `"{role}: ..."` text (`:586-601`), so it competes with Claude Code's own system prompt. The CLI has `--system-prompt` and `--append-system-prompt` (both present in `claude --help` of 2.1.310; print-mode behaviour unverified); use `--append-system-prompt` for the caller's system prompt and keep the stdin transcript for the turns. Keep label quoting either way.
11. Argv: add `--max-turns 1` (the CLI then stops itself; verification after the fact is the second line) and `--disallowedTools "mcp__*"`, because the official reference says `--tools` "doesn't affect MCP tools". Consider `--restricted` once the minimum CLI version is pinned at 2.1.248 (probe once; fall back without it).
12. Lockdown verification: hard failure. If `num_turns != 1`, `is_error`, or any `tool_use` appears, raise `LockdownViolation` carrying the audit event and withhold the content. A completion that was produced after a tool ran may contain what the tool read. Offer `on_violation="raise"` as the only v0.1 value; a `"flag"` mode can come later if a user asks, never as default.

## Improve

Do not copy as is:

| Origin (file:line) | Problem | Do instead |
|---|---|---|
| `cli_provider.py:54` `_ENV_ALLOWLIST = ("HOME", "TERM")` | `HOME` inherited in key mode | `home="scratch"` default (Design 5) |
| `cli_provider.py:247-263` `_claude_build_args` | No `--max-turns`, no MCP denial; `--safe-mode` is a troubleshooting flag per docs | Add `--max-turns 1`, `--disallowedTools "mcp__*"`; keep `--safe-mode` as belt and braces |
| `cli_provider.py:665-676` `_close_read_pipes` | Reads `process._transport`, a private asyncio attribute | Keep, but add a CI assertion that the attribute exists on 3.12, 3.13, 3.14, and a fallback that skips the fast close |
| `cli_provider.py:680-702` `_kill_process_group` | Correct, but a descendant that calls `setsid()` leaves the group | Document as a FLAGS limit; on Linux add `prctl(PR_SET_CHILD_SUBREAPER)` via `ctypes` and a `/proc` walk; the OS tier (pid namespace) is the real fix |
| `cli_provider.py:1063` `tempfile.mkdtemp(prefix="jervis-cli-")` | Origin name | `prefix="safe-cli-"`; `mkdtemp` is 0700, fine on both OSes |
| `cli_provider.py:1116-1117` tiktoken estimate | Dependency and false precision | Drop; `usage_estimated=True` with zeros, as planned |
| `cli_provider.py:1091-1096` `_check_exit` | Bare `RuntimeError` with stderr tail | `CliExitError`, tail truncated to 1,000 chars |
| `cli_binary.py:55` `_warned` module global | Process-wide mutable state in a library | Attribute on `Runner` |
| `cli_binary.py:181-190` `binary_problems` | Passes on hosted runners only if `/usr/local/bin` and ancestors are root- or runner-owned and not group-writable | Prove in the #9 smoke on ubuntu and macos runners before claiming "works in CI" |
| `prompt_injection.py:263-288` `_invisible_codepoints()` at import | Walks 0x21000 code points on `import` | `functools.cache`, computed on first scan |
| `prompt_injection.py:97-262` pattern table | Subset of the owner's Rust `injection-scanner` (84 patterns) | Record provenance and pattern ids in the module docstring; do not maintain two tables silently |
| Comments citing `#306`, `#307`, `ADR-028 D2` throughout | Point into a private tracker | Translate to this repo's issue numbers or plain prose during the port |

Where the three guarantees can still be bypassed under FLAGS:

- Env allowlist. Linux: a same-uid child reads `/proc/<ppid>/environ`; Yama `ptrace_scope=1` restricts attach, not this read. macOS: `ps -Eww` shows the environment of the user's other processes. Both OSes: files such as `~/.aws/credentials` are readable when `HOME` or the filesystem is visible. Only the OS tier (bwrap `--unshare-pid` with a fresh `/proc`, seatbelt `deny file-read*` outside the scratch dir) closes this. The README must call the allowlist hygiene.
- Process-group kill. Both OSes: a descendant that calls `setsid()` escapes `killpg`; PID reuse is not a problem because `wait()` has not run. Linux: `PR_SET_CHILD_SUBREAPER` or a cgroup scope catches escapees; macOS: nothing short of seatbelt or `launchd`.
- 4 MiB cap. Stdout only, and correct as written (about 4 MiB plus one chunk plus pipe buffers). Bypasses: writes to the scratch cwd and to `~/.claude/debug` (unbounded disk, fixed by fresh `HOME` and a `du` check on cleanup), and stderr (bounded tail, fine).

Tests missing beyond the port: argv contains `--max-turns 1`; `LockdownViolation` fixture with a `tool_use` line and with `num_turns: 2`; audit event never contains any prompt substring (property test with hypothesis over random prompts); `_quote_turn_labels` over every `str.splitlines` separator (parametrize `\r`, `\v`, `\f`, `\x85`, ` `, ` `); `/proc/self/environ` negative test on Linux (asserts the leak under FLAGS, documents it, xfail strict); `setsid` escapee test (expected orphan under FLAGS, asserts the warning log); fresh `HOME` first-run behaviour (live smoke); hosted-runner vetting on both OSes (live smoke); Python 3.14 in the matrix; `run_sync` inside a running loop raises.

## Build

| Item | State | Change |
|---|---|---|
| uv 0.11.32 by script, `uv sync --all-extras` | fine | `uv sync --locked --all-extras` so the lock is enforced; `uv lock --check` as a step |
| hatchling, src layout, sdist excludes | fine | Add `LICENSE` and `CHANGELOG.md` to the sdist explicitly; verify with `uv build && tar tzf dist/*.tar.gz` |
| ruff rule set (E F W I N UP B S A C4 SIM RUF ASYNC PT) | good | Add `D` for public modules once code exists, `TID` to ban relative imports; keep `S101` ignore in tests only (already) |
| `mypy --strict src` | good | Also `tests` with `disallow_untyped_defs`; `warn_unreachable` already on |
| pytest-asyncio strict, function loop scope | right for subprocess tests | Add `pytest-cov`, `--cov=safe_cli_runner --cov-fail-under=85 --cov-branch`; `-p no:cacheprovider` in CI |
| Matrix ubuntu-latest, macos-latest x 3.12, 3.13 | ok | Add 3.14 (classifier too); use `macos-14` per the portfolio convention or record the deviation; Windows stays deferred (S5), say so in README |
| Org policy: only `actions/checkout`, SHA pinned | satisfied | Means no Scorecard, codecov or pypi-publish actions; do everything with `uv run` and `gh`. Coverage: print the table in the log and fail on threshold; no badge service |
| `uv publish --trusted-publishing always` | fine | Confirm PEP 740 attestations are emitted (uv does this with trusted publishing; verify on the first TestPyPI upload) |
| Dependabot actions + uv monthly | fine | Add `pip-audit` (`uv run --with pip-audit pip-audit`) as a weekly `schedule` job; attach `pip-audit --format cyclonedx-json` SBOM to the GitHub release in `release.yml` |
| `py.typed`, `Typing :: Typed`, `Topic :: Security` classifiers | present | Add `Framework :: AsyncIO`, `Environment :: Console`, and `Development Status :: 3 - Alpha` at v0.1.0 |
| Reproducible lock | `uv.lock` committed | Add `requires-python` upper bound only if 3.15 breaks `_transport`; otherwise none |
| OpenSSF | none | A bestpractices.dev "passing" badge is reachable by hand (website, bug reporting, tests, release notes); do it at v0.1.0, not before |

## Develop

Working process for one person with an agent:

1. Port order, one issue per branch, TDD by oracle: copy the origin test file first, replace the six `config` monkeypatches with parameters, run it red against an empty module, then copy the origin code and make it green. Order: `binary.py` (#2, 29 tests), `process.py` + `transcript.py` (#3, 56), `gate.py` (#4, 30), `adapters/claude_code.py` only (#5, 21, Codex and OpenCode as unregistered modules, Gemini deferred), `runner.py` + `errors.py` (#6), lockdown (#7), `sandbox.py` enum and probe (#8).
2. The oracle check: `pytest --collect-only -q` in the origin filtered to `test_cli_*` lists 126 names; the same command here must list the same names (plus new ones) before #6 closes. Put the origin-to-new name mapping in each test module's docstring, not in a separate document.
3. Docs at 20 percent of commits: the convention is a cap, not a target. One docs commit after each closed issue (TODO tick, CHANGELOG line), nothing else. ADR-002 only when the OS tier is actually started. No new planning files.
4. Branches: `issue-N-short-name`, squash merge to `main`, CI must be green on both OSes. Releases: `0.1.0a1` to TestPyPI after #3 (the process core is the product), `0.1.0` after #8 and the smoke. Tag only from `main`, `release.yml` does the rest.
5. Live smoke (#9): `workflow_dispatch` only, never on PR; run it three times: once when the Claude adapter lands (field names for `num_turns`, `is_error`), once when fresh `HOME` is tried, once before tagging `v0.1.0`. Assert `num_turns == 1`, `cost_usd > 0`, vetting passes on the hosted runner, `~/.claude` untouched.
6. Agent hygiene for this repo: the agent never edits the origin; it reads it. Every ported function keeps a one-line "ported from `cli_provider.py:NNN`" comment so the next reviewer can diff.

## Deliver

The plan puts post 1 before step 3 (`docs/reviews/2026-10-24-deep-dive-and-plan.md`, "First 2 hours"). I would invert it: port #2 and #3 first (7 hours), publish `0.1.0a1`, then post with a runnable example. A security post without code gets "vaporware" replies; a post with `pip install safe-cli-runner==0.1.0a1` and a 10-line example gets issues.

| Day | Action | Channel |
|---|---|---|
| -7 to -1 | Port #2, #3, #6 minimum; `0.1.0a1` on TestPyPI then PyPI; GitHub topics `claude-code`, `codex`, `sandbox`, `llm`, `python`, `security`; README top block per convention; VHS GIF of the 30-second example | repo |
| 0 (Tue to Thu, 14:00 to 16:00 CET) | Post 1 on the owner's site; same hour one r/ClaudeAI post (convention: one per launch), two free hours for replies | blog, r/ClaudeAI |
| 0 | Plain HN submission of the post (not Show HN; nothing to "try" yet beyond pip) | HN |
| 1 | PR to `scadastrangelove/awesome-ai-security-tools`, section "AI Agent & Coding-Agent Security" (1,683 stars; check its acceptance rules, unverified) | awesome list |
| 7 | Post 2 "Killing a subprocess is the easy part" only if post 1 got any reply of substance | blog |
| 14 | `awesome-claude-code` eligibility: 14 days of commits after the first, issue form only, one resource, human-submitted, no `gh` ([CONTRIBUTING](https://github.com/hesreallyhim/awesome-claude-code/blob/main/CONTRIBUTING.md)); submit on day 14 to 21 | awesome list |
| 21 to 28 | `v0.1.0` with #7, #8, #9, #10; Show HN with the story (convention: day 30 to 60) | HN |
| 30 | Measure | decision |

"Continue" means, by day 30 after post 1: 25 stars or 3 external issues or PRs (portfolio S7). Softer but acceptable: one stranger's issue with a traceback (they ran it). Anything less: tag `v0.1.0`, add the "maintenance" badge, stop; the origin is frozen anyway.

Post 1 outline, 600 words, title "Your coding CLI is an LLM API with a shell attached":

1. The accident waiting to happen (120 words): `claude -p "summarise this"` from a directory loads `CLAUDE.md`, user hooks, MCP servers and all tools, with your whole environment. Link the 48,000-files story and the ClawHavoc campaign. One sentence: the model is not the risk, the shell around it is.
2. What a pure completion call needs (150 words, the code block): the argv `-p --output-format json --model haiku --tools "" --setting-sources "" --strict-mcp-config --safe-mode --no-session-persistence --max-turns 1`, prompt on stdin, fresh scratch cwd, one credential variable in an empty environment. Explain each flag in one line, cite the CLI reference.
3. What flags cannot do (130 words): PATH, the process tree, output size, binary trust, the parent environment visible through `/proc`. What the package does about each, and what only an OS sandbox does. Honest "flags are not a sandbox" paragraph.
4. Why not the Agent SDK (100 words): list what it covers (tools, settings, MCP, turns, budget, bundled binary) and what it inherits (environment, process tree, output). "If you only use Claude and trust your machine, use the SDK."
5. What this is and the ask (100 words): `pip install safe-cli-runner==0.1.0a1`, the 10-line example, the tier table, the three things coming next, and "tell me whether you would run this; if nobody needs it I stop at v0.1".

## Fable's opinion

1. The Agent SDK is the competitor and the README must name it in the first screen; a reader who finds out on their own that `tools=[]` exists will not come back.
2. Disagreement with the plan: code before post 1, not after; a security claim with nothing to install gets dismissed, and the port of #2 and #3 is one working day.
3. Disagreement with the plan: `OwnLogin` should not be a top-level export; Anthropic's page says it enforces "without prior notice", and a public package whose headline API offers the mode is a liability the owner does not need.
4. Disagreement with the plan: the gate should be off by default in a library whose child has no tools; an injection against a tool-less completion can only corrupt the answer, and false positives on legitimate security prompts will be the first issue filed.
5. `--max-turns 1` belongs in argv; verifying `num_turns` afterwards is the tripwire, not the control.
6. Fresh `HOME` in API-key mode is the highest-value change available to the FLAGS tier and it costs one live test.
7. The env allowlist is hygiene on both OSes and the README should say "a same-uid child can read your environment through `/proc` or `ps`"; a security library that overstates its boundary loses the only asset it has.
8. The OS tier should shell out to `srt` when present and generate profiles only as a fallback; Anthropic maintains those seatbelt and bwrap profiles with 6,500 stars of eyes, and a solo developer should not.
9. Codex, OpenCode and Gemini adapters add maintenance without demand in v0.1; ship Claude Code only, keep the other adapters unregistered as the origin does, and let an issue decide.
10. `LockdownViolation` must withhold the content; a result object with a `violated=True` flag will be logged and ignored in production.
11. Use the portfolio stop rule, not the plan's softer one; a single star is noise.
12. Python 3.14 must be in the matrix before v0.1.0 because the kill path depends on `process._transport`, and that is the kind of thing that breaks on a minor release.

## Open questions for a second opinion

1. With `tools=[]`, `setting_sources=[]`, `strict_mcp_config=True`, `max_turns=1`, `permission_mode="dontAsk"` and a caller-built `env`, is the Agent SDK good enough that the honest recommendation is "use the SDK", and the package should be a 200-line hardening layer on top of it rather than a parallel runner?
2. Should `home="scratch"` be the v0.1 default before the CLI's first-run behaviour with an empty `HOME` is known, or opt-in until the smoke proves it?
3. Hard failure that withholds content on `LockdownViolation`, or return the content with a flag and let the host decide?
4. OS tier: call `srt` (npm dependency, research preview) or generate seatbelt and bwrap argv natively (owner maintains profiles)?
5. Is the prompt gate worth anything when the child has no tools, or is it only a liability (false positives, maintenance of a second pattern table)?
6. Should `OwnLogin` exist in a public package at all, given the vendor's wording, or only in the frozen origin?
7. Is `process._transport` acceptable in a security library, or should the pipe-close path be rewritten on `anyio.open_process` so the kill does not depend on asyncio internals?
8. Post before code (plan) or code before post (this document)?

## Appendix: prompt for Claude Opus

```
You are Claude Opus, giving an independent second opinion on a small open-source Python package.

Read, in this order, in the repository /Users/jirihermann/Documents/workspace-current-projects/safe-cli-runner:
1. docs/reviews/2026-10-25-fable-analysis.md (this file, written by Claude Fable 5.1)
2. docs/reviews/2026-10-24-deep-dive-and-plan.md (the extraction plan)
3. docs/API.md, docs/adr/ADR-001-extracted-from-jervis.md, README.md, pyproject.toml, .github/workflows/ci.yml
Read only, never edit, the origin code: /Users/jirihermann/Documents/workspace-current-projects/ai-jervis-python/src/jervis/core/providers/cli_provider.py, cli_binary.py, and src/jervis/core/prompt_injection.py.
Verify the Agent SDK claims yourself: pip metadata of claude-agent-sdk, and the file src/claude_agent_sdk/_internal/transport/subprocess_cli.py in anthropics/claude-agent-sdk-python (env construction, kill path, tools flag, buffer size).

Then write ONE file, docs/reviews/2026-10-25-opus-analysis.md, 150 to 250 lines, plain Markdown with tables, no em-dashes anywhere, headed exactly:

# safe-cli-runner: Opus analysis (2026-10-25)

Author: Claude Opus (state your model id), second opinion requested by the owner.
Status: opinion document, responds to docs/reviews/2026-10-25-fable-analysis.md.

Sections, in this order:
1. Answers to the eight open questions in Fable's section "Open questions for a second opinion", numbered, each with a verdict in one sentence and the reasoning in at most five.
2. Where you disagree with Fable, as a table: Fable's statement, your position, the evidence (file:line or URL).
3. Where you disagree with the plan (docs/reviews/2026-10-24-deep-dive-and-plan.md), same table shape.
4. Your own ranked next three actions for the owner, with effort in hours and the issue number each maps to.
5. One paragraph: what you would tell a reader who asks "why not just use the Agent SDK".

Rules: every market claim carries a URL, every code claim carries file:line, write "unverified" where you could not check. Do not restate the plan or Fable's document; reference them. Do not commit, do not edit any other file, do not modify code in any repository. Finish by printing the path, the line count, and the count of U+2014 (em-dash) code points in your file, counted with Python or grep (it must be 0).
```
