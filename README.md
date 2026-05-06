# 🤖 Instagram Style Telegram Bot

## Commands
- `/post Apple buying Formula 1` → Viral image + caption + hashtags
- `/auto` → Auto trending topic post
- `/help` → Help

## Setup Guide

### Step 1: bot.py তে API Keys বসাও
```python
TELEGRAM_BOT_TOKEN = "তোমার telegram bot token"
GEMINI_API_KEY = "তোমার gemini api key"
```

### Step 2: GitHub এ Upload করো
1. github.com → New Repository → "instagram-bot"
2. সব files upload করো (bot.py, requirements.txt, railway.toml)

### Step 3: Railway তে Deploy করো (FREE)
1. railway.app → Login with GitHub
2. "New Project" → "Deploy from GitHub repo"
3. তোমার repo select করো
4. Environment Variables এ দাও:
   - TELEGRAM_BOT_TOKEN = your_token
   - GEMINI_API_KEY = your_key
5. Deploy!

### ✅ Done! Bot 24/7 চলবে!
