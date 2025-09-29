import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

def register_handlers(bot: Client):
    """Register bot handlers"""
    
    @bot.on_message(filters.command("start"))
    async def start_command(client: Client, message: Message):
        logger.info(f"Start command from user {message.from_user.id}")
        
        welcome_text = """
🎬 **Welcome to Kannada Entertainment Bot** 🎬

Available Commands:
• /start - Show this message
• /help - Get help

Choose an option:
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Search", callback_data="search")],
            [InlineKeyboardButton("📺 Latest", callback_data="latest")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ])
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
    
    @bot.on_message(filters.command("help"))
    async def help_command(client: Client, message: Message):
        await message.reply_text("ℹ️ Help: Use /start to begin")
    
    logger.info("✅ Handlers registered")
