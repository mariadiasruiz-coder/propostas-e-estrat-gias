const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const mode = process.argv[2];
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('console:', m.text()));
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('file://' + path.resolve('web/index.html'));
  await page.evaluate(() => window.ready);
  const el = await page.$('#cv');
  for (const w of [1, 10, 20]) await page.evaluate(t => window.draw(t), w);
  await page.waitForTimeout(800); await el.screenshot();
  if (mode === 'still') {
    for (const t of process.argv.slice(3).map(Number)) {
      await page.evaluate(t => window.draw(t), t);
      await el.screenshot({ path: `prev/f_${t.toFixed(2)}.png` });
    }
  } else {
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'png', '-i', '-', '-c:v', 'ffv1', '-pix_fmt', 'yuv444p', `seg_${process.argv[3]}.mkv`], { stdio: ['pipe', 'inherit', 'inherit'] });
    const a = +process.argv[4], b = +process.argv[5];
    for (let i = a; i < b; i++) {
      await page.evaluate(t => window.draw(t), i / 30);
      const buf = await el.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 60 === 0) console.log('frame', i);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
