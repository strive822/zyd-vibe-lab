//! 六个收集通道：剪贴板文字/图片、手动输入、截图文件夹、资源管理器复制、拖入岛。
//!
//! 通道开关默认全开，随时生效；关闭通道不删除已有条目。
//! 同一次复制可能同时提供文件列表、位图与文字：只取最具体的一种。
//! 截图通道的提交确认不在扫描线程里做：入库方在暂存提交成功后才回settle，
//! 写失败不确认，扫描线程下一轮重收同一文件。
use std::collections::{BTreeMap, VecDeque};
use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};

pub(crate) const TEXT_CLIPBOARD: usize = 0;
pub(crate) const TEXT_MANUAL: usize = 1;
pub(crate) const IMAGE_CLIPBOARD: usize = 2;
pub(crate) const IMAGE_SCREENSHOT: usize = 3;
pub(crate) const FILE_CLIPBOARD: usize = 4;
pub(crate) const FILE_DROP: usize = 5;

pub(crate) const CHANNEL_LABELS: [&str; 6] = ["剪贴板文字", "手动输入", "剪贴板图片", "截图文件夹", "资源管理器复制", "拖入岛"];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum Format {
    Files,
    Image,
    Text,
}

/// 同一份剪贴板里多种格式并存时的取用顺序：文件列表 > 图像 > 文字。
pub(crate) fn pick_formats(has_files: bool, has_image: bool, has_text: bool) -> Option<Format> {
    if has_files {
        Some(Format::Files)
    } else if has_image {
        Some(Format::Image)
    } else if has_text {
        Some(Format::Text)
    } else {
        None
    }
}

/// 一次剪贴板读取到的内容。截图载荷携带来源文件路径：入库提交成功后才确认，
/// 写失败不确认、下一轮扫描自然重收（F12）。
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum Payload {
    Files(Vec<PathBuf>),
    Image { rgba: Vec<u8>, width: u32, height: u32, screenshot: bool, screenshot_path: Option<PathBuf> },
    Text(String),
}

pub(crate) fn channel_of(payload: &Payload) -> usize {
    match payload {
        Payload::Files(_) => FILE_CLIPBOARD,
        Payload::Image { screenshot: true, .. } => IMAGE_SCREENSHOT,
        Payload::Image { .. } => IMAGE_CLIPBOARD,
        Payload::Text(_) => TEXT_CLIPBOARD,
    }
}

/// 只从开着的入口收集；关闭通道时已有条目不受影响。
pub(crate) fn accepts(channels: &[bool; 6], payload: &Payload) -> bool {
    channels[channel_of(payload)]
}

fn queue() -> &'static Mutex<VecDeque<Payload>> {
    static QUEUE: OnceLock<Mutex<VecDeque<Payload>>> = OnceLock::new();
    QUEUE.get_or_init(|| Mutex::new(VecDeque::new()))
}

pub(crate) fn push(payload: Payload) {
    if let Ok(mut queue) = queue().lock() {
        queue.push_back(payload);
    }
}

pub(crate) fn drain() -> Vec<Payload> {
    queue().lock().map(|mut queue| queue.drain(..).collect()).unwrap_or_default()
}

static COPIED: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);
static REPAINT: OnceLock<eframe::egui::Context> = OnceLock::new();

/// 只传递成功读取的复制事件，不携带内容；与暂存通道开关和去重无关。
pub(crate) fn take_copy_notice() -> bool {
    COPIED.swap(false, std::sync::atomic::Ordering::AcqRel)
}

pub(crate) fn receive_clipboard(payload: Payload) {
    COPIED.store(true, std::sync::atomic::Ordering::Release);
    if let Some(ctx)=REPAINT.get() {ctx.request_repaint();}
    let own=match &payload {Payload::Text(text)=>is_self_copy(text),_=>{is_self_copy("");false}};
    if own { return; }
    push(payload);
}

fn self_copy() -> &'static Mutex<String> {
    static SELF: OnceLock<Mutex<String>> = OnceLock::new();
    SELF.get_or_init(|| Mutex::new(String::new()))
}

/// 岛内“复制”只执行复制，不让自身回写触发新收集。
pub fn note_self_copy(text: &str) {
    if let Ok(mut last) = self_copy().lock() {
        *last = text.trim_end_matches(['\r', '\n']).to_string();
    }
}

pub(crate) fn is_self_copy(text: &str) -> bool {
    let text = text.trim_end_matches(['\r', '\n']);
    // 标记只属于下一次读取；外部再次复制同文或切换格式不能继续被排除。
    self_copy().lock().map(|mut last| {let own=!last.is_empty() && last.as_str()==text;last.clear();own}).unwrap_or(false)
}

/// 截图目录里的文件快照：大小 + 修改时间。写了一半的文件下一次探测时大小会变，会再次触发。
pub(crate) fn snapshot(dir: &Path) -> BTreeMap<PathBuf, (u64, i64)> {
    let mut map = BTreeMap::new();
    let Ok(entries) = std::fs::read_dir(dir) else { return map };
    for entry in entries.flatten() {
        let path = entry.path();
        let Ok(meta) = entry.metadata() else { continue };
        if !meta.is_file() {
            continue;
        }
        let stamp = meta.modified().ok().and_then(|time| time.duration_since(std::time::UNIX_EPOCH).ok()).map(|span| span.as_millis() as i64).unwrap_or(0);
        map.insert(path, (meta.len(), stamp));
    }
    map
}

/// 新增或被替换的文件；只认截图的常见后缀。
pub(crate) fn changed(previous: &BTreeMap<PathBuf, (u64, i64)>, current: &BTreeMap<PathBuf, (u64, i64)>) -> Vec<PathBuf> {
    current.iter().filter(|(path, meta)| is_image(path) && previous.get(*path) != Some(*meta)).map(|(path, _)| path.clone()).collect()
}

fn is_image(path: &Path) -> bool {
    path.extension().and_then(|ext| ext.to_str()).map(|ext| matches!(ext.to_ascii_lowercase().as_str(), "png" | "jpg" | "jpeg" | "bmp" | "gif" | "webp")).unwrap_or(false)
}

#[cfg(windows)]
static CLIPBOARD_UPDATES: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);

#[cfg(windows)]
static CLIPBOARD_READING: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

#[cfg(windows)]
static CLIPBOARD_SEQUENCE: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);

#[cfg(any(windows,test))]
fn keep_reading(updates:&std::sync::atomic::AtomicUsize, reading:&std::sync::atomic::AtomicBool, observed:usize)->bool {
    use std::sync::atomic::Ordering::SeqCst;
    reading.store(false,SeqCst);
    updates.load(SeqCst)!=observed && !reading.swap(true,SeqCst)
}

/// 剪贴板是全局资源：同一时刻只允许一个线程 Open/Close，避免互相踩踏。
#[cfg(windows)]
fn clipboard_lock() -> &'static Mutex<()> {
    static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    LOCK.get_or_init(|| Mutex::new(()))
}

/// 消息窗口累计收到的 WM_CLIPBOARDUPDATE 次数（联调/回归用）。
#[cfg(windows)]
pub(crate) fn update_count() -> usize { CLIPBOARD_UPDATES.load(std::sync::atomic::Ordering::Relaxed) }

/// 启动两类监听（只启动一次）：剪贴板与截图文件夹。
pub(crate) fn start(ctx: &eframe::egui::Context) {
    let _=REPAINT.set(ctx.clone());
    static STARTED: OnceLock<()> = OnceLock::new();
    STARTED.get_or_init(|| {
        #[cfg(windows)]
        {
            spawn_clipboard();
            spawn_screenshots();
        }
    });
}

#[cfg(windows)]
fn spawn_clipboard() {
    use windows::Win32::System::DataExchange::AddClipboardFormatListener;
    use windows::Win32::UI::WindowsAndMessaging::{CreateWindowExW, DispatchMessageW, GetMessageW, RegisterClassW, TranslateMessage, DefWindowProcW, MSG, WINDOW_EX_STYLE, WINDOW_STYLE, WNDCLASSW};
    use windows::core::w;

    // 安全 extern "system" fn 可隐式转换为 WNDCLASSW.lpfnWndProc 需要的 unsafe 函数指针；
    // 内部唯一的 unsafe 调用（DefWindowProcW）包在显式块里，避免整段落在 unsafe 边界外。
    extern "system" fn wndproc(hwnd: windows::Win32::Foundation::HWND, msg: u32, wparam: windows::Win32::Foundation::WPARAM, lparam: windows::Win32::Foundation::LPARAM) -> windows::Win32::Foundation::LRESULT {
        use windows::Win32::Foundation::LRESULT;
        const WM_CLIPBOARDUPDATE: u32 = 0x031D;
        if msg == WM_CLIPBOARDUPDATE {
            CLIPBOARD_UPDATES.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
            if std::env::var("DAOZAI_DEBUG_COLLECT").is_ok() { eprintln!("[collect] clipboard update"); }
            // 同一次复制会连发数条更新：只保留一轮等待，读全格式后一次入库。
            if CLIPBOARD_READING.swap(true, std::sync::atomic::Ordering::SeqCst) {
                return LRESULT(0);
            }
            std::thread::spawn(|| loop {
                std::thread::sleep(std::time::Duration::from_millis(140));
                let observed=CLIPBOARD_UPDATES.load(std::sync::atomic::Ordering::SeqCst);
                match read_clipboard() {
                    Ok(Some((sequence,payload)))=>{
                        if sequence==0 || CLIPBOARD_SEQUENCE.swap(sequence,std::sync::atomic::Ordering::SeqCst)!=sequence {
                            receive_clipboard(payload);
                        }
                    },
                    Ok(None)=>{is_self_copy("");},
                    // 被其他程序占用只代表尚未读到，不代表没有复制；保留读取者等待释放。
                    Err(())=>continue,
                }
                // 清标志后复核：读取期间的新更新不能被丢掉；若消息线程已接手则由它续读。
                if !keep_reading(&CLIPBOARD_UPDATES,&CLIPBOARD_READING,observed) {break;}
            });
            return LRESULT(0);
        }
        // SAFETY：hwnd/msg/wparam/lparam 由 Windows 消息循环提供，只在该窗口过程的线程上调用。
        unsafe { DefWindowProcW(hwnd, msg, wparam, lparam) }
    }

    std::thread::spawn(|| unsafe {
        let module = windows::Win32::System::LibraryLoader::GetModuleHandleW(None).unwrap_or_default();
        let hinst = windows::Win32::Foundation::HINSTANCE(module.0);
        let class = WNDCLASSW { lpfnWndProc: Some(wndproc), hInstance: hinst, lpszClassName: w!("DaozaiClipboard"), ..Default::default() };
        let _ = RegisterClassW(&class);
        let hwnd = CreateWindowExW(WINDOW_EX_STYLE(0), w!("DaozaiClipboard"), w!(""), WINDOW_STYLE(0), 0, 0, 0, 0, None, None, hinst, None);
        let Ok(hwnd) = hwnd else {
            if std::env::var("DAOZAI_DEBUG_COLLECT").is_ok() { eprintln!("[collect] create window failed"); }
            return;
        };
        let registered = AddClipboardFormatListener(hwnd).is_ok();
        if std::env::var("DAOZAI_DEBUG_COLLECT").is_ok() { eprintln!("[collect] clipboard window ready={registered}"); }
        let mut msg = MSG::default();
        while GetMessageW(&mut msg, None, 0, 0).as_bool() {
            let _ = TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    });
}

#[cfg(windows)]
fn read_clipboard() -> Result<Option<(u32,Payload)>,()> {
    let _guard = clipboard_lock().lock().map_err(|_|())?;
    use windows::Win32::System::DataExchange::{CloseClipboard, GetClipboardSequenceNumber, IsClipboardFormatAvailable, OpenClipboard};
    use windows::Win32::System::Ole::{CF_BITMAP, CF_DIB, CF_HDROP, CF_UNICODETEXT};

    // 复制方进程退出、剪贴板正被写入时 OpenClipboard 会短暂失败，重试约 1 秒。
    for attempt in 0..20 {
        if unsafe { OpenClipboard(None) }.is_ok() {
            // 持有系统剪贴板锁后再选格式，避免连续复制改变格式时读到过期的格式判断。
            let has_files = unsafe { IsClipboardFormatAvailable(u32::from(CF_HDROP.0)) }.is_ok();
            let has_image = unsafe { IsClipboardFormatAvailable(u32::from(CF_DIB.0)) }.is_ok()
                || unsafe { IsClipboardFormatAvailable(u32::from(CF_BITMAP.0)) }.is_ok();
            let has_text = unsafe { IsClipboardFormatAvailable(u32::from(CF_UNICODETEXT.0)) }.is_ok();
            let payload = pick_formats(has_files,has_image,has_text).and_then(|format| {
                match format {
                    Format::Files => read_files(),
                    Format::Image => read_dib().or_else(|| read_bitmap()),
                    Format::Text => read_text(),
                }
            });
            let sequence=unsafe { GetClipboardSequenceNumber() };
            unsafe { let _ = CloseClipboard(); }
            if std::env::var("DAOZAI_DEBUG_COLLECT").is_ok() {
                eprintln!("[collect] read {:?}", payload.as_ref().map(|payload| match payload {
                    Payload::Text(text) => format!("text {}B", text.len()),
                    Payload::Image { width, height, .. } => format!("image {width}x{height}"),
                    Payload::Files(files) => format!("files {}", files.len()),
                }));
            }
            return Ok(payload.map(|payload|(sequence,payload)));
        }
        if std::env::var("DAOZAI_DEBUG_COLLECT").is_ok() && attempt == 19 {
            eprintln!("[collect] open clipboard failed after retries");
        }
        std::thread::sleep(std::time::Duration::from_millis(50));
    }
    Err(())
}

/// 所有 Win32 调用都已放进显式 unsafe 块，签名不需要 unsafe。
#[cfg(windows)]
fn read_text() -> Option<Payload> {
    use windows::Win32::Foundation::HGLOBAL;
    use windows::Win32::System::DataExchange::GetClipboardData;
    use windows::Win32::System::Memory::{GlobalLock, GlobalSize, GlobalUnlock};
    use windows::Win32::System::Ole::CF_UNICODETEXT;
    let handle = unsafe { GetClipboardData(u32::from(CF_UNICODETEXT.0)) }.ok()?;
    let hglobal = HGLOBAL(handle.0);
    let ptr = unsafe { GlobalLock(hglobal) } as *const u16;
    if ptr.is_null() {
        return None;
    }
    let len = unsafe { GlobalSize(hglobal) } / 2;
    // SAFETY：GlobalLock 成功后 ptr 指向缓冲区；GlobalSize 给出字节长度。
    let slice = unsafe { std::slice::from_raw_parts(ptr, len) };
    let end = slice.iter().position(|value| *value == 0).unwrap_or(len);
    let text = String::from_utf16_lossy(&slice[..end]);
    let _ = unsafe { GlobalUnlock(hglobal) };
    if text.is_empty() {
        None
    } else {
        Some(Payload::Text(text))
    }
}

/// 所有 Win32 调用都已放进显式 unsafe 块，签名不需要 unsafe。
#[cfg(windows)]
fn read_files() -> Option<Payload> {
    use windows::Win32::System::DataExchange::GetClipboardData;
    use windows::Win32::System::Ole::CF_HDROP;
    use windows::Win32::UI::Shell::{DragQueryFileW, HDROP};
    let handle = unsafe { GetClipboardData(u32::from(CF_HDROP.0)) }.ok()?;
    let drop = HDROP(handle.0);
    let count = unsafe { DragQueryFileW(drop, u32::MAX, None) };
    let mut files = Vec::new();
    for index in 0..count {
        let mut buffer = vec![0u16; 1024];
        let len = unsafe { DragQueryFileW(drop, index, Some(&mut buffer)) };
        if len > 0 {
            files.push(PathBuf::from(String::from_utf16_lossy(&buffer[..len as usize])));
        }
    }
    if files.is_empty() {
        None
    } else {
        Some(Payload::Files(files))
    }
}

/// 所有 Win32 调用都已放进显式 unsafe 块，签名不需要 unsafe。
#[cfg(windows)]
fn read_dib() -> Option<Payload> {
    use windows::Win32::Foundation::HGLOBAL;
    use windows::Win32::System::DataExchange::GetClipboardData;
    use windows::Win32::System::Memory::{GlobalLock, GlobalSize, GlobalUnlock};
    use windows::Win32::System::Ole::CF_DIB;
    let handle = unsafe { GetClipboardData(u32::from(CF_DIB.0)) }.ok()?;
    let hglobal = HGLOBAL(handle.0);
    let ptr = unsafe { GlobalLock(hglobal) } as *const u8;
    if ptr.is_null() {
        return None;
    }
    let size = unsafe { GlobalSize(hglobal) };
    let payload = dib_to_rgba(ptr, size);
    let _ = unsafe { GlobalUnlock(hglobal) };
    payload
}

/// CF_BITMAP 走 GetDIBits 取 BGRA 像素；剪贴板不给 alpha 时按不透明处理。
/// 所有 Win32 调用都已放进显式 unsafe 块，签名不需要 unsafe。
#[cfg(windows)]
fn read_bitmap() -> Option<Payload> {
    use windows::Win32::System::DataExchange::GetClipboardData;
    use windows::Win32::System::Ole::CF_BITMAP;
    let handle = unsafe { GetClipboardData(u32::from(CF_BITMAP.0)) }.ok()?;
    let (rgba,width,height)=bitmap_to_rgba(windows::Win32::Graphics::Gdi::HBITMAP(handle.0))?;
    Some(Payload::Image { rgba, width, height, screenshot: false, screenshot_path: None })
}

#[cfg(windows)]
pub(crate) fn bitmap_to_rgba(bitmap_handle:windows::Win32::Graphics::Gdi::HBITMAP)->Option<(Vec<u8>,u32,u32)> {
    use windows::Win32::Graphics::Gdi::{GetDIBits, GetDC, GetObjectW, ReleaseDC, BITMAP, BITMAPINFO, DIB_RGB_COLORS};
    let mut bitmap = BITMAP::default();
    if unsafe { GetObjectW(bitmap_handle, std::mem::size_of::<BITMAP>() as i32, Some(&mut bitmap as *mut _ as *mut core::ffi::c_void)) } == 0 {
        return None;
    }
    let width = bitmap.bmWidth.max(0) as u32;
    let height = bitmap.bmHeight.max(0) as u32;
    if width == 0 || height == 0 || u64::from(width)*u64::from(height)>32*1024*1024 {
        return None;
    }
    let dc = unsafe { GetDC(None) };
    if dc.is_invalid() {
        return None;
    }
    let mut info = BITMAPINFO::default();
    info.bmiHeader.biSize = std::mem::size_of::<windows::Win32::Graphics::Gdi::BITMAPINFOHEADER>() as u32;
    info.bmiHeader.biWidth = width as i32;
    info.bmiHeader.biHeight = -(height as i32);
    info.bmiHeader.biPlanes = 1;
    info.bmiHeader.biBitCount = 32;
    info.bmiHeader.biCompression = 0;
    let mut rgba = vec![0u8; (width * height * 4) as usize];
    let lines = unsafe { GetDIBits(dc, bitmap_handle, 0, height, Some(rgba.as_mut_ptr() as *mut core::ffi::c_void), &mut info, DIB_RGB_COLORS) };
    let _ = unsafe { ReleaseDC(None, dc) };
    if lines == 0 {
        return None;
    }
    for pixel in rgba.as_chunks_mut::<4>().0 {
        pixel.swap(0, 2);
        if pixel[3] == 0 {
            pixel[3] = 255;
        }
    }
    Some((rgba,width,height))
}

/// 解析 24/32 位 BI_RGB 的 DIB 字节（不含 14 字节文件头），返回 (rgba, 宽, 高)。
/// 负高度 = top-down：存储顺序就是从上到下；正高度 = bottom-up：行序倒着存。
/// 方向必须在取绝对值之前判定——先 abs 再判会永远当成 bottom-up，
/// 导致 top-down 截图被上下翻转（F11）。其他位深暂不支持，返回 None（宁可少收，不乱收）。
#[cfg_attr(not(windows), allow(dead_code))]
pub(crate) fn dib_bytes_to_rgba(bytes: &[u8]) -> Option<(Vec<u8>, u32, u32)> {
    if bytes.len() < 40 {
        return None;
    }
    let header = &bytes[..40];
    let header_size = u32::from_le_bytes(header[0..4].try_into().ok()?) as usize;
    let width = i32::from_le_bytes(header[4..8].try_into().ok()?);
    let height = i32::from_le_bytes(header[8..12].try_into().ok()?);
    let depth = u16::from_le_bytes(header[14..16].try_into().ok()?);
    let compression = u32::from_le_bytes(header[16..20].try_into().ok()?);
    if compression != 0 || width <= 0 || height == 0 || !matches!(depth, 24 | 32) {
        return None;
    }
    let bottom_up = height > 0;
    let width = width as u32;
    let height = height.unsigned_abs();
    if u64::from(width)*u64::from(height)>32*1024*1024 || header_size<40 {return None;}
    let stride = ((width * u32::from(depth)).div_ceil(32) * 4) as usize;
    let offset = header_size;
    let needed = offset + stride * height as usize;
    if bytes.len() < needed {
        return None;
    }
    let pixels = &bytes[offset..needed];
    let mut rgba = vec![0u8; (width * height * 4) as usize];
    for y in 0..height as usize {
        let row = if bottom_up { height as usize - 1 - y } else { y };
        for x in 0..width as usize {
            let source = row * stride + x * (depth as usize / 8);
            let alpha = if depth == 32 { pixels[source + 3] } else { 255 };
            let target = (y * width as usize + x) * 4;
            // pi-lens-ignore: redundant-unsafe-function
            rgba[target] = pixels[source + 2];
            rgba[target + 1] = pixels[source + 1];
            rgba[target + 2] = pixels[source];
            rgba[target + 3] = if alpha == 0 { 255 } else { alpha };
        }
    }
    Some((rgba, width, height))
}

/// 解析剪贴板 CF_DIB 全局内存块。安全边界在函数内部（显式 unsafe 块）。
#[cfg(windows)]
fn dib_to_rgba(ptr: *const u8, size: usize) -> Option<Payload> {
    // SAFETY：调用方保证 ptr 指向 GlobalLock 锁定的 size 字节可读内存。
    let bytes = unsafe { std::slice::from_raw_parts(ptr, size) };
    let (rgba, width, height) = dib_bytes_to_rgba(bytes)?;
    Some(Payload::Image { rgba, width, height, screenshot: false, screenshot_path: None })
}

/// 系统截图目录（支持已重定向的 FOLDERID_Screenshots）。
pub(crate) fn screenshot_dir() -> Option<PathBuf> {
    #[cfg(windows)]
    {
        use windows::Win32::UI::Shell::{FOLDERID_Screenshots, SHGetKnownFolderPath, KF_FLAG_DEFAULT};
        if let Ok(path) = unsafe { SHGetKnownFolderPath(&FOLDERID_Screenshots, KF_FLAG_DEFAULT, None) } {
            let text = unsafe { path.to_string() }.ok();
            unsafe { windows::Win32::System::Com::CoTaskMemFree(Some(path.0 as *const _)) };
            if let Some(text) = text {
                let dir = PathBuf::from(text);
                if dir.is_dir() {
                    return Some(dir);
                }
            }
        }
        if let Ok(profile) = std::env::var("USERPROFILE") {
            let dir = PathBuf::from(profile).join("Pictures").join("Screenshots");
            if dir.is_dir() {
                return Some(dir);
            }
        }
        None
    }
    #[cfg(not(windows))]
    {
        None
    }
}

/// 截图通道的提交确认交接：previous=已确认处理的文件快照，inflight=已入队待确认。
/// 入库提交成功（或通道关闭明确丢弃）才确认；写失败不确认，下一轮扫描自然重收（F12）。
#[derive(Default)]
pub(crate) struct ScreenshotHandoff {
    previous: BTreeMap<PathBuf, (u64, i64)>,
    inflight: BTreeMap<PathBuf, (u64, i64)>,
}

impl ScreenshotHandoff {
    /// 以目录当前内容作基线：启动时已有截图不追溯收集。
    #[cfg(windows)]
    fn baseline(&mut self, dir: &Path) {
        self.previous = snapshot(dir);
    }

    /// 扫描一轮：新文件解码入队并登记待确认；previous 只在 settle 确认后更新。
    #[cfg(windows)]
    fn scan(&mut self, dir: &Path) {
        let current = snapshot(dir);
        for path in changed(&self.previous, &current) {
            // 仍在写入或暂时不可读：不进任何快照，下一轮自动重试。
            let Ok(bytes) = std::fs::read(&path) else { continue };
            let Ok(image) = image::load_from_memory(&bytes) else { continue };
            let rgba = image.to_rgba8();
            push(Payload::Image { rgba: rgba.as_raw().clone(), width: rgba.width(), height: rgba.height(), screenshot: true, screenshot_path: Some(path.clone()) });
            if let Some(meta) = current.get(&path) {
                self.inflight.insert(path.clone(), *meta);
            }
        }
        self.previous.retain(|path, _| current.contains_key(path));
    }

    /// 入库方回报结果：成功才确认；失败时丢弃待确认标记，下一轮重收同一文件。
    fn settle(&mut self, path: &Path, processed: bool) {
        let Some(meta) = self.inflight.remove(path) else { return };
        if processed {
            self.previous.insert(path.to_path_buf(), meta);
        }
    }
}

fn screenshot_handoff() -> &'static Mutex<ScreenshotHandoff> {
    static HANDOFF: OnceLock<Mutex<ScreenshotHandoff>> = OnceLock::new();
    HANDOFF.get_or_init(|| Mutex::new(ScreenshotHandoff::default()))
}

/// 入库方（pump）在提交成功或明确丢弃后调用，把该截图标记为已处理。
pub(crate) fn settle_screenshot(path: &Path, processed: bool) {
    if let Ok(mut handoff) = screenshot_handoff().lock() {
        handoff.settle(path, processed);
    }
}

#[cfg(windows)]
fn spawn_screenshots() {
    std::thread::spawn(|| {
        {
            let Ok(mut handoff) = screenshot_handoff().lock() else { return };
            if let Some(dir) = screenshot_dir() { handoff.baseline(&dir); }
        }
        loop {
            std::thread::sleep(std::time::Duration::from_secs(10));
            let Some(dir) = screenshot_dir() else { continue };
            let Ok(mut handoff) = screenshot_handoff().lock() else { continue };
            handoff.scan(&dir);
        }
    });
}

/// 消息窗口累计收到的 WM_CLIPBOARDUPDATE 次数（联调/回归用）。
#[cfg(all(test, windows))]
pub(crate) fn clipboard_update_count_for_test() -> usize {
    update_count()
}

/// 真实剪贴板读取入口，仅供本机联调测试使用。
#[cfg(all(test, windows))]
pub(crate) fn read_clipboard_for_test() -> Option<Payload> {
    read_clipboard().ok().flatten().map(|(_,payload)|payload)
}

/// 系统截图目录是否可解析（重定向后也应拿到实际路径）。
#[cfg(all(test, windows))]
pub(crate) fn screenshot_dir_for_test() -> Option<PathBuf> {
    screenshot_dir()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn updates_during_a_read_schedule_another_read_without_waiting_for_a_new_event() {
        use std::sync::atomic::{AtomicBool,AtomicUsize,Ordering::SeqCst};
        let updates=AtomicUsize::new(4);let reading=AtomicBool::new(true);
        updates.fetch_add(1,SeqCst);
        assert!(keep_reading(&updates,&reading,4));
        assert!(reading.load(SeqCst),"读取过程中已发生的新更新必须有后续读取者");
        assert!(!keep_reading(&updates,&reading,5));
        assert!(!reading.load(SeqCst),"无新更新时释放，让下一次消息可唤醒读取");
    }

    fn mask_channels(mask: usize) -> [bool; 6] {
        let mut channels = [false; 6];
        for (index, channel) in channels.iter_mut().enumerate() {
            *channel = mask & (1 << index) != 0;
        }
        channels
    }


    #[cfg(windows)]
    fn powershell(script: &str) -> bool {
        std::process::Command::new("powershell")
            .args(["-NoProfile", "-STA", "-Command", script])
            .status()
            .map(|status| status.success())
            .unwrap_or(false)
    }

    #[cfg(windows)]
    fn wait_for_clipboard(predicate: impl Fn(Option<Payload>) -> bool) -> Option<Payload> {
        for _ in 0..20 {
            std::thread::sleep(std::time::Duration::from_millis(100));
            let payload = read_clipboard_for_test();
            if predicate(payload.clone()) {
                return payload;
            }
        }
        None
    }

    #[cfg(windows)]
    #[test]
    #[ignore = "需要真实剪贴板；运行中的岛仔实例可能占用，按需显式执行"]
    fn real_clipboard_text_is_read_and_restored() {
        let saved = std::process::Command::new("powershell")
            .args(["-NoProfile", "-Command", "Get-Clipboard -Raw"])
            .output()
            .ok()
            .map(|out| String::from_utf8_lossy(&out.stdout).to_string())
            .unwrap_or_default();
        let marker = format!("daozai-clip-{}", std::process::id());
        assert!(powershell(&format!("Set-Clipboard -Value '{marker}'")), "无法写入测试文本（剪贴板被占用？）");
        let payload = wait_for_clipboard(|payload| matches!(&payload, Some(Payload::Text(text)) if text.contains("daozai-clip-")));
        match payload {
            Some(Payload::Text(text)) => assert!(text.contains(&marker), "读到的文本应包含标记：{text}"),
            other => panic!("应读到文本，实际 {other:?}"),
        }
        // 还原用户原来的剪贴板内容。
        if !saved.trim().is_empty() {
            let escaped = saved.replace("'", "''");
            let _ = powershell(&format!("Set-Clipboard -Value '{escaped}'"));
        }
    }

    #[cfg(windows)]
    #[test]
    #[ignore = "需要真实剪贴板；运行中的岛仔实例可能占用，按需显式执行"]
    fn real_clipboard_file_list_is_read() {
        let dir = std::env::temp_dir().join(format!("daozai-clip-files-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).unwrap();
        let file = dir.join("剪贴板文件.txt");
        std::fs::write(&file, b"x").unwrap();
        assert!(powershell(&format!("Set-Clipboard -Path '{}'", file.display())), "无法写入文件列表");
        let payload = wait_for_clipboard(|payload| matches!(&payload, Some(Payload::Files(files)) if !files.is_empty()));
        match payload {
            Some(Payload::Files(files)) => assert!(files.iter().any(|path| path == &file), "文件列表应包含测试文件：{files:?}"),
            other => panic!("应读到文件列表，实际 {other:?}"),
        }
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[cfg(windows)]
    #[test]
    #[ignore = "需要真实剪贴板；运行中的岛仔实例可能占用，按需显式执行"]
    fn real_clipboard_bitmap_is_read() {
        let script = "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; $bmp = New-Object System.Drawing.Bitmap 6,5; $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::FromArgb(0,128,255)); [System.Windows.Forms.Clipboard]::SetImage($bmp)";
        assert!(powershell(script), "无法写入测试位图");
        let payload = wait_for_clipboard(|payload| matches!(&payload, Some(Payload::Image { .. })));
        match payload {
            Some(Payload::Image { width, height, screenshot, rgba, .. }) => {
                assert_eq!((width, height), (6, 5), "位图尺寸应一致");
                assert!(!screenshot, "剪贴板图片不是截图来源");
                assert_eq!(rgba.len(), 6 * 5 * 4);
            }
            other => panic!("应读到位图，实际 {other:?}"),
        }
    }

    #[cfg(windows)]
    #[test]
    #[ignore = "需要真实剪贴板；运行中的岛仔实例可能占用，按需显式执行"]
    fn message_window_receives_clipboard_updates() {
        start(&eframe::egui::Context::default());
        std::thread::sleep(std::time::Duration::from_millis(300));
        let before = clipboard_update_count_for_test();
        assert!(powershell(&format!("Set-Clipboard -Value 'msg-test-{}'", std::process::id())));
        for _ in 0..30 {
            std::thread::sleep(std::time::Duration::from_millis(100));
            if clipboard_update_count_for_test() > before {
                return;
            }
        }
        panic!("3 秒内没有收到 WM_CLIPBOARDUPDATE（收到 {} 次）", clipboard_update_count_for_test());
    }

    #[cfg(windows)]
    #[test]
    fn real_screenshot_folder_resolves() {
        let dir = screenshot_dir_for_test();
        assert!(dir.as_deref().is_some_and(std::path::Path::is_dir), "FOLDERID_Screenshots 应解析到真实目录：{dir:?}");
    }

    #[test]
    fn all_sixty_four_channel_combinations_gate_only_their_own_kind() {
        let payloads = [
            (Payload::Text("文字".into()), TEXT_CLIPBOARD),
            (Payload::Image { rgba: vec![0; 4], width: 1, height: 1, screenshot: false, screenshot_path: None }, IMAGE_CLIPBOARD),
            (Payload::Image { rgba: vec![0; 4], width: 1, height: 1, screenshot: true, screenshot_path: None }, IMAGE_SCREENSHOT),
            (Payload::Files(vec![PathBuf::from("a.txt")]), FILE_CLIPBOARD),
        ];
        for mask in 0..64usize {
            let channels = mask_channels(mask);
            for (payload, channel) in &payloads {
                assert_eq!(accepts(&channels, payload), mask & (1 << channel) != 0, "mask={mask:b} channel={channel}");
            }
        }
        assert!(!accepts(&[false; 6], &Payload::Text("被关掉的通道".into())));
        assert!(accepts(&[true; 6], &Payload::Files(vec![PathBuf::from("a")])));
    }

    #[test]
    fn multi_format_copy_prefers_the_most_specific_payload() {
        assert_eq!(pick_formats(true, true, true), Some(Format::Files));
        assert_eq!(pick_formats(false, true, true), Some(Format::Image));
        assert_eq!(pick_formats(false, false, true), Some(Format::Text));
        assert_eq!(pick_formats(false, false, false), None);
    }

    #[test]
    fn self_copy_is_not_collected_again() {
        note_self_copy("岛内复制的一段\n");
        assert!(is_self_copy("岛内复制的一段"));
        assert!(!is_self_copy("岛内复制的一段"),"自身复制标记只能消费一次，外部同文仍应收集");
        note_self_copy("岛内复制的一段");
        assert!(!is_self_copy("别的程序复制的一段"));
        assert!(!is_self_copy("岛内复制的一段"),"中间复制其他文本后，旧标记不得继续排除");
        note_self_copy("岛内复制的一段");
        is_self_copy("");
        assert!(!is_self_copy("岛内复制的一段"),"非支持格式覆盖剪贴板也应清除旧标记");
        note_self_copy("");
        assert!(!is_self_copy("任何内容"));
    }

    #[test]
    fn screenshot_retries_until_commit_is_confirmed() {
        let dir = std::env::temp_dir().join(format!("daozai-shot-commit-{}-{}", std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|span| span.as_nanos()).unwrap_or(0)));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).unwrap();
        let mut handoff = ScreenshotHandoff::default();
        handoff.baseline(&dir);
        let shot = dir.join("截图.png");
        image::DynamicImage::ImageRgba8(image::RgbaImage::from_raw(2, 2, vec![9u8; 16]).unwrap()).save(&shot).unwrap();
        drain();
        handoff.scan(&dir);
        let queued = drain();
        assert_eq!(queued.len(), 1, "新增截图应入队一次：{queued:?}");
        match &queued[0] {
            Payload::Image { screenshot: true, screenshot_path: Some(path), .. } => assert_eq!(path, &shot),
            other => panic!("截图载荷应携带来源路径：{other:?}"),
        }
        // 首次提交失败：不确认，下一轮必须重收同一个文件（无需改动原图）。
        handoff.settle(&shot, false);
        handoff.scan(&dir);
        assert_eq!(drain().len(), 1, "提交失败后未确认，下一轮扫描应重新收同一张截图");
        // 第二次提交成功：确认后不再重复收。
        handoff.settle(&shot, true);
        handoff.scan(&dir);
        assert!(drain().is_empty(), "提交成功后不得重复入库");
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn screenshot_scan_detects_new_and_replaced_files_only() {
        let dir = std::env::temp_dir().join(format!("daozai-shots-{}-{}", std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|span| span.as_nanos()).unwrap_or(0)));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).unwrap();
        let first = dir.join("截图 1.png");
        std::fs::write(&first, b"one").unwrap();
        std::fs::write(dir.join("说明.txt"), b"ignored").unwrap();
        let baseline = snapshot(&dir);
        assert!(changed(&baseline, &snapshot(&dir)).is_empty(), "已有截图作为基线，不追溯");
        let second = dir.join("截图 2.PNG");
        std::fs::write(&second, b"two").unwrap();
        let now = snapshot(&dir);
        let fresh = changed(&baseline, &now);
        assert_eq!(fresh, vec![second.clone()], "只收新增的图片文件");
        std::fs::write(&first, b"one-but-longer").unwrap();
        let replaced = changed(&now, &snapshot(&dir));
        assert_eq!(replaced, vec![first.clone()], "被替换的截图要重新收");
        std::fs::remove_file(&second).unwrap();
        assert!(changed(&snapshot(&dir), &snapshot(&dir)).is_empty());
        let _ = std::fs::remove_dir_all(&dir);
    }

    fn dib_header(width: i32, height: i32, depth: u16) -> Vec<u8> {
        // BITMAPINFOHEADER 完整 40 字节。
        let mut header = Vec::new();
        header.extend_from_slice(&40u32.to_le_bytes());
        header.extend_from_slice(&width.to_le_bytes());
        header.extend_from_slice(&height.to_le_bytes());
        header.extend_from_slice(&1u16.to_le_bytes());
        header.extend_from_slice(&depth.to_le_bytes());
        header.extend_from_slice(&0u32.to_le_bytes()); // BI_RGB
        header.extend_from_slice(&0u32.to_le_bytes()); // biSizeImage
        header.extend_from_slice(&0u32.to_le_bytes()); // biXPelsPerMeter
        header.extend_from_slice(&0u32.to_le_bytes()); // biYPelsPerMeter
        header.extend_from_slice(&0u32.to_le_bytes()); // biClrUsed
        header.extend_from_slice(&0u32.to_le_bytes()); // biClrImportant
        header
    }

    fn pixel_row(r: u8, g: u8, b: u8, width: usize, depth: u16) -> Vec<u8> {
        let mut row = Vec::new();
        for _ in 0..width {
            match depth {
                32 => row.extend_from_slice(&[b, g, r, 255]),
                _ => row.extend_from_slice(&[b, g, r]),
            }
        }
        let stride = ((width as u32 * u32::from(depth)).div_ceil(32) * 4) as usize;
        row.resize(stride, 0xAB); // 行尾 padding 用非零填充，验证不会混进像素
        row
    }

    fn top_pixel(bytes: &[u8], width: u32) -> [u8; 3] {
        let (rgba, decoded_width, _) = dib_bytes_to_rgba(bytes).expect("DIB 应解析成功");
        assert_eq!(decoded_width, width);
        [rgba[0], rgba[1], rgba[2]]
    }

    #[test]
    fn top_down_dib_keeps_its_row_order() {
        // 1×2 top-down（负高度）：存储第一行就是最上面一行。修复前先 abs 后判方向，
        // 永远当成 bottom-up，输出上蓝下红（上下翻转）。
        let mut dib = dib_header(1, -2, 32);
        dib.extend_from_slice(&pixel_row(255, 0, 0, 1, 32)); // 上：红
        dib.extend_from_slice(&pixel_row(0, 0, 255, 1, 32)); // 下：蓝
        assert_eq!(top_pixel(&dib, 1), [255, 0, 0], "top-down 第一行必须仍是顶行");
    }

    #[test]
    fn bottom_up_dib_still_flips_rows() {
        // 1×2 bottom-up（正高度）：存储第一行是最下面一行，解码后顶行应是第二行。
        let mut dib = dib_header(1, 2, 32);
        dib.extend_from_slice(&pixel_row(255, 0, 0, 1, 32)); // 底：红
        dib.extend_from_slice(&pixel_row(0, 0, 255, 1, 32)); // 顶：蓝
        assert_eq!(top_pixel(&dib, 1), [0, 0, 255]);
    }

    #[test]
    fn twenty_four_bit_odd_width_skips_row_padding() {
        // 3×2 24 位奇数宽：每行 9 字节像素 + 3 字节 padding，padding 不能渗进行首。
        let mut dib = dib_header(3, -2, 24);
        dib.extend_from_slice(&pixel_row(250, 10, 20, 3, 24));
        dib.extend_from_slice(&pixel_row(20, 200, 30, 3, 24));
        let (rgba, width, height) = dib_bytes_to_rgba(&dib).expect("DIB 应解析成功");
        assert_eq!((width, height), (3, 2));
        assert_eq!(&rgba[0..3], &[250, 10, 20], "顶行首像素");
        assert_eq!(&rgba[8..11], &[250, 10, 20], "顶行末像素不受 padding 影响");
        assert_eq!(&rgba[12..15], &[20, 200, 30], "次行首像素");
    }

    #[test]
    fn invalid_dibs_are_rejected() {
        assert!(dib_bytes_to_rgba(&[0u8; 39]).is_none(), "长度不足 40");
        let mut dib = dib_header(2, -1, 16);
        dib.extend_from_slice(&[0u8; 8]);
        assert!(dib_bytes_to_rgba(&dib).is_none(), "16 位深不支持");
        let mut dib = dib_header(2, 0, 32);
        dib.extend_from_slice(&[0u8; 8]);
        assert!(dib_bytes_to_rgba(&dib).is_none(), "高度为 0");
        let mut dib = dib_header(1, -1, 32);
        dib.extend_from_slice(&[0u8; 3]);
        assert!(dib_bytes_to_rgba(&dib).is_none(), "像素数据不完整");
    }
}
