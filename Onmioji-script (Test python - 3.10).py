import time
import random
import math
import threading

try:
    import pyautogui
    import keyboard
except Exception as e:
    raise SystemExit("缺少依赖，请安装：pip install pyautogui keyboard") from e

# ======================================================================
#        点击区域：在按下 F8 时由鼠标位置确定为 40×40 区域
# ======================================================================
CLICK_AREA = None  # 动态生成

def set_click_area(center):
    cx, cy = center
    return {
        "xmin": cx - 20,
        "xmax": cx + 20,
        "ymin": cy - 20,
        "ymax": cy + 20,
    }

# ======================================================================
#        Perlin 噪声（纯 Python）
# ======================================================================
class Perlin1D:
    def __init__(self, seed=None):
        self.gradients = {}
        if seed is not None:
            random.seed(seed)

    def _gradient(self, x):
        if x not in self.gradients:
            self.gradients[x] = random.uniform(-1, 1)
        return self.gradients[x]

    def _fade(self, t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    def noise(self, x):
        x0 = int(math.floor(x))
        x1 = x0 + 1
        t = x - x0
        g0 = self._gradient(x0)
        g1 = self._gradient(x1)
        d0 = g0 * (x - x0)
        d1 = g1 * (x - x1)
        return d0 + self._fade(t) * (d1 - d0)

# 鼠标按键延迟（Perlin 控制，秒）
perlin = Perlin1D(seed=2333)
_perlin_t = 0.0
interval_min = 0.000033
interval_max = 0.6003

# 键盘按键延迟（Perlin 控制，秒）
key_delay_min = 7.777
key_delay_max = 67.223

def get_perlin_interval():
    global _perlin_t
    _perlin_t += random.uniform(0.07, 0.37)
    n = perlin.noise(_perlin_t)
    return interval_min + (n + 1) / 2 * (interval_max - interval_min)

def get_perlin_key_delay():
    global _perlin_t
    _perlin_t += random.uniform(0.11, 0.41)
    n = perlin.noise(_perlin_t)
    return key_delay_min + (n + 1) / 2 * (key_delay_max - key_delay_min)

# ======================================================================
#                 区域几何工具与贝塞尔
# ======================================================================
def clamp_point(pt, area):
    x = max(area["xmin"], min(pt[0], area["xmax"]))
    y = max(area["ymin"], min(pt[1], area["ymax"]))
    return (x, y)

def random_point(area):
    return (
        random.uniform(area["xmin"], area["xmax"]),
        random.uniform(area["ymin"], area["ymax"]),
    )

def safe_ctrl(area, base, jitter=10):
    x = base[0] + random.uniform(-jitter, jitter)
    y = base[1] + random.uniform(-jitter, jitter)
    return clamp_point((x, y), area)

def bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return (
        u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
    )

# ======================================================================
#                 贝塞尔曲线移动（严格区域内）
# ======================================================================
def human_like_move(start, end, area, steps=32):
    ctrl1 = safe_ctrl(area, start, jitter=10)
    ctrl2 = safe_ctrl(area, end, jitter=10)
    for i in range(steps):
        t = (i + 1) / steps
        t2 = t * t * (3 - 2 * t)  # smoothstep
        x, y = bezier(start, ctrl1, ctrl2, end, t2)
        x += random.gauss(0, 0.4)
        y += random.gauss(0, 0.4)
        x, y = clamp_point((x, y), area)
        pyautogui.moveTo(x, y, duration=0)
        time.sleep(random.uniform(0.0007, 0.0037))

# ======================================================================
#                            连点线程
# ======================================================================
clicking = False
click_thread = None
key_thread = None

def click_loop(area):
    global clicking
    while clicking:
        cur = pyautogui.position()
        cur = clamp_point(cur, area)
        target = random_point(area)
        human_like_move(cur, target, area, steps=random.randint(7, 17))
        tx, ty = int(target[0]), int(target[1])
        pyautogui.click(tx, ty)
        time.sleep(get_perlin_interval())

def key_loop():
    global clicking
    while clicking:
        delay = get_perlin_key_delay()
        time.sleep(delay)
        keyboard.press('1')
        time.sleep(random.uniform(0.003, 0.01967))
        keyboard.release('1')

# ======================================================================
#                            热键控制
# ======================================================================
def start_clicking():
    global clicking, click_thread, key_thread, CLICK_AREA
    if clicking:
        return

    center = pyautogui.position()
    CLICK_AREA = set_click_area(center)
    print(f"启动，限制区域：{CLICK_AREA}")

    clicking = True

    # 鼠标线程
    click_thread = threading.Thread(target=click_loop, args=(CLICK_AREA,), daemon=True)
    click_thread.start()

    # 键盘线程
    key_thread = threading.Thread(target=key_loop, daemon=True)
    key_thread.start()

def stop_clicking():
    global clicking
    clicking = False
    print("已停止")

# 注册热键
keyboard.add_hotkey("f8", start_clicking)
keyboard.add_hotkey("esc", stop_clicking)

print("按 F8 启动（以当前位置为中心 40×40 区域）。按 ESC 停止。")
print("也可以在模拟器中设置“1”作为模拟按键，并自行调整位置")

while True:
    time.sleep(1)
