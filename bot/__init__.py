# bot/__init__.py

"""
Kannada Entertainment Bot Module

This __init__.py file is crucial. It tells Python that the 'bot' directory
should be treated as a package. This allows files from outside the
directory (like main.py) to import modules from inside it (like handlers.py).
"""

# This line imports the handlers.py file, making it accessible to main.py.
# When handlers.py is imported, it in turn imports all the bot's command
# functions from the 'parts' directory, registering them with the client.
from . import handlers
