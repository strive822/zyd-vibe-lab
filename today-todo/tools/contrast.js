'use strict';

/**
 * WCAG 对比度实测。不做估算，只算 sRGB 相对亮度比。
 * 用法：node tools/contrast.js
 * 任一「正文/控件文字」配对比值低于要求即退出码 1。
 */

const PAIRS = [
  { name: '正文 · 纸色底', fg: '#111111', bg: '#F2EFE6', min: 4.5 },
  { name: '正文 · 白卡片', fg: '#111111', bg: '#FFFFFF', min: 4.5 },
  { name: '按钮文字 · 黄底', fg: '#111111', bg: '#FFD426', min: 4.5 },
  { name: '保存按钮文字 · 黑底', fg: '#FFFFFF', bg: '#111111', min: 4.5 },
  { name: '删除图标 · 红底', fg: '#111111', bg: '#FF4D2E', min: 4.5 },
  { name: '说明文字 · 纸色底', fg: '#5B5649', bg: '#F2EFE6', min: 4.5 },
  { name: '说明文字 · 白卡片', fg: '#5B5649', bg: '#FFFFFF', min: 4.5 },
  { name: '已完成文字 · 白卡片', fg: '#5B5649', bg: '#FFFFFF', min: 4.5 },
  { name: '占位符 · 输入框白底', fg: '#736C5D', bg: '#FFFFFF', min: 4.5 },
  { name: '勾选对勾 · 黑底', fg: '#FFD426', bg: '#111111', min: 3, note: '非文字图形，3:1' },
  { name: '描边 · 纸色底', fg: '#111111', bg: '#F2EFE6', min: 3, note: '控件边界，3:1' },
  { name: '描边 · 黄底', fg: '#111111', bg: '#FFD426', min: 3, note: '控件边界，3:1' },
  { name: '描边 · 红底', fg: '#111111', bg: '#FF4D2E', min: 3, note: '控件边界，3:1' },
];

function channel(value) {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function luminance(hex) {
  const clean = hex.replace('#', '');
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

function ratio(a, b) {
  const la = luminance(a);
  const lb = luminance(b);
  const light = Math.max(la, lb);
  const dark = Math.min(la, lb);
  return (light + 0.05) / (dark + 0.05);
}

let failed = 0;

console.log('WCAG 对比度实测');
console.log('─'.repeat(58));
for (const pair of PAIRS) {
  const value = ratio(pair.fg, pair.bg);
  const pass = value >= pair.min;
  if (!pass) failed += 1;
  const flag = pass ? 'PASS' : 'FAIL';
  const note = pair.note ? `  (${pair.note})` : '';
  console.log(
    `${flag}  ${value.toFixed(2).padStart(5)}:1  ≥${pair.min}  ${pair.name}${note}`
  );
}
console.log('─'.repeat(58));
console.log(failed === 0 ? `全部通过（${PAIRS.length} 组）` : `${failed} 组未通过`);
process.exitCode = failed === 0 ? 0 : 1;
