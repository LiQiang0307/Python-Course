# 东软健康数据管理平台 · Flask 教学版

本项目以 [命令行版 health_platform](https://github.com/LiQiang0307/Python-Course/tree/main/health_platform) 为基础，增加 Flask 页面和 JSON API。源代码参照仓库 `main` 提交 `3ec5d524c4a000669fed89a58d57bd6eeed131b6`。示例账户与记录均为虚构数据。

## 运行方法

需要 Python 3.9 或以上。在本项目目录打开终端：

```bash
python -m pip install -r requirements.txt
python app.py
```

浏览器访问 <http://127.0.0.1:5000/>。如果系统使用 `python3`，请将命令中的 `python` 改成 `python3`。停止服务：在终端按 `Ctrl+C`。

演示账户：**student1**；密码：**Student123**。也可以自行注册。运行测试：`python -m unittest discover -s tests -v`；测试使用临时数据，不会修改示例数据。

## 功能与课组任务

| 任务 | 路由 | 涉及知识 |
| --- | --- | --- |
| 首页、健康记录、评测结果 | `/`、`/records`、`/assessment` | 路由、`render_template`、Jinja 模板 |
| 表单和 JSON 请求 | `/records` 和 `/api/records` 的 POST | `request.form`、`request.get_json()`、验证和重定向 |
| 健康记录 JSON API | `/api/records` 的 GET 和 POST | `jsonify`、HTTP 状态码 |

页面支持添加、查询体检、用药和其他记录，按类型筛选、导出 CSV、下载 TXT 健康报告。评测页面展示记录汇总和最近一次体检的 BMI。原项目提供 BMI 计算和报告汇总，没有诊断或健康等级规则，因此本项目没有添加这些结论。

`models/` 沿用原来的 `HealthRecord`、`PhysicalExamRecord`、`MedicationRecord` 和 `Report`，包括原 BMI 计算；`services/` 继续负责记录、报告和用户认证；`utils/` 保留验证、文件与日志工具；`cli_main.py` 是原命令行入口，可用 `python cli_main.py` 运行。Web 入口是 `app.py`，页面在 `templates/`，样式在 `static/style.css`。

Web 使用 Flask session 保持登录；获取和保存记录时使用 session 中的用户 ID，不接受客户端指定其他用户。Web 入口增加日期及数值检查；读取损坏的 JSON 文件时中止操作，避免按空数据覆盖。为课堂简洁，每个登录请求重新创建认证服务，因此不复用命令行版的进程内连续登录失败次数限制。

## JSON API 示例

API 使用网页登录后的 session。以下是 macOS/Linux 的 curl 示例（Windows 终端引号写法可能不同）：

```bash
# 登录，把 session cookie 保存到本地文件
curl -i -c cookie.txt -X POST http://127.0.0.1:5000/login \
  -d 'username=student1&password=Student123'

# 获取当前用户的记录
curl -b cookie.txt http://127.0.0.1:5000/api/records

# 按记录类型筛选
curl -G -b cookie.txt --data-urlencode 'type=体检' http://127.0.0.1:5000/api/records

# 新增体检记录
curl -i -b cookie.txt -X POST http://127.0.0.1:5000/api/records \
  -H 'Content-Type: application/json' \
  -d '{"record_type":"体检","record_date":"2026-10-12","height":170,"weight":65,"blood_pressure":"120/80","blood_sugar":5.2,"heart_rate":72,"notes":"课堂练习"}'
```

用药 JSON 示例：

```json
{"record_type":"用药","record_date":"2026-10-12","medicine_name":"示例药品","dosage":"1片","frequency":"每日2次","duration_days":3}
```

其他记录可直接传入自定义类型：

```json
{"record_type":"睡眠","record_date":"2026-10-12","value":"7.5","unit":"小时"}
```

GET 成功返回 `200`，POST 新增成功返回 `201`；参数或 JSON 格式错误返回 `400`，未登录返回 `401`，请求类型不为 JSON 返回 `415`，保存失败返回 `500`。表单提交成功返回 `302` 并跳转，参数错误返回 `400` 并显示提示。

## 数据与使用边界

数据保存在 `data/users.json`、`data/records.json`，重启后仍保留；TXT 报告保存在 `data/reports/`；日志保存在运行目录下 `logs/`。CSV 导出会合并不同记录类型的字段。JSON 文件存储沿用原项目方案，不保证多进程并发写入。

原项目使用 MD5 保存密码，本版为兼容原账户仍沿用；MD5 不适合正式系统的密码存储。示例密钥、调试模式和 session 配置仅适合本地教学。请勿输入真实健康信息或直接部署到公网；正式部署需要重新设计认证、密码存储、数据安全及并发机制。
