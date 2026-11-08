"""
应用启动入口
使用方式:
    python run.py                # 开发服务器
    flask --app run.py run       # flask cli
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
