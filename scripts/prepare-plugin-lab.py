"""Prepare a fresh Windows plugin integration lab; never reuse production settings."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import time
import tomllib
import zipfile
import yaml

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--plugins', type=Path, required=True, help='ecpa-plugins source workspace with packaged releases')
parser.add_argument('--core', type=Path, required=True, help='Known CLIProxyAPI v8.0.29 executable')
parser.add_argument('--output', type=Path, default=Path('integration-build/PluginLab'))
parser.add_argument('--port', type=int, default=18317)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
binary = root / 'src-tauri/target/release/cpa-gui.exe'
output = args.output.resolve()
assert binary.is_file() and args.core.is_file(), 'Build the GUI and provide the core first'
assert (args.core.parent / 'config.example.yaml').is_file(), 'Use an extracted official core release including config.example.yaml'
assert not output.exists(), 'Use a new output directory; existing lab data is never overwritten'
assert 1024 <= args.port <= 65535
catalogue = json.loads((args.plugins / 'registry.json').read_text())['plugins']
for entry in catalogue:
    entry['version'] = tomllib.loads((args.plugins / 'plugins' / entry['id'] / 'Cargo.toml').read_text())['package']['version']
    entry['archive'] = args.plugins / 'dist' / entry['id'] / f"{entry['id']}_{entry['version']}_windows_amd64.zip"
    assert entry['archive'].is_file(), entry['archive']
output.mkdir(parents=True)
core = output / 'cpa-core'
core.mkdir()
home = output / 'sample-files'
home.mkdir()
oauth = output / 'oauth'
oauth.mkdir()
shutil.copy2(binary, output / 'ECPA-Plugin-Lab.exe')
shutil.copy2(args.core, core / 'cli-proxy-api.exe')
shutil.copy2(args.core.parent / 'config.example.yaml', core / 'config.example.yaml')
registry = 'https://raw.githubusercontent.com/GoblinRules/ecpa-plugins/master/registry.json'
configs = {}
paths = {}
for field in ['claude_path', 'codex_path', 'codex_override_path', 'kimi_path', 'grok_path', 'zcode_path', 'antigravity_path', 'antigravity_agents_path']:
    path = home / (field + '.md')
    path.write_text('# Plugin Lab sample\n\nThis is a disposable test file.\n')
    paths[field] = path.as_posix()
paths['claude_config_path'] = (home / 'claude.json').as_posix()
paths['codex_config_path'] = (home / 'codex.toml').as_posix()
(home / 'claude.json').write_text(json.dumps({'mcpServers': {'example-local': {'command': 'node', 'args': ['example-server.js']}}}, indent=2))
(home / 'codex.toml').write_text('model = "fixture"\n[mcp_servers.example_remote]\nurl = "https://example.com/mcp"\n')
for field in ['claude_skills_dir', 'codex_skills_dir', 'extra_skills_dir']:
    path = home / field
    path.mkdir()
    paths[field] = path.as_posix()
    skill = path / 'example'
    skill.mkdir()
    (skill / 'SKILL.md').write_text('---\nname: example\ndescription: A disposable Plugin Lab sample.\n---\n\nReview this fixture.\n')
plugins = core / 'plugins/windows/amd64'
plugins.mkdir(parents=True)
for entry in catalogue:
    plugin_id, version = entry['id'], entry['version']
    with zipfile.ZipFile(entry['archive']) as archive:
        (plugins / f'{plugin_id}-v{version}.dll').write_bytes(archive.read(plugin_id + '.dll'))
    configs[plugin_id] = {**paths, 'enabled': True, 'data_dir': (home / 'records' / plugin_id).as_posix(),
        'store': {'source-url': registry, 'version': version, 'repository': entry['repository']}}
key = secrets.token_urlsafe(32)
(output / 'config.toml').write_text(f'''locale = "en"
port = {args.port}
host = "127.0.0.1"
allow-lan = false
run-on-startup = false
start-core-on-launch = true
silent-start = false
close-behavior = "exit"
auth-dir = {json.dumps(oauth.as_posix())}
auth-dir-user-selected = true
management-secret-key = {json.dumps(key)}
plugins-enabled = true
''')
(core / 'config.yaml').write_text(yaml.safe_dump({'host': '127.0.0.1', 'port': args.port,
    'auth-dir': oauth.as_posix(), 'api-keys': [secrets.token_urlsafe(32)],
    'remote-management': {'allow-remote': False, 'secret-key': key, 'disable-control-panel': True},
    'plugins': {'enabled': True, 'dir': (core / 'plugins').as_posix(), 'store-sources': [registry], 'configs': configs}}, sort_keys=False))
(core / 'cpa-gui-meta.json').write_text(json.dumps({'version': '8.0.29', 'assetName': 'CLIProxyAPI_8.0.29_windows_amd64.zip', 'installedAtUnix': int(time.time())}))
# Deliberately omit portable-app.json: the stock updater must not replace this lab build.
(output / 'Launch-Plugin-Lab.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\nstart "" "%~dp0ECPA-Plugin-Lab.exe"\r\n')
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
(output / 'build-info.json').write_text(json.dumps({'source': commit, 'branch': 'integration/plugin-experience',
    'pullRequests': [457, 458, 459, 460], 'port': args.port,
    'plugins': {entry['id']: entry['version'] for entry in catalogue},
    'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}, indent=2))
(output / 'README.txt').write_text(f'''ECPA Plugin Lab - local integration build

Run Launch-Plugin-Lab.cmd. This app uses its own browser profile, config.toml,
core, OAuth directory and port ({args.port}). Your installed app is not replaced.
The seven bundled plugins point to sample-files in this directory.
Sample MCP definitions are illustrative and do not start a working MCP server.

Try Plugins -> Pin to sidebar, Find in store, Check for updates, Store source,
and plugin artwork. Restart the lab to check saved sidebar pins.
The management key for unlocking plugin editors is in this lab's config.toml.

This is not an operating-system sandbox. Other app features, particularly
Agent Configuration and system proxy controls, can affect real system settings.
Keep this test focused on Plugins. Do not configure real accounts here.
Paths are absolute; regenerate the package if moving its folder.
No automatic app updater is enabled for this custom build.
Source revision at packaging: {commit}
''')
print(f'Prepared {output}; core port {args.port}; {len(catalogue)} fixture plugins')
