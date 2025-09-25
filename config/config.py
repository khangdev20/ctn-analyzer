"""
Configuration settings for the Flask Background Worker Bot.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class."""

    # Flask settings
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Worker settings
    WORKER_INTERVAL = int(os.environ.get('WORKER_INTERVAL', 60))  # seconds
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 4))

    # Redis settings (if using Celery)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # Database settings (if needed)
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///bot.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'bot.log')

    # Bot specific settings
    BOT_NAME = os.environ.get('BOT_NAME', 'BackgroundWorkerBot')
    BOT_VERSION = '1.0.0'

    # Discord settings
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    DISCORD_WEBHOOK = os.environ.get('DISCORD_WEBHOOK')

    # API settings
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 30))
    RATE_LIMIT = int(os.environ.get('RATE_LIMIT', 100))  # requests per minute


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    WORKER_INTERVAL = 30  # More frequent in development


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WORKER_INTERVAL = 5  # Fast for testing


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
