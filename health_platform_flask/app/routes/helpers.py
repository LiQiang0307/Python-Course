"""路由层辅助函数"""
from functools import wraps

from flask import current_app, redirect, request, session, url_for

from ..services import AuthService, DataService, AssessmentService


def get_auth_service():
    return AuthService(current_app.config)


def get_data_service():
    return DataService(current_app.config)


def get_assessment_service():
    return AssessmentService()


def login_required(view):
    """登录保护装饰器：未登录跳转登录页，API 请求返回 401 JSON"""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            if request.path.startswith('/api/'):
                return {'code': 401, 'message': '未登录或凭证无效'}, 401
            return redirect(url_for('auth.login', next=request.path))
        return view(*args, **kwargs)

    return wrapped
