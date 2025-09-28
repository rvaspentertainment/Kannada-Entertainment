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

# Part 2: Details Collection, Database Storage, and Media Processing

# Additional imports for Part 2
import uuid
import re
from urllib.parse import urlparse
import requests
from typing import Any

# Continue from Part 1...

# Handle detail input messages
@app.on_message(filters.text & filters.user(ADMIN_IDS))
async def handle_detail_input(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        session = get_user_session(user_id)
        
        # Check if we're in details collection mode
        if not hasattr(session, 'current_step') or session.current_step != "collecting_details":
            return
        
        detail_value = message.text.strip()
        
        # Handle "none" or "unknown" inputs
        if detail_value.lower() in ["none", "unknown", "n/a", ""]:
            detail_value = "Unknown"
        
        # Store the detail
        await store_current_detail(session, detail_value)
        
        # Move to next field
        session.current_field_index += 1
        await collect_item_details(client, message, user_id)
        
    except Exception as e:
        logger.error(f"Error handling detail input: {e}")
        await message.reply_text("❌ Error processing input. Please try again.")

async def store_current_detail(session: MediaProcessor, value: str):
    """Store current detail being collected"""
    try:
        processed_names = session.names_to_process[:session.current_name_index]
        current_item = processed_names[session.current_detail_index]
        entertainment_type = session.entertainment_type
        
        # Define fields based on entertainment type
        if entertainment_type == "movies":
            fields = ["name", "year", "language", "genre", "actors", "director", "poster_link", "description"]
        else:
            fields = ["name", "year", "language", "genre", "actors", "seasons", "episodes", "poster_link", "description"]
        
        current_field = fields[session.current_field_index]
        
        # Initialize details dict for current item if not exists
        if current_item not in session.details:
            session.details[current_item] = {}
        
        # Process specific fields
        if current_field == "actors":
            # Split by comma and clean
            actors_list = [actor.strip() for actor in value.split(",") if actor.strip()]
            session.details[current_item][current_field] = actors_list
        elif current_field == "year":
            # Validate year
            try:
                year_int = int(value) if value != "Unknown" else 0
                if year_int < 1900 or year_int > 2030:
                    year_int = 0
                session.details[current_item][current_field] = year_int
            except:
                session.details[current_item][current_field] = 0
        elif current_field in ["seasons", "episodes"]:
            # Convert to integer
            try:
                session.details[current_item][current_field] = int(value) if value != "Unknown" else 1
            except:
                session.details[current_item][current_field] = 1
        elif current_field == "language":
            # Handle language specially for Kannada content
            lang_lower = value.lower()
            if "kannada" in lang_lower and "dub" in lang_lower:
                session.details[current_item][current_field] = "Kannada Dub"
                session.details[current_item]["is_dubbed"] = True
            elif "kannada" in lang_lower:
                session.details[current_item][current_field] = "Kannada"
                session.details[current_item]["is_dubbed"] = False
            else:
                session.details[current_item][current_field] = value
                session.details[current_item]["is_dubbed"] = "dub" in lang_lower
        else:
            session.details[current_item][current_field] = value
            
    except Exception as e:
        logger.error(f"Error storing detail: {e}")

async def finalize_upload(client: Client, message: Message, user_id: int):
    """Finalize the upload process and save to database"""
    try:
        session = get_user_session(user_id)
        
        await message.reply_text(
            "💾 **Processing and saving data to database...**\n"
            "⏳ Please wait while I organize all the information."
        )
        
        saved_count = 0
        error_count = 0
        
        # Process each item
        for item_name, item_details in session.details.items():
            try:
                # Get selected media for this item
                item_media = get_item_media(session, item_name)
                
                if not item_media:
                    logger.warning(f"No media found for {item_name}")
                    continue
                
                # Process media files based on entertainment type
                processed_media = await process_media_files(client, item_media, session.entertainment_type)
                
                # Create database document
                doc_data = create_database_document(item_name, item_details, processed_media, session.entertainment_type)
                
                # Save to appropriate collection
                collection = get_collection_by_type(session.entertainment_type)
                
                # Check if already exists
                existing = collection.find_one({"name": item_details.get("name", item_name)})
                if existing:
                    # Update existing
                    collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": doc_data}
                    )
                else:
                    # Insert new
                    collection.insert_one(doc_data)
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {item_name}: {e}")
                error_count += 1
        
        # Send completion message
        completion_text = f"✅ **Upload Process Completed!**\n\n"
        completion_text += f"💾 **Saved to Database:** {saved_count} items\n"
        if error_count > 0:
            completion_text += f"❌ **Errors:** {error_count} items\n"
        if session.unavailable_list:
            completion_text += f"📝 **Unavailable:** {len(session.unavailable_list)} items\n"
            completion_text += f"🔍 **Unavailable List:**\n"
            for item in session.unavailable_list:
                completion_text += f"   • {item}\n"
        
        completion_text += f"\n🌐 **Next Step:** Updating blogger site..."
        
        await message.reply_text(completion_text)
        
        # Update blogger site
        if saved_count > 0:
            await update_blogger_site(client, message, user_id)
        
        # Clear session
        session.reset_data()
        
    except Exception as e:
        logger.error(f"Error finalizing upload: {e}")
        await message.reply_text("❌ Error occurred while saving data.")

def get_item_media(session: MediaProcessor, item_name: str) -> List[dict]:
    """Get selected media files for specific item"""
    item_media = []
    
    try:
        # Get search results for this item
        if item_name in session.search_results:
            results = session.search_results[item_name]
            
            # Get selected media keys for this item
            selected_keys = [k for k in session.selected_media.keys() if k.startswith(f"{item_name}_")]
            
            # If no specific selections, take all results as correct
            if not selected_keys:
                item_media = results
            else:
                # Get only selected items
                for key in selected_keys:
                    index = int(key.split("_")[-1])
                    if index < len(results):
                        item_media.append(results[index])
                        
    except Exception as e:
        logger.error(f"Error getting item media for {item_name}: {e}")
    
    return item_media

async def process_media_files(client: Client, media_files: List[dict], entertainment_type: str) -> List[dict]:
    """Process and organize media files"""
    processed_files = []
    
    try:
        for media in media_files:
            processed_media = {
                "msg_id": str(uuid.uuid4()),  # Unique ID for bot links
                "original_msg_id": media["message_id"],
                "channel_id": media["channel_id"],
                "file_name": media["file_name"],
                "caption": media["caption"],
                "quality": media["quality"],
                "size": media["size"],
                "file_type": media["file_type"],
                "telegram_link": media["link"]
            }
            
            # For series/shows, try to extract season/episode info
            if entertainment_type in ["webseries", "tvseries", "shows"]:
                season_episode = extract_season_episode(media["file_name"], media["caption"])
                processed_media.update(season_episode)
            
            # Validate quality and ask admin if unknown
            if processed_media["quality"] == "UNKNOWN":
                try:
                    await ask_admin_for_quality(client, media, processed_media)
                except:
                    processed_media["quality"] = "HD"  # Default fallback
            
            processed_files.append(processed_media)
            
    except Exception as e:
        logger.error(f"Error processing media files: {e}")
    
    return processed_files

def extract_season_episode(filename: str, caption: str) -> dict:
    """Extract season and episode information from filename or caption"""
    text = f"{filename} {caption}".lower()
    result = {"season": 1, "episode": 1, "season_episode_text": ""}
    
    try:
        # Season patterns
        season_patterns = [
            r's(\d+)',  # s1, s2
            r'season[\s\._-]*(\d+)',  # season 1, season_1
            r'series[\s\._-]*(\d+)',  # series 1
        ]
        
        # Episode patterns  
        episode_patterns = [
            r'e(\d+)',  # e1, e2
            r'ep[\s\._-]*(\d+)',  # ep1, ep_1
            r'episode[\s\._-]*(\d+)',  # episode 1
        ]
        
        # Combined patterns
        combined_patterns = [
            r's(\d+)e(\d+)',  # s1e1
            r'season[\s\._-]*(\d+)[\s\._-]*episode[\s\._-]*(\d+)',  # season 1 episode 1
        ]
        
        # Try combined patterns first
        for pattern in combined_patterns:
            match = re.search(pattern, text)
            if match:
                result["season"] = int(match.group(1))
                result["episode"] = int(match.group(2))
                result["season_episode_text"] = match.group(0)
                return result
        
        # Try individual patterns
        for pattern in season_patterns:
            match = re.search(pattern, text)
            if match:
                result["season"] = int(match.group(1))
                break
        
        for pattern in episode_patterns:
            match = re.search(pattern, text)
            if match:
                result["episode"] = int(match.group(1))
                break
                
    except Exception as e:
        logger.error(f"Error extracting season/episode: {e}")
    
    return result

async def ask_admin_for_quality(client: Client, media: dict, processed_media: dict):
    """Ask admin for quality when it can't be detected"""
    try:
        for admin_id in ADMIN_IDS:
            try:
                quality_text = f"🔍 **Quality Detection Needed**\n\n"
                quality_text += f"📁 **File:** {media['file_name']}\n"
                quality_text += f"📝 **Caption:** {media['caption'][:100]}...\n"
                quality_text += f"🔗 **Link:** {media['link']}\n\n"
                quality_text += f"❓ **Please specify quality:**"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("4K", callback_data=f"quality_4K_{processed_media['msg_id']}"),
                     InlineKeyboardButton("1080P", callback_data=f"quality_1080P_{processed_media['msg_id']}")],
                    [InlineKeyboardButton("720P", callback_data=f"quality_720P_{processed_media['msg_id']}"),
                     InlineKeyboardButton("480P", callback_data=f"quality_480P_{processed_media['msg_id']}")],
                    [InlineKeyboardButton("360P", callback_data=f"quality_360P_{processed_media['msg_id']}"),
                     InlineKeyboardButton("Skip", callback_data=f"quality_SKIP_{processed_media['msg_id']}")]
                ])
                
                await client.send_message(
                    chat_id=admin_id,
                    text=quality_text,
                    reply_markup=keyboard
                )
                break  # Send to first admin only
                
            except Exception as e:
                logger.error(f"Error sending quality request to admin {admin_id}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in ask_admin_for_quality: {e}")

# Handle quality selection callback
@app.on_callback_query(filters.regex(r"^quality_"))
async def handle_quality_selection(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        if user_id not in ADMIN_IDS:
            await callback_query.answer("❌ Not authorized")
            return
        
        data_parts = callback_query.data.split("_")
        quality = data_parts[1]
        msg_id = data_parts[2]
        
        if quality == "SKIP":
            quality = "HD"  # Default quality
        
        # Update temporary storage (in real implementation, you'd store this properly)
        temp_quality_store[msg_id] = quality
        
        await callback_query.edit_message_text(
            f"✅ **Quality Updated**\n"
            f"📐 **Selected Quality:** {quality}\n"
            f"🆔 **Media ID:** {msg_id}"
        )
        
    except Exception as e:
        logger.error(f"Error handling quality selection: {e}")
        await callback_query.answer("❌ Error occurred")

# Global temp storage for quality updates
temp_quality_store = {}

def create_database_document(item_name: str, item_details: dict, media_files: List[dict], entertainment_type: str) -> dict:
    """Create database document structure"""
    
    base_doc = {
        "name": item_details.get("name", item_name),
        "original_search_name": item_name,
        "type": entertainment_type,
        "year": item_details.get("year", 0),
        "language": item_details.get("language", "Kannada"),
        "genre": item_details.get("genre", "Unknown"),
        "actors": item_details.get("actors", []),
        "poster_url": item_details.get("poster_link", ""),
        "description": item_details.get("description", ""),
        "is_dubbed": item_details.get("is_dubbed", False),
        "media_files": media_files,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "view_count": 0,
        "download_count": 0,
        "rating": 0.0,
        "total_ratings": 0
    }
    
    # Add type-specific fields
    if entertainment_type == "movies":
        base_doc.update({
            "director": item_details.get("director", "Unknown"),
            "duration": item_details.get("duration", ""),
            "imdb_rating": 0.0,
            "box_office": ""
        })
    else:
        # For series/shows
        base_doc.update({
            "total_seasons": item_details.get("seasons", 1),
            "total_episodes": item_details.get("episodes", 1),
            "status": "Completed",  # Completed, Ongoing, Upcoming
            "network": item_details.get("network", ""),
            "creator": item_details.get("director", "Unknown")
        })
        
        # Organize episodes by season
        seasons_data = organize_episodes_by_season(media_files)
        base_doc["seasons_data"] = seasons_data
    
    return base_doc

def organize_episodes_by_season(media_files: List[dict]) -> dict:
    """Organize media files by seasons and episodes"""
    seasons = {}
    
    try:
        for media in media_files:
            season_num = media.get("season", 1)
            episode_num = media.get("episode", 1)
            
            if season_num not in seasons:
                seasons[season_num] = {
                    "season_number": season_num,
                    "episodes": {},
                    "episode_count": 0
                }
            
            # Group by episode (multiple qualities)
            if episode_num not in seasons[season_num]["episodes"]:
                seasons[season_num]["episodes"][episode_num] = {
                    "episode_number": episode_num,
                    "title": f"Episode {episode_num}",
                    "description": "",
                    "files": []
                }
            
            seasons[season_num]["episodes"][episode_num]["files"].append(media)
            
        # Update episode counts
        for season_num in seasons:
            seasons[season_num]["episode_count"] = len(seasons[season_num]["episodes"])
            
    except Exception as e:
        logger.error(f"Error organizing episodes: {e}")
    
    return seasons

def get_collection_by_type(entertainment_type: str):
    """Get appropriate MongoDB collection by type"""
    collections = {
        "movies": movies_collection,
        "webseries": series_collection,
        "tvseries": series_collection,
        "shows": shows_collection
    }
    return collections.get(entertainment_type, movies_collection)

async def update_blogger_site(client: Client, message: Message, user_id: int):
    """Update the blogger site with new content"""
    try:
        await message.reply_text(
            "🌐 **Updating Blogger Site...**\n"
            "📤 Preparing content for blog publication..."
        )
        
        # This would integrate with Blogger API
        # For now, we'll create the content structure
        
        session = get_user_session(user_id)
        blog_updates = []
        
        for item_name, item_details in session.details.items():
            blog_post = create_blog_post_content(item_name, item_details, session.entertainment_type)
            blog_updates.append(blog_post)
        
        # In real implementation, post to Blogger API
        success_count = await publish_to_blogger(blog_updates)
        
        await message.reply_text(
            f"✅ **Blogger Update Complete!**\n\n"
            f"📝 **Published:** {success_count} posts\n"
            f"🌐 **Blog URL:** https://kannada-movies-rvasp.blogspot.com\n\n"
            f"🎉 **Process fully completed!**"
        )
        
    except Exception as e:
        logger.error(f"Error updating blogger: {e}")
        await message.reply_text("❌ Error updating blogger site.")

def create_blog_post_content(item_name: str, item_details: dict, entertainment_type: str) -> dict:
    """Create blog post content structure"""
    
    post_content = {
        "title": item_details.get("name", item_name),
        "content": generate_blog_html_content(item_details, entertainment_type),
        "labels": generate_blog_labels(item_details, entertainment_type),
        "status": "PUBLISHED"
    }
    
    return post_content

def generate_blog_html_content(details: dict, entertainment_type: str) -> str:
    """Generate HTML content for blog post"""
    
    html = f"""
    <div class="movie-container">
        <div class="movie-header">
            <img src="{details.get('poster_url', '')}" alt="{details.get('name', '')}" class="movie-poster">
            <div class="movie-info">
                <h1>{details.get('name', '')}</h1>
                <p><strong>Year:</strong> {details.get('year', 'Unknown')}</p>
                <p><strong>Language:</strong> {details.get('language', 'Kannada')}</p>
                <p><strong>Genre:</strong> {details.get('genre', 'Unknown')}</p>
                <p><strong>Actors:</strong> {', '.join(details.get('actors', []))}</p>
                {'<p><strong>Director:</strong> ' + details.get('director', 'Unknown') + '</p>' if entertainment_type == 'movies' else ''}
            </div>
        </div>
        
        <div class="movie-description">
            <h3>Description</h3>
            <p>{details.get('description', 'No description available.')}</p>
        </div>
        
        <div class="download-section">
            <h3>Download Links</h3>
            <div id="download-buttons">
                <!-- Download buttons will be generated by JavaScript -->
            </div>
        </div>
    </div>
    
    <script>
        // JavaScript to generate download buttons
        // This will be populated with actual download links
    </script>
    """
    
    return html

def generate_blog_labels(details: dict, entertainment_type: str) -> List[str]:
    """Generate labels/tags for blog post"""
    labels = []
    
    # Add basic labels
    labels.append(entertainment_type.title())
    labels.append(details.get('language', 'Kannada'))
    labels.append(str(details.get('year', '')))
    
    # Add genre
    if details.get('genre'):
        labels.append(details['genre'])
    
    # Add actors as labels
    actors = details.get('actors', [])
    for actor in actors[:3]:  # Limit to first 3 actors
        labels.append(actor)
    
    # Add dubbed label if applicable
    if details.get('is_dubbed'):
        labels.append('Dubbed')
    
    return [label for label in labels if label and label != 'Unknown']

async def publish_to_blogger(blog_updates: List[dict]) -> int:
    """Publish updates to Blogger (mock implementation)"""
    try:
        # This would use Google Blogger API
        # For now, return success count
        return len(blog_updates)
        
    except Exception as e:
        logger.error(f"Error publishing to blogger: {e}")
        return 0

# Handle removal callbacks
@app.on_callback_query(filters.regex(r"^remove_"))
async def handle_file_removal(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        if user_id not in ADMIN_IDS:
            await callback_query.answer("❌ Not authorized")
            return
        
        session = get_user_session(user_id)
        
        # Parse callback data: remove_itemname_index
        parts = callback_query.data.split("_", 2)
        item_name = parts[1]
        file_index = int(parts[2])
        
        # Remove from selected media
        removal_key = f"{item_name}_{file_index}"
        if removal_key in session.selected_media:
            del session.selected_media[removal_key]
            await callback_query.answer(f"✅ Removed file #{file_index + 1}")
        else:
            # Add to selected media for removal (toggle behavior)
            session.selected_media[removal_key] = {"removed": True}
            await callback_query.answer(f"❌ Marked file #{file_index + 1} for removal")
        
    except Exception as e:
        logger.error(f"Error handling file removal: {e}")
        await callback_query.answer("❌ Error occurred")

# Handle removal navigation
@app.on_callback_query(filters.regex(r"^(prev|next)_remove_"))
async def handle_removal_navigation(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        session = get_user_session(user_id)
        
        data_parts = callback_query.data.split("_")
        action = data_parts[0]
        item_name = data_parts[2]
        
        if action == "prev":
            session.current_page = max(0, session.current_page - 1)
        elif action == "next":
            session.current_page = min(session.total_pages - 1, session.current_page + 1)
        
        await show_removal_options(client, callback_query.message, user_id, item_name)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in removal navigation: {e}")
        await callback_query.answer("❌ Error occurred")

# Handle done removing
@app.on_callback_query(filters.regex(r"^done_remove_"))
async def handle_done_removing(client: Client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        session = get_user_session(user_id)
        
        item_name = callback_query.data.replace("done_remove_", "")
        
        # Show updated results
        await show_search_results(client, callback_query.message, user_id, item_name)
        await callback_query.answer("✅ File removal completed")
        
    except Exception as e:
        logger.error(f"Error handling done removing: {e}")
        await callback_query.answer("❌ Error occurred")

print("📦 Part 2: Details Collection and Database Storage loaded!")
