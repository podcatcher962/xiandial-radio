#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 XianForge.en.html（英文版台源转换器）

★ 为什么要生成而不是手工维护一份
  两份 HTML 手改必然分叉。而它们【必须严格一致】——
  一致性不只是文案，还包括 13 个栏目名 + 43 个地区名 + 城市匹配表：
  那些是【固件按中文字面量匹配的协议 token】，翻成英文就会导致
  「导入成功但全部落到兜底分类」，而界面和自检都看不出异常。
  ⇒ 一律从中文版生成，协议 token 由 protect/restore 强制原样保留。

★ 三道不可省的门
  1 token 保护   —— 栏目/地区/城市名换成占位符，替换完原样还原
  2 语法闸门     —— 译文会被塞进单引号字符串，英文所有格（firmware's）
                  的裸撇号会让整个 script 段 SyntaxError ⇒ 工具双击白屏，
                  而生成脚本一路绿灯。实测踩过 ⇒ 必须 node --check
  3 残留清单     —— 打印所有仍是中文的可见文本，人工逐条确认是有意保留

★ 折叠字面量拼接（关键一步）
  源码里一句话常被拆成 '前半' + '后半'。不折叠的话，
  「完整句子」这个概念根本不存在，表里写什么都不可能命中。
  实测：不做折叠只替换了 55 条；折叠后能按整句匹配。
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _xf_en_text import PAGE                      # noqa: E402

SRC = os.path.join(HERE, "XianForge.html")
DST = os.path.join(HERE, "XianForge.en.html")
# ★ 不硬编码本机路径与用户名 —— 发布闸门 _release_gitscan 会把
#   "C:\Users\<name>\..." 判成隐私泄漏（而且那本来就不该进仓库）。
#   需要指定 node 时设环境变量 XF_NODE，否则用 PATH 里的 node。
NODE = os.environ.get("XF_NODE", "node")

# ══════════════════════════════ 协议 token（一个字节都不能改）
CAT_TOKENS = ['新闻综合', '交通台', '音乐', '文艺', '说书', '戏曲',
              '怀旧老歌', '网络台', '教育台', '电视伴音', '综合',
              '宗教', '境外新闻']

PROV_TOKENS = ['全国', '其他', '北京', '天津', '河北', '山西', '内蒙古',
               '辽宁', '吉林', '黑龙江', '上海', '江苏', '浙江', '安徽',
               '福建', '江西', '山东', '河南', '湖北', '湖南', '广东',
               '广西', '海南', '重庆', '四川', '贵州', '云南', '西藏',
               '陕西', '甘肃', '青海', '宁夏', '新疆', '中国台湾',
               '中国香港', '中国澳门', '其他华语', '北美', '欧洲', '日韩',
               '新马', '东南亚', '大洋洲', '海外中文']

LIT = r"'(?:[^'\\\n]|\\.)*'"


def protect(src):
    table = {}
    for i, tok in enumerate(sorted(set(CAT_TOKENS + PROV_TOKENS),
                                  key=len, reverse=True)):
        ph = "\x01T%03d\x01" % i
        if ph in src:
            continue
        table[ph] = tok
        src = src.replace(tok, ph)
    return src, table


def restore(src, table):
    for ph, tok in table.items():
        src = src.replace(ph, tok)
    return src


def fold(src):
    """把 'A' + 'B' 折叠成 'ABC'。"""
    chain = re.compile(LIT + r"(?:\s*\+\s*" + LIT + r")+")
    return chain.sub(
        lambda m: "'" + "".join(x[1:-1] for x in re.findall(LIT, m.group(0)))
        + "'", src)


def main():
    if not os.path.exists(SRC):
        print("找不到 XianForge.html")
        return 1
    raw = io.open(SRC, encoding="utf-8").read()

    # ---- ★ 顺序很关键：先做「含 token 的整句替换」，再做 token 保护
    #  为什么：像「13 个标准名，对不上归「综合」」这种句子，
    #  它【本身含协议 token】（综合 / 全国 / 其他）。
    #  如果先 protect成占位符，键就再也匹配不上了
    #  ——我第一版就是这个顺序，那两条规格表说明怎么都翻译不了。
    #  这里反过来：能整句替换的先替掉，剩下的中文由 token 保护兜住。
    src = fold(raw)
    pre = 0
    pre_keys = set()
    for k in sorted(PAGE, key=len, reverse=True):
        if k in src:
            pre += src.count(k)
            pre_keys.add(k)
            src = src.replace(k, PAGE[k])

    src, table = protect(src)

    # ══════════════════════════════════════════════════════════
    # ★★★ 替换策略：只替换【> 与 < 之间的可见文本】
    #
    #  为什么不能用 str.replace 全局替换（我前两版都栽在这）：
    #    全局替换不区分「标签之间的文案」与「属性/数据里的同一个字」。
    #    实测事故（全都发生在同一版里）：
    #      '上限'  → 'Limit'    ⇒ '不超过固件上限' 变成 '不超过固件Limit'
    #      '换行'  → 'Line endings' ⇒ 'UTF-8 无 BOM + LF 换行' 变成
    #                                       'UTF-8 无 BOM + LF Line endings'
    #      '编码'/'自动识别' 同理
    #    这些字在正文里到处都是，全局替换必然误伤。
    #
    #  ⇒ 只有「>文案<」这种带标签边界的才是真文案。
    #    属性值（id="btnParse"）、数据（示例台单里的中文台名）都不带这个边界，
    #    天然被排除在外。
    # ══════════════════════════════════════════════════════════
    stats = {"hit": 0, "keys": set()}

    def vis_repl(m):
        t = m.group(1)
        if t in PAGE:
            stats["hit"] += 1
            stats["keys"].add(t)
            return ">" + PAGE[t] + "<"
        return m.group(0)

    out = re.sub(r">([^<>{}]{1,200})<", vis_repl, src)

    # 少数文案在标签【外面】（例如 '</b>，存到 SD 卡<b>根目录</b>。已强制…</p>'
    # 里 '。已强制…' 在 </p> 之前没有前导 >）。这些用「独占一行整句」处理。
    def line_repl(text):
        for k, v in PAGE.items():
            # 只在【整条字面量恰好等于该句】时替换，避免误伤
            pat = re.compile(r"(?<![一-鿿])" + re.escape(k) + r"(?![一-鿿])")
            text, n = pat.subn(lambda _m: v.replace("\\", "\\\\"), text)
            if n:
                stats["hit"] += n
                stats["keys"].add(k)
        return text

    # 对「纯字面量内容」做边界安全的替换（前后不得紧邻汉字）
    def lit_safe(m):
        body = m.group(0)[1:-1]
        new = line_repl(body)
        return "'" + new + "'" if new != body else m.group(0)

    out = re.sub(LIT, lit_safe, out)

    # token 还原
    out = restore(out, table)

    stats["pre"] = pre

    # 语言标记
    out = out.replace('<html lang="zh-CN" data-theme="dark">',
                      '<html lang="en" data-theme="dark">')
    out = out.replace("<title>拾声 · 台源转换器</title>",
                      "<title>XianDial · Station List Builder</title>")
    out = re.sub(r"(S\.lang\s*=\s*)'zh'", r"\1'en'", out)
    out = out.replace(
        "(S.lang==='zh'?'© 永远的兰兰（Lanlan Eternal）':'© Lanlan Eternal (永远的兰兰)')",
        "'&copy; Lanlan Eternal'")
    out = out.replace("'XianForge　台单 → stations.tsv'",
                      "'XianForge　list &rarr; stations.tsv'")
    out = out.replace("'#EXTM3U&#10;#EXTINF:-1,示例新闻广播",
                      "'#EXTM3U&#10;#EXTINF:-1,Example News")

    io.open(DST, "w", encoding="utf-8", newline="\n").write(out)

    miss_keys = [k for k in PAGE if k not in pre_keys]
    print("已生成 %s（%d 字节）" % (DST, len(out.encode("utf-8"))))
    print("  整句替换 %d 处，命中 %d / %d 条文案"
          % (pre, len(pre_keys), len(PAGE)))
    print("  协议 token 保护 %d 个" % len(table))
    if miss_keys:
        print("  ★ 表里 %d 条未命中（键与源码不符，需更新 _xf_en_text.py）："
              % len(miss_keys))
        for k in miss_keys[:10]:
            print("     ", repr(k[:60]))

    # ---- 语法闸门
    node = NODE if os.path.exists(NODE) else "node"
    js = re.search(r"<script[^>]*>([\s\S]*?)</script>", out)
    if not js:
        print("★ 找不到 <script>")
        return 1
    tmp = os.path.join(HERE, "_xf_en_syntax_tmp.js")
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(js.group(1))
    p = subprocess.run([node, "--check", tmp], capture_output=True,
                       text=True, errors="replace")
    try:
        os.remove(tmp)
    except OSError:
        pass
    if p.returncode != 0:
        print("★ JS 语法错误：")
        print((p.stderr or "").strip()[:600])
        return 1
    print("  JS 语法自检：通过")

    # ---- 残留清单（折叠后的视角，才能看到完整句子）
    f = fold(out)
    cities = set()
    for name in ("PROVS_CN", "PROVS_XW"):
        m = re.search(r"var\s+%s\s*=\s*\[([^\]]*)\]" % name, raw)
        if m:
            cities |= set(re.findall(r"'([^']*)'", m.group(1)))
    seen = set()
    left = []
    for m in re.finditer(r">([^<>{}]{1,160})<", f):
        t = m.group(1)
        if not re.search(r"[\u4e00-\u9fff]", t):
            continue
        if t in seen:
            continue
        seen.add(t)
        if t in CAT_TOKENS or t in PROV_TOKENS or t in cities:
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]{1,3}", t):     # 单字/双字 token
            continue
        left.append(t)
    if left:
        print("\n界面仍为中文的可见文本 %d 条（需人工确认）：" % len(left))
        for t in sorted(left):
            print("   ", repr(t[:88]))
    else:
        print("  界面残留中文：0")
    return 0


if __name__ == "__main__":
    sys.exit(main())