//! 检查更新：只查上游正式 release 并提示，不下载、不缓存、不启动安装程序。
//!
//! 个人分支基线为 0.6.50；比较对象是已整合的上游正式版本。
use eframe::egui;
use std::sync::mpsc::{self, Receiver};
use std::time::Duration;

const REPOSITORY: &str = "https://github.com/Renly1994/xiaotang-daozai";
const API: &str = "https://api.github.com/repos/Renly1994/xiaotang-daozai/releases/latest";
const RELEASES: &str = "https://github.com/Renly1994/xiaotang-daozai/releases";

#[derive(Clone, Debug)]
struct Release { version: String, notes: String, page: String }

/// 检查结果：只区分「有更新」「同版」「上游更旧」「预发布」，不做任何下载动作。
#[derive(Clone, Debug)]
pub(crate) enum Status {
    Newer(Release),
    Same { current: String, latest: String },
    Older { current: String, latest: String },
    Prerelease { latest: String },
}

enum Event { Checked(Result<Status, String>) }

#[derive(Default)]
pub(crate) struct State {
    rx: Option<Receiver<Event>>,
    result: Option<Result<Status, String>>,
    message: String,
    dialog_open: bool,
    focus_requested: bool,
    logo: Option<egui::TextureHandle>,
}

impl State {
    pub(crate) fn poll(&mut self, ctx: &egui::Context) {
        let Some(rx) = self.rx.as_ref() else { return };
        match rx.try_recv() {
            Ok(Event::Checked(result)) => {
                self.dialog_open = matches!(&result, Ok(Status::Newer(_)));
                self.focus_requested = self.dialog_open;
                self.message = match &result {
                    Ok(Status::Same { current, latest }) => format!("当前已是最新正式版（{current}；上游 {latest}）"),
                    Ok(Status::Older { current, latest }) => format!("当前 {current} 已高于上游最新正式版 {latest}"),
                    Ok(Status::Prerelease { latest }) => format!("上游最新是预发布版本 {latest}，暂不提示"),
                    Ok(Status::Newer(release)) => format!("发现上游正式版 {}", release.version),
                    Err(message) => message.clone(),
                };
                self.result = Some(result);
                self.rx = None;
                ctx.request_repaint();
            }
            Err(mpsc::TryRecvError::Disconnected) => {
                self.rx = None;
                self.message = "检查已中断，请重试。".into();
            }
            Err(mpsc::TryRecvError::Empty) => ctx.request_repaint_after(Duration::from_millis(120)),
        }
    }

    pub(crate) fn ui(&mut self, ui: &mut egui::Ui) {
        if ui.add_enabled(self.rx.is_none(), egui::Button::new("检查更新")).clicked() {
            let (tx, rx) = mpsc::channel();
            self.rx = Some(rx);
            self.message.clear();
            self.result = None;
            self.dialog_open = false;
            let ctx = ui.ctx().clone();
            std::thread::spawn(move || {
                let _ = tx.send(Event::Checked(check()));
                ctx.request_repaint();
            });
        }
        match &self.result {
            Some(Ok(Status::Newer(release))) => {
                if ui.button(format!("发现上游正式版 {} · 查看说明", release.version)).clicked() {
                    self.dialog_open = true;
                    self.focus_requested = true;
                }
            }
            Some(Ok(_)) => { ui.label(&self.message); }
            Some(Err(message)) => {
                ui.label(message);
                ui.label(egui::RichText::new(RELEASES).size(11.5).color(crate::theme::GRAY));
            }
            None if self.rx.is_some() => { ui.label("正在检查…"); }
            _ => {}
        }
        ui.add_space(5.0);
    }

    fn dismiss(&mut self) { self.dialog_open = false; }

    pub(crate) fn dialog_ui(&mut self, ctx: &egui::Context) {
        use crate::theme::{self, W};
        if !self.dialog_open { return; }
        let Some(Ok(Status::Newer(release))) = self.result.clone() else { return; };
        let focus = std::mem::take(&mut self.focus_requested);
        let logo = self.logo.get_or_insert_with(|| {
            let icon = theme::app_icon();
            ctx.load_texture("update-logo", egui::ColorImage::from_rgba_unmultiplied([icon.width as usize, icon.height as usize], &icon.rgba), egui::TextureOptions::LINEAR)
        }).id();
        ctx.show_viewport_immediate(egui::ViewportId::from_hash_of("daozai-update"),
            egui::ViewportBuilder::default().with_title("岛仔有上游新版本").with_icon(theme::app_icon())
                .with_inner_size([520.0, 380.0]).with_resizable(false).with_decorations(false)
                .with_transparent(true).with_active(true), |ctx, _| {
                if focus {
                    ctx.send_viewport_cmd(egui::ViewportCommand::Minimized(false));
                    ctx.send_viewport_cmd(egui::ViewportCommand::Focus);
                }
                if ctx.input(|input| input.viewport().close_requested()) { self.dismiss(); return; }
                egui::CentralPanel::default().frame(egui::Frame::NONE).show(ctx, |ui| {
                    let window = ui.max_rect().shrink(8.0);
                    ui.painter().rect_filled(window, 22.0, egui::Color32::from_rgb(25, 25, 28));
                    ui.painter().rect_stroke(window, 22.0, egui::Stroke::new(1.0_f32, egui::Color32::from_rgb(55, 55, 61)), egui::StrokeKind::Inside);
                    let close_rect = egui::Rect::from_min_size(window.right_top() + egui::vec2(-42.0, 12.0), egui::vec2(28.0, 28.0));
                    let close = ui.interact(close_rect, ui.id().with("update-close"), egui::Sense::click()).on_hover_text("关闭");
                    if close.hovered() { ui.painter().rect_filled(close_rect, 8.0, theme::BTN_HOVER); }
                    let center = close_rect.center();
                    for direction in [-1.0, 1.0] {
                        ui.painter().line_segment([center + egui::vec2(-4.0, -4.0 * direction), center + egui::vec2(4.0, 4.0 * direction)], egui::Stroke::new(1.5_f32, theme::GRAY));
                    }
                    if close.clicked() { self.dismiss(); }
                    let drag_rect = egui::Rect::from_min_max(window.min, egui::pos2(close_rect.left() - 8.0, window.top() + 42.0));
                    if ui.interact(drag_rect, ui.id().with("update-drag"), egui::Sense::drag()).drag_started() {
                        ctx.send_viewport_cmd(egui::ViewportCommand::StartDrag);
                    }
                    ui.scope_builder(egui::UiBuilder::new().max_rect(window.shrink2(egui::vec2(24.0, 24.0))), |ui| {
                        let style = ui.style_mut();
                        style.visuals.override_text_color = Some(theme::WHITE);
                        style.visuals.widgets.inactive.corner_radius = egui::CornerRadius::same(10);
                        style.visuals.widgets.hovered.corner_radius = egui::CornerRadius::same(10);
                        style.visuals.widgets.active.corner_radius = egui::CornerRadius::same(10);
                        style.spacing.item_spacing = egui::vec2(10.0, 8.0);
                        style.text_styles.insert(egui::TextStyle::Body, theme::font(13.0, W::Regular));
                        style.text_styles.insert(egui::TextStyle::Button, theme::font(13.0, W::Semibold));
                        ui.horizontal(|ui| {
                            ui.image((logo, egui::vec2(52.0, 52.0)));
                            ui.add_space(4.0);
                            ui.vertical(|ui| {
                                ui.label(egui::RichText::new("上游有新版本").font(theme::font(21.0, W::Semibold)));
                                ui.horizontal(|ui| {
                                    ui.label(egui::RichText::new(env!("CARGO_PKG_VERSION")).color(theme::DIM));
                                    ui.label(egui::RichText::new("→").color(theme::DIM));
                                    egui::Frame::new().fill(theme::alpha_blue(0.12)).corner_radius(6.0)
                                        .inner_margin(egui::Margin::symmetric(8, 3)).show(ui, |ui| {
                                            ui.label(egui::RichText::new(&release.version).color(theme::BLUE).font(theme::font(12.0, W::Semibold)));
                                        });
                                });
                            });
                        });
                        ui.add_space(10.0);
                        egui::Frame::new().fill(egui::Color32::from_rgb(35, 35, 39)).corner_radius(12.0)
                            .inner_margin(16.0).show(ui, |ui| {
                                ui.set_min_width(ui.available_width());
                                ui.label(egui::RichText::new("上游更新说明").color(theme::GRAY).font(theme::font(11.5, W::Semibold)));
                                egui::ScrollArea::vertical().id_salt("update-notes").max_height(96.0).min_scrolled_height(96.0)
                                    .auto_shrink([false, false]).show(ui, |ui| {
                                        if release.notes.trim().is_empty() { ui.label("（此版本没有填写说明）"); }
                                        else { for line in release.notes.lines() {
                                            let line = line.trim();
                                            if line.is_empty() { ui.add_space(3.0); continue; }
                                            let heading = line.starts_with('#');
                                            let text = if heading { line.trim_start_matches('#').trim().to_owned() }
                                                else if let Some(item) = line.strip_prefix("- ").or_else(|| line.strip_prefix("* ")) { format!("•  {item}") }
                                                else { line.to_owned() };
                                            ui.label(egui::RichText::new(text).font(theme::font(13.0, if heading { W::Semibold } else { W::Regular })).color(egui::Color32::from_gray(225)));
                                        } }
                                    });
                            });
                        ui.add_space(4.0);
                        ui.label(egui::RichText::new("个人分支只提示，不下载、不自动安装；需要时按发布页手动整合。").color(theme::DIM).size(11.5));
                        ui.add_space(4.0);
                        ui.horizontal(|ui| {
                            if ui.add(egui::Button::new("稍后").fill(theme::BTN).min_size(egui::vec2(110.0, 40.0))).clicked() { self.dismiss(); }
                            if ui.add(egui::Button::new(egui::RichText::new("复制发布页链接").color(theme::WHITE)).fill(theme::BLUE).min_size(egui::vec2(ui.available_width(), 40.0))).clicked() {
                                crate::collect::note_self_copy(&release.page);
                                ui.ctx().copy_text(release.page.clone());
                            }
                        });
                        ui.add_space(2.0);
                        ui.label(egui::RichText::new(&release.page).size(11.0).color(theme::GRAY));
                    });
                });
            });
    }
}

/// 更新请求使用的代理：优先显式环境变量，其次 Windows 系统代理。
/// 上游 v0.6.50 的代理支持在合并时被个人版更新模块整体替换掉了，这里恢复。
fn update_agent(proxy: Option<&str>, timeout: Duration) -> Result<ureq::Agent, String> {
    // 整体 timeout 会覆盖读取超时，分别限制连接和无数据等待。
    let mut builder = ureq::AgentBuilder::new().try_proxy_from_env(false)
        .timeout_connect(Duration::from_secs(20)).timeout_read(timeout).timeout_write(timeout);
    if let Some(proxy) = proxy {
        builder = builder.proxy(ureq::Proxy::new(proxy).map_err(|_| "代理地址无效，请检查代理设置后重试".to_owned())?);
    }
    Ok(builder.build())
}

fn http_agent() -> Result<ureq::Agent, String> {
    let proxy = ["HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "HTTP_PROXY", "http_proxy"]
        .iter().find_map(|key| std::env::var(key).ok().filter(|value| !value.trim().is_empty()))
        .or_else(crate::quota::system_proxy);
    update_agent(proxy.as_deref(), Duration::from_secs(15))
}

fn check() -> Result<Status, String> {
    let response = http_agent()?
        .get(API).set("User-Agent", concat!("Daozai/", env!("CARGO_PKG_VERSION")))
        .set("Accept", "application/vnd.github+json").call().map_err(|error| match error {
            ureq::Error::Status(403 | 429, _) => "检查过于频繁，请稍后重试".to_owned(),
            ureq::Error::Status(404, _) => "暂未找到正式版本，请查看发布页".to_owned(),
            _ => "无法连接更新服务，请检查网络或代理后重试".to_owned(),
        })?;
    let value: serde_json::Value = serde_json::from_reader(response.into_reader())
        .map_err(|_| "更新信息格式异常，请稍后重试".to_owned())?;
    classify(&value, env!("CARGO_PKG_VERSION"))
}

/// 只读元数据：发布说明与版本号；不解析、不接触任何安装包地址。
fn classify(value: &serde_json::Value, current: &str) -> Result<Status, String> {
    let invalid = || "更新信息格式异常，请稍后重试".to_owned();
    let tag = value["tag_name"].as_str().ok_or_else(invalid)?;
    let tag = tag.trim_start_matches('v').to_string();
    if value["draft"].as_bool() != Some(false) {
        return Err(invalid());
    }
    if value["prerelease"].as_bool() == Some(true) {
        return Ok(Status::Prerelease { latest: tag });
    }
    let latest = version(&tag).ok_or_else(invalid)?;
    let now = version(current).ok_or_else(invalid)?;
    if latest > now {
        Ok(Status::Newer(Release {
            page: format!("{REPOSITORY}/releases/tag/v{tag}"),
            version: tag,
            notes: value["body"].as_str().unwrap_or("").to_owned(),
        }))
    } else if latest == now {
        Ok(Status::Same { current: current.into(), latest: tag })
    } else {
        Ok(Status::Older { current: current.into(), latest: tag })
    }
}

fn version(value: &str) -> Option<[u64; 3]> {
    let mut parts = value.strip_prefix('v').unwrap_or(value).split('.');
    let mut numbers = [0; 3];
    for number in &mut numbers {
        let part = parts.next()?;
        if part.is_empty() || !part.bytes().all(|c| c.is_ascii_digit()) { return None; }
        *number = part.parse().ok()?;
    }
    parts.next().is_none().then_some(numbers)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn release(tag: &str) -> serde_json::Value {
        serde_json::json!({"tag_name": tag, "draft": false, "prerelease": false, "body": "说明"})
    }

    #[test]
    fn compares_versions_numerically() {
        assert!(matches!(classify(&release("v0.6.41"), "0.6.40").unwrap(), Status::Newer(_)));
        assert!(matches!(classify(&release("v0.7.0"), "0.6.40").unwrap(), Status::Newer(_)));
        assert!(matches!(classify(&release("v0.6.40"), "0.6.40").unwrap(), Status::Same { .. }));
        assert!(matches!(classify(&release("v0.6.39"), "0.6.40").unwrap(), Status::Older { .. }));
        assert!(matches!(classify(&release("v0.10.0"), "0.9.9").unwrap(), Status::Newer(_)));
    }

    #[test]
    fn prerelease_and_draft_are_not_offered() {
        let mut value = release("v0.7.0");
        value["prerelease"] = serde_json::json!(true);
        assert!(matches!(classify(&value, "0.6.40").unwrap(), Status::Prerelease { .. }));
        let mut value = release("v0.7.0");
        value["draft"] = serde_json::json!(true);
        assert!(classify(&value, "0.6.40").is_err(), "草稿版本按格式错误处理");
    }

    #[test]
    fn invalid_tags_are_rejected() {
        assert!(classify(&release("v0.6"), "0.6.40").is_err());
        assert!(classify(&release("nightly"), "0.6.40").is_err());
        assert!(classify(&serde_json::json!({"draft": false}), "0.6.40").is_err());
    }

    /// 配了代理时更新检查必须走代理，而不是直连。
    #[test]
    fn update_requests_use_configured_proxy() {
        use std::io::{Read, Write};
        let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
        listener.set_nonblocking(true).unwrap();
        let proxy = format!("http://{}", listener.local_addr().unwrap());
        let worker = std::thread::spawn(move || {
            let start = std::time::Instant::now();
            loop {
                if let Ok((mut stream, _)) = listener.accept() {
                    // 监听套接字是非阻塞的，accept 出来的连接可能继承该模式。
                    stream.set_nonblocking(false).unwrap();
                    stream.set_read_timeout(Some(Duration::from_secs(1))).unwrap();
                    let mut request = [0; 4096];
                    let n = stream.read(&mut request).unwrap();
                    assert!(String::from_utf8_lossy(&request[..n]).starts_with("GET http://127.0.0.1:1/update.zip"));
                    stream.write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok").unwrap();
                    return;
                }
                if start.elapsed() > Duration::from_secs(3) { return; }
            }
        });
        let result = update_agent(Some(&proxy), Duration::from_millis(200)).unwrap()
            .get("http://127.0.0.1:1/update.zip").call();
        worker.join().unwrap();
        assert_eq!(result.unwrap().into_string().unwrap(), "ok");
    }

    /// 方案 N14：只提示，不下载、不缓存、不拉起进程。
    #[test]
    fn check_only_never_downloads_or_launches() {
        let source = include_str!("updates.rs");
        let forbidden = [
            ["fn do", "wnload("].concat(),
            ["launch_", "installer"].concat(),
            ["std::process::", "Command"].concat(),
            ["File::", "create"].concat(),
            ["remove_dir_", "all"].concat(),
            ["LOCALAPPDATA", "/Daozai/Updates"].concat(),
        ];
        for token in forbidden {
            assert!(!source.contains(&token), "检查更新不应包含下载/安装相关代码：{token}");
        }
    }
}

#[cfg(test)]
mod live {
    use super::*;

    /// 真实请求上游正式版；只验证「能拿到分类结果且没有副作用」。
    /// 断网时明确跳过，不伪装通过。
    #[test]
    fn live_check_has_no_side_effects() {
        let cache = std::env::var_os("LOCALAPPDATA").map(std::path::PathBuf::from).map(|root| root.join("Daozai").join("Updates"));
        let before = cache.as_deref().map(std::path::Path::exists);
        match check() {
            Ok(status) => {
                let label = match &status {
                    Status::Newer(release) => format!("上游有更新 {}", release.version),
                    Status::Same { current, latest } => format!("同版 {current}/{latest}"),
                    Status::Older { current, latest } => format!("上游更旧 {current}/{latest}"),
                    Status::Prerelease { latest } => format!("预发布 {latest}"),
                };
                eprintln!("实机检查结果：{label}");
            }
            Err(message) => {
                eprintln!("跳过实机检查：{message}");
                return;
            }
        }
        assert_eq!(cache.as_deref().map(std::path::Path::exists), before, "检查更新不应创建/改动缓存目录");
    }
}
