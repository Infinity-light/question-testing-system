from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app.models import db, Question, TestResult, ApiCallLog, User
from app.services.testing_service import testing_service
from app.services.export_service import export_service
from datetime import datetime
import threading

bp = Blueprint('testing', __name__, url_prefix='/testing')


@bp.route('/run/<int:question_id>', methods=['POST'])
@login_required
def run_test(question_id):
    """Start a test for a specific question"""
    question = Question.query.get_or_404(question_id)

    # Check permission: only question author or admin can run tests
    if not current_user.is_admin() and question.user_id != current_user.id:
        flash('您没有权限测试此问题', 'error')
        return redirect(url_for('questions.index'))

    try:
        # Run test in background thread to avoid blocking
        def run_test_async():
            from app import create_app
            app = create_app()
            with app.app_context():
                testing_service.run_question_test(question_id)

        thread = threading.Thread(target=run_test_async)
        thread.start()

        flash(f'测试已启动: {question.title}', 'info')
        return redirect(url_for('testing.test_list'))

    except Exception as e:
        flash(f'启动测试时出错: {str(e)}', 'error')
        return redirect(url_for('questions.index'))


@bp.route('/run-sync/<int:question_id>', methods=['GET', 'POST'])
@login_required
def run_test_sync(question_id):
    """Run test and show progress"""
    question = Question.query.get_or_404(question_id)

    # Check permission: only question author or admin can run tests
    if not current_user.is_admin() and question.user_id != current_user.id:
        flash('您没有权限测试此问题', 'error')
        return redirect(url_for('questions.index'))

    try:
        # Create test result record first
        from flask import current_app
        test_result = TestResult(
            question_id=question_id,
            total_attempts=current_app.config['TEST_ATTEMPTS'],
            correct_count=0,
            success_rate=0.0,
            qualified=False,
            difficulty_status="0/8"
        )
        db.session.add(test_result)
        db.session.commit()

        # Start test in background thread
        def run_test_async():
            from app import create_app
            app = create_app()
            with app.app_context():
                testing_service.run_question_test(question_id, test_result.id)

        import threading
        thread = threading.Thread(target=run_test_async)
        thread.daemon = True
        thread.start()

        # Show progress page
        return render_template('test_progress.html',
                             question=question,
                             test_result_id=test_result.id)

    except Exception as e:
        flash(f'测试失败: {str(e)}', 'error')
        return redirect(url_for('questions.index'))


@bp.route('/results')
@login_required
def test_list():
    """Display list of all test results"""
    # Get filter parameters
    qualified_only = request.args.get('qualified', type=bool, default=False)

    # Build query - only show completed tests
    query = TestResult.query.filter_by(status='completed')

    # Filter by user role
    if current_user.is_user():
        # Regular users can only see their own question results
        query = query.join(Question).filter(Question.user_id == current_user.id)
    # Reviewers and admins can see all results

    if qualified_only:
        query = query.filter_by(qualified=True)

    test_results = query.order_by(TestResult.test_date.desc()).all()

    return render_template('test_results.html', test_results=test_results, qualified_only=qualified_only)


@bp.route('/result/<int:test_result_id>')
@login_required
def view_result(test_result_id):
    """View detailed test result"""
    test_result = TestResult.query.get_or_404(test_result_id)

    # Check permission: users can only view their own question results
    if current_user.is_user() and test_result.question.user_id != current_user.id:
        flash('您没有权限查看此测试结果', 'error')
        return redirect(url_for('testing.test_list'))

    api_logs = ApiCallLog.query.filter_by(test_result_id=test_result_id).order_by(ApiCallLog.attempt_number).all()

    return render_template('test_detail.html', test_result=test_result, api_logs=api_logs)


@bp.route('/progress/<int:test_result_id>')
@login_required
def get_progress(test_result_id):
    """Get test progress (AJAX endpoint)"""
    test_result = TestResult.query.get(test_result_id)

    if not test_result:
        return jsonify({'error': 'Test result not found'}), 404

    # Check permission
    if current_user.is_user() and test_result.question.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403

    progress = testing_service.get_test_progress(test_result_id)

    if not progress:
        return jsonify({'error': 'Test result not found'}), 404

    # Get API call logs for detailed progress
    api_logs = ApiCallLog.query.filter_by(test_result_id=test_result_id).order_by(ApiCallLog.attempt_number).all()

    # Add log details to progress
    progress['logs'] = [
        {
            'attempt_number': log.attempt_number,
            'is_correct': log.is_correct,
            'ai_answer': log.ai_answer[:100] if log.ai_answer else '',
            'error_message': log.error_message
        }
        for log in api_logs
    ]

    return jsonify(progress)


@bp.route('/export', methods=['POST'])
@login_required
def export_results():
    """Export selected test results to Excel"""
    # Only reviewers and admins can export
    if not (current_user.is_reviewer() or current_user.is_admin()):
        flash('您没有权限导出测试结果', 'error')
        return redirect(url_for('testing.test_list'))

    test_result_ids = request.form.getlist('test_result_ids', type=int)

    if not test_result_ids:
        flash('请选择要导出的测试结果', 'error')
        return redirect(url_for('testing.test_list'))

    try:
        output_path = export_service.export_to_excel(test_result_ids)
        flash(f'导出成功！文件已保存到: {output_path}', 'success')
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        flash(f'导出失败: {str(e)}', 'error')
        return redirect(url_for('testing.test_list'))


@bp.route('/export-qualified')
@login_required
def export_qualified():
    """Export all qualified questions to Excel"""
    # Only reviewers and admins can export
    if not (current_user.is_reviewer() or current_user.is_admin()):
        flash('您没有权限导出测试结果', 'error')
        return redirect(url_for('testing.test_list'))

    try:
        output_path = export_service.export_qualified_questions()

        if not output_path:
            flash('没有找到合格的测试结果', 'warning')
            return redirect(url_for('testing.test_list'))

        flash(f'导出成功！文件已保存到: {output_path}', 'success')
        return send_file(output_path, as_attachment=True)

    except Exception as e:
        flash(f'导出失败: {str(e)}', 'error')
        return redirect(url_for('testing.test_list'))


@bp.route('/delete/<int:test_result_id>', methods=['POST'])
@login_required
def delete_result(test_result_id):
    """Delete a test result"""
    test_result = TestResult.query.get_or_404(test_result_id)
    question_id = test_result.question_id

    # Check permission: only question author or admin can delete
    if not current_user.is_admin() and test_result.question.user_id != current_user.id:
        flash('您没有权限删除此测试结果', 'error')
        return redirect(url_for('testing.test_list'))

    # Get return URL from form or default to test list
    return_url = request.form.get('return_url', '')

    try:
        db.session.delete(test_result)
        db.session.commit()
        flash('测试结果删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除测试结果时出错: {str(e)}', 'error')

    # Redirect to return URL or question detail page
    if return_url == 'question_detail':
        # Use JavaScript redirect with cache busting
        response = redirect(url_for('questions.view_question', question_id=question_id))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    else:
        return redirect(url_for('testing.test_list'))


@bp.route('/delete-batch', methods=['POST'])
@login_required
def delete_batch():
    """Delete multiple test results"""
    # Only admins can batch delete
    if not current_user.is_admin():
        flash('您没有权限批量删除测试结果', 'error')
        return redirect(url_for('testing.test_list'))

    test_result_ids = request.form.getlist('test_result_ids', type=int)

    if not test_result_ids:
        flash('请选择要删除的测试结果', 'error')
        return redirect(url_for('testing.test_list'))

    try:
        deleted_count = 0
        for test_result_id in test_result_ids:
            test_result = TestResult.query.get(test_result_id)
            if test_result:
                db.session.delete(test_result)
                deleted_count += 1

        db.session.commit()
        flash(f'成功删除 {deleted_count} 个测试结果！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'批量删除时出错: {str(e)}', 'error')

    return redirect(url_for('testing.test_list'))


@bp.route('/review-list')
@login_required
def review_list():
    """Display list of test results for manual review"""
    # Only reviewers and admins can access manual review
    if not (current_user.is_reviewer() or current_user.is_admin()):
        flash('您没有权限访问人工审核功能', 'error')
        return redirect(url_for('questions.index'))

    filter_status = request.args.get('status', 'pending')
    filter_subject = request.args.get('subject', '')
    filter_difficulty = request.args.get('difficulty', '')
    filter_qualified = request.args.get('qualified', '')
    filter_submitter = request.args.get('submitter', '')

    # Build query - only show completed tests
    query = TestResult.query.filter_by(status='completed')

    # Filter by manual review status
    if filter_status == 'pending':
        query = query.filter_by(manual_review_status='pending')
    elif filter_status in ['approved', 'rejected']:
        query = query.filter_by(manual_review_status=filter_status)
    # 'all' shows all completed tests

    # Join with Question table for subject and difficulty filters
    query = query.join(Question)

    # Filter by subject
    if filter_subject:
        query = query.filter(Question.subject == filter_subject)

    # Filter by difficulty
    if filter_difficulty:
        query = query.filter(Question.difficulty == filter_difficulty)

    # Filter by AI qualification status
    if filter_qualified == 'yes':
        query = query.filter(TestResult.qualified == True)
    elif filter_qualified == 'no':
        query = query.filter(TestResult.qualified == False)

    # Filter by submitter real name
    if filter_submitter:
        query = query.join(User).filter(User.real_name == filter_submitter)

    test_results = query.order_by(TestResult.test_date.desc()).all()

    # Get unique subjects and difficulties for filter dropdowns
    subjects = db.session.query(Question.subject).distinct().order_by(Question.subject).all()
    subjects = [s[0] for s in subjects]

    difficulties = db.session.query(Question.difficulty).distinct().order_by(Question.difficulty).all()
    difficulties = [d[0] for d in difficulties]

    # Get unique submitter names for filter
    submitters = db.session.query(User.real_name).join(Question).distinct().all()
    submitters = [s[0] for s in submitters]

    return render_template('review_list.html',
                         test_results=test_results,
                         filter_status=filter_status,
                         filter_subject=filter_subject,
                         filter_difficulty=filter_difficulty,
                         filter_qualified=filter_qualified,
                         filter_submitter=filter_submitter,
                         subjects=subjects,
                         difficulties=difficulties,
                         submitters=submitters)


@bp.route('/review/<int:test_result_id>', methods=['GET', 'POST'])
@login_required
def review_test(test_result_id):
    """Manual review page for a test result"""
    # Only reviewers and admins can perform manual review
    if not (current_user.is_reviewer() or current_user.is_admin()):
        flash('您没有权限进行人工审核', 'error')
        return redirect(url_for('questions.index'))

    test_result = TestResult.query.get_or_404(test_result_id)

    if request.method == 'POST':
        decision = request.form.get('decision')  # 'approved' or 'rejected'
        comment = request.form.get('comment', '').strip()

        # Validate input
        if not decision or decision not in ['approved', 'rejected']:
            flash('请选择审核结果（通过或不通过）', 'error')
            return redirect(url_for('testing.review_test', test_result_id=test_result_id))

        # Update test result with manual review
        test_result.manual_review_status = decision
        test_result.manual_reviewed_by = current_user.username
        test_result.manual_review_time = datetime.utcnow()
        test_result.manual_review_comment = comment if comment else None

        try:
            db.session.commit()
            result_text = '通过' if decision == 'approved' else '不通过'
            flash(f'审核完成！结果：{result_text}', 'success')
            return redirect(url_for('testing.review_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'保存审核结果时出错: {str(e)}', 'error')
            return redirect(url_for('testing.review_test', test_result_id=test_result_id))

    # GET request - show review form
    api_logs = ApiCallLog.query.filter_by(test_result_id=test_result_id).order_by(ApiCallLog.attempt_number).all()

    return render_template('review_form.html',
                         test_result=test_result,
                         api_logs=api_logs)
