import { expect, it, vi } from 'vitest';

const protectedFetch = vi.hoisted(() => vi.fn(async () => new Response('protected')));
vi.mock('undici', async (original) => ({ ...await original<typeof import('undici')>(), fetch: protectedFetch }));

it('重载模块后，已安装的包装器仍识别受保护作用域', async () => {
  const regularFetch = vi.fn(async () => new Response('regular'));
  vi.stubGlobal('fetch', regularFetch);
  try {
    await import('./ssrf');
    vi.resetModules();
    const { runWithSSRFProtection } = await import('./ssrf');
    const res = await runWithSSRFProtection({}, () => fetch('https://example.invalid/fixture'));
    expect(await res.text()).toBe('protected');
    expect(protectedFetch).toHaveBeenCalledTimes(1);
    expect(regularFetch).not.toHaveBeenCalled();
  } finally {
    vi.unstubAllGlobals();
  }
});
