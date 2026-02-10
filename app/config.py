import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///questions.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Anthropic Claude API
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    ANTHROPIC_BASE_URL = os.getenv('ANTHROPIC_BASE_URL', 'https://deeprouter.top/v1')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-opus-4-5-20251101')

    # Testing parameters
    TEST_ATTEMPTS = int(os.getenv('TEST_ATTEMPTS', 8))
    QUALIFICATION_THRESHOLD = float(os.getenv('QUALIFICATION_THRESHOLD', 50))

    # Export directory
    EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
