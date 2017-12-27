#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A REST API meant to be deployed with Flynn.

# Development Mode

Run a dockerized Redis (https://hub.docker.com/r/_/redis/) with default settings:
```
$ docker run --name redis-rest-api -d -p 6379:6379 redis
```

# Production Mode

Provision a Redis database from Flynn, with default settings
"""

import os
import hammock
import logging
from flask import Flask, request, render_template, redirect
from flask_caching import Cache
from flask_restful import Resource, Api
from redis import ConnectionError

# Configure Flask application
app = Flask(__name__)
# Load config from local file
# import logging.config
# try:
#     app.config.from_pyfile('app_config.py')
#     if 'LOGGING' in app.config:
#         logging.config.dictConfig(app.config['LOGGING'])
# except IOError:
#     app.logger.warning("Could not load app_config.py")

# Configure Flask-Caching with Redis
# Use environment variables in production or default values in development with Dockerized Redis
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')  # default to empty for local development
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')  # default to localhost for local development
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))  # default to 6379 for local development
REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}'
cache = Cache(app,
              config={
                  'CACHE_TYPE': 'redis',
                  'CACHE_REDIS_URL': REDIS_URL,
                  'CACHE_DEFAULT_TIMEOUT': 3600,  # in seconds
              })

# Configure Flask-RESTful
api = Api(app)

# Credentials and Hammock instances
# TODO Move to beforeFirstRequest?
LMS_TOKEN = os.environ['LMS_TOKEN']
LMS = hammock.Hammock('https://talend.talentlms.com/api/v1',
                      auth=(LMS_TOKEN, ''))

# Data
# FIXME Save in database (Redis, same as caching?)
todos = {
    'todo1': 'Remember the milk',
    'todo2': 'Change my brakepads',
}


# Logging
@app.before_first_request
def setup_logging():
    if not app.debug:
        # Have gunicorn capture logging messages from Flask
        # https://github.com/benoitc/gunicorn/issues/379
        # ---
        # In production mode, add log handler to sys.stderr
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)


# Errors
@app.errorhandler(404)
def page_not_found(e):
    app.logger.error('Page not found! Rendering error page...')
    return render_template('error.html',
                           message='Page not found!',
                           description='The requested URL was not found on the server.'), 404


@app.errorhandler(ConnectionError)
def connection_error(e):
    debug_description = 'a (dockerized?) <strong>redis-server</strong> is running locally'
    production_description = 'a <strong>redis-server</strong> has been provisioned in Flynn for this app'
    description = 'Please confirm that %s.' % (debug_description if app.debug else production_description)
    app.logger.error(f'Could not connect to the Redis cache! (at {REDIS_URL})')
    return render_template('error.html',
                           message='Could not connect to the Redis cache!',
                           description=description), 500


@api.resource('/todos/<string:todo_id>')
class Todo(Resource):
    def get(self, todo_id):
        app.logger.info(f'Fetching todo item with ID [{todo_id}]...')
        return {todo_id: todos[todo_id]}

    def put(self, todo_id):
        app.logger.info(f'Creating todo item with ID [{todo_id}]...')
        todos[todo_id] = request.form['data']
        return {todo_id: todos[todo_id]}, 201


@api.resource('/todos')
class TodoList(Resource):
    def get(self):
        app.logger.info('Fetching all todo items...')
        return todos


@api.resource('/lms/users')
class LMSUserList(Resource):
    @cache.cached()
    def get(self):
        app.logger.info('Fetching users on LMS...')
        return LMS.users.GET().json()


@api.resource('/lms/courses')
class LMSCourseList(Resource):
    @cache.cached()
    def get(self):
        app.logger.info('Fetching courses on LMS...')
        return LMS.courses.GET().json()


# Views
@app.route('/')
def index():
    app.logger.info('Redirecting to /todos...')
    return redirect('/todos')


# Enable debug mode when app is ran locally in development mode
if __name__ == '__main__':
    app.run(debug=True)
