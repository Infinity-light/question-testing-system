from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import Config
from app.models import db


def create_app(config_class=Config):
    """Flask application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes import question_routes, testing_routes, auth_routes
    app.register_blueprint(question_routes.bp)
    app.register_blueprint(testing_routes.bp)
    app.register_blueprint(auth_routes.bp)

    # Create database tables
    with app.app_context():
        db.create_all()

        # Clean up incomplete tests on startup
        from app.services.testing_service import testing_service
        try:
            cleaned = testing_service.cleanup_incomplete_tests(max_age_minutes=30)
            if cleaned > 0:
                app.logger.info(f"Cleaned up {cleaned} incomplete test results on startup")
        except Exception as e:
            app.logger.error(f"Error cleaning up incomplete tests: {str(e)}")

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return "Internal server error", 500

    return app
