import os
import feedparser
import requests
from telegram import Bot
from bs4 import BeautifulSoup
import openai
import random
import time

# =============== CONFIG ===============
BOT_TOKEN = os.getenv("BOT_TOKEN")              # Telegram bot token
CHANNEL_ID = os.getenv("CHANNEL_ID")            # Your channel username (e.g. "@ainewsfeed")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")    # OpenAI API key
openai.api_key = OPENAI_API_KEY

# AI news RSS feeds
RSS_FEEDS = [
    "https://www.artificialintelligence-news.com/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.theverge.com/artificial-intelligence/rss/index.xml",
]

bot = Bot(token=BOT_TOKEN)
posted_links = set()  # to prevent duplicates

# =============== GET NEWS ===============
def get_latest_articles():
    articles = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            link = entry.link
            if link not in posted_links:
                articles.append({
                    "title": entry.title,
                    "summary": getattr(entry, "summary", ""),
                    "link": link,
                })
    return articles

# =============== SUMMARIZE ===============
def summarize_text(text):
    prompt = f"Summarize this AI news in 2 short lines with emojis and key points:\n\n{text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print("Summarization error:", e)
        return text[:150] + "..."

# =============== FIND IMAGE ===============
def find_image(url):
    try:
        html = requests.get(url, timeout=8).text
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
    except:
        pass
    keywords = ["AI", "robot", "neural network", "technology", "machine learning"]
    return f"https://source.unsplash.com/600x400/?{random.choice(keywords)}"

# =============== POST TO TELEGRAM ===============
def post_article(article):
    summary = summarize_text(article["summary"] or article["title"])
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

# =============== MAIN LOOP ===============
def main():
    print("🤖 AI News Bot started...")
    while True:
        try:
            articles = get_latest_articles()
            for article in articles:
                post_article(article)
                time.sleep(10)  # avoid Telegram spam limit
        except Exception as e:
            print("⚠️ Error:", e)

        # check for new news every hour
        print("⏳ Waiting 1 hour for next update...")
        time.sleep(3600)

if __name__ == "__main__":
    main()
