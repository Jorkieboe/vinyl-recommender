import sqlite3
import json
import os

class Database:
    def __init__(self, db_path="vinyl_agent.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # User Preferences (Sonic DNA)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    track_id INTEGER PRIMARY KEY,
                    title TEXT,
                    artist TEXT,
                    album_id INTEGER,
                    album_title TEXT,
                    cover_url TEXT,
                    features_json TEXT,
                    album_track_count INTEGER
                )
            ''')

            # Scanned Albums Cache
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scanned_albums (
                    album_id INTEGER PRIMARY KEY,
                    title TEXT,
                    artist TEXT,
                    confidence_score REAL,
                    anchors INTEGER DEFAULT 0,
                    inner_bridge INTEGER DEFAULT 0,
                    outer_bridge INTEGER DEFAULT 0,
                    horizon INTEGER DEFAULT 0,
                    cover_url TEXT,
                    analysis_text TEXT,
                    is_recommended INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Physical Shelf (Confirmed Purchases)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS physical_shelf (
                    album_id INTEGER PRIMARY KEY,
                    title TEXT,
                    artist TEXT,
                    purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # CLAP Analysis Cache
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clap_results (
                    track_id INTEGER PRIMARY KEY,
                    results_json TEXT
                )
            ''')

            # Global User Profile (Sonic DNA)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_profile (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    profile_json TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    def save_global_profile(self, profile):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO global_profile (id, profile_json, updated_at)
                VALUES (1, ?, CURRENT_TIMESTAMP)
            ''', (json.dumps(profile),))
            conn.commit()

    def get_global_profile(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT profile_json FROM global_profile WHERE id = 1')
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None

    def get_all_clap_results(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT results_json FROM clap_results')
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def save_track_preference(self, track_meta, features, cover_url, album_track_count=0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences
                (track_id, title, artist, album_id, album_title, cover_url, features_json, album_track_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                track_meta['id'],
                track_meta['title'],
                track_meta['artist']['name'],
                track_meta.get('album', {}).get('id'),
                track_meta.get('album', {}).get('title'),
                cover_url,
                json.dumps(features),
                album_track_count
            ))
            conn.commit()

    def get_track_preference(self, track_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_preferences WHERE track_id = ?', (track_id,))
            return cursor.fetchone()

    def get_preference_count(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM user_preferences')
            return cursor.fetchone()[0]

    def get_all_synced_albums(self, min_tracks=4):
        """Returns unique albums that meet the track count threshold"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Group by album_id to show unique albums in the dashboard
            cursor.execute('''
                SELECT album_id, album_title, artist, cover_url, track_id
                FROM user_preferences
                WHERE album_track_count >= ?
                GROUP BY album_id
            ''', (min_tracks,))
            rows = cursor.fetchall()
            return [{"album_id": r[0], "title": r[1], "artist": r[2], "cover": r[3], "sample_track_id": r[4]} for r in rows]

    def get_high_score_albums(self, min_score=60):
        """Returns analyzed albums with a high confidence score"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT album_id, title, artist, confidence_score, anchors, inner_bridge, outer_bridge, horizon, cover_url, analysis_text
                FROM scanned_albums
                WHERE confidence_score >= ?
                ORDER BY confidence_score DESC
            ''', (min_score,))
            rows = cursor.fetchall()
            return [{
                "album_id": r[0],
                "title": r[1],
                "artist": r[2],
                "confidence_score": r[3],
                "anchors": r[4],
                "inner_bridge": r[5],
                "outer_bridge": r[6],
                "horizon": r[7],
                "cover_url": r[8],
                "analysis_json": json.loads(r[9]) if r[9] else {},
            } for r in rows]

    def get_recommended_albums(self):
        """Returns albums explicitly recommended by the agent"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT album_id, title, artist, confidence_score, anchors, inner_bridge, outer_bridge, horizon, cover_url, analysis_text
                FROM scanned_albums
                WHERE is_recommended = 1
                ORDER BY timestamp DESC
            ''')
            rows = cursor.fetchall()
            return [{
                "album_id": r[0],
                "title": r[1],
                "artist": r[2],
                "confidence_score": r[3],
                "anchors": r[4],
                "inner_bridge": r[5],
                "outer_bridge": r[6],
                "horizon": r[7],
                "cover_url": r[8],
                "analysis_json": json.loads(r[9]) if r[9] else {},
            } for r in rows]

    def get_all_features(self):
        """Returns list of dicts containing artist and features for every synced track"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT artist, features_json FROM user_preferences')
            return [{"artist": r[0], "features": json.loads(r[1])} for r in cursor.fetchall()]

    def save_scanned_album(self, album_id, title, artist, confidence_score, anchors, inner_bridge, outer_bridge, horizon, cover_url, analysis_text, is_recommended=0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scanned_albums
                (album_id, title, artist, confidence_score, anchors, inner_bridge, outer_bridge, horizon, cover_url, analysis_text, is_recommended)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (album_id, title, artist, confidence_score, anchors, inner_bridge, outer_bridge, horizon, cover_url, analysis_text, is_recommended))
            conn.commit()

    def get_scanned_album(self, album_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM scanned_albums WHERE album_id = ?', (album_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "album_id": row[0],
                    "title": row[1],
                    "artist": row[2],
                    "confidence_score": row[3],
                    "anchors": row[4],
                    "inner_bridge": row[5],
                    "outer_bridge": row[6],
                    "horizon": row[7],
                    "cover_url": row[8],
                    "analysis_text": row[9],
                    "is_recommended": row[10]
                }
            return None

    def mark_album_as_recommended(self, album_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE scanned_albums SET is_recommended = 1 WHERE album_id = ?', (album_id,))
            conn.commit()

    def save_clap_result(self, track_id, results):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO clap_results
                (track_id, results_json)
                VALUES (?, ?)
            ''', (track_id, json.dumps(results)))
            conn.commit()

    def get_clap_result(self, track_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT results_json FROM clap_results WHERE track_id = ?', (track_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None