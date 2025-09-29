# bot/parts/blogger_integration.py

import logging
import aiohttp
from config import Config

logger = logging.getLogger(__name__)

async def update_blogger_site(client, message, content_doc: dict, ent_type: str):
    """
    Generates content and publishes it to the Blogger site.
    This is called after a new item is successfully saved to the database.
    """
    if not all([Config.BLOGGER_API_KEY, Config.BLOGGER_BLOG_ID]):
        logger.warning("Blogger API Key or Blog ID is not configured. Skipping blog post.")
        return

    try:
        title = f"{content_doc['name']} ({content_doc['year']}) Kannada {'Dubbed ' if content_doc.get('is_dubbed') else ''}{ent_type.title()} Download"
        
        # Generate labels
        labels = [ent_type.title()]
        labels.append(str(content_doc['year']))
        if content_doc.get('is_dubbed'):
            labels.append("Dubbed")
        if content_doc.get('genre'):
            labels.extend(content_doc['genre'])
        if content_doc.get('actors'):
            labels.extend(content_doc['actors'][:2]) # Add first 2 actors as labels

        # Generate HTML content from template
        html_content = generate_blog_html(content_doc)

        # Publish the post
        success = await publish_post(title, html_content, labels)
        
        if success:
            logger.info(f"Successfully published '{title}' to Blogger.")
            # Optionally send a confirmation to the admin
            # await client.send_message(message.chat.id, f"✅ Successfully published '{title}' to the blog.")
        else:
            logger.error(f"Failed to publish '{title}' to Blogger.")
            # await client.send_message(message.chat.id, f"❌ Failed to publish '{title}' to the blog.")

    except Exception as e:
        logger.error(f"Error in update_blogger_site: {e}")

def generate_blog_html(content: dict) -> str:
    """Reads the HTML template and populates it with content details."""
    try:
        with open('templates/blog_template.html', 'r', encoding='utf-8') as f:
            template = f.read()

        # --- Populate Placeholders ---
        # Basic Info
        template = template.replace("{{POST_TITLE}}", content.get('name', ''))
        template = template.replace("{{POSTER_URL}}", content.get('poster_url', ''))
        template = template.replace("{{YEAR}}", str(content.get('year', 'N/A')))
        template = template.replace("{{LANGUAGE}}", content.get('language', 'N/A'))
        template = template.replace("{{GENRE}}", ", ".join(content.get('genre', [])))
        template = template.replace("{{ACTORS}}", ", ".join(content.get('actors', [])))
        template = template.replace("{{DESCRIPTION}}", content.get('description', ''))
        
        # Download Buttons
        download_buttons_html = ""
        for media in content.get('media_files', []):
            url = f"https://t.me/{Config.BOT_USERNAME}?start=media-{media['msg_id']}"
            download_buttons_html += f"""
            <a href="{url}" class="download-btn" target="_blank">
                <div class="download-info">
                    <div class="download-quality">{media['quality']}</div>
                    <div class="download-size">{media['size']}</div>
                </div>
                <i class="fas fa-download download-icon"></i>
            </a>
            """
        template = template.replace("{{DOWNLOAD_BUTTONS}}", download_buttons_html)
        
        return template

    except FileNotFoundError:
        logger.error("Could not find blog_template.html in the /templates directory.")
        return f"<h1>{content.get('name')}</h1><p>Error: Blog template not found.</p>"
    except Exception as e:
        logger.error(f"Error generating blog HTML: {e}")
        return f"<h1>{content.get('name')}</h1><p>Error generating blog content.</p>"

async def publish_post(title: str, content: str, labels: list) -> bool:
    """Makes the API call to Google Blogger to create a new post."""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{Config.BLOGGER_BLOG_ID}/posts?key={Config.BLOGGER_API_KEY}"
    
    post_data = {
        "kind": "blogger#post",
        "title": title,
        "content": content,
        "labels": list(set(filter(None, labels))) # Remove duplicates and None values
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=post_data, headers=headers) as response:
                if response.status == 200:
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Blogger API Error ({response.status}): {error_text}")
                    return False
    except Exception as e:
        logger.error(f"HTTP error while publishing to Blogger: {e}")
        return False
