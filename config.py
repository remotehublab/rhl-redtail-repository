import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'mysql+pymysql://redtail:redtail@localhost/redtail'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    PROJECT_ROOT = PROJECT_ROOT
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'redtail_repository', 'uploads')
    PUBLIC_FOLDER = os.path.join(PROJECT_ROOT, 'public')
    PRIVATE_FOLDER = os.path.join(PROJECT_ROOT, 'private')
    KNOWN_DOMAINS = tuple(
        domain.strip()
        for domain in (os.environ.get('KNOWN_DOMAINS') or 'redtail.rhlab.ece.uw.edu').split(',')
        if domain.strip()
    )
    PUBLIC_BASE_URL = (
        os.environ.get('REDTAIL_PUBLIC_BASE_URL')
        or 'https://redtail.rhlab.ece.uw.edu'
    ).rstrip('/')
    SERVE_PUBLIC_FILES = False

class DevelopmentConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret'
    SQLALCHEMY_RECORD_QUERIES = True
    SERVE_PUBLIC_FILES = True

class StagingConfig(Config):
    pass

class ProductionConfig(Config):
    pass

class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite://'
    ASSETS_DEBUG = os.environ.get('REDTAIL_ASSETS_DEBUG', 'true').lower() == 'true'
    WTF_CSRF_ENABLED = False
    SERVE_PUBLIC_FILES = True

configurations = {
    'default': DevelopmentConfig,
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
