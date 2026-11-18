/**
 * download-saver 的行为测试（issue #977）。
 *
 * 承重的是「发起下载」与「已落盘」之间的区别：浏览器对 `a.click()` 不给回执，
 * 所以内存模式必须留住可重放的产物，同时不能把取消/空产物发给浏览器。
 * 这里不引 jsdom，只 stub 模块真正用到的那几个全局：
 * document.createElement/body.appendChild、URL.createObjectURL/revokeObjectURL、window.confirm。
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  UserCancelledError,
  createMemoryTarget,
  detectSavingCapability,
  pickSaveTarget,
  releaseSavedBlob,
  retainSavedBlob,
  type SaveTarget,
  triggerBrowserDownload,
} from './download-saver';

interface AnchorStub {
  tag: string;
  href: string;
  download: string;
  rel: string;
  clicks: number;
  removes: number;
  click(): void;
  remove(): void;
}

const anchors: AnchorStub[] = [];
const appended: AnchorStub[] = [];
let createObjectURL = vi.fn(() => 'blob:generated-1');
let revokeObjectURL = vi.fn();

function anchor(): AnchorStub {
  const self: AnchorStub = {
    tag: 'a',
    href: '',
    download: '',
    rel: '',
    clicks: 0,
    removes: 0,
    click: () => { self.clicks += 1; },
    remove: () => { self.removes += 1; },
  };
  return self;
}

beforeEach(() => {
  anchors.length = 0;
  appended.length = 0;
  createObjectURL = vi.fn(() => 'blob:generated-1');
  revokeObjectURL = vi.fn();

  const doc = {
    body: { appendChild: (node: AnchorStub) => { appended.push(node); anchors.push(node); } },
    createElement: (tag: string) => { const a = anchor(); a.tag = tag; return a; },
  };
  vi.stubGlobal('document', doc);
  vi.stubGlobal('window', { confirm: vi.fn(() => true) });
  const urlCtor = URL as unknown as { createObjectURL: unknown; revokeObjectURL: unknown };
  urlCtor.createObjectURL = createObjectURL;
  urlCtor.revokeObjectURL = revokeObjectURL;
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
  const urlCtor = URL as unknown as { createObjectURL?: unknown; revokeObjectURL?: unknown };
  delete urlCtor.createObjectURL;
  delete urlCtor.revokeObjectURL;
});

const chunk = (bytes = 4) => new Uint8Array(bytes).fill(7);

it('文件选择后、打开写入流前拒绝被其他标签占用的任务', async () => {
  const createWritable = vi.fn();
  Object.assign(window, { showSaveFilePicker: async () => ({ createWritable }) });
  await expect(pickSaveTarget('a.mp4', undefined, async () => {
    throw new Error('任务占用中');
  })).rejects.toThrow('任务占用中');
  expect(createWritable).not.toHaveBeenCalled();
});

describe('内存聚合：产物可重放', () => {
  it('close() 生成一次 Blob 并发起一次下载，文件名沿用建议名', async () => {
    const target = await pickSaveTarget('盗梦空间.mp4');
    expect(target.kind).toBe('memory');
    expect(target.filename).toBe('盗梦空间.mp4');
    expect(target.savedUrl()).toBeNull(); // 还没生成，界面此时不该给「保存到设备」

    await target.write(chunk());
    await target.write(chunk());
    await target.close();

    expect(createObjectURL).toHaveBeenCalledTimes(1);
    expect(anchors).toHaveLength(1);
    expect(anchors[0].clicks).toBe(1);
    expect(anchors[0].download).toBe('盗梦空间.mp4');
    expect(target.savedUrl()).toBe('blob:generated-1');
  });

  it('重复 close() 幂等：不再复制字节，也不再向浏览器重复投递', async () => {
    const target = await pickSaveTarget('a.mp4');
    await target.write(chunk());
    await target.close();
    await target.close();

    expect(createObjectURL).toHaveBeenCalledTimes(1);
    expect(anchors).toHaveLength(1);
    expect(anchors[0].clicks).toBe(1);
  });

  it('锚点延后一帧再摘除：同步 remove 会被部分引擎当成取消下载', async () => {
    vi.useFakeTimers();
    const target = await pickSaveTarget('a.mp4');
    await target.write(chunk());
    await target.close();

    expect(anchors[0].removes).toBe(0);
    vi.advanceTimersByTime(0);
    expect(anchors[0].removes).toBe(1);
  });

  it('「保存到设备」复用同一个 objectURL，不需要重新生成产物', async () => {
    const target = await pickSaveTarget('a.mp4');
    await target.write(chunk());
    await target.close();
    const url = target.savedUrl();
    expect(url).toBeTruthy();

    triggerBrowserDownload(target);
    triggerBrowserDownload(target);

    expect(createObjectURL).toHaveBeenCalledTimes(1); // 只有 close() 那次
    expect(anchors).toHaveLength(3); // 首次 + 两次重放
    expect(anchors[1].href).toBe(url);
    expect(anchors[2].href).toBe(url);
  });

  it('abort() 之后 close() 不产出：取消不该把空文件发给浏览器', async () => {
    const target = await pickSaveTarget('a.mp4');
    await target.write(chunk());
    await target.abort();
    await target.close();

    expect(createObjectURL).not.toHaveBeenCalled();
    expect(anchors).toHaveLength(0);
    expect(target.savedUrl()).toBeNull();
  });

  it('超过阈值先征求确认：拒绝即失败且不落产物，同意则继续产出', async () => {
    const confirm = (window as unknown as { confirm: ReturnType<typeof vi.fn> }).confirm;

    const denied = createMemoryTarget('big.mp4', 8);
    confirm.mockReturnValueOnce(false);
    await expect(denied.write(new Uint8Array(10).fill(1))).rejects.toThrow('内存超限');
    expect(confirm).toHaveBeenCalledTimes(1);
    expect(anchors).toHaveLength(0);

    const accepted = createMemoryTarget('big.mp4', 8);
    confirm.mockReturnValueOnce(true);
    await expect(accepted.write(new Uint8Array(10).fill(1))).resolves.toBeUndefined();
    await accepted.close();
    expect(anchors).toHaveLength(1);
  });

  it('完成的内存产物超过预算时移出较旧文件，给已发起的保存留出读取时间', async () => {
    vi.useFakeTimers();
    createObjectURL.mockReturnValueOnce('blob:first').mockReturnValueOnce('blob:second');
    const retained = new Map<string, SaveTarget>();
    const first = createMemoryTarget('first.mp4');
    const second = createMemoryTarget('second.mp4');
    await first.write(chunk(5));
    await second.write(chunk(6));
    await first.close();
    retainSavedBlob(retained, 'first', first, 10);
    await second.close();
    retainSavedBlob(retained, 'second', second, 10);
    expect([...retained.keys()]).toEqual(['second']);
    expect(revokeObjectURL).not.toHaveBeenCalled();
    vi.advanceTimersByTime(60_000);
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:first');
    expect(second.savedUrl()).toBe('blob:second');
  });

  it('releaseSavedBlob 无产物时不 revoke，有产物时把 objectURL 交还浏览器', async () => {
    vi.useFakeTimers();
    const target = createMemoryTarget('a.mp4');
    releaseSavedBlob(target); // 还没生成：不该 revoke 一个不存在的 URL
    expect(revokeObjectURL).not.toHaveBeenCalled();

    await target.write(chunk());
    await target.close();
    vi.advanceTimersByTime(60_000);
    // 调用方（下载面板）release 之后即丢弃对该 target 的引用，所以这里只发生一次
    releaseSavedBlob(target);
    expect(revokeObjectURL).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:generated-1');
  });

  it('重存后删除任务时以最近一次保存为准延迟撤销', async () => {
    vi.useFakeTimers();
    const target = createMemoryTarget('a.mp4');
    await target.write(chunk());
    await target.close();
    vi.advanceTimersByTime(59_000);
    triggerBrowserDownload(target);
    releaseSavedBlob(target);
    vi.advanceTimersByTime(59_000);
    expect(revokeObjectURL).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1_000);
    expect(revokeObjectURL).toHaveBeenCalledExactlyOnceWith('blob:generated-1');
  });

  it('系统时钟向前调整不会跳过浏览器下载宽限期', async () => {
    vi.useFakeTimers({ toFake: ['Date', 'performance', 'setTimeout'] });
    const target = createMemoryTarget('a.mp4');
    await target.write(chunk());
    await target.close();
    vi.setSystemTime(Date.now() + 600_000);
    releaseSavedBlob(target);
    vi.advanceTimersByTime(59_999);
    expect(revokeObjectURL).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(revokeObjectURL).toHaveBeenCalledExactlyOnceWith('blob:generated-1');
  });
});

describe('磁盘直写：没有可重放的产物', () => {
  it('fs 目标 savedUrl 恒为 null，写入与关闭都走文件句柄', async () => {
    const writes: Uint8Array[] = [];
    let closed = 0;
    vi.stubGlobal('window', {
      showSaveFilePicker: vi.fn(async () => ({
        // 真实链路：handle.createWritable() 返回流，流的 getWriter() 是同步的
        createWritable: async () => ({
          getWriter: () => ({
            write: async (d: Uint8Array) => { writes.push(d); },
            close: async () => { closed += 1; },
            abort: async () => {},
          }),
        }),
      })),
    });

    const target = await pickSaveTarget('a.mp4');
    expect(target.kind).toBe('fs');
    await target.write(chunk(3));
    await target.close();

    expect(writes).toHaveLength(1);
    expect(closed).toBe(1);
    expect(target.savedUrl()).toBeNull();
    expect(createObjectURL).not.toHaveBeenCalled();
    expect(anchors).toHaveLength(0);
  });

  it('用户在文件选择器里取消 → UserCancelledError，不静默转内存模式', async () => {
    const abortError = new DOMException('cancelled', 'AbortError');
    vi.stubGlobal('window', { showSaveFilePicker: vi.fn(async () => { throw abortError; }) });
    await expect(pickSaveTarget('a.mp4')).rejects.toBeInstanceOf(UserCancelledError);
  });

  it('保存能力探测跟随环境：有 showSaveFilePicker 才算 fs-access', async () => {
    expect(detectSavingCapability()).toBe('memory');
    vi.stubGlobal('window', { showSaveFilePicker: vi.fn() });
    expect(detectSavingCapability()).toBe('fs-access');
  });
});
