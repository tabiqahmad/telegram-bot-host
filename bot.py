import requests
from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

REACTION = "❤️"

# Each bot = {"token": "...", "base_url": "...", "offset": 0}
ALL_BOTS = []


def start_bot(bot):
    """Start polling this bot forever"""
    print("Starting bot:", bot["token"][:15], "...")
    while True:
        try:
            url = bot["base_url"] + f"getUpdates?offset={bot['offset']}"
            res = requests.get(url, timeout=5).json()

            if "result" in res:
                for upd in res["result"]:
                    bot["offset"] = upd["update_id"] + 1

                    if "message" in upd:
                        chat_id = upd["message"]["chat"]["id"]
                        msg_id = upd["message"]["message_id"]

                        # send reaction
                        try:
                            requests.post(
                                bot["base_url"] + "setMessageReaction",
                                json={
                                    "chat_id": chat_id,
                                    "message_id": msg_id,
                                    "reaction": [
                                        {"type": "emoji", "emoji": REACTION}
                                    ]
                                },
                                timeout=5
                            )
                        except:
                            pass

        except Exception as e:
            print("Error:", e)

        time.sleep(0.5)


@app.route("/")
def home():
    return "Unlimited Bot Maker running!"


@app.route("/create", methods=["POST"])
def create():
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"status": "error", "message": "Token missing"})

    base_url = f"https://api.telegram.org/bot{token}/"

    # Check: bot already exists?
    for b in ALL_BOTS:
        if b["token"] == token:
            return jsonify({
                "status": "ok",
                "message": "Bot already active."
            })

    # Create bot object
    bot_obj = {
        "token": token,
        "base_url": base_url,
        "offset": 0
    }
    ALL_BOTS.append(bot_obj)

    # Start new thread for this bot
    t = threading.Thread(target=start_bot, args=(bot_obj,), daemon=True)
    t.start()

    return jsonify({
        "status": "ok",
        "message": "New reaction bot started!"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
