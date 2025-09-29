# config.py

import os
from dotenv import load_dotenv

# Load environment variables from a .env file for local development
load_dotenv()

class Config:
    """
    Configuration class for the Kannada Entertainment Bot.
    Reads all settings from environment variables.
    """
    # Telegram API Configuration
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # Admin and Channel Configuration
    # Expects a comma-separated string of IDs, e.g., "12345,67890"
    ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
    CHANNEL_IDS = [int(x) for x in os.environ.get("CHANNEL_IDS", "").split(",") if x.strip()]

    # Database Configuration
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "kannada_entertainment")

    # Blogger Configuration
    BLOGGER_API_KEY = os.environ.get("BLOGGER_API_KEY", "")
    BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")
    BLOG_URL = os.environ.get("BLOG_URL", "https://kannada-movies-rvasp.blogspot.com")

    # Bot Configuration
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "").replace("@", "")

    # Server Configuration (for health checks on deployment platforms)
    PORT = int(os.environ.get("PORT", 8080))
