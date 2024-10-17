from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

# DATABASES

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",  # 디버그 레벨로 설정
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.db.backends": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",  # 요청 관련 로그 디버그 레벨로 설정
            "propagate": True,
        },
    },
}

FRONTEND_HOST = "http://localhost:5500"
