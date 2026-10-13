import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve, extname } from 'node:path';
import assert from 'node:assert/strict';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = resolve(fileURLToPath(new URL('../', import.meta.url)));
const types = {'.html':'text/html','.js':'text/javascript','.json':'application/json','.css':'text/css','.svg':'image/svg+xml','.jpg':'image/jpeg'};
const server = createServer(async (req,res) => {
  try {
    let path = resolve(root, '.' + new URL(req.url, 'http://test').pathname);
    if (!path.startsWith(root)) throw new Error('Invalid path');
    if ((await stat(path)).isDirectory()) path += '/index.html';
    res.setHeader('content-type', types[extname(path)] || 'application/octet-stream');
    res.end(await readFile(path));
  } catch { res.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
const url = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({headless:true});
try {
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.route('https://**/*',route=>route.abort());
  await page.goto(url);
  await page.waitForSelector('.ayah-card');
  await page.waitForFunction(()=>!!loadedData[3]);
  // Delay a colouring request, then change surah. Its stale result must not
  // replace the latest selected surah after the network finally answers.
  let release;
  const delayed = new Promise(resolve=>{release=resolve});
  let requested=false;
  await page.route('**/data/tajweed-1.json',async route=>{
    requested=true;await delayed;await route.continue();
  });
  await page.locator('#settingsToggle').click();
  await page.locator('#tajweedToggle').check();
  await page.waitForFunction(()=>settings.tajweed);
  while(!requested) await new Promise(resolve=>setTimeout(resolve,10));
  await page.locator('#settingsClose').click();
  await page.locator('#surahSelect').selectOption('2');
  await page.waitForFunction(()=>document.querySelector('.verse-section-title')?.textContent.includes('Baqarah'));
  release();
  await page.waitForFunction(()=>!!tajweedCache[1]);
  assert.match(await page.locator('.verse-section-title').first().innerText(),/Baqarah/);
  assert.equal(await page.locator('#surahSelect').inputValue(),'2');
  // A failed request must be retryable and distinct from a real empty scaffold.
  let fail=true;
  await page.route('**/data/surah-4.json',route=>fail?route.fulfill({status:503,body:'Unavailable'}):route.continue());
  await page.locator('#surahSelect').selectOption('4');
  await page.getByRole('button',{name:'Retry',exact:true}).waitFor();
  assert.equal(await page.locator('.scaffold-notice').count(),0);
  fail=false;await page.getByRole('button',{name:'Retry',exact:true}).click();
  await page.waitForSelector('.scaffold-notice');
  assert.match(await page.locator('.verse-section-title').innerText(),/Nisa/);
  // Arrow keys inside the settings drawer must not advance Quran pages.
  await page.locator('#settingsToggle').click();
  await page.locator('#themeSelect').focus();
  const pageBefore=await page.locator('#pageSelect').inputValue();
  await page.keyboard.press('ArrowDown');
  assert.equal(await page.locator('#pageSelect').inputValue(),pageBefore);
  assert.deepEqual(errors,[]);
  console.log('Latest selection wins delayed tajweed; network failure/retry and settings keyboard pass.');
} finally { await browser.close(); await new Promise(resolve=>server.close(resolve)); }
