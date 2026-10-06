#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""XianForge 英文版 · 第二阶段：整块翻译四个说明页

★ 为什么单独一个文件
  _make_xianforge_en.py 走的是「单字面量替换」，能覆盖按钮、标签、报错。
  但「使用方法 / 免责 / 关于 / FAQ」这四页是【整段 HTML 字符串拼接】，
  逐字替换要写上百条映射、且极易漏掉半个句子。
  ⇒ 这里改成整函数替换：定位 `function viewXxx(){` 到下一个 `\n}` 的
    整段源码，整体换成英文。判据是【函数头】而不是行号 ——
    行号会随任何一次改动漂移，整块替换就会悄悄替换错位置。

★ 一个必须写对的事实
  原文「使用方法」页写着「恢复内置台单 / 1254 台」—— 那是**自用版**的说法。
  发布版内置台单是 0 条，固件里根本没有「内置台单」可恢复。
  英文版按**发布版事实**写：只有读卡导入一条路，没有「restore built-in」。
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "XianForge.en.html")
# ★ 不硬编码本机路径与用户名 —— 发布闸门 _release_gitscan 会把
#   "C:\Users\<name>\..." 判成隐私泄漏（而且那本来就不该进仓库）。
#   需要指定 node 时设环境变量 XF_NODE，否则用 PATH 里的 node。
NODE = os.environ.get("XF_NODE", "node")

# ────────────────────────────────────── 四个说明页的英文整块实现
BLOCKS = {}

BLOCKS["viewUse"] = r'''function viewUse(){
  return '<div class="card doc"><h2>How to use</h2>'
   + '<h3>1 &middot; Convert (on your computer)</h3>'
   + '<ol>'
   + '<li>Find your station list (<code>.m3u</code> or <code>.txt</code>). Common sources are share links people post, or station-list repositories on Gitee / GitHub.</li>'
   + '<li>Drag it into the drop area at the top of this page, or paste the content. UTF-8 / GBK / UTF-16 are detected automatically &mdash; no transcoding needed.</li>'
   + '<li>Look at the parse result. Rows with no name fall back to the domain or file name and are flagged <b>auto-named</b>.</li>'
   + '<li>Review. Every cell is editable; use the chips at the top to change the <b>category</b> or <b>region</b> for all rows at once.</li>'
   + '<li>Open the <b>Self-check</b> tab and confirm there are no hard errors.</li>'
   + '<li>Click <b>Download stations.tsv</b>.</li>'
   + '</ol>'
   + '<h3>2 &middot; Put it on the card (TF / microSD)</h3>'
   + '<ol>'
   + '<li>Copy <code>stations.tsv</code> to the <b>root</b> of the card, not into a subfolder.</li>'
   + '<li>&#9888;&#65039; Make sure the <b>device is powered off</b> before inserting the card; hot-swapping can damage it.</li>'
   + '<li>&#9888;&#65039; The onboard Type-C port <b>cannot act as a USB host</b>, so reading the card over a PC connection will not work. Use a USB card reader, or put the card straight into the device.</li>'
   + '</ol>'
   + '<h3>3 &middot; Import on the device</h3>'
   + '<ol>'
   + '<li>Power on. The device reads <code>/stations.tsv</code> from the card automatically and shows the station count.</li>'
   + '<li>That is the whole flow. If the card is missing or the file is unreadable, the device simply stays at 0 stations &mdash; it never shows a blank screen.</li>'
   + '<li>You can also push the file over the serial console instead of using a card. See <code>tools/_sd_push.py</code>.</li>'
   + '</ol>'
   + '<h3>4 &middot; The two traps you must know about</h3>'
   + '<ul>'
   + '<li>&#9888;&#65039; <b>No BOM</b>. Notepad&rsquo;s &ldquo;UTF-8&rdquo; save adds a BOM by default, which puts a box glyph in front of the first station name and permanently breaks name-based favourites.</li>'
   + '<li>&#9888;&#65039; <b>Line endings must be LF</b>. Many Windows tools write CRLF, which leaves an invisible character at the end of every URL &mdash; symptom: &ldquo;every other station works, but these few don&rsquo;t&rdquo;.</li>'
   + '</ul>'
   + '<p>Both of those are handled by this page, so the file you download is already correct.</p>'
   + '</div>';
}'''

BLOCKS["viewDisc"] = r'''function viewDisc(){
  return '<div class="card doc"><h2>Disclaimer</h2>'
   + '<p>This tool is a companion utility for the <a href="#" data-x="1">XianDial</a> hardware project. It is an <strong>unofficial third-party tool</strong>, '
   + 'is not affiliated with any radio station, TV network, platform or organisation, and does not speak for any of them.</p>'
   + '<ul>'
   + '<li>This tool performs <b>text format conversion</b> only. It does not collect, provide or proxy any station URL. What you import is your own decision.</li>'
   + '<li>All data is processed <b>inside your own browser</b>. Nothing is uploaded to any server, and there is no analytics.</li>'
   + '<li>This tool <b>does not check whether a station is reachable</b>. A successful conversion does not mean you can hear it &mdash; dead URLs are normal.</li>'
   + '<li>Please <b>listen only to stations you are legally permitted to receive</b> in your country or region. Complying with local rules is your responsibility.</li>'
   + '<li>Use it as-is, at your own risk. The tool&rsquo;s author accepts no liability for indirect loss.</li>'
   + '<li>All station names, frequencies and programme content remain the property of their respective rights holders. Trademarks belong to their respective owners.</li>'
   + '</ul>'
   + '<p style="color:var(--tx2);font-size:13px;margin-top:14px">Free to use and to redistribute unchanged &mdash; please keep the attribution. '
   + 'If you modify it, please keep the modified version to yourself and do not redistribute it. &copy; Lanlan Eternal (&#27704;&#32445;&#32445;&#30340;&#20891;&#20891;). All rights reserved.</p>'
   + '</div>';
}'''

BLOCKS["viewAbout"] = r'''function viewAbout(){
  return '<div class="card doc"><h2>About</h2>'
   + '<p><b>XianDial &middot; Station List Builder</b> (XianForge) is the companion tool for the XianDial hardware project. '
   + 'It converts an M3U or plain-text station list you found online into a format the device can read.</p>'
   + '<h3>Why it exists</h3>'
   + '<p>This firmware ships with <b>zero built-in stations</b> &mdash; that is deliberate, not unfinished. '
   + 'A list of real stream URLs is the project&rsquo;s biggest public risk, and shipping one would make this repository a distribution channel for somebody else&rsquo;s servers. '
   + 'So the device can only play your stations if you provide them as a file that it reads at runtime. '
   + 'This tool is the first half of that path; the second half lives in the firmware.</p>'
   + '<h3>What it deliberately does not do</h3>'
   + '<ul>'
   + '<li>It does not collect stations or provide station URLs, and it <b>touches no copyrighted content</b>.</li>'
   + '<li>It does not test station availability over the network (a web page is cross-origin restricted, so it cannot give a trustworthy answer).</li>'
   + '<li>It installs nothing and changes nothing on your system. Double-click and it runs.</li>'
   + '</ul>'
   + '<h3>Technical notes</h3>'
   + '<ul>'
   + '<li>A single HTML file with <b>zero external dependencies</b>. Double-click to run, fully offline.</li>'
   + '<li>Automatic UTF-8 / GBK / UTF-16 detection.</li>'
   + '<li>Always exports <b>UTF-8 without BOM and LF line endings</b> &mdash; these are the two things the firmware most often misreads.</li>'
   + '<li>Category and region values are written as the <b>fixed Simplified Chinese identifiers the firmware parses</b> (13 categories, 42 regions). They are protocol tokens, not display text, so an export made with this English tool loads on the Chinese firmware unchanged.</li>'
   + '</ul>'
   + '<div class="sig" style="text-align:left;margin-top:20px">'
   + 'XianDial &middot; Station List Builder v1.0<br>&copy; Lanlan Eternal</div>'
   + '</div>';
}'''

# ★ selfCheck 是【纯字符串拼接】—— 每个 push 的参数里没有任何 HTML 标签，
#   所以「只替换 >…< 之间的可见文本」这一路完全够不着它。
#   实测：改成标签边界匹配后，selfCheck 里 9 条文案一条没换。
#   ⇒ 整函数替换。★ 判据只看「有没有动过 token」：
#     这段文案里出现 13 个栏目名与 42 个地区名，
#     翻译时必须保留它们在引号内的中文原样。
BLOCKS["selfCheck"] = r'''function selfCheck(){
  var r=[], hard=[], soft=[];
  var n = S.rows.length;

  if(!n){ r.push(['warn','No stations parsed yet. Paste or drop an M3U / plain-text list above.']); return r; }

  /* names */
  var badName=S.rows.filter(function(x){return x.err.indexOf('name-long')>=0||x.err.indexOf('name-tab')>=0;});
  if(badName.length) hard.push('There <code>'+badName.length+'</code> rows have a name over '+MAX_NAME+' bytes or containing a TAB &mdash; those rows export corrupted and the firmware cannot read them.');

  /* URL */
  var badUrl=S.rows.filter(function(x){return x.err.indexOf('url-bad')>=0;});
  var longUrl=S.rows.filter(function(x){return x.err.indexOf('url-long')>=0;});
  if(badUrl.length) hard.push('There <code>'+badUrl.length+'</code> rows have a URL that does not start with http/https. They were kept &mdash; please check them.');
  if(longUrl.length) hard.push('There <code>'+longUrl.length+'</code> rows have a URL over '+MAX_URL+' bytes, exceeding the firmware field limit.');

  /* unknown category / region */
  var badCat=S.rows.filter(function(x){return x.err.indexOf('cat-unknown')>=0;});
  var badProv=S.rows.filter(function(x){return x.err.indexOf('prov-unknown')>=0;});
  if(badCat.length) hard.push('There <code>'+badCat.length+'</code> rows use a category that is not one of the 13 standard values; the firmware will fall back to the default.');
  if(badProv.length) hard.push('There <code>'+badProv.length+'</code> rows use a region that is not one of the 42 standard values; the firmware will fall back to the default.');

  /* count */
  if(n>MAX_N) hard.push('Parsed <code>'+n+'</code> stations, over the firmware limit of <code>'+MAX_N+'</code> stations. The import will be rejected.');
  else if(n>MAX_N*0.8) soft.push('You already have <code>'+n+'</code> stations, close to the limit of '+MAX_N+' stations.');

  /* protocol mix */
  var hls=S.rows.filter(function(x){return /\.m3u8(\?|$)/i.test(x.url);}).length;
  var http=S.rows.filter(function(x){return /^http:/i.test(x.url);}).length;
  var https=S.rows.length-http;
  soft.push('Protocol mix: <code>http '+http+'</code> / <code>https '+https+'</code>, of which <code>HLS(m3u8) '+hls+'</code>.');
  if(hls) soft.push('HLS stations do play on the XianDial firmware, but they cost more bandwidth and memory. <b>Verify one yourself</b> before relying on it.');

  /* suspicious URLs */
  var q = S.rows.filter(function(x){return /\?wsSession=|&wsIPSercert=|token=|sessionid=/i.test(x.url);});
  if(q.length) soft.push('There <code>'+q.length+'</code> URLs carry signed parameters (wsSession and friends). <b>These links expire</b> &mdash; they are one-shot sources.');
  var demo = S.rows.filter(function(x){return /example\.com|localhost|127\.0\.0\.1|test\.|\/test$|your[-_]?url/i.test(x.url);});
  if(demo.length) soft.push('There <code>'+demo.length+'</code> URLs look like examples or local addresses; they will not play once imported.');

  /* font coverage note */
  soft.push('If an imported name contains rare characters, the UI may show a box glyph. This depends on whether the station-name font in the firmware covers the GB2312 level-1 set.');

  if(!hard.length) r.push(['pass','All hard checks passed: ' + n + ' stations &mdash; names, URLs, categories and regions are all within limits.']);
  hard.forEach(function(h){ r.push(['err',h]); });
  soft.forEach(function(s){ r.push(['warn',s]); });
  return r;
}'''

# FAQ：原文是三元切换，英文版直接取英文那半
BLOCKS["viewFaq"] = r'''function viewFaq(){
  var faqs = (S.lang==='zh') ? [
    ['台名全是乱码怎么办？',
     '正常不会。本页自动识别 UTF-8／GBK／UTF-16。如果还是乱码，说明源文件本身就用了别的编码（比如 Big5）—— 把它用记事本另存为 UTF-8，再拖进来。'],
    ['有些台显示「需修正」，还能导吗？',
     '能导，但要弄清是哪一类。<b>地址不是 http 开头</b>和<b>台名超长</b>会真的坏事；<b>栏目／地区对不上</b>只是会被固件归到「综合」或「其他」，不影响播放。'],
    ['为什么不做「在线验活」？',
     '因为网页受跨域限制，对绝大多数第三方流都探不到，<b>给出「可播」的假结论比不给更糟</b>——用户导入完发现一半播不了，会怪到固件头上。所以这里只保证格式对、地址合法，能不能播由机器说话。'],
    ['HLS（.m3u8）的台能导吗？',
     '能，固件支持。但 HLS 更吃流量和内存，建议自己先在机器上试播几个常用的，再决定留哪些。'],
    ['带 wsSession 这种签名地址怎么办？',
     '这类链接<b>会过期</b>，属于一次性源，导入后过阵子就播不出来。本页会把它标出来，别当成长期台单。'],
    ['上限 2000 台是怎么来的？',
     '固件侧台单放 PSRAM（ESP32-S3 的 8 MB 里给台单分了约 200 KB 预算）。2000 台是留了余量后的数。再多机器装不下，导入会被直接拒绝。'],
    ['导入了以后原来的收藏还在吗？',
     '在。收藏和历史存的是<b>台名不是序号</b>，开机重解析台单。所以同一个台的内置版和导入版能对上，不会指错。'],
    ['台单文件能放子目录吗？',
     '不能，必须在 SD 卡根目录，而且文件名就是 stations.tsv。固件只认这一个路径。'],
    ['能转多份吗？',
     '一次转一份。想要多套就分多次导 —— 固件目前只读根目录那一个 stations.tsv。']
  ] : [
    ['Station names all garbled?',
     'Normally not. This page auto-detects UTF-8 / GBK / UTF-16. If it is still garbled, the source uses another encoding (e.g. Big5) — re-save it as UTF-8 and drop it in again.'],
    ['Rows flagged "needs fix" — can I still export?',
     'Yes, but check which kind. A URL not starting with http, or an over-long name, actually breaks things. An unknown category/region only falls back to "General" / "Other" and does not affect playback.'],
    ['Why is there no online liveness check?',
     'Because a web page is cross-origin restricted and cannot probe most third-party streams. A false "playable" verdict is worse than none — the user would blame the firmware. Here we only guarantee the format is correct; the device decides what actually plays.'],
    ['Can I import HLS (.m3u8) stations?',
     'Yes, the firmware supports it. But HLS costs more bandwidth and memory. Try a few on the device first before committing them to the list.'],
    ['What about signed URLs with wsSession?',
     'They expire. They are one-shot sources and will stop playing after a while. This page flags them so you do not treat them as a permanent list.'],
    ['Where does the 2000-station limit come from?',
     'The station list lives in PSRAM (about 200 KB of the ESP32-S3\'s 8 MB is budgeted for it). 2000 is the number left after headroom. Beyond that the device cannot hold it and import is rejected.'],
    ['Will my favourites survive an import?',
     'Yes. Favourites and history store the station NAME, not the index, and are re-resolved at boot. So the built-in and imported version of the same station match up correctly.'],
    ['Can the file live in a subfolder?',
     'No. It must be stations.tsv in the SD card root. The firmware looks at exactly that path.'],
    ['Can I convert several lists?',
     'One list per pass. The firmware reads the single /stations.tsv in the card root.']
  ];
  var h='<div class="card doc"><h2>'+(S.lang==='zh'?'常见问题':'FAQ')+'</h2>';
  faqs.forEach(function(f,i){
    h += '<h3>'+(i+1)+'. '+esc(f[0])+'</h3><p>'+f[1]+'</p>';
  });
  h += '</div>';
  return h;
}'''


def replace_func(src, name, new_code):
    """整函数替换。判据用函数头，不依赖行号。"""
    pat = re.compile(r"function\s+" + re.escape(name) + r"\s*\(\s*\)\s*\{")
    m = pat.search(src)
    if not m:
        raise SystemExit("找不到函数 %s" % name)
    # 从函数头起，扫到【列 0 的右花括号 + 换行】或下一个 function 定义为止
    i = src.index("{", m.start())
    depth = 0
    j = i
    instr = None
    while j < len(src):
        ch = src[j]
        if instr:
            if ch == "\\":
                j += 2
                continue
            if ch == instr:
                instr = None
        elif ch in "'\"":
            instr = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    if depth != 0:
        raise SystemExit("函数 %s 括号不配对" % name)
    old = src[m.start():j + 1]
    if "function" not in new_code:
        raise SystemExit("新代码不含函数头")
    return src[:m.start()] + new_code + src[j + 1:], len(old)


def main():
    if not os.path.exists(SRC):
        print("找不到 XianForge.en.html —— 请先跑 _make_xianforge_en.py")
        return 1
    src = io.open(SRC, encoding="utf-8", newline=None).read()
    total = 0
    for name in ("selfCheck", "viewUse", "viewFaq", "viewDisc", "viewAbout"):
        src, n = replace_func(src, name, BLOCKS[name])
        print("  %-10s 整块替换 %d 字符 -> %d 字符" % (name, n, len(BLOCKS[name])))
        total += n

    # ---- ★ 语法闸门：整块替换是手写代码，必须验能被 JS 引擎解析
    node = NODE if os.path.exists(NODE) else "node"
    js = re.search(r"<script[^>]*>([\s\S]*?)</script>", src)
    tmp = os.path.join(HERE, "_xf_en_syntax_tmp2.js")
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(js.group(1))
    p = subprocess.run([node, "--check", tmp], capture_output=True,
                       text=True, errors="replace")
    try:
        os.remove(tmp)
    except OSError:
        pass
    if p.returncode != 0:
        print("★ JS 语法错误：")
        print((p.stderr or "").strip()[:500])
        return 1
    print("  JS 语法自检：通过")

    io.open(SRC, "w", encoding="utf-8", newline="\n").write(src)
    print("完成，五个函数共替换 %d 字符" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())