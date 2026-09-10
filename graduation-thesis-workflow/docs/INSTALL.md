# 安装与平台差异

唯一源目录是 `skills/graduation-thesis/`，必须完整复制其中 references 与 scripts，不要只复制 SKILL.md。三端复用同一核心规则；不使用特定平台的工具名称、动态 shell frontmatter 或绝对个人路径。

## Codex

依 [官方技能说明](https://learn.chatgpt.com/docs/build-skills) 使用项目级 `.agents/skills/`。在实际论文工作目录下放置 `.agents/skills/graduation-thesis/`，或按你当前版本的技能设置安装本地包。重新打开项目/会话让技能被发现；输入 `$graduation-thesis` 或直接要求使用该技能。

不要把整个公共仓库复制为论文原稿目录；只安装技能文件夹。也可直接指示助手读取技能路径。

## Claude Code

依 [官方技能说明](https://code.claude.com/docs/en/skills)，项目级目录是 `.claude/skills/graduation-thesis/`，个人级可放 `~/.claude/skills/graduation-thesis/`。完整复制，重新进入会话，使用 `/graduation-thesis`，再指定论文项目路径。

## WorkBuddy

直接下载仓库 `packages/graduation-thesis-workbuddy.zip`，在技能界面使用“添加技能 → 上传技能”导入；维护者可运行 `python scripts/package.py --out packages` 重建，启用后在对话中要求使用 graduation-thesis。依据：[官方安装说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)、[包结构说明](https://open.workbuddy.cn/docs/skill)。

WorkBuddy 分发包附加中英文描述、版本和作者字段。未将 `.codebuddy` 等其他产品目录混同为 WorkBuddy 安装目录。不同版本界面可能变化，导入失败时参考当前官方说明；可暂用“读取本地 SKILL.md”方式验证文件工作流，不能据此声称原生导入已验证。

## 能力检查

能发现技能只是第一步。启动时记录文件读写、联网、Python、文档生成和渲染是否可用。脚本将项目目录作为参数，路径有空格时加引号。Windows 用实际能运行的 `python`，不要假设 `py` 已配置。

首次试运行先用演示目录；确认提问与证据检查行为再使用正式材料。没有学校模板的演示不应得到“已完成正式论文”。不要求用户为启动购买 API。学校订阅/账户权限由使用者自行配置。
