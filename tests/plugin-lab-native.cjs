// Launch only the isolated lab with WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=
// --remote-debugging-port=19227, then attach this real-WebView smoke test.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
  const lab = path.resolve(process.env.PLUGIN_LAB_DIR || 'integration-build/PluginLab');
  const config = fs.readFileSync(path.join(lab, 'config.toml'), 'utf8');
  const key = config.match(/^management-secret-key\s*=\s*"([^"]+)"/m)?.[1];
  assert(key, 'Lab configuration must provide the fixture management key');
  const browser = await chromium.connectOverCDP('http://127.0.0.1:19227');
  try {
    const page = browser.contexts().flatMap(c => c.pages()).find(p => p.url().includes('tauri.localhost'));
    assert(page, 'Native Tauri page exists');
    page.setDefaultTimeout(45000);
    const status = await page.evaluate(() => window.__TAURI_INTERNALS__.invoke('get_core_status'));
    assert.equal(path.resolve(status.installDir).toLowerCase(), path.join(lab,'cpa-core').toLowerCase(), 'Only operate the separate lab core');
    if (!status.running) await page.evaluate(() => window.__TAURI_INTERNALS__.invoke('start_core_process'));
    await page.waitForFunction(async () => (await window.__TAURI_INTERNALS__.invoke('get_core_status')).ready, null, {timeout:60000});
    const nav = page.locator('.nav-section');
    await nav.getByRole('button', { name: 'Plugins', exact: true }).click();
    const pin = page.getByRole('checkbox', { name: 'Pin to sidebar: MCP Manager', exact: true });
    await pin.check();
    await nav.getByRole('button', { name: 'MCP Manager', exact: true }).click();
    const frame = page.frameLocator('iframe');
    await frame.getByRole('heading', { name: 'MCP Manager', exact: true }).waitFor();
    await frame.locator('#key').fill(key);
    await frame.getByRole('button', { name: 'Unlock', exact: true }).click();
    await frame.locator('#app').waitFor();
    assert.match(await frame.locator('#agent-path').innerText(), /sample-files/);
    await frame.getByRole('button', { name: /example-local/ }).click();
    assert.equal(await frame.locator('#command').inputValue(), 'node');
    fs.mkdirSync('test-artifacts', { recursive: true });
    await page.screenshot({path:'test-artifacts/native-mcp-pinned.png'});
    await page.reload();
    await nav.getByRole('button', {name:'MCP Manager',exact:true}).waitFor();
    await nav.getByRole('button', {name:'Plugins',exact:true}).click();
    assert.equal(await pin.isChecked(),true,'Native pins persist across page reload');
    const card=page.locator('.plugin-card').filter({has:page.getByRole('heading',{name:'MCP Manager',exact:true})});
    await card.locator('.plugin-icon img').waitFor();
    await page.screenshot({path:'test-artifacts/native-plugin-cards.png'});
    await card.getByRole('button',{name:'Find in store',exact:true}).click();
    await page.getByRole('combobox',{name:'Store source',exact:true}).waitFor();
    await page.screenshot({path:'test-artifacts/native-store.png'});
    console.log('PASS native WebView: real core, sidebar pin, real MCP plugin iframe/unlock, sample paths, persisted pin, card icon, store navigation');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
