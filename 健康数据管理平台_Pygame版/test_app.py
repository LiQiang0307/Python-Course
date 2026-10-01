"""临时目录回归测试，不触碰用户数据。"""
import os, tempfile, unittest, hashlib, csv
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
_tmp=tempfile.TemporaryDirectory()
os.environ['HEALTH_DATA_DIR']=_tmp.name
import pygame, config
from gui import HealthApp
from utils.file_handler import FileHandler
from utils.validator import Validator

class Tests(unittest.TestCase):
    def setUp(self):
        for p in Path(config.DATA_DIR).rglob('*'):
            if p.is_file():p.unlink()
        self.app=HealthApp()
    def tearDown(self):pygame.quit()
    def fill(self,values):
        for key,value in values.items():
            self.app.focus=next(i for i,f in enumerate(self.app.fields) if f.key==key)
            self.app.handle(pygame.event.Event(pygame.TEXTINPUT,text=value))
    def account(self,name='testuser'):
        self.app.change('register');self.fill({'username':name,'password':'abc123'});self.app.submit()
        self.assertEqual(self.app.state,'login')
        self.fill({'password':'abc123'});self.app.submit();self.assertEqual(self.app.state,'dashboard')
    def exam(self):
        self.app.choose_kind('体检')
        self.fill({'height':'170','weight':'65','blood_pressure':'120/80','blood_sugar':'5.5','heart_rate':'72'})
        self.app.submit();self.assertEqual(self.app.state,'records')
    def test_full_flow(self):
        self.account();self.exam();self.app.choose_kind('用药')
        self.fill({'medicine_name':'示例药品','dosage':'1片','frequency':'每日1次','duration_days':'3'});self.app.submit()
        self.app.choose_kind('其他');self.fill({'record_type':'运动','value':'30','unit':'分钟'});self.app.submit()
        self.assertEqual(len(self.app.user_records()),3)
        self.app.export();self.app.backup();self.app.report();self.assertTrue(self.app.report_lines)
        with next((Path(config.DATA_DIR)/'exports').glob('*.csv')).open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),3);self.assertIn('height',rows[0]);self.assertIn('medicine_name',rows[0])
        self.app.change('assessment');self.app.start_assessment()
        for _ in range(150):self.app.update(.02)
        self.assertEqual(self.app.progress,1);self.assertTrue(any('22.49' in x for x in self.app.result))
        for state in ['dashboard','records','stats','report','assessment','add']:
            self.app.change(state);self.app.draw();self.app.present()
        self.app.handle(pygame.event.Event(pygame.VIDEORESIZE,w=800,h=600));self.app.draw();self.app.present()
        self.app.logout();self.app.fields[0].value='testuser';self.app.fields[1].value='abc123';self.app.submit()
        self.assertEqual(len(self.app.user_records()),3)
        self.app.logout();self.account('anotheruser');self.assertEqual(self.app.user_records(),[])
    def test_invalid_and_corrupt(self):
        self.account();self.app.choose_kind('体检');self.app.fields[0].value='2026-02-30'
        with self.assertRaises(ValueError):self.app.submit()
        self.assertEqual(self.app.user_records(),[]);self.assertFalse(Validator.validate_date('2026-02-30')[0])
        p=Path(config.RECORDS_FILE);p.write_text('{broken')
        with self.assertRaises(ValueError):self.app.user_records()
        self.assertEqual(p.read_text(),'{broken')
    def test_legacy(self):
        FileHandler.write_json(config.USERS_FILE,[{'user_id':'U0001','username':'legacy','password':hashlib.md5(b'abc123').hexdigest(),'created_at':'2020-01-01'}])
        self.assertTrue(self.app.auth.login('legacy','abc123')[0])
        saved=FileHandler.read_json(config.USERS_FILE)[0]
        self.assertTrue(saved['password'].startswith('pbkdf2_sha256$'));self.assertEqual(saved['created_at'],'2020-01-01')
    def test_events(self):
        self.app.draw();rect,_=next((r,a) for r,a in self.app.buttons if r.x==330)
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=rect.center));self.assertEqual(self.app.state,'register')
        self.fill({'username':'中文名字'})
        self.app.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_BACKSPACE,mod=0));self.assertEqual(self.app.fields[0].value,'中文名')
        self.app.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB,mod=0));self.assertEqual(self.app.focus,1)
        self.app.handle(pygame.event.Event(pygame.QUIT));self.assertFalse(self.app.running)

    def test_pagination_detail_and_validation(self):
        self.account()
        for i in range(7):
            self.app.data.add_record(self.app.auth.current_user.user_id,'运动','2026-09-30',str(i),notes='长备注'*300)
        self.app.change('records');self.app.draw()
        self.app.handle(pygame.event.Event(pygame.MOUSEWHEEL,y=-1,x=0))
        self.assertEqual(self.app.page,1)
        self.app.select_record(self.app.user_records()[0]);self.app.draw()
        self.assertTrue(len(self.app.detail_lines())>15)
        self.app.handle(pygame.event.Event(pygame.MOUSEWHEEL,y=-4,x=0))
        self.assertGreater(self.app.detail_offset,0);self.app.draw()
        self.app.choose_kind('体检')
        self.fill({'height':'nan','weight':'65','blood_pressure':'120/80','blood_sugar':'5.5','heart_rate':'72'})
        self.app.safe(self.app.submit)
        self.assertTrue(self.app.toast_error);self.assertEqual(len(self.app.user_records()),7)

if __name__=='__main__':unittest.main()
