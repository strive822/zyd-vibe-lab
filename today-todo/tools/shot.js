'use strict';

/**
 * 真实设备尺寸截图 + 布局体检。
 * 为什么不用 chrome --window-size：headless 在 Windows 上会把窗口宽度限制在约 500px，
 * 页面按 512px 布局、截图却裁成 390px，看起来像「右侧被裁掉」，其实是量错了。
 * 这里用 CDP 的 Emulation.setDeviceMetricsOverride 覆盖视口，才是手机真实尺寸。
 *
 * 用法：
 *   node tools/shot.js --w=390 --h=844 --out=shots/mobile.png --mobile
 *   node tools/shot.js --w=1440 --h=900 --out=shots/desktop.png
 */

const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 9333;
// 浏览器调试配置放到系统临时目录，避免落进项目被打包
const PROFILE = path.join(os.tmpdir(), 'today-todo-cdp');

const args = Object.fromEntries(
  process.argv.slice(2).map((raw) => {
    const [key, ...rest] = raw.replace(/^--/, '').split('=');
    return [key, rest.length ? rest.join('=') : true];
  })
);

const url = args.url || 'http://127.0.0.1:3000/';
const width = Number(args.w || 390);
const height = Number(args.h || 844);
const mobile = Boolean(args.mobile);
const dpr = Number(args.dpr || (mobile ? 2 : 1));
const out = args.out ? path.resolve(args.out) : null;
const waitMs = Number(args.wait || 1500);
const evalCode = typeof args.eval === 'string' ? args.eval : null;
const tabCount = Number(args.tab || 0);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const MEASURE = `(() => {
  const doc = document.documentElement;
  const limit = doc.clientWidth;
  const offenders = [...document.querySelectorAll('body *')]
    .filter((el) => !el.classList.contains('sr-only'))
    .map((el) => {
      const r = el.getBoundingClientRect();
      return {
        tag: el.tagName.toLowerCase(),
        cls: typeof el.className === 'string' ? el.className : '',
        id: el.id || '',
        left: Math.round(r.left),
        right: Math.round(r.right),
        width: Math.round(r.width),
      };
    })
    .filter((x) => x.right > limit + 0.5 || x.left < -0.5)
    .slice(0, 12);

    const items = document.querySelectorAll('.task').length;
  const active = document.activeElement;
  return JSON.stringify({
    clientWidth: doc.clientWidth,
    clientHeight: doc.clientHeight,
    scrollWidth: doc.scrollWidth,
    scrollHeight: doc.scrollHeight,
    overflowX: doc.scrollWidth > doc.clientWidth,
    dpr: window.devicePixelRatio,
    items,
    countText: (document.getElementById('count') || {}).textContent || null,
    focus: active ? (active.id || active.className || active.tagName) : null,
    focusOutline: active ? getComputedStyle(active).outlineWidth + ' ' + getComputedStyle(active).outlineStyle : null,
    offenders,
  });
})()`;

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.nextId = 0;
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
    const id = ++this.nextId;
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

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    ws.addEventListener('open', () => resolve(new Cdp(ws)));
    ws.addEventListener('error', () => reject(new Error('WebSocket 连接失败')));
  });
}

(async () => {
  fs.mkdirSync(PROFILE, { recursive: true });

  const chrome = spawn(CHROME, [
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--no-first-run',
    '--no-default-browser-check',
    '--force-color-profile=srgb',
    `--user-data-dir=${PROFILE}`,
    `--remote-debugging-port=${PORT}`,
    'about:blank',
  ], { stdio: 'ignore' });

  try {
    const target = await openTarget();
    const cdp = await connect(target.webSocketDebuggerUrl);

    await cdp.send('Page.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride', {
      width,
      height,
      deviceScaleFactor: dpr,
      mobile,
    });
    if (mobile) {
      await cdp.send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
    }

    const loaded = cdp.once('Page.loadEventFired');
    await cdp.send('Page.navigate', { url });
    await loaded;
    await sleep(waitMs);

    // 在页面里跑一段脚本，用来切到撤销条、焦点、空状态等真实交互态
    if (evalCode) {
      const result = await cdp.send('Runtime.evaluate', {
        expression: evalCode,
        awaitPromise: true,
        returnByValue: true,
      });
      if (result.result && result.result.value !== undefined) {
        console.log('eval →', JSON.stringify(result.result.value));
      }
      await sleep(400);
    }

    // 真实键盘 Tab 走查，焦点环只有在键盘模态下才是 :focus-visible
    for (let i = 0; i < tabCount; i += 1) {
      for (const type of ['keyDown', 'keyUp']) {
        await cdp.send('Input.dispatchKeyEvent', {
          type,
          key: 'Tab',
          code: 'Tab',
          windowsVirtualKeyCode: 9,
          nativeVirtualKeyCode: 9,
        });
      }
      await sleep(80);
    }
    if (tabCount > 0) await sleep(250);

    // 页面加载完成后切断网络，验证断连提示与重试路径（真实网络层，不是改代码）
    if (args.offline) {
      await cdp.send('Network.enable');
      await cdp.send('Network.emulateNetworkConditions', {
        offline: true,
        latency: 0,
        downloadThroughput: 0,
        uploadThroughput: 0,
      });
      await sleep(Number(args.offline) || 5000);
    }

    const measured = JSON.parse((await cdp.send('Runtime.evaluate', {
      expression: MEASURE,
      returnByValue: true,
    })).result.value);

    console.log(`视口 ${measured.clientWidth}×${measured.clientHeight}  dpr=${measured.dpr}  任务数=${measured.items}  计数=${measured.countText}`);
    console.log(`焦点=${measured.focus || '无'}  轮廓=${measured.focusOutline || '无'}`);
    console.log(measured.overflowX ? '横向溢出：有' : '横向溢出：无');
    if (measured.offenders.length) {
      console.log('越界元素：');
      for (const o of measured.offenders) {
        console.log(`  ${o.tag}${o.id ? '#' + o.id : ''}${o.cls ? '.' + o.cls.replace(/\s+/g, '.') : ''}  left=${o.left} right=${o.right} width=${o.width}`);
      }
    }

    if (out) {
      const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
      fs.mkdirSync(path.dirname(out), { recursive: true });
      fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
      console.log(`截图 ${out} (${Math.round(fs.statSync(out).size / 1024)} KB)`);
    }

    process.exitCode = measured.overflowX ? 1 : 0;
    chrome.kill();
  } catch (err) {
    console.error('失败：', err.message);
    process.exitCode = 2;
    chrome.kill();
  }
})();
