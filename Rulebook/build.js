// Renders rulebook.html to GloryToRome-PocketRules.pdf (US Letter landscape, 2 sheets).
//
//   node build.js                       folded size 3.4in (drops into a 3.5in space)
//   node build.js 3.5                   any other folded size in inches, up to 3.6
//   node build.js --back-shift=1.5,0    nudge the inside sheet right 1.5mm / down 0mm, to cancel
//                                       a printer's front-to-back offset (negative = left / up)
//
// Needs Playwright with Chromium (npm i playwright && npx playwright install chromium).
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const args = process.argv.slice(2);
  const panel = parseFloat(args.find(a => !a.startsWith('--')) || '3.4');
  const [shiftX, shiftY] = ((args.find(a => a.startsWith('--back-shift=')) || '=0,0').split('=')[1] + ',0').split(',').map(Number);
  if (![shiftX, shiftY].every(v => Math.abs(v) <= 5)) throw new Error('--back-shift takes x,y in millimetres, each within 5mm.');
  if (!(panel > 2 && panel <= 3.6)) throw new Error('Folded size must be between 2 and 3.6 inches to fit three panels on Letter.');

  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.addInitScript(p => {
    document.addEventListener('DOMContentLoaded', () => document.documentElement.style.setProperty('--panel', p + 'in'), { once: true });
  }, panel);
  await page.goto('file://' + path.join(__dirname, 'rulebook.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(([x, y]) => { document.getElementById('inside-strip').style.transform = `translate(${x}mm, ${y}mm)`; }, [shiftX, shiftY]);

  // Fail loudly if any panel's text no longer fits.
  const overflowing = await page.$$eval('.panel', ps => ps
    .map((p, i) => ({ i, over: p.scrollHeight - p.clientHeight, folio: p.querySelector('.folio'), last: [...p.children].filter(c => !c.classList.contains('folio')).pop() }))
    .filter(o => o.over > 0 || (o.folio && o.last && o.last.getBoundingClientRect().bottom > o.folio.getBoundingClientRect().top && o.last.getBoundingClientRect().right > o.folio.getBoundingClientRect().left))
    .map(o => o.i));
  if (overflowing.length) console.warn('WARNING: text overflows or hits the page number in panel index(es): ' + overflowing.join(', '));

  const out = path.join(__dirname, 'GloryToRome-PocketRules.pdf');
  await page.pdf({ path: out, width: '11in', height: '8.5in', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  await browser.close();
  console.log('Wrote ' + out + ' (folded size ' + panel + 'in, inside sheet shifted ' + shiftX + 'mm right, ' + shiftY + 'mm down)');
})();
