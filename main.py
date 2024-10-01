from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjksa"
socketio = SocketIO(app)

rooms = {}
clients_public_keys = {}  # To store public keys of connected clients
private_keys = {}  # In-memory storage for private keys (don't store in session)

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
        
    return code

# Function to generate RSA key pair for the client
def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

# Function to serialize the public key to PEM format
def serialize_public_key(public_key):
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')

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
        
        # Generate RSA key pair and store the public key in session
        private_key, public_key = generate_rsa_key_pair()
        private_keys[name] = private_key  # Store private key in memory, associated with the client name
        session["public_key_pem"] = serialize_public_key(public_key)  # Store public key PEM format in session
        
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
        public_key_pem=session.get("public_key_pem")
    )

# Handle client hello message
@socketio.on("hello")
def handle_hello(data):
    room = session.get("room")
    name = session.get("name")
    public_key_pem = data.get("data", {}).get("public_key")

    print(f"Received 'hello' event. Room: {room}, Name: {name}, Public Key: {public_key_pem}")

    if not room or room not in rooms:
        print(f"Error: Room '{room}' not found or not set.")
        return
    if not public_key_pem:
        print(f"Error: Public key is missing from the 'hello' event.")
        return

    # Store the client's public key
    clients_public_keys[name] = public_key_pem
    print(f"Stored public key for {name}: {public_key_pem}")
    send({"name": name, "message": "has shared their public key."}, to=room)

# Send a hello message with public key when client connects
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

    # Remove this block
    # if public_key_pem:
    #     print(f"Emitting 'hello' message for {name} with public key.")
    #     socketio.emit("hello", {"public_key": public_key_pem}, to=room)

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    
    # Remove the private key from in-memory storage
    if name in private_keys:
        del private_keys[name]
    
    # delete room if no one is in it
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)
