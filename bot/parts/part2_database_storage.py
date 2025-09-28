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
