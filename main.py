from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, emit, SocketIO
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
    return code  # Corrected indentation here


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
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")


@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template(
        "room.html",
        code=room,
        messages=rooms[room]["messages"],
    )


@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")
    session_id = request.sid

    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    # Add client to the clients dictionary
    clients[session_id] = {'name': name, 'public_key_pem': None, 'room': room}
    join_room(room)
    rooms[room]["members"] += 1

    # Use 'emit' with 'public_message' event
    emit("public_message", {"sender": name, "message": "has entered the room"}, to=room)
    emit_client_list_update(room)
    print(f"{name} has entered the room {room}")


@socketio.on("hello")
def handle_hello(message_payload):
    room = session.get("room")
    name = session.get("name")
    session_id = request.sid

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

    # Check the counter
    last_counter = client_counters.get(name, 0)
    if counter <= last_counter:
        print(f"Replay attack detected or invalid counter in hello from {name}.")
        return

    # Update stored counter
    client_counters[name] = counter

    # Store the client's public key
    clients[session_id]['public_key_pem'] = public_key_pem
    print(f"Stored public key for {name}.")

    # Send updated client list to all clients in the room
    emit_client_list_update(room)


@socketio.on("public_message")
def handle_public_message(data):
    room = session.get("room")
    name = session.get("name")

    if room not in rooms:
        return

    # Broadcast the public message to all clients in the room
    content = {
        "sender": name,
        "message": data.get("message")
    }
    emit("public_message", content, to=room)
    rooms[room]["messages"].append(content)
    print(f"Public message from {name}: {data.get('message')}")


@socketio.on("chat_message")
def handle_chat_message(data):
    room = session.get("room")
    name = session.get("name")
    session_id = request.sid

    if room not in rooms:
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

    # Send the message to the recipient and sender
    content = {
        "sender": name,
        "recipient": recipient_name,
        "message": data.get("message")
    }
    emit("chat_message", content, room=recipient_sid)
    emit("chat_message", content, room=session_id)
    print(f"Whisper from {name} to {recipient_name}: {data.get('message')}")


@socketio.on("disconnect")
def disconnect():
    session_id = request.sid
    client_info = clients.get(session_id)
    if client_info:
        name = client_info['name']
        room = client_info['room']
        leave_room(room)
        clients.pop(session_id, None)
        client_counters.pop(name, None)

        # Update room members
        if room in rooms:
            rooms[room]["members"] -= 1
            if rooms[room]["members"] <= 0:
                del rooms[room]

        # Use 'emit' with 'public_message' event
        emit("public_message", {"sender": name, "message": "has left the room"}, to=room)
        emit_client_list_update(room)
        print(f"{name} has left the room {room}")


def emit_client_list_update(room):
    # Send the list of clients in the room to all clients
    client_list = []
    clients_public_keys = {}
    for sid, client in clients.items():
        if client['room'] == room:
            client_list.append({'name': client['name']})
            if client['public_key_pem']:
                clients_public_keys[client['name']] = client['public_key_pem']
    socketio.emit('client_list_update', {'clients': client_list, 'clientsPublicKeys': clients_public_keys}, room=room)


if __name__ == "__main__":
    socketio.run(app, debug=True)
