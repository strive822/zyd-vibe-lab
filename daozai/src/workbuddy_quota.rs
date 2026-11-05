//! WorkBuddy 积分：计费请求头经本机 DPAPI 保存，只发给计费服务。
//!
//! 端点为待核对项（`copilot.tencent.com/v2/billing/meter/get-user-resource`）。
//! 官网字段可能变化，因此解析按常见命名容错；拿不到积分就报错，不把失败画成 0。
use super::{Snapshot, Window};
use serde_json::Value;

pub(crate) const ENDPOINT: &str =
    "https://www.workbuddy.cn/billing/meter/get-user-resource-summary";

/// 只接受 Cookie / Authorization 两种头，其余行忽略，避免把无关 Cookie 发出去。
pub(crate) fn normalize(raw: &str) -> Result<String, String> {
    let mut kept = Vec::new();
    let mut has_auth = false;
    for line in raw.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let Some((name, value)) = line.split_once(':') else {
            return Err("请粘贴「名称: 值」形式的请求头".into());
        };
        if value.trim().is_empty() {
            return Err(format!("请求头 {} 没有值", name.trim()));
        }
        // 认证头至少要有 Cookie 或 Authorization；只有 x-client-platform 不算连接（F17）。
        match name.trim().to_ascii_lowercase().as_str() {
            "cookie" | "authorization" => {
                has_auth = true;
                kept.push(format!("{}: {}", name.trim(), value.trim()))
            }
            "x-client-platform" => kept.push(format!("{}: {}", name.trim(), value.trim())),
            _ => {}
        }
    }
    if !has_auth {
        return Err("请粘贴包含 Cookie 或 Authorization 的计费请求头".into());
    }
    Ok(kept.join("\n"))
}

pub(crate) fn header_pairs(raw: &str) -> Vec<(String, String)> {
    raw.lines()
        .filter_map(|line| line.split_once(':'))
        .map(|(name, value)| (name.trim().to_string(), value.trim().to_string()))
        .collect()
}

fn blob_path(id: &str) -> std::path::PathBuf {
    crate::model::config_dir().join(format!("workbuddy-{id}.bin"))
}

pub(crate) fn store_header(id: &str, raw: &str) -> Result<(), String> {
    let header = normalize(raw)?;
    let blob = protect(header.as_bytes())?;
    crate::model::atomic_write(&blob_path(id), &blob).map_err(|_| "无法保存计费请求头".to_string())
}

pub(crate) fn load_header(id: &str) -> Result<String, String> {
    let raw = std::fs::read(blob_path(id)).map_err(|_| "没有保存计费请求头".to_string())?;
    let plain = unprotect(&raw)?;
    String::from_utf8(plain).map_err(|_| "保存的请求头已损坏".to_string())
}

pub(crate) fn forget_header(id: &str) {
    let _ = std::fs::remove_file(blob_path(id));
}

fn find_number(value: &Value, keys: &[&str]) -> Option<f64> {
    keys.iter().find_map(|key| {
        let raw = value.get(*key)?;
        raw.as_f64()
            .or_else(|| raw.as_str()?.trim().parse().ok())
            .filter(|number| number.is_finite())
    })
}

fn find_text(value: &Value, keys: &[&str]) -> Option<String> {
    keys.iter().find_map(|key| {
        let raw = value.get(*key)?;
        raw.as_str()
            .map(str::trim)
            .filter(|text| !text.is_empty())
            .map(str::to_owned)
    })
}

fn points_text(points: f64) -> String {
    if (points.fract()).abs() < f64::EPSILON {
        format!("{points:.0}")
    } else {
        format!("{points:.1}")
    }
}

/// 成功、零积分与失败必须分开：没有积分字段算失败，积分恰好为 0 是有效快照。
///
/// 官网真实返回：`data.TotalCredits` + `data.CreditGroups[]` + `data.SubscriptionPackageName`。
pub(crate) fn parse(value: &Value) -> Result<Snapshot, String> {
    if let Some(code) = value.get("code").or_else(|| value.get("errcode")).and_then(Value::as_i64) {
        if code != 0 {
            let message = value.get("message").or_else(|| value.get("msg")).and_then(Value::as_str).unwrap_or("计费服务返回错误");
            return Err(format!("{message}（{code}）"));
        }
    }
    if value.get("success").and_then(Value::as_bool) == Some(false) {
        return Err("计费请求未通过，请重新粘贴请求头".into());
    }
    let data = value.get("data").filter(|data| data.is_object()).unwrap_or(value);
    let points = find_number(data, &["TotalCredits", "totalCredits", "points", "remaining_points", "remain_points", "available_points", "left_points", "total_points", "balance", "credit", "score"])
        .ok_or_else(|| "计费服务没有返回积分".to_string())?;
    if points < 0.0 {
        return Err("计费服务返回了无效的积分".into());
    }
    let plan = find_text(data, &["SubscriptionPackageName", "subscriptionPackageName", "plan_name", "package_name", "plan", "package", "product_name", "tier", "resource_name"]).unwrap_or_default();
    let mut snapshot = Snapshot {
        plan: if plan.is_empty() { "WorkBuddy".into() } else { plan.clone() },
        at: chrono::Utc::now().timestamp(),
        ..Default::default()
    };
    snapshot.windows.push(Window {
        label: "积分".into(),
        seconds: None,
        remaining: if points > 0.0 { 100.0 } else { 0.0 },
        reset: None,
        text: Some(points_text(points)),
    });
    // 明细：额度分组（套餐基础/赠送/购买/平台奖励），每组给出剩余与总量。
    if let Some(groups) = data.get("CreditGroups").and_then(Value::as_array) {
        for group in groups {
            let remain = find_number(group, &["CycleRemainCapacity", "remaining"]);
            let total = find_number(group, &["CycleTotalCapacity", "total"]);
            let name = find_text(group, &["Name", "name"]).unwrap_or_default();
            let (Some(remain), Some(total)) = (remain, total) else { continue };
            if total <= 0.0 && remain <= 0.0 { continue; }
            let percent = if total > 0.0 { (remain / total * 100.0).clamp(0.0, 100.0) as f32 } else { 0.0 };
            snapshot.extra.push(Window {
                label: format!("{} · 共 {}", if name.is_empty() { "积分" } else { &name }, points_text(total)),
                seconds: None,
                remaining: percent,
                reset: None,
                text: Some(points_text(remain)),
            });
        }
    }
    if snapshot.extra.is_empty() {
        let total = find_number(data, &["Total", "total", "quota", "limit", "monthly_points"]).filter(|total| *total > 0.0);
        match total {
            Some(total) => snapshot.extra.push(Window {
                label: format!("套餐 {} · 共 {}", if plan.is_empty() { "WorkBuddy" } else { &plan }, points_text(total)),
                seconds: None,
                remaining: (points / total * 100.0).clamp(0.0, 100.0) as f32,
                reset: None,
                text: Some(points_text(points)),
            }),
            None if !plan.is_empty() => snapshot.extra.push(Window { label: format!("套餐 {plan}"), seconds: None, remaining: 0.0, reset: None, text: None }),
            None => {}
        }
    }
    Ok(snapshot)
}

#[cfg(windows)]
fn protect(plain: &[u8]) -> Result<Vec<u8>, String> {
    use windows::Win32::Security::Cryptography::{
        CryptProtectData, CRYPTPROTECT_UI_FORBIDDEN, CRYPT_INTEGER_BLOB,
    };
    let input = CRYPT_INTEGER_BLOB {
        cbData: plain.len() as u32,
        pbData: plain.as_ptr() as *mut u8,
    };
    let mut output = CRYPT_INTEGER_BLOB::default();
    unsafe {
        CryptProtectData(
            &input,
            None,
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            &mut output,
        )
    }
    .map_err(|_| "无法加密请求头（DPAPI）".to_string())?;
    let bytes =
        unsafe { std::slice::from_raw_parts(output.pbData, output.cbData as usize) }.to_vec();
    unsafe {
        windows::Win32::Foundation::LocalFree(windows::Win32::Foundation::HLOCAL(
            output.pbData as *mut _,
        ));
    }
    let mut blob = b"DPAPI".to_vec();
    blob.extend_from_slice(&bytes);
    Ok(blob)
}

#[cfg(not(windows))]
fn protect(_: &[u8]) -> Result<Vec<u8>, String> {
    Err("仅支持 Windows 的本地加密".into())
}

#[cfg(windows)]
fn unprotect(blob: &[u8]) -> Result<Vec<u8>, String> {
    use windows::Win32::Security::Cryptography::{
        CryptUnprotectData, CRYPTPROTECT_UI_FORBIDDEN, CRYPT_INTEGER_BLOB,
    };
    let data = blob
        .strip_prefix(b"DPAPI")
        .ok_or_else(|| "请求头不是本机加密格式".to_string())?;
    let input = CRYPT_INTEGER_BLOB {
        cbData: data.len() as u32,
        pbData: data.as_ptr() as *mut u8,
    };
    let mut output = CRYPT_INTEGER_BLOB::default();
    unsafe {
        CryptUnprotectData(
            &input,
            None,
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            &mut output,
        )
    }
    .map_err(|_| "请求头无法解密，请重新粘贴".to_string())?;
    let bytes =
        unsafe { std::slice::from_raw_parts(output.pbData, output.cbData as usize) }.to_vec();
    unsafe {
        windows::Win32::Foundation::LocalFree(windows::Win32::Foundation::HLOCAL(
            output.pbData as *mut _,
        ));
    }
    Ok(bytes)
}

#[cfg(not(windows))]
fn unprotect(_: &[u8]) -> Result<Vec<u8>, String> {
    Err("仅支持 Windows 的本地加密".into())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn headers_keep_only_cookie_and_authorization() {
        let raw = "Accept: */*\r\nCookie: sid=abc; uid=42\r\nAuthorization: Bearer tok\r\nSec-Fetch-Site: same-origin";
        let kept = normalize(raw).unwrap();
        assert_eq!(kept, "Cookie: sid=abc; uid=42\nAuthorization: Bearer tok");
        let pairs = header_pairs(&kept);
        assert_eq!(pairs.len(), 2);
        assert_eq!(pairs[0].0, "Cookie");
    }

    #[test]
    fn unrelated_or_malformed_headers_are_rejected() {
        assert!(
            normalize("Accept: */*").is_err(),
            "没有 Cookie/Authorization 不能保存"
        );
        assert!(normalize("Cookie sid=abc").is_err(), "缺少冒号要报格式错误");
        assert!(normalize("Cookie:").is_err(), "空值要报错");
    }

    #[test]
    fn points_parse_and_zero_is_not_an_error() {
        let snapshot = parse(
            &serde_json::json!({"code":0,"data":{"points":1280,"total":2000,"package_name":"Pro"}}),
        )
        .unwrap();
        assert_eq!(snapshot.windows.len(), 1);
        assert_eq!(snapshot.windows[0].text.as_deref(), Some("1280"));
        assert_eq!(snapshot.windows[0].remaining, 100.0);
        assert_eq!(snapshot.plan, "Pro");
        assert!(snapshot.extra[0].label.contains("共 2000"));

        let zero = parse(&serde_json::json!({"data":{"points":0,"plan":"Free"}})).unwrap();
        assert_eq!(zero.windows[0].text.as_deref(), Some("0"));
        assert_eq!(
            zero.windows[0].remaining, 0.0,
            "零积分画空环，但仍是一条有效数据"
        );
        assert_eq!(zero.plan, "Free");
    }


    #[test]
    fn real_summary_payload_shows_total_and_groups() {
        let snapshot = parse(&serde_json::json!({
            "code": 0, "msg": "OK",
            "data": {
                "TotalCredits": "2407.60000128",
                "SubscriptionPackageName": "体验版",
                "IsPaidUser": false,
                "CreditGroups": [
                    {"Kind": "plan_base", "Name": "套餐基础积分", "CycleTotalCapacity": "500", "CycleRemainCapacity": "500", "CycleUsedCapacity": "0"},
                    {"Kind": "plan_bonus", "Name": "套餐赠送积分", "CycleTotalCapacity": "0", "CycleRemainCapacity": "0", "CycleUsedCapacity": "0"},
                    {"Kind": "benefit", "Name": "平台奖励积分", "CycleTotalCapacity": "3900", "CycleRemainCapacity": "1907.60000128", "CycleUsedCapacity": "1992.39999872"}
                ]
            }
        })).unwrap();
        assert_eq!(snapshot.plan, "体验版");
        assert_eq!(snapshot.windows[0].text.as_deref(), Some("2407.6"), "环内显示总积分");
        assert_eq!(snapshot.windows[0].remaining, 100.0);
        assert_eq!(snapshot.extra.len(), 2, "零额度的分组不占一行");
        assert!(snapshot.extra[0].label.contains("套餐基础积分"));
        assert_eq!(snapshot.extra[0].text.as_deref(), Some("500"));
        assert!(snapshot.extra[1].label.contains("平台奖励积分"));
        assert_eq!(snapshot.extra[1].text.as_deref(), Some("1907.6"));
        assert!((snapshot.extra[1].remaining - 48.91).abs() < 0.1, "剩余占比 1907.6/3900");
    }

    #[test]
    fn zero_total_credits_is_still_valid() {
        let snapshot = parse(&serde_json::json!({"code":0,"data":{"TotalCredits":"0","SubscriptionPackageName":"体验版","CreditGroups":[]}})).unwrap();
        assert_eq!(snapshot.windows[0].text.as_deref(), Some("0"));
        assert_eq!(snapshot.windows[0].remaining, 0.0);
    }

    #[test]
    fn failure_shapes_are_errors_not_zero_points() {
        assert!(parse(&serde_json::json!({"code":401,"msg":"session expired"})).is_err());
        assert!(parse(&serde_json::json!({"success":false})).is_err());
        assert!(
            parse(&serde_json::json!({"data":{}})).is_err(),
            "没有积分字段必须报错"
        );
        assert!(parse(&serde_json::json!({"data":{"points":-5}})).is_err());
    }

    #[test]
    fn text_numbers_and_string_points_are_accepted() {
        let snapshot = parse(&serde_json::json!({"data":{"points":"12.5","plan":"Lite"}})).unwrap();
        assert_eq!(snapshot.windows[0].text.as_deref(), Some("12.5"));
        assert_eq!(snapshot.plan, "Lite");
    }

    #[cfg(windows)]
    #[test]
    fn header_is_encrypted_at_rest_and_round_trips() {
        let id = format!("workbuddy-test-{}", std::process::id());
        store_header(&id, "Cookie: sid=secret-value").unwrap();
        let path = blob_path(&id);
        let raw = std::fs::read(&path).unwrap();
        assert!(raw.starts_with(b"DPAPI"));
        assert!(
            !raw.windows(6).any(|window| window == b"secret"),
            "落盘内容不能出现明文"
        );
        assert_eq!(load_header(&id).unwrap(), "Cookie: sid=secret-value");
        forget_header(&id);
        assert!(!path.exists());
        assert!(load_header(&id).is_err());
    }
}
