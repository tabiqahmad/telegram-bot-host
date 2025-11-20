import requests
from flask import Flask, request
import threading
import time
import os

# TOKEN environment variable se milega (Render me set karoge)
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"

# Change this emoji to 👍 ❤️ 😂 🔥 😍 😡 etc
REACTION = "❤️"

app = Flask(__name__)

offset = 0

def add_reaction(chat_id, message_id):
    try:
        requests.post(
            BASE_URL + "setMessageReaction",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "reaction": [{"type": "emoji", "emoji": REACTION}]
            }
        )
    except:
        pass

def poll_messages():
    global offset
    while True:
        try:
            res = requests.get(BASE_URL + f"getUpdates?offset={offset}").json()

            if "result" in res:
                for update in res["result"]:
                    offset = update["update_id"] + 1

                    if "message" in update:
                        chat_id = update["message"]["chat"]["id"]
                        message_id = update["message"]["message_id"]
                        add_reaction(chat_id, message_id)

        except Exception as e:
            print("Error:", e)

        time.sleep(1)

@app.route("/")
def home():
    return "Reaction bot is running!"

# Background me bot chalu rahega
threading.Thread(target=poll_messages).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
