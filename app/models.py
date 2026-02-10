from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(100), nullable=False)  # 真实姓名
    organization = db.Column(db.String(200), nullable=False)  # 所在单位
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin', 'reviewer', 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    questions = db.relationship('Question', backref='author', lazy=True)
    reviewer_applications = db.relationship('ReviewerApplication', foreign_keys='ReviewerApplication.user_id', backref='applicant', lazy=True)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'

    def is_reviewer(self):
        """Check if user is reviewer"""
        return self.role == 'reviewer'

    def is_user(self):
        """Check if user is regular user"""
        return self.role == 'user'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class ReviewerApplication(db.Model):
    """Reviewer application model"""
    __tablename__ = 'reviewer_applications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)  # Application reason
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    review_comment = db.Column(db.Text)

    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_applications')

    def __repr__(self):
        return f'<ReviewerApplication {self.id}: User {self.user_id} - {self.status}>'


class Question(db.Model):
    """Question model for storing professional domain questions"""
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Question author
    title = db.Column(db.String(200), nullable=False)
    question_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(50), nullable=False)  # math, physics, chemistry, biology, law, finance, medicine, STEM
    difficulty = db.Column(db.String(20), nullable=False)  # 高中, 大学
    knowledge_points = db.Column(db.Text, nullable=False)  # comma-separated tags
    question_text = db.Column(db.Text, nullable=False)  # LaTeX format
    standard_answer = db.Column(db.Text, nullable=False)
    solution_approach = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test_results = db.relationship('TestResult', backref='question', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Question {self.id}: {self.title}>'


class TestResult(db.Model):
    """Test result model for storing AI testing outcomes"""
    __tablename__ = 'test_results'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    test_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_attempts = db.Column(db.Integer, default=8)
    correct_count = db.Column(db.Integer, nullable=False)
    success_rate = db.Column(db.Float, nullable=False)  # percentage
    qualified = db.Column(db.Boolean, nullable=False)  # true if success_rate < 50%
    difficulty_status = db.Column(db.String(20), nullable=False)  # format "X/8"
    status = db.Column(db.String(20), default='running')  # 'running' or 'completed'

    # Manual review fields
    manual_review_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    manual_reviewed_by = db.Column(db.String(100))  # reviewer name
    manual_review_time = db.Column(db.DateTime)  # review timestamp
    manual_review_comment = db.Column(db.Text)  # optional review comment

    # Relationships
    api_call_logs = db.relationship('ApiCallLog', backref='test_result', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TestResult {self.id}: Q{self.question_id} - {self.correct_count}/{self.total_attempts}>'


class ApiCallLog(db.Model):
    """API call log model for storing individual attempt details"""
    __tablename__ = 'api_call_logs'

    id = db.Column(db.Integer, primary_key=True)
    test_result_id = db.Column(db.Integer, db.ForeignKey('test_results.id'), nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False)  # 1-8
    ai_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    verification_response = db.Column(db.Text)
    call_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text)

    def __repr__(self):
        return f'<ApiCallLog {self.id}: Attempt {self.attempt_number}>'
