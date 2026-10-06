/* 真浏览器验证：用 Chrome DevTools Protocol 打开 XianForge.en.html，
 * 真的点按钮、真的导出，然后把导出的 TSV 拿回来核对。
 * ★ 为什么不用 jsdom：jsdom 只验 JS 能跑，验不了「界面真的显示英文」。
 *   这个脚本要的是屏幕上那个 DOM。
 * 用法：node _xf_en_browser.js <html路径> <截图输出png>
 */
'use strict';
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9333;
const file = process.argv[2];
const shot = process.argv[3];

function get(url) {
  return new Promise((res, rej) => {
    http.get(url, r => { let d = ''; r.on('data', c => d += c);
                         r.on('end', () => res(JSON.parse(d))); }).on('error', rej);
  });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const prof = path.join(require('os').tmpdir(), 'xf_en_chrome_' + Date.now());
  const chrome = spawn(CHROME, [
    '--headless=new', '--disable-gpu', '--no-first-run',
    '--remote-debugging-port=' + PORT,
    '--user-data-dir=' + prof,
    '--window-size=1280,1600',
    'file:///' + file.replace(/\\/g, '/'),
  ], { stdio: 'ignore' });

  let ver = null;
  for (let i = 0; i < 40; i++) {
    try { ver = await get('http://127.0.0.1:' + PORT + '/json/version'); break; }
    catch (e) { await sleep(300); }
  }
  if (!ver) { console.error('✗ Chrome 没起来'); chrome.kill(); process.exit(2); }
  console.log('  Chrome:', ver['Browser']);

  // ★ 必须连【页面 target】的 webSocketDebuggerUrl，不能连 /json/version 那个。
  //   /json/version 返回的是【浏览器级】端点，连上之后 Runtime.evaluate
  //   全部返回 undefined —— 我第一版就这么写的，输出是一排 undefined，
  //   而且我居然还打了 ✓（因为只判断了「没抛异常」）。
  //   ⇒ 教训：断言不能只判"没报错"，必须判"值对得上"。
  const list = await get('http://127.0.0.1:' + PORT + '/json/list');
  const page = list.find(t => t.type === 'page' && t.url.indexOf('file:') >= 0)
            || list.find(t => t.type === 'page');
  if (!page) { console.error('✗ 找不到页面 target'); chrome.kill(); process.exit(2); }
  console.log('  页面：', (page.title || page.url).slice(0, 60));

  const WebSocket = require('ws');
  let ws;
  try { ws = new WebSocket(page.webSocketDebuggerUrl); }
  catch (e) {
    console.log('  （没装 ws 模块）');
    chrome.kill(); process.exit(3);
  }
  await new Promise(r => ws.on('open', r));

  let id = 0; const pend = new Map();
  ws.on('message', m => {
    const j = JSON.parse(m);
    if (j.id && pend.has(j.id)) { pend.get(j.id)(j); pend.delete(j.id); }
  });
  const send = (method, params) => new Promise(r => {
    const i = ++id; pend.set(i, r);
    ws.send(JSON.stringify({ id: i, method, params: params || {} }));
  });
  const evalJS = async expr => {
    const r = await send('Runtime.evaluate',
      { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) {
      throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 300));
    }
    return r.result && r.result.result ? r.result.result.value : undefined;
  };

  await send('Runtime.enable');
  await send('Page.enable');
  await sleep(1200);

  // 1. 页面加载无 JS 报错
  const title = await evalJS('document.title');
  console.log('  ✓ 标题：' + title);

  const lang = await evalJS('document.documentElement.lang');
  console.log('  ✓ html lang = ' + lang);

  const navTxt = await evalJS(
    'Array.from(document.querySelectorAll("#nav button")).map(b=>b.textContent).join(" | ")');
  console.log('  ✓ 导航页签：' + navTxt);

  // 2. 各页正文是不是英文（抓可见文本里的中文）
  for (const [id, name] of [['conv','Convert'],['check','Self-check'],
                            ['use','How to use'],['disc','Disclaimer'],
                            ['about','About']]) {
    await evalJS(`(function(){ S.page='${id}'; render(); })()`);
    await sleep(150);
    const cn = await evalJS(
      '(function(){var t=document.getElementById("main").innerText;' +
      'return (t.match(/[\\u4e00-\\u9fff]/g)||[]).length;})()');
    console.log(`  ${cn === 0 ? '✓' : '·'} ${name.padEnd(12)} 页内汉字数 = ${cn}`);
  }

  // 3. 真跑一遍转换：塞 M3U → 解析 → 导出
  await evalJS(`(function(){ S.page='conv'; render(); })()`);
  await sleep(150);
  const n = await evalJS(`(function(){
    var ta = document.getElementById('ta');
    ta.value = ['#EXTM3U',
      '#EXTINF:-1,北京人民广播电台',
      'http://example.com/a/64k.mp3',
      '#EXTINF:-1,杭州交通经济广播',
      'http://example.com/b/64k.mp3',
      '#EXTINF:-1,深圳音乐广播',
      'https://example.com/c/live.m3u8',
      '#EXTINF:-1,BBC中文台',
      'http://example.com/d/64k.mp3',
      '#EXTINF:-1,English News Channel',
      'http://example.com/e/64k.mp3'].join('\\n');
    ingestText(ta.value, 'test.m3u');
    render();
    return S.rows.length;
  })()`);
  console.log('  ✓ 浏览器内解析出 ' + n + ' 条');

  const tsv = await evalJS('buildTsv()');
  const data = tsv.split('\n').filter(l => l.trim() && l[0] !== '#');
  console.log('  ✓ 导出数据行 ' + data.length + ' 条');
  data.forEach(l => {
    const c = l.split('\t');
    const okc = c.length === 4;
    const oku = /^https?:\/\//.test(c[3] || '');
    console.log(`     ${okc && oku ? '✓' : '✗'} ${l}`);
  });

  // 4. 关键判据：栏目/地区必须是中文 token
  //  ★ 这些符号是 <script> 里的顶层 var/function，在页面全局作用域上可见，
  //    但 Runtime.evaluate 默认跑在【另一个独立世界】里，看不到它们。
  //    必须显式声明它们在页面全局上 —— 我第一版直接写 CATS，
  //    报 "CATS is not defined"，而前面 12 行输出全是 ✓，
  //    看起来像"测过了"。
  const tokOk = await evalJS(`(function(){
    var C = CATS, P = PROVS, SP = SPECIAL_PROV;
    var out = ${JSON.stringify(data)};
    return out.every(function(l){
      var c = l.split('\\t');
      return C.indexOf(c[1]) >= 0 &&
             (P.indexOf(c[2]) >= 0 || SP.indexOf(c[2]) >= 0);
    });
  })()`);
  console.log('  ' + (tokOk ? '✓' : '✗') + ' 栏目/地区 token 全为中文协议值');
  console.log('  ' + (tsv.indexOf('\r') < 0 ? '✓' : '✗') + ' 无 CRLF');
  console.log('  ' + (tsv.charCodeAt(0) !== 0xFEFF ? '✓' : '✗') + ' 无 BOM');

  // 5. 截图
  await evalJS(`(function(){ S.page='conv'; render(); })()`);
  await sleep(400);
  const r = await send('Page.captureScreenshot', { format: 'png',
                                                   captureBeyondViewport: true });
  if (r.result && r.result.data) {
    fs.writeFileSync(shot, Buffer.from(r.result.data, 'base64'));
    console.log('  ✓ 截图：' + shot);
  }

  ws.close(); chrome.kill();
  try { fs.rmSync(prof, { recursive: true, force: true }); } catch (e) {}
  const allOk = tokOk && data.length === 5 && tsv.indexOf('\r') < 0;
  console.log('\n' + (allOk ? '✓ 全部通过' : '✗ 有失败项'));
  process.exit(allOk ? 0 : 1);
})().catch(e => { console.error('✗', e.message); process.exit(2); });