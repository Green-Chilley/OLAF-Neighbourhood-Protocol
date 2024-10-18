# OLAF Neighbourhood Protocol Implementation

This project implements a secure chat application using the OLAF Neighbourhood Protocol with Flask and Socket.IO. The application supports secure public and private messaging, room creation, room connectivity, file transfer, and user authentication through RSA key pairs.

## Features

- **RSA Key Generation**: Clients generate their own RSA key pairs for secure communication.
- **Public and Private Chat**: Supports both public broadcasting and private (whisper) messages.
- **Room Management**: Users can create, join, and leave chat rooms.
- **Room Connectivity**: Rooms can be connected, allowing messages and files to be shared across connected rooms.
- **File Transfer**: Users can securely send and receive files within rooms.
- **Persistence**: Rooms remain open even if all users leave, allowing them to rejoin later.
- **User Authentication**: Users are authenticated through RSA key pairs and message signatures.

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

Alternatively, you can install all dependencies at once using:

```bash
pip install -r requirements.txt
```

*(Make sure to create a `requirements.txt` file with the listed packages if you choose this option.)*

## How to Run the Server

1. Navigate to the directory where `main.py` is located.
2. Run the server with:

    ```bash
    python main.py
    ```

3. In the terminal, CTRL + Click the link to `http://localhost:5000` to open the application in your browser.

## Usage Instructions

### Creating or Joining a Room

- **Create a Room**: Enter your name and click on the **Create a Room** button. A unique room code will be generated.
- **Join a Room**: Enter your name and the room code provided by another user, then click on the **Join a Room** button.

### Room Connectivity

- **Connect Rooms**: In the chat interface, use the **Connect Rooms** section to link two rooms.
    - Enter the codes of two rooms you want to connect.
    - Click on **Connect Rooms**.
    - Once connected, messages and files sent in one room will be propagated to the other.

### Sending Messages

- **Public Message**: Type your message in the input field, ensure **Everyone** is selected in the recipient dropdown, and click **Send**.
- **Private Message (Whisper)**:
    - Select a recipient from the dropdown menu (other than **Everyone**).
    - Type your message and click **Send**.
    - Only the selected recipient will see the message.

### File Transfer

- **Sending a File**:
    - Click on the **Choose File** button or the file input field.
    - Select the file you wish to send (maximum size: 5 MB).
    - Click on **Send File**.
    - The file will be sent to all users in the room (and connected rooms, if applicable).

- **Receiving a File**:
    - When another user sends a file, it will appear in the chat with a download link.
    - Click on the file name to download it.

### Leaving a Room

- Click on the **Home/Leave** button at the top-right corner to leave the room and return to the home page.

## Testing

1. **Single User Testing**:
    - Run the server and open `http://localhost:5000` in your browser.
    - Create a room and test sending messages and files to ensure basic functionality.

2. **Multiple Users Testing**:
    - Open multiple browser windows or use incognito/private browsing modes to simulate different users.
    - Each browser instance can log in with a different name.
    - Test public messaging, private messaging, room connectivity, and file transfer between users.

3. **Room Connectivity Testing**:
    - Create two separate rooms with different users.
    - Use the **Connect Rooms** feature to link them.
    - Verify that messages and files sent in one room appear in the other.

4. **File Transfer Testing**:
    - Send files between users.
    - Ensure that files are correctly received and can be downloaded.

> **Note**: For more than two users, use multiple browsers or devices due to Flask's session management limitations.

## Persistence

- **Rooms**: Designed to remain open even when all users leave, allowing conversations to continue later.
- **Connected Rooms**: Connections between rooms persist, so once rooms are connected, they remain connected until the server restarts.

## Project Structure

- `main.py`: The main server code implementing the chat application with vulnerabilities for educational review.
- `templates/`: Contains HTML templates for rendering the UI.
  - `base.html`: Base template with common HTML structure and imports.
  - `home.html`: Template for the home page where users create or join rooms.
  - `room.html`: Template for the chat room interface, including messaging, room connectivity, and file transfer features.
- `static/css/`: Contains `style.css` for styling the chat application (if used).
- `screenshots/`: Contains screenshots demonstrating the application (update as needed).

## Vulnerabilities

This implementation includes intentional vulnerabilities introduced as part of an educational exercise. Reviewers are encouraged to analyze the code for potential security issues. Testing should be conducted in a controlled environment.

## Usage Notes

- **Educational Purpose**: The vulnerabilities should only be tested in a controlled environment. The code is not suitable for production use.
- **Room Code**: The room code can be copied and shared to allow other users to join a specific room.
- **Private Messages**: Use the recipient dropdown to select the user you want to send a private message to.
- **Room Connectivity**: Only users with knowledge of both room codes can connect rooms.
- **File Transfer Limitations**:
  - Maximum file size is 5 MB.
  - All users in the room (and connected rooms) will receive the file.

## Screenshots

*(Update the screenshots as needed to reflect the new features.)*

### 1. Home Screen

The home screen allows users to pick a name and either create a new room or join an existing one using a room code.

![Home Screen](./screenshots/home.jpg)

### 2. Chat Room Interface

The chat room interface includes messaging, room connectivity, and file transfer features.

![Chat Room](./screenshots/chat_room.jpg)

### 3. Room Connectivity

Users can connect two rooms using their codes, allowing messages and files to be shared across them.

![Room Connectivity](./screenshots/room_connectivity.jpg)

### 4. File Transfer

Users can send and receive files within the chat room.

![File Transfer](./screenshots/file_transfer.jpg)

### Explanation

- **Public Messages**: Visible to all users in the room and connected rooms.
- **Private Messages (Whispers)**: Only visible to the sender and the selected recipient.
- **Room Connectivity**: Messages and files sent in one room are propagated to connected rooms.
- **File Transfer**: Files are shared within rooms and connected rooms, and users can download received files.

These screenshots provide a visual overview of the chat application's UI and its handling of new features, highlighting its capability to manage private communications, connect rooms, and transfer files securely.

## License

This project is developed for educational purposes and is not intended for commercial use.

## Contributors/Authors

- **Elliot Koh**
- **Bryan Van**
- **Leo Nguyen**
- **Nathaniel Cordero**

### Group Contact

- **Discord ID**: proximobinks