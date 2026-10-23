import argparse,hashlib,json,shutil,stat,tempfile,urllib.request,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
URL='https://github.com/Wunsch2048/codex-bailong-desktop-pet/releases/download/v0.9.3/bailong-desktop-pet-0.9.3-windows-x64.zip'
SHA256='d31a35f3c2b7214c408843853bd6f4d9e73f61935a49e22e06b64efec45b1915'

def active_files(manifest):
    import sys
    sys.path.insert(0,str(ROOT/'app'))
    from desktop_services import all_items
    from sustained_assets import seam_items
    return sorted({item.get('playbackFile') or item['file'] for item in all_items(manifest)+seam_items(manifest)})

def extract_assets(archive,destination):
    destination=Path(destination).resolve()
    if destination.exists() and any(p.suffix in ('.webp','.webm','.gif') for p in destination.rglob('*')):
        raise ValueError('Existing animations were preserved. Use a new project directory.')
    with zipfile.ZipFile(archive) as bundle:
        entries={}
        for info in bundle.infolist():
            p=PurePosixPath(info.orig_filename)
            if p.is_absolute() or '..' in p.parts or '\\' in info.orig_filename or ':' in info.orig_filename or stat.S_ISLNK(info.external_attr>>16):raise ValueError('Unsafe archive entry')
            marker='/outputs/白龙桌宠素材/'
            path='/'+info.filename
            if marker in path:
                relative=path.split(marker,1)[1]
                if relative.casefold() in {name.casefold() for name in entries}:raise ValueError('Duplicate asset path')
                entries[relative]=info
        if '素材清单.json' not in entries:raise ValueError('Official playback manifest not found')
        manifest=json.loads(bundle.read(entries['素材清单.json']))
        names=['素材清单.json',*active_files(manifest)]
        # Validate the full selected set before writing any file.
        for name in names:
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or name not in entries:raise ValueError('Missing or unsafe playback asset')
            if not (0<entries[name].file_size<256*1024*1024):raise ValueError('Invalid asset size')
            target=destination.joinpath(*p.parts)
            if not target.resolve().is_relative_to(destination):raise ValueError('Asset path escaped destination')
            if target.exists():raise ValueError('Existing asset file was preserved')
        for name in names:
            target=destination.joinpath(*PurePosixPath(name).parts)
            if not target.resolve().is_relative_to(destination):raise ValueError('Asset path escaped destination')
            target.parent.mkdir(parents=True,exist_ok=True)
            with bundle.open(entries[name]) as source,target.open('wb') as output:shutil.copyfileobj(source,output)
    return len(names)

def embedded_payload(installer,payload):
    from PyInstaller.archive.readers import CArchiveReader
    payload.write_bytes(CArchiveReader(str(installer)).extract('payload.zip'))

def extract_container(archive,destination):
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            path=PurePosixPath(info.orig_filename)
            if path.is_absolute() or '..' in path.parts or '\\' in info.orig_filename or ':' in info.orig_filename or stat.S_ISLNK(info.external_attr>>16):raise ValueError('Unsafe container entry')
        if any('/outputs/白龙桌宠素材/' in '/'+name for name in bundle.namelist()):
            return extract_assets(archive,destination)
        installers=[info for info in bundle.infolist() if not info.is_dir() and info.filename.lower().endswith('.exe')]
        if len(installers)!=1:raise ValueError('Expected one embedded official installer')
        # The official public ZIP wraps assets in a PyInstaller payload. Read it
        # strictly as data; never launch the installer or deploy its application.
        with tempfile.TemporaryDirectory(prefix='bailong-payload-') as temporary:
            installer=Path(temporary)/'installer.exe';payload=Path(temporary)/'payload.zip'
            with bundle.open(installers[0]) as source,installer.open('wb') as output:shutil.copyfileobj(source,output)
            embedded_payload(installer,payload)
            return extract_assets(payload,destination)

def main():
    p=argparse.ArgumentParser(description='Download verified official assets only; never execute its installer.')
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--download',action='store_true');g.add_argument('--archive',type=Path)
    args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='bailong-assets-') as tmp:
        archive=args.archive
        if args.download:
            archive=Path(tmp)/'upstream.zip'
            print('Downloading official v0.9.3 assets container (about 740 MB); installer will not run.')
            with urllib.request.urlopen(urllib.request.Request(URL,headers={'User-Agent':'BailongAssetSetup/1'}),timeout=60) as response,archive.open('wb') as out:shutil.copyfileobj(response,out)
        with archive.open('rb') as source:actual=hashlib.file_digest(source,'sha256').hexdigest()
        if actual!=SHA256:raise ValueError('SHA-256 mismatch; no assets were imported')
        print('Verified SHA-256; imported files:',extract_container(archive,ROOT/'outputs/白龙桌宠素材'))
if __name__=='__main__':main()
