//! 常驻组件按实际占位排布，并在开关变化时连续补位。
use crate::anim::{smoothstep, Spring};

pub(crate) const CLOCK: usize = 0;
pub(crate) const BATTERY: usize = 1;
pub(crate) const QUOTA: usize = 2;
/// 常驻条最多同时显示 8 个额度环；更多账号在「AI 额度」页查看。
pub(crate) const MAX_QUOTA: usize = 8;
/// 额度整组占用的槽位范围（用于排序与淡出计算）。
pub(crate) const MORE: usize = QUOTA + MAX_QUOTA - 1;
pub(crate) const MUSIC: usize = QUOTA + MAX_QUOTA;
pub(crate) const FOCUS: usize = MUSIC + 1;
pub(crate) const BELL: usize = MUSIC + 2;
pub(crate) const PET: usize = MUSIC + 3;
/// 饮水、暂存站、待办、日程：页入口与专用槽一样只占一个图标位。
pub(crate) const WATER: usize = MUSIC + 4;
pub(crate) const SHELF: usize = MUSIC + 5;
pub(crate) const TODO: usize = MUSIC + 6;
pub(crate) const CAL: usize = MUSIC + 7;
const SLOTS: usize = CAL + 1;
const ICON: f32 = 18.0;
const GAP: f32 = 10.0;
const MARGIN: f32 = 16.0;
const RING: f32 = 27.0;
const WIDTHS: [f32; SLOTS] = [
    44.0, 20.0,
    RING, RING, RING, RING, RING, RING, RING, RING,
    14.0, crate::focus_bar::WIDTH, 20.0, 32.0,
    ICON, ICON, ICON, ICON,
];

/// 可排序的常驻槽：六个原有组件 + 四个页入口（铃铛固定收尾，不参与排序）。
pub(crate) const ORDER: [usize;10]=[BATTERY,PET,CLOCK,QUOTA,MUSIC,FOCUS,WATER,SHELF,TODO,CAL];
pub(crate) const DEFAULT_ORDER: [usize;10]=ORDER;
pub(crate) fn valid_order(order:&[usize])->bool {
    order.len()==ORDER.len() && ORDER.iter().all(|slot|order.iter().filter(|value|*value==slot).count()==1)
}
/// 页槽 → 页号（与 `page_slot` 互逆）。
/// 邮箱用铃铛槽（不再只在通知时存在），AI 额度用额度组首槽：
/// 无账号时该槽变作「连接 AI」入口，不会因为通知/无账号而消失（F04）。
pub(crate) fn slot_page(slot:usize)->Option<usize>{(0..8).find(|page|page_slot(*page)==slot)}
/// v0.6.40 的六个常驻槽旧编号 → 当前稳定槽。
/// 旧编号：0 时钟、1 电量、2 额度、6 音乐、7 专注、9 吉祥物。
/// 后来在专注与吉祥物之间插入额度组与四个页入口，数字整体后移，
/// 所以不能拿新常量去识别旧持久化值（F15）。
pub(crate) const LEGACY_SIX: [(usize, usize); 6] = [(0, CLOCK), (1, BATTERY), (2, QUOTA), (6, MUSIC), (7, FOCUS), (9, PET)];

/// 旧配置只存六个组件：先把旧编号翻译成稳定槽，再按 `page_order` 补齐新增页入口。
pub(crate) fn migrate_order(order:&[usize],pages:[usize;8])->Option<Vec<usize>> {
    if valid_order(order){return Some(order.to_vec());}
    if order.len()!=6{return None;}
    // 兼容两种来源：已是新编号的六值，或真正的旧编号。
    let translated: Vec<usize> = if ORDER[..6].iter().all(|slot|order.iter().filter(|value|*value==slot).count()==1) {
        order.to_vec()
    } else {
        order.iter().map(|value|LEGACY_SIX.iter().find(|(old,_)|old==value).map(|(_,new)|*new)).collect::<Option<Vec<_>>>()?
    };
    if !ORDER[..6].iter().all(|slot|translated.iter().filter(|value|*value==slot).count()==1){return None;}
    let mut out=translated;
    for (rank,&page) in pages.iter().enumerate() {
        let slot=page_slot(page);
        if !ORDER[6..].contains(&slot){continue;}
        let at=pages[..rank].iter().rev().filter_map(|p|out.iter().position(|v|*v==page_slot(*p))).next().map(|index|index+1)
            .or_else(||pages[rank+1..].iter().filter_map(|p|out.iter().position(|v|*v==page_slot(*p))).next())
            .unwrap_or(out.len());
        out.insert(at,slot);
    }
    Some(out)
}

/// 页顺序（`settings.page_order`）→ 常驻页槽。日程固定用 CAL。
/// 八个页号全部有稳定槽：音乐/专注/饮水/暂存/待办/邮箱/额度/日程。
pub(crate) fn page_slot(page:usize)->usize{match page{0=>MUSIC,1=>FOCUS,2=>WATER,3=>SHELF,4=>TODO,5=>BELL,6=>QUOTA,7=>CAL,_=>usize::MAX}}

pub(crate) fn animations_enabled()->bool {
    #[cfg(windows)] {
        static ENABLED:std::sync::OnceLock<bool>=std::sync::OnceLock::new();
        *ENABLED.get_or_init(||{
            use windows::Win32::{Foundation::BOOL,UI::WindowsAndMessaging::*};
            let mut enabled=BOOL(1);
            unsafe {let _=SystemParametersInfoW(SPI_GETCLIENTAREAANIMATION,0,Some((&mut enabled as *mut BOOL).cast()),SYSTEM_PARAMETERS_INFO_UPDATE_FLAGS(0));}
            enabled.as_bool()
        })
    }
    #[cfg(not(windows))] {true}
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct Layout {
    pub width: f32,
    pub x: [Option<f32>; SLOTS],
}

impl Layout {
    /// `_bell` 保留在签名里只为不改调用方：铃铛自 F04 起常驻（`pages[5]`），
    /// 通知状态不再参与布局，否则通知会把额度组或功能页顶掉。
    pub fn new(battery:bool,quotas:usize,pages:[bool;8],_bell:bool,pet:bool)->Self {
        fn place(cursor:&mut f32,width:f32)->f32 {let x=*cursor+width/2.0;*cursor+=width+GAP;x}
        let mut x=[None;SLOTS];let mut cursor=MARGIN;
        let count=quotas.min(MAX_QUOTA);
        let order=if battery {[BATTERY,CLOCK,QUOTA]}else{[QUOTA,CLOCK,BATTERY]};
        for slot in order {
            match slot {
                BATTERY if battery=>x[slot]=Some(place(&mut cursor,WIDTHS[slot])),
                CLOCK=>{
                    if pet {x[PET]=Some(place(&mut cursor,WIDTHS[PET]));}
                    x[slot]=Some(place(&mut cursor,WIDTHS[slot]));
                },
                QUOTA if count>0&&pages[6]=>{
                    let width=count as f32*27.0+(count.saturating_sub(1)) as f32*7.0;
                    let left=place(&mut cursor,width)-width/2.0;
                    for i in 0..count {x[QUOTA+i]=Some(left+13.5+i as f32*34.0);}
                },
                // 无账号时额度组空着，但页入口不能消失：占一个环位作为「连接 AI」入口。
                QUOTA if count==0&&pages[6]=>{x[QUOTA]=Some(place(&mut cursor,RING));},
                _=>{},
            }
        }
        // 页入口：音乐、专注沿用原有专用槽，其余依次补在后面；邮箱固定用铃铛槽，
        // 与临时通知状态解耦——通知只叠加摇摆/小红点，不再顶掉常驻入口（F04）。
        for page in 0..8 {
            if !pages[page]{continue;}
            let slot=page_slot(page);
            if slot==usize::MAX||slot==BELL {continue;}
            if x[slot].is_none(){x[slot]=Some(place(&mut cursor,WIDTHS[slot]));}
        }
        if pages[5] {x[BELL]=Some(place(&mut cursor,WIDTHS[BELL]));}
        let width=cursor-GAP+MARGIN;
        for value in x.iter_mut().flatten() {*value-=width/2.0;}
        Self {width:width.max(96.0),x}
    }
    pub fn widen_clock(&mut self, extra:f32) {
        let clock=self.x[CLOCK].unwrap();
        for (slot,x) in self.x.iter_mut().enumerate() {
            if slot!=CLOCK { if let Some(x)=x { *x+=if *x<clock {-extra/2.0}else{extra/2.0}; } }
        }
        self.width+=extra;
    }
    pub fn reorder(&mut self,order:&[usize]) {
        if !valid_order(order){return;}
        let original=self.x;let mut cursor=-self.width/2.0+MARGIN;
        for slot in order.iter().copied().chain(std::iter::once(BELL)) {
            let slots:Vec<usize>=if slot==QUOTA{(QUOTA..=MORE).collect()}else{vec![slot]};
            let left=slots.iter().filter_map(|&i|original[i].map(|x|x-WIDTHS[i]/2.0)).fold(f32::INFINITY,f32::min);
            let right=slots.iter().filter_map(|&i|original[i].map(|x|x+WIDTHS[i]/2.0)).fold(f32::NEG_INFINITY,f32::max);
            if !left.is_finite(){continue;}
            for i in slots {if let Some(x)=original[i]{self.x[i]=Some(cursor+x-left);}}
            cursor+=right-left+GAP;
        }
    }
    /// 圆环换边经过时钟时，暂时淡出时钟，避免移动中相互遮挡。
    pub fn clearance(&self,slot:usize)->f32 {
        let Some(x)=self.x[slot] else{return 0.0;};
        let distance=self.x[QUOTA..=MORE].iter().flatten().map(|other|(other-x).abs()).fold(f32::INFINITY,f32::min);
        let quota=if slot==CLOCK {smoothstep(32.0,42.0,distance)}else{smoothstep(22.0,34.0,distance)};
        quota*self.pet_clearance(slot)
    }
    pub fn pet_clearance(&self,slot:usize)->f32 {
        match (self.x[slot],self.x[PET]) {
            (Some(x),Some(pet))=>smoothstep(WIDTHS[slot]/2.0+14.0,WIDTHS[slot]/2.0+24.0,(x-pet).abs()),
            _=>1.0,
        }
    }
}

pub(crate) struct Motion {
    pub target: Layout,
    positions: [Spring; SLOTS],
    initialized: bool,
}
impl Default for Motion {
    fn default()->Self {Self {target:Layout::new(false,0,[false;8],false,false),positions:[Spring::new(0.0,360.0,0.76);SLOTS],initialized:false}}
}
impl Motion {
    pub fn step(&mut self,target:Layout,dt:f32,animate:bool) {
        for (i,x) in target.x.iter().enumerate() {
            if let Some(x)=x {
                let spring=&mut self.positions[i];spring.target=*x;
                if !self.initialized || self.target.x[i].is_none() || !animate {spring.snap(*x);}else{spring.step(dt);}
            }
        }
        self.target=target;self.initialized=true;
    }
    pub fn current(&self)->Layout {
        let mut layout=self.target;
        for (i,x) in layout.x.iter_mut().enumerate() {if x.is_some(){*x=Some(self.positions[i].pos);}}
        layout
    }
    pub fn position(&self,slot:usize)->f32 {self.positions[slot].pos}
    pub fn settled(&self)->bool {self.target.x.iter().enumerate().all(|(i,x)|x.is_none()||self.positions[i].settled(100.0))}
}

#[cfg(test)]
mod tests {
    use super::*;
    fn only(pages:&[usize])->[bool;8]{let mut v=[false;8];for p in pages{v[*p]=true;}v}

    #[test]
    fn clock_12h_keeps_components_separate_in_custom_orders(){
        for order in [DEFAULT_ORDER,[FOCUS,MUSIC,QUOTA,CLOCK,PET,BATTERY,WATER,SHELF,TODO,CAL]] {
            for quotas in 0..=5 {
                let mut layout=Layout::new(true,quotas,[true;8],false,true);
                layout.reorder(&order);layout.widen_clock(40.0);
                let mut boxes:Vec<_>=layout.x.iter().enumerate().filter_map(|(i,x)|x.map(|x|{
                    let width=WIDTHS[i]+if i==CLOCK {40.0}else{0.0};
                    (x-width/2.0,x+width/2.0)
                })).collect();
                boxes.sort_by(|a,b|a.0.total_cmp(&b.0));
                assert!(boxes.windows(2).all(|p|p[1].0-p[0].1>=6.9));
                assert!(boxes.first().unwrap().0>=-layout.width/2.0+15.9);
                assert!(boxes.last().unwrap().1<=layout.width/2.0-15.9);
            }
        }
    }
    #[test]
    fn custom_order_preserves_groups_and_hidden_positions(){
        assert!(!valid_order(&[0,0,2,6,7,9]));
        assert!(!valid_order(&[0,1,2]));
        let order=[FOCUS,MUSIC,QUOTA,CLOCK,PET,BATTERY,CAL,TODO,SHELF,WATER];
        for battery in [false,true]{for count in 0..=5 {
            let mut layout=Layout::new(battery,count,only(&[0,1,2,3,4,6,7]),false,true);
            let width=layout.width;layout.reorder(&order);
            assert_eq!(layout.width,width);
            let positions:Vec<_>=order.iter().filter_map(|i|layout.x[*i]).collect();
            assert!(positions.windows(2).all(|p|p[0]<p[1]));
            if count>1 {assert_eq!(layout.x[QUOTA+1].unwrap()-layout.x[QUOTA].unwrap(),34.0);}
            let mut boxes:Vec<_>=layout.x.iter().enumerate().filter_map(|(i,x)|x.map(|x|(x-WIDTHS[i]/2.0,x+WIDTHS[i]/2.0))).collect();
            boxes.sort_by(|a,b|a.0.total_cmp(&b.0));
            assert!(boxes.windows(2).all(|p|p[1].0-p[0].1>=6.9));
        }}
    }
    #[test]
    fn every_component_combination_fits_without_overlaps(){
        for quotas in 0..=8 {for battery in [false,true] {for bell in [false,true] {for pet in [false,true] {
            let layout=Layout::new(battery,quotas,only(&[0,1,2,3,4,5,6,7]),bell,pet);
            let mut boxes:Vec<_>=layout.x.iter().enumerate().filter_map(|(i,x)|x.map(|x|(x-WIDTHS[i]/2.0,x+WIDTHS[i]/2.0))).collect();
            boxes.sort_by(|a,b|a.0.total_cmp(&b.0));
            assert!(boxes.first().unwrap().0>=-layout.width/2.0+MARGIN-0.1);
            assert!(boxes.last().unwrap().1<=layout.width/2.0-MARGIN+0.1);
            assert!(boxes.windows(2).all(|pair|pair[1].0-pair[0].1>=6.9),"组件不能挤在一起：{layout:?}");
            assert_eq!(layout.clearance(CLOCK),1.0,"静止时时钟必须完全显示：{layout:?}");
        }}}}
    }
    /// N7/F04：八个页面的 255 种非空组合都要有入口、互不重叠，并记录宽度。
    #[test]
    fn every_non_empty_page_combination_has_an_entry(){
        let mut widest=(0usize,0.0f32);
        for mask in 1u16..256 {
            let mut pages=[false;8];for page in 0..8{if mask&(1<<page)!=0{pages[page]=true;}}
            let layout=Layout::new(true,3,pages,false,true);
            let mut boxes=Vec::new();
            for page in 0..8 {
                let slot=page_slot(page);
                if !pages[page] {continue;}
                // 八个页号都必须有稳定槽，不再有 usize::MAX 的漏网页。
                assert!(slot!=usize::MAX,"页 {page} 必须映射到常驻槽，不能跳过");
                let x=layout.x[slot].unwrap_or_else(||panic!("页 {page} 启用后必须有入口：{pages:?}"));
                boxes.push((page,x-WIDTHS[slot]/2.0,x+WIDTHS[slot]/2.0));
            }
            assert_eq!(boxes.len(),pages.iter().filter(|on|**on).count(),"每个启用页都要有入口");
            boxes.sort_by(|a,b|a.1.total_cmp(&b.1));
            assert!(boxes.windows(2).all(|p|p[1].1-p[0].2>=6.9),"页入口不能重叠：{pages:?}");
            if layout.width>widest.1 {widest=(mask as usize,layout.width);}
        }
        println!("八页全开最宽 {:.1}px（PW=419）",widest.1);
        assert!(widest.1<=560.0,"超出窗口可用宽度：{:.1}",widest.1);
    }
    #[test]
    fn real_v064_eight_slot_default_order_migrates() {
        // v0.6.40 实际落盘的默认六槽（旧编号），不是当前常量。
        let legacy=[1usize,9,0,2,6,7];
        let order=migrate_order(&legacy,[0,1,2,3,4,5,6,7]).expect("真实旧配置必须能迁移，不能返回 None");
        assert!(valid_order(&order));
        let kept:Vec<_>=order.iter().copied().filter(|slot|[BATTERY,PET,CLOCK,QUOTA,MUSIC,FOCUS].contains(slot)).collect();
        assert_eq!(kept,[BATTERY,PET,CLOCK,QUOTA,MUSIC,FOCUS],"旧顺序的相对次序必须保持");
        for page in 0..8 {
            let slot=page_slot(page);
            if slot==BELL {continue;} // 铃铛固定收尾，不参与排序
            assert!(order.contains(&slot),"页 {page} 的槽要入列");
        }
        assert_eq!(order.len(),ORDER.len());
    }

    #[test]
    fn legacy_six_slot_order_migrates_into_page_slots(){
        let legacy=[CLOCK,BATTERY,PET,QUOTA,MUSIC,FOCUS];
        let order=migrate_order(&legacy,[0,1,2,3,4,5,6,7]).unwrap();
        assert!(valid_order(&order));
        let kept:Vec<_>=order.iter().copied().filter(|slot|legacy.contains(slot)).collect();
        assert_eq!(kept,legacy,"旧配置的相对顺序必须原样保留");
        // 默认页顺序下：饮水/暂存站/待办紧跟专注，日程跟在额度之后。
        let at=|slot|order.iter().position(|value|*value==slot).unwrap();
        assert!(at(FOCUS)<at(WATER)&&at(WATER)<at(SHELF)&&at(SHELF)<at(TODO));
        assert!(at(QUOTA)<at(CAL));
        // 页顺序改变时按稳定页标识补位：日程排到最前时落在第一个页入口之前，但不越过电量/吉祥物/时钟。
        let order=migrate_order(&legacy,[7,0,1,2,3,4,5,6]).unwrap();
        assert!(valid_order(&order));
        let at=|slot|order.iter().position(|value|*value==slot).unwrap();
        assert!(at(CAL)<at(MUSIC)&&at(CAL)>at(QUOTA));
        // 残缺或重复的旧配置不迁移。
        assert!(migrate_order(&[CLOCK,CLOCK,BATTERY,PET,QUOTA,MUSIC], [0,1,2,3,4,5,6,7]).is_none());
    }

    #[test]
    fn hidden_pages_leave_no_slot_and_one_page_is_always_possible(){
        let layout=Layout::new(true,3,[true,false,false,false,false,false,false,false],false,true);
        assert!(layout.x[MUSIC].is_some());
        for slot in [FOCUS,WATER,SHELF,TODO,CAL] {assert!(layout.x[slot].is_none(),"未启用页不能占位");}
        let layout=Layout::new(true,0,only(&[3]),false,false);
        assert!(layout.x[SHELF].is_some()&&layout.x[CAL].is_none());
    }
    #[test]
    fn replacing_battery_moves_continuously_and_supports_an_instant_state(){
        let before=Layout::new(true,1,only(&[0,6]),false,true);let after=Layout::new(false,1,only(&[0,6]),false,true);
        let mut motion=Motion::default();motion.step(before,0.0,true);
        motion.step(after,1.0/60.0,true);let mid=motion.current().x[QUOTA].unwrap();
        assert!(mid<before.x[QUOTA].unwrap()&&mid>after.x[QUOTA].unwrap());
        for _ in 0..120 {motion.step(after,1.0/60.0,true);}
        assert!((motion.current().x[QUOTA].unwrap()-after.x[QUOTA].unwrap()).abs()<0.01);
        motion.step(before,1.0/60.0,false);assert_eq!(motion.current().x,before.x);
    }
}
