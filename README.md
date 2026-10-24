# safe-cli-runner

`claude -p` as a function call that provably cannot touch your machine.

safe-cli-runner runs Claude Code, Codex or Gemini CLI as a plain, non-agentic LLM
call from Python: one prompt in, one answer out, no tools, no MCP servers, no
settings files, no session on disk, no access to anything but a fresh scratch
directory. It pins and vets the binary instead of trusting `PATH`, passes the
prompt on stdin, injects exactly one credential variable into an otherwise empty
environment, enforces a byte cap and a deadline while reading, and kills the whole
process group when either trips. It is an isolation primitive, not an
orchestration framework: it does not plan, retry, route or keep state. Use it
from whatever already does.

**Status (2026-10-24): bootstrapping, v0.1.0 not yet released.** The code is
being extracted from an internal project where it has 126 unit tests and three
months of review behind it. Plan and progress:
[`docs/reviews/2026-10-24-deep-dive-and-plan.md`](docs/reviews/2026-10-24-deep-dive-and-plan.md),
checklist: [`docs/TODO.md`](docs/TODO.md).

## 30 seconds (planned v0.1 API)

```python
import asyncio
import os

from safe_cli_runner import ApiKey, RunnerConfig, run

config = RunnerConfig(
    binary_dir="/usr/local/bin",
    credential=ApiKey("ANTHROPIC_API_KEY", os.environ["ANTHROPIC_API_KEY"]),
)

result = asyncio.run(run("Summarise this diff", config=config))
print(result.content, result.cost_usd, result.sandbox)
```

Install, once released: `pip install safe-cli-runner`. Only runtime dependency:
`anyio`. Python 3.12 or newer, macOS and Linux.

The full planned API is in [`docs/API.md`](docs/API.md).

## Sandbox tiers

| Tier | What it is | Version | Eligible adapters |
|---|---|---|---|
| `FLAGS` | The CLI's own lockdown flags (`--tools "" --setting-sources "" --strict-mcp-config --safe-mode --no-session-persistence`), prompt on stdin, fresh temporary cwd, env allowlist, process-group kill, 4 MiB stdout cap enforced while reading, deadline, binary vetting up the directory chain, model catalog check, transcript role quoting, injection gate, plus a post-run check that the CLI did not use a tool or take more than one turn (`LockdownViolation`) | v0.1 | Claude Code only. Codex and OpenCode cannot disable tools by flag and raise `SandboxRequired` |
| `OS` | macOS `sandbox-exec` (seatbelt) profile or Linux `bubblewrap`: read-only bind of the vetted binary dir and interpreter, tmpfs `HOME` holding only the auth file the CLI needs, no writable path but the scratch cwd, network allowed for the provider endpoint. `probe()` reports availability; `sandbox=Sandbox.OS` fails if unavailable | v0.2 | Codex (`--sandbox read-only` inside), Gemini, OpenCode |
| `CONTAINER` | docker or podman with an egress proxy allowlist and CPU and memory limits | v0.3 | hosted or multi-tenant use |

## Flags are not a sandbox

`FLAGS` is what exists today and what has the tests. It relies on the CLI
honouring its own flags: a bug or a deliberate change in the CLI, or a prompt that
talks it into something the flags do not cover, is not stopped by this tier. That
is why the runner reads the result and fails closed if the CLI reports any tool
use or more than one turn, why adapters that cannot disable tools refuse to run
under `FLAGS` at all, and why the `OS` tier (the same seatbelt and bubblewrap
mechanisms the CLI vendors' own sandboxes use) is the next step rather than a
nice-to-have. Until you run under `OS` or `CONTAINER`, treat the child as a
process with your user's permissions that has been politely asked to behave.

## What it is not

- Not an agent framework: no tools, no loops, no memory. Paperclip and OpenAI
  Symphony own orchestration; this is the thing they would call.
- Not a way around API billing. The default and tested path is an API key passed
  as one environment variable. Subscription login (`OwnLogin`) is an explicit,
  warned, local-only opt-in.
- Not a replacement for the vendor SDK when you can use it. Use this when the CLI
  is what you have, or when you want the CLI's model catalog and cost reporting
  without the CLI's reach.

## Origin and licence

Extracted from an internal project (copy, not move; the origin keeps its own
copy). Decisions are recorded in [`docs/adr/ADR-001-extracted-from-jervis.md`](docs/adr/ADR-001-extracted-from-jervis.md).
Licensed under Apache-2.0, see [`LICENSE`](LICENSE). Security reports:
[`SECURITY.md`](SECURITY.md).
