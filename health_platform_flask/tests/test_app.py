"""
端到端功能测试
覆盖：任务1 路由、任务2 表单/JSON 与状态码、任务3 JSON API
"""
import pytest

from app import create_app
from app.services import AuthService


@pytest.fixture
def client(tmp_path):
    """使用临时数据目录的测试客户端"""
    app = create_app('testing')
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    app.config.update({
        'DATA_DIR': str(data_dir),
        'REPORTS_DIR': str(data_dir / 'reports'),
        'BACKUP_DIR': str(data_dir / 'backups'),
        'USERS_FILE': str(data_dir / 'users.json'),
        'RECORDS_FILE': str(data_dir / 'records.json'),
        'LOG_DIR': str(tmp_path / 'logs'),
    })
    with app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(client):
    """注册并登录后的测试客户端"""
    resp = client.post('/register', json={
        'username': '张三', 'password': 'abc123',
    })
    assert resp.status_code == 201
    resp = client.post('/login', json={
        'username': '张三', 'password': 'abc123',
    })
    assert resp.status_code == 200
    return client


# ---------- 任务1：核心路由 ----------
class TestCoreRoutes:
    def test_index_anonymous(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        assert '健康'.encode() in resp.data

    def test_index_logged_in(self, logged_in_client):
        resp = logged_in_client.get('/')
        assert resp.status_code == 200

    def test_records_requires_login(self, client):
        resp = client.get('/records')
        assert resp.status_code == 302

    def test_records_page(self, logged_in_client):
        resp = logged_in_client.get('/records')
        assert resp.status_code == 200

    def test_add_record_page(self, logged_in_client):
        resp = logged_in_client.get('/records/add')
        assert resp.status_code == 200

    def test_assessment_page(self, client):
        resp = client.get('/assessment')
        assert resp.status_code == 200

    def test_404_page(self, client):
        resp = client.get('/not-exist')
        assert resp.status_code == 404


# ---------- 任务2：表单/JSON 请求与状态码 ----------
class TestFormAndJson:
    def test_register_json_201(self, client):
        resp = client.post('/register', json={
            'username': '李四', 'password': 'pass123',
        })
        assert resp.status_code == 201
        assert resp.get_json()['code'] == 201

    def test_register_invalid_password_400(self, client):
        resp = client.post('/register', json={
            'username': '王五', 'password': '123',
        })
        assert resp.status_code == 400

    def test_login_success(self, client):
        client.post('/register', json={'username': '赵六', 'password': 'abc123'})
        resp = client.post('/login', json={'username': '赵六', 'password': 'abc123'})
        assert resp.status_code == 200

    def test_login_wrong_password_400(self, client):
        client.post('/register', json={'username': '孙七', 'password': 'abc123'})
        resp = client.post('/login', json={'username': '孙七', 'password': 'wrong1'})
        assert resp.status_code == 400

    def test_add_record_form_redirect(self, logged_in_client):
        resp = logged_in_client.post('/records/add', data={
            'record_type': '体检', 'record_date': '2026-11-08',
            'height': '170', 'weight': '65',
            'blood_pressure': '120/80', 'blood_sugar': '5.6', 'heart_rate': '72',
        })
        assert resp.status_code == 302

    def test_add_record_json_201(self, logged_in_client):
        resp = logged_in_client.post('/records/add', json={
            'record_type': '体检', 'record_date': '2026-11-08',
            'height': 170, 'weight': 65,
            'blood_pressure': '120/80', 'blood_sugar': 5.6, 'heart_rate': 72,
        })
        assert resp.status_code == 201
        assert resp.get_json()['data']['record_type'] == '体检'

    def test_add_record_invalid_bp_400(self, logged_in_client):
        resp = logged_in_client.post('/records/add', json={
            'record_type': '体检', 'record_date': '2026-11-08',
            'blood_pressure': '300/50',
        })
        assert resp.status_code == 400

    def test_assessment_result_200(self, client):
        resp = client.post('/assessment', data={
            'height': '170', 'weight': '80',
            'blood_pressure': '140/95', 'blood_sugar': '7.5', 'heart_rate': '110',
        })
        assert resp.status_code == 200
        assert '需关注'.encode() in resp.data

    def test_assessment_invalid_bp_400(self, client):
        resp = client.post('/assessment', data={'blood_pressure': '99/999'})
        assert resp.status_code == 400


# ---------- 任务3：JSON API ----------
class TestRecordApi:
    def test_create_record_201(self, logged_in_client):
        resp = logged_in_client.post('/api/v1/records', json={
            'record_type': '体检', 'record_date': '2026-11-08',
            'height': 170, 'weight': 65,
            'blood_pressure': '120/80', 'blood_sugar': 5.6, 'heart_rate': 72,
        })
        assert resp.status_code == 201
        body = resp.get_json()
        assert body['data']['record_id'].startswith('R')

    def test_create_medication_record_201(self, logged_in_client):
        resp = logged_in_client.post('/api/v1/records', json={
            'record_type': '用药', 'record_date': '2026-11-08',
            'medicine_name': '阿莫西林', 'dosage': '500mg',
            'frequency': '每日3次', 'duration_days': 7,
        })
        assert resp.status_code == 201

    def test_create_record_empty_body_400(self, logged_in_client):
        resp = logged_in_client.post('/api/v1/records', json={})
        assert resp.status_code == 400

    def test_create_record_requires_login_401(self, client):
        resp = client.post('/api/v1/records', json={
            'record_type': '体检', 'record_date': '2026-11-08',
        })
        assert resp.status_code == 401

    def test_list_records_200(self, logged_in_client):
        logged_in_client.post('/api/v1/records', json={
            'record_type': '体检', 'record_date': '2026-11-08', 'height': 170,
        })
        resp = logged_in_client.get('/api/v1/records')
        assert resp.status_code == 200
        assert resp.get_json()['data']['count'] == 1

    def test_list_records_invalid_type_400(self, logged_in_client):
        resp = logged_in_client.get('/api/v1/records?type=abc')
        assert resp.status_code == 400

    def test_get_record_200_and_404(self, logged_in_client):
        resp = logged_in_client.post('/api/v1/records', json={
            'record_type': '其他', 'record_date': '2026-11-08', 'value': '跑步',
        })
        record_id = resp.get_json()['data']['record_id']

        resp = logged_in_client.get(f'/api/v1/records/{record_id}')
        assert resp.status_code == 200

        resp = logged_in_client.get('/api/v1/records/R9999')
        assert resp.status_code == 404

    def test_delete_record_204(self, logged_in_client):
        resp = logged_in_client.post('/api/v1/records', json={
            'record_type': '其他', 'record_date': '2026-11-08', 'value': '步行',
        })
        record_id = resp.get_json()['data']['record_id']

        resp = logged_in_client.delete(f'/api/v1/records/{record_id}')
        assert resp.status_code == 204

        resp = logged_in_client.delete(f'/api/v1/records/{record_id}')
        assert resp.status_code == 404

    def test_statistics_200_and_404(self, logged_in_client):
        resp = logged_in_client.get('/api/v1/statistics')
        assert resp.status_code == 404

        logged_in_client.post('/api/v1/records', json={
            'record_type': '其他', 'record_date': '2026-11-08', 'value': '步数 8000',
        })
        resp = logged_in_client.get('/api/v1/statistics?type=其他')
        assert resp.status_code == 200
        assert resp.get_json()['data']['count'] == 1


# ---------- 服务层回归 ----------
class TestServices:
    def test_register_and_login(self, tmp_path):
        from app.config import BaseConfig
        config = dict(BaseConfig.__dict__)
        config['USERS_FILE'] = str(tmp_path / 'users.json')
        config['LOG_DIR'] = str(tmp_path / 'logs')

        service = AuthService(config)
        ok, msg, user = service.register('测试用户', 'abc123')
        assert ok and user.user_id == 'U0001'

        ok, msg, user = service.login('测试用户', 'abc123')
        assert ok
        assert service.get_current_user() is None  # 未写入会话前无当前用户
