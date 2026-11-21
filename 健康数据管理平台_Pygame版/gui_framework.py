"""
第九课组 · 事件驱动交互"通用框架"（从 gui.py 提取，业务已挖空）
================================================================

【这个文件是干什么的】
  它是"机制骨架"：窗口、事件队列、状态机、动画、声音、绘制、缩放。
  它不含任何业务逻辑——所有业务都通过 self.b（backend）这个唯一出口调用。
  教师讲这一个文件，学生写自己的 backend.py 接进来，就能跑自己的项目。

【对照原 gui.py 的改动】
  原 self.auth.xxx / self.data.xxx / Validator.xxx  ->  统一为 self.b.xxx
  原 save_record 的校验组装  ->  self.b.prepare_record（插槽⑦）
  原 update 里的 BMI 计算   ->  self.b.build_assessment（插槽⑧）
  原 change 里的字段 specs  ->  self.b.field_specs（插槽⑥）

============================ 注意事项（务必先读）============================

1.【本目录现状】本目录的 my_backend_template.py 已填好（接的是真实
   AuthService/DataService），main() 用 App(MyBackend()).run()，可直接运行。
   发给学生时要把这个文件换成"全 TODO 的空模板"：那样直接跑会在登录时抛
   NotImplementedError 崩溃，因为下面的 safe() 不捕获它。三种用法任选：
     a) 讲机制、要一个必定能跑的演示：把 main() 改成 App(DemoBackend()).run()；
     b) 用真实业务（本目录现状）：保持 App(MyBackend()).run()；
     c) 学生练习：先填完 my_backend_template.py 的 TODO 再跑。

2.【中文乱码】pygame 默认字体 Font(None) 不含中文字形。find_font() 会按优先级
   找中文字体；都找不到会抛 RuntimeError，需要放 assets/font.ttf 或设 HEALTH_FONT。

3.【坐标系统】所有坐标都基于固定逻辑画布 W×H = 1200×800。窗口可缩放，
   present() 负责等比缩放，logical_pos() 负责把鼠标位置换回逻辑坐标。
   改布局时记住：真实数据是中文和长字符串，字体占位比英文宽，
   之前登录框跑出卡片、统计文字溢出，都是"按理想数据排版"导致的。

4.【接口约定】self.b 是唯一业务出口，13 个插槽的签名见 backend_contract.py。
   四个真实项目里踩过的坑：
     - register 真实签名是拆开的参数，模板传 dict，要 ** 展开并过滤键；
     - get_statistics 无记录返回 None、generate_report 返回 (None,msg)，要兜底；
     - prepare_record 校验失败必须 raise ValueError('人话')，不能 return False；
     - 真实 get_user_records 返回的键是 record_type，本框架"记录查询"页用
       r.get('kind') 取值，会显示为空——这是留给学生发现的接口不一致。

5.【健康评测的边界】评测只是"数据汇总＋交互动画"：BMI 是算术，血压血糖心率
   只是读出来显示。不做疾病诊断、不判等级、不建议用药——教学原型的安全底线。

6.【学生不要改本文件】只改自己的 backend.py。框架改了，全班就对不上答案了。

7.【初始化的坑·框架】App 的 __init__ 末尾必须调 self.change('login') 才会生成登录页输入框。
   只写 self.state='login' 不够——输入框是在 change() 里经 field_specs 生成的。
   踩坑现象：首页空卡片没输入框，点"创建账号"再返回才出现（提取框架时漏过这一行）。

8.【初始化的坑·backend】backend 的 __init__ 里要先调 config.init_directories()，
   建好 data/ 和 data/reports/。漏掉后点"生成报告"会显示"保存报告失败"——
   因为 Report.save_to_file 直接 open 写文件，data/reports/ 不存在就抛
   [Errno 2] No such file or directory。原 gui.py 的 __init__ 有这一行，
   把业务搬进 backend 时容易只搬服务调用而漏掉它。注意：这条坑在 backend 文件里，
   不在本框架文件里——学生填的是 backend，改这里没用。
"""

import math                      # 正弦、isfinite：动画浮动与数值校验
import os                        # 读环境变量 HEALTH_FONT
from pathlib import Path         # 拼字体文件路径、判断文件是否存在
from array import array          # 合成提示音的音频样本缓冲区
import pygame                    # 图形库：窗口/事件/绘制/字体/声音/时钟

from my_backend_template import MyBackend   # 学生要填的业务类（当前全是 TODO，见注意事项1）

# ---- 逻辑画布尺寸与配色常量（改皮肤只需动这里）----
W, H = 1200, 800                 # 固定逻辑画布：绘制永远在这个尺寸上进行
BG = (240, 245, 250)             # 页面浅灰蓝底色 RGB
INK = (25, 44, 64)               # 主文字深蓝灰
MUTED = (93, 111, 128)           # 次要文字灰蓝
TEAL = (0, 139, 133)             # 主题青绿：主按钮/进度条/强调
WHITE = (255, 255, 255)          # 白：卡片底/主按钮文字
RED = (200, 60, 60)              # 错误提示红


# ============ 中文字体查找（机制，学生不改）============
def find_font():
    """按优先级找中文字体：环境变量 > 项目自带 > 各系统常见字体。"""
    here = Path(__file__).parent                       # 本文件所在目录
    candidates = [                                     # 候选路径，按顺序试
        os.environ.get('HEALTH_FONT', ''),             # ① 用户显式指定的环境变量
        str(here / 'assets/font.otf'),                 # ② 项目自带字体（OTF）
        str(here / 'assets/font.ttf'),                 # ③ 项目自带字体（TTF）
        # macOS 本机实际可用（已验证命中 Hiragino Sans GB）
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        '/System/Library/Fonts/PingFang.ttc',
        # Windows / Linux 常见中文字体
        'C:/Windows/Fonts/msyh.ttc',                   # 微软雅黑
        'C:/Windows/Fonts/simhei.ttf',                 # 黑体
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    ]
    for path in candidates:                            # 逐个检查路径
        if path and Path(path).is_file():              # 非空且文件真实存在
            return path                                # 找到就立即返回
    for name in ['PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
                 'Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'STHeiti']:
        path = pygame.font.match_font(name)            # 让 pygame 按字体名查
        if path:
            return path                                # 查到就返回
    raise RuntimeError('未找到中文字体：请放 assets/font.ttf 或设置环境变量 HEALTH_FONT')


# ============ 框架组件①：输入控件（机制，学生不改）============
class Field:
    """一个输入框控件。中文输入用 TEXTINPUT 接收、TEXTEDITING 显示输入法组合文本。"""

    def __init__(self, key, label, rect, value='', secret=False):
        # key: 字段名（对应业务 dict 的键）；label: 显示给用户的提示文字
        self.key, self.label, self.rect = key, label, pygame.Rect(rect)  # rect 统一转成 Rect 对象
        self.value, self.secret, self.composition = value, secret, ''   # 值/是否密码/输入法组合中的临时文字

    def event(self, event):
        """事件 -> 更新输入框内容。这是"事件驱动"最小示例：不同事件改不同状态。"""
        if event.type == pygame.TEXTINPUT:              # 输入法提交的最终文字
            self.value = (self.value + event.text)[:200]  # 追加，并限制最多 200 字
            self.composition = ''                       # 组合文字已定稿，清空
        elif event.type == pygame.TEXTEDITING:          # 输入法正在组合（拼音未选字）
            self.composition = event.text               # 暂存组合文字，用于显示
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]                # 退格：删最后一个字
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DELETE:
            self.value = ''                             # Delete：清空整个输入

    def draw(self, app, focused):
        """把输入框画到 app.canvas 上；focused 表示它是否是当前焦点。"""
        app.text(self.label, (self.rect.x, self.rect.y - 27), 18, MUTED)     # 标签画在框上方
        pygame.draw.rect(app.canvas, WHITE, self.rect, border_radius=9)      # 白色圆角底
        pygame.draw.rect(app.canvas, TEAL if focused else (203, 216, 228),  # 焦点时青绿边框
                         self.rect, 2, border_radius=9)                     # 线宽 2，圆角
        value = '•' * len(self.value) if self.secret else self.value         # 密码用圆点遮盖
        if focused and self.composition:                                     # 输入法组合中的文字也要显示
            value += ('•' * len(self.composition) if self.secret else self.composition)
        if focused and pygame.time.get_ticks() // 500 % 2 == 0:              # 每 500ms 闪烁一次光标
            value += '|'
        while value and app.font(20).size(value)[0] > self.rect.width - 24:  # 文字太宽就从头裁掉
            value = value[1:]                                                # 保证不溢出输入框
        app.text(value, (self.rect.x + 12, self.rect.y + 12), 20)            # 最终把值画进框内


# ============ 框架组件②：应用主类（机制，学生不改）============
class App:
    """登录→总览→录入/查询/统计/报告/评测 的状态机。业务全部走 self.b。"""

    def __init__(self, backend):
        self.b = backend                      # ← 唯一的业务出入口（插槽总线）
        pygame.mixer.pre_init(22050, -16, 1, 512)  # 音频预初始化：采样率/位宽/声道/缓冲
        pygame.init()                         # 初始化所有 pygame 模块
        self.window = pygame.display.set_mode((W, H), pygame.RESIZABLE)  # 真实窗口，可缩放
        pygame.display.set_caption('交互框架 · 学生业务版')               # 窗口标题
        self.canvas = pygame.Surface((W, H))  # 逻辑画布：绘制永远在固定尺寸上，与窗口大小解耦
        self.clock = pygame.time.Clock()      # 时钟：控制帧率、产生 dt
        self.font_path = find_font()          # ← 中文字体路径（见注意事项2）
        self.fonts = {}                       # 字体缓存：size -> Font 对象，避免重复创建
        self.running, self.state = True, 'login'  # 主循环开关 / 当前状态（初始在登录页）
        self.fields, self.focus, self.buttons = [], 0, []  # 输入框列表 / 焦点下标 / 上一帧按钮命中区
        self.toast, self.toast_until, self.toast_error = '', 0, False  # 提示条文字/到期时间/是否错误
        self.record_kind, self.page = '体检', 0   # 当前录入类型 / 记录查询页码
        self.report_lines, self.report_offset = [], 0  # 报告分行内容 / 滚动偏移
        self.assessing, self.progress, self.result = False, 0.0, None  # 评测中/进度0~1/结果文字
        self.actor = pygame.Vector2(805, 420)  # 评测角色的逻辑坐标（向量便于方向计算）
        self.pointer = (805, 420)             # 记录鼠标最后一次点击的逻辑坐标
        self.viewport = pygame.Rect(0, 0, W, H)  # 逻辑画布在真实窗口中的显示区域
        self.sound_enabled, self.sounds = True, {}  # 声音开关 / 合成音效字典
        self.make_sounds()                    # 生成提示音；无声卡会自动降级
        self.change('login')                  # ★ 关键：初始化登录页输入框（漏掉会导致首页无输入框，
                                             #   点"注册"再返回才有——因为只有 change() 才调 field_specs 生成字段）

    # ---------- 绘制原语（所有页面共用的积木）----------
    def font(self, size):
        """按字号取字体对象，带缓存；加载失败退回默认字体兜底。"""
        if size not in self.fonts:            # 该字号还没缓存过
            try:
                self.fonts[size] = pygame.font.Font(self.font_path, size)  # 中文
            except Exception:                 # 字体文件损坏等异常
                self.fonts[size] = pygame.font.Font(None, size)            # 兜底（可能无中文）
        return self.fonts[size]               # 返回可复用的 Font 对象

    def text(self, value, pos, size=20, color=INK):
        """把一段文字画到逻辑画布；任何值都先 str() 再渲染。"""
        self.canvas.blit(self.font(size).render(str(value), True, color), pos)  # render 生成文字图，blit 贴上去

    def wrap(self, value, width, size=19):
        """按像素宽度把长文本折行（中文逐字测量，不按字数猜）。"""
        lines, line = [], ''                  # lines: 已完成的行；line: 当前行
        for char in str(value):               # 逐字处理
            if char == '\n':                  # 显式换行符
                lines.append(line); line = '' # 收起当前行，开始新行
            elif self.font(size).size(line + char)[0] > width:  # 加上这个字会超宽
                lines.append(line); line = char                 # 当前行收起，该字成为新行开头
            else:
                line += char                  # 没超宽，继续拼
        return lines + [line]                 # 别忘了最后一行

    def paragraph(self, value, pos, width, size=19, max_lines=8, color=INK):
        """画一段自动折行的文字，最多 max_lines 行，行距 size+9。"""
        for i, line in enumerate(self.wrap(value, width, size)[:max_lines]):  # 折行后截断
            self.text(line, (pos[0], pos[1] + i * (size + 9)), size, color)   # 逐行下移绘制

    def card(self, rect):
        """画一张白色圆角卡片（信息卡片的"形状"）。"""
        pygame.draw.rect(self.canvas, WHITE, rect, border_radius=16)  # 圆角 16 的大卡片

    def button(self, label, rect, action, primary=False):
        """画按钮并把 (命中区, 回调函数) 记入 self.buttons，供点击时查找。"""
        rect = pygame.Rect(rect)                       # 规整成 Rect
        pos = self.logical_pos(pygame.mouse.get_pos()) # 鼠标屏幕坐标 -> 逻辑坐标
        color = TEAL if primary else (226, 237, 245)   # 主按钮青绿，次按钮浅蓝
        if rect.collidepoint(pos):                     # 鼠标悬停时变色（交互反馈）
            color = (0, 117, 113) if primary else (204, 223, 235)
        pygame.draw.rect(self.canvas, color, rect, border_radius=9)      # 按钮底
        txt = self.font(18).render(label, True, WHITE if primary else INK)  # 按钮文字
        self.canvas.blit(txt, txt.get_rect(center=rect.center))          # 文字居中
        self.buttons.append((rect, action))            # ★ 关键：记录命中区与回调，点击事件靠它触发

    # ---------- 音效与消息（机制）----------
    def make_sounds(self):
        """合成短音，不依赖外部音频；无声卡时自动降级。"""
        if not pygame.mixer.get_init():       # 音频设备没初始化成功
            self.sound_enabled = False        # 关闭声音，后面不播
            return
        for name, hz in [('ok', 660), ('error', 220), ('done', 880)]:  # 三种音：成功/错误/完成
            samples = array('h', [int(6000 * math.sin(2 * math.pi * hz * i / 22050) * (1 - i / 3300))
                                  for i in range(3300)])               # 用正弦+衰减包络合成短音样本
            self.sounds[name] = pygame.mixer.Sound(buffer=samples.tobytes())  # 生成 Sound 对象

    def notify(self, message, error=False):
        """底部弹出提示条；error=True 显示红色并播错误音。"""
        self.toast, self.toast_error = message, error   # 存提示文字与是否错误
        self.toast_until = pygame.time.get_ticks() + 6500  # 6.5 秒后自动消失
        if self.sound_enabled and self.sounds:          # 有声音才播
            self.sounds['error' if error else 'ok'].play()  # 错误/成功音

    def safe(self, operation, *args):
        """异常兜底：业务抛错不让界面崩（注意不捕获 NotImplementedError，见注意事项1）。"""
        try:
            operation(*args)                           # 正常执行传入的函数
        except (ValueError, OSError, KeyError, TypeError) as exc:  # 只捕获这四类常见业务异常
            self.notify(str(exc), True)                # 转成红色提示条显示给用户

    # ---------- 状态机（机制）----------
    def change(self, state):
        """切换页面状态：重建输入框与焦点，重置分页/滚动，必要时重置动画。"""
        self.state, self.fields, self.focus = state, [], 0  # 新状态；清空输入框；焦点归零
        self.page, self.report_offset = 0, 0             # 换页后回到第一页、报告滚到顶
        specs = self.b.field_specs(state, self.record_kind)   # 插槽⑥：向业务要该页的字段规格
        # 登录/注册：居中卡片内单列；录入页：右侧双列。按页面分别排版（历史踩过溢出的坑）。
        for i, (key, label, default, secret) in enumerate(specs):
            if state in ('login', 'register'):
                rect = (380, 330 + i * 78, 440, 48)    # 单列：x 固定，y 每 78 递增
            else:
                rect = (270 + (i % 2) * 440, 240 + (i // 2) * 100, 400, 48)  # 双列：两列交替
            self.fields.append(Field(key, label, rect, default, secret))  # 生成控件
        if self.fields:                                # 有输入框
            pygame.key.start_text_input()              # 开启文本输入（支持中文输入法）
        else:                                          # 没有输入框
            pygame.key.stop_text_input()               # 关闭文本输入
        if state == 'assessment':                      # 进入评测页要重置动画状态
            self.progress, self.assessing, self.result = 0, False, None  # 进度归零、未在评测、结果清空
            self.actor.update(805, 420)                # 角色回到初始位置

    def values(self):
        """把所有输入框的值收集成 dict（键是 Field.key），供业务层使用。"""
        return {f.key: f.value.strip() for f in self.fields}  # strip 去掉首尾空白

    # ---------- 业务调用点（插槽①②③④⑤，框架只转发，不含业务规则）----------
    def submit(self):
        """回车/点提交按钮：按当前状态把收集到的值转发给对应的业务接口。"""
        values = self.values()                          # 先收集表单值
        if self.state == 'login':                       # 登录页
            ok, msg = self.b.login(values['username'], values['password'])  # 插槽①：调业务登录
            if ok:                                      # 登录成功
                self.change('dashboard')                # 切到总览页
        elif self.state == 'register':                  # 注册页
            ok, msg = self.b.register(values)           # 插槽①：注册（注意真实签名要 ** 展开）
            if ok:                                      # 注册成功
                self.change('login')                    # 回到登录页
                if self.fields:                         # 把用户名预填回登录框，省得重打
                    self.fields[0].value = values['username']
        elif self.state == 'add':                       # 录入页
            self.save_record(values)                    # 交给 save_record 处理
            return                                      # save_record 自己会 notify，这里直接返回
        self.notify(msg, not ok)                        # 用业务返回的 msg 弹提示（失败为红）

    def save_record(self, values):
        """录入一条记录：先让业务校验组装，再调业务保存（界面不碰校验细节）。"""
        kind, value, payload = self.b.prepare_record(values, self.record_kind)  # 插槽⑦：校验+组装
        user_id = self.b.get_current_user().user_id      # 从业务拿当前用户 id
        ok, msg = self.b.add_record(user_id, kind, values['record_date'], value, **payload)  # 插槽②：保存
        if ok:                                          # 保存成功
            self.change('records')                      # 跳到记录查询页看结果
        self.notify(msg, not ok)                        # 弹提示

    def export(self):
        """导出 CSV：业务负责写文件，界面只传路径并显示结果。"""
        ok, msg = self.b.export_to_csv(self.b.get_current_user().user_id, 'records.csv')  # 插槽④
        self.notify(msg, not ok)

    def report(self):
        """生成报告：业务返回 report 对象（需有 .content），界面负责折行显示。"""
        report, msg = self.b.generate_report(self.b.get_current_user().user_id,  # 插槽⑤
                                             self.b.get_current_user().username)
        if report:                                      # 无记录时业务可能返回 None，这里判空
            self.report_lines = [x for raw in report.content.splitlines() for x in self.wrap(raw, 820, 19)]
            self.change('report')                       # 切到报告页
        self.notify(msg, not bool(report))              # report 为空则红色提示

    def logout(self):
        """退出登录：调业务登出，回登录页，清掉报告缓存。"""
        self.b.logout()                                 # 业务清当前用户
        self.change('login')                            # 回登录页
        self.report_lines = []                          # 清报告，避免下一个用户看到

    # ---------- 动画（机制：dt 时间步长，帧率无关）----------
    def start_assessment(self):
        """启动评测：先检查有无体检记录，再置动画初值。"""
        if not self.user_records('体检'):               # 没有体检记录
            self.notify('请先添加一条体检记录，再开始评测', True)  # 红字提示，不启动
            return
        self.progress, self.assessing, self.result = 0, True, None  # 进度0、开启动画、清空结果

    def update(self, dt):
        """每帧更新：只在评测页工作。dt 是本帧耗时（秒），保证动画与帧率无关。"""
        if self.state == 'assessment':                  # 不在评测页什么都不做
            keys = pygame.key.get_pressed()             # 取当前按住的所有键（长按移动）
            direction = pygame.Vector2(int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT]),
                                       int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP]))  # 方向向量（右-左, 下-上）
            if direction.length_squared():              # 有按键才移动
                self.actor += direction.normalize() * 230 * dt  # 位移=速度230×dt，斜向不加速
            self.actor.x = max(720, min(1070, self.actor.x))  # 限制角色活动范围 x
            self.actor.y = max(320, min(520, self.actor.y))   # 限制角色活动范围 y
            if self.assessing:                          # 正在评测（动画推进中）
                self.progress = min(1.0, self.progress + dt / 2.4)  # 2.4 秒走完，与帧率无关
                if self.progress >= 1:                  # 进度满了——这一帧才真正"评测"
                    self.result = self.b.build_assessment(self.user_records('体检'))  # 插槽⑧：业务计算结果
                    self.assessing = False              # 停止动画
                    self.notify('评测完成：结果面板已更新')  # 弹提示
                    if self.sound_enabled and self.sounds:  # 播完成音
                        self.sounds['done'].play()

    # ---------- 事件分发（机制）----------
    def logical_pos(self, pos):
        """窗口可缩放：把屏幕鼠标坐标换算回 1200×800 逻辑画布坐标。"""
        return ((pos[0] - self.viewport.x) * W / self.viewport.width,
                (pos[1] - self.viewport.y) * H / self.viewport.height)

    def handle(self, event):
        """事件分发总入口：一个 if/elif 链，每种事件改一点状态。这是"事件驱动"的核心。"""
        if event.type == pygame.QUIT:                   # 点窗口关闭按钮
            self.running = False                        # 停主循环
        elif event.type == pygame.VIDEORESIZE:          # 用户拖动改变窗口大小
            self.window = pygame.display.set_mode((max(640, event.w), max(480, event.h)), pygame.RESIZABLE)
            self.present()                              # 立即重绘一次，避免闪烁
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 鼠标左键
            pos = self.logical_pos(event.pos)           # 换算成逻辑坐标
            self.pointer = pos                          # 记录点击位置
            for i, field in enumerate(self.fields):     # 先看点没点到输入框
                if field.rect.collidepoint(pos):        # 命中输入框
                    self.focus = i; break               # 设焦点并跳出
            for rect, action in list(self.buttons):     # 再看点没点到按钮（用上一帧记录的命中区）
                if rect.collidepoint(pos):              # 命中按钮
                    action(); break                     # 调用按钮绑定的回调函数
        elif event.type == pygame.MOUSEWHEEL:           # 鼠标滚轮
            if self.state == 'report':                  # 只在报告页滚动
                self.report_offset = max(0, self.report_offset - event.y * 3)  # 下限 0，防滚过头
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:  # Esc
            if self.b.is_logged_in():                   # 已登录才回总览
                self.change('dashboard')
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB and self.fields:  # Tab 切焦点
            self.fields[self.focus].composition = ''    # 清掉输入法组合文字
            self.focus = (self.focus + (-1 if event.mod & pygame.KMOD_SHIFT else 1)) % len(self.fields)  # Shift+Tab 反向，取模循环
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.fields:  # 回车提交
            if not self.fields[self.focus].composition: # 输入法正在选字时不能提交
                self.submit()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.state == 'assessment':  # 空格启动评测
            self.start_assessment()
        elif self.fields:                               # 其余键盘事件交给当前输入框（文本输入）
            self.fields[self.focus].event(event)

    def user_records(self, kind=None):
        """取当前用户的记录（框架内部小工具，转发给业务）。"""
        return self.b.get_user_records(self.b.get_current_user().user_id, kind)

    # ---------- 绘制（机制 + 通用页面，学生可换皮肤）----------
    def draw(self):
        """每帧重画整个界面：先分登录页/已登录页，再叠加表单与提示条。"""
        self.canvas.fill(BG)                            # 清屏：整张逻辑画布刷底色
        self.buttons = []                               # ★ 清空上一帧按钮命中区（button() 会重新登记）
        if not self.b.is_logged_in():                   # ---------- 登录/注册页 ----------
            # 卡片高度按字段数伸缩：注册比登录多两个选填项
            card_h = max(420, 250 + len(self.fields) * 78 + 80)  # 字段越多卡片越高
            self.card((330, 150, 540, card_h))          # 居中白卡片
            self.text('交互框架 · 学生业务版', (365, 185), 30)  # 标题
            for i, f in enumerate(self.fields):         # 画所有输入框
                f.draw(self, i == self.focus)           # 当前焦点框高亮
            btn_y = 330 + len(self.fields) * 78 + 10    # 按钮 y 随字段数下移，避免压到输入框
            self.button('登录' if self.state == 'login' else '注册',  # 主按钮文案随状态变
                        (380, btn_y, 200, 48), self.submit, True)    # 点它调 submit
            self.button('创建账号' if self.state == 'login' else '返回登录',  # 次按钮：登录↔注册切换
                        (600, btn_y, 210, 48),
                        lambda: self.change('register' if self.state == 'login' else 'login'))
            self.text('用 Tab 切换 · Enter 提交 · 支持中文输入', (365, btn_y + 62), 16, MUTED)  # 操作提示
        else:                                           # ---------- 已登录：左侧导航 + 内容区 ----------
            pygame.draw.rect(self.canvas, INK, (0, 0, 220, H))  # 深色侧边栏
            self.text('数据平台', (23, 30), 25, WHITE)  # 侧栏标题
            self.text(self.b.get_current_user().username[:10], (24, 80), 19, (166, 204, 218))  # 用户名（截短）
            nav = [('总览', 'dashboard'), ('添加记录', 'add'), ('记录查询', 'records'),
                   ('分类统计', 'stats'), ('健康评测', 'assessment')]  # 导航项：显示名 -> 状态名
            for i, (label, state) in enumerate(nav):    # 逐个画导航按钮
                self.button(label, (20, 140 + i * 60, 180, 44), lambda s=state: self.change(s), self.state == state)
            self.button('导出 CSV', (20, 465, 180, 44), self.export)    # 功能按钮
            self.button('生成报告', (20, 520, 180, 44), self.report)
            self.button('退出登录', (20, 575, 180, 44), self.logout)
            titles = {'dashboard': '数据总览', 'add': '添加记录', 'records': '记录查询',
                      'stats': '分类统计', 'assessment': '健康评测交互原型', 'report': '报告预览'}
            self.text(titles.get(self.state, ''), (260, 38), 30)  # 内容区大标题
            self.draw_content()                         # 画当前页面的具体内容
        # 表单与提示（所有页面通用）
        if self.b.is_logged_in():                       # 已登录页的输入框（录入表单）也在这里统一画
            for i, field in enumerate(self.fields):
                field.draw(self, i == self.focus)
        if self.toast and pygame.time.get_ticks() < self.toast_until:  # 提示条还没过期
            color = RED if self.toast_error else TEAL   # 错误红、成功青绿
            pygame.draw.rect(self.canvas, color, (240, 700, 940, 48), border_radius=10)  # 底部条
            self.paragraph(self.toast, (255, 710), 910, 16, max_lines=1, color=WHITE)    # 单行文字

    def draw_content(self):
        """按 state 画内容区：每个 elif 是一个页面。学生可换皮肤，但不改业务调用。"""
        if self.state == 'dashboard':                   # ---------- 总览页：三张计数卡片 ----------
            records = self.user_records()               # 取全部记录
            counts = [('全部记录', len(records)),       # 统计三类数量
                      ('体检', len(self.user_records('体检'))),
                      ('用药', len(self.user_records('用药')))]
            for i, (label, n) in enumerate(counts):     # 画三张卡片
                x = 260 + i * 300                       # 横向排列
                self.card((x, 130, 270, 130))           # 白卡片
                self.text(label, (x + 24, 155), 20, MUTED)  # 卡名
                self.text(str(n), (x + 24, 190), 44, TEAL)  # 大数字
        elif self.state == 'add':                       # ---------- 录入页：一张大卡片＋提交按钮 ----------
            self.card((260, 130, 880, 520))             # 表单背景卡（输入框由 draw() 统一画）
            self.button('提交记录', (270, 620, 220, 48), lambda: self.save_record(self.values()), True)
        elif self.state == 'records':                   # ---------- 记录查询页：每页 6 条 ----------
            records = self.user_records()               # 取记录
            shown = records[self.page * 6:self.page * 6 + 6]  # 切片：当前页的 6 条
            for i, r in enumerate(shown):               # 逐条画成卡片
                self.card((260, 130 + i * 88, 880, 78)) # 卡片高度 78，间距 88
                # 注意：真实数据的类型键是 record_type，这里用 kind 会显示为空（见注意事项4）
                self.text(f"{r.get('record_date', '')}  {r.get('kind', '')}", (284, 145 + i * 88), 20)
                self.text(str(r.get('value', ''))[:40], (284, 174 + i * 88), 17, MUTED)  # value 截 40 字防溢出
            self.button('下一页', (960, 650, 160, 44), lambda: setattr(self, 'page', self.page + 1))  # 翻页
        elif self.state == 'stats':                     # ---------- 分类统计页 ----------
            stats = self.b.get_statistics(self.b.get_current_user().user_id, self.record_kind)  # 插槽③
            items = list(stats.items()) if hasattr(stats, 'items') else list(enumerate(stats))  # 兼容 dict/列表
            if not items:                               # 无数据
                self.text('暂无统计数据，请先添加记录', (270, 160), 22, MUTED)
            for i, (k, v) in enumerate(items):          # 每个指标一张卡
                col, row = i % 3, i // 3                # 3 列排布
                x, y = 260 + col * 300, 130 + row * 140 # 卡片左上角
                self.card((x, y, 280, 125))             # 白卡片
                self.text(str(k), (x + 20, y + 14), 19, MUTED)  # 指标名
                # 真实统计值是长串（"最新 x | 均值 y | 范围 z-w"），按 | 拆行、小字显示，防溢出
                for j, line in enumerate([s.strip() for s in str(v).split('|') if s.strip()][:4]):
                    self.text(line, (x + 20, y + 46 + j * 22), 15, TEAL)  # 每行下移 22
        elif self.state == 'assessment':                # ---------- 健康评测页 ----------
            bob = math.sin(pygame.time.get_ticks() / 180) * 5 if self.assessing else 0  # 正弦上下浮动 ±5
            cx, cy = int(self.actor.x), int(self.actor.y + bob)         # 角色位置（向量转整数）
            pygame.draw.circle(self.canvas, BLUE := (53, 104, 193), (cx, cy), 26)  # 蓝色实心圆角色
            if self.assessing:                          # 评测中：外圈脉冲动画
                pygame.draw.circle(self.canvas, TEAL, (cx, cy), int(34 + 5 * math.sin(pygame.time.get_ticks() / 120)), 2)
            pygame.draw.rect(self.canvas, (220, 230, 238), (730, 565, 400, 18), border_radius=9)  # 进度条底槽
            if self.progress:                           # 有进度才画填充部分
                pygame.draw.rect(self.canvas, TEAL, (730, 565, int(400 * self.progress), 18), border_radius=9)
            self.text(f"评测进度：{int(self.progress * 100)}%", (730, 593), 18, MUTED)  # 百分比文字
            self.button('开始 / 重新评测', (730, 630, 230, 40), self.start_assessment, True)  # 启动按钮
            for i, line in enumerate(self.result or []):  # 逐行画业务返回的结果（7 行）
                self.text(line, (730, 120 + i * 34), 18)  # 行距 34
        elif self.state == 'report':                    # ---------- 报告预览页 ----------
            for i, line in enumerate(self.report_lines[self.report_offset:self.report_offset + 17]):  # 只画可见 17 行
                self.text(line, (270, 130 + i * 30), 18)  # 行距 30

    def present(self):
        """逻辑画布 -> 实际窗口，等比缩放并居中；鼠标坐标同步换算（见 logical_pos）。"""
        sw, sh = self.window.get_size()                 # 当前真实窗口尺寸
        scale = min(sw / W, sh / H)                     # 取较小比例，保证不变形、不裁切
        size = (max(1, int(W * scale)), max(1, int(H * scale)))  # 缩放后的画布尺寸
        self.viewport = pygame.Rect((sw - size[0]) // 2, (sh - size[1]) // 2, *size)  # 居中显示区域
        self.window.fill((18, 32, 48))                  # 窗口背景（画布外的留白）
        self.window.blit(pygame.transform.smoothscale(self.canvas, size), self.viewport)  # 平滑缩放贴上
        pygame.display.flip()                           # 一次性刷新显示（双缓冲）

    def run(self):
        """主循环：取事件 -> 分发 -> 更新 -> 绘制 -> 刷新。动画不阻塞事件。"""
        try:
            while self.running:                          # 只要 running 为 True 就一直转
                dt = min(self.clock.tick(60) / 1000, 0.05)  # tick(60) 限制最高 60 帧；dt 秒；上限 0.05 防切后台后跳变
                for event in pygame.event.get():          # 取出这一帧所有事件
                    self.safe(self.handle, event)         # 逐个分发（出错弹提示，不崩）
                self.safe(self.update, dt)                # 更新动画/状态
                self.safe(self.draw)                      # 画到逻辑画布
                self.present()                            # 缩放刷到真实窗口
        finally:
            pygame.quit()                                 # 无论正常退出还是异常，都释放 pygame


# ============ 演示用假业务（讲框架时先跑它；学生换成自己的）============
class DemoBackend:
    """只为了让框架能跑的假数据，学生用你的真实业务替换它（见注意事项1的切换方法）。"""

    def __init__(self):
        self.user = None                                 # 当前用户（模拟）
        self.records = []                                # 记录列表（内存，不落盘）

    def login(self, username, password):
        if username and password:                        # 只要账号密码非空就通过（假逻辑）
            self.user = type('U', (), {'user_id': 'demo', 'username': username})()  # 动态造个用户对象
            return True, '登录成功'
        return False, '请输入用户名和密码'

    def register(self, values):
        return True, '注册成功，请登录'                  # 假注册：永远成功

    def logout(self):
        self.user = None                                 # 清空当前用户

    def get_current_user(self):
        return self.user                                 # 返回用户对象或 None

    def is_logged_in(self):
        return self.user is not None                     # 有用户对象即已登录

    def add_record(self, user_id, kind, record_date, value, **payload):
        self.records.append({'record_date': record_date, 'kind': kind, 'value': value, **payload})  # 存内存
        return True, '记录已保存'

    def get_user_records(self, user_id, kind=None):
        return [r for r in self.records if kind is None or r['kind'] == kind]  # 按类型过滤

    def get_statistics(self, user_id, kind):
        return {'记录条数': len(self.records)}           # 假统计：只有条数

    def export_to_csv(self, user_id, path):
        return True, f'已导出：{path}'                   # 假导出：不真写文件

    def generate_report(self, user_id, username):
        report = type('R', (), {'content': '演示报告\n共 %d 条记录' % len(self.records)})()  # 造个有 .content 的对象
        return report, '报告已生成'

    def prepare_record(self, values, kind):
        payload = dict(values)                           # 复制一份表单值
        payload.pop('record_date', None)                 # 日期单独传，不进 payload
        value = payload.pop('height', '') or payload.pop('medicine_name', '') or '示例记录'  # 编一个 value
        return kind, str(value), payload                 # 返回 (类型, 值, 附加字段)

    def build_assessment(self, records):
        return ['评测结果（演示数据）', f'体检记录：{len(records)} 条', '仅作数据汇总，不作诊断。']  # 假结果 3 行

    def field_specs(self, state, record_kind):
        defaults = {
            'login': [('username', '用户名', '', False), ('password', '密码', '', True)],
            'register': [('username', '用户名', '', False), ('password', '密码', '', True)],
            'add': [('record_date', '日期', '2026-01-01', False),
                    ('height', '身高 cm', '', False), ('weight', '体重 kg', '', False)],
        }
        return defaults.get(state, [])                   # 没有的状态返回空列表


def main():
    # ★ 切换后端就改这一行（详见文件顶部注意事项1）：
    #   App(DemoBackend()).run()       -> 假数据，保证能跑，讲机制用
    #   App(MyBackend()).run()         -> 学生填完模板后用
    #   from my_backend_filled import MyBackend -> 用真实项目业务
    App(MyBackend()).run()   # 当前：用学生 backend（模板未填会崩，请先按注意事项1处理）


if __name__ == '__main__':
    main()                                               # 脚本直接运行时才启动
