# bot/parts/user_features.py

import logging
from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto
)
from bson import ObjectId

from config import Config
from .core_bot_functionality import (
    movies_collection, series_collection, shows_collection, get_collection_by_type
)

logger = logging.getLogger(__name__)

# --- /search Command ---
@Client.on_message(filters.command("search") & filters.private)
@Client.on_callback_query(filters.regex("^search_content$"))
async def search_command(client: Client, update: Message | CallbackQuery):
    """Presents the main search menu to the user."""
    text = "🔍 **Search for Content**\n\nHow would you like to find your entertainment?"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔤 By Name", callback_data="search_name")],
        [
            InlineKeyboardButton("🎭 By Genre", callback_data="search_genre"),
            InlineKeyboardButton("👥 By Actor", callback_data="search_actor")
        ],
        [
            InlineKeyboardButton("📅 By Year", callback_data="search_year"),
            InlineKeyboardButton("🗣️ Dubbed Only", callback_data="search_dubbed")
        ],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main")]
    ])
    
    if isinstance(update, Message):
        await update.reply_text(text, reply_markup=keyboard)
    else:
        await update.message.edit_text(text, reply_markup=keyboard)
        await update.answer()

# --- Content Display ---
async def show_content_details(client: Client, callback_query: CallbackQuery, content_id_str: str):
    """Displays the full details of a selected movie or series."""
    try:
        content_id = ObjectId(content_id_str)
        content = None
        
        # Search all collections for the content
        for collection in [movies_collection, series_collection, shows_collection]:
            content = collection.find_one({"_id": content_id})
            if content:
                break
        
        if not content:
            await callback_query.answer("❌ Content not found. It might have been removed.", show_alert=True)
            return

        # --- Format Details ---
        title = content.get('name', 'N/A')
        year = content.get('year', 'N/A')
        lang = content.get('language', 'N/A')
        genre = ", ".join(content.get('genre', []))
        actors = ", ".join(content.get('actors', [])[:3])
        description = content.get('description', 'No description available.')

        caption = f"🎬 **{title}** ({year})\n\n"
        caption += f"🗣️ **Language:** {lang}\n"
        caption += f"🎭 **Genre:** {genre}\n"
        caption += f"👥 **Cast:** {actors}...\n\n"
        caption += f"📖 **Plot:** {description[:200]}...\n\n"

        buttons = []
        # --- Download Buttons ---
        if content.get('media_files'): # For Movies
            caption += "💾 **Available Downloads:**\n"
            for media in content['media_files']:
                buttons.append([
                    InlineKeyboardButton(
                        f"📥 {media['quality']} ({media['size']})",
                        url=f"https://t.me/{Config.BOT_USERNAME}?start=media-{media['msg_id']}"
                    )
                ])
        elif content.get('seasons_data'): # For Series/Shows
            caption += "📺 **Select a Season to View Episodes:**\n"
            # In a real scenario, this would lead to another callback to show episodes.
            # For simplicity, we can show the first season's first episode as an example.
            # A full implementation would create buttons for each season.
            buttons.append([InlineKeyboardButton("➡️ View Seasons & Episodes", callback_data=f"view_seasons_{content_id_str}")])

        buttons.append([InlineKeyboardButton("⬅️ Back to Search", callback_data="search_content")])
        keyboard = InlineKeyboardMarkup(buttons)
        
        poster_url = content.get("poster_url")
        try:
            if poster_url:
                await callback_query.message.reply_photo(
                    photo=poster_url,
                    caption=caption,
                    reply_markup=keyboard
                )
                await callback_query.message.delete() # clean up previous message
            else:
                await callback_query.message.edit_text(caption, reply_markup=keyboard)
        except Exception as e:
            logger.warning(f"Could not send poster for {title}, sending text instead. Error: {e}")
            await callback_query.message.edit_text(caption, reply_markup=keyboard)

        await callback_query.answer()

    except Exception as e:
        logger.error(f"Error in show_content_details: {e}", exc_info=True)
        await callback_query.answer("❌ An error occurred while fetching details.", show_alert=True)

# --- Media Serving ---
async def handle_media_request(client: Client, message: Message):
    """Handles deep links to serve media files to users."""
    try:
        media_id = message.command[1].replace("media-", "")
        
        target_file = None
        # Find the media file across all collections
        for collection in [movies_collection, series_collection, shows_collection]:
            result = collection.find_one({"media_files.msg_id": media_id})
            if result:
                for f in result["media_files"]:
                    if f["msg_id"] == media_id:
                        target_file = f
                        break
                if target_file:
                    break
        
        if not target_file:
            await message.reply_text("❌ Media not found or the link has expired. Please search for the content again.")
            return

        await message.reply_text(f"✅ **File Found!**\n\n**Name:** `{target_file['file_name']}`\n**Size:** `{target_file['size']}`\n\n⬇️ Your download will start shortly...")

        try:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=target_file["channel_id"],
                message_id=target_file["original_msg_id"]
            )
        except Exception as e:
            logger.error(f"Failed to forward media {media_id}: {e}")
            await message.reply_text("❌ Failed to send the file. It might have been removed from the source channel. Please try another quality or contact an admin.")

    except Exception as e:
        logger.error(f"Error in handle_media_request: {e}")
        await message.reply_text("❌ An error occurred while processing your request.")

# Placeholder for a content view callback handler
@Client.on_callback_query(filters.regex(r"^view_content_"))
async def view_content_callback(client: Client, callback_query: CallbackQuery):
    content_id = callback_query.data.split("_", 2)[2]
    await show_content_details(client, callback_query, content_id)

# Placeholder for back to main menu
@Client.on_callback_query(filters.regex("^back_to_main$"))
async def back_to_main_callback(client: Client, callback_query: CallbackQuery):
    # This re-uses the /start command's logic
    from .core_bot_functionality import start_command
    # We need to simulate a Message object
    await start_command(client, callback_query.message)
    await callback_query.message.delete()
    await callback_query.answer()
