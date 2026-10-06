#!/usr/bin/env node
/* XianForge.en.html 英文版自检（无浏览器）
 * ============================================================
 *  ★★ 本文件最重要的不是"英文版能不能跑"，而是这一条：
 *
 *     英文版导出的 stations.tsv，栏目/地区字段必须与中文版
 *     【逐字相同】。
 *
 *  为什么这是生死线：栏目名（新闻综合/交通台/音乐…）和地区名
 *  （北京/江苏/全国…）是【固件解析用的固定标识符】，不是显示文本。
 *  固件里是按中文字面量 strcmp 匹配的。
 *  ⇒ 一旦英文版把它们翻成 "News" / "Beijing"，
 *    导出的文件在真机上就会「导入成功但全部落到兜底分类」，
 *    而工具自检是绿的、界面也看不出来。
 *
 *  这就是铁律 41：判据本身可能被绕过，所以判据要跟【另一个
 *  已知正确的产物】比，而不是自己验自己。
 *
 * 跑法：
 *   node tools/_xf_en_selftest.js
 * ============================================================ */
'use strict';
const fs = require('fs');
const path = require('path');

// ---- 与中文版同一套 DOM 桩（英文版加载路径相同）----
function mkEl() {
  const cls = { add(){}, remove(){}, toggle(){}, contains(){ return false; } };
  return {
    value: '', textContent: '', innerHTML: '', checked: false,
    disabled: false, files: [], className: '', style: {},
    classList: cls, appendChild(){}, removeChild(){}, click(){},
    addEventListener(){}, removeEventListener(){}, setAttribute(){},
    getAttribute(){ return null; },
    querySelector(){ return null; }, querySelectorAll(){ return []; },
  };
}
global.document = {
  getElementById: mkEl, querySelector: mkEl, querySelectorAll: () => [],
  createElement: mkEl, createTextNode: () => ({}), body: mkEl(),
  addEventListener(){}, readyState: 'complete',
};
global.window = { addEventListener(){}, location: { href: '' } };
try {
  Object.defineProperty(globalThis, 'navigator',
    { value: { userAgent: 'node' }, writable: true, configurable: true });
} catch (e) { /* 忽略 */ }
global.localStorage = { getItem: () => null, setItem(){}, removeItem(){} };
global.alert = () => {};
global.FileReader = function () { this.readAsArrayBuffer = () => {}; };
global.Blob = function () {};
if (typeof global.URL.createObjectURL !== 'function') {
  global.URL.createObjectURL = () => 'blob:x';
}

function loadTool(file) {
  const html = fs.readFileSync(path.join(__dirname, file), 'utf8');
  const m = html.match(/<script[^>]*>([\s\S]*)<\/script>/);
  if (!m) { console.error('✗ ' + file + ' 里找不到 <script>'); process.exit(2); }
  const EXPORTS = ['S', 'CATS', 'PROVS', 'PROVS_CN', 'PROVS_XW',
                 'SPECIAL_PROV', 'parseInput', 'normalize', 'buildTsv',
                 'buildExample', 'guessCat', 'guessProv', 'viewConv',
                 'viewUse', 'viewDisc', 'viewAbout'];
  // eslint-disable-next-line no-new-func
  const X = new Function(m[1] + '\nreturn {' + EXPORTS.join(',') + '};')();
  X.S.rows = [];
  X.S.srcName = '';
  return X;
}

const EN = loadTool('XianForge.en.html');
const ZH = loadTool('XianForge.html');

let fails = 0;
function check(label, cond, detail) {
  if (cond) { console.log('  ✓ ' + label); }
  else { console.log('  ✗ ' + label + (detail ? ('   ' + detail) : '')); fails++; }
}

// ============================================================
console.log('=== 1. ★ 协议 token 必须与中文版逐字相同 ===');
check('13 个栏目名完全一致',
      JSON.stringify(EN.CATS) === JSON.stringify(ZH.CATS),
      '\n      EN: ' + JSON.stringify(EN.CATS) +
      '\n      ZH: ' + JSON.stringify(ZH.CATS));
check('43 个地区名（42 + 全国/其他）完全一致',
      JSON.stringify(EN.PROVS) === JSON.stringify(ZH.PROVS),
      '数量 EN=' + EN.PROVS.length + ' ZH=' + ZH.PROVS.length);
check('特殊地区标记（全国/其他 → 固件 255）一致',
      JSON.stringify(EN.SPECIAL_PROV) === JSON.stringify(ZH.SPECIAL_PROV),
      JSON.stringify(EN.SPECIAL_PROV));
check('城市匹配表一致（否则地区推断会变）',
      JSON.stringify(EN.PROVS_CN) === JSON.stringify(ZH.PROVS_CN) &&
      JSON.stringify(EN.PROVS_XW) === JSON.stringify(ZH.PROVS_XW));

// ============================================================
console.log('\n=== 2. ★ 同一份 M3U，两个版本导出的 TSV 必须一致 ===');
// ★ 这条是整份自检的核心。它不检查"英文版对不对"，
//   它检查"英文版有没有偷偷改动数据"。
//   注释头允许不同（文案是给人看的），数据行必须逐字相同。
const M3U = [
  '#EXTM3U',
  '#EXTINF:-1 tvg-id="r1" group-title="新闻",北京人民广播电台',
  'http://example.com/a/64k.mp3',
  '#EXTINF:-1,杭州交通经济广播',
  'http://example.com/b/64k.mp3',
  '#EXTINF:-1,深圳音乐广播',
  'https://example.com/c/live.m3u8',
  '#EXTINF:-1,BBC中文台',
  'http://example.com/d/64k.mp3',
  '#EXTINF:-1,CCTV综合',
  'http://example.com/e/64k.mp3',
  'English News Channel',
  'http://example.com/f/64k.mp3',
].join('\n');

function exportData(tool) {
  const r = tool.parseInput(M3U);
  tool.S.rows = r.rows;
  tool.normalize();
  return tool.buildTsv()
    .split('\n')
    .filter(l => l.trim() && l.charAt(0) !== '#')
    .join('\n');
}
const enData = exportData(EN);
const zhData = exportData(ZH);
check('数据行逐字相同（注释头可以不同）', enData === zhData,
      '\n--- EN ---\n' + enData + '\n--- ZH ---\n' + zhData);

const enLines = enData.split('\n');
check('条数 = 6', enLines.length === 6, '实际 ' + enLines.length);
// ★ 合法地区 = PROVS（42 个省级/海外）+ SPECIAL_PROV（全国/其他）。
//   我第一版只查 PROVS，于是每一行的「其他」都被报成非法 ——
//   判据自己少查了一个数组，却让我以为产物坏了。
//   ⇒ 铁律 41 的又一次：先确认「正确答案」是什么，再写判据。
const OK_PROV = EN.PROVS.concat(EN.SPECIAL_PROV);
let bad = 0;
enLines.forEach((l) => {
  const c = l.split('\t');
  if (c.length !== 4) { bad++; console.log('      列数=' + c.length + ': ' + l); }
  else if (!/^https?:\/\//.test(c[3])) { bad++; console.log('      URL 异常: ' + c[3]); }
  else if (EN.CATS.indexOf(c[1]) < 0) { bad++; console.log('      栏目非法: ' + c[1]); }
  else if (OK_PROV.indexOf(c[2]) < 0) { bad++; console.log('      地区非法: ' + c[2]); }
});
check('每行四列且 token 全部合法', bad === 0, bad + ' 行有问题');
check('★ 输出无 BOM', enData.charCodeAt(0) !== 0xFEFF);
check('★ 输出无 CRLF', EN.buildTsv().indexOf('\r') < 0);
check('★ 栏目/地区确实写的是中文 token（不是英文）',
      enLines.some(l => EN.CATS.indexOf(l.split('\t')[1]) >= 0) &&
      enLines.some(l => OK_PROV.indexOf(l.split('\t')[2]) >= 0) &&
      enLines.every(l => !/^(News|Music|General|Traffic)$/.test(l.split('\t')[1])));

// ============================================================
console.log('\n=== 3. 推断逻辑未被翻译破坏 ===');
[['北京人民广播电台', '新闻综合'], ['BBC中文台', '境外新闻'],
 ['CCTV综合', '电视伴音'], ['深圳音乐广播', '音乐'],
 ['杭州交通经济广播', '交通台']].forEach(([n, want]) => {
  const got = EN.guessCat(n, '');
  check(n + ' → ' + want, got === want, '实际 ' + got);
});
check('guessProv(江苏交通广播) → 江苏',
      EN.guessProv('江苏交通广播') === '江苏',
      '实际 ' + EN.guessProv('江苏交通广播'));

// ============================================================
console.log('\n=== 4. 英文界面确实是英文（不是中文壳）===');
// ★ 判据设计说明（这里我改过一次，改对了）：
//     ① 协议 token：13 个栏目名、43 个地区名
//     ② 城市匹配表：约 200 个地级市名（用来从中文台名推断地区）
//     ③ FAQ 页的 zh 分支（英文模式下永不显示，但源码里在）
//   ⇒ 判据不能是"残留中文 = 0"，而是
//     【剥掉这三类之后，剩下的必须是 0】。
//   我第一版只剥了 token 和栏目词，城市名没剥 ⇒ 报了 12 个假。
// ★ 判据设计说明（这里我改过一次，改对了）：
//   界面里【必然】出现中文，且是应该出现的三类：
//     ① 协议 token：13 个栏目名、43 个地区名
//     ② 城市匹配表：约 200 个地级市名（用来从中文台名推断地区）
//     ③ FAQ 页的 zh 分支（英文模式下永不显示，但源码里在）
//   ⇒ 判据不能是"残留中文 = 0"，而是
//     【剥掉这三类之后，剩下的必须是 0】。
//   我第一版只剥了 token 和栏目词，城市名没剥 ⇒ 报了 12 个假。
const uiText = EN.viewConv() + EN.viewUse() + EN.viewDisc() + EN.viewAbout();
const UI_STRIP = [
  ...EN.CATS, ...EN.PROVS, ...EN.SPECIAL_PROV,
  ...(EN.PROVS_CN || []), ...(EN.PROVS_XW || []),
];
let residue = uiText;
UI_STRIP.forEach(t => { residue = residue.split(t).join(''); });
// FAQ 的中文分支：整段挖掉（'...zh 段...' 到三元运算符结束）
residue = residue.replace(/\[(?:[^\[\]]|\[[^\[\]]*\])*\]/g, '');
// 剩下的：只允许英文、空白、HTML 标签、标点、数学符号
const SAMPLE_OK = ['示例新闻广播', '示例之声', '示例交通广播', '示例音乐台',
                   '示例直播台', '示例乡镇广播', '人民广播电台',
                   '杭州交通经济广播', '深圳广播', '中文台', 'Example'];
SAMPLE_OK.forEach(t => { residue = residue.split(t).join(''); });
const leftCn = residue.match(/[\u4e00-\u9fff]{2,}/g) || [];
check('★ 剥掉 token/城市/FAQ-zh 后，界面残留中文 = 0',
      leftCn.length === 0, leftCn.slice(0, 12).join(' | '));
check('（城市名确实仍以中文出现在下拉框里，这是有意的）',
      /北京/.test(uiText) && /天津/.test(uiText));

check('英文界面含英文字段名 Name/Category/Region',
      EN.viewConv().indexOf('Category') >= 0 &&
      EN.viewConv().indexOf('Region') >= 0);
check('英文界面含关键操作词 Download / Self-check',
      /Download\s+stations\.tsv/.test(EN.viewConv()));
check('页面标题为英文',
      /<title>XianDial/.test(
        fs.readFileSync(path.join(__dirname, 'XianForge.en.html'), 'utf8')));

// ============================================================
console.log('\n=== 5. 英文版自述：告知 token 为中文是有意的 ===');
const about = EN.viewAbout();
check('About 页说明了 token 是固件固定标识符',
      /fixed Simplified Chinese identifiers the firmware parses/.test(about));

// ============================================================
console.log('\n' + '='.repeat(58));
if (fails === 0) {
  console.log('✓ 全部通过');
  process.exit(0);
} else {
  console.log('✗ ' + fails + ' 项失败');
  process.exit(1);
}