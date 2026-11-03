# PicRope · 图绳安装入口（给 Agent）

这是 `zyd-vibe-lab` 里的 Windows 截图工具增强版。用户要求下载、安装或运行时，请完成实际操作并如实报告结果，不要把“文件已下载”“进程已启动”“界面已验证”混为一谈。

## 先确认环境

| 项目 | 要求 | 检查方式 |
| --- | --- | --- |
| 系统 | Windows 10 / 11 x64 | `[Environment]::OSVersion` |
| .NET Framework | 4.8 或更高 | `(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full').Release` ≥ 528040 |
| PowerShell | 7 优先（5.1 读取无 BOM 中文脚本会解析失败） | `pwsh --version` |
| WebView2 | 随包附带运行库，无需单独安装 | 见 `app/` 内 DLL |

## 获取完整文件

仓库：`https://github.com/strive822/zyd-vibe-lab`，项目目录 `PicRope`。

有 Git 时克隆到新目录；没有 Git 时用实际可用的下载工具取得
`https://github.com/strive822/zyd-vibe-lab/archive/refs/heads/main.zip`，解压后取 `PicRope/` 子目录。需要源码时不能只下载 README 或安装脚本。

也可以直接使用项目独立包（推荐，避免下载整仓库）：

```text
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/PicRope/delivery/PicRope.zip
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/PicRope/delivery/SHA256SUMS.txt
https://raw.githubusercontent.com/strive822/zyd-vibe-lab/main/PicRope/delivery/FILES.json
```

下载放到本次专用临时目录。解压前检查条目，拒绝绝对路径和 `..` 越界；校验 `SHA256SUMS.txt`，失败最多重试两次，不换未知来源。

## 安装（官方流程）

安装包结构：`app/`（程序与运行库）、`install.ps1`、`Install.cmd`。

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

`install.ps1` 会：复制 `app/*` 到 `%LocalAppData%\Programs\PicRope`，创建桌面 `PicRope.lnk`，写入卸载注册项 `HKCU\...\Uninstall\PicRope`，然后启动程序。

**已装过旧版时**：先退出托盘中的图绳（托盘右键退出，或运行程序加 `--quit`），再确认安装目录内的 `data\` 已备份，然后安装。程序自身数据目录固定为安装目录下的 `data\`，安装脚本不会覆盖它；如果旧版装在别处（例如桌面），需要手动把 `data\` 复制到新安装目录，否则历史截图与设置会丢失。

卸载：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "$env:LocalAppData\Programs\PicRope\uninstall.ps1"
```

## 额度面板配置（可选）

首次打开“更多 → 模型额度”会生成 `data\quotas.json` 模板：

```json
{
  "refreshMinutes": 5,
  "codex": { "enabled": true },
  "zhipu": { "enabled": true, "apiKey": "" },
  "deepseek": { "enabled": true, "apiKey": "" },
  "workbuddy": { "enabled": true }
}
```

- `codex` 读取本机 `~/.codex/auth.json` 的登录凭证，不需要填写 Key；本机无法访问 `chatgpt.com` 时该行会显示查询失败。
- `zhipu` 填智谱开放平台（bigmodel.cn）的 API Key，接口为 `open.bigmodel.cn/api/monitor/usage/quota/limit`，Key 无套餐或失效时面板会提示。
- `deepseek` 填 DeepSeek 开放平台的 API Key，接口为 `api.deepseek.com/user/balance`。
- `workbuddy` 目前没有公开查询接口，面板只说明并给出打开应用的入口。
- 密钥只写在 `data\quotas.json`，不要提交到仓库、不要贴进聊天记录。

## 完成标准

报告里逐项说明：实际保存或安装路径、.NET 环境检查结果、数据迁移是否发生、程序是否真的启动（进程与界面）、额度面板里哪几家返回了真实数据、哪几家失败及原因。权限提示、登录动作仍需用户本人处理。
