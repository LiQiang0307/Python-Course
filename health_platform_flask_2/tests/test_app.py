"""使用 Flask 自带测试客户端，检查核心课程任务。"""
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
import config
from app import app, data_service
from models.user import User


class FlaskCourseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.old_users, self.old_reports = config.USERS_FILE, config.REPORTS_DIR
        self.old_records = data_service.records_file
        config.USERS_FILE = str(base / 'users.json')
        config.REPORTS_DIR = str(base)
        data_service.records_file = str(base / 'records.json')
        users = [User('U0001', 'student1', 'Student123').to_dict(), User('U0002', 'student2', 'Student123').to_dict()]
        Path(config.USERS_FILE).write_text(json.dumps(users), encoding='utf-8')
        Path(data_service.records_file).write_text('[]', encoding='utf-8')
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def tearDown(self):
        config.USERS_FILE, config.REPORTS_DIR = self.old_users, self.old_reports
        data_service.records_file = self.old_records
        self.temp.cleanup()

    def login(self, name='student1'):
        return self.client.post('/login', data={'username': name, 'password': 'Student123'})

    def exam(self):
        return {'record_type': '体检', 'record_date': '2026-10-12', 'height': 170, 'weight': 65,
                'blood_pressure': '120/80', 'blood_sugar': 5.2, 'heart_rate': 72}

    def test_pages_and_authentication(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/records').status_code, 302)
        self.assertEqual(self.client.get('/api/records').status_code, 401)
        self.assertEqual(self.login().status_code, 302)
        self.assertEqual(self.client.get('/records').status_code, 200)
        self.assertEqual(self.client.get('/assessment').status_code, 200)

    def test_form_validation_and_assessment(self):
        self.login()
        bad = self.exam() | {'record_date': '2026-02-30'}
        self.assertEqual(self.client.post('/records', data=bad).status_code, 400)
        self.assertEqual(self.client.post('/records', data=self.exam()).status_code, 302)
        response = self.client.get('/assessment')
        self.assertEqual(response.status_code, 200)
        self.assertIn('22.49', response.get_data(as_text=True))

    def test_api_statuses_and_user_isolation(self):
        self.login()
        self.assertEqual(self.client.post('/api/records', data='x', content_type='text/plain').status_code, 415)
        self.assertEqual(self.client.post('/api/records', data='{', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post('/api/records', json=self.exam() | {'height': 0}).status_code, 400)
        self.assertEqual(self.client.post('/api/records', json=self.exam()).status_code, 201)
        self.assertEqual(self.client.get('/api/records').get_json()['count'], 1)
        self.client.post('/logout')
        self.login('student2')
        self.assertEqual(self.client.get('/api/records').get_json()['count'], 0)

    def test_registration_and_bad_json_data(self):
        self.assertEqual(self.client.post('/register', data={'username':'newuser', 'password':'Pass123'}).status_code, 302)
        self.assertEqual(self.client.post('/register', data={'username':'newuser', 'password':'Pass123'}).status_code, 400)
        self.login()
        self.assertEqual(self.client.post('/api/records', json=[]).status_code, 400)
        self.assertEqual(self.client.post('/api/records', json={'record_type': None, 'record_date':'2026-10-12'}).status_code, 400)
        # 文件损坏时不得当作空列表覆盖；关闭异常传播以检查 500 响应。
        Path(data_service.records_file).write_text('{broken', encoding='utf-8')
        app.config['PROPAGATE_EXCEPTIONS'] = False
        try:
            response = self.client.post('/api/records', json=self.exam())
            self.assertEqual(response.status_code, 500)
            self.assertFalse(response.get_json()['ok'])
            self.assertEqual(Path(data_service.records_file).read_text(encoding='utf-8'), '{broken')
        finally:
            app.config.pop('PROPAGATE_EXCEPTIONS', None)

    def test_mixed_types_and_csv(self):
        self.login()
        self.client.post('/api/records', json=self.exam())
        medicine = {'record_type': '用药', 'record_date': '2026-10-13', 'medicine_name': '示例',
                    'dosage': '1片', 'frequency': '每日一次', 'duration_days': 3}
        self.assertEqual(self.client.post('/api/records', json=medicine).status_code, 201)
        self.assertEqual(self.client.post('/api/records', json={'record_type':'睡眠', 'record_date':'2026-10-14', 'value':'7.5', 'unit':'小时'}).status_code, 201)
        content = self.client.get('/records.csv').get_data(as_text=True).lstrip('\ufeff')
        rows = list(csv.DictReader(io.StringIO(content)))
        self.assertEqual(len(rows), 3)
        self.assertTrue({'height', 'medicine_name', 'unit'}.issubset(rows[0].keys()))
        self.assertEqual(self.client.get('/report.txt').status_code, 200)


if __name__ == '__main__':
    unittest.main()
