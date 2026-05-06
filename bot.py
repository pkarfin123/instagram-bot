import os
import requests
import textwrap
import json
import random
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ============================================
# Keys come from Railway Environment Variables
# NEVER hardcode keys here!
# ============================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")


def generate_content(topic: str) -> dict:
    """Use OpenRouter (Free) to generate headline, caption and hashtags"""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [{
                "role": "user",
                "content": f"""You are a viral Instagram content creator like @marketingmentor.in

Topic: {topic}

Generate ONLY a JSON object, no extra text:
{{
  "headline": "Short punchy headline max 8 words shocking viral style",
  "caption": "Engaging Instagram caption 3-4 sentences ends with a question",
  "hashtags": "#tag1 #tag2 #tag3 ... (30 hashtags total)"
}}"""
            }]
        },
        timeout=30
    )
    text = response.json()["choices"][0]["message"]["content"].strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)


def get_background_image(topic: str) -> Image.Image:
    """Fetch background image from Unsplash (free, no key)"""
    try:
        search_term = topic.replace(" ", ",")[:50]
        url = f"https://source.unsplash.com/1080x1080/?{search_term}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGB")
    except:
        pass
    # Fallback dark background
    return Image.new("RGB", (1080, 1080), color=(15, 15, 30))


def create_post_image(headline: str, topic: str) -> BytesIO:
    """Create Instagram-style post image with bold text overlay"""
    bg = get_background_image(topic).resize((1080, 1080))

    # Dark overlay
    overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 170))
    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, overlay).convert("RGB")

    draw = ImageDraw.Draw(bg)

    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_cta = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
    except:
        font_big = ImageFont.load_default()
        font_cta = font_big

    # Wrap and center headline
    wrapped = textwrap.fill(headline, width=22)
    lines = wrapped.split("\n")
    line_height = 88
    total_height = len(lines) * line_height
    start_y = (1080 - total_height) // 2 - 40

    for i, line in enumerate(lines):
        y = start_y + i * line_height
        # Shadow
        draw.text((55, y + 4), line, font=font_big, fill=(0, 0, 0))
        # White text
        draw.text((50, y), line, font=font_big, fill=(255, 255, 255))

    # Bottom bar
    draw.rectangle([(0, 980), (1080, 1080)], fill=(20, 20, 20))
    draw.text((50, 1005), "Swipe left →", font=font_cta, fill=(200, 200, 200))

    # Red dot branding
    draw.ellipse([(30, 30), (65, 65)], fill=(220, 50, 50))

    output = BytesIO()
    bg.save(output, format="JPEG", quality=95)
    output.seek(0)
    return output


# ============================================
# Telegram Handlers
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Instagram Content Bot*\n\n"
        "Commands:\n"
        "📌 `/post <topic>` — Viral post বানাও\n"
        "📌 `/auto` — Auto trending post\n"
        "📌 `/help` — Help\n\n"
        "Example: `/post Apple buying Formula 1`",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Examples:*\n\n"
        "`/post Apple buying Formula 1`\n"
        "`/post 5 habits of millionaires`\n"
        "`/post Why 99% fail at marketing`\n\n"
        "Bot দেবে:\n"
        "🖼 Viral image\n"
        "📝 Caption\n"
        "#️⃣ 30 Hashtags",
        parse_mode="Markdown"
    )

async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args)
    if not topic:
        await update.message.reply_text(
            "❌ Topic দাও!\nExample: `/post Apple buying Formula 1`",
            parse_mode="Markdown"
        )
        return

    msg = await update.message.reply_text("⏳ Generating viral post...")

    try:
        content = generate_content(topic)
        headline = content.get("headline", topic.upper())
        caption = content.get("caption", "")
        hashtags = content.get("hashtags", "")

        image_bytes = create_post_image(headline, topic)
        full_caption = f"{caption}\n\n{hashtags}"

        await update.message.reply_photo(
            photo=image_bytes,
            caption=full_caption[:1024]
        )
        if len(full_caption) > 1024:
            await update.message.reply_text(hashtags)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}\nআবার চেষ্টা করো!")


async def auto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topics = [
        "Why most startups fail in first year",
        "Elon Musk secret business strategy",
        "How AI is replacing marketing jobs",
        "5 habits of self-made millionaires",
        "Why 99% people never become rich",
        "Apple secret product launch strategy",
        "How Instagram algorithm really works",
        "Warren Buffett investing rules for beginners",
        "Why personal brand is your best asset",
        "How to make money while you sleep"
    ]
    topic = random.choice(topics)
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
