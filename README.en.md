# XianDial firmware · 拾声

**An ESP32-S3 internet radio firmware with zero built-in stations. You bring the stations.**

Radio the way it was meant to work: power on, pick a station, hear it. No account, no recommendation engine, no splash ads.

- **Hardware:** ESP32-S3 + 3.5" IPS TFT touchscreen (480×320, ST77922 + FT5x06 capacitive touch)
- **Audio:** I2S DAC → amplifier. Plays MP3 / AAC / FLAC / OGG, plus HLS (`.m3u8`) live streams
- **Stations:** read **your own** station list from a TF card (**0 stations built in** — see below)
- **Memory:** LVGL pool 112 KB, 8 MB PSRAM

> 中文版 / Chinese version: [README.md](README.md) · 烧录步骤 / Flashing: [FLASHING.md](FLASHING.md)
>
> ⚠️ **This manual covers the Chinese-interface firmware.** If you want the **English-interface** firmware, it lives in a separate repository: **[xiandial-radio-en](https://github.com/podcatcher962/xiandial-radio-en)** — same engine, same station-list format, English UI, also zero built-in stations.

---

## Why this repo ships with an empty station list

**The built-in station count is 0.** That's a deliberate decision, not an unfinished feature:

1. A list of real radio stream URLs is this project's single biggest public risk (provenance and copyright). Publishing one would make the repo a distribution channel for somebody else's servers.
2. The author's own list was built years ago with `http` + `.ts` segments to save RAM. **Most M3U files you can download today are `https` + raw ADTS AAC** — completely different code paths. Shipping a "starter list" would actively mislead you.

So the division of labour is: **the firmware provides the interface, the tool builds the list, the URLs are yours.**

### What you actually get

A firmware that **completes the whole workflow end to end** — not a promise that every M3U you throw at it will play:

| | Status |
|---|---|
| UI and interaction (station grid, now-playing, favourites, history, sleep timer, WiFi setup) | ✅ Full source, modify freely |
| Playback engine (direct streams + HLS live + format sniffing) | ✅ Full source |
| Station import (TF card / serial push / hot reload) | ✅ Complete |
| How many of *your* M3U entries will play | ⚠️ **Depends on the source** — see below |

### How many of your stations will play

This shouldn't be vague, so here's the model:

```
playable ≈ total entries × format support rate × server reachability × https pass rate
```

| Factor | What drives it | Typical |
|---|---|---|
| **Format support** | Direct MP3/AAC/FLAC/OGG and HLS (`.m3u8`). **Not supported:** nested `.m3u`/`.pls` playlists, audiobook formats, streams needing a `Referer` header, authenticated streams, non-standard containers | ~85% |
| **Server reachability** | Is the origin still alive? Does it allow your IP? Region or rate limits? | 70–85% |
| **https pass rate** | https costs TLS buffers. **Fixed in this build** (v1.51 shrank the mbedTLS single-connection buffer 16 KB → 4 KB and enabled startup-time allocation). Failures now are almost always certificate-chain problems | near 100% after the fix |

> ⚠️ **In v1.50 and earlier, https stations were essentially all broken.** Root cause: the largest *contiguous* block of internal RAM was too small for TLS (this is not the same as "free memory is too low" — checking free memory gives you the opposite conclusion). **That is fixed here.**

For reference, the author's own 1253-entry list had this shape:

| Type | Share | Plays? |
|---|---|---|
| Direct `.mp3` / `.aac` | 59.3% | ✅ Most reliable |
| HLS `.m3u8` | 28.4% | ✅ If the server allows it |
| No extension (content sniffing) | 12.3% | ⚠️ Coin flip |

**Your M3U will look different.** The author's list was 98.7% `http` by design; most lists you find online today are `https`, which is the harder path. **Plan for ~70% and treat anything above that as a bonus.**

### When a station won't play

Use the serial console to find out which layer fails (**the `?insecure` suffix only exists in self-compiled builds** — it's compiled out of the release):

```
st_net http://your-stream-url
```

The log tells you which layer broke: **DNS / TCP / TLS / HTTP / decode**. If any of the first four fails, it isn't the firmware's fault.

- `403` → needs a `Referer` or UA spoof. Not supported.
- `open` fails + TLS error → certificate chain problem (expired or self-signed).
- `200` but nothing after `#EXTM3U` → the server responds but serves no data.
- Decode errors → codec the firmware doesn't handle (some WMA and AMR variants).

---

## Flashing the firmware

**Full step-by-step guide: [FLASHING.md](FLASHING.md)** — including serial port names, boot mode, and a troubleshooting table.

The short version:

**You need:**

| Item | Notes |
|---|---|
| An ESP32-S3 board | With a 3.5" IPS TFT (ST77922 + FT5x06). **This firmware targets that display only.** |
| A USB **data** cable | Onboard USB. Note: the Type-C PHY is taken by Serial-JTAG, so the board **cannot** act as a USB host (no USB drives, no card readers). |
| A computer | Windows / macOS / Linux |
| A TF card | Optional — you can push the station list over serial instead. |

**Three files go into the flash, at fixed offsets:**

| Offset | Content | File |
|---|---|---|
| `0x0` | Bootloader | `bootloader.bin` |
| `0x8000` | Partition table | `partition-table.bin` |
| `0x10000` | Application | `xiandial-radio.bin` |

> ⚠️ **The most common beginner mistake: flashing `xiandial-radio.bin` to `0x0`.** That writes the application into the bootloader region and the board will not boot (no serial log, black screen). It's one of three segments, and its offset must be `0x10000`.

**Release assets:**

| File | Use |
|---|---|
| **`XianDial-v1.51-merged.bin`** | ★ **Recommended.** All three segments merged into one file, flash at `0x0`. No address mistakes possible. |
| `bootloader.bin` + `partition-table.bin` + `xiandial-radio.bin` | Segment flashing, three addresses. Full commands in `FLASHING.md`. |
| `XianForge.html` | Station list builder (Chinese UI) |
| `XianForge.en.html` | Station list builder (English UI, identical output format) |
| `SHA256SUMS.md` | SHA256 of every asset — verify after download, before flashing |

**Easiest path — web flasher, nothing to install:**

Open [ESP Web Tools](https://espressif.github.io/esptool-js/) → `Connect` → pick your port →
select **`XianDial-v1.51-merged.bin`** → chip **ESP32-S3**, address **`0x0`** → `Start`.

**Command line:**

```bash
pip install esptool
esptool.py --list-ports

# Recommended when upgrading versions (clears WiFi config and favourites)
esptool.py --chip esp32s3 --port COM3 erase_flash

esptool.py --chip esp32s3 --port COM3 --baud 460800 \
    write_flash 0x0 XianDial-v1.51-merged.bin

# Watch the boot log (prints version, station count, WiFi status)
esptool.py --chip esp32s3 --port COM3 monitor
```

**From source** (only if you want to change the UI or add formats):

```bash
git clone <this repo> && cd xiandial-radio
idf.py set-target esp32s3
idf.py -p COM3 build flash monitor
```

Requires ESP-IDF **6.0+** (built with 6.1).

> ⚠️ **Flashing overwrites whatever is already on the chip.** There is **no OTA partition**, so every upgrade means flashing again.

### First boot

1. The screen prompts you to join its WiFi hotspot (named `XianDial-XXXX`); open `http://192.168.4.1` and enter your WiFi name and password
2. It works without WiFi too — the device sits at "0 stations" waiting for your list rather than showing a blank screen

---

## Adding stations: three steps

```
①  Open tools/XianForge.html, drop in your M3U / TXT  →  export stations.tsv
②  Copy stations.tsv to the root of a TF card
③  Insert the card and power on — the device reads it
```

A missing card, an unreadable card, or a malformed file will never produce a blank screen: the device stays at "0 stations" and tells you to import.

**Hot reload** works with the card inserted: send `st_reload` over serial to re-read without rebooting, or `st_put stations.tsv` to overwrite over serial.

**The favourites list is empty on first boot — this is expected.** The built-in list is empty and the author's favourites were not shipped. After you import a `stations.tsv`, press the favourite key on the now-playing page and your stations stick from then on.

---

## Station file format

Path must be **`/sdcard/stations.tsv`** (TF card root).

```
Station Name<TAB>Category<TAB>Region<TAB>URL
```

| Requirement | Value |
|---|---|
| Encoding | UTF-8, **no BOM** |
| Line endings | LF (**not** CRLF) |
| Separator | **TAB** (not spaces) |
| Max entries | 2000 |
| Blank lines / `#` comments | Ignored |

Extra spaces inside a field are stripped; the URL must be field 4 and must not contain a TAB.

**Why BOM and CRLF matter so much:** a BOM puts a stray box glyph in front of the first station name and breaks name-based favourite matching. CRLF leaves a trailing `\r` on the URL — the symptom is "every other station works, but these few don't", which is miserable to debug.

Category and region values (the converter infers them, so you rarely need to care):

- **Category (13):** `新闻综合` `交通台` `音乐` `文艺` `说书` `戏曲` `怀旧老歌` `网络台` `教育台` `电视伴音` `综合` `宗教` `境外新闻`
- **Region (42):** `北京` … `新疆` `中国台湾` `中国香港` `中国澳门` `其他华语` `北美` `欧洲` `日韩` `新马` `东南亚` `大洋洲` `海外中文`
- Empty region or `其他` → treated as a nationwide station

> ⚠️ **These are fixed identifiers parsed by the firmware, not display strings.** They stay in Simplified Chinese in every build. `XianForge.en.html` writes the same tokens, so a file produced by the English tool works on a Chinese build and vice versa.

---

## ⚠️ Important limitation for non-Chinese station names

**The station-name font shipped in this build covers ASCII plus the 3755 level-1 characters of GB2312 (Simplified Chinese).**

Consequences:

- ✅ Station names in **English, Spanish, French, German, Italian, Portuguese, Vietnamese, Indonesian, Malay** — Latin letters are all in the ASCII block, so these render correctly.
- ❌ Station names in **Cyrillic (Russian, Ukrainian), Greek, Arabic, Hebrew, Devanagari, Thai, Hangul, or Kana** — these render as **boxes (□)**.

This is not a code bug; it's the size tradeoff. The station name comes from your file at runtime, so the glyphs must be baked in at build time, and shipping a full Unicode font would multiply the firmware size several times over.

**If your stations have Cyrillic or CJK-kana names, you need to rebuild the station-name font.** See *Rare station names show up as boxes* below — the same instructions apply; just point the generator at your own `stations.tsv`. After regenerating, remember to update the file list in `main/CMakeLists.txt`.

The **UI chrome** (menus, labels, buttons) is Simplified Chinese in this build. For a genuinely localised build you would change the strings in `ui_xiandial.c` and regenerate the main fonts — both are straightforward but neither is done here.

---

## Companion tool

### XianForge.html — station list builder

**A single HTML file. Double-click to run. No network, no uploads.** Location: `tools/XianForge.html` (Chinese UI) or `tools/XianForge.en.html` (English UI).

- Reads M3U (any `#EXTINF` variant) and plain-text lists
- Auto-detects UTF-8 / GBK / UTF-16
- Infers category and region from the station name
- De-duplicates by URL (multiple mirrors of the same station are all kept)
- Exports `stations.tsv`

Both language versions write the identical file format, so they're interchangeable.

**Run the self-test after any change** (needs Node.js, no browser):

```bash
node tools/_xf_selftest.js
```

31 assertions covering category inference (including the very common `XX People's Broadcasting Station` pattern and the TV-audio priority rule), M3U parsing, URL de-duplication, TSV four-field compliance, and edge cases such as CRLF, a trailing CR, missing names, and rows with no URL. Non-zero exit code means something is wrong.

> This self-test is not ceremony. It caught a real bug during development: the category rule table only listed `Central People's Broadcasting Station`, so every `Beijing People's Broadcasting Station` was classified as the fallback `General`. The build was clean and the UI showed nothing wrong.

### _sd_push.py — serial card push (optional, in `tools/`)

The onboard TF slot runs in SDIO, so Windows can't see the card; and the Type-C PHY is occupied by Serial-JTAG, so the board can't act as a USB host. The firmware therefore exposes a serial channel that can read and write the card directly:

```bash
pip install pyserial

python tools/_sd_push.py stations.tsv     # push the list (with flow control and a line-count check)
python tools/_sd_cmd.py   st_reload       # re-read and rebuild the UI, no reboot
python tools/_sd_cmd.py   st_ls           # list files on the card
```

Supported serial commands: `st_dump` `st_reload` `st_ls` `st_cat <file>` `st_rm <file>` `st_put <file>` (line-by-line, a lone `.` terminates) `st_play <index>` `st_net <url>` (layered network test).

File writes go to a `.tmp` first and are then renamed, so a dropped connection never leaves a half-written file behind.

---

## Hardware specification

The configuration verified on the author's own unit. **This firmware has only been tested on this hardware** — a different display, touch controller, or audio path means code changes.

| Item | Spec |
|---|---|
| MCU | **ESP32-S3** (RISC-V, 512 KB SRAM, 8 MB PSRAM) |
| Display | **3.5" IPS TFT**, 480×320, **ST77922**, SPI |
| Touch | **FT5x06** capacitive (I2C), 5 points |
| Audio | I2S DAC → amplifier (**+5 V**), 4 Ω 3 W mono speaker |
| Storage | Onboard **TF slot** (SDIO); 16 MB flash for firmware |
| Network | 2.4 GHz WiFi + Bluetooth (on-module) |
| Power | 3.7 V Li-ion + LDO, LDO-only ⇒ ~2 hours from 1000 mAh |
| Sleep | Deep sleep, **RTC wake from IO0–21 only** (BOOT button = IO0) |
| WiFi setup | **SoftAP + captive portal** (IO45/46 cannot wake from deep sleep) |
| Framework | ESP-IDF 6.1 + LVGL 9 (`LV_MEM_SIZE` = 112 KB) |
| Partitions | No OTA; upgrading requires a reflash |

**Known hardware constraints (read before changing boards):**

- The onboard Type-C USB PHY is occupied by Serial-JTAG, so the board **cannot act as a USB host** — external USB drives and card readers do not work. Write to the TF card over WiFi or use the onboard slot.
- The TF card is on **SDIO** and is not visible when the board is plugged into a PC. On a desktop, use a USB card reader and join the `XianDial-XXXX` hotspot.
- Power-off relies on a hardware quirk (Q3's gate is not wired to the MCU), so **no GPIO can actually cut power**. "Off" means display off + WiFi off + deep sleep.

---

## Building

```bash
git clone <this repo>
cd xiandial-radio
idf.py set-target esp32s3
idf.py build
idf.py -p COM3 flash monitor
```

Requires ESP-IDF **6.0+** (built with **6.1**).

> `main/idf_component.yml` declares `idf: ">=6.0"`. This is not arbitrary: the project uses `esp_driver_i2s`, `esp_driver_sdmmc`, `esp_driver_ledc`, and `esp_driver_usb_serial_jtag`, whose component registration differs between 5.x and 6.x. Declaring 5.x leaves users stuck in CMake halfway through a build. Better to require the higher version.

**What's in the repo, and what isn't:**

| Content | Status |
|---|---|
| Application source, station import, UI, playback | ✅ Complete |
| Main fonts `xs_font_12/16/24` + `xs_font_cjk12` | ✅ Complete (Ark Pixel + Source Han Sans, both OFL-1.1) |
| Release station list `net_stations_pub.c` | ✅ 0 entries |
| Station-name fonts `xs_font_pub_st12/16.c` | ✅ Generic (GB2312 level-1, 3755 chars + ASCII) |
| Real station lists, fonts baked from real station names, source TTFs | ❌ Not included |

### Why there are two station-name fonts

Station names arrive at runtime from your `stations.tsv`, so the build cannot know which glyphs will be needed. A separate font is compiled in for them.

| | Author's build | This repo |
|---|---|---|
| Files | `fonts/xs_font_st12/16.c` | `fonts/xs_font_pub_st12/16.c` |
| Glyph source | Characters appearing in a real station list | GB2312 level-1, 3755 characters |
| In the repo | ❌ Excluded | ✅ Included |
| Size | 1.00 MiB | 2.86 MiB |

**Why not include the author's set:** it is baked from the characters occurring in a real 1254-entry list. Shipping the list as *glyph outlines* is still shipping the list — that is not an empty list.

**Both sets deliberately use the same symbol names** (`xs_font_st12`); only the filenames differ. `main/CMakeLists.txt` picks one based on whether `net_stations_pub.c` exists, so the two are never compiled together. **The UI code is byte-identical between builds** — not one line needs changing.

**Font sizes:** 12 px (station grid, list rows) and 16 px (large name on the now-playing page). The 24 px set was **deleted** — no label ever used it (see the comment in `ui_xiandial.c`), and it cost 1.21 MiB of build time and repository size for nothing.

### Rare station names show up as boxes

The bundled font covers GB2312 level-1 (3755 characters), which handles 99.7% of everyday modern Chinese text. A few rare characters (GB2312 level-2, dialect characters, coined words) will render as boxes.

**Regenerate it from your own list:**

```bash
# 1. Point the generator at your stations.tsv
#    (st_chars() scans the TSV plus the region and category name tables)
# 2. Generate xs_font_st12.c / xs_font_st16.c
python ../gen_fonts_st.py
# 3. Remove main/net_stations_pub.c so CMake takes the non-release branch
```

The glyph set narrows to what your list actually uses, so the result is usually smaller than the bundled font. After adding or removing font sizes, update the file list in `main/CMakeLists.txt` — a mismatch there produces `missing and no known rule to make it`.

> The source TTFs (Ark Pixel / Source Han Sans) are not in the repository. Follow the instructions at the top of `firmware/gen_fonts.py` to obtain them; both OFL licence texts ship with this project.

---

## Known limitations

- **No OTA.** Upgrading requires reflashing.
- **Some M3U sources will not play.** Usual causes: certificate chain mismatch, a required `Referer` header, authentication, non-standard container formats. Adapting to every one of them isn't realistic; the firmware handles mainstream formats (direct MP3/AAC/FLAC, HLS live).
- **HLS multi-variant streams use the first variant only**, without selecting by bandwidth.
- **Deep-sleep wake works from RTC IO0–21 only.** Hence SoftAP + captive portal for WiFi setup.
- **HLS live windows slide**: segments expire, so reconnecting to a live source after a drop can take a few seconds.

These are design trade-offs, not leftover bugs. The source is all here.

---

## Before you modify anything

If you plan to change this firmware (swap the UI, add a station format, adjust font sizes), know whether it's currently clean:

```bash
node tools/_xf_selftest.js        # 31 assertions for the station tool
```

Two development-time check scripts also ship with the project (in `firmware/`, outside the `xiandial-radio/` repository):

| Script | Purpose |
|---|---|
| `_release_check.py` | Pre-release gates: empty station list, font symbol names and de-identification, leak scanning, tool self-test, README consistency, licence completeness |
| `_release_gitscan.py` | Scans only what Git will actually commit, and validates its own rules first |

> Both scripts are built around "verify the checker against a known answer first". They each caught a real problem during development — one was the scanner reading CSS `font:13px` as a local filesystem path, the other caught the release font baking in the `-o` output path. **"It ran without errors" is not the same as "it passed" — read the self-test section.**

---

## Privacy (this section is a commitment, not marketing copy)

### What this device does on the network

**Three things in total:**

1. Connects to **your** WiFi (SoftAP setup page, or reads `wifi.txt` from the card)
2. Fetches the **station streams you imported** (the URLs in your `stations.tsv`)
3. Sends **one** time-sync request to `ntp.aliyun.com` (UDP/123)

**There is no fourth thing.** Specifically:

| You might worry about | Reality |
|---|---|
| Uploading MAC / chip ID / IMEI / device fingerprint | **No.** The MAC is used only for the local SoftAP name (`XianDial-XXXX`) and the IDF's own partition, and is never transmitted |
| Telemetry / analytics / crash reporting / usage stats | **No.** There is no statistics SDK anywhere in the firmware |
| Update checks / version reporting | **No.** No OTA partition, no update-check request of any kind |
| Uploading your station list to the author | **No.** The list lives on the TF card; the device only treats entries as connection targets |
| Sending your WiFi password off the device | **No.** The setup page only talks to your own router |

### You can verify this yourself

The firmware is not a black box. Scan it:

```bash
# Every fixed outbound domain in the firmware (there is exactly one)
strings -n 6 firmware.bin | grep -oE '[a-z0-9-]+(\.[a-z0-9-]+)*\.(com|net|org|cn|io)' | sort -u

# Confirm there are no POST / PUT requests (only GET should appear)
strings -n 6 firmware.bin | grep -iE 'POST|PUT'
```

Every hit other than `ntp.aliyun.com` comes from the bundled CA certificate package, which is there to **verify other people's** https certificates — not to be connected to.

### What is stored on the device

| Location | Contents |
|---|---|
| NVS `xs_wifi` | Your WiFi **name and password (plaintext)** |
| NVS `xs_fav` | Favourite station names |
| NVS `xs_hist` | Listening history |
| NVS `xs_sleep` | Sleep timer minutes |

**On the plaintext WiFi password:** ESP-IDF's NVS is unencrypted by default and can be read over serial. This is a deliberate tradeoff at the "home router" scale — it avoids a third-party crypto dependency and saves a few hundred bytes of flash. If your WiFi password shouldn't be stored that way, **don't set up this device with it**, or enable `CONFIG_NVS_ENCRYPTION` in the source (costs flash).

### Two things the firmware cannot do (better stated up front)

- **There is no switch to disable HTTPS certificate verification.** The author's build has an `?insecure` suffix used for debugging (to distinguish "out of memory" from "certificate not trusted"); **the release build removes it at compile time.** Compile it yourself if you need it.
- **The serial log prints nearby WiFi network names** (the scan results before connecting). That is local serial output and does not leave the device — but if you pipe serial logs into a public logging service, those names go with it.

---

## Disclaimer

**Please read this section before using the firmware.**

### What this is

This is firmware for an **open-source hardware project**. The author built a network radio for personal use and tidied the code into a public repository. It is not a commercial product and has **undergone no commercial certification, stress testing, or long-term operation**.

### What the author does not promise

- **No promise that your station sources will play.** Whether they play depends on the source itself — container format, whether the server permits access, certificate validity, and whether the bitrate is supported. This firmware handles mainstream formats only.
- **No promise of stability.** There is no OTA, so upgrades require a reflash. The author has verified it **only on the unit in their own hand**; your board revision, display, touch panel, and TF card may differ.
- **No promise of bug-free operation.** This is a personal project with no test team.

### What is your responsibility

- **Flashing the firmware overwrites the existing program on the chip.** Please be sure you know what your device contained beforehand.
- **Station sources belong to their respective owners.** This repository **ships no station URLs at all** (the built-in list is empty). Whether any M3U playlist, station list, or stream URL you obtained from anywhere is legal is for you to judge; the author accepts no responsibility for your use of it.
- **Comply with local law and with copyright rules covering audio content.**
- **Your own data is your own responsibility.** The firmware reports nothing, but radio content and IP addresses are yours.

### Limits of the author's liability

- The source is open and licensed under **MIT**, with no warranty of any kind (see `LICENSE`).
  ※ The MIT text requires that the copyright notice be retained — if you fork or redistribute, please keep the attribution at the end of this file.
- Fonts are licensed under OFL-1.1 (`OFL-1.1-*.txt`).
- **The author bears no responsibility for any direct or indirect loss arising from use of this firmware.**

### One-sentence version

> This is a reference implementation that completes the whole workflow, not a product guaranteed to work. It shows you how an internet radio can be built; the rest of the road is yours.

---

## Licences and credits

- Firmware source: **MIT**
- **Ark Pixel** (12 px pixel font) — SIL OFL 1.1, see `OFL-1.1-Ark-Pixel.txt`
- **Source Han Sans SC** — SIL OFL 1.1, see `OFL-1.1-Source-Han-Sans.txt`

Station lists, URLs, and broadcast content are **not distributed** with this firmware and must be supplied by the user.

---

© Lanlan Eternal · 永远的兰兰