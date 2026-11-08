"""
基础路由测试（任务1）
覆盖：首页、健康记录、评测结果路由
"""
import re


def test_index_anonymous(client):
    """未访问首页返回 200 且包含欢迎信息"""
    resp = client.get('/')
    assert resp.status_code == 200
    assert '健康数据管理平台'.encode() in resp.data


def test_records_requires_login(client):
    """未登录访问健康记录页应 302 跳转登录页"""
    resp = client.get('/records')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']


def test_assessment_page(client):
    """健康评测页返回 200"""
    resp = client.get('/assessment')
    assert resp.status_code == 200


def test_404_page(client):
    """不存在的路由返回 404"""
    resp = client.get('/not-exist')
    assert resp.status_code == 404


def test_api_health_check(client):
    """API 健康检查返回 200"""
    resp = client.get('/api/v1/health')
    assert resp.status_code == 200
    assert resp.get_json()['data']['status'] == 'up'


def test_register_and_login_flow(client):
    """注册 → 登录 → 首页出现用户名"""
    resp = client.post('/register', data={
        'username': '测试用户',
        'password': 'abc12345',
    })
    assert resp.status_code == 302

    resp = client.post('/login', data={
        'username': '测试用户',
        'password': 'abc12345',
    })
    assert resp.status_code == 302

    resp = client.get('/')
    assert '测试用户'.encode() in resp.data


def test_login_wrong_password(client):
    """密码错误返回 400"""
    client.post('/register', data={
        'username': 'user01', 'password': 'abc12345',
    })
    resp = client.post('/login', data={
        'username': 'user01', 'password': 'wrongpass',
    })
    assert resp.status_code == 400
