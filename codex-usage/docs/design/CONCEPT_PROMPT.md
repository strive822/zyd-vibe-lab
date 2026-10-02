# B+C融合静态图生成记录

日期：2026-09-27。使用内置 image_gen 编辑/融合两张已查看的参考图；只有一个融合方向，不重新生成三个候选。

生成时以 B「对照叶」负责轮廓、配色和窗口对照结构，以 C「时标」提供固定内部时间区的交互逻辑。原始候选图已按用户要求删除，仅保留当前 [融合稿](fusion.png)。以下保留实际生成提示和标题校正记录；尺寸是设计预算，静态图不能证明数字动画已经实现。

## 融合提示

```text
Use case: ui-mockup / precise fusion of two user-selected design references.
Reference image 1 is 对照叶: preserve its warm ivory asymmetric leaf silhouette, olive accents, fine typography, five action discs, and WINDOW-FIRST quota table (Codex and GLM are columns, 5h and 周 are rows).
Reference image 2 is 时标: take ONLY its fixed internal information slot behavior. On provider hover the contents of a reserved area change without adding a new panel or changing the body's dimensions. Do not take its blue palette, egg-shaped body or service-row table.

Create ONE refined fusion concept, in a static review board showing normal and hovered states of the same design. Name '对照叶 · 内部时区'. Fully opaque, uniform pale neutral #ecebe7 canvas, target1536×1024. Precise flat digital UI, clean thin outlines and minimal shadow, no 3D bevel, glass, glow, gradient, paper folds, no conventional rectangular central card. Modest top-left concept heading, not gigantic. Two same-size scenes side by side labelled '常态' and '悬浮 Codex'. The footer must say '静态设计 · 动效示意 · 示例数据'. Do not imply it is a working prototype.

CORE: one warm ivory curved leaf, left shoulder wide, right end gently tapered and rounded, not sharp. A slightly fuller leaf than reference1 to accommodate the internally reserved time slot. Intended fixed size236×208DIP; main drawing each body about472×416image pixels, both copies exactly the same dimensions and placement structure. Not a gigantic panel. Both TOP time slot and BOTTOM quota table are INSIDE the same continuous leaf, separated only by whitespace or one delicate line. No panel within panel, no separate time card. On hover the OUTER SHAPE NEVER GROWS. NO external tooltip below, NO connecting line to an outside card, NO extra extension in either state.

INTERNAL TOP SLOT roughly190DIP wide and64DIP tall, deliberately reserved in both states:
LEFT normal:
small 'Codex · 下次恢复'
a single clear three-unit countdown '1时30分00秒' in a confident readable size
small '03:40 · 更新 02:09'
RIGHT hovered:
small top line 'Codex · 恢复' and '更新 02:09'
two carefully aligned compact lines:
left '5h 03:40', right '1时30分00秒'
left '周 09/30 02:10', right '3天00时00分'
The numeric right columns align, units smaller than digits but readable. Fixed width digit slots prevent all horizontal jumping. Body copy target12DIP, detail countdown numerals14DIP, normal focus numerals18–20DIP. All date/countdown content fits inside the leaf without clipping. On the hovered state place a tiny olive pointer marker at the Codex TABLE COLUMN header below, with a short underline and that column's two percentages slightly accented. Do not select an action disc at the same time.

BOTTOM SUMMARY is IDENTICAL and STATIONARY in both states and follows reference1 WINDOW-FIRST organization:
header: empty row-label slot, 'Codex', 'GLM ½'
row: '5h', '68%', '71%'
row: '周', '42%', '58%'
under a delicate divider: 'DeepSeek ½' then amount '¥86.42' on one baseline where room permits.
All five summary values stay visible. Summary numbers16–18DIP, labels12–13DIP. Do not replace this table with the second reference's provider rows. Do not hide or shift any of the summaries. Do not add a DeepSeek percentage, reset time or progress bar. Warm ivory surface, near-black type, restrained olive accent. Tables are flat text on one shared surface, no inner cards.

Exactly FIVE small28DIP action discs outside the LEFT half-circle of each leaf, with real visible space from the leaf boundary: copy/pages, translation, ellipsis, bell, settings. Fine consistent monochrome glyphs, no emoji, no extra action ball.36DIP implied hit targets, no overlaps. Keep all positions fixed across normal and hovered states. These should be visibly smaller and quieter than the information center.

Under the two main scenes, a SMALL editorial animation-spec strip, separated from the product and clearly labelled '数字过渡示意'. It must NOT look like another application panel. Show two short transitions in plain clear type with a subtle arrow:
'10时00分00秒 → 9时59分59秒' with tiny caption '变化的位滑入 / 滑出'
'1天00时00分 → 23时59分59秒' with tiny caption '单位成组切换'
Use only exact complete before/after text, no duplicated ghost characters or unreadable motion blur. Do not claim static image is an actual animation. Enough whitespace so this strip doesn't compete with the two main states.

Bottom right optional very small40DIP half-ball against one thin screen edge, no microtext inside, caption '贴边收起'. Main caption near footer '目标中心 236 × 208 DIP · 悬浮尺寸不变'. The diagram size is a design budget, not a measured physical screenshot.

TIME RULES: Three units ALWAYS. At or above24hours show 天/时/分. Below24hours show 时/分/秒. First number not zero-padded, last two numbers two digits. Target fixed digit cells and stable unit positions; on10→9 the disappearing digit animates within its reserved space. At24h boundary, all three unit labels and corresponding values transition together, never mix old and new units. Time anchor for mockdata2026-09-27 02:10:00 Asia/Shanghai; Codex next03:40:00, weekly09/30 02:10:00; updated02:09. All values illustrative. Keep B's visual character and clear table; introduce C's INTERNAL content substitution only. This user explicitly rejected growth of an additional hover card, so that constraint is essential.
```

## 标题校正

```text
Edit only the editorial heading and subtitle of this static UI fusion review board. Change the large top-left title from '对照叶·内部时区' to the correct Chinese '对照叶 · 内置时间区'. Change the subtitle underneath to '悬浮切换平台详情，主体尺寸保持不变'. The phrase 时区 incorrectly implies timezone; this is a fixed internal time-information area. Preserve EVERYTHING ELSE exactly: both leaf-shaped widgets, all positions and sizes, warm palette, five action balls per widget, all correct quota values, exact three-unit countdowns, transition examples, captions, and the fully opaque neutral background. Do not modify data, render new UI, enlarge, crop, add an external detail block, or change shape. This is just a precise two-line typography correction.
```
