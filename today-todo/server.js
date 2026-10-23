'use strict';

/**
 * 今日待办 · 本地服务
 * 零依赖：只用 Node 内置模块。职责：静态托管、任务 API、局域网地址提示、端口回退。
 */

const http = require('node:http');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');

const ROOT = __dirname;
const PUBLIC_DIR = path.join(ROOT, 'public');
const DATA_FILE = process.env.DATA_FILE
  ? path.resolve(process.env.DATA_FILE)
  : path.join(ROOT, 'data', 'todos.json');
const BASE_PORT = Number.parseInt(process.env.PORT || '3000', 10);
const PORT_TRIES = 5;
// 任务长度不设上限；这里只是请求体的基础设施上限（1 MB），不是产品限制。
const MAX_BODY = 1024 * 1024;
const STALE_TMP_MS = 10 * 60 * 1000;

// 已完成任务在多久没有再次操作后自动清理。测试里可以传小数（如 0.0003 ≈ 1 秒）。
const DONE_TTL_HOURS_RAW = Number.parseFloat(process.env.DONE_TTL_HOURS || '24');
const DONE_TTL_HOURS = Number.isFinite(DONE_TTL_HOURS_RAW) && DONE_TTL_HOURS_RAW >= 0
  ? DONE_TTL_HOURS_RAW
  : 24;
const DONE_TTL_MS = DONE_TTL_HOURS * 60 * 60 * 1000;

const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.svg', 'image/svg+xml'],
  ['.ico', 'image/x-icon'],
  ['.png', 'image/png'],
  ['.webmanifest', 'application/manifest+json'],
  ['.txt', 'text/plain; charset=utf-8'],
]);

const SECURITY_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'same-origin',
  'Content-Security-Policy':
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; " +
    "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
};

const state = { version: 0, items: [] };

/* ---------------------------------------------------------------- 工具 */

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function httpError(status, message) {
  const err = new Error(message);
  err.status = status;
  return err;
}

/** 本地日期 YYYY-MM-DD。不能用 toISOString：那是 UTC，东八区会错 8 小时。 */
function localDate(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function normalizeItem(raw) {
  if (!raw || typeof raw !== 'object') return null;
  if (typeof raw.id !== 'string' || typeof raw.text !== 'string') return null;
  const text = raw.text.trim();
  if (!text) return null;

  const done = raw.done === true;
  // 老数据里已完成但没有 doneAt 的，给满一个完整周期，不因升级就被清掉
  let doneAt = typeof raw.doneAt === 'string' ? raw.doneAt : null;
  if (done && !doneAt) doneAt = new Date().toISOString();
  if (!done) doneAt = null;

  return {
    id: raw.id,
    text,
    done,
    doneAt,
    createdAt: typeof raw.createdAt === 'string' ? raw.createdAt : new Date().toISOString(),
    date: typeof raw.date === 'string' ? raw.date : localDate(),
  };
}

/**
 * 清理「已完成且超过 24 小时没有再次操作」的任务。
 * 取消完成会清掉 doneAt，所以只要中途动过就不会被删。
 */
function purgeExpired() {
  const now = Date.now();
  const before = state.items.length;

  state.items = state.items.filter((item) => {
    if (!item.done || !item.doneAt) return true;
    const finishedAt = Date.parse(item.doneAt);
    if (Number.isNaN(finishedAt)) return true;
    return now - finishedAt < DONE_TTL_MS;
  });

  if (state.items.length === before) return false;
  state.version += 1;
  return true;
}

function sendJson(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    ...SECURITY_HEADERS,
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(payload),
    'Cache-Control': 'no-store',
  });
  res.end(payload);
}

function sendEmpty(res, status) {
  res.writeHead(status, { ...SECURITY_HEADERS, 'Cache-Control': 'no-store' });
  res.end();
}

/* ---------------------------------------------------------------- 存储 */

/**
 * 读盘。文件不存在视为空清单；JSON 损坏则备份改名后以空清单启动，
 * 服务不因数据文件问题而起不来。
 */
function loadState() {
  try {
    const parsed = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
    if (!parsed || !Array.isArray(parsed.items)) throw new Error('结构不合法');
    state.version = Number.isInteger(parsed.version) && parsed.version >= 0 ? parsed.version : 0;
    state.items = parsed.items.map(normalizeItem).filter(Boolean);
    return { ok: true };
  } catch (err) {
    state.version = 0;
    state.items = [];
    if (err.code === 'ENOENT') return { ok: true, created: true };
    const backup = `${DATA_FILE}.corrupt-${Date.now()}`;
    try {
      fs.renameSync(DATA_FILE, backup);
    } catch {
      /* 备份失败也要能启动 */
    }
    return { ok: false, backup, reason: err.message };
  }
}

/** 写盘串行化：临时文件 + rename 原子替换，响应前 await，保证「看到即已落盘」。 */
let writeChain = Promise.resolve();

function saveState() {
  const run = writeChain.then(async () => {
    const payload = JSON.stringify({ version: state.version, items: state.items }, null, 2);
    await fsp.mkdir(path.dirname(DATA_FILE), { recursive: true });
    const tmp = `${DATA_FILE}.tmp`;
    await fsp.writeFile(tmp, payload, 'utf8');
    let lastErr;
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        await fsp.rename(tmp, DATA_FILE);
        return;
      } catch (err) {
        lastErr = err;
        if (attempt < 3) await sleep(30 * attempt);
      }
    }
    throw lastErr;
  });
  writeChain = run.catch(() => {});
  return run;
}

/** 上次崩溃残留的 .tmp 不应污染目录，启动时顺手清掉。 */
function cleanStaleTmp() {
  const tmp = `${DATA_FILE}.tmp`;
  try {
    const st = fs.statSync(tmp);
    if (Date.now() - st.mtimeMs > STALE_TMP_MS) fs.unlinkSync(tmp);
  } catch {
    /* 没有就算了 */
  }
}

/* ---------------------------------------------------------------- 请求体 */

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    let rejected = false;
    req.on('data', (chunk) => {
      if (rejected) return;
      size += chunk.length;
      if (size > MAX_BODY) {
        rejected = true;
        reject(httpError(413, '请求体过大'));
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      if (!rejected) resolve(Buffer.concat(chunks).toString('utf8'));
    });
    req.on('error', (err) => {
      if (!rejected) reject(err);
    });
  });
}

function parseJsonBody(raw) {
  if (!raw || !raw.trim()) throw httpError(400, '请求体为空');
  try {
    return JSON.parse(raw);
  } catch {
    throw httpError(400, '请求体不是合法 JSON');
  }
}

/* ---------------------------------------------------------------- API */

async function handleApi(req, res, url) {
  const { pathname } = url;

  if (pathname === '/api/health') {
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.setHeader('Allow', 'GET, HEAD');
      throw httpError(405, '方法不允许');
    }
    return sendJson(res, 200, {
      ok: true,
      version: state.version,
      port: url.port || null,
      date: localDate(),
      addrs: lanAddresses().map((a) => a.address),
    });
  }

  if (pathname === '/api/todos') {
    if (req.method === 'GET' || req.method === 'HEAD') {
      // 惰性清理：读取时顺手清掉过期的已完成任务，不需要额外定时器
      if (purgeExpired()) {
        try {
          await saveState();
        } catch (err) {
          console.error('[write] 自动清理落盘失败：', err.message);
        }
      }
      return sendJson(res, 200, {
        version: state.version,
        items: state.items,
        doneTtlHours: DONE_TTL_HOURS,
      });
    }
    if (req.method === 'POST') return createTodo(req, res);
    res.setHeader('Allow', 'GET, HEAD, POST');
    throw httpError(405, '方法不允许');
  }

  const matched = /^\/api\/todos\/([A-Za-z0-9-]{1,64})$/.exec(pathname);
  if (matched) {
    const id = matched[1];
    if (req.method === 'PATCH') return updateTodo(req, res, id);
    if (req.method === 'DELETE') return removeTodo(req, res, id);
    res.setHeader('Allow', 'PATCH, DELETE');
    throw httpError(405, '方法不允许');
  }

  throw httpError(404, '接口不存在');
}

async function createTodo(req, res) {
  const body = parseJsonBody(await readBody(req));
  const text = typeof body.text === 'string' ? body.text.trim() : '';
  if (!text) throw httpError(400, '写点什么再加：任务内容不能为空');

  const item = {
    id: crypto.randomUUID(),
    text,
    done: false,
    doneAt: null,
    createdAt: new Date().toISOString(),
    date: localDate(),
  };
  state.items.unshift(item);
  state.version += 1;

  try {
    await saveState();
  } catch (err) {
    state.items = state.items.filter((i) => i.id !== item.id);
    state.version = Math.max(0, state.version - 1);
    console.error('[write] 新增落盘失败：', err.message);
    throw httpError(503, '写入失败，请重试');
  }

  return sendJson(res, 201, { item, version: state.version });
}

async function updateTodo(req, res, id) {
  const body = parseJsonBody(await readBody(req));

  const hasDone = Object.prototype.hasOwnProperty.call(body, 'done');
  const hasText = Object.prototype.hasOwnProperty.call(body, 'text');
  if (!hasDone && !hasText) throw httpError(400, '没有可更新的字段');

  let nextText = null;
  if (hasText) {
    if (typeof body.text !== 'string') throw httpError(400, 'text 必须是字符串');
    nextText = body.text.trim();
    if (!nextText) throw httpError(400, '任务内容不能为空');
  }
  if (hasDone && typeof body.done !== 'boolean') throw httpError(400, 'done 必须是 true 或 false');

  const item = state.items.find((i) => i.id === id);
  if (!item) throw httpError(404, '任务不存在');

  const prev = { text: item.text, done: item.done, doneAt: item.doneAt };

  if (hasText) item.text = nextText;
  if (hasDone) {
    item.done = body.done;
    // 每次勾选都重新计时；取消完成则清空，表示"中途操作过"
    item.doneAt = body.done ? new Date().toISOString() : null;
  }
  state.version += 1;

  try {
    await saveState();
  } catch (err) {
    item.text = prev.text;
    item.done = prev.done;
    item.doneAt = prev.doneAt;
    state.version = Math.max(0, state.version - 1);
    console.error('[write] 更新落盘失败：', err.message);
    throw httpError(503, '写入失败，请重试');
  }

  return sendJson(res, 200, { item, version: state.version });
}

async function removeTodo(req, res, id) {
  const index = state.items.findIndex((i) => i.id === id);
  if (index === -1) throw httpError(404, '任务不存在');

  const [removed] = state.items.splice(index, 1);
  state.version += 1;

  try {
    await saveState();
  } catch (err) {
    state.items.splice(index, 0, removed);
    state.version = Math.max(0, state.version - 1);
    console.error('[write] 删除落盘失败：', err.message);
    throw httpError(503, '写入失败，请重试');
  }

  return sendEmpty(res, 204);
}

/* ---------------------------------------------------------------- 静态资源 */

function resolveStaticPath(pathname) {
  let decoded;
  try {
    decoded = decodeURIComponent(pathname);
  } catch {
    return null;
  }
  if (decoded.includes('\0')) return null;
  const rel = path.posix.normalize(decoded).replace(/^\/+/, '');
  if (!rel || rel === '.' || rel.endsWith('/')) return null;
  const resolved = path.resolve(PUBLIC_DIR, rel);
  if (resolved !== PUBLIC_DIR && !resolved.startsWith(PUBLIC_DIR + path.sep)) return null;
  return resolved;
}

function serveStatic(req, res, url) {
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.setHeader('Allow', 'GET, HEAD');
    return sendJson(res, 405, { error: '方法不允许' });
  }

  const target = url.pathname === '/' ? '/index.html' : url.pathname;
  const filePath = resolveStaticPath(target);
  if (!filePath) return sendJson(res, 403, { error: '禁止访问' });

  fs.stat(filePath, (err, stat) => {
    if (err || !stat.isFile()) {
      const payload = '页面不存在';
      res.writeHead(404, {
        ...SECURITY_HEADERS,
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Length': Buffer.byteLength(payload),
        'Cache-Control': 'no-store',
      });
      return res.end(req.method === 'HEAD' ? undefined : payload);
    }

    const type = MIME.get(path.extname(filePath).toLowerCase()) || 'application/octet-stream';
    res.writeHead(200, {
      ...SECURITY_HEADERS,
      'Content-Type': type,
      'Content-Length': stat.size,
      'Cache-Control': 'no-store',
    });
    if (req.method === 'HEAD') return res.end();
    const stream = fs.createReadStream(filePath);
    stream.on('error', () => res.destroy());
    return stream.pipe(res);
  });
}

/* ---------------------------------------------------------------- 局域网地址 */

function lanAddresses() {
  const found = [];
  const interfaces = os.networkInterfaces();

  for (const [name, list] of Object.entries(interfaces)) {
    for (const addr of list || []) {
      if (addr.family !== 'IPv4' || addr.internal) continue;
      if (addr.address.startsWith('169.254.')) continue;
      // 虚拟机、WSL、蓝牙、Wi-Fi Direct 等虚拟网卡会把用户带到错误地址
      if (/vEthernet|VMware|VirtualBox|Hyper-V|WSL|Loopback|Bluetooth|蓝牙|本地连接\*/i.test(name)) continue;
      found.push({ name, address: addr.address });
    }
  }

  const score = ({ name, address }) => {
    let value = 0;
    if (/WLAN|Wi-?Fi|无线/i.test(name)) value += 40;
    else if (/Ethernet|以太网/i.test(name)) value += 30;
    if (address.startsWith('192.168.')) value += 6;
    else if (address.startsWith('10.')) value += 4;
    else if (/^172\.(1[6-9]|2\d|3[01])\./.test(address)) value += 3;
    return value;
  };

  return found.sort((a, b) => score(b) - score(a));
}

/* ---------------------------------------------------------------- 启动 */

const server = http.createServer((req, res) => {
  let url;
  try {
    url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  } catch {
    return sendJson(res, 400, { error: '请求地址不合法' });
  }

  const fail = (err) => {
    const status = err && err.status ? err.status : 500;
    if (status === 500) console.error('[error]', err && err.stack ? err.stack : err);
    if (res.headersSent) return res.destroy();
    return sendJson(res, status, { error: status === 500 ? '服务器内部错误' : err.message });
  };

  try {
    const task = url.pathname.startsWith('/api/')
      ? handleApi(req, res, url)
      : serveStatic(req, res, url);
    Promise.resolve(task).catch(fail);
  } catch (err) {
    fail(err);
  }
});

function listenWithFallback(port) {
  return new Promise((resolve, reject) => {
    let attempt = 0;

    const tryListen = (candidate) => {
      const onError = (err) => {
        server.removeListener('listening', onListening);
        if (err.code === 'EADDRINUSE' && attempt < PORT_TRIES) {
          attempt += 1;
          console.warn(`[warn] 端口 ${candidate} 被占用，试 ${candidate + 1}`);
          tryListen(candidate + 1);
          return;
        }
        reject(err);
      };
      const onListening = () => {
        server.removeListener('error', onError);
        resolve(server.address().port);
      };
      server.once('error', onError);
      server.once('listening', onListening);
      // 绑定 0.0.0.0：手机必须能从局域网连进来，不能只监听 127.0.0.1
      server.listen(candidate, '0.0.0.0');
    };

    tryListen(port);
  });
}

/** 探测 3000–3005 上是否已有本服务在跑，避免两个进程写同一份数据。 */
async function findRunningInstance() {
  for (let port = BASE_PORT; port <= BASE_PORT + PORT_TRIES; port += 1) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/health`, {
        signal: AbortSignal.timeout(500),
      });
      if (!res.ok) continue;
      const data = await res.json();
      if (data && data.ok === true) return { port, data };
    } catch {
      /* 这个端口上没有服务 */
    }
  }
  return null;
}

/** 用系统默认浏览器打开。端口以实际监听到的为准，回退到 3001 也不会打开错地址。 */
function openBrowser(url) {
  if (process.platform !== 'win32') {
    console.log('[info] 非 Windows 环境，请手动打开 ' + url);
    return;
  }
  try {
    const child = spawn('cmd.exe', ['/c', 'start', '""', url], {
      stdio: 'ignore',
      detached: true,
    });
    child.on('error', () => console.warn('[warn] 浏览器没能打开，请手动访问 ' + url));
    child.unref();
    console.log('[info] 已请求系统默认浏览器打开 ' + url);
  } catch (err) {
    console.warn('[warn] 浏览器没能打开，请手动访问 ' + url);
  }
}

function printBanner(port) {
  const addrs = lanAddresses();
  const primary = addrs[0];
  const rest = addrs.slice(1);
  const line = '='.repeat(52);

  console.log('');
  console.log(line);
  console.log('  今日待办 · 服务已启动');
  console.log('-'.repeat(52));
  console.log(`  电脑打开：  http://localhost:${port}`);
  console.log('');
  if (primary) {
    console.log('  手机打开（需连同一个 WiFi）：');
    console.log(`  [推荐]      http://${primary.address}:${port}   (${primary.name})`);
    for (const extra of rest) {
      console.log(`  [备用]      http://${extra.address}:${port}   (${extra.name})`);
    }
  } else {
    console.log('  未找到局域网地址：电脑可能没连 WiFi。');
    console.log('  先连网络，或直接用手机热点后重启本服务。');
  }
  console.log('');
  console.log('  手机打不开？见 docs/VERIFY.md');
  console.log('  · 首次运行请在防火墙提示里点「允许访问」');
  console.log('  · 校园网开了「客户端隔离」时，改用手机热点');
  console.log('-'.repeat(52));
  console.log(`  数据文件：  ${DATA_FILE}`);
  console.log('  Ctrl+C 停止服务（数据已实时保存）');
  console.log(line);
  console.log('');
}

async function start() {
  fs.mkdirSync(path.dirname(DATA_FILE), { recursive: true });
  cleanStaleTmp();

  // 双击很容易连点两下。两个进程写同一个 JSON 会互相覆盖，所以在占端口前先看有没有在跑的实例。
  // PORT=0（测试用）不参与这个检查。
  if (BASE_PORT > 0) {
    const running = await findRunningInstance();
    if (running) {
      console.log(`[info] 已有服务在 ${running.port} 端口运行，不再启动第二个。`);
      if (process.env.OPEN_BROWSER === '1') openBrowser(`http://localhost:${running.port}`);
      else console.log(`[info] 直接访问 http://localhost:${running.port}`);
      return;
    }
  }

  const loaded = loadState();
  if (loaded.created) console.log('[info] 首次运行，已创建空清单');
  if (loaded.backup) {
    console.warn('[warn] 数据文件损坏，已备份为', path.basename(loaded.backup), '，以空清单启动');
    console.warn('[warn] 原因：', loaded.reason);
  }

  // 启动时先清一轮：停机期间过期的已完成任务不该在开机后复活
  if (purgeExpired()) {
    try {
      await saveState();
      console.log('[info] 已清理超过 ' + DONE_TTL_HOURS + ' 小时的已完成任务');
    } catch (err) {
      console.error('[write] 启动清理落盘失败：', err.message);
    }
  }

  const port = await listenWithFallback(BASE_PORT);
  printBanner(port);

  if (process.env.OPEN_BROWSER === '1') openBrowser(`http://localhost:${port}`);
}

if (require.main === module) {
  start().catch((err) => {
    console.error('[fatal] 启动失败：', err.message);
    if (err.code === 'EACCES') console.error('提示：端口被系统保留，换端口启动：PORT=3010 node server.js');
    process.exit(1);
  });
}

module.exports = { server, start, state, DATA_FILE };
