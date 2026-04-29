import requests
import os
from backend.utils.logger import logger

class LastFMClient:
    def __init__(self):
        self.api_key = os.getenv("LASTFM_API_KEY")
        self.base_url = "http://ws.audioscrobbler.com/2.0/"

    def get_similar_artists(self, artist_name, limit=3):
        params = {
            "method": "artist.getsimilar",
            "artist": artist_name,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit
        }
        try:
            res = requests.get(self.base_url, params=params)
            data = res.json()
            artists = [a['name'] for a in data.get('similarartists', {}).get('artist', [])]
            return artists
        except Exception as e:
            logger.error(f"LastFM Error: {e}")
            return []