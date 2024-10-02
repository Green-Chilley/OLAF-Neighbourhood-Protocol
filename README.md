# OLAF Neighbourhood Protocol Implementation
>using Flask and Socketio

## Installations
pip install pycryptodome
pip install flack_socketio
pip install flask
pip install cryptography

## How to run server
1. Head to directory where `main.py` is located.
2. Type in `python main.py`
3. CTRL + Click the localhost to port 5000 link in terminal to open the application in your browser

## Testing
1. Open 2 tabs under the same url, one in ur browser, one in an incognito window
2. In one tab enter name and create room
3. Click on the chat room code to copy to clipboard
4. On the other tab, join the room using the room
5. You can now public chat, private chat (whisper), leave/rejoin rooms, create new rooms.

Notes: for 3 or more users u need to use multiple browsers due to how flask sessions work.
We also added persistence, so that if user count is less than or equal to 0 the room remains open so the users can join back and talk later if they would like.

## Vulnerabilities
