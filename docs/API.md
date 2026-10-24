# Planned public API (v0.1)

Status (2026-10-24): design only, nothing implemented. This is the contract the
port in issues #2 to #8 implements; changes to it go through an ADR.

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
duration_s, sandbox, audit: AuditEvent`.

Extras (gated on demand, see the plan): `[langgraph]` adds `as_langchain_tool()`,
`[pydantic-ai]` adds `as_pydantic_ai_tool()`, `[tiktoken]` gives exact local token counts
(without it `usage_estimated=True` when the CLI does not report usage).

## Modules

| Module | Holds |
|---|---|
| `safe_cli_runner.binary` | `resolve_cli_binary`, `binary_problems`, `ResolvedCliBinary` (pinning and vetting up the directory chain) |
| `safe_cli_runner.process` | env allowlist, capped and deadline-bound subprocess run, process-group kill, pipe close |
| `safe_cli_runner.transcript` | roles, turn-label quoting, prompt flattening, Unicode normalisation |
| `safe_cli_runner.gate` | regex injection gate; `gate.default`, on by default, `prompt_gate=None` disables |
| `safe_cli_runner.adapters` | `CLAUDE_CODE`, `CODEX`, `OPENCODE`, `GEMINI` with a `lockdown` field (`FULL` or `PARTIAL`) |
| `safe_cli_runner.runner` | `RunnerConfig`, `Runner` (owns the semaphore), `run`, `stream`, `CliResult`, `CliDelta`, `AuditEvent` |
| `safe_cli_runner.sandbox` | `Sandbox` enum, `Lockdown` enum, `probe()` |
| `safe_cli_runner.errors` | `CliBinaryError`, `CliCredentialError`, `CliUnavailable`, `CliOutputLimitError`, `SandboxRequired`, `LockdownViolation` |

## Errors

| Error | Raised when |
|---|---|
| `CliBinaryError` | the pinned binary, its directory chain or the interpreter fails vetting |
| `CliCredentialError` | `credential` is missing or the named env var is empty |
| `CliUnavailable` | the CLI exits non-zero or cannot be started; carries a short machine code |
| `CliOutputLimitError` | stdout exceeded `max_stdout_bytes` (the child is killed first) |
| `SandboxRequired` | the adapter's lockdown is `PARTIAL` and `config.sandbox` is `FLAGS`, or the requested tier is unavailable per `probe()` |
| `LockdownViolation` | the result JSON shows `num_turns > 1` or any tool use |

## Guarantees the audit event makes

`AuditEvent` carries argv, the names (never values) of environment variables passed,
stdout and stderr byte counts, exit status, duration, reported cost and the sandbox tier.
It never carries prompt or completion text.
