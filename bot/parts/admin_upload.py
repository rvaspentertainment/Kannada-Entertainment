# bot/parts/admin_upload.py

import logging
import re
from typing import List
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified

# FIX: Added the missing import for Config
from config import Config
from .core_bot_functionality import get_user_session, format_file_size

logger = logging.getLogger(__name__)

# --- Helper: Extract Quality ---
def extract_quality(text: str) -> str:
    """Extracts video quality from text (filename or caption)."""
    text = text.lower()
    qualities = {
        "4K": ["4k", "2160p", "uhd"],
        "1080P": ["1080p", "fhd"],
        "720P": ["720p", "hd"],
        "480P": ["480p", "sd"],
        "360P": ["360p"],
    }
    for quality, patterns in qualities.items():
        if any(p in text for p in patterns):
            return quality
    return "UNKNOWN"


# --- Command: /up ---
@Client.on_message(filters.command("up") & filters.user(Config.ADMIN_IDS) & filters.private)
async def upload_command(client: Client, message: Message):
    """Initiates the content upload process for admins."""
    try:
        user_id = message.from_user.id
        session = get_user_session(user_id)
        session.reset_data() # Start a fresh session

        welcome_text = "📤 **Upload Content**\n\nPlease select the type of content you want to upload:"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Movie", callback_data="up_movies")],
            [InlineKeyboardButton("📺 Web Series", callback_data="up_webseries")],
            [InlineKeyboardButton("📻 TV Series", callback_data="up_tvseries")],
            [InlineKeyboardButton("🎭 Show", callback_data="up_shows")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")]
        ])
        await message.reply_text(welcome_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in upload_command: {e}")
        await message.reply_text("❌ An error occurred while starting the upload process.")


# --- Step 1: Handle Content Type Selection ---
@Client.on_callback_query(filters.regex(r"^up_") & filters.user(Config.ADMIN_IDS))
async def handle_upload_type(client: Client, callback_query: CallbackQuery):
    """Handles the admin's choice of entertainment type."""
    try:
        user_id = callback_query.from_user.id
        session = get_user_session(user_id)
        session.entertainment_type = callback_query.data.split("_", 1)[1]
        session.current_step = "waiting_for_names"

        type_map = {
            "movies": "Movie(s)", "webseries": "Web Series",
            "tvseries": "TV Series", "shows": "Show(s)"
        }
        ent_type_str = type_map.get(session.entertainment_type, "Content")

        prompt_text = (
            f"✅ **Type Selected:** {ent_type_str}\n\n"
            "📝 Now, send me the name(s) of the content you wish to upload.\n\n"
            "**Formatting Guide:**\n"
            "- For a single item: `KGF Chapter 2`\n"
            "- For multiple items, separate them with a comma: `Kantara, RRR, Vikrant Rona`"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")]])
        await callback_query.message.edit_text(prompt_text, reply_markup=keyboard)
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in handle_upload_type: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)


# --- Step 2: Handle Name Input ---
@Client.on_message(filters.text & filters.user(Config.ADMIN_IDS) & filters.private)
async def handle_name_input(client: Client, message: Message):
    """Handles the text message containing the names to be processed."""
    user_id = message.from_user.id
    session = get_user_session(user_id)

    # Ensure this handler only runs when the bot is expecting names
    if session.current_step != "waiting_for_names":
        # Check for other steps that might handle text input
        if session.current_step == "collecting_details":
            from .details_collection import handle_detail_input
            await handle_detail_input(client, message)
        return

    try:
        names_input = message.text.strip()
        names = [name.strip() for name in names_input.split(",") if name.strip()]

        if not names:
            await message.reply_text("⚠️ Please provide at least one valid name. Send the names again.")
            return

        session.names_to_process = names
        session.current_name_index = 0
        session.current_step = "processing_names"

        await message.reply_text(
            f"✅ **Names Received:** {len(names)}\n"
            f"**Names:** `{', '.join(names)}`\n\n"
            "🔍 Starting search process..."
        )
        # Start processing the first name
        await process_next_name(client, message, user_id)
    except Exception as e:
        logger.error(f"Error in handle_name_input: {e}")
        await message.reply_text("❌ An error occurred while processing the names.")


# --- Step 3: Search and Display Results (Looping) ---
async def process_next_name(client: Client, message: Message, user_id: int):
    """Processes the next name in the list, searches channels, and shows results."""
    session = get_user_session(user_id)
    
    # If all names are processed, move to the details collection step
    if session.current_name_index >= len(session.names_to_process):
        from .details_collection import ask_for_details # Avoid circular import
        await ask_for_details(client, message, user_id)
        return

    current_name = session.names_to_process[session.current_name_index]
    progress_msg = await client.send_message(
        chat_id=user_id,
        text=(
            f"🔄 **Processing Item {session.current_name_index + 1}/{len(session.names_to_process)}**\n"
            f"**Searching for:** `{current_name}`\n\n"
            "⏳ Please wait..."
        )
    )

    try:
        # Search in channels
        search_results = await search_in_channels(client, current_name)

        if not search_results:
            session.unavailable_list.append(current_name)
            await progress_msg.edit_text(
                f"❌ **No results found for:** `{current_name}`\n"
                "This item has been added to the unavailable list.\n\n"
                "⏭️ Moving to the next item..."
            )
            session.current_name_index += 1
            await process_next_name(client, message, user_id)
            return

        # Store results and reset pagination for the new item
        session.search_results[current_name] = search_results
        session.current_page = 0
        session.total_pages = (len(search_results) - 1) // 10 + 1
        
        # All search results are considered 'selected' by default
        session.selected_media[current_name] = list(range(len(search_results)))

        await show_search_results(client, progress_msg, user_id, current_name)

    except Exception as e:
        logger.error(f"Error in process_next_name for '{current_name}': {e}")
        await progress_msg.edit_text(f"❌ An error occurred while processing `{current_name}`. Moving to next.")
        session.current_name_index += 1
        await process_next_name(client, message, user_id)


async def search_in_channels(client: Client, search_term: str) -> List[dict]:
    """Searches for a term across all configured admin channels."""
    results = []
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)

    for channel_id in Config.CHANNEL_IDS:
        try:
            async for msg in client.search_messages(chat_id=channel_id, query=search_term, limit=50):
                if msg.video or msg.document:
                    file_name = getattr(msg.video or msg.document, 'file_name', '') or ""
                    caption = msg.caption or ""
                    
                    if pattern.search(file_name) or pattern.search(caption):
                        file_size_bytes = getattr(msg.video or msg.document, 'file_size', 0)
                        
                        results.append({
                            "message_id": msg.id,
                            "channel_id": channel_id,
                            "caption": caption,
                            "file_name": file_name,
                            "size_bytes": file_size_bytes,
                            "size_str": format_file_size(file_size_bytes),
                            "quality": extract_quality(file_name + " " + caption),
                            "file_type": "video" if msg.video else "document",
                            "link": msg.link
                        })
        except Exception as e:
            logger.error(f"Could not search in channel {channel_id}: {e}")
    return results


async def show_search_results(client: Client, message: Message, user_id: int, current_name: str):
    """Displays paginated search results to the admin for confirmation."""
    session = get_user_session(user_id)
    results = session.search_results.get(current_name, [])
    selected_indices = session.selected_media.get(current_name, [])
    
    if not results:
        await message.edit_text(f"No results found for `{current_name}`.")
        return

    start_idx = session.current_page * 10
    end_idx = start_idx + 10
    page_results = results[start_idx:end_idx]

    text = f"🔍 **Search Results for:** `{current_name}`\n"
    text += f"📄 **Page {session.current_page + 1}/{session.total_pages}** | ✅ **{len(selected_indices)} files selected**\n\n"

    for i, result in enumerate(page_results, start=start_idx):
        status_icon = "✅" if i in selected_indices else "❌"
        display_name = result["file_name"] if result["file_name"] else "No Filename"
        text += (
            f"**{i+1}.** {status_icon} `{display_name[:50]}`\n"
            f"   - Quality: {result['quality']} | Size: {result['size_str']}\n"
        )
    
    text += "\nAre these the correct files for this item?"

    buttons = []
    nav_buttons = []
    if session.current_page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_page_{current_name}"))
    if session.current_page < session.total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"next_page_{current_name}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([
        InlineKeyboardButton("✅ Correct", callback_data=f"correct_{current_name}"),
        InlineKeyboardButton("❌ Wrong Files", callback_data=f"wrong_{current_name}")
    ])
    
    try:
        await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f"Error in show_search_results: {e}")
        await client.send_message(user_id, text, reply_markup=InlineKeyboardMarkup(buttons))


# --- Step 4: Handle Admin Actions (Correct, Wrong, Pagination) ---
@Client.on_callback_query(filters.regex(r"^(correct_|wrong_|prev_page_|next_page_)") & filters.user(Config.ADMIN_IDS))
async def handle_search_action(client: Client, callback_query: CallbackQuery):
    """Handles admin's selection for the search results."""
    user_id = callback_query.from_user.id
    session = get_user_session(user_id)
    data = callback_query.data
    
    try:
        action, name = data.split("_", 1)

        if action == "correct":
            await callback_query.answer("✅ Correct! Moving to the next item...")
            session.current_name_index += 1
            await process_next_name(client, callback_query.message, user_id)

        elif action == "wrong":
            await callback_query.answer("Select files to remove.")
            await show_removal_options(client, callback_query.message, user_id, name)

        elif action in ["prev_page", "next_page"]:
            session.current_page += -1 if action == "prev_page" else 1
            await show_search_results(client, callback_query.message, user_id, name)
            await callback_query.answer()

    except Exception as e:
        logger.error(f"Error in handle_search_action: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)


# --- Step 4a: File Removal Flow ---
async def show_removal_options(client: Client, message: Message, user_id: int, current_name: str):
    """Shows a grid of file numbers for the admin to deselect."""
    session = get_user_session(user_id)
    results = session.search_results.get(current_name, [])
    selected_indices = session.selected_media.get(current_name, [])
    
    start_idx = session.current_page * 10
    end_idx = min(start_idx + 10, len(results))

    text = (
        f"❌ **Modify Selection for:** `{current_name}`\n"
        f"📄 **Page {session.current_page + 1}/{session.total_pages}**\n\n"
        "Click on a number to toggle its selection (✅/❌)."
    )
    
    buttons = []
    row = []
    for i in range(start_idx, end_idx):
        status_icon = "✅" if i in selected_indices else "❌"
        row.append(InlineKeyboardButton(f"{i+1} {status_icon}", callback_data=f"remove_{current_name}_{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    nav_buttons = []
    if session.current_page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"nav_remove_{current_name}_prev"))
    nav_buttons.append(InlineKeyboardButton("✅ Done", callback_data=f"done_remove_{current_name}"))
    if session.current_page < session.total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"nav_remove_{current_name}_next"))
    
    buttons.append(nav_buttons)
    
    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex(r"^(remove_|done_remove_|nav_remove_)") & filters.user(Config.ADMIN_IDS))
async def handle_removal_action(client: Client, callback_query: CallbackQuery):
    """Handles toggling file selections, navigating, or finishing removal."""
    user_id = callback_query.from_user.id
    session = get_user_session(user_id)
    data = callback_query.data
    
    try:
        parts = data.split("_")
        action = parts[0]
        
        if action == "remove":
            name, index_str = parts[1], parts[2]
            index = int(index_str)
            selected_indices = session.selected_media.get(name, [])
            if index in selected_indices:
                selected_indices.remove(index)
                await callback_query.answer(f"File #{index+1} removed.")
            else:
                selected_indices.append(index)
                await callback_query.answer(f"File #{index+1} added back.")
            
            session.selected_media[name] = sorted(selected_indices)
            await show_removal_options(client, callback_query.message, user_id, name)

        elif action == "nav_remove":
            name, direction = parts[1], parts[2]
            session.current_page += -1 if direction == "prev" else 1
            await show_removal_options(client, callback_query.message, user_id, name)
            await callback_query.answer()

        elif action == "done_remove":
            name = parts[1]
            await callback_query.answer("Selection updated.")
            await show_search_results(client, callback_query.message, user_id, name)
            
    except Exception as e:
        logger.error(f"Error in handle_removal_action: {e}")
        await callback_query.answer("❌ An error occurred.", show_alert=True)
        

# --- General Cancel Action ---
@Client.on_callback_query(filters.regex("^cancel_upload") & filters.user(Config.ADMIN_IDS))
async def cancel_upload(client: Client, callback_query: CallbackQuery):
    """Cancels the entire upload process and resets the session."""
    user_id = callback_query.from_user.id
    session = get_user_session(user_id)
    session.reset_data()
    await callback_query.message.edit_text("❌ **Upload process has been cancelled.**")
    await callback_query.answer("Cancelled.")
