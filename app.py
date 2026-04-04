import os
import requests
from flask import Flask, Response, request

PORT = int(os.environ.get("PORT", 8080))
app = Flask(__name__)

# ---------- NewsAPI key (лучше вынести в переменную окружения) ----------
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "3a09b58fa2224fe58ff9b58d5759a5ee")

# ---------- Reddit ----------
def fetch_reddit_json(subreddit: str, limit: int = 25) -> dict:
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {"User-Agent": "n8n-reddit-rss-bot/1.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

def build_reddit_rss(reddit_json: dict, subreddit: str, limit: int = 25) -> str:
    items = reddit_json.get("data", {}).get("children", [])[:limit]
    rss = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
    rss += f'<title>Reddit r/{subreddit}</title>\n'
    rss += f'<link>https://www.reddit.com/r/{subreddit}/</link>\n'
    rss += f'<description>RSS feed for Reddit /r/{subreddit} (hot)</description>\n'
    rss += '<language>en-us</language>\n'
    for item in items:
        data = item.get("data", {})
        title = data.get("title", "No Title").replace("&", "&amp;")
        link = f"https://www.reddit.com{data.get('permalink', '')}"
        rss += f'<item>\n<title>{title}</title>\n<link>{link}</link>\n</item>\n'
    rss += '</channel>\n</rss>'
    return rss

@app.route('/<subreddit>')
def rss_feed(subreddit: str):
    try:
        limit = request.args.get('limit', 25, type=int)
        data = fetch_reddit_json(subreddit, limit=limit)
        return Response(build_reddit_rss(data, subreddit, limit), mimetype='application/xml')
    except Exception as e:
        return Response(str(e), status=500)

# ---------- Hacker News ----------
@app.route('/hn')
def hackernews_rss():
    try:
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        resp = requests.get(top_url, timeout=10)
        resp.raise_for_status()
        story_ids = resp.json()[:30]

        items = []
        for sid in story_ids:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            item_resp = requests.get(item_url, timeout=10)
            if item_resp.status_code == 200:
                items.append(item_resp.json())

        rss = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
        rss += '<title>Hacker News Top Stories</title>\n'
        rss += '<link>https://news.ycombinator.com/</link>\n'
        rss += '<description>Top 30 stories from Hacker News</description>\n'
        for item in items:
            title = item.get('title', 'No Title').replace('&', '&amp;')
            url = item.get('url', f"https://news.ycombinator.com/item?id={item.get('id')}")
            rss += f'<item>\n<title>{title}</title>\n<link>{url}</link>\n</item>\n'
        rss += '</channel>\n</rss>'
        return Response(rss, mimetype='application/xml')
    except Exception as e:
        return Response(f"Hacker News error: {e}", status=500)

# ---------- NewsAPI ----------
@app.route('/news')
def newsapi_rss():
    try:
        category = request.args.get('category', 'science')
        language = request.args.get('language', 'en')
        page_size = request.args.get('pageSize', 20, type=int)

        params = {
            'apiKey': NEWS_API_KEY,
            'category': category,
            'language': language,
            'pageSize': page_size
        }
        resp = requests.get("https://newsapi.org/v2/top-headlines", params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get('articles', [])

        rss = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
        rss += f'<title>NewsAPI - {category} ({language})</title>\n'
        rss += '<link>https://newsapi.org/</link>\n'
        rss += f'<description>Top headlines from NewsAPI: category {category}, language {language}</description>\n'
        for art in articles:
            title = art.get('title', 'No title').replace('&', '&amp;')
            link = art.get('url', '')
            desc = art.get('description', '')
            if desc:
                desc = desc.replace('&', '&amp;')
            rss += f'<item>\n<title>{title}</title>\n<link>{link}</link>\n<description>{desc}</description>\n</item>\n'
        rss += '</channel>\n</rss>'
        return Response(rss, mimetype='application/xml')
    except Exception as e:
        return Response(f"NewsAPI error: {e}", status=500)

# ---------- Root ----------
@app.route('/')
def index():
    return "Reddit + Hacker News + NewsAPI RSS server is running. Use /<subreddit> or /hn or /news"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
