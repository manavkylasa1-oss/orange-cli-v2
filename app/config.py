import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    COGNITO_REGION = os.getenv('COGNITO_REGION', '')
    COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID', '')
    COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID', '')
    COGNITO_ISSUER = os.getenv('COGNITO_ISSUER', '')
    COGNITO_JWKS_URL = os.getenv('COGNITO_JWKS_URL', '')


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    ALPHA_VANTAGE_API_KEY = 'test-key'
    COGNITO_CLIENT_ID = 'test-client'
    COGNITO_ISSUER = 'https://issuer.example.com'
    COGNITO_JWKS_URL = 'https://issuer.example.com/.well-known/jwks.json'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://kiwi_local:kiwilocaldb@localhost:3306/kiwilocal'
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f'mysql+pymysql://{os.environ.get("DB_USER", "")}:{os.environ.get("DB_PASSWORD", "")}@'
        f'{os.environ.get("DB_HOST", "")}:{os.environ.get("DB_PORT", "3306")}/{os.environ.get("DB_NAME", "")}'
    )
    DEBUG = False
    SQLALCHEMY_ECHO = False


config = {'development': DevelopmentConfig, 'production': ProductionConfig, 'test': TestConfig}


def get_config(env: str):
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)
