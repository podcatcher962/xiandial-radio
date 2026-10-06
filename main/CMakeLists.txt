# ============================================================
#  拾声 (XianDial) 硬件版 —— main 组件
# ============================================================
# ★★★ 10-06：台单与台名字库要能【自用版 / 发布版】自动二选一。
#
#   做法（在 register 之前用 list(APPEND) 拼好）：
#     存在 net_stations_pub.c（_gen_stations_all.py --publish 生成的 0 条
#     空台单）就只编它 + 两个【发布版台名字库】，否则编自用版的
#     net_stations.c + 三个自用版台名字库。
#     ⇒ 贡献者 clone 下来不用手改任何文件，开箱即编。
#
#   ★★ 为什么字库也要分两套（这是发布最大的坑，台单置空了但字库没换）：
#     xs_font_st12/16/24.c 三个文件（自用版合计 2.26 MB）是拿
#     【net_stations.c 里出现的字】烘出来的字形。台单置空却把它们留着
#     = 1254 个真实台名仍然以【字形】形式残留在固件里，等于没置空。
#     ⇒ 发布版改用 gen_fonts_st.py --publish 生成的
#       fonts/xs_font_pub_st12.c / xs_font_pub_st16.c，
#       字形来源是【GB2312 一级汉字 3755 字】，与任何人的台单无关。
#
#   ★★ 为什么符号名【故意相同】（xs_font_pub_st12.c 里定义的是
#     xs_font_st12，不是 xs_font_pub_st12）：
#     ui_xiandial.c 直接 extern xs_font_st12/st16，改符号名就得改 UI，
#     两个版本各编一份 UI 是维护灾难。文件名不同 ⇒ 两套永不同时进编译，
#     所以同名不冲突。这样【发布版与自用版的 UI 代码 100% 相同】，
#     差异只体现在"字形从哪来"这一处。
#
#   ★★ 为什么发布版只编 12/16 两档、不编 24：
#     st24 是【死符号】—— 全项目检索只有 ui_xiandial.c 的 extern 声明和
#     #define 两处提到它，没有任何地方真正使用。链接器会把它丢掉，
#     但它仍要占 1.2 MB 仓库体积和一段编译时间。
#     自用版也一并去掉（对自用固件 bin 大小零影响）。
#
#   ★★ 必须在 idf_component_register() 【之前】定义，且要用
#     list(APPEND) 而不是把 ${VAR} 写进 SRCS 参数列表。
#     我在 SRCS 里做条件连错三次（SRCS 中间插 if/else ⇒ endif 之后的
#     INCLUDE_DIRS 被甩到函数外，报 Parse error；set() 写在 register
#     之后 ⇒ 本文件 register 在第 1 行，set 完全无效）。
#     ⇒ idf_component_register 是【一次函数调用】，所有参数必须在同一对
#       括号内；list(APPEND) 是逐个追加，展开后是一串独立 token，
#       没有那种解析歧义。这是唯一可靠的写法。
#
#   ⚠ 以后增删台单文件 / 字库档位，这里必须同步改，否则报
#     ninja: error: ... missing and no known rule to make it
#     —— 这条已踩过两次（10-05 删字库档位、10-06 发布版换台单）。
# ============================================================
list(APPEND XS_SRCS
    "xiandial_main.c"
    "app_display.c"
    "app_audio.c"
    "app_sd.c"
    "app_stlist.c"     # ★ 10-06：读 /sdcard/stations.tsv，调用点已切到访问器
    "app_sys.c"
    "app_prov.c"       # ★ 10-04：SoftAP + captive portal 网页配网
    "app_radio.c"
    "app_hls.c"        # ★ 10-03：m3u8 拉流器（HLS 直播）
    "app_fav.c"
    "app_hist.c"
    "app_sleep.c"      # ★ 10-04：睡眠定时（到点自动停播，设定存 NVS）
    "app_pwr.c"        # ★ 10-04：电量检测 IO8 + deep sleep 关机（BOOT 键开机）
    "app_led.c"        # ★ 10-04：板载 RGB 状态灯 IO40（WS2812 via RMT）
    "ui_xiandial.c"
    # ★ 10-05 换字库（v1.36）：Ark Pixel 12px + 思源黑体补字，均为 OFL-1.1。
    #   字号档由 11/14/18/38/52 五档砍到 12/24 两档（10.85 MB → 4.02 MB）。
    #   生成脚本：firmware/gen_fonts.py（主）／gen_fonts_st.py（台名）
    # ★ 10-05 v1.37 加回 16px 中间档（真机反馈：18px 全映射到 24px 太大）
    "fonts/xs_font_12.c"
    "fonts/xs_font_16.c"
    "fonts/xs_font_24.c"
    "fonts/xs_font_cjk12.c"
)

if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/net_stations_pub.c")
    # ---- 发布版：0 条台单 + 通用汉字台名字库（GB2312 一级 3755 字）----
    list(APPEND XS_SRCS "net_stations_pub.c"
                         "fonts/xs_font_pub_st12.c"
                         "fonts/xs_font_pub_st16.c")
    set(XS_ST_MSG "发布版 · 0 条台单（net_stations_pub.c）+ 通用汉字台名字库")
    # ★★ 10-06：发布版【不播种收藏】。宏在文件末尾用
    #   target_compile_definitions 传（不是在这里 append）。
    #   app_fav.c 原来硬编码着兰兰常听的 10 个真实台名（上海戏曲广播、
    #   上海交通、上海第一财经、宁波交通…）。源码扫描查不出来 —— 它们不是
    #   URL、不是路径、不是凭据，只是一个中文字符串；是【直接 grep 编译产物
    #   xiandial-radio.bin】才发现发布版固件里带着这五个台名。
    #   ⇒ 名单改成随台单版本走：自用版 include net_stations_seed.h（本地文件，
    #     已 gitignore），发布版把 XS_FAV_PUBLISH 设成 1 关掉播种。
    #   ⚠⚠ 判据【必须】是 CMake 里这个 if/else，不能在 .c 里用
    #     __has_include("net_stations_seed.h")：
    #     那个头文件是【自用版本地文件】，开发者自己机器上有，
    #     编「发布版」时它照样在 include 路径里 —— 我第一版就是这么写的，
    #     重编后 bin 里 10 个真实台名【一个没少】。
    #     ⇒ 只有「Git 仓库里有什么」和「我这台机器上有什么」是两件事；
    #       判发布形态只能看前者，而 CMake 那个 if/else 就是前者的唯一入口。
    set(XS_FAV_PUBLISH 1)
else()
    # ---- 自用版：1254 台真实地址 + 按台单烘焙的台名字库 ----
    # st24 是死符号（零使用点），不编。
    list(APPEND XS_SRCS "net_stations.c"
                         "fonts/xs_font_st12.c"
                         "fonts/xs_font_st16.c")
    set(XS_ST_MSG "自用版 · 1254 条（net_stations.c）+ 台单烘焙台名字库")
    # 自用版：app_fav.c 会 include main/net_stations_seed.h（XS_FAV_SEED 宏，10 条）
    set(XS_FAV_PUBLISH 0)
endif()
message(STATUS "拾声：台单用【${XS_ST_MSG}】")

idf_component_register(
    SRCS
        ${XS_SRCS}
    INCLUDE_DIRS "."
    # ★★ 这里【只能】出现 idf_component_register 认识的关键字：
    #   SRCS / INCLUDE_DIRS / PRIV_INCLUDE_DIRS / REQUIRES / PRIV_REQUIRES /
    #   EMBED_FILES / EMBED_TXTFILES / WHOLE_ARCHIVE / IDR_TOOLCHAIN
    #   它【没有 DEFINES 参数】。塞 -D 进来会不匹配任何关键字，
    #   于是被并进【上一个】关键字的值列表 —— 上一个是 INCLUDE_DIRS，
    #   报错是「Include directory '.../main/-DXS_FAV_PUBLISH=1' is not a
    #   directory」，完全不提示真因（10-06 踩过，exit 2）。
    #   ⇒ 要传宏，用下面文件末尾的 target_compile_definitions。
    # ★★ 第二十四次踩的坑：main 之前【没写 REQUIRES】，IDF 会把全部组件
    #   的公共头都算进来，所以少写也能编过。app_prov.c 要用 esp_http_server，
    #   一旦加上 REQUIRES，这条「隐式全给」就没了，于是每个用到的组件
    #   都得显式列出，否则报
    #     「app_xxx.c includes xxx.h, provided by xxx component(s).
    #      However xxx is not in the requirements list of "main"」
    #   —— 一次只报一个，得来回好几轮。所以这里一次列全。
    #   清单是扫 main/*.c 的 #include 反查出来的，加新文件时照这个路子补。
    REQUIRES
        # ---- 外设驱动。⚠️ IDF 6.x 把老的 driver 组件拆成 esp_driver_* ----
        #   （driver/i2s_std.h 这个【路径】没变，但提供它的组件叫 esp_driver_i2s）
        esp_driver_gpio          # app_display.c / app_audio.c / app_led.c
        esp_driver_i2c           # app_display.c / app_audio.c
        esp_driver_ledc          # app_display.c：背光 PWM
        esp_driver_spi           # app_display.c：ST77922 QSPI
        esp_driver_i2s           # app_audio.c：I2S0
        esp_driver_sdmmc         # app_sd.c：SDIO 四线
        sdmmc                    # app_sd.c：sdmmc_cmd.h
        # ★★ 10-06：串口命令通道（st_reload / st_dump / st_ls / st_put /
        #   st_play / st_net）要用。这块板【没有硬件 UART】，
        #   控制台是 USB Serial/JTAG（CONFIG_ESP_CONSOLE_UART_NUM=-1），
        #   所以只能靠 esp_driver_usb_serial_jtag 读命令。
        #   不加这一行会报「app_stlist.c includes driver/usb_serial_jtag.h,
        #   provided by esp_driver_usb_serial_jtag ... not in the requirements list」。
        esp_driver_usb_serial_jtag   # app_stlist.c：串口命令通道
        # ⚠️ esp_driver_rmt 已去掉 —— 它只被 app_led.c 用（WS2812 时序），
        #   而 RGB 灯功能被兰兰 10-04 叫停（XS_LED_ENABLE=0）。
        #   复活灯时把这一行加回来，否则 app_led.c 里的 rmt_* 会链接失败。
        esp_adc                  # app_pwr.c：IO8 电池电压 oneshot + 校准
        # ---- 网络 ----
        esp_wifi                 # app_sys.c：STA 扫描与连接
        esp_netif                # app_prov.c：AP netif；esp_netif_sntp.h 也归它
        esp_event                # app_sys.c：WIFI_EVENT / IP_EVENT
        esp_http_server          # app_prov.c：配网页
        lwip                     # app_prov.c：DNS 劫持；esp_sntp.h 也归它
        # ---- 流与存储 ----
        esp_http_client          # app_hls.c：m3u8 拉流
        mbedtls                  # esp_crt_bundle.h（app_hls.c 的 HTTPS）
        nvs_flash
        fatfs                    # app_sd.c
        esp_timer
        # ---- 显示与界面 ----
        esp_lcd                  # app_display.c：ST77922 面板
        esp_app_format           # esp_app_desc.h（app_sys.c 读编译信息）
        lvgl
        espressif__esp_lvgl_port
        espressif__esp_lcd_st77922
        espressif__esp_lcd_touch
        espressif__esp_lcd_touch_ft5x06
        # ---- 音频 ----
        espressif__esp_codec_dev
        espressif__esp_audio_codec
)

# ★★ 10-06：发布版不播种收藏（app_fav.c 里的真实台名曾泄漏进发布版 .bin）。
#   XS_FAV_PUBLISH 由上面那个【和台单同一个】if/else 决定 —— 那是「发布形态」
#   的唯一真相源。必须在这里（register 之后）传，因为 idf_component_register
#   没有 DEFINES 参数（见上面 register 里那段注释）。
target_compile_definitions(${COMPONENT_LIB} PRIVATE XS_FAV_PUBLISH=${XS_FAV_PUBLISH})
if(XS_FAV_PUBLISH)
    message(STATUS "拾声：XS_FAV_PUBLISH=1（发布版 · 不播种收藏）")
else()
    message(STATUS "拾声：XS_FAV_PUBLISH=0（自用版 · 播种 net_stations_seed.h 的常听台）")
endif()
