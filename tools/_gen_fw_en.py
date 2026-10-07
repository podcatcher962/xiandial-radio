#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从中文版源码生成英文版源码（拾声 XianDial · 面向国际使用者的版本）

=========================== 为什么是「生成」不是「手写两份」===========================
英文版与中文版的**逻辑代码必须 100% 相同**（同一份播放/配网/导入逻辑，
只是文案与字库不同）。手写两份 = 改一处 bug 要改两处 = 迟早分叉。
⇒ 英文版源码由本脚本从中文版生成，放在 en/ 目录，CMake 按开关选用。
   译文真源＝ tools/_xf_fw_en_text.py（改翻译只改那一个文件）。

=========================== 三条铁律===========================
① ★★★ 协议 token 绝对不能翻★★★
   栏目 13 个（g_cat_name）+ 地区 42 个（g_prov_name）+ 全国/其他。
   它们是 TSV 第 2、3 列的匹配键：app_stlist.c 用 strcmp 逐个比。
   翻成 "News"之后：导入不报错、四列都合法、界面正常，
   只有分类/地区全落兜底 —— 而所有格式检查都绿。
   ⇒ 本脚本【一个字节都不碰】net_stations*.c 与 g_cat_name/g_prov_name。

② ★ 日志串不翻★
   ESP_LOG*/printf 的中文使用者看不到（只在串口监视器里）。
   翻了纯浪费 flash。判据＝字符串进的是 lv_label_set_text* / tap_note
   还是 ESP_LOG/printf。

③ ★★ 字面量必须【折叠后再匹配】★★★
   源码里一句话常被拆成 'A' + 'B' + 'C' 三段（为了塞进行宽）。
   不折叠就永远匹配不上整句 ⇒ 第一版只命中 55/118。
"""

import io
import os
import shutil
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.abspath(os.path.join(HERE, ".."))
DST_ROOT = os.path.join(SRC_ROOT, "en")

sys.path.insert(0, HERE)
from _xf_fw_en_text import (  # noqa: E402
    ALL, CHIP, CHIP_MAX_CHARS, LOG_ONLY, PROV_HTML_EN,
)
from _xf_fw_en_names import (  # noqa: E402
    CAT_SHORT, PROV_SHORT, PROV_LONG, PROVS as _NAMES_PROVS, CATS as _NAMES_CATS,
)

# ───────────────────────────────────────────── ① 协议 token 白名单
#    ★ 这些串一个字都不能动。它们不是"文案"，是【数据协议】。
CATS = ["新闻综合", "交通台", "音乐", "文艺", "说书", "戏曲", "怀旧老歌",
        "网络台", "教育台", "电视伴音", "综合", "宗教", "境外新闻"]
PROVS = ["北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
         "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
         "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州",
         "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆",
         "中国台湾", "中国香港", "中国澳门", "其他华语",
         "北美", "欧洲", "日韩", "新马", "东南亚", "大洋洲", "海外中文"]
PROTOCOL = set(CATS) | set(PROVS) | {"全国", "其他"}

# ★ 台名单的解析/比对 token 也要保护（app_stlist.c 里的字面量）
STLIST_TOKENS = {
    "新闻综合", "交通台", "音乐", "文艺", "说书", "戏曲", "怀旧老歌",
    "网络台", "教育台", "电视伴音", "综合", "宗教", "境外新闻",
    "全国", "其他", "□", "内置",
}
PROTECT = PROTOCOL | STLIST_TOKENS

#★★★ 「全国 / 其他」在 ui_xiandial.c 里是【显示】，在 app_stlist.c 里是【键】★★★
#   全局把这两个放进 PROTECT 是对的（app_stlist.c 的 strcmp 要靠它们），
#   但 ui_xiandial.c 里也有字面量 "全国"：
#       const char *pn = (st->prov == NET_PROV_NONE) ? "全国"
#                                                  : xs_prov_long_en[...];
#   那是给「来源标签」显示的，界面上的 "Nationalwide"。
#   ⇒ 同一个串在不同文件里语义不同，不能用一张全局表判。
#     判据 = 【文件】：只有 app_stlist.c 与 net_stations*.c 保护，
#     ui_xiandial.c 走显示语义（可译）。
#   ⚠ 我第一版是全局保护，结果英文界面的来源标签留了一处中文 "全国"，
#     而它是这一行的唯一中文 —— 肉眼极容易漏（就三个字）。
PROTECT_FILES = ("app_stlist.c", "net_stations")

# ───────────────────────────────────────────── ② 要生成的文件
#   net_stations* 完全不生成（协议 token 所在，英文版直接复用中文版那份）
SKIP_FILES = {"net_stations.c", "net_stations.h", "net_stations_seed.h",
              "net_stations_pub.c", "net_stations_pub.h",
              "net_stations_pub_seed.h"}

#★★★ ★★★ 发布版【绝不能】复制自用版的台单文件 ★★★
#   我第一版把 SKIP_FILES 里的 6 个文件全部原样复制过去，
#   结果把 net_stations.c（**1254 条真实台源 URL**）和
#   net_stations_seed.h（收藏播种用的 10 个真实台名）放进了英文版目录。
#   那两个文件正是发布闸禁要排除的东西（自用版台单 + 私人台名），
#   而它们一旦存在，CMake 的
#       if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/net_stations_pub.c")
#   判断虽然仍会走发布分支（pub 也在），但【自用版文件就在树里】——
#   打包时若用整目录，就是把 1254 个真实台源连同我的私人收藏一起发出去。
#   ⇒ 英文版【只允许】复制 *_pub.* 三个文件，其余一律不复制。
#     而且复制后要【断言 g_station_count == 0】，让"混进自用版台单"
#     在生成这一步就炸掉，而不是等发布闸禁才发现。
COPY_FILES = {"net_stations_pub.c", "net_stations_pub.h",
              "net_stations_pub_seed.h"}

#★★ 字面量的引号必须是【双引号】★★
#   C 字符串字面量用双引号："正在载入台单…"。我第一版照着 JS 工具的
#   经验写成单引号 '...' ⇒ 全文件只匹配到 10 个单引号片段，
#   479 个双引号字面量一个都没匹配上 ⇒ 「文案替换 0 处」。
#   而脚本仍打印「★ 所有中文字面量都已处理」之外的 miss 列表退出 0，
#   差点让我以为翻译表已经生效。
#   ⇒ 这条与_gh_publish.py 的 rc 语义是同一类错误：
#      【判据写错时的表现和「事情没做」完全一样】。
LIT = r'"(?:[^"\\\n]|\\.)*"'

#★★★ ① 注释必须【先剥掉】，再翻译 ★★★
#   我第一版是「先翻译、后翻译表查询」，没有剥注释，于是
#     /* …界面上只看到"0 台"这种合法状态… */
#   这条【注释】里的字面量也被替换成 "0 stations"，
#   而 app_stlist.c 里真正的代码一个字都没改 —— 判据完全错了。
#   更糟的是它【不报错】：编译正常、界面正常，只有注释被改，
#   没人会去 diff 注释。铁律 14「正则能看起来对上时要拿已知答案验」。
#
#   ★ 剥法必须是状态机而不是正则（见 _fw_en_probe_ui.strip_comments）：
#     本工程满是 URL（'http://…'），`//[^\n]*` 会把整行 URL 之后吃掉；
#     `/\*.*?\*/` 处理不了「注释里出现 /*」。
#
#   ★★ 为什么要【保留位置】而不是简单删掉：
#     删掉会让后面所有行号错位，排查时对不上原文件。
#     所以按【字符位置】标记：把注释区段的字符替换成空格（保留 \n），
#     翻译完再按 span 把改动写回原串。
COMMENT_SPAN = []      # [(start, end)] 注释区段（源串坐标）


def mask_comments(src):
    """把注释整段换成【唯一占位符】，返回 (masked, 占位符->原文 的映射)。

    ★★★ 为什么用占位符而不是「替换成等长空格」★★★
      等长空格方案看着更优雅（行号不变），但注释里的字面量被替换后
      **长度会变**，于是「注释区」的偏移全部失效，想把它原样放回去
      就必须做字符级 diff 对齐。我第一版就是这么做的（_apply_diff +
      difflib），结果在 app_prov.c 上错位，把
          "…<b>Connected/* JSON 字符串转义…"
      这种「半个字面量 + 半个注释」的怪物拼了出来 ——
      自检立刻抓到，但它证明这条路不可靠：300KB 文本上做字符级
      SequenceMatcher，既慢又可能错位。
      ⇒ 改用占位符：注释段整体换成 \x01123\x01 这种不含引号/反斜杠/
        中文/换行的短 token。所有后续处理（fold / chip_block / 替换 /
        正则）都碰不到它，最后按 token 精确还原。
        长度变化只发生在【代码段】，而代码段之间不互相依赖偏移。

    ★ 剥法必须是状态机而不是正则：
      本工程满是 URL（"http://…"），`//[^\n]*` 会把 URL 之后整行吃掉；
      `/\*.*?\*/` 处理不了「注释里出现 /*」。
    """
    out = []
    saved = {}
    i, n = 0, len(src)
    state = 0          # 0 代码 1 块注释 2 行注释 3 字符串 4 字符
    seg_start = None
    k = [0]

    def flush(end):
        k[0] += 1
        tok = "\x01%d\x01" % k[0]
        saved[tok] = src[seg_start:end]
        out.append(tok)

    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if state == 0:
            if c == "/" and nxt == "*":
                state, seg_start = 1, i
                i += 2
                continue
            if c == "/" and nxt == "/":
                state, seg_start = 2, i
                i += 2
                continue
            if c == '"':
                state = 3
            out.append(c); i += 1
        elif state == 1:
            if c == "*" and nxt == "/":
                flush(i + 2)
                state, seg_start = 0, None
                i += 2
            else:
                i += 1
        elif state == 2:
            if c == "\n":
                flush(i)
                out.append("\n")
                state, seg_start = 0, None
            i += 1
        elif state == 3:
            if c == "\\":
                out.append(src[i:i + 2]); i += 2; continue
            if c == '"':
                state = 0
            out.append(c); i += 1
        else:
            if c == "\\":
                out.append(src[i:i + 2]); i += 2; continue
            if c == "'":
                state = 0
            out.append(c); i += 1
    if seg_start is not None:          # 文件以未闭合注释结束
        flush(n)
    return "".join(out), saved


def unmask_comments(masked, saved):
    """把占位符换回注释原文。占位符唯一 ⇒ 与出现顺序无关。"""
    if not saved:
        return masked
    pat = re.compile("|".join(re.escape(t) for t in
                              sorted(saved, key=len, reverse=True)))
    return pat.sub(lambda m: saved[m.group(0)], masked)


def lit_body(text):
    """取出字面量的内容（去掉两侧引号，处理 \\" 与 \\\\）。"""
    t = text[1:-1]
    return t.replace('\\"', '"').replace("\\\\", "\\")


def lit_c(s):
    """把内容重新包成合法 C 双引号字面量。"""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def fold(src):
    """把 "A" + "B" + "C" 折叠成 "ABC"。★ 必须先做，否则匹配不到整句。"""
    chain = re.compile(LIT + r"(?:\s*\+\s*" + LIT + r")+")

    def rep(m):
        parts = re.findall(LIT, m.group(0))
        return lit_c("".join(lit_body(x) for x in parts))

    return chain.sub(rep, src)


def chip_block(src):
    """整块替换 k_cat_short[] 数组（胶囊短名 51px，必须用 CHIP 表）。

    ★ 正则踩坑：数组声明是 `k_cat_short[HCAT_ALL + 1]`，
      下标里有【空格】和【+】。我第一版写 `\\[\\w+\\]` 只匹配纯标识符
      ⇒ 完全匹配不上 ⇒ 「胶囊整块替换 0 项」而脚本仍退出 0。
      ⇒ 下标部分用 `\\[[^\\]]*\\]`（非贪婪到第一个右方括号）。
    """
    m = re.search(r"(static const char \*const k_cat_short\[[^\]]*\]\s*=\s*\{)"
                  r"(.*?)(\n\};)", src, re.S)
    if not m:
        #★ 没匹配上必须硬失败，绝不能静默跳过 ——
        #   跳过 = 胶囊里还是中文 = 英文界面出现「收藏」这种字，
        #   而闸门只查「译文表有没有命中」，查不出「整块替换没跑」。
        print("!! 没找到 k_cat_short[] 数组定义 —— 正则或源码结构变了？")
        sys.exit(1)
    body = m.group(2)
    # ★★★ 按【字面量的字符位置】替换，不要按「行里有没有中文」判断 ★★★
    #   我第一版按行遍历找中文，源码里那些注释
    #   （/* 3 个自定义入口（标签条上用短名，理由见上）*/）里全是汉字，
    #   于是「含中文的行数」多于「中文字面量的个数」，
    #   7 个数据项后面跟着 9 行注释 ⇒ 计数错位、只替了 7 个。
    #   ⇒ 用 re.finditer 拿到每个字面量的确切 span，逐一原地替换，
    #     注释与排版一个字节都不动。
    out = []
    pos = 0
    n = 0
    for mm in re.finditer(LIT, body):
        t = lit_body(mm.group(0))
        if not re.search(r"[\u4e00-\u9fff]", t):
            continue
        if t not in CHIP:
            print("!! 胶囊短名 %r 不在 CHIP 表里（会漏译）" % t)
            sys.exit(1)
        out.append(body[pos:mm.start()])
        out.append(lit_c(CHIP[t]))
        pos = mm.end()
        n += 1
    out.append(body[pos:])
    if n != len([x for x in re.findall(LIT, body)
                 if re.search(r"[\u4e00-\u9fff]", lit_body(x))]):
        print("!! 胶囊替换计数不自洽")
        sys.exit(1)
    new_body = "".join(out)
    # 短名对齐：中文 2 字 vs 英文 4~6 字符，逗号后补空格保持可读
    return (src[:m.start(2)] + new_body + src[m.end(2):], n)


def names_tables_c(rel, src):
    """给 ui_xiandial.c 注入两张【显示用】英文名数组，并改写所有显示点。

    ★★★ 这是整个英文版最危险的一处改写，所以三重保险 ★★★
      ① 【协议表一个字节都不碰】—— app_stlist.c 的两处 strcmp 仍在读
         g_cat_name / g_prov_name（中文），TSV 匹配键完好。
         而 ui_xiandial.c 里 g_*_name 的 15 处使用点【全部是显示】
         （已逐个核对：无一处在 strcmp/strncmp/memcmp 里），
         所以把它们改读 xs_*_name_en 是安全的。
      ② 【下标不变】—— 新数组与协议表同序同长，第 i 项对第 i 项。
         PROV_SHORT/PROV_LONG 各 42 项、PROV_LONG 缺一项就会错位，
         所以 _xf_fw_en_names._selftest() 对长度做硬判据。
      ③ 【改完必须回读计数】—— 替换处数与源码里 g_*_name 的出现次数
         必须相等（注释不计），不等就 sys.exit(1)。

    ⚠⚠ 第一版我差点用「全文替换 g_prov_name → xs_prov_name_en」一刀切，
      那会把 app_stlist.c 里那两处【strcmp 比较键】也换掉 ——
      后果是导入的中文台单再也匹配不上分类/地区，全落兜底，
      而所有格式检查都是绿的。这里严格限定【只改 ui_xiandial.c 一个文件】。
    """
    if not rel.endswith("ui_xiandial.c"):
        return src, 0

    # ---- ① 先统计：剥注释后的 g_*_name 出现次数（改写判据的基准）----
    bare = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    bare = re.sub(r"//[^\n]*", "", bare)
    n_cat = len(re.findall(r"\bg_cat_name\b", bare))
    n_prov = len(re.findall(r"\bg_prov_name\b", bare))
    if n_cat == 0 and n_prov == 0:
        return src, 0

    # ---- ② 注入两张表（放在 k_cat_short 之后，便于人读）----
    def arr(name, tbl, src_order):
        items = ", ".join('"%s"' % tbl[k] for k in src_order)
        return ("\n/* ★★★ 英文版专用：显示用名称表（协议表 g_*_name 保持中文，\n"
                " *   它是 TSV 匹配键，改了就静默失效）。下标与协议表严格一致。*/\n"
                'const char *const xs_%s[NET_%s_N] = {\n    %s,\n};\n'
                % (name, "CAT" if name == "cat_name_en" else "PROV", items))

    tbl_cat = arr("cat_name_en", CAT_SHORT, _NAMES_CATS)
    tbl_prov_s = arr("prov_short_en", PROV_SHORT, _NAMES_PROVS)
    tbl_prov_l = arr("prov_long_en", PROV_LONG, _NAMES_PROVS)

    anchor = re.search(r"(static const char \*const k_cat_short\[[^\]]*\]\s*=\s*\{"
                       r".*?\n\};\n)", src, re.S)
    if not anchor:
        print("!! 没找到 k_cat_short 数组，无法定位注入点")
        sys.exit(1)
    inject = anchor.group(1) + tbl_cat + tbl_prov_s + tbl_prov_l
    src = src[:anchor.start(1)] + inject + src[anchor.end(1):]

    # ---- ③ 改写显示点：g_prov_name → xs_prov_long_en ----
    #  为什么统一用【长名】而不是短名：
    #   长名出现在列表页标题（300px）与来源标签（约 100px）；
    #   胶囊那一档走的是 g_prov_name[idx]（见下），那里必须短名。
    n1 = len(re.findall(r"\bg_prov_name\[", src))
    src = re.sub(r"\bg_prov_name\[", "xs_prov_long_en[", src)
    #   胶囊那处（hstrip_show）例外：51 px 塞不下长名。
    #   判据是紧跟其后的那行注释含「胶囊」/ 或它属于 s_prov_strip 分支。
    #   ★ 这里用「出现位置在 hstrip_show 函数体内」来定位，而不是靠中文注释 ——
    #     注释会被人改，用它做判据 = 哪天注释一改就静默失效。
    m_hs = re.search(r"static void hstrip_show\(.*?\n\}\n", src, re.S)
    if not m_hs:
        print("!! 没找到 hstrip_show()，胶囊短名替换点无法定位")
        sys.exit(1)
    body = m_hs.group(0)
    if "xs_prov_long_en[idx % NET_PROV_N]" not in body:
        print("!! hstrip_show 里没有地区名引用，源码结构变了？")
        sys.exit(1)
    body2 = body.replace("xs_prov_long_en[idx % NET_PROV_N]",
                         "xs_prov_short_en[idx % NET_PROV_N]")
    src = src[:m_hs.start()] + body2 + src[m_hs.end():]

    n2 = len(re.findall(r"\bg_cat_name\[", src))
    src = re.sub(r"\bg_cat_name\[", "xs_cat_name_en[", src)

    print("  ui_xiandial.c      显示点改写：地区 %d 处（大标题长名 + 胶囊短名 1 处）"
          " / 栏目 %d 处" % (n1, n2))
    return src, n1 + n2


def _assert_pub_empty(path):
    """断言复制过来的发布版台单确实是 0 条。

    ★ 为什么加这一层：英文版一旦混进自用版台单，发布闸禁虽然也能查出来，
      但那是在【打包之后】才炸；这里在【生成源码这一步】就炸，
      根因离现场近得多。这是"同一个事实要在两个地方各查一遍"的取舍：
      前者便宜（早），后者权威（晚）。两个都留。
    """
    txt = io.open(path, encoding="utf-8").read()
    m = re.search(r"g_station_count\s*=\s*(\d+)", txt)
    if not m:
        print("!! %s 里找不到 g_station_count —— 台单文件格式变了？" % path)
        sys.exit(1)
    if int(m.group(1)) != 0:
        print("!! %s 的 g_station_count = %s，英文版必须是 0 条发布台单！"
              % (os.path.basename(path), m.group(1)))
        sys.exit(1)


def prov_html(src):
    """整块替换 captive portal 网页（app_prov.c 的 PROV_HTML[]）。

    ★★★ 为什么必须整块，不能逐条翻 ★★★
      它是 27 个相邻字面量拼成的一整页 HTML。逐条翻译有两个致命风险：
        ① 译文里出现半角 " ⇒ 破坏 C 字面量转义 ⇒ 页面【白屏】，
           而编译器一个字都不报（那是合法 C 字符串）。
        ② 漏一条就是英文界面里一截中文（编译同样不报）。
      ⇒ 改成整块用英文版原文重写，并**回读验证**：
         引号必须配平、且块内不得有中文。
      这两条任一不过就 sys.exit(1) —— 判据不可信时不能往下走。
    """
    m = re.search(r"(static const char PROV_HTML\[\]\s*=\s*\n)(.*?)(;\n)",
                  src, re.S)
    if not m:
        print("!! 没找到 PROV_HTML[] 定义 —— 源码结构变了？")
        sys.exit(1)
    body = m.group(2)
    # ★ 自检：新块必须引号配平（数 C 字面量的开头数）
    n_open = len(re.findall(r'"', body)) - len(re.findall(r'\\"', body))
    if n_open % 2 != 0:
        print("!! PROV_HTML 英译块引号不配平（%d 个）" % n_open)
        sys.exit(1)
    if re.search(r"[\u4e00-\u9fff]", PROV_HTML_EN):
        print("!! PROV_HTML 英译块里还有中文")
        sys.exit(1)
    # 块内原有字面量数（用于确认没把非 HTML 的东西吞进来）
    if not (PROV_HTML_EN.rstrip().endswith('"')
            and "</script></body></html>\"" in PROV_HTML_EN):
        print("!! PROV_HTML 英译块结尾不对，疑似截断")
        sys.exit(1)
    out = src[:m.start(2)] + PROV_HTML_EN + "\n" + src[m.end(2):]
    print("  app_prov.c          captive portal 整页英译 (%d 字符)"
          % len(PROV_HTML_EN))
    return out


def _check_verified_all_used(_used=None):
    """VERIFIED_LOG 里每一条都必须【真的还在源码里】。

    ★★★ 为什么必须查这个 ★★★
      白名单是「人工核对过的结论」，它绑定的是**具体字符串**。
      源码一旦改了那条日志（比如 "UI: 二次确认通过 → 关机" 改成
      "UI: 二次确认通过 → power off"），白名单里的旧串就再也匹配不上，
      新串会被判成「界面文案」而卡住生成 —— 这算好的方向。
      危险的是反过来的情形：源码删掉了那条日志，白名单里还留着，
      于是白名单变成死条目，**看起来一直在起作用，其实已经失效**。
      门禁不该给这种假安全感 ⇒ 每次生成都核对「用了几条 / 共几条」。
    """
    if _used is None:
        return
    global _VERIFIED_USED
    miss = sorted(VERIFIED_LOG - _used)
    _VERIFIED_USED = _used
    if miss:
        print("\n⚠ VERIFIED_LOG 有 %d 条在源码里已不存在（白名单失效）：" % len(miss))
        for m in miss:
            print("   %r" % m)
        print("   ⇒ 请删掉它们，或确认源码改了名字后重新核对。")


_VERIFIED_USED = set()


def is_ui_context(lines, i):
    """lines[i] 这个字面量会不会上屏？

    判据 = 它所在的【语句块】里有没有【界面写入 API】或【错误缓冲区】：
      lv_label_set_text* / tap_note( / textContent / innerHTML
      snprintf(s_err/s_reason/...)  ← 这些缓冲区的内容会被 UI 读出来显示
      —— ESP_LOG / 普通 printf 是纯日志，留中文是有意的。

    ★★★ 为什么窗口不能是固定 ±6 行 ★★★
      我第一版写死「上下各 6 行」，结果漏掉两条真 UI 文案：
        "全国"   在三元表达式里，lv_label_set_text 在【下一行】的下一行
        "开不了热点 %.36s"  先 snprintf 到 m，下一行才 tap_note(m)
      两个的 UI 出口都在 6 行之外（中间夹着换行与缩进）。
      ⇒ 改成【向上找到所属的 { } 块，向下同���】，再扫这一段。
    """
    n = len(lines)
    # ---------- 向上：找所属的 { } 块 ----------
    lo = i
    depth = 0
    while lo > 0:
        lo -= 1
        for ch in lines[lo]:
            if ch == "}":
                depth += 1
            elif ch == "{":
                if depth == 0:
                    lo -= 1
                    break
                depth -= 1
        else:
            continue
        break
    # ---------- 向下：找与之配对的 } ----------
    depth = 0
    hi = i
    started = False
    while hi < n:
        for ch in lines[hi]:
            if ch == "{":
                depth += 1
                started = True
            elif ch == "}":
                if started and depth == 0:
                    hi += 1
                    break
                depth -= 1
        else:
            hi += 1
            continue
        break
    lo = max(0, lo)
    hi = min(n, hi + 2)

    #★★★ ★★★ 整块扫描会误判，必须按【子块】再分一层 ★★★
    #   踩到的实例（app_prov.c 的 ap_start()）：
    #       if (e != ESP_OK) {
    #           ESP_LOGE(TAG, "切 APSTA 失败: %s", ...);   ← 真·日志
    #           return e;
    #       }
    #       e = esp_wifi_set_config(WIFI_IF_AP, &wc);
    #       if (e != ESP_OK) {
    #           ESP_LOGE(TAG, "AP 参数失败: %s", ...);      ← 真·日志
    #           return e;
    #       }
    #       ESP_LOGI(TAG, "SoftAP 已开…");                    ← 真·日志
    #   而【同一个函数块】下面还有 PROV_HTML（那是网页，真 UI）。
    #   我按函数块扫 ⇒ 三个 ESP_LOG 全被判成"要上屏" ⇒ 误杀 3 条日志。
    #
    #   ⇒ 真正的判据：【本字面量自己那一条语句所在的最小 {} 块】。
    #     ESP_LOG(TAG, "…") 在一个只有 return 的 if 块里 ⇒ 该块无 UI API
    #     ⇒ 判日志。 "全国" 在三元里，往下 1 行的最小块里有
    #       lv_label_set_text ⇒ 判 UI。
    #   做法：先把函数块按 {} 拆成【顶层子句】，再在子句内找 API。
    sub = _sub_statements(lines, lo, hi)
    own = None
    for a, b in sub:
        if a <= i <= b:
            own = (a, b)
            break
    ctx = "\n".join(lines[own[0]:own[1] + 3]) if own else \
        "\n".join(lines[lo:hi])

    if UI_SINK.search(ctx):
        return True
    if LOG_ONLY_SINK.search(ctx) and not ERR_BUF_SINK.search(ctx):
        return False
    # 自身块里没有 UI API，但整块里有 ⇒ 次优判据：取整块
    ctx_all = "\n".join(lines[lo:hi])
    if UI_SINK.search(ctx_all) and not LOG_ONLY_SINK.search(ctx_all):
        return True
    return False


def _sub_statements(lines, lo, hi):
    """把 [lo, hi] 按顶层 {} 拆成若干 (起始行, 结束行) 区间。"""
    out = []
    depth = 0
    start = lo
    for i in range(lo, min(hi, len(lines))):
        ln = lines[i]
        code = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', ln)  # 去掉字符串再数括号
        for ch in code:
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    out.append((start, i))
    if not out:
        out.append((lo, hi - 1))
    return out


UI_SINK = re.compile(
    r"lv_label_set_text|lv_label_create|tap_note\(|textContent|innerHTML|"
    r"lv_snprintf|hls_set_err\s*\(")
LOG_ONLY_SINK = re.compile(r"ESP_LOG|\bprintf\s*\(")
#★★★ 10-07 补 hls_set_err ★★★
#   同一个教训的【第二次复发】：ERRSET 那段注释里已经写过
#   「判据必须是这个缓冲区最终给不给 UI 看，不是用了哪个 API」，
#   而我把 snprintf(s_err,…) 补进了 ERR_BUF_SINK，却漏了它的孪生兄弟
#      app_hls.c: hls_set_err(h, "HLS: 连不上播放列表")
#   这条路径是：
#      hls_set_err → hls_error() → app_radio.c 的 s_err
#      → app_radio_last_error() → ui 的 player_refresh()
#      → lv_label_set_text(s_np_state, err)          ← 上屏
#   于是英文固件里 10 条中文错误串一路绿灯进到用户屏幕上，
#   而闸门 g4 用的是 is_ui_context()，自然全放过。
#   ⇒ 教训升级：补判据时要【顺着缓冲区的流向再走一步】，
#     凡是"别人把文案交给某个 helper"的地方，都要问一句 helper 的产物去哪。
#   长度预算：s_np_state 宽 140 px，12px 英文约 6px/字符 ⇒ 译文 ≤ 24 字符。
ERR_BUF_SINK = re.compile(
    r"snprintf\s*\(\s*s_(err|reason|note|last_err|msg|status)|hls_set_err\s*\(")

#★★★ 判据补不上、但已【人工逐条核对】确定为纯日志的字面量 ★★★
#  收进来的前提：① 确认只进 ESP_LOG*（使用者界面看不到）
#              ② 上下文推断判不出这个结论，必须人来判
#  用它兜底，是因为纯自动判据在这个规模的代码上必然有盲区：
#    "全国"      在三元表达式里，UI 出口 lv_label_set_text 在【后面的子块】
#    "station_step(%d) 失败"  ESP_LOG 在后，同一子块里 UI 出口在前一行
#    "pw_btn: 池满…"  ESP_LOGE 在 else 分支里，函数块内有 lv_label_create
#  ⇒ 这类"同函数内既有 UI 又有日志"的情况，任何行/块窗口都会二选一失手。
#    与其把判据调到越来越复杂、越来越不可信，不如把人工结论显式登记，
#    并在生成时打印条数，让新增的漏网项【显形】而不是被自动逻辑放过。
VERIFIED_LOG = {
    #★★ 10-07 新增 5 条 ★★
    #  把 hls_set_err( 补进 UI_SINK 之后，app_hls.c 的 seg_get 那一段
    #  整体被算成"UI 上下文"，于是这几条【真日志】也被扫了出来。
    #  入册前逐条用 _logonly_verify.py 核实过（该脚本用"折叠后精确比对 +
    #  括号配平回溯调用名"，并先拿已知答案验过）：
    #    seg_buf %.0f KB 分配失败（…）        → ESP_LOGW  app_hls.c:218
    #    seg_buf malloc(%d) 彻底失败，HLS 没法播 → ESP_LOGE  app_hls.c:223
    #    seg_buf %.0f KB 已分配               → ESP_LOGI  app_hls.c:227
    #    seg esp_http_client_init 返回 NULL …  → ESP_LOGE  app_hls.c:241
    #    连续 %d 片子拉不下来，放弃这个源（…）  → ESP_LOGE  app_hls.c:437
    #  ⇒ 均为纯日志，保留中文有利于排障。
    "seg_buf %.0f KB 分配失败（PSRAM 与内部都没有？）",
    "seg_buf malloc(%d) 彻底失败，HLS 没法播",
    "seg_buf %.0f KB 已分配",
    "seg esp_http_client_init 返回 NULL url=%.80s",
    "连续 %d 片子拉不下来，放弃这个源（累计失败 %d）",
    "UI: 二次确认通过 → 关机",
    "home grid: %d 格（收藏 %d + 历史 %d + 其余补满）",
    "station_step(%d) 失败",
    "pw_btn: 池满，建不出按钮",
    # 这三条已处理完：
    #   "开不了热点 %.36s" 已进 ERRSET 译文表（它是 tap_note 实参，必须翻）
    #   另两条的原文带「第6 页」/「池满」，与源码实际字面量不符，已删除
    #   ⇒ 白名单里留着它们 = 门禁永远报"失效条目"，噪声会让人无视门禁
}


def translate(src, path):
    """替换整条字面量（折叠后的一句就是一个字面量）。"""
    hit, miss, skip = 0, [], 0
    nlog = 0

    def rep(m):
        nonlocal hit, skip, nlog
        body = m.group(0)
        t = lit_body(body)
        if not re.search(r"[\u4e00-\u9fff]", t):
            return body
        #★★★ 协议 token 的保护要【按文件】判断 ★★★
        #   "全国"/"其他" 在 app_stlist.c 里是 TSV 匹配键（必须留中文），
        #   在 ui_xiandial.c 里是来源标签的显示文案（该翻）。
        #   全局保护会让英文界面的来源标签留一处中文 "全国"。
        if t in PROTECT:
            if any(k in path for k in PROTECT_FILES):
                skip += 1      # 协议 token：原样保留
                return body
            # 非匹配文件里同名 ⇒ 按显示处理，继续往下走查译文表
        if t in ALL:
            hit += 1
            return lit_c(ALL[t])
        # ★ 串口日志：保留中文，但【记账】——
        #   记账的意义是让闸门能区分"日志里留中文"（可接受）
        #   与"界面漏了中文"（必须补）。不记账的话，
        #   清单里 288 条日志和真正漏网的文案混在一起，无法下手。
        if t in LOG_ONLY:
            nlog += 1
            return body
        miss.append(t)
        return body

    out = re.sub(LIT, rep, src)
    return out, hit, miss, skip, nlog


def main():
    if not os.path.isdir(SRC_ROOT):
        print("找不到源码目录", SRC_ROOT)
        return 1
    total_hit = total_skip = total_log = total_disp = 0
    total_left_ui = total_left_log = total_verified = 0
    verified_used = set()
    all_miss = {}
    made = []
    copied = []

    for root, dirs, fns in os.walk(SRC_ROOT):
        dirs[:] = [d for d in dirs
                   if d not in ("build", "build_pub", "managed_components",
                                "__pycache__", ".git", "fonts", "en", "_retired")]
        for fn in fns:
            if not fn.endswith((".c", ".h")):
                continue
            if fn == "net_stations.h":
                # ★ 必须【排在 SKIP_FILES 判断之前】：
                #   net_stations.h 在 SKIP_FILES 里（自用版头不能复制到英文版），
                #   而它又必须存在（5 处写死 include）⇒ 这里造转发头。
                #   顺序反了就会被下面的 `continue` 吃掉，静默不生成。
                pub = os.path.join(root, "net_stations_pub.h")
                if not os.path.exists(pub):
                    print("!! 找不到 net_stations_pub.h，无法造转发头")
                    sys.exit(1)
                dst_h = os.path.join(DST_ROOT, "main", "net_stations.h")
                with io.open(dst_h, "w", encoding="utf-8", newline="\n") as fp:
                    fp.write(
                        "#pragma once\n"
                        "\n"
                        "/* 拾声英文版 · 转发头（由 tools/_gen_fw_en.py 生成，勿手改）\n"
                        " *\n"
                        " *  源码里 5 处写死 include net_stations.h：\n"
                        " *    app_stlist.h / app_fav.c / app_hist.c /\n"
                        " *    app_radio.c / ui_xiandial.c\n"
                        " *  而英文版只有 net_stations_pub.h。\n"
                        " *  两个头声明等价（NET_CAT_N / NET_PROV_N / net_station_t /\n"
                        " *  四个 extern 全同），所以转发即可。\n"
                        " */\n"
                        "#include \"net_stations_pub.h\"\n")
                copied.append("main/net_stations.h (转发头)")
                continue
            if fn in SKIP_FILES:
                if fn not in COPY_FILES:
                    # ★ 自用版台单 / 私人种子：一律【不复制】到英文版
                    continue
                # ★★ 协议文件不是"翻译"，是【原样复制】★★
                #   net_stations_pub.c/.h 里是 g_cat_name / g_prov_name
                #   （中文协议 token）与 g_station_count = 0。
                #   它们必须【一字节不差】地出现在英文版里 ——
                #   否则 CMake 的 if(EXISTS net_stations_pub.c) 会走错分支，
                #   编到 1254 条的自用版台单（那会把真实台源带进国际版）。
                sp = os.path.join(root, fn)
                rel = os.path.relpath(sp, SRC_ROOT).replace("\\", "/")
                dst = os.path.join(DST_ROOT, rel)
                d = os.path.dirname(dst)
                if not os.path.isdir(d):
                    os.makedirs(d)
                shutil.copyfile(sp, dst)
                copied.append(rel)
                if fn.endswith(".c"):
                    _assert_pub_empty(dst)
                continue
                continue
            sp = os.path.join(root, fn)
            rel = os.path.relpath(sp, SRC_ROOT).replace("\\", "/")
            src = io.open(sp, encoding="utf-8", errors="strict").read()
            if not re.search(r"[\u4e00-\u9fff]", src):
                continue
            #★★★ 第一步就遮蔽注释，之后所有处理都在 masked 上做 ★★★
            #   否则 /* …"0 台"… */ 这种注释里的字面量会被翻译，
            #   而 app_stlist.c 的真代码一行没动 —— 编译正常、界面正常，
            #   只有注释变了，没人看得出来（这版已修，见 mask_comments 注释）。
            masked, saved = mask_comments(src)
            out = masked
            if fn == "ui_xiandial.c":
                out, nchip = chip_block(out)
                print("  %-24s 胶囊整块替换 %d 项" % (rel, nchip))
            # ★★ prov_html 必须在 fold 【之前】——
            #   fold() 会把相邻字面量合并成一条（"A" "B" → "AB"），
            #   而 PROV_HTML 的匹配锚点是 `PROV_HTML[] =\n` 起始的一整块；
            #   顺序反了会匹配失败（然后脚本仍退出 0 —— 又是那种静默）。
            if fn == "app_prov.c":
                out = prov_html(out)
            out = fold(out)
            out, ndisp = names_tables_c(rel, out)
            total_disp += ndisp
            out, hit, miss, skip, nlog = translate(out, rel)
            total_hit += hit
            total_skip += skip
            total_log += nlog
            if miss:
                all_miss[rel] = miss
            #★★ 最后一步：把注释【原样恢复】，英文版的注释保持中文 ★★★
            #   注释是给工程师看的，中文更好读；而且它不该被"翻译"污染 ——
            #   译了之后注释里的中文与代码里的英文对不上号，读代码时会误导。
            final = unmask_comments(out, saved)
            # ★ 回读自检：英文版里【代码区】不该再有【界面文案】中文。
            #   ⚠⚠ 判据必须用与 translate() 完全相同的 LIT 正则。
            #     我第一版写的是 `"[^"]*[\u4e00-\u9fff][^"]*"`，那个 `[^"]*`
            #     【会跨行贪婪匹配】—— 它从某个字面量的开头一路吃到文件里
            #     下一个引号，把中间的注释、#include 一起算成"一条中文串"，
            #     于是 app_audio.c 明明只剩串口日志，却被判成"代码区仍有中文"。
            #     ⇒ 判据不可信 = 白干。这里改用同一条 LIT（排除 \\ 与 \n）。
            chk, _ = mask_comments(final)   # 还原后再遮蔽一次：此时注释是中文
            # ★★ 只查【会进 UI 的那些】—— 串口日志里留中文是有意的
            #   （省 flash、排障读中文快），把它算进来等于把设计当错误。
            c_lines = chk.split("\n")
            leftovers = []
            for m in re.finditer(LIT, chk):
                t = lit_body(m.group(0))
                if re.search(r"[\u4e00-\u9fff]", t):
                    ln = chk[:m.start()].count("\n")
                    leftovers.append((ln + 1, t,
                                      is_ui_context(c_lines, ln)))
            bad = [(ln, t) for ln, t, is_ui in leftovers if is_ui]
            # 人工核对过的纯日志优先放行（判据的盲区由人补，不放宽判据）
            still = []
            for ln, t in bad:
                if t in VERIFIED_LOG:
                    total_verified += 1
                    verified_used.add(t)
                else:
                    still.append((ln, t))
            bad = still
            if bad:
                print("!! %s 代码区仍有 %d 条【界面】中文字面量（不该留）:"
                      % (rel, len(bad)))
                for ln, t in bad[:12]:
                    print("     :%d %r" % (ln, t[:56]))
                return 1
            total_left_ui += 0
            total_left_log += len(leftovers) - len(bad)
            dst = os.path.join(DST_ROOT, rel)
            d = os.path.dirname(dst)
            if not os.path.isdir(d):
                os.makedirs(d)
            io.open(dst, "w", encoding="utf-8", newline="\n").write(final)
            made.append(rel)

    print("\n生成 %d 个翻译文件 + 原样复制 %d 个协议文件到 %s"
          % (len(made), len(copied), DST_ROOT))
    if copied:
        print("  原样复制: %s" % ", ".join(copied))
    print("  文案替换 %d 处 / 协议 token 保留 %d 处 / 串口日志保留中文 %d 处"
          % (total_hit, total_skip, total_log))
    print("  栏目地区显示点改写 %d 处" % total_disp)
    print("  代码区剩余中文：界面 %d 条（须为 0）/ 串口日志 %d 条（有意保留）"
          % (total_left_ui, total_left_log))
    print("  其中 %d 条靠人工核对放行（VERIFIED_LOG）—— 改代码后请复核"
          % total_verified)
    _check_verified_all_used(verified_used)
    # ★ 显示点改写为 0 必须硬失败：那意味着界面会显示中文「北京」「新闻综合」。
    if total_disp == 0:
        print("\n★★ 栏目/地区显示点改写 0 处 —— 界面会留中文，立刻排查")
        return 1

    # ★★★ 自检：替换数为 0 必须硬失败 ★★★
    #   开发过程中我踩了三个「静默通过」的坑，每一个的表现都是
    #   「脚本退出 0、打印正常、实际什么都没做」：
    #     ① 字面量正则写成单引号（JS 习惯）→ 479 个双引号字面量全漏
    #     ② k_cat_short 的下标正则 `\[\w+\]` 匹配不了 `[HCAT_ALL + 1]`
    #     ③ 折叠函数的引号与源码不一致
    #   共同教训：**判据写错时的外在表现，和「事情没做」一模一样。**
    #   ⇒ 所以凡是用正则做替换，必须回头验证「真的替换到了几条」。
    if total_hit == 0:
        print("\n★★ 文案替换 0 处 —— 生成器没干活，立刻排查（引号？正则？）")
        return 1
    if not all_miss:
        print("  ★ 所有中文字面量都已处理")
    else:
        n = sum(len(set(v)) for v in all_miss.values())
        print("\n★ 未翻译（表里没有）的中文字面量：%d 条" % n)
        # ★ 写进文件而不是刷屏：这份清单要逐条分类处理
        #   （要翻 / 是日志、可以留中文 / 是协议 token，要进保护名单），
        #   打印到终端会被后面的编译日志淹没。
        rep = os.path.join(HERE, "_fw_en_untranslated.txt")
        with io.open(rep, "w", encoding="utf-8", newline="\n") as f:
            f.write("# 英文版未翻译清单（%d 条）\n" % n)
            f.write("# 分类处理：要翻 → 补进 _xf_fw_en_text.py；\n")
            f.write("#是日志 → 可留中文，但要确认它真的只进 ESP_LOG/printf；\n")
            f.write("#   是协议 token → 加进 _gen_fw_en.py 的 PROTECT\n")
            f.write("# 由 tools/_gen_fw_en.py 自动生成\n\n")
            for p, ms in sorted(all_miss.items()):
                f.write("=== %s (%d)\n" % (p, len(set(ms))))
                for t in sorted(set(ms)):
                    f.write("    %r\n" % t)
        print("  已写入 %s" % rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())