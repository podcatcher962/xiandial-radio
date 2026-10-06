#!/usr/bin/env node
/* XianForge 冒烟测试（无浏览器）
 * ============================================================
 * 为什么要它：README 里写「工具能造台源」是一句话，但那句话
 *   我【没法只靠读代码确认】—— 上一轮就因为规则表里少了一条
 *   「XX人民广播电台」，把最常见的台名全判成了「综合」，
 *   而编译零报错、界面也看不出来。
 *
 *   ⇒ 铁律 41：自写 check 要先拿已知答案验证再信结论。
 *     这个文件就是那组「已知答案」。
 *
 * 跑法（需要 node，仓库根目录下）：
 *   node tools/_xf_selftest.js
 *
 * 做法：把 XianForge.html 里的 <script> 抽出来，套一层极简 DOM 桩，
 *   然后直接调它的纯函数（parseInput / normalize / guessCat / buildTsv）。
 *   不测渲染、不测交互 —— 那些要真浏览器，那是另一回事。
 * ============================================================ */
'use strict';
const fs = require('fs');
const path = require('path');

// ---- DOM 桩：只提供脚本 init 阶段会碰到的那些接口 ----
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
global.window = { addEventListener(){}, location: { href: '' }, navigator: { userAgent: 'node' } };
// ⚠ Node 21+ 的 globalThis.navigator 是【只读 getter】，直接赋值会抛
//   "Cannot set property navigator of #<Object> which has only a getter"。
//   用 defineProperty 绕过。（我第一次写 `global.navigator = {...}` 就踩了）
try {
  Object.defineProperty(globalThis, 'navigator',
    { value: { userAgent: 'node' }, writable: true, configurable: true });
} catch (e) { /* 老版本 Node 上没这个限制，忽略 */ }
global.localStorage = { getItem: () => null, setItem(){}, removeItem(){} };
global.alert = () => {};
global.FileReader = function () { this.readAsArrayBuffer = () => {}; };
global.Blob = function () {};
// ⚠⚠ 不要覆盖 global.URL —— Node 的 URL 是【类构造器】，fs shim 里有
//   `filePath instanceof URL`。我为了补 createObjectURL 把它换成普通对象，
//   结果 fs.readFileSync 直接报 "Right-hand side of 'instanceof' is not callable"。
//   ⇒ 只补缺失的方法，保留原构造器。
if (typeof global.URL.createObjectURL !== 'function') {
  global.URL.createObjectURL = () => 'blob:x';
}

// ---- 载入被测脚本 ----
const html = fs.readFileSync(path.join(__dirname, 'XianForge.html'), 'utf8');
const m = html.match(/<script[^>]*>([\s\S]*)<\/script>/);
if (!m) { console.error('✗ 在 XianForge.html 里找不到 <script> 段'); process.exit(2); }

/* ⚠⚠ 这里【必须】用 new Function + 挂到 globalThis，不能用间接 eval：
 *   间接 eval 的代码里 `var`/`function` 声明落在 eval 自己的局部作用域，
 *   外层看不见 —— 我第一版写 (0,eval)(m[1])，结果后面直接
 *   "ReferenceError: guessCat is not defined"。
 *   而 new Function 的代码体里 var/function 属于该函数作用域，
 *   追加 return 就能把需要的符号一次性交出来。
 */
const EXPORTS = ['S', 'CATS', 'PROVS', 'parseInput', 'normalize',
                 'buildTsv', 'buildExample', 'guessCat', 'guessProv',
                 'extinfTitle'];
// eslint-disable-next-line no-new-func
const load = new Function(m[1] + '\nreturn {' + EXPORTS.join(',') + '};');
const X = load();
const { S, CATS } = X;
const { parseInput, normalize, buildTsv, guessCat } = X;

let fails = 0;
function check(label, cond, detail) {
  if (cond) { console.log('  ✓ ' + label); }
  else { console.log('  ✗ ' + label + (detail ? ('   ' + detail) : '')); fails++; }
}

// ============================================================
console.log('=== 1. 栏目推断（拿已知答案验）===');
// 第 3 个值 = 是否必须匹配；0 表示「不该是这个」
const CASES = [
  ['北京人民广播电台', '新闻综合', 1], ['广东人民广播电台', '新闻综合', 1],
  ['西藏人民广播电台', '新闻综合', 1], ['中国之声', '新闻综合', 1],
  ['中央人民广播电台', '新闻综合', 1], ['中国之声—海南版', '新闻综合', 1],
  ['中国国际广播电台', '境外新闻', 1], ['BBC中文台', '境外新闻', 1],
  ['上海戏曲曲艺广播', '戏曲', 1], ['杭州交通经济广播', '交通台', 1],
  ['深圳音乐广播', '音乐', 1], ['古典音乐台', '音乐', 1],
  ['北京文艺广播', '文艺', 1], ['中国教育广播', '教育台', 1],
  // 优先级回归：电视伴音必须压过新闻综合
  ['CCTV综合', '电视伴音', 1], ['湖南卫视', '电视伴音', 1],
  // 护栏：地名里的「莲花」「佛山」不算宗教
  ['莲花山广播', '宗教', 0], ['佛山人民广播', '宗教', 0],
];
CASES.forEach(([n, want, must]) => {
  const got = guessCat(n, '');
  check(n + ' → ' + want, must ? (got === want) : (got !== want),
        '实际 ' + got);
});

// ============================================================
console.log('\n=== 2. M3U 解析 + TSV 生成 ===');
const m3u = [
  '#EXTM3U',
  '#EXTINF:-1 tvg-id="r1" tvg-name="R1" group-title="新闻",北京人民广播电台',
  'http://example.com/a/64k.mp3',
  '#EXTINF:-1,上海东方卫视',
  'http://example.com/b/64k.mp3',
  '#EXTINF:-1,GLISH NEWS',
  'http://example.com/c/64k.mp3',
  '#EXTINF:-1,重复的台',
  'http://example.com/a/64k.mp3',      // 与第 1 条同 URL —— 应被去重
  '戏曲频道, http://example.com/d/64k.mp3',
].join('\n');

const r = parseInput(m3u);
check('识别为 M3U', r.m3u === true);
check('解析出 5 条', r.rows.length === 5, '实际 ' + r.rows.length);
check('tvg-* 属性被剥掉（第 1 条台名干净）',
      r.rows[0].name === '北京人民广播电台', '实际 ' + JSON.stringify(r.rows[0].name));

S.rows = r.rows;
normalize();
check('URL 去重后剩 4 条', S.rows.length === 4, '实际 ' + S.rows.length);

const tsv = buildTsv();
const data = tsv.split('\n').filter(l => l.trim() && l.charAt(0) !== '#');
check('TSV 数据行数 = 4', data.length === 4, '实际 ' + data.length);
let bad = 0;
data.forEach((l) => {
  const c = l.split('\t');
  if (c.length !== 4) { bad++; console.log('      列数=' + c.length + ': ' + l); }
  else if (!/^https?:\/\//.test(c[3])) { bad++; console.log('      URL 异常: ' + c[3]); }
  else if (CATS.indexOf(c[1]) < 0) { bad++; console.log('      栏目不在 13 类内: ' + c[1]); }
});
check('每行都是「台名/栏目/地区/URL」4 列且取值合法', bad === 0, bad + ' 行有问题');

// ============================================================
console.log('\n=== 3. 边界情况 ===');
// 3.1 空输入
check('空输入不炸', (() => {
  try { const z = parseInput(''); return z.rows.length === 0; } catch (e) { return false; }
})());
// 3.2 缺台名 → 【normalize()】里用 URL 兜底，不留空台名行。
//     ⚠ 我第一版把这条写成「parseInput 后就该有名字」，实测失败 ——
//     翻代码才发现兜底在 normalize() 里（r.name 为空时拿域名+末段文件名）。
//     ⇒ 这就是铁律 41：拿已知答案验之前，先确认「正确答案」是什么。
const noName = parseInput('#EXTM3U\nhttp://example.com/only-url/64k.mp3');
check('缺台名的条目被 parseInput 收进来',
      noName.rows.length === 1, '实际 ' + noName.rows.length);
S.rows = noName.rows;
normalize();
check('normalize 后台名非空（用 URL 兜底）',
      S.rows.length === 1 && S.rows[0].name.length > 0,
      JSON.stringify(S.rows));
// 3.3 CRLF 必须归一化（Windows 存的 M3U 最常见）
const crlf = parseInput('#EXTM3U\r\n#EXTINF:-1,测试台\r\nhttp://example.com/x/64k.mp3\r\n');
check('CRLF 归一化后能解析出 1 条',
      crlf.rows.length === 1 && crlf.rows[0].url === 'http://example.com/x/64k.mp3',
      JSON.stringify(crlf.rows));
// 3.4 行尾粘连的垃圾字符
const junk = parseInput('#EXTM3U\n#EXTINF:-1,测试台\nhttp://example.com/y/64k.mp3\r');
check('URL 尾部 CR 被去掉',
      junk.rows.length === 1 && junk.rows[0].url === 'http://example.com/y/64k.mp3',
      JSON.stringify(junk.rows));
// 3.5 非 URL 行被丢弃
const noise = parseInput('#EXTM3U\n这是一行注释不是URL\n#EXTINF:-1,正常台\nhttp://example.com/z/64k.mp3');
check('无 URL 的行被丢弃', noise.rows.length === 1, JSON.stringify(noise.rows));

// ============================================================
console.log('\n' + '='.repeat(58));
if (fails === 0) {
  console.log('✓ 全部通过');
  process.exit(0);
} else {
  console.log('✗ ' + fails + ' 项失败');
  process.exit(1);
}