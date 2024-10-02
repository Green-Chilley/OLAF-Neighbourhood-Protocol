# OLAF Neighbourhood Protocol Implementation
This project implements a secure chat application using the OLAF Neighbourhood Protocol with Flask and Socket.IO. The application supports secure public and private messaging, room creation, and user authentication through RSA key pairs.

## Features
- **RSA Key Generation**: Clients generate their own RSA key pairs for secure communication.
- **Public and Private Chat**: Supports both public broadcasting and private (whisper) messages.
- **Room Management**: Users can create, join, and leave chat rooms.
- **Persistence**: Rooms remain open even if all users leave, allowing them to rejoin later.

> **Note:** This version of the code intentionally includes vulnerabilities for educational purposes, as part of the assignment's requirements.

## Installation
Ensure you have Python and `pip` installed. Then, run the following commands to install the necessary dependencies:

```bash
pip install flask
pip install flask_socketio
pip install cryptography
pip install pycryptodome
pip install canonicaljson
pip install eventlet
```

## How to Run the Server
1. Navigate to the directory where `main.py` is located.
2. Run the server with:
    ```bash
    python main.py
    ```
3. In the terminal, CTRL + Click the link to `localhost:5000` to open the application in your browser.

## Testing
1. Open two browser windows: one in regular mode and one in incognito mode.
2. In one tab, enter a name and create a room.
3. Copy the room code to your clipboard.
4. In the other tab, enter a name and use the room code to join the room.
5. Test public chatting and private chatting (whispers), and try leaving and rejoining rooms.

> **Note**: For more than two users, use multiple browsers due to Flask's session management limitations.

## Persistence
- Rooms are designed to remain open even when all users leave. This allows users to rejoin the room later and continue their conversation.

## Project Structure
- `main.py`: The main server code implementing the chat application with vulnerabilities for educational review.
- `templates/`: Contains HTML templates (`base.html`, `home.html`, `room.html`) for rendering the UI.
- `static/css/`: Contains `style.css` for styling the chat application.

## Vulnerabilities
This code version intentionally includes two vulnerabilities to meet the assignment's requirements. These vulnerabilities are labelled in the code as "VULNERABLE CODE" for educational review.

If you want to use the code **without vulnerabilities**, please run the `main-no-vul.py` file instead of the default `main.py`.

### **Vulnerability 1: Skipping Signature Verification in Public Messages**
**Description**: In the `handle_public_message` function, the server skips the signature verification step, allowing any client to send messages without proper authentication.

**Impact**:
- **Impersonate Other Users**: An attacker can send messages on behalf of other users.
- **Send Unauthorized Messages**: Messages are sent without verifying the sender's identity.
- **Compromise Message Integrity**: Attackers can modify messages without detection.

**Code Reference**:
The skipped signature verification is commented out in the `handle_public_message` function in `main.py`.

### **Vulnerability 2: Overwriting Public Keys in 'hello' Messages**
**Description**: The `handle_hello` function allows clients to overwrite existing users' public keys. This means that an attacker can impersonate a user by sending a `hello` message with a different public key.

**Impact**:
- **Man-in-the-Middle Attack**: An attacker can intercept and alter communications.
- **Impersonate Other Users**: The attacker can send messages that appear to come from another user.
- **Eavesdropping**: Attackers can decrypt messages intended for the victim.

**Code Reference**:
The check preventing the overwriting of client entries has been removed in the `handle_hello` function in `main.py`.

## Usage Notes
- **Testing**: The vulnerabilities mentioned above should only be tested in a controlled environment for educational purposes. The code is not suitable for production use.
- **Room Code**: The room code can be copied and shared to allow other users to join a specific room.
- **Whisper**: To send a private message, select a recipient from the dropdown menu.

## Screenshots

### 1. Home Screen
The home screen allows users to pick a name and either create a new room or join an existing one using a room code.

![Home Screen](./screenshots/home.jpg)

### 2. User A Creating a Room
User A creates a room and sends a public message to everyone in the room: "Hello everyone from A!"

![User A](./screenshots/user-a.jpg)

### 3. User B Whispering to User A
User B joins the room and whispers to User A: "hi this is a test whisper from B." Only User A can see this message.

![User B](./screenshots/user-b.jpg)

### 4. User C Joining and Messaging
User C joins the room, sends a public message: "hello everyone from C," and then whispers to User B: "hello this is a test whisper from C."

![User C](./screenshots/user-c.jpg)

### Explanation
- As shown in the screenshots, **public messages** (e.g., "Hello everyone from A" and "Hello everyone from C") are visible to all users in the room.
- **Whispers** are private messages that can only be seen by the intended recipient:
  - User A does not receive User C's whisper to User B.
  - Similarly, User C does not receive User B's whisper to User A.
- This illustrates how the application maintains **message privacy** for whispers, ensuring only the sender and intended recipient can see the content of private messages.

These screenshots provide a visual overview of the chat application's UI and its handling of public messages and whispers, highlighting its capability to manage private communications securely within a room.

## License
This project is developed for educational purposes and is not intended for commercial use. 

## Contributors/Authors
Elliot Koh, Bryan Van, Leo Nguyen, Nathaniel Cordero