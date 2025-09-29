# bot/parts/core_bot_functionality.py

import logging
import math
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config

# --- Setup ---
logger = logging.getLogger(__name__)

# --- Database Connection ---
try:
    mongo_client = MongoClient(Config.MONGO_URL)
    db = mongo_client[Config.DATABASE_NAME]
    movies_collection = db.movies
    series_collection = db.series
    shows_collection = db.shows
    logger.info("Successfully connected to MongoDB.")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {e}")
    # The bot will likely fail to start, which is intended if the DB is down.

# --- Session Management ---
class MediaProcessor:
    """A class to hold the state of an admin's upload session."""
    def __init__(self):
        self.reset_data()

    def reset_data(self):
        """Resets all session data to default values."""
        self.entertainment_type = None
        self.names_to_process = []
        self.current_name_index = 0
        self.search_results = {}
        self.selected_media = {}
        self.details = {}
        self.unavailable_list = []
        self.current_step = None # e.g., 'waiting_for_names', 'collecting_details'
        self.current_page = 0
        self.total_pages = 0
        # For details collection
        self.current_detail_index = 0
        self.current_field_index = 0
        logger.info("MediaProcessor session data has been reset.")


# Global dictionary to store session objects for each admin user
user_sessions = {}

def get_user_session(user_id: int) -> MediaProcessor:
    """Retrieves or creates a MediaProcessor session for a given user."""
    if user_id not in user_sessions:
        user_sessions[user_id] = MediaProcessor()
    return user_sessions[user_id]

# --- Helper Functions ---
def format_file_size(size_bytes: int) -> str:
    """Formats file size into a human-readable string."""
    if size_bytes is None or size_bytes == 0:
        return "0 B"
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def get_collection_by_type(entertainment_type: str):
    """Returns the appropriate MongoDB collection based on the entertainment type."""
    collections = {
        "movies": movies_collection,
        "webseries": series_collection,
        "tvseries": series_collection,
        "shows": shows_collection
    }
    return collections.get(entertainment_type, movies_collection)

# --- Core Command Handlers ---
@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Handles the /start command."""
    try:
        # Check if it's a deep link for a media request
        if len(message.command) > 1 and message.command[1].startswith("media-"):
            from .user_features import handle_media_request # Avoid circular import
            await handle_media_request(client, message)
            return

        welcome_text = """
🎬 **Welcome to the Kannada Entertainment Bot!** 🎬

Your ultimate destination for Kannada Movies, Web Series, TV Shows, and much more.

**How to use me:**
- Use **/search** to find any content.
- Use **/latest** to see the newest additions.
- Use **/help** to see all available commands and features.

Ready to dive in? Choose an option below to get started!
        """
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Search Content", callback_data="search_content")],
            [
                InlineKeyboardButton("📺 Latest Movies", callback_data="latest_movies"),
                InlineKeyboardButton("🎭 Latest Series", callback_data="latest_series")
            ],
            [InlineKeyboardButton("🌐 Visit Our Blog", url=Config.BLOG_URL)],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help_menu")]
        ])
        await message.reply_text(welcome_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await message.reply_text("❌ An error occurred. Please try again later.")


@Client.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    """Handles the /help command."""
    try:
        help_text = """
ℹ️ **Bot Help & Features**

This bot helps you discover and download Kannada entertainment content easily.

**Available Commands:**
• `/start` - Welcome message and main menu.
• `/search` - The main way to find content. You can search by name, actor, genre, year, or for dubbed content.
• `/latest` - Quickly see the most recently added movies and series.
• `/help` - Shows this help message.

**Features:**
✅ **Smart Search:** Find exactly what you're looking for.
✅ **Multi-Quality:** Download content in various qualities (4K, 1080p, 720p, etc.).
✅ **Detailed Info:** Get posters, descriptions, cast, and more before you download.
✅ **Organized Series:** Episodes are neatly organized by season.
✅ **Blog Integration:** Visit our blog for a web-based browsing experience.

If you encounter any issues, please contact an admin.
        """
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Start Searching", callback_data="search_content")],
            [InlineKeyboardButton("🌐 Visit Our Blog", url=Config.BLOG_URL)]
        ])
        await message.reply_text(help_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        await message.reply_text("❌ An error occurred. Please try again later.")
