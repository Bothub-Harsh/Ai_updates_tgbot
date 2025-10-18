import os
import feedparser
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI
from telegram import Bot
import random
from flask import Flask

# ---------- ENV VARIABLES ----------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")

# ---------- RSS FEEDS ----------
RSS_FEEDS = [
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://the-decoder.com/feed/",
    "https://www.technologyreview.com/feed/"
]

# ---------- FALLBACK IMAGES ----------
FALLBACK_IMAGES = [
    "https://cdn.pixabay.com/photo/2016/11/29/02/23/artificial-intelligence-1867436_1280.jpg",
    "https://cdn.pixabay.com/photo/2017/09/04/18/12/artificial-intelligence-2718835_1280.jpg",
    "https://cdn.pixabay.com/photo/2023/01/10/10/18/robot-7709864_1280.jpg",
    "https://cdn.pixabay.com/photo/2022/06/28/11/03/ai-7289292_1280.jpg"
]

# ---------- INITIAL SETUP ----------
client = OpenAI(api_key=OPENAI_API_KEY)
bot = Bot(token=TELEGRAM_BOT_TOKEN)
posted_links = set()

# ---------- FUNCTIONS ----------
def summarize_text(text):
    try:
        prompt = f"Summarize this AI news in 2 short, engaging lines with emojis:\n{text}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except:
        return text[:200] + "..."

def get_image_from_article(url):
    try:
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        for tag in ["og:image", "twitter:image"]:
            img_tag = soup.find("meta", property=tag)
            if img_tag and img_tag.get("content"):
                return img_tag["content"]
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
    except:
        pass
    return random.choice(FALLBACK_IMAGES)

def fetch_and_post_news():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            title = entry.title
            link = entry.link
            if link in posted_links:
                continue
            summary_text = entry.get("summary", title)
            summary = summarize_text(summary_text)
            image_url = get_image_from_article(link)
            caption = f"🧠 <b>{title}</b>\n\n{summary}\n\n🔗 <a href='{link}'>Read full article</a>"
            try:
                bot.send_photo(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    photo=image_url,
                    caption=caption,
                    parse_mode="HTML"
                )
                print(f"✅ Posted: {title}")
                posted_links.add(link)
                time.sleep(5)
            except Exception as e:
                print("⚠️ Telegram post error:", e)

# ---------- FLASK WEB SERVER ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AI News Bot is running on Render!"

# ---------- MAIN LOOP ----------
def run_bot():
    print("🚀 AI News Bot running on Render Web Service...")
    while True:
        fetch_and_post_news()
        print(f"⏰ Checked at {datetime.now().strftime('%H:%M:%S')}")
        time.sleep(3600)  # hourly updates

if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
