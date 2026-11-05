// Production-only launcher; keeps its private password across restarts.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import nextEnv from '@next/env';

const root = path.dirname(fileURLToPath(import.meta.url));
process.chdir(root);
const settings = path.join(root, '.env.local');
if (!fs.existsSync(settings)) {
  const defaults = fs.readFileSync(path.join(root, 'defaults.json'), 'utf8');
  fs.writeFileSync(settings, 'PASSWORD=' + crypto.randomBytes(32).toString('base64url') +
    '\nDEFAULT_SOURCES=' + JSON.stringify(JSON.parse(defaults)) + '\n', { flag: 'wx', mode: 0o600 });
}
process.env.NODE_ENV = 'production';
nextEnv.loadEnvConfig(root, false);
if (!process.env.PASSWORD) throw new Error('PASSWORD is empty; restore your local .env.local before starting.');
process.env.HOSTNAME = '127.0.0.1';
process.env.PORT = '8080';
process.env.NEXT_TELEMETRY_DISABLED = '1';
console.log('LibreTV: http://127.0.0.1:8080 (Ctrl+C stops the service).');
console.log('Your local login password is the PASSWORD value in .env.local; keep that file private.');
await import('./server.js');
