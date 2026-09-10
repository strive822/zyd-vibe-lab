# 交付前自动 Humanizer 润色

这是默认必经阶段，在内容证据初审后、最终排版交付前运行。内置 [Humanizer 3.0.0](vendor/humanizer/SKILL.md)，无需用户另行下载、注册服务或给论文上传第三方网站。它由当前助手读取执行，不是一个独立的检测器。

先核对本项目学校 AI 规则。学校允许的范围内自动执行，不再逐章询问；若学校明确禁止此类改写，则保留原文并写明具体规则与来源，记录 skipped_school_policy，不悄悄绕过规定。

## 执行

1. 完成正文事实与引用初审。保存 `manuscript/before-humanizer.md`（或真实源稿格式）及哈希，不能覆盖唯一稿件。
2. 阅读内置原版 Humanizer，按文件/嵌入模式处理语言。其风格建议仅适用于普通叙述，不能移除学校强制的标题、引用样式，不能更改直接引语、术语、数值、单位、公式、文献标题或必要限定条件。其关于“AI 痕迹”的说法不作为检测结论或论文事实依据。
3. 中文论文保留中文学术习惯；不机械套用英文词表，不添加个人经历、受访者语气或故意语病来伪装作者。只减少空话、重复和不自然句式。没有需要修改的内容可以保持原文，并如实记录。
4. 将润色稿保存为独立源稿，逐项对比事实、引用、数字与结论强度。输出 `reviews/humanizer-review.md`：处理范围、工具版本、真实改动、受保护内容检查和遗留问题。
5. 更新 polishing.json：status=applied、before_path/before_sha256、after_path/after_sha256、review_path/review_sha256。不得在尚未执行时标 applied。
6. 对润色稿重新执行 06-review，再进行 07-delivery。最终导出的文档必须来源于核验过的润色稿；后续实质改写后重新核验，不沿用旧记录。

## 指标边界

“AI 检测分数”和“文字重复率”是不同指标。Humanizer 没有测量或保证任一分数的能力。不生成虚假检测报告，不写“已降到某百分比”。重复内容应通过原创分析、正确引用与必要重写处理，不能用换同义词掩盖抄袭；按学校要求保留 AI 使用披露。

## 许可与可追溯性

上游为 blader/humanizer，固定提交和文件 SHA256 见 [UPSTREAM.json](vendor/humanizer/UPSTREAM.json)，许可证为 [MIT](vendor/humanizer/LICENSE)，Copyright (c) 2025 Siqi Chen。上游内容原样保存，学术约束写在本模块，不伪造为原作者规则。安装和打包时必须保留许可与来源文件。

## 辅助比较与失败处理

前后稿必须是不同路径，保存 UTF-8 Markdown、文本或 LaTeX 源稿后运行：

```text
python <技能目录>/scripts/polish_check.py <润色前源稿> <润色后源稿> --out <项目目录>/reviews/polish-tokens-001.json
```

报告只比较常见数字、方括号/LaTeX 引用及部分公式标记，退出码 1 表示发现变化待核查，不是程序崩溃。它不能识别所有引用格式或判断语义；即使 no_token_changes，也须逐段检查单位、术语、归属、否定、因果、显著性、适用范围和结论强度。直接引语应逐字核对。二进制 Word/PDF 必须先用宿主能力提取并核对文本，不能直接输入本脚本。

把检查报告路径记入 polishing.json 的 token_check_path；语义审查结论写入 humanizer-review.md。任何事实漂移都先修复或恢复原稿，不得以“降 AI 率”为理由放行。报告文件不覆盖旧版本。
