import requests
from flask import Flask, request, jsonify
import threading
import time
from datetime import datetime

app = Flask(__name__)

REACTION = "❤️"

# Each bot = {"token", "base_url", "offset", "username", "created"}
ALL_BOTS = []


def send_message(token, chat_id, text):
    """Send normal text message"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
    except:
        pass


def get_username(token):
    """Fetch bot username from Telegram API"""
    try:
        res = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5).json()
        if res.get("ok"):
            return res["result"]["username"]
    except:
        pass
    return "UnknownBot"


def start_bot(bot):
    """Start polling this bot forever"""
    print("Starting bot:", bot["token"][:12], "...")

    # Send startup message to owner
    send_message(bot["token"], bot["owner_id"],
                 f"🤖 Bot Started Successfully!\n@{bot['username']} is now reacting automatically ❤️")

    while True:
        try:
            res = requests.get(
                bot["base_url"] + f"getUpdates?offset={bot['offset']}",
                timeout=5
            ).json()

            if "result" in res:
                for upd in res["result"]:
                    bot["offset"] = upd["update_id"] + 1

                    # Welcome message when bot is added to a group
                    if "message" in upd:
                        msg = upd["message"]

                        # Detect new chat members (bot added)
                        if "new_chat_members" in msg:
                            for member in msg["new_chat_members"]:
                                if member.get("username") == bot["username"]:
                                    send_message(
                                        bot["token"], msg["chat"]["id"],
                                        "👋 Hello everyone!\n\nI'm a Reaction Bot.\nI will react to every message ❤️\n\nThanks for adding me!"
                                    )

                        # Normal reaction logic
                        if "text" in msg:
                            chat_id = msg["chat"]["id"]
                            msg_id = msg["message_id"]

                            try:
                                requests.post(
                                    bot["base_url"] + "setMessageReaction",
                                    json={
                                        "chat_id": chat_id,
                                        "message_id": msg_id,
                                        "reaction": [{"type": "emoji", "emoji": REACTION}]
                                    },
                                    timeout=5
                                )
                            except:
                                pass

        except Exception as e:
            print("Polling error:", e)

        time.sleep(0.5)


@app.route("/create", methods=["POST"])
def create_bot():
    data = request.get_json()
    token = data.get("token")
    owner_id = data.get("userId")  # <-- IMPORTANT: Pass user ID from website

    if not token:
        return jsonify({"status": "error", "message": "Token missing"})

    if not owner_id:
        return jsonify({"status": "error", "message": "Missing userId"})

    base_url = f"https://api.telegram.org/bot{token}/"

    # check if exists
    for b in ALL_BOTS:
        if b["token"] == token:
            return jsonify({
                "status": "ok",
                "message": "Bot already active."
            })

    username = get_username(token)

    bot_obj = {
        "token": token,
        "base_url": base_url,
        "offset": 0,
        "username": username,
        "created": datetime.utcnow().isoformat(),
        "owner_id": owner_id
    }

    ALL_BOTS.append(bot_obj)

    t = threading.Thread(target=start_bot, args=(bot_obj,), daemon=True)
    t.start()

    return jsonify({
        "status": "ok",
        "message": f"New bot started successfully!\nBot: @{username}"
    })


@app.route("/global-bots", methods=["GET"])
def global_bots():
    result = []

    for b in ALL_BOTS:
        masked_token = b["token"][:10] + "*****"

        result.append({
            "token": masked_token,
            "username": b["username"],
            "link": f"https://t.me/{b['username']}",
            "created": b["created"]
        })

    return jsonify({
        "status": "ok",
        "total_bots": len(ALL_BOTS),
        "bots": result
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
