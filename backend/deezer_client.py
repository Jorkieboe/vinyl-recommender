import requests
import librosa
import numpy as np
import os
import tempfile
from backend.utils.logger import logger

class DeezerClient:
    def __init__(self, bridge):
        self.BASE_URL = "https://api.deezer.com"
        self.bridge = bridge

    def get_loved_tracks(self, user_id):
        """Fetches the 'Loved Tracks' for a specific user ID (Top 50 via pagination)"""
        all_tracks = []
        # Paginate to get up to 50 tracks as requested
        for index in [0, 25]:
            try:
                # Note: For production, this would use OAuth tokens
                # For this MVP, we assume public profiles or a provided ID
                response = requests.get(f"{self.BASE_URL}/user/{user_id}/charts?index={index}")
                response.raise_for_status()
                data = response.json().get('data', [])
                all_tracks.extend(data)
            except Exception as e:
                logger.error(f"Error fetching loved tracks at index {index}: {e}")

        return all_tracks

    def get_user_flow(self, user_id):
        """Fetches the personalized 'Flow' tracks for a user"""
        try:
            response = requests.get(f"{self.BASE_URL}/user/{user_id}/flow")
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Error fetching user flow: {e}")
            return []

    def get_track(self, track_id):
        """Fetches track metadata"""
        try:
            response = requests.get(f"{self.BASE_URL}/track/{track_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching track: {e}")
            return None

    def get_album_by_artist(self, query):
        """Searches for albums by a specific artist and returns the first matching ID"""
        try:
            logger.ai(f'Searching Deezer for artist: {query}')
            response = requests.get(f"{self.BASE_URL}/search/album?q=artist:\"{query}\"&limit=5")
            response.raise_for_status()
            res = response.json()

            albums = res.get('data', [])

            for alb in albums:
                alb_id = alb.get('id')
                artist_name = alb.get('artist', {}).get('name', '')

                # Check if it's the correct artist
                if artist_name.lower() != query.lower():
                    continue

                cached = self.bridge.db.get_scanned_album(alb_id)

                # If never scanned before, it's a perfect candidate
                if not cached:
                    return alb_id, alb.get('title', '')

                # If scanned before, check if it should be skipped
                if cached.get('is_recommended') == 1:
                    logger.ai(f"Skipping {alb.get('title')} - Already recommended.")
                    continue

                if cached.get('confidence_score', 0) < 50:
                    logger.ai(f"Skipping {alb.get('title')} - Low match score ({cached.get('confidence_score')}%).")
                    continue

                logger.ai(f"Re-evaluating previously scanned album: {alb.get('title')}")
                return alb_id, alb.get('title', '')

            return None
        except Exception as e:
            logger.error(f"Error searching album by artist: {e}")
            return None

    def get_album(self, album_id):
        """Fetches album metadata"""
        try:
            response = requests.get(f"{self.BASE_URL}/album/{album_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching album {album_id}: {e}")
            return None

    def get_album_tracks(self, album_id):
        """Fetches all tracks for a specific album"""
        try:
            response = requests.get(f"{self.BASE_URL}/album/{album_id}/tracks")
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Error fetching album tracks: {e}")
            return []

    def download_preview(self, url, track_id):
        """Downloads the 30s preview to a temporary file"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"track_{track_id}.mp3")

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return file_path
        except Exception as e:
            logger.error(f"Error downloading preview: {e}")
            return None

    def analyze_audio(self, file_path):
        """Extracts key audio features using Librosa"""
        try:
            # Load the audio file
            y, sr = librosa.load(file_path, duration=30)

            # MFCCs (Timbre)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfccs_avg = np.mean(mfccs, axis=1).tolist()

            # Chroma (Harmonic content)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_avg = np.mean(chroma, axis=1).tolist()

            # Spectral Centroid (Brightness)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            spectral_avg = np.mean(spectral_centroid).tolist()

            # Tempo
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

            return {
                "mfcc": mfccs_avg,
                "chroma": chroma_avg,
                "spectral_brightness": spectral_avg,
                "tempo": float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
            }
        except Exception as e:
            logger.error(f"Error analyzing audio: {e}")
            return None