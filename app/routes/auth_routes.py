from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, ReviewerApplication
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration - only regular users can register"""
    if current_user.is_authenticated:
        return redirect(url_for('questions.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        real_name = request.form.get('real_name', '').strip()
        organization = request.form.get('organization', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validation
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return redirect(url_for('auth.register'))

        if not real_name:
            flash('真实姓名不能为空', 'error')
            return redirect(url_for('auth.register'))

        if not organization:
            flash('所在单位不能为空', 'error')
            return redirect(url_for('auth.register'))

        if len(username) < 3:
            flash('用户名至少需要3个字符', 'error')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('密码至少需要6个字符', 'error')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return redirect(url_for('auth.register'))

        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('auth.register'))

        # Create new user
        user = User(username=username, real_name=real_name, organization=organization, role='user')
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            flash('注册成功！请登录', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'注册失败: {str(e)}', 'error')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('questions.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'欢迎回来，{user.username}！', 'success')

            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('questions.index'))
        else:
            flash('用户名或密码错误', 'error')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('auth.login'))


@bp.route('/apply-reviewer', methods=['GET', 'POST'])
@login_required
def apply_reviewer():
    """Apply to become a reviewer"""
    if current_user.is_reviewer() or current_user.is_admin():
        flash('您已经是审核员或管理员', 'info')
        return redirect(url_for('questions.index'))

    # Check if user has pending application
    pending_app = ReviewerApplication.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).first()

    if pending_app:
        flash('您已有待审批的申请，请耐心等待', 'info')
        return redirect(url_for('questions.index'))

    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()

        if not reason:
            flash('请填写申请理由', 'error')
            return redirect(url_for('auth.apply_reviewer'))

        if len(reason) < 10:
            flash('申请理由至少需要10个字符', 'error')
            return redirect(url_for('auth.apply_reviewer'))

        # Create application
        application = ReviewerApplication(
            user_id=current_user.id,
            reason=reason,
            status='pending'
        )

        try:
            db.session.add(application)
            db.session.commit()
            flash('申请已提交，请等待管理员审批', 'success')
            return redirect(url_for('questions.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'提交申请失败: {str(e)}', 'error')
            return redirect(url_for('auth.apply_reviewer'))

    return render_template('auth/apply_reviewer.html')


@bp.route('/admin/applications')
@login_required
def admin_applications():
    """Admin view of reviewer applications"""
    if not current_user.is_admin():
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('questions.index'))

    filter_status = request.args.get('status', 'pending')

    query = ReviewerApplication.query

    if filter_status in ['pending', 'approved', 'rejected']:
        query = query.filter_by(status=filter_status)

    applications = query.order_by(ReviewerApplication.applied_at.desc()).all()

    return render_template('auth/admin_applications.html',
                         applications=applications,
                         filter_status=filter_status)


@bp.route('/admin/applications/<int:app_id>/review', methods=['POST'])
@login_required
def review_application(app_id):
    """Admin review of reviewer application"""
    if not current_user.is_admin():
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('questions.index'))

    application = ReviewerApplication.query.get_or_404(app_id)

    if application.status != 'pending':
        flash('该申请已被处理', 'warning')
        return redirect(url_for('auth.admin_applications'))

    decision = request.form.get('decision')  # 'approved' or 'rejected'
    comment = request.form.get('comment', '').strip()

    if decision not in ['approved', 'rejected']:
        flash('无效的审批决定', 'error')
        return redirect(url_for('auth.admin_applications'))

    # Update application
    application.status = decision
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.utcnow()
    application.review_comment = comment if comment else None

    # If approved, upgrade user to reviewer
    if decision == 'approved':
        user = User.query.get(application.user_id)
        user.role = 'reviewer'

    try:
        db.session.commit()
        result_text = '通过' if decision == 'approved' else '拒绝'
        flash(f'申请已{result_text}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'处理申请失败: {str(e)}', 'error')

    return redirect(url_for('auth.admin_applications'))
