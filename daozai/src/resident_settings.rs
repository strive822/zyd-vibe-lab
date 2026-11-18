use crate::{bar_layout::*,paint::{self,Card,H},theme::{self,W}};
use eframe::egui::{self,Color32,RichText,Rect,Pos2,Vec2};

impl crate::app::App {
    /// 使用真实电量、宠物、页开关和常驻账号条件，不给隐藏组件留占位。
    pub(crate) fn resident_preview_layout(&self)->Layout {
        let mut pages = self.settings.visible_pages;
        pages[8] &= self.weather_pill().is_some();
        let layout = Layout::new(self.settings.show_battery && self.resident_power.0.is_some(),
            self.quota_bar_indices().len(), pages, false, self.pet_enabled());
        self.style_resident_preview(layout, &self.settings.resident_order)
    }

    fn style_resident_preview(&self, mut layout: Layout, order: &[usize]) -> Layout {
        layout.reorder(order);
        if self.settings.clock_period != 0 { layout.widen_clock(40.0); }
        if self.settings.clock_seconds { layout.widen_clock(24.0); }
        if !self.settings.show_clock { layout.hide_clock(); }
        layout
    }

    fn resident_preview_layout_for(&self, ctx: &egui::Context, order: &[usize]) -> Layout {
        // 排列预览保留停用的项目，仍可调整它们的顺序。
        let mut layout = Layout::new(true, self.quota_bar_indices().len(), [true; 9], false, true);
        layout.reorder(order);
        if self.settings.clock_period != 0 { layout.widen_clock(40.0); }
        if self.settings.clock_seconds { layout.widen_clock(24.0); }
        for (position, extra) in self.quota_balance_layout(ctx) { layout.balance_tail(position, extra); }
        if let Some(extra) = self.weather_pill_extra(ctx) { layout.widen(WEATHER, extra); }
        layout
    }

    /// 首次拖动以当前可见顺序为准；隐藏组件仍保留在完整顺序中。
    pub(crate) fn resident_edit_order(&self)->Vec<usize> {
        if valid_order(&self.settings.resident_order){return self.settings.resident_order.clone();}
        let layout=self.resident_preview_layout();
        let mut shown:Vec<_>=DEFAULT_ORDER.into_iter().filter(|slot|layout.x[*slot].is_some()).collect();
        shown.sort_by(|a,b|layout.x[*a].unwrap().total_cmp(&layout.x[*b].unwrap()));
        let mut shown=shown.into_iter();
        DEFAULT_ORDER.into_iter().map(|slot|if layout.x[slot].is_some(){shown.next().unwrap()}else{slot}).collect()
    }

    pub(crate) fn resident_order_settings(&mut self,ui:&mut egui::Ui){
        let default=DEFAULT_ORDER.to_vec();
        let mut order=self.resident_edit_order();
        ui.horizontal(|ui|{
            ui.label(RichText::new("拖动岛上的图标").color(ui.visuals().text_color()));
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center),|ui|{
                if ui.small_button("恢复默认").clicked(){self.settings.resident_order.clear();order=default;}
            });
        });
        ui.add_space(12.0);
        let weather_snapshot = self.weather_pill().cloned();
        let displayed = self.resident_preview_layout();
        let layout = self.resident_preview_layout_for(ui.ctx(), &order);
        let (stage,_)=ui.allocate_exact_size(Vec2::new(ui.available_width(),100.0),egui::Sense::hover());
        ui.painter().rect_filled(stage,10.0,Color32::from_rgb(19,25,36));
        let scale=((stage.width()-28.0)/layout.width).min(1.0);
        let origin=Pos2::new(stage.center().x-layout.width*scale/2.0,stage.top());
        // 预览跟随当前的皮肤与形状。
        let pill=self.settings.island_shape==crate::model::IslandShape::Pill;
        let origin=if pill{origin+Vec2::new(0.0,4.0)}else{origin};
        let body=Rect::from_min_size(origin,Vec2::new(layout.width*scale,30.0*scale));
        let fill=self.preview_fill();
        if pill {ui.painter().rect_filled(body,15.0*scale,fill);}
        else {crate::shape::fill(ui.painter(),body,8.0*scale,10.0*scale,12.0*scale,fill,1.0/ui.ctx().pixels_per_point());}
        if self.settings.skin.is_glass() {
            let rim=egui::Stroke::new(1.0_f32,Color32::from_white_alpha(60));
            if pill {ui.painter().rect_stroke(body,15.0*scale,rim,egui::StrokeKind::Inside);}
            else {
                let edge=Rect::from_min_max(body.min+Vec2::new(0.5,0.0),body.max-Vec2::new(0.5,0.5));
                ui.painter().add(egui::Shape::line(crate::shape::outline(edge,8.0*scale,10.0*scale,12.0*scale-0.5),rim));
            }
        }
        let content_from=crate::skin_paint::shape_count(ui.ctx(),ui.layer_id());
        let mut card=Card::new(ui,origin,stage);card.s=scale;
        let cx=layout.width/2.0;
        let pointer=ui.ctx().pointer_interact_pos();
        let dragged=egui::DragAndDrop::payload::<usize>(ui.ctx());
        let mut movement=None;
        let label=|slot|match slot{CLOCK=>"时间",WEATHER=>"天气",BATTERY=>"电量",QUOTA=>"AI 额度",MUSIC=>"音乐",FOCUS=>"专注",WATER=>"饮水",SHELF=>"暂存站",TODO=>"待办",CAL=>"日程",_=>"吉祥物"};
        for (index,&slot) in order.iter().enumerate(){
            let Some(x) = layout.x[slot].map(|x| cx + x) else { continue; };
            let width = if slot == QUOTA {
                let left = layout.quota_slots().filter_map(|i| layout.x[i].map(|x| x - layout.widths[i] / 2.0)).fold(f32::INFINITY, f32::min);
                let right = layout.quota_slots().filter_map(|i| layout.x[i].map(|x| x + layout.widths[i] / 2.0)).fold(f32::NEG_INFINITY, f32::max);
                right - left
            } else { layout.widths[slot] };
            let left=if slot==QUOTA{cx+layout.quota_slots().filter_map(|i|layout.x[i].map(|x|x-layout.widths[i]/2.0)).fold(f32::INFINITY,f32::min)}else{x-width/2.0};
            let rect=card.rect(left-5.0,1.0,width+10.0,28.0);
            let response=ui.interact(rect,ui.id().with(("resident-icon",slot)),egui::Sense::click_and_drag()).on_hover_cursor(egui::CursorIcon::Grab);
            response.dnd_set_drag_payload(slot);
            if let (Some(from),Some(point))=(dragged.as_deref(),pointer){
                if *from!=slot && rect.contains(point) && ui.input(|i|i.pointer.primary_down()){movement=Some((*from,index));}
            }
            let is_dragged=dragged.as_deref()==Some(&slot);
            let dx=if is_dragged{pointer.map(|p|((p.x-origin.x)/scale-(left+width/2.0)).clamp(-left,layout.width-left-width)).unwrap_or(0.0)}else{0.0};
            if is_dragged {ui.ctx().set_cursor_icon(egui::CursorIcon::Grabbing);}
            else if response.hovered(){ui.painter().rect_filled(rect,6.0,Color32::from_white_alpha(18));}
            let opacity = if displayed.x[slot].is_some() { 1.0 } else { 0.35 };
            let c=card.shifted(dx,0.0).faded(opacity).ghost();
            match slot{
                BATTERY=>paint::battery(&c,x,15.0,self.resident_power.0,self.resident_power.1,1.0),
                CLOCK=>{let text=self.settings.clock_text(&chrono::Local::now().format("%H:%M:%S").to_string());paint::clock(&c,x-paint::clock_width(&c,&text,theme::size::PILL_CLOCK)/2.0,21.0,&text,theme::size::PILL_CLOCK);},
                WEATHER=>if let Some(snapshot)=weather_snapshot.as_ref(){self.paint_pill_weather(&c,x,&layout,snapshot);}else{
                    c.text(x,20.0,"天气",10.0,W::Regular,theme::WHITE,H::Center);
                },
                PET=>self.pet.draw(&c,x,self.t,self.skin_palette()),
                MUSIC if self.media.is_music()=>paint::playback_bars(&c,x,15.0,self.t,self.media.playing,theme::WHITE),
                MUSIC=>paint::note(&c,x,15.0,13.0,theme::WHITE),
                FOCUS=>crate::focus_bar::draw(&c,x,15.0,self.t,&crate::app::Pomo{phase:self.pomo.phase,remaining:if self.pomo.remaining>0.0{self.pomo.remaining}else{self.phase_secs(self.pomo.phase)},running:self.pomo.running},self.phase_secs(self.pomo.phase),false),
                QUOTA=>self.draw_quota_bar(&c,cx,&layout),
                WATER|SHELF|TODO|CAL=>{
                    let today=chrono::Local::now().format("%Y-%m-%d").to_string();
                    paint::page_entry_icon(&c,slot_page(slot).unwrap(),x,self.water.drunk_ml as f32/self.water.goal_ml.max(1) as f32,self.todos.items.iter().filter(|t|t.done_on.is_none()).count(),&self.calendar_entry_label(&today))
                },
                _=>{},
            }
            if is_dragged {ui.painter().line_segment([Pos2::new(rect.center().x,body.bottom()+6.0),Pos2::new(rect.center().x,body.bottom()+12.0)],egui::Stroke::new(2.0_f32,theme::BLUE));}
            response.on_hover_text(label(slot));
        }
        if let Some(palette)=self.skin_palette() {
            let end=crate::skin_paint::shape_count(ui.ctx(),ui.layer_id());
            crate::skin_paint::recolor_layer(ui.ctx(),ui.layer_id(),&[(content_from,end)],&palette);
        }
        if let Some((slot,index))=movement{
            if let Some(from)=order.iter().position(|value|*value==slot){order.remove(from);order.insert(index,slot);self.settings.resident_order=order;}
        }
        if let Some(x)=layout.x[BELL]{paint::bell(&card,cx+x,14.0,theme::WHITE,0.0);}
        ui.painter().text(Pos2::new(stage.center().x,stage.bottom()-22.0),egui::Align2::CENTER_CENTER,"按住图标左右拖动",theme::font(11.0,W::Regular),Color32::from_gray(160));
    }
}
