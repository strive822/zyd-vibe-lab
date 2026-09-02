# -*- mode: python ; coding: utf-8 -*-
# 单文件 exe 打包规格（方案 A：前后端一体，免 Node 运行时）
# 运行：在 backend/ 下执行  .venv\Scripts\python.exe -m PyInstaller build_exe.spec --clean --noconfirm
from PyInstaller.utils.hooks import collect_all

# uvicorn / certifi(requests 的 CA 证书) / requests 的隐式导入与数据文件
uvicorn_datas, uvicorn_bins, uvicorn_hidden = collect_all("uvicorn")
certifi_datas, certifi_bins, certifi_hidden = collect_all("certifi")
requests_datas, requests_bins, requests_hidden = collect_all("requests")

a = Analysis(
    ["build_exe_entry.py"],
    pathex=[".", ".."],
    binaries=uvicorn_bins + certifi_bins + requests_bins,
    # 前端静态资源：源 ../frontend/out -> 打包内 out/（运行时在 sys._MEIPASS/out）
    datas=[("../frontend/out", "out")]
    + uvicorn_datas
    + certifi_datas
    + requests_datas,
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.loops.uvloop",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "uvicorn.server",
    ]
    + uvicorn_hidden
    + certifi_hidden
    + requests_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="DCA-Calculator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
