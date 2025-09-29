#!/usr/bin/env python3
import os
import sys
import logging
from threading import Thread
from flask import Flask, jsonify
from pyrogram import Client

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

if not all([API_ID, API_HASH, BOT_TOKEN]):
    logger.error("Missing credentials!")
    sys.exit(1)

# Create bot
app = Client("kannada_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)

# Register handlers
from bot.handlers import register_handlers
register_handlers(app)

# Flask
flask_app = Flask(__name__)

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    logger.info(f"Flask on port {PORT}")
    logger.info("Starting bot...")
    app.run()
