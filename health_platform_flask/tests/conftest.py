"""
pytest 全局 fixture
为每个测试创建独立的临时数据目录，避免污染真实数据
"""
import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path):
    """测试客户端：使用临时目录作为数据/日志存储"""
    app = create_app('testing')

    data_dir = tmp_path / 'data'
    log_dir = tmp_path / 'logs'
    reports_dir = data_dir / 'reports'
    backup_dir = data_dir / 'backups'
    for d in (data_dir, log_dir, reports_dir, backup_dir):
        d.mkdir(parents=True)

    app.config.update(
        TESTING=True,
        DATA_DIR=str(data_dir),
        REPORTS_DIR=str(reports_dir),
        BACKUP_DIR=str(backup_dir),
        LOG_DIR=str(log_dir),
        USERS_FILE=str(data_dir / 'users.json'),
        RECORDS_FILE=str(data_dir / 'records.json'),
        WTF_CSRF_ENABLED=False,
    )

    with app.test_client() as client:
        yield client
