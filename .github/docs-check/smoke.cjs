// Temporary hosted tool only. No npx, package installation, or remote browser endpoint.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const { setTimeout: delay } = require('node:timers/promises');
const playwright = require('/tools/node_modules/playwright');
assert.equal(process.versions.node, '24.22.1');
assert.equal(process.getuid(), 10001);
const browserName = 'chromium';
const origin = 'http://127.0.0.1:8765';
const baseline = JSON.parse(fs.readFileSync('/tools/baseline.json', 'utf8'));
assert.equal(baseline.length, 8);
const routes = baseline.map(x => x.route);
const fragments = ['/auth/#credential-precedence','/tools/#output-and-requests','/tools/ga4-admin/#destructive-admin-mutations'];
(async () => {
  const context = await playwright[browserName].launchPersistentContext('/tmp/isolated-profile', {
    headless: true, chromiumSandbox: true, serviceWorkers: 'block',
    viewport: { width: 1440, height: 1000 }
  });
  try {
    context.setDefaultTimeout(15000);
    context.setDefaultNavigationTimeout(30000);
    const errors = [];
    await context.route('**/*', route => {
      if (new URL(route.request().url()).origin !== origin) {
        errors.push('external request '+route.request().url());
        return route.abort('blockedbyclient');
      }
      return route.continue();
    });
    await context.routeWebSocket('**/*', ws => { errors.push('unexpected websocket'); ws.close(); });
    context.on('page', page => {
      page.on('pageerror', e => errors.push(String(e)));
      page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
      page.on('response', r => { if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`); });
      page.on('requestfailed', q => errors.push(`${q.url()} ${q.failure()?.errorText}`));
    });
    const page = await context.newPage();
    await page.goto('about:blank');
    await page.evaluate(() => navigator.userAgent);
    console.log('sandbox-probe-ready');
    let approved = false;
    for (let i=0;i<300;i++) {
      if (fs.existsSync('/evidence/sandbox-ok')) { approved=true; break; }
      await delay(100);
    }
    assert(approved, 'host sandbox/network/private-file probes did not pass');
    assert.match(context.browser().version(), /^156\.0\.8078\.4$/);
    for (const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
      await page.setViewportSize(viewport);
      for (const old of baseline) {
        const response = await page.goto(origin+old.route, {waitUntil:'networkidle'});
        assert.equal(response.status(), 200);
        assert.equal(new URL(page.url()).pathname, old.route);
        assert.equal((await page.reload({waitUntil:'networkidle'})).status(),200);
        for (const h of old.headings) assert.equal(await page.locator(`[id="${h.id}"]`).count(),1);
        for (const element of await page.locator('.vp-doc table, .vp-doc pre').all()) {
          assert(await element.isVisible());
          const b = await element.boundingBox();
          assert(b && b.width>0 && b.height>0);
        }
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth+2));
      }
      for (const target of fragments) {
        await page.goto(origin+target,{waitUntil:'networkidle'});
        assert.equal((await page.reload({waitUntil:'networkidle'})).status(),200);
        assert.equal(new URL(page.url()).hash, new URL(origin+target).hash);
        assert(await page.locator(`[id="${target.split('#')[1]}"]`).isVisible());
      }
      await page.goto(origin+'/auth/', {waitUntil:'networkidle'});
      if (viewport.width<600) {
        const toggle = page.locator('.VPLocalNav button.menu');
        await toggle.click();
      }
      const side = page.locator('.VPSidebar');
      await side.locator('a[href="/tools/"]').first().click();
      await page.waitForURL(origin+'/tools/');
      await page.waitForLoadState('networkidle');
      if (viewport.width<600) await page.locator('.VPLocalNav button.menu').click();
      await side.locator('a[href="/auth/"]').first().click();
      await page.waitForURL(origin+'/auth/');
      await page.goBack({waitUntil:'networkidle'});
      assert.equal(new URL(page.url()).pathname,'/tools/');
      await page.goForward({waitUntil:'networkidle'});
      assert.equal(new URL(page.url()).pathname,'/auth/');
      await page.screenshot({path:`/evidence/auth-${viewport.width}.png`,fullPage:true});
    }
    assert.deepEqual(errors,[]);
    fs.writeFileSync('/evidence/browser-result.json',JSON.stringify({routes,fragments,viewports:[[1440,1000],[390,844]],browserVersion:context.browser().version(),nodeVersion:process.versions.node,sandbox:true,errors},null,2));
  } finally { await context.close(); }
})().catch(e => {console.error(e);process.exitCode=1;});
