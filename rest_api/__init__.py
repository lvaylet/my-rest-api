import os
import hammock
from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)

app = Flask(__name__)
api = Api(app)

LMS_TOKEN = os.environ['LMS_TOKEN']
LMS = hammock.Hammock('https://talend.talentlms.com/api/v1',
                      auth=(LMS_TOKEN, ''))

todos = {
    'todo1': 'Remember the milk',
    'todo2': 'Change my brakepads',
}


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
    def get(self):
        return LMS.users.GET().json()


if __name__ == '__main__':
    app.run(debug=True)
