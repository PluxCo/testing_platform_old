import logging

from web import app, socketio

logging.basicConfig(level="DEBUG")

app.config['SECRET_KEY'] = 'secret_key'

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", allow_unsafe_werkzeug=True, port=3002)
