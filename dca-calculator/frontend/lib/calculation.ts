/** Read both success and error JSON; reject incomplete weights before showing results. */
export const ASSET_ORDER = ["ndx", "csi500", "gold"] as const;

type Weights = Record<string, number>;
type AssetInfo = { key: string; name: string; data_time: string; source: string };
export type CalculationResponse = {
  c_model: Weights;
  rigorous_model: Weights;
  assets: AssetInfo[];
};

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function validWeights(value: unknown): value is Weights {
  if (!isObject(value) || Object.keys(value).length !== ASSET_ORDER.length) return false;
  const weights = ASSET_ORDER.map((key) => value[key]);
  return weights.every((w) => typeof w === "number" && Number.isFinite(w) && w >= 0 && w <= 1)
    && Math.abs((weights as number[]).reduce((sum, w) => sum + w, 0) - 1) < 1e-9;
}

function validCalculation(value: unknown): value is CalculationResponse {
  if (!isObject(value) || !validWeights(value.c_model) || !validWeights(value.rigorous_model)
    || !Array.isArray(value.assets) || value.assets.length !== ASSET_ORDER.length) return false;
  const assets = value.assets;
  return ASSET_ORDER.every((key) => assets.filter((asset: unknown) =>
    isObject(asset) && asset.key === key
    && ["name", "data_time", "source"].every((field) =>
      typeof asset[field] === "string" && asset[field].trim().length > 0)).length === 1);
}

export async function readCalculationResponse(response: Response): Promise<CalculationResponse> {
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = isObject(body) && typeof body.detail === "string" && body.detail.trim()
      ? body.detail : `请求失败（HTTP ${response.status}）`;
    throw new Error(detail);
  }
  if (!validCalculation(body)) {
    throw new Error("当前无法完成计算：服务返回的数据格式不正确，请重试。");
  }
  return body;
}
