# 3.1 装饰器：给函数套一层

装饰器不是语法糖，它就是一个「接收函数、返回函数」的普通函数。理解这一点，`@` 符号就没有秘密了。

## 3.1.1 最朴素的写法

先把一个函数装进另一个函数里，手动调用：

```python
import time

def timer(fn):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        cost = time.perf_counter() - start
        print(f"{fn.__name__} 耗时 {cost:.3f}s")
        return result
    return wrapper

def work(n):
    total = 0
    for i in range(n):
        total += i * i
    return total

work = timer(work)
work(1000)
```

注意 `wrapper` 里的 `*args, **kwargs`：没有它，被装饰的函数就不能带参数。这是最常见的漏写。

## 3.1.2 换成 @ 语法

`@timer` 等价于 `work = timer(work)`，只发生在定义函数的那一瞬间，不是调用时。

```python
@timer
def work(n):
    total = 0
    for i in range(n):
        total += i * i
    return total

work(1000)
```

等价关系的三个细节：装饰时机在定义时、返回值必须可调用、原函数名会被覆盖。

## 3.1.3 带参数的装饰器

三层嵌套：最外层收装饰器参数，中间层收函数，最内层收调用参数。

```python
def retry(times=3, delay=0.5):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            last = None
            for i in range(times):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last = e
                    time.sleep(delay)
            raise last
        return wrapper
    return decorator

@retry(times=5, delay=0.2)
def fetch(url):
    return requests.get(url, timeout=3).json()
```

## 3.1.4 别丢掉元信息

`wrapper` 会覆盖原函数的 `__name__`、`__doc__`。用 `functools.wraps` 复制回去：

```python
from functools import wraps

def timer(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper
```

不加 `wraps`，日志里所有函数都叫 `wrapper`，排查问题会浪费很多时间。
