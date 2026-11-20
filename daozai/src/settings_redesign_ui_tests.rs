use super::*;

#[test]
fn settings_pages_and_background_switches_remain_independent() {
    let _guard = ENV_LOCK.lock().unwrap_or_else(|error| error.into_inner());
    let mut h = H::new();
    h.app.settings.visible_pages = [true; 9];
    h.app.settings.mail_enabled = false;
    h.app.quota.config.enabled = false;
    assert!(!h.app.mail_active() && !h.app.quota_active());
    assert!(h.app.module_on(crate::app::MAIL_PAGE) && h.app.module_on(crate::app::QUOTA_PAGE));
    h.app.settings.mail_enabled = true;
    h.app.quota.config.enabled = true;
    assert!(h.app.mail_active() && h.app.quota_active());
    h.app.set_page_visible(crate::app::MAIL_PAGE, false);
    h.app.set_page_visible(crate::app::QUOTA_PAGE, false);
    assert!(!h.app.mail_active() && !h.app.quota_active());
    assert!(h.app.settings.mail_enabled && h.app.quota.config.enabled);
}

/// 旧的分页序号（岛上入口、更新提示等按序号跳转）仍能打开合并后的页面，每个序号只属于一个侧栏项。
#[test]
fn settings_old_tab_numbers_open_merged_pages(){
    use crate::extras::settings_tab_group_for_tests as group;
    assert_eq!(group(2),"专注与健康");assert_eq!(group(3),"专注与健康");
    assert_eq!(group(4),"待办与暂存");assert_eq!(group(5),"待办与暂存");
    assert_eq!(group(6),"消息提醒");assert_eq!(group(7),"邮箱");assert_eq!(group(8),"日程");
    assert_eq!(group(0),"通用");assert_eq!(group(13),"外观");assert_eq!(group(14),"位置");
    assert_eq!(group(10),"页面管理");assert_eq!(group(9),"关于");
}

/// 每个分页都能正常绘制（含功能关闭时的提示），不会因为挪动布局而崩溃。
#[test]
fn settings_every_tab_renders_with_modules_on_and_off(){
    let _g=ENV_LOCK.lock().unwrap_or_else(|e|e.into_inner());
    for on in [true,false] {
        let mut h=H::new();h.app.open_settings();h.ctx.set_embed_viewports(true);
        if !on {for page in 0..9 {if page!=crate::app::MUSIC_PAGE {h.app.settings.visible_pages[page]=false;}}}
        for tab in 0..=14 {
            h.app.settings_tab=tab;
            for _ in 0..2 {let _=h.ctx.run(egui::RawInput::default(),|ctx|h.app.settings_ui(ctx,false));}
            assert_eq!(h.app.settings_tab,tab,"绘制分页 {tab} 不应自行跳转");
        }
    }
}

/// 设置窗口拉到最小（600×450）时，侧栏 13 项都在可见区内，「关于」不会被挤出去。
#[test]
fn settings_sidebar_keeps_about_visible_at_minimum_height(){
    let _g=ENV_LOCK.lock().unwrap_or_else(|e|e.into_inner());
    let mut h=H::new();h.app.open_settings();h.ctx.set_embed_viewports(false);
    let output=std::sync::Arc::new(Mutex::new(None));let capture=output.clone();
    egui::Context::set_immediate_viewport_renderer(move|ctx,mut viewport|{
        let id=viewport.ids.this;
        let raw=egui::RawInput{viewport_id:id,screen_rect:Some(Rect::from_min_size(Pos2::ZERO,egui::vec2(600.0,450.0))),
            viewports:std::iter::once((id,egui::ViewportInfo::default())).collect(),..Default::default()};
        *capture.lock().unwrap()=Some(ctx.run(raw,|ctx|(viewport.viewport_ui_cb)(ctx)));
    });
    for _ in 0..3 {let _=h.ctx.run(Default::default(),|ctx|h.app.settings_ui(ctx,false));}
    let frame=output.lock().unwrap().take().unwrap();
    for label in ["通用","天气","关于"] {
        let rect=frame.shapes.iter().find_map(|s|match &s.shape{egui::Shape::Text(t) if t.galley.text()==label && t.pos.x<180.0=>Some(t.visual_bounding_rect()),_=>None})
            .unwrap_or_else(||panic!("侧栏缺少 {label}"));
        assert!(rect.bottom()<=450.0,"{label} 超出窗口底部：{rect:?}");
    }
}

#[test]
fn calendar_provider_draft_keeps_the_connected_account() {
    use crate::calendar::{self, Config, Provider};
    let _guard = ENV_LOCK.lock().unwrap_or_else(|error| error.into_inner());
    let mut h = H::new();
    let connected = Config { provider: Provider::Feishu, username: "fixture@example.test".into(),
        href: None, server: None };
    calendar::save_config(&connected).unwrap();
    h.app.calendar = crate::app::CalendarState::load();
    h.app.open_calendar_connection();
    h.app.calendar.form.password = "fixture input".into();

    h.app.set_calendar_form_provider(Provider::WeCom);
    assert_eq!(h.app.calendar.form.provider, Provider::WeCom);
    assert!(h.app.calendar.form.open && h.app.calendar.form.guide_open);
    assert!(h.app.calendar.form.password.is_empty());
    assert_eq!(h.app.calendar.config.as_ref(), Some(&connected));
    assert_eq!(h.app.calendar_configs(), vec![connected.clone()]);
    assert_eq!(calendar::load_config().as_ref(), Some(&connected));

    h.app.calendar.form.open = false;
    h.app.open_calendar_connection();
    assert_eq!(h.app.calendar.form.provider, Provider::Feishu);
    assert_eq!(h.app.calendar.form.username, connected.username);
}

#[test]
fn long_quota_alias_keeps_details_reachable_at_minimum_width() {
    let _guard = ENV_LOCK.lock().unwrap_or_else(|error| error.into_inner());
    let mut h = H::new();
    h.app.settings.visible_pages[crate::app::QUOTA_PAGE] = true;
    h.app.quota.config.accounts = vec![crate::quota::Account {
        id: "long-alias-fixture".into(), provider: crate::quota::Provider::Claude,
        alias: "长名字".repeat(100), source: Default::default(), slot: None,
        enabled: true, pinned: true,
    }];
    h.app.open_settings();
    h.app.settings_tab = 11;
    h.ctx.set_embed_viewports(false);
    let output = std::sync::Arc::new(Mutex::new(None));
    let capture = output.clone();
    egui::Context::set_immediate_viewport_renderer(move |ctx, mut viewport| {
        let id = viewport.ids.this;
        let input = egui::RawInput {
            viewport_id: id,
            screen_rect: Some(Rect::from_min_size(Pos2::ZERO, egui::vec2(600.0, 450.0))),
            viewports: std::iter::once((id, egui::ViewportInfo::default())).collect(),
            ..Default::default()
        };
        *capture.lock().unwrap() = Some(ctx.run(input, |ctx| (viewport.viewport_ui_cb)(ctx)));
    });
    for _ in 0..3 {
        let _ = h.ctx.run(Default::default(), |ctx| h.app.settings_ui(ctx, false));
    }
    let frame = output.lock().unwrap().take().unwrap();
    let button = frame.shapes.iter().find(|shape| matches!(&shape.shape,
        egui::Shape::Text(text) if text.galley.text() == "详情")).expect("长别名仍应显示详情按钮");
    assert!(button.clip_rect.contains_rect(button.shape.visual_bounding_rect()));
}
