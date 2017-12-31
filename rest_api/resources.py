#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps

from flask import request
from flask_restful_swagger_2 import swagger, Resource

from rest_api import app, LMS
from rest_api.models import TodoModel, ErrorModel

# Initial model
# FIXME Save in database (or Redis, same as caching?)
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
    # @cache.cached()  # FIXME Figure out how to import cache without circular references
    @return_as_json_api
    def get(self):
        app.logger.debug('Fetching LMS users...')
        return LMS.users.GET().json(), 200


class LMSCourseListResource(Resource):
    # @cache.cached()  # FIXME Figure out how to import cache without circular references
    @return_as_json_api
    def get(self):
        app.logger.debug('Fetching LMS courses...')
        return LMS.courses.GET().json(), 200
