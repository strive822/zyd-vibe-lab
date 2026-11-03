# PicRope · 图绳安装入口（给 Agent）

这是 `zyd-vibe-lab` 里的 Windows 截图工具增强版。用户要求下载、安装或运行时，请完成实际操作并如实报告结果，不要把“文件已下载”“进程已启动”“界面已验证”混为一谈。

## 先确认环境

| 项目 | 要求 | 检查方式 |
| --- | --- | --- |
| 系统 | Windows 10 / 11 x64 | `[Environment]::OSVersion` |
| .NET Framework | 4.8 或更高 | `(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full').Release` ≥ 528040 |
| PowerShell | 7 优先（5.1 读取无 BOM 中文脚本会解析失败） | `pwsh --version` |
| WebView2 运行库 | 安装包内已附带，无需单独安装 | 见安装包 `app/` 内 DLL |

## 两种安装方式

仓库里的 `delivery/` 有两个包，用途不同，不要混用：

| 文件 | 内容 | 用途 |
| --- | --- | --- |
| `delivery/PicRope-installer.zip` | `app/`（程序与运行库）+ `install.ps1` + `Install.cmd` | **直接安装**，免编译 |
| `delivery/PicRope.zip` | 源码快照（`src/`、`vendor/`、`tests/`、`packaging/`、`build.ps1`…） | 自己构建或改代码 |

### 方式 A：用安装包直接安装（推荐）

```text
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/PicRope/delivery/PicRope-installer.zip
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/PicRope/delivery/INSTALLER-SHA256.txt
```

下载到一个专用临时目录，校验 SHA-256（`INSTALLER-SHA256.txt` 里是安装包的值，当前为 `8901682c5e952128b42bc9a120a7b75d4071f70455d8c12288857ae74e79977b`），失败最多重试两次，不换未知来源。

解压后用 PowerShell 7 运行：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

`install.ps1` 会：复制 `app/*` 到 `%LocalAppData%\Programs\PicRope`，创建桌面 `PicRope.lnk`，写入卸载注册项 `HKCU\...\Uninstall\PicRope`，然后启动程序。

**已装过旧版时**：先退出托盘里的图绳（托盘右键退出，或运行 `PicRope.exe --quit`），确认旧安装目录内 `data\` 已备份，再安装。安装脚本不会覆盖安装目录下的 `data\`；如果旧版装在别处（例如桌面），需手动把 `data\` 复制到新安装目录，否则历史截图与设置会丢失。

### 方式 B：从源码构建

```powershell
git clone https://github.com/strive822/zyd-vibe-lab.git
cd zyd-vibe-lab/PicRope
pwsh -NoProfile -ExecutionPolicy Bypass -File build.ps1 -BuildOnly   # 产出 build\PicRope.exe
pwsh -NoProfile -ExecutionPolicy Bypass -File package.ps1            # 产出 releases\PicRope-<版本>-windows-x64.zip
```

把 `releases\*.zip` 解压到临时目录，再按方式 A 的方法运行其中的 `install.ps1`。构建只需要 .NET Framework 自带的 `csc.exe`（`%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe`）与 PowerShell 7，不需要 Visual Studio 或 MSBuild。

## 卸载

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "$env:LocalAppData\Programs\PicRope\uninstall.ps1"
```

## 额度面板配置（可选）

首次打开“更多 → 模型额度”（或运行 `PicRope.exe --quota` 直接打开）会生成 `data\quotas.json` 模板：

```json
{
  "refreshMinutes": 5,
  "codex": { "enabled": true },
  "zhipu": { "enabled": true, "apiKey": "" },
  "deepseek": { "enabled": true, "apiKey": "" },
  "workbuddy": { "enabled": true }
}
```

- `codex` 读取本机 `~/.codex/auth.json` 的登录凭证（`access_token` 或 `tokens.access_token`），不需要填写 Key，查询 `chatgpt.com/backend-api/wham/usage` 得到 5 小时窗口与每周额度。本机无法访问该域名时这一行会显示查询失败，其余行不受影响。
- `zhipu` 填智谱开放平台（bigmodel.cn）的 API Key，接口为 `open.bigmodel.cn/api/monitor/usage/quota/limit`，Key 无套餐或失效时面板会提示。
- `deepseek` 填 DeepSeek 开放平台的 API Key，接口为 `api.deepseek.com/user/balance`，显示各币种可用余额。
- `workbuddy` 目前没有公开查询接口，面板只说明原因并给出打开应用的入口。
- 修改 `quotas.json` 后点面板里的“刷新”即可生效，不必重启；`refreshMinutes` 控制自动刷新间隔（1–1440 分钟）。
- 密钥只写在 `data\quotas.json`，不要提交到仓库、不要贴进聊天记录。

## 快捷键

托盘“更多 → 截图快捷键…”可分别设置统一截图、矩形截图、窗口截图、全屏截图四组组合键，不用的可以禁用，避免和系统或其他软件冲突。默认只有统一截图绑定了 `Ctrl+Alt+S`。

## 完成标准

报告里逐项说明：实际保存或安装路径、.NET 环境检查结果、数据迁移是否发生、程序是否真的启动（进程与界面）、额度面板里哪几家返回了真实数据、哪几家失败及原因。权限提示、登录动作仍需用户本人处理。
