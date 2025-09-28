#!/usr/bin/env python3
import os
import sys
import logging
from threading import Thread
import asyncio
from flask import Flask, jsonify
from pyrogram import Client
from dotenv import load_dotenv

# Load environment variables
import os
import logging

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Then your existing logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
class Config:
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    CHANNEL_IDS = [int(x) for x in os.getenv("CHANNEL_IDS", "").split(",") if x.strip()]
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "kannada_entertainment")
    BLOGGER_API_KEY = os.getenv("BLOGGER_API_KEY", "")
    BLOGGER_BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "")
    BLOG_URL = os.getenv("BLOG_URL", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")
    PORT = int(os.getenv("PORT", 8080))

# Validate required configuration
required_config = ["API_ID", "API_HASH", "BOT_TOKEN"]
missing_config = [key for key in required_config if not getattr(Config, key)]

if missing_config:
    logger.error(f"Missing required configuration: {', '.join(missing_config)}")
    sys.exit(1)

# Initialize Pyrogram client
app = Client(
    "kannada_bot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

# Import bot handlers (this is where your Part 1-5 code will be imported)
try:
    from bot import handlers  # This will import all your bot code
    logger.info("Bot handlers imported successfully")
except ImportError as e:
    logger.error(f"Failed to import bot handlers: {e}")
    sys.exit(1)

# Flask app for health checks
flask_app = Flask(__name__)

@flask_app.route('/health')
def health_check():
    """Health check endpoint for Koyeb"""
    return jsonify({
        "status": "healthy",
        "bot": "running",
        "timestamp": str(asyncio.get_event_loop().time())
    }), 200

@flask_app.route('/status')
def status():
    """Status endpoint with more details"""
    return jsonify({
        "bot_name": "Kannada Entertainment Bot",
        "status": "operational",
        "version": "1.0.0",
        "features": [
            "content_upload",
            "user_search",
            "blog_integration",
            "analytics",
            "feedback_system"
        ]
    }), 200

def run_flask():
    """Run Flask app in a separate thread"""
    flask_app.run(host='0.0.0.0', port=Config.PORT, debug=False)

def main():
    """Main function to start both Flask and Pyrogram"""
    try:
        # Start Flask app in a separate thread
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info(f"Flask health check server started on port {Config.PORT}")
        
        # Start Pyrogram bot
        logger.info("Starting Kannada Entertainment Bot...")
        app.run()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
