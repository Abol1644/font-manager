# Security policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately through GitHub's **Report a vulnerability** feature in this repository's **Security** tab when private vulnerability reporting is enabled. This lets maintainers review a report without exposing exploit details publicly.

If the private reporting control is unavailable, use [GitHub Support](https://support.github.com/contact) and request a private security report route for the repository. Do not post credentials, private data, or an actionable exploit in a public issue.

Please include the affected version or commit, the environment, reproduction steps, and the impact. A report is not a promise of a particular response time; maintainers will assess and coordinate a fix where appropriate.

## Scope and current status

Glyph is an early prototype. The Electron renderer currently uses sandboxing, context isolation, disabled Node integration, a restrictive content security policy, and a narrow preload API. These controls have not been independently audited.

The separate Python font feasibility spike parses local font files and is not a production app service. Future font parsing and preview functionality should treat font files as untrusted input and use process isolation and resource limits.

## Supported versions

There are no published stable releases yet. For now, reports against the current `main` branch are welcome.
