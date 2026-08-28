import urllib.request
import urllib.parse
import re
import time

def get_direct_youtube_play_url(query: str) -> str:
    """Searches YouTube and returns direct video watch URL with autoplay."""
    try:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        html = urllib.request.urlopen(req, timeout=4).read().decode("utf-8")
        video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
        if video_ids:
            # First unique valid video id
            return f"https://www.youtube.com/watch?v={video_ids[0]}&autoplay=1"
    except Exception as e:
        print(f"[YouTube Scraper Fallback] {e}")
    
    # Fallback to search results
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"

if __name__ == "__main__":
    t0 = time.time()
    direct_url = get_direct_youtube_play_url("latest trending songs")
    print(f"Direct Play URL ({int((time.time()-t0)*1000)}ms): {direct_url}")
