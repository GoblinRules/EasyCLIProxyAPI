# ECPA Plugin Lab

This fork-only integration branch combines the four independently proposed plugin changes on upstream `d64dda6`:

- [#457](https://github.com/router-for-me/EasyCLIProxyAPI/pull/457): optional sidebar pins.
- [#458](https://github.com/router-for-me/EasyCLIProxyAPI/pull/458): Find in store and Check for updates.
- [#459](https://github.com/router-for-me/EasyCLIProxyAPI/pull/459): store-source dropdown.
- [#460](https://github.com/router-for-me/EasyCLIProxyAPI/pull/460): declared plugin artwork.

The integration branch is `integration/plugin-experience`. Individual PR branches remain separate for upstream review. Do not submit this entire branch as an additional upstream PR.

## Build and prepare on Windows

```powershell
bun install --frozen-lockfile
python -m pip install PyYAML
./scripts/build-plugin-lab.ps1
python scripts/prepare-plugin-lab.py --plugins C:/path/to/ecpa-plugins --core C:/path/to/cli-proxy-api.exe
```

The core must be v8.0.29; plugin archives must already be packaged under their per-plugin `dist` directories. The preparation script requires a new output directory, copies the executable/core/plugins, creates sample agent files, and configures all bundled plugin file paths to those samples. It does not read personal agent content or production credentials.

Launch `integration-build/PluginLab/Launch-Plugin-Lab.cmd`. The lab has a distinct product name and application identifier, separate WebView profile, local app/core settings and credentials, and core port 18317 (override `--port` when preparing). No stock portable-update marker is installed. It cannot overwrite the production app through the stock auto-updater.

This is not an OS sandbox. Other features such as Agent Configuration and system proxy controls still have their normal access. Keep evaluation focused on Plugins. Plugin editor unlock credentials are in the lab's `config.toml`; do not share that file or the generated runtime directory publicly. The fixture paths are absolute, so regenerate the lab after moving it.

## Integration findings

- Resolved overlapping imports, card actions and styles without dropping any of the four features.
- Find in store and Check for updates must reset the new store-source filter as well as the ordinary filter. Otherwise a plugin in another store stays hidden. The combined browser test covers this interaction.
- The upstream source has two `clearInterval` type errors with the installed type definitions. Explicit undefined guards in `AuthFileHealthStatus.tsx` and `quotaTime.ts` allow a full checked build; these are integration-only build fixes.
- The full-app pinning browser test now scans its actual entry point rather than all unrelated fixture pages during dependency optimization.

## Checks

Verified on Windows, 2026-10-15: full TypeScript/Vite and optimized Tauri build; 8 targeted unit tests; both combined browser workflows; real WebView opening/unlocking MCP Manager against the separate core; sidebar persistence; real store navigation; and a clean application restart with core v8.0.29 auto-start and restored sidebar pin. Four upstream unused-code warnings remain in the Rust build. The native check validates navigation, not an actual plugin upgrade/download.

Packaging must copy the core's `config.example.yaml`, write `cpa-gui-meta.json` with camelCase fields, and generate block-style YAML for the core configuration. JSON-shaped YAML works in the core but does not work with the app's config rewriting path; these details were caught and corrected during native startup testing.

Use the build wrapper above: application update manifests validate their GitCode fallback URLs even when fetched through GitHub. Omitting the official build's `GITCODE_GUI_REPOSITORY` and `GITCODE_CORE_REPOSITORY` compile-time settings makes all app-version checks fail. The wrapper supplies those settings without changing the calling shell permanently. Check detection only in this lab; keep its custom executable rather than installing a stock app update.

```powershell
bun test tests/pluginPins.test.ts tests/pluginUpdates.test.ts tests/pluginStoreSources.test.ts
$env:PLAYWRIGHT_MODULE='C:/path/to/node_modules/playwright'
$env:PLUGIN_SCREENSHOT_DIR='test-artifacts'
node tests/plugins-ui.cjs
node tests/plugin-pins-ui.cjs
```

These browser workflows use explicit fixture data. They exercise plugin states, card artwork/fallbacks, source and update filters, store shortcuts, configuration, installation, uninstallation, sidebar pin lifecycle and responsive English/Chinese layouts. Screenshots are written to `test-artifacts` when requested.

Passing this integration suite reduces merge risk; upstream changes, other operating systems and external service behavior still need review when the PRs are merged. Keep further feature fixes on the relevant individual PR branches and merge them into this integration branch again for combined verification.

For a native WebView smoke test, launch only the lab executable with the temporary environment variable `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=19227`, then run `node tests/plugin-lab-native.cjs` with the same Playwright module setting. The test verifies the core installation path before operating the UI, opens the real MCP Manager iframe, checks its sample-file path, tests pin persistence and navigates to the real store. Remove the debugging environment variable for normal use. Do not run this against the installed production app.
