#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO Use JSON API specifications: http://jsonapi.org/
# TODO Add description of .env (and LMS token) in README.md
# TODO Use recommended project structure
#      https://flask-restful.readthedocs.io/en/latest/intermediate-usage.html#project-structure

import logging
import os
from functools import wraps

from flask import Flask, render_template, request, redirect
from flask_caching import Cache
from flask_cors import CORS
from flask_restful_swagger_2 import Api
from flask_restful_swagger_2 import swagger, Resource
from redis import ConnectionError

from rest_api import LMS
from rest_api.models import TodoModel, ErrorModel

app = Flask(__name__)
CORS(app)  # required to access specification from swagger-ui

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


# Initial model
# FIXME Save in database (Redis, same as caching?)
todos = [
    {
        'id': 1,
        'description': 'Remember the milk',
        'completed': False
    },
    {
        'id': 2,
        'description': 'Change my breakpads',
        'completed': True
    }
]


# Decorators
# TODO Handle 'errors' field too. Use response code to decide whether to return 'data' or 'errors'?
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


class TodoResource(Resource):
    # @return_as_json_api
    @swagger.doc({
        'tags': ['todo'],
        'description': 'Returns a todo item',
        'parameters': [
            {
                'name': 'todo_id',
                'description': 'Todo identifier',
                'in': 'path',
                'type': 'string',
                'required': True
            }
        ],
        'responses': {
            '200': {
                'description': 'Success',
                'schema': TodoModel,
                'examples': {
                    'application/json': {
                        'id': 1,
                        'description': 'Remember the milk',
                        'completed': False
                    }
                }
            }
        }
    })
    def get(self, todo_id):
        app.logger.debug(f'Fetching todo item with ID [{todo_id}]...')

        todo = next((t for t in todos if t['id'] == todo_id), None)

        if todo is None:
            return ErrorModel(**{'message': f'Todo item with ID [{todo_id}] not found'}), 404

        # Return data through schema model
        return TodoModel(**todo), 200

    # @return_as_json_api
    @swagger.doc({
        'tags': ['todo'],
        'description': 'Updates a todo item',
        'parameters': [
            {
                'name': 'todo_id',
                'description': 'Todo identifier',
                'in': 'path',
                'type': 'string',
                'required': True
            },
            {
                'name': 'payload',
                'description': 'Request body',
                'in': 'body',
                'schema': TodoModel,
                'required': True
            }
        ],
        'responses': {
            '200': {
                'description': 'Success',
                'schema': TodoModel,
                'examples': {
                    'application/json': {
                        'id': 1,
                        'description': 'Remember the milk',
                        'completed': False
                    }
                }
            }
        }
    })
    def put(self, todo_id):
        payload = request.get_json()  # updated details are in the body

        app.logger.debug(f'Updating todo item with ID [{todo_id}] with payload [{payload}]...')

        # TODO Replace with next(...), like GET and DELETE?
        for todo in todos:
            if todo['id'] == todo_id:
                todo.update(payload)
                # FIXME Replace with TodoModel(...)?
                return todo, 201
        return 'Todo item does not exist', 404

    # @return_as_json_api
    @swagger.doc({
        'tags': ['todo'],
        'description': 'Deletes a todo item',
        'parameters': [
            {
                'name': 'todo_id',
                'description': 'Todo identifier',
                'in': 'path',
                'type': 'string',
                'required': True
            }
        ],
        'responses': {
            '204': {
                'description': 'Success',
            }
        }
    })
    def delete(self, todo_id):
        todo = next((t for t in todos if t['id'] == todo_id), None)

        if todo is None:
            return ErrorModel(**{'message': f'Todo item with ID [{todo_id}] not found'}), 404
        else:
            todos.remove(todo)
            return '', 204


class TodoListResource(Resource):
    # @return_as_json_api
    @swagger.doc({
        'tags': ['todos'],
        'description': 'Returns all todo items',
        'parameters': [
            {
                'name': 'completed',
                'description': 'Filter by status',
                'type': 'boolean',
                'in': 'query'
            }
        ],
        'responses': {
            '200': {
                'description': 'Success',
                'schema': TodoModel,
                'examples': {
                    'application/json': [
                        {
                            'id': 1,
                            'description': 'Remember the milk',
                            'completed': False
                        }
                    ]
                }
            }
        }
    })
    def get(self, _parser):
        # The `swagger.doc` decorator returns a query parameter parser in the special
        # '_parser' function argument if it is present. If a resource function contains
        # the special argument `_parser`, any `query` type parameters in the documentation
        # will be automatically added to a `reqparse` parser and assigned to the `_parser`
        # argument.
        args = _parser.parse_args()
        completed = args['completed']

        app.logger.debug('Fetching all todo items...')

        if completed is not None:
            return [t for t in todos if t['completed'] == completed]
        else:
            return todos

    # @return_as_json_api
    @swagger.doc({
        'tags': ['todos'],
        'description': 'Adds a todo item',
        'parameters': [
            {
                'name': 'payload',
                'description': 'Request body',
                'in': 'body',
                'schema': TodoModel,
                'required': True
            }
        ],
        'responses': {
            '201': {
                'description': 'Success',
                'schema': TodoModel,
                'headers': {
                    'Location': {
                        'type': 'string',
                        'description': 'Location of the new todo item'
                    }
                },
                'examples': {
                    'application/json': [
                        {
                            'id': 1,
                            'description': 'Remember the milk',
                            'completed': False
                        }
                    ]
                }
            }
        }
    })
    def post(self):
        # Validate request body with schema model
        try:
            todo = TodoModel(**request.get_json())
        except ValueError as e:
            return ErrorModel(**{'message': e.args[0]}), 400

        todo['id'] = max([t['id'] for t in todos]) + 1

        app.logger.debug(f'Creating new todo item [{todo}]...')

        todos.append(todo)

        return todo, 201, {'Location': request.path + '/' + str(todo['id'])}


class LMSUserListResource(Resource):
    @cache.cached()
    @return_as_json_api
    def get(self):
        app.logger.debug('Fetching LMS users...')
        return LMS.users.GET().json(), 200


class LMSCourseListResource(Resource):
    @cache.cached()
    @return_as_json_api
    def get(self):
        app.logger.debug('Fetching LMS courses...')
        return LMS.courses.GET().json(), 200


api.add_resource(TodoResource, '/api/todo/<int:todo_id>')
api.add_resource(TodoListResource, '/api/todos')
api.add_resource(LMSUserListResource, '/api/lms/users')
api.add_resource(LMSCourseListResource, '/api/lms/courses')


# Redirect root to Swagger UI
@app.route('/')
@app.route('/api')
def index():
    return redirect('http://petstore.swagger.io/?url=http://localhost:8000/api/swagger.json', code=302)


if __name__ == '__main__':
    app.run(host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'])
