#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO Use JSON API specifications: http://jsonapi.org/

import logging
import os
from functools import wraps

import hammock
from flask import Flask, render_template, redirect, url_for
from flask_caching import Cache
from flask_restful import Api, Resource, reqparse, abort
from redis import ConnectionError

# Configure Flask application
app = Flask(__name__)

# Load configuration from object in local module
# https://realpython.com/blog/python/flask-by-example-part-1-project-setup/
config_module = os.environ['FLASK_CONFIG']
app.config.from_object(config_module)

# Configure logging
#
# NOTE: Flask logs do not show up in Gunicorn, as Gunicorn only handles itself.
# Two options there:
# 1. Extend Gunicorn's error handler with Flask's.
#    https://stackoverflow.com/questions/26578733/why-is-flask-application-not-creating-any-logs-when-hosted-by-gunicorn
#      app.logger.handlers.extend(gunicorn_error_logger.handlers)
# 2. Replace the default loggers entirely and use Gunicorn's
#      app.logger.handlers = gunicorn_error_logger.handlers
#
# The idea is to log INFO, WARNING or DEBUG messages with Gunicorn and app.logger.setLevel(logging.<LEVEL>):
# web_1    | [2017-12-29 09:58:34 +0000] [13] [INFO] Booting worker with pid: 13
# web_1    | [2017-12-29 09:58:35 +0000] [13] [INFO] this INFO shows in the log
# web_1    | [2017-12-29 09:58:35 +0000] [13] [WARNING] this WARNING shows in the log
# web_1    | [2017-12-29 09:58:35 +0000] [13] [DEBUG] this DEBUG shows in the log

# TODO Configure from file
#   if 'LOGGING' in app.config:
#       logging.config.dictConfig(app.config['LOGGING'])
# then figure out what to put in config.py to mimic the current behavior:
#   LOGGING = {
#       'version': 1,
#       'handlers': { 'console': { 'level': 'DEBUG', 'class': 'logging.StreamHandler' } },
#       'loggers': { 'worker': { 'handlers': ['console'], 'level': 'DEBUG' } }
#   }

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_error_logger.handlers

app.logger.setLevel(app.config['LOG_LEVEL'])

# Configure Flask-Caching
cache = Cache(app, config=app.config['CACHING_REDIS'])

# Configure Flask-RESTful
api = Api(app)

# Credentials and Hammock instances
# TODO Move to beforeFirstRequest? or __init__.py when the rest of the code is moved to a dedicated file?
LMS_TOKEN = os.environ['LMS_TOKEN']
LMS = hammock.Hammock('https://talend.talentlms.com/api/v1',
                      auth=(LMS_TOKEN, ''))


# Decorators
def return_as_json_api(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        raw_data = f(*args, **kwds)  # JSON response or tuple with (JSON response, response code, response headers)

        # TODO Refactor with something more pythonic, or a parser like marshmallow
        if isinstance(raw_data, tuple):
            # Parse tuple (and use default values on missing data)
            response = raw_data[0]

            try:
                response_code = raw_data[1]
            except IndexError:
                response_code = 200

            try:
                response_headers = raw_data[2]
            except IndexError:
                response_headers = {}
        else:
            response = raw_data
            response_code = 200
            response_headers = {}

        return {
            'data': response,
            'jsonapi': {
                'version': '1.0'
            }
        }, response_code, response_headers

    return wrapper


# Data
# FIXME Save in database (Redis, same as caching?)
todos = {
    'todo1': 'Remember the milk',
    'todo2': 'Change my brakepads',
}


# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    app.logger.error('Page not found! Rendering error page...')
    return render_template('error.html',
                           message='Page not found!',
                           description='The requested URL was not found on the server.'), 404


@app.errorhandler(ConnectionError)
def connection_error(e):
    debug_description = 'a (containerized?) <strong>Redis server</strong> is running locally'
    production_description = 'a <strong>Redis server</strong> has been provisioned in Flynn for this app'
    description = 'Please confirm that %s.' % (debug_description if app.debug else production_description)
    redis_url = app.config['CACHING_REDIS']['CACHE_REDIS_URL']
    app.logger.error(f'Could not connect to the Redis cache! (at {redis_url})')
    return render_template('error.html',
                           message='Could not connect to the Redis cache!',
                           description=description), 500


# Parse and validate form data
# https://flask-restful.readthedocs.io/en/latest/quickstart.html#argument-parsing
parser = reqparse.RequestParser()
parser.add_argument('task')


# Resources
@api.resource('/todo/<string:todo_id>')
class Todo(Resource):
    @return_as_json_api
    def get(self, todo_id):
        app.logger.debug(f'Fetching todo item with ID [{todo_id}]...')
        try:
            return {todo_id: todos[todo_id]}, 200
        except KeyError:
            abort(404, message=f'Todo item with ID [{todo_id}] does not exist.')

    @return_as_json_api
    def put(self, todo_id):
        args = parser.parse_args()
        task = args['task']
        app.logger.debug(f'Updating todo item with ID [{todo_id}] with task [{task}]...')
        todos[todo_id] = task
        return {todo_id: todos[todo_id]}, 201

    @return_as_json_api
    def delete(self, todo_id):
        try:
            del todos[todo_id]
            return '', 204
        except KeyError:
            abort(404, message=f'Todo item with ID [{todo_id}] does not exist.')


@api.resource('/todos')
class TodoList(Resource):
    @return_as_json_api
    def get(self):
        app.logger.debug('Fetching all todo items...')
        return todos

    @return_as_json_api
    def post(self):
        args = parser.parse_args()
        task = args['task']
        todo_id = int(max(todos.keys()).lstrip('todo')) + 1
        todo_id = f'todo{todo_id}'
        app.logger.debug(f'Creating new todo item with ID [{todo_id}] and task [{task}]...')
        todos[todo_id] = task
        return todos[todo_id], 201


@api.resource('/lms/users')
class LMSUserList(Resource):
    @cache.cached()
    @return_as_json_api
    def get(self):
        app.logger.debug('Fetching LMS users...')
        return LMS.users.GET().json()


@api.resource('/lms/courses')
class LMSCourseList(Resource):
    @cache.cached()
    @return_as_json_api
    def get(self):
        app.logger.debug('Fetching LMS courses...')
        return LMS.courses.GET().json()


# Views
@app.route('/')
def index():
    todos_url = url_for('todos')
    app.logger.debug(f'Redirecting to {todos_url}...')
    return redirect(todos_url)
