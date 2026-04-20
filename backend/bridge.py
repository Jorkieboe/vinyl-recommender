import threading
from backend.deezer_client import DeezerClient
from backend.database import Database

class Bridge:
    def __init__(self):
        self.db = Database()
        self.client = DeezerClient()

    def echo(self, text):
        """Simple echo function to test the bridge"""
        print(f"JS call to echo: {text}")
        return f"Python received: {text}"

    def start_initial_sync(self, user_id):
        """
        Starts the background process to fetch loved tracks
        and extract audio features.
        """
        def sync_worker():
            print(f"Starting sync for user: {user_id}")
            tracks = self.client.get_loved_tracks(user_id)
            # print(tracks['tracklist'])
            # for track in tracks:
            # 1. Check if already processed
            # if self.db.get_track_preference(tracks[0]['id']):
            #     continue

            track_data = self.client.get_track(tracks[1]['id'])

            print(track_data['preview'])

            # 2. Download and Analyze
            preview_path = self.client.download_preview(track_data['preview'], track_data['id'])
            if preview_path:
                features = self.client.analyze_audio(preview_path)
                if features:
                    # 3. Store in DB
                    print(features)
                    self.db.save_track_preference(tracks[1], features)

                # Cleanup downloaded file
                try:
                    import os
                    os.remove(preview_path)
                except:
                    pass    

            print("Sync complete.")

        threading.Thread(target=sync_worker, daemon=True).start()
        return {"status": "success", "message": "Sync started in background"}

    def get_sync_status(self):
        """Returns the count of processed tracks"""
        count = self.db.get_preference_count()
        return {"count": count}

    def analyze_album_for_track(self, track_id):
        """Mock for album analysis - to be implemented in next phase"""
        print(f"Starting analysis for track ID: {track_id}")
        return {"status": "pending", "track_id": track_id}