//! 智谱 GLM Coding 套餐的周期额度：只读额度上限，不接钱包余额。
use super::{number, Snapshot, Window};
use chrono::DateTime;
use serde_json::Value;

/// 接口的重置时间可能是秒或毫秒；无法识别时留空，不编造。
fn reset_ms(v: &Value) -> Option<i64> {
    let raw = v.as_i64()?;
    if raw <= 0 {
        return None;
    }
    let seconds = if raw > 1_000_000_000_000 { raw / 1000 } else { raw };
    DateTime::from_timestamp(seconds, 0).map(|_| seconds)
}

/// `number` × 单位。真实返回见过 (5, 3) 与 (1, 6)；未知单位不猜，交给调用方回落。
fn window_seconds(count: i64, unit: i64) -> Option<i64> {
    let unit_seconds = match unit { 3 => 3_600, 6 => 604_800, _ => return None };
    (count > 0).then(|| count * unit_seconds)
}

pub fn parse(v: &Value) -> Result<Snapshot, String> {
    let limits = v
        .pointer("/data/limits")
        .and_then(Value::as_array)
        .ok_or("服务没有返回额度信息")?;
    let mut snapshot = Snapshot {
        plan: "GLM Coding".into(),
        at: chrono::Utc::now().timestamp(),
        ..Default::default()
    };
    for item in limits {
        let Some(used) = number(&item["percentage"]) else {
            continue;
        };
        // 真实接口用 number/unit 表示周期（3=小时、6=周）；按 Codex 的周期文案展示。
        let seconds = item["number"].as_i64().zip(item["unit"].as_i64()).and_then(|(count, unit)| window_seconds(count, unit))
            .or_else(|| match item["type"].as_str() {
                Some("TOKENS_LIMIT") => Some(18_000),
                Some("TIME_LIMIT") => Some(2_592_000),
                _ => None,
            });
        let label = match seconds {
            Some(seconds) => super::cadence(Some(seconds)),
            None => item["type"].as_str().map(str::to_string).unwrap_or_else(|| "额度周期".into()),
        };
        snapshot.windows.push(Window {
            label,
            seconds,
            remaining: (100.0 - used).clamp(0.0, 100.0) as f32,
            reset: reset_ms(&item["nextResetTime"]),
            text: None,
        });
    }
    if snapshot.windows.is_empty() {
        return Err("服务未提供周期额度，暂不绘制进度".into());
    }
    snapshot
        .windows
        .sort_by_key(|w| w.seconds.unwrap_or(i64::MAX));
    Ok(snapshot)
}

#[cfg(test)]
mod tests {
    use super::*;


    #[test]
    fn real_payload_number_and_unit_render_like_codex() {
        let snapshot = parse(&serde_json::json!({
            "code": 200,
            "data": {"level": "lite", "limits": [
                {"currentValue": 0, "number": 5, "percentage": 0, "remaining": 2000, "type": "CREDIT_LIMIT", "unit": 3, "usage": 2000},
                {"currentValue": 6531, "nextResetTime": 1_793_855_307_999i64, "number": 1, "percentage": 65, "remaining": 3468, "type": "CREDIT_LIMIT", "unit": 6, "usage": 10000}
            ]}
        })).unwrap();
        assert_eq!(snapshot.windows.len(), 2);
        assert_eq!(snapshot.windows[0].label, "5 小时");
        assert_eq!(snapshot.windows[0].remaining, 100.0);
        assert_eq!(snapshot.windows[1].label, "本周");
        assert_eq!(snapshot.windows[1].remaining, 35.0);
        assert_eq!(snapshot.windows[1].reset, Some(1_793_855_307), "毫秒重置时间应换成秒");
    }

    #[test]
    fn five_hour_and_monthly_limits_keep_their_own_reset_times() {
        let snapshot = parse(&serde_json::json!({
            "code": 200,
            "data": {"limits": [
                {"type": "TOKENS_LIMIT", "percentage": 37.5, "nextResetTime": 1_900_000_000_000i64},
                {"type": "TIME_LIMIT", "percentage": 12.0, "currentValue": 36, "usage": 300}
            ]}
        }))
        .unwrap();
        assert_eq!(snapshot.windows.len(), 2);
        assert_eq!(snapshot.windows[0].label, "5 小时");
        assert_eq!(snapshot.windows[0].remaining, 62.5);
        assert!(snapshot.windows[0].reset.is_some(), "毫秒时间戳应换算成秒");
        assert_eq!(snapshot.windows[1].label, "30 天");
        assert_eq!(snapshot.windows[1].remaining, 88.0);
        assert_eq!(snapshot.windows[1].reset, None, "接口没给重置时间就应留空");
        assert_eq!(snapshot.rings().len(), 2, "主环优先 5 小时周期");
        assert_eq!(snapshot.rings()[0].label, "5 小时");
    }

    #[test]
    fn numbers_may_arrive_as_strings_and_unknown_types_stay_visible() {
        let snapshot = parse(&serde_json::json!({
            "data": {"limits": [{"type": "TOKENS_LIMIT", "percentage": "100"}, {"type": "CUSTOM", "percentage": 0}]}
        }))
        .unwrap();
        assert_eq!(snapshot.windows[0].remaining, 0.0);
        assert_eq!(snapshot.windows[1].label, "CUSTOM");
        assert_eq!(snapshot.windows[1].remaining, 100.0);
    }

    #[test]
    fn missing_or_malformed_payloads_are_reported_instead_of_faked() {
        for payload in [
            serde_json::json!({}),
            serde_json::json!({"data": {}}),
            serde_json::json!({"data": {"limits": []}}),
            serde_json::json!({"data": {"limits": [{"type": "TOKENS_LIMIT"}]}}),
        ] {
            assert!(parse(&payload).is_err(), "无法解析时应报错：{payload}");
        }
    }
}
