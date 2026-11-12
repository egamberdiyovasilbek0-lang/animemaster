import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("kino_bot.db", check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            joined_at TEXT DEFAULT (datetime('now'))
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT,
            status TEXT DEFAULT 'davom etmoqda',
            views INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            number INTEGER,
            file_id TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            bank TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS channel_members (
            user_id INTEGER PRIMARY KEY
        )""")
        self.conn.commit()

    def add_user(self, uid):
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
        self.conn.commit()

    def is_vip_user(self, uid):
        return False  # Hozircha soddalashtiramiz

    def set_vip(self, uid, months):
        pass

    def add_movie(self, code, name):
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO movies (code, name) VALUES (?, ?)", (code, name))
            self.conn.commit()
            return c.lastrowid
        except:
            return None

    def get_movie_by_code(self, code):
        c = self.conn.cursor()
        c.execute("SELECT * FROM movies WHERE code=?", (code,))
        return c.fetchone()

    def list_movies(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM movies ORDER BY id DESC")
        return c.fetchall()

    def delete_movie(self, mid):
        c = self.conn.cursor()
        c.execute("DELETE FROM episodes WHERE movie_id=?", (mid,))
        c.execute("DELETE FROM movies WHERE id=?", (mid,))
        self.conn.commit()

    def update_status(self, mid, status):
        c = self.conn.cursor()
        c.execute("UPDATE movies SET status=? WHERE id=?", (status, mid))
        self.conn.commit()

    def add_view(self, mid):
        c = self.conn.cursor()
        c.execute("UPDATE movies SET views=views+1 WHERE id=?", (mid,))
        self.conn.commit()

    def add_episode(self, mid, num, fid):
        c = self.conn.cursor()
        c.execute("INSERT INTO episodes (movie_id, number, file_id) VALUES (?, ?, ?)", (mid, num, fid))
        self.conn.commit()

    def get_episodes(self, mid):
        c = self.conn.cursor()
        c.execute("SELECT * FROM episodes WHERE movie_id=? ORDER BY number", (mid,))
        return c.fetchall()

    def get_cards(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM cards")
        return c.fetchall()

    def add_card(self, num, bank):
        c = self.conn.cursor()
        c.execute("INSERT INTO cards (number, bank) VALUES (?, ?)", (num, bank))
        self.conn.commit()

    def delete_card(self, cid):
        c = self.conn.cursor()
        c.execute("DELETE FROM cards WHERE id=?", (cid,))
        self.conn.commit()

    def add_channel_member(self, uid):
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO channel_members VALUES (?)", (uid,))
        self.conn.commit()

    def count_channel_members(self):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM channel_members")
        return c.fetchone()[0]

db = Database()
