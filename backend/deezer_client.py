import requests
import librosa
import numpy as np
import os
import tempfile

class DeezerClient:
    BASE_URL = "https://api.deezer.com"

    def get_loved_tracks(self, user_id):
        """Fetches the 'Loved Tracks' for a specific user ID"""
        try:
            # Note: For production, this would use OAuth tokens
            # For this MVP, we assume public profiles or a provided ID
            response = requests.get(f"{self.BASE_URL}/user/{user_id}/tracks")
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            print(f"Error fetching loved tracks: {e}")
            return []

    def get_track(self, track_id):
        """Fetches the 'Loved Tracks' for a specific user ID"""
        try:
            print(track_id)
            response = requests.get(f"{self.BASE_URL}/track/{track_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching track: {e}")
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
            print(f"Error downloading preview: {e}")
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
            print(f"Error analyzing audio: {e}")
            return None