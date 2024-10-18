from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, emit, SocketIO
import random
from string import ascii_uppercase
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import canonicaljson
import base64

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjksa"
socketio = SocketIO(app)

# Updated rooms to include 'connected_rooms' for each room
rooms = {}

client_counters = {}  # To store the last counter value for each client

# Store clients with their session IDs, names, and public keys
clients = {}  # Key: session ID, Value: {'name': name, 'public_key_pem': None, 'room': room}


def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code


@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)

        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": [], "connected_rooms": set()}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")


@app.route("/room")
def room():
    room = session.get("room")
    name = session.get("name")
    if room is None or name is None:
        return redirect(url_for("home"))

    # Ensure the room exists in rooms
    if room not in rooms:
        rooms[room] = {"members": 0, "messages": [], "connected_rooms": set()}

    return render_template(
        "room.html",
        code=room,
        messages=rooms[room]["messages"],
    )


@socketio.on("connect")
def connect():
    session_id = request.sid
    print(f"Client connected: {session_id}")


@socketio.on("hello")
def handle_hello(message_payload):
    session_id = request.sid
    name = session.get("name")
    room = session.get("room")

    if not room or not name:
        print(f"Missing room or name in session for session_id: {session_id}")
        return

    clients[session_id] = {'name': name,
                           'public_key_pem': None, 'room': room}
    join_room(room)
    rooms[room]["members"] += 1
    print(f"Rooms after {name} joined: {rooms}")

    # Inform other clients
    content = {
        "sender": name,
        "message": "has entered the room"
    }
    emit("public_message", content, room=room)

    data = message_payload.get("data")
    counter = message_payload.get("counter")
    signature_b64 = message_payload.get("signature")

    if not data or counter is None or not signature_b64:
        print("Invalid hello message format.")
        return

    public_key_pem = data.get("public_key")
    if not public_key_pem:
        print("Public key missing in hello message.")
        return

    # Load public key
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
    except Exception as e:
        print(f"Failed to load public key from {name}: {e}")
        return

    # Prepare data for verification with canonical JSON
    data_string = canonicaljson.encode_canonical_json(data).decode('utf-8')
    data_to_verify = (data_string + str(counter)).encode('utf-8')
    signature = base64.b64decode(signature_b64)
    print(f"Data to Verify for {name}: {data_string}{counter}")

    # Verify signature
    try:
        public_key.verify(
            signature,
            data_to_verify,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
    except Exception as e:
        print(f"Hello signature verification failed for {name}: {e}")
        return

    # Check the counter using session_id
    last_counter = client_counters.get(session_id, 0)
    if counter <= last_counter:
        print(
            f"Replay attack detected or invalid counter in hello from {name}.")
        return

    # Update stored counter
    client_counters[session_id] = counter

    # Store the client's public key
    clients[session_id]['public_key_pem'] = public_key_pem
    print(f"Stored public key for {name}.")

    # Send updated client list to all clients in the room
    emit_client_list_update(room)


@socketio.on("public_message")
def handle_public_message(message_payload):
    room = session.get("room")
    name = session.get("name")
    session_id = request.sid

    if room not in rooms:
        return

    data = message_payload.get("data")
    counter = message_payload.get("counter")
    signature_b64 = message_payload.get("signature")

    if not data or counter is None or not signature_b64:
        print("Invalid message format.")
        return

    # Retrieve sender's public key
    client_info = clients.get(session_id)
    public_key_pem = client_info.get('public_key_pem') if client_info else None

    if not public_key_pem:
        print(f"No public key found for {name}")
        return

    # Check the counter
    last_counter = client_counters.get(session_id, 0)
    if counter <= last_counter:
        print(f"Replay attack detected or invalid counter from {name}.")
        return

    # Update stored counter
    client_counters[session_id] = counter

    # Broadcast the public message to all clients in connected rooms
    content = {
        "sender": name,
        "message": data.get("message")
    }
    propagate_message_to_connected_rooms(room, content)
    rooms[room]["messages"].append(content)
    print(f"Public message from {name}: {data.get('message')}")


@socketio.on("chat_message")
def handle_chat_message(message_payload):
    room = session.get("room")
    name = session.get("name")
    session_id = request.sid

    if room not in rooms:
        return

    data = message_payload.get("data")
    counter = message_payload.get("counter")
    signature_b64 = message_payload.get("signature")

    if not data or counter is None or not signature_b64:
        print("Invalid message format.")
        return

    recipient_name = data.get("recipient")
    recipient_sid = None

    # Find the recipient's session ID
    for sid, client_info in clients.items():
        if client_info['name'] == recipient_name and client_info['room'] == room:
            recipient_sid = sid
            break

    if not recipient_sid:
        print(f"Recipient {recipient_name} not found in room {room}.")
        return

    # Retrieve sender's public key
    client_info = clients.get(session_id)
    public_key_pem = client_info.get('public_key_pem') if client_info else None
    if not public_key_pem:
        print(f"No public key found for {name}")
        return

    # Load public key
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
    except Exception as e:
        print(f"Failed to load public key for {name}: {e}")
        return

    # Prepare data for verification
    data_string = canonicaljson.encode_canonical_json(data).decode('utf-8')
    data_to_verify = (data_string + str(counter)).encode('utf-8')
    signature = base64.b64decode(signature_b64)
    print(f"Data to Verify for {name}: {data_string}{counter}")

    # Verify signature
    try:
        public_key.verify(
            signature,
            data_to_verify,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
    except Exception as e:
        print(f"Signature verification failed for {name}: {e}")
        return

    # Check the counter
    last_counter = client_counters.get(session_id, 0)
    if counter <= last_counter:
        print(f"Replay attack detected or invalid counter from {name}.")
        return

    # Update stored counter using session_id
    client_counters[session_id] = counter

    # Send the message to the recipient and sender
    content = {
        "sender": name,
        "recipient": recipient_name,
        "message": data.get("message")
    }
    emit("chat_message", content, room=recipient_sid)
    emit("chat_message", content, room=session_id)
    print(f"Whisper from {name} to {recipient_name}: {data.get('message')}")


@socketio.on("file_transfer")
def handle_file_transfer(message_payload):
    room = session.get("room")
    name = session.get("name")
    session_id = request.sid

    if room not in rooms:
        return

    data = message_payload.get("data")
    counter = message_payload.get("counter")
    signature_b64 = message_payload.get("signature")

    if not data or counter is None or not signature_b64:
        print("Invalid file transfer message format.")
        return

    # Retrieve sender's public key
    client_info = clients.get(session_id)
    public_key_pem = client_info.get('public_key_pem') if client_info else None

    if not public_key_pem:
        print(f"No public key found for {name}")
        return

    # Check the counter
    last_counter = client_counters.get(session_id, 0)
    if counter <= last_counter:
        print(f"Replay attack detected or invalid counter from {name}.")
        return

    # Update stored counter
    client_counters[session_id] = counter

    # Verify signature
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )
    data_string = canonicaljson.encode_canonical_json(data).decode('utf-8')
    data_to_verify = (data_string + str(counter)).encode('utf-8')
    signature = base64.b64decode(signature_b64)

    try:
        public_key.verify(
            signature,
            data_to_verify,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
    except Exception as e:
        print(f"Signature verification failed for {name}: {e}")
        return

    # Limit file size (e.g., 5 MB)
    max_size = 5 * 1024 * 1024  # 5 MB
    file_data_b64 = data.get("file_data")
    if len(base64.b64decode(file_data_b64)) > max_size:
        print(f"File size exceeds the maximum allowed limit from {name}.")
        return

    # Broadcast the file to all clients in connected rooms
    content = {
        "sender": name,
        "file_name": data.get("file_name"),
        "file_type": data.get("file_type"),
        "file_data": file_data_b64
    }
    propagate_file_to_connected_rooms(room, content)
    print(f"File received from {name}: {data.get('file_name')}")


@socketio.on("disconnect")
def disconnect():
    session_id = request.sid
    client_info = clients.get(session_id)
    if client_info:
        name = client_info['name']
        room = client_info['room']
        leave_room(room)
        clients.pop(session_id, None)
        client_counters.pop(session_id, None)

        # Update room members
        if room in rooms:
            rooms[room]["members"] -= 1
            print(f"Rooms after {name} disconnected: {rooms}")

        print(f"{name} has left the room {room}")

        # Inform other clients
        content = {
            "sender": name,
            "message": "has left the room"
        }
        emit("public_message", content, room=room)

        # Send updated client list to all clients in the room
        emit_client_list_update(room)


def emit_client_list_update(room):
    # Send the list of clients in the room to all clients
    client_list = []
    clients_public_keys = {}
    for sid, client in clients.items():
        if client['room'] == room:
            client_list.append({'name': client['name']})
            if client['public_key_pem']:
                clients_public_keys[client['name']] = client['public_key_pem']
    socketio.emit('client_list_update', {
                  'clients': client_list, 'clientsPublicKeys': clients_public_keys}, room=room)


@socketio.on('connect_rooms')
def handle_connect_rooms(data):
    room1 = data.get('room1')
    room2 = data.get('room2')
    session_id = request.sid
    name = session.get("name")

    # Check if both rooms exist
    if room1 in rooms and room2 in rooms:
        rooms[room1]['connected_rooms'].add(room2)
        rooms[room2]['connected_rooms'].add(room1)
        print(f"{name} connected rooms {room1} and {room2}")

        # Inform users in both rooms about the new connection
        content = {
            "message": f"Rooms {room1} and {room2} are now connected."
        }
        emit("public_message", content, room=room1)
        emit("public_message", content, room=room2)
    else:
        print(
            f"Cannot connect rooms {room1} and {room2}: One or both rooms do not exist.")
        emit("error", {"message": "One or both rooms do not exist."}, room=session_id)


def propagate_message_to_connected_rooms(origin_room, content, visited_rooms=None):
    if visited_rooms is None:
        visited_rooms = set()
    if origin_room in visited_rooms:
        return
    visited_rooms.add(origin_room)
    # Emit the message to the origin room
    emit('public_message', content, room=origin_room)
    # Recursively propagate to connected rooms
    for connected_room in rooms[origin_room].get('connected_rooms', set()):
        propagate_message_to_connected_rooms(
            connected_room, content, visited_rooms)


def propagate_file_to_connected_rooms(origin_room, content, visited_rooms=None):
    if visited_rooms is None:
        visited_rooms = set()
    if origin_room in visited_rooms:
        return
    visited_rooms.add(origin_room)
    # Emit the file to the origin room
    emit('file_transfer', content, room=origin_room)
    # Recursively propagate to connected rooms
    for connected_room in rooms[origin_room].get('connected_rooms', set()):
        propagate_file_to_connected_rooms(
            connected_room, content, visited_rooms)


if __name__ == "__main__":
    socketio.run(app, debug=True)
