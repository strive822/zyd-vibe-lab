'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Drawer } from './drawer';
import { Icon } from './icon';
import { useToast } from './toast';
import { db, type DownloadTaskEntry } from '@/lib/db';
import {
  PauseResumeController,
  clearDownloadChunks,
  runDownloadJob,
  supportsChunkCache,
  type DownloadProgress,
} from '@/lib/m3u8-downloader';
import { loadDownloadSettings, saveDownloadSettings } from '@/lib/download-settings';
import {
  detectSavingCapability,
  pickSaveTarget,
  releaseSavedBlob,
  retainSavedBlob,
  triggerBrowserDownload,
  type SaveTarget,
} from '@/lib/download-saver';
import { Switch } from './settings-shared';

/**
 * 全局下载管理器（UI 采用本站 Drawer 模式）：
 * - 入口：header 下载图标 + 播放页「下载本集」（均派发 window 事件）；
 * - 并发：全局最多同时进行 3 个任务，其余排队（waiting）；
 * - 断点：已下载分片写入 Cache Storage（网络层断点）；
 *   保存目标（FS Access / 内存）活不过页面刷新，恢复时由用户点击「继续」重新选择。
 * - 「下载完成」不等于「已保存到设备」：内存聚合只能发起浏览器下载、拿不到回执，
 *   这类任务仅保留近期 Blob 供「保存到设备」。暂存清理或页面刷新后可「重新下载」（issue #977）。
 */

const MAX_CONCURRENT_DOWNLOADS = 3;
/** 进度落库节流间隔：整集动辄上千分片，逐片「写库 + 全量查询 + setState」会把长任务页面拖垮 */
const PROGRESS_PERSIST_INTERVAL_MS = 1000;
const ADD_TASK_EVENT = 'libretv:add-download';
const SHOW_MANAGER_EVENT = 'libretv:show-download-manager';
const TASK_LOCK_PREFIX = 'libretv:download:';
export const DOWNLOADS_UPDATED_EVENT = 'libretv:downloads-updated';

export interface AddDownloadPayload {
  url: string;
  title: string;
  format?: 'TS' | 'MP4';
}

/** 运行中的任务句柄（不进持久化） */
interface RunningHandle {
  attempt?: string;
  abort: AbortController;
  pause: PauseResumeController;
  release: () => void;
  completion?: Promise<void>;
  cancelling?: boolean;
}

interface PendingTarget {
  attempt?: string;
  target: SaveTarget;
  release: () => void;
}

function acquireTaskLock(id: string): Promise<(() => void) | undefined> {
  if (!navigator.locks) return Promise.resolve(() => {});
  return new Promise((resolve) => {
    void navigator.locks.request(TASK_LOCK_PREFIX + id, { ifAvailable: true }, (lock) => {
      if (!lock) { resolve(undefined); return; }
      return new Promise<void>((release) => resolve(release));
    }).catch(() => resolve(undefined));
  });
}

export function DownloadManager({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { toast } = useToast();
  const [tasks, setTasks] = useState<DownloadTaskEntry[]>([]);
  const [capability, setCapability] = useState<'fs-access' | 'memory'>('memory');
  const [chunkCache, setChunkCache] = useState(true);
  const [proxy, setProxy] = useState(false);
  const [lockedTasks, setLockedTasks] = useState<Set<string>>(new Set());
  const running = useRef(new Map<string, RunningHandle>());
  const pendingTargets = useRef(new Map<string, PendingTarget>());
  /**
   * 内存聚合任务完成后的保存目标（taskId → target）。只在本组件生命周期内有效：
   * 页面刷新后 Blob 随之丢失，此时「保存到设备」降级为「重新下载」。
   */
  const savedTargets = useRef(new Map<string, SaveTarget>());

  const refresh = useCallback(() => {
    void db.downloads.orderBy('createdAt').reverse().toArray().then(setTasks).catch(() => {});
    void navigator.locks?.query().then(({ held }) => setLockedTasks(new Set(held
      ?.flatMap(({ name }) => name?.startsWith(TASK_LOCK_PREFIX) ? [name.slice(TASK_LOCK_PREFIX.length)] : []))))
      .catch(() => {});
  }, []);

  const updateEntry = useCallback(async (id: string, patch: Partial<DownloadTaskEntry>) => {
    const updated = await db.downloads.update(id, { ...patch, updatedAt: Date.now() });
    if (!updated) throw new Error('下载任务已删除');
    refresh();
  }, [refresh]);

  // 下载设置在挂载时读取：抽屉关闭时 header / 播放页也会派发入队事件，
  // 若只在打开抽屉时才读，关闭状态下加入的任务会漏掉用户的中转偏好
  useEffect(() => {
    setProxy(loadDownloadSettings().proxy);
  }, []);

  // —— 任务启动：选目标 → runDownloadJob ——
  const startTask = useCallback(
    async (entry: DownloadTaskEntry) => {
      if (running.current.has(entry.id)) return;
      const pending = pendingTargets.current.get(entry.id);
      if (!pending || pending.attempt !== entry.attempt) return;
      const { target, release } = pending;
      pendingTargets.current.delete(entry.id);
      const abort = new AbortController();
      const pause = new PauseResumeController();
      const handle: RunningHandle = { abort, pause, release, attempt: entry.attempt };
      running.current.set(entry.id, handle);
      handle.completion = (async () => {
        let saved = false;
        let claimed = false;
        const savedToDisk = target.kind === 'fs';
        try {
          claimed = Boolean(await db.downloads.where('id').equals(entry.id)
            .and((task) => task.status === 'waiting' && task.attempt === entry.attempt)
            .modify({ status: 'downloading', updatedAt: Date.now() }));
          if (!claimed || abort.signal.aborted) return;
          refresh();
          let lastPersistAt = 0;
          const onProgress = (progress: DownloadProgress) => {
            if (abort.signal.aborted) return;
            const patch = { total: progress.total, finished: progress.current };
            setTasks((previous) => previous.map((task) => task.id === entry.id ? { ...task, ...patch } : task));
            const now = Date.now();
            if (progress.status === 'downloading' && now - lastPersistAt < PROGRESS_PERSIST_INTERVAL_MS) return;
            lastPersistAt = now;
            void db.downloads.update(entry.id, { ...patch, updatedAt: now }).catch(() => {});
          };

          await runDownloadJob({
            taskId: entry.id, url: entry.url, title: entry.title, format: entry.format,
            signal: abort.signal, pause, proxy: loadDownloadSettings().proxy, onProgress, target,
          });
          if (abort.signal.aborted) return;
          saved = true;
          if (!savedToDisk && target.savedUrl()) retainSavedBlob(savedTargets.current, entry.id, target);
          await clearDownloadChunks(entry.id);
          if (abort.signal.aborted) return;
          await updateEntry(entry.id, { status: 'completed', savedToDisk });
          toast(savedToDisk
            ? `《${entry.title}》已保存到所选位置`
            : `《${entry.title}》已生成，请在浏览器下载列表确认；没保存成功可点「保存到设备」`, 'success');
        } catch (err) {
          if (abort.signal.aborted) return;
          if (claimed) await updateEntry(entry.id, { status: 'error' }).catch(() => {});
          toast(`《${entry.title}》下载失败：${err instanceof Error ? err.message : String(err)}`, 'error');
        } finally {
          if (!saved) await target.abort().catch(() => {});
          running.current.delete(entry.id);
          if (!handle.cancelling) release();
          refresh();
          scheduleNext();
        }
      })();
      await handle.completion;
    },
    // scheduleNext 刻意不进依赖：它与 startTask 相互引用，进依赖会让回调每帧重建
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [toast, updateEntry, refresh]
  );

  // —— 全局并发调度 ——
  const scheduleNext = useCallback(() => {
    void (async () => {
      const all = await db.downloads.orderBy('createdAt').toArray();
      for (const entry of all) {
        if (running.current.size >= MAX_CONCURRENT_DOWNLOADS) break;
        if (entry.status === 'waiting' && pendingTargets.current.has(entry.id)) void startTask(entry);
      }
    })().catch(() => {});
  }, [startTask]);

  // —— 事件：新增任务（用户手势内触发，可安全弹文件选择器） ——
  // 监听器必须常驻：播放页「下载本集」在抽屉关闭时也会派发事件，
  // 若仅 isOpen 时注册，事件会凭空丢失——toast 提示了入队，实际什么都没发生
  useEffect(() => {
    const onAdd = (e: Event) => {
      const detail = (e as CustomEvent<AddDownloadPayload>).detail;
      if (!detail?.url || !detail?.title) return;
      // 无 Cache Storage（HTTP 访问 / 老浏览器）时下载必然失败——分片无处暂存。
      // 在入队这一步就讲清楚，别让用户等到任务跑到一半才看到报错
      if (!supportsChunkCache()) {
        toast('当前环境不支持下载缓存（需通过 HTTPS 访问），无法下载', 'error');
        return;
      }
      void (async () => {
        const format = detail.format ?? 'MP4';
        const id = `dl_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
        const entry: DownloadTaskEntry = {
          id,
          url: detail.url,
          title: detail.title,
          format,
          status: 'waiting',
          attempt: id,
          finished: 0,
          total: 0,
          errorNum: 0,
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        // 用户手势内预选保存目标（FS Access 弹窗必须在手势内）
        let target: SaveTarget;
        try {
          target = await pickSaveTarget(`${detail.title}.${format.toLowerCase()}`);
        } catch (err) {
          if (err instanceof Error && err.message.includes('取消')) {
            toast('已取消下载', 'info');
          } else {
            toast('无法选择保存位置，请重试', 'error');
          }
          return;
        }
        const release = await acquireTaskLock(id);
        if (!release) {
          await target.abort().catch(() => {});
          toast('无法锁定下载任务，请重试', 'error');
          return;
        }
        try {
          await db.downloads.put(entry);
        } catch {
          await target.abort().catch(() => {});
          release();
          toast('无法添加下载任务，请重试', 'error');
          return;
        }
        pendingTargets.current.set(id, { target, release, attempt: id });
        refresh();
        scheduleNext();
        toast(`《${detail.title}》已加入下载队列`, 'success');
      })();
    };

    window.addEventListener(ADD_TASK_EVENT, onAdd);
    return () => {
      window.removeEventListener(ADD_TASK_EVENT, onAdd);
    };
  }, [refresh, scheduleNext, toast]);

  // 抽屉打开时：刷新保存能力与任务列表，并启动排队中的任务
  useEffect(() => {
    if (!isOpen) return;
    setCapability(detectSavingCapability());
    setChunkCache(supportsChunkCache());
    // 顺带重读下载设置：多标签页下另一处改了开关也能同步过来
    setProxy(loadDownloadSettings().proxy);
    refresh();
    scheduleNext();
    window.addEventListener('focus', refresh);
    return () => window.removeEventListener('focus', refresh);
  }, [isOpen, refresh, scheduleNext]);

  const queueWithTarget = async (entry: DownloadTaskEntry, patch: Partial<DownloadTaskEntry>): Promise<boolean> => {
    if (pendingTargets.current.has(entry.id)) return false;
    if (!navigator.locks && ['waiting', 'downloading', 'paused'].includes(entry.status)) return false;
    let target: SaveTarget;
    let release: (() => void) | undefined;
    try {
      target = await pickSaveTarget(`${entry.title}.${entry.format.toLowerCase()}`, undefined, async () => {
        release = await acquireTaskLock(entry.id);
        if (!release) throw new Error('另一个标签页正在处理这个任务');
        const current = await db.downloads.get(entry.id);
        if (!current || current.status !== entry.status || current.attempt !== entry.attempt) {
          throw new Error('下载任务已在其他标签页更新');
        }
      });
    } catch (err) {
      release?.();
      toast(err instanceof Error ? err.message : '无法选择保存位置，请重试', 'info');
      refresh();
      return false;
    }
    if (!release) {
      await target.abort().catch(() => {});
      return false;
    }
    const attempt = crypto.randomUUID();
    try {
      const queued = await db.downloads.where('id').equals(entry.id)
        .and((task) => task.status === entry.status && task.attempt === entry.attempt && !running.current.has(entry.id))
        .modify({ ...patch, attempt, status: 'waiting', updatedAt: Date.now() });
      if (!queued) {
        await target.abort().catch(() => {});
        release();
        refresh();
        return false;
      }
    } catch {
      await target.abort().catch(() => {});
      release();
      toast('无法更新下载任务，请重试', 'error');
      return false;
    }
    pendingTargets.current.set(entry.id, { target, release, attempt });
    refresh();
    scheduleNext();
    return true;
  };

  const onToggleProxy = (next: boolean) => {
    // 以落库结果为准回写 state：存储不可用（隐私模式）时 UI 不能假装已保存
    setProxy(saveDownloadSettings({ proxy: next }).proxy);
    toast(
      next ? '已开启下载中转，新任务经服务器转发' : '已关闭下载中转，新任务直连源站',
      'info'
    );
  };

  const onPauseResume = async (entry: DownloadTaskEntry) => {
    const handle = running.current.get(entry.id);
    if (handle && entry.status === 'downloading') {
      handle.pause.pause();
      await updateEntry(entry.id, { status: 'paused' });
      return;
    }
    if (handle && entry.status === 'paused') {
      handle.pause.resume();
      await updateEntry(entry.id, { status: 'downloading' });
      return;
    }
    if (entry.status === 'paused' || entry.status === 'waiting' || entry.status === 'error' || entry.status === 'downloading') {
      // 恢复：需要用户手势内重选保存目标（浏览器限制）
      await queueWithTarget(entry, {});
    }
  };

  /**
   * 重新把内存聚合产物交给浏览器（issue #977）。
   * 浏览器仍然不给落盘回执，所以这里只说「已再次发起保存」，落没落由用户核对；
   * 但代价从「重下整集」降为「再点一次」。
   */
  const onResave = (entry: DownloadTaskEntry) => {
    const target = savedTargets.current.get(entry.id);
    const url = target?.savedUrl();
    if (!target || !url) {
      toast('暂存数据已失效，请重新下载', 'error');
      return;
    }
    triggerBrowserDownload(target, target.filename || `${entry.title}.${entry.format.toLowerCase()}`);
    toast(`已再次把《${entry.title}》交给浏览器保存，请在下载列表中确认`, 'info');
  };

  /** Blob 随页面刷新丢失（内存产物不入库）：在手势内重选保存位置后整集重下 */
  const onRedownload = async (entry: DownloadTaskEntry) => {
    if (await queueWithTarget(entry, { finished: 0 })) {
      const saved = savedTargets.current.get(entry.id);
      if (saved) releaseSavedBlob(saved);
      savedTargets.current.delete(entry.id);
      toast(`《${entry.title}》已重新加入下载队列`, 'success');
    }
  };

  const onCancel = async (entry: DownloadTaskEntry) => {
    const handle = running.current.get(entry.id);
    if (handle?.cancelling) return;
    const pending = pendingTargets.current.get(entry.id);
    if (!navigator.locks && !handle && !pending && ['waiting', 'downloading', 'paused'].includes(entry.status)) {
      toast('请在处理这个任务的标签页取消', 'info');
      return;
    }
    const release = handle?.release ?? pending?.release ?? await acquireTaskLock(entry.id);
    if (!release) {
      toast('请在处理这个任务的标签页取消', 'info');
      refresh();
      return;
    }
    pendingTargets.current.delete(entry.id);
    if (pending) await pending.target.abort().catch(() => {});
    if (handle) {
      handle.cancelling = true;
      handle.abort.abort();
      handle.pause.resume();
      await handle.completion;
    }
    // 记录删掉就没有地方再触发保存了，内存产物随之释放，避免整集字节悬在页面里
    const saved = savedTargets.current.get(entry.id);
    if (saved) {
      releaseSavedBlob(saved);
      savedTargets.current.delete(entry.id);
    }
    try {
      const deleted = await db.transaction('rw', db.downloads, async () => {
        const current = await db.downloads.get(entry.id);
        if (!current) return false;
        if (current.attempt !== (handle ? handle.attempt : pending ? pending.attempt : entry.attempt)) return false;
        if (!navigator.locks && !handle && !pending &&
            (current.status !== entry.status || ['waiting', 'downloading', 'paused'].includes(current.status))) {
          return false;
        }
        await db.downloads.delete(entry.id);
        return true;
      });
      if (!deleted) {
        refresh();
        return;
      }
      await clearDownloadChunks(entry.id);
    } catch {
      toast('无法删除下载任务，请重试', 'error');
      return;
    } finally {
      release?.();
    }
    refresh();
    // 终态（已完成/失败）删的是记录而非终止任务；fs 直写的文件在用户选定的位置，不受影响
    toast(
      saved
        ? `《${entry.title}》已删除记录，未确认保存的暂存内容同时丢弃`
        : entry.status === 'completed' || entry.status === 'error'
          ? `《${entry.title}》已删除下载记录`
          : `《${entry.title}》已取消下载`,
      'info'
    );
  };

  const statusLabel: Record<DownloadTaskEntry['status'], string> = {
    waiting: '排队中',
    downloading: '下载中',
    paused: '已暂停',
    completed: '已完成',
    error: '失败',
  };

  /**
   * 「已完成」只在能确认落盘时说：内存聚合的任务标「已生成，待保存」，
   * 免得浏览器其实没保存、界面却报喜（issue #977）。
   */
  const entryLabel = (t: DownloadTaskEntry) =>
    t.status === 'completed' && t.savedToDisk === false
      ? savedTargets.current.has(t.id) ? '已生成，待保存' : '未确认保存，暂存已清理'
      : statusLabel[t.status];

  return (
    <Drawer open={isOpen} onClose={onClose} title="下载管理" width="max-w-lg">
      <div className="space-y-3">
        <div className="card p-3 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm text-content">经服务器中转下载</p>
            <p className="text-xs text-faint">
              直连被跨域 / 防盗链 / 混合内容拦下时开启：整集流量（含分片与密钥）经服务器转发，
              带宽由部署者承担。仅对之后开始的任务生效。
            </p>
          </div>
          <Switch checked={proxy} onChange={onToggleProxy} label="经服务器中转下载" />
        </div>
        <p className="text-xs text-faint">
          保存能力：{capability === 'fs-access' ? '磁盘直写（边下边存）' : '内存聚合（完成后浏览器下载）'}
          {capability === 'memory' && '，浏览器不回报是否已保存'}
          {chunkCache ? ' · 支持断点续传' : ' · 当前环境无断点缓存（需 HTTPS 访问）'} ·
          同时进行 {Math.min(running.current.size, MAX_CONCURRENT_DOWNLOADS)}/{MAX_CONCURRENT_DOWNLOADS} 个任务
        </p>
        {tasks.length === 0 && (
          <div className="py-10 text-center text-sm text-faint">
            暂无下载任务。在播放页点击「下载本集」开始。
          </div>
        )}
        {tasks.map((t) => (
          <div key={t.id} className="card p-3 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm text-content truncate">{t.title}</p>
                <p className="text-xs text-faint">
                  {t.format.toUpperCase()} · {entryLabel(t)}
                  {t.status === 'downloading' && t.total > 0 ? ` · ${t.finished}/${t.total} 分片` : ''}
                </p>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {t.status === 'downloading' && running.current.has(t.id) && (
                  <button
                    type="button"
                    className="px-2 py-1 rounded bg-chip hover:bg-hover text-xs text-content transition-colors"
                    onClick={() => void onPauseResume(t)}
                  >
                    暂停
                  </button>
                )}
                {!pendingTargets.current.has(t.id) &&
                  (running.current.has(t.id) ? t.status === 'paused' :
                    !lockedTasks.has(t.id) && (t.status === 'error' ||
                      (typeof navigator !== 'undefined' && Boolean(navigator.locks) && t.status !== 'completed'))) && (
                  <button
                    type="button"
                    className="px-2 py-1 rounded bg-chip hover:bg-hover text-xs text-content transition-colors"
                    onClick={() => void onPauseResume(t)}
                  >
                    继续
                  </button>
                )}
                {t.status === 'completed' && t.savedToDisk === false && savedTargets.current.has(t.id) && (
                  <button
                    type="button"
                    className="px-2 py-1 rounded bg-chip hover:bg-hover text-xs text-content transition-colors"
                    onClick={() => onResave(t)}
                  >
                    保存到设备
                  </button>
                )}
                {t.status === 'completed' && t.savedToDisk === false && !savedTargets.current.has(t.id) && (
                  <button
                    type="button"
                    className="px-2 py-1 rounded bg-chip hover:bg-hover text-xs text-content transition-colors"
                    onClick={() => void onRedownload(t)}
                  >
                    重新下载
                  </button>
                )}
                <button
                  type="button"
                  aria-label="删除下载任务"
                  className="p-1.5 rounded bg-chip hover:bg-hover text-content transition-colors"
                  onClick={() => void onCancel(t)}
                >
                  <Icon name="close" className="w-4 h-4" />
                </button>
              </div>
            </div>
            {t.status === 'completed' && t.savedToDisk === false && (
              <p className="text-xs text-faint">
                {savedTargets.current.has(t.id)
                  ? '内存聚合无法确认浏览器是否真的保存：请到浏览器下载列表核对，没保存成功就再点「保存到设备」。'
                  : '请先在浏览器下载列表核对。暂存内容已清理，如未保存需重新下载。'}
              </p>
            )}
            {(t.status === 'downloading' || t.status === 'paused' || t.status === 'completed') && t.total > 0 && (
              <div className="h-1.5 rounded-full bg-chip overflow-hidden">
                <div
                  className="h-full bg-accent transition-all"
                  style={{ width: `${t.total > 0 ? Math.min(100, Math.round((t.finished / t.total) * 100)) : 0}%` }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </Drawer>
  );
}

/** 播放页等处调用：把一集加入下载队列（必须在用户手势内调用） */
export function enqueueDownload(payload: AddDownloadPayload): void {
  window.dispatchEvent(new CustomEvent(ADD_TASK_EVENT, { detail: payload }));
}

/** header 等处调用：打开下载管理器 */
export function requestShowDownloadManager(): void {
  window.dispatchEvent(new CustomEvent(SHOW_MANAGER_EVENT));
}

/** 全局挂载点：根布局渲染一次，监听打开事件 */
export function GlobalDownloadManager() {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const onShow = () => setOpen(true);
    window.addEventListener(SHOW_MANAGER_EVENT, onShow);
    return () => window.removeEventListener(SHOW_MANAGER_EVENT, onShow);
  }, []);
  return <DownloadManager isOpen={open} onClose={() => setOpen(false)} />;
}

