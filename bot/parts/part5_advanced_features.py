import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
import base64
from typing import Dict, List, Optional, Any
import re
from urllib.parse import quote, unquote
import hashlib
import os
from dataclasses import dataclass
from enum import Enum
import logging
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import uuid

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
class Config:
    # Environment variables
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    # Admin Configuration
    ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
    CHANNEL_IDS = [int(x) for x in os.environ.get("CHANNEL_IDS", "").split(",") if x.strip()]
    
    # Database Configuration
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "kannada_entertainment")
    
    # Blogger Configuration
    BLOGGER_API_KEY = os.environ.get("BLOGGER_API_KEY", "")
    BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")
    BLOG_URL = os.environ.get("BLOG_URL", "")
    
    # Bot Configuration
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
    
    # Advanced Settings
    MAX_SEARCH_RESULTS = 50
    ITEMS_PER_PAGE = 10
    MAX_FILE_SIZE_GB = 4.0
    SUPPORTED_FORMATS = ['.mp4', '.mkv', '.avi', '.mov', '.m4v']
    
    # Cache Settings
    CACHE_DURATION_HOURS = 24
    MAX_CACHE_SIZE_MB = 100
# Initialize MongoDB connection
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DATABASE_NAME]

# Collections
movies_collection = db.movies
series_collection = db.series
shows_collection = db.shows

# Initialize Pyrogram client
app = Client("kannada_bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)


# Data Classes for Better Structure
@dataclass
class MediaFile:
    msg_id: str
    original_msg_id: int
    channel_id: int
    file_name: str
    caption: str
    quality: str
    size: str
    file_type: str
    telegram_link: str
    season: int = 1
    episode: int = 1

@dataclass
class ContentItem:
    id: str
    name: str
    type: str  # movies, webseries, tvseries, shows
    year: int
    language: str
    genre: str
    actors: List[str]
    director: str
    poster_url: str
    description: str
    rating: float
    view_count: int
    download_count: int
    media_files: List[MediaFile]
    is_dubbed: bool
    is_latest: bool
    created_at: datetime
    updated_at: datetime

# Advanced User Session Management
class UserSession:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.current_step = None
        self.entertainment_type = None
        self.names_to_process = []
        self.current_name_index = 0
        self.current_detail_index = 0
        self.current_field_index = 0
        self.search_results = {}
        self.selected_media = {}
        self.details = {}
        self.unavailable_list = []
        self.current_page = 0
        self.total_pages = 0
        self.last_activity = datetime.utcnow()

# Enhanced Session Manager
class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.cleanup_interval = 3600  # 1 hour
    
    def get_session(self, user_id: int) -> UserSession:
        # Clean up old sessions
        self.cleanup_expired_sessions()
        
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession()
        
        self.sessions[user_id].last_activity = datetime.utcnow()
        return self.sessions[user_id]
    
    def cleanup_expired_sessions(self):
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for user_id, session in self.sessions.items():
            if (current_time - session.last_activity).seconds > self.cleanup_interval:
                expired_sessions.append(user_id)
        
        for user_id in expired_sessions:
            del self.sessions[user_id]

# Advanced Blogger API Integration
class BloggerAPI:
    def __init__(self):
        self.api_key = Config.BLOGGER_API_KEY
        self.blog_id = Config.BLOGGER_BLOG_ID
        self.base_url = f"https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}"
    
    async def create_post(self, title: str, content: str, labels: List[str]) -> bool:
        """Create a new blog post"""
        try:
            post_data = {
                "kind": "blogger#post",
                "title": title,
                "content": content,
                "labels": labels,
                "status": "PUBLISHED"
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/posts?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                
                async with session.post(url, json=post_data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Blog post created: {result.get('url')}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create blog post: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error creating blog post: {e}")
            return False
    
    async def update_post(self, post_id: str, title: str, content: str, labels: List[str]) -> bool:
        """Update an existing blog post"""
        try:
            post_data = {
                "title": title,
                "content": content,
                "labels": labels
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/posts/{post_id}?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                
                async with session.put(url, json=post_data, headers=headers) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error updating blog post: {e}")
            return False
    
    async def search_posts(self, query: str) -> List[dict]:
        """Search for existing blog posts"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/posts/search?q={quote(query)}&key={self.api_key}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("items", [])
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching blog posts: {e}")
            return []

# Advanced Content Generator
class ContentGenerator:
    def __init__(self):
        self.blogger_api = BloggerAPI()
    
    def generate_blog_content(self, content_item: ContentItem) -> str:
        """Generate complete HTML blog content"""
        
        # Determine content type emoji and title
        type_emoji = {
            "movies": "🎬",
            "webseries": "📺",
            "tvseries": "📻", 
            "shows": "🎭"
        }
        
        emoji = type_emoji.get(content_item.type, "🎬")
        
        # Generate structured HTML content
        html_content = f"""
        <div class="content-container">
            <!-- Header Section -->
            <div class="content-header">
                <div class="poster-section">
                    <img src="{content_item.poster_url}" alt="{content_item.name} Poster" class="main-poster" />
                </div>
                <div class="info-section">
                    <h1 class="content-title">{emoji} {content_item.name}</h1>
                    <div class="content-meta">
                        <div class="meta-item">
                            <span class="meta-label">📅 Year:</span>
                            <span class="meta-value">{content_item.year}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">🗣️ Language:</span>
                            <span class="meta-value">{content_item.language}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">🎭 Genre:</span>
                            <span class="meta-value">{content_item.genre}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">🎬 Director:</span>
                            <span class="meta-value">{content_item.director}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">⭐ Rating:</span>
                            <span class="meta-value">{content_item.rating}/5</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Cast Section -->
            <div class="cast-section">
                <h3>👥 Cast</h3>
                <div class="cast-list">
                    {', '.join(content_item.actors)}
                </div>
            </div>
            
            <!-- Description Section -->
            <div class="description-section">
                <h3>📖 Plot Summary</h3>
                <p class="plot-text">{content_item.description}</p>
            </div>
            
            <!-- Download Section -->
            <div class="download-section">
                <h3>💾 Download Links</h3>
                <div class="download-info">
                    <p>🤖 <strong>How to Download:</strong></p>
                    <ol>
                        <li>Click on your preferred quality below</li>
                        <li>You'll be redirected to our Telegram bot</li>
                        <li>Click "START" in the bot</li>
                        <li>Your download will begin automatically</li>
                    </ol>
                </div>
                
                <div class="download-buttons">
                    {self.generate_download_buttons(content_item.media_files)}
                </div>
            </div>
            
            <!-- Statistics Section -->
            <div class="stats-section">
                <div class="stat-item">
                    <span class="stat-number">{content_item.view_count:,}</span>
                    <span class="stat-label">Views</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{content_item.download_count:,}</span>
                    <span class="stat-label">Downloads</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{content_item.rating}</span>
                    <span class="stat-label">Rating</span>
                </div>
            </div>
            
            <!-- Related Content Section -->
            <div class="related-section">
                <h3>🔍 You Might Also Like</h3>
                <p>Check out our <a href="{Config.BLOG_URL}">complete collection</a> of Kannada entertainment!</p>
            </div>
            
            <!-- Bot Promotion -->
            <div class="bot-promotion">
                <h3>🤖 Join Our Telegram Bot</h3>
                <p>Get instant access to all our content through our Telegram bot!</p>
                <a href="https://t.me/{Config.BOT_USERNAME}" class="bot-link" target="_blank">
                    🚀 Start Bot
                </a>
            </div>
        </div>
        
        <style>
            .content-container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            
            .content-header {{
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }}
            
            .poster-section {{
                flex: 0 0 200px;
            }}
            
            .main-poster {{
                width: 100%;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }}
            
            .info-section {{
                flex: 1;
                min-width: 300px;
            }}
            
            .content-title {{
                font-size: 2.2em;
                margin-bottom: 20px;
                color: #2c3e50;
                font-weight: bold;
            }}
            
            .content-meta {{
                display: grid;
                gap: 10px;
            }}
            
            .meta-item {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }}
            
            .meta-label {{
                font-weight: 600;
                color: #555;
            }}
            
            .meta-value {{
                color: #333;
            }}
            
            .cast-section, .description-section {{
                margin: 30px 0;
            }}
            
            .cast-section h3, .description-section h3 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }}
            
            .cast-list {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                font-weight: 500;
            }}
            
            .plot-text {{
                line-height: 1.8;
                color: #444;
                font-size: 1.1em;
            }}
            
            .download-section {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin: 30px 0;
            }}
            
            .download-section h3 {{
                margin-bottom: 20px;
                font-size: 1.8em;
            }}
            
            .download-info {{
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            
            .download-info ol {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            
            .download-buttons {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }}
            
            .download-btn {{
                background: rgba(255,255,255,0.2);
                border: 2px solid rgba(255,255,255,0.3);
                color: white;
                padding: 15px 20px;
                border-radius: 10px;
                text-decoration: none;
                text-align: center;
                transition: all 0.3s ease;
                font-weight: 600;
            }}
            
            .download-btn:hover {{
                background: rgba(255,255,255,0.3);
                border-color: rgba(255,255,255,0.5);
                transform: translateY(-2px);
            }}
            
            .quality {{
                font-size: 1.2em;
                display: block;
            }}
            
            .file-size {{
                font-size: 0.9em;
                opacity: 0.8;
            }}
            
            .stats-section {{
                display: flex;
                justify-content: space-around;
                background: #f8f9fa;
                padding: 30px;
                border-radius: 10px;
                margin: 30px 0;
            }}
            
            .stat-item {{
                text-align: center;
            }}
            
            .stat-number {{
                display: block;
                font-size: 2em;
                font-weight: bold;
                color: #3498db;
            }}
            
            .stat-label {{
                color: #666;
                font-size: 0.9em;
                text-transform: uppercase;
            }}
            
            .related-section {{
                background: #fff3cd;
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #ffc107;
                margin: 30px 0;
            }}
            
            .bot-promotion {{
                background: #d1ecf1;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                border: 2px solid #bee5eb;
            }}
            
            .bot-link {{
                display: inline-block;
                background: #007bff;
                color: white;
                padding: 12px 30px;
                border-radius: 25px;
                text-decoration: none;
                font-weight: bold;
                margin-top: 15px;
                transition: background 0.3s ease;
            }}
            
            .bot-link:hover {{
                background: #0056b3;
            }}
            
            @media (max-width: 768px) {{
                .content-header {{
                    flex-direction: column;
                }}
                
                .poster-section {{
                    flex: none;
                    text-align: center;
                }}
                
                .main-poster {{
                    max-width: 300px;
                }}
                
                .download-buttons {{
                    grid-template-columns: 1fr;
                }}
                
                .stats-section {{
                    flex-direction: column;
                    gap: 20px;
                }}
            }}
        </style>
        """
        
        return html_content
    
    def generate_download_buttons(self, media_files: List[MediaFile]) -> str:
        """Generate download buttons HTML"""
        buttons_html = ""
        
        # Group by quality for better organization
        quality_files = {}
        for file in media_files:
            if file.quality not in quality_files:
                quality_files[file.quality] = []
            quality_files[file.quality].append(file)
        
        # Sort qualities by preference
        quality_order = ["4K", "1080P", "720P", "480P", "360P", "HD"]
        sorted_qualities = sorted(quality_files.keys(), 
                                key=lambda x: quality_order.index(x) if x in quality_order else 999)
        
        for quality in sorted_qualities:
            files = quality_files[quality]
            if len(files) == 1:
                file = files[0]
                buttons_html += f'''
                <a href="https://t.me/{Config.BOT_USERNAME}?start=media-{file.msg_id}" 
                   class="download-btn" target="_blank">
                    <span class="quality">{quality}</span>
                    <span class="file-size">{file.size}</span>
                </a>
                '''
            else:
                # Multiple files with same quality (episodes, parts, etc.)
                for i, file in enumerate(files, 1):
                    buttons_html += f'''
                    <a href="https://t.me/{Config.BOT_USERNAME}?start=media-{file.msg_id}" 
                       class="download-btn" target="_blank">
                        <span class="quality">{quality} - Part {i}</span>
                        <span class="file-size">{file.size}</span>
                    </a>
                    '''
        
        return buttons_html
    
    def generate_labels(self, content_item: ContentItem) -> List[str]:
        """Generate SEO-friendly labels for the blog post"""
        labels = []
        
        # Basic labels
        labels.append(content_item.type.replace('_', ' ').title())
        labels.append(content_item.language)
        labels.append(str(content_item.year))
        labels.append(content_item.genre)
        
        # Actor labels (limit to top 3)
        for actor in content_item.actors[:3]:
            labels.append(actor)
        
        # Special labels
        if content_item.is_dubbed:
            labels.append("Dubbed")
        if content_item.is_latest:
            labels.append("Latest")
        if content_item.rating >= 4.5:
            labels.append("Highly Rated")
        
        # Quality labels
        qualities = list(set([file.quality for file in content_item.media_files]))
        if "4K" in qualities:
            labels.append("4K")
        if "1080P" in qualities:
            labels.append("Full HD")
        
        return list(set(labels))  # Remove duplicates
    
    async def publish_to_blog(self, content_item: ContentItem) -> bool:
        """Publish content item to blog"""
        try:
            # Generate blog content
            title = f"{content_item.name} ({content_item.year}) - {content_item.language} {content_item.type.title()}"
            content = self.generate_blog_content(content_item)
            labels = self.generate_labels(content_item)
            
            # Check if post already exists
            existing_posts = await self.blogger_api.search_posts(content_item.name)
            
            if existing_posts:
                # Update existing post
                post_id = existing_posts[0]["id"]
                success = await self.blogger_api.update_post(post_id, title, content, labels)
                logger.info(f"Updated blog post for {content_item.name}: {success}")
            else:
                # Create new post
                success = await self.blogger_api.create_post(title, content, labels)
                logger.info(f"Created blog post for {content_item.name}: {success}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing to blog: {e}")
            return False

# Enhanced Analytics System
class AnalyticsManager:
    def __init__(self):
        self.analytics_collection = db.analytics
    
    async def track_event(self, event_type: str, user_id: int, data: dict):
        """Track user events for analytics"""
        try:
            event_data = {
                "event_type": event_type,
                "user_id": user_id,
                "data": data,
                "timestamp": datetime.utcnow(),
                "date": datetime.utcnow().date().isoformat()
            }
            
            self.analytics_collection.insert_one(event_data)
            
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
    
    async def get_popular_content(self, limit: int = 10) -> List[dict]:
        """Get most popular content based on downloads"""
        try:
            pipeline = [
                {"$match": {"event_type": "download"}},
                {"$group": {
                    "_id": "$data.content_id",
                    "download_count": {"$sum": 1}
                }},
                {"$sort": {"download_count": -1}},
                {"$limit": limit}
            ]
            
            results = list(self.analytics_collection.aggregate(pipeline))
            return results
            
        except Exception as e:
            logger.error(f"Error getting popular content: {e}")
            return []
    
    async def get_daily_stats(self, days: int = 7) -> dict:
        """Get daily statistics"""
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
            
            pipeline = [
                {"$match": {"date": {"$gte": start_date}}},
                {"$group": {
                    "_id": {
                        "date": "$date",
                        "event_type": "$event_type"
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id.date": 1}}
            ]
            
            results = list(self.analytics_collection.aggregate(pipeline))
            return results
            
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return {}

# Initialize advanced components
session_manager = SessionManager()
content_generator = ContentGenerator()
analytics_manager = AnalyticsManager()

# Enhanced helper functions
def get_user_session(user_id: int) -> UserSession:
    return session_manager.get_session(user_id)

async def enhanced_search_in_channels(client: Client, search_term: str) -> List[dict]:
    """Enhanced search with better filtering and quality detection"""
    results = []
    
    try:
        for channel_id in Config.CHANNEL_IDS:
            try:
                search_queries = [
                    search_term,
                    search_term.replace(" ", ""),
                    search_term.replace(" ", "."),
                    search_term.replace(" ", "_")
                ]
                
                for query in search_queries:
                    async for msg in client.search_messages(
                        chat_id=channel_id,
                        query=query,
                        limit=25
                    ):
                        if msg.video or msg.document:
                            # Enhanced content filtering
                            if await is_valid_content(msg, search_term):
                                result = await process_media_message(msg, channel_id)
                                if result and result not in results:
                                    results.append(result)
                        
                        if len(results) >= Config.MAX_SEARCH_RESULTS:
                            break
                    
                    if len(results) >= Config.MAX_SEARCH_RESULTS:
                        break
                        
            except Exception as e:
                logger.error(f"Error searching in channel {channel_id}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error in enhanced_search_in_channels: {e}")
    
    return results[:Config.MAX_SEARCH_RESULTS]

async def is_valid_content(message, search_term: str) -> bool:
    """Check if message contains valid entertainment content"""
    try:
        # Get text from caption or filename
        caption = message.caption or ""
        file_name = ""
        
        if message.video:
            file_name = message.video.file_name or ""
            file_size_gb = message.video.file_size / (1024**3) if message.video.file_size else 0
        elif message.document:
            file_name = message.document.file_name or ""
            file_size_gb = message.document.file_size / (1024**3) if message.document.file_size else 0
        else:
            return False
        
        # Check file size (skip very large or very small files)
        if file_size_gb > Config.MAX_FILE_SIZE_GB or file_size_gb < 0.1:
            return False
        
        # Check file format
        file_extension = os.path.splitext(file_name.lower())[1]
        if file_extension not in Config.SUPPORTED_FORMATS:
            return False
        
        # Check if search term matches
        full_text = f"{caption} {file_name}".lower()
        search_lower = search_term.lower()
        
        # Exact match or close match
        if (search_lower in full_text or 
            any(word in full_text for word in search_lower.split()) or
            similar_strings(search_lower, full_text)):
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error validating content: {e}")
        return False

def similar_strings(s1: str, s2: str, threshold: float = 0.6) -> bool:
    """Check if two strings are similar using simple similarity"""
    try:
        # Simple similarity check
        s1_words = set(s1.lower().split())
        s2_words = set(s2.lower().split())
        
        if not s1_words or not s2_words:
            return False
        
        intersection = s1_words.intersection(s2_words)
        union = s1_words.union(s2_words)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold
        
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return False

async def process_media_message(message, channel_id: int) -> Optional[dict]:
    """Process media message and extract information"""
    try:
        caption = message.caption or ""
        file_name = ""
        file_size = 0
        
        if message.video:
            file_name = message.video.file_name or ""
            file_size = message.video.file_size or 0
        elif message.document:
            file_name = message.document.file_name or ""
            file_size = message.document.file_size or 0
        
        # Enhanced quality detection
        quality = detect_quality_advanced(file_name + " " + caption)
        
        # Extract additional metadata
        metadata = extract_metadata(file_name, caption)
        
        result = {
            "message_id": message.id,
            "channel_id": channel_id,
            "caption": caption,
            "file_name": file_name,
            "quality": quality,
            "size": format_file_size(file_size),
            "file_type": "video" if message.video else "document",
            "link": f"https://t.me/c/{str(channel_id)[4:]}/{message.id}",
            "metadata": metadata
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing media message: {e}")
        return None

def detect_quality_advanced(text: str) -> str:
    """Advanced quality detection with multiple patterns"""
    text = text.lower()
    
    # Priority-based quality detection
    quality_patterns = {
        "4K": [r'4k', r'2160p', r'uhd', r'ultra.?hd', r'4320p'],
        "2K": [r'2k', r'1440p', r'qhd'],
        "1080P": [r'1080p', r'fhd', r'full.?hd', r'1080'],
        "720P": [r'720p', r'hd', r'720'],
        "480P": [r'480p', r'480'],
        "360P": [r'360p', r'360']
    }
    
    for quality, patterns in quality_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return quality
    
    # Advanced heuristics based on file size and name patterns
    if any(word in text for word in ['bluray', 'brrip', 'bdrip']):
        return "1080P"
    elif any(word in text for word in ['webrip', 'web-dl', 'webdl']):
        return "720P"
    elif any(word in text for word in ['dvdrip', 'dvdscr']):
        return "480P"
    elif any(word in text for word in ['camrip', 'cam', 'ts', 'tc']):
        return "360P"
    
    return "HD"  # Default fallback

def extract_metadata(file_name: str, caption: str) -> dict:
    """Extract additional metadata from filename and caption"""
    metadata = {
        "language": "Unknown",
        "year": None,
        "genre": "Unknown",
        "audio": "Unknown",
        "subtitle": False
    }
    
    try:
        text = f"{file_name} {caption}".lower()
        
        # Language detection
        if any(lang in text for lang in ['kannada', 'kan']):
            metadata["language"] = "Kannada"
        elif any(lang in text for lang in ['hindi', 'hin']):
            metadata["language"] = "Hindi"
        elif any(lang in text for lang in ['tamil', 'tam']):
            metadata["language"] = "Tamil"
        elif any(lang in text for lang in ['telugu', 'tel']):
            metadata["language"] = "Telugu"
        elif any(lang in text for lang in ['english', 'eng']):
            metadata["language"] = "English"
        
        # Year extraction
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            metadata["year"] = int(year_match.group())
        
        # Audio format detection
        if any(audio in text for audio in ['atmos', 'dolby']):
            metadata["audio"] = "Dolby Atmos"
        elif any(audio in text for audio in ['dts', 'dts-hd']):
            metadata["audio"] = "DTS"
        elif any(audio in text for audio in ['aac', 'ac3']):
            metadata["audio"] = "AAC"
        
        # Subtitle detection
        metadata["subtitle"] = any(sub in text for sub in ['sub', 'subtitle', 'srt'])
        
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
    
    return metadata

# Enhanced upload finalization with blogger integration
async def enhanced_finalize_upload(client: Client, message: Message, user_id: int):
    """Enhanced finalization with blogger integration"""
    try:
        session = get_user_session(user_id)
        
        await message.reply_text(
            "🔄 **Processing Upload...**\n"
            "📊 Organizing data\n"
            "💾 Saving to database\n"
            "🌐 Publishing to blog\n"
            "⏳ This may take a few moments..."
        )
        
        saved_count = 0
        blog_published = 0
        error_count = 0
        
        # Process each item
        for item_name, item_details in session.details.items():
            try:
                # Get selected media for this item
                item_media = get_item_media(session, item_name)
                
                if not item_media:
                    logger.warning(f"No media found for {item_name}")
                    continue
                
                # Process media files
                processed_media = await process_media_files(client, item_media, session.entertainment_type)
                
                # Create ContentItem object
                content_item = create_content_item(item_name, item_details, processed_media, session.entertainment_type)
                
                # Save to database
                collection = get_collection_by_type(session.entertainment_type)
                
                existing = collection.find_one({"name": content_item.name})
                if existing:
                    collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": content_item.__dict__}
                    )
                else:
                    collection.insert_one(content_item.__dict__)
                
                saved_count += 1
                
                # Publish to blog
                try:
                    blog_success = await content_generator.publish_to_blog(content_item)
                    if blog_success:
                        blog_published += 1
                except Exception as blog_error:
                    logger.error(f"Blog publishing error for {item_name}: {blog_error}")
                
                # Track analytics
                await analytics_manager.track_event("content_uploaded", user_id, {
                    "content_id": content_item.id,
                    "content_name": content_item.name,
                    "content_type": content_item.type
                })
                
            except Exception as e:
                logger.error(f"Error processing {item_name}: {e}")
                error_count += 1
        
        # Send completion message
        completion_text = f"✅ **Upload Process Completed!**\n\n"
        completion_text += f"💾 **Database:** {saved_count} items saved\n"
        completion_text += f"🌐 **Blog:** {blog_published} posts published\n"
        
        if error_count > 0:
            completion_text += f"❌ **Errors:** {error_count} items failed\n"
        
        if session.unavailable_list:
            completion_text += f"\n📝 **Unavailable Items:**\n"
            for item in session.unavailable_list:
                completion_text += f"   • {item}\n"
        
        completion_text += f"\n🎉 **All done!** Content is now live on:\n"
        completion_text += f"🌐 **Blog:** {Config.BLOG_URL}\n"
        completion_text += f"🤖 **Bot:** @{Config.BOT_USERNAME}"
        
        await message.reply_text(completion_text)
        
        # Clear session
        session.reset()
        
    except Exception as e:
        logger.error(f"Error in enhanced finalization: {e}")
        await message.reply_text("❌ Error occurred during finalization.")

def create_content_item(item_name: str, item_details: dict, media_files: List[dict], entertainment_type: str) -> ContentItem:
    """Create ContentItem object from processed data"""
    
    # Convert media files to MediaFile objects
    media_objects = []
    for media in media_files:
        media_obj = MediaFile(
            msg_id=media["msg_id"],
            original_msg_id=media["original_msg_id"],
            channel_id=media["channel_id"],
            file_name=media["file_name"],
            caption=media["caption"],
            quality=media["quality"],
            size=media["size"],
            file_type=media["file_type"],
            telegram_link=media["telegram_link"],
            season=media.get("season", 1),
            episode=media.get("episode", 1)
        )
        media_objects.append(media_obj)
    
    # Create ContentItem
    content_item = ContentItem(
        id=str(uuid.uuid4()),
        name=item_details.get("name", item_name),
        type=entertainment_type,
        year=item_details.get("year", 2024),
        language=item_details.get("language", "Kannada"),
        genre=item_details.get("genre", "Unknown"),
        actors=item_details.get("actors", []),
        director=item_details.get("director", "Unknown"),
        poster_url=item_details.get("poster_link", ""),
        description=item_details.get("description", ""),
        rating=0.0,
        view_count=0,
        download_count=0,
        media_files=media_objects,
        is_dubbed=item_details.get("is_dubbed", False),
        is_latest=True,  # Newly uploaded content is latest
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    return content_item

# Enhanced user commands with analytics
@app.on_message(filters.command("stats") & filters.user(Config.ADMIN_IDS))
async def stats_command(client: Client, message: Message):
    """Show bot statistics (Admin only)"""
    try:
        # Get database stats
        movies_count = movies_collection.count_documents({})
        series_count = series_collection.count_documents({})
        shows_count = shows_collection.count_documents({})
        
        # Get daily stats
        daily_stats = await analytics_manager.get_daily_stats(7)
        
        # Get popular content
        popular_content = await analytics_manager.get_popular_content(5)
        
        stats_text = f"📊 **Bot Statistics**\n\n"
        stats_text += f"🎬 **Movies:** {movies_count}\n"
        stats_text += f"📺 **Series:** {series_count}\n"
        stats_text += f"🎭 **Shows:** {shows_count}\n"
        stats_text += f"📁 **Total Content:** {movies_count + series_count + shows_count}\n\n"
        
        if popular_content:
            stats_text += f"🔥 **Most Downloaded (This Week):**\n"
            for i, item in enumerate(popular_content[:3], 1):
                content_id = item["_id"]
                download_count = item["download_count"]
                
                # Get content details
                content = None
                for collection in [movies_collection, series_collection, shows_collection]:
                    content = collection.find_one({"id": content_id})
                    if content:
                        break
                
                if content:
                    stats_text += f"{i}. {content['name']} - {download_count} downloads\n"
        
        stats_text += f"\n🌐 **Blog:** {Config.BLOG_URL}\n"
        stats_text += f"🤖 **Bot:** @{Config.BOT_USERNAME}"
        
        await message.reply_text(stats_text)
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.reply_text("❌ Error getting statistics.")

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_IDS))
async def broadcast_command(client: Client, message: Message):
    """Broadcast message to all users (Admin only)"""
    try:
        if len(message.command) < 2:
            await message.reply_text("Usage: /broadcast <message>")
            return
        
        broadcast_message = " ".join(message.command[1:])
        
        # Get all unique users from analytics
        users = analytics_manager.analytics_collection.distinct("user_id")
        
        success_count = 0
        error_count = 0
        
        progress_message = await message.reply_text(f"📢 Broadcasting to {len(users)} users...")
        
        for user_id in users:
            try:
                await client.send_message(user_id, broadcast_message)
                success_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Error broadcasting to {user_id}: {e}")
        
        await progress_message.edit_text(
            f"✅ **Broadcast Complete**\n"
            f"📤 **Sent:** {success_count}\n"
            f"❌ **Failed:** {error_count}"
        )
        
    except Exception as e:
        logger.error(f"Error in broadcast command: {e}")
        await message.reply_text("❌ Error broadcasting message.")

@app.on_message(filters.command("backup") & filters.user(Config.ADMIN_IDS))
async def backup_command(client: Client, message: Message):
    """Create database backup (Admin only)"""
    try:
        await message.reply_text("🔄 Creating database backup...")
        
        # Export collections to JSON
        backup_data = {
            "movies": list(movies_collection.find({})),
            "series": list(series_collection.find({})),
            "shows": list(shows_collection.find({})),
            "analytics": list(analytics_manager.analytics_collection.find({})),
            "backup_date": datetime.utcnow().isoformat()
        }
        
        # Convert ObjectId to string for JSON serialization
        def convert_objectid(obj):
            if hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                if hasattr(obj, 'items'):
                    return {key: convert_objectid(value) for key, value in obj.items()}
                else:
                    return [convert_objectid(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return convert_objectid(obj.__dict__)
            elif str(type(obj)) == "<class 'bson.objectid.ObjectId'>":
                return str(obj)
            else:
                return obj
        
        backup_data = convert_objectid(backup_data)
        
        # Create backup file
        backup_filename = f"kannada_bot_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        # Send backup file
        await client.send_document(
            chat_id=message.chat.id,
            document=backup_filename,
            caption=f"🗃️ **Database Backup**\n📅 **Created:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Clean up local file
        os.remove(backup_filename)
        
        await message.reply_text("✅ Backup created and sent successfully!")
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        await message.reply_text("❌ Error creating backup.")

# Enhanced content sharing
@app.on_callback_query(filters.regex(r"^share_"))
async def enhanced_handle_share(client: Client, callback_query: CallbackQuery):
    """Enhanced sharing with multiple options"""
    try:
        content_id = callback_query.data.replace("share_", "")
        
        # Get content info
        content = None
        for collection in [movies_collection, series_collection, shows_collection]:
            try:
                from bson import ObjectId
                content = collection.find_one({"_id": ObjectId(content_id)})
                if content:
                    break
            except:
                continue
        
        if not content:
            await callback_query.answer("❌ Content not found")
            return
        
        # Generate share content
        bot_username = Config.BOT_USERNAME
        blog_url = f"{Config.BLOG_URL}/search/label/{quote(content['name'])}"
        bot_link = f"https://t.me/{bot_username}?start=content-{content_id}"
        
        share_text = f"""🎬 **{content['name']}** ({content.get('year', '')})

🎭 **Genre:** {content.get('genre', 'Unknown')}
🗣️ **Language:** {content.get('language', 'Unknown')}
⭐ **Rating:** {content.get('rating', 0)}/5

📱 **Download:** {bot_link}
🌐 **Blog:** {blog_url}

#KannadaMovies #KannadaEntertainment"""
        
        # Share options
        buttons = [
            [
                InlineKeyboardButton("📱 Share to Chat", switch_inline_query=share_text),
                InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_link_{content_id}")
            ],
            [
                InlineKeyboardButton("🌐 Open in Blog", url=blog_url),
                InlineKeyboardButton("🤖 Open in Bot", url=bot_link)
            ],
            [
                InlineKeyboardButton("📤 More Options", callback_data=f"share_options_{content_id}"),
                InlineKeyboardButton("🔙 Back", callback_data=f"view_content_{content_id}")
            ]
        ]
        
        keyboard = InlineKeyboardMarkup(buttons)
        
        await callback_query.edit_message_text(
            f"📤 **Share: {content['name']}**\n\n"
            f"Choose how you'd like to share this content:\n\n"
            f"🔗 **Bot Link:**\n`{bot_link}`\n\n"
            f"🌐 **Blog Link:**\n`{blog_url}`",
            reply_markup=keyboard
        )
        
        # Track sharing event
        await analytics_manager.track_event("content_shared", callback_query.from_user.id, {
            "content_id": content_id,
            "content_name": content['name']
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced sharing: {e}")
        await callback_query.answer("❌ Error occurred")

# User feedback system
@app.on_message(filters.command("feedback"))
async def feedback_command(client: Client, message: Message):
    """Collect user feedback"""
    try:
        if len(message.command) < 2:
            feedback_text = """📝 **Send Your Feedback**

We value your opinion! Help us improve by sending feedback.

**Usage:** `/feedback Your message here`

**Examples:**
• `/feedback The bot is awesome! Love the quality options.`
• `/feedback Please add more South Indian movies.`
• `/feedback Found a bug in the search feature.`

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
        
        # Save feedback to database
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
        admin_message = f"""📝 **New Feedback Received**

👤 **User:** @{username} ({user_id})
💬 **Message:** {feedback_text}
📅 **Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        for admin_id in Config.ADMIN_IDS:
            try:
                await client.send_message(admin_id, admin_message)
            except:
                pass
        
        await message.reply_text(
            "✅ **Thank you for your feedback!**\n\n"
            "Your message has been sent to our team. We appreciate your input and "
            "will use it to improve our service.\n\n"
            "🎬 Keep enjoying Kannada entertainment!"
        )
        
        # Track feedback event
        await analytics_manager.track_event("feedback_sent", user_id, {
            "feedback_type": "general",
            "feedback_length": len(feedback_text)
        })
        
    except Exception as e:
        logger.error(f"Error in feedback command: {e}")
        await message.reply_text("❌ Error processing feedback. Please try again later.")

# Quick feedback callbacks
@app.on_callback_query(filters.regex(r"^(rate_bot|report_bug|suggest_feature|send_compliment)$"))
async def handle_quick_feedback(client: Client, callback_query: CallbackQuery):
    """Handle quick feedback options"""
    try:
        action = callback_query.data
        user_id = callback_query.from_user.id
        
        feedback_prompts = {
            "rate_bot": "⭐ **Rate Our Bot**\n\nHow would you rate your experience with our bot?",
            "report_bug": "🐛 **Report a Bug**\n\nPlease describe the bug you encountered:",
            "suggest_feature": "💡 **Suggest a Feature**\n\nWhat feature would you like to see added?",
            "send_compliment": "❤️ **Send Compliment**\n\nWe'd love to hear what you like about our service:"
        }
        
        if action == "rate_bot":
            # Show rating buttons
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
            # Store user state for text input
            user_feedback_state[user_id] = action
            
            await callback_query.edit_message_text(
                f"{feedback_prompts[action]}\n\n"
                "💬 **Please send your message in the chat.**"
            )
        
    except Exception as e:
        logger.error(f"Error handling quick feedback: {e}")
        await callback_query.answer("❌ Error occurred")

# Global state for feedback
user_feedback_state = {}

# Handle rating selection
@app.on_callback_query(filters.regex(r"^rating_\d$"))
async def handle_bot_rating(client: Client, callback_query: CallbackQuery):
    """Handle bot rating selection"""
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
            "timestamp": datetime.utcnow(),
            "status": "new"
        }
        
        db.feedback.insert_one(feedback_data)
        
        # Thank user
        stars = "⭐" * rating
        await callback_query.edit_message_text(
            f"✅ **Thank you for rating us!**\n\n"
            f"Your rating: {stars} ({rating}/5)\n\n"
            f"We appreciate your feedback and will continue to improve our service!"
        )
        
        # Track rating event
        await analytics_manager.track_event("bot_rated", user_id, {"rating": rating})
        
    except Exception as e:
        logger.error(f"Error handling bot rating: {e}")
        await callback_query.answer("❌ Error occurred")

# Handle feedback text input
@app.on_message(filters.text & ~filters.command())
async def handle_feedback_input(client: Client, message: Message):
    """Handle feedback text input"""
    try:
        user_id = message.from_user.id
        
        if user_id not in user_feedback_state:
            return
        
        feedback_type = user_feedback_state[user_id]
        feedback_text = message.text.strip()
        username = message.from_user.username or "Unknown"
        
        # Save feedback
        feedback_data = {
            "user_id": user_id,
            "username": username,
            "feedback": feedback_text,
            "type": feedback_type,
            "timestamp": datetime.utcnow(),
            "status": "new"
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
💬 **Message:** {feedback_text}
📅 **Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        for admin_id in Config.ADMIN_IDS:
            try:
                await client.send_message(admin_id, admin_message)
            except:
                pass
        
        # Thank user
        response_messages = {
            "report_bug": "🐛 **Bug Report Received!**\n\nThank you for reporting this issue. Our team will investigate and fix it as soon as possible.",
            "suggest_feature": "💡 **Feature Suggestion Received!**\n\nGreat idea! We'll consider adding this feature in future updates.",
            "send_compliment": "❤️ **Thank You!**\n\nYour kind words mean a lot to us! We're glad you're enjoying our service."
        }
        
        await message.reply_text(
            response_messages.get(feedback_type, "✅ Thank you for your feedback!")
        )
        
        # Clear user state
        del user_feedback_state[user_id]
        
        # Track feedback event
        await analytics_manager.track_event("feedback_sent", user_id, {
            "feedback_type": feedback_type,
            "feedback_length": len(feedback_text)
        })
        
    except Exception as e:
        logger.error(f"Error handling feedback input: {e}")

print("🚀 Part 5: Advanced Bot Features & Complete Integration loaded!")
print("✅ Features: Enhanced search, Blogger integration, Analytics, Feedback system")
print("🎬 Complete Kannada Entertainment System ready!")

# Start the bot
if __name__ == "__main__":
    print("🎬 Starting Advanced Kannada Entertainment Bot...")
    print("📱 All advanced features loaded successfully!")
    print("🌐 Blog integration active")
    print("📊 Analytics system ready")
    print("💬 Feedback system enabled")
    app.run()
