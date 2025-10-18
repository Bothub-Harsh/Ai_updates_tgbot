import os
import feedparser
import requests
from telegram import Bot
from bs4 import BeautifulSoup
import openai
import random
import time

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

bot = Bot(token=BOT_TOKEN)
posted_links = set()

RSS_FEEDS = [
    "https://www.artificialintelligence-news.com/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.theverge.com/artificial-intelligence/rss/index.xml",
]

def get_latest_articles():
    articles = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:2]:
            if entry.link not in posted_links:
                articles.append({
                    "title": entry.title,
                    "summary": getattr(entry, "summary", ""),
                    "link": entry.link,
                })
    return articles

def summarize(text):
    prompt = f"Summarize this AI news in 2 lines with emojis:\n\n{text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print("Summarization error:", e)
        return text[:150] + "..."

def find_image(url):
    try:
        html = requests.get(url, timeout=8).text
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
    except:
        pass
    keywords = ["AI", "robot", "neural network", "machine learning"]
    return f"https://source.unsplash.com/600x400/?{random.choice(keywords)}"

def post_to_telegram(article):
    summary = summarize(article["summary"] or article["title"])
    image_url = find_image(article["link"])
    message = (
        f"📰 *{article['title']}*\n\n"
        f"{summary}\n\n"
        f"🔗 [Read full article]({article['link']})"
    )
    try:
        bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=image_url,
            caption=message,
            parse_mode="Markdown"
        )
        posted_links.add(article["link"])
        print(f"✅ Posted: {article['title']}")
    except Exception as e:
        print("❌ Telegram post error:", e)

def main():
    print("🤖 Bot started successfully — running on Render...")
    while True:
        try:
            articles = get_latest_articles()
            for article in articles:
                post_to_telegram(article)
                time.sleep(10)
        except Exception as e:
            print("⚠️ Error:", e)

        print("🕒 Waiting 1 hour for next check...")
        time.sleep(3600)

if __name__ == "__main__":
    main()
