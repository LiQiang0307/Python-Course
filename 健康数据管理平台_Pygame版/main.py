"""运行 python main.py 启动 Pygame 版；CLI 保留在 cli_main.py。"""
from gui import HealthApp

if __name__ == '__main__':
    try:
        HealthApp().run()
    except (RuntimeError, OSError) as error:
        print(f'启动失败：{error}')
        raise SystemExit(1)
