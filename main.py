from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import canonicaljson
import base64

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjksa"
socketio = SocketIO(app)

rooms = {}
clients_public_keys = {}  # To store public keys of connected clients
client_counters = {}      # To store the last counter value for each client

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
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} has entered the room {room}")

@socketio.on("hello")
def handle_hello(message_payload):
    room = session.get("room")
    name = session.get("name")

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
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
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
    clients_public_keys[name] = public_key_pem
    print(f"Stored public key for {name}.")
    send({"name": name, "message": "has shared their public key."}, to=room)

@socketio.on("message")
def handle_message(message_payload):
    room = session.get("room")
    name = session.get("name")

    if room not in rooms:
        return

    print(f"handle_message called from {name}")

    data = message_payload.get("data")
    counter = message_payload.get("counter")
    signature_b64 = message_payload.get("signature")

    if not data or counter is None or not signature_b64:
        print("Invalid message format.")
        return

    # Retrieve sender's public key
    public_key_pem = clients_public_keys.get(name)
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
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
    except Exception as e:
        print(f"Signature verification failed for {name}: {e}")
        return

    # Check the counter
    last_counter = client_counters.get(name, 0)
    if counter <= last_counter:
        print(f"Replay attack detected or invalid counter from {name}.")
        return

    # Update stored counter
    client_counters[name] = counter

    # Process the message
    content = {
        "name": name,
        "message": data.get("message")
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{name} said: {data.get('message')}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    
    # Remove client data
    clients_public_keys.pop(name, None)
    client_counters.pop(name, None)
    
    # Update room members
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)
