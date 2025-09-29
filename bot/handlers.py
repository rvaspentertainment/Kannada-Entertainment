# bot/handlers.py - Fixed Complete Handler System

import os
import logging
import asyncio
from typing import Dict, List, Optional, Union
from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardButton, 
    InlineKeyboardMarkup, InputMediaPhoto, InputMediaDocument
)
from pymongo import MongoClient
from datetime import datetime
import re
import json
import uuid
from urllib.parse import quote, unquote

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import configuration from environment variables
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
CHANNEL_IDS = [int(x) for x in os.environ.get("CHANNEL_IDS", "").split(",") if x.strip()]
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "kannada_entertainment")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

# Initialize clients
app = Client("kannada_entertainment_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DATABASE_NAME]

# Collections
movies_collection = db.movies
series_collection = db.series
shows_collection = db.shows

# Global dictionaries to store temporary data
user_sessions = {}
user_search_data = {}
user_feedback_state = {}

class MediaProcessor:
    def __init__(self):
        self.reset_data()
    
    def reset_data(self):
        self.selected_media = {}
        self.search_results = {}
        self.current_page = 0
        self.total_pages = 0
        self.entertainment_type = None
        self.names_to_process = []
        self.current_name_index = 0
        self.current_detail_index = 0
        self.current_field_index = 0
        self.details = {}
        self.unavailable_list = []
        self.current_step = None

def get_user_session(user_id: int) -> MediaProcessor:
    if user_id not in user_sessions:
        user_sessions[user_id] = MediaProcessor()
    return user_sessions[user_id]

# =============================================================================
# START COMMAND - Entry Point
# =============================================================================
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    try:
        # Check if it's a media request
        if len(message.command) > 1 and message.command[1].startswith("media-"):
            await handle_media_request(client, message)
            return
        
        welcome_text = """
🎬 **Welcome to Kannada Entertainment Bot** 🎬

This bot helps you find and access Kannada movies, web series, TV shows, and more!

**Available Commands:**
• /up - Upload and manage entertainment content (Admin only)
• /search - Search for movies/series
• /latest - Get latest additions
• /help - Get help
• /feedback - Send feedback

**Features:**
✅ Movies & Web Series
✅ TV Shows & Entertainment
✅ Multi-quality downloads
✅ Kannada & Dubbed content
✅ Smart search system

Choose an option below to get started:
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Search Content", callback_data="search_content")],
            [InlineKeyboardButton("📺 Latest Movies", callback_data="latest_movies"),
             InlineKeyboardButton("🎭 Latest Series", callback_data="latest_series")],
            [InlineKeyboardButton("📱 Visit Blog", url="https://kannada-movies-rvasp.blogspot.com")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help_menu")]
        ])
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")

# =============================================================================
# ADMIN COMMANDS
# =============================================================================
@app.on_message(filters.command("up") & filters.user(ADMIN_IDS))
async def upload_command(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        session = get_user_session(user_id)
        session.reset_data()
        
        welcome_text = """
📤 **Upload Entertainment Content**

Select the type of content you want to upload:
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Movies", callback_data="up_movies")],
            [InlineKeyboardButton("📺 Web Series", callback_data="up_webseries")],
            [InlineKeyboardButton("📻 TV Series", callback_data="up_tvseries")],
            [InlineKeyboardButton("🎭 Shows", callback_data="up_shows")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")]
        ])
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in upload command: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")

@app.on_message(filters.command("stats") & filters.user(ADMIN_IDS))
async def stats_command(client: Client, message: Message):
    try:
        movies_count = movies_collection.count_documents({})
        series_count = series_collection.count_documents({})
        shows_count = shows_collection.count_documents({})
        
        stats_text = f"📊 **Bot Statistics**\n\n"
        stats_text += f"🎬 **Movies:** {movies_count}\n"
        stats_text += f"📺 **Series:** {series_count}\n"
        stats_text += f"🎭 **Shows:** {shows_count}\n"
        stats_text += f"📁 **Total Content:** {movies_count + series_count + shows_count}\n\n"
        stats_text += f"🤖 **Bot:** @{BOT_USERNAME}"
        
        await message.reply_text(stats_text)
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.reply_text("❌ Error getting statistics.")

# =============================================================================
# USER COMMANDS
# =============================================================================
@app.on_message(filters.command("search"))
async def search_command(client: Client, message: Message):
    try:
        welcome_text = """
🔍 **Search Kannada Entertainment**

What would you like to search for?
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Movies", callback_data="search_movies"),
             InlineKeyboardButton("📺 Web Series", callback_data="search_webseries")],
            [InlineKeyboardButton("📻 TV Series", callback_data="search_tvseries"),
             InlineKeyboardButton("🎭 Shows", callback_data="search_shows")],
            [InlineKeyboardButton("🎭 By Actor", callback_data="search_actors"),
             InlineKeyboardButton("🎨 By Genre", callback_data="search_genres")],
            [InlineKeyboardButton("📅 By Year", callback_data="search_years"),
             InlineKeyboardButton("🗣️ Dubbed Movies", callback_data="search_dubbed")],
            [InlineKeyboardButton("🔤 By Name", callback_data="search_name")]
        ])
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in search command: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")

@app.on_message(filters.command("latest"))
async def latest_command(client: Client, message: Message):
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Latest Movies", callback_data="latest_movies"),
             InlineKeyboardButton("📺 Latest Series", callback_data="latest_series")],
            [InlineKeyboardButton("🎭 Latest Shows", callback_data="latest_shows"),
             InlineKeyboardButton("🔥 All Latest", callback_data="latest_all")]
        ])
        
        await message.reply_text(
            "📺 **Latest Additions**\n\nSelect category to see the latest content:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in latest command: {e}")

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    try:
        help_text = """
ℹ️ **Kannada Entertainment Bot Help**

**🔍 Search Commands:**
• /search - Search movies, series, shows
• /latest - View latest additions
• /feedback - Send feedback to admins

**📱 How to Use:**
1️⃣ Use /search to find content
2️⃣ Browse by categories (Movies, Series, etc.)
3️⃣ Select content to view details
4️⃣ Choose quality and download

**🎯 Search Options:**
• **By Name** - Search directly by movie/series name
• **By Actor** - Find content featuring specific actors
• **By Genre** - Browse by genres (Action, Drama, etc.)
• **By Year** - Find content from specific years
• **Dubbed Content** - Find Kannada dubbed movies

**📺 Content Types:**
• 🎬 Movies
• 📺 Web Series  
• 📻 TV Series
• 🎭 Shows

**❓ Need Help?**
Contact admin using /feedback command!
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Start Searching", callback_data="search_content")],
            [InlineKeyboardButton("📺 Latest Content", callback_data="latest_all")]
        ])
        
        await message.reply_text(help_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")

@app.on_message(filters.command("feedback"))
async def feedback_command(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            feedback_text = """📝 **Send Your Feedback**

We value your opinion! Help us improve by sending feedback.

**Usage:** `/feedback Your message here`

**Examples:**
• `/feedback The bot is awesome! Love the quality options.`
• `/feedback Please add more South Indian movies.`

**Or use these quick options:**"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Rate Bot", callback_data="rate_bot")],
                [InlineKeyboardButton("🐛 Report Bug", callback_data="report_bug")],
                [InlineKeyboardButton("💡 Suggest Feature", callback_data="suggest_feature")],
                [InlineKeyboardButton("❤️ Compliment", callback_data="send_compliment")]
            ])
            
            await message.reply_text(feedback_text, reply_markup=keyboard)
            return
        
        # Process feedback
        feedback_text = " ".join(message.command[1:])
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        
        # Save to database
        feedback_data = {
            "user_id": user_id,
            "username": username,
            "feedback": feedback_text,
            "type": "general",
            "timestamp": datetime.utcnow(),
            "status": "new"
        }
        
        db.feedback.insert_one(feedback_data)
        
        # Send to admins
        admin_message = f"""📝 **New Feedback**

👤 **User:** @{username} ({user_id})
💬 **Message:** {feedback_text}
📅 **Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        for admin_id in ADMIN_IDS:
            try:
                await client.send_message(admin_id, admin_message)
            except:
                pass
        
        await message.reply_text(
            "✅ **Thank you for your feedback!**\n\n"
            "Your message has been sent to our team."
        )
        
    except Exception as e:
        logger.error(f"Error in feedback command: {e}")

# =============================================================================
# CALLBACK QUERY HANDLERS - Main Router
# =============================================================================
@app.on_callback_query()
async def handle_callbacks(client: Client, callback_query: CallbackQuery):
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # Admin only callbacks
        admin_callbacks = ["up_", "cancel_upload", "quality_", "prev_page_", "next_page_", 
                          "correct_", "wrong_", "remove_", "done_remove_", "prev_remove_", "next_remove_"]
        
        if any(data.startswith(prefix) for prefix in admin_callbacks) and user_id not in ADMIN_IDS:
            await callback_query.answer("❌ You're not authorized.")
            return
        
        # Route callbacks to appropriate handlers
        if data.startswith("up_"):
            await handle_upload_type(client, callback_query)
        elif data == "cancel_upload":
            await handle_cancel_upload(client, callback_query)
        elif data.startswith("search_"):
            await handle_search_type(client, callback_query)
        elif data.startswith("latest_"):
            await handle_latest_content(client, callback_query)
        elif data.startswith("view_content_"):
            await handle_content_view(client, callback_query)
        elif data.startswith("season_"):
            await handle_season_selection(client, callback_query)
        elif data.startswith("episode_"):
            await handle_episode_selection(client, callback_query)
        elif data.startswith("rate_"):
            await handle_rating(client, callback_query)
        elif data.startswith("rating_"):
            await handle_rating_submission(client, callback_query)
        elif data.startswith("share_"):
            await handle_share(client, callback_query)
        elif data.startswith("filter_"):
            await handle_filter_selection(client, callback_query)
        elif data.startswith("nav_"):
            await handle_navigation(client, callback_query)
        elif data.startswith("back_"):
            await handle_back_navigation(client, callback_query)
        elif data.startswith("prev_page_") or data.startswith("next_page_"):
            await handle_pagination(client, callback_query)
        elif data.startswith("correct_") or data.startswith("wrong_"):
            await handle_correct_wrong(client, callback_query)
        elif data.startswith("remove_"):
            await handle_file_removal(client, callback_query)
        elif data in ["rate_bot", "report_bug", "suggest_feature", "send_compliment"]:
            await handle_quick_feedback(client, callback_query)
        elif data.startswith("rating_") and len(data.split("_")) == 2:
            await handle_bot_rating(client, callback_query)
        elif data == "help_menu":
            await help_command(client, callback_query.message)
        elif data == "search_content":
            await search_command(client, callback_query.message)
        else:
            await callback_query.answer("Unknown action")
            
    except Exception as e:
        logger.error(f"Error handling callback {callback_query.data}: {e}")
        await callback_query.answer("❌ An error occurred.")

# =============================================================================
# UPLOAD SYSTEM HANDLERS
# =============================================================================
async def handle_upload_type(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        session = get_user_session(user_id)
        entertainment_type = callback_query.data.replace("up_", "")
        session.entertainment_type = entertainment_type
        
        type_names = {
            "movies": "Movies 🎬",
            "webseries": "Web Series 📺",
            "tvseries": "TV Series 📻",
            "shows": "Shows 🎭"
        }
        
        await callback_query.edit_message_text(
            f"✅ Selected: **{type_names.get(entertainment_type, entertainment_type)}**\n\n"
            f"📝 **Send the name(s) of the {entertainment_type} you want to upload.**\n\n"
            f"**Format:**\n"
            f"• Single name: `KGF`\n"
            f"• Multiple names: `KGF, Kantara, RRR`\n\n"
            f"**Note:** Use commas to separate multiple names.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")]
            ])
        )
        
        session.current_step = "waiting_for_names"
        
    except Exception as e:
        logger.error(f"Error handling upload type: {e}")

async def handle_cancel_upload(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        session = get_user_session(user_id)
        session.reset_data()
        await callback_query.edit_message_text("❌ Upload process cancelled.")
    except Exception as e:
        logger.error(f"Error canceling upload: {e}")

async def handle_pagination(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        session = get_user_session(user_id)
        data = callback_query.data
        
        if data.startswith("prev_page_"):
            session.current_page = max(0, session.current_page - 1)
            name = data.replace("prev_page_", "")
        elif data.startswith("next_page_"):
            session.current_page = min(session.total_pages - 1, session.current_page + 1)
            name = data.replace("next_page_", "")
        
        await show_search_results(client, callback_query.message, user_id, name)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error handling pagination: {e}")

async def handle_correct_wrong(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        session = get_user_session(user_id)
        
        if callback_query.data.startswith("correct_"):
            name = callback_query.data.replace("correct_", "")
            session.current_name_index += 1
            await callback_query.answer("✅ Marked as correct!")
            await process_next_name(client, callback_query.message, user_id)
        elif callback_query.data.startswith("wrong_"):
            name = callback_query.data.replace("wrong_", "")
            await show_removal_options(client, callback_query.message, user_id, name)
            await callback_query.answer()
            
    except Exception as e:
        logger.error(f"Error handling correct/wrong: {e}")

async def handle_file_removal(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        session = get_user_session(user_id)
        
        parts = callback_query.data.split("_", 2)
        item_name = parts[1]
        file_index = int(parts[2])
        
        removal_key = f"{item_name}_{file_index}"
        if removal_key in session.selected_media:
            del session.selected_media[removal_key]
            await callback_query.answer(f"✅ Removed file #{file_index + 1}")
        else:
            session.selected_media[removal_key] = {"removed": True}
            await callback_query.answer(f"❌ Marked file #{file_index + 1} for removal")
        
    except Exception as e:
        logger.error(f"Error handling file removal: {e}")

# =============================================================================
# SEARCH SYSTEM HANDLERS
# =============================================================================
async def handle_search_type(client: Client, callback_query: CallbackQuery):
    try:
        search_type = callback_query.data.replace("search_", "")
        user_id = callback_query.from_user.id
        
        user_search_data[user_id] = {"search_type": search_type, "page": 0}
        
        if search_type == "name":
            await callback_query.edit_message_text(
                "🔤 **Search by Name**\n\n"
                "📝 Send me the name of the movie, series, or show you're looking for.\n\n"
                "**Examples:**\n"
                "• KGF\n"
                "• Kantara\n"
                "• Scam 1992",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Search", callback_data="back_to_search")]
                ])
            )
        else:
            await show_search_results_by_type(client, callback_query, search_type)
            
    except Exception as e:
        logger.error(f"Error handling search type: {e}")

async def handle_latest_content(client: Client, callback_query: CallbackQuery):
    try:
        content_type = callback_query.data.replace("latest_", "")
        
        if content_type == "all":
            latest_content = await get_latest_all_content()
            title = "🔥 **Latest Additions**"
        else:
            latest_content = await get_latest_by_type(content_type)
            type_titles = {
                "movies": "🎬 **Latest Movies**",
                "series": "📺 **Latest Series**",
                "shows": "🎭 **Latest Shows**"
            }
            title = type_titles.get(content_type, f"**Latest {content_type.title()}**")
        
        if not latest_content:
            await callback_query.answer("❌ No latest content found")
            return
            
        await display_latest_content(client, callback_query, latest_content, title)
        
    except Exception as e:
        logger.error(f"Error handling latest content: {e}")

async def handle_content_view(client: Client, callback_query: CallbackQuery):
    try:
        content_id = callback_query.data.replace("view_content_", "")
        
        # Find content in all collections
        content = None
        content_type = None
        
        for collection_name, collection in [
            ("movies", movies_collection), 
            ("series", series_collection), 
            ("shows", shows_collection)
        ]:
            try:
                from bson import ObjectId
                content = collection.find_one({"_id": ObjectId(content_id)})
                if content:
                    content_type = collection_name
                    break
            except:
                continue
        
        if not content:
            await callback_query.answer("❌ Content not found")
            return
        
        # Update view count
        collection.update_one(
            {"_id": content["_id"]}, 
            {"$inc": {"view_count": 1}}
        )
        
        await show_content_details(client, callback_query, content, content_type)
        
    except Exception as e:
        logger.error(f"Error handling content view: {e}")

# =============================================================================
# FEEDBACK SYSTEM HANDLERS
# =============================================================================
async def handle_quick_feedback(client: Client, callback_query: CallbackQuery):
    try:
        action = callback_query.data
        user_id = callback_query.from_user.id
        
        feedback_prompts = {
            "rate_bot": "⭐ **Rate Our Bot**\n\nHow would you rate your experience?",
            "report_bug": "🐛 **Report a Bug**\n\nPlease describe the bug:",
            "suggest_feature": "💡 **Suggest a Feature**\n\nWhat feature would you like?",
            "send_compliment": "❤️ **Send Compliment**\n\nWhat do you like about our service?"
        }
        
        if action == "rate_bot":
            buttons = []
            for i in range(1, 6):
                stars = "⭐" * i
                buttons.append([InlineKeyboardButton(f"{stars} {i}/5", callback_data=f"rating_{i}")])
            
            keyboard = InlineKeyboardMarkup(buttons)
            await callback_query.edit_message_text(
                feedback_prompts[action],
                reply_markup=keyboard
            )
        else:
            user_feedback_state[user_id] = action
            await callback_query.edit_message_text(
                f"{feedback_prompts[action]}\n\n"
                "💬 **Please send your message in the chat.**"
            )
        
    except Exception as e:
        logger.error(f"Error handling quick feedback: {e}")

async def handle_bot_rating(client: Client, callback_query: CallbackQuery):
    try:
        rating = int(callback_query.data.split("_")[1])
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username or "Unknown"
        
        # Save rating
        feedback_data = {
            "user_id": user_id,
            "username": username,
            "feedback": f"Bot rating: {rating}/5 stars",
            "type": "rating",
            "rating": rating,
            "timestamp": datetime.utcnow()
        }
        
        db.feedback.insert_one(feedback_data)
        
        stars = "⭐" * rating
        await callback_query.edit_message_text(
            f"✅ **Thank you for rating us!**\n\n"
            f"Your rating: {stars} ({rating}/5)\n\n"
            f"We appreciate your feedback!"
        )
        
    except Exception as e:
        logger.error(f"Error handling bot rating: {e}")

# =============================================================================
# MESSAGE HANDLERS
# =============================================================================
@app.on_message(filters.text & filters.user(ADMIN_IDS) & ~filters.command())
async def handle_admin_text_input(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        session = get_user_session(user_id)
        
        if hasattr(session, 'current_step'):
            if session.current_step == "waiting_for_names":
                await handle_name_input(client, message)
            elif session.current_step == "collecting_details":
                await handle_detail_input(client, message)
                
    except Exception as e:
        logger.error(f"Error handling admin text input: {e}")

@app.on_message(filters.text & filters.private & ~filters.command() & ~filters.user(ADMIN_IDS))
async def handle_user_text_input(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        
        # Check for feedback input
        if user_id in user_feedback_state:
            await handle_feedback_input(client, message)
            return
        
        # Check for name search
        user_data = user_search_data.get(user_id, {})
        if user_data.get("search_type") == "name":
            await handle_name_search(client, message)
            return
            
    except Exception as e:
        logger.error(f"Error handling user text input: {e}")

# =============================================================================
# HELPER FUNCTIONS (Simplified versions for now)
# =============================================================================
async def handle_media_request(client: Client, message: Message):
    try:
        media_id = message.command[1].replace("media-", "")
        
        # Find media in database
        media_data = None
        for collection in [movies_collection, series_collection, shows_collection]:
            media_data = collection.find_one({"media_files.msg_id": media_id})
            if media_data:
                break
        
        if not media_data:
            await message.reply_text("❌ Media not found or expired.")
            return
        
        # Find specific file and forward it
        target_file = None
        for file_info in media_data.get("media_files", []):
            if file_info.get("msg_id") == media_id:
                target_file = file_info
                break
        
        if not target_file:
            await message.reply_text("❌ File not found.")
            return
        
        # Forward the media
        channel_id = target_file.get("channel_id")
        msg_id = int(target_file.get("original_msg_id"))
        
        await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=channel_id,
            message_id=msg_id
        )
        
    except Exception as e:
        logger.error(f"Error handling media request: {e}")
        await message.reply_text("❌ Failed to send media.")

async def handle_name_input(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        session = get_user_session(user_id)
        
        names_input = message.text.strip()
        names = [name.strip() for name in names_input.split(",") if name.strip()]
        
        if not names:
            await message.reply_text("❌ Please provide valid names.")
            return
        
        session.names_to_process = names
        session.current_name_index = 0
        
        await message.reply_text(
            f"✅ **Names received:** {len(names)}\n"
            f"📝 Names: {', '.join(names)}\n\n"
            f"🔍 **Starting search process...**"
        )
        
        # Start processing (simplified for now)
        await message.reply_text("🔄 Processing... (This is a simplified version)")
        
    except Exception as e:
        logger.error(f"Error handling name input: {e}")
        await message.reply_text("❌ An error occurred while processing names.")

async def handle_detail_input(client: Client, message: Message):
    try:
        # Simplified detail handling
        await message.reply_text("Detail received. Processing...")
    except Exception as e:
        logger.error(f"Error handling detail input: {e}")

async def handle_feedback_input(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        feedback_type = user_feedback_state[user_id]
        feedback_text = message.text.strip()
        username = message.from_user.username or "Unknown"
        
        # Save feedback
        feedback_data = {
            "user_id": user_id,
            "username": username,
            "feedback": feedback_text,
            "type": feedback_type,
            "timestamp": datetime.utcnow()
        }
        
        db.feedback.insert_one(feedback_data)
        
        # Send to admins
        type_names = {
            "report_bug": "🐛 Bug Report",
            "suggest_feature": "💡 Feature Suggestion", 
            "send_compliment": "❤️ Compliment"
        }
        
        admin_message = f"""{type_names.get(feedback_type, "📝 Feedback")}

👤 **User:** @{username} ({user_id})
💬 **Message:** {feedback_text}"""
        
        for admin_id in ADMIN_IDS:
            try:
                await client.send_message(admin_id, admin_message)
            except:
                pass
        
        response_messages = {
            "report_bug": "🐛 **Bug Report Received!**\n\nThank you for reporting this issue.",
            "suggest_feature": "💡 **Feature Suggestion Received!**\n\nGreat idea! We'll consider it.",
            "send_compliment": "❤️ **Thank You!**\n\nYour kind words mean a lot to us!"
        }
        
        await message.reply_text(
            response_messages.get(feedback_type, "✅ Thank you for your feedback!")
        )
        
        # Clear user state
        del user_feedback_state[user_id]
        
    except Exception as e:
        logger.error(f"Error handling feedback input: {e}")

async def handle_name_search(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        search_query = message.text.strip()
        
        if len(search_query) < 2:
            await message.reply_text("⚠️ Please enter at least 2 characters to search.")
            return
        
        # Search in database (simplified)
        results = await search_by_name(search_query)
        
        if not results:
            await message.reply_text(
                f"❌ No results found for: `{search_query}`\n\n"
                f"Try searching with different keywords.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Search", callback_data="back_to_search")]
                ])
            )
            return
        
        await display_name_search_results(client, message, search_query, results)
        
        # Clear search mode
        if user_id in user_search_data:
            del user_search_data[user_id]
            
    except Exception as e:
        logger.error(f"Error handling name search: {e}")

# Simplified helper functions
async def search_by_name(query: str) -> list:
    try:
        results = []
        search_pattern = {"$regex": query, "$options": "i"}
        
        for collection_name, collection in [
            ("movies", movies_collection),
            ("webseries", series_collection),
            ("shows", shows_collection)
        ]:
            search_results = list(collection.find({
                "$or": [
                    {"name": search_pattern},
                    {"actors": {"$in": [search_pattern]}}
                ]
            }).limit(10))
            
            for result in search_results:
                result["content_type"] = collection_name
                results.append(result)
        
        return results[:20]
        
    except Exception as e:
        logger.error(f"Error searching by name: {e}")
        return []

async def display_name_search_results(client: Client, message: Message, query: str, results: list):
    try:
        text = f"🔍 **Search Results for:** `{query}`\n"
        text += f"📊 **Found {len(results)} results**\n\n"
        
        buttons = []
        
        for i, result in enumerate(results[:10], 1):
            name = result["name"]
            year = result.get("year", "")
            
            display_text = f"**{i}.** {name}"
            if year:
                display_text += f" ({year})"
            
            text += display_text + "\n"
            
            button_text = name[:25] + "..." if len(name) > 25 else name
            buttons.append([InlineKeyboardButton(
                f"{i}. {button_text}",
                callback_data=f"view_content_{result['_id']}"
            )])
        
        buttons.append([InlineKeyboardButton("🔙 Back to Search", callback_data="back_to_search")])
        
        keyboard = InlineKeyboardMarkup(buttons)
        await message.reply_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error displaying name search results: {e}")

async def show_search_results_by_type(client: Client, callback_query: CallbackQuery, search_type: str):
    try:
        results = await get_content_by_type(search_type, 0)
        
        type_names = {
            "movies": "🎬 **Movies**",
            "webseries": "📺 **Web Series**",
            "tvseries": "📻 **TV Series**",
            "shows": "🎭 **Shows**",
            "dubbed": "🗣️ **Dubbed Content**"
        }
        
        title = type_names.get(search_type, f"**{search_type.title()}**")
        await display_search_results(client, callback_query, results, title, search_type)
        
    except Exception as e:
        logger.error(f"Error showing search results by type: {e}")

async def get_content_by_type(content_type: str, page: int = 0) -> dict:
    try:
        if content_type == "dubbed":
            # Search for dubbed content across all collections
            query = {"is_dubbed": True}
            items = []
            for collection in [movies_collection, series_collection, shows_collection]:
                results = list(collection.find(query).sort("created_at", -1).limit(10))
                items.extend(results)
        else:
            # Get specific content type
            collection_map = {
                "movies": movies_collection,
                "webseries": series_collection,
                "tvseries": series_collection,
                "shows": shows_collection
            }
            collection = collection_map.get(content_type, movies_collection)
            items = list(collection.find({}).sort("created_at", -1).limit(10))
        
        return {
            "data": items[:10],
            "total": len(items),
            "has_more": len(items) == 10
        }
        
    except Exception as e:
        logger.error(f"Error getting content by type: {e}")
        return {"data": [], "total": 0, "has_more": False}

async def display_search_results(client: Client, callback_query: CallbackQuery, results: dict, title: str, search_type: str):
    try:
        if not results["data"]:
            await callback_query.edit_message_text(
                f"{title}\n\n❌ No results found.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Search", callback_data="back_to_search")]
                ])
            )
            return
        
        text = f"{title}\n"
        text += f"📊 **Total: {results['total']}**\n\n"
        
        buttons = []
        
        for i, item in enumerate(results["data"], 1):
            name = item["name"]
            year = item.get("year", "")
            language = item.get("language", "")
            
            text += f"**{i}.** {name}"
            if year:
                text += f" ({year})"
            if language:
                text += f" - {language}"
            text += "\n"
            
            buttons.append([InlineKeyboardButton(
                f"{i}. {name[:25]}..." if len(name) > 25 else f"{i}. {name}",
                callback_data=f"view_content_{item['_id']}"
            )])
        
        buttons.append([InlineKeyboardButton("🔙 Back to Search", callback_data="back_to_search")])
        
        keyboard = InlineKeyboardMarkup(buttons)
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error displaying search results: {e}")

async def get_latest_all_content() -> list:
    try:
        all_content = []
        
        for collection_name, collection in [
            ("movies", movies_collection),
            ("series", series_collection),
            ("shows", shows_collection)
        ]:
            latest = list(collection.find({}).sort("created_at", -1).limit(5))
            for item in latest:
                item["content_type"] = collection_name
                all_content.append(item)
        
        all_content.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        return all_content[:15]
        
    except Exception as e:
        logger.error(f"Error getting latest all content: {e}")
        return []

async def get_latest_by_type(content_type: str) -> list:
    try:
        if content_type == "series":
            collection = series_collection
        elif content_type == "shows":
            collection = shows_collection
        else:  # movies
            collection = movies_collection
        
        latest = list(collection.find({}).sort("created_at", -1).limit(15))
        for item in latest:
            item["content_type"] = content_type
        
        return latest
        
    except Exception as e:
        logger.error(f"Error getting latest by type: {e}")
        return []

async def display_latest_content(client: Client, callback_query: CallbackQuery, content_list: list, title: str):
    try:
        text = f"{title}\n"
        text += f"📅 **Recently Added Content**\n\n"
        
        buttons = []
        
        for i, item in enumerate(content_list[:10], 1):
            name = item["name"]
            year = item.get("year", "")
            
            display_text = f"**{i}.** {name}"
            if year:
                display_text += f" ({year})"
            
            text += display_text + "\n"
            
            button_text = name[:25] + "..." if len(name) > 25 else name
            buttons.append([InlineKeyboardButton(
                f"{i}. {button_text}",
                callback_data=f"view_content_{item['_id']}"
            )])
        
        buttons.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main")])
        
        keyboard = InlineKeyboardMarkup(buttons)
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error displaying latest content: {e}")

async def show_content_details(client: Client, callback_query: CallbackQuery, content: dict, content_type: str):
    try:
        text = f"🎬 **{content['name']}**\n\n"
        
        if content.get("year"):
            text += f"📅 **Year:** {content['year']}\n"
        if content.get("language"):
            text += f"🗣️ **Language:** {content['language']}\n"
        if content.get("genre"):
            text += f"🎭 **Genre:** {content['genre']}\n"
        
        if content.get("actors"):
            actors_str = ", ".join(content["actors"][:3])
            if len(content["actors"]) > 3:
                actors_str += f" and {len(content['actors']) - 3} more"
            text += f"👥 **Actors:** {actors_str}\n"
        
        if content.get("description"):
            text += f"\n📖 **Description:**\n{content['description'][:200]}"
            if len(content["description"]) > 200:
                text += "..."
            text += "\n"
        
        text += f"\n📊 **Views:** {content.get('view_count', 0)}"
        text += f" | **Downloads:** {content.get('download_count', 0)}"
        
        buttons = []
        
        # Show download options
        media_files = content.get("media_files", [])
        if media_files:
            text += f"\n\n💾 **Available Downloads:**\n"
            for i, media in enumerate(media_files[:3], 1):
                quality = media.get("quality", "HD")
                size = media.get("size", "Unknown")
                text += f"**{i}.** {quality} - {size}\n"
                
                buttons.append([InlineKeyboardButton(
                    f"📥 Download {quality} ({size})",
                    url=f"t.me/{BOT_USERNAME}?start=media-{media.get('msg_id', 'unknown')}"
                )])
        
        # Action buttons
        action_buttons = []
        action_buttons.append(InlineKeyboardButton("⭐ Rate", callback_data=f"rate_{content['_id']}"))
        action_buttons.append(InlineKeyboardButton("📱 Share", callback_data=f"share_{content['_id']}"))
        buttons.append(action_buttons)
        
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_search")])
        
        keyboard = InlineKeyboardMarkup(buttons)
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error showing content details: {e}")

# Remaining handler stubs
async def handle_season_selection(client: Client, callback_query: CallbackQuery):
    await callback_query.answer("Season selection feature coming soon!")

async def handle_episode_selection(client: Client, callback_query: CallbackQuery):
    await callback_query.answer("Episode selection feature coming soon!")

async def handle_rating(client: Client, callback_query: CallbackQuery):
    content_id = callback_query.data.replace("rate_", "")
    buttons = []
    for i in range(1, 6):
        buttons.append([InlineKeyboardButton(f"{'⭐' * i}", callback_data=f"rating_{content_id}_{i}")])
    
    keyboard = InlineKeyboardMarkup(buttons)
    await callback_query.edit_message_text("⭐ **Rate this content:**", reply_markup=keyboard)

async def handle_rating_submission(client: Client, callback_query: CallbackQuery):
    parts = callback_query.data.split("_")
    rating = int(parts[2])
    await callback_query.edit_message_text(f"✅ Thank you for rating {rating} stars!")

async def handle_share(client: Client, callback_query: CallbackQuery):
    content_id = callback_query.data.replace("share_", "")
    share_url = f"t.me/{BOT_USERNAME}?start=content-{content_id}"
    
    await callback_query.edit_message_text(
        f"📤 **Share this content:**\n\n`{share_url}`\n\nShare this link with friends!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data=f"view_content_{content_id}")]
        ])
    )

async def handle_filter_selection(client: Client, callback_query: CallbackQuery):
    await callback_query.answer("Filter feature coming soon!")

async def handle_navigation(client: Client, callback_query: CallbackQuery):
    await callback_query.answer("Navigation feature coming soon!")

async def handle_back_navigation(client: Client, callback_query: CallbackQuery):
    try:
        back_type = callback_query.data.replace("back_", "")
        
        if back_type == "to_search":
            await search_command(client, callback_query.message)
        elif back_type == "to_main":
            await start_command(client, callback_query.message)
        else:
            await search_command(client, callback_query.message)
    except Exception as e:
        logger.error(f"Error handling back navigation: {e}")

# Simplified helper functions for upload system
async def show_search_results(client: Client, message: Message, user_id: int, name: str):
    await message.reply_text(f"Showing search results for: {name}")

async def show_removal_options(client: Client, message: Message, user_id: int, name: str):
    await message.reply_text(f"Removal options for: {name}")

async def process_next_name(client: Client, message: Message, user_id: int):
    await message.reply_text("Processing next name...")

print("✅ Fixed Bot Handlers loaded!")
print("🎬 All command and callback handlers properly structured!")

# For Koyeb ping (add this to your main.py)
"""
# Add this to main.py for Koyeb ping functionality:

import requests
import threading
import time

def ping_server():
    '''Keep Koyeb instance alive by pinging itself'''
    url = "https://your-app-name.koyeb.app/health"  # Replace with your Koyeb URL
    
    while True:
        try:
            response = requests.get(url, timeout=30)
            logger.info(f"Ping successful: {response.status_code}")
        except Exception as e:
            logger.error(f"Ping failed: {e}")
        
        time.sleep(600)  # Ping every 10 minutes

# Start ping thread
ping_thread = threading.Thread(target=ping_server, daemon=True)
ping_thread.start()
"""
        
    except Exception as e:
        logger.error(f
