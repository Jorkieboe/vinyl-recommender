import threading
import asyncio
import numpy as np
import os
import re
from backend.deezer_client import DeezerClient
from backend.database import Database
from backend.llm_advisor import LLMAdvisor
from backend.scraper import MarketplaceScraper
from backend.profile_engine import ProfileEngine, ClusterEngine
from backend.utils.logger import logger
from backend.agent import Agentloop
from backend.lastfm_client import LastFMClient

class Bridge:
    def __init__(self):
        self.db = Database()
        self.client = DeezerClient()
        self.advisor = LLMAdvisor()
        self.lfmclient = LastFMClient()
        self.scraper = MarketplaceScraper(self.advisor)
        self.profile_engine = ProfileEngine()
        self.cluster_engine = ClusterEngine(n_clusters=5)
        self.headless_mode = False

    def echo(self, text):
        """Simple echo function to test the bridge"""
        logger.sync(f"JS call to echo: {text}")
        return f"Python received: {text}"

    def get_default_user(self):
        """Returns the default user ID from environment variables"""
        return os.getenv("DEFAULT_USER", "2529")

    def set_headless_mode(self, enabled):
        """Toggles whether the scraper browser is visible"""
        self.headless_mode = not enabled
        logger.scrape(f"Headless mode set to: {self.headless_mode}")

    def _count_unique_tracks(self, album_id):
        """Fetches album tracks and counts unique songs by cleaning titles"""
        tracks = self.client.get_album_tracks(album_id)
        if not tracks:
            return 0

        unique_titles = set()
        for t in tracks:
            # Simple cleaning: remove common version suffixes and lowercase
            clean = t['title'].lower()
            clean = re.sub(r'\(.*?\)', '', clean) # Remove (Remastered), etc
            clean = re.sub(r'\[.*?\]', '', clean) # Remove [Edit], etc
            clean = re.split(r' - ', clean)[0]    # Split on " - " and take first part
            unique_titles.add(clean.strip())

        return len(unique_titles)

    def start_initial_sync(self, user_id):
        """
        Starts the background process to fetch loved tracks,
        extract audio features, and perform CLAP analysis.
        """
        def sync_worker():
            logger.sync(f"Starting sync for user: {user_id}")
            tracks = self.client.get_loved_tracks(user_id)

            album_counts = {} # Cache counts during sync

            for track in tracks:
                track_data = self.client.get_track(track['id'])
                if not track_data or not track_data.get('preview'):
                    continue

                album_id = track_data.get('album', {}).get('id')
                if album_id and album_id not in album_counts:
                    album_counts[album_id] = self._count_unique_tracks(album_id)

                unique_count = album_counts.get(album_id, 0)
                needs_features = not self.db.get_track_preference(track['id'])
                needs_clap = not self.db.get_clap_result(track['id'])

                # Consolidate download to one single session per track
                if needs_features or needs_clap:
                    logger.sync(f"Syncing {track_data['title']} (Album Size: {unique_count})...")
                    preview_path = self.client.download_preview(track_data['preview'], track_data['id'])
                    if not preview_path:
                        continue

                    try:
                        # 1. Librosa Audio Features
                        if needs_features:
                            features = self.client.analyze_audio(preview_path)
                            if features:
                                cover_url = track_data.get('album', {}).get('cover_medium', '')
                                self.db.save_track_preference(track_data, features, cover_url, album_track_count=unique_count)

                        # 2. CLAP AI Semantic Tagging
                        if needs_clap:
                            from backend.clap_analyzer import ClapAnalyzer
                            if not hasattr(self, 'clap_analyzer'):
                                self.clap_analyzer = ClapAnalyzer()

                            results = self.clap_analyzer.analyze(preview_path)
                            if results:
                                self.db.save_clap_result(track['id'], results)
                    except Exception as e:
                        logger.error(f"Sync Error for {track_data['title']}: {e}")
                    finally:
                        if os.path.exists(preview_path):
                            os.remove(preview_path)

            # 3. Finalize Global Profile via RRF
            logger.result("Sync complete. Generating global Sonic DNA Profile...")
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
        """Returns unique albums (with at least 3 tracks) found via loved tracks"""
        return self.db.get_all_synced_albums(min_tracks=3)

    def get_discovery_results(self):
        """Returns analyzed albums with a score > 60 for the discovery tab"""
        return self.db.get_high_score_albums(min_score=60)

    def start_flow_discovery(self, user_id):
        """Fetches Deezer flow and analyzes albums contained within it"""
        def flow_worker():
            logger.sync(f"Discovering Flow for user: {user_id}")
            flow_tracks = self.client.get_user_flow(user_id)

            # Map album_id to a sample track_id for analysis
            album_map = {}
            for t in flow_tracks:
                alb = t.get('album', {})
                alb_id = alb.get('id')
                if alb_id and alb_id not in album_map:
                    album_map[alb_id] = t['id']

            for alb_id, sample_track_id in album_map.items():
                unique_count = self._count_unique_tracks(alb_id)
                if unique_count >= 3:
                    logger.analysis(f"Flow Discovery: Analyzing album {alb_id} (Size: {unique_count})")
                    self._run_album_analysis_logic(sample_track_id)

        threading.Thread(target=flow_worker, daemon=True).start()
        return {"status": "success", "message": "Flow discovery started"}

    def _run_album_analysis_logic(self, track_id, album_id):
        """Synchronous version of the analysis worker logic for internal use"""
        target_id = album_id

        # If a track ID was provided, resolve the album ID from it first
        if track_id:
            track_meta = self.client.get_track(track_id)
            if not track_meta: return 0
            target_id = track_meta['album']['id']
            album_info = {
                "title": track_meta['album']['title'],
                "artist": track_meta['artist']['name'],
                "cover_url": track_meta['album'].get('cover_medium', '')
            }
        else:
            # Fetch album metadata directly if no track was provided
            album_meta = self.client.get_album(target_id)
            if not album_meta: return 0
            album_info = {
                "title": album_meta['title'],
                "artist": album_meta['artist']['name'],
                "cover_url": album_meta.get('cover_medium', '')
            }

        # Perform logic similar to analysis_worker in analyze_album_for_track
        all_prefs = self.db.get_all_features()
        user_profile = self.db.get_global_profile()
        if not all_prefs: return 0

        self.cluster_engine.fit_clusters(all_prefs)
        album_tracks = self.client.get_album_tracks(target_id)
        track_scores = []
        album_feature_history = []

        for t in album_tracks:
            full_t = self.client.get_track(t['id'])
            if not full_t or not full_t.get('preview'): continue
            path = self.client.download_preview(full_t['preview'], full_t['id'])
            if path:
                feats = self.client.analyze_audio(path)
                clap_res = self.db.get_clap_result(full_t['id'])
                if not clap_res:
                    from backend.clap_analyzer import ClapAnalyzer
                    if not hasattr(self, 'clap_analyzer'): self.clap_analyzer = ClapAnalyzer()
                    clap_res = self.clap_analyzer.analyze(path)
                    if clap_res: self.db.save_clap_result(full_t['id'], clap_res)
                if feats:
                    album_feature_history.append(feats)
                    similarity = self.cluster_engine.get_best_similarity(feats)
                    tier = "Risky"
                    if similarity >= 0.80: tier = "Instant Hit"
                    elif similarity >= 0.70: tier = "Natural Grower"
                    elif similarity >= 0.60: tier = "Slow Burner"
                    semantic_tags = {}
                    if clap_res:
                        for layer, labels in clap_res.items():
                            top_labels = sorted(labels.items(), key=lambda x: x[1], reverse=True)[:2]
                            semantic_tags[layer] = [l[0] for l in top_labels]
                    track_scores.append({"title": full_t['title'], "similarity": similarity, "tier": tier, "semantic_tags": semantic_tags})
                os.remove(path)

        if not track_scores: return 0

        sims = [s['similarity'] for s in track_scores]
        n_anchors = len([s for s in sims if s >= 0.80])
        n_inner = len([s for s in sims if 0.70 <= s < 0.80])
        n_outer = len([s for s in sims if 0.60 <= s < 0.70])
        n_horizon = len([s for s in sims if s < 0.60])

        buy_votes = (n_anchors * 4) + (n_inner * 2) + (n_outer * 1)
        total_possible_votes = (n_anchors * 4) + (n_inner * 2) + (n_outer * 3) + (n_horizon * 3)
        final_score = int((buy_votes / total_possible_votes) * 100) if total_possible_votes > 0 else 0
        if n_anchors == 0: final_score = min(final_score, 30)

        journey_data = {"anchors": n_anchors, "inner_bridges": n_inner, "outer_bridges": n_outer, "horizon": n_horizon, "calculated_score": final_score}
        insight = self.advisor.get_album_insight(album_info, track_scores, journey_data, user_profile)
        insight['calculated_confidence_math'] = final_score
        insight['is_complete'] = False if final_score > 60 else True

        self.db.save_scanned_album(target_id, album_info['title'], album_info['artist'], final_score, insight, album_info['cover_url'])

        if final_score > 60:
            acquisition_links = self.scraper.get_links(album_info['artist'], album_info['title'], headless=self.headless_mode)
            insight['acquisition_links'] = acquisition_links
            insight['is_complete'] = True
            self.db.save_scanned_album(target_id, album_info['title'], album_info['artist'], final_score, insight, album_info['cover_url'])

        return final_score

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
            logger.analysis(f"Analyzing album: {track_meta['album']['title']}")

            # 1. Prepare User Taste Clusters & Global Profile
            all_prefs = self.db.get_all_features()
            user_profile = self.db.get_global_profile()
            if not all_prefs:
                logger.warning("No user preferences found. Please sync first.")
                return

            self.cluster_engine.fit_clusters(all_prefs)

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
                    # A. Librosa Math
                    feats = self.client.analyze_audio(path)

                    # B. CLAP Semantic Tags
                    clap_res = self.db.get_clap_result(full_t['id'])
                    if not clap_res:
                        from backend.clap_analyzer import ClapAnalyzer
                        if not hasattr(self, 'clap_analyzer'):
                            self.clap_analyzer = ClapAnalyzer()
                        clap_res = self.clap_analyzer.analyze(path)
                        if clap_res:
                            self.db.save_clap_result(full_t['id'], clap_res)

                    if feats:
                        album_feature_history.append(feats)
                        similarity = self.cluster_engine.get_best_similarity(feats)

                        # Determine Tier Name for LLM (Friendly Labels)
                        tier = "Risky"
                        if similarity >= 0.80: tier = "Instant Hit"
                        elif similarity >= 0.70: tier = "Natural Grower"
                        elif similarity >= 0.60: tier = "Slow Burner"

                        # Extract top semantic tags for LLM context
                        semantic_tags = {}
                        if clap_res:
                            for layer, labels in clap_res.items():
                                top_labels = sorted(labels.items(), key=lambda x: x[1], reverse=True)[:2]
                                semantic_tags[layer] = [l[0] for l in top_labels]

                        track_scores.append({
                            "title": full_t['title'],
                            "similarity": similarity,
                            "tier": tier,
                            "semantic_tags": semantic_tags
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

                buy_votes = (n_anchors * 4) + (n_inner * 2) + (n_outer * 1) + (n_horizon * 0)
                total_possible_votes = (n_anchors * 4) + (n_inner * 2) + (n_outer * 3) + (n_horizon * 3)
                calculated_score = int((buy_votes / total_possible_votes) * 100) if total_possible_votes > 0 else 0

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

            # 4. Get LLM Breakdown (Qualitative Analysis only)
            album_info = {
                "title": track_meta['album']['title'],
                "artist": track_meta['artist']['name'],
                "cover_url": track_meta['album'].get('cover_medium', '')
            }
            insight = self.advisor.get_album_insight(album_info, track_scores, journey_data, user_profile)

            # Use the Hard Math score for the final result, not the LLM's version
            final_score = journey_data['calculated_score']
            insight['calculated_confidence_math'] = final_score

            # 5. Intermediate Save (Show breakdown to user immediately)
            # Mark as not complete if we intend to scrape
            insight['is_complete'] = False if final_score > 60 else True

            self.db.save_scanned_album(
                album_id,
                album_info['title'],
                album_info['artist'],
                final_score,
                insight,
                album_info['cover_url']
            )

            # 6. Marketplace Scraper (Triggered if score > 60)
            if final_score > 60:
                logger.scrape(f"Score promising ({final_score}%). Triggering marketplace search...")
                acquisition_links = self.scraper.get_links(album_info['artist'], album_info['title'], headless=self.headless_mode)

                # Update insight with links and mark as complete
                insight['acquisition_links'] = acquisition_links
                insight['is_complete'] = True

                self.db.save_scanned_album(
                    album_id,
                    album_info['title'],
                    album_info['artist'],
                    final_score,
                    insight,
                    album_info['cover_url']
                )

            logger.result(f"Analysis complete for {album_info['title']}")

        threading.Thread(target=analysis_worker, daemon=True).start()
        return {"status": "pending", "message": "Album analysis started", "album_id": album_id}

    def manual_marketplace_search(self, artist, album):
        """Manually trigger a marketplace search via Google for UI testing"""
        logger.scrape(f"Manual marketplace search triggered for: {artist} - {album} (Headless: {self.headless_mode})")
        return self.scraper.get_links(artist, album, headless=self.headless_mode)

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
            logger.audio(f"Starting CLAP analysis for track {track_id}")
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
                        logger.result(f"CLAP Analysis complete for {track_meta['title']}")
                except Exception as e:
                    logger.error(f"CLAP Error: {e}")
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

    def call_agent(self, text):
        """Calls the AI agent loop with user input"""

        logger.ai(f"Direct Agent call: {text}")
        agent = Agentloop(bridge=self)
        try:
            # Use asyncio.run to execute the coroutine and return the result synchronously to the bridge
            result = asyncio.run(agent.run(text))
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Agent Bridge Error: {e}")
            return {"status": "error", "message": str(e)}