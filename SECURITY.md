# Security policy

safe-cli-runner is a security component: its whole job is to run a coding CLI
in a way that cannot touch the host beyond a scratch directory. A bug that lets
the child process read, write or exfiltrate anything outside that scope is a
vulnerability, not a feature request.

## Supported versions

Nothing is released yet (2026-10-24). Once v0.1.0 is out, only the latest
minor release receives fixes.

## Reporting a vulnerability

Report privately through GitHub Security Advisories:

https://github.com/UnityInFlow/safe-cli-runner/security/advisories/new

Please include the CLI and version (`claude --version`, `codex --version`,
`gemini --version`), the operating system, the `RunnerConfig` you used with
secrets removed, and a minimal reproduction. Do not open a public issue for
anything that lets the child escape the documented scope.

You will get an acknowledgement within 7 days and a fix or a written
assessment within 30 days. Credit is given in the changelog unless you ask
otherwise.

## Out of scope

- Behaviour of the CLI vendors' own software beyond what this package
  configures (report those to Anthropic, OpenAI or Google).
- Prompt-injection text that the regex gate does not catch. The gate is a
  tripwire, not a control; see the threat-model table in the README.
- Anything that requires `allow_path_lookup=True`, which is documented as a
  development-only setting that skips the binary vetting.
