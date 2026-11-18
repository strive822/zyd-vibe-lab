/**
 * zustand persist 用的节流 localStorage 包装（独立成模块的原因：
 * db.ts 的 importConfig 需要 flush 节流缓冲，而运行时依赖方向是 store → db，
 * db.ts 不能反向 import store，故把两者共用的存储逻辑放在这个无依赖的底层模块）。
 */

import type { StateStorage } from 'zustand/middleware';

/** store 持久化在 localStorage 中的键（store.ts 的 persist name 与 importConfig 共用） */
export const PERSIST_KEY = 'libretv-settings';

/** 节流窗口：搜索/测活等高频 set 合并为 800ms 一次落盘 */
const THROTTLE_MS = 800;

interface Snapshot {
  state: Record<string, unknown>;
  version?: number;
  generation?: string;
  editedAt?: Record<string, number>;
}

interface PendingPatch {
  generation?: string;
  changes: Record<string, unknown>;
  removed: string[];
  editedAt?: Record<string, number>;
}

interface ThrottledStorage extends StateStorage {
  syncSnapshot: (state: Record<string, unknown>, version?: number) => void;
}

interface StorageMigration {
  version: number;
  migrate: (state: Record<string, unknown>, version: number) => object;
}

const flushers = new Set<(exclusive: boolean) => boolean>();
const SETTINGS_LOCK = 'libretv:settings-write';
const pendingPrefix = (name: string) => name + ':pending:';
const generationKey = (name: string) => name + ':active-generation';
const snapshotKey = (name: string, id: string) => name + ':generation:' + id;
const newId = () => Date.now().toString(36) + '-' + Math.random().toString(36).slice(2);

function activeSettingsKey(storage: Storage, name: string): string {
  const id = storage.getItem(generationKey(name));
  return id ? snapshotKey(name, id) : name;
}

function readActiveSnapshot(storage: Storage, name: string): string | null {
  for (let attempt = 0; attempt < 3; attempt++) {
    const active = activeSettingsKey(storage, name);
    const value = storage.getItem(active);
    if (active === activeSettingsKey(storage, name)) return value;
  }
  throw new Error('设置正在被其他标签页更新，请重试');
}

export function readPersistedSettings(): string | null {
  const raw = readActiveSnapshot(localStorage, PERSIST_KEY);
  const snapshot = parseSnapshot(raw);
  const patches = readPendingPatches(localStorage, PERSIST_KEY);
  if (patches.length === 0) return raw;
  const state = { ...snapshot?.state };
  const editedAt = { ...snapshot?.editedAt };
  applyPatches(state, snapshot?.generation, editedAt, patches.map(([, patch]) => patch));
  return JSON.stringify({ ...snapshot, state, editedAt });
}

function canSerializeWrites(): boolean {
  return (typeof navigator !== 'undefined' && Boolean(navigator.locks)) ||
    typeof indexedDB !== 'undefined';
}

let coordination: Promise<IDBDatabase> | undefined;

function openCoordination(): Promise<IDBDatabase> {
  return coordination ??= new Promise((resolve, reject) => {
    const request = indexedDB.open(SETTINGS_LOCK, 1);
    request.onupgradeneeded = () => request.result.createObjectStore('lock');
    request.onsuccess = () => {
      const db = request.result;
      db.onversionchange = () => { db.close(); coordination = undefined; };
      resolve(db);
    };
    request.onerror = () => { coordination = undefined; reject(request.error); };
  });
}

function withSettingsLock<T>(operation: (exclusive: boolean) => T): T | Promise<T> {
  const locks = typeof navigator === 'undefined' ? undefined : navigator.locks;
  if (locks) return locks.request(SETTINGS_LOCK, () => operation(true));
  if (typeof indexedDB === 'undefined') return operation(false);
  // IndexedDB is also available on HTTP. Conflicting read/write transactions
  // are serialized until their callbacks finish across documents of the origin.
  return openCoordination().then((db) => new Promise<T>((resolve, reject) => {
    const transaction = db.transaction('lock', 'readwrite');
    const reservation = transaction.objectStore('lock').get(SETTINGS_LOCK);
    let result: T;
    reservation.onsuccess = () => {
      try { result = operation(true); }
      catch (error) { reject(error); transaction.abort(); }
    };
    transaction.oncomplete = () => resolve(result);
    transaction.onabort = () => reject(transaction.error ?? new Error('无法取得设置存储锁'));
    transaction.onerror = () => reject(transaction.error);
  }), () => operation(false));
}
const listeners = new Set<() => void>();

/** 外部写入及本标签重基落盘后，让 store 恢复合并后的快照（恢复本身不写盘）。 */
export function subscribePersistChanges(listener: () => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

function notifyChanges(): void {
  for (const listener of listeners) listener();
}

function parseSnapshot(value: string | null): Snapshot | null {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value) as Snapshot;
    return parsed && parsed.state && typeof parsed.state === 'object' && !Array.isArray(parsed.state)
      ? parsed : null;
  } catch {
    return null;
  }
}

function readPendingPatches(storage: Storage | undefined, name: string): [string, PendingPatch][] {
  if (!storage) return [];
  const patches: [string, PendingPatch][] = [];
  for (let index = 0; index < storage.length; index++) {
    const key = storage.key(index);
    if (!key?.startsWith(pendingPrefix(name))) continue;
    try {
      const patch = JSON.parse(storage.getItem(key) ?? 'null') as PendingPatch | null;
      if (patch?.changes && Array.isArray(patch.removed)) patches.push([key, patch]);
    } catch {
      // Ignore invalid recovery records.
    }
  }
  return patches.sort(([left], [right]) => left.localeCompare(right));
}

function applyPatches(
  state: Record<string, unknown>, generation: string | undefined,
  editedAt: Record<string, number>, patches: PendingPatch[],
): void {
  for (const patch of patches) {
    if (patch.generation !== generation) continue;
    const accept = (key: string) => {
      if (key === '__proto__') return false;
      const timestamp = patch.editedAt?.[key] ?? 0;
      if (timestamp < (editedAt[key] ?? 0)) return false;
      editedAt[key] = timestamp;
      return true;
    };
    for (const key of patch.removed) {
      if (accept(key)) delete state[key];
    }
    for (const [key, value] of Object.entries(patch.changes)) {
      if (accept(key)) state[key] = value;
    }
  }
}

function flushUnlocked(exclusive: boolean): boolean {
  let complete = true;
  for (const flush of flushers) {
    if (!flush(exclusive)) complete = false;
  }
  return complete;
}

export async function flushPendingPersist(): Promise<boolean> {
  return withSettingsLock(flushUnlocked);
}

/** Keep the buffer flush and replacement in the same origin-wide write lock. */
export async function replacePersistedSettings(value: string): Promise<void> {
  const imported = parseSnapshot(value);
  if (!imported) throw new Error('配置文件格式不正确');
  await withSettingsLock((exclusive) => {
    if (!flushUnlocked(exclusive)) throw new Error('无法保存当前设置，请检查浏览器存储后重试导入');
    const oldKey = activeSettingsKey(localStorage, PERSIST_KEY);
    const id = newId();
    const key = snapshotKey(PERSIST_KEY, id);
    localStorage.setItem(key, JSON.stringify({ ...imported, generation: id, editedAt: undefined }));
    try {
      // Old tabs finish writing to the old slot even if there is no Web Lock.
      localStorage.setItem(generationKey(PERSIST_KEY), id);
    } catch (error) {
      localStorage.removeItem(key);
      throw error;
    }
    if (oldKey !== PERSIST_KEY) localStorage.removeItem(oldKey);
    notifyChanges();
  });
}

/**
 * 节流写入的 localStorage 包装。
 * 搜索会逐源写健康度、测活每 200ms 合并写回，这些都会触发 persist 的整份序列化 + 写盘；
 * 这里把写入合并为 800ms 一次，并在页面隐藏/卸载时立即 flush，确保不丢最后一次修改。
 */
export function createThrottledStorage(migration?: StorageMigration): ThrottledStorage {
  // 每个标签独立维护「上次交给 store 的快照」和实际修改过的字段。
  // 不能拿整份旧快照覆盖磁盘：即使 storage 事件尚未送达，测速等无关 set 也应保留新源。
  let storage: Storage | undefined;
  try { storage = localStorage; } catch { /* SSR / 禁止存储 */ }
  let snapshot: Snapshot | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let pendingName: string | null = null;
  /**
   * 我们最后一次读到 / 写掉的磁盘原文。用来在 flush 时判断「磁盘上是否有别的标签
   * 刚写进去、而我们内存里没有的内容」——只有真有外部改动才值得让本标签 rehydrate。
   */
  let lastKnownDisk: string | null = null;
  let generation: string | undefined;
  const changes = new Map<string, unknown>();
  const removed = new Set<string>();
  const edits = new Map<string, number>();

  const read = (name: string): string | null => storage ? readActiveSnapshot(storage, name) : null;
  const localPatch = (): PendingPatch => ({
    generation, changes: Object.fromEntries(changes), removed: [...removed], editedAt: Object.fromEntries(edits),
  });
  const pendingPatches = (name: string) => readPendingPatches(storage, name);
  const requiresMigration = (latest: Snapshot | null) =>
    latest !== null && migration !== undefined && (latest.version ?? 0) < migration.version;
  const rebase = (latest: Snapshot | null, patches: PendingPatch[]): Snapshot => {
    const diskVersion = latest?.version ?? 0;
    const state: Record<string, unknown> = requiresMigration(latest) && migration && latest
      ? { ...migration.migrate(latest.state, diskVersion) }
      : { ...(latest?.state ?? {}) };
    const editedAt = { ...latest?.editedAt };
    applyPatches(state, latest?.generation, editedAt, patches);
    // Retain a newer on-disk version when a tab is still running older code.
    const version = latest && migration
      ? Math.max(diskVersion, migration.version)
      : snapshot?.version ?? latest?.version;
    return { state, version, generation: latest?.generation, editedAt };
  };
  const flushNow = (exclusive: boolean) => {
    if (timer) clearTimeout(timer);
    timer = null;
    if (!pendingName) return true;
    if (!storage) return false;
    const name = pendingName;
    try {
      const destination = activeSettingsKey(storage, name);
      const latest = storage.getItem(destination);
      // 磁盘内容与上次已知不一致 = 别的标签写过，本标签内存确实落后，才需要 rehydrate。
      // 单标签场景（绝大多数时候）这一句直接把「每次落盘都自我 rehydrate」省掉：
      // 那会多出一轮全应用订阅者通知，而值并没有任何变化。
      const external = latest !== lastKnownDisk;
      const disk = parseSnapshot(latest);
      const recovered = pendingPatches(name);
      const next = JSON.stringify(rebase(disk, [...recovered.map(([, patch]) => patch), localPatch()]));
      if (next !== latest) {
        storage.setItem(destination, next);
        lastKnownDisk = next;
      } else {
        lastKnownDisk = latest;
      }
      pendingName = null;
      changes.clear();
      removed.clear();
      edits.clear();
      generation = disk?.generation;
      if (exclusive) for (const [key] of recovered) storage.removeItem(key);
      const active = activeSettingsKey(storage, name);
      if (active !== destination && destination !== name) storage.removeItem(destination);
      if (external || (exclusive && recovered.length) || active !== destination) notifyChanges();
      return true;
    } catch {
      // 配额不足 / 隐私模式下保留内存态，后续操作或显式 flush 可重试。
      return false;
    }
  };
  flushers.add(flushNow);

  const scheduleFlush = (name: string) => {
    pendingName = name;
    if (!timer) timer = setTimeout(flushInBrowser, THROTTLE_MS);
  };
  function flushInBrowser() {
    void Promise.resolve(withSettingsLock(flushNow)).catch(() => {});
  }

  function writePending(name: string) {
    storage?.setItem(pendingPrefix(name) + newId(), JSON.stringify(localPatch()));
  }

  function saveBeforeLeaving() {
    if (!canSerializeWrites()) {
      flushNow(false);
      return;
    }
    // Page dismissal cannot wait for Web Locks. Write only this tab's pending
    // fields to a separate key so it cannot overwrite an in-flight snapshot.
    if (storage && pendingName && (changes.size || removed.size)) {
      try {
        writePending(pendingName);
        changes.clear();
        removed.clear();
        edits.clear();
      } catch {
        // Keep the in-memory patch available if the page continues running.
      }
    }
    flushInBrowser();
  }

  if (typeof window !== 'undefined') {
    const doc = document;
    doc.addEventListener?.('visibilitychange', () => {
      if (doc.visibilityState === 'hidden') saveBeforeLeaving();
    });
    window.addEventListener('pagehide', saveBeforeLeaving);
    window.addEventListener('beforeunload', saveBeforeLeaving);
    window.addEventListener('storage', (event) => {
      if (event.storageArea !== storage) return;
      const key = event.key;
      if (key === PERSIST_KEY || key === null || key === generationKey(PERSIST_KEY) ||
          key.startsWith(pendingPrefix(PERSIST_KEY)) || key.startsWith(PERSIST_KEY + ':generation:')) {
        notifyChanges();
      }
    });
  }

  return {
    // hydration 会补入缺省字段；比较基线必须与实际 store 一致，否则旧快照缺少的
    // 默认值会在下次普通 set 时被误认作本标签的修改，回退另一标签的新偏好。
    syncSnapshot: (state, version) => { snapshot = { state, version }; },
    getItem: (name) => {
      try {
        const latest = read(name);
        lastKnownDisk = latest;
        const disk = parseSnapshot(latest);
        if (generation !== disk?.generation) {
          changes.clear();
          removed.clear();
          edits.clear();
          generation = disk?.generation;
        }
        const recovered = pendingPatches(name);
        // Hydrate from the migrated state without submitting automatic changes as user edits.
        // Once the write lock is acquired, migrate the snapshot that actually remains on disk.
        if (requiresMigration(disk) || (recovered.length && canSerializeWrites())) scheduleFlush(name);
        return pendingName === name || recovered.length
          ? JSON.stringify(rebase(disk, [...recovered.map(([, patch]) => patch), localPatch()]))
          : latest;
      } catch {
        return null;
      }
    },
    setItem: (name, value) => {
      const next = parseSnapshot(value);
      if (!next) return;
      const versionChanged = snapshot?.version !== next.version;
      const previous = snapshot?.state ?? {};
      for (const key of new Set([...Object.keys(previous), ...Object.keys(next.state)])) {
        if (JSON.stringify(previous[key]) === JSON.stringify(next.state[key])) continue;
        edits.set(key, performance.timeOrigin + performance.now());
        if (Object.hasOwn(next.state, key)) {
          changes.set(key, next.state[key]);
          removed.delete(key);
        } else {
          changes.delete(key);
          removed.add(key);
        }
      }
      snapshot = next;
      if (changes.size === 0 && removed.size === 0 && !versionChanged) return;
      scheduleFlush(name);
    },
    removeItem: (name) => {
      if (timer) clearTimeout(timer);
      timer = null;
      pendingName = null;
      changes.clear();
      removed.clear();
      edits.clear();
      snapshot = null;
      lastKnownDisk = null;
      generation = undefined;
      return withSettingsLock(() => {
        try {
          if (!storage) return;
          const active = activeSettingsKey(storage, name);
          storage.removeItem(active);
          storage.removeItem(generationKey(name));
          storage?.removeItem(name);
          for (const [key] of pendingPatches(name)) storage?.removeItem(key);
        } catch {
          // 浏览器可能禁用存储。
        }
      });
    },
  };
}
