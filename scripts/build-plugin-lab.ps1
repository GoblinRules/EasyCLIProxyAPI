$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
$previousGui = $env:GITCODE_GUI_REPOSITORY
$previousCore = $env:GITCODE_CORE_REPOSITORY
try {
    # Match the official build's fallback metadata, required by update validation.
    $env:GITCODE_GUI_REPOSITORY = 'lzt404/EasyCLIProxyAPI'
    $env:GITCODE_CORE_REPOSITORY = 'lzt404/CLIProxyAPI'
    bun tauri build --no-bundle --config src-tauri/tauri.integration.conf.json
    if ($LASTEXITCODE -ne 0) { throw 'Plugin Lab build failed' }
} finally {
    $env:GITCODE_GUI_REPOSITORY = $previousGui
    $env:GITCODE_CORE_REPOSITORY = $previousCore
    Pop-Location
}
