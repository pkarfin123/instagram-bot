import os
import requests
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import random

# ============================================
# 🔑 এখানে তোমার API Keys বসাও
# ============================================
TELEGRAM_BOT_TOKEN = "8608123260:AAFd-WIH0KXGs0l_H74NPfkC9oYIQItyss8"
GEMINI_API_KEY = "AIzaSyC6gcpsXhWKyuxSK-m7lUpsZrZnszgGVtE"
# ============================================

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Image sources (free, no API key needed)
UNSPLASH_TOPICS = [
    "business", "technology", "marketing", "success", 
    "finance", "entrepreneur", "motivation", "strategy"
]

def get_background_image(topic: str) -> Image.Image:
    """Fetch a relevant background image from Picsum (always free)"""
    try:
        # Try Unsplash source (free, no key needed)
        search_term = topic.replace(" ", ",")
        url = f"https://source.unsplash.com/1080x1080/?{search_term}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGB")
    except:
        pass
    
    # Fallback: colored gradient background
    img = Image.new("RGB", (1080, 1080), color=(20, 20, 40))
    return img

def create_post_image(headline: str, topic: str) -> BytesIO:
    """Create Instagram-style post image with bold text overlay"""
    
    # Get background
    bg = get_background_image(topic)
    bg = bg.resize((1080, 1080))
    
    # Dark overlay for text readability
    overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 160))
    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, overlay)
    bg = bg.convert("RGB")
    
    draw = ImageDraw.Draw(bg)
    
    # Try to use bold font, fallback to default
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        font_cta = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
    except:
        font_big = ImageFont.load_default()
        font_small = font_big
        font_cta = font_big

    # Wrap headline text
    wrapped = textwrap.fill(headline, width=22)
    lines = wrapped.split("\n")
    
    # Calculate total text height
    line_height = 85
    total_height = len(lines) * line_height
    start_y = (1080 - total_height) // 2 - 40
    
    # Draw headline with shadow
    for i, line in enumerate(lines):
        y = start_y + i * line_height
        # Shadow
        draw.text((55, y + 4), line, font=font_big, fill=(0, 0, 0, 200))
        # Main text
        draw.text((50, y), line, font=font_big, fill=(255, 255, 255))
    
    # Bottom accent bar
    draw.rectangle([(0, 980), (1080, 1080)], fill=(30, 30, 30, 220))
    
    # "Swipe left →" CTA
    draw.text((50, 1005), "Swipe left →", font=font_cta, fill=(200, 200, 200))
    
    # Top left branding dot
    draw.ellipse([(30, 30), (60, 60)], fill=(255, 60, 60))

    # Save to bytes
    output = BytesIO()
    bg.save(output, format="JPEG", quality=95)
    output.seek(0)
    return output


def generate_content(topic: str) -> dict:
    """Use Gemini to generate headline, caption and hashtags"""
    
    prompt = f"""
You are a viral Instagram content creator like @marketingmentor.in and @millionaire_mentor.

Topic: {topic}

Generate the following in JSON format:
{{
  "headline": "Short punchy headline (max 8 words, ALL CAPS style, shocking/viral)",
  "caption": "Engaging Instagram caption (3-4 sentences, conversational, ends with a question to boost engagement)",
  "hashtags": "30 relevant hashtags separated by spaces"
}}

Rules:
- Headline must be bold and shocking (like: "Apple is quietly going all-in on Formula 1!!")
- Caption must be engaging and informative
- Mix broad and niche hashtags
- Respond ONLY with valid JSON, no extra text
"""
    
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    # Clean JSON
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    import json
    data = json.loads(text)
    return data


# ============================================
# Telegram Command Handlers
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Instagram Content Bot*\n\n"
        "Commands:\n"
        "📌 `/post <topic>` — Generate viral post\n"
        "📌 `/auto` — Auto generate trending post\n"
        "📌 `/help` — Show help\n\n"
        "Example: `/post Apple buying Formula 1`",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use:*\n\n"
        "`/post Apple buying Formula 1`\n"
        "`/post 5 habits of millionaires`\n"
        "`/post Why 99% people fail at marketing`\n\n"
        "Bot will generate:\n"
        "🖼 Viral image with bold headline\n"
        "📝 Engaging caption\n"
        "#️⃣ 30 hashtags",
        parse_mode="Markdown"
    )

async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get topic from command
    topic = " ".join(context.args)
    
    if not topic:
        await update.message.reply_text(
            "❌ Topic দাও!\nExample: `/post Apple buying Formula 1`",
            parse_mode="Markdown"
        )
        return
    
    # Send loading message
    msg = await update.message.reply_text("⏳ Generating viral post...")
    
    try:
        # Generate content with Gemini
        content = generate_content(topic)
        headline = content.get("headline", topic.upper())
        caption = content.get("caption", "")
        hashtags = content.get("hashtags", "")
        
        # Create image
        image_bytes = create_post_image(headline, topic)
        
        # Full caption
        full_caption = f"{caption}\n\n{hashtags}"
        
        # Send image with caption
        await update.message.reply_photo(
            photo=image_bytes,
            caption=full_caption[:1024]  # Telegram caption limit
        )
        
        # Send full hashtags separately if too long
        if len(full_caption) > 1024:
            await update.message.reply_text(hashtags)
        
        await msg.delete()
        
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}\nআবার চেষ্টা করো!")


async def auto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto generate post with trending business/marketing topic"""
    
    trending_topics = [
        "Why most startups fail in first year",
        "Elon Musk secret business strategy",
        "How AI is replacing marketing jobs",
        "5 habits of self-made millionaires",
        "Why 99% people never become rich",
        "Apple secret product launch strategy",
        "How Instagram algorithm really works",
        "Warren Buffett investing rules for beginners",
        "Why your personal brand is your best asset",
        "How to make money while you sleep"
    ]
    
    topic = random.choice(trending_topics)
    context.args = topic.split()
    
    await update.message.reply_text(f"🎯 Auto topic: *{topic}*", parse_mode="Markdown")
    await post_command(update, context)


# ============================================
# Main
# ============================================

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("post", post_command))
    app.add_handler(CommandHandler("auto", auto_command))
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
