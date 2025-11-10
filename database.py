import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

# Load .env locally — Render will already have environment variables
load_dotenv()

class TravelDatabase:
    def __init__(self):
        # Prefer Render’s internal DB if available
        self.db_url = (
            os.getenv("RENDER_INTERNAL_DATABASE_URL")
            or os.getenv("DATABASE_URL")
        )

        if not self.db_url:
            raise ValueError("❌ No DATABASE_URL or RENDER_INTERNAL_DATABASE_URL found in environment variables.")

        self.conn = None
        self._connect()

    def _connect(self):
        """Establish or re-establish PostgreSQL connection."""
        try:
            if self.conn:
                self.conn.close()
            # sslmode="require" is safe for public connections; Render internal doesn't need it
            self.conn = psycopg2.connect(self.db_url, sslmode="require")
            self.conn.autocommit = False
            print("✅ Connected to PostgreSQL successfully!")
            self._create_table()
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.conn = None

    def _create_table(self):
        """Ensure the searches table exists."""
        if not self.conn:
            print("⚠️ No DB connection to create table.")
            return

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS searches (
                        id SERIAL PRIMARY KEY,
                        user_query TEXT NOT NULL,
                        bot_reply TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                self.conn.commit()
                print("✅ Table 'searches' ready.")
        except Exception as e:
            print(f"⚠️ Error creating table: {e}")
            self._rollback()

    def _rollback(self):
        """Rollback transaction safely."""
        try:
            if self.conn:
                self.conn.rollback()
                print("↩️ Transaction rolled back.")
        except Exception as e:
            print(f"⚠️ Rollback failed: {e}")
            self._connect()

    def save_search(self, user_query, bot_reply):
        """Save user and bot messages into DB."""
        if not self.conn:
            print("⚠️ No DB connection — reconnecting …")
            self._connect()

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO searches (user_query, bot_reply, created_at) VALUES (%s, %s, %s);",
                    (user_query, bot_reply, datetime.utcnow())
                )
                self.conn.commit()
                print(f"💾 Saved search → {user_query[:30]} | {bot_reply[:50]}")
        except psycopg2.InterfaceError:
            print("⚠️ Lost DB connection — reconnecting …")
            self._connect()
            self.save_search(user_query, bot_reply)
        except Exception as e:
            print(f"⚠️ Error saving search: {e}")
            self._rollback()

    def get_all_searches(self):
        """Fetch all saved searches safely."""
        if not self.conn:
            print("⚠️ No DB connection — reconnecting …")
            self._connect()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM searches ORDER BY created_at DESC;")
                rows = cur.fetchall()
                self.conn.commit()
                print(f"📜 Retrieved {len(rows)} records.")
                return rows
        except psycopg2.InterfaceError:
            print("⚠️ Lost DB connection — reconnecting …")
            self._connect()
            return self.get_all_searches()
        except Exception as e:
            print(f"⚠️ Error reading searches: {e}")
            self._rollback()
            return []

    def __del__(self):
        """Close the DB connection cleanly."""
        try:
            if self.conn:
                self.conn.close()
                print("🔒 PostgreSQL connection closed.")
        except Exception:
            pass
