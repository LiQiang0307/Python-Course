"""
认证蓝图：注册 / 登录 / 登出
支持表单与 JSON 提交，返回规范状态码
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..utils import Validator
from .helpers import get_auth_service

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册：GET 渲染表单，POST 处理提交（成功 302 / 校验失败 400）"""
    if request.method == 'GET':
        return render_template('auth/register.html')

    data = _get_request_data()
    username = Validator.clean_input(data.get('username', ''))
    password = data.get('password', '')
    phone = Validator.clean_phone_input(data.get('phone', ''))
    email = Validator.clean_email_input(data.get('email', ''))

    success, message, user = get_auth_service().register(
        username=username, password=password, phone=phone, email=email)

    if not success:
        return _auth_error(message, 'auth/register.html')

    # 注册成功后自动登录
    get_auth_service().login_session(user)

    if _wants_json():
        return {'code': 201, 'message': message,
                'data': user.to_public_dict()}, 201

    flash(message, 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录：GET 渲染表单，POST 处理提交"""
    if request.method == 'GET':
        return render_template('auth/login.html')

    data = _get_request_data()
    username = Validator.clean_input(data.get('username', ''))
    password = data.get('password', '')

    if not username or not password:
        return _auth_error('用户名和密码不能为空', 'auth/login.html')

    success, message, user = get_auth_service().login(username, password)
    if not success:
        return _auth_error(message, 'auth/login.html')

    get_auth_service().login_session(user)

    if _wants_json():
        return {'code': 200, 'message': message,
                'data': user.to_public_dict()}, 200

    next_url = request.args.get('next') or request.form.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(url_for('main.index'))


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """用户登出"""
    username = session.get('username')
    get_auth_service().logout_session()

    if _wants_json():
        return {'code': 200, 'message': '登出成功'}, 200

    if username:
        flash(f'再见，{username}！', 'info')
    return redirect(url_for('main.index'))


# ---------- 内部辅助 ----------
def _get_request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form


def _auth_error(message, template):
    if _wants_json():
        return {'code': 400, 'message': message}, 400
    flash(message, 'danger')
    return render_template(template, next=request.args.get('next', '')), 400


def _wants_json():
    return request.is_json or request.path.startswith('/api/')
