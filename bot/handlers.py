

# bot/handlers.py
"""
Main handlers file that imports all bot functionality from different parts.
This file serves as the entry point for all bot handlers.
"""

# Part 1: Core Upload System & Admin Features
# Part 2: Details Collection & Database Storage  
# Part 3: User Search System & File Serving
from .parts.core_bot_functionality import *

# Part 4: Blog Integration (HTML templates handled separately)
from .parts.part4_blog_integration import *

# Part 5: Advanced Features & Analytics
from .parts.part5_advanced_features import *

import logging

logger = logging.getLogger(__name__)

# Initialize all components when handlers are imported
def initialize_bot_components():
    """Initialize all bot components"""
    try:
        logger.info("Initializing bot handlers...")
        logger.info("✓ Part 1: Upload System loaded")
        logger.info("✓ Part 2: Database Storage loaded") 
        logger.info("✓ Part 3: Search System loaded")
        logger.info("✓ Part 4: Blog Integration loaded")
        logger.info("✓ Part 5: Advanced Features loaded")
        logger.info("🚀 All bot components initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing bot components: {e}")
        return False

# Auto-initialize when imported
initialize_bot_components()
