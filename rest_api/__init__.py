#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


# Configure Flask-Caching
cache = Cache(app, config=app.config['CACHING_REDIS'])


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
