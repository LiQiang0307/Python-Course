"""
健康记录 JSON API 测试（任务3）
"""
import pytest


def _register_user(client, username='apiuser', password='abc12345'):
    client.post('/register', data={'username': username, 'password': password})
    client.post('/login', data={'username': username, 'password': password})


def test_api_create_record_success(client):
    """创建记录成功返回 201（任务3）"""
    _register_user(client)
    resp = client.post('/api/v1/records', json={
        'record_type': '体检',
        'record_date': '2026-11-08',
        'height': 172,
        'weight': 66,
        'blood_pressure': '118/76',
        'blood_sugar': 5.4,
        'heart_rate': 70,
    })
    assert resp.status_code == 201
    body = resp.get_json()
    assert body['code'] == 201
    assert body['data']['record_id'] == 'R0001'
    assert body['data']['bmi'] > 0


def test_api_create_record_validation_error(client):
    """缺少必填字段返回 400"""
    _register_user(client)
    resp = client.post('/api/v1/records', json={
        'record_type': '体检',
    })
    assert resp.status_code == 400
    assert resp.get_json()['code'] == 400


def test_api_create_record_bad_date(client):
    """非法日期返回 400"""
    _register_user(client)
    resp = client.post('/api/v1/records', json={
        'record_type': '其他', 'record_date': '2026/11/08', 'value': '12',
    })
    assert resp.status_code == 400


def test_api_create_record_not_json(client):
    """非 JSON 请求返回 415"""
    _register_user(client)
    resp = client.post('/api/v1/records', data={'record_type': '体检'})
    assert resp.status_code == 415


def test_api_list_records(client):
    """获取记录列表返回 200 且数据结构正确"""
    _register_user(client)
    client.post('/api/v1/records', json={
        'record_type': '用药', 'record_date': '2026-11-01',
        'medicine_name': '维生素C', 'dosage': '100mg',
        'frequency': '每日1次', 'duration_days': 30,
    })
    resp = client.get('/api/v1/records')
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['total'] == 1
    assert data['items'][0]['medicine_name'] == '维生素C'


def test_api_get_record_404(client):
    """查询不存在的记录返回 404"""
    _register_user(client)
    resp = client.get('/api/v1/records/R9999')
    assert resp.status_code == 404


def test_api_delete_record(client):
    """删除自己的记录返回 204，再次查询返回 404"""
    _register_user(client)
    resp = client.post('/api/v1/records', json={
        'record_type': '其他', 'record_date': '2026-11-08', 'value': '跑步30分钟',
    })
    record_id = resp.get_json()['data']['record_id']

    resp = client.delete(f'/api/v1/records/{record_id}')
    assert resp.status_code == 204

    resp = client.get(f'/api/v1/records/{record_id}')
    assert resp.status_code == 404


def test_api_statistics(client):
    """统计接口返回 200"""
    _register_user(client)
    client.post('/api/v1/records', json={
        'record_type': '其他', 'record_date': '2026-11-08', 'value': '体重 65.5',
    })
    resp = client.get('/api/v1/statistics')
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['count'] == 1


def test_api_requires_user_id_when_anonymous(client):
    """未登录且未提供 user_id 时返回 401"""
    resp = client.get('/api/v1/records')
    assert resp.status_code == 401
