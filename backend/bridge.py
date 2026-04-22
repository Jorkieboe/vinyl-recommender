import threading
import numpy as np
import os
from backend.deezer_client import DeezerClient
from backend.database import Database
from backend.llm_advisor import LLMAdvisor
from backend.scraper import MarketplaceScraper

class Bridge:
    def __init__(self):
        self.db = Database()
        self.client = DeezerClient()
        self.advisor = LLMAdvisor()
        self.scraper = MarketplaceScraper(self.advisor)

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

            for track in tracks:
                # Check if already processed
                if self.db.get_track_preference(track['id']):
                    continue

                # Fetch full track data for preview URL
                track_data = self.client.get_track(track['id'])
                if not track_data or not track_data.get('preview'):
                    continue

                print(f"Processing: {track_data['title']}")

                # Download and Analyze
                preview_path = self.client.download_preview(track_data['preview'], track_data['id'])
                if preview_path:
                    features = self.client.analyze_audio(preview_path)
                    if features:
                        # Extract cover art URL
                        print(track_data.get('album', {}))
                        cover_url = track_data.get('album', {}).get('cover_medium', '')
                        self.db.save_track_preference(track_data, features, cover_url)

                    # Cleanup
                    try:
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

    def get_synced_tracks(self):
        """Returns all synced tracks from the database"""
        return self.db.get_all_synced_tracks()

    def _calculate_similarity(self, feat_a, feat_b):
        """Simple Euclidean distance based similarity (0 to 1)"""
        # MFCC
        dist_mfcc = np.linalg.norm(np.array(feat_a['mfcc']) - np.array(feat_b['mfcc']))
        # Chroma
        dist_chroma = np.linalg.norm(np.array(feat_a['chroma']) - np.array(feat_b['chroma']))

        # Heuristic normalization
        score = 1 / (1 + (0.01 * dist_mfcc) + (0.5 * dist_chroma))
        return float(score)

    def get_album_analysis(self, album_id):
        """Returns cached analysis for an album if it exists"""
        cached = self.db.get_scanned_album(album_id)
        if cached:
            return {"status": "success", "data": cached}
        return {"status": "not_found"}

    def analyze_album_for_track(self, track_id):
        """
        Full logic: Find album -> Analyze all tracks -> Compare to Centroid -> LLM Insight -> Scrape
        """
        track_meta = self.client.get_track(track_id)
        if not track_meta:
            return {"status": "error", "message": "Track not found"}

        album_id = track_meta['album']['id']
        cached = self.db.get_scanned_album(album_id)
        if cached:
            return {"status": "success", "data": cached}

        def analysis_worker():
            print(f"Analyzing album: {track_meta['album']['title']}")

            # 1. Get User Taste Centroid
            all_features = self.db.get_all_features()
            if not all_features:
                print("No user preferences found. Please sync first.")
                return

            # Compute mean vectors for the centroid
            centroid = {
                "mfcc": np.mean([f['mfcc'] for f in all_features], axis=0).tolist(),
                "chroma": np.mean([f['chroma'] for f in all_features], axis=0).tolist(),
                "spectral_brightness": np.mean([f['spectral_brightness'] for f in all_features])
            }

            # 2. Get Album Tracks
            album_tracks = self.client.get_album_tracks(album_id)
            track_scores = []

            for t in album_tracks:
                # We need the preview URL, so fetch full track info
                full_t = self.client.get_track(t['id'])
                if not full_t or not full_t.get('preview'):
                    continue

                path = self.client.download_preview(full_t['preview'], full_t['id'])
                if path:
                    feats = self.client.analyze_audio(path)
                    if feats:
                        similarity = self._calculate_similarity(feats, centroid)
                        track_scores.append({
                            "title": full_t['title'],
                            "similarity": similarity
                        })
                    os.remove(path)

            # 3. Get LLM Breakdown
            album_info = {
                "title": track_meta['album']['title'],
                "artist": track_meta['artist']['name'],
                "cover_url": track_meta['album'].get('cover_medium', '')
            }
            insight = self.advisor.get_album_insight(album_info, track_scores, centroid)

            # 4. Marketplace Scraper (Triggered if score > 65)
            acquisition_links = []
            if insight.get('confidence_score', 0) > 65:
                print(f"Score high ({insight['confidence_score']}%). Triggering marketplace search...")
                acquisition_links = self.scraper.get_links(album_info['artist'], album_info['title'])
                insight['acquisition_links'] = acquisition_links

            # 5. Save to DB
            self.db.save_scanned_album(
                album_id,
                album_info['title'],
                album_info['artist'],
                insight['confidence_score'],
                insight,
                album_info['cover_url']
            )
            print(f"Analysis complete for {album_info['title']}")

        threading.Thread(target=analysis_worker, daemon=True).start()
        return {"status": "pending", "message": "Album analysis started", "album_id": album_id}

    def test_clap_on_track(self, track_id):
        """Tests natural language audio tagging via CLAP for a single track"""
        track_meta = self.client.get_track(track_id)
        if not track_meta:
            return {"status": "error", "message": "Track not found"}

        # Return cached CLAP results if available
        cached = self.db.get_clap_result(track_id)
        if cached:
            return {"status": "success", "data": cached}

        def worker():
            print(f"Starting CLAP analysis for track {track_id}")
            path = self.client.download_preview(track_meta['preview'], track_meta['id'])
            if path:
                try:
                    # Lazy load CLAP Analyzer to prevent huge startup delay
                    from backend.clap_analyzer import ClapAnalyzer
                    if not hasattr(self, 'clap_analyzer'):
                        self.clap_analyzer = ClapAnalyzer()

                    results = self.clap_analyzer.analyze(path)
                    if results:
                        self.db.save_clap_result(track_id, results)
                        print(f"CLAP Analysis complete for {track_meta['title']}")
                except Exception as e:
                    print(f"CLAP Error: {e}")
                finally:
                    if os.path.exists(path):
                        os.remove(path)

        threading.Thread(target=worker, daemon=True).start()
        return {"status": "pending", "message": "CLAP analysis started", "track_id": track_id}

    def get_clap_result(self, track_id):
        """Returns cached CLAP analysis for a track"""
        res = self.db.get_clap_result(track_id)
        if res:
            return {"status": "success", "data": res}
        return {"status": "pending"}