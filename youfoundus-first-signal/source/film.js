// THE FIRST SIGNAL — Campaign Film 001 — deterministic frame renderer
'use strict';
const W = 1080, H = 1920, FPS = 30;
const VARIANT = new URLSearchParams(location.search).get('variant') || 'cta';
const PORCELAIN = '#F1F0ED', SILVER = '#A8ABB3';

// ---------- math ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const eOutExpo = k => k >= 1 ? 1 : 1 - Math.pow(2, -10 * k);
const eOutCubic = k => 1 - Math.pow(1 - k, 3);
const eInOutCubic = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
const eInCubic = k => k * k * k;
const eInOutSine = k => -(Math.cos(Math.PI * k) - 1) / 2;
const v3 = (x, y, z) => [x, y, z];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = a => mul(a, 1 / Math.hypot(...a));
// object rotation R = Ry(yaw) * Rx(pitch); returns rows of R
function objRot(yaw, pitch) {
  const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
  // R = [[cy, sy*sp, sy*cp],[0, cp, -sp],[-sy, cy*sp, cy*cp]]
  return [[cy, sy * sp, sy * cp], [0, cp, -sp], [-sy, cy * sp, cy * cp]];
}
const applyR = (R, v) => [dot(R[0], v), dot(R[1], v), dot(R[2], v)];
// uniform for world->local = R^T ; column-major => columns are rows of R^T = columns of R... careful:
// M = R^T. Column j of M = row j of R.
const RtUniform = R => new Float32Array([...R[0], ...R[1], ...R[2]]);
function lookAt(pos, target) {
  const f = norm(sub(target, pos)); const r = norm(cross(f, [0, 1, 0])); const u = cross(r, f);
  return { pos, f, r, u, m: new Float32Array([...r, ...u, ...f]) };
}
function project(cam, tanHalf, p) {
  const v = sub(p, cam.pos); const z = dot(v, cam.f);
  const x = dot(v, cam.r) / (z * tanHalf * (W / H)), y = dot(v, cam.u) / (z * tanHalf);
  return [(x * .5 + .5) * W, (1 - (y * .5 + .5)) * H]; // canvas coords (top origin)
}
// deterministic random
function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// ---------- typography ----------
const SERIF = 'Cormorant', SANS = 'Manrope';
const cache = new Map();
function glyphs(str, st) {
  const key = str + '|' + JSON.stringify(st);
  if (cache.has(key)) return cache.get(key);
  const c = document.createElement('canvas'), x = c.getContext('2d');
  const font = `${st.italic ? 'italic ' : ''}${st.weight} ${st.size}px ${st.family}`;
  x.font = font; x.letterSpacing = (st.track || 0) * st.size + 'px';
  const m = x.measureText(str);
  const ls = (st.track || 0) * st.size;
  const w = Math.ceil(m.width - ls), pad = Math.ceil(st.size * 0.35);
  const asc = Math.ceil(m.actualBoundingBoxAscent), desc = Math.ceil(m.actualBoundingBoxDescent);
  c.width = w + pad * 2; c.height = asc + desc + pad * 2;
  x.font = font; x.letterSpacing = ls + 'px'; x.fillStyle = st.color || PORCELAIN; x.textBaseline = 'alphabetic';
  x.fillText(str, pad, pad + asc);
  const g = { c, w, pad, asc, desc, h: c.height };
  cache.set(key, g); return g;
}
const scratch = document.createElement('canvas'); scratch.width = W; scratch.height = H;
const sx = scratch.getContext('2d');
// draw text with baseline at (x,y); align: 'left' | 'center'; mask: {type, k, soft}
function text(ctx, str, st, x, y, o = {}) {
  const g = glyphs(str, st);
  const alpha = o.alpha == null ? 1 : o.alpha; if (alpha <= 0.001) return;
  const s = o.scale || 1;
  const left = (o.align === 'center') ? -g.w / 2 : 0;
  let src = g.c;
  if (o.mask) {
    const m = o.mask; sx.setTransform(1, 0, 0, 1, 0, 0); sx.globalCompositeOperation = 'source-over';
    sx.clearRect(0, 0, g.c.width + 4, g.c.height + 4); sx.drawImage(g.c, 0, 0);
    sx.globalCompositeOperation = 'destination-in';
    const soft = m.soft || 40, cw = g.c.width, ch = g.c.height;
    let gr;
    if (m.type === 'wipe') { const e = lerp(-soft, cw + soft, m.k); gr = sx.createLinearGradient(e - soft, 0, e + soft * 0.2, 0); gr.addColorStop(0, '#fff'); gr.addColorStop(1, 'rgba(255,255,255,0)'); }
    else if (m.type === 'up') { const e = lerp(ch + soft, -soft, m.k); gr = sx.createLinearGradient(0, e - soft * 0.2, 0, e + soft); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(1, '#fff'); }
    else if (m.type === 'center') { const hw = lerp(0, cw / 2 + soft, m.k), c0 = cw / 2; gr = sx.createLinearGradient(c0 - hw - soft, 0, c0 + hw + soft, 0); const span = 2 * hw + 2 * soft; const a = soft / span; gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(clamp(a), '#fff'); gr.addColorStop(clamp(1 - a), '#fff'); gr.addColorStop(1, 'rgba(255,255,255,0)'); }
    else if (m.type === 'keepRight') { const e = m.x; gr = sx.createLinearGradient(e - soft * 0.3, 0, e + soft, 0); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(1, '#fff'); }
    sx.fillStyle = gr; sx.fillRect(0, 0, cw, ch);
    sx.globalCompositeOperation = 'source-over';
    src = scratch;
  }
  ctx.save();
  ctx.globalAlpha = alpha;
  if (o.blur) ctx.filter = `blur(${o.blur}px)`;
  ctx.translate(x, y); ctx.scale(s, s); if (o.dy) ctx.translate(0, o.dy);
  ctx.drawImage(src, 0, 0, g.c.width, g.c.height, left - g.pad, -g.asc - g.pad, g.c.width, g.c.height);
  ctx.restore();
  return g;
}
// sheen: draw a moving silver highlight clipped to the glyphs
function sheen(ctx, str, st, x, y, o, k) {
  const g = glyphs(str, st);
  const left = (o.align === 'center') ? -g.w / 2 : 0, s = o.scale || 1;
  sx.setTransform(1, 0, 0, 1, 0, 0); sx.clearRect(0, 0, g.c.width + 4, g.c.height + 4);
  sx.drawImage(g.c, 0, 0); sx.globalCompositeOperation = 'source-in';
  const cx = lerp(-g.c.width * 0.4, g.c.width * 1.4, k);
  const gr = sx.createLinearGradient(cx - 120, 0, cx + 120, g.c.height * 0.3);
  gr.addColorStop(0, 'rgba(168,171,179,0)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.95)'); gr.addColorStop(1, 'rgba(168,171,179,0)');
  sx.fillStyle = gr; sx.fillRect(0, 0, g.c.width, g.c.height); sx.globalCompositeOperation = 'source-over';
  ctx.save(); ctx.globalAlpha = o.alpha == null ? 1 : o.alpha; ctx.globalCompositeOperation = 'lighter';
  ctx.translate(x, y); ctx.scale(s, s);
  ctx.drawImage(scratch, 0, 0, g.c.width, g.c.height, left - g.pad, -g.asc - g.pad, g.c.width, g.c.height);
  ctx.restore();
}

// styles (sizes resolved after fonts load)
const ST = {};
function fitSize(str, st, maxW) { const g = glyphs(str, { ...st, size: 100 }); return Math.floor(100 * maxW / g.w); }
function defineStyles() {
  const head = { family: SERIF, weight: 400, track: 0.02, color: PORCELAIN };
  const sz = Math.min(150, fitSize('QUEM CRIE', head, 864), fitSize('AS MARCAS', head, 864));
  ST.head = { ...head, size: sz };
  ST.headIt = { family: SERIF, weight: 400, italic: true, track: 0.0, color: PORCELAIN, size: sz };
  ST.q1 = { family: SERIF, weight: 400, track: 0.10, color: PORCELAIN, size: 84 };
  ST.q1.size = Math.min(84, fitSize('E QUEM CRIA', ST.q1, 760));
  ST.por = { ...ST.q1 };
  ST.voce = { family: SERIF, weight: 300, italic: true, track: 0.0, color: PORCELAIN, size: 300 };
  ST.voce.size = Math.min(320, fitSize('VOCÊ?', ST.voce, 860));
  ST.yf = { family: SERIF, weight: 300, track: 0.02, color: PORCELAIN, size: 250 };
  ST.word = { family: SERIF, weight: 400, track: 0.34, color: PORCELAIN, size: 44 };
  ST.word.size = Math.min(44, fitSize('YOU FOUND US.', ST.word, 640));
  ST.access = { family: SERIF, weight: 400, track: 0.14, color: PORCELAIN, size: 64 };
  ST.access.size = Math.min(64, fitSize('ACESSO ANTECIPADO.', ST.access, 820));
  ST.handle = { family: SANS, weight: 300, track: 0.06, color: PORCELAIN, size: 32 };
  ST.bio = { family: SANS, weight: 400, track: 0.42, color: SILVER, size: 24 };
}

// ---------- layouts ----------
const X0 = 108;
const L = { y1: 690, y2: 690 + 0, y3: 0, y4: 0 };
function headLayout() {
  const lh = ST.head.size * 1.02;
  L.y1 = 660; L.y2 = L.y1 + lh; L.y3 = L.y2 + lh * 1.18; L.y4 = L.y3 + lh;
}
// question block (scene 03)
const Q = { y1: 735, y2: 880, y3: 1185 };
function qScale(t) { return 1 + 0.035 * eOutCubic(seg(t, 5.2, 6.8)); }

// ---------- particles for the dissolve & the monogram ----------
let parts = null;
function buildParticles() {
  const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d');
  drawQuestion(x, 6.8, null, true);
  const d = x.getImageData(0, 0, W, H).data;
  const src = [];
  for (let y = 0; y < H; y += 2) for (let xx = 0; xx < W; xx += 2) if (d[(y * W + xx) * 4 + 3] > 140) src.push([xx, y]);
  // monogram targets
  x.clearRect(0, 0, W, H); drawYF(x, 8.0, { alpha: 1, plain: true });
  const d2 = x.getImageData(0, 0, W, H).data; const tg = [];
  for (let y = 0; y < H; y += 2) for (let xx = 0; xx < W; xx += 2) if (d2[(y * W + xx) * 4 + 3] > 160) tg.push([xx, y]);
  const rnd = mulberry(7);
  const P = [];
  const NF = Math.min(2600, tg.length);
  for (let i = 0; i < src.length; i++) {
    const s = src[i];
    P.push({ x: s[0], y: s[1], vx: 25 + rnd() * 70, vy: -(10 + rnd() * 50), life: 0.35 + rnd() * 0.5, frag: false, r: rnd() });
  }
  // fragments: pick sources spread over text, map to monogram targets
  for (let i = 0; i < NF; i++) {
    const s = src[Math.floor(rnd() * src.length)], tgt = tg[Math.floor(rnd() * tg.length)];
    P.push({ x: s[0], y: s[1], vx: 20 + rnd() * 60, vy: -(10 + rnd() * 40), frag: true, tx: tgt[0], ty: tgt[1],
      delay: rnd() * 0.22, dur: 0.48 + rnd() * 0.22, curl: (rnd() - .5) * 520, a0: rnd() * 6.28, spin: (rnd() - .5) * 18, r: rnd() });
  }
  parts = P;
}
const sweepX = t => lerp(-40, 1120, eInOutSine(seg(t, 6.8, 7.3)));
const sweepTime = x => 6.8 + 0.5 * clamp((x + 40) / 1160); // approx inverse (good enough for spawn)

function drawQuestion(ctx, t, mask, plain) {
  const s = qScale(t);
  const cx = 540, cy = 960;
  const tf = (y) => cy + (y - cy) * s;
  text(ctx, 'E QUEM CRIA', ST.q1, cx, tf(Q.y1), { align: 'center', scale: s, mask });
  if (!plain) return;
  text(ctx, 'POR', ST.por, cx, tf(Q.y2), { align: 'center', scale: s, mask });
  text(ctx, 'VOCÊ?', ST.voce, cx, tf(Q.y3), { align: 'center', scale: s, mask });
}
function yfPose(t) {
  if (VARIANT === 'cta') {
    const k = eInOutCubic(seg(t, 9.2, 9.9));
    return { y: lerp(1015, 690, k), s: lerp(1, 0.46, k) };
  }
  const k = eInOutCubic(seg(t, 9.2, 9.9));
  return { y: lerp(1015, 950, k), s: lerp(1, 0.86, k) };
}
function drawYF(ctx, t, o) {
  const p = yfPose(t);
  text(ctx, 'YF.', ST.yf, 540, p.y, { align: 'center', scale: p.s, alpha: o.alpha });
  if (!o.plain && o.sheen != null) sheen(ctx, 'YF.', ST.yf, 540, p.y, { align: 'center', scale: p.s, alpha: o.alpha * 0.85 }, o.sheen);
}

// ---------- WebGL ----------
const cv = document.getElementById('gl');
const gl = cv.getContext('webgl2', { antialias: false, preserveDrawingBuffer: true, premultipliedAlpha: false });
gl.getExtension('EXT_color_buffer_float'); gl.getExtension('OES_texture_float_linear');
function prog(fsId) {
  const mk = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src.trim()); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
  const p = gl.createProgram();
  gl.attachShader(p, mk(gl.VERTEX_SHADER, document.getElementById('vsrc').textContent));
  gl.attachShader(p, mk(gl.FRAGMENT_SHADER, document.getElementById(fsId).textContent));
  gl.bindAttribLocation(p, 0, 'aPos'); gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
  const u = {}; const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
  for (let i = 0; i < n; i++) { const a = gl.getActiveUniform(p, i); u[a.name.replace('[0]', '')] = gl.getUniformLocation(p, a.name); }
  return { p, u };
}
let PA, PB, sceneTex, fbo, frontTex, backTex, front, back, fctx, bctx;
function initGL() {
  PA = prog('fsScene'); PB = prog('fsComp');
  const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  sceneTex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, sceneTex);
  const levels = Math.floor(Math.log2(Math.max(W, H))) + 1;
  gl.texStorage2D(gl.TEXTURE_2D, levels, gl.RGBA16F, W, H);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  fbo = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, sceneTex, 0);
  if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) throw new Error('fbo incomplete');
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  const mkT = () => { const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE); return t; };
  frontTex = mkT(); backTex = mkT();
  front = document.createElement('canvas'); front.width = W; front.height = H; fctx = front.getContext('2d');
  back = document.createElement('canvas'); back.width = W; back.height = H; bctx = back.getContext('2d');
}

// ---------- the timeline ----------
function sceneState(t) {
  const S = {
    gap: 0, splitRot: 0, fissure: 0, fissureGlow: 0, beamY: 2, beam: 0, frames: 0, light: 0, inner: 0, tendril: 0,
    focus: 6, aperture: 0.5, exposure: 1, glassX: 2000, glass: 0, beam2D: [0, 0, 0, 0], sweep: [0, 0, 60, 0], shaft: [540, 10, 0, 0],
    haze: 1, dust: 0, ring: 0, textGlow: 0.5, backOcc: 1, grain: 2.2, fade: 1, frontRefr: 0,
    yaw: 0.5, pitch: 0, camPos: [0, 0, 6.4], camTgt: [0, 0, 0], tanHalf: 0.268,
  };
  if (t < 1.5) {                                   // CENA 01 — macro, first interruption
    S.yaw = 0.62 - 0.04 * t; S.pitch = -0.06;
    const R = objRot(S.yaw, S.pitch);
    const tgt = applyR(R, [0.27, 0.70, 0.09]);
    const dir = norm(applyR(R, [0.55, -0.35, 1.0]));
    const dist = lerp(1.05, 0.40, eOutExpo(seg(t, 0, 0.75))) - 0.04 * seg(t, 0.75, 1.5);
    S.camPos = add(tgt, add(mul(dir, dist), [0.04 * t, 0, 0])); S.camTgt = add(tgt, [0, -0.02 * t, 0]);
    S.tanHalf = 0.30; S.light = 1.0;
    S.focus = dist; S.aperture = 5.0;
    S.beam = 1.0 - 0.5 * seg(t, 0.8, 1.5); S.beamY = lerp(1.3, -1.1, eOutCubic(seg(t, 0.02, 1.4)));
    const bk = eOutCubic(seg(t, 0.0, 0.5));
    S.beam2D = [H - 772, lerp(-60, 1200, bk), lerp(200, 1300, bk), 1.0 - seg(t, 0.45, 1.0)];
    S.exposure = 1.0; S.haze = 0.8; S.textGlow = 0.6;
  } else if (t < 3.8) {                            // CENA 02 — the world of brands
    const k = seg(t, 1.5, 3.8);
    S.yaw = lerp(0.40, 0.95, eInOutSine(k)); S.pitch = -0.04;
    S.camTgt = [0.0, lerp(0.25, -0.15, k), 0];
    S.camPos = [lerp(0.55, 0.15, k), lerp(0.35, -0.05, k), lerp(1.55, 1.35, k)];
    S.tanHalf = 0.34; S.light = 1.0 - 0.9 * eInCubic(seg(t, 3.2, 3.78));
    S.focus = Math.hypot(...sub(S.camPos, S.camTgt)) - 0.1; S.aperture = 3.0;
    S.frames = seg(t, 1.5, 1.8) * (1 - seg(t, 3.1, 3.5)); S.beam = 0.15; S.beamY = lerp(0.3, -0.5, k);
    S.exposure = 0.72; S.ring = seg(t, 1.6, 2.0) * (1 - seg(t, 2.6, 3.0));
    const gk = seg(t, 2.70, 3.30);
    S.glass = Math.sin(Math.PI * gk) > 0 ? Math.min(1, Math.sin(Math.PI * gk) * 2.2) : 0;
    S.glassX = lerp(1450, -500, eInOutSine(gk)); S.frontRefr = 1;
    S.textGlow = 0.4;
  } else if (t < 6.8) {                            // CENA 03 — the rupture
    S.yaw = lerp(0.36, 0.22, seg(t, 3.8, 6.8)); S.pitch = 0.02;
    const push = eOutCubic(seg(t, 5.2, 6.8));
    const D = lerp(6.4, 5.6, push) - 0.12 * seg(t, 3.9, 5.2);
    S.camPos = [0, 0.02, D]; S.camTgt = [0, 0.02, 0]; S.tanHalf = 0.268;
    S.light = t < 3.95 ? 0 : eInOutSine(seg(t, 3.95, 4.55));
    S.beam = seg(t, 3.95, 4.2) * (1 - seg(t, 4.6, 5.0)) * 0.9; S.beamY = lerp(0.8, -0.6, seg(t, 3.95, 4.9));
    S.fissure = eInOutCubic(seg(t, 4.25, 4.70)); S.fissureGlow = seg(t, 4.22, 4.30) * (1 - seg(t, 5.2, 5.35));
    const g1 = 0.032 * eInCubic(seg(t, 4.72, 5.18));
    const g2 = 1.75 * eOutExpo(seg(t, 5.2, 6.6));
    S.gap = t < 5.2 ? g1 : g1 + g2 * 1.0;
    S.splitRot = 0.62 * eOutExpo(seg(t, 5.2, 6.6));
    S.tendril = t < 5.45 ? 1 : 0;
    S.inner = seg(t, 4.72, 5.15) * 0.7 + (t >= 5.2 ? 1.6 * Math.exp(-(t - 5.2) / 0.22) : 0);
    const shaftI = seg(t, 4.75, 5.15) * 0.45 * (t < 5.2 ? 1 : 0) + (t >= 5.2 ? 0.9 * Math.exp(-(t - 5.2) / 0.14) + 0.03 * (1 - seg(t, 5.6, 6.8)) : 0);
    const cam = lookAt(S.camPos, S.camTgt);
    const cpx = project(cam, S.tanHalf, [0, 0, 0]);
    S.shaft = [cpx[0], t < 5.2 ? 3 + 8 * seg(t, 4.75, 5.15) : 10 + 90 * eOutExpo(seg(t, 5.2, 6.0)), shaftI, 0];
    S.focus = D; S.aperture = 0.6; S.exposure = 1.0;
    S.textGlow = 0.5 + (t >= 5.2 ? 1.2 * Math.exp(-(t - 5.2) / 0.35) : 0);
    S.haze = 1.0; S.dust = seg(t, 4.0, 4.6) * 0.6;
    S.fade = t < 3.8 ? 0 : 1;
  } else {                                          // CENAS 04/05 — brand & invitation
    S.light = 0; S.haze = 1.0 - 0.35 * seg(t, 9.2, 10.0); S.dust = 0.5 * (1 - seg(t, 9.0, 10.0));
    const sk = seg(t, 6.78, 7.32);
    S.sweep = [sweepX(t), Math.sin(Math.PI * sk) * 1.1, 70, 0];
    S.textGlow = 0.45;
    // the signal returns
    if (t > 9.95) {
      const bk = eOutCubic(seg(t, 10.0, 10.55));
      const contract = eInOutCubic(seg(t, 10.45, 10.95));
      const y = VARIANT === 'cta' ? 1062 : 1110;
      const head = lerp(-60, 1200, bk);
      S.beam2D = [H - y, lerp(head, 588, contract), lerp(lerp(200, 1300, bk), 96, contract), lerp(1.0, 0.26, contract)];
    }
  }
  return S;
}

function drawTypography(t) {
  const F = fctx, B = bctx;
  F.clearRect(0, 0, W, H); B.clearRect(0, 0, W, H);
  if (t < 3.8) {
    // CENA 01/02 — headline
    const drift = -18 * seg(t, 1.5, 3.8);
    const s = 1 + 0.025 * seg(t, 1.5, 3.8);
    const T = (y) => 960 + (y - 960 + drift) * s;
    const bx = lerp(-60, 1200, eOutCubic(seg(t, 0.0, 0.5)));
    const wipeK = clamp((bx - X0 + 30) / 900);
    const out = eInOutSine(seg(t, 3.22, 3.58));
    const outO = { alpha: 1 - out, blur: out * 7 };
    const mask = wipeK < 1 ? { type: 'wipe', k: wipeK, soft: 70 } : null;
    text(F, 'AS MARCAS', ST.head, X0, T(L.y1), { scale: s, mask, ...outO });
    text(F, 'JÁ TÊM', ST.head, X0, T(L.y2), { scale: s, mask, ...outO });
    // phrase completes
    const k3 = eOutExpo(seg(t, 1.50, 2.05)), k4 = eOutExpo(seg(t, 1.72, 2.30));
    if (t >= 1.5) {
      text(F, 'QUEM CRIE', ST.head, X0, T(L.y3), { scale: s, mask: { type: 'up', k: k3, soft: 50 }, dy: 26 * (1 - k3), ...outO });
      const gp = glyphs('POR ', ST.headIt);
      text(F, 'POR', ST.headIt, X0, T(L.y4), { scale: s, mask: { type: 'up', k: k4, soft: 50 }, dy: 26 * (1 - k4), ...outO });
      text(F, 'ELAS.', ST.headIt, X0 + (gp.w + ST.headIt.size * 0.22) * s, T(L.y4), { scale: s, mask: { type: 'up', k: k4, soft: 50 }, dy: 26 * (1 - k4) });
    }
    return;
  }
  if (t < 6.8) {
    // CENA 03 — the question, born from the fissure / revealed behind the sculpture
    const k1 = eOutCubic(seg(t, 4.66, 5.08));
    if (t >= 4.66) drawQuestion(F, t, k1 < 1 ? { type: 'center', k: k1, soft: 60 } : null, false);
    if (t >= 5.2) {
      const s = qScale(t), kv = eOutExpo(seg(t, 5.2, 5.9));
      const vs = s * (1.07 - 0.07 * kv);
      text(B, 'POR', ST.por, 540, 960 + (Q.y2 - 960) * s, { align: 'center', scale: s, alpha: seg(t, 5.2, 5.32) });
      text(B, 'VOCÊ?', ST.voce, 540, 960 + (Q.y3 - 960) * s, { align: 'center', scale: vs, alpha: seg(t, 5.2, 5.28) });
    }
    return;
  }
  // CENA 04 — dissolve into light, fragments become the monogram
  if (t < 7.4) {
    const xs = sweepX(t);
    const g = document.createElement('canvas');
    // draw question frozen at 6.8, keeping only what the sweep hasn't touched
    const tmp = getTmp(); tmp.x.clearRect(0, 0, W, H); drawQuestion(tmp.x, 6.8, null, true);
    F.save(); F.drawImage(tmp.c, 0, 0);
    F.globalCompositeOperation = 'destination-in';
    const gr = F.createLinearGradient(xs - 10, 0, xs + 40, 0); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(1, '#fff');
    F.fillStyle = gr; F.fillRect(0, 0, W, H); F.restore();
  }
  // particles
  if (t >= 6.8 && t < 8.3) {
    F.save(); F.globalCompositeOperation = 'lighter';
    const xs = sweepX(t);
    for (const p of parts) {
      if (p.x > xs) continue;
      const t0 = sweepTime(p.x); const a = t - t0; if (a < 0) continue;
      if (!p.frag) {
        if (a > p.life) continue;
        const life = a / p.life;
        const x = p.x + p.vx * a, y = p.y + p.vy * a;
        F.globalAlpha = (1 - life) * 0.75; F.fillStyle = life < 0.3 ? PORCELAIN : SILVER;
        const r = 1.6 * (1 - life * 0.6); F.fillRect(x - r / 2, y - r / 2, r, r);
      } else {
        const tStart = 7.22 + p.delay; const fk = clamp((t - tStart) / p.dur);
        const ak = Math.min(a, tStart - t0);
        const x0 = p.x + p.vx * ak, y0 = p.y + p.vy * ak;
        const e = eInOutCubic(fk);
        const mx = (x0 + p.tx) / 2, my = (y0 + p.ty) / 2;
        const dx = p.tx - x0, dy = p.ty - y0, dl = Math.hypot(dx, dy) + 1e-3;
        const cx = mx - dy / dl * p.curl, cy = my + dx / dl * p.curl;
        const x = (1 - e) * (1 - e) * x0 + 2 * (1 - e) * e * cx + e * e * p.tx;
        const y = (1 - e) * (1 - e) * y0 + 2 * (1 - e) * e * cy + e * e * p.ty;
        const ang = p.a0 + p.spin * (1 - Math.pow(1 - fk, 3)) * 0.4 + p.spin * 0.05 * a;
        const glint = 0.5 + 0.5 * Math.pow(Math.abs(Math.cos(ang * 2 + p.r * 6)), 10);
        const settle = seg(t, 7.85, 8.25);
        const len = lerp(7, 2.2, e), wid = 1.3;
        F.globalAlpha = (0.55 + 0.45 * glint) * (1 - settle) * clamp(a / 0.08);
        F.fillStyle = glint > 0.85 ? '#ffffff' : (p.r > 0.5 ? SILVER : '#cfd1d6');
        F.save(); F.translate(x, y); F.rotate(ang * (1 - e) + 0.0); F.fillRect(-len / 2, -wid / 2, len, wid); F.restore();
      }
    }
    F.restore();
  }
  // monogram resolves
  const yfA = eInOutSine(seg(t, 7.78, 8.10));
  if (yfA > 0) drawYF(F, t, { alpha: yfA, sheen: (t > 7.85 && t < 8.6) ? seg(t, 7.85, 8.6) : null });
  // wordmark
  if (t >= 8.3) {
    const kw = eOutCubic(seg(t, 8.3, 8.8));
    const outW = VARIANT === 'cta' ? eInOutSine(seg(t, 9.2, 9.5)) : 0;
    const p = yfPose(t);
    const wy = VARIANT === 'cta' ? 1120 : lerp(1120, 1028, eInOutCubic(seg(t, 9.2, 9.9)));
    text(F, 'YOU FOUND US.', ST.word, 540, wy, { align: 'center', mask: kw < 1 ? { type: 'center', k: kw, soft: 80 } : null, alpha: 1 - outW, blur: outW * 4 });
  }
  if (t >= 9.6) {
    if (VARIANT === 'cta') {
      const ka = eOutCubic(seg(t, 9.72, 10.35));
      text(F, 'ACESSO ANTECIPADO.', ST.access, 540, 992 + 10 * (1 - ka), { align: 'center', mask: ka < 1 ? { type: 'wipe', k: ka, soft: 120 } : null });
      const kh = eOutCubic(seg(t, 10.5, 10.95)), kb = eOutCubic(seg(t, 10.62, 11.05));
      text(F, '@youfoundus.dl', ST.handle, 540, 1146 + 6 * (1 - kh), { align: 'center', mask: kh < 1 ? { type: 'up', k: kh, soft: 30 } : null });
      text(F, 'LINK NA BIO', ST.bio, 540, 1206 + 6 * (1 - kb), { align: 'center', mask: kb < 1 ? { type: 'up', k: kb, soft: 24 } : null });
    } else {
      const kh = eOutCubic(seg(t, 10.5, 10.95));
      text(F, '@youfoundus.dl', ST.handle, 540, 1190 + 6 * (1 - kh), { align: 'center', mask: kh < 1 ? { type: 'up', k: kh, soft: 30 } : null });
    }
  }
}
let _tmp = null;
function getTmp() { if (!_tmp) { const c = document.createElement('canvas'); c.width = W; c.height = H; _tmp = { c, x: c.getContext('2d') }; } return _tmp; }

function upload(tex, canvas) {
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, canvas);
  gl.generateMipmap(gl.TEXTURE_2D);
}

function renderFrame(t) {
  const S = sceneState(t);
  drawTypography(t);
  const cam = lookAt(S.camPos, S.camTgt);
  const R = objRot(S.yaw, S.pitch);
  // PASS A
  gl.bindFramebuffer(gl.FRAMEBUFFER, fbo); gl.viewport(0, 0, W, H);
  gl.useProgram(PA.p); const a = PA.u;
  gl.uniform2f(a.uRes, W, H); gl.uniform3fv(a.uCamPos, S.camPos); gl.uniformMatrix3fv(a.uCamMat, false, cam.m);
  gl.uniform1f(a.uTanHalf, S.tanHalf); gl.uniformMatrix3fv(a.uObjRot, false, RtUniform(R)); gl.uniform3f(a.uObjPos, 0, 0, 0);
  gl.uniform1f(a.uGap, S.gap); gl.uniform1f(a.uSplitRot, S.splitRot); gl.uniform1f(a.uFissure, S.fissure); gl.uniform1f(a.uFissureGlow, S.fissureGlow);
  gl.uniform1f(a.uBeamY, S.beamY); gl.uniform1f(a.uBeam, S.beam); gl.uniform1f(a.uFrames, S.frames); gl.uniform1f(a.uTime, t);
  gl.uniform1f(a.uLight, S.light); gl.uniform1f(a.uInner, S.inner); gl.uniform1f(a.uTendril, S.tendril);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  gl.bindTexture(gl.TEXTURE_2D, sceneTex); gl.generateMipmap(gl.TEXTURE_2D);
  upload(frontTex, front); upload(backTex, back);
  // PASS B
  gl.viewport(0, 0, W, H); gl.useProgram(PB.p); const b = PB.u;
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, sceneTex); gl.uniform1i(b.uScene, 0);
  gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, frontTex); gl.uniform1i(b.uFront, 1);
  gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, backTex); gl.uniform1i(b.uBack, 2);
  gl.activeTexture(gl.TEXTURE0);
  gl.uniform2f(b.uRes, W, H); gl.uniform1f(b.uTime, t); gl.uniform1f(b.uFocus, S.focus); gl.uniform1f(b.uAperture, S.aperture);
  gl.uniform1f(b.uExposure, S.exposure); gl.uniform1f(b.uGlassX, S.glassX); gl.uniform1f(b.uGlass, S.glass);
  gl.uniform4fv(b.uBeam2D, S.beam2D); gl.uniform4fv(b.uSweep, S.sweep); gl.uniform4fv(b.uShaft, [S.shaft[0], S.shaft[1], S.shaft[2], 0]);
  gl.uniform1f(b.uHaze, S.haze); gl.uniform1f(b.uDust, S.dust); gl.uniform1f(b.uRing, S.ring); gl.uniform1f(b.uTextGlow, S.textGlow);
  gl.uniform1f(b.uBackOcc, S.backOcc); gl.uniform1f(b.uGrain, S.grain); gl.uniform1f(b.uFade, S.fade); gl.uniform1f(b.uFrontRefr, S.frontRefr);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  gl.finish();
}

async function boot() {
  const faces = [
    new FontFace(SERIF, 'url(fonts/CormorantGaramond.ttf)', { weight: '300 700', style: 'normal' }),
    new FontFace(SERIF, 'url(fonts/CormorantGaramond-Italic.ttf)', { weight: '300 700', style: 'italic' }),
    new FontFace(SANS, 'url(fonts/Manrope.ttf)', { weight: '200 800', style: 'normal' }),
  ];
  for (const f of faces) { await f.load(); document.fonts.add(f); }
  await document.fonts.ready;
  defineStyles(); headLayout(); initGL(); buildParticles();
  window.renderFrame = renderFrame; window.FILM = { W, H, FPS, ST, nParts: parts.length };
  window.READY = true;
}
boot().catch(e => { window.BOOT_ERROR = String(e && e.stack || e); });
