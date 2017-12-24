import os
from flask import Flask

app = Flask(__name__)

PORT = int(os.environ.get('PORT', 5000))  # default to 5000
HOSTNAME = os.environ.get('HOSTNAME', 'NONAME')  # default to NONAME


@app.route('/')
def hello():
    return f'Hello world from Flynn on port {PORT} from container {HOSTNAME}'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
