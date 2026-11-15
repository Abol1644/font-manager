# Contributing to Glyph

Thanks for considering a contribution. Glyph is an early desktop prototype, so clear scope and accurate status reporting are especially useful.

## Before you start

- Check existing issues and pull requests for related work.
- For a substantial change, open an issue first to discuss its scope and approach.
- Keep changes focused and preserve the design system in `app/DESIGN.md` unless the issue explicitly concerns that system.
- Do not describe demo catalogue entries, CSS specimen behavior, or the variable-weight fixture as real font-engine functionality.

## Local setup

Use Node.js 22 or newer. From `app/` run:

```sh
npm ci
npm start
```

The separate Python feasibility study is documented in `docs/research/windows-font-spike.md`. It is research code, not the desktop app backend.

## Before opening a pull request

Run the checks from `app/`:

```sh
npm run typecheck
npm run lint
npm run package
```

Include a concise description of the user-visible change, the reason for it, the checks you ran, and any platform you could not verify. Add screenshots for meaningful UI changes. Update documentation when behavior, setup, or limitations change.

## Pull requests

- Keep the pull request focused and explain the problem it solves.
- Link the related issue when one exists.
- Call out changes to security boundaries, native integrations, bundled assets, or licensing.
- Do not include generated output, dependency folders, local databases, or machine-specific files.
- Do not claim CI, platform support, or release readiness until it has actually been verified.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
