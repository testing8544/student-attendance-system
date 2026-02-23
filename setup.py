import os

files = {
    'models.py': '''from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'faculty', 'student'
    name = db.Column(db.String(100), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    status = db.Column(db.String(10), nullable=False) # 'present', 'absent'
    
    student = db.relationship('User', foreign_keys=[student_id], backref='attendances')
    faculty = db.relationship('User', foreign_keys=[faculty_id])
''',
    'app.py': '''from flask import Flask, redirect, url_for
from models import db, User
from flask_login import LoginManager
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev_secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.admin_login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.faculty import faculty_bp
    from routes.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(faculty_bp, url_prefix='/faculty')
    app.register_blueprint(student_bp, url_prefix='/student')

    @app.route('/')
    def index():
        return redirect(url_for('auth.student_login'))

    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin', name='Administrator')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
''',
    'routes/__init__.py': '',
    'routes/auth.py': '''from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from functools import wraps
from flask import abort

auth_bp = Blueprint('auth', __name__)

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def handle_login(role):
    if current_user.is_authenticated:
        if current_user.role == 'admin': return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'faculty': return redirect(url_for('faculty.dashboard'))
        else: return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, role=role).first()
        if user and user.check_password(password):
            login_user(user)
            if role == 'admin': return redirect(url_for('admin.dashboard'))
            elif role == 'faculty': return redirect(url_for('faculty.dashboard'))
            else: return redirect(url_for('student.dashboard'))
        else:
            flash(f'Invalid {role} credentials.')
            
    return render_template('login.html', role=role)

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return handle_login('admin')

@auth_bp.route('/faculty/login', methods=['GET', 'POST'])
def faculty_login():
    return handle_login('faculty')

@auth_bp.route('/student/login', methods=['GET', 'POST'])
def student_login():
    return handle_login('student')

@auth_bp.route('/logout')
@login_required
def logout():
    role = current_user.role
    logout_user()
    if role == 'admin': return redirect(url_for('auth.admin_login'))
    elif role == 'faculty': return redirect(url_for('auth.faculty_login'))
    else: return redirect(url_for('auth.student_login'))
''',
    'routes/admin.py': '''from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, User, Attendance
from .auth import role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@role_required('admin')
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/create_faculty', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_faculty():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
        else:
            new_faculty = User(username=username, role='faculty', name=name)
            new_faculty.set_password(password)
            db.session.add(new_faculty)
            db.session.commit()
            flash('Faculty created successfully.')
            return redirect(url_for('admin.dashboard'))
    return render_template('admin/create_faculty.html')

@admin_bp.route('/create_student', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_student():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
        else:
            new_student = User(username=username, role='student', name=name)
            new_student.set_password(password)
            db.session.add(new_student)
            db.session.commit()
            flash('Student created successfully.')
            return redirect(url_for('admin.dashboard'))
    return render_template('admin/create_student.html')

@admin_bp.route('/view_attendance')
@login_required
@role_required('admin')
def view_attendance():
    attendances = Attendance.query.all()
    return render_template('admin/view_attendance.html', attendances=attendances)
''',
    'routes/faculty.py': '''from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Attendance
from .auth import role_required
import datetime

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/')
@login_required
@role_required('faculty')
def dashboard():
    return render_template('faculty/dashboard.html')

@faculty_bp.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
@role_required('faculty')
def mark_attendance():
    students = User.query.filter_by(role='student').all()
    if request.method == 'POST':
        date_str = request.form.get('date')
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            date = datetime.date.today()
            
        for student in students:
            status = request.form.get(f'status_{student.id}')
            if status:
                existing = Attendance.query.filter_by(student_id=student.id, date=date).first()
                if existing:
                    existing.status = status
                    existing.faculty_id = current_user.id
                else:
                    new_att = Attendance(student_id=student.id, faculty_id=current_user.id, date=date, status=status)
                    db.session.add(new_att)
        db.session.commit()
        flash('Attendance marked successfully.')
        return redirect(url_for('faculty.dashboard'))
    return render_template('faculty/mark_attendance.html', students=students, today=datetime.date.today())

@faculty_bp.route('/view_records')
@login_required
@role_required('faculty')
def view_records():
    attendances = Attendance.query.filter_by(faculty_id=current_user.id).order_by(Attendance.date.desc()).all()
    return render_template('faculty/view_records.html', attendances=attendances)
''',
    'routes/student.py': '''from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Attendance
from .auth import role_required

student_bp = Blueprint('student', __name__)

@student_bp.route('/')
@login_required
@role_required('student')
def dashboard():
    return render_template('student/dashboard.html')

@student_bp.route('/view_attendance')
@login_required
@role_required('student')
def view_attendance():
    attendances = Attendance.query.filter_by(student_id=current_user.id).order_by(Attendance.date.desc()).all()
    total = len(attendances)
    present = sum(1 for a in attendances if a.status == 'present')
    percentage = (present / total * 100) if total > 0 else 0
    return render_template('student/view_attendance.html', attendances=attendances, percentage=percentage, total=total, present=present)
''',
    'templates/base.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attendance Management System</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">Attendance System</div>
        <div class="nav-links">
            {% if current_user.is_authenticated %}
                <span class="user-info">Logged in as: {{ current_user.name }} ({{ current_user.role | capitalize }})</span>
                {% if current_user.role == 'admin' %}
                    <a href="{{ url_for('admin.dashboard') }}">Dashboard</a>
                {% elif current_user.role == 'faculty' %}
                    <a href="{{ url_for('faculty.dashboard') }}">Dashboard</a>
                {% elif current_user.role == 'student' %}
                    <a href="{{ url_for('student.dashboard') }}">Dashboard</a>
                {% endif %}
                <a href="{{ url_for('auth.logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('auth.admin_login') }}">Admin Login</a>
                <a href="{{ url_for('auth.faculty_login') }}">Faculty Login</a>
                <a href="{{ url_for('auth.student_login') }}">Student Login</a>
            {% endif %}
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="flashes">
                    {% for message in messages %}
                        <div class="flash">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
''',
    'templates/login.html': '''{% extends 'base.html' %}
{% block content %}
<div class="card login-card">
    <h2>{{ role | capitalize }} Login</h2>
    <form method="POST">
        <div class="form-group">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" required>
        </div>
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
        </div>
        <button type="submit" class="btn">Login</button>
    </form>
</div>
{% endblock %}
''',
    'templates/admin/dashboard.html': '''{% extends 'base.html' %}
{% block content %}
<h2>Admin Dashboard</h2>
<div class="dashboard-grid">
    <a href="{{ url_for('admin.create_faculty') }}" class="card">
        <h3>Create Faculty</h3>
        <p>Add new faculty members</p>
    </a>
    <a href="{{ url_for('admin.create_student') }}" class="card">
        <h3>Create Student</h3>
        <p>Add new students</p>
    </a>
    <a href="{{ url_for('admin.view_attendance') }}" class="card">
        <h3>View Attendance</h3>
        <p>View all attendance records</p>
    </a>
</div>
{% endblock %}
''',
    'templates/admin/create_faculty.html': '''{% extends 'base.html' %}
{% block content %}
<h2>Create Faculty</h2>
<div class="card">
    <form method="POST">
        <div class="form-group">
            <label>Name</label>
            <input type="text" name="name" required>
        </div>
        <div class="form-group">
            <label>Username</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn">Create Faculty</button>
    </form>
</div>
<a href="{{ url_for('admin.dashboard') }}" class="back-link">Back to Dashboard</a>
{% endblock %}
''',
    'templates/admin/create_student.html': '''{% extends 'base.html' %}
{% block content %}
<h2>Create Student</h2>
<div class="card">
    <form method="POST">
        <div class="form-group">
            <label>Name</label>
            <input type="text" name="name" required>
        </div>
        <div class="form-group">
            <label>Username</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn">Create Student</button>
    </form>
</div>
<a href="{{ url_for('admin.dashboard') }}" class="back-link">Back to Dashboard</a>
{% endblock %}
''',
    'templates/admin/view_attendance.html': '''{% extends 'base.html' %}
{% block content %}
<h2>All Attendance Records</h2>
<div class="card">
    <table class="table">
        <thead>
            <tr>
                <th>Date</th>
                <th>Student</th>
                <th>Status</th>
                <th>Marked By (Faculty)</th>
            </tr>
        </thead>
        <tbody>
            {% for att in attendances %}
            <tr>
                <td>{{ att.date }}</td>
                <td>{{ att.student.name }} ({{ att.student.username }})</td>
                <td><span class="status-{{ att.status }}">{{ att.status | capitalize }}</span></td>
                <td>{{ att.faculty.name }}</td>
            </tr>
            {% else %}
            <tr><td colspan="4">No records found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
<a href="{{ url_for('admin.dashboard') }}" class="back-link">Back to Dashboard</a>
{% endblock %}
''',
    'templates/faculty/dashboard.html': '''{% extends 'base.html' %}
{% block content %}
<h2>Faculty Dashboard</h2>
<div class="dashboard-grid">
    <a href="{{ url_for('faculty.mark_attendance') }}" class="card">
        <h3>Mark Attendance</h3>
        <p>Record daily attendance</p>
    </a>
    <a href="{{ url_for('faculty.view_records') }}" class="card">
        <h3>View Records</h3>
        <p>View attendance you marked</p>
    </a>
</div>
{% endblock %}
''',
    'templates/faculty/mark_attendance.html': '''{% extends 'base.html' %}
{% block content %}
<h2>Mark Attendance</h2>
<div class="card">
    <form method="POST">
        <div class="form-group">
            <label>Date</label>
            <input type="date" name="date" value="{{ today }}" required>
        </div>
        <table class="table">
            <thead>
                <tr>
                    <th>Student Name</th>
                    <th>Username</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for student in students %}
                <tr>
                    <td>{{ student.name }}</td>
                    <td>{{ student.username }}</td>
                    <td>
                        <label><input type="radio" name="status_{{ student.id }}" value="present" required> Present</label>
                        <label style="margin-left: 1rem;"><input type="radio" name="status_{{ student.id }}" value="absent" required> Absent</label>
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="3">No students found.</td></tr>
                {% endfor %}
            </tbody>
        </table>
        <br>
        {% if students %}
        <button type="submit" class="btn">Submit Attendance</button>
        {% endif %}
    </form>
</div>
<a href="{{ url_for('faculty.dashboard') }}" class="back-link">Back to Dashboard</a>
{% endblock %}
''',
    'templates/faculty/view_records.html': '''{% extends 'base.html' %}
{% block content %}
<h2>Your Marked Attendance Records</h2>
<div class="card">
    <table class="table">
        <thead>
            <tr>
                <th>Date</th>
                <th>Student</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for att in attendances %}
            <tr>
                <td>{{ att.date }}</td>
                <td>{{ att.student.name }}</td>
                <td><span class="status-{{ att.status }}">{{ att.status | capitalize }}</span></td>
            </tr>
            {% else %}
            <tr><td colspan="3">No records found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
<a href="{{ url_for('faculty.dashboard') }}" class="back-link">Back to Dashboard</a>
{% endblock %}
''',
    'templates/student/dashboard.html': '''{% extends 'base.html' %}
{% block content %}
<h2>Student Dashboard</h2>
<div class="dashboard-grid">
    <a href="{{ url_for('student.view_attendance') }}" class="card">
        <h3>View Attendance</h3>
        <p>Check your attendance percentage</p>
    </a>
</div>
{% endblock %}
''',
    'templates/student/view_attendance.html': '''{% extends 'base.html' %}
{% block content %}
<h2>My Attendance</h2>
<div class="stats-grid">
    <div class="stat-card">
        <h4>Total Classes</h4>
        <div class="stat-value">{{ total }}</div>
    </div>
    <div class="stat-card">
        <h4>Classes Attended</h4>
        <div class="stat-value">{{ present }}</div>
    </div>
    <div class="stat-card">
        <h4>Attendance %</h4>
        <div class="stat-value">{{ "%.2f"|format(percentage) }}%</div>
    </div>
</div>
<div class="card">
    <table class="table">
        <thead>
            <tr>
                <th>Date</th>
                <th>Status</th>
                <th>Marked By</th>
            </tr>
        </thead>
        <tbody>
            {% for att in attendances %}
            <tr>
                <td>{{ att.date }}</td>
                <td><span class="status-{{ att.status }}">{{ att.status | capitalize }}</span></td>
                <td>{{ att.faculty.name }}</td>
            </tr>
            {% else %}
            <tr><td colspan="3">No records found.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
<a href="{{ url_for('student.dashboard') }}" class="back-link">Back to Dashboard</a>
{% endblock %}
''',
    'static/style.css': ''':root {
    --primary-color: #4f46e5;
    --primary-hover: #4338ca;
    --bg-color: #f3f4f6;
    --card-bg: #ffffff;
    --text-main: #1f2937;
    --text-muted: #6b7280;
    --border-color: #e5e7eb;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-main);
    margin: 0;
    padding: 0;
}

.navbar {
    background-color: var(--primary-color);
    color: white;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-brand {
    font-size: 1.25rem;
    font-weight: bold;
}

.nav-links a {
    color: white;
    text-decoration: none;
    margin-left: 1.5rem;
    opacity: 0.9;
}

.nav-links a:hover {
    opacity: 1;
}

.user-info {
    margin-right: 1.5rem;
    font-size: 0.9rem;
    opacity: 0.8;
}

.container {
    max-width: 1000px;
    margin: 2rem auto;
    padding: 0 1rem;
}

.card {
    background: var(--card-bg);
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
}

.login-card {
    max-width: 400px;
    margin: 4rem auto;
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.form-group input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    box-sizing: border-box;
}

.btn {
    background-color: var(--primary-color);
    color: white;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    width: 100%;
}

.btn:hover {
    background-color: var(--primary-hover);
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
}

.dashboard-grid .card {
    text-decoration: none;
    color: var(--text-main);
    transition: transform 0.2s, box-shadow 0.2s;
    display: block;
}

.dashboard-grid .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.table {
    width: 100%;
    border-collapse: collapse;
}

.table th, .table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.table th {
    font-weight: 600;
    color: var(--text-muted);
}

.status-present {
    color: #059669;
    font-weight: 500;
}

.status-absent {
    color: #dc2626;
    font-weight: 500;
}

.flashes {
    margin-bottom: 1.5rem;
}

.flash {
    background-color: #fee2e2;
    color: #991b1b;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 0.5rem;
}

.back-link {
    display: inline-block;
    margin-top: 1rem;
    color: var(--primary-color);
    text-decoration: none;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.stat-card {
    background: var(--card-bg);
    padding: 1.5rem;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-card h4 {
    margin: 0 0 0.5rem 0;
    color: var(--text-muted);
}

.stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: var(--primary-color);
}
'''
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

print("Files generated successfully.")
