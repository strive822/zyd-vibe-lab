/**
 * 金额分摊与展示格式化。
 *
 * 金额在前端本地计算（不触发任何行情请求）：Amount_i = Total × Weight_i，
 * 采用“最大余额法”分摊到分，保证三项显示金额之和严格等于输入总金额
 * （需求文档 §9 / §16）。
 */

// Keep a precision margin for cents -> floating yuan -> displayed cents round trips.
const MAX_CENTS = Math.floor(Number.MAX_SAFE_INTEGER / 4);

/** Accept positive decimal amounts with at most two places and safe integer cents. */
export function parseAmount(text: string): number | null {
  const value = text.trim().replace(/,/g, "");
  if (!/^(?:\d+(?:\.\d{1,2})?|\.\d{1,2})$/.test(value)) return null;
  const [whole, fraction = ""] = value.split(".");
  const cents = Number(`${whole || "0"}${fraction.padEnd(2, "0")}`);
  const amount = Number(value);
  return Number.isFinite(amount) && amount > 0 && Number.isSafeInteger(cents) && cents <= MAX_CENTS
    && Math.round(amount * 100) === cents
    ? amount : null;
}

/** 按权重把总金额分摊为各资产金额（单位：元，保留 2 位小数语义）。 */
export function splitAmounts(totalYuan: number, weights: number[]): number[] {
  if (!Number.isFinite(totalYuan) || totalYuan <= 0) {
    return weights.map(() => 0);
  }
  const totalCents = Math.round(totalYuan * 100);
  if (!Number.isSafeInteger(totalCents) || totalCents > MAX_CENTS) throw new RangeError("金额超出可精确计算的范围");
  const weightSum = weights.reduce((sum, w) => sum + w, 0);
  if (weights.length === 0 || weights.some((w) => !Number.isFinite(w) || w < 0 || w > 1)
    || Math.abs(weightSum - 1) >= 1e-9) throw new RangeError("权重无效");
  const exact = weights.map((w) => totalCents * (w / weightSum));
  const floors = exact.map((x) => Math.floor(x));
  let leftover = totalCents - floors.reduce((a, b) => a + b, 0);

  // 尾差按“小数部分大者优先”分配 1 分钱；权重相同者保持稳定顺序
  const order = exact
    .map((x, i) => ({ i, remainder: x - floors[i] }))
    .sort((a, b) => b.remainder - a.remainder || a.i - b.i);

  const cents = [...floors];
  let guard = 0;
  while (leftover !== 0 && guard < 10) {
    for (const { i } of order) {
      if (leftover === 0) break;
      if (leftover > 0) {
        cents[i] += 1;
        leftover -= 1;
      } else if (cents[i] > 0) {
        cents[i] -= 1; // 浮点极端情况的负尾差兜底
        leftover += 1;
      }
    }
    guard += 1;
  }
  return cents.map((c) => c / 100);
}

/** 金额展示：千分位 + 固定 2 位小数，如 1,234.56 */
export function formatYuan(value: number): string {
  return value.toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/** 权重展示：固定 2 位小数百分数，如 35.27% */
export function formatPercent(weight: number): string {
  return `${(weight * 100).toFixed(2)}%`;
}
