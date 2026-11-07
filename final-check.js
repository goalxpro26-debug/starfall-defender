// Final visual + input verification for Starfall Defender.
// 1) menu screenshot (no clipped title), 2) real keyboard input moves the
// ship and fires, P pauses/resumes, 3) mid-boss-fight screenshot (L4),
// 4) L1 autopilot smoke completion on the final build.
const { chromium } = require('/home/hatch/workspace/tools/pw-shot/node_modules/playwright-core');
const fs = require('fs');
const outDir = '/home/hatch/workspace/gamemonetize-restoration/starfall-defender/test-evidence';
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
  const errs = [];
  page.on('pageerror', (e) => errs.push('PAGEERROR: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error' && !m.text().includes('ERR_SSL')) errs.push('CONSOLE: ' + m.text().slice(0, 200)); });
  await page.goto('file:///home/hatch/workspace/gamemonetize-restoration/starfall-defender/index.html?dtcap=0.12', { waitUntil: 'load' });
  await page.waitForFunction(() => window.__starfallLoaded === true, null, { timeout: 20000 });
  await sleep(400);
  await page.screenshot({ path: outDir + '/07-menu-final.png' });
  const menuBox = await page.evaluate(() => {
    const h = document.querySelector('#menuScreen h1').getBoundingClientRect();
    const g = document.getElementById('levelGrid').getBoundingClientRect();
    return { titleTop: Math.round(h.top), titleH: Math.round(h.height), gridBottom: Math.round(g.bottom) };
  });
  console.log('MENU layout: ' + JSON.stringify(menuBox) + ' (titleTop>=0 and gridBottom<=640 means nothing clipped)');

  // --- real keyboard input ---
  await page.click('#playBtn');
  await page.waitForFunction(() => window.__starfall.state === 'playing', null, { timeout: 15000 });
  const x0 = await page.evaluate(() => window.__starfall.debug.player.x);
  await page.keyboard.down('ArrowLeft');
  await sleep(900);
  await page.keyboard.up('ArrowLeft');
  const x1 = await page.evaluate(() => window.__starfall.debug.player.x);
  console.log('KEYBOARD ArrowLeft: x ' + x0.toFixed(0) + ' -> ' + x1.toFixed(0) + ' (moved left: ' + (x1 < x0 - 50) + ')');
  await page.keyboard.down('Space');
  await sleep(700);
  const bullets = await page.evaluate(() => window.__starfall.debug.bullets);
  await page.keyboard.up('Space');
  console.log('KEYBOARD Space: bullets in flight = ' + bullets + ' (fired: ' + (bullets > 0) + ')');
  await page.keyboard.press('p');
  await sleep(300);
  const paused = await page.evaluate(() => window.__starfall.state);
  await page.keyboard.press('p');
  await sleep(300);
  const resumed = await page.evaluate(() => window.__starfall.state);
  console.log('KEYBOARD P: paused=' + paused + ' resumed=' + resumed);
  // finish L1 with autopilot (smoke test of final build)
  await page.evaluate(() => window.__starfall.setAutopilot(true));
  const t0 = Date.now();
  let st = '';
  while (Date.now() - t0 < 240000) {
    st = await page.evaluate(() => window.__starfall.state);
    if (st === 'complete') break;
    await sleep(1000);
  }
  console.log('L1 smoke on final build: ' + st);

  // --- mid-boss-fight screenshot (L4) ---
  await page.evaluate(() => { window.__starfall.setAutopilot(true); window.__starfall.setGodMode(true); window.__starfall.pressPlay(3); });
  await page.waitForFunction(() => window.__starfall.state === 'playing', null, { timeout: 15000 });
  await sleep(12000);
  const boss = await page.evaluate(() => ({ hp: window.__starfall.bossHp, max: window.__starfall.bossMaxHp }));
  console.log('BOSS mid-fight: hp=' + boss.hp + '/' + boss.max);
  await page.screenshot({ path: outDir + '/08-boss-fight.png' });

  console.log('ERRORS (excluding SDK SSL load): ' + errs.length, errs);
  await browser.close();
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
