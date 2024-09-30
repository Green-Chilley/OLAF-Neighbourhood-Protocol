from flask_socketio import SocketIO, join_room, leave_room, send, emit
from flask import Flask, session
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from base64 import b64encode, b64decode
import random
from string import ascii_uppercase
import json

app = Flask(__name__)
socketio = SocketIO(app)

rooms = {}

# Generate unique room code
def generate_unique_code(length=4):
    while True:
        code = ''.join(random.choices(ascii_uppercase, k=length))
        if code not in rooms:
            return code

@socketio.on('create_room')
def handle_create_room(data):
    name = data.get("name")
    room = generate_unique_code()
    rooms[room] = {"members": 0, "messages": []}
    
    session["room"] = room
    session["name"] = name
    join_room(room)
    
    rooms[room]["members"] += 1
    send(f'{name} has created and joined room {room}', to=room)
    print(f'{name} created room {room}')

@socketio.on('join_room')
def handle_join_room(data):
    room = data.get("room")
    name = data.get("name")
    
    if room not in rooms:
        emit('error', {"message": "Room does not exist"})
        return
    
    session["room"] = room
    session["name"] = name
    join_room(room)
    
    rooms[room]["members"] += 1
    send(f'{name} has joined room {room}', to=room)
    print(f'{name} joined room {room}')

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send(f'{name} has left the room', to=room)
    print(f'{name} has left room {room}')

# Other socket message handling...
if __name__ == '__main__':
    socketio.run(app)
