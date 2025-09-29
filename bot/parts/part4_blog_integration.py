import os
import aiohttp
import logging
from typing import List, Dict
from pymongo import MongoClient

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "kannada_entertainment")
BLOGGER_API_KEY = os.environ.get("BLOGGER_API_KEY", "")
BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")
BLOG_URL = os.environ.get("BLOG_URL", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

logger = logging.getLogger(__name__)

# Database connection
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DATABASE_NAME]

class BloggerAPI:
    def __init__(self):
        self.api_key = BLOGGER_API_KEY
        self.blog_id = BLOGGER_BLOG_ID
        self.base_url = f"https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}"
    
    async def create_post(self, title: str, content: str, labels: List[str]) -> bool:
        """Create a new blog post"""
        try:
            post_data = {
                "kind": "blogger#post",
                "title": title,
                "content": content,
                "labels": labels
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/posts?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                
                async with session.post(url, json=post_data, headers=headers) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error creating blog post: {e}")
            return False

class ContentGenerator:
    def __init__(self):
        self.blogger_api = BloggerAPI()
    
    def generate_blog_content(self, content_item) -> str:
        """Generate blog HTML content"""
        
        # Load template
        try:
            with open('templates/blog_template.html', 'r', encoding='utf-8') as f:
                template = f.read()
        except:
            logger.error("Could not load blog template")
            return ""
        
        # For now, return basic HTML
        # In production, you'd replace placeholders in template
        html = f"""
        <h1>{content_item.get('name', '')}</h1>
        <p>Year: {content_item.get('year', '')}</p>
        <p>Language: {content_item.get('language', '')}</p>
        <p>{content_item.get('description', '')}</p>
        """
        
        return html
    
    async def publish_to_blog(self, content_item) -> bool:
        """Publish content to blog"""
        try:
            title = f"{content_item.get('name')} ({content_item.get('year')})"
            content = self.generate_blog_content(content_item)
            labels = [content_item.get('language', ''), str(content_item.get('year', ''))]
            
            return await self.blogger_api.create_post(title, content, labels)
            
        except Exception as e:
            logger.error(f"Error publishing to blog: {e}")
            return False

# Initialize
content_generator = ContentGenerator()
