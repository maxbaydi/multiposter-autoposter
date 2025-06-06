import sqlite3
from datetime import datetime, timedelta

class DBManager:
    def __init__(self, db_path='autoposter.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            title TEXT,
            body TEXT,
            tags TEXT,
            telegram_summary TEXT,
            status TEXT,
            platforms TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            file_path TEXT,
            wp_media_id INTEGER,
            wp_url TEXT,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS publication_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT,
            topic TEXT,
            platform TEXT,
            status TEXT,
            published_at TEXT
        )''')
        self.conn.commit()

    def add_post(self, topic, title, body, tags, telegram_summary, status, platforms):
        c = self.conn.cursor()
        c.execute('''INSERT INTO posts (topic, title, body, tags, telegram_summary, status, platforms)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (topic, title, body, tags, telegram_summary, status, platforms))
        self.conn.commit()
        return c.lastrowid

    def get_posts(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM posts ORDER BY created_at DESC')
        return c.fetchall()

    def add_publication_history(self, brand, topic, platform, status, published_at=None):
        c = self.conn.cursor()
        if not published_at:
            published_at = datetime.now().isoformat()
        c.execute('''INSERT INTO publication_history (brand, topic, platform, status, published_at)
                     VALUES (?, ?, ?, ?, ?)''',
                  (brand, topic, platform, status, published_at))
        self.conn.commit()

    def get_recent_publications(self, days=3):
        c = self.conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute('SELECT brand, topic, platform, published_at FROM publication_history WHERE published_at > ?', (since,))
        return c.fetchall() 