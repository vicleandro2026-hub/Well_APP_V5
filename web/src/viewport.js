import { clamp, geometry, logoKey } from './engine.js';

export class Viewport {
  constructor(stage, canvas, onMove, onZoom) {
    this.stage = stage; this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.onMove = onMove; this.onZoom = onZoom;
    this.scale = 1; this.ox = 0; this.oy = 0; this.mode = 'logo';
    this.pointers = new Map(); this.space = false;
    this.observer = new ResizeObserver(() => this.resize());
    this.observer.observe(stage);
    stage.addEventListener('pointerdown', e => this.pointerDown(e));
    stage.addEventListener('pointermove', e => this.pointerMove(e));
    for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) stage.addEventListener(name, e => this.pointerEnd(e));
    stage.addEventListener('wheel', e => {
      if (!this.photo) return;
      e.preventDefault(); const p = this.point(e);
      this.zoom(Math.exp(-clamp(e.deltaY, -120, 120) * .002), p.x, p.y);
    }, { passive: false });
    stage.addEventListener('contextmenu', e => e.preventDefault());
    stage.addEventListener('keydown', e => this.keyDown(e));
    stage.addEventListener('keyup', e => { if (e.code === 'Space') { this.space = false; this.cursor(); } });
    window.addEventListener('blur', () => { this.space = false; this.pointerEnd(); });
  }
  resize() {
    const oldW = this.width || 0, oldH = this.height || 0;
    this.width = this.stage.clientWidth; this.height = this.stage.clientHeight;
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.canvas.width = Math.round(this.width * this.dpr);
    this.canvas.height = Math.round(this.height * this.dpr);
    if (this.photo && this.fitted) this.fit();
    else { this.ox += (this.width - oldW) / 2; this.oy += (this.height - oldH) / 2; this.constrain(); this.draw(); }
  }
  setPhoto(photo, bitmap) {
    this.photo = photo; this.bitmap = bitmap; this.pointerEnd();
    if (photo && bitmap) this.fit(); else { this.draw(); this.onZoom(null); }
    this.cursor();
  }
  update(settings, logos, original = false, locked = false) {
    this.settings = settings; this.logos = logos; this.original = original; this.locked = locked;
    this.cursor(); this.draw();
  }
  setMode(mode) { this.mode = mode; this.cursor(); this.draw(); }
  cursor() { this.stage.style.cursor = !this.photo ? 'default' : this.mode === 'pan' || this.space ? 'grab' : 'move'; }
  fit() {
    if (!this.photo) return;
    this.scale = Math.min((this.width - 44) / this.photo.width, (this.height - 44) / this.photo.height);
    this.scale = Math.max(.001, this.scale);
    this.ox = (this.width - this.photo.width * this.scale) / 2;
    this.oy = (this.height - this.photo.height * this.scale) / 2;
    this.fitted = true; this.onZoom(this.scale); this.draw();
  }
  actual() { if (this.photo) this.zoom(1 / this.scale); }
  zoom(factor, x = this.width / 2, y = this.height / 2) {
    if (!this.photo) return;
    const min = Math.min(.01, this.fitScale() / 2);
    const next = clamp(this.scale * factor, min, 8);
    this.ox = x - (x - this.ox) * next / this.scale;
    this.oy = y - (y - this.oy) * next / this.scale;
    this.scale = next; this.fitted = false;
    this.constrain(); this.onZoom(this.scale); this.draw();
  }
  fitScale() { return Math.max(.001, Math.min((this.width - 44) / this.photo.width, (this.height - 44) / this.photo.height)); }
  constrain() {
    if (!this.photo) return;
    const w = this.photo.width * this.scale, h = this.photo.height * this.scale;
    this.ox = clamp(this.ox, -w + Math.min(60, w / 2), this.width - Math.min(60, w / 2));
    this.oy = clamp(this.oy, -h + Math.min(60, h / 2), this.height - Math.min(60, h / 2));
  }
  draw() {
    if (this.frame) return;
    this.frame = requestAnimationFrame(() => { this.frame = null; this.paint(); });
  }
  paint() {
    const c = this.ctx; if (!c) return;
    c.setTransform(this.dpr, 0, 0, this.dpr, 0, 0); c.clearRect(0, 0, this.width, this.height);
    if (!this.photo || !this.bitmap || !this.settings) return;
    const w = this.photo.width * this.scale, h = this.photo.height * this.scale;
    c.save(); c.shadowColor = '#0009'; c.shadowBlur = 20; c.shadowOffsetY = 5;
    c.fillStyle = '#22251f'; c.fillRect(this.ox, this.oy, w, h); c.restore();
    c.imageSmoothingEnabled = true; c.imageSmoothingQuality = 'high';
    c.drawImage(this.bitmap, this.ox, this.oy, w, h);
    if (this.original || !this.logos) return;
    const b = geometry(this.photo, this.settings);
    const x = this.ox + b.x * this.scale, y = this.oy + b.y * this.scale;
    const bw = b.width * this.scale, bh = b.height * this.scale;
    c.globalAlpha = this.settings.opacity / 100;
    c.drawImage(this.logos[logoKey(this.photo)], x, y, bw, bh); c.globalAlpha = 1;
    if (this.mode !== 'logo' || this.locked || this.space) return;
    c.save(); c.strokeStyle = '#d3b578'; c.lineWidth = 1; c.setLineDash([4, 4]); c.strokeRect(x - 5, y - 5, bw + 10, bh + 10);
    c.setLineDash([]); c.fillStyle = '#d3b578';
    for (const [hx, hy] of [[x - 5, y - 5], [x + bw + 5, y - 5], [x - 5, y + bh + 5], [x + bw + 5, y + bh + 5]]) c.fillRect(hx - 2, hy - 2, 4, 4);
    c.restore();
  }
  point(e) { const r = this.stage.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; }
  pointerDown(e) {
    if (!this.photo || e.target !== this.canvas && e.target !== this.stage) return;
    e.preventDefault(); this.stage.focus({ preventScroll: true });
    const p = this.point(e); this.pointers.set(e.pointerId, p);
    this.stage.setPointerCapture(e.pointerId);
    if (this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      this.pinch = { distance: Math.hypot(a.x - b.x, a.y - b.y), center: { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 } };
      this.drag = null; return;
    }
    const box = geometry(this.photo, this.settings);
    const px = (p.x - this.ox) / this.scale, py = (p.y - this.oy) / this.scale;
    const hit = px >= box.x - 10 / this.scale && px <= box.x + box.width + 10 / this.scale && py >= box.y - 10 / this.scale && py <= box.y + box.height + 10 / this.scale;
    if (hit && this.mode === 'logo' && !this.space && !this.original && !this.locked && e.button === 0) {
      this.drag = { type: 'logo', dx: px - (box.x + box.width / 2), dy: py - (box.y + box.height / 2) };
    } else this.drag = { type: 'pan', x: p.x, y: p.y, ox: this.ox, oy: this.oy };
    this.stage.classList.add('is-dragging');
  }
  pointerMove(e) {
    if (!this.pointers.has(e.pointerId)) return;
    const p = this.point(e); this.pointers.set(e.pointerId, p);
    if (this.pinch && this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      const center = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
      const distance = Math.hypot(a.x - b.x, a.y - b.y);
      this.zoom(distance / Math.max(1, this.pinch.distance), this.pinch.center.x, this.pinch.center.y);
      this.ox += center.x - this.pinch.center.x; this.oy += center.y - this.pinch.center.y;
      this.pinch = { distance, center }; this.constrain(); this.draw(); return;
    }
    if (!this.drag) return;
    if (this.drag.type === 'pan') {
      this.ox = this.drag.ox + p.x - this.drag.x; this.oy = this.drag.oy + p.y - this.drag.y;
      this.fitted = false; this.constrain(); this.draw();
    } else {
      const box = geometry(this.photo, this.settings);
      const x = clamp((p.x - this.ox) / this.scale - this.drag.dx, box.width / 2, this.photo.width - box.width / 2);
      const y = clamp((p.y - this.oy) / this.scale - this.drag.dy, box.height / 2, this.photo.height - box.height / 2);
      this.onMove(x / this.photo.width, y / this.photo.height);
    }
  }
  pointerEnd(e) {
    if (e) this.pointers.delete(e.pointerId); else this.pointers.clear();
    this.drag = null; this.pinch = null; this.stage.classList.remove('is-dragging');
  }
  keyDown(e) {
    if (!this.photo || e.target !== this.stage) return;
    if (e.code === 'Space') { e.preventDefault(); this.space = true; this.cursor(); this.draw(); return; }
    if (e.key === 'Home') { e.preventDefault(); this.fit(); return; }
    if (e.key === '+' || e.key === '=') { e.preventDefault(); this.zoom(1.2); return; }
    if (e.key === '-') { e.preventDefault(); this.zoom(1 / 1.2); return; }
    const dirs = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
    if (!dirs[e.key]) return;
    e.preventDefault(); const [dx, dy] = dirs[e.key];
    if (this.mode === 'pan' || this.space) {
      const step = e.shiftKey ? 60 : 20; this.ox += dx * step; this.oy += dy * step;
      this.fitted = false; this.constrain(); this.draw();
    } else if (!this.original && !this.locked) {
      const b = geometry(this.photo, this.settings), step = e.shiftKey ? 10 : 1;
      this.onMove(clamp(b.x + b.width / 2 + dx * step, b.width / 2, this.photo.width - b.width / 2) / this.photo.width, clamp(b.y + b.height / 2 + dy * step, b.height / 2, this.photo.height - b.height / 2) / this.photo.height);
    }
  }
}
