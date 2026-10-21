---
name: ai-course-video
agent_created: true
description: AI 视频工作流 · 编程教学 —— 把 Markdown 教程 / 技术文档 / 课程章节做成 AI 教学视频（编程教学场景）。核心是「一幕一页 + 逐句 TTS + 字幕实测对齐」：代码逐页完整讲解、原文提炼成知识卡、可商用 BGM、烧入字幕。当用户要求把某一章节 / 某篇文档 / 某个代码库做成教学视频、讲课视频、代码讲解视频、知识卡片视频时使用。
---

# AI 视频工作流 · 编程教学

把一份 Markdown 教程变成一支能发 B 站 / 视频号的教学视频。

**这套流程的关键不是画面炫，而是三件事对齐**：画面在讲哪一段、口播在讲哪一段、字幕在显示哪一句。

## 参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `--md <path>` | 是 | 源 Markdown 教程 |
| `--section <已解决的范围>` | 否 | 只做某一节，例如 `8.2`（默认整篇） |
| `--voice <edge-voice>` | 否 | 默认 `zh-CN-YunyangNeural`（云扬） |
| `--rate <+N%>` | 否 | 语速，默认 `+8%` |
| `--bgm <path>` | 否 | 背景音乐；建议 Mixkit（可商用、免署名） |
| `--gap <秒>` | 否 | 场景间隙，默认 `0.7` |
| `--out <dir>` | 否 | 工作目录，默认 `./video-out` |

## 前置检查（每次会话一次）

```bash
node --version          # >= 22
ffmpeg -version
py -3.12 -c "import PIL, edge_tts"
```

缺 `edge_tts` 就 `py -3.12 -m pip install edge-tts`。

字体（Windows 自带，不用装）：

| 用途 | 文件 |
|---|---|
| 中文正文 / 标题 | `C:/Windows/Fonts/msyh.ttc`、`msyhbd.ttc` |
| 代码 | `C:/Windows/Fonts/consola.ttf` |
| Emoji（代码里的 ✅❌🔍） | `C:/Windows/Fonts/seguiemj.ttf` |

---

## 核心原则（先记住这四条，再动手）

### 1. 一幕一页，不要「一块代码配一段口播」

**这是本 Skill 最重要的一条。** 常见错误是：一个代码块配一段口播，再把音频平均切到多页画面。结果画面、语音、字幕三套时间轴各自计算，越到后面偏得越多。

正确做法：

- 一个代码块按行数分页，**每页 = 一个独立场景**
- 每页有**自己的口播文本**（50–90 字，讲清这页在做什么）
- 画面时长 = 该页音频时长 + `--gap`
- 字幕 = 该句音频的**实测时长**

### 2. 逐句 TTS，字幕不用字数估算

把口播按 `。！？` 切句，**每句单独合成**，用 `ffprobe` 量出真实时长，字幕起止直接写实测值。

按字数比例分配只在「一句话」内部凑合，跨场景累计误差会肉眼可见。

### 3. 原文要提炼，不要整段贴板

把原文段落转成「标题 + 3–5 条要点」的知识卡：

- 每条 ≤ 40 字
- 公式、权重、阈值、默认值必须保留
- 一份原文 → 一张卡，信息不减，阅读负担大减

**代码例外**：代码必须逐行原样保留，不能精简、不能改写，只允许分页。

### 4. 代码行太长要整页缩字号

签名行超过 100 字符很常见。渲染前测量最长行宽度，超过安全宽度就整体缩字号（最低 14px），不要裁切、不要换行。

---

## 流程

### 步骤 1：解析源文档

从 Markdown 里切出目标小节，按 ``` 围栏解析成两类块：

- `code`：代码块（保留原始行，含空行）
- `text`：代码块之间的说明文字（去掉 HTML 标签、图片、markdown 标题符号）

输出一份 `scenes.json` 骨架。

参考实现：`scripts/extract.py`

### 步骤 2：规划场景

按「开场 → 各小节 → 收尾」排场景。每幕确定：

| 字段 | 说明 |
|---|---|
| `kind` | `hook` / `title` / `text` / `code` / `image` / `end` |
| `img` | 画布文件名 |
| `voice` | 该幕口播（**必须**，禁止占位句） |

代码块的页数：

```python
npg = max(1, (len(rows) + 17) // 18)      # 每页最多 18 行
per = (len(rows) + npg - 1) // npg         # 均分，避免最后一页只剩 2 行
```

**自检**：`每个代码块的 len(voices) == 页数`。不等就会退化成占位句，必须在生成前报错。

### 步骤 3：渲染画面

1600×1000，浅色纸底 + 细网格 + 角落 pastel。三类版式：

| 类型 | 版式 |
|---|---|
| 文字卡 | 标题 + 紫色圆点列表，字号 30，行高 48 |
| 代码页 | 深色终端（`#1E2128`），行号 + 语法高亮，字号自适应 |
| 图片页 | 白底卡片 + 细边框，居中，底部留出字幕区 |

代码高亮用正则切 token：注释 / 字符串 / 数字 / 关键字 / 标识符（后跟 `(` 的着色为函数）。中文用雅黑、ASCII 用 Consolas、emoji 用 Segoe UI Emoji，**三者混排**，否则中文注释会变方块。

参考实现：`scripts/render.py`

### 步骤 4：逐句配音

```python
sents = [x for x in re.split(r"(?<=[。！？])", text) if x.strip()]
for k, s in enumerate(sents):
    await edge_tts.Communicate(s, VOICE, rate=RATE).save(f"{idx:02d}_{k}.mp3")
# 再 concat 成整幕音频
```

### 步骤 5：字幕

ASS，`PlayResX/Y = 1600/1000`，`Microsoft YaHei`，38px，白底深字（`BorderStyle=3`），`MarginV=74`。

每句字幕的 Start/End = 该句 mp3 的实测起止。全局时间轴按「幕时长 + gap」累加。

### 步骤 6：合成

```
每幕：ffmpeg -loop 1 -i 画面.png -i 幕音频.mp3 -t (T+gap) ...
concat → withvoice.mp4
烧字幕 → voice.mp4
loudnorm 到 -16 LUFS
混 BGM（比口播低 9 dB）→ 最终 mp4
```

### 步骤 7：质检

| 项 | 方法 | 合格 |
|---|---|---|
| 同步 | 抽 3 帧，看字幕是否在讲画面上的东西 | 一致 |
| 代码口播 | 检查有无占位句 | 0 条 |
| 长行 | 抽最长签名的页 | 不裁切 |
| 中文 | 抽代码注释页 | 无方块 |
| BGM | 口播间隙 `volumedetect` | 比口播低 8–12 dB |
| 峰值 | `volumedetect` | ≤ -0.8 dB |

---

## 常见坑

| 现象 | 原因 | 解法 |
|---|---|---|
| 越到后面越不同步 | 一块一音频再均分 | 一幕一页，一页一音频 |
| 字幕比语音慢/快 | 按字数估时长 | 逐句 TTS + ffprobe 实测 |
| 代码后几页没讲解 | voices 数量 < 页数 | 生成前断言，数量必须相等 |
| 中文注释变方块 | Consolas 不含中文 | 中英 emoji 三分支混排 |
| 长签名行被裁 | 固定字号 | 测最长行，整页缩字号 |
| 最后一页只剩两行 | 18 行硬切 | 先算页数再均分 |
| BGM 盖人声 | 只按峰值估 | 按均值算，目标低 9 dB |
| 文字卡溢出 | 固定字号 | 排版前试算行数，超了缩字号 |
| ASS 字幕全丢 | Dialogue 行没换行 | 每行末尾必须 `\n` |
| 峰值 0 dB 削波 | 口播 + BGM 叠加 | `alimiter=limit=0.89:level=0` |

---

## 素材授权（必须核对）

| 素材 | 常见授权 | 能否商用 |
|---|---|---|
| BGM：Mixkit | Mixkit Free License | ✅ 可商用、免署名 |
| BGM：Pixabay | Pixabay License | ✅ 多数可商用 |
| BGM：Incompetech | CC BY 4.0 | ✅ 需署名 |
| 教程原文 / 代码 / 配图 | 看仓库 LICENSE，常见 CC BY-NC-SA | ❌ 非商用 |

**先看源仓库 LICENSE 再动手**。CC BY-NC-SA 的教程可以做个人学习视频，但不能放进商业产品。

---

## 交付

输出目录建议：

```
video-out/
├── <成片>.mp4
├── cover-bilibili-1200x900.png
├── cover-wechat-1080x1440.png
├── README.md          # 时间轴 + 授权 + 复现命令
├── scenes.json        # 场景表（含口播）
├── slides/            # 画面
├── vo/                # 逐句音频
└── subs.ass
```

**改口播只改 `scenes.json`**，然后重跑合成。TTS 目录要换名或清空，否则会跳过已存在的音频。

详细参数、ffmpeg 命令、Pillow 片段见 [reference.md](./reference.md)；可复用脚本见 [scripts/](./scripts/)。
