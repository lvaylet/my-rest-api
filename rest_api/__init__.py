# -*- coding: utf-8 -*-

# TODO Use JSON API specifications: http://jsonapi.org/
# TODO Use recommended project structure
#      https://flask-restful.readthedocs.io/en/latest/intermediate-usage.html#project-structure

import logging
import os

import hammock
from flask import Flask, render_template, redirect
from flask_caching import Cache
from flask_cors import CORS
from flask_restful_swagger_2 import Api
from redis import ConnectionError

# Credentials and Hammock instances
LMS_TOKEN = os.environ['LMS_TOKEN']
LMS = hammock.Hammock('https://talend.talentlms.com/api/v1',
                      auth=(LMS_TOKEN, ''))

app = Flask(__name__)
CORS(app)  # required to access specification from swagger-ui

# Import resources after the application object is created to prevent circular references (with
# the `LMS` constant for example)
# http://flask.pocoo.org/docs/0.12/patterns/packages/#larger-applications (especially the Circular Imports note)
from rest_api.resources import TodoResource, TodoListResource, LMSCourseListResource, LMSUserListResource

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

# Configure Flask-RESTful and Flask-RESTful-Swagger-2
api = Api(app,
          title='My REST API',
          api_version='0.0')


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


api.add_resource(TodoResource, '/api/todo/<int:todo_id>')
api.add_resource(TodoListResource, '/api/todos')
api.add_resource(LMSUserListResource, '/api/lms/users')
api.add_resource(LMSCourseListResource, '/api/lms/courses')


# Redirect root to Swagger UI
@app.route('/')
@app.route('/api')
def index():
    return redirect('http://petstore.swagger.io/?url=http://localhost:8000/api/swagger.json', code=302)
