# -*- coding: utf-8 -*-

from flask_restful_swagger_2 import Schema


class TodoModel(Schema):
    type = 'object'
    properties = {
        'id': {
            'type': 'integer',
            'format': 'int64',
            'readOnly': True
        },
        'description': {
            'type': 'string',
            'minLength': 1,
        },
        'completed': {
            'type': 'boolean'
        }
    }
    required = ['description']


class ErrorModel(Schema):
    type = 'object'
    properties = {
        'message': {
            'type': 'string'
        }
    }
