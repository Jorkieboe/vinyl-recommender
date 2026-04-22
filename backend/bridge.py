import threading
import numpy as np
import os
from backend.deezer_client import DeezerClient
from backend.database import Database
from backend.llm_advisor import LLMAdvisor
from backend.scraper import MarketplaceScraper
from backend.profile_engine import ProfileEngine, ClusterEngine

class Bridge:
    def __init__(self):
        self.db = Database()
        self.client = DeezerClient()
        self.advisor = LLMAdvisor()
        self.scraper = MarketplaceScraper(self.advisor)
        self.profile_engine = ProfileEngine()
        self.cluster_engine = ClusterEngine(n_clusters=5)

    def echo(self, text):
        """Simple echo function to test the bridge"""
        print(f"JS call to echo: {text}")
        return f"Python received: {text}"

    def get_default_user(self):
        """Returns the default user ID from environment variables"""
        return os.getenv("DEFAULT_USER", "2529")

    def start_initial_sync(self, user_id):
        """
        Starts the background process to fetch loved tracks,
        extract audio features, and perform CLAP analysis.
        """
        def sync_worker():
            print(f"Starting sync for user: {user_id}")
            tracks = self.client.get_loved_tracks(user_id)

            for track in tracks:
                track_data = self.client.get_track(track['id'])
                if not track_data or not track_data.get('preview'):
                    continue

                needs_features = not self.db.get_track_preference(track['id'])
                needs_clap = not self.db.get_clap_result(track['id'])

                # Consolidate download to one single session per track
                if needs_features or needs_clap:
                    print(f"Syncing {track_data['title']}...")
                    preview_path = self.client.download_preview(track_data['preview'], track_data['id'])
                    if not preview_path:
                        continue

                    try:
                        # 1. Librosa Audio Features
                        if needs_features:
                            features = self.client.analyze_audio(preview_path)
                            if features:
                                cover_url = track_data.get('album', {}).get('cover_medium', '')
                                self.db.save_track_preference(track_data, features, cover_url)

                        # 2. CLAP AI Semantic Tagging
                        if needs_clap:
                            from backend.clap_analyzer import ClapAnalyzer
                            if not hasattr(self, 'clap_analyzer'):
                                self.clap_analyzer = ClapAnalyzer()

                            results = self.clap_analyzer.analyze(preview_path)
                            if results:
                                self.db.save_clap_result(track['id'], results)
                    except Exception as e:
                        print(f"Sync Error for {track_data['title']}: {e}")
                    finally:
                        if os.path.exists(preview_path):
                            os.remove(preview_path)

            # 3. Finalize Global Profile via RRF
            print("Sync complete. Generating global Sonic DNA Profile...")
            self.recalculate_user_profile()

        threading.Thread(target=sync_worker, daemon=True).start()
        return {"status": "success", "message": "Sync started in background"}

    def recalculate_user_profile(self):
        """Triggers RRF calculation across all synced tracks"""
        all_results = self.db.get_all_clap_results()
        if all_results:
            profile = self.profile_engine.calculate_rrf(all_results)
            self.db.save_global_profile(profile)
            return {"status": "success", "profile": profile}
        return {"status": "error", "message": "No data for profile calculation"}

    def get_user_profile(self):
        """Returns the current aggregated Sonic DNA profile"""
        profile = self.db.get_global_profile()
        if profile:
            return {"status": "success", "data": profile}
        return {"status": "pending"}

    def get_sync_status(self):
        """Returns the count of processed tracks"""
        count = self.db.get_preference_count()
        return {"count": count}

    def get_synced_tracks(self):
        """Returns all synced tracks from the database"""
        return self.db.get_all_synced_tracks()

    def get_album_analysis(self, album_id):
        """Returns cached analysis for an album if it exists"""
        cached = self.db.get_scanned_album(album_id)
        if cached:
            return {"status": "success", "data": cached}
        return {"status": "not_found"}

    def analyze_album_for_track(self, track_id):
        """
        Full logic: Find album -> Analyze all tracks -> Compare to Taste Clusters -> LLM Insight -> Scrape
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

            # 1. Prepare User Taste Clusters
            all_features = self.db.get_all_features()
            if not all_features:
                print("No user preferences found. Please sync first.")
                return

            self.cluster_engine.fit_clusters(all_features)

            # 2. Get Album Tracks and score against nearest cluster
            album_tracks = self.client.get_album_tracks(album_id)
            track_scores = []
            album_feature_history = []

            for t in album_tracks:
                full_t = self.client.get_track(t['id'])
                if not full_t or not full_t.get('preview'):
                    continue

                path = self.client.download_preview(full_t['preview'], full_t['id'])
                if path:
                    feats = self.client.analyze_audio(path)
                    if feats:
                        album_feature_history.append(feats)
                        similarity = self.cluster_engine.get_best_similarity(feats)
                        track_scores.append({
                            "title": full_t['title'],
                            "similarity": similarity
                        })
                    os.remove(path)

            # 3. Calculate Sonic Journey & Math-Based Confidence
            journey_data = {
                "anchors": 0,        # Instant Comfort (>0.80)
                "inner_bridges": 0,  # Near-term Growth (0.70 - 0.80)
                "outer_bridges": 0,  # Challenging Expansion (0.60 - 0.70)
                "horizon": 0,        # Experimental/Risky (<0.60)
                "is_repetitive": False,
                "calculated_score": 0
            }

            if track_scores:
                sims = [s['similarity'] for s in track_scores]
                n_anchors = len([s for s in sims if s >= 0.80])
                n_inner = len([s for s in sims if 0.70 <= s < 0.80])
                n_outer = len([s for s in sims if 0.60 <= s < 0.70])
                n_horizon = len([s for s in sims if s < 0.60])

                journey_data.update({
                    "anchors": n_anchors,
                    "inner_bridges": n_inner,
                    "outer_bridges": n_outer,
                    "horizon": n_horizon
                })

                # --- Core Decision Logic (Exploration-First Voting System) ---
                # Weights adjusted to favor albums with strong comfort bases (Anchors)
                # and discovery potential (Inner Bridges)
                buy_votes = (n_anchors * 4) + (n_inner * 2) + (n_outer * 1) + (n_horizon * 0)

                # Total possible votes per tier for normalization
                # Anchors: 4, Inner: 2, Outer: 3, Horizon: 3
                total_possible_votes = (n_anchors * 4) + (n_inner * 2) + (n_outer * 3) + (n_horizon * 3)

                # Calculate percentage of positive evidence
                calculated_score = int((buy_votes / total_possible_votes) * 100) if total_possible_votes > 0 else 0

                # Hard Gate: No vinyl purchase without at least one instant hook (Anchor)
                if n_anchors == 0:
                    calculated_score = min(calculated_score, 30)

                journey_data["calculated_score"] = calculated_score

                if len(album_feature_history) > 1:
                    flattened_alb = np.array([self.cluster_engine._flatten(f) for f in album_feature_history])
                    scaled_alb = self.cluster_engine.scaler.transform(flattened_alb)
                    alb_dispersion = np.mean(np.std(scaled_alb, axis=0))
                    if alb_dispersion < 0.05:
                        journey_data["is_repetitive"] = True

            # Generate Visualization Map for Debugging
            if album_feature_history:
                self.cluster_engine.generate_taste_map(album_feature_history, track_meta['album']['title'])

            # 4. Get LLM Breakdown
            album_info = {
                "title": track_meta['album']['title'],
                "artist": track_meta['artist']['name'],
                "cover_url": track_meta['album'].get('cover_medium', '')
            }
            insight = self.advisor.get_album_insight(album_info, track_scores, journey_data)

            # 5. Marketplace Scraper (Triggered if score > 60 - lowered for potential growers)
            acquisition_links = []
            if insight.get('confidence_score', 0) > 60:
                print(f"Score promising ({insight['confidence_score']}%). Triggering marketplace search...")
                acquisition_links = self.scraper.get_links(album_info['artist'], album_info['title'])
                insight['acquisition_links'] = acquisition_links

            # 6. Save to DB
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

        # Return cached CLAP results if available (formatted for UI)
        cached_res = self.get_clap_result(track_id)
        if cached_res["status"] == "success":
            return cached_res

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
        """Returns cached CLAP analysis for a track with raw probabilities sorted by rank"""
        res = self.db.get_clap_result(track_id)
        if res:
            # Sort and filter to Top 3 for the UI, but keep probabilities as pairs [label, prob]
            ui_res = {}
            for layer, labels in res.items():
                sorted_labels = sorted(labels.items(), key=lambda x: x[1], reverse=True)
                # Convert dict items to list of lists for JS compatibility
                ui_res[layer] = [[label, prob] for label, prob in sorted_labels[:3]]
            return {"status": "success", "data": ui_res}
        return {"status": "pending"}