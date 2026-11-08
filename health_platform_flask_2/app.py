"""东软健康数据管理平台：用 Flask 为原有服务添加 Web 界面。"""
import csv
import io
import math
import os
from datetime import date, datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, Response
import config
from services.auth_service import AuthService
from services.data_service import DataService
from utils.validator import Validator

app = Flask(__name__)
# 课堂本地演示使用；部署到服务器前必须设置独立的随机密钥。
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'local-classroom-demo-change-me')
config.init_directories()
data_service = DataService()


def current_user():
    """session 只保存用户 ID 和用户名，不把密码放入浏览器。"""
    return session.get('user')


def validate_record(data):
    """表单和 JSON 请求共用这套检查；输出可以交给原 DataService 的参数。"""
    if not isinstance(data, dict):
        return None, '请求内容必须是对象。'
    def text(field):
        value = data.get(field)
        return '' if value is None else str(value).strip()

    kind = text('record_type')
    day = text('record_date')
    notes = text('notes')
    try:
        if len(day) != 10 or date.fromisoformat(day).isoformat() != day:
            raise ValueError
    except ValueError:
        return None, '日期无效，请使用 YYYY-MM-DD 格式。'
    if not kind:
        return None, '请选择或填写记录类型。'

    result = {'record_type': kind, 'record_date': day, 'notes': notes}
    if kind == '体检':
        try:
            height = float(data.get('height', ''))
            weight = float(data.get('weight', ''))
            sugar = float(data.get('blood_sugar', ''))
            heart = float(data.get('heart_rate', ''))
            if not all(math.isfinite(n) for n in [height, weight, sugar, heart]):
                raise ValueError
            if height <= 0 or weight <= 0 or sugar < 0 or heart <= 0 or not heart.is_integer():
                raise ValueError
        except (ValueError, TypeError, OverflowError):
            return None, '身高、体重、心率须为正数，心率须为整数；血糖须为非负数。'
        bp = text('blood_pressure')
        ok, msg = Validator.validate_blood_pressure(bp)
        if not ok:
            return None, msg
        result.update(height=height, weight=weight, blood_sugar=sugar, heart_rate=int(heart), blood_pressure=bp, value='')
    elif kind == '用药':
        name = text('medicine_name')
        dosage = text('dosage')
        frequency = text('frequency')
        try:
            duration_text = text('duration_days')
            if not duration_text.isdecimal() or int(duration_text) < 1:
                raise ValueError
            duration = int(duration_text)
        except (ValueError, TypeError):
            return None, '用药天数须为正整数。'
        if not name or not dosage or not frequency:
            return None, '请填写药品名称、剂量和频次。'
        result.update(medicine_name=name, dosage=dosage, frequency=frequency, duration_days=duration, value='')
    else:
        if kind == '其他':
            kind = text('other_type')
            if not kind or kind in ('体检', '用药', '其他'):
                return None, '请填写有效的其他记录类型。'
            result['record_type'] = kind
        value = text('value')
        if not value:
            return None, '请填写记录内容。'
        result.update(value=value, unit=text('unit'))
    return result, ''


def add_record(data):
    valid, error = validate_record(data)
    if error:
        return False, error, 400
    ok, message = data_service.add_record(user_id=current_user()['user_id'], **valid)
    if not ok:
        return False, message, 500
    return True, message, 201


@app.context_processor
def common_data():
    return {'user': current_user(), 'today': date.today().isoformat()}


@app.route('/')
def index():
    records = data_service.get_user_records(current_user()['user_id']) if current_user() else []
    return render_template('index.html', records=records)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        auth = AuthService()  # 不在不同浏览器之间共享 current_user
        ok, message = auth.login(username, request.form.get('password', ''))
        if ok:
            user = auth.get_current_user()
            session.clear()
            session['user'] = {'user_id': user.user_id, 'username': user.username}
            flash(message, 'success')
            return redirect(url_for('index'))
        return render_template('login.html', error=message, username=username), 401
    return render_template('login.html', username='')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        auth = AuthService()
        ok, message = auth.register(username, request.form.get('password', ''),
                                    request.form.get('phone', '').strip(), request.form.get('email', '').strip())
        if ok:
            flash('注册成功，请登录。', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', error=message, username=username), 400
    return render_template('register.html', username='')


@app.post('/logout')
def logout():
    session.clear()
    flash('已退出登录。', 'success')
    return redirect(url_for('index'))


@app.route('/records', methods=['GET', 'POST'])
def records():
    if not current_user():
        return redirect(url_for('login'))
    error = ''
    if request.method == 'POST':
        ok, message, status = add_record(request.form.to_dict())
        if ok:
            flash(message, 'success')
            return redirect(url_for('records'))
        error = message
    selected = request.args.get('type', '')
    rows = data_service.get_user_records(current_user()['user_id'], selected or None)
    return render_template('records.html', records=rows, selected=selected, error=error,
                           form=request.form if request.method == 'POST' else {}), (400 if error and status == 400 else 500 if error else 200)


@app.get('/assessment')
def assessment():
    if not current_user():
        return redirect(url_for('login'))
    rows = data_service.get_user_records(current_user()['user_id'])
    counts = {}
    for row in rows:
        counts[row['record_type']] = counts.get(row['record_type'], 0) + 1
    exam = next((row for row in rows if row['record_type'] == '体检'), None)
    return render_template('assessment.html', records=rows, counts=counts, exam=exam)


@app.get('/records.csv')
def export_csv():
    if not current_user():
        return redirect(url_for('login'))
    rows = data_service.get_user_records(current_user()['user_id'])
    if not rows:
        flash('暂无记录可导出。', 'error')
        return redirect(url_for('records'))
    # 体检与用药字段不同，取全部字段的并集，避免遗漏。
    columns = list(dict.fromkeys(key for row in rows for key in row))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return Response('\ufeff' + stream.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=health_records.csv'})


@app.get('/report.txt')
def download_report():
    if not current_user():
        return redirect(url_for('login'))
    user = current_user()
    report, message = data_service.generate_report(user['user_id'], user['username'])
    if not report:
        flash(message, 'error')
        return redirect(url_for('assessment'))
    return Response(report.content, mimetype='text/plain',
                    headers={'Content-Disposition': 'attachment; filename=health_report.txt'})


@app.route('/api/records', methods=['GET', 'POST'])
def records_api():
    if not current_user():
        return jsonify({'ok': False, 'message': '请先登录。'}), 401
    if request.method == 'GET':
        kind = request.args.get('type', '').strip()
        rows = data_service.get_user_records(current_user()['user_id'], kind or None)
        return jsonify({'ok': True, 'count': len(rows), 'records': rows}), 200
    if not request.is_json:
        return jsonify({'ok': False, 'message': '请使用 application/json。'}), 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'ok': False, 'message': 'JSON 格式无效，且顶层必须是对象。'}), 400
    ok, message, status = add_record(payload)
    return jsonify({'ok': ok, 'message': message}), status


@app.errorhandler(500)
def internal_error(error):
    # 文件读取或保存出现异常时，不暴露文件路径等内部细节。
    if request.path.startswith('/api/'):
        return jsonify({'ok': False, 'message': '服务器处理失败，请检查数据文件或日志。'}), 500
    return render_template('error.html'), 500


if __name__ == '__main__':
    app.run(debug=True)  # 仅限本地教学调试
