import requests
from flask import Flask, request, jsonify
import threading
import time
import os

app = Flask(__name__)

# Global token (initially from environment)
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"
REACTION = "❤️"
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
    global offset, BASE_URL
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

@app.route("/create", methods=["POST"])
def create_bot():
    global TOKEN, BASE_URL, offset

    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"status": "error", "message": "Token missing"})

    TOKEN = token
    BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"
    offset = 0  # reset updates pointer

    return jsonify({"status": "ok", "message": "Reaction bot activated with new token!"})

# Start reaction bot thread
threading.Thread(target=poll_messages).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
