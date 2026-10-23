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
const routes = [...baseline.map(x => x.route), '/changelog/'];
const releaseAnchors = ['release-0-6-0','release-0-5-1','release-0-5-0','release-0-4-0','release-0-3-1','release-0-3-0','release-0-2-0','release-0-1-0'];
// Independent readable-content witnesses, not runtime records or comment IDs.
const releaseWitnesses = [
  'Supply canonical, unescaped resource IDs.',
  'All three tools share a per-user lock.',
  'Stop invoking accounts containers combine and accounts containers move-tag-id.',
  'Add --confirm-resource with the exact resource name to destructive apply scripts.',
  'Explicit empty credential environment variables now fail instead of selecting another credential source.',
  'User guides cover installation, authentication, the three command families',
  'Native OAuth adds auth login, auth status, auth forget, and auth revoke.',
  'ga4datactl provides GA4 reports and audience exports'
];
// Independent warning/limit witnesses in the same release order, in both JS modes.
const releaseWarnings = [
  'Inspect GTM state before retrying a mutation',
  'Compatibility review is incomplete. Migration impact for existing custom profiles remains uncertain.',
  'This CLI provides no replacement.',
  'Inspect current state before retrying uncertain creates.',
  'Inspect existing audience exports before retrying an uncertain create.',
  'Site publication success was not verified.',
  'A selected invalid source fails instead of switching identity.',
  'There is no tag or GitHub Release for this interval.'
];
const themeResults = [];
async function waitForRouteContent(page, route) {
  const headings = route === '/changelog/'
    ? releaseAnchors.map(id => `h2[id="${id}"]`)
    : baseline.find(item => item.route === route).headings.map(h => `h${h.level}[id="${h.id}"]`);
  try {
    // Client navigation can update the URL before Vue replaces the old article.
    // networkidle describes network activity, not destination-content readiness.
    await page.waitForFunction(({url, headings}) => location.href === url &&
      headings.every(selector => document.querySelectorAll(`.vp-doc ${selector}`).length === 1),
    {url: origin+route, headings}, {timeout:15000});
  } catch (error) {
    console.error('route-content timeout', JSON.stringify({expectedRoute:route, url:page.url()}));
    // Only inspect the served public docs. Keep diagnostics bounded and retain the
    // original error even if the page is no longer responsive.
    if (new URL(page.url()).origin === origin) {
      try {
        const snapshot = await page.locator('html').evaluate((_, servedOrigin) => location.origin === servedOrigin ? ({
          url:location.href, title:document.title.slice(0,256),
          headings:[...document.querySelectorAll('.vp-doc h1, .vp-doc h2')].slice(0,40)
            .map(node => ({id:node.id.slice(0,128), text:node.textContent.slice(0,256)}))
        }) : null, origin, {timeout:3000, signal:AbortSignal.timeout(3000)});
        console.error('route-content failure DOM', JSON.stringify(snapshot));
        if (!snapshot || new URL(page.url()).origin !== origin) throw new Error('left served docs');
        // Reuse an allowlisted output slot; on failure this is a diagnostic,
        // NOT a successful theme/auth screenshot (identified explicitly in log).
        const path = `/evidence/${route === '/changelog/' ? 'changelog' : 'auth'}-${page.viewportSize().width}${route === '/changelog/' ? '-light' : ''}.png`;
        await page.screenshot({path, timeout:3000});
        console.error('route-content failure screenshot', path);
      } catch (diagnosticError) { console.error('route-content diagnostic failed', String(diagnosticError)); }
    }
    throw error;
  }
}
async function assertNativeReleases(page) {
  assert.equal(await page.locator('.vp-doc h2').count(), 8);
  for (const [index, id] of releaseAnchors.entries()) {
    const heading = page.locator(`h2[id="${id}"]`);
    assert.equal(await heading.count(), 1);
    assert((await heading.innerText()).includes(id.slice(8).replaceAll('-','.')));
    const content = await heading.evaluate(node => {
      let text = '';
      for (let next = node.nextElementSibling; next && next.tagName !== 'H2'; next = next.nextElementSibling) text += next.innerText + '\n';
      return text;
    });
    assert(content.includes(releaseWitnesses[index]), id);
    assert(content.includes(releaseWarnings[index]), id);
  }
  assert.equal(await page.locator('.vp-doc select, .vp-doc input, .vp-doc button').count(), 0);
}
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
      await waitForRouteContent(page, '/tools/');
      if (viewport.width<600) await page.locator('.VPLocalNav button.menu').click();
      await side.locator('a[href="/auth/"]').first().click();
      await waitForRouteContent(page, '/auth/');
      await page.goBack({waitUntil:'networkidle'});
      await waitForRouteContent(page, '/tools/');
      assert.equal(new URL(page.url()).pathname,'/tools/');
      await page.goForward({waitUntil:'networkidle'});
      await waitForRouteContent(page, '/auth/');
      assert.equal(new URL(page.url()).pathname,'/auth/');
      await page.screenshot({path:`/evidence/auth-${viewport.width}.png`,fullPage:true});
    }
    // A separate context proves that build-produced HTML works without hydration.
    const noJS = await context.browser().newContext({javaScriptEnabled:false,serviceWorkers:'block',viewport:{width:390,height:844}});
    try {
      await noJS.route('**/*', route => new URL(route.request().url()).origin===origin ? route.continue() : route.abort('blockedbyclient'));
      const plain = await noJS.newPage();
      await plain.goto(origin+'/changelog/#release-0-1-0',{waitUntil:'networkidle'});
      await assertNativeReleases(plain);
      assert.equal((await plain.reload({waitUntil:'networkidle'})).status(),200);
      assert.equal(new URL(plain.url()).hash,'#release-0-1-0');
      assert.equal(await plain.locator('main').count(),1);
      assert.equal(await plain.locator('h1').count(),1);
    } finally { await noJS.close(); }
    for (const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
      await page.setViewportSize(viewport);
      await page.goto(origin+'/auth/',{waitUntil:'networkidle'});
      if (viewport.width<600) await page.locator('.VPLocalNav button.menu').click();
      await page.locator('.VPSidebar a[href="/changelog/"]').first().click();
      await waitForRouteContent(page, '/changelog/');
      await assertNativeReleases(page);
      assert.equal(await page.locator('main').count(),1);
      assert.equal(await page.locator('h1').count(),1);
      const skip = page.locator('.VPSkipLink');
      assert.equal(await skip.count(),1);
      await skip.focus();
      assert(await skip.evaluate(node=>node===document.activeElement));
      const skipBox = await skip.boundingBox();
      assert(skipBox && skipBox.x>=0 && skipBox.y>=0);
      await page.keyboard.press('Tab');
      assert(await page.evaluate(()=>document.activeElement.tagName==='A'));
      await page.keyboard.press('Shift+Tab');
      assert(await skip.evaluate(node=>node===document.activeElement));
      const skipTarget = await skip.getAttribute('href');
      await skip.press('Enter');
      await page.waitForURL(origin+'/changelog/'+skipTarget);
      assert.equal(new URL(page.url()).hash,skipTarget);
      assert.equal(await page.locator(skipTarget).count(),1);
      if (viewport.width>=600) {
        const outline = page.locator('.VPDocAsideOutline');
        for (const id of releaseAnchors) assert.equal(await outline.locator(`a[href="#${id}"]`).count(),1);
        const link = outline.locator('a[href="#release-0-1-0"]');
        await link.focus();
        assert(await link.evaluate(node=>node===document.activeElement));
        await link.press('Enter');
        await page.waitForURL(origin+'/changelog/#release-0-1-0');
      }
      for (const id of releaseAnchors) {
        await page.goto(origin+'/changelog/#'+id,{waitUntil:'networkidle'});
        assert.equal((await page.reload({waitUntil:'networkidle'})).status(),200);
        assert.equal(new URL(page.url()).hash,'#'+id);
        assert(await page.locator('h2#'+id).isVisible());
      }
      await page.goto(origin+'/changelog/#release-0-6-0',{waitUntil:'networkidle'});
      for (const theme of ['light','dark']) {
        if (viewport.width<600) await page.locator('.VPNavBarHamburger').click();
        const nav = page.locator(viewport.width<600 ? '.VPNavScreen:visible' : '.VPNavBar:visible');
        // The desktop navbar also contains hidden responsive copies of these controls.
        const github = nav.locator(viewport.width<600 ? '.VPNavScreenSocialLinks:visible' : '.VPNavBarSocialLinks:visible')
          .getByRole('link',{name:'Marketing Toolbox on GitHub',exact:true});
        assert(await github.isVisible());
        assert.equal(await github.getAttribute('href'),'https://github.com/en-ver/marketing-toolbox');
        assert(await github.locator('.vpi-social-github').isVisible());
        await github.focus();
        assert(await github.evaluate(node=>node===document.activeElement));
        const appearance = nav.locator(viewport.width<600 ? '.VPNavScreenAppearance:visible' : '.VPNavBarAppearance:visible')
          .getByRole('switch');
        assert(await appearance.isVisible());
        if (await page.locator('html').evaluate(node=>node.classList.contains('dark')) !== (theme==='dark')) {
          await appearance.focus();
          await appearance.press('Space');
        }
        await page.waitForFunction(dark=>document.documentElement.classList.contains('dark')===dark,theme==='dark');
        if (viewport.width<600) {
          await page.locator('.VPNavBarHamburger').click();
          // Vue keeps the full-screen menu mounted during its leave transition.
          await page.locator('#VPNavScreen.VPNavScreen').waitFor({state:'detached',timeout:15000});
          await page.locator('.vp-doc').waitFor({state:'visible',timeout:15000});
          await page.locator('.vp-doc h2#release-0-6-0').scrollIntoViewIfNeeded();
          // Visible geometry alone can pass beneath an overlay. Hit-test the
          // native release heading in the viewport before measuring or capturing.
          await page.waitForFunction(() => {
            const toggles = document.querySelectorAll('.VPNavBarHamburger');
            const articles = document.querySelectorAll('.vp-doc');
            const headings = document.querySelectorAll('.vp-doc h2#release-0-6-0');
            if (location.pathname !== '/changelog/' || location.hash !== '#release-0-6-0' ||
                toggles.length !== 1 || toggles[0].getAttribute('aria-expanded') !== 'false' ||
                document.querySelectorAll('.VPNavScreen').length !== 0 ||
                articles.length !== 1 || headings.length !== 1) return false;
            const heading = headings[0], box = heading.getBoundingClientRect();
            const x = box.x+box.width/2, y = box.y+box.height/2;
            return box.width>0 && box.height>0 && x>0 && x<innerWidth && y>0 && y<innerHeight &&
              heading.contains(document.elementFromPoint(x,y));
          }, null, {timeout:15000});
        }
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
        assert(await page.locator('.vp-doc').evaluate(node=>[...node.querySelectorAll('li,p')].every(n=>n.getBoundingClientRect().right<=innerWidth+2)));
        themeResults.push({width:viewport.width,theme,colors:await page.locator('.vp-doc').evaluate(node=>({text:getComputedStyle(node).color,background:getComputedStyle(document.body).backgroundColor}))});
        await page.screenshot({path:`/evidence/changelog-${viewport.width}-${theme}.png`});
      }
    }
    assert.deepEqual(errors,[]);
    fs.writeFileSync('/evidence/browser-result.json',JSON.stringify({routes,fragments,viewports:[[1440,1000],[390,844]],browserVersion:context.browser().version(),nodeVersion:process.versions.node,sandbox:true,releaseAnchors,themeResults,noJavaScript:true,errors},null,2));
  } finally { await context.close(); }
})().catch(e => {console.error(e);process.exitCode=1;});
