# -*- coding: utf-8 -*-
"""给 extract.py 生成的 scenes.json 填 label / title / points / voice。

示例用：装饰器一节。真实项目里这一步人工改，或让模型按 SKILL.md 的
「标题 + 3~5 条要点」规则生成。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
P = ROOT / "scenes.json"
S = json.loads(P.read_text(encoding="utf-8"))

FILL = {
    0: dict(sub="装饰器，到底在做什么？"),
    1: dict(
        label="3.1.1",
        title="装饰器就是一个普通函数",
        points=[
            "接收一个函数，返回一个新函数",
            "wrapper 里先做额外的事，再调用原函数",
            "手动写 work = timer(work) 也算装饰",
            "关键：*args, **kwargs 不能漏",
        ],
        voice="装饰器不是语法糖，它就是一个接收函数、返回函数的普通函数。先把一个函数装进另一个函数里，手动调用，跑通了再换成 @ 语法。",
    ),
    2: dict(
        label="3.1.2",
        title="计时器：包住原函数",
        voice="这段代码做三件事：记开始时间，调用原函数，算耗时并打印。注意 wrapper 里的星号参数，没有它，被装饰的函数就不能带参数。",
    ),
    3: dict(
        label="3.1.2",
        title="手动调用一次看看",
        voice="最后一行把 work 重新赋值成 timer 的返回值，再调用。这时候打印出来的名字还是 work，但真正执行的已经是 wrapper 了。",
    ),
    4: dict(
        label="3.1.2",
        title="没写 *args 会怎样",
        points=[
            "wrapper 只收一个参数，work(1000) 直接报错",
            "原函数的参数被丢掉，调用即失败",
            "补上 *args, **kwargs 才能透传任意参数",
        ],
        voice="这是最常见的漏写。wrapper 如果只收一个参数，那被装饰的函数只要带参数就报错，因为参数根本没传进去。",
    ),
    5: dict(
        label="3.1.3",
        title="@timer 只是换了个写法",
        voice="@timer 等价于 work 等于 timer 括号 work，而且只发生在定义函数的那一瞬间。记住这一点，装饰顺序就不会搞混。",
    ),
    6: dict(
        label="3.1.3",
        title="等价关系的三个细节",
        points=[
            "装饰发生在定义时，不是调用时",
            "返回值必须可调用，否则调用即报错",
            "原函数名被覆盖，这是刻意设计",
        ],
        voice="等价关系有三个细节：装饰时机在定义时，返回值必须可调用，原函数名会被覆盖。第三条不是 bug，是装饰器能生效的前提。",
    ),
    7: dict(
        label="3.1.4",
        title="带参数的装饰器：三层嵌套",
        voice="想在装饰器上传参数，就要三层嵌套。最外层收装饰器参数，中间层收函数，最内层收调用参数。少一层，括号就对不上。",
    ),
    8: dict(
        label="3.1.5",
        title="wraps：把元信息还回去",
        voice="最后别忘了 wraps。不加它，所有被装饰的函数名字都叫 wrapper，日志和报错里全是同一个名字，排查问题会多花很多时间。",
    ),
    9: dict(
        label="3.1.5",
        title="为什么一定要 wraps",
        points=[
            "wrapper 覆盖了 __name__ 和 __doc__",
            "functools.wraps 把元信息复制回去",
            "日志、调试、文档生成都依赖它",
        ],
        voice="wraps 做的事很简单：把原函数的名字、文档、注解复制到 wrapper 上。日志、调试、文档生成，全都依赖这些元信息。",
    ),
}

for s in S:
    i = s["idx"]
    s.update(FILL.get(i, {}))
    if s["kind"] == "code" and not s.get("voice"):
        s["voice"] = s.get("title", "代码") + "。"

# 自检：每个代码块每页都要有口播
bad = [s["idx"] for s in S if s["kind"] == "code" and not s.get("voice")]
if bad:
    print("缺口播的场景:", bad)
    sys.exit(1)

P.write_text(json.dumps(S, ensure_ascii=False, indent=1), encoding="utf-8")
print("filled", len(S), "scenes")
