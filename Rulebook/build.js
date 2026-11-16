// Renders rulebook.html to GloryToRome-PocketRules.pdf (US Letter landscape, 2 sheets).
//
//   node build.js            folded size 3.4in (drops into a 3.5in space)
//   node build.js 3.5        any other folded size in inches, up to 3.6
//
// Needs Playwright with Chromium (npm i playwright && npx playwright install chromium).
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const panel = parseFloat(process.argv[2] || '3.4');
  if (!(panel > 2 && panel <= 3.6)) throw new Error('Folded size must be between 2 and 3.6 inches to fit three panels on Letter.');

  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.addInitScript(p => {
    document.addEventListener('DOMContentLoaded', () => document.documentElement.style.setProperty('--panel', p + 'in'), { once: true });
  }, panel);
  await page.goto('file://' + path.join(__dirname, 'rulebook.html'));
  await page.evaluate(() => document.fonts.ready);

  // Fail loudly if any panel's text no longer fits.
  const overflowing = await page.$$eval('.panel', ps => ps
    .map((p, i) => ({ i, over: p.scrollHeight - p.clientHeight, folio: p.querySelector('.folio'), last: [...p.children].filter(c => !c.classList.contains('folio')).pop() }))
    .filter(o => o.over > 0 || (o.folio && o.last && o.last.getBoundingClientRect().bottom > o.folio.getBoundingClientRect().top && o.last.getBoundingClientRect().right > o.folio.getBoundingClientRect().left))
    .map(o => o.i));
  if (overflowing.length) console.warn('WARNING: text overflows or hits the page number in panel index(es): ' + overflowing.join(', '));

  const out = path.join(__dirname, 'GloryToRome-PocketRules.pdf');
  await page.pdf({ path: out, width: '11in', height: '8.5in', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  await browser.close();
  console.log('Wrote ' + out + ' (folded size ' + panel + 'in)');
})();
