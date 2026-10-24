"""safe-cli-runner: run a coding CLI as a sandboxed, non-agentic LLM call.

Status (2026-10-24): bootstrapping. Nothing below is implemented yet; this
docstring records the planned v0.1 public API so that the package name,
import path and shape are fixed before the code is ported. The authoritative
copy lives in ``docs/API.md``; the plan is ``docs/reviews/2026-10-24-deep-dive-and-plan.md``.

Planned v0.1 public API::

    from safe_cli_runner import Runner, RunnerConfig, ApiKey, OwnLogin, Sandbox, run, stream
    from safe_cli_runner.adapters import CLAUDE_CODE, CODEX, GEMINI

    @dataclass(frozen=True)
    class RunnerConfig:
        binary_path: str | None = None          # pinned absolute path, or allow_path_lookup
        binary_dir: str | None = None
        allow_path_lookup: bool = False         # dev only; also skips strict owner/mode checks
        credential: ApiKey | OwnLogin | None = None   # ApiKey(env="ANTHROPIC_API_KEY", value)
        sandbox: Sandbox = Sandbox.FLAGS        # FLAGS | OS | CONTAINER; SandboxRequired if unmet
        timeout_s: float = 90.0
        max_stdout_bytes: int = 4 * 1024 * 1024
        max_concurrency: int = 2
        env_passthrough: tuple[str, ...] = ("HOME", "TERM")
        prompt_gate: Callable[[str], Awaitable[None]] | None = gate.default
        token_counter: Callable[[str], int] | None = None
        audit: Callable[[AuditEvent], None] | None = None   # argv, env NAMES, bytes, exit, cost

    async def run(messages: list[Message] | str, *, adapter=CLAUDE_CODE,
                  model: str | None = None, system_prompt: str = "",
                  config: RunnerConfig | None = None) -> CliResult
    async def stream(...) -> AsyncIterator[CliDelta | CliResult]

``CliResult``: ``content, model, adapter, input_tokens, output_tokens, usage_estimated,
cost_usd, duration_s, sandbox, audit: AuditEvent``.

Sandbox tiers: ``FLAGS`` (v0.1, Claude Code only), ``OS`` (v0.2, seatbelt or
bubblewrap), ``CONTAINER`` (v0.3). Adapters whose lockdown is partial refuse to
run under ``FLAGS`` and raise ``SandboxRequired``. Flags are not a sandbox.
"""

__version__ = "0.0.1.dev0"

__all__ = ["__version__"]
