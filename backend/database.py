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

            conn.commit()

    def save_track_preference(self, track_meta, features):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences
                (track_id, title, artist, album_title, features_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                track_meta['id'],
                track_meta['title'],
                track_meta['artist']['name'],
                track_meta['album']['title'],
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

    def get_all_features(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT features_json FROM user_preferences')
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def save_scanned_album(self, album_id, title, artist, confidence_score, analysis_json):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scanned_albums
                (album_id, title, artist, confidence_score, analysis_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (album_id, title, artist, confidence_score, json.dumps(analysis_json)))
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
                    "analysis_json": json.loads(row[4])
                }
            return None