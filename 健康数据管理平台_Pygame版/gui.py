"""第九课组：窗口、Surface、事件队列、状态机、动画与声音。
业务层复用原 health_platform；界面不调用 input() 或阻塞式 sleep()。
"""
import math
import os
from pathlib import Path
from datetime import date, datetime
from array import array
import pygame
import config
from services.auth_service import AuthService
from services.data_service import DataService
from utils.validator import Validator

W, H = 1200, 800
BG = (240, 245, 250)
INK = (25, 44, 64)
MUTED = (93, 111, 128)
TEAL = (0, 139, 133)
BLUE = (53, 104, 193)
WHITE = (255, 255, 255)
RED = (185, 57, 66)


def find_font():
    """允许自带字体，随后查找 Windows/macOS/Linux 常见中文字体。"""
    candidates = [os.environ.get('HEALTH_FONT', ''), str(Path(__file__).parent/'assets/font.otf'), str(Path(__file__).parent/'assets/font.ttf'),
                  'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf',
                  '/System/Library/Fonts/PingFang.ttc',
                  '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']
    for path in candidates:
        if path and Path(path).is_file():
            return path
    for name in ['Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC', 'WenQuanYi Zen Hei']:
        path = pygame.font.match_font(name)
        if path:
            return path
    raise RuntimeError('未找到中文字体。请将中文字体保存为 assets/font.ttf，或设置 HEALTH_FONT。')


class Field:
    """输入控件：TEXTINPUT 接收中文提交，TEXTEDITING 显示输入法组合文本。"""
    def __init__(self, key, label, rect, value='', secret=False):
        self.key, self.label, self.rect = key, label, pygame.Rect(rect)
        self.value, self.secret, self.composition = value, secret, ''

    def event(self, event):
        if event.type == pygame.TEXTINPUT:
            self.value = (self.value + event.text)[:200]
            self.composition = ''
        elif event.type == pygame.TEXTEDITING:
            self.composition = event.text
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DELETE:
            self.value = ''

    def draw(self, app, focused):
        app.text(self.label, (self.rect.x, self.rect.y-27), 18, MUTED)
        pygame.draw.rect(app.canvas, WHITE, self.rect, border_radius=9)
        pygame.draw.rect(app.canvas, TEAL if focused else (203, 216, 228), self.rect, 2, border_radius=9)
        value = '•'*len(self.value) if self.secret else self.value
        if focused and self.composition:
            value += ('•'*len(self.composition) if self.secret else self.composition)
        if focused and pygame.time.get_ticks()//500 % 2 == 0:
            value += '|'
        # 从尾部显示，长文本不会溢出控件。
        while value and app.font(20).size(value)[0] > self.rect.width-24:
            value = value[1:]
        app.text(value, (self.rect.x+12, self.rect.y+12), 20)


class HealthApp:
    """登录→仪表盘→录入/查询/统计/报告/评测的状态机。"""
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        self.window = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        pygame.display.set_caption('健康数据管理平台 · Pygame 交互版')
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_path, self.fonts = find_font(), {}
        config.init_directories()
        self.auth, self.data = AuthService(), DataService()
        self.running, self.state = True, 'login'
        self.fields, self.focus, self.buttons = [], 0, []
        self.toast, self.toast_until, self.toast_error = '', 0, False
        self.record_kind, self.filter_kind, self.page = '体检', None, 0
        self.selected = None
        self.detail_offset = 0
        self.report_lines, self.report_offset = [], 0
        self.assessing, self.progress, self.result = False, 0.0, None
        self.actor = pygame.Vector2(805, 420)
        self.sound_enabled, self.sounds = True, {}
        self.pointer = (805,420)
        self.viewport = pygame.Rect(0, 0, W, H)
        self.make_sounds()
        self.change('login')

    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(self.font_path, size)
        return self.fonts[size]

    def text(self, value, pos, size=20, color=INK):
        self.canvas.blit(self.font(size).render(str(value), True, color), pos)

    def wrap(self, value, width, size=19):
        lines, line = [], ''
        for char in str(value):
            if char == '\n':
                lines.append(line); line = ''
            elif self.font(size).size(line+char)[0] > width:
                lines.append(line); line = char
            else:
                line += char
        return lines+[line]

    def paragraph(self, value, pos, width, size=19, color=INK, max_lines=8):
        for i, line in enumerate(self.wrap(value, width, size)[:max_lines]):
            self.text(line, (pos[0], pos[1]+i*(size+9)), size, color)

    def card(self, rect):
        pygame.draw.rect(self.canvas, WHITE, rect, border_radius=16)

    def button(self, label, rect, action, primary=False):
        rect = pygame.Rect(rect)
        pos = self.logical_pos(pygame.mouse.get_pos())
        color = TEAL if primary else (226, 237, 245)
        if rect.collidepoint(pos):
            color = (0, 117, 113) if primary else (204, 223, 235)
        pygame.draw.rect(self.canvas, color, rect, border_radius=9)
        txt = self.font(18).render(label, True, WHITE if primary else INK)
        self.canvas.blit(txt, txt.get_rect(center=rect.center))
        self.buttons.append((rect, action))

    def make_sounds(self):
        """合成短音，不依赖外部音频；无声卡时允许正常运行。"""
        if not pygame.mixer.get_init():
            self.sound_enabled = False
            return
        for name, hz in [('ok', 660), ('error', 220), ('done', 880)]:
            samples = array('h', [int(6000*math.sin(2*math.pi*hz*i/22050)*(1-i/3300))
                                  for i in range(3300)])
            self.sounds[name] = pygame.mixer.Sound(buffer=samples.tobytes())

    def notify(self, message, error=False):
        self.toast, self.toast_error = message, error
        self.toast_until = pygame.time.get_ticks()+6500
        if self.sound_enabled and self.sounds:
            self.sounds['error' if error else 'ok'].play()

    def change(self, state):
        self.state, self.fields, self.focus = state, [], 0
        self.selected, self.page, self.report_offset = None, 0, 0
        specs = []
        if state in ('login', 'register'):
            specs = [('username', '用户名（4–16位，支持中文）', ''), ('password', '密码（至少6位，数字和字母）', '')]
            if state == 'register':
                specs += [('phone', '手机号（选填）', ''), ('email', '邮箱（选填）', '')]
            for i, (key, label, val) in enumerate(specs):
                self.fields.append(Field(key, label, (105, 260+i*94, 440, 48), val, key=='password'))
        elif state == 'add':
            specs = [('record_date', '日期 YYYY-MM-DD', date.today().isoformat())]
            if self.record_kind == '体检':
                specs += [('height', '身高 cm', ''), ('weight', '体重 kg', ''),
                          ('blood_pressure', '血压 mmHg，例如120/80', ''), ('blood_sugar', '血糖 mmol/L', ''),
                          ('heart_rate', '心率 次/分', '')]
            elif self.record_kind == '用药':
                specs += [('medicine_name', '药品名称', ''), ('dosage', '剂量（例如1片）', ''),
                          ('frequency', '频次（例如每日3次）', ''), ('duration_days', '用药天数（正整数）', '')]
            else:
                specs += [('record_type', '记录类型（例如运动）', ''), ('value', '数值 / 内容', ''), ('unit', '单位（选填）', '')]
            specs += [('notes', '备注（选填）', '')]
            for i, (key, label, val) in enumerate(specs):
                self.fields.append(Field(key, label, (270+(i%2)*440, 240+(i//2)*100, 400, 48), val))
        if self.fields:
            pygame.key.start_text_input()
        else:
            pygame.key.stop_text_input()
        if state == 'assessment':
            self.progress, self.assessing, self.result = 0, False, None
            self.actor.update(805, 420)

    def values(self):
        return {f.key: f.value.strip() for f in self.fields}

    def user_records(self, kind=None):
        return self.data.get_user_records(self.auth.get_current_user().user_id, kind)

    def submit(self):
        values = self.values()
        if self.state == 'login':
            ok, msg = self.auth.login(values['username'], values['password'])
            if ok:
                self.change('dashboard')
            self.notify(msg, not ok)
        elif self.state == 'register':
            ok, msg = self.auth.register(**values)
            if ok:
                name = values['username']
                self.change('login'); self.fields[0].value = name; self.focus = 1
            self.notify(msg, not ok)
        elif self.state == 'add':
            self.save_record(values)

    def save_record(self, values):
        ok, msg = Validator.validate_date(values['record_date'])
        if not ok:
            raise ValueError(msg)
        if values['record_date'] > date.today().isoformat():
            raise ValueError('健康记录日期不能晚于今天')
        kind = self.record_kind
        payload = {k:v for k,v in values.items() if k != 'record_date'}
        if kind == '体检':
            for key in ['height', 'weight', 'blood_sugar', 'heart_rate']:
                try:
                    number = float(values[key])
                except ValueError:
                    raise ValueError('身高、体重、血糖、心率必须填写有效数字')
                if not math.isfinite(number) or number <= 0:
                    raise ValueError('数值必须为大于0的有限数字')
                if key == 'heart_rate' and not number.is_integer():
                    raise ValueError('心率必须为正整数')
                payload[key] = int(number) if key=='heart_rate' else number
            parts = values['blood_pressure'].split('/')
            if len(parts)!=2 or not all(x.isdigit() and int(x)>0 for x in parts):
                raise ValueError('血压格式应为正整数/正整数，例如120/80')
            value = f"BP:{payload['blood_pressure']}, BS:{payload['blood_sugar']}"
        elif kind == '用药':
            if not all(values[k] for k in ['medicine_name', 'dosage', 'frequency']):
                raise ValueError('请完整填写药品名称、剂量和频次')
            if not values['duration_days'].isdigit() or int(values['duration_days'])<=0:
                raise ValueError('用药天数必须为正整数')
            payload['duration_days'] = int(values['duration_days'])
            value = values['dosage']+' '+values['frequency']
        else:
            kind = payload.pop('record_type')
            value = payload.pop('value')
            if not kind or not value or kind in ['体检', '用药']:
                raise ValueError('请填写其他记录类型和内容；体检/用药请使用专用表单')
        ok, msg = self.data.add_record(self.auth.current_user.user_id, kind, values['record_date'], value, **payload)
        if ok:
            self.change('records')
        self.notify(msg, not ok)

    def export(self):
        path = Path(config.DATA_DIR)/'exports'
        path.mkdir(exist_ok=True)
        file = path/f'records_{self.auth.current_user.user_id}_{datetime.now():%Y%m%d_%H%M%S_%f}.csv'
        ok, msg = self.data.export_to_csv(self.auth.current_user.user_id, str(file))
        self.notify(msg, not ok)

    def backup(self):
        """备份当前登录用户，避免给普通用户导出其他人的数据。"""
        import json
        folder = Path(config.DATA_DIR)/'backups'
        folder.mkdir(exist_ok=True)
        path = folder/f'{self.auth.current_user.user_id}_{datetime.now():%Y%m%d_%H%M%S_%f}.json'
        path.write_text(json.dumps({'user_id': self.auth.current_user.user_id,
                                    'records': self.user_records()}, ensure_ascii=False, indent=2), encoding='utf-8')
        self.notify(f'当前用户记录备份成功：{path}')

    def report(self):
        report, msg = self.data.generate_report(self.auth.current_user.user_id, self.auth.current_user.username)
        if report:
            self.report_lines = [line for raw in report.content.splitlines() for line in self.wrap(raw, 820, 19)]
            self.change('report')
        self.notify(msg, not bool(report))

    def start_assessment(self):
        if not self.user_records('体检'):
            self.notify('请先添加一条体检记录，再开始评测', True)
            return
        self.progress, self.assessing, self.result = 0, True, None

    def update(self, dt):
        """时间步长动画；评测期间也继续处理窗口和输入事件。"""
        if self.state == 'assessment':
            keys = pygame.key.get_pressed()
            direction = pygame.Vector2(int(keys[pygame.K_RIGHT])-int(keys[pygame.K_LEFT]),
                                       int(keys[pygame.K_DOWN])-int(keys[pygame.K_UP]))
            if direction.length_squared():
                self.actor += direction.normalize()*230*dt
            self.actor.x = max(720, min(1070, self.actor.x))
            self.actor.y = max(320, min(520, self.actor.y))
            if self.assessing:
                self.progress = min(1.0, self.progress+dt/2.4)
                if self.progress >= 1:
                    records = self.user_records('体检')
                    r = records[0]
                    bmi = r.get('bmi')
                    if not isinstance(bmi, (int, float)) and r.get('height', 0)>0:
                        bmi = r.get('weight', 0)/(r['height']/100)**2
                    self.result = ['最新体检日期：'+r['record_date'],
                                   'BMI：'+(f'{bmi:.2f}' if isinstance(bmi, (int,float)) else '未提供'),
                                   '血压：'+str(r.get('blood_pressure', '未提供'))+' mmHg',
                                   '血糖：'+str(r.get('blood_sugar', '未提供'))+' mmol/L',
                                   '心率：'+str(r.get('heart_rate', '未提供'))+' 次/分',
                                   f'已归档体检记录：{len(records)} 条',
                                   '仅作数据汇总，不提供诊断或用药建议。']
                    self.assessing = False
                    self.notify('评测完成：结果面板已更新')
                    if self.sound_enabled and self.sounds:
                        self.sounds['done'].play()

    def logical_pos(self, pos):
        return ((pos[0]-self.viewport.x)*W/self.viewport.width,
                (pos[1]-self.viewport.y)*H/self.viewport.height)

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            self.window = pygame.display.set_mode((max(640,event.w), max(480,event.h)), pygame.RESIZABLE)
            self.present()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
            pos = self.logical_pos(event.pos)
            self.pointer = pos
            for i, field in enumerate(self.fields):
                if field.rect.collidepoint(pos):
                    self.focus = i; break
            # 使用上一帧可见按钮的命中区域，不在事件处理中重建界面。
            for rect, action in list(self.buttons):
                if rect.collidepoint(pos):
                    action(); break
        elif event.type == pygame.MOUSEWHEEL:
            if self.state == 'records' and self.selected:
                self.detail_offset = max(0, min(max(0,len(self.detail_lines())-15), self.detail_offset-event.y*3))
            elif self.state == 'records':
                total = len(self.user_records(self.filter_kind))
                self.page = max(0, min(max(0,(total-1)//6), self.page-event.y))
            elif self.state == 'report':
                self.report_offset = max(0, min(max(0,len(self.report_lines)-17), self.report_offset-event.y*3))
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == 'register':
                self.change('login')
            elif self.auth.is_logged_in():
                self.change('dashboard')
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB and self.fields:
            self.fields[self.focus].composition = ''
            self.focus = (self.focus+(-1 if event.mod & pygame.KMOD_SHIFT else 1))%len(self.fields)
        elif event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_KP_ENTER] and self.fields:
            if not self.fields[self.focus].composition:
                self.submit()
        elif event.type == pygame.KEYDOWN and event.key==pygame.K_SPACE and self.state=='assessment':
            self.start_assessment()
        elif self.fields:
            self.fields[self.focus].event(event)

    def safe(self, operation, *args):
        try:
            operation(*args)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            self.notify(str(exc), True)

    def logout(self):
        self.auth.logout(); self.change('login'); self.report_lines = []

    def choose_kind(self, kind):
        self.record_kind = kind; self.change('add')

    def filter(self, kind):
        self.filter_kind, self.page, self.selected = kind, 0, None

    def select_record(self, record):
        self.selected, self.detail_offset = record, 0

    def detail_lines(self):
        labels = {'record_id':'记录编号', 'record_date':'日期','record_type':'类型','value':'内容',
                  'unit':'单位','height':'身高 cm','weight':'体重 kg','blood_pressure':'血压 mmHg',
                  'blood_sugar':'血糖 mmol/L','heart_rate':'心率 次/分','bmi':'BMI',
                  'medicine_name':'药名','dosage':'剂量','frequency':'频次','duration_days':'天数','notes':'备注'}
        lines = []
        for key,label in labels.items():
            if key in self.selected:
                val = self.selected[key]
                if key == 'bmi' and isinstance(val, (int,float)):
                    val = f'{val:.2f}'
                lines.extend(self.wrap(f'{label}：{val}',590,18))
        return lines

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled if self.sounds else False
        if not self.sounds:
            self.notify('未检测到音频设备，界面继续正常运行')

    def draw(self):
        self.canvas.fill(BG); self.buttons = []
        if self.state in ['login', 'register']:
            self.card((65, 155, 520, 585))
            self.text('健康数据管理平台', (90, 72), 34)
            self.text('记录日常健康，让数据清晰可见', (92, 120), 19, MUTED)
            self.text('用户登录' if self.state=='login' else '创建账号', (105, 185), 28)
            self.button('登录' if self.state=='login' else '注册', (105, 650, 200, 48), self.submit, True)
            self.button('创建账号' if self.state=='login' else '返回登录', (330,650,215,48),
                        lambda: self.change('register' if self.state=='login' else 'login'))
            self.card((630, 155, 510, 585))
            self.text('Pygame · 事件驱动与多媒体交互', (665, 195), 24)
            for i, line in enumerate(['信息卡片 / 进度条 / 结果面板', '鼠标交互 / 中文输入 / 键盘控制',
                                      '状态切换 / 时间步长动画 / 提示音', 'JSON保存 / CSV导出 / 文本报告']):
                self.text(line, (665, 280+i*58), 21, MUTED)
            self.paragraph('首次使用请创建账号。原命令行数据可迁移，详见 README。', (665, 555), 425, 20)
        else:
            pygame.draw.rect(self.canvas, INK, (0,0,220,H))
            self.text('健康数据平台', (23,30), 25, WHITE)
            self.text(self.auth.current_user.username[:10], (24,80), 19, (166,204,218))
            nav = [('总览','dashboard'),('添加记录','add'),('记录查询','records'),('分类统计','stats'),('健康评测','assessment')]
            for i,(label,state) in enumerate(nav):
                self.button(label, (20,140+i*60,180,44), lambda s=state:self.change(s), self.state==state)
            self.button('导出 CSV', (20,465,180,44), self.export)
            self.button('生成报告', (20,520,180,44), self.report)
            self.button('备份我的记录', (20,575,180,44), self.backup)
            self.button('提示音：'+('开' if self.sound_enabled else '关'), (20,640,180,40), self.toggle_sound)
            self.button('退出登录', (20,700,180,40), self.logout)
            titles = {'dashboard':'健康数据总览','add':'添加健康记录','records':'健康记录查询',
                      'stats':'按指标查看统计','assessment':'健康评测交互原型','report':'健康报告预览'}
            self.text(titles[self.state], (260,38), 30)
            self.text('本地保存 · 当前用户独立查询', (262,84), 18, MUTED)
            self.draw_content()
        for i, field in enumerate(self.fields):
            field.draw(self, i==self.focus)
        if self.fields:
            self.text('Tab 切换输入框 · Enter 提交 · Delete 清空当前输入', (270 if self.auth.is_logged_in() else 105, 720), 16, MUTED)
            field = self.fields[self.focus]
            x = self.viewport.x+int(field.rect.x*self.viewport.width/W)
            y = self.viewport.y+int(field.rect.bottom*self.viewport.height/H)
            pygame.key.set_text_input_rect(pygame.Rect(x,y,300,30))
        if self.toast and pygame.time.get_ticks()<self.toast_until:
            color = RED if self.toast_error else TEAL
            pygame.draw.rect(self.canvas, color, (240,746,940,48), border_radius=10)
            self.paragraph(self.toast,(255,756),910,16,WHITE,max_lines=1)

    def draw_content(self):
        if self.state=='dashboard':
            records = self.user_records()
            counts = [('全部记录',len(records)), ('体检',len(self.user_records('体检'))), ('用药',len(self.user_records('用药')))]
            for i,(label,count) in enumerate(counts):
                x=260+i*305; self.card((x,145,285,150))
                self.text(label,(x+22,167),21,MUTED);self.text(count,(x+22,209),42,TEAL)
            self.card((260,325,900,360));self.text('从记录到反馈', (290,355),26)
            self.paragraph('1. 添加体检、用药或其他日常记录。\n2. 查询记录，查看分指标统计。\n3. 在健康评测中移动角色，启动评测并查看汇总。\n4. 导出 CSV、生成报告或备份当前用户记录。', (290,410),800,22)
            self.text('健康评测仅展示已记录数据，不提供医学诊断。',(290,635),18,MUTED)
        elif self.state=='add':
            for i,kind in enumerate(['体检','用药','其他']):
                self.button(kind,(270+i*150,140,130,42),lambda k=kind:self.choose_kind(k),self.record_kind==kind)
            self.button('保存记录',(270,655,220,48),self.submit,True)
        elif self.state=='records':
            for i,kind in enumerate([None,'体检','用药']):
                self.button(kind or '全部',(260+i*135,130,120,40),lambda k=kind:self.filter(k),self.filter_kind==kind)
            records=self.user_records(self.filter_kind)
            for i,r in enumerate(records[self.page*6:self.page*6+6]):
                y=190+i*72;self.card((260,y,900,62))
                self.text(f"{r['record_date']}  {r['record_type']}  {r['record_id']}",(275,y+7),18)
                summary=(r.get('medicine_name','')+' '+str(r['value'])+' '+r.get('unit','')).strip()
                self.paragraph(summary,(275,y+33),735,16,MUTED,1)
                self.button('详情',(1050,y+12,95,38),lambda row=r:self.select_record(row))
            pages=max(1,(len(records)+5)//6)
            self.text(f'第 {self.page+1}/{pages} 页 · 共 {len(records)} 条（滚轮翻页）',(260,640),18,MUTED)
            self.button('上一页',(790,633,120,40),lambda:setattr(self,'page',max(0,self.page-1)))
            self.button('下一页',(930,633,120,40),lambda:setattr(self,'page',min(pages-1,self.page+1)))
            if not records:self.text('暂无记录，请先添加。',(280,240),23,MUTED)
            if self.selected:
                overlay=pygame.Surface((W,H),pygame.SRCALPHA);overlay.fill((20,35,50,160));self.canvas.blit(overlay,(0,0))
                self.buttons=[] # 模态详情阻止点击背后的导航。
                self.card((320,130,650,575));self.text('记录详情',(350,150),26)
                for i,line in enumerate(self.detail_lines()[self.detail_offset:self.detail_offset+15]):
                    self.text(line,(350,202+i*28),18)
                self.text('滚轮查看全文',(350,654),16,MUTED)
                self.button('关闭',(765,645,170,40),lambda:setattr(self,'selected',None),True)
        elif self.state=='stats':
            y=145
            for kind in ['体检','用药']:
                self.card((260,y,900,255 if kind=='体检' else 160))
                self.text(kind+'统计',(285,y+20),25,TEAL)
                stats=self.data.get_statistics(self.auth.current_user.user_id,kind)
                for i,(key,val) in enumerate((stats or {'提示':'暂无记录'}).items()):
                    self.text(f'{key}：{val}',(285,y+64+i*27),18)
                y+=285
            self.text('各指标独立统计；最新值按记录日期降序选取。',(270,655),18,MUTED)
        elif self.state=='report':
            self.card((260,130,900,555))
            for i,line in enumerate(self.report_lines[self.report_offset:self.report_offset+17]):
                self.text(line,(285,150+i*29),19)
            self.text('鼠标滚轮查看全文；完整 TXT 已保存到 data/reports。',(270,705),18,MUTED)
        elif self.state=='assessment':
            self.card((260,135,420,550));self.text('结果面板',(285,160),26)
            if self.result:
                for i,line in enumerate(self.result):self.paragraph(line,(285,218+i*57),365,19,max_lines=2)
            else:self.paragraph('请先录入体检数据，再启动评测。这里会展示最新指标和记录汇总。',(285,230),360,23)
            self.card((705,135,455,550));self.text('交互评测区',(730,160),26)
            self.paragraph('方向键移动角色 · 鼠标点击场地移动\n空格 / 开始按钮启动评测',(730,210),400,18,MUTED)
            # 场地点击是鼠标事件驱动角色的位置变化。
            arena=pygame.Rect(720,300,410,240)
            pygame.draw.rect(self.canvas,(227,244,242),arena,border_radius=12)
            self.buttons.append((arena,lambda:self.actor.update(self.pointer)))
            bob=math.sin(pygame.time.get_ticks()/180)*5 if self.assessing else 0
            cx,cy=int(self.actor.x),int(self.actor.y+bob)
            pygame.draw.circle(self.canvas,TEAL,(cx,cy),27)
            pygame.draw.circle(self.canvas,WHITE,(cx-8,cy-5),4);pygame.draw.circle(self.canvas,WHITE,(cx+8,cy-5),4)
            pygame.draw.arc(self.canvas,WHITE,(cx-12,cy-6,24,22),math.pi,2*math.pi,2)
            if self.assessing:
                pygame.draw.circle(self.canvas,BLUE,(cx,cy),int(34+5*math.sin(pygame.time.get_ticks()/120)),2)
            pygame.draw.rect(self.canvas,(217,228,237),(730,565,400,18),border_radius=9)
            if self.progress:pygame.draw.rect(self.canvas,TEAL,(730,565,int(400*self.progress),18),border_radius=9)
            self.text(f"{'数据整理动画' if self.assessing else '评测进度'}：{int(self.progress*100)}%",(730,593),18,MUTED)
            self.button('开始 / 重新评测',(730,630,230,40),self.start_assessment,True)

    def present(self):
        sw,sh=self.window.get_size();scale=min(sw/W,sh/H)
        size=(max(1,int(W*scale)),max(1,int(H*scale)))
        self.viewport=pygame.Rect((sw-size[0])//2,(sh-size[1])//2,*size)
        self.window.fill((18,32,48))
        self.window.blit(pygame.transform.smoothscale(self.canvas,size),self.viewport)
        pygame.display.flip()

    def run(self):
        try:
            while self.running:
                dt=min(self.clock.tick(60)/1000,0.05)
                for event in pygame.event.get():
                    self.safe(self.handle,event)
                self.safe(self.update,dt)
                self.safe(self.draw)
                self.present()
        finally:
            pygame.quit()
