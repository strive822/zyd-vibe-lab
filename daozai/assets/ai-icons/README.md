# 新增 AI 品牌图标来源

`zai.svg`（智谱 GLM／开放平台当前使用的斜线 Z 标识）、`deepseek.svg`、`workbuddy.svg` 来自 [Lobe Icons](https://github.com/lobehub/lobe-icons)，固定 commit：`ea434b96e75813517b377825e01c0df61dee8836`。

原文件路径均为 `packages/static-svg/icons/<文件名>`，原样保存；原许可证副本见 [lobe-icons-LICENSE.txt](lobe-icons-LICENSE.txt)（MIT，Copyright (c) 2023 LobeHub）。

使用理由：替代难识别的 G/D/W 字母，同时沿用项目已有的 SVG 加载和白色覆盖率绘制方式，不增加运行时依赖。升级或替换时核对来源、许可及小尺寸识别度。品牌标识的商标权仍归相应权利人；MIT 不代表服务商背书或认证。

本说明仅覆盖上述三个新增文件，不改变既有 Codex/Grok 图标的来源声明。

2026-11-05：对照 [智谱开放平台官网](https://bigmodel.cn/) 的 /static/images/favicon.png 与 [Z.ai](https://z.ai/) 的 https://z-cdn.chatglm.cn/z-ai/static/logo.svg 确认斜线 Z 图形。撤销此前误选的 Zhipu 点阵公司标识，采用上述同一固定 commit 的 packages/static-svg/icons/zai.svg，不增加依赖。
