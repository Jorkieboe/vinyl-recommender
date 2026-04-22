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
                    album_title TEXT,
                    cover_url TEXT,
                    features_json TEXT
                )
            ''')

            # Scanned Albums Cache
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scanned_albums (
                    album_id INTEGER PRIMARY KEY,
                    title TEXT,
                    artist TEXT,
                    confidence_score REAL,
                    cover_url TEXT,
                    analysis_json TEXT,
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

            conn.commit()

    def save_track_preference(self, track_meta, features, cover_url):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences
                (track_id, title, artist, album_title, cover_url, features_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                track_meta['id'],
                track_meta['title'],
                track_meta['artist']['name'],
                track_meta['album']['title'],
                cover_url,
                json.dumps(features)
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

    def get_all_synced_tracks(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT track_id, title, artist, album_title, cover_url FROM user_preferences')
            rows = cursor.fetchall()
            return [{"id": r[0], "title": r[1], "artist": r[2], "album": r[3], "cover": r[4]} for r in rows]

    def get_all_features(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT features_json FROM user_preferences')
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def save_scanned_album(self, album_id, title, artist, confidence_score, analysis_json, cover_url):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scanned_albums
                (album_id, title, artist, confidence_score, cover_url, analysis_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (album_id, title, artist, confidence_score, cover_url, json.dumps(analysis_json)))
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
                    "cover_url": row[4],
                    "analysis_json": json.loads(row[5])
                }
            return None

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