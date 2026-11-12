import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("kino_bot.db", check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        
        # Foydalanuvchilar
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_vip BOOLEAN DEFAULT 0,
            vip_expire TIMESTAMP
        )""")
        
        # Kinolar
        c.execute("""CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT,
            status TEXT DEFAULT 'davom etmoqda',
            views INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Kino qismlari
        c.execute("""CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            number INTEGER,
            file_id TEXT,
            FOREIGN KEY(movie_id) REFERENCES movies(id)
        )""")
        
        # Obuna bo'lganlar (kanalga kim qo'shilganini hisoblash)
        c.execute("""CREATE TABLE IF NOT EXISTS channel_members (
            user_id INTEGER PRIMARY KEY,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Bank kartalari
        c.execute("""CREATE TABLE IF NOT EXISTS bank_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT,
            bank_name TEXT
        )""")
        
        self.conn.commit()

    # === Foydalanuvchilar ===
    def add_user(self, user_id):
        c = self.conn.cursor()
        try:
            c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            self.conn.commit()
        except: pass

    def get_user(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return c.fetchone()

    def is_vip_user(self, user_id):
        user = self.get_user(user_id)
        if not user or not user[2]: return False
        expire = user[3]
        if expire and datetime.now() < datetime.fromisoformat(expire):
            return True
        return False

    def set_vip(self, user_id, months):
        c = self.conn.cursor()
        expire_date = datetime.now() + timedelta(days=30*months)
        c.execute("UPDATE users SET is_vip=1, vip_expire=? WHERE user_id=?", 
                  (expire_date.isoformat(), user_id))
        self.conn.commit()

    # === Kinolar ===
    def add_movie(self, code, name, status="davom etmoqda"):
        c = self.conn.cursor()
        try:
            c.execute("INSERT INTO movies (code, name, status) VALUES (?, ?, ?)",
                      (code, name, status))
            self.conn.commit()
            return c.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_movie_by_code(self, code):
        c = self.conn.cursor()
        c.execute("SELECT * FROM movies WHERE code=?", (code,))
        return c.fetchone()

    def list_movies(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM movies ORDER BY id DESC")
        return c.fetchall()

    def delete_movie(self, movie_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM episodes WHERE movie_id=?", (movie_id,))
        c.execute("DELETE FROM movies WHERE id=?", (movie_id,))
        self.conn.commit()

    def update_movie_status(self, movie_id, status):
        c = self.conn.cursor()
        c.execute("UPDATE movies SET status=? WHERE id=?", (status, movie_id))
        self.conn.commit()

    def increment_views(self, movie_id):
        c = self.conn.cursor()
        c.execute("UPDATE movies SET views = views + 1 WHERE id=?", (movie_id,))
        self.conn.commit()

    # === Qismlar ===
    def add_episode(self, movie_id, number, file_id):
        c = self.conn.cursor()
        c.execute("INSERT INTO episodes (movie_id, number, file_id) VALUES (?, ?, ?)",
                  (movie_id, number, file_id))
        self.conn.commit()

    def get_episodes(self, movie_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM episodes WHERE movie_id=? ORDER BY number", (movie_id,))
        return c.fetchall()

    def delete_episode(self, episode_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM episodes WHERE id=?", (episode_id,))
        self.conn.commit()

    # === Kanal a'zolari ===
    def add_channel_member(self, user_id):
        c = self.conn.cursor()
        try:
            c.execute("INSERT OR IGNORE INTO channel_members (user_id) VALUES (?)", (user_id,))
            self.conn.commit()
        except: pass

    def count_channel_members(self):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM channel_members")
        return c.fetchone()[0]

    # === Bank kartalari ===
    def add_bank_card(self, card_number, bank_name):
        c = self.conn.cursor()
        c.execute("INSERT INTO bank_cards (card_number, bank_name) VALUES (?, ?)",
                  (card_number, bank_name))
        self.conn.commit()

    def get_bank_cards(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM bank_cards")
        return c.fetchall()

    def delete_bank_card(self, card_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM bank_cards WHERE id=?", (card_id,))
        self.conn.commit()

db = Database()
