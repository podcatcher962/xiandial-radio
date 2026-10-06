#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""列出 XianForge.en.html 里仍为中文的可见文本（诊断用）

★ 为什么单独一个脚本
  替换表会随文案改动而失效。与其每次人工翻 HTML，不如让脚本
  按【折叠后 + 标签边界】的视角列出全部残留中文 ——
  这正是"人眼在页面上看到的那句话"。

用法：
  python _xf_en_residual.py            # 查英文版
  python _xf_en_residual.py XianForge.html   # 查中文版（应全是中文）
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIT = r"'(?:[^'\\\n]|\\.)*'"
CAT = ['新闻综合', '交通台', '音乐', '文艺', '说书', '戏曲', '怀旧老歌',
       '网络台', '教育台', '电视伴音', '综合', '宗教', '境外新闻']


def fold(src):
    chain = re.compile(LIT + r"(?:\s*\+\s*" + LIT + r")+")
    return chain.sub(
        lambda m: "'" + "".join(x[1:-1] for x in re.findall(LIT, m.group(0)))
        + "'", src)


def main():
    f = sys.argv[1] if len(sys.argv) > 1 else "XianForge.en.html"
    p = os.path.join(HERE, f)
    raw = io.open(p, encoding="utf-8").read()
    js = fold(raw[raw.find("<script"):])

    cities = set()
    for name in ("PROVS_CN", "PROVS_XW"):
        m = re.search(r"var\s+%s\s*=\s*\[([^\]]*)\]" % name, raw)
        if m:
            cities |= set(re.findall(r"'([^']*)'", m.group(1)))

    seen, left = set(), []
    for m in re.finditer(r">([^<>{}]{1,220})<", js):
        t = m.group(1)
        if not re.search(r"[\u4e00-\u9fff]", t) or t in seen:
            continue
        seen.add(t)
        if t in CAT or t in cities or re.fullmatch(r"[\u4e00-\u9fff]{1,3}", t):
            continue
        left.append(t)

    print("%s：残留中文可见文本 %d 条" % (f, len(left)))
    for t in sorted(left):
        print("   ", repr(t[:100]))
    return 0


if __name__ == "__main__":
    sys.exit(main())