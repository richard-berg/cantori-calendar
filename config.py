import os
import secrets


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(16)
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
