"""
健康评测测试（任务2：表单请求处理与模板渲染）
"""
import pytest


@pytest.fixture()
def logged_in_client(client):
    client.post('/register', data={'username': 'assessuser', 'password': 'abc12345'})
    client.post('/login', data={'username': 'assessuser', 'password': 'abc12345'})
    return client


def test_assessment_form_submit(logged_in_client):
    """表单提交评测，返回 200 并渲染评测结果页"""
    resp = logged_in_client.post('/assessment', data={
        'height': '170', 'weight': '65',
        'blood_pressure': '118/76',
        'blood_sugar': '5.4', 'heart_rate': '72',
        'save_record': 'on',
    })
    assert resp.status_code == 200
    assert '评测结果'.encode() in resp.data or '良好'.encode() in resp.data


def test_assessment_json_submit(logged_in_client):
    """JSON 提交评测，返回 200 与结构化结果"""
    resp = logged_in_client.post('/assessment', json={
        'height': 170, 'weight': 90,
        'blood_pressure': '150/95',
        'blood_sugar': 7.5, 'heart_rate': 110,
    })
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['overall'] == '需关注'
    assert data['bmi'] > 28


def test_assessment_empty_input(logged_in_client):
    """空提交返回 400"""
    resp = logged_in_client.post('/assessment', data={})
    assert resp.status_code == 400


def test_assessment_invalid_blood_pressure(logged_in_client):
    """非法血压格式返回 400"""
    resp = logged_in_client.post('/assessment', data={'blood_pressure': '300/80'})
    assert resp.status_code == 400


def test_assessment_saves_record_when_logged_in(logged_in_client):
    """勾选保存后，评测数据写入健康记录"""
    logged_in_client.post('/assessment', data={
        'height': '170', 'weight': '65', 'save_record': 'on',
    })
    resp = logged_in_client.get('/api/v1/records')
    records = resp.get_json()['data']['records']
    assert len(records) == 1
    assert records[0]['record_type'] == '体检'
