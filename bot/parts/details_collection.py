# bot/parts/details_collection.py

import logging
import uuid
from typing import List, Dict
from datetime import datetime
import re

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# The missing import is added here
from config import Config
from .core_bot_functionality import get_user_session, get_collection_by_type

logger = logging.getLogger(__name__)

# A temporary dictionary to hold media while waiting for admin quality selection
temp_media_for_quality_check = {}

# --- Step 5: Start Details Collection ---
async def ask_for_details(client: Client, message: Message, user_id: int):
    """Initiates the process of collecting details for the processed items."""
    session = get_user_session(user_id)
    session.current_step = "collecting_details"
    
    processed_names = [name for i, name in enumerate(session.names_to_process) if session.selected_media.get(name)]

    if not processed_names:
        summary_text = "✅ **Search Process Completed!**\n\nNo items with selected files were found."
        if session.unavailable_list:
            summary_text += f"\n\n**Unavailable Items:**\n`{', '.join(session.unavailable_list)}`"
        await client.send_message(user_id, summary_text)
        session.reset_data()
        return

    summary_text = (
        f"✅ **Search Process Completed!**\n\n"
        f"Now collecting details for the **{len(processed_names)}** item(s) you confirmed.\n\n"
        "💡 **Tip:** If you don't know a detail, just send `none`, `skip`, or `unknown`."
    )
    await client.send_message(user_id, summary_text)

    # Reset detail indices and start with the first item
    session.current_detail_index = 0
    session.current_field_index = 0
    await collect_next_detail(client, message, user_id)


async def collect_next_detail(client: Client, message: Message, user_id: int):
    """Asks the admin for the next piece of information required."""
    session = get_user_session(user_id)
    
    processed_names = [name for i, name in enumerate(session.names_to_process) if session.selected_media.get(name)]

    # Check if we are done with all items
    if session.current_detail_index >= len(processed_names):
        await finalize_upload(client, message, user_id)
        return

    current_item_name = processed_names[session.current_detail_index]
    ent_type = session.entertainment_type

    # Define fields based on entertainment type
    base_fields = ["name", "year", "language", "genre", "actors", "poster_link", "description"]
    if ent_type == "movies":
        fields = base_fields + ["director"]
    else: # Series, Shows
        fields = base_fields + ["seasons", "episodes"]
    
    # Check if we are done with all fields for the current item
    if session.current_field_index >= len(fields):
        session.current_detail_index += 1
        session.current_field_index = 0
        await collect_next_detail(client, message, user_id) # Move to next item
        return

    current_field = fields[session.current_field_index]
    
    prompts = {
        "name": f"📝 **Full Name** (default: `{current_item_name}`):",
        "year": "📅 **Release Year** (e.g., `2023`):",
        "language": "🗣️ **Language(s)** (e.g., `Kannada`, `Kannada Dub`):",
        "genre": "🎭 **Genre(s)** (comma-separated, e.g., `Action, Thriller`):",
        "actors": "👥 **Main Actors** (comma-separated):",
        "poster_link": "🖼️ **Poster URL** (direct link to an image):",
        "description": "📖 **Plot/Description**:",
        "director": "🎬 **Director's Name**:",
        "seasons": "📺 **Total Seasons**:",
        "episodes": "📋 **Total Episodes**:",
    }

    progress_text = f"📊 **Collecting Details for:** `{current_item_name}` ({session.current_detail_index + 1}/{len(processed_names)})\n\n"
    prompt_text = prompts.get(current_field, f"Enter {current_field.replace('_', ' ')}:")
    
    await client.send_message(user_id, progress_text + prompt_text)

# --- Step 6: Handle Detail Input ---
@Client.on_message(filters.text & filters.user(Config.ADMIN_IDS) & filters.private)
async def handle_detail_input(client: Client, message: Message):
    """Handles the admin's text responses for each detail."""
    user_id = message.from_user.id
    session = get_user_session(user_id)

    if session.current_step != "collecting_details":
        return

    try:
        value = message.text.strip()
        if value.lower() in ["none", "skip", "unknown", "n/a"]:
            value = None # Use None to represent unknown values

        # --- Get current context ---
        processed_names = [name for i, name in enumerate(session.names_to_process) if session.selected_media.get(name)]
        current_item_name = processed_names[session.current_detail_index]
        ent_type = session.entertainment_type
        
        base_fields = ["name", "year", "language", "genre", "actors", "poster_link", "description"]
        fields = base_fields + (["director"] if ent_type == "movies" else ["seasons", "episodes"])
        current_field = fields[session.current_field_index]

        # Initialize details dict for the item if it doesn't exist
        if current_item_name not in session.details:
            session.details[current_item_name] = {"original_search_name": current_item_name}

        # Store the value
        session.details[current_item_name][current_field] = value
        
        # Move to the next field
        session.current_field_index += 1
        await collect_next_detail(client, message, user_id)

    except Exception as e:
        logger.error(f"Error in handle_detail_input: {e}")
        await message.reply_text("❌ An error occurred. Please try providing the detail again.")

# --- Step 7: Finalize and Save to DB ---
async def finalize_upload(client: Client, message: Message, user_id: int):
    """Processes all collected data, saves to the database, and reports back."""
    session = get_user_session(user_id)
    progress_msg = await client.send_message(user_id, "⏳ **Finalizing...**\nProcessing all data and saving to the database. Please wait.")
    
    saved_count = 0
    error_count = 0

    try:
        # Loop through all the details we collected
        for item_name, details in session.details.items():
            try:
                collection = get_collection_by_type(session.entertainment_type)
                
                # Prepare media files, checking for quality
                media_files_raw = [session.search_results[item_name][i] for i in session.selected_media[item_name]]
                processed_media_files = []

                for media in media_files_raw:
                    unique_id = str(uuid.uuid4())
                    
                    if media["quality"] == "UNKNOWN":
                        logger.warning(f"Quality for '{media['file_name']}' is UNKNOWN. Defaulting to 'HD'.")
                        media["quality"] = "HD"

                    # For series, extract season/episode info
                    season, episode = 1, 1
                    if session.entertainment_type != "movies":
                        season, episode = extract_season_episode(media["file_name"] + media["caption"])

                    processed_media_files.append({
                        "msg_id": unique_id,
                        "original_msg_id": media["message_id"],
                        "channel_id": media["channel_id"],
                        "file_name": media["file_name"],
                        "caption": media["caption"],
                        "quality": media["quality"],
                        "size": media["size_str"],
                        "telegram_link": media["link"],
                        "season": season,
                        "episode": episode
                    })

                # --- Construct the database document ---
                doc = {
                    "name": details.get("name") or item_name,
                    "year": int(details["year"]) if details.get("year", "").isdigit() else None,
                    "language": details.get("language"),
                    "is_dubbed": "dub" in (details.get("language") or "").lower(),
                    "genre": [g.strip() for g in details.get("genre", "").split(",")] if details.get("genre") else [],
                    "actors": [a.strip() for a in details.get("actors", "").split(",")] if details.get("actors") else [],
                    "poster_url": details.get("poster_link"),
                    "description": details.get("description"),
                    "media_files": processed_media_files,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }

                if session.entertainment_type == "movies":
                    doc["director"] = details.get("director")
                else:
                    doc["total_seasons"] = int(details.get("seasons")) if details.get("seasons", "").isdigit() else None
                    doc["total_episodes"] = int(details.get("episodes")) if details.get("episodes", "").isdigit() else None
                    doc["seasons_data"] = organize_episodes_by_season(processed_media_files)

                # Insert or update in the database
                collection.update_one(
                    {"name": doc["name"], "year": doc["year"]},
                    {"$set": doc},
                    upsert=True
                )
                saved_count += 1
                
                # --- Trigger Blogger Update ---
                from .blogger_integration import update_blogger_site
                await update_blogger_site(client, message, doc, session.entertainment_type)

            except Exception as item_error:
                logger.error(f"Error saving item '{item_name}': {item_error}")
                error_count += 1

        # --- Final Report ---
        completion_text = f"✅ **Upload Process Completed!**\n\n"
        completion_text += f"💾 **Saved to Database:** {saved_count} items\n"
        if error_count > 0:
            completion_text += f"❌ **Errors:** {error_count} items failed to save.\n"
        if session.unavailable_list:
            completion_text += f"❓ **Unavailable Items:** {len(session.unavailable_list)}\n"
            completion_text += f"`{', '.join(session.unavailable_list)}`"

        await progress_msg.edit_text(completion_text)

    except Exception as e:
        logger.error(f"Critical error in finalize_upload: {e}")
        await progress_msg.edit_text("❌ A critical error occurred during the finalization process. Check logs.")
    finally:
        session.reset_data()

def extract_season_episode(text: str) -> (int, int):
    """Extracts season and episode number from text using regex."""
    text = text.lower()
    match = re.search(r'[sS](\d+)[eE](\d+)', text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 1, 1

def organize_episodes_by_season(media_files: List[Dict]) -> Dict:
    """Organizes a flat list of media files into a nested dictionary by season and episode."""
    seasons = {}
    for media in media_files:
        season_num = media.get("season", 1)
        episode_num = media.get("episode", 1)

        if season_num not in seasons:
            seasons[season_num] = {"episodes": {}}
        
        if episode_num not in seasons[season_num]["episodes"]:
            seasons[season_num]["episodes"][episode_num] = {"files": []}
        
        seasons[season_num]["episodes"][episode_num]["files"].append(media)
    return seasons
