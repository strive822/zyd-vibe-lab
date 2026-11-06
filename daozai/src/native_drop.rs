//! OLE drop target. Protocol references and dependency provenance: THIRD_PARTY.md.
//! Query formats during hover; materialize bytes only after an accepted COPY drop.
use crate::app::DropData;
use eframe::egui;
use std::{cell::RefCell, rc::Rc, path::PathBuf};
use windows::{core::*, Win32::{Foundation::*, System::{Com::*, DataExchange::RegisterClipboardFormatW, Memory::*, Ole::*, SystemServices::MODIFIERKEYS_FLAGS}, UI::{Shell::*, Input::KeyboardAndMouse::GetAsyncKeyState}}};

const LIMIT:usize=128*1024*1024;
const TOTAL:usize=256*1024*1024;
const ITEMS:usize=128;
const FILES:u16=15;
const TEXT:u16=13;
const DIB:u16=8;

#[derive(Default)]
struct State { enabled:bool, hovering:bool, supported:bool, items:Vec<DropData>, error:Option<String> }

pub(crate) struct Target { hwnd:HWND, state:Rc<RefCell<State>>, _target:IDropTarget }
impl Target {
    pub fn register(hwnd:HWND,ctx:egui::Context)->Result<Self>{unsafe{
        OleInitialize(None)?;
        let state=Rc::new(RefCell::new(State::default()));
        let target:IDropTarget=Receiver{state:state.clone(),ctx}.into();
        if let Err(e)=RegisterDragDrop(hwnd,&target){OleUninitialize();return Err(e);}
        Ok(Self{hwnd,state,_target:target})
    }}
    pub fn enable(&self,enabled:bool){self.state.borrow_mut().enabled=enabled;}
    pub fn take(&self)->(bool,Vec<DropData>,Option<String>){
        let mut state=self.state.borrow_mut();
        (state.hovering,std::mem::take(&mut state.items),state.error.take())
    }
}
impl Drop for Target {fn drop(&mut self){unsafe{let _=RevokeDragDrop(self.hwnd);OleUninitialize();}}}

#[implement(IDropTarget)]
struct Receiver {state:Rc<RefCell<State>>,ctx:egui::Context}
impl Receiver {
    fn effect(&self,effect:*mut DROPEFFECT)->Result<()> {
        if effect.is_null(){return Err(Error::from_hresult(E_POINTER));}
        let s=self.state.borrow();
        // Check physical state again at the native callback, including a key held before entry.
        let pass=passthrough_active();
        unsafe{*effect=if s.enabled&&s.supported&&!pass&&(*effect&DROPEFFECT_COPY)!=DROPEFFECT_NONE {DROPEFFECT_COPY}else{DROPEFFECT_NONE};}
        Ok(())
    }
}

pub(crate) fn passthrough_active()->bool {
    unsafe{GetAsyncKeyState(0xc0)<0 && [0x10,0x11,0x12,0x5b,0x5c].iter().all(|&key|GetAsyncKeyState(key)>=0)}
}
#[allow(non_snake_case)]
impl IDropTarget_Impl for Receiver_Impl {
    fn DragEnter(&self,data:Option<&IDataObject>,_:MODIFIERKEYS_FLAGS,_:&POINTL,effect:*mut DROPEFFECT)->Result<()> {
        let supported=data.is_some_and(supported);
        {let mut s=self.state.borrow_mut();s.supported=supported;s.hovering=supported;}
        self.ctx.request_repaint();self.effect(effect)
    }
    fn DragOver(&self,_:MODIFIERKEYS_FLAGS,_:&POINTL,effect:*mut DROPEFFECT)->Result<()>{self.effect(effect)}
    fn DragLeave(&self)->Result<()>{let mut s=self.state.borrow_mut();s.hovering=false;s.supported=false;self.ctx.request_repaint();Ok(())}
    fn Drop(&self,data:Option<&IDataObject>,_:MODIFIERKEYS_FLAGS,_:&POINTL,effect:*mut DROPEFFECT)->Result<()> {
        self.effect(effect)?;
        let accepted=unsafe{*effect==DROPEFFECT_COPY};
        if accepted {
            let result=data.ok_or_else(||Error::from_hresult(E_INVALIDARG)).and_then(read);
            let mut s=self.state.borrow_mut();
            match result {Ok(items) if !items.is_empty()=>s.items.extend(items),_=>{
                s.error=Some("无法读取拖入内容，未接收；请重试或先保存为文件".into());unsafe{*effect=DROPEFFECT_NONE;}
            }}
        }
        {let mut s=self.state.borrow_mut();s.hovering=false;s.supported=false;}
        self.ctx.request_repaint();Ok(())
    }
}

fn format(id:u16,index:i32,tymed:TYMED)->FORMATETC {FORMATETC{cfFormat:id,dwAspect:DVASPECT_CONTENT.0,lindex:index,tymed:tymed.0 as u32,..Default::default()}}
fn registered(name:PCWSTR)->u16 {unsafe{RegisterClipboardFormatW(name)as u16}}
fn descriptor()->u16{registered(CFSTR_FILEDESCRIPTORW)}
fn contents()->u16{registered(CFSTR_FILECONTENTS)}
fn offers(data:&IDataObject,id:u16,tymed:TYMED)->bool {id!=0&&unsafe{data.QueryGetData(&format(id,-1,tymed))}.is_ok()}
fn supported(data:&IDataObject)->bool {
    offers(data,2,TYMED_GDI) || [FILES,descriptor(),DIB,17,TEXT,registered(w!("PNG")),registered(CFSTR_INETURLW)].iter().any(|&id|offers(data,id,TYMED_HGLOBAL))
}
struct Medium(STGMEDIUM);
impl Drop for Medium {fn drop(&mut self){unsafe{ReleaseStgMedium(&mut self.0);}}}
fn get(data:&IDataObject,id:u16,index:i32,tymed:TYMED)->Result<Medium>{unsafe{data.GetData(&format(id,index,tymed)).map(Medium)}}
fn invalid()->Error{Error::from_hresult(E_INVALIDARG)}
fn global(m:&Medium)->Result<Vec<u8>>{unsafe{
    if m.0.tymed!=TYMED_HGLOBAL.0 as u32{return Err(invalid());}
    let handle=m.0.u.hGlobal;let size=GlobalSize(handle);
    if size>LIMIT{return Err(invalid());}if size==0{return Ok(Vec::new());}
    let ptr=GlobalLock(handle);if ptr.is_null(){return Err(Error::from_win32());}
    let bytes=std::slice::from_raw_parts(ptr as *const u8,size).to_vec();
    let _=GlobalUnlock(handle);Ok(bytes)
}}
fn bytes(m:&Medium)->Result<Vec<u8>>{
    if m.0.tymed==TYMED_HGLOBAL.0 as u32{return global(m);}
    if m.0.tymed!=TYMED_ISTREAM.0 as u32{return Err(invalid());}
    let stream=unsafe{m.0.u.pstm.as_ref()}.ok_or_else(invalid)?;
    let mut output=Vec::new();let mut chunk=[0u8;65536];
    loop {let mut count=0;unsafe{stream.Read(chunk.as_mut_ptr().cast(),chunk.len()as u32,Some(&mut count))}.ok()?;
        if count as usize>chunk.len() || output.len()+count as usize>LIMIT{return Err(invalid());}
        output.extend_from_slice(&chunk[..count as usize]);if count==0{break;}}
    Ok(output)
}
fn unicode(bytes:&[u8])->Result<String>{
    if bytes.len()%2!=0{return Err(invalid());}
    let units:Vec<_>=bytes.chunks_exact(2).map(|p|u16::from_le_bytes([p[0],p[1]])).take_while(|&u|u!=0).collect();
    String::from_utf16(&units).map_err(|_|invalid())
}
fn names(bytes:&[u8])->Result<Vec<String>>{
    let offset=std::mem::offset_of!(FILEGROUPDESCRIPTORW,fgd);
    if bytes.len()<offset{return Err(invalid());}
    let count=u32::from_le_bytes(bytes[..4].try_into().unwrap())as usize;
    let size=std::mem::size_of::<FILEDESCRIPTORW>();
    if count==0||count>ITEMS||bytes.len()<offset+count*size{return Err(invalid());}
    (0..count).map(|i|{
        let descriptor=unsafe{std::ptr::read_unaligned(bytes.as_ptr().add(offset+i*size).cast::<FILEDESCRIPTORW>())};
        let filename=descriptor.cFileName;
        let end=filename.iter().position(|&c|c==0).ok_or_else(invalid)?;
        let name=String::from_utf16(&filename[..end]).map_err(|_|invalid())?;
        if name.is_empty()||name=="."||name==".."||name.chars().any(|c|c.is_control()||"<>:\\/?*\"|".contains(c))||name.ends_with([' ','.']) {return Err(invalid());}
        Ok(name)
    }).collect()
}
fn read(data:&IDataObject)->Result<Vec<DropData>>{
    if offers(data,FILES,TYMED_HGLOBAL){
        let medium=get(data,FILES,-1,TYMED_HGLOBAL)?;
        let handle=unsafe{HDROP(medium.0.u.hGlobal.0)};
        let count=unsafe{DragQueryFileW(handle,u32::MAX,None)};
        if count==0||count as usize>ITEMS{return Err(invalid());}
        return (0..count).map(|i|{
            let len=unsafe{DragQueryFileW(handle,i,None)};if len==0||len>32767{return Err(invalid());}
            let mut path=vec![0u16;len as usize+1];
            if unsafe{DragQueryFileW(handle,i,Some(&mut path))}!=len{return Err(invalid());}
            use std::os::windows::ffi::OsStringExt;
            Ok(DropData::File(PathBuf::from(std::ffi::OsString::from_wide(&path[..len as usize]))))
        }).collect();
    }
    if offers(data,descriptor(),TYMED_HGLOBAL){
        let names=names(&global(&get(data,descriptor(),-1,TYMED_HGLOBAL)?)?)?;
        let mut total=0;let mut result=Vec::new();
        for (index,name) in names.into_iter().enumerate(){
            let bytes=bytes(&get(data,contents(),index as i32,TYMED(TYMED_ISTREAM.0|TYMED_HGLOBAL.0))?)?;
            total+=bytes.len();if total>TOTAL{return Err(invalid());}
            result.push(DropData::VirtualFile{name,bytes});
        }return Ok(result);
    }
    let png=registered(w!("PNG"));
    if offers(data,png,TYMED_HGLOBAL){return Ok(vec![DropData::VirtualFile{name:"image.png".into(),bytes:global(&get(data,png,-1,TYMED_HGLOBAL)?)?}]);}
    for id in [17,DIB] {if offers(data,id,TYMED_HGLOBAL){
        let mut bytes=global(&get(data,id,-1,TYMED_HGLOBAL)?)?;
        // The standard BGRA DIBV5 layout uses BI_BITFIELDS rather than BI_RGB.
        if id==17 && bytes.len()>=124 && bytes[14..16]==32u16.to_le_bytes() && bytes[16..20]==3u32.to_le_bytes() {
            let masks=[0x00ff0000u32,0x0000ff00,0x000000ff,0xff000000];
            if !(0..4).all(|i|bytes[40+i*4..44+i*4]==masks[i].to_le_bytes()){return Err(invalid());}
            bytes[16..20].copy_from_slice(&0u32.to_le_bytes());
        }
        let (rgba,width,height)=crate::collect::dib_bytes_to_rgba(&bytes).ok_or_else(invalid)?;
        return Ok(vec![DropData::Image{rgba,width,height}]);
    }}
    if offers(data,2,TYMED_GDI){
        let medium=get(data,2,-1,TYMED_GDI)?;
        if medium.0.tymed!=TYMED_GDI.0 as u32{return Err(invalid());}
        let (rgba,width,height)=crate::collect::bitmap_to_rgba(unsafe{medium.0.u.hBitmap}).ok_or_else(invalid)?;
        return Ok(vec![DropData::Image{rgba,width,height}]);
    }
    for id in [TEXT,registered(CFSTR_INETURLW)] {
        if offers(data,id,TYMED_HGLOBAL){
            let text=unicode(&global(&get(data,id,-1,TYMED_HGLOBAL)?)?)?;
            if text.trim().is_empty(){return Err(invalid());}return Ok(vec![DropData::Text(text)]);
        }
    }
    Err(invalid())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::{mem::ManuallyDrop, sync::{Arc,atomic::{AtomicUsize,Ordering}}};
    #[implement(IDataObject)]
    struct Data {formats:Vec<(u16,i32,bool,Vec<u8>)>,reads:Arc<AtomicUsize>}
    #[allow(non_snake_case)]
    impl IDataObject_Impl for Data_Impl {
        fn GetData(&self,f:*const FORMATETC)->Result<STGMEDIUM>{unsafe{
            let f=f.as_ref().ok_or_else(invalid)?;
            let (_,_,stream,body)=self.formats.iter().find(|(id,index,stream,_)|*id==f.cfFormat&&*index==f.lindex&&f.tymed&(if *stream{TYMED_ISTREAM}else{TYMED_HGLOBAL}).0 as u32!=0).ok_or_else(invalid)?;
            self.reads.fetch_add(1,Ordering::Relaxed);
            let h=GlobalAlloc(GMEM_MOVEABLE,body.len().max(1))?;
            let ptr=GlobalLock(h);assert!(!ptr.is_null());
            std::ptr::copy_nonoverlapping(body.as_ptr(),ptr.cast(),body.len());let _=GlobalUnlock(h);
            let mut medium=STGMEDIUM::default();
            if *stream {
                let s=StructuredStorage::CreateStreamOnHGlobal(h,true)?;
                medium.tymed=TYMED_ISTREAM.0 as u32;medium.u.pstm=ManuallyDrop::new(Some(s));
            }else{medium.tymed=TYMED_HGLOBAL.0 as u32;medium.u.hGlobal=h;}
            Ok(medium)
        }}
        fn QueryGetData(&self,f:*const FORMATETC)->HRESULT{unsafe{
            if f.is_null(){return E_POINTER;}let f=&*f;
            if self.formats.iter().any(|(id,index,stream,_)|*id==f.cfFormat&&*index==f.lindex&&f.tymed&(if *stream{TYMED_ISTREAM}else{TYMED_HGLOBAL}).0 as u32!=0){S_OK}else{E_INVALIDARG}
        }}
        fn GetDataHere(&self,_:*const FORMATETC,_:*mut STGMEDIUM)->Result<()>{Err(invalid())}
        fn GetCanonicalFormatEtc(&self,_:*const FORMATETC,_:*mut FORMATETC)->HRESULT{E_NOTIMPL}
        fn SetData(&self,_:*const FORMATETC,_:*const STGMEDIUM,_:BOOL)->Result<()>{Err(invalid())}
        fn EnumFormatEtc(&self,_:u32)->Result<IEnumFORMATETC>{Err(invalid())}
        fn DAdvise(&self,_:*const FORMATETC,_:u32,_:Option<&IAdviseSink>)->Result<u32>{Err(invalid())}
        fn DUnadvise(&self,_:u32)->Result<()>{Err(invalid())}
        fn EnumDAdvise(&self)->Result<IEnumSTATDATA>{Err(invalid())}
    }
    fn data(formats:Vec<(u16,i32,bool,Vec<u8>)>)->(IDataObject,Arc<AtomicUsize>){
        let reads=Arc::new(AtomicUsize::new(0));(Data{formats,reads:reads.clone()}.into(),reads)
    }
    fn utf16(s:&str)->Vec<u8>{s.encode_utf16().chain([0]).flat_map(u16::to_le_bytes).collect()}
    fn descriptors(names:&[&str])->Vec<u8>{
        let mut bytes=(names.len()as u32).to_le_bytes().to_vec();
        for name in names {
            let mut descriptor=FILEDESCRIPTORW::default();let mut filename=[0u16;260];
            for (dst,src) in filename.iter_mut().zip(name.encode_utf16()){*dst=src;}
            descriptor.cFileName=filename;
            bytes.extend_from_slice(unsafe{std::slice::from_raw_parts((&descriptor as *const FILEDESCRIPTORW).cast::<u8>(),std::mem::size_of::<FILEDESCRIPTORW>())});
        }bytes
    }
    #[test]
    fn unicode_and_url_drops_do_not_materialize_on_hover(){
        for id in [TEXT,registered(CFSTR_INETURLW)]{
            let (data,reads)=data(vec![(id,-1,false,utf16("中文 😀 https://example.com"))]);
            assert!(supported(&data));assert_eq!(reads.load(Ordering::Relaxed),0);
            assert!(matches!(&read(&data).unwrap()[0],DropData::Text(s) if s=="中文 😀 https://example.com"));
        }
    }
    #[test]
    fn file_folder_and_multi_file_drop_paths_survive_unicode(){
        let mut body=vec![0u8;20];body[..4].copy_from_slice(&20u32.to_le_bytes());body[16..20].copy_from_slice(&1u32.to_le_bytes());
        body.extend(utf16("C:\\文件\\a.txt"));body.extend(utf16("C:\\folder"));body.extend([0,0]);
        let (data,_)=data(vec![(FILES,-1,false,body)]);
        let items=read(&data).unwrap();assert_eq!(items.len(),2);
        assert!(matches!(&items[0],DropData::File(p) if p==&PathBuf::from("C:\\文件\\a.txt")));
    }
    #[test]
    fn virtual_attachments_use_each_index_and_accept_streams_or_memory(){
        let (data,reads)=data(vec![(descriptor(),-1,false,descriptors(&["邮件.txt","image.png"])),(contents(),0,true,b"attachment".to_vec()),(contents(),1,false,b"png".to_vec()),(TEXT,-1,false,utf16("fallback URL"))]);
        assert!(supported(&data));assert_eq!(reads.load(Ordering::Relaxed),0);
        let items=read(&data).unwrap();assert_eq!(items.len(),2);
        assert!(matches!(&items[0],DropData::VirtualFile{name,bytes} if name=="邮件.txt"&&bytes==b"attachment"));
        assert!(matches!(&items[1],DropData::VirtualFile{name,bytes} if name=="image.png"&&bytes==b"png"));
    }
    #[test]
    fn missing_virtual_contents_fail_without_falling_back_to_url(){
        let (data,_)=data(vec![(descriptor(),-1,false,descriptors(&["file.txt"])),(TEXT,-1,false,utf16("fallback"))]);
        assert!(read(&data).is_err());
        assert!(names(&descriptors(&["../escape.txt"])).is_err());
        assert!(names(&[255,255,255,255]).is_err());
    }
    #[test]
    fn dib_drop_keeps_top_down_image_pixels(){
        let mut dib=vec![0u8;40];dib[..4].copy_from_slice(&40u32.to_le_bytes());dib[4..8].copy_from_slice(&1i32.to_le_bytes());dib[8..12].copy_from_slice(&(-1i32).to_le_bytes());dib[12..14].copy_from_slice(&1u16.to_le_bytes());dib[14..16].copy_from_slice(&32u16.to_le_bytes());dib.extend([30,20,10,255]);
        let (data,_)=data(vec![(DIB,-1,false,dib)]);
        assert!(matches!(&read(&data).unwrap()[0],DropData::Image{rgba,width:1,height:1} if rgba==&[10,20,30,255]));
    }

    #[test]
    fn png_drop_preserves_original_encoded_bytes(){
        let body=b"original encoded image bytes".to_vec();
        let (data,_)=data(vec![(registered(w!("PNG")),-1,false,body.clone()),(TEXT,-1,false,utf16("URL"))]);
        assert!(matches!(&read(&data).unwrap()[0],DropData::VirtualFile{name,bytes} if name=="image.png"&&bytes==&body));
    }
}
