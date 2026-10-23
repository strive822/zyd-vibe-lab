'use strict';

/**
 * 生成 Windows 快捷方式用的图标：把 public/favicon.svg 渲染成 256×256 PNG，
 * 再包成 ICO（PNG 压缩格式，Vista 以上支持），输出 assets/app.ico。
 *
 * 用法：node tools/make-icon.js
 */

const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 9444;
const SIZE = 256;
const TMP_HTML = path.join(ROOT, 'shots', '_icon.html');
const OUT_ICO = path.join(ROOT, 'assets', 'app.ico');
const OUT_PNG = path.join(ROOT, 'shots', 'icon-256.png');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    this.waiters = new Map();
    ws.addEventListener('message', (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(msg.error.message));
        else resolve(msg.result);
        return;
      }
      if (msg.method && this.waiters.has(msg.method)) {
        const list = this.waiters.get(msg.method);
        this.waiters.delete(msg.method);
        for (const fn of list) fn(msg.params);
      }
    });
  }

  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  once(method) {
    return new Promise((resolve) => {
      const list = this.waiters.get(method) || [];
      this.waiters.set(method, [...list, resolve]);
    });
  }
}

async function openTarget() {
  for (let i = 0; i < 60; i += 1) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const list = await res.json();
      const page = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
      if (page) return page;
    } catch (_) { /* 还没起来 */ }
    await sleep(200);
  }
  throw new Error('连不上 Chrome 调试端口');
}

function wrapIco(pngBuffer) {
  const header = Buffer.alloc(6);
  header.writeUInt16LE(0, 0); // reserved
  header.writeUInt16LE(1, 2); // type = icon
  header.writeUInt16LE(1, 4); // 一张图

  const entry = Buffer.alloc(16);
  entry.writeUInt8(0, 0); // 0 表示 256
  entry.writeUInt8(0, 1);
  entry.writeUInt8(0, 2);
  entry.writeUInt8(0, 3);
  entry.writeUInt16LE(1, 4); // planes
  entry.writeUInt16LE(32, 6); // bpp
  entry.writeUInt32LE(pngBuffer.length, 8);
  entry.writeUInt32LE(22, 12); // 6 + 16

  return Buffer.concat([header, entry, pngBuffer]);
}

(async () => {
  const svg = fs.readFileSync(path.join(ROOT, 'public', 'favicon.svg'), 'utf8')
    .replace(/width="\d+"/, `width="${SIZE}"`)
    .replace(/height="\d+"/, `height="${SIZE}"`);

  fs.mkdirSync(path.dirname(TMP_HTML), { recursive: true });
  fs.writeFileSync(
    TMP_HTML,
    `<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:transparent}` +
    `svg{display:block;width:${SIZE}px;height:${SIZE}px}</style>${svg}`,
    'utf8'
  );

  const chrome = spawn(CHROME, [
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--no-first-run',
    '--no-default-browser-check',
    `--user-data-dir=${path.join(ROOT, 'shots', '.icon-profile')}`,
    `--remote-debugging-port=${PORT}`,
    'about:blank',
  ], { stdio: 'ignore' });

  try {
    const target = await openTarget();
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.addEventListener('open', resolve);
      ws.addEventListener('error', () => reject(new Error('WebSocket 连接失败')));
    });
    const cdp = new Cdp(ws);

    await cdp.send('Page.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride', {
      width: SIZE,
      height: SIZE,
      deviceScaleFactor: 1,
      mobile: false,
    });
    // 透明底，快捷方式图标才不会带一块白方块
    await cdp.send('Emulation.setDefaultBackgroundColorOverride', {
      color: { r: 0, g: 0, b: 0, a: 0 },
    });

    const loaded = cdp.once('Page.loadEventFired');
    await cdp.send('Page.navigate', { url: 'file:///' + TMP_HTML.replace(/\\/g, '/') });
    await loaded;
    await sleep(400);

    const shot = await cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: true });
    const png = Buffer.from(shot.data, 'base64');

    fs.mkdirSync(path.dirname(OUT_ICO), { recursive: true });
    fs.writeFileSync(OUT_PNG, png);
    fs.writeFileSync(OUT_ICO, wrapIco(png));

    console.log(`PNG ${OUT_PNG} (${Math.round(png.length / 1024)} KB)`);
    console.log(`ICO ${OUT_ICO} (${Math.round(fs.statSync(OUT_ICO).size / 1024)} KB)`);
  } finally {
    chrome.kill();
    try { fs.unlinkSync(TMP_HTML); } catch (_) { /* 已删除 */ }
    fs.rmSync(path.join(ROOT, 'shots', '.icon-profile'), { recursive: true, force: true });
  }
})();
