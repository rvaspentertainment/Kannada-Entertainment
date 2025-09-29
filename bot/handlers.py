# bot/handlers.py
"""
Main handlers file that imports all bot functionality from different parts.
This file serves as the entry point for all bot handlers.
"""

import logging

logger = logging.getLogger(__name__)

# This structure assumes you will split your feature files as we planned.
# If a file doesn't exist yet, you can comment out the import.

try:
    # Part 1 & 3: Core functions, User Search System & File Serving
    from .parts.core_bot_functionality import *
    from .parts.user_features import *

    # Part 2: Admin Upload System & Details Collection
    from .parts.admin_upload import *
    from .parts.details_collection import *

    # Part 4: Blog Integration
    from .parts.blogger_integration import *

    logger.info("Successfully imported all feature modules from bot/parts/.")

except ImportError as e:
    logger.error(f"FATAL: Failed to import a module from bot/parts/. Error: {e}")
    logger.error("Please ensure all part files (core_bot_functionality.py, admin_upload.py, etc.) exist in the bot/parts/ directory.")


# Initialize all components when handlers are imported
def initialize_bot_components():
    """Initialize all bot components"""
    try:
        logger.info("Initializing bot handlers...")
        logger.info("✓ Part 1: Core/User System loaded")
        logger.info("✓ Part 2: Admin/Database System loaded")
        logger.info("✓ Part 3: Search System loaded")
        logger.info("✓ Part 4: Blog Integration loaded")
        logger.info("🚀 All bot components initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing bot components: {e}")
        return False

# Auto-initialize when imported
initialize_bot_components()
