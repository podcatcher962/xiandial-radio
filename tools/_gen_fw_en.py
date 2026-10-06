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
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.abspath(os.path.join(HERE, ".."))
DST_ROOT = os.path.join(SRC_ROOT, "en")

sys.path.insert(0, HERE)
from _xf_fw_en_text import ALL, CHIP, CHIP_MAX_CHARS  # noqa: E402

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

# ───────────────────────────────────────────── ② 要生成的文件
#   net_stations* 完全不生成（协议 token 所在，英文版直接复用中文版那份）
SKIP_FILES = {"net_stations.c", "net_stations.h", "net_stations_seed.h",
              "net_stations_pub.c", "net_stations_pub.h",
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
    # 取出原有的中文字面量，按顺序查 CHIP
    lits = re.findall(LIT, body)
    seq = []
    for lit in lits:
        t = lit_body(lit)
        if re.search(r"[\u4e00-\u9fff]", t):
            if t not in CHIP:
                print("!! 胶囊短名 %r 不在 CHIP 表里（会漏译）" % t)
                sys.exit(1)
            seq.append(lit_c(CHIP[t]))
        else:
            seq.append(lit)
    # 保留原来的排版：每行一项 + 原注释
    lines = body.split("\n")
    out, k = [], 0
    for ln in lines:
        m2 = re.search(r"^(\s*)(.*?)(\s*/\*.*?\*/)?\s*$", ln)
        if "/*" in ln and not seq[k:k + 1]:
            out.append(ln)
            continue
        if re.search(r"[\u4e00-\u9fff]", ln):
            indent = " " * (len(ln) - len(ln.lstrip()))
            comment = ""
            mc = re.search(r"(/\*.*\*/)\s*$", ln)
            if mc:
                comment = "  " + mc.group(1)
            out.append("%s%s,%s" % (indent, seq[k], comment))
            k += 1
        else:
            out.append(ln)
    if k != len(seq):
        print("!! k_cat_short 项数不匹配：替换 %d / 表 %d" % (k, len(seq)))
        sys.exit(1)
    return src[:m.start(2)] + "\n".join(out) + src[m.end(2):], k


def translate(src, path):
    """替换整条字面量（折叠后的一句就是一个字面量）。"""
    hit, miss, skip = 0, [], 0

    def rep(m):
        nonlocal hit, skip
        body = m.group(0)
        t = lit_body(body)
        if not re.search(r"[\u4e00-\u9fff]", t):
            return body
        if t in PROTECT:
            skip += 1          # 协议 token：原样保留
            return body
        if t in ALL:
            hit += 1
            return lit_c(ALL[t])
        miss.append(t)
        return body

    out = re.sub(LIT, rep, src)
    return out, hit, miss, skip


def main():
    if not os.path.isdir(SRC_ROOT):
        print("找不到源码目录", SRC_ROOT)
        return 1
    total_hit = total_skip = 0
    all_miss = {}
    made = []

    for root, dirs, fns in os.walk(SRC_ROOT):
        dirs[:] = [d for d in dirs
                   if d not in ("build", "build_pub", "managed_components",
                                "__pycache__", ".git", "fonts", "en", "_retired")]
        for fn in fns:
            if not fn.endswith((".c", ".h")):
                continue
            if fn in SKIP_FILES:
                continue
            sp = os.path.join(root, fn)
            rel = os.path.relpath(sp, SRC_ROOT).replace("\\", "/")
            src = io.open(sp, encoding="utf-8", errors="strict").read()
            if not re.search(r"[\u4e00-\u9fff]", src):
                continue
            out = src
            if fn == "ui_xiandial.c":
                out, nchip = chip_block(out)
                print("  %-24s 胶囊整块替换 %d 项" % (rel, nchip))
            out = fold(out)
            out, hit, miss, skip = translate(out, rel)
            total_hit += hit
            total_skip += skip
            if miss:
                all_miss[rel] = miss
            dst = os.path.join(DST_ROOT, rel)
            d = os.path.dirname(dst)
            if not os.path.isdir(d):
                os.makedirs(d)
            io.open(dst, "w", encoding="utf-8", newline="\n").write(out)
            made.append(rel)

    print("\n生成 %d 个文件到 %s" % (len(made), DST_ROOT))
    print("  文案替换 %d 处 / 协议 token 保留 %d 处" % (total_hit, total_skip))

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