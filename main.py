#!/usr/bin/env python3
import os
import sys
import logging
from threading import Thread
from flask import Flask, jsonify
from pyrogram import Client
import requests
import threading
import time

def ping_server():
    """Keep Koyeb instance alive by pinging itself"""
    # Replace with your actual Koyeb app URL
    url = "https://running-aime-file-get-81528fdc.koyeb.app"
    
    while True:
        try:
            response = requests.get(url, timeout=30)
            logger.info(f"Ping successful: {response.status_code}")
        except Exception as e:
            logger.error(f"Ping failed: {e}")
        
        time.sleep(60)  # Ping every 10 minutes
def main():
    try:
        # Start keep-alive ping
        ping_thread = threading.Thread(target=ping_server, daemon=True)
        ping_thread.start()
        logger.info("Keep-alive ping started")
        
        # Start Flask in separate thread
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        # Start bot
        app.run()
    except Exception as e:
        logger.error(f"Error: {e}")

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
