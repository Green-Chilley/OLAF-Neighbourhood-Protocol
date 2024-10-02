# OLAF Neighbourhood Protocol Implementation
>using Flask and Socketio
## How to run server
1. Head to directory where `main.py` is located.
2. Type in `python main.py`
3. CTRL + Click the localhost to port 5000 link in terminal to open the application in your browser

## Testing
1. Open 2 tabs under the same url, one in ur browser, one in an incognito window
2. In one tab enter name and create room
3. Click on the chat room code to copy to clipboard
4. On the other tab, join the room using the room

Notes: for 3 or more users u need to use multiple browsers due to how flask sessions work.

## Installations
pip install pycryptodome
pip install flack_socketio
pip install flask
pip install cryptography