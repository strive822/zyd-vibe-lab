# -*- coding: utf-8 -*-
"""数据源可行性验证脚本（开发前实际验证，需求文档 §3 / §18.1）。

验证目标：
  1. 东方财富（Eastmoney）能否获得 NDX、000905、XAU/USD 三个基准的
     日线历史数据（至少 800 个完整交易日）与最新报价。
  2. 新浪财经作为交叉校验源，核对最新价是否一致。

运行方式（无需任何第三方依赖）：
  python verify_data_sources.py

本脚本只读不写，不作为运行时数据通道，仅作为选源证据。
"""
import csv
import io
import json
import re
import urllib.request
from datetime import datetime, timezone, timedelta

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

REQUIRED_BARS = 800
UT_TOKEN = "fa5fd1943c7b386f172d6893dbfba10b"  # 东财网页端公共令牌（非密钥）
# 本机实测：HTTPS 主域会断连/返回空体，HTTP(80) 与数字子域镜像可用 → 按序回退
KLINE_HOSTS = ["http://push2his.eastmoney.com", "https://92.push2his.eastmoney.com"]
QUOTE_HOSTS = ["http://push2.eastmoney.com", "https://82.push2.eastmoney.com"]
results = []


def record(name, ok, detail):
    results.append((name, ok, detail))
    print(("PASS  " if ok else "FAIL  ") + name + "  |  " + detail)


def http_get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fmt_ts(ts, tz_hours):
    if not ts:
        return "None"
    return datetime.fromtimestamp(int(ts), timezone(timedelta(hours=tz_hours))).strftime("%Y-%m-%d %H:%M")


def check_eastmoney_kline(secid, label, tz_hours=8):
    """日线历史深度与最新一根K线（多端点回退）。"""
    path = (
        f"/api/qt/stock/kline/get?secid={secid}&ut={UT_TOKEN}"
        "&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56"
        "&klt=101&fqt=0&beg=0&end=20500101&lmt=2000"
    )
    last_err = None
    for host in KLINE_HOSTS:
        try:
            data = json.loads(http_get(host + path).decode("utf-8", "replace"))
            d = data.get("data") or {}
            klines = d.get("klines") or []
            rows = []
            for k in klines:
                parts = k.split(",")
                # fields2=f51(date),f52(open),f53(close),f54(high),f55(low),f56(volume)
                try:
                    c = float(parts[2])
                except (ValueError, IndexError):
                    continue
                if c > 0:
                    rows.append((parts[0], c))
            ok = len(rows) >= REQUIRED_BARS
            today = datetime.now(timezone(timedelta(hours=tz_hours))).strftime("%Y-%m-%d")
            detail = (
                f"name={d.get('name')} bars={len(rows)} "
                f"first={rows[0][0] if rows else None} last={rows[-1] if rows else None} "
                f"today_bar={rows[-1][0] == today if rows else None} (today={today})"
            )
            record(f"Eastmoney kline {secid} ({label})", ok, detail)
            return rows
        except Exception as e:  # noqa: BLE001
            last_err = e
    record(f"Eastmoney kline {secid} ({label})", False, f"error={type(last_err).__name__}: {last_err}")
    return []


def check_eastmoney_quote(secid, label, tz_hours=8):
    """最新报价 + 报价时间戳（f86，Unix 秒）（多端点回退）。"""
    path = (
        f"/api/qt/stock/get?secid={secid}&ut={UT_TOKEN}"
        "&invt=2&fltt=2&fields=f43,f57,f58,f59,f60,f86"
    )
    last_err = None
    for host in QUOTE_HOSTS:
        try:
            data = json.loads(http_get(host + path).decode("utf-8", "replace"))
            d = data.get("data") or {}
            price = d.get("f43")
            ts = d.get("f86")
            ok = isinstance(price, (int, float)) and price > 0 and ts
            detail = (
                f"name={d.get('f58')} code={d.get('f57')} price={price} "
                f"prev_close={d.get('f60')} quote_time={fmt_ts(ts, tz_hours)} f86={ts}"
            )
            record(f"Eastmoney quote {secid} ({label})", ok, detail)
            return price, ts
        except Exception as e:  # noqa: BLE001
            last_err = e
    record(f"Eastmoney quote {secid} ({label})", False, f"error={type(last_err).__name__}: {last_err}")
    return None, None


def check_sina_crosscheck():
    """新浪实时行情交叉校验：gb_ndx(纳斯达克100) / sh000905 / hf_XAU(伦敦金)。"""
    url = "https://hq.sinajs.cn/list=gb_ndx,sh000905,hf_XAU"
    try:
        raw = http_get(url, headers={"Referer": "https://finance.sina.com.cn"})
        text = raw.decode("gbk", "replace")
        fields = {}
        for m in re.finditer(r'hq_str_(\w+)="([^"]*)"', text):
            fields[m.group(1)] = m.group(2).split(",")
        ndx = fields.get("gb_ndx", [])
        csi = fields.get("sh000905", [])
        gold = fields.get("hf_XAU", [])
        record(
            "Sina cross-check",
            bool(ndx and csi and gold),
            f"gb_ndx[0..3]={ndx[:4]} | sh000905[0..3]={csi[:4]} | hf_XAU[0..3]={gold[:4]}",
        )
        return {"ndx": ndx, "csi500": csi, "gold": gold}
    except Exception as e:  # noqa: BLE001
        record("Sina cross-check", False, f"error={type(e).__name__}: {e}")
        return {}


def check_stooq_reference():
    """参考信息：Stooq（此前会话记录返回 JS 挑战页，此处仅复核并留档）。"""
    url = "https://stooq.com/q/d/l/?s=xauusd&i=d"
    try:
        text = http_get(url, timeout=15).decode("utf-8", "replace")
        rows = list(csv.DictReader(io.StringIO(text)))
        ok = len(rows) >= REQUIRED_BARS and "Close" in rows[0]
        record("Stooq xauusd (参考)", ok, f"rows={len(rows)} head={text[:60]!r}")
    except Exception as e:  # noqa: BLE001
        record("Stooq xauusd (参考)", False, f"error={type(e).__name__}: {e}")


def main():
    print("=" * 100)
    print("数据源可行性验证  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 100)

    print("\n--- 东方财富：日线历史（要求 >= 800 根完整日线） ---")
    em_ndx = check_eastmoney_kline("100.NDX100", "纳斯达克100")
    em_csi = check_eastmoney_kline("1.000905", "中证500")
    em_gold = check_eastmoney_kline("122.XAU", "黄金/美元 现货")

    print("\n--- 东方财富：最新报价（CurrentPrice 数据通道） ---")
    check_eastmoney_quote("100.NDX100", "纳斯达克100", tz_hours=-4)  # 美东夏令时 EDT
    check_eastmoney_quote("1.000905", "中证500", tz_hours=8)
    check_eastmoney_quote("122.XAU", "黄金/美元 现货", tz_hours=8)

    print("\n--- 新浪财经：交叉校验 ---")
    sina = check_sina_crosscheck()

    print("\n--- 参考核对（非选型依据） ---")
    check_stooq_reference()

    print("\n" + "=" * 100)
    print("交叉校验比对：")
    try:
        if em_ndx and sina.get("ndx"):
            print(f"  NDX100     东财收={em_ndx[-1][1]}  vs 新浪最新={sina['ndx'][1]}")
        if em_csi and sina.get("csi500"):
            print(f"  中证500    东财收={em_csi[-1][1]}  vs 新浪最新={sina['csi500'][3]}")
        if em_gold and sina.get("gold"):
            print(f"  黄金XAU    东财收={em_gold[-1][1]}  vs 新浪最新={sina['gold'][0]}")
    except Exception as e:  # noqa: BLE001
        print(f"  比对失败: {e}")

    print("\n结论汇总：")
    for name, ok, _ in results:
        print(f"  [{'OK ' if ok else 'NG '}] {name}")
    n_ok = sum(1 for _, ok, _ in results if ok)
    print(f"\n通过 {n_ok}/{len(results)}")


if __name__ == "__main__":
    main()
