import requests
import feedparser
import threading
import time

class ThreatIntelAggregator:
    def __init__(self):
        self.intel_data = {}
        self.feeds = [
            ("CISA", "https://www.cisa.gov/news-events/cybersecurity-advisories.xml"),
            ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
            ("KrebsOnSecurity", "https://krebsonsecurity.com/feed/"),
            ("TheHackerNews", "https://thehackernews.com/feeds/posts/default"),
            ("RedditNetSec", "https://www.reddit.com/r/netsec/.rss"),
            ("RedditHacking", "https://www.reddit.com/r/hacking/.rss"),
            ("HaveIBeenPwned", "https://haveibeenpwned.com/Feed/AllBreaches"),
        ]
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def fetch_rss(self, url, max_items=5):
        try:
            d = feedparser.parse(url)
            return [(entry.title, entry.link) for entry in d.entries[:max_items]]
        except Exception as e:
            return [("Feed Error", str(e))]

    def fetch_all(self):
        data = {}
        for name, url in self.feeds:
            results = self.fetch_rss(url)
            data[name] = results
        self.intel_data = data
        return data

    def background_refresh(self, interval=1800):
        while True:
            try:
                self.fetch_all()
            except Exception as e:
                print(f"ThreatIntelAggregator fetch error: {e}")
            time.sleep(interval)

    def start_background(self, interval=1800):
        t = threading.Thread(target=self.background_refresh, args=(interval,), daemon=True)
        t.start()
