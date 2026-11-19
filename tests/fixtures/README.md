# npm golden wrapper fixtures

Six files were produced on 2026-11-19 by the host's existing npm `cmd-shim`
**8.0.0**, using its `cmdShim(from, to)` function in a fresh temporary folder.
No package was installed. The Node input began with `#!/usr/bin/env node`; the
native input was inert `MZ_SYNTHETIC_ONLY` bytes without a shebang. The package
targets were `node_modules/@openai/codex/bin/codex.js` and
`node_modules/@anthropic-ai/claude-code/claude.exe` respectively.

The files are literal generator output, independent of the doctor's matching
function. Tests substitute the package/bin path only. They are data fixtures,
never executed. The exit-7 regression executes only a separately constructed,
fixed synthetic CMD file. See [third-party license](../../THIRD_PARTY_NOTICES.md).
