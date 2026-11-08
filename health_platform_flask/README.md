# 东软健康数据管理平台（Flask 版）

将原 CLI 版健康平台（`health_platform`）转换为标准 Flask Web 项目。
保留原有 `models / services / utils` 分层架构，新增 `routes`（蓝图）、`templates`、`static` 等 Web 层。

## 功能

| 任务 | 说明 | 对应路由 |
|------|------|----------|
| 任务1 | 首页、健康记录、评测结果路由 | `/`、`/records`、`/records/add`、`/assessment`、`/assessment`（结果页） |
| 任务2 | 表单/JSON 请求处理、模板渲染、规范状态码 | 注册/登录/添加记录/评测均支持 form 与 JSON，成功 `200/201/302`，校验失败 `400`，未登录 `401/302`，未找到 `404` |
| 任务3 | 健康记录 JSON API | `/api/v1/records` 系列接口（见下） |

## 项目结构

```
health_platform_flask/
├── run.py                     # 启动入口
├── requirements.txt
├── app/
│   ├── __init__.py            # 应用工厂 create_app()
│   ├── config.py              # 多环境配置（development/testing/production）
│   ├── models/                # 数据模型（User / HealthRecord / Report）
│   ├── services/              # 业务服务（auth / data / assessment）
│   ├── utils/                 # 工具（validator / file_handler / logger）
│   ├── routes/                # 蓝图（main / auth / api）+ helpers
│   ├── templates/             # Jinja2 模板
│   └── static/css/style.css
├── data/                      # JSON 数据存储（users.json / records.json）
├── logs/                      # 运行日志
└── tests/                     # pytest 测试
```

## 快速开始

```bash
cd health_platform_flask
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run.py            # 访问 http://127.0.0.1:5000
```

运行测试：

```bash
pytest tests/ -v
```

## JSON API（任务3）

统一响应格式：`{"code": 状态码, "message": "...", "data": {...}}`

| 方法 | 路径 | 说明 | 成功状态码 |
|------|------|------|-----------|
| GET  | `/api/v1/records?user_id=U0001&type=体检` | 记录列表（未登录需传 user_id） | 200 |
| GET  | `/api/v1/records/<record_id>` | 单条记录 | 200 / 404 |
| POST | `/api/v1/records` | 创建记录（JSON），未登录需在 body 中带 user_id | 201 / 400 / 415 |
| DELETE | `/api/v1/records/<record_id>` | 删除当前登录用户的记录 | 204 / 404 |
| GET  | `/api/v1/records/statistics` | 统计信息 | 200 / 404 |
| GET  | `/api/v1/health` | 服务健康检查 | 200 |

创建记录示例：

```bash
curl -X POST http://127.0.0.1:5000/api/v1/records \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U0001","record_type":"体检","record_date":"2026-11-08",
       "height":170,"weight":65,"blood_pressure":"120/80","blood_sugar":5.6,"heart_rate":72}'
```

健康评测也可用 JSON 调用：

```bash
curl -X POST http://127.0.0.1:5000/assessment \
  -H "Content-Type: application/json" \
  -d '{"height":170,"weight":65,"blood_pressure":"120/80","blood_sugar":5.6,"heart_rate":72}'
```

## 与原项目的对应关系

| 原 CLI 模块 | Flask 版位置 | 变化 |
|-------------|--------------|------|
| `main.py`（菜单循环） | `app/routes/main.py`、`app/routes/auth.py` | 输入菜单 → Web 页面与表单 |
| `config.py` | `app/config.py` | 增加多环境配置类 |
| `models/` | `app/models/` | 原样迁移，User 增加 `to_public_dict` |
| `services/auth_service.py` | `app/services/auth_service.py` | 登录状态改为 Flask session |
| `services/data_service.py` | `app/services/data_service.py` | 原样迁移并增加 get/delete record |
| `utils/` | `app/utils/` | 原样迁移（日期增加真实日期校验） |
| — | `app/services/assessment_service.py` | 新增：健康评测（BMI/血压/血糖/心率） |
| `test_*.py` | `tests/` | 改为 pytest 接口测试 |

> 注：项目仅用于教学演示，密码哈希沿用原项目的 md5（生产环境请改用 bcrypt/argon2）。

> 本仓库不包含本地用户资料和健康记录；程序启动时自动创建数据目录，新数据保存在本地。
