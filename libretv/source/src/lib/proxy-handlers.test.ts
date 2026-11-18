import { afterEach, describe, expect, it, vi } from 'vitest';
import { handleLiveStreamRequest, handleProxyRequest } from './proxy-handlers';

const { cancelStalledPlaylist } = vi.hoisted(() => ({
  cancelStalledPlaylist: vi.fn(() => new Promise<void>(() => {})),
}));

vi.mock('@/lib/api-guard', () => ({
  guardRequest: () => null,
  jsonError: (error: string, status: number) => Response.json({ error }, { status }),
}));

vi.mock('@/lib/ssrf', () => ({
  checkLiveUrlAllowed: async () => ({ ok: true }),
  isBlockedByDNS: async () => false,
  isValidProxyUrl: () => true,
}));

vi.mock('@/lib/fetch-utils', () => ({
  fetchWithSafeRedirects: async (url: string) => {
    const target = new URL(url);
    const name = target.pathname;
    if (name === '/short.ts') {
      return { finalUrl: url, res: new Response('bytes', { headers: { 'Content-Type': 'video/mp2t' } }) };
    }
    if (name === '/stalled.m3u8' || name === '/rejected.m3u8') {
      const stalled = new ReadableStream({ cancel: cancelStalledPlaylist });
      return { finalUrl: url, res: new Response(stalled, {
        status: name === '/rejected.m3u8' ? 403 : 200,
        headers: { 'Content-Type': 'application/vnd.apple.mpegurl' },
      }) };
    }
    const text = name === '/master.m3u8'
      ? ['#EXTM3U', '#EXT-X-DEFINE:NAME="part",VALUE="short"',
        `#EXT-X-DEFINE:NAME="signed",VALUE="${'q'.repeat(4500)}${target.searchParams.get('fixture') ?? ''}"`,
        '#EXT-X-STREAM-INF:BANDWIDTH=1000', 'first.m3u8',
        '#EXT-X-STREAM-INF:BANDWIDTH=2000', 'second.m3u8'].join('\n')
      : ['#EXTM3U', '#EXT-X-DEFINE:IMPORT="signed"', '#EXT-X-DEFINE:IMPORT="part"',
        '#EXTINF:4,', '{$part}.ts', '#EXT-X-ENDLIST'].join('\n');
    return { finalUrl: url, res: new Response(text, { headers: { 'Content-Type': 'application/vnd.apple.mpegurl' } }) };
  },
}));

const SITE = 'https://app.example';
const UPSTREAM = 'https://cdn.example.com/master.m3u8';
const MINUTE = 60_000;

afterEach(() => vi.restoreAllMocks());

describe.each([
  { path: '/api/proxy', handle: handleProxyRequest },
  { path: '/api/live/stream', handle: handleLiveStreamRequest },
])('HLS references at $path', ({ path, handle }) => {
  const request = (uri: string) => {
    const url = new URL(uri, SITE);
    return handle(new Request(url), url.searchParams.get('url')!);
  };

  it('preserves the exact parent across a long playback with locally cached fragments', async () => {
    const clock = vi.spyOn(Date, 'now').mockReturnValue(0);
    const master = await request(path + '?url=' + encodeURIComponent(UPSTREAM));
    const variants = (await master.text()).split('\n').filter(line => line.startsWith('/'));
    const contextId = new URL(variants[0], SITE).searchParams.get('hls-context');
    expect(contextId).toBeTruthy();

    const first = await request(variants[0]);
    const segment = (await first.text()).split('\n').find(line => line.startsWith('/'))!;
    expect(new URL(segment, SITE).searchParams.get('hls-context')).toBe(contextId);
    expect(new URL(segment, SITE).searchParams.get('url')).toBe('https://cdn.example.com/short.ts');

    clock.mockReturnValue(130 * MINUTE);
    const second = await request(variants[1]);
    expect(second.status).toBe(200);
    expect(await second.text()).toContain(`NAME="signed",VALUE="${'q'.repeat(4500)}"`);
  });

  it('returns a reload response without reading a stalled playlist when the parent was lost', async () => {
    cancelStalledPlaylist.mockClear();
    const res = await request(path + '?url=' + encodeURIComponent('https://cdn.example.com/stalled.m3u8') +
      '&hls-context=lost-fixture');
    expect(res.status).toBe(502);
    expect(res.headers.get('cache-control')).toBe('no-store');
    expect(await res.text()).toContain('请重新加载');
    expect(cancelStalledPlaylist).toHaveBeenCalledOnce();
  });
});

it('returns the live upstream error without waiting for body cancellation to finish', async () => {
  cancelStalledPlaylist.mockClear();
  const upstream = 'https://cdn.example.com/rejected.m3u8';
  const res = await handleLiveStreamRequest(new Request(SITE + '/api/live/stream?url=' + encodeURIComponent(upstream)), upstream);
  expect(res.status).toBe(403);
  expect(res.headers.get('x-live-upstream-status')).toBe('403');
  expect(res.headers.get('cache-control')).toBe('no-store');
  expect(cancelStalledPlaylist).toHaveBeenCalledOnce();
});

it('evicts the least recently used parent while allowing already-expanded fragments to load', async () => {
  const request = (uri: string) => {
    const url = new URL(uri, SITE);
    return handleProxyRequest(new Request(url), url.searchParams.get('url')!);
  };
  const loadMaster = async (fixture: number) => {
    const master = await request('/api/proxy?url=' + encodeURIComponent(UPSTREAM + '?fixture=' + fixture));
    return (await master.text()).split('\n').find(line => line.startsWith('/'))!;
  };

  const kept = await loadMaster(0);
  const evicted = await loadMaster(1);
  const firstVariant = await request(evicted);
  const oldSegment = (await firstVariant.text()).split('\n').find(line => line.startsWith('/'))!;
  for (let i = 2; i < 500; i++) await loadMaster(i);
  const keptVariant = await request(kept);
  const segment = (await keptVariant.text()).split('\n').find(line => line.startsWith('/'))!;
  await loadMaster(500);
  expect(await (await request(segment)).text()).toBe('bytes');
  expect((await request(kept)).status).toBe(200);
  expect((await request(evicted)).status).toBe(502);
  expect(await (await request(oldSegment)).text()).toBe('bytes');
});
