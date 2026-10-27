// WHAT BRANDON THINKS — 24s Reels film. Deterministic: draw(t) renders the frame at time t (s).
const W = 1080, H = 1920, CX = 540;
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');

const C = {
  n0: '#04070F', n1: '#0A1228', n2: '#13224A', n3: '#1C3168',
  blue: '#4F95F8', blueL: '#8BB9FF', cyan: '#73E2FF', cream: '#F3EAD9',
  gold: '#D9AE55', goldL: '#F1D08A', ink: '#0B1430', white: '#FFFFFF',
};

// ---------- math ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, x) => a + (b - a) * x;
const prog = (t, a, d) => clamp((t - a) / d);
const E = {
  out3: x => 1 - Math.pow(1 - x, 3),
  in3: x => x * x * x,
  io3: x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2,
  outExpo: x => x >= 1 ? 1 : 1 - Math.pow(2, -10 * x),
  inExpo: x => x <= 0 ? 0 : Math.pow(2, 10 * x - 10),
  outBack: (x, s = 1.70158) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2),
  outElastic: x => x === 0 ? 0 : x === 1 ? 1 : Math.pow(2, -9 * x) * Math.sin((x * 10 - .75) * (2 * Math.PI) / 3.2) + 1,
};
function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// ---------- assets ----------
const IMG = {};
function load(name, src) { return new Promise(r => { const i = new Image(); i.onload = () => { IMG[name] = i; r(); }; i.src = src; }); }

// ---------- primitives ----------
function rr(c, x, y, w, h, r) { c.beginPath(); c.roundRect(x, y, w, h, r); }
function glass(c, x, y, w, h, r, o = {}) {
  c.save();
  if (o.shadow !== false) { c.shadowColor = o.shadowColor || 'rgba(0,0,0,0.45)'; c.shadowBlur = o.shadowBlur ?? 50; c.shadowOffsetY = o.shadowY ?? 20; }
  rr(c, x, y, w, h, r);
  const g = c.createLinearGradient(x, y, x + w * .4, y + h);
  g.addColorStop(0, o.top || 'rgba(255,255,255,0.16)'); g.addColorStop(1, o.bot || 'rgba(255,255,255,0.05)');
  c.fillStyle = g; c.fill();
  c.shadowColor = 'transparent';
  const s = c.createLinearGradient(x, y, x + w, y + h);
  s.addColorStop(0, o.edge || 'rgba(255,255,255,0.55)'); s.addColorStop(.5, 'rgba(255,255,255,0.08)'); s.addColorStop(1, o.edge2 || 'rgba(140,190,255,0.35)');
  c.lineWidth = o.lw || 2; c.strokeStyle = s; c.stroke();
  c.restore();
}
function glow(c, x, y, r, color, a = 1) {
  c.save(); c.globalAlpha = a; c.globalCompositeOperation = 'lighter';
  const g = c.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, color); g.addColorStop(1, 'rgba(0,0,0,0)');
  c.fillStyle = g; c.fillRect(x - r, y - r, 2 * r, 2 * r); c.restore();
}
function flash(c, a, color = '#fff') { if (a <= 0) return; c.save(); c.globalAlpha = clamp(a); c.fillStyle = color; c.fillRect(0, 0, W, H); c.restore(); }
function bars(c, x, y, w, n, col, h = 14, gap = 12, seed = 1) { // blurred "text" placeholder lines
  const R = rng(seed); c.save(); c.fillStyle = col;
  for (let i = 0; i < n; i++) { const ww = w * (i === n - 1 ? .45 + R() * .2 : .75 + R() * .25); rr(c, x, y + i * (h + gap), ww, h, h / 2); c.fill(); }
  c.restore();
}
function font(size, w = 800, fam = 'Sora') { return `${w} ${size}px ${fam}`; }
function txt(c, s, x, y, size, o = {}) {
  c.save(); c.font = font(size, o.w || 700, o.fam || 'SG'); c.textAlign = o.align || 'center'; c.textBaseline = 'alphabetic';
  c.letterSpacing = (o.ls || 0) + 'px'; c.globalAlpha *= (o.a ?? 1); c.fillStyle = o.color || '#fff';
  if (o.glow) { c.shadowColor = o.glow; c.shadowBlur = o.gb || 24; }
  c.fillText(s, x, y); c.restore();
}

// ---------- kinetic headline ----------
// lines: '\n'-separated; hl: {WORD: style}. style: 'grad' | 'gold' | 'cream' | color string
function headline(c, t, o) {
  const size0 = o.size || 120, fam = o.fam || 'Sora', wt = o.w || 800, maxW = o.maxW || 940;
  const lines = o.text.split('\n');
  c.save(); c.textBaseline = 'alphabetic';
  let wi = 0;
  lines.forEach((line, li) => {
    let size = size0; c.font = font(size, wt, fam); c.letterSpacing = (o.ls ?? -2) + 'px';
    let lw = c.measureText(line).width;
    if (lw > maxW) { size = size0 * maxW / lw; c.font = font(size, wt, fam); lw = c.measureText(line).width; }
    const y = o.y + li * (o.lh || size0 * 1.08);
    const words = line.split(' ');
    const sp = c.measureText(' ').width;
    let x = (o.x ?? CX) - lw / 2;
    words.forEach(word => {
      const ww = c.measureText(word).width;
      const st = o.start + wi * (o.stagger ?? .09);
      const p = prog(t, st, o.dur || .45);
      wi++;
      if (p <= 0) { x += ww + sp; return; }
      let ex = 0; if (o.exit != null) ex = E.in3(prog(t, o.exit + (wi - 1) * .03, o.exitDur || .3));
      const style = (o.hl && o.hl[word.replace(/[?.,!…]/g, '')]) || null;
      c.save();
      const cxw = x + ww / 2;
      let dy = 0, sc = 1, a = 1, blur = 0;
      const mode = o.style || 'rise';
      if (mode === 'rise') { const e = E.outBack(p, 1.4); dy = (1 - e) * size * .95; a = clamp(p * 2.2); blur = (1 - E.out3(p)) * 14; }
      else if (mode === 'pop') { const e = E.outBack(p, 2.2); sc = lerp(1.9, 1, e); a = clamp(p * 3); blur = (1 - E.out3(p)) * 18; }
      else if (mode === 'track') { const e = E.outExpo(p); c.letterSpacing = lerp(size * .5, o.ls ?? -2, e) + 'px'; a = clamp(p * 2); blur = (1 - e) * 16; }
      dy -= ex * size * .7; a *= 1 - ex; blur += ex * 16;
      if (a <= 0) { c.restore(); x += ww + sp; return; }
      if (mode === 'rise') { c.beginPath(); c.rect(x - 40, y - size * 1.05 - ex * size, ww + 80, size * 1.35); c.clip(); }
      c.translate(cxw, y - size * .35 + dy); c.scale(sc, sc); c.translate(-cxw, -(y - size * .35));
      c.globalAlpha = a;
      if (blur > .5) c.filter = `blur(${blur.toFixed(1)}px)`;
      let fill = o.color || '#fff';
      if (style === 'grad') {
        const g = c.createLinearGradient(x, y - size, x + ww, y); g.addColorStop(0, C.cyan); g.addColorStop(1, C.blue); fill = g;
        c.shadowColor = 'rgba(115,226,255,0.9)'; c.shadowBlur = 40 + 20 * Math.sin(t * 9);
      } else if (style === 'gold') {
        const g = c.createLinearGradient(x, y - size, x, y); g.addColorStop(0, C.goldL); g.addColorStop(1, C.gold); fill = g;
        c.shadowColor = 'rgba(241,208,138,0.55)'; c.shadowBlur = 30;
      } else if (style) fill = style;
      if (o.shadow !== false && !style) { c.shadowColor = o.shadowColor || 'rgba(0,0,0,0.45)'; c.shadowBlur = 30; c.shadowOffsetY = 8; }
      c.fillStyle = fill; c.textAlign = 'left';
      c.fillText(word, x, y);
      c.restore();
      x += ww + sp;
    });
  });
  c.restore();
}

// ---------- mascot ----------
// head.png anchor: bottom-centre of chin. Lens centres in head.png coords.
const HEAD = { ax: 532, ay: 1001, lenses: [[406, 597], [670, 597]], lr: [112, 92] };
function headPoint(x, y, s, r, px, py) { const dx = px - HEAD.ax, dy = py - HEAD.ay; return [x + s * (dx * Math.cos(r) - dy * Math.sin(r)), y + s * (dx * Math.sin(r) + dy * Math.cos(r))]; }
function drawHead(c, x, y, s, r = 0, o = {}) {
  const im = IMG.head; if (!im) return;
  c.save(); c.globalAlpha *= (o.a ?? 1);
  // contact shadow + rim glow
  if (o.shadow !== false) { c.save(); c.globalAlpha *= .5; c.fillStyle = 'rgba(0,0,0,0.6)'; c.filter = 'blur(30px)'; c.beginPath(); c.ellipse(x, y + 10 * s, 300 * s, 60 * s, 0, 0, 7); c.fill(); c.restore(); }
  c.translate(x, y); c.rotate(r);
  const sx = s * (o.sx || 1), sy = s * (o.sy || 1);
  c.scale(sx, sy);
  if (o.rim) { c.save(); c.shadowColor = o.rim; c.shadowBlur = 60; c.drawImage(im, -HEAD.ax, -HEAD.ay); c.restore(); }
  c.drawImage(im, -HEAD.ax, -HEAD.ay);
  // lens glint sweep
  if (o.glint != null && o.glint > 0 && o.glint < 1) {
    c.save(); c.beginPath();
    for (const [lx, ly] of HEAD.lenses) { c.moveTo(lx - HEAD.ax + HEAD.lr[0], ly - HEAD.ay); c.ellipse(lx - HEAD.ax, ly - HEAD.ay, HEAD.lr[0], HEAD.lr[1], 0, 0, 7); }
    c.clip();
    const gx = lerp(-420, 420, o.glint);
    c.translate(gx, -404); c.rotate(-.6);
    const g = c.createLinearGradient(-60, 0, 60, 0);
    g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(.5, 'rgba(255,255,255,0.85)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    c.globalCompositeOperation = 'lighter'; c.fillStyle = g; c.fillRect(-60, -400, 120, 800);
    c.restore();
  }
  c.restore();
}
// Character (desk cut-out): crop of char.png, anchor bottom-centre
const CHAR = { sx: 0, sy: 77, sw: 1022, sh: 844 };
function drawChar(c, x, y, s, r = 0, o = {}) {
  const im = IMG.char; if (!im) return;
  c.save(); c.globalAlpha *= (o.a ?? 1); c.translate(x, y); c.rotate(r); c.scale(s * (o.sx || 1), s * (o.sy || 1));
  if (o.rim) { c.shadowColor = o.rim; c.shadowBlur = 70; }
  c.drawImage(im, CHAR.sx, CHAR.sy, CHAR.sw, CHAR.sh, -CHAR.sw / 2, -CHAR.sh, CHAR.sw, CHAR.sh);
  c.restore();
}

// ---------- shared environment ----------
const DUST = (() => { const R = rng(7); return Array.from({ length: 140 }, () => ({ x: R() * W, y: R() * H, z: .3 + R() * .7, r: .8 + R() * 2.6, ph: R() * 6.28 })); })();
function dust(c, t, color = '180,215,255', a = 1, vx = 6, vy = -14) {
  c.save(); c.globalCompositeOperation = 'lighter';
  for (const d of DUST) {
    const x = ((d.x + t * vx * d.z * 6) % W + W) % W, y = ((d.y + t * vy * d.z * 6) % H + H) % H;
    const al = a * d.z * (.35 + .35 * Math.sin(t * 2 + d.ph));
    c.fillStyle = `rgba(${color},${al.toFixed(3)})`; c.beginPath(); c.arc(x, y, d.r * d.z * 1.4, 0, 7); c.fill();
  }
  c.restore();
}
function bgRadial(c, cx, cy, inner, outer, r = 1400) {
  const g = c.createRadialGradient(cx, cy, 0, cx, cy, r); g.addColorStop(0, inner); g.addColorStop(1, outer);
  c.fillStyle = g; c.fillRect(0, 0, W, H);
}
function camera(c, z, fx, fy, k = 0) { c.translate(lerp(fx, CX, k), lerp(fy, 960, k)); c.scale(z, z); c.translate(-fx, -fy); }

// Phone mock (conceptual)
function phone(c, cx, cy, w, h, rotY, screen) {
  const k = Math.cos(rotY), side = Math.sin(rotY);
  c.save(); c.translate(cx, cy); c.transform(k, side * .12, 0, 1, 0, 0);
  // thickness
  c.save(); c.translate(-side * 26, 0); rr(c, -w / 2, -h / 2, w, h, 64); c.fillStyle = '#05070d'; c.fill(); c.restore();
  // shadow
  c.save(); c.shadowColor = 'rgba(0,0,0,0.6)'; c.shadowBlur = 80; c.shadowOffsetY = 40; rr(c, -w / 2, -h / 2, w, h, 64); c.fillStyle = '#121826'; c.fill(); c.restore();
  // metal bezel
  rr(c, -w / 2, -h / 2, w, h, 64);
  const g = c.createLinearGradient(-w / 2, -h / 2, w / 2, h / 2);
  g.addColorStop(0, '#9aa7c0'); g.addColorStop(.3, '#2b3348'); g.addColorStop(.7, '#151b2b'); g.addColorStop(1, '#8090b0');
  c.fillStyle = g; c.fill();
  rr(c, -w / 2 + 10, -h / 2 + 10, w - 20, h - 20, 56); c.fillStyle = '#04060c'; c.fill();
  // screen
  c.save(); rr(c, -w / 2 + 18, -h / 2 + 18, w - 36, h - 36, 48); c.clip();
  screen(c, -w / 2 + 18, -h / 2 + 18, w - 36, h - 36);
  // reflection
  const rg = c.createLinearGradient(-w / 2, -h / 2, w / 2, h / 2);
  rg.addColorStop(0, 'rgba(255,255,255,0.18)'); rg.addColorStop(.35, 'rgba(255,255,255,0.0)'); rg.addColorStop(1, 'rgba(255,255,255,0.05)');
  c.fillStyle = rg; c.fillRect(-w / 2, -h / 2, w, h);
  c.restore();
  // island
  rr(c, -50, -h / 2 + 30, 100, 28, 14); c.fillStyle = '#000'; c.fill();
  c.restore();
}
function chatScreen(c, x, y, w, h, t, o = {}) {
  const g = c.createLinearGradient(x, y, x, y + h); g.addColorStop(0, o.bg0 || '#0f1a33'); g.addColorStop(1, o.bg1 || '#0a1122');
  c.fillStyle = g; c.fillRect(x, y, w, h);
  c.fillStyle = 'rgba(255,255,255,0.06)'; c.fillRect(x, y, w, 120);
  c.fillStyle = o.avatar || '#8BB9FF'; c.beginPath(); c.arc(x + 60, y + 78, 24, 0, 7); c.fill();
  if (o.title) txt(c, o.title, x + 100, y + 88, 24, { align: 'left', w: 600, color: '#e8eefc' });
  else bars(c, x + 100, y + 66, 140, 1, 'rgba(255,255,255,0.5)', 14);
  const R = rng(o.seed || 3); let yy = y + 160 + ((o.scroll || 0) % 1) * 0;
  for (let i = 0; i < 9; i++) {
    const me = R() > .5, bw = w * (.42 + R() * .3), bh = 54 + Math.floor(R() * 2) * 34;
    const bx = me ? x + w - bw - 22 : x + 22;
    rr(c, bx, yy, bw, bh, 22); c.fillStyle = me ? (o.me || 'rgba(79,149,248,0.85)') : 'rgba(255,255,255,0.12)'; c.fill();
    bars(c, bx + 18, yy + 18, bw - 40, bh > 60 ? 2 : 1, me ? 'rgba(255,255,255,0.55)' : 'rgba(255,255,255,0.35)', 10, 12, i + 9);
    yy += bh + 16;
  }
}
function docIcon(c, x, y, w, h, o = {}) {
  c.save(); c.translate(x, y);
  const f = w * .28;
  c.beginPath(); c.moveTo(-w / 2, -h / 2 + 14); c.arcTo(-w / 2, -h / 2, -w / 2 + 14, -h / 2, 14); c.lineTo(w / 2 - f, -h / 2); c.lineTo(w / 2, -h / 2 + f); c.lineTo(w / 2, h / 2 - 14); c.arcTo(w / 2, h / 2, w / 2 - 14, h / 2, 14); c.lineTo(-w / 2 + 14, h / 2); c.arcTo(-w / 2, h / 2, -w / 2, h / 2 - 14, 14); c.closePath();
  c.shadowColor = o.glow || 'rgba(115,226,255,0.9)'; c.shadowBlur = o.gb ?? 50;
  const g = c.createLinearGradient(0, -h / 2, 0, h / 2); g.addColorStop(0, '#ffffff'); g.addColorStop(1, '#d6e6ff');
  c.fillStyle = g; c.fill(); c.shadowBlur = 0;
  c.beginPath(); c.moveTo(w / 2 - f, -h / 2); c.lineTo(w / 2 - f, -h / 2 + f); c.lineTo(w / 2, -h / 2 + f); c.fillStyle = '#a9c6f5'; c.fill();
  for (let i = 0; i < 2; i++) { rr(c, -w / 2 + 18, -h / 2 + 30 + i * 34, w * (i ? .5 : .62), 24, 12); c.fillStyle = i ? 'rgba(11,20,48,0.18)' : 'rgba(79,149,248,0.9)'; c.fill(); }
  bars(c, -w / 2 + 18, -h / 2 + 108, w - 40, 3, 'rgba(11,20,48,0.22)', 9, 11, 4);
  if (o.label) txt(c, o.label, 0, h / 2 + 44, 26, { w: 600, color: '#fff', a: o.la ?? 1 });
  c.restore();
}
function lockIcon(c, x, y, s, shackle /*0 open..1 closed*/, o = {}) {
  c.save(); c.translate(x, y); c.scale(s, s);
  const lift = (1 - shackle) * 34;
  c.lineWidth = 16; c.lineCap = 'round'; c.strokeStyle = o.sh || '#e9eef8';
  c.beginPath(); c.moveTo(-34, -20); c.lineTo(-34, -52 - lift); c.arc(0, -52 - lift, 34, Math.PI, 0); c.lineTo(34, -20 - lift * (shackle < 1 ? 1 : 0)); c.stroke();
  rr(c, -58, -26, 116, 96, 22);
  const g = c.createLinearGradient(0, -26, 0, 70); g.addColorStop(0, C.goldL); g.addColorStop(1, C.gold);
  c.shadowColor = 'rgba(241,208,138,0.7)'; c.shadowBlur = 40; c.fillStyle = g; c.fill(); c.shadowBlur = 0;
  c.fillStyle = C.ink; c.beginPath(); c.arc(0, 14, 12, 0, 7); c.fill(); rr(c, -5, 16, 10, 28, 5); c.fill();
  c.restore();
}
function shieldPath(c, x, y, r) { c.beginPath(); for (let i = 0; i < 6; i++) { const a = Math.PI / 6 + i * Math.PI / 3; c.lineTo(x + r * Math.cos(a), y + r * Math.sin(a)); } c.closePath(); }
function bell(c, x, y, s, muted, a = 1) {
  c.save(); c.globalAlpha *= a; c.translate(x, y); c.scale(s, s);
  c.beginPath(); c.arc(0, 0, 40, 0, 7); c.fillStyle = 'rgba(10,18,40,0.9)'; c.fill(); c.lineWidth = 3; c.strokeStyle = 'rgba(255,255,255,0.35)'; c.stroke();
  c.fillStyle = '#dfe8fa';
  c.beginPath(); c.moveTo(-17, 10); c.quadraticCurveTo(-17, -20, 0, -20); c.quadraticCurveTo(17, -20, 17, 10); c.lineTo(21, 14); c.lineTo(-21, 14); c.closePath(); c.fill();
  c.beginPath(); c.arc(0, 19, 6, 0, Math.PI); c.fill();
  if (muted) { c.strokeStyle = '#ff6b7a'; c.lineWidth = 6; c.lineCap = 'round'; c.beginPath(); c.moveTo(-24, -24); c.lineTo(24, 24); c.stroke(); }
  c.restore();
}
function trash(c, x, y, s, col = '#ff8a95') {
  c.save(); c.translate(x, y); c.scale(s, s); c.strokeStyle = col; c.lineWidth = 4; c.lineJoin = 'round'; c.lineCap = 'round';
  c.beginPath(); c.moveTo(-16, -12); c.lineTo(16, -12); c.moveTo(-6, -12); c.lineTo(-6, -18); c.lineTo(6, -18); c.lineTo(6, -12); c.stroke();
  c.beginPath(); c.moveTo(-12, -8); c.lineTo(-10, 18); c.lineTo(10, 18); c.lineTo(12, -8); c.stroke(); c.restore();
}
function check(c, x, y, s, p, col = '#7CF2B0') {
  c.save(); c.translate(x, y); c.scale(s, s); c.strokeStyle = col; c.lineWidth = 7; c.lineCap = 'round'; c.lineJoin = 'round';
  c.beginPath(); const L = [[-16, 0], [-5, 12], [18, -14]];
  const segs = p * 2; c.moveTo(...L[0]);
  for (let i = 0; i < 2; i++) { const f = clamp(segs - i); if (f <= 0) break; c.lineTo(lerp(L[i][0], L[i + 1][0], f), lerp(L[i][1], L[i + 1][1], f)); }
  c.stroke(); c.restore();
}
function ring(c, x, y, p, rmax, col = '255,255,255', lw = 6) {
  if (p <= 0 || p >= 1) return; c.save(); c.globalCompositeOperation = 'lighter';
  c.strokeStyle = `rgba(${col},${(1 - p) * .9})`; c.lineWidth = lw * (1 - p) + 1; c.beginPath(); c.arc(x, y, rmax * E.out3(p), 0, 7); c.stroke(); c.restore();
}
function tap(c, x, y, p) { if (p <= 0 || p >= 1) return; c.save(); c.fillStyle = `rgba(255,255,255,${.55 * (1 - p)})`; c.beginPath(); c.arc(x, y, 18 + 50 * E.out3(p), 0, 7); c.fill(); c.restore(); ring(c, x, y, p, 90); }
function pill(c, x, y, w, h, fill, s, tc, size, a = 1) { c.save(); c.globalAlpha *= a; rr(c, x - w / 2, y - h / 2, w, h, h / 2); c.fillStyle = fill; c.fill(); txt(c, s, x, y + size * .36, size, { color: tc, w: 700 }); c.restore(); }
function spark(c, x, y, s, a = 1) { // 4-point star
  c.save(); c.globalAlpha *= a; c.translate(x, y); c.scale(s, s); c.fillStyle = '#fff'; c.shadowColor = C.cyan; c.shadowBlur = 30;
  c.beginPath(); c.moveTo(0, -30); c.quadraticCurveTo(3, -3, 30, 0); c.quadraticCurveTo(3, 3, 0, 30); c.quadraticCurveTo(-3, 3, -30, 0); c.quadraticCurveTo(-3, -3, 0, -30); c.fill(); c.restore();
}

// =====================================================================
// SCENE 1  0.0 – 2.7   A GRANDE DÚVIDA
// =====================================================================
const BUB = (() => { const R = rng(11); return Array.from({ length: 54 }, () => ({ x: (R() - .5) * 1700, y: (R() - .5) * 2900, z: 150 + R() * 2450, w: 260 + R() * 240, h: 90 + R() * 70, me: R() > .55, seed: Math.floor(R() * 1e6) })); })();
function s1(c, t) {
  // camera time with a freeze-frame on the "IA" impact
  const tc = t < .17 ? t * 1.6 : t < .32 ? .272 : .272 + (t - .32) * .75;
  bgRadial(c, CX, 900, '#16264f', C.n0, 1300);
  glow(c, CX, 820, 700, 'rgba(79,149,248,0.25)');
  // head pos (world) for push-in target
  const hp = E.outBack(prog(t, 1.0, .55), 1.3);
  const hx = 810, hy = lerp(2600, 1790, hp), hs = .6, hr = -.13 + Math.sin(t * 3) * .015;
  const [lx, ly] = headPoint(hx, hy, hs, hr, ...HEAD.lenses[0]);
  const pz = E.inExpo(prog(t, 2.2, .5));
  c.save();
  camera(c, 1 + pz * 22, lx, ly, pz);
  c.save(); camera(c, 1 + .03 * Math.sin(tc * 2), CX, 960, 0);
  // bubble field — fly-through
  const f = 900, list = BUB.map(b => { let z = b.z - tc * 1250; z = ((z - 150) % 2450 + 2450) % 2450 + 150; return { ...b, zz: z }; }).sort((a, b) => b.zz - a.zz);
  for (const b of list) {
    const s = f / b.zz, x = CX + b.x * s, y = 900 + b.y * s;
    const a = clamp((2600 - b.zz) / 700) * clamp((b.zz - 150) / 220);
    if (a <= 0.01 || s < .05) continue;
    c.save(); c.globalAlpha = a * .9; c.translate(x, y); c.scale(s, s);
    if (b.zz < 420) c.filter = `blur(${((420 - b.zz) / 30).toFixed(1)}px)`;
    rr(c, -b.w / 2, -b.h / 2, b.w, b.h, 34);
    c.fillStyle = b.me ? 'rgba(79,149,248,0.30)' : 'rgba(255,255,255,0.07)'; c.fill();
    c.lineWidth = 2; c.strokeStyle = b.me ? 'rgba(139,185,255,0.55)' : 'rgba(255,255,255,0.18)'; c.stroke();
    bars(c, -b.w / 2 + 26, -b.h / 2 + 24, b.w - 60, b.h > 130 ? 2 : 1, 'rgba(255,255,255,0.28)', 14, 14, b.seed);
    c.restore();
  }
  c.restore();
  dust(c, t, '170,205,255', .8);
  // phone
  const pp = E.outExpo(prog(t, -.18, .7));
  c.save(); c.globalAlpha = pp;
  phone(c, CX - 40, lerp(1250, 1080, pp), 400 * lerp(.8, 1, pp), 820 * lerp(.8, 1, pp), .32 * Math.sin(t * 1.4 + .6) - .1, (cc, x, y, w, h) => {
    chatScreen(cc, x, y, w, h, t, { seed: 5 });
    // abstract notification pings
    for (let i = 0; i < 3; i++) { const p = prog(t, .35 + i * .3, .5); if (p > 0 && p < 1) { cc.save(); cc.globalAlpha = 1 - p; rr(cc, x + 20, y + 140 + i * 90 - p * 30, w - 40, 70, 20); cc.fillStyle = 'rgba(255,255,255,0.18)'; cc.fill(); cc.restore(); } }
  });
  c.restore();
  // light spot on the "IA" impact
  const imp = prog(t, .17, .5); if (imp > 0 && imp < 1) glow(c, CX, 440, 520, 'rgba(115,226,255,0.55)', 1 - imp);
  // Brandon peeks in, intrigued
  if (hp > .001) drawHead(c, hx, hy, hs, hr, { glint: prog(t, 1.55, .45), rim: 'rgba(115,226,255,0.35)' });
  c.restore();
  // HUD typography (outside the camera push)
  const ha = 1 - prog(t, 2.42, .2);
  c.save(); c.globalAlpha = ha;
  headline(c, t, { text: 'UMA IA LENDO\nSEU CHAT?', y: 440, size: 132, start: -.3, stagger: .12, dur: .42, style: 'pop', hl: { IA: 'grad' }, exit: 1.62, exitDur: .25 });
  headline(c, t, { text: 'MAS…\nÉ SEGURO?', y: 440, size: 150, start: 1.86, stagger: .13, dur: .4, style: 'pop', hl: { SEGURO: 'gold' } });
  c.restore();
    if (t >= .17) flash(c, (1 - prog(t, .17, .1)) * .35, '#ffffff');
  // lens fills frame -> black
  flash(c, prog(t, 2.55, .15), '#05060a');
}

// =====================================================================
// SCENE 2  2.7 – 5.6   VOCÊ ESCOLHE O QUE ENVIAR
// =====================================================================
function s2(c, T) {
  const t = T - 2.7;
  // warm brand-blue world
  const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#3f86ee'); g.addColorStop(.5, '#4F95F8'); g.addColorStop(1, '#1d4fb0');
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  glow(c, 180, 260, 700, 'rgba(255,236,200,0.45)');
  glow(c, 900, 1500, 800, 'rgba(20,40,110,0.55)');
  // soft floating glass discs (depth)
  const R = rng(21);
  for (let i = 0; i < 7; i++) { const x = R() * W, y = R() * H, r = 60 + R() * 140, z = .4 + R() * .6; c.save(); c.globalAlpha = .25; c.beginPath(); c.arc(x + Math.sin(t + i) * 20 * z, y - t * 40 * z, r * z, 0, 7); c.fillStyle = 'rgba(255,255,255,0.18)'; c.fill(); c.restore(); }
  dust(c, T, '255,250,235', .7, 4, -10);
  const cam = E.out3(prog(t, 0, 2.9));
  c.save(); camera(c, lerp(1.08, 1, cam), CX, 900, 0);
  // phone
  const pin = E.outExpo(prog(t, .05, .6));
  const px = lerp(-200, 315, pin), py = 905;
  phone(c, px, py, 340, 700, .28 + .04 * Math.sin(t * 2), (cc, x, y, w, h) => {
    chatScreen(cc, x, y, w, h, t, { title: 'Conversa', seed: 8, bg0: '#101c38' });
    const sh = E.outExpo(prog(t, .45, .4));
    if (sh > 0) {
      cc.save(); cc.fillStyle = `rgba(0,0,0,${.35 * sh})`; cc.fillRect(x, y, w, h);
      const sy = y + h - 250 * sh; rr(cc, x, sy, w, 280, 30); cc.fillStyle = '#f4f7ff'; cc.fill();
      const rows = ['Exportar conversa', 'Mais opções'];
      rows.forEach((s, i) => { const ry = sy + 40 + i * 92; if (i === 0) { rr(cc, x + 14, ry, w - 28, 76, 18); cc.fillStyle = prog(t, .95, .1) > 0 ? 'rgba(79,149,248,0.25)' : 'rgba(79,149,248,0.10)'; cc.fill(); }
        txt(cc, s, x + 36, ry + 48, 25, { align: 'left', w: 600, color: i ? '#7a869e' : '#0B1430' }); });
      tap(cc, x + w * .62, sy + 78, prog(t, .95, .45));
      cc.restore();
    }
  });
  // drop zone card (conceptual mockup)
  const din = E.outExpo(prog(t, .25, .6));
  const dx = lerp(1300, 768, din), dy = 905, dw = 380, dh = 540;
  c.save();
  const snap = prog(t, 1.9, .5);
  const sb = snap > 0 ? 1 + .05 * Math.sin(snap * Math.PI) : 1;
  c.translate(dx, dy); c.scale(sb, sb); c.translate(-dx, -dy);
  c.save(); c.shadowColor = 'rgba(10,25,80,0.45)'; c.shadowBlur = 60; c.shadowOffsetY = 26; rr(c, dx - dw / 2, dy - dh / 2, dw, dh, 40); c.fillStyle = 'rgba(248,250,255,0.96)'; c.fill(); c.restore();
  if (IMG.logo) { c.save(); rr(c, dx - 45, dy - dh / 2 + 36, 90, 90, 24); c.clip(); c.drawImage(IMG.logo, dx - 45, dy - dh / 2 + 36, 90, 90); c.restore(); }
  txt(c, 'What Brandon Thinks', dx, dy - dh / 2 + 166, 27, { w: 700, color: C.ink });
  const zy = dy + 20, zh = 220;
  c.save(); rr(c, dx - dw / 2 + 30, zy - zh / 2 + 30, dw - 60, zh, 28); c.setLineDash([14, 12]); c.lineDashOffset = -t * 40; c.lineWidth = 4;
  c.strokeStyle = snap > 0 ? '#2f7cf0' : 'rgba(47,124,240,0.55)'; c.stroke(); c.fillStyle = `rgba(79,149,248,${.06 + .14 * snap})`; c.fill(); c.restore();
  if (snap <= 0) txt(c, 'Enviar conversa', dx, zy + 30, 26, { w: 600, color: '#5b6a88' });
  // progress & check
  const up = E.io3(prog(t, 2.05, .55));
  rr(c, dx - dw / 2 + 40, dy + dh / 2 - 90, dw - 80, 14, 7); c.fillStyle = 'rgba(11,20,48,0.1)'; c.fill();
  if (up > 0) { rr(c, dx - dw / 2 + 40, dy + dh / 2 - 90, (dw - 80) * up, 14, 7); c.fillStyle = '#2f7cf0'; c.fill(); }
  if (up >= 1) { check(c, dx - 74, dy + dh / 2 - 38, 1, E.out3(prog(t, 2.6, .25)), '#1fb46c'); txt(c, 'Enviado', dx + 18, dy + dh / 2 - 28, 26, { w: 700, color: '#1fb46c', a: prog(t, 2.6, .2) }); }
  c.restore();
  ring(c, dx, zy, snap, 260, '255,255,255', 8);
  // the file — user-initiated export flying to upload
  const fp = prog(t, 1.15, .75);
  if (t > 1.1) {
    const e = E.io3(fp);
    const x0 = px + 40, y0 = py + 160, x1 = dx, y1 = zy + 15;
    const bx = lerp(lerp(x0, CX, e), lerp(CX, x1, e), e), by = lerp(lerp(y0, 560, e), lerp(560, y1, e), e);
    const sc = (fp < 1 ? lerp(.6, 1, E.outBack(prog(t, 1.1, .3))) : 1) * (snap > 0 ? lerp(1, .72, E.outBack(clamp(snap * 3))) : 1);
    // trail
    for (let i = 1; i <= 6; i++) { const ee = E.io3(clamp(fp - i * .025)); const tx = lerp(lerp(x0, CX, ee), lerp(CX, x1, ee), ee), ty = lerp(lerp(y0, 560, ee), lerp(560, y1, ee), ee); if (fp < 1) glow(c, tx, ty, 70 - i * 7, 'rgba(255,255,255,0.35)'); }
    c.save(); c.translate(bx, by); c.rotate((1 - e) * -.4 + Math.sin(fp * Math.PI) * .15); c.scale(sc, sc);
    docIcon(c, 0, 0, 150, 190, { label: 'conversa.txt', la: 1 - snap * 2 });
    c.restore();
  }
  c.restore();
  // Brandon follows the file with his eyes
  const hin = E.outBack(prog(t, .35, .55), 1.4);
  const fx = t > 1.15 ? lerp(315, 768, E.io3(fp)) : 315;
  const hx = 540 + (fx - 540) * .22, hr = (fx - 540) * .00035 + Math.sin(t * 2.4) * .02;
  drawHead(c, hx, lerp(2650, 1925, hin), .62, hr, { glint: prog(t, 1.95, .45), rim: 'rgba(255,240,210,0.5)' });
  // typography
  headline(c, T, { text: 'VOCÊ ESCOLHE', y: 400, size: 128, start: 2.85, stagger: .1, dur: .45, style: 'rise', shadowColor: 'rgba(10,30,90,0.35)' });
  headline(c, T, { text: 'O QUE ENVIAR.', y: 532, size: 128, start: 3.2, stagger: .1, dur: .45, style: 'rise', color: C.ink, shadow: false, hl: { ENVIAR: C.ink } });
  // iris open from lens-black
  const ir = E.out3(prog(t, 0, .4));
  if (ir < 1) { c.save(); c.beginPath(); c.rect(0, 0, W, H); c.moveTo(CX + 1200 * ir, 960); c.arc(CX, 960, 1200 * ir, 0, Math.PI * 2); c.fillStyle = '#05060a'; c.fill('evenodd'); c.restore(); }
  // exit bloom
  const ex = prog(t, 2.62, .28);
  if (ex > 0) { glow(c, 768, 865, 300 + 1400 * E.in3(ex), 'rgba(200,240,255,1)', ex); flash(c, E.in3(ex) * .95, '#e6f6ff'); }
}

// =====================================================================
// SCENE 3  5.6 – 9.0   CRIPTOGRAFIA
// =====================================================================
const SPH = (() => { const R = rng(31), N = 560, gold = 2.399963; return Array.from({ length: N }, (_, i) => { const y = 1 - (i / (N - 1)) * 2, r = Math.sqrt(1 - y * y), th = gold * i; return { x: Math.cos(th) * r, y, z: Math.sin(th) * r, sx: (R() - .5) * 220, sy: (R() - .5) * 280, d: R() * .35 }; }); })();
const HEXS = (() => { const R = rng(41); return Array.from({ length: 26 }, () => Array.from({ length: 4 }, () => Math.floor(R() * 65536).toString(16).padStart(4, '0')).join(' ')); })();
function s3(c, T) {
  const t = T - 5.6, cx = CX, cy = 860;
  bgRadial(c, cx, cy, '#0f1f48', C.n0, 1300);
  const zin = E.inExpo(prog(t, 3.05, .35));
  c.save(); camera(c, 1 + zin * 7, cx, cy, 0);
  // tunnel of hex rings
  for (let i = 0; i < 16; i++) {
    let z = ((i / 16 - t * .32) % 1 + 1) % 1; const s = .15 + Math.pow(z, 2.2) * 4.5; const a = clamp(z * 2) * clamp((1 - z) * 4) * .55;
    c.save(); c.globalAlpha = a; shieldPath(c, cx, cy, 300 * s); c.lineWidth = 2 + z * 3; c.strokeStyle = i % 3 ? 'rgba(79,149,248,0.7)' : 'rgba(115,226,255,0.9)'; c.stroke(); c.restore();
  }
  // light streaks
  const R = rng(51);
  c.save(); c.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 46; i++) { const ang = R() * 6.283, sp = .4 + R(); const d = ((R() + t * sp * .7) % 1); const r0 = 120 + d * d * 1500, r1 = r0 + 40 + d * 220;
    c.strokeStyle = `rgba(140,200,255,${(d * .6).toFixed(3)})`; c.lineWidth = 1 + d * 3; c.beginPath(); c.moveTo(cx + Math.cos(ang) * r0, cy + Math.sin(ang) * r0); c.lineTo(cx + Math.cos(ang) * r1, cy + Math.sin(ang) * r1); c.stroke(); }
  c.restore();
  // data sphere — particles condense from the file
  const rotA = t * .9, rotB = .35, rad = 190;
  const pts = SPH.map(p => {
    let x = p.x * Math.cos(rotA) - p.z * Math.sin(rotA), z = p.x * Math.sin(rotA) + p.z * Math.cos(rotA);
    let y = p.y * Math.cos(rotB) - z * Math.sin(rotB); z = p.y * Math.sin(rotB) + z * Math.cos(rotB);
    const k = E.io3(prog(t, .05 + p.d, .7));
    return { x: lerp(cx + p.sx, cx + x * rad, k), y: lerp(cy + p.sy, cy + y * rad, k), z, k };
  }).sort((a, b) => a.z - b.z);
  c.save(); c.globalCompositeOperation = 'lighter';
  for (const p of pts) { const s = 1.6 + (p.z + 1) * 1.8; c.fillStyle = `rgba(${p.z > .3 ? '230,248,255' : '115,226,255'},${(.35 + (p.z + 1) * .32).toFixed(3)})`; c.beginPath(); c.arc(p.x, p.y, s, 0, 7); c.fill(); }
  c.restore();
  glow(c, cx, cy, 320, 'rgba(79,149,248,0.35)');
  // the incoming file dissolving
  const fd = prog(t, 0, .45); if (fd < 1) { c.save(); c.globalAlpha = 1 - fd; c.filter = `blur(${fd * 20}px)`; docIcon(c, cx, cy, 150 * (1 + fd), 190 * (1 + fd)); c.restore(); }
  // glass shield with cryptographic patterning
  const sp = E.io3(prog(t, .55, .6)), lock = prog(t, 1.9, .1);
  const pulse = lock > 0 ? (1 - prog(t, 1.95, .6)) : 0;
  if (sp > 0) {
    const sr = 300 + 10 * Math.sin(t * 3);
    c.save(); shieldPath(c, cx, cy, sr); c.clip();
    c.globalAlpha = sp * .9;
    const fg = c.createLinearGradient(cx - sr, cy - sr, cx + sr, cy + sr); fg.addColorStop(0, 'rgba(160,210,255,0.20)'); fg.addColorStop(1, 'rgba(79,149,248,0.06)');
    c.fillStyle = fg; c.fillRect(cx - sr, cy - sr, 2 * sr, 2 * sr);
    c.font = font(17, 500, 'SG'); c.fillStyle = 'rgba(160,220,255,0.22)'; c.textAlign = 'center';
    HEXS.forEach((s, i) => c.fillText(s, cx + ((i % 2) ? 40 : -40), cy - sr + 30 + i * 24 - (t * 30 % 24)));
    c.lineWidth = 1.2; c.strokeStyle = 'rgba(160,220,255,0.18)';
    for (let gx = -6; gx <= 6; gx++) for (let gy = -7; gy <= 7; gy++) { shieldPath(c, cx + gx * 52 + (gy % 2) * 26, cy + gy * 45, 30); c.stroke(); }
    c.restore();
    c.save(); shieldPath(c, cx, cy, sr); c.setLineDash([sr * 6 * sp, 4000]); c.lineWidth = 7 + pulse * 6; c.shadowColor = C.cyan; c.shadowBlur = 30 + pulse * 60;
    const sg = c.createLinearGradient(cx - sr, cy - sr, cx + sr, cy + sr); sg.addColorStop(0, '#ffffff'); sg.addColorStop(.5, C.cyan); sg.addColorStop(1, C.blue);
    c.strokeStyle = sg; c.stroke(); c.restore();
  }
  // lock mechanism
  const lp = E.outBack(prog(t, 1.15, .4), 2);
  if (lp > 0) { lockIcon(c, cx, cy + 20, lerp(.3, 1.15, lp) * (1 + pulse * .08), E.outBack(lock, 3)); }
  ring(c, cx, cy, prog(t, 1.95, .6), 520, '200,240,255', 10);
  if (pulse > 0) glow(c, cx, cy, 600, 'rgba(160,230,255,0.6)', pulse);
  // protected path to secure storage
  const fl = prog(t, 2.15, .8);
  if (fl > 0) {
    const sx = 800, sy = 1330;
    c.save(); c.lineWidth = 5; c.strokeStyle = 'rgba(115,226,255,0.5)'; c.setLineDash([2, 12]); c.lineCap = 'round';
    c.beginPath(); c.moveTo(cx + 140, cy + 260); c.quadraticCurveTo(820, 1150, sx, sy - 70); c.stroke(); c.restore();
    for (let i = 0; i < 4; i++) { const q = clamp(fl * 1.6 - i * .15); if (q <= 0 || q >= 1) continue; const x = lerp(lerp(cx + 140, 820, q), lerp(820, sx, q), q), y = lerp(lerp(cy + 260, 1150, q), lerp(1150, sy - 70, q), q); glow(c, x, y, 40, 'rgba(200,245,255,1)'); }
    const so = E.outBack(prog(t, 2.15, .4));
    c.save(); c.globalAlpha = so; c.translate(sx, sy); c.scale(so, so);
    for (let i = 2; i >= 0; i--) { c.beginPath(); c.ellipse(0, i * 38 - 30, 78, 24, 0, 0, 7); c.fillStyle = '#0d1a3a'; c.fill(); c.lineWidth = 4; c.strokeStyle = i === 0 && fl > .7 ? C.cyan : 'rgba(115,226,255,0.6)'; c.stroke(); }
    lockIcon(c, 62, 40, .38, 1);
    c.restore();
    if (fl > .7) glow(c, sx, sy, 180, 'rgba(115,226,255,0.5)', 1 - prog(t, 2.8, .4));
  }
  // Brandon floats beside the shield and nods on the lock
  const hin = E.outBack(prog(t, .8, .5), 1.4);
  const nod = Math.sin(clamp((t - 1.85) / .35) * Math.PI) * .12;
  drawHead(c, 215, lerp(1900, 1460, hin) + Math.sin(t * 2.2) * 10 + nod * 60, .4, -.08 + nod, { glint: prog(t, 2.0, .45), rim: 'rgba(115,226,255,0.55)' });
  c.restore();
  // type
  c.save(); c.globalAlpha = 1 - zin;
  headline(c, T, { text: 'CRIPTOGRAFADO.', y: 405, size: 118, start: 5.75, stagger: 0, dur: .6, style: 'track', hl: { CRIPTOGRAFADO: 'grad' } });
  const sa = E.out3(prog(T, 6.3, .4));
  c.save(); c.globalAlpha *= sa; c.filter = sa < 1 ? `blur(${(1 - sa) * 10}px)` : 'none';
  txt(c, 'NO ENVIO + NO ARMAZENAMENTO', CX, 488 + (1 - sa) * 20, 40, { w: 700, color: C.cream, ls: 3 });
  c.restore(); c.restore();
  flash(c, (1 - prog(t, 0, .3)) * .9, '#e6f6ff');
  flash(c, E.in3(prog(t, 3.2, .2)), '#dff1ff');
}

// =====================================================================
// SCENE 4  9.0 – 11.8   NINGUÉM DO CHAT É AVISADO
// =====================================================================
function s4(c, T) {
  const t = T - 9.0;
  bgRadial(c, CX, 850, '#1a2f66', '#060b1a', 1300);
  glow(c, CX, 860, 650, 'rgba(79,149,248,0.28)');
  dust(c, T, '170,205,255', .6);
  // match-cut: hexagon dissolves into the chat card
  const m = E.out3(prog(t, 0, .45));
  if (m < 1) { c.save(); c.globalAlpha = 1 - m; shieldPath(c, CX, 860, lerp(700, 380, m)); c.lineWidth = 8; c.strokeStyle = C.cyan; c.shadowColor = C.cyan; c.shadowBlur = 40; c.stroke(); c.restore(); }
  const cw = 780, ch = 380, cx = CX, cy = 830;
  c.save(); c.globalAlpha = m; c.translate(cx, cy); c.scale(lerp(1.25, 1, m), lerp(1.25, 1, m)); c.translate(-cx, -cy);
  glass(c, cx - cw / 2, cy - ch / 2, cw, ch, 40);
  const av = [['A', '#F2B880'], ['M', '#8BB9FF'], ['J', '#9fe0b8']];
  av.forEach(([l, col], i) => { const ax = cx - cw / 2 + 70 + i * 52; c.beginPath(); c.arc(ax, cy - ch / 2 + 74, 32, 0, 7); c.fillStyle = col; c.fill(); c.lineWidth = 5; c.strokeStyle = '#13224A'; c.stroke(); txt(c, l, ax, cy - ch / 2 + 84, 28, { w: 700, color: C.ink }); });
  txt(c, 'Conversa em grupo', cx - cw / 2 + 210, cy - ch / 2 + 70, 30, { align: 'left', w: 700, color: '#fff' });
  txt(c, '3 participantes', cx - cw / 2 + 210, cy - ch / 2 + 106, 24, { align: 'left', w: 500, color: 'rgba(220,232,255,0.7)' });
  const R = rng(61);
  for (let i = 0; i < 3; i++) { const me = i === 1, bw = 300 + R() * 160, bx = me ? cx + cw / 2 - bw - 36 : cx - cw / 2 + 36, by = cy - 20 + i * 64; rr(c, bx, by, bw, 50, 22); c.fillStyle = me ? 'rgba(79,149,248,0.7)' : 'rgba(255,255,255,0.12)'; c.fill(); bars(c, bx + 18, by + 18, bw - 40, 1, 'rgba(255,255,255,0.45)', 12, 0, i + 70); }
  c.restore();
  // private flow: card -> private report (no branches to participants)
  const lp = E.io3(prog(t, .55, .55));
  const y0 = cy + ch / 2, y1 = 1160;
  if (lp > 0) {
    c.save(); c.lineWidth = 6; c.lineCap = 'round'; c.strokeStyle = 'rgba(115,226,255,0.9)'; c.shadowColor = C.cyan; c.shadowBlur = 20;
    c.beginPath(); c.moveTo(cx, y0); c.lineTo(cx, lerp(y0, y1 - 60, lp)); c.stroke(); c.restore();
    for (let i = 0; i < 3; i++) { const q = ((t * 1.2 + i / 3) % 1); if (lp >= 1) glow(c, cx, lerp(y0, y1 - 60, q), 30, 'rgba(220,250,255,1)'); }
  }
  const rp = E.outBack(prog(t, 1.0, .4));
  if (rp > 0) {
    c.save(); c.globalAlpha = clamp(rp); c.translate(cx, y1); c.scale(rp, rp);
    glass(c, -250, -60, 500, 120, 60, { top: 'rgba(255,255,255,0.22)' });
    lockIcon(c, -180, 6, .38, 1);
    txt(c, 'Relatório privado', 30, 12, 34, { w: 700, color: '#fff' });
    c.restore();
  }
  // muted bells pop on the participants
  av.forEach((_, i) => { const p = E.outBack(prog(t, .9 + i * .1, .35), 2.4); if (p > 0) bell(c, cx - cw / 2 + 70 + i * 52 + 14, cy - ch / 2 - 6, .62 * p, true); });
  // Brandon: "shhh"
  const hin = E.outBack(prog(t, .3, .5), 1.4);
  drawHead(c, 250, lerp(2650, 1880, hin) + Math.sin(t * 2) * 8, .58, .1 + Math.sin(t * 1.6) * .02, { glint: prog(t, 1.2, .5), rim: 'rgba(139,185,255,0.45)' });
  const bp = E.outBack(prog(t, 1.05, .35), 2);
  if (bp > 0) { c.save(); c.translate(560, 1440); c.scale(bp, bp); glass(c, -130, -50, 260, 100, 50, { top: 'rgba(255,255,255,0.9)', bot: 'rgba(235,242,255,0.85)', shadowBlur: 30 });
    c.beginPath(); c.moveTo(-90, 40); c.lineTo(-140, 80); c.lineTo(-50, 48); c.fillStyle = 'rgba(240,245,255,0.9)'; c.fill();
    txt(c, 'Shhh…', 0, 16, 42, { fam: 'Sora', w: 800, color: C.ink }); c.restore(); }
  headline(c, T, { text: 'NINGUÉM DO CHAT', y: 400, size: 124, start: 9.15, stagger: .09, dur: .45, style: 'rise' });
  headline(c, T, { text: 'É AVISADO.', y: 535, size: 132, start: 9.85, stagger: .12, dur: .45, style: 'pop', hl: { É: 'gold', AVISADO: 'gold' } });
  flash(c, (1 - prog(t, 0, .35)) * .85, '#dff1ff');
}

// =====================================================================
// SCENE 5  11.8 – 14.9   SEUS CHATS NÃO TREINAM IA
// =====================================================================
function s5(c, T) {
  const t = T - 11.8;
  c.fillStyle = '#060a16'; c.fillRect(0, 0, W, H);
  glow(c, CX, 900, 800, 'rgba(40,80,170,0.35)');
  c.save(); c.fillStyle = 'rgba(140,180,255,0.10)'; for (let x = 30; x < W; x += 60) for (let y = 30; y < H; y += 60) { c.beginPath(); c.arc(x, y, 1.6, 0, 7); c.fill(); } c.restore();
  const A = [CX, 660], L1 = [300, 880], L2 = [300, 1110], R1 = [785, 880];
  const blk = prog(t, 1.2, .2);
  const draw = (p, a, b, col, w = 6) => { if (p <= 0) return; c.save(); c.lineWidth = w; c.lineCap = 'round'; c.strokeStyle = col; c.shadowColor = col; c.shadowBlur = 16; c.beginPath(); c.moveTo(a[0], a[1]); const my = (a[1] + b[1]) / 2; const e = clamp(p);
    // cubic path sampled up to e
    for (let i = 1; i <= 30 * e; i++) { const q = i / 30; const x = Math.pow(1 - q, 3) * a[0] + 3 * Math.pow(1 - q, 2) * q * a[0] + 3 * (1 - q) * q * q * b[0] + q * q * q * b[0]; const y = Math.pow(1 - q, 3) * a[1] + 3 * Math.pow(1 - q, 2) * q * my + 3 * (1 - q) * q * q * my + q * q * q * b[1]; c.lineTo(x, y); }
    c.stroke(); c.restore(); };
  const ptOn = (a, b, q) => { const my = (a[1] + b[1]) / 2; return [Math.pow(1 - q, 3) * a[0] + 3 * Math.pow(1 - q, 2) * q * a[0] + 3 * (1 - q) * q * q * b[0] + q * q * q * b[0], Math.pow(1 - q, 3) * a[1] + 3 * Math.pow(1 - q, 2) * q * my + 3 * (1 - q) * q * q * my + q * q * q * b[1]]; };
  const lp = E.io3(prog(t, .2, .55));
  draw(lp, A, L1, C.cyan); draw(E.io3(prog(t, .55, .4)), L1, L2, C.cyan);
  draw(lp, A, R1, blk > 0 ? `rgba(120,130,150,${lerp(.9, .35, blk)})` : C.blueL);
  // flowing data
  for (let i = 0; i < 6; i++) {
    const q = ((t * .9 + i / 6) % 1);
    if (t > .6) { const [x, y] = ptOn(A, L1, q); glow(c, x, y, 26, 'rgba(210,250,255,1)'); }
    if (t > 1.0) { const [x, y] = ptOn(L1, L2, q); glow(c, x, y, 26, 'rgba(210,250,255,1)'); }
    if (t > .6) { const [x, y] = ptOn(A, R1, q); if (blk <= 0 || q < .45) glow(c, x, y, 26, 'rgba(180,210,255,1)', blk > 0 ? (1 - prog(t, 1.2, .5)) : 1); }
  }
  // nodes
  const node = (p, x, y, w, label, o = {}) => { if (p <= 0) return; c.save(); c.globalAlpha = clamp(p) * (o.dim ? lerp(1, .4, o.dim) : 1); c.translate(x, y); const s = E.outBack(clamp(p)); c.scale(s, s);
    glass(c, -w / 2, -48, w, 96, 48, { top: o.top || 'rgba(255,255,255,0.14)', edge2: o.edge || 'rgba(140,190,255,0.35)' });
    if (o.icon) o.icon(c, -w / 2 + 52, 0); txt(c, label, o.icon ? 22 : 0, 11, 30, { w: 700, color: '#fff' }); c.restore(); };
  node(prog(t, 0, .35), A[0], A[1], 360, 'Sua conversa', { icon: (cc, x, y) => docIcon(cc, x, y, 36, 46, { gb: 10 }) });
  node(prog(t, .65, .35), L1[0], L1[1], 380, 'Análise por IA', { icon: (cc, x, y) => spark(cc, x, y, .7), edge: 'rgba(115,226,255,0.8)' });
  node(prog(t, 1.0, .35), L2[0], L2[1], 340, 'Relatório', { icon: (cc, x, y) => check(cc, x, y, .9, prog(t, 1.6, .3)), top: prog(t, 1.6, .2) > 0 ? 'rgba(124,242,176,0.22)' : undefined, edge: 'rgba(124,242,176,0.8)' });
  node(prog(t, .65, .35), R1[0], R1[1], 420, 'Treinar modelos', { dim: blk });
  // barrier
  if (blk > 0) {
    const bx = 668, by = 772, bs = E.outBack(blk, 2.5);
    c.save(); c.translate(bx, lerp(by - 200, by, E.out3(blk))); c.scale(bs, bs);
    c.shadowColor = 'rgba(255,107,122,0.8)'; c.shadowBlur = 40; c.beginPath(); c.arc(0, 0, 54, 0, 7); c.fillStyle = 'rgba(20,10,20,0.92)'; c.fill();
    c.lineWidth = 10; c.strokeStyle = '#ff6b7a'; c.stroke(); c.beginPath(); c.moveTo(-36, -36); c.lineTo(36, 36); c.stroke(); c.restore();
    ring(c, bx, by, prog(t, 1.3, .5), 220, '255,120,130', 8);
    const tg = E.out3(prog(t, 1.45, .3)); if (tg > 0) pill(c, R1[0], R1[1] + 92, 210, 54, 'rgba(255,107,122,0.18)', 'Bloqueado', '#ff9aa4', 26, tg);
    // disintegrating particles past the barrier
    const R = rng(71); for (let i = 0; i < 40; i++) { const q = prog(t, 1.2 + R() * .2, .8); if (q <= 0 || q >= 1) continue; const x = bx + 20 + R() * 120 + q * 80 * R(), y = by + R() * 90 - q * 120; c.fillStyle = `rgba(190,200,230,${(1 - q) * .8})`; c.beginPath(); c.arc(x, y, 2 + R() * 2, 0, 7); c.fill(); }
  }
  // Brandon reaches toward the training line — a spark travels to the barrier
  const hin = E.outBack(prog(t, .25, .5), 1.4);
  const lean = E.io3(prog(t, .95, .3)) * (1 - E.io3(prog(t, 1.5, .4)));
  const hx = 820 - lean * 40, hy = lerp(2650, 1880, hin) + Math.sin(t * 2) * 8;
  drawHead(c, hx, hy, .56, -.08 - lean * .12, { glint: prog(t, 1.05, .4), rim: 'rgba(139,185,255,0.45)' });
  const sp = prog(t, 1.0, .22); if (sp > 0 && sp < 1) { const x = lerp(hx - 60, 668, E.io3(sp)), y = lerp(hy - 420, 772, E.io3(sp)); spark(c, x, y, .8); glow(c, x, y, 80, 'rgba(160,230,255,0.8)'); }
  headline(c, T, { text: 'SEUS CHATS NÃO', y: 400, size: 124, start: 11.95, stagger: .1, dur: .45, style: 'rise' });
  headline(c, T, { text: 'TREINAM IA.', y: 532, size: 132, start: 12.5, stagger: .14, dur: .45, style: 'pop', hl: { IA: 'grad' } });
  const sh = E.outBack(prog(T, 12.9, .4), 2);
  if (sh > 0) { c.save(); c.translate(905, 478); c.scale(sh * .5, sh * .5); shieldPath(c, 0, 0, 60); c.fillStyle = 'rgba(115,226,255,0.25)'; c.fill(); c.lineWidth = 6; c.strokeStyle = C.cyan; c.stroke(); check(c, 0, 2, 1, 1, '#fff'); c.restore(); }
}

// =====================================================================
// SCENE 6  14.9 – 18.0   VOCÊ CONTROLA SEUS DADOS
// =====================================================================
function s6(c, T) {
  const t = T - 14.9;
  bgRadial(c, 300, 600, '#1d3a7a', '#070c1c', 1500);
  glow(c, 900, 1300, 700, 'rgba(79,149,248,0.25)');
  dust(c, T, '200,220,255', .6, -4, -8);
  const pin = E.outExpo(prog(t, .05, .6));
  const px = CX, py = lerp(1300, 950, pin), pw = 840, ph = 560;
  c.save(); c.globalAlpha = clamp(pin * 1.5);
  glass(c, px - pw / 2, py - ph / 2, pw, ph, 44, { top: 'rgba(255,255,255,0.15)' });
  txt(c, 'Minha conta', px - pw / 2 + 44, py - ph / 2 + 64, 32, { align: 'left', w: 700 });
  txt(c, 'Privacidade', px + pw / 2 - 44, py - ph / 2 + 64, 26, { align: 'right', w: 600, color: C.cyan });
  c.fillStyle = 'rgba(255,255,255,0.12)'; c.fillRect(px - pw / 2 + 40, py - ph / 2 + 92, pw - 80, 2);
  const del = prog(t, 1.15, .55), up = E.io3(prog(t, 1.55, .35));
  const items = ['Conversa · Amigos', 'Conversa · Grupo', 'Conversa · Trabalho'];
  items.forEach((s, i) => {
    let y = py - ph / 2 + 128 + i * 112; if (i === 2) y -= 112 * up;
    const x = px - pw / 2 + 40, w = pw - 80, h = 92;
    if (i === 1 && del > 0) {
      // refined dissolve into particles
      const R = rng(81);
      c.save(); c.globalAlpha = (1 - E.out3(del)) * .9; c.filter = `blur(${del * 8}px)`; rr(c, x + del * 40, y, w, h, 24); c.fillStyle = 'rgba(255,255,255,0.10)'; c.fill(); c.restore();
      c.save(); c.globalCompositeOperation = 'lighter';
      for (let k = 0; k < 120; k++) { const ox = x + R() * w, oy = y + R() * h, vx = 120 + R() * 380, vy = -60 - R() * 220, q = E.out3(clamp(del * 1.3 - R() * .3)); if (q <= 0) continue;
        c.fillStyle = `rgba(190,225,255,${((1 - q) * .9).toFixed(3)})`; c.beginPath(); c.arc(ox + vx * q, oy + vy * q, 2.4 * (1 - q) + .6, 0, 7); c.fill(); }
      c.restore(); return;
    }
    rr(c, x, y, w, h, 24); c.fillStyle = i === 1 && t > 1.0 ? 'rgba(255,107,122,0.12)' : 'rgba(255,255,255,0.08)'; c.fill();
    c.beginPath(); c.arc(x + 50, y + 46, 22, 0, 7); c.fillStyle = ['#F2B880', '#8BB9FF', '#9fe0b8'][i]; c.fill();
    txt(c, s, x + 92, y + 56, 28, { align: 'left', w: 600, color: '#eef3ff' });
    rr(c, x + w - 84, y + 18, 56, 56, 16); c.fillStyle = 'rgba(255,107,122,0.14)'; c.fill(); trash(c, x + w - 56, y + 47, 1);
  });
  // tap on delete
  tap(c, px + pw / 2 - 96, py - ph / 2 + 128 + 112 + 47, prog(t, .95, .45));
  // auto-removal note (conversations only, not reports)
  const note = E.out3(prog(t, 1.85, .45));
  if (note > 0) {
    c.save(); c.globalAlpha *= note; const ny = py + ph / 2 - 120 + (1 - note) * 20;
    rr(c, px - pw / 2 + 40, ny, pw - 80, 84, 22); c.fillStyle = 'rgba(115,226,255,0.10)'; c.fill(); c.lineWidth = 2; c.strokeStyle = 'rgba(115,226,255,0.35)'; c.stroke();
    // clock
    c.beginPath(); c.arc(px - pw / 2 + 86, ny + 42, 20, 0, 7); c.lineWidth = 4; c.strokeStyle = C.cyan; c.stroke();
    c.beginPath(); c.moveTo(px - pw / 2 + 86, ny + 30); c.lineTo(px - pw / 2 + 86, ny + 43); c.lineTo(px - pw / 2 + 96, ny + 49); c.stroke();
    txt(c, 'Conversas enviadas são removidas em até', px - pw / 2 + 126, ny + 36, 23, { align: 'left', w: 500, color: '#dff4ff' });
    txt(c, '7 dias após o último relatório.', px - pw / 2 + 126, ny + 66, 23, { align: 'left', w: 500, color: '#dff4ff' });
    c.restore();
  }
  c.restore();
  // Brandon taps delete — spark from his gaze
  const hin = E.outBack(prog(t, .3, .5), 1.4);
  const hx = 200, hy = lerp(2650, 1900, hin) + Math.sin(t * 2) * 8;
  drawHead(c, hx, hy, .52, .12, { glint: prog(t, .85, .4), rim: 'rgba(139,185,255,0.45)' });
  const sp = prog(t, .78, .2); if (sp > 0 && sp < 1) { const x = lerp(hx + 60, px + pw / 2 - 96, E.io3(sp)), y = lerp(hy - 420, py - ph / 2 + 287, E.io3(sp)); spark(c, x, y, .7); glow(c, x, y, 70, 'rgba(160,230,255,0.8)'); }
  headline(c, T, { text: 'VOCÊ CONTROLA', y: 390, size: 124, start: 15.0, stagger: .1, dur: .45, style: 'rise' });
  headline(c, T, { text: 'SEUS DADOS.', y: 520, size: 132, start: 15.45, stagger: .13, dur: .45, style: 'pop', hl: { DADOS: 'grad' } });
  const sa = E.out3(prog(T, 16.15, .4));
  if (sa > 0) { c.save(); c.globalAlpha = sa; c.letterSpacing = '0px'; pill(c, CX, 600 + (1 - sa) * 16, 560, 66, 'rgba(255,255,255,0.12)', 'EXCLUA QUANDO QUISER', C.cream, 30); c.restore(); }
  // warm light-leak into the reveal
  const lk = prog(t, 2.85, .25); if (lk > 0) { glow(c, 900, 300, 600 + 1600 * lk, 'rgba(255,215,150,1)', lk); flash(c, E.in3(lk) * .8, '#fff2dc'); }
}

// =====================================================================
// SCENE 7  18.0 – 21.1   O VEREDITO DO BRANDON
// =====================================================================
function s7(c, T) {
  const t = T - 18.0;
  // ambient plate from the desk scene: heavy blur, lateral parallax
  const pan = lerp(60, -60, E.io3(prog(t, 0, 3.1)));
  if (IMG.desk) { c.save(); c.filter = 'blur(26px) brightness(0.55) saturate(1.1)'; const s = 2.1; c.drawImage(IMG.desk, CX - 1254 * s / 2 + pan * .5 - 120, 960 - 1254 * s / 2 - 200, 1254 * s, 1254 * s); c.restore(); }
  const ov = c.createLinearGradient(0, 0, 0, H); ov.addColorStop(0, 'rgba(6,10,26,0.80)'); ov.addColorStop(.6, 'rgba(10,18,40,0.55)'); ov.addColorStop(1, 'rgba(6,10,26,0.9)');
  c.fillStyle = ov; c.fillRect(0, 0, W, H);
  glow(c, 220, 520, 600, 'rgba(255,200,120,0.25)');
  dust(c, T, '255,230,190', .7, 8, -6);
  // floating analysis cards in depth
  const rec = E.io3(prog(t, 1.8, .4)), gather = E.in3(prog(t, 2.75, .35));
  const card = (i, y, w, h, title, body) => {
    const p = E.outBack(prog(t, .2 + i * .48, .5), 1.5); if (p <= 0) return;
    const depth = [1.0, .7, 1.25][i];
    let x = CX + pan * depth * (i === 1 ? -1 : 1) + (1 - p) * (i % 2 ? -700 : 700);
    let s = lerp(1, .82, rec) * (1 - gather * .8); let yy = lerp(y, y + (i - 1) * -40, rec);
    x = lerp(x, CX, gather); yy = lerp(yy, 590, gather);
    c.save(); c.globalAlpha = clamp(p) * lerp(1, .35, rec) * (1 - gather); c.translate(x, yy); c.rotate((i - 1) * .025 * (1 - rec)); c.scale(s, s);
    if (rec > 0) c.filter = `blur(${rec * 7}px)`;
    glass(c, -w / 2, -h / 2, w, h, 36, { top: 'rgba(255,255,255,0.18)', bot: 'rgba(255,255,255,0.07)' });
    txt(c, title, -w / 2 + 40, -h / 2 + 62, 34, { align: 'left', fam: 'Sora', w: 800, color: C.cream, ls: 1 });
    body(c, -w / 2 + 40, -h / 2 + 90, w - 80, h - 120, p);
    c.restore();
  };
  card(0, 470, 820, 230, 'PADRÕES DA CONVERSA', (c, x, y, w, h) => {
    const R = rng(91); for (let i = 0; i < 12; i++) { const v = .25 + R() * .75, gp = E.out3(prog(t, .45 + i * .03, .4)); rr(c, x + i * (w / 12), y + h - v * h * gp + 10, w / 12 - 14, v * h * gp, 8); const g = c.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, C.cyan); g.addColorStop(1, C.blue); c.fillStyle = g; c.fill(); }
  });
  card(1, 730, 820, 230, 'QUEM PUXA ASSUNTO?', (c, x, y, w, h) => {
    [['Pessoa A', .78, C.goldL], ['Pessoa B', .46, C.blueL]].forEach(([l, v, col], i) => { const gp = E.out3(prog(t, .95 + i * .1, .5)); txt(c, l, x, y + 40 + i * 62, 26, { align: 'left', w: 600, color: '#dfe8fa' }); rr(c, x + 150, y + 18 + i * 62, (w - 160), 28, 14); c.fillStyle = 'rgba(255,255,255,0.08)'; c.fill(); rr(c, x + 150, y + 18 + i * 62, (w - 160) * v * gp, 28, 14); c.fillStyle = col; c.fill(); });
  });
  card(2, 990, 820, 230, 'O VEREDITO DO BRANDON', (c, x, y, w, h) => {
    txt(c, '“', x + 10, y + 86, 110, { fam: 'Sora', w: 800, color: C.gold, align: 'left' });
    bars(c, x + 80, y + 20, w - 120, 3, 'rgba(255,255,255,0.35)', 16, 16, 93);
  });
  // the character reads the report… then turns to camera
  const cin = E.out3(prog(t, .0, .6)), cout = E.in3(prog(t, 1.85, .25));
  if (cout < 1) drawChar(c, CX + pan * .3, lerp(2650, 1985, cin) + cout * 500 + Math.sin(t * 2) * 6, 1.02, 0, { a: 1 - cout * .3, rim: 'rgba(255,215,150,0.35)' });
  const hp = E.outBack(prog(t, 2.0, .45), 2.2);
  if (hp > .001) {
    const hop = Math.sin(clamp((t - 2.35) / .3) * Math.PI) * 40;
    const hx = lerp(CX, CX, gather), hy = lerp(lerp(2700, 1900, hp) - hop, 830, gather), hs = lerp(.66, .38, gather);
    drawHead(c, hx, hy, hs, Math.sin(t * 5) * .03 * (1 - gather), { glint: prog(t, 2.45, .45), rim: 'rgba(255,215,150,0.55)', sy: 1 + Math.sin(clamp((t - 2.35) / .3) * Math.PI) * .04, shadow: gather < .1 });
  }
  headline(c, T, { text: 'E O BRANDON?', y: 660, size: 132, start: 19.88, stagger: .1, dur: .4, style: 'rise', exit: 20.85, exitDur: .22 });
  headline(c, T, { text: 'TEM UMA OPINIÃO.', y: 800, size: 116, start: 20.3, stagger: .09, dur: .4, style: 'pop', hl: { OPINIÃO: 'gold' }, exit: 20.85, exitDur: .22 });
  flash(c, (1 - prog(t, 0, .4)) * .8, '#fff2dc');
}

// =====================================================================
// SCENE 8  21.1 – 24.0   CTA + MARCA
// =====================================================================
function s8(c, T) {
  const t = T - 21.1;
  bgRadial(c, CX, 600, '#2a5fc4', '#050a1a', 1400);
  // rotating light rays behind the logo
  c.save(); c.globalCompositeOperation = 'lighter'; c.translate(CX, 590); c.rotate(t * .12);
  for (let i = 0; i < 14; i++) { c.rotate(Math.PI * 2 / 14); const g = c.createLinearGradient(0, 0, 0, -1100); g.addColorStop(0, 'rgba(139,185,255,0.18)'); g.addColorStop(1, 'rgba(139,185,255,0)'); c.fillStyle = g; c.beginPath(); c.moveTo(0, 0); c.lineTo(-60, -1100); c.lineTo(60, -1100); c.fill(); }
  c.restore();
  glow(c, CX, 590, 520, 'rgba(79,149,248,0.55)');
  dust(c, T, '200,225,255', .9);
  // logo: the head flies in and settles into the official mark
  const lp = E.outBack(prog(t, 0, .55), 1.6), ls = 420;
  const breathe = 1 + .012 * Math.sin(t * 3);
  c.save(); c.translate(CX, 590); c.scale(lp * breathe, lp * breathe);
  c.shadowColor = 'rgba(0,0,0,0.55)'; c.shadowBlur = 80; c.shadowOffsetY = 30;
  rr(c, -ls / 2, -ls / 2, ls, ls, ls * .23); c.fillStyle = '#4F95F8'; c.fill(); c.shadowColor = 'transparent';
  c.save(); rr(c, -ls / 2, -ls / 2, ls, ls, ls * .23); c.clip(); if (IMG.logo) c.drawImage(IMG.logo, -ls / 2, -ls / 2, ls, ls);
  for (const sw of [prog(t, .55, .7), prog(t, 2.2, .7)]) if (sw > 0 && sw < 1) { c.save(); c.rotate(-.5); const x = lerp(-ls, ls, E.io3(sw)); const g = c.createLinearGradient(x - 80, 0, x + 80, 0); g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(.5, 'rgba(255,255,255,0.45)'); g.addColorStop(1, 'rgba(255,255,255,0)'); c.fillStyle = g; c.fillRect(-ls, -ls, 2 * ls, 2 * ls); c.restore(); }
  c.restore();
  rr(c, -ls / 2, -ls / 2, ls, ls, ls * .23); c.lineWidth = 3; c.strokeStyle = 'rgba(255,255,255,0.35)'; c.stroke();
  c.restore();
  ring(c, CX, 590, prog(t, .3, .7), 520, '200,230,255', 8);
  // brand name
  const wa = E.out3(prog(t, .3, .5));
  txt(c, 'WHAT BRANDON THINKS', CX, 870, 50, { fam: 'Sora', w: 800, color: C.cream, ls: lerp(24, 4, wa), a: wa });
  headline(c, T, { text: 'AGORA É SUA VEZ.', y: 990, size: 98, start: 21.45, stagger: .08, dur: .4, style: 'rise' });
  const cp = E.outBack(prog(t, .85, .45), 1.8);
  if (cp > 0) {
    const pulse = 1 + .03 * Math.sin(Math.max(0, t - 1.4) * 6) * (t > 1.4 ? 1 : 0);
    c.save(); c.translate(CX, 1082); c.scale(cp * pulse, cp * pulse);
    c.shadowColor = 'rgba(241,208,138,0.6)'; c.shadowBlur = 40;
    const g = c.createLinearGradient(0, -48, 0, 48); g.addColorStop(0, C.goldL); g.addColorStop(1, C.gold);
    rr(c, -350, -48, 700, 96, 48); c.fillStyle = g; c.fill(); c.shadowBlur = 0;
    txt(c, 'TESTE A PRÉVIA GRÁTIS', 0, 15, 42, { fam: 'Sora', w: 800, color: C.ink, ls: 1 });
    c.restore();
  }
  // domain types on
  const dom = 'whatbrandonthinks.com', n = Math.floor(clamp((t - 1.2) / .5) * dom.length);
  if (n > 0) { txt(c, dom.slice(0, n), CX, 1182, 48, { w: 700, color: '#fff', glow: 'rgba(139,185,255,0.7)', gb: 20 }); if (n < dom.length || Math.floor(t * 3) % 2) { c.save(); c.font = font(48, 700, 'SG'); const w = c.measureText(dom.slice(0, n)).width; c.restore(); if (n < dom.length) { c.fillStyle = C.cyan; c.fillRect(CX + w / 2 + 6, 1146, 4, 44); } } }
  const fo = E.out3(prog(t, 1.65, .4));
  txt(c, 'SIGA @WHATBRANDONTHINKSBRASIL', CX, 1236, 30, { w: 700, color: C.cyan, ls: 2, a: fo });
  // Brandon peeks in, gesturing towards the address
  const hin = E.outBack(prog(t, 1.0, .55), 1.5);
  const nod = Math.sin(clamp((t - 1.9) / .4) * Math.PI) * .06;
  drawHead(c, 870, lerp(2650, 1935, hin), .52, -.16 - nod, { glint: prog(t, 1.95, .5), rim: 'rgba(139,185,255,0.5)' });
  // pointer arc from Brandon to the domain
  const ar = E.io3(prog(t, 1.55, .35));
  if (ar > 0) { c.save(); c.globalAlpha = ar * .9; c.strokeStyle = C.cyan; c.lineWidth = 5; c.lineCap = 'round'; c.setLineDash([2, 14]);
    c.beginPath(); c.moveTo(790, 1440); c.quadraticCurveTo(900, 1320, lerp(790, 820, ar), lerp(1440, 1218, ar)); c.stroke(); c.restore(); }
  flash(c, (1 - prog(t, 0, .25)) * .7, '#e6f0ff');
}

// ---------- whip-pan composite between scenes ----------
const bufA = document.createElement('canvas'); bufA.width = W; bufA.height = H; const ca = bufA.getContext('2d');
const bufB = document.createElement('canvas'); bufB.width = W; bufB.height = H; const cb = bufB.getContext('2d');
function whip(c, t, at, from, to, dir) { // dir: [dx,dy]
  const d = .2; const p = (t - (at - d)) / (2 * d);
  ca.setTransform(1, 0, 0, 1, 0, 0); ca.clearRect(0, 0, W, H);
  const src = p < .5 ? from : to; src(ca, t);
  const e = p < .5 ? E.in3(p * 2) : 1 - E.out3((p - .5) * 2);
  const off = (p < .5 ? -1 : 1) * e * 1150;
  const n = 7;
  c.fillStyle = '#05070f'; c.fillRect(0, 0, W, H);
  for (let i = 0; i < n; i++) { const k = (i / (n - 1) - .5) * e * 160; c.globalAlpha = 1 / n * 1.6; c.drawImage(bufA, dir[0] * (off + k), dir[1] * (off + k)); }
  c.globalAlpha = 1;
}

// ---------- film grain + vignette ----------
const grain = []; for (let k = 0; k < 4; k++) { const g = document.createElement('canvas'); g.width = 540; g.height = 960; const gc = g.getContext('2d'); const id = gc.createImageData(540, 960); const R = rng(100 + k); for (let i = 0; i < id.data.length; i += 4) { const v = 128 + (R() - .5) * 90; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; } gc.putImageData(id, 0, 0); grain.push(g); }
function finish(c, t) {
  const v = c.createRadialGradient(CX, 960, 500, CX, 960, 1250); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.45)');
  c.fillStyle = v; c.fillRect(0, 0, W, H);
  c.save(); c.globalAlpha = .045; c.globalCompositeOperation = 'overlay'; c.drawImage(grain[Math.floor(t * 30) % 4], 0, 0, W, H); c.restore();
}

window.draw = function (t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.filter = 'none';
  if (t < 2.7) s1(ctx, t);
  else if (t < 5.6) s2(ctx, t);
  else if (t < 9.0) s3(ctx, t);
  else if (t < 11.6) s4(ctx, t);
  else if (t < 12.0) whip(ctx, t, 11.8, s4, s5, [1, 0]);
  else if (t < 14.7) s5(ctx, t);
  else if (t < 15.1) whip(ctx, t, 14.9, s5, s6, [0, 1]);
  else if (t < 18.0) s6(ctx, t);
  else if (t < 21.1) s7(ctx, t);
  else s8(ctx, Math.min(t, 24));
  finish(ctx, t);
};
window.ready = (async () => {
  await Promise.all([load('head', 'head.png'), load('char', 'char.png'), load('desk', 'desk.jpg'), load('logo', 'logo.jpg')]);
  await document.fonts.load('800 100px Sora'); await document.fonts.load('700 100px Sora'); await document.fonts.load('700 100px SG'); await document.fonts.load('600 100px SG'); await document.fonts.load('500 100px SG');
  return true;
})();
