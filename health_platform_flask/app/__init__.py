"""
应用工厂模块
负责创建并初始化 Flask 应用
"""
import os

from flask import Flask, jsonify, render_template

from .config import get_config


def create_app(config_name=None):
    """创建 Flask 应用实例"""
    app = Flask(__name__)
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    _init_directories(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_template_context(app)

    return app


def _init_directories(app):
    """初始化数据、报告、备份、日志目录"""
    for dir_path in [app.config['DATA_DIR'], app.config['REPORTS_DIR'],
                     app.config['BACKUP_DIR'], app.config['LOG_DIR']]:
        os.makedirs(dir_path, exist_ok=True)


def _register_blueprints(app):
    """注册蓝图"""
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')


def _register_error_handlers(app):
    """统一错误处理，按请求类型返回 HTML 或 JSON"""

    @app.errorhandler(404)
    def not_found(e):
        if _wants_json():
            return jsonify({'code': 404, 'message': '资源不存在'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        if _wants_json():
            return jsonify({'code': 500, 'message': '服务器内部错误'}), 500
        return render_template('errors/500.html'), 500

    def _wants_json():
        return '/api/' in (request_path() or '')

    def request_path():
        from flask import request
        return request.path


def _register_template_context(app):
    """注入模板全局变量"""

    @app.context_processor
    def inject_globals():
        return {
            'APP_NAME': app.config['APP_NAME'],
            'APP_VERSION': app.config['VERSION'],
        }
