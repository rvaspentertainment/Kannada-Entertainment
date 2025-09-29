# main.py

import sys
import logging
from threading import Thread
from flask import Flask, jsonify
from pyrogram import Client

# Import configuration
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Validate required configuration
if not all([Config.API_ID, Config.API_HASH, Config.BOT_TOKEN]):
    logger.error("FATAL: Missing required environment variables: API_ID, API_HASH, BOT_TOKEN")
    sys.exit(1)

# Initialize Pyrogram Client
app = Client(
    "kannada_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Import bot handlers AFTER client initialization
# This ensures the client instance is available for the decorators
from bot import handlers
logger.info("Bot handlers imported.")

# Flask app for health checks
flask_app = Flask(__name__)

@flask_app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms like Koyeb."""
    return jsonify({"status": "healthy"}), 200

def run_flask():
    """Runs the Flask web server in a separate thread."""
    flask_app.run(host='0.0.0.0', port=Config.PORT, debug=False)

def main():
    """Main function to start the bot and health check server."""
    try:
        # Start Flask in a separate thread for health checks
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info(f"Health check server running on port {Config.PORT}")

        # Start the Pyrogram bot
        logger.info("Starting Kannada Entertainment Bot...")
        app.run()
        logger.info("Bot stopped.")

    except Exception as e:
        logger.error(f"An error occurred while starting the bot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
