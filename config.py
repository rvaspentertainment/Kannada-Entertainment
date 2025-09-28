import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Kannada Entertainment Bot"""
    
    # Telegram Bot Configuration
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Admin and Channel Configuration
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    CHANNEL_IDS = [int(x) for x in os.getenv("CHANNEL_IDS", "").split(",") if x.strip()]
    
    # Database Configuration
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "kannada_entertainment")
    
    # Blogger Configuration
    BLOGGER_API_KEY = os.getenv("BLOGGER_API_KEY", "")
    BLOGGER_BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "")
    BLOG_URL = os.getenv("BLOG_URL", "")
    
    # Bot Configuration
    BOT_USERNAME = os.getenv("BOT_USERNAME", "").replace("@", "")
    
    # Server Configuration
    PORT = int(os.getenv("PORT", 8080))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # Advanced Settings
    MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", 50))
    ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", 10))
    MAX_FILE_SIZE_GB = float(os.getenv("MAX_FILE_SIZE_GB", 4.0))
    
    # Supported file formats
    SUPPORTED_FORMATS = ['.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm']
    
    # Cache Settings
    CACHE_DURATION_HOURS = int(os.getenv("CACHE_DURATION_HOURS", 24))
    MAX_CACHE_SIZE_MB = int(os.getenv("MAX_CACHE_SIZE_MB", 100))
    
    # Rate Limiting
    RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", 30))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate required configuration and return missing items"""
        required_fields = [
            "API_ID", "API_HASH", "BOT_TOKEN"
        ]
        
        missing = []
        for field in required_fields:
            value = getattr(cls, field)
            if not value or (isinstance(value, str) and value.strip() == ""):
                missing.append(field)
        
        return missing
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in cls.ADMIN_IDS
    
    @classmethod
    def get_mongo_uri(cls) -> str:
        """Get MongoDB URI with database name"""
        if cls.MONGO_URL.endswith('/'):
            return f"{cls.MONGO_URL}{cls.DATABASE_NAME}"
        return f"{cls.MONGO_URL}/{cls.DATABASE_NAME}"
