from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Question, User

bp = Blueprint('questions', __name__)


@bp.route('/')
@login_required
def index():
    """Display list of all questions"""
    # Get filter parameters
    subject = request.args.get('subject', '')
    difficulty = request.args.get('difficulty', '')
    submitter = request.args.get('submitter', '')

    # Build query based on user role
    if current_user.is_user():
        # Regular users can only see their own questions
        query = Question.query.filter_by(user_id=current_user.id)
    else:
        # Reviewers and admins can see all questions
        query = Question.query

    if subject:
        query = query.filter_by(subject=subject)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if submitter:
        query = query.join(User).filter(User.real_name == submitter)

    questions = query.order_by(Question.created_at.desc()).all()

    # Get unique subjects and difficulties for filters
    subjects = db.session.query(Question.subject).distinct().all()
    subjects = [s[0] for s in subjects]

    difficulties = db.session.query(Question.difficulty).distinct().all()
    difficulties = [d[0] for d in difficulties]

    # Get unique submitter names for filter
    submitters = db.session.query(User.real_name).join(Question).distinct().all()
    submitters = [s[0] for s in submitters]

    return render_template('question_list.html',
                         questions=questions,
                         subjects=subjects,
                         difficulties=difficulties,
                         submitters=submitters,
                         current_subject=subject,
                         current_difficulty=difficulty,
                         current_submitter=submitter)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_question():
    """Create a new question"""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        question_type = request.form.get('question_type', '').strip()
        subject = request.form.get('subject', '').strip()
        if subject == 'custom':
            subject = request.form.get('custom_subject', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        knowledge_points = request.form.get('knowledge_points', '').strip()
        question_text = request.form.get('question_text', '').strip()
        standard_answer = request.form.get('standard_answer', '').strip()
        solution_approach = request.form.get('solution_approach', '').strip()

        # Validate required fields
        if not all([title, question_type, subject, difficulty, knowledge_points,
                   question_text, standard_answer, solution_approach]):
            flash('所有字段都是必填的', 'error')
            return render_template('question_form.html', form_data=request.form)

        # Create question with current user as author
        question = Question(
            user_id=current_user.id,
            title=title,
            question_type=question_type,
            subject=subject,
            difficulty=difficulty,
            knowledge_points=knowledge_points,
            question_text=question_text,
            standard_answer=standard_answer,
            solution_approach=solution_approach
        )

        try:
            db.session.add(question)
            db.session.commit()
            flash('问题创建成功！正在自动运行测试...', 'success')
            # 自动运行测试
            return redirect(url_for('testing.run_test_sync', question_id=question.id))
        except Exception as e:
            db.session.rollback()
            flash(f'创建问题时出错: {str(e)}', 'error')
            return render_template('question_form.html', form_data=request.form)

    return render_template('question_form.html', form_data=None)


@bp.route('/edit/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    """Edit an existing question"""
    question = Question.query.get_or_404(question_id)

    # Check permission: only question author or admin can edit
    if not current_user.is_admin() and question.user_id != current_user.id:
        flash('您没有权限编辑此问题', 'error')
        return redirect(url_for('questions.index'))

    if request.method == 'POST':
        # Get form data
        question.title = request.form.get('title', '').strip()
        question.question_type = request.form.get('question_type', '').strip()
        question.subject = request.form.get('subject', '').strip()
        if question.subject == 'custom':
            question.subject = request.form.get('custom_subject', '').strip()
        question.difficulty = request.form.get('difficulty', '').strip()
        question.knowledge_points = request.form.get('knowledge_points', '').strip()
        question.question_text = request.form.get('question_text', '').strip()
        question.standard_answer = request.form.get('standard_answer', '').strip()
        question.solution_approach = request.form.get('solution_approach', '').strip()

        # Validate required fields
        if not all([question.title, question.question_type, question.subject,
                   question.difficulty, question.knowledge_points, question.question_text,
                   question.standard_answer, question.solution_approach]):
            flash('所有字段都是必填的', 'error')
            return render_template('question_form.html', question=question, form_data=request.form)

        try:
            db.session.commit()
            flash('问题更新成功！', 'success')
            return redirect(url_for('questions.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新问题时出错: {str(e)}', 'error')
            return render_template('question_form.html', question=question, form_data=request.form)

    return render_template('question_form.html', question=question, form_data=None)


@bp.route('/delete/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete a question"""
    question = Question.query.get_or_404(question_id)

    # Check permission: only question author or admin can delete
    if not current_user.is_admin() and question.user_id != current_user.id:
        flash('您没有权限删除此问题', 'error')
        return redirect(url_for('questions.index'))

    try:
        db.session.delete(question)
        db.session.commit()
        flash('问题删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除问题时出错: {str(e)}', 'error')

    return redirect(url_for('questions.index'))


@bp.route('/view/<int:question_id>')
@login_required
def view_question(question_id):
    """View question details"""
    question = Question.query.get_or_404(question_id)

    # Check permission: users can only view their own questions
    if current_user.is_user() and question.user_id != current_user.id:
        flash('您没有权限查看此问题', 'error')
        return redirect(url_for('questions.index'))

    return render_template('question_detail.html', question=question)
