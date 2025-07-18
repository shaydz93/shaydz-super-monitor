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
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            d = feedparser.parse(response.content)
            if d.bozo:
                return [("Feed Parse Error", f"Malformed feed: {url}")]
            return [(entry.title, entry.link) for entry in d.entries[:max_items]]
        except requests.exceptions.RequestException as e:
            return [("Network Error", f"Failed to fetch {url}: {str(e)}")]
        except Exception as e:
            return [("Feed Error", f"Error processing {url}: {str(e)}")]

    def fetch_all(self):
        data = {}
        for name, url in self.feeds:
            try:
                results = self.fetch_rss(url)
                data[name] = results
            except Exception as e:
                data[name] = [("Error", f"Failed to fetch {name}: {str(e)}")]
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
