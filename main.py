#!/usr/bin/env python3
import os
import sys
import logging
from threading import Thread
import asyncio
from flask import Flask, jsonify
from pyrogram import Client

# Configure logging FIRST
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Try to load .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded .env file")
except:
    logger.info("Running without .env file (using system environment variables)")

# Configuration - Read directly from os.environ
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = os.environ.get("ADMIN_IDS", "")
CHANNEL_IDS = os.environ.get("CHANNEL_IDS", "")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "kannada_entertainment")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
PORT = int(os.environ.get("PORT", 8080))

# Debug: Print what we got (hide sensitive data)
logger.info(f"API_ID present: {bool(API_ID)}")
logger.info(f"API_HASH present: {bool(API_HASH)}")
logger.info(f"BOT_TOKEN present: {bool(BOT_TOKEN)}")
logger.info(f"PORT: {PORT}")

# Validate required configuration
if not API_ID or not API_HASH or not BOT_TOKEN:
    logger.error("Missing required configuration: API_ID, API_HASH, BOT_TOKEN")
    logger.error("Please set environment variables in Koyeb dashboard")
    sys.exit(1)

# Initialize Pyrogram client
app = Client(
    "kannada_bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Import bot handlers
try:
    from bot import handlers
    logger.info("Bot handlers imported successfully")
except ImportError as e:
    logger.error(f"Failed to import bot handlers: {e}")
    sys.exit(1)

# Flask app for health checks
flask_app = Flask(__name__)

@flask_app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "bot": "running"}), 200

@flask_app.route('/status')
def status():
    return jsonify({
        "bot_name": "Kannada Entertainment Bot",
        "status": "operational",
        "version": "1.0.0"
    }), 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT, debug=False)

def main():
    try:
        # Start Flask in separate thread
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info(f"Flask server started on port {PORT}")
        
        # Start bot
        logger.info("Starting Kannada Entertainment Bot...")
        app.run()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
