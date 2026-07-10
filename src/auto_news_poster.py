import os
import feedparser
import requests
from google import genai
from google.genai import types
from google.genai.errors import APIError

MAKE_WEBHOOK_URL = "https://hook.us2.make.com/8j58x1cnz4yytbn3avfqfer75cp49l3g"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]

def get_latest_news():
    rss_url = "https://feeds.feedburner.com/dawn-news"
    feed = feedparser.parse(rss_url)
    if feed.entries:
        entry = feed.entries[0]
        return {"title": entry.title, "summary": entry.summary, "link": entry.link}
    return None

def generate_seo_post_with_fallback(news_data):
    if not GEMINI_API_KEY:
        raise Exception("❌ GEMINI_API_KEY environment variable nahi mila.")
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    system_instruction = """
    Aap Pakistan ke top digital news editor aur SEO expert hain. 
    News ko engaging, human-like Roman Urdu mein Facebook post ke liye rewrite karein.
    Structure: Catchy Hook, Main Story, Bullet Points, Call to Action, aur Trending Hashtags.
    """

    prompt = f"Title: {news_data['title']}\nDetails: {news_data['summary']}\nSource: {news_data['link']}"
    config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.7)

    for model_name in AVAILABLE_MODELS:
        try:
            print(f"🔄 Trying: {model_name}...")
            response = client.models.generate_content(model=model_name, contents=prompt, config=config)
            return response.text
        except Exception:
            print(f"⚠️ {model_name} failed. Trying next...")

    raise Exception("❌ All Gemini models failed.")

def process_and_push():
    news = get_latest_news()
    if not news:
        print("❌ No news found.")
        return

    try:
        seo_post = generate_seo_post_with_fallback(news)
    except Exception as err:
        print(err)
        return

    payload = {"original_title": news["title"], "post_content": seo_post, "source_url": news["link"], "platform": "Facebook"}
    response = requests.post(MAKE_WEBHOOK_URL, json=payload)
    
    if response.status_code == 200:
        print("🚀 Success! Sent to Make.com")
    else:
        print(f"❌ Failed. Status: {response.status_code}")

if __name__ == "__main__":
    process_and_push()
