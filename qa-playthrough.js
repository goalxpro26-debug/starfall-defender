// Starfall Defender — headless QA playthrough (playwright-core).
// Usage: node qa-playthrough.js <baseUrl> <outDir>
// Plays level 1 legit (autopilot, NO god mode), reloads to verify save/resume,
// then sweeps levels 2-12 with autopilot+god mode, verifying bosses, saves,
// pause/mute, and collecting console errors. Writes results.json + screenshots.
const { chromium } = require('/home/hatch/workspace/tools/pw-shot/node_modules/playwright-core');
const fs = require('fs');
const path = require('path');

const base = process.argv[2] || 'http://127.0.0.1:8907/index.html';
// ?dtcap=0.12 accelerates headless testing only (see index.html: the cap
// never binds at real 60 fps play, so shipped behaviour is unchanged).
const url = base.includes('?') ? base + '&dtcap=0.12' : base + '?dtcap=0.12';
const outDir = process.argv[3] || '/home/hatch/workspace/gamemonetize-restoration/starfall-defender/test-evidence';
fs.mkdirSync(outDir, { recursive: true });

const results = { startedAt: new Date().toISOString(), checks: [], levels: {}, errors: [], warnings: [] };
function check(name, ok, detail) {
  results.checks.push({ name, pass: !!ok, detail: detail || '' });
  console.log((ok ? 'PASS' : 'FAIL') + ' | ' + name + (detail ? ' | ' + detail : ''));
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function waitState(page, want, timeoutMs, label) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    const s = await page.evaluate(() => window.__starfall && window.__starfall.state);
    if (s === want) return true;
    if (s === 'over' && want !== 'over') return 'over';
    if (s === 'victory' && want === 'complete') return 'victory';
    await sleep(500);
  }
  const s = await page.evaluate(() => window.__starfall && window.__starfall.state);
  console.log('TIMEOUT waiting for ' + want + ' (' + label + '), state=' + s);
  return false;
}

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
  page.on('pageerror', (e) => results.errors.push('PAGEERROR: ' + e.message));
  page.on('console', (m) => {
    if (m.type() === 'error') results.errors.push('CONSOLE: ' + m.text().slice(0, 300));
  });
  page.on('requestfailed', (r) => {
    const u = r.url();
    if (!u.includes('gamemonetize.com')) results.errors.push('REQFAIL: ' + u + ' ' + (r.failure() || {}).errorText);
    else results.warnings.push('sdk unreachable (expected off-portal): ' + u);
  });

  await page.goto(url, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__starfallLoaded === true, null, { timeout: 20000 });
  await sleep(500);

  // --- 1. menu / assets / no ad on load ---
  const boot = await page.evaluate(() => ({
    ready: window.__starfall.ready, state: window.__starfall.state,
    img: window.__starfall.imagesLoaded + '/' + window.__starfall.imagesTotal,
    levels: window.__starfall.levels.length,
    save: window.__starfall.save, gmPreRoll: window.__starfall.gmPreRollShown,
    gmAvailable: window.__starfall.gmAvailable, sdkType: typeof window.sdk,
  }));
  check('boot: menu state', boot.state === 'menu', JSON.stringify(boot));
  check('boot: all images loaded', boot.img === '18/18', boot.img);
  check('boot: 12 levels defined', boot.levels === 12, String(boot.levels));
  check('boot: fresh save unlocked=1', boot.save.unlocked === 1, JSON.stringify(boot.save));
  check('boot: NO ad on load (preRoll false)', boot.gmPreRoll === false, 'preRoll=' + boot.gmPreRoll);
  check('boot: SDK absent is tolerated (game runs anyway)', boot.sdkType === 'undefined' || boot.gmAvailable === false, 'sdk=' + boot.sdkType);
  const gridCount = await page.evaluate(() => document.querySelectorAll('#levelGrid .lvl').length);
  check('menu: 12 level buttons', gridCount === 12, String(gridCount));
  const lockedCount = await page.evaluate(() => document.querySelectorAll('#levelGrid .lvl.locked').length);
  check('menu: 11 locked at start', lockedCount === 11, String(lockedCount));
  const fps = await page.evaluate(() => new Promise(res => {
    let n = 0; const t0 = performance.now();
    (function f() { n++; if (performance.now() - t0 < 3000) requestAnimationFrame(f); else res((n / 3).toFixed(1)); })();
  }));
  results.headlessFps = fps;
  console.log('HEADLESS FPS (SwiftShader, menu): ' + fps);
  await page.screenshot({ path: path.join(outDir, '01-menu.png') });

  // --- 2. PLAY -> 3s loading -> playing; ad fires on PLAY only ---
  await page.click('#playBtn');
  await sleep(600);
  const loading = await page.evaluate(() => ({
    state: window.__starfall.state,
    loadingVisible: !document.getElementById('loadingScreen').classList.contains('hidden'),
    preRoll: window.__starfall.gmPreRollShown,
  }));
  check('play: loading screen shows', loading.state === 'loading' && loading.loadingVisible, JSON.stringify(loading));
  const tLoad0 = Date.now();
  await waitState(page, 'playing', 10000, 'after loading');
  const loadMs = Date.now() - tLoad0;
  check('play: loading lasts ~3s', loadMs >= 2000 && loadMs <= 4500, loadMs + 'ms after click+600ms wait');
  await sleep(1000);
  await page.screenshot({ path: path.join(outDir, '02-level1-play.png') });

  // --- 3. Level 1, autopilot, NO god mode (legit playability) ---
  await page.evaluate(() => window.__starfall.setAutopilot(true));
  const l1 = await playLevel(page, 1, 600000);
  results.levels[1] = l1;
  check('L1 completes without god mode', l1.outcome === 'complete', JSON.stringify(l1));
  await page.screenshot({ path: path.join(outDir, '03-level1-complete.png') });

  // --- 4. Save / resume: reload, continue must offer level 2 ---
  await page.reload({ waitUntil: 'load' });
  await page.waitForFunction(() => window.__starfallLoaded === true, null, { timeout: 20000 });
  const afterReload = await page.evaluate(() => ({
    save: window.__starfall.save, state: window.__starfall.state,
    cont: document.getElementById('continueBtn').textContent,
  }));
  check('save: reload keeps unlocked=2 + stars', afterReload.save.unlocked === 2 && afterReload.save.stars['1'] >= 1,
    JSON.stringify(afterReload.save) + ' | btn="' + afterReload.cont + '"');
  check('save: menu after reload', afterReload.state === 'menu', afterReload.state);

  // --- 5. Pause / mute / GM event simulation ---
  await page.evaluate(() => window.__starfall.pressPlay(0));
  await waitState(page, 'playing', 10000, 're-enter L1');
  await page.evaluate(() => window.__gamemonetize.simulatePause());
  await sleep(400);
  const paused = await page.evaluate(() => window.__starfall.state);
  check('GM SDK_GAME_PAUSE pauses game', paused === 'paused', paused);
  await page.evaluate(() => window.__gamemonetize.simulateResume());
  await sleep(400);
  const resumed = await page.evaluate(() => window.__starfall.state);
  check('GM SDK_GAME_START resumes game', resumed === 'playing', resumed);
  await page.evaluate(() => window.__starfall.setMuted(true));
  const muted = await page.evaluate(() => window.__starfall.muted);
  check('mute toggle works', muted === true, String(muted));
  await page.evaluate(() => window.__starfall.setMuted(false));
  await page.evaluate(() => { window.__starfall.setAutopilot(false); window.__starfall.renderMenu(); });

  // --- 6. Full sweep levels 2..12, autopilot + god mode ---
  await page.evaluate(() => { window.__starfall.setAutopilot(true); window.__starfall.setGodMode(true); });
  for (let n = 2; n <= 12; n++) {
    const r = await playLevel(page, n, 900000);
    results.levels[n] = r;
    const isBoss = [4, 8, 12].includes(n);
    const want = n === 12 ? 'victory' : 'complete';
    check('L' + n + (isBoss ? ' (BOSS)' : '') + ' completes', r.outcome === want,
      JSON.stringify(r));
    if (isBoss) check('L' + n + ' boss was present (hp seen)', r.bossSeen === true, 'bossHp max seen=' + r.bossMaxSeen);
    if (n === 4) await page.screenshot({ path: path.join(outDir, '04-boss-level4.png') }).catch(() => {});
    if (n === 12) await page.screenshot({ path: path.join(outDir, '05-victory.png') }).catch(() => {});
    if (r.outcome === 'complete') { // advance via Next button (real UI path)
      await page.click('#nextBtn').catch(() => {});
      await waitState(page, 'playing', 10000, 'next level start L' + (n + 1));
    }
  }
  // After victory, menu should show all unlocked + stars
  await page.evaluate(() => window.__starfall.renderMenu());
  await sleep(400);
  const finalSave = await page.evaluate(() => window.__starfall.save);
  check('final: all 12 levels unlocked', finalSave.unlocked === 12, JSON.stringify(finalSave));
  check('final: stars recorded for all 12', Object.keys(finalSave.stars).length === 12, JSON.stringify(finalSave.stars));
  await page.screenshot({ path: path.join(outDir, '06-menu-all-unlocked.png') });

  // --- 7. enemy variety: distinct image per level (from hook data) ---
  const variety = await page.evaluate(() => window.__starfall.levels);
  const imgs = new Set(variety.map(l => l.enemy));
  check('enemy variety: 12 distinct enemy images', imgs.size === 12, [...imgs].join(','));

  results.finishedAt = new Date().toISOString();
  results.totalAutopilotSeconds = Object.values(results.levels).reduce((a, l) => a + (l.seconds || 0), 0);
  fs.writeFileSync(path.join(outDir, 'results.json'), JSON.stringify(results, null, 2));
  console.log('\n=== SUMMARY ===');
  console.log('levels:', JSON.stringify(results.levels));
  console.log('total autopilot seconds:', results.totalAutopilotSeconds);
  console.log('errors:', results.errors.length, results.errors.slice(0, 10));
  console.log('checks passed:', results.checks.filter(c => c.pass).length + '/' + results.checks.length);
  await browser.close();
})().catch(e => { console.error('HARNESS FATAL', e); process.exit(1); });

async function playLevel(page, n, timeoutMs) {
  // Assumes menu is showing OR previous level-complete screen handled by caller.
  // Start level n via the test hook (same path as a level-select tap -> pressPlay).
  const t0 = Date.now();
  let bossSeen = false, bossMaxSeen = 0;
  await page.evaluate((nn) => window.__starfall.pressPlay(nn - 1), n);
  // wait for playing (loading is 3s)
  const ok = await waitState(page, 'playing', 12000, 'start L' + n);
  if (ok !== true) return { level: n, outcome: 'never-started state=' + ok, seconds: (Date.now() - t0) / 1000 };
  // poll: boss hp + state (log progress every ~60s so a stall is visible)
  let lastProgressLog = 0;
  while (Date.now() - t0 < timeoutMs) {
    const s = await page.evaluate(() => ({
      state: window.__starfall.state, bossHp: window.__starfall.bossHp,
      bossMax: window.__starfall.bossMaxHp, kills: window.__starfall.kills,
      leaked: window.__starfall.leaked, baseHp: window.__starfall.baseHp,
      level: window.__starfall.level, lives: window.__starfall.lives,
      levelTime: window.__starfall.levelTime,
    }));
    if (Date.now() - lastProgressLog > 60000) {
      lastProgressLog = Date.now();
      console.log('... L' + n + ' progress: state=' + s.state + ' kills=' + s.kills +
        ' leaked=' + s.leaked + ' baseHp=' + s.baseHp + ' levelTime=' + s.levelTime.toFixed(1) + 's bossHp=' + s.bossHp);
    }
    if (s.bossHp !== null) { bossSeen = true; bossMaxSeen = Math.max(bossMaxSeen, s.bossMax || 0); }
    if (s.state === 'complete' || s.state === 'victory') {
      const lt = await page.evaluate(() => window.__starfall.levelTime);
      return { level: n, outcome: s.state, seconds: +(lt).toFixed(1), kills: s.kills, leaked: s.leaked, baseHp: s.baseHp, livesLeft: s.lives, bossSeen, bossMaxSeen };
    }
    if (s.state === 'over') {
      return { level: n, outcome: 'over', seconds: +((Date.now() - t0) / 1000).toFixed(1), kills: s.kills, leaked: s.leaked, baseHp: s.baseHp, bossSeen, bossMaxSeen };
    }
    if (s.state !== 'playing') {
      return { level: n, outcome: 'unexpected state=' + s.state, seconds: +((Date.now() - t0) / 1000).toFixed(1), bossSeen, bossMaxSeen };
    }
    await sleep(700);
  }
  return { level: n, outcome: 'TIMEOUT', seconds: +(timeoutMs / 1000).toFixed(0), bossSeen, bossMaxSeen };
}
