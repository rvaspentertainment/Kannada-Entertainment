import os
import asyncio
import logging
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
from config import *
# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration


# Initialize clients
app = Client
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DATABASE_NAME]

# Collections
movies_collection = db.movies
series_collection = db.series
shows_collection = db.shows
temp_data_collection = db.temp_data

# Global dictionaries to store temporary data
user_sessions = {}

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
        self.details = {}
        self.unavailable_list = []

    def add_media(self, media_id: str, media_info: dict):
        self.selected_media[media_id] = media_info

    def remove_media(self, media_id: str):
        if media_id in self.selected_media:
            del self.selected_media[media_id]

    def get_selected_count(self):
        return len(self.selected_media)

def get_user_session(user_id: int) -> MediaProcessor:
    if user_id not in user_sessions:
        user_sessions[user_id] = MediaProcessor()
    return user_sessions[user_id]

# Start command
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

# Media request handler
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
        
        # Find specific file
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
        
        try:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=channel_id,
                message_id=msg_id
            )
        except Exception as e:
            logger.error(f"Error forwarding media: {e}")
            await message.reply_text("❌ Failed to send media. Please contact admin.")
            
    except Exception as e:
        logger.error(f"Error handling media request: {e}")
        await message.reply_text("❌ An error occurred while processing your request.")

# Upload command (Admin only)
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

# Callback query handler for upload type selection
@app.on_callback_query(filters.regex(r"^up_"))
async def handle_upload_type(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        if user_id not in ADMIN_IDS:
            await callback_query.answer("❌ You're not authorized to use this feature.")
            return
        
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
        
        # Set user state for name input
        session.current_step = "waiting_for_names"
        
    except Exception as e:
        logger.error(f"Error handling upload type: {e}")
        await callback_query.answer("❌ An error occurred. Please try again.")

# Message handler for name input
@app.on_message(filters.text & filters.user(ADMIN_IDS))
async def handle_name_input(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        session = get_user_session(user_id)
        
        if not hasattr(session, 'current_step') or session.current_step != "waiting_for_names":
            return
        
        # Parse names from input
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
        
        # Start processing first name
        await process_next_name(client, message, user_id)
        
    except Exception as e:
        logger.error(f"Error handling name input: {e}")
        await message.reply_text("❌ An error occurred while processing names.")

async def process_next_name(client: Client, message: Message, user_id: int):
    try:
        session = get_user_session(user_id)
        
        if session.current_name_index >= len(session.names_to_process):
            await ask_for_details(client, message, user_id)
            return
        
        current_name = session.names_to_process[session.current_name_index]
        
        await message.reply_text(
            f"🔍 **Searching for:** `{current_name}`\n"
            f"📊 **Progress:** {session.current_name_index + 1}/{len(session.names_to_process)}\n\n"
            f"⏳ Please wait while I search in channels..."
        )
        
        # Search in channels
        search_results = await search_in_channels(client, current_name)
        
        if not search_results:
            session.unavailable_list.append(current_name)
            await message.reply_text(
                f"❌ **No results found for:** `{current_name}`\n"
                f"📝 Added to unavailable list.\n\n"
                f"⏭️ Moving to next item..."
            )
            session.current_name_index += 1
            await process_next_name(client, message, user_id)
            return
        
        session.search_results[current_name] = search_results
        session.current_page = 0
        session.total_pages = (len(search_results) - 1) // 10 + 1
        
        await show_search_results(client, message, user_id, current_name)
        
    except Exception as e:
        logger.error(f"Error processing name: {e}")
        await message.reply_text("❌ An error occurred while processing.")

async def search_in_channels(client: Client, search_term: str) -> List[dict]:
    """Search for media in configured channels"""
    results = []
    
    try:
        for channel_id in CHANNEL_IDS:
            try:
                async for msg in client.search_messages(
                    chat_id=channel_id,
                    query=search_term,
                    limit=50
                ):
                    if msg.video or msg.document:
                        # Check if search term matches in caption or file name
                        caption = msg.caption or ""
                        file_name = ""
                        
                        if msg.video:
                            file_name = msg.video.file_name or ""
                        elif msg.document:
                            file_name = msg.document.file_name or ""
                        
                        # Case-insensitive search
                        if (search_term.lower() in caption.lower() or 
                            search_term.lower() in file_name.lower()):
                            
                            # Extract quality from filename or caption
                            quality = extract_quality(file_name + " " + caption)
                            size = ""
                            
                            if msg.video:
                                size = format_file_size(msg.video.file_size)
                            elif msg.document:
                                size = format_file_size(msg.document.file_size)
                            
                            results.append({
                                "message_id": msg.id,
                                "channel_id": channel_id,
                                "caption": caption,
                                "file_name": file_name,
                                "quality": quality,
                                "size": size,
                                "file_type": "video" if msg.video else "document",
                                "link": f"https://t.me/c/{str(channel_id)[4:]}/{msg.id}"
                            })
                            
            except Exception as e:
                logger.error(f"Error searching in channel {channel_id}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in search_in_channels: {e}")
    
    return results

def extract_quality(text: str) -> str:
    """Extract video quality from text"""
    text = text.lower()
    qualities = ["4k", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p"]
    
    for quality in qualities:
        if quality in text:
            return quality.upper()
    
    # Check for common quality indicators
    if "uhd" in text or "ultra hd" in text:
        return "4K"
    elif "fhd" in text or "full hd" in text:
        return "1080P"
    elif "hd" in text:
        return "720P"
    
    return "UNKNOWN"

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

async def show_search_results(client: Client, message: Message, user_id: int, current_name: str):
    try:
        session = get_user_session(user_id)
        results = session.search_results[current_name]
        
        start_idx = session.current_page * 10
        end_idx = min(start_idx + 10, len(results))
        page_results = results[start_idx:end_idx]
        
        text = f"🔍 **Search Results for:** `{current_name}`\n"
        text += f"📊 **Page {session.current_page + 1} of {session.total_pages}**\n"
        text += f"📁 **Total Results:** {len(results)}\n\n"
        
        buttons = []
        for i, result in enumerate(page_results, start_idx + 1):
            display_text = result["file_name"] or result["caption"][:50]
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            
            text += f"**{i}.** `{display_text}`\n"
            text += f"   📐 Quality: {result['quality']} | 💾 Size: {result['size']}\n"
            text += f"   🔗 [Link]({result['link']})\n\n"
        
        # Navigation buttons
        nav_buttons = []
        if session.current_page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_page_{current_name}"))
        if session.current_page < session.total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"next_page_{current_name}"))
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        # Action buttons
        action_buttons = [
            InlineKeyboardButton("✅ Correct", callback_data=f"correct_{current_name}"),
            InlineKeyboardButton("❌ Wrong", callback_data=f"wrong_{current_name}")
        ]
        buttons.append(action_buttons)
        
        # Show selected media count if any
        selected_count = len([k for k in session.selected_media.keys() if k.startswith(current_name)])
        if selected_count > 0:
            text += f"✅ **Selected Files:** {selected_count}\n"
        
        keyboard = InlineKeyboardMarkup(buttons)
        
        try:
            await message.edit_text(text, reply_markup=keyboard)
        except:
            await message.reply_text(text, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error showing search results: {e}")
        await message.reply_text("❌ An error occurred while displaying results.")

# Callback query handlers for pagination and actions
@app.on_callback_query()
async def handle_callbacks(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        if user_id not in ADMIN_IDS and not data.startswith(("search_", "latest_", "help_")):
            await callback_query.answer("❌ You're not authorized.")
            return
        
        session = get_user_session(user_id)
        
        # Handle pagination
        if data.startswith("prev_page_") or data.startswith("next_page_"):
            action, _, name = data.split("_", 2)
            if action == "prev":
                session.current_page = max(0, session.current_page - 1)
            elif action == "next":
                session.current_page = min(session.total_pages - 1, session.current_page + 1)
            
            await show_search_results(client, callback_query.message, user_id, name)
            await callback_query.answer()
            
        # Handle correct selection
        elif data.startswith("correct_"):
            name = data.replace("correct_", "")
            # Mark current name as processed and move to next
            session.current_name_index += 1
            await callback_query.answer("✅ Marked as correct!")
            await process_next_name(client, callback_query.message, user_id)
            
        # Handle wrong selection
        elif data.startswith("wrong_"):
            name = data.replace("wrong_", "")
            await show_removal_options(client, callback_query.message, user_id, name)
            await callback_query.answer()
            
        # Handle cancel
        elif data == "cancel_upload":
            session.reset_data()
            await callback_query.edit_message_text("❌ Upload process cancelled.")
            
    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        await callback_query.answer("❌ An error occurred.")

async def show_removal_options(client: Client, message: Message, user_id: int, current_name: str):
    """Show buttons to remove specific files from selection"""
    try:
        session = get_user_session(user_id)
        results = session.search_results[current_name]
        
        start_idx = session.current_page * 10
        end_idx = min(start_idx + 10, len(results))
        
        text = f"❌ **Remove Files for:** `{current_name}`\n"
        text += f"📄 **Page {session.current_page + 1} of {session.total_pages}**\n\n"
        text += "👆 **Click on the file numbers you want to REMOVE:**\n\n"
        
        buttons = []
        row = []
        
        for i in range(start_idx, end_idx):
            file_num = i + 1
            row.append(InlineKeyboardButton(f"{file_num}", callback_data=f"remove_{current_name}_{i}"))
            if len(row) == 5:  # 5 buttons per row
                buttons.append(row)
                row = []
        
        if row:  # Add remaining buttons
            buttons.append(row)
        
        # Navigation and action buttons
        nav_buttons = []
        if session.current_page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_remove_{current_name}"))
        if session.current_page < session.total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"next_remove_{current_name}"))
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        # Done button
        buttons.append([InlineKeyboardButton("✅ Done Removing", callback_data=f"done_remove_{current_name}")])
        
        keyboard = InlineKeyboardMarkup(buttons)
        await message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error showing removal options: {e}")

async def ask_for_details(client: Client, message: Message, user_id: int):
    """Ask user for entertainment details"""
    try:
        session = get_user_session(user_id)
        
        # Show summary and start details collection
        processed_names = session.names_to_process[:session.current_name_index]
        
        summary_text = "🎉 **Search Process Completed!**\n\n"
        summary_text += f"✅ **Processed:** {len(processed_names)} items\n"
        if session.unavailable_list:
            summary_text += f"❌ **Unavailable:** {len(session.unavailable_list)} items\n"
            summary_text += f"📝 Unavailable list: {', '.join(session.unavailable_list)}\n\n"
        
        summary_text += "📋 **Now collecting details for each item...**\n"
        summary_text += "💡 **Tip:** Send 'none' or 'unknown' if you don't know any detail.\n\n"
        
        await message.reply_text(summary_text)
        
        # Start collecting details for first processed item
        if processed_names:
            session.current_detail_index = 0
            await collect_item_details(client, message, user_id)
        else:
            await finalize_upload(client, message, user_id)
            
    except Exception as e:
        logger.error(f"Error asking for details: {e}")

async def collect_item_details(client: Client, message: Message, user_id: int):
    """Collect details for individual items"""
    try:
        session = get_user_session(user_id)
        
        if not hasattr(session, 'current_detail_index'):
            session.current_detail_index = 0
        
        processed_names = session.names_to_process[:session.current_name_index]
        
        if session.current_detail_index >= len(processed_names):
            await finalize_upload(client, message, user_id)
            return
        
        current_item = processed_names[session.current_detail_index]
        entertainment_type = session.entertainment_type
        
        # Define fields based on entertainment type
        if entertainment_type == "movies":
            fields = ["name", "year", "language", "genre", "actors", "director", "poster_link", "description"]
        else:  # series, shows, etc.
            fields = ["name", "year", "language", "genre", "actors", "seasons", "episodes", "poster_link", "description"]
        
        if not hasattr(session, 'current_field_index'):
            session.current_field_index = 0
        
        if session.current_field_index >= len(fields):
            # Move to next item
            session.current_detail_index += 1
            session.current_field_index = 0
            await collect_item_details(client, message, user_id)
            return
        
        current_field = fields[session.current_field_index]
        
        field_prompts = {
            "name": "📝 **Enter the full name:**",
            "year": "📅 **Enter release year:**",
            "language": "🗣️ **Enter language (e.g., Kannada, Kannada Dub):**",
            "genre": "🎭 **Enter genre (e.g., Action, Drama, Comedy):**",
            "actors": "👥 **Enter main actors (comma-separated):**",
            "director": "🎬 **Enter director name:**",
            "seasons": "📺 **Enter number of seasons:**",
            "episodes": "📋 **Enter total episodes:**",
            "poster_link": "🖼️ **Enter poster image URL:**",
            "description": "📖 **Enter description/plot:**"
        }
        
        prompt_text = f"📊 **Item {session.current_detail_index + 1}/{len(processed_names)}:** `{current_item}`\n\n"
        prompt_text += field_prompts.get(current_field, f"Enter {current_field}:")
        prompt_text += f"\n\n💡 Send 'none' or 'unknown' if not available."
        
        await message.reply_text(prompt_text)
        session.current_step = "collecting_details"
        
    except Exception as e:
        logger.error(f"Error collecting item details: {e}")

# Continue with more handlers and the finalization process...

