'use strict';

/**
 * 接口与持久化测试。真实起进程、真实写文件，不打桩。
 * 运行：node --test test/api.test.js
 */

const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

const ROOT = path.join(__dirname, '..');
const TMP_DIR = path.join(__dirname, '.tmp');
const DATA_FILE = path.join(TMP_DIR, 'todos.json');

let child = null;
let base = '';

function startServer(dataFile, extraEnv) {
  const proc = spawn(process.execPath, ['server.js'], {
    cwd: ROOT,
    env: { ...process.env, PORT: '0', DATA_FILE: dataFile, ...(extraEnv || {}) },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  return new Promise((resolve, reject) => {
    let output = '';
    const timer = setTimeout(() => reject(new Error('服务启动超时：' + output)), 10000);

    const onData = (chunk) => {
      output += chunk.toString('utf8');
      const matched = /localhost:(\d+)/.exec(output);
      if (matched) {
        clearTimeout(timer);
        resolve({ proc, port: Number(matched[1]) });
      }
    };

    proc.stdout.on('data', onData);
    proc.stderr.on('data', onData);
    proc.on('exit', (code) => {
      clearTimeout(timer);
      reject(new Error(`服务提前退出（${code}）：${output}`));
    });
  });
}

function stopServer(proc) {
  return new Promise((resolve) => {
    if (!proc || proc.exitCode !== null) return resolve();
    proc.once('exit', () => resolve());
    proc.kill();
  });
}

const url = (p) => base + p;

async function request(p, options) {
  const init = { method: 'GET' };
  if (options) {
    Object.assign(init, options);
    if (options.body !== undefined) {
      init.headers = { 'Content-Type': 'application/json' };
      init.body = JSON.stringify(options.body);
    }
  }
  const res = await fetch(url(p), init);
  const text = await res.text();
  let json = null;
  try { json = text ? JSON.parse(text) : null; } catch (_) { /* 非 JSON */ }
  return { status: res.status, json, text, headers: res.headers };
}

before(async () => {
  fs.rmSync(TMP_DIR, { recursive: true, force: true });
  fs.mkdirSync(TMP_DIR, { recursive: true });
  const started = await startServer(DATA_FILE);
  child = started.proc;
  base = `http://127.0.0.1:${started.port}`;
});

after(async () => {
  await stopServer(child);
});

test('空清单返回 version 0 与空数组', async () => {
  const res = await request('/api/todos');
  assert.equal(res.status, 200);
  assert.equal(res.json.version, 0);
  assert.deepEqual(res.json.items, []);
  assert.equal(res.json.doneTtlHours, 24, '默认完成后保留 24 小时');
});

test('新增任务：201，字段完整，中文原样保存', async () => {
  const res = await request('/api/todos', { method: 'POST', body: { text: '  把周报发出去  ' } });
  assert.equal(res.status, 201);
  assert.equal(res.json.item.text, '把周报发出去', '前后空格应被裁剪');
  assert.equal(res.json.item.done, false);
  assert.equal(res.json.item.doneAt, null, '未完成的任务不应带完成时间');
  assert.match(res.json.item.id, /^[0-9a-f-]{36}$/);
  assert.match(res.json.item.date, /^\d{4}-\d{2}-\d{2}$/, 'date 必须是本地日期，不是 UTC');
  assert.equal(res.json.version, 1);
});

test('完成时记录 doneAt，取消完成时清空', async () => {
  const created = await request('/api/todos', { method: 'POST', body: { text: '记录完成时间' } });
  const id = created.json.item.id;

  const done = await request(`/api/todos/${id}`, { method: 'PATCH', body: { done: true } });
  assert.equal(done.status, 200);
  assert.ok(done.json.item.doneAt, '勾选完成必须记录 doneAt');
  assert.ok(Date.parse(done.json.item.doneAt) > 0, 'doneAt 必须是可解析的时间');

  const undone = await request(`/api/todos/${id}`, { method: 'PATCH', body: { done: false } });
  assert.equal(undone.json.item.doneAt, null, '取消完成后不应再被自动清理');
  assert.equal(undone.json.item.done, false);
});

test('空白任务被拒绝：空串、半角空格、全角空格都不落库', async () => {
  const before = await request('/api/todos');

  for (const text of ['', '   ', '\u3000\u3000', '\t\n']) {
    const res = await request('/api/todos', { method: 'POST', body: { text } });
    assert.equal(res.status, 400, `「${JSON.stringify(text)}」应被拒绝`);
    assert.ok(res.json.error, '应返回错误说明');
  }

  const after = await request('/api/todos');
  assert.equal(after.json.items.length, before.json.items.length, '不应产生任何空任务');
  assert.equal(after.json.items.some((item) => !item.text.trim()), false, '库里不应存在空文本');
});

test('任务长度不设上限：5000 字原样保存', async () => {
  const text = '长'.repeat(5000);
  const res = await request('/api/todos', { method: 'POST', body: { text } });
  assert.equal(res.status, 201);
  assert.equal(res.json.item.text.length, 5000);

  const list = await request('/api/todos');
  const saved = list.json.items.find((item) => item.id === res.json.item.id);
  assert.equal(saved.text.length, 5000, '落库后长度不变');
});

test('勾选完成：200，且计数口径由 done 决定', async () => {
  const list = await request('/api/todos');
  const target = list.json.items.find((item) => item.text === '把周报发出去');

  const res = await request(`/api/todos/${target.id}`, { method: 'PATCH', body: { done: true } });
  assert.equal(res.status, 200);
  assert.equal(res.json.item.done, true);

  const after = await request('/api/todos');
  const saved = after.json.items.find((item) => item.id === target.id);
  assert.equal(saved.done, true, '勾选状态必须落库');
});

test('勾选参数非法 → 400；任务不存在 → 404', async () => {
  const list = await request('/api/todos');
  const id = list.json.items[0].id;

  const bad = await request(`/api/todos/${id}`, { method: 'PATCH', body: { done: 'yes' } });
  assert.equal(bad.status, 400);

  const missing = await request('/api/todos/00000000-0000-4000-8000-000000000000', {
    method: 'PATCH',
    body: { done: true },
  });
  assert.equal(missing.status, 404);
});

test('修改任务文本：200，文本更新，完成状态不动', async () => {
  const created = await request('/api/todos', { method: 'POST', body: { text: '原来的文案' } });
  const id = created.json.item.id;
  await request(`/api/todos/${id}`, { method: 'PATCH', body: { done: true } });

  const res = await request(`/api/todos/${id}`, { method: 'PATCH', body: { text: '  改过的文案  ' } });
  assert.equal(res.status, 200);
  assert.equal(res.json.item.text, '改过的文案', '前后空格应被裁剪');
  assert.equal(res.json.item.done, true, '改文本不该改变完成状态');
  assert.ok(res.json.item.doneAt, '改文本不该重置完成时间');
});

test('改文本的边界：空白与无字段被拒、原文不变；长文本可保存', async () => {
  const created = await request('/api/todos', { method: 'POST', body: { text: '不该被改掉' } });
  const id = created.json.item.id;

  for (const text of ['', '   ', '\u3000\u3000']) {
    const res = await request(`/api/todos/${id}`, { method: 'PATCH', body: { text } });
    assert.equal(res.status, 400, `「${JSON.stringify(text)}」应被拒绝`);
  }

  const noField = await request(`/api/todos/${id}`, { method: 'PATCH', body: {} });
  assert.equal(noField.status, 400);

  const list = await request('/api/todos');
  const item = list.json.items.find((entry) => entry.id === id);
  assert.equal(item.text, '不该被改掉', '失败的请求不能改动原文');

  const longEdit = await request(`/api/todos/${id}`, { method: 'PATCH', body: { text: '长'.repeat(3000) } });
  assert.equal(longEdit.status, 200, '改文本同样没有长度上限');
  assert.equal(longEdit.json.item.text.length, 3000);
});

test('文本和完成状态可以一次改完', async () => {
  const created = await request('/api/todos', { method: 'POST', body: { text: '一起改' } });
  const id = created.json.item.id;

  const res = await request(`/api/todos/${id}`, { method: 'PATCH', body: { text: '一起改了', done: true } });
  assert.equal(res.status, 200);
  assert.equal(res.json.item.text, '一起改了');
  assert.equal(res.json.item.done, true);
});

test('删除：204，重复删除 → 404', async () => {
  const created = await request('/api/todos', { method: 'POST', body: { text: '待删除' } });
  const id = created.json.item.id;

  const first = await request(`/api/todos/${id}`, { method: 'DELETE' });
  assert.equal(first.status, 204);

  const second = await request(`/api/todos/${id}`, { method: 'DELETE' });
  assert.equal(second.status, 404);

  const list = await request('/api/todos');
  assert.equal(list.json.items.some((item) => item.id === id), false);
});

test('未知接口与非法方法有明确状态码', async () => {
  const noRoute = await request('/api/nope');
  assert.equal(noRoute.status, 404);

  const method = await request('/api/todos', { method: 'PUT' });
  assert.equal(method.status, 405);

  const badJson = await fetch(url('/api/todos'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{oops',
  });
  assert.equal(badJson.status, 400);
});

test('静态资源：首页 200，路径穿越被挡', async () => {
  const page = await request('/');
  assert.equal(page.status, 200);
  assert.match(page.headers.get('content-type'), /text\/html/);

  const css = await request('/style.css');
  assert.equal(css.status, 200);
  assert.match(css.headers.get('content-type'), /text\/css/);

  for (const attack of ['/../server.js', '/..%2Fserver.js', '/%2e%2e/server.js', '/..\\server.js']) {
    const res = await request(attack);
    assert.ok([403, 404].includes(res.status), `${attack} 不应返回 200`);
    assert.equal(res.text.includes('createServer'), false, `${attack} 泄漏了服务端源码`);
  }
});

test('重启后数据仍在：进程崩溃也不会丢已确认的写入', async () => {
  const before = await request('/api/todos');
  assert.ok(before.json.items.length >= 2);

  await stopServer(child);
  const restarted = await startServer(DATA_FILE);
  child = restarted.proc;
  base = `http://127.0.0.1:${restarted.port}`;

  const after = await request('/api/todos');
  assert.equal(after.json.items.length, before.json.items.length);
  assert.equal(after.json.version, before.json.version, 'version 必须持久化');

  const raw = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
  assert.equal(raw.items.length, before.json.items.length, '磁盘上的数据应与接口一致');
});

test('已完成的 24 小时没有再次操作会被清理，未完成的不会被清理', async () => {
  const file = path.join(TMP_DIR, 'ttl.json');
  // 把 24 小时压到约 1.4 秒，才能真的等得到
  const started = await startServer(file, { DONE_TTL_HOURS: '0.0004' });
  const ttlBase = `http://127.0.0.1:${started.port}`;

  const post = (text) => fetch(ttlBase + '/api/todos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  }).then((res) => res.json());

  const read = () => fetch(ttlBase + '/api/todos').then((res) => res.json());

  try {
    const finished = await post('已完成的会被清理');
    await post('没完成的要留下');
    await fetch(`${ttlBase}/api/todos/${finished.item.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ done: true }),
    });

    const beforeExpiry = await read();
    assert.equal(beforeExpiry.items.length, 2, '未到时间不能删');
    assert.equal(beforeExpiry.doneTtlHours, 0.0004, '接口要告诉前端实际规则');

    await new Promise((resolve) => setTimeout(resolve, 1700));

    const afterExpiry = await read();
    assert.equal(afterExpiry.items.length, 1, '过期的已完成任务应被清理');
    assert.equal(afterExpiry.items[0].text, '没完成的要留下');
    assert.ok(afterExpiry.version > beforeExpiry.version, '清理后 version 必须递增，前端才会重绘');

    const onDisk = JSON.parse(fs.readFileSync(file, 'utf8'));
    assert.equal(onDisk.items.length, 1, '清理结果必须落盘，重启不该复活');
  } finally {
    await stopServer(started.proc);
  }
});

test('数据文件损坏：备份后以空清单启动，不崩溃', async () => {
  const brokenFile = path.join(TMP_DIR, 'broken.json');
  fs.writeFileSync(brokenFile, '{ this is not json', 'utf8');

  const started = await startServer(brokenFile);
  const port = started.port;

  const res = await fetch(`http://127.0.0.1:${port}/api/todos`);
  const body = await res.json();
  assert.equal(body.items.length, 0, '损坏文件应以空清单启动');
  assert.equal(body.version, 0);

  const backups = fs.readdirSync(TMP_DIR).filter((name) => name.startsWith('broken.json.corrupt-'));
  assert.equal(backups.length, 1, '原文件应被备份而不是直接丢弃');

  await stopServer(started.proc);
});
