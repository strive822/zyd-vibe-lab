//! 按显示屏的物理坐标居中岛体，透明画布的额外宽度不参与居中。
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Bounds { pub left:i32, pub top:i32, pub right:i32, pub bottom:i32 }

#[derive(Clone, Debug)]
pub struct Display { pub id:String, pub label:String, pub bounds:Bounds, pub primary:bool }

pub fn selected<'a>(displays:&'a [Display],id:&str)->Option<&'a Display>{
    displays.iter().find(|d|!id.is_empty()&&d.id==id)
        .or_else(||displays.iter().find(|d|d.primary)).or_else(||displays.first())
}

#[cfg(windows)]
pub fn connected()->Vec<Display>{
    use windows::{core::PCWSTR,Win32::{Foundation::{BOOL,LPARAM,RECT},Graphics::Gdi::*,UI::WindowsAndMessaging::EDD_GET_DEVICE_INTERFACE_NAME}};
    fn text(value:&[u16])->String {String::from_utf16_lossy(&value[..value.iter().position(|c|*c==0).unwrap_or(value.len())])}
    unsafe extern "system" fn collect(monitor:HMONITOR,_:HDC,_:*mut RECT,data:LPARAM)->BOOL {
        let mut info=MONITORINFOEXW::default();info.monitorInfo.cbSize=std::mem::size_of::<MONITORINFOEXW>() as u32;
        if GetMonitorInfoW(monitor,&mut info.monitorInfo).as_bool(){
            let device=text(&info.szDevice);
            let mut details=DISPLAY_DEVICEW{cb:std::mem::size_of::<DISPLAY_DEVICEW>() as u32,..Default::default()};
            let found=EnumDisplayDevicesW(PCWSTR(info.szDevice.as_ptr()),0,&mut details,EDD_GET_DEVICE_INTERFACE_NAME).as_bool();
            let stable_id=if found{text(&details.DeviceID)}else{String::new()};
            let name=if found{text(&details.DeviceString)}else{String::new()};
            let number=device.trim_start_matches(r"\\.\DISPLAY");let r=info.monitorInfo.rcMonitor;
            let primary=info.monitorInfo.dwFlags&1!=0;
            let label=format!("显示器 {number}{} · {} × {}{}",if name.is_empty(){String::new()}else{format!(" · {name}")},r.right-r.left,r.bottom-r.top,if primary{" · 主屏"}else{""});
            let displays=&mut *(data.0 as *mut Vec<Display>);
            displays.push(Display{id:if stable_id.is_empty(){device}else{stable_id},label,bounds:Bounds{left:r.left,top:r.top,right:r.right,bottom:r.bottom},primary});
        }
        BOOL(1)
    }
    let mut displays:Vec<Display>=Vec::new();
    unsafe {let _=EnumDisplayMonitors(None,None,Some(collect),LPARAM(&mut displays as *mut Vec<Display> as isize));}
    displays.sort_by(|a,b|a.label.cmp(&b.label));displays
}

#[cfg(not(windows))]
pub fn connected()->Vec<Display>{Vec::new()}

pub fn island_origin(m:Bounds, island_width:f32, scale:f32)->Option<(i32,i32)> {
    if m.right<=m.left || m.bottom<=m.top || !scale.is_finite() || scale<=0.0 || !island_width.is_finite() || island_width<=0.0 {return None;}
    let width=(island_width as f64*scale as f64).round();
    let x=(m.left as f64+(m.right as f64-m.left as f64-width)/2.0).round();
    Some((x.clamp(i32::MIN as f64,i32::MAX as f64) as i32,m.top))
}

/// 拖动整岛的水平范围（相对屏幕居中的逻辑点偏移，正数向右）。
/// 约束的是**岛体本身**完全留在屏幕内；透明承载余量允许出屏，
/// 但右侧为收起态通知徽标预留 `reserve_right`，避免拖到最右时通知被屏幕裁掉。
pub fn drag_limits(m:Bounds, body_width:f32, scale:f32, reserve_right:f32)->Option<(f32,f32)> {
    if m.right<=m.left || !scale.is_finite() || scale<=0.0 || !body_width.is_finite() || body_width<0.0 || !reserve_right.is_finite() {return None;}
    let logical=(m.right-m.left) as f64/scale as f64;
    let body=(body_width as f64).clamp(0.0,logical);
    let travel=((logical-body)/2.0).max(0.0);
    let reserve=(reserve_right as f64).max(0.0).min(travel);
    let max=(travel-reserve).max(-travel);
    Some(((-travel) as f32,max as f32))
}

/// 拖动后的窗口原点：永远贴目标屏幕顶部，横向偏移按 `drag_limits` 钳制。
/// 返回窗口原点与**实际生效**的偏移；岛体比屏幕还宽时保持居中且不可拖。
pub fn island_origin_for(m:Bounds, island_width:f32, scale:f32, offset:Option<f32>, body_width:f32, reserve_right:f32)->Option<((i32,i32),f32)> {
    let center=island_origin(m,island_width,scale)?;
    let (min,max)=drag_limits(m,body_width,scale,reserve_right)?;
    let want=offset.filter(|value|value.is_finite()).unwrap_or(0.0).clamp(min,max);
    if want==0.0 {return Some((center,0.0));}
    let x=(center.0 as f64+(want as f64*scale as f64).round()).clamp(i32::MIN as f64,i32::MAX as f64) as i32;
    Some(((x,center.1),((x as f64-center.0 as f64)/scale as f64) as f32))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[cfg(windows)]
    #[test] fn connected_displays_have_valid_bounds_and_distinct_ids(){
        let displays=connected();
        for (i,display) in displays.iter().enumerate(){
            println!("{}：{:?}",display.label,display.bounds);
            assert!(!display.id.is_empty());assert!(island_origin(display.bounds,640.0,1.0).is_some());
            assert!(!displays[..i].iter().any(|d|d.id==display.id));
        }
        if !displays.is_empty(){assert_eq!(displays.iter().filter(|d|d.primary).count(),1);}
    }
    #[test] fn display_selection_survives_reordering_disconnect_and_reconnect(){
        let primary=Display{id:"internal".into(),label:"内屏".into(),bounds:Bounds{left:0,top:0,right:1920,bottom:1080},primary:true};
        let external=Display{id:"external".into(),label:"外屏".into(),bounds:Bounds{left:-2560,top:-400,right:0,bottom:1040},primary:false};
        for displays in [vec![primary.clone(),external.clone()],vec![external.clone(),primary.clone()]] {
            assert_eq!(selected(&displays,"").unwrap().id,"internal");
            let target=selected(&displays,"external").unwrap();assert_eq!(target.id,"external");
            assert_eq!(island_origin(target.bounds,640.0,1.5),Some((-1760,-400)));
        }
        assert_eq!(selected(&[primary.clone()],"external").unwrap().id,"internal");
        assert_eq!(selected(&[primary,external],"external").unwrap().id,"external");
        assert!(selected(&[],"external").is_none());
    }
    #[test] fn real_origins_and_dpi_center_only_the_island(){
        for (m,scale,want) in [
            (Bounds{left:0,top:0,right:1920,bottom:1080},1.0,(640,0)),
            (Bounds{left:-2560,top:-400,right:0,bottom:1040},1.5,(-1760,-400)),
            (Bounds{left:300,top:-1440,right:2860,bottom:0},2.0,(940,-1440)),
            (Bounds{left:1920,top:200,right:3840,bottom:1280},1.25,(2480,200)),
        ] {assert_eq!(island_origin(m,640.0,scale),Some(want));}
    }
    #[test] fn dragging_keeps_the_island_docked_and_inside_the_display(){
        let m=Bounds{left:0,top:0,right:1920,bottom:1080};
        // 岛体 300 宽：居中 544，左右可拖到岛体贴住屏幕边缘（±810）。
        assert_eq!(drag_limits(m,300.0,1.0,0.0),Some((-810.0,810.0)));
        assert_eq!(island_origin_for(m,832.0,1.0,Some(100.0),300.0,0.0),Some(((644,0),100.0)));
        assert_eq!(island_origin_for(m,832.0,1.0,Some(-100.0),300.0,0.0),Some(((444,0),-100.0)));
        assert_eq!(island_origin_for(m,832.0,1.0,None,300.0,0.0),Some(((544,0),0.0)));
        // 拖到左边缘：岛体左边贴住屏幕 0，透明承载余量可以出屏。
        let (edge,applied)=island_origin_for(m,832.0,1.0,Some(-5000.0),300.0,0.0).unwrap();
        assert_eq!(edge,(-266,0));assert!((applied+810.0).abs()<0.01,"{applied}");
        assert_eq!(edge.0 as f32+(832.0-300.0)/2.0,0.0);
        // 非有限值按居中处理，不能把窗口甩出屏幕。
        assert_eq!(island_origin_for(m,832.0,1.0,Some(f32::NAN),300.0,0.0),Some(((544,0),0.0)));
    }
    #[test] fn right_side_reserves_room_for_the_notice_badge(){
        let m=Bounds{left:0,top:0,right:1920,bottom:1080};
        // 右侧预留 52 点给收起态通知徽标，左侧不留；岛体仍然完整可见。
        assert_eq!(drag_limits(m,300.0,1.0,52.0),Some((-810.0,758.0)));
        let (origin,applied)=island_origin_for(m,832.0,1.0,Some(5000.0),300.0,52.0).unwrap();
        assert_eq!(applied,758.0);
        let body_right=origin.0 as f32+(832.0+300.0)/2.0;
        assert!((body_right-(1920.0-52.0)).abs()<0.01,"岛体右侧应给通知徽标留出空间：{body_right}");
        // 最宽的岛：左右范围随岛体宽度收缩。
        assert_eq!(drag_limits(m,832.0,1.0,52.0),Some((-544.0,492.0)));
        // 屏幕比岛体还窄时不可拖，保持居中。
        assert_eq!(drag_limits(Bounds{left:0,top:0,right:600,bottom:800},832.0,1.0,52.0),Some((0.0,0.0)));
        assert_eq!(drag_limits(m,300.0,f32::NAN,52.0),None);
    }
    #[test] fn dragging_scales_with_dpi_and_negative_origins(){
        let mixed=Bounds{left:-2560,top:-400,right:0,bottom:1040};
        // 2560 宽的屏按 125% 缩放：承载宽度 1040，居中 -1904。
        assert_eq!(island_origin_for(mixed,832.0,1.5,None,832.0,0.0),Some(((-1904,-400),0.0)));
        assert_eq!(island_origin_for(mixed,832.0,1.5,Some(40.0),832.0,0.0),Some(((-1844,-400),40.0)));
        let (origin,applied)=island_origin_for(mixed,832.0,1.5,Some(-1000.0),832.0,0.0).unwrap();
        assert_eq!(origin,(-2560,-400),"拖到左边缘应贴住屏内");assert!(applied<0.0);
        // 2.0 倍缩放时同样的逻辑偏移对应两倍物理像素。
        let high=Bounds{left:200,top:-1440,right:2760,bottom:0};
        assert_eq!(island_origin_for(high,832.0,2.0,Some(10.0),832.0,0.0),Some(((668,-1440),10.0)));
    }
    #[test] fn narrow_display_keeps_the_island_centered_without_dragging(){
        let narrow=Bounds{left:0,top:0,right:600,bottom:800};
        let (origin,applied)=island_origin_for(narrow,832.0,1.0,Some(300.0),832.0,52.0).unwrap();
        assert_eq!(origin,(-116,0),"比承载宽度窄的屏幕保持原有居中行为");
        assert_eq!(applied,0.0);
        assert_eq!(drag_limits(narrow,832.0,1.0,0.0),Some((0.0,0.0)));
    }
    #[test] fn trackpad_sized_offsets_round_to_physical_pixels(){
        let m=Bounds{left:0,top:0,right:1920,bottom:1080};
        // 1.25 倍缩放：承载宽度 1040，居中 440；33.3 点 ≈ 42 物理像素。
        let Some(((x,_),applied))=island_origin_for(m,832.0,1.25,Some(33.3),832.0,0.0) else {panic!()};
        assert_eq!(x,482);
        assert!((applied-33.6).abs()<0.01,"{applied}");
    }
    #[test] fn changing_primary_unplugging_and_dpi_recompute_without_stale_state(){
        let a=Bounds{left:0,top:0,right:1920,bottom:1080};
        let b=Bounds{left:-2560,top:0,right:0,bottom:1440};
        assert_ne!(island_origin(a,640.0,1.0),island_origin(b,640.0,1.5));
        assert_eq!(island_origin(a,640.0,1.0),Some((640,0)));
        assert_eq!(island_origin(a,640.0,2.0),Some((320,0)));
        assert_eq!(island_origin(a,640.0,f32::NAN),None);
    }
}

/// 只有岛仔所在屏幕的前台全屏窗口才触发隐藏。
pub fn hide_for_fullscreen(enabled:bool,fullscreen:Option<Bounds>,island:Option<Bounds>)->bool {
    enabled && fullscreen.is_some() && fullscreen==island
}

#[cfg(test)]
mod fullscreen_tests {
    use super::*;
    #[test]
    fn fullscreen_on_another_monitor_keeps_island_visible(){
        let primary=Bounds{left:0,top:0,right:1920,bottom:1080};
        for secondary in [Bounds{left:-2560,top:0,right:0,bottom:1440},Bounds{left:1920,top:-200,right:4480,bottom:1240},Bounds{left:0,top:-1440,right:2560,bottom:0}] {
            assert!(!hide_for_fullscreen(true,Some(secondary),Some(primary)));
            assert!(!hide_for_fullscreen(true,Some(primary),Some(secondary)));
            assert!(hide_for_fullscreen(true,Some(secondary),Some(secondary)));
        }
        assert!(hide_for_fullscreen(true,Some(primary),Some(primary)));
        assert!(!hide_for_fullscreen(false,Some(primary),Some(primary)));
        assert!(!hide_for_fullscreen(true,None,Some(primary)));
        assert!(!hide_for_fullscreen(true,None,None));
        assert!(!hide_for_fullscreen(true,Some(primary),None));
    }
}
