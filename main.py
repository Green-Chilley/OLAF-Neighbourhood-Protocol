from client import app
from server import socketio

# Initialize the socketio object with the app in main.py
socketio.init_app(app)

if __name__ == "__main__":
    socketio.run(app, debug=True)
