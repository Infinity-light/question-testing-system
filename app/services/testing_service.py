from datetime import datetime
from flask import current_app
from app.models import db, Question, TestResult, ApiCallLog
from app.services.claude_service import claude_service


class TestingService:
    """Service for orchestrating question testing with Claude AI"""

    def cleanup_incomplete_tests(self, max_age_minutes=30):
        """
        Clean up incomplete test results that are older than max_age_minutes.

        Args:
            max_age_minutes: Maximum age in minutes for incomplete tests
        """
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)

        # Find incomplete tests older than cutoff time
        incomplete_tests = TestResult.query.filter(
            TestResult.status == 'running',
            TestResult.test_date < cutoff_time
        ).all()

        for test_result in incomplete_tests:
            current_app.logger.info(f"Cleaning up incomplete test result {test_result.id}")
            # Delete associated API logs first
            ApiCallLog.query.filter_by(test_result_id=test_result.id).delete()
            db.session.delete(test_result)

        if incomplete_tests:
            db.session.commit()
            current_app.logger.info(f"Cleaned up {len(incomplete_tests)} incomplete test results")

        return len(incomplete_tests)

    def run_question_test(self, question_id: int, test_result_id: int = None) -> TestResult:
        """
        Run a complete test on a question with 8 stateless API attempts.

        Args:
            question_id: The ID of the question to test
            test_result_id: Optional existing test result ID to update

        Returns:
            TestResult object with test outcomes
        """
        question = Question.query.get(question_id)
        if not question:
            raise ValueError(f"Question with ID {question_id} not found")

        # Use existing test result or create new one
        if test_result_id:
            test_result = TestResult.query.get(test_result_id)
            if not test_result:
                raise ValueError(f"Test result with ID {test_result_id} not found")
        else:
            # Create test result record
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

        correct_count = 0
        total_attempts = current_app.config['TEST_ATTEMPTS']
        completed_attempts = 0

        current_app.logger.info(f"Starting test for question {question_id}: {question.title}")

        try:
            # Run 8 independent attempts
            for attempt_num in range(1, total_attempts + 1):
                try:
                    current_app.logger.info(f"Attempt {attempt_num}/{total_attempts}")

                    # Call Claude to answer the question (stateless)
                    ai_answer = claude_service.call_claude_stateless(question.question_text)
                    current_app.logger.info(f"AI Answer: {ai_answer[:100]}...")

                    # Add rate limiting delay
                    claude_service.add_rate_limit_delay()

                    # Verify the answer using Claude
                    is_correct, verification_response = claude_service.verify_answer(
                        ai_answer,
                        question.standard_answer,
                        question.question_text
                    )
                    current_app.logger.info(f"Verification: {'Correct' if is_correct else 'Incorrect'}")

                    if is_correct:
                        correct_count += 1

                    # Log the API call
                    api_log = ApiCallLog(
                        test_result_id=test_result.id,
                        attempt_number=attempt_num,
                        ai_answer=ai_answer,
                        is_correct=is_correct,
                        verification_response=verification_response,
                        call_timestamp=datetime.utcnow()
                    )
                    db.session.add(api_log)
                    db.session.commit()

                    completed_attempts += 1

                    # Add rate limiting delay before next attempt
                    if attempt_num < total_attempts:
                        claude_service.add_rate_limit_delay()

                except Exception as e:
                    error_msg = f"Error in attempt {attempt_num}: {str(e)}"
                    current_app.logger.error(error_msg)

                    # Log the error
                    api_log = ApiCallLog(
                        test_result_id=test_result.id,
                        attempt_number=attempt_num,
                        ai_answer="",
                        is_correct=False,
                        verification_response="",
                        call_timestamp=datetime.utcnow(),
                        error_message=error_msg
                    )
                    db.session.add(api_log)
                    db.session.commit()

                    completed_attempts += 1

            # Calculate final results
            success_rate = (correct_count / total_attempts) * 100
            qualified = success_rate < current_app.config['QUALIFICATION_THRESHOLD']
            difficulty_status = f"{correct_count}/{total_attempts}"

            # Update test result
            test_result.correct_count = correct_count
            test_result.success_rate = success_rate
            test_result.qualified = qualified
            test_result.difficulty_status = difficulty_status
            test_result.status = 'completed'  # Mark as completed
            db.session.commit()

            current_app.logger.info(
                f"Test completed: {correct_count}/{total_attempts} correct "
                f"({success_rate:.1f}%), Qualified: {qualified}"
            )

            return test_result

        except Exception as e:
            # If test was interrupted and not all attempts completed, delete the test result
            current_app.logger.error(f"Test interrupted: {str(e)}")
            if completed_attempts < total_attempts:
                current_app.logger.info(f"Deleting incomplete test result (completed {completed_attempts}/{total_attempts})")
                # Delete associated API logs first
                ApiCallLog.query.filter_by(test_result_id=test_result.id).delete()
                db.session.delete(test_result)
                db.session.commit()
            raise

    def get_test_progress(self, test_result_id: int) -> dict:
        """
        Get the current progress of a test.

        Args:
            test_result_id: The ID of the test result

        Returns:
            Dictionary with progress information
        """
        test_result = TestResult.query.get(test_result_id)
        if not test_result:
            return None

        completed_attempts = ApiCallLog.query.filter_by(
            test_result_id=test_result_id
        ).count()

        return {
            'test_result_id': test_result_id,
            'total_attempts': test_result.total_attempts,
            'completed_attempts': completed_attempts,
            'correct_count': test_result.correct_count,
            'is_complete': completed_attempts >= test_result.total_attempts
        }


# Global service instance
testing_service = TestingService()
