// Capture real website states for the narrated walkthrough.
// Requires Playwright and its Chromium browser; run with a local server on port 8765.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const out = path.resolve('.sites-runtime/video');
fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:840},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror', e=>errors.push(e.message));
  async function open(file){
    await page.goto('http://localhost:8765/'+file,{waitUntil:'networkidle'});
    await page.addStyleTag({content:'html {scroll-behavior:auto!important}'});
    await page.waitForTimeout(700);
  }
  async function shot(n, selector){
    if(selector) await page.locator(selector).first().evaluate(e=>window.scrollTo(0,e.getBoundingClientRect().top+window.scrollY-90));
    await page.waitForTimeout(500);
    await page.screenshot({path:path.join(out,`${n}.png`)});
    console.log(`Captured scene ${n}: ${page.url()}`);
  }
  await open('index.html');
  await page.waitForFunction(()=>document.querySelector('#headline-value').textContent==='Central Square');
  await page.locator('#district-chart canvas, #district-chart svg').first().waitFor();
  await shot(1);
  await shot(2,'.chart-grid');
  await open('methodology.html'); await shot(3);
  await shot(4,'.definition-grid');
  await open('explore.html');
  await page.waitForFunction(()=>document.querySelector('#result-count').textContent.startsWith('96 storefront'));
  await shot(5,'.workspace');
  await page.locator('#district-options input[value="East Cambridge"]').uncheck();
  await shot(6,'.workspace');
  await page.locator('[data-view="districts"]').click(); await shot(7,'.workspace');
  await page.locator('#min-months').fill('36');
  await page.locator('[data-view="profile"]').click(); await shot(8,'.workspace');
  await open('data.html'); await shot(9);
  await open('index.html'); await shot(10,'#findings-list');
  await shot(11,'#recommendations-list');
  await open('reflection.html'); await shot(12,'h2:has-text("Uncertainty")');
  await browser.close();
  if(errors.length) throw new Error(errors.join('\n'));
})();
