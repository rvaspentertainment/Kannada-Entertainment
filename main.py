







# kannada_bot.py
import os
import sys
import logging
import re
import uuid
import math
import asyncio
from datetime import datetime
from typing import Dict, List, Any
from urllib.parse import quote
from threading import Thread

# Third-party libraries
import aiohttp
from dotenv import load_dotenv
from flask import Flask, jsonify
from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardButton,
    InlineKeyboardMarkup, InputMediaPhoto
)
from pyrogram.errors import MessageNotModified
from pymongo import MongoClient
from bson import ObjectId

# --- 1. INITIAL SETUP: CONFIG, LOGGING, CLIENTS ---

# region --- Configuration and Initialization ---

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- Environment Variable Loading & Validation ---
try:
    API_ID = int(os.environ["API_ID"])
    API_HASH = os.environ["API_HASH"]
    BOT_TOKEN = os.environ["BOT_TOKEN"]
    ADMIN_IDS = [int(x) for x in os.environ["ADMIN_IDS"].split(",") if x.strip()]
    CHANNEL_IDS = [int(x) for x in os.environ["CHANNEL_IDS"].split(",") if x.strip()]
    MONGO_URL = os.environ["MONGO_URL"]
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "kannada_entertainment")
    BOT_USERNAME = os.environ["BOT_USERNAME"].replace("@", "")
    BLOGGER_API_KEY = os.environ.get("BLOGGER_API_KEY")
    BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID")
    BLOG_URL = os.environ.get("BLOG_URL")
    PORT = int(os.environ.get("PORT", 8080))
except (KeyError, ValueError) as e:
    logger.critical(f"❌ Critical Error: Missing or invalid environment variable: {e}. Bot cannot start.")
    sys.exit(1)

# --- Pyrogram Client and Database Connection ---
try:
    app = Client("kannada_entertainment_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    mongo_client = MongoClient(MONGO_URL)
    db = mongo_client[DATABASE_NAME]
    movies_collection = db.movies
    series_collection = db.series
    shows_collection = db.shows
    logger.info("✅ Successfully connected to MongoDB.")
except Exception as e:
    logger.critical(f"❌ Critical Error: Could not connect to MongoDB: {e}. Check MONGO_URL.")
    sys.exit(1)

# Filters for easy access control
admin_filter = filters.user(ADMIN_IDS)
# endregion

# --- 2. HELPER CLASSES & CORE FUNCTIONS ---

# region --- Helper Classes and Functions ---

class AdminSession:
    """Manages the state for an admin's multi-step upload process."""
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.reset()

    def reset(self):
        """Resets the session to its initial state."""
        self.step = None
        self.content_type = None
        self.names_to_process = []
        self.current_name_index = 0
        self.search_results = {}
        self.details_buffer = {}
        self.unavailable_list = []
        self.current_page = 0
        self.total_pages = 0
        self.current_details_item = None
        self.required_fields = []
        self.current_field_index = 0
        logger.info(f"Admin session for {self.user_id} has been reset.")

admin_sessions: Dict[int, AdminSession] = {}

def get_admin_session(user_id: int) -> AdminSession:
    """Gets or creates a session for an admin."""
    if user_id not in admin_sessions:
        admin_sessions[user_id] = AdminSession(user_id)
    return admin_sessions[user_id]

def format_file_size(size_bytes: int) -> str:
    """Formats file size into a human-readable string (e.g., '1.25 GB')."""
    if not isinstance(size_bytes, (int, float)) or size_bytes <= 0:
        return "0 B"
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def extract_quality(text: str) -> str:
    """Extracts video quality from text (filename or caption)."""
    text = text.lower()
    patterns = {
        "4K": [r'4k', r'2160p', r'uhd'],
        "1080p": [r'1080p', r'fhd'],
        "720p": [r'720p', r'hd'],
        "480p": [r'480p'],
        "360p": [r'360p']
    }
    for quality, regex_list in patterns.items():
        for regex in regex_list:
            if re.search(regex, text):
                return quality
    return "HD"

def get_collection_by_type(content_type: str):
    """Returns the correct MongoDB collection based on content type."""
    return {
        "movie": movies_collection,
        "webseries": series_collection,
        "tvseries": series_collection,
        "show": shows_collection
    }.get(content_type, movies_collection)

async def edit_or_reply(message: Message, text: str, reply_markup=None, is_edit: bool = False):
    """Edits a message if possible, otherwise sends a new one."""
    try:
        if is_edit:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await message.reply_text(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.MARKDOWN)
    except MessageNotModified:
        pass
    except Exception as e:
        logger.warning(f"Could not edit message, sending new one. Error: {e}")
        await message.reply_text(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.MARKDOWN)
# endregion

# --- (The rest of the bot code goes here as provided in the previous response) ---

# --- 3. ADMIN UPLOAD WORKFLOW ---

# region --- Admin: /up Command and Initial Setup ---

@app.on_message(filters.command("up") & admin_filter)
async def upload_command(client: Client, message: Message):
    try:
        session = get_admin_session(message.from_user.id)
        session.reset()
        text = "📤 **Content Upload System**\n\nSelect the type of entertainment you wish to upload:"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Movie", callback_data="up_type_movie")],
            [InlineKeyboardButton("📺 Web Series", callback_data="up_type_webseries")],
            [InlineKeyboardButton("📻 TV Series", callback_data="up_type_tvseries")],
            [InlineKeyboardButton("🎭 Show", callback_data="up_type_show")],
            [InlineKeyboardButton("❌ Cancel", callback_data="up_cancel")]
        ])
        await message.reply_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in /up command: {e}", exc_info=True)
        await message.reply_text("An error occurred. Please try again.")

@app.on_callback_query(filters.regex(r"^up_type_") & admin_filter)
async def up_type_callback(client: Client, cb: CallbackQuery):
    try:
        session = get_admin_session(cb.from_user.id)
        session.content_type = cb.data.split("_")[-1]
        session.step = 'awaiting_names'
        type_name = session.content_type.replace("series", " Series").title()
        text = (
            f"✅ **Type Selected: {type_name}**\n\n"
            f"📝 Now, send me the name(s) of the `{type_name}` you want to upload.\n\n"
            "**Format Examples:**\n"
            "• For a single item: `Kantara`\n"
            "• For multiple items: `KGF, RRR, Salaar` (separated by a comma)"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="up_cancel")]])
        await cb.edit_message_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in up_type_callback: {e}", exc_info=True)
        await cb.answer("An error occurred.", show_alert=True)

@app.on_message(filters.text & admin_filter & filters.private & ~filters.command(None))
async def admin_text_handler(client: Client, message: Message):
    session = get_admin_session(message.from_user.id)
    if not session.step: return

    try:
        if session.step == 'awaiting_names':
            await process_names_input(client, message, session)
        elif session.step == 'awaiting_details':
            await process_details_input(client, message, session)
    except Exception as e:
        logger.error(f"Error in admin_text_handler (step: {session.step}): {e}", exc_info=True)
        await message.reply_text("An error occurred while processing your input.")

async def process_names_input(client: Client, message: Message, session: AdminSession):
    names = [name.strip() for name in message.text.split(",") if name.strip()]
    if not names:
        await message.reply_text("Please provide at least one valid name.")
        return
    session.names_to_process = names
    session.step = 'searching'
    await message.reply_text(f"✅ Received {len(names)} names. Starting search process...")
    await search_next_name(client, message, session)

# endregion

# region --- Admin: Channel Search and File Verification ---

async def search_next_name(client: Client, message: Message, session: AdminSession):
    if session.current_name_index >= len(session.names_to_process):
        await start_details_collection(client, message, session)
        return

    current_name = session.names_to_process[session.current_name_index]
    status_msg = await message.reply_text(f"🔍 Searching for `{current_name}`... ({session.current_name_index + 1}/{len(session.names_to_process)})")

    all_results = []
    for channel_id in CHANNEL_IDS:
        try:
            async for msg in client.search_messages(chat_id=channel_id, query=current_name, limit=100):
                if msg.video or msg.document:
                    file_name = (msg.video.file_name if msg.video else msg.document.file_name) or ""
                    caption = msg.caption or ""
                    if current_name.lower() in file_name.lower() or current_name.lower() in caption.lower():
                        all_results.append({
                            "msg_id": msg.id,
                            "original_msg_id": msg.id,
                            "channel_id": msg.chat.id,
                            "file_name": file_name,
                            "caption": caption,
                            "size": format_file_size(msg.video.file_size if msg.video else msg.document.file_size),
                            "quality": extract_quality(f"{file_name} {caption}")
                        })
        except Exception as e:
            logger.error(f"Could not search in channel {channel_id}: {e}")

    if not all_results:
        session.unavailable_list.append(current_name)
        await status_msg.edit_text(f"❌ No results found for `{current_name}`. Added to unavailable list.")
        session.current_name_index += 1
        await asyncio.sleep(2)
        await search_next_name(client, message, session)
    else:
        session.search_results[current_name] = {"results": all_results, "removed_indices": set()}
        await show_verification_results(status_msg, session, is_edit=True)

async def show_verification_results(message: Message, session: AdminSession, is_edit: bool = False):
    current_name = session.names_to_process[session.current_name_index]
    data = session.search_results[current_name]
    results, removed_indices = data["results"], data["removed_indices"]
    session.total_pages = math.ceil(len(results) / 10)
    start_index = session.current_page * 10
    page_results = results[start_index : start_index + 10]
    text = f"**🔍 Results for `{current_name}`**\nPage {session.current_page + 1}/{session.total_pages}\n\n"
    for i, result in enumerate(page_results, start=start_index):
        file_info = f"`{result['file_name'] or 'No Filename'}` ({result['quality']}, {result['size']})"
        text += f"~~{i+1}. {file_info}~~ 🗑️\n" if i in removed_indices else f"{i+1}. {file_info}\n"
    text += "\nReview the files. If they are correct, proceed. If some are wrong, remove them first."
    keyboard = []
    nav_row = []
    if session.current_page > 0: nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data="up_nav_prev"))
    if start_index + 10 < len(results): nav_row.append(InlineKeyboardButton("Next ➡️", callback_data="up_nav_next"))
    if nav_row: keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton("✅ All Correct", callback_data="up_correct"), InlineKeyboardButton("🗑️ Remove Files", callback_data="up_wrong")])
    keyboard.append([InlineKeyboardButton("❌ Cancel Upload", callback_data="up_cancel")])
    await edit_or_reply(message, text, InlineKeyboardMarkup(keyboard), is_edit=is_edit)

async def show_removal_options(message: Message, session: AdminSession, is_edit: bool = True):
    current_name = session.names_to_process[session.current_name_index]
    data = session.search_results[current_name]
    results, removed_indices = data["results"], data["removed_indices"]
    start_index = session.current_page * 10
    page_results = results[start_index : start_index + 10]
    text = f"**🗑️ Remove incorrect files for `{current_name}`**\nClick a number to mark/unmark it for removal."
    buttons = []
    row = []
    for i in range(start_index, start_index + len(page_results)):
        label = f"✅ {i+1}" if i in removed_indices else f"❌ {i+1}"
        row.append(InlineKeyboardButton(label, callback_data=f"up_remove_{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton("✅ Done Removing", callback_data="up_done_removing")])
    await edit_or_reply(message, text, InlineKeyboardMarkup(buttons), is_edit=is_edit)

# endregion

# region --- Admin: Details Collection ---

async def start_details_collection(client: Client, message: Message, session: AdminSession):
    processed_names = [name for name in session.names_to_process if name not in session.unavailable_list]
    if not processed_names:
        summary = "Upload process finished."
        if session.unavailable_list: summary += f"\n\n❌ **Unavailable Items:**\n- " + "\n- ".join(session.unavailable_list)
        await message.reply_text(summary)
        session.reset()
        return

    session.names_to_process = processed_names
    session.current_name_index = 0
    await message.reply_text(f"✅ **File verification complete!**\n\nNow, let's collect details for the **{len(processed_names)}** items found.\n\n💡 Send `none` or `unknown` for any detail you don't have.")
    await asyncio.sleep(2)
    await ask_for_next_detail(client, message, session)

async def ask_for_next_detail(client: Client, message: Message, session: AdminSession):
    if session.current_name_index >= len(session.names_to_process):
        await finalize_upload(client, message, session)
        return

    item_name = session.names_to_process[session.current_name_index]
    session.current_details_item = item_name

    if item_name not in session.details_buffer:
        session.details_buffer[item_name] = {}
        session.current_field_index = 0
        base_fields = ["Proper Name", "Year", "Language", "Genre", "Actors", "Poster URL", "Description"]
        session.required_fields = base_fields + ["Director"] if session.content_type == "movie" else base_fields + ["Seasons", "Episodes"]

    if session.current_field_index >= len(session.required_fields):
        session.current_name_index += 1
        await ask_for_next_detail(client, message, session)
        return
        
    session.step = 'awaiting_details'
    current_field = session.required_fields[session.current_field_index]
    prompt = f"**📊 Collecting Details for: `{item_name}`** ({session.current_name_index + 1}/{len(session.names_to_process)})\n\n➡️ **Please provide the `{current_field}`:**"
    await message.reply_text(prompt)

async def process_details_input(client: Client, message: Message, session: AdminSession):
    value = message.text.strip()
    if value.lower() in ['none', 'unknown', 'na', 'n/a']: value = None
    item_name = session.current_details_item
    field_name = session.required_fields[session.current_field_index]
    session.details_buffer[item_name][field_name] = value
    session.current_field_index += 1
    await ask_for_next_detail(client, message, session)

# endregion

# region --- Admin: Finalization and Blogger Post ---

async def finalize_upload(client: Client, message: Message, session: AdminSession):
    await message.reply_text("✅ All details collected. Finalizing upload, please wait...")
    session.step = 'finalizing'
    successful_uploads, failed_uploads = 0, []

    for item_name, details in session.details_buffer.items():
        try:
            search_data = session.search_results[item_name]
            final_media_files = [file for i, file in enumerate(search_data["results"]) if i not in search_data["removed_indices"]]
            if not final_media_files:
                failed_uploads.append(f"{item_name} (No media files selected)")
                continue

            is_dubbed = "dub" in (details.get("Language", "") or "").lower()
            doc = {
                "name": details.get("Proper Name", item_name),
                "year": int(details["Year"]) if (details.get("Year") or "").isdigit() else None,
                "language": details.get("Language", "Kannada"),
                "genre": details.get("Genre"),
                "actors": [a.strip() for a in details["Actors"].split(",")] if details.get("Actors") else [],
                "poster_url": details.get("Poster URL"),
                "description": details.get("Description"),
                "is_dubbed": is_dubbed,
                "media_files": [{**f, "msg_id": str(uuid.uuid4())} for f in final_media_files],
                "created_at": datetime.utcnow(),
                "view_count": 0, "download_count": 0, "rating": 0, "total_ratings": 0
            }
            if session.content_type == "movie":
                doc["director"] = details.get("Director")
            else:
                doc["total_seasons"] = int(details["Seasons"]) if (details.get("Seasons") or "").isdigit() else 1
                doc["total_episodes"] = int(details["Episodes"]) if (details.get("Episodes") or "").isdigit() else 1
            
            collection = get_collection_by_type(session.content_type)
            collection.update_one({"name": doc["name"], "year": doc["year"]}, {"$set": doc}, upsert=True)
            
            if BLOGGER_API_KEY and BLOGGER_BLOG_ID:
                if not await Blogger.post(doc): logger.warning(f"Failed to post {doc['name']} to Blogger.")
            
            successful_uploads += 1
        except Exception as e:
            logger.error(f"Failed to process item '{item_name}': {e}", exc_info=True)
            failed_uploads.append(f"{item_name} (Error: {e})")

    summary_text = f"🎉 **Upload Complete!**\n\n✅ **Processed:** {successful_uploads} item(s)\n"
    if failed_uploads: summary_text += f"❌ **Failed:** {len(failed_uploads)} item(s)\n- " + "\n- ".join(failed_uploads) + "\n"
    if session.unavailable_list: summary_text += f"🤷 **Unavailable:** {len(session.unavailable_list)} item(s)\n- " + "\n- ".join(session.unavailable_list)
    await message.reply_text(summary_text)
    session.reset()

# endregion

# --- 4. USER-FACING COMMANDS & CONTENT SERVING ---

# region --- User Commands and Content Serving ---

@app.on_message(filters.command("start") | filters.command("help"))
async def start_command(client: Client, message: Message):
    try:
        if len(message.command) > 1 and message.command[1].startswith("media-"):
            media_id = message.command[1].split("-", 1)[1]
            await serve_file_by_uuid(client, message, media_id)
            return

        welcome_text = (
            f"🎬 **Welcome to the Kannada Entertainment Bot!**\n\n"
            "Use the buttons below or the following commands:\n"
            "- `/search` - Find specific content.\n"
            "- `/latest` - See what's new."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Search Content", callback_data="search_menu")],
            [InlineKeyboardButton("⚡ Latest Movies", callback_data="latest_movie"), InlineKeyboardButton("🔥 Latest Series", callback_data="latest_webseries")]
        ])
        await message.reply_text(welcome_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in start_command: {e}", exc_info=True)
        await message.reply_text("❌ An error occurred.")

async def serve_file_by_uuid(client: Client, message: Message, media_uuid: str):
    try:
        media_data, target_file = None, None
        query = {"media_files.msg_id": media_uuid}
        for collection in [movies_collection, series_collection, shows_collection]:
            media_data = collection.find_one(query)
            if media_data:
                for file_info in media_data.get("media_files", []):
                    if file_info.get("msg_id") == media_uuid:
                        target_file = file_info
                        break
                if target_file:
                    collection.update_one({"_id": media_data["_id"]}, {"$inc": {"download_count": 1}})
                    break
        
        if not target_file:
            await message.reply_text("❌ **File Not Found**\n\nThis link may be old or invalid.")
            return

        caption = (f"**🎬 {media_data.get('name', 'N/A')}**\n"
                   f"**💡 File:** `{target_file.get('file_name', 'N/A')}`\n"
                   f"**✨ Quality:** {target_file.get('quality', 'N/A')}\n"
                   f"**💾 Size:** {target_file.get('size', 'N/A')}")
        await message.reply_text(f"✅ Your download is starting...\n\n{caption}")
        await client.copy_message(chat_id=message.chat.id, from_chat_id=target_file["channel_id"], message_id=target_file["original_msg_id"], caption=f"Downloaded from @{BOT_USERNAME}")
    except Exception as e:
        logger.error(f"Error serving file with UUID {media_uuid}: {e}", exc_info=True)
        await message.reply_text("❌ **Download Failed**\n\nThe file might have been deleted from the source channel.")

# (Placeholder for /search, /latest, and other user features)

# endregion

# --- 5. CALLBACK QUERY HANDLERS ---

# region --- Callback Handlers ---

@app.on_callback_query(admin_filter & filters.regex(r"^up_"))
async def admin_upload_callbacks(client: Client, cb: CallbackQuery):
    try:
        session = get_admin_session(cb.from_user.id)
        data = cb.data
        if data == "up_cancel":
            session.reset()
            await cb.edit_message_text("❌ Upload process cancelled.")
        elif data.startswith("up_nav_"):
            session.current_page += 1 if data.endswith("next") else -1
            await show_verification_results(cb.message, session, is_edit=True)
        elif data == "up_correct":
            session.current_name_index += 1
            await cb.message.delete()
            await search_next_name(client, cb.message, session)
        elif data == "up_wrong":
            await show_removal_options(cb.message, session, is_edit=True)
        elif data.startswith("up_remove_"):
            index_to_toggle = int(data.split("_")[-1])
            current_name = session.names_to_process[session.current_name_index]
            removed_set = session.search_results[current_name]["removed_indices"]
            if index_to_toggle in removed_set: removed_set.remove(index_to_toggle)
            else: removed_set.add(index_to_toggle)
            await show_removal_options(cb.message, session, is_edit=True)
        elif data == "up_done_removing":
            await show_verification_results(cb.message, session, is_edit=True)
        await cb.answer()
    except Exception as e:
        logger.error(f"Error in admin_upload_callbacks (data: {cb.data}): {e}", exc_info=True)
        await cb.answer("An error occurred.", show_alert=True)
# endregion

# --- 6. BLOGGER INTEGRATION ---

# region --- Blogger API and Content Generation ---
class Blogger:
    BASE_URL = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}"

    @staticmethod
    async def post(content: Dict[str, Any]) -> bool:
        if not all([BLOGGER_API_KEY, BLOGGER_BLOG_ID]):
            logger.warning("Blogger API Key/Blog ID not set. Skipping blog post.")
            return False
        try:
            title, html_content, labels = Blogger._generate_post_content(content)
            post_data = {"kind": "blogger#post", "title": title, "content": html_content, "labels": labels}
            async with aiohttp.ClientSession() as session:
                url = f"{Blogger.BASE_URL}/posts?key={BLOGGER_API_KEY}"
                headers = {"Content-Type": "application/json"}
                async with session.post(url, json=post_data, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"Successfully posted '{title}' to Blogger.")
                        return True
                    else:
                        logger.error(f"Failed to create blog post. Status: {response.status}, Error: {await response.text()}")
                        return False
        except Exception as e:
            logger.error(f"An error occurred during Blogger post: {e}", exc_info=True)
            return False

    @staticmethod
    def _generate_post_content(content: Dict[str, Any]) -> (str, str, List[str]):
        name, year, lang = content.get("name", "N/A"), content.get("year", ""), content.get("language", "Kannada")
        title = f"{name} ({year}) {lang} Full Movie Download"
        labels = ["Kannada Entertainment", lang, str(year)]
        if content.get("genre"): labels.extend([g.strip() for g in content["genre"].split(",")])
        if content.get("actors"): labels.extend(content["actors"][:3])
        if content.get("is_dubbed"): labels.append("Dubbed")
        
        download_buttons_html = ""
        for file in content.get("media_files", []):
            bot_link = f"https://t.me/{BOT_USERNAME}?start=media-{file['msg_id']}"
            download_buttons_html += f'<a href="{bot_link}" target="_blank" class="download-button"><div class="quality">{file.get("quality", "HD")}</div><div class="size">{file.get("size", "N/A")}</div></a>'
        
        html_content = f"""
<style>.post-container{{max-width:700px;margin:auto;font-family:sans-serif}}.poster{{width:100%;border-radius:8px;margin-bottom:15px}}.details-table{{width:100%;border-collapse:collapse;margin-bottom:20px}}.details-table td{{padding:8px;border-bottom:1px solid #ddd}}.details-table td:first-child{{font-weight:bold;width:30%}}.download-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-top:10px}}.download-button{{background-color:#0088cc;color:white;padding:10px;text-align:center;border-radius:5px;text-decoration:none;font-weight:bold}}.download-button .quality{{font-size:1.1em}}.download-button .size{{font-size:0.8em;opacity:0.8}}</style>
<div class="post-container">
<img src="{content.get('poster_url', '')}" alt="{name} Poster" class="poster"><h2>{name} ({year}) - {lang}</h2><p>{content.get('description', '')}</p>
<h3>Movie Details:</h3>
<table class="details-table">
<tr><td>Genre</td><td>{content.get('genre', 'N/A')}</td></tr>
<tr><td>Actors</td><td>{', '.join(content.get('actors', []))}</td></tr>
{f"<tr><td>Director</td><td>{content.get('director', 'N/A')}</td></tr>" if 'director' in content else ""}
</table><h3>Download Links:</h3><div class="download-grid">{download_buttons_html}</div></div>"""
        return title, html_content, list(set(labels))
# endregion

# --- 7. FLASK WEB SERVER & BOT EXECUTION ---
flask_app = Flask(__name__)

@flask_app.route('/health')
def health_check():
    """Health check endpoint for Koyeb to ping."""
    return jsonify({"status": "healthy", "bot": BOT_USERNAME}), 200

def run_flask():
    """Runs the Flask web server in a separate thread."""
    flask_app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == "__main__":
    logger.info("Bot is starting...")
    try:
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info(f"Flask health check server started on port {PORT}")
        app.run()
        logger.info("Bot stopped.")
    except Exception as e:
        logger.critical(f"❌ Bot crashed with a critical error: {e}", exc_info=True)
