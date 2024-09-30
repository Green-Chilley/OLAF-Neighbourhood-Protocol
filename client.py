from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from base64 import b64encode, b64decode
import json

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjksa"
socketio = SocketIO(app)

# Key pair generation
def generate_key_pair():
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key

private_key, public_key = generate_key_pair()
counter = 0

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
        
        # Join an existing room
        if join and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        # Create a new room
        if create:
            room = None  # Let the server generate the room code
            session["create"] = True
        else:
            session["create"] = False
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    
    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None:
        return redirect(url_for("home"))
    
    return render_template("room.html", code=room)

# Sign and send message
def sign_message(message, private_key):
    global counter
    counter += 1
    message_str = json.dumps(message) + str(counter)
    message_hash = SHA256.new(message_str.encode())
    signer = pkcs1_15.new(RSA.import_key(private_key))
    signature = b64encode(signer.sign(message_hash)).decode('utf-8')
    
    return {
        "type": "signed_data",
        "data": message,
        "counter": counter,
        "signature": signature
    }

@socketio.on('connect')
def on_connect():
    if session.get("create"):
        emit('create_room', {"name": session.get("name")})
    else:
        emit('join_room', {"name": session.get("name"), "room": session.get("room")})

    # Send hello message with public key
    hello_message = {
        "data": {
            "type": "hello",
            "public_key": b64encode(public_key).decode('utf-8')
        }
    }
    emit('message', json.dumps(hello_message))

@socketio.on("chat")
def on_chat_message(data):
    message_content = {
        "type": "chat",
        "message": data["message"]
    }
    signed_message = sign_message(message_content, private_key)
    emit('message', json.dumps(signed_message))

if __name__ == '__main__':
    socketio.run(app)
