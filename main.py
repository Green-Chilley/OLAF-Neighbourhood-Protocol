from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Required for using session
socketio = SocketIO(app)

@app.route('/', methods=['GET', 'POST'])
def home():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        room = request.form['code']  # Get the room code from the form input

        if not name or not room:
            error = "Name and room code cannot be empty."
            return render_template('home.html', error=error)

        session['name'] = name  # Store the name in session
        session['room'] = room  # Store the room in session

        return redirect(url_for('room'))
    
    return render_template('home.html', error=error)

@app.route('/room')
def room():
    name = session.get('name')  # Retrieve the name from session
    room = session.get('room')  # Retrieve the room from session

    # Debugging: print the room being requested
    print(f"Requested room: {room}")

    if name and room:
        return render_template('room.html', name=name, room=room)
    else:
        return redirect(url_for('home'))

@socketio.on('join')
def handle_join(data):
    name = data['name']
    room = data['room']
    join_room(room)
    emit('message', {'name': 'System', 'message': f'{name} has joined the room.'}, room=room)

@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    message = data['message']
    name = data['name']
    emit('message', {'name': name, 'message': message}, room=room)

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000)
