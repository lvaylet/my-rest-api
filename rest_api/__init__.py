#!/usr/bin/env python

"""
A REST API meant to be deployed with Flynn.

# Development

Run a dockerized Redis (https://hub.docker.com/r/_/redis/) with default settings:
```
$ docker run --name redis-rest-api -d -p 6379:6379 redis
```

# Production

Provision a Redis database from Flynn, with default settings
"""

import os
import hammock
# import logging.confg
from flask import Flask, request, render_template, redirect
from flask_caching import Cache
from flask_restful import Resource, Api
from redis import ConnectionError

# Configure Flask application
app = Flask(__name__)
# app.config.from_pyfile('config.py')
# if 'LOGGING' in app.config:
#     logging.config.dictConfig(app.config['LOGGING'])

# Configure Flask-Caching with Redis
# Use environment variables in production or default values in development with Dockerized Redis
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')  # default to empty for local development
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')  # default to localhost for local development
REDIS_PORT = int(os.getenv('PORT', 6379))  # default to 6379 for local development
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

todos = {
    'todo1': 'Remember the milk',
    'todo2': 'Change my brakepads',
}


# Errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                           message='Page not found!',
                           description='The requested URL was not found on the server.'), 404


@app.errorhandler(ConnectionError)
def connection_error(e):
    debug_description = "a (dockerized?) <strong>redis-server</strong> is running locally"
    production_description = "a <strong>redis-server</strong> has been provisioned in Flynn for this app"
    description = "Please confirm that %s." % (debug_description if app.debug else production_description)
    return render_template('error.html',
                           message='Could not connect to the Redis cache!',
                           description=description), 500


@api.resource('/todos/<string:todo_id>')
class Todo(Resource):
    def get(self, todo_id):
        return {todo_id: todos[todo_id]}

    def put(self, todo_id):
        todos[todo_id] = request.form['data']
        return {todo_id: todos[todo_id]}, 201


@api.resource('/todos')
class TodoList(Resource):
    def get(self):
        return todos


@api.resource('/lms/users')
class LMSUserList(Resource):
    @cache.cached()
    def get(self):
        return LMS.users.GET().json()


@api.resource('/lms/courses')
class LMSCourseList(Resource):
    @cache.cached()
    def get(self):
        return LMS.courses.GET().json()


# Views
@app.route('/')
def index():
    return redirect('/todos')


# Enable debug mode when app is ran locally in development mode
if __name__ == '__main__':
    app.run(debug=True)
