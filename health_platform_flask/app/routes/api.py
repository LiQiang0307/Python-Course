"""
健康记录 JSON API 蓝图（任务3）
统一前缀: /api/v1
统一响应结构: { "code": int, "message": str, "data": ... }
状态码规范: 200 查询成功 / 201 创建成功 / 204 删除成功 /
           400 参数错误 / 401 未登录 / 404 资源不存在
"""
from flask import Blueprint, jsonify, request

from .helpers import get_auth_service, get_data_service, login_required

api_bp = Blueprint('api', __name__)


def _ok(data=None, message='ok', status=200):
    return jsonify({'code': status, 'message': message, 'data': data}), status


def _current_user_or_none():
    return get_auth_service().get_current_user()


def _resolve_user(data):
    """优先使用会话用户；未登录时可通过 user_id 参数指定（教学场景）"""
    user = _current_user_or_none()
    if user:
        return user, None
    user_id = (data or {}).get('user_id') or request.args.get('user_id', '')
    if not user_id:
        return None, ('未登录且未指定 user_id', 401)
    user = get_auth_service().find_user(user_id)
    if not user:
        return None, ('指定的用户不存在', 404)
    return user, None


@api_bp.get('/health')
def health_check():
    """GET /api/v1/health 健康检查"""
    return _ok({'status': 'up'})


@api_bp.get('/records')
def list_records():
    """GET /api/v1/records?user_id=&type=&page=&per_page= 查询健康记录列表"""
    data_service = get_data_service()
    user, err = _resolve_user(None)
    if err:
        return _ok(None, err[0], err[1])

    record_type = request.args.get('type', '').strip() or None
    if record_type and record_type not in ('体检', '用药', '其他'):
        return _ok(None, '无效的记录类型，可选值：体检/用药/其他', 400)

    records = data_service.get_user_records(user.user_id, record_type)

    # 简单分页
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
    except ValueError:
        return _ok(None, 'page/per_page 必须是整数', 400)

    total = len(records)
    items = records[(page - 1) * per_page: page * per_page]
    return _ok({
        'count': total,
        'total': total,
        'page': page,
        'per_page': per_page,
        'records': items,
        'items': items,
    })


@api_bp.get('/records/<record_id>')
def get_record(record_id):
    """GET /api/v1/records/<record_id> 查询单条记录"""
    user, err = _resolve_user(None)
    if err:
        return _ok(None, err[0], err[1])

    record = get_data_service().get_record(record_id, user.user_id)
    if not record:
        return _ok(None, '记录不存在', 404)
    return _ok(record)


@api_bp.post('/records')
@login_required
def create_record():
    """POST /api/v1/records 创建记录（JSON），成功返回 201"""
    data = request.get_json(silent=True)
    if not request.is_json:
        return _ok(None, 'Content-Type 必须为 application/json', 415)
    if not isinstance(data, dict) or not data:
        return _ok(None, '请求体必须是非空的 JSON 对象', 400)

    user = _current_user_or_none()
    from ..utils import Validator

    record_type = str(data.get('record_type', '')).strip()
    record_date = str(data.get('record_date', '')).strip()
    if not record_type:
        return _ok(None, '缺少必需字段: record_type', 400)
    if not record_date:
        return _ok(None, '缺少必需字段: record_date', 400)

    def to_float(value):
        try:
            return float(value) if value not in (None, '') else 0
        except (TypeError, ValueError):
            return 0

    kwargs = {}
    if record_type == '体检':
        bp = str(data.get('blood_pressure', '')).strip()
        if bp:
            is_valid, msg = Validator.validate_blood_pressure(bp)
            if not is_valid:
                return _ok(None, msg, 400)
        kwargs = {
            'height': to_float(data.get('height')),
            'weight': to_float(data.get('weight')),
            'blood_pressure': bp,
            'blood_sugar': to_float(data.get('blood_sugar')),
            'heart_rate': int(to_float(data.get('heart_rate'))),
            'notes': str(data.get('notes', '')),
        }
    elif record_type == '用药':
        kwargs = {
            'medicine_name': str(data.get('medicine_name', '')),
            'dosage': str(data.get('dosage', '')),
            'frequency': str(data.get('frequency', '')),
            'duration_days': int(to_float(data.get('duration_days'))),
            'notes': str(data.get('notes', '')),
        }

    success, message, record = get_data_service().add_record(
        user.user_id, record_type, record_date,
        str(data.get('value', '')), **kwargs)

    if not success:
        return _ok(None, message, 400)
    return _ok(record.to_dict() if record else None, message, 201)


@api_bp.delete('/records/<record_id>')
@login_required
def delete_record(record_id):
    """DELETE /api/v1/records/<record_id> 删除记录，成功返回 204"""
    user = _current_user_or_none()
    success, message = get_data_service().delete_record(record_id, user.user_id)
    if not success:
        return _ok(None, message, 404)
    return '', 204


@api_bp.get('/records/statistics')
@api_bp.get('/statistics')
def get_statistics():
    """GET /api/v1/statistics?user_id=&type= 查询统计信息"""
    user, err = _resolve_user(None)
    if err:
        return _ok(None, err[0], err[1])

    record_type = request.args.get('type', '').strip() or None
    stats = get_data_service().get_statistics(user.user_id, record_type)
    if stats is None:
        return _ok(None, '暂无记录数据', 404)
    return _ok(stats)
