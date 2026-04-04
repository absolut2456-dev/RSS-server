import os
import requests
from flask import Flask, Response, request

# Railway assigns PORT; default fallback for local run
PORT = int(os.environ.get("PORT", 8080))
app = Flask(__name__)

DEFAULT_SUBREDDIT = "funny"

def fetch_reddit_json(subreddit: str, limit: int = 25) -> dict:
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {"User-Agent": "n8n-reddit-rss-bot/1.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

def build_rss(reddit_json: dict, subreddit: str, limit: int = 25) -> str:
    items = reddit_json.get("data", {}).get("children", [])[:limit]
    rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
    rss += '<rss version="2.0">\n<channel>\n'
    rss += f'<title>Reddit r/{subreddit}</title>\n'
    rss += f'<link>https://www.reddit.com/r/{subreddit}/</link>\n'
    rss += f'<description>RSS feed for Reddit /r/{subreddit} (hot)</description>\n'
    rss += '<language>en-us</language>\n'
    for item in items:
        data = item.get("data", {})
        title = data.get("title", "No Title").replace("&", "&amp;")
        permalink = data.get("permalink", "")
        link = f"https://www.reddit.com{permalink}"
        rss += '<item>\n'
        rss += f'<title>{title}</title>\n'
        rss += f'<link>{link}</link>\n'
        rss += '</item>\n'
    rss += '</channel>\n</rss>'
    return rss

@app.route('/<subreddit>')
def rss_feed(subreddit: str):
    try:
        limit = 25
        if 'limit' in request.args:
            try:
                limit = int(request.args.get('limit', 25))
            except ValueError:
                limit = 25
        data = fetch_reddit_json(subreddit, limit=limit)
        rss = build_rss(data, subreddit, limit=limit)
        return Response(rss, mimetype='application/xml')
    except requests.HTTPError as e:
        return Response(f"HTTP error: {e}", status=500)
    except Exception as e:
        return Response(str(e), status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)