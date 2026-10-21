# scripts/ —— 参考实现

四个脚本，按顺序跑。都可以直接运行，但**输入内容需要你填**。

## 用法

```bash
# 0) 准备
py -3.12 -m pip install edge-tts pillow

# 1) 解析文档 → scenes.json
py -3.12 extract.py --md ../教程.md --start 8.2 --end 8.3 --out ../video-out

# 2) 填 scenes.json 里的 voice / title / points（见下）

# 3) 渲染画面
py -3.12 render.py --scenes ../video-out/scenes.json --out ../video-out/slides

# 4) 合成
py -3.12 build.py --scenes ../video-out/scenes.json --out ../video-out \
    --bgm bgm.mp3 --name 课程-01.mp4
```

## 每个脚本要改什么

### extract.py

| 位置 | 说明 |
|---|---|
| `--start` / `--end` | 截取小节；不传则整篇 |
| `pages_split(max_lines=18)` | 每页最多几行；代码字号大就调小 |

输出 `scenes.json` 的每个 `text` 场景只有 `paras`（原文段落）。**必须人工改成提炼卡**：

```json
{
  "kind": "text",
  "label": "8.2.3",
  "title": "add 做了三件事",
  "points": ["会话 ID 管理：每条记忆有明确归属", "..."],
  "voice": "..."
}
```

### render.py

| 位置 | 说明 |
|---|---|
| `header()` in `common.py` | 标签/标题字号 |
| `text_card()` | 要点字号 30、行高 48 |
| `code_page()` | 代码字号 21 起，超宽自动缩 |
| `hook_page()` | 开头钩子的两行大字 |

### build.py

| 参数 | 说明 |
|---|---|
| `--voice` | `zh-CN-YunyangNeural`（云扬）/ `zh-CN-YunxiNeural`（云希）/ `zh-CN-YunjianNeural`（云健） |
| `--rate` | 默认 `+8%`；讲得急就降到 `+3%` |
| `--gap` | 场景间隙，默认 0.7s |
| `--bgm` | 不给则无 BGM |

**改口播后必须换 `vo/` 目录或清空**，否则脚本会跳过已存在音频。

## 只用其中一部分

- 只想要文字卡：跑 extract + render 的 `text` 分支
- 只想给已有视频配字幕：跳过 render，直接改 build 的字幕段
- 不要 BGM：`--bgm` 不传

## 已知边界

- 只处理 Python 代码高亮；换语言要改 `common.py` 的 `KEYWORDS`
- 代码页固定 1600×1000、每页最多 18 行
- 图片场景需要你在 scenes.json 里手填 `src` / `maxw` / `maxh`
