"""
主页面蓝图
任务1：首页、健康记录、评测结果路由
任务2：表单/JSON请求处理、模板渲染与规范状态码
"""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..services import AssessmentService
from ..utils import Validator
from .helpers import get_data_service, login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首页：未登录显示欢迎页，已登录显示数据总览"""
    from .helpers import get_auth_service
    user = get_auth_service().get_current_user()
    if not user:
        return render_template('index.html', user=None)

    records = get_data_service().get_user_records(user.user_id)
    record_types = {}
    for record in records:
        record_types[record['record_type']] = record_types.get(record['record_type'], 0) + 1

    stats = {
        'total': len(records),
        'by_type': record_types,
        'exam_count': record_types.get('体检', 0),
        'medication_count': record_types.get('用药', 0),
    }
    recent = records[:5]
    return render_template('index.html', user=user, stats=stats, recent=recent)


@main_bp.route('/records')
@login_required
def records():
    """健康记录列表页，支持 ?type=体检|用药 筛选"""
    record_type = request.args.get('type', '').strip() or None
    if record_type not in (None, '体检', '用药', '其他'):
        flash('无效的记录类型筛选条件', 'warning')
        return redirect(url_for('main.records')), 302

    user = _current_user()
    records = get_data_service().get_user_records(user.user_id, record_type)
    return render_template('records/list.html', user=user, records=records,
                           current_type=record_type or '')


@main_bp.route('/records/add', methods=['GET', 'POST'])
@login_required
def add_record():
    """添加健康记录：GET 渲染表单，POST 处理表单/JSON 提交"""
    user = _current_user()

    if request.method == 'GET':
        return render_template('records/add.html', user=user)

    # 同时支持表单与 JSON 提交（任务2）
    data = _get_request_data()

    record_type = Validator.clean_input(data.get('record_type', ''))
    record_date = Validator.clean_input(data.get('record_date', ''))
    if not record_date:
        record_date = datetime.now().strftime('%Y-%m-%d')

    kwargs = {}
    if record_type == '体检':
        kwargs = {
            'height': _to_float(data.get('height')),
            'weight': _to_float(data.get('weight')),
            'blood_pressure': Validator.clean_input(data.get('blood_pressure', '')),
            'blood_sugar': _to_float(data.get('blood_sugar')),
            'heart_rate': int(_to_float(data.get('heart_rate'))),
            'notes': Validator.clean_input(data.get('notes', '')),
        }
        if kwargs['blood_pressure'] and not Validator.validate_blood_pressure(kwargs['blood_pressure'])[0]:
            msg = Validator.validate_blood_pressure(kwargs['blood_pressure'])[1]
            return _add_record_error(msg)
    elif record_type == '用药':
        kwargs = {
            'medicine_name': Validator.clean_input(data.get('medicine_name', '')),
            'dosage': Validator.clean_input(data.get('dosage', '')),
            'frequency': Validator.clean_input(data.get('frequency', '')),
            'duration_days': int(_to_float(data.get('duration_days'))),
            'notes': Validator.clean_input(data.get('notes', '')),
        }
    else:
        record_type = Validator.clean_input(data.get('record_type')) or '其他'
        kwargs = {
            'unit': Validator.clean_input(data.get('unit', '')),
            'notes': Validator.clean_input(data.get('notes', '')),
        }

    value = Validator.clean_input(data.get('value', ''))
    success, message, record = get_data_service().add_record(
        user.user_id, record_type, record_date, value, **kwargs)

    if not success:
        return _add_record_error(message)

    if _wants_json():
        return {'code': 201, 'message': message,
                'data': record.to_dict() if record else None}, 201

    flash(message, 'success')
    return redirect(url_for('main.records'))


def _add_record_error(message):
    """表单/JSON 校验失败时返回 400"""
    if _wants_json():
        return {'code': 400, 'message': message}, 400
    flash(message, 'danger')
    return redirect(url_for('main.add_record')), 302


@main_bp.route('/assessment', methods=['GET', 'POST'])
def assessment():
    """健康评测：GET 渲染评测表单，POST 计算并渲染评测结果"""
    if request.method == 'GET':
        return render_template('assessment/index.html')

    data = _get_request_data()
    height = _to_float(data.get('height'))
    weight = _to_float(data.get('weight'))
    blood_pressure = Validator.clean_input(data.get('blood_pressure', ''))
    blood_sugar = _to_float(data.get('blood_sugar'))
    heart_rate = int(_to_float(data.get('heart_rate')))

    errors = []
    if blood_pressure:
        is_valid, msg = Validator.validate_blood_pressure(blood_pressure)
        if not is_valid:
            errors.append(msg)
    if not any([height, weight, blood_pressure, blood_sugar, heart_rate]):
        errors.append('请至少填写一项评测指标')

    if errors:
        if _wants_json():
            return {'code': 400, 'message': '；'.join(errors)}, 400
        for err in errors:
            flash(err, 'danger')
        return render_template('assessment/index.html'), 400

    result = AssessmentService.full_assessment(height, weight, blood_pressure,
                                               blood_sugar, heart_rate)

    # 勾选"保存为体检记录"且已登录时保存
    save_as_record = request.form.get('save_record') == 'on' or data.get('save_record') is True
    saved_message = None
    if save_as_record:
        from .helpers import get_auth_service
        user = get_auth_service().get_current_user()
        if user:
            success, message, _ = get_data_service().add_record(
                user.user_id, '体检', datetime.now().strftime('%Y-%m-%d'),
                f"BP:{blood_pressure}, BS:{blood_sugar}",
                height=height, weight=weight, blood_pressure=blood_pressure,
                blood_sugar=blood_sugar, heart_rate=heart_rate,
                notes='健康评测保存')
            saved_message = message if success else message

    if _wants_json():
        payload = {'code': 200, 'message': '评测完成', 'data': result}
        if saved_message:
            payload['data']['saved_message'] = saved_message
        return payload, 200

    return render_template('assessment/result.html', result=result,
                           inputs={'height': height, 'weight': weight,
                                   'blood_pressure': blood_pressure,
                                   'blood_sugar': blood_sugar,
                                   'heart_rate': heart_rate},
                           saved_message=saved_message)


# ---------- 内部辅助 ----------
def _current_user():
    """获取当前登录用户（调用方需保证已登录）"""
    from .helpers import get_auth_service
    return get_auth_service().get_current_user()


def _get_request_data():
    """统一获取表单或 JSON 请求数据"""
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form


def _to_float(value):
    """安全转换为 float，失败返回 0"""
    cleaned = Validator.clean_numeric_input(str(value)) if value not in (None, '') else ''
    try:
        return float(cleaned) if cleaned else 0
    except ValueError:
        return 0


def _wants_json():
    return request.is_json or request.path.startswith('/api/')
