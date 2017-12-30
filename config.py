import os
import logging

# Helper constants for Redis caching
# Use environment variables in production or default values in development with Dockerized Redis
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')  # default to empty for local development
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')  # default to localhost for local development
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))  # default to 6379 for local development
REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}'


class BaseConfig(object):
    DEBUG = False
    TESTING = False
    CACHING_REDIS = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': REDIS_URL,
        'CACHE_DEFAULT_TIMEOUT': 3600,  # in seconds
    }


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8000
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(BaseConfig):
    LOG_LEVEL = logging.INFO
