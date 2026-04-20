import os
import requests
import concurrent.futures
from flask import Flask, Response, request

PORT = int(os.environ.get("PORT", 8080))
app = Flask(__name__)

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "3a09b58fa2224fe58ff9b58d5759a5ee")

@app.route('/')
def index():
    return """RSS Server endpoints:
/hn - Hacker News top stories
/news?category=technology&language=en - NewsAPI headlines
/bbcworld - BBC World News
/techcrunch - TechCrunch
/ign - IGN Gaming News
/nasa - NASA News
"""

@app.route('/hn')
def hackernews_rss():
    try:
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
        resp.raise_for_status()
        story_ids = resp.json()[:20]

        def fetch_item(sid):
            try:
                r = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=5)
                return r.json() if r.status_code == 200 else None
            except:
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            items = list(executor.map(fetch_item, story_ids))
        items = [i for i in items if i]

        rss = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
        rss += '<title>Hacker News Top Stories</title>\n'
        rss += '<link>https://news.ycombinator.com/</link>\n'
        rss += '<description>Top stories from Hacker News</description>\n'
        for item in items:
            title = item.get('title', 'No Title').replace('&', '&amp;')
            url = item.get('url', f"https://news.ycombinator.com/item?id={item.get('id')}")
            rss += f'<item>\n<title>{title}</title>\n<link>{url}</link>\n</item>\n'
        rss += '</channel>\n</rss>'
        return Response(rss, mimetype='application/xml')
    except Exception as e:
        return Response(f"HN error: {e}", status=500)

@app.route('/news')
def newsapi_rss():
    try:
        category = request.args.get('category', 'technology')
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
        rss += f'<description>Top headlines: {category}, {language}</description>\n'
        for art in articles:
            title = art.get('title', 'No title').replace('&', '&amp;')
            link = art.get('url', '')
            desc = art.get('description', '') or ''
            desc = desc.replace('&', '&amp;')
            rss += f'<item>\n<title>{title}</title>\n<link>{link}</link>\n<description>{desc}</description>\n</item>\n'
        rss += '</channel>\n</rss>'
        return Response(rss, mimetype='application/xml')
    except Exception as e:
        return Response(f"NewsAPI error: {e}", status=500)

def proxy_rss(url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return Response(resp.content, mimetype='application/xml')
    except Exception as e:
        return Response(f"Error: {e}", status=500)

@app.route('/bbcworld')
def bbc_world():
    return proxy_rss("http://feeds.bbci.co.uk/news/world/rss.xml")

@app.route('/bbctech')
def bbc_tech():
    return proxy_rss("http://feeds.bbci.co.uk/news/technology/rss.xml")

@app.route('/techcrunch')
def techcrunch():
    return proxy_rss("https://techcrunch.com/feed/")

@app.route('/ign')
def ign():
    return proxy_rss("https://feeds.ign.com/ign/all")

@app.route('/nasa')
def nasa():
    return proxy_rss("https://www.nasa.gov/rss/dyn/breaking_news.rss")

@app.route('/verge')
def verge():
    return proxy_rss("https://www.theverge.com/rss/index.xml")

@app.route('/wired')
def wired():
    return proxy_rss("https://www.wired.com/feed/rss")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
