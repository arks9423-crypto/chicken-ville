import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'qrmenu-dev-secret-2024-change-in-production')

    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
    VAPID_CLAIMS_EMAIL = os.environ.get('VAPID_EMAIL', 'admin@qrmenu.om')

    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB — base64 inflates size by ~33%
