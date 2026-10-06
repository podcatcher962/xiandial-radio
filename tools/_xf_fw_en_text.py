# -*- coding: utf-8 -*-
"""英文版 UI 文案翻译表（拾声 XianDial · 发布版）

★★★ 这个表是英文版固件里【唯一】的真源。英文版源码由
   _gen_ui_en.py 从中文版生成，翻译只在这里改。

=========================== 铁律三条 ===========================

① ★★★ 协议 token 一个字都不能翻 ★★★
   栏目 13 个（g_cat_name）+ 地区 42 个（g_prov_name）+ 全国/其他
   —— 它们是 TSV 第 2、3 列的**匹配键**：
        app_stlist.c  strcmp(TSV第2列, g_cat_name[i])  ⇒ 下标
   翻成"News"之后，导入不报错、四列都合法、界面正常，
   只有分类/地区全落兜底 —— 而所有格式检查都绿。
   ⇒ 表里【没有】它们，生成器也不许碰它们。

② ★★ 英文比中文长，UI 有固定宽度 ★★
   这不是翻译，是【排版预算】。中文 2 字 = 24 px，
   英文 "Favorites" 9 字符 = 54 px，差 2.25 倍。
   已知的窄容器：
     - hstrip 胶囊 51 px（6 个/屏）  ⇒ 标签条最多 3~4 字符
     - hstrip 胶囊 57 px（全屏页）  ⇒ 同上
     - 首页大卡片 152 px             ⇒ 最多 10~11 字符
   ⇒ 表里的译文我按「该串会被画进多宽的容器」压缩过，
     不是按英文习惯的完整词。反例：收藏 → "Fav"（不是 Favorites）。

③ ★ 日志串不用翻 ★
   ESP_LOG* / printf 的中文串使用者看不到（只在串口监视器里）。
   翻了它们= 纯浪费 flash，而且万一日志里有中文，
   闸门会误报。生成器按「是否进 lv_label_set_text」区分。

④ ★★★ 同一个中文词可能有两个合法译文（按容器宽度分）★★★
   最典型的是「历史」：
     - 标签条胶囊 51 px  ⇒只能 "Hist"（4 字符）
     - 页面大标题 300 px ⇒ 可以 "History"（7 字符）
   这不是翻译表能表达的 —— 它是【上下文】。
   ⇒ 本文件把译文分成两级：
       CHIP —— 胶囊短名表，由生成器【整块替换 k_cat_short 数组】用
       ALL  —— 其余全部文案，按「完整字面量精确匹配」用
     两张表互不干扰，同一个中文词可以各有一份译文。
"""

# ═════════════════════════════════════════════ ① 胶囊短名（CHIP）
#    ★ 这一张表【不进ALL】，它是整块替换 k_cat_short[] 用的。
#      容器只有 51 px（6 个/屏），留给英文的宽度 ≈ 4 个字符。
#      顺序必须与 ui_xiandial.c 的 k_cat_short[] 完全一致（13+1 项）。
CHIP = {
    # 0,1,2三个自定义入口
    "收藏": "Fav",
    "历史": "Hist",
    "卡内": "SD",
    # 3..14 —— 12 个栏目短名（顺序与 g_cat_name 一致）
    "新闻": "News",
    "交通": "Traf",
    "音乐": "Mus",
    "文艺": "Arts",
    "说书": "Tell",
    "戏曲": "Oper",
    "怀旧": "Oldi",
    "网络": "Net",
    "教育": "Edu",
    "伴音": "TV",
    "宗教": "Reli",
    "境外": "Intl",
    # 15 —— 全部
    "全部": "All",
}
#  胶囊宽度硬判据（Ark Pixel 12px 约 6 px/字符 + 左右内边距各 4 px）
CHIP_MAX_CHARS = 5

# ═════════════════════════════════════════════ ② 常规文案（ALL）
UI = {
    # ---- 底部导航 5 项
    "首页": "Home",
    "发现": "Browse",
    "播放": "Playing",
    "夜间": "Night",
    "状态": "Status",

    # ---- 完整栏目名 / 地区名（进全屏页，容器宽，可长一点）
    "新闻综合": "News & Talk",
    "交通台": "Traffic",
    "怀旧老歌": "Oldies",
    "网络台": "Online",
    "教育台": "Education",
    "电视伴音": "TV Audio",
    "境外新闻": "Intl News",
    "其他华语": "Other Chinese",
    "海外中文": "Chinese Intl",

    # ---- 首页问候（4 张卡片，宽152 px）
    "夜深了 · 听点什么": "Late night?",
    "早上好 · 今天从声音开始": "Good morning",
    "上午好 · 慢一点": "Good morning",
    "中午好 · 歇一会儿": "Good noon",
    "下午好 · 来电台吧": "Good afternoon",
    "晚上好 · 夜里还长": "Good evening",
    "点一下立即进入": "Tap to start",
    "更靠中间": "Closer to middle",

    # ---- 品牌
    "拾声": "XianDial",
    "© 永远的兰兰": "© Lanlan Eternal",
}

# ───────────────────────────────────────────── ② 播放页 / 播放控制
PLAY = {
    "正在播放": "Now Playing",
    "播放中": "Playing",
    "已暂停": "Paused",
    "‖ 已暂停": "|| Paused",
    "暂停": "Pause",
    "继续": "Resume",
    "还没在放": "Nothing playing",
    "还没在播": "Not playing",
    "未在播放": "Not playing",
    "● 正在播放": "* Now playing",
    "● 正在播放（直播）": "* Now playing (live)",
    "● 正在播放：%s": "* Now playing: %s",
    "正在收听": "Listening",
    "播放失败 (%s)": "Playback failed (%s)",
    "× 换台失败": "x Tuning failed",
    "台单已重载，网格重建完成": "Station list reloaded",
    "全部电台 · 载入中…": "Loading all stations...",

    # ---- 跳转（直播流不可用）
    "直播不能拖": "Cannot seek (live)",
    "读不出总长": "Duration unavailable",
    "跳转": "Seek",
    "跳不了": "Cannot seek",
    "直播不能跳": "Cannot seek (live)",
    "%s%d 分 %d 秒": "%s%d:%02d",
    "快进": "Fwd",
    "快退": "Rew",
    "%s%.10d 秒": "%s%.10ds",
    "快进 ": "Fwd ",
    "快退 ": "Rew ",
    "先播一个再调速": "Play first, then set speed",
    "倍速 %d.%dX": "Speed %d.%dx",
    "已恢复正常": "Back to normal",
    "已切到": "Switched to",
    "倍速 1.0X": "Speed 1.0x",
    "播放提示音": "Playing chime",

    # ---- 进度条提示
    "松手就跳过去": "Release to seek",
    "直播流 · 进度条只读": "Live stream - progress is read-only",
    "拖粗条跳位置 · 上面四键跳分钟": "Drag the bar to seek",
    "读不出总长 · 只能用四个跳转键": "No duration - use the 4 keys",
    "退2分": "-2m",
    "退10分": "-10m",
    "进10分": "+10m",
    "进2分": "+2m",
    "细条可左右拖动": "Drag the thin bar",
    "LIVE  %s  延迟%lds": "LIVE  %s  delay%lds",
    "LIVE  00:32  延迟5s": "LIVE  00:32  delay5s",

    # ---- 音量 / 亮度
    "音量 %d%%": "Vol %d%%",
    "音量 60%": "Vol 60%",
    "屏幕亮度 %d%%": "Brightness %d%%",
    "屏幕亮度 85%": "Brightness 85%",

    # ---- 音频格式
    "网络流": "Net stream",
    "网络电台 · 直播\\n%s %d/%d": "Internet radio - live\\n%s %d/%d",
    "网络流 · 64 kbps": "Net stream - 64 kbps",
    "网络直播 · 64 kbps": "Internet live - 64 kbps",
    "本地音频 · 内存卡\\n%d.%01dkHz %s": "Local audio - SD card\\n%d.%01dkHz %s",
    "本地音频 · 内存卡\\n正在解析格式…": "Local audio - SD card\\nParsing format...",
    "正在解析格式…": "Parsing format...",
    "单声道": "Mono",
    "立体声": "Stereo",

    # ---- 上一台 / 下一台
    "上一个": "Prev",
    "下一个": "Next",

    # ---- 频谱
    "频谱·柱": "Bars",
    "频谱·镜": "Mirror",
    "频谱·环": "Ring",
    "切换频谱": "Spectrum",
}

# ───────────────────────────────────────────── ③ 首页 / 列表页
LIST = {
    "选项": "Menu",
    #★ 「收藏」「历史」在这里是【页面标题】（容器 300+ px），
    #   用完整词；而标签条胶囊（同词，51 px）在 CHIP 表里是 "Fav"/"Hist"。
    #   生成器按位置区分：k_cat_short[] 数组整块用 CHIP，其余用 ALL。
    "收藏": "Favorites",
    "历史": "History",
    "电台列表": "Stations",
    "电台": "Stations",
    "本地列表": "Local files",
    "本列表": "This list",
    "本地": "Local",
    "所在文件夹": "Folder",
    "全部电台 · 共 %d 台 · 上下滑看更多": "All stations - %d - scroll for more",
    "收藏/历史优先 · 显示 %d / 共 %d 台 · 上下滑": "Fav/History first - %d of %d",
    "全国台 %d 个 · 全部 %d 个 · 上下滑": "%d nationwide - %d total - scroll",
    "海外与港澳台 · %d 个地区 · 点一个看它的台": "World - %d regions - tap one",
    "海外与港澳台": "World",
    "海外 %d": "Intl %d",
    "海外": "Intl",
    "地区 · 左右滑": "Regions - swipe",
    "点 ← → 翻到想要的地区，再点地区看该省全部电台（长按电台名 = 收藏）":
        "Swipe for a region, tap it to list - long-press to favorite",
    "%s · 共 %d 台 · 上下滑": "%s - %d - scroll",
    "%s · 还没有台": "%s - empty",
    "收藏 · 历史 · 卡内 ｜ 12 个栏目 · 点 ← → 翻页":
        "Fav - History - SD | 12 categories - swipe",
    "正在载入台单…": "Loading...",
    "载入中…": "Loading...",
    "返回": "Back",
    "‹ 返回": "< Back",
    "← 返回": "< Back",
    "返回上级": "Up one level",
    "返回首页": "Home",
    "‹ 首页": "< Home",
    "读取中…": "Reading...",

    # ---- 首页三张入口卡
    "收藏电台": "Favorites",
    "我的收藏": "My favorites",
    "播放历史": "History",
    "最近听过": "Recently played",
    "音乐库": "SD audio",
    "全部电台就在下面": "All stations below",
    "城市声音集": "Local audio",
    "本地音频": "SD audio",
    "城市声音集 -> 本地音频": "Local audio",
    "正在播放卡 -> 播放页": "Now playing",
    "先在下面选一个台": "Pick a station below",
    "还没有记录": "Nothing yet",
    "%d 个常用台": "%d favorites",
    "已收藏": "Favorited",
    "已取消收藏": "Removed",
    "收藏满了（最多 64 个）": "Favorites full (max 64)",
    "★ 已收藏": "* Favorited",
    "收藏就绪：%d 个": "Favorites ready: %d",
    "★ 收藏": "* Fav",
    "☆ 收藏": "☆ Fav",

    # ---- 台单行
    "点电台名 = 播放　长按 = 收藏/取消　返回 = 回上一页":
        "Tap = play. Long-press = favorite. Back = previous page",
    "%s 首 →": "%d items >",
    "暂无音频 →": "No audio >",
    "去「城市声音集」点一首": "Pick a track in SD audio",
    "本目录没有别的音频": "No other audio in this folder",
    "× 这一目录没有别的音频": "x No other audio here",
    "点首页一行电台 →": "Tap a station on Home >",

    # ---- 本地音频
    "未检测到内存卡": "No SD card",
    "未插内存卡": "No SD card",
    "未挂载内存卡": "No SD card",
    "请插入 FAT32 格式的 TF 卡后重试": "Insert a FAT32 TF card and retry",
    "%s · %u MB · 本目录 %d 项 · 全卡音频 %d 首":
        "%s - %u MB - %d here - %d total",
    "目录 →": "Folder >",
    "现在不是电台（本地文件不收藏）": "Not a station (local files cannot be favorited)",
}

# ───────────────────────────────────────────── ④ 状态页
SYS = {
    "系统状态": "System status",
    "刷新状态": "Refresh",
    "重新读取": "Reload",
    "固件": "Firmware",
    "运行": "Uptime",
    "内存": "Memory",
    "音频": "Audio",
    "存储": "Storage",
    "电池": "Battery",
    "内部 %u KB / PSRAM %u MB": "Internal %u KB / PSRAM %u MB",
    "TF %u MB · 音频 %d 首": "TF %u MB - %d tracks",
    "无卡": "No card",
    "就绪": "Ready",
    "未就绪": "Not ready",
    "已接电池": "Battery connected",
    "未接电池": "No battery",
    "正在充电": "Charging",
    "电池 %d%% · %d.%02d V（点击=未接）": "Battery %d%% - %d.%02d V",
    "电池 未接（点击=已接）": "No battery",
    "未初始化": "Not initialized",
    "已连接": "Connected",
    "已设置": "Configured",
    "未配置": "Not configured",
    "连接中": "Connecting...",
    "连不上": "Failed",
    "已定位": "Found",
    "不在列表里": "Not in list",
    "找不到该网络": "Network not found",
    "密码错": "Wrong password",
    "被拒绝": "Rejected",
    "未知": "Unknown",
    "正常": "Normal",
    "正常关闭": "Clean close",
    "认证过期": "Auth expired",
    "扫描中…": "Scanning...",
    "扫描中…（上次 %d 个）": "Scanning... (%d last time)",
    "连接中… %s": "Connecting to %s",
    "连接失败 (%s)": "Connection failed (%s)",
    "连不上 · %s · %s": "Cannot connect - %s - %s",
    "未配置 · 内存卡里放 wifi.txt": "Not configured - put wifi.txt on the SD card",
    "日期等待联网校时": "Date pending network sync",
    "%d 月 %d 日 · %s": "%b %d, %s",
    "月/日": "M/D",
    "星期日": "Sun",
    "星期一": "Mon",
    "星期二": "Tue",
    "星期三": "Wed",
    "星期四": "Thu",
    "星期五": "Fri",
    "星期六": "Sat",

    # ---- WiFi 配网
    "WiFi 配网": "WiFi setup",
    "开始配网": "Start setup",
    "关掉配网": "Stop setup",
    "扫描 WiFi": "Scan WiFi",
    "扫描周围 WiFi": "Scan nearby WiFi",
    "重新扫描": "Rescan",
    "手机配网 →": "Setup via phone >",
    "连 wifi.txt": "Connect wifi.txt",
    "返回状态页": "Back to status",
    "还没连过网 —— 下面点「开始配网」": "Never connected - tap Start setup",
    "网络未初始化": "Network not initialized",
    "附近 %d 个网络（网页里会列出来）": "%d networks nearby",
    "已扫到 %d 个网络，网页下拉里选": "%d networks found - pick in the page",
    "没扫到也能配，网页里可手输名称": "Can still set up - type the name manually",
    "（还没开热点）": "(hotspot not started)",
    "1. 手机已连上热点（%d 台）": "1. Phone connected to hotspot (%d devices)",
    "1. 请用手机连下面这个热点": "1. Connect your phone to the hotspot below",
    "1. 点「开始配网」，然后手机连这个热点":
        "1. Tap Start setup, then connect your phone",
    "2. 连上后手机会自动弹出配网页": "2. A setup page will pop up in your browser",
    "3. 已连上，关掉网页就行": "3. Connected - you can close the page",
    "3. 正在连接，请稍等…": "3. Connecting, please wait...",
    "3. 密码不对？换个网络再试": "3. Wrong password? Try another network",
    "3. 网页里选 WiFi、填密码、点连接":
        "3. Pick WiFi, enter password, tap Connect",
    "正在扫描周围网络…（约 3 秒）": "Scanning nearby networks... (about 3s)",
    "正在用你选的网络连接…": "Connecting to the network you chose...",
    "没连上：%s": "Not connected: %s",
    "已连 %s · %s · %d dBm": "Connected to %s - %s - %d dBm",
    "正在连接 %s…": "Connecting to %s...",
    "连不上 %s · %s": "Cannot connect to %s - %s",
    "网页提交的内容不对，请重试": "Bad input from the page, please retry",
    "已填": "entered",
    "空（开放网络）": "empty (open network)",
    "强": "Strong",
    "中": "Medium",
    "弱": "Weak",
    "很弱": "Very weak",
}

# ───────────────────────────────────────────── ⑤ 提示条 / Toast
TOAST = {
    "已到点 · 播放已停止": "Timer reached - playback stopped",
    "还有 %d 分 %02d 秒后自动停播": "%d:%02d left before auto-stop",
    "睡眠定时（分钟，到点自动停播）": "Sleep timer (minutes)",
    "定时": "Timer",
    "关闭": "Off",
    "请输入分钟数": "Enter minutes",

    # ---- 关机
    "关机": "Power off",
    "正在关机…": "Powering off...",
    "关机？再点一次": "Power off? Tap again",
    "再点一次关机": "Tap again to power off",

    # ---- SD 卡
    "未检测到内存卡": "No SD card",
}

# ═════════════════════════════════════════════ ⑥ 合并与自检
ALL = {}
for d in (UI, PLAY, LIST, SYS, TOAST):
    for k, v in d.items():
        if k in ALL and ALL[k] != v:
            raise SystemExit(
                "!! 翻译表冲突：%r 有两个不同译文（%r / %r）\n"
                "   同一个中文词在两处宽度不同时，别硬塞进ALL ——\n"
                "   窄容器用 CHIP（整块替换），宽容器才进 ALL。"
                % (k, ALL[k], v))
        ALL[k] = v

# ★ 自检 1：CHIP 译文必须【比ALL 短或等长】。
#   同一个中文词允许两张表都有（「收藏」「历史」就是如此）：
#     - 胶囊 51 px  ⇒ 用 CHIP 的短名（Fav / Hist）
#     - 页面 300 px ⇒ 用 ALL 的完整词（Favorites / History）
#   生成器按【位置】选用哪张表：k_cat_short[] 数组整块用 CHIP，
#   其余所有字面量用 ALL。所以重叠不是错误。
#   真错误是反过来的：CHIP 比 ALL 还长 —— 那说明写反了。
for _k in set(CHIP) & set(ALL):
    if len(CHIP[_k]) > len(ALL[_k]):
        raise SystemExit(
            "!! 胶囊译文比宽容器还长，写反了：%r CHIP=%r ALL=%r"
            % (_k, CHIP[_k], ALL[_k]))
print("  （CHIP/ALL 重叠词 %d 个，按位置选用：%s）"
      % (len(set(CHIP) & set(ALL)),
         ", ".join("%s=%s/%s" % (k, CHIP[k], ALL[k])
                   for k in sorted(set(CHIP) & set(ALL)))))

# ★ 自检 2：胶囊译文必须够短（超宽 ⇒ 界面截字，肉眼可见的坏）
for k, v in CHIP.items():
    if len(v) > CHIP_MAX_CHARS:
        raise SystemExit("!! 胶囊译文过长（%d > %d）：%r -> %r"
                         % (len(v), CHIP_MAX_CHARS, k, v))

if __name__ == "__main__":
    print("ALL 文案 %d 条 / CHIP 胶囊 %d 条" % (len(ALL), len(CHIP)))
    print("胶囊最长%d 字符（上限 %d）"
          % (max(len(v) for v in CHIP.values()), CHIP_MAX_CHARS))
    print("\n★ 需人工确认「译文是否放得进容器」的长条目：")
    for k, v in ALL.items():
        if len(v) >= 22:
            print("   %2d字符 %r-> %r" % (len(v), k, v))