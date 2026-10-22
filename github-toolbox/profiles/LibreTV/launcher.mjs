import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn, execFile } from 'node:child_process';
import { promisify } from 'node:util';

const root = path.dirname(fileURLToPath(import.meta.url));
const source = path.join(root, 'source');
const node = path.join(root, 'runtime', 'node.exe');
const lock = path.join(root, '.service-lock.json');
const logs = path.join(root, 'logs');
const url = 'http://localhost:8080';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const expected = JSON.parse(fs.readFileSync(path.join(source, 'package.json'), 'utf8')).version;
fs.mkdirSync(logs, { recursive: true });
const log = msg => fs.appendFileSync(path.join(logs, 'launcher.log'), `${new Date().toISOString()} ${msg}\n`);
const alive = pid => { try { process.kill(pid, 0); return true; } catch { return false; } };
async function open() {
  // The local default HTTP handler was verified as MSEdgeHTM. Launch its
  // executable explicitly: Explorer URL dispatch can leave the browser hidden.
  const candidates = [
    path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
    path.join(process.env.ProgramFiles || 'C:\\Program Files', 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
  ];
  const browser = candidates.find(candidate => fs.existsSync(candidate));
  if (!browser) throw new Error('Microsoft Edge was not found. Open http://localhost:8080 manually; see launcher.log.');
  log('Opening maximized browser window: ' + browser);
  const ps = path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
  const result = await promisify(execFile)(ps, ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(root, 'open-browser.ps1'),
    '-Browser', browser, '-Url', url, '-StateFile', path.join(logs, 'browser-window.json')], {
    windowsHide: true, timeout: 45000
  });
  log(result.stdout.trim());
  log('Browser window verified maximized');
}
async function status() {
  try {
    const r = await fetch(`http://127.0.0.1:8080/api/status`, { signal: AbortSignal.timeout(2000) });
    if (!r.ok) return false;
    const s = await r.json();
    return s.version === expected && s.passwordRequired === true;
  } catch { return false; }
}
function notify(message) {
  spawn('wscript.exe', [path.join(root, 'notify.vbs'), message], { windowsHide: true, stdio: 'ignore' }).unref();
}
async function run() {
  if (fs.existsSync(lock)) {
    let previous;
    for (let i = 0; i < 10; i++) {
      try { previous = JSON.parse(fs.readFileSync(lock, 'utf8')); break; } catch { await sleep(100); }
    }
    if (!previous) throw new Error('Could not read LibreTV service state. See logs before retrying.');
    if (previous && alive(previous.pid)) {
      for (let i = 0; i < 90; i++) {
        if (await status()) { log("Reusing running LibreTV service"); await open(); return; }
        if (!alive(previous.pid)) break;
        await sleep(1000);
      }
      throw new Error('Existing LibreTV launcher did not become ready. See logs; no duplicate service was started.');
    }
    fs.unlinkSync(lock);
  }
  // Exclusive creation prevents two rapid double-clicks from starting two servers.
  let fd;
  try { fd = fs.openSync(lock, 'wx'); }
  catch (e) {
    if (e.code === 'EEXIST') { await sleep(500); return run(); }
    throw e;
  }
  fs.writeFileSync(fd, JSON.stringify({ pid: process.pid, root, started: new Date().toISOString() }));
  fs.closeSync(fd);
  let child;
  const release = () => {
    try {
      const current = JSON.parse(fs.readFileSync(lock, 'utf8'));
      if (current.pid === process.pid) fs.unlinkSync(lock);
    } catch {}
  };
  try {
    if (!fs.existsSync(path.join(source, '.next', 'BUILD_ID'))) throw new Error('Production build is missing. Rebuild using the instructions.');
    // Refuse a busy port, including another unrelated HTTP service.
    const net = await import('node:net');
    await new Promise((resolve, reject) => {
      const probe = net.createServer();
      probe.once('error', reject);
      probe.listen(8080, '127.0.0.1', () => probe.close(resolve));
    });
    for (const name of ['server.log', 'launcher.log']) {
      const f = path.join(logs, name);
      if (fs.existsSync(f) && fs.statSync(f).size > 1024 * 1024) fs.truncateSync(f);
    }
    const output = fs.openSync(path.join(logs, 'server.log'), 'a');
    log('Starting LibreTV on 127.0.0.1:8080');
    child = spawn(node, [path.join(source, 'node_modules', 'next', 'dist', 'bin', 'next'), 'start', '--hostname', '127.0.0.1', '--port', '8080'], {
      cwd: source, windowsHide: true, stdio: ['ignore', output, output],
      env: { ...process.env, NODE_ENV: 'production', NEXT_TELEMETRY_DISABLED: '1' }
    });
    fs.closeSync(output);
    let failure;
    child.once('error', e => { failure = e; });
    const finished = new Promise(resolve => child.once('exit', (code, signal) => { log(`Server exited: ${code ?? signal}`); resolve(); }));
    let ready = false;
    for (let i = 0; i < 90; i++) {
      if (failure) throw failure;
      if (child.exitCode !== null) throw new Error('LibreTV exited before readiness. See logs/server.log.');
      if (await status()) { ready = true; break; }
      await sleep(1000);
    }
    if (!ready) throw new Error('LibreTV did not become ready within 90 seconds. See logs/server.log.');
    log(`Ready; server PID ${child.pid}`);
    fs.writeFileSync(lock, JSON.stringify({ pid: process.pid, serverPid: child.pid, root, started: new Date().toISOString() }));
    await open();
    await finished;
  } finally {
    if (child && child.exitCode === null) child.kill();
    release();
  }
}
run().catch(error => {
  log(error.stack || String(error));
  notify('LibreTV failed to start. Details: ' + path.join(logs, 'launcher.log') + '\n' + error.message);
  process.exitCode = 1;
});
