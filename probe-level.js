// Probe one level with enemy-state dumps (diagnose stalls).
// Usage: node probe-level.js <level 1-12> <seconds>
const { chromium } = require('/home/hatch/workspace/tools/pw-shot/node_modules/playwright-core');
const level = parseInt(process.argv[2] || '5', 10);
const budget = parseInt(process.argv[3] || '180', 10) * 1000;
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/meta-chromium/chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--allow-file-access-from-files',
      '--use-angle=swiftshader', '--autoplay-policy=no-user-gesture-required',
      '--hatch-webgl-allowed-domains-file=/home/hatch/workspace/tools/pw-shot/webgl-policy.txt',
      '--hatch-webgl-allowed-domains-sha256=dc8a0e5eec744f6590a4c1889139c00568ffedc3eced6d0a1a5127e35f9ccd16',
      '--disable-features=LocalNetworkAccessChecks', '--no-proxy-server'],
  });
  const page = await browser.newPage({ viewport: { width: 960, height: 640 } });
  page.on('pageerror', (e) => console.log('PAGEERROR: ' + e.message));
  await page.goto('file:///home/hatch/workspace/gamemonetize-restoration/starfall-defender/index.html?dtcap=0.12', { waitUntil: 'load' });
  await page.waitForFunction(() => window.__starfallLoaded === true, null, { timeout: 20000 });
  await page.evaluate(() => { window.__starfall.setAutopilot(true); window.__starfall.setGodMode(true); });
  await page.evaluate((n) => window.__starfall.pressPlay(n - 1), level);
  const t0 = Date.now();
  // wait out the 3s loading
  while (Date.now() - t0 < 15000) {
    const s = await page.evaluate(() => window.__starfall.state);
    if (s === 'playing') break;
    await sleep(500);
  }
  let lastKills = -1, stuckSince = 0;
  while (Date.now() - t0 < budget) {
    const d = await page.evaluate(() => ({
      state: window.__starfall.state, kills: window.__starfall.kills,
      leaked: window.__starfall.leaked, baseHp: window.__starfall.baseHp,
      quota: window.__starfall.quota, levelTime: window.__starfall.levelTime,
      debug: window.__starfall.debug,
    }));
    console.log(JSON.stringify(d));
    if (d.state !== 'playing') { console.log('END STATE: ' + d.state); break; }
    if (d.kills === lastKills) { if (!stuckSince) stuckSince = Date.now(); }
    else { lastKills = d.kills; stuckSince = 0; }
    await sleep(5000);
  }
  await browser.close();
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
