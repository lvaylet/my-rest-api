#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO Use JSON API specifications: http://jsonapi.org/
# TODO Configure deployment on push with Flynn (add remote, refer to Flynn docs and Python example app)

import logging
import os

import hammock
from flask import Flask, request, render_template, redirect
from flask_caching import Cache
from flask_restful import Resource, Api
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

if app.config['DEBUG']:
    app.logger.setLevel(logging.DEBUG)  # development
else:
    app.logger.setLevel(logging.INFO)  # production

# Configure Flask-Caching
cache = Cache(app, config=app.config['CACHING_REDIS'])

# Configure Flask-RESTful
api = Api(app)

# Credentials and Hammock instances
# TODO Move to beforeFirstRequest? or __init__.py when the rest of the code is moved to a dedicated file?
LMS_TOKEN = os.environ['LMS_TOKEN']
LMS = hammock.Hammock('https://talend.talentlms.com/api/v1',
                      auth=(LMS_TOKEN, ''))

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


# Resources
@api.resource('/todos/<string:todo_id>')
class Todo(Resource):
    def get(self, todo_id):
        app.logger.debug(f'Fetching todo item with ID [{todo_id}]...')
        return {todo_id: todos[todo_id]}

    def put(self, todo_id):
        payload = request.form['data']
        app.logger.debug(f'Updating todo item with ID [{todo_id}] with payload [{payload}]...')
        todos[todo_id] = payload
        return {todo_id: todos[todo_id]}, 201


@api.resource('/todos')
class TodoList(Resource):
    def get(self):
        app.logger.debug('Fetching all todo items...')
        return todos


@api.resource('/lms/users')
class LMSUserList(Resource):
    @cache.cached()
    def get(self):
        app.logger.debug('Fetching LMS users...')
        return LMS.users.GET().json()


@api.resource('/lms/courses')
class LMSCourseList(Resource):
    @cache.cached()
    def get(self):
        app.logger.debug('Fetching LMS courses...')
        return LMS.courses.GET().json()


# Views
@app.route('/')
def index():
    app.logger.debug('Redirecting to /todos...')
    return redirect('/todos')
