# Kannada Entertainment Bot

A comprehensive Telegram bot for managing and serving Kannada entertainment content including movies, web series, TV shows, and dubbed content.

## Features

- 🎬 Content Upload & Management (Admin)
- 🔍 Smart Search System
- 📺 Multi-format Downloads
- 🌐 Blog Integration
- 📊 Analytics & Statistics
- 💬 User Feedback System
- 🤖 Automated Content Organization

## Deployment on Koyeb

### Prerequisites

1. Telegram Bot Token from [@BotFather](https://t.me/BotFather)
2. Telegram API ID & Hash from [my.telegram.org](https://my.telegram.org)
3. MongoDB Database (MongoDB Atlas recommended)
4. Koyeb Account

### Quick Deploy

1. **Clone this repository**
   ```bash
   git clone <your-repo-url>
   cd kannada-entertainment-bot
   ```

2. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Fill in all required values

3. **Deploy to Koyeb**
   - Connect your GitHub repository to Koyeb
   - Koyeb will automatically detect the `Dockerfile`
   - Set environment variables in Koyeb dashboard
   - Deploy!

### Environment Variables

Required variables for Koyeb deployment:

```bash
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
BOT_TOKEN=your_bot_token
ADMIN_IDS=123456789,987654321
CHANNEL_IDS=-1001234567890,-1001234567891
MONGO_URL=mongodb://username:password@host:port/
DATABASE_NAME=kannada_entertainment
BOT_USERNAME=your_bot_username
```

Optional variables:
```bash
BLOGGER_API_KEY=your_blogger_api_key
BLOGGER_BLOG_ID=your_blog_id
BLOG_URL=https://your-blog.blogspot.com
PORT=8080
```

### File Structure

```
├── main.py                 # Entry point
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── Dockerfile            # Docker configuration
├── Procfile              # Process configuration
├── .koyeb/
│   └── koyeb.yml         # Koyeb deployment config
├── bot/
│   ├── __init__.py
│   ├── handlers.py       # Main handlers
│   └── parts/
│       ├── part1_upload_system.py
│       ├── part2_database_storage.py
│       ├── part3_search_system.py
│       ├── part4_blog_integration.py
│       └── part5_advanced_features.py
└── templates/
    └── blog_template.html  # Blog template
```

## Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Run the bot**
   ```bash
   python main.py
   ```

## Commands

### User Commands
- `/start` - Start the bot
- `/search` - Search content
- `/latest` - Latest additions
- `/help` - Help information
- `/feedback` - Send feedback

### Admin Commands
- `/up` - Upload content
- `/stats` - View statistics
- `/broadcast` - Broadcast message
- `/backup` - Create database backup

## Support

For support and updates:
- Bot: [@your_bot_username](https://t.me/your_bot_username)
- Channel: [@your_channel](https://t.me/your_channel)

## License

This project is for educational purposes only.
