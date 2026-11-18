import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./db', () => ({
  db: {},
  clearLiveProbeResultsDb: vi.fn(async () => {}),
  loadLiveProbeResults: vi.fn(async () => ({})),
  saveLiveProbeResults: vi.fn(async () => {}),
}));

const KEY = 'libretv-settings';
const sources = [
  { key: 'custom_0', name: '非凡', url: 'https://ff.example/api' },
  { key: 'custom_1', name: '量子', url: 'https://lz.example/api' },
];
const added = { name: '360', url: 'https://360.example/api' };
const disk = new Map<string, string>();

function makeStorage(): Storage {
  return {
    get length() { return disk.size; },
    key: (index) => [...disk.keys()][index] ?? null,
    clear: () => disk.clear(),
    getItem: (key) => disk.get(key) ?? null,
    setItem: (key, value) => { disk.set(key, value); },
    removeItem: (key) => { disk.delete(key); },
  };
}

/** 每次加载真实 store 和 adapter 的独立模块副本，模拟共享磁盘的独立标签页。 */
async function openTab() {
  const target = new EventTarget();
  const storage = makeStorage();
  vi.stubGlobal('window', target);
  vi.stubGlobal('document', { visibilityState: 'visible' });
  vi.stubGlobal('localStorage', storage);
  vi.resetModules();
  const { useAppStore } = await import('./store');
  const { flushPendingPersist, replacePersistedSettings } = await import('./persist-storage');
  await useAppStore.persist.rehydrate();
  return {
    store: useAppStore,
    flush: flushPendingPersist,
    replace: replacePersistedSettings,
    notify: () => target.dispatchEvent(Object.assign(new Event('storage'), {
      key: KEY, storageArea: storage, newValue: storage.getItem(KEY),
    })),
    unload: () => target.dispatchEvent(new Event('beforeunload')),
    storage,
  };
}

function saved() {
  const generation = disk.get(KEY + ':active-generation');
  return JSON.parse(disk.get(generation ? KEY + ':generation:' + generation : KEY)!).state;
}

beforeEach(() => {
  // Use the same browser fixture on every Node version. Tests for locks install their own provider.
  vi.stubGlobal('navigator', {});
  vi.stubGlobal('indexedDB', undefined);
  vi.useFakeTimers();
  disk.clear();
  disk.set(KEY, JSON.stringify({ version: 8, state: {
    customAPIs: sources,
    selectedKeys: sources.map((source) => source.key),
    sourceHealth: {},
    adFilter: true,
  } }));
});

afterEach(() => {
  vi.clearAllTimers();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('多标签配置持久化', () => {
  it('未收到 storage 通知的旧标签更新健康度，不覆盖另一标签新增的源', async () => {
    const a = await openTab();
    const b = await openTab();
    b.store.getState().addCustomApi(added);
    await b.flush();
    a.store.getState().recordSourceHealth([{ sourceKey: 'custom_0', ok: true, ms: 100, list: [] }]);
    await a.flush();
    expect(saved().customAPIs.map((source: { name: string }) => source.name)).toEqual(['非凡', '量子', '360']);
    expect(saved().sourceHealth.custom_0.ok).toBe(true);
  });

  it.each(['新增', '删除', '停用'] as const)('旧标签已排队的延迟写不能覆盖另一标签的%s操作', async (operation) => {
    const a = await openTab();
    const b = await openTab();
    a.store.getState().recordSourceHealth([{ sourceKey: 'custom_0', ok: true, ms: 100, list: [] }]);
    if (operation === '新增') b.store.getState().addCustomApi(added);
    if (operation === '删除') b.store.getState().removeCustomApi('custom_0');
    if (operation === '停用') b.store.getState().toggleSourceSelected('custom_0');
    await b.flush();
    const expectedSources = saved().customAPIs;
    const expectedSelected = saved().selectedKeys;
    vi.advanceTimersByTime(800);
    expect(saved().customAPIs).toEqual(expectedSources);
    expect(saved().selectedKeys).toEqual(expectedSelected);
    expect(saved().sourceHealth.custom_0.ok).toBe(true);
  });

  it('页面卸载前的 flush 也不能复活另一标签已删除的源', async () => {
    const a = await openTab();
    const b = await openTab();
    a.store.getState().updateSettings({ adFilter: false });
    b.store.getState().removeCustomApi('custom_0');
    await b.flush();
    a.unload();
    expect(saved().customAPIs).toEqual([sources[1]]);
    expect(saved().adFilter).toBe(false);
  });

  it('外部 storage 通知恢复内存配置，且不会触发回写循环', async () => {
    const a = await openTab();
    const b = await openTab();
    b.store.getState().addCustomApi(added);
    await b.flush();
    const persisted = disk.get(KEY);
    a.notify();
    expect(a.store.getState().customAPIs.map((source) => source.name)).toEqual(['非凡', '量子', '360']);
    vi.advanceTimersByTime(800);
    expect(disk.get(KEY)).toBe(persisted);
  });

  it('收到外部配置时保留本标签尚未落盘的修改', async () => {
    const a = await openTab();
    const b = await openTab();
    a.store.getState().updateSettings({ adFilter: false });
    b.store.getState().addCustomApi(added);
    await b.flush();
    a.notify();
    expect(a.store.getState().adFilter).toBe(false);
    expect(a.store.getState().customAPIs).toHaveLength(3);
    await a.flush();
    expect(saved().adFilter).toBe(false);
    expect(saved().customAPIs).toHaveLength(3);
  });

  it('导入直接覆盖快照后，旧标签普通状态更新不回退导入配置', async () => {
    const a = await openTab();
    a.storage.setItem(KEY, JSON.stringify({ version: 8, state: {
      customAPIs: [{ key: 'imported', name: '导入源', url: 'https://import.example/api' }],
      selectedKeys: ['imported'],
      adFilter: true,
      sourceHealth: {},
    } }));
    a.store.getState().recordSourceHealth([{ sourceKey: 'custom_0', ok: true, ms: 100, list: [] }]);
    await a.flush();
    expect(saved().customAPIs[0].key).toBe('imported');
    expect(saved().selectedKeys).toEqual(['imported']);
  });

  it('本标签连续新增、停用、删除仍按用户操作保存', async () => {
    const a = await openTab();
    a.store.getState().addCustomApi(added);
    a.store.getState().toggleSourceSelected('custom_1');
    a.store.getState().removeCustomApi('custom_0');
    await a.flush();
    const restored = await openTab();
    expect(restored.store.getState().customAPIs.map((source) => source.name)).toEqual(['量子', '360']);
    expect(restored.store.getState().selectedKeys).toEqual(['custom_2']);
  });

  it('两标签分别修改不同偏好时，两项操作都持久化', async () => {
    const a = await openTab();
    const b = await openTab();
    a.store.getState().updateSettings({ adFilter: false });
    b.store.getState().updateSettings({ autoplayNext: false });
    await b.flush();
    await a.flush();
    expect(saved().adFilter).toBe(false);
    expect(saved().autoplayNext).toBe(false);
    expect(a.store.getState().autoplayNext).toBe(false);
  });

  it('空存储首次打开的旧标签无关更新，不覆盖另一标签新配置', async () => {
    disk.clear();
    const a = await openTab();
    const b = await openTab();
    b.store.getState().addCustomApi(added);
    b.store.getState().updateSettings({ autoplayNext: false });
    await b.flush();
    a.store.getState().recordSourceHealth([{ sourceKey: 'custom_0', ok: true, ms: 100, list: [] }]);
    await a.flush();
    expect(saved().customAPIs.map((source: { name: string }) => source.name)).toEqual(['360']);
    expect(saved().autoplayNext).toBe(false);
  });

  it('旧版配置迁移产生的待写默认值不回退另一标签的新偏好', async () => {
    disk.set(KEY, JSON.stringify({ ...JSON.parse(disk.get(KEY)!), version: 7 }));
    const a = await openTab();
    const b = await openTab();
    b.store.getState().updateSettings({ autoplayNext: false });
    await b.flush();
    await a.flush();
    expect(saved().autoplayNext).toBe(false);
    expect(saved().customAPIs).toEqual(sources);
    expect(JSON.parse(disk.get(KEY)!).version).toBe(8);
  });

  it('本标签 flush 同步新基线后，后续普通更新仍保留远端源', async () => {
    const a = await openTab();
    const b = await openTab();
    b.store.getState().addCustomApi(added);
    await b.flush();
    a.store.getState().updateSettings({ adFilter: false });
    await a.flush();
    a.store.getState().updateSettings({ autoplayNext: false });
    await a.flush();
    expect(saved().customAPIs).toHaveLength(3);
    expect(a.store.getState().customAPIs).toHaveLength(3);
  });

  it('重复 rehydrate 不丢待写偏好，也不把远端源误判为本地删除', async () => {
    const a = await openTab();
    const b = await openTab();
    a.store.getState().updateSettings({ adFilter: false });
    b.store.getState().addCustomApi(added);
    await b.flush();
    await a.store.persist.rehydrate();
    await a.store.persist.rehydrate();
    a.store.getState().updateSettings({ autoplayNext: false });
    await a.flush();
    expect(saved().customAPIs).toHaveLength(3);
    expect(saved().adFilter).toBe(false);
    expect(saved().autoplayNext).toBe(false);
  });

  it('清除持久化存储会取消本标签已经排队的旧写入', async () => {
    const a = await openTab();
    a.store.getState().addCustomApi(added);
    a.store.persist.clearStorage();
    vi.advanceTimersByTime(800);
    a.unload();
    expect(disk.has(KEY)).toBe(false);
  });

  it('写入失败后内存操作仍可用，显式重试成功保存', async () => {
    const a = await openTab();
    a.store.getState().addCustomApi(added);
    const fail = vi.spyOn(a.storage, 'setItem').mockImplementationOnce(() => { throw new Error('quota'); });
    await expect(a.flush()).resolves.toBe(false);
    expect(a.store.getState().customAPIs).toHaveLength(3);
    expect(saved().customAPIs).toHaveLength(2);
    await a.flush();
    expect(saved().customAPIs).toHaveLength(3);
    fail.mockRestore();
  });

  it('导入前写盘失败时保留现有配置并允许重试', async () => {
    const tab = await openTab();
    const { importConfig } = await vi.importActual<typeof import('./db')>('./db');
    const original = disk.get(KEY);
    const imported = JSON.stringify({ version: 8, state: { customAPIs: [sources[1]] } });
    const config = JSON.stringify({ name: 'LibreTV-Settings', data: { [KEY]: imported } });

    tab.store.getState().addCustomApi(added);
    vi.spyOn(tab.storage, 'setItem').mockImplementationOnce(() => { throw new Error('quota'); });

    await expect(importConfig(config)).rejects.toThrow('无法保存当前设置');
    expect(disk.get(KEY)).toBe(original);
    expect(tab.store.getState().customAPIs).toHaveLength(3);
    await expect(tab.flush()).resolves.toBe(true);
    expect(saved().customAPIs.map(({ name }: { name: string }) => name)).toContain(added.name);
    await importConfig(config);
    expect(saved()).toEqual(JSON.parse(imported).state);
  });

  it.each(['storage', 'flush'])('经由 %s 将待写字段合入旧版设置前先迁移旧标记', async (route) => {
    const tab = await openTab();
    tab.store.getState().updateSettings({ adFilter: false });
    disk.set(KEY, JSON.stringify({
      version: 2,
      state: { skipMarks: { fixture: { introEnd: 12, outroStart: 120 } } },
    }));

    if (route === 'storage') tab.notify();
    await tab.flush();

    const expected = [
      { type: 'opening', start: 0, end: 12 },
      { type: 'ending', start: 120, end: -1 },
    ];
    expect(saved().skipMarks.fixture.segments).toEqual(expected);
    expect(tab.store.getState().skipMarks.fixture.segments).toEqual(expected);
    expect(saved().adFilter).toBe(false);
    expect(JSON.parse(disk.get(KEY)!).version).toBe(8);
  });

  it('旧快照含空直播订阅时保存有效订阅和待写设置', async () => {
    const tab = await openTab();
    const subscription = { url: 'https://example.invalid/list', name: 'Fixture' };
    tab.store.getState().updateSettings({ adFilter: false });
    disk.set(KEY, JSON.stringify({ version: 1, state: {
      liveSubscriptions: [null, subscription], customAPIs: sources,
    } }));
    await expect(tab.flush()).resolves.toBe(true);
    expect(saved().liveSubscriptions).toEqual([{ ...subscription, fromSubscriptions: [] }]);
    expect(saved().customAPIs).toEqual(sources);
    expect(saved().adFilter).toBe(false);
  });

  it('无法读取最新存储时不使用不完整差异覆盖原配置', async () => {
    const a = await openTab();
    a.store.getState().updateSettings({ adFilter: false });
    const fail = vi.spyOn(a.storage, 'getItem').mockImplementationOnce(() => { throw new Error('denied'); });
    await expect(a.flush()).resolves.toBe(false);
    expect(saved().customAPIs).toEqual(sources);
    expect(saved().adFilter).toBe(true);
    await a.flush();
    expect(saved().adFilter).toBe(false);
    fail.mockRestore();
  });

  /**
   * 明确记录该 PR **没有**解决的部分：数组不做并集，同一个顶层字段仍是 last-flush-wins。
   * 标题是 "preserve settings across browser tabs"，用户会读成「不再丢配置」，
   * 所以这条边界要有用例钉住，而不是只写在 PR 描述里。
   */
  it('两个标签各自新增源时仍按后落盘者覆盖（数组不并集）', async () => {
    const a = await openTab();
    const b = await openTab();
    a.store.getState().addCustomApi({ name: 'A 标签加的', url: 'https://a.example/api' });
    await a.flush();
    b.store.getState().addCustomApi({ name: 'B 标签加的', url: 'https://b.example/api' });
    await b.flush();
    // B 的内存里没有 A 的新源（storage 事件未送达），落盘后 A 的那条被覆盖
    expect(saved().customAPIs.map((source: { name: string }) => source.name)).toEqual(['非凡', '量子', 'B 标签加的']);
  });

  /**
   * 单标签场景下，本标签自己的落盘不应再触发一次 rehydrate：
   * 那会在每个 800ms 窗口多一轮全应用订阅者通知，而值并没有任何变化。
   * 直接盯 rehydrate 的调用次数，比数订阅者通知更准（后者会被异步调度干扰）。
   */
  it('本标签自己落盘不再自我 rehydrate，只有磁盘真有外部改动才通知', async () => {
    const a = await openTab();
    const rehydrate = vi.spyOn(a.store.persist, 'rehydrate');

    a.store.getState().recordSourceHealth([{ sourceKey: 'custom_0', ok: true, ms: 100, list: [] }]);
    await a.flush();
    expect(rehydrate).not.toHaveBeenCalled();
    expect(saved().sourceHealth.custom_0.ok).toBe(true);

    // 对照：另一标签真的写了盘，本标签收到 storage 事件时才恢复内存基线
    const b = await openTab();
    b.store.getState().addCustomApi(added);
    await b.flush();
    a.notify();
    expect(rehydrate).toHaveBeenCalled();
    await a.store.persist.rehydrate();
    expect(a.store.getState().customAPIs).toHaveLength(3);
    rehydrate.mockRestore();
  });
});


it('旧版迁移排队后，导入的新片尾标记仍在磁盘上', async () => {
  disk.set(KEY, JSON.stringify({ version: 7, state: { skipMarks: {
    'old:fixture': { segments: [{ kind: 'outro', start: 130, end: 180 }] },
  } } }));
  const tab = await openTab();
  const imported = { 'new:fixture': { segments: [{ kind: 'outro', start: 145, tail: 35 }] } };
  tab.storage.setItem(KEY, JSON.stringify({ version: 8, state: { skipMarks: imported } }));
  await tab.flush();
  expect(saved().skipMarks).toEqual(imported);
});

it('稀疏导入的缺省值在旧标签和新标签一致', async () => {
  const oldTab = await openTab();
  expect(oldTab.store.getState().selectedKeys).toEqual(['custom_0', 'custom_1']);
  oldTab.storage.setItem(KEY, JSON.stringify({ version: 8, state: { customAPIs: [sources[0]] } }));
  oldTab.notify();
  const newTab = await openTab();
  expect(oldTab.store.getState().selectedKeys).toEqual(newTab.store.getState().selectedKeys);
  expect(oldTab.store.getState().selectedKeys).toEqual([]);
});

it('同一源锁排队后，各标签读到上一笔设置并保留各自不同字段', async () => {
  let queue = Promise.resolve();
  const request = vi.fn(<T,>(_name: string, update: () => T) => {
    const next = queue.then(update);
    queue = next.then(() => {});
    return next;
  });
  vi.stubGlobal('navigator', { locks: { request } });
  const a = await openTab();
  const b = await openTab();
  a.store.getState().updateSettings({ adFilter: false });
  b.store.getState().updateSettings({ autoplayNext: false });
  await Promise.all([a.flush(), b.flush()]);
  expect(request).toHaveBeenCalledTimes(2);
  expect(saved().adFilter).toBe(false);
  expect(saved().autoplayNext).toBe(false);
});

it.each(['storage', 'flush'])('导入完成后跳过另一标签待写的旧来源列表（%s）', async (route) => {
  const a = await openTab();
  const b = await openTab();
  b.store.getState().addCustomApi(added);
  await a.replace(JSON.stringify({ version: 8, state: {
    customAPIs: [sources[1]], selectedKeys: [sources[1].key],
  } }));
  if (route === 'storage') b.notify();
  await b.flush();
  expect(saved().customAPIs).toEqual([sources[1]]);
  expect(saved().selectedKeys).toEqual([sources[1].key]);
});

it('页面无法等待写锁就退出时，后续标签恢复已保存的字段', async () => {
  const queued: (() => void)[] = [];
  vi.stubGlobal('navigator', { locks: {
    request: <T,>(_name: string, operation: () => T) =>
      new Promise<T>((resolve) => queued.push(() => resolve(operation()))),
  } });
  const closing = await openTab();
  closing.store.getState().updateSettings({ adFilter: false });
  closing.unload();
  expect(saved().adFilter).toBe(true);
  // The old document closes before its callback runs.
  queued.length = 0;
  const reopened = await openTab();
  expect(reopened.store.getState().adFilter).toBe(false);
  const flushed = reopened.flush();
  queued[0]();
  expect(await flushed).toBe(true);
  expect(saved().adFilter).toBe(false);
  expect([...disk.keys()]).toEqual([KEY]);
});

it('排在前面的旧写入不会覆盖后编辑但先进入日志的字段', async () => {
  const queued: (() => void)[] = [];
  vi.stubGlobal('navigator', { locks: {
    request: <T,>(_name: string, operation: () => T) =>
      new Promise<T>((resolve) => queued.push(() => resolve(operation()))),
  } });
  const old = await openTab();
  const fresh = await openTab();
  old.store.getState().updateSettings({ customImageProxy: 'https://old.example/' });
  const first = old.flush();
  vi.advanceTimersByTime(100);
  fresh.store.getState().updateSettings({ customImageProxy: 'https://new.example/' });
  fresh.unload();
  queued.shift()!();
  await expect(first).resolves.toBe(true);
  queued.shift()!();
  expect(saved().customImageProxy).toBe('https://new.example/');
  expect([...disk.keys()]).toEqual([KEY]);
});

it('无 Web Locks 时，已经开始的旧标签写入无法改写并发导入的配置', async () => {
  vi.stubGlobal('navigator', {});
  const a = await openTab();
  const b = await openTab();
  b.store.getState().addCustomApi(added);
  let pendingImport: Promise<void> | undefined;
  vi.spyOn(b.storage, 'setItem').mockImplementationOnce((key, value) => {
    pendingImport = a.replace(JSON.stringify({ version: 8, state: { customAPIs: [sources[1]] } }));
    disk.set(key, value);
  });
  await b.flush();
  await pendingImport;
  expect(saved().customAPIs).toEqual([sources[1]]);
});
