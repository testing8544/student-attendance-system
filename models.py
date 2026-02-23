from flask_sqlalchemy import SQLAlchemy
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
    department = db.Column(db.String(50), nullable=True) # e.g., 'B.Tech CSE'
    branch = db.Column(db.String(50), nullable=True) # e.g., 'B.Tech CSE'
    year = db.Column(db.String(20), nullable=True)   # e.g., '1st Year'
    section = db.Column(db.String(10), nullable=True) # e.g., 'A', 'B'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    period = db.Column(db.Integer, nullable=False) # 1 to 6
    status = db.Column(db.String(10), nullable=False) # 'present', 'absent'
    
    # Add unique constraint to prevent duplicate attendance for same student, date, and period
    __table_args__ = (db.UniqueConstraint('student_id', 'date', 'period', name='_student_date_period_uc'),)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='attendances')
    faculty = db.relationship('User', foreign_keys=[faculty_id])
