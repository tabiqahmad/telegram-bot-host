from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import threading
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins

REACTION = "❤️"

# Each bot stored as:
# {"token", "base_url", "offset", "username", "created", "owner_id"}
ALL_BOTS = []


############# BASIC UTILITIES #############

def send_message(token, chat_id, text):
    """Send text message to a chat."""
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
    except Exception as e:
        print("SendMessageError:", e)


def get_username(token):
    """Fetch Telegram bot username."""
    try:
        res = requests.get(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=5
        ).json()
        if res.get("ok"):
            return res["result"]["username"]
    except Exception as e:
        print("UsernameError:", e)
    return "UnknownBot"


############# BOT THREAD #############

def start_bot(bot):
    """Runs in a separate thread for each bot."""
    print("STARTED BOT:", bot["token"][:12])

    # Send startup message to OWNER (optional)
    send_message(
        bot["token"],
        bot["owner_id"],
        f"🤖 Your bot @{bot['username']} has started!\nIt will react to all messages ❤️"
    )

    while True:
        try:
            res = requests.get(
                bot["base_url"] + f"getUpdates?offset={bot['offset']}",
                timeout=5
            ).json()

            if "result" in res:
                for upd in res["result"]:
                    bot["offset"] = upd["update_id"] + 1
                    msg = upd.get("message", {})

                    # -------------------------------
                    # 1️⃣ Handle /start from ANY USER
                    # -------------------------------
                    if "text" in msg and msg["text"].strip() == "/start":
                        user_chat = msg["chat"]["id"]
                        send_message(
                            bot["token"],
                            user_chat,
                            "👋 Welcome!\nYour bot is active and reacting automatically ❤️"
                        )

                    # -------------------------------
                    # 2️⃣ If bot is added to a group
                    # -------------------------------
                    if "new_chat_members" in msg:
                        for m in msg["new_chat_members"]:
                            if m.get("username") == bot["username"]:
                                send_message(
                                    bot["token"],
                                    msg["chat"]["id"],
                                    "👋 Hello everyone!\nI am Reaction Bot.\nI will react to all your messages ❤️"
                                )

                    # -------------------------------
                    # 3️⃣ Reaction to every message
                    # -------------------------------
                    if "message_id" in msg:
                        try:
                            requests.post(
                                bot["base_url"] + "setMessageReaction",
                                json={
                                    "chat_id": msg["chat"]["id"],
                                    "message_id": msg["message_id"],
                                    "reaction": [{"type": "emoji", "emoji": REACTION}]
                                },
                                timeout=5
                            )
                        except Exception as e:
                            print("ReactionError:", e)

        except Exception as e:
            print("PollingError:", e)

        time.sleep(0.5)


############# ROUTES #############

@app.route("/")
def home():
    return "Unlimited Reaction Bot Maker Backend Running!"


@app.route("/create", methods=["POST"])
def create_bot():
    data = request.get_json()

    token = data.get("token")
    owner_id = data.get("userId")

    if not token:
        return jsonify({"status": "error", "message": "Token missing"})

    if not owner_id:
        return jsonify({"status": "error", "message": "Missing userId"})

    # Check if bot already exists
    for b in ALL_BOTS:
        if b["token"] == token:
            return jsonify({"status": "ok", "message": "Bot already active!"})

    username = get_username(token)

    bot_obj = {
        "token": token,
        "base_url": f"https://api.telegram.org/bot{token}/",
        "offset": 0,
        "username": username,
        "created": datetime.utcnow().isoformat(),
        "owner_id": owner_id
    }

    ALL_BOTS.append(bot_obj)

    # Start bot thread
    th = threading.Thread(target=start_bot, args=(bot_obj,), daemon=True)
    th.start()

    return jsonify({
        "status": "ok",
        "message": f"Bot Started Successfully!\nBot: @{username}"
    })


@app.route("/global-bots", methods=["GET"])
def global_bots():
    bots = []

    for b in ALL_BOTS:
        bots.append({
            "token": b["token"][:10] + "*****",
            "username": b["username"],
            "link": f"https://t.me/{b['username']}",
            "created": b["created"]
        })

    return jsonify({
        "status": "ok",
        "total_bots": len(ALL_BOTS),
        "bots": bots
    })


############# START APP #############

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
