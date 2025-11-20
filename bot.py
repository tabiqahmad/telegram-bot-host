from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import threading
import time
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

# RANDOM REACTIONS LIST
REACTIONS = ["❤️", "🥰", "😍", "😘", "🔥"]

ALL_BOTS = []


############# UTILITIES #############

def send_message(token, chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
    except:
        pass


def get_username(token):
    try:
        res = requests.get(
            f"https://api.telegram.org/bot{token}/getMe", timeout=5
        ).json()
        if res.get("ok"):
            return res["result"]["username"]
    except:
        pass
    return "UnknownBot"


############# BOT LOGIC #############

def start_bot(bot):
    print("STARTED BOT:", bot["token"][:12])

    # Owner notification with detailed message
    send_message(
        bot["token"],
        bot["owner_id"],
        f"""
🤖 Your bot @{bot['username']} is now LIVE!

✨ Features:
• Auto-reaction on every message
• Random reactions: ❤️ 🥰 😍 😘 🔥
• Works in Groups, Supergroups, Channels
• Reacts to edited messages too
• Sends welcome message when added to a group
• 24/7 Online – No downtime

Enjoy your premium reaction bot ✨🔥
"""
    )

    while True:
        try:
            res = requests.get(
                bot["base_url"] + f"getUpdates?offset={bot['offset']}",
                timeout=10
            ).json()

            if "result" in res:
                for upd in res["result"]:
                    bot["offset"] = upd["update_id"] + 1

                    # Handle ALL message types (Group, Channel, Edited)
                    msg = {}
                    if "message" in upd:
                        msg = upd["message"]
                    elif "channel_post" in upd:
                        msg = upd["channel_post"]
                    elif "edited_message" in upd:
                        msg = upd["edited_message"]
                    elif "edited_channel_post" in upd:
                        msg = upd["edited_channel_post"]
                    else:
                        continue

                    # 1️⃣ User pressed /start
                    if "text" in msg and msg["text"].strip() == "/start":
                        send_message(
                            bot["token"],
                            msg["chat"]["id"],
                            "👋 Hello! I am your Reaction Bot.\nI react randomly with ❤️🥰😍😘🔥"
                        )

                    # 2️⃣ Bot added to group
                    if "new_chat_members" in msg:
                        for m in msg["new_chat_members"]:
                            if m.get("username") == bot["username"]:
                                send_message(
                                    bot["token"],
                                    msg["chat"]["id"],
                                    "👋 Hello everyone! I will react randomly with ❤️🥰😍😘🔥"
                                )

                    # 3️⃣ RANDOM REACTION for all messages
                    if "message_id" in msg:
                        try:
                            random_emoji = random.choice(REACTIONS)
                            requests.post(
                                bot["base_url"] + "setMessageReaction",
                                json={
                                    "chat_id": msg["chat"]["id"],
                                    "message_id": msg["message_id"],
                                    "reaction": [
                                        {"type": "emoji", "emoji": random_emoji}
                                    ]
                                },
                                timeout=5
                            )
                        except:
                            pass

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

    # Prevent duplicate bot threads
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

    threading.Thread(target=start_bot, args=(bot_obj,), daemon=True).start()

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
    return jsonify({"status": "ok", "total_bots": len(ALL_BOTS), "bots": bots})


############# START SERVER #############

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
