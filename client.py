from flask import Flask, render_template, request, session, redirect, url_for
from server import rooms, generate_unique_code
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjksa"
socketio = SocketIO(app)

# RSA key generation for the client
def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    # Serialize the public key to be sent to the server
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    # Serialize the private key to store it in the session
    pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()  # No password for now
    )
    print(f"Generated RSA key pair for client:\nPublic Key: {pem_public_key.decode('utf-8')}")
    return pem_private_key.decode('utf-8'), pem_public_key.decode('utf-8')

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
            rooms[room] = {"members": 0, "messages": [], "keys": {}}
            print(f"Created new room with code: {room}")
        elif code not in rooms:
            print(f"Room {code} does not exist.")
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name

        # Generate RSA keys and send public key to server via connection
        private_key, public_key = generate_rsa_key_pair()
        session["private_key"] = private_key  # Store serialized private key in session
        session["public_key"] = public_key   # Store public key in session
        
        # No need to call socketio.connect() manually
        return redirect(url_for("room"))
    
    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    
    print(f"Entered room: {room}")
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

if __name__ == "__main__":
    socketio.run(app, debug=True)
