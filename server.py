from flask_socketio import SocketIO, join_room, leave_room, send, emit
import random
from string import ascii_uppercase
from flask import session
from cryptography.hazmat.primitives import serialization

socketio = SocketIO()

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
        
    return code

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    public_key = session.get("public_key")  # Public key sent from the client

    if not room or not name:
        print("Connection failed: room or name missing.")
        return
    if room not in rooms:
        leave_room(room)
        print(f"Room {room} does not exist, leaving room.")
        return
    
    join_room(room)
    
    # Store the public key for this user after connection
    if public_key:
        if room in rooms:
            rooms[room]["keys"][name] = public_key
            print(f"Stored public key for {name} in room {room}:\n{public_key}")
        else:
            print(f"Room {room} does not exist.")
    
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        print(f"Message failed: room {room} does not exist.")
        return
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said in room {room}: {data['data']}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
            print(f"Room {room} deleted as it now has no members.")
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

