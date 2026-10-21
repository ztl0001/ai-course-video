# ai视频工作流-编程教学 · 参考实现

SKILL.md 是流程，这里放**参数、颜色、命令和可复制片段**。

---

## 一、画布与色板

```python
W, H = 1600, 1000

PAPER  = (250, 248, 246)   # 纸底
GRID   = (240, 237, 233)   # 网格
INK    = (36, 38, 44)      # 主文字
GRAY   = (112, 114, 124)   # 次要文字
LGRAY  = (168, 170, 180)   # 页码 / 英文
PURPLE = (124, 92, 180)    # 强调
LINE   = (226, 222, 216)   # 分隔线
DARK   = (30, 33, 40)      # 终端底
WHITE  = (255, 255, 255)
```

网格 40px 一格；角落 pastel 径向渐变（雾蓝 `#C2D4EE` / 淡紫 `#E0D2EE`），`GaussianBlur(70)`。

## 二、字体

| 用途 | 字体 | 字号 |
|---|---|---|
| 大标题 | `msyhbd.ttc` | 46–52 |
| 小节标签 | `msyhbd.ttc` | 23 |
| 正文 / 要点 | `msyh.ttc` | 27–30 |
| 代码 | `consola.ttf` | 14–21（自适应） |
| Emoji | `seguiemj.ttf` | 与代码同号 |

**中英 emoji 混排**（关键，否则中文注释变方块）：

```python
def is_emoji(ch):
    o = ord(ch)
    return (0x1F000 <= o <= 0x1FAFF) or (0x2600 <= o <= 0x27BF) or (0x2B00 <= o <= 0x2BFF)

def draw_mixed(d, x, y, text, color, size):
    fa, fc, fe = fm(size), fr(size), fe_font(size)
    cx, buf, kind = x, "", None
    def flush(b, k):
        nonlocal cx
        f = fe if k == "e" else (fc if k == "c" else fa)
        d.text((cx, y), b, font=f, fill=color)
        cx += d.textlength(b, font=f)
    for ch in text:
        k = "e" if is_emoji(ch) else ("c" if ord(ch) > 127 else "a")
        if kind is None or k == kind:
            buf += ch; kind = k
        else:
            flush(buf, kind); buf, kind = ch, k
    flush(buf, kind)
    return cx
```

## 三、代码语法高亮

```python
KEYWORDS = {"def","class","return","if","elif","else","for","while","in","not","and",
 "or","is","None","True","False","import","from","as","try","except","finally","with",
 "lambda","yield","pass","continue","break","self","async","await","raise","del"}

TOK = re.compile(r"(#[^\n]*)|('(?:\\.|[^'])*'|\"(?:\\.|[^\"])*\")|"
                 r"(\b\d+\.?\d*\b)|([A-Za-z_]\w*)|(\s+)|(.)")

C_KEY=(198,120,221); C_STR=(152,195,121); C_FUN=(229,192,123)
C_CMT=(106,112,124); C_NUM=(209,154,102); C_TXT=(171,178,191)

def tokenize(line):
    out = []
    for m in TOK.finditer(line):
        if m.group(1):   out.append((m.group(1), C_CMT))
        elif m.group(2): out.append((m.group(2), C_STR))
        elif m.group(3): out.append((m.group(3), C_NUM))
        elif m.group(4):
            w = m.group(4)
            nxt = line[m.end():m.end()+1]
            out.append((w, C_KEY if w in KEYWORDS else (C_FUN if nxt == "(" else C_TXT)))
        elif m.group(5): out.append((m.group(5), C_TXT))
        else:            out.append((m.group(6), C_TXT))
    return out
```

## 四、自适应字号（代码页）

```python
size = 21
probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
def line_w(line):
    w = 0
    for seg, _ in tokenize(line):
        f = fm(size) if all(ord(c) < 128 for c in seg) else fr(size)
        w += probe.textlength(seg, font=f)
    return w

mw = max((line_w(l) for _, l in rows), default=0)
if mw > 1390:                      # 终端内可用宽度
    size = max(14, int(size * 1390 / mw))
lh = max(20, int(size * 1.48))
```

## 五、ASS 字幕完整样式

浅色画面用「白底深字」，深浅背景都能读：

```
[Script Info]
ScriptType: v4.00+
PlayResX: 1600
PlayResY: 1000
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Microsoft YaHei,38,&H00282626,&H000000FF,&H00FFFFFF,&H28FFFFFF,0,0,0,0,100,100,0,0,3,20,0,2,80,80,74,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
```

- 颜色是 **BGR**：`&H00BBGGRR`
- `&H28FFFFFF` = 84% 不透明白底
- 每行 `Dialogue` **必须以 `\n` 结尾**，否则所有字幕会拼成一行，整段丢失

## 六、ffmpeg 命令集

### 单幕（静图 + 音频）

```bash
ffmpeg -y -loop 1 -framerate 30 -i slide.png -i vo.mp3 \
  -t $DUR -map 0:v -map 1:a -af "apad" \
  -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 160k -ar 48000 -ac 2 seg.mp4
```

### concat

```bash
# list.txt 用相对路径，避免中文/空格路径解析问题
printf "file 'seg/00.mp4'\nfile 'seg/01.mp4'\n" > list.txt
ffmpeg -y -f concat -safe 0 -i list.txt -c copy withvoice.mp4
```

### 烧字幕

```bash
ffmpeg -y -i withvoice.mp4 -vf "ass=subs.ass" \
  -c:v libx264 -preset medium -crf 19 -g 60 -keyint_min 30 \
  -pix_fmt yuv420p -c:a copy -movflags +faststart voice.mp4
```

用 `ass=` 不要用 `subtitles=`（后者对中文/冒号路径敏感）。

### 响度标准化

```bash
ffmpeg -y -i voice.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 voice_n.mp4
```

### BGM 混音

```python
# 目标：BGM 比口播低 9 dB（宁可轻，不可盖人声）
v = mean_vol("voice_n.mp4")      # 口播均值，例 -21.3
b = mean_vol("bgm.mp3")          # BGM 均值，例 -14.9
gain_db = abs(b) - (abs(v) + 9)  # = -15.4
coef = 10 ** (gain_db / 20)      # = 0.170
```

```bash
ffmpeg -y -i voice_n.mp4 -stream_loop -1 -i bgm.mp3 -filter_complex \
"[1:a]volume=0.170,afade=t=in:st=0:d=2,afade=t=out:st=$FADE:d=3[bg];\
 [0:a][bg]amix=inputs=2:duration=first:normalize=0[mix];\
 [mix]alimiter=limit=0.89:level=0[a]" \
-map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
-movflags +faststart final.mp4
```

`alimiter` 必须加 `level=0`，否则自动增益会把限幅抵消，峰值仍是 0 dB。

## 七、封面

| 规格 | 尺寸 | 用途 |
|---|---|---|
| 4:3 | 1200×900 | B站主封面 |
| 3:4 | 1080×1440 | 视频号 |

版式：纸底 + 网格 + pastel；左侧三行大标题（字号按实际字宽自适应，**不要按字符数估**），关键词用淡紫圆角 chip 包住；右侧放一张画面截图，**不倾斜**，越界裁切。

## 八、BGM 可商用来源

| 来源 | 直链方式 | 授权 |
|---|---|---|
| Mixkit | `https://assets.mixkit.co/music/<id>/<id>.mp3`，从 `mixkit.co/free-stock-music/<tag>/` 页面 JSON-LD 里取 | Mixkit Free License，可商用、免署名 |
| Pixabay | 播放器 `<audio>` 的 `currentSrc` | Pixabay License |
| FreePD | 公共领域 | CC0 |

拿不准授权就不用；宁可无 BGM。
