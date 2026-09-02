"use client";

/**
 * 三资产定投权重计算器 —— 桌面端主页面。
 *
 * 行为约定（需求文档 §12）：
 *  - 仅在页面打开/刷新时请求一次 /api/calculation（行情 + 权重）；
 *  - 修改定投金额时只在本地按已有权重重算金额，绝不重新请求行情。
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { formatPercent, formatYuan, splitAmounts } from "@/lib/money";

type Weights = Record<string, number>;

type AssetInfo = {
  key: string;
  name: string;
  data_time: string;
  source: string;
};

type CalculationResponse = {
  c_model: Weights;
  rigorous_model: Weights;
  assets: AssetInfo[];
};

const ASSET_ORDER = ["ndx", "csi500", "gold"] as const;

function parseAmount(text: string): number | null {
  const t = text.trim().replace(/,/g, "");
  if (!t) return null;
  const n = Number(t);
  if (!Number.isFinite(n) || n <= 0) return null;
  return n;
}

export default function Home() {
  const [data, setData] = useState<CalculationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [amountText, setAmountText] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/calculation", { cache: "no-store" });
      const body = res.ok ? await res.json() : null;
      if (!res.ok || !body) {
        const detail =
          body && typeof body.detail === "string"
            ? body.detail
            : `请求失败（HTTP ${res.status}）`;
        setError(detail);
        setData(null);
      } else {
        setData(body as CalculationResponse);
      }
    } catch {
      setError("当前无法完成计算：无法连接本地服务，请确认后端已启动（见 README）。");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const amount = useMemo(() => parseAmount(amountText), [amountText]);
  const amountInvalid = amountText.trim() !== "" && amount === null;

  const assetNames = useMemo(() => {
    const map: Record<string, string> = {};
    data?.assets.forEach((a) => {
      map[a.key] = a.name;
    });
    return map;
  }, [data]);

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <div className="mx-auto max-w-6xl px-10 py-12">
        {/* 标题 */}
        <h1 className="text-center text-3xl font-semibold tracking-tight">
          三资产定投权重计算器
        </h1>

        {/* 总金额输入 */}
        <div className="mt-8 flex flex-col items-center gap-2">
          <div className="flex items-center gap-3">
            <label htmlFor="total-amount" className="text-lg text-slate-600">
              本次定投总金额
            </label>
            <div className="flex items-center rounded-xl border border-slate-300 bg-white px-4 py-2.5 shadow-sm focus-within:border-slate-500 focus-within:ring-2 focus-within:ring-slate-200">
              <span className="mr-1 text-2xl text-slate-400">¥</span>
              <input
                id="total-amount"
                inputMode="decimal"
                value={amountText}
                onChange={(e) => setAmountText(e.target.value)}
                placeholder="1000"
                className="w-56 bg-transparent text-right text-2xl tabular-nums outline-none placeholder:text-slate-300"
              />
            </div>
          </div>
          {amountInvalid && (
            <p className="text-sm text-red-600">请输入大于 0 的有效金额</p>
          )}
          {!amountInvalid && amount === null && (
            <p className="text-sm text-slate-400">输入金额后自动计算各资产应投入金额</p>
          )}
        </div>

        {/* 加载中 */}
        {loading && (
          <div className="mt-16 flex flex-col items-center gap-4 text-slate-500">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-300 border-t-slate-600" />
            <p className="text-lg">正在获取最新行情并计算权重…</p>
          </div>
        )}

        {/* 错误：数据不可靠时明确报错，绝不显示错误权重 */}
        {!loading && error && (
          <div className="mx-auto mt-16 max-w-2xl rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
            <p className="text-lg font-medium text-red-700">{error}</p>
            <button
              onClick={() => void load()}
              className="mt-6 rounded-lg bg-red-600 px-5 py-2 text-white hover:bg-red-700"
            >
              重试
            </button>
          </div>
        )}

        {/* 结果：两模型左右并排 */}
        {!loading && !error && data && (
          <>
            <div className="mt-10 grid grid-cols-2 gap-8">
              {(
                [
                  { title: "C哥模型", weights: data.c_model },
                  { title: "严谨模型", weights: data.rigorous_model },
                ] as const
              ).map((model) => {
                const weights = ASSET_ORDER.map((k) => model.weights[k] ?? 0);
                const amounts =
                  amount !== null ? splitAmounts(amount, weights) : null;
                return (
                  <section
                    key={model.title}
                    className="rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200"
                  >
                    <h2 className="border-b border-slate-100 pb-5 text-center text-xl font-medium text-slate-500">
                      {model.title}
                    </h2>
                    <div className="divide-y divide-slate-100">
                      {ASSET_ORDER.map((key, idx) => (
                        <div key={key} className="py-7 text-center">
                          <div className="text-sm text-slate-500">
                            {assetNames[key] ?? key}
                          </div>
                          {/* 权重：第一视觉重点 */}
                          <div className="mt-2 text-5xl font-bold tabular-nums tracking-tight">
                            {formatPercent(weights[idx])}
                          </div>
                          {/* 金额：第二视觉重点 */}
                          <div className="mt-2.5 text-xl tabular-nums text-slate-500">
                            {amounts ? `¥${formatYuan(amounts[idx])}` : "¥ —"}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="border-t border-slate-100 pt-4 text-center text-sm text-slate-400">
                      权重合计{" "}
                      {formatPercent(weights.reduce((a, b) => a + b, 0))}
                    </div>
                  </section>
                );
              })}
            </div>

            {/* 行情时间：各资产实际参与计算的数据时间 */}
            <div className="mt-10 rounded-xl bg-white px-8 py-5 shadow-sm ring-1 ring-slate-200">
              <div className="flex items-center justify-center gap-10 text-sm">
                <span className="font-medium text-slate-500">数据时间</span>
                {data.assets.map((a) => (
                  <span key={a.key} className="text-slate-500">
                    {a.name}：
                    <span className="ml-1 tabular-nums text-slate-800">
                      {a.data_time}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
