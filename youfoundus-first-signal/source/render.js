// usage: node render.js <outDir> <variant> <frames: "a-b" or "t:1.2,3.4"> [port]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const [outDir, variant = 'cta', spec = '0-359', port = '8123'] = process.argv.slice(2);
const root = __dirname;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.ttf': 'font/ttf' };
const srv = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); }); });
(async () => {
  await new Promise(res => srv.listen(+port, res));
  fs.mkdirSync(outDir, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  p.on('console', m => console.log('[page]', m.text()));
  await p.goto(`http://localhost:${port}/index.html?variant=${variant}`);
  await p.waitForFunction(() => window.READY || window.BOOT_ERROR, null, { timeout: 120000 });
  const err = await p.evaluate(() => window.BOOT_ERROR); if (err) { console.error(err); process.exit(1); }
  console.log(JSON.stringify(await p.evaluate(() => ({ n: FILM.nParts, st: Object.fromEntries(Object.entries(FILM.ST).map(([k, v]) => [k, v.size])) }))));
  let list = [];
  if (spec.startsWith('t:')) list = spec.slice(2).split(',').map(s => ({ t: +s, name: 't' + s }));
  else { const [a, z] = spec.split('-').map(Number); for (let i = a; i <= z; i++) list.push({ t: i / 30, name: String(i).padStart(4, '0') }); }
  const cv = await p.$('#gl');
  for (const f of list) {
    const t0 = Date.now();
    await p.evaluate(t => renderFrame(t), f.t);
    await cv.screenshot({ path: path.join(outDir, f.name + '.png') });
    console.log(f.name, f.t.toFixed(3), (Date.now() - t0) + 'ms');
  }
  await b.close(); srv.close();
})();
