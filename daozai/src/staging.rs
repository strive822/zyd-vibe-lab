//! 暂存站索引：`staging.json` + `staging\` 下的自有副本。
//!
//! 规则（方案 M2）：
//! - 文件条目只记录用户原路径，不复制；图片/文字把副本写进 `staging\`。
//! - 先写妥副本再提交索引；索引原子写入，失败时保留上一有效状态。
//! - `migrated` 标记区分“尚未迁移”和“有效的空索引”，清空后重启不会复活旧清单。
//! - 索引损坏时保留现场并报错，不覆盖。
//! - 只有位于 `staging\` 内的自有副本允许删除；越界路径与指向外部的链接一律拒绝。
use serde::{Deserialize, Serialize};
use std::fs;
use std::io;
use std::path::{Component, Path, PathBuf};

pub(crate) const STAGING_DIR: &str = "staging";
const INDEX_FILE: &str = "staging.json";
const LEGACY_FILE: &str = "shelf.txt";
const MAX_PREVIEW: usize = 240;

/// 进程内单调序号：同毫秒多次入库也能得到不同副本名。
static COPY_SEQ: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub(crate) enum Kind {
    Text,
    Image,
    File,
}

impl Kind {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Kind::Text => "文字",
            Kind::Image => "图片",
            Kind::File => "文件",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub(crate) struct Entry {
    pub id: String,
    pub kind: Kind,
    /// 文件条目是用户原路径；文字/图片是相对 `staging\` 的副本名。
    pub path: String,
    /// 收集来源，例如“剪贴板文本”“截图文件夹”。
    pub source: String,
    /// 副本字节数；文件条目恒为 0（不虚增占用）。
    pub bytes: u64,
    pub dims: Option<(u32, u32)>,
    pub preview: String,
    pub first_at: i64,
    pub last_at: i64,
}

#[derive(Clone, Default, Serialize, Deserialize)]
struct Index {
    /// 是否已经完成（或明确跳过）旧 `shelf.txt` 的迁移。
    #[serde(default)]
    migrated: bool,
    #[serde(default)]
    entries: Vec<Entry>,
}

pub(crate) struct Staging {
    root: PathBuf,
    index_path: PathBuf,
    index: Index,
}

/// 清空/删除时逐个副本的结果，便于界面提示并重试。
#[derive(Default, Debug)]
pub(crate) struct Cleanup {
    pub removed: usize,
    pub failed: Vec<String>,
}

impl Staging {
    pub(crate) fn load(root: &Path) -> io::Result<Self> {
        let index_path = root.join(INDEX_FILE);
        let index = match fs::read(&index_path) {
            Ok(raw) => serde_json::from_slice::<Index>(&raw)
                .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, format!("暂存索引损坏：{error}")))?,
            Err(error) if error.kind() == io::ErrorKind::NotFound => Index::default(),
            Err(error) => return Err(error),
        };
        // 上次删除事务在「索引提交成功、真删之前」中断会留下 .del- 文件：
        // 索引已不含它、占用也统计不到，这里在加载期清掉（F-1）。
        let staging_dir = root.join(STAGING_DIR);
        if let Ok(items) = fs::read_dir(&staging_dir) {
            for item in items.flatten() {
                let name = item.file_name();
                if name.to_string_lossy().contains(".del-") {
                    let _ = fs::remove_file(item.path());
                }
            }
        }
        Ok(Self { root: root.to_path_buf(), index_path, index })
    }

    pub(crate) fn entries(&self) -> &[Entry] {
        &self.index.entries
    }

    pub(crate) fn staging_dir(&self) -> PathBuf {
        self.root.join(STAGING_DIR)
    }

    /// 首次启动把 `shelf.txt` 的旧路径迁入一次；已迁移过则不再导入。
    /// 迁移后`migrated` 落盘，旧清单原样保留。
    pub(crate) fn migrate_legacy(&mut self) -> io::Result<usize> {
        if self.index.migrated {
            return Ok(0);
        }
        // 只有「旧清单不存在」能当空清单；编码/权限等读取错误必须保留未迁移状态，
        // 否则会把读失败当成空清单并标记已迁移，之后再也导不进来（F17）。
        let legacy = match fs::read_to_string(self.root.join(LEGACY_FILE)) {
            Ok(text) => text,
            Err(error) if error.kind() == io::ErrorKind::NotFound => String::new(),
            Err(error) => return Err(io::Error::new(error.kind(), format!("旧暂存清单读取失败：{error}"))),
        };
        let now = chrono::Utc::now().timestamp();
        let mut staged = self.index.clone();
        let mut added = 0;
        for line in legacy.lines() {
            let raw = line.trim();
            if raw.is_empty() {
                continue;
            }
            let path = PathBuf::from(raw);
            let key = path.display().to_string();
            if staged.entries.iter().any(|entry| entry.kind == Kind::File && entry.path == key) {
                continue;
            }
            staged.entries.push(Entry {
                id: id_for(Kind::File, &key),
                kind: Kind::File,
                path: key,
                source: "旧暂存清单".into(),
                bytes: 0,
                dims: None,
                preview: String::new(),
                first_at: now,
                last_at: now,
            });
            added += 1;
        }
        staged.migrated = true;
        self.commit(&staged)?;
        self.index = staged;
        Ok(added)
    }

    pub(crate) fn save(&self) -> io::Result<()> {
        self.commit(&self.index)
    }

    /// 把一份索引原子落盘。所有变更走「构造 staged 索引 → commit 成功才替换内存」：
    /// 提交失败时内存与磁盘都保持上一致状态，不存在等下一次无关保存时被悄悄带出的脏项（F07）。
    fn commit(&self, staged: &Index) -> io::Result<()> {
        let body = serde_json::to_vec_pretty(staged)
            .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))?;
        write_atomic(&self.index_path, &body)
    }

    /// `staging\` 下自有副本的实际占用；同一副本只算一次，外部原文件不计。
    pub(crate) fn occupancy(&self) -> u64 {
        let mut seen: Vec<PathBuf> = Vec::new();
        let mut total = 0;
        for entry in &self.index.entries {
            if entry.kind == Kind::File {
                continue;
            }
            let Some(path) = self.own_copy(entry) else { continue };
            if seen.contains(&path) {
                continue;
            }
            if let Ok(meta) = fs::metadata(&path) {
                total += meta.len();
                seen.push(path);
            }
        }
        total
    }

    /// 收集文字：全文一致才算同一条，命中则只更新最近时间。
    pub(crate) fn add_text(&mut self, text: &str, source: &str) -> io::Result<()> {
        self.add_text_at(text, source, chrono::Utc::now().timestamp_millis())
    }

    /// add_text 的可注入时钟版本（隔离测试固定时钟用）。
    fn add_text_at(&mut self, text: &str, source: &str, now_millis: i64) -> io::Result<()> {
        let body = text.trim_end_matches(['\r', '\n']);
        if body.trim().is_empty() {
            return Ok(());
        }
        let duplicate = self.index.entries.iter().position(|entry| entry.kind == Kind::Text && self.read_text(entry).is_some_and(|old| old == body));
        if let Some(index) = duplicate {
            let mut staged = self.index.clone();
            let entry = &mut staged.entries[index];
            entry.last_at = chrono::Utc::now().timestamp();
            if entry.source != source {
                entry.source = source.into();
            }
            self.commit(&staged)?;
            self.index = staged;
            return Ok(());
        }
        let name = self.unique_copy_name("text", "txt", now_millis);
        self.write_copy(&name, body.as_bytes())?;
        let now = chrono::Utc::now().timestamp();
        self.push(Entry {
            id: id_for(Kind::Text, &name),
            kind: Kind::Text,
            path: name,
            source: source.into(),
            bytes: body.len() as u64,
            dims: None,
            preview: preview(body),
            first_at: now,
            last_at: now,
        })
    }

    /// 收集图片：解码后的尺寸与像素完全一致才算同一条（不同 PNG 编码也能合并）。
    pub(crate) fn add_image(&mut self, rgba: &[u8], width: u32, height: u32, source: &str) -> io::Result<()> {
        self.add_image_at(rgba, width, height, source, chrono::Utc::now().timestamp_millis())
    }

    /// add_image 的可注入时钟版本（隔离测试固定时钟用）。
    fn add_image_at(&mut self, rgba: &[u8], width: u32, height: u32, source: &str, now_millis: i64) -> io::Result<()> {
        if width == 0 || height == 0 {
            return Ok(());
        }
        let candidates: Vec<(usize, PathBuf)> = self.index.entries.iter().enumerate()
            .filter(|(_, entry)| entry.kind == Kind::Image && entry.dims == Some((width, height)))
            .filter_map(|(index, entry)| self.own_copy(entry).map(|path| (index, path)))
            .collect();
        for (index, path) in candidates {
            if let Ok(decoded) = image::open(&path) {
                let decoded = decoded.to_rgba8();
                if decoded.width() == width && decoded.height() == height && decoded.as_raw() == rgba {
                    let mut staged = self.index.clone();
                    staged.entries[index].last_at = chrono::Utc::now().timestamp();
                    self.commit(&staged)?;
                    self.index = staged;
                    return Ok(());
                }
            }
        }
        let name = self.unique_copy_name("image", "png", now_millis);
        let mut png = Vec::new();
        image::DynamicImage::ImageRgba8(image::RgbaImage::from_raw(width, height, rgba.to_vec()).ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "图像数据尺寸不符"))?)
            .write_to(&mut io::Cursor::new(&mut png), image::ImageFormat::Png)
            .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))?;
        self.write_copy(&name, &png)?;
        let now = chrono::Utc::now().timestamp();
        self.push(Entry {
            id: id_for(Kind::Image, &name),
            kind: Kind::Image,
            path: name,
            source: source.into(),
            bytes: png.len() as u64,
            dims: Some((width, height)),
            preview: format!("{width} × {height}"),
            first_at: now,
            last_at: now,
        })
    }

    /// 收集文件：只记录路径，同一路径不重复入库。
    pub(crate) fn add_file(&mut self, path: &Path, source: &str) -> io::Result<()> {
        if !path.exists() {
            return Err(io::Error::new(io::ErrorKind::NotFound, "文件不存在"));
        }
        let key = path.display().to_string();
        let duplicate = self.index.entries.iter().position(|entry| entry.kind == Kind::File && entry.path == key);
        if let Some(index) = duplicate {
            let mut staged = self.index.clone();
            staged.entries[index].last_at = chrono::Utc::now().timestamp();
            self.commit(&staged)?;
            self.index = staged;
            return Ok(());
        }
        self.push(Entry {
            id: id_for(Kind::File, &key),
            kind: Kind::File,
            path: key,
            source: source.into(),
            bytes: 0,
            dims: None,
            preview: String::new(),
            first_at: chrono::Utc::now().timestamp(),
            last_at: chrono::Utc::now().timestamp(),
        })
    }

    /// 删除一条：外部文件只移除记录，自有副本才删实体；越界一律拒绝。
    /// 事务（F07）：先把副本改名为待删文件（同目录 rename 原子），提交去掉该条的索引
    /// 后才真正删除；任一步失败都回退，内存、磁盘与正文保持一致、条目可见可重试。
    pub(crate) fn remove(&mut self, id: &str) -> io::Result<()> {
        let Some(index) = self.index.entries.iter().position(|entry| entry.id == id) else { return Ok(()) };
        let entry = self.index.entries[index].clone();
        let pending = match self.own_copy(&entry).filter(|path| path.exists()) {
            Some(path) => {
                let pending = pending_delete_name(&path);
                fs::rename(&path, &pending).map(|()| Some((path, pending)))?
            }
            None => None,
        };
        let mut staged = self.index.clone();
        staged.entries.remove(index);
        if let Err(error) = self.commit(&staged) {
            if let Some((path, pending)) = &pending {
                let _ = fs::rename(pending, path);
            }
            return Err(error);
        }
        self.index = staged;
        if let Some((path, pending)) = &pending {
            if let Err(error) = fs::remove_file(pending) {
                // 真删失败：整体回滚，条目仍计占用，释放后可重试。
                let mut restored = self.index.clone();
                restored.entries.insert(index, entry);
                if self.commit(&restored).is_ok() {
                    self.index = restored;
                }
                let _ = fs::rename(pending, path);
                return Err(error);
            }
        }
        Ok(())
    }

    /// 清空：删除全部自有副本，保留外部原文件；返回逐项失败原因。
    /// 事务（F08）：副本先改名待删，提交幸存者索引后才逐个真删；
    /// 删不掉的条目回填索引、继续计占用，释放占用后重试即可删净。
    pub(crate) fn clear(&mut self) -> io::Result<Cleanup> {
        let mut cleanup = Cleanup::default();
        let mut staged = self.index.clone();
        let mut survivors: Vec<Entry> = Vec::with_capacity(staged.entries.len());
        let mut pending: Vec<(usize, Entry, PathBuf, PathBuf)> = Vec::new();
        for (position, entry) in std::mem::take(&mut staged.entries).into_iter().enumerate() {
            if entry.kind == Kind::File {
                cleanup.removed += 1;
                continue;
            }
            match self.own_copy(&entry) {
                Some(path) => {
                    let target = pending_delete_name(&path);
                    match fs::rename(&path, &target) {
                        Ok(()) => pending.push((position, entry, path, target)),
                        Err(error) => {
                            cleanup.failed.push(format!("{}：{error}", entry.path));
                            survivors.push(entry);
                        }
                    }
                }
                None => cleanup.failed.push(format!("{}：不在暂存目录内，未删除", entry.path)),
            }
        }
        staged.entries = survivors;
        if let Err(error) = self.commit(&staged) {
            // 提交失败：待删文件全部挪回原名，内存保持原状。
            for (_, _, path, target) in &pending {
                let _ = fs::rename(target, path);
            }
            return Err(error);
        }
        self.index = staged;
        // 真删；删不掉的条目按原位置回填索引，保持可见与占用。
        let mut purge_failed: Vec<(usize, Entry)> = Vec::new();
        for (position, entry, path, target) in pending {
            match fs::remove_file(&target) {
                Ok(()) => cleanup.removed += 1,
                Err(error) if error.kind() == io::ErrorKind::NotFound => cleanup.removed += 1,
                Err(error) => {
                    let _ = fs::rename(&target, &path);
                    cleanup.failed.push(format!("{}：{error}", entry.path));
                    purge_failed.push((position, entry));
                }
            }
        }
        if !purge_failed.is_empty() {
            let mut merged: Vec<(usize, Entry)> = self.index.entries.iter().cloned().enumerate().collect();
            merged.extend(purge_failed);
            merged.sort_by_key(|(position, _)| *position);
            let mut restored = self.index.clone();
            restored.entries = merged.into_iter().map(|(_, entry)| entry).collect();
            if self.commit(&restored).is_ok() {
                self.index = restored;
            }
        }
        Ok(cleanup)
    }

    /// 仅供 UI 测试：直接登记若干文件条目（不校验存在性）。
    #[cfg(test)]
    pub(crate) fn seed_files(&mut self, paths: &[PathBuf]) {
        let now = chrono::Utc::now().timestamp();
        for path in paths {
            let key = path.display().to_string();
            if self.index.entries.iter().any(|entry| entry.kind == Kind::File && entry.path == key) {
                continue;
            }
            self.index.entries.push(Entry {
                id: id_for(Kind::File, &key),
                kind: Kind::File,
                path: key,
                source: "测试".into(),
                bytes: 0,
                dims: None,
                preview: String::new(),
                first_at: now,
                last_at: now,
            });
        }
        let _ = self.save();
    }

    fn push(&mut self, entry: Entry) -> io::Result<()> {
        let mut staged = self.index.clone();
        // 提交失败时撤掉刚写的副本（外部文件条目没有副本）。
        let copy = (entry.kind != Kind::File).then(|| self.staging_dir().join(&entry.path));
        staged.entries.push(entry);
        if let Err(error) = self.commit(&staged) {
            if let Some(copy) = copy {
                let _ = fs::remove_file(copy);
            }
            return Err(error);
        }
        self.index = staged;
        Ok(())
    }

    /// 唯一副本名：毫秒时间戳 + 进程内序号，并跳过已存在的同名文件。
    /// 同毫秒与时钟回退都不能靠可覆盖写入含沙射影地保证唯一（F09）——
    /// id 从文件名哈希而来，覆盖同名副本会让两条记录指向同一份内容。
    fn unique_copy_name(&self, prefix: &str, extension: &str, now_millis: i64) -> String {
        let staging_dir = self.staging_dir();
        let mut seq = COPY_SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        loop {
            let name = format!("{prefix}-{now_millis}-{seq}.{extension}");
            if !staging_dir.join(&name).exists() {
                return name;
            }
            seq += 1;
        }
    }

    fn write_copy(&self, name: &str, body: &[u8]) -> io::Result<()> {
        let dir = self.staging_dir();
        fs::create_dir_all(&dir)?;
        let path = dir.join(name);
        // 副本先落盘，索引随后提交。
        write_atomic(&path, body)
    }

    /// 自有副本的绝对路径（图片/文字）；外部文件条目返回 None。
    pub(crate) fn copy_path(&self, entry: &Entry) -> Option<PathBuf> {
        self.own_copy(entry)
    }

    pub(crate) fn text_of(&self, entry: &Entry) -> Option<String> {
        self.read_text(entry)
    }

    fn read_text(&self, entry: &Entry) -> Option<String> {
        let path = self.own_copy(entry)?;
        fs::read_to_string(path).ok()
    }

    /// 只认 `staging\` 下真实存在的自有副本；目录穿越、junction 指向外部都返回 None。
    fn own_copy(&self, entry: &Entry) -> Option<PathBuf> {
        let rel = Path::new(&entry.path);
        if entry.kind == Kind::File || rel.is_absolute() || rel.components().any(|part| !matches!(part, Component::Normal(_))) {
            return None;
        }
        let dir = fs::canonicalize(self.staging_dir()).ok()?;
        let path = fs::canonicalize(dir.join(rel)).ok()?;
        path.starts_with(&dir).then_some(path)
    }
}

fn preview(text: &str) -> String {
    let mut out = String::new();
    for line in text.lines().take(3) {
        if !out.is_empty() {
            out.push('\n');
        }
        out.push_str(line);
        if out.chars().count() >= MAX_PREVIEW {
            break;
        }
    }
    out.chars().take(MAX_PREVIEW).collect()
}

fn id_for(kind: Kind, key: &str) -> String {
    format!("{:?}-{}", kind, fnv64(key.as_bytes()))
}

/// 删除事务的待删名：同目录、带序号，不会与任何索引路径重合；占用/占用释放前始终可回退。
fn pending_delete_name(path: &Path) -> PathBuf {
    let seq = COPY_SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let mut name = path.file_name().map(|name| name.to_os_string()).unwrap_or_default();
    name.push(format!(".del-{seq}"));
    path.with_file_name(name)
}

fn fnv64(bytes: &[u8]) -> u64 {
    let mut hash = 0xcbf2_9ce4_8422_2325u64;
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100_0000_01b3);
    }
    hash
}

fn write_atomic(path: &Path, body: &[u8]) -> io::Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let tmp = path.with_extension("tmp");
    fs::write(&tmp, body)?;
    fs::rename(&tmp, path).inspect_err(|_| {
        let _ = fs::remove_file(&tmp);
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering};

    static SEQ: AtomicUsize = AtomicUsize::new(0);

    fn scratch(tag: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!("daozai-staging-{}-{}-{tag}", std::process::id(), SEQ.fetch_add(1, Ordering::Relaxed)));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    fn load(dir: &Path) -> Staging {
        let mut staging = Staging::load(dir).unwrap();
        staging.migrate_legacy().unwrap();
        staging
    }

    /// staging 目录内的文件名清单（排序后），用于断言副本没多没少。
    fn staging_files(dir: &Path) -> Vec<String> {
        let mut names: Vec<String> = fs::read_dir(dir.join(STAGING_DIR))
            .into_iter()
            .flatten()
            .flatten()
            .filter_map(|entry| entry.file_name().into_string().ok())
            .collect();
        names.sort();
        names
    }

    /// 用同名目录堵住索引的原子写入临时文件（staging.json → staging.tmp），注入提交失败。
    fn block_index_commit(dir: &Path) {
        fs::create_dir_all(dir.join("staging.tmp")).unwrap();
    }

    #[test]
    fn failed_add_commit_keeps_memory_disk_and_copies_consistent() {
        let dir = scratch("txn-add");
        let mut staging = load(&dir);
        staging.add_text("第一条", "手动输入").unwrap();
        let disk_before = fs::read(dir.join(INDEX_FILE)).unwrap();
        let copies_before = staging_files(&dir);
        block_index_commit(&dir);
        assert!(staging.add_text("第二条", "手动输入").is_err(), "提交失败必须报错");
        assert_eq!(staging.entries().len(), 1, "提交失败不得改动内存索引");
        assert_eq!(fs::read(dir.join(INDEX_FILE)).unwrap(), disk_before, "提交失败不得改动磁盘索引");
        assert_eq!(staging_files(&dir), copies_before, "提交失败后刚写的副本要撤掉");
        // 重复入库同样不得悄悄改内存。
        let (before_last, before_source) = (staging.entries()[0].last_at, staging.entries()[0].source.clone());
        assert!(staging.add_text("第一条", "另一来源").is_err());
        assert_eq!(staging.entries().len(), 1);
        assert_eq!(staging.entries()[0].last_at, before_last, "重复入库提交失败时 last_at 不得变更");
        assert_eq!(staging.entries()[0].source, before_source, "source 也不得变更");
        // 解除阻塞后重试成功，重启不丢。
        fs::remove_dir(dir.join("staging.tmp")).unwrap();
        staging.add_text("第二条", "手动输入").unwrap();
        assert_eq!(staging.entries().len(), 2);
        assert_eq!(Staging::load(&dir).unwrap().entries().len(), 2, "重启后不丢已提交条目");
    }

    #[test]
    fn failed_remove_keeps_entry_copy_and_index_together() {
        let dir = scratch("txn-remove");
        let mut staging = load(&dir);
        staging.add_text("要删除的", "手动输入").unwrap();
        let id = staging.entries()[0].id.clone();
        let copy = staging.staging_dir().join(staging.entries()[0].path.clone());
        assert!(copy.exists());
        block_index_commit(&dir);
        assert!(staging.remove(&id).is_err(), "索引提交失败必须报错");
        assert_eq!(staging.entries().len(), 1, "条目必须保留在内存");
        assert!(copy.exists(), "副本必须原样保留");
        assert_eq!(Staging::load(&dir).unwrap().entries().len(), 1, "磁盘索引必须保留该条目");
        // 解除阻塞：完整走通删除，不留待删残件。
        fs::remove_dir(dir.join("staging.tmp")).unwrap();
        staging.remove(&id).unwrap();
        assert!(staging.entries().is_empty());
        assert!(!copy.exists(), "副本最终应删除");
        assert!(!staging_files(&dir).iter().any(|name| name.contains(".del-")), "不得残留 .del- 待删文件：{:?}", staging_files(&dir));
        assert!(Staging::load(&dir).unwrap().entries().is_empty());
    }

    #[test]
    fn legacy_shelf_migrates_once_including_missing_paths() {
        let dir = scratch("migrate");
        let external = dir.join("报告.docx");
        fs::write(&external, b"x").unwrap();
        let gone = dir.join("已经不存在的文件.txt");
        fs::write(dir.join("shelf.txt"), format!("{}\n{}\n", external.display(), gone.display())).unwrap();
        let staging = load(&dir);
        assert_eq!(staging.entries().len(), 2, "失效路径也要迁入");
        assert!(staging.entries().iter().all(|entry| entry.kind == Kind::File));
        assert!(external.exists() && dir.join("shelf.txt").exists(), "原文件与旧清单都不能删");
        let again = load(&dir);
        assert_eq!(again.entries().len(), 2, "已有索引不得重复导入");
    }

    #[test]
    fn cleared_index_stays_empty_after_restart() {
        let dir = scratch("clear");
        fs::write(dir.join("shelf.txt"), dir.join("a.txt").display().to_string()).unwrap();
        let mut staging = load(&dir);
        assert_eq!(staging.entries().len(), 1);
        staging.clear().unwrap();
        assert!(staging.entries().is_empty());
        let restarted = load(&dir);
        assert!(restarted.entries().is_empty(), "清空后重启不能复活旧清单");
    }

    #[test]
    fn corrupt_index_is_reported_and_kept_untouched() {
        let dir = scratch("corrupt");
        let body = b"{ not json";
        fs::write(dir.join(INDEX_FILE), body).unwrap();
        let error = Staging::load(&dir).err().expect("损坏索引必须报错");
        assert_eq!(error.kind(), io::ErrorKind::InvalidData);
        assert_eq!(fs::read(dir.join(INDEX_FILE)).unwrap(), body, "损坏现场不能被覆盖");
    }

    #[test]
    fn failed_write_keeps_the_previous_index() {
        let dir = scratch("writefail");
        let mut staging = load(&dir);
        staging.add_text("第一段", "手动输入").unwrap();
        let before = fs::read(dir.join(INDEX_FILE)).unwrap();
        let blocked = dir.join("blocked");
        fs::create_dir_all(&blocked).unwrap();
        let error = write_atomic(&blocked, b"new").err().expect("目标是目录时必须失败");
        assert!(matches!(error.kind(), io::ErrorKind::IsADirectory | io::ErrorKind::PermissionDenied | io::ErrorKind::Other | io::ErrorKind::AlreadyExists));
        assert_eq!(fs::read(dir.join(INDEX_FILE)).unwrap(), before, "写失败不能覆盖上一有效索引");
        let reloaded = Staging::load(&dir).unwrap();
        assert_eq!(reloaded.entries().len(), 1);
    }

    #[test]
    fn text_and_file_dedupe_by_full_content_or_path() {
        let dir = scratch("dedupe");
        let mut staging = load(&dir);
        staging.add_text("完整的一段文字", "剪贴板文本").unwrap();
        staging.add_text("完整的一段文字", "手动输入").unwrap();
        assert_eq!(staging.entries().len(), 1, "全文一致应合并");
        staging.add_text("完整的一段文", "剪贴板文本").unwrap();
        assert_eq!(staging.entries().len(), 2, "前缀相同但内容不同要保留两份");
        let file = dir.join("素材.pdf");
        fs::write(&file, b"pdf").unwrap();
        staging.add_file(&file, "拖入岛").unwrap();
        staging.add_file(&file, "资源管理器复制").unwrap();
        assert_eq!(staging.entries().iter().filter(|entry| entry.kind == Kind::File).count(), 1, "同一路径只入库一次");
    }

    #[test]
    fn images_dedupe_by_normalized_pixels_not_encoding() {
        let dir = scratch("image");
        let mut staging = load(&dir);
        let pixels = vec![255u8; 4 * 3 * 4];
        let (w, h) = (4u32, 3u32);
        staging.add_image(&pixels, w, h, "剪贴板图像").unwrap();
        // 同一像素、不同压缩参数重新编码，仍应合并。
        let name = staging.entries()[0].path.clone();
        let path = staging.staging_dir().join(&name);
        let image = image::open(&path).unwrap().to_rgba8();
        let mut other = Vec::new();
        image::DynamicImage::ImageRgba8(image).write_to(&mut io::Cursor::new(&mut other), image::ImageFormat::Png).unwrap();
        fs::write(&path, other).unwrap();
        staging.add_image(&pixels, w, h, "截图文件夹").unwrap();
        assert_eq!(staging.entries().len(), 1, "标准化像素一致应合并");
        let different = vec![0u8; 4 * 3 * 4];
        staging.add_image(&different, w, h, "剪贴板图像").unwrap();
        assert_eq!(staging.entries().len(), 2, "同尺寸不同内容必须分开");
    }

    #[test]
    fn occupancy_counts_only_own_copies_once() {
        let dir = scratch("usage");
        let mut staging = load(&dir);
        staging.add_text("一段文字", "手动输入").unwrap();
        staging.add_image(&vec![9u8; 2 * 2 * 4], 2, 2, "剪贴板图像").unwrap();
        let external = dir.join("big.bin");
        fs::write(&external, vec![0u8; 4096]).unwrap();
        staging.add_file(&external, "拖入岛").unwrap();
        let expected: u64 = staging.entries().iter().filter(|entry| entry.kind != Kind::File).map(|entry| fs::metadata(staging.staging_dir().join(&entry.path)).unwrap().len()).sum();
        assert_eq!(staging.occupancy(), expected, "大文件引用不能虚增占用");
        // 重启后重新核对
        let restarted = Staging::load(&dir).unwrap();
        assert_eq!(restarted.occupancy(), expected);
    }

    #[test]
    fn same_millisecond_copies_get_unique_names_and_keep_first_content() {
        let dir = scratch("same-millis");
        let mut staging = load(&dir);
        // 固定时钟：三次入库都在同一毫秒。修复前同名副本互相覆盖，三条记录同 id 同内容。
        staging.add_text_at("第一条内容", "剪贴板文本", 1000).unwrap();
        staging.add_text_at("第二条内容", "剪贴板文本", 1000).unwrap();
        staging.add_text_at("第三条内容", "剪贴板文本", 1000).unwrap();
        let entries = staging.entries();
        assert_eq!(entries.len(), 3);
        let mut ids: Vec<_> = entries.iter().map(|entry| entry.id.clone()).collect();
        ids.sort();
        ids.dedup();
        assert_eq!(ids.len(), 3, "同一固定时钟下 id 必须唯一：{:?}", ids);
        let mut paths: Vec<_> = entries.iter().map(|entry| entry.path.clone()).collect();
        paths.sort();
        paths.dedup();
        assert_eq!(paths.len(), 3, "同一固定时钟下副本名必须唯一：{:?}", paths);
        for (index, expected) in ["第一条内容", "第二条内容", "第三条内容"].iter().enumerate() {
            let text = staging.text_of(&entries[index]).unwrap();
            assert_eq!(text, *expected, "第 {} 条内容不能被覆盖", index + 1);
        }
    }

    #[test]
    fn same_millisecond_images_get_unique_copies() {
        let dir = scratch("same-millis-image");
        let mut staging = load(&dir);
        let (width, height) = (2u32, 2u32);
        let first = vec![255u8; 4 * 2 * 2];
        let second = vec![0u8; 4 * 2 * 2];
        staging.add_image_at(&first, width, height, "截图文件夹", 42).unwrap();
        staging.add_image_at(&second, width, height, "截图文件夹", 42).unwrap();
        assert_eq!(staging.entries().len(), 2, "同毫秒不同像素必须各存一条");
        let mut paths: Vec<_> = staging.entries().iter().map(|entry| entry.path.clone()).collect();
        paths.sort();
        paths.dedup();
        assert_eq!(paths.len(), 2, "同毫秒图片副本名必须唯一：{:?}", paths);
        // 第一条像素必须原样保留。
        let copy = staging.copy_path(&staging.entries()[0]).unwrap();
        let decoded = image::open(&copy).unwrap().to_rgba8();
        assert_eq!(decoded.as_raw(), &first, "第一张图不能被第二张覆盖");
    }

    #[test]
    fn unique_copy_names_never_overwrite_existing_files() {
        let dir = scratch("unique-name");
        let staging = load(&dir);
        std::fs::create_dir_all(staging.staging_dir()).unwrap();
        let first = staging.unique_copy_name("text", "txt", 500);
        std::fs::write(staging.staging_dir().join(&first), "占用".as_bytes()).unwrap();
        let second = staging.unique_copy_name("text", "txt", 500);
        assert_ne!(first, second, "已存在的副本名必须跳过，不能覆盖（含时钟回退场景）");
        assert_eq!(std::fs::read(staging.staging_dir().join(&first)).unwrap(), "占用".as_bytes());
    }

    #[cfg(windows)]
    #[test]
    fn clear_keeps_failed_entries_and_allows_retry() {
        use std::os::windows::fs::OpenOptionsExt;
        let dir = scratch("clear-partial");
        let mut staging = load(&dir);
        staging.add_text("正常副本", "手动输入").unwrap();
        staging.add_text("被占用的副本", "手动输入").unwrap();
        let external = dir.join("外部文件.txt");
        fs::write(&external, "keep".as_bytes()).unwrap();
        staging.add_file(&external, "拖入岛").unwrap();
        // 不共享 DELETE 的句柄（审计同款方法）：等价于被其他程序占用。
        let locked_entry = staging.entries().iter().find(|entry| entry.preview.contains("被占用")).unwrap().clone();
        let locked = staging.staging_dir().join(&locked_entry.path);
        let handle = fs::OpenOptions::new().read(true).share_mode(1).open(&locked).unwrap();
        let cleanup = staging.clear().unwrap();
        assert_eq!(cleanup.removed, 2, "外部文件条目与正常副本应移除：{cleanup:?}");
        assert_eq!(cleanup.failed.len(), 1, "被占用副本应报告失败：{cleanup:?}");
        assert!(external.exists(), "外部原文件不能动");
        assert_eq!(staging.entries().len(), 1, "失败条目保留在内存");
        assert_eq!(staging.entries()[0].id, locked_entry.id, "保留的必须是失败那条");
        assert!(staging.occupancy() > 0, "失败条目必须继续计占用");
        // 重启后失败项仍在。
        assert_eq!(Staging::load(&dir).unwrap().entries().len(), 1, "重启后失败条目仍在磁盘");
        // 解除占用后第二次删净，不留待删残件。
        drop(handle);
        let cleanup = staging.clear().unwrap();
        assert_eq!(cleanup.removed, 1);
        assert!(cleanup.failed.is_empty(), "第二次清空不应再有失败：{cleanup:?}");
        assert!(staging.entries().is_empty());
        assert!(!locked.exists(), "解除占用后副本应删净");
        assert!(Staging::load(&dir).unwrap().entries().is_empty());
        assert!(external.exists());
        assert!(!staging_files(&dir).iter().any(|name| name.contains(".del-")), "不得残留 .del- 待删文件：{:?}", staging_files(&dir));
    }

    #[test]
    fn junction_into_foreign_folder_is_refused() {
        let dir = scratch("junction");
        let foreign = dir.join("外部目录");
        fs::create_dir_all(&foreign).unwrap();
        let sample = foreign.join("样本.txt");
        fs::write(&sample, b"junction sample").unwrap();
        let staging_dir = dir.join(STAGING_DIR);
        fs::create_dir_all(&staging_dir).unwrap();
        let link = staging_dir.join("link");
        let status = std::process::Command::new("cmd")
            .args(["/c", "mklink", "/J", &link.display().to_string(), &foreign.display().to_string()])
            .output();
        let created = status.map(|out| out.status.success()).unwrap_or(false) && link.exists();
        if !created {
            eprintln!("跳过 junction 用例：本机无法创建目录联接");
            return;
        }
        let mut staging = Staging::load(&dir).unwrap();
        staging.migrate_legacy().unwrap();
        staging.add_text("占位", "手动输入").unwrap();
        let mut index = serde_json::from_slice::<Index>(&fs::read(dir.join(INDEX_FILE)).unwrap()).unwrap();
        index.entries[0].path = "link/样本.txt".into();
        fs::write(dir.join(INDEX_FILE), serde_json::to_vec(&index).unwrap()).unwrap();
        let mut staging = Staging::load(&dir).unwrap();
        let cleanup = staging.clear().unwrap();
        assert!(sample.exists(), "经 junction 指向外部的文件不能被删");
        assert_eq!(fs::read(&sample).unwrap(), b"junction sample");
        assert!(!cleanup.failed.is_empty(), "junction 逃逸应报告无法安全删除");
    }

    #[test]
    fn deletes_stay_inside_the_staging_folder() {
        let dir = scratch("escape");
        let staging_root = dir.join(STAGING_DIR);
        fs::create_dir_all(&staging_root).unwrap();
        let outside = dir.join("外部样本.txt");
        fs::write(&outside, b"keep me").unwrap();
        let mut staging = load(&dir);
        // 1) 正常自有副本可以删除
        staging.add_text("可删的文字", "手动输入").unwrap();
        let id = staging.entries()[0].id.clone();
        let copy = staging.staging_dir().join(staging.entries()[0].path.clone());
        staging.remove(&id).unwrap();
        assert!(!copy.exists(), "自有副本应被删除");
        // 2) 外部文件条目只移除记录
        staging.add_file(&outside, "拖入岛").unwrap();
        let id = staging.entries()[0].id.clone();
        staging.remove(&id).unwrap();
        assert!(outside.exists(), "外部原文件必须保留");
        // 3) 越界路径拒绝删除
        staging.add_text("越界样本", "手动输入").unwrap();
        let mut index = serde_json::from_slice::<Index>(&fs::read(dir.join(INDEX_FILE)).unwrap()).unwrap();
        index.entries[0].path = "..\\外部样本.txt".into();
        fs::write(dir.join(INDEX_FILE), serde_json::to_vec(&index).unwrap()).unwrap();
        let mut staging = Staging::load(&dir).unwrap();
        let cleanup = staging.clear().unwrap();
        assert!(outside.exists(), "越界路径不能删到目录外的文件");
        assert_eq!(fs::read(&outside).unwrap(), b"keep me");
        assert!(!cleanup.failed.is_empty(), "越界副本应报告无法安全删除");
    }
}
