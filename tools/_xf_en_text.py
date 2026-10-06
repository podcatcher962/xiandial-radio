#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""XianForge 英文版 · 文案表（折叠后的完整可见文本）

★ 这份表怎么来的（别手改源码去凑）
  ① 先把源码里所有 'A' + 'B' 的字面量拼接【折叠】成一条长句
     —— 否则一句话被拆成两三段，任何单条匹配都对不上
  ② 再提取 >…< 之间的可见文本（标签边界明确 ⇒ 键是完整句子）
  ③ 排除协议 token（栏目/地区/城市名），它们一个都不能动
  ④ 结果就是下面这张表

★ 为什么用「折叠后的完整文本」而不是「中文片段」
  我试过片段级替换（把「台名」「共」「行」这种 2~3 字当键），
  它必然出事：这些字在【数据】里也出现 ——
    '示例新闻广播' 里的 '台' 被换成 'stations'
    '#   栏目与地区取值见' 里的 '栏目' 被换成 'Category'
  症状极隐蔽：界面正常，自检全绿，但导出的 stations.tsv 里
  【栏目字段被写成英文】⇒ 真机上全部落到兜底分类。
  ⇒ 键必须是「有标签边界、且不可能出现在数据里」的完整可见文本。
"""

# ═══════════════════════════ 转换页 / 自检页 / 规格表 / 顶栏 / 页签
PAGE = {
    # ── 顶栏与品牌
    "拾声 · 台源转换器": "XianDial &middot; Station List Builder",
    "拾声 · 台源转换器 v1.0": "XianDial &middot; Station List Builder v1.0",
    "© 永远的兰兰（Lanlan Eternal）": "&copy; Lanlan Eternal",
    "切换深浅主题": "Toggle light / dark",
    "切换中英文": "Switch language",

    # ── 页签
    "转换台源": "Convert",
    "格式自检": "Self-check",
    "使用方法": "How to use",
    "常见问题": "FAQ",
    "免责声明": "Disclaimer",
    "关于": "About",

    # ── ① 放入台单
    "① 放入台单": "1 &middot; Load your list",
    "把你下载的 M3U 或文本台单拖进来，或直接粘贴。":
        "Drop in an M3U or plain-text list you downloaded, or paste it.",
    "UTF-8 / GBK / UTF-16 会自动识别": "UTF-8 / GBK / UTF-16 are detected automatically",
    "，不用自己转码。": " &mdash; no manual transcoding.",
    "把 M3U / TXT 拖到这里": "Drop M3U / TXT here",
    "或点这一块选文件 · 也可以直接往下面粘贴":
        "or click to choose files &middot; or paste below",
    "或粘贴内容：": "Or paste the content:",
    "或者一行一个：": "or one per line:",
    "解析": "Parse",
    "载入示例台单": "Load sample list",
    "清空": "Clear",
    "当前：": "Current: ",
    "（识别为 ": " (detected as ",
    "还没有电台。上面放一个 M3U 进来，或点「载入示例台单」先看看效果。":
        "No stations yet. Drop an M3U above, or click &ldquo;Load sample list&rdquo; to see how it works.",

    # ── ② 解析结果
    "② 解析结果": "2 &middot; Parse result",
    "电台总数": "Total stations",
    "台名可用": "Usable names",
    "HLS 流": "HLS streams",
    "需修正": "Need fixing",
    "余量（上限": "Headroom (max ",
    "）": ")",
    "全表栏目改为：": "Set category for all rows:",
    "全表地区改为：": "Set region for all rows:",
    "（不改）": "(unchanged)",

    # ── ③ 逐条校对
    "③ 逐条校对": "3 &middot; Review row by row",
    "每行都能改。改动即时生效，改完直接导出就是最终文件。":
        "Every row is editable. Changes apply immediately &mdash; whatever you export is the final file.",
    "台名": "Name",
    "栏目": "Category",
    "地区": "Region",
    "标记": "Flags",
    "自动命名": "auto-named",
    "地址": "URL",
    "超长": "too long",
    "台名超长": "name too long",
    "⚠️ 只显示前 ": "&#9888;&#65039; Showing only the first ",
    " 行（共 ": " rows (of ",
    " 行）。全部 ": " in total). All ",
    " 行之后的内容仍会照常导出。":
        " rows and beyond are still exported normally.",
    "导出前去掉重复": "Remove duplicates before export",
    "空栏目按台名自动推断": "Infer an empty category from the station name",

    # ── ④ 导出
    "④ 导出": "4 &middot; Export",
    "文件名 ": "File name: ",
    "，存到 SD 卡": " &mdash; copy it to the ",
    "根目录": "root",
    "。已强制：UTF-8 无 BOM、LF 换行、TAB 分隔 —— 固件读这三样最挑。":
        ". Guaranteed: UTF-8 without BOM, LF line endings, TAB separators &mdash; the three things the firmware is pickiest about.",
    "下载 ": "Download ",
    "复制到剪贴板": "Copy to clipboard",
    "复制全文": "Copy all",
    "下载格式示例": "Download the example file",
    "下载示例文件": "Download the example file",
    "（点上面任一按钮生成预览）":
        "(click either button above to generate a preview)",
    "共 ": "Total ",
    " 行 · ": " rows &middot; ",
    " 字节": " bytes",
    " 台": " stations",
    "「下载 stations.tsv」": "&ldquo;Download stations.tsv&rdquo;",

    # ── 自检页
    "按《拾声台源文件格式规格 v1》逐条核对。":
        "Checked line by line against the Station File Format Spec v1.",
    "「硬性」不通过就导不出能用的文件。":
        "A failing <b>hard</b> check means the exported file will not work.",
    "还没有电台可检。先去「转换台源」解析一个台单。":
        "Nothing to check yet. Go to Convert and parse a list first.",
    "规格速查": "Specification at a glance",
    "路径": "Path",
    "编码": "Encoding",
    "换行": "Line endings",
    "分隔": "Separator",
    "列序": "Column order",
    "上限": "Limit",
    "台名上限": "Max name length",
    "URL 上限": "Max URL length",
    "注释": "Comments",
    "（根目录）": " (card root)",
    "（UTF-8）": " (UTF-8)",
    "TAB，一个": "TAB, exactly one",
    "台名 · 栏目 · 地区 · URL": "Name &middot; Category &middot; Region &middot; URL",
    " 开头整行跳过；空行跳过":
        " are skipped entirely; blank lines are skipped",
    "以 ": "Lines starting with ",
    "13 个标准名，对不上归「综合」":
        "13 standard values; anything else falls back to the default",
    "42 个标准名，或「全国」「其他」→ 无归属":
        "42 standard values, or the nationwide/other markers &rarr; no specific region",

    # ── 导出注释头
    "# 拾声台源stations.tsv  共 ": "# XianDial stations.tsv &mdash; ",
    "# 拾声台源文件格式示例  stations.example.tsv":
        "# XianDial station file format example  stations.example.tsv",
    "# 每一行一个电台，四个字段用【制表符 Tab】分隔，顺序固定：":
        "# One station per line. Four fields separated by TAB, in this exact order:",
    "#   台名<TAB>栏目<TAB>地区<TAB>播放地址URL":
        "#   Name<TAB>Category<TAB>Region<TAB>StreamURL",
    "# 硬性要求：": "# Hard requirements:",
    "#   · 编码 UTF-8 【无 BOM】（带 BOM 会让第一个台名多一个方块）":
        "#   - Encoding: UTF-8, NO BOM (a BOM puts a stray box glyph in front of the first name)",
    "#   · 换行 LF（不要 CRLF，会让 URL 尾部挂个看不见的 CR 字符）":
        "#   - Line endings: LF (CRLF leaves an invisible CR at the end of every URL)",
    "#   · 字段之间必须是 Tab，不是空格":
        "#   - Separator must be TAB, not spaces",
    "#   · 最多 2000 台": "#   - Maximum 2000 stations",
    "#   · # 开头的行是注释，会被忽略":
        "#   - Lines starting with # are comments and are ignored",
    "# 放到 TF 卡【根目录】，文件名必须是 stations.tsv，插卡开机即自动读取。":
        "# Copy to the ROOT of the TF card as stations.tsv. Insert the card and power on.",
    "# 没有卡 / 文件读不出 / 格式不对，机器都不会白屏，只是保持 0 台。":
        "# No card, unreadable file or a bad format never blanks the screen &mdash; the device just stays at 0 stations.",
    "# ★ 下面的地址是【占位示例】，播不出声音。请换成你自己 M3U 里的真实地址。":
        "# * The URLs below are PLACEHOLDERS and will not play. Replace them with real URLs from your own M3U.",
    "#   栏目与地区取值见 README：栏目 13 种、地区 42 种（留空即全国台）。":
        "#   Category and region values are listed in the README: 13 categories, 42 regions (empty = nationwide).",
    "# ── 新闻综合 ──": "# -- News and talk --",
    "# ── 交通台 ──": "# -- Traffic --",
    "# ── 音乐 ──": "# -- Music --",
    "# ── HLS 直播（m3u8）也可以 ──": "# -- HLS live (m3u8) works too --",
    "# ── 地区可留空（= 全国台），栏目按最接近的填 ──":
        "# -- Region may be left empty (= nationwide); pick the closest category --",

    # ── 剪贴板 / 提示
    "已复制到剪贴板。": "Copied to clipboard.",
    "粘贴到记事本另存为 UTF-8 时，":
        " When pasting into Notepad and saving as UTF-8, ",
    "记得选「无 BOM」，换行选 LF，否则固件读不了。":
        " choose <b>no BOM</b> and <b>LF</b> line endings &mdash; otherwise the firmware cannot read the file.",
    "复制失败，请改用「下载」按钮。":
        "Copy failed. Please use the &ldquo;Download&rdquo; button instead.",
    "内容是空的。": "The content is empty.",
    "没解析出任何电台。": "No stations parsed.",
    "请确认内容里有 http:// 或 https:// 开头的地址。":
        "Please make sure the content contains addresses starting with http:// or https://.",

    # ── ★ 跨标签的句子（前半已在 </b> / </code> 之后，没有前导 >）
    #    这些必须整句替换，拆不动。
    "，存到 SD 卡": " &mdash; copy it to the ",
    "根目录": "root",
    "。已强制：UTF-8 无 BOM、LF 换行、TAB 分隔 —— 固件读这三样最挑。":
        ". Guaranteed: UTF-8 without BOM, LF line endings, TAB separators &mdash; the three things the firmware is pickiest about.",
    " —— 这两样是固件最容易读错的地方。":
        " &mdash; these are the two things the firmware most often misreads.",
    "，超过固件上限 ": ", over the firmware limit of ",
    "13 个标准名，对不上归「综合」":
        "13 standard values; anything else falls back to the default",
    "42 个标准名，或「全国」「其他」→ 无归属":
        "42 standard values, or the nationwide/other markers &rarr; no specific region",
    "UTF-8 / GBK / UTF-16 自动识别。":
        "Automatic UTF-8 / GBK / UTF-16 detection.",
    "UTF-8 无 BOM + LF 换行": "UTF-8 without BOM + LF line endings",
    "强制导出 ": "Always exports ",
    "无 BOM": "no BOM",
    "不能是 CRLF": "must not be CRLF",
    "换行必须是 LF": "Line endings must be LF",
    "文件不能有 BOM": "The file must not have a BOM",
    "台单仓库": "station-list repositories",
    "行。": " rows.",
    " 台": " stations",
    " 条。": ".",
    " 或 ": " or ",
    " 或 ": " or ",
    " 和": " and ",
    " → 找": " &rarr; find ",
    " 拷到 SD 卡": " copy it to the SD card",
    # 顶栏按钮（title 属性里，靠 lit_safe 那一路）
    "切换深浅主题": "Toggle light / dark",
    "切换中英文": "Switch language",
    "◐ 主题": "◐ Theme",
}