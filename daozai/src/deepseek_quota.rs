//! DeepSeek 官方余额：按币种显示总额，明细区分赠送与充值。
use super::{Snapshot, Window};
use serde_json::Value;

fn money(raw: &str, currency: &str) -> String {
    let symbol = match currency {
        "CNY" => "¥",
        "USD" => "$",
        _ => "",
    };
    let amount = raw.parse::<f64>().ok();
    match (symbol, amount) {
        (symbol, Some(amount)) if !symbol.is_empty() => format!("{symbol}{amount:.2}"),
        (_, Some(amount)) => format!("{amount:.2} {currency}"),
        _ => format!("{raw} {currency}"),
    }
}

pub fn parse(v: &Value) -> Result<Snapshot, String> {
    let infos = v["balance_infos"]
        .as_array()
        .ok_or("服务没有返回余额信息")?;
    // 必要字段校验：`balance_infos:[{}]` 这类空对象不能降级成「有效零余额」（F17）。
    for info in infos {
        if info["currency"].as_str().map(str::trim).unwrap_or_default().is_empty() {
            return Err("余额信息缺少币种，无法判断".into());
        }
        if info["total_balance"].as_str().is_none() {
            return Err("余额信息缺少金额，无法判断".into());
        }
    }
    let available = v["is_available"].as_bool().unwrap_or(true);
    if infos.is_empty() {
        return Err(if available {
            "没有可用的余额信息".into()
        } else {
            "当前账户余额不可用".to_string()
        });
    }
    // 主环优先人民币；没有 CNY 时取接口返回的首个币种。不同币种不求和。
    let first = infos
        .iter()
        .find(|info| info["currency"].as_str() == Some("CNY"))
        .unwrap_or(&infos[0]);
    let currency = first["currency"].as_str().unwrap_or_default();
    let total = first["total_balance"].as_str().unwrap_or("0");
    let mut snapshot = Snapshot {
        plan: if available { "可用".into() } else { "不可用".into() },
        at: chrono::Utc::now().timestamp(),
        ..Default::default()
    };
    snapshot.windows.push(Window {
        label: currency.to_string(),
        seconds: None,
        remaining: if available { 100.0 } else { 0.0 },
        reset: None,
        text: Some(money(total, currency)),
    });
    for info in infos {
        let currency = info["currency"].as_str().unwrap_or_default();
        let granted = info["granted_balance"].as_str().unwrap_or("0");
        let topped = info["topped_up_balance"].as_str().unwrap_or("0");
        snapshot.extra.push(Window {
            label: format!(
                "{currency} · 赠送 {} · 充值 {}",
                money(granted, currency),
                money(topped, currency)
            ),
            seconds: None,
            remaining: 0.0,
            reset: None,
            text: Some(money(
                info["total_balance"].as_str().unwrap_or("0"),
                currency,
            )),
        });
    }
    Ok(snapshot)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cny_balance_wins_the_ring_and_keeps_granted_and_topped_up_details() {
        let snapshot = parse(&serde_json::json!({
            "is_available": true,
            "balance_infos": [{"currency": "CNY", "total_balance": "110.00", "granted_balance": "10.00", "topped_up_balance": "100.00"}]
        }))
        .unwrap();
        assert_eq!(snapshot.windows[0].text.as_deref(), Some("¥110.00"));
        assert_eq!(snapshot.windows[0].label, "CNY");
        assert_eq!(snapshot.extra[0].label, "CNY · 赠送 ¥10.00 · 充值 ¥100.00");
    }

    #[test]
    fn usd_only_and_multi_currency_are_listed_without_summing() {
        let usd = parse(&serde_json::json!({
            "is_available": true,
            "balance_infos": [{"currency": "USD", "total_balance": "12.5", "granted_balance": "0.00", "topped_up_balance": "12.50"}]
        }))
        .unwrap();
        assert_eq!(usd.windows[0].text.as_deref(), Some("$12.50"));

        let multi = parse(&serde_json::json!({
            "is_available": true,
            "balance_infos": [
                {"currency": "USD", "total_balance": "5.00", "granted_balance": "0.00", "topped_up_balance": "5.00"},
                {"currency": "CNY", "total_balance": "20.00", "granted_balance": "20.00", "topped_up_balance": "0.00"}
            ]
        }))
        .unwrap();
        assert_eq!(multi.windows.len(), 1, "主环只显示一个币种");
        assert_eq!(multi.windows[0].text.as_deref(), Some("¥20.00"), "有 CNY 时优先 CNY");
        assert_eq!(multi.extra.len(), 2, "明细逐币种列出，不做换算求和");
    }

    #[test]
    fn zero_balance_is_not_confused_with_a_failed_query() {
        let zero = parse(&serde_json::json!({
            "is_available": true,
            "balance_infos": [{"currency": "CNY", "total_balance": "0.00", "granted_balance": "0.00", "topped_up_balance": "0.00"}]
        }))
        .unwrap();
        assert_eq!(zero.windows[0].text.as_deref(), Some("¥0.00"));
        assert_eq!(zero.windows[0].remaining, 100.0);

        assert!(parse(&serde_json::json!({"is_available": true})).is_err());
        assert!(parse(&serde_json::json!({"is_available": false, "balance_infos": []})).is_err());
        assert!(parse(&serde_json::json!({"is_available": false})).is_err());
    }

    #[test]
    fn unavailable_account_does_not_render_a_full_ring() {
        let snapshot = parse(&serde_json::json!({
            "is_available": false,
            "balance_infos": [{"currency": "CNY", "total_balance": "3.00", "granted_balance": "0.00", "topped_up_balance": "3.00"}]
        }))
        .unwrap();
        assert_eq!(snapshot.windows[0].remaining, 0.0);
        assert_eq!(snapshot.plan, "不可用");
    }
}
